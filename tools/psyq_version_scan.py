#!/usr/bin/env python3
"""Which PsyQ signature set fits the boot EXE best? (T1.6 evidence)

Part 1  Lists the 'Ps' library-version records the ghidra_psx_ldr detector looks
        for (bytes 'P' 's' ... , big-endian version word at +6) in the EXE.
Part 2  For every signature set shipped with the extension (data/psyq/<ver>/),
        counts how many OBJ signatures match somewhere in the EXE's text
        (masked byte search, '??' = wildcard; signatures with fewer than 24
        fixed bytes are skipped as too weak).

Input  : work/disc/SLUS_004.76 (read only), <ghidra>/Ghidra/Extensions/ghidra_psx_ldr/data/psyq
Output : work/psyq_version_scan.json (deterministic) and a table on stdout.
Usage  : python -I tools/psyq_version_scan.py [--root PATH] [--ghidra DIR]
Stdlib only.
"""
import argparse
import json
import os
import re

RETRO_TOOLS = os.environ.get("RETRO_TOOLS_DIR") or os.path.join(os.path.expanduser("~"), "retro-tools")
DEFAULT_GHIDRA = os.path.join(RETRO_TOOLS, "ghidra", "ghidra_12.1.4_PUBLIC")
TEXT_BASE = 0x80010000
HDR = 0x800


def compile_sig(sig):
    parts = sig.split()
    fixed = sum(1 for p in parts if p != "??")
    pat = b"".join(b"." if p == "??" else re.escape(bytes([int(p, 16)])) for p in parts)
    return fixed, re.compile(pat, re.DOTALL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--ghidra", default=DEFAULT_GHIDRA)
    a = ap.parse_args()
    exe = open(os.path.join(a.root, "work", "disc", "SLUS_004.76"), "rb").read()
    text = exe[HDR:]
    sigdir = os.path.join(a.ghidra, "Ghidra", "Extensions", "ghidra_psx_ldr", "data", "psyq")

    records = []
    for m in re.finditer(rb"Ps", text):
        w = text[m.start():m.start() + 8]
        if len(w) == 8 and (w[2] & 0xE0) == 0 and (w[6] & 0x88) == 0 and (w[7] & 0xEE) == 0:
            ver = (w[6] << 8) | w[7]
            records.append({"address": "0x%08X" % (TEXT_BASE + m.start()), "bytes": w.hex(),
                            "lib_byte": w[2], "version_word_be": "0x%04X" % ver})
    print("Ps version records: %d, version words: %s" % (
        len(records), sorted(set(r["version_word_be"] for r in records))))

    result = {"ps_records": records, "sets": {}}
    for ver in sorted(d for d in os.listdir(sigdir) if os.path.isdir(os.path.join(sigdir, d)) and d[0].isdigit()):
        hits = total = 0
        for fn in sorted(os.listdir(os.path.join(sigdir, ver))):
            if not fn.endswith(".json") or fn == "patches.json":
                continue
            for item in json.load(open(os.path.join(sigdir, ver, fn), encoding="utf-8")):
                if "sig" not in item:
                    continue
                fixed, rx = compile_sig(item["sig"])
                if fixed < 24:
                    continue
                total += 1
                if rx.search(text):
                    hits += 1
        result["sets"][ver] = {"obj_sigs_considered": total, "obj_sigs_matched": hits}
        print("set %-5s considered %5d matched %4d" % (ver, total, hits), flush=True)
    out = os.path.join(a.root, "work", "psyq_version_scan.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, sort_keys=True)
        f.write("\n")
    print("wrote", os.path.relpath(out, a.root))


if __name__ == "__main__":
    main()
