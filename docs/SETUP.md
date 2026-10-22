# SETUP

## Repo initialisation (T0.1)

The repo lives at `<REPO_ROOT>`.

- The repo was created with `git init`. The branch is `master`.
- First commit: titled "T0.1: Initialise the repo safely". Its hash changed in the 2026-10-21 history rewrite (D31).
- The first commit holds 16 kit files. It holds no game data.
- Git ignores the game and scratch folders. This was checked with `git check-ignore -v`.

| Path | Git status | Check |
|------|------------|-------|
| `ps1_game/` | ignored | `git check-ignore -v` |
| `work/` | ignored | `git check-ignore -v` |

No `.bin` or `.cue` file is tracked.

The git user name is set in this repo's config to Patricio Aumedes. The first commit used the author name of the original local account until the 2026-10-21 history rewrite (D31), which set every commit to the new identity. See `docs/OPEN_QUESTIONS.md`, question 1.

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

## Install of missing prerequisites (T0.3)

No installers were run. Each tool came as a portable zip. Each zip was unzipped under `<RETRO_TOOLS_DIR>\<tool>`.

The `C:\` root was not writable, so the tools live under `<RETRO_TOOLS_DIR>`. This is the default root of `tools\check_prereqs.ps1`. To use another root, set the environment variable `RETRO_TOOLS_DIR`.

Final run of `tools\check_prereqs.ps1`: all 9 tools PRESENT, exit code 0.

| Tool | Version installed | Source |
|------|-------------------|--------|
| C/C++ toolchain (CMake, Ninja, clang) | CMake 3.31.12, Ninja 1.13.2, clang 22.1.8 | RetroPorting-Toolchains release v1.0.14 |
| Ghidra | 12.1.4 | Official Ghidra release |
| Java | Temurin JDK 21.0.12.1+1 | Eclipse Temurin |
| Node.js | 22.23.3 | Official Node.js release |
| Python | 3.12.10 (embeddable) | python.org |
| Emulator | DuckStation 0.1.12083 (portable) | Official DuckStation release |

Git was already PRESENT and was not changed.

### Download list

These are the downloads used. The zips were kept in `<RETRO_TOOLS_DIR>\_downloads`. They were deleted after Phase 1 (see Notes).

| Download | Source |
|----------|--------|
| `cmake-clang-v1-windows-x64.zip` | RetroPorting-Toolchains release v1.0.14 |
| `ghidra_12.1.4_PUBLIC_20260921.zip` | Official Ghidra release, 12.1.4 |
| Temurin JDK 21.0.12.1+1 zip | Eclipse Temurin |
| Node.js 22.23.3 zip | Official Node.js release |
| Python 3.12.10 embeddable zip | python.org |
| DuckStation 0.1.12083 portable zip | Official DuckStation release |

### Notes

- Python 3.12.11 and later have no Windows embeddable zip on python.org. The check for 3.12.11 returned 404. That is why 3.12.10 was used.
- The embeddable Python has no pip. The scripts in `tools\` must use only the Python standard library.
- A `portable.txt` file was added to the DuckStation folder.
- To use the C/C++ toolchain in a PowerShell session:

```
$env:PSXRECOMP_TOOLCHAIN_DIR = '<RETRO_TOOLS_DIR>\cmake-clang'
$env:PATH = '<RETRO_TOOLS_DIR>\cmake-clang\bin;' + $env:PATH
```

- The `_downloads` folder is outside the repo. On the user's request, the downloaded zips in `_downloads` (about 1.2 GB) were deleted after Phase 1. To reinstall a tool, download its zip again from the sources in the table above.

### Uninstall

Delete the folder `<RETRO_TOOLS_DIR>`.

## Reference emulator check (T0.7, Phase 0 gate)

This check is user-reported. No agent ran it, and no artifact was saved.

- Emulator: DuckStation 0.1.12083, portable, at `<RETRO_TOOLS_DIR>\duckstation`.
- Patricio booted the disc in DuckStation and confirmed it reaches gameplay.
- The first run needs the user's own PS1 BIOS dump. The BIOS file is not in this repo and must not be committed.

## Disc identity (T0.4)

The script `tools\disc_identify.py` reads the disc in `ps1_game\` and prints its identity. Run it from the repo root:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\disc_identify.py
```

- It writes `work\disc_identity.json`. The `work\` folder is git-ignored.
- It uses only the Python standard library. This fits the embeddable Python from T0.3.
- It is deterministic. Running it again gives the same output.
- It does not change anything in `ps1_game\`.
- If a `.cue` or `.bin` file is missing or misnamed, it stops with a clear message.
- The results are in `docs/DISC.md`. The file holds hashes and the serial only.

## Disc file list (T1.1)

The script `tools\disc_list.py` walks the disc's ISO 9660 tree and writes every file's name, path, start LBA, size, sector count and XA flags. Run it from the repo root:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\disc_list.py
```

- It writes `work\disc_files.json`. The `work\` folder is git-ignored.
- It uses only the Python standard library.
- It does not change anything in `ps1_game\`.
- The results are in `docs/DISC_MAP.md`. That page holds names, paths, sizes, LBAs and flags only. It holds no file contents.

## Disc format classification (T1.3)

The script `tools\disc_classify.py` gives each disc file a format tag. It also extracts the files. Run it from the repo root after `tools\disc_list.py`, because it reads `work\disc_files.json`:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\disc_classify.py [--no-extract]
```

- It writes `work\disc_classes.json`. The `work\` folder is git-ignored.
- It extracts files to `work\extracted\`. Extraction takes about 530 MB.
- On the user's request, `work\extracted\` (about 530 MB) was deleted after Phase 1. Run this script again, without `--no-extract`, to regenerate it.
- STR video files are extracted as raw 2352-byte sectors. Their names end in `.raw2352`.
- All other files are extracted as their Form 1 user data, cut to the ISO size.
- `--no-extract` skips the extraction step and writes the JSON only.
- The usage line also lists `--files PATH` and `--out PATH`.
- The results are in `docs/FORMATS.md`. That page holds tags and evidence kinds only. It holds no file contents.

## PSXRecomp framework (T0.5)

PSXRecomp is added as a git submodule at `psxrecomp\`. It is pinned to one commit.

| Item | Value |
|------|-------|
| Source | `https://github.com/RetroPortingToolKit/psxrecomp` |
| Path | `psxrecomp\` |
| Pinned commit | `449c31e5029f3a3281fa15060105928d2b3b13f7` |
| Describe | `v0.3.2-alpha-1770-g449c31e5` |
| Nested: `lib\recomp-net` | `e53059306824edf4f0aec4aae5ae65151b18535f` (v0.1.9) |
| Nested: `lib\retcomm-rbengine` | `2a03e73693acee0fb78076ea058642c931bef12e` |

### Shell setup

Run this in each new PowerShell session. Put Git's `bin` folder first on `PATH`, so `bash` is Git's bash.

```
$env:PSXRECOMP_TOOLCHAIN_DIR = '<RETRO_TOOLS_DIR>\cmake-clang'
$env:PATH = '<RETRO_TOOLS_DIR>\cmake-clang\bin;<RETRO_TOOLS_DIR>\python;' + $env:PATH
```

The compiler is clang 22, MinGW-style.

### Commands

Run these from the `psxrecomp\` folder.

```
git submodule add https://github.com/RetroPortingToolKit/psxrecomp psxrecomp
git submodule update --init --recursive

cmake -S recompiler -B recompiler/build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build recompiler/build --target psxrecomp-bios psxrecomp-game
bash tools/regen_bios.sh --config bios/OpenBIOS.toml

cmake -S runtime -B runtime/build -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSX_RECOMP_UI=OFF
cmake --build runtime/build --target psx-runtime
```

The recompiler build also makes `psxrecomp.exe`, `psxrecomp-analyze.exe` and `psxrecomp-toml.exe`.

### Results on this machine

| Step | Result |
|------|--------|
| Recompiler target `psxrecomp-bios psxrecomp-game` | Built |
| `regen_bios.sh --config bios/OpenBIOS.toml` | `EMIT OK`, emitted=651, interpreted=0, skipped=4, instructions=17526, dispatch_entries=3990 |
| Runtime target `psx-runtime` (about 1 min 44 s) | Built. Output is `runtime\build\PSXRecomp.exe` (30.4 MB) |

The runtime target writes `PSXRecomp.exe`, not `psx-runtime.exe`.

### Known deviation: default recompiler build fails

The default build `cmake --build recompiler/build` exits with code 1. Two upstream unit-test targets fail to link:

- `ws_cull_edge_interp_test`
- `draw_distance_interp_test`

The linker reports undefined symbols, for example `gr_backend`, `gl_renderer_texture_banks_supported` and `psx_mod_gpu_dma_resolve_address`. The build uses `-O3 -flto` with this toolchain. The reviewer reproduced the failure.

Use the explicit targets above instead. No upstream source was changed. It is not known whether upstream CI builds these targets with this toolchain. See `docs/OPEN_QUESTIONS.md`.

### Other notes from the build

- The Vulkan SDK is not installed. The Vulkan renderer is a software stub.
- The `psx-beetle` target was skipped. `libmednafen_psx.a` is absent.
- The `psx-oracle` build warns about `DEFAULT_BIOS_PATH`.

### Git status of the submodule

`git status` shows `psxrecomp` as modified. The cause is CRLF line endings. `core.autocrlf=true` changes the tracked generated `OpenBIOS*` files. With `--ignore-cr-at-eol` the diff is empty. The fix is not applied yet. See `docs/OPEN_QUESTIONS.md`.

- The submodule shows ` m` in `git status` for this reason (CRLF only, per the diff check above).
- Never commit it. Do not run `git add psxrecomp`, and do not run `git commit -a`. Either one stages the submodule's ` m` change.
- Stage only the named files of this repo, then run `git status` before each commit.

### Commit note

`.gitmodules` and the `psxrecomp` gitlink were committed in the T0.7 commit (titled "T0.7: Reference emulator check confirmed by user"). They were staged in that commit by accident of staging order.

## Leftover debug symbol hunt (T1.2)

The script `tools\symbol_hunt.py` scans every sector of the disc for debug symbols, linker map text, source paths and function-name-like strings. Run it from the repo root:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\symbol_hunt.py
```

- It takes about 5.5 minutes.
- It writes `work\symbol_hunt.txt`. The `work\` folder is git-ignored.
- It uses only the Python standard library.
- It does not change anything in `ps1_game\`.
- `--selftest` runs the built-in tests. They pass 12 of 12.
- The results are in `docs/SYMBOLS.md`. That page holds offsets and short context only. It holds no disc bytes.

## EXE header and overlay load addresses (T1.4)

The script `tools\exe_overlays.py` reads the boot EXE and the overlay files. It gives the EXE header, the start-up constants, and the load address and size of each `.OVR` file. Run it from the repo root after `tools\disc_classify.py`, because it reads `work\extracted\` and `work\disc_classes.json`:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\exe_overlays.py [--root PATH]
```

- It needs `work\extracted\SLUS_004.76` and `work\extracted\OVERLAYS\*.OVR` from T1.3.
- It needs `work\disc_classes.json` from T1.3.
- `work\extracted\` was deleted after Phase 1. Run `tools\disc_classify.py` (without `--no-extract`) first. It writes `work\disc_classes.json` and regenerates `work\extracted\`.
- It reads `ps1_game\*.bin` for the independent header parse. It only reads the disc. It does not change anything in `ps1_game\`. If the disc image is missing, the header is still written, and the independent parse is marked "not run".
- It writes `work\exe_header.json` and `work\overlay_candidates.json`. Both folders and files are git-ignored.
- It uses only the Python standard library.
- It is deterministic. Running it again gives the same output.
- The usage line also lists `--root PATH`, the repo root. It defaults to the folder above `tools\`.
- The results are in `docs/EXE_OVERLAYS.md`. That page holds addresses and sizes only.

## Game project scaffold (T0.6)

The game project was made with the upstream setup script, `setup_project.ps1`. The script was run in a temp folder. Its output was then copied into the repo root. See `docs\DECISIONS.md` (D3).

### Scaffold command

Run from the repo root. The `-Disc` path and the `-Dir` folder are relative.

```
powershell -NoProfile -ExecutionPolicy Bypass -File <path to setup_project.ps1> -Disc "ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue" -Dir work\scaffold-test -Name MythologyKombat -Players 1 -Yes -EnableRecompUi -NoNetplay -NoCi -NoFetchBoxart -NoGenerate -NoBuild -NoGithub -Description "Sub-Zero PS1 static recomp" -Publisher TBD -Year TBD -PsxrecompUrl https://github.com/RetroPortingToolKit/psxrecomp
```

- `-Publisher TBD` and `-Year TBD` are placeholders. Empty values made the disc probe fail, so real values were passed.
- `-NoGenerate` and `-NoBuild` mean nothing was generated from the disc and nothing was built by the script.

### Python workaround

The embeddable Python from T0.3 ignores `PYTHONPATH`. It reads its `._pth` file instead. The fix is a private copy of Python at `work\py-scaffold`. The script directory was added to its `python312._pth` file. The script finds this copy through the environment variable `PSXRECOMP_PYTHON`.

```
$env:PSXRECOMP_PYTHON = '<REPO_ROOT>\work\py-scaffold\python.exe'
```

### Disc probe result

| Item | Value |
|------|-------|
| Serial | SLUS-00476 |
| Boot file | `SLUS_004.76` |
| Track count | 1 |
| Entry point | `0x80090E70` |
| Seed addresses | 1175 |

### Files copied to the repo root

| File or folder | Purpose |
|----------------|---------|
| `CMakeLists.txt` | Project build file |
| `game.toml` | Game settings |
| `game_options.toml` | Game options |
| `codegen_setup.c`, `codegen_setup.h` | Code generation setup |
| `VERSION` | Version, `0.1.0` |
| `symbols.toml` | Symbol names |
| `psx_symbols.h` | Symbol header |
| `seeds\ghidra_funcs.txt` | 1175 function addresses, taken from the boot EXE's JAL targets |
| `catalog_identity.json` | Catalog identity |
| `.recomp.json` | Recompiler settings |
| `framework_pins.txt` | Framework pins |
| `assets\` | Asset folder |
| `scripts\package_release.sh` | Release script |
| `mods\preloaded\` | Preloaded mods folder |
| `tools\sync_symbols.py` | Symbol sync script |
| `.gitignore` | Extra lines added. Existing lines are kept |

- The name `seeds\ghidra_funcs.txt` is a misnomer. The addresses come from the boot EXE, not from Ghidra. See `docs/OPEN_QUESTIONS.md`.
- `disc_probe.json` holds an absolute path on this machine. It is git-ignored and is not committed.

### Edits made to `game.toml`

| Key | Value |
|-----|-------|
| disc | `ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue` (relative) |
| exe | `work\disc\SLUS_004.76` |
| `[prepare_disc]` `out_dir` | `work\disc` |

Extracted disc data stays under `work\`, as `CLAUDE.md` requires.

### Submodule and generated code

| Item | Value |
|------|-------|
| Submodule | `recomp-ui\` |
| Source | `https://github.com/RetroPortingToolKit/recomp-ui.git` |
| Pinned commit | `7c635c6b366a6e0d5d3c913a7fce6ec04dd9f256` |
| `generated\` | Git-ignored on purpose. Not committed |

- Do not run `git add psxrecomp`. The submodule shows as modified because of CRLF line endings. See `docs/OPEN_QUESTIONS.md`, question 13.

### Configure check

```
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
```

Result: exit code 0.

The configure step set these options:

| Option | Value |
|--------|-------|
| SDL3 | On |
| `PSX_NETPLAY` | OFF |
| OpenBIOS | Linked |
| `PSX_MAX_PLAYERS` | 1 |
| `PSX_SETUP_WIZARD` | ON (default) |
| recomp-ui backend | SDL3 |

### Leftover folders

`work\scaffold-test\` and `work\py-scaffold\` are scratch. They are safe to delete. They are git-ignored.

## Ghidra + PS1 loader + REA (T1.5)

Headless Ghidra (`analyzeHeadless`) opens the boot EXE with the PS1 loader. The headless run matches the EXE header and crt0 values from T1.4. REA could not open the EXE, so it is not registered. See `docs/DECISIONS.md` (D4).

- The PS1 loader was verified only with `analyzeHeadless`. The run is reproducible, and the reviewer re-ran it.
- The Ghidra GUI has NOT been opened by anyone. No agent and no user has checked the GUI. An earlier note that the GUI works was an automatic reply, not an observation. It is wrong and is withdrawn.
- A GUI check is an optional user step. See "Optional GUI check" below. It is question 62 in `docs/OPEN_QUESTIONS.md`.

### Tools

| Item | Version | Location |
|------|---------|----------|
| Ghidra | 12.1.4 (zip `ghidra_12.1.4_PUBLIC_20260921.zip`) | `<RETRO_TOOLS_DIR>\ghidra\ghidra_12.1.4_PUBLIC` |
| Java | Temurin JDK 21.0.12.1 | `<RETRO_TOOLS_DIR>\jdk` |
| PS1 loader | `ghidra_psx_ldr` release 2026.10.03 | Installed in Ghidra, see below |
| REA | `rea-agents` 6.7.0 (npm) | Not set up. Not registered |

Headless Ghidra needs Java on the path. Run this in each new PowerShell session:

```
$env:JAVA_HOME = '<RETRO_TOOLS_DIR>\jdk'
$env:PATH = '<RETRO_TOOLS_DIR>\jdk\bin;' + $env:PATH
```

### PS1 loader install

- Source: `https://github.com/lab313ru/ghidra_psx_ldr`, release 2026.10.03.
- Asset: `ghidra_12.1.4_PUBLIC_20261004_ghidra_psx_ldr.zip`, 9,159,228 bytes.
- SHA-256 as downloaded: `32abacd90a5950b97a0756f67e991c3cc0f8a62edd5531890d91af68a9916255`.
- This hash was not compared with a published hash. See `docs/OPEN_QUESTIONS.md`.

Ghidra uses two folders for extensions. Put the files in the right one.

| Folder | What it holds | Loaded by Ghidra? |
|--------|---------------|-------------------|
| `<RETRO_TOOLS_DIR>\ghidra\ghidra_12.1.4_PUBLIC\Ghidra\Extensions\ghidra_psx_ldr\` | The unpacked extension. `extension.properties` says version 12.1.4 | Yes |
| `<RETRO_TOOLS_DIR>\ghidra\ghidra_12.1.4_PUBLIC\Extensions\Ghidra\` | The zip, kept here. Not checked in the GUI, which was not opened | No |

A first attempt unpacked the zip into the wrong folder. Headless Ghidra then failed with "No load spec". The fix was to unpack into `Ghidra\Extensions\`.

### Headless import

Run `analyzeHeadless` from the `support\` folder of the Ghidra install. Pass a project folder under `work\`, then the import:

```
analyzeHeadless <project folder> <project name> -import work\disc\SLUS_004.76 -overwrite
```

- The run takes about 3 minutes. Analysis takes about 138 seconds.
- Ghidra picks the loader `PSX Executables Loader` on its own.
- Language: `PSX:LE:32:default`. Compiler spec: default.
- The EXE is at `work\disc\SLUS_004.76`. That is the path set in `game.toml` (T0.6).
- Scratch Ghidra projects are under `work\ghidra-test` and `work\ghidra-test2`. They can be deleted.

### Memory blocks

| Block | Start | End | Notes |
|-------|-------|-----|-------|
| CODE | `0x80010000` | `0x800D7FFF` | 0xC8000 bytes. Initialised |
| RAM | `0x800D8000` | `0x801FFFFF` | Not initialised. The loader sets it this way |
| Hardware | | | IO, DMA, timers, CDROM, GPU, MDEC, SPU and GTEMAC blocks. GTEMAC starts at `0x20000000` |

### What Ghidra shows

| Item | T1.4 value | Ghidra result |
|------|-----------|---------------|
| Entry point | `0x80090E70` | Entry at this address, named `start` |
| Text load address | `0x80010000` | CODE block starts here |
| Text size | `0xC8000` | CODE block ends at `0x800D7FFF` |
| BSS clear range | `0x800D7B40` to `0x80130FF8` | Matches `start()` |
| Heap start | `0x80130FFC` | Matches the first argument of InitHeap |
| Heap size | `sp - [0x800BF358] - 0x130FF8` | Matches `start()` |

- Ghidra found 1730 functions.
- `start()` clears BSS, saves `ra`, calls InitHeap, calls `main()`, then calls `trap(1)`.
- The entry is also tagged as a PsyQ `__SN_ENTRY_POINT` stub.
- Ghidra does not check GP, initial SP, or the header's d, b and s fields in this run.

### Warnings

- About 460 "Unable to read bytes" warnings come from data and BSS references. The RAM block is not initialised, so these reads fail.
- One "pcode error" is at `0x80090F1C`, after `trap(1)`. The word there is at file offset `0x8171C`. It is not a GTE instruction. The reviewer judged it harmless. The cause is not checked.

### Other loader results

- A raw binary import (BinaryLoader, `MIPS:LE:32:default`, base `0x80010000`, file offset `0x800`) found 1934 functions. The PS1 loader is the better path, so it is used.
- The Ghidra GUI has not been opened. Nothing shows that it opens the EXE with the PS1 loader. No GUI project was found under the user profile folder.

### Optional GUI check (user step, not done)

Only the user can do this. It is not needed for Phase 1.

1. Run `<RETRO_TOOLS_DIR>\ghidra\ghidra_12.1.4_PUBLIC\ghidraRun.bat`.
2. Create a Ghidra project outside the repo, for example under `%USERPROFILE%\ghidra-projects`.
3. Import `work\disc\SLUS_004.76` into that project. Ghidra should pick the PS1 loader.
4. Record the result in `docs/OPEN_QUESTIONS.md` (question 62).

### REA result

REA is `rea-agents` 6.7.0. It is a Node package from npm, under the MIT licence. Its source is at `https://github.com/morluto/rea`. It has one maintainer. It was first published on 2026-07-12. It has no install scripts. Its prebuilt Windows native addon was not audited.

| Check | Result |
|-------|--------|
| `npx -y rea-agents@6.7.0 doctor --json` | Ghidra checks pass: 12.1.4, headless, JDK 21. Failures only for hopper, ida, jadx and kuna, and for client registrations |
| `inspect work\disc\SLUS_004.76 --provider ghidra --format json` | Fails. See below |

The inspect command returned this error:

| Field | Value |
|-------|-------|
| error | Analysis failed |
| code | target_unavailable |
| category | unsupported_target |
| message | Cannot open artifact: unsupported binary format. |
| constraint | file_format_rejected |

- REA's raw-binary support covers 6502, x86, x86_64, arm, arm64 and m68k. It does not cover MIPS.
- REA's documented Windows Ghidra support is experimental. It covers native x86, x64 and ARM PE files.
- So REA does not return pseudocode for the EXE. The T1.5 acceptance check for REA is not met. The failure is recorded here. Pseudocode came from Ghidra headless instead.
- `rea-agents setup` was not run. It would write to user-level files: `~/.claude.json` and `~/.claude/skills`. No MCP server is registered.
- The npm cache for the test was kept under `work\npm-cache`. Outputs are under `work\rea-out`. The reviewer checked that `~/.claude.json` is unchanged.

### Git status

`psxrecomp` still shows as modified, as in T0.5. Do not commit it. See `docs/OPEN_QUESTIONS.md`, question 13.

## SDK function names (T1.6)

The script `tools\ghidra_sdk_names.py` runs Ghidra on the boot EXE and names the Sony library (PsyQ) functions. It writes `work\symbols_sdk.json`. The version evidence and the name counts are in `docs/SYMBOLS.md`.

