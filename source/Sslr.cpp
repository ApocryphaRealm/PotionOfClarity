#include "PCH.h"

#include "Sslr.h"

#include "utils/Logger.h"

#include <algorithm>
#include <cmath>
#include <format>

namespace Sslr
{
	namespace
	{
		constexpr const char* kPlugin = "StaticSkillLeveling.esp";
		constexpr RE::FormID kGlobPointsLeft = 0xB12;   // SSL_PointsLeftAfterLvlUp
		constexpr RE::FormID kGlobCost0 = 0xD81;        // SSL_SkillPointCost0  (below 25)
		constexpr RE::FormID kGlobCost25 = 0xD82;       // SSL_SkillPointCost25 (25..49)
		constexpr RE::FormID kGlobCost50 = 0xD83;       // SSL_SkillPointCost50 (50..74)
		constexpr RE::FormID kGlobCost75 = 0xD84;       // SSL_SkillPointCost75 (75+)
		constexpr RE::FormID kQuest = 0xD7E;            // StaticSkillLevelingQuest
		constexpr const char* kQuestScript = "StaticSkillLevelingQuestScript";
		constexpr const char* kPointsProperty = "PointsLeftAfterLvlUp";
		constexpr int kSkillBase = 15;                  // fallback if the player's NPC record is unreadable
		constexpr std::uint32_t kFirstSkill = 6;        // kOneHanded
		constexpr std::uint32_t kSkillCount = 18;       // .. kEnchanting (23)

		bool g_detected = false;
		RE::TESGlobal* g_points = nullptr;
		RE::TESGlobal* g_cost[4] = { nullptr, nullptr, nullptr, nullptr };
		RE::TESQuest* g_quest = nullptr;

		// A skill's untrained value. Two readings, take the higher: (a) the player's own NPC record
		// (DNAM skill base) - vanilla writes 15 there, but on a live character the game has been seen
		// holding the race-adjusted start there already (20 for a Nord's One-Handed, gate 2026-09-01),
		// and character-start mods may edit it; (b) 15 plus the RACE record's skill boost, which is
		// how the game composes a fresh character's start (race overhauls and custom races edit it).
		// max() is right in every observed case: 15+boost when DNAM is the vanilla 15, DNAM when it
		// already includes the boost. Only levels ABOVE this were bought with SSLR points.
		int StartingLevel(RE::PlayerCharacter* a_player, RE::ActorValue a_skill)
		{
			int fromRecord = kSkillBase;
			const std::uint32_t index = static_cast<std::uint32_t>(a_skill) - kFirstSkill;
			if (auto* base = a_player->GetActorBase(); base && index < RE::TESNPC::Skills::kTotal)
			{
				fromRecord = static_cast<int>(base->playerSkills.values[index]);
			}
			int fromRace = kSkillBase;
			if (auto* race = a_player->GetRace())
			{
				for (const auto& boost : race->data.skillBoosts)
				{
					if (boost.skill.get() == a_skill) { fromRace += static_cast<int>(boost.bonus); }
				}
			}
			logger::trace("SSLR: skill {} starting value: record {} / race {} -> {}", static_cast<int>(a_skill), fromRecord, fromRace, std::max(fromRecord, fromRace));
			return std::max(fromRecord, fromRace);
		}

		int CostForLevel(int a_level)
		{
			const int tier = a_level < 25 ? 0 : a_level < 50 ? 1 : a_level < 75 ? 2 : 3;
			return g_cost[tier] ? static_cast<int>(std::lround(g_cost[tier]->value)) : 0;
		}

		// Script variants keep the pool as an Int property on the quest script; add there too
		// when such a property exists, so whichever variant is installed sees the refund.
		bool AddToScriptProperty(std::int32_t a_add)
		{
			auto* vm = RE::BSScript::Internal::VirtualMachine::GetSingleton();
			if (!vm || !g_quest) { return false; }
			auto* policy = vm->GetObjectHandlePolicy();
			if (!policy) { return false; }
			const RE::VMHandle handle = policy->GetHandleForObject(static_cast<RE::VMTypeID>(RE::FormType::Quest), g_quest);
			RE::BSTSmartPointer<RE::BSScript::Object> object;
			if (!vm->FindBoundObject(handle, kQuestScript, object) || !object) { return false; }
			auto* prop = object->GetProperty(kPointsProperty);
			if (!prop || !prop->IsInt()) { return false; }
			prop->SetSInt(prop->GetSInt() + a_add);
			logger::info("SSLR: script property {} += {} -> {}", kPointsProperty, a_add, prop->GetSInt());
			return true;
		}
	}

