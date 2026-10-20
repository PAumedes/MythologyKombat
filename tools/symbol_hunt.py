#!/usr/bin/env python3
"""Hunt for leftover debug symbols on the disc (T1.2).

Scans the user data of EVERY sector of track 1 (Form 1: 2048 bytes, Form 2:
2324 bytes, chosen per sector from the CD-XA subheader) for:
  - Psy-Q .SYM files ('MND' magic) and SYM-like name tables,
  - linker .MAP text,
  - source paths / toolchain strings,
  - PsyQ library version / copyright / date strings,
  - function-name-like identifiers (aggregated).

Pass 1 scans region by region (each file extent, each filesystem structure,
each gap between files) so every hit maps to (region, offset, LBA).
Pass 2 scans the whole track once as a single stream and cross-checks that
the signature hits agree with pass 1 (differences can only occur at region
boundaries).

Writes work/symbol_hunt.txt. Deterministic: no timestamps, no absolute paths.
Standard library only. Read-only on the disc image.

Usage:
  python -I tools/symbol_hunt.py [--cue PATH] [--out PATH]
  python -I tools/symbol_hunt.py --selftest
"""
import argparse
import bisect
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from disc_identify import DiscError, MODES, SYNC  # noqa: E402
import disc_list  # noqa: E402

RAW = 2352
CTX = 32
LOWER = bytes((c + 32) if 65 <= c <= 90 else c for c in range(256))

# ---------------------------------------------------------------- patterns
# All text patterns run on a lower-cased copy of the buffer (bytes.translate is
# fast); offsets are identical so the original-case text is sliced from `buf`.
B = rb"(?<![a-z0-9_])"
E = rb"(?![a-z0-9_])"

TEXT_PATTERNS = [
    # (category, kind, regex)
    ("path", "drive_path", re.compile(rb"(?<![a-z])[a-z]:\\[a-z0-9_.\- $\\]{4,}")),
    ("path", "psx_dir", re.compile(rb"[\\/]psx[\\/]")),
    ("path", "src_dir", re.compile(rb"[\\/]src[\\/]")),
    ("path", "source_filename", re.compile(
        rb"(?<![a-z0-9_\-./\\:$])[a-z0-9_\-./\\:$]{2,64}\.(?:c|h|cpp|obj|lib|sym|map|cpe|asm|mak|bat)(?![a-z0-9_])")),
    ("path", "toolchain", re.compile(
        rb"psyq|sn systems|snsystems|programmers? group|ccpsx|cc1psx|aspsx|dmpsx|psylink|gcc2_compiled|__gnu_compiled|psymake")),
    ("map", "map_header", re.compile(
        rb"address +publics by|start +length +name|publics by (?:name|value)|\.(?:text|data|bss|rdata|sdata|sbss) +[0-9a-f]{8} +[0-9a-f]{8}")),
    ("version", "run_time_library", re.compile(rb"ps-x run-time library")),
    ("version", "library_release", re.compile(rb"library release|library version|runtime library|run-time library")),
    ("version", "psyq_lib_name", re.compile(
        B + rb"lib(?:gpu|spu|cd|gte|gs|gpu|api|etc|pad|snd|ds|press|math|sn|card|mcrd|tap|gun|com|hmd|c2|c|sio|siocook|cd|cd2)" + E)),
    ("version", "rcs_keyword", re.compile(rb"\$(?:id|header|revision|log|date|author|source)[:$ ]|revision +\d")),
    ("version", "copyright", re.compile(rb"copyright|\(c\) *(?:19)?9\d")),
    ("version", "sony_text", re.compile(rb"sony computer|licensed by|playstation")),
    ("version", "company", re.compile(rb"midway|acclaim|eurocom|williams|mortal kombat|netherrealm|boon")),
    ("version", "date_text", re.compile(
        rb"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.? +\d{1,2},? +(?:19|20)\d\d")),
    ("version", "date_numeric", re.compile(
        B + rb"(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12]\d|3[01])/(?:19)?9\d" + E)),
    ("version", "date_numeric_dash", re.compile(B + rb"199\d[-/.](?:0[1-9]|1[0-2])[-/.](?:0[1-9]|[12]\d|3[01])" + E)),
    ("api", "psyq_api_name", re.compile(
        B + rb"(?:resetgraph|setdefdrawenv|setdefdispenv|putdrawenv|putdispenv|drawsync|vsync|drawotag|clearotag|"
        rb"initgeom|cdinit|cdread|cdsync|cdcontrol|spuinit|spusetvoice|padinit|initpad|startpad|memcardinit|"
        rb"setvideomode|loadimage|storeimage|fntload|fntprint|gsinitgraph|initheap|entercriticalsection|"
        rb"decdctin|stsetring|openevent|testevent|exec|loadexec|flushcache|bios_|_96_init)" + E)),
]
MAP_LINE = re.compile(rb"(?m)^[ \t]*[0-9a-f]{8}[ \t]+[a-z_.$@][a-z0-9_.$@]{2,63}[ \t]*\r?$")
MND = re.compile(rb"MND")
SYM_CAND = re.compile(rb"\x80[\x00-\xff][\x03-\x40][A-Za-z_.$@]")
IDENT = re.compile(rb"(?<![\x21-\x7e])[A-Za-z_][A-Za-z0-9_]{5,63}(?![\x21-\x7e])")
UNDERSCORE = re.compile(rb"[A-Za-z0-9]_[A-Za-z0-9]")
CAMEL = re.compile(rb"[a-z0-9][A-Z][a-z]")
INIT = re.compile(rb"(?:Init|Set|Get|Load|Draw|Update|Reset|Start|Stop|Play|Free|Alloc|Create|Destroy)[A-Z][A-Za-z0-9]+")


