#!/usr/bin/env python3
"""Preuve du tweak sdvintage-7th (notes/18) : SD VINTAGE en 7e machine « SDVtg », à côté de SNARE.

On exécute le VRAI code de l'OS Cycles (stock et modifié) en émulation, fonction par fonction :
  1. démarrage : décompression par le bootstrap, crochet de recopie, constructeur des tables de paramètres
     (0x4005a274) : tables identiques au stock pour les machines 0..5, une 7e rangée pour SDVtg ;
  2. recherches (slot, machine) -> descripteur, « propre à une machine », CC reçu -> descripteur : identiques
     au stock partout, sauf la machine 6 qui trouve les descripteurs de SDVtg ;
  3. accesseurs des descripteurs et de leur état : identiques pour 0..75, les nouveaux pour 76..80 ;
  4. écran MACHINES (dessin intercepté) : noms, images et repères pour les machines 0..6 ;
  5. icône de machine bornée : SNARE pour SDVtg ;
  6. son : SDVtg identique au Syntakt, SNARE identique à la SNARE d'origine, rien du Syntakt au repos.

    python3 tools/emu/test_sdvintage_7th.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx
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
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_MEM_UNMAPPED, UC_HOOK_CODE, UcError
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                  # noqa: E402
import gen_sdvintage_7th as g7  # noqa: E402
import mcengine as E          # noqa: E402
import syntakt                # noqa: E402
import test_sdvintage as T    # noqa: E402
import test_sdvintage_exact as X  # noqa: E402

TWEAK = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "22-sdvintage-7th.json"
BASE, STOP, STACK = 0x40000400, 0x90000100, 0x90010000
SCRATCH = 0x91000000
FAIL = []


def check(ok, msg):
    print(f"  {'ok   ' if ok else 'ECHEC'} {msg}", flush=True)
    if not ok:
        FAIL.append(msg)
    return ok


class UI:
    """Le code de l'interface de l'OS, exécuté fonction par fonction (image + BSS + charge utile)."""

    def __init__(self, img, payload=b""):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x02400000)            # image + BSS (jusqu'à 0x423380b0)
        uc.mem_write(BASE, img[:E.IMAGE_LEN])
        uc.mem_map(0x43000000, max(0x00100000, (len(payload) + 0xfffff) & ~0xfffff))   # charge utile et variables
        uc.mem_write(0x43000000, payload)
        uc.mem_map(0x90000000, 0x04000000)            # pile, objets factices, fonctions interceptées
        uc.mem_write(STOP, b"\x4e\x71\x4e\x71")
        self.bad, self.hooks, self.calls = [], {}, []
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.bad.append(addr) or False)
        uc.hook_add(UC_HOOK_CODE, self._hook)

    def _hook(self, uc, addr, size, ud):
        if addr in self.hooks:                        # fonction interceptée : on note ses arguments, rts
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack(">8I", uc.mem_read(sp + 4, 32))
            name, ret = self.hooks[addr] if isinstance(self.hooks[addr], tuple) else (self.hooks[addr], 0)
            self.calls.append((name, args))
            uc.reg_write(mk.UC_M68K_REG_D0, ret)
            uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def u32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def call(self, fn, *args, count=20_000_000):
        self.uc.reg_write(mk.UC_M68K_REG_A0, SCRATCH)      # 0x4005a65a copie 12 o vers (a0)
        sp = STACK - 0x400
        self.uc.mem_write(sp, struct.pack(">I" + "I" * len(args), STOP, *[a & 0xffffffff for a in args]))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        self.bad.clear()
        self.uc.emu_start(fn, STOP, count=count)
        return self.uc.reg_read(mk.UC_M68K_REG_D0)


def dis(img, va, n=2):
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "x.bin"
        p.write_bytes(img[va - BASE:va - BASE + n])
        out = subprocess.run(["m68k-elf-objdump", "-D", "-b", "binary", "-m", "m68k:cfv4e", f"--adjust-vma={va:#x}",
                              str(p)], capture_output=True, text=True).stdout
    return " ".join(l.split("\t")[-1].strip() for l in out.splitlines() if re.match(r"\s*[0-9a-f]+:\t", l))


# --- 1. tables construites au démarrage --------------------------------------------------------------
BSS_TABLES = (0x40a79200, 0x40a7b000)
ROW_COUNT = 0x40a79260


def tables(stock, patched, payload):
    a, b = UI(stock), UI(patched, payload)
    a.call(0x4005a274)
    b.call(0x4005a274)
    check(not a.bad and not b.bad, "constructeur des tables (0x4005a274) exécuté sans accès hors mémoire")
    sa = bytes(a.uc.mem_read(BSS_TABLES[0], BSS_TABLES[1] - BSS_TABLES[0]))
    sb = bytearray(b.uc.mem_read(BSS_TABLES[0], BSS_TABLES[1] - BSS_TABLES[0]))
    rows_a = sa[g7.ROWS - BSS_TABLES[0]:][:6 * 32]
    cc_a = sa[g7.CCROWS - BSS_TABLES[0]:][:6 * 32]
    rows_b = bytes(b.uc.mem_read(g7.ROWS7, 7 * 32))
    cc_b = bytes(b.uc.mem_read(g7.CCROWS7, 7 * 32))
    # les anciennes tables par machine restent vides dans l'OS modifié : on les remet pour comparer le reste
    sb[g7.ROWS - BSS_TABLES[0]:g7.ROWS - BSS_TABLES[0] + 6 * 32] = rows_a
    sb[g7.CCROWS - BSS_TABLES[0]:g7.CCROWS - BSS_TABLES[0] + 6 * 32] = cc_a
    nrows = (a.u32(ROW_COUNT), b.u32(ROW_COUNT))            # nombre de rangées de « decay » par machine
    sb[ROW_COUNT - BSS_TABLES[0]:ROW_COUNT - BSS_TABLES[0] + 4] = sa[ROW_COUNT - BSS_TABLES[0]:][:4]
    check(nrows == (6, 7), f"rangées de machines construites : stock {nrows[0]}, modifié {nrows[1]}")
    check(bytes(sb) == sa, "toutes les autres tables du BSS identiques au stock")
    check(rows_b[:6 * 32] == rows_a and cc_b[:6 * 32] == cc_a, "rangées des machines 0..5 identiques au stock")
    r6 = struct.unpack(">8I", rows_b[6 * 32:])
    c6 = struct.unpack(">8I", cc_b[6 * 32:])
    r1 = struct.unpack(">8I", rows_a[32:64])
    c1 = struct.unpack(">8I", cc_a[32:64])
    exp_r = tuple(80 if x == 55 else 76 + x - 51 if 51 <= x <= 54 else x for x in r1)
    exp_c = tuple(76 + x - 51 if 51 <= x <= 54 else x for x in c1)
    check(r6 == exp_r and c6 == exp_c, f"rangée 6 = SDVtg : slots {r6[:6]} (SNARE {r1[:6]}), CC 16..19 {c6[:4]}")
    return a, b


# --- 2. recherches -----------------------------------------------------------------------------------
def lookups(a, b):
    diff = []
    for m in range(7):                               # 0..6 : les seules valeurs possibles de la machine
        for slot in range(34):
            x, y = a.call(0x4005a692, slot, m), b.call(0x4005a692, slot, m)
            if x != y:
                diff.append((m, slot, x, y))
    ok6 = all(m == 6 and ((s in (0xb, 0xc, 0xd, 0xe) and y == 76 + s - 0xb) or (s == 0x12 and y == 80))
              for m, s, x, y in diff)
    check(ok6 and len(diff) == 5, f"(slot, machine) -> descripteur : identique sauf machine 6 ({len(diff)} écarts, tous SDVtg)")
    spec = [(i, a.call(0x4005a556, i), b.call(0x4005a556, i)) for i in range(90)]
    bad = [(i, x, y) for i, x, y in spec if (x != y) != (76 <= i <= 79)]
    check(not bad, "« descripteur propre à une machine » : identique, plus 76..79 (SDVtg)")
    diff = []
    for t in range(8):
        for m in range(7):
            for cc in range(128):
                x, y = a.call(0x4005a8ce, t, m, cc), b.call(0x4005a8ce, t, m, cc)
                if x != y:
                    diff.append((t, m, cc, x, y))
    ok = all(t <= 5 and m == 6 for t, m, *_ in diff) and \
        {(cc, y) for t, m, cc, x, y in diff} == {(16, 76), (17, 77), (18, 78), (19, 79)}
    check(ok, f"CC reçu -> descripteur : identique sauf pistes 0..5 en machine 6 ({len(diff)} écarts)")


# --- 3. accesseurs -----------------------------------------------------------------------------------
def accessors(a, b, stock, patched):
    L = subprocess.run(["m68k-elf-objdump", "-D", "-b", "binary", "-m", "m68k:cfv4e", f"--adjust-vma={BASE:#x}",
                        "--start-address=0x40000400", "--stop-address=0x40060000", str(STOCK_BIN)],
                       capture_output=True, text=True).stdout.splitlines()
    addrs, rts = [], set()
    for l in L:
        m = re.match(r"\s*([0-9a-f]+):\t", l)
        if m:
            addrs.append(int(m.group(1), 16))
            if l.rstrip().endswith("rts"):
                rts.add(addrs[-1])
    entries = set()
    for va in g7.BOUNDS + (0x4004df40, 0x4004dfa2):
        k = bisect.bisect_left(addrs, va)
        while k > 0 and addrs[k - 1] not in rts:
            k -= 1
        entries.add(addrs[k])
    lo7, hi7 = g7.DESC, g7.DESC + g7.NDESC * g7.DSTRIDE

    def norm(v):                                     # un pointeur dans la table stock -> même entrée déplacée
        return v - lo7 + g7.DESC7 if lo7 <= v < hi7 else v
    tested, skipped, bad = 0, [], []
    for fn in sorted(entries):
        try:
            ra = [a.call(fn, i, i, i, count=200_000) for i in range(76)]
            rb = [b.call(fn, i, i, i, count=200_000) for i in range(76)]
        except UcError:
            skipped.append(fn)
            continue
        if a.bad or b.bad:
            skipped.append(fn)
            continue
        tested += 1
        if [norm(x) for x in ra] != rb:
            bad.append(fn)
    check(not bad and tested >= 20, f"{tested} accesseurs identiques au stock pour les descripteurs 0..75"
          f" ({len(skipped)} méthodes d'objet non appelables seules)" + (f" ; écarts : {[hex(x) for x in bad]}" if bad else ""))
    # toutes les bornes, y compris celles des méthodes non appelables seules : relues dans le désassemblage
    ok = all(dis(stock, va).startswith(("moveq #76,", "moveq #75,")) and
             dis(patched, va) == dis(stock, va).replace("#76,", "#81,").replace("#75,", "#80,") for va in g7.BOUNDS)
    ok &= all(dis(patched, va, 6).startswith("jmp 0x4303") for va, _, _ in g7.JUMPS)
    check(ok, f"les {len(g7.BOUNDS)} bornes 76/75 deviennent 81/80, les {len(g7.JUMPS)} détours sont des jmp vers la charge utile")
    # nouveaux descripteurs : champs lus par les accesseurs simples
    ok = True
    for i, (long_, short, default) in enumerate(g7.KNOBS):
        idx = 76 + i
        ok &= b.call(0x4005a50a, idx) == 6                       # machine
        ok &= b.call(0x4005a4e8, idx) == 0xb + i                 # slot
        name = bytes(b.uc.mem_read(b.call(0x4000b22a, 0, idx), 16)).split(b"\0")[0].decode()
        short_ = bytes(b.uc.mem_read(b.call(0x4000b208, 0, idx), 8)).split(b"\0")[0].decode()
        ok &= (name, short_) == (long_, short)
        b.call(0x4005a65a, idx)
        ok &= struct.unpack(">3i", b.uc.mem_read(SCRATCH, 12)) == (0, 127 << 8, default << 8)
    b.call(0x4005a65a, 80)
    ok &= struct.unpack(">3i", b.uc.mem_read(SCRATCH, 12))[2] == g7.DECAY_DEFAULT << 8
    b.call(0x4005a65a, g7.ALG_DESC)
    ok &= struct.unpack(">3i", b.uc.mem_read(SCRATCH, 12))[1] == 6 << 8
    check(ok, "descripteurs 76..80 : machine 6, slots, noms (Inharm/INHM…), plages, défauts 0/110/74/80/33 ;"
              " « Algorithm » va jusqu'à 6")
    # état par descripteur : 76..80 partagent celui de SNARE (51..55)
    st = [(a.call(0x4004df40, i), b.call(0x4004df40, i)) for i in range(90)]
    ok = all(y == x for x, y in st[:76]) and all(st[i][1] == st[i - 25][0] for i in range(76, 81)) \
        and all(y == st[0][0] for x, y in st[81:])
    b.hooks = {0x400ddf60: "connect"}
    a.hooks = {0x400ddf60: "connect"}
    for i in (0, 51, 75, 76, 80, 81):
        b.calls.clear()
        a.calls.clear()
        rb = b.call(0x4004dfa2, i, 0x1234)
        ra = a.call(0x4004dfa2, min(i - 25, 0) if i > 80 else (i - 25 if i >= 76 else i), 0x1234)
        ok &= rb == ra == 0x40a71500 and [c[1][:2] for c in b.calls] == [c[1][:2] for c in a.calls]
    b.hooks, a.hooks = {}, {}
    check(ok, "état par descripteur (0x4004df40, 0x4004dfa2) : 0..75 inchangés, 76..80 -> SNARE 51..55")


# --- 4. écran MACHINES -------------------------------------------------------------------------------
def drum_select(img, payload, m):
    u = UI(img, payload)
    u.hooks = {0x40071a04: "texte", 0x40071da4: "image", 0x40070c4e: "repère", 0x40070efc: "repère plein",
               0x93000000: "a5", 0x93000010: "a4"}
    for a in (0x93000000, 0x93000010):
        u.uc.mem_write(a, b"\x4e\x75")
    u.uc.mem_write(0x40fe32cc, struct.pack(">I", 0x92000000))
    u.uc.mem_write(0x40fe384c, struct.pack(">I", 0x92100000))
    u.uc.mem_write(0x91001000 + 108, struct.pack(">I", 0x91002000))
    sp = STACK - 0x800
    u.uc.mem_write(sp, struct.pack(">I", STOP) * 64)   # on entre au milieu de la fonction : tout retour -> STOP
    regs = {mk.UC_M68K_REG_D3: m, mk.UC_M68K_REG_D2: 0x91000000, mk.UC_M68K_REG_A2: 0x91001000,
            mk.UC_M68K_REG_A5: 0x93000000, mk.UC_M68K_REG_A4: 0x93000010, mk.UC_M68K_REG_A7: sp}
    for r, v in regs.items():
        u.uc.reg_write(r, v)
    u.uc.emu_start(0x400a25e0, STOP, count=1_000_000)
    txt = [bytes(u.uc.mem_read(args[6], 12)).split(b"\0")[0].decode() for k, args in u.calls if k == "texte"]
    imgs = [args[1] for k, args in u.calls if k == "image"]
    marks = [k for k, args in u.calls if k.startswith("repère")]
    return txt, imgs, marks, u.bad


def screens(stock, patched, payload):
    names = ["Kick", "Snare", "Metal", "Perc", "Tone", "Chord"]
    ok = True
    for m in range(7):
        ts, is_, ms, bs = drum_select(stock, b"", m)
        tp, ip, mp, bp = drum_select(patched, payload, m)
        shown = 1 if m == 6 else m
        want_img = [0x92000000 + 28 * shown, 0x92100000 + 28 * shown]
        full = ["repère"] * 7
        full[m] = "repère plein"
        ok &= not bp and tp == [(names + ["SDVtg"])[m]] and ip == want_img and mp == full
        if m < 6:
            ok &= ts == tp and is_ == ip and ms == mp[:6]
        else:
            ok &= ts == ["Error"] and is_ == []
        print(f"        machine {m} : stock {ts} {len(ms)} repères | modifié {tp}, images {[hex(x) for x in ip]},"
              f" repère plein n° {mp.index('repère plein') + 1}/{len(mp)}")
    check(ok, "écran MACHINES : 7 noms, 7 repères, images identiques pour 0..5, images de SNARE pour SDVtg")


# --- 4b. réglage de la machine d'une piste (menu MACHINES, CC 70) -------------------------------------
def fake_track(u, machine):
    """Une piste factice pour 0x4001477e / 0x4001488a : ses méthodes sont interceptées, vt[40] rend son son."""
    obj, vt, snd = 0x93800000, 0x93801000, 0x93802000
    u.uc.mem_write(obj, struct.pack(">I", vt))
    for k in range(16):
        u.uc.mem_write(vt + 4 * k, struct.pack(">I", 0x93803000 + 16 * k))
        u.hooks[0x93803000 + 16 * k] = (f"vt{4 * k}", snd if 4 * k == 40 else 0)
    for fn in (0x400cf866, 0x4000eb90, 0x40013126, 0x40014072):
        u.hooks[fn] = (f"{fn:#x}", 0)
    u.uc.mem_write(snd + 38, struct.pack(">H", machine << 8))
    return obj, snd


REC_BASE, REC_LEN = 0x40a71540, 76
REP = 0x93b00000                                     # une chaîne C++ factice (copie sur écriture) : « GROO »


def fill_records(u):
    """Les 7 enregistrements par machine, comme les construit l'OS au démarrage (0x400e0fc6..) : deux chaînes,
    puis les 17 descripteurs de la page (PITCH, DECAY, COLOR..CONTOUR de la machine, puis paramètres communs)."""
    u.uc.mem_write(REP, struct.pack(">iii", 4, 4, 0) + b"GROO\0")
    for i in range(7):
        rec = bytearray(REC_LEN)
        rec[0:8] = struct.pack(">II", REP + 12, REP + 12)
        if i:
            b = 46 + 5 * (i - 1)
            ids = [42, b + 4, b, b + 1, b + 2, b + 3, 26, 27, 29, 25, 23, 22, 39, 37, 40, 38, 9]
            rec[8:] = struct.pack(">17i", *ids)
        u.uc.mem_write(REC_BASE + REC_LEN * i, bytes(rec))


def refcount(u):
    return struct.unpack(">i", u.uc.mem_read(REP + 8, 4))[0]


def records(stock, patched, payload):
    a, b = UI(stock), UI(patched, payload)
    for u in (a, b):
        fill_records(u)
    ok = all(a.call(0x4004df5c, i) == b.call(0x4004df5c, i) for i in list(range(7)) + [8, 100])
    ok &= all(a.call(0x4004df76, m) == b.call(0x4004df76, m) for m in list(range(6)) + [7, 100])
    before = refcount(b)
    r7, r6 = b.call(0x4004df5c, 7), b.call(0x4004df76, 6)
    rec = bytes(b.uc.mem_read(r7, REC_LEN))
    ids = struct.unpack(">17i", rec[8:])
    ok &= r7 == r6 == g7.REC8 and rec[:8] == struct.pack(">II", REP + 12, REP + 12) and refcount(b) == before + 2
    ok &= ids == (42, 80, 76, 77, 78, 79, 26, 27, 29, 25, 23, 22, 39, 37, 40, 38, 9)
    stock7 = a.call(0x4004df5c, 7)
    check(ok, f"enregistrements par machine : 0..6 identiques ; SDVtg -> 8e enregistrement {r7:#x} (descripteurs {ids[:6]},"
              f" chaînes partagées avec la bonne référence) ; stock : {stock7:#x}, avant le tableau")


def machine_change(stock, patched, payload):
    """Molette de Chord vers SDVtg, avec le VRAI gestionnaire de changement de machine (0x40014072) : c'est lui
    qui gelait (enregistrement lu avant le tableau). Il doit écrire les défauts de SDVtg dans le son."""
    res = {}
    for name, img, pl in (("stock", stock, b""), ("modifié", patched, payload)):
        u = UI(img, pl)
        fill_records(u)
        obj, snd = fake_track(u, 5)
        del u.hooks[0x40014072]
        this = 0x93900000
        for k in range(6):
            u.uc.mem_write(this + 70 + 4 * k, struct.pack(">i", -1))
        for a_, v in {0x400cf866: 0x93a00000, 0x4000eb90: 0x93a00000, 0x40012412: 0, 0x400cf9a8: 0x93a00000,
                      0x4006bdfe: 0, 0x4000eb9c: 0x93a00000, 0x40009c1a: obj, 0x400f44c6: 0, 0x4001416c: 0}.items():
            u.hooks[a_] = (f"{a_:#x}", v)
        rc = refcount(u)
        u.call(0x400a2712, this, 1, 0, 0)
        m = struct.unpack(">H", u.uc.mem_read(snd + 38, 2))[0] >> 8
        # le son range ses valeurs 8.8 à 0x14 + 2 x slot (la machine, slot 9, est à +38)
        vals = [struct.unpack(">h", u.uc.mem_read(snd + 0x14 + 2 * sl, 2))[0] >> 8 for sl in (0xb, 0xc, 0xd, 0xe, 0x12)]
        res[name] = (m, vals, refcount(u) - rc, bool(u.bad))
    s_, p_ = res["stock"], res["modifié"]
    ok = s_[0] == 5 and p_[0] == 6 and p_[1] == [0, 110, 74, 80, 33] and not p_[3]
    check(ok, f"Chord -> SDVtg avec le vrai changement de machine (0x40014072) : modifié machine {p_[0]}, défauts {p_[1]},"
              f" +{p_[2]} référence(s) (la 8e fiche) ; stock machine {s_[0]}")


def knobs(stock, patched, payload):
    """Écran principal, potard -> descripteur (méthode 0x4001e814) : machine -> enregistrement par le vecteur
    [1..6] de l'écran, puis descripteur = enregistrement[potard]. Pour SDVtg, l'OS lisait après le vecteur."""
    res = {}
    for name, img, pl in (("stock", stock, b""), ("modifié", patched, payload)):
        u = UI(img, pl)
        fill_records(u)
        this, vec = 0x93900000, 0x93910000
        u.uc.mem_write(vec, struct.pack(">7i", 1, 2, 3, 4, 5, 6, 0))   # après le vecteur : 0 ici
        u.uc.mem_write(this + 104, struct.pack(">III", vec, vec + 24, vec + 24))
        out = {}
        for m in range(7):
            u.hooks = {0x4001e318: ("machine", m), 0x400cf9a8: ("app", 0x93a00000), 0x4006b736: ("verrou", 0)}
            out[m] = [u.call(0x4001e814, this, k, 0, 0) for k in range(2, 16)]
        res[name] = out
    same = all(res["stock"][m] == res["modifié"][m] for m in range(6))
    got = res["modifié"][6][:6]
    ok = same and got == [42, 80, 76, 77, 78, 79] and res["modifié"][6][6:] == res["modifié"][1][6:]
    check(ok, f"potards de l'écran principal (0x4001e814) : machines 0..5 identiques ; SDVtg -> {got}"
              f" (PITCH, DEC, INHM, FCMP, SWEP, MENV) ; stock -> {res['stock'][6][:6]}")


def wheel(stock, patched, payload):
    """Molette de l'écran MACHINES : 0x4001488a(piste, pas) = machine + pas, bornée, puis 0x4001477e."""
    seq = {}
    for name, img, pl in (("stock", stock, b""), ("modifié", patched, payload)):
        u = UI(img, pl)
        obj, snd = fake_track(u, 0)
        out = []
        for step in [1] * 8 + [-1] * 3:
            u.call(0x4001488a, obj, step, 0, 0)
            out.append(struct.unpack(">H", u.uc.mem_read(snd + 38, 2))[0] >> 8)
        seq[name] = out
    ok = seq["stock"] == [1, 2, 3, 4, 5, 5, 5, 5, 4, 3, 2] and seq["modifié"] == [1, 2, 3, 4, 5, 6, 6, 6, 5, 4, 3]
    check(ok, f"molette (0x4001488a, +1 x8 puis -1 x3) : stock {seq['stock']}, modifié {seq['modifié']}")
    # tout le gestionnaire de l'écran MACHINES (0x400a2712, appelé par l'événement molette 0x400a28b4),
    # son environnement intercepté : piste active 0, aucun pas tenu
    seq = {}
    for name, img, pl in (("stock", stock, b""), ("modifié", patched, payload)):
        u = UI(img, pl)
        obj, snd = fake_track(u, 0)
        this = 0x93900000
        for k in range(6):
            u.uc.mem_write(this + 70 + 4 * k, struct.pack(">i", -1))
        for a, v in {0x400cf866: 0x93a00000, 0x4000eb90: 0x93a00000, 0x40012412: 0, 0x400cf9a8: 0x93a00000,
                     0x4006bdfe: 0, 0x4000eb9c: 0x93a00000, 0x40009c1a: obj, 0x400f44c6: 0, 0x4001416c: 0}.items():
            u.hooks[a] = (f"{a:#x}", v)
        out = []
        for _ in range(8):
            u.call(0x400a2712, this, 1, 0, 0)
            out.append(struct.unpack(">H", u.uc.mem_read(snd + 38, 2))[0] >> 8)
        seq[name] = out
    check(seq["stock"] == [1, 2, 3, 4, 5, 5, 5, 5] and seq["modifié"] == [1, 2, 3, 4, 5, 6, 6, 6],
          f"gestionnaire de l'écran MACHINES (0x400a2712), +1 x8 : stock {seq['stock']}, modifié {seq['modifié']}")


