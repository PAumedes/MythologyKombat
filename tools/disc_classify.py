#!/usr/bin/env python3
"""Classify every file on the disc by format and extract it (T1.3).

Input : work/disc_files.json (T1.1, tools/disc_list.py) and the disc image.
Output: work/disc_classes.json (deterministic: no timestamps, no absolute
        paths; files sorted by path) and extracted files under work/extracted/.

Every file gets a primary tag, optional secondary tags, and evidence strings,
each evidence item carrying a kind:
  magic       signature bytes at a fixed offset
  structure   internal fields that must be self-consistent (sizes, tables)
  subheader   CD-XA sector subheader bits
  heuristic   statistical test (MIPS code density, SPU-ADPCM block validity)
  content     whole-file content test (filler pattern, printable text)
  hint        extension/directory name; supporting evidence only, never alone

Tags: PS-X EXE, STR video, XA audio, TIM image, VAB, VAG, SEQ, SEP,
overlay candidate, SPU-ADPCM (headerless), magic container, offset-table
container, u16-id-table container, filler, text, unknown.  The tags after
"overlay candidate" are not in the task list; they
are added only where a verifiable rule exists, so that "unknown" stays honest.

Extraction (work/extracted/<disc path>):
  - Form 1 files: the raw 2048-byte user-data bytes, cut to the ISO size.
  - STR files: the raw 2352-byte sectors (sync, header, subheader, payload,
    EDC/ECC) as <disc path>.raw2352, because Form 2 sectors lose data when
    reduced to 2048-byte user data.  --no-extract skips all extraction.

Standard library only.  Read-only on the disc image.

Usage:
  python -I tools/disc_classify.py [--files PATH] [--out PATH] [--no-extract]
"""
import argparse
import hashlib
import json
import math
import os
import random
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from disc_identify import DiscError, MODES, SYNC, parse_cue  # noqa: E402
from disc_list import Track  # noqa: E402

RAW = 2352
THRESH_MIPS_SCORE = 0.80      # see calibrate(); EXE text 0.855, non-code max < 0.65
THRESH_MIPS_MIN_NONZERO = 256
ADPCM_MIN_BLOCKS = 2000       # non-zero 16-byte blocks needed to claim headerless SPU-ADPCM
ADPCM_MIN_FRACTION = 0.97
PRIORITY = ["PS-X EXE", "STR video", "XA audio", "TIM image", "VAB", "VAG", "SEQ", "SEP",
            "overlay candidate", "SPU-ADPCM (headerless)", "magic container",
            "offset-table container", "u16-id-table container", "filler", "text", "unknown"]
MAGICS = [(b"pBAV", "VAB"), (b"VAGp", "VAG"), (b"pQES", "SEQ"), (b"SEQp", "SEP")]
# Magics seen at offset 0 in this disc's own files; their meaning is NOT claimed.
CUSTOM_MAGICS = [(b"\xdd\xcc\xbb\xaa", "bytes DD CC BB AA (u32 0xAABBCCDD)"),
                 (b"\x33\x22\x11\x00", "bytes 33 22 11 00 (u32 0x00112233)"),
                 (b"SPSX", "ASCII 'SPSX'"), (b"SSEQ", "ASCII 'SSEQ'")]


def ev(kind, text):
    return {"kind": kind, "text": text}


# ---------------------------------------------------------------- reading ----

def raw_sectors(trk, lba, count):
    """Raw 2352-byte sectors of track 1 (MODE2/2352 only), as one bytes object."""
    if trk.size != RAW:
        raise DiscError("classification needs raw 2352-byte sectors (cue mode %s)" % trk.mode)
    if lba < 0 or lba + count > trk.sectors:
        raise DiscError("extent %d+%d outside track" % (lba, count))
    trk.f.seek((trk.start + lba) * RAW)
    buf = trk.f.read(count * RAW)
    if len(buf) != count * RAW:
        raise DiscError("short read at LBA %d" % lba)
    return buf


def entropy(b, limit=1 << 20):
    b = b[:limit]
    if not b:
        return 0.0
    n = len(b)
    c = [0] * 256
    for v in b:
        c[v] += 1
    return -sum(x / n * math.log2(x / n) for x in c if x)


# ------------------------------------------------------------ MIPS scoring ----