Run it from the repo root:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\ghidra_sdk_names.py [--reuse] [--ghidra PATH] [--jdk PATH] [--root PATH] [--exe PATH] [--out PATH]
```

| Option | Meaning |
|--------|---------|
| `--reuse` | Re-open the existing Ghidra project under `work\ghidra-sdk\` with `-process -noanalysis`. |
| `--ghidra PATH` | Ghidra install folder. Defaults to the `GHIDRA_HOME` variable, then to `<RETRO_TOOLS_DIR>\ghidra\ghidra_12.1.4_PUBLIC`. |
| `--jdk PATH` | JDK folder. Defaults to the `JAVA_HOME` variable, then to `<RETRO_TOOLS_DIR>\jdk`. |
| `--root PATH` | Repo root. Defaults to the folder above `tools\`. |
| `--exe PATH` | Boot EXE. Defaults to `work\disc\SLUS_004.76`. |
| `--out PATH` | Output file. Defaults to `work\symbols_sdk.json`. |

- Without `--reuse`, the Ghidra project is rebuilt from scratch. This takes about 2.5 minutes.
- With `--reuse`, the run takes about 13 seconds in the test run. The script's own header says about 20 seconds.
- The output is deterministic. Two runs give byte-identical files (checked with `cmp`).
- It needs `work\disc\SLUS_004.76` from T1.4.
- It does not change anything in `ps1_game\`.

### Version scan

The script `tools\psyq_version_scan.py` checks the EXE's library-version records against the PsyQ object-signature sets. It prints a count per set and writes `work\psyq_version_scan.json`.

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\psyq_version_scan.py [--root PATH] [--ghidra PATH]
```

- Its `--ghidra` default is the hard-coded Ghidra path above. It does not read `GHIDRA_HOME`.
- It has no existence checks. It opens files without closing them. See `docs/OPEN_QUESTIONS.md`.
- It needs `work\disc\SLUS_004.76` from T1.4.

## Upstream CLI wrapper (T2.1)

The script `tools\run_psxrecomp.ps1` runs the upstream `psxrecomp_cli.py`. Run it from the repo root, with `--config game.toml`:

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_psxrecomp.ps1 <subcommand> ...
```

| Item | Behaviour |
|------|-----------|
| `RETRO_TOOLS_DIR` | Environment variable. Sets the retro-tools folder. Defaults to `<RETRO_TOOLS_DIR>` |
| Toolchain | Sets `PSXRECOMP_TOOLCHAIN_DIR`. Puts `cmake-clang\bin` and Git's `bin` folder first on `PATH`. Git's `bin` gives bash |
| Output | Prints which Python and which toolchain it uses |
| Exit code | The upstream exit code is passed through |
| Exit 4 | STOP. No Python works, so nothing ran |

Python choice: see `docs/DECISIONS.md` (D5). The first option is the unmodified `<RETRO_TOOLS_DIR>\python\python.exe`, without `-I`. The fallback is a private copy at `work\py-psxrecomp`. The script makes it only when the first option fails. The variable `PSXRECOMP_FORCE_PRIVATE_PY=1` forces the fallback, for testing.

### Disc re-verification

Verify the disc with the wrapper:

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_psxrecomp.ps1 verify-disc --config game.toml --disc "ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue"
```

- A relative `--disc` path resolves against the config's folder. So run this from the repo root, with `game.toml`.
- `verify-disc` passes if any one digest family matches. Only `tools\check_boot_exe.py` checks all of them.

Check the boot EXE with the retro-tools Python:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\check_boot_exe.py
```

- It compares the SHA-256 of `work\disc\SLUS_004.76` with `45a937ac7785af328ae90cba37924b7b7c423ef01c28c116f193e1c1c0d0f1cd`. The file is 821248 bytes.
- It also compares the size, and the known MD5, SHA-1 and CRC-32 values in `game.toml`, with `disc_probe.json`.
- `disc_probe.json` is git-ignored and holds paths for this machine. If it is absent, the check is skipped.

Results on this machine:

| Check | Exit code | Output or reason |
|-------|-----------|------------------|
| `verify-disc` on the real disc | 0 | `Main track accepted; subchannel status: unknown` |
| `verify-disc` with zeroed digests (negative test) | 3 | `disc digests not in prepare_disc.known_*` |

- `ps1_game\` was checked before and after. The file sizes and modified times did not change.

## Seed sanity and static coverage (T2.2)

Two commands check the seed list and count what the analyzer covers. The counts are in `docs/COVERAGE.md`. Run both from the repo root.

### Seed check

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\check_seeds.py [--no-run]
```

- It runs `psxrecomp-analyze` itself. It sets `PATH` before it runs.
- It writes `work\seed_report.json` and the files in `work\analysis\`. Both are git-ignored.
- It exits with code 1 if a seed is invalid or duplicated.
- The seed file path is fixed in the script. There is no `--seeds` option.
- The usage line lists `--no-run`. See `docs/OPEN_QUESTIONS.md`, question 88.

### Ghidra function export

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\ghidra_sdk_names.py --all-funcs
```

- It reuses the Ghidra project under `work\ghidra-sdk\`.
- It runs `tools\ghidra_scripts\ExportAllFunctions.java`.
- It writes `work\ghidra_funcs_all.txt`. The file has 1730 entries: 1552 CODE, 153 GTEMAC and 25 RAM.
- It leaves `work\symbols_sdk.json` untouched.
- It saves the Ghidra project again. See `docs/OPEN_QUESTIONS.md`, question 89.

## First Generate (T2.3)

This step runs the upstream generator on the boot EXE. It writes C code to `generated\`. Run it from the repo root:

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_psxrecomp.ps1 generate --config game.toml --project-root . --disc "ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue"
```

- No `--bios` and no `--force-prepare` were passed.
- Logs are in `work\generate_run1.txt`, `work\generate_run2.txt` and `work\generate_run3.txt`. The `work\` folder is git-ignored.
- `prepare_disc` was skipped, because `work\disc\SLUS_004.76` already exists.
- The OpenBIOS backends were reused. They were not regenerated.

### Runs

| Run | Kind | Result |
|-----|------|--------|
| 1 | First run | Exit 0, 76 s. About 60 s was a one-time rebuild of the emitters in `psxrecomp\recompiler\build` |
| 2 | Incremental | No-op, 9 s. Log shows 58 shards, 0 updated. Dispatch unchanged |
| 3 | From scratch (`generated\` deleted first) | Output SHA-256 list is byte-identical to run 1 |

- The from-scratch comparison (run 3 against run 1) is the real determinism test. Run 2 only checks that a second run changes nothing.

### Output

`generated\` holds 61 files. The folder is git-ignored. `git check-ignore` matches `.gitignore` line 4.

| File | Content |
|------|---------|
| `SLUS_004.76_decls.h` | Declarations |
| `SLUS_004.76_dispatch.c` | Dispatch table |
| `SLUS_004.76_full.ranges` | Ranges |
| `SLUS_004.76_full_00.c` to `SLUS_004.76_full_57.c` | 58 C shards |

| Item | Value |
|------|-------|
| Functions emitted | 7262 |
| Lines of C | 2,157,405 in the 58 shards |
| Dispatch table entries | 2890. All lie in `0x80015EC0` to `0x800D7F8C`. No BIOS functions |
| Analysis | 2589 functions, 59796 basic blocks, 2713 loops |

### Discovery

- 2203 entries came from the `jr ra` scan.
- 2319 entries came after the JAL targets were added.
- 1175 seeds were added.
- 6 forced entries were added: `0x8001F208`, `0x80031BC8`, `0x80031CF8`, `0x80031E98`, `0x80032080` and `0x8003213C`.
- The pre-pass reports 4673 new entry points and 7262 functions.

### Warnings

| Warning | Count | Notes |
|---------|-------|-------|
| Reserved opcode (data read as code) | 141 | The tool hides these. Set `PSXRECOMP_VERBOSE_RI_WARNINGS=1` to see them |
| "out-of-function branch/jump, emitting fallthrough" | 562 (508 branch, 54 jump) | Saved in `work\generate_run1_oof_warnings.txt`. Clustered at `0x800D5B08` to `0x800D5E54`, `0x800D6610` to `0x800D6638`, `0x800D7290` and `0x800D7824` |
| `/* TODO: opcode=0x.. */` in generated C | 5201 (reviewer count) | Mostly `0x800BA3F4` to `0x800D7A84` |

- The reviewer found that the bytes at `0x800D5B08`, `0x800D7290` and `0x800D7824` are data tables. The emitter decodes them as code. They are probably unreachable. This is not verified.
- The reviewer judged `0x800D6610` ambiguous.
- See `docs/OPEN_QUESTIONS.md`, questions 91 to 95.

### Strict mode

- `game.toml` sets `[recompiler] strict = true`.
- `config_loader.h` line 942 says the value is "currently always true". The log prints no strict banner and no skip count.
- "No skipped-function failures" means that no skip lines appear in the log.
- The generated C has no `interpret`, `SKIPPED`, `unsupported` or `halt` markers.

### Checks after the run

- The submodule `psxrecomp\` is unchanged. Only the known CRLF noise shows (`docs/OPEN_QUESTIONS.md`, question 13).
- `ps1_game\` is unchanged.
- The boot EXE SHA-256 is unchanged.
- `generated\` is not committed.

## Game executable build (T2.4)

This step builds the game exe, `build\MythologyKombat.exe`, from the repo root.

### Environment

Run this in each new PowerShell session. `<Git>` is Git's install folder.

```
$env:PSXRECOMP_TOOLCHAIN_DIR = '<RETRO_TOOLS_DIR>\cmake-clang'
$env:PATH = '<RETRO_TOOLS_DIR>\cmake-clang\bin;<Git>\bin;<RETRO_TOOLS_DIR>\python;' + $env:PATH
```

### Commands

```
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSXRECOMP_REQUIRE_GAME_C=ON
cmake --build build --target psx-runtime
```

- The existing `build\` cache was Ninja and Release, with `PSXRECOMP_REQUIRE_GAME_C` OFF. The configure step changed it to ON.
- The build uses Ninja's default job count on 4 logical CPUs, with 31.9 GB RAM. It did not run out of memory.

### Steps on this machine

| Step | Result |
|------|--------|
| Configure | 8.8 s. Log: `psxrecomp: linking generated game C (full runtime) — generated/SLUS_004.76_dispatch.c`. Log: `BIOS backends linked: OpenBIOS`. The SCPH1001 backend was skipped. This is expected |
| First build of `psx-runtime` | 428 steps, about 2 min 36 s. The link failed at step 427 of 428. See the link failure below |
| Rebuild after the fix | Relink took 1.7 s. Built |

### Link failure and workaround

- Error: `ld.lld: error: duplicate resource: type MANIFEST (ID 24)/name ID 1/language 1033`. It names `psx-runtime_manifest.rc.obj` and `psx-runtime_recomp_utf8_manifest.rc.obj`.
- Cause: an upstream bug. Both psxrecomp and recomp-ui add an application manifest to the same target.
  - `psxrecomp\cmake\psx_windows_manifest.cmake` adds the manifest object.
  - `recomp-ui\recomp_ui.cmake` adds a second manifest resource. Its guard does not see the object, so it adds a second `.rc` file.
- Both manifests say `asInvoker`, with the same `supportedOS` GUIDs and UTF-8 code page. Neither has DPI or common-controls settings. So dropping the recomp-ui one loses nothing.
- Workaround: the root `CMakeLists.txt` removes `psx-runtime_recomp_utf8_manifest.rc` from the target on Windows with a non-MSVC compiler. See `docs/DECISIONS.md` (D6).
- No upstream option turns this off. The check was run on psxrecomp `449c31e5` and recomp-ui `7c635c6`.

### Result

| Item | Value |
|------|-------|
| File | `build\MythologyKombat.exe` |
| Size | 46,905,344 bytes |
| SHA-256 | `66fdb5be60c2b023465cadeb1b6a79f889f2d8553f1709ca1535224590052af5` |
| Built | 2026-10-20 10:23 |
| Linking | Static. SDL 3.4.10 is built in. No DLLs sit beside the exe |
| Compiler | clang 22.1.8. Release, `-O3 -DNDEBUG` |
| Execution profile | ENHANCED. Identity `a45799857ef4be4851e3bd2957092a1955434f1c8942f65093da26ad875ad1e9` |
| Manifest | One embedded manifest (`<assembly` appears once). It is not XML-validated |

- Any rebuild changes the SHA-256. Record the SHA of the build that is tested.

### Warnings

- First build: 58 warnings. All come from upstream code, not from generated code.
  - `-Wcomment` at `pgxp.h` line 206 and `gpu_sw_renderer.c` line 1944.
  - `-Wformat-truncation` at `traps.c` line 1441.
  - `-Wswitch` at `launcher_imgui.cpp` line 14199.
- Rebuild: 0 warnings.

### Files staged beside the exe

| Path under `build\` | Note |
|---------------------|------|
| `bios\openbios.bin` | OpenBIOS |
| `bios\OpenBIOS.LICENSE` | OpenBIOS licence |
| `game.toml`, `game_options.toml` | Game config copies |
| `mods\README.md` | Mods folder note |
| `mods\bundled\` | 6 framework packages |
| `assets\psxrecomp.png` | Image |
| `MythologyKombat.execution.json` | Execution profile |

### Command line

`MythologyKombat.exe --help` and `--version` are not supported. The exe starts the launcher and the SDL path instead. Flags, from `psxrecomp\runtime\src\main.cpp`:

| Flag | Meaning |
|------|---------|
| `--disc <path>` | Disc image |
| `--game <toml>` | Game config |
| `--bios <path>` | BIOS file |
| `--no-launcher` / `--launcher` | Skip or show the launcher |
| `--headless` | No window and no audio. TCP screenshots and state still work |
| `--hidden-window` | Full presenter in a window that is never shown |
| `--headless-opengl` | Hidden GL context. Needs real OpenGL |
| `--debug-port <n>` | Debug port. Default 4370 |
| `--memcard-dir <path>` | Memory card folder |
| `--renderer software\|opengl\|vulkan` | Renderer choice |
| `--game-mode` / `--no-game-mode` | Game mode on or off |
| `--window-title` | Window title |
| `--audit-mod-plugins` | Mod plugin audit |
| `--netplay`, `--net-*`, `--netplay-query` | Netplay options |

- Debug tools are NOT compiled in. `PSX_DEBUG_TOOLS` is OFF in this build, so no TCP debug server runs on port 4370. An earlier line here said the opposite. That line was wrong. See the headless smoke test below (T2.5) and `docs/DECISIONS.md` (D7).
- Startup log: `tcc tier active but no bundled toolchain at build\overlay_toolchain (overlay gaps -> interpreter)`. No overlay toolchain is staged. See `docs/OPEN_QUESTIONS.md`.

## Headless smoke test (T2.5)

The script `tools\smoke_boot.py` starts the game exe with no window. It checks that the game keeps running and keeps drawing frames. It is an automated check. It is not the user's play test, which is T2.6.

Run it from the repo root:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\smoke_boot.py [--seconds 60] [--exe X] [--disc cue] [--port 4370] [--renderer software|opengl|vulkan] [--startup-wait 30] [--kill] [--self-test-kill]
```

- The defaults of `--seconds`, `--renderer` and `--startup-wait` are not recorded here. See `docs/OPEN_QUESTIONS.md`.
- `--self-test-kill` kills the child at 5 s. It tests the kill switch. The run then exits 1.
- `--kill` clears a stale instance before the run. It was tested on a stale instance on port 4377.

### Which exe is tested

The script uses the first of these that applies:

| Order | Source |
|-------|--------|
| 1 | `--exe PATH` |
| 2 | Environment variable `SMOKE_EXE` |
| 3 | `work\build-dbg\MythologyKombat.exe`, if it exists |
| 4 | `build\MythologyKombat.exe` |

The script prints the exe path and its SHA-256 at the start. The debug build from this step has SHA-256 `7bcb28c2693038e1f830bd10802eba2a58fb2817f41adf5b994fa546edc66a21`.

### Launch

The script starts the exe with the working folder set to the exe folder:

```
<exe> --disc "<cue>" --game <exedir>\game.toml --no-launcher --headless --debug-port 4370 --memcard-dir work\smoke_saves
```

The script talks to the game over TCP. The server binds 127.0.0.1 only. `netstat` was used to check this.

### PASS rules

The run passes only if all three hold:

- The game process stays alive for the whole run.
- The frame counter goes up on each check.
- No `psx_crash.txt` appears. The script watches the working folder, the exe folder, the memory card folder and the repo root. The file location is inferred from the upstream code (relative `fopen` in `runtime/src/memory.c` and `traps.c`). No crash was seen, so the file was never written in a test.

### Outputs

| Path | Content |
|------|---------|
| `work\smoke\run.log` | Run log |
| `work\smoke\pid.txt` | PID of the game process |
| `work\shots\smoke_t00.png` | Screenshot at the start |
| `work\shots\smoke_t10.png` | Screenshot at 10 s |
| `work\shots\smoke_t30.png` | Screenshot at 30 s |
| `work\shots\smoke_end.png` | Screenshot at the end |

