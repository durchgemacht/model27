#!/usr/bin/env python3
"""Preuve du portage exact (notes/17) : le vrai SD VINTAGE du Syntakt, extrait de TON Syntakt_OS1.42.syx
et greffé dans TON OS Cycles par le tweak sdvintage-exact, doit sortir EXACTEMENT les mêmes échantillons
que dans le moteur audio du Syntakt émulé (stengine.py).

Vérifie aussi le démarrage : le vrai décompresseur du bootstrap relit l'OS agrandi, le crochet recopie la charge
utile, et aucun code du Syntakt ne tourne tant qu'une piste SNARE n'est pas déclenchée.

Même note, mêmes réglages, même instant de déclenchement. La boucle des voix du Cycles divise la sortie
d'une piste par 2 : on compare Cycles x 2 et Syntakt, à 1 LSB près (arrondi du décalage).

    python3 tools/emu/test_sdvintage_exact.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx
"""
import argparse
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                  # noqa: E402  (tools/build.py)
import mcengine as E          # noqa: E402
import stengine as S          # noqa: E402
import syntakt                # noqa: E402
import test_sdvintage as T    # noqa: E402

TWEAK = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "21-sdvintage-exact.json"
DEF = dict(tune=64, inhm=0, fcmp=110, swep=74, menv=80, punch=0, gate=0, dec=33)
CASES = [
    ("défauts", {}), ("note 48", {"note": 48}), ("note 72", {"note": 72}), ("TUNE 76", {"tune": 76}),
    ("SWEP 127", {"swep": 127}), ("SWEP 0", {"swep": 0}), ("INHM 127", {"inhm": 127}), ("FCMP 0", {"fcmp": 0}),
    ("MENV 0", {"menv": 0}), ("DEC 90", {"dec": 90}), ("DEC 5", {"dec": 5}), ("PNCH", {"punch": 1}),
]


def render_syntakt(img, blocks, note, kw):
    e = S.Engine(img)
    e.solo(0)
    e.machine(0, "SD VINTAGE")
    e.note(0, note)
    e.set(0, tune=kw["tune"], p1=kw["inhm"], p2=kw["fcmp"], p3=kw["swep"], p4=kw["menv"], punch=kw["punch"],
          gate=kw["gate"], decay=kw["dec"], over=0)
    x = e.render(blocks, trig_at=(1,))
    assert not e.unmapped, e.unmapped[:3]
    return x


def render_cycles(os_img, blocks, note, kw):
    e = E.Engine(os_img)
    e.solo(0)
    e.set(0, machine="SNARE", note=note, pitch=kw["tune"], color=kw["inhm"], shape=kw["fcmp"], sweep=kw["swep"],
          contour=kw["menv"], punch=kw["punch"], gate=kw["gate"], finetune=64, decay=kw["dec"])
    x = e.render(blocks, trig_at=(1,))
    assert not e.unmapped, [(hex(a), hex(b)) for a, b in e.unmapped[:3]]
    return x