def mips_valid(w):
    """Strict check that a non-zero 32-bit word is a well-formed common R3000 instruction."""
    op = w >> 26
    rs = (w >> 21) & 31
    rt = (w >> 16) & 31
    rd = (w >> 11) & 31
    sh = (w >> 6) & 31
    fn = w & 63
    if op == 0:
        if fn in (0, 2, 3):
            return rs == 0
        if fn in (4, 6, 7, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x2A, 0x2B):
            return sh == 0
        if fn == 8:
            return rt == 0 and rd == 0 and sh == 0
        if fn == 9:
            return rt == 0 and sh == 0
        if fn in (0xC, 0xD):
            return True
        if fn in (0x10, 0x12):
            return rs == 0 and rt == 0 and sh == 0
        if fn in (0x11, 0x13):
            return rt == 0 and rd == 0 and sh == 0
        if fn in (0x18, 0x19, 0x1A, 0x1B):
            return rd == 0 and sh == 0
        return False
    if op == 1:
        return rt in (0, 1, 16, 17)
    if op in (2, 3):                      # j/jal target inside 2 MiB of RAM
        return (w & 0x3FFFFFF) < 0x80000
    if op in (4, 5):
        return True
    if op in (6, 7):
        return rt == 0
    if 8 <= op <= 14:
        return True
    if op == 15:                          # lui
        return rs == 0
    if op == 0x10:                        # cop0
        return rs in (0, 4, 16)
    if op == 0x12:                        # cop2 (GTE)
        return bool(w & (1 << 25)) or rs in (0, 2, 4, 6)
    if op in (0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x28, 0x29, 0x2A, 0x2B, 0x2E, 0x32, 0x3A):
        return rs != 0                    # base register $zero: pointer-table words, not code
    return False


def mips_score(b):
    n = len(b) // 4
    ws = struct.unpack("<%dI" % n, b[:n * 4])
    nz = [w for w in ws if w]
    valid = sum(1 for w in nz if mips_valid(w))
    return {"score": round(valid / len(nz), 4) if nz else 0.0,
            "nonzero_words": len(nz), "words": n,
            "prologues": sum(1 for w in ws if (w >> 16) == 0x27BD and (w & 0x8000)),
            "jr_ra": sum(1 for w in ws if w == 0x03E00008),
            "jal": sum(1 for w in ws if (w >> 26) == 3 and (w & 0x3FFFFFF) < 0x80000),
            "lui": sum(1 for w in ws if (w >> 26) == 15)}


def leading_pointer_run(b):
    n = len(b) // 4
    ws = struct.unpack("<%dI" % min(n, 4096), b[:min(n, 4096) * 4])
    run = []
    for w in ws:
        if 0x80000000 <= w < 0x80200000:
            run.append(w)
        else:
            break
    return run


def calibrate(exe_text, samples):
    """Score reference data so the threshold is not a guess."""
    rnd = random.Random(1)
    rb = bytes(rnd.randrange(256) for _ in range(200000))
    out = {"exe_text_section": mips_score(exe_text),
           "random_bytes_seed1_200000": mips_score(rb)}
    for name, blob in samples:
        out[name] = mips_score(blob)
    return out


# ------------------------------------------------------------------- TIM ----

def tim_at(b, o):
    """Return (end_offset, info) if a structurally valid TIM starts at o, else None."""
    n = len(b)
    if o + 20 > n or b[o:o + 4] != b"\x10\x00\x00\x00":
        return None
    flags = struct.unpack_from("<I", b, o + 4)[0]
    if flags not in (0, 1, 2, 3, 8, 9, 10, 11):
        return None
    pmode = flags & 3
    has_clut = bool(flags & 8)
    if (pmode in (0, 1)) != has_clut:     # 4/8bpp need a CLUT; 16/24bpp do not
        return None
    p = o + 8
    clut = None
    if has_clut:
        bnum, x, y, w, h = struct.unpack_from("<IHHHH", b, p)
        if bnum != 12 + w * h * 2 or not (0 < w <= 1024 and 0 < h <= 512 and x < 1024 and y < 512):
            return None
        if p + bnum > n:
            return None
        clut = (w, h)
        p += bnum
    if p + 12 > n:
        return None
    bnum, x, y, w, h = struct.unpack_from("<IHHHH", b, p)
    if bnum != 12 + w * h * 2 or not (0 < w <= 1024 and 0 < h <= 512 and x < 1024 and y < 512):
        return None
    if p + bnum > n:
        return None
    px_w = w * {0: 4, 1: 2, 2: 1, 3: 2 / 3.0}[pmode]
    return p + bnum, {"bpp": (4, 8, 16, 24)[pmode], "clut": clut, "vram_xy": (x, y),
                      "width_px": int(round(px_w)), "height": h}


