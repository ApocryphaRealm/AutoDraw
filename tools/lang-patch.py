# -*- coding: utf-8 -*-
"""lang-patch.py - one-shot, re-runnable language-support patch for Auto Draw.

Applies the consumer-side mechanism from D:\\Claude output\\4. plans\\translation-rollout\\plan.md
sections 2 and 4.1: strings::TR() routing for every literal the settings page draws, the
"!ApocryphaMenuFramework" module-name lookup, strings::Configure() at kDataLoaded, and a
"strings" DevBench op. Every edit below is a must-match anchor replace: if an anchor is not
found EXACTLY ONCE the script raises instead of silently doing nothing, so a stale run against
changed source fails loudly rather than leaving the code half patched.

Run from anywhere: `python tools/lang-patch.py` (paths are relative to the repo root, taken as
this script's grandparent directory).
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path):
    # Universal-newline read: whichever convention the file uses on disk, every anchor below is
    # written once, in "\n" - write() restores the file's own convention (crlf=True/False).
    with open(path, "r", encoding="utf-8", newline=None) as f:
        return f.read()


def write(path, text, crlf=False):
    with open(path, "w", encoding="utf-8", newline="\r\n" if crlf else "\n") as f:
        f.write(text)


def apply_one(text, anchor, replacement, label, done_marker=None):
    # If this exact replacement text is already present, the edit was already applied by a
    # previous (partial) run - skip it so the script is safely re-runnable.
    if done_marker is not None and done_marker in text:
        return text
    n = text.count(anchor)
    if n != 1:
        raise RuntimeError(f"[{label}] anchor found {n} time(s), expected exactly 1:\n{anchor!r}")
    return text.replace(anchor, replacement, 1)


# ------------------------------------------------------------------------------------------------
# 1) include/SKSEMenuFramework.h - "!ApocryphaMenuFramework" first, ahead of the alias name.
# ------------------------------------------------------------------------------------------------
def patch_skse_menu_framework_h():
    path = os.path.join(REPO, "include", "SKSEMenuFramework.h")
    text = read(path)
    if 'GetModuleHandleW(L"!ApocryphaMenuFramework")' in text:
        return  # already applied by a previous (partial) run
    anchor = (
        "inline HMODULE GetMenuFrameworkModule() {\n"
        "    static HMODULE menuFramework = nullptr;\n"
        "    if (!menuFramework) {\n"
        "        menuFramework = GetModuleHandleW(L\"ApocryphaMenuFramework\");\n"
        "        if (!menuFramework) {\n"
        "            menuFramework = GetModuleHandleW(L\"SKSEMenuFramework\");\n"
        "        }\n"
        "    }\n"
        "    return menuFramework;\n"
        "}"
    )
    replacement = (
        "inline HMODULE GetMenuFrameworkModule() {\n"
        "    static HMODULE menuFramework = nullptr;\n"
        "    if (!menuFramework) {\n"
        "        menuFramework = GetModuleHandleW(L\"!ApocryphaMenuFramework\");\n"
        "        if (!menuFramework) {\n"
        "            menuFramework = GetModuleHandleW(L\"ApocryphaMenuFramework\");\n"
        "        }\n"
        "        if (!menuFramework) {\n"
        "            menuFramework = GetModuleHandleW(L\"SKSEMenuFramework\");\n"
        "        }\n"
        "    }\n"
        "    return menuFramework;\n"
        "}"
    )
    text = apply_one(text, anchor, replacement, "SKSEMenuFramework.h:GetMenuFrameworkModule")
    write(path, text, crlf=True)


# ------------------------------------------------------------------------------------------------
# 2) source/main.cpp - strings::Configure("AutoDraw") at kDataLoaded.
# ------------------------------------------------------------------------------------------------
def patch_main_cpp():
    path = os.path.join(REPO, "source", "main.cpp")
    text = read(path)
    if 'strings::Configure("AutoDraw")' in text:
        return  # already applied by a previous (partial) run

    text = apply_one(
        text,
        "#include \"UI.h\"\n\n#include \"utils/Logger.h\"",
        "#include \"UI.h\"\n\n#include \"utils/Logger.h\"\n#include \"utils/Strings.h\"",
        "main.cpp:include",
    )

    anchor = (
        "\t\tcase SKSE::MessagingInterface::kDataLoaded:\n"
        "\t\t\tUI::Register();\n"
        "\t\t\tAutoDraw::Install();\n"
        "\t\t\tDevBenchTool::Init(true);\n"
        "\t\t\tbreak;"
    )
    replacement = (
        "\t\tcase SKSE::MessagingInterface::kDataLoaded:\n"
        "\t\t\tstrings::Configure(\"AutoDraw\");\n"
        "\t\t\tUI::Register();\n"
        "\t\t\tAutoDraw::Install();\n"
        "\t\t\tDevBenchTool::Init(true);\n"
        "\t\t\tbreak;"
    )
    text = apply_one(text, anchor, replacement, "main.cpp:kDataLoaded")
    write(path, text)


# ------------------------------------------------------------------------------------------------
# 3) source/DevBenchTool.cpp - a "strings" op returning strings::StatusJson(); descriptor updated.
# ------------------------------------------------------------------------------------------------
def patch_devbench_tool_cpp():
    path = os.path.join(REPO, "source", "DevBenchTool.cpp")
    text = read(path)

    text = apply_one(
        text,
        "#include \"Settings.h\"\n#include \"utils/Logger.h\"",
        "#include \"Settings.h\"\n#include \"utils/Logger.h\"\n#include \"utils/Strings.h\"",
        "DevBenchTool.cpp:include",
    )

    anchor = (
        "\t\t\tif (has(\"reload\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tconst bool ok = settings::Reload();\n"
        "\t\t\t\ta_write(a_sink, std::format(R\"({{\"ok\":{},\"op\":\"reload\"}})\", ok ? \"true\" : \"false\").c_str());\n"
        "\t\t\t\treturn;\n"
        "\t\t\t}\n"
    )
    replacement = (
        "\t\t\tif (has(\"reload\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tconst bool ok = settings::Reload();\n"
        "\t\t\t\ta_write(a_sink, std::format(R\"({{\"ok\":{},\"op\":\"reload\"}})\", ok ? \"true\" : \"false\").c_str());\n"
        "\t\t\t\treturn;\n"
        "\t\t\t}\n"
        "\t\t\tif (has(\"strings\"))\n"
        "\t\t\t{\n"
        "\t\t\t\ta_write(a_sink, std::format(R\"({{\"ok\":true,\"op\":\"strings\",\"strings\":{}}})\", strings::StatusJson()).c_str());\n"
        "\t\t\t\treturn;\n"
        "\t\t\t}\n"
    )
    text = apply_one(text, anchor, replacement, "DevBenchTool.cpp:ControlTool ops")

    text = apply_one(
        text,
        "\t\t\t\"op=reload re-reads the INI.\\\",\"\n",
        "\t\t\t\"op=reload re-reads the INI. op=strings reports the active language, source and loaded \"\n"
        "\t\t\t\"translation count.\\\",\"\n",
        "DevBenchTool.cpp:descriptor",
    )
    write(path, text)


# ------------------------------------------------------------------------------------------------
# 4) source/UI.cpp - route every drawn literal through strings::TR().
# ------------------------------------------------------------------------------------------------
def patch_ui_cpp():
    path = os.path.join(REPO, "source", "UI.cpp")
    text = read(path)

    text = apply_one(
        text,
        "#include \"utils/Logger.h\"\n#include \"utils/Toggle.h\"",
        "#include \"utils/Logger.h\"\n#include \"utils/Strings.h\"\n#include \"utils/Toggle.h\"",
        "UI.cpp:include",
    )

    text = apply_one(
        text,
        "#include <algorithm>\n#include <functional>\n#include <string>",
        "#include <algorithm>\n#include <functional>\n#include <string>\n#include <vector>",
        "UI.cpp:vector include",
    )

    # --- HelpMarker: the tooltip text is the parameter, already TR'd at each call site ----------
    text = apply_one(
        text,
        "\t\t\tImGuiMCP::SameLine();\n"
        "\t\t\tImGuiMCP::TextDisabled(\"(?)\");\n"
        "\t\t\tif (ImGuiMCP::IsItemHovered())\n"
        "\t\t\t{\n"
        "\t\t\t\tImGuiMCP::SetTooltip(\"%s\", a_description);\n"
        "\t\t\t}",
        "\t\t\tImGuiMCP::SameLine();\n"
        "\t\t\tImGuiMCP::TextDisabled(\"%s\", strings::TR(\"AD_HelpMark\", \"(?)\"));\n"
        "\t\t\tif (ImGuiMCP::IsItemHovered())\n"
        "\t\t\t{\n"
        "\t\t\t\tImGuiMCP::SetTooltip(\"%s\", a_description);\n"
        "\t\t\t}",
        "UI.cpp:HelpMarker",
    )

    # --- NudgeableSlider: the "<-->" nudge indicator ---------------------------------------------
    text = apply_one(
        text,
        "\t\t\t\tImGuiMCP::SameLine();\n"
        "\t\t\t\tImGuiMCP::TextDisabled(\"<-->\");",
        "\t\t\t\tImGuiMCP::SameLine();\n"
        "\t\t\t\tImGuiMCP::TextDisabled(\"%s\", strings::TR(\"AD_NudgeArrows\", \"<-->\"));",
        "UI.cpp:NudgeArrows",
    )

    # --- RenderAutomationSection ------------------------------------------------------------------
    text = apply_one(
        text,
        "\t\t\tImGuiMCP::SeparatorText(\"Automation\");\n"
        "\n"
        "\t\t\tImGuiMCP::Toggle(\"Auto draw\", &automation::enableAutoDraw);\n"
        "\t\t\tHelpMarker(\"Draws your weapon or magic the instant something targets you in combat.\");\n"
        "\n"
        "\t\t\tImGuiMCP::Toggle(\"Auto sheathe\", &automation::enableAutoSheathe);\n"
        "\t\t\tHelpMarker(\"Sheathes your weapon or magic a set delay after you leave combat, or after you draw it manually.\");\n"
        "\n"
        "\t\t\tNudgeableSlider(\"Sheathe delay\", &automation::sheatheDelaySeconds, 0.5F, 30.0F, \"%.1f s\", 0.5F);\n"
        "\t\t\tHelpMarker(\"How long to wait after leaving combat, or after drawing manually, before the forced sheathe. Attacking, blocking, being airborne or re-entering combat restarts the wait.\");\n"
        "\n"
        "\t\t\tImGuiMCP::Toggle(\"Leave bound weapons drawn\", &automation::exemptBoundWeapons);\n"
        "\t\t\tHelpMarker(\"Skips the forced sheathe while a bound (conjured) weapon is drawn, so it is not dismissed early - it still ends on its own duration or when you sheathe it yourself.\");",
        "\t\t\tImGuiMCP::SeparatorText(strings::TR(\"AD_Automation\", \"Automation\"));\n"
        "\n"
        "\t\t\tImGuiMCP::Toggle(strings::TR(\"AD_AutoDraw\", \"Auto draw\"), &automation::enableAutoDraw);\n"
        "\t\t\tHelpMarker(strings::TR(\"AD_HelpAutoDraw\", \"Draws your weapon or magic the instant something targets you in combat.\"));\n"
        "\n"
        "\t\t\tImGuiMCP::Toggle(strings::TR(\"AD_AutoSheathe\", \"Auto sheathe\"), &automation::enableAutoSheathe);\n"
        "\t\t\tHelpMarker(strings::TR(\"AD_HelpAutoSheathe\", \"Sheathes your weapon or magic a set delay after you leave combat, or after you draw it manually.\"));\n"
        "\n"
        "\t\t\tNudgeableSlider(strings::TR(\"AD_SheatheDelay\", \"Sheathe delay\"), &automation::sheatheDelaySeconds, 0.5F, 30.0F, \"%.1f s\", 0.5F);\n"
        "\t\t\tHelpMarker(strings::TR(\"AD_HelpSheatheDelay\", \"How long to wait after leaving combat, or after drawing manually, before the forced sheathe. Attacking, blocking, being airborne or re-entering combat restarts the wait.\"));\n"
        "\n"
        "\t\t\tImGuiMCP::Toggle(strings::TR(\"AD_ExemptBound\", \"Leave bound weapons drawn\"), &automation::exemptBoundWeapons);\n"
        "\t\t\tHelpMarker(strings::TR(\"AD_HelpExemptBound\", \"Skips the forced sheathe while a bound (conjured) weapon is drawn, so it is not dismissed early - it still ends on its own duration or when you sheathe it yourself.\"));",
        "UI.cpp:RenderAutomationSection",
    )

    # --- RenderDebugSection: SeparatorText + Combo label + option list + HelpMarker ---------------
    text = apply_one(
        text,
        "\t\t\tImGuiMCP::SeparatorText(\"Debug\");\n"
        "\n"
        "\t\t\tint level = static_cast<int>(debug::logLevel);\n"
        "\t\t\tlevel = std::clamp(level, 0, kLogLevelCount - 1);\n"
        "\t\t\tif (ImGuiMCP::Combo(\"Log level\", &level, kLogLevelNames, kLogLevelCount))\n"
        "\t\t\t{\n"
        "\t\t\t\tdebug::logLevel = static_cast<std::uint32_t>(level);\n"
        "\t\t\t\tApplyLogLevel();\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(\"Applies immediately. The log is at Documents\\\\My Games\\\\Skyrim Special Edition\\\\SKSE\\\\AutoDraw.log. Set this to Trace or Debug before reproducing a bug you plan to report.\");",
        "\t\t\tImGuiMCP::SeparatorText(strings::TR(\"AD_Debug\", \"Debug\"));\n"
        "\n"
        "\t\t\tint level = static_cast<int>(debug::logLevel);\n"
        "\t\t\tlevel = std::clamp(level, 0, kLogLevelCount - 1);\n"
        "\t\t\t// Rebuilt from TR'd entries every frame (plan 2.2); labelStore owns the translated\n"
        "\t\t\t// bytes for this call so the const char* pointers handed to Combo stay valid.\n"
        "\t\t\tstd::vector<std::string> logLevelLabelStore;\n"
        "\t\t\tlogLevelLabelStore.reserve(kLogLevelCount);\n"
        "\t\t\tfor (int i = 0; i < kLogLevelCount; ++i)\n"
        "\t\t\t{\n"
        "\t\t\t\tlogLevelLabelStore.push_back(strings::TR(kLogLevelKeys[i], kLogLevelNames[i]));\n"
        "\t\t\t}\n"
        "\t\t\tstd::vector<const char*> logLevelLabels;\n"
        "\t\t\tlogLevelLabels.reserve(logLevelLabelStore.size());\n"
        "\t\t\tfor (const auto& s : logLevelLabelStore) { logLevelLabels.push_back(s.c_str()); }\n"
        "\t\t\tif (ImGuiMCP::Combo(strings::TR(\"AD_LogLevel\", \"Log level\"), &level, logLevelLabels.data(), kLogLevelCount))\n"
        "\t\t\t{\n"
        "\t\t\t\tdebug::logLevel = static_cast<std::uint32_t>(level);\n"
        "\t\t\t\tApplyLogLevel();\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"AD_HelpLogLevel\", \"Applies immediately. The log is at Documents\\\\My Games\\\\Skyrim Special Edition\\\\SKSE\\\\AutoDraw.log. Set this to Trace or Debug before reproducing a bug you plan to report.\"));",
        "UI.cpp:RenderDebugSection",
    )

    # --- kLogLevelNames block: add the parallel key array right after it --------------------------
    text = apply_one(
        text,
        "\t\tconstexpr const char* kLogLevelNames[] = { \"Trace\", \"Debug\", \"Info\", \"Warning\", \"Error\", \"Critical\", \"Off\" };\n"
        "\t\tconstexpr int kLogLevelCount = 7;",
        "\t\tconstexpr const char* kLogLevelNames[] = { \"Trace\", \"Debug\", \"Info\", \"Warning\", \"Error\", \"Critical\", \"Off\" };\n"
        "\t\tconstexpr const char* kLogLevelKeys[] = { \"AD_LogLevel_Trace\", \"AD_LogLevel_Debug\", \"AD_LogLevel_Info\",\n"
        "\t\t\t\t\t\t\t\t\t\t\t\t\t\"AD_LogLevel_Warning\", \"AD_LogLevel_Error\", \"AD_LogLevel_Critical\", \"AD_LogLevel_Off\" };\n"
        "\t\tconstexpr int kLogLevelCount = 7;",
        "UI.cpp:kLogLevelKeys",
    )

    # --- RenderButtons: Save / Reload / Restore buttons, their HelpMarkers, status assignments ----
    text = apply_one(
        text,
        "\t\t\tif (ImGuiMCP::Button(\"Save\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tstatusMessage = \"Saving...\";\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tstatusMessage = settings::Save() ? \"Settings saved.\" : \"Could not write the INI. See the log for why.\";\n"
        "\t\t\t\t});\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(\"Writes every setting on this page to the plugin's INI so it survives a restart.\");\n"
        "\n"
        "\t\t\tImGuiMCP::SameLine();\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(\"Reload from INI\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tstatusMessage = \"Reloading...\";\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tstatusMessage = settings::Reload() ? \"Settings reloaded from the INI.\"\n"
        "\t\t\t\t\t\t\t\t\t\t\t\t\t   : \"Could not read the INI. See the log for why.\";\n"
        "\t\t\t\t});\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(\"Throws away any change made here since the last save and re-reads the INI from disk. Also picks up edits made to the file by hand.\");\n"
        "\n"
        "\t\t\tImGuiMCP::SameLine();\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(\"Restore defaults\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tsettings::RestoreDefaults();\n"
        "\t\t\t\t\tlogger::debug(\"Restored default settings\");\n"
        "\t\t\t\t});\n"
        "\n"
        "\t\t\t\tstatusMessage = \"Defaults restored. Press Save to keep them.\";\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(\"Puts every setting back to the value it has on a fresh install. Nothing is written until you press Save.\");",
        "\t\t\tif (ImGuiMCP::Button(strings::TR(\"AD_SaveBtn\", \"Save\")))\n"
        "\t\t\t{\n"
        "\t\t\t\tstatusMessage = strings::TR(\"AD_StatusSaving\", \"Saving...\");\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tstatusMessage = settings::Save() ? strings::TR(\"AD_StatusSaved\", \"Settings saved.\")\n"
        "\t\t\t\t\t\t\t\t\t\t\t\t\t   : strings::TR(\"AD_StatusSaveFail\", \"Could not write the INI. See the log for why.\");\n"
        "\t\t\t\t});\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"AD_HelpSave\", \"Writes every setting on this page to the plugin's INI so it survives a restart.\"));\n"
        "\n"
        "\t\t\tImGuiMCP::SameLine();\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(strings::TR(\"AD_ReloadBtn\", \"Reload from INI\")))\n"
        "\t\t\t{\n"
        "\t\t\t\tstatusMessage = strings::TR(\"AD_StatusReloading\", \"Reloading...\");\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tstatusMessage = settings::Reload() ? strings::TR(\"AD_StatusReloaded\", \"Settings reloaded from the INI.\")\n"
        "\t\t\t\t\t\t\t\t\t\t\t\t\t   : strings::TR(\"AD_StatusReloadFail\", \"Could not read the INI. See the log for why.\");\n"
        "\t\t\t\t});\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"AD_HelpReload\", \"Throws away any change made here since the last save and re-reads the INI from disk. Also picks up edits made to the file by hand.\"));\n"
        "\n"
        "\t\t\tImGuiMCP::SameLine();\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(strings::TR(\"AD_RestoreBtn\", \"Restore defaults\")))\n"
        "\t\t\t{\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tsettings::RestoreDefaults();\n"
        "\t\t\t\t\tlogger::debug(\"Restored default settings\");\n"
        "\t\t\t\t});\n"
        "\n"
        "\t\t\t\tstatusMessage = strings::TR(\"AD_StatusRestored\", \"Defaults restored. Press Save to keep them.\");\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"AD_HelpRestore\", \"Puts every setting back to the value it has on a fresh install. Nothing is written until you press Save.\"));",
        "UI.cpp:RenderButtons",
    )

    # --- SettingsPanel::Render: strings::Tick() first, then the intro text ------------------------
    text = apply_one(
        text,
        "\tvoid __stdcall SettingsPanel::Render()\n"
        "\t{\n"
        "\t\tImGuiMCP::TextWrapped(\"Changes apply as soon as you make them. Press Save to keep them for the next time you play.\");",
        "\tvoid __stdcall SettingsPanel::Render()\n"
        "\t{\n"
        "\t\tstrings::Tick();\n"
        "\n"
        "\t\tImGuiMCP::TextWrapped(\"%s\", strings::TR(\"AD_Intro\", \"Changes apply as soon as you make them. Press Save to keep them for the next time you play.\"));",
        "UI.cpp:Render Tick+Intro",
    )

    write(path, text, crlf=True)


def main():
    patch_skse_menu_framework_h()
    patch_main_cpp()
    patch_devbench_tool_cpp()
    patch_ui_cpp()
    print("lang-patch.py: all anchors matched and patched.")


if __name__ == "__main__":
    main()
