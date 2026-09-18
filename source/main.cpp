// Auto Draw - clean-room MIT rebuild (2026-08-31). Own code throughout: behaviour specified
// from this project's previously shipped INI/README and public mod-page descriptions; the
// original Auto Draw (closed source) is credited as the inspiration. No vendored third-party
// mod source anywhere in this repo.
#include "PCH.h"

#include "AutoDraw.h"
#include "DevBenchTool.h"
#include "Settings.h"
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
			strings::Configure("AutoDraw");
			UI::Register();
			AutoDraw::Install();
			DevBenchTool::Init(true);
			break;
		default:
			break;
		}
	}
}

SKSEPluginLoad(const SKSE::LoadInterface* a_skse)
{
	SKSE::log::init("AutoDraw");
	// Address Library pre-check (the guard every mod of ours carries), BEFORE SKSE::Init, which opens the
	// Address Library itself (logic library 6026): a missing file gets a message naming it and the plugin
	// loads inert instead of CommonLibSSE-NG's bare failure line.
	if (!AddressLibraryGuard::Guard("Auto Draw"))
	{
		return true;
	}
	SKSE::Init(a_skse);

	settings::Init("AutoDraw.ini");
	settings::ApplyLogLevel();

	logger::info("Auto Draw {} loading (clean-room rebuild)",
				 SKSE::PluginDeclaration::GetSingleton()->GetVersion().string("."));

	SKSE::GetMessagingInterface()->RegisterListener(MessageHandler);

	return true;
}
