# Replay infrastructure

Frame-exact input routes and expected state digests for the debug build. Driver: `tools\run_boot_route.py`.

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\run_boot_route.py --runs 3 --expect tests\replays\expected\boot_to_menu.json
<RETRO_TOOLS_DIR>\python\python.exe -I tools\run_boot_route.py --runs 5 --record-expected tests\replays\expected\boot_to_menu.json
```

It starts `work\build-dbg\MythologyKombat.exe --headless` (no window, no audio) on debug port 4381, with an empty
memory card directory (`work\route_saves`, deleted and recreated each run, so every run is a cold boot). It queues the
route with `input_route_append` and one `input_route_start at_frame=N`, then reads digests at fixed guest frames.
Exit code 0 = match, 1 = mismatch or failed run, 2 = setup error. A single run takes about 70 s of wall clock.

## Committed

| Path | Content |
|------|---------|
| `routes\*.json` | Route files: button names, exact guest frame numbers, hold lengths, checkpoint frames. No game data. |
| `expected\*.json` | Expected digests: frame numbers, guest-cycle counters, write-stream hashes, SHA-256 of RAM and VRAM, route and exe hashes. No paths, no timestamps. |
| `README.md`, `.gitignore` | This file. |

## Not committed (git-ignored)

- Screenshots (`--shots` writes PNGs under `work\`; they show game pixels and are only agent evidence).
- Recordings (`local\`, from T2.19/T2.20; they hold RAM digests and personal data. Whether they are ever committed is the user's decision).
- Save files and memory cards, audio dumps, run logs, scratch results (`work\route\`).
- Game pixels, any disc data, BIOS images, RAM or VRAM contents. Only their SHA-256 hashes are stored.

## Route file

```json
{"name": "boot_to_menu", "checkpoints": [600, 1800, ...],
 "steps": [{"frame": 3000, "buttons": ["START"], "hold": 4}]}
```

A step presses the buttons on guest frames `frame` .. `frame+hold-1`. Frame = the debug server's vblank counter (the
`frame` command). Button names: SELECT L3 R3 START UP RIGHT DOWN LEFT L2 R2 L1 R1 TRIANGLE CIRCLE CROSS SQUARE.
Steps must not overlap. The first step must be later than the frame at which the tool connects (about frame 40).

## Digests

- `fingerprint` is the server's per-frame write fingerprint (`frame_fingerprint`), read for exactly frame N. It covers guest cycle count
  (`cyc`), main-RAM write count and hash (`wc`, `ws`), MMIO and scratchpad write hashes. These are the failure criteria.
  `wr` and `pc` are ordered locators; upstream says they may differ for identical guest state, so a difference is a warning.
- `ram_sha256` / `vram_sha256` hash the whole 2 MB main RAM and 1 MB VRAM. The host cannot stop the guest on an exact frame,
  so the tool pauses as close as it can and records `paused_frame`. The hashes are compared only when `ram_exact` is true (the pause landed
  on frame N) in both the result and the expected file. `--runs N` repeats cold boots until every checkpoint has an exact hash.
- `PSX_DEBUG_FMV_QUIET=0` is set for the child (upstream rule for identity runs).

See `docs\SETUP.md` for the debug build. Replays here are tied to one exe build (`exe_sha256`); after a rebuild that changes
generated code, re-record and review the diff.
