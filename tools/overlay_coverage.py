#!/usr/bin/env python3
r"""T2.17: overlay coverage monitor. Launch the debug build, let Patricio play, log what loads (stdlib only).

Run:  <RETRO_TOOLS_DIR>\python\python.exe -I tools\overlay_coverage.py [options]
  or: powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_overlay_coverage.ps1 [options]

  --interval S      seconds between polls (default 3)
  --port N          debug port (default 4385; 4370/4380/4381/4383/4384 are used by other tools)
  --boot-route      play tests\replays\routes\boot_to_menu.json (skips the intro, selects New Game) so the
                    game reaches the first level (TEMPLE) by itself. Without it you play from the logos.
  --warp LEVEL      coverage aid, NOT natural play: after the New Game boot route, make the game's level dispatcher
                    (jump table 0x80013910, index word 0x800D76A8) start LEVEL instead of TEMPLE. LEVEL is one of
                    TEMPLE WIND WATER EARTH PRISON FIRE FIRE2 BRIDGE FORTRESS, or a dispatcher index 0-5, 7-9. Implies
                    --boot-route. It rewrites table entry 0 in guest RAM with write_ram (4 single-byte writes, read back
                    and verified); no file, framework or generated code is touched. See docs/SETUP.md ("Warp to a level").
  --shots S         every S seconds save a 320x240 PNG screenshot to <out>\shots\ (debug server `screenshot`; evidence of
                    what is on screen, e.g. for warped levels). Off by default.
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
DISP_TABLE, DISP_N, IDX_ADDR = 0x80013910, 12, 0x800D76A8
# dispatcher index -> level name (docs/EXE_OVERLAYS.md, "Dispatcher"); 6 and 11 load no overlay, 10 is conditional
WARP = {"TEMPLE": 0, "WIND": 1, "WATER": 2, "EARTH": 3, "PRISON": 4, "FIRE": 5, "FIRE2": 7, "BRIDGE": 8, "FORTRESS": 9}
WARP_ID = {0: 140, 1: 142, 2: 141, 3: 136, 4: 139, 5: 137, 7: 137, 8: 135, 9: 138}
# Game flags that TEMPLE's own level function sets in its first-run branch (0x8002B6B8..0x8002B6DC: sh v1,2760(gp);
# sh v1,2904(gp); sw v0,0x800D8084). The other level functions test gp+2760 and, when it is 0, play a long story movie
# (0x8002B4E8 then 0x80050548) instead of going on to read their overlay. Warping sets them like a played TEMPLE would
# have. (address, width in bytes, value, label). Written once inside the window WARP_STATE_FROM..WARP_STATE_TO: the game
# zeroes them at frame ~4006 (New Game init, seen by polling them) and the level function enters at ~4063 on this route.
WARP_STATE = [(0x800D8074, 2, 1, "gp+2760"), (0x800D8104, 2, 1, "gp+2904"), (0x800D8084, 4, 1, "0x800D8084")]
WARP_STATE_FROM, WARP_STATE_TO = 4012, 4060   # New Game's init zeroes the flags at guest frame ~4006; the level function reads them at ~4063
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


def rd_word(dbg, addr):
    return int.from_bytes(bytes.fromhex(rb.call_ok(dbg, "read_ram", addr="0x%08X" % addr, len=4)["hex"]), "little")


def apply_warp(dbg, idx):
    """Copy dispatcher jump-table entry `idx` over entry 0 (TEMPLE) in guest RAM. Entry 0 is only read by the level
    dispatcher at 0x80032ED8 (lw v0,14608(at)); the thunk it points at passes the level function to the task spawner."""
    t_end = time.time() + 120               # the EXE is copied into RAM a little after the debug port opens
    while True:
        table = [rd_word(dbg, DISP_TABLE + 4 * i) for i in range(DISP_N)]
        if all(0x80032000 <= v < 0x80033000 for v in table) or time.time() > t_end:
            break
        time.sleep(0.25)
    for i, v in enumerate(table):
        if not 0x80032000 <= v < 0x80033000:
            raise rb.Fail("jump table entry %d = 0x%08X is not a thunk address; wrong build/disc? (table %s)" % (
                i, v, ["0x%08X" % x for x in table]))
    new = table[idx]
    for k in range(4):
        rb.call_ok(dbg, "write_ram", addr="0x%08X" % (DISP_TABLE + k), val=(new >> (8 * k)) & 0xFF)
    got = rd_word(dbg, DISP_TABLE)
    if got != new:
        raise rb.Fail("warp write did not stick: wanted 0x%08X read 0x%08X" % (new, got))
    return {"index": idx, "expected_overlay_id": WARP_ID[idx], "table_before": ["0x%08X" % x for x in table],
            "old_entry0": table[0], "new_entry0": new}


def write_mem(dbg, addr, val, n):
    for k in range(n):
        rb.call_ok(dbg, "write_ram", addr="0x%08X" % (addr + k), val=(val >> (8 * k)) & 0xFF)
    got = int.from_bytes(bytes.fromhex(rb.call_ok(dbg, "read_ram", addr="0x%08X" % addr, len=n)["hex"]), "little")
    if got != val:
        raise rb.Fail("write 0x%08X <- %d read back %d" % (addr, val, got))


def warp_state_phase(dbg):
    """Spin on the guest frame counter and write WARP_STATE inside the window WARP_STATE_FROM..WARP_STATE_TO."""
    t_end = time.time() + 15
    while time.time() < t_end:
        fr = rb.call_ok(dbg, "frame")["frame"]
        if fr > WARP_STATE_TO:
            raise rb.Fail("warp flags NOT set: frame %d is past %d (missed the window; rerun)" % (fr, WARP_STATE_TO))
        if fr >= WARP_STATE_FROM:
            before = {lab: rd_word(dbg, ad) & ((1 << (8 * n)) - 1) for ad, n, v, lab in WARP_STATE}
            for ad, n, v, lab in WARP_STATE:
                write_mem(dbg, ad, v, n)
            log("[%s] WARP: game flags set at frame %d (were %s)" % (now_s(), fr, before))
            return {"frame_written": fr, "values_before": before, "set": {lab: v for ad, n, v, lab in WARP_STATE}}
        time.sleep(0.01 if fr >= WARP_STATE_FROM - 40 else 0.15)
    raise rb.Fail("warp flags NOT set: frame counter never reached %d" % WARP_STATE_FROM)


def new_stats():
    return {"first_seen_frame": None, "first_seen_t": None, "polls_resident": 0, "resident_s": 0.0,
            "delta": {k: 0 for k in DELTA_KEYS}, "range_hits": 0, "entries_hit": set(), "hits_by_entry": {}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--interval", type=float, default=3.0)
    ap.add_argument("--port", type=int, default=4385)
    ap.add_argument("--boot-route", action="store_true")
    ap.add_argument("--warp", metavar="LEVEL", help="see the top of the file; implies --boot-route")
    ap.add_argument("--warp-no-state", action="store_true", help="with --warp: do not set the TEMPLE first-run flags (the level function may then play a story movie)")
    ap.add_argument("--shots", type=float, default=0)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--max-seconds", type=float, default=0)
    ap.add_argument("--fresh-saves", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--exe", default=sb.DBG_EXE)
    ap.add_argument("--disc", default=sb.DEF_DISC)
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    warp_idx = None
    if a.warp:
        w = a.warp.strip().upper()
        if w in WARP:
            warp_idx = WARP[w]
        elif w.isdigit() and int(w) in WARP_ID:
            warp_idx = int(w)
        else:
            print("setup: --warp must be one of %s or an index in %s" % (" ".join(WARP), sorted(WARP_ID))); return 2
        a.boot_route = True
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
    warp_info = None
    last_shot = 0.0
    warp_state_done = None
    idx_seen = []                                       # [frame, value of 0x800D76A8] when it changes
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
        warp_info = None
        if warp_idx is not None:
            warp_info = apply_warp(dbg, warp_idx)
            log("[%s] WARP: dispatcher entry 0 (TEMPLE) now points at index %d (%s), word 0x%08X; %s" % (
                now_s(), warp_idx, a.warp.upper(), warp_info["new_entry0"], "verified by read-back"))
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
            warp_pending = warp_info and warp_idx != 0 and not a.warp_no_state and not warp_state_done
            time.sleep(0.4 if (warp_pending and (last_frame or 0) >= 3300) else a.interval)
            if proc.poll() is not None:
                continue
            if warp_pending and (last_frame or 0) >= 3300:
                try:
                    warp_state_done = warp_state_phase(dbg)
                    warp_info["state_flags"] = warp_state_done
                except rb.Fail as e:
                    errors += 1
                    warp_state_done = warp_info["state_flags"] = {"error": str(e)}
                    log("[%s] WARP: %s" % (now_s(), e))
            tp = time.time()
            if a.shots and tp - last_shot >= a.shots and (last_frame or 0) >= 300:
                last_shot = tp
                os.makedirs(os.path.join(out, "shots"), exist_ok=True)
                try:
                    rb.call_ok(dbg, "screenshot", path=os.path.join(out, "shots", "t%04d_f%d.png" % (tp - t_start, last_frame or 0)))
                except rb.Fail:
                    pass
            rec = {"t": round(tp - t_start, 1), "wall": datetime.datetime.now().isoformat(timespec="seconds")}
            try:
                fr = rb.call_ok(dbg, "frame")["frame"]
                st = rb.call_ok(dbg, "overlay_loader_status")
                ent = rb.call_ok(dbg, "overlay_static_entries", addr_lo=WIN_LO, addr_hi=WIN_HI, limit=1024)
                head = bytes.fromhex(rb.call_ok(dbg, "read_ram", addr=WIN_LO, len=HEAD)["hex"])
                idx_now = rd_word(dbg, IDX_ADDR)
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
            if not idx_seen or idx_seen[-1][1] != idx_now:
                idx_seen.append([fr, idx_now])
            prev_tp = last_poll_t
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
                s["resident_s"] += (tp - prev_tp) if prev_tp else a.interval
                for k in DELTA_KEYS:
                    s["delta"][k] += max(0, d[k])
                s["range_hits"] += sum(grew.values())
                for ad, g in grew.items():
                    s["entries_hit"].add(ad)
                    s["hits_by_entry"][ad] = s["hits_by_entry"].get(ad, 0) + g
            prev_status, prev_hits = status, hits_now
            rec.update({"frame": fr, "level_index": idx_now, "window_id": rid, "resident": cur, "level_entries": new_lv, "status": status,
                        "range_hits": ent.get("range_hits"), "range_hit_entries": ent.get("range_hit_entries"),
                        "top": ent.get("top", [])[:5]})
            jl.write(json.dumps(rec) + "\n")
            if not a.quiet and time.time() - last_hb >= 30:
                last_hb = time.time()
                log("[%s] t=%6.1fs frame %d resident=%s range_hits=%s hit_entries=%s fallback=%s" % (
                    now_s(), tp - t_start, fr, ("%d %s" % (cur, IDS[cur])) if cur else "none", ent.get("range_hits"),
                    ent.get("range_hit_entries"), status["dispatch_interp_fallback"]))
    except rb.Fail as e:
        reason = "setup failed: %s" % e
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
               "warp": ({"level": a.warp.upper(), "natural_play": False, **warp_info} if warp_info else None),
               "level_index_changes": idx_seen,
               "faults": faults, "crash_like_log_lines": crashy[-20:]}
    json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=1)

    lines = ["", "=== overlay coverage summary (%s) ===" % out,
             "end: %s; exit code %s; %d polls (%d errors); last frame %s; %.0f s" % (reason, exit_code, polls, errors, last_frame, summary["duration_s"]),
             ("WARPED run (not natural play): %s -> dispatcher index %d, expected overlay id %d; faults below may come from the warp" % (
                 a.warp.upper(), warp_info["index"], warp_info["expected_overlay_id"])) if warp_info else "natural run (no warp)",
             "gp+252 (0x800D76A8) changes [frame, value]: %s" % idx_seen,
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