def esc(b, limit=None):
    if limit is not None:
        b = b[:limit]
    return "".join(chr(c) if 32 <= c < 127 else "." for c in b)


def sym_chains(buf, hits):
    """Find runs of >=4 back-to-back SYM-style entries (u32 addr 0x80xxxxxx LE,
    u8 tag, u8 len, name[len]). Appends ('sym','sym_chain',pos,len,note)."""
    skip_to = 0
    for m in SYM_CAND.finditer(buf):
        e = m.start() - 3
        if e < skip_to or e < 0:
            continue
        cur, n = e, 0
        while cur + 7 <= len(buf):
            if buf[cur + 3] != 0x80:
                break
            ln = buf[cur + 5]
            name = buf[cur + 6:cur + 6 + ln]
            if not (3 <= ln <= 64) or len(name) != ln or not re.fullmatch(rb"[A-Za-z_.$@][\x21-\x7e]*", name):
                break
            n += 1
            cur += 6 + ln
        if n >= 4:
            hits.append(("sym", "sym_chain", e, cur - e, "%d consecutive entries" % n))
            skip_to = cur


def scan_signatures(buf):
    """Return list of (cat, kind, pos, length, note). No position resolution."""
    hits = []
    low = buf.translate(LOWER)
    for cat, kind, rx in TEXT_PATTERNS:
        for m in rx.finditer(low):
            hits.append((cat, kind, m.start(), m.end() - m.start(), ""))
    # map lines: group consecutive ones
    prev_end, start, count = -1, 0, 0
    lines = []
    for m in MAP_LINE.finditer(low):
        lines.append((m.start(), m.end()))
    i = 0
    while i < len(lines):
        j = i
        while j + 1 < len(lines) and lines[j + 1][0] - lines[j][1] <= 2:
            j += 1
        n = j - i + 1
        if n >= 3:
            hits.append(("map", "map_line_block", lines[i][0], lines[j][1] - lines[i][0], "%d consecutive lines" % n))
        else:
            hits.append(("map", "map_line_single", lines[i][0], lines[i][1] - lines[i][0], ""))
        i = j + 1
    for m in MND.finditer(buf):
        hits.append(("sym", "mnd_raw", m.start(), 3, ""))
    sym_chains(buf, hits)
    return hits


