# RENDERER AND GPU: why OpenGL on the Intel GPU

Read-only research, 2026-10-20. No code, config or system setting was changed. Tags: [M] measured (log, file or query output on this machine), [S] source-read (file:line), [H] hypothesis.

Question: why does the game run on OpenGL on the Intel HD 630, and would DX12 or Vulkan on the GeForce MX150 be better?

## Short answer

1. There is no DX12 or D3D11 renderer. The runtime has Software, OpenGL and an experimental Vulkan backend [S].
2. Vulkan is not usable in this build: the exe contains the inert stub (no Vulkan SDK or glslc on the machine), and the launcher hides it anyway [M/S, section 1].
3. The Intel GPU is chosen by Windows, not by the game. The exe has no NVIDIA/AMD high-performance export and no per-app preference exists, so Windows gives the OpenGL context to the iGPU [M/S, section 2]. This is fixable without any code change, with a per-app Windows setting (a USER step).
4. Whether the MX150 is faster is not yet measured. All existing GPU-relevant data is from hidden-window runs that cannot see GPU cost (section 3). A visible A/B is needed (section 4).

## 1. Renderers offered

| Item | Finding | Tag |
|---|---|---|
| Renderer values | `--renderer software|opengl|vulkan` maps to 0/1/2 | S `psxrecomp/runtime/src/main.cpp:17490-17495` |
| Launcher labels | `"Software"`, `"OpenGL (Recommended)"`, `"Vulkan"`; the list has 3 entries only if `vulkan_offered`, else 2 | S `main.cpp:16317-16321`, `16566` |
| What "Recommended" means | A label the PSX host puts on OpenGL. The imgui launcher draws the label verbatim and shows the host's own `renderer_note` below the combo; it does not define maturity. Comment at `recomp-ui/src/common/backends/imgui/launcher_imgui.cpp:4101-4119` (the "experimental" text there is an example of a longer host label closing to "OpenGL (exper"). The model defaults to the label containing "OpenGL" | S `launcher_model.c:2039-2049` |
| Vulkan visibility | Hidden unless `game.toml [video] offer_vulkan = true`. This game's `game.toml` has only `renderer = "opengl"`, `aspect_ratio`, `vsync` under `[video]` (lines 42-45), so Vulkan is not offered. A settings.toml value of Vulkan is downgraded to OpenGL when not offered | S `psxrecomp/docs/config_schema.md:677-686`; `main.cpp:18356-18362`; M `game.toml` |
| Upstream status of Vulkan | "Experimental runtime choice". Upstream 4:3 test matrix: Vulkan YELLOW on every title tested (sluggish FMV, slowdown, HUD bug), "OpenGL 4:3 is the strong, shippable path on all titles" | S `psxrecomp/docs/ENHANCEMENTS.md:195-216` |
| Upstream audit | Vulkan is "substantially implemented" but needs a separate qualification track; "not a recommendation to switch users away from OpenGL"; OpenGL is the primary renderer and its acceptance is mandatory | S `psxrecomp/docs/performance/RUNTIME_AUDIT.md:74-102`; `PERFORMANCE_CAMPAIGN.md:11` |
| Vulkan limits | Software and Vulkan stop at 4x supersampling; render thread is OpenGL only; Vulkan lacks `wide_dump_full`; netplay forces software | S `config_schema.md:950, 995`; `RUNTIME_AUDIT.md:89-95` |
| Vulkan in this exe | Not compiled in. CMake cache has `PSX_ENABLE_VULKAN=ON` but that only requests it; `PSX_HAVE_VULKAN` is set only if SDK headers and `glslc` are found (`runtime.cmake:2442-2453`), else `gpu_vk_renderer.c:37-52` compiles an inert stub. This machine has no `VULKAN_SDK`, no `glslc`, no `C:\VulkanSDK`; `build.ninja` has no `PSX_HAVE_VULKAN` define; `build\MythologyKombat.exe` has none of the real backend's strings (`no Vulkan physical devices`, `vulkan: device`) while it does contain the OpenGL ones | M (file searches on `build.ninja`, `strings`-style grep of the exe); conclusion is strong but not a run |
| Vulkan device pick (if it were built) | Prefers a discrete GPU, so on this laptop Vulkan would pick the MX150 by itself | S `gpu_vk_renderer.c:782-808` |
| D3D11/D3D12/Metal | No such backend in the runtime. SDL render-driver hints exist only for the SDL 2D fallback and are set to `opengl` | S `main.cpp:2778, 21111-21125` |
| Upstream backend-choice guidance | `docs/SDL_BACKENDS.md` is about SDL2 vs SDL3 only (parity result, "not claims that one SDL generation makes emulation faster"). Its Vulkan smoke run was on an RTX 3080 Ti, not a comparative performance claim | S `psxrecomp/docs/SDL_BACKENDS.md` |

