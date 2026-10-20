#!/usr/bin/env python3
"""Replay infrastructure, step 1: cold-boot the debug build, play a frame-exact
button route, and record deterministic digests at fixed guest frames (stdlib only).

Run:  <RETRO_TOOLS_DIR>\\python\\python.exe -I tools\\run_boot_route.py [options]

  --route R             route file (default tests\\replays\\routes\\boot_to_menu.json)
  --out FILE            write the result JSON here (default work\\route\\result.json)
  --expect FILE         compare the result with committed expected digests; exit 1 on mismatch
  --record-expected F   write the result to F in the committed (path-free) form
  --checkpoints a,b,c   override the route file's checkpoint frames (experiments)
  --shots DIR           debug only: save a PNG at each checkpoint (DIR must be under work\\).
                        Screenshots are agent evidence and are NEVER committed.
  --runs N              up to N cold boots, merged (see below); fingerprints must agree across runs
  --no-ram              skip the paused RAM/VRAM hash capture (fingerprint digests only)
  --port N              debug port (default 4381; the Release game and smoke_boot use 4370)

What is launched: work\\build-dbg\\MythologyKombat.exe --headless (no window, no audio) with a
fresh memory card dir (work\\route_saves is deleted and recreated on every run = cold boot).
Only the child process started here is ever killed (pid in work\\route\\pid.txt).

Route file format (JSON; button names and exact guest frame numbers only):
  {"name": "...", "checkpoints": [600, 1800, ...],
   "steps": [{"frame": 3000, "buttons": ["START"], "hold": 4}, ...]}
A step presses the listed buttons on guest frames frame .. frame+hold-1 (frame = the debug
server's vblank counter, the number `frame` command reports). Steps must not overlap.
The tool turns this into input_route_append (one idle step per gap, one step per press) and
a single input_route_start at_frame=<first step frame>.

Digests recorded per checkpoint frame N (all deterministic functions of guest state):
  fingerprint  the `frame_fingerprint` ring entry for frame N. It is keyed by frame number, so it is
               exact no matter when the host reads it. cyc = guest cycle counter, wc/ws = main-RAM write
               count and order-independent hash of (addr,value) writes, mmio/mc, sp/sc = MMIO and
               scratchpad write hashes, qc = FMV-quiet writes. Judge columns: cyc wc ws mmio mc sp sc qc.
               wr and pc are ordered locators: recorded and reported, not a failure on their own.
  ram_sha256 / vram_sha256
               SHA-256 of main RAM 0x80000000-0x801FFFFF and of the whole 1024x512 16-bit VRAM,
               taken with host_pause. The host cannot stop the guest on an exact frame, so the hash is
               of the frame the pause landed on (paused_frame). `ram_exact` is true only when that is
               checkpoint frame N; --expect compares the RAM/VRAM hashes only for checkpoints that are
               exact in both result and expected file.

Exit codes: 0 ok (and match, with --expect), 1 mismatch or run failure, 2 usage/setup error.
"""
import argparse, hashlib, json, os, shutil, socket, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smoke_boot as sb  # noqa: E402  (Dbg client, kill_pid, pid_is_ours, DBG_EXE, DEF_DISC)

ROOT = sb.ROOT
WORK = os.path.join(ROOT, "work")
ROUTE_DIR = os.path.join(WORK, "route")
SAVES = os.path.join(WORK, "route_saves")
PIDFILE = os.path.join(ROUTE_DIR, "pid.txt")
DEF_ROUTE = os.path.join(ROOT, "tests", "replays", "routes", "boot_to_menu.json")

# PS1 digital pad word bit positions (0 = pressed in the word sent to the server).
BUTTON_BIT = {"SELECT": 0, "L3": 1, "R3": 2, "START": 3, "UP": 4, "RIGHT": 5, "DOWN": 6,
              "LEFT": 7, "L2": 8, "R2": 9, "L1": 10, "R1": 11, "TRIANGLE": 12,
              "CIRCLE": 13, "CROSS": 14, "SQUARE": 15}
JUDGE = ("cyc", "wc", "ws", "mmio", "mc", "sp", "sc", "qc")
LOCATOR = ("wr", "pc")


def log(m):
    print(m, flush=True)


class Fail(Exception):
    pass


def pad_word(names):
    w = 0xFFFF
    for n in names:
        if n.upper() not in BUTTON_BIT:
            raise Fail("unknown button %r (valid: %s)" % (n, ", ".join(BUTTON_BIT)))
        w &= ~(1 << BUTTON_BIT[n.upper()])
    return w


