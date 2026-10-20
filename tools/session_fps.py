"""Guest vblank rate from a playtest diagnostics telemetry.csv (T2.20 / T2.10 facts).
Usage: python tools/session_fps.py <session-dir> [...]
Uses host_interval_us (host time between guest VBlanks; first row is 0 and skipped).
Splits samples by cd_xa: rows where cd_xa != 0 vs == 0. Reports count, mean Hz (n / sum of intervals) and median Hz.
Stdlib only. Prints measurements only; it does not identify which movie plays."""
import csv, statistics, sys, os
def stats(iv):
    if not iv: return "n=0"
    hz = sorted(1e6 / x for x in iv if x > 0)
    return "n=%d mean=%.1f Hz median=%.1f Hz p5=%.1f Hz" % (len(iv), len(iv) * 1e6 / sum(iv), statistics.median(hz), hz[len(hz) // 20])
for d in sys.argv[1:]:
    rows = list(csv.DictReader(open(os.path.join(d, "telemetry.csv"), newline="")))[1:]
    xa = [int(r["host_interval_us"]) for r in rows if int(r["cd_xa"])]
    non = [int(r["host_interval_us"]) for r in rows if not int(r["cd_xa"])]
    print(os.path.basename(d.rstrip("/\\")))
    print("  cd_xa != 0 :", stats(xa))
    print("  cd_xa == 0 :", stats(non))
    print("  all        :", stats(xa + non))
