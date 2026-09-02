#pragma once

// Potion of Clarity - settings. Plain-file INI (redirector-proof, the project standard).
// Deliberately tiny (design decision 2026-09-01: the menu just controls how much the potion
// costs): the potion is the feature, and its price is the one knob.

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
		inline std::uint32_t price = 500;  // uPrice:General - the potion's gold value (what merchants charge); 0..1000
	}

	void Init(const std::string& a_iniFileName);
	bool Reload();
	bool Save();
	void RestoreDefaults();
	void ApplyLogLevel();
	const std::string& GetIniPath();
}
