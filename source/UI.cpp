#include "PCH.h"

#include "UI.h"

#include "SKSEMenuFramework.h"

#include "AutoDraw.h"
#include "Settings.h"

#include "utils/Logger.h"
#include "utils/Toggle.h"

#include <algorithm>
#include <functional>
#include <string>

namespace UI
{
	namespace
	{
		std::string statusMessage;

		// The slider the arrow keys currently drive. Set by clicking one (project convention:
		// sliders are nudgeable with all four arrow keys; up/right increase, down/left decrease).
		std::string selectedSlider;

		constexpr const char* kLogLevelNames[] = { "Trace", "Debug", "Info", "Warning", "Error", "Critical", "Off" };
		constexpr int kLogLevelCount = 7;

		// The framework renders from the renderer's present hook; anything touching game state
		// is handed to the main thread first.
		void OnMainThread(std::function<void()> a_task)
		{
			if (auto* taskInterface = SKSE::GetTaskInterface())
			{
				taskInterface->AddTask(std::move(a_task));
			}
		}

		// Refuse to register unless every exported cimgui entry point this page calls is
		// actually there - an older framework build would otherwise crash on first draw
		// through a null function pointer. Probed by RESOLVED export name (varargs wrappers
		// resolve their V variant - igTextDisabledV, not igTextDisabled).
		bool HasRequiredExports()
		{
			constexpr const char* required[] = {
				"AddSectionItem",
				"igTextV",
				"igTextDisabledV",
				"igTextWrappedV",
				"igSetTooltipV",
				"igSeparatorText",
				"igCombo_Str_arr",
				"igSliderFloat",
				"igIsKeyPressed_Bool",
				"igIsItemClicked",
				"igIsItemActive",
				"igIsItemHovered",
				"igButton",
				"igSameLine",
				"igSpacing",
				"igPushItemWidth",
				"igPopItemWidth",
				// utils/Toggle.h - the on/off switch every boolean renders as (rule 32).
				"igGetCursorScreenPos",
				"igGetWindowDrawList",
				"igGetFrameHeight",
				"igInvisibleButton",
				"igPushID_Str",
				"igPopID",
				"ImDrawList_AddRectFilled",
				"ImDrawList_AddCircleFilled"
			};

			for (const char* name : required)
			{
				if (!GetMenuFrameworkFunction<void*>(name))
				{
					logger::warn("The menu framework does not export \"{}\"", name);

					return false;
				}
			}

			return true;
		}

		// Dim "(?)" marker with a readable tooltip. Markers recede; prose stays readable
		// (project rule: TextDisabled is for ornament only, never for words people must read).
		void HelpMarker(const char* a_description)
		{
			ImGuiMCP::SameLine();
			ImGuiMCP::TextDisabled("(?)");
			if (ImGuiMCP::IsItemHovered())
			{
				ImGuiMCP::SetTooltip("%s", a_description);
			}
		}

		bool NudgeableSlider(const char* a_label, float* a_value, float a_min, float a_max,
							 const char* a_format, float a_step)
		{
			bool changed = ImGuiMCP::SliderFloat(a_label, a_value, a_min, a_max, a_format);

			if (ImGuiMCP::IsItemClicked() || ImGuiMCP::IsItemActive())
			{
				selectedSlider = a_label;
			}

			if (selectedSlider == a_label)
			{
				float nudge = 0.0F;

				if (ImGuiMCP::IsKeyPressed(ImGuiMCP::ImGuiKey_LeftArrow) || ImGuiMCP::IsKeyPressed(ImGuiMCP::ImGuiKey_DownArrow))
				{
					nudge -= a_step;
				}
				if (ImGuiMCP::IsKeyPressed(ImGuiMCP::ImGuiKey_RightArrow) || ImGuiMCP::IsKeyPressed(ImGuiMCP::ImGuiKey_UpArrow))
				{
					nudge += a_step;
				}

				if (nudge != 0.0F)
				{
					*a_value = std::clamp(*a_value + nudge, a_min, a_max);
					changed = true;
				}

				ImGuiMCP::SameLine();
				ImGuiMCP::TextDisabled("<-->");
			}

			return changed;
		}

