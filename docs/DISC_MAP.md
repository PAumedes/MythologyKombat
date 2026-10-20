# DISC MAP

This page lists every file on the disc. It has names, paths, sizes, start sectors (LBA), sector counts, and XA flags only. It holds no file contents.

Source: `work\disc_files.json`, written by `tools\disc_list.py` (T1.1). The file is git-ignored.

Tag column: this page has no tag column. The format tag of each file (primary tag, secondary tags, evidence kind) is in `docs/FORMATS.md` (T1.3).

Regenerate from the repo root:

```
<RETRO_TOOLS_DIR>\python\python.exe -I tools\disc_list.py
```

## Summary

| Item | Value |
|------|-------|
| Files | 211 |
| Directories | 22 (including the root `/`) |
| Total file bytes | 468367066 |
| File sectors | 228788 |
| Track 1 sectors | 228991 |
| Audio tracks | 0 |
| Track 1 | `Mortal Kombat Mythologies - Sub-Zero.bin`, mode MODE2/2352 |
| Boot EXE | `/SLUS_004.76` (LBA 23, 401 sectors) |
| Volume system ID | PLAYSTATION |
| Volume ID | blank |
| Files with XA flag | 27 (all in `/MOVIES`) |

Size note: `size_bytes` is the ISO directory size. It equals sectors x 2048 for every file. Form 2 sectors hold 2324 data bytes, so the interleaved STR files hold less data than their size shows.

Disc paths have no version suffix here. The raw ISO names end in `;1`.

## Files per top-level directory

| Top-level directory | Files |
|---------------------|-------|
| (root) | 4 |
| CHARS | 13 |
| CHARS2 | 19 |
| LCDS | 14 |
| LCDS2 | 15 |
| LEVELS | 77 |
| LSDS | 16 |
| LSDS2 | 15 |
| MOVIES | 28 |
| OVERLAYS | 10 |
| Total | 211 |

## XA flags

- A file is XA-flagged when its XA attribute has the interleaved bit set and it holds Form 2 sectors.
- The 27 XA-flagged files are all in `/MOVIES`. Their XA attribute word is 0x2555.
- `/MOVIES/LEGAL.STR` is the one STR file that is not flagged. It has no Form 2 or interleaved sectors. Its XA attribute word is 0x0d55.
- The other 183 files have XA attribute word 0x0d55 and are not flagged. Directories have 0x8d55.

## Files

Each table is sorted by start LBA.

### Root (`/`)

| Path | LBA | Size (bytes) | Sectors | XA-flagged |
|------|-----|--------------|---------|------------|
| /SLUS_004.76 | 23 | 821248 | 401 | No |
| /SYSTEM.CNF | 214190 | 66 | 1 | No |
| /DOZER.BIN | 214191 | 217 | 1 | No |
| /NOXCUSES.BIN | 214192 | 30000000 | 14649 | No |

### /CHARS

| Path | LBA | Size (bytes) | Sectors | XA-flagged |
|------|-----|--------------|---------|------------|
| /CHARS/ASASSIN2.BIN | 204996 | 226304 | 111 | No |
| /CHARS/ASASSIN3.BIN | 205107 | 241616 | 118 | No |
| /CHARS/ASS2.BIN | 205225 | 41540 | 21 | No |
| /CHARS/ASSASSIN.BIN | 205246 | 213032 | 105 | No |
| /CHARS/FAST.BIN | 205351 | 135508 | 67 | No |
| /CHARS/FIREGOD.BIN | 205418 | 438348 | 215 | No |
| /CHARS/GRUNT.BIN | 205633 | 153054 | 75 | No |
| /CHARS/GRUNT2.BIN | 205708 | 116660 | 57 | No |
| /CHARS/HANGLID.BIN | 205765 | 37782 | 19 | No |
| /CHARS/HEADLESS.BIN | 205784 | 150124 | 74 | No |
| /CHARS/HOUND.BIN | 205858 | 205408 | 101 | No |
| /CHARS/HOVMONK.BIN | 205959 | 99561 | 49 | No |
| /CHARS/HULK.BIN | 206008 | 180748 | 89 | No |

### /CHARS2

