# DECISIONS

_Filled in by the doc-writer as tasks pass review._

## D1 Build the framework with explicit targets (T0.5)

- Context: the default recompiler build exits 1 because two upstream test targets fail to link with this toolchain.
- Decision: build `psxrecomp-bios psxrecomp-game` for the recompiler, and `psx-runtime` for the runtime. Do not use the default build.
- Reason: with these targets the recompiler, the BIOS regen and the runtime all build. The failing test targets were not built.
- Upstream source is not modified. See `docs/SETUP.md` and `docs/OPEN_QUESTIONS.md` (question 12).

## D2 Pin PSXRecomp to one commit (T0.5)

- Decision: the `psxrecomp\` submodule is pinned to `449c31e5029f3a3281fa15060105928d2b3b13f7`.
- Reason: the task asks for a pinned submodule commit. The exact hashes are in `docs/SETUP.md`.

## D3 Scaffold the game project in a temp folder, then copy (T0.6)

- Context: the upstream PSXRecomp setup script creates a new project folder. This repo already exists.
- Decision: run the upstream `setup_project.ps1` in `work\scaffold-test\`. Then copy its output into the repo root. The copy does not overwrite existing files.
- Not chosen, and why:
  - Running the script in place. It always creates a new folder. It runs `git init`, makes its own commit and adds submodules. Those would fight the existing history.
  - Writing the files by hand. That would drift from the upstream templates and lose the values read from the disc.
- Reason: the copy gets the upstream templates and the disc-derived values, and keeps the repo history clean.
- Divergence from upstream: `generated\` stays git-ignored. Upstream commits `generated\` for its release CI. `CLAUDE.md` forbids committing generated C, so the upstream release CI templates will not work as-is. Decide later. See `docs/OPEN_QUESTIONS.md`.
- Details of the run are in `docs/SETUP.md`.

## D4 Do not register REA. Use Ghidra headless instead (T1.5)

- Context: REA (`rea-agents` 6.7.0) was tested to open the boot EXE through Ghidra. Its inspect command fails with `unsupported binary format`. REA does not list MIPS as a raw-binary architecture. Its Windows Ghidra support is documented as experimental for x86, x64 and ARM PE files.
- Decision: do not register REA. Do not run `rea-agents setup`. Use Ghidra directly, through `analyzeHeadless` and any post-scripts. The Ghidra GUI has not been opened by anyone. Using it is an optional user step (see `docs/SETUP.md`, T1.5).
- Not chosen, and why:
  - Registering REA with `setup`. Setup writes to `~/.claude.json` and `~/.claude/skills`, and REA cannot open this EXE.
  - Registering REA at project scope with `claude mcp add --scope local`. This was not tested.
  - A raw binary import in Ghidra. It found 1934 functions, against 1730 with the PS1 loader.
- Reason: the PS1 loader gives an entry point and text range that match T1.4. REA cannot read the EXE.
- Revisit if REA adds MIPS, or if a community Ghidra MCP server (ReVa or GhidraMCP) is wanted. Neither was researched.
- Details are in `docs/SETUP.md` (T1.5). Open items are in `docs/OPEN_QUESTIONS.md` (59 to 61).

## D5 Python for the upstream CLI (T2.1)

- Context: the upstream `psxrecomp_cli.py` must run. The embeddable Python from T0.3 ignores `PYTHONPATH` and reads its `._pth` file instead. The T0.6 workaround used a private Python copy.
- Decision: run `psxrecomp_cli.py` with the unmodified embeddable Python at `<RETRO_TOOLS_DIR>\python\python.exe`. Do not pass `-I`. The CLI puts `psxrecomp\tools` on `sys.path` itself (`psxrecomp_cli.py` line 34, and again near line 2241). So the `._pth` limit does not matter. No full Python install is needed.
- Fallback, used only if the first option fails: a private copy at `work\py-psxrecomp`. The script `tools\run_psxrecomp.ps1` creates it. Its `python312._pth` gets `psxrecomp\tools`, `psxrecomp\tools\new_project_layout` and `psxrecomp`, plus `import site`. It was tested, and it also passes `verify-disc`. The test hook is the environment variable `PSXRECOMP_FORCE_PRIVATE_PY=1`.
- The retro-tools install is never modified.
- Our own tools keep using `python -I`.
- The TASKS.md text named `work\py-scaffold`. The fallback that was built is `work\py-psxrecomp`.
- Not chosen, and why:
  - A full Python install. It is not needed, as stated above.
- Open items are in `docs/OPEN_QUESTIONS.md` (78 to 80). Question 26 is resolved by this decision.
- Details are in `docs/SETUP.md` (T2.1).

## D6 Work around the duplicate manifest in the game exe build (T2.4)

- Context: the `psx-runtime` link fails with `duplicate resource: type MANIFEST`. psxrecomp and recomp-ui both add a manifest to the same target. This is an upstream bug. No upstream option turns off the recomp-ui manifest.
- Decision: in the root `CMakeLists.txt`, after `psxrecomp_add_game_runtime`, on Windows with a non-MSVC compiler, remove `psx-runtime_recomp_utf8_manifest.rc` from the `psx-runtime` sources.
- Not chosen, and why:
  - Editing the recomp-ui or psxrecomp submodule. Upstream source is not modified (see D1).
  - Turning off the manifest with an upstream option. No such option exists.
- Reason: the two manifests say the same things, so dropping recomp-ui's loses nothing. The link works.
- Risks: the workaround depends on recomp-ui's generated file name. Under MSVC, psxrecomp adds a `.manifest` source that the guard matches, so there is no duplicate there. The workaround is not used under MSVC.
- Revisit when upstream fixes the guard. See `docs/OPEN_QUESTIONS.md` (98) and `docs/SETUP.md` (T2.4).

## D7 Keep build\ as the shipping exe. Test with work\build-dbg (T2.5)

- Context: the T2.4 Release exe, `build\MythologyKombat.exe`, is built with `PSX_DEBUG_TOOLS=OFF`. Its TCP debug server is off, so port 4370 never opens. The headless smoke test needs that server.
- Decision: keep `build\MythologyKombat.exe` as the shipping exe. The T2.6 user run uses it. Build a second, debug-tools exe in `work\build-dbg\` (git-ignored). The smoke test uses it by default.
- Not chosen, and why:
  - Turn on `PSX_DEBUG_TOOLS` in `build\`. Not done. It would change the shipping exe. Open as question 103.
- Reason: the user run needs no debug server. The automated test does.
- Details are in `docs/SETUP.md` (T2.5). Open items are in `docs/OPEN_QUESTIONS.md` (103).

## D8 Commit derived symbol and address data, never game data (T2.21)

- Context: question 75 asked whether the derived files may be committed. These are address lists, names, sizes and hashes, not game data.
- Decision: the user answered yes (Patricio, through the question tool). The following may be committed:
  - `symbols.toml`
  - `psx_symbols.h`
  - `seeds\ghidra_funcs.txt`
  - `catalog_identity.json`
  - `game.toml`
  - `.recomp.json`
  - Later: `aot\overlays.json` and test routes
- Still never committed: game data, `generated\`, extracted files, BIOS dumps, and any `work\` output. `CLAUDE.md` lists these rules.
- Replay recordings are a separate question. See `docs/TASKS.md`, open question 3.
- T2.18 used this decision. `tests\replays\routes\` and `tests\replays\expected\` are committed. Recordings, screenshots, saves and game bytes are not. Details are in `docs/SETUP.md` (T2.18).
- Reason: the user's answer. Run `git status` before every commit, as `CLAUDE.md` requires.
- Details are in `docs/SETUP.md` (T2.21). Open items are in `docs/OPEN_QUESTIONS.md` (140 to 147).

## D9 FMV pacing fix is a vsync setting, not a code change (T2.10)

- Status: approved by the user. Default is now `[video] vsync = "off"` in `game.toml` (set in the T2.10 follow-up). User-reported: with vsync off the movie audio was clean. Telemetry (`tools\session_fps.py`, `cd_xa` not 0): 59.9 Hz mean with vsync off, 51.9 Hz with vsync on.
- Implementation: `[video] vsync = "off"` added to `game.toml`, and staged to `build\game.toml` (and `work\build-dbg\game.toml`). Config only: the value is read at run time by `config_loader.cpp`, so no relink or regeneration. `game.toml` is copied beside the exe by a POST_BUILD `copy_if_different`, so the next build keeps it. The player's `build\settings.toml` (written by the launcher) overrides `game.toml` and held `vsync = "on"`; it was changed to `"off"` (backup: `work\settings.toml.bak_vsync_on`). A player whose own `settings.toml` says `"on"` still gets vsync on. `build\game.toml` also has `multitap_analog = true` under `[controller]`, which the repo `game.toml` lacks. The user reports that the launcher adds it. `build\` is git-ignored.
- Honored (agent, hidden window, Release exe, no `PSX_VSYNC`, `tools\perf_run.ps1 -Name V0`): the log prints `present cadence: wall-clock pacer (16.6639 ms/frame)`, not `driver vsync`. FMV phase guest rate min/median/max 58.8/60.0/61.0 Hz, 0 underruns. Pre-FMV median 60.0, max 60.1 Hz. The "0 underruns" figure applies to the FMV window only. `work\perf\run_V0.log` pre-FMV sample 5 shows guest 29.68 Hz with underruns +12735 (see question 166 for a similar dip in run G).
- Speed: not running fast. With vsync off the wall-clock pacer is deadline-based and still caps the guest at about 60 Hz (see the comment above `present_effective_swap_interval` in `psxrecomp\runtime\src\main.cpp`). The 69.6 Hz mean in question 223 is the mean of per-interval host rates over bursty intervals, which is biased upward; it is not a sustained rate. Not checked: sustained gameplay speed in a visible window (the user reported no speed problem). Adaptive was not needed.
- Context: hidden-window Release runs show the FMV at about 50 Hz with vsync on, and 60.0 Hz with vsync off. Per-frame guest cost is about 13 ms. Details are in `docs/SETUP.md` ("FMV speed measurement (Release, hidden window)").
- Decision: treat the FMV pacing problem as a vsync setting. Do not change game code for it yet. ~~The test is `PSX_VSYNC=0` in one visible-window run. If the user agrees, the setting becomes `[video] vsync = "off"` in `game.toml`.~~ Superseded: the user approved, and `[video] vsync = "off"` is now in `game.toml` (see Status).
- Not chosen, and why:
  - Changing the FMV decode or the overlay path. The FMV decode runs in the exe's AOT code, not in interpreted overlays. Staging the overlay toolchain would not fix the FMV rate.
  - A PGO or LTO build first. Headroom is thin, and the build was not tested.
  - Treating `PSX_VSYNC=0` as uncapped. The wall-clock pacer still runs.
- Reason: with vsync off, the FMV phase median is 60.0 Hz, with 0 underruns. ~~This was measured in a hidden window only.~~ Superseded: the user has since reported clean audio in a visible window (see the paragraph below).
- The hidden-window run confirms 60 Hz; the user reports clean audio in a visible window. Tearing was not reported. Fallback if tearing appears: `"adaptive"`. Open items are in `docs/OPEN_QUESTIONS.md` (116, 155 and 162 to 170).

## D10 The runtime overlay check has no pc_break. It uses fn_filter, a write ring and host_pause (T2.13)

- Context: the native debug server has no `pc_break`, `pc_hit_last` or `pc_unbreak` commands. These are DuckStation-only, per `psxrecomp\docs\TCP_COMMANDS.md`. The pause, step and continue commands were removed upstream.
- Decision: watch the overlay load with these three parts:
  - `fn_filter` with `fn_entry_dump`. This records a0 to a3, ra, s0 to s3 and the frame at each function entry. Phase 1 filters `read_file` at `0x800861D4` (id and buffer). Phase 2 filters the memcpy wrapper at `0x8009F31C`.
  - `host_pause` after the memcpy entry.
  - A write-transition ring, armed at launch with `PSX_WTRACE_BOOT_RANGES=0x130FF8-0x13C720`. It logs value-changing CPU stores in the window. The window RAM is rebuilt just before and just after the copy by undoing newer entries in reverse order.
- Reason: the native server has no `pc_break`. This method gives a before and after view of the copy. The check for untraced writers (DMA, for example) found 0 inconsistencies.
- Limits: the ring has capacity 1 << 20. The pause lands inside the copy, so the tool resumes one frame and pauses again. See `docs/EXE_OVERLAYS.md` ("Runtime proof (T2.13)") and `docs/SETUP.md` ("Runtime overlay proof (T2.13)").
- Open items are in `docs/OPEN_QUESTIONS.md` (178 to 183).

## D11 Overlay strategy: runtime route now, AOT static route next, no DLL release route (T2.14)

- Context: the eight `.OVR` files all load at `0x80130FF8` (`docs/EXE_OVERLAYS.md`). Today they run through the runtime route. No overlay toolchain is staged. The startup log says `tcc tier active but no bundled toolchain at build\overlay_toolchain (overlay gaps -> interpreter)`. Measured for T2.14: 0 overlay native dispatches, and about 1,100 interpreter dispatches per second during the FMV. The FMV pace is set by vsync, not by the overlays (D9).
- Decision, in this order:
  1. Keep the runtime route working. This is the interpreter plus runtime autocompile, with `[runtime] overlay_cache = true` in `game.toml`. Nothing changes now.
  2. Next, the AOT static route. Write `aot\overlays.json` (T2.15) for the eight `.OVR` files. Set `static_output` to `generated/overlays_static.c`. Link that file into the exe with `GAME_OVERLAY_STATIC_C` (T2.16). The profile holds addresses, sizes and hashes only, so it may be committed (D8). The generated C stays git-ignored.
  3. Do not use the DLL cache or the `release` route now.
- Not chosen, and why:
  - The DLL cache with `release`. It ships audited DLL shards in a `cache\` folder. Those shards come from play or from a developer's machine (`psxrecomp\docs\AOT_SHARDING.md`, `psxrecomp\docs\COMPILING_OVERLAYS.md`, section 0). This repo has no release packaging yet. The cache also grows with play, which this local build does not need.
  - Runtime captures as the source. Captures come from play. The static route reads only the disc. No playthrough is needed (`psxrecomp\docs\AOT_SHARDING.md`, "Production pipeline").
  - Staging the overlay toolchain now. This decision does not do it. Question 99 stays open.
- Reason:
  - This is a local, single-user build.
  - No captures or playthrough are needed.
  - The output is deterministic from disc bytes. The upstream `static` step extracts, compiles and audits from the disc. It reuses its output when no input changes (`psxrecomp\docs\AOT_SHARDING.md`, "Linking recipes into the runtime").
  - The generated C stays git-ignored, as D8 and `CLAUDE.md` require.
  - T2.13 showed the window bytes equal the disc bytes after the copy, for TEMPLE.
- Assumption: no patching happens to the window after the copy. This is proven for TEMPLE only (T2.13). The other seven are pending (T2.17).
- The T2.14 "user commit answer" condition is met by D8 (question 75, answered yes). Nothing is built in T2.14.
- Risks and open items:
  - Only TEMPLE is runtime-proven. The static entries and `overlay_loader_status` checks for the other levels are T2.17.
  - The copy overwrites 16 bytes, `0x80130FFC` to `0x8013100B`. These were BIOS heap before the copy. Whether the game uses them is not known (`docs/EXE_OVERLAYS.md`, question 180).
  - Four overlays start with an address table: BRIDGE (32 words), FIRE (27), WATER (83) and WIND (102). Each needs an `excluded_ranges` entry (SHA-256 and reason) or a verified entry. Anything not proven stays listed as open. It is not weakened.
  - The `--cps` option must match the runtime build. This build has not been checked for it.
  - If the disc does not match `disc_hashes`, `static` exits 3 (`psxrecomp\docs\AOT_SHARDING.md`).
  - The AOT audit must pass, with guarded entries for every image (T2.16).
  - The static shard is a fixed snapshot. It does not grow with play (`psxrecomp\docs\COMPILING_OVERLAYS.md`, section 2).
  - Revisit if the interpreter fallback becomes a real cost. It is not the FMV bottleneck. Vsync is (D9).
- Open items are in `docs/OPEN_QUESTIONS.md` (99 and 180). See `docs/EXE_OVERLAYS.md` ("Overlay strategy (T2.14)").

## D12 AOT overlay profile: schema choices (T2.15)

- Context: D11 asks for `aot\overlays.json`. The upstream pipeline, `psxrecomp\tools\aot_overlay_pipeline.py`, defines the schema. It differs from the T2.15 text in `docs/TASKS.md`.
- Decision:
  - Use `fixed_address_extents` for the eight images, not `fixed_address_files`. The upstream `fixed_address_files` has no size or SHA-256 field. The pipeline reads size and SHA-256 only for extents.
  - Use `excluded_ranges` with absolute start and end addresses, a SHA-256 and a reason. Requires `strict_bounds` true. Used for the four images that start with an address table: `BRIDGE`, `FIRE`, `WATER` and `WIND`.
  - Use the `entries` list for the verified loader `jal` targets from the level functions.
  - Use disc names without a leading slash.
  - Use `hashlib` algorithms only for `disc_hashes` (MD5 and SHA-1). CRC-32 and `known_sizes` cannot be used.
  - Pin `expected_records` to 8. This is a count guard.
  - Replace `bcd_extent_table` with the words checks. Their agreement with the ISO extents is shown by `tools\overlay_facts.py`.
- Not chosen, and why:
  - `fixed_address_files`. It has no size or SHA-256 field.
  - `bcd_extent_table`. It cannot read this game's tables (4-byte location table, separate size table).
  - Dropping the checks that the schema cannot express. Not done. Each gap is listed as an open question.
- Reason: the upstream pipeline reads only the schema it defines. The profile must pass its checks, and every hash is asserted against the disc.
- Open items are in `docs/OPEN_QUESTIONS.md` (184 to 189). See `docs/SETUP.md` ("AOT overlay profile (T2.15)").

## D13 Run `generate` with the private Python copy (T2.16)

- Context: the static overlay step (T2.16) runs a subprocess from `psxrecomp\tools\aot_overlay_pipeline.py`. With the unmodified embeddable Python from T0.3, it failed with `ModuleNotFoundError: compile_overlays` at line 21. The subprocess does not get `psxrecomp\tools` on `sys.path`. The embeddable Python reads its `._pth` file, not `PYTHONPATH` (`docs/SETUP.md`, T0.6).
- Decision: `tools\run_psxrecomp.ps1` always uses the private copy `work\py-psxrecomp` for `generate`. The script reads `$args[0]` as the subcommand. For `generate`, it skips option (a), the unmodified retro-tools Python. Other subcommands keep option (a).
- Not chosen, and why:
  - Changing the upstream subprocess. Upstream source is not modified (D1).
  - Setting `PYTHONPATH`. The embeddable Python ignores it.
- Reason: the static step passed with the private copy. Run 1 printed `Verified 8 images / 8 recipes`.
- Risk: the check reads only the first argument. A global option placed before `generate` defeats it, so option (a) runs first. Reviewer minor. See `docs/OPEN_QUESTIONS.md` (196).
- Details are in `docs/SETUP.md` (T2.16). Open items are in `docs/OPEN_QUESTIONS.md` (190 to 196).

## D14 Recording is on by default in non-public builds. Public release is unchanged (T2.19)

- Context: playtests need a record of the inputs and a per-frame RAM digest. The upstream recorder is off by default in the source. The defaults script fails a public build unless the source says false.
- Decision: the diagnostics package ships with `recording` and `osd` on, in every build where `PSX_PUBLIC_RELEASE` is OFF. The switch is made in the staged copy of the manifest at build time. The source manifest keeps `default_enabled = false`. A public build (`PSX_PUBLIC_RELEASE=ON`) keeps both off.
- Not chosen, and why:
  - Setting `default_enabled = true` in the source. The defaults script would then fail a public build.
- Reason: the user plays non-public builds. The public release is unchanged: both features stay off.
- Rule for the user's recordings: the Release exe, `build\MythologyKombat.exe`, is the one the user plays on. Any further rebuild (for example T2.8 seed growth) must happen before the user records. A relink changes the exe SHA-256 and breaks strict replay (T2.20).
- Recordings are private. Never share or commit a session folder. See `docs/SETUP.md` (T2.19) and `docs/OPEN_QUESTIONS.md` (204).
- Open items are in `docs/OPEN_QUESTIONS.md` (203 to 212). Details are in `docs/SETUP.md` (T2.19).

## D15 Manual seed policy: WARN addresses need two independent checks, and the exe is frozen before user recording (T2.8)

- Context: `tools\grow_seeds.py` adds only ACCEPT addresses from `psxrecomp\tools\vet_seeds.py`. At T2.8, `0x8003A674` was ACCEPT and `0x80032760` was WARN. A WARN means the vet tool could not decide. The `0x80032760` head has seven instructions before its stack prologue. That is past the tool's 4-instruction window.
- Decision:
  1. The tool adds only ACCEPT addresses.
  2. A WARN address is added only with `--manual`, and only after a manual review by two independent disassemblies. The reason goes in the seed file as a `# manual ID: TEXT` comment.
  3. The exe is frozen before the user records. Any relink after that changes the exe SHA-256 and breaks strict replay (T2.20). Seed growth must happen before recording, as D14 says.
