#!/usr/bin/env python3
r"""T2.16: prove the build-time static overlay shard runs in the first level (stdlib only).

Run:  <RETRO_TOOLS_DIR>\python\python.exe -I tools\overlay_static_probe.py [options]

  --out FILE     result JSON (default work\overlay_static_probe.json; no absolute paths, no timestamps)
  --route R      input route (default tests\replays\routes\boot_to_menu.json, which reaches the first level)
  --frames a,b,c guest frames at which to query (default 5000,5400,6000)
  --port N       debug port (default 4384)
  --shots DIR    debug only: screenshot at the last query (DIR must be under work\; never committed)

Launches the debug build work\build-dbg\MythologyKombat.exe --headless (cold boot, fresh memory card dir),
plays the route and at each frame sends `overlay_static_entries` over the overlay window
0x80130FF8..0x8013C720 and `overlay_loader_status`. Frames are polled, so the query lands a few frames
after the requested one (the real frame is recorded). Exit 0 when static hits are 0 at the first query
and non-zero at the last, else 1 (setup errors 2).
"""
import argparse, json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smoke_boot as sb      # noqa: E402
import run_boot_route as rb  # noqa: E402

LO, HI = "0x80130FF8", "0x8013C720"
STATUS_KEYS = ["static_checks", "static_hits", "static_variant_misses", "static_crc_misses", "static_rehashes",
               "static_gen_fastpath", "static_address_misses", "dispatch_native", "dispatch_interp_fallback",
               "segment_alias_interp", "segment_native"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(rb.WORK, "overlay_static_probe.json"))
    ap.add_argument("--route", default=rb.DEF_ROUTE)
    ap.add_argument("--frames", default="5000,5400,6000")
    ap.add_argument("--port", type=int, default=4384)
    ap.add_argument("--shots")
    a = ap.parse_args()
    frames = sorted(int(x) for x in a.frames.split(","))
    route = rb.load_route(a.route)
    exe, disc = os.path.abspath(sb.DBG_EXE), os.path.abspath(sb.DEF_DISC)
    for p, what in ((exe, "exe"), (disc, "disc image")):
        if not os.path.isfile(p):
            print("setup: %s not found: %s" % (what, p)); return 2
    if not sb.exe_has_debug_server(exe):
        print("setup: exe was built without PSX_DEBUG_TOOLS; use work\build-dbg"); return 2
    shots = None
    if a.shots:
        shots = os.path.abspath(a.shots)
        if not shots.lower().startswith(rb.WORK.lower() + os.sep):
            print("setup: --shots must be under work\\"); return 2
        os.makedirs(shots, exist_ok=True)
    saves = os.path.join(rb.WORK, "static_probe_saves")
    shutil.rmtree(saves, ignore_errors=True)
    os.makedirs(saves)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    env = dict(os.environ)
    env["PSX_DEBUG_FMV_QUIET"] = "0"
    lf = open(os.path.join(rb.WORK, "static_probe_run.log"), "wb")
    exe_dir = os.path.dirname(exe)
    proc = subprocess.Popen([exe, "--disc", disc, "--game", os.path.join(exe_dir, "game.toml"), "--no-launcher",
                             "--headless", "--debug-port", str(a.port), "--memcard-dir", saves],
                            cwd=exe_dir, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env)
    dbg = sb.Dbg(a.port)
    queries = []
    try:
        t0 = time.time()
        while True:
            if proc.poll() is not None:
                print("game exited during startup"); return 1
            try:
                dbg.connect(); break
            except OSError:
                if time.time() - t0 > 60:
                    print("debug port never opened"); return 1
                time.sleep(0.1)
        rb.call_ok(dbg, "input_route_clear")
        for c in route["cmds"]:
            rb.call_ok(dbg, "input_route_append", frames=c["frames"], buttons=c["buttons"])
        rb.call_ok(dbg, "input_route_start", at_frame=route["first"])
        for n in frames:
            while rb.call_ok(dbg, "frame")["frame"] < n:
                if proc.poll() is not None:
                    print("game died before frame %d" % n); return 1
                time.sleep(0.1)
            ent = rb.call_ok(dbg, "overlay_static_entries", addr_lo=LO, addr_hi=HI, limit=12)
            st = rb.call_ok(dbg, "overlay_loader_status")
            q = {"requested_frame": n, "frame": rb.call_ok(dbg, "frame")["frame"],
                 "entries": {k: ent[k] for k in ("entries", "total_hits", "range_variants", "range_hits",
                                                 "range_hit_entries")},
                 "top": ent.get("top", []),
                 "loader": {k: st.get(k) for k in STATUS_KEYS}}
            queries.append(q)
            print("frame %d (req %d): range_hits=%s hit_entries=%s static_checks=%s static_hits=%s crc_misses=%s" % (
                q["frame"], n, q["entries"]["range_hits"], q["entries"]["range_hit_entries"],
                q["loader"]["static_checks"], q["loader"]["static_hits"], q["loader"]["static_crc_misses"]))
        if shots:
            rb.call_ok(dbg, "screenshot", path=os.path.join(shots, "static_probe_f%d.png" % frames[-1]))
    finally:
        try:
            dbg.call("quit")
        except Exception:
            pass
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            sb.kill_pid(proc.pid)
        lf.close()
    ok = (queries[0]["entries"]["range_hits"] == 0 and queries[-1]["entries"]["range_hits"] > 0)
    res = {"schema": 1, "route_name": route["name"], "window": [LO, HI], "queries": queries, "static_hits_in_window_at_end": ok}
    json.dump(res, open(a.out, "w"), indent=1)
    print("result written: %s" % os.path.relpath(a.out, rb.ROOT))
    print("RESULT: %s" % ("STATIC OVERLAY CODE RUNS (hits 0 -> %d)" % queries[-1]["entries"]["range_hits"] if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
