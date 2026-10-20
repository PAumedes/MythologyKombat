# FORMATS

This page classifies every file on the disc by format. It gives each file a primary tag, any secondary tags, and the kinds of evidence behind the tags. It holds no file contents.

Source: `work\disc_classes.json`, written by `tools\disc_classify.py` (T1.3). The file is git-ignored.

Regenerate from the repo root (needs `work\disc_files.json` from T1.1 first):

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\disc_classify.py
```

Paths are disc paths, as in `docs/DISC_MAP.md`. Sizes are ISO directory sizes.

## Summary

| Primary tag | Files | Bytes |
|-------------|-------|-------|
| PS-X EXE | 1 | 821248 |
| STR video | 28 | 418940928 |
| overlay candidate | 8 | 218650 |
| SPU-ADPCM (headerless) | 29 | 4855504 |
| magic container | 31 | 2424664 |
| offset-table container | 46 | 5309759 |
| u16-id-table container | 28 | 290440 |
| filler | 1 | 30000000 |
| text | 2 | 283 |
| unknown | 37 | 5505590 |
| **Total** | **211** | **468367066** |

Secondary tags:

| Secondary tag | Files |
|---------------|-------|
| XA audio | 27 (all STR video files except `/MOVIES/LEGAL.STR`) |
| u16-id-table container | 27 (`.LCD` files, see below) |
| text | 1 (`/NOXCUSES.BIN`) |

No file is tagged TIM, VAB, VAG, SEQ or SEP. See the open questions.

## Evidence kinds

The kinds are the labels in the header of `tools\disc_classify.py`.

| Kind | Meaning |
|------|---------|
| magic | Signature bytes at a fixed offset |
| structure | Internal fields that must agree (sizes, tables) |
| subheader | CD-XA sector subheader bits |
| heuristic | Statistical test (MIPS code density, SPU-ADPCM block validity) |
| content | Whole-file test (filler pattern, printable text), or no rule matched |
| hint | Extension or directory name. Never used alone. Kept in `hints_not_evidence` |

## Per-file tags

Files are grouped by directory and, where a directory has mixed formats, by extension. Unknown files and overlay candidates are listed one by one.

### Root (`/`)

| Path | Primary | Secondary | Evidence |
|------|---------|-----------|----------|
| `/SLUS_004.76` | PS-X EXE | none | magic, structure |
| `/SYSTEM.CNF` | text | none | content |
| `/DOZER.BIN` | text | none | content |
| `/NOXCUSES.BIN` | filler | text | content |

### `/CHARS` (13 files)

| Files | Count | Primary | Secondary | Evidence |
|-------|-------|---------|-----------|----------|
| ASASSIN2, ASASSIN3, ASS2, ASSASSIN, FAST, FIREGOD, GRUNT, GRUNT2, HANGLID, HEADLESS, HOUND, HOVMONK, HULK (all `.BIN`) | 13 | offset-table container | none | structure |

### `/CHARS2` (19 files)

| Files | Count | Primary | Secondary | Evidence |
|-------|-------|---------|-----------|----------|
| MKSZ, MONK, MONK2, MONK3, MONK4, MONK5, MONK6, PGRUNT1, PGRUNT2, PGRUNT3, PGRUNT4, PGRUNT5, QUANCHI, QUANCHI2, SCORPION, SHINNOK, WATERFX, WATERGOD, WINDGOD (all `.BIN`) | 19 | offset-table container | none | structure |

### `/LCDS` (14 files)

| Files | Count | Primary | Secondary | Evidence |
|-------|-------|---------|-----------|----------|
| SZL1SFX, SZL1TUNZ, SZL2SFX1, SZL2SFX3, SZL2TUNZ, SZL3SFX1, SZL3SFX2, SZL3SFX3, SZL3TUNZ, SZL4BOSS, SZL4SFX, SZL4TUNZ (all `.LCD`) | 12 | SPU-ADPCM (headerless) | u16-id-table container | heuristic, structure |
| FIGHTSFX, SZL2SFX2 (both `.LCD`) | 2 | SPU-ADPCM (headerless) | none | heuristic |

### `/LCDS2` (15 files)

| Files | Count | Primary | Secondary | Evidence |
|-------|-------|---------|-----------|----------|
| SZL5BOSS, SZL5SFX, SZL5TUNZ, SZL7SFX1, SZL7SFX2, SZL7TUNZ, SZL8SFX, SZL8TUNZ, SZL9FXA1, SZL9FXA2, SZL9FXA3, SZL9FXQC, SZL9FXSH, SZL9SFX, SZL9TUNZ (all `.LCD`) | 15 | SPU-ADPCM (headerless) | u16-id-table container | heuristic, structure |

### `/LSDS` (16 files)

| Files | Count | Primary | Secondary | Evidence |
|-------|-------|---------|-----------|----------|
| SZL1SFX, SZL1TUNZ, SZL2SFX1, SZL2SFX2, SZL2SFX3, SZL2TUNZ, SZL3SFX1, SZL3SFX2, SZL3SFX3, SZL3TUNZ, SZL4BOSS, SZL4SFX, SZL4TUNZ (all `.LSD`) | 13 | u16-id-table container | none | structure |
| SUBZERO.WMD | 1 | magic container | none | magic |
| SUBZERO.WSD | 1 | magic container | none | magic |
| `/LSDS/FIGHTSFX.LSD` | 1 | unknown | none | content |

### `/LSDS2` (15 files)

| Files | Count | Primary | Secondary | Evidence |
|-------|-------|---------|-----------|----------|
| SZL5BOSS, SZL5SFX, SZL5TUNZ, SZL7SFX1, SZL7SFX2, SZL7TUNZ, SZL8SFX, SZL8TUNZ, SZL9FXA1, SZL9FXA2, SZL9FXA3, SZL9FXQC, SZL9FXSH, SZL9SFX, SZL9TUNZ (all `.LSD`) | 15 | u16-id-table container | none | structure |

### `/MOVIES` (28 files)

| Files | Count | Primary | Secondary | Evidence |
|-------|-------|---------|-----------|----------|
| BIOS, BRDGFL1, CREDS01, DROWN2, E2WTR, FIREFL1, FMV1, FMV2, FMV3A, FMV3B, FMV4AB, FMV5, FMV6, FMV7AB, MIDWAY01, MK4A, NUFALL3, OPEN, OUTTKES1, PRSNFAL2, QUANDETH, ROCKDETH, SZINTRO1, SZLOGO15, WND2E, WTR2FR, WTRDRN1 (all `.STR`) | 27 | STR video | XA audio | subheader, structure |
| `/MOVIES/LEGAL.STR` | 1 | STR video | none | subheader, structure |

### `/OVERLAYS` (10 files)

| Path | Primary | Secondary | Evidence | Start of file |
|------|---------|-----------|----------|---------------|
| `/OVERLAYS/BRDGDEMO.BIN` | unknown | none | content | not applicable (2048-byte halfword data) |
| `/OVERLAYS/WINDDEMO.BIN` | unknown | none | content | not applicable (2048-byte halfword data) |
| `/OVERLAYS/BRIDGE.OVR` | overlay candidate | none | heuristic x2, structure | table of RAM-address words |
| `/OVERLAYS/EARTH.OVR` | overlay candidate | none | heuristic x2, structure | begins with instructions |
| `/OVERLAYS/FIRE.OVR` | overlay candidate | none | heuristic x2, structure | table of RAM-address words |
| `/OVERLAYS/FORTRESS.OVR` | overlay candidate | none | heuristic x2, structure | begins with instructions |
| `/OVERLAYS/PRISON.OVR` | overlay candidate | none | heuristic x2, structure | begins with instructions |
| `/OVERLAYS/TEMPLE.OVR` | overlay candidate | none | heuristic x2, structure | begins with instructions |
| `/OVERLAYS/WATER.OVR` | overlay candidate | none | heuristic x2, structure | table of RAM-address words |
| `/OVERLAYS/WIND.OVR` | overlay candidate | none | heuristic x2, structure | table of RAM-address words |

### `/LEVELS` (77 files)

Grouped by extension. The unknown `.TSQ`, `.TXD` and `.BIN` files are listed one by one.

| Files (under `/LEVELS/`) | Count | Primary | Secondary | Evidence |
|--------------------------|-------|---------|-----------|----------|
| `.LVL`: BRIDGE/BRIDGE.LVL, BRIDGE/DINO.LVL, EARTH/EARTH.LVL, FIRE/FIRE.LVL, FIRE2/FIRE2.LVL, FORTRESS/FORTRESS.LVL, PRISON/PRISON.LVL, ROCKY/ROCKY.LVL, SKULLMAN/SKULLMAN.LVL, SKULLMAN/SKULLMN2.LVL, TEMPLE/TEMPLE.LVL, THRONERM/MONSTER.LVL, THRONERM/THRONERM.LVL, WATER/WATER.LVL, WATER/WTRGOD.LVL, WIND/WIND.LVL, WIND/WINDGD.LVL | 17 | magic container | none | magic |
| `.WAL`: BRIDGE/BRIDGE.WAL, EARTH/EARTH.WAL, FIRE/FIRE.WAL, FIRE2/FIRE2.WAL, FORTRESS/FORTRESS.WAL, PRISON/PRISON.WAL, TEMPLE/TEMPLE.WAL, THRONERM/THRONERM.WAL, WATER/WATER.WAL, WATER/WTRGOD.WAL, WIND/WIND.WAL, WIND/WINDGD.WAL | 12 | magic container | none | magic |
| `.BIN` (offset table): BRIDGE/BRDGBG.BIN, BRIDGE/BRDGFLUF.BIN, BRIDGE/DINO.BIN, FIRE/FIREBG.BIN, FIRE/FIREFLUF.BIN, FORTRESS/FORTBG.BIN, FORTRESS/FORTFLUF.BIN, PRISON/PRISFLUF.BIN, PRISON/PRISONBG.BIN, TEMPLE/TEMPLEBG.BIN, THRONERM/MONSTER.BIN, WATER/WATRFLUF.BIN, WIND/WINDBG.BIN, WIND/WINDFLUF.BIN | 14 | offset-table container | none | structure |

Unknown files under `/LEVELS/`:

| Path | Primary | Secondary | Evidence |
|------|---------|-----------|----------|
| `/LEVELS/BRIDGE/BRIDGE.TSQ` | unknown | none | content |
| `/LEVELS/BRIDGE/BRIDGE.TXD` | unknown | none | content |
| `/LEVELS/EARTH/DIRTFLUF.BIN` | unknown | none | content |
| `/LEVELS/EARTH/EARTH.TSQ` | unknown | none | content |
| `/LEVELS/EARTH/EARTH.TXD` | unknown | none | content |
| `/LEVELS/FIRE/FIRE.TSQ` | unknown | none | content |
| `/LEVELS/FIRE/FIRE.TXD` | unknown | none | content |
| `/LEVELS/FIRE2/FIRE2.TSQ` | unknown | none | content |
| `/LEVELS/FIRE2/FIRE2.TXD` | unknown | none | content |
| `/LEVELS/FORTRESS/FORTRESS.TSQ` | unknown | none | content |
| `/LEVELS/FORTRESS/FORTRESS.TXD` | unknown | none | content |
| `/LEVELS/PRISON/PRISON.TSQ` | unknown | none | content |
| `/LEVELS/PRISON/PRISON.TXD` | unknown | none | content |
| `/LEVELS/ROCKY/ROCKMAN.BIN` | unknown | none | content |
| `/LEVELS/SKULLMAN/SKULLMAN.BIN` | unknown | none | content |
| `/LEVELS/SKULLMAN/SKULLMAN.TSQ` | unknown | none | content |
| `/LEVELS/SKULLMAN/SKULLMN2.TSQ` | unknown | none | content |
| `/LEVELS/SKULLMAN/SKULMAN2.BIN` | unknown | none | content |
| `/LEVELS/TEMPLE/FLUFF.TXD` | unknown | none | content |
| `/LEVELS/TEMPLE/LVLSEL.TXD` | unknown | none | content |
| `/LEVELS/TEMPLE/TEMPFLUF.BIN` | unknown | none | content |
| `/LEVELS/TEMPLE/TEMPLE.TSQ` | unknown | none | content |
| `/LEVELS/TEMPLE/TEMPLE.TXD` | unknown | none | content |
| `/LEVELS/THRONERM/SHINFLUF.BIN` | unknown | none | content |
| `/LEVELS/THRONERM/THRONERM.TSQ` | unknown | none | content |
| `/LEVELS/THRONERM/THRONERM.TXD` | unknown | none | content |
| `/LEVELS/WATER/WATER.TSQ` | unknown | none | content |
| `/LEVELS/WATER/WATER.TXD` | unknown | none | content |
| `/LEVELS/WATER/WTRGOD.TSQ` | unknown | none | content |
| `/LEVELS/WATER/WTRGOD.TXD` | unknown | none | content |
| `/LEVELS/WIND/WIND.TSQ` | unknown | none | content |
| `/LEVELS/WIND/WIND.TXD` | unknown | none | content |
| `/LEVELS/WIND/WINDGD.TSQ` | unknown | none | content |
| `/LEVELS/WIND/WINDGD.TXD` | unknown | none | content |

Counts check: 17 + 12 + 14 + 34 unknown = 77.

## Unknown files outside `/LEVELS/`

| Path | Primary | Secondary | Evidence |
|------|---------|-----------|----------|
| `/LSDS/FIGHTSFX.LSD` | unknown | none | content |
| `/OVERLAYS/BRDGDEMO.BIN` | unknown | none | content |
| `/OVERLAYS/WINDDEMO.BIN` | unknown | none | content |

Total unknown: 34 under `/LEVELS/` and 3 elsewhere = 37.

## Format notes by tag

Each note records what the tools measured. Meanings are not claimed unless stated.

### PS-X EXE

- `/SLUS_004.76` is the boot file. Its header gives pc `0x80090E70`, text address `0x80010000`, text size 819200 bytes, a `0x800` byte header, and a stack top of `0x801FFFF0`.

### STR video and XA audio

- 28 STR video files hold 418,940,928 bytes.
- Video sectors are Form 1 with submode `0x48`. `/MOVIES/LEGAL.STR` uses submode `0x08` and has no audio.
- The video submode bit `0x02` is never set on this disc. This differs from the textbook STR layout.
- Each video payload starts with a header. It holds a u16 `0x0160`, a u16 `0x8001`, a chunk number, chunks per frame, a frame number, a demux size, a width and a height.
- The MDEC magic `0x3800` is at payload offset 22.
- The first frame of `/MOVIES/BIOS.STR` is 320 x 240, with 9 chunks, version 2 and qscale 1.
- 27 STR files hold interleaved XA audio. The audio sectors are Form 2 with submode `0x64` and coding `0x01`. The coding decodes to stereo, 37.8 kHz, 4-bit. The audio is on file 1, channel 1.
- A few sectors have submode `0x00` or `0x80`. They are empty.

### SPU-ADPCM (headerless)

- 29 `.LCD` files.
- 99.95 to 100 percent of their 16-byte blocks pass the block test. Random data passes about 0.8 percent.

### Overlay candidate

- 8 `.OVR` files, all in `/OVERLAYS`.
- MIPS validity is 0.939 to 0.985 on the code test.
- Each has 19 to 45 `addiu sp,sp,-N` prologues and 22 to 51 `jr ra` instructions.
- Rule: score at least 0.80, and at least one prologue, and at least one `jr ra`, and at least 256 non-zero words.
- `EARTH`, `FORTRESS`, `PRISON` and `TEMPLE` begin directly with instructions.
- `BRIDGE`, `FIRE`, `WATER` and `WIND` begin with a table of words that look like RAM addresses near `0x8013xxxx`.
- The RAM address each overlay loads to is in `docs/EXE_OVERLAYS.md` (T1.4). All eight load at `0x80130FF8`. The check is static. The runtime check is pending. See `docs/OPEN_QUESTIONS.md`, questions 35 and 44.

### Magic container

- 31 files. Each starts with a signature at offset 0.
- 17 `.LVL` files start with the bytes `DD CC BB AA`.
- 12 `.WAL` files start with the bytes `33 22 11 00`.
- `/LSDS/SUBZERO.WMD` starts with the text `SPSX`.
- `/LSDS/SUBZERO.WSD` starts with the text `SSEQ`.
- What these formats hold is not claimed.

### Offset-table container

- 46 files. Each starts with a leading u32 table. The first entry is the table length.
- Example: `/CHARS/ASASSIN2.BIN` has 208 entries. Its first entry is `0x340`. Of the 208, 135 are 4-aligned offsets inside the file, 43 are `0` or `0xFFFFFFFF` sentinels, and 30 are other values.
- What the offsets point to is not checked.

### u16-id-table container

- 28 files, all `.LSD`.
- Each holds a u16 count N, then N u16 ids, then a zero u16.
- 27 `.LCD` files carry this tag as a secondary tag. The exception is `/LCDS/SZL2SFX2.LCD`. `/LCDS/FIGHTSFX.LCD` also has no tag.

### Filler

- `/NOXCUSES.BIN` is 30,000,000 bytes. It is an 11-byte ASCII phrase repeated. The phrase restarts at each 32768-byte block.

### Text

- `/SYSTEM.CNF` and `/DOZER.BIN` are plain text. `/DOZER.BIN` ends with a `0x1A` byte.

### Unknown

- 37 files. Their contents are not analysed.
- They are 14 `.TXD` files and 14 `.TSQ` files in `/LEVELS/`, 8 `.BIN` files, and `/LSDS/FIGHTSFX.LSD`.
- `/OVERLAYS/BRDGDEMO.BIN` and `/OVERLAYS/WINDDEMO.BIN` are 2048-byte halfword data. They pass the code score but fail the prologue and `jr ra` rule.

### Not found

- No TIM, VAB, VAG, SEQ or SEP file is on the disc.
- The classifier found 233 TIM-like byte patterns. None passed the block-size check.

## Notes

- The STR files extract with the suffix `.raw2352`. Later tools must allow for it.
- The extracted files and the JSON are in `work\`, which is git-ignored.
- See `docs/OPEN_QUESTIONS.md`, questions 29 to 43.
