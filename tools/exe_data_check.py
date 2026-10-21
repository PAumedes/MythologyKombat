#!/usr/bin/env python3
"""Does the release exe embed game DATA bytes? (OPEN_QUESTIONS Q280). Stdlib only.

Method (read-only on the disc image; all output under work/):
  1. Read the boot executable (/SLUS_004.76) and every file under /OVERLAYS from the
     disc image in memory, using tools/disc_list.py (Track, build). With --all-disc,
     every other Mode2/Form1 file except /MOVIES is added (stride is then coarser).
     Nothing is written to ps1_game/.
  2. Extract the release zip into a NEW (or empty / identical) directory under work/
     and locate MythologyKombat.exe there.
  3. Index disc data as WINDOW-byte windows (default 32) taken every STRIDE bytes
     (default 16), skipping windows that are trivial (zero-heavy, <8 distinct byte
     values, or repeating with a period <= 4). Index key = first 8 bytes.
     Any NON-TRIVIAL exact run >= WINDOW+STRIDE-1 bytes (default 47) contains at least
     one indexed window and is found. A run whose covering windows were all skipped as
     trivial, or dropped because their key is over-common, can be MISSED. The disc bytes
     not covered by any indexed window are counted and reported (count and percent,
     never content) so the blind spot is known; there is no fallback pass for them.
  4. Scan EVERY byte offset of the exe (and of every other zip member) for those
     keys, verify the full window, extend left/right against the disc file, and keep
     maximal runs >= MINRUN bytes (default 64) with <= 50% zero bytes.
  5. Report per disc file: exe bytes matched (union of runs), run count, longest run;
     split by PE section (.text/.rdata/.data/...) via manual PE header parsing.
  6. Strings: printable ASCII runs (>= 8 chars, >= 5 letters) of the disc exe and
     overlays are searched for inside the exe's printable runs.

Usage:
  python -I tools/exe_data_check.py [--zip PATH] [--extract-dir DIR] [--cue PATH]
        [--window 32] [--stride 16] [--minrun 64] [--all-disc] [--skip-other-members]
        [--out work/exe_data_check.json]
Exit 0 always on a completed analysis (the conclusion is in the printed summary).
"""
import argparse
import bisect
import hashlib
import json
import os
import re
import struct
import sys
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import disc_list  # noqa: E402
from disc_identify import DiscError  # noqa: E402
from disc_classify import open_track  # noqa: E402

KEY = 8
MAX_KEY_ENTRIES = 256


def die(msg):
    print("ERROR: %s" % msg, file=sys.stderr)
    sys.exit(2)


def under_work(path):
    w = os.path.realpath(os.path.join(ROOT, "work"))
    p = os.path.realpath(path)
    return os.path.commonpath([w, p]) == w


# ------------------------------------------------------------------ PE ----

def parse_pe(data):
    if data[:2] != b"MZ":
        return None
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        return None
    nsec, = struct.unpack_from("<H", data, pe + 6)
    optsz, = struct.unpack_from("<H", data, pe + 20)
    secoff = pe + 24 + optsz
    secs = []
    for i in range(nsec):
        o = secoff + 40 * i
        name = data[o:o + 8].rstrip(b"\0").decode("latin1")
        vsize, va, rawsz, rawptr = struct.unpack_from("<IIII", data, o + 8)
        ch, = struct.unpack_from("<I", data, o + 36)
        secs.append({"name": name, "va": va, "vsize": vsize, "raw_off": rawptr,
                     "raw_size": rawsz, "flags": "0x%08x" % ch})
    return secs


def section_of(secs, off):
    if not secs:
        return "(not PE)"
    for s in secs:
        if s["raw_off"] <= off < s["raw_off"] + s["raw_size"]:
            return s["name"]
    return "(headers/overlay)"


# ------------------------------------------------------------- disc read ----

def load_disc(cue, all_disc):
    """Return {path: bytes} for SLUS_004.76, /OVERLAYS/* (and optionally more)."""
    listing = disc_list.build(cue)
    trk, _ = open_track(cue)
    out = {}
    try:
        for f in listing["files"]:
            p = f["path"]
            up = p.upper()
            want = up == "/SLUS_004.76" or up.startswith("/OVERLAYS/")
            if all_disc and not want:
                want = (not up.startswith("/MOVIES/") and not f["xa_flagged"]
                        and f["xa_record"] is not None
                        and f["xa_record"]["mode2_form1"] and f["size_bytes"] > 0)
            if not want:
                continue
            if f["xa_flagged"] or (f["xa_record"] and not f["xa_record"]["mode2_form1"]):
                print("skip (XA/Form2): %s" % p)
                continue
            out[p] = trk.read_extent(f["lba"], f["size_bytes"])
    finally:
        trk.close()
    return out


