#!/usr/bin/env python3
"""LBA / CdlLOC to disc-file lookup (T2.9).

Usage (repo root):
  <RETRO_TOOLS_DIR>\\python\\python.exe -I tools\\lba_lookup.py [--json] [--bcd] ARG [ARG ...]

ARG is one of:
  * an LBA, decimal or 0x hex:            153072   0x25590
  * a CdlLOC as mm:ss:ff decimal text:     34:01:72
    (with --bcd the three fields are raw BCD bytes, i.e. hex digits with an
     optional 0x prefix, as stored in the game's CD tables: 0x03:0x21:0x17 or
     03:21:17; each byte is BCD-decoded, invalid nibbles are rejected)
CdlLOC -> LBA = (mm*60 + ss)*75 + ff - 150.

Reads only work/disc_files.json (written by tools/disc_list.py) and, if
present, work/disc_classes.json for the optional format tag. Stdlib only.
Exit codes: 0 ok, 2 usage error / bad input / missing data. Out-of-range or
unmapped LBAs are valid answers (exit 0), reported in the result.

Offsets: sector_offset is relative to the file's first sector. byte_offset is
sector_offset * 2048 (ISO size basis). For XA/STR files (Form 2 sectors,
2324 data bytes, interleaved with Form 1) this is a sector-granular index into
the extent, not a byte position in the extracted data stream.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES_JSON = os.path.join(ROOT, "work", "disc_files.json")
CLASSES_JSON = os.path.join(ROOT, "work", "disc_classes.json")
SECTOR = 2048


class UsageError(Exception):
    pass


def usage_exit(msg):
    sys.stderr.write("lba_lookup: %s\n" % msg)
    sys.stderr.write("usage: lba_lookup.py [--json] [--bcd] LBA|0xLBA|mm:ss:ff ...\n")
    sys.exit(2)


def parse_bcd_field(s):
    t = s.lower()
    if t.startswith("0x"):
        t = t[2:]
    if not t or len(t) > 2 or any(c not in "0123456789abcdef" for c in t):
        raise UsageError("bad BCD field %r" % s)
    v = int(t, 16)
    hi, lo = v >> 4, v & 15
    if hi > 9 or lo > 9:
        raise UsageError("invalid BCD byte %r" % s)
    return hi * 10 + lo


def parse_arg(arg, bcd):
    """Return (lba, kind, extra dict)."""
    if ":" in arg:
        parts = arg.split(":")
        if len(parts) != 3:
            raise UsageError("CdlLOC must be mm:ss:ff, got %r" % arg)
        if bcd:
            mm, ss, ff = (parse_bcd_field(p) for p in parts)
        else:
            if not all(p.isdigit() and len(p) <= 3 for p in parts):
                raise UsageError("bad CdlLOC %r" % arg)
            mm, ss, ff = (int(p, 10) for p in parts)
        if ss >= 60 or ff >= 75:
            raise UsageError("CdlLOC field out of range (ss<60, ff<75): %r" % arg)
        return (mm * 60 + ss) * 75 + ff - 150, "cdlloc", {"mm": mm, "ss": ss, "ff": ff}
    t = arg.strip()
    try:
        if t.lower().startswith("0x"):
            v = int(t, 16)
        elif t.isdigit() or (t[:1] == "-" and t[1:].isdigit()):
            v = int(t, 10)
        else:
            raise ValueError
    except ValueError:
        raise UsageError("not an LBA or CdlLOC: %r" % arg)
    return v, "lba", {}


def load():
    if not os.path.isfile(FILES_JSON):
        usage_exit("work/disc_files.json is missing; generate it with: "
                   "python -I tools\\disc_list.py")
    with open(FILES_JSON, "r", encoding="utf-8") as f:
        d = json.load(f)
    tags = {}
    if os.path.isfile(CLASSES_JSON):
        try:
            with open(CLASSES_JSON, "r", encoding="utf-8") as f:
                for e in json.load(f).get("files", []):
                    tags[e["path"]] = {"tag": e.get("tag"),
                                       "secondary_tags": e.get("secondary_tags", [])}
        except (ValueError, KeyError, OSError):
            tags = {}
    return d, tags


def mmssff(lba):
    n = lba + 150
    return "%02d:%02d:%02d" % (n // 4500, (n // 75) % 60, n % 75)


def lookup(lba, d, tags):
    r = {"lba": lba, "cdlloc": mmssff(lba) if lba >= -150 else None}
    total = d["tracks"][0]["sectors"]
    if lba < 0 or lba >= total:
        r.update(kind="out_of_range", status="out of range",
                 detail="track 1 has LBAs 0..%d" % (total - 1))
        return r
    for f in d["files"]:
        if f["lba"] <= lba <= f["end_lba"]:
            off = lba - f["lba"]
            r.update(kind="file", status="file", path=f["path"],
                     file_lba=f["lba"], file_end_lba=f["end_lba"],
                     file_sectors=f["sectors"], file_size_bytes=f["size_bytes"],
                     sector_offset=off, byte_offset=off * SECTOR,
                     xa_flagged=f["xa_flagged"])
            if f["xa_flagged"]:
                r["note"] = ("XA/STR file: Form 1 and Form 2 (2324-byte) sectors are "
                             "interleaved; byte_offset is sector_offset*2048 (ISO size basis)")
            if f["path"] in tags:
                r["tag"] = tags[f["path"]]["tag"]
                r["secondary_tags"] = tags[f["path"]]["secondary_tags"]
            return r
    for dr in d["directories"]:
        if dr["lba"] <= lba < dr["lba"] + dr["sectors"]:
            r.update(kind="directory", status="directory extent", path=dr["path"],
                     extent_lba=dr["lba"], extent_sectors=dr["sectors"],
                     sector_offset=lba - dr["lba"])
            return r
    for s in d["filesystem_structures"]:
        if s["lba"] <= lba < s["lba"] + s["sectors"]:
            r.update(kind="structure", status="filesystem structure",
                     what=s["what"], extent_lba=s["lba"], extent_sectors=s["sectors"],
                     sector_offset=lba - s["lba"])
            return r
    for g in d["gaps"]:
        if g["start_lba"] <= lba <= g["end_lba"]:
            r.update(kind="gap", status="no file (gap)", gap_start_lba=g["start_lba"],
                     gap_end_lba=g["end_lba"], gap_sectors=g["sectors"])
            return r
    r.update(kind="unmapped", status="no file (unmapped)",
             detail="not in any file, directory, structure or recorded gap")
    return r


def render(r, arg):
    if r["lba"] >= 0:
        head = "%s -> LBA %d (0x%X)" % (arg, r["lba"], r["lba"])
    else:
        head = "%s -> LBA %d" % (arg, r["lba"])
    if r.get("cdlloc"):
        head += " CdlLOC %s" % r["cdlloc"]
    k = r["kind"]
    if k == "file":
        s = "%s: %s sector +%d (byte +%d) of %d sectors, extent %d..%d" % (
            head, r["path"], r["sector_offset"], r["byte_offset"],
            r["file_sectors"], r["file_lba"], r["file_end_lba"])
        if "tag" in r:
            s += "; tag: %s" % r["tag"]
        if "note" in r:
            s += "\n    note: " + r["note"]
        return s
    if k == "directory":
        return "%s: directory extent of %s (sector +%d of %d)" % (
            head, r["path"], r["sector_offset"], r["extent_sectors"])
    if k == "structure":
        return "%s: filesystem structure %s (sector +%d of %d)" % (
            head, r["what"], r["sector_offset"], r["extent_sectors"])
    if k == "gap":
        return "%s: no file (gap %d..%d, %d sectors)" % (
            head, r["gap_start_lba"], r["gap_end_lba"], r["gap_sectors"])
    if k == "out_of_range":
        return "%s: out of range (%s)" % (head, r["detail"])
    return "%s: no file (unmapped)" % head


def main(argv):
    as_json = bcd = False
    args = []
    for a in argv:
        if a == "--json":
            as_json = True
        elif a == "--bcd":
            bcd = True
        elif a in ("-h", "--help"):
            sys.stdout.write(__doc__)
            return 0
        elif a.startswith("-") and not a[1:].isdigit():
            usage_exit("unknown option %s" % a)
        else:
            args.append(a)
    if not args:
        usage_exit("no LBA or CdlLOC given")
    parsed = []
    try:
        for a in args:
            parsed.append((a,) + parse_arg(a, bcd))
    except UsageError as e:
        usage_exit(str(e))
    d, tags = load()
    out = []
    for a, lba, kind, extra in parsed:
        r = lookup(lba, d, tags)
        r["input"] = a
        r["input_kind"] = kind
        r.update({"cdlloc_" + k: v for k, v in extra.items()})
        out.append((a, r))
    if as_json:
        sys.stdout.write(json.dumps([r for _, r in out], indent=2, sort_keys=True) + "\n")
    else:
        for a, r in out:
            sys.stdout.write(render(r, a) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