	void Install()
	{
		auto* dataHandler = RE::TESDataHandler::GetSingleton();
		if (!dataHandler || !dataHandler->LookupModByName(kPlugin))
		{
			logger::info("SSLR: {} not in the load order - skill-point refund unavailable", kPlugin);
			return;
		}
		g_points = dataHandler->LookupForm<RE::TESGlobal>(kGlobPointsLeft, kPlugin);
		g_cost[0] = dataHandler->LookupForm<RE::TESGlobal>(kGlobCost0, kPlugin);
		g_cost[1] = dataHandler->LookupForm<RE::TESGlobal>(kGlobCost25, kPlugin);
		g_cost[2] = dataHandler->LookupForm<RE::TESGlobal>(kGlobCost50, kPlugin);
		g_cost[3] = dataHandler->LookupForm<RE::TESGlobal>(kGlobCost75, kPlugin);
		g_quest = dataHandler->LookupForm<RE::TESQuest>(kQuest, kPlugin);
		g_detected = g_points && g_cost[0] && g_cost[1] && g_cost[2] && g_cost[3];
		if (g_detected)
		{
			logger::info("SSLR detected: points pool {} (global 0x{:08X}), cost tiers {}/{}/{}/{}, quest {}",
						 static_cast<int>(std::lround(g_points->value)), g_points->GetFormID(),
						 CostForLevel(0), CostForLevel(25), CostForLevel(50), CostForLevel(75), g_quest ? "found" : "missing");
		}
		else
		{
			logger::warn("SSLR: {} is loaded but its globals were not found at the expected FormIDs - skill-point refund disabled", kPlugin);
		}
	}

	bool IsDetected() { return g_detected; }

	Result RefundSkills()
	{
		Result r;
		auto* player = RE::PlayerCharacter::GetSingleton();
		if (!g_detected || !player)
		{
			r.message = "SSLR not detected.";
			return r;
		}
		auto* avOwner = player->AsActorValueOwner();
		auto* skills = player->GetPlayerRuntimeData().skills;
		int refund = 0;
		for (std::uint32_t i = 0; i < kSkillCount; ++i)
		{
			const auto av = static_cast<RE::ActorValue>(kFirstSkill + i);
			const int current = static_cast<int>(std::lround(avOwner->GetBaseActorValue(av)));
			const int floor = StartingLevel(player, av);
			if (current <= floor) { continue; }
			int thisSkill = 0;
			for (int level = floor; level < current; ++level) { thisSkill += CostForLevel(level); }
			refund += thisSkill;
			avOwner->SetBaseActorValue(av, static_cast<float>(floor));
			if (skills && skills->data)
			{
				// The game caches each skill's level and next-level threshold here and recomputes them only
				// when the skill levels up, so a reset rewrites them - otherwise the first level after the
				// respec would still cost what the old, higher level cost. Threshold = improveMult x
				// level^fSkillUseCurve + improveOffset (the AVIF's AVSK block).
				auto& sd = skills->data->skills[i];
				sd.level = static_cast<float>(floor);
				sd.xp = 0.0F;
				float curve = 1.95F;
				if (auto* gs = RE::GameSettingCollection::GetSingleton()) { if (auto* s = gs->GetSetting("fSkillUseCurve")) { curve = s->GetFloat(); } }
#if RUNTIME_LINE == 17
				auto* info = RE::ActorValueList::GetActorValueInfo(av);
#else
				auto* list = RE::ActorValueList::GetSingleton();
				auto* info = list ? list->GetActorValue(av) : nullptr;
#endif
				if (info && info->skill) { sd.levelThreshold = info->skill->improveMult * std::pow(static_cast<float>(floor), curve) + info->skill->improveOffset; }
			}
			++r.skillsReset;
			logger::debug("SSLR: skill {} {} -> {} (starting value) refunds {} point(s)", static_cast<int>(av), current, floor, thisSkill);
		}

		if (refund > 0)
		{
			g_points->value += static_cast<float>(refund);
			AddToScriptProperty(refund);
		}
		r.pointsRefunded = static_cast<std::uint32_t>(refund);
		r.message = std::format("{} trained skill{} reset to {} starting value{}, {} skill point{} returned to Static Skill Leveling.",
								r.skillsReset, r.skillsReset == 1 ? "" : "s", r.skillsReset == 1 ? "its" : "their", r.skillsReset == 1 ? "" : "s", refund, refund == 1 ? "" : "s");
		logger::info("SSLR: {} (pool now {})", r.message, static_cast<int>(std::lround(g_points->value)));
		return r;
	}

	std::int32_t GetPointsPool()
	{
		return (g_detected && g_points) ? static_cast<std::int32_t>(std::lround(g_points->value)) : -1;
	}
}
