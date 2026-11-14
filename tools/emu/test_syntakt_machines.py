#!/usr/bin/env python3
"""Preuve des tweaks « vrais moteurs du Syntakt en machines ajoutées » : syntakt-vintage (notes/19, SD VINTAGE
et CP VINTAGE en 7e et 8e machines « SDVtg » (6) et « CPVtg » (7)) et ceux de tools/gen_syntakt_engines.py
(notes/20, n'importe quel choix de moteurs du catalogue, machines 6, 7, 8…).

Mêmes vérifications que test_sdvintage_7th.py (notes/18), sur le VRAI code de l'OS, étendues à 8 machines :
démarrage (bootstrap, crochet, constructeur des tables), recherches, accesseurs, état par descripteur,
écran MACHINES (8 noms, 8 repères dans l'écran), réglage de la machine, molette, enregistrements par machine,
changement de machine réel (défauts écrits), potards de l'écran principal, icônes, et le son : SDVtg et CPVtg
identiques au Syntakt, SNARE identique à l'OS stock.

    python3 tools/emu/test_syntakt_machines.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx [--tweak …json]
"""
import argparse
import bisect
import json
import pathlib
import re
import struct
import subprocess
import sys
import tempfile

import numpy as np
from unicorn import UC_HOOK_CODE, UcError
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_sdvintage_7th as g7      # noqa: E402
import gen_syntakt_engines as gs   # noqa: E402
import gen_syntakt_machines as g8   # noqa: E402
import mcengine as E                # noqa: E402
import stengine as S                # noqa: E402
import syntakt                      # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
from test_sdvintage_7th import UI, check, dis, fill_records, fake_track, refcount, SCRATCH, REC_BASE, REC_LEN  # noqa: E402

TWEAK = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "23-syntakt-vintage.json"
BASE = 0x40000400
# Machines ajoutées et disposition de la charge utile, fixées par configure() d'après le tweak testé.
ADDED, FIRST, NAMES, REC, ROWS, CCROWS = [], {}, [], {}, 0, 0
NM = TOP = N = 0                                    # nombre de machines, plus grand index, machines ajoutées
SAFE = False                                        # machines hors limites protégées (gen_syntakt_engines.py)


def configure(tweak):
    global ADDED, FIRST, NAMES, REC, ROWS, CCROWS, NM, TOP, N, SAFE
    SAFE = tweak["id"] != "syntakt-vintage"
    if tweak["id"] == "syntakt-vintage":            # disposition de gen_syntakt_machines.py
        codes, recs, ROWS, CCROWS = ["sd", "cp"], [g8.REC8, g8.REC9], g8.ROWS8, g8.CCROWS8
    else:
        codes = [c for c in tweak["id"].split("-")[1:]]
        recs, ROWS, CCROWS = [gs.RECS + 0x60 * i for i in range(len(codes))], gs.ROWSN, gs.CCROWSN
    ADDED = [dict(gs.CATALOG[c], code=c, index=6 + i) for i, c in enumerate(codes)]
    N, NM, TOP = len(ADDED), 6 + len(ADDED), 5 + len(ADDED)
    FIRST = {6 + i: 76 + 5 * i for i in range(N)}
    REC = {6 + i: r for i, r in enumerate(recs)}
    NAMES = ["Kick", "Snare", "Metal", "Perc", "Tone", "Chord"] + [m["name"] for m in ADDED]


def snare_map(x, m):
    """Descripteur de SNARE (51..55) -> celui de la machine ajoutée m ; autres inchangés."""
    return FIRST[m] + x - 51 if 51 <= x <= 55 else x