def machine_setter(stock, patched, payload):
    """0x4001477e(piste, machine, _, drapeau) : écrit la machine dans le son de la piste (+38) et, si elle
    change, appelle 0x40014072 (valeurs par défaut de la machine). L'OS stock refuse au-delà de 5."""
    got = {}
    for name, img, pl in (("stock", stock, b""), ("modifié", patched, payload)):
        for m in range(8):
            u = UI(img, pl)
            obj, vt, snd = 0x93800000, 0x93801000, 0x93802000
            u.uc.mem_write(obj, struct.pack(">I", vt))
            for k in range(16):                          # méthodes de la piste : interceptées
                u.uc.mem_write(vt + 4 * k, struct.pack(">I", 0x93803000 + 16 * k))
                u.hooks[0x93803000 + 16 * k] = (f"vt{4 * k}", snd if 4 * k == 40 else 0)
            for fn in (0x400cf866, 0x4000eb90, 0x40013126, 0x40014072):
                u.hooks[fn] = (f"{fn:#x}", 0)
            u.uc.mem_write(snd + 38, struct.pack(">H", 1 << 8))   # la piste est en SNARE
            u.call(0x4001477e, obj, m, 0, 0)
            changed = any(c[0] == "0x40014072" for c in u.calls)
            got[name, m] = (struct.unpack(">H", u.uc.mem_read(snd + 38, 2))[0] >> 8, changed)
    ok = all(got["stock", m] == got["modifié", m] for m in range(6))
    ok &= got["stock", 6] == (1, False) and got["modifié", 6] == (6, True) and got["modifié", 7] == (1, False)
    check(ok, f"réglage de la machine (0x4001477e) : SDVtg (6) accepté et défauts chargés ; stock {got['stock', 6]},"
              f" modifié {got['modifié', 6]}, 7 refusé {got['modifié', 7]}")


