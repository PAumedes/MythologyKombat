# Tasks — Phase 0 (setup) and Phase 1 (survey and naming)

Status values: `todo` · `in-progress` · `blocked` · `done`. `USER` = only Patricio can do it; the orchestrator explains the steps and waits.
The orchestrator updates the Status column; nobody else edits this table.

| ID | Title | Depends on | Owner | Status |
| --- | --- | --- | --- | --- |
| T0.1 | Initialise the repo safely | — | agents | done |
| T0.2 | Prerequisite check script | T0.1 | agents | done |
| T0.3 | Install missing prerequisites | T0.2 | USER | in-progress |
| T0.4 | Identify and fingerprint the disc | T0.1 | agents | todo |
| T0.5 | Add PSXRecomp and build the framework | T0.3 | agents | todo |
| T0.6 | Decide how to scaffold the game project | T0.5 | agents | todo |
| T0.7 | Reference emulator check (Phase 0 gate) | T0.3 | USER | todo |
| T1.1 | List every file on the disc | T0.4 | agents | todo |
| T1.2 | Hunt for leftover debug symbols | T1.1 | agents | todo |
| T1.3 | Classify every file by format | T1.1 | agents | todo |
| T1.4 | Main EXE header and overlay candidates | T1.3 | agents | todo |
| T1.5 | Ghidra + PS1 loader + REA setup | T0.3 | USER + agents | todo |
| T1.6 | Identify PsyQ SDK functions | T1.4, T1.5 | agents | todo |
| T1.7 | Phase 1 gate review | T1.2, T1.3, T1.6 | agents | todo |

---

## T0.1 Initialise the repo safely
`git init` in the repo root (if not already a repo), add `.gitignore` (provided), make an empty first commit of the kit files.
**Accept when:** `git status` shows no file under `ps1_game/` or `work/`; `git check-ignore ps1_game/anything.bin` confirms it is ignored; first commit exists.

## T0.2 Prerequisite check script
Write `tools/check_prereqs.ps1` that reports present / missing with version for: Git, Python 3.10+, CMake 3.20+, Ninja, a C/C++ compiler (clang, MSVC `cl` or gcc), Java 21+ (for Ghidra), Ghidra, Node.js 22+ (for REA), and a reference emulator (DuckStation or PCSX-Redux). It must not install anything.
**Accept when:** it runs in a plain PowerShell window, prints one line per tool, exits 0 even when tools are missing, and never needs admin.

## T0.3 Install missing prerequisites — USER
Orchestrator: run `tools/check_prereqs.ps1`, then give Patricio the exact install steps for each missing tool. Follow PSXRecomp's README "Build requirements → Windows" (bundled `cmake-clang` toolchain recommended). Wait for him to confirm, re-run the script.
**Accept when:** the script shows every tool present.

## T0.4 Identify and fingerprint the disc
Write `tools/disc_identify.py`: parse the `.cue` in `ps1_game/`, list tracks, compute SHA-256 of each `.bin`, read `SYSTEM.CNF` from the ISO9660 filesystem of track 1 and print the boot executable name (the serial). Output to `work/disc_identity.json`; the hashes and serial (not file contents) go into `docs/DISC.md`.
Raw `.bin` files are 2352-byte sectors (Mode 2): handle that, don't assume a 2048-byte ISO.
**Accept when:** the serial comes from `SYSTEM.CNF`, not a guess; re-running gives identical output; a missing or misnamed `.bin` fails with a clear message. Record whether the serial is an NTSC-U one (`SLUS-`); if not, stop and ask the user.

## T0.5 Add PSXRecomp and build the framework
Add `https://github.com/RetroPortingToolKit/psxrecomp` as a submodule at `psxrecomp/` (with `--recurse-submodules`). Follow its README "Setup" section on Windows: build the recompiler, regenerate the OpenBIOS backend, build the runtime. Pin the submodule commit.
**Accept when:** the recompiler build, `regen_bios` for `bios/OpenBIOS.toml` and the runtime build all succeed; the exact commands and commit hash are recorded for the doc-writer.