- Screenshots are 320 by 240 PNG files.
- A screenshot that fails, for example with `display disabled`, is retried until 8 s after its mark.
- All files are under `work\`, which is git-ignored.

### Stopping and safety

- A `try/finally` block sends `quit` over TCP. It waits 10 s. If the game is still running, it terminates the process. It then runs `taskkill /F /T` on the child PID only. It never kills by image name.
- Before killing, the script checks the PID in `work\smoke\pid.txt` with `tasklist`. The PID must be `MythologyKombat.exe`.
- The script refuses to start if a stale instance runs or the port is in use.
- The script handles `KeyboardInterrupt`.

### Exit codes seen in tests

| Case | Result |
|------|--------|
| Wrong disc path | Exit 2. `FAIL(setup): disc image not found` |
| Invalid cue file | The game prints `Disc Could Not Be Mounted`. Exit 1 |
| `--self-test-kill` | Exit 1 |
| Release exe (see below) | Exit 1, with an explanation |

### Why the Release exe does not work

`build\MythologyKombat.exe` is built with `PSX_DEBUG_TOOLS=OFF`. The upstream `BUILDING.md` says Release turns the TCP debug server off. So port 4370 never opens.

- The harness fails after about 9 s. It does this when the `CMakeCache.txt` next to the exe says `PSX_DEBUG_TOOLS` is not ON.
- `build\` stays the shipping exe. The T2.6 user run uses it, and it needs no debug server.
- The harness uses a separate debug-tools build. See `docs/DECISIONS.md` (D7).

### Debug-tools build (for tests)

Run this in PowerShell from the repo root. `<Git>` is Git's install folder.

```
$env:PSXRECOMP_TOOLCHAIN_DIR = '<RETRO_TOOLS_DIR>\cmake-clang'
$env:PATH = '<RETRO_TOOLS_DIR>\cmake-clang\bin;<Git>\bin;<RETRO_TOOLS_DIR>\python;' + $env:PATH
cmake -S . -B work\build-dbg -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSX_DEBUG_TOOLS=ON -DPSXRECOMP_REQUIRE_GAME_C=ON
cmake --build work\build-dbg --target psx-runtime
```

- The build takes about 5 minutes with ccache. It exits 0.
- The log shows `BIOS backends linked: OpenBIOS` and `linking generated game C (full runtime)`.
- It uses the same `generated\` inputs as `build\`.
- The root `CMakeLists.txt` manifest workaround (D6) applies.
- The debug build is not committed. `work\` is git-ignored.
- The debug build SHA-256 is listed above.
- An alternative is to turn on `PSX_DEBUG_TOOLS` in `build\` itself. That was not done. See `docs/OPEN_QUESTIONS.md` (103).

### Test results

| Run | Result |
|-----|--------|
| 60 s run, debug build | PASS. Frames 40 to 4319, about 70 frames per second. No `psx_crash.txt` |
| 20 s run, reviewer | PASS |
| 20 s run, final script | PASS. Frames 38 to 1788. Screenshots `t0`, `t10` and `end` written |

- The screenshots checked in the tests are all 230723 bytes. This is judged harmless. See `docs/OPEN_QUESTIONS.md`.
- Agent reports describe the screenshots. These descriptions are not checked by a user. They are not the T2.6 gate. See `docs/OPEN_QUESTIONS.md`.

### Side effects

- A run of the Release exe writes `psx_freeze_heartbeat.json` at the repo root and in `build\`. Both are git-ignored.
- The same run writes `build\overlay_captures.json`. This path existed before this step. It is git-ignored. Never commit it.
- No orphan processes were left after the tests. `tasklist` was checked.

### Not tested

- The `opengl` and `vulkan` renderers.
- `--hidden-window` and `--headless-opengl`.
- A real Ctrl-C.
- Audio. Headless mode has no audio.
- Timing against real hardware.

See `docs/OPEN_QUESTIONS.md` (104 to 114).

## Visual first boot (T2.6)

This is the user's play test. It is user-reported. No agent ran it, and no artifact was saved. No agent checked the picture or the sound. The outcome is recorded as accepted: the Midway logo and the intro movie were reached, and there was no crash.

### Run

| Item | Value |
|------|-------|
| Exe | `build\MythologyKombat.exe` (Release build) |
| SHA-256 | `66fdb5be60c2b023465cadeb1b6a79f889f2d8553f1709ca1535224590052af5` |
| BIOS | OpenBIOS |
| Renderer | `opengl`, the default in `game.toml` |
| Window | Yes |
| Command | `build\MythologyKombat.exe --disc "<REPO_ROOT>\ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue" --game build\game.toml --no-launcher` |

### What the user saw

| Check | Result (user report) |
|-------|----------------------|
| Sony logo | Not seen |
| Midway logo | Seen |
| Intro movie (FMV) | Played |
| FMV audio | "Really really glitchy" |
| FMV video frame rate | Not sure. The bad audio may have made it feel off |
| Crash or black screen | None seen |
| Key to quit inside the game | Found. The key was not recorded |

Not reported by the user:

- Whether the main menu was reached.
- The key bindings.
- Whether the window was windowed or fullscreen.
- The system load.

### Notes

- The Sony logo is probably drawn by the retail BIOS. OpenBIOS has no such logo. This is a guess, not checked. See `docs/OPEN_QUESTIONS.md`, question 115.
- The FMV audio problem is handed to T2.10 (the FMV check). T2.9 and T2.12 run in parallel with it. See `docs/OPEN_QUESTIONS.md`, questions 116 to 127.
- The headless smoke test (T2.5) has no audio. So it cannot show the audio problem. See question 107.

## Playtest 2: FMV and gameplay (T2.10/T2.11 partial)

This is the user's second play test. It is user-reported. No agent ran it, and no artifact was saved. No agent checked the picture or the sound. The frame rates are the user's estimates, not measured values. At the time of this playtest, T2.10 and T2.11 were left as they were in `docs/TASKS.md`. This section did not change their status.

### Run

| Item | Value |
|------|-------|
| Exe | `build\MythologyKombat.exe` (Release build) |
| SHA-256 | Not given in the report. Not checked |
| BIOS | OpenBIOS |
| Renderer | `opengl` |
| Window | Windowed |
| Command | Same as T2.6: `build\MythologyKombat.exe --disc "<REPO_ROOT>\ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue" --game build\game.toml --no-launcher` |

### What the user saw

| Check | Result (user report) |
|-------|----------------------|
| Midway logo movie | A first digital glitch. Then it stutters, as in the first play test |
| Intro movie | Only stuttering audio reported. The picture was not described |
| Movie frame rate | About 50 fps. The user's estimate is 48 at the lowest and 54 at the highest |
| Game after the first menu | Runs at 60 fps with no issue |
| Main menu | Reached |
| New game | Started |
| Fight | Played. The user died in it. Controls responded. Play time not stated |
| Level or location | Not stated. Not named here |
| Gameplay audio | "Apparently ok" |
| Crash | None reported |
| Keys | See `docs\CONTROLS.md` |
| Quit | The user asked whether to close the window. The answer was yes. The quit key was not recorded |

### Not reported by the user

- Which movies play, apart from the Midway logo and the intro.
- Which level or location the fight was in.
- Monitor refresh rate.
- CPU model, system load and power plan.
- Whether `PSX_RUNTIME_PERF_DIAG` was run. It was not.

### Reading (agent hypothesis, not verified)

The reading below comes from `work\audio_investigation.md`. It is not a finding.

- Hypothesis 1: the movies run below real time. The NTSC real-time rate used there is about 59.94 fps. At 48 to 54 fps the audio starves and stutters. Gameplay holds 60 fps, so it does not starve.
- Hypothesis 2: the first glitch is a cold-start or cache warm-up effect. Not tested.
- Other candidates in that file: the host audio device or format, other CPU load, the power plan, a monitor that is not 60 Hz, and overlay code that runs in the interpreter. The overlay toolchain is not staged (see `docs/OPEN_QUESTIONS.md`, question 99). The PGO profile is empty.
- Real XA bug: judged unlikely. The XA decode in `psxrecomp\runtime\src\cdrom.c` (lines 1395 to 1430) reads stereo, 37800 Hz, 4-bit sectors. The comment at lines 2628 to 2640 says a stream freeze that starved XA was removed on 2026-07-10. The read of these lines was done by reading code. It was not run.
- Upstream notes: `psxrecomp\docs\ENHANCEMENTS.md` reports a "sluggish FMV" for another title. The investigation cites this as context. It is not about this game.
- OpenBIOS: no evidence of a cause.

### Flags and settings to try

None of these has been run yet. Names come from the investigation. The names were found in the runtime source.

| Flag or setting | What the investigation says it does | Status |
|-----------------|-------------------------------------|--------|
| `PSX_RUNTIME_PERF_DIAG=1` and `PSX_RUNTIME_PERF_DIAG_MS=1000` | Prints guest Hz, SPU Hz, audio fill, underruns, and overlay native and interpreter counts | Not run |
| `F` key, or `PSX_FPS_TELEMETRY=1` | Shows the fps counter | `F` was reported working |
| `PSX_VSYNC=0`, or `video_vsync` in `settings.toml` | Vsync setting | Not run |
| `--renderer software` | Software renderer | Not run |
| `PSXRECOMP_AUDIO_LEGACY=1` | Older audio path | Not run |
| `[audio] buffer_ms` in `game.toml` | Audio buffer. Range 30 to 500. Default 180 | Range and default checked in code. `build\game.toml` has no `[audio]` block, so 180 is used. Not changed yet |
| `PSX_LOAD_DELAY=0` | Diagnostic only. Upstream says FMV is much faster with it. Do not keep | Not run |
| Debug build (`work\build-dbg`) TCP commands: `audio_stats`, `audio_wav`, `audio_events`, `fmv_state`, `cdrom_state`, `cdrom_sector_history`, `mdec_state`, `frame_perf`, `pace_state` | Inspect audio, FMV and pacing state | Not run. The names are in `psxrecomp\docs\TCP_COMMANDS.md` |

### Planned next steps

1. The user runs once with the diagnostic flag. In PowerShell: `$env:PSX_RUNTIME_PERF_DIAG = '1'`. Then run the exe with the T2.6 arguments, with stdout sent to `work\perf.log` (for example `> work\perf.log`). The user presses `F` during the intro.
2. Then try `--renderer software` and `PSX_VSYNC=0`, one at a time.
3. Agents read `work\perf.log`.

Candidate engineering fixes, not decided:

- Stage the overlay toolchain (the tcc tier), so overlay gaps are not interpreted.
- A PGO or LTO build.
- Find where the FMV decode runs, in the EXE or in an overlay.

See `docs/OPEN_QUESTIONS.md`, questions 116 to 127 and 148 to 161.

## FMV check (T2.10) and first fight (T2.11)

Status: T2.11 is `done` in `docs/TASKS.md`. T2.10 was `in-progress` until the user descoped it on 2026-10-20. It is now `done`, with the movies checked so far (`docs/DECISIONS.md`, D17). Three kinds of evidence are kept apart below: user-reported (playtests 1 and 2 above), agent-observed (debug build, headless, `tools\fmv_identify.py`), and user-session facts read from artifacts of the user's own recordings (`telemetry.csv`, the visible coverage run). Picture and audio quality are user-reported only. Disc reads, LBAs and files come from the traces.

### Movies the user reported

| Movie | File | Picture | Audio | Frame rate |
|-------|------|---------|-------|------------|
| Midway logo | `MIDWAY01.STR` (file matched by LBA trace, see "Movies identified by LBA") | Digital glitch, then stutter (vsync on). Vsync off: not reported | Stutters (vsync on). Clean with vsync off | 48 to 54 fps, user estimate (vsync on). About 60 fps (vsync off) |
| Intro | `SZINTRO1.STR` (matched by LBA trace and by order in the user's own session telemetry; the user did not name the file) | Not described | Stutters (vsync on). Clean with vsync off | 48 to 54 fps, user estimate (vsync on) |
| Sony logo | Not seen by the user. No movie file is read before `LEGAL.STR` in any trace, so no STR file is a candidate. Not identified | Not seen | Not seen | Not seen |

- Telemetry (`tools\session_fps.py`, D9 in `docs/DECISIONS.md`): XA mean 51.9 Hz with vsync on, 59.9 Hz with vsync off. The telemetry does not name the movie.
- Clean audio with vsync off is the user's words for "movie audio". It is not split by movie.

### Movies identified by LBA

Tool: `tools\fmv_identify.py` (stdlib only). It cold-boots `work\build-dbg\MythologyKombat.exe --headless`, pulls the new entries of `cdrom_sector_history` every 0.4 s (de-duplicated by `seq`; the 8192-entry ring did not wrap in any run) and samples `fmv_state` (`mdec_decode_count`). It maps each LBA to a disc file with the same `work\disc_files.json` that `tools\lba_lookup.py` uses. `--telemetry DIR` does the same for a recorded session's `cd_lba` column. Results are saved in `work\fmv\` (git-ignored). "Other reads" are all non-XA-audio sector reads (STR picture data); the history does not mark video sectors, and an LBA can be read more than once. Frames are guest VBlanks (the debug server `frame` number). Picture and audio quality were not judged here.

Agent-observed, no input at all (`--route none --until 6200`, 88 s wall; `work\fmv\identify_noinput.json`):

| Order | Movie file | LBA range read | First frame | Last frame | XA-audio reads | MDEC decodes in window |
|-------|-----------|----------------|-------------|-----------|----------------|------------------------|
| 1 | `LEGAL.STR` | 151572-151674 | 372 | 413 | 0 | 9 |
| 2 | `MIDWAY01.STR` | 153072-154822 | 848 | 1548 | 217 | 176 |
| 3 | `SZINTRO1.STR` | 187024-195845 | 1554 | 5082 | 1104 | 887 |
| 4 | `SZLOGO15.STR` | 196167-196989 | 5089 | 5418 | 103 | 82 |

Agent-observed, boot route `boot_to_menu` (START at frame 3000, CROSS at frame 4000; `--until 5600`, 75 s wall; `work\fmv\identify.json`):

| Order | Movie file | LBA range read | First frame | Last frame | XA-audio reads | MDEC decodes in window |
|-------|-----------|----------------|-------------|-----------|----------------|------------------------|
| 1 | `LEGAL.STR` | 151573-151674 | 373 | 413 | 0 | 9 |
| 2 | `MIDWAY01.STR` | 153072-154822 | 848 | 1548 | 218 | 176 |
| 3 | `SZINTRO1.STR` | 187024-190675 | 1554 | 3014 | 456 | 367 |
| 4 | `SZLOGO15.STR` | 196167-196989 | 3021 | 3350 | 102 | 81 |
| 5 | `OPEN.STR` | 164189-166989 | 4067 | 5187 | 349 | 279 |

- With the route, START at frame 3000 cuts `SZINTRO1.STR` short (3637 of its 9143 sectors read). Then `SZLOGO15.STR` plays, then the title menu. CROSS at frame 4000 (New Game) starts `OPEN.STR`, which ends at frame 5187. `TEMPLE.OVR` (id 140) is read at frames 5202 to 5206.
- The earlier boot-sequence notes (no input) list movies near frames 2500, 4000 and 5250 ("Boot sequence seen by an agent"). By the no-input trace those frames fall in `SZINTRO1.STR` (frames 1554 to 5082) for 2500 and 4000, and in `SZLOGO15.STR` (frames 5089 to 5418) for 5250. This is a match by frame number, not by comparing a screenshot with each file.
- Not claimed: that `SZLOGO15.STR` is a Sony logo (or any particular logo), or what the picture of each movie shows. Nothing in a trace says so.
- No movie file is read before `LEGAL.STR` (frame 372). The first reads are the disc volume sectors, `SYSTEM.CNF`, then the boot EXE.

User-session facts read from artifacts (not an agent route). Session `session-1792525023167056` (`tests\replays\local\`, frozen Release exe `b5573bbe...7856b`, vsync on is user-reported). Command: `tools\fmv_identify.py --telemetry tests\replays\local\session-1792525023167056`; output in `work\fmv\telemetry_table.txt`. The `cd_lba` column is one sample per VBlank, so LBA ranges are sampled, not every sector.

| Item | Value |
|------|-------|
| Play duration (`host_elapsed_us`, last row) | 399,627,599 us = 399.6 s = 6 min 39.6 s, 23,155 guest VBlanks |
| `LEGAL.STR` | host 3.4 to 4.2 s, 50.2 Hz mean |
| `MIDWAY01.STR` | host 11.5 to 24.8 s, VBlank 848 to 1548, 52.4 Hz mean, `cd_xa` set on 698 of 701 samples |
| `SZINTRO1.STR` | host 24.9 to 92.9 s, VBlank 1553 to 5082, 52.0 Hz mean, last LBA 195846 (file ends at 196166), so it played to the end |
| `SZLOGO15.STR` | host 93.0 to 99.8 s, VBlank 5089 to 5418, 48.2 Hz mean |
| `WIND.OVR` (id 142) read | host 133.1 s, VBlank 7406 to 7414. Cause not known (open question 242) |
| `OPEN.STR` | host 169.5 to 190.9 s, VBlank 9578 to 10698, 52.5 Hz mean |
| `TEMPLE.OVR` (id 140) read | host 191.1 to 191.2 s, VBlank 10713 to 10716 |
| `TEMPLE.LVL` / `TEMPLE.WAL` reads | host 199.0 to 316.1 s (level data is read during play) |
| Time from the `TEMPLE.OVR` read to the end of the recording | 399.6 s minus 191.1 s = about 208 s (upper bound for the first level; includes loading) |
| Incidents | The `incident` column is 0 in all 23,155 rows |

The vsync-off session `session-1792524829517909` (`build\saves\diagnostics\`, vsync off is user-reported, 94.2 s total, ends in the intro) shows the same files in the same order at 60.1 Hz (`LEGAL.STR`), 60.0 Hz (`MIDWAY01.STR`), 59.8 Hz (`SZINTRO1.STR`) and 60.0 Hz (`SZLOGO15.STR`). This fits the user's report of about 60 fps with vsync off and 48 to 54 fps with vsync on. Which session had vsync on or off is user-reported (open question 222).

Visible coverage run (a visible window, not headless, no warp, no boot route): `work\overlay_coverage\20261020_182310\summary.json` (tool `tools\overlay_coverage.py`). `warp` is null, the run log shows the OpenGL renderer (no `--headless`), and the game ended with `exit_origin sdl_window_close` in `psx_last_run_report.json` (the window was closed). The boot route was not used: the level index returns to 0 at frame 2547 and the TEMPLE level function is entered at frame 2469, before the route's first button press (frame 3000). Results: `TEMPLE` (id 140) is the only image reached, first seen at frame 3208 (t = 63.9 s); duration 113.0 s, last frame 5762; `faults` and `crash_like_log_lines` are empty. The artifacts do not say who held the pad. The run is attributed to the user. The basis is that its table (TEMPLE first at frame 3208, 17,989 static hits, 88 entries, 65 CRC misses) matches the table the user pasted in chat. Who held the pad is not in the artifacts.

### Per-movie table (28 `/MOVIES` STR files)

LBA and sector counts come from `docs/DISC_MAP.md`. Untested means no report exists. "Read" means the file was seen in a CD read trace (section above); that shows the disc read and MDEC activity, not that picture or audio are right. The picture and audio columns are user-reported only.

| File | LBA | Sectors | Picture | Audio | Status |
|------|-----|---------|---------|-------|--------|
| `BIOS.STR` | 426 | 5223 | Not reported | Not reported | Untested |
| `BRDGFL1.STR` | 5649 | 1615 | Not reported | Not reported | Untested |
| `CREDS01.STR` | 7264 | 27567 | Not reported | Not reported | Untested |
| `DROWN2.STR` | 34831 | 903 | Not reported | Not reported | Untested |
| `E2WTR.STR` | 35734 | 2775 | Not reported | Not reported | Untested |
| `FIREFL1.STR` | 38509 | 1055 | Not reported | Not reported | Untested |
| `FMV1.STR` | 39564 | 29079 | Not reported | Not reported | Untested |
| `FMV2.STR` | 68643 | 26087 | Not reported | Not reported | Untested |
| `FMV3A.STR` | 94730 | 9439 | Not reported | Not reported | Untested |
| `FMV3B.STR` | 104169 | 7287 | Not reported | Not reported | Untested |
| `FMV4AB.STR` | 111456 | 11223 | Not reported | Not reported | Untested |
| `FMV5.STR` | 122679 | 11647 | Not reported | Not reported | Untested |
| `FMV6.STR` | 134326 | 4919 | Not reported | Not reported | Untested |
| `FMV7AB.STR` | 139245 | 12327 | Not reported | Not reported | Untested |
| `LEGAL.STR` | 151572 | 1500 | Not reported | Not reported | Read (agent trace, user session). Picture and audio not reported. No XA audio |
| `MIDWAY01.STR` | 153072 | 1911 | See the table above | See the table above | Reached (user). File confirmed by LBA trace (agent frames 848 to 1548; user session host 11.5 to 24.8 s) |
| `MK4A.STR` | 154983 | 8359 | Not reported | Not reported | Untested |
| `NUFALL3.STR` | 163350 | 839 | Not reported | Not reported | Untested |
| `OPEN.STR` | 164189 | 3111 | Not reported | Not reported | Read after New Game (agent frames 4067 to 5187; user session host 169.5 to 190.9 s). Picture and audio not reported |
| `OUTTKES1.STR` | 167300 | 16671 | Not reported | Not reported | Untested |
| `PRSNFAL2.STR` | 183971 | 943 | Not reported | Not reported | Untested |
| `QUANDETH.STR` | 184914 | 911 | Not reported | Not reported | Untested |
| `ROCKDETH.STR` | 185825 | 1199 | Not reported | Not reported | Untested |
| `SZINTRO1.STR` | 187024 | 9143 | See the table above | See the table above | Reached (user). The intro by LBA trace and by order (agent frames 1554 to 5082 with no input; user session host 24.9 to 92.9 s). The user did not name the file |
| `SZLOGO15.STR` | 196167 | 1135 | Not reported | Not reported | Read after the intro (agent frames 5089 to 5418; user session host 93.0 to 99.8 s). Not identified as the Sony logo; what it shows is not known |
| `WND2E.STR` | 197302 | 2615 | Not reported | Not reported | Untested |
| `WTR2FR.STR` | 199917 | 2791 | Not reported | Not reported | Untested |
| `WTRDRN1.STR` | 202708 | 2287 | Not reported | Not reported | Untested |

- Count: 2 movies with a user report (`MIDWAY01.STR`, `SZINTRO1.STR`). 3 more were read in the traces but have no picture or audio report (`LEGAL.STR`, `SZLOGO15.STR`, `OPEN.STR`). 23 untested.
- The other STR files (for example `FMV1.STR`, `BIOS.STR`) were not read in any trace. The boot route stops at the first level.

### Why T2.10 was in-progress (before the D17 descope)

Accept line: "each movie reached has a row (picture OK?, audio OK?, glitches); unreached movies are marked untested; failures become `docs/OPEN_QUESTIONS.md` entries naming the exact movie."

Met:

- A row exists for each movie reached: `MIDWAY01.STR` and `SZINTRO1.STR` (user-reported), and `LEGAL.STR`, `SZLOGO15.STR`, `OPEN.STR` (read in traces).
- The other 23 movies are marked untested.
- The Midway and intro failures (stutter with vsync on) name exact files, `MIDWAY01.STR` and `SZINTRO1.STR`, by LBA trace (open questions 235 and 236 closed).

Not met:

- `LEGAL.STR`, `SZLOGO15.STR` and `OPEN.STR` were reached in the user's session, but the user gave no picture or audio report for them, so their "picture OK? audio OK?" cells are empty.
- Picture with vsync off was not reported for `MIDWAY01.STR` or `SZINTRO1.STR`. The digital glitch with vsync off is not known (237).
- The Midway "digital glitch" has no cause. The stutter is handled as a vsync setting (D9). No upstream code fix was made.
- Whether the Sony logo exists as a movie is not known (241). No movie file is read before `LEGAL.STR`.
- The 23 untested movies were not reached by anyone. Whether the user can reach them is not known (238).

Open items: `docs/OPEN_QUESTIONS.md` (148, 150, 162, 237, 238, 241). The user's descope on 2026-10-20 (D17) does not close them. Question 242 (`WIND.OVR`) also stays open.

### First fight (T2.11)

Accept line: "Patricio confirms the menu and a fight with responsive controls; play time and whether any crash occurred are recorded; the level name comes from the observed overlay id."

Status: done in `docs/TASKS.md`. Gate facts are user-reported, plus the telemetry facts below.

Met:

- The user reached the main menu, started a new game and played a fight with responsive controls (user report).
- No crash was reported (user report). The artifacts agree: the coverage run's `summary.json` has empty `faults` and `crash_like_log_lines`, and the session telemetry `incident` column is 0 in every row.
- Play time is recorded from the user's session telemetry: 399.6 s (6 min 39.6 s) in total, and about 208 s from the `TEMPLE.OVR` read to the end. The 208 s is an upper bound for the first level. It includes loading. It is read from the file, not stated by the user (see "User-session facts read from artifacts").
- The level is TEMPLE, from overlay id 140 in the user's session telemetry (inferred; the user did not say it in words). `TEMPLE.OVR` (id 140) is read in the user's recorded session (VBlank 10713). `TEMPLE` (id 140) is also the only image loaded in the visible coverage run (frame 3208). Agents saw the same id 140 in warp-free runs (T2.13, T2.16). Question 240.
- Screenshots and frame numbers for each boot stage were taken by an agent (table "Boot sequence seen by an agent" above).

Not met (recorded, not blocking the T2.11 status):

- The user has not said in their own words that the fight they played was in the TEMPLE level. The id is read from the disc-read trace and the coverage run, and it fits New Game followed by `OPEN.STR`. The length of the fight itself is also not separated from loading (open question 239 covers the session length only).
- Who held the pad in the coverage run is not in the artifacts (see above).
- The `WIND.OVR` read at VBlank 7406 in the user's session, before New Game, is unexplained. Its cause is not known (open question 242).

Open items: `docs/OPEN_QUESTIONS.md` (149, 240 and 242).

## FMV speed measurement (Release, hidden window)

This is an agent measurement under T2.10. It is not a user test. The runs used a hidden window, not the window the user plays in. The reviewer re-parsed the logs and gave a PASS. The user's visible-window test is still to do.

### System

| Item | Value |
|------|-------|
| CPU | Intel Core i5-7300HQ, 4 cores, 4 threads, 2.5 GHz |
| Machine | MSI laptop, model MS-16JD |
| Power | AC power. Windows "Balanced" power plan |
| GPU | Intel HD Graphics 630, driver 22.20.16.4708 (old). NVIDIA MX150 is also present |
| GL context | Created on the Intel HD 630 |
| Panel | 1920 x 1080 at 60 Hz |
| Audio | Realtek HD Audio. The default device sample rate was not captured |

### Method

- Exe: `build\MythologyKombat.exe`, Release. SHA-256 `66fdb5be60c2b023465cadeb1b6a79f889f2d8553f1709ca1535224590052af5`.
- Script: `tools\perf_run.ps1 -Name X [-Seconds 105] [-ExtraArgs ...] [-Env @{...}]`.
- The script starts the exe in `build\` with `--hidden-window --no-launcher --disc <cue> --game game.toml --memcard-dir work\perf_saves`.
- Every run sets `PSX_RUNTIME_PERF_DIAG=1`, `PSX_RUNTIME_PERF_DIAG_MS=1000` and `PSX_FPS_TELEMETRY=1`. Extra settings are in the run table.
- Logs go to `work\perf\run_X.log`, `work\perf\run_X.err.log` and `work\perf\run_X.meta.txt`. The meta file holds the exact arguments, the environment and the PID.
- The script kills only its own PID. It restores its environment variables in a `try/finally`.
- An earlier version of the script leaked `PSX_VSYNC=0` from run D into a later run E. Those results were discarded and the run was repeated.
- Summary: `tools\perf_summarize.py <names> [--series]`. It merges the runs. The FMV window is found from the data. It is the first 3 consecutive samples with guest work at or above 500 ms per second.

### Runs

| Run | Extra setting | Note |
|-----|---------------|------|
| A | None (cold default) | 100 s. Ends before the FMV |
| B | None (warm) | 100 s. Ends before the FMV |
| C | `--renderer software` | |
| D | `PSX_VSYNC=0` | |
| E | `PSXRECOMP_AUDIO_LEGACY=1` | 100 s. Ends before the FMV |
| F | `PSX_LOAD_DELAY=0` | |
| G | None, same as A | 260 s |

### Timeline of a run

- A boot burst comes first.
- Samples 2 to 11 are the boot, the Midway logo and the menu. The guest runs at about 60 Hz.
- The FMV phase starts at about sample 12. It is about 4690 guest frames, or about 78 s of guest time at 60 Hz.
- The FMV phase takes 92 s of wall time with vsync on, and 78 s with vsync off.
- After the FMV the guest is back at about 60 Hz.

### Results in the FMV phase

| Run | Setting | Guest Hz (min / median / max) | Underruns per s (median) | Other |
|-----|---------|-------------------------------|--------------------------|-------|
| A | Default | 47.2 / 50.9 / 54.9 | 6575 | Guest work about 652 ms/s. Pacer about 3 |
| B | Warm | 46.8 / 50.4 / 54.2 | about 6868 | |
| C | Software renderer | about 50.3 | not recorded | |
| D | `PSX_VSYNC=0` | 58.8 / 60.0 / 61.0 | 0 | Audio fill about 178 ms. Guest work about 775 ms/s. Pacer about 180 ms/s |
| E | Legacy audio | about 50.8 | about 25 | Audio fill 0 to 13 ms |
| F | `PSX_LOAD_DELAY=0` | about 40.0 | about 14,700 | Worse than the default. Do not use. The upstream claim that it helps is not borne out. Cause not known |

### Overlay counters

- In the FMV phase the native overlay count is 0.
- The interpreted overlay count is about 1100 dispatches a second, about 9k instructions a second.
- So the FMV decode runs in the exe's AOT code, not in interpreted overlays.
- Staging the overlay toolchain would not fix the FMV rate.

### Other observations

- Midway logo dip: the guest runs at about 50 to 54 Hz at samples 4 and 5 in every vsync-on run. Run B once fell to 18.7 Hz with 26,912 underruns. The dip lines up with overlay captures (+48 to +66) and GL uploads. It is absent with `PSX_VSYNC=0`.
- Run G at about sample 209: the guest fell to 23.6 Hz with 25,317 underruns. This is outside the FMV. Not explained.
- The log header shows the present mode:
  - Vsync-on runs print `present cadence: driver vsync (60.0 Hz panel; wall-clock cap 16.6639 ms/frame)`.
  - Run D prints `present cadence: wall-clock pacer (16.6639 ms/frame)`.

### Reading (supported, not proven for the visible window)

- With vsync on, the guest holds 60 Hz in light phases.
- In the FMV, a frame costs about 13 ms against a 16.66 ms budget. That leaves about 22% headroom.
- Some long frames miss a vblank and wait a full refresh. The average falls to about 50 Hz.
- Audio underruns follow from this. SPU and XA are produced on guest time. 37 kHz audio goes to a 44.1 kHz device. The underruns are a result, not the cause.
- The renderer, a cold cache and the audio bridge are not the cause.
- Per-frame guest cost is about 13 ms in both modes. That is about 650 ms/s work at 50 Hz, and about 775 ms/s at 60 Hz.

### Vsync settings in the code

- `psxrecomp\runtime\src\main.cpp`, near line 18612, reads `PSX_VSYNC` as an integer:
  - 1: vsync on. This is the default.
  - 0: immediate. The wall-clock pacer still runs, so tearing is possible. It is not uncapped.
  - -1: adaptive.
  - 2: VRR. The swap interval is 0. "Smooth motion" targets the panel maximum.
- The saved setting is `[video] vsync = "on"`, `"off"`, `"immediate"`, `"adaptive"` or `"vrr"` in `game.toml`. The code is in `psxrecomp\recompiler\src\config_loader.cpp`, lines 981 to 991. It is the per-game default.
- The player's `settings.toml` overrides `game.toml` (`main.cpp`, about line 18522). The launcher writes it. Where it is kept is not verified.
- The environment variable is for one run only (`main.cpp`, lines 1565 to 1568).
- `PSX_PRESENT_THREAD=1` and `PSX_RENDER_THREAD=1` are not tested.

### Caveats

- All runs used a hidden window. The user's visible windowed run (48 to 54 fps) is similar in size.
- These runs cannot separate the hidden-window effect from the vsync swap.
- The visible-window vsync-off run is pending.
- The movie file is not identified. The Release build prints no LBAs. The earlier guess of 7100 sectors and `FMV3B.STR` is withdrawn.
- To identify it, the debug build needs `fmv_state` or `cdrom_sector_history`.

### User and session results (T2.10, from T2.20)

- User-reported: with vsync off the audio was clean. With vsync on the audio was glitchy.
- Telemetry, measured by `tools\session_fps.py` on the T2.20 recording (exe SHA-256 `b5573bbe...7856b`, rows with `cd_xa` not 0): the vsync-off session averages 59.9 Hz and the vsync-on session averages 51.9 Hz.
- Which session had vsync on or off is user-reported. `session.json` does not record it (question 222). The movie is not identified (question 162).
- Details and the other session figures are in `docs/OPEN_QUESTIONS.md`, questions 220 to 224.

### Next steps

1. The user runs a visible-window test with vsync off. In PowerShell:

```
cd build
$env:PSX_VSYNC = '0'
.\MythologyKombat.exe --disc "<cue>" --game game.toml --no-launcher
```

   The user reports the fps, the audio and any tearing.
2. Then try `PSX_VSYNC=-1` (adaptive).
3. Done: the user approved, and `[video] vsync = "off"` is now in `game.toml` (D9). Check with `tools\perf_run.ps1 -Name X` (run it with `powershell -ExecutionPolicy Bypass -File`): the log must print `present cadence: wall-clock pacer`. The player's `build\settings.toml` overrides `game.toml`; it must also say `vsync = "off"`.
4. Later: PGO or LTO. Headroom is thin. Updating the Intel driver, or forcing the MX150, is untested.
5. Staging the overlay toolchain is low priority. It affects only the Midway logo dip and overlay interpretation.

Do not call the fix confirmed until the visible-window vsync-off run shows 60 Hz. See `docs/DECISIONS.md` (D9) and `docs/OPEN_QUESTIONS.md`.

## LBA-to-file lookup (T2.9)

The script `tools\lba_lookup.py` shows which disc file holds a given sector. Run it from the repo root:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\lba_lookup.py [--json] [--bcd] <LBA | 0xHEX | mm:ss:ff> ...
```

