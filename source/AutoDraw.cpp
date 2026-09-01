#include "PCH.h"

#include "AutoDraw.h"

#include "Settings.h"
#include "utils/Logger.h"

#include <atomic>
#include <chrono>
#include <mutex>
#include <optional>
#include <thread>

namespace AutoDraw
{
	namespace
	{
		using Clock = std::chrono::steady_clock;

		std::atomic<bool> g_installed{ false };

		// True while a posted tick is waiting to run on the main thread. The poster thread
		// only posts when this is clear, so the task queue can never accumulate ticks - and a
		// tick can never re-queue ITSELF: SKSE drains its task queue until empty within one
		// frame, so a self-requeuing task pins the main thread in that drain loop forever.
		// (Found the hard way: the first build froze the game at kDataLoaded and AMF's
		// watchdog terminated it after 120 frameless seconds.)
		std::atomic<bool> g_tickPending{ false };

		// Everything below the mutex is written by the main-thread tick and read by the
		// DevBench tool from its listener thread.
		std::mutex g_stateLock;
		State g_state;

		// When the "drawn, out of combat, not busy" condition FIRST became true, or empty
		// while it is false. The timer is this timestamp, nothing else - so any tick that sees
		// a disqualifier simply clears it and the wait starts over.
		std::optional<Clock::time_point> g_eligibleSince;

		bool BoundWeaponHeld(RE::PlayerCharacter* a_player)
		{
			for (const bool leftHand : { false, true })
			{
				if (const auto* obj = a_player->GetEquippedObject(leftHand))
				{
					if (const auto* weap = obj->As<RE::TESObjectWEAP>(); weap && weap->IsBound())
					{
						return true;
					}
				}
			}
			return false;
		}

		void Tick()
		{
			// Mark this tick consumed FIRST so an early return can never wedge the poster.
			g_tickPending.store(false, std::memory_order_release);

			State s;
			s.ticking = true;

			auto* ui = RE::UI::GetSingleton();
			s.paused = !ui || ui->GameIsPaused();

			auto* player = RE::PlayerCharacter::GetSingleton();
			if (s.paused || !player || !player->Is3DLoaded() || player->IsDead())
			{
				// Menus, loading, death: do nothing, decide fresh when gameplay resumes. The
				// timer deliberately clears - a delay that kept counting through a menu would
				// sheathe the instant it closed, which reads as the mod acting while paused.
				g_eligibleSince.reset();
				std::scoped_lock l(g_stateLock);
				s.autoDraws = g_state.autoDraws;
				s.autoSheathes = g_state.autoSheathes;
				s.lastAction = g_state.lastAction;
				g_state = s;
				return;
			}

			auto* actorState = player->AsActorState();
			const auto weaponState = actorState->GetWeaponState();
			s.weaponState = static_cast<std::uint32_t>(weaponState);
			s.inCombat = player->IsInCombat();
			s.boundWeaponHeld = BoundWeaponHeld(player);

			// AUTO DRAW: combat has found the player and the weapon is away. The call is the
			// animation-only draw; it equips nothing and works for weapons and magic alike.
			if (settings::automation::enableAutoDraw && s.inCombat && weaponState == RE::WEAPON_STATE::kSheathed)
			{
				player->DrawWeaponMagicHands(true);
				g_eligibleSince.reset();
				std::scoped_lock l(g_stateLock);
				s.autoDraws = g_state.autoDraws + 1;
				s.autoSheathes = g_state.autoSheathes;
				s.lastAction = "draw";
				g_state = s;
				logger::debug("auto draw: combat, weapon was sheathed");
				return;
			}

			// AUTO SHEATHE, state-based: "drawn while out of combat" is the whole condition,
			// however it came about - combat ended, the player drew manually, or a save was
			// LOADED with the weapon already out (the case the event-driven approach misses).
			// Attacking, blocking or being airborne pauses the countdown by restarting it.
			const bool busy = actorState->GetAttackState() != RE::ATTACK_STATE_ENUM::kNone ||
							  player->IsBlocking() || player->IsInMidair();
			const bool eligible = settings::automation::enableAutoSheathe && !s.inCombat &&
								  weaponState == RE::WEAPON_STATE::kDrawn && !busy;

			if (!eligible)
			{
				g_eligibleSince.reset();
			}
			else
			{
				const auto now = Clock::now();
				if (!g_eligibleSince) { g_eligibleSince = now; }
				const float held = std::chrono::duration<float>(now - *g_eligibleSince).count();
				s.sheatheTimerRunning = true;
				s.sheatheTimerSeconds = held;

				if (held >= settings::automation::sheatheDelaySeconds)
				{
					if (settings::automation::exemptBoundWeapons && s.boundWeaponHeld)
					{
						// A bound weapon stays out: it ends on its own duration or when the
						// player sheathes it. Restart the wait so dismissal is followed by a
						// full, predictable delay rather than an instant sheathe.
						g_eligibleSince = now;
						s.sheatheTimerSeconds = 0.0F;
					}
					else
					{
						player->DrawWeaponMagicHands(false);
						g_eligibleSince.reset();
						s.sheatheTimerRunning = false;
						s.sheatheTimerSeconds = 0.0F;
						std::scoped_lock l(g_stateLock);
						s.autoDraws = g_state.autoDraws;
						s.autoSheathes = g_state.autoSheathes + 1;
						s.lastAction = "sheathe";
						g_state = s;
						logger::debug("auto sheathe: {:.1f}s out of combat", held);
						return;
					}
				}
			}

			std::scoped_lock l(g_stateLock);
			s.autoDraws = g_state.autoDraws;
			s.autoSheathes = g_state.autoSheathes;
			s.lastAction = g_state.lastAction;
			g_state = s;
		}
	}

	void Install()
	{
		if (g_installed.exchange(true)) { return; }
		if (!SKSE::GetTaskInterface())
		{
			g_installed = false;
			logger::error("SKSE task interface unavailable; Auto Draw cannot run");
			return;
		}

		// A detached poster thread hands one tick at a time to the main thread, ~20 times a
		// second. The main thread only ever executes; it never schedules - so no hooks, no
		// relocations, and no way for the tick to monopolise a frame. If the main thread is
		// busy (loading screens), g_tickPending simply stays set and the poster idles.
		std::thread([]() {
			while (g_installed.load(std::memory_order_relaxed))
			{
				if (!g_tickPending.exchange(true, std::memory_order_acq_rel))
				{
					if (auto* tasks = SKSE::GetTaskInterface()) { tasks->AddTask(Tick); }
					else { g_tickPending.store(false, std::memory_order_release); }
				}
				std::this_thread::sleep_for(std::chrono::milliseconds(50));
			}
		}).detach();

		logger::info("tick poster installed (state-based, ~20 Hz; no hooks, no relocations)");
	}

	State GetState()
	{
		std::scoped_lock l(g_stateLock);
		return g_state;
	}

	void ForceDraw()
	{
		if (auto* tasks = SKSE::GetTaskInterface())
		{
			tasks->AddTask([]() {
				if (auto* player = RE::PlayerCharacter::GetSingleton()) { player->DrawWeaponMagicHands(true); }
			});
		}
	}

	void ForceSheathe()
	{
		if (auto* tasks = SKSE::GetTaskInterface())
		{
			tasks->AddTask([]() {
				if (auto* player = RE::PlayerCharacter::GetSingleton()) { player->DrawWeaponMagicHands(false); }
			});
		}
	}
}
