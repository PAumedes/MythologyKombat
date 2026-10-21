# Feature Ideas & Engineering Implementations

This document outlines architectural context and engineering opportunities for **MythologyKombat** (Mortal Kombat Mythologies: Sub-Zero PS1 static recompilation), focusing on **Image Quality**, **Sound Quality**, and **Performance & Latency**.

---

## 1. Architecture Context: Recompilation vs. Runtime Emulation

To understand where improvements can be made, it helps to understand how the project is partitioned between native execution and runtime emulation:

* **Statically Recompiled (Native CPU Code):**
  * The game's MIPS R3000A machine code from the disc executable (`SLUS_004.76`) and its overlays (`.OVR`) are translated ahead-of-time (AOT) into native C code (in `aot/` and `generated/`).
  * This code is compiled using MSVC/Clang directly into native x86_64 machine instructions. Your host CPU executes game logic directly without any CPU interpreter or JIT overhead.
* **Transient Fallback Interpreter:**
  * Located in `psxrecomp/runtime/src/dirty_ram_interp.c`. Used only as a fallback safety net for self-modifying code or unmapped overlays until they are statically captured.
* **Emulated Subsystems (Hardware Runtime):**
  * Because modern PCs do not have PS1 hardware, the custom chips and I/O controllers are simulated in software under `psxrecomp/runtime/src/`:
    * **GPU:** `gpu.c`, `render_pass.c`, `shaders/` (translates PS1 primitives to Vulkan / OpenGL / DirectX via SDL3).
    * **SPU:** `spu.c` (decodes 24 ADPCM hardware voices, reverb, volume envelopes to SDL audio).
    * **CD-ROM:** `cdrom.c` (emulates sector read timing, seek delays, and drive interrupts).
    * **DMA & Timers:** `dma.c`, `timers.c` (root counters and 7 DMA channels).
    * **SIO:** `sio.c` (controller and memory card serial protocol).
    * **GTE (COP2):** Math functions in C calculating vector-matrix operations and perspective projection.
    * **BIOS:** OpenBIOS or high-level BIOS emulation in `bios_hle.c`.

---

## 2. Quick Reference: Code Actions & Technical Impacts

| Feature | Target Files | Code Action | Result / Impact |
| :--- | :--- | :--- | :--- |
| **PGXP Sub-Pixel Precision** | GTE routines, `render_pass.c` | Intercept `RTPS`/`RTPT`, cache 32-bit float vertices, pass $1/w$ to shaders | Eliminates polygon wobble/jitter and affine texture warping |
| **Internal Resolution Scaling** | `render_pass.c`, shaders | Upscale off-screen render targets (2x–16x / up to 4K/8K) | Ultra-sharp rendering without blurring 2D pixel alignment |
| **True Widescreen (16:9 / 21:9)** | `ws_aspect_cone_math.c`, `render_pass_projection.cpp` | Adjust horizontal FOV projection, widen scissor box, patch cull checks | Modern aspect ratios without image stretching or black bars |
| **De-Dithering & 32-Bit Color** | GP0 dispatch, present shaders | Disable 15-bit RGB555 4×4 dither matrix, output to 32-bit RGBA8888 / FP16 | Eliminates gradient mesh patterns and color banding |
| **HD Texture Replacement** | `duckstation_texture_pack.cpp` | Hash VRAM pages via xxHash64, bind external high-res PNG/DDS assets | Replaces low-res textures with HD community texture packs |
| **Band-Limited SPU Resampling** | `spu.c` | Replace 4-point Gaussian table with band-limited sinc / cubic spline interpolation | Removes high-frequency aliasing and muffling on pitched sounds |
| **32-Bit Float SPU Mixing** | `spu.c`, `recomp_audio_drc.h` | Sum 24 voices in 32-bit float with dynamic range compression | Prevents harsh digital clipping during loud combat hits/explosions |
| **High-Fidelity Reverb** | `spu.c` | Route reverb wet send to modern algorithmic (Freeverb/FDN) or convolution engine | Cleans up metallic, low-memory PS1 hardware reverb |
| **Lossless CD-DA Audio** | `cdrom.c` | Hook `CdlPlay`/`CdlSeekL` to stream external FLAC/WAV audio tracks | Lossless remastered soundtrack with sample-accurate loop points |
| **100% Static AOT Coverage** | `aot/overlays.json`, `CMakeLists.txt` | Fully map all `.OVR` overlays, link via `GAME_OVERLAY_STATIC_C` | Completely idle interpreter; 100% native CPU execution |
| **Zero Load Times (`LOAD_TIME_ZERO`)** | `cdrom.c` | Pre-cache disc sectors in host RAM, service read DMA requests instantly | Instant level loads, bypassing 2x CD-ROM spin-up delays |
| **SIMD Vectorization** | GTE math routines | Rewrite vector/matrix transformations using AVX2 / SSE4.1 / NEON intrinsics | High-throughput geometry processing |
| **1000 Hz Raw Input Polling** | `sio.c`, input thread | Decouple gamepad polling from 60 Hz VBlank, feed latest state at 1000 Hz | Minimum possible input latency for fighting game inputs |

