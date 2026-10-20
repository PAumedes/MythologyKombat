#!/usr/bin/env python3
"""Overlay facts from the boot EXE and the disc (T2.12).

Inputs : work/disc/SLUS_004.76 (boot EXE, cross-checked against the .bin),
         work/disc_files.json (T1.1), the disc image ps1_game/*.bin (read-only,
         read through the tools/disc_identify.py sector reader).
         It does NOT use work/extracted.
Output : work/overlay_facts.json (deterministic: no timestamps, no absolute
         paths, keys sorted).  work/overlay_candidates.json is read only to
         compare the leading address-table lengths.

Sections of the output
  tables        CdlLOC table (0x80012F28) and size table (0x80013264) for file
                ids 134..143 against the ISO9660 directory (LBA, size, sectors)
  dest_pointer  word at 0x80015134 and every instruction that can address it
  read_file     every call site of read_file (0x800861D4) with its id source;
                the two variable-id sites (0x80085CF8, 0x80085D74) resolved
  dispatcher    jump table that selects the nine level functions
  levels        per level function: ids read, overlay-window references
  ovr_files     SHA-256, size, sector alignment, leading address table length
  second_checks FORTRESS / PRISON (and the others, for calibration): checks
                that do not use the "lui+addiu address constant" rule
  fire_sites    the two FIRE level functions side by side

A small MIPS-I decoder is imported from tools/exe_overlays.py (stdlib only).
Read-only on every input.

Usage:
  python -I tools/overlay_facts.py
"""
import bisect
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import exe_overlays as eo           # noqa: E402  (decoder: fmt, dest_reg, ...)
import disc_identify as di          # noqa: E402  (cue parser, raw sector reader)

EXE_PATH = "work/disc/SLUS_004.76"
FILES_JSON = "work/disc_files.json"
CAND_JSON = "work/overlay_candidates.json"
OUT = "work/overlay_facts.json"

B = 0x80010000                      # EXE text load address
LOC_BASE = 0x80012F28
SIZE_BASE = 0x80013264
DEST_PTR = 0x80015134
WINDOW_LO, WINDOW_HI = 0x80130FF8, 0x8013C720
GP = 0x800D75AC                     # set by crt0 at pc 0x80090EF4 (T1.4)
GET_SIZE, READ_FILE, MEMCPY = 0x800861BC, 0x800861D4, 0x8009F31C
IDS = list(range(134, 144))
JR_RA = eo.JR_RA
H = eo.h


def p(rel):
    return os.path.join(ROOT, rel)


def s16(x):
    return x - 0x10000 if x & 0x8000 else x


def load_exe():
    data = open(p(EXE_PATH), "rb").read()
    if data[:8] != b"PS-X EXE":
        raise SystemExit("work/disc/SLUS_004.76 is not a PS-X EXE")
    return data


class Exe:
    def __init__(self, data):
        self.data = data
        n = (len(data) - 0x800) // 4
        self.W = struct.unpack("<%dI" % n, data[0x800:0x800 + 4 * n])
        self.end = B + 4 * n

    def w(self, a):
        return self.W[(a - B) >> 2]

    def b4(self, a):
        o = 0x800 + a - B
        return self.data[o:o + 4]

    def text(self, a):
        return eo.fmt(self.w(a), a)


# ------------------------------------------------------------------ disc access
def open_disc():
    d = p("ps1_game")
    cues = sorted(x for x in os.listdir(d) if x.lower().endswith(".cue"))
    if len(cues) != 1:
        raise SystemExit("expected one .cue in ps1_game")
    fl = di.parse_cue(os.path.join(d, cues[0]))
    t = fl[0]["tracks"][0]
    return di.Track1Reader(os.path.join(d, fl[0]["name"]), t["mode"], t["indexes"][1])


def bcd_ok(b):
    return (b >> 4) < 10 and (b & 15) < 10


def bcd(b):
    return (b >> 4) * 10 + (b & 15)


# ------------------------------------------------------------------ const propagation
class Ref:
    __slots__ = ("pc", "kind", "addr", "indexed", "op")

    def __init__(self, pc, kind, addr, indexed, op):
        self.pc, self.kind, self.addr, self.indexed, self.op = pc, kind, addr, indexed, op


def scan_refs(X, span=64):
    """Forward constant propagation from every `lui`, ignoring branches (it
    over-approximates: every straight-line continuation is followed).

    A tracked register holds (value, indexed).  `indexed` becomes true after
    `addu reg, tracked, unknown` (base plus a variable index).  Reports:
      kind 'val'    register becomes a constant (lui/addiu/ori/move)
      kind 'load'/'store'  memory operand with a tracked base register
    plus gp-relative memory operands (gp = 0x800D75AC).
    """
    W = X.W
    n = len(W)
    out = []
    for i in range(n):
        pc = B + 4 * i
        w = W[i]
        op = w >> 26
        if op in eo.LOAD_OPS or op in eo.STORE_OPS:
            if eo.rs_(w) == 28:
                out.append(Ref(pc, "load" if op in eo.LOAD_OPS else "store",
                               (GP + s16(w & 0xFFFF)) & 0xFFFFFFFF, False, op))
        if op != 0x0F:
            continue
        reg = eo.rt_(w)
        if reg == 0:
            continue
        regs = {reg: ((w & 0xFFFF) << 16, False)}
        out.append(Ref(pc, "val", (w & 0xFFFF) << 16, False, op))
        for j in range(i + 1, min(i + span, n)):
            if not regs:
                break
            v = W[j]
            vop = v >> 26
            vpc = B + 4 * j
            rs, rt, rd = eo.rs_(v), eo.rt_(v), eo.rd_(v)
            if vop in eo.LOAD_OPS or vop in eo.STORE_OPS:
                if rs in regs:
                    val, ix = regs[rs]
                    out.append(Ref(vpc, "load" if vop in eo.LOAD_OPS else "store",
                                   (val + s16(v & 0xFFFF)) & 0xFFFFFFFF, ix, vop))
            new = None
            dst = None
            if vop in (9, 13) and rs in regs:
                val, ix = regs[rs]
                imm = s16(v & 0xFFFF) if vop == 9 else v & 0xFFFF
                nv = (val + imm) & 0xFFFFFFFF if vop == 9 else val | imm
                new, dst = (nv, ix), rt
                out.append(Ref(vpc, "val", nv, ix, vop))
            elif vop == 0 and (v & 63) in (0x21, 0x25):
                if rs in regs and rt == 0:
                    new, dst = regs[rs], rd
                elif rt in regs and rs == 0:
                    new, dst = regs[rt], rd
                elif rs in regs or rt in regs:
                    val = regs[rs][0] if rs in regs else regs[rt][0]
                    new, dst = (val, True), rd
            if dst is None:
                dst = eo.dest_reg(v)
            if dst is not None:
                if new is not None:
                    regs[dst] = new
                else:
                    regs.pop(dst, None)
    return out


