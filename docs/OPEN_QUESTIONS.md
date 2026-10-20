# OPEN QUESTIONS

## Repo setup (from T0.1)

| # | Question | Notes |
|---|----------|-------|
| 1 | What git user name should commits use? | Resolved at the T1.7 gate. The git identity is now set in this repo's config to Patricio Aumedes. The first commit `fa5df2b` was authored as `localuser`. History was not rewritten. |
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
| 35 | What load address does each overlay candidate use in RAM? | Static answer in `docs/EXE_OVERLAYS.md` (T1.4): all eight load at `0x80130FF8`. Runtime check pending (question 44). |
| 36 | Is the overlay rule sound? | The rule uses a score, a prologue, a `jr ra` and a word count. Reviewer note: the signals are weak. |
| 37 | Are `/OVERLAYS/BRDGDEMO.BIN` and `/OVERLAYS/WINDDEMO.BIN` code? | Both pass the score test. They are rejected only by the prologue and `jr ra` rule. Reviewer note: both are 2048-byte halfword data. Meaning not known. |
| 38 | Why does `/LEVELS/WIND/WIND.TSQ` score 0.999 on the code test, yet tag as unknown? | Reviewer note. Not checked. |
| 39 | Is the comment at `tools\disc_classify.py` line 51 correct? | The comment says the non-code max score is below 0.65. The recorded max is 0.8676, for `/OVERLAYS/WINDDEMO.BIN`. Reviewer note. The comment needs fixing. |
| 40 | Why is the STR video submode bit `0x02` never set, and why are video sectors submode `0x48`? | The layout differs from the textbook STR layout. Cause not checked. Reviewer note. |
| 41 | Is there any TIM, VAB, VAG, SEQ or SEP data on this disc? | None is tagged. No file passes the structural TIM test in `tools\disc_classify.py`, and `work\disc_classes.json` has no TIM entries. The script does not report rejected TIM candidates (question 73). |
| 42 | Do later tools handle the `.raw2352` suffix on STR files? | Reviewer note. Not checked. |
| 43 | Does `tools\disc_classify.py` handle a wrong-region disc, a multi-track cue, or a missing file? | These paths are untested. Reviewer note. What `/NOXCUSES.BIN` (filler) and `/DOZER.BIN` (text, ends with `0x1A`) are for is also not known. |

## EXE header and overlays (from T1.4)

| # | Question | Notes |
|---|----------|-------|
| 44 | Do the EXE header, the crt0 values and the overlay load addresses match a debugger or Ghidra? | Partly answered in T1.5. Ghidra headless matches the entry point, text address and size, BSS range and heap start and size. Not yet checked in Ghidra: the overlay load addresses, GP, initial SP and the header's d, b and s fields. No emulator check is recorded. DuckStation cannot be queried automatically. See `docs/SETUP.md` (T1.5) and `docs/EXE_OVERLAYS.md`. |
| 45 | Where does the scratch read buffer come from, and does the memcpy into `0x80130FF8` overlap it? | The scratch allocator is at `0x800865C0`. crt0 starts the BIOS heap at `0x80130FFC`, inside the overlay window. The buffer may start near `0x80131000`, so the move may overlap. Not proven. The return value of the malloc(4) call at `0x8008652C` is unknown. |
| 46 | Which level is the second FIRE site at `0x8002E130`? | The level function at `0x8002E130` also reads id 137 (`/OVERLAYS/FIRE.OVR`). The level it belongs to is not known. |
| 47 | What do `/OVERLAYS/BRDGDEMO.BIN` and `/OVERLAYS/WINDDEMO.BIN` hold? | They are 2048-byte files. The BRIDGE and WIND level functions read them. They are not copied to the window. Their contents were not analysed. |
| 48 | What do the leading address tables in BRIDGE, FIRE, WATER and WIND mean? | The tables hold 32, 27, 83 and 102 words. The words point at data inside the file, not at function starts. Their use is not known. |
| 49 | What is the part of the text range from `0x800D7B40` to `0x800D8000`? | The crt0 BSS start (`0x800D7B40`) lies inside the file-backed text range. All file bytes in that part are 0. Their meaning is not established. |
| 50 | Do any other functions load overlays? | Two `read_file` calls use a variable id, at `0x80085CF8` and `0x80085D74`. The script does not resolve them. So the claim that only the nine level functions load overlays has a small gap. |
| 51 | Do FORTRESS and PRISON load at `0x80130FF8` for sure? | Both are confirmed by the address-constant check only. FORTRESS has no jal targets in the window. PRISON's jal result was not decisive. |
| 52 | Should `tools\exe_overlays.py` be fixed? | Two things in the script's text need fixing. (a) The docstring lines 13 to 17 describe function starts as "the word after `jr ra` plus delay slot". The script also treats the first word after a leading address table as a start. (b) The InitHeap note in the `unresolved` list says "per review". It should state the plain fact that the word at `0x800BF358` is `0x8000`. The tool is not changed by T1.4. |

## Symbol hunt (from T1.2)

