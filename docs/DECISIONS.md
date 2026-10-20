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