- It takes one or more sector values in one run.
- It reads `work\disc_files.json` from T1.1. If that file is missing, it exits with code 2 and points to `tools\disc_list.py`.
- It also reads `work\disc_classes.json` from T1.3, if that file exists. It uses the file to add format tags.
- It uses only the Python standard library.
- It does not change anything in `ps1_game\`.
- The usage line also lists `--json`.

### Input forms

| Form | Example | Meaning |
|------|---------|---------|
| LBA, decimal | `14942` | Sector number |
| LBA, hex | `0x17` | Sector number in hex |
| `mm:ss:ff` text | `03:21:17` | Decimal text. LBA = (mm × 60 + ss) × 75 + ff − 150 |
| `--bcd` fields | `--bcd 0x03:0x21:0x17` or `--bcd 46:45:26` | Raw BCD fields, as in a CdlLOC command |

- With `--bcd`, each field is one raw byte read as BCD. For example, `46:45:26` reads the bytes 0x46, 0x45 and 0x26.
- A bare `03:21:17` is decimal text, not BCD.
- A negative number such as `-5` is read as an LBA. It is out of range.
- Bad input exits with code 2 and prints the usage line.
- The valid range is LBA 0 to 228990. That is all 228991 sectors of track 1.

### Output

| Field | Meaning |
|-------|---------|
| File path | The disc path, for example `/MOVIES/CREDS01.STR` |
| Sector offset | The LBA minus the file's start LBA |
| Byte offset | Sector offset × 2048. This uses the ISO size |
| Tag | The format tag from `work\disc_classes.json`, if that file is present |

- For XA and STR files, the byte offset is a sector index. It is not a byte position in the data stream. The tool prints a note about this.
- LBAs that are not file sectors are reported as "no file" or as a structure:

| LBA | Reported as |
|-----|-------------|
| 0 to 15 | System area |
| 16, 17 | Volume descriptors |
| 18 to 21 | Path tables. LBA 20 is `path_table_M` |
| 22 | Directory extent of `/` |
| 425 | Directory extent of `/MOVIES` |
| 424, 163342 to 163349, 228841 to 228990 | Gaps. "No file" |

### Examples

| Input | Result |
|-------|--------|
| `0x17` | `/SLUS_004.76`, sector offset +0 (PS-X EXE) |
| `03:21:17` | LBA 14942, `/MOVIES/CREDS01.STR`, sector offset +7678 |
| `154982` | `/MOVIES/MIDWAY01.STR`, sector offset +1910 |
| `--bcd 46:45:26` | LBA 210251, `/OVERLAYS/BRIDGE.OVR`, sector offset +0. This is the BRIDGE CdlLOC value `46 45 26 00` from the EXE's table at `0x80012F28 + 135 × 4` |

### Checks on this disc

| Check | Result |
|-------|--------|
| LBAs checked | 1298. These are the first, last and neighbour sectors of all 211 files and 22 directories, the structure and gap edges, and 500 random LBAs |
| Mismatches against an independent ISO 9660 parse | 0 |
| Cross-check by the implementer | 10 files |
| Repeat run | Byte-identical (`cmp`) |
| Absolute paths in output | None |

- Every LBA from 0 to 228990 maps to a file, a structure or a gap. The tool found no unmapped LBA on this disc.
- The missing-JSON exit path was checked by reading the code. It was not run. See `docs/OPEN_QUESTIONS.md`, question 129.
- The tool output is not committed. `work\` is git-ignored.

## Static overlay facts (T2.12)

The script `tools\overlay_facts.py` reads the boot EXE and the eight `.OVR` files, and the two demo files. It checks the loader tables, the destination pointer, the call sites into the overlay window, and the read_file callers. Run it from the repo root:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\overlay_facts.py
```

- It takes about 2.5 s.
- It reads the boot EXE and the overlays from the disc `.bin`, through the ISO helpers. It does not read `work\extracted\`. So it does not need `tools\disc_classify.py` to run first.
- It writes `work\overlay_facts.json`. The `work\` folder is git-ignored.
- It is deterministic. Running it again gives the same output.
- The results are in `docs/EXE_OVERLAYS.md`, under "Static overlay facts (T2.12)". That page holds addresses, sizes and 16-hex hash prefixes only.
- The checks are static. They are strong consistency evidence, not proof. The runtime check is T2.13. See `docs/OPEN_QUESTIONS.md`, questions 130 to 139.

## Seeding symbols.toml (T2.21)

The script `tools\seed_symbols.py` fills `symbols.toml` from `work\symbols_sdk.json`. The script `tools\sync_symbols.py` then regenerates `psx_symbols.h`. Run both from the repo root.

### Seed step

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\seed_symbols.py [--sdk-json PATH] [--symbols PATH] [--include-suspects] [--dry-run]
```

| Option | Meaning |
|--------|---------|
| `--sdk-json PATH` | Input file. The default input is `work\symbols_sdk.json` from T1.6. A missing file gives a raw traceback (question 140) |
| `--symbols PATH` | Target `symbols.toml`. Test on copies, not on the real file |
| `--include-suspects` | Also add the 3 suspects, as `guessed`, with the note "probably false positive" |
| `--dry-run` | Dry run. Its exact effect is not recorded here (question 147) |

### Sync step

```
<RETRO_TOOLS_DIR>\python\python.exe tools\sync_symbols.py [--check]
```

- Do not pass `-I` to this script.
- It regenerates `psx_symbols.h`.
- `--check` verifies the files.

### Counts

| Item | Count |
|------|-------|
| Functions in `work\symbols_sdk.json` | 931 |
| Excluded `gte_macro` | 153 |
| Excluded `obj_label` | 335 |
| Kind `sdk` | 443 |
| Omitted loader-named `main` at `0x80020474` | 1 |
| Omitted loader-named `start` at `0x80090E70` (held by the hand-owned BootEntry) | 1 |
| Omitted suspects (default) | 3 |
| Seeded entries | 438 |
| Hand-owned BootEntry | 1 |
| `[[func]]` entries, default run | 439 |
| `[[func]]` entries, with `--include-suspects` | 442 |

- The 3 suspects are `SsUtReverbOn` at `0x80053AD0`, `SsUtReverbOff` at `0x8005E1B0` and `_SsSndPlay` at `0x8008387C`.
- Status counts recorded: 8 `confirmed` and 431 `guessed`. These add to 439, one more than the 438 seeded entries. See question 146.

### Status

| Name | Address | Status |
|------|---------|--------|
| VSync | `0x800945E4` | `confirmed` (see question 142) |
| ResetGraph | `0x8009C238` | `confirmed` |
| CdInit | `0x800952D8` | `confirmed` |
| memcpy | `0x8009F31C` | `confirmed`. Emitted as `sdk_memcpy` |
| printf | `0x8009F34C` | `confirmed`. Emitted as `sdk_printf` |
| RotTransPers | `0x8009A618` | `confirmed` |
| MemCardInit | `0x8009FF0C` | `confirmed` |
| SpuIsTransferCompleted | `0x80093D68` | `confirmed` |

- Confirmed means the name has recorded evidence in `docs/SYMBOLS.md`. All other seeded names are `guessed`.
- DrawSync (`0x8009C6F8`), StartPAD (`0x800A246C`), DecDCTReset (`0x80098C5C`) and InitPAD (`0x800A23D0`) stay `guessed`. They become `confirmed` only after their evidence is recorded in `docs/SYMBOLS.md` (question 144).

### Rules for the file

- Every entry has `emit = false`.
- Entries are keyed by address.
- All addresses lie in `[0x80010000, 0x800D8000)`.
- Each seeded block starts with a marker line, `# seed_symbols:<sha1>`. The hash is of the block body.
- If a block body no longer matches its hash, someone hand-edited it. The script keeps the block.
- Entries with no marker (BootEntry) are hand-owned. The script keeps their name and address reserved.
- The script is idempotent. A second run reports `unchanged`. `cmp` shows `symbols.toml` and `psx_symbols.h` are identical after the second run.

### Names that clash with C library names

`psx_symbols.h` emits `#define func_XXXXXXXX <name>` and `PSX_FN_<name>` for each entry.

| Rule | Result |
|------|--------|
| Name matches a hand-picked libc, POSIX or runtime list, or starts with `__` | Gets the prefix `sdk_`. The original name is kept in the note. 26 entries |
| Duplicate names | Get the address as a suffix |

- The 26 prefixed names are: memcpy, memmove, memchr, printf, sprintf, malloc, strlen, strcat, bzero, open, read, write, close, lseek, format, erase, setjmp, csin, csincos, catan, `__main`, `__divdi3`, `__udivdi3`, `__udivmoddi4`, and memset (2 entries).
- The suffixed duplicates are: `memclr_80094EAC`, `memclr_80094FD4`, `memclr_8009527C`, `sdk_memset_8009F2A0` and `sdk_memset_8009F32C`.
- The list of prefixed names is hand-picked. It is not exhaustive (question 141).

### Checks

| Check | Result |
|-------|--------|
| `psx_symbols.h` compiled with clang as C and as C++, with stdio, string, stdlib, math, setjmp, time, io, fcntl and windows.h, in both include orders | No clashes (reviewer) |
| Overlap with a broad libc list | `callback` at `0x80097268` and `timeout` at `0x8009928C`. Not in the risky list. Harmless unless a `func_XXXXXXXX` alias is used for them (question 145) |
| Generated C | 61 of 61 SHA-256 values match `work\generate_run1.sha256.txt`. Generate was not re-run |
| Include check | `psx_symbols.h` is not referenced by `codegen_setup.c`, `CMakeLists.txt` or `generated\` |

- `psx_symbols.h` must never be included from generated C.
- Other open items for T2.21 are in `docs/OPEN_QUESTIONS.md`, questions 140 to 147.
- The decision to commit these derived files is in `docs/DECISIONS.md` (D8).

## Boot-to-menu replay route (T2.18)

The script `tools\run_boot_route.py` boots the debug build, feeds it a fixed input route, and compares the result with an expected digest file. It is an automated regression check of the boot path. It is not the user's play test.

Run it from the repo root:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\run_boot_route.py [--runs N] [--expect tests\replays\expected\boot_to_menu.json | --record-expected <file>] [--route <json>] [--out <file>]
```

- It imports `Dbg`, `kill_pid` and `pid_is_ours` from `tools\smoke_boot.py`.
- `--runs N` repeats cold boots. It fills gaps in the checks.
- A non-deterministic run FAILS.

### Run rules

| Item | Value |
|------|-------|
| Exe | `work\build-dbg\MythologyKombat.exe` only. `build\` is not used (D7) |
| Mode | `--headless`, debug port 4381. The smoke test uses 4370 |
| Boot | Cold boot each run. `work\route_saves` is recreated each time |
| Environment | `PSX_DEBUG_FMV_QUIET=0` |
| Time | About 70 s per run. That is 5000 guest frames, at about 70 fps in the FMV |
| Process | Kills only its own child PID, read from `work\route\pid.txt`. Checks the port is free and that no stale PID is left |

### Route

The route file is `tests\replays\routes\boot_to_menu.json`. It holds button names and guest frame numbers only.

| Button | Guest frame | Hold |
|--------|-------------|------|
| START | 3000 | 4 frames |
| CROSS | 4000 | 4 frames |

- Route buttons use the inverted 16-bit pad word. 0 means pressed. The tool translates this.
- A route step is consumed once per vblank.
- The input route's `at_frame` is ignored if it is at or before the current frame. The tool connects at about frame 35 to 40. It checks `start_frame` in the reply.

### Checkpoints and digests

The checkpoints are guest frames 600, 1800, 3000, 3600, 3900, 4300 and 5000.

| Digest | Source |
|--------|--------|
| Fingerprint columns | The server's `frame_fingerprint` ring, keyed by frame number. Columns: `ws`, `wc` (main RAM writes), `mmio`, `mc` (MMIO writes), `sp`, `sc` (scratchpad), `qc` (queue) and `cyc` (guest cycle counter). The judge columns gate the result. `wr` and `pc` are locators. They only warn |
| RAM | SHA-256 of main RAM, 2 MB from `0x80000000` (`read_ram`) |
| VRAM | SHA-256 of the 1024 by 512 VRAM. It is read as 32 by 16 blocks of 128 by 128 (`vram_peek`) |

- RAM and VRAM are taken while paused with `host_pause`. The pause lands one frame early or late (question 172). The result records `ram_exact` for each checkpoint.
- RAM and VRAM are compared only where `ram_exact` is set in both the result and the expected file.
- The expected digests are tied to one exe build. A different exe SHA-256 only warns (question 173).

### Gates

| Gate | Pass rule |
|------|-----------|
| `route_sha256` | Matches the expected route |
| `dispatch_miss_total` | 0 |
| `segment_miss_total` | 0 |
| Checkpoint set | Same 7 checkpoints |
| Fingerprint judge columns | Match at every checkpoint |
| `exe_sha256` | Mismatch only warns |

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | MATCH |
| 1 | MISMATCH, a run failure, or a setup error (`SystemExit` with a string) |

- The docstring and README say a setup error exits 2. The code exits 1. See question 176.

### Results on this machine

| Check | Result |
|-------|--------|
| `--record-expected`, 3 cold boots | Bit-identical at all 7 checkpoints |
| `--runs 3 --expect` | MATCH, exit 0 |
| Reviewer, `--runs 1 --expect` | MATCH at 7 checkpoints, in 70.6 s. Frame 1800 was paused on frame 1801, so its RAM and VRAM hashes were skipped with a warning |
| Negative control, START at 3001 instead of 3000 | MISMATCH with 13 differences, exit 1. `wc`, `ws` and `mmio` differed at 3600, 3900, 4300 and 5000, and `route_sha256` differed. The RAM and VRAM hashes at those frames matched |

- A MATCH with `--runs 1` guarantees the fingerprint columns at all 7 checkpoints. RAM and VRAM are compared only at the exact checkpoints. The final line of the script does not yet say how many were compared (question 171).
- No RAM ranges needed excluding.
- The fingerprints were the sensitive digest in the negative control. The RAM and VRAM hashes did not change there.

### Boot sequence seen by an agent

These notes come from agent screenshots. They are evidence only. No user has checked them. The screenshots are not committed.

| Frame | What the agent saw |
|-------|--------------------|
| No input | Intro movies. A text screen with the 'mythology' definition, near frame 2500. A logo and candle movie, near 4000. A title movie, near 5250. The main menu between 5800 and 6700. Attract gameplay, near 6500 (seen once, question 175) |
| START at 3000 | The main menu, with START and OPTIONS and 'X - SELECT', is visible by 3600 |
| CROSS at 4000 | START is selected. The screen goes black, then a cutscene (a domed temple under a moon, near 4600). 'MISSION OBJECTIVE: STEAL THE SACRED MAP OF ELEMENTS - LOADING' shows by about 5500 |

### Committed files

Per D8 (`docs/DECISIONS.md`), routes and expected digests may be committed. Recordings, screenshots, saves, game pixels, game bytes and the BIOS may not.

| Path | Content |
|------|---------|
| `tools\run_boot_route.py` | The script |
| `tests\replays\README.md` | Folder note |
| `tests\replays\.gitignore` | Ignores `local\`, `*.png`, `*.jpg`, `*.bmp`, `*.wav`, save and memory card files, logs, `result*.json`, `shots\`, `scratch\` and `out\` |
| `tests\replays\routes\boot_to_menu.json` | The route |
| `tests\replays\expected\boot_to_menu.json` | Expected digests: frame numbers, counters, 64-bit hashes, and SHA-256 of RAM, VRAM, route and exe. No absolute paths and no timestamps |

- `work\` holds the run output. It is git-ignored.
- Open items are in `docs/OPEN_QUESTIONS.md`, questions 171 to 177.

## Runtime overlay proof (T2.13)

The script `tools\overlay_runtime_check.py` boots the debug build, watches one overlay load, and checks the copy against the disc. It is agent-run. The result is in `docs/EXE_OVERLAYS.md` ("Runtime proof (T2.13)").

Run it from the repo root:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\overlay_runtime_check.py [--runs N] [--shots <dir>] [--out <file>] [--route <json>]
```

| Option | Meaning |
|--------|---------|
| `--runs N` | Number of cold boots. Each boot is checked. The runs must agree |
| `--shots <dir>` | Folder for screenshots. Optional |
| `--out <file>` | Output file. The result is written to `work\overlay_runtime.json` by default |
| `--route <json>` | Input route. The committed route is `tests\replays\routes\boot_to_menu.json` |

- It uses the debug build, `work\build-dbg\MythologyKombat.exe`. See "Debug-tools build (for tests)" above.
- It starts the game headless on port 4383.
- It kills only its own child process, by its own PID. It does not kill by image name.
- One cold boot takes about 85 to 90 seconds.
- Exit code 0 means the proof holds, and the runs agree. The result is in the JSON file.
- The runs were made with `PSX_DEBUG_FMV_QUIET=0` set.
- The output is `work\overlay_runtime.json`. It is git-ignored. Do not commit it.
- The method is in `docs/DECISIONS.md` (D10). The native debug server has no `pc_break`, so the tool does not use one.
- The tool stops at the first overlay copy. It checks only TEMPLE-style loads. See `docs/EXE_OVERLAYS.md` ("Limits").

### Results on this machine

| Run | Result |
|-----|--------|
| Cold boot 1 | Proof holds. TEMPLE, id 140, at `0x80130FF8`. 0 differing bytes |
| Cold boot 2 | Same result as boot 1 |
| Reviewer re-run, 1 boot | Proof holds. 16 checks passed |

- The pause frame is 5210 or 5212, depending on the run. It is not part of the check.
- The screenshots are agent evidence. They are not committed.

### Files

| Path | Status |
|------|--------|
| `work\overlay_runtime.json` | Run output. Under `work\`, which is git-ignored. Not committed |

- Open items are in `docs/OPEN_QUESTIONS.md`, questions 178 to 183.
- `git status` shows `psxrecomp` as modified. This is the known CRLF noise (question 13). It is not from T2.13.

## AOT overlay profile (T2.15)

The file `aot\overlays.json` is the profile for the AOT static route (`docs/DECISIONS.md`, D11). It holds addresses, sizes, hashes and reason strings only. It has 258 lines and no absolute paths. It may be committed (D8). It is not a build. Nothing is linked from it yet (T2.16).

The schema is set by the upstream `psxrecomp\tools\aot_overlay_pipeline.py`. It differs from the T2.15 text in `docs/TASKS.md`. The choices are in `docs/DECISIONS.md` (D12).

### Regenerate the profile

Run from the repo root:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\make_overlay_profile.py
```

- It reads `work\overlay_facts.json`, the disc and the boot EXE.
- It asserts every hash against the disc.
- It has no `--out` option. It writes straight to `aot\overlays.json`.
- Two runs give byte-identical output.

### Check the profile

Run the upstream `extract` step from the repo root. Do not pass `--stage`.

```
$env:PYTHONUTF8 = '1'
work\py-psxrecomp\python.exe psxrecomp\tools\aot_overlay_pipeline.py extract --profile aot\overlays.json --game-toml game.toml --disc "ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue" --recompiler psxrecomp\recompiler\build\psxrecomp-game.exe --work-dir work\aot_extract\run1
```

