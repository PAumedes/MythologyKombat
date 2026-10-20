# COVERAGE

Static coverage of the boot EXE (`SLUS_004.76`). This page holds counts and addresses only. It was made in T2.2.

The numbers come from `tools\check_seeds.py` and `tools\ghidra_sdk_names.py --all-funcs`. The commands are in `docs/SETUP.md` (T2.2). Open items are in `docs/OPEN_QUESTIONS.md` (questions 81 to 90 and 213 to 219). Counts marked T2.8 are after seed growth (`docs/SETUP.md`, "Seed growth from dispatch misses (T2.8)"). Other counts are from T2.2.

## Text range

| Item | Value |
|------|-------|
| Text range | `0x80010000` to `0x800D8000` |
| Source | EXE header |

## Seeds

| Item | Value |
|------|-------|
| Lines in seed file | 1182 (T2.8). 1175 at T2.2 |
| Unique seeds | 1177 (T2.8). 1175 at T2.2 |
| Unaligned or out of range | 0 |
| Entry `0x80090E70` in the seeds | Yes |
| Seed classes | verified 453, high 485, medium 86, low 149, data 2 (T2.2; not re-counted at T2.8) |
| Seeds that are also Ghidra function starts | 1069 (T2.2) |
| Seeds that are not Ghidra function starts | 108 (106 at T2.2) |

- At T2.2, the 106 seeds that were not Ghidra starts were: low 56, medium 43, high 4, data 2, verified 1. T2.8 added two more. Their classes are not recorded here.
- Their addresses are in `work\seed_report.json` under `seed_classification.anomalies`.
- All 1177 seeds are analyzer function starts (T2.8 `check_seeds` run).

## Analyzer (`psxrecomp-analyze`)

Only the function count was re-checked at T2.8. The other rows are T2.2 values.

Command form:

```
psxrecomp-analyze <EXE> --out DIR --emit-tsv F --seeds F --quiet
```

| Item | Value |
|------|-------|
| Functions | 2322 (T2.8; was 2320) |
| Function classes | verified 565, high 893, medium 418, low 441, data 3 |
| Partial decodes | 4 |
| Instructions decoded | 152797 |
| Image covered by code | 74.6% |
| Bytes in no code function | 208012 (25.4%) |
| Functions reachable from entry | 1516 |
| Orphan functions | 804 |
| Direct calls | 10750 |
| Jump tables | 29 (392 targets) |
| Indirect sites | 240 |

Indirect sites by kind:

| Kind | Count |
|------|-------|
| Unresolved | 133 (129 `jalr`, 4 `jr`) |
| BIOS dispatch | 50 |
| `call_ptr` static slots | 28 |
| Jump tables | 29 |

## Ghidra against the analyzer

The counts in this section are T2.2 values. T2.8 did not re-run them.

Ghidra export: `work\ghidra_funcs_all.txt`, 1730 entries (1552 CODE, 153 GTEMAC, 25 RAM).

| Item | Count |
|------|-------|
| Ghidra functions in text, also an analyzer function | 1227 |
| Ghidra functions in text only | 325 |
| Analyzer functions only | 1093 |
| Named Ghidra functions in text | 778 |
| Named Ghidra functions in text that the analyzer finds | 453 |

- The 325 Ghidra-only entries all carry PsyQ-style or OBJ label names.
- 323 of them lie inside an analyzer function.
- 2 lie in no analyzer function: `cb_data` at `0x8009761C` and `_spu_2pitch` at `0x800A8D18`.
- The 1093 analyzer-only functions are: verified 101, high 379, medium 331, low 279, data 3. 106 of them are seeds.

## Overlay window

Window: `0x80130FF8` to `0x8013C720`. See `docs/EXE_OVERLAYS.md` for the overlay load address.

| Item | Value |
|------|-------|
| JAL sites into the window | 34 |
| Unique JAL targets | 26 (`0x80130FF8` to `0x8013B934`) |
| Most called target | `0x80133500` (5 calls) |
| Second most called target | `0x801310C0` (3 calls) |
| J sites into the window | 0 |
| Seeds in the window | 0 |
| `lui` plus `addiu` or `ori` sites that point into the window | 29 (23 distinct constants) |

- The last row is informational. The reviewer found it by hand. It is not part of the analyzer count.

## Seed growth (T2.8)

See `docs/SETUP.md` ("Seed growth from dispatch misses (T2.8)").

| Item | T2.2 | T2.8 |
|------|------|------|
| Seeds | 1175 | 1177 |
| Analyzer functions | 2320 | 2322 |

- Two seeds were added: `0x8003A674` (vet ACCEPT) and `0x80032760` (manual, D15 in `docs/DECISIONS.md`).
- Both lie in the text range, below the overlay window.
