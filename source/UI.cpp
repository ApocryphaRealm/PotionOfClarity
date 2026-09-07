#include "PCH.h"

#include "UI.h"

#include "SKSEMenuFramework.h"

#include "Clarity.h"
#include "Settings.h"
#include "Sslr.h"

#include "utils/Logger.h"
#include "utils/Strings.h"
#include "utils/Toggle.h"

#include <algorithm>
#include <functional>
#include <string>
#include <vector>

namespace UI
{
	namespace
	{
		std::string statusMessage;

		constexpr const char* kLogLevelNames[] = { "Trace", "Debug", "Info", "Warning", "Error", "Critical", "Off" };
		constexpr const char* kLogLevelKeys[] = { "POC_LogLevel_Trace", "POC_LogLevel_Debug", "POC_LogLevel_Info",
													"POC_LogLevel_Warning", "POC_LogLevel_Error", "POC_LogLevel_Critical", "POC_LogLevel_Off" };
		constexpr int kLogLevelCount = 7;

		void OnMainThread(std::function<void()> a_task)
		{
			if (auto* taskInterface = SKSE::GetTaskInterface())
			{
				taskInterface->AddTask(std::move(a_task));
			}
		}

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
				"igIsItemHovered",
				"igButton",
				"igSameLine",
				"igSpacing",
				"igPushItemWidth",
				"igPopItemWidth",
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

		void HelpMarker(const char* a_description)
		{
			ImGuiMCP::SameLine();
			ImGuiMCP::TextDisabled("%s", strings::TR("POC_HelpMark", "(?)"));
			if (ImGuiMCP::IsItemHovered())
			{
				ImGuiMCP::SetTooltip("%s", a_description);
			}
		}

		void RenderGeneralSection()
		{
			using namespace settings;

			ImGuiMCP::SeparatorText(strings::TR("POC_Title", "Potion of Clarity"));

			float price = static_cast<float>(general::price);
			if (ImGuiMCP::SliderFloat(strings::TR("POC_Price", "Price"), &price, 0.0F, 1000.0F, strings::TR("POC_PriceFormat", "%.0f gold")))
			{
				general::price = static_cast<std::uint32_t>(std::clamp(price, 0.0F, 1000.0F) + 0.5F);
				OnMainThread([]() { Clarity::ApplyPrice(); });
			}
			HelpMarker(strings::TR("POC_HelpPrice", "How much a Potion of Clarity costs - its gold value, which is what merchants charge for it (0 to 1000)."));

			ImGuiMCP::Toggle(strings::TR("POC_SslrToggle", "Static Skill Leveling Rewritten compatibility"), &general::sslrCompat);
			HelpMarker(strings::TR("POC_HelpSslrToggle", "With Static Skill Leveling Rewritten installed, drinking the potion also resets every trained skill to its starting value (15 plus your racial bonus) and returns the skill points SSLR charged for the levels above it to its pool, to spend again at your next level-up. Off: perks only."));
			if (general::sslrCompat)
			{
				if (Sslr::IsDetected()) { ImGuiMCP::TextDisabled(strings::TR("POC_SslrDetected", "SSLR detected - points pool: %d"), Sslr::GetPointsPool()); }
				else { ImGuiMCP::TextDisabled("%s", strings::TR("POC_SslrNotDetected", "SSLR not detected - the toggle does nothing until it is installed.")); }
			}

			ImGuiMCP::Toggle(strings::TR("POC_CpcToggle", "Character Progression Control compatibility"), &general::cpcCompat);
			HelpMarker(strings::TR("POC_HelpCpcToggle", "With Character Progression Control installed and using skill points, drinking the potion also asks it to reset every trained skill to its starting value and return the points it charged to its bank. It does nothing otherwise. On by default."));
			if (general::cpcCompat)
			{
				if (GetModuleHandleA("CharacterProgressionControl.dll")) { ImGuiMCP::Text("%s", strings::TR("POC_CpcDetected", "Character Progression Control detected.")); }
				else { ImGuiMCP::Text("%s", strings::TR("POC_CpcNotDetected", "Character Progression Control not detected - the toggle does nothing until it is installed.")); }
			}

			const auto s = Clarity::GetState();
			if (!s.potionResolved)
			{
				ImGuiMCP::TextWrapped("%s", strings::TR("POC_EslNotLoaded", "PotionOfClarity.esl is not loaded - enable it in your mod manager or the potion cannot exist."));
			}
		}

