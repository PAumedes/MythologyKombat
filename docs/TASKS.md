# Tasks — Phase 0 (setup), Phase 1 (survey and naming) and Phase 2 (first boot)

Status values: `todo` · `in-progress` · `blocked` · `done`. `USER` = only Patricio can do it; the orchestrator explains the steps and waits.
The orchestrator updates the Status column; nobody else edits this table.

| ID | Title | Depends on | Owner | Status |
| --- | --- | --- | --- | --- |
| T0.1 | Initialise the repo safely | — | agents | done |
| T0.2 | Prerequisite check script | T0.1 | agents | done |
| T0.3 | Install missing prerequisites | T0.2 | USER | done |
| T0.4 | Identify and fingerprint the disc | T0.1 | agents | done |
| T0.5 | Add PSXRecomp and build the framework | T0.3 | agents | done |
| T0.6 | Decide how to scaffold the game project | T0.5 | agents | done |
| T0.7 | Reference emulator check (Phase 0 gate) | T0.3 | USER | done |
| T1.1 | List every file on the disc | T0.4 | agents | done |
| T1.2 | Hunt for leftover debug symbols | T1.1 | agents | done |
| T1.3 | Classify every file by format | T1.1 | agents | done |
| T1.4 | Main EXE header and overlay candidates | T1.3 | agents | done |
| T1.5 | Ghidra + PS1 loader + REA setup | T0.3 | USER + agents | done |
| T1.6 | Identify PsyQ SDK functions | T1.4, T1.5 | agents | done |
| T1.7 | Phase 1 gate review | T1.2, T1.3, T1.6 | agents | done |

### Phase 2 (first boot)

| ID | Title | Depends on | Owner | Status |
| --- | --- | --- | --- | --- |
| T2.1 | CLI wrapper and disc re-verification | T1.7 | agents | done |
| T2.2 | Seed sanity and static coverage baseline | T2.1 | agents | done |
| T2.3 | First Generate (boot EXE, OpenBIOS only) | T2.1, T2.2 | agents | done |
| T2.4 | Configure and build the game executable | T2.3 | agents | done |
| T2.5 | Headless smoke-test harness | T2.4 | agents | done |
| T2.6 | Visual first boot: logos | T2.5 | USER | done |
| T2.7 | Provide a retail BIOS (conditional) | T2.6 | USER | done |
| T2.8 | Seed growth from dispatch misses | T2.5 | agents | done |
| T2.9 | LBA-to-file lookup tool | T1.1 | agents | done |
| T2.10 | FMV check (STR and XA) | T2.6, T2.9 | USER + agents | in-progress |
| T2.11 | Main menu and first fight | T2.10 | USER + agents | done |
| T2.12 | Overlay facts from the EXE and disc | T1.4 | agents | done |
| T2.13 | Runtime proof: overlay RAM equals file bytes | T2.11, T2.12 | USER + agents | done |
| T2.14 | Overlay strategy decision | T2.13 | agents | done |
| T2.15 | Write aot/overlays.json | T2.14 | agents | done |
| T2.16 | Static overlay build, link and audit | T2.15, T2.4 | agents | done |
| T2.17 | Overlay coverage across all nine level functions | T2.16 | USER + agents | done |
| T2.18 | Replay infrastructure: scaffold and boot-to-menu route | T2.5 | agents | done |
| T2.19 | Playtest diagnostics package (recorder) | T2.4 | agents | done |
| T2.20 | Record a session and strict replay | T2.19, T2.11 | USER + agents | done |
| T2.21 | Seed symbols.toml from the SDK names | T1.6 | agents | done |
| T2.22 | Name the overlay loader and level functions | T2.12, T2.21 | agents | done |
| T2.23 | Phase 2 gate review | all above | agents | in-progress |