def ident_tokens(buf):
    """Yield function-name-like identifier tokens (bytes)."""
    for m in IDENT.finditer(buf):
        t = m.group()
        letters = sum(1 for c in t if 65 <= c <= 90 or 97 <= c <= 122)
        if letters * 10 < len(t) * 7:
            continue
        if UNDERSCORE.search(t) or CAMEL.search(t) or INIT.fullmatch(t):
            if t.upper() == t and b"_" not in t:
                continue
            yield m.start(), t


# ---------------------------------------------------------------- disc access
class Reader:
    def __init__(self, path):
        self.f = open(path, "rb")
        self.bad_sync = 0

    def sectors(self, lba, count):
        """Return (payloads list, lbas list, form2 count). Bad-sync sectors skipped."""
        self.f.seek(lba * RAW)
        raw = self.f.read(count * RAW)
        if len(raw) != count * RAW:
            raise DiscError("short read at LBA %d" % lba)
        pay, lbas, f2 = [], [], 0
        for i in range(count):
            b = i * RAW
            if raw[b:b + 12] != SYNC:
                self.bad_sync += 1
                continue
            if raw[b + 18] & 0x20:
                pay.append(raw[b + 24:b + 24 + 2324])
                f2 += 1
            else:
                pay.append(raw[b + 24:b + 24 + 2048])
            lbas.append(lba + i)
        return pay, lbas, f2


class Mapper:
    """Maps a position in a concatenated payload buffer to (lba, offset in sector)."""

    def __init__(self, payloads, lbas):
        self.lbas = lbas
        self.starts = []
        t = 0
        for p in payloads:
            self.starts.append(t)
            t += len(p)
        self.total = t

    def at(self, pos):
        i = bisect.bisect_right(self.starts, pos) - 1
        return self.lbas[i], pos - self.starts[i]

    def is_sector_start(self, pos):
        i = bisect.bisect_right(self.starts, pos) - 1
        return self.starts[i] == pos


def context(buf, pos, ln):
    a = max(0, pos - CTX)
    z = min(len(buf), pos + ln + CTX)
    return esc(buf[a:pos]) + "[" + esc(buf[pos:pos + ln], 120) + "]" + esc(buf[pos + ln:z])


def classify_mnd(buf, pos, mp, region_start_pos):
    """Return None for noise, else (kind, note)."""
    ver = buf[pos + 3] if pos + 3 < len(buf) else -1
    at_region = pos == region_start_pos
    at_sector = mp.is_sector_start(pos)
    hdr = buf[pos:pos + 8]
    if ver == 1 and (at_region or at_sector):
        return ("mnd_strong", "MND+0x01 at %s start; header=%s" % ("file/region" if at_region else "sector", hdr.hex()))
    if ver in (1, 2):
        return ("mnd_weak", "MND+0x%02x mid-data; header=%s" % (ver, hdr.hex()))
    return ("mnd_noise", "")


# ---------------------------------------------------------------- scanning
class Results:
    def __init__(self):
        self.hits = []          # dicts
        self.counts = collections.Counter()        # (cat, kind) -> n
        self.idents = collections.Counter()        # token -> n
        self.ident_by_region = collections.Counter()
        self.ident_by_class = collections.Counter()
        self.idents_nm = collections.Counter()     # identifiers outside STR (media) regions
        self.keys = {}          # pass key -> True

    def add(self, region, cls, hit, buf, mp, region_start_pos):
        cat, kind, pos, ln, note = hit
        if kind == "mnd_raw":
            r = classify_mnd(buf, pos, mp, region_start_pos)
            kind, note = r
            if kind == "mnd_noise":
                self.counts[(cat, kind)] += 1
                return
        lba, off = mp.at(pos)
        self.counts[(cat, kind)] += 1
        self.hits.append({"cat": cat, "kind": kind, "region": region, "cls": cls, "lba": lba, "off_sector": off,
                          "stream_off": pos, "len": ln, "note": note, "ctx": context(buf, pos, ln),
                          "text": esc(buf[pos:pos + ln], 100)})