# --- 1. tables construites au démarrage ------------------------------------------------------------------
def tables(stock, patched, payload):
    a, b = UI(stock), UI(patched, payload)
    a.call(0x4005a274)
    b.call(0x4005a274)
    check(not a.bad and not b.bad, "constructeur des tables (0x4005a274) exécuté sans accès hors mémoire")
    lo, hi = t7.BSS_TABLES
    sa = bytes(a.uc.mem_read(lo, hi - lo))
    sb = bytearray(b.uc.mem_read(lo, hi - lo))
    rows_a, cc_a = sa[g7.ROWS - lo:][:6 * 32], sa[g7.CCROWS - lo:][:6 * 32]
    rows_b, cc_b = bytes(b.uc.mem_read(ROWS, NM * 32)), bytes(b.uc.mem_read(CCROWS, NM * 32))
    sb[g7.ROWS - lo:g7.ROWS - lo + 6 * 32] = rows_a
    sb[g7.CCROWS - lo:g7.CCROWS - lo + 6 * 32] = cc_a
    nrows = (a.u32(t7.ROW_COUNT), b.u32(t7.ROW_COUNT))
    sb[t7.ROW_COUNT - lo:t7.ROW_COUNT - lo + 4] = sa[t7.ROW_COUNT - lo:][:4]
    check(nrows == (6, NM), f"rangées de machines construites : stock {nrows[0]}, modifié {nrows[1]}")
    check(bytes(sb) == sa, "toutes les autres tables du BSS identiques au stock")
    check(rows_b[:6 * 32] == rows_a and cc_b[:6 * 32] == cc_a, "rangées des machines 0..5 identiques au stock")
    r1, c1 = struct.unpack(">8I", rows_a[32:64]), struct.unpack(">8I", cc_a[32:64])
    ok = True
    for m in FIRST:
        r, c = struct.unpack(">8I", rows_b[32 * m:32 * m + 32]), struct.unpack(">8I", cc_b[32 * m:32 * m + 32])
        ok &= r == tuple(snare_map(x, m) for x in r1) and c == tuple(snare_map(x, m) if 51 <= x <= 54 else x for x in c1)
        print(f"        rangée {m} ({NAMES[m]}) : slots {r[:6]}, CC 16..19 {c[:4]}")
    check(ok, f"rangées {list(FIRST)} ({', '.join(NAMES[6:])}) = celles de SNARE avec leurs propres descripteurs")
    return a, b


# --- 2. recherches -----------------------------------------------------------------------------------------
def lookups(a, b):
    diff = []
    for m in range(NM):
        for slot in range(34):
            x, y = a.call(0x4005a692, slot, m), b.call(0x4005a692, slot, m)
            if x != y:
                diff.append((m, slot, y))
    want = {(m, s, FIRST[m] + s - 0xb) for m in FIRST for s in (0xb, 0xc, 0xd, 0xe)} | \
           {(m, 0x12, FIRST[m] + 4) for m in FIRST}
    check(set(diff) == want, f"(slot, machine) -> descripteur : identique sauf machines {list(FIRST)} ({len(diff)} écarts, les leurs)")
    last = 76 + 5 * N
    spec = [(i, a.call(0x4005a556, i), b.call(0x4005a556, i)) for i in range(last + 9)]
    bad = [i for i, x, y in spec if (x != y) != (76 <= i < last and (i - 76) % 5 != 4)]
    check(not bad, f"« descripteur propre à une machine » : identique, plus les 4 potards de chaque machine ajoutée")
    dm = [(a.call(0x4005a50a, i), b.call(0x4005a50a, i)) for i in range(last + 9)]
    ok = all(x == y for x, y in dm[:76]) and [y for x, y in dm[76:last]] == [v for i in range(N) for v in [6 + i] * 4 + [7]] and all(y == dm[0][0] for x, y in dm[last:])
    check(ok, f"machine d'un descripteur (0x4005a50a, test d'applicabilité) : 0..75 identiques, 76..{last - 1} -> {[y for x, y in dm[76:last]]}")
    diff = set()
    for t in range(8):
        for m in range(NM):
            for cc in range(128):
                x, y = a.call(0x4005a8ce, t, m, cc), b.call(0x4005a8ce, t, m, cc)
                if x != y:
                    diff.add((t <= 5, m, cc, y))
    want = {(True, m, cc, FIRST[m] + cc - 16) for m in FIRST for cc in (16, 17, 18, 19)}
    check(diff == want, f"CC reçu -> descripteur : identique sauf pistes 0..5 en machines {list(FIRST)}, CC 16..19 ({len(diff)} écarts)")


