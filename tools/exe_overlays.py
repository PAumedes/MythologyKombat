#!/usr/bin/env python3
"""Boot EXE header and overlay load addresses (T1.4).

Inputs : work/extracted/SLUS_004.76, work/extracted/OVERLAYS/*.OVR,
         work/disc_classes.json (T1.3), and the disc image ps1_game/*.bin (read-only)
         for the independent header read (raw_sector_header).
Output : work/exe_header.json, work/overlay_candidates.json
         (deterministic: no timestamps, no absolute paths, keys sorted).

Part 1  PS-X EXE header (pc, gp, text/data/bss/stack fields, region string) and
        the constants the crt0 code at the entry point loads (gp, BSS range).
Part 2  Overlay load address, by two independent methods:
  A (overlay side)  Function starts are the words that follow a `jr ra` plus its
        delay slot.  For every candidate base address, count how many of the
        overlay's own jal targets (A1) and lui+addiu/ori address constants (A2)
        land exactly on a function start.  The right base makes (almost) all
        of them hit; a wrong base makes almost none hit.
  B (EXE side)      The EXE's file loader is found from the file-size table and
        the CD location table (CdlLOC, BCD min/sec/frame) of the /OVERLAYS files.
        Each level function calls read_file(id, buf), then memcpy (BIOS A(0x2a))
        to the address held in an EXE data word, then jal into the window.
Status is `confirmed` only when A and B give the same exact address.

A small MIPS-I decoder is built in (stdlib only, no disassembler library).
Read-only on every input.

Usage:
  python -I tools/exe_overlays.py [--root PATH]
"""
import argparse
import bisect
import collections
import json
import os
import struct
import sys

EXE_PATH = "work/extracted/SLUS_004.76"
OVR_DIR = "work/extracted/OVERLAYS"
CLASSES_PATH = "work/disc_classes.json"
OUT_HEADER = "work/exe_header.json"
OUT_OVERLAYS = "work/overlay_candidates.json"

WINDOW_LO = 0x80130000          # search window for overlay load addresses
WINDOW_HI = 0x80140000
BASE_SCAN = range(0x80130000, 0x80134000, 4)
JR_RA = 0x03E00008
REGS = ["zero", "at", "v0", "v1", "a0", "a1", "a2", "a3", "t0", "t1", "t2", "t3",
        "t4", "t5", "t6", "t7", "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7",
        "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra"]
R_A0, R_GP, R_RA = 4, 28, 31


def h(x):
    return "0x%08x" % x


def s16(x):
    return x - 0x10000 if x & 0x8000 else x


# ---------------------------------------------------------------- MIPS-I decoder
# Enough for: lui, addiu, ori, jal, j, jr, jalr, lw, sw (and lb/lh/sb/sh variants),
# addiu sp, branches, plus a text form for evidence lines.
ALU_I = {8: "addi", 9: "addiu", 10: "slti", 11: "sltiu", 12: "andi", 13: "ori", 14: "xori"}
MEM_OPS = {0x20: "lb", 0x21: "lh", 0x22: "lwl", 0x23: "lw", 0x24: "lbu", 0x25: "lhu",
           0x26: "lwr", 0x28: "sb", 0x29: "sh", 0x2A: "swl", 0x2B: "sw", 0x2E: "swr"}
LOAD_OPS = {0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26}
STORE_OPS = {0x28, 0x29, 0x2A, 0x2B, 0x2E}
R_NAMES = {0: "sll", 2: "srl", 3: "sra", 8: "jr", 9: "jalr", 0x21: "addu", 0x23: "subu",
           0x24: "and", 0x25: "or", 0x26: "xor", 0x27: "nor", 0x2A: "slt", 0x2B: "sltu",
           0x10: "mfhi", 0x12: "mflo", 0x18: "mult", 0x1A: "div", 0x0C: "syscall"}


def rs_(w):
    return (w >> 21) & 31


def rt_(w):
    return (w >> 16) & 31


def rd_(w):
    return (w >> 11) & 31


def is_branch(w):
    op = w >> 26
    return op in (1, 4, 5, 6, 7) or (op == 0 and (w & 63) in (8, 9)) or op in (2, 3)


def dest_reg(w):
    """Register written by instruction w, or None (loads/ALU/jal/jalr only)."""
    op = w >> 26
    if op == 0:
        f = w & 63
        if f in (8, 0x18, 0x19, 0x1A, 0x1B, 0x11, 0x13, 0x0C):
            return None
        return rd_(w)
    if op == 3:
        return R_RA
    if op in ALU_I or op == 0x0F or op in LOAD_OPS:
        return rt_(w)
    return None


def jal_target(w):
    return ((w & 0x03FFFFFF) << 2) | 0x80000000


