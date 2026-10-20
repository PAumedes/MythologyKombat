# EXE OVERLAYS

This page covers the boot EXE header, the start-up code (crt0), the memory map, and the eight `.OVR` overlay files. It holds addresses and sizes only. It holds no file contents.

Source: `work\exe_header.json` and `work\overlay_candidates.json`, written by `tools\exe_overlays.py` (T1.4). Both files are git-ignored. How to rerun the script is in `docs/SETUP.md`.

Status words used here:

- **confirmed by independent parse**: a second parser read the raw disc sectors and got the same value.
- **confirmed by Ghidra headless**: Ghidra 12.1.4 with the PS1 loader gave the same value (T1.5). Used for the entry point, text address and size, BSS range and heap values only. See `docs/SETUP.md`.
- **pending Ghidra/emulator**: not yet compared with a debugger, and not checked in Ghidra. The emulator check is still pending.
- **confirmed** (overlays): the overlay's own code fits the load address that the EXE's loader uses. This is a static check only. Ghidra has not checked the overlays yet. A runtime check is still pending.

## EXE header

The boot file is `/SLUS_004.76`. It is 821,248 bytes. That is the 0x800-byte header plus the text size.

| Field | Value | Status |
|-------|-------|--------|
| pc0 (entry point) | `0x80090E70` | confirmed by independent parse and Ghidra headless. Emulator check pending |
| gp0 (initial GP) | `0x00000000` | confirmed by independent parse. Not checked in Ghidra |
| t_addr (text load address) | `0x80010000` | confirmed by independent parse and Ghidra headless. Emulator check pending |
| t_size (text size) | `0xC8000` (819,200 bytes) | confirmed by independent parse and Ghidra headless. Emulator check pending |
| d_addr / d_size | `0x00000000` / `0x00000000` | confirmed by independent parse. Not checked in Ghidra |
| b_addr / b_size | `0x00000000` / `0x00000000` | confirmed by independent parse. Not checked in Ghidra |
| s_addr / s_size | `0x801FFFF0` / `0x00000000` | confirmed by independent parse. Not checked in Ghidra |
| Initial SP | `0x801FFFF0` | confirmed by independent parse. Not checked in Ghidra |
| Region string | Sony Computer Entertainment Inc. for North America area | confirmed by independent parse |

The independent parse reads `.bin` sector 23 (the boot EXE start), takes the Form 1 user data at offset 24, and reads the header from there. The code is `raw_sector_header()` in `tools\exe_overlays.py`.

## Start-up code (crt0)

The code at the entry point is decoded by the script. Ghidra headless decodes the same start-up code (T1.5). The BSS range and the heap start and size match. GP is not checked in Ghidra. The emulator check is pending.

| Item | Value | Where |
|------|-------|-------|
| GP is set to | `0x800D75AC` | pc `0x80090EF4` |
| BSS is cleared from | `0x800D7B40` | store at pc `0x80090E80` |
| BSS is cleared up to (exclusive) | `0x80130FF8` | compare at pc `0x80090E88` |
| Heap start passed to BIOS InitHeap (A(0x39)) | `0x80130FFC` | a0 |
| Heap size passed to InitHeap | `sp - [0x800BF358] - 0x130FF8` | a1 |

The word at `0x800BF358` holds `0x8000`. The header GP is 0, but crt0 sets GP in code. The BIOS heap starts inside the overlay window (see the open questions).

## Memory map

| Region | Start | End (exclusive) | Notes |
|--------|-------|-----------------|-------|
| Text (EXE code and data) | `0x80010000` | `0x800D8000` | Loaded from the file |
| BSS (cleared by crt0) | `0x800D7B40` | `0x80130FF8` | Starts inside the text range. The bytes in that part of the file are all 0 |
| Overlay window | `0x80130FF8` | `0x8013C720` | All eight overlays load here. WIND is the largest |
| Stack | below `0x801FFFF0` | | Initial SP is `0x801FFFF0`. The overlay window ends below it |

No overlay overlaps the EXE text or the cleared BSS. The overlay window starts exactly where crt0's clear stops.

In Ghidra's PS1 loader, the RAM block at `0x800D8000` to `0x801FFFFF` is uninitialised. The overlay window is inside this block. See `docs/SETUP.md` (T1.5).

## Overlay table

All eight `.OVR` files load at `0x80130FF8`. The table gives the size, the disc start LBA, and the end address (exclusive) of each file in RAM.

