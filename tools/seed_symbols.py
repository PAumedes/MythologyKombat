#!/usr/bin/env python3
"""Seed symbols.toml from work/symbols_sdk.json (T2.21).  Stdlib only.

Run from the repo root:
  <RETRO_TOOLS_DIR>\\python\\python.exe -I tools\\seed_symbols.py
  ... then: python tools\\sync_symbols.py  (regenerates psx_symbols.h)

What it does
  * keeps only kind == "sdk" entries (PsyQ signature names), excludes the
    gte_macro and obj_label kinds (counts printed);
  * omits the 3 suspect names unless --include-suspects (then 'guessed',
    note says "probably false positive");
  * omits loader-named entries (origin == "loader": `start`, `main`). `start`
    is already the hand-written BootEntry at the same address;
  * all entries emit=false; status "confirmed" only for names whose evidence is
    recorded in docs/SYMBOLS.md ("Spot checks" table), otherwise "guessed";
  * names: valid unique C identifiers. Duplicate SDK names get an address
    suffix (memset_8009F2A0). Names that collide with libc / POSIX / compiler
    runtime identifiers get the prefix "sdk_" (see RISKY policy below);
  * idempotent merge. Each tool-owned block is preceded by a marker comment
    "# seed_symbols:<hash>" where <hash> covers the block body. A block whose
    body no longer matches its hash was hand-edited and is never touched.
    Blocks without a marker (e.g. BootEntry) are hand-owned and never touched;
    their pc and name are reserved so the seed never duplicates them.

Risky-name policy
  psx_symbols.h emits  #define PSX_FN_<name> 0x...u  and
  #define func_<ADDR> <name>.  The PSX_FN_ prefix is always safe, but the
  func_<ADDR> alias expands to the bare name, so a name equal to a libc /
  POSIX / C99 / compiler-runtime identifier (printf, memcpy, malloc, open,
  read, setjmp, csin, __divdi3 ...) could clash with host code that includes
  both psx_symbols.h and system headers. Such names are stored as
  "sdk_<name>"; the note keeps the original SDK name. psx_symbols.h must
  never be included from generated C (generated functions are named
  func_<ADDR> and the aliases would rename them).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    print("error: need Python 3.11+ (tomllib)", file=sys.stderr)
    raise SystemExit(2)

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARK = "# seed_symbols:"
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

SUSPECTS = {
    0x80053AD0: "SsUtReverbOn",
    0x8005E1B0: "SsUtReverbOff",
    0x8008387C: "_SsSndPlay",
}

# Evidence recorded in docs/SYMBOLS.md "Spot checks" (T1.6). DrawSync,
# StartPAD, DecDCTReset and InitPAD are listed there as "Evidence not
# recorded", so they stay 'guessed'.
CONFIRMED = {
    0x800945E4: "v_wait at 0x8009472C refers to string 'VSync: timeout' (docs/SYMBOLS.md, T1.6)",
    0x8009C238: "string 'ResetGraph:jtb=' (docs/SYMBOLS.md, T1.6)",
    0x800952D8: "string 'CdInit: Init failed' (docs/SYMBOLS.md, T1.6)",
    0x8009F31C: "BIOS trampoline A(0x2a) (docs/SYMBOLS.md, T1.6)",
    0x8009F34C: "BIOS trampoline A(0x3f) (docs/SYMBOLS.md, T1.6)",
    0x8009A618: "lwc2 and COP2 RTPS word 0x4A180001 (docs/SYMBOLS.md, T1.6)",
    0x8009FF0C: "calls _card_open at 0x800A1B10 (docs/SYMBOLS.md, T1.6)",
    0x80093D68: "TestEvent loop (docs/SYMBOLS.md, T1.6)",
}

# libc / POSIX / C99 / compiler-runtime / Win32-CRT identifiers that SDK names
# can equal. Anything here, or starting with "__", gets the "sdk_" prefix.
RISKY = set("""
printf sprintf puts putchar getchar scanf sscanf fopen fclose fread fwrite
memcpy memmove memset memchr memcmp bcopy bzero strlen strcpy strncpy strcat
strncat strcmp strncmp strchr strrchr strstr malloc calloc realloc free abs
labs atoi atol rand srand exit abort qsort bsearch toupper tolower open read
write close lseek ioctl rename remove setjmp longjmp main start catan csin
ccos csincos sin cos tan sqrt div ldiv format erase signal raise time clock
""".split())


def c_name(raw: str) -> str:
    n = re.sub(r"[^A-Za-z0-9_]", "_", raw)
    if not n or n[0].isdigit():
        n = "_" + n
    return n


def esc(s: str) -> str:
    return json.dumps(s, ensure_ascii=True)


def body_text(pc: int, name: str, status: str, note: str) -> str:
    return (
        "[[func]]\n"
        f"pc = 0x{pc:08X}\n"
        f"name = {esc(name)}\n"
        "emit = false\n"
        f"status = {esc(status)}\n"
        f"note = {esc(note)}"
    )


def digest(body: str) -> str:
    return hashlib.sha1(body.strip().encode("utf-8")).hexdigest()[:12]


def split_blocks(text: str):
    """Return (preamble_lines, blocks). block = dict(marker, body, raw)."""
    lines = text.splitlines()
    starts = [i for i, l in enumerate(lines) if l.strip() == "[[func]]"]
    if not starts:
        return lines, []
    begins = []
    for i in starts:
        begins.append(i - 1 if i > 0 and lines[i - 1].startswith(MARK) else i)
    pre = lines[: begins[0]]
    blocks = []
    for k, b in enumerate(begins):
        end = begins[k + 1] if k + 1 < len(begins) else len(lines)
        chunk = lines[b:end]
        marker = None
        if chunk and chunk[0].startswith(MARK):
            marker = chunk[0][len(MARK):].strip()
            chunk = chunk[1:]
        body = "\n".join(chunk).strip("\n").rstrip()
        data = tomllib.loads(body)["func"][0]
        blocks.append({"marker": marker, "body": body,
                       "pc": int(data["pc"]) & 0xFFFFFFFF, "name": str(data["name"])})
    return pre, blocks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sdk-json", type=pathlib.Path, default=ROOT / "work" / "symbols_sdk.json")
    ap.add_argument("--symbols", type=pathlib.Path, default=ROOT / "symbols.toml")
    ap.add_argument("--include-suspects", action="store_true",
                    help="add the 3 suspect names as 'guessed' (probably false positive)")
    ap.add_argument("--dry-run", action="store_true", help="print counts, write nothing")
    args = ap.parse_args()

    data = json.loads(args.sdk_json.read_text(encoding="utf-8"))
    funcs = data["functions"]
    kinds: dict[str, int] = {}
    for f in funcs:
        kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
    sdk = [f for f in funcs if f["kind"] == "sdk"]
    print(f"input: {len(funcs)} functions; kinds {kinds}")
    print(f"excluded gte_macro: {kinds.get('gte_macro', 0)}")
    print(f"excluded obj_label: {kinds.get('obj_label', 0)}")

    text = args.symbols.read_text(encoding="utf-8") if args.symbols.is_file() else ""
    pre, blocks = split_blocks(text)

    # Classify existing blocks.
    kept = []       # list of (block) retained in place, or None placeholder for regen
    hand_pcs, hand_names = set(), set()
    owned = {}      # pc -> index in kept
    n_hand = n_edited = 0
    for b in blocks:
        is_owned = b["marker"] is not None and b["marker"] == digest(b["body"])
        if is_owned:
            b["owned"] = True
            owned[b["pc"]] = b
        else:
            b["owned"] = False
            hand_pcs.add(b["pc"])
            hand_names.add(b["name"])
            if b["marker"] is None:
                n_hand += 1
            else:
                n_edited += 1

    # Candidate seed entries.
    skipped_loader, skipped_suspect, skipped_hand_pc = [], [], []
    cand = []
    for f in sdk:
        pc = int(f["address"], 0)
        if f.get("origin") == "loader":
            skipped_loader.append((f["name"], pc))
            continue
        if pc in SUSPECTS and not args.include_suspects:
            skipped_suspect.append((f["name"], pc))
            continue
        if pc in hand_pcs:
            skipped_hand_pc.append((f["name"], pc))
            continue
        cand.append((pc, f))
    cand.sort(key=lambda t: t[0])

    counts: dict[str, int] = {}
    for _, f in cand:
        counts[f["name"]] = counts.get(f["name"], 0) + 1

    used = set(hand_names)
    new_bodies: dict[int, str] = {}
    risky_prefixed, dup_suffixed = [], []
    for pc, f in cand:
        raw = f["name"]
        name = c_name(raw)
        if name in RISKY or name.startswith("__"):
            name = "sdk_" + name
            risky_prefixed.append((raw, name, pc))
        if counts[raw] > 1:
            name = f"{name}_{pc:08X}"
            dup_suffixed.append((raw, name, pc))
        if name in used:
            name = f"{name}_{pc:08X}"
        assert IDENT.fullmatch(name), name
        used.add(name)
        suspect = pc in SUSPECTS
        status = "confirmed" if pc in CONFIRMED else "guessed"
        note = f"PsyQ SDK name '{raw}' ({f.get('origin')}), {f.get('size')} bytes; seeded from T1.6 symbols_sdk.json"
        if pc in CONFIRMED:
            note += "; evidence: " + CONFIRMED[pc]
        if suspect:
            note += "; probably false positive (below the SDK block)"
        new_bodies[pc] = body_text(pc, name, status, note)

    # Assemble output: keep existing order; regenerate unmodified owned blocks.
    out_blocks = []
    seen = set()
    n_regen = n_dropped = 0
    for b in blocks:
        if b["owned"]:
            if b["pc"] in new_bodies:
                body = new_bodies[b["pc"]]
                seen.add(b["pc"])
                out_blocks.append((digest(body), body))
                n_regen += 1
            else:
                n_dropped += 1  # no longer in the seed set
        else:
            out_blocks.append((b["marker"], b["body"]))
            seen.add(b["pc"])
    n_new = 0
    for pc in sorted(new_bodies):
        if pc not in seen:
            body = new_bodies[pc]
            out_blocks.append((digest(body), body))
            n_new += 1

    pre_text = "\n".join(pre).rstrip("\n")
    parts = []
    for marker, body in out_blocks:
        parts.append((f"{MARK}{marker}\n" if marker else "") + body)
    result = (pre_text + "\n\n" if pre_text else "") + "\n\n".join(parts) + "\n"

    total = len(out_blocks)
    n_conf = sum(1 for _, b in out_blocks if 'status = "confirmed"' in b)
    print(f"sdk-kind input entries: {len(sdk)}")
    print(f"omitted loader-named: {len(skipped_loader)} {skipped_loader}")
    print(f"omitted suspects: {len(skipped_suspect)} {[(n, hex(p)) for n, p in skipped_suspect]}"
          + ("  (use --include-suspects)" if skipped_suspect else ""))
    print(f"skipped, pc already hand-owned: {len(skipped_hand_pc)} {skipped_hand_pc}")
    print(f"duplicate names suffixed: {len(dup_suffixed)}")
    for raw, n, pc in dup_suffixed:
        print(f"   {raw} @0x{pc:08X} -> {n}")
    print(f"risky names prefixed sdk_: {len(risky_prefixed)}")
    print("   " + ", ".join(f"{r}->{n}" for r, n, _ in risky_prefixed))
    print(f"existing hand-owned blocks kept: {n_hand}; hand-edited seeded blocks kept: {n_edited}")
    print(f"seed blocks: new {n_new}, regenerated {n_regen}, dropped {n_dropped}")
    print(f"total [[func]] entries: {total} (confirmed {n_conf})")

    if args.dry_run:
        return 0
    if result != text:
        args.symbols.write_text(result, encoding="utf-8", newline="\n")
        print(f"wrote {args.symbols}")
    else:
        print(f"unchanged {args.symbols}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
