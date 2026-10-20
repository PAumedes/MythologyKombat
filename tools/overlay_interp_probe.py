#!/usr/bin/env python3
r"""T2.17 investigation: what do the interpreter fallbacks, the static CRC misses and the FIRE/WIND entries look like? (stdlib only)

Run:  <RETRO_TOOLS_DIR>\python\python.exe -I tools\overlay_interp_probe.py [options]

  --frames a,b     guest frames at which to sample (default 6100,7300); the game is paused for each sample
  --out FILE       result JSON (default work\overlay_interp_probe.json)
  --port N         debug port (default 4386)

Plays the boot_to_menu route on the debug build (--headless, cold boot, fresh memory card dir) and, at each frame:
  * `dirty_ram_stats` per_pc = the interpreted entry PCs (physical), with hits, instructions and the external $ra;
  * `overlay_loader_status` counters and `overlay_static_entries` over the overlay window (limit 1024);
  * RAM words at each interpreted PC and at the caller (the jal before $ra).
Offline (no game needed): disassembles, with a small decoder, the entry instructions of every image listed in
aot\overlays.json from the .OVR bytes on the disc (shows what "lands on lui" means), and counts, from
generated\AOT_STATIC_AUDIT.json, how many entry addresses are shared by more than one image (CRC-miss candidates).
Output is under work\ (git-ignored). Exit 0 if it ran.
"""
import argparse, collections, json, os, shutil, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smoke_boot as sb              # noqa: E402
import run_boot_route as rb          # noqa: E402
import overlay_runtime_check as orc  # noqa: E402

ROOT = sb.ROOT
LO, HI = "0x80130FF8", "0x8013C720"
BASE = 0x80130FF8
REG = ["zero", "at", "v0", "v1", "a0", "a1", "a2", "a3", "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "s0", "s1", "s2", "s3",
       "s4", "s5", "s6", "s7", "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra"]


def s16(x):
    return x - 0x10000 if x & 0x8000 else x