# --- 3. accesseurs et état par descripteur -----------------------------------------------------------------
def accessors(a, b, stock, patched):
    last = 76 + 5 * N
    ok = all(dis(stock, va).startswith(("moveq #76,", "moveq #75,")) and
             dis(patched, va) == dis(stock, va).replace("#76,", f"#{last},").replace("#75,", f"#{last - 1},")
             for va in g7.BOUNDS if va not in {j[0] for j in g8.JUMPS8})
    ok &= all(dis(patched, va, 6).startswith("jmp 0x4303") for va, _, _ in g7.JUMPS + g8.JUMPS8)
    check(ok, f"bornes 76/75 -> {last}/{last - 1}, détours = jmp vers la charge utile")
    ok, rows = True, []
    for m in ADDED:
        base = FIRST[m["index"]]
        for i, (long_, short, default, *rng) in enumerate(m["knobs"]):
            lo, hi = rng or (0, 127)
            idx = base + i
            ok &= b.call(0x4005a4e8, idx) == 0xb + i
            name = bytes(b.uc.mem_read(b.call(0x4000b22a, 0, idx), 16)).split(b"\0")[0].decode()
            short_ = bytes(b.uc.mem_read(b.call(0x4000b208, 0, idx), 8)).split(b"\0")[0].decode()
            ok &= (name, short_) == (long_, short)
            b.call(0x4005a65a, idx)
            ok &= struct.unpack(">3i", b.uc.mem_read(SCRATCH, 12)) == (lo << 8, hi << 8, default << 8)
            rows.append(name)
        b.call(0x4005a65a, base + 4)
        ok &= struct.unpack(">3i", b.uc.mem_read(SCRATCH, 12))[2] == m["decay"] << 8
    b.call(0x4005a65a, g7.ALG_DESC)
    ok &= struct.unpack(">3i", b.uc.mem_read(SCRATCH, 12))[1] == TOP << 8
    check(ok, f"descripteurs 76..{last - 1} : slots, noms {rows}, plages, défauts ; « Algorithm » va jusqu'à {TOP}")
    st = [(a.call(0x4004df40, i), b.call(0x4004df40, i)) for i in range(last + 9)]
    ok = all(y == x for x, y in st[:76]) and all(st[i][1] == st[51 + (i - 76) % 5][0] for i in range(76, last)) \
        and all(y == st[0][0] for x, y in st[last:])
    check(ok, f"état par descripteur : 0..75 inchangés ; 76..{last - 1} -> objets de SNARE 51..55")


# --- 4. écran MACHINES, réglage de la machine, molette -----------------------------------------------------
def screens(stock, patched, payload):
    ok = True
    for m in range(NM):
        ts, is_, ms, _ = t7.drum_select(stock, b"", m)
        tp, ip, mp, bp = t7.drum_select(patched, payload, m)
        shown = {x["index"]: x["image"] for x in ADDED}.get(m, m)
        full = ["repère"] * NM
        full[m] = "repère plein"
        want = [0x92000000 + 28 * shown, 0x92100000 + 28 * shown]
        pics = {x["index"]: x.get("pics") for x in ADDED}.get(m)
        if pics:                            # ses propres images (notes/71 §13) : la carte, l'icône
            want = [pics[0] or want[0], pics[1] or want[1]]
        ok &= not bp and tp == [NAMES[m]] and ip == want and mp == full
        if m < 6:
            ok &= ts == tp and is_ == ip
        else:
            ok &= ts == ["Error"] and is_ == []
        img_ = "ses propres images" if pics else f"image de la machine {shown}"
        print(f"        machine {m} : stock {ts} | modifié {tp}, {img_}, repère plein {mp.index('repère plein') + 1}/{len(mp)}")
    # position des repères : dans l'écran (128 px)
    u = UI(patched, payload)
    xs = []
    u.hooks = {0x40071a04: "texte", 0x40071da4: "image", 0x40070c4e: "repère", 0x40070efc: "repère plein",
               0x93000000: "a5", 0x93000010: "a4"}
    for a_ in (0x93000000, 0x93000010):
        u.uc.mem_write(a_, b"\x4e\x75")
    u.uc.mem_write(0x40fe32cc, struct.pack(">I", 0x92000000))
    u.uc.mem_write(0x40fe384c, struct.pack(">I", 0x92100000))
    u.uc.mem_write(0x91001000 + 108, struct.pack(">I", 0x91002000))
    sp = t7.STACK - 0x800
    u.uc.mem_write(sp, struct.pack(">I", t7.STOP) * 64)
    for r, v in {mk.UC_M68K_REG_D3: TOP, mk.UC_M68K_REG_D2: 0x91000000, mk.UC_M68K_REG_A2: 0x91001000,
                 mk.UC_M68K_REG_A5: 0x93000000, mk.UC_M68K_REG_A4: 0x93000010, mk.UC_M68K_REG_A7: sp}.items():
        u.uc.reg_write(r, v)
    u.uc.emu_start(0x400a25e0, t7.STOP, count=1_000_000)
    xs = [(args[1], args[3]) for k, args in u.calls if k.startswith("repère")]
    ys = [args[2] for k, args in u.calls if k.startswith("repère")]
    ok &= len(xs) == NM and max(x2 for _, x2 in xs) <= 127
    # au-delà de 7 machines, 2 lignes dans la moitié droite (gs.marks_asm) : rien sur l'image et le nom, à gauche
    rows = sorted(set(ys))
    if NM > gs.MARKS_ROW:
        ok &= min(x for x, _ in xs) >= 64 and rows == sorted(gs.MARKS["y"]) and ys[:gs.MARKS_ROW] == [gs.MARKS["y"][0]] * gs.MARKS_ROW
    imgs = ", ".join(f"{m['name']} -> " + ("its own" if m.get("pics") else NAMES[m['image']].upper()) for m in ADDED)
    check(ok, f"écran MACHINES : {NM} noms, images ({imgs}), {NM} repères de x = {min(x for x, _ in xs)} à "
              f"{max(x2 for _, x2 in xs)}, sur {len(rows)} ligne(s) (les 7 premiers à y = {ys[0]}, en haut ; y monte)")


