#!/usr/bin/env python3
"""Probe W1 of CHORD Tables (notes/66 §2.1, §7): what CHORD's wave setup can read at a trig, on the OS's own code.
Nothing is patched: every part runs the official MAIN OS 1.13.

  1. The sites the plan relies on, in the user's MAIN OS: `jsr 0x400a8080` at 0x400ab15e and no other call of it;
     the selector's table 0x40118590; the sound copy of 0x40058a0a into 0x800015ae + 66 t, and CUR_SNDS at
     0x800015a0 + (147 + t) * 4.
  2. The voice loop (0x400a7d4a, mcengine): three CHORD tracks next to KICK, SNARE and TONE, trigs at chosen blocks.
     The voice loop looks at a track's machine only in a block with v + 0x38 set, and then resets the voice, which
     clears v + 0x34 (notes/66 §11.6). So at the entry of 0x400a8080: no call in the block of the first trig; from
     the next block on, the machine change, one call per block for each CHORD track and for no other, from
     0x400ab164, with v = 0x42308828 + t * 0x31c and p = params + 14 + 66 t; in the change's block v + 0x34 clear
     (a trig there is lost) and v + 0x38 set; later v + 0x34 set exactly in the trig blocks and v + 0x38 exactly in
     the block after; p + 0x3c is k 30 as written.
  3. The event loop of the audio interrupt (0x40058d46..0x400591e4, test_arp.Audio), notes entering by 0x4005894a as
     from the interface:
     a. a note on a CHORD track whose sound is new to the track: the targets 0x800015ae + 66 t get the sound's 66
        bytes (k 30 at +60), CUR_SNDS[t] the sound;
     b. k 30 changed in the sound object, then a note with the same sound: CUR_SNDS[t] stays; the targets' k 30 is
        reported (a finding: stale or not);
     c. a preview note (the event's +52, as the browser sends it): after the loop CUR_SNDS[t] = 0 and the targets hold
        the preview sound's 66 bytes;
     d. a normal note after it: the kit sound is copied again.

Lines marked "finding" are facts for the design (notes/66 §2.1), not failures. Exits non-zero on a FAIL.

Needs Unicorn and numpy (pip install unicorn numpy); Unicorn's JIT does not run inside a sandbox that forbids it:
run it in a normal terminal. A few seconds.

    python3 tools/emu/probe_chord_tables.py --cycles model-cycles_OS1.13.syx
"""
import argparse
import pathlib
import struct
import sys

from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import mcengine as E                # noqa: E402
import test_arp as A                # noqa: E402
import test_model_tg as TM          # noqa: E402
import test_sdvintage as T          # noqa: E402

BASE = E.BASE
SETUP, CALL_AT, RET_AT = 0x400a8080, 0x400ab15e, 0x400ab164
SELECTOR_LEA = 0x400a806c                  # lea 0x40118590,a0 in the selector 0x400a8060
COPY = 0x40058a0a                          # (sound, t): CUR_SNDS[t] = sound, 66 bytes from sound + 20 to the targets
TARGETS, CUR_SNDS = 0x800015ae, 0x800017ec
K30 = 60                                   # k 30 = RETRIG + SWEEP (notes/66 §10), 2 * 30 bytes into the 66
CHORD = 5
FAIL = []


def check(ok, msg):
    print(("ok    " if ok else "FAIL  ") + msg)
    if not ok:
        FAIL.append(msg)


def finding(msg):
    print("finding  " + msg)


def be16s(b, off=0):
    return struct.unpack_from(">h", b, off)[0]


# --- 1. the sites ----------------------------------------------------------------------------------------------------

def site_tests(img):
    at = lambda va, n: bytes(img[va - BASE:va - BASE + n])
    call = bytes.fromhex("4eb9") + struct.pack(">I", SETUP)
    check(at(CALL_AT, 6) == call, f"{CALL_AT:#x}: jsr {SETUP:#x}")
    jumps = []
    for op in ("4eb9", "4ef9"):
        pat, i = bytes.fromhex(op) + struct.pack(">I", SETUP), -1
        while (i := img.find(pat, i + 1)) >= 0:
            if i % 2 == 0:
                jumps.append(i)
    check(jumps == [CALL_AT - BASE], f"no other jsr or jmp to {SETUP:#x} in the image "
          f"({', '.join(hex(BASE + i) for i in jumps)})")
    check(at(SELECTOR_LEA, 6) == bytes.fromhex("41f940118590"), f"{SELECTOR_LEA:#x}: lea 0x40118590 (the selector's table)")
    check(at(0x40058a18, 6) == bytes.fromhex("41f9800015a0") and at(0x40058a1e, 6) == bytes.fromhex("068000000093")
          and at(0x40058a40, 6) == bytes.fromhex("0680800015ae") and at(0x40058a32, 4) == bytes.fromhex("48780042"),
          f"{COPY:#x}: CUR_SNDS[t] at 0x800015a0 + (147 + t) * 4, 66 bytes to 0x800015ae + 66 t")