- Use the private Python copy at `work\py-psxrecomp` (D5), without `-I`. The retro-tools `python.exe` fails on this tool with `No module named compile_overlays`.
- The run takes about 7 s. Output is written under `work\aot_extract\`.

### Profile contents

| Item | Value |
|------|-------|
| Schema | `psxrecomp AOT methods v1` |
| `game_id` | `SLUS-00476`. Same as `[game].id` in `game.toml` |
| `disc_hashes` | MD5 `8a75edba7855618f8f61338daef1be1d`, SHA-1 `bf5803d35aa7f55dc60bebbac645fc0d4e99c978` |
| `generic_exclude_files` | `OVERLAYS/BRDGDEMO.BIN`, `OVERLAYS/WINDDEMO.BIN` |
| Images | 8 |
| `expected_records` | 8 |
| `strict_bounds` | `true` |
| `static_output` | `generated/overlays_static.c` |

- Disc names have no leading slash, for example `OVERLAYS/BRIDGE.OVR`.
- The pipeline uses only `hashlib` algorithms. So CRC-32 and `known_sizes` are not used.

### Images and entries

Sizes and hashes equal the disc and `work\overlay_facts.json`.

| File | Size (bytes) | Loader entries (verified `jal` targets) | Excluded range (absolute) |
|------|--------------|------------------------------------------|---------------------------|
| `BRIDGE.OVR` | 23,164 | `0x801310C0` | `0x80130FF8` to `0x80131078` (32 words) |
| `EARTH.OVR` | 37,516 | `0x80133EF0`, `0x801342C4` | none |
| `FIRE.OVR` | 20,800 | `0x80131064` | `0x80130FF8` to `0x80131064` (27 words) |
| `FORTRESS.OVR` | 19,874 | `0x80133274`, `0x80133380`, `0x801333FC` | none |
| `PRISON.OVR` | 23,256 | `0x801316A4`, `0x80131DC0` | none |
| `TEMPLE.OVR` | 19,100 | `0x80130FF8`, `0x80132854` | none |
| `WATER.OVR` | 28,052 | `0x80131144`, `0x801313D8` | `0x80130FF8` to `0x80131144` (83 words) |
| `WIND.OVR` | 46,888 | `0x80131190` | `0x80130FF8` to `0x80131190` (102 words) |

- The entries are the `jal` targets of the level functions that the static check found (`docs/EXE_OVERLAYS.md`, T2.12). Whether each is a real function start is for the T2.16 audit.
- `FIRE`, `WATER` and `WIND` each hold one zero word in their table. So not every word in those excluded ranges is an address. `BRIDGE`'s words are all addresses.
- `FIRE` and `WIND` entries land on a `lui`, not on a stack prologue.
- The fixed extents use the file name, offset 0, base 0, address 0, the file size, the SHA-256 and `load_addr` `0x80130FF8`. `allow_missing` is `true`.

### Checks in the profile

| Check | Where |
|-------|-------|
| Pointer word | EXE `0x80015134` must equal `0x80130FF8` |
| CdlLOC words, ids 134 to 143 | `0x80013140` to `0x80013164` |
| Size-table words | `0x8001347C` to `0x800134A0` |
| Adjacent files | `BRDGDEMO.BIN` then `BRIDGE.OVR` |

### Negative tests

Each change was made to a copy under `work\aot_neg\` or `work\review\`. The profile was not changed.

| Change | Exit | Message or result |
|--------|------|-------------------|
| `expected_records` 9 | 1 | `Expected 9 recipes, got 8` |
| `expected_records` 7 | 1 | Fails |
| One image removed | 1 | `Expected 8 recipes, got 7` |
| One image removed and `expected_records` 7 | 0 | Passes |
| Ninth image added | 1 | `Duplicate configured source` |
| Corrupt extent SHA-256 | 1 | `Extent bytes changed` |
| Corrupt disc MD5 | 3 | `not applicable` |
| Corrupt excluded-range SHA-256 | 1 | Fails |
| Wrong pointer word | 1 | Fails |
| Wrong CdlLOC word | 1 | Fails |
| `strict_bounds` false, with excluded ranges | 1 | Fails |
| Adjacent files `BRIDGE` to `EARTH` | 1 | Fails |
| Entry placed inside an excluded table | 1 | `Excluded required loader entry` |
| Entries removed | 0 | Allowed by design |
| `EARTH` `load_addr` changed to `0x80131000` | 0 | Passes. Nothing ties `load_addr` to the pointer word (question 184) |

- Two extract runs gave 8 `runtime-inputs\*.json` files that are byte-identical.
- The inventory shows `recipe_count` 8, 8 required images, and `full_static_coverage_proven` false.
- The profile SHA-256 starts `06bf55548f8fd343`. The original disc SHA-256 starts `71d0e9785d7326e1`.

### Limits

- The schema cannot express this game's loader tables. The `bcd_extent_table` check reads 8-byte entries. This game has a 4-byte location table at `0x80012F28` and a separate size table at `0x80013264`. So the words checks replace it. Their agreement with the ISO extents is shown by `tools\overlay_facts.py`, not by the pipeline (question 185).
- `adjacent_files` needs non-last sizes to be multiples of 2048. The `.OVR` sizes are not. So only `BRDGDEMO` to `BRIDGE` can be checked (question 186).
- `load_addr` is pinned only by the pointer-word check, and by the entries and excluded ranges (question 184).
- Only TEMPLE is runtime-proven (T2.13). The other seven are pending T2.17 (question 178).
- Entry validity waits for the T2.16 audit (question 187).
- The `--cps` value must match the runtime build. It was not checked (question 188).
- The 16-byte overwrite at `0x80130FFC` is unchanged by this profile (question 180).

## Static overlay build (T2.16)

This step builds the static overlay code from the disc bytes. It writes generated C for the eight overlay images, and links that C into the game exe. It reads the disc only. It does not change anything in `ps1_game\`. The profile is `aot\overlays.json` (T2.15). The design is in `docs/DECISIONS.md` (D11 and D13). The results are in `docs/EXE_OVERLAYS.md` ("Static overlay build (T2.16)").

### CMake change

The root `CMakeLists.txt` gets 6 new lines. The new keyword must sit right after `GEN_MARKER` and before `GEN_FULL_GLOB`:

```
GAME_OVERLAY_STATIC_C "${CMAKE_CURRENT_SOURCE_DIR}/generated/overlays_static.c"
```

- `psxrecomp_add_game_runtime` takes several values after `GEN_FULL_GLOB`, `CODEGEN_SETUP_SOURCES` and `EXCLUDE_BUILTIN_MODS`. A keyword written after one of them is read as a value of that list.
- The first attempt put the keyword after `CODEGEN_SETUP_SOURCES`. The link then failed with undefined `psxrecomp_codegen_host_apply`, `psxrecomp_codegen_relaunch_or_exit` and `psxrecomp_forward_if_built`.
- `psxrecomp\runtime\overlay_static_sources.cmake` checks the two names. If `static_output` in `aot\overlays.json` and the keyword name point at different files, it stops with a FATAL_ERROR. If the file is absent while a game links, it prints a warning.

### Generate

Run the same command as T2.3, from the repo root:

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_psxrecomp.ps1 generate --config game.toml --project-root . --disc "ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue"
```

- The static step runs inside `generate`. For `generate`, the wrapper uses the private Python copy `work\py-psxrecomp` (D13).
- With the unmodified embeddable Python, the static step failed with `ModuleNotFoundError: compile_overlays`. The error is at line 21 of `psxrecomp\tools\aot_overlay_pipeline.py`. The subprocess does not get `psxrecomp\tools` on `sys.path`.
- The CLI adds `--cps` and `--reuse` itself, and runs with `--workers 2`. `--cps` was detected from `psx_cps_mark_game` in `generated\SLUS_004.76_dispatch.c`.
- The static step found 5551 distinct entry addresses. Up to 5 variants share one address.

| Run | Kind | Result |
|-----|------|--------|
| 1 | First static build | `Verified 8 images / 8 recipes`. `Published 8014 audited static variants in 9 files`. 30.6 s |
| 2 | Plain rerun | `Reused 8014 audited static variants in 9 files: every generation input is unchanged (2748b13f56f3f09c)`. 11.6 to 11.9 s |
| 3 | Full rebuild with `--force-aot-static` | `RESULT_STATIC=built`. The shard files are identical to run 1 |

### Output

All files are in `generated\`, which is git-ignored (`.gitignore` line 4). None may be committed.

| File | Content |
|------|---------|
| `overlays_static.c` | Dispatcher. `PsxOvVariant` holds `{ranges, count, crc, fn}`. The table is `psx_ov_variants[8014]` |
| `overlays_static_0000.c` to `overlays_static_0007.c` | Static code from the disc bytes. Derived from game data |
| `AOT_STATIC_AUDIT.json` (1.07 MB) | Audit. See the fields in `docs/EXE_OVERLAYS.md` |

- The `generated\` baseline is now 70 shard files: the 61 from T2.3 plus the 9 static files. The new listing is `work\generate_run4_static.sha256.txt`.
- The T2.3 listing, `work\generate_run1.sha256.txt`, still matches the 61 original files.
- The audit file is not byte-reproducible. Its `recipe_input_sha256` changes on each run that does not reuse. Compare the shard hashes and `generation_inputs_sha256` instead.

### Builds

Run these from the repo root. Set the toolchain first, as in T2.4.

```
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSXRECOMP_REQUIRE_GAME_C=ON
cmake --build build --target psx-runtime
cmake -S . -B work\build-dbg -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSX_DEBUG_TOOLS=ON -DPSXRECOMP_REQUIRE_GAME_C=ON
cmake --build work\build-dbg --target psx-runtime
```

| Exe | Size (bytes) | SHA-256 | Note |
|-----|--------------|---------|------|
| `build\MythologyKombat.exe` (Release) | 51,699,712 | `7c86bcbc...b577` at build time | Was 46,905,344 bytes at T2.4. See the note below |
| `work\build-dbg\MythologyKombat.exe` (debug) | 35,465,728 | `23e09f8514a642e6f2c975bd359d700d663432a2db40fa8c723c8350a35220b1` | Debug tools on |

- Neither configure nor build printed a `GAME_OVERLAY_STATIC_C` mismatch or absent warning.
- The `overlays_static` objects take about 1 minute to compile. A relink takes about 2.5 s.
- The Release SHA-256 changes on every relink. A reviewer's no-op rebuild gave `4c3cca88...`, at the same size. Record the SHA of the exe you test. The SHA-256 values in the T2.4 and T2.6 sections belong to the older 46,905,344-byte exe.
- The Release exe has no debug server. Its link was checked with a byte search (`grep -a`). The strings `psx_overlay_static_code_matches` and `overlay_static_entries` are in both exes.

### Runtime checks

| Check | Result |
|-------|--------|
| `tools\overlay_runtime_check.py --runs 1` on the new build | PROOF HOLDS, TEMPLE (see `docs/EXE_OVERLAYS.md`) |
| `tools\overlay_static_probe.py` (new) | Debug build, headless, port 4384. Options used: `--out work\overlay_static_probe.json`, `--route`, `--frames 5000,5400,6000`, `--port 4384`, and `--shots` under `work\`. See the results in `docs/EXE_OVERLAYS.md` |
| `tools\run_boot_route.py --expect` with `tests\replays\expected\boot_to_menu.json` | MATCH, 7 checkpoints. The only warning is the exe SHA-256 one |

- The probe exits 0 only when `range_hits` is 0 at the first query and above 0 at the last query.
- The `exe_sha256` in `tests\replays\expected\boot_to_menu.json` was stale at this point. It was re-recorded at T3.2 (below). See `docs/OPEN_QUESTIONS.md` (173).
- Coverage is not proven. The audit field `full_static_coverage_proven` is false.
- The static dispatcher handles only KSEG0 PCs. See `docs/OPEN_QUESTIONS.md` (190).

### Git status

- `psxrecomp` still shows ` m` because of CRLF noise (`docs/OPEN_QUESTIONS.md`, question 13). Do not commit inside the submodule.

## Hand-owned symbols and seeding rules (T2.22)

Task T2.22 adds names for the overlay loader and the level functions. It also marks one seeded entry as hand-owned. The names are listed in `docs\SYMBOLS.md` ("Overlay loader and level-function names (T2.22)"). This step changes only `symbols.toml` and `psx_symbols.h`.

### What changed

| File | Change |
|------|--------|
| `symbols.toml` | 14 entries added as hand-owned. `sdk_memcpy` at `0x8009F31C` edited to hand-owned |
| `psx_symbols.h` | Regenerated by `tools\sync_symbols.py` |

- Every new entry has `emit = false`.
- The 14 new entries are 5 loader names (`get_size`, `read_file`, `scratch_alloc`, `load_arena_record`, `read_file_alloc`) and 9 level functions (`level_load_TEMPLE` and 8 others, including `level_load_FIRE_alt`).
- `sdk_memcpy` keeps its PsyQ name `memcpy` in the note.

### Rules for seeding

- A seeded block starts with a marker line, `# seed_symbols:<sha1>`.
- Removing the marker makes the block hand-owned. `tools\seed_symbols.py` then never overwrites it.
- A hand-owned entry keeps its name and address. The script does not touch it.
- A block whose body no longer matches its hash is also kept (see "Seeding symbols.toml (T2.21)").
- Two runs of `tools\seed_symbols.py` were recorded. Both reported `unchanged`.

### Counts

| Item | Count |
|------|-------|
| Hand-owned entries, incl. BootEntry | 16 |
| Seeded entries | 437 |
| Functions in `psx_symbols.h` | 453 |
| Status `confirmed` | 10 |
| Status `guessed` | 443 |

### Checks

| Check | Result |
|-------|--------|
| `generated\` after this step | Unchanged. `sha256sum -c work\generate_run4_static.sha256.txt` passes for every file except `AOT_STATIC_AUDIT.json`, which is not byte-reproducible (T2.16) |
| `psx_symbols.h` compile | Compiled clean with clang as C and as C++ (reviewer), with `stdio.h`, `string.h`, `stdlib.h` and `windows.h` in both orders |
| Include of `psx_symbols.h` | No file in the repo includes it yet |

- The names `get_size`, `read_file` and `scratch_alloc` have no prefix. Their `func_XXXXXXXX` aliases could clash with a future host file. See `docs/OPEN_QUESTIONS.md` (question 197).
- The `confirmed` status of `read_file` and `level_load_TEMPLE` rests on the T2.13 observation. See `docs/SYMBOLS.md`.

## Playtest diagnostics recorder (T2.19)

Task T2.19 adds a recorder for playtests. It writes the inputs and a per-frame RAM digest to a session folder. It also adds an input display. Both come from the upstream `psxrecomp\runtime\playtest_diagnostics.cmake` helper, through a package in this repo. The package is config only. It holds no game data.

### What changed

| File | Change |
|------|--------|
| `CMakeLists.txt` | 11 lines added. It includes `psxrecomp\runtime\playtest_diagnostics.cmake` and calls `psxrecomp_add_playtest_diagnostics` with game id `SLUS-00476` and mod id `mythologykombat.diagnostics`. The call sits after `psxrecomp_add_game_runtime` and before the manifest workaround (D6) |
| `mods\preloaded\packages\mythologykombat.diagnostics\1.0.0\manifest.toml` | New package. Format version 5. Target game `SLUS-00476`. Two features, `recording` and `osd`. Two plugins, `mythologykombat.diagnostics` and `mythologykombat.diagnostics.osd`. No channel is set, so it is a developer package |

- In the source file, both features are `default_enabled = false`.
- The package must be in `mods\preloaded\packages\`. The defaults step fails if it is not.

### Default by build

The upstream defaults script, `psx_playtest_diagnostics_defaults.cmake`, runs after the build. It edits the staged copy of the manifest, not the source.

| Build | Recording and input display | Evidence |
|-------|-----------------------------|----------|
| Non-public (the default, `PSX_PUBLIC_RELEASE` OFF) | On. The staged `default_enabled` is set to true | `build\mods\bundled` and `work\build-dbg\mods\bundled` show true at lines 21 and 28. Build log line: `psx-runtime non-public build; mythologykombat.diagnostics recording/osd default on` |
| Public (`-DPSX_PUBLIC_RELEASE=ON`) | Off. The build fails unless the source says false | Not run. Read from the script. The option is in `psxrecomp\runtime\runtime.cmake` (line 129), default OFF |

- `PSX_PUBLIC_RELEASE` is OFF in the CMake cache of both build folders. The repo never sets it.
- Build log line: `staged mod catalog OK: 7 package(s) = 1 game-owned + 6 framework-owned, all under mods/bundled, no mods/packages`.
- `replay-diagnostics.py` is staged beside both exes.

### Where sessions go

| Build | Session folder |
|-------|----------------|
| `build\MythologyKombat.exe` | `build\saves\diagnostics\session-<timestamp>\` |
| `work\build-dbg\MythologyKombat.exe` | `work\build-dbg\saves\diagnostics\session-<timestamp>\` |
| Fallback | `%TEMP%\psxrecomp-diagnostics\SLUS-00476\session-<timestamp>\` |

- `build\saves\` and `work\build-dbg\saves\` are git-ignored.
- `work\build-dbg\diagnostics-location.txt` holds the path of the latest session.
- The condition for the fallback is not recorded here. See `docs/OPEN_QUESTIONS.md` (question 205).

### Files in a session

| File | Content |
|------|---------|
| `inputs.csv` | One row per sample. See the format below |
| `session.json` | Session record. Field names are not described here |
| `telemetry.csv` | Telemetry. Columns are not described here |
| `mods-state.toml` | Mod state for the session |
| `card1.mcd`, `card2.mcd` | Copies of the starting memory cards |

**Privacy:** the cards are copies of the starting saves, and the inputs are traced. Never share or commit a session folder. The upstream doc says to zip the complete session folder, and that zip includes the cards. See `docs/OPEN_QUESTIONS.md` (question 204). `*.mcd` and `/saves/` are git-ignored.

### inputs.csv format

- Four comment lines come first:
  - `# psxrecomp-input-v2`
  - `# execution <hash>`
  - `# plan <hash>`
  - `# build SLUS-00476/0.1.0+01068a3-dirty/psxrecomp-nightly-805-g449c31e5-dirty/sha256-<exe sha>`
- There is no column-name header.
- Each data row has 16 fields. The column constants are in `playtest_diagnostics.cpp`.

| Field | Meaning |
|-------|---------|
| 1 | Sample number `N` and sequence number `seq`, separated by a space |
| 2 | Pad 0 buttons |
| 3 | Pad 1 buttons |
| 4 | Pad 0 block, first field. Meaning not stated |
| 5 to 8 | Pad 0, four stick bytes |
| 9 | Pad 1 block, first field. Meaning not stated |
| 10 to 13 | Pad 1, four stick bytes |
| 14 | RAM digest for the sample |
| 15 | Pad 0 connected (1 or 0) |
| 16 | Pad 1 connected (1 or 0) |

- Idle sample: `N 0,65535,65535,0,128,128,128,128,0,128,128,128,128,2136692531,1,0`. Pad 0 is connected and pad 1 is not.
- See `docs/OPEN_QUESTIONS.md` (question 203) for fields 4 and 9.

### Turning it on or off

- Recording and the input display are on by default in every non-public build.
- In the launcher, open the Mods list. The group is `Diagnostics`, with `Playtest Recording` and `Input Display`.
- Player choices in `mods\state.toml` override the default.
- Recording starts at the first guest VBlank.
- Quit the game normally. The writer drains its data on a normal quit. See `docs/OPEN_QUESTIONS.md` (question 206).
- Pressing L3 and R3 together marks an incident in the recording.

### Analyze a session

The analyzer needs no game launch.

```
<RETRO_TOOLS_DIR>\python\python.exe build\replay-diagnostics.py <session-dir> --analyze
```

| Run | Samples | Sequence discontinuities |
|-----|---------|--------------------------|
| Headless smoke run, 25 s | 2007 | 0 |
| Reviewer run, 15 s | 1406 | 0 |

### Replay (T2.20, not run)

```
<RETRO_TOOLS_DIR>\python\python.exe build\replay-diagnostics.py <session-dir> --exe <original exe> --disc "ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue" --game game.toml --output <NEW private dir>
```

- `--input-only` is for dev builds only.
- Strict replay needs the same exe binary. The build id embeds the exe SHA-256, and it ends in `-dirty`. The game repo and the psxrecomp submodule are both dirty (question 13).
- Record with the exe that T2.20 will replay. Do not relink or rebuild between recording and replay.
- A recording made with the debug exe cannot be replayed on the Release exe.

| Exe | SHA-256 (changes on every relink) |
|-----|-----------------------------------|
| `build\MythologyKombat.exe` (Release) | `3e7de066840cd99c9f3ec26ef5b76734f22e917c7d3e8944f664ee65c24b1460` |
| `work\build-dbg\MythologyKombat.exe` (debug) | `49fb311adbf2b75e1a23a73634b5ad4fa39aae0ca0be089f221433b8dd5d3fc7` |

### Checks in T2.19

| Check | Result |
|-------|--------|
| `tools\smoke_boot.py --exe work\build-dbg\MythologyKombat.exe --port 4385 --seconds 25` | PASS. Frames 1 to 2006 |
| Reviewer 15 s run | PASS. Frames 23 to 1406 |
| Session folder from the smoke run | `inputs.csv`, `session.json`, `telemetry.csv`, `mods-state.toml`, `card1.mcd`, `card2.mcd` present |
| `replay-diagnostics.py --analyze` | See the table above |

### Not run

- Strict replay (T2.20).
- A `PSX_PUBLIC_RELEASE=ON` configure. The public-build result is read from the script only.
- The reviewer's CMake no-op rebuild check.
- The on-screen input display was not checked on screen (question 212).

## Seed growth from dispatch misses (T2.8)

This step adds function starts to the seed file, `seeds\ghidra_funcs.txt`. Each new start comes from a runtime dispatch miss. Each candidate is vetted before it is added.

Status: the main part passed review. The manual follow-up (batch T2.8-2, the `--manual` option and the rebuild) was checked by the implementer only. No reviewer has checked it. See `docs/OPEN_QUESTIONS.md` (213) and `docs/DECISIONS.md` (D15).

### Routes and collection

The runs used the debug build, `work\build-dbg\MythologyKombat.exe`, headless on port 4386, with its own PID.

| Route | Frames | Result |
|-------|--------|--------|
| Boot route | to frame 5016 | 1 miss address, `0x80032760` (4604 hits) |
| `work\t28\route_temple.json` | to about 11231 | 2 miss addresses (below) |

The longer route is the boot route, then button mashing every 17 frames from frame 6200 to 11000. The TEMPLE load is at about frame 5200. The first fight is at about frame 6000.

| Address | Hits | Instructions | Overlay window |
|---------|------|--------------|----------------|
| `0x80032760` | 10825 | 108250 | No |
| `0x8003A674` | 286 | 858 | No |

- Both are interpreter entries from dirty RAM.
- On the same run, the dispatch counts were: static hits 5,128,302, miss total 0, segment miss total 0. So the static dispatch saw no misses.

Collection command:

```
collect_game_misses.py --game-toml game.toml 0x80010000 0x800D8000
```

The report does not say which folder this script is in. See `docs/OPEN_QUESTIONS.md` (218).

### Vetting

Command, run from the repo root:

```
work\py-psxrecomp\python.exe psxrecomp\tools\vet_seeds.py --game game.toml work\dirty_ram_misses.txt
```

| Address | Vet result | Reason |
|---------|------------|--------|
| `0x8003A674` | ACCEPT | A function boundary and a stack prologue at instruction 3. The analyzer start was `0x8003A680`, 12 bytes later. The seed sits after a `jr ra` and its delay-slot nop. No static references. |
| `0x80032760` | WARN | "frameless; manual Ghidra check required". Seven instructions come before the stack prologue at `0x80032788`. That is past the 4-instruction window of `vet_seeds`. No `jal`, `j` or branch targets it. It is reached through a function pointer. |
| Any | REJECT | None |

### Growth tool

`tools\grow_seeds.py` is new. It uses only the standard library, so run it with `python -I`.

1. It runs `vet_seeds` as a child process.
2. It reads the ACCEPT, WARN and REJECT lines.
3. It appends only ACCEPT addresses. Each one must be word-aligned, inside the EXE text range from the PS-X EXE header, and not already in the file.
4. It writes one comment line per batch, `# batch ID: source ...`.
5. It keeps the CRLF line endings. It never edits an existing line.

| Option | Meaning |
|--------|---------|
| `--dry-run` | Shows what would change. Changes nothing |
| `--manual ADDR` | Adds an address that vet did not accept. Repeatable. Skips vet. Alignment, range and duplicate checks still apply |
| `--reason TEXT` | Text for the manual comment line, `# manual ID: TEXT` |