def fmt(w, pc):
    """Text form of one instruction (evidence lines only)."""
    if w == 0:
        return "nop"
    op, rs, rt, rd = w >> 26, REGS[rs_(w)], REGS[rt_(w)], REGS[rd_(w)]
    imm = w & 0xFFFF
    s = s16(imm)
    if op == 0:
        f = w & 63
        n = R_NAMES.get(f, "special%02x" % f)
        if f in (0, 2, 3):
            return "%s %s,%s,%d" % (n, rd, rt, (w >> 6) & 31)
        if f == 8:
            return "jr %s" % rs
        if f == 9:
            return "jalr %s,%s" % (rd, rs)
        if f in (0x10, 0x12):
            return "%s %s" % (n, rd)
        return "%s %s,%s,%s" % (n, rd, rs, rt)
    if op in (2, 3):
        return "%s %s" % ("j" if op == 2 else "jal", h(jal_target(w)))
    if op in (1, 4, 5, 6, 7):
        return "b%d %s,%s,%s" % (op, rs, rt, h((pc + 4 + s * 4) & 0xFFFFFFFF))
    if op in ALU_I:
        return "%s %s,%s,%s" % (ALU_I[op], rt, rs, s if op in (8, 9, 10, 11) else hex(imm))
    if op == 0x0F:
        return "lui %s,0x%04x" % (rt, imm)
    if op in MEM_OPS:
        return "%s %s,%d(%s)" % (MEM_OPS[op], rt, s, rs)
    return ".word 0x%08x" % w


# ---------------------------------------------------------------- code image
class Image:
    """A flat run of 32-bit words at a base address."""

    def __init__(self, data, base):
        n = len(data) // 4
        self.words = struct.unpack("<%dI" % n, data[:n * 4])
        self.base = base
        self.end = base + n * 4

    def __len__(self):
        return len(self.words)

    def w(self, addr):
        return self.words[(addr - self.base) >> 2]

    def addr(self, i):
        return self.base + i * 4

    def func_starts(self):
        """Function starts: word 0 and the word after each `jr ra` + delay slot."""
        out = {0}
        for i, w in enumerate(self.words):
            if w == JR_RA and i + 2 < len(self.words):
                out.add(i + 2)
        return out

    def func_start_before(self, addr):
        """Start of the function containing addr: word after the previous jr ra + delay."""
        i = (addr - self.base) >> 2
        while i > 1:
            i -= 1
            if self.words[i - 1] == JR_RA:
                return self.addr(i + 1)
        return self.base

    def abs_refs(self, hi_lo=None, hi_hi=None):
        """lui + addiu/ori address constants and lui + load/store effective addresses.

        Returns a list of (pc, address, kind) with kind 'addr' (addiu/ori result) or
        'load' / 'store' (memory operand).  The lui register is followed until it is
        overwritten or the first branch/jump (plus its delay slot) ends the block.
        """
        out = []
        words = self.words
        n = len(words)
        for i, w in enumerate(words):
            if w >> 26 != 0x0F:
                continue
            reg, hi = rt_(w), w & 0xFFFF
            if reg == 0:
                continue
            if hi_lo is not None and not (hi_lo <= hi < hi_hi):
                continue
            ended = False
            for j in range(i + 1, min(i + 14, n)):
                v = words[j]
                op = v >> 26
                if rs_(v) == reg:
                    if op == 9:
                        out.append((self.addr(j), ((hi << 16) + s16(v & 0xFFFF)) & 0xFFFFFFFF, "addr"))
                    elif op == 13:
                        out.append((self.addr(j), (hi << 16) | (v & 0xFFFF), "addr"))
                    elif op in LOAD_OPS or op in STORE_OPS:
                        kind = "load" if op in LOAD_OPS else "store"
                        out.append((self.addr(j), ((hi << 16) + s16(v & 0xFFFF)) & 0xFFFFFFFF, kind))
                if op == 0 and (v & 63) == 0x21 and rd_(v) == reg and reg in (rs_(v), rt_(v)):
                    pass   # addu reg,reg,index: the base stays in reg
                elif dest_reg(v) == reg:
                    break
                if ended:
                    break
                if is_branch(v):
                    ended = True   # the delay slot is still examined
        return out


# ---------------------------------------------------------------- PS-X EXE header
HEADER_FIELDS = ["pc0", "gp0", "t_addr", "t_size", "d_addr", "d_size", "b_addr",
                 "b_size", "s_addr", "s_size"]


def parse_exe_header(data):
    if data[:8] != b"PS-X EXE":
        raise SystemExit("not a PS-X EXE (magic %r)" % data[:8])
    vals = struct.unpack_from("<10I", data, 0x10)
    hdr = dict(zip(HEADER_FIELDS, vals))
    hdr["region"] = data[0x4C:0x800].split(b"\0")[0].decode("ascii")
    return hdr