- Not chosen, and why:
  - Adding WARN addresses automatically. The tool cannot decide them.
  - Adding a WARN address on one disassembly. The policy needs two.
- Reason: `0x80032760` has 10,825 runtime dispatch misses on the test route, so it is reached on the test route. The vet tool cannot confirm it alone.
- Status: the manual seed `0x80032760` and the `--manual` option were checked by the implementer only. No reviewer has checked them (question 213).
- The current Release exe SHA-256 is `b5573bbe586f7669f3dfad11d3ca3a6f8888f8e37eb47eccdffbb8f201a7856b` (`docs/SETUP.md`, T2.8). Any relink before the user's recording changes it.
- Open items are in `docs/OPEN_QUESTIONS.md` (213 to 219). Details are in `docs/SETUP.md` (T2.8).

## D16 Replay recordings stay local and git-ignored (T2.20)

- Context: a recording folder holds `card1.mcd`, `card2.mcd` (copies of the starting cards), `inputs.csv` with a RAM digest per vblank, and `telemetry.csv`.
- Decision: copy sessions to `tests\replays\local\` and never commit them. `tests\replays\.gitignore` and the root `.gitignore` both ignore that folder. `tools\run_replays.ps1` replays them into `work\replay_out\`. Whether recordings are ever committed stays the user's decision (TASKS open question 3).
- Derived route metadata with no game data (button names, frame numbers) may be committed under D8. Nothing of that kind was added by T2.20.

## D17 User descopes T2.10 with the movies checked so far. T2.23 closes (T2.10, T2.23)

- Date: 2026-10-20.
- Context: T2.10 (FMV check) stayed `in-progress`. Only 5 of the 28 `/MOVIES` STR files were reached in any trace or report. Picture with vsync off was not reported for the two movies with a user report. T2.23 could not close until T2.10 was done or the user descoped it (`docs/TASKS.md`, gate notes).
- Decision: Patricio, the user, decided in chat to descope T2.10. T2.10 is accepted as `done` with the movies checked so far. The user recorded this as his own decision. T2.23 (Phase 2 gate review) is closed as `done` on the same decision. The gate review had PASSED on checks before this.
- Reason: the user's decision. It is not an agent finding.
- What remains untested or unreported:

| Item | State | Open question |
|------|-------|---------------|
| 23 of the 28 `/MOVIES` STR files | Never reached by any trace or report. Marked untested in the table in `docs/SETUP.md` | 238 |
| Picture with vsync off for `MIDWAY01.STR` and `SZINTRO1.STR` | Not reported. Audio with vsync off is reported as clean | 237 |
| Picture and audio for `LEGAL.STR`, `SZLOGO15.STR` and `OPEN.STR` | Read in traces. No picture or audio report | 148, 238 |
| Cause of the Midway logo "digital glitch" | Unknown. No code fix was made. Stutter is handled as the vsync setting (D9) | 237 |
| Which movie is the Sony logo | Not identified. No STR file is read before `LEGAL.STR` | 241 |
| `WIND.OVR` read before New Game | Cause unknown | 242 |

- Open questions that stay open: 148, 150, 162, 237, 238, 241 and 242. This decision closes none of them.
- Effect: the status of T2.10 and T2.23 changes in `docs/TASKS.md`. The FMV evidence in `docs/SETUP.md` is unchanged.
- Details are in `docs/SETUP.md` ("FMV check (T2.10) and first fight (T2.11)"). Open items are in `docs/OPEN_QUESTIONS.md`.

## D18 Release model: setup-host kit (2026-10-20)

- Context: `docs/LAUNCHER_DESIGN.md` (section 2, option A) and `docs/PUBLISHING_AUDIT.md` (section 8, blocker 1) left the release model open. Game C, any exe built from it, and disc-derived data may not be distributed (D8, `CLAUDE.md`).
- Decision (Patricio, in chat, 2026-10-20):
  - The release is a setup-host kit: a release zip with the launcher, the toolchain and the recompiler.
  - The player's PC runs `verify-disc`, `generate` and the compile once, from the player's own disc.
  - The launcher checks GitHub Releases for updates.
  - No game-derived code or data is ever distributed.
- Not chosen, and why:
  - Upstream bundled release (`LAUNCHER_DESIGN.md` option X1). It ships generated game C and the compiled game. D8 forbids it.
  - Source-only repo (option B). The design calls it the cheapest route with the worst player experience.
  - Own thin launcher (option C). Kept in the design as the fallback if the recomp-ui wizard proves too rough.
  - Retro Launcher catalogue entry (option D). Possible later. Retro's handling of setup-host kits is not verified.
- Reason: the user's choice. The design gives this as the only route with a download-and-run feel that also keeps D8.
- Open items (none decided yet): code signing (question 244), legal wording (245), box art licence (246), the toolchain pin at v1.0.14 (247), option E prebuilt framework libraries (248), and whether the toolchain ships inside the zip or is downloaded by the wizard (253). The design's option A has the wizard download it. D18 says the zip carries it. The two differ and are not reconciled.
- Tasks: T3.6 to T3.26 in `docs/TASKS.md`.

## D19 Launcher fixes are local patch files, applied at build time (2026-10-20)

- Context: `CLAUDE.md` says "upstream first" and reserves `patches/` for hooks and enhancements. The launcher is the `recomp-ui` submodule (MIT). `docs/LAUNCHER_DESIGN.md` (section 6) lists five user-reported UX items. D1 and D6 already keep upstream source unmodified.
- Decision (Patricio, in chat, 2026-10-20):
  - Launcher fixes are patch files under `patches\`, applied at build time.
  - The `recomp-ui\` submodule stays untouched.
  - The patches can be sent upstream later.
- Not chosen, and why:
  - Editing `recomp-ui\` in place. It breaks the pin and the upstream-first rule.
  - Forking `recomp-ui`. The fork-or-patch question (question 243) is answered by this decision as "patch".
- Reason: the user's choice. The fixes stay separate from the upstream code and can be proposed upstream later.
- Open items: which items come first, and the outcome after the screenshots (T3.11 and T3.12). The apply step (CMake or a script) and the upstream-or-local choice per item are set in T3.12. Question 243 is open for item order.
- Outcome (T3.12, 2026-10-20): the apply step is `tools\apply_launcher_patches.ps1` (a copy under `work\`, then `git apply`, not CMake). Patches 0001 to 0007 exist. Per-item outcomes are in `docs/LAUNCHER_DESIGN.md` section 6.2. Item 4 awaits the user's confirmation. Upstream choice per item is still the user's call.

## D20 Licence for this repo's own files: PolyForm Noncommercial 1.0.0 (2026-10-20)

- Decision (Patricio, in chat, 2026-10-20): the repo's own files are licensed under PolyForm Noncommercial License 1.0.0.
- Files: `LICENSE` and `NOTICE` at the repo root. Copyright line: `Copyright (c) 2026 Patricio Aumedes`.
- `NOTICE` names each third-party component the kit uses, with its licence and file. It also says that the game, its disc image and anything generated from game code are not covered and not distributed.
- Not verified yet, and open: the scope paragraph in `LICENSE` was written by an agent, and the user has not yet confirmed its wording or that `seeds\`, `aot\`, `symbols.toml` and `psx_symbols.h` are original to this repo (question 263). SDL3 and zlib licence texts are not in the tree (question 261). The `gl_core_3_1` licence is not stated (question 262).
- Reason: the user's choice. psxrecomp is PolyForm Noncommercial, so this port stays free (`CLAUDE.md`).
- Task: T3.14. Its `NOTICE` wording question (question 265) is open.

## D21 Local paths are scrubbed, not kept (2026-10-20)

- Decision (Patricio, in chat, 2026-10-20): local user paths in tracked files are scrubbed. Repo paths use `<REPO_ROOT>`. Retro-tools paths use `<RETRO_TOOLS_DIR>`. `CLAUDE.md` explains the placeholders (its line 41).
- Scan result (reported to the doc-writer in the task; not re-run by the doc-writer): only 3 literal pattern mentions remain, all in `docs\TASKS.md`. They are the scan commands and the acceptance text of T3.15.
- Scope: the current tree only. Older commits still hold the old paths and the author email. The history question is D22.
- Not chosen: keeping the paths. The user chose the scrub.
- Task: T3.15 (part). Question 250 is answered by D21 and D22.

## D22 Author email: history rewrite plan only, not done (2026-10-20)

- Decision (Patricio, in chat, 2026-10-20): the author email is replaced by a GitHub noreply address, by rewriting history before the first push. No rewrite has happened yet.
- Facts: the email is in 46 commits (`docs\PUBLISHING_AUDIT.md` section 1a). A rewrite cannot be undone once pushed.
- Rules, all from the user's answer:
  1. Rewrite only before the first push.
  2. The rewrite runs after all other commits are made.
  3. It is the last step before the T3.23 push.
  4. Make a backup bundle of the repo first.
  5. No rewrite happens without the user's final explicit yes in chat.
- Replacement identity: name `Patricio Aumedes`; email `12850986+PAumedes@users.noreply.github.com`. This comes from the GitHub login `PAumedes` (id 12850986), looked up with `gh api users/paumedes`. The repo-local git config `user.email` changes at that point, not before.
- The first commit `fa5df2b` was authored as `localuser`. The rewrite maps it to the same identity. Its hash will change after the rewrite.
- Not chosen: keeping the email, or using the noreply address for future commits only. The user chose the rewrite.
- Task: T3.15 (remaining part). Question 266 asks whether the email text in `docs\PUBLISHING_AUDIT.md` is also to be scrubbed.

## D23 Derived docs and replay digests may be public (2026-10-20)

- Decision (Patricio, in chat, 2026-10-20): these may be in the public repo: `docs\DISC_MAP.md`, `docs\FORMATS.md`, `docs\SYMBOLS.md`, `docs\EXE_OVERLAYS.md`, `docs\COVERAGE.md` and the replay digests.
- This widens D8, which named a shorter list. The rules of D8 still apply: no game data, no `generated\`, no extracted files, no `work\` output.
- Not covered: replay recordings. D16 keeps them local and git-ignored.
- Reason: the user's answer to question 251.
- Task: T3.15 (part).

## D24 Setup-host exe for the kit comes only from a clean build (2026-10-20)

- Finding (T3.18, measured by the implementer): with `PSXRECOMP_FORCE_SETUP_HOST=ON`, a dev tree that has `generated\` still compiles and links `generated\overlays_static*.c`. That is 9 extra objects and about 4.8 MB more. The cause is the overlay-static glob in `psxrecomp\runtime\overlay_static_sources.cmake` and `runtime.cmake` (about line 1612), which ignores `FORCE_SETUP_HOST`.
- Rule: a setup-host exe built in a dev tree holds game-derived code. It must never go in the kit.
- Rule: the kit exe and the CI setup-host exe are built from a clean clone or CI checkout with no `generated\` folder.
- Checks to add: T3.17 (CI) fails if there is no clean checkout, or if the configure or ninja graph mentions `generated/overlays_static`. T3.19 (kit) checks the content and builds from a clean clone.
- Clean-clone exe, measured: 32,589,824 bytes, SHA-256 `b4e9d186d918e0839631a80dbb267e075307627bae45471bb63ff4bfa8b711a3`.
- Open: the upstream glob bug (question 269).
- Task: T3.18. Steps in `docs/SETUP.md`.