| Path | LBA | Size (bytes) | Sectors | XA-flagged |
|------|-----|--------------|---------|------------|
| /CHARS2/MKSZ.BIN | 210364 | 235144 | 115 | No |
| /CHARS2/MONK.BIN | 210479 | 140720 | 69 | No |
| /CHARS2/MONK2.BIN | 210548 | 142308 | 70 | No |
| /CHARS2/MONK3.BIN | 210618 | 46340 | 23 | No |
| /CHARS2/MONK4.BIN | 210641 | 85720 | 42 | No |
| /CHARS2/MONK5.BIN | 210683 | 123228 | 61 | No |
| /CHARS2/MONK6.BIN | 210744 | 41840 | 21 | No |
| /CHARS2/PGRUNT1.BIN | 210765 | 130054 | 64 | No |
| /CHARS2/PGRUNT2.BIN | 210829 | 112904 | 56 | No |
| /CHARS2/PGRUNT3.BIN | 210885 | 116036 | 57 | No |
| /CHARS2/PGRUNT4.BIN | 210942 | 78232 | 39 | No |
| /CHARS2/PGRUNT5.BIN | 210981 | 103008 | 51 | No |
| /CHARS2/QUANCHI.BIN | 211032 | 323092 | 158 | No |
| /CHARS2/QUANCHI2.BIN | 211190 | 118592 | 58 | No |
| /CHARS2/SCORPION.BIN | 211248 | 260872 | 128 | No |
| /CHARS2/SHINNOK.BIN | 211376 | 190192 | 93 | No |
| /CHARS2/WATERFX.BIN | 211469 | 34744 | 17 | No |
| /CHARS2/WATERGOD.BIN | 211486 | 221112 | 108 | No |
| /CHARS2/WINDGOD.BIN | 211594 | 218756 | 107 | No |

### /LCDS

| Path | LBA | Size (bytes) | Sectors | XA-flagged |
|------|-----|--------------|---------|------------|
| /LCDS/FIGHTSFX.LCD | 211702 | 120016 | 59 | No |
| /LCDS/SZL1SFX.LCD | 211761 | 180368 | 89 | No |
| /LCDS/SZL1TUNZ.LCD | 211850 | 175808 | 86 | No |
| /LCDS/SZL2SFX1.LCD | 211936 | 63904 | 32 | No |
| /LCDS/SZL2SFX2.LCD | 211968 | 144336 | 71 | No |
| /LCDS/SZL2SFX3.LCD | 212039 | 153488 | 75 | No |
| /LCDS/SZL2TUNZ.LCD | 212114 | 161280 | 79 | No |
| /LCDS/SZL3SFX1.LCD | 212193 | 140880 | 69 | No |
| /LCDS/SZL3SFX2.LCD | 212262 | 80864 | 40 | No |
| /LCDS/SZL3SFX3.LCD | 212302 | 78000 | 39 | No |
| /LCDS/SZL3TUNZ.LCD | 212341 | 149808 | 74 | No |
| /LCDS/SZL4BOSS.LCD | 212415 | 205216 | 101 | No |
| /LCDS/SZL4SFX.LCD | 212516 | 194816 | 96 | No |
| /LCDS/SZL4TUNZ.LCD | 212612 | 167568 | 82 | No |

### /LCDS2

| Path | LBA | Size (bytes) | Sectors | XA-flagged |
|------|-----|--------------|---------|------------|
| /LCDS2/SZL5BOSS.LCD | 212795 | 225792 | 111 | No |
| /LCDS2/SZL5SFX.LCD | 212906 | 178320 | 88 | No |
| /LCDS2/SZL5TUNZ.LCD | 212994 | 123120 | 61 | No |
| /LCDS2/SZL7SFX1.LCD | 213055 | 168768 | 83 | No |
| /LCDS2/SZL7SFX2.LCD | 213138 | 253936 | 124 | No |
| /LCDS2/SZL7TUNZ.LCD | 213262 | 125936 | 62 | No |
| /LCDS2/SZL8SFX.LCD | 213324 | 237264 | 116 | No |
| /LCDS2/SZL8TUNZ.LCD | 213440 | 138224 | 68 | No |
| /LCDS2/SZL9FXA1.LCD | 213508 | 137680 | 68 | No |
| /LCDS2/SZL9FXA2.LCD | 213576 | 195424 | 96 | No |
| /LCDS2/SZL9FXA3.LCD | 213672 | 160976 | 79 | No |
| /LCDS2/SZL9FXQC.LCD | 213751 | 330880 | 162 | No |
| /LCDS2/SZL9FXSH.LCD | 213913 | 373760 | 183 | No |
| /LCDS2/SZL9SFX.LCD | 214096 | 92592 | 46 | No |
| /LCDS2/SZL9TUNZ.LCD | 214142 | 96480 | 48 | No |

