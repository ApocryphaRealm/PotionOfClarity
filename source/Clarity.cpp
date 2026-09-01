#include "PCH.h"

#include "Clarity.h"

#include "Settings.h"
#include "utils/Logger.h"

#include <algorithm>
#include <chrono>
#include <mutex>
#include <vector>

namespace Clarity
{
	namespace
	{
		// The contract with PotionOfClarity.esl (tools/Build-PotionOfClarityEsl.py):
		// 0x800 MGEF (inert), 0x801 ALCH (the potion), 0x802 COBJ (cookpot recipe).
		constexpr const char* kPluginFileName = "PotionOfClarity.esl";
		constexpr RE::FormID kPotionLocalFormID = 0x801;
		constexpr std::uint32_t kSkillCount = 18;  // kOneHanded (6) .. kEnchanting (23), contiguous

		RE::TESBoundObject* g_potion = nullptr;
		bool g_sinkRegistered = false;

		std::mutex g_stateLock;
		State g_state;
		std::chrono::steady_clock::time_point g_lastWalk{};

		// Depth-first over one skill's perk tree. Trees share nodes, so a visited guard is
		// required or shared nodes would be counted twice.
		void CollectNodePerks(RE::BGSSkillPerkTreeNode* a_node, std::vector<RE::BGSSkillPerkTreeNode*>& a_visited,
							  std::vector<RE::BGSPerk*>& a_out)
		{
			if (!a_node || std::ranges::find(a_visited, a_node) != a_visited.end()) { return; }
			a_visited.push_back(a_node);

			// Every rank of a multi-rank perk is its own BGSPerk, chained through nextPerk -
			// each rank is one point the player spent.
			for (RE::BGSPerk* rank = a_node->perk; rank; rank = rank->nextPerk) { a_out.push_back(rank); }
			for (RE::BGSSkillPerkTreeNode* child : a_node->children) { CollectNodePerks(child, a_visited, a_out); }
		}

		std::vector<RE::BGSPerk*> CollectAllTreePerks()
		{
			std::vector<RE::BGSPerk*> perks;
			auto* avList = RE::ActorValueList::GetSingleton();
			if (!avList)
			{
				logger::error("ActorValueList singleton unavailable; cannot enumerate perk trees");
				return perks;
			}
			for (std::uint32_t i = 0; i < kSkillCount; ++i)
			{
				const auto av = static_cast<RE::ActorValue>(static_cast<std::uint32_t>(RE::ActorValue::kOneHanded) + i);
				auto* info = avList->GetActorValue(av);
				if (!info || !info->perkTree) { continue; }
				std::vector<RE::BGSSkillPerkTreeNode*> visited;
				CollectNodePerks(info->perkTree, visited, perks);
			}
			return perks;
		}

		std::vector<RE::BGSPerk*> CollectOwnedTreePerks(RE::PlayerCharacter* a_player)
		{
			std::vector<RE::BGSPerk*> owned;
			for (RE::BGSPerk* perk : CollectAllTreePerks())
			{
				if (perk && a_player->HasPerk(perk)) { owned.push_back(perk); }
			}
			return owned;
		}

		void RefreshCounts(RE::PlayerCharacter* a_player)
		{
			const auto owned = CollectOwnedTreePerks(a_player);
			std::scoped_lock l(g_stateLock);
			g_state.spentPerks = static_cast<std::uint32_t>(owned.size());
			g_state.perkPoints = a_player->GetGameStatsData().perkCount;
		}

		// Drinking a potion is an EQUIP in this engine - TESEquipEvent is what fires. One
		// integer compare rejects every unrelated equip before anything is dereferenced.
		class EquipSink : public RE::BSTEventSink<RE::TESEquipEvent>
		{
		public:
			static EquipSink* GetSingleton()
			{
				static EquipSink singleton;
				return &singleton;
			}

			RE::BSEventNotifyControl ProcessEvent(const RE::TESEquipEvent* a_event, RE::BSTEventSource<RE::TESEquipEvent>*) override
			{
				if (!a_event || !g_potion || a_event->baseObject != g_potion->GetFormID() || !a_event->equipped)
				{
					return RE::BSEventNotifyControl::kContinue;
				}

				auto* player = RE::PlayerCharacter::GetSingleton();
				if (!player || !a_event->actor || a_event->actor.get() != static_cast<RE::TESObjectREFR*>(player))
				{
					// An NPC drinking it does nothing - perk points are the player's alone.
					logger::debug("Potion of Clarity consumed by a non-player actor; ignoring");
					return RE::BSEventNotifyControl::kContinue;
				}

				if (!settings::general::enabled)
				{
					logger::info("Potion of Clarity consumed while the mod is disabled (bEnabled=0); no refund");
					RE::DebugNotification("Potion of Clarity is disabled in its settings.");
					return RE::BSEventNotifyControl::kContinue;
				}

				logger::info("Potion of Clarity consumed by the player");
				const Result r = Refund();
				RE::DebugNotification(r.message.c_str());
				return RE::BSEventNotifyControl::kContinue;
			}
		};
	}

