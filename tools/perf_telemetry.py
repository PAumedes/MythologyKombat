"""Vblank interval percentiles from playtest diagnostics telemetry folders (T3.6; was work/scratch/tele.py).
Usage: python -I tools/perf_telemetry.py <session-dir> [<session-dir> ...]
Reads <dir>/telemetry.csv (host_interval_us = host time between guest VBlanks; rows 0 and 1 skipped).
Per group (all / cd_xa != 0 = movie audio / cd_xa == 0) prints n, interval ms p50 p90 p99 p99.9 max,
the count above 20 ms and above 33 ms, and the share above 33 ms. Stdlib only, deterministic."""
import csv, sys, os, collections

def pct(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(len(v) * p))]

def main(dirs):
    for d in dirs:
        rows = list(csv.DictReader(open(os.path.join(d, 'telemetry.csv'), newline='')))
        print('==', d, len(rows), 'rows')
        for k in ('composed_internal_scale', 'video_renderer', 'video_resolution_preset'):
            if rows and k in rows[0]:
                print(' ', k, collections.Counter(r[k] for r in rows).most_common(4))
        for lab, sel in (('all', lambda r: True), ('xa', lambda r: r['cd_xa'] != '0'), ('noxa', lambda r: r['cd_xa'] == '0')):
            v = [int(r['host_interval_us']) / 1000 for r in rows[2:] if sel(r)]
            if not v: continue
            o33 = sum(x > 33 for x in v)
            print(' ', lab, len(v), 'interval ms p50 %.2f p90 %.2f p99 %.2f p99.9 %.2f max %.1f  >20ms:%d >33ms:%d (%.2f%% above 33 ms)'
                  % (pct(v, .5), pct(v, .9), pct(v, .99), pct(v, .999), max(v), sum(x > 20 for x in v), o33, 100.0 * o33 / len(v)))

if __name__ == '__main__':
    if len(sys.argv) < 2: sys.exit(__doc__)
    main(sys.argv[1:])
