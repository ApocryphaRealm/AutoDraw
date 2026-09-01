#pragma once

// Auto Draw core - clean-room MIT rebuild (2026-08-31). STATE-BASED by design: a per-frame
// main-thread tick reads the player's actual weapon/combat state and acts on what it sees,
// rather than reacting to events. That makes the behaviour self-healing - loading a save with
// the weapon already drawn simply IS the "drawn, out of combat" state, so the sheathe timer
// starts on its own (the event-driven original missed exactly that case).

#include <cstdint>
#include <string>

namespace AutoDraw
{
	// Starts the per-frame tick (self-requeuing SKSE main-thread task). Call once at
	// kDataLoaded. Idempotent.
	void Install();

	// Live state for the DevBench tool: everything the tick last observed and did.
	struct State
	{
		bool ticking = false;
		bool paused = false;           // game paused last tick (logic skipped)
		bool inCombat = false;
		std::uint32_t weaponState = 0; // RE::WEAPON_STATE as int
		bool sheatheTimerRunning = false;
		float sheatheTimerSeconds = 0.0F;  // how long the eligible state has held
		bool boundWeaponHeld = false;
		std::uint64_t autoDraws = 0;    // lifetime counters this session
		std::uint64_t autoSheathes = 0;
		std::string lastAction;         // "draw" / "sheathe" / ""
	};
	State GetState();

	// Test hooks for the DevBench tool: force the animation call now (main-thread queued).
	void ForceDraw();
	void ForceSheathe();
}