def boot_hook_ok(os_img, payload):
    """Exécute la vraie remise à zéro du BSS 0x400004b2 de l'OS patché : le crochet doit recopier la charge
    utile vers 0x43000000, puis le BSS (qui la contenait) doit être remis à zéro et la fonction revenir. La SRAM
    est déjà initialisée par l'OS (0x4000045c, appelée juste avant) : le crochet n'y touche pas, sauf si le tweak
    sort de la SRAM les tables d'ondes de CHORD (notes/28) ; il y recopie alors le début de la charge utile
    (E.SRAM_BANKS), et rien d'autre."""
    from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
    from unicorn import m68k_const as mk
    import struct
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
    uc.mem_map(0x40000000, 0x02400000)                 # image + BSS jusqu'à 0x423380b0
    uc.mem_map(E.PAYLOAD_DST, max(0x00100000, (len(payload) + 0xfffff) & ~0xfffff))   # charge utile et variables
    uc.mem_map(0x80000000, 0x00010000)                 # SRAM, telle que 0x4000045c la laisse
    uc.mem_map(0x90000000, 0x00020000)
    uc.mem_write(E.BASE, os_img)
    sram = bytearray(0x10000)
    sram[0:0x74c0] = os_img[0x4019b590 - E.BASE:0x401a2a50 - E.BASE]
    sram[0x8000:0x8000 + 0x76f0] = os_img[0x401a2a50 - E.BASE:0x401aa140 - E.BASE]
    uc.mem_write(0x80000000, bytes(sram))
    uc.mem_write(E.STOP, b"\x4e\x71\x4e\x71")
    sp = 0x90010000
    uc.mem_write(sp, struct.pack(">I", E.STOP))
    uc.reg_write(mk.UC_M68K_REG_A7, sp)
    uc.emu_start(0x400004b2, E.STOP, count=20_000_000)
    copied = bytes(uc.mem_read(E.PAYLOAD_DST, len(payload))) == payload
    src = E.BASE + E.IMAGE_LEN
    cleared = not any(uc.mem_read(src, len(payload))) and not any(uc.mem_read(0x42338000, 0xb0))
    back = uc.reg_read(mk.UC_M68K_REG_A7) == sp + 4
    want = bytearray(sram)
    in_sram = not 0x80000000 <= struct.unpack_from(">I", os_img, 0x40118594 - E.BASE)[0] < 0x80010000
    if in_sram:
        for stage, run, n in E.SRAM_BANKS:
            want[run - 0x80000000:run - 0x80000000 + n] = payload[stage - E.PAYLOAD_DST:stage - E.PAYLOAD_DST + n]
    sram_ok = bytes(uc.mem_read(0x80000000, 0x10000)) == bytes(want)
    ok = copied and cleared and back and sram_ok
    print(f"  {'ok   ' if ok else 'ECHEC'} crochet de démarrage : charge utile recopiée {'intacte' if copied else 'FAUSSE'},"
          f" BSS remis à zéro {'oui' if cleared else 'NON'}, retour {'normal' if back else 'ANORMAL'}, SRAM "
          + (f"{'avec' if sram_ok else 'SANS'} le code et les voix du Syntakt en "
             f"{', '.join(f'{r:#x} ({n} o)' for _, r, n in E.SRAM_BANKS)}, intacte ailleurs" if in_sram
             else f"{'intacte' if sram_ok else 'MODIFIÉE'}"), flush=True)
    return ok


def bootstrap_depack_ok(cycles_syx, tweak, syntakt_path):
    """Au démarrage, c'est le décompresseur aPLib du BOOTSTRAP du Cycles (section 2, 0x800006bc, appelé par
    le chargeur 0x80000850 avec la section lue en flash à 0x40200000) qui décompresse l'OS vers 0x40000400,
    et non mtlib. On l'exécute pour de vrai sur la section 3 agrandie, recompressée comme build.py. tweak : un tweak,
    ou une liste (version combinée avec Model-TG)."""
    import struct
    import aplib_grow
    from build import unwrap, container, aplib
    from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_MEM_UNMAPPED
    from unicorn import m68k_const as mk
    stream, _ = unwrap(pathlib.Path(cycles_syx).read_bytes())
    c = container.parse(stream)
    sec = {x["id"]: c["blob"][x["off"]:x["off"] + x["size"]] for x in c["sections"]}
    boot = aplib.depack(sec[2])[0]                       # section 2 : bootstrap, exécuté à 0x800003fc
    stock, ops = aplib.depack(sec[3])
    tweaks = tweak if isinstance(tweak, list) else [tweak]
    patched, dirty = build.apply_writes(stock, tweaks)
    payload, _ = build.build_payload(tweaks, stock, syntakt_path)
    want = bytes(patched) + payload
    comp = aplib_grow.repack_grow(want, ops, dirty + bytearray(b"\x01") * len(payload), len(stock))
    STAGE, DEST, STOP, SP = 0x40200000, 0x40000400, 0x8001f000, 0x8001e000
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
    uc.mem_map(0x80000000, 0x20000)
    uc.mem_write(0x800003fc, boot)
    uc.mem_map(0x40000000, 0x00400000)
    uc.mem_write(STAGE, comp)
    uc.mem_write(STOP, b"\x4e\x71\x4e\x71")
    uc.mem_write(SP, struct.pack(">III", STOP, STAGE, DEST))
    uc.reg_write(mk.UC_M68K_REG_A7, SP)
    bad = []
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, size, v, d: bad.append(addr) or False)
    uc.emu_start(0x800006bc, STOP, count=400_000_000)
    same = bytes(uc.mem_read(DEST, len(want))) == want
    tail = not any(uc.mem_read(DEST + len(want), 64))
    fits = DEST + len(want) <= STAGE                     # l'OS décompressé ne doit pas atteindre la zone de transit
    ok = same and tail and fits and not bad and uc.reg_read(mk.UC_M68K_REG_D0) == len(want)
    print(f"  {'ok   ' if ok else 'ECHEC'} décompresseur du bootstrap : OS agrandi relu {'à l' + chr(39) + 'identique' if same else 'DIFFÉREMMENT'}"
          f" ({len(comp)} -> {len(want)} o, fin {DEST + len(want):#x} < {STAGE:#x} : {'oui' if fits else 'NON'})", flush=True)
    return ok


