"""Unit tests for tools/exe_data_check.py (synthetic data only).
Run: python -I tests/test_exe_data_check.py
"""
import contextlib
import io
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import exe_data_check as m  # noqa: E402

W, S, MIN = 32, 16, 64


def rnd(n, seed):
    r = random.Random(seed)
    return bytes(r.randrange(256) for _ in range(n))


class T(unittest.TestCase):
    def run_scan(self, disc, target):
        files = {"/F": disc}
        names, idx, st = m.build_index(files, W, S)
        return m.scan(target, names, files, idx, W, MIN), st

    def test_planted_random_run_found(self):
        disc = rnd(4096, 1)
        for start in (1000, 1001, 1007, 1015):  # every alignment vs. the stride
            target = rnd(3000, 2) + disc[start:start + 64] + rnd(3000, 3)
            runs, _ = self.run_scan(disc, target)
            self.assertTrue(any(r[0] == "/F" and r[3] >= 64 and r[1] <= 3000 and r[1] + r[3] >= 3064
                                for r in runs), (start, runs))

    def test_no_match_no_runs(self):
        runs, _ = self.run_scan(rnd(4096, 1), rnd(20000, 9))
        self.assertEqual(runs, [])

    def test_trivial_run_reported_uncovered(self):
        r = random.Random(5)
        run = bytes(r.choice(b"\x01\x02\x03\x04\x05\x06") for _ in range(64))  # <8 distinct -> trivial
        disc = rnd(512, 1) + run + rnd(512, 2)
        target = rnd(300, 3) + run + rnd(300, 4)
        runs, st = self.run_scan(disc, target)
        self.assertEqual(runs, [])  # blind spot: not found ...
        self.assertGreaterEqual(st["uncovered_disc_bytes"], W)  # ... but reported as uncovered
        self.assertGreater(st["uncovered_ranges"], 0)
        self.assertGreater(st["uncovered_disc_pct"], 0)

    def test_stats_report_counts(self):
        _, st = self.run_scan(rnd(2048, 1), b"")
        for k in ("trivial_skipped", "dropped_windows", "uncovered_disc_bytes", "uncovered_disc_pct"):
            self.assertIn(k, st)

    def test_no_raw_disc_bytes_in_output(self):
        disc = rnd(2048, 7)
        names, idx, st = m.build_index({"/F": disc}, W, S)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            print(st)
            print(m.summarize([("/F", 10, 0, 64)], None))
        text = out.getvalue()
        for i in range(0, len(disc) - 8, 8):
            self.assertNotIn(disc[i:i + 8].hex(), text)
        self.assertNotIn(repr(disc[:8]), text)


if __name__ == "__main__":
    unittest.main()
