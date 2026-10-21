#!/usr/bin/env python3
"""Release content check (T3.19). Stdlib only.

Checks a staged release folder (--dir) or the finished zip (--zip) against an
ALLOW-LIST layout plus a deny-list of things that must never ship. Every
violation prints one line "FAIL <path>: <reason>"; exit 1 if there is any.

  python tools/check_release_content.py --dir DIR  [--generated-dir GEN] [--openbios-sha256 HEX]
  python tools/check_release_content.py --zip FILE [--generated-dir GEN] [--openbios-sha256 HEX]

Deny-list (any depth, case-insensitive):
  * extensions .bin .cue .iso .chd .img .mcd .mcr .mcc .vmc .gme .pbp .ccd .sub .mds .mdf
    (the single exception is bios/openbios.bin, the bundled OpenBIOS image; with
    --openbios-sha256 its SHA-256 must match, so a retail BIOS renamed to that
    path is caught)
  * session recordings: any path segment "session-*" or "diagnostics", or a file named
    inputs.csv, telemetry.csv, session.json, mods-state.toml; anything under saves/
  * path segments ps1_game, work, generated, cache, disc, seeds, psxrecomp, recomp-ui
  * names overlay_captures.json (and .d), disc.cfg, rom.cfg, settings.toml, keybinds.ini,
    input.ini, psx_crash.txt, psx_last_run_report.json, psx_freeze_heartbeat.json,
    compiler.txt (holds a machine path), *.pdb
  * BIOS dumps: SCPH* (other than .toml profiles), *.rom, any file of exactly 512 KiB
    that is not bios/openbios.bin (a retail BIOS is 512 KiB)
  * content: first 8 bytes "PS-X EXE"; first 12 bytes = CD sync pattern
  * C/C++ sources: .c .cc .cpp .cxx .h .hpp .inc outside overlay_toolchain/ ; and, with
    --generated-dir, any file anywhere whose SHA-256 equals a file under that folder
    (generated game C must never ship, even renamed). Names SLUS_* and overlays_static*.
  * local paths: text files (txt toml json ini cfg md cmd py) containing "<drive>:\\Users\\"
  * zip hygiene: absolute names, "..", backslashes, symlinks, duplicate names
  * sizes: exe 8..256 MiB, no other file > 64 MiB, release total <= 400 MiB (tunable)
Layout (allow-list of top-level names): the exe + its execution.json + psx_game_version.txt,
assets/ bios/ mods/ overlay_toolchain/ licenses/ game.toml game_options.toml LICENSE NOTICE
README_FIRST.txt release_info.json, plus sibling *.dll. A top-level wrapper folder (the
zip's single root folder) is stripped first. Required files must exist.

--deep adds informational "WARN" lines (not failures) when PS-X EXE or the CD sync pattern
occurs anywhere inside a file (the runtime code may legitimately carry those constants).
Output is sorted, so it is identical across runs.
"""
import argparse
import hashlib
import os
import re
import stat
import sys
import zipfile

BAD_EXT = {".bin", ".cue", ".iso", ".chd", ".img", ".mcd", ".mcr", ".mcc", ".vmc",
           ".gme", ".pbp", ".ccd", ".sub", ".mds", ".mdf", ".rom", ".pdb"}
BAD_SEGMENTS = {"ps1_game", "work", "generated", "cache", "disc", "seeds", "psxrecomp",
                "recomp-ui", "diagnostics", "saves"}
BAD_NAMES = {"overlay_captures.json", "overlay_captures.json.d", "disc.cfg", "rom.cfg",
             "settings.toml", "keybinds.ini", "input.ini", "psx_crash.txt",
             "psx_last_run_report.json", "psx_freeze_heartbeat.json", "compiler.txt",
             "inputs.csv", "telemetry.csv", "session.json", "mods-state.toml"}
SRC_EXT = {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".inc"}
TEXT_EXT = {".txt", ".toml", ".json", ".ini", ".cfg", ".md", ".cmd", ".py"}
TOP_ALLOWED = {"assets", "bios", "mods", "overlay_toolchain", "licenses", "game.toml",
               "game_options.toml", "license", "notice", "readme_first.txt",
               "release_info.json", "psx_game_version.txt"}
REQUIRED = ["MythologyKombat.exe", "LICENSE", "NOTICE", "README_FIRST.txt", "release_info.json",
            "game.toml", "psx_game_version.txt", "bios/openbios.bin", "bios/OpenBIOS.LICENSE",
            "assets", "mods/bundled"]
