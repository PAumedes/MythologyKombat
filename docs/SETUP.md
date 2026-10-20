# SETUP

## Repo initialisation (T0.1)

The repo lives at `<REPO_ROOT>`.

- The repo was created with `git init`. The branch is `master`.
- First commit: `fa5df2bb544d52b2d604855a7aff9577e4d52eda`, titled "T0.1: Initialise the repo safely".
- The first commit holds 16 kit files. It holds no game data.
- Git ignores the game and scratch folders. This was checked with `git check-ignore -v`.

| Path | Git status | Check |
|------|------------|-------|
| `ps1_game/` | ignored | `git check-ignore -v` |
| `work/` | ignored | `git check-ignore -v` |

No `.bin` or `.cue` file is tracked.

No git user name is set on this machine. The first commit used a per-command author. See `docs/OPEN_QUESTIONS.md`.

## Prerequisite check (T0.2)

The script `tools\check_prereqs.ps1` checks the tools this port needs. Run it from the repo root:

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools\check_prereqs.ps1
```

The script checks these tools:

| Tool | Required version |
|------|------------------|
| Git | - |
| Python | 3.10+ |
| CMake | 3.20+ |
| Ninja | - |
| C/C++ compiler | clang, MSVC `cl`, or gcc (no version) |
| Java | 21+ |
| Ghidra | - |
| Node.js | 22+ |
| Emulator | DuckStation or PCSX-Redux (no version) |

It prints one line per tool. Each line shows a status, the version, and the path:

| Status | Meaning |
|--------|---------|
| PRESENT | Found, and the version is new enough |
| MISSING | Not found |
| TOO OLD | Found, but the version is below the required one |

The script exits with code 0 every time. It does not install anything and does not need admin rights. Read the printed lines to see what is missing.

First run on this machine:

| Tool | Status | Version | Note |
|------|--------|---------|------|
| Git | PRESENT | 2.56.0 | |
| CMake | PRESENT | 3.31.6 | Bundled with VS Build Tools, not on PATH |
| Ninja | PRESENT | 1.12.1 | Bundled with VS Build Tools, not on PATH |
| MSVC `cl` | PRESENT | 19.44.35229 | Found through the VS directory. Needs a Developer prompt to use |
| Python | MISSING | | |
| Java | MISSING | | |
| Ghidra | MISSING | | |
| Node.js | MISSING | | |
| Emulator | MISSING | | |
