# Tasks — Phase 0 (setup), Phase 1 (survey and naming), Phase 2 (first boot) and Phase 3 (stabilise and release prep)

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
| T2.10 | FMV check (STR and XA) | T2.6, T2.9 | USER + agents | done |
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
| T2.23 | Phase 2 gate review | all above | agents | done |

Phase 2 notes: T2.9, T2.12, T2.21 and T2.19 do not need the game to boot. They can run in parallel with the main chain once their dependencies are done. All outputs go under `work\` (git-ignored) unless noted. Python scripts are stdlib-only. Every disc claim comes from a `tools\` script. Run the upstream CLI WITHOUT `python -I` (see T2.1).

Gate notes:
- T2.10 is `done`. The user descoped it on 2026-10-20 with the movies checked so far (`docs/DECISIONS.md`, D17). 23 of the 28 `/MOVIES` STR files are untested. Its open items are in `docs/SETUP.md` ("Why T2.10 was in-progress") and stay open.
- T2.23 is `done`. The user closed it on 2026-10-20, after the T2.10 descope (D17). Its gate review had PASSED on checks before that.

### Phase 3 (stabilise and release prep)

| ID | Title | Depends on | Owner | Status |
| --- | --- | --- | --- | --- |
| T3.1 | Release rebuild with vsync-off default | T2.23 | agents | done |
| T3.2 | Refresh replay baselines | T3.1 | agents | done |
| T3.3 | Record a new session on the new exe | T3.1 | USER (deferred, only needed for T3.4 replay) | todo |
| T3.4 | Strict replay of the new recording, twice, with negative control | T3.3 | agents | todo |
| T3.5 | Phase 3 gate review (runs last) | T3.1, T3.2, T3.4, T3.6 to T3.26 | agents | todo |
| T3.6 | Perf measurement hygiene | T3.1 | agents | done |
| T3.7 | 1x vs 4K resolution A/B (visible window) | T3.6 | USER + agents | todo |
| T3.8 | Vsync and window mode A/B (visible window) | T3.6 | USER + agents | todo |
| T3.9 | Sampling profile of the Release exe during the FMV | T3.6 | USER + agents | todo |
| T3.10 | PGO and LTO trial (flag-only, only if T3.9 points at compiled code) | T3.6, T3.7, T3.8, T3.9 | agents | todo |
| T3.11 | Launcher screenshots at default and user scale | T3.1 | USER | done |
| T3.12 | Launcher fixes as local patch files (D19) | T3.11, T3.13 | agents | done |
| T3.13 | Box art and disc icon source and licence | T3.11 | USER | todo (superseded, optional) |
| T3.14 | Licence for this repo's own files (LICENSE and NOTICE) | — | USER + agents | done |
| T3.15 | Path, email and derived-data decisions, then the scrub | T3.14 | USER + agents | in-progress |
| T3.16 | No-game-data guard script | — | agents | done |
| T3.17 | CI on GitHub-hosted runners (guard, emitters-test, setup-host build from a clean clone) | T3.16, T3.18 | agents | done |
| T3.18 | Setup-host build in the repo, and the first wizard run | T3.1 | agents + USER | done |
| T3.19 | Local release script `tools\release.ps1` (game zip, content check, checksums) | T3.12, T3.14, T3.16, T3.18 | agents + USER | done |
| T3.20 | Optional: self-hosted runner for the game build (tag only, disc stays on the PC) | T3.17, T3.19 | USER + agents | todo |
| T3.21 | Launcher updater: check, verify, replace, keep saves | T3.19 | agents | todo |
| T3.22 | Clean-machine test of the downloaded zip (disc only) | T3.19 | USER | todo |
| T3.23 | First push to GitHub, history rewrite (D22) and first CI run | T3.15, T3.17, T3.19 | USER + agents | todo |
| T3.24 | Code-signing decision for the release exe | T3.19 | USER | todo |
| T3.25 | README rewrite and legal wording | T3.14, T3.15, T3.21, T3.22, T3.24 | agents + USER | todo |
| T3.26 | Reproducibility of the release exe (Q274) | T3.19 | agents | todo |

Phase 3 notes:
- T3.3 is deferred. It is the only recording step, and only T3.4 needs it.
- T3.5 is the gate and runs last. Its number stays T3.5 because other docs cite it.
- Any relink of `build\MythologyKombat.exe` changes its SHA-256 and breaks strict replay (T2.20). So the user recording (T3.3) must come after the last relink (D14, D15).
- Release model: D25 (a prebuilt game zip, built on the user's PC). D25 supersedes D18 where they conflict; D18's setup-host kit is the fallback and developer path. Launcher fixes: D19 (patch files). Release open questions are 244 to 295 in `docs\OPEN_QUESTIONS.md`.
- Every USER step lists its exact commands in its task section.

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

## Phase 3: stabilise and release prep

## T3.1 Release rebuild with vsync-off default (agents)
Rebuild the Release exe from the current commit using the project's documented build steps (`docs\SETUP.md`). Record the new exe SHA-256 and size. Confirm `game.toml` and the settings staging (`[video] vsync = "off"`, D9) are in `build\`. Run `tools\smoke_boot.py` (expect PASS) and `tools\run_boot_route.py` (expect MATCH). Confirm no game data is embedded in or tracked by the repo.
**Accept when:** the hash and size are recorded in docs; the build commands are reproducible from `docs\SETUP.md`; smoke_boot PASS and run_boot_route MATCH are recorded; no tracked game data (`git ls-files` check).

## T3.2 Refresh replay baselines (agents)
Re-record the expected digests in `tests\replays\expected` against the T3.1 exe. The stored `exe_sha256` is stale (open question 173). Update `README.md` to match.
**Accept when:** `exe_sha256` in the expected files equals the T3.1 exe hash; the boot route still gives MATCH against the new baseline; `README.md` states the new baseline.

## T3.3 Record a new session on the new exe — USER (deferred)
Depends on: T3.1. Owner: USER. Deferred: only T3.4 needs it, so the user records it when the rest of Phase 3 is ready. Record it on the final exe. If a later task relinks `build\MythologyKombat.exe`, record again (D14, D15).
Orchestrator: give Patricio the short steps. He starts the exe with recording on (recording is on by default in non-public builds, D14), plays from the title screen through a new game, then about 1 minute of a fight, and tells the orchestrator when done. He decides nothing else.
**What you do:**
```
cd <REPO_ROOT>
Start-Process -FilePath .\build\MythologyKombat.exe -ArgumentList '--disc "<REPO_ROOT>\ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue"'
```
When you are done, close the game and run:
```
Get-ChildItem build\saves\diagnostics -Directory | Sort-Object LastWriteTime | Select-Object -Last 1 | ForEach-Object FullName
```
Tell the orchestrator the folder name.
**Accept when:** Patricio confirms the session is done; a new session folder exists under `tests\replays\local\` (git-ignored); the session is recorded as user-reported.

## T3.4 Strict replay of the new recording, twice, with negative control (agents)
Run `replay_diagnostics.py <session> --exe <T3.1 exe> --disc <cue> --game game.toml --output <new private dir>` twice. Run `tools\run_replays.ps1` (with `-ExecutionPolicy Bypass`) on the recording. Run one negative control: a changed input row or a different exe build.
**Accept when:** both strict replays succeed; the negative control reports a mismatch; `tools\run_replays.ps1` prints pass or fail for the recording; the recording stays git-ignored.

## T3.5 Phase 3 gate review (agents, runs last)
Depends on: T3.1, T3.2, T3.4, T3.6 to T3.26. T3.3 and T3.4 wait for the user's recording. If the user descopes any of T3.3, T3.4, T3.20 or T3.22 to T3.24, the gate records that choice, as D17 did for T2.10.
Adversarial reviewer only, as in T2.23. Check that no game data is tracked (`git ls-files`); the T3.1 hash in the docs matches the built exe; each doc claim maps to a `tools\` script; the T3.3 session is recorded as user-reported, not agent-observed.
**Accept when:** PASS. Then stop and report to the user.

## T3.6 Perf measurement hygiene (agents)
Depends on: T3.1. Owner: agents. Source: `docs\PERF_AND_ENGINEERING_IDEAS.md` section 1 (items 1, 2, 5), section 6, and question 222.
`tools\perf_run.ps1` writes a `run_<name>.meta.txt` with: the effective video settings from `build\settings.toml` (`internal_resolution`, `supersampling`, `antialiasing`, `dynamic_resolution`, `vsync`, and the fullscreen key if present), the power plan (`powercfg /getactivescheme`), the GPU and driver (`Get-CimInstance Win32_VideoController`), the psxrecomp and recomp-ui pins with their dirty state, and the exe SHA-256. Add `vsync` and `internal_resolution` to the session metadata too. Turn the scratch script `work\scratch\tele.py` into a stdlib tool under `tools\` that prints the vblank percentiles and the share above 33 ms.
**Accept when:** a run writes the meta file; two runs with the same settings give the same meta lines, except the run name and time; the meta matches `build\settings.toml`; the new tool gives the same output twice on the same telemetry folder.

Done note: the "session metadata" part is implemented in the run meta file (`work\perf\run_<name>.meta.txt`), not in `session.json`, because `session.json` is written by the exe. Question 222 stays open. In the meta, `video.supersampling` shows the raw key from `settings.toml`, while the game log reports the preset-derived value (for example 4 against 9x). Read both. Usage is in `docs/SETUP.md` (T3.6).

## T3.7 1x vs 4K resolution A/B (USER + agents)
Depends on: T3.6. Owner: USER + agents. Source: `docs\PERF_AND_ENGINEERING_IDEAS.md` section 1 item 2 and section 3.1.
Question: does the 4K setting (9x) cause missed vblanks on this laptop? The evidence so far is a correlation across sessions, not a test. The test is one visible minute per variant, on the same route.
**What you do:** from the repo root, save your current settings first:
```
cd <REPO_ROOT>
Copy-Item build\settings.toml work\settings_before_ab.toml
```
1. Variant 1 (1x): open the launcher Settings, set the internal resolution to Native (1x), then close the launcher. Start the game:
```
Start-Process -FilePath .\build\MythologyKombat.exe -ArgumentList '--disc "<REPO_ROOT>\ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue"'
```
Play the same route: title screen, a new game, then about 60 seconds of a fight. Close the game.
2. Variant 2 (4K): set the internal resolution to 4K in the launcher. Start the game and play the same route. Close the game.
3. Restore your settings:
```
Copy-Item work\settings_before_ab.toml build\settings.toml -Force
```
4. Find the two session folders (run once after each variant, or list them all):
```
Get-ChildItem build\saves\diagnostics -Directory | Sort-Object LastWriteTime | Select-Object -Last 2 | ForEach-Object FullName
```
Tell the orchestrator the folder names and say in one line each what you saw (stutter, tearing, picture). That is user-reported, not agent-observed.
**Accept when:** both sessions exist with the T3.6 meta; agents report, per variant, the share of non-movie intervals above 33 ms; the rule in `PERF_AND_ENGINEERING_IDEAS.md` section 3.1 (highest setting with the share under 1%) is applied; a change to the default is written to `docs\DECISIONS.md` only if the user agrees; `build\settings.toml` matches `work\settings_before_ab.toml`.

## T3.8 Vsync and window mode A/B (USER + agents)
Depends on: T3.6. Owner: USER + agents. Source: `docs\PERF_AND_ENGINEERING_IDEAS.md` items 3 and 9, section 3.2, question 168. D9 keeps the vsync default. Do not change it without this visible test.
Variants: `vsync = "off"` (the current default), `"adaptive"`, and `"on"`. If the launcher offers a fullscreen or borderless option, add it as a fourth variant (the key name is not verified).
**What you do:** save your settings as in T3.7, then for each variant change `vsync` in the launcher, or edit it by hand:
```
cd <REPO_ROOT>
Copy-Item build\settings.toml work\settings_before_ab.toml
notepad build\settings.toml
```
In Notepad, set the `vsync` line in the `[video]` section, save and close. Then start the game as in T3.7 and play the same minute. Repeat for each variant. Restore with `Copy-Item work\settings_before_ab.toml build\settings.toml -Force`. Tell the orchestrator the session folder for each variant and one line on what you saw.
**Accept when:** each variant has a session with the T3.6 meta; agents report p50, p90 and p99 of the host interval and the share above 33 ms per variant; any default change is proposed in `docs\DECISIONS.md` and made only with the user's yes; the settings file is restored.

## T3.9 Sampling profile of the Release exe during the FMV (USER + agents)
Depends on: T3.6. Owner: USER + agents. Source: `docs\PERF_AND_ENGINEERING_IDEAS.md` section 1 item 3, section 2 items 16 and 17. The 13 to 14 ms per FMV frame is in AOT code, and no profile shows where. Do this before any PGO, LTO or SIMD work.
**What you do:** open PowerShell as Administrator (not verified that this is needed on this PC). Then:
```
cd <REPO_ROOT>
New-Item -ItemType Directory -Force work\perf | Out-Null
wpr -start CPU -filemode
Start-Process -FilePath .\build\MythologyKombat.exe -ArgumentList '--disc "<REPO_ROOT>\ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue"'
```
Let the first movie (LEGAL.STR) play for about 60 seconds, then close the game and run:
```
wpr -stop work\perf\fmv_cpu.etl
```
Tell the orchestrator when the trace is saved.
**Accept when:** the trace is in `work\perf\` (git-ignored); agents report the top sampled code by count, with names only where `symbols.toml` or the generated code allows; the report says whether the cost is in AOT code, the interpreter, the GL driver or the audio path; question 256 is updated.

## T3.10 PGO and LTO trial (agents)
Depends on: T3.6, T3.7, T3.8, T3.9. Owner: agents. Source: `docs\PERF_AND_ENGINEERING_IDEAS.md` items 6, 7 and section 3.4. Only if T3.9 points at compiled code.
PGO is a flag-only change. The profile is empty today (`docs\SETUP.md`). Training uses the disc, locally only. Upstream says not to set `PSX_PGO` in CI. LTO is tried only after PGO, and only if its gain is clear of the run-to-run spread.
Measure with three runs per variant, all at the same settings from T3.6. Report the FMV `workG` median and the `host_interval_us` p99.
Every relink changes the exe hash and breaks strict replay. Adopting either flag needs the replay baseline refresh (the T3.2 pattern) and the user recording on the final exe (T3.3, D14, D15).
**Accept when:** three runs per variant, with meta; a `docs\DECISIONS.md` entry records adopt or reject, with the numbers; if adopted, the new exe hash is recorded and a baseline task is added to `docs\TASKS.md`; no generated C is edited (the hash list is unchanged).

## T3.11 Launcher screenshots at default and user scale (USER)
Depends on: T3.1. Owner: USER. Source: `docs\LAUNCHER_DESIGN.md` section 6. The five UX items are user-reported. Their causes are hypotheses until seen, so screenshots come first.
**What you do:** first read your display scale. 96 means 100 percent:
```
(Get-ItemProperty 'HKCU:\Control Panel\Desktop\WindowMetrics').AppliedDPI
```
Then start the launcher the way you normally do, using the same command as before:
```
cd <REPO_ROOT>
New-Item -ItemType Directory -Force work\screens | Out-Null
Start-Process .\build\MythologyKombat.exe
```
After each view, run this in the same PowerShell window to save the whole screen as a PNG in `work\screens`:
```
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
[System.Drawing.Graphics]::FromImage($bmp).CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
$bmp.Save((Join-Path (Resolve-Path work\screens) ("shot_" + (Get-Date -Format HHmmss) + ".png")))
```
Views to capture: the main page with the game loaded, the main page scrolled to the bottom, the Settings page, the Analog/D-pad area, and the Renderer dropdown open. Tell the orchestrator the DPI number and the folder. The screenshots stay in `work\` and are not committed.
**Result (2026-10-20):** DPI is 120 (`AppliedDPI`, which is 125 percent). Five images are in `work\screens\`: `shot_230017.png` (main page), `shot_230036.png` (main page scrolled), `shot_230049.png` (Settings top), `shot_230059.png` (Settings scrolled) and `shot_230113.png` (Mods/Features). The Renderer dropdown-open view was not captured, so item 5b shows the closed combo only. Findings are in `docs\LAUNCHER_DESIGN.md` section 6.1. Items 1, 2, 3, 5a and 5b are seen in the images; item 4 is partly seen (spacing above the Keyboard row); 5c is not confirmed. The window-size cause is a hypothesis, not tested. The images are agent-viewed, not run live.
**Accept when:** at least one screenshot for each of the five items in `docs\LAUNCHER_DESIGN.md` section 6; the DPI number is recorded; section 6 is updated from hypothesis to observed for each item.

## T3.12 Launcher fixes as local patch files (agents)
Depends on: T3.11, T3.13. Owner: agents. Source: D19, `docs\LAUNCHER_DESIGN.md` section 6 and section 8 item 6.
Each fix is a patch file under `patches\launcher\`, applied at build time by a step the implementer adds (CMake or a script; record which). The `recomp-ui\` submodule is not edited. Fixes, after the screenshots:
1. Scroll on the main section (design item 1).
2. Disc or game icon in place of the calendar-like placeholder (item 2; uses the choice from T3.13).
3. Filename wrap (item 3).
4. Window size as a dropdown (item 5a).
5. Renderer combo width so the OpenGL label fits (item 5b).
6. Bottom padding for the Analog/D-pad area and the other padding items (item 4, item 5c), after the screenshots show which element is meant.
Each fix has a before and after screenshot in `work\screens`. Each states whether it goes upstream; that is the user's call (`LAUNCHER_DESIGN.md` section 8 item 6). A relink changes the exe hash, so the user recording (T3.3) comes after this task.
**Accept when:** the patches apply cleanly to the pinned submodule on a clean checkout of the pin; `git -C recomp-ui status --short` prints nothing after the build; the exe builds; before and after screenshots exist for each fix; no unrelated screen changes; section 6 of `docs\LAUNCHER_DESIGN.md` records the outcome.
**Result (2026-10-20):** done. Seven patches are in `patches\launcher\` (0001 to 0007). `tools\apply_launcher_patches.ps1` applies them to a copy under `work\recomp-ui-patched`; the submodule stays clean. Steps are in `docs\SETUP.md` ("Launcher patches and screenshots"). Outcomes are in `docs\LAUNCHER_DESIGN.md` section 6.2. The window-clipping hypothesis is refuted. The fixes are agent-measured; item 4 (patch 0004) awaits the user's confirmation. Dependency on T3.13 is resolved through route (b), the disc glyph (patch 0002). Upstream: the call is the user's (`LAUNCHER_DESIGN.md` section 8, item 6).

## T3.13 Box art and disc icon source and licence (USER)
**Status: superseded, optional.** T3.12 took route (b), a neutral disc glyph drawn by patch 0002, with no copyrighted art. Route (a) is not needed unless the user later wants real art. The user was told and did not object, but has not explicitly confirmed this. Do not start this task unless the user asks for box art.
Depends on: T3.11. Owner: USER. Source: question 246, `docs\LAUNCHER_DESIGN.md` section 6 item 2.
Two routes: (a) an image you own or may use, for the `LAUNCHER_BOXART` option in `CMakeLists.txt`, which is commented out now; or (b) a disc glyph drawn by a patch, using `recomp-ui\assets\consoles\psx\img\disc.tga` (its licence was not checked). Do not use a third-party box-art source without the rights to it.
**What you do:**
```
cd <REPO_ROOT>
Get-Item recomp-ui\assets\consoles\psx\img\disc.tga
Get-ChildItem recomp-ui -Recurse -Filter NOTICE.md | Select-Object FullName
```
Then reply to the orchestrator with (a) the file you choose and the permission you have for it, or (b) "disc glyph".
**Accept when:** the choice and its licence are recorded, and question 246 is closed. No image is committed unless the user approves it.

## T3.14 Licence for this repo's own files (USER + agents)
Depends on: none. Owner: USER + agents. Source: question 249, `docs\PUBLISHING_AUDIT.md` section 3 and blocker 2. No `LICENSE`, `NOTICE` or `COPYING` exists. psxrecomp is PolyForm Noncommercial, recomp-ui is MIT, and OpenBIOS is MIT. The audit read only the start of the psxrecomp licence.
**What you do:** read the full licence files, then reply in chat with the licence you choose for this repo's own files (`tools\`, `docs\`, `symbols.toml`, `seeds\`, `aot\overlays.json`, tests):
```
cd <REPO_ROOT>
Get-Content psxrecomp\LICENSE
Get-Content recomp-ui\LICENSE -TotalCount 5
Get-Content psxrecomp\THIRD_PARTY_ATTRIBUTION.md -TotalCount 40
```
Agents then add `LICENSE` for our files and `NOTICE`, which lists each third-party component the kit ships with its licence file, using the notices in `recomp-ui\assets\` and `psxrecomp\bios\OpenBIOS.LICENSE`.
**Accept when:** the choice is recorded in `docs\DECISIONS.md`; `LICENSE` and `NOTICE` exist and are tracked by git; `NOTICE` names each third-party component the kit ships.

## T3.15 Path, email and derived-data decisions, then the scrub (USER + agents)
Depends on: T3.14. Owner: USER + agents. Must be done before T3.23. Source: questions 250 and 251, `docs\PUBLISHING_AUDIT.md` section 1a, section 2 and blockers 3 and 4.
**What you do:** run these to see the facts:
```
cd <REPO_ROOT>
git log --all --format="%an <%ae>" | Sort-Object -Unique
git grep -c -F "%USERPROFILE%" -- . ":!psxrecomp" ":!recomp-ui"
```
Then reply in chat with three answers:
1. Local paths: scrub them (agents replace them with relative paths or `%RETRO_TOOLS_DIR%`), or keep them.
2. Author email: keep it; use a GitHub noreply address for future commits only; or rewrite the history before the first push. A rewrite cannot be undone after the push.
3. Derived files `DISC_MAP.md`, `FORMATS.md`, `SYMBOLS.md`, `EXE_OVERLAYS.md`, `COVERAGE.md` and the replay digests: allow them in the public repo, or remove them from the public tree.
Agents carry out the answers, then re-run the scans in `docs\PUBLISHING_AUDIT.md` section 1 and record the counts.
**Accept when:** each of the three answers is recorded in `docs\DECISIONS.md`; the scans show the agreed result; no history rewrite happens without the user's explicit yes.

**Status 2026-10-20 (in-progress):** answers recorded in D20 to D23 (licence, paths, history plan, derived docs). Paths scrubbed (D21). Remaining: the history rewrite (D22). It runs only as the last step before T3.23, after all other commits, with a backup bundle and the user's final yes. Then re-run the scans in `docs\PUBLISHING_AUDIT.md` section 1 and record the counts. The email text in `docs\PUBLISHING_AUDIT.md` is question 266.

## T3.16 No-game-data guard script (agents)
Depends on: none. Owner: agents. Source: `docs\LAUNCHER_DESIGN.md` section 5 (`guard` row).
Write `tools\check_no_game_data.py`. It is stdlib only and reads `git ls-files`. It fails on any tracked path under `generated/`, `ps1_game/` or `work/`; any `*.bin`, `*.cue`, `*.iso`, `*.exe`, `*.dll`, `*.zip`, `*.ovr`, `*.str` or `*.mcd`; `overlay_captures.json`; and any file whose first 8 bytes are `PS-X EXE`. It allows the derived files named in D8.
**Accept when:** exit 0 on the current repo; a negative test in a temp git repo under `work\` with a planted `.bin` and a file with the `PS-X EXE` header each exits 1 and names the file; output is the same on two runs.

## T3.17 CI on GitHub-hosted runners (agents)
Depends on: T3.16, T3.18. Owner: agents. Source: D25, D24, `docs\LAUNCHER_DESIGN.md` section 5 (CI rows, revised by D25).
GitHub-hosted runners have no disc, so CI never builds the game (D25). CI builds and tests only the launcher, the setup-host and the tools. Add `.github\workflows\ci.yml` with three jobs, all on GitHub-hosted runners:
1. `guard` (ubuntu-latest): runs `tools\check_no_game_data.py` (T3.16) on the git tree.
2. `emitters-test` (windows-latest, recursive submodules): installs the toolchain, builds `psxrecomp\recompiler`, then runs `ctest`.
3. `setup-host-build` (windows-latest, clean clone, recursive submodules, no `generated\`): configures with the setup-host flags from T3.18, builds `psx-runtime`. It fails if the configure log says "linking generated game C", if a `generated\` folder exists, or if the configure or ninja graph mentions `generated/overlays_static` (D24).
Toolchain version: v1.0.14, as in `docs\SETUP.md`. How the pin is applied is open (question 247).
Rules: no job has a disc or a game file. CI does not run `generate` or `rebuild`. CI does not set `PSX_PGO`. CI does not `git add -f` any artifact. The launcher or tool artifacts may be uploaded as workflow artifacts, never committed.
**Accept when:** the YAML parses, checked with a tool named in the report; the `guard` job gives the same result as T3.16 on the repo; the workflow runs green on the first push (T3.23), or each failure is listed as a new task.

**Status 2026-10-21 (done, with one part deferred):** the workflow file, the local checks and the adversarial review passed (commit `717ee78`). The first run on GitHub is not done. It is deferred to T3.23. Until then the GitHub side is unverified. Details are in `docs/SETUP.md` ("CI (T3.17)") and open questions 286 to 290.

## T3.18 Setup-host build in the repo, and the first wizard run (agents + USER)
Depends on: T3.1. Owner: agents + USER. Source: `docs\LAUNCHER_DESIGN.md` sections 2 and 5, `docs\PUBLISHING_AUDIT.md` section 4 and question 258.
Agents build the setup-host exe (`PSXRECOMP_FORCE_SETUP_HOST=ON`, `PSX_SETUP_WIZARD=ON`, no game C) in `build-setup\`, which `.gitignore` already covers. Use the generator and commands in `docs\SETUP.md`. Also decide question 258 (fix the modified psxrecomp files or document them) and question 257 (keep the pin or bump it; a bump needs the T3.2 baseline refresh).
**Status 2026-10-20 (in-progress):** agent part measured and recorded in `docs\SETUP.md` (Setup-host build, T3.18): exe hashes, timings and the fresh clone test. Question 258 closed; question 257 closed (pin kept at `449c31e5`). D24 records that dev-tree setup-host exes must not go in the kit. Remaining: the user's first wizard run (the steps are in `docs\SETUP.md`), then the result is recorded and the task is closed.
**D25 note (2026-10-21):** the setup-host exe is the fallback and developer path. The release is the prebuilt game zip (T3.19). D24 still holds: a setup-host exe built in a dev tree never goes in a release.

**What you do** (when the agents ask, for the first wizard run on this machine):
```
cd <REPO_ROOT>
Start-Process -FilePath .\build-setup\MythologyKombat.exe
```
Pick the disc in the wizard, then tell the orchestrator each step and any error text. The wizard may generate and compile, which takes several minutes.
**Accept when:** the configure log has no "linking generated game C"; `build-setup\MythologyKombat.exe` exists; a fresh clone in `work\clone-test` (with `--recurse-submodules`, no `generated\`) configures and builds it; the exe hash is recorded in `docs\SETUP.md`; question 258 is closed; the wizard run is recorded as user-reported.

**Status note 2026-10-21 (wizard run agent-observed, not user-reported):** The first wizard run was done by agents in `work\clone-test`, with the clone exe `b4e9d186...`. Patricio did not take part. The run is in `docs\SETUP.md` (First wizard run). Met: exe built (`build-release\MythologyKombat.exe`, SHA-256 `17ca5c78...`), fresh clone builds, hash recorded, question 258 closed. Not met as written: the run is recorded as agent-observed, not user-reported. Patricio's own run is still open. The orchestrator sets the status; this note does not change the status column.

## T3.19 Local release script `tools\release.ps1` (agents; USER runs it and uploads)
Depends on: T3.12, T3.14, T3.16, T3.18. Owner: agents (the script). USER (the run and the upload). Source: D25, D8, D16, D24, `docs\LAUNCHER_DESIGN.md` section 2 (revised by D25).
The release game build is made on the user's PC, from the user's disc. The script is run by hand at release time. It is not a pre-commit step. `tools\release.ps1` does these steps in order:
1. Takes a clean checkout of a tag (a fresh clone, or a worktree under `work\`, with recursive submodules). It stops if the tree is dirty or the tag does not exist.
2. Takes the disc as a parameter (`-Disc`, the path to the `.cue`). In that checkout it runs `verify-disc`, `generate` and `rebuild` through `tools\run_psxrecomp.ps1`. Generated code stays in the checkout.
3. Builds the game exe. It includes the launcher (recomp-ui is linked into it, `LAUNCHER_DESIGN.md` section 3).
4. Packages the game zip from an allow-list: the release exe, its launcher files, `mods\`, `LICENSE`, `NOTICE`, a version file and the settings defaults. It excludes the disc, saves, recordings, BIOS dumps and memory cards.
5. Runs a release content check on the zip. It fails on any `.bin`, `.cue`, `.iso`, `.chd` or `.mcd` file, on any session recording, and on any path under `ps1_game\`. It names each file it rejects.
6. Writes `checksums.txt` (SHA-256 of the zip).
7. Stops. It does not upload anything.
Outputs go to `work\release\` (git-ignored). The upload is a separate step, run only after the user says yes in chat. It creates a draft first: `gh release create <tag> <zip> checksums.txt --draft`. Publishing the draft is a second explicit yes.
Do not call `scripts\package_release.sh` (bundled packager). Do not call `psxrecomp\tools\package_setup_host.sh` (retired).
**What you do** (USER, after the agents say the script is ready). The real parameters, from `tools\release.ps1`:
```
cd <REPO_ROOT>
git status --short
git tag --list "v*"
powershell -NoProfile -ExecutionPolicy Bypass -File tools\release.ps1 -Version <x.y.z> -Disc "<REPO_ROOT>\ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue" [-Ref <commit>] [-Draft] [-Repo owner/name] [-Pgo] [-KeepDisc]
```
- Without `-Ref`, the tag `v<x.y.z>` must exist. The script stops if it does not.
- `-Draft` prints the exact `gh release create ... --draft` command. It runs that command only after you type `UPLOAD` in an interactive window. Case matters.
- `-Publish` is not implemented. Publishing a draft is a separate, explicit step.
- `-Pgo`, `-KeepDisc` and `-Repo` are described in the script's header.
- Do not run the upload in a non-interactive session. The script does not upload there.
**Accept when:** from a clean checkout at a tag, the script runs with the user's disc and writes the zip and `checksums.txt` to `work\release\`; the content check passes on the zip; a test copy with a planted `.bin` or `.cue` makes the check fail and name the file; `checksums.txt` matches the zip; `git status` is clean after the run; the only upload is the draft, and only after the user's yes.

**Status 2026-10-21 (done):** the script, the content check, its 18 tests and the smoke script passed review (commit `717ee78`). A test run wrote `work\release\test\`. Its zip is `MythologyKombat-test-Windows-x64.zip`. The user's own run with the real version is still to do, and the draft upload is still to do. Details are in `docs/SETUP.md` ("Local release script (T3.19)") and open questions 280 to 296. Decisions are in `docs/DECISIONS.md` (D26).

## T3.20 Optional: self-hosted runner for the game build (USER + agents)
Depends on: T3.17, T3.19. Owner: USER + agents. Optional: the user decides. Source: D25, `docs\LAUNCHER_DESIGN.md` section 5.
A GitHub Actions self-hosted runner on the user's PC can run the same steps as T3.19 when a version tag is pushed. The disc never leaves the PC.
Rules:
- The runner runs on the user's PC only. Its label is chosen in this task and written in `docs\SETUP.md`.
- The disc path comes from a local environment variable set on that PC. The variable name is chosen in this task. The path is never in the repo, in a workflow file or in chat.
- The workflow runs only on a version tag that the user pushed (`v*`). It does not run on pull requests, and it does not run for forks.
- It creates a draft release only. Publishing is the user's step (T3.19).
- Check whether the repo's tag rules can limit who may push `v*` tags. Not verified.
**What you do** (USER, when the agents ask):
```
[Environment]::SetEnvironmentVariable("<variable name chosen in T3.20>", "<REPO_ROOT>\ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue", "User")
```
The runner install commands are on the GitHub page at Settings, Actions, Runners, New self-hosted runner. Run them in a PowerShell window yourself. Do not paste the runner token in chat.
**Accept when:** the user confirms the runner is registered; with the user's yes, a test tag produces a draft release from the runner; `git grep` for the disc file name finds nothing in the tracked tree; a pull request from a fork does not start the job; each failure becomes a question or a task.

## T3.21 Launcher updater: check, verify, replace, keep saves (agents)
Depends on: T3.19. Owner: agents. Source: D25, question 252, question 284, `docs\LAUNCHER_DESIGN.md` section 4 (proposal, revised by D25).
Step 1, research first: read how Hell's Gate Recomp and Shaolin Monks Recomp update, from their public source and release assets. Record the findings in `docs\LAUNCHER_DESIGN.md`. Then choose the mechanism: a launcher-built-in updater (a patch under `patches\launcher\`, D19), or an upstream one if one exists. Record the choice as a new entry in `docs\DECISIONS.md`. `recomp-ui\` is not edited.
Behaviour:
- Calls `GET https://api.github.com/repos/<owner>/<repo>/releases/latest` and compares the tag with the local version file.
- If the release is newer, downloads the game zip and `checksums.txt` and checks the SHA-256. A mismatch is refused, and nothing is replaced.
- Replaces the game build. Keeps `saves\`, `settings.toml`, `bios\` and the disc path.
- Keeps the previous build until the new one has started once (rollback).
- Never downloads or stores a disc.
The data-version check in the older design does not apply. The release is a prebuilt game build, so the player does not regenerate.
**Accept when:** against a local test server or a test release: (1) a newer version is found and installed; (2) a checksum mismatch is refused and nothing is replaced; (3) saves and settings survive the update; (4) the previous build stays until the new one has run once.

## T3.22 Clean-machine test of the downloaded zip (USER)
Depends on: T3.19. Owner: USER. Source: `docs\PUBLISHING_AUDIT.md` section 6 and blocker 12, `docs\LAUNCHER_DESIGN.md` section 3, D25, questions 255 and 275. This is the acceptance test for the release zip. It needs a second Windows machine or a VM with only your disc. Test the zip you download (a draft release asset, or the copy in `work\release\`), not this PC's build.
**What you do:**
1. Put your disc in a folder outside the repo. Copy the `.cue` and the `.bin` by hand, or:
```
New-Item -ItemType Directory -Force "$env:USERPROFILE\Discs\MK" | Out-Null
Copy-Item "<path to your .cue>" "$env:USERPROFILE\Discs\MK\"
Copy-Item "<path to your .bin>" "$env:USERPROFILE\Discs\MK\"
```
2. Download the zip from the draft release page, or copy it to the test machine by USB. The zip name is set in T3.19. Then:
```
Expand-Archive -Path "$env:USERPROFILE\Downloads\MythologyKombat-<version>-windows-x64.zip" -DestinationPath "$env:USERPROFILE\MythologyKombat"
Get-ChildItem "$env:USERPROFILE\MythologyKombat" | Select-Object Name, Length
```
3. Start the program:
```
Start-Process "$env:USERPROFILE\MythologyKombat\MythologyKombat.exe"
```
4. In the launcher, pick the `.cue` from `Discs\MK`, check the verdict, and press PLAY. Note any error text.
5. Check that no disc file is in the folder:
```
Get-ChildItem "$env:USERPROFILE\MythologyKombat" -Recurse -Include *.bin,*.cue,*.iso,*.chd,*.mcd,*.ovr,*.str | Select-Object FullName
```
6. Report: the Windows version (`(Get-CimInstance Win32_OperatingSystem).Caption`), each step and its result, whether the game reaches the title screen, the time from PLAY to the title screen, and any Smart App Control message.
**Accept when:** the user confirms the game starts from the zip on the test machine; agents record the steps, times and errors as user-reported; the check in step 5 finds nothing; each failure becomes a question or a task.

## T3.23 First push to GitHub, history rewrite (D22) and first CI run (USER + agents)
Depends on: T3.15, T3.17, T3.19. Owner: USER + agents. Source: `docs\PUBLISHING_AUDIT.md` sections 1 and 8, D22, D25.
A push is hard to undo, because the author email is in the history. The order is fixed by D22: all other commits first, then a backup bundle, then the history rewrite only after the user's final yes, then the push. The repo has no remote today.
**What you do:** create an empty GitHub repo first, under a name you choose (public or private is your choice). Then:
```
cd <REPO_ROOT>
git status --short
git ls-files | Select-String -Pattern "^(ps1_game|work|generated|build)/"
git bundle create "$env:USERPROFILE\MythologyKombat-backup.bundle" --all
```
The `Select-String` line must print nothing. The bundle goes outside the repo. Then tell the orchestrator and say yes in chat to the rewrite. The agents run the rewrite and report the author list. After that, you run:
```
git remote add origin https://github.com/<your-github-user>/<repo-name>.git
git push -u origin master
```
Do not create a tag or a release until you say so.
**Accept when:** the bundle exists outside the repo; `git log --all --format="%ae" | Sort-Object -Unique` shows only the noreply address after the rewrite (D22); the user confirms the push; agents report the first CI run (T3.17), green or with each failure listed as a task; no tag or release exists without the user's yes.

## T3.24 Code-signing decision for the release exe (USER)
Depends on: T3.19. Owner: USER. Source: question 244, question 255, `docs\LAUNCHER_DESIGN.md` sections 2 and 8 item 3, D25. Smart App Control may block an unsigned exe (question 255, not tested). The release exe is built on your PC (D25), so the GitHub-secrets signing route in the older design does not fit. Options, not decided: (a) sign locally in `tools\release.ps1`, with a certificate kept on your PC; (b) ship unsigned, and say so in the README. A certificate costs money. The choice is yours.
**What you do:**
```
cd <REPO_ROOT>
Get-Content docs\LAUNCHER_DESIGN.md | Select-String -Pattern "Smart App Control|signing"
```
Reply in chat: (a) sign locally, or (b) ship unsigned. Do not paste a certificate, its password or its file path in chat.
**Accept when:** question 244 is closed in `docs\OPEN_QUESTIONS.md`; if (a) is chosen, the release script signs the exe and `Get-AuthenticodeSignature` on the exe in the zip reports Valid; if (b) is chosen, the README says the release is unsigned.

## T3.25 README rewrite and legal wording (agents + USER)
Depends on: T3.14, T3.15, T3.21, T3.22, T3.24. Owner: agents (doc-writer) + USER (the legal wording, question 245). Source: `docs\PUBLISHING_AUDIT.md` section 7, D25.
Rewrite `README.md` in the style of the Shaolin Monks Recomp README: download the zip, extract it, start the exe, select your disc, PLAY. Include the checksums (`checksums.txt`), the status (D17), the requirements, the controls link (`docs\CONTROLS.md`), troubleshooting, the update check (T3.21), the signing status (T3.24), the licence and credits, and the legal note.
Legal rules (D25):
- The README must not say the program contains no game-derived code. The release zip contains a program built from the game's code.
- It states what the zip contains and does not contain, as the T3.19 content check shows. The disc image, saves, recordings, BIOS dumps and memory cards are not in the zip.
- The player supplies their own disc.
- The wording about game data depends on question 280 (whether the exe holds game data bytes, not only code).
- The current `README.md` line 9 says the repo holds no game code. That is true of the repo, and it is replaced by the rules above.
**What you do:** reply in chat with the legal wording you approve, or with changes. Check the draft with:
```
cd <REPO_ROOT>
Get-Content README.md
```
**Accept when:** every section in the audit's section 7 exists, or is marked "not yet"; the README makes no claim of "no game code"; the legal note is the wording the user approved (question 245); each claim maps to a doc, a script or the T3.19 content check; the player steps match the zip from T3.19 and the updater from T3.21.

## T3.26 Reproducibility of the release exe (agents)
Depends on: T3.19. Owner: agents. Source: question 274, D14, D15, D24, T2.20.
Two exes of the same size had different hashes (question 274): `ff813773...` (T3.1, dev tree) and `17ca5c78...` (wizard build). The released exe needs a known hash, and the user's recordings are tied to one exe hash (D14, D15).
Steps: build the same tag twice from two clean clones and compare the SHA-256 of the exe. Then compare a dev-tree build with a clean-clone build. Find the cause of any difference (for example timestamps, paths or the toolchain). Record the cause in `docs\SETUP.md`. Record the hash of the released exe in `docs\CHANGELOG.md` at release time.
**Accept when:** two clean builds of the same tag give the same SHA-256, or each difference is explained and recorded with its cause; the released exe hash is recorded; any framework-level fix goes upstream first (`CLAUDE.md`), or is recorded as a question.

## Backlog (not scheduled, no task IDs yet)

These are ideas only. Each needs its own task before work starts.

| Item | Related |
| --- | --- |
| Further playtest of other levels and movies | Open questions 237, 238, 232 |
| Embedded Python, pinned or offline toolchain, offline kit (formerly T3.26). Not needed by the prebuilt release route (D25) unless the fallback kit is used | Q247, Q253, Q254 |
| Enhancements | `docs\ENHANCEMENTS.md` |
| Overlay toolchain and KUSEG shard (left for later, `docs\PERF_AND_ENGINEERING_IDEAS.md` item 5). Intel driver update and GPU choice (item 4) are USER system changes, not scheduled | Q99, Q190 |

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
| Box art or icon source and its licence | Q246 | T3.12 (choose before patches) |
| Repo licence for this repo's own files | Q249 | T3.14 |
| Path and email scrub, history rewrite, derived-data scope | Q250, Q251 | T3.15 (before T3.23) |
| Pushing the repo to GitHub | — | T3.23 |
| Publishing a locally built release exe: draft first, then a public release (each a separate yes) | D25, Q281, Q285 | T3.19, T3.22 |
| Running a self-hosted runner on this PC, and its disc-path variable | D25, Q282 | T3.20 |
| Code-signing for the release exe (sign locally or ship unsigned) | Q244 | T3.24 |
| Legal wording for the README and release page | Q245, Q280, Q285 | T3.25 |
| Shipping the release exe with translated game code (takedown risk accepted, no legal opinion) | D25, Q285 | T3.19 |

### Open questions for the user

1. Which BIOS dump exists (model, for example SCPH-1001), and may we ask for its path if OpenBIOS fails?
2. May `aot\overlays.json` (hashes, offsets, addresses, sizes), `symbols.toml`, seeds and test routes be committed (Q75)?
3. May strict-replay recordings ever be committed?
4. Is a full Python 3.12 install acceptable if the embeddable one cannot run the framework CLI?
5. Can you play through all nine level functions (T2.17), or only the early levels?
6. May the first launch open a normal window while agents run the debug server on port 4370?