def load_route(path):
    raw = open(path, "rb").read()
    r = json.loads(raw)
    steps = sorted(r["steps"], key=lambda s: s["frame"])
    cmds, cursor = [], None
    for s in steps:
        f, hold = int(s["frame"]), int(s.get("hold", 1))
        if hold < 1 or f < 1:
            raise Fail("bad step %r" % s)
        if cursor is None:
            first = f
        else:
            if f < cursor:
                raise Fail("steps overlap at frame %d" % f)
            if f > cursor:
                cmds.append({"frames": f - cursor, "buttons": 0xFFFF})
        cmds.append({"frames": hold, "buttons": pad_word(s["buttons"])})
        cursor = f + hold
    if not cmds:
        raise Fail("route has no steps")
    return {"name": r.get("name", os.path.basename(path)), "checkpoints": r["checkpoints"],
            "first": first, "cmds": cmds, "sha256": hashlib.sha256(raw).hexdigest()}


def call_ok(dbg, cmd, **kw):
    try:
        r = dbg.call(cmd, **kw)
    except (OSError, ConnectionError, ValueError) as e:
        raise Fail("debug server unreachable during %s (game process gone?): %s" % (cmd, e))
    if not r.get("ok"):
        raise Fail("%s failed: %s" % (cmd, json.dumps(r)))
    return r


def read_fp(dbg, frame):
    r = call_ok(dbg, "frame_fingerprint", frame_lo=frame, frame_hi=frame, count=1)
    ent = [e for e in r["entries"] if e["frame"] == frame]
    if not ent:
        raise Fail("no fingerprint entry for frame %d" % frame)
    e = ent[0]
    return {k: e[k] for k in JUDGE + LOCATOR}


def hash_ram_vram(dbg):
    ram = call_ok(dbg, "read_ram", addr="0x80000000", len=0x200000, timeout=60)
    if ram["len"] != 0x200000:
        raise Fail("short RAM read: %d" % ram["len"])
    ram_h = hashlib.sha256(bytes.fromhex(ram["hex"])).hexdigest()
    vh = hashlib.sha256()
    for y in range(0, 512, 128):
        for x in range(0, 1024, 128):
            r = call_ok(dbg, "vram_peek", x=x, y=y, w=128, h=128)
            vh.update(bytes.fromhex(r["hex"]))
    return ram_h, vh.hexdigest()


def capture_checkpoint(dbg, n, want_ram, lead, shots):
    """Wait for guest frame n. Returns the checkpoint record."""
    rec = {"frame": n}
    if want_ram:
        # coarse wait, then a tight poll and host_pause as close to frame n as the host allows
        while True:
            f = call_ok(dbg, "frame")["frame"]
            if f >= n - 40:
                break
            time.sleep(max(0.0, min(0.2, (n - 40 - f) / 400.0)))
        while call_ok(dbg, "frame")["frame"] < n - lead:
            pass
        call_ok(dbg, "host_pause", on=1)
        time.sleep(0.15)  # let the pause settle; the frame counter must stop
        f1 = call_ok(dbg, "frame")["frame"]
        time.sleep(0.05)
        f2 = call_ok(dbg, "frame")["frame"]
        if f1 != f2:
            time.sleep(0.3)
            f1 = call_ok(dbg, "frame")["frame"]
        rec["paused_frame"] = f1
        rec["ram_exact"] = (f1 == n)
        rec["ram_sha256"], rec["vram_sha256"] = hash_ram_vram(dbg)
        # fingerprint for the checkpoint frame itself (exists once the frame has passed) and for the paused frame
        if f1 >= n:
            rec["fingerprint"] = read_fp(dbg, n)
        if shots:
            call_ok(dbg, "screenshot", path=os.path.join(shots, "cp%06d_paused%06d.png" % (n, f1)))
        call_ok(dbg, "host_pause", on=0)
        if f1 < n:
            while call_ok(dbg, "frame")["frame"] < n + 1:
                time.sleep(0.01)
            rec["fingerprint"] = read_fp(dbg, n)
    else:
        while call_ok(dbg, "frame")["frame"] < n + 1:
            time.sleep(0.01)
        rec["fingerprint"] = read_fp(dbg, n)
        if shots:
            call_ok(dbg, "screenshot", path=os.path.join(shots, "cp%06d.png" % n))
    return rec


def run(a):
    route = load_route(a.route)
    cps = sorted(int(x) for x in a.checkpoints.split(",")) if a.checkpoints else sorted(route["checkpoints"])
    exe, disc = os.path.abspath(a.exe), os.path.abspath(a.disc)
    for p, what in ((exe, "exe"), (disc, "disc image")):
        if not os.path.isfile(p):
            raise SystemExit("setup: %s not found: %s" % (what, p))
    if not sb.exe_has_debug_server(exe):
        raise SystemExit("setup: exe was built without PSX_DEBUG_TOOLS; use work\\build-dbg")
    if a.shots:
        a.shots = os.path.abspath(a.shots)
        if not a.shots.lower().startswith(WORK.lower() + os.sep):
            raise SystemExit("setup: --shots must be under work\\ (screenshots are never committed)")
        os.makedirs(a.shots, exist_ok=True)
    try:
        socket.create_connection(("127.0.0.1", a.port), timeout=1).close()
        raise SystemExit("setup: port %d already in use; pick another with --port" % a.port)
    except OSError:
        pass
    os.makedirs(ROUTE_DIR, exist_ok=True)
    if os.path.isfile(PIDFILE):
        try:
            old = int(open(PIDFILE).read().strip())
            if sb.pid_is_ours(old):
                raise SystemExit("setup: stale run pid %d still alive; kill it (taskkill /F /PID %d) first" % (old, old))
        except ValueError:
            pass
    # cold boot: fresh memory card directory every run
    shutil.rmtree(SAVES, ignore_errors=True)
    os.makedirs(SAVES, exist_ok=True)

    exe_dir = os.path.dirname(exe)
    cmd = [exe, "--disc", disc, "--game", os.path.join(exe_dir, "game.toml"), "--no-launcher",
           "--headless", "--debug-port", str(a.port), "--memcard-dir", SAVES]
    env = dict(os.environ)
    env["PSX_DEBUG_FMV_QUIET"] = "0"  # upstream rule for identity runs (TCP_COMMANDS.md, frame_fingerprint)
    lf = open(os.path.join(ROUTE_DIR, "run.log"), "wb")
    t0 = time.time()
    proc = subprocess.Popen(cmd, cwd=exe_dir, stdout=lf, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, env=env)
    open(PIDFILE, "w").write(str(proc.pid))
    dbg = sb.Dbg(a.port)
    result = None
    try:
        while True:
            if proc.poll() is not None:
                raise Fail("game exited during startup, code %s" % proc.returncode)
            try:
                dbg.connect()
                break
            except OSError:
                if time.time() - t0 > 60:
                    raise Fail("debug port never opened")
                time.sleep(0.1)
        call_ok(dbg, "input_route_clear")
        for c in route["cmds"]:
            call_ok(dbg, "input_route_append", frames=c["frames"], buttons=c["buttons"])
        r = call_ok(dbg, "input_route_start", at_frame=route["first"])
        cur = call_ok(dbg, "frame")["frame"]
        if r.get("start_frame") != route["first"]:
            raise Fail("route started too late: first step frame %d but server frame was already %d "
                       "(server replied start_frame=%s)" % (route["first"], cur, r.get("start_frame")))
        log("route %s queued: %d steps, first step at frame %d (server frame %d)"
            % (route["name"], len(route["cmds"]), route["first"], cur))
        cp_recs = []
        for n in cps:
            if proc.poll() is not None:
                raise Fail("game died before checkpoint %d (exit %s)" % (n, proc.returncode))
            rec = capture_checkpoint(dbg, n, not a.no_ram, a.lead, a.shots)
            cp_recs.append(rec)
            log("checkpoint %6d  paused_frame=%s exact=%s  ws=%s ram=%s" % (
                n, rec.get("paused_frame"), rec.get("ram_exact"),
                rec["fingerprint"]["ws"], (rec.get("ram_sha256") or "-")[:12]))
        last = call_ok(dbg, "frame")
        ds = call_ok(dbg, "dispatch_stats")
        st = call_ok(dbg, "input_route_status")
        result = {
            "schema": 1,
            "route_name": route["name"],
            "route_sha256": route["sha256"],
            "exe_sha256": hashlib.sha256(open(exe, "rb").read()).hexdigest(),
            "dispatch_miss_total": ds.get("miss_total"),
            "segment_miss_total": ds.get("segment_miss_total"),
            "route_finished": not st.get("active"),
            "checkpoints": cp_recs,
        }
        log("run took %.1f s wall clock, final guest frame %s" % (time.time() - t0, last.get("frame")))
    finally:
        try:
            dbg.call("quit")
        except Exception:
            pass
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            sb.kill_pid(proc.pid)  # our own child only
        lf.close()
        try:
            os.remove(PIDFILE)
        except OSError:
            pass
    return result


def merge(res, cur):
    """Fold a further cold-boot run into res. Fingerprints must be identical in every judge column
    (this is the cross-run determinism check); an exact RAM/VRAM hash fills a gap or must agree."""
    if cur["route_sha256"] != res["route_sha256"] or cur["exe_sha256"] != res["exe_sha256"]:
        raise Fail("runs used different route or exe")
    for k in ("dispatch_miss_total", "segment_miss_total"):
        if cur[k] != res[k]:
            raise Fail("%s differs between runs: %s vs %s" % (k, res[k], cur[k]))
    byf = {c["frame"]: c for c in res["checkpoints"]}
    for c in cur["checkpoints"]:
        b = byf[c["frame"]]
        for k in JUDGE:
            if b["fingerprint"][k] != c["fingerprint"][k]:
                raise Fail("NON-DETERMINISTIC: frame %d fingerprint.%s differs between cold-boot runs: %s vs %s"
                           % (c["frame"], k, b["fingerprint"][k], c["fingerprint"][k]))
        for k in LOCATOR:
            if b["fingerprint"][k] != c["fingerprint"][k]:
                log("warn: frame %d locator %s differs between runs" % (c["frame"], k))
        if c.get("ram_exact"):
            if b.get("ram_exact"):
                if (b["ram_sha256"], b["vram_sha256"]) != (c["ram_sha256"], c["vram_sha256"]):
                    raise Fail("NON-DETERMINISTIC: frame %d RAM/VRAM hash differs between cold-boot runs" % c["frame"])
            else:
                for k in ("paused_frame", "ram_exact", "ram_sha256", "vram_sha256"):
                    b[k] = c[k]


def compare(res, exp):
    """Returns (errors, warnings)."""
    err, warn = [], []
    for k in ("route_sha256", "dispatch_miss_total", "segment_miss_total"):
        if res.get(k) != exp.get(k):
            err.append("%s: result %r != expected %r" % (k, res.get(k), exp.get(k)))
    if res.get("exe_sha256") != exp.get("exe_sha256"):
        warn.append("exe_sha256 differs (different build than the one expected was recorded with)")
    rc = {c["frame"]: c for c in res["checkpoints"]}
    ec = {c["frame"]: c for c in exp["checkpoints"]}
    if sorted(rc) != sorted(ec):
        err.append("checkpoint frames differ: result %s vs expected %s" % (sorted(rc), sorted(ec)))
    for n in sorted(set(rc) & set(ec)):
        r, e = rc[n], ec[n]
        for k in JUDGE:
            if r["fingerprint"][k] != e["fingerprint"][k]:
                err.append("frame %d fingerprint.%s: %s != expected %s" % (n, k, r["fingerprint"][k], e["fingerprint"][k]))
        for k in LOCATOR:
            if r["fingerprint"][k] != e["fingerprint"][k]:
                warn.append("frame %d fingerprint.%s (locator) differs" % (n, k))
        if r.get("ram_exact") and e.get("ram_exact"):
            for k in ("ram_sha256", "vram_sha256"):
                if r[k] != e[k]:
                    err.append("frame %d %s: %s != expected %s" % (n, k, r[k][:16], e[k][:16]))
        elif "ram_sha256" in r or "ram_sha256" in e:
            warn.append("frame %d RAM/VRAM hash not compared (paused on frame %s, expected paused on %s)"
                        % (n, r.get("paused_frame"), e.get("paused_frame")))
    return err, warn


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--route", default=DEF_ROUTE)
    ap.add_argument("--out", default=os.path.join(ROUTE_DIR, "result.json"))
    ap.add_argument("--expect")
    ap.add_argument("--record-expected")
    ap.add_argument("--checkpoints")
    ap.add_argument("--shots")
    ap.add_argument("--no-ram", action="store_true")
    ap.add_argument("--runs", type=int, default=1,
                    help="up to N cold-boot runs; stop early once every checkpoint has an exact RAM/VRAM hash; "
                         "digests of all runs must agree")
    ap.add_argument("--lead", type=int, default=1, help="frames before a checkpoint at which host_pause is sent")
    ap.add_argument("--port", type=int, default=4381)
    ap.add_argument("--exe", default=sb.DBG_EXE)
    ap.add_argument("--disc", default=sb.DEF_DISC)
    a = ap.parse_args()
    res = None
    try:
        for i in range(1, a.runs + 1):
            if a.runs > 1:
                log("=== cold-boot run %d of up to %d ===" % (i, a.runs))
            cur = run(a)
            if res is None:
                res = cur
            else:
                merge(res, cur)
            missing = [c["frame"] for c in res["checkpoints"] if not a.no_ram and not c.get("ram_exact")]
            if not missing:
                break
            log("checkpoints without an exact RAM/VRAM hash: %s" % missing)
        res["runs"] = i
    except Fail as e:
        log("RESULT: FAIL (%s)" % e)
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1, sort_keys=True)
    log("result written: %s" % a.out)
    if a.record_expected:
        os.makedirs(os.path.dirname(os.path.abspath(a.record_expected)), exist_ok=True)
        json.dump(res, open(a.record_expected, "w"), indent=1, sort_keys=True)
        open(a.record_expected, "a").write("\n")
        log("expected digests recorded: %s" % a.record_expected)
    if a.expect:
        exp = json.load(open(a.expect))
        err, warn = compare(res, exp)
        for w in warn:
            log("warn: " + w)
        if err:
            log("RESULT: MISMATCH (%d differences)" % len(err))
            for e in err:
                log("  - " + e)
            return 1
        log("RESULT: MATCH (%d checkpoints)" % len(res["checkpoints"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
