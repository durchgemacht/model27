#!/usr/bin/env python3
"""Fabrique une image ELE3 synthetique + les .syx modifies attendus (via le
pipeline Python de reference), pour tester le port JS docs/flasher/builder.js."""
import hashlib, json, pathlib, sys, hmac
sys.path.insert(0, "tools")
import build                                   # tools/build.py (rend mtlib importable)
from mtlib import aplib, container
from mtlib.syx import wrap, unwrap, BYTES_PER_MSG

OUT = pathlib.Path(sys.argv[1])
BASE = 0x40000400
SECT_LEN = 1744192
DEV = json.loads(pathlib.Path("tweaks/model-cycles_OS1.13/device.json").read_text())
TWEAKS = {}
for f in ("01-latching-mute", "02-trig-preview", "03-browser-scroll",
          "10-6ch-multiout", "11-6ch-usbup", "20-sdvintage-snare", "49-control-all-config"):
    TWEAKS[f] = json.loads(pathlib.Path(f"tweaks/model-cycles_OS1.13/{f}.json").read_text())
BY_ID = {t["id"]: t for t in TWEAKS.values()}
COMBOS = [["6ch-multiout"], ["6ch-usbup"], ["sdvintage-snare"], ["6ch-usbup", "sdvintage-snare"],
          ["latching-mute", "trig-preview", "browser-scroll"],
          ["6ch-usbup", "latching-mute", "trig-preview", "browser-scroll"],
          ["control-all-config"]]          # model27's card without payload: the smoke test's build on this image
KNOWN = DEV["cave_refs_ok"]

# --- 1. MAIN OS synthetique -------------------------------------------------
main = bytearray((i * 37 + 11) & 0xFF for i in range(SECT_LEN))   # remplissage deterministe

# masques 0xFF de sprites (comme dans l'image reelle, tools/sprites.py), bordes de non-0xFF
import sprites                                   # noqa: E402
for va, (size, *more) in list(sprites.MASKS.items()) + [(sprites.SHARED_MASK, (1040, 0, ""))]:
    if len(more) > 2:                            # masques 47x47 partagés : pas à 0xFF
        continue
    o = va - BASE
    main[o - 1] = 0x4E
    main[o:o + size] = b"\xff" * size
    main[o + size] = 0x4E

# table caractere -> glyphe de la police de chiffres (comme dans l'image reelle) : 74 o a 0xFF
# pointes par la constante 0x40148564 (reference verifiee a la main, device.json « cave_refs_ok »)
FONT_MAP, FONT_REF = 0x401485ee, 0x40148564
main[FONT_REF - BASE:FONT_REF - BASE + 4] = FONT_MAP.to_bytes(4, "big")
main[FONT_MAP - BASE - 1] = 0x00
main[FONT_MAP - BASE:FONT_MAP - BASE + 74] = b"\xff" * 74
main[FONT_MAP - BASE + 74] = 0x00

# octets 'old' de chaque tweak, a leur offset
for t in TWEAKS.values():
    for w in t["writes"]:
        old = bytes.fromhex(w["old"])
        main[w["off"]:w["off"] + len(old)] = old

# materiel de cle HMAC : ancre + chaine + \0 + constante 32 o, dans une zone libre
key_off = 0x800
s = b"REVERB SEND"
const = bytes((i * 7 + 3) & 0xFF for i in range(32))
material = container.KEY_ANCHOR + s + b"\0" + const
main[key_off:key_off + len(material)] = material
h = hashlib.sha256(s).digest(); hr = hashlib.sha256(s[::-1]).digest()
key = bytes(a ^ b ^ c for a, b, c in zip(h, hr, const))

main = bytes(main)

# --- 2. section 3 compressee ----------------------------------------------------
# The first LIT bytes as literals, the rest packed: a .syx of about 1.1 MB (8,900 packets), the size of a real build.
# All literals made a 2.5 MB .syx (19,400 packets), more than the 16,384 packet numbers builder.js wrap() allows.
import aplib_grow                                # noqa: E402
LIT = 800000
_, tail_ops = aplib.depack(bytes(aplib.SECT_HDR) + aplib_grow.pack(main[LIT:]))
ops = [(aplib.LITERAL, i, 0, 1) for i in range(LIT)] + [(k, p + LIT, o, n) for k, p, o, n in tail_ops]
s3 = aplib.repack(main, ops, bytearray(len(main)))
assert aplib.depack(s3)[0] == main, "aller-retour aplib synthetique"

# --- 3. blob ELE3 (1 section, id 3), mise en page comme container.rebuild ----
TABLE_OFF, ENTRY_SZ, ALIGN, DIGEST = 0x20, 16, 16, 32
first = TABLE_OFF + ENTRY_SZ                    # 0x30
off3 = (first + ALIGN - 1) & ~(ALIGN - 1)
blob = bytearray(off3 + len(s3))
blob[0:4] = b"ELE3"
blob[8:16] = b"1.13\0\0\0\0"
blob[0x1c:0x20] = (1).to_bytes(4, "big")        # count
blob[0x20:0x24] = (3).to_bytes(4, "big")        # id
blob[0x24:0x28] = off3.to_bytes(4, "big")       # off
blob[0x28:0x2c] = len(s3).to_bytes(4, "big")    # size
blob[0x2c:0x30] = (0).to_bytes(4, "big")        # attr
blob[off3:off3 + len(s3)] = s3
end = off3 + len(s3)
hmac_off = (end + 4 + ALIGN - 1) & ~(ALIGN - 1)
blob += b"\0" * (hmac_off + DIGEST - len(blob))
digest = hmac.new(key, bytes(blob[:hmac_off]), hashlib.sha256).digest()
blob[hmac_off:hmac_off + DIGEST] = digest
blob = bytes(blob)

