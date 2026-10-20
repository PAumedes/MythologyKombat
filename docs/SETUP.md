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

No git user name is set on this machine. The first commit used a per-command author. See `docs/OPEN_QUESTIONS.md`.

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

These are the downloads used. The zips are kept in `<RETRO_TOOLS_DIR>\_downloads`.

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

- The `_downloads` folder is outside the repo. It is safe to delete.

### Uninstall

Delete the folder `<RETRO_TOOLS_DIR>`.

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

## EXE header and overlay load addresses (T1.4)

The script `tools\exe_overlays.py` reads the boot EXE and the overlay files. It gives the EXE header, the start-up constants, and the load address and size of each `.OVR` file. Run it from the repo root after `tools\disc_classify.py`, because it reads `work\extracted\` and `work\disc_classes.json`:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\exe_overlays.py [--root PATH]
```

- It needs `work\extracted\SLUS_004.76` and `work\extracted\OVERLAYS\*.OVR` from T1.3.
- It needs `work\disc_classes.json` from T1.3.
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
