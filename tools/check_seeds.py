#!/usr/bin/env python3
"""T2.2 - seed sanity and static coverage baseline.  Stdlib only; run with python -I.

1. Validates seeds/ghidra_funcs.txt: every non-comment line is a word-aligned address
   inside the boot EXE text range (bounds read from the PS-X EXE header, not hard-coded).
2. Runs psxrecomp-analyze (unless --no-run) on work/disc/SLUS_004.76 with those seeds.
3. Compares analyzer function starts with Ghidra's full function list
   (work/ghidra_funcs_all.txt, made by `tools/ghidra_sdk_names.py --all-funcs`) and
   cross-checks the named set in work/symbols_sdk.json.
4. Reports indirect-transfer gaps and J/JAL targets landing in the overlay window.

Outputs: work/seed_report.json (deterministic: no timestamps, no absolute paths) and a
readable summary on stdout (also deterministic). Exit 1 if a seed is invalid/duplicate.
"""
import argparse, json, os, struct, subprocess, sys

OVL_LO, OVL_HI = 0x80130FF8, 0x8013C720   # docs/EXE_OVERLAYS.md; hi exclusive


def h(v):
    return "0x%08X" % v


def parse_seeds(path):
    seeds, bad = [], []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        t = line.split("#", 1)[0].strip()
        if not t:
            continue
        try:
            seeds.append((n, int(t, 16)))
        except ValueError:
            bad.append({"line": n, "text": t, "problem": "not a hex address"})
    return seeds, bad


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-run", action="store_true", help="reuse existing work/analysis")
    a = ap.parse_args()

    def J(*p):
        return os.path.join(root, *p)

    exe = open(J("work", "disc", "SLUS_004.76"), "rb").read()
    assert exe[:8] == b"PS-X EXE"
    entry, _gp, load, tsize = struct.unpack_from("<4I", exe, 0x10)
    lo, hi = load, load + tsize
    text = exe[0x800:0x800 + tsize]
    report = {"text_range": [h(lo), h(hi)], "entry": h(entry)}

    # ---- 1. seed sanity
    seeds, bad = parse_seeds(J("seeds", "ghidra_funcs.txt"))
    seen, dups = {}, []
    for n, v in seeds:
        if v in seen:
            dups.append({"addr": h(v), "lines": [seen[v], n]})
        seen.setdefault(v, n)
    for n, v in seeds:
        if v & 3:
            bad.append({"line": n, "text": h(v), "problem": "unaligned"})
        elif not (lo <= v < hi):
            bad.append({"line": n, "text": h(v), "problem": "outside text range"})
    sset = set(seen)
    report["seeds"] = {"count": len(seeds), "unique": len(sset), "entry_in_file": entry in sset,
                       "unique_plus_entry": len(sset | {entry}),
                       "duplicates": dups, "invalid": bad}

    # ---- 2. analyzer
    ana = J("work", "analysis")
    if not a.no_run:
        env = dict(os.environ)
        env["PATH"] = os.pathsep.join([r"<RETRO_TOOLS_DIR>\cmake-clang\bin",
                                       r"C:\Program Files\Git\bin", env.get("PATH", "")])
        os.makedirs(ana, exist_ok=True)
        r = subprocess.run([J("psxrecomp", "recompiler", "build", "psxrecomp-analyze.exe"),
                            J("work", "disc", "SLUS_004.76"), "--out", ana,
                            "--emit-tsv", os.path.join(ana, "functions.tsv"),
                            "--seeds", J("seeds", "ghidra_funcs.txt"), "--quiet"],
                           env=env, capture_output=True, text=True, cwd=root)
        if r.returncode != 0:
            sys.exit("analyzer failed rc=%d\n%s" % (r.returncode, r.stderr[-2000:]))
    A = json.load(open(os.path.join(ana, "analysis.json")))
    funcs = A["functions"]
    afn = {f["addr"]: f for f in funcs}
    astarts = set(afn)
    report["analyzer"] = {"stats": A["stats"], "function_count": len(funcs),
                          "by_confidence": {}, "partial": sum(1 for f in funcs if f["partial"]),
                          "is_data": sum(1 for f in funcs if f["is_data"])}
    for f in funcs:
        c = f["confidence"]
        report["analyzer"]["by_confidence"][c] = report["analyzer"]["by_confidence"].get(c, 0) + 1
    ranges = sorted((f["addr"], f["end"]) for f in funcs)

    def containing(addr):
        lo_, hi_ = 0, len(ranges)
        while lo_ < hi_:
            m = (lo_ + hi_) // 2
            if ranges[m][0] <= addr:
                lo_ = m + 1
            else:
                hi_ = m
        if lo_ and addr < ranges[lo_ - 1][1]:
            return ranges[lo_ - 1][0]
        return None

    # ---- 3. Ghidra
    G = {}
    for line in open(J("work", "ghidra_funcs_all.txt"), encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        G[int(p[0], 16)] = (p[1], p[2])
    gram = {x for x in G if lo <= x < hi}
    named = json.load(open(J("work", "symbols_sdk.json")))["functions"]
    named_a = {int(x["address"], 16) for x in named}
    outside = sorted(set(G) - gram)
    only_g = sorted(gram - astarts)
    only_a = sorted(astarts - gram)
    both = gram & astarts
    report["ghidra"] = {
        "total_functions": len(G), "in_exe_text": len(gram),
        "outside_exe_text": len(outside),
        "outside_blocks": sorted({G[x][1] for x in outside}),
        "named_total": len(named_a), "named_in_exe_text": len(named_a & gram),
        "named_not_in_full_list": len(named_a - set(G)),
        "named_found_by_analyzer": len(named_a & astarts),
        "named_missed_by_analyzer": [h(x) for x in sorted((named_a & gram) - astarts)],
    }
    report["compare"] = {
        "analyzer_found": len(astarts), "ghidra_in_text": len(gram), "overlap": len(both),
        "ghidra_only": len(only_g), "analyzer_only": len(only_a),
        "ghidra_only_inside_analyzer_function": sum(1 for x in only_g if containing(x) is not None),
        "ghidra_only_in_no_analyzer_function": sum(1 for x in only_g if containing(x) is None),
        "analyzer_only_by_confidence": {},
        "analyzer_only_that_are_seeds": sum(1 for x in only_a if x in sset),
        "ghidra_only_detail": [{"addr": h(x), "name": G[x][0],
                                "inside_analyzer_func": (h(containing(x)) if containing(x) is not None else None)}
                               for x in only_g],
        "analyzer_only_addrs": [h(x) for x in only_a],
    }
    for x in only_a:
        c = afn[x]["confidence"]
        d = report["compare"]["analyzer_only_by_confidence"]
        d[c] = d.get(c, 0) + 1

    # seed classification
    cls = {"analyzer_function_start": 0, "inside_other_analyzer_function": 0,
           "in_no_analyzer_function": 0, "also_ghidra_function_start": 0,
           "not_ghidra_function_start": 0}
    odd = []
    seed_conf = {}
    for v in sorted(sset):
        if v in astarts:
            cls["analyzer_function_start"] += 1
            c = afn[v]["confidence"]
            seed_conf[c] = seed_conf.get(c, 0) + 1
        elif containing(v) is not None:
            cls["inside_other_analyzer_function"] += 1
            odd.append({"addr": h(v), "kind": "inside analyzer function", "func": h(containing(v))})
        else:
            cls["in_no_analyzer_function"] += 1
            odd.append({"addr": h(v), "kind": "in no analyzer function"})
        if v in G:
            cls["also_ghidra_function_start"] += 1
        else:
            cls["not_ghidra_function_start"] += 1
            odd.append({"addr": h(v), "kind": "not a Ghidra function start",
                        "analyzer_confidence": afn[v]["confidence"] if v in afn else None})
    report["seed_classification"] = dict(cls, by_analyzer_confidence=seed_conf, anomalies=odd)

    # ---- 4. indirect gaps
    I = json.load(open(os.path.join(ana, "indirect.json")))["sites"]
    unres = [s for s in I if s["classification"] == "unresolved"]
    kinds = {}
    for s in I:
        k = s["classification"].split(":")[0]
        kinds[k] = kinds.get(k, 0) + 1
    report["indirect"] = {
        "total_sites": len(I), "by_class": dict(sorted(kinds.items())),
        "unresolved": len(unres),
        "unresolved_jalr": sum(1 for s in unres if s["kind"] == "jalr"),
        "unresolved_jr": sum(1 for s in unres if s["kind"] == "jr"),
        "unresolved_sites": [{"pc": h(s["pc"]), "kind": s["kind"], "reg": s["reg"], "func": h(s["func"])}
                             for s in sorted(unres, key=lambda s: s["pc"])],
    }

    # ---- 5. J/JAL into the overlay window
    def scan(pcs):
        out = {"jal": {}, "j": {}}
        for pc in pcs:
            w = struct.unpack_from("<I", text, pc - load)[0]
            op = w >> 26
            if op in (2, 3):
                tgt = ((pc + 4) & 0xF0000000) | ((w & 0x03FFFFFF) << 2)
                if OVL_LO <= tgt < OVL_HI:
                    out["jal" if op == 3 else "j"].setdefault(tgt, []).append(pc)
        return out

    def pack(o, targets=True):
        d = {"jal_sites": sum(len(v) for v in o["jal"].values()),
             "jal_unique_targets": len(o["jal"]),
             "j_sites": sum(len(v) for v in o["j"].values()),
             "j_unique_targets": len(o["j"])}
        if targets:
            d["targets"] = [{"target": h(t), "jal_from": [h(x) for x in o["jal"].get(t, [])],
                             "j_from": [h(x) for x in o["j"].get(t, [])]}
                            for t in sorted(set(o["jal"]) | set(o["j"]))]
        return d

    fpcs = [pc for f in funcs if not f["is_data"] for pc in range(f["addr"], f["end"], 4)]
    infn = pack(scan(fpcs))
    raw = pack(scan(range(lo, hi, 4)), targets=False)
    infn["raw_only_extra_sites"] = (raw["jal_sites"] + raw["j_sites"]
                                    - infn["jal_sites"] - infn["j_sites"])
    ov_seeds = sorted(x for x in sset if OVL_LO <= x < OVL_HI)
    report["overlay_window"] = {"range": [h(OVL_LO), h(OVL_HI)], "inside_analyzer_functions": infn,
                                "raw_text_scan_incl_data": raw, "seeds_in_window": [h(x) for x in ov_seeds]}

    with open(J("work", "seed_report.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=1, sort_keys=True)
        f.write("\n")

    # ---- summary
    C = report["compare"]
    print("Text range from EXE header : %s .. %s (entry %s)" % (h(lo), h(hi), h(entry)))
    print("Seeds                      : %d lines, %d unique, %d duplicates, %d invalid; entry in file: %s; unique+entry %d"
          % (len(seeds), len(sset), len(dups), len(bad), entry in sset, len(sset | {entry})))
    for b in bad:
        print("  INVALID line %d: %s (%s)" % (b["line"], b["text"], b["problem"]))
    print("Seed classification        :", json.dumps(cls, sort_keys=True))
    print("  analyzer confidence      :", json.dumps(seed_conf, sort_keys=True))
    print("  anomalies                : %d" % len(odd))
    print("Analyzer functions         : %d %s, partial %d, data %d" % (
        len(funcs), json.dumps(report["analyzer"]["by_confidence"], sort_keys=True),
        report["analyzer"]["partial"], report["analyzer"]["is_data"]))
    print("Ghidra functions           : %d total, %d in EXE text, %d elsewhere (blocks %s)" % (
        len(G), len(gram), len(outside), ",".join(report["ghidra"]["outside_blocks"])))
    print("Named (symbols_sdk)        : %d, in text %d, found by analyzer %d, missed %d" % (
        len(named_a), len(named_a & gram), len(named_a & astarts),
        len(report["ghidra"]["named_missed_by_analyzer"])))
    print("Overlap                    : %d" % C["overlap"])
    print("Ghidra-only starts         : %d (inside an analyzer function %d, in none %d)" % (
        C["ghidra_only"], C["ghidra_only_inside_analyzer_function"], C["ghidra_only_in_no_analyzer_function"]))
    print("Analyzer-only starts       : %d (by confidence %s; seeds among them %d)" % (
        C["analyzer_only"], json.dumps(C["analyzer_only_by_confidence"], sort_keys=True),
        C["analyzer_only_that_are_seeds"]))
    I_ = report["indirect"]
    print("Indirect sites             : %d total %s; UNRESOLVED %d (jalr %d, jr %d)" % (
        I_["total_sites"], json.dumps(I_["by_class"], sort_keys=True), I_["unresolved"],
        I_["unresolved_jalr"], I_["unresolved_jr"]))
    print("Overlay window %s..%s" % (h(OVL_LO), h(OVL_HI)))
    print("  in analyzer functions    : %d JAL sites -> %d targets; %d J sites -> %d targets (raw-only extra sites %d)" % (
        infn["jal_sites"], infn["jal_unique_targets"], infn["j_sites"], infn["j_unique_targets"],
        infn["raw_only_extra_sites"]))
    print("  raw text scan (incl data): %s" % json.dumps(raw, sort_keys=True))
    print("  seeds in window          : %d" % len(ov_seeds))
    for t in infn["targets"]:
        print("    %s  jal from %s%s" % (t["target"], ",".join(t["jal_from"]) or "-",
                                         ("  j from " + ",".join(t["j_from"])) if t["j_from"] else ""))
    sys.exit(1 if (bad or dups) else 0)


if __name__ == "__main__":
    main()