def scan_region(res, region, cls, payloads, lbas, with_idents=True):
    if not payloads:
        return
    buf = b"".join(payloads)
    mp = Mapper(payloads, lbas)
    for h in scan_signatures(buf):
        res.add(region, cls, h, buf, mp, 0)
    if with_idents:
        n = 0
        for pos, t in ident_tokens(buf):
            res.idents[t] += 1
            if cls != "file:STR":
                res.idents_nm[t] += 1
            n += 1
        res.ident_by_region[region] += n
        res.ident_by_class[cls] += n


def run_scan(cue):
    d = disc_list.build(cue)
    cue_dir = os.path.dirname(cue)
    binpath = os.path.join(cue_dir, d["tracks"][0]["file"])
    nsec = d["tracks"][0]["sectors"]
    if d["tracks"][0]["mode"] != "MODE2/2352":
        raise DiscError("expected MODE2/2352 track")
    regions = []   # (name, class, lba, sectors)
    for s in d["filesystem_structures"]:
        regions.append(("struct:" + s["what"], "fs_structure", s["lba"], s["sectors"]))
    for x in d["directories"]:
        regions.append(("dir:" + x["path"], "fs_structure", x["lba"], x["sectors"]))
    for f in d["files"]:
        if f["sectors"]:
            ext = f["name"].rsplit(".", 1)[-1].upper() if "." in f["name"] else ""
            regions.append(("file:" + f["path"], "file", f["lba"], f["sectors"]))
    gi = 0
    for g in d["gaps"]:
        regions.append(("gap:%d-%d" % (g["start_lba"], g["end_lba"]), "gap", g["start_lba"], g["sectors"]))
    regions.sort(key=lambda r: (r[2], r[0]))
    # coverage check: regions must tile track 1 exactly (identical extents may repeat)
    covered = bytearray(nsec)
    for _, _, l, c in regions:
        for i in range(l, l + c):
            covered[i] = 1
    uncovered = covered.count(0)
    file_ext = {f["path"]: f for f in d["files"]}

    rd = Reader(binpath)
    res = Results()
    cov = collections.OrderedDict()
    for cls in ("file", "fs_structure", "gap"):
        cov[cls] = {"regions": 0, "sectors": 0, "bytes": 0, "form2_sectors": 0}
    scanned_lbas = set()
    per_file_media = {}
    for name, cls, lba, cnt in regions:
        pay, lbas, f2 = rd.sectors(lba, cnt)
        c = cov[cls]
        c["regions"] += 1
        c["sectors"] += len(pay)
        c["bytes"] += sum(len(p) for p in pay)
        c["form2_sectors"] += f2
        scanned_lbas.update(lbas)
        icls = cls
        if cls == "file":
            f = file_ext[name[5:]]
            ext = f["name"].rsplit(".", 1)[-1].upper()
            icls = "file:" + ext
        scan_region(res, name, icls, pay, lbas)
    total_scanned = len(scanned_lbas)

    # ---- pass 2: whole-track stream cross-check (signatures only)
    res2 = Results()
    BLOCK, LOOK = 8192, 8
    stream_bytes = 0
    lba = 0
    while lba < nsec:
        cnt = min(BLOCK, nsec - lba)
        pay, lbas, _ = rd.sectors(lba, cnt)
        stream_bytes += sum(len(p) for p in pay)
        lcnt = min(LOOK, nsec - lba - cnt)
        lpay, llbas = [], []
        if lcnt:
            lpay, llbas, _ = rd.sectors(lba + cnt, lcnt)
        # reads above double-count bad_sync only if any exist; handled by reporting once from pass 1
        allp = pay + lpay
        mp = Mapper(allp, lbas + llbas)
        buf = b"".join(allp)
        limit = sum(len(p) for p in pay)
        for h in scan_signatures(buf):
            if h[2] < limit:
                res2.add("stream", "stream", h, buf, mp, -1)
        lba += cnt
    rd.f.close()
    return d, res, res2, cov, nsec, total_scanned, uncovered, stream_bytes, rd.bad_sync