# ----------------------------------------------------------------- index ----

def trivial(w):
    if w.count(0) * 2 > len(w):
        return True
    if len(set(w)) < 8:
        return True
    for per in (1, 2, 3, 4):
        if w[per:] == w[:-per]:
            return True
    return False


def build_index(files, window, stride):
    names = sorted(files)
    idx = {}
    total = skipped = 0
    for fi, n in enumerate(names):
        d = files[n]
        for off in range(0, len(d) - window + 1, stride):
            w = d[off:off + window]
            total += 1
            if trivial(w):
                skipped += 1
                continue
            idx.setdefault(w[:KEY], []).append((fi, off))
    dropped_keys = dropped_windows = 0
    dropped = set()
    for k in [k for k, v in idx.items() if len(v) > MAX_KEY_ENTRIES]:
        dropped_keys += 1
        dropped_windows += len(idx[k])
        dropped.update(idx[k])
        del idx[k]
    covered = {}
    for v in idx.values():
        for fi, off in v:
            covered.setdefault(fi, []).append((off, off + window))
    unc_bytes = unc_ranges = disc_bytes = 0
    for fi, n in enumerate(names):
        disc_bytes += len(files[n])
        cov = merge_ivs(covered.get(fi, []))
        pos = 0
        for s_, e_ in cov + [[len(files[n]), len(files[n])]]:
            if s_ > pos:
                unc_bytes += s_ - pos
                unc_ranges += 1
            pos = max(pos, e_)
    return names, idx, {"windows": total, "trivial_skipped": skipped,
                        "trivial_skipped_pct": round(100.0 * skipped / max(total, 1), 2),
                        "indexed_keys": len(idx), "dropped_common_keys": dropped_keys,
                        "dropped_windows": dropped_windows,
                        "dropped_windows_pct": round(100.0 * dropped_windows / max(total, 1), 2),
                        "disc_bytes": disc_bytes,
                        "uncovered_disc_bytes": unc_bytes, "uncovered_ranges": unc_ranges,
                        "uncovered_disc_pct": round(100.0 * unc_bytes / max(disc_bytes, 1), 2)}


# ------------------------------------------------------------------ scan ----

def scan(target, names, files, idx, window, minrun):
    """Return list of runs (file_name, exe_off, disc_off, length)."""
    runs = []
    last_end = {}
    n = len(target)
    get = idx.get
    for i in range(n - window + 1):
        cand = get(target[i:i + KEY])
        if cand is None:
            continue
        for fi, doff in cand:
            fname = names[fi]
            k = (fi, doff - i)
            if last_end.get(k, -1) > i:
                continue
            d = files[fname]
            if target[i:i + window] != d[doff:doff + window]:
                continue
            a, b = i, i + window            # exe interval
            da = doff
            while a > 0 and da > 0 and target[a - 1] == d[da - 1]:
                a -= 1
                da -= 1
            db = doff + window
            while b < n and db < len(d) and target[b] == d[db]:
                b += 1
                db += 1
            last_end[k] = b
            if b - a >= minrun:
                seg = target[a:b]
                if seg.count(0) * 2 <= len(seg):
                    runs.append((fname, a, da, b - a))
    return runs


def union_len(ivs):
    tot = 0
    cur_s = cur_e = None
    for s, e in sorted(ivs):
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                tot += cur_e - cur_s
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        tot += cur_e - cur_s
    return tot


def merge_ivs(ivs, gap=0):
    out = []
    for s, e in sorted(ivs):
        if out and s <= out[-1][1] + gap:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def summarize(runs, secs):
    per = {}
    for f, a, da, ln in runs:
        per.setdefault(f, []).append((a, a + ln, da))
    res = {}
    for f in sorted(per):
        r = per[f]
        secb = {}
        for a, b, _ in r:
            # split by section boundaries
            x = a
            while x < b:
                sn = section_of(secs, x)
                end = b
                for s in secs or []:
                    if s["name"] == sn and s["raw_off"] <= x < s["raw_off"] + s["raw_size"]:
                        end = min(b, s["raw_off"] + s["raw_size"])
                        break
                secb.setdefault(sn, []).append((x, end))
                x = end
        res[f] = {
            "runs": len(r),
            "exe_bytes_matched_union": union_len([(a, b) for a, b, _ in r]),
            "longest_run": max(b - a for a, b, _ in r),
            "by_section": {k: union_len(v) for k, v in sorted(secb.items())},
            "exe_regions": [[s, e, section_of(secs, s)] for s, e in merge_ivs([(a, b) for a, b, _ in r], 256)][:12],
        }
    return res


# --------------------------------------------------------------- strings ----

PRINT = re.compile(rb"[\x20-\x7e]{8,}")