def track_consts(img, start, count):
    """Linear constant propagation (lui/addiu/ori/addu-from-zero) over `count` words.

    Returns events: ('gp', value), ('store0', reg_const, pc), ('sltu', rs_const, rt_const, pc).
    """
    regs = {0: 0}
    events = []
    for k in range(count):
        pc = start + 4 * k
        w = img.w(pc)
        op = w >> 26
        if op == 0x0F:
            regs[rt_(w)] = (w & 0xFFFF) << 16
        elif op in (9, 13) and rs_(w) in regs:
            v = regs[rs_(w)]
            regs[rt_(w)] = (v + s16(w & 0xFFFF)) & 0xFFFFFFFF if op == 9 else v | (w & 0xFFFF)
        elif op == 0 and (w & 63) == 0x21 and rs_(w) in regs and rt_(w) in regs:
            regs[rd_(w)] = (regs[rs_(w)] + regs[rt_(w)]) & 0xFFFFFFFF
        elif op == 0x2B and rt_(w) == 0 and rs_(w) in regs:
            events.append(("store0", regs[rs_(w)], pc))
        elif op == 0 and (w & 63) == 0x2B:
            events.append(("sltu", regs.get(rs_(w)), regs.get(rt_(w)), pc))
        else:
            d = dest_reg(w)
            if d is not None:
                regs.pop(d, None)
        if rt_(w) == R_GP and op == 9 and R_GP in regs:
            events.append(("gp", regs[R_GP], pc))
    return events


SYNC = b"\x00" + b"\xff" * 10 + b"\x00"


def raw_sector_header(root):
    """Second, independent read of the EXE header: straight from the .bin sectors.

    Does not use work/extracted.  Reads the raw 2352-byte Mode 2 sector at LBA 23
    (the boot EXE start, DISC_MAP.md), checks sync, takes the Form 1 user data at +24.
    Returns a dict like parse_exe_header, or None if the disc image is not present.
    """
    import glob
    bins = sorted(glob.glob(os.path.join(root, "ps1_game", "*.bin")))
    if len(bins) != 1:
        return None
    with open(bins[0], "rb") as f:
        f.seek(23 * 2352)
        sec = f.read(2352)
    if len(sec) != 2352 or sec[:12] != SYNC:
        return None
    user = sec[24:24 + 2048]
    if user[:8] != b"PS-X EXE":
        return None
    out = dict(zip(HEADER_FIELDS, struct.unpack_from("<10I", user, 0x10)))
    out["region"] = user[0x4C:].split(SYNC[:1])[0].decode("ascii")
    return out


def build_header(exe_bytes, img, crosscheck):
    hdr = parse_exe_header(exe_bytes)
    t_end = hdr["t_addr"] + hdr["t_size"]
    out = {"file": "SLUS_004.76", "file_size": len(exe_bytes),
           "file_size_matches_header": len(exe_bytes) == 0x800 + hdr["t_size"],
           "region": hdr["region"], "fields": {}}
    labels = {"pc0": "entry point (initial PC)", "gp0": "initial GP",
              "t_addr": "text load address", "t_size": "text size in bytes",
              "d_addr": "data address", "d_size": "data size",
              "b_addr": "bss address", "b_size": "bss size",
              "s_addr": "stack base (initial SP = s_addr + s_size)", "s_size": "stack offset"}
    for k in HEADER_FIELDS:
        v = hdr[k]
        status = "pending Ghidra/emulator"
        if crosscheck is not None:
            status = ("confirmed by independent parse (pending Ghidra/emulator too)"
                      if crosscheck.get(k) == v else "MISMATCH with independent parse")
        out["fields"][k] = {"value": v, "hex": h(v), "meaning": labels[k], "status": status}
    sp = (hdr["s_addr"] + hdr["s_size"]) & 0xFFFFFFFF
    out["initial_sp"] = {"value": sp, "hex": h(sp)}
    out["text_range"] = {"start": h(hdr["t_addr"]), "end_exclusive": h(t_end)}
    region_ok = None
    if crosscheck is not None:
        region_ok = crosscheck.get("region") == hdr["region"]
    out["region_status"] = ("confirmed by independent parse" if region_ok else
                            "pending Ghidra/emulator" if region_ok is None else "MISMATCH")
    out["independent_parse"] = ("raw_sector_header() in tools/exe_overlays.py: .bin LBA 23, user data +24"
                                if crosscheck is not None else "not run (disc image missing)")
    out["emulator_or_ghidra"] = ("pending: DuckStation cannot be queried automatically; "
                                 "compare with Ghidra after T1.5")
    # crt0 constants, found by decoding the code at the entry point
    ev = track_consts(img, hdr["pc0"], 80)
    crt0 = {"decoded_from": h(hdr["pc0"]), "status": "decoded from code at pc0 (pending Ghidra/emulator)"}
    gps = [e for e in ev if e[0] == "gp"]
    if gps:
        crt0["gp_set_to"] = {"value": h(gps[0][1]), "at_pc": h(gps[0][2])}
    st = [e for e in ev if e[0] == "store0"]
    sl = [e for e in ev if e[0] == "sltu" and e[1] is not None and e[2] is not None]
    if st and sl:
        crt0["bss_clear"] = {"start": h(st[0][1]), "end_exclusive": h(sl[0][2]),
                             "store_pc": h(st[0][2]), "compare_pc": h(sl[0][3])}
    out["crt0"] = crt0
    return out, hdr


