"""Summarize work/perf/run_<X>.log(+.err.log) PERF_DIAG cadence lines. Usage: python -I tools/perf_summarize.py A B D [--series]
Prints the run_<X>.meta.txt header (video settings, power plan, GPU, exe SHA, pins) and the settings the game itself logged, so runs are comparable (T3.6).
FMV window = first run of >=3 consecutive samples (after sample 1) with guest work >= 500 ms/s, until 3 consecutive below."""
import re, sys, os, statistics as st
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RX = re.compile(r'cadence: guest=([\d.]+) Hz, spu=([\d.]+) Hz, audio_fill=([\d.]+) ms, underruns=\+(\d+), overflows=\+(\d+).*?work guest=([\d.]+) pacer=([\d.]+).*?overlay native=\+(\d+) interp=\+(\d+)')
NAMES = ['guest', 'spu', 'fill', 'under', 'ovf', 'workG', 'pacer', 'nat', 'interp']
SHOW = ['guest', 'spu', 'fill', 'under', 'workG', 'pacer', 'interp']
def load(n):
    rows = []
    for suf in ('.log', '.err.log'):
        p = os.path.join(ROOT, 'work', 'perf', f'run_{n}{suf}')
        if not os.path.exists(p): continue
        for l in open(p, errors='replace').read().splitlines():
            m = RX.search(l)
            if m: rows.append([float(x) for x in m.groups()])
    return rows
def fmv_window(r):
    a = None
    for i in range(1, len(r) - 2):
        if all(x[5] >= 500 for x in r[i:i+3]): a = i; break
    if a is None: return None
    b = len(r)
    for j in range(a, len(r) - 2):
        if all(x[5] < 500 for x in r[j:j+3]): b = j; break
    return a, b
LOGKEYS = ('internal resolution', 'supersampling', 'sync-to-host', 'vsync', 'OpenGL context created', 'renderer =')
def header(n):
    p = os.path.join(ROOT, 'work', 'perf', f'run_{n}.meta.txt')
    if os.path.exists(p):
        print(' meta (' + os.path.relpath(p, ROOT) + '):')
        for l in open(p, errors='replace').read().splitlines(): print('   ' + l)
    else:
        print(' meta: MISSING (run predates T3.6 or was not made with perf_run.ps1); settings unknown')
    seen = []
    p = os.path.join(ROOT, 'work', 'perf', f'run_{n}.log')
    if os.path.exists(p):
        for l in open(p, errors='replace').read().splitlines():
            if any(k in l for k in LOGKEYS) and l not in seen: seen.append(l)
    if seen:
        print(' as logged by the game:')
        for l in seen: print('   ' + l.strip())
def mmm(v): return '%.1f/%.1f/%.1f' % (min(v), st.median(v), max(v))
args = [x for x in sys.argv[1:] if not x.startswith('--')]
for n in args:
    r = load(n)
    print(f'== run {n}: {len(r)} samples')
    header(n)
    if '--series' in sys.argv: print(' guestHz:', ' '.join('%d' % x[0] for x in r))
    w = fmv_window(r)
    if not w: print(' no FMV window found'); continue
    a, b = w
    phases = [('pre-FMV (samples 2..%d)' % a, r[1:a]), ('FMV (samples %d..%d)' % (a + 1, b), r[a:b])]
    for lab, p in phases:
        if not p: continue
        frames = sum(x[0] for x in p)
        print(f' {lab}: wall={len(p)} s, guest frames~{frames:.0f} (~{frames/60:.0f} s guest time at 60 Hz)')
        for nm in SHOW:
            print(f'   {nm:6s} min/med/max {mmm([x[NAMES.index(nm)] for x in p])}')
    post = r[b:]
    odd = [(b + i + 1, x[0], int(x[3])) for i, x in enumerate(post) if x[0] < 40]
    if odd: print(' post-FMV samples with guest<40 Hz (sample, Hz, underruns):', odd)