- With `--manual`, the miss file is optional, because vet is skipped.
- The summary line counts manual addresses under "ACCEPT". This is cosmetic. See `docs/OPEN_QUESTIONS.md` (217).

### Seed batches

| Batch | Change | Seed count | Seed file | SHA-256 |
|-------|--------|------------|-----------|---------|
| T2.8-1 | `0x8003A674` added (vet ACCEPT) | 1175 to 1176 | | `058637987b613a62...e038` (abbreviated in the report) |
| T2.8-2 | `0x80032760` added (manual) | 1176 to 1177 | 1182 lines | `114bb1056a45aa8486c062e5432a4903c88185cee04ae5fa4b45ed1fd96cd351` |

- The comment for batch T2.8-2 records the WARN, the two independent disassemblies, the 10825 runtime dispatch misses, and that the address is a pre-prologue entry of analyzer function `func_80032788`.
- The manual seed follows D15 (`docs/DECISIONS.md`).

### Regeneration

After batch 1 (`work\t28` run 10 listing: `work\generate_run10_seed_t28.sha256.txt`):

- 1 of 58 shards updated. The dispatch table has 2891 entries. The static route was reused.
- Files changed against the run 4 baseline: `SLUS_004.76_decls.h`, `SLUS_004.76_dispatch.c`, `SLUS_004.76_full.ranges` and `SLUS_004.76_full_11.c`.
- `AOT_STATIC_AUDIT.json` also changed. It is not reproducible. See `docs/OPEN_QUESTIONS.md` (195).

After batch 2 (log `work\t28\generate2.txt`):

- It loaded 1177 extra function addresses (0 interior, 0 hosted-interior).
- The forced entry `0x80032760` was added.
- 1 of 58 shards updated. No overlap, interior or duplicate warnings.
- `func_80032760` is its own function in `SLUS_004.76_full_09.c`. It ends with a fall-through call to `func_80032788`.
- Exactly four files changed against run 10: `decls.h`, `dispatch.c`, `full.ranges` and `full_09.c`. The audit JSON did not change.
- The new baseline listing is `work\generate_run11_seed_t28b.sha256.txt` (71 entries). This is the current baseline.

### Builds

Both builds were made with nobody running the game.

| Exe | Size | SHA-256 |
|-----|------|---------|
| `build\MythologyKombat.exe` (Release, FINAL) | 51,759,616 bytes | `b5573bbe586f7669f3dfad11d3ca3a6f8888f8e37eb47eccdffbb8f201a7856b` |
| `work\build-dbg\MythologyKombat.exe` (debug, FINAL) | 35,525,632 bytes | `e9936464c03f6b78c697b1cf2642cbbf4597b7832b5838d0256c8af98891e01e` |

- The Release hash replaces the T2.4 hash `66fdb5...` as the current shipping exe.
- Any further relink changes the Release hash. Record the hash of the exe the user will record on. See D15.

### Checks

| Check | Result |
|-------|--------|
| `run_boot_route --expect boot_to_menu` | MATCH, 7 checkpoints. All judge columns match. Warnings only: locator (wr/pc) at frames 4300 and 5000, because code layout changed; and a stale `exe_sha256`. The expected file was not re-recorded (question 173) |
| Re-collection on the TEMPLE route, frame about 11212 | No new addresses. Miss total 0. Segment miss total 0 |
| `overlay_static_probe` | Static hits went from 0 to 2865 |
| `overlay_runtime_check` | PROOF HOLDS |
| `tools\check_seeds.py`, full run | 1177 seeds. 0 duplicates. 0 invalid. The analyzer starts a function at every seed, with `in_no_analyzer_function` 0 and `inside_other` 0. Analyzer functions 2322 (was 2320). 108 seeds are analyzer-only starts, equal to the not-Ghidra-start count (108) |

### Coverage caveat

- Coverage is one TEMPLE fight with mashed buttons.
- Other levels, characters, menus and FMVs were not run.
- More seeds may appear with user play. See `docs/OPEN_QUESTIONS.md` (215).

### Tool notes

- `psxrecomp-analyze.exe` was missing from `psxrecomp\recompiler\build` at one point. The command `cmake --build psxrecomp/recompiler/build --target psxrecomp-analyze` rebuilt it. The cause of the disappearance is not known (question 216).
- `psxrecomp.exe` and `psxrecomp-toml.exe` are also absent here. The T0.5 section says the recompiler build makes them.
- `psxrecomp` shows ` m` in git status. This is the old CRLF noise (question 13). Do not commit inside the submodule.

## Overlay coverage session (T2.17)

Task T2.17 needs you to play into each level. The agent side is `tools\overlay_coverage.py` (launcher: `tools\run_overlay_coverage.ps1`). It starts the **debug build** (`work\build-dbg\MythologyKombat.exe`) in a normal visible window and watches it while you play. It reads the disc image and the debug server only. It changes nothing in `ps1_game\`. Output goes to `work\overlay_coverage\<timestamp>\` (git-ignored, never committed).

### Commands

Open PowerShell in `<REPO_ROOT>` and run one of these.

```
# You play from the logos on. Close the game window (or press Ctrl+C here) when you are done.
powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_overlay_coverage.ps1

# The tool presses START and selects New Game for you, so you take over in the first level (TEMPLE).
powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_overlay_coverage.ps1 -BootRoute

# All options
powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_overlay_coverage.ps1 --help
```

The same without the launcher: `<RETRO_TOOLS_DIR>\python\python.exe -I tools\overlay_coverage.py [options]`.

Useful options: `--interval 3` (seconds between polls), `--fresh-saves` (start with an empty memory card; by default the card in `work\overlay_coverage_saves` is kept between sessions, so you can save in a level and continue later), `--max-seconds N` (stop by itself), `--quiet`.

Only one copy may run at a time (debug port 4385). If the tool says the port is in use, close the other game window first.

### What you will see

- A line such as `NEW OVERLAY 140 TEMPLE resident` each time a different level file is loaded, with the guest frame.
- A line such as `level function entered: FIRE2` when the game calls one of the nine level-load functions.
- A short status line every 30 seconds.
- When you close the window or press Ctrl+C, a table with one row per overlay id: reached or not, first frame, static hits, distinct static entries hit, interpreter fallbacks, `segment_alias_interp` and CRC misses. Under it: which level functions were entered, and any fault (non-zero exit code, `psx_crash.txt`, crash-like lines of the game log).
- Files in the output folder: `coverage.jsonl` (one JSON line per poll), `summary.json`, `summary.txt`, `run.log` (the game's output) and a copy of `psx_last_run_report.json`.

### What to play

Reach as many of these as you can, in any order, and say which you could not reach: TEMPLE (id 140), EARTH (136), WIND (142), WATER (141), PRISON (139), FIRE (137, two level functions), BRIDGE (135), FORTRESS (138). In each level, fight or walk for a minute so the code runs. Tell the agent about anything you see that the tool cannot see: wrong graphics, a freeze, missing sound, a crash. The tool counts a crash only if the process dies or writes `psx_crash.txt`.

### How to read the numbers

- Overlays share the load address `0x80130FF8`, so the tool identifies the resident one by comparing the first 256 bytes of the window with each `.OVR` file. Counter changes between two polls are credited to the id resident at the end of the poll. Polls are seconds apart, so the numbers are approximate.
- "Static hits" are runs of build-time compiled overlay code (`overlay_static_entries` over `0x80130FF8..0x8013C720`). "Interpreter fallbacks" are calls the interpreter ran instead. Question 190 in `docs/OPEN_QUESTIONS.md` infers (not proven) that the fallbacks are the BIOS exception path in low RAM, not overlay code, so a non-zero fallback count alone is not a fault.
- A `no match` poll means the window held no known `.OVR` head (a load in progress, or the level changed its own code).

### Self-test result (agent, headless, no human)

`tools\overlay_coverage.py -BootRoute --headless --max-seconds 100` (the same polling code as a visible run) booted by itself, entered the TEMPLE level function at frame 4063, saw the TEMPLE overlay resident from frame 5383, then 14,716 static hits in 81 entries, 65 CRC misses, a clean exit and no crash file. The other seven rows read "no". That proves the polling and the summary. It does not prove the other levels. A separate 20 s visible-window run (no input) started, polled 10 times with 0 errors, and exited cleanly; nobody played it, so Ctrl+C and window-close handling were not exercised.

### Warp to a level (coverage aid, not natural play)

Patricio cannot play far, so `tools\overlay_coverage.py --warp LEVEL` starts a level directly. It is for coverage testing of your own copy, on the debug build only. It changes guest RAM through the debug server (`write_ram`). It changes no file, no framework code and no generated code. Nothing from it is committed.

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_overlay_coverage.ps1 --warp WIND
powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_overlay_coverage.ps1 --warp FORTRESS --headless --max-seconds 100 --shots 8
```

- `LEVEL` is `TEMPLE`, `WIND`, `WATER`, `EARTH`, `PRISON`, `FIRE`, `FIRE2`, `BRIDGE` or `FORTRESS`, or a dispatcher index (0 to 5, 7 to 9). `--warp` implies `--boot-route`: the tool plays New Game by itself, and the warped level starts instead of TEMPLE at guest frame 4063.
- Use `--port 4386` (or another free port) if a coverage session is already open on 4385.
- `--shots S` saves a 320x240 PNG every S seconds to `<out>\shots\`. `--warp-no-state` skips the flag writes below (the level then plays a long movie, see below).
- Run about 100 s headless: the level function enters at frame 4063 (about 60 s of wall time at the headless speed seen here, 55 to 65 guest frames per second), the overlay becomes resident at about frame 4310 in the nine recorded runs, but the frame varied between runs (4306 to 4315 for the eight overlays; a re-run of WIND became resident at 4439). Then you get 30 to 40 s of the level.
- The summary says `WARPED run (not natural play)` and lists `gp+252` changes. The JSON has a `warp` block with the table before and after and the flag write. **A fault in a warped run may come from the warp, not from the level. Report it separately from natural play.** The game state is not what a played game would have: character, health, score, lives, saved progress and the story flags are those of a fresh New Game.

How it works (agent-observed, from the sources below):

1. The EXE function at `0x80032D60` (called from `0x800489B4`, `0x80048A48`, `0x80048ADC`, `0x80048BEC`) sets up a game, then at `0x80032EA8` reads the word at `0x800D76A8` (gp+252), applies abs(), and jumps through the 12-word table at `0x80013910` (`lw v0,14608(at)` at `0x80032ED8`, the only reader of the table in the EXE text, static scan). Each entry is a thunk at `0x80032EE8..0x80032F98` that loads a level function and calls `0x8003846C(21, function)` (it passes the function and the priority 21; the meaning of that call is not known).
2. The tool waits until all 12 table words are in RAM (the EXE is copied there a little after the debug port opens), then copies entry N over entry 0 (index 0 = TEMPLE, the first level of New Game). It writes the four bytes with `write_ram` and reads them back. Run log line: `WARP: dispatcher entry 0 (TEMPLE) now points at index N`.
3. Without more, most level functions never reach their overlay load. At `0x8002C434..0x8002C47C` (the WIND function; the other level functions were not read for this) the function tests gp+2760 (`0x800D8074`). When it is 0 it calls `0x8002B4E8(6)` and `0x80050548`, which play a long story movie (seen on screen in a headless run: the story FMV with Sub-Zero and the sorcerer, still playing at frame 6170 and later). TEMPLE's own function sets gp+2760 and gp+2904 (`0x800D8104`) to 1 and the word `0x800D8084` to 1 at `0x8002B6B8..0x8002B6DC`, so a game that has played TEMPLE skips the movie. The game zeroes all three at frame about 4006 (New Game init; polled: 0 at 3007, 1 after my write at 3502, 0 again at 4006). So the tool writes them to 1 inside the guest-frame window 4012 to 4060, by spinning on `frame`. If it misses the window the run log says `warp flags NOT set` and you rerun. TEMPLE needs no flags.
4. START skips the movie but the game then goes back to the title screens (agent test: reads of ids 84, 118, 177 to 179, 163, 193 and 194 repeated at frames 4281 to 4522, the same ids as the boot at frames 551 to 797). So skipping with START is not a way to a level.

Result of nine headless runs (agent, 100 s each, `--warp`, `--shots 8`, port 4386, debug build; output `work\overlay_coverage\warp_<LEVEL>\summary.json`):

| Level (index, id) | Loaded id | Reached | Resident from frame | Static hits | Entries hit | Interpreter fallback (count) | Fault |
|-------------------|-----------|---------|---------------------|-------------|-------------|------------------------------|-------|
| TEMPLE (0, 140), control | 140 | yes | 5261 | 20,075 | 81 | yes (21,258) | none |
| WIND (1, 142) | 142 | yes | 4310 | 295,816 | 77 | yes (34,083) | none |
| WATER (2, 141) | 141 | yes | 4315 | 248,864 | 121 | yes (30,366) | none |
| EARTH (3, 136) | 136 | yes | 4311 | 31,705 | 36 | yes (30,989) | none |
| PRISON (4, 139) | 139 | yes | 4306 | 37,329 | 42 | yes (30,771) | none |
| FIRE (5, 137) | 137 | yes | 4310 | 121,966 | 82 | yes (29,881) | none |
| FIRE2 (7, 137) | 137 | loaded, black screen | 4310 | 20 | 4 | yes (38,618) | none |
| BRIDGE (8, 135) | 135 | yes | 4307 | 233,124 | 67 | yes (33,783) | none |
| FORTRESS (9, 138) | 138 | yes | 4310 | 6,884 | 19 | yes (34,527) | none |

- "Reached" means the first 256 bytes of the window equal the `.OVR` head from the disc (`tools\overlay_coverage.py`) and the level function was entered (`fn_entry`: one entry at frame 4063 in each run, except EARTH 3, FORTRESS 4 and FIRE2 6 entries). In every run the matching held for every poll after the first match (0 unmatched polls after it).
- For each run, exit code 0, no `psx_crash.txt`, no crash-like line in `run.log` (the `faults` field is empty). The counters are deltas between polls 2 s apart. See "How to read the numbers". All `segment_alias_interp` counts are 99.9 to 100 percent of the interpreter fallbacks, as in question 190. The fallback is not a fault by itself.
- Screens (agent saw them in the screenshots, not committed, not checked by Patricio): WIND, WATER, EARTH, PRISON, FIRE, BRIDGE and FORTRESS show a 3D stage with Sub-Zero, the health bars and a lives counter. EARTH and FORTRESS show an enemy fighting him. TEMPLE showed the first fight in T2.16. The names of the stages in the table are the tool's labels for the overlay files, not confirmed level names.
- FIRE2 (index 7, function `0x8002E130`) loads the FIRE file but the screen is black at frames 4970 and 8816 (a small moon shape at 6858), and `gp+252` goes 7, -1, 7 (at frames 6858 and 7450). Only 4 static entries ran. It is a different mode, not a playable stage as warped. Which state it needs is not known (question 232).
- FORTRESS shows `gp+252` 9, -1, 9 (frames 8211 and 8817) and 4 level-function entries, FIRE2 shows 6. The tool did not press any pad button after the boot route. The reason for the restart is not known (question 233).
- Dispatcher indices 6 and 11 load no overlay, and index 10 is conditional (`docs/EXE_OVERLAYS.md`). They are not options.

An earlier set of nine runs without the flag writes entered each level function at frame 4063, but no overlay but TEMPLE's and FIRE2's was ever resident in 100 s (50 of 50 polls unmatched), because of the movie in step 3. That is why the flag write exists.

Files used and changed: `tools\overlay_coverage.py` (new options `--warp`, `--warp-no-state`, `--shots`). The scratch probes `work\warp_probe.py` and `work\state_probe.py` are not part of the repo (git-ignored). If your copy's save or New Game flow differs, the frame numbers 4012 to 4060 may need a change (constants `WARP_STATE_FROM`, `WARP_STATE_TO`).

### Investigation script

`tools\overlay_interp_probe.py` (headless, about 2 minutes) lists the interpreted PCs and their code, the FIRE and WIND entry instructions, and the shared-entry counts. Results are in `docs/OPEN_QUESTIONS.md` (190 to 193).

## T3.1 Release rebuild with the vsync-off default

Agent-run, 2026-10-20, from the repo root, same commit as the D9 follow-up. Generated code was not regenerated.

### Commands

```
$env:PSXRECOMP_TOOLCHAIN_DIR = '<RETRO_TOOLS_DIR>\cmake-clang'
$env:PATH = '<RETRO_TOOLS_DIR>\cmake-clang\bin;<Git>\bin;<RETRO_TOOLS_DIR>\python;' + $env:PATH
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSXRECOMP_REQUIRE_GAME_C=ON
cmake --build build --target psx-runtime
cmake -S . -B work\build-dbg -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSX_DEBUG_TOOLS=ON -DPSXRECOMP_REQUIRE_GAME_C=ON
cmake --build work\build-dbg --target psx-runtime
```

Only 3 steps rebuilt in each tree (BIOS registry object, playtest diagnostics object, link). The previous Release exe was copied to `work\exe_backup\` first (git-ignored), with the previous `build\game.toml` and `build\settings.toml` and the previous debug exe.

### Result

| Item | Size (bytes) | SHA-256 |
|------|--------------|---------|
| `build\MythologyKombat.exe` (Release, the exe to record on) | 51,759,616 | `ff813773b1c5a9a608ee0331c82e004a0c468c61192975817c9199c45e7a0a81` |
| `work\build-dbg\MythologyKombat.exe` (debug tools, used by smoke and boot route) | 35,525,632 | `b31a6b490ccc5029b26d56438cc1a787d53e3ddbe1f90f324e514e35e4993b44` |
| Previous Release exe (rollback copy, `work\exe_backup\`) | 51,759,616 | `b5573bbe586f7669f3dfad11d3ca3a6f8888f8e37eb47eccdffbb8f201a7856b` |

- Same size as the previous exe; the hash differs because each relink changes it (see the T2.4 note). The new hash is the one to record on.
- Generated code unchanged: all files listed in `work\generate_run11_seed_t28b.sha256.txt` match (0 mismatches, checked by a PowerShell hash loop).

### Config staging

- `game.toml` has `[video] vsync = "off"`. The build copies it to `build\game.toml` with `copy_if_different`. This build copied it again, because the staged file differed. The staged file now equals the repo file, so the launcher-added `multitap_analog = true` line under `[controller]` is gone from `build\game.toml`.
- `build\settings.toml` was not touched by the build (identical to before). It overrides `game.toml`. It reads `vsync = "immediate"` (rewritten by the launcher; the earlier D9 edit set `"off"`) and `multitap_analog = true`.
- `"immediate"` and `"off"` both map to 0. Source: `psxrecomp\recompiler\src\config_loader.cpp` lines 983 to 984 (`game.toml` `[video]`) and lines 3153 to 3154 (`settings.toml` `[video]`).
- `multitap_analog` is read from `settings.toml` (`config_loader.cpp` lines 3406 to 3408). `build\settings.toml` line 61 sets it to true, so removing the line from `build\game.toml` changes nothing. Which file wins when both set it was not exercised at runtime.
- The perf run `tools\perf_run.ps1 -Name T31` used the `game.toml` path only. The hidden-window run below uses `--game game.toml` with `--no-launcher` and shows the wall-clock pacer.

### Checks

| Check | Result |
|-------|--------|
| `python tools\smoke_boot.py` (debug build) | PASS, 60 s, frames 0 to 4081, 4 screenshots ok |
| `python tools\run_boot_route.py --expect tests\replays\expected\boot_to_menu.json` | MATCH, 7 checkpoints. Warnings: `exe_sha256 differs` (expected file still has the old hash, T3.2) and `wr`/`pc` locator differences at frames 3900, 4300, 5000, plus no RAM/VRAM compare at frame 3900 (paused on 3903). The expected file was not changed |
| `tools\perf_run.ps1 -Name T31 -Seconds 40` (no `PSX_VSYNC`) | log line `present cadence: wall-clock pacer (16.6639 ms/frame)` (`work\perf\run_T31.log`) |
| `git ls-files` for `ps1_game/`, `work/`, `generated/`, `.bin .cue .exe .ovr .iso .img` | no matches. `git status` shows only the docs edits and the pre-existing `psxrecomp` submodule state |

- The recording in `tests\replays\local\session-1792525023167056` was made on the old exe `b5573bbe...7856b`. It does not apply to the new exe; the new recording is T3.3.

## T3.2 Refresh replay baselines

Agent-run, 2026-10-20, from the repo root, against the T3.1 debug build `work\build-dbg\MythologyKombat.exe` (SHA-256 `b31a6b490ccc5029b26d56438cc1a787d53e3ddbe1f90f324e514e35e4993b44`). The route file was not changed.

### Commands

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\run_boot_route.py --runs 5 --record-expected tests\replays\expected\boot_to_menu.json
<RETRO_TOOLS_DIR>\python\python.exe -I tools\run_boot_route.py --runs 1 --expect tests\replays\expected\boot_to_menu.json     (twice)
# negative control: copy of the route with the CROSS step at frame 4001 instead of 4000, under work\route_neg\
<RETRO_TOOLS_DIR>\python\python.exe -I tools\run_boot_route.py --runs 1 --route work\route_neg\neg.json --out work\route_neg\result.json --expect tests\replays\expected\boot_to_menu.json
```

### Results

| Step | Result |
|------|--------|
| Record | One cold boot gave an exact RAM/VRAM hash at all 7 checkpoints, so the tool stopped (`runs: 1`). The file now has `exe_sha256` `b31a6b49...3b44` |
| Diff against the old baseline | Only `exe_sha256`, `runs` (3 to 1) and the `wr`/`pc` locators changed (12 locator values). All judge columns (`cyc wc ws mmio mc sp sc qc`), `ram_sha256`, `vram_sha256`, `route_sha256` and the miss totals are identical |
| Verify run 1 | MATCH, 7 checkpoints, exit 0. No `exe_sha256` warning, no locator warning. Two notes: frames 1800 and 5000 were paused one frame late (1801, 5001), so their RAM/VRAM hashes were not compared (the fingerprint was compared) |
| Verify run 2 | MATCH, 7 checkpoints, exit 0. No warnings at all; all 7 RAM/VRAM hashes compared |
| Negative control | MISMATCH, 12 differences, exit 1. Frames 3000 to 3900 identical (input not yet different); from frame 4300 `wc`, `ws`, `mmio`, `mc`, `ram_sha256` and `vram_sha256` differ, and so do `wc`, `ws`, `mmio`, `mc` and `ram_sha256` at 5000. `route_sha256` also differs (expected, the file changed) |

### Locator warnings

- The `wr`/`pc` warnings seen at T3.1 (frames 3900, 4300, 5000) were comparisons against the old-exe baseline. After re-recording, neither verify run printed any locator warning, and the `exe_sha256` warning is gone.
- They are ordered locators that upstream says may differ for identical guest state. The evidence that they were benign: the old and new baselines have identical judge columns and RAM/VRAM hashes and differ only in `wr`/`pc`, which is what a relinked exe with identical generated code would give. In the negative control they differ only at frames 4300 and 5000, where the judge columns also differ. Whether they would stay stable across more builds was not tested.
- The "RAM/VRAM hash not compared" note is a timing effect of the host pause, not a state difference. `--runs N` exists to fill those gaps at record time.

### Files

