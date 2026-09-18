// Potion of Clarity - own code, GPL-3.0-or-later (2026-09-01). Drink the potion, get every spent perk back
// as perk points. The potion is an ALCH record in the tiny PotionOfClarity.esp that ships
// with this DLL; the refund itself is a plain main-thread edit of the player's perk list and
// the game's own perk-point counter - no hooks, no relocations, no serialization.
#include "PCH.h"

#include "Clarity.h"
#include "DevBenchTool.h"
#include "Settings.h"
#include "Sslr.h"
#include "UI.h"

#include "utils/AddressLibraryGuard.h"
#include "utils/Logger.h"
#include "utils/Strings.h"

namespace
{
	void MessageHandler(SKSE::MessagingInterface::Message* a_msg)
	{
		switch (a_msg->type)
		{
		case SKSE::MessagingInterface::kPostLoad:
			DevBenchTool::Init(false);
			break;
		case SKSE::MessagingInterface::kDataLoaded:
			strings::Configure("PotionOfClarity");
			UI::Register();
			Clarity::Install();
			Sslr::Install();
			DevBenchTool::Init(true);
			break;
		default:
			break;
		}
	}
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	SKSE::log::init("PotionOfClarity");
	// Address Library pre-check (the guard every mod of ours carries), BEFORE SKSE::Init, which opens the
	// Address Library itself (logic library 6026): a missing file gets a message naming it and the plugin
	// loads inert instead of CommonLibSSE-NG's bare failure line.
	if (!AddressLibraryGuard::Guard("Potion of Clarity"))
	{
		return true;
	}
	SKSE::Init(a_skse);

	settings::Init("PotionOfClarity.ini");
	settings::ApplyLogLevel();

	logger::info("Potion of Clarity {} loading",
				 SKSE::PluginDeclaration::GetSingleton()->GetVersion().string("."));

	SKSE::GetMessagingInterface()->RegisterListener(MessageHandler);

	return true;
}
