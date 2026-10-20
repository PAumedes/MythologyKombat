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

- Status: pending. The user's visible-window test has not been run.
- Context: hidden-window Release runs show the FMV at about 50 Hz with vsync on, and 60.0 Hz with vsync off. Per-frame guest cost is about 13 ms. Details are in `docs/SETUP.md` ("FMV speed measurement (Release, hidden window)").
- Decision: treat the FMV pacing problem as a vsync setting. Do not change game code for it yet. The test is `PSX_VSYNC=0` in one visible-window run. If the user agrees, the setting becomes `[video] vsync = "off"` in `game.toml`.
- Not chosen, and why:
  - Changing the FMV decode or the overlay path. The FMV decode runs in the exe's AOT code, not in interpreted overlays. Staging the overlay toolchain would not fix the FMV rate.
  - A PGO or LTO build first. Headroom is thin, and the build was not tested.
  - Treating `PSX_VSYNC=0` as uncapped. The wall-clock pacer still runs.
- Reason: with vsync off, the FMV phase median is 60.0 Hz, with 0 underruns. This was measured in a hidden window only.
- Not confirmed. Do not call it a fix until the visible-window vsync-off run shows 60 Hz. Open items are in `docs/OPEN_QUESTIONS.md` (116, 155 and 162 to 170).