### /LEVELS (77 files in 10 subdirectories)

| Path | LBA | Size (bytes) | Sectors | XA-flagged |
|------|-----|--------------|---------|------------|
| /LEVELS/BRIDGE/BRDGBG.BIN | 206099 | 916 | 1 | No |
| /LEVELS/BRIDGE/BRDGFLUF.BIN | 206100 | 17196 | 9 | No |
| /LEVELS/BRIDGE/BRIDGE.LVL | 206109 | 202374 | 99 | No |
| /LEVELS/BRIDGE/BRIDGE.TSQ | 206208 | 27004 | 14 | No |
| /LEVELS/BRIDGE/BRIDGE.TXD | 206222 | 492496 | 241 | No |
| /LEVELS/BRIDGE/BRIDGE.WAL | 206463 | 16964 | 9 | No |
| /LEVELS/BRIDGE/DINO.BIN | 206472 | 138000 | 68 | No |
| /LEVELS/BRIDGE/DINO.LVL | 206540 | 28712 | 15 | No |
| /LEVELS/EARTH/DIRTFLUF.BIN | 206556 | 20424 | 10 | No |
| /LEVELS/EARTH/EARTH.LVL | 206566 | 185836 | 91 | No |
| /LEVELS/EARTH/EARTH.TSQ | 206657 | 35012 | 18 | No |
| /LEVELS/EARTH/EARTH.TXD | 206675 | 446412 | 218 | No |
| /LEVELS/EARTH/EARTH.WAL | 206893 | 15200 | 8 | No |
| /LEVELS/FIRE/FIRE.LVL | 206902 | 156988 | 77 | No |
| /LEVELS/FIRE/FIRE.TSQ | 206979 | 11804 | 6 | No |
| /LEVELS/FIRE/FIRE.TXD | 206985 | 290122 | 142 | No |
| /LEVELS/FIRE/FIRE.WAL | 207127 | 18004 | 9 | No |
| /LEVELS/FIRE/FIREBG.BIN | 207136 | 1084 | 1 | No |
| /LEVELS/FIRE/FIREFLUF.BIN | 207137 | 9520 | 5 | No |
| /LEVELS/FIRE2/FIRE2.LVL | 207143 | 43986 | 22 | No |
| /LEVELS/FIRE2/FIRE2.TSQ | 207165 | 11804 | 6 | No |
| /LEVELS/FIRE2/FIRE2.TXD | 207171 | 248110 | 122 | No |
| /LEVELS/FIRE2/FIRE2.WAL | 207293 | 1004 | 1 | No |
| /LEVELS/FORTRESS/FORTBG.BIN | 207295 | 892 | 1 | No |
| /LEVELS/FORTRESS/FORTFLUF.BIN | 207296 | 13848 | 7 | No |
| /LEVELS/FORTRESS/FORTRESS.LVL | 207303 | 237608 | 117 | No |
| /LEVELS/FORTRESS/FORTRESS.TSQ | 207420 | 4 | 1 | No |
| /LEVELS/FORTRESS/FORTRESS.TXD | 207421 | 442068 | 216 | No |
| /LEVELS/FORTRESS/FORTRESS.WAL | 207637 | 11080 | 6 | No |
| /LEVELS/PRISON/PRISFLUF.BIN | 207644 | 18664 | 10 | No |
| /LEVELS/PRISON/PRISON.LVL | 207654 | 167314 | 82 | No |
| /LEVELS/PRISON/PRISON.TSQ | 207736 | 27004 | 14 | No |
| /LEVELS/PRISON/PRISON.TXD | 207750 | 436562 | 214 | No |
| /LEVELS/PRISON/PRISON.WAL | 207964 | 9144 | 5 | No |
| /LEVELS/PRISON/PRISONBG.BIN | 207969 | 868 | 1 | No |
| /LEVELS/ROCKY/ROCKMAN.BIN | 207971 | 192948 | 95 | No |
| /LEVELS/ROCKY/ROCKY.LVL | 208066 | 24220 | 12 | No |
| /LEVELS/SKULLMAN/SKULLMAN.BIN | 208079 | 126410 | 62 | No |
| /LEVELS/SKULLMAN/SKULLMAN.LVL | 208141 | 25964 | 13 | No |
| /LEVELS/SKULLMAN/SKULLMAN.TSQ | 208154 | 36676 | 18 | No |
| /LEVELS/SKULLMAN/SKULLMN2.LVL | 208172 | 25966 | 13 | No |
| /LEVELS/SKULLMAN/SKULLMN2.TSQ | 208185 | 9064 | 5 | No |
| /LEVELS/SKULLMAN/SKULMAN2.BIN | 208190 | 18926 | 10 | No |
| /LEVELS/TEMPLE/FLUFF.TXD | 208201 | 328448 | 161 | No |
| /LEVELS/TEMPLE/LVLSEL.TXD | 208362 | 12504 | 7 | No |
| /LEVELS/TEMPLE/TEMPFLUF.BIN | 208369 | 64608 | 32 | No |
| /LEVELS/TEMPLE/TEMPLE.LVL | 208401 | 198332 | 97 | No |
| /LEVELS/TEMPLE/TEMPLE.TSQ | 208498 | 16124 | 8 | No |
| /LEVELS/TEMPLE/TEMPLE.TXD | 208506 | 394302 | 193 | No |
| /LEVELS/TEMPLE/TEMPLE.WAL | 208699 | 6720 | 4 | No |
| /LEVELS/TEMPLE/TEMPLEBG.BIN | 208703 | 1468 | 1 | No |
| /LEVELS/THRONERM/MONSTER.BIN | 208705 | 109288 | 54 | No |
| /LEVELS/THRONERM/MONSTER.LVL | 208759 | 28140 | 14 | No |
| /LEVELS/THRONERM/SHINFLUF.BIN | 208773 | 88448 | 44 | No |
| /LEVELS/THRONERM/THRONERM.LVL | 208817 | 24312 | 12 | No |
| /LEVELS/THRONERM/THRONERM.TSQ | 208829 | 4 | 1 | No |
| /LEVELS/THRONERM/THRONERM.TXD | 208830 | 447486 | 219 | No |
| /LEVELS/THRONERM/THRONERM.WAL | 209049 | 716 | 1 | No |
| /LEVELS/WATER/WATER.LVL | 209051 | 264048 | 129 | No |
| /LEVELS/WATER/WATER.TSQ | 209180 | 51444 | 26 | No |
| /LEVELS/WATER/WATER.TXD | 209206 | 267498 | 131 | No |
| /LEVELS/WATER/WATER.WAL | 209337 | 23032 | 12 | No |
| /LEVELS/WATER/WATRFLUF.BIN | 209349 | 25820 | 13 | No |
| /LEVELS/WATER/WTRGOD.LVL | 209362 | 25772 | 13 | No |
| /LEVELS/WATER/WTRGOD.TSQ | 209375 | 30904 | 16 | No |
| /LEVELS/WATER/WTRGOD.TXD | 209391 | 200096 | 98 | No |
| /LEVELS/WATER/WTRGOD.WAL | 209489 | 620 | 1 | No |
| /LEVELS/WIND/WIND.LVL | 209491 | 343976 | 168 | No |
| /LEVELS/WIND/WIND.TSQ | 209659 | 20544 | 11 | No |
| /LEVELS/WIND/WIND.TXD | 209670 | 470146 | 230 | No |
| /LEVELS/WIND/WIND.WAL | 209900 | 28588 | 14 | No |
| /LEVELS/WIND/WINDBG.BIN | 209914 | 1012 | 1 | No |
| /LEVELS/WIND/WINDFLUF.BIN | 209915 | 8604 | 5 | No |
| /LEVELS/WIND/WINDGD.LVL | 209920 | 55204 | 27 | No |
| /LEVELS/WIND/WINDGD.TSQ | 209947 | 20544 | 11 | No |
| /LEVELS/WIND/WINDGD.TXD | 209958 | 212048 | 104 | No |
| /LEVELS/WIND/WINDGD.WAL | 210062 | 512 | 1 | No |