# ------------------------------------------------------------------ 1. tables
EXPECT_CODE = {
    # get_size(id)
    0x800861BC: 0x00042080, 0x800861C0: 0x3C018001, 0x800861C4: 0x00240821, 0x800861C8: 0x8C223264,
    # read_file(id, buf)
    0x800861DC: 0x00048080, 0x800861F0: 0x3C018001, 0x800861F4: 0x00300821, 0x800861F8: 0x8C223264,
    0x80086200: 0x244207FF, 0x80086208: 0x000292C2, 0x80086210: 0x02008821, 0x8008621C: 0x02008821,
    0x8008626C: 0x3C058001, 0x80086270: 0x24A52F28, 0x80086274: 0x02252821,
}


def do_tables(X, files, rd):
    code = {H(a): {"word": "0x%08x" % X.w(a), "text": X.text(a), "as_expected": X.w(a) == e}
            for a, e in sorted(EXPECT_CODE.items())}
    stride_ok = all(c["as_expected"] for c in code.values())
    byid = {}
    rows = []
    for i, fid in enumerate(IDS):
        f = files[i]
        loc = X.b4(LOC_BASE + 4 * fid)
        size = struct.unpack("<I", X.b4(SIZE_BASE + 4 * fid))[0]
        bcd_valid = all(bcd_ok(b) for b in loc[:3])
        lba = (bcd(loc[0]) * 60 + bcd(loc[1])) * 75 + bcd(loc[2]) - 150 if bcd_valid else None
        sectors = (size + 2047) // 2048
        r = {"id": fid, "path": f["path"],
             "loc_entry_addr": H(LOC_BASE + 4 * fid), "loc_bytes": loc.hex(),
             "loc_fourth_byte_zero": loc[3] == 0,
             "loc_msf_bcd": "%02x:%02x:%02x" % tuple(loc[:3]),
             "loc_lba": lba, "disc_lba": f["lba"], "lba_match": lba == f["lba"],
             "size_entry_addr": H(SIZE_BASE + 4 * fid), "size_table": size,
             "disc_size": f["size_bytes"], "size_match": size == f["size_bytes"],
             "size_sectors_ceil": sectors, "disc_sectors": f["sectors"],
             "sectors_match": sectors == f["sectors"]}
        r["agree"] = bool(bcd_valid and r["loc_fourth_byte_zero"] and r["lba_match"] and
                          r["size_match"] and r["sectors_match"])
        rows.append(r)
        byid[fid] = r
    # LBA contiguity between neighbouring files in id order
    for a, b in zip(rows, rows[1:]):
        a["next_file_lba_equals_end_plus_1"] = (files[IDS.index(a["id"])]["end_lba"] + 1 ==
                                                 files[IDS.index(b["id"])]["lba"])
    # independent read of the sector contents
    for r in rows:
        f = files[IDS.index(r["id"])]
        data = rd.read_extent(f["lba"], f["size_bytes"])
        r["sha256"] = hashlib.sha256(data).hexdigest()
        r["size_read"] = len(data)
    return {"entry_layout": {
                "loc_table_base": H(LOC_BASE), "loc_stride_bytes": 4,
                "loc_layout": "min, sec, frame (BCD each), 0; LBA = (min*60+sec)*75+frame-150",
                "size_table_base": H(SIZE_BASE), "size_stride_bytes": 4,
                "size_layout": "little-endian u32 byte count",
                "stride_evidence": code, "stride_evidence_ok": stride_ok,
                "reads_sectors_ceil_size_over_2048": (X.w(0x80086200) == 0x244207FF and
                                                      X.w(0x80086208) == 0x000292C2)},
            "ids": rows,
            "all_ten_agree": all(r["agree"] for r in rows),
            "mismatches": [r["id"] for r in rows if not r["agree"]]}


# ------------------------------------------------------------------ level functions
def func_range_end(X, start, floor=16):
    """End (exclusive) of the function that starts at `start`: the first
    `jr ra` + delay slot that is followed by `addiu sp,sp,-N` (next prologue)."""
    i = (start - B) // 4 + floor
    W = X.W
    while i + 2 < len(W):
        nxt = W[i + 2]
        if (W[i] == JR_RA and nxt >> 26 == 9 and eo.rs_(nxt) == 29 and eo.rt_(nxt) == 29
                and nxt & 0x8000):
            return B + 4 * (i + 2)
        i += 1
    return None


def explore_a1(X, start):
    """Follow both outcomes of every branch from `start` until `jal 0x8003846c`
    (the screen-change call); return the set of a1 constants at that call."""
    seen, found = set(), set()
    stack = [(start, None)]
    while stack:
        pc, a1 = stack.pop()
        for _ in range(64):
            if (pc, a1) in seen:
                break
            seen.add((pc, a1))
            w = X.w(pc)
            op = w >> 26
            if op == 0x0F and eo.rt_(w) == 5:
                a1 = (w & 0xFFFF) << 16
            elif op in (9, 13) and eo.rt_(w) == 5 and eo.rs_(w) == 5 and a1 is not None:
                a1 = (a1 + s16(w & 0xFFFF)) & 0xFFFFFFFF if op == 9 else a1 | (w & 0xFFFF)
            elif eo.dest_reg(w) == 5:
                a1 = None
            if op == 3 and eo.jal_target(w) == 0x8003846C:
                found.add(a1)
                break
            if op in (1, 4, 5, 6, 7):
                tgt = (pc + 4 + s16(w & 0xFFFF) * 4) & 0xFFFFFFFF
                stack.append((tgt, a1))
                pc += 8
                continue
            if op == 2:
                # unconditional jump; its delay slot only sets a0 in this dispatcher
                pc = eo.jal_target(w)
                continue
            if op == 0 and (w & 63) == 8:
                break
            pc += 4
    return found