`tests\replays\expected\boot_to_menu.json` (changed, committable), `tests\replays\README.md`, `docs\SETUP.md`, `docs\CHANGELOG.md`, `docs\OPEN_QUESTIONS.md`. The negative-control route and result are under `work\route_neg\` (git-ignored). No screenshots or recordings were made.

## Perf measurement tools (T3.6)

Run these from the repo root. `tools\perf_run.ps1` is a PowerShell script. The two Python tools use only the standard library.

### Run and meta file

```
powershell -ExecutionPolicy Bypass -File tools\perf_run.ps1 -Name X
```

- It writes the settings block into `work\perf\run_X.meta.txt`. The `work\` folder is git-ignored.
- The settings are not added to `session.json`. That file is written by the exe, so the meta file is the place for them. See `docs/OPEN_QUESTIONS.md`, question 222, which stays open.
- In the meta, `video.supersampling` shows the raw key from `settings.toml`. The game log reports the preset-derived value. For example, the meta shows 4 and the log says 9x. Read both before you compare runs.

### Print the settings block

```
python -I tools\perf_summarize.py X
```

- It prints the settings block from `work\perf\run_X.meta.txt`.
- If the meta file is missing, it says so. The run then predates T3.6 or was not made with `perf_run.ps1`.

### Vblank percentiles

```
python -I tools\perf_telemetry.py <session-dir> [<session-dir> ...]
```

- It reads `telemetry.csv` in each session folder. The session folders are under `build\saves\diagnostics\`.
- It prints the vblank interval at p50, p90, p99, p99.9 and max, in milliseconds.
- It prints the share of intervals above 33 ms. The share is split in three groups: all rows, `cd_xa != 0` and `cd_xa == 0`.
- It replaces the scratch script `work\scratch\tele.py`.
- The same telemetry folder gives the same output on every run.

### Measured on this machine (2026-10-20)

| Item | Value | Note |
|------|-------|------|
| `build\settings.toml` video | `internal_resolution = "4k"`, `supersampling = 4`, `antialiasing = true`, `vsync = "immediate"` | Read from the file. It overrides `game.toml` |
| GPU | Intel HD 630, driver 22.20.16.4708 (dated 2017). NVIDIA MX150 | |
| Power plan | Ultimate Performance | |
| Display scale | DPI 120 (125% scale) | User-reported. Not measured by an agent |

## Guard for game data in the repo (T3.16)

The guard checks that no game data is in the git index. Run it from the repo root:

```
python tools\check_no_game_data.py [--repo DIR] [--list FILE|- [--root DIR]] [--max-mb N]
```

| Option | Meaning |
|--------|---------|
| `--repo DIR` | Repo to check. Defaults to the folder above `tools\` |
| `--list FILE` or `--list -` | Check the paths in a file, or read them from stdin, instead of the index. `-` reads stdin |
| `--root DIR` | Folder that the `--list` paths are relative to. It also turns on the content checks |
| `--max-mb N` | Size limit for a staged file. Default 32 MB |

| Exit code | Meaning |
|-----------|---------|
| 0 | Clean |
| 1 | Violations. Each one prints as `FAIL <path>: <reason>` |
| 2 | Usage or git error |

- It checks the staged index blobs, not the files in the work tree.
- Extra checks: a raw CD sector (the 12-byte CD sync pattern), a file over the size limit, the `PS-X EXE` header, and the nested `ps1_game/`, `work/` and `generated/` folders.
- For CI (T3.17): run the guard on a checkout without submodules.

### Tests

```
python tests\test_check_no_game_data.py
```

- 19 tests. They take about 25 s.
- `python -I -m unittest` does not work for this. Use the file path, as above, or `python -m unittest discover -s tests -p "test_check*"`.

### Known minor issue

- A file path with non-ASCII characters prints as mojibake in its `FAIL` line on the Windows console.

## Launcher patches and screenshots (T3.12)

The launcher fixes are patch files under `patches\launcher\` (D19). The `recomp-ui\` submodule is not edited. The patches apply to the pinned commit `7c635c6b`.

| File | Item (`docs/LAUNCHER_DESIGN.md` 6.1) |
|------|--------------------------------------|
| `patches\launcher\0001-dashboard-fit-right-column.patch` | Scroll on the main section |
| `patches\launcher\0002-game-card-disc-glyph.patch` | Calendar-like glyph in the game tile |
| `patches\launcher\0003-game-card-wrap-file-name.patch` | File name cropped |
| `patches\launcher\0004-player-card-selector-padding.patch` | Analog/D-Pad bottom padding |
| `patches\launcher\0005-settings-window-size-combo.patch` | Window size dropdown |
| `patches\launcher\0006-settings-control-column-width.patch` | Renderer label width |
| `patches\launcher\0007-settings-align-checkboxes-and-screen-model.patch` | Misaligned controls |

### Apply the patches

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools\apply_launcher_patches.ps1
```

- It reads the recomp-ui commit that the repo pins. It exports that commit with `git archive` into `work\recomp-ui-patched`, then applies every `patches\launcher\*.patch` in name order with `git apply`.
- It prints the destination path on its last line.
- `-Only 0001,0003` applies a subset. The before and after screenshots use this.
- It writes only under `work\`.
- `git -C recomp-ui status --short` must print nothing.

### Build with the patched tree

Use the same flags as T2.4, and add `-DRECOMP_UI_ROOT`. The T3.12 report does not say whether the T2.4 flags were kept, so check the configure log.

```
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DRECOMP_UI_ROOT=<REPO_ROOT>\work\recomp-ui-patched
cmake --build build --target psx-runtime
```

- PSXRecomp's `runtime.cmake` uses `RECOMP_UI_ROOT` when it is set. No CMake change is needed.
- Any relink changes the exe SHA-256. Record the hash of the build you test. A user recording (T3.3) must come after the final relink.

### Capture a DPI-aware screenshot

The T3.11 method (`CopyFromScreen` from a process that is not DPI aware) gives a 1536 by 864 crop of a 1920 by 1080 screen at 125 percent. Do not use it for layout checks.

```
powershell -ExecutionPolicy Bypass -File tools\launcher_window_probe.ps1 -Exe work\build-launcher-test\MythologyKombat.exe -Out work\screens\probe.png
```

- The script marks itself per-monitor DPI aware, then reports the real window rectangle and the primary display, and saves a capture.
- Options: `-DelaySeconds N` (default 10) and `-Disc <cue>`.
- Scripted views: the launcher has a built-in hook, `LNG_SCRIPT`. The T3.12 report gives this form: `LNG_SCRIPT="wait:N;view:settings;click:x,y;shot:f.png;quit"`. This doc does not record a run of the hook in the game exe.

### Lesson: line endings in patch files

A Windows Python text-mode write added CR bytes to a patch header. `patches\launcher\.gitattributes` sets `*.patch -text`, so patches must keep LF line endings. Write patch files in binary mode, or with `newline=''`, when a script writes them.

### Status

- The patches are agent-measured. The user has not confirmed them. Item 4 (patch 0004) is not verified as the user's complaint.
- Outcomes are in `docs/LAUNCHER_DESIGN.md` section 6.2. Open items are in `docs/OPEN_QUESTIONS.md` (243).
- Not tested: multitap, narrow layout, non-PSX consoles, real mouse session.

## Setup-host build (T3.18)

The setup host is the exe that runs the setup wizard. It is built with no game C. Its build folder is `build-setup\`, which is git-ignored.

Agent part measured on 2026-10-20 by the implementer. The first wizard run was observed by agents (see First wizard run below). Patricio's own run is still open. Logs are under `work\`: `build_setup_run.txt`, `build-setup.configure.log` and `clone_test_build.txt`.

### Environment

Use the same toolchain environment as T2.4 (`Game executable build (T2.4)` above).

### Commands

Run these from the repo root:

```
cmake -S . -B build-setup -G Ninja -DCMAKE_BUILD_TYPE=Release -DPSXRECOMP_FORCE_SETUP_HOST=ON -DPSX_SETUP_WIZARD=ON
cmake --build build-setup --target psx-runtime
```

### Timings

| Step | Dev tree (warm) | Fresh clone (cold) |
|------|-----------------|--------------------|
| Configure | about 25 s | 26 s |
| Build `psx-runtime` | about 1 min | 2 min 42 s, 310 steps |
| `git clone --recurse-submodules` | - | 49 s |

### Exe hashes

| Build | Size (bytes) | SHA-256 | Use |
|-------|--------------|---------|-----|
| Dev tree | 37,383,168 | `ce2a2497545ab53ce7445fb935d498e6460e127ea5cb6b0c3acbe0d8a5051e65` | Not for the kit. See the finding below |
| Patched variant | 37,386,240 | `6aba104feefbaa573c7cf890e314ee0466eb3476b7b75dc01c32fdb6084e3d2f` | Not for the kit. The report does not say which tree it was built in |
| Fresh clone, no `generated\` | 32,589,824 | `b4e9d186d918e0839631a80dbb267e075307627bae45471bb63ff4bfa8b711a3` | The true setup host |

### Finding: dev trees link game code into the setup host

- In a dev tree where `generated\` exists, `PSXRECOMP_FORCE_SETUP_HOST=ON` still compiles and links `generated\overlays_static*.c`. That is 9 extra objects and about 4.8 MB more.
- Cause: the overlay-static glob in `psxrecomp\runtime\overlay_static_sources.cmake` and in `psxrecomp\runtime\runtime.cmake` (about line 1612) ignores `FORCE_SETUP_HOST`.
- So a dev-tree setup-host exe holds game-derived code. It must never go in the kit.
- The kit and CI exe must be built from a clean clone or CI checkout with no `generated\` folder. See `docs/DECISIONS.md` (D24).

### Fresh clone test

The clone is at `work\clone-test`. The check was run on 2026-10-20.

- `git clone --recurse-submodules` took 49 s.
- The clone was clean. It had no `generated\` folder and no tracked game files.
- Configure took 26 s. The build gave the 32,589,824-byte exe above.

### Submodule status (question 258, closed)

- The `psxrecomp` ` m` in `git status` was a stale index entry. The index recorded 66 bytes for `generated/OpenBIOS.emitter.sha`, from a CRLF checkout. The file on disk is 65 bytes with LF. The blobs equal HEAD, and `git -C psxrecomp diff --raw` is empty.
- Fix, in the submodule index only:

```
git -C psxrecomp add generated/OpenBIOS.emitter.sha generated/OpenBIOS_dispatch.c generated/OpenBIOS_full.c
```

- Optional, per clone: `git -C psxrecomp config core.autocrlf input`.
- The superproject has no `.gitattributes`, and that cannot affect the submodule.
- The ` m` may come back after the emitters run. Check it with `git -C psxrecomp diff --raw` before you act on it.
- Do not run `git add psxrecomp`. See the T0.5 section above.

### Pin decision (question 257, closed)

- The psxrecomp pin stays at `449c31e5`.
- Upstream `958ae0e3` is 3 commits ahead, with 19 files changed.
- The only substantive change is a shared title release command with a required channel. It adds `runtime\psx_release_channel.cmake`.
- Revisit at T3.19 and T3.21.

### Open log line (question 267)

- The setup-host configure log prints `BIOS backends linked: OpenBIOS`. A setup host should link no game C. The cause is not investigated.

### First wizard run (T3.18): agent-observed on 2026-10-21

- Not user-run. The agents ran this test. Patricio did not click anything.
- The result is agent-observed, not user-reported.
- Exe: `build-setup\MythologyKombat.exe` in the fresh clone `work\clone-test`, SHA-256 `b4e9d186...` (see Exe hashes above).
- Wizard state was kept inside the clone. `RETCOMM_DATA_HOME`, `TEMP` and `TMP` pointed into it.
- Clicks came from recomp-ui's `LNG_SCRIPT` hook. Screenshots were saved as PNG files. The native file dialog was driven with Windows UI Automation and SendKeys.

#### Wizard pages

| Page | What it showed | What happened |
|------|----------------|---------------|
| 1. Build tools | "Download latest portable toolchain", checked by default. The link text names `TechnicallyComputers/retcomm-toolchains` | Clicking Next started the download at once. No confirmation was asked |
| 2. Setup required | BIOS optional (the bundled OpenBIOS was used). Disc image, with Browse | The `.cue` was picked. The wizard showed "Disc verified", SLUS-00476, NTSC-U and "ISO header OK" |
| 3. Generate and rebuild | "Generate & rebuild..." | Ran with no confirmation |

Page 1 details:

- Asset `cmake-clang-v1-windows-x64.zip`, 209,497,009 bytes. The latest release was v1.0.14 at the time.
- The zip unpacked to `retcomm-data\toolchains\cmake-clang\1.0.14` (about 798 MB).
- A second copy went to `<REPO_ROOT>\toolchain\` (798,317,234 bytes). Together the two copies use about 1.6 GB.
- The link text is stale. The repo redirects (HTTP 301) to `RetroPortingToolKit/RetroPorting-Toolchains`. The name is set in `psxrecomp\host\psxrecomp_codegen_host.c` at line 2005 (`k_tc_repo`). See question 270.

Page 3 steps, in the order they ran:

1. Built the emitters with `ninja -j4`.
2. Ran the pack's own Python: `psxrecomp_cli.py generate --project-root ... --config game.toml --disc ... --gen-marker ... --json-progress`.
3. The static overlay step ran with the pack's bundled Python. The D13 error "No module named compile_overlays" did not appear. The reason was not checked.
4. The setup exe quit. It started `build-release\recomp_deferred_rebuild.cmd`.
5. That script ran `ensure-toolchain`, then `rebuild --build-dir build-release --target psx-runtime --exe-basename MythologyKombat --no-pgo --prune-after build-intermediates`, then started the exe with `--launcher`.

#### Timings

| Step | Time |
|------|------|
| Toolchain download | about 110 s |
| Toolchain step, whole | 3 to 4 min |
| Generate, cold emitter build included | about 1 min |
| Rebuild (`psx-runtime`, 451 ninja log lines) | 5 min 20 s |
| First run, total | about 10 min on this machine |

#### Results

| Item | Result |
|------|--------|
| `build-release\MythologyKombat.exe` | 51,759,616 bytes. SHA-256 `17ca5c784e1bed9d47492651ef53c92eefe85e98c2cfaeecb59b9c0d2c6b4a8a` |
| `build\MythologyKombat.exe` (T3.1 exe) | Same size. SHA-256 starts `ff813773`, so the hash differs. Cause not checked (question 274) |
| `generated\` in the clone | 71 files, 100,583,108 bytes. 70 of 70 match `work\generate_run11_seed_t28b.sha256.txt` byte for byte. `AOT_STATIC_AUDIT.json` differs, as expected |
| Window | Windowed boot reached the title screen (START, OPTIONS). Window title "MythologyKombat Recompiled" |
| `tools\smoke_boot.py` | Fails on the release build. A release build has no TCP debug server. Expected |
| Build string | Says `-dirty`, because the wizard changed `game.toml` |

#### What the user sees

- Next on page 1 starts a 209 MB download. Nothing asks first.
- The disc pick on page 2 is not remembered on the next launch. The wizard writes `disc.cfg` and `rom.cfg` into the project root.
- "Generate & rebuild" runs with no prompt.
- The game window opens on the title screen.

#### Toolchain pin

- The wizard fetches the latest toolchain. It does not pin one. This run got v1.0.14.
- Not tested: the variable `RETCOMM_TOOLCHAIN_SKIP_UPDATE` is said to change only the update prompt. See questions 247 and 276.

#### Fixes made after the run

These are uncommitted until the orchestrator commits them.

- `.gitignore` now ignores `/toolchain/`, `/disc.cfg`, `/rom.cfg`, `/build-release/`, `/build-setup/` and `/build-setup.configure.log`.
- `game.toml` now has `multitap_analog = true` under `[controller]`, right after `default_mode`. The launcher writer adds a key after the last line of `[controller]`, before the next header. Before the fix, the key landed below the `[netplay]` comment block. Keep the key where it is. Do not put a comment directly above a header that follows `[controller]` keys. The writer was not tested by a run. The writer rewrites LF line endings. See question 279.

#### Not verified

- Wizard error paths, for example no network or antivirus blocking.
- The automatic relaunch with `--launcher` after the rebuild, as a separate check. The title screen was reached (see Results).
- Why the two exe hashes differ.

### User step: first wizard run (T3.18, user run still open)

Only you can do this. Your run is still open. The agent run above does not replace it. Use the fresh clone, so the exe has no game C.

```
cd <REPO_ROOT>\work\clone-test
Start-Process -FilePath .\build-setup\MythologyKombat.exe
```

1. In the wizard, pick the disc: `<REPO_ROOT>\ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue`.
2. Before you approve any download, write down what the wizard asks you. Copy the exact text. Note any size or address it shows. The agent run recorded the pages (question 268). Compare your text with them.
3. Go on step by step. For each step, note what happened, how long it took, and any error text. Copy error text word for word.
4. Send the list back to the orchestrator. The wizard may generate and compile, which takes several minutes.

Your run is user-reported. The agent run above is agent-observed and does not replace it.

## CI (T3.17)

The workflow is `.github\workflows\ci.yml`. Its jobs run on GitHub-hosted runners, which have no disc. No job has a game file. CI does not run `generate` or `rebuild`, does not set `PSX_PGO`, and does not add any artifact to git (D25).

- Triggers: push and pull request on `main` and `master`, and manual `workflow_dispatch`.
- Permissions: `contents: read`. Every checkout has `persist-credentials: false`.
- Composite action: `.github\actions\toolchain\action.yml`. It was read by eye only. No tool ran it.

| Job | Runner | What it does |
|-----|--------|--------------|
| `guard` | ubuntu-latest, no submodules | Runs `tools/check_no_game_data.py` (T3.16) with `python3 -I`, then the guard tests. Forward slashes, because it runs on Ubuntu |
| `emitters-test` | windows-latest, recursive submodules | Installs the toolchain pack, builds `psxrecomp\recompiler`, runs `ctest` |
| `setup-host-build` | windows-latest, clean clone, recursive submodules, no `generated\` | Applies `patches\launcher`, configures the setup host, builds `psx-runtime`, runs the asserts, uploads the artifact |

### Toolchain pin

- Pack: the clang pack from RetroPorting-Toolchains, tag `v1.0.14`. CI does not use MSYS2.
- Pinned by tag and SHA-256: `28da9742385e7ff875b3d9311e8ed89dbdc84f27b6ecba2bc0d0acc11f6d2b4d`. Size 209,497,009 bytes.
- This answers question 247 for CI. The setup wizard still fetches the latest pack (question 276).

### emitters-test

- Two upstream test targets are excluded: `ws_cull_edge_interp_test` and `draw_distance_interp_test`. They do not link with the clang pack. See `docs/SETUP.md` (T0.5).
- The build step tolerates only those two failures. It then sets `$global:LASTEXITCODE` to 0. GitHub's `pwsh` wrapper appends an exit with `LASTEXITCODE`, so without the reset the step would fail.
- The job asserts `ctest` version 3.26 or newer.
- Local check (agent, before the first run): 35 tests were registered, and the non-excluded ones were run one by one. `ctest` itself was not run locally, so that count is partial. The first GitHub run registered 145 tests (see "First GitHub run" below). The count of 38 given for this suite is not reconciled (question 288).
- The job runs on `windows-latest`. It does not run on Linux.
- Fix after the first run: the job sets `TEMP` and `TMP` to `runner.temp`. Two tests (52 `cli_generate_aot_static` and 77 `disc_companion`) failed on the 8.3 short temp path (`C:\Users\RUNNER~1`, not `runneradmin`).
- Fix after the first run: a new step runs `psxrecomp\runtime\hash_codegen.cmake`. It writes `runtime\include\overlay_codegen_hash.h`, which is git-ignored and only a runtime build wrote before. Without it, test 56 `compile_overlays_static_tail` failed with `STALE RECOMPILER BINARY tag hash 00000000`. The local output is `0x115b1739`, equal to the baked hash. The step reads source files only and no game data.
- Tolerated tests: nine tests are listed in a map inside `ci.yml`, each with a one-line reason. A listed test that fails is allowed. A listed test that passes gives a warning only.

| Tolerated test | Reason (from the first run and local runs) |
|----------------|--------------------------------------------|
| `overlay_segment_keys` | Harness link fails: undefined `psx_mod_memory_address`, `psx_mod_immediate_select`, `host_span_begin` and `host_span_end` |
| `overlay_segment_gate` | Same harness link failure as `overlay_segment_keys` |
| `bundled_release_layout` | Expects `SCPH1001` in the "BIOS backends linked" line. The template at the pin says OpenBIOS |
| `gpu_frame` | Needs numpy, which is missing on the runner |
| `aot_overlay_discovery` | Hardcodes `C:\msys64\mingw64\bin\gcc.exe` |
| `mod_owned_display_controls` | Extra calls happen before the baseline in `main.cpp` |
| `gl_internal_scale_guards` | Three errors: `flush_flat_batch` not found. One failure: `test_hr_surface_users_pick_the_right_scale` |
| `native_wide_line_batching` | `flush_flat_batch` definition is missing |
| `overlay_candidate_capacity` | Assertion on the order of `load_one_dll` fails |

- The reasons for test numbers 61 and 126 rely on the CI log only. They were not reproduced locally.
- Strictness: any failure outside the map fails the job. So does a `ctest` exit that is nonzero with no listed failure, and any `(Not Run)` or `Timeout` result. Tests shown as `Not Run (Disabled)` are ignored. Three are disabled upstream: `interpreter_perf_guards`, `runtime_perf_diag_guards` and `overlay_pair_dedup_runtime`. They still make `ctest` exit nonzero.
- Nine tolerated tests are upstream test drift. Reporting them to RetroPortingToolKit/psxrecomp is the user's decision (question 324).

### setup-host-build

- Clean checkout with recursive submodules. The job checks that no `generated\` folder exists.
- Applies the launcher patches with `tools\apply_launcher_patches.ps1` (D19).
- Configures with `PSXRECOMP_FORCE_SETUP_HOST=ON` and `PSX_SETUP_WIZARD=ON`.
- Runs `tools\ci_assert_setup_host.ps1` (D24). It fails if:
  - a `generated\` or `ps1_game\` folder exists;
  - the configure log says `linking generated game C`;
  - `build.ninja` or `.ninja_log` mentions `generated/overlays_static`, or the `SLUS_004.76` dispatch.
- Uploads `MythologyKombat-setup-host-windows-x64` (the exe and `SHA256SUMS.txt`) as a workflow artifact. It is kept 14 days. It is never committed.

### Pinned actions

| Action | Version | Commit |
|--------|---------|--------|
| `actions/checkout` | v6.1.0 | `d23441a48e516b6c34aea4fa41551a30e30af803` |
| `actions/cache` | v5.1.0 | `caa296126883cff596d87d8935842f9db880ef25` |
| `actions/upload-artifact` | v6.0.0 | `b7c566a772e6b6bfb58ed0dc250532a479d7789f` |

- The reviewer re-checked these commits with `gh api`.

### Local checks

| Check | Result |
|-------|--------|
| `actionlint` v1.7.12 on `ci.yml` | No findings. The zip was downloaded from `rhysd/actionlint`, with SHA-256 `6e7241b51e6817ea6a047693d8e6fed13b31819c9a0dd6c5a726e1592d22f6e9`. It is kept in `work\actionlint` (git-ignored). The orchestrator downloaded it with the user's yes |
| Composite action | Read by eye only |

### First GitHub run (2026-10-21)

- The repo was pushed to GitHub as the private repo `PAumedes/MythologyKombat` on 2026-10-21 (T3.23, D28). The first CI run is run `39700721720`.
- `guard`: passed.
- `setup-host-build`: passed in 3 min 35 s.
- `emitters-test`: failed. `ctest` ran 145 tests (147 minus the two excluded interpreter tests). 12 failed. The fixes above and the tolerated-test map were made after this run.
- The fixed workflow has not run on a runner yet. The fixes are unverified until the next push.
- GitHub showed an `ubuntu-latest` image migration notice. It concerns the `guard` job only, which runs on Ubuntu. The other two jobs run on `windows-latest`.

### Not verified

- The fixed workflow has not run on GitHub. The next push is the check.
- Not verified yet: the toolchain download and unpack on a runner, `pwsh` 7 behaviour, the SDL3 lookup, the libchdr `FetchContent`, and cache effects. The first run showed `setup-host-build` passing, so the parts it covers are checked on a runner.
- Open items: questions 286 to 290 and 324 to 326 in `docs/OPEN_QUESTIONS.md`.

## Local release script (T3.19)

`tools\release.ps1` builds the game zip on the PC that holds the disc. Run it by hand at release time. It is not a pre-commit step (D25). It runs under Windows PowerShell 5.1.

### Command

Run from the repo root:

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools\release.ps1 -Version <x.y.z> -Disc "<REPO_ROOT>\ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue" [-Ref <commit>] [-Draft] [-Repo owner/name] [-Pgo] [-KeepDisc]
```