# --- 5. icône bornée ---------------------------------------------------------------------------------
def small_icon(patched, stock, payload):
    ok = True
    for va in (0x4001b69c, 0x400a40a6, 0x400a4fb0):
        ok &= dis(stock, va) == "moveq #5,%d0" and dis(patched, va) == "moveq #1,%d0"
    got = {}
    for name, img, pl in (("stock", stock, b""), ("modifié", patched, payload)):
        for m in (-1, 0, 3, 5, 6):
            u = UI(img, pl)
            u.hooks = {0x40071da4: "image"}
            u.uc.mem_write(0x40fe37f0, struct.pack(">I", 0x92200000))
            fp = STACK - 0x100
            u.uc.mem_write(fp, struct.pack(">II", 0, STOP))
            u.uc.reg_write(mk.UC_M68K_REG_FP, fp) if hasattr(mk, "UC_M68K_REG_FP") else u.uc.reg_write(mk.UC_M68K_REG_A6, fp)
            u.uc.reg_write(mk.UC_M68K_REG_A7, fp - 0x80)
            u.uc.reg_write(mk.UC_M68K_REG_D2, m & 0xffffffff)
            u.uc.reg_write(mk.UC_M68K_REG_A0, 0x91000000)
            u.uc.emu_start(0x400a4dc4, STOP, count=100_000)
            got[name, m] = [(args[1] - 0x92200000) // 28 for k, args in u.calls if k == "image"]
    ok &= all(got["stock", m] == got["modifié", m] for m in (-1, 0, 3, 5))
    ok &= got["stock", 6] == [5] and got["modifié", 6] == [1]
    check(ok, f"icônes bornées : identiques pour 0..5, SNARE au lieu de CHORD pour SDVtg (stock {got['stock', 6]},"
              f" modifié {got['modifié', 6]})")


# --- 6. son ------------------------------------------------------------------------------------------
def sound(stock, patched, syntakt_img, blocks):
    def cycles(img, machine, kw, note=60):
        e = E.Engine(img)
        for t in range(1, 6):                          # coupe les autres voix : machine hors bornes
            e.uc.mem_write(E.VOICE0 + t * E.VSTRIDE, struct.pack(">I", 7))
        e.set(0, machine=machine, note=note, pitch=kw["tune"], color=kw["inhm"], shape=kw["fcmp"], sweep=kw["swep"],
              contour=kw["menv"], punch=kw["punch"], gate=kw["gate"], finetune=64, decay=kw["dec"])
        x = e.render(blocks, trig_at=(1,))
        return x, e
    ok = True
    for name, over in X.CASES[:6]:
        kw = dict(X.DEF)
        kw.update(over)
        note = kw.pop("note", 60)
        a = X.render_syntakt(syntakt_img, blocks, note, kw)
        b, e = cycles(patched, 6, kw, note)
        d = np.abs(a - 2 * b)
        ok &= np.max(np.abs(a)) > 1e6 and d.max() <= 2 and not e.unmapped
    check(ok, "SDVtg (machine 6) identique au Syntakt (6 cas, 1 LSB)")
    snare = dict(tune=64, inhm=0, fcmp=127, swep=8, menv=0, punch=0, gate=0, dec=40)
    x, _ = cycles(stock, 1, snare)
    y, e = cycles(patched, 1, snare)
    check(np.array_equal(x, y) and np.max(np.abs(x)) > 1e6 and not e.unmapped,
          "SNARE (machine 1) identique échantillon par échantillon à la SNARE de l'OS stock")
    e = E.Engine(patched)
    for t in range(1, 6):
        e.uc.mem_write(E.VOICE0 + t * E.VSTRIDE, struct.pack(">I", 7))
    e.set(0, machine=6, note=60, pitch=64, finetune=64, color=0, shape=110, sweep=74, contour=80, decay=33)
    ran = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: ran.append(a), begin=E.PAYLOAD_CODE[0][0], end=E.PAYLOAD_CODE[0][1])
    x = e.render(50, trig_at=())
    check(not ran and not x.any() and not e.unmapped, f"au repos : {len(ran)} instructions du Syntakt, sortie muette")
    # machine lock : SNARE puis SDVtg sur la même piste
    e = E.Engine(patched)
    for t in range(1, 6):
        e.uc.mem_write(E.VOICE0 + t * E.VSTRIDE, struct.pack(">I", 7))
    e.set(0, machine=1, note=60, pitch=64, finetune=64, color=0, shape=127, sweep=8, contour=0, decay=40)

    def switch(eng, b):
        if b == 60:
            eng.set(0, machine=6, shape=110, sweep=74, contour=80, decay=33)
    x = e.render(160, trig_at=(1, 61), on_block=switch)
    s1, s2 = np.max(np.abs(x[32 * 2:32 * 60])), np.max(np.abs(x[32 * 62:]))
    check(s1 > 1e6 and s2 > 1e6 and not e.unmapped, "machine lock SNARE -> SDVtg sur la même piste : les deux jouent")


