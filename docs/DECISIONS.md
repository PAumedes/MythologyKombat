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
