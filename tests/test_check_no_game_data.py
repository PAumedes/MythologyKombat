"""Negative controls for tools/check_no_game_data.py (T3.16).

Run: python tests/test_check_no_game_data.py
Plants forbidden files in throwaway git repos under work/ (git-ignored); the
real repo index is never touched.
"""
import os
import shutil
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(ROOT, "tools", "check_no_game_data.py")
SCRATCH = os.path.join(ROOT, "work", "guard_test")


def rmtree(p):
    def fix(fn, path, _):
        os.chmod(path, 0o700)
        fn(path)
    if os.path.isdir(p):
        shutil.rmtree(p, onerror=fix)


def run_guard(*args):
    r = subprocess.run([sys.executable, "-I", GUARD, *args], capture_output=True, text=True)
    return r.returncode, r.stdout


def git(repo, *a):
    subprocess.run(["git", "-C", repo, *a], check=True, capture_output=True)


class Guard(unittest.TestCase):
    def setUp(self):
        rmtree(SCRATCH)
        os.makedirs(SCRATCH)
        git(SCRATCH, "init", "-q")
        git(SCRATCH, "config", "user.email", "t@t")
        git(SCRATCH, "config", "user.name", "t")
        self.put("docs/ok.md", b"fine\n")
        self.put("seeds/ghidra_funcs.txt", b"80010000 main\n")
        self.put("aot/overlays.json", b"{}\n")

    def tearDown(self):
        rmtree(SCRATCH)

    def put(self, rel, data):
        p = os.path.join(SCRATCH, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)
        git(SCRATCH, "add", "-f", rel)

    def expect_fail(self, rel, data, reason=None):
        self.put(rel, data)
        code, out = run_guard("--repo", SCRATCH)
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL " + rel + ":", out)
        if reason:
            self.assertIn(reason, out)
        self.assertEqual(run_guard("--repo", SCRATCH), (code, out))  # deterministic

    def test_clean(self):
        code, out = run_guard("--repo", SCRATCH)
        self.assertEqual(code, 0, out)

    def test_real_repo_clean(self):
        code, out = run_guard()
        self.assertEqual(code, 0, out)

    def test_bin(self): self.expect_fail("disc/game.bin", b"x", ".bin")
    def test_cue(self): self.expect_fail("game.cue", b"x")
    def test_mcd(self): self.expect_fail("saves/card.mcd", b"x", ".mcd")
    def test_exe_ext(self): self.expect_fail("tool.exe", b"MZ")
    def test_generated(self): self.expect_fail("generated/x.c", b"int x;", "generated")
    def test_ps1_game(self): self.expect_fail("ps1_game/readme.txt", b"x", "forbidden directory")
    def test_work(self): self.expect_fail("work/n.txt", b"x", "forbidden directory")
    def test_captures(self): self.expect_fail("aot/overlay_captures.json", b"{}", "overlay_captures")
    def test_upper_ext(self): self.expect_fail("A/SLUS_000.01.OVR", b"x", ".ovr")

    def test_psx_magic_renamed(self):
        self.expect_fail("data/innocent.txt", b"PS-X EXE" + b"\0" * 2040, "PS-X EXE")

    def test_cd_sector(self):
        self.expect_fail("data/dump.dat", b"\x00" + b"\xff" * 10 + b"\x00" + b"\0" * 2340, "CD sector")

    def test_large_file(self):
        self.put("data/big.dat", b"\x5a" * (3 * 1024 * 1024))
        code, out = run_guard("--repo", SCRATCH, "--max-mb", "2")
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL data/big.dat: file larger than 2 MB", out)

    def test_staged_header_differs_from_worktree(self):
        self.put("m.txt", b"PS-X EXE\0\0\0\0")
        with open(os.path.join(SCRATCH, "m.txt"), "wb") as f:
            f.write(b"benign\n")
        code, out = run_guard("--repo", SCRATCH)
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL m.txt: PS-X EXE header", out)

    def test_staged_size_differs_from_worktree(self):
        self.put("big.dat", b"\0" * 3000000)
        with open(os.path.join(SCRATCH, "big.dat"), "wb") as f:
            f.write(b"s\n")
        code, out = run_guard("--repo", SCRATCH, "--max-mb", "1")
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL big.dat: file larger than 1 MB", out)

    def test_nested_prefixes(self):
        self.expect_fail("x/ps1_game/a.txt", b"x", "forbidden directory")
        self.expect_fail("y/work/a.txt", b"x", "forbidden directory")

    def test_dot_slash_list(self):
        lst = os.path.join(SCRATCH, "l.txt")
        with open(lst, "w") as f:
            f.write("./.hidden/a.bin\n")
        code, out = run_guard("--list", lst)
        self.assertIn("FAIL .hidden/a.bin:", out)

    def test_list_mode(self):
        os.makedirs(os.path.join(SCRATCH, "stage"))
        with open(os.path.join(SCRATCH, "stage", "a.txt"), "wb") as f:
            f.write(b"PS-X EXE")
        lst = os.path.join(SCRATCH, "list.txt")
        with open(lst, "w") as f:
            f.write("stage/a.txt\nstage/b.bin\n")
        code, out = run_guard("--list", lst, "--root", SCRATCH)
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL stage/a.txt: PS-X EXE header", out)
        self.assertIn("FAIL stage/b.bin:", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
