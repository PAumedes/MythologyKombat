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
| 44 | Do the EXE header, the crt0 values and the overlay load addresses match a debugger or Ghidra? | Partly answered in T1.5. Ghidra headless matches the entry point, text address and size, BSS range and heap start and size. Not yet checked in Ghidra: the overlay load addresses, GP, initial SP and the header's d, b and s fields. No emulator check is recorded. DuckStation cannot be queried automatically. T2.12 adds static checks of the overlay load address (`docs/EXE_OVERLAYS.md`). The runtime check is T2.13. See `docs/SETUP.md` (T1.5). |
| 45 | Where does the scratch read buffer come from, and does the memcpy into `0x80130FF8` overlap it? | The scratch allocator is at `0x800865C0`. crt0 starts the BIOS heap at `0x80130FFC`, inside the overlay window. The buffer may start near `0x80131000`, so the move may overlap. Not proven. The return value of the malloc(4) call at `0x8008652C` is unknown. |
| 46 | Which level is the second FIRE site at `0x8002E130`? | The function at `0x8002E130` also reads id 137 (`/OVERLAYS/FIRE.OVR`). T2.12 shows it is a second function that loads FIRE. It is selected by dispatcher index 7, and by index 10 when `[0x800D7E48] >= 0`. Which level or mode it serves is not known. Its constant id set was not checked by the reviewer (question 133). |
| 47 | What do `/OVERLAYS/BRDGDEMO.BIN` and `/OVERLAYS/WINDDEMO.BIN` hold? | They are 2048-byte files. The BRIDGE and WIND level functions read them. They are not copied to the window. Their contents were not analysed. |
| 48 | What do the leading address tables in BRIDGE, FIRE, WATER and WIND mean? | The tables hold 32, 27, 83 and 102 words. The words point at data inside the file, not at function starts. Their use is not known. |
| 49 | What is the part of the text range from `0x800D7B40` to `0x800D8000`? | The crt0 BSS start (`0x800D7B40`) lies inside the file-backed text range. All file bytes in that part are 0. Their meaning is not established. |
| 50 | Do any other functions load overlays? | Three `read_file` calls use a variable id: `0x80085CF8` and `0x80085D74` (in `0x80085AF8`), and `0x8008635C` (in the wrapper `0x80086324`). T2.12 corrects the earlier count of two. The reachable ids from these sites are outside 134 to 143, but the callback table at `0x80082DF4` calls the wrapper with unknown ids (question 132). The id tables behind these results were not checked by the reviewer (question 131). |
| 51 | Do FORTRESS and PRISON load at `0x80130FF8` for sure? | T2.12 gives two static checks for each. The EXE call sites land on function starts, and the containment check holds. Both give `0x80130FF8` as the one base. This is a strong consistency check, not proof. T2.13 (runtime) still owns the final confirmation. The earlier statement that FORTRESS had no jal targets in the window was wrong. |
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

## Upstream CLI wrapper (from T2.1)

| # | Question | Notes |
|---|----------|-------|
| 78 | Should the wrapper check that the retro-tools folder exists? | `tools\run_psxrecomp.ps1` does not check `RETRO_TOOLS_DIR` up front. A bad value can silently reuse a stale `work\py-psxrecomp`. Reviewer note. |
| 79 | Does the private Python copy go stale if the repo moves? | The `._pth` file in `work\py-psxrecomp` holds absolute repo paths, written once. If the repo moves, those paths are stale. Reviewer note. |
| 80 | Is the unmodified Python enough for the `generate` subcommand? | Partly answered at T2.3: `generate` exited 0 through the wrapper. The report does not say which Python ran, so the private fallback is not ruled out. Check the wrapper's printed line in `work\generate_run1.txt`. |

## Seeds and static coverage (from T2.2)

| # | Question | Notes |
|---|----------|-------|
| 81 | Are the 106 seeds that are not Ghidra function starts real functions? | They are analyzer function starts. Most are low or medium class. Addresses are in `work\seed_report.json` under `seed_classification.anomalies`. Needs review. See `docs/COVERAGE.md`. |
| 82 | Are the 325 Ghidra-only entries labels, not function boundaries? | All 325 carry PsyQ-style or OBJ label names. They are probably labels. Not confirmed. |
| 83 | What are the 2 Ghidra symbols that lie in no analyzer function? | `cb_data` at `0x8009761C` and `_spu_2pitch` at `0x800A8D18`. Possibly data. Not checked. |
| 84 | How many of the 1093 analyzer-only starts are real functions? | Most are orphans or low and medium prologue scans. The real count is unknown. |
| 85 | What are the 133 unresolved indirect transfers (129 `jalr`, 4 `jr`)? | This is the dispatch-miss worklist for T2.8. Not resolved. |
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
| 99 | Should an overlay toolchain be staged for the tcc tier (T2.8 and T2.16)? | The startup log says `tcc tier active but no bundled toolchain at build\overlay_toolchain`. Overlay gaps fall back to the interpreter. Not decided. See `docs/SETUP.md` (T2.4). |
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
| 116 | What causes the glitchy FMV audio? | The user said the intro movie audio is "really really glitchy". Candidate causes: the XA ADPCM audio path in the recompiled runtime, OpenBIOS, or the host audio device. Not decided. Planned for T2.10 (FMV check). |
| 117 | Is the FMV video frame rate correct? | The user was not sure whether the video was fine or only felt off because of the audio. Not measured. |
| 118 | Does DuckStation play the same movie with clean audio and the right frame rate? | Not done. The user did not report a DuckStation comparison of this movie. |
| 119 | Does the audio glitch change with other renderers? | Not tested. Try `--renderer software` in a windowed build. The headless build cannot test audio, because it has no audio (question 107). |
| 120 | What do the audio buffer settings in `game.toml` and `game_options.toml` do, and what are they set to? | Not checked. |
| 121 | Is the game locked to 60 Hz or 50 Hz? | The T2.5 headless run measured about 70 frames per second (question 108). Its renderer is not recorded (question 114). That rate may mean the frame pacing is not locked. Not verified. Check the pacing in a windowed run. |
| 122 | Does CPU load or frame pacing cause the audio glitch? | Not measured. The user did not report the system load. |
| 123 | Is this audio problem a known PSXRecomp issue? | Not checked. Search `psxrecomp\docs` for XA, audio and latency. This search has not been run. |
| 124 | Which key quits the game? | The user found the key, but did not say which key it is. Record it. |
| 125 | Which keys control the game, and what is the framework's default key map? | Not reported by the user. Find the default key map in the PSXRecomp source. |
| 126 | Was the main menu reached? | Not reported by the user. |
| 127 | Did the window run windowed or fullscreen? | Not reported by the user. |

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
| 137 | Can DMA, the BIOS, or a computed pointer write `0x80015134` or the window? | The EXE text has no store to the destination pointer. A static scan cannot exclude a write through a computed pointer, DMA or the BIOS. |
| 138 | Does any pointer outside the image (BSS or heap) point into the window? | The containment check for FORTRESS and PRISON would widen if one did. The check cannot exclude this. |
| 139 | Does anything read the last 2 bytes of `/OVERLAYS/FORTRESS.OVR`? | The size is 19,874, not a multiple of 4. The tool's word scan drops the last 2 bytes. The loader's memcpy length is get_size(id). Whether the code reads those bytes is not checked. |