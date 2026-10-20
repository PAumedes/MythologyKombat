# OPEN QUESTIONS

## Repo setup (from T0.1)

| # | Question | Notes |
|---|----------|-------|
| 1 | What git user name should commits use? | No git user identity is set on this machine. The first commit used a per-command author. The user is to choose the name. |
| 2 | Should `.claude/settings.json` also deny `Write` to `ps1_game/**`? | The current deny rule covers `Edit(ps1_game/**)` only. Reviewer suggestion. |
| 3 | Should `.gitignore` stop ignoring `*.exe` and `*.dll` everywhere? | A global ignore could hide legitimate tool binaries added later. Reviewer suggestion. |