| Id | File | Size (bytes) | Start LBA | Load address | End (exclusive) | Layout | Status |
|----|------|--------------|-----------|--------------|-----------------|--------|--------|
| 135 | `/OVERLAYS/BRIDGE.OVR` | 23,164 | 210251 | `0x80130FF8` | `0x80136A74` | address table, then code | confirmed |
| 136 | `/OVERLAYS/EARTH.OVR` | 37,516 | 210263 | `0x80130FF8` | `0x8013A284` | code from offset 0 | confirmed |
| 137 | `/OVERLAYS/FIRE.OVR` | 20,800 | 210282 | `0x80130FF8` | `0x80136138` | address table, then code | confirmed |
| 138 | `/OVERLAYS/FORTRESS.OVR` | 19,874 | 210293 | `0x80130FF8` | `0x80135D9A` | code from offset 0 | confirmed (rests on one check only) |
| 139 | `/OVERLAYS/PRISON.OVR` | 23,256 | 210303 | `0x80130FF8` | `0x80136AD0` | code from offset 0 | confirmed (rests on one check only) |
| 140 | `/OVERLAYS/TEMPLE.OVR` | 19,100 | 210315 | `0x80130FF8` | `0x80135A94` | code from offset 0 | confirmed |
| 141 | `/OVERLAYS/WATER.OVR` | 28,052 | 210325 | `0x80130FF8` | `0x80137D8C` | address table, then code | confirmed |
| 142 | `/OVERLAYS/WIND.OVR` | 46,888 | 210339 | `0x80130FF8` | `0x8013C720` | address table, then code | confirmed |

- BRIDGE, FIRE, WATER and WIND start with a table of address words. The table has 32, 27, 83 and 102 words. The words point at data, not at function starts.
- The other four start with code.
- FORTRESS and PRISON are confirmed by the address-constant check only. FORTRESS has no jal targets in the window. PRISON's jal targets did not give a decisive result.
- Ids 134 (`/OVERLAYS/BRDGDEMO.BIN`) and 143 (`/OVERLAYS/WINDDEMO.BIN`) are 2048-byte files. The loader does not copy them to the window. See `docs/FORMATS.md`.

## How overlays are loaded

Overlay sizes and disc positions are in two tables inside the EXE data.

| Item | Address | Notes |
|------|---------|-------|
| CdlLOC table (BCD min, sec, frame, 0) | base `0x80012F28` | Index 0. The entries for ids 134 to 143 start at `0x80013140` |
| File-size table (4 bytes per id) | base `0x80013264` | Index 0. The entries for ids 134 to 143 start at `0x8001347C` |

The table index is the file id. The ids are 134 to 143, from `/OVERLAYS/BRDGDEMO.BIN` to `/OVERLAYS/WINDDEMO.BIN`.

| Function | Address | Role |
|----------|---------|------|
| get_size(id) | `0x800861BC` | Returns the file size for an id |
| read_file(id, buf) | `0x800861D4` | Seeks with CdlSetloc, then reads with CdRead. It reads ceil(size / 2048) sectors |
| Scratch allocator | `0x800865C0` | Gives the temporary read buffer. Not traced in full |
| memcpy (BIOS A(0x2A)) wrapper | `0x8009F31C` | Copies the read buffer into the window |
| Destination pointer | word at `0x80015134` | Holds `0x80130FF8`. The EXE never stores to it |

Each level function does this:

1. Calls read_file(id, buf) into the scratch buffer.
2. Calls memcpy with length get_size(id) to the pointer at `0x80015134`.
3. Calls code inside the window. For TEMPLE, one call goes to `0x80130FF8`, the first byte of the overlay.

### Level functions that load overlays

| Level function | Overlay id(s) | read_file call | memcpy call |
|----------------|---------------|----------------|-------------|
| `0x8002B688` | 140 (TEMPLE) | `0x8002B798` | `0x8002B7D8` |
| `0x8002BD10` | 136 (EARTH) | `0x8002BE34` | `0x8002BE74` |
| `0x8002C420` | 142 (WIND), and 143 (WINDDEMO, read only) | `0x8002C570`, `0x8002C864` | `0x8002C5B0` |
| `0x8002CB34` | 141 (WATER) | `0x8002CC2C` | `0x8002CC6C` |
| `0x8002D198` | 139 (PRISON) | `0x8002D324` | `0x8002D364` |
| `0x8002DA94` | 137 (FIRE) | `0x8002DB88` | `0x8002DBC8` |
| `0x8002E130` | 137 (FIRE), second site | `0x8002E214` | `0x8002E254` |
| `0x8002E7F0` | 135 (BRIDGE), and 134 (BRDGDEMO, read only) | `0x8002E924`, `0x8002EB30` | `0x8002E964` |
| `0x8002EFBC` | 138 (FORTRESS) | `0x8002F1CC` | `0x8002F20C` |

The memcpy column is the BIOS memcpy call that follows each read. The WINDDEMO and BRDGDEMO rows have a read call only.

## Method notes

- The script finds each overlay's load address two ways. The first way (A) checks the overlay's own jal targets and address constants. The second way (B) reads the EXE loader's pointer. The status is "confirmed" only when the two agree on one exact address.
- Function starts are taken as the word after `jr ra` and its delay slot. For the overlays that begin with an address table, the first word after the table also counts as a start.
- The common check "a jal target is an `addiu sp,sp,-N` prologue" does not work for this code. Many functions start with `lui` or `lw` before the stack change. That check picks the wrong base, so the script does not use it.

## Not yet confirmed

See `docs/OPEN_QUESTIONS.md`, questions 44 to 52.