# ---------------------------------------------------------------- report
STRONG_KINDS = {("sym", "mnd_strong"), ("sym", "sym_chain"), ("map", "map_line_block"), ("map", "map_header")}
DETAIL_CAP = 40
NOTABLE_KINDS = ["run_time_library", "library_release", "psyq_lib_name", "rcs_keyword", "toolchain", "copyright",
                 "date_text", "date_numeric", "date_numeric_dash", "drive_path", "psx_dir", "src_dir"]


def key_of(h):
    return (h["cat"], h["kind"], h["lba"], h["off_sector"])


def fmt_hit(h):
    return "  LBA %d +0x%03x  %s  stream_off=0x%x  %s\n      ctx: %s" % (
        h["lba"], h["off_sector"], h["region"], h["stream_off"],
        (h["kind"] + (" (" + h["note"] + ")" if h["note"] else "")), h["ctx"])


def ident_report(res, out):
    uniq = len(res.idents)
    tot = sum(res.idents.values())
    out.append("Function-name-like identifiers (ASCII token, >=6 chars, bounded by non-graphic bytes,")
    out.append("  >=70% letters, containing an interior '_' or a lower/Upper camel boundary or a verb+Capital prefix):")
    out.append("  total occurrences: %d   unique tokens: %d" % (tot, uniq))
    out.append("  occurrences by region class:")
    for k, v in sorted(res.ident_by_class.items(), key=lambda kv: (-kv[1], kv[0])):
        out.append("    %-16s %d" % (k, v))
    out.append("  top 15 regions by occurrence count:")
    for k, v in sorted(res.ident_by_region.items(), key=lambda kv: (-kv[1], kv[0]))[:15]:
        out.append("    %-40s %d" % (k, v))
    # samples: tokens seen >=2 times, ranked by (count, length)
    ids = res.idents_nm
    out.append("  Lists below EXCLUDE file:STR regions (compressed video, tokens there are chance matches);")
    out.append("  non-STR occurrences: %d, unique: %d" % (sum(ids.values()), len(ids)))
    rep = [(t, n) for t, n in ids.items() if n >= 2 and len(t) >= 7]
    rep.sort(key=lambda tn: (-tn[1], -len(tn[0]), tn[0]))
    out.append("  top 40 non-STR tokens occurring >=2 times (len>=7), by count:")
    for t, n in rep[:40]:
        out.append("    %6d  %s" % (n, esc(t)))
    under = [(t, n) for t, n in ids.items() if b"_" in t and len(t) >= 8]
    under.sort(key=lambda tn: (-tn[1], -len(tn[0]), tn[0]))
    out.append("  top 30 non-STR tokens containing '_' (len>=8), by count:")
    for t, n in under[:30]:
        out.append("    %6d  %s" % (n, esc(t)))
    initl = [(t, n) for t, n in ids.items() if INIT.fullmatch(t)]
    initl.sort(key=lambda tn: (-tn[1], tn[0]))
    out.append("  verb+Capital pattern (Init*/Set*/Get*/Load*/Draw*/...): %d unique, top 25:" % len(initl))
    for t, n in initl[:25]:
        out.append("    %6d  %s" % (n, esc(t)))


