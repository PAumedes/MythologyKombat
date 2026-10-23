# PERF AND ENGINEERING IDEAS

Read-only analysis, 2026-10-20. No code or config was changed. Scratch script: `work\scratch\tele.py` (git-ignored).
Machine: i5-7300HQ (4C/4T), 32 GB RAM, Intel HD 630 (driver 22.20.16.4708, dated 2017-06-15) plus NVIDIA MX150 (driver 32.0.15.8278), 1080p60 panel.

Tags used on every statement:

- **[M]** measured: cites a tool output or file that exists in the repo or `work\`.
- **[S]** source-read: cites file and line (or doc) in the repo or in the `psxrecomp` submodule. Not run.
- **[H]** hypothesis: not tested. Needs the measurement named next to it.

## 1. What the existing evidence says (read this first)

1. **The internal resolution changed between the baselines and the user's current setup.** [M] `work\perf\run_V0.log` prints `internal resolution Native ... 1x requested`. `work\perf\run_T31.log` prints `internal resolution 4K (reference 240 lines): 9x requested`, `supersampling 9x (antialiasing on, texture filter bilinear)`. [M] `build\settings.toml` (written by the launcher, 2026-10-20 21:51) has `internal_resolution = "4k"`, `supersampling = 4`, `antialiasing = true`, `dynamic_resolution = false`, `vsync = "immediate"`. `settings.toml` overrides `game.toml` [S: `docs/SETUP.md` line 1282]. Runs A to G (D9 evidence) print no internal-resolution line at all, so their scale is not recorded.
2. **The user's own telemetry shows more missed vblanks at 9x.** [M] `work\scratch\tele.py` over `build\saves\diagnostics\session-*\telemetry.csv` (column `composed_internal_scale`, `host_interval_us`). Non-movie rows (`cd_xa == 0`), share of guest-vblank intervals above 33 ms:

| Session | Scale | Non-movie rows | > 33 ms | p90 / p99 (ms) | Note |
|---|---|---|---|---|---|
| `1792525023167056` | 1x | 17,484 | 78 (0.4%) | 20.8 / 22.1 | vsync on (user-reported), visible |
| `1792524829517909` | 1x | 1,265 | 10 (0.8%) | 19.9 / 26.0 | vsync off (user-reported), visible |
| `1792527693065521` | 1x | 1,676 | 9 (0.5%) | 18.6 / 23.6 | |
| `1792543875882848` | **9x** | 6,565 | **678 (10.3%)** | 33.2 / 47.0 | visible window (matches `psx_last_run_report.json`, frame 8941) |
| `1792545166792701` | 9x | 857 | 12 (1.4%) | 19.4 / 34.3 | the 40 s hidden `T31` run |

   This is a correlation across sessions with different phases and unknown vsync mode (`session.json` does not record vsync, question 222). It is a strong lead, not proof. [H] The HD 630 (24 EUs, shared memory) cannot hold a 2880x2160-class internal target plus 4x supersample and AA at 60 Hz in a visible window. Test in section 3, item 1.
3. **The CPU headroom in the FMV is thin and is not the interpreter.** [M] `tools\perf_summarize.py V0 T31 D`: FMV guest work median 830 / 827 / 776 ms per second (about 13 to 14 ms per 16.66 ms frame). [M] `run_T31.log`: `dirty=9928 insn/s 1241 dispatch/s` in the FMV, against about 33.8 M guest cycles per second. The interpreter is about 0.03% of guest instructions [H on the exact cost, M on the counts]. [M] `autocapture=0.0 to 0.1 ms/s` in every sample.
4. **Hidden-window runs say nothing about GPU load.** [S] The wall-clock pacer sleeps between frames (`pacer=` in the log) and `work guest` is host CPU time on the emulation thread. GL work is asynchronous. [M] T31 (9x) shows FMV guest work 827 ms/s against V0 (1x) 830 ms/s: no CPU difference, so any 9x cost is on the GPU or in the swap, which these logs do not measure.
5. **Power plan.** [M] `powercfg /getactivescheme` today: Ultimate Performance, AC min/max processor state 100%. [M] `docs/SETUP.md` line 1202 recorded Balanced during the D9 runs. So today's plan differs from the plan in the baselines. The i5-7300HQ clock reads 2500 MHz (base) [M, one `Get-CimInstance` sample, not under load].
6. **The submodule is dirty.** [M] `git -C psxrecomp status --short`: `generated/OpenBIOS.emitter.sha`, `OpenBIOS_dispatch.c`, `OpenBIOS_full.c` modified. [M] `build\psx_last_run_report.json`: build string `nightly-805-g449c31e5-dirty`. Reproducibility cost, see item 12.

## 2. Ranked list

Columns: benefit, evidence needed, risk, effort, needs upstream change (U), touches generated code (G). Rank is by expected benefit for the stated problem (FMV and Midway-logo dip on this laptop) divided by risk and effort.

| # | Idea | Expected benefit | Evidence / how to measure with existing tools | Risk | Effort | U | G |
|---|---|---|---|---|---|---|---|
| 1 | **Cap internal resolution and supersampling for this GPU** (try `native`, `720p`, `1080p`, and `dynamic_resolution = true`; set `supersampling` low or `antialiasing = false`) | High if section 1 item 2 holds: removes GPU-bound missed vblanks in gameplay and movies | See 3.1. A/B `tools\perf_run.ps1` is hidden-window and cannot show GPU cost. Use a visible run with the debug build and `frame_perf` (GL timer queries, `PSX_GL_PERF` [S: `gpu_gl_renderer.c` 7459]) plus `tools\session_fps.py` on the recordings | Low. Settings only. Image quality drops from 4K. | Low | No | No |
| 2 | **Done (T3.6).** **Fix the measurement baseline first**: make `tools\perf_run.ps1` record and force the video settings (it uses the player's `build\settings.toml`), and print scale, vsync mode, power plan, GPU in `run_X.meta.txt` | Makes every other number comparable. Today V0 (1x) and T31 (9x) differ silently. | Diff `meta.txt` and the `internal resolution` log line between runs | None | Low | No | No |
| 3 | **Visible-window and borderless test with vsync on** (`fullscreen` in `settings.toml`, `PSX_VSYNC=1`) | Medium. D9 was a vsync-off fix. Windowed vsync-on on Windows goes through DWM and can add a frame. Borderless or exclusive may let vsync-on hold 60 Hz and avoid the tearing risk of vsync-off. | `tools\session_fps.py` on a recording, `cd_xa != 0` rows. Compare p50/p90 of `host_interval_us` (the vsync-off sessions already show p50 12.7 to 15.4 ms and p90 about 33 ms in movies, i.e. uneven delivery) [M] | Low | Low (user plays 2 runs) | No | No |
| 4 | **GPU selection and driver**: (a) Windows Graphics settings, per-app "High performance" for `MythologyKombat.exe` (MX150), (b) update the Intel driver | Unknown. (a) The GL context is created on the HD 630 [M: `run_T31.log`]. The MX150 is far faster at 4K-class targets, at the cost of a copy to the Intel display path. (b) The 2017 driver exposes GL 3.3 only [M: log `3.3.0 - Build 22.20.16.4708`]. | Visible run with `frame_perf` GPU times on each GPU. The log line `OpenGL context created (... )` names the GPU actually used. | (a) Low. Optimus copy can add latency or cause stutter [H]. (b) Driver change is a USER step (system change). | Low | No. [S] The runtime has no `NvOptimusEnablement` or `AmdPowerXpress` export (grep of `runtime/src`, `runtime/include`, `recompiler/src`: no match), so the choice is Windows' | No |
| 5 | **Stage the overlay toolchain (Q99) and warm a KUSEG/KSEG1 shard for the BIOS exception path (Q190)** | Small per frame. Removes about 6 to 20 interpreter dispatches per frame [M: 6.06 calls and 49 insns per frame in TEMPLE, Q191; 1241 dispatch/s in FMV] | After staging, run `tools\overlay_coverage.py` and read `segment_alias_interp`. Upstream expects about 0 on a warm cache [S: `psxrecomp/docs/SEGMENT_AWARE_CODE.md` 1236 to 1262, other titles]. Compare `dirty=... insn/s` in `perf_run` logs. | Medium. Background autocompile (tcc or gcc subprocess) on a 4-core CPU could itself cause dips during play [H]. Exe-hash and cache state become part of replay identity [S: upstream says cold vs warm judge columns identical for Kula World]. Upstream `overlay_toolchain\compiler.txt` points at another developer's path (`C:\Users\Matthew\...`) [S]. | Medium | No (stage-toolchain exists in `psxrecomp/tools/release_stage.py`) [S] | No (shards are runtime output, not `generated\`) |
| 6 | **PGO build** (`PSX_PGO=generate`, train, `use`) | Unknown, likely 5 to 15% of guest work [H]. Directly addresses the 13 to 14 ms/frame FMV cost, which is in AOT code [M]. | Same route, same settings, `tools\perf_run.ps1` FMV window `workG` median, 3 runs each, plus the per-frame tail (`host_interval_us` p99) | Medium. Doc says PGO profile is currently empty [S: `docs/SETUP.md` 1015; `build\CMakeCache.txt` `PSX_PGO:STRING=` empty, `PSX_RUNTIME_IPO:BOOL=OFF`, `BUILD_LTO:BOOL=OFF`]. Every relink changes the exe hash and breaks strict replay (D14, D15). Upstream says "Do not set PSX_PGO in CI" [S: `docs/ci/templates/game-release.yml`]. Training needs the disc, local only. | High. The `pgo-train` flow builds debug-ON first, trains, then rebuilds [S: `RUNTIME_IPO_EXPERIMENT.md`]. About 2 builds of about 5 min each plus training. | No (CLI `pgo-train` exists, `psxrecomp_cli.py` 1732, 1895, 2170) | No (compile flags only). Generated C is recompiled, not edited. |
| 7 | **LTO / ThinLTO** (`-DPSX_RUNTIME_IPO=ON`) | Likely small. Upstream's own review says the incremental gain "overlaps the earlier run-to-run spread" [S: `RUNTIME_IPO_EXPERIMENT.md`]. | Combine with item 6 or measure alone. Needs repeated trials and tail latency, not mean fps. | Medium. Link time and memory grow with about 97 MB of generated C [M: `du -sh generated` = 97M]. Experimental in upstream. | Medium | No | No |
| 8 | **Audio buffer** (`[audio] buffer_ms` in `game.toml`, 30 to 500, default 180; per-game only, not read from `settings.toml`) | Low now. With vsync off the FMV has 0 underruns and fill about 170 to 200 ms [M: `perf_summarize D, T31`]. A larger value only helps if underruns return. A smaller one reduces SFX latency. | `audio_fill` and `underruns` columns in `perf_summarize.py`; debug `audio_stats`, `audio_events` [S: `TCP_COMMANDS.md`] | Low | Low | No | No |
| 9 | **Uneven frame delivery with vsync off** (judder): the wall-clock pacer lets guest vblank intervals go bursty | Smoothness. Not fixed by any setting yet. | [M] movie rows of vsync-off sessions: p50 12.7 to 15.4 ms, p90 31 to 33 ms (`tele.py`). Need the present timestamps, not guest vblank times, to know what the eye sees. `pace_state` and `frame_perf` (debug build). Try `vsync = "adaptive"` and `"vrr"` (not run, Q168) and `PSX_PRESENT_THREAD=1` / `render_thread` (Q169). | Low to medium. Render and present threads are opt-in and OpenGL only [S: `docs/RENDER_THREAD.md`]. | Low | No | No |
| 10 | **Software or Vulkan renderer** | None expected. [M] run C (`--renderer software`) gave about 50.3 Hz in the FMV, the same as OpenGL (D9 table). Vulkan is built in [M: `PSX_ENABLE_VULKAN:BOOL=ON`] but is experimental and hidden unless `offer_vulkan` [S: `config_schema.md` Video Block]. | Vulkan could be tested with `--renderer vulkan` and `frame_perf`. On the HD 630 the Vulkan driver is also old [H]. | Medium (visual bugs) | Low to try | No | No |
| 11 | **Interpreter fallbacks as such** (about 6 per frame in gameplay, about 20 per frame in the FMV) | Negligible by itself [M: about 10k insn/s]. Only the correctness side matters (is every fallback the BIOS exception path?). | `tools\overlay_interp_probe.py` already shows 2 entry PCs (`0x000027B4`, `0x0000281C`) equal to the whole counter in TEMPLE [M: Q190 finding]. Repeat per level (Q191 says other levels are open). | Low | Low | No | No |
| 12 | **Seed and static coverage growth** | Correctness and tail, not mean speed. [M] seeds 1177, analyzer functions 2322, image covered by code 74.6%, 133 unresolved indirect sites (`docs/COVERAGE.md`). `full_static_coverage_proven` is false (Q194). | `tools\collect_game_misses.py` plus `tools\grow_seeds.py` (ACCEPT only, D15). Each seed change regenerates and relinks, so it must precede any user recording (D14). | Medium. Breaks replay hash. | Medium | No | **Yes, regenerates `generated\`** (never hand-edited) |
| 13 | **Build time and incremental builds** | Developer speed only. [M] debug build about 5 min with ccache (`docs/SETUP.md` 894), static overlay objects about 1 min, relink about 2.5 s (1841). | `cmake --build ... -v` timing. ccache is already auto-enabled when found [S: `runtime.cmake` ccache block]. Verify it is on PATH: `build\CMakeCache.txt` shows no `CMAKE_C_COMPILER_LAUNCHER` line [M, not checked further]. Unity builds and `-j` are [H]. | Low | Low | No | No |
| 14 | **Startup time** | User-visible only for the first 20 s (LEGAL and Midway movies are unskippable in the log; the first sample shows `guest=231 Hz` boot burst). | No tool times time-to-first-frame. Use `host_elapsed_us` of the first rows in `telemetry.csv` (row 0 is 5.6 ms) plus the first log line timestamps from `perf_run` (add `Get-Date` wrapper). `fast_boot = false` in `settings.toml`; the source calls it a deprecated HLE boot-skip alias [S: `main.cpp` 17675]. | Low | Low | No | No |
| 15 | **Fast Loading and CD speed mods** (`psx.enhancement.fast-loading`, `psx.enhancement.cd-speed`, bundled in `build\mods\bundled\`) | Load times only. | Time a level load in telemetry (`cd_reading`, `host_elapsed_us`). The `turbo_loads` key is deprecated and ignored [S: `config_schema.md` 626 to 648]. | Medium. Changes guest timing, so replays differ. Upstream warns it is outside the parity campaign [S: `HLE_EXECUTION.md` 85]. | Low | No | No |
| 16 | **GTE SIMD** | Unknown, likely small. [S] `runtime/src/gte.cpp` has no SSE/AVX use (grep). [S] MDEC already has SSE2 IDCT and 24-bit row encode (`mdec.c` 326 to 613). No profile shows the GTE as the hotspot. | A sampling profile (Windows Performance Recorder / ETW or `xperf`) of the Release exe during the FMV and a fight. No in-repo tool does this. | High. Bit-exactness against Beetle is the project's rule [S: `RUNTIME_IPO_EXPERIMENT.md`, `FMV_IRQ_BATCHING_RFC.md`] | High | **Yes** | No |
| 17 | **Per-instruction guest cost (icache fetch, cycle charge, IRQ checks) in recompiled code** | The likely real source of the 13 to 14 ms. [H] Only a profile can say. | Same sampling profile. Upstream's RFC shows batching removed cycle charges incorrectly [S: `FMV_IRQ_BATCHING_RFC.md`]. | High | High | **Yes** | Indirectly (emitter change regenerates `generated\`) |

## 3. Detail on the top items

### 3.1 Internal resolution and GPU (items 1, 2, 4)

- Evidence on file: section 1 items 1, 2, 4. [S] 4K means S = 9 for a 240-line reference (`runtime/include/internal_resolution.h` lines 17 to 22), so a 320x240 frame becomes about 2880x2160. 1080p is S = 5, 720p is S = 3.
- The user reported "60 fps with no issue" after the first menu at the old setting [M: `docs/SETUP.md` 991], which was 1x [M: session `...167056`].
- Proposed measurement, using only existing tools:
  1. Add a copy of `build\settings.toml` per variant (the tool already reads the player's file; copy and restore by hand, USER or implementer). Variants: `native`, `720p`, `1080p`, `4k`.
  2. For each, one visible-window run of the debug build for 60 s of the same boot route (`tools\run_boot_route.py` is headless, so the GPU is not exercised; use the visible `tools\overlay_coverage.py` or a user run).
  3. Read `frame_perf` GPU scene and present times (GL timer queries exist, [S] `gpu_gl_renderer.c` 7455 to 7475) and `tele.py` percentiles.
  4. Decision rule: pick the highest setting whose non-movie `> 33 ms` share stays under 1% (the 1x baseline is 0.4 to 0.8%).
- `dynamic_resolution = true` with `dynamic_resolution_min` is the framework's own safety net [S: `QUALITY_PRESETS.md`, `config_schema.md` 792 to 803]. Currently `false` in `build\settings.toml` [M].

### 3.2 The vsync default (D9)

- [M] Vsync off gives guest 60.0 Hz in the FMV with 0 underruns (D9, `run_V0`, `run_T31`).
- [M] But the vblank cadence in vsync-off movie sessions is bursty (p50 12.7 to 15.4 ms, p90 about 33 ms). The mean is right, the distribution is not. [H] This can look like judder or tearing even at a 60.0 mean. Present-side data is needed (item 9).
- [S] "off" and "immediate" both map to 0 (`config_loader.cpp` 983, 984, 3153, 3154). The wall-clock pacer still caps the guest (D9, `main.cpp` comment above `present_effective_swap_interval`).
- Keep `off` as the default. Add `adaptive` and a borderless vsync-on run to the test list (Q168). Do not change the default without a visible-window test.

### 3.3 Overlay toolchain and interpreter fallbacks (items 5, 11)

- [M] Startup log: `tcc tier active but no bundled toolchain at ...\build\overlay_toolchain (overlay gaps -> interpreter)` (`run_T31.log`). `build\cache\SLUS-00476\` holds only `datashards` [M], so there are no `seg-kuseg` or `seg-kseg1` shards.
- [S] Upstream design: OpenBIOS patch slots in KUSEG get a KUSEG shard, and `segment_alias_interp` drops to 0 on a warm cache (`SEGMENT_AWARE_CODE.md` 770 to 785, 1213 to 1237, 1262). This was proven on other titles, not on this one.
- [M] In this game the interpreted PCs are in low RAM (`0x000027B4`, `0x0000281C`), not in overlays (Q190 finding). So the AOT overlay work (D11, T2.15 to T2.17) cannot remove them. Static overlays were not the lever here; the kernel-page shard is.
- Cost/benefit: the saving is below 0.1 ms per frame [H, from 49 instructions per frame]. The main reason to do it is determinism (no mixed tiers), not speed. Do it only if a measurement shows a tail latency tied to `dirty=` spikes (V0 shows interp up to 8,686 per second at boot [M], not in gameplay).
- Risk to note before staging: the compile subprocess competes with the game on 4 cores [H]. Do it once on a dev box, cache the shards, and do not leave autocompile running during play (`PSX_OVERLAY_AUTOCOMPILE_OFF=1` exists, [S] `SEGMENT_AWARE_CODE.md` procedure text).

### 3.4 PGO and LTO (items 6, 7)

- [M] Current flags: Release `-O3 -DNDEBUG`, `BUILD_LTO=OFF`, `PSX_RUNTIME_IPO=OFF`, `PSX_PGO=` (empty), compiler clang (`build\CMakeCache.txt`).
- Both are compile-flag changes; the generated C is not edited. Both change the exe hash, so they need a replay re-baseline (T3.2 pattern) and a fresh user recording (D14).
- Order of work: (1) measure with a sampling profile where the 13 to 14 ms goes; (2) only then PGO; (3) LTO last, as upstream says its gain is inside run-to-run noise [S].
- Measurement discipline: three runs per variant, same settings (item 2), report FMV `workG` median and `host_interval_us` p99, not mean fps. Save raw logs in `work\perf\`.

### 3.5 CI-friendly reproducibility and test automation

What can run without the disc: [S] nothing in this repo's `tests\replays` (all need the disc and the BIOS); [M] `tools\check_seeds.py`, `tools\sync_symbols.py`, `tools\seed_symbols.py` read derived files (symbols, seeds), and `tools\check_prereqs.ps1` checks the tool chain. The framework has ctest targets (two fail to link here, D1) that do not need the disc [S: `docs/SETUP.md` 226 to 227].

Proposed no-disc CI set (all [H] until built):

1. Lint and schema checks on committed derived files: `seeds\ghidra_funcs.txt` (word-aligned, in range, no duplicates), `symbols.toml` (unique valid C identifiers), `aot\overlays.json` (schema keys, `expected_records = 8`), `tests\replays\routes\*.json` (non-overlapping steps), `docs` tables. These need only text.
2. Shell and PowerShell syntax check of `tools\*.ps1` and `python -m py_compile tools\*.py`.
3. Configure-only CMake check (no `generated\`): confirms the root `CMakeLists.txt` still parses with the pinned submodules (`framework_pins.txt`). Today the project requires `generated\SLUS_004.76_dispatch.c` (`GEN_MARKER`), so it must run with `-DPSXRECOMP_REQUIRE_GAME_C=OFF` [S: `CMakeLists.txt`]; whether that configures cleanly is not tested.
4. A "self-hosted, disc-present" job on the user's machine (not GitHub-hosted): `tools\smoke_boot.py` and `tools\run_boot_route.py --expect ...` as a scheduled task. That is the only real regression test (T3.2 baseline MATCH ×2 [M]).

Not possible in hosted CI: anything that reads the disc, BIOS, `generated\` or the exe. The upstream release template assumes committed `generated\` [S: `game-release.yml`], which D3 and `CLAUDE.md` forbid, so that template is not usable as-is.

Reproducibility gaps found [M unless stated]:

- The framework submodule is dirty (three `OpenBIOS` generated files modified). A clean checkout of the pin does not reproduce the shipping exe. Record whether these are regenerated outputs and add a script to regenerate or verify them (U: no).
- `AOT_STATIC_AUDIT.json` is not byte-reproducible (`docs/SETUP.md` 1899).
- The relink changes the exe hash on every build (`docs/SETUP.md` 1287). Replay identity therefore needs the exe hash recorded, which D14 and T3.2 already do.
- `build\game.toml` and `build\settings.toml` drift from the repo copy (D9 notes, SETUP 2292). Record the effective video settings in every run (item 2).

### 3.6 Software/GL renderer options

- [M] Software renderer run C: about 50.3 Hz in the FMV with vsync on, same as OpenGL. So the renderer is not the FMV bottleneck on this machine.
- [S] GL context is 3.3 on the HD 630 [M log]. A newer Intel driver or the MX150 would give a newer GL version [H]; not needed by the runtime as far as the logs show.
- No evidence that a different renderer helps. Only test Vulkan if a GPU time problem (item 1) remains after the resolution cap.

### 3.7 Audio

- [M] `[audio] frequency = 44100`, `spu_hq = true` in `build\settings.toml`; `buffer_ms` not set, so 180 [S: Q120]. [M] The FMV in vsync-off has `audio_fill` about 170 to 200 ms and 0 underruns.
- The legacy path (`PSXRECOMP_AUDIO_LEGACY=1`) gave audio fill 0 to 13 ms and about 25 underruns/s (run E [M]). It is worse; leave it.
- No audio change is justified by the current data. Revisit if underruns return at 9x.

### 3.8 Power plan and GPU selection

- [M] Plan is Ultimate Performance on AC. Do not assume the baseline runs matched it (they say Balanced).
- [H] On battery (DC) the plan sets min processor state 5% (`powercfg /query ... PROCTHROTTLEMIN`, DC index 0x5): gameplay on battery could drop clocks. Not measured.
- For GPU selection see item 4. The registry key `HKCU\Software\Microsoft\DirectX\UserGpuPreferences` has no entry for this exe [M, empty query], so Windows uses its default (the Intel iGPU, as the log shows).

## 4. Evaluation of `docs/ENHANCEMENTS.md` (Gemini-written, UNVERIFIED)

| Claim in the file | Verdict | Basis |
|---|---|---|
| 100% static AOT gives "completely idle interpreter" | **Wrong for this game.** The fallbacks are the BIOS exception path in low RAM, not overlay code. `full_static_coverage_proven` is false. | [M] Q190 finding, Q194 |
| Zero Load Times: "Low effort, Available in PSXRecomp", `LOAD_TIME_ZERO` path in `cdrom.c` | **Wrong.** The upstream document is an exploration checklist with "no code changes". `turbo_loads` is deprecated and ignored. What exists is the pair of mods `fast-loading` and `cd-speed`. | [S] `psxrecomp/docs/LOAD_TIME_ZERO.md` 1 to 8; `config_schema.md` 626 to 648; [M] `build\mods\bundled\` |
| Lossless CD-DA tracks, `CdlPlay`/`CdlSeekL` | **Does not apply.** The disc has one data track, so no CD-DA. Music and movie audio are XA in the STR files. | [M] the `.cue` (one TRACK 01 MODE2/2352), `docs/DISC.md` line 18, `docs/FORMATS.md` 35 |
| Internal resolution scaling "Low effort / Framework Supported" | **Already on, and probably too high for this laptop.** It is a settings choice, not a task. | [M] `build\settings.toml`, `run_T31.log` |
| PGXP "Medium effort" implement `RTPS`/`RTPT` interception | **Already in the framework** (`pgxp.cpp`, bundled mod `psx.enhancement.pgxp`, `geometry_correction`, `perspective_texturing` keys, both `false` now). Effort is a toggle plus game testing, not an implementation. | [M] `build\mods\bundled`, `settings.toml`; [S] `runtime.cmake` source list |
| SIMD GTE with AVX2 as a performance item | **Unproven value.** No profile shows the GTE is hot. MDEC already uses SSE2. Bit-exactness risk. AVX2 is not guaranteed (i5-7300HQ has AVX2 but the build is generic x86-64 [H]). | [S] `gte.cpp`, `mdec.c`; no profile exists |
| Multithreading (guest / render / audio) as new work | **Partly exists.** `render_thread` and `present_thread` are opt-in, OpenGL only, and currently `false`. Not tested on this game (Q169). | [S] `docs/RENDER_THREAD.md`; [M] `settings.toml` |
| 1000 Hz raw input polling "Low effort, High impact" | **Unverified and likely small.** The game reads the pad once per vblank; the question is only at which host moment the state is latched. Whether that is already late-latched was not checked. | [H]; no source read |
| 32-bit float SPU mixing, band-limited resampling | **Partly exists**: the log prints `SPU float-shadow enabled (verified-enhancement)` and `spu_hq = true` is set. Whether they are the same features was not checked. | [M] `run_T31.log`, `settings.toml` |
| Widescreen "High effort, Planned (Phase 3)" | **Not evaluated here.** Not a performance topic. Check `docs/WIDESCREEN.md` in the submodule before planning. | not read |
| `psxrecomp/runtime/src/dirty_ram_interp.c` is only for self-modifying code or unmapped overlays | **Incomplete.** In this game it also runs the OpenBIOS exception path (Q190). | [M] Q190 |

## 5. Top 5 recommendations

1. **Test a lower internal resolution first** (items 1, 2, 4). Evidence: 9x sessions show 10.3% of non-movie vblank intervals above 33 ms against 0.4 to 0.8% at 1x. Make `perf_run.ps1` record the video settings so the next numbers are comparable.
2. **Run a visible-window A/B of vsync modes** (items 3, 9): borderless vsync on, `adaptive`, `off`; measure present cadence with `frame_perf`/`pace_state`, not only guest Hz. The current vsync-off cadence is bursty.
3. **Get a sampling profile of the Release exe** during the FMV before touching PGO, LTO or SIMD (items 6, 7, 16, 17). The 13 to 14 ms/frame is in AOT code; nothing in the repo shows where.
4. **Then try PGO (and LTO) as a flag-only change** with the 3-run discipline, and re-baseline the replay hash (T3.2 pattern). No generated code changes.
5. **Leave the overlay toolchain and interpreter fallback (Q99, Q190) for later.** The measured interpreter share is about 0.03% of guest instructions. If done, do it for determinism, warm the KUSEG shard once, and turn off autocompile during play.

Also cheap: add the no-disc lint set (3.5) and resolve the dirty-submodule question for reproducibility.

## 6. Open items created by this analysis

- Which vsync mode and which `settings.toml` were active in each telemetry session (`session.json` does not record it, existing Q222). Add `vsync` and `internal_resolution` to the run metadata.
- Whether the HD 630 is GPU-bound at 9x: needs `frame_perf` on a visible run. Not measured here.
- Whether `ccache` is active for this build: not checked beyond the cache file.

## 7. Outcome of the A/B (2026-10-22, T3.7 and T3.8)

Full numbers and method: `docs/RENDERER_AND_GPU.md` section 6. Tags: [M].

| Item | Outcome | Status |
|---|---|---|
| 1 (cap internal resolution) | 4K passes the under-1% rule on both GPUs (0.48% Intel, 0.47% MX150) on the test route. No default change. The 9x drop from the older telemetry was not reproduced (question 334). | Measured, route has no fight (question 330) |
| 2 (measurement baseline) | Done in T3.6. The A/B used copies of the exe with their own settings (`tools\perf_ab.ps1`). | Done |
| 3 and 9 (vsync and window mode) | Vsync on costs about 8 fps on Intel at 4K (51.8 against 60.0) and about 6 fps at 1x. The MX150 does not show it. Adaptive matches vsync on. Borderless fullscreen at 4K with vsync off gives 59.2 fps. Vsync off stays the default (D9). Present-side cadence (item 9) was not measured. Exclusive fullscreen was not tried (question 331). | Measured. User visual check pending (T3.8) |
| 4 (GPU choice) | The Windows per-app preference works (the log names the MX150). With vsync off the two GPUs look the same. No default change proposed. | Measured |
| 6, 7, 16, 17 (profile, PGO, LTO, SIMD) | The sampling profile (T3.9) was not run. It needs an elevated shell (question 332). | Open |

Next steps, in order: the optional fight run (question 330), then the elevated profile (T3.9, question 332). Neither changes a default by itself.
