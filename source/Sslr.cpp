#include "PCH.h"

#include "Sslr.h"

#include "utils/Logger.h"

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
		constexpr int kSkillBase = 15;                  // every skill starts at 15 before the racial bonus
		constexpr std::uint32_t kFirstSkill = 6;        // kOneHanded
		constexpr std::uint32_t kSkillCount = 18;       // .. kEnchanting (23)

		bool g_detected = false;
		RE::TESGlobal* g_points = nullptr;
		RE::TESGlobal* g_cost[4] = { nullptr, nullptr, nullptr, nullptr };
		RE::TESQuest* g_quest = nullptr;

		// A skill's untrained value: 15 plus the player's racial bonus for it. Only levels ABOVE
		// this were bought with SSLR points, so only those are refunded (the Skill Reset addon
		// resets to a flat 10 and refunds from there, which hands out points nobody spent).
		int StartingLevel(RE::PlayerCharacter* a_player, RE::ActorValue a_skill)
		{
			int floor = kSkillBase;
			if (auto* race = a_player->GetRace())
			{
				for (const auto& boost : race->data.skillBoosts)
				{
					if (boost.skill.get() == a_skill) { floor += static_cast<int>(boost.bonus); }
				}
			}
			return floor;
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
			if (skills && skills->data) { skills->data->skills[i].xp = 0.0F; }
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
