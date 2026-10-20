# Getting started

## 1. Put the kit in place

Unzip this kit into `<REPO_ROOT>`, so that `CLAUDE.md`, `.claude\`, `docs\` and `tools\` sit at the top of that folder. Your disc image (`.cue` + `.bin`) goes in `ps1_game\`.

## 2. Start Claude Code there

Open PowerShell:

```
cd <REPO_ROOT>
claude
```

Type `/agents` and check you see `implementer` (Sonnet), `adversarial-reviewer` (Sonnet) and `doc-writer` (Haiku). Press Esc to close the list.

## 3. Paste this message

```
Read CLAUDE.md and docs/TASKS.md. You are the orchestrator: don't write code yourself.
Work through the tasks in order. For every task: dispatch the implementer subagent,
then the adversarial-reviewer subagent on its result (loop up to 3 rounds on FAIL),
then the doc-writer subagent, then commit. Update the Status column in docs/TASKS.md as you go.
When you reach a USER task, tell me exactly what to do and wait for me.
Stop after T1.7 and give me a short summary of what we learned about the disc.
Start with T0.1.
```

## Tips

- It will ask permission before running commands. Approve the ones that look right; say no to anything touching `ps1_game\` other than reading.
- If a session ends midway, start `claude` again in the same folder and say: `Continue from docs/TASKS.md.` The task list is the memory.
- The task list stops at the end of Phase 1 on purpose. Come back with the results and we'll plan Phase 2 (first boot).