### /LSDS

| Path | LBA | Size (bytes) | Sectors | XA-flagged |
|------|-----|--------------|---------|------------|
| /LSDS/FIGHTSFX.LSD | 210064 | 3496 | 2 | No |
| /LSDS/SUBZERO.WMD | 210066 | 21904 | 11 | No |
| /LSDS/SUBZERO.WSD | 210077 | 232424 | 114 | No |
| /LSDS/SZL1SFX.LSD | 210191 | 4176 | 3 | No |
| /LSDS/SZL1TUNZ.LSD | 210194 | 18296 | 9 | No |
| /LSDS/SZL2SFX1.LSD | 210203 | 2432 | 2 | No |
| /LSDS/SZL2SFX2.LSD | 210205 | 3216 | 2 | No |
| /LSDS/SZL2SFX3.LSD | 210207 | 3088 | 2 | No |
| /LSDS/SZL2TUNZ.LSD | 210209 | 27136 | 14 | No |
| /LSDS/SZL3SFX1.LSD | 210223 | 3296 | 2 | No |
| /LSDS/SZL3SFX2.LSD | 210225 | 2888 | 2 | No |
| /LSDS/SZL3SFX3.LSD | 210227 | 2400 | 2 | No |
| /LSDS/SZL3TUNZ.LSD | 210229 | 21784 | 11 | No |
| /LSDS/SZL4BOSS.LSD | 210240 | 3128 | 2 | No |
| /LSDS/SZL4SFX.LSD | 210242 | 3696 | 2 | No |
| /LSDS/SZL4TUNZ.LSD | 210244 | 8968 | 5 | No |

