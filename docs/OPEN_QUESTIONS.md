# OPEN QUESTIONS

## Repo setup (from T0.1)

| # | Question | Notes |
|---|----------|-------|
| 1 | What git user name should commits use? | No git user identity is set on this machine. The first commit used a per-command author. The user is to choose the name. |
| 2 | Should `.claude/settings.json` also deny `Write` to `ps1_game/**`? | The current deny rule covers `Edit(ps1_game/**)` only. Reviewer suggestion. |
| 3 | Should `.gitignore` stop ignoring `*.exe` and `*.dll` everywhere? | A global ignore could hide legitimate tool binaries added later. Reviewer suggestion. |

## Prerequisite check (from T0.2)

| # | Question | Notes |
|---|----------|-------|
| 4 | Should the 15 s timeout also cover a hung tool? | The script calls `ReadToEnd` before `WaitForExit`. So the timeout does not stop a tool that hangs. Reviewer note. |
| 5 | Should the Java version show more than major.minor? | The script shows Java as major.minor only. Reviewer note. |
| 6 | Should the messages say "22.0+" instead of "need 22.0"? | The messages say "need 22.0" without the "+". The required version is 22+. Reviewer note. |
| 7 | Do the Ghidra, emulator, gcc and clang checks work when the tool is installed? | The found case has not been tested for these four tools. Reviewer note. |

## Disc identity (from T0.4)

| # | Question | Notes |
|---|----------|-------|
| 8 | Does the sector count use the first track's sector size? | `tools\disc_identify.py` counts sectors with the first track's size. The disc has one track, so this is fine here. Reviewer note. |
| 9 | Is the serial regex search-based or anchored? | The serial match searches the `BOOT=` line. It is not anchored. Reviewer note. |
| 10 | What does the script say when the `.wav` audio file is missing? | The message mentions ".bin" when a `.wav` file is missing. Reviewer note. |
| 11 | Does the script handle multi-FILE cues and INDEX 00? | Only synthetic cues were tested. The real disc has one FILE and one track. Reviewer note. |

## PSXRecomp framework (from T0.5)

| # | Question | Notes |
|---|----------|-------|
| 12 | Why does the default `cmake --build recompiler/build` fail? | Two upstream test targets, `ws_cull_edge_interp_test` and `draw_distance_interp_test`, fail to link. The linker reports undefined symbols such as `gr_backend`. Built with `-O3 -flto` on clang 22. Reviewer reproduced it. Not checked whether upstream CI builds these targets with this toolchain. The workaround is to build explicit targets. |
| 13 | Should the submodule ignore CRLF noise? | `git status` shows `psxrecomp` as modified because of `core.autocrlf=true` on the tracked generated `OpenBIOS*` files. Possible fixes: `git config submodule.psxrecomp.ignore dirty`, or set `core.autocrlf` to false inside the submodule. Not applied. |
| 14 | Should the Vulkan SDK be installed? | The Vulkan SDK is absent, so the Vulkan renderer is a software stub. Not decided. |
| 15 | Should `psx-beetle` be built? | The target was skipped because `libmednafen_psx.a` is absent. Not decided. |
| 16 | What causes the `DEFAULT_BIOS_PATH` warning in `psx-oracle`? | The build prints the warning. The cause and effect are not checked. |
| 17 | Should the `.gitmodules` and gitlink commit be fixed? | `.gitmodules` and the `psxrecomp` gitlink were committed in the "T0.7" commit `beee35b` by accident of staging order. Not decided whether to rewrite history. |

## Game project scaffold (from T0.6)