| # | Question | Notes |
|---|----------|-------|
| 53 | Are there other regional releases (PAL, demo discs) worth checking for symbols? | Task T1.2 asks for this. Only the NTSC-U disc (SLUS-00476) has been scanned. Not decided which other discs to get or check. |
| 54 | Should `tools\symbol_hunt.py` match the form `Ver n`? | The version patterns miss the form `Ver n`. The reviewer found `PS-X Control TAP Driver Ver 3.0` in the EXE by hand. The tool is not changed by T1.2. Reviewer note. |
| 55 | What PsyQ library version is on the disc? | Answered as a best fit in T1.6: the PsyQ 4.0 signature set (`ghidra_psx_ldr` reports `PsyQ Version` 4.0.0). This is not an exact SDK identity. The RCS dates are not mapped to a release (question 68). See `docs/SYMBOLS.md`. |
| 56 | Is the symbol hunt output byte-for-byte repeatable? | The tool was run once in full. Repeat output is judged from the code only. A second full run is not done. Reviewer note. |
| 57 | Why are the `PS-X Run-time Library`, `Library Release`, `Revision`, `$Header` and compile-date strings absent? | Their absence is not explained. Not checked. |
| 58 | What do the three gap regions hold? | The gaps are at LBA 424, LBA 163342 to 163349, and LBA 228841 to 228990. They were scanned and had no symbol hits. Their contents are not described. |

## Ghidra, PS1 loader and REA (from T1.5)

| # | Question | Notes |
|---|----------|-------|
| 59 | Should REA be revisited? | REA cannot open the boot EXE. Its inspect command returns `unsupported binary format` for the Ghidra provider. REA does not list MIPS. The decision is in `docs/DECISIONS.md` (D4). Revisit if REA adds MIPS. |
| 60 | Should a community Ghidra MCP server be used instead? | Named candidates are ReVa and GhidraMCP. Neither was researched. Not decided. |
| 61 | Is REA safe to install? | REA is from one maintainer and was first published on 2026-07-12. Its prebuilt Windows native addon was not audited. Setup was not run. Not decided. |
| 62 | Does the Ghidra GUI open the EXE with the PS1 loader? | Not checked. The Ghidra GUI has not been opened by anyone. An earlier note saying it works was an automatic reply, not an observation, and is withdrawn. The PS1 loader was verified only with `analyzeHeadless` (reproducible). Optional user step: see `docs/SETUP.md` (T1.5, "Optional GUI check"). |
| 63 | Is the `ghidra_psx_ldr` zip the upstream file? | Its SHA-256 is recorded in `docs/SETUP.md`. It was not compared with a published hash. |
| 64 | Should the Ghidra check be a script in `tools\`? | Addressed for T1.6: `tools\ghidra_sdk_names.py` runs Ghidra for the SDK names. Whether it also covers the T1.5 import checks is not checked. See `docs/SETUP.md` (T1.6). |
| 65 | Should the RAM block be marked initialised? | The loader leaves `0x800D8000` to `0x801FFFFF` uninitialised. This causes about 460 "Unable to read bytes" warnings. Not decided. |
| 66 | What causes the pcode error after `trap(1)`? | The error is at `0x80090F1C`, file offset `0x8171C`. The word there is not a GTE instruction. The reviewer judged it harmless. The cause is not checked. |
| 67 | Which Ghidra scratch projects should be kept? | `work\ghidra-test` and `work\ghidra-test2` are scratch. Delete or keep. Not decided. |

## SDK function names (from T1.6)

| # | Question | Notes |
|---|----------|-------|
| 68 | Which PsyQ release matches the RCS dates? | The RCS dates on the disc fall between Dec 1996 and Mar 1997. They are not mapped to a PsyQ release. No release list is available. See `docs/SYMBOLS.md`. |
| 69 | Are the small-function SDK names false positives? | `SsUtReverbOn`, `SsUtReverbOff` and `_SsSndPlay` sit below the SDK block and are probably false positives. The JSON does not flag them. 157 SDK names are 32 bytes or less, and look-alike wrappers may be swapped. Key on the address, not the name. |
| 70 | Should `tools\ghidra_sdk_names.py` and `tools\psyq_version_scan.py` be fixed? | `psyq_version_scan.py` ignores `GHIDRA_HOME`, has no existence checks, and does not close its file handles. Both scripts hard-code default paths for this machine. Both can be overridden. Not changed by T1.6. |
| 71 | What are the 335 `obj_label` placeholders? | Names such as `TAP_OBJ_C8` and `LIBMCRD_OBJ_xx` are not real SDK names. They are not resolved. |
| 72 | Which string hints should be applied as names? | The string hints in `docs/SYMBOLS.md` (for example `SPU:T/O [%s]` and `MDEC_rest:bad option`) are not applied as names. Not decided. The `__main` comment from Ghidra is also unreliable. |

## Phase 2 carry-over (from the T1.7 gate)

| # | Question | Notes |
|---|----------|-------|
| 73 | Should `tools\disc_classify.py` report rejected TIM candidates? | The script tags no file as TIM. It does not list the byte patterns it rejected, so a reader cannot check the TIM result. Not changed at the T1.7 gate. |
| 74 | Is there a script for the T1.5 Ghidra import checks? | The checks (CODE block, BSS range, heap arguments, entry point) are a manual `analyzeHeadless` command. See `docs/SETUP.md` (T1.5). No `tools\` script runs them. |
| 75 | Should these files be committed? | `seeds\ghidra_funcs.txt` (1175 JAL targets from the boot EXE, address list only, no bytes), `catalog_identity.json`, `game.toml`, and `.recomp.json` (disc digests). Not decided. |
| 76 | Should the docs and tools stop hard-coding `%USERPROFILE%\...` paths? | Committed docs and tools use this machine's absolute paths. Not changed at the T1.7 gate. |
| 77 | Should the stale comment at `tools\disc_classify.py` line 51 be fixed? | Same issue as question 39. Not changed at the T1.7 gate. |