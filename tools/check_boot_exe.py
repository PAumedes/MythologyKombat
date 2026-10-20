"""Check disc digests / boot EXE against game.toml and disc_probe.json.

Reusable: python -I tools/check_boot_exe.py [--repo DIR]
 - SHA-256 of the extracted boot EXE (game.toml [game] exe) == disc_probe.json boot_exe_sha256
 - disc_probe.json data_track md5/sha1/crc32/size == game.toml [prepare_disc] known_* (if probe exists)
Exit 0 only if everything present matches. Stdlib only (tomllib needs 3.11+; embeddable here is 3.12).
"""
import argparse, hashlib, json, sys
from pathlib import Path
import tomllib

ap = argparse.ArgumentParser()
ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
a = ap.parse_args()
root = Path(a.repo)
cfg = tomllib.loads((root / "game.toml").read_text(encoding="utf-8"))
ok = True

exe = root / cfg["game"]["exe"]
h = hashlib.sha256(exe.read_bytes()).hexdigest()
print(f"exe {exe} size={exe.stat().st_size} sha256={h}")

probe_path = root / "disc_probe.json"
if not probe_path.exists():
    print("disc_probe.json not present (git-ignored, machine-specific): digest cross-check skipped")
    sys.exit(0)
p = json.loads(probe_path.read_text(encoding="utf-8"))
m = h == p["boot_exe_sha256"]
print(f"boot_exe_sha256 vs disc_probe.json: {'MATCH' if m else 'MISMATCH'} ({p['boot_exe_sha256']})")
ok &= m
pd = cfg["prepare_disc"]
for key, probe_key, conv in (("known_md5", "data_track_md5", str), ("known_sha1", "data_track_sha1", str),
                             ("known_crc32", "data_track_crc32", str), ("known_sizes", "data_track_size", int)):
    mm = conv(p[probe_key]) in [conv(x) for x in pd[key]]
    print(f"{key} vs disc_probe.{probe_key}: {'MATCH' if mm else 'MISMATCH'}")
    ok &= mm
print("OK" if ok else "FAIL")
sys.exit(0 if ok else 1)