		void RenderAutomationSection()
		{
			using namespace settings;

			ImGuiMCP::SeparatorText("Automation");

			ImGuiMCP::Toggle("Auto draw", &automation::enableAutoDraw);
			HelpMarker("Draws your weapon or magic the instant something targets you in combat.");

			ImGuiMCP::Toggle("Auto sheathe", &automation::enableAutoSheathe);
			HelpMarker("Sheathes your weapon or magic a set delay after you leave combat, or after you draw it manually.");

			NudgeableSlider("Sheathe delay", &automation::sheatheDelaySeconds, 0.5F, 30.0F, "%.1f s", 0.5F);
			HelpMarker("How long to wait after leaving combat, or after drawing manually, before the forced sheathe. Attacking, blocking, being airborne or re-entering combat restarts the wait.");

			ImGuiMCP::Toggle("Leave bound weapons drawn", &automation::exemptBoundWeapons);
			HelpMarker("Skips the forced sheathe while a bound (conjured) weapon is drawn, so it is not dismissed early - it still ends on its own duration or when you sheathe it yourself.");
		}

		void RenderDebugSection()
		{
			using namespace settings;

			ImGuiMCP::SeparatorText("Debug");

			int level = static_cast<int>(debug::logLevel);
			level = std::clamp(level, 0, kLogLevelCount - 1);
			if (ImGuiMCP::Combo("Log level", &level, kLogLevelNames, kLogLevelCount))
			{
				debug::logLevel = static_cast<std::uint32_t>(level);
				ApplyLogLevel();
			}
			HelpMarker("Applies immediately. The log is at Documents\\My Games\\Skyrim Special Edition\\SKSE\\AutoDraw.log. Set this to Trace or Debug before reproducing a bug you plan to report.");
		}

		void RenderButtons()
		{
			ImGuiMCP::SeparatorText("");

			if (ImGuiMCP::Button("Save"))
			{
				statusMessage = "Saving...";
				OnMainThread([]() {
					statusMessage = settings::Save() ? "Settings saved." : "Could not write the INI. See the log for why.";
				});
			}
			HelpMarker("Writes every setting on this page to the plugin's INI so it survives a restart.");

			ImGuiMCP::SameLine();

			if (ImGuiMCP::Button("Reload from INI"))
			{
				statusMessage = "Reloading...";
				OnMainThread([]() {
					statusMessage = settings::Reload() ? "Settings reloaded from the INI."
													   : "Could not read the INI. See the log for why.";
				});
			}
			HelpMarker("Throws away any change made here since the last save and re-reads the INI from disk. Also picks up edits made to the file by hand.");

			ImGuiMCP::SameLine();

			if (ImGuiMCP::Button("Restore defaults"))
			{
				OnMainThread([]() {
					settings::RestoreDefaults();
					logger::debug("Restored default settings");
				});

				statusMessage = "Defaults restored. Press Save to keep them.";
			}
			HelpMarker("Puts every setting back to the value it has on a fresh install. Nothing is written until you press Save.");

			if (!statusMessage.empty())
			{
				ImGuiMCP::TextWrapped("%s", statusMessage.c_str());
			}

			ImGuiMCP::Spacing();
			// Readable, not dim: a file path is something a person reads and often copies.
			ImGuiMCP::Text("%s", settings::GetIniPath().c_str());
		}
	}

	void Register()
	{
		if (!SKSEMenuFramework::IsInstalled())
		{
			logger::info("No menu framework is installed; settings will be read from the INI only");

			return;
		}

		if (!HasRequiredExports())
		{
			logger::warn("The installed menu framework is older than this plugin's settings "
						 "menu needs. Update it (Apocrypha Menu Framework, or SKSE Menu "
						 "Framework version 3 or newer) to configure Auto Draw in game.");

			return;
		}

		SKSEMenuFramework::SetSection("Auto Draw");
		SKSEMenuFramework::AddSectionItem("Settings", SettingsPanel::Render);

		logger::info("Registered the settings page with the menu framework");
	}

	void __stdcall SettingsPanel::Render()
	{
		ImGuiMCP::TextWrapped("Changes apply as soon as you make them. Press Save to keep them for the next time you play.");
		ImGuiMCP::Spacing();

		ImGuiMCP::PushItemWidth(260.0F);

		RenderAutomationSection();
		ImGuiMCP::Spacing();

		RenderDebugSection();
		ImGuiMCP::Spacing();

		ImGuiMCP::PopItemWidth();

		RenderButtons();
	}
}
