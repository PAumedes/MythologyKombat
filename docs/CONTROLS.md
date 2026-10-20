# CONTROLS

This page is incomplete. Keys come from two sources. Each row says which.

- **User-reported**: Patricio pressed the key in the second play test (`docs/SETUP.md`, "Playtest 2"). No agent checked it.
- **Framework default**: the key is set in PSXRecomp source, in `psxrecomp\runtime\src\psx_keybinds.c` (lines 43 to 66) or `psxrecomp\runtime\src\host_keymap.c` (lines 90 to 120). The game was not tested with it.

The framework writes `keybinds.ini` next to the exe on first run. Edit it and restart to change the keys. The user's copy was not checked.

## Keys the user pressed

| Key | Pad button or function | What the user reported | Source |
|-----|------------------------|------------------------|--------|
| A | Triangle | Attack. Used for high or low kick or punch. Which move is not stated | User-reported. Default mapping from source |
| S | Circle | Attack. Used for high or low kick or punch. Which move is not stated | User-reported. Default mapping from source |
| Z | Square | Attack. Used for high or low kick or punch. Which move is not stated | User-reported. Default mapping from source |
| X | Cross | Attack. Used for high or low kick or punch. Which move is not stated | User-reported. Default mapping from source |
| Enter | Start | Pause | User-reported. Default mapping from source |
| Right Shift | Select | Select items | User-reported. Default mapping from source |
| Tab | Not a pad button. Host "Turbo" key | Fast-forward, 4x | User-reported. Default host key from source. The 4x value is not checked in source |
| F | Not a pad button. Host "DisplayPerf" key | Shows the fps counter | User-reported. Default host key from source |

## Framework defaults not reported

These keys are the framework default. The user did not report them, so they are not confirmed in the game.

| Key | Pad button | Source |
|-----|-----------|--------|
| Arrow keys (Up, Down, Left, Right) | D-pad. Also the left analog stick | Framework default |
| Q | L1 | Framework default |
| W | R1 | Framework default |
| E | L2 | Framework default |
| R | R2 | Framework default |
| T | L3 (stick click) | Framework default |
| Y | R3 (stick click) | Framework default |

## Host keys not reported

These are framework defaults for the window. None was reported. None was tested in this game.

| Key | Action | Source |
|-----|--------|--------|
| Alt+Enter | Fullscreen | Framework default |
| Ctrl+F | Fullscreen | Framework default |
| Keypad + and - | Volume up and down | Framework default |
| F6 | Scanlines | Framework default |
| F7 | Save state menu | Framework default |
| F8 | Rewind. Only in builds with `PSX_HAS_RBENGINE_SNAP`. Not checked for this build | Framework default |
| F9 | Turbo toggle | Framework default |
| Ctrl+L or F10 | Open launcher | Framework default |
| Ctrl+M | Capture mark | Framework default |

## Unknown

| Item | Status |
|------|--------|
| Key to quit the game | Not reported. The user asked about closing the window, and the answer was yes. See `docs/OPEN_QUESTIONS.md`, question 124 |
| In-game move for each attack key | Not reported |
| Whether the defaults above are what the user's `keybinds.ini` holds | Not checked |

See `docs/OPEN_QUESTIONS.md`, questions 124 and 125.