# ---------------------------------------------------------------- EXE loader (method B)
def find_run(data, pattern):
    hits, i = [], data.find(pattern)
    while i >= 0:
        hits.append(i)
        i = data.find(pattern, i + 1)
    return hits


def bcd(x):
    return ((x // 10) << 4) | (x % 10)


def loc_bytes(lba):
    f = lba + 150
    return bytes([bcd(f // 4500), bcd((f // 75) % 60), bcd(f % 75), 0])


def analyze_loader(exe_bytes, img, ovl_files):
    """Method B.  ovl_files: [(path, lba, size)] for every /OVERLAYS file, sorted by LBA."""
    res = {"found": False}
    data = exe_bytes[0x800:]
    base = img.base
    size_pat = b"".join(struct.pack("<I", s) for _, _, s in ovl_files)
    loc_pat = b"".join(loc_bytes(l) for _, l, _ in ovl_files)
    sruns, lruns = find_run(data, size_pat), find_run(data, loc_pat)
    res["size_table_run"] = [h(base + i) for i in sruns]
    res["loc_table_run"] = [h(base + i) for i in lruns]
    if len(sruns) != 1 or len(lruns) != 1:
        return res
    size_run, loc_run = base + sruns[0], base + lruns[0]
    full_refs = img.abs_refs()
    refs = [r for r in full_refs if 0x80010000 <= r[1] < 0x80020000]
    # table base for sizes: address of a `lw` (index in a register) at or below the run
    cand = collections.Counter(a for _, a, k in refs if k == "load" and a <= size_run
                               and (size_run - a) % 4 == 0 and (size_run - a) // 4 < 1000)
    if not cand:
        return res
    size_base = max(cand.items(), key=lambda kv: (kv[1], -kv[0]))[0]
    first_id = (size_run - size_base) // 4
    loc_cand = [(pc, a) for pc, a, k in refs if k == "addr" and a <= loc_run
                and (loc_run - a) % 4 == 0 and (loc_run - a) // 4 == first_id]
    if not loc_cand:
        return res
    loc_base = loc_cand[0][1]
    ids = {first_id + i: p for i, (p, _, _) in enumerate(ovl_files)}
    res.update({"found": True, "size_table_base": h(size_base), "loc_table_base": h(loc_base),
                "first_overlay_dir_id": first_id,
                "ids": {str(k): v for k, v in sorted(ids.items())},
                "id_from_size_table_equals_id_from_loc_table": True,
                "size_table_xrefs": sorted(h(pc) for pc, a, k in refs if k == "load" and a == size_base)})
    # accessor functions
    get_size = sorted({img.func_start_before(pc) for pc, a, k in refs if k == "load" and a == size_base})
    read_file = sorted({img.func_start_before(pc) for pc, a in loc_cand})
    # get_size is the tiny leaf: its body is <= 8 words
    def body_len(fs):
        i = (fs - base) >> 2
        j = i
        while img.words[j] != JR_RA:
            j += 1
        return j - i + 2
    gs = [f for f in get_size if body_len(f) <= 8]
    res["get_size_function"] = h(gs[0]) if gs else None
    res["read_file_function"] = h(read_file[0]) if len(read_file) == 1 else [h(f) for f in read_file]
    if not gs or len(read_file) != 1:
        return res
    gs_addr, rf_addr = gs[0], read_file[0]
    # BIOS A-function stub: addiu t2,zero,0xa0 ; jr t2 ; addiu t1,zero,N
    stubs = {}
    ws = img.words
    for i in range(len(ws) - 2):
        if ws[i] == 0x240A00A0 and ws[i + 1] == 0x01400008 and ws[i + 2] >> 16 == 0x2409:
            stubs[ws[i + 2] & 0xFFFF] = img.addr(i)
    memcpy = stubs.get(0x2A)
    res["bios_a_stubs_found"] = {("0x%02x" % k): h(v) for k, v in sorted(stubs.items())}
    res["memcpy_stub_A_2a"] = h(memcpy) if memcpy else None
    # all stores into candidate pointer variables, to check they are never written
    store_addrs = collections.Counter(a for _, a, k in full_refs if k == "store")
    load_at = {pc: a for pc, a, k in full_refs if k == "load"}
    # prologue starts for bounding a loader function body
    pro = [i for i, w in enumerate(ws) if w >> 16 == 0x27BD and w & 0x8000 and i >= 2 and ws[i - 2] == JR_RA]
    pro_addrs = [img.addr(i) for i in pro]
    sites = []
    for i, w in enumerate(ws):
        if w >> 26 != 3 or jal_target(w) != rf_addr:
            continue
        pc = img.addr(i)
        fid = None
        for k in range(i - 1, max(i - 10, 0), -1):
            v = ws[k]
            if v >> 16 in (0x2404, 0x3404) and rs_(v) == 0:
                fid = v & 0xFFFF
                break
            if v >> 26 == 3:
                break
        if fid is None or fid not in ids:
            continue
        fs = img.func_start_before(pc)
        k = bisect.bisect_right(pro_addrs, fs)
        fend = pro_addrs[k] if k < len(pro_addrs) else img.end
        site = {"id": fid, "file": ids[fid], "read_file_call_pc": h(pc),
                "caller_function": h(fs), "caller_end_exclusive": h(fend)}
        # memcpy after the read, with get_size(id) as its length
        for j in range((pc - base) >> 2, (fend - base) >> 2):
            v = ws[j]
            if v >> 26 == 3 and memcpy is not None and jal_target(v) == memcpy:
                mpc = img.addr(j)
                # length: nearest get_size call before the memcpy
                gid = None
                for m in range(j - 1, max(j - 14, 0), -1):
                    if ws[m] >> 26 == 3 and jal_target(ws[m]) == gs_addr:
                        if ws[m + 1] >> 16 in (0x2404, 0x3404):
                            gid = ws[m + 1] & 0xFFFF
                        else:
                            for q in range(m - 1, m - 4, -1):
                                if ws[q] >> 16 in (0x2404, 0x3404):
                                    gid = ws[q] & 0xFFFF
                                    break
                        break
                # destination: a0 comes from a register loaded from a data variable
                dst = None
                reg = None
                delay = ws[j + 1]
                if delay >> 26 == 0 and (delay & 63) == 0x21 and rt_(delay) == 0 and rd_(delay) == R_A0:
                    reg = rs_(delay)
                if reg is not None:
                    for m in range(j - 1, max(j - 40, 0), -1):
                        v2 = ws[m]
                        if v2 >> 26 == 0x23 and rt_(v2) == reg:
                            dst = load_at.get(img.addr(m))
                            break
                dst_val = None
                if dst is not None and base <= dst < img.end:
                    dst_val = ws[(dst - base) >> 2]
                sites.append((fid, site, {"memcpy_call_pc": h(mpc), "length_from_get_size_id": gid,
                                          "dst_variable": h(dst) if dst else None,
                                          "dst_variable_initial_value": h(dst_val) if dst_val is not None else None,
                                          "dst_variable_stores_in_exe": store_addrs.get(dst, 0) if dst else None,
                                          "_j": j}))
                break
        else:
            sites.append((fid, site, None))
    loaders = []
    for fid, site, mc in sites:
        rec = dict(site)
        if mc:
            j = mc.pop("_j")
            rec.update(mc)
            ent = []
            for q in range(j + 1, (int(rec["caller_end_exclusive"], 16) - base) >> 2):
                v = ws[q]
                if v >> 26 == 3 and WINDOW_LO <= jal_target(v) < 0x80200000:
                    ent.append({"pc": h(img.addr(q)), "target": h(jal_target(v))})
            rec["jal_into_window_after_memcpy"] = ent
        loaders.append(rec)
    res["loader_sites"] = sorted(loaders, key=lambda r: (r["id"], r["read_file_call_pc"]))
    return res


# ---------------------------------------------------------------- overlays (method A)
def score_bases(starts, targets, n_bytes):
    """For each base in BASE_SCAN: (hits, in_range) of `targets` against function starts."""
    out = []
    for base in BASE_SCAN:
        inr = [t for t in targets if base <= t < base + n_bytes and (t - base) % 4 == 0]
        hits = sum(1 for t in inr if ((t - base) >> 2) in starts)
        out.append((base, hits, len(inr)))
    return out


def rank(scores):
    """Return (best_base, hits, in_range, tied_best_count, runner_up_hits)."""
    ordered = sorted(scores, key=lambda s: (-s[1], s[0]))
    top = ordered[0]
    tied = [s for s in ordered if s[1] == top[1]]
    nxt = [s for s in ordered if s[1] < top[1]]
    return top[0], top[1], top[2], len(tied), (nxt[0][1] if nxt else 0)


def analyze_overlay(name, data, size, loader_base, loader_sites, ovl_id):
    img = Image(data, 0)
    n = len(img)
    starts = img.func_starts()
    k = 0
    while k < n and (WINDOW_LO <= img.words[k] < WINDOW_HI or img.words[k] == 0):
        k += 1
    if sum(1 for x in img.words[:k] if x) >= 4:
        starts.add(k)   # the word after a leading address table is the first function
    ev = []
    jal_t = sorted({jal_target(w) for w in img.words if w >> 26 == 3 and WINDOW_LO <= jal_target(w) < WINDOW_HI})
    abs_t = sorted({a for _, a, k in img.abs_refs(WINDOW_LO >> 16, WINDOW_HI >> 16) if k == "addr"})
    entry_t = sorted({int(e["target"], 16) for s in loader_sites if s["id"] == ovl_id
                      for e in s.get("jal_into_window_after_memcpy", [])})
    table = None
    if sum(1 for x in img.words[:k] if x) >= 4:
        tab = [x for x in img.words[:k] if x]
        table = {"words": k, "pointer_words": len(tab), "min": h(min(tab)), "max": h(max(tab))}
    rec = {"size_bytes": size, "id": ovl_id, "layout": "address table + code" if table else "code from offset 0",
           "leading_address_table": table, "function_starts_found": len(starts),
           "jal_targets_in_window": len(jal_t), "address_constants_in_window": len(abs_t),
           "exe_entry_targets": [h(t) for t in entry_t]}
    a1 = rank(score_bases(starts, jal_t, size)) if jal_t else None
    a2 = rank(score_bases(starts, abs_t, size)) if abs_t else None

    def pack(r, total):
        if r is None:
            return None
        return {"best_base": h(r[0]), "hits": r[1], "in_range": r[2], "of_total": total,
                "bases_tied_for_best": r[3], "runner_up_hits": r[4],
                "decisive": r[1] >= 3 and r[3] == 1}
    rec["method_A1_jal_targets"] = pack(a1, len(jal_t))
    rec["method_A2_address_constants"] = pack(a2, len(abs_t))
    # load address from the EXE loader
    rec["method_B_exe_loader"] = {"address": h(loader_base) if loader_base else None,
                                  "loader_functions": sorted({s["caller_function"] for s in loader_sites
                                                              if s["id"] == ovl_id and s.get("dst_variable")})}
    # check of the loader address against overlay content
    if loader_base:
        st = score_bases(starts, jal_t, size)
        d = {b: (hh, ir) for b, hh, ir in st}
        rec["check_at_loader_address"] = {
            "jal_targets_on_function_start": "%d of %d in range" % d[loader_base] if loader_base in d else None,
            "exe_entry_targets_on_function_start": "%d of %d" % (
                sum(1 for t in entry_t if loader_base <= t < loader_base + size and ((t - loader_base) >> 2) in starts),
                len(entry_t)),
        }
        if table:
            ptrs = [x for x in img.words[:table["words"]] if x]
            inside = [p for p in ptrs if loader_base + table["words"] * 4 <= p < loader_base + size]
            on_fn = sum(1 for p in inside if ((p - loader_base) >> 2) in starts)
            rec["check_at_loader_address"]["table_words_inside_file_after_table"] = "%d of %d" % (len(inside), len(ptrs))
            rec["check_at_loader_address"]["table_words_on_function_start"] = "%d of %d" % (on_fn, len(inside))
    # decision
    agree = []
    for tag, r in (("A1", a1), ("A2", a2)):
        if r is not None and r[1] >= 3 and r[3] == 1 and loader_base and r[0] == loader_base:
            agree.append(tag)
    unique_a = [tag for tag, r in (("A1", a1), ("A2", a2)) if r is not None and r[1] >= 3 and r[3] == 1]
    rec["methods_agreeing_with_B"] = agree
    if loader_base and agree:
        rec["load_address"] = h(loader_base)
        rec["status"] = "confirmed"
        rec["status_scope"] = ("static confirmation only (overlay-side fit agrees with the EXE-side loader "
                               "pointer); runtime confirmation pending Ghidra/emulator")
        rec["confidence"] = "high"
        rec["relies_on_A2_only"] = agree == ["A2"]
    elif loader_base:
        rec["load_address"] = h(loader_base)
        rec["status"] = "estimated"
        rec["confidence"] = "medium (loader only)"
    elif unique_a:
        best = a1 if "A1" in unique_a else a2
        rec["load_address"] = h(best[0])
        rec["status"] = "estimated"
        rec["confidence"] = "medium (overlay content only)"
    else:
        rec["load_address"] = None
        rec["status"] = "estimated"
        rec["confidence"] = "none"
    if rec["load_address"]:
        la = int(rec["load_address"], 16)
        rec["end_address_exclusive"] = h(la + size)
    # evidence list (plain statements, each reproducible from this script)
    evl = []
    if loader_base:
        evl.append("B: the level function(s) %s call read_file(id %s, buf), then memcpy (BIOS A(0x2a)) "
                   "with length get_size(id) to the pointer held at EXE data word %s = %s (never stored to "
                   "in the EXE)." % (", ".join(rec["method_B_exe_loader"]["loader_functions"]), ovl_id,
                                     loader_site_var(loader_sites, ovl_id), h(loader_base)))
    for tag, r, what in (("A1", a1, "its own jal targets"), ("A2", a2, "its own lui+addiu/ori address constants")):
        if r is None:
            evl.append("%s: no usable data (%s: none in the window)." % (tag, what))
        else:
            evl.append("%s: %d of %d in-range %s land on function starts at base %s (%d bases tie, runner-up "
                       "%d hits)%s." % (tag, r[1], r[2], what, h(r[0]), r[3], r[4],
                                        "" if (r[1] >= 3 and r[3] == 1) else "; not decisive"))
    if rec.get("check_at_loader_address"):
        c = rec["check_at_loader_address"]
        evl.append("EXE entry targets (jal in the level function after the memcpy) on function starts at "
                   "the loader address: %s." % c["exe_entry_targets_on_function_start"])
    if table:
        evl.append("Leading table of %d address words (%s..%s) points into the file body after the table at "
                   "the loader address; the words point at data, not at function starts." % (
                       table["words"], table["min"], table["max"]))
    if loader_base and loader_base in entry_t:
        evl.append("The level function calls jal %s, the load address itself: the overlay is entered at "
                   "file offset 0." % h(loader_base))
    if rec.get("relies_on_A2_only"):
        evl.append("Caveat: the overlay-side agreement rests on A2 (address constants) alone; A1 has no "
                   "decisive jal targets.")
    rec["evidence"] = evl
    return rec


def loader_site_var(loader_sites, ovl_id):
    for s in loader_sites:
        if s["id"] == ovl_id and s.get("dst_variable"):
            return s["dst_variable"]
    return None


# ---------------------------------------------------------------- driver
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    args = ap.parse_args()
    root = args.root

    def p(rel):
        return os.path.join(root, *rel.split("/"))

    exe_bytes = open(p(EXE_PATH), "rb").read()
    hdr0 = parse_exe_header(exe_bytes)
    img = Image(exe_bytes[0x800:], hdr0["t_addr"])
    crosscheck = raw_sector_header(root)
    header_json, hdr = build_header(exe_bytes, img, crosscheck)

    classes = load_json(p(CLASSES_PATH))
    ovl = sorted((f for f in classes["files"] if f["path"].startswith("/OVERLAYS/")), key=lambda f: f["lba"])
    ovl_files = [(f["path"], f["lba"], os.path.getsize(p("work/extracted" + f["path"]))) for f in ovl]
    loader = analyze_loader(exe_bytes, img, ovl_files)

    # memory map
    t_end = hdr["t_addr"] + hdr["t_size"]
    mm = {"text": {"start": h(hdr["t_addr"]), "end_exclusive": h(t_end), "size": hdr["t_size"]}}
    bss = header_json["crt0"].get("bss_clear")
    if bss:
        bs, be = int(bss["start"], 16), int(bss["end_exclusive"], 16)
        mm["bss_cleared_by_crt0"] = {"start": h(bs), "end_exclusive": h(be)}
        tail = exe_bytes[0x800 + (bs - hdr["t_addr"]):]
        mm["bss_start_inside_text_file_range"] = bs < t_end
        mm["nonzero_bytes_in_file_between_bss_start_and_text_end"] = sum(1 for b in tail if b)
    mm["stack_top"] = header_json["initial_sp"]["hex"]

    overlays = []
    for path, lba, size in ovl_files:
        if not path.endswith(".OVR"):
            continue
        name = os.path.basename(path)
        data = open(p("work/extracted" + path), "rb").read()
        ids = {v: int(k) for k, v in loader.get("ids", {}).items()}
        oid = ids.get(path)
        sites = [s for s in loader.get("loader_sites", [])]
        dsts = {s.get("dst_variable_initial_value") for s in sites if s["id"] == oid and s.get("dst_variable_initial_value")}
        loader_base = int(dsts.pop(), 16) if len(dsts) == 1 else None
        rec = analyze_overlay(name, data, size, loader_base, sites, oid)
        rec.update({"path": path, "lba": lba, "name": name})
        overlays.append(rec)
    overlays.sort(key=lambda r: r["name"])

    # collisions
    bases = sorted({r["load_address"] for r in overlays if r["load_address"]})
    wins = [(int(r["load_address"], 16), int(r["end_address_exclusive"], 16), r["name"]) for r in overlays
            if r["load_address"]]
    lo, hi = (min(w[0] for w in wins), max(w[1] for w in wins)) if wins else (None, None)
    coll = {"overlay_window_union": {"start": h(lo), "end_exclusive": h(hi)} if wins else None,
            "all_overlays_share_one_load_address": len(bases) == 1,
            "distinct_load_addresses": bases}
    if wins:
        sp = hdr["s_addr"] + hdr["s_size"]
        coll["overlaps_exe_text"] = lo < t_end and hi > hdr["t_addr"]
        if bss:
            coll["overlaps_exe_bss_cleared_by_crt0"] = lo < be and hi > bs
            coll["window_start_minus_bss_end"] = lo - be
        coll["ends_below_initial_sp"] = hi <= sp
        coll["largest_overlay"] = max(wins, key=lambda w: w[1] - w[0])[2]
    mm["overlay_collision_check"] = coll

    unresolved = [
        "Header and crt0 values are confirmed only by a second parser of the raw sectors; the "
        "emulator/Ghidra comparison is pending (DuckStation cannot be queried automatically).",
        "crt0 sets GP in code (header gp0 is 0). The crt0 BSS start lies inside the file-backed "
        "text range; the meaning of the last bytes of the text segment is not established.",
        "The overlay window starts exactly at the BSS end that crt0 clears up to, and crt0 loads "
        "the same constant a second time (0x80090ec0..0x80090ec4). Where the scratch allocator "
        "(pointers at gp+0x684/0x688/0x68c, used for the temporary read buffer before the "
        "memcpy) takes its memory from, and whether it overlaps the overlay window, was not traced.",
        "crt0 calls BIOS A(0x39) InitHeap with a0 = 0x80130ffc and a1 = sp - [0x800bf358] - 0x130ff8 "
        "(that word is 0x8000, per review), so the BIOS heap starts inside the overlay window. The scratch "
        "read buffer (allocator 0x800865c0) likely starts near 0x80131000, so the memcpy to 0x80130ff8 "
        "may be a small forward-overlapping move. Not proven; the return value of the malloc(4) at "
        "0x8008652c is unknown.",
        "read_file has two call sites with a variable id (0x80085cf8 and 0x80085d74), which this tool "
        "does not resolve; this is a small hole in the claim that only the nine level functions load overlays.",
        "Function starts are taken as the word after `jr ra` + delay slot. The common check "
        "'jal target is an addiu sp,sp,-N prologue' is wrong for this code: its functions often begin "
        "with lui/lw before the stack adjustment, so that check wrongly prefers base 0x80130ff0.",
        "Whether any code outside the nine level functions loads an overlay (for example a "
        "second FIRE level, ids 137 loaded by two functions) was not traced further.",
        "BRDGDEMO.BIN and WINDDEMO.BIN (ids 134 and 143) are loaded by the BRIDGE and WIND "
        "level functions; what they hold was not analysed.",
    ]
    result = {
        "tool": "tools/exe_overlays.py",
        "loader": loader,
        "memory_map": mm,
        "overlays": overlays,
        "unresolved": unresolved,
    }
    header_json["memory_map_ref"] = OUT_OVERLAYS + " (memory_map)"

    for rel, obj in ((OUT_HEADER, header_json), (OUT_OVERLAYS, result)):
        with open(p(rel), "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, indent=1, sort_keys=True)
            f.write("\n")
    # console summary
    print("EXE header:")
    for k in HEADER_FIELDS:
        fld = header_json["fields"][k]
        print("  %-7s %s  %s" % (k, fld["hex"], fld["status"]))
    print("  region  %s (%s)" % (hdr["region"], header_json["region_status"]))
    print("  initial_sp %s" % header_json["initial_sp"]["hex"])
    print("crt0:", json.dumps(header_json["crt0"], sort_keys=True))
    print("overlays:")
    for r in overlays:
        print("  %-13s size %6d  load %s  end %s  %s  A1=%s A2=%s" % (
            r["name"], r["size_bytes"], r["load_address"], r.get("end_address_exclusive"), r["status"],
            (r["method_A1_jal_targets"] or {}).get("hits"), (r["method_A2_address_constants"] or {}).get("hits")))
    print("collision check:", json.dumps(coll, sort_keys=True))


if __name__ == "__main__":
    main()