| # | Question | Notes |
|---|----------|-------|
| 18 | Is 1 player right for the game? | `-Players 1` was passed. The value comes from the scaffold default. Not checked against the game. |
| 19 | What are the publisher and year? | Both are `TBD` in `catalog_identity.json` and `.recomp.json`. Needs real values. |
| 20 | Do the relative paths in `game.toml` work? | The disc path and the `work\disc` paths were set by hand. They need checking at the first Generate step. |
| 21 | Should `PSX_SETUP_WIZARD` be ON? | It is ON by default in the configure step. Not checked what it does. |
| 22 | Is the scaffold's default psxrecomp URL the same project? | The script default is `mstan/psxrecomp`. We use `RetroPortingToolKit/psxrecomp`. Not checked whether they are the same project. |
| 23 | How should release CI work without committed `generated\`? | Upstream commits `generated\` for its release CI. `CLAUDE.md` forbids committing generated C, so the release CI templates will not work as-is. Not decided. |
| 24 | Should the upstream scaffold bug be reported? | An empty `-Description`, `-Publisher` or `-Year` breaks `probe_disc.py`. Not reported. |
| 25 | Should `seeds\ghidra_funcs.txt` be renamed? | The file name says Ghidra, but the addresses come from the boot EXE's JAL targets. Not decided. |
| 26 | Should the scaffold's Python workaround be kept? | The embeddable Python ignores `PYTHONPATH`, so a private copy with a `._pth` edit was used. Not decided if this is needed again. |

## Disc file list (from T1.1)

| # | Question | Notes |
|---|----------|-------|
| 27 | Does `tools\disc_list.py` handle a multi-track cue? | Only the one-track cue of this disc was tested. Reviewer note. |
| 28 | Does `tools\disc_list.py` handle a non-NTSC-U disc? | Only the NTSC-U disc (SLUS-00476) was tested. Reviewer note. |

## Disc format classification (from T1.3)

| # | Question | Notes |
|---|----------|-------|
| 29 | What do the `.LVL` and `.WAL` magic containers hold? | 17 `.LVL` files start with `DD CC BB AA`. 12 `.WAL` files start with `33 22 11 00`. Meanings not claimed. |
| 30 | What do `SUBZERO.WMD` and `SUBZERO.WSD` hold? | They start with `SPSX` and `SSEQ`. Meanings not claimed. |
| 31 | What do the 46 offset-table containers hold? | Each starts with a leading u32 table. What the offsets point to is not checked. |
| 32 | What do the 28 u16-id-table containers (`.LSD`) hold, and how are the ids used? | Each is a u16 count, that many u16 ids, then a zero u16. Use not checked. |
| 33 | Why does `/LCDS/SZL2SFX2.LCD` have no paired id table, when the other 27 SZL `.LCD` files do? | `/LCDS/FIGHTSFX.LCD` also has no tag. Cause not checked. |
| 34 | What are the 37 unknown files? | 14 `.TXD` and 14 `.TSQ` in `/LEVELS/`, 8 `.BIN` files, and `/LSDS/FIGHTSFX.LSD`. Their contents are not analysed. |
| 35 | What load address does each overlay candidate use in RAM? | The 8 `.OVR` files have no known load address. Estimates only, for T1.4. |
| 36 | Is the overlay rule sound? | The rule uses a score, a prologue, a `jr ra` and a word count. Reviewer note: the signals are weak. |
| 37 | Are `/OVERLAYS/BRDGDEMO.BIN` and `/OVERLAYS/WINDDEMO.BIN` code? | Both pass the score test. They are rejected only by the prologue and `jr ra` rule. Reviewer note: both are 2048-byte halfword data. Meaning not known. |
| 38 | Why does `/LEVELS/WIND/WIND.TSQ` score 0.999 on the code test, yet tag as unknown? | Reviewer note. Not checked. |
| 39 | Is the comment at `tools\disc_classify.py` line 51 correct? | The comment says the non-code max score is below 0.65. The recorded max is 0.8676, for `/OVERLAYS/WINDDEMO.BIN`. Reviewer note. The comment needs fixing. |
| 40 | Why is the STR video submode bit `0x02` never set, and why are video sectors submode `0x48`? | The layout differs from the textbook STR layout. Cause not checked. Reviewer note. |
| 41 | Is there any TIM, VAB, VAG, SEQ or SEP data on this disc? | None is tagged. 233 TIM-like byte patterns were found, and all failed the block-size check. |
| 42 | Do later tools handle the `.raw2352` suffix on STR files? | Reviewer note. Not checked. |
| 43 | Does `tools\disc_classify.py` handle a wrong-region disc, a multi-track cue, or a missing file? | These paths are untested. Reviewer note. What `/NOXCUSES.BIN` (filler) and `/DOZER.BIN` (text, ends with `0x1A`) are for is also not known. |