def do_dispatcher(X):
    out = {"jump_table": H(0x80013910), "entries": []}
    for i in range(12):
        tgt = X.w(0x80013910 + 4 * i)
        consts = explore_a1(X, tgt)
        out["entries"].append({"index": i, "block": H(tgt),
                               "functions": sorted(H(c) for c in consts if c is not None),
                               "reaches_call_with_unknown_a1": None in consts})
    # index range check at the dispatcher
    out["index_check"] = {"sltiu_12_at": H(0x80032EC4), "word": "0x%08x" % X.w(0x80032EC4),
                          "ok": X.w(0x80032EC4) == 0x2C62000C,
                          "index_variable": "gp+252 = 0x800d76a8 (negated if negative at 0x80032EB0)",
                          "text": [X.text(a) for a in range(0x80032EA8, 0x80032EE8, 4)]}
    out["case10_condition"] = {"text": [X.text(a) for a in range(0x80032F78, 0x80032FA8, 4)],
                               "meaning": ("index 10: if word gp+2204 (0x800d7e48) >= 0 the "
                                           "function 0x8002e130 is called, otherwise 0x8002ac74")}
    return out


def level_info(X, name, start, end, ovl_id_set):
    W = X.W
    i0, i1 = (start - B) // 4, (end - B) // 4
    reads, sizes, jal_t, win_jal, win_abs, jalr = [], [], {}, [], [], 0
    ptr_readers, memcpy_sites, gp252, gp256 = [], [], [], []
    for i in range(i0, i1):
        pc = B + 4 * i
        w = W[i]
        op = w >> 26
        if op in (2, 3):
            t = eo.jal_target(w)
            if op == 3:
                jal_t[t] = jal_t.get(t, 0) + 1
                if t == READ_FILE:
                    reads.append((pc, arg_a0(X, i)))
                elif t == GET_SIZE:
                    sizes.append((pc, arg_a0(X, i)))
                elif t == MEMCPY:
                    memcpy_sites.append(pc)
            if WINDOW_LO <= t < WINDOW_HI:
                win_jal.append((pc, t))
        if op == 0 and (w & 63) == 9:
            jalr += 1
        if op == 0x23 and (w & 0xFFFF) == 0x5134 and W[i - 1] == (0x3C008001 | (eo.rs_(w) << 16)):
            ptr_readers.append(pc)
        if op == 0x2B and eo.rs_(w) == 28 and (w & 0xFFFF) in (252, 256):
            val = back_const(X, i, eo.rt_(w))
            (gp252 if (w & 0xFFFF) == 252 else gp256).append((pc, val))
    for r in scan_refs_range(X, i0, i1):
        if WINDOW_LO <= r.addr < WINDOW_HI and r.kind == "val" and r.op in (9, 13):
            win_abs.append((r.pc, r.addr))
    ids_const = sorted({a for _, a in reads if isinstance(a, int)})
    return {
        "name": name, "start": H(start), "end_exclusive": H(end),
        "read_file_calls": [{"pc": H(a), "id": (v if isinstance(v, int) else v)} for a, v in reads],
        "get_size_calls": [{"pc": H(a), "id": (v if isinstance(v, int) else v)} for a, v in sizes],
        "overlay_ids_read": sorted(set(ids_const) & ovl_id_set),
        "const_ids_read": ids_const,
        "dest_pointer_reads": [H(a) for a in ptr_readers],
        "memcpy_calls": [H(a) for a in memcpy_sites],
        "jal_into_window": [{"pc": H(a), "target": H(t)} for a, t in win_jal],
        "address_consts_into_window": [{"pc": H(a), "value": H(v)} for a, v in win_abs],
        "jalr_count": jalr,
        "stores_gp252": [{"pc": H(a), "value": v} for a, v in gp252],
        "stores_gp256": [{"pc": H(a), "value": v} for a, v in gp256],
        "callee_set": sorted(H(t) for t in jal_t),
    }


def scan_refs_range(X, i0, i1):
    return [r for r in ALL_REFS if B + 4 * i0 <= r.pc < B + 4 * i1]


def const_of(w):
    """Constant loaded into a register by w (addiu/ori from zero, move of zero), else None."""
    op = w >> 26
    if op in (9, 13) and eo.rs_(w) == 0:
        return s16(w & 0xFFFF) if op == 9 else w & 0xFFFF
    if op == 0 and (w & 63) in (0x21, 0x25) and eo.rs_(w) == 0 and eo.rt_(w) == 0:
        return 0
    return None


def back_const(X, i, reg, span=48):
    """Constant last written to `reg` before word index i (straight-line scan)."""
    for k in range(i - 1, max(i - span, 0), -1):
        w = X.W[k]
        if eo.dest_reg(w) == reg:
            c = const_of(w)
            return c if c is not None else "variable: " + eo.fmt(w, B + 4 * k)
        if eo.is_branch(w) and k < i - 1:
            return "unresolved (block boundary)"
    return "unresolved"


def arg_a0(X, i):
    """Where does a0 come from at the jal at word index i (delay slot first)."""
    W = X.W
    if eo.dest_reg(W[i + 1]) == 4:
        c = const_of(W[i + 1])
        return c if c is not None else "variable: " + eo.fmt(W[i + 1], B + 4 * (i + 1))
    for k in range(i - 1, max(i - 16, 0), -1):
        w = W[k]
        if eo.dest_reg(w) == 4:
            c = const_of(w)
            return c if c is not None else "variable: " + eo.fmt(w, B + 4 * k)
        if eo.is_branch(w) and k != i - 1:
            return "unresolved (block boundary)"
    return "unresolved"


