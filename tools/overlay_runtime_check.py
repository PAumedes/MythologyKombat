#!/usr/bin/env python3
"""T2.13: runtime proof that RAM at the overlay window equals the .OVR file bytes (stdlib only).

Run:  <RETRO_TOOLS_DIR>\\python\\python.exe -I tools\\overlay_runtime_check.py [options]

  --runs N        cold boots to run (default 2); the invariant result must be identical in every run
  --route R       input route (default tests\\replays\\routes\\boot_to_menu.json, which reaches the first level)
  --out FILE      result JSON (default work\\overlay_runtime.json; no absolute paths, no timestamps)
  --shots DIR     debug only: save a PNG at the pause (DIR must be under work\\). Agent evidence, never committed.
  --max-frame N   give up if no overlay load is seen by this guest frame (default 12000)
  --port N        debug port (default 4383; 4370 and 4381 belong to the Release game / other tools)

What it does (debug build work\\build-dbg\\MythologyKombat.exe --headless, fresh memory card dir, cold boot):
  1. The native debug server has NO pc_break (that family is DuckStation-only; TCP_COMMANDS.md). Function entries
     are captured instead: `fn_filter` makes the server record a0..a3, $ra and the frame for every entry of the
     chosen address range into the `fn_entry` ring.
  2. Phase 1: the filter is read_file 0x800861D4 only. The tool polls `fn_entry_dump` until read_file is entered
     with an overlay id (134..143). That gives the id and the scratch buffer (a1).
  3. Phase 2: the filter is switched to the memcpy wrapper 0x8009F31C only. The tool polls until it is entered
     with a0 inside the overlay window, then sends `host_pause` at once (the pause lands on a frame boundary,
     so the guest has run on for a frame or two; step 5 accounts for that).
  4. While paused: `read_ram` of the whole overlay window 0x80130FF8..0x8013C720, and the write-transition
     ring (`wtrace_trans_dump`). The ring is armed at launch with PSX_WTRACE_BOOT_RANGES over the window. It
     keeps every value-changing CPU store into the window with old value, new value, store pc, $ra, $sp.
  5. Offline: undo the ring entries newer than the last memcpy store (in reverse order) to get the window
     as it was when the memcpy finished, and undo those from the first memcpy store on to get it as it was when
     the memcpy started (source buffer included). Every undo step checks that the byte currently held equals
     the entry's new value (an untraced write, such as DMA, would show up as an inconsistency).
  6. Compare with the .OVR file bytes read from the disc image (by LBA and size from work\\disc_files.json):
       - source buffer before the memcpy == file bytes (what the CD read produced)
       - window after the memcpy == file bytes, SHA-256 compared with work\\overlay_facts.json
       - RAM at the pause == file bytes, and every differing byte is explained by a later store
       - a forward byte-by-byte copy, simulated on the state before the memcpy, gives the file bytes (overlap)

Exit codes: 0 proof holds and runs agree, 1 proof failed / run failure, 2 setup error.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smoke_boot as sb          # noqa: E402  (Dbg, kill_pid, pid_is_ours, DBG_EXE, DEF_DISC)
import run_boot_route as rb      # noqa: E402  (load_route, call_ok, Fail, DEF_ROUTE)
import disc_identify as di       # noqa: E402  (cue parser, raw sector reader)

ROOT = sb.ROOT
WORK = os.path.join(ROOT, "work")
RT_DIR = os.path.join(WORK, "overlay_rt")
SAVES = os.path.join(WORK, "overlay_rt_saves")
PIDFILE = os.path.join(RT_DIR, "pid.txt")
FACTS = os.path.join(WORK, "overlay_facts.json")
FILES = os.path.join(WORK, "disc_files.json")

WIN_LO, WIN_HI = 0x80130FF8, 0x8013C720
GET_SIZE, READ_FILE, ALLOC, MEMCPY = 0x800861BC, 0x800861D4, 0x800865C0, 0x8009F31C
DEST_PTR = 0x80015134
OVL_IDS = range(134, 144)
ROM_BASE = 0xBFC00000


def log(m):
    print(m, flush=True)


def hx(s):
    return int(s, 16)


def h8(v):
    return "0x%08X" % v


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


# ------------------------------------------------------------------ disc / facts
def open_disc():
    d = os.path.join(ROOT, "ps1_game")
    cues = sorted(x for x in os.listdir(d) if x.lower().endswith(".cue"))
    if len(cues) != 1:
        raise SystemExit("setup: expected one .cue in ps1_game")
    fl = di.parse_cue(os.path.join(d, cues[0]))
    t = fl[0]["tracks"][0]
    return di.Track1Reader(os.path.join(d, fl[0]["name"]), t["mode"], t["indexes"][1])


def load_expected():
    """id -> {name, size, sha256, bytes}; level functions; all from the T2.12 outputs and the disc."""
    for p in (FACTS, FILES):
        if not os.path.isfile(p):
            raise SystemExit("setup: %s missing (run tools\\overlay_facts.py / tools\\disc_list.py first)" % p)
    facts = json.load(open(FACTS))
    files = {f["path"]: f for f in json.load(open(FILES))["files"]}
    rd = open_disc()
    ovr = {}
    for o in facts["ovr_files"]:
        f = files[o["path"]]
        data = rd.read_extent(f["lba"], f["size_bytes"])[:o["size"]]
        if sha(data) != o["sha256"]:
            raise SystemExit("setup: %s bytes read from the disc do not match overlay_facts.json sha256" % o["path"])
        ovr[o["id"]] = {"name": o["name"], "path": o["path"], "size": o["size"], "sha256": o["sha256"], "data": data}
    levels = []
    for L in facts["levels"]:
        levels.append({"name": L["name"], "start": hx(L["start"]), "end": hx(L["end_exclusive"]),
                       "memcpy_calls": [hx(x) for x in L["memcpy_calls"]],
                       "dest_pointer_reads": [hx(x) for x in L["dest_pointer_reads"]],
                       "ids": L["overlay_ids_read"]})
    return ovr, levels, facts["boot_exe"]["sha256"]


# ------------------------------------------------------------------ process control
def launch(port, route_path, ranges):
    exe, disc = os.path.abspath(sb.DBG_EXE), os.path.abspath(sb.DEF_DISC)
    for p, what in ((exe, "exe"), (disc, "disc image")):
        if not os.path.isfile(p):
            raise SystemExit("setup: %s not found: %s" % (what, p))
    if not sb.exe_has_debug_server(exe):
        raise SystemExit("setup: exe was built without PSX_DEBUG_TOOLS; use work\\build-dbg")
    try:
        import socket
        socket.create_connection(("127.0.0.1", port), timeout=1).close()
        raise SystemExit("setup: port %d already in use; pick another with --port" % port)
    except OSError:
        pass
    os.makedirs(RT_DIR, exist_ok=True)
    if os.path.isfile(PIDFILE):
        try:
            old = int(open(PIDFILE).read().strip())
            if sb.pid_is_ours(old):
                raise SystemExit("setup: stale run pid %d still alive; kill it (taskkill /F /PID %d) first" % (old, old))
        except ValueError:
            pass
    shutil.rmtree(SAVES, ignore_errors=True)
    os.makedirs(SAVES, exist_ok=True)
    exe_dir = os.path.dirname(exe)
    cmd = [exe, "--disc", disc, "--game", os.path.join(exe_dir, "game.toml"), "--no-launcher",
           "--headless", "--debug-port", str(port), "--memcard-dir", SAVES]
    env = dict(os.environ)
    env["PSX_DEBUG_FMV_QUIET"] = "0"
    env["PSX_WTRACE_BOOT_RANGES"] = ranges
    lf = open(os.path.join(RT_DIR, "run.log"), "wb")
    proc = subprocess.Popen(cmd, cwd=exe_dir, stdout=lf, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, env=env)
    open(PIDFILE, "w").write(str(proc.pid))
    return proc, lf


def shutdown(dbg, proc, lf):
    try:
        dbg.call("host_pause", on=0)
    except Exception:
        pass
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


# ------------------------------------------------------------------ polling
def fn_dump(dbg, seq_lo, lo, hi):
    r = rb.call_ok(dbg, "fn_entry_dump", seq_lo=seq_lo, count=2048, addr_lo=h8(lo), addr_hi=h8(hi))
    return r


def poll_entries(dbg, state, lo, hi):
    """Yield entries of [lo,hi) newer than state['seq'] (state is advanced)."""
    out = []
    while True:
        r = fn_dump(dbg, state["seq"], lo, hi)
        ents = r["entries"]
        out += ents
        if len(ents) >= 2048:  # page full; there may be more
            state["seq"] = ents[-1]["seq"] + 1
            continue
        state["seq"] = max(state["seq"], r["seq_hi"])
        return out


def trans_all(dbg, seq_lo):
    ents = []
    s = seq_lo
    while True:
        r = rb.call_ok(dbg, "wtrace_trans_dump", seq_lo=s, count=2048, timeout=60)
        e = r["entries"]
        ents += e
        if len(e) < 2048:
            return ents
        s = e[-1]["seq"] + 1


# ------------------------------------------------------------------ one run
def one_run(a, ovr, levels):
    route = rb.load_route(a.route)
    lo_phys, hi_phys = WIN_LO & 0x1FFFFFFF, WIN_HI & 0x1FFFFFFF
    proc, lf = launch(a.port, a.route, "0x%X-0x%X" % (lo_phys, hi_phys))
    dbg = sb.Dbg(a.port)
    t0 = time.time()
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
        rb.call_ok(dbg, "input_route_clear")
        for c in route["cmds"]:
            rb.call_ok(dbg, "input_route_append", frames=c["frames"], buttons=c["buttons"])
        r = rb.call_ok(dbg, "input_route_start", at_frame=route["first"])
        if r.get("start_frame") != route["first"]:
            raise rb.Fail("route started too late (start_frame=%s)" % r.get("start_frame"))

        # --- phase 1: read_file only
        rb.call_ok(dbg, "fn_filter", lo=h8(READ_FILE), hi=h8(READ_FILE + 4))
        st = {"seq": rb.call_ok(dbg, "fn_stats")["entry_total"]}
        reads = []
        rf = None
        while rf is None:
            if proc.poll() is not None:
                raise rb.Fail("game died while waiting for an overlay read")
            for e in poll_entries(dbg, st, READ_FILE, READ_FILE + 4):
                rid = hx(e["a0"])
                reads.append({"id": rid, "buf": hx(e["a1"]), "ra": hx(e["ra"]), "frame": e["frame"]})
                if rid in OVL_IDS:
                    rf = reads[-1]
                    break
            if rf is None:
                if rb.call_ok(dbg, "frame")["frame"] > a.max_frame:
                    raise rb.Fail("no overlay read_file by frame %d" % a.max_frame)
                time.sleep(0.002)
        # --- phase 2: memcpy wrapper only. The CD read takes several frames, so there is time to switch.
        tmark = rb.call_ok(dbg, "wtrace_trans_stats")
        rb.call_ok(dbg, "fn_filter", lo=h8(MEMCPY), hi=h8(MEMCPY + 4))
        st = {"seq": rb.call_ok(dbg, "fn_stats")["entry_total"]}
        hit = None
        while hit is None:
            if proc.poll() is not None:
                raise rb.Fail("game died while waiting for the memcpy")
            for e in poll_entries(dbg, st, MEMCPY, MEMCPY + 4):
                if WIN_LO <= hx(e["a0"]) < WIN_HI:
                    hit = e
                    break
            if hit is None:
                time.sleep(0.001)
        t_pause = time.time()
        pauses = []
        for attempt in range(40):
            rb.call_ok(dbg, "host_pause", on=1)
            prev = -1
            for _ in range(100):
                time.sleep(0.05)
                f = rb.call_ok(dbg, "frame")["frame"]
                if f == prev:
                    break
                prev = f
            regs = rb.call_ok(dbg, "get_registers")
            pc = hx(regs["pc"])
            in_rom = (pc & 0x1FFFFFFF) >= 0x1FC00000   # inside the BIOS ROM: the memcpy loop (or a handler) is running
            pauses.append({"frame": prev, "pc": h8(pc), "in_bios_rom": in_rom})
            if not in_rom:
                break
            # the pause landed inside the BIOS memcpy loop: let the guest run on and pause again
            rb.call_ok(dbg, "host_pause", on=0)
            while rb.call_ok(dbg, "frame")["frame"] <= prev:
                time.sleep(0.002)
        else:
            raise rb.Fail("could not pause outside the BIOS memcpy loop")
        paused_frame = prev
        rb.call_ok(dbg, "fn_disable")

        # --- capture while paused
        win = bytes.fromhex(rb.call_ok(dbg, "read_ram", addr=h8(WIN_LO), len=WIN_HI - WIN_LO, timeout=60)["hex"])
        if len(win) != WIN_HI - WIN_LO:
            raise rb.Fail("short window read")
        a0, a1, a2 = hx(hit["a0"]), hx(hit["a1"]), hx(hit["a2"])
        ra = hx(hit["ra"])
        code = {}
        code["jal"] = rb.call_ok(dbg, "read_ram", addr=h8(ra - 8), len=4)["hex"]
        dest_ptr_word = rb.call_ok(dbg, "read_ram", addr=h8(DEST_PTR), len=4)["hex"]
        if a.shots:
            rb.call_ok(dbg, "screenshot", path=os.path.join(a.shots, "paused_f%d.png" % paused_frame))
        ents = trans_all(dbg, tmark["total"])
        stats = rb.call_ok(dbg, "wtrace_trans_stats")
        if stats.get("env_error"):
            raise rb.Fail("wtrace boot ranges refused: %s" % stats["env_error"])
        if stats["oldest_seq"] != 0:
            raise rb.Fail("write-transition ring wrapped (oldest_seq %s)" % stats["oldest_seq"])
        return {"rf": rf, "reads": reads, "hit": hit, "win": win, "ents": ents, "code": code,
                "dest_ptr_word": dest_ptr_word, "paused_frame": paused_frame, "pauses": pauses,
                "pause_latency_s": time.time() - t_pause, "wall_s": time.time() - t0}
    finally:
        shutdown(dbg, proc, lf)


# ------------------------------------------------------------------ analysis
def analyse(cap, ovr, levels, boot_sha):
    hit, rf, win, ents = cap["hit"], cap["rf"], cap["win"], cap["ents"]
    a0, a1, a2 = hx(hit["a0"]), hx(hit["a1"]), hx(hit["a2"])
    ra, hit_frame = hx(hit["ra"]), hit["frame"]
    o = ovr[rf["id"]]
    out = {"checks": {}}
    ck = out["checks"]

    # which level function / call site
    call_pc = ra - 8
    lvl = [L for L in levels if call_pc in L["memcpy_calls"]]
    rlvl = [L for L in levels if L["start"] <= rf["ra"] < L["end"]]
    ck["memcpy_call_site_is_known_level_site"] = len(lvl) == 1
    ck["read_file_and_memcpy_in_same_level_function"] = len(lvl) == 1 and len(rlvl) == 1 and lvl[0] is rlvl[0]
    ck["id_is_one_of_the_ids_the_level_function_reads"] = len(lvl) == 1 and rf["id"] in lvl[0]["ids"]
    jal = int.from_bytes(bytes.fromhex(cap["code"]["jal"]), "little")
    ck["instruction_at_call_pc_is_jal_memcpy"] = jal == (0x0C000000 | ((MEMCPY >> 2) & 0x03FFFFFF))
    ck["dest_pointer_word_is_window_base"] = int.from_bytes(bytes.fromhex(cap["dest_ptr_word"]), "little") == WIN_LO
    ck["a0_is_window_base"] = a0 == WIN_LO
    ck["a2_is_get_size_of_id"] = a2 == o["size"]
    ck["read_file_buffer_is_memcpy_source"] = rf["buf"] == a1

    # memcpy stores in the transition ring
    E = []
    for e in ents:
        E.append((e["seq"], hx(e["addr"]) | 0x80000000, hx(e["old"]), hx(e["new"]), hx(e["pc"]), hx(e["ra"]),
                  hx(e["sp"]), e["w"], e["frame"]))
    cp = [x for x in E if x[5] == ra and x[4] >= ROM_BASE and a0 <= x[1] < a0 + a2]
    out["memcpy_stores"] = {"count": len(cp), "store_pcs": sorted({h8(x[4]) for x in cp}),
                            "widths": sorted({x[7] for x in cp}),
                            "sp": sorted({h8(x[6]) for x in cp}),
                            "ra": sorted({h8(x[5]) for x in cp}),
                            "first_frame": min(x[8] for x in cp) if cp else None,
                            "last_frame": max(x[8] for x in cp) if cp else None,
                            "forward_addresses": all(cp[i][1] <= cp[i + 1][1] for i in range(len(cp) - 1)) if cp else None,
                            "note": "value-changing stores only; a byte that already held the right value is not logged"}
    if not cp:
        out["fail"] = "no memcpy stores found in the write-transition ring"
        return out, None
    first_cp, last_cp = min(x[0] for x in cp), max(x[0] for x in cp)
    # undo helper
    def undo(mem, seq_min):
        bad = 0
        n = 0
        for x in reversed(E):
            if x[0] < seq_min:
                break
            _, addr, old, new, _, _, _, w, _ = x
            off = addr - WIN_LO
            if not (0 <= off and off + w <= len(mem)):
                continue
            cur = int.from_bytes(mem[off:off + w], "little")
            if cur != (new & ((1 << (8 * w)) - 1)):
                bad += 1
            mem[off:off + w] = (old & ((1 << (8 * w)) - 1)).to_bytes(w, "little")
            n += 1
        return n, bad

    now = bytearray(win)
    after = bytearray(now)
    n_after, bad_after = undo(after, last_cp + 1)
    before = bytearray(now)
    n_before, bad_before = undo(before, first_cp)
    out["undo"] = {"entries_undone_after_memcpy": n_after, "inconsistent_after": bad_after,
                   "entries_undone_to_memcpy_start": n_before, "inconsistent_before": bad_before}
    ck["undo_consistent_no_untraced_writes"] = bad_after == 0 and bad_before == 0

    fdata = o["data"]
    d_off, s_off = a0 - WIN_LO, a1 - WIN_LO
    src_inside = 0 <= s_off and s_off + a2 <= len(before)
    out["overlap"] = {"a0": h8(a0), "a1": h8(a1), "a2": h8(a2), "dest_end_exclusive": h8(a0 + a2),
                      "src_end_exclusive": h8(a1 + a2), "src_minus_dest": a1 - a0,
                      "ranges_overlap": max(a0, a1) < min(a0 + a2, a1 + a2),
                      "overlap_bytes": max(0, min(a0 + a2, a1 + a2) - max(a0, a1)),
                      "dest_below_source": a0 <= a1,
                      "source_inside_traced_window": src_inside}
    if not src_inside:
        out["fail"] = "source buffer outside the traced window; cannot reconstruct the pre-memcpy state"
        return out, None
    src_before = bytes(before[s_off:s_off + a2])
    ck["source_buffer_before_memcpy_equals_file"] = src_before == fdata
    # simulate a forward byte copy (what the byte-store loop does) and a memmove on the pre-memcpy state
    sim = bytearray(before)
    for i in range(a2):
        sim[d_off + i] = sim[s_off + i]
    mm = bytearray(before)
    mm[d_off:d_off + a2] = bytes(before[s_off:s_off + a2])
    ck["simulated_forward_copy_equals_file"] = bytes(sim[d_off:d_off + a2]) == fdata
    ck["simulated_forward_copy_equals_memmove"] = sim == mm
    dest_after = bytes(after[d_off:d_off + a2])
    ck["window_after_memcpy_equals_file"] = dest_after == fdata
    ck["window_after_memcpy_equals_simulated_copy"] = dest_after == bytes(sim[d_off:d_off + a2])
    ck["window_after_memcpy_sha256_equals_facts_sha256"] = sha(dest_after) == o["sha256"]
    # RAM at the pause
    now_dest = bytes(now[d_off:d_off + a2])
    diff = [i for i in range(a2) if now_dest[i] != fdata[i]]
    covered = set()
    for x in E:
        if x[0] > last_cp:
            for k in range(x[7]):
                covered.add(x[1] + k)
    unexplained = [i for i in diff if (a0 + i) not in covered]
    wpcs = {}
    for x in E:
        if x[0] > last_cp and any(a0 <= x[1] + k < a0 + a2 for k in range(x[7])):
            wpcs[h8(x[4])] = wpcs.get(h8(x[4]), 0) + 1
    out["at_pause"] = {"paused_frame": cap["paused_frame"], "memcpy_hit_frame": hit_frame,
                       "window_sha256_first_a2_bytes": sha(now_dest),
                       "differs_from_file": bool(diff), "differing_bytes": len(diff),
                       "first_differing_offset": (diff[0] if diff else None),
                       "last_differing_offset": (diff[-1] if diff else None),
                       "all_differences_explained_by_later_stores": not unexplained,
                       "unexplained_differing_bytes": len(unexplained),
                       "later_store_pcs_into_image_range": dict(sorted(wpcs.items()))}
    ck["ram_at_pause_equals_file_or_every_difference_explained_by_a_later_store"] = not unexplained
    out["hashes"] = {"file_sha256": o["sha256"], "window_after_memcpy_sha256": sha(dest_after),
                     "window_before_memcpy_src_sha256": sha(src_before),
                     }
    # facts about the heap header just below the scratch buffer (runtime values, no disc content)
    hdr_lo = 0x80130FFC
    if hdr_lo >= WIN_LO and a1 > hdr_lo and a1 - hdr_lo <= 64:
        hw = [int.from_bytes(before[hdr_lo - WIN_LO + k:hdr_lo - WIN_LO + k + 4], "little") for k in range(0, a1 - hdr_lo, 4)]
        out["heap_words_between_0x80130FFC_and_source_before_memcpy"] = [h8(v) for v in hw]
        hw2 = [int.from_bytes(after[hdr_lo - WIN_LO + k:hdr_lo - WIN_LO + k + 4], "little") for k in range(0, a1 - hdr_lo, 4)]
        out["heap_words_between_0x80130FFC_and_source_after_memcpy"] = [h8(v) for v in hw2]
    return out, ck


def invariant(a, rf, hit, an):
    """The part of a run that must be identical in every cold boot."""
    return {
        "read_file": {"id": rf["id"], "buffer_a1": h8(rf["buf"]), "ra": h8(rf["ra"]), "frame": rf["frame"]},
        "memcpy": {"a0": hit["a0"], "a1": hit["a1"], "a2": hit["a2"], "a2_decimal": hx(hit["a2"]),
                   "a3": hit["a3"], "ra": hit["ra"], "s0": hit["s0"], "s1": hit["s1"], "s2": hit["s2"],
                   "s3": hit["s3"], "frame": hit["frame"]},
        "analysis": an,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--route", default=rb.DEF_ROUTE)
    ap.add_argument("--out", default=os.path.join(WORK, "overlay_runtime.json"))
    ap.add_argument("--shots")
    ap.add_argument("--max-frame", type=int, default=12000)
    ap.add_argument("--port", type=int, default=4383)
    a = ap.parse_args()
    if a.port in (4370, 4371, 4380, 4381):
        raise SystemExit("setup: port %d is reserved for other tools / the Release game" % a.port)
    if a.shots:
        a.shots = os.path.abspath(a.shots)
        if not a.shots.lower().startswith(WORK.lower() + os.sep):
            raise SystemExit("setup: --shots must be under work\\")
        os.makedirs(a.shots, exist_ok=True)
    ovr, levels, boot_sha = load_expected()
    results, extras = [], []
    try:
        for i in range(a.runs):
            log("=== cold-boot run %d of %d ===" % (i + 1, a.runs))
            cap = one_run(a, ovr, levels)
            an, ck = analyse(cap, ovr, levels, boot_sha)
            obs = an.pop("at_pause", None)   # depends on where the pause landed: informational only
            inv = invariant(a, cap["rf"], cap["hit"], an)
            results.append(inv)
            extras.append({"at_pause": obs, "paused_frame": cap["paused_frame"], "pauses": cap["pauses"], "wall_s": round(cap["wall_s"], 1)})
            h = cap["hit"]
            log("overlay read: id %d buf %s at frame %d (ra %s)" % (cap["rf"]["id"], h8(cap["rf"]["buf"]),
                                                                    cap["rf"]["frame"], h8(cap["rf"]["ra"])))
            log("memcpy entry: a0=%s a1=%s a2=%s (%d) ra=%s frame %d; paused on frame %d; run took %.1f s"
                % (h["a0"], h["a1"], h["a2"], hx(h["a2"]), h["ra"], h["frame"], cap["paused_frame"], cap["wall_s"]))
            if ck is None:
                log("FAIL: %s" % an.get("fail"))
                break
            for k, v in ck.items():
                log("  %-62s %s" % (k, "yes" if v else "NO"))
            log("  hashes: %s" % json.dumps(an["hashes"]))
            log("  at pause (informational): %s" % json.dumps(obs))
    except rb.Fail as e:
        log("RESULT: FAIL (%s)" % e)
        return 1
    if not results or "fail" in results[0]["analysis"]:
        return 1
    ok = all(all(r["analysis"]["checks"].values()) for r in results)
    det = all(json.dumps(r, sort_keys=True) == json.dumps(results[0], sort_keys=True) for r in results)
    o = ovr[results[0]["read_file"]["id"]]
    final = {"schema": 1, "tool": "tools/overlay_runtime_check.py",
             "method": "fn_entry ring (read_file, memcpy wrapper) + write-transition ring over the overlay window; pc_break does not exist in the native debug server",
             "overlay": {"id": results[0]["read_file"]["id"], "file": o["name"], "size": o["size"], "sha256": o["sha256"]},
             "window": {"lo": h8(WIN_LO), "hi_exclusive": h8(WIN_HI)},
             "runs": len(results), "runs_identical": det, "proof_holds": ok,
             "result": results[0],
             "run_observations_not_part_of_the_invariant": [
                 {"at_pause": e["at_pause"], "pauses": e["pauses"]} for e in extras]}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(final, open(a.out, "w"), indent=1, sort_keys=True)
    log("result written: %s" % a.out)
    log("pauses (informational, not part of the invariant): %s" % [e["pauses"] for e in extras])
    log("RESULT: %s; %d run(s) %s" % ("PROOF HOLDS" if ok else "PROOF FAILED", len(results),
                                      "identical" if det else "DIFFER"))
    return 0 if (ok and det) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(1)