| Parameter | Meaning |
|-----------|---------|
| `-Version` | Release version, for example `0.1.0`. The tag is `v<Version>`. A version that starts with x.y.z (including 0.1.0-rc1) must equal the `VERSION` file exactly. Only non-numeric labels such as `test` skip the check. The format is checked with a regex. The binary version stamp must also equal `VERSION`. See "Release-candidate verification" below |
| `-Disc` | Path to the `.cue` of your own disc image |
| `-Ref` | Tag or commit to build. Default: tag `v<Version>`, which must exist |
| `-Pgo` | Build with PGO. Needs the disc and a window. Off by default |
| `-Draft` | Print the `gh release create ... --draft` command. It runs only after you type `UPLOAD` in an interactive window |
| `-Publish` | Not implemented. The script throws |
| `-Repo` | `owner/name`, passed to `gh` as `--repo`. Optional |
| `-KeepDisc` | Keep the disc copy that `generate` makes in the staging clone. Deleted by default |

The script's header describes each parameter.

### Steps

1. Clones the repo at `-Ref` into `work\release\<Version>\src`, with recursive submodules. It never uses the dirty working tree. It stops if the clone is dirty, if a submodule differs from `framework_pins.txt`, or if a `generated\` folder is present.
2. Applies `patches\launcher` through the clone's own `tools\apply_launcher_patches.ps1` (D19). The build then points at the patched copy with `-DRECOMP_UI_ROOT`.
3. Runs `verify-disc`, `generate`, `ensure-toolchain` and `rebuild` through the clone's `tools\run_psxrecomp.ps1`. The build is Release, with no PGO unless `-Pgo`. It sets `-DPSX_PUBLIC_RELEASE=ON`, so the playtest recorder and input display are off by default (D14, D26).
4. Runs the build guards.
5. Builds the release folder from an allow-list. It does not copy the build folder and remove items.
6. Runs `tools\check_release_content.py` on the folder, then on the zip. Any violation stops the script.
7. Writes the zip (sorted entries, fixed timestamps), `checksums.txt` (SHA-256, in `sha256sum` format) and `release_notes.md`.
8. With `-Draft`, prints the upload command. Otherwise nothing is uploaded.

Outputs are in `work\release\<Version>\`: the zip, `checksums.txt`, `release_notes.md`, `logs\`, `src\` and the staged folder. `work\` is git-ignored.

### Timings (measured 2026-10-21)

| Step | Time |
|------|------|
| Clone | 99.6 s |
| Launcher patches | 8.5 s |
| `verify-disc` | 6.2 s |
| `generate` | 140 s |
| `ensure-toolchain` | 36 s |
| `rebuild` | 105 s warm, 434 s cold |
| Zip | 5 s |

- Whole run: about 7 minutes with a warm ccache, about 15 minutes cold.

### Test run (2026-10-21)

The test folder is `work\release\test\`. The version label was `test`, so the version check was skipped (see `-Version`).

| Item | Value |
|------|-------|
| Zip | `MythologyKombat-test-Windows-x64.zip`, 27,117,891 bytes |
| SHA-256, from `work\release\test\checksums.txt` | `72f8c31c92c6188a9e6f517f2813fec2d4ed283ebf047d84565279ebb5f254b3` |
| Files in the zip | 421 files, about 89 MB unzipped |
| Game exe in the zip | 51,762,176 bytes |
| Top-level folder | `MythologyKombat-<version>\` |

- The zip is not in git. The hash above is a hash, not game data.

### What the zip holds

The zip holds only what the allow-list names. Inside the top-level folder:

| Item | Note |
|------|------|
| Game exe, with the launcher | Release build |
| `execution.json`, `psx_game_version.txt`, `release_info.json`, `README_FIRST.txt` | Version and run files |
| `game.toml`, `game_options.toml` | Config. `game.toml` holds disc digests (MD5, SHA-1, CRC-32 and size) and relative names such as `ps1_game\...` and `work\disc\SLUS_004.76`. These are hashes and names, which D8 and D23 allow |
| `LICENSE`, `NOTICE` | Licences (D20) |
| `assets\`, `mods\`, `licenses\` | Assets, mod packages and licence texts |
| `bios\` | `openbios.bin` only. Its SHA-256 was compared with `psxrecomp\bios\openbios.bin` |
| `overlay_toolchain\` | 374 files: tcc, `psxrecomp-game.exe`, `psxrecomp-bios.exe`, an embedded Python, 9 seed JSON files (address lists only), and headers. The seed files hold no BIOS or game bytes. Four of them are retail-BIOS seed files that carry ROM SHA-256 digests as text |

Not in the zip:

- `input.ini`, `keybinds.ini`, `overlay_captures.json`, `mods\state.toml`, `texture-packs`, `cache`, `saves`, `replay-diagnostics.py`, `diagnostics-location.txt`, `psx_execution`, `_deps`.
- `compiler.txt`. It holds a local path.
- The disc, memory cards, BIOS dumps and recordings. These are excluded by the allow-list and by the content check.

### Content check

- `tools\check_release_content.py` is stdlib only. Use `--dir` for a folder, or `--zip` for a zip.
- It fails on any `.bin`, `.cue`, `.iso`, `.chd` or `.mcd` file, on any session recording, and on any path under `ps1_game\`. It names each file it rejects. The full rule list is in the checker's docstring.
- Deep scan: it reports WARNs for the PS-X EXE header and the CD sync byte pattern inside `MythologyKombat.exe`, `psxrecomp-game.exe`, `psxrecomp-bios.exe` and `sqlite3.dll`. These are framework constants. They do not answer question 280.
- Tests: `python -I tests\test_check_release_content.py`. There are 18 tests.
- Negative controls, run by the implementer: 13 FAIL lines on planted files. The planted files were a `.bin`, a `ps1_game` cue, a session recording, a renamed generated file and a 512 KiB BIOS-sized file. The reviewer re-planted a `.bin`, a local-path text, a `.mcd`, a CD sync pattern and a PS-X EXE header. Each was caught.

### Smoke test

- `tools\smoke_release.ps1 -Zip <zip> -Disc <cue> -At 15,30,45,60`.
- Measured: unzip 1.7 s. Windowed boot with `--disc` and `--no-launcher`. The process stayed alive for 60 s. The frame counter read 530, 1420, 2328 and 3231 at 15, 30, 45 and 60 s. Between the 30 s and 60 s samples that is about 60 frames a second. No crash file was written.
- The screen captures were black. So the smoke test gives no visual evidence.
- A `psx_freeze_dump` `hard_freeze` appeared at frame 0, about 3 s after start, on every boot. This includes the dev exe. Frames kept advancing. It is probably a false positive. It was not investigated (question 291).
- The user still has to look at the title screen once in the unzipped release (question 292).

### Draft upload safety

- The only network write in the script is the `gh` call at about line 538 of `tools\release.ps1`. It sits behind `-Draft`.
- It runs only if the tag matches the built commit, the session is interactive, and you type `UPLOAD`. The match is case-sensitive.
- `-Publish` throws.

### Known limits

- Reproducibility: fixed on this PC for one commit (see "Reproducibility (T3.26)" below). Cross-machine is open (question 295).
- Runtime files appear in an unzipped folder: `input.ini`, `keybinds.ini`, `overlay_captures.json`, `saves\*.mcd`, `mods\state.toml` and the freeze dump. The updater (T3.21) must keep `saves\`, the settings and the input files (question 293).
- `-Ref` and `-Repo` are checked only by the regex on `-Version` (question 294).

### Reproducibility (T3.26)

Questions 274 and 295. Decision D27.

Before the fix, builds of one commit gave different exes. Two of them differed in 70 bytes. The causes, all fixed:

| Cause | Where | Fix |
|-------|-------|-----|
| PE COFF timestamp, set by the linker | `CMakeLists.txt` (`psx-runtime`), and the framework recompiler build in `tools\release.ps1` | `-Wl,--no-insert-timestamp`. `target_link_options` for the game. The `LDFLAGS` environment variable for the framework build |
| `__DATE__` and `__TIME__` in the build id | `psxrecomp\runtime\src\crash_trace.c`, lines 59 to 61 (`kBuildId`) | A force-included header, `mk_reproducible.h`, redefines both from the commit time |
| `git describe` in the build id | `psxrecomp\cmake\psx_build_revision.cmake` | `tools\release.ps1` sets `core.abbrev=12` and deletes all tags in the staging clone and its submodules. The describe string is the bare 12-character commit hash |
| Build paths | Compiler flags | `-ffile-prefix-map`, as a guard |

- The build id now has this form: `SLUS-00476/<VERSION>+<describe>/psxrecomp-<describe>/sha256-...`.
- The game build date comes from the CMake cache variable `MK_SOURCE_DATE_EPOCH`. Empty means a normal build, unchanged. `tools\release.ps1` passes `--cmake-extra=-DMK_SOURCE_DATE_EPOCH=<commit time in Unix seconds>`.
- `psxrecomp\` is not edited. Upstream has no `SOURCE_DATE_EPOCH` support (question 296).

Measured (agent run, 2026-10-21): five full `tools\release.ps1` runs, each from a clean clone of one throwaway commit (`bde0bd7`).

| Item | Result |
|------|--------|
| Exe SHA-256 | `fea0f713be1d4886a1b802812ba2267d13d78eacbe2b3dc20f99e957f3f6a7fb`, 51,762,176 bytes, in all five runs |
| Different `-Version` labels | Same exe hash |
| Zip SHA-256, two runs with the same label | `320821bfcf5e942f58a0c057b4c88428b6c962061475f6dcb7f09ebe0d82ed4e`, 27,120,365 bytes |

- Three earlier runs had different zips. Some had a different label. Others had framework helper exes with link timestamps from before the `LDFLAGS` fix.
- A different label changes the zip by design: `release_info.json`, the README, the folder prefix and the zip name. It does not change the exe.

Limits:

- It holds per commit. A new commit gives a new exe, because the build id holds the commit hash and the commit time.
- Proven on this PC and this toolchain (clang pack 1.0.14). Cross-machine is not tested.
- The CMake change was checked by reading. There was no full configure diff of `build.ninja`.
- The fix takes effect only once `CMakeLists.txt` is committed, because `tools\release.ps1` builds committed state.
- The T3.1 and wizard exe pair (question 274) was not rebuilt, so that pair is not explained here.

### Status

- T3.19 is done (agent part and review). The user's own run with the real version is still to do.
- T3.26 is done (agent part and review). Reproducibility holds on this PC for one commit. See D27.
- The draft upload is still to do. It needs your typed `UPLOAD`.
- Decisions: `docs/DECISIONS.md` (D26).

## Known issue: Midway logo audio on the release zip (2026-10-21)

Status: not reproduced on a quiet machine. Root cause not found. No release change is made. Open items: questions 297 to 300 in `docs/OPEN_QUESTIONS.md`.

### What was seen

- User-reported: the first run of the freshly unzipped release (`work\release\eyes\MythologyKombat-test`, built from commit `717ee78` by `tools\release.ps1`, run with `--disc` and `--no-launcher`) had broken Midway-logo audio. That run has no log.
- User-reported: the user then ran it twice on a quiet machine with `PSX_RUNTIME_PERF_DIAG=1`. Logs: `work\release\run1.out`, `work\release\run1.err`, `work\release\run2.out` and `work\release\run2.err`. Both runs played the audio correctly.

### Agent investigation

Agent-measured, about 20 runs under `work\release\audio-test`.

| Hypothesis | Result |
|------------|--------|
| H1: the bundled tcc autocompile stalls the audio | Not supported. Each cold run compiles once: a 4100-byte block at `0x80002000`, in BIOS-region code. With autocompile on and with `PSX_OVERLAY_AUTOCOMPILE_OFF=1`, 3 cold runs each were clean |
| H2: the release settings differ from the dev build | Cleared. The release has no `settings.toml`, so `game.toml` applies: vsync off, OpenGL, 1x. The dev `build\` run used 4K, 9x supersampling and vsync immediate. The audio defaults match: 44.1 kHz, `buffer_ms` 180 |
| H3: `PSX_PUBLIC_RELEASE` | Cleared. It changes only the playtest diagnostics defaults |
| H4: first run against second run | No systematic difference |
| H5: hidden window | Clean |

The failure was seen only in these runs:

| Run set | Result |
|---------|--------|
| Release runs (2 of 14) | Audio failure at FMV start. One run: audio fill pinned at 218.3 ms for 9 s, about 44.1k overflows a second, so the output was not draining. The other: fill pinned at 257 to 260 ms, about 1.3k overflows a second, about 3% dropped for the whole FMV |
| Dev exe in the release layout, no toolchain (3 of 3) | Failed. 92,493 underruns in total, with stalls |
| Dev exe in `build\` (one control run) | Clean |

- The failure did not follow CPU load (4 busy processes), compiles or window visibility.
- During the user's broken run, agents were running `tools\release.ps1` and CMake builds on the same PC.
- The user's boot had a 2 to 3 s stall at frame 0. A `psx_freeze_dump` `hard_freeze` file is in the `eyes` folder, and its heartbeat entries are all at frame 0. This fits a contended start, but it is not proven.
- None of the agent's runs wrote a freeze dump.

### Candidate fix, not tested

- Raise `[audio] buffer_ms` in `game.toml` from 180 to 250 to 300 ms. The valid range is 30 to 500 ms. Not run. See question 300.
- A possible upstream cause is the audio output stats and the sink at FMV start, `psxrecomp\runtime\src\main.cpp` near line 4855. Not verified. See question 297.

### How to capture a log (user step)

Use this if the Midway logo audio is broken again. Run the commands in one PowerShell window, from the folder that holds the unzipped release.

1. Set the diagnostics variable in that window:
```
$env:PSX_RUNTIME_PERF_DIAG = '1'
```
2. Start the game with its output sent to files. `-Wait` holds the window until the game closes:
```
Start-Process -FilePath ".\MythologyKombat.exe" -ArgumentList '--disc', '<path to your .cue>', '--no-launcher' -RedirectStandardOutput "work\release\runN.out" -RedirectStandardError "work\release\runN.err" -Wait
```
3. Note the time, whether the Midway logo audio was broken, and anything else running. Send the `.out` and `.err` files to the agents, and say whether a `psx_freeze_dump` file was written in the game folder.

Without the redirect, the output is not kept. The first broken run had no log, so the cause is still unknown.

## Updater (T3.21)

Status 2026-10-21: built and tested on a local fake server. Not tested against real GitHub (the repo does not exist yet, T3.23). Decision D29. Open items: questions 302 to 307.

### What it is

A PowerShell updater in the release zip: `update.cmd` (a one-line wrapper) and `update.ps1`. It checks `PAumedes/MythologyKombat` for a newer release, downloads the zip and `checksums.txt`, checks the SHA-256, and replaces the game build. It keeps the player's files (see below). It never starts the game and never runs anything from the zip.

### How a player uses it

1. Open PowerShell or a console in the extracted game folder (the folder with `MythologyKombat.exe`).
2. Run:
```
.\update.cmd
```
3. The updater shows the new version and asks `y/N`. Type `y` to install. Any other answer stops it with nothing changed.
4. The update runs only when you start it. Close the game first. The updater refuses while the game runs, and checks again just before the swap.

### Options

| Option | What it does |
|--------|--------------|
| `-CheckOnly` | Checks for a newer release and stops. Changes nothing. |
| `-DryRun` | Runs the checks and the plan without replacing files. |
| `-Rollback` | Restores the previous build from `.update\backup-<old>`. |

Example: `.\update.cmd -CheckOnly`.

### What it keeps

`saves\`, `settings.toml`, `input.ini`, `keybinds.ini`, `disc.cfg`, `bios.cfg`, `launcher-window.ini`, `mods\state.toml`, `mods\texture-packs\`, `cache\` and `overlay_captures.json`. The disc path is never touched.

`game.toml` and `game_options.toml` are replaced only if the file is unchanged from the old release. If you edited one, your copy is kept and the new one is written beside it as `.new`.

The previous build stays in `.update\backup-<old>` until the new build has run once.

### How it is checked

- Only `https://github.com` downloads from `PAumedes/MythologyKombat` release assets, and the CDN hosts GitHub redirects to. Redirects are followed by hand, up to 5 hops.
- Only versions strictly newer than the installed one, in the form `vX.Y.Z`.
- The SHA-256 from `checksums.txt` is checked before anything is unpacked.
- The zip is checked for unsafe names and links, and its files must match `manifest.json` exactly.

### Release side

| Item | Where |
|------|-------|
| Updater source | `tools\updater\update.cmd`, `tools\updater\update.ps1` |
| Manifest | `tools\new_release_manifest.ps1` writes `manifest.json` (SHA-256 and size of each file) |
| Zip contents | `release.ps1` copies the updater files and writes `manifest.json` after `release_info.json` and `README` |
| Line endings | `.gitattributes`: `update.cmd` is CRLF, `update.ps1` is LF |
| Repo default | `release.ps1 -Repo` defaults to `PAumedes/MythologyKombat`; the same value is in `release_info.json` as `repo` |

The first release must ship `manifest.json`, so the first update has an old manifest to compare with. It does.

### Test commands

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools\test_updater.ps1
python -I tests\test_check_release_content.py
```

The first runs 228 checks in about 8 minutes, against the fake server `tests\updater_test_server.py` and a fake install made from `work\release\test\MythologyKombat-test`. The second runs 25 tests.

### Not tested

- A real GitHub or CDN download (question 307h).
- A game start during the preparation step (question 307e).
- The `Local\` mutex warning (question 307d).
- The exe-hash failure after the swap (question 307f).
- `update.cmd` does not return the updater's exit code (question 307b).

## Release-candidate verification (2026-10-21)

This is the agent's check of the release pipeline at the T3.21 commit (before the history rewrite, D31). It is agent-measured on this PC. It is not a release, and no draft was uploaded. The title screen was not checked by an agent (see below).

### Command

Run twice, with no `-Draft`. Both runs succeeded:

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools\release.ps1 -Version 0.1.0 -Ref HEAD -Disc "<REPO_ROOT>\ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue"
```

| Run | Log | Zip | Total |
|-----|-----|-----|-------|
| a | `work\release\rc1-a.log` | `work\release\rc1-a\MythologyKombat-0.1.0-Windows-x64.zip` | 401.4 s |
| b | `work\release\rc1-b.log` | `work\release\rc1-b\MythologyKombat-0.1.0-Windows-x64.zip` | 251.1 s |

Stage times in seconds. Rebuild is 195.5 s in run a and 50.3 s in run b. The other stages are given as ranges or single values from the record:

| Stage | Time |
|-------|------|
| Clone | 58 |
| Patches | 4 |
| Verify | 4 |
| Generate | 91 to 95 |
| Ensure toolchain | 28 |
| Rebuild | 195.5 (run a), 50.3 (run b) |
| Assemble | 6 |
| Content checks | 2 to 3 |
| Zip | 4 |

### Results

| Item | Result |
|------|--------|
| Exe SHA-256 | `86e02021338504a6e0263661e51bd2ece5493463cdd00cc6f771163c36a8ec50`, 51,762,176 bytes. Same in both runs |
| Zip SHA-256 | `73279dc370f934923325457312a4f33895e24c042562ff777c607946b9ac65a5`, 27,156,192 bytes. Byte-identical in both runs (`cmp`) |
| `checksums.txt` | Identical in both runs |
| `manifest.json` | Identical in both runs. SHA-256 starts `ea7fa2dd`. It lists 423 files |
| Zip entries | 424. The record does not say which entry is not in the manifest list. Open, see question 312 |
| Content check | OK on the zip and on the folder: 424 files, 71 generated hashes, 0 violations |
| Smoke run of the release exe | Alive for 60 s. Frame counter 819, 1686, 2591 and 3482 at 15, 30, 45 and 60 s (about 59 fps). No crash file. A `hard_freeze` dump was written at start (question 291) |
| Updater harness on the real build | `tools\test_updater.ps1 -SourceDir work\release\rc1-b\MythologyKombat-0.1.0 -Only 01`: 20 of 20. Covers CheckOnly, DryRun, a full update with all 423 manifest files byte-exact, preserved files identical, a second run that is up to date, and a rollback tree that is byte-identical |

### Zip layout

One top folder, `MythologyKombat-0.1.0\`.

| File | Size | Note |
|------|------|------|
| `update.cmd` | 101 bytes | One CRLF line |
| `update.ps1` | 49,855 bytes | LF line endings |
| `manifest.json` | | Hashes of the release files |
| `release_info.json` | | Repo `PAumedes/MythologyKombat`, version `0.1.0`, tag `v0.1.0` (the tag does not exist yet), commit: the T3.21 commit (pre-rewrite hash, not kept, D31), `public_release` true, `pgo` false, toolchain 1.0.14, psxrecomp `449c31e5`, recomp-ui `7c635c6`, 7 launcher patches |

### Title screen: not checked by an agent

- Every capture method returned a black image. The methods were CopyFromScreen, PrintWindow and a DPI-aware capture.
- The dev build control gave black too. So this is a capture limit of this PC's GL surface, not a result for the release.
- The user must look at the title screen by eye. The user did check an earlier release-test zip by eye and reported correct audio.
- Question 311.

### Findings

- The script's version check (line 235) matches any label that starts with `x.y.z`. So `0.1.0-rc1` is treated as a version. It must then equal `VERSION`. The binary version stamp must also equal `VERSION` (line 325).
- So a pre-release label needs `VERSION` to hold that string, or the regex needs an end anchor. The first release ships as plain `0.1.0`, marked as a pre-release on GitHub (D30). Question 308.
- The draft command has no pre-release flag (`gh release create ... --draft`).

### Sequencing

- The build id holds the commit hash and the commit time (D27). So every new commit changes the exe hash. The history rewrite (D22) changes every hash.
- The release zip must be built from the final commit, after the rewrite and the push (T3.23).
- The two zips above show that the pipeline is reproducible on this PC. They are not the release.

### Known open items

| Item | Question |
|------|----------|
| Version label rule for pre-releases | 308 |
| Windows Sandbox on this edition | 309 |
| OpenGL 3.3 in Windows Sandbox | 310 |
| Title screen by eye | 311 |
| Manifest entry count (424 zip entries, 423 listed) | 312 |
| Smart App Control on a clean machine | 255 |

## Clean-machine test (T3.22, done with partial result)

Run by the user on 2026-10-21 in Windows Sandbox on this PC (user-reported, no agent artifact; D30). Zip 0.1.0, SHA-256 `73279dc3...65a5`, extracted and run with `--no-launcher`. Settings: no network, 4 GB memory, vGPU on, disc folder mapped read-only. Steps are in `docs\TASKS.md` (T3.22).

| Item | Result |
|------|------|
| Default OpenGL renderer | Game started. Gameplay reported OK. Question 310 |
| `--renderer software` | Game started. Gameplay reported OK |
| FMV videos | Slower than on the dev PC in both renderers. Question 313 |
| Audio | Not judged. The Sandbox cannot be used for audio. Question 315 |
| Updater online path | Not tested (no internet). Covered by `tools\test_updater.ps1` and the 20 of 20 harness only. Question 316 |
| Other T3.22 steps | Not reported (hash check, SmartScreen, Smart App Control, Mark of the Web, launcher with no arguments, forbidden-file listing). Question 317 |

Windows Sandbox works on this edition (question 309).