# --- 2. the voice loop -----------------------------------------------------------------------------------------------

CHORD_TRACKS = {0: 0x0300, 2: 0x1100, 5: 0x4000}      # track -> k 30 (3, 17, 64)
OTHERS = {1: "KICK", 3: "SNARE", 4: "TONE"}
# block -> trig mask. Block 0: the first trig of every track, so block 1 is the machine change (0x400a7d4a looks at
# the machine only when v + 0x38 is set, then resets the voice, which clears v + 0x34); track 2's trig in block 1
# falls into that reset. Then trigs on a playing CHORD voice, two of them in consecutive blocks (track 5, 30 and 31).
PLAN = {0: 0b111111, 1: 0b000100, 10: 0b000001, 20: 0b100001, 21: 0b000100, 30: 0b100000, 31: 0b100000}
BLOCKS = 40


def voice_tests(img):
    e = TM.engine(img)
    uc = e.uc
    for t, m in OTHERS.items():
        e.machine_defaults(t, m)
    for t in CHORD_TRACKS:
        e.machine_defaults(t, "CHORD")
    for t in range(6):
        e.set(t, note=60, pitch=64)
    for t, k in CHORD_TRACKS.items():
        uc.mem_write(E.PARAMS + 0xe + 0x42 * t + K30, struct.pack(">h", k))
    calls, block = [], [0]
    r32 = lambda a: struct.unpack(">I", uc.mem_read(a, 4))[0]

    def hook(uc_, addr, size, ud):
        sp = uc_.reg_read(mk.UC_M68K_REG_A7)
        ret, v, p = struct.unpack(">III", uc_.mem_read(sp, 12))
        calls.append(dict(block=block[0], ret=ret, v=v, p=p, f34=r32(v + 0x34), f38=r32(v + 0x38),
                          k30=be16s(bytes(uc_.mem_read(p + K30, 2)))))
    uc.hook_add(UC_HOOK_CODE, hook, begin=SETUP, end=SETUP)
    for b in range(BLOCKS):
        block[0] = b
        e.block(PLAN.get(b, 0))
    check(not e.unmapped, f"{BLOCKS} blocks without an unmapped access ({e.unmapped[:3]})")
    by = {}
    for c in calls:
        t = (c["v"] - E.VOICE0) // E.VSTRIDE
        by.setdefault((c["block"], t), []).append(c)
    tracks = sorted({t for _b, t in by})
    check(tracks == sorted(CHORD_TRACKS), f"called for the CHORD tracks only: {tracks}")
    check(not any((0, t) in by for t in CHORD_TRACKS),
          "block 0, the first trig: no call (the voice still runs the machine it had)")
    check(all(len(by.get((b, t), [])) == 1 for b in range(1, BLOCKS) for t in CHORD_TRACKS),
          f"from block 1 on, once per block and CHORD track ({len(calls)} calls for {BLOCKS - 1} blocks x "
          f"{len(CHORD_TRACKS)} tracks)")
    check(all(c["ret"] == RET_AT for c in calls), f"always from {RET_AT:#x}, the call at {CALL_AT:#x}")
    check(all(c["v"] == E.VOICE0 + t * E.VSTRIDE and c["p"] == E.PARAMS + 0xe + 0x42 * t
              for (b, t), cs in by.items() for c in cs),
          "v = 0x42308828 + t * 0x31c, p = the voice loop's params + 14 + 66 t")
    trig = lambda b, t: bool(PLAN.get(b, 0) >> t & 1)
    first = {t: by[(1, t)][0] for t in CHORD_TRACKS if (1, t) in by}
    check(len(first) == len(CHORD_TRACKS) and all(not c["f34"] and c["f38"] for c in first.values()),
          "block 1, the machine change: v + 0x34 clear (track 2's trig of that block too: the reset clears it), "
          "v + 0x38 set")
    f34 = sorted((b, t) for (b, t), cs in by.items() if b >= 2 and cs[0]["f34"])
    check(f34 == sorted((b, t) for b in range(2, BLOCKS) for t in CHORD_TRACKS if trig(b, t)),
          f"later, v + 0x34 set exactly in the trig blocks: {f34}")
    f38 = sorted((b, t) for (b, t), cs in by.items() if b >= 2 and cs[0]["f38"])
    check(f38 == sorted((b, t) for b in range(3, BLOCKS) for t in CHORD_TRACKS if trig(b - 1, t)),
          f"later, v + 0x38 set exactly in the block after each trig: {f38}")
    finding("the block in which a note starts on CHORD is the one with v + 0x38 set: the block after the trig, or "
            "the machine change; a trig in the change's own block is lost to the reset")
    check(all(cs[0]["k30"] == CHORD_TRACKS[t] for (b, t), cs in by.items()),
          "p + 0x3c is k 30 as written (3, 17, 64 as 8.8)")