def disc_strings(files):
    out = {}
    for n, d in files.items():
        for m in PRINT.finditer(d):
            s = m.group()
            if sum(c in b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ" for c in s) >= 5:
                out.setdefault(s, set()).add(n)
    return out


def string_check(target, secs, dstr):
    offs, parts = [], []
    pos = 0
    for m in PRINT.finditer(target):
        offs.append(pos)
        parts.append(m.group())
        pos += len(m.group()) + 1
    blob = b"\n".join(parts)
    starts = []
    pos = 0
    # file offsets of each run, in order
    for m in PRINT.finditer(target):
        starts.append(m.start())
    found = []
    for s, srcs in dstr.items():
        j = blob.find(s)
        if j >= 0:
            k = bisect.bisect_right(offs, j) - 1
            fo = starts[k] + (j - offs[k])
            found.append((s, sorted(srcs), fo, section_of(secs, fo)))
    return found, len(parts)


# ------------------------------------------------------------------ main ----

def extract_zip(zpath, edir):
    z = zipfile.ZipFile(zpath)
    names = z.namelist()
    for n in names:
        if n.startswith("/") or ".." in n.split("/") or "\\" in n or ":" in n:
            die("unsafe zip member name: %r" % n)
    if os.path.isdir(edir) and os.listdir(edir):
        # reuse only if it is an exact extraction of this zip
        for i in z.infolist():
            if i.is_dir():
                continue
            p = os.path.join(edir, *i.filename.split("/"))
            if not os.path.isfile(p) or os.path.getsize(p) != i.file_size:
                die("%s exists, is not empty and does not match the zip (%s); "
                    "pass a new empty --extract-dir" % (edir, i.filename))
        print("reusing identical extraction in %s" % edir)
        return z
    os.makedirs(edir, exist_ok=True)
    for i in z.infolist():
        if i.is_dir():
            continue
        p = os.path.join(edir, *i.filename.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with z.open(i) as src, open(p, "wb") as dst:
            while True:
                b = src.read(1 << 20)
                if not b:
                    break
                dst.write(b)
    print("extracted %d members to %s" % (len(names), edir))
    return z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=os.path.join(ROOT, "work", "release", "rc1-a",
                                                  "MythologyKombat-0.1.0-Windows-x64.zip"))
    ap.add_argument("--extract-dir", default=os.path.join(ROOT, "work", "exe_data_check", "zip"))
    ap.add_argument("--cue")
    ap.add_argument("--window", type=int, default=32)
    ap.add_argument("--stride", type=int, default=16)
    ap.add_argument("--minrun", type=int, default=64)
    ap.add_argument("--all-disc", action="store_true")
    ap.add_argument("--skip-other-members", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "exe_data_check.json"))
    a = ap.parse_args()
    for p in (a.extract_dir, a.out):
        if not under_work(p):
            die("output path must be under work/: %s" % p)
    cue = a.cue
    if not cue:
        d = os.path.join(ROOT, "ps1_game")
        cues = sorted(x for x in os.listdir(d) if x.lower().endswith(".cue"))
        if len(cues) != 1:
            die("expected exactly one .cue in ps1_game")
        cue = os.path.join(d, cues[0])
    t0 = time.time()
    try:
        files = load_disc(os.path.abspath(cue), a.all_disc)
    except DiscError as e:
        die(str(e))
    print("disc files loaded: %d, %d bytes" % (len(files), sum(map(len, files.values()))))
    names, idx, istat = build_index(files, a.window, a.stride)
    print("index: %s" % istat)
    print("  detects NON-TRIVIAL runs >= %d bytes only; %d of %d disc bytes (%.2f%%) lie in no "
          "indexed window (trivial-skipped %d windows = %.2f%%, dropped common keys %d / %d windows = "
          "%.2f%%), so a run lying wholly in such bytes could be missed."
          % (a.window + a.stride - 1, istat["uncovered_disc_bytes"], istat["disc_bytes"],
             istat["uncovered_disc_pct"], istat["trivial_skipped"], istat["trivial_skipped_pct"],
             istat["dropped_common_keys"], istat["dropped_windows"], istat["dropped_windows_pct"]))

    z = extract_zip(a.zip, a.extract_dir)
    exe_member = [i for i in z.infolist() if i.filename.endswith("/MythologyKombat.exe")
                  or i.filename == "MythologyKombat.exe"]
    if len(exe_member) != 1:
        die("MythologyKombat.exe not found exactly once in zip")
    exe_path = os.path.join(a.extract_dir, *exe_member[0].filename.split("/"))
    with open(exe_path, "rb") as fh:
        exe = fh.read()
    print("exe: %s  %d bytes  sha256 %s" % (exe_member[0].filename, len(exe),
                                            hashlib.sha256(exe).hexdigest()))
    secs = parse_pe(exe)
    print("PE sections: " + ", ".join("%s raw=0x%x+0x%x" % (s["name"], s["raw_off"], s["raw_size"])
                                      for s in secs))

    t1 = time.time()
    runs = scan(exe, names, files, idx, a.window, a.minrun)
    print("exe scan: %.1fs, %d runs >= %d bytes" % (time.time() - t1, len(runs), a.minrun))
    summ = summarize(runs, secs)
    all_iv = [(r[1], r[1] + r[3]) for r in runs]
    exe_union = union_len(all_iv)

    print("\n== MythologyKombat.exe vs disc files (runs >= %d bytes, <=50%% zero) ==" % a.minrun)
    print("%-34s %6s %12s %10s  %s" % ("disc file", "runs", "bytes_matched", "longest", "by section"))
    for f, s in summ.items():
        print("%-34s %6d %12d %10d  %s" % (f, s["runs"], s["exe_bytes_matched_union"],
                                           s["longest_run"], s["by_section"]))
    if not summ:
        print("(no non-trivial matches found)")
    print("exe bytes covered by any disc run (union over files): %d (%.4f%% of exe)"
          % (exe_union, 100.0 * exe_union / len(exe)))
    for f, s in summ.items():
        for r in s["exe_regions"][:3]:
            print("  region %s: exe file off 0x%x..0x%x section %s" % (f, r[0], r[1], r[2]))

    # strings
    dstr = disc_strings({n: files[n] for n in files
                         if n.upper() == "/SLUS_004.76" or n.upper().startswith("/OVERLAYS/")})
    found, nruns = string_check(exe, secs, dstr)
    bysec = {}
    for s, src, fo, sn in found:
        bysec[sn] = bysec.get(sn, 0) + 1
    print("\n== strings (>=8 printable ASCII, >=5 letters) from disc exe + overlays ==")
    print("distinct disc strings: %d; exe printable runs: %d; disc strings found inside exe: %d; by section %s"
          % (len(dstr), nruns, len(found), dict(sorted(bysec.items()))))
    for s, src, fo, sn in sorted(found, key=lambda x: -len(x[0]))[:15]:
        print("  len %-4d %-10s off 0x%x  %r  in %s" % (len(s), sn, fo, s[:70].decode("ascii"), src[:2]))

    # other members
    others = {}
    if not a.skip_other_members:
        print("\n== other zip members vs disc data ==")
        for i in z.infolist():
            if i.is_dir() or i is exe_member[0] or i.file_size < a.window:
                continue
            p = os.path.join(a.extract_dir, *i.filename.split("/"))
            with open(p, "rb") as fh:
                d = fh.read()
            r = scan(d, names, files, idx, a.window, a.minrun)
            rs = summarize(r, parse_pe(d) if d[:2] == b"MZ" else None)
            if r:
                others[i.filename] = rs
                print("MATCH %s: %s" % (i.filename, {k: (v["exe_bytes_matched_union"], v["longest_run"])
                                                    for k, v in rs.items()}))
        print("members scanned: %d; members with matches: %d" % (
            sum(1 for i in z.infolist() if not i.is_dir() and i.file_size >= a.window), len(others)))

    # conclusion
    print("\n== conclusion ==")
    if exe_union == 0:
        print("exe: no non-trivial exact byte run >= %d bytes (<=50%% zero) found shared with the %d "
              "scanned disc files (blind spot: %.2f%% of disc bytes uncovered by the index)."
              % (a.minrun, len(files), istat["uncovered_disc_pct"]))
    else:
        sec_tot = {}
        for s in summ.values():
            for k, v in s["by_section"].items():
                sec_tot[k] = sec_tot.get(k, 0) + v
        print("exe: %d bytes (%.1f KB) lie in exact runs >= %d bytes shared with disc files; "
              "per-file sums by section: %s" % (exe_union, exe_union / 1024.0, a.minrun, dict(sorted(sec_tot.items()))))
    print("disc strings inside exe: %d of %d" % (len(found), len(dstr)))
    print("other zip members with matches: %d" % len(others))

    res = {"params": {"window": a.window, "stride": a.stride, "minrun": a.minrun,
                      "all_disc": a.all_disc},
           "disc_files": {n: len(files[n]) for n in sorted(files)}, "index": istat,
           "exe": {"size": len(exe), "sha256": hashlib.sha256(exe).hexdigest(), "sections": secs},
           "exe_matches": summ, "exe_union_bytes": exe_union,
           "strings": {"disc_distinct": len(dstr), "found": len(found), "by_section": bysec,
                       "longest": [[s.decode("ascii"), src, fo, sn] for s, src, fo, sn in
                                   sorted(found, key=lambda x: -len(x[0]))[:50]]},
           "other_members": others}
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s (%.0fs total)" % (a.out, time.time() - t0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
