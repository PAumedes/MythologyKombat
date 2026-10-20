# SYMBOLS

## Leftover debug symbols (T1.2)

The disc has no debug symbol file. It has no linker map text. It has no game function names.

The script `tools\symbol_hunt.py` scanned every sector of the disc. It found no Psy-Q `.SYM` file, no `.MAP` text and no symbol name table.

| Search | Result |
|--------|--------|
| Psy-Q `.SYM` file (starts with `MND`) | None at any file or sector start. 7 chance `MND` byte runs sit in the middle of data. They are noise. |
| Linker `.MAP` text | None |
| SYM-style name tables | None |
| Game function names | None |
| Source paths (`.c`, `.h`, `C:\`, `\PSX\`) | One developer path, in one game file. See the leftovers below. |
| Function-name-like strings | Noise, except one Sony library name (`LoadImage`). See below. |

"Nothing found" is the result for symbols. The disc does not give the game's own function names.

### Coverage

| Item | Value |
|------|-------|
| Track 1 sectors | 228991 |
| Sectors scanned | 228991 of 228991 |
| User data scanned | 475,976,240 bytes |
| Form 1 sector size used | 2048 bytes |
| Form 2 sector size used | 2324 bytes (per CD-XA subheader) |
| Sectors skipped for bad sync | 0 |

The scan split the track into three kinds of region. A second pass read the whole track as one stream. Both passes agree on every category.

| Region kind | Regions | Sectors | Bytes |
|-------------|---------|---------|-------|
| Files | 211 | 228788 | 475,556,908 |
| Filesystem structures (system area, volume descriptors, path tables, directories) | 29 | 44 | 91,216 |
| Gaps between files | 3 | 159 | 328,116 |

The three gaps lie at LBA 424, LBA 163342 to 163349, and LBA 228841 to 228990. An independent reviewer rescan agreed with the counts.

### Real leftovers

These are the only items worth a note. All offsets are in the boot EXE, `SLUS_004.76`, unless marked.

| Item | Where | Offset | What it is |
|------|-------|--------|------------|
| Source-file revision ids (3) | `/SLUS_004.76` (LBA 34 to 35) | EXE `0x5b18`, `0x5dc8`, `0x6094` | Version-control ids for three Sony library source files: `intr.c`, `bios.c` and `sys.c`. Dates in these ids fall between Dec 1996 and Mar 1997. |
| Sony library copyright line | `/SLUS_004.76` (LBA 374) | EXE `0xafb89` | Copyright notice for the Sony library, years 1993 to 1997. |
| Sony library error text | `/SLUS_004.76` | EXE `0x6618` | Debug message from the memory card library. |
| Sony library API names and messages | `/SLUS_004.76` | EXE `0x5b08` to `0x6264` | Names such as `VSync`, `CdInit`, `CdRead`, `ResetGraph`, `DrawSync`, `LoadImage`, `StoreImage`, `ClearOTag`, `DrawOTag`, `PutDrawEnv` and `PutDispEnv`. Also MDEC and CD-ROM debug messages. |
| Sony control driver version | `/SLUS_004.76` | EXE `0xaf350` | Text `PS-X Control TAP Driver`, version 3.0. Found by the reviewer. The tool misses it (see Limits). |
| Developer build path (3 hits) | `/LEVELS/WIND/WIND.WAL` | file `0x6984`, `0x6bf4`, `0x6e64` | A Windows path on a developer drive, in a level data file. It is a path leak, not a symbol table. The path is not copied here in full. |
| Game title and text strings | `/SLUS_004.76` | EXE `0x41b4`, `0x5398`, `0x594c` | Game text and the serial string. Not symbols. |
| Publisher name | `/MOVIES` directory record (LBA 425) | dir offset `0x3f3` | A publisher name in a directory record. Not analysed further. |
| System area licence text | system area (LBA 4) | `0x2020` | Expected. Platform text. |
| Volume and boot text | volume descriptors (LBA 16), `/SLUS_004.76` (LBA 23) | various | Expected. Platform text. |

### What the Sony strings say

- The Sony library strings indicate a PsyQ library with revision dates from about Dec 1996 to Mar 1997. This is not a confirmed version.
- The strings `PS-X Run-time Library`, `Library Release`, `Revision`, `$Header` and a compile date were **not** found.
- The library strings include debug text. This may help with the SDK names in T1.6.
- The T1.6 step must check these strings against the EXE directly. Do not rely on this summary alone.

### What the Sony strings do not say

- They do not name any game function.
- They do not give the game's own address map.
- They do not show that the library was built with symbols.

### Noise that was not counted as evidence

| Item | Count | Why it is noise |
|------|-------|-----------------|
| Source-filename pattern hits | 295 (3 real) | Random data in texture and video files. |
| Identifier-like tokens | 9346 occurrences, 8151 unique | Mostly in video (`STR`) and texture (`TXD`) files. |
| Function-name-like tokens | 1 real | `LoadImage` is the only verb-plus-capital name from the Sony library. |
| Hits inside `STR` video files | 204561 of 228788 file sectors are `STR` | Compressed data. Hits there are counted but not listed. |

### Overlays

No symbol or path hits were found in the `.OVR` overlay files.

## Limits

- The version patterns in `tools\symbol_hunt.py` miss the form `Ver n`. The reviewer found the `PS-X Control TAP Driver Ver 3.0` line by hand. See `docs/OPEN_QUESTIONS.md`.
- The version evidence from T1.2 is only a summary. The full version evidence is in the "SDK functions (T1.6)" section below.
- The tool was run once in full. Byte-for-byte repeat output is judged from the code, not from a second full run.

## Reproduce

Run from the repo root. The run takes about 5.5 minutes.

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\symbol_hunt.py
```

- It writes `work\symbol_hunt.txt`. The `work\` folder is git-ignored.
- It uses only the Python standard library.
- It does not change anything in `ps1_game\`.
- The self test runs with `--selftest`. It passes 12 of 12 tests.
- The full report is in `work\symbol_hunt.txt`. Its section 1 holds the coverage counts.

## SDK functions (T1.6)

This section lists the Sony library (PsyQ) functions found in the EXE. It gives a best-fit library version. It is not an exact SDK identity.

The result is in `work\symbols_sdk.json`. That folder is git-ignored. This page holds names, addresses and counts only.

### Library version

| Item | Value |
|------|-------|
| Version source | 11 `Ps` library-version records in the EXE. Each record starts with the letters `Ps`. The version word is big-endian `0x4000`, at offset +6. |
| Record addresses | `0x80099D98`, `0x8009F2CC`, `0x8009FC64`, `0x800BEB44`, `0x800BEBE0`, `0x800BF360`, `0x800C054C`, `0x800C0A78`, `0x800D71CC`, `0x800D7360`, `0x800D7378` |
| Ghidra PS1 loader | `ghidra_psx_ldr` `DetectPsyQ` maps the EXE to the signature set `data\psyq\400`. Program Information shows `PsyQ Version` = `4.0.0`. |
| Best fit | PsyQ 4.0 signature set. Not an exact SDK identity. |
| Control driver | Text `PS-X Control TAP Driver Ver 3.0` at `0x800BEB50`. |

Object-signature match counts per set, from `tools\psyq_version_scan.py`:

| Set | Matches | Set | Matches |
|-----|---------|-----|---------|
| 400 | 116 | 420-450 | 43 |
| 370 | 95 | 410 | 41 |
| 460 | 61 | 330 | 26 |
| 470 | 54 | 340 | 24 |
| 3610/3611 | 49 | 260/300 | 5 |
| 350 | 43 | | |

- The set 400 has the most matches. The best-fit label rests on this count.
- The scan reports the 420-450 and 3610/3611 rows as given. Each row is one count from the scan output.
- The RCS revision dates on the disc fall between Dec 1996 and Mar 1997. They are not mapped to a PsyQ release. No release list was available.

### Function counts

| Item | Count |
|------|-------|
| Functions found by Ghidra | 1730 |
| Named functions | 931 |
| Named from the IMPORTED source | 425 |
| Named from the USER_DEFINED source | 506 |
| `sdk` kind (names from PsyQ signatures, plus `start` and `main` named by the PS1 loader) | 443 |
| `obj_label` kind (placeholders, not SDK names) | 335 |
| `gte_macro` kind (at the synthetic `0x20000000` block) | 153 |

- The 153 `gte_macro` names are excluded from the recompiler seed.
- The 335 `obj_label` names are placeholders such as `TAP_OBJ_C8`, `SYS_OBJ_11C` and `LIBMCRD_OBJ_xx`. They are not real SDK names.

### The 443 SDK names by library

| Library group | Names |
|---------------|-------|
| GPU, GS primitives and Fnt | 134 |
| Cd, CD_ and St | 60 |
| MemCard and _card | 57 |
| libc and BIOS stubs | 46 |
| Spu, _spu and Ss | 44 |
| GTE and math | 24 |
| Interrupt and callback | 23 |
| Pad | 21 |
| MDEC and DecDCT | 21 |
| TAP | 6 |
| crt0 and loader | 4 |
| Other | 3 |

### Spot checks

The implementer checked 5 names. The reviewer checked 5 more. Each name was matched to code or a string.

| Name | Address | Evidence |
|------|---------|----------|
| VSync | `0x800945E4` | `v_wait` at `0x8009472C` refers to the string `VSync: timeout` |
| ResetGraph | `0x8009C238` | String `ResetGraph:jtb=` |
| CdInit | `0x800952D8` | String `CdInit: Init failed` |
| DrawSync | `0x8009C6F8` | Implementer spot check. Evidence not recorded. |
| memcpy | `0x8009F31C` | BIOS trampoline `A(0x2a)` |
| printf | `0x8009F34C` | BIOS trampoline `A(0x3f)` |
| RotTransPers | `0x8009A618` | `lwc2` and COP2 RTPS word `0x4A180001` |
| MemCardInit | `0x8009FF0C` | Calls `_card_open` at `0x800A1B10` |
| StartPAD | `0x800A246C` | Reviewer spot check. Evidence not recorded. |
| SpuIsTransferCompleted | `0x80093D68` | `TestEvent` loop |
| DecDCTReset | `0x80098C5C` | Reviewer spot check. Evidence not recorded. |
| InitPAD | `0x800A23D0` | Reviewer spot check. Evidence not recorded. |

### Suspect names

| Name | Address | Size | Why |
|------|---------|------|-----|
| `SsUtReverbOn` | `0x80053AD0` | 32 bytes | Below the SDK block. Probably a false positive. |
| `SsUtReverbOff` | `0x8005E1B0` | 32 bytes | Below the SDK block. Probably a false positive. |
| `_SsSndPlay` | `0x8008387C` | 44 bytes | Below the SDK block. Probably a false positive. |

- `main` is at `0x80020474`. The PS1 loader named it.
- `start` is at `0x80090E70`. The PS1 loader named it.
- `__main` at `0x80090E68` has a Ghidra comment that calls it a possible `SsUtVibrateOff`. That comment is unreliable.
- 157 `sdk` functions are 32 bytes or less. Of these, 48 are BIOS `jr t2` stubs, 1 is a bare `jr ra`, and 108 are small bodies. Look-alike wrappers may be swapped, such as in the TAP family and in `__main` and `stup0`. Key on the address, not the name.
- Duplicate names: `memset` at `0x8009F2A0` and `0x8009F32C`. `memclr` three times.

### String hints (not applied as names)

These string references point at likely names. No name was applied.

| String | Address | Likely name |
|--------|---------|-------------|
| `SPU:T/O [%s]` | `0x80092648` | SPU function (`SPU_OBJ_3AC`) |
| `CdRead: sector error` | `0x800973F0` | CdRead (`CDREAD_OBJ_A4`) |
| `MDEC_rest:bad option(%d)` | `0x80099000` | Probably `MDEC_rest` (`LIBPRESS_OBJ_3A4`) |
| `PS-X Control TAP Driver Ver 3.0` | `0x80091F64` | TAP driver (`TAP_OBJ_1038`) |
| `ResetGraph(%d)...` | `0x8009C354` | ResetGraph (`SYS_OBJ_11C`) |
| `CDROM: unknown intr` | none | No code reference. Probably the CD interrupt handler, called through a pointer table. |

Game functions stay unnamed.

### Reproduce

Run from the repo root.

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\ghidra_sdk_names.py
<RETRO_TOOLS_DIR>\python\python.exe -I tools\ghidra_sdk_names.py --reuse
<RETRO_TOOLS_DIR>\python\python.exe -I tools\psyq_version_scan.py
```

- The full Ghidra run takes about 2.5 minutes. `--reuse` takes about 13 seconds.
- Both Ghidra runs write `work\symbols_sdk.json`. The output is the same on every run.
- `tools\psyq_version_scan.py` writes `work\psyq_version_scan.json` and prints a table.
- See `docs\SETUP.md` (T1.6) for the options.
