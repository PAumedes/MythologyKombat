# DISC

This page holds the identity of the disc. It has hashes and the serial only. It holds no file contents.

Source: `tools\disc_identify.py` (T0.4). The script writes `work\disc_identity.json`.

## Cue and track

| Item | Value |
|------|-------|
| Cue file | `ps1_game\Mortal Kombat Mythologies - Sub-Zero.cue` |
| Tracks | 1 |
| Track 01 | MODE2/2352, INDEX 01 at frame 0 |
| Data file | `ps1_game\Mortal Kombat Mythologies - Sub-Zero.bin` |
| Data file size | 538586832 bytes |
| Sectors | 228991 sectors of 2352 bytes |

The cue has one track. So the disc has no CDDA audio tracks.

## Hash

| File | Algorithm | Value |
|------|-----------|-------|
| `Mortal Kombat Mythologies - Sub-Zero.bin` | SHA-256 | `71d0e9785d7326e14b3b3745c739a355c79ddb8b64922b520571b59e465b7054` |

## Filesystem

| Item | Value |
|------|-------|
| Filesystem | ISO9660 |
| Primary volume descriptor | LBA 16 |
| Volume ID | empty |

## Boot and serial

| Item | Value |
|------|-------|
| `SYSTEM.CNF` | In the root. Start LBA 214190. 66 bytes. |
| Boot executable | `SLUS_004.76`, in the root, 821248 bytes |
| Serial | `SLUS-00476` |
| Region | NTSC-U (`SLUS-` prefix) |

The serial comes from the `BOOT=` line of `SYSTEM.CNF`. It is not guessed.
