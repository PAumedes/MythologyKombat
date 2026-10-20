#!/usr/bin/env python3
"""Identify the movies (and other disc streams) read during a boot route (T2.10). Stdlib only.

Run:  <RETRO_TOOLS_DIR>\\python\\python.exe -I tools\\fmv_identify.py [options]

  --route R        route file (default tests\\replays\\routes\\boot_to_menu.json); "none" = no input at all
  --until N        stop at guest frame N (default 5600)
  --out FILE       write the result JSON here (default work\\fmv\\identify.json)
  --port N         debug port (default 4382)
  --from-json F    do not run the game; re-print the table from a saved result JSON
  --telemetry DIR  do not run the game; read DIR\telemetry.csv (a recorded playtest session) and map its
                   per-VBlank cd_lba samples to disc files. Also prints host_elapsed (play duration).
                   Samples are one per guest VBlank, so LBA ranges are sampled positions, not every sector.

What it does: cold-boots work\\build-dbg\\MythologyKombat.exe --headless (fresh memcard dir
work\\fmv_saves), queues the route like tools\\run_boot_route.py, and every ~0.4 s pulls the
new entries of the debug server's `cdrom_sector_history` ring (de-duplicated by `seq`, so
nothing is read twice and nothing is lost unless the ring wraps; wrap is detected and reported).
It also samples `fmv_state` (mdec_decode_count) so the picture decoder activity per movie is shown.

Each sector LBA is mapped to its disc file with the same data tools\\lba_lookup.py uses
(work\\disc_files.json, written by tools\\disc_list.py). Consecutive sectors in the same file
form one "span" (a read burst); a movie is every span of a /MOVIES/*.STR file. Output table:
file, LBA range seen, number of distinct sectors read, first/last guest frame seen, MDEC decodes
during the window, XA-audio sectors (xa_submode bit 2) vs other sector reads (STR video/data; the
history marks no sector as video, so there is no separate video column; reads can repeat an LBA).
ps1_game is only read by the game process itself (read only); nothing is written there.
Exit codes: 0 ok, 1 run failure, 2 setup error.
"""
import argparse, json, os, shutil, socket, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smoke_boot as sb  # noqa: E402
import run_boot_route as rb  # noqa: E402
import lba_lookup as ll  # noqa: E402

ROOT = sb.ROOT
WORK = os.path.join(ROOT, "work")
OUTDIR = os.path.join(WORK, "fmv")
SAVES = os.path.join(WORK, "fmv_saves")
PIDFILE = os.path.join(OUTDIR, "pid.txt")


def log(m):
    print(m, flush=True)


def load_files():
    d = json.load(open(ll.FILES_JSON))
    files = d["files"] if isinstance(d, dict) and "files" in d else d
    out = []
    for f in files:
        name = f.get("path") or f.get("name")
        lba = f.get("lba", f.get("start_lba"))
        n = f.get("sectors", f.get("sector_count"))
        if n is None and "size" in f:
            n = (f["size"] + 2047) // 2048
        if name is None or lba is None or n is None:
            continue
        out.append((name, int(lba), int(n)))
    out.sort(key=lambda t: t[1])
    return out


def file_of(files, lba):
    for name, s, n in files:
        if s <= lba < s + n:
            return name
    return None


