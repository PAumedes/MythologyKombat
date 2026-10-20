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