So "DX12 or Vulkan on the MX150" is not an available option. The real question is OpenGL on Intel versus OpenGL on the MX150.

## 2. How the GPU is chosen on Windows

- The log names the GPU that got the context: `psxrecomp: OpenGL context created (3.3.0 - Build 22.20.16.4708; Intel(R) HD Graphics 630)` in every run A to G, V0, T31, T36, T36b [M: `work\perf\run_T31.log:17`, same line in the other `work\perf\run_*.log`]. T31 also prints `GL GPU pipeline ready (internal scale 9x ...)` on that Intel GPU [M: line 18].
- Requested context is core 3.3 (4.6 only for OpenXR builds) [S `main.cpp:2447-2476`], so the old Intel driver is not what limits the context version; it is exactly 3.3.
- GPU facts [M: `work\perf\run_T36b.meta.txt`, `Win32_VideoController`]: Intel HD Graphics 630, driver 22.20.16.4708, dated 2017-06-15; NVIDIA GeForce MX150, driver 32.0.15.8278, dated 2026-06-24. Power plan Ultimate Performance.
- The exe does not ask for the NVIDIA GPU. No `NvOptimusEnablement` or `AmdPowerXpressRequestHighPerformance` exists anywhere in the runtime source or in the built exe [S: grep of `psxrecomp/runtime`, `recomp-ui/src`, `CMakeLists.txt`, `patches/` returns no match; M: `grep -ac NvOptimusEnablement build\MythologyKombat.exe` = 0]. Only `SDL_HINT_WINDOWS_DPI_*`, joystick and render-scale hints are set [S `main.cpp:18974-18978, 20810-20844`]; none selects an adapter.
- With no export and no override, an Optimus laptop gives a plain OpenGL app to the iGPU. Windows' per-app preference is the supported override. `HKCU\Software\Microsoft\DirectX\UserGpuPreferences` has no entry for this exe [M, from the earlier query recorded in `docs/PERF_AND_ENGINEERING_IDEAS.md:126`; the USER task below re-checks it].
- Side effect of the MX150 on Optimus: its frames are copied across to the Intel-driven display path. That copy costs bandwidth and can add a frame of latency or stutter, more so with vsync off in a window [H].

## 3. How GPU-bound is this workload

- 1x (about 320x240 internal): at 1x the sessions have 0.4 to 0.8 percent of non-movie vblank intervals above 33 ms, p99 22 to 26 ms [M: table in `docs/PERF_AND_ENGINEERING_IDEAS.md` section 1 item 2, computed from `build\saves\diagnostics\session-*\telemetry.csv`]. Nothing there points at the GPU.
- 4K, 9x (about 2880x2160, plus 4x supersample and AA per `build\settings.toml`): the one visible 9x session has 10.3 percent above 33 ms (p90 33.2, p99 47.0 ms); the 40 s hidden T31 session has only 1.4 percent [M, same table]. Different phases and unknown vsync; correlation only, not proof.
- CPU is not the difference: FMV guest work is about 830 ms per second at both 1x (V0) and 9x (T31) [M, `tools\perf_summarize.py V0 T31 D`], and the GL submission cost in the log is about 0 to 3 ms per second (`cpu=`, `tex=`, `draw=`) [M `run_T31.log`]. So any 9x cost is on the GPU or in the swap, which the logs do not measure.
- `tools\perf_run.ps1` uses `--hidden-window` and records `no visible swap chain, GPU present cost not measured` in its meta [S `tools/perf_run.ps1:36, 58`]. Hidden runs therefore cannot answer GPU-bound questions. No `frame_perf` GPU time exists for this machine: those GL timer queries are compiled out of Release builds (`gpu_gl_renderer.c:7378-7392`, enabled by `PSX_GL_PERF` at `7459` in a diagnostics build) [S].
- Hypothesis [H]: an HD 630 (24 EUs, shared memory) is the bottleneck at 9x with 4x supersampling and AA; the MX150 (384 CUDA cores, dedicated GDDR5) should handle that better, minus the Optimus copy. Not measured. Native 1x is almost certainly fine on either.
- Neither the MX150 nor the Intel GPU should be needed at all at 1x or 720p; the better first lever is the resolution setting (see `docs/PERF_AND_ENGINEERING_IDEAS.md` item 1).