Phase 2 notes: T2.9, T2.12, T2.21 and T2.19 do not need the game to boot. They can run in parallel with the main chain once their dependencies are done. All outputs go under `work\` (git-ignored) unless noted. Python scripts are stdlib-only. Every disc claim comes from a `tools\` script. Run the upstream CLI WITHOUT `python -I` (see T2.1).

Gate notes:
- T2.10 stays `in-progress`. Its open items are in `docs/SETUP.md` ("Why T2.10 stays in-progress").
- T2.23 gate review PASSED on checks. It cannot be closed until T2.10 is done, or the user explicitly descopes T2.10.

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

## T2.1 CLI wrapper and disc re-verification
Write `tools\run_psxrecomp.ps1`. It sets the toolchain environment from `docs/SETUP.md`, picks a Python that can run `psxrecomp\psxrecomp_cli.py`, and forwards the arguments. The upstream CLI needs `psxrecomp\tools` on `sys.path`. The embeddable Python ignores `PYTHONPATH` because of its `._pth` file. Our tools use `python -I`, but the upstream CLI must not. Resolve Q26: try the embeddable Python without `-I`, then the `work\py-scaffold` copy whose `._pth` lists `psxrecomp\tools`. If neither works, STOP and ask the user for a full Python install. No hard-coded `%USERPROFILE%` paths except documented, environment-overridable defaults (Q76). Record the Python decision as D5.
**Accept when:** `verify-disc --config game.toml --disc <cue>` exits 0 with digests matching the `[prepare_disc] known_*` values and `disc_probe.json`; the SHA-256 of `work\disc\SLUS_004.76` equals `boot_exe_sha256` in `disc_probe.json`; nothing under `ps1_game\` changed (mtimes and sizes before and after); the Python decision is recorded as D5.

## T2.2 Seed sanity and static coverage baseline
Write `tools\check_seeds.py`. Every non-comment line of `seeds\ghidra_funcs.txt` must be a word-aligned address in [0x80010000, 0x800D8000). Also run `psxrecomp-analyze work\disc\SLUS_004.76 --out work\analysis --emit-tsv work\analysis\functions.tsv --seeds seeds\ghidra_funcs.txt` and compare its function starts with the Ghidra list in `work\symbols_sdk.json` (1730 functions).
**Accept when:** the report counts 1175 seeds plus the entry, and lists any out-of-range seeds (none expected; if any are found, add them to `docs/OPEN_QUESTIONS.md`); a report of analyze-found, Ghidra-only and analyze-only starts, plus indirect-transfer gaps; a count of JALs that target the overlay window 0x80130FF8..0x8013C720; the output is deterministic.

## T2.3 First Generate (boot EXE, OpenBIOS only)
Run `generate --config game.toml --project-root . --disc <cue>` through the wrapper. No `--bios`, no `--force-prepare`. Log to `work\generate_run1.txt`.
**Accept when:** exit 0; `generated\SLUS_004.76_dispatch.c` and `generated\SLUS_004.76_full_*.c` exist; the log shows strict mode and no skipped-function failures (skip list saved under `work\`); `git status` shows nothing under `generated\` and `git check-ignore` confirms it; a second Generate is byte-identical (SHA-256 lists compared); no hand edits; psxrecomp submodule status is no worse (Q13 noise only).

## T2.4 Configure and build the game executable
Run `cmake -S . -B build -DPSXRECOMP_REQUIRE_GAME_C=ON`, then build `--target psx-runtime` in the background. Use `-j 2` if the compiler dies silently.
**Accept when:** the configure log contains `linking generated game C (full runtime)` and `BIOS backends linked: OpenBIOS`; `build\MythologyKombat.exe` exists with `bios\openbios.bin` and `game.toml` beside it; commands, times and the exe SHA-256 are recorded for the docs; no build output is tracked.

## T2.5 Headless smoke-test harness
Write `tools\smoke_boot.py`. Confirm the headless or hidden-window flags in the framework's `main.cpp` first. Launch the exe with `--disc`, and talk to the TCP debug server on port 4370 (ping, frame, screenshot, quit). Save screenshots to `work\shots\`.
**Accept when:** it exits 0 when the process stays alive for 60 s, the frame counter increases, and there is no `psx_crash.txt`; it prints the frame count and screenshot paths; a negative test (wrong disc path, killed process) fails correctly; an agent opens a screenshot and describes it (evidence only, not the user gate); there is a clean kill switch.

## T2.6 Visual first boot: logos — USER
Run `build\MythologyKombat.exe --disc "<repo>\ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue"`. Watch for the Sony and Midway logos, audio, and any crash or black screen. Report what appears and how long it takes. "Pixels on screen" is the bar (psxrecomp `CLAUDE.md` rule 5). If OpenBIOS hangs or fails, go to T2.7. Do not guess a cause.
**Accept when:** Patricio confirms the logos.

## T2.7 Provide a retail BIOS (conditional) — USER
Only if T2.6 fails under OpenBIOS and the failure is plausibly BIOS-related. Confirm the model with the user first. Patricio places a retail SCPH-1001 dump OUTSIDE the repo (not in `ps1_game\` or `psxrecomp\`) and gives the path. Agents run `generate --bios <abs path> --force-bios` through the wrapper. The BIOS is never committed.
**Accept when:** the BIOS backend is generated; `git status` (repo and psxrecomp) shows no BIOS tracked; boot is retried and the result is recorded. If OpenBIOS booted, mark done as not needed.

## T2.8 Seed growth from dispatch misses
After the smoke test, and during user play, run `tools\collect_game_misses.py` against the debug port with text range 0x80010000..0x800D8000, writing `work\dirty_ram_misses.txt`. Vet the list with `tools\vet_seeds.py --game game.toml`. Append only ACCEPTed addresses to `seeds\ghidra_funcs.txt` with a small script. Regenerate and rebuild.
**Accept when:** the miss list and verdict counts (ACCEPT, WARN, REJECT) are recorded; WARN addresses are listed for manual review and not seeded; after the rebuild, those addresses no longer miss on the same smoke path; committing seeds is covered by the Q75 decision.

## T2.9 LBA-to-file lookup tool
Write `tools\lba_lookup.py`. Given an LBA or a CdlLOC (BCD minute:second:frame), print the disc file and offset, using `work\disc_files.json` (including `/MOVIES/*.STR`).
**Accept when:** the correct file is found for the first and last LBA of at least five files (including MIDWAY01.STR, LEGAL.STR and a .OVR); gap LBA 424 gives "no file"; the output is deterministic; stdlib only.

## T2.10 FMV check (STR and XA) — USER + agents
Patricio reports which movies play with picture and audio, from the intro and the menu. Agents provide a checklist of the 28 `/MOVIES` STR files (LEGAL.STR has no XA). If the debug server offers a CD read trace, map LBAs to names with T2.9. Fix causes in the framework upstream first (rule 4).
**Accept when:** each movie reached has a row (picture OK?, audio OK?, glitches); unreached movies are marked untested; failures become `docs/OPEN_QUESTIONS.md` entries naming the exact movie.

## T2.11 Main menu and first fight — USER + agents
Patricio reaches the main menu, starts a new game and plays into the first fight. Agents capture a screenshot and frame number at each stage through the debug server. Record which level loads from the observed overlay id (use pc_break on the read_file call sites in `docs/EXE_OVERLAYS.md`). Do not name the level from memory.
**Accept when:** Patricio confirms the menu and a fight with responsive controls; play time and whether any crash occurred are recorded; the level name comes from the observed overlay id.

## T2.12 Overlay facts from the EXE and disc
Write `tools\overlay_facts.py`, which writes `work\overlay_facts.json`. For ids 134 to 143, check the CdlLOC table (0x80012F28) and the size table (0x80013264) against `work\disc_files.json`. Check that the destination pointer word at 0x80015134 equals 0x80130FF8, and that no instruction other than the known readers touches 0x80015134. Resolve the ids reachable by the two variable-id read_file callers (0x80085CF8, 0x80085D74) (Q50). For each .OVR, record SHA-256, size and sector alignment. Record the exact address-table prefix lengths for BRIDGE, FIRE, WATER and WIND.
**Accept when:** all ten entries agree, or the mismatches are listed; Q50 and Q51 are answered with evidence or reduced to a stated unknown; the output is deterministic; for FORTRESS and PRISON, the "one check only" gap is closed by a second independent check or stays flagged.

## T2.13 Runtime proof: overlay RAM equals file bytes — USER + agents
At the first-fight overlay memcpy call site, use pc_break. Record a0 to a2 and $ra. Use read_ram on 0x80130FF8 for the file size, and hash it against the T2.12 file hash. This answers Q45 (scratch buffer, overlap), the OpenBIOS memcpy question and Q44 (runtime check).
**Accept when:** for at least one level, the RAM hash equals the .OVR hash (otherwise record the first differing offset and cause); a0 to a2 are recorded in `docs/EXE_OVERLAYS.md` with the scratch buffer address; if the bytes differ, STOP and ask the user. No game-config workaround.

## T2.14 Overlay strategy decision
Write a DECISIONS entry. Recommendation: keep the runtime route working first (interpreter plus runtime autocompile, `overlay_cache=true`). Then the AOT static route (`aot\overlays.json` with `static_output` linked into the exe). Reasons: local single user, no captures, deterministic, generated code stays git-ignored. Do not use the DLL-cache route now. The profile holds addresses, sizes and hashes only. Ask the user whether it may be committed.
**Accept when:** the decision and reasons are written; the user's commit answer is obtained; nothing is built.

## T2.15 Write aot/overlays.json
Create `aot\overlays.json` for the 8 .OVR files: `disc_hashes`, 8 `fixed_address_files` at 0x80130FF8, `generic_exclude_files` for BRDGDEMO.BIN and WINDDEMO.BIN, `bcd_extent_table` for the CdlLOC table, `adjacent_files`, `words` checks for the pointer word, `excluded_ranges` for the four address-table prefixes (SHA-256 and reason) or verified entries, `expected_records`, `strict_bounds`, and `static_output = "generated/overlays_static.c"`.
**Accept when:** `python psxrecomp\tools\aot_overlay_pipeline.py extract --profile aot\overlays.json --game-toml game.toml ...` (no `--stage`) runs against the real disc in a work dir outside the repo and exits 0; it reports exactly 8 image records; it fails when a record is added or removed (negative test on a profile copy); unprovable checks are listed as open, not weakened.

## T2.16 Static overlay build, link and audit
Add `GAME_OVERLAY_STATIC_C "generated/overlays_static.c"` to `CMakeLists.txt`. Generate builds the static shard. Reconfigure and build.
**Accept when:** `generated\overlays_static*.c` and `AOT_STATIC_AUDIT.json` exist and the audit passes with guarded entries for every image; both are git-ignored; the configure log shows no GAME_OVERLAY_STATIC_C mismatch; the exe boots into the T2.11 level and `overlay_static_entries` over 0x80130FF8..0x8013C720 is non-zero; the build still works on a second Generate (`--reuse`).

## T2.17 Overlay coverage across all nine level functions — USER + agents
Patricio reaches each level function listed in `docs/EXE_OVERLAYS.md` (TEMPLE, EARTH, WIND, WATER, PRISON, FIRE twice, BRIDGE, FORTRESS) as far as possible, and reports any he cannot reach. Agents read `overlay_static_entries` and `overlay_loader_status` after each.
**Accept when:** there is a table per level function (loaded id, reached?, static hits, interpreter fallback?, visible fault); Q46 and Q51 are closed for the levels reached; unreached levels stay untested.

Done note: TEMPLE user-played; the other seven overlays agent-observed via warp (not natural play); FIRE2 black screen unexplained; no natural play beyond TEMPLE.

## T2.18 Replay infrastructure: scaffold and boot-to-menu route
Create `tests\replays\` with a README and a .gitignore. Write `tools\run_boot_route.py`. It launches the exe, queues a button route with `input_route_append` and `input_route_start at_frame=N`, and captures state at fixed frames. Compare RAM digest ranges and frame counters, NOT screenshots. Route files hold only button steps and frame numbers, so they can be committed. No game pixels are committed.
**Accept when:** two cold-boot runs give identical digests at the checkpoints; changing one input frame changes the digests (negative control); the README states what is committed (routes, expected digests) and what is not (screenshots, recordings, saves).

## T2.19 Playtest diagnostics package (recorder)
Add `psxrecomp_add_playtest_diagnostics(psx-runtime GAME_ID "SLUS-00476" MOD_ID "<id>")` to `CMakeLists.txt`. Add a mod package under `mods\preloaded\packages\` with recording and input-display features, following `psxrecomp\docs\MOD_PACKAGES.md`.
**Accept when:** it configures and builds; it stages `replay-diagnostics.py` beside the exe; the catalog check passes (no "undeclared catalog" error); a short headless run produces a session folder with an input CSV; public-release defaults are unchanged.

## T2.20 Record a session and strict replay — USER + agents
Patricio plays boot, logos, menu, a new game and about 1 minute of a fight with recording on. Agents run `replay_diagnostics.py <session> --exe <exe> --disc <cue> --game game.toml --output <new private dir>` twice. `tools\run_replays.ps1` runs all recordings under `tests\replays\local\` and prints pass or fail.
**Accept when:** strict replay succeeds on two runs; a negative control (different exe build, or a modified input row) reports a mismatch; `tools\run_replays.ps1` prints pass or fail for each recording; recordings stay git-ignored (RAM digests and personal data); Patricio decides whether recordings are ever committed.

## T2.21 Seed symbols.toml from the SDK names
Write `tools\seed_symbols.py`, which seeds `symbols.toml` from `work\symbols_sdk.json`. Use only kind == sdk. Exclude 153 gte_macro and 335 obj_label. By default omit the 3 suspects: SsUtReverbOn 0x80053AD0, SsUtReverbOff 0x8005E1B0, _SsSndPlay 0x8008387C. Disambiguate duplicates (memset x2, memclr x3) with an address suffix. Names must be valid, unique C identifiers. Set emit=false for all. Set status 'confirmed' only for names with recorded evidence in `docs/SYMBOLS.md` (VSync, ResetGraph, CdInit, memcpy, printf, RotTransPers, MemCardInit, SpuIsTransferCompleted); otherwise 'guessed'. Key entries by address. Keep BootEntry.
**Accept when:** `python tools\sync_symbols.py` and `--check` both pass; the entry count equals 443 minus exclusions, with the exclusion counts printed; the run is idempotent and never overwrites hand-edited entries; generated C is unchanged (SHA-256 list compared with T2.3). Never include `psx_symbols.h` from generated C.

## T2.22 Name the overlay loader and level functions
Add to `symbols.toml` the functions established in `docs/EXE_OVERLAYS.md`: get_size 0x800861BC, read_file 0x800861D4, scratch allocator 0x800865C0, memcpy wrapper 0x8009F31C, and the 9 level-loader functions named by the file they load (for example 0x8002B688 loads TEMPLE.OVR). Status is 'confirmed' only if T2.13 or T2.17 observed it at runtime; otherwise 'guessed'.
**Accept when:** sync passes; each note cites a doc section or runtime observation; no name claims more than the docs do.

## T2.23 Phase 2 gate review
Adversarial reviewer only. Check that no game data is tracked (`git ls-files` shows no generated, work, ps1_game, captures, recordings, BIOS or .bin files); generated code was never hand-edited (regenerate and compare); each doc claim maps to a `tools\` script; user gates (T2.6, T2.10, T2.11, T2.17, T2.20) are recorded as user-reported, not agent-observed.
**Accept when:** PASS. Then stop and report to the user before any Phase 3.

## Decisions needing the user (before they block)

Hard to undo, so ask first:

| Decision | Related | Needed by |
| --- | --- | --- |
| Committing derived files (`seeds\ghidra_funcs.txt`, `aot\overlays.json`, `symbols.toml`, `psx_symbols.h`, test routes) | Q75 | T2.8, T2.14, T2.15, T2.18, T2.21 |
| Committing replay recordings | — | T2.20 |
| Providing a retail BIOS dump and its location | — | T2.7 |
| Installing a full Python system-wide (only if the wrapper fails) | Q26 | T2.1 |
| Pushing to a remote, or changing the generated-code policy | Q23 | Not needed in Phase 2 |
| Deleting `work\` scratch or ghidra-* projects | Q67 | — |

### Open questions for the user

1. Which BIOS dump exists (model, for example SCPH-1001), and may we ask for its path if OpenBIOS fails?
2. May `aot\overlays.json` (hashes, offsets, addresses, sizes), `symbols.toml`, seeds and test routes be committed (Q75)?
3. May strict-replay recordings ever be committed?
4. Is a full Python 3.12 install acceptable if the embeddable one cannot run the framework CLI?
5. Can you play through all nine level functions (T2.17), or only the early levels?
6. May the first launch open a normal window while agents run the debug server on port 4370?