def idle_is_safe(os_img):
    """Tant qu'aucune piste SNARE n'est déclenchée (démarrage, séquenceur arrêté), aucune instruction du code
    du Syntakt ne doit s'exécuter : si ce code posait problème, le Cycles démarrerait quand même."""
    from unicorn import UC_HOOK_CODE
    e = E.Engine(os_img)
    e.solo(0)
    e.set(0, machine="SNARE", note=60, pitch=64, finetune=64, color=0, shape=110, sweep=74, contour=80, decay=33)
    ran = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: ran.append(a), begin=E.PAYLOAD_CODE[0][0], end=E.PAYLOAD_CODE[0][1])
    x = e.render(50, trig_at=())
    ok = not ran and not x.any() and not e.unmapped
    print(f"  {'ok   ' if ok else 'ECHEC'} au repos (50 blocs sans déclenchement) : {len(ran)} instructions du Syntakt"
          f" exécutées, sortie {'muette' if not x.any() else 'NON muette'}", flush=True)
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", required=True, help="Syntakt_OS1.42.syx (ou 1.41) officiel")
    ap.add_argument("--blocks", type=int, default=200, help="blocs de 32 trames par cas")
    ap.add_argument("--cases", help="numéros des cas à jouer (défaut : tous)")
    args = ap.parse_args()

    tweak = json.loads(TWEAK.read_text(encoding="utf-8"))
    stock = T.main_os_from_syx(args.cycles)
    patched, _ = build.apply_writes(stock, [tweak])
    payload, _ = build.build_payload([tweak], stock, args.syntakt)
    os_img = patched + payload
    img = syntakt.dsp_image(args.syntakt)

    fail = (0 if bootstrap_depack_ok(args.cycles, tweak, args.syntakt) else 1)
    fail += (0 if boot_hook_ok(os_img, payload) else 1) + (0 if idle_is_safe(os_img) else 1)
    picks = [int(k) for k in args.cases.split(",")] if args.cases else range(len(CASES))
    for k in picks:
        name, over = CASES[k]
        kw = dict(DEF)
        kw.update(over)
        note = kw.pop("note", 60)
        a = render_syntakt(img, args.blocks, note, kw)
        b = render_cycles(os_img, args.blocks, note, kw) * 2
        diff = np.abs(a - b)
        loud = np.max(np.abs(a))
        ok = loud > 1e6 and diff.max() <= 2
        fail += not ok
        print(f"  {'ok   ' if ok else 'ECHEC'} {name:9} : crête {loud:.3g}, écart max {diff.max():.0f} LSB, "
              f"{np.count_nonzero(diff > 2)} échantillons différents sur {len(a)}", flush=True)
    print("\nIDENTIQUE au Syntakt" if not fail else f"\n{fail} cas différents")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
