#!/usr/bin/env python3
"""Write aot/overlays.json (T2.15) from work/overlay_facts.json and the disc.

Inputs (read only): work/overlay_facts.json (tools/overlay_facts.py),
work/disc/SLUS_004.76 (boot EXE), ps1_game/*.cue (through tools/disc_identify.py),
game.toml ([prepare_disc] digests, [game] id).
Output: aot/overlays.json. It holds addresses, sizes and hashes only (D8).
Every hash is recomputed from the disc here and compared with the facts file;
a mismatch stops the script. Deterministic: no timestamps, sorted keys.

Usage: python tools/make_overlay_profile.py
"""
import hashlib
import json
import os
import struct
import sys
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import disc_identify as di  # noqa: E402

BASE = 0x80130FF8
EXE_BASE = 0x80010000
LOC_BASE, SIZE_BASE, DEST_PTR = 0x80012F28, 0x80013264, 0x80015134
OVR = ["BRIDGE", "EARTH", "FIRE", "FORTRESS", "PRISON", "TEMPLE", "WATER", "WIND"]
# Disc names are the pipeline's (no leading slash). Jal targets from the EXE level functions that load each overlay id
# (overlay_facts.json "levels"/"fire_sites", jal_into_window).
H = lambda v: "0x%08X" % v


def p(*a):
    return os.path.join(ROOT, *a)


def main():
    facts = json.load(open(p("work", "overlay_facts.json"), encoding="utf-8"))
    cfg = tomllib.load(open(p("game.toml"), "rb"))
    prep = cfg["prepare_disc"]
    exe = open(p("work", "disc", "SLUS_004.76"), "rb").read()

    d = p("ps1_game")
    cue = sorted(x for x in os.listdir(d) if x.lower().endswith(".cue"))[0]
    fl = di.parse_cue(os.path.join(d, cue))
    t = fl[0]["tracks"][0]
    rd = di.Track1Reader(os.path.join(d, fl[0]["name"]), t["mode"], t["indexes"][1])

    ids = {i["id"]: i for i in facts["tables"]["ids"]}
    ovr = {o["name"]: o for o in facts["ovr_files"]}

    def exe_word(addr):
        off = 0x800 + addr - EXE_BASE
        return struct.unpack_from("<I", exe, off)[0]

    # Entry targets: every jal from a level function into the window, by overlay id.
    entry = {}
    for lv in facts["levels"]:
        for j in lv.get("jal_into_window", []):
            for oid in lv["overlay_ids_read"]:
                if oid in (135, 136, 137, 138, 139, 140, 141, 142):
                    entry.setdefault(oid, set()).add(int(j["target"], 16))

    images = []
    for name in OVR:
        o = ovr[name + ".OVR"]
        i = ids[o["id"]]
        assert i["path"] == o["path"] and i["disc_size"] == o["size"]
        data = rd.read_extent(i["disc_lba"], i["disc_size"])
        sha = hashlib.sha256(data).hexdigest()
        assert sha == o["sha256"] == i["sha256"], name
        item = dict(file=o["path"].lstrip("/"), file_offset="0x0", base="0x0", address="0x0",
                    size=len(data), sha256=sha, load_addr=H(BASE))
        words = o["address_table_words"]
        if words:
            end = BASE + 4 * words
            item["excluded_ranges"] = [dict(
                start=H(BASE), end=H(end),
                sha256=hashlib.sha256(data[:4 * words]).hexdigest(),
                reason="Leading %d-word address table: data words (RAM addresses "
                       "0x8013xxxx), not code. tools/overlay_facts.py (T2.12)." % words)]
            # entries must stay outside the table (verified below)
        tg = sorted(entry.get(o["id"], []))
        for e in tg:
            assert BASE <= e < BASE + len(data) and e % 4 == 0, (name, hex(e))
            assert e >= BASE + 4 * words, (name, hex(e), "inside excluded table")
        if tg:
            item["entries"] = [H(e) for e in tg]
        images.append(dict(method="fixed_address_extents", allow_missing=True, extents=[item]))

    check_words = []
    check_words.append(dict(
        method="words", file="SLUS_004.76", file_offset="0x800", base=H(EXE_BASE),
        values={H(DEST_PTR): H(exe_word(DEST_PTR))}))
    assert exe_word(DEST_PTR) == BASE
    loc, size = {}, {}
    for oid in range(134, 144):
        a = LOC_BASE + 4 * oid
        b = SIZE_BASE + 4 * oid
        assert H(a) == "0x%08X" % int(ids[oid]["loc_entry_addr"], 16)
        assert H(b) == "0x%08X" % int(ids[oid]["size_entry_addr"], 16)
        loc[H(a)] = H(exe_word(a))
        size[H(b)] = H(exe_word(b))
        assert exe_word(b) == ids[oid]["disc_size"]
    for tbl in (loc, size):
        check_words.append(dict(method="words", file="SLUS_004.76", file_offset="0x800",
                                base=H(EXE_BASE), values=tbl))
    # Adjacency: only a pair whose first file is a whole number of sectors passes
    # the pipeline's check (see report); BRDGDEMO.BIN (2048 bytes) -> BRIDGE.OVR.
    adj = dict(method="adjacent_files", files=["OVERLAYS/BRDGDEMO.BIN", "OVERLAYS/BRIDGE.OVR"])

    profile = dict(
        schema="psxrecomp AOT methods v1",
        game_id=cfg["game"]["id"],
        disc_hashes=dict(md5=prep["known_md5"][0], sha1=prep["known_sha1"][0]),
        generic_exclude_files=[dict(
            files=["OVERLAYS/BRDGDEMO.BIN", "OVERLAYS/WINDDEMO.BIN"],
            reason="Data files (2048 bytes each, ids 134 and 143), not code; the profile "
                   "owns the eight .OVR images (docs/EXE_OVERLAYS.md).")],
        checks=check_words + [adj],
        images=images,
        expected_records=8,
        strict_bounds=True,
        static_output="generated/overlays_static.c",
    )
    os.makedirs(p("aot"), exist_ok=True)
    with open(p("aot", "overlays.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(profile, f, indent=2, sort_keys=False)
        f.write("\n")
    print("wrote aot/overlays.json: %d images, %d checks" % (len(images), len(profile["checks"])))


if __name__ == "__main__":
    main()
