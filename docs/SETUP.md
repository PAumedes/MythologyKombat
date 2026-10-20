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

The git user name is set in this repo's config to Patricio Aumedes. The first commit used the author `localuser`. History was not rewritten. See `docs/OPEN_QUESTIONS.md`, question 1.

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

### Commit note

`.gitmodules` and the `psxrecomp` gitlink were committed in the "T0.7: ..." commit (`beee35b`). They were staged in that commit by accident of staging order.

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
- The Ghidra GUI has not been opened. Nothing shows that it opens the EXE with the PS1 loader. No GUI project was found under `%USERPROFILE%`.

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

This is the user's second play test. It is user-reported. No agent ran it, and no artifact was saved. No agent checked the picture or the sound. The frame rates are the user's estimates, not measured values. T2.10 and T2.11 stay as they are in `docs/TASKS.md`. This section does not change their status.

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

### Next steps

1. The user runs a visible-window test with vsync off. In PowerShell:

```
cd build
$env:PSX_VSYNC = '0'
.\MythologyKombat.exe --disc "<cue>" --game game.toml --no-launcher
```

   The user reports the fps, the audio and any tearing.
2. Then try `PSX_VSYNC=-1` (adaptive).
3. If vsync off is acceptable, set `[video] vsync = "off"` (or adaptive) in `game.toml`. Do this only with the user's agreement.
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