### /LSDS2

| Path | LBA | Size (bytes) | Sectors | XA-flagged |
|------|-----|--------------|---------|------------|
| /LSDS2/SZL5BOSS.LSD | 212695 | 3224 | 2 | No |
| /LSDS2/SZL5SFX.LSD | 212697 | 3920 | 2 | No |
| /LSDS2/SZL5TUNZ.LSD | 212699 | 31688 | 16 | No |
| /LSDS2/SZL7SFX1.LSD | 212715 | 3824 | 2 | No |
| /LSDS2/SZL7SFX2.LSD | 212717 | 4344 | 3 | No |
| /LSDS2/SZL7TUNZ.LSD | 212720 | 40352 | 20 | No |
| /LSDS2/SZL8SFX.LSD | 212740 | 4160 | 3 | No |
| /LSDS2/SZL8TUNZ.LSD | 212743 | 16960 | 9 | No |
| /LSDS2/SZL9FXA1.LSD | 212752 | 3200 | 2 | No |
| /LSDS2/SZL9FXA2.LSD | 212754 | 3504 | 2 | No |
| /LSDS2/SZL9FXA3.LSD | 212756 | 3264 | 2 | No |
| /LSDS2/SZL9FXQC.LSD | 212758 | 10744 | 6 | No |
| /LSDS2/SZL9FXSH.LSD | 212764 | 26904 | 14 | No |
| /LSDS2/SZL9SFX.LSD | 212778 | 3088 | 2 | No |
| /LSDS2/SZL9TUNZ.LSD | 212780 | 26760 | 14 | No |

### /MOVIES

| Path | LBA | Size (bytes) | Sectors | XA-flagged |
|------|-----|--------------|---------|------------|
| /MOVIES/BIOS.STR | 426 | 10696704 | 5223 | Yes |
| /MOVIES/BRDGFL1.STR | 5649 | 3307520 | 1615 | Yes |
| /MOVIES/CREDS01.STR | 7264 | 56457216 | 27567 | Yes |
| /MOVIES/DROWN2.STR | 34831 | 1849344 | 903 | Yes |
| /MOVIES/E2WTR.STR | 35734 | 5683200 | 2775 | Yes |
| /MOVIES/FIREFL1.STR | 38509 | 2160640 | 1055 | Yes |
| /MOVIES/FMV1.STR | 39564 | 59553792 | 29079 | Yes |
| /MOVIES/FMV2.STR | 68643 | 53426176 | 26087 | Yes |
| /MOVIES/FMV3A.STR | 94730 | 19331072 | 9439 | Yes |
| /MOVIES/FMV3B.STR | 104169 | 14923776 | 7287 | Yes |
| /MOVIES/FMV4AB.STR | 111456 | 22984704 | 11223 | Yes |
| /MOVIES/FMV5.STR | 122679 | 23853056 | 11647 | Yes |
| /MOVIES/FMV6.STR | 134326 | 10074112 | 4919 | Yes |
| /MOVIES/FMV7AB.STR | 139245 | 25245696 | 12327 | Yes |
| /MOVIES/LEGAL.STR | 151572 | 3072000 | 1500 | No |
| /MOVIES/MIDWAY01.STR | 153072 | 3913728 | 1911 | Yes |
| /MOVIES/MK4A.STR | 154983 | 17119232 | 8359 | Yes |
| /MOVIES/NUFALL3.STR | 163350 | 1718272 | 839 | Yes |
| /MOVIES/OPEN.STR | 164189 | 6371328 | 3111 | Yes |
| /MOVIES/OUTTKES1.STR | 167300 | 34142208 | 16671 | Yes |
| /MOVIES/PRSNFAL2.STR | 183971 | 1931264 | 943 | Yes |
| /MOVIES/QUANDETH.STR | 184914 | 1865728 | 911 | Yes |
| /MOVIES/ROCKDETH.STR | 185825 | 2455552 | 1199 | Yes |
| /MOVIES/SZINTRO1.STR | 187024 | 18724864 | 9143 | Yes |
| /MOVIES/SZLOGO15.STR | 196167 | 2324480 | 1135 | Yes |
| /MOVIES/WND2E.STR | 197302 | 5355520 | 2615 | Yes |
| /MOVIES/WTR2FR.STR | 199917 | 5715968 | 2791 | Yes |
| /MOVIES/WTRDRN1.STR | 202708 | 4683776 | 2287 | Yes |