stream = container.build_stream(blob, BYTES_PER_MSG)
raw = wrap(stream, 0x11, start_seq=114)
OUT.joinpath("synth.syx").write_bytes(raw)

meta = {"section_sha256": hashlib.sha256(main).hexdigest(), "device": DEV["device"], "os": DEV["os"]}

# --- 4. sorties attendues via le pipeline Python de reference ---------------
def ref_build(raw, tweaks):
    stream, info = unwrap(raw)
    c = container.parse(stream)
    sec3 = next(s for s in c["sections"] if s["id"] == 3)
    m, ops = aplib.depack(c["blob"][sec3["off"]:sec3["off"] + sec3["size"]])
    build.check_conflicts(tweaks)
    patched, dirty = build.apply_writes(m, tweaks)
    build.check_caves(m, tweaks, False, dirty, patched, KNOWN)   # doit passer sans --force-cave
    new_s3 = aplib.repack(patched, ops, dirty)
    msg = c["blob"][:len(c["blob"]) - container.DIGEST_LEN]
    expect = c["blob"][len(c["blob"]) - container.DIGEST_LEN:]
    plain = []
    for sx in c["sections"]:
        try: plain.append(aplib.depack(c["blob"][sx["off"]:sx["off"] + sx["size"]])[0])
        except Exception: pass
    k = container.find_key(plain, msg, expect)
    assert k == key, "find_key doit retrouver la meme cle"
    nb = container.rebuild(c, {3: new_s3}, k)
    out = wrap(container.build_stream(nb, BYTES_PER_MSG), info["product"], info["start_seq"])
    return out, hashlib.sha256(patched).hexdigest()

meta["expect"] = {}
for ids in COMBOS:
    combo = "+".join(ids)
    out, sha = ref_build(raw, [BY_ID[i] for i in ids])
    OUT.joinpath(f"expect_{combo}.syx").write_bytes(out)
    meta["expect"][combo] = {"ids": ids, "sha_mainos": sha, "bytes": len(out)}

# --- 5. regle des caves, partagee avec builder.js -----------------------------
# ecrire dans un masque encore reference -> refus ; avec la redirection du sprite -> accepte
zone = 0x4016cae8
refuse = {"id": "cave-refusee", "writes": [{"off": zone - BASE, "old": "ffff", "new": "4e71"}]}
accept = {"id": "cave-acceptee", "writes": refuse["writes"] + [sprites.redirect_write(zone)]}
same = dict(sprites.redirect_write(zone))
same["new"] = same["old"]                        # « reecriture » qui garde le pointeur : doit rester bloquante
noop = {"id": "cave-reecriture-vide", "writes": refuse["writes"] + [same]}
for t, verdict in ((refuse, "refuse"), (noop, "refuse"), (accept, "accepte")):
    patched, dirty = build.apply_writes(main, [t])
    try:
        build.check_caves(main, [t], False, dirty, patched)
        got = "accepte"
    except SystemExit:
        got = "refuse"
    if got != verdict:
        raise SystemExit(f"!! check_caves : {t['id']} {got}, attendu {verdict}")
meta["cave_rule"] = {"refuse": refuse, "noop": noop, "accept": accept}

# reference connue : ecrire dans sa partie libre [lo, hi) -> accepte ; deborder -> refuse ;
# sans la liste des references connues -> refuse
inside = {"id": "connue-dedans", "writes": [{"off": 0x401485f0 - BASE, "old": "ffff", "new": "4e71"}]}
outside = {"id": "connue-dehors", "writes": [{"off": 0x40148630 - BASE, "old": "ffff", "new": "4e71"}]}
for t, known, verdict in ((inside, KNOWN, "accepte"), (outside, KNOWN, "refuse"), (inside, None, "refuse")):
    patched, dirty = build.apply_writes(main, [t])
    try:
        build.check_caves(main, [t], False, dirty, patched, known)
        got = "accepte"
    except SystemExit:
        got = "refuse"
    if got != verdict:
        raise SystemExit(f"!! check_caves (reference connue) : {t['id']} {got}, attendu {verdict}")
meta["known_rule"] = {"inside": inside, "outside": outside}
meta["cave_refs_ok"] = KNOWN

# --- 6. charge utile compressée (append.compress = "aplib", notes/50) : même flux que aplib_grow.pack ----------------
import aplib_grow                                # noqa: E402
import random                                    # noqa: E402
rnd = random.Random(50)                          # littéraux, décalages lointains (> 3 328), longues répétitions
blk = bytes(rnd.getrandbits(8) for _ in range(5000))
data = (bytes(40000) + blk + bytes(rnd.choice(b"ab\0") for _ in range(20000)) + blk[:3] + blk + bytes(70000) + blk
        + b"".join(bytes([rnd.getrandbits(8)]) * rnd.randint(1, 300) for _ in range(500)) + main[:30000])
OUT.joinpath("aplib_in.bin").write_bytes(data)
OUT.joinpath("aplib_out.bin").write_bytes(aplib_grow.pack(data))
if aplib.depack(bytes(aplib.SECT_HDR) + aplib_grow.pack(data))[0] != data:
    raise SystemExit("!! aplib_grow.pack : relecture différente")

OUT.joinpath("meta.json").write_text(json.dumps(meta))
print("synth.syx", len(raw), "o ; section3 sha", meta["section_sha256"][:16],
      "; builds", list(meta["expect"]), "; regle des caves OK (Python)")
