# AutoDraw - changelog

Rule 61: this mod's own history, kept beside the code it describes. This repo is the
CLEAN-ROOM MIT REBUILD of Auto Draw; versions continue the released product line (1.0.4 was
the last working build of the retired previous repo).

<!-- VERSIONING-RULES -->
> **Versioning rules (CLAUDE.md rules 6 and 48 - identical for mods and documents):**
> * `X.Y.Z`. A change increments the THIRD number. At `.9` the MINOR rolls: `1.0.9 -> 1.1.0`;
>   `1.0.10` never exists.
> * The next number is **LAST WORKING + 1**. A failed, scratch or untested test build does NOT
>   consume its number - the next attempt at the same step REUSES it.
> * Numbers are assigned by the tooling, never by hand: mods via `version-ledger.ps1 -Action next`
>   then `set-version.ps1`; governed documents via `docs-pipeline.ps1 -Action bump`; the rules via
>   `rules-version.ps1 -Action bump`. If a number was typed by hand, it is wrong until the tool
>   agrees.

## 1.0.6 - 2026-09-05 - untested

### Added
- Added a Skyrim 1.7.99 / 1.7.104 build; the mod now installs as a FOMOD that picks the build for your game version (SE 1.5.97 / AE 1.6.1170, or Skyrim 1.7.x).

## 1.0.5 - 2026-08-31 - working

### Changed
- COMPLETE CLEAN-ROOM REBUILD, MIT licensed, own code throughout. The previous repo vendored
  the original mod's unpublished source and is retired; this one contains none of it - the
  behaviour was specified from our previously shipped INI/README and public descriptions,
  and the original Auto Draw is credited as the inspiration.
- STATE-BASED core instead of event-driven: a ~20 Hz main-thread tick reads the player's
  actual weapon/combat state and acts on it. This fixes the known "no auto-sheathe after
  loading a save with the weapon already drawn" bug by construction - a loaded-in drawn
  weapon simply IS the "drawn, out of combat" state and the countdown starts on its own.
  No hooks and no relocations: a poster thread hands one tick at a time to SKSE's task
  queue (never self-requeuing - SKSE drains its queue within one frame, so a task that
  re-queues itself pins the main thread; found and fixed during the build's first gate).
- Settings menu registers with Apocrypha Menu Framework by its real module name (stock SKSE
  Menu Framework as the fallback) - the AMF-aware vendored header, same as DEM 1.5.8/LMU 1.2.6.
- INI parsed with plain file I/O only, never the Win32 profile API, so
  PrivateProfileRedirector can neither serve stale values on reload nor overwrite the file
  (the old repo's 1.0.6 fix, carried into the rebuild). Hex and decimal numeric values both
  parse (base auto-detection).
- DevBench driving tool `autodraw.control` (the driving-tool standard): live settings +
  runtime state (combat, weapon state, sheathe countdown, bound-weapon hold, counters), and
  op=draw / op=sheathe / op=reload test drives.
- The .pdb debug symbols ship inside the main download (packaging standard since 2026-08-31).
