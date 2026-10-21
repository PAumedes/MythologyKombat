# MythologyKombat — Mortal Kombat Mythologies: Sub-Zero (PS1) static recomp

Native Windows 11 port of the PS1 NTSC-U version, built on PSXRecomp
(https://github.com/RetroPortingToolKit/psxrecomp). Plan of record: the
"MK Mythologies: Sub-Zero (PS1) Recomp Plan" doc. Current work: Phase 0 (setup)
and Phase 1 (survey and naming). Task list: `docs/TASKS.md`.

## Repo layout

- `ps1_game/` — the user's own disc image (.cue/.bin). READ ONLY. Never modify, move or commit.
- `work/` — scratch: extracted disc files, Ghidra projects, dumps. Git-ignored.
- `psxrecomp/`, `recomp-ui/` — framework submodules (added in Phase 0).
- `tools/` — our scripts (Python 3 / PowerShell).
- `patches/` — hooks and enhancements (later phases).
- `docs/` — disc map, symbol notes, decisions, task list.
- `tests/replays/` — input recordings (later phases).

## How work is done: implement → adversarial review → document

The main session is the ORCHESTRATOR. It does not write code itself. For each task in `docs/TASKS.md`:

1. Pick the first task whose status is `todo` and whose dependencies are `done`. Mark it `in-progress`.
2. Dispatch the `implementer` subagent with: task id, full task text, acceptance criteria, relevant files.
3. Dispatch the `adversarial-reviewer` subagent with: task id, acceptance criteria, the list of changed files
   (`git status` / `git diff`), and the implementer's report. The reviewer must not see the implementer's reasoning beyond its report.
4. If the verdict is `FAIL`, send the findings back to the implementer and review again. Max 3 rounds.
   After 3 failed rounds, stop that task, mark it `blocked`, and ask the user.
5. On `PASS`, dispatch the `doc-writer` subagent to update `docs/` (and `docs/CHANGELOG.md`).
6. Commit with message `T<id>: <title>`, mark the task `done`, move to the next.

Stop and ask the user whenever a task needs something only they can do (installing software, providing a file,
a decision that can't be undone). Tasks marked `USER` are such steps: explain exactly what to do, then wait.

## Hard rules

- Never commit game data: nothing from `ps1_game/`, `work/`, generated C from game code (`generated/`),
  game binaries, or `overlay_captures.json`. Check `git status` before every commit.
- Generated code is never hand-edited: fix the recompiler or config and regenerate.
- No invented facts about the game. Unknowns go in `docs/OPEN_QUESTIONS.md`.
- Every claim about the disc must come from a script in `tools/` whose output can be reproduced.
- Windows paths: the repo root is the folder holding this file (written `<REPO_ROOT>` in docs; the retro-tools folder is `<RETRO_TOOLS_DIR>`, default `%USERPROFILE%\retro-tools`). Prefer PowerShell or Python; avoid bash-only scripts.
- Upstream first: before writing framework-level code, read the relevant PSXRecomp doc
  (`docs/GAME_PROJECT_SETUP.md`, `docs/AOT_SHARDING.md`, `docs/WIDESCREEN.md`, `CLAUDE.md` in the submodule).
- PSXRecomp is PolyForm Noncommercial: this port stays free.
