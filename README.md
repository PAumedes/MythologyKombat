# MythologyKombat

A native Windows 11 port of the PS1 NTSC-U version of Mortal Kombat Mythologies: Sub-Zero. The port is made by static recompilation. The disc code is turned into C and built as a native program.

The port is built on PSXRecomp: https://github.com/RetroPortingToolKit/psxrecomp

## What this repo does not include

- No game data. The repo holds no disc image, no extracted files and no generated code from the game.
- You need your own copy of the game on disc. Put the `.cue` and `.bin` files in `ps1_game\`. That folder is git-ignored.

## Licence

PSXRecomp is licensed under PolyForm Noncommercial. This port stays free. Do not use it for commercial purposes.

## Setup

See [docs/SETUP.md](docs/SETUP.md) for the steps to set up the tools, the framework and the project.

## Docs

The files in `docs\` describe the disc map, the symbols, the decisions and the open questions.
