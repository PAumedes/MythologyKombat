# EXE OVERLAYS

This page covers the boot EXE header, the start-up code (crt0), the memory map, and the eight `.OVR` overlay files. It holds addresses and sizes only. It holds no file contents.

Sources:

- `work\exe_header.json` and `work\overlay_candidates.json`, written by `tools\exe_overlays.py` (T1.4).
- `work\overlay_facts.json`, written by `tools\overlay_facts.py` (T2.12). The section "Static overlay facts (T2.12)" below comes from this file.

All three files are git-ignored. How to rerun the scripts is in `docs/SETUP.md`.

Status words used here:

- **confirmed by independent parse**: a second parser read the raw disc sectors and got the same value.
- **confirmed by Ghidra headless**: Ghidra 12.1.4 with the PS1 loader, run through `analyzeHeadless`, gave the same value (T1.5). Used for the entry point, text address and size, BSS range and heap values only. The Ghidra GUI has not been opened. See `docs/SETUP.md`.
- **pending Ghidra/emulator**: not yet compared with a debugger, and not checked in Ghidra. The emulator check is still pending.
- **confirmed** (overlays): the overlay's own code fits the load address that the EXE's loader uses. This is a static check only. Ghidra has not checked the overlays yet. TEMPLE has a runtime check (T2.13, see "Runtime proof (T2.13)"). The other seven are still runtime-pending.
- **static check (T2.12)**: a check on the EXE code and the overlay bytes, done by `tools\overlay_facts.py`. It is strong consistency evidence, not proof. The runtime check (T2.13) confirmed it for TEMPLE. FORTRESS and PRISON are still runtime-pending (T2.17).
- **runtime (T2.13)**: seen in a running debug build, by a script that reads the guest RAM. It is agent-observed. It is not a user observation.

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

All eight `.OVR` files load at `0x80130FF8`. The table gives the size, the disc start LBA, and the end address (exclusive) of each file in RAM. The BRDGDEMO and WINDDEMO files (ids 134 and 143) are not in this table. See the T2.12 section.

| Id | File | Size (bytes) | Start LBA | Load address | End (exclusive) | Layout | Status |
|----|------|--------------|-----------|--------------|-----------------|--------|--------|
| 135 | `/OVERLAYS/BRIDGE.OVR` | 23,164 | 210251 | `0x80130FF8` | `0x80136A74` | address table, then code | confirmed (T1.4). T2.12 joint check not unique (question 130) |
| 136 | `/OVERLAYS/EARTH.OVR` | 37,516 | 210263 | `0x80130FF8` | `0x8013A284` | code from offset 0 | confirmed (T1.4). T2.12 static check gives one base |
| 137 | `/OVERLAYS/FIRE.OVR` | 20,800 | 210282 | `0x80130FF8` | `0x80136138` | address table, then code | confirmed (T1.4). T2.12 joint check not unique (question 130) |
| 138 | `/OVERLAYS/FORTRESS.OVR` | 19,874 | 210293 | `0x80130FF8` | `0x80135D9A` | code from offset 0 | confirmed (T1.4). Two static checks in T2.12. Runtime pending (T2.17) |
| 139 | `/OVERLAYS/PRISON.OVR` | 23,256 | 210303 | `0x80130FF8` | `0x80136AD0` | code from offset 0 | confirmed (T1.4). Two static checks in T2.12. Runtime pending (T2.17) |
| 140 | `/OVERLAYS/TEMPLE.OVR` | 19,100 | 210315 | `0x80130FF8` | `0x80135A94` | code from offset 0 | confirmed (T1.4). T2.12 static check gives one base. Runtime confirmed at `0x80130FF8` (T2.13) |
| 141 | `/OVERLAYS/WATER.OVR` | 28,052 | 210325 | `0x80130FF8` | `0x80137D8C` | address table, then code | confirmed (T1.4). T2.12 joint check not unique (question 130) |
| 142 | `/OVERLAYS/WIND.OVR` | 46,888 | 210339 | `0x80130FF8` | `0x8013C720` | address table, then code | confirmed (T1.4). T2.12 joint check not unique (question 130) |

