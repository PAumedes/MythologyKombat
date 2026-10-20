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
- The version evidence is not collected in one place. The list above is the only summary. See `docs/OPEN_QUESTIONS.md`.
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

_To be filled in by T1.6. The PsyQ library version source and the named-function count go here._
