#include "PCH.h"

#include "DevBenchTool.h"

#include "AutoDraw.h"
#include "DevBench/DevBenchAPI.h"
#include "Settings.h"
#include "utils/Logger.h"
#include "utils/Strings.h"

#include <format>
#include <string>
#include <string_view>

namespace DevBenchTool
{
	namespace
	{
		std::string EscapeJson(std::string_view a_in)
		{
			std::string out;
			out.reserve(a_in.size() + 8);
			for (const char c : a_in)
			{
				switch (c)
				{
				case '\\': out += "\\\\"; break;
				case '"': out += "\\\""; break;
				case '\n': out += "\\n"; break;
				default: out += c; break;
				}
			}
			return out;
		}

		void ControlTool(void*, const char* a_argsJson, void* a_sink, DevBenchAPI::WriteFn a_write)
		{
			const std::string_view args = a_argsJson ? a_argsJson : "";
			auto has = [&](const char* a_op) { return args.find(std::format("\"{}\"", a_op)) != std::string_view::npos; };

			if (has("draw"))
			{
				AutoDraw::ForceDraw();
				a_write(a_sink, R"({"ok":true,"op":"draw"})");
				return;
			}
			if (has("sheathe"))
			{
				AutoDraw::ForceSheathe();
				a_write(a_sink, R"({"ok":true,"op":"sheathe"})");
				return;
			}
			if (has("reload"))
			{
				const bool ok = settings::Reload();
				a_write(a_sink, std::format(R"({{"ok":{},"op":"reload"}})", ok ? "true" : "false").c_str());
				return;
			}
			if (has("strings"))
			{
				a_write(a_sink, std::format(R"({{"ok":true,"op":"strings","strings":{}}})", strings::StatusJson()).c_str());
				return;
			}

			const auto s = AutoDraw::GetState();
			const std::string json = std::format(
				"{{\"ok\":true,"
				"\"settings\":{{\"enableAutoDraw\":{},\"enableAutoSheathe\":{},\"sheatheDelaySeconds\":{:.1f},"
				"\"exemptBoundWeapons\":{},\"logLevel\":{},\"iniPath\":\"{}\"}},"
				"\"runtime\":{{\"ticking\":{},\"paused\":{},\"inCombat\":{},\"weaponState\":{},"
				"\"sheatheTimerRunning\":{},\"sheatheTimerSeconds\":{:.2f},\"boundWeaponHeld\":{},"
				"\"autoDraws\":{},\"autoSheathes\":{},\"lastAction\":\"{}\"}}}}",
				settings::automation::enableAutoDraw, settings::automation::enableAutoSheathe,
				settings::automation::sheatheDelaySeconds, settings::automation::exemptBoundWeapons,
				settings::debug::logLevel, EscapeJson(settings::GetIniPath()),
				s.ticking, s.paused, s.inCombat, s.weaponState,
				s.sheatheTimerRunning, s.sheatheTimerSeconds, s.boundWeaponHeld,
				s.autoDraws, s.autoSheathes, EscapeJson(s.lastAction));
			a_write(a_sink, json.c_str());
		}
	}

	void Init(bool a_lastAttempt)
	{
		static bool registered = false;
		if (registered) { return; }

		DevBenchAPI::IDevBenchInterface001* devBench = DevBenchAPI::GetDevBenchInterface001();
		if (!devBench)
		{
			if (a_lastAttempt)
			{
				logger::info("DevBench not detected; skipping the \"autodraw.control\" tool (logging alone covers this session)");
			}
			else
			{
				logger::debug("DevBench not detected yet; will retry at the next message");
			}
			return;
		}

		constexpr const char* descriptor =
			"{"
			"\"description\":\"Auto Draw live state and test drives: current settings, the tick's "
			"last observation (combat, weapon state, sheathe countdown, bound-weapon hold) and "
			"lifetime counters. op=draw / op=sheathe force the animation call for testing; "
			"op=reload re-reads the INI. op=strings reports the active language, source and loaded "
			"translation count.\","
			"\"inputSchema\":{\"type\":\"object\",\"properties\":{\"op\":{\"type\":\"string\"}}},"
			"\"readOnly\":false"
			"}";

		if (devBench->RegisterTool("autodraw.control", descriptor, &ControlTool, nullptr))
		{
			logger::info("Registered \"autodraw.control\" with DevBench (build {})", devBench->GetBuildNumber());
			registered = true;
		}
	}
}
