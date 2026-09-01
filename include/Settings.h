#pragma once

// Potion of Clarity - settings. Plain-file INI (redirector-proof, the project standard).
// Deliberately tiny: the potion is the feature, and the only decision left to the player is
// whether the mod is switched on.

#include <cstdint>
#include <string>

namespace settings
{
	namespace debug
	{
		inline std::uint32_t logLevel = 0;  // uLogLevel:Debug
	}

	namespace general
	{
		inline bool enabled = true;  // bEnabled:General - drinking the potion refunds perks
	}

	void Init(const std::string& a_iniFileName);
	bool Reload();
	bool Save();
	void RestoreDefaults();
	void ApplyLogLevel();
	const std::string& GetIniPath();
}
