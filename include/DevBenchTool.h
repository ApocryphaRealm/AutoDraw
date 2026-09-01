#pragma once

namespace DevBenchTool
{
	// Registers "autodraw.control" with DevBench when it is present (the driving-tool
	// standard: state readable AND the behaviour drivable headlessly). Call with false at
	// kPostLoad and true at kDataLoaded - DevBench's own server can lose the startup race,
	// so the early call may find nothing and the late one logs if it still does.
	void Init(bool a_lastAttempt);
}