def scan_tims(b):
    """4-byte-aligned scan; returns list of (offset, end, info)."""
    out = []
    i = b.find(b"\x10\x00\x00\x00")
    while i != -1:
        if i % 4 == 0:
            r = tim_at(b, i)
            if r:
                out.append((i, r[0], r[1]))
        i = b.find(b"\x10\x00\x00\x00", i + 1)
    return out


# ------------------------------------------------------------ SPU-ADPCM ----

def adpcm_stats(b):
    """Best 16-byte alignment (0..240 step 16 is meaningless; try 0..15 byte shifts of 2)."""
    best = None
    for al in range(0, 16, 2):
        nzb = ok = 0
        for o in range(al, len(b) - 15, 16):
            blk = b[o:o + 16]
            if not any(blk):
                continue
            nzb += 1
            if (blk[0] >> 4) <= 4 and (blk[0] & 15) <= 12 and blk[1] <= 7:
                ok += 1
        frac = ok / nzb if nzb else 0.0
        if best is None or frac > best[0]:
            best = (frac, al, nzb)
    return best


# ---------------------------------------------------------- offset table ----

def offset_table(b):
    """Leading u32 table: word 0 (`first`) is the table length in bytes, and every word below
    it is 0, 0xFFFFFFFF or a 4-aligned offset in [first, file size].  Accepted when there are
    at least 8 offsets and twice as many offsets as other words, or (sparse tables) at least
    2 offsets and no other words.  Random data almost never yields a 4-aligned in-range word,
    so a false positive needs a structured file."""
    n = len(b)
    if n < 16:
        return None
    first = struct.unpack_from("<I", b, 0)[0]
    if first % 4 or first < 16 or first > n // 2 or first > 0x4000:
        return None
    k = first // 4
    ws = struct.unpack_from("<%dI" % k, b, 0)
    real = sent = bad = 0
    for w in ws:
        if w in (0, 0xFFFFFFFF):
            sent += 1
        elif w % 4 == 0 and first <= w <= n:
            real += 1
        else:
            bad += 1
    if not ((real >= 8 and real >= 2 * bad) or (real >= 2 and bad == 0)):
        return None
    return {"entries": k, "offset_entries": real, "sentinel_entries": sent,
            "other_entries": bad, "first": first, "max_offset": max(w for w in ws if w != 0xFFFFFFFF)}


def id_table(b):
    """u16 N, then N non-zero u16 ids, then a zero u16 (the layout of every .LSD/.LCD header)."""
    n = len(b)
    if n < 8:
        return None
    cnt = struct.unpack_from("<H", b, 0)[0]
    if not 1 <= cnt <= 1024 or 2 + 2 * cnt + 2 > n:
        return None
    ids = struct.unpack_from("<%dH" % cnt, b, 2)
    nxt = struct.unpack_from("<H", b, 2 + 2 * cnt)[0]
    if 0 in ids or nxt != 0:
        return None
    return {"count": cnt, "min_id": min(ids), "max_id": max(ids), "distinct": len(set(ids))}


# --------------------------------------------------------------- STR / XA ----

def decode_coding(ci):
    return {"channels": "stereo" if ci & 3 == 1 else ("mono" if ci & 3 == 0 else "reserved"),
            "sample_rate_hz": {0: 37800, 1: 18900}.get((ci >> 2) & 3),
            "bits_per_sample": {0: 4, 1: 8}.get((ci >> 4) & 3),
            "emphasis": bool(ci & 0x40)}


