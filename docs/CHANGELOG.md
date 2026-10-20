# Changelog

- Kit created: CLAUDE.md, subagents, Phase 0–1 task list.
- T0.1 Initialise the repo safely: `git init` on branch master; first commit fa5df2b holds the 16 kit files, and ps1_game/ and work/ are confirmed git-ignored.
- T0.2 Prerequisite check script: `tools\check_prereqs.ps1` prints PRESENT, MISSING or TOO OLD with version and path for each required tool; exits 0; installs nothing.
- T0.3 Install missing prerequisites: portable tools unzipped under `<RETRO_TOOLS_DIR>`; `tools\check_prereqs.ps1` shows all 9 tools PRESENT and exits 0; no installers run.