# --- 3. the event loop -----------------------------------------------------------------------------------------------

def sound(k30, seed):
    """100 bytes: a CHORD sound whose parameter words k 0..32 (at +20 + 2 k) are distinct, with k 30 = k30."""
    s = bytearray(100)
    for k in range(33):
        struct.pack_into(">H", s, 20 + 2 * k, (seed * 0x0101 + k * 0x0203) & 0x7fff)
    struct.pack_into(">H", s, 20 + 2 * 9, CHORD << 8)          # the machine, byte +38
    struct.pack_into(">h", s, 20 + K30, k30)
    return bytes(s)


def note(a, t, n, preview=0):
    """test_arp.Audio.send's note-on message, with the event's +52 = the preview sound (0: none)."""
    m = [0] * 14
    m[0], m[1], m[2], m[3], m[5], m[8] = t, n, 100, 1, 0xffffffff, 0x40
    m[4], m[9], m[10], m[13] = 0x38081, 9, 127, preview
    a.uc.mem_write(A.MSG, struct.pack(">14I", *[x & 0xffffffff for x in m]))
    a.w32(0x8000184c, a.now)
    a.e.call(0x4005894a, A.MSG)


def event_tests(img):
    a = A.Audio(img)
    uc = a.uc
    uc.mem_map(0, 0x1000)                 # the OS reads *(0 + 96) after a preview note (0x40059160, notes/46 §2)
    t = 2
    kit = A.KIT + 28 + 100 * t
    pv = 0x4e500000
    uc.mem_write(kit, sound(0x0300, 0x21))
    uc.mem_write(pv, sound(0x0700, 0x35))
    a.w32(CUR_SNDS + 4 * t, 0)
    tg = lambda: bytes(uc.mem_read(TARGETS + 66 * t, 66))
    cur = lambda: a.r32(CUR_SNDS + 4 * t)
    # a. a new sound
    note(a, t, 60)
    mask = a.run()
    check(mask is not None and mask >> t & 1, f"a. note on track {t}: the loop ends, the track is triggered")
    check(cur() == kit and tg() == bytes(uc.mem_read(kit + 20, 66)) and be16s(tg(), K30) == 0x0300,
          f"a. new sound: CUR_SNDS[{t}] = the kit sound ({cur():#x}), the targets = its 66 bytes, k 30 = 0x0300")
    # b. the same sound, k 30 changed in the sound object
    a.send(2, t, 60)
    a.run()
    uc.mem_write(kit + 20 + K30, struct.pack(">h", 0x0500))
    note(a, t, 62)
    mask = a.run()
    check(mask is not None and mask >> t & 1 and cur() == kit, f"b. same sound: triggered, CUR_SNDS[{t}] stays")
    k_t, k_s = be16s(tg(), K30), be16s(bytes(uc.mem_read(cur() + 20 + K30, 2)))
    finding(f"b. after k 30 changed in the sound object without a new sound: targets k 30 = {k_t:#06x}, "
            f"sound object (CUR_SNDS[{t}] + 80) = {k_s:#06x}: "
            + ("the targets are stale, read the sound object" if k_t != k_s else "the targets follow the sound object"))
    # c. a preview note
    a.send(2, t, 62)
    a.run()
    note(a, t, 64, preview=pv)
    mask = a.run()
    check(mask is not None and mask >> t & 1, "c. preview note: triggered")
    check(cur() == 0 and tg() == bytes(uc.mem_read(pv + 20, 66)) and be16s(tg(), K30) == 0x0700,
          f"c. preview note: CUR_SNDS[{t}] = 0 after the loop ({cur():#x}), the targets = the preview sound, "
          "k 30 = 0x0700")
    # d. a normal note after it
    a.send(2, t, 64)
    a.run()
    note(a, t, 65)
    mask = a.run()
    check(mask is not None and mask >> t & 1 and cur() == kit and be16s(tg(), K30) == 0x0500,
          f"d. normal note after the preview: CUR_SNDS[{t}] = the kit sound again, targets k 30 = 0x0500")
    check(not a.e.unmapped, f"event loop without an unmapped access ({a.e.unmapped[:3]})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="the official model-cycles_OS1.13.syx")
    args = ap.parse_args()
    img = T.main_os_from_syx(args.cycles)
    print("1. sites")
    site_tests(img)
    print("2. voice loop")
    voice_tests(img)
    print("3. event loop")
    event_tests(img)
    print("ALL OK" if not FAIL else f"{len(FAIL)} FAIL")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