def setter_and_wheel(stock, patched, payload):
    got = {}
    for name, img, pl in (("stock", stock, b""), ("modifié", patched, payload)):
        for m in range(NM + 1):
            u = UI(img, pl)
            obj, snd = fake_track(u, 1)
            u.call(0x4001477e, obj, m, 0, 0)
            got[name, m] = struct.unpack(">H", u.uc.mem_read(snd + 38, 2))[0] >> 8
    ok = all(got["stock", m] == got["modifié", m] for m in range(6))
    added = list(range(6, NM + 1))
    ok &= [got["stock", m] for m in added] == [1] * len(added) and [got["modifié", m] for m in added] == added[:-1] + [1]
    check(ok, f"réglage de la machine (0x4001477e) : {added[:-1]} acceptés, {NM} refusé ; stock refuse {added[:-1]}")
    seq = {}
    for name, img, pl in (("stock", stock, b""), ("modifié", patched, payload)):
        u = UI(img, pl)
        obj, snd = fake_track(u, 0)
        out = []
        for step in [1] * (NM + 1) + [-1] * 3:
            u.call(0x4001488a, obj, step, 0, 0)
            out.append(struct.unpack(">H", u.uc.mem_read(snd + 38, 2))[0] >> 8)
        seq[name] = out
    walk = lambda top: [min(k, top) for k in range(1, NM + 2)] + [top - 1, top - 2, top - 3]
    check(seq["stock"] == walk(5) and seq["modifié"] == walk(TOP),
          f"molette (0x4001488a) : stock {seq['stock']}, modifié {seq['modifié']}")