def analyze_sectors(raw, nsec):
    """Walk raw sectors of one file extent; returns stats and STR header observations."""
    st = {"sectors": nsec, "form1": 0, "form2": 0, "submode_hist": {}, "coding_hist_audio": {},
          "video_bit_0x02": 0, "audio_form2": 0, "video_hdr": 0, "form1_data": 0,
          "chunk0": 0, "mdec3800": 0, "frames": set(), "bad_sync": 0,
          "file_channels": set(), "first_video": None, "first_video_lba_index": None,
          "other_sectors": 0, "other_nonzero": 0}
    for i in range(nsec):
        s = raw[i * RAW:(i + 1) * RAW]
        if s[:12] != SYNC:
            st["bad_sync"] += 1
            continue
        fn, ch, sm, ci = s[16], s[17], s[18], s[19]
        st["submode_hist"][sm] = st["submode_hist"].get(sm, 0) + 1
        form2 = bool(sm & 0x20)
        st["form2" if form2 else "form1"] += 1
        if sm & 0x02:
            st["video_bit_0x02"] += 1
        pay = s[24:24 + (2324 if form2 else 2048)]
        if sm & 0x04 and form2:
            st["audio_form2"] += 1
            st["coding_hist_audio"][ci] = st["coding_hist_audio"].get(ci, 0) + 1
            st["file_channels"].add((fn, ch))
            continue
        if sm & 0x08 and not form2:
            st["form1_data"] += 1
            if pay[0:2] == b"\x60\x01" and pay[2:4] == b"\x01\x80":
                st["video_hdr"] += 1
                chunk, nchunks, frame, demux = struct.unpack_from("<HHII", pay, 4)
                st["frames"].add(frame)
                if chunk == 0:
                    st["chunk0"] += 1
                    w, h, words, magic, qs, ver = struct.unpack_from("<HHHHHH", pay, 16)
                    if magic == 0x3800:
                        st["mdec3800"] += 1
                    if st["first_video"] is None:
                        st["first_video"] = {
                            "sector_index_in_file": i, "subheader": "%02x%02x%02x%02x" % (fn, ch, sm, ci),
                            "header_hex": pay[:32].hex(), "u16_0_magic": "0x%04x" % 0x0160,
                            "u16_2_type": "0x%04x" % 0x8001, "chunk_no": chunk,
                            "chunks_in_frame": nchunks, "frame_no": frame, "demux_bytes": demux,
                            "width": w, "height": h, "mdec_len_words": words,
                            "mdec_magic_at_payload_off_22": "0x%04x" % magic,
                            "qscale": qs, "version": ver}
                st["file_channels"].add((fn, ch))
                continue
        st["other_sectors"] += 1
        if any(pay):
            st["other_nonzero"] += 1
    return st


# --------------------------------------------------------------- classify ----

