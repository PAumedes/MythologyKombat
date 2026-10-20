#!/usr/bin/env python3
"""List every file on the disc, with XA/Form 2 classification (T1.1).

Walks the ISO9660 tree of the first data track (raw 2352-byte Mode 2 sectors),
reads the CD-XA subheader of every sector in each file extent, parses the
ISO9660 XA system-use extension of each directory record, and computes the
LBA ranges of track 1 not covered by any file or filesystem structure.

Writes work/disc_files.json. Deterministic: no timestamps, no absolute paths;
files sorted by (LBA, path). Standard library only. Read-only on the disc image.

Usage:
  python -I tools/disc_list.py [--cue PATH] [--out PATH]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from disc_identify import DiscError, MODES, SYNC, parse_cue  # noqa: E402

SECTOR_DATA = 2048
DIR_FLAGS = [(0, "hidden"), (1, "directory"), (2, "associated"), (3, "record"),
             (4, "protection"), (7, "multi_extent")]
# CD-XA attribute word bits (ISO9660 XA system-use extension)
XA_BITS = [(0x0800, "mode2_form1"), (0x1000, "mode2_form2"),
           (0x2000, "interleaved"), (0x4000, "cdda"), (0x8000, "directory")]


class Track:
    """Raw reader for one data track. LBA 0 = INDEX 01 of the track."""

    def __init__(self, path, mode, start_frame, sectors):
        self.f = open(path, "rb")
        self.mode = mode
        self.size, self.off = MODES[mode]
        self.start = start_frame
        self.sectors = sectors
        # offset of the 8-byte subheader copy pair inside a raw sector
        self.sub_off = {"MODE2/2352": 16, "MODE2/2336": 0}.get(mode)

    def read_user(self, lba):
        if not 0 <= lba < self.sectors:
            raise DiscError("LBA %d is outside track 1 (%d sectors)" % (lba, self.sectors))
        self.f.seek((self.start + lba) * self.size)
        raw = self.f.read(self.size)
        if len(raw) != self.size:
            raise DiscError("short read at LBA %d" % lba)
        return raw[self.off:self.off + SECTOR_DATA]

    def read_extent(self, lba, size):
        n = (size + 2047) // 2048
        return b"".join(self.read_user(lba + i) for i in range(n))[:size]

    def sector_stats(self, lba, count, want_ids=True):
        """Classify `count` sectors from `lba` by subheader. None if mode has none."""
        if self.sub_off is None:
            return None
        if count <= 0:
            return finish_stats(empty_stats())
        if lba < 0 or lba + count > self.sectors:
            raise DiscError("extent LBA %d..%d is outside track 1 (%d sectors)"
                            % (lba, lba + count - 1, self.sectors))
        st = empty_stats()
        done = 0
        while done < count:
            n = min(4096, count - done)
            self.f.seek((self.start + lba + done) * self.size)
            buf = self.f.read(n * self.size)
            if len(buf) != n * self.size:
                raise DiscError("short read in extent at LBA %d" % (lba + done))
            for i in range(n):
                base = i * self.size
                if self.mode == "MODE2/2352" and buf[base:base + 12] != SYNC:
                    st["bad_sync"] += 1
                    continue
                h = buf[base + self.sub_off:base + self.sub_off + 8]
                if h[0:4] != h[4:8]:
                    st["subheader_copy_mismatch"] += 1
                fn, ch, sm, ci = h[0], h[1], h[2], h[3]
                st["_sm"][sm] = st["_sm"].get(sm, 0) + 1
                st["_ci"][ci] = st["_ci"].get(ci, 0) + 1
                st["_fn"].add(fn)
                st["_ch"].add(ch)
                st["_fc"].add((fn, ch))
                if sm & 0x20:
                    st["form2_sectors"] += 1
                else:
                    st["form1_sectors"] += 1
                if sm & 0x40:
                    st["realtime_sectors"] += 1
                if sm & 0x08:
                    st["data_sectors"] += 1
                if sm & 0x04:
                    st["audio_sectors"] += 1
                if sm & 0x02:
                    st["video_sectors"] += 1
                if sm & 0x01:
                    st["eof_sectors"] += 1
            done += n
        return finish_stats(st)

    def close(self):
        self.f.close()


def empty_stats():
    return {"sectors": 0, "form1_sectors": 0, "form2_sectors": 0, "realtime_sectors": 0,
            "data_sectors": 0, "audio_sectors": 0, "video_sectors": 0, "eof_sectors": 0,
            "bad_sync": 0, "subheader_copy_mismatch": 0,
            "_sm": {}, "_ci": {}, "_fn": set(), "_ch": set(), "_fc": set()}


def finish_stats(st):
    sm = st.pop("_sm")
    ci = st.pop("_ci")
    fn = st.pop("_fn")
    ch = st.pop("_ch")
    fc = st.pop("_fc")
    st["sectors"] = sum(sm.values()) + st["bad_sync"]
    st["submode_histogram"] = {"0x%02x" % k: sm[k] for k in sorted(sm)}
    st["coding_info_histogram"] = {"0x%02x" % k: ci[k] for k in sorted(ci)}
    st["dominant_submode"] = ("0x%02x" % min(sm, key=lambda k: (-sm[k], k))) if sm else None
    if sm:
        d = min(sm, key=lambda k: (-sm[k], k))
        st["dominant_form"] = 2 if d & 0x20 else 1
    else:
        st["dominant_form"] = None
    st["file_numbers"] = sorted(fn)
    st["channels"] = sorted(ch)
    st["file_channel_pairs"] = [list(p) for p in sorted(fc)]
    return st


def flag_names(b):
    return [n for bit, n in DIR_FLAGS if b & (1 << bit)]


def parse_xa(su):
    """Parse the 14-byte CD-XA system-use block, or None."""
    for off in (0, len(su) - 14):
        if off >= 0 and len(su) >= off + 14 and su[off + 6:off + 8] == b"XA":
            b = su[off:off + 14]
            attr = int.from_bytes(b[4:6], "big")
            return {"group_id": int.from_bytes(b[0:2], "big"),
                    "user_id": int.from_bytes(b[2:4], "big"),
                    "attributes": "0x%04x" % attr,
                    "attribute_flags": [n for bit, n in XA_BITS if attr & bit],
                    "mode2_form1": bool(attr & 0x0800),
                    "mode2_form2": bool(attr & 0x1000),
                    "interleaved": bool(attr & 0x2000),
                    "cdda": bool(attr & 0x4000),
                    "file_number": b[8]}
    return None


def parse_dir_records(data):
    out = []
    pos = 0
    while pos < len(data):
        ln = data[pos]
        if ln == 0:
            pos = (pos // 2048 + 1) * 2048
            continue
        rec = data[pos:pos + ln]
        if len(rec) < 34 or len(rec) < 33 + rec[32]:
            raise DiscError("truncated directory record")
        nlen = rec[32]
        raw = rec[33:33 + nlen]
        if raw == b"\x00":
            name = "."
        elif raw == b"\x01":
            name = ".."
        else:
            name = raw.decode("ascii", "replace")
        su_start = 33 + nlen + (1 if nlen % 2 == 0 else 0)
        su = rec[su_start:ln] if su_start < ln else b""
        out.append({"name": name, "lba": int.from_bytes(rec[2:6], "little"),
                    "size": int.from_bytes(rec[10:14], "little"),
                    "flags": rec[25], "xa": parse_xa(su) if su else None,
                    "system_use_len": len(su)})
        pos += ln
    return out


def walk(trk, root_lba, root_size):
    files, dirs = [], []
    seen = set()

    def visit(path, lba, size):
        if lba in seen:
            return
        seen.add(lba)
        recs = parse_dir_records(trk.read_extent(lba, size))
        selfrec = next((r for r in recs if r["name"] == "."), None)
        dirs.append({"path": path, "lba": lba, "size_bytes": size,
                     "sectors": (size + 2047) // 2048,
                     "xa": selfrec["xa"] if selfrec else None})
        for r in recs:
            if r["name"] in (".", ".."):
                continue
            if r["flags"] & 2:
                visit(path.rstrip("/") + "/" + r["name"], r["lba"], r["size"])
            else:
                files.append((path, r))

    visit("/", root_lba, root_size)
    return files, dirs


def merge(intervals):
    """Merge [(start, end_inclusive)] into sorted disjoint ranges."""
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def build(cue):
    files = parse_cue(cue)
    cue_dir = os.path.dirname(cue)
    tracks_out, audio_out = [], []
    data = None
    for fl in files:
        p = os.path.join(cue_dir, fl["name"])
        if not os.path.isfile(p):
            raise DiscError("cue references '%s' but that file does not exist in %s "
                            "(missing or misnamed .bin)" % (fl["name"], cue_dir))
        fsize = os.path.getsize(p)
        trks = fl["tracks"]
        for i, t in enumerate(trks):
            sz, _ = MODES[t["mode"]]
            start = t["indexes"][1]
            if i + 1 < len(trks):
                nxt = trks[i + 1]
                end = nxt["indexes"].get(0, nxt["indexes"][1])
            else:
                end = fsize // sz
            entry = {"number": t["number"], "mode": t["mode"], "file": fl["name"],
                     "start_frame": start, "sectors": end - start,
                     "index_frames": {"%02d" % k: v for k, v in sorted(t["indexes"].items())}}
            tracks_out.append(entry)
            if t["mode"] == "AUDIO":
                audio_out.append(entry)
            elif data is None:
                data = (p, t["mode"], start, end - start, entry)
    if data is None:
        raise DiscError("no data track in cue")
    p, mode, start, nsec, tentry = data
    trk = Track(p, mode, start, nsec)
    try:
        pvd = trk.read_user(16)
        if pvd[0] != 1 or pvd[1:6] != b"CD001":
            raise DiscError("no ISO9660 primary volume descriptor at LBA 16")
        root_rec = pvd[156:190]
        root_lba = int.from_bytes(root_rec[2:6], "little")
        root_size = int.from_bytes(root_rec[10:14], "little")
        vol = {"volume_id": pvd[40:72].decode("ascii", "replace").strip(),
               "system_id": pvd[8:40].decode("ascii", "replace").strip(),
               "volume_space_sectors": int.from_bytes(pvd[80:84], "little"),
               "logical_block_size": int.from_bytes(pvd[128:130], "little"),
               "path_table_size": int.from_bytes(pvd[132:136], "little")}
        # filesystem structures
        structs = [{"what": "system_area", "lba": 0, "sectors": 16}]
        lba = 16
        while True:
            vd = trk.read_user(lba)
            if vd[1:6] != b"CD001":
                raise DiscError("bad volume descriptor at LBA %d" % lba)
            structs.append({"what": "volume_descriptor_type_%d" % vd[0], "lba": lba, "sectors": 1})
            lba += 1
            if vd[0] == 255:
                break
        pt_sectors = (vol["path_table_size"] + 2047) // 2048
        for key, off, big in (("path_table_L", 140, False), ("path_table_L_optional", 144, False),
                              ("path_table_M", 148, True), ("path_table_M_optional", 152, True)):
            v = int.from_bytes(pvd[off:off + 4], "big" if big else "little")
            if v:
                structs.append({"what": key, "lba": v, "sectors": pt_sectors})
        flist, dlist = walk(trk, root_lba, root_size)

        out_files = []
        for dpath, r in flist:
            nm = r["name"]
            base, _, ver = nm.partition(";")
            version = int(ver) if ver.isdigit() else None
            path = dpath.rstrip("/") + "/" + base
            sectors = (r["size"] + 2047) // 2048
            xa = r["xa"]
            st = trk.sector_stats(r["lba"], sectors)
            form2_attr = bool(xa and xa["mode2_form2"])
            inter_attr = bool(xa and xa["interleaved"])
            flagged = form2_attr or inter_attr or bool(st and st["form2_sectors"] > 0)
            out_files.append({
                "path": path, "name": base, "name_raw": nm, "version": version,
                "directory": dpath, "lba": r["lba"], "size_bytes": r["size"],
                "sectors": sectors, "end_lba": r["lba"] + sectors - 1 if sectors else None,
                "iso_flags": "0x%02x" % r["flags"], "iso_flag_names": flag_names(r["flags"]),
                "xa_record": xa, "xa_stats": st,
                "xa_flagged": flagged,
                "xa_flag_reasons": [n for n, c in (
                    ("xa_attr_form2", form2_attr), ("xa_attr_interleaved", inter_attr),
                    ("form2_sectors_in_extent", bool(st and st["form2_sectors"] > 0))) if c],
            })
        out_files.sort(key=lambda f: (f["lba"], f["path"]))
        out_dirs = sorted(dlist, key=lambda d: (d["lba"], d["path"]))

        # coverage
        cover = []
        for s in structs:
            cover.append((s["lba"], s["lba"] + s["sectors"] - 1, "struct:" + s["what"]))
        for d in out_dirs:
            cover.append((d["lba"], d["lba"] + d["sectors"] - 1, "dir:" + d["path"]))
        for f in out_files:
            if f["sectors"]:
                cover.append((f["lba"], f["end_lba"], "file:" + f["path"]))
        for s, e, w in cover:
            if s < 0 or e >= nsec:
                raise DiscError("%s extent %d..%d does not fit in track 1 (%d sectors)"
                                % (w, s, e, nsec))
        # overlaps (exact, pairwise via sweep)
        overlaps = []
        srt = sorted(cover)
        active = None
        for c in srt:
            if active and c[0] <= active[1]:
                overlaps.append({"a": active[2], "a_range": [active[0], active[1]],
                                 "b": c[2], "b_range": [c[0], c[1]]})
            if not active or c[1] > active[1]:
                active = c
        merged = merge([(s, e) for s, e, _ in cover])
        gaps = []
        prev = 0
        for s, e in merged + [[nsec, nsec]]:
            if s > prev:
                g = {"start_lba": prev, "end_lba": s - 1, "sectors": s - prev}
                g["sector_stats"] = trk.sector_stats(prev, s - prev)
                gaps.append(g)
            prev = max(prev, e + 1)

        top = {}
        for f in out_files:
            parts = f["path"].split("/")
            key = parts[1] if len(parts) > 2 else "(root)"
            top[key] = top.get(key, 0) + 1
        totals = {
            "file_count": len(out_files), "directory_count": len(out_dirs),
            "total_file_bytes": sum(f["size_bytes"] for f in out_files),
            "total_file_sectors": sum(f["sectors"] for f in out_files),
            "track1_sectors": nsec,
            "gap_ranges": len(gaps), "gap_sectors": sum(g["sectors"] for g in gaps),
            "files_with_xa_record": sum(1 for f in out_files if f["xa_record"]),
            "xa_flagged_files": sum(1 for f in out_files if f["xa_flagged"]),
            "overlap_count": len(overlaps),
            "files_per_top_level": {k: top[k] for k in sorted(top)},
        }
        res = {"cue": os.path.basename(cue), "tracks": tracks_out,
               "audio_tracks": audio_out, "audio_track_count": len(audio_out),
               "volume": vol, "filesystem_structures": structs,
               "directories": out_dirs, "files": out_files,
               "gaps": gaps, "overlaps": overlaps, "totals": totals}
        return res
    finally:
        trk.close()


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--cue")
    ap.add_argument("--out", default=os.path.join(root, "work", "disc_files.json"))
    a = ap.parse_args()
    try:
        cue = a.cue
        if not cue:
            d = os.path.join(root, "ps1_game")
            cues = sorted(x for x in os.listdir(d) if x.lower().endswith(".cue")) if os.path.isdir(d) else []
            if len(cues) != 1:
                raise DiscError("expected exactly one .cue in %s, found %d" % (d, len(cues)))
            cue = os.path.join(d, cues[0])
        res = build(os.path.abspath(cue))
    except DiscError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=2, sort_keys=True)
        f.write("\n")
    t = res["totals"]
    print("audio tracks: %d" % res["audio_track_count"])
    print("files: %d  directories: %d" % (t["file_count"], t["directory_count"]))
    print("total file bytes: %d  total file sectors: %d  track1 sectors: %d"
          % (t["total_file_bytes"], t["total_file_sectors"], t["track1_sectors"]))
    print("files with XA record: %d  XA/Form2-flagged files: %d"
          % (t["files_with_xa_record"], t["xa_flagged_files"]))
    print("gaps: %d ranges, %d sectors  overlaps: %d"
          % (t["gap_ranges"], t["gap_sectors"], t["overlap_count"]))
    for k, v in t["files_per_top_level"].items():
        print("  %-12s %d files" % (k, v))
    print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