OPENBIOS = "bios/openbios.bin"
EXE_NAME = "MythologyKombat.exe"
PSX_MAGIC = b"PS-X EXE"
CD_SYNC = b"\x00" + b"\xff" * 10 + b"\x00"
LOCAL_PATH = re.compile(rb"[A-Za-z]:(?:\\{1,4}|/)Users(?:\\{1,4}|/)[A-Za-z0-9_]", re.I)  # a user-specific path, also JSON-escaped or with forward slashes; "C:/Users/..." in a comment is not one
MIB = 1 << 20
TEXT_SCAN_MAX = 4 * MIB


class Entry:
    """One file: relative path (forward slashes), size, and lazy content access."""

    def __init__(self, rel, size, opener):
        self.rel, self.size, self._open = rel, size, opener

    def head(self, n=12):
        with self._open() as f:
            return f.read(n)

    def read_all(self):
        with self._open() as f:
            return f.read()

    def sha256(self):
        h = hashlib.sha256()
        with self._open() as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()


def sha_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def entries_from_dir(root):
    out, problems = [], []
    for dp, dn, fn in os.walk(root):
        for name in fn:
            full = os.path.join(dp, name)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if os.path.islink(full):
                problems.append((rel, "symbolic link"))
                continue
            out.append(Entry(rel, os.path.getsize(full), lambda p=full: open(p, "rb")))
    return out, problems


def entries_from_zip(path):
    out, problems = [], []
    zf = zipfile.ZipFile(path)
    seen = set()
    for info in zf.infolist():
        name = info.filename
        if "\\" in name:
            problems.append((name, "backslash in zip entry name"))
            name = name.replace("\\", "/")
        if name.startswith("/") or re.match(r"^[A-Za-z]:", name) or ".." in name.split("/"):
            problems.append((name, "absolute or parent-relative zip entry name"))
        if name.endswith("/"):
            continue
        mode = info.external_attr >> 16
        if mode and stat.S_ISLNK(mode):
            problems.append((name, "symbolic link"))
        if name.lower() in seen:
            problems.append((name, "duplicate zip entry"))
        seen.add(name.lower())
        out.append(Entry(name, info.file_size, lambda i=info: zf.open(i)))
    return out, problems


def strip_wrapper(entries):
    """Strip a single wrapper folder when every entry lives under one top-level folder."""
    tops = {e.rel.split("/", 1)[0] for e in entries}
    if len(tops) == 1 and all("/" in e.rel for e in entries):
        top = next(iter(tops))
        if top.lower() not in TOP_ALLOWED:
            for e in entries:
                e.rel = e.rel.split("/", 1)[1]
            return top
    return None


def generated_hashes(gen_dir):
    hashes = {}
    for dp, dn, fn in os.walk(gen_dir):
        for name in fn:
            full = os.path.join(dp, name)
            if os.path.getsize(full) == 0:
                continue
            hashes.setdefault(sha_of_file(full), os.path.relpath(full, gen_dir).replace("\\", "/"))
    return hashes


