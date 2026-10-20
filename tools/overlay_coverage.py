#!/usr/bin/env python3
r"""T2.17: overlay coverage monitor. Launch the debug build, let Patricio play, log what loads (stdlib only).

Run:  <RETRO_TOOLS_DIR>\python\python.exe -I tools\overlay_coverage.py [options]
  or: powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_overlay_coverage.ps1 [options]

  --interval S      seconds between polls (default 3)
  --port N          debug port (default 4385; 4370/4380/4381/4383/4384 are used by other tools)
  --boot-route      play tests\replays\routes\boot_to_menu.json (skips the intro, selects New Game) so the
                    game reaches the first level (TEMPLE) by itself. Without it you play from the logos.
  --headless        no window, no audio (self-test only; a human cannot play like this)
  --max-seconds S   stop after S seconds (default: run until the window is closed or Ctrl+C)
  --fresh-saves     delete the coverage memory-card dir first (default: keep it, so saves persist between sessions)
  --out DIR         output dir (default work\overlay_coverage\<timestamp>; must be under work\)
  --exe / --disc    override the exe (default work\build-dbg\MythologyKombat.exe) / the disc .cue
  --quiet           print the live line only when something new loads (no heartbeat every 30 s)

What it does:
  * launches the DEBUG build with a visible window (the Release exe has no debug server);
  * every --interval seconds sends `frame`, `overlay_loader_status` and `overlay_static_entries` over the overlay
    window 0x80130FF8..0x8013C720 (limit 1024) and reads the first 256 bytes of that window from RAM;
  * uses `fn_filter` over the nine level-load functions (0x8002B688..0x8002FC84) so every entry of a level
    function is recorded with the guest frame (this is how FIRE's two functions are told apart);
  * identifies the loaded overlay by comparing the window head with the .OVR bytes read from the disc image
    (ids BRIDGE 135, EARTH 136, FIRE 137, FORTRESS 138, PRISON 139, TEMPLE 140, WATER 141, WIND 142);
  * writes one JSON line per poll to <out>\coverage.jsonl and prints a live line when a new id appears;
  * on exit (window closed, Ctrl+C, --max-seconds) writes <out>\summary.json and <out>\summary.txt and prints the table.

Attribution rule: counter deltas between two polls are credited to the overlay id resident at the END of the poll
(overlays share the base 0x80130FF8, so per-entry hits cannot be split any other way). Polls are a few seconds
apart, so the poll that sees a new id also credits the previous interval to it; read the numbers as approximate.
Per-entry deltas come from `overlay_static_entries`, so "static entries hit" counts distinct entry addresses whose
hit count grew while that id was resident.

Faults: exit code, psx_crash.txt (exe dir, saves dir, cwd, repo root) if new, and crash-like lines of run.log are
copied into the summary. A game that dies shows as "exit code != 0" or a crash file; a window closed by hand is exit 0.

Exit codes: 0 finished (summary written), 2 setup error. Nothing here modifies ps1_game\ or the game; output is
under work\ (git-ignored).
"""
import argparse, datetime, json, os, re, shutil, socket, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smoke_boot as sb              # noqa: E402  (Dbg, kill_pid, pid_is_ours, exe_has_debug_server)
import run_boot_route as rb          # noqa: E402  (load_route, call_ok, Fail, DEF_ROUTE)
import overlay_runtime_check as orc  # noqa: E402  (load_expected: .OVR bytes from the disc, level functions)

ROOT = sb.ROOT
WORK = os.path.join(ROOT, "work")
WIN_LO, WIN_HI = "0x80130FF8", "0x8013C720"
HEAD = 256
LV_LO, LV_HI = 0x8002B688, 0x8002FC84
IDS = {135: "BRIDGE", 136: "EARTH", 137: "FIRE", 138: "FORTRESS", 139: "PRISON", 140: "TEMPLE", 141: "WATER", 142: "WIND"}
STATUS_KEYS = ["loads", "regions", "static_checks", "static_hits", "static_variant_misses", "static_crc_misses",
               "static_rehashes", "static_gen_fastpath", "static_address_misses", "dispatch_native",
               "dispatch_interp_fallback", "segment_alias_interp", "segment_native"]