# --- 5. enregistrements par machine, changement de machine réel, potards ----------------------------------
def records_and_change(stock, patched, payload):
    a, b = UI(stock), UI(patched, payload)
    for u in (a, b):
        fill_records(u)
    ok = all(a.call(0x4004df5c, i) == b.call(0x4004df5c, i) for i in range(7))
    ok &= all(a.call(0x4004df76, m) == b.call(0x4004df76, m) for m in range(6))
    if not SAFE:                                   # tweak d'origine : hors limites comme l'OS (avant le tableau)
        ok &= all(a.call(0x4004df5c, i) == b.call(0x4004df5c, i) for i in (NM + 1, 100))
        ok &= all(a.call(0x4004df76, m) == b.call(0x4004df76, m) for m in (NM, 100))
    rc = refcount(b)
    got = {}
    for m, rec in REC.items():
        r1, r2 = b.call(0x4004df5c, m + 1), b.call(0x4004df76, m)
        ids = struct.unpack(">17i", bytes(b.uc.mem_read(r1, REC_LEN))[8:])
        ok &= r1 == r2 == rec and ids[:6] == (42, FIRST[m] + 4, FIRST[m], FIRST[m] + 1, FIRST[m] + 2, FIRST[m] + 3)
        got[m] = ids[:6]
    ok &= refcount(b) == rc + 2 * N
    recs = ", ".join(f"{m + 1} -> {NAMES[m]} {got[m]}" for m in REC)
    check(ok, f"enregistrements par machine : 0..6 identiques ; {recs} ; chaînes +{2 * N} références")
    res = {}
    for m_from, m_to in ((m - 1, m) for m in FIRST):
        u = UI(patched, payload)
        fill_records(u)
        obj, snd = fake_track(u, m_from)
        del u.hooks[0x40014072]
        this = 0x93900000
        for k in range(6):
            u.uc.mem_write(this + 70 + 4 * k, struct.pack(">i", -1))
        for a_, v in {0x400cf866: 0x93a00000, 0x4000eb90: 0x93a00000, 0x40012412: 0, 0x400cf9a8: 0x93a00000,
                      0x4006bdfe: 0, 0x4000eb9c: 0x93a00000, 0x40009c1a: obj, 0x400f44c6: 0, 0x4001416c: 0}.items():
            u.hooks[a_] = (f"{a_:#x}", v)
        u.call(0x400a2712, this, 1, 0, 0)
        mach = struct.unpack(">H", u.uc.mem_read(snd + 38, 2))[0] >> 8
        vals = [struct.unpack(">h", u.uc.mem_read(snd + 0x14 + 2 * sl, 2))[0] >> 8 for sl in (0xb, 0xc, 0xd, 0xe, 0x12)]
        res[m_to] = (mach, vals, bool(u.bad))
    want = {m["index"]: (m["index"], [k[2] for k in m["knobs"]] + [m["decay"]], False) for m in ADDED}
    chain = ", ".join(f"{NAMES[m - 1]} -> {NAMES[m]} {res[m][1]}" for m in res)
    check(res == want, f"changement de machine réel (0x40014072) : {chain}")
    out = {}
    for name, img, pl in (("stock", stock, b""), ("modifié", patched, payload)):
        u = UI(img, pl)
        fill_records(u)
        this, vec = 0x93900000, 0x93910000
        u.uc.mem_write(vec, struct.pack(">8i", 1, 2, 3, 4, 5, 6, 0, 0))
        u.uc.mem_write(this + 104, struct.pack(">III", vec, vec + 24, vec + 24))
        r = {}
        for m in range(NM):
            u.hooks = {0x4001e318: ("machine", m), 0x400cf9a8: ("app", 0x93a00000), 0x4006b736: ("verrou", 0)}
            r[m] = [u.call(0x4001e814, this, k, 0, 0) for k in range(2, 16)]
        out[name] = r
    ok = all(out["stock"][m] == out["modifié"][m] for m in range(6))
    for m in FIRST:
        ok &= out["modifié"][m][:6] == [42, FIRST[m] + 4] + [FIRST[m] + i for i in range(4)]
    knobs = ", ".join(f"{NAMES[m]} {out['modifié'][m][:6]}" for m in FIRST)
    check(ok, f"potards de l'écran principal (0x4001e814) : 0..5 identiques ; {knobs}")


POISON = 0xa0000000                                 # zone non mappée : toute lecture par ces pointeurs est signalée


def poison(u):
    """Les 76 o avant le tableau des enregistrements (ce que l'OS lit pour une machine hors limites) : sur la
    machine, d'autres données ; ici des pointeurs vers une zone non mappée, pour que leur usage se voie."""
    u.uc.mem_write(REC_BASE - REC_LEN, struct.pack(">19I", *[POISON + 16 * k for k in range(19)]))