def build_report(d, res, res2, cov, nsec, total_scanned, uncovered, stream_bytes, bad_sync):
    out = []
    A = out.append
    A("SYMBOL HUNT REPORT (T1.2)")
    A("=" * 72)
    A("Disc: %s   volume id: %s" % (d["cue"], d["volume"]["volume_id"] or "(blank)"))
    A("Scanned data: Form 1 sectors 2048 bytes, Form 2 sectors 2324 bytes (per CD-XA subheader).")
    A("Not scanned: sync/header/subheader bytes, EDC/ECC (not user data).")
    A("Offsets: 'LBA n +0xNNN' = byte offset inside that sector's user data; 'stream_off' = byte")
    A("  offset in the region's concatenated user data (for a Form 1 file this is the file offset).")
    A("Context: +-%d bytes, non-printable bytes shown as '.', hit text in [brackets]." % CTX)
    A("")
    A("1. COVERAGE")
    A("-" * 72)
    A("Track 1: %d sectors (%d raw bytes)" % (nsec, nsec * RAW))
    tot_b = tot_s = 0
    for cls, label in (("file", "files (file extents)"), ("fs_structure", "filesystem structures (system area, volume descriptors, path tables, directories)"),
                       ("gap", "gaps between files")):
        c = cov[cls]
        A("  %-12s regions=%-4d sectors=%-7d user-data bytes scanned=%-10d (Form 2 sectors: %d)" %
          (cls, c["regions"], c["sectors"], c["bytes"], c["form2_sectors"]))
        A("               %s" % label)
        tot_b += c["bytes"]
        tot_s += c["sectors"]
    A("  TOTAL pass 1: regions sectors=%d, bytes=%d; distinct LBAs scanned=%d of %d; LBAs not covered by any region=%d" %
      (tot_s, tot_b, total_scanned, nsec, uncovered))
    A("  (Regions do not overlap: TOTAL sectors equals track sectors only if no sector is listed twice.)")
    A("  Sectors skipped for bad sync: %d" % bad_sync)
    A("  Pass 2 (whole track as one stream): %d bytes of user data scanned." % stream_bytes)
    ok = total_scanned == nsec and uncovered == 0 and bad_sync == 0
    A("  Coverage verdict: %s" % ("COMPLETE - every sector of track 1 scanned" if ok else "INCOMPLETE - see numbers above"))
    A("")
    A("2. HIT SUMMARY (pass 1, per category/kind)")
    A("-" * 72)
    for (cat, kind), n in sorted(res.counts.items()):
        A("  %-8s %-20s %d%s" % (cat, kind, n, "   <- strong indicator" if (cat, kind) in STRONG_KINDS else ""))
    strong = sum(n for k, n in res.counts.items() if k in STRONG_KINDS)
    A("")
    A("  Strong indicators of real debug symbols (MND at file/sector start, SYM entry chains, map blocks/headers): %d" % strong)
    A("")
    A("3. NOTABLE HITS (library/version/toolchain/path strings; offsets for T1.6)")
    A("-" * 72)
    by_kind = collections.defaultdict(list)
    str_counts = collections.Counter()
    for h in res.hits:
        if h["cls"] == "file:STR" and (h["cat"], h["kind"]) not in STRONG_KINDS:
            str_counts[h["kind"]] += 1      # chance matches in compressed video: counted, not listed
            continue
        by_kind[h["kind"]].append(h)
    A("  Hits inside file:STR regions (compressed video / interleaved audio) are counted but not listed;")
    A("  they are chance matches in random-looking data. Counts: " +
      (", ".join("%s=%d" % (k, v) for k, v in sorted(str_counts.items())) or "none"))
    for kind in NOTABLE_KINDS:
        hs = sorted(by_kind.get(kind, []), key=lambda h: (h["lba"], h["off_sector"]))
        if not hs:
            A("[%s] none" % kind)
            continue
        A("[%s] %d hit(s)" % (kind, len(hs)))
        for h in hs[:DETAIL_CAP]:
            A(fmt_hit(h))
        if len(hs) > DETAIL_CAP:
            per = collections.Counter(h["region"] for h in hs[DETAIL_CAP:])
            A("  ... %d more; remaining by region: %s" % (len(hs) - DETAIL_CAP,
              ", ".join("%s=%d" % (k, v) for k, v in sorted(per.items(), key=lambda kv: (-kv[1], kv[0]))[:10])))
    A("")
    A("4. SYM / MAP / SOURCE-FILENAME DETAIL")
    A("-" * 72)
    for kind in ("mnd_strong", "mnd_weak", "sym_chain", "map_line_block", "map_header", "map_line_single",
                 "source_filename", "psyq_api_name", "sony_text", "company"):
        hs = sorted(by_kind.get(kind, []), key=lambda h: (h["lba"], h["off_sector"]))
        A("[%s] %d hit(s)" % (kind, len(hs)))
        for h in hs[:DETAIL_CAP if kind not in ("map_line_single",) else 10]:
            A(fmt_hit(h))
        if len(hs) > (DETAIL_CAP if kind != "map_line_single" else 10):
            n_left = len(hs) - (DETAIL_CAP if kind != "map_line_single" else 10)
            per = collections.Counter(h["region"] for h in hs)
            A("  ... %d more not shown; all hits by region (top 10): %s" % (
                n_left, ", ".join("%s=%d" % (k, v) for k, v in sorted(per.items(), key=lambda kv: (-kv[1], kv[0]))[:10])))
    A("  (mnd_noise = 'MND' bytes not followed by 0x01/0x02: %d occurrences, counted only)" % res.counts[("sym", "mnd_noise")])
    A("")
    A("5. FUNCTION-NAME-LIKE STRINGS (aggregate)")
    A("-" * 72)
    ident_report(res, out)
    A("")
    A("6. CROSS-CHECK (pass 1 per-region vs pass 2 whole-track stream)")
    A("-" * 72)
    sig_kinds = sorted(set(k for k in list(res.counts) + list(res2.counts) if k[1] not in ("mnd_noise",)))
    A("  %-8s %-20s %8s %8s" % ("cat", "kind", "pass1", "pass2"))
    for k in sig_kinds:
        A("  %-8s %-20s %8d %8d" % (k[0], k[1], res.counts[k], res2.counts[k]))
    k1 = set(key_of(h) for h in res.hits)
    k2 = set(key_of(h) for h in res2.hits)
    only1 = sorted(k1 - k2)
    only2 = sorted(k2 - k1)
    A("  hits only in pass 1: %d   only in pass 2: %d" % (len(only1), len(only2)))
    A("  (differences are expected only where a string or a line spans a region boundary, or where a")
    A("   hit sits at a region start so 'file start' differs from 'sector start')")
    for k in (only1 + only2)[:30]:
        A("    %s %s LBA %d +0x%x  (%s)" % (k[0], k[1], k[2], k[3], "pass1 only" if k in k1 - k2 else "pass2 only"))
    A("")
    A("7. FALSE-POSITIVE ASSESSMENT")
    A("-" * 72)
    A("  - 'MND' is 3 bytes; in %d bytes of data ~%d chance occurrences are expected. Only 'MND'+0x01 at a" % (stream_bytes, stream_bytes // (1 << 24)))
    A("    file/sector start is treated as a plausible SYM header (mnd_strong). Mid-data 'MND'+0x01/0x02 is weak.")
    A("    A real Psy-Q .SYM would also yield a sym_chain (>=4 back-to-back 0x80xxxxxx address + tag + length + name entries).")
    A("  - 204561 of 228788 file sectors are STR (compressed video / XA interleave); short printable runs in them are")
    A("    random-data coincidences. Identifier counts are therefore split by region class above.")
    A("  - source_filename / copyright / date patterns are short and can match by chance in binary data; each hit is shown")
    A("    with context so it can be judged. A hit counts as a symbol hint only if the surrounding text is a coherent string.")
    A("  - map_line_single (one 'hex8 name' line) is not treated as a map; only >=3 consecutive lines (map_line_block) count.")
    A("")
    A("8. CONCLUSION")
    A("-" * 72)
    mnd_s = res.counts[("sym", "mnd_strong")]
    chain = res.counts[("sym", "sym_chain")]
    mapb = res.counts[("map", "map_line_block")] + res.counts[("map", "map_header")]
    A("  Psy-Q .SYM files (MND at file/sector start): %s" % ("%d candidate(s), see section 4" % mnd_s if mnd_s else "none found"))
    A("  SYM-style entry chains: %s" % ("%d candidate(s), see section 4" % chain if chain else "none found"))
    A("  Linker .MAP text: %s" % ("%d candidate(s), see section 4" % mapb if mapb else "none found"))
    pth = res.counts[("path", "drive_path")] + res.counts[("path", "psx_dir")] + res.counts[("path", "src_dir")]
    A("  Source/drive paths (drive letter, \\PSX\\, \\SRC\\): %s" % ("%d hit(s), see sections 3/4" % pth if pth else "none found"))
    A("  Source-style filenames (.c/.h/.obj/...): %d hit(s) (judge by context, section 4)" % res.counts[("path", "source_filename")])
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- selftest
def selftest():
    sym = b"MND\x01\x02\x00\x00\x00"
    for i, nm in enumerate((b"main", b"InitGame", b"Player_Update", b"DrawSprite", b"_start")):
        sym += (0x80010000 + i * 0x40).to_bytes(4, "little") + b"\x01" + bytes([len(nm)]) + nm
    mapt = (b"Address  Publics by Name\r\n"
            b"80010000  main\r\n80010040  InitGame\r\n80010080  Player_Update\r\n")
    path = b"\x00\x00C:\\PSX\\SRC\\MAIN.C\x00"
    func = b"\x00\x00InitPlayerStats\x00"
    ver = b"\x00PS-X Run-time Library Release 4.6\x00"
    noise = bytes((i * 37 + 11) & 0xFF for i in range(2048))
    sectors = [sym.ljust(2048, b"\xaa"), mapt.ljust(2048, b"\x00"), (path + func + ver).ljust(2048, b"\x00"),
               noise]
    mid = b"\x55" * 100 + b"MND\x01\x01" + b"\x55" * 100
    sectors.append(mid.ljust(2048, b"\x55"))
    buf = b"".join(sectors)
    lbas = list(range(len(sectors)))
    mp = Mapper(sectors, lbas)
    res = Results()
    for h in scan_signatures(buf):
        res.add("selftest", "file:BIN", h, buf, mp, 0)
    idents = [t for _, t in ident_tokens(buf)]
    checks = []

    def has(kind, lba=None):
        return any(h["kind"] == kind and (lba is None or h["lba"] == lba) for h in res.hits)
    checks.append(("MND header at file start detected as mnd_strong", has("mnd_strong", 0)))
    checks.append(("SYM entry chain detected", has("sym_chain", 0)))
    checks.append(("map line block detected", has("map_line_block", 1)))
    checks.append(("map header detected", has("map_header", 1)))
    checks.append(("drive path detected", has("drive_path", 2)))
    checks.append(("\\PSX\\ dir detected", has("psx_dir", 2)))
    checks.append(("source filename MAIN.C detected", has("source_filename", 2)))
    checks.append(("function-name string InitPlayerStats detected", b"InitPlayerStats" in idents))
    checks.append(("underscore symbol Player_Update detected", b"Player_Update" in idents))
    checks.append(("run-time library string detected", has("run_time_library", 2)))
    checks.append(("mid-data MND+0x01 is weak, not strong", has("mnd_weak", 4) and not has("mnd_strong", 4)))
    checks.append(("noise sector produced no strong hit", not any(h["lba"] == 3 and (h["cat"], h["kind"]) in STRONG_KINDS for h in res.hits)))
    fails = 0
    for name, ok in checks:
        print("%s  %s" % ("PASS" if ok else "FAIL", name))
        fails += 0 if ok else 1
    print("selftest: %d/%d passed" % (len(checks) - fails, len(checks)))
    return 1 if fails else 0


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--cue")
    ap.add_argument("--out", default=os.path.join(root, "work", "symbol_hunt.txt"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    try:
        cue = a.cue
        if not cue:
            dd = os.path.join(root, "ps1_game")
            cues = sorted(x for x in os.listdir(dd) if x.lower().endswith(".cue")) if os.path.isdir(dd) else []
            if len(cues) != 1:
                raise DiscError("expected exactly one .cue in %s, found %d" % (dd, len(cues)))
            cue = os.path.join(dd, cues[0])
        r = run_scan(os.path.abspath(cue))
        text = build_report(*r)
    except DiscError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    sys.stdout.write(text[:text.index("3. NOTABLE")])
    print("wrote %s (%d bytes)" % (os.path.relpath(a.out, root).replace("\\", "/"), len(text.encode())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
