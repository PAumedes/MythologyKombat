#!/usr/bin/env python3
r"""T2.8 - append ACCEPTed dispatch-miss addresses to seeds/ghidra_funcs.txt.  Stdlib only; run with python -I.

  python -I tools/grow_seeds.py MISS_FILE --batch ID [--dry-run]
  python -I tools/grow_seeds.py --batch ID --manual 0xADDR [--manual ...] --reason TEXT [--dry-run]

MISS_FILE is the output of psxrecomp/tools/collect_game_misses.py (work\dirty_ram_misses.txt).
The miss list is vetted by psxrecomp/tools/vet_seeds.py --game game.toml (run here as a child
process); ONLY addresses it marks [ACCEPT] are considered. WARN and REJECT are listed, never written.
An ACCEPTed address is appended only if it is word-aligned, inside the boot EXE text range read from
the PS-X EXE header (not the overlay window), and not already a seed.
--manual adds an address a human has reviewed (for example a vet_seeds WARN). It is not vetted
here, but gets the same alignment, range and duplicate checks. The comment line is then
"# manual ID: TEXT" followed by the address(es). Without --manual, MISS_FILE is required.
Existing lines are never changed or removed. A batch is one comment line
("# batch ID: source 'dispatch misses T2.8', N address(es)") followed by the new addresses, sorted,
in the file's existing line ending style. If nothing qualifies the file is not touched.
Prints counts. Exit 0 on success (including "nothing to add"), 2 on setup errors.
"""
import argparse, os, re, struct, subprocess, sys


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("miss_file", nargs="?")
    ap.add_argument("--manual", action="append", default=[], help="reviewed address to add (repeatable)")
    ap.add_argument("--reason", help="required with --manual; goes in the comment line")
    ap.add_argument("--batch", required=True, help="batch id for the header comment, e.g. T2.8-1")
    ap.add_argument("--seeds", default=os.path.join(root, "seeds", "ghidra_funcs.txt"))
    ap.add_argument("--game", default=os.path.join(root, "game.toml"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    exe = open(os.path.join(root, "work", "disc", "SLUS_004.76"), "rb").read(0x20)
    if exe[:8] != b"PS-X EXE":
        sys.exit("setup: work/disc/SLUS_004.76 is not a PS-X EXE")
    _entry, _gp, load, tsize = struct.unpack_from("<4I", exe, 0x10)
    lo, hi = load, load + tsize

    if a.manual and not a.reason:
        sys.exit("setup: --manual needs --reason")
    if not a.manual and not a.miss_file:
        sys.exit("setup: give MISS_FILE or --manual")
    vet = os.path.join(root, "psxrecomp", "tools", "vet_seeds.py")
    verdicts = {"ACCEPT": [], "WARN": [], "REJECT": []}
    out_lines = []
    if a.manual:
        verdicts["ACCEPT"] = [int(x, 0) for x in a.manual]
    else:
        r = subprocess.run([sys.executable, "-I", vet, "--game", a.game, a.miss_file],
                           capture_output=True, text=True, cwd=root)
        if r.returncode != 0:
            sys.exit("vet_seeds failed rc=%d\n%s%s" % (r.returncode, r.stdout[-1500:], r.stderr[-1500:]))
        out_lines = r.stdout.splitlines()
    for line in out_lines:
        m = re.match(r"\s*\[\s*(ACCEPT|WARN|REJECT)\s*\]\s+(0x[0-9A-Fa-f]+)", line)
        if m:
            verdicts[m.group(1)].append(int(m.group(2), 16))

    raw = open(a.seeds, "rb").read()
    text = raw.decode("utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    existing = set()
    for ln in text.splitlines():
        t = ln.split("#", 1)[0].strip()
        if t:
            existing.add(int(t, 16))

    add, skipped = [], []
    for v in sorted(set(verdicts["ACCEPT"])):
        if v & 3:
            skipped.append((v, "unaligned"))
        elif not lo <= v < hi:
            skipped.append((v, "outside boot EXE text [0x%08X,0x%08X)" % (lo, hi)))
        elif v in existing:
            skipped.append((v, "already a seed"))
        else:
            add.append(v)

    print("vet verdicts: ACCEPT %d, WARN %d, REJECT %d"
          % (len(verdicts["ACCEPT"]), len(verdicts["WARN"]), len(verdicts["REJECT"])))
    for k in ("WARN", "REJECT"):
        for v in sorted(verdicts[k]):
            print("  %s (not seeded): 0x%08X" % (k, v))
    for v, why in skipped:
        print("  ACCEPT skipped 0x%08X: %s" % (v, why))
    print("seeds before: %d addresses; to append: %d" % (len(existing), len(add)))
    if not add:
        print("nothing to add; %s not modified" % a.seeds)
        return 0
    if a.manual:
        block = ["# manual %s: %s" % (a.batch, a.reason)]
    else:
        block = ["# batch %s: source 'dispatch misses T2.8', %d address(es)" % (a.batch, len(add))]
    block += ["0x%08X" % v for v in add]
    for ln in block:
        print("  +" + ln)
    if a.dry_run:
        print("dry run: %s not modified" % a.seeds)
        return 0
    out = text if text.endswith(("\n", "\r")) or not text else text + nl
    out += nl.join(block) + nl
    with open(a.seeds, "wb") as f:
        f.write(out.encode("utf-8"))
    print("appended %d; seeds after: %d addresses" % (len(add), len(existing) + len(add)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