## 4. Measured A/B plan (Intel vs MX150, 1x vs 4K)

Constraint: hidden-window `perf_run.ps1` runs do not exercise the swap chain, so they can confirm which GPU is used and the CPU side, but not GPU cost. The deciding data must come from a visible run read with `tools\perf_telemetry.py`. Everything below uses existing tools; nothing is added to the repo.

Variants (4 runs, same route each time, about 90 s covering the first FMV and then the menu or first gameplay; keep power plan, AC, window size and vsync identical):

| Run | GPU | Video setting |
|---|---|---|
| I1 | Intel (no per-app entry) | `internal_resolution = "native"`, `supersampling = 1` |
| N1 | MX150 (per-app High performance) | same as I1 |
| I4 | Intel | `internal_resolution = "4k"`, `supersampling = 4` (current) |
| N4 | MX150 | same as I4 |

Per run:
1. Edit `build\settings.toml` `[video]` for the variant (`internal_resolution`, `supersampling`; leave `vsync`, `window_width`, `renderer` alone; back up the file first: `Copy-Item build\settings.toml work\perf\settings.toml.bak`).
2. Start the game visibly from `<REPO_ROOT>\build`: `.\MythologyKombat.exe --no-launcher --disc "<REPO_ROOT>\ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue" --game game.toml` (or via the launcher), play the same route, quit normally.
3. Confirm the GPU in the console or log: the line `OpenGL context created (... ; <GPU name>)` must show the intended GPU. If a hidden check is wanted: `powershell -File tools\perf_run.ps1 -Name I4chk -Seconds 20` and `Select-String 'OpenGL context created' work\perf\run_I4chk.log` (does not measure GPU time).
4. Read the newest session: `python -I tools\perf_telemetry.py build\saves\diagnostics\session-<newest>` and for all four: `python -I tools\perf_telemetry.py <I1> <N1> <I4> <N4>`. Compare, per group (all, movie `cd_xa != 0`, non-movie): p50, p90, p99, count above 33 ms, share above 33 ms.
5. Optional GPU-time source: a debug build with `PSX_GL_PERF=1` (see `work\build-dbg`) reports true GPU scene and present time through the debug server `frame_perf` command (`psxrecomp/docs/TCP_COMMANDS.md:626`). Use this only if telemetry percentiles are ambiguous.

Decision rule: the MX150 is "better" at 4K only if the non-movie share above 33 ms drops clearly (from about 10 percent toward under 1 percent, the 1x level) and p99 falls with no new stutter; if N1 is worse than I1, the Optimus copy is costing more than it gains at low resolution and the preference should be applied only at high resolution (or not at all). Run each variant twice if the first two results differ by less than the 1x spread (0.4 to 0.8 percent).

### Exact USER commands: set the per-app GPU preference

Executable: `<REPO_ROOT>\build\MythologyKombat.exe`. Close the game before changing; the preference applies to the next launch.

Settings UI (preferred): Settings > System > Display > Graphics > "Add desktop app" > Browse > select the exe above > Add > click the entry > Options > choose "High performance" (NVIDIA GeForce MX150) > Save. To go back to the Intel GPU choose "Power saving"; to return to the default, Remove the entry.

Registry (equivalent, PowerShell, no admin needed, it is per-user):

```powershell
# Check current state (empty output means no entry)
Get-ItemProperty 'HKCU:\Software\Microsoft\DirectX\UserGpuPreferences' -ErrorAction SilentlyContinue |
  Select-Object '<REPO_ROOT>\build\MythologyKombat.exe'

# Set: GpuPreference=2 is High performance (the MX150); 1 is Power saving (Intel); 0 is "let Windows decide"
New-Item -Path 'HKCU:\Software\Microsoft\DirectX' -Name 'UserGpuPreferences' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\DirectX\UserGpuPreferences' `
  -Name '<REPO_ROOT>\build\MythologyKombat.exe' -Value 'GpuPreference=2;'

