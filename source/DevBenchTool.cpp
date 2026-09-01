#include "PCH.h"

#include "DevBenchTool.h"

#include "Clarity.h"
#include "DevBench/DevBenchAPI.h"
#include "Settings.h"
#include "utils/Logger.h"

#include <format>
#include <string>
#include <string_view>

namespace DevBenchTool
{
	namespace
	{
		std::string EscapeJson(std::string_view a_in)
		{
			std::string out;
			out.reserve(a_in.size() + 8);
			for (const char c : a_in)
			{
				switch (c)
				{
				case '\\': out += "\\\\"; break;
				case '"': out += "\\\""; break;
				case '\n': out += "\\n"; break;
				default: out += c; break;
				}
			}
			return out;
		}

		void ControlTool(void*, const char* a_argsJson, void* a_sink, DevBenchAPI::WriteFn a_write)
		{
			const std::string_view args = a_argsJson ? a_argsJson : "";
			auto has = [&](const char* a_op) { return args.find(std::format("\"{}\"", a_op)) != std::string_view::npos; };

			if (has("give"))
			{
				// Test drive: one potion into the player's inventory, main-thread queued.
				if (!Clarity::GetPotion()) { a_write(a_sink, R"({"ok":false,"op":"give","error":"potion not resolved"})"); return; }
				if (auto* tasks = SKSE::GetTaskInterface())
				{
					tasks->AddTask([]() {
						auto* player = RE::PlayerCharacter::GetSingleton();
						auto* potion = Clarity::GetPotion();
						if (player && potion) { player->AddObjectToContainer(potion, nullptr, 1, nullptr); }
					});
				}
				a_write(a_sink, R"({"ok":true,"op":"give","count":1})");
				return;
			}
			if (has("drink"))
			{
				// Test drive through the REAL path: the equip manager consumes the potion the
				// same way the inventory menu does, so TESEquipEvent fires and the sink refunds.
				if (!Clarity::GetPotion()) { a_write(a_sink, R"({"ok":false,"op":"drink","error":"potion not resolved"})"); return; }
				if (auto* tasks = SKSE::GetTaskInterface())
				{
					tasks->AddTask([]() {
						auto* player = RE::PlayerCharacter::GetSingleton();
						auto* potion = Clarity::GetPotion();
						auto* mgr = RE::ActorEquipManager::GetSingleton();
						if (player && potion && mgr) { mgr->EquipObject(player, potion); }
					});
				}
				a_write(a_sink, R"({"ok":true,"op":"drink"})");
				return;
			}
			if (has("refund"))
			{
				// Direct refund, bypassing the potion (isolates the perk walk from the equip path).
				Clarity::RequestRefund();
				a_write(a_sink, R"({"ok":true,"op":"refund"})");
				return;
			}
			if (has("reload"))
			{
				const bool ok = settings::Reload();
				a_write(a_sink, std::format(R"({{"ok":{},"op":"reload"}})", ok ? "true" : "false").c_str());
				return;
			}

			const auto s = Clarity::GetState();
			const std::string json = std::format(
				"{{\"ok\":true,"
				"\"settings\":{{\"enabled\":{},\"logLevel\":{},\"iniPath\":\"{}\"}},"
				"\"runtime\":{{\"potionResolved\":{},\"potionFormId\":\"0x{:08X}\",\"spentPerks\":{},\"perkPoints\":{},"
				"\"refunds\":{},\"lastMessage\":\"{}\"}}}}",
				settings::general::enabled, settings::debug::logLevel, EscapeJson(settings::GetIniPath()),
				s.potionResolved, s.potionFormID, s.spentPerks, static_cast<int>(s.perkPoints), s.refunds,
				EscapeJson(s.lastMessage));
			a_write(a_sink, json.c_str());
		}
	}

	void Init(bool a_lastAttempt)
	{
		static bool registered = false;
		if (registered) { return; }

		DevBenchAPI::IDevBenchInterface001* devBench = DevBenchAPI::GetDevBenchInterface001();
		if (!devBench)
		{
			if (a_lastAttempt) { logger::info("DevBench not detected; skipping the \"poc.control\" tool"); }
			else { logger::debug("DevBench not detected yet; will retry at the next message"); }
			return;
		}

		constexpr const char* descriptor =
			"{"
			"\"description\":\"Potion of Clarity live state: settings, whether the potion resolved from the ESL, "
			"owned tree perks, perk points, lifetime refunds. op=give adds one potion; op=drink consumes one through "
			"the equip manager (the real path); op=refund refunds directly; op=reload re-reads the INI.\","
			"\"inputSchema\":{\"type\":\"object\",\"properties\":{\"op\":{\"type\":\"string\"}}},"
			"\"readOnly\":false"
			"}";

		if (devBench->RegisterTool("poc.control", descriptor, &ControlTool, nullptr))
		{
			logger::info("Registered \"poc.control\" with DevBench (build {})", devBench->GetBuildNumber());
			registered = true;
		}
	}
}
