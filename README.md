# MythologyKombat

A native Windows 11 port of Mortal Kombat Mythologies: Sub-Zero, the PS1 NTSC-U version. The game's code is recompiled into a native Windows program. The port is built on PSXRecomp: https://github.com/RetroPortingToolKit/psxrecomp

It is a fan project. It does not include the game. You need your own copy.

## What it is

- A static recompilation of the PS1 game's executable code, built as a Windows program.
- It uses PSXRecomp and recomp-ui (the launcher).
- You supply the disc. The release never includes it.

## Install

### Requirements

- Windows 11, 64-bit.
- Your own legally obtained copy of Mortal Kombat Mythologies: Sub-Zero, PS1 NTSC-U (serial SLUS-00476), as a `.cue` file with its `.bin` file.
- A graphics driver that supports OpenGL. The default renderer uses OpenGL.

### Steps

1. Open the Releases page of `PAumedes/MythologyKombat` on GitHub. Download the Windows zip, `MythologyKombat-<version>-Windows-x64.zip`, and `checksums.txt`. Take both from the same release.
2. Check the SHA-256 hash. In PowerShell, in the folder you downloaded to, run:

   ```
   Get-FileHash .\MythologyKombat-<version>-Windows-x64.zip -Algorithm SHA256
   ```

   Find the line for the zip in `checksums.txt`. The hash must match. The letter case of the hex digits does not matter. If it does not match, download the zip again and do not extract it.
3. Extract the zip. Use a folder you can write to, not Program Files. The game writes its saves and settings next to the exe.
4. In the extracted folder, run `MythologyKombat.exe`.
5. In the launcher, select your own disc (the `.cue` file).
6. Press PLAY.

### What the zip contains

| Holds | Does not hold |
|-------|---------------|
| `MythologyKombat.exe`, a recompiled build of the game's executable code | Your disc image |
| `bios\openbios.bin`, the free OpenBIOS image | Saves, memory cards or recordings |
| `game.toml`, with disc digests and file names | A PlayStation BIOS dump |
| `overlay_toolchain\`, `licenses\`, `NOTICE`, `LICENSE` | |
| `manifest.json`, `update.cmd` and `update.ps1` | |

### Troubleshooting

- Hash does not match: download the zip again. Do not run the exe.
- The window does not open: the default renderer needs a working OpenGL driver. Update the graphics driver. A test in a virtual machine is in question 310 of `docs\OPEN_QUESTIONS.md`.
- The disc is not accepted: use the NTSC-U disc (serial SLUS-00476) with its `.cue` and `.bin`.

## Status and known issues

- The main menu, a new game and a fight were reached in play tests (user reports).
- Movies: 23 of the 28 movie files were never reached in testing. See `docs\DECISIONS.md` (D17).
- Movie speed: the movies may run slower on some machines. The cause is not known. On the dev PC the movies ran at about 60 fps with vsync off, which is the default. See `docs\OPEN_QUESTIONS.md` (question 313).
- Midway logo audio: in some release runs an audio stall started at the first movie. It was not reproduced on a quiet machine, and the cause is not known. If it happens, capture a log as described in `docs\SETUP.md` ("Known issue: Midway logo audio on the release zip").
- The Sony logo did not show in play tests. The cause is not known (`docs\OPEN_QUESTIONS.md`, question 115).
- Unsigned program: the release exe is not code-signed (D30). Windows SmartScreen may show a warning. Smart App Control may block the exe. This is not tested on a clean PC (question 255). Check the SHA-256 hash before you run it.
- The controls list is incomplete. See `docs\CONTROLS.md`.

## Updating

In the game folder (the one with `MythologyKombat.exe`), open PowerShell and run:

```
.\update.cmd
```

- The updater shows the new version and asks `y/N`. It installs only if you type `y`. Close the game first.
- `.\update.cmd -CheckOnly` checks for a new release and changes nothing.
- `.\update.cmd -DryRun` runs the checks and the plan, and changes nothing.
- `.\update.cmd -Rollback` restores the previous build.

The updater keeps `saves\`, `settings.toml`, `input.ini`, `keybinds.ini`, `disc.cfg`, `bios.cfg`, `launcher-window.ini`, `mods\state.toml`, `mods\texture-packs\`, `cache\` and `overlay_captures.json`. It never starts the game. It talks only to GitHub. It checks the SHA-256 from `checksums.txt` before it unpacks anything. Details are in `docs\SETUP.md` ("Updater (T3.21)") and `docs\DECISIONS.md` (D29).

## Settings and controls

- `game.toml` holds the defaults. It sets vsync off by default.
- The launcher writes `settings.toml`. Its values override `game.toml`.
- The framework writes `keybinds.ini` next to the exe on first run. Edit it and restart to change the keys.
- The keys are listed in `docs\CONTROLS.md`. The list is incomplete.

## Building from source

Building needs the toolchain, the framework and your own disc on your PC. See `docs\SETUP.md` for the steps. Generated game code is never committed to git.

## Credits

- PSXRecomp, by RetroPortingToolKit and Matthew Stanley (PolyForm Noncommercial 1.0.0).
- recomp-ui, the launcher, by Matthew Stanley (MIT).
- OpenBIOS, from the PCSX-Redux project (MIT).
- Other components and their licences are listed in `NOTICE`.

## License

The files in this repository are licensed under the PolyForm Noncommercial License 1.0.0 (see `LICENSE`). Copyright (c) 2026 Patricio Aumedes. Noncommercial use only: no commercial use. This port stays free. Third-party components keep their own licences (see `NOTICE`).

## Legal

- This project is not affiliated with, and not endorsed by, Midway, Warner Bros. or NetherRealm.
- Trademarks belong to their owners.
- The project does not include the game disc, movies, audio or textures. You must supply your own legally obtained copy of the game.
- The release program is a recompilation of the game's executable code. It is provided for noncommercial, educational and interoperability purposes, with no warranty.
- No retail BIOS is included. The release uses OpenBIOS, a free BIOS image with its own licence.
- You are responsible for complying with the laws that apply to you.
