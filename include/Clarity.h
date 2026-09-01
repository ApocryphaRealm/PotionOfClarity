#pragma once

// Potion of Clarity - core. Drinking the potion (an ALCH record in PotionOfClarity.esl)
// removes every perk the player bought from the 18 skill trees and hands the same number of
// perk points back. Perks and perk points are both game-saved state, so nothing is
// serialized: the refund is a plain main-thread edit of the player's perk list and the
// perk-point counter.
//
// Perk enumeration walks each skill's BGSSkillPerkTreeNode graph (depth-first, with a visited
// guard because trees share nodes) and collects every rank chained through nextPerk; only
// perks reachable from a skill tree count, so racial, quest and mod-granted abilities that
// live outside the trees are never touched.

#include <cstdint>
#include <string>

namespace Clarity
{
	// Resolves the potion form from PotionOfClarity.esl and registers the consume sink.
	// Call at kDataLoaded. Safe to call again (no-op once resolved).
	void Install();

	struct Result
	{
		bool success = false;
		std::uint32_t perksRemoved = 0;   // every owned rank found in the 18 trees
		std::uint32_t pointsRefunded = 0; // perksRemoved, minus anything lost to the 127 cap
		std::string message;              // shown to the player and kept for the settings page
	};

	// Writes settings::general::price onto the potion form (its gold value). Main thread only;
	// called at load and whenever the setting changes.
	void ApplyPrice();

	// Removes every tree perk the player owns and refunds the points. Main thread only.
	Result Refund();

	// Queues Refund() onto the main thread (safe from any thread).
	void RequestRefund();

	struct State
	{
		bool potionResolved = false;
		std::uint32_t potionFormID = 0;   // runtime FormID (FExxx801 once the ESL is loaded)
		std::uint32_t spentPerks = 0;     // owned tree-perk ranks right now
		std::int8_t perkPoints = 0;
		std::uint64_t refunds = 0;        // lifetime refunds this session
		std::string lastMessage;
	};
	// Cheap; the perk count is re-walked at most once a second.
	State GetState();

	// The runtime potion form (nullptr until the ESL resolves). Used by the DevBench tool.
	RE::TESBoundObject* GetPotion();
}