def collect(a):
    exe, disc = os.path.abspath(a.exe), os.path.abspath(a.disc)
    for p, what in ((exe, "exe"), (disc, "disc image")):
        if not os.path.isfile(p):
            raise SystemExit("setup: %s not found: %s" % (what, p))
    try:
        socket.create_connection(("127.0.0.1", a.port), timeout=1).close()
        raise SystemExit("setup: port %d in use" % a.port)
    except OSError:
        pass
    os.makedirs(OUTDIR, exist_ok=True)
    shutil.rmtree(SAVES, ignore_errors=True)
    os.makedirs(SAVES, exist_ok=True)
    route = None if a.route.lower() == "none" else rb.load_route(a.route)
    exe_dir = os.path.dirname(exe)
    cmd = [exe, "--disc", disc, "--game", os.path.join(exe_dir, "game.toml"), "--no-launcher",
           "--headless", "--debug-port", str(a.port), "--memcard-dir", SAVES]
    env = dict(os.environ)
    env["PSX_DEBUG_FMV_QUIET"] = "0"
    lf = open(os.path.join(OUTDIR, "run.log"), "wb")
    t0 = time.time()
    proc = subprocess.Popen(cmd, cwd=exe_dir, stdout=lf, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, env=env)
    open(PIDFILE, "w").write(str(proc.pid))
    dbg = sb.Dbg(a.port)
    sectors = []   # (seq, lba, frame, xa_submode, data_delivered, xa_audio_delivered, mdec_count)
    mdec_samples = []  # (frame, mdec_decode_count)
    wrapped = False
    last_total = 0
    try:
        while True:
            if proc.poll() is not None:
                raise rb.Fail("game exited during startup, code %s" % proc.returncode)
            try:
                dbg.connect()
                break
            except OSError:
                if time.time() - t0 > 60:
                    raise rb.Fail("debug port never opened")
                time.sleep(0.1)
        if route:
            rb.call_ok(dbg, "input_route_clear")
            for c in route["cmds"]:
                rb.call_ok(dbg, "input_route_append", frames=c["frames"], buttons=c["buttons"])
            r = rb.call_ok(dbg, "input_route_start", at_frame=route["first"])
            if r.get("start_frame") != route["first"]:
                raise rb.Fail("route started too late (start_frame=%s)" % r.get("start_frame"))
        while True:
            if proc.poll() is not None:
                raise rb.Fail("game died (exit %s)" % proc.returncode)
            fr = rb.call_ok(dbg, "frame")["frame"]
            fs = rb.call_ok(dbg, "fmv_state")
            mdec_samples.append((fr, fs["mdec_decode_count"]))
            want = 64
            h = rb.call_ok(dbg, "cdrom_sector_history", count=1)
            total = h["total"]
            if total > last_total:
                want = min(total - last_total, 8192)
                if total - last_total > 8192:
                    wrapped = True
                h = rb.call_ok(dbg, "cdrom_sector_history", count=want, timeout=60)
                for e in h["entries"]:
                    if e["seq"] >= last_total:
                        sectors.append((e["seq"], e["lba"], e["frame"], int(e["xa_submode"], 16),
                                        e["data_delivered"], e["xa_audio_delivered"]))
                last_total = total
            if fr >= a.until:
                break
            time.sleep(0.4)
        wall = time.time() - t0
        log("run: %.1f s wall, final frame %d, %d sector entries (ring total %d), ring_wrapped=%s"
            % (wall, fr, len(sectors), last_total, wrapped))
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
        try:
            os.remove(PIDFILE)
        except OSError:
            pass
    return {"schema": 1, "route": a.route, "until": a.until, "ring_wrapped": wrapped,
            "ring_total": last_total,
            "exe_sha256": __import__("hashlib").sha256(open(exe, "rb").read()).hexdigest(),
            "sectors": [list(s) for s in sectors], "mdec_samples": mdec_samples}


def summarize(res):
    files = load_files()
    spans = []  # per-file aggregate in first-seen order
    agg = {}
    order = []
    for seq, lba, frame, sub, dd, xd in sorted(res["sectors"]):
        name = file_of(files, lba) or "(no file: LBA %d)" % lba
        if name not in agg:
            agg[name] = {"file": name, "lbas": set(), "first": frame, "last": frame,
                         "first_seq": seq, "video": 0, "audio": 0, "other": 0, "bursts": 0, "_prev": None}
            order.append(name)
        g = agg[name]
        g["lbas"].add(lba)
        g["first"] = min(g["first"], frame)
        g["last"] = max(g["last"], frame)
        if sub & 0x04:
            g["audio"] += 1
        elif sub & 0x02:
            g["video"] += 1
        else:
            g["other"] += 1
        if g["_prev"] is None or lba != g["_prev"] + 1:
            g["bursts"] += 1
        g["_prev"] = lba
    ms = res["mdec_samples"]

    def mdec_at(frame, after):
        best = None
        for f, c in ms:
            if (f <= frame) if not after else (f >= frame):
                if not after:
                    best = c
                else:
                    return c
        return best
    rows = []
    for name in order:
        g = agg[name]
        lbas = sorted(g["lbas"])
        m0, m1 = mdec_at(g["first"], False), mdec_at(g["last"], True)
        rows.append({"file": name, "lba_lo": lbas[0], "lba_hi": lbas[-1], "distinct": len(lbas),
                     "bursts": g["bursts"], "first_frame": g["first"], "last_frame": g["last"],
                     "video": g["video"], "audio": g["audio"], "other": g["other"],
                     "mdec_delta": (m1 - m0) if (m0 is not None and m1 is not None) else None})
    return rows