---

## 3. Deep-Dive: Image Quality Enhancements

### 3.1 Precision Geometry Transform Pipeline (PGXP)
* **The Problem:** The PS1 GPU and Geometry Transformation Engine (GTE) use 16-bit fixed-point arithmetic without sub-pixel precision. Vertices snap to integer pixel grids, producing the characteristic PS1 "wobble" and polygon jitter. Furthermore, the PS1 lacks perspective-correct texture mapping (affine texture mapping only), causing textures to warp as triangles rotate.
* **Engineering Implementation:**
  * **Vertex Precision Extension:** Intercept GTE transform instructions (`RTPS`, `RTPT`) and maintain a parallel 32-bit floating-point coordinate cache for vertices.
  * **Perspective Division ($W$ coordinate):** Store reciprocal depth ($1/w$) during projection and pass it down the rasterization pipeline to fragment shaders.
  * **Perspective-Correct UVs:** In the shader, interpolate $(u/w, v/w, 1/w)$ rather than linear $(u, v)$ to eliminate texture swimming and shearing on 3D geometry and backgrounds.

### 3.2 Internal Resolution Upscaling (Up to 4K / 8K)
* **The Problem:** The native PS1 framebuffer operates at 320×240 (or 512×240). Running on modern displays results in blurriness or extreme pixelation.
* **Engineering Implementation:**
  * In `psxrecomp/runtime/src/render_pass.c` and OpenGL/Vulkan renderers, allocate off-screen render targets scaled by an integer multiple (2x, 4x, 8x, up to 16x for 4K/8K).
  * Scale vertex positions while preserving PS1 integer coordinate rules for 2D sprites to avoid seam artifacts and texture misalignment.

### 3.3 True Widescreen & Ultrawide (16:9, 21:9, 32:9)
* **The Problem:** Stretching the 4:3 image causes distortion; simple pillarboxing leaves large black bars on modern monitors.
* **Engineering Implementation:**
  * **Projection Expansion:** Utilize `ws_aspect_cone_math.c` and `render_pass_projection.cpp` to adjust the horizontal Field of View (FOV) ratio:
    $$\tan\left(\frac{\text{FOV}_{\text{wide}}}{2}\right) = \tan\left(\frac{\text{FOV}_{4:3}}{2}\right) \times \frac{\text{Aspect}_{\text{target}}}{4/3}$$
  * **Scissor Rect & Frustum Expansion:** Widen the GPU scissor box so primitives rendered outside the original 320px boundary are not clipped.
  * **Cull Patching:** Identify and hook the game's out-of-bounds visibility culling routines so off-screen sprites/enemies do not pop in abruptly.
  * **HUD Anchoring:** Anchor 2D HUD elements (health bars, inventory icons, dialogue prompts) to screen corners or keep them bound to a 4:3 safe zone.