- BRIDGE, FIRE, WATER and WIND start with a table of address words. The table has 32, 27, 83 and 102 words. The words point at data, not at function starts.
- FIRE, WATER and WIND each hold exactly one null word inside their table.
- The other four start with code.
- Earlier text said FORTRESS and PRISON were confirmed by one check only, and that FORTRESS had no jal targets in the window. Both statements are corrected by the T2.12 section.
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
| Destination pointer | word at `0x80015134` | Holds `0x80130FF8`. No store to it in the EXE text (static scan, T2.12). Holds `0x80130FF8` at runtime (T2.13). See the limits in the T2.12 section |

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
| `0x8002E130` | 137 (FIRE), second function. See the T2.12 section | `0x8002E214` | `0x8002E254` |
| `0x8002E7F0` | 135 (BRIDGE), and 134 (BRDGDEMO, read only) | `0x8002E924`, `0x8002EB30` | `0x8002E964` |
| `0x8002EFBC` | 138 (FORTRESS) | `0x8002F1CC` | `0x8002F20C` |

- The memcpy column is the BIOS memcpy call that follows each read. The WINDDEMO and BRDGDEMO rows have a read call only.
- The names in brackets are the overlay file names that the tool reports for each function. They are labels for the overlay, not names of levels.

## Method notes

- The script finds each overlay's load address two ways. The first way (A) checks the overlay's own jal targets and address constants. The second way (B) reads the EXE loader's pointer. The status is "confirmed" only when the two agree on one exact address.
- Function starts are taken as the word after `jr ra` and its delay slot. For the overlays that begin with an address table, the first word after the table also counts as a start.
- The common check "a jal target is an `addiu sp,sp,-N` prologue" does not work for this code. Many functions start with `lui` or `lw` before the stack change. That check picks the wrong base, so the script does not use it.

## Static overlay facts (T2.12)

