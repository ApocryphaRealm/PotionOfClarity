#include "PCH.h"

#include "UI.h"

#include "SKSEMenuFramework.h"

#include "Clarity.h"
#include "Settings.h"
#include "Sslr.h"

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

		constexpr const char* kLogLevelNames[] = { "Trace", "Debug", "Info", "Warning", "Error", "Critical", "Off" };
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
			ImGuiMCP::TextDisabled("(?)");
			if (ImGuiMCP::IsItemHovered())
			{
				ImGuiMCP::SetTooltip("%s", a_description);
			}
		}

		void RenderGeneralSection()
		{
			using namespace settings;

			ImGuiMCP::SeparatorText("Potion of Clarity");

			float price = static_cast<float>(general::price);
			if (ImGuiMCP::SliderFloat("Price", &price, 0.0F, 1000.0F, "%.0f gold"))
			{
				general::price = static_cast<std::uint32_t>(std::clamp(price, 0.0F, 1000.0F) + 0.5F);
				OnMainThread([]() { Clarity::ApplyPrice(); });
			}
			HelpMarker("How much a Potion of Clarity costs - its gold value, which is what merchants charge for it (0 to 1000).");

			ImGuiMCP::Toggle("Static Skill Leveling Rewritten compatibility", &general::sslrCompat);
			HelpMarker("With Static Skill Leveling Rewritten installed, drinking the potion also resets every trained skill to its starting value (15 plus your racial bonus) and returns the skill points SSLR charged for the levels above it to its pool, to spend again at your next level-up. Off: perks only.");
			if (general::sslrCompat)
			{
				if (Sslr::IsDetected()) { ImGuiMCP::TextDisabled("SSLR detected - points pool: %d", Sslr::GetPointsPool()); }
				else { ImGuiMCP::TextDisabled("SSLR not detected - the toggle does nothing until it is installed."); }
			}

			const auto s = Clarity::GetState();
			if (!s.potionResolved)
			{
				ImGuiMCP::TextWrapped("PotionOfClarity.esl is not loaded - enable it in your mod manager or the potion cannot exist.");
			}
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
			HelpMarker("Applies immediately. The log is at Documents\\My Games\\Skyrim Special Edition\\SKSE\\PotionOfClarity.log.");
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
			HelpMarker("Throws away any change made here since the last save and re-reads the INI from disk.");

			ImGuiMCP::SameLine();

			if (ImGuiMCP::Button("Restore defaults"))
			{
				OnMainThread([]() {
					settings::RestoreDefaults();
					logger::debug("Restored default settings");
				});
				statusMessage = "Defaults restored. Press Save to keep them.";
			}
			HelpMarker("Puts every setting back to its fresh-install value. Nothing is written until you press Save.");

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
		ImGuiMCP::TextWrapped("Changes apply as soon as you make them. Press Save to keep them for the next time you play.");
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
