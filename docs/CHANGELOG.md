# Changelog

- Kit created: CLAUDE.md, subagents, Phase 0–1 task list.
- T0.1 Initialise the repo safely: `git init` on branch master; first commit fa5df2b holds the 16 kit files, and ps1_game/ and work/ are confirmed git-ignored.
- T0.2 Prerequisite check script: `tools\check_prereqs.ps1` prints PRESENT, MISSING or TOO OLD with version and path for each required tool; exits 0; installs nothing.
- T0.3 Install missing prerequisites: portable tools unzipped under `<RETRO_TOOLS_DIR>`; `tools\check_prereqs.ps1` shows all 9 tools PRESENT and exits 0; no installers run.
- T0.4 Identify and fingerprint the disc: `tools\disc_identify.py` reads the cue, SHA-256 of the .bin, and the serial SLUS-00476 from SYSTEM.CNF (NTSC-U); writes `work\disc_identity.json`; hashes and serial in `docs/DISC.md`.
- T0.5 Add PSXRecomp and build the framework: PSXRecomp added as submodule at `psxrecomp\`, pinned to 449c31e; recompiler, OpenBIOS regen and runtime build succeed; default recompiler build exits 1 because two upstream test targets fail to link, so explicit targets are used.
- T0.6 Decide how to scaffold the game project: upstream `setup_project.ps1` run in `work\scaffold-test\`, then no-clobber copy into the repo root; `game.toml` paths edited; recomp-ui submodule pinned to 7c635c6; project configures with CMake exit 0; `generated\` kept git-ignored.
- T1.1 List every file on the disc: `tools\disc_list.py` writes `work\disc_files.json`; 211 files in 22 directories, 468367066 file bytes, 27 XA-flagged files in /MOVIES, 0 audio tracks; table in `docs/DISC_MAP.md`.
- T1.3 Classify every file by format: `tools\disc_classify.py` tags all 211 files and extracts them to `work\extracted\` (about 530 MB); 1 PS-X EXE, 28 STR video, 8 overlay candidates, 37 unknown; tags and evidence in `docs/FORMATS.md`.