### /OVERLAYS

| Path | LBA | Size (bytes) | Sectors | XA-flagged |
|------|-----|--------------|---------|------------|
| /OVERLAYS/BRDGDEMO.BIN | 210250 | 2048 | 1 | No |
| /OVERLAYS/BRIDGE.OVR | 210251 | 23164 | 12 | No |
| /OVERLAYS/EARTH.OVR | 210263 | 37516 | 19 | No |
| /OVERLAYS/FIRE.OVR | 210282 | 20800 | 11 | No |
| /OVERLAYS/FORTRESS.OVR | 210293 | 19874 | 10 | No |
| /OVERLAYS/PRISON.OVR | 210303 | 23256 | 12 | No |
| /OVERLAYS/TEMPLE.OVR | 210315 | 19100 | 10 | No |
| /OVERLAYS/WATER.OVR | 210325 | 28052 | 14 | No |
| /OVERLAYS/WIND.OVR | 210339 | 46888 | 23 | No |
| /OVERLAYS/WINDDEMO.BIN | 210362 | 2048 | 1 | No |

## Directories

| Path | LBA | Sectors |
|------|-----|---------|
| / | 22 | 1 |
| /MOVIES | 425 | 1 |
| /CHARS | 204995 | 1 |
| /LEVELS | 206097 | 1 |
| /LEVELS/BRIDGE | 206098 | 1 |
| /LEVELS/EARTH | 206555 | 1 |
| /LEVELS/FIRE | 206901 | 1 |
| /LEVELS/FIRE2 | 207142 | 1 |
| /LEVELS/FORTRESS | 207294 | 1 |
| /LEVELS/PRISON | 207643 | 1 |
| /LEVELS/ROCKY | 207970 | 1 |
| /LEVELS/SKULLMAN | 208078 | 1 |
| /LEVELS/TEMPLE | 208200 | 1 |
| /LEVELS/THRONERM | 208704 | 1 |
| /LEVELS/WATER | 209050 | 1 |
| /LEVELS/WIND | 209490 | 1 |
| /LSDS | 210063 | 1 |
| /OVERLAYS | 210249 | 1 |
| /CHARS2 | 210363 | 1 |
| /LCDS | 211701 | 1 |
| /LSDS2 | 212694 | 1 |
| /LCDS2 | 212794 | 1 |

## Filesystem structures

| LBA | Sectors | Structure |
|-----|---------|-----------|
| 0 to 15 | 16 | System area |
| 16 | 1 | Volume descriptor, type 1 (primary) |
| 17 | 1 | Volume descriptor, type 255 (terminator) |
| 18 | 1 | Path table, L |
| 19 | 1 | Path table, L (optional copy) |
| 20 | 1 | Path table, M |
| 21 | 1 | Path table, M (optional copy) |

The path tables are 304 bytes long. The directory records are at the LBAs in the Directories table above.

## Gaps

Sectors that no file entry covers. There are 3 gap ranges and 159 sectors in total.

| LBA range | Sectors | Sector form | Submode |
|-----------|---------|-------------|---------|
| 424 | 1 | Form 2 | 0x20 |
| 163342 to 163349 | 8 | Form 2 | 0x20 |
| 228841 to 228990 | 150 | Form 1 | 0x00 |

The gap at 424 sits between `/SLUS_004.76` (ends at LBA 423) and the `/MOVIES` directory (LBA 425). The gap at 163342 to 163349 sits between `/MOVIES/MK4A.STR` (ends at LBA 163341) and `/MOVIES/NUFALL3.STR` (starts at LBA 163350). The last gap ends at LBA 228990, the last sector of track 1.

## Overlaps

None. The scan found 0 overlaps.

## Open items

See `docs/OPEN_QUESTIONS.md`, questions 27 and 28. The map covers track 1 only. The cue lists one track. Multi-track cues are untested.
