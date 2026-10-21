#!/usr/bin/env python3
"""No-game-data guard (T3.16). Stdlib only; works locally and in CI.

Fails (exit 1) when the git index / tracked files, or an explicit file list,
contain anything that looks like game data:

  * a path under generated/, ps1_game/ or work/ (generated/ at any depth)
  * a file with extension .bin .cue .iso .exe .dll .zip .ovr .str .mcd
    (also .chd .img .mcr .sym, which .gitignore also blocks)
  * overlay_captures.json
  * a file whose first 8 bytes are "PS-X EXE"
  * a raw CD sector image (starts with the 12-byte CD sync pattern)
  * a file (staged blob) larger than --max-mb (default 32) that is not allow-listed

Derived data allowed by D8 (seeds/*, game.toml, catalog_identity.json,
*.recomp.json, aot/overlays.json, symbols.toml, docs) is not matched by any
rule above. ALLOW below lists exact paths exempt from the *extension* and
*size* rules only; the PS-X EXE and path-prefix rules always apply.

Usage:
  python tools/check_no_game_data.py                 # repo containing this script
  python tools/check_no_game_data.py --repo DIR      # another git repo
  python tools/check_no_game_data.py --list FILE|-   # newline paths (e.g. a zip listing);
                                                     # with --root DIR also content-checks them
Exit: 0 clean, 1 violations (each printed as "FAIL <path>: <reason>"), 2 usage/git error.
Output is sorted, so it is identical across runs.
"""
import argparse
import os
import subprocess
import sys

BAD_EXT = {".bin", ".cue", ".iso", ".exe", ".dll", ".zip", ".ovr", ".str",
           ".mcd", ".chd", ".img", ".mcr", ".sym"}
BAD_PREFIX = ("ps1_game/", "work/", "generated/")
BAD_NAMES = {"overlay_captures.json"}
ALLOW = set()  # exact repo-relative paths exempt from extension/size rules
PSX_MAGIC = b"PS-X EXE"
CD_SYNC = b"\x00" + b"\xff" * 10 + b"\x00"


def git(repo, *args):
    try:
        return subprocess.run(["git", "-C", repo, *args], check=True,
                              capture_output=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        err = getattr(e, "stderr", b"") or b""
        print("ERROR: git %s failed: %s %s" % (" ".join(args), e, err.decode(errors="replace")),
              file=sys.stderr)
        sys.exit(2)


def index_heads(repo, entries):
    """{path: (first 12 bytes, size)} from the staged blobs (git cat-file --batch)."""
    out = {}
    proc = subprocess.Popen(["git", "-C", repo, "cat-file", "--batch"],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for oid, path in entries:
            proc.stdin.write(oid.encode() + b"\n")
            proc.stdin.flush()
            hdr = proc.stdout.readline().split()
            if len(hdr) != 3:
                print("ERROR: cat-file failed for %s (%s)" % (path, oid), file=sys.stderr)
                sys.exit(2)
            size = int(hdr[2])
            head = proc.stdout.read(min(12, size))
            left = size - len(head) + 1  # content remainder + trailing LF
            while left > 0:
                left -= len(proc.stdout.read(min(left, 1 << 20)) or b"\0" * left)
            out[path] = (head, size)
    finally:
        proc.stdin.close()
        proc.wait()
    return out


def tree_heads(root, paths):
    out = {}
    for path in paths:
        full = os.path.join(root, *path.split("/"))
        if os.path.isfile(full):
            with open(full, "rb") as f:
                out[path] = (f.read(12), os.path.getsize(full))
    return out


def check(paths, heads, max_bytes):
    problems = []
    for p in sorted(set(paths)):
        norm = p.replace("\\", "/")
        if norm.startswith("./"):
            norm = norm[2:]
        low = norm.lower()
        reasons = []
        if any(low.startswith(d) or "/" + d in low for d in BAD_PREFIX):
            reasons.append("path under forbidden directory")
        if "/generated/" in "/" + low:
            reasons.append("generated/ directory")
        name = low.rsplit("/", 1)[-1]
        if name in BAD_NAMES:
            reasons.append("overlay_captures.json")
        allowed = norm in ALLOW
        ext = os.path.splitext(name)[1]
        if ext in BAD_EXT and not allowed:
            reasons.append("forbidden extension " + ext)
        head, size = heads.get(p, heads.get(norm, (None, None)))
        if head is not None:
            if head[:8] == PSX_MAGIC:
                reasons.append("PS-X EXE header")
            if head[:12] == CD_SYNC:
                reasons.append("raw CD sector (sync pattern)")
            if size > max_bytes and not allowed:
                reasons.append("file larger than %d MB (%d bytes)" % (max_bytes >> 20, size))
        for r in dict.fromkeys(reasons):
            problems.append((norm, r))
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--list", help="file of newline-separated paths ('-' = stdin) instead of git ls-files")
    ap.add_argument("--root", help="directory the --list paths are relative to (enables content checks)")
    ap.add_argument("--max-mb", type=int, default=32)
    a = ap.parse_args()

    if a.list:
        data = sys.stdin.read() if a.list == "-" else open(a.list, encoding="utf-8").read()
        paths = [l.strip() for l in data.splitlines() if l.strip() and not l.strip().endswith("/")]
        source = "list"
    else:
        out = git(a.repo, "ls-files", "-z", "--cached", "--stage")
        paths, entries = [], []
        for rec in out.split(b"\0"):
            if not rec:
                continue
            meta, _, path = rec.partition(b"\t")
            if meta.startswith(b"160000"):  # submodule gitlink, not a file
                continue
            path = path.decode("utf-8", "surrogateescape")
            paths.append(path)
            entries.append((meta.split()[1].decode(), path))
        source = "git"
    if a.list:
        heads = tree_heads(a.root, paths) if a.root else {}
    else:
        heads = index_heads(a.repo, entries)  # staged blobs, never the work tree
    problems = check(paths, heads, a.max_mb << 20)
    for path, reason in problems:
        print("FAIL %s: %s" % (path, reason))
    print("%s: %d files checked (%s), %d violation(s)" % (
        "FAIL" if problems else "OK", len(set(paths)), source, len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