# ------------------------------------------------------------------ 2. destination pointer
def do_dest_pointer(X, levels):
    W = X.W
    word = X.w(DEST_PTR)
    refs = [r for r in ALL_REFS if r.kind in ("load", "store") and r.addr == DEST_PTR]
    imm_sites = [(B + 4 * i, W[i]) for i in range(len(W))
                 if (W[i] & 0xFFFF) == 0x5134 and (W[i] >> 26) != 0]
    data_ptrs = [H(B + 4 * i) for i in range(len(W)) if W[i] == DEST_PTR]
    # array-base style references to the table that precedes the word
    near_vals = sorted({(r.pc, r.addr, r.indexed) for r in ALL_REFS
                        if r.kind == "val" and 0x80015100 <= r.addr <= DEST_PTR
                        and not (r.addr & 0xFFFF == 0)})
    stores = [r for r in refs if r.kind == "store"]
    gp_possible = (DEST_PTR - GP) if -0x8000 <= (DEST_PTR - GP) < 0x8000 else None
    readers = []
    for r in sorted(refs, key=lambda r: r.pc):
        i = (r.pc - B) // 4
        # the memcpy call that follows: jal 0x8009f31c within 16 words, delay slot `addu a0,s0,zero`
        nxt = None
        for k in range(i + 1, i + 16):
            if W[k] >> 26 == 3 and eo.jal_target(W[k]) == MEMCPY:
                nxt = (B + 4 * k, MEMCPY, W[k + 1] == 0x02002021)
                break
        lvl = next((L["name"] for L in levels if int(L["start"], 16) <= r.pc < int(L["end_exclusive"], 16)), None)
        readers.append({"pc": H(r.pc), "text": X.text(r.pc), "indexed": r.indexed,
                        "in_level_function": lvl,
                        "memcpy_call": {"pc": H(nxt[0]), "a0_is_loaded_pointer_in_delay_slot": nxt[2]} if nxt else None})
    neighbours = {H(a): "0x%08x" % X.w(a) for a in range(DEST_PTR - 8, DEST_PTR + 12, 4)}
    return {"address": H(DEST_PTR), "word": "0x%08x" % word, "equals_0x80130ff8": word == 0x80130FF8,
            "file_offset": H(0x800 + DEST_PTR - B), "in_text_file_range": True,
            "readers": readers, "reader_count": len(readers),
            "writers": [{"pc": H(r.pc), "text": X.text(r.pc)} for r in stores],
            "no_writer_found": len(stores) == 0,
            "instructions_with_immediate_0x5134": [{"pc": H(a), "text": eo.fmt(w, a)} for a, w in imm_sites],
            "data_words_equal_to_address": data_ptrs,
            "gp_relative_possible": gp_possible is not None,
            "gp_offset_would_be": (DEST_PTR - GP),
            "address_constants_of_neighbouring_table_below": [
                {"pc": H(pc), "value": H(a), "indexed": ix} for pc, a, ix in near_vals],
            "neighbouring_words": neighbours,
            "limits": ["Only direct (lui/gp based, tracked through moves and adds) addressing is excluded.",
                       "A write through a pointer computed from unrelated data, or by DMA or the BIOS, "
                       "cannot be excluded by a static scan."]}


# ------------------------------------------------------------------ 3. read_file call sites
def do_read_file(X, level_ranges):
    W = X.W
    sites = []
    for i, w in enumerate(W):
        if w >> 26 == 3 and eo.jal_target(w) == READ_FILE:
            pc = B + 4 * i
            a0 = arg_a0(X, i)
            lvl = next((n for n, (s, e) in level_ranges.items() if s <= pc < e), None)
            sites.append({"pc": H(pc), "id": a0, "level_function": lvl,
                          "segment_start": H(eo.Image(X.data[0x800:], B).func_start_before(pc))})
    const_sites = [s for s in sites if isinstance(s["id"], int)]
    var_sites = [s for s in sites if not isinstance(s["id"], int)]
    ovl_sites = [s for s in const_sites if 134 <= s["id"] <= 143]
    return {"call_sites_total": len(sites), "constant_id_sites": len(const_sites),
            "overlay_id_sites": [{"pc": s["pc"], "id": s["id"], "level_function": s["level_function"]}
                                 for s in ovl_sites],
            "overlay_id_sites_outside_level_functions": [s["pc"] for s in ovl_sites if s["level_function"] is None],
            "variable_or_unresolved_sites": var_sites,
            "constant_ids_outside_134_143": sorted({s["id"] for s in const_sites if not 134 <= s["id"] <= 143})}