def check(entries, gen_hashes=None, openbios_sha=None, deep=False,
          exe_mib=(8, 256), file_max_mib=64, total_max_mib=400):
    fails, warns = [], []

    def fail(rel, why):
        fails.append((rel, why))

    total = 0
    for e in entries:
        rel = e.rel
        low = rel.lower()
        segs = low.split("/")
        name = segs[-1]
        ext = os.path.splitext(name)[1]
        total += e.size
        in_ovtc = segs[0] == "overlay_toolchain"
        is_openbios = (low == OPENBIOS)

        if len(segs) == 1 and name not in TOP_ALLOWED and name != EXE_NAME.lower() \
                and name != "mythologykombat.execution.json" and ext != ".dll":
            fail(rel, "not on the top-level allow-list")
        if len(segs) > 1 and segs[0] not in TOP_ALLOWED:
            fail(rel, "top-level folder %r is not on the allow-list" % segs[0])
        for s in segs[:-1]:
            if s in BAD_SEGMENTS and not (in_ovtc and s in ("seeds", "psxrecomp")):
                fail(rel, "forbidden directory %r" % s)
            if s.startswith("session-"):
                fail(rel, "session recording folder")
        if name.startswith("session-"):
            fail(rel, "session recording")
        if name in BAD_NAMES:
            fail(rel, "forbidden file name %s" % name)
        if ext in BAD_EXT and not is_openbios:
            fail(rel, "forbidden extension %s" % ext)
        if name.startswith("scph") and ext != ".toml":
            fail(rel, "BIOS dump name (SCPH*)")
        if name.startswith("slus_") or name.startswith("overlays_static"):
            fail(rel, "game-derived file name")
        if ext == ".exe" and not (low == EXE_NAME.lower() or in_ovtc):
            fail(rel, "executable outside the allowed exe and overlay_toolchain/")
        if ext in SRC_EXT and not in_ovtc:
            fail(rel, "C/C++ source outside overlay_toolchain/ (sources must not ship)")
        if e.size == 512 * 1024 and not is_openbios:
            fail(rel, "512 KiB file (size of a retail BIOS image)")

        if is_openbios:
            if openbios_sha and e.sha256() != openbios_sha.lower():
                fail(rel, "SHA-256 differs from the bundled OpenBIOS image")
        elif e.size >= 8:
            head = e.head(12)
            if head[:8] == PSX_MAGIC:
                fail(rel, "PS-X EXE header")
            if head[:12] == CD_SYNC:
                fail(rel, "raw CD sector (sync pattern)")

        if gen_hashes and e.size > 0:
            h = e.sha256()
            if h in gen_hashes:
                fail(rel, "identical to generated/%s (generated code must not ship)" % gen_hashes[h])

        if ext in TEXT_EXT and 0 < e.size <= TEXT_SCAN_MAX:
            m = LOCAL_PATH.search(e.read_all())
            if m:
                fail(rel, "contains a local user path (%s...)" % m.group(0).decode("ascii", "replace"))

        if deep and e.size > 0 and not is_openbios and e.size <= 512 * MIB:
            data = e.read_all()
            if PSX_MAGIC in data:
                warns.append((rel, "contains 'PS-X EXE' at offset %d (informational)" % data.find(PSX_MAGIC)))
            if CD_SYNC in data:
                warns.append((rel, "contains a CD sync pattern at offset %d (informational)" % data.find(CD_SYNC)))

        if low == EXE_NAME.lower():
            lo, hi = exe_mib
            if not (lo * MIB <= e.size <= hi * MIB):
                fail(rel, "exe size %d bytes outside %d..%d MiB" % (e.size, lo, hi))
        elif e.size > file_max_mib * MIB:
            fail(rel, "file larger than %d MiB (%d bytes)" % (file_max_mib, e.size))

    if total > total_max_mib * MIB:
        fail("(release total)", "uncompressed total %d bytes exceeds %d MiB" % (total, total_max_mib))

    present = {e.rel.lower() for e in entries}
    prefixes = {p for e in entries for p in _prefixes(e.rel.lower())}
    for req in REQUIRED:
        r = req.lower()
        if r not in present and r not in prefixes:
            fail(req, "required item is missing")
    return sorted(set(fails)), sorted(set(warns))


def _prefixes(low):
    parts = low.split("/")
    return ["/".join(parts[:i]) for i in range(1, len(parts))]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dir")
    g.add_argument("--zip")
    ap.add_argument("--generated-dir", help="folder of generated game C; files equal to any of it fail")
    ap.add_argument("--openbios-sha256", help="expected SHA-256 of bios/openbios.bin")
    ap.add_argument("--deep", action="store_true")
    ap.add_argument("--exe-mib", default="8,256", help="min,max exe size in MiB")
    ap.add_argument("--file-max-mib", type=int, default=64)
    ap.add_argument("--total-max-mib", type=int, default=400)
    a = ap.parse_args()
    try:
        if a.dir:
            entries, problems = entries_from_dir(a.dir)
            src = "dir"
        else:
            entries, problems = entries_from_zip(a.zip)
            src = "zip"
    except (OSError, zipfile.BadZipFile) as e:
        print("ERROR: cannot read input: %s" % e, file=sys.stderr)
        return 2
    wrapper = strip_wrapper(entries)
    gh = None
    if a.generated_dir:
        if not os.path.isdir(a.generated_dir):
            print("ERROR: --generated-dir not found: %s" % a.generated_dir, file=sys.stderr)
            return 2
        gh = generated_hashes(a.generated_dir)
    lo, hi = (int(x) for x in a.exe_mib.split(","))
    fails, warns = check(entries, gh, a.openbios_sha256, a.deep, (lo, hi), a.file_max_mib, a.total_max_mib)
    fails = sorted(set(fails) | set(problems))
    for rel, why in fails:
        print("FAIL %s: %s" % (rel, why))
    for rel, why in warns:
        print("WARN %s: %s" % (rel, why))
    print("%s: %d files checked (%s%s%s), %d violation(s)" % (
        "FAIL" if fails else "OK", len(entries), src,
        ", wrapper folder %s" % wrapper if wrapper else "",
        ", %d generated hashes" % len(gh) if gh else "", len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
