#pragma once

// Static Skill Leveling Rewritten (SSLR) compatibility - opt-in (bSSLRCompat). With SSLR,
// skills are raised by spending skill points earned at level-up instead of by use; a full
// respec therefore also has to give those points back. Mechanism (own code, from the
// documented behaviour of SSLR and its Skill Reset addon, analysed 2026-09-01):
//   for every skill 6..23 whose base value is above its STARTING value (15 + racial bonus):
//     refund += sum over level in [starting, current) of the SSLR cost tier for that level
//              (SSL_SkillPointCost0 / 25 / 50 / 75 globals - the cost to raise a skill
//               below 25 / 50 / 75 / above)
//     base value -> starting value, skill XP -> 0
//   SSLR's points pool += refund. The pool lives in the global SSL_PointsLeftAfterLvlUp
//   (SSLR 1.8) and, on script variants that keep it as an Int script property
//   "PointsLeftAfterLvlUp" on the SSLR quest, there too - both are written when present.
// The refunded points appear in SSLR's level-up menu at the next level-up, under SSLR's own
// spending rules.

#include <cstdint>
#include <string>

namespace Sslr
{
	// Resolves SSLR's plugin, globals and quest. Call at kDataLoaded (no-op when absent).
	void Install();

	bool IsDetected();

	struct Result
	{
		std::uint32_t skillsReset = 0;
		std::uint32_t pointsRefunded = 0;
		std::string message;
	};
	// Resets every trained skill to its starting value and refunds SSLR points. Main thread only.
	Result RefundSkills();

	// Current SSLR points pool (global value), or -1 when SSLR is absent.
	std::int32_t GetPointsPool();
}