### 3.4 De-Dithering & 32-Bit True Color Output
* **The Problem:** The PS1 outputs 15-bit RGB555 color with a 4×4 ordered dithering pattern to mask color banding, creating a visible mesh pattern on gradients.
* **Engineering Implementation:**
  * **Dither Removal:** Disable the hardware dither flag in GP0 draw commands or implement a post-processing de-dither filter that reconstructs smooth gradients.
  * **32-Bit Framebuffer:** Upgrade the intermediate presentation surface to 32-bit RGBA8888 or 16-bit floating point (FP16) to eliminate internal color quantization banding.

### 3.5 High-Resolution Texture Replacement
* **The Problem:** In-game textures and sprites are heavily downsampled to fit the PS1's 1 MB VRAM.
* **Engineering Implementation:**
  * Integrate the DuckStation-compatible texture replacement pipeline (`duckstation_texture_pack.cpp`).
  * Hash active VRAM texture pages and CLUT palettes using xxHash64.
  * Intercept draw commands matching the hash and bind high-resolution external PNG/DDS textures.

### 3.6 CRT Simulation & Post-Processing Shaders
* **The Problem:** PS1 240p pixel art was designed to be viewed on CRT monitors with phosphor bloom, scanlines, and shadow masks.
* **Engineering Implementation:**
  * Integrate lightweight post-processing shaders (e.g., CRT-Easymode, scanlines, bloom, subtle chromatic aberration, and color correction).

---

## 4. Deep-Dive: Sound Quality Enhancements

### 4.1 Band-Limited Resampling & Sinc/Spline Interpolation
* **The Problem:** The PS1 SPU decodes 4-bit ADPCM into 16-bit PCM at 44.1 kHz using a hardware 4-point Gaussian interpolation filter. While smooth, it rolls off high frequencies and introduces aliasing when sounds are pitch-shifted.
* **Engineering Implementation:**
  * In `spu.c`, replace the fixed Gaussian filter table with band-limited sinc interpolation, Catmull-Rom cubic spline, or Hermite interpolation.
  * Produces crisper high-frequency transients for fighting impacts, voice clips, and ambient sound effects.

### 4.2 32-Bit Floating-Point Voice Mixing & Dynamic Range Control (DRC)
* **The Problem:** Original hardware sums all 24 voice channels into a 16-bit integer accumulator. Loud, simultaneous sound effects (explosions, martial arts impacts, voice screams) frequently saturate the accumulator, causing clipping distortion.
* **Engineering Implementation:**
  * Mix all 24 voice channels in 32-bit floating-point space (`float`).
  * Implement an audio limiter / DRC (`recomp_audio_drc.h`) before feeding the SDL3 audio stream to prevent digital clipping while preserving dynamic range.

### 4.3 High-Fidelity Algorithmic & Convolution Reverb
* **The Problem:** PS1 hardware reverb was restricted by a small buffer inside the 512 KB SPU RAM, resulting in a metallic, low-density reverberation.
* **Engineering Implementation:**
  * Intercept the SPU reverb register configuration parameters (`SPU_dAPF1`, `SPU_mAPF1`, comb filter delays).
  * Route the reverb wet send into a high-density modern algorithmic reverb (e.g., Freeverb, FDN) or impulse response (IR) convolution engine.

### 4.4 Lossless CD-DA Audio Tracks & Seamless Looping
* **The Problem:** MK Mythologies relies on Redbook CD-DA tracks streamed from the disc, which can suffer from seek pauses or abrupt loop restarts.
* **Engineering Implementation:**
  * Intercept CD-ROM audio commands (`CdlPlay`, `CdlSeekL`) in `cdrom.c`.
  * Stream remastered lossless FLAC / WAV audio files with sample-accurate loop markers and configurable crossfading.

