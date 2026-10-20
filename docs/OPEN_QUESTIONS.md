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
| 20 | Do the relative paths in `game.toml` work? | The disc path and the `work\disc` paths were set by hand. Partly answered at T2.3: the first Generate run used them and exited 0. See `docs/SETUP.md` (T2.3). |
| 21 | Should `PSX_SETUP_WIZARD` be ON? | It is ON by default in the configure step. Not checked what it does. |
| 22 | Is the scaffold's default psxrecomp URL the same project? | The script default is `mstan/psxrecomp`. We use `RetroPortingToolKit/psxrecomp`. Not checked whether they are the same project. |
| 23 | How should release CI work without committed `generated\`? | Upstream commits `generated\` for its release CI. `CLAUDE.md` forbids committing generated C, so the release CI templates will not work as-is. Not decided. |
| 24 | Should the upstream scaffold bug be reported? | An empty `-Description`, `-Publisher` or `-Year` breaks `probe_disc.py`. Not reported. |
| 25 | Should `seeds\ghidra_funcs.txt` be renamed? | The file name says Ghidra, but the addresses come from the boot EXE's JAL targets. Not decided. |
| 26 | Should the scaffold's Python workaround be kept? | Resolved in T2.1 by D5 (`docs/DECISIONS.md`). The unmodified retro-tools Python is used first. The private copy is only a fallback. |

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
| 35 | What load address does each overlay candidate use in RAM? | Static answer in `docs/EXE_OVERLAYS.md` (T1.4): all eight load at `0x80130FF8`. TEMPLE is confirmed at runtime (T2.13, question 44). The other seven are not yet seen at runtime (question 178). |
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
| 44 | Do the EXE header, the crt0 values and the overlay load addresses match a debugger or Ghidra? | Partly answered in T1.5. Ghidra headless matches the entry point, text address and size, BSS range and heap start and size. Not yet checked in Ghidra: the overlay load addresses, GP, initial SP and the header's d, b and s fields. No emulator check of the header values is recorded. T2.13 confirmed at runtime, by agent observation, that TEMPLE (id 140) loads at `0x80130FF8` and that the pointer word `0x80015134` holds `0x80130FF8` (`docs/EXE_OVERLAYS.md`, "Runtime proof (T2.13)"). The other seven overlays are pending (question 178). See `docs/SETUP.md` (T1.5). |
| 45 | Where does the scratch read buffer come from, and does the memcpy into `0x80130FF8` overlap it? | The scratch allocator is at `0x800865C0`. crt0 starts the BIOS heap at `0x80130FFC`, inside the overlay window. T2.13 (agent observation, TEMPLE only): the buffer `0x8013100C` is 20 bytes above the destination, so the ranges overlap by 19,080 bytes. The destination is below the source, and the copy is a forward byte loop. So it is overlap-safe, like a memmove, under OpenBIOS as run by PSXRecomp. The copy overwrites 16 bytes, `0x80130FFC` to `0x8013100B`, which were BIOS heap words. Whether anything uses them later is question 180. The retail BIOS memcpy was not examined (question 179). The return value of the malloc(4) call at `0x8008652C` is unknown. |
| 46 | Which level is the second FIRE site at `0x8002E130`? | The function at `0x8002E130` also reads id 137 (`/OVERLAYS/FIRE.OVR`). T2.12 shows it is a second function that loads FIRE. It is selected by dispatcher index 7, and by index 10 when `[0x800D7E48] >= 0`. Which level or mode it serves is not known. Its constant id set was not checked by the reviewer (question 133). Still static-only. It was not reached in the T2.13 run (question 178). |
| 47 | What do `/OVERLAYS/BRDGDEMO.BIN` and `/OVERLAYS/WINDDEMO.BIN` hold? | They are 2048-byte files. The BRIDGE and WIND level functions read them. They are not copied to the window. Their contents were not analysed. |
| 48 | What do the leading address tables in BRIDGE, FIRE, WATER and WIND mean? | The tables hold 32, 27, 83 and 102 words. The words point at data inside the file, not at function starts. Their use is not known. |
| 49 | What is the part of the text range from `0x800D7B40` to `0x800D8000`? | The crt0 BSS start (`0x800D7B40`) lies inside the file-backed text range. All file bytes in that part are 0. Their meaning is not established. |
| 50 | Do any other functions load overlays? | Three `read_file` calls use a variable id: `0x80085CF8` and `0x80085D74` (in `0x80085AF8`), and `0x8008635C` (in the wrapper `0x80086324`). T2.12 corrects the earlier count of two. The reachable ids from these sites are outside 134 to 143, but the callback table at `0x80082DF4` calls the wrapper with unknown ids (question 132). The id tables behind these results were not checked by the reviewer (question 131). |
| 51 | Do FORTRESS and PRISON load at `0x80130FF8` for sure? | T2.12 gives two static checks for each. The EXE call sites land on function starts, and the containment check holds. Both give `0x80130FF8` as the one base. This is a strong consistency check, not proof. T2.13 confirmed the base for TEMPLE only. FORTRESS and PRISON are still static-only, and their runtime check is pending (T2.17, question 178). The earlier statement that FORTRESS had no jal targets in the window was wrong. |
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
| 75 | Should these files be committed? | `seeds\ghidra_funcs.txt` (1175 JAL targets from the boot EXE, address list only, no bytes), `catalog_identity.json`, `game.toml`, and `.recomp.json` (disc digests). Resolved at T2.21: the user answered yes. See `docs/DECISIONS.md` (D8). |
| 76 | Should the docs and tools stop hard-coding `%USERPROFILE%\...` paths? | Committed docs and tools use this machine's absolute paths. Not changed at the T1.7 gate. |
| 77 | Should the stale comment at `tools\disc_classify.py` line 51 be fixed? | Same issue as question 39. Not changed at the T1.7 gate. |

## Upstream CLI wrapper (from T2.1)

| # | Question | Notes |
|---|----------|-------|
| 78 | Should the wrapper check that the retro-tools folder exists? | `tools\run_psxrecomp.ps1` does not check `RETRO_TOOLS_DIR` up front. A bad value can silently reuse a stale `work\py-psxrecomp`. Reviewer note. |
| 79 | Does the private Python copy go stale if the repo moves? | The `._pth` file in `work\py-psxrecomp` holds absolute repo paths, written once. If the repo moves, those paths are stale. Reviewer note. |
| 80 | Is the unmodified Python enough for the `generate` subcommand? | Partly answered at T2.3: `generate` exited 0 through the wrapper. The report does not say which Python ran, so the private fallback is not ruled out. Check the wrapper's printed line in `work\generate_run1.txt`. At T2.16 the unmodified embeddable Python failed in the static step, and the private copy passed. See `docs/DECISIONS.md` (D13). |

## Seeds and static coverage (from T2.2)

| # | Question | Notes |
|---|----------|-------|
| 81 | Are the 108 seeds that are not Ghidra function starts real functions? | They are analyzer function starts. Most are low or medium class. Addresses are in `work\seed_report.json` under `seed_classification.anomalies`. Partly answered at T2.8: the two added seeds, `0x8003A674` (vet ACCEPT) and `0x80032760` (manual, question 213), are among the 108. The other 106 still need review. See `docs/COVERAGE.md`. |
| 82 | Are the 325 Ghidra-only entries labels, not function boundaries? | All 325 carry PsyQ-style or OBJ label names. They are probably labels. Not confirmed. |
| 83 | What are the 2 Ghidra symbols that lie in no analyzer function? | `cb_data` at `0x8009761C` and `_spu_2pitch` at `0x800A8D18`. Possibly data. Not checked. |
| 84 | How many of the 1093 analyzer-only starts are real functions? | Most are orphans or low and medium prologue scans. The real count is unknown. |
| 85 | What are the 133 unresolved indirect transfers (129 `jalr`, 4 `jr`)? | T2.8 used runtime dispatch misses as its worklist (`docs/SETUP.md`). The static count of 133 was not re-run. Not resolved. |
| 86 | What is the 25.4% of the image outside any code function? | Possibly data or overlay tables. Unverified. |
| 87 | Does the invalid-seed exit code of `tools\check_seeds.py` work? | The script has no `--seeds` option, so the seed path cannot be changed. The exit 1 path for invalid seeds is untested. |
| 88 | What does `tools\check_seeds.py --no-run` skip? | The usage line lists the flag. The effect is not described in the T2.2 report. Not checked. |
| 89 | Should `--all-funcs` stop re-saving the Ghidra project? | It re-saves the project under `work\ghidra-sdk\`. Not decided. |
| 90 | What do the 29 `lui` plus `addiu` or `ori` sites that point into the overlay window do? | They use 23 distinct constants. The reviewer found them by hand. Informational. Not checked. |

## First Generate (from T2.3)

| # | Question | Notes |
|---|----------|-------|
| 91 | Does the generator have a flag that prints a strict or skip summary? | The log prints no strict banner and no skip count. `config_loader.h` line 942 says strict is "currently always true". `game.toml` sets `strict = true`. "No skipped-function failures" was judged from the absence of skip lines. Not checked whether an upstream flag exists. See `docs/SETUP.md` (T2.3). |
| 92 | Are the 562 out-of-function warnings and 5201 TODO opcode markers data read as code? | They sit at the EXE tail, mostly `0x800BA3F4` to `0x800D7A84`. The reviewer says the bytes at `0x800D5B08`, `0x800D7290` and `0x800D7824` are data tables. The emitter decodes them as code. They are probably unreachable. Not verified. Not decided whether to exclude them through config. |
| 93 | Are the warning clusters in the overlay window or in BSS? | Clusters include `0x800D5B08` to `0x800D5E54`, `0x800D6610` to `0x800D6638`, `0x800D7290` and `0x800D7824`. The BSS start `0x800D7B40` lies inside the file-backed text range (question 49). Not checked whether any cluster lies in the overlay window or BSS. |
| 94 | Is `0x800D6610` code or data? | The reviewer judged it ambiguous. Not checked. |
| 95 | What are the 141 reserved-opcode warnings? | The tool hides them. They may be the same data-as-code bytes as question 92. Set `PSXRECOMP_VERBOSE_RI_WARNINGS=1` to list them. Not checked. |
| 96 | Was run 2 of the determinism test checked? | The reviewer compared the SHA-256 lists of run 1 and run 3. The run 2 list was not compared. See `docs/SETUP.md` (T2.3). |
| 97 | Should OpenBIOS be regenerated by `generate`? | `generate` reused the OpenBIOS backends and did not regenerate them. Not decided whether a later step needs a fresh OpenBIOS build. |

## Game executable build (from T2.4)

| # | Question | Notes |
|---|----------|-------|
| 98 | When does the manifest workaround go? | The build has two manifests on one target: psxrecomp's and recomp-ui's. Both are at `psxrecomp` 449c31e5 and `recomp-ui` 7c635c6. The root `CMakeLists.txt` drops recomp-ui's manifest (D6, `docs/DECISIONS.md`). Upstream fix suggested: the guard should also match `$<TARGET_OBJECTS:..._manifest>`, or check for a `*_manifest` target. Keep the workaround until upstream fixes this. Then remove it. The workaround depends on recomp-ui's generated file name. |
| 99 | Should an overlay toolchain be staged for the tcc tier (T2.8 and T2.16)? | The startup log says `tcc tier active but no bundled toolchain at build\overlay_toolchain`. Overlay gaps fall back to the interpreter. Not decided. See `docs/SETUP.md` (T2.4). T2.16 adds the static route through `GAME_OVERLAY_STATIC_C`. The T2.16 report does not say whether the tcc startup line still appears, and does not mention staging a toolchain. |
| 100 | Is a retail BIOS backend needed? | The SCPH1001 backend was skipped at configure. Only OpenBIOS is linked. A retail BIOS backend would be needed only if T2.7 requires it. Not decided. |
| 101 | Why is the `psxrecomp` submodule shown as modified after T2.4? | The `psxrecomp` submodule shows ` m`. The cause is CRLF noise from the T0.5 regen. It is not from T2.4. It is the same issue as question 13. Do not commit inside the submodule. |
| 102 | Is the embedded manifest valid XML? | The exe has one embedded manifest (`<assembly` appears once). It was not checked with an XML validator. |

## Headless smoke test (from T2.5)

| # | Question | Notes |
|---|----------|-------|
| 103 | Should `PSX_DEBUG_TOOLS` also be ON in `build\`? | The shipping exe has the debug server off. The smoke test uses `work\build-dbg` instead (D7, `docs/DECISIONS.md`). Turning it on in `build\` is the alternative. Not decided. |
| 104 | Do the `opengl` and `vulkan` renderers pass the smoke test? | Not tested. The Vulkan renderer is a software stub (question 14). |
| 105 | Do `--hidden-window` and `--headless-opengl` work with the harness? | Not tested. `--headless-opengl` needs real OpenGL. |
| 106 | Does a real Ctrl-C stop the harness cleanly? | Only `KeyboardInterrupt` handling is in the code. Not tested with a real Ctrl-C. |
| 107 | Does audio work in the test runs? | Headless mode has no audio. Not tested. |
| 108 | Does the game run at the same speed as hardware? | The 60 s run measured about 70 frames per second. Not compared with hardware. |
| 109 | Do the screenshots show what the agent reports describe? | The descriptions come from agent reports and were not checked by a user. The reviewer saw a black frame at the 20 s mark in one run. The user check is at the T2.6 gate. |
| 110 | Why are the checked screenshots the same size, 230723 bytes? | Judged harmless. Not checked. |
| 111 | Is `psx_crash.txt` written where the harness watches? | The location is inferred from upstream code. No crash was seen, so the watch was never tested with a real file. |
| 112 | Does the 60 s run have 3 or 4 screenshots? | The T2.5 report says 3 for the 60 s run. The harness names 4 files (`t00`, `t10`, `t30`, `end`). Not checked. |
| 113 | What exit code does a PASS run give? | The T2.5 report does not record it. |
| 114 | What are the defaults of `--seconds`, `--renderer` and `--startup-wait`? | The usage line lists the options. The defaults are not recorded in the T2.5 report. |

## Visual first boot (from T2.6)

The T2.6 result is user-reported. No agent checked it. See `docs/SETUP.md` (T2.6).

| # | Question | Notes |
|---|----------|-------|
| 115 | Where does the Sony logo come from, and why was it not seen? | The user did not see the Sony logo, but saw the Midway logo. Hypothesis, not verified: the Sony boot logo comes from the retail BIOS, and OpenBIOS has no such logo. To check: (a) whether the game itself holds any Sony logo; (b) whether a DuckStation run with its retail BIOS shows the Sony logo. The user did not say what DuckStation showed. |
| 116 | What causes the glitchy FMV audio? | Partly answered by measurement (hidden window, agent, not user). The FMV runs at about 50 Hz with vsync on. The audio underruns follow from that rate (`docs/SETUP.md`, "FMV speed measurement (Release, hidden window)"). This is supported, not proven for the visible window. The user's visible-window vsync-off run is pending (question 155, and D9 in `docs/DECISIONS.md`). The user's first digital glitch was not heard in these runs. |
| 117 | Is the FMV video frame rate correct? | Partly answered by measurement (hidden window, agent). Guest rate in the FMV phase: about 50 Hz with vsync on, and 60.0 Hz with `PSX_VSYNC=0`. The movie file is not identified, so the rate of each movie is not known. Whether 50 Hz is wrong for these movies is still not checked. See questions 150 and 153. |
| 118 | Does DuckStation play the same movie with clean audio and the right frame rate? | Still open. Not done. |
| 119 | Does the audio glitch change with other renderers? | Partly answered for speed. Hidden-window run C (`--renderer software`) gives about 50.3 Hz in the FMV phase, the same as the OpenGL runs. The audio was not judged. The headless build cannot test audio (question 107). |
| 120 | What do the audio buffer settings in `game.toml` and `game_options.toml` do, and what are they set to? | Partly answered. `[audio] buffer_ms` is read in `psxrecomp\recompiler\src\config_loader.cpp` (lines 1022 to 1035). It must be 30 to 500 ms. The default is 180 ms (`psxrecomp\recompiler\src\config_loader.h` line 788). `build\game.toml` has no `[audio]` block, so 180 ms is used. The same block has `spu_hq`, whose effect is not checked. Other values are not tested. `game_options.toml` is not checked. See question 156. |
| 121 | Is the game locked to 60 Hz or 50 Hz? | Answered by measurement (hidden window, agent). Outside the movies the guest holds about 60 Hz. In the FMV phase it averages about 50 Hz with vsync on. With `PSX_VSYNC=0` it holds 60.0 Hz in the FMV phase, so it is not fixed at 50 Hz. The visible-window check is pending. See `docs/SETUP.md`. |
| 122 | Does CPU load or frame pacing cause the audio glitch? | Partly answered by measurement (agent). Frame pacing with vsync on is the likely cause of the 50 Hz rate. A frame in the FMV costs about 13 ms against a 16.66 ms budget, and some frames miss a vblank. The audio underruns follow from the rate. CPU load was not measured as a separate cause. Not proven for the visible window. See `docs/SETUP.md`. |
| 123 | Is this audio problem a known PSXRecomp issue? | Partly checked. `psxrecomp\docs\ENHANCEMENTS.md` reports "sluggish FMV" for Tomba 2. `psxrecomp\docs\ROLLBACK_MOTK_HOOKUP.md` reports FMV at about 43 to 55 fps with a host CPU ceiling. Neither is this game. The XA-specific search has not been run. |
| 124 | Which key quits the game? | Still open. The user asked whether to close the game window, and was told yes. No quit key was reported. See `docs/CONTROLS.md`. |
| 125 | Which keys control the game, and what is the framework's default key map? | Partly answered. The default map is in `psxrecomp\runtime\src\psx_keybinds.c` (lines 43 to 66) and `psxrecomp\runtime\src\host_keymap.c` (lines 90 to 120). The user reported A, S, Z, X, Enter, Right Shift, Tab and F. Arrow keys and Q, W, E, R, T, Y are the default but were not reported. See `docs/CONTROLS.md`. |
| 126 | Was the main menu reached? | Answered yes by the user (playtest 2). The user reached the main menu, started a new game, and played a fight. See `docs/SETUP.md` ("Playtest 2"). |
| 127 | Did the window run windowed or fullscreen? | Answered by the user: windowed, with the same command as T2.6. |

## LBA-to-file lookup (from T2.9)

| # | Question | Notes |
|---|----------|-------|
| 128 | Should `tools\lba_lookup.py --bcd` reject single-digit fields? | `--bcd` accepts single-digit fields. So `0x3:0x4:0x5` reads as `03:04:05`. This is looser than documented. Reviewer note. See `docs/SETUP.md` (T2.9). |
| 129 | Does `tools\lba_lookup.py` report a missing `work\disc_files.json` correctly? | Checked by code reading only. The run did not test it. The tool has no option or environment variable to point at another file. Reviewer note. |

## Static overlay facts (from T2.12)

See `docs/EXE_OVERLAYS.md` ("Static overlay facts (T2.12)") and `docs/SETUP.md` (T2.12). Items 130 to 139 are open.

| # | Question | Notes |
|---|----------|-------|
| 130 | Why does the T2.12 joint check give more than one base for BRIDGE, FIRE, WATER and WIND? | `work\overlay_facts.json` gives "not one base" for these four. The reason is not in the T2.12 report. Their status rests on the T1.4 checks. |
| 131 | Are the id tables behind the variable-id read sites correct? | The reachable ids at `0x80085CF8` and `0x80085D74`, the four id-table functions behind the wrapper at `0x80086324` (tables at `0x800AF5E4` and `0x800B1D34`), and the constant 59 used when `i < 0` come from tool output. The reviewer did not check them. |
| 132 | Which ids do the indirect calls through the callback table at `0x80082DF4` use? | The wrapper address is stored in a callback table built in `0x80082D78` and passed to `0x800A3F8C`. The ids used through it are not known. |
| 133 | Do the constant id sets of the two FIRE functions match? | Tool output: `0x8002E130` reads {58, 60, 61, 62, 63, 137, 144}. `0x8002DA94` reads {54, 55, 56, 58, 60, 61, 62, 63, 137, 144}. Not checked by the reviewer. |
| 134 | What do the generic callers `0x80061690` and `0x80061960` do with window code? | The T2.12 report says both reach `0x801310C0`, code in the window, from outside the level functions. What they load, and when, is not known. |
| 135 | What is the record table at `0x800AC440` (stride 28), and what sets index `i` at `0x800D7E48`? | The ids of the variable-id site come from this table. The writes to `i` are at `0x8002A6DC` (-1) and `0x8002AB70` (clamp to 0 to 24). What the 25 records hold is not known. |
| 136 | Which index does TEMPLE store, and what do index 6, index 11 and the functions `0x8002AC74` and `0x8002B594` do? | The store at `0x8002B740` is unresolved (block boundary). Index 6 loads -1. The tool finds no overlay load in `0x8002AC74` or `0x8002B594`. Their roles are not checked. |
| 137 | Can DMA, the BIOS, or a computed pointer write `0x80015134` or the window? | The EXE text has no store to the destination pointer. A static scan cannot exclude a write through a computed pointer, DMA or the BIOS. T2.13 checked the TEMPLE copy only: the undo of the write ring found no untraced writer. This is evidence for one copy, not for the whole run. |
| 138 | Does any pointer outside the image (BSS or heap) point into the window? | The containment check for FORTRESS and PRISON would widen if one did. The check cannot exclude this. |
| 139 | Does anything read the last 2 bytes of `/OVERLAYS/FORTRESS.OVR`? | The size is 19,874, not a multiple of 4. The tool's word scan drops the last 2 bytes. The loader's memcpy length is get_size(id). Whether the code reads those bytes is not checked. |

## Symbols.toml seeding (from T2.21)

See `docs/SETUP.md` ("Seeding symbols.toml (T2.21)") and `docs/DECISIONS.md` (D8).

| # | Question | Notes |
|---|----------|-------|
| 140 | Should `tools\seed_symbols.py` give a clear message when `--sdk-json` names a missing file? | A missing file gives a raw traceback. Reviewer note. |
| 141 | Should the risky-name list be complete? | The list of names that get the `sdk_` prefix is hand-picked from libc, POSIX and runtime names. It is not exhaustive. Reviewer note. |
| 142 | Is the `confirmed` status for VSync right? | The note in `docs/SYMBOLS.md` shows evidence that `v_wait` refers to `VSync: timeout`. That supports the containing function, not the bare name `VSync` at `0x800945E4`. Not decided whether the status stays. Reviewer note. |
| 143 | Should the loader-named `main` at `0x80020474` get a name? | T2.21 leaves it unnamed. Not decided. |
| 144 | Do DrawSync, StartPAD, DecDCTReset and InitPAD have recorded evidence? | They stay `guessed` until their evidence is recorded in `docs/SYMBOLS.md`. The reviewer spot-checked them. |
| 145 | Do `callback` (`0x80097268`) and `timeout` (`0x8009928C`) need the `sdk_` prefix? | They match a broad libc list but are not in the risky list. Harmless unless a `func_XXXXXXXX` alias is used for them. Reviewer note. |
| 146 | Which entries make up the status counts? | The recorded counts are 8 `confirmed` and 431 `guessed`. They add to 439. The seeded count is 438, and BootEntry is hand-owned. Whether BootEntry is in the 431, or one count is off, is not checked. |
| 147 | What does `tools\seed_symbols.py --dry-run` change? | The option is listed in the usage. Its effect is not recorded in the T2.21 report. Not checked. |

## Playtest 2 (from T2.10/T2.11 partial)

See `docs/SETUP.md` ("Playtest 2: FMV and gameplay") and `docs/CONTROLS.md`. All items are user-reported. None is agent-verified.

| # | Question | Notes |
|---|----------|-------|
| 148 | Which movies play, and do all of them stutter? | The user says all movies run at about 50 fps. Only the Midway logo movie and the intro are named. The other movies and their audio are not described. |
| 149 | Which level was the fight in, and which overlay loaded it? | The user played a real fight and died. Controls responded. No crash was reported. The level or location was not stated, and the overlay id was not observed. Needs a debug-server `pc_break` observation, or an overlay log from `PSX_RUNTIME_PERF_DIAG`. This is the open part of T2.11. At T2.16 an agent observed the first fight after a fresh New Game follow the TEMPLE load (id 140, `0x80130FF8`). This is agent evidence from a screenshot and the overlay log, not a user observation. See `docs/EXE_OVERLAYS.md` ("Static overlay build (T2.16)"). |
| 150 | What is the real frame rate of each movie? | The 48 to 54 fps figures are the user's estimates. Not measured by the user. Partly answered by measurement (hidden window, agent): guest Hz in the FMV phase is about 50 Hz with vsync on and 60.0 Hz with `PSX_VSYNC=0`. Only one movie was measured, and its file is not identified. See `docs/SETUP.md`. |
| 151 | What are the monitor refresh rate, CPU model, power plan and system load? | Partly answered by measurement (agent). Recorded: panel 1920 by 1080 at 60 Hz, Intel i5-7300HQ, AC power, Windows "Balanced" plan, Intel HD 630 (old driver) and NVIDIA MX150. The window mode is windowed (question 127). Not recorded: the system load during the user's run. See `docs/SETUP.md`. |
| 152 | Is the first digital glitch at the Midway logo a cold-start effect? | Partly answered by measurement (agent). The cold run A and the warm run B give the same FMV-phase rate, about 50 Hz. The dip at the Midway logo appears in both cold and warm vsync-on runs. The audio glitch itself was not heard in these runs. Hypothesis 2 in `work\audio_investigation.md`. |
| 153 | What does `PSX_RUNTIME_PERF_DIAG=1` show for the movies? | Answered by measurement (hidden window, agent). The diagnostic prints guest Hz, underruns, audio fill, work and pacer time, and overlay native and interpreter counts. In the FMV phase the native overlay count is 0. The interpreted count is about 1100 dispatches a second. See `docs/SETUP.md` ("FMV speed measurement (Release, hidden window)"). |
| 154 | Does `--renderer software` change the movie speed or the stutter? | Partly answered for speed. Hidden-window run C gives about 50.3 Hz in the FMV phase, the same as OpenGL. The stutter was not judged. See also question 119. |
| 155 | Does `PSX_VSYNC=0` change the movie speed or the stutter? | Answered for speed in the hidden window (agent). With `PSX_VSYNC=0` the FMV phase runs at 60.0 Hz median (range 58.8 to 61.0), with 0 underruns. The visible-window test is still to do. The stutter as heard was not judged. See D9 in `docs/DECISIONS.md`. |
| 156 | Does `[audio] buffer_ms = 300` change the stutter? | Not run. 300 is inside the checked range (30 to 500). See question 120. |
| 157 | Is the real XA path the cause, or only the host audio path? | The investigation judges the real XA path unlikely. The decode in `psxrecomp\runtime\src\cdrom.c` (lines 1395 to 1430) reads stereo, 37800 Hz, 4-bit sectors. A code comment at lines 2628 to 2640 says a stream freeze that starved XA was removed on 2026-07-10. Read from code, not run. OpenBIOS: no evidence. Measurement (hidden window, agent, `docs/SETUP.md`): the underruns follow the guest rate. SPU and XA are produced on guest time, and 37 kHz audio goes to a 44.1 kHz device. Not proven as the cause. Legacy audio (run E) gave about 25 underruns a second. |
| 158 | Does interpreting overlay code slow the movies? | Answered in part (hidden window, agent). In the FMV phase the native overlay count is 0 and the interpreted count is about 1100 dispatches a second, about 9k instructions a second. So overlay interpretation is not the FMV cause. Staging the overlay toolchain (question 99) would not fix the FMV rate. The time spent in the interpreter was not separately timed. |
| 159 | Where does the FMV decode run, in the EXE or in an overlay? | Answered by overlay counters (hidden window, agent): the FMV decode runs in the exe's AOT code, not in interpreted overlays. Not yet confirmed by the debug build's `fmv_state`, which was not run. The movie file is not identified (question 162). The names are in `psxrecomp\docs\TCP_COMMANDS.md`. |
| 160 | Does the host audio device or format cause the stutter? | Partly. The host is Realtek HD Audio. Its default sample rate was not captured, so the rate mismatch (37 kHz audio to a 44.1 kHz device, as in `docs/SETUP.md`) is not checked. Not run as a separate test. |
| 161 | Would a PGO or LTO build help the movies? | The investigation says the PGO profile is empty. The measured headroom with vsync on is about 22 percent. Not built or tested. Not decided. |
| 162 | Which movie file plays in the FMV phase? | Not identified. The Release build prints no LBAs. The earlier guess of 7100 sectors and `FMV3B.STR` is withdrawn. Needs a debug build run of `fmv_state` or `cdrom_sector_history`. See `docs/SETUP.md` ("FMV speed measurement"). |
| 163 | Does the visible-window run with `PSX_VSYNC=0` show 60 Hz, and is there tearing? | Not run. This is the gate for D9 in `docs/DECISIONS.md`. The user reports fps, audio and tearing. |
| 164 | Do the hidden-window results match a visible window with vsync on? | Not separable. Hidden-window runs also change the swap. The user's visible run (48 to 54 fps) is similar in size. |
| 165 | Why does `PSX_LOAD_DELAY=0` make the FMV slower (about 40 Hz)? | Run F gave about 40.0 Hz with about 14,700 underruns a second. This is the opposite of the upstream claim. Cause not known. Do not use the setting. |
| 166 | What causes the run G dip to 23.6 Hz at about sample 209? | Outside the FMV. Run G (260 s) gave 25,317 underruns in that sample. Not explained. |
| 167 | What causes the Midway logo dip? | The guest runs at about 50 to 54 Hz at samples 4 and 5 in every vsync-on run. Run B once fell to 18.7 Hz. The dip lines up with overlay captures and GL uploads, and is absent with `PSX_VSYNC=0`. Not explained. |
| 168 | Do `PSX_VSYNC=-1` (adaptive) and `PSX_VSYNC=2` (VRR) change the FMV rate? | Not run. Their code paths are in `psxrecomp\runtime\src\main.cpp` (near line 18612). |
| 169 | Do `PSX_PRESENT_THREAD=1` or `PSX_RENDER_THREAD=1` change the FMV rate? | Not tested. |
| 170 | Where does the launcher keep the player's `settings.toml`? | The file overrides `game.toml` for the vsync setting. Its location is not verified. See `docs/SETUP.md`. |

## Boot-to-menu replay route (from T2.18)

See `docs/SETUP.md` ("Boot-to-menu replay route (T2.18)") and `docs/DECISIONS.md` (D8).

| # | Question | Notes |
|---|----------|-------|
| 171 | Should the final line of `tools\run_boot_route.py` say how many RAM and VRAM checks ran? | With `--runs 1`, a MATCH says "MATCH" but compares RAM and VRAM only where they are exact. The reviewer run skipped the hash at frame 1800, with a warning. The final line should print `RAM/VRAM compared at k/7`. Not done. |
| 172 | Can the pause land on the exact frame? | `host_pause` lands one frame early or late (+-1). Commands are served once per vblank. Upstream removed `pause`, `run_to_frame` and `step`. A framework-level "pause at frame N" would make the RAM and VRAM hashes exact at every checkpoint. Not decided. |
| 173 | When should the expected digests be re-recorded? | The expected digests are tied to one exe build (its SHA-256 is in `tests\replays\expected\boot_to_menu.json`). The script only warns when the exe differs. The policy for re-recording after a rebuild is not decided. At T2.16 the replay gave MATCH (7 checkpoints) on the new exe, with the exe SHA-256 warning only. The recorded `exe_sha256` is now stale, and it was not re-recorded. At T2.8 the replay gave MATCH (7 checkpoints) again, with the same warnings. Still not re-recorded. |
| 174 | What caused the one earlier mid-run process death? | One earlier run died partway through. The cause is unknown. It did not come back in 8 runs. It may have been an external `taskkill`. Not checked. |
| 175 | Does attract mode start at about frame 6500 on every run? | Seen once, in an agent screenshot. Not checked on other runs. |
| 176 | Which exit code does a setup error give? | The docstring and README of `tools\run_boot_route.py` say exit 2. A `SystemExit` with a string exits 1. Either the docs or the code must change. Not changed. |
| 177 | How strong is the evidence that the `mmio` and `mc` columns respond to input? | The evidence is one negative control: START at frame 3001 instead of 3000. It changed `mmio` and `wc` and `ws` at later checkpoints. One control is thin evidence. |

## Runtime proof (from T2.13)

See `docs/EXE_OVERLAYS.md` ("Runtime proof (T2.13)"), `docs/SETUP.md` ("Runtime overlay proof (T2.13)") and `docs/DECISIONS.md` (D10). The TEMPLE result is agent-observed, not user-observed.

| # | Question | Notes |
|---|----------|-------|
| 178 | What do the other eight level functions load at runtime? | Only TEMPLE (`0x8002B688`, id 140) fired in the committed route up to frame 9000. EARTH, WIND, WATER, PRISON, FIRE (both functions `0x8002DA94` and `0x8002E130`), BRIDGE and FORTRESS are not seen at runtime. The check is T2.17. At T2.16 the static probe reached TEMPLE's fight, and no other id was reported as seen. The tool is hard-coded to TEMPLE-style checks (question 183). |
| 179 | Does the retail BIOS memcpy copy the TEMPLE overlay the same way? | The overlap check (question 45) used OpenBIOS, as run by PSXRecomp. The retail BIOS memcpy was not examined. Its behaviour for an overlapping copy is not known. |
| 180 | Does the game read the 16 bytes that the TEMPLE copy overwrites? | The bytes are `0x80130FFC` to `0x8013100B`. They were BIOS heap words before the copy and overlay bytes after it. Whether any code reads them later is not checked. |
| 181 | What do the read_file ids 85 (`0x55`) and 144 (`0x90`) load, and do they copy into the window? | Earlier runs, not the committed tool, saw these reads at about frames 4002 and 4007. They used the same buffer `0x8013100C`. Id 140 (`0x8C`) was also seen. Id 144 is outside 134 to 143 and is in the constant id set of `0x8002DA94`. What these reads do is not known. |
| 182 | Why does the pause frame differ between runs (5210 or 5212)? | The first pause lands inside the copy. The tool resumes one frame and pauses again. That second pause frame differs by run. The cause is not known. The pause frame is not part of the check. Exact frame pause is question 172. |
| 183 | Should `tools\overlay_runtime_check.py` wait for any given overlay id? | The tool stops at the first overlay copy and checks TEMPLE-style loads only: a0 equals the window base, and a2 equals `get_size(id)`. Waiting for a given id is said to be a small change. Not made. |

## AOT overlay profile (from T2.15)

See `docs/SETUP.md` ("AOT overlay profile (T2.15)") and `docs/DECISIONS.md` (D12).

| # | Question | Notes |
|---|----------|-------|
| 184 | Does anything tie `load_addr` in the profile to the pointer word? | No. Changing `EARTH` `load_addr` to `0x80131000` still passes the extract step. `load_addr` is pinned only by the pointer-word check, the entries and the excluded ranges. Schema gap. |
| 185 | Can the pipeline check the loader tables directly? | No, for this game. The `bcd_extent_table` check reads 8-byte entries. The game has a 4-byte location table and a separate size table. The words checks replace it. Their agreement with the ISO extents is shown by `tools\overlay_facts.py`, not by the pipeline. |
| 186 | Can `adjacent_files` check the other `.OVR` files? | No. It needs non-last sizes to be multiples of 2048. The `.OVR` sizes are not. Only `BRDGDEMO` to `BRIDGE` is checked. |
| 187 | Are the 14 profile entries real function starts? | Not yet. The entries are verified `jal` targets. FIRE and WIND land on a `lui`, not a stack prologue. The T2.16 audit gives a guard for each of the 14 required entries. The audit does not state that each is a function start. Still open, see question 193 for the FIRE and WIND `lui` entries. |
| 188 | Does the `--cps` value in the profile match the runtime build? | Partly. The CLI detected `--cps` from `psx_cps_mark_game` in `generated\SLUS_004.76_dispatch.c`, and the audit reports `cps` true. The runtime-side match was not checked as a separate step. |
| 189 | Are the FIRE, WATER and WIND table lengths right? | The FIRE, WATER and WIND entries equal their table ends. This independently supports the lengths. Whether each entry is a real function start is question 187. Each table holds one zero word. |

## Static overlay build (from T2.16)

See `docs/EXE_OVERLAYS.md` ("Static overlay build (T2.16)"), `docs/SETUP.md` ("Static overlay build (T2.16)") and `docs/DECISIONS.md` (D13).

| # | Question | Notes |
|---|----------|-------|
| 190 | Where do the about 121,000 `segment_alias_interp` calls come from? | The counter covers non-KSEG0 aliases. The likely PCs are KUSEG `0x00130000` or KSEG1 `0xA013xxxx`. Not checked. If they are real overlay code, KUSEG and KSEG1 static shards are needed. The upstream note in `psxrecomp\docs\SEGMENT_AWARE_CODE.md` (about lines 1237 and 1262) says these drop to about 0 to 700 with those shards. Planned for T2.17. |
| 191 | What is the steady-state fallback per frame, and how many interpreted instructions run? | The counters are cumulative since cold boot. The reviewer's reading is about 10 to 15 calls a frame between frames 5001 and 6004. Instructions were not counted. Not confirmed. Planned for T2.17. |
| 192 | Why are there 48 static CRC misses? | Probably the first probe of addresses shared by several overlays (the base `0x80130FF8` is shared). Not confirmed. |
| 193 | Do the FIRE and WIND entries that land on `lui` run correctly? | The audit checks them. They were not run in the probe. Their behaviour is not known. |
| 194 | Is static coverage complete? | No. The audit says `full_static_coverage_proven` is false. Not proven. |
| 195 | Should `AOT_STATIC_AUDIT.json` be byte-reproducible? | Its `recipe_input_sha256` changes on each run that does not reuse. The shard hashes and `generation_inputs_sha256` are the compare keys. Whether upstream intends this is not checked. |
| 196 | Should the wrapper detect the subcommand after global options? | `tools\run_psxrecomp.ps1` reads only `$args[0]`. A global option placed before `generate` defeats the `generate` check, so option (a) runs first. Reviewer minor. Not changed. See D13 in `docs/DECISIONS.md`. |

## Overlay loader and level names (from T2.22)

See `docs/SYMBOLS.md` ("Overlay loader and level-function names (T2.22)") and `docs/SETUP.md` ("Hand-owned symbols and seeding rules (T2.22)").

| # | Question | Notes |
|---|----------|-------|
| 197 | Should `get_size`, `read_file` and `scratch_alloc` get a prefix? | The names have no prefix. Their `func_XXXXXXXX` aliases could clash with a future host file that includes `psx_symbols.h`. No clash today. Nothing includes the header yet. `psxrecomp\runtime\src\mod_packages.cpp` has its own `read_file` but does not include the header. Reviewer suggestion: prefix later. |
| 198 | Is `get_size` at `0x800861BC` right? | Only the value was checked. No entry was observed at runtime. |
| 199 | Do `scratch_alloc`, `load_arena_record` and `read_file_alloc` do what their names say? | The roles come from static reading. `scratch_alloc` was not traced in full. `load_arena_record` owns the variable-id read sites, but its ids are not in 134 to 143. Its only caller is inside `level_load_FIRE_alt`. |
| 200 | What does each `level_load_*` function do in play? | The names come from the file each loads, not from a gameplay role. Only `level_load_TEMPLE` is seen at runtime (question 178). |
| 201 | Is `0x8002B688` the real entry of `level_load_TEMPLE`? | The start comes from the dispatcher table in `docs/EXE_OVERLAYS.md`. The two return addresses seen at T2.13 lie inside the function. No entry was observed at `0x8002B688`. |
| 202 | Is the hand-edit of `sdk_memcpy` kept on every seed run? | `sdk_memcpy` lost its seed marker by hand, so the script keeps it. Only two runs of `tools\seed_symbols.py` were recorded, and both reported `unchanged`. The T2.22 report records no test of a hand-edited block. |

## Playtest diagnostics recorder (from T2.19)

See `docs\SETUP.md` ("Playtest diagnostics recorder (T2.19)") and `docs\DECISIONS.md` (D14).

| # | Question | Notes |
|---|----------|-------|
| 203 | What do fields 4 and 9 of each `inputs.csv` row hold? | They are the first field of each pad's stick block. They are 0 in the idle sample. Likely analog-mode flags. Not verified. |
| 204 | Is a session folder safe to share? | The folder holds copies of the starting memory cards and a trace of the inputs. The upstream doc says to zip the complete session folder, and that includes the cards. The repo gives no safe sharing step. Not decided. |
| 205 | When is the `%TEMP%` fallback folder used? | `docs\SETUP.md` gives the fallback path. The condition is not recorded. Not checked. |
| 206 | What is lost if the game crashes or is killed, instead of quitting normally? | The writer drains its data on a normal quit. What is lost on a crash or a kill is not checked. |
| 207 | What does a `PSX_PUBLIC_RELEASE=ON` build ship with? | The defaults script fails a public build unless the source says false, and the source says false. A configure with the option ON was not run. The public output is not checked. |
| 208 | Does the Release exe replay its own recording? | Strict replay is T2.20. Not run. The same-exe rule comes from the build id. Not tested. |
| 209 | Does the CMake no-op rebuild check pass after the diagnostics package was added? | The reviewer did not run it. Not checked. |
| 210 | What does the sample number `N` in the first field of each row count? | The field holds `N` and a sequence number. The report does not say what `N` counts. Not checked. |
| 211 | Are the fields of `session.json`, `telemetry.csv` and `mods-state.toml` documented? | The T2.19 report does not describe them. Not checked. |
| 212 | Does the on-screen input display show the right buttons? | The `osd` feature was staged on, but the display was not checked on screen. Not checked. |

## Seed growth (from T2.8)

See `docs/SETUP.md` ("Seed growth from dispatch misses (T2.8)") and `docs/DECISIONS.md` (D15).

| # | Question | Notes |
|---|----------|-------|
| 213 | Has anyone reviewed the manual seed `0x80032760` and the `--manual` option? | The main part of T2.8 passed review. The manual follow-up (batch T2.8-2, the option and the rebuild) was checked by the implementer only. The seed comment says two independent disassemblies confirmed it. No reviewer has checked this. |
| 214 | Does `tools\vet_seeds.py` miss function heads that sit more than 4 instructions before the prologue? | Its 4-instruction window gave WARN for `0x80032760`, which has seven instructions before its prologue. `0x8003A674`, with three, was accepted. Not checked whether other heads are missed, or whether the window should be wider. |
| 215 | How many dispatch misses appear with other levels, characters, menus and FMVs? | The coverage is one TEMPLE fight with mashed buttons. Other levels, characters, menus and FMVs were not run. The seed count may grow with user play. |
| 216 | Why did `psxrecomp-analyze.exe` go missing, and why are `psxrecomp.exe` and `psxrecomp-toml.exe` absent? | `psxrecomp-analyze.exe` was rebuilt with `cmake --build psxrecomp/recompiler/build --target psxrecomp-analyze`. The cause of its disappearance is not known. `docs/SETUP.md` (T0.5) says the recompiler build makes all three exes. Not checked. |
| 217 | Should `tools\grow_seeds.py` count manual addresses under their own label? | Its summary line counts manual addresses under "ACCEPT". The seed file itself is correct. Cosmetic. Not changed. |
| 218 | Where is `collect_game_misses.py`, and is it kept under `tools\`? | The T2.8 report gives the command but not its folder. `CLAUDE.md` requires disc claims to come from scripts in `tools\`. Not checked. |
| 219 | Which exe will the user record on, and is it frozen? | The Release exe SHA-256 is `b5573bbe...` (`docs/SETUP.md`, T2.8). D14 and D15 say the exe must be frozen before recording. The T2.8 report does not say which exe the user will use. Not decided. |