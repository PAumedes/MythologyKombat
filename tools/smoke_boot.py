#!/usr/bin/env python3
"""Headless smoke test for build\\MythologyKombat.exe (stdlib only).

Run:  <RETRO_TOOLS_DIR>\\python\\python.exe -I tools\\smoke_boot.py [--seconds 60]

Launches the exe with --headless (no window, no audio), talks to the TCP debug
server (JSON, one object per line: {"id":N,"cmd":"ping"} -> {"id":N,"ok":true,"frame":F,...}),
polls the frame counter, saves PNG screenshots to work\\shots\\, and quits.

PASS (exit 0) iff: process alive the whole run, frame counter strictly increases
between samples, and no psx_crash.txt appears (cwd, exe dir, memcard dir, repo root).
Exit codes: 0 pass, 1 fail, 2 usage/setup error.

--kill              kill a stale instance recorded in work\\smoke\\pid.txt, then exit.
--self-test-kill    negative test: the script kills the child at 5 s.
"""
import argparse, json, os, socket, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMOKE = os.path.join(ROOT, "work", "smoke")
SHOTS = os.path.join(ROOT, "work", "shots")
PIDFILE = os.path.join(SMOKE, "pid.txt")
DBG_EXE = os.path.join(ROOT, "work", "build-dbg", "MythologyKombat.exe")
REL_EXE = os.path.join(ROOT, "build", "MythologyKombat.exe")
# Resolution order: --exe, env SMOKE_EXE, work/build-dbg (has the TCP debug server), then build/.
DEF_EXE = os.environ.get("SMOKE_EXE") or (DBG_EXE if os.path.isfile(DBG_EXE) else REL_EXE)
DEF_DISC = os.path.join(ROOT, "ps1_game", "Mortal Kombat Mythologies - Sub-Zero.cue")


def log(m):
    print(m, flush=True)


def kill_pid(pid):
    # taskkill /T also removes child processes.
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def pid_is_ours(pid):
    out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    return "MythologyKombat.exe" in out


def do_kill_switch():
    if not os.path.isfile(PIDFILE):
        log("kill: no pid file (%s); nothing to do" % PIDFILE)
        return 0
    try:
        pid = int(open(PIDFILE).read().strip())
    except ValueError:
        log("kill: bad pid file; removing")
        os.remove(PIDFILE)
        return 0
    if pid_is_ours(pid):
        kill_pid(pid)
        log("kill: killed stale MythologyKombat.exe pid %d" % pid)
    else:
        log("kill: pid %d is not a running MythologyKombat.exe; not touching it" % pid)
    os.remove(PIDFILE)
    return 0


class Dbg:
    """The server answers ONE request per TCP connection and then closes it,
    so every call opens a fresh connection."""

    def __init__(self, port):
        self.port = port
        self.n = 0
        self.s = None  # kept for 'is the server reachable' bookkeeping

    def connect(self):
        # probe only (the port is open)
        socket.create_connection(("127.0.0.1", self.port), timeout=3).close()
        self.s = True

    def close(self):
        self.s = None

    def call(self, cmd, timeout=15, **kw):
        self.n += 1
        req = dict(kw, id=self.n, cmd=cmd)
        c = socket.create_connection(("127.0.0.1", self.port), timeout=3)
        try:
            c.settimeout(timeout)
            c.sendall(json.dumps(req).encode() + bytes([10]))
            buf = b""
            while bytes([10]) not in buf:
                d = c.recv(65536)
                if not d:
                    break
                buf += d
        finally:
            c.close()
        if not buf.strip():
            raise ConnectionError("empty reply to %s" % cmd)
        return json.loads(buf.split(bytes([10]), 1)[0])


def exe_has_debug_server(exe):
    """False only when the exe's own CMakeCache.txt says PSX_DEBUG_TOOLS=OFF."""
    try:
        for l in open(os.path.join(os.path.dirname(exe), "CMakeCache.txt"), errors="replace"):
            if l.startswith("PSX_DEBUG_TOOLS:"):
                return l.strip().endswith("=ON")
    except OSError:
        pass
    return True


def crash_files(extra_dirs):
    seen = {}
    for d in extra_dirs:
        p = os.path.join(d, "psx_crash.txt")
        if os.path.isfile(p):
            seen[os.path.abspath(p)] = os.path.getmtime(p)
    return seen


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--port", type=int, default=4370)
    ap.add_argument("--startup-wait", type=float, default=30,
                    help="seconds to wait for the debug port before failing (default 30)")
    ap.add_argument("--disc", default=DEF_DISC)
    ap.add_argument("--exe", default=DEF_EXE)
    ap.add_argument("--renderer", default=None, choices=["software", "opengl", "vulkan"])
    ap.add_argument("--kill", action="store_true", help="kill stale instance from pid file and exit")
    ap.add_argument("--self-test-kill", action="store_true", help="kill the child at 5 s (negative test)")
    a = ap.parse_args()

    os.makedirs(SMOKE, exist_ok=True)
    os.makedirs(SHOTS, exist_ok=True)
    if a.kill:
        return do_kill_switch()

    exe = os.path.abspath(a.exe)
    disc = os.path.abspath(a.disc)
    if not os.path.isfile(exe):
        log("FAIL(setup): exe not found: %s" % exe)
        return 2
    if not os.path.isfile(disc):
        log("FAIL(setup): disc image not found: %s" % disc)
        return 2
    # stale instance guard
    if os.path.isfile(PIDFILE):
        try:
            old = int(open(PIDFILE).read().strip())
            if pid_is_ours(old):
                log("FAIL(setup): stale instance pid %d running; run with --kill first" % old)
                return 2
        except ValueError:
            pass
        os.remove(PIDFILE)
    # refuse if port already in use (could be another program)
    try:
        socket.create_connection(("127.0.0.1", a.port), timeout=1).close()
        log("FAIL(setup): port %d already in use; pick another with --port" % a.port)
        return 2
    except OSError:
        pass

    exe_dir = os.path.dirname(exe)
    cwd = exe_dir  # game.toml, assets and input.ini live next to the exe
    memdir = os.path.join(ROOT, "work", "smoke_saves")
    os.makedirs(memdir, exist_ok=True)
    import hashlib
    h = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    log("exe: %s" % exe)
    log("exe sha256: %s" % h)
    cmd = [exe, "--disc", disc, "--game", os.path.join(exe_dir, "game.toml"),
           "--no-launcher", "--headless", "--debug-port", str(a.port), "--memcard-dir", memdir]
    if a.renderer:
        cmd += ["--renderer", a.renderer]
    crash_dirs = [cwd, exe_dir, memdir, ROOT]
    before = crash_files(crash_dirs)
    runlog = os.path.join(SMOKE, "run.log")
    lf = open(runlog, "wb")
    log("launch: " + " ".join('"%s"' % c if " " in c else c for c in cmd))
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=lf, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL)
    open(PIDFILE, "w").write(str(proc.pid))
    log("pid %d, log %s" % (proc.pid, runlog))

    dbg = Dbg(a.port)
    fails = []
    frames = []
    shots = []
    end_ok = False
    shot_status = {}
    t0 = time.time()
    try:
        # 1. wait for debug port
        connected = False
        while time.time() - t0 < a.startup_wait:
            if proc.poll() is not None:
                fails.append("process exited during startup, code %s" % proc.returncode)
                break
            try:
                dbg.connect()
                connected = True
                break
            except OSError:
                if time.time() - t0 > 8 and not exe_has_debug_server(exe):
                    break
                time.sleep(0.25)
        if connected:
            r = dbg.call("ping")
            log("ping -> %s" % json.dumps(r))
            if not r.get("ok"):
                fails.append("ping not ok")
        elif not fails:
            fails.append("debug port %d never opened in %.0f s while the process stayed alive. "
                         "The exe was probably built without PSX_DEBUG_TOOLS (Release default turns the "
                         "TCP debug server off); rebuild with -DPSX_DEBUG_TOOLS=ON or pass --exe to such a build"
                         % (a.port, time.time() - t0))

        if not fails:
            tstart = time.time()
            shot_marks = [0.0, 10.0, 30.0]
            shot_done = set()
            killed = False
            last_poll = 0
            while True:
                el = time.time() - tstart
                if proc.poll() is not None:
                    fails.append("process died at %.1f s, exit code %s" % (el, proc.returncode))
                    break
                if a.self_test_kill and not killed and el >= 5:
                    log("self-test-kill: killing child at %.1f s" % el)
                    kill_pid(proc.pid)
                    killed = True
                    time.sleep(0.5)
                    continue
                if el >= a.seconds:
                    break
                try:
                    if time.time() - last_poll >= 1.0:
                        last_poll = time.time()
                        f = dbg.call("frame")
                        fr = f.get("frame")
                        if fr is None:
                            fails.append("frame reply has no 'frame': %s" % json.dumps(f))
                            break
                        frames.append((round(el, 1), fr))
                    for m in shot_marks:
                        if el >= m and m not in shot_done and m <= a.seconds:
                            p = os.path.join(SHOTS, "smoke_t%02d.png" % int(m))
                            r = dbg.call("screenshot", path=p)
                            if r.get("ok"):
                                shots.append(p)
                                shot_done.add(m)
                                shot_status[m] = "ok"
                                log("t=%.1f s frame=%s screenshot -> %s (%sx%s)" %
                                    (el, frames[-1][1] if frames else "?", p, r.get("width"), r.get("height")))
                            else:
                                # e.g. "display disabled" before the first frame is shown: retry for 8 s
                                if el > m + 8:
                                    shot_done.add(m)
                                    shot_status[m] = "FAILED (%s)" % r.get("error")
                                    log("screenshot t=%d failed: %s" % (int(m), json.dumps(r)))
                except (OSError, ConnectionError, ValueError) as e:
                    if proc.poll() is not None:
                        continue  # loop top reports the death
                    fails.append("debug server error at %.1f s: %s" % (el, e))
                    break
                time.sleep(0.1)
            # end screenshot
            if not fails:
                try:
                    p = os.path.join(SHOTS, "smoke_end.png")
                    r = dbg.call("screenshot", path=p)
                    end_ok = bool(r.get("ok"))
                    if r.get("ok"):
                        shots.append(p)
                        log("end screenshot -> %s (%sx%s)" % (p, r.get("width"), r.get("height")))
                    f = dbg.call("frame")
                    frames.append((round(time.time() - tstart, 1), f.get("frame")))
                except (OSError, ConnectionError, ValueError) as e:
                    fails.append("final query failed: %s" % e)
    except KeyboardInterrupt:
        fails.append("interrupted by user")
    finally:
        # graceful quit, then terminate, then kill
        try:
            if dbg.s and proc.poll() is None:
                try:
                    dbg.call("quit")
                except Exception:
                    pass
        except Exception:
            pass
        dbg.close()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                kill_pid(proc.pid)
                proc.kill()
                proc.wait(timeout=5)
        lf.close()
        try:
            os.remove(PIDFILE)
        except OSError:
            pass

    # evaluate
    if frames:
        log("frame samples (t_s, frame): " + ", ".join("%s:%s" % x for x in frames[:3]) +
            " ... " + ", ".join("%s:%s" % x for x in frames[-3:]))
        log("frame count first=%s last=%s" % (frames[0][1], frames[-1][1]))
        vals = [v for _, v in frames]
        if not all(b > a_ for a_, b in zip(vals, vals[1:])):
            stalls = [(frames[i][0], frames[i + 1][0], vals[i]) for i in range(len(vals) - 1) if vals[i + 1] <= vals[i]]
            fails.append("frame counter not strictly increasing (stalls: %s)" % stalls[:5])
    else:
        fails.append("no frame samples collected")
    after = crash_files(crash_dirs)
    for p, mt in after.items():
        if p not in before or before[p] != mt:
            fails.append("psx_crash.txt appeared/changed: %s" % p)
            try:
                log("--- %s ---\n%s" % (p, open(p, errors="replace").read()[:4000]))
            except OSError:
                pass
    for p in shots:
        log("screenshot: " + p)
    if fails:
        log("RESULT: FAIL")
        for f in fails:
            log("  - " + f)
        try:
            tail = open(runlog, errors="replace").read().splitlines()[-15:]
            log("--- last log lines (%s) ---" % runlog)
            for l in tail:
                log(l)
        except OSError:
            pass
        return 1
    st = ", ".join("t%d=%s" % (int(m), v) for m, v in sorted(shot_status.items()))
    log("RESULT: PASS (%.0f s, frames %s -> %s, %d screenshots: %s, end=%s)" %
        (a.seconds, frames[0][1], frames[-1][1], len(shots), st,
         "ok" if end_ok else "FAILED"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