	void Install()
	{
		if (g_sinkRegistered) { return; }

		auto* dataHandler = RE::TESDataHandler::GetSingleton();
		if (!dataHandler)
		{
			logger::warn("TESDataHandler unavailable at kDataLoaded; the potion cannot be resolved");
			return;
		}

		RE::TESForm* form = dataHandler->LookupForm(kPotionLocalFormID, kPluginFileName);
		if (!form)
		{
			logger::error("{} is not in the load order (or 0x{:03X} is not in it) - the potion cannot exist, so nothing will "
						  "trigger a refund. Install the plugin that ships with this mod.",
						  kPluginFileName, kPotionLocalFormID);
			return;
		}

		g_potion = form->As<RE::TESBoundObject>();
		if (!g_potion)
		{
			logger::error("{} 0x{:03X} resolved but is not an inventory object (type {})", kPluginFileName, kPotionLocalFormID,
						  static_cast<int>(form->GetFormType()));
			return;
		}

		auto* holder = RE::ScriptEventSourceHolder::GetSingleton();
		if (!holder)
		{
			logger::warn("ScriptEventSourceHolder unavailable; the potion will not trigger a refund");
			return;
		}
		holder->AddEventSink<RE::TESEquipEvent>(EquipSink::GetSingleton());
		g_sinkRegistered = true;

		{
			std::scoped_lock l(g_stateLock);
			g_state.potionResolved = true;
			g_state.potionFormID = form->GetFormID();
		}
		logger::info("Potion of Clarity resolved from {} at 0x{:08X} (\"{}\"); consume sink registered",
					 kPluginFileName, form->GetFormID(), form->GetName());
	}

	Result Refund()
	{
		Result result;
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!player)
		{
			result.message = "Could not find the player character.";
			logger::error("Refund: PlayerCharacter singleton unavailable");
			return result;
		}

		const auto owned = CollectOwnedTreePerks(player);
		result.perksRemoved = static_cast<std::uint32_t>(owned.size());

		if (owned.empty())
		{
			result.success = true;
			result.message = "Clarity: no spent perks to return.";
			logger::info("Refund: the player owns no tree perks; nothing to do");
			RefreshCounts(player);
			std::scoped_lock l(g_stateLock);
			g_state.lastMessage = result.message;
			return result;
		}

		for (RE::BGSPerk* perk : owned)
		{
			player->RemovePerk(perk);
			logger::trace("Refund: removed \"{}\" (0x{:08X})", perk->GetFullName(), perk->GetFormID());
		}

		// perkCount is a signed byte the game saves itself; clamp instead of wrapping.
		auto& stats = player->GetGameStatsData();
		const int before = static_cast<int>(stats.perkCount);
		const int after = std::clamp(before + static_cast<int>(owned.size()), 0, 127);
		stats.perkCount = static_cast<std::int8_t>(after);
		result.pointsRefunded = static_cast<std::uint32_t>(after - before);
		if (result.pointsRefunded != owned.size())
		{
			logger::warn("Refund: perk points capped at 127 - {} of {} point(s) could not be banked", owned.size() - result.pointsRefunded, owned.size());
		}

		result.success = true;
		result.message = std::format("Clarity: {} perk{} returned as {} perk point{}.", owned.size(), owned.size() == 1 ? "" : "s",
									 result.pointsRefunded, result.pointsRefunded == 1 ? "" : "s");
		logger::info("Refund: {} (perk points {} -> {})", result.message, before, after);

		RefreshCounts(player);
		std::scoped_lock l(g_stateLock);
		g_state.refunds += 1;
		g_state.lastMessage = result.message;
		return result;
	}

	void RequestRefund()
	{
		if (auto* tasks = SKSE::GetTaskInterface()) { tasks->AddTask([]() { Refund(); }); }
	}

	State GetState()
	{
		// The settings page renders every frame; re-walk the trees at most once a second and
		// only from the main thread's render callback (the UI is the only caller).
		const auto now = std::chrono::steady_clock::now();
		if (now - g_lastWalk > std::chrono::seconds(1))
		{
			g_lastWalk = now;
			if (auto* player = RE::PlayerCharacter::GetSingleton(); player && player->Is3DLoaded()) { RefreshCounts(player); }
		}
		std::scoped_lock l(g_stateLock);
		return g_state;
	}

	RE::TESBoundObject* GetPotion() { return g_potion; }
}
