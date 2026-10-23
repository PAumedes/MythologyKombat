"""Summarize perf_ab results (T3.7/T3.8): python -I tools/perf_ab_summary.py [prefix]  (stdlib only).
Reads work/perf_ab/results/<GPU>_<config>_r<N>/telemetry.csv. Skips the first 8 s of host time (boot),
then per run: avg fps = 1e6 / mean(host_interval_us), p50/p90/p99 of the interval in ms, share above 33 ms,
for all rows and for non-movie rows (cd_xa == 0). Per config prints the median over rounds of each metric
plus the per-round values of p99 (so spread is visible)."""
import csv, os, sys, re, statistics as st, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'work', 'perf_ab', 'results')
def pct(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(len(v) * p))]
def stats(v):
    if len(v) < 20: return None
    return dict(n=len(v), fps=1000.0 / (sum(v) / len(v)), p50=pct(v, .5), p90=pct(v, .9), p99=pct(v, .99), mx=max(v),
                o33=100.0 * sum(x > 33 for x in v) / len(v))
def run(d):
    rows = list(csv.DictReader(open(os.path.join(RES, d, 'telemetry.csv'), newline='')))
    t = [r for r in rows[2:] if int(r['host_elapsed_us']) >= 8_000_000]
    meta = open(os.path.join(RES, d, 'meta.txt'), errors='replace').read()
    gpu = ('MX150' if 'MX150' in meta else 'Intel HD630' if 'Intel' in meta else '?')
    all_ = [int(r['host_interval_us']) / 1000 for r in t]
    non = [int(r['host_interval_us']) / 1000 for r in t if r['cd_xa'] == '0']
    dur = int(rows[-1]['host_elapsed_us']) / 1e6
    return gpu, dur, stats(all_), stats(non), collections.Counter(r['composed_internal_scale'] for r in t).most_common(1)[0][0]
pre = sys.argv[1] if len(sys.argv) > 1 else ''
groups = collections.OrderedDict()
for d in sorted(os.listdir(RES)):
    m = re.match(r'(.+)_r(\d+)$', d)
    if m and d.startswith(pre) and os.path.exists(os.path.join(RES, d, 'telemetry.csv')):
        groups.setdefault(m.group(1), []).append(d)
print('config | GPU(from log) | runs | scale | avg fps (all) | p50 | p90 | p99 ms (all) | p99 per run | >33ms% all | >33ms% non-movie | p99 non-movie | max ms')
for g, ds in groups.items():
    R = [run(d) for d in ds]
    A = [r[2] for r in R if r[2]]; N = [r[3] for r in R if r[3]]
    med = lambda L, k: st.median(x[k] for x in L) if L else float('nan')
    print('%s | %s | %d | %sx | %.1f | %.1f | %.1f | %.1f | %s | %.2f | %.2f | %.1f | %.0f' % (
        g, R[0][0], len(R), R[0][4], med(A, 'fps'), med(A, 'p50'), med(A, 'p90'), med(A, 'p99'),
        '/'.join('%.1f' % x['p99'] for x in A), med(A, 'o33'), med(N, 'o33'), med(N, 'p99'), max(x['mx'] for x in A)))