def out_of_range(stock, patched, payload):
    """Une piste réglée sur une machine qui n'existe pas dans CE firmware (projet fait avec un autre choix de
    moteurs : CPVtg était la machine 7 avec SD + CP, elle n'existe plus avec SYToy seul). Sur la machine,
    l'appui sur MACHINES gelait (notes/20 §5) : l'enregistrement lu était 76 o avant le tableau."""
    if not SAFE:
        print("        (tweak d'origine, non protégé : une machine au-delà de", TOP, "lit avant le tableau)")
        return
    u = UI(patched, payload)
    fill_records(u)
    poison(u)
    kick = u.call(0x4004df76, 0)
    ok = all(u.call(0x4004df76, m) == kick for m in (NM, NM + 1, 100, -1))
    ok &= all(u.call(0x4004df5c, i) == REC_BASE + REC_LEN for i in (NM + 1, NM + 2, 100, -1))
    this, vec = 0x93900000, 0x93910000
    u.uc.mem_write(vec, struct.pack(">8i", 1, 2, 3, 4, 5, 6, 0, 0))
    u.uc.mem_write(this + 104, struct.pack(">III", vec, vec + 24, vec + 24))
    knobs = {}
    for m in (0, NM, NM + 1, 100):
        u.hooks = {0x4001e318: ("machine", m), 0x400cf9a8: ("app", 0x93a00000), 0x4006b736: ("verrou", 0)}
        knobs[m] = [u.call(0x4001e814, this, k, 0, 0) for k in range(2, 8)]
        ok &= not u.bad
    ok &= all(knobs[m] == knobs[0] for m in knobs)
    wheel = {}
    for step in (-1, 1):
        u = UI(patched, payload)
        fill_records(u)
        poison(u)
        obj, snd = fake_track(u, NM)
        del u.hooks[0x40014072]
        this = 0x93900000
        for k in range(6):
            u.uc.mem_write(this + 70 + 4 * k, struct.pack(">i", -1))
        for a_, v in {0x400cf866: 0x93a00000, 0x4000eb90: 0x93a00000, 0x40012412: 0, 0x400cf9a8: 0x93a00000,
                      0x4006bdfe: 0, 0x4000eb9c: 0x93a00000, 0x40009c1a: obj, 0x400f44c6: 0, 0x4001416c: 0}.items():
            u.hooks[a_] = (f"{a_:#x}", v)
        u.call(0x400a2712, this, step, 0, 0)
        wheel[step] = (struct.unpack(">H", u.uc.mem_read(snd + 38, 2))[0] >> 8, bool(u.bad))
    ok &= wheel == {-1: (TOP, False), 1: (TOP, False)}
    check(ok, f"machine hors limites ({NM}, {NM + 1}, 100) : enregistrement et potards de KICK {knobs[NM]},"
              f" molette -> {wheel[-1][0]} / {wheel[1][0]}, aucun accès hors mémoire")


