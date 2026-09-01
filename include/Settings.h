#pragma once

// Auto Draw - clean-room MIT rebuild (2026-08-31). Settings are the same five the previous
// package shipped (same names, same defaults, same INI layout), reimplemented fresh: parsed
// straight from the INI with plain file I/O and never handed to the Win32 profile API, so
// PrivateProfileRedirector can neither serve a stale cache on reload nor flush one back over
// the file (the class of bug Dragon's Eye Minimap 1.5.7 diagnosed end to end).

#include <cstdint>
#include <string>

namespace settings
{
	namespace debug
	{
		inline std::uint32_t logLevel = 0;  // uLogLevel:Debug - 0 = trace (project default)
	}

	namespace automation
	{
		inline bool enableAutoDraw = true;       // bEnableAutoDraw:Automation
		inline bool enableAutoSheathe = true;    // bEnableAutoSheathe:Automation
		inline float sheatheDelaySeconds = 6.0F; // fSheatheDelaySeconds:Automation
		inline bool exemptBoundWeapons = true;   // bExemptBoundWeapons:Automation
	}

	// Reads the INI (creating nothing - a missing file just keeps the compiled defaults),
	// registers the settings with the game's INISettingCollection for consistency, and applies
	// the log level. Call once at plugin load.
	void Init(const std::string& a_iniFileName);

	// Re-reads the INI from disk, replacing every in-memory value. Plain file I/O only.
	bool Reload();

	// Writes every setting back into the INI in place (comments and unknown keys untouched).
	bool Save();

	// Puts every setting back to its compiled-in default. Nothing is written until Save().
	void RestoreDefaults();

	// Applies debug::logLevel to the live logger.
	void ApplyLogLevel();

	const std::string& GetIniPath();
}