## T0.6 Decide how to scaffold the game project
Read `psxrecomp/docs/GAME_PROJECT_SETUP.md`. Its setup script normally creates a NEW project folder; ours already exists. Work out the cleanest way: scaffold into a temp folder and move the files in, or set things up by hand. Do a dry run in `work/scaffold-test/`. Don't run "Generate" against the real disc yet.
**Accept when:** a written decision with the reason exists; `game.toml`, CMake files and `recomp-ui/` submodule are in place at the repo root; the project configures with CMake. Any decision that's hard to undo → ask the user first.

## T0.7 Reference emulator check — USER (Phase 0 gate)
Patricio boots the disc in DuckStation or PCSX-Redux with the debugger enabled and confirms it reaches gameplay. Orchestrator gives short steps.
**Accept when:** Patricio confirms.

## T1.1 List every file on the disc
`tools/disc_list.py`: walk the ISO9660 tree of track 1 and write name, path, start LBA, size, and file flags (including the XA attributes for Form 2 / interleaved files) to `work/disc_files.json`. The doc-writer turns it into `docs/DISC_MAP.md` (names, sizes, LBAs only). Also note any audio tracks from the `.cue`.
**Accept when:** the file count and total size are reported; files with XA/Form 2 flags are marked; output is deterministic.

## T1.2 Hunt for leftover debug symbols
Scan every file and the free space between files for: Psy-Q `.SYM` files (they start with the bytes `MND`), linker `.MAP` text, source paths (`.c`, `.h`, `C:\`, `\PSX\`), and function-name-like strings. `tools/symbol_hunt.py`, report to `work/symbol_hunt.txt`, summary to `docs/SYMBOLS.md`.
**Accept when:** every file and every gap between files was scanned (the report says how many bytes); any hit lists offset and context; "nothing found" is a valid result, stated plainly. Also add to `docs/OPEN_QUESTIONS.md`: are there other regional releases (PAL, demo discs) worth checking?

## T1.3 Classify every file by format
`tools/disc_classify.py`: tag each file as PS-X EXE (header `PS-X EXE`), STR video (MDEC sectors via subheader), XA audio, TIM image, VAB/VAG/SEQ audio, overlay candidate (raw MIPS code), or unknown, with the evidence used. Extraction to `work/extracted/` only.
**Accept when:** every file from T1.1 has a tag and an evidence string; `unknown` is allowed but counted.

## T1.4 Main EXE header and overlay candidates
Parse the boot EXE's header: load address, entry point, text size, initial GP/SP. For each overlay candidate, estimate its load address (from pointers into its own range, or the code that loads it) and size.
**Accept when:** header values match a second independent read (e.g. compare with the emulator's debugger, or with Ghidra once T1.5 is done); overlay load addresses are marked "confirmed" or "estimated".

## T1.5 Ghidra + PS1 loader + REA setup — USER + agents
Patricio installs Ghidra and the `ghidra_psx_ldr` extension; agents then help set up REA (`npx rea-agents setup`, which registers its MCP server with Claude Code) and check whether REA can open the boot EXE through Ghidra.
**Accept when:** Ghidra opens the boot EXE with the PS1 loader; REA returns pseudocode for the entry function, or the failure is recorded in `docs/OPEN_QUESTIONS.md` with the error.

## T1.6 Identify PsyQ SDK functions
Find the PsyQ library version strings in the EXE, apply matching PsyQ signatures (the `ghidra_psx_ldr` extension ships them), and export named SDK functions (name, address) to `docs/SYMBOLS.md` and a machine-readable `work/symbols_sdk.json`. Game functions stay unnamed for now.
**Accept when:** the SDK version source is shown; named-function count is reported; spot-check 5 names against their code.

## T1.7 Phase 1 gate review
Adversarial reviewer only: check every file on the disc has a classification, `docs/` matches the scripts' output, and no game data is committed.
**Accept when:** PASS. Then stop and report to Patricio before starting Phase 2.