# Revert (removes only this exe's entry)
Remove-ItemProperty -Path 'HKCU:\Software\Microsoft\DirectX\UserGpuPreferences' `
  -Name '<REPO_ROOT>\build\MythologyKombat.exe' -ErrorAction SilentlyContinue
```

Notes: the entry is keyed by the exact exe path, so a rebuilt exe at the same path keeps the setting but a moved or renamed exe does not. The per-app list may also be reachable through the NVIDIA Control Panel (Manage 3D settings > Program Settings), which does the same job for this app. After the A/B, revert with the commands above (or "Remove" in the UI) and restore `build\settings.toml` from the backup unless the user chooses to keep the winner.

## 5. Would a Windows high-performance export need an upstream change?

- It is a few lines compiled into the exe: `__declspec(dllexport) DWORD NvOptimusEnablement = 1;` and `__declspec(dllexport) int AmdPowerXpressRequestHighPerformance = 1;`. They must be in the final executable's own object files, not in a static library, or the linker drops them.
- The runtime has no such export today [S/M, section 2], and the game exe is built from `psxrecomp/runtime/src/main.cpp` plus our `CMakeLists.txt` (framework submodule). So it would be either an upstream change in the runtime (best, behind an option such as a game.toml `[video] prefer_discrete_gpu`, and they are noncommercial-licensed so it needs coordination), or a local patch kept in `patches\` (currently holds only `launcher\`) applied to the submodule or a tiny extra translation unit added to our top-level `CMakeLists.txt` target. [H] A small extra `.c` file in our own `CMakeLists.txt` is the least invasive since it touches no submodule file, provided the object is linked into the exe directly. Not implemented, not verified that it takes effect through the static link.
- Trade-off: the export forces the discrete GPU for all users, including those who would prefer the iGPU's lower latency or power. Windows' per-app setting overrides it either way. For a shipped port a per-game option is better than a hardcoded export.
- Any such change alters the exe hash, which affects strict replay identity (D14, D15 in `docs/DECISIONS.md`).

## Recommendation

1. Do not pursue DX12. There is no such backend, and writing one is far outside scope.
2. Do not pursue Vulkan for performance now. It is not built into this exe (needs the Vulkan SDK and `glslc` to rebuild), the launcher hides it, upstream rates it YELLOW on every title, and it caps supersampling at 4x. It would pick the MX150 automatically, but that is its only advantage here.
3. Do run the OpenGL Intel vs MX150 A/B in section 4 as a USER task. It is a reversible per-user setting, needs no code, and answers the question with data. Expect the MX150 to help only at 4K with supersampling; at 1x either GPU should be fine.
4. In parallel the cheapest fix for stutter at 4K is lowering internal resolution or supersampling or enabling `dynamic_resolution` (`docs/PERF_AND_ENGINEERING_IDEAS.md` item 1), which is independent of the GPU choice.
5. Only if the MX150 wins and the port is to be shared, add the high-performance export as an option (upstream-first), instead of relying on each user's Windows setting.

## Open items

- Confirm that the Vulkan backend is a stub in this exe by running it once with `--renderer vulkan` and reading the log (expected: fallback to software or OpenGL, no `vulkan: device` line). Not run, because this research was read-only.
- Whether the CLI `--renderer vulkan` bypasses the `offer_vulkan` gate (the gate is visible only in the settings.toml path, `main.cpp:18357`). Not verified.
- Session telemetry does not record vsync mode or GPU used (see question 222 in `docs/OPEN_QUESTIONS.md`); record both in each A/B run by hand.
- The 9x (4K) telemetry drop of 10.3 percent above 33 ms (section 3) was not reproduced in the 2026-10-22 A/B (section 6). Question 334 in `docs/OPEN_QUESTIONS.md`.

## 6. Results: visible A/B, Intel vs MX150, 1x vs 4K (2026-10-22)

Tags as above. Method and scripts: `tools\perf_ab.ps1`, `tools\perf_ab_matrix.ps1`, `tools\perf_ab_gpu.ps1`, `tools\perf_ab_summary.py`. Results are under `work\perf_ab\` (git-ignored). Run the summary with `<RETRO_TOOLS_DIR>\python\python.exe -I tools\perf_ab_summary.py`.

Method [M]:

- The copy of the 0.1.0 release exe runs in its own folder, with its own `settings.toml`. That file is derived from the video keys only. `[disc]` and `[memcard]` are removed, and `--memcard-dir work\perf_ab\saves` is used.
- The recorder is enabled only in the copy's manifest. The original is kept as `manifest.toml.orig`.
- Vsync is set per run by the environment variable `PSX_VSYNC` (0 off, 1 on, -1 adaptive).
- Each run lasts 75 s. The first 8 s are skipped.
- The route is boot, the movie intros (`cd_xa != 0`), then title and attract. It is the same route each time. It has no fight.
- Three interleaved rounds. The Ultimate Performance power plan was active.
- Avg fps is 1000 divided by the mean host interval. Table values are the median of 3 runs.

Table (median of 3) [M]:

| Run | GPU | Avg fps | p99 (ms) | Non-movie share above 33 ms |
|---|---|---|---|---|
| 1x, vsync off | Intel HD 630 | 58.7 | 36.4 | 0.00% |
| 2x, vsync off | Intel HD 630 | 59.6 | 37.3 | 0.00% |
| 3x (720p), vsync off | Intel HD 630 | 59.2 | 37.3 | 0.00% |
| 4K (9x), vsync off | Intel HD 630 | 60.0 | 36.3 | 0.48% |
| 4K, vsync off, borderless fullscreen | Intel HD 630 | 59.2 | 36.1 | 0.48% |
| 4K, vsync on | Intel HD 630 | 51.8 | 38.9 | 0.00% (13.55% of all frames above 33 ms) |
| 4K, adaptive | Intel HD 630 | 51.7 | 39.0 | not in report |
| 1x, vsync on | Intel HD 630 | 52.3 | 38.7 | not in report |
| 1x, vsync off | MX150 | 59.7 | 36.9 | 0.89% |
| 2x, vsync off | MX150 | 59.8 | 36.4 | 0.00% |
| 4K, vsync off | MX150 | 58.6 | 37.0 | 0.47% |
| 4K, vsync on | MX150 | 59.5 | 36.7 | 0.95% |

Which GPU ran [M]: the startup log shows `Intel(R) HD Graphics 630` (OpenGL 3.3.0, driver Build 22.20.16.4708) on the default run. With the Windows per-app preference `GpuPreference=2;` set on the copy exe, the log shows `NVIDIA GeForce MX150` (OpenGL 3.3.0 NVIDIA 582.78). So OpenGL honours the Windows preference.

The preference key `HKCU\Software\Microsoft\DirectX\UserGpuPreferences` did not exist before the test. The test created it for the copy exe path only. The entry was deleted afterwards, and the deletion was checked.

Findings [M, from the table]:

1. Internal resolution makes no measurable difference on this route. 4K passes the under-1% rule on both GPUs (0.48% Intel, 0.47% MX150). So the default does not change.
2. Vsync on costs about 8 fps on the Intel GPU (51.8 against 60.0 at 4K). It costs about 6 fps at 1x too (52.3 against 58.7). So it is a frame pacing effect, not GPU load. The MX150 does not show it (59.5 at 4K). Vsync off stays the default (D9). The data is consistent with D9.
3. With vsync off, Intel and MX150 look the same (58 to 60 fps, p99 36 to 37 ms).
4. Adaptive vsync on Intel (51.7 fps) behaves like vsync on.
5. The earlier 10 percent figure at 9x (section 3, telemetry from older sessions) was not reproduced here. At 4K with vsync off the share is 0.48%.

Caveats [M]:

- The telemetry is host vblank intervals. There is no GPU timer in the Release build, so GPU cost is not measured directly.
- One route only, with no fight. Gameplay at 4K is not measured (question 330 in `docs/OPEN_QUESTIONS.md`).
- Run-to-run p99 varies from 33 to 53 ms. Rare single spikes reach 789 ms. Those are single events, not a trend.
- Exclusive fullscreen was not tried (question 331).
- What the player sees (tearing, stutter) is a USER step (T3.7, T3.8). It is not in this report.