def classify_file(trk, f, want_extract, ext_root):
    path = f["path"]
    lba, nsec, size = f["lba"], f["sectors"], f["size_bytes"]
    raw = raw_sectors(trk, lba, nsec) if nsec else b""
    st = analyze_sectors(raw, nsec)
    form2 = st["form2"]
    cands = []          # (tag, [evidence])
    details = {}
    hints = []
    ext = os.path.splitext(f["name"])[1].upper()
    if ext:
        hints.append("extension %s" % ext)
    hints.append("directory %s" % f["directory"])

    data = None
    if form2 == 0:
        data = b"".join(raw[i * RAW + 24:i * RAW + 24 + 2048] for i in range(nsec))[:size]

    # --- STR / XA audio (sector level) ---
    if st["video_hdr"]:
        frac = st["video_hdr"] / max(1, st["form1_data"])
        if frac >= 0.95 and st["mdec3800"] == st["chunk0"] and st["chunk0"] > 0:
            fv = st["first_video"]
            e = [ev("subheader", "%d/%d Form 1 data sectors carry a video chunk header (u16 0x0160, u16 0x8001 at payload offset 0)"
                    % (st["video_hdr"], st["form1_data"])),
                 ev("structure", "MDEC magic 0x3800 at payload offset 22 in %d/%d chunk-0 sectors"
                    % (st["mdec3800"], st["chunk0"])),
                 ev("structure", "%d distinct frame numbers; first frame %dx%d, %d chunks/frame, version %d"
                    % (len(st["frames"]), fv["width"], fv["height"], fv["chunks_in_frame"], fv["version"])),
                 ev("subheader", "submode video bit 0x02 set in %d sectors (video sectors use submode 0x%02x)"
                    % (st["video_bit_0x02"], int(fv["subheader"][4:6], 16)))]
            cands.append(("STR video", e))
            details["str"] = {
                "video_chunk_sectors": st["video_hdr"], "frames": len(st["frames"]),
                "max_frame_no": max(st["frames"]), "chunk0_sectors": st["chunk0"],
                "mdec_magic_ok": st["mdec3800"], "submode_video_bit_0x02_sectors": st["video_bit_0x02"],
                "first_video_sector": fv}
    if st["audio_form2"]:
        aud = st["audio_form2"]
        cih = {"0x%02x" % k: v for k, v in sorted(st["coding_hist_audio"].items())}
        dec = {k: decode_coding(int(k, 16)) for k in cih}
        e = [ev("subheader", "%d Form 2 sectors with submode audio bit 0x04 (of %d sectors); coding info histogram %s"
                % (aud, nsec, json.dumps(cih)))]
        e.append(ev("subheader", "coding info decoded: " + "; ".join(
            "%s=%s %s Hz %d-bit" % (k, d["channels"], d["sample_rate_hz"], d["bits_per_sample"])
            for k, d in dec.items())))
        tag = "XA audio"
        if st["video_hdr"]:
            tag = "XA audio"          # secondary on STR files, placed after STR by priority
            e.append(ev("subheader", "interleaved with video sectors (file/channel pairs %s)"
                        % sorted(st["file_channels"])))
        cands.append((tag, e))
        details["xa_audio"] = {"form2_audio_sectors": aud, "coding_info_histogram": cih,
                               "coding_info_decoded": dec,
                               "file_channel_pairs": [list(p) for p in sorted(st["file_channels"])],
                               "share_of_sectors": round(aud / max(1, nsec), 4)}
    details["sectors"] = {"form1": st["form1"], "form2": st["form2"],
                          "submode_histogram": {"0x%02x" % k: v for k, v in sorted(st["submode_hist"].items())},
                          "bad_sync": st["bad_sync"]}
    if st["other_sectors"] and (st["video_hdr"] or st["audio_form2"]):
        details["sectors"]["non_video_non_audio_sectors"] = st["other_sectors"]
        details["sectors"]["non_video_non_audio_nonzero_payload"] = st["other_nonzero"]

    is_stream = bool(st["video_hdr"] or st["audio_form2"])
    ext_info = None
    if data is not None:
        b = data
        # --- PS-X EXE ---
        if b[:8] == b"PS-X EXE":
            h = struct.unpack_from("<10I", b, 0x10)
            pc, gp, taddr, tsize, daddr, dsize, baddr, bsize, saddr, ssize = h
            region = b[0x4C:0x4C + 64].split(b"\0")[0].decode("ascii", "replace")
            consistent = (len(b) == 0x800 + tsize)
            cands.append(("PS-X EXE", [
                ev("magic", "'PS-X EXE' at offset 0"),
                ev("structure", "pc=0x%08x gp=0x%08x text addr=0x%08x size=%d data addr=0x%08x size=%d bss addr=0x%08x size=%d stack addr=0x%08x size=%d"
                   % (pc, gp, taddr, tsize, daddr, dsize, baddr, bsize, saddr, ssize)),
                ev("structure", "file size %d %s 0x800 header + text size %d" % (len(b), "==" if consistent else "!=", tsize)),
                ev("structure", "region string at 0x4C: %r" % region)]))
            details["exe"] = {"pc": "0x%08x" % pc, "gp": "0x%08x" % gp, "text_addr": "0x%08x" % taddr,
                              "text_size": tsize, "data_addr": "0x%08x" % daddr, "data_size": dsize,
                              "bss_addr": "0x%08x" % baddr, "bss_size": bsize,
                              "stack_addr": "0x%08x" % saddr, "stack_size": ssize,
                              "size_matches_header": consistent, "region_string": region}
        # --- magics at offset 0 and embedded ---
        emb = {}
        for m, nm in MAGICS:
            offs, i = [], b.find(m)
            while i != -1 and len(offs) < 8:
                offs.append(i)
                i = b.find(m, i + 1)
            if offs:
                emb[nm] = offs
                if offs[0] == 0:
                    cands.append((nm, [ev("magic", "'%s' at offset 0" % m.decode())]))
        if emb:
            details["magic_offsets"] = emb
        # --- TIM ---
        tims = scan_tims(b)
        if tims:
            chain_end, k = 0, 0
            while k < len(tims) and tims[k][0] == chain_end:
                chain_end = tims[k][1]
                k += 1
            pad_zero = not any(b[chain_end:]) if chain_end else False
            details["tim"] = {"count": len(tims),
                              "offsets": [t[0] for t in tims[:16]],
                              "first": dict(tims[0][2], offset=tims[0][0], end=tims[0][1], bytes=tims[0][1] - tims[0][0])}
            if tims[0][0] == 0 and (chain_end == len(b) or (pad_zero and len(b) - chain_end < 2048)):
                cands.append(("TIM image", [
                    ev("magic", "TIM magic 0x00000010 at offset 0"),
                    ev("structure", "%d chained TIM(s) cover bytes 0..%d of %d; block sizes (bnum) match w*h*2+12 for every block"
                       % (k, chain_end, len(b)))]))
            else:
                details["tim"]["note"] = "embedded; TIM blocks pass bnum==12+w*h*2, bpp/CLUT-flag and VRAM range checks"
        # --- text / filler ---
        tb = b[:-1] if b[-1:] == b"" else b      # DOS end-of-file marker
        if len(tb) > 0 and all(c in (9, 10, 13) or 32 <= c < 127 for c in tb):
            cands.append(("text", [ev("content", "all %d bytes are printable ASCII/CR/LF/TAB%s"
                                      % (len(tb), " plus a final 0x1A" if tb is not b else ""))]))
        if len(b) > 64:
            found = False
            for plen in range(1, 33):
                pat = b[:plen]
                # the pattern may restart at every block boundary (block 0 = no restart)
                for blk in (0, 2048, 4096, 8192, 16384, 32768, 65536):
                    if blk == 0:
                        ref = (pat * (len(b) // plen + 1))[:len(b)]
                    else:
                        unit = (pat * (blk // plen + 1))[:blk]
                        ref = (unit * (len(b) // blk + 1))[:len(b)]
                    if b == ref:
                        cands.append(("filler", [ev("content", "whole file is the %d-byte string %r repeated%s" % (
                            plen, pat, " (restarting every %d bytes)" % blk if blk else ""))]))
                        details["filler"] = {"pattern": pat.decode("latin-1"), "period": plen, "restart_block": blk}
                        found = True
                        break
                if found:
                    break
        # --- custom magics (offset 0 only) ---
        for m, desc in CUSTOM_MAGICS:
            if b[:4] == m:
                cands.append(("magic container", [ev("magic", "first 4 bytes are %s; format not identified by this project yet" % desc)]))
                details["custom_magic"] = m.hex()
        # --- offset table ---
        ot = offset_table(b)
        if ot:
            cands.append(("offset-table container", [ev(
                "structure", "leading u32 table of %d entries (first entry 0x%x = table length): %d 4-aligned offsets in [0x%x, file size], %d 0/0xFFFFFFFF sentinels, %d other"
                % (ot["entries"], ot["first"], ot["offset_entries"], ot["first"], ot["sentinel_entries"], ot["other_entries"]))]))
            details["offset_table"] = ot
        it = id_table(b)
        if it:
            cands.append(("u16-id-table container", [ev(
                "structure", "u16 count %d, then %d non-zero u16 ids (min %d, max %d), then a zero u16"
                % (it["count"], it["count"], it["min_id"], it["max_id"]))]))
            details["id_table"] = it
        # --- MIPS / ADPCM (skip pure filler/text) ---
        if not any(t in ("filler", "text") for t, _ in cands):
            ms = mips_score(b)
            ptr = leading_pointer_run(b)
            details["mips"] = ms
            if ptr:
                details["mips"]["leading_pointer_words"] = {"count": len(ptr), "min": "0x%08x" % min(ptr), "max": "0x%08x" % max(ptr)}
            if (ms["score"] >= THRESH_MIPS_SCORE and ms["prologues"] >= 1 and ms["jr_ra"] >= 1
                    and ms["nonzero_words"] >= THRESH_MIPS_MIN_NONZERO and b[:8] != b"PS-X EXE"):
                e = [ev("heuristic", "%.1f%% of %d non-zero words are well-formed R3000 instructions (threshold %.0f%%)"
                        % (ms["score"] * 100, ms["nonzero_words"], THRESH_MIPS_SCORE * 100)),
                     ev("heuristic", "%d 'addiu sp,sp,-N' prologues, %d 'jr ra', %d jal into RAM, %d lui"
                        % (ms["prologues"], ms["jr_ra"], ms["jal"], ms["lui"]))]
                if ptr:
                    e.append(ev("structure", "starts with %d u32 words in 0x%08x..0x%08x (RAM-address table) before code"
                                % (len(ptr), min(ptr), max(ptr))))
                else:
                    e.append(ev("structure", "starts directly with instruction words (no leading RAM-address table)"))
                cands.append(("overlay candidate", e))
            fr, al, nzb = adpcm_stats(b)
            details["spu_adpcm"] = {"valid_fraction": round(fr, 4), "nonzero_blocks": nzb, "alignment": al}
            if nzb >= ADPCM_MIN_BLOCKS and fr >= ADPCM_MIN_FRACTION:
                cands.append(("SPU-ADPCM (headerless)", [ev(
                    "heuristic", "%.2f%% of %d non-zero 16-byte blocks have predict<=4, shift<=12, flags<=7 (byte alignment %d); random data scores about 0.8%%"
                    % (fr * 100, nzb, al))]))
    else:
        pass     # Form 2 sectors present: only streams are expected here
    if data is None and not is_stream:
        cands.append(("unknown", [ev("subheader", "Form 2 sectors present but no STR/XA stream recognized")]))

    # primary / secondary
    names = []
    for t, _ in sorted(cands, key=lambda c: PRIORITY.index(c[0])):
        if t not in names:
            names.append(t)
    if not names:
        names = ["unknown"]
    primary = names[0]
    if want_extract:
        if primary == "STR video" or data is None:
            ext_info = extract_raw(f, raw, ext_root)
        else:
            ext_info = extract_form1(f, data, ext_root)
    evid = []
    for t, es in sorted(cands, key=lambda c: PRIORITY.index(c[0])):
        for e_ in es:
            evid.append(dict(e_, tag=t))
    if primary == "unknown" and not cands:
        evid.append({"tag": "unknown", "kind": "content",
                     "text": "no magic, STR/XA, TIM, MIPS-code, SPU-ADPCM, offset-table or text/filler rule matched"})
    rec = {"path": path, "lba": lba, "size_bytes": size, "sectors": nsec,
           "tag": primary, "secondary_tags": names[1:], "evidence": evid,
           "hints_not_evidence": hints, "details": details}
    if primary == "unknown" and data is not None:
        rec["unknown_info"] = {"first16_hex": data[:16].hex(), "size_bytes": size,
                               "entropy_bits_per_byte": round(entropy(data), 3)}
    if ext_info:
        rec["extracted"] = ext_info
    return rec, data


# ------------------------------------------------------------- extraction ----

def safe_target(ext_root, rel):
    parts = [p for p in rel.split("/") if p]
    if not parts or any(p in (".", "..") or ":" in p or "\\" in p for p in parts):
        raise DiscError("unsafe disc path for extraction: %r" % rel)
    t = os.path.join(ext_root, *parts)
    if os.path.commonpath([os.path.abspath(t), ext_root]) != ext_root:
        raise DiscError("extraction path escapes work/extracted: %r" % rel)
    return t


def write_if_changed(target, blob):
    h = hashlib.sha256(blob).hexdigest()
    if os.path.isfile(target) and os.path.getsize(target) == len(blob):
        with open(target, "rb") as fh:
            if hashlib.sha256(fh.read()).hexdigest() == h:
                return h
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as fh:
        fh.write(blob)
    return h


def extract_form1(f, data, ext_root):
    target = safe_target(ext_root, f["path"])
    h = write_if_changed(target, data)
    return {"path": "work/extracted" + f["path"], "kind": "form1_user_data", "bytes": len(data), "sha256": h}


def extract_raw(f, raw, ext_root):
    target = safe_target(ext_root, f["path"] + ".raw2352")
    h = write_if_changed(target, raw)
    return {"path": "work/extracted" + f["path"] + ".raw2352", "kind": "raw_sectors_2352",
            "bytes": len(raw), "sha256": h}


# ------------------------------------------------------------------- main ----

def open_track(cue):
    files = parse_cue(cue)
    cdir = os.path.dirname(cue)
    for fl in files:
        p = os.path.join(cdir, fl["name"])
        for t in fl["tracks"]:
            if t["mode"] != "AUDIO":
                fsz = os.path.getsize(p)
                sz = MODES[t["mode"]][0]
                return Track(p, t["mode"], t["indexes"][1], fsz // sz - t["indexes"][1]), fl["name"]
    raise DiscError("no data track in cue")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", default=os.path.join(root, "work", "disc_files.json"))
    ap.add_argument("--out", default=os.path.join(root, "work", "disc_classes.json"))
    ap.add_argument("--extract-dir", default=os.path.join(root, "work", "extracted"))
    ap.add_argument("--cue")
    ap.add_argument("--no-extract", action="store_true")
    a = ap.parse_args()
    try:
        with open(a.files, "r", encoding="utf-8") as fh:
            listing = json.load(fh)
        cue = a.cue
        if not cue:
            d = os.path.join(root, "ps1_game")
            cues = sorted(x for x in os.listdir(d) if x.lower().endswith(".cue"))
            if len(cues) != 1:
                raise DiscError("expected exactly one .cue in %s" % d)
            cue = os.path.join(d, cues[0])
        cue = os.path.abspath(cue)
        if os.path.basename(cue) != listing["cue"]:
            raise DiscError("cue %s does not match %s (%s)" % (os.path.basename(cue), a.files, listing["cue"]))
        ext_root = os.path.abspath(a.extract_dir)
        trk, _ = open_track(cue)
        recs, exe_text, str_samples = [], None, []
        try:
            for f in sorted(listing["files"], key=lambda x: x["path"]):
                rec, data = classify_file(trk, f, not a.no_extract, ext_root)
                recs.append(rec)
                if rec["tag"] == "PS-X EXE" and f["path"] == "/SLUS_004.76":
                    h = rec["details"]["exe"]
                    exe_text = data[0x800:0x800 + h["text_size"]]
                if rec["tag"] == "STR video" and len(str_samples) < 1:
                    n = min(f["sectors"], 400)
                    raw = raw_sectors(trk, f["lba"], n)
                    pay = b"".join(raw[i * RAW + 24:i * RAW + 24 + 2048] for i in range(n)
                                   if raw[i * RAW + 18] & 0x08 and not raw[i * RAW + 18] & 0x20)
                    str_samples.append(("first_%d_data_sectors_of_%s" % (n, f["path"]), pay))
        finally:
            trk.close()
    except (DiscError, OSError, ValueError, KeyError) as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2

    cal = calibrate(exe_text, str_samples)
    non_code = [(r["details"]["mips"]["score"], r["path"]) for r in recs
                if "mips" in r["details"] and r["tag"] != "overlay candidate" and r["tag"] != "PS-X EXE"]
    non_code.sort(reverse=True)
    ov = sorted((r["details"]["mips"]["score"], r["path"]) for r in recs if r["tag"] == "overlay candidate")
    cal["non_code_files_max_score"] = {"score": non_code[0][0], "path": non_code[0][1]} if non_code else None
    nc_loose = sorted(((r["details"]["mips"]["score"], r["path"]) for r in recs
                       if "mips" in r["details"] and r["tag"] not in ("overlay candidate", "PS-X EXE")
                       and r["details"]["mips"]["prologues"] and r["details"]["mips"]["jr_ra"]), reverse=True)
    cal["non_code_with_prologue_and_jr_ra_max_score"] = (
        {"score": nc_loose[0][0], "path": nc_loose[0][1]} if nc_loose else None)
    cal["overlay_candidates_min_score"] = {"score": ov[0][0], "path": ov[0][1]} if ov else None
    cal["rule"] = ("overlay candidate = score >= %.2f AND >=1 prologue AND >=1 jr ra AND >= %d non-zero words"
                   % (THRESH_MIPS_SCORE, THRESH_MIPS_MIN_NONZERO))
    cal["note"] = ("score = fraction of non-zero 32-bit LE words that are well-formed R3000 instructions "
                   "(loads/stores need a non-zero base register, j/jal targets must lie in 2 MiB RAM). "
                   "The score alone also passes the 2048-byte *DEMO.BIN files; the prologue and jr ra requirement rejects them.")

    tags = {}
    for r in recs:
        t = tags.setdefault(r["tag"], {"files": 0, "bytes": 0})
        t["files"] += 1
        t["bytes"] += r["size_bytes"]
    sec = {}
    for r in recs:
        for t in r["secondary_tags"]:
            sec[t] = sec.get(t, 0) + 1
    unknown = [r for r in recs if r["tag"] == "unknown"]
    extracted = [r["extracted"] for r in recs if "extracted" in r]
    out = {"source": os.path.basename(a.files), "cue": listing["cue"],
           "file_count": len(recs),
           "tag_totals": {k: tags[k] for k in sorted(tags)},
           "secondary_tag_counts": {k: sec[k] for k in sorted(sec)},
           "unknown_count": len(unknown),
           "unknown_files": [dict(path=r["path"], **r["unknown_info"]) for r in unknown if "unknown_info" in r],
           "mips_calibration": cal,
           "extraction": {"root": "work/extracted", "enabled": not a.no_extract,
                          "files_written": len(extracted),
                          "bytes": sum(e["bytes"] for e in extracted),
                          "kinds": {"form1_user_data": "raw 2048-byte user data per sector, cut to ISO size",
                                    "raw_sectors_2352": "full 2352-byte raw sectors (STR files, .raw2352 suffix)"}},
           "files": recs}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("%-26s %6s %14s" % ("tag", "files", "bytes"))
    for k in PRIORITY:
        if k in tags:
            print("%-26s %6d %14d" % (k, tags[k]["files"], tags[k]["bytes"]))
    print("%-26s %6d %14d" % ("TOTAL", len(recs), sum(r["size_bytes"] for r in recs)))
    print("secondary tags: %s" % json.dumps(out["secondary_tag_counts"], sort_keys=True))
    print("unknown: %d" % len(unknown))
    for r in unknown:
        ui = r.get("unknown_info", {})
        print("  %-36s %9d bytes  entropy %.2f  first16 %s" % (
            r["path"], r["size_bytes"], ui.get("entropy_bits_per_byte", -1), ui.get("first16_hex", "")))
    print("MIPS calibration: exe_text=%.3f random=%.3f str_payload=%s non_code_max=%s overlay_min=%s"
          % (cal["exe_text_section"]["score"], cal["random_bytes_seed1_200000"]["score"],
             [v["score"] for k, v in cal.items() if k.startswith("first_")],
             cal["non_code_files_max_score"], cal["overlay_candidates_min_score"]))
    if not a.no_extract:
        print("extracted: %d files, %d bytes under work/extracted" % (len(extracted), out["extraction"]["bytes"]))
    print("wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