def print_table(rows, res):
    hdr = ("file", "LBA range seen", "distinct LBAs", "first frame", "last frame", "xa-audio reads", "other reads", "mdec decodes")
    print("route=%s until=%s ring_wrapped=%s ring_total=%s" % (res["route"], res["until"],
                                                              res["ring_wrapped"], res["ring_total"]))
    print("| " + " | ".join(hdr) + " |")
    print("|" + "---|" * len(hdr))
    for r in sorted(rows, key=lambda r: r["first_frame"]):
        print("| %s | %d-%d | %d | %d | %d | %d | %d | %s |" % (
            r["file"], r["lba_lo"], r["lba_hi"], r["distinct"], r["first_frame"], r["last_frame"],
            r["audio"], r["video"] + r["other"], r["mdec_delta"]))


def telemetry_report(d):
    import csv
    files = load_files()
    rows = list(csv.DictReader(open(os.path.join(d, "telemetry.csv"), newline="")))
    last = rows[-1]
    print("session: %s" % os.path.basename(d.rstrip("/\\")))
    print("telemetry rows (guest VBlanks): %d, last sequence %s" % (len(rows), last["sequence"]))
    el = int(last["host_elapsed_us"])
    print("host_elapsed (first row %s us -> last row %d us): %.1f s = %d min %.1f s" % (
        rows[0]["host_elapsed_us"], el, el / 1e6, el // 60000000, (el % 60000000) / 1e6))
    agg, order = {}, []
    for r in rows:
        lba = int(r["cd_lba"])
        if lba < 0 or not int(r["cd_reading"]):
            continue
        name = file_of(files, lba) or "(no file: LBA %d)" % lba
        g = agg.get(name)
        seq, t = int(r["sequence"]), int(r["host_elapsed_us"]) / 1e6
        if g is None:
            g = agg[name] = {"lo": lba, "hi": lba, "s0": seq, "s1": seq, "t0": t, "t1": t, "n": 0, "xa": 0, "iv": 0}
            order.append(name)
        g["lo"], g["hi"] = min(g["lo"], lba), max(g["hi"], lba)
        g["s1"], g["t1"] = seq, t
        g["n"] += 1
        g["xa"] += 1 if int(r["cd_xa"]) else 0
        g["iv"] += int(r["host_interval_us"])
    print("| file | LBA range sampled | VBlank samples | of which cd_xa!=0 | first seq | last seq | first host s | last host s | mean guest Hz (samples / sum host_interval) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name in order:
        g = agg[name]
        print("| %s | %d-%d | %d | %d | %d | %d | %.1f | %.1f | %.1f |" % (
            name, g["lo"], g["hi"], g["n"], g["xa"], g["s0"], g["s1"], g["t0"], g["t1"],
            g["n"] * 1e6 / g["iv"] if g["iv"] else 0.0))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--route", default=rb.DEF_ROUTE)
    ap.add_argument("--until", type=int, default=5600)
    ap.add_argument("--out", default=os.path.join(OUTDIR, "identify.json"))
    ap.add_argument("--port", type=int, default=4382)
    ap.add_argument("--exe", default=sb.DBG_EXE)
    ap.add_argument("--disc", default=sb.DEF_DISC)
    ap.add_argument("--from-json")
    ap.add_argument("--telemetry")
    a = ap.parse_args()
    if a.telemetry:
        telemetry_report(a.telemetry)
        return 0
    if a.from_json:
        res = json.load(open(a.from_json))
    else:
        try:
            res = collect(a)
        except rb.Fail as e:
            log("RESULT: FAIL (%s)" % e)
            return 1
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump(res, open(a.out, "w"))
        log("saved: %s" % a.out)
    print_table(summarize(res), res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
