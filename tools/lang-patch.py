# -*- coding: utf-8 -*-
"""lang-patch.py - one-shot, re-runnable language-support patch for Potion of Clarity.

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
    with open(path, "r", encoding="utf-8", newline=None) as f:
        return f.read()


def write(path, text, crlf=False):
    with open(path, "w", encoding="utf-8", newline="\r\n" if crlf else "\n") as f:
        f.write(text)


def apply_one(text, anchor, replacement, label, done_marker=None):
    if done_marker is not None and done_marker in text:
        return text
    n = text.count(anchor)
    if n != 1:
        raise RuntimeError("[{}] anchor found {} time(s), expected exactly 1:\n{!r}".format(label, n, anchor))
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
# 2) source/main.cpp - strings::Configure("PotionOfClarity") at kDataLoaded.
# ------------------------------------------------------------------------------------------------
def patch_main_cpp():
    path = os.path.join(REPO, "source", "main.cpp")
    text = read(path)
    if 'strings::Configure("PotionOfClarity")' in text:
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
        "\t\t\tClarity::Install();\n"
        "\t\t\tSslr::Install();\n"
        "\t\t\tDevBenchTool::Init(true);\n"
        "\t\t\tbreak;"
    )
    replacement = (
        "\t\tcase SKSE::MessagingInterface::kDataLoaded:\n"
        "\t\t\tstrings::Configure(\"PotionOfClarity\");\n"
        "\t\t\tUI::Register();\n"
        "\t\t\tClarity::Install();\n"
        "\t\t\tSslr::Install();\n"
        "\t\t\tDevBenchTool::Init(true);\n"
        "\t\t\tbreak;"
    )
    text = apply_one(text, anchor, replacement, "main.cpp:kDataLoaded")
    write(path, text, crlf=True)


# ------------------------------------------------------------------------------------------------
# 3) source/DevBenchTool.cpp - a "strings" op returning strings::StatusJson(); descriptor updated.
# ------------------------------------------------------------------------------------------------
def patch_devbench_tool_cpp():
    path = os.path.join(REPO, "source", "DevBenchTool.cpp")
    text = read(path)

    text = apply_one(
        text,
        "#include \"Sslr.h\"\n#include \"utils/Logger.h\"\n",
        "#include \"Sslr.h\"\n#include \"utils/Logger.h\"\n#include \"utils/Strings.h\"\n",
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
        "\"owned tree perks, perk points, lifetime refunds. op=give adds one potion; op=drink consumes one through \"\n"
        "\t\t\t\"the equip manager (the real path); op=refund refunds directly; op=sslr:on / sslr:off toggle SSLR compat; op=sslr:refund runs the SSLR skill refund alone; op=reload re-reads the INI.\\\",\"\n",
        "\"owned tree perks, perk points, lifetime refunds. op=give adds one potion; op=drink consumes one through \"\n"
        "\t\t\t\"the equip manager (the real path); op=refund refunds directly; op=sslr:on / sslr:off toggle SSLR compat; op=sslr:refund runs the SSLR skill refund alone; op=reload re-reads the INI; \"\n"
        "\t\t\t\"op=strings reports the active language, source and loaded translation count.\\\",\"\n",
        "DevBenchTool.cpp:descriptor",
    )
    write(path, text, crlf=True)


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

    # --- kLogLevelNames block: add the parallel key array right after it --------------------------
    text = apply_one(
        text,
        "\t\tconstexpr const char* kLogLevelNames[] = { \"Trace\", \"Debug\", \"Info\", \"Warning\", \"Error\", \"Critical\", \"Off\" };\n"
        "\t\tconstexpr int kLogLevelCount = 7;",
        "\t\tconstexpr const char* kLogLevelNames[] = { \"Trace\", \"Debug\", \"Info\", \"Warning\", \"Error\", \"Critical\", \"Off\" };\n"
        "\t\tconstexpr const char* kLogLevelKeys[] = { \"POC_LogLevel_Trace\", \"POC_LogLevel_Debug\", \"POC_LogLevel_Info\",\n"
        "\t\t\t\t\t\t\t\t\t\t\t\t\t\"POC_LogLevel_Warning\", \"POC_LogLevel_Error\", \"POC_LogLevel_Critical\", \"POC_LogLevel_Off\" };\n"
        "\t\tconstexpr int kLogLevelCount = 7;",
        "UI.cpp:kLogLevelKeys",
    )

    # --- HelpMarker: the "(?)" indicator (the tooltip text passed in is TR'd at each call site) ---
    text = apply_one(
        text,
        "\t\t\tImGuiMCP::SameLine();\n"
        "\t\t\tImGuiMCP::TextDisabled(\"(?)\");\n"
        "\t\t\tif (ImGuiMCP::IsItemHovered())\n"
        "\t\t\t{\n"
        "\t\t\t\tImGuiMCP::SetTooltip(\"%s\", a_description);\n"
        "\t\t\t}",
        "\t\t\tImGuiMCP::SameLine();\n"
        "\t\t\tImGuiMCP::TextDisabled(\"%s\", strings::TR(\"POC_HelpMark\", \"(?)\"));\n"
        "\t\t\tif (ImGuiMCP::IsItemHovered())\n"
        "\t\t\t{\n"
        "\t\t\t\tImGuiMCP::SetTooltip(\"%s\", a_description);\n"
        "\t\t\t}",
        "UI.cpp:HelpMarker",
    )

    # --- RenderGeneralSection: title, price slider + help, SSLR toggle + help + status, CPC toggle
    #     + help + status, ESL-not-loaded warning ---------------------------------------------------
    text = apply_one(
        text,
        "\t\t\tImGuiMCP::SeparatorText(\"Potion of Clarity\");\n"
        "\n"
        "\t\t\tfloat price = static_cast<float>(general::price);\n"
        "\t\t\tif (ImGuiMCP::SliderFloat(\"Price\", &price, 0.0F, 1000.0F, \"%.0f gold\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tgeneral::price = static_cast<std::uint32_t>(std::clamp(price, 0.0F, 1000.0F) + 0.5F);\n"
        "\t\t\t\tOnMainThread([]() { Clarity::ApplyPrice(); });\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(\"How much a Potion of Clarity costs - its gold value, which is what merchants charge for it (0 to 1000).\");\n"
        "\n"
        "\t\t\tImGuiMCP::Toggle(\"Static Skill Leveling Rewritten compatibility\", &general::sslrCompat);\n"
        "\t\t\tHelpMarker(\"With Static Skill Leveling Rewritten installed, drinking the potion also resets every trained skill to its starting value (15 plus your racial bonus) and returns the skill points SSLR charged for the levels above it to its pool, to spend again at your next level-up. Off: perks only.\");\n"
        "\t\t\tif (general::sslrCompat)\n"
        "\t\t\t{\n"
        "\t\t\t\tif (Sslr::IsDetected()) { ImGuiMCP::TextDisabled(\"SSLR detected - points pool: %d\", Sslr::GetPointsPool()); }\n"
        "\t\t\t\telse { ImGuiMCP::TextDisabled(\"SSLR not detected - the toggle does nothing until it is installed.\"); }\n"
        "\t\t\t}\n"
        "\n"
        "\t\t\tImGuiMCP::Toggle(\"Character Progression Control compatibility\", &general::cpcCompat);\n"
        "\t\t\tHelpMarker(\"With Character Progression Control installed and using skill points, drinking the potion also asks it to reset every trained skill to its starting value and return the points it charged to its bank. It does nothing otherwise. On by default.\");\n"
        "\t\t\tif (general::cpcCompat)\n"
        "\t\t\t{\n"
        "\t\t\t\tif (GetModuleHandleA(\"CharacterProgressionControl.dll\")) { ImGuiMCP::Text(\"Character Progression Control detected.\"); }\n"
        "\t\t\t\telse { ImGuiMCP::Text(\"Character Progression Control not detected - the toggle does nothing until it is installed.\"); }\n"
        "\t\t\t}\n"
        "\n"
        "\t\t\tconst auto s = Clarity::GetState();\n"
        "\t\t\tif (!s.potionResolved)\n"
        "\t\t\t{\n"
        "\t\t\t\tImGuiMCP::TextWrapped(\"PotionOfClarity.esl is not loaded - enable it in your mod manager or the potion cannot exist.\");\n"
        "\t\t\t}",
        "\t\t\tImGuiMCP::SeparatorText(strings::TR(\"POC_Title\", \"Potion of Clarity\"));\n"
        "\n"
        "\t\t\tfloat price = static_cast<float>(general::price);\n"
        "\t\t\tif (ImGuiMCP::SliderFloat(strings::TR(\"POC_Price\", \"Price\"), &price, 0.0F, 1000.0F, strings::TR(\"POC_PriceFormat\", \"%.0f gold\")))\n"
        "\t\t\t{\n"
        "\t\t\t\tgeneral::price = static_cast<std::uint32_t>(std::clamp(price, 0.0F, 1000.0F) + 0.5F);\n"
        "\t\t\t\tOnMainThread([]() { Clarity::ApplyPrice(); });\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"POC_HelpPrice\", \"How much a Potion of Clarity costs - its gold value, which is what merchants charge for it (0 to 1000).\"));\n"
        "\n"
        "\t\t\tImGuiMCP::Toggle(strings::TR(\"POC_SslrToggle\", \"Static Skill Leveling Rewritten compatibility\"), &general::sslrCompat);\n"
        "\t\t\tHelpMarker(strings::TR(\"POC_HelpSslrToggle\", \"With Static Skill Leveling Rewritten installed, drinking the potion also resets every trained skill to its starting value (15 plus your racial bonus) and returns the skill points SSLR charged for the levels above it to its pool, to spend again at your next level-up. Off: perks only.\"));\n"
        "\t\t\tif (general::sslrCompat)\n"
        "\t\t\t{\n"
        "\t\t\t\tif (Sslr::IsDetected()) { ImGuiMCP::TextDisabled(strings::TR(\"POC_SslrDetected\", \"SSLR detected - points pool: %d\"), Sslr::GetPointsPool()); }\n"
        "\t\t\t\telse { ImGuiMCP::TextDisabled(\"%s\", strings::TR(\"POC_SslrNotDetected\", \"SSLR not detected - the toggle does nothing until it is installed.\")); }\n"
        "\t\t\t}\n"
        "\n"
        "\t\t\tImGuiMCP::Toggle(strings::TR(\"POC_CpcToggle\", \"Character Progression Control compatibility\"), &general::cpcCompat);\n"
        "\t\t\tHelpMarker(strings::TR(\"POC_HelpCpcToggle\", \"With Character Progression Control installed and using skill points, drinking the potion also asks it to reset every trained skill to its starting value and return the points it charged to its bank. It does nothing otherwise. On by default.\"));\n"
        "\t\t\tif (general::cpcCompat)\n"
        "\t\t\t{\n"
        "\t\t\t\tif (GetModuleHandleA(\"CharacterProgressionControl.dll\")) { ImGuiMCP::Text(\"%s\", strings::TR(\"POC_CpcDetected\", \"Character Progression Control detected.\")); }\n"
        "\t\t\t\telse { ImGuiMCP::Text(\"%s\", strings::TR(\"POC_CpcNotDetected\", \"Character Progression Control not detected - the toggle does nothing until it is installed.\")); }\n"
        "\t\t\t}\n"
        "\n"
        "\t\t\tconst auto s = Clarity::GetState();\n"
        "\t\t\tif (!s.potionResolved)\n"
        "\t\t\t{\n"
        "\t\t\t\tImGuiMCP::TextWrapped(\"%s\", strings::TR(\"POC_EslNotLoaded\", \"PotionOfClarity.esl is not loaded - enable it in your mod manager or the potion cannot exist.\"));\n"
        "\t\t\t}",
        "UI.cpp:RenderGeneralSection",
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
        "\t\t\tHelpMarker(\"Applies immediately. The log is at Documents\\\\My Games\\\\Skyrim Special Edition\\\\SKSE\\\\PotionOfClarity.log.\");",
        "\t\t\tImGuiMCP::SeparatorText(strings::TR(\"POC_Debug\", \"Debug\"));\n"
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
        "\t\t\tif (ImGuiMCP::Combo(strings::TR(\"POC_LogLevel\", \"Log level\"), &level, logLevelLabels.data(), kLogLevelCount))\n"
        "\t\t\t{\n"
        "\t\t\t\tdebug::logLevel = static_cast<std::uint32_t>(level);\n"
        "\t\t\t\tApplyLogLevel();\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"POC_HelpLogLevel\", \"Applies immediately. The log is at Documents\\\\My Games\\\\Skyrim Special Edition\\\\SKSE\\\\PotionOfClarity.log.\"));",
        "UI.cpp:RenderDebugSection",
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
        "\t\t\tHelpMarker(\"Throws away any change made here since the last save and re-reads the INI from disk.\");\n"
        "\n"
        "\t\t\tImGuiMCP::SameLine();\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(\"Restore defaults\"))\n"
        "\t\t\t{\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tsettings::RestoreDefaults();\n"
        "\t\t\t\t\tlogger::debug(\"Restored default settings\");\n"
        "\t\t\t\t});\n"
        "\t\t\t\tstatusMessage = \"Defaults restored. Press Save to keep them.\";\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(\"Puts every setting back to its fresh-install value. Nothing is written until you press Save.\");",
        "\t\t\tif (ImGuiMCP::Button(strings::TR(\"POC_SaveBtn\", \"Save\")))\n"
        "\t\t\t{\n"
        "\t\t\t\tstatusMessage = strings::TR(\"POC_StatusSaving\", \"Saving...\");\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tstatusMessage = settings::Save() ? strings::TR(\"POC_StatusSaved\", \"Settings saved.\")\n"
        "\t\t\t\t\t\t\t\t\t\t\t\t\t   : strings::TR(\"POC_StatusSaveFail\", \"Could not write the INI. See the log for why.\");\n"
        "\t\t\t\t});\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"POC_HelpSave\", \"Writes every setting on this page to the plugin's INI so it survives a restart.\"));\n"
        "\n"
        "\t\t\tImGuiMCP::SameLine();\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(strings::TR(\"POC_ReloadBtn\", \"Reload from INI\")))\n"
        "\t\t\t{\n"
        "\t\t\t\tstatusMessage = strings::TR(\"POC_StatusReloading\", \"Reloading...\");\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tstatusMessage = settings::Reload() ? strings::TR(\"POC_StatusReloaded\", \"Settings reloaded from the INI.\")\n"
        "\t\t\t\t\t\t\t\t\t\t\t\t\t   : strings::TR(\"POC_StatusReloadFail\", \"Could not read the INI. See the log for why.\");\n"
        "\t\t\t\t});\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"POC_HelpReload\", \"Throws away any change made here since the last save and re-reads the INI from disk.\"));\n"
        "\n"
        "\t\t\tImGuiMCP::SameLine();\n"
        "\n"
        "\t\t\tif (ImGuiMCP::Button(strings::TR(\"POC_RestoreBtn\", \"Restore defaults\")))\n"
        "\t\t\t{\n"
        "\t\t\t\tOnMainThread([]() {\n"
        "\t\t\t\t\tsettings::RestoreDefaults();\n"
        "\t\t\t\t\tlogger::debug(\"Restored default settings\");\n"
        "\t\t\t\t});\n"
        "\t\t\t\tstatusMessage = strings::TR(\"POC_StatusRestored\", \"Defaults restored. Press Save to keep them.\");\n"
        "\t\t\t}\n"
        "\t\t\tHelpMarker(strings::TR(\"POC_HelpRestore\", \"Puts every setting back to its fresh-install value. Nothing is written until you press Save.\"));",
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
        "\t\tImGuiMCP::TextWrapped(\"%s\", strings::TR(\"POC_Intro\", \"Changes apply as soon as you make them. Press Save to keep them for the next time you play.\"));",
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