def main():
    global STOCK_BIN
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--blocks", type=int, default=120)
    args = ap.parse_args()
    tweak = json.loads(TWEAK.read_text(encoding="utf-8"))
    stock = T.main_os_from_syx(args.cycles)
    patched, _ = build.apply_writes(stock, [tweak])
    payload, _ = build.build_payload([tweak], stock, args.syntakt)
    patched = bytes(patched) + payload
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(stock)
        STOCK_BIN = f.name

    print("démarrage")
    X.bootstrap_depack_ok(args.cycles, tweak, args.syntakt) or FAIL.append("bootstrap")
    X.boot_hook_ok(patched, payload) or FAIL.append("crochet")
    a, b = tables(stock, patched, payload)
    print("recherches")
    lookups(a, b)
    print("accesseurs")
    accessors(a, b, stock, patched)
    print("écran MACHINES")
    screens(stock, patched, payload)
    machine_setter(stock, patched, payload)
    wheel(stock, patched, payload)
    records(stock, patched, payload)
    machine_change(stock, patched, payload)
    knobs(stock, patched, payload)
    small_icon(patched, stock, payload)
    print("son")
    sound(stock, patched, syntakt.dsp_image(args.syntakt), args.blocks)
    pathlib.Path(STOCK_BIN).unlink()
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