DELTA_KEYS = ["static_checks", "static_hits", "static_crc_misses", "static_address_misses",
              "dispatch_interp_fallback", "segment_alias_interp"]
CRASHY = re.compile(r"crash|fault|exception|abort|fatal|assert|unhandled|access violation|panic|error", re.I)


def log(m):
    print(m, flush=True)


def now_s():
    return datetime.datetime.now().strftime("%H:%M:%S")


def hx(v):
    return int(v, 16) if isinstance(v, str) else int(v)


def level_of(pc, levels):
    for L in levels:
        if L["start"] <= pc < L["end"]:
            return L
    return None


def entry_pc(e):
    for k in ("addr", "pc", "entry", "fn", "func", "target"):
        if k in e:
            try:
                return hx(e[k])
            except (ValueError, TypeError):
                pass
    return None


def new_stats():
    return {"first_seen_frame": None, "first_seen_t": None, "polls_resident": 0, "resident_s": 0.0,
            "delta": {k: 0 for k in DELTA_KEYS}, "range_hits": 0, "entries_hit": set(), "hits_by_entry": {}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--interval", type=float, default=3.0)
    ap.add_argument("--port", type=int, default=4385)
    ap.add_argument("--boot-route", action="store_true")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--max-seconds", type=float, default=0)
    ap.add_argument("--fresh-saves", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--exe", default=sb.DBG_EXE)
    ap.add_argument("--disc", default=sb.DEF_DISC)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    if a.port in (4370, 4371, 4380, 4381, 4383, 4384):
        print("setup: port %d is used by the Release game / other tools; pick another" % a.port); return 2
    exe, disc = os.path.abspath(a.exe), os.path.abspath(a.disc)
    for p, what in ((exe, "exe"), (disc, "disc image")):
        if not os.path.isfile(p):
            print("setup: %s not found: %s" % (what, p)); return 2
    if not sb.exe_has_debug_server(exe):
        print("setup: exe was built without PSX_DEBUG_TOOLS; use work\\build-dbg"); return 2
    try:
        socket.create_connection(("127.0.0.1", a.port), timeout=1).close()
        print("setup: port %d already in use (another game instance running?)" % a.port); return 2
    except OSError:
        pass
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.abspath(a.out) if a.out else os.path.join(WORK, "overlay_coverage", ts)
    if not out.lower().startswith(WORK.lower() + os.sep):
        print("setup: --out must be under work\\"); return 2
    os.makedirs(out, exist_ok=True)

    log("loading expected .OVR bytes from the disc image ...")
    ovr, levels, _boot = orc.load_expected()
    heads = {i: bytes(o["data"][:HEAD]) for i, o in ovr.items()}
    route = rb.load_route(rb.DEF_ROUTE) if a.boot_route else None

    saves = os.path.join(WORK, "overlay_coverage_saves")
    if a.fresh_saves:
        shutil.rmtree(saves, ignore_errors=True)
    os.makedirs(saves, exist_ok=True)
    exe_dir = os.path.dirname(exe)
    crash_dirs = [exe_dir, saves, os.getcwd(), ROOT]
    crash_before = sb.crash_files(crash_dirs)
    cmd = [exe, "--disc", disc, "--game", os.path.join(exe_dir, "game.toml"), "--no-launcher",
           "--debug-port", str(a.port), "--memcard-dir", saves]
    if a.headless:
        cmd.append("--headless")
    runlog_path = os.path.join(out, "run.log")
    lf = open(runlog_path, "wb")
    proc = subprocess.Popen(cmd, cwd=exe_dir, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    log("exe pid %d, window %s, output %s" % (proc.pid, "HIDDEN (headless)" if a.headless else "visible", out))
    dbg = sb.Dbg(a.port)
    jl = open(os.path.join(out, "coverage.jsonl"), "w", buffering=1)

    stats = {i: new_stats() for i in IDS}
    lvl_entries = {L["name"]: [] for L in levels}      # name -> [{frame, t, ra}]
    cur = None                                          # resident id
    sequence = []                                       # ids in order of first appearance / change
    prev_status, prev_hits = None, {}
    unmatched_polls, errors, polls = 0, 0, 0
    last_frame, last_poll_t = None, None
    seq_cursor = 0
    pc_key_seen = None
    t0 = time.time()
    last_hb = t0
    reason = "unknown"
    try:
        while True:                                     # wait for the debug port
            if proc.poll() is not None:
                reason = "game exited during startup, code %s" % proc.returncode
                raise SystemExit(0)
            try:
                dbg.connect(); break
            except OSError:
                if time.time() - t0 > 90:
                    reason = "debug port never opened"; raise SystemExit(0)
                time.sleep(0.2)
        log("[%s] debug server up. %s" % (now_s(), "Playing boot route (New Game)." if route else "Play the game now; close the window or press Ctrl+C when done."))
        if route:
            rb.call_ok(dbg, "input_route_clear")
            for c in route["cmds"]:
                rb.call_ok(dbg, "input_route_append", frames=c["frames"], buttons=c["buttons"])
            rb.call_ok(dbg, "input_route_start", at_frame=route["first"])
        rb.call_ok(dbg, "fn_filter", lo="0x%08X" % LV_LO, hi="0x%08X" % LV_HI)
        seq_cursor = rb.call_ok(dbg, "fn_stats")["entry_total"]
        t_start = time.time()
        while True:
            if proc.poll() is not None:
                reason = "game process ended (exit code %s)" % proc.returncode
                break
            if a.max_seconds and time.time() - t_start >= a.max_seconds:
                reason = "--max-seconds reached"
                break
            time.sleep(a.interval)
            if proc.poll() is not None:
                continue
            tp = time.time()
            rec = {"t": round(tp - t_start, 1), "wall": datetime.datetime.now().isoformat(timespec="seconds")}
            try:
                fr = rb.call_ok(dbg, "frame")["frame"]
                st = rb.call_ok(dbg, "overlay_loader_status")
                ent = rb.call_ok(dbg, "overlay_static_entries", addr_lo=WIN_LO, addr_hi=WIN_HI, limit=1024)
                head = bytes.fromhex(rb.call_ok(dbg, "read_ram", addr=WIN_LO, len=HEAD)["hex"])
                fe = rb.call_ok(dbg, "fn_entry_dump", seq_lo=seq_cursor, count=2048,
                                addr_lo="0x%08X" % LV_LO, addr_hi="0x%08X" % LV_HI)
            except (rb.Fail, OSError, ValueError) as e:
                if proc.poll() is not None:
                    continue
                errors += 1
                rec["error"] = str(e)[:200]
                jl.write(json.dumps(rec) + "\n")
                if errors >= 5 and errors > polls // 2 + 5:
                    reason = "debug server unusable (%s)" % e
                    break
                continue
            polls += 1
            last_frame, last_poll_t = fr, tp
            status = {k: st.get(k) for k in STATUS_KEYS}

            # level-function entries since the last poll
            new_lv = []
            for e in fe.get("entries", []):
                pc = entry_pc(e)
                if pc is not None:
                    pc_key_seen = pc_key_seen or True
                L = level_of(pc, levels) if pc is not None else None
                name = L["name"] if L else "?"
                lvl_entries.setdefault(name, []).append({"frame": e.get("frame"), "t": round(tp - t_start, 1), "ra": e.get("ra")})
                new_lv.append(name)
            seq_cursor = max(seq_cursor, fe.get("seq_hi", seq_cursor), (fe["entries"][-1]["seq"] + 1) if fe.get("entries") else 0)

            # which overlay is resident
            ids = [i for i, h in heads.items() if head == h]
            rid = ids[0] if len(ids) == 1 else None
            if rid is None:
                unmatched_polls += 1
            # per-entry hit deltas
            hits_now = {t["addr"]: t["hits"] for t in ent.get("top", [])}
            grew = {ad: h - prev_hits.get(ad, 0) for ad, h in hits_now.items() if h > prev_hits.get(ad, 0)}
            d = {k: (status[k] - prev_status[k]) if (prev_status and isinstance(status[k], int) and isinstance(prev_status.get(k), int)) else (status[k] if isinstance(status[k], int) else 0) for k in DELTA_KEYS}
            credit = rid if rid is not None else cur
            if rid is not None and rid != cur:
                s = stats[rid]
                if s["first_seen_frame"] is None:
                    s["first_seen_frame"], s["first_seen_t"] = fr, round(tp - t_start, 1)
                sequence.append({"id": rid, "frame": fr, "t": round(tp - t_start, 1)})
                log("[%s] t=%6.1fs frame %d: NEW OVERLAY %d %s resident  (loader entered: %s; static range_hits so far %s, interp fallbacks %s)" % (
                    now_s(), tp - t_start, fr, rid, IDS[rid], ",".join(new_lv) or "not seen this interval",
                    ent.get("range_hits"), status["dispatch_interp_fallback"]))
                cur = rid
            elif new_lv:
                log("[%s] t=%6.1fs frame %d: level function entered: %s" % (now_s(), tp - t_start, fr, ",".join(new_lv)))
            if credit is not None:
                s = stats[credit]
                s["polls_resident"] += 1
                s["resident_s"] += a.interval
                for k in DELTA_KEYS:
                    s["delta"][k] += max(0, d[k])
                s["range_hits"] += sum(grew.values())
                for ad, g in grew.items():
                    s["entries_hit"].add(ad)
                    s["hits_by_entry"][ad] = s["hits_by_entry"].get(ad, 0) + g
            prev_status, prev_hits = status, hits_now
            rec.update({"frame": fr, "window_id": rid, "resident": cur, "level_entries": new_lv, "status": status,
                        "range_hits": ent.get("range_hits"), "range_hit_entries": ent.get("range_hit_entries"),
                        "top": ent.get("top", [])[:5]})
            jl.write(json.dumps(rec) + "\n")
            if not a.quiet and time.time() - last_hb >= 30:
                last_hb = time.time()
                log("[%s] t=%6.1fs frame %d resident=%s range_hits=%s hit_entries=%s fallback=%s" % (
                    now_s(), tp - t_start, fr, ("%d %s" % (cur, IDS[cur])) if cur else "none", ent.get("range_hits"),
                    ent.get("range_hit_entries"), status["dispatch_interp_fallback"]))
    except KeyboardInterrupt:
        reason = "Ctrl+C"
    except SystemExit:
        pass
    finally:
        if proc.poll() is None:
            try:
                dbg.call("quit")
            except Exception:
                pass
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                sb.kill_pid(proc.pid)          # our own child only
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
        lf.close()
        jl.close()

    exit_code = proc.returncode
    # ---- faults
    faults = []
    if exit_code not in (0, None):
        faults.append("exit code %s (0x%08X)" % (exit_code, exit_code & 0xFFFFFFFF))
    for p, mt in sb.crash_files(crash_dirs).items():
        if p not in crash_before or crash_before[p] != mt:
            dst = os.path.join(out, "psx_crash_%s.txt" % os.path.basename(os.path.dirname(p)))
            shutil.copyfile(p, dst)
            faults.append("psx_crash.txt written: %s (copied to %s)" % (p, dst))
    try:
        crashy = [l.strip() for l in open(runlog_path, errors="replace") if CRASHY.search(l)]
    except OSError:
        crashy = []
    rep = os.path.join(exe_dir, "psx_last_run_report.json")
    if os.path.isfile(rep) and os.path.getmtime(rep) >= t0:
        shutil.copyfile(rep, os.path.join(out, "psx_last_run_report.json"))

    # ---- summary
    final = None
    try:
        final = prev_status
    except NameError:
        pass
    level_rows = []
    for L in levels:
        ents = lvl_entries.get(L["name"], [])
        level_rows.append({"level_function": L["name"], "start": "0x%08X" % L["start"], "ids_read": L["ids"],
                           "loader_entries": len(ents), "first_entry_frame": ents[0]["frame"] if ents else None})
    img_rows = []
    for i in sorted(IDS):
        s = stats[i]
        img_rows.append({"id": i, "name": IDS[i], "reached": s["first_seen_frame"] is not None,
                         "first_seen_frame": s["first_seen_frame"], "first_seen_t": s["first_seen_t"],
                         "polls_resident": s["polls_resident"], "static_hits_in_window": s["range_hits"],
                         "static_entries_hit": len(s["entries_hit"]),
                         "interpreter_fallbacks": s["delta"]["dispatch_interp_fallback"],
                         "interpreter_fallback": s["delta"]["dispatch_interp_fallback"] > 0,
                         "segment_alias_interp": s["delta"]["segment_alias_interp"],
                         "static_crc_misses": s["delta"]["static_crc_misses"],
                         "static_address_misses": s["delta"]["static_address_misses"],
                         "top_entries": sorted(s["hits_by_entry"].items(), key=lambda kv: -kv[1])[:5]})
    summary = {"schema": 1, "tool": "tools/overlay_coverage.py", "out_dir": out, "end_reason": reason, "exit_code": exit_code,
               "polls": polls, "poll_errors": errors, "polls_with_unmatched_window": unmatched_polls,
               "last_frame": last_frame, "duration_s": round(time.time() - t0, 1), "load_sequence": sequence,
               "images": img_rows, "level_functions": level_rows, "final_loader_status": final,
               "faults": faults, "crash_like_log_lines": crashy[-20:]}
    json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=1)

    lines = ["", "=== overlay coverage summary (%s) ===" % out,
             "end: %s; exit code %s; %d polls (%d errors); last frame %s; %.0f s" % (reason, exit_code, polls, errors, last_frame, summary["duration_s"]),
             "load order: %s" % (" -> ".join("%s@f%d" % (IDS[x["id"]], x["frame"]) for x in sequence) or "none"),
             "", "%-4s %-9s %-8s %-9s %-12s %-9s %-10s %-10s %s" % ("id", "name", "reached", "frame", "static hits", "entries", "interp fb", "seg alias", "crc miss"),
             ]
    for r in img_rows:
        lines.append("%-4d %-9s %-8s %-9s %-12d %-9d %-10s %-10d %d" % (
            r["id"], r["name"], "yes" if r["reached"] else "no", r["first_seen_frame"] if r["reached"] else "-",
            r["static_hits_in_window"], r["static_entries_hit"],
            ("yes %d" % r["interpreter_fallbacks"]) if r["interpreter_fallback"] else "no",
            r["segment_alias_interp"], r["static_crc_misses"]))
    lines += ["", "level functions seen entering (fn_entry ring): " + ", ".join(
        "%s x%d%s" % (r["level_function"], r["loader_entries"], (" (f%s)" % r["first_entry_frame"]) if r["loader_entries"] else "") for r in level_rows)]
    lines.append("faults: %s" % ("; ".join(faults) if faults else "none (clean exit, no psx_crash.txt)"))
    if crashy:
        lines.append("crash-like lines in run.log (last %d of %d): " % (min(5, len(crashy)), len(crashy)))
        lines += ["    " + l[:160] for l in crashy[-5:]]
    if unmatched_polls:
        lines.append("note: %d of %d polls had a window head that matched no .OVR (loading in progress, or code patched)" % (unmatched_polls, polls))
    lines.append("Visible faults (graphics, hangs, wrong music) are not detectable here: report them to the agent by hand.")
    txt = "\n".join(lines)
    open(os.path.join(out, "summary.txt"), "w").write(txt + "\n")
    print(txt)
    log("files: %s" % ", ".join(sorted(os.listdir(out))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