def do_q50(X, rf):
    """Resolve the two variable-id read_file callers."""
    W = X.W
    var = {s["pc"] for s in rf["variable_or_unresolved_sites"]}
    res = {"variable_sites_found": sorted(var),
           "variable_sites_are_the_two_expected_plus_wrapper_site": var == {H(0x80085CF8), H(0x80085D74), H(0x8008635C)}}
    # shape of the id computation, decoded from the words
    shape = {}
    # site 1: lw v1,idx; sll v0,v1,3; subu v0,v0,v1; sll v0,v0,2; lui at,hi; addu; lw a0,off(at)
    for site, first in ((0x80085CF8, 0x80085CD4), (0x80085D74, 0x80085D50)):
        seq = [W[(first + 4 * k - B) // 4] for k in range(0, (site - first) // 4)]
        txt = [X.text(first + 4 * k) for k in range((site - first) // 4)]
        # decode: lui a0,0x800d ; lw a0,0x7e48(a0) ; nop ; sll v1,a0,3 ; subu v1,v1,a0 ; sll v1,v1,2 ;
        #         lui at,0x800b ; addu at,at,v1 ; lw a0,off(at)
        ok = (len(seq) == 9 and seq[0] >> 26 == 0x0F and (seq[0] & 0xFFFF) == 0x800D and
              seq[1] >> 26 == 0x23 and (seq[1] & 0xFFFF) == 0x7E48 and
              (seq[3] & 0x7FF) == ((3 << 6) | 0) and seq[4] & 63 == 0x23 and (seq[5] >> 6) & 31 == 2 and
              seq[6] >> 26 == 0x0F and seq[7] & 63 == 0x21 and seq[8] >> 26 == 0x23)
        hi = seq[6] & 0xFFFF
        off = s16(seq[8] & 0xFFFF)
        shape[H(site)] = {"code": txt, "shape_ok": ok,
                          "index_variable": "0x800d7e48 (= gp+2204)",
                          "record_stride_bytes": 28,
                          "id_word_address": "%s + 28*index" % H(((hi << 16) + off) & 0xFFFFFFFF),
                          "id_word_offset_in_record_from_0x800ac43c": ((hi << 16) + off - 0x800AC43C) & 0xFFFFFFFF}
    res["id_computation"] = shape
    # the table
    TB, STRIDE, NREC = 0x800AC43C, 28, 25
    recs = []
    for i in range(NREC):
        a = TB + STRIDE * i
        recs.append({"index": i, "addr": H(a), "words": ["0x%x" % X.w(a + 4 * k) for k in range(7)]})
    res["record_table"] = {"base": H(TB), "stride": STRIDE, "records_decoded": NREC,
                           "rows": recs,
                           "note": "words 0..6 of each record; word 1 and word 3 are read_file ids, "
                                   "word 2 is a pointer (zero = skip the second read), word 6 is a get_size id"}
    ids1 = [X.w(TB + STRIDE * i + 4) for i in range(NREC)]
    ids2 = [X.w(TB + STRIDE * i + 12) for i, in [(i,) for i in range(NREC)] if X.w(TB + STRIDE * i + 8) != 0]
    res["reachable_ids_site_0x80085cf8"] = sorted(set(ids1))
    res["reachable_ids_site_0x80085d74"] = sorted(set(ids2))
    allv = set(ids1) | set(ids2)
    res["reachable_ids_union"] = sorted(allv)
    res["reachable_ids_in_134_143"] = sorted(i for i in allv if 134 <= i <= 143)
    # records beyond the table: are words 25.. plausible records? (they are not)
    res["record_25_words"] = ["0x%x" % X.w(TB + STRIDE * 25 + 4 * k) for k in range(7)]
    # index domain: all stores to 0x800d7e48
    stores = [r for r in ALL_REFS if r.kind == "store" and r.addr == 0x800D7E48]
    res["index_writers"] = [{"pc": H(r.pc), "text": X.text(r.pc)} for r in sorted(stores, key=lambda r: r.pc)]
    exp_a = {0x8002A6D8: 0x2402FFFF, 0x8002A6DC: 0xAF82089C}
    exp_b = {0x8002AB50: 0x06A10003, 0x8002AB54: 0x2AA20019, 0x8002AB58: 0x24150018,
             0x8002AB5C: 0x2AA20019, 0x8002AB60: 0x14400002, 0x8002AB64: 0x24040050,
             0x8002AB68: 0x0000A821, 0x8002AB6C: 0x24050014, 0x8002AB70: 0xAF95089C}
    res["index_writer_code_as_expected"] = all(X.w(a) == w for a, w in {**exp_a, **exp_b}.items())
    res["index_writer_code"] = {"set_minus_one": [X.text(a) for a in sorted(exp_a)],
                                "clamp_then_store": [X.text(a) for a in sorted(exp_b)]}
    # nothing may jump into the clamp between its first branch and the store
    lo, hi = 0x8002AB54, 0x8002AB70
    enter = []
    for i, w in enumerate(W):
        pc = B + 4 * i
        op = w >> 26
        t = None
        if op in (1, 4, 5, 6, 7):
            t = (pc + 4 + s16(w & 0xFFFF) * 4) & 0xFFFFFFFF
        elif op in (2, 3):
            t = eo.jal_target(w)
        if t is not None and lo <= t <= hi and not (0x8002AB50 <= pc <= 0x8002AB6C):
            enter.append(H(pc))
    res["jumps_into_clamp_from_outside"] = enter
    res["index_domain"] = ("-1 (set at 0x8002a6dc), or 0..24 (clamped before the store at 0x8002ab70: "
                           "negative -> 24, >= 25 -> 0)")
    # writers into the record table
    tw = [r for r in ALL_REFS if r.kind == "store" and 0x800AC438 <= r.addr < TB + STRIDE * NREC + 4]
    res["stores_into_record_table"] = [{"pc": H(r.pc), "text": X.text(r.pc)} for r in tw]
    # callers of the enclosing function
    FN = 0x80085AF8
    callers = [H(B + 4 * i) for i, w in enumerate(W) if w >> 26 in (2, 3) and eo.jal_target(w) == FN]
    callers += [H(r.pc) for r in ALL_REFS if r.kind == "val" and r.addr == FN]
    callers += [H(B + 4 * i) for i, w in enumerate(W) if w == FN]
    res["enclosing_function"] = {"start": H(FN),
                                 "entry_text": [X.text(a) for a in range(FN, FN + 24, 4)],
                                 "negative_index_branch": X.text(0x80085B10),
                                 "negative_index_path": ("0x80085e08: get_size(59), alloc, "
                                                         "read_file(59) at 0x80085e34 (constant id 59)"),
                                 "callers": sorted(callers)}
    return res


def callers_of(X, t):
    out = [{"kind": "jal" if w >> 26 == 3 else "j", "pc": B + 4 * i} for i, w in enumerate(X.W)
           if w >> 26 in (2, 3) and eo.jal_target(w) == t]
    out += [{"kind": "address constant", "pc": r.pc} for r in ALL_REFS
            if r.kind == "val" and r.addr == t and r.op in (9, 13)]
    out += [{"kind": "data word", "pc": B + 4 * i} for i, w in enumerate(X.W) if w == t]
    return sorted(out, key=lambda c: (c["pc"], c["kind"]))


def a0_untouched(X, start, jal_pc):
    """True if a0 is not written, and no branch occurs, between start and the jal."""
    for a in range(start, jal_pc, 4):
        w = X.w(a)
        if eo.dest_reg(w) == 4 or eo.is_branch(w):
            return False
    return True


def seg_start(X, pc):
    return eo.Image(X.data[0x800:], B).func_start_before(pc)


def do_wrapper(X):
    """The third variable-id read_file caller (pc 0x8008635c) inside wrapper 0x80086324."""
    WR = 0x80086324
    res = {"wrapper": H(WR), "read_file_site": H(0x8008635C),
           "code": [X.text(a) for a in range(WR, WR + 0x58, 4)],
           "behaviour": "stores a0 (the id) at gp+1652; get_size(a0) rounded up to 2048 -> allocator "
                        "0x800865c0 -> read_file(a0, buffer); returns a0"}
    res["wrapper_shape_ok"] = (X.w(0x8008632C) == 0x00808021 and X.w(0x80086354) == 0x02002021 and
                               X.w(0x8008635C) == 0x0C021875)
    cs = callers_of(X, WR)
    res["callers_of_wrapper"] = [{"kind": c["kind"], "pc": H(c["pc"])} for c in cs]
    lvl1 = {}
    for c in cs:
        if c["kind"] == "jal":
            st = seg_start(X, c["pc"])
            lvl1[st] = {"jal": H(c["pc"]), "a0_passed_through_unchanged": a0_untouched(X, st, c["pc"])}
    res["passthrough_functions"] = {H(k): v for k, v in sorted(lvl1.items())}
    loaders, callee_of = {}, {}
    for f in sorted(lvl1):
        for c in callers_of(X, f):
            loaders.setdefault(seg_start(X, c["pc"]), []).append(c)
            callee_of[seg_start(X, c["pc"])] = f
    shape, tables = {}, {}
    for g in sorted(loaders):
        words = [X.w(g + 4 * k) for k in range(12)]
        lw = next(((g + 4 * k, words[k]) for k in range(12) if words[k] >> 26 == 0x23
                   and eo.rt_(words[k]) == 4 and eo.rs_(words[k]) == 1), None)
        lui = next(((g + 4 * k, words[k]) for k in range(12) if words[k] >> 26 == 0x0F
                    and eo.rt_(words[k]) == 1), None)
        if lw is None or lui is None:
            shape[H(g)] = {"shape_ok": False}
            continue
        base = (((lui[1] & 0xFFFF) << 16) + s16(lw[1] & 0xFFFF)) & 0xFFFFFFFF
        if words[1:6] == [0x000430C0, 0x00C43021, 0x00063080, 0x00C43021, 0x000630C0]:
            stride = 296        # ((a0*8 + a0)*4 + a0)*8
        elif words[1:4] == [0x00043180, 0x00C43023, 0x00063100]:
            stride = 1008       # (a0*64 - a0)*16
        else:
            stride = None
        callers = []
        for c in callers_of(X, g):
            seg = seg_start(X, c["pc"])
            callers.append({"kind": c["kind"], "pc": H(c["pc"]), "in_function_segment": H(seg),
                            "index_arg_a0": arg_a0(X, (c["pc"] - B) // 4) if c["kind"] == "jal" else None})
        shape[H(g)] = {"shape_ok": stride is not None, "table_base": H(base), "record_stride": stride,
                       "calls_function": H(callee_of[g]),
                       "multiply_and_load": [X.text(g + 4 * k) for k in range(1, 12)
                                             if words[k] != 0 and k in (1, 2, 3, 4, 5, 6, 7, 8, 9)],
                       "load": X.text(lw[0]), "callers": callers}
        if stride:
            tables[g] = (base, stride)
    res["id_table_functions"] = shape
    TB = 0x800AC43C
    rec_w5 = sorted({X.w(TB + 28 * i + 20) for i in range(25)})
    dom, unresolved, via_record = set(), [], False
    for g, info in shape.items():
        for c in info.get("callers", []):
            a = c["index_arg_a0"]
            if isinstance(a, int):
                dom.add(a)
            elif a == "variable: lw a0,-15280(at)":
                via_record = True        # 0x800ac43c + 20: word 5 of the 28-byte record
            else:
                unresolved.append({"function": g, "pc": c["pc"], "arg": a})
    if via_record:
        dom |= set(rec_w5)
    res["index_domain"] = sorted(dom)
    res["record_word5_values"] = {"values": rec_w5, "used_by_variable_sites": via_record}
    res["index_sources_unresolved"] = unresolved
    res["id_tables"] = {H(g): {"table_base": H(b), "stride": st,
                               "ids_index_0_to_28": [X.w(b + st * i) for i in range(29)],
                               "word_at_index_29": X.w(b + st * 29)}
                        for g, (b, st) in sorted(tables.items())}
    rid = {X.w(b + st * i) for (b, st) in tables.values() for i in dom}
    res["reachable_ids_direct_callers"] = sorted(rid)
    res["reachable_ids_in_134_143"] = sorted(i for i in rid if 134 <= i <= 143)
    res["limits"] = ["The wrapper address is also stored in a callback table built at pc 0x80082df4 "
                     "(function 0x80082d78, table passed to 0x800a3f8c). Calls made through that table "
                     "are indirect and their id argument is not statically known."]
    return res


# ------------------------------------------------------------------ 4. ovr files
def addr_prefix(ws, base, size):
    """Own rule (not the one in exe_overlays.py): the longest leading run of words
    that are each either 0 (a null entry) or a 4-aligned value inside
    [base, base+size).  Trailing zeros of the run are trimmed (they could be the
    first nops of code).  A run with fewer than 4 non-zero words is not a table.
    Returns (words_in_table, non_zero_words, zeros_inside, trailing_zeros_trimmed)."""
    n = 0
    while n < len(ws) and (ws[n] == 0 or (base <= ws[n] < base + size and ws[n] % 4 == 0)):
        n += 1
    m = n
    while m > 0 and ws[m - 1] == 0:
        m -= 1
    nz = sum(1 for x in ws[:m] if x)
    if nz < 4:
        return 0, 0, 0, 0
    return m, nz, m - nz, n - m


def do_ovr_files(files, rd, base, cand):
    out = []
    for fid, f in zip(IDS, files):
        if not f["path"].endswith(".OVR"):
            continue
        data = rd.read_extent(f["lba"], f["size_bytes"])
        ws = struct.unpack("<%dI" % (len(data) // 4), data[:len(data) // 4 * 4])
        n, nz, zin, ztrim = addr_prefix(ws, base, len(data))
        pre = [x for x in ws[:n] if x]
        r = {"id": fid, "name": f["name"], "path": f["path"], "sha256": hashlib.sha256(data).hexdigest(),
             "size": len(data), "sectors_on_disc": f["sectors"],
             "size_mod_2048": len(data) % 2048, "padded_size": f["sectors"] * 2048,
             "tail_pad_bytes": f["sectors"] * 2048 - len(data),
             "size_multiple_of_4": len(data) % 4 == 0,
             "size_is_sector_multiple": len(data) % 2048 == 0,
             "end_in_ram_exclusive": H(base + len(data)),
             "address_table_words": n, "address_table_pointer_words": nz,
             "address_table_null_words": zin, "zero_words_after_table_before_code": ztrim}
        if n:
            r["address_table_range"] = [H(min(pre)), H(max(pre))]
            r["address_table_all_pointers_inside_image"] = True
            r["address_table_monotonic_nondecreasing"] = all(a <= b for a, b in zip(pre, pre[1:]))
            r["first_word_after_table"] = "0x%08x" % ws[n]
            r["first_word_after_table_text"] = eo.fmt(ws[n], base + 4 * n)
        else:
            r["first_word"] = "0x%08x" % ws[0]
            r["first_word_text"] = eo.fmt(ws[0], base)
        c = next((o for o in cand["overlays"] if o["name"] == f["name"]), None)
        cw = (c.get("leading_address_table") or {}).get("words", 0) if c else None
        r["exe_overlays_py_table_words"] = cw
        r["prefix_agrees_with_exe_overlays_py"] = (cw == n) if cw is not None else None
        out.append(r)
    return out


# ------------------------------------------------------------------ 5. second checks
def starts_of(ws):
    """Function-start offsets (word indexes): 0 and the word after `jr ra` + delay slot."""
    s = {0}
    for i, w in enumerate(ws):
        if w == JR_RA and i + 2 < len(ws):
            s.add(i + 2)
    return s


def prologue_at(ws, k, span=10):
    for q in range(k, min(k + span, len(ws))):
        x = ws[q]
        if x >> 26 == 9 and eo.rs_(x) == 29 and eo.rt_(x) == 29 and x & 0x8000:
            return True
    return False


def land_ok(ws, fs, k):
    """Function-start-like word index k: first word, word after `jr ra`+delay slot,
    or an `addiu sp,sp,-N` within the next 10 words."""
    return k in fs or prologue_at(ws, k)


def do_second_checks(X, levels, ovr_data, base):
    """Two checks per image that do not use the EXE loader pointer or the
    "lui+addiu constant lands on a function start" rule:
      E  the EXE's own call sites (jal/j into the window, grouped by the level
         function that loads this image) must land on function-start-like words
         of the image.  Swept over 2048 candidate bases.
      C  containment: every address the image itself uses (jal/j targets, data
         pointers, lui+addiu/ori constants) at or above 0x80130FF8 (the end of
         the BSS that crt0 clears) must fall inside [base, base+size).  This
         bounds the base to an interval.
    The joint set is E's bases inside C's interval."""
    W = X.W
    win_sites = []
    for i, w in enumerate(W):
        if w >> 26 in (2, 3):
            t = eo.jal_target(w)
            if WINDOW_LO <= t < WINDOW_HI:
                win_sites.append((B + 4 * i, t))
    res = {"exe_window_call_sites": len(win_sites),
           "exe_window_call_unique_targets": len({t for _, t in win_sites}),
           "sweep": "bases 0x80130000..0x80131ffc, step 4 (2048 candidates)",
           "landing_rule": "word index 0, or the word after `jr ra`+delay slot, or an `addiu sp,sp,-N` within 10 words",
           "constants_lower_limit": H(WINDOW_LO) + " (crt0 clears BSS up to here, T1.4)"}
    names = {"TEMPLE.OVR": "TEMPLE", "EARTH.OVR": "EARTH", "WIND.OVR": "WIND", "WATER.OVR": "WATER",
             "PRISON.OVR": "PRISON", "FIRE.OVR": "FIRE", "BRIDGE.OVR": "BRIDGE", "FORTRESS.OVR": "FORTRESS"}
    lv = {L["name"]: L for L in levels}
    parsed = {}
    for on, d in ovr_data.items():
        if on.endswith(".OVR"):
            ws = struct.unpack("<%dI" % (len(d) // 4), d[:len(d) // 4 * 4])
            parsed[on] = (ws, starts_of(ws), len(d))
    per = {}
    for on, nm in sorted(names.items()):
        ws, fs, n = parsed[on]
        L = lv[nm]
        lo, hi = int(L["start"], 16), int(L["end_exclusive"], 16)
        sites = sorted((pc, t) for pc, t in win_sites if lo <= pc < hi)
        density = sum(1 for k in range(len(ws)) if land_ok(ws, fs, k)) / len(ws)

        def land(b, t, ws=ws, fs=fs, n=n):
            off = t - b
            return 0 <= off < n and off % 4 == 0 and land_ok(ws, fs, off // 4)
        r = {"level_function": L["start"], "exe_sites": [{"pc": H(pc), "target": H(t)} for pc, t in sites],
             "landing_density_in_image": round(density, 4)}
        e = {"sites": len(sites),
             "land_function_start_at_true_base": sum(1 for _, t in sites if 0 <= t - base < n and
                                                     ((t - base) // 4) in fs and (t - base) % 4 == 0),
             "land_sp_prologue_at_true_base": sum(1 for _, t in sites if 0 <= t - base < n and
                                                  prologue_at(ws, (t - base) // 4)),
             "land_rule_at_true_base": sum(1 for _, t in sites if land(base, t))}
        eset = [b for b in range(0x80130000, 0x80132000, 4) if all(land(b, t) for _, t in sites)] if sites else []
        e["bases_where_all_sites_land"] = len(eset)
        e["true_base_in_set"] = base in eset
        ctrl = {}
        for on2, (w2, f2, n2) in sorted(parsed.items()):
            if on2 != on:
                ctrl[on2] = sum(1 for _, t in sites if 0 <= t - base < n2 and (t - base) % 4 == 0
                                and land_ok(w2, f2, (t - base) // 4))
        e["same_sites_in_other_images_at_true_base"] = ctrl
        r["E_exe_call_sites"] = e
        # C: containment interval
        img = eo.Image(b"".join(struct.pack("<I", x) for x in ws), 0)
        jt = [eo.jal_target(w) for w in ws if w >> 26 in (2, 3)]
        pt = [w for w in ws if w % 4 == 0]
        ab = [a for _, a, k in img.abs_refs(0x8013, 0x8014) if k == "addr"]
        vals = {"jump_targets": jt, "data_pointers": pt, "address_constants": ab}
        allv, c = [], {}
        for key, v in vals.items():
            vv = sorted(x for x in v if WINDOW_LO <= x < 0x80140000)
            c[key] = {"count": len(vv), "min": H(vv[0]) if vv else None, "max": H(vv[-1]) if vv else None}
            allv += vv
        c["lowest_address"] = H(min(allv)) if allv else None
        c["highest_address"] = H(max(allv)) if allv else None
        if allv:
            ilo, ihi = max(allv) - n + 4, min(allv)
            c["base_interval"] = [H(ilo), H(ihi)]
            c["interval_width_bytes"] = ihi - ilo + 4
            c["true_base_in_interval"] = ilo <= base <= ihi
            c["highest_address_to_image_end_bytes"] = base + n - max(allv)
            joint = [b for b in eset if ilo <= b <= ihi]
        else:
            joint = []
        r["C_containment"] = c
        r["joint"] = {"bases": [H(b) for b in joint[:8]], "count": len(joint),
                      "true_base_is_only_one": joint == [base]}
        # supplementary: the image's own jal targets
        own_in = [eo.jal_target(w) for w in ws if w >> 26 == 3 and 0 <= eo.jal_target(w) - base < n]
        r["A1_own_jal_targets_in_image_at_true_base"] = {
            "in_image": len(own_in),
            "on_function_start": sum(1 for t in own_in if ((t - base) // 4) in fs and (t - base) % 4 == 0)}
        per[on] = r
    res["per_overlay"] = per
    return res


# ------------------------------------------------------------------ main
ALL_REFS = []


def main():
    global ALL_REFS
    X = Exe(load_exe())
    files_all = json.load(open(p(FILES_JSON)))["files"]
    fmap = {f["path"]: f for f in files_all}
    ovl_paths = sorted((f for f in files_all if f["path"].startswith("/OVERLAYS/")), key=lambda f: f["lba"])
    files = ovl_paths
    if len(files) != 10:
        raise SystemExit("expected 10 /OVERLAYS files, found %d" % len(files))
    rd = open_disc()
    ALL_REFS = scan_refs(X)

    result = {"tool": "tools/overlay_facts.py"}
    # boot EXE cross-check: work/disc copy vs the .bin
    boot = fmap["/SLUS_004.76"]
    from_bin = rd.read_extent(boot["lba"], boot["size_bytes"])
    result["boot_exe"] = {"path": "/SLUS_004.76", "size": len(X.data), "sha256": hashlib.sha256(X.data).hexdigest(),
                          "identical_to_bytes_read_from_bin": from_bin == X.data,
                          "disc_lba": boot["lba"]}
    result["tables"] = do_tables(X, files, rd)

    # level functions from the dispatcher
    disp = do_dispatcher(X)
    result["dispatcher"] = disp
    lvl_starts = {}
    for e in disp["entries"]:
        for fnaddr in e["functions"]:
            lvl_starts.setdefault(int(fnaddr, 16), []).append(e["index"])
    nine = [0x8002B688, 0x8002BD10, 0x8002C420, 0x8002CB34, 0x8002D198, 0x8002DA94, 0x8002E130,
            0x8002E7F0, 0x8002EFBC]
    result["dispatcher"]["level_function_set_matches_docs"] = all(a in lvl_starts for a in nine)
    result["dispatcher"]["other_functions_in_table"] = sorted(H(a) for a in lvl_starts if a not in nine)
    names = {0x8002B688: "TEMPLE", 0x8002BD10: "EARTH", 0x8002C420: "WIND", 0x8002CB34: "WATER",
             0x8002D198: "PRISON", 0x8002DA94: "FIRE", 0x8002E130: "FIRE2", 0x8002E7F0: "BRIDGE",
             0x8002EFBC: "FORTRESS"}
    srt = sorted(nine)
    ends = {a: (srt[i + 1] if i + 1 < len(srt) else func_range_end(X, a)) for i, a in enumerate(srt)}
    ovl_id_set = set(IDS)
    levels = [level_info(X, names[a], a, ends[a], ovl_id_set) for a in srt]
    for L in levels:
        L["dispatcher_indexes"] = lvl_starts.get(int(L["start"], 16), [])
    result["levels"] = levels
    ranges = {L["name"]: (int(L["start"], 16), int(L["end_exclusive"], 16)) for L in levels}

    result["dest_pointer"] = do_dest_pointer(X, levels)
    rf = do_read_file(X, ranges)
    result["read_file"] = rf
    result["q50_variable_id_callers"] = do_q50(X, rf)
    result["q50_wrapper_0x80086324"] = do_wrapper(X)

    cand = json.load(open(p(CAND_JSON)))
    base = X.w(DEST_PTR)
    result["ovr_files"] = do_ovr_files(files, rd, base, cand)

    ovr_data = {f["name"]: rd.read_extent(f["lba"], f["size_bytes"]) for f in files}
    result["second_checks"] = do_second_checks(X, levels, ovr_data, base)

    # Q51: the two FIRE level functions side by side
    A = next(L for L in levels if L["name"] == "FIRE")
    C = next(L for L in levels if L["name"] == "FIRE2")
    sa, sc = set(A["callee_set"]), set(C["callee_set"])
    result["fire_sites"] = {
        "FIRE_0x8002da94": A, "FIRE2_0x8002e130": C,
        "callees_only_in_0x8002da94": sorted(sa - sc),
        "callees_only_in_0x8002e130": sorted(sc - sa),
        "const_ids_only_in_0x8002da94": sorted(set(A["const_ids_read"]) - set(C["const_ids_read"])),
        "const_ids_only_in_0x8002e130": sorted(set(C["const_ids_read"]) - set(A["const_ids_read"])),
        "const_ids_in_both": sorted(set(C["const_ids_read"]) & set(A["const_ids_read"])),
        "same_overlay_id": A["overlay_ids_read"] == C["overlay_ids_read"] == [137],
        "each_has_one_dest_pointer_read_and_one_memcpy": (len(A["dest_pointer_reads"]) == 1 and
                                                          len(C["dest_pointer_reads"]) == 1 and
                                                          len(A["memcpy_calls"]) == 1 and len(C["memcpy_calls"]) == 1),
    }

    sc = result["second_checks"]["per_overlay"]
    q50 = result["q50_variable_id_callers"]
    q50w = result["q50_wrapper_0x80086324"]
    result["summary"] = {
        "tables_all_ten_agree": result["tables"]["all_ten_agree"],
        "dest_pointer_is_0x80130ff8": result["dest_pointer"]["equals_0x80130ff8"],
        "dest_pointer_readers": result["dest_pointer"]["reader_count"],
        "dest_pointer_writers": len(result["dest_pointer"]["writers"]),
        "read_file_variable_sites": [s_["pc"] for s_ in rf["variable_or_unresolved_sites"]],
        "variable_sites_reach_overlay_ids_134_143": bool(q50["reachable_ids_in_134_143"] or
                                                         q50w["reachable_ids_in_134_143"]),
        "variable_sites_with_statically_unknown_callers": ["0x8008635c (callback table at 0x80082df4)"],
        "address_table_prefix_agrees_with_exe_overlays_py": all(
            r["prefix_agrees_with_exe_overlays_py"] for r in result["ovr_files"]),
        "address_table_words": {r["name"]: r["address_table_words"] for r in result["ovr_files"]},
        "second_check_unique_base": {k: v["joint"]["true_base_is_only_one"] for k, v in sorted(sc.items())},
    }
    os.makedirs(os.path.dirname(p(OUT)), exist_ok=True)
    with open(p(OUT), "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")

    # console summary
    t = result["tables"]
    print("tables: all ten agree = %s, mismatches = %s" % (t["all_ten_agree"], t["mismatches"]))
    print("dest pointer 0x80015134 = %s, readers = %d, writers = %d" % (
        result["dest_pointer"]["word"], result["dest_pointer"]["reader_count"],
        len(result["dest_pointer"]["writers"])))
    print("read_file sites: %d total, %d variable" % (rf["call_sites_total"],
                                                      len(rf["variable_or_unresolved_sites"])))
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
