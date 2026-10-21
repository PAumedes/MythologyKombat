"""Negative controls for tools/check_release_content.py (T3.19).

Run: python -I tests/test_check_release_content.py
Builds a small synthetic release folder under work/release_check_test (git-ignored),
proves it passes, then plants one forbidden thing at a time and proves the check
fails and names the planted path. No game data is used: the "PS-X EXE" and "CD sync"
files are synthetic byte strings.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(ROOT, "tools", "check_release_content.py")
SCRATCH = os.path.join(ROOT, "work", "release_check_test")
GOOD = os.path.join(SCRATCH, "good")
GEN = os.path.join(SCRATCH, "generated")
OPENBIOS = b"\x11" * (512 * 1024)
OPENBIOS_SHA = None


def rmtree(p):
    def fix(fn, path, _):
        os.chmod(path, 0o700)
        fn(path)
    if os.path.isdir(p):
        shutil.rmtree(p, onerror=fix)


def put(root, rel, data=b"x\n"):
    full = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as f:
        f.write(data)
    return full


def build_good(root):
    put(root, "MythologyKombat.exe", b"MZ" + b"\x90" * (9 * 1024 * 1024))
    put(root, "MythologyKombat.execution.json", b"{}\n")
    put(root, "psx_game_version.txt", b"0.1.0\n")
    put(root, "LICENSE", b"license\n")
    put(root, "NOTICE", b"notice\n")
    put(root, "README_FIRST.txt", b"readme\n")
    put(root, "release_info.json", b"{}\n")
    put(root, "game.toml", b'[game]\ndisc = "ps1_game/x.cue"\n')
    put(root, "game_options.toml", b"# none\n")
    put(root, "bios/openbios.bin", OPENBIOS)
    put(root, "bios/OpenBIOS.LICENSE", b"mit\n")
    put(root, "assets/fonts/a.ttf", b"font")
    put(root, "mods/bundled/mythologykombat.diagnostics/1.0.0/manifest.toml", b"id='x'\n")
    put(root, "overlay_toolchain/include/cpu_state.h", b"// runtime header\n")
    put(root, "overlay_toolchain/psxrecomp-game.exe", b"MZ" + b"\x00" * 1000)
    put(root, "licenses/TinyCC-LICENSE.txt", b"lgpl\n")
    put(root, "update.cmd", b"@echo off\r\npowershell -NoProfile -File update.ps1\r\n")
    put(root, "update.ps1", b"# updater\n")
    write_manifest(root)


def write_manifest(root):
    files = []
    for dp, _, fn in os.walk(root):
        for n in fn:
            full = os.path.join(dp, n)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if rel == "manifest.json":
                continue
            with open(full, "rb") as f:
                data = f.read()
            files.append({"path": rel, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    files.sort(key=lambda x: x["path"])
    put(root, "manifest.json", json.dumps({"manifest_version": 1, "files": files}).encode())


def run(*args):
    r = subprocess.run([sys.executable, "-I", CHECK, *args], capture_output=True, text=True)
    return r.returncode, r.stdout


class Release(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import hashlib
        global OPENBIOS_SHA
        OPENBIOS_SHA = hashlib.sha256(OPENBIOS).hexdigest()

    def setUp(self):
        rmtree(SCRATCH)
        os.makedirs(SCRATCH)
        build_good(GOOD)
        put(GEN, "SLUS_004.76_full_0001.c", b"/* synthetic generated game C */\nint f(void){return 1;}\n")

    def tearDown(self):
        rmtree(SCRATCH)

    def args(self):
        write_manifest(GOOD)   # planted files are listed, so only the planted fault is reported
        return ["--dir", GOOD, "--generated-dir", GEN, "--openbios-sha256", OPENBIOS_SHA]

    def test_good_tree_passes(self):
        code, out = run(*self.args())
        self.assertEqual(code, 0, out)
        self.assertIn("OK:", out)

    def test_good_zip_passes_with_wrapper(self):
        z = os.path.join(SCRATCH, "r.zip")
        with zipfile.ZipFile(z, "w") as zf:
            for dp, _, fn in os.walk(GOOD):
                for n in fn:
                    full = os.path.join(dp, n)
                    zf.write(full, "MythologyKombat-test/" + os.path.relpath(full, GOOD).replace("\\", "/"))
        code, out = run("--zip", z, "--generated-dir", GEN, "--openbios-sha256", OPENBIOS_SHA)
        self.assertEqual(code, 0, out)
        self.assertIn("wrapper folder", out)

    def plant(self, rel, data=b"x\n"):
        put(GOOD, rel, data)
        code, out = run(*self.args())
        self.assertEqual(code, 1, "expected FAIL for %s\n%s" % (rel, out))
        self.assertIn("FAIL " + rel, out)
        return out

    def test_forbidden_extensions(self):
        for ext in (".bin", ".cue", ".iso", ".chd", ".img", ".mcd", ".mcr"):
            with self.subTest(ext=ext):
                self.plant("extra/disc" + ext)

    def test_disc_in_nested_and_ps1_game(self):
        self.plant("ps1_game/Mortal Kombat Mythologies - Sub-Zero.cue")
        self.plant("assets/Game.BIN")

    def test_recordings(self):
        for rel in ("saves/diagnostics/session-1/inputs.csv", "assets/telemetry.csv",
                    "mods/session-9/x.txt", "saves/card1.mcd", "assets/inputs.csv"):
            with self.subTest(rel=rel):
                self.plant(rel)

    def test_dev_artifacts(self):
        for rel in ("overlay_captures.json", "disc.cfg", "settings.toml",
                    "overlay_toolchain/compiler.txt", "psx_crash.txt"):
            with self.subTest(rel=rel):
                self.plant(rel)

    def test_ps_x_exe_header(self):
        out = self.plant("assets/boot.dat", b"PS-X EXE" + b"\x00" * 100)
        self.assertIn("PS-X EXE header", out)

    def test_cd_sync(self):
        out = self.plant("assets/sector.dat", b"\x00" + b"\xff" * 10 + b"\x00" + b"\x01" * 2340)
        self.assertIn("CD sector", out)

    def test_generated_source_by_name_and_by_hash(self):
        self.plant("generated/SLUS_004.76_full_0001.c")
        # renamed copy of a generated file under overlay_toolchain/ (where .c is otherwise allowed)
        with open(os.path.join(GEN, "SLUS_004.76_full_0001.c"), "rb") as f:
            data = f.read()
        out = self.plant("overlay_toolchain/include/innocent.c", data)
        self.assertIn("identical to generated/", out)

    def test_source_outside_overlay_toolchain(self):
        self.plant("assets/foo.c")
        self.plant("assets/foo.h")

    def test_bios(self):
        self.plant("bios/SCPH1001.BIN")
        self.plant("assets/bios.dat", b"\x22" * (512 * 1024))
        # a different image placed at the openbios path
        put(GOOD, "bios/openbios.bin", b"\x33" * (512 * 1024))
        code, out = run(*self.args())
        self.assertEqual(code, 1)
        self.assertIn("FAIL bios/openbios.bin: SHA-256 differs", out)

    def test_local_path_in_text(self):
        self.plant("README_FIRST.txt", b"see C:\\Users\\someone\\x\n")

    def test_local_path_json_escaped_and_slashes(self):
        self.plant("release_info.json", b'{"PSPath": "C:\\\\Users\\\\someone\\\\x"}\n')
        self.plant("assets/p.json", b'{"p": "C:/Users/someone/x"}\n')

    def test_generic_users_placeholder_is_not_flagged(self):
        put(GOOD, "overlay_toolchain/note.py", b"# gcc -v showed /home/x arriving as C:/Users/... here\n")
        code, out = run(*self.args())
        self.assertEqual(code, 0, out)

    def test_missing_required(self):
        os.remove(os.path.join(GOOD, "NOTICE"))
        code, out = run(*self.args())
        self.assertEqual(code, 1)
        self.assertIn("FAIL NOTICE: required item is missing", out)

    def test_unlisted_top_level(self):
        self.plant("psxrecomp/readme.md")
        self.plant("stray.dat")

    def test_size_sanity(self):
        put(GOOD, "MythologyKombat.exe", b"MZ" + b"\x00" * 1000)  # too small
        code, out = run(*self.args())
        self.assertEqual(code, 1)
        self.assertIn("FAIL MythologyKombat.exe: exe size", out)

    def test_planted_file_in_zip(self):
        z = os.path.join(SCRATCH, "bad.zip")
        with zipfile.ZipFile(z, "w") as zf:
            for dp, _, fn in os.walk(GOOD):
                for n in fn:
                    full = os.path.join(dp, n)
                    zf.write(full, os.path.relpath(full, GOOD).replace("\\", "/"))
            zf.writestr("extra/game.cue", "FILE x.bin BINARY\n")
        code, out = run("--zip", z, "--openbios-sha256", OPENBIOS_SHA)
        self.assertEqual(code, 1)
        self.assertIn("FAIL extra/game.cue", out)

    # ---- updater files and manifest.json (T3.21)
    def test_manifest_detects_modified_file(self):
        put(GOOD, "licenses/TinyCC-LICENSE.txt", b"tampered\n")   # no manifest rewrite
        code, out = run("--dir", GOOD, "--openbios-sha256", OPENBIOS_SHA)
        self.assertEqual(code, 1)
        self.assertIn("FAIL licenses/TinyCC-LICENSE.txt: ", out)
        self.assertIn("differs from manifest.json", out)

    def test_manifest_detects_unlisted_and_missing_file(self):
        put(GOOD, "assets/new.ttf", b"font2")
        os.remove(os.path.join(GOOD, "NOTICE"))
        code, out = run("--dir", GOOD, "--openbios-sha256", OPENBIOS_SHA)
        self.assertEqual(code, 1)
        self.assertIn("FAIL assets/new.ttf: file is not listed in manifest.json", out)
        self.assertIn("FAIL NOTICE: manifest.json lists a file that is not in the release", out)

    def test_manifest_size_mismatch(self):
        put(GOOD, "game_options.toml", b"# none, but longer\n")
        code, out = run("--dir", GOOD, "--openbios-sha256", OPENBIOS_SHA)
        self.assertEqual(code, 1)
        self.assertIn("FAIL game_options.toml: size differs from manifest.json", out)

    def test_manifest_missing_and_unreadable(self):
        os.remove(os.path.join(GOOD, "manifest.json"))
        code, out = run("--dir", GOOD, "--openbios-sha256", OPENBIOS_SHA)
        self.assertEqual(code, 1)
        self.assertIn("FAIL manifest.json: required item is missing", out)
        put(GOOD, "manifest.json", b"not json")
        code, out = run("--dir", GOOD, "--openbios-sha256", OPENBIOS_SHA)
        self.assertEqual(code, 1)
        self.assertIn("FAIL manifest.json: unreadable manifest", out)

    def test_updater_files_required(self):
        for name in ("update.cmd", "update.ps1"):
            with self.subTest(name=name):
                build_good(GOOD)
                os.remove(os.path.join(GOOD, name))
                write_manifest(GOOD)
                code, out = run("--dir", GOOD, "--openbios-sha256", OPENBIOS_SHA)
                self.assertEqual(code, 1)
                self.assertIn("FAIL %s: required item is missing" % name, out)

    def test_updater_must_be_ascii_and_free_of_local_paths(self):
        out = self.plant("update.ps1", "# caf\u00e9\n".encode("utf-8"))
        self.assertIn("updater file is not ASCII", out)
        out = self.plant("update.ps1", b"$x = 'C:\\Users\\someone\\x'\n")
        self.assertIn("local user path", out)

    def test_zip_with_manifest_passes_and_tampered_zip_fails(self):
        z = os.path.join(SCRATCH, "m.zip")
        with zipfile.ZipFile(z, "w") as zf:
            for dp, _, fn in os.walk(GOOD):
                for n in fn:
                    full = os.path.join(dp, n)
                    zf.write(full, "MythologyKombat-1.2.3/" + os.path.relpath(full, GOOD).replace("\\", "/"))
        code, out = run("--zip", z, "--openbios-sha256", OPENBIOS_SHA)
        self.assertEqual(code, 0, out)
        z2 = os.path.join(SCRATCH, "m2.zip")
        with zipfile.ZipFile(z, "r") as zin, zipfile.ZipFile(z2, "w") as zout:
            for i in zin.infolist():
                data = zin.read(i)
                if i.filename.endswith("/NOTICE"):
                    data = b"changed\n"
                zout.writestr(i.filename, data)
        code, out = run("--zip", z2, "--openbios-sha256", OPENBIOS_SHA)
        self.assertEqual(code, 1)
        self.assertIn("FAIL NOTICE: size differs from manifest.json", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
