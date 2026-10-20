#!/usr/bin/env python3
"""Identify and fingerprint a PS1 disc image (T0.4).

Parses the .cue, lists tracks, SHA-256 hashes each .bin (streaming), reads
SYSTEM.CNF from the ISO9660 filesystem of the first data track (raw 2352-byte
sectors supported) and reports the boot executable / serial.

Output is deterministic (no timestamps, no absolute paths): work/disc_identity.json.
Standard library only. Read-only on the disc image.

Usage:
  python -I tools/disc_identify.py [--cue PATH] [--out PATH]
"""
import argparse
import hashlib
import json
import os
import re
import sys

SYNC = b"\x00" + b"\xff" * 10 + b"\x00"
CHUNK = 4 * 1024 * 1024

# mode -> (sector_size, user_data_offset or None for audio)
MODES = {
    "MODE1/2048": (2048, 0),
    "MODE1/2352": (2352, 16),
    "MODE2/2336": (2336, 8),
    "MODE2/2352": (2352, 24),  # Form 1 assumed; verified via subheader
    "AUDIO": (2352, None),
}


class DiscError(Exception):
    pass


def msf_to_frames(s):
    m = re.fullmatch(r"(\d+):(\d\d):(\d\d)", s)
    if not m:
        raise DiscError("bad MM:SS:FF timestamp in cue: %r" % s)
    mm, ss, ff = map(int, m.groups())
    return (mm * 60 + ss) * 75 + ff