def small_icon(stock, patched, payload):
    got = {}
    for name, img, pl in (("stock", stock, b""), ("modifié", patched, payload)):
        for m in [0, 3, 5] + list(FIRST) + [NM]:
            u = UI(img, pl)
            u.hooks = {0x40071da4: "image"}
            u.uc.mem_write(0x40fe37f0, struct.pack(">I", 0x92200000))
            fp = t7.STACK - 0x100
            u.uc.mem_write(fp, struct.pack(">II", 0, t7.STOP))
            u.uc.reg_write(mk.UC_M68K_REG_A6, fp)
            u.uc.reg_write(mk.UC_M68K_REG_A7, fp - 0x80)
            u.uc.reg_write(mk.UC_M68K_REG_D2, m)
            u.uc.reg_write(mk.UC_M68K_REG_A0, 0x91000000)
            u.uc.emu_start(0x400a4dc4, t7.STOP, count=100_000)
            got[name, m] = [(args[1] - 0x92200000) // 28 for k, args in u.calls if k == "image"]
    ok = all(got["stock", m] == got["modifié", m] for m in (0, 3, 5, NM))
    ok &= all(got["modifié", m["index"]] == [m["image"]] for m in ADDED if not (m.get("pics") or [0, 0, 0])[2])
    for m in ADDED:                         # ses propres images (notes/71 §13) : la petite icône est la sienne
        if (m.get("pics") or [0, 0, 0])[2]:
            ok &= got["modifié", m["index"]] == [(m["pics"][2] - 0x92200000) // 28]
    icons = ", ".join(f"{m['name']} -> " + (f"its own {m['pics'][2]:#x}" if (m.get("pics") or [0, 0, 0])[2]
                                             else f"{NAMES[m['image']].upper()} {got['modifié', m['index']]}")
                      for m in ADDED)
    check(ok, f"petite icône : 0..5 identiques, {icons}")


# --- 6. son -------------------------------------------------------------------------------------------------
CP_CASES = [("défauts", {}), ("note 48", {"note": 48}), ("BODY 100", {"p1": 100}), ("BAL 0", {"p2": 0}),
            ("BAL 127", {"p2": 127}), ("SPCR 90", {"p3": 90}), ("BENV 110", {"p4": 110}), ("DEC 90", {"dec": 90})]
CASES = {"sd": [("défauts", {}), ("note 48", {"note": 48}), ("SWEP 127", {"p3": 127})], "cp": CP_CASES}
# SY BITS : Detune va de 40 à 88 (une valeur hors plage, venue d'un autre moteur, est bornée par la passerelle) ;
# PUNCH actif = Bit Redux à punch_on. 3e élément : ce que reçoit le Syntakt quand ça diffère du Cycles.
CASES["bits"] = [("défauts", {}), ("note 48", {"note": 48}), ("DET 40", {"p1": 40}), ("DET 64", {"p1": 64}),
                 ("DET 88", {"p1": 88}), ("BAL 0", {"p2": 0}), ("BAL 127", {"p2": 127}), ("SRR 64", {"p3": 64}),
                 ("SRR 127", {"p3": 127}), ("WAVE 0", {"p4": 0}), ("WAVE 64", {"p4": 64}), ("WAVE 127", {"p4": 127}),
                 ("DEC 90", {"dec": 90}), ("PUNCH -> Bit Redux", {"punch": 1}, {"punch": "punch_on"}),
                 ("COLOR 0 borné à 40", {"p1": 0}, {"p1": 40}), ("COLOR 127 borné à 88", {"p1": 127}, {"p1": 88})]
# SY SWARM : PUNCH inactif = Fundamental Sub 2 (défaut du Syntakt), actif = 1 (une octave plus bas).
CASES["swarm"] = [("défauts", {}), ("note 48", {"note": 48}), ("NMOD 0", {"p1": 0}), ("NMOD 127", {"p1": 127}),
                  ("ANIM 0", {"p2": 0}), ("ANIM 127", {"p2": 127}), ("DET 0", {"p3": 0}), ("DET 127", {"p3": 127}),
                  ("MIX 0", {"p4": 0}), ("MIX 64", {"p4": 64}), ("DEC 90", {"dec": 90}),
                  ("PUNCH -> Sub -1 octave", {"punch": 1}), ("PUNCH, note 36", {"punch": 1, "note": 36})]
GENERIC_CASES = [("défauts", {}), ("note 48", {"note": 48}), ("p1 0", {"p1": 0}), ("p1 127", {"p1": 127}),
                 ("p2 0", {"p2": 0}), ("p2 127", {"p2": 127}), ("p3 0", {"p3": 0}), ("p3 127", {"p3": 127}),
                 ("p4 0", {"p4": 0}), ("p4 127", {"p4": 127}), ("DEC 90", {"dec": 90})]


def sound(stock, patched, st_img, blocks):
    def cycles(img, machine, kw, note=60):
        e = E.Engine(img)
        for t in range(1, 6):
            e.uc.mem_write(E.VOICE0 + t * E.VSTRIDE, struct.pack(">I", 9))
        e.set(0, machine=machine, note=note, pitch=kw["tune"], color=kw["p1"], shape=kw["p2"], sweep=kw["p3"],
              contour=kw["p4"], punch=kw.get("punch", 0), gate=0, finetune=64, decay=kw["dec"])
        return e.render(blocks, trig_at=(1,)), e

    def syn(name, kw, note=60):
        e = S.Engine(st_img)
        e.solo(0)
        e.machine(0, name)
        e.note(0, note)
        e.set(0, tune=kw["tune"], p1=kw["p1"], p2=kw["p2"], p3=kw["p3"], p4=kw["p4"], punch=kw.get("punch", 0),
              gate=0, decay=kw["dec"], over=0)
        return e.render(blocks, trig_at=(1,))
    for m in ADDED:
        name, cases = m["label"], CASES.get(m["code"], GENERIC_CASES)
        base = dict(tune=64, p1=m["knobs"][0][2], p2=m["knobs"][1][2], p3=m["knobs"][2][2], p4=m["knobs"][3][2],
                    dec=m["decay"])
        ok, worst = True, 0
        for cname, over, *st in cases:
            kw = dict(base)
            kw.update(over)
            note = kw.pop("note", 60)
            skw = dict(kw)                              # ce que doit recevoir le moteur du Syntakt
            if "punch_on" in m:                         # emplacement 23 sans potard : PUNCH le commande
                skw["punch"] = m["punch_on"] if kw.get("punch") else m.get("punch_off", 0)
            skw.update({k: m[v] if isinstance(v, str) else v for k, v in (st[0] if st else {}).items()})
            a = syn(name, skw, note)
            b, e = cycles(patched, m["index"], kw, note)
            d = np.abs(a - 2 * b)
            worst = max(worst, int(d.max()))
            ok &= np.max(np.abs(a)) > 1e6 and d.max() <= 2 and not e.unmapped
        check(ok, f"{m['name']} (machine {m['index']}) identique au {name} du Syntakt ({len(cases)} cas, écart max {worst} LSB)")
    snare = dict(tune=64, p1=0, p2=127, p3=8, p4=0, dec=40)
    x, _ = cycles(stock, 1, snare)
    y, e = cycles(patched, 1, snare)
    check(np.array_equal(x, y) and np.max(np.abs(x)) > 1e6, "SNARE (machine 1) identique échantillon par échantillon à l'OS stock")
    e = E.Engine(patched)
    for t in range(1, 6):
        e.uc.mem_write(E.VOICE0 + t * E.VSTRIDE, struct.pack(">I", 9))
    last = ADDED[-1]
    e.set(0, machine=last["index"], note=60, pitch=64, finetune=64, **knob_kw(last))
    ran = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: ran.append(a), begin=E.PAYLOAD_CODE[0][0], end=E.PAYLOAD_CODE[0][1])
    x = e.render(50, trig_at=())
    check(not ran and not x.any(), f"au repos : {len(ran)} instructions du Syntakt, sortie muette")
    e = E.Engine(patched)
    for t in range(1, 6):
        e.uc.mem_write(E.VOICE0 + t * E.VSTRIDE, struct.pack(">I", 9))
    e.set(0, machine=1, note=60, pitch=64, finetune=64, color=0, shape=127, sweep=8, contour=0, decay=40)

    def locks(eng, blk):
        if blk % 60 == 0 and 1 <= blk // 60 <= N:
            m = ADDED[blk // 60 - 1]
            eng.set(0, machine=m["index"], **knob_kw(m))
    x = e.render(60 * (N + 1), trig_at=tuple(60 * k + 1 for k in range(N + 1)), on_block=locks)
    parts = [np.max(np.abs(x[32 * (60 * k + 2):32 * (60 * k + 60)])) for k in range(N + 1)]
    check(all(p > 1e6 for p in parts) and not e.unmapped,
          f"machine locks {' -> '.join(NAMES[m] for m in [1] + list(FIRST))} sur une piste : toutes jouent")


def knob_kw(m):
    return dict(zip(("color", "shape", "sweep", "contour"), (k[2] for k in m["knobs"])), decay=m["decay"])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--blocks", type=int, default=100)
    ap.add_argument("--tweak", default=str(TWEAK), help="tweak à vérifier (défaut : 23-syntakt-vintage.json)")
    args = ap.parse_args()
    tweak = json.loads(pathlib.Path(args.tweak).read_text(encoding="utf-8"))
    configure(tweak)
    added = ", ".join(f"{m['index']} = {m['name']}" for m in ADDED)
    print(f"{tweak['id']} : machines ajoutées {added}")
    stock = T.main_os_from_syx(args.cycles)
    patched, _ = build.apply_writes(stock, [tweak])
    payload, _ = build.build_payload([tweak], stock, args.syntakt)
    patched = bytes(patched) + payload
    print("démarrage")
    t7.X.bootstrap_depack_ok(args.cycles, tweak, args.syntakt) or t7.FAIL.append("bootstrap")
    t7.X.boot_hook_ok(patched, payload) or t7.FAIL.append("crochet")
    a, b = tables(stock, patched, payload)
    print("recherches")
    lookups(a, b)
    print("accesseurs")
    accessors(a, b, stock, patched)
    print("écran MACHINES, réglage, molette")
    screens(stock, patched, payload)
    setter_and_wheel(stock, patched, payload)
    print("enregistrements par machine, changement de machine, potards")
    records_and_change(stock, patched, payload)
    out_of_range(stock, patched, payload)
    small_icon(stock, patched, payload)
    print("son")
    sound(stock, patched, syntakt.dsp_image(args.syntakt), args.blocks)
    print("\nTOUT OK" if not t7.FAIL else f"\n{len(t7.FAIL)} ÉCHEC(S)")
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