def dis(w, pc):
    op, rs, rt, rd, sh, fn = w >> 26, (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31, (w >> 6) & 31, w & 63
    im = w & 0xFFFF
    r = REG
    if w == 0:
        return "nop"
    if op == 0:
        n = {0: "sll", 2: "srl", 3: "sra"}
        if fn in n:
            return "%s %s,%s,%d" % (n[fn], r[rd], r[rt], sh)
        if fn == 8:
            return "jr %s" % r[rs]
        if fn == 9:
            return "jalr %s,%s" % (r[rd], r[rs])
        n3 = {0x21: "addu", 0x23: "subu", 0x24: "and", 0x25: "or", 0x26: "xor", 0x27: "nor", 0x2A: "slt", 0x2B: "sltu", 0x20: "add"}
        if fn in n3:
            return "%s %s,%s,%s" % (n3[fn], r[rd], r[rs], r[rt])
    if op in (2, 3):
        return "%s 0x%08X" % ("j" if op == 2 else "jal", ((pc + 4) & 0xF0000000) | ((w & 0x3FFFFFF) << 2))
    if op in (4, 5):
        return "%s %s,%s,0x%08X" % ("beq" if op == 4 else "bne", r[rs], r[rt], pc + 4 + (s16(im) << 2))
    if op in (6, 7):
        return "%s %s,0x%08X" % ("blez" if op == 6 else "bgtz", r[rs], pc + 4 + (s16(im) << 2))
    n = {8: "addi", 9: "addiu", 10: "slti", 11: "sltiu", 12: "andi", 13: "ori", 14: "xori"}
    if op in n:
        return "%s %s,%s,%s" % (n[op], r[rt], r[rs], ("0x%X" % im) if op in (12, 13, 14) else str(s16(im)))
    if op == 15:
        return "lui %s,0x%X" % (r[rt], im)
    m = {0x20: "lb", 0x21: "lh", 0x23: "lw", 0x24: "lbu", 0x25: "lhu", 0x28: "sb", 0x29: "sh", 0x2B: "sw"}
    if op in m:
        return "%s %s,%d(%s)" % (m[op], r[rt], s16(im), r[rs])
    return ".word 0x%08X" % w


def dis_block(data, base, n):
    return ["0x%08X  %08X  %s" % (base + 4 * i, struct.unpack_from("<I", data, 4 * i)[0],
                                    dis(struct.unpack_from("<I", data, 4 * i)[0], base + 4 * i))
            for i in range(min(n, len(data) // 4))]


def hx(v):
    return int(v, 16) if isinstance(v, str) else int(v)


def static_part(ovr):
    prof = json.load(open(os.path.join(ROOT, "aot", "overlays.json")))
    out = []
    for im in prof["images"]:
        for ex in im["extents"]:
            name = os.path.basename(ex["file"])
            oid = [i for i, o in ovr.items() if o["name"] == name]
            if not oid:
                continue
            data = ovr[oid[0]]["data"]
            for e in ex.get("entries", []):
                off = hx(e) - BASE
                out.append({"image": name, "id": oid[0], "entry": e, "listing": dis_block(data[off:off + 64], hx(e), 12)})
    aud = json.load(open(os.path.join(ROOT, "generated", "AOT_STATIC_AUDIT.json")))
    by = collections.defaultdict(set)
    for v in aud["variants"]:
        by[v["entry"]].add(v["matched_recipe"].split("@")[0].split("-", 1)[1])
    shared = {k: sorted(v) for k, v in by.items() if len(v) > 1}
    return out, {"variants": len(aud["variants"]), "entry_addresses": len(by), "shared_by_2plus_images": len(shared),
                 "max_images_on_one_entry": max(len(v) for v in by.values()),
                 "shared_with_temple": sum(1 for v in shared.values() if any(x.endswith("TEMPLE.OVR") for x in v))}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--frames", default="6100,7300")
    ap.add_argument("--out", default=os.path.join(rb.WORK, "overlay_interp_probe.json"))
    ap.add_argument("--port", type=int, default=4386)
    a = ap.parse_args()
    frames = sorted(int(x) for x in a.frames.split(","))
    ovr, _levels, _ = orc.load_expected()
    entries_listing, shared = static_part(ovr)
    for e in entries_listing:
        print("== %s (id %d) entry %s" % (e["image"], e["id"], e["entry"]))
        for l in e["listing"][:6]:
            print("   " + l)
    print("audit variants: %s" % json.dumps(shared))

    route = rb.load_route(rb.DEF_ROUTE)
    exe = sb.DBG_EXE
    d = os.path.dirname(exe)
    sv = os.path.join(rb.WORK, "interp_probe_saves")
    shutil.rmtree(sv, ignore_errors=True)
    os.makedirs(sv)
    p = subprocess.Popen([exe, "--disc", sb.DEF_DISC, "--game", os.path.join(d, "game.toml"), "--no-launcher", "--headless",
                          "--debug-port", str(a.port), "--memcard-dir", sv], cwd=d, stdout=subprocess.DEVNULL,
                         stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    dbg = sb.Dbg(a.port)
    samples = []
    try:
        t0 = time.time()
        while True:
            if p.poll() is not None:
                print("game exited during startup"); return 1
            try:
                dbg.connect(); break
            except OSError:
                if time.time() - t0 > 60:
                    print("debug port never opened"); return 1
                time.sleep(0.2)
        rb.call_ok(dbg, "input_route_clear")
        for c in route["cmds"]:
            rb.call_ok(dbg, "input_route_append", frames=c["frames"], buttons=c["buttons"])
        rb.call_ok(dbg, "input_route_start", at_frame=route["first"])
        for n in frames:
            while rb.call_ok(dbg, "frame")["frame"] < n:
                time.sleep(0.1)
            rb.call_ok(dbg, "host_pause", on=1)
            time.sleep(0.5)
            fr = rb.call_ok(dbg, "frame")["frame"]
            ds = rb.call_ok(dbg, "dirty_ram_stats", per_pc=1, timeout=60)
            st = rb.call_ok(dbg, "overlay_loader_status")
            en = rb.call_ok(dbg, "overlay_static_entries", addr_lo=LO, addr_hi=HI, limit=1024)
            pcs = []
            for r in ds.get("per_pc", []):
                pc, ra = hx(r["pc"]), hx(r["ext_ra"])
                code = bytes.fromhex(rb.call_ok(dbg, "read_ram", addr="0x%08X" % (0x80000000 | pc), len=96)["hex"])
                call_pc = ra - 8
                caller = bytes.fromhex(rb.call_ok(dbg, "read_ram", addr="0x%08X" % (0x80000000 | (call_pc & 0x1FFFFFFF)), len=16)["hex"])
                pcs.append({"pc": r["pc"], "hits": r["hits"], "insns": r["insns"], "entries": r["entries"], "ext_ra": r["ext_ra"],
                            "code": dis_block(code, pc, 24),
                            "caller": dis_block(caller, call_pc, 4)})
            samples.append({"frame": fr, "dirty_ram": {k: ds[k] for k in ("blocks_run", "insns_run", "aborts", "native_handoffs",
                                                                           "dirty_bitmap", "per_pc_matching", "text_native_blocked",
                                                                           "text_diverged_pages", "text_exact_mismatches") if k in ds},
                            "loader": {k: st.get(k) for k in ("static_checks", "static_hits", "static_variant_misses", "static_crc_misses",
                                                              "static_rehashes", "static_address_misses", "dispatch_interp_fallback",
                                                              "segment_alias_interp", "segment_native", "loads", "regions")},
                            "window": {k: en[k] for k in ("entries", "range_entries", "range_variants", "range_hits", "range_hit_entries")},
                            "hit_entries_with_variants_gt1": sum(1 for t in en.get("top", []) if t.get("variants", 1) > 1),
                            "sum_other_variants_over_hit_entries": sum(t.get("variants", 1) - 1 for t in en.get("top", [])),
                            "hit_entries_listed": len(en.get("top", [])),
                            "per_pc": pcs})
            s = samples[-1]
            print("frame %d: fallback=%s alias=%s crc_miss=%s rehash=%s blocks=%s insns=%s range_hits=%s hit_entries=%s (entries with >1 variant: %d; sum of other variants %d over %d listed)" % (
                fr, s["loader"]["dispatch_interp_fallback"], s["loader"]["segment_alias_interp"], s["loader"]["static_crc_misses"],
                s["loader"]["static_rehashes"], s["dirty_ram"]["blocks_run"], s["dirty_ram"]["insns_run"], s["window"]["range_hits"],
                s["window"]["range_hit_entries"], s["hit_entries_with_variants_gt1"], s["sum_other_variants_over_hit_entries"], s["hit_entries_listed"]))
            for q in pcs:
                print("   interp pc %s hits %d insns %d entries %d ext_ra %s" % (q["pc"], q["hits"], q["insns"], q["entries"], q["ext_ra"]))
            rb.call_ok(dbg, "host_pause", on=0)
        if len(samples) >= 2:
            x, y = samples[0], samples[-1]
            df = y["frame"] - x["frame"]
            print("between frames %d and %d: fallback +%d (%.2f/frame), insns +%d (%.0f/frame), crc misses +%d, hits +%d" % (
                x["frame"], y["frame"], y["loader"]["dispatch_interp_fallback"] - x["loader"]["dispatch_interp_fallback"],
                (y["loader"]["dispatch_interp_fallback"] - x["loader"]["dispatch_interp_fallback"]) / df,
                y["dirty_ram"]["insns_run"] - x["dirty_ram"]["insns_run"], (y["dirty_ram"]["insns_run"] - x["dirty_ram"]["insns_run"]) / df,
                y["loader"]["static_crc_misses"] - x["loader"]["static_crc_misses"],
                y["loader"]["static_hits"] - x["loader"]["static_hits"]))
    finally:
        try:
            dbg.call("quit")
        except Exception:
            pass
        try:
            p.wait(timeout=15)
        except subprocess.TimeoutExpired:
            sb.kill_pid(p.pid)
    json.dump({"schema": 1, "static_entries": entries_listing, "audit_shared": shared, "samples": samples},
              open(a.out, "w"), indent=1)
    print("result written: %s" % os.path.relpath(a.out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