### 4.5 Positional 3D Audio (HRTF / Spatializer)
* **The Problem:** In-game audio is mixed to simple stereo left/right panning.
* **Engineering Implementation:**
  * Identify game functions that update entity coordinates (Sub-Zero, enemies, stage hazards).
  * Expose entity 3D coordinates to an OpenAL Soft or SDL3 3D audio spatializer with Head-Related Transfer Function (HRTF) support.

---

## 5. Deep-Dive: Performance & Latency Optimizations

### 5.1 100% Ahead-Of-Time (AOT) Recompilation Coverage
* **The Problem:** Any code path that hits dynamic RAM or an unmapped overlay falls back to the MIPS interpreter (`dirty_ram_interp.c`).
* **Engineering Implementation:**
  * Complete full symbol and overlay extraction in `aot/overlays.json` for all `.OVR` files (TEMPLE, EARTH, WIND, WATER, PRISON, FIRE, BRIDGE, FORTRESS).
  * Compile all overlay shards statically via `GAME_OVERLAY_STATIC_C` in `CMakeLists.txt`.
  * Result: 0% interpreter fallback during gameplay; 100% native x64 CPU execution.

### 5.2 Zero-Seek CD-ROM (Load Time Zero)
* **The Problem:** Original disc reads simulate the mechanical 2x CD-ROM drive (300 KB/s transfer rate, seek delays of 200–500ms).
* **Engineering Implementation:**
  * In `cdrom.c`, implement the `LOAD_TIME_ZERO` path: pre-cache disc sectors directly in host RAM and service read requests instantly (subject to guest DMA cycle safety).
  * Level transitions and overlay swaps become instantaneous.

### 5.3 Asynchronous Multithreading (Render / Audio / Logic)
* **The Problem:** Running CPU logic, GPU draw call translation, and audio mixing on a single main thread risks micro-stutter when complex scenes are submitted.
* **Engineering Implementation:**
  * **Decoupled Architecture:**
    1. **Guest Thread:** Runs recompiled MIPS code and peripheral registers.
    2. **Render Thread (`render_thread.c`):** Consumes draw packets via a lockless ring buffer and talks to the modern graphics API.
    3. **Audio Thread:** Serves SDL3 audio callbacks asynchronously without blocking game logic.

### 5.4 SIMD Intrinsics for GTE Operations
* **The Problem:** Vector transformations, lighting dot products, and perspective calculations are called thousands of times per frame.
* **Engineering Implementation:**
  * Optimize recompiled GTE vector-matrix routines using AVX2 / SSE4.1 / NEON intrinsics to process coordinates and color vectors in parallel.

### 5.5 1000 Hz Low-Latency Input Polling
* **The Problem:** PS1 games typically poll controllers once per VBlank frame (16.6ms at 60 Hz, or 33.3ms at 30 Hz), creating noticeable input latency.
* **Engineering Implementation:**
  * Decouple SDL3 gamepad polling from VBlank.
  * Poll controller inputs on an independent high-frequency timer (up to 1000 Hz / 1ms).
  * Feed the most recent input state into the emulated SIO registers immediately before the game's polling routine executes.

---

## 6. Implementation Priority Matrix

| Feature | Category | Effort | Impact | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Complete AOT Static Overlays** | Performance | Medium | High | In Progress (Phase 2 Done) |
| **Zero Load Times (`LOAD_TIME_ZERO`)** | Performance | Low | High | Available in PSXRecomp |
| **PGXP (Anti-Jitter & Correct UVs)** | Image Quality | Medium | Very High | Framework Supported |
| **Internal Resolution Scaling (4K)** | Image Quality | Low | High | Framework Supported |
| **Widescreen FOV & Frustum Hack** | Image Quality | High | Very High | Planned (Phase 3) |
| **Band-Limited SPU Resampling** | Sound Quality | Medium | Medium | Framework Supported |
| **32-Bit Float SPU Mixing (Anti-Clip)**| Sound Quality | Low | Medium | Framework Supported |
| **DuckStation Texture Replacement** | Image Quality | Medium | High | Framework Supported |
| **High-Polling Raw Input (Low-Lag)** | Latency | Low | High | Planned |