		void RenderDebugSection()
		{
			using namespace settings;

			ImGuiMCP::SeparatorText(strings::TR("POC_Debug", "Debug"));

			int level = static_cast<int>(debug::logLevel);
			level = std::clamp(level, 0, kLogLevelCount - 1);
			// Rebuilt from TR'd entries every frame (plan 2.2); labelStore owns the translated
			// bytes for this call so the const char* pointers handed to Combo stay valid.
			std::vector<std::string> logLevelLabelStore;
			logLevelLabelStore.reserve(kLogLevelCount);
			for (int i = 0; i < kLogLevelCount; ++i)
			{
				logLevelLabelStore.push_back(strings::TR(kLogLevelKeys[i], kLogLevelNames[i]));
			}
			std::vector<const char*> logLevelLabels;
			logLevelLabels.reserve(logLevelLabelStore.size());
			for (const auto& s : logLevelLabelStore) { logLevelLabels.push_back(s.c_str()); }
			if (ImGuiMCP::Combo(strings::TR("POC_LogLevel", "Log level"), &level, logLevelLabels.data(), kLogLevelCount))
			{
				debug::logLevel = static_cast<std::uint32_t>(level);
				ApplyLogLevel();
			}
			HelpMarker(strings::TR("POC_HelpLogLevel", "Applies immediately. The log is at Documents\\My Games\\Skyrim Special Edition\\SKSE\\PotionOfClarity.log."));
		}

		void RenderButtons()
		{
			ImGuiMCP::SeparatorText("");

			if (ImGuiMCP::Button(strings::TR("POC_SaveBtn", "Save")))
			{
				statusMessage = strings::TR("POC_StatusSaving", "Saving...");
				OnMainThread([]() {
					statusMessage = settings::Save() ? strings::TR("POC_StatusSaved", "Settings saved.")
													   : strings::TR("POC_StatusSaveFail", "Could not write the INI. See the log for why.");
				});
			}
			HelpMarker(strings::TR("POC_HelpSave", "Writes every setting on this page to the plugin's INI so it survives a restart."));

			ImGuiMCP::SameLine();

			if (ImGuiMCP::Button(strings::TR("POC_ReloadBtn", "Reload from INI")))
			{
				statusMessage = strings::TR("POC_StatusReloading", "Reloading...");
				OnMainThread([]() {
					statusMessage = settings::Reload() ? strings::TR("POC_StatusReloaded", "Settings reloaded from the INI.")
													   : strings::TR("POC_StatusReloadFail", "Could not read the INI. See the log for why.");
				});
			}
			HelpMarker(strings::TR("POC_HelpReload", "Throws away any change made here since the last save and re-reads the INI from disk."));

			ImGuiMCP::SameLine();

			if (ImGuiMCP::Button(strings::TR("POC_RestoreBtn", "Restore defaults")))
			{
				OnMainThread([]() {
					settings::RestoreDefaults();
					logger::debug("Restored default settings");
				});
				statusMessage = strings::TR("POC_StatusRestored", "Defaults restored. Press Save to keep them.");
			}
			HelpMarker(strings::TR("POC_HelpRestore", "Puts every setting back to its fresh-install value. Nothing is written until you press Save."));

			if (!statusMessage.empty())
			{
				ImGuiMCP::TextWrapped("%s", statusMessage.c_str());
			}

			ImGuiMCP::Spacing();
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
						 "Framework version 3 or newer).");
			return;
		}

		SKSEMenuFramework::SetSection("Potion of Clarity");
		SKSEMenuFramework::AddSectionItem("Settings", SettingsPanel::Render);
		logger::info("Registered the settings page with the menu framework");
	}

	void __stdcall SettingsPanel::Render()
	{
		strings::Tick();

		ImGuiMCP::TextWrapped("%s", strings::TR("POC_Intro", "Changes apply as soon as you make them. Press Save to keep them for the next time you play."));
		ImGuiMCP::Spacing();

		ImGuiMCP::PushItemWidth(260.0F);

		RenderGeneralSection();
		ImGuiMCP::Spacing();

		RenderDebugSection();
		ImGuiMCP::Spacing();

		ImGuiMCP::PopItemWidth();

		RenderButtons();
	}
}
