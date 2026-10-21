# PUBLISHING AUDIT

Read-only audit of this repo for a possible public GitHub release. Nothing was pushed, no remote was created, `ps1_game\` was not touched.
No legal conclusions are drawn. Facts only.

Evidence tags: **[M]** measured (a command was run, output seen), **[S]** source-read (a file was read), **[H]** hypothesis (not verified).
Audit date: 2026-10-20. Repo HEAD at audit: `b5f9e13` on `master`.

## 1. What is in git

| Fact | Evidence |
|------|----------|
| 80 tracked files, 47 commits, 1 branch (`master`), no remote configured | [M] `git ls-files \| wc -l`, `git log --all --oneline \| wc -l`, `git branch -a`, `git remote -v` |
| Every path ever committed (`git log --all --name-only`) still exists in the current tree. Nothing was ever added and then deleted, so there is no removed-file history to scrub | [M] `comm -23` of all-history paths vs `git ls-files` printed nothing; `git log --diff-filter=D` printed nothing |
| No tracked file is matched by `.gitignore` (nothing force-added) | [M] `git ls-files -i -c --exclude-standard` listed nothing |
| Working tree clean, except the `psxrecomp` submodule shows `m` (see section 4) | [M] `git status --short` |
| Largest tracked files: `assets/psxrecomp.ico` 370 KB, `docs/SETUP.md` 140 KB, `symbols.toml` 94 KB, `psx_symbols.h` 89 KB. Repo object store 2.4 MB | [M] `ls -la`, `git count-objects -vH` |
| No `.bin/.cue/.exe/.iso`, no `generated/`, no `work/`, no BIOS file, no memory card, no screenshot is tracked | [M] `git ls-files` listing read in full |
| No tokens, API keys, passwords, private keys found. The word hits (`token`, `secret`) are the "identifier-like token" text in `docs/SYMBOLS.md` and `tools/symbol_hunt.py` | [M] `git grep -i -E 'ghp_\|github_pat\|api[_-]?key\|secret\|token\|password\|AKIA\|BEGIN (RSA\|PRIVATE)'` |
| History was searched for `localuser` additions with `git log -p -S`. The only additions are the `<RETRO_TOOLS_DIR>\python\python.exe` run lines in tool docstrings and docs | [M] |

### 1a. Personal information

| Item | Where | Evidence |
|------|-------|----------|
| Author identity `Patricio Aumedes <the author personal email>` on 46 commits. The first commit `fa5df2b` is `localuser <the author personal email>` (author and committer). Intentional per the task, flagged here. Every commit is public once pushed; the email cannot be removed without rewriting history. GitHub offers a `noreply` address if wanted | all commits | [M] `git log --all --format='%an <%ae>'` |
| Co-author trailer `Co-Authored-By: Claude ...` in commit messages (per harness rule) | commit messages | [H] not grepped per commit |
| Local path `%USERPROFILE%\...` (user name `localuser`, tool root `<RETRO_TOOLS_DIR>`) | 25 tracked files: `CLAUDE.md`, `KICKOFF.md`, `docs/SETUP.md` (62 lines), `docs/TASKS.md` (17), `docs/CHANGELOG.md`, `docs/CONTROLS.md`, `docs/DECISIONS.md`, `docs/DISC_MAP.md`, `docs/FORMATS.md`, `docs/OPEN_QUESTIONS.md`, `docs/SYMBOLS.md`, `tests/replays/README.md`, `tools/*.py` and `tools/run_replays.ps1` (docstring "Run:" lines and one default `$Python` parameter) | [M] `git grep -c` |
| The email address does not appear in any file content (only in commit metadata) | | [M] `git grep '@gmail'` empty |
| `tools/check_prereqs.ps1` lists generic search dirs (`Downloads`, `Desktop`, `Documents`, `source`) built from `$HOME`; no literal user name | | [S] line 241 |
| The text names the user as "Patricio" in `docs/DECISIONS.md`, `docs/TASKS.md`, `docs/SETUP.md`, `docs/OPEN_QUESTIONS.md`, `docs/CHANGELOG.md`, `docs/CONTROLS.md` as the decision maker and play tester | | [M] `grep -c` |
| `docs/OPEN_QUESTIONS.md` question 1 and `docs/SETUP.md` line 19 say the first commit used the author `localuser` | | [S] |

### 1b. Gitignored local files that must stay out

Present on disk, ignored, never tracked [M] (`ls`): `ps1_game\` (the bin and cue), `work\`, `generated\`, `build\`, `saves\`, `disc_probe.json` (absolute path), `psx_freeze_heartbeat.json`. A fresh `git clone` will not contain them.
`.gitignore` also blocks `*.exe`, `*.dll`, `*.zip`, `/tests/replays/local/`, `session-*/`, `SCPH*.BIN`. [S]

Hazard: `.gitignore` blocks `*.exe`, `*.dll` and `*.zip` globally. A release artifact or a vendored DLL will not be picked up by `git add` without `-f`. Not a leak risk; a workflow trap. [S]

## 2. Tracked files derived from the game

Decision D8 (`docs/DECISIONS.md` lines 73-88) lets the user commit "address lists, names, sizes and hashes", and lists the allowed files. The user answered yes (question 75). [S]
D8 does not list `docs/DISC_MAP.md`, `docs/FORMATS.md`, `docs/SYMBOLS.md`, `docs/EXE_OVERLAYS.md`, `docs/COVERAGE.md`, or the replay digest files by name beyond "test routes". Those docs are also derived facts and are listed below so the owner can decide. [S]

| File | What it holds (facts) | Derived from | Evidence |
|------|-----------------------|--------------|----------|
| `game.toml`, `catalog_identity.json` | Serial `SLUS-00476`, boot EXE name `SLUS_004.76`, EXE load address, entry PC, text size, Track-01 size 538586832, **MD5 `8a75edba...`, SHA-1 `bf5803d3...`, CRC-32 `83988529`**, TOC fingerprint `dc720deb...` | disc image | [S] |
| `aot/overlays.json` | Disc MD5 and SHA-1, 12 `sha256` values (overlay images and excluded ranges), byte-offset checks with expected 32-bit words (about 20 words per check, e.g. `0x80013140: 0x00254546`), overlay file names | disc and boot EXE | [S] 258 lines |
| `seeds/ghidra_funcs.txt` | 1175 function start addresses (jal targets) in the boot EXE | boot EXE | [S] |
| `symbols.toml`, `psx_symbols.h` | 453 `[[func]]` entries: 10 `confirmed`, 443 `guessed`. Names are mostly Psy-Q SDK names matched by signature (`sdk_` prefix, `_spu_*`, `InitTAP`). The `psx_symbols.h` is the generated header form | boot EXE and SDK signature match | [M] `grep -c`, [S] |
| `docs/DISC_MAP.md` (384 lines) | Full file list of the disc: 211 file paths, sizes, start LBAs, sector counts, XA flags. No contents | disc | [S] |
| `docs/FORMATS.md`, `docs/SYMBOLS.md`, `docs/EXE_OVERLAYS.md`, `docs/COVERAGE.md`, `docs/DISC.md` | Format tags per file, offsets of a few strings in the EXE (e.g. `PS-X Control TAP Driver Ver 3.0` at `0x800BEB50`, `VSync: timeout`), overlay table facts, disc hashes | disc | [S] |
| `tests/replays/expected/boot_to_menu.json` | 7 checkpoints with a RAM SHA-256, a VRAM SHA-256 and hashed fingerprints per frame | the runtime running the game (OpenBIOS boot) | [S]; 16 sha256 values [M] |
| `tests/replays/routes/boot_to_menu.json` | Button names and frame numbers only | none | [S] |
| `docs/OPEN_QUESTIONS.md`, `docs/SETUP.md`, `docs/CHANGELOG.md` | Play-test notes, movie names (`MIDWAY01.STR`, `SZINTRO1.STR`), measurement results | disc and runs | [S] |

Facts relevant to sharing:
- No file contents from the disc were found in tracked files. A search for 16-byte hex dumps in `docs\` and `tools\` found none. [M] `git grep -E '[0-9a-f]{2}( [0-9a-f]{2}){15}'`
- The expected-word values in `aot/overlays.json` are 32-bit words copied from the boot EXE (a few dozen words in total). [S]
- Replay digests are hashes of emulated RAM and VRAM, not RAM. They depend on the exact build. `docs/DECISIONS.md` D9 and the git log say the baseline was refreshed after the T3.1 rebuild (exe `ff813773...`), so another person's build may not match. [H] not tested on another machine.
- `symbols.toml` names come from the SDK (Sony library), not from the game. Sony Psy-Q SDK names are a separate third-party matter. [S] note in `docs/SYMBOLS.md`
- Disc hashes identify one specific dump (NTSC-U SLUS-00476, 1 track). They are needed by the tooling (`known_md5`, `disc_hashes`, `required_disc_fp`); removing them would break verification (`psxrecomp\docs\AOT_SHARDING.md`: exit 3 on mismatch). [S]
- Other public recomp repos of the same framework commit the same kind of file (`game.toml`, `catalog_identity.json`, `.recomp.json`). `psxrecomp\docs\GAME_PROJECT_SETUP.md` lists them in the recommended layout. [S]
- Upstream's own public model commits **generated game C** (see section 5). This repo forbids that (`CLAUDE.md` hard rule). So this repo is more conservative than upstream. [S]

Not checked: whether any individual line in `docs/*.md` quotes game text longer than a few words. Only 3 string offsets are cited and a handful of names. A reviewer should skim `docs/SYMBOLS.md` and `docs/FORMATS.md` once.

## 3. Licence

| Component | Licence | Evidence |
|-----------|---------|----------|
| `psxrecomp/` | **PolyForm Noncommercial 1.0.0**, `Copyright (c) 2026 Matthew Stanley`; README says commercial licensing goes to him | [S] `psxrecomp\LICENSE`, `psxrecomp\README.md` lines 826-841 |
| `recomp-ui/` | **MIT**, `Copyright (c) 2026 Matthew Stanley` | [S] `recomp-ui\LICENSE` |
| `psxrecomp\lib\recomp-net`, `lib\retcomm-rbengine` (nested submodules) | MIT, "recomp-net contributors" / "retcomm-rbengine contributors" | [S] their `LICENSE` files |
| OpenBIOS (bundled `bios/openbios.bin`) | MIT, notice `psxrecomp\bios\OpenBIOS.LICENSE` | [S] `THIRD_PARTY_ATTRIBUTION.md` |
| libchdr | BSD-3-Clause (with bundled zstd BSD/GPL dual, LZMA SDK public domain, miniz MIT) | [S] same file |
| libjuice (netplay builds only) | MPL-2.0 | [S] |
| libwebp | BSD-3-Clause | [S] |
| TinyCC 0.9.27 (only in release zips) | notice files `licenses/TinyCC-LICENSE.txt`, `overlay_toolchain/tcc/COPYING` required by upstream CI | [S] `game-release.yml` lines ~627-628 |
| SDL3, Dear ImGui, fonts and images | not read in this audit; recomp-ui ships `assets/{fonts,img}/NOTICE.md` in release zips | [S] `BUNDLED_RELEASES.md` step 5 |

Correction to a project statement: `CLAUDE.md` and `README.md` say "PSXRecomp ... PolyForm Noncommercial" (correct). The task text for this audit said recomp-ui is also PolyForm; its `LICENSE` file is **MIT**. [S]

PolyForm Noncommercial 1.0.0 text grants a licence for noncommercial purposes and covers distributing the software and "new works based on it" (read from `psxrecomp\LICENSE`, first 1500 characters). The full conditions (notices, patent, noncompliance) were not read to the end. Reading the rest is a pre-publish step. [S, partial]

Files in this repo that came from the psxrecomp scaffold and so likely carry its licence terms (hypothesis, no copyright notice in the files themselves): `CMakeLists.txt`, `codegen_setup.c/.h`, `scripts/package_release.sh`, `.recomp.json`, `catalog_identity.json`, `game.toml`, `assets/psxrecomp.{ico,png,svg}`, `.claude\...` not. `game.toml` says "Autofilled by tools/new_project_layout/probe_disc.py". [S][H]
Files written in this project: `tools/*`, `docs/*`, `symbols.toml`, `seeds/`, `aot/overlays.json`, replay files. No licence file exists for them yet. [M] there is no `LICENSE`, `NOTICE` or `COPYING` in `git ls-files`.

What the repo needs (facts from upstream's own release docs, `psxrecomp\docs\ci\BUNDLED_RELEASES.md`, step 5): a `licenses/` folder in any shipped zip with psxrecomp's notices, `recomp-ui-LICENSE`, `assets/{fonts,img}/NOTICE.md`, OpenBIOS notice. The packager `psxrecomp\tools\package_game_release.sh` does this when run.

## 4. Submodules

| Item | psxrecomp | recomp-ui |
|------|-----------|-----------|
| URL in `.gitmodules` | `https://github.com/RetroPortingToolKit/psxrecomp` | `https://github.com/RetroPortingToolKit/recomp-ui.git` |
| Pinned commit | `449c31e5029f3a3281fa15060105928d2b3b13f7` (`v0.3.2-alpha-1770-g449c31e5`; `git describe` in the submodule says `nightly-805-g449c31e5`) | `7c635c6b366a6e0d5d3c913a7fce6ec04dd9f256` (`coverage-20261018-13-g7c635c6`) |
| Public upstream? | Yes. `git ls-remote` works; `origin/master` contains the pin (`git branch -r --contains`). Upstream `HEAD` is now `958ae0e3...` (the dry-run fetch showed `449c31e5..958ae0e3 master`), so the pin is behind upstream, not missing | Yes. `git ls-remote` `HEAD` is exactly `7c635c6...`, so the pin is the upstream tip |
| Dirty tree | 3 files under `psxrecomp/generated/` (`OpenBIOS.emitter.sha`, `OpenBIOS_dispatch.c`, `OpenBIOS_full.c`) show modified. | clean |

[M] for all rows (commands: `git submodule status`, `git ls-remote`, `git branch -r --contains`, `git fetch --dry-run`, `git status --short` in each).

Dirty tree is line endings only: `git diff --ignore-cr-at-eol --ignore-space-at-eol` in `psxrecomp` outputs 0 lines; git warns "LF will be replaced by CRLF" and `core.autocrlf=true`. [M] These three files are tracked upstream (they are the committed OpenBIOS recompiled C, per `BUNDLED_RELEASES.md`). No local content patch exists in the submodule. A fork is not needed for the pinned commits. [M]

Other facts:
- `psxrecomp` has its own nested submodules `lib/recomp-net` (`e5305932`, v0.1.9) and `lib/retcomm-rbengine` (`2a03e736`); a clone needs `--recurse-submodules`. Both are listed in `framework_pins.txt` along with the other two. [M] `git submodule status`, [S]
- Our superproject `.gitmodules` does not list recomp-net or rbengine; they come through psxrecomp's own `.gitmodules`. [S]
- The `recomp-ui` README says to add it from `https://github.com/mstan/recomp-ui.git`; `.gitmodules` uses the `RetroPortingToolKit` org. Both resolve at the time of audit (psxrecomp BUILDING.md also names `mstan/psxrecomp`). Whether `mstan/...` is a redirect was not checked. [S]
- Repo-level modifications live in this repo (`CMakeLists.txt`, `codegen_setup.*`) and not in the submodules. [S]
- Upstream branches are numerous and named like `codex/...`, `claude/...`; pinned SHAs on master are what matter. [M] `ls-remote` output
- Upstream moves quickly (`psxrecomp` is ahead of the pin; `recomp-ui` tag names are dated 20261018). If the pin goes stale, a user running `git submodule update --init` still gets the pinned commit, so the pins are stable. [H]

Pitfall: `git submodule update --init` for a user will clone upstream at the pinned SHA. If upstream force-pushes or deletes branches, the SHA could become unreachable. [H] Not observed.

## 5. What CI can build without a disc

Upstream facts (all [S] unless noted):

1. **Upstream's current public release model is "bundled"**: the title repo commits `generated/` (recompiled game C), CI links it and ships a compiled game zip. Players never run Generate. (`psxrecomp\docs\ci\BUNDLED_RELEASES.md`, `LOCAL_CODEGEN_SDK.md` section "Where this sits now"). The generated C needs the disc to produce. This repo forbids committing it (`CLAUDE.md`, `.gitignore`). **CI therefore cannot produce a playable bundled release from this repo as it stands.**
2. The older "setup host" model is retired upstream: `package_setup_host.sh` and `stage_setup_sdk.sh` are named "retired ... not part of the release flow". A setup host is still buildable locally with `-DPSXRECOMP_FORCE_SETUP_HOST=ON` (found in `psxrecomp\runtime\runtime.cmake` line 2663) and is described as "a developer convenience - not what CI ships". A setup-host release for end users would be a path upstream does not support in CI. The first-run Generate and rebuild wizard needs `PSX_SETUP_WIZARD=ON`, which `CMakeLists.txt` line 24 already sets.
3. The Generate path on a user's machine (`LOCAL_CODEGEN_SDK.md`): `python psxrecomp/psxrecomp_cli.py verify-disc | generate | rebuild`. It needs Python 3, a C/C++ toolchain (the `cmake-clang-v1` pack from `RetroPortingToolKit/RetroPorting-Toolchains`, fetched to `%LOCALAPPDATA%\retcomm\toolchains\cmake-clang-v1\`), the `psxrecomp` sources/emitters, and the user's disc. After a rebuild the playable product lives in `build-release/`; the zip-root exe forwards to it.
4. **recomp-ui standalone** (`recomp-ui\CMakeLists.txt`): top-level builds only a self-test exe `recomp-ui-launcher` ("so the repo can verify itself in isolation"). Real consumers `include(recomp_ui.cmake)`. So there is no standalone end-user launcher in recomp-ui. Requires CMake 3.24, SDL3 (`find_package(SDL3 CONFIG REQUIRED)`) or SDL2. No `.github/workflows` in recomp-ui. [S] (`ls recomp-ui\.github` failed).
5. psxrecomp workflows present: `cli-release.yml` (windows-latest + msys2 MinGW64 + `python tools/build_cli.py release`; triggered by `workflow_dispatch` and `release: published`; uploads `psxrecomp-cli-windows-x86_64.zip`) and `nightly-source-release.yml` (source snapshot including submodules). The title template is `docs/ci/templates/game-release.yml` (matrix `ubuntu-24.04`, `windows-2022`, `macos-15`, `macos-15-intel`; uses composite actions `build-emitters` and `fetch-toolchain` from `RetroPorting-Toolchains`; requires `-DPSXRECOMP_REQUIRE_GAME_C=ON`, i.e. committed generated C). The template also asserts `generated/<boot>_dispatch.c` is tracked (`tools/ci/check_generated.sh`), which this repo would fail. `psxrecomp\.github\actions\` exists in the submodule, but GitHub Actions only picks up workflows from the top-level `.github/workflows/` of the superproject; this repo has no `.github` directory. [M] `ls .github` failed.
6. Recompiler tests: `cd recompiler/build && ctest` runs 38 tests in under 5 seconds with no BIOS or disc (`BUILDING.md` "Check the build"). This is the safest CI job. [S] (not run in this audit)
7. The `RetroPorting-Toolchains` pack is the Windows clang/CMake/Ninja toolchain used locally (`docs/SETUP.md` line 77: release v1.0.14, CMake 3.31.12, Ninja 1.13.2, clang 22.1.8). In CI the upstream action `fetch-toolchain` downloads `/releases/latest` of that repo unless `RETCOMM_TOOLCHAIN_MIN_VERSION` is set; use a pinned version for reproducibility. [S]

What a disc-less GitHub Actions job on `windows-latest` can build, by evidence:

| Job | Possible without disc? | Evidence |
|-----|------------------------|----------|
| Recompiler tools (`psxrecomp-game`, `psxrecomp-bios`) and their `ctest` | Yes | [S] `BUILDING.md`; upstream `build_emitters.sh` |
| psxrecomp CLI package (`psxrecomp.exe`) | Yes (upstream already does) | [S] `cli-release.yml` |
| OpenBIOS C regeneration | Yes (from the tracked image) | [S] `BUILDING.md` step 2 |
| recomp-ui standalone self-test exe | Yes, needs SDL3 (system package or vendored) | [S] `recomp-ui\CMakeLists.txt` |
| This repo's `MythologyKombat.exe` (game runtime, setup-host form, no game C) | Plausible: `-DPSXRECOMP_FORCE_SETUP_HOST=ON`, which links no game C. This repo's configure passed with game C present; the setup-host form was not built in this audit | [H] |
| This repo's playable exe | **No.** Needs `generated/SLUS_004.76_*.c` from the disc | [S] `docs/SETUP.md` line 726, `CMakeLists.txt` |
| Overlay shard cache | No (compiled from the disc) | [S] `package_release.sh` comment, `BUNDLED_RELEASES.md` |
| `scripts/package_release.sh` | Needs the compiled game; the script itself is a bash wrapper | [S] |

Clang specifically: nothing in the upstream CI uses clang on `windows-latest`; it uses MSYS2 MinGW64 (`cli-release.yml`) or `llvm-mingw` from the `cmake-clang-v1` pack on the `windows-2022` matrix leg of `game-release.yml`. [S]

### Candidate "release artifact for people to download the launcher"

Options (facts, not a recommendation):

A. **Setup-host zip**: `MythologyKombat.exe` built with `PSXRECOMP_FORCE_SETUP_HOST=ON` plus the `psxrecomp/` tree needed for Generate (CLI, tools, emitters sources, OpenBIOS profiles), the pinned recomp-ui assets, licences. On first run the wizard asks for a disc, runs verify-disc, generate, and rebuild to `build-release/`. Upstream retired this shape for CI, so the packaging script would be ours (`package_setup_host.sh`, which still exists in the submodule, retired) [S]. The user machine needs the clang pack download (network) and Python. The Windows build step on the user side is the long part. Not tested in this repo. [H]

B. **Source-only repo + README instructions** (no binary releases): users clone with `--recurse-submodules`, install the toolchain, run the project's own scripts (`tools\run_psxrecomp.ps1`, see `docs/SETUP.md`). Nothing to build in CI beyond tests. [H]

C. **Bundled release** (upstream standard) requires committing `generated/` or making CI generate it from a disc, which Actions does not have. Conflicts with `CLAUDE.md` rule. [S]

## 6. What users must do with their own disc

(From `README.md`, `docs/SETUP.md`, `psxrecomp\docs\LOCAL_CODEGEN_SDK.md`.) All [S].

1. Own a copy of the NTSC-U disc (serial SLUS-00476). Dump to a single `.bin` and `.cue` (MODE2/2352, 1 track). The expected data-track MD5 is in `game.toml` (the repo says it is the hash of the dump the author used, and `required_disc_fp` is checked when netplay is enabled). Other dumps will fail verification (`docs/DISC.md`).
2. Place the files in `ps1_game\` (the folder holds `PUT_DISC_IMAGE_HERE.txt` and `readme.html`, ignored files, so a fresh clone will not have them unless the folder is created).
3. Verify: `psxrecomp_cli.py verify-disc --config game.toml --disc ...`.
4. Generate: `psxrecomp_cli.py generate --config game.toml ...` (OpenBIOS C is emitted from the bundled `openbios.bin`; no retail BIOS is needed. A retail `SCPH1001.BIN` is optional and the user's own).
5. Rebuild with the toolchain and run `build-release\MythologyKombat.exe`. Also needed for overlays: `aot/overlays.json` is committed, but its generated C (`overlays_static.c`) comes from the disc, so it is produced during generate (`docs/DECISIONS.md` D11-D12).
6. Saves go to `saves\`; settings to `settings.toml` beside the exe.

Not verified in this audit: that a clean clone, with only a disc, completes steps 3-5 on a second machine. [H] Nobody has done this yet; it is the main acceptance test for any public README.

## 7. Proposed README structure for end users

1. Title, one-line description, status badge (`.recomp.json` says `exploring`; update before publish).
2. **What this is / is not**: static recompilation of the PS1 NTSC-U Sub-Zero; no game data, no disc, no BIOS included; you must own the game. Not affiliated with Midway/Warner/Sony (wording is the owner's call).
3. **Status**: what works (boots, menu, first fight confirmed; movies partly tested, see D17), known issues (FMV pacing/vsync, untested 23 of 28 movies), link to `docs/OPEN_QUESTIONS.md`.
4. **Requirements**: Windows 11 x64, disc image requirements (serial, 1 track, expected hashes), GPU (OpenGL), disk space, optional controller.
5. **Quick start for players**: download, run, pick the disc, press Generate, wait, Play. Or the source route if option B is chosen.
6. **Build from source** (developers): clone `--recurse-submodules`, toolchain install (`RetroPorting-Toolchains` pinned version), exact commands.
7. **Controls and settings**: link `docs/CONTROLS.md`; `game.toml` vs `settings.toml`; vsync default off (D9).
8. **Troubleshooting**: hash mismatch, wrong dump, antivirus, toolchain download failure.
9. **Repo layout and docs index** (as in `CLAUDE.md`), contributions policy.
10. **Licence and credits**: licence of this repo's own files; PolyForm Noncommercial for psxrecomp and the "stays free" statement; MIT for recomp-ui, OpenBIOS, recomp-net, rbengine; link to `psxrecomp\THIRD_PARTY_ATTRIBUTION.md`; credit Matthew Stanley / RetroPortingToolKit.
11. **Legal note**: no copyrighted game data distributed; user supplies own copy; trademarks belong to their owners.

## 8. Prioritised checklist

### Blockers (decide before the first push)

1. **Decide the release model.** CI-built playable releases are not possible without committing generated game C or a disc (sections 5, option C). `CLAUDE.md` forbids it. The choices are A (setup host, locally built, not CI-supported upstream) or B (source only). Nothing else in section 5 matters until this is decided. [S]
2. **Add a licence for this repo's own files** and a `NOTICE`/third-party section. No licence file exists now ([M]). Files copied from the psxrecomp scaffold may need to follow its terms ([H]). Read the whole of `psxrecomp\LICENSE` (only the start was read here).
3. **Clean user paths and identity in tracked files** (decide, then act): 25 files hold `%USERPROFILE%\...`. The author email is in all 47 commits (no way to change without a history rewrite). If a rewrite is wanted, do it before the first push, not after. [M]
4. **The owner confirms the derived-data scope** (section 2). D8 already approves the main files; `docs/DISC_MAP.md`, `FORMATS.md`, `SYMBOLS.md`, `EXE_OVERLAYS.md` and the replay digests are not named in D8 and are not covered by an explicit decision. [S]

### Should do

5. Skim `docs/SYMBOLS.md` and `docs/FORMATS.md` for quoted game text, and `docs/CHANGELOG.md` / `SETUP.md` for first-person user notes that should not be public. [H]
6. Run the full pre-publish scan again just before the push (`git ls-files`, `git log --all --name-only`, the grep commands in section 1) and `git status` for the `psxrecomp` `m` flag. [M]
7. Mark `psxrecomp` line-ending noise: add `.gitattributes` or set the submodule's `core.autocrlf` so a user does not see a "modified" submodule. Content is identical (0 diff lines ignoring EOL). [M]
8. Decide whether to bump the `psxrecomp` pin (upstream is ahead; `958ae0e3` at audit time) or keep it. A bump needs a rebuild and a new replay baseline (T3.2 process). [M]
9. Add a `.github/workflows/ci.yml` limited to: submodule checkout (recursive), build `recompiler/` with the `RetroPorting-Toolchains` clang pack (pinned) or MSYS2 MinGW64, run `ctest`, and a docs/lint job (e.g. a script that fails if `git ls-files` includes `generated/`, `.bin`, `.cue`, `ps1_game`, `work`). No disc steps. [H]
10. Add a CI "no game data" guard script in `tools\` and run it locally and in CI. [H]
11. Pin the toolchain version in docs and CI (v1.0.14, per `docs/SETUP.md`). [S]
12. Test the whole user path on a second clean Windows machine or VM with only a disc (section 6). [H]

### Nice to have

13. Replace `<RETRO_TOOLS_DIR>\python\python.exe` in docstrings with a relative `python` or `%RETRO_TOOLS_DIR%`. [S]
14. Add `CONTRIBUTING`/issue template that says: do not attach disc dumps, BIOS files, or memory cards.
15. Create a GitHub release only after the model in item 1 is chosen; include `licenses/` per `BUNDLED_RELEASES.md` step 5. [S]
16. Consider noting the framework dependency on upstream's reorganisation (`mstan/...` vs `RetroPortingToolKit/...` URLs in upstream docs). [S]

## Commands used (reproducible)

```
git ls-files | wc -l
git log --all --name-only --format= | sort -u
git ls-files -i -c --exclude-standard
git log --all --format='%an <%ae> | %cn <%ce>' | sort | uniq -c
git grep -c -i 'localuser' -- . ':!psxrecomp' ':!recomp-ui'
git grep -n -i -E 'ghp_|github_pat|api[_-]?key|secret|token|password|AKIA|BEGIN (RSA|PRIVATE)'
git grep -n -i -E '8a75edba|bf5803d3|83988529|dc720deb'
git submodule status
git ls-remote https://github.com/RetroPortingToolKit/psxrecomp
git ls-remote https://github.com/RetroPortingToolKit/recomp-ui.git
git -C psxrecomp diff --ignore-cr-at-eol --ignore-space-at-eol
git -C psxrecomp branch -r --contains 449c31e5
```