Source: `work\overlay_facts.json`, written by `tools\overlay_facts.py`. The script reads the boot EXE and the overlays from the disc `.bin` through the ISO helpers. It does not read `work\extracted\`. Run steps are in `docs/SETUP.md`.

### Loader tables

- The CdlLOC entry is 4 bytes: BCD minute, second, frame, then 0. The base is `0x80012F28`, indexed by id × 4.
- The size entry is a little-endian u32. The base is `0x80013264`, indexed by id × 4.
- LBA = (min × 60 + sec) × 75 + frame − 150.
- Sectors = ceil(size / 2048).

All ten ids agree with the disc file list (`work\disc_files.json`). The ids are contiguous: each file starts at the LBA after the previous file ends.

| Id | File | MSF (BCD) | LBA | Size (bytes) | Sectors |
|----|------|-----------|-----|--------------|---------|
| 134 | `/OVERLAYS/BRDGDEMO.BIN` | 46:45:25 | 210250 | 2,048 | 1 |
| 135 | `/OVERLAYS/BRIDGE.OVR` | 46:45:26 | 210251 | 23,164 | 12 |
| 136 | `/OVERLAYS/EARTH.OVR` | 46:45:38 | 210263 | 37,516 | 19 |
| 137 | `/OVERLAYS/FIRE.OVR` | 46:45:57 | 210282 | 20,800 | 11 |
| 138 | `/OVERLAYS/FORTRESS.OVR` | 46:45:68 | 210293 | 19,874 | 10 |
| 139 | `/OVERLAYS/PRISON.OVR` | 46:46:03 | 210303 | 23,256 | 12 |
| 140 | `/OVERLAYS/TEMPLE.OVR` | 46:46:15 | 210315 | 19,100 | 10 |
| 141 | `/OVERLAYS/WATER.OVR` | 46:46:25 | 210325 | 28,052 | 14 |
| 142 | `/OVERLAYS/WIND.OVR` | 46:46:39 | 210339 | 46,888 | 23 |
| 143 | `/OVERLAYS/WINDDEMO.BIN` | 46:46:62 | 210362 | 2,048 | 1 |

### File ends and leading tables

No `.OVR` file ends on a sector boundary. The tail is the number of bytes from the end of the file to the next 2048-byte boundary. The two demo files are exactly one sector, so their tail is 0.

| Id | File | Tail to next sector (bytes) | Leading address-table words | SHA-256 (first 16 hex) |
|----|------|------------------------------|-----------------------------|------------------------|
| 134 | `BRDGDEMO.BIN` | 0 | not applicable | `17a8beb8d4b3f8e2` |
| 135 | `BRIDGE.OVR` | 1,412 | 32 | `c23488d03a45d87f` |
| 136 | `EARTH.OVR` | 1,396 | 0 | `c612daa9585cc471` |
| 137 | `FIRE.OVR` | 1,728 | 27 | `97542431c98528e4` |
| 138 | `FORTRESS.OVR` | 606 | 0 | `358c301b724ac342` |
| 139 | `PRISON.OVR` | 1,320 | 0 | `2270420ecfa226ec` |
| 140 | `TEMPLE.OVR` | 1,380 | 0 | `291c16ccc2afa65e` |
| 141 | `WATER.OVR` | 620 | 83 | `7b076e6a7649f815` |
| 142 | `WIND.OVR` | 216 | 102 | `530cd442a219cd44` |
| 143 | `WINDDEMO.BIN` | 0 | not applicable | `11731a35bb1dbd04` |

- The leading-table count is the longest run of words from the start of the file whose value is 0 or a multiple of 4. The count matches the table in `tools\exe_overlays.py`.
- FORTRESS's size (19,874) is not a multiple of 4. The tool's word scan drops the last 2 bytes. The tool flags this as `size_multiple_of_4: false`. The loader's memcpy uses get_size(id). See question 139.
- Full SHA-256 values are in `work\overlay_facts.json`.

### Destination pointer

- The word at `0x80015134` (file offset `0x5934`) is `0x80130FF8`.
- Nine functions read it. Each reads it with `lw s0,20788(s0)` after `lui s0,0x8001`, then calls memcpy at `0x8009F31C` with a0 = s0.

| Reader pc | Level function |
|-----------|----------------|
| `0x8002B7C4` | `0x8002B688` (TEMPLE) |
| `0x8002BE60` | `0x8002BD10` (EARTH) |
| `0x8002C59C` | `0x8002C420` (WIND) |
| `0x8002CC58` | `0x8002CB34` (WATER) |
| `0x8002D350` | `0x8002D198` (PRISON) |
| `0x8002DBB4` | `0x8002DA94` (FIRE) |
| `0x8002E240` | `0x8002E130` (second FIRE function) |
| `0x8002E950` | `0x8002E7F0` (BRIDGE) |
| `0x8002F1F8` | `0x8002EFBC` (FORTRESS) |

- No store to `0x80015134` was found in the EXE text.
- Limit: a write through a pointer computed from other data, a DMA transfer, or a BIOS call cannot be excluded by a static scan. See question 137.

### Two checks for the window base

The tool runs two static checks. It tests 2048 candidate bases, from `0x80130000` to `0x80131FFC`.

- **Check E (EXE call sites).** The EXE has 34 call sites into the window, with 26 unique targets. Each call site is grouped by the level function that loads the overlay. A base passes if every call from that group lands on a function start in the overlay. A function start is word 0, the word after `jr ra` and its delay slot, or an `addiu sp,sp,-N` within 10 words.
- **Check C (containment).** Every address the image uses at or above `0x80130FF8` must lie inside `[base, base + size)`. The lower bound `0x80130FF8` is the end of the crt0 BSS clear. It does not depend on the pointer word.

| Overlay | Check E: bases where all sites land | Check C: base interval | Result after both checks |
|---------|-------------------------------------|------------------------|--------------------------|
| EARTH | 3 | `0x801306A8` to `0x80130FF8` | one base |
| TEMPLE | 1 | not listed here (see the JSON) | one base |
| FORTRESS | 1 | `0x80130FA0` to `0x80130FF8` | one base: `0x80130FF8` |
| PRISON | 11 | `0x80130FF4` to `0x80130FF8` | one base: `0x80130FF8` |
| BRIDGE | 52 | `0x80130FE0` to `0x80131078` | not one base (question 130) |
| FIRE | 41 | not listed here (see the JSON) | not one base (question 130) |
| WATER | 8 | not listed here (see the JSON) | not one base (question 130) |
| WIND | 61 | not listed here (see the JSON) | not one base (question 130) |

- **FORTRESS.** The EXE has 3 call sites into the window, all from the FORTRESS level function `0x8002EFBC`: `0x8002F2E4` to `0x80133380`, `0x8002F9D4` to `0x801333FC`, and `0x8002FA14` to `0x80133274`. All three land on function starts at `0x80130FF8`. The same three sites land 0 times in the other seven images at the same base.
- **PRISON.** The EXE has 2 call sites into the window, from the PRISON level function `0x8002D198`: `0x8002D49C` to `0x801316A4` and `0x8002D694` to `0x80131DC0`. Check E alone leaves 11 bases. With check C, only `0x80130FF8` remains. The control gives 1 landing in the EARTH image at this base. The others give 0.
- **Strength.** For FORTRESS and PRISON, this is a strong consistency check, not proof. Their runtime check is still pending (T2.17). TEMPLE was confirmed at runtime (T2.13), see below.
- **Limit on check C.** The containment set includes every 4-aligned word in `[0x80130FF8, 0x80140000)`. So it can include data that is not a pointer. A pointer into BSS or the heap beyond the image would widen the interval.
- **Earlier error.** The earlier note that FORTRESS has no jal targets in the window was a function-boundary artifact. The tool used the level function range `0x8002EFBC` to `0x8002FC84`. FORTRESS has 0 jal targets inside its own image and 54 `j` targets.

### Dispatcher

The level functions are reached through a jump table at `0x80013910` with 12 entries. The index is the word at `0x800D76A8` (gp+252). It is checked by `sltiu` against 12 at `0x80032EC4`. Each entry points to a thunk that loads the target function.

| Index | Target function | Overlay id (tool) | Index that the function stores in gp+252 |
|-------|-----------------|-------------------|-------------------------------------------|
| 0 | `0x8002B688` | 140 | not resolved. The store at `0x8002B740` is at a block boundary |
| 1 | `0x8002C420` | 142 | 1 |
| 2 | `0x8002CB34` | 141 | 2 |
| 3 | `0x8002BD10` | 136 | 3 |
| 4 | `0x8002D198` | 139 | 4 |
| 5 | `0x8002DA94` | 137 | 5 |
| 6 | none. The thunk loads -1 | none | not applicable |
| 7 | `0x8002E130` | 137 (second function) | 7 |
| 8 | `0x8002E7F0` | 135 | 8 |
| 9 | `0x8002EFBC` | 138 | 9 |
| 10 | `0x8002E130` if `[0x800D7E48] >= 0`, otherwise `0x8002AC74` | 137 or none | not applicable |
| 11 | `0x8002B594` | none reported by the tool | not applicable |

- The index order follows the overlay ids. The docs do not give level names for these indices.
- The jump table values and the thunks were checked by the reviewer. The matching of each function to its overlay name comes from the tool.
- `0x8002AC74` and `0x8002B594` are in the table. The tool finds no overlay load in either.

### Second FIRE function at 0x8002E130

- It loads id 137, the same as `0x8002DA94`. It uses the same pointer and the same memcpy.
- It is reached from dispatcher index 7, and from index 10 when `[0x800D7E48] >= 0`.
- Its constant ids are 58, 60, 61, 62, 63, 137 and 144. The id set of `0x8002DA94` is 54, 55, 56, 58, 60, 61, 62, 63, 137 and 144. The comparison is tool output, not checked by the reviewer (question 133).
- It also calls the arena-record loader at `0x80085AF8` and five library functions.
- It has no jal, j or jalr into the window, and no address constant into it. `0x8002DA94` has `jal 0x80131064` at `0x8002DFDC`.
- It stores 2 into gp+256 twice.
- Which level or mode it serves is not known (question 46).

### read_file callers

- There are 128 jal sites to read_file at `0x800861D4`.
- 125 of them use a constant id.
- The 11 constant ids from 134 to 143 are exactly the sites of the nine level functions above.
- Three sites use a variable id:
  - `0x80085CF8` and `0x80085D74`, in function `0x80085AF8`. Its only caller is at `0x8002E6F8`, inside `0x8002E130`. The ids come from the records at `0x800AC440` (field 0, stride 28) and `0x800AC448` (field 2). The index `i` is the word at `0x800D7E48` (gp+2204). It is stored at `0x8002A6DC` (value -1) and at `0x8002AB70` (clamped: negative becomes 24, 25 or more becomes 0). So `i` is -1 or 0 to 24. When `i < 0`, the tool uses constant id 59. This path was not checked by the reviewer.
  - Reachable ids at `0x80085CF8` are 28, 29, 31, 32, 33, 34, 35, 40, 144 to 156, 158, 159, 161 and 162. Reachable ids at `0x80085D74` are 34, 146, 149, 151 and 160. None is in 134 to 143.
  - `0x8008635C`, in the wrapper at `0x80086324`. The wrapper takes the id in a0, stores it, gets the size, allocates, reads, and returns the id. Its direct callers are `0x80083A2C` (in `0x800839F4`) and `0x80083E18` (in `0x80083DE0`). Four id-table functions call it: `0x80083B8C`, `0x80083BEC` (table at `0x800AF5E4`, stride 296), `0x80083F60` and `0x80083FC0` (table at `0x800B1D34`, stride 1008). Each has 29 entries. The ids are 163 to 176 and 192 to 206 in one table, and 118, 121 to 133 and 177 to 191 in the other. None is in 134 to 143. These id tables were not checked by the reviewer.
- The wrapper's address is also stored at `0x80082DF4`, in a callback table built on the stack in `0x80082D78` and passed to `0x800A3F8C`. The ids used by these indirect calls are not known (question 132).
- The window pointer is read only by the nine level functions. So for direct call paths, only those nine functions load overlays into the window.
- The T2.12 report also notes that the generic callers `0x80061690` and `0x80061960` call `0x801310C0`, which is code in the window, from outside the level functions (question 134). This is from the report. It is not in the JSON file.

### Corrections to earlier text

| Earlier statement | Correction |
|-------------------|------------|
| Two read_file calls use a variable id | There are three (see above) |
| FORTRESS has no jal targets in the window | Wrong. The EXE calls 3 window addresses from the FORTRESS function. The earlier result was a function-boundary artifact |
| PRISON's jal targets did not give a decisive result | PRISON has 2 EXE call sites. With both checks, one base remains: `0x80130FF8` |
| FORTRESS and PRISON are confirmed by one check only | Both have two static checks (E and C). Runtime is still pending (T2.13) |
| The function at `0x8002E130` is the second FIRE site, with its level unknown | Still true. It is also a second function that loads FIRE, selected by dispatcher index 7 (or 10). Its level is unknown (question 46) |

## Runtime proof (T2.13)

Source: `work\overlay_runtime.json`, written by `tools\overlay_runtime_check.py`. The run steps are in `docs/SETUP.md` ("Runtime overlay proof (T2.13)"). The method is in `docs/DECISIONS.md` (D10).

Scope: one level, TEMPLE (function `0x8002B688`, id 140). Only this level's overlay load fired in the runs. The run went to guest frame 9000 with the committed route `boot_to_menu`. Two cold boots gave identical results. A reviewer re-ran one of them, and the checks held.

### What was seen

| Step | Guest frame | Value seen |
|------|-------------|------------|
| `read_file` entry (function `0x800861D4`) | 5200 | a0 = 140 (`/OVERLAYS/TEMPLE.OVR`). a1 = `0x8013100C`, the scratch buffer. ra = `0x8002B7A0`. The call is at `0x8002B798` |
| memcpy wrapper entry (`0x8009F31C`) | 5207 | a0 = `0x80130FF8` (the window base). a1 = `0x8013100C`. a2 = `0x00004A9C`, which is 19,100, the size from `get_size(140)`. a3 = `0xFFFFFFFF`. ra = `0x8002B7E0`. The call is at `0x8002B7D8` |
| Copy stores | 5207 to 5208 | 16,592 value-changing byte stores. Each is width 1, with strictly ascending addresses. The store is at pc `0xBFC085F8`, in the OpenBIOS memcpy byte loop (`0xBFC085D8` to `0xBFC085FC`) |
| Pointer word `0x80015134` | at pause | `0x80130FF8` |

### Hash check

| Item | Value |
|------|-------|
| SHA-256 of the window bytes `[0x80130FF8, +19100)` after the copy, from live RAM | `291c16ccc2afa65e504a7603e4624f2d9bf5e71720ab5782cb9d1d6898e3a6eb` |
| SHA-256 of `TEMPLE.OVR` in `work\overlay_facts.json` | Same value |
| SHA-256 recomputed from the disc (LBA 210315, 19,100 bytes) | Same value |
| Bytes that differ | 0 |
| Source buffer `[0x8013100C, 0x80135AA8)` before the copy | Same SHA-256. The CD read gave the file bytes |

- The window bytes were read from live RAM at the pause. They do not depend on the undo step below.

### Overlap of the copy (question 45)

- The source `0x8013100C` is 0x14 (20 bytes) above the destination `0x80130FF8`. It is 16 bytes above the BIOS heap start `0x80130FFC`.
- The two ranges overlap by 19,080 bytes.
- The destination is below the source, and the loop copies forward byte by byte. So the copy is safe for this overlap. It gives the same result as a memmove.
- This holds under OpenBIOS as run by PSXRecomp. The retail BIOS memcpy was not examined.
- The copy overwrites 16 bytes, `0x80130FFC` to `0x8013100B`. These were BIOS heap words before the copy, and overlay bytes after it. Their values are not recorded here. Whether the program uses them later is not known (question 180).

### Method

- The tool armed two things at launch. The first is a function filter with an entry dump. It records a0 to a3, ra, s0 to s3, and the frame, at each entry to `0x800861D4` (filter id 140 and buffer) and to `0x8009F31C`.
- The second is a write-transition ring. It was armed with `PSX_WTRACE_BOOT_RANGES=0x130FF8-0x13C720`. It logs value-changing CPU stores in the overlay window. Each entry holds the address, the old and new values, pc, ra, sp and the frame. The capacity is 1 << 20 entries. The overflow guard `oldest_seq == 0` held, and 16,592 stores were logged. The ring records widths 1, 2 and 4, and it includes stores made by BIOS ROM code.
- The tool paused the game with `host_pause` at the first memcpy. The pause landed inside the copy, at pc `0xBFC085E0` in BIOS ROM.
- The RAM just before and just after the copy was rebuilt by undoing newer ring entries in reverse order.
- The DMA check: a DMA or an untraced writer would show as an inconsistency in the undo. None was found. The ring holds 0 such cases.
- The tool then resumed for one frame and paused again, at pc `0x800947A0`. That frame was 5210 or 5212, depending on the run. That second pause is not part of the invariant.

### Limits

- Only TEMPLE is shown. The eight other level functions and their ids were not seen. The tool is hard-coded to TEMPLE-style checks: a0 equals the window base, and a2 equals `get_size(id)`. It stops at the first overlay memcpy. Waiting for a given id would be a small change.
- Runs beyond frame 9000 were not made.
- FORTRESS was not run. Its size, 19,874, is not a multiple of 4. The byte loop suggests the same copy path, but this is not shown (question 139).
- The 16 clobbered bytes were not checked for later use. The retail BIOS memcpy was not checked.
- Earlier runs, not the committed tool, saw other reads. `read_file` calls with ids `0x55` (85) and `0x90` (144) ran at about frames 4002 and 4007. They also used buffer `0x8013100C`. Id `0x8C` (140) was also seen. What the ids 85 and 144 load, and whether they copy into the window, is not known (question 181).
- The screen at the pause showed a mission objective and a loading message. This is an agent observation. The screenshot is not committed.

## Not yet confirmed

See `docs/OPEN_QUESTIONS.md`, questions 44 to 52, 130 to 139, and 178 to 183.