def parse_cue(cue_path):
    try:
        with open(cue_path, "r", encoding="utf-8-sig", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError as e:
        raise DiscError("cannot read cue %s: %s" % (cue_path, e))
    files = []
    cur_file = None
    cur_track = None
    for ln, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        m = re.match(r'FILE\s+(?:"([^"]*)"|(\S+))\s+(\S+)', line, re.I)
        if m:
            cur_file = {"name": m.group(1) if m.group(1) is not None else m.group(2),
                        "type": m.group(3).upper(), "tracks": []}
            files.append(cur_file)
            cur_track = None
            continue
        m = re.match(r"TRACK\s+(\d+)\s+(\S+)", line, re.I)
        if m:
            if cur_file is None:
                raise DiscError("cue line %d: TRACK before FILE" % ln)
            mode = m.group(2).upper()
            if mode not in MODES:
                raise DiscError("cue line %d: unsupported track mode %s" % (ln, mode))
            cur_track = {"number": int(m.group(1)), "mode": mode, "indexes": {}}
            cur_file["tracks"].append(cur_track)
            continue
        m = re.match(r"INDEX\s+(\d+)\s+(\S+)", line, re.I)
        if m:
            if cur_track is None:
                raise DiscError("cue line %d: INDEX before TRACK" % ln)
            cur_track["indexes"][int(m.group(1))] = msf_to_frames(m.group(2))
            continue
        # PREGAP, POSTGAP, FLAGS, CATALOG, REM, etc. ignored
    if not files:
        raise DiscError("cue has no FILE entries")
    for fl in files:
        if not fl["tracks"]:
            raise DiscError("cue FILE %r has no TRACK" % fl["name"])
        for t in fl["tracks"]:
            if 1 not in t["indexes"]:
                raise DiscError("track %02d has no INDEX 01" % t["number"])
    return files


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


class Track1Reader:
    """Reads 2048-byte user-data sectors of a data track (LBA 0 = INDEX 01)."""

    def __init__(self, path, mode, start_frame):
        self.f = open(path, "rb")
        self.size, self.off = MODES[mode]
        self.mode = mode
        self.start = start_frame
        self.fsize = os.path.getsize(path)

    def read_sector(self, lba):
        pos = (self.start + lba) * self.size
        if pos + self.size > self.fsize:
            raise DiscError("LBA %d is beyond the end of the .bin" % lba)
        self.f.seek(pos)
        raw = self.f.read(self.size)
        if self.mode in ("MODE1/2352", "MODE2/2352") and raw[:12] != SYNC:
            raise DiscError("LBA %d: no CD sync pattern; not a raw 2352 sector (wrong mode in cue?)" % lba)
        if self.mode == "MODE2/2352":
            if raw[16:20] != raw[20:24]:
                raise DiscError("LBA %d: inconsistent Mode 2 subheader copies" % lba)
            if raw[18] & 0x20:
                raise DiscError("LBA %d: Form 2 sector where Form 1 data expected" % lba)
        return raw[self.off:self.off + 2048]

    def read_extent(self, lba, size):
        n = (size + 2047) // 2048
        return b"".join(self.read_sector(lba + i) for i in range(n))[:size]

    def close(self):
        self.f.close()


def parse_dir(data):
    entries = []
    pos = 0
    while pos < len(data):
        ln = data[pos]
        if ln == 0:  # padding to next sector boundary
            pos = (pos // 2048 + 1) * 2048
            continue
        rec = data[pos:pos + ln]
        nlen = rec[32]
        name = rec[33:33 + nlen]
        if name == b"\x00":
            name = "."
        elif name == b"\x01":
            name = ".."
        else:
            name = name.decode("ascii", "replace")
        entries.append({
            "name": name,
            "lba": int.from_bytes(rec[2:6], "little"),
            "size": int.from_bytes(rec[10:14], "little"),
            "is_dir": bool(rec[25] & 2),
        })
        pos += ln
    return entries


def find_in_root(rd, root, name):
    for e in parse_dir(rd.read_extent(root["lba"], root["size"])):
        strip = lambda n: n.upper().split(";")[0]
        if strip(e["name"]) == strip(name) and not e["is_dir"]:
            return e
    return None


REGIONS = {
    "SLUS": "NTSC-U", "SCUS": "NTSC-U",
    "SLES": "PAL", "SCES": "PAL",
    "SLPS": "NTSC-J", "SLPM": "NTSC-J", "SCPS": "NTSC-J", "SCPM": "NTSC-J",
}


def identify(rd):
    pvd = rd.read_sector(16)
    if pvd[0] != 1 or pvd[1:6] != b"CD001":
        raise DiscError("no ISO9660 primary volume descriptor at LBA 16")
    root_rec = pvd[156:190]
    root = {"lba": int.from_bytes(root_rec[2:6], "little"),
            "size": int.from_bytes(root_rec[10:14], "little")}
    volume_id = pvd[40:72].decode("ascii", "replace").strip()
    ent = find_in_root(rd, root, "SYSTEM.CNF;1") or find_in_root(rd, root, "SYSTEM.CNF")
    if not ent:
        raise DiscError("SYSTEM.CNF not found in ISO9660 root directory")
    cnf = rd.read_extent(ent["lba"], ent["size"]).decode("ascii", "replace")
    boot = None
    for line in cnf.splitlines():
        m = re.match(r"\s*BOOT\s*=\s*(.+?)\s*$", line, re.I)
        if m:
            boot = m.group(1)
            break
    if boot is None:
        raise DiscError("no BOOT= line in SYSTEM.CNF")
    m = re.search(r"([A-Za-z]{4})[_\-.]?(\d{3})\.?(\d{2})", boot)
    if not m:
        raise DiscError("cannot extract a serial from BOOT line: %r" % boot)
    prefix = m.group(1).upper()
    exe_name = re.split(r"[\\/:]", boot)[-1]
    exe_ent = find_in_root(rd, root, exe_name)
    result = {
        "volume_id": volume_id,
        "system_cnf_lines": [l.strip() for l in cnf.splitlines() if l.strip()],
        "boot_line": boot,
        "boot_executable": exe_name,
        "boot_executable_in_root": exe_ent is not None,
        "boot_executable_size": exe_ent["size"] if exe_ent else None,
        "serial": "%s-%s%s" % (prefix, m.group(2), m.group(3)),
        "serial_source": "SYSTEM.CNF BOOT=",
        "region": REGIONS.get(prefix, "UNKNOWN"),
    }
    result["is_ntsc_u"] = prefix in ("SLUS", "SCUS")
    return result


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--cue")
    ap.add_argument("--out", default=os.path.join(root, "work", "disc_identity.json"))
    a = ap.parse_args()
    try:
        cue = a.cue
        if not cue:
            d = os.path.join(root, "ps1_game")
            cues = sorted(x for x in os.listdir(d) if x.lower().endswith(".cue")) if os.path.isdir(d) else []
            if len(cues) != 1:
                raise DiscError("expected exactly one .cue in %s, found %d" % (d, len(cues)))
            cue = os.path.join(d, cues[0])
        cue = os.path.abspath(cue)
        files = parse_cue(cue)
        cue_dir = os.path.dirname(cue)
        out_files, tracks = [], []
        data_reader = None
        try:
            for fl in files:
                p = os.path.join(cue_dir, fl["name"])
                if not os.path.isfile(p):
                    raise DiscError("cue references '%s' but that file does not exist in %s "
                                    "(missing or misnamed .bin)" % (fl["name"], cue_dir))
                size = os.path.getsize(p)
                tsz = MODES[fl["tracks"][0]["mode"]][0]
                out_files.append({"name": fl["name"], "size_bytes": size,
                                  "sectors": size // tsz, "size_is_sector_multiple": size % tsz == 0,
                                  "sha256": sha256_file(p)})
                for t in fl["tracks"]:
                    sz, _ = MODES[t["mode"]]
                    tracks.append({"number": t["number"], "mode": t["mode"], "sector_size": sz,
                                   "file": fl["name"],
                                   "index_frames": {"%02d" % k: v for k, v in sorted(t["indexes"].items())}})
                    if data_reader is None and t["mode"] != "AUDIO":
                        data_reader = Track1Reader(p, t["mode"], t["indexes"][1])
            if data_reader is None:
                raise DiscError("no data track in cue")
            ident = identify(data_reader)
        finally:
            if data_reader:
                data_reader.close()
        res = {"cue": os.path.basename(cue), "files": out_files, "tracks": tracks, "iso9660": ident}
    except DiscError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=2, sort_keys=True)
        f.write("\n")
    for t in tracks:
        print("track %02d  %-10s %s" % (t["number"], t["mode"], t["file"]))
    for fl in out_files:
        print("sha256 %s  %s (%d bytes)" % (fl["sha256"], fl["name"], fl["size_bytes"]))
    print("SYSTEM.CNF BOOT = %s" % ident["boot_line"])
    print("serial: %s  region: %s" % (ident["serial"], ident["region"]))
    if not ident["is_ntsc_u"]:
        print("!!! WARNING: serial is NOT NTSC-U (SLUS-/SCUS-). Region is %s. !!!" % ident["region"])
    else:
        print("NTSC-U confirmed (SLUS-/SCUS- prefix)")
    print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
