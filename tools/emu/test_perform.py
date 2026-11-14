#!/usr/bin/env python3
"""Proof of Perform Kit, steps P1 to P3 (tools/machines/perform/, notes/81): the switch, the pattern change and what is saved, on the OS's own code, the stock OS
and the build side by side.

  1. the build, alone, with RESAMPLE and with the offered cards: the fifteen writes (fourteen with RESAMPLE, which holds the
     key code accessor), each over its stock bytes; pk_held the part's own byte or RESAMPLE's set_held; the data block
     zero; every other write and the payload before the part's code as in the build without it; the tweaks that write
     at its sites among the conflicts;
  2. the sequencer's four writes of the playing kit (0x40054d6a, 0x40055510, 0x4005571e, 0x40055c62), each run as the
     one instruction it is, with every register set: 0x40a78888, the registers, the condition codes and the stack as
     the stock instruction leaves them; with the mode off no kit and no byte of the data block changes; with it on
     the kits and the state follow the model of perform.c (a change, the same kit again, a pointer that is no kit, a
     second change before the interface ran); the instructions a change costs, counted;
  3. the interface's kit selection (0x4000f36a), the real function with its calls stubbed: the same calls with the
     same arguments and the same answer as on the stock OS, bound to the playing pattern or to another; with a
     pattern still to give back, the kits after it follow the model; the stack and d2-d7/a2-a6 kept;
  4. SETTINGS + PATTERN at PatternGridView's PATTERN case (0x40020ad0): without SETTINGS the instruction replaced and
     nothing else (a3, the stack, the registers); with SETTINGS held PATTERN's press switches the mode on and ends
     the handler as handled (d3 = 1 at its epilogue 0x400212c6, the stack as at the case's start), its repeat and
     its release are taken without a second switch; again: off, the active pattern's own bytes back, the audio
     side's call (0x4005950e with the playing kit) and the kit's change notice (0x400d1f98(project + 116, n, 0));
     SETTINGS by its last event alone (pk_held) is enough;
  5. the key code accessor (0x4007240c): the code as the stock accessor returns it; in the build without RESAMPLE
     SETTINGS' events set and clear the part's held byte, another key leaves it.
  6. the start of the kit serializer (0x4005b2ae), its two first instructions: the stack, the saved registers and the
     arguments as on the stock OS, but the kit, which for the active pattern and for the pattern left is a copy
     with the pattern's own bytes in 0..693 and the pool as it is; the kit itself for every other, and with the mode
     off; the instructions the copy costs, counted;
  7. the kit's save to a slot (0x400100ba): into the serializer with the stack and the registers of the stock call,
     the kit itself; Save Pattern makes the tweaked bytes the pattern's own, a temp save notes the pattern;
  8. the kit's load from a slot (0x400107a4), the loader stubbed: called once with the same arguments, its answer
     back, the stack and the registers kept; Reload Pattern makes the loaded bytes the pattern's own, a temp reload,
     a failed load and another pattern do not;
  9. the project replaced (0x4000eb12) and the starts of pattern paste and clear (0x40010c7a, 0x4001190c,
     0x40011a7e): the frame, the stack and the registers as the stock instructions leave them; another project
     drops the mode and writes no kit; paste and clear switch it off first: the own bytes back, the audio side and
     the interface told, the temp-saved patterns' kits saved to the temp slot again.
  10. the popup: with the views up, the switch builds the OS's popup as RESAMPLE's save does: the string of "Perform
     Kit ON" or "Perform Kit OFF", 0x9c bytes, the popup's constructor on them, the holder (0x400fbf40, 1, 1, the
     popup), presented on the views' target, the reference and the string dropped; before the views are up, none.
  11. the mark on the main screen, through MainScreenView's draw slot (0x400ffe30): the draw behind it called once
     with the same arguments, as the stock slot calls the stock draw; the stack and d2-d7/a2-a6 kept; the view kept;
     with the mode on and no value window the two leftmost columns of the bitmap hold the checkerboard (0xaaaaaaaa,
     0x55555555), every other word as the draw behind left it; with the mode off or a value window open no word
     changes; a switch asks the kept view for a redraw. Section 1 also composes the part with SAMPLE (its own main
     draw behind the mark) and with SAMPLE and REF2 (the dispatcher behind it).

Unicorn's JIT stops with SIGILL in a sandbox that forbids generated code: run it in a normal terminal.

    python3 tools/emu/test_perform.py --cycles model-cycles_OS1.13.syx
    python3 tools/emu/test_perform.py --cycles model-cycles_OS1.13.syx --dry      # section 1 only, without Unicorn
"""
import argparse
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import compose                      # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
from test_sdvintage_7th import check  # noqa: E402

PART = compose.load_part("perform")
DATA, SITES = PART["data"], PART["sites"]
OFFERED = ["sampler", "digidelay", "pots", "smpfilter", "crush", "ring", "reso", "eq"]
SELECTIONS = [("perform", [], {}), ("resample+perform", [], {"resample": True}),
              ("sampler+perform", ["sampler"], {}), ("sampler+refmachine2+perform", ["sampler", "refmachine2"], {}),
              ("offered+cpu+resample+transpose+perform", OFFERED, {"cpu": True, "resample": True, "transpose": True})]
BOOT_SITES = {0x400004b2, 0x400b1106, 0x4016cae8}   # the payload's boot: the hook, the stub's mask and its sprite
KITS, KIT_SIZE, HEAD, NKITS = 0x409c9c80, 7094, 694, 96
PLAYING_KIT, PENDING_KIT = 0x40a78888, 0x40a7888c
SEQ_SITES = {"seq_queued": "d0", "seq_stop": "fp", "seq_chain": "fp", "seq_set": "d2"}
KIT_SELECT, BIND, SEQ_STATE, CURRENT = 0x4000f36a, 0x40009a1e, 0x400cfd0e, 0x4006a96c
PAT_CASE, PAT_NEXT, EPILOGUE, UI_STATE = 0x40020ad0, 0x40020ad6, 0x400212c6, 0x400cf9a8
PROJECT, KIT_CHANGED, AUDIO_KIT, PLAY_KIT, ACCESSOR = 0x400cf866, 0x400d1f98, 0x4005950e, 0x800017e4, 0x4007240c
SERIALIZER, SER_NEXT, KSAVE_SITE, KLOAD_SITE, KLOAD_NEXT, LOADER = 0x4005b2ae, 0x4005b2b6, 0x400100ba, 0x400107a4, 0x400107aa, 0x4005d080
TEMP_KIT_SAVE, DROP_SITE, DROP_NEXT = 0x4001002c, 0x4000eb12, 0x4000eb18
OFF_SITES = {"paste": (0x40010c7a, 0x40010c82), "cut": (0x4001190c, 0x40011914), "clear": (0x40011a7e, 0x40011a86)}
BUF, RET = 0x93e30000, 0x93e40000
VIEWS_UP, STRING, NEW, POPUP, VIEWS, TARGET, PRESENT, DROP, STRING_DROP = (
    0x40fe4178, 0x400f980c, 0x400802e0, 0x400747c0, 0x400d0974, 0x400060d8, 0x4007700e, 0x400cf23c, 0x400f7d5c)
POPUP_HOLDER_VT, VIEWS_OBJ, TARGET_OBJ = 0x400fbf40, 0x93e60000, 0x93e70000
MAIN_SLOT, MAIN_DRAW, VALUE_SHOWN, NEEDS_REDRAW, BITMAP = 0x400ffe30, 0x4001b22a, 0x4006b704, 0x40076082, 0x93e90000
K_PATTERN, K_SETTINGS = 3, 13
OBJ, VT, H_BOUND, PROJ, VIEW, EVENT = 0x93e00000, 0x93e01000, 0x93e02000, 0x93a00000, 0x93e10000, 0x93d10000


def kit(n):
    return KITS + KIT_SIZE * n


def composed(stock, sel, perform, **kw):
    tweak, info = compose.compose(stock, sel, perform=perform, **kw)
    patched, _ = build.apply_writes(stock, [tweak])
    runtime = build.payload_runtime(tweak, stock, None)
    return tweak, info, bytes(patched) + build.payload_image(tweak, runtime), runtime


# --- 1. the build -----------------------------------------------------------------------------------------------------
def build_tests(key, w, wo, resample):
    tweak, info, _img, runtime = w
    pi = info["perform"]
    by = {x["off"] + compose.BASE: x for x in tweak["writes"]}
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    ours = set()
    for name, s in SITES.items():
        va, old = int(s["at"], 16), s["stock"]
        x = by.get(va)
        if resample and s.get("unless") == "resample":
            rs = syms.get("rs_code")
            check(x is not None and rs is not None and x["new"] == f"4ef9{rs:08x}",
                  f"{key}: {va:#x} is RESAMPLE's (jmp rs_code), not written by Perform Kit")
            continue
        ours.add(va)
        new = {"jsr": "4eb9", "jmp": "4ef9"}[s["op"]] + f"{syms[s['symbol']]:08x}"
        new += "4e71" * ((len(old) - len(new)) // 4)
        check(x is not None and x["old"] == old and x["new"] == new,
              f"{key}: {name} {va:#x} {old} -> {s['op']} {s['symbol']} ({syms[s['symbol']]:#x})"
              + (" and a nop" if len(new) > 12 else ""))
    x = by.get(MAIN_SLOT)
    ours.add(MAIN_SLOT)
    check(x is not None and x["old"] == f"{MAIN_DRAW:08x}" and x["new"] == f"{syms['pk_main']:08x}",
          f"{key}: MainScreenView's draw slot {MAIN_SLOT:#x}: {MAIN_DRAW:#x} -> pk_main ({syms['pk_main']:#x})")
    pay = compose.gs.PAY_ALONE
    block = bytearray(runtime[pi["data_at"] - pay:pi["data_at"] - pay + DATA["size"]])
    nxt = struct.unpack_from(">I", block, DATA["next"])[0]
    block[DATA["next"]:DATA["next"] + 4] = bytes(4)
    behind = int(wo[0]["writes"][[w_["off"] + compose.BASE for w_ in wo[0]["writes"]].index(MAIN_SLOT)]["new"], 16) \
        if wo is not None and MAIN_SLOT in [w_["off"] + compose.BASE for w_ in wo[0]["writes"]] else MAIN_DRAW
    check(nxt == behind == pi["main_next"],
          f"{key}: the draw behind the mark ({pi['main_behind']}, {nxt:#x}) is what the build without Perform Kit has "
          "in the slot")
    check(len(block) == DATA["size"] and not any(block) and syms["pk_data"] == pi["data_at"],
          f"{key}: the data block at {pi['data_at']:#x}, {DATA['size']} bytes, zero but for that address")
    if resample:
        want = info["resample"]["data_at"] + compose.load_part("resample")["data"]["set_held"]
        who = "RESAMPLE's set_held"
    else:
        want, who = pi["data_at"] + DATA["held"], "the part's own held byte"
    check(syms["pk_held"] == want == pi["held"], f"{key}: pk_held is {who} ({want:#x})")
    if wo is None:
        others = set(by) - ours
        check(others == BOOT_SITES, f"{key}: nothing else written but the payload's boot ({len(by)} writes; "
                                    f"{sorted(map(hex, others - BOOT_SITES))})")
    else:
        bw = {x["off"] + compose.BASE: x for x in wo[0]["writes"]}
        diff = sorted(a for a in set(by) | set(bw) if by.get(a) != bw.get(a))
        check(set(diff) <= ours | BOOT_SITES and not (ours - {MAIN_SLOT}) & set(bw),
              f"{key}: every other write as in the build without Perform Kit ({len(by)} writes; differing "
              f"{', '.join(map(hex, diff))})")
        n = pi["code_at"] - pay
        check(runtime[:n] == wo[3][:n], f"{key}: the payload as in the build without Perform Kit up to its code "
                                        f"({pi['code_at']:#x})")
    size = {va: len(by[va]["new"]) // 2 for va in ours}
    takers = set()
    for f in compose.DEV.glob("*.json"):
        if f.name == "device.json":
            continue
        t = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(t, dict):
            continue
        for x in t.get("writes", []):
            va, n = x["off"] + compose.BASE, len(x["new"]) // 2
            if any(va < s_ + k and s_ < va + n for s_, k in size.items()) and (va not in by or by[va]["new"] != x["new"]):
                takers.add(t["id"])
    check(takers <= set(tweak["conflicts"]),
          f"{key}: the tweaks that write at its sites are among the conflicts ({len(takers)}: "
          f"{', '.join(sorted(takers)[:5])}{', ...' if len(takers) > 5 else ''})")


# --- the model of perform.c -------------------------------------------------------------------------------------------
class Model:
    def __init__(self, kits):
        self.kits = bytearray(kits)
        self.on = self.home = self.left1 = self.which = self.taken = 0
        self.buf = [bytearray(DATA["buf_bytes"]), bytearray(DATA["buf_bytes"])]
        self.temp = set()
        self.view = self.next = 0
        self.big = bytes(DATA["size"] - DATA["big"])

    def head(self, n):
        return self.kits[KIT_SIZE * n:KIT_SIZE * n + HEAD]

    def put(self, n, b):
        self.kits[KIT_SIZE * n:KIT_SIZE * n + HEAD] = b[:HEAD]

    def give_back(self):
        if self.left1:
            self.put(self.left1 - 1, self.buf[self.which ^ 1])
            self.left1 = 0

    def change(self, ptr):
        if not self.on or ptr < KITS:
            return
        n, r = divmod(ptr - KITS, KIT_SIZE)
        if n >= NKITS or r or n == self.home:
            return
        self.give_back()
        self.buf[self.which ^ 1][:HEAD] = self.head(n)
        self.put(n, self.head(self.home))
        self.left1, self.home = self.home + 1, n
        self.which ^= 1

    def ui(self):
        if self.on and self.left1:
            self.put(self.home, self.head(self.left1 - 1))
            self.give_back()

    def toggle(self, playing):
        """-> the patterns whose kit goes to the temp slot again (mode off)."""
        if not self.on:
            self.buf[self.which][:HEAD] = self.head(playing)
            self.home, self.left1, self.on = playing, 0, 1
            return []
        self.give_back()
        self.put(self.home, self.buf[self.which])
        self.on = 0
        saved, self.temp = sorted(self.temp), set()
        return saved

    def drop(self):
        self.on = self.left1 = 0
        self.temp = set()

    def ser(self, ptr):
        """The bytes the serializer gets for this kit, None: the kit itself."""
        if not self.on:
            return None
        if ptr == kit(self.home):
            own = self.buf[self.which]
        elif self.left1 and ptr == kit(self.left1 - 1):
            own = self.buf[self.which ^ 1]
        else:
            return None
        n = (ptr - KITS) // KIT_SIZE
        return bytes(own[:HEAD]) + bytes(self.kits[KIT_SIZE * n + HEAD:KIT_SIZE * (n + 1)])

    def ksave(self, n, slot):
        if self.on and n < NKITS and n == self.home:
            if slot == 96:
                self.temp.add(n)
            else:
                self.buf[self.which][:HEAD] = self.head(n)

    def loaded(self, n, slot, ok):
        if self.on and ok & 0xff and slot != 96 and n == self.home:
            self.buf[self.which][:HEAD] = self.head(n)

    def block(self, held=0, big=None):
        bits = bytearray(DATA["temp_bytes"])
        for n in self.temp:
            bits[n >> 3] |= 1 << (n & 7)
        return (bytes([self.on, self.home, self.left1, self.which, self.taken, held, 0, 0])
                + bytes(self.buf[0]) + bytes(self.buf[1]) + bytes(bits) + struct.pack(">II", self.view, self.next)
                + (self.big if big is None else big))


def rig(img, runtime=None):
    import test_shortcuts as SH
    u = SH.UI(img, runtime or b"")
    import unicorn.m68k_const as mk
    u.uc.mem_map(0x80000000, 0x10000)                 # the SRAM: the audio side's playing kit
    u.uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)         # supervisor, as the OS runs: the part reads and writes SR
    return u


def pattern_bytes():
    return bytes((i * 2654435761 >> 13) & 0xff for i in range(NKITS * KIT_SIZE))


def load(u, m, da, held=0):
    u.uc.mem_write(KITS, bytes(m.kits))
    if da:
        m.next = u.u32(da + DATA["next"])             # the composer's: the draw behind the mark
        u.uc.mem_write(da, m.block(held))


def state(u, da):
    return bytes(u.uc.mem_read(KITS, NKITS * KIT_SIZE)), (bytes(u.uc.mem_read(da, DATA["size"])) if da else None)


def regs_of():
    import unicorn.m68k_const as mk
    return [getattr(mk, f"UC_M68K_REG_{r}") for r in
            ("D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "A0", "A1", "A2", "A3", "A4", "A5", "A6")]


# --- 2. the sequencer's writes of the playing kit ------------------------------------------------------------------
def one_write(u, va, how, ptr, ccr):
    """The instruction at va with every register set: (0x40a78888, the registers, the condition codes, the stack,
    the instructions run)."""
    from unicorn import UC_HOOK_CODE
    import unicorn.m68k_const as mk
    regs = regs_of()
    vals = [0x5a000000 + 0x1111 * i for i in range(len(regs))]
    if how == "d0":
        vals[0] = ptr
    elif how == "d2":
        vals[2] = ptr
    else:
        vals[14] = PENDING_KIT
        u.uc.mem_write(PENDING_KIT, struct.pack(">I", ptr))
    for r, v in zip(regs, vals):
        u.uc.reg_write(r, v)
    sp = t7.STACK - 0x400
    u.uc.reg_write(mk.UC_M68K_REG_SR, 0x2700 | ccr)   # before a7: a change of mode swaps the stack pointers
    u.uc.reg_write(mk.UC_M68K_REG_A7, sp)
    u.uc.mem_write(PLAYING_KIT, struct.pack(">I", 0xdeadbeef))
    u.bad.clear()
    n = [0]

    def count(uc, addr, size, ud):
        n[0] += 1
    h = u.uc.hook_add(UC_HOOK_CODE, count)
    u.uc.emu_start(va, va + 6, count=200_000)
    u.uc.hook_del(h)
    got = [u.uc.reg_read(r) & 0xffffffff for r in regs]
    return (u.u32(PLAYING_KIT), got == vals, u.uc.reg_read(mk.UC_M68K_REG_SR) & 0x1f,
            u.uc.reg_read(mk.UC_M68K_REG_A7) == sp, n[0], not u.bad)


def seq_tests(key, stock, w):
    tweak, info, img, runtime = w
    da = info["perform"]["data_at"]
    a, b = rig(stock), rig(img, runtime)
    fresh = pattern_bytes()
    ptrs = [kit(5), kit(0), kit(95), kit(3), kit(5) + 2, KITS - 4, kit(95) + KIT_SIZE, 0, 0x80001000]
    cost = {}
    for name, how in SEQ_SITES.items():
        va = int(SITES[name]["at"], 16)
        same = kept = quiet = follows = True
        for ccr in (0x00, 0x1f):
            for ptr in ptrs:
                ra = one_write(a, va, how, ptr, ccr)
                m = Model(fresh)                      # the mode off
                load(b, m, da)
                rb = one_write(b, va, how, ptr, ccr)
                same &= ra[0] == rb[0] == ptr and ra[2] == rb[2] and ra[1] and rb[1] and ra[3] and rb[3] and ra[5] and rb[5]
                quiet &= state(b, da) == (fresh, m.block())
                cost.setdefault("off", rb[4])
                m = Model(fresh)                      # the mode on in pattern 3, tweaked
                m.toggle(3)
                m.kits[KIT_SIZE * 3 + 40] ^= 0xff
                m.kits[KIT_SIZE * 3 + 693] ^= 0x55
                load(b, m, da)
                rb = one_write(b, va, how, ptr, ccr)
                m.change(ptr)
                kept &= ra[0] == rb[0] == ptr and ra[2] == rb[2] and rb[1] and rb[3] and rb[5]
                follows &= state(b, da) == (bytes(m.kits), m.block())
                if ptr == kit(5):
                    cost["change"] = rb[4]
                nxt = kit(9)                          # a second change before the interface ran
                rb = one_write(b, va, how, nxt, ccr)
                m.change(nxt)
                follows &= rb[0] == nxt and rb[1] and rb[5] and state(b, da) == (bytes(m.kits), m.block())
                if ptr == kit(5):
                    cost["second"] = rb[4]
        check(same, f"{key}: {name} {va:#x}, the mode off: 0x40a78888, every register, the condition codes and the stack "
                    f"as the stock instruction leaves them ({2 * len(ptrs)} cases)")
        check(quiet, f"{key}: {name}, the mode off: no kit and no byte of the data block changes")
        check(kept, f"{key}: {name}, the mode on: the write, the registers, the condition codes and the stack as stock")
        check(follows, f"{key}: {name}, the mode on: the kits and the state follow perform.c's model (a change, the "
                       "same kit, a pointer that is no kit, a second change before the interface ran)")
    print(f"        cost of the write, in instructions (stock 1): the mode off {cost['off']}, a change "
          f"{cost['change']}, a second change before the interface ran {cost['second']}")


# --- 3. the interface's kit selection --------------------------------------------------------------------------------
def select(u, bound, current, force):
    import test_shortcuts as SH
    u.uc.mem_write(OBJ + 116, struct.pack(">I", VT))
    u.uc.mem_write(VT + 108, struct.pack(">I", H_BOUND))
    u.hooks = {H_BOUND: ("bound", bound), SEQ_STATE: ("seq", 0x93e20000), CURRENT: ("current", current),
               BIND: ("bind", 0)}
    u.calls.clear()
    vals = SH.sentinels(u)
    d0 = u.call(KIT_SELECT, OBJ, force)
    kept = [u.uc.reg_read(r) & 0xffffffff for r in SH.KEPT] == vals
    calls = [(n, a[:4] if n == "bind" else a[:1]) for n, a in u.calls]
    return d0 & 0xffffffff, calls, u.sp_ok and kept and not u.bad


def ui_tests(key, stock, w):
    tweak, info, img, runtime = w
    da = info["perform"]["data_at"]
    a, b = rig(stock), rig(img, runtime)
    fresh = pattern_bytes()
    same = ok = follows = True
    binds = 0
    for bound, current, force in ((3, 3, 0), (3, 5, 0), (3, 3, 1), (5, 5, 0), (7, 5, 1)):
        ra = select(a, bound, current, force)
        for on, pending in ((0, 0), (1, 0), (1, 1)):
            m = Model(fresh)
            if on:
                m.toggle(3)
                m.kits[KIT_SIZE * 3 + 200] ^= 0xff
            if pending:
                m.change(kit(5))
                m.kits[KIT_SIZE * 3 + 300] ^= 0xff     # a knob after the change, on the kit left
            load(b, m, da)
            rb = select(b, bound, current, force)
            m.ui()
            same &= ra[:2] == rb[:2]
            ok &= ra[2] and rb[2]
            follows &= state(b, da) == (bytes(m.kits), m.block())
        binds += sum(1 for n, _ in ra[1] if n == "bind")
    check(same and binds == 3, f"{key}: 0x4000f36a makes the same calls with the same arguments and answers as on the "
                               f"stock OS, bound or not, forced or not ({binds} of 5 bind)")
    check(ok, f"{key}: 0x4000f36a: the stack comes back, d2-d7/a2-a6 kept, no access outside memory")
    check(follows, f"{key}: 0x4000f36a: with a pattern to give back the kits and the state follow the model (the "
                   "tweaked bytes once more, the pattern left its own); else nothing changes")


# --- 4. SETTINGS + PATTERN ---------------------------------------------------------------------------------------------
def pat_case(u, flags, playing=3, extra=None):
    """PatternGridView's PATTERN case from its first instruction: (where it goes, a3, d3's byte, the stack against
    the case's start, the registers kept, the calls)."""
    from unicorn import UC_HOOK_CODE
    import unicorn.m68k_const as mk
    regs = regs_of()
    vals = [0x5b000000 + 0x1111 * i for i in range(len(regs))]
    vals[2], vals[10] = EVENT, VIEW                   # d2 the event, a2 the view
    for r, v in zip(regs, vals):
        u.uc.reg_write(r, v)
    sp = t7.STACK - 0x400
    u.uc.reg_write(mk.UC_M68K_REG_SR, 0x2000)         # before a7: a change of mode swaps the stack pointers
    u.uc.reg_write(mk.UC_M68K_REG_A7, sp)
    ev = bytearray(32)
    struct.pack_into(">II", ev, 12, K_PATTERN, flags)
    u.uc.mem_write(EVENT, bytes(ev))
    u.hooks = {SEQ_STATE: ("seq", 0x93e20000), CURRENT: ("current", playing), PROJECT: ("project", PROJ),
               KIT_CHANGED: ("changed", 0), AUDIO_KIT: ("audio", 0), UI_STATE: ("ui", 0x93a20000),
               TEMP_KIT_SAVE: ("tempsave", 1)}
    u.hooks.update(extra or {})
    u.calls.clear()
    u.bad.clear()
    got = []

    def stop(uc, addr, size, ud):
        if addr in (PAT_NEXT, EPILOGUE):
            got.append(addr)
            uc.emu_stop()
    h = u.uc.hook_add(UC_HOOK_CODE, stop)
    u.uc.emu_start(PAT_CASE, 0x90000000, count=200_000)
    u.uc.hook_del(h)
    now = [u.uc.reg_read(r) & 0xffffffff for r in regs]
    others = [i for i in range(len(regs)) if i not in (0, 1, 3, 8, 9, 11)]     # but d0, d1, d3, a0, a1, a3
    d3_ok = now[3] == vals[3] if got == [PAT_NEXT] else now[3] == 1            # handled: moveq #1,d3, as 0x40020d5e
    return (got[0] if got else None, now[11], now[3] & 0xff, u.uc.reg_read(mk.UC_M68K_REG_A7) - sp,
            all(now[i] == vals[i] for i in others) and d3_ok and not u.bad,
            [(n, a[:3]) for n, a in u.calls if n in ("changed", "audio")])


def gesture_tests(key, stock, w):
    tweak, info, img, runtime = w
    da, held_at = info["perform"]["data_at"], info["perform"]["held"]
    a, b = rig(stock), rig(img, runtime)
    fresh = pattern_bytes()
    press, repeat, release = 1, 9, 0
    ok = True
    for u in (a, b):
        u.hold(K_SETTINGS, False)
    m = Model(fresh)
    load(b, m, da)
    b.uc.mem_write(held_at, b"\0")
    for flags in (press, repeat, release):
        ra, rb = pat_case(a, flags), pat_case(b, flags)
        ok &= ra[0] == rb[0] == PAT_NEXT and ra[1] == rb[1] == UI_STATE and ra[3] == rb[3] == 0 and ra[4] and rb[4]
        ok &= not rb[5] and state(b, da)[0] == fresh and state(b, da)[1][:5] == bytes(5)
    check(ok, f"{key}: PATTERN without SETTINGS (press, repeat, release): on to {PAT_NEXT:#x} with a3 = {UI_STATE:#x}, "
              "the stack and the registers as on the stock OS, the mode off, no kit touched")
    b.hold(K_SETTINGS, True)
    r = pat_case(b, repeat)
    check(r[0] == PAT_NEXT and state(b, da)[1][0] == 0, f"{key}: SETTINGS held, PATTERN's repeat without its press: stock")
    r = pat_case(b, press, playing=3)
    m.toggle(3)
    m.taken = 1
    check(r[0] == EPILOGUE and r[2] == 1 and r[3] == 0 and r[4] and state(b, da) == (bytes(m.kits), m.block()),
          f"{key}: SETTINGS + PATTERN: the mode on in the playing pattern, its own bytes kept, the handler ends as "
          f"handled (d3 = 1 at {EPILOGUE:#x}, the stack as at the case's start, the registers kept)")
    b.hold(K_SETTINGS, False)                         # SETTINGS let go first
    r = pat_case(b, repeat)
    check(r[0] == EPILOGUE and state(b, da) == (bytes(m.kits), m.block()), f"{key}: the taken press's repeat: taken, no "
                                                                           "second switch")
    r = pat_case(b, release)
    m.taken = 0
    check(r[0] == EPILOGUE and state(b, da) == (bytes(m.kits), m.block()), f"{key}: its release: taken, then nothing "
                                                                           "more is")
    r = pat_case(b, press)
    r2 = pat_case(b, release)
    check(r[0] == r2[0] == PAT_NEXT and state(b, da)[1][0] == 1, f"{key}: PATTERN alone with the mode on: stock")
    kits = bytearray(state(b, da)[0])                 # tweaked, then a change to 6 and the interface
    kits[KIT_SIZE * 3 + 50] ^= 0xff
    m.kits[KIT_SIZE * 3 + 50] ^= 0xff
    b.uc.mem_write(KITS, bytes(kits))
    one_write(b, int(SITES["seq_set"]["at"], 16), "d2", kit(6), 0)
    m.change(kit(6))
    b.uc.mem_write(PLAY_KIT, struct.pack(">I", kit(6)))
    b.uc.mem_write(held_at, b"\1")                    # SETTINGS by its last event alone
    r = pat_case(b, press, playing=6)
    m.toggle(6)
    m.taken = 1
    kits_now, block = state(b, da)
    check(r[0] == EPILOGUE and kits_now == fresh == bytes(m.kits) and block[:5] == m.block()[:5],
          f"{key}: SETTINGS by its last event + PATTERN: the mode off, every kit has its own bytes again (the pattern "
          "left before the interface ran too)")
    check(r[5] == [("audio", (kit(6),) + r[5][0][1][1:]), ("changed", (PROJ + 116, 6, 0))] if len(r[5]) == 2 else False,
          f"{key}: off: the audio side's call with the playing kit, then the kit's change notice (project + 116, 6, 0)")
    pat_case(b, release)


# --- 5. the key code accessor ----------------------------------------------------------------------------------------
def accessor_tests(key, stock, w):
    tweak, info, img, runtime = w
    held_at = info["perform"]["held"]
    a, b = rig(stock), rig(img, runtime)
    ok = byte = True
    b.uc.mem_write(held_at, b"\0")
    for code, flags, want in ((K_SETTINGS, 1, 1), (K_PATTERN, 0, 1), (K_SETTINGS, 9, 1), (K_SETTINGS, 0x21, 1),
                              (K_PATTERN, 1, 1), (K_SETTINGS, 0, 0), (K_SETTINGS, 0x10, 0), (9, 1, 0)):
        ev = bytearray(32)
        struct.pack_into(">II", ev, 12, code, flags)
        for u in (a, b):
            u.uc.mem_write(EVENT, bytes(ev))
        ok &= a.call(ACCESSOR, EVENT) == b.call(ACCESSOR, EVENT) == code and not a.bad and not b.bad
        byte &= b.uc.mem_read(held_at, 1)[0] == want
    check(ok, f"{key}: 0x4007240c returns the event's code as the stock accessor does")
    check(byte, f"{key}: SETTINGS' events set the held byte ({held_at:#x}) on a press, a repeat and a long hold and "
                "clear it on the release and the tap; another key leaves it")


# --- 6 to 9. what is saved -----------------------------------------------------------------------------------------
KEPT_IDX = (2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14)     # d2-d7, a2-a6 in regs_of()


def window(u, start, stops, sets, stack, hooks=None):
    """The code from start to the first of stops, every register set (sets: index in regs_of() -> value), the stack
    words at a7: (where it stopped, the registers, a7 against its start, the stack's bytes from a7 to the end of the
    words, the calls, the instructions run, no access outside memory)."""
    from unicorn import UC_HOOK_CODE
    import unicorn.m68k_const as mk
    regs = regs_of()
    vals = [0x5c000000 + 0x1111 * i for i in range(len(regs))]
    for i, v in sets.items():
        vals[i] = v
    sp = t7.STACK - 0x400
    u.uc.reg_write(mk.UC_M68K_REG_SR, 0x2000)
    for r, v in zip(regs, vals):
        u.uc.reg_write(r, v)
    u.uc.reg_write(mk.UC_M68K_REG_A7, sp)
    u.uc.mem_write(sp - 0x100, bytes(0x100))
    u.uc.mem_write(sp, struct.pack(f">{len(stack)}I", *[x & 0xffffffff for x in stack]))
    u.hooks = dict(hooks or {})
    u.calls.clear()
    u.bad.clear()
    got, n = [], [0]

    def step(uc, addr, size, ud):
        n[0] += 1
        if addr in stops and n[0] > 1:
            got.append(addr)
            uc.emu_stop()
    h = u.uc.hook_add(UC_HOOK_CODE, step)
    u.uc.emu_start(start, 0x90000000, count=2_000_000)
    u.uc.hook_del(h)
    now = [u.uc.reg_read(r) & 0xffffffff for r in regs]
    a7 = u.uc.reg_read(mk.UC_M68K_REG_A7)
    end = sp + 4 * len(stack)
    mem = bytes(u.uc.mem_read(a7, end - a7)) if 0 < end - a7 < 0x400 else b""
    return (got[0] if got else None, now, a7 - sp, mem, [(nm, a) for nm, a in u.calls], n[0], not u.bad)


def kept(ra, rb, more=()):
    return all(ra[1][i] == rb[1][i] for i in KEPT_IDX + tuple(more)) and ra[2] == rb[2] and ra[6] and rb[6]


def framed(ra, rb, low, words):
    """A function's start run: the bytes its instructions wrote at a7 (low) and the saved frame pointer with the
    stack's words above it; the locals between are not written by the stock instructions, and in the build they
    hold what the part's call left there."""
    tail = 4 + 4 * words
    return (len(ra[3]) == len(rb[3]) >= low + tail and ra[3][:low] == rb[3][:low] and ra[3][-tail:] == rb[3][-tail:])


def prepared(fresh, case):
    """A model in one of the states the sections use: (model, the kits worth asking for)."""
    m = Model(fresh)
    if case == "off":
        return m
    m.toggle(3)
    m.kits[KIT_SIZE * 3 + 40] ^= 0xff
    m.kits[KIT_SIZE * 3 + 693] ^= 0x55
    m.kits[KIT_SIZE * 3 + HEAD + 9] ^= 0x0f           # a lock sound of pattern 3 edited: the pool is the pattern's
    if case == "left":
        m.change(kit(5))
    return m


def ser_tests(key, stock, w):
    tweak, info, img, runtime = w
    da = info["perform"]["data_at"]
    a, b = rig(stock), rig(img, runtime)
    fresh = pattern_bytes()
    frame = itself = copied = True
    cost = {}
    for case in ("off", "home", "left"):
        for ptr in (kit(3), kit(5), kit(9), kit(95), 0x93e50000):
            stack = [RET, BUF, ptr, 0]
            ra = window(a, SERIALIZER, {SER_NEXT}, {}, stack)
            m = prepared(fresh, case)
            load(b, m, da)
            rb = window(b, SERIALIZER, {SER_NEXT}, {}, stack)
            want = m.ser(ptr)
            at = len(rb[3]) - 8                           # the kit argument, the stack's third word from its end
            got_ptr = struct.unpack(">I", rb[3][at:at + 4])[0] if len(rb[3]) >= 16 else None
            frame &= (ra[0] == rb[0] == SER_NEXT and kept(ra, rb) and len(ra[3]) == len(rb[3]) == 44
                      and ra[3][:at] == rb[3][:at] and ra[3][at + 4:] == rb[3][at + 4:])
            kits_now, block = state(b, da)
            if want is None:
                itself &= got_ptr == ptr and (kits_now, block) == (bytes(m.kits), m.block())
                cost.setdefault("itself", rb[5])
            else:
                big = da + DATA["big"]
                copied &= (got_ptr == big and bytes(b.uc.mem_read(big, KIT_SIZE)) == want
                           and kits_now == bytes(m.kits) and block[:DATA["big"]] == m.block()[:DATA["big"]])
                cost["copy"] = rb[5]
    check(frame, f"{key}: {SERIALIZER:#x} to {SER_NEXT:#x}: the stack, the saved registers, the buffer and the flag as "
                 "on the stock OS (15 cases)")
    check(itself, f"{key}: the mode off, another pattern or no kit: the kit itself, nothing written")
    check(copied, f"{key}: the active pattern's kit and the kit of the pattern left: a copy with the pattern's own "
                  "bytes in 0..693 and the pool as it is; the kits and the state untouched")
    print(f"        cost of the serializer's start, in instructions (stock 2): the kit itself {cost['itself']}, "
          f"a copy {cost['copy']}")


def ksave_tests(key, stock, w):
    tweak, info, img, runtime = w
    da = info["perform"]["data_at"]
    a, b = rig(stock), rig(img, runtime)
    fresh = pattern_bytes()
    same = follows = True
    for case in ("off", "home", "left"):
        for n, slot in ((3, 96), (3, 2), (5, 96), (5, 2), (9, 96), (9, 2)):
            stack = [BUF, kit(n), 0]
            sets = {2: slot, 4: n}
            ra = window(a, KSAVE_SITE, {SER_NEXT}, sets, stack)
            m = prepared(fresh, case)
            load(b, m, da)
            rb = window(b, KSAVE_SITE, {SER_NEXT}, sets, stack)
            m.ksave(n, slot)
            same &= ra[0] == rb[0] == SER_NEXT and kept(ra, rb) and ra[3] == rb[3] and len(ra[3]) == 44
            follows &= state(b, da) == (bytes(m.kits), m.block())
    check(same, f"{key}: {KSAVE_SITE:#x}: into the serializer at {SER_NEXT:#x} with the stack (the return to "
                f"{KSAVE_SITE + 6:#x}, the kit itself), the saved registers and d2-d7/a2-a6 of the stock call (18 cases)")
    check(follows, f"{key}: {KSAVE_SITE:#x}: Save Pattern of the active pattern makes the tweaked bytes its own, a temp "
                   "save notes it; another pattern, the pattern left and the mode off: nothing")


def kload_tests(key, stock, w):
    tweak, info, img, runtime = w
    da = info["perform"]["data_at"]
    a, b = rig(stock), rig(img, runtime)
    fresh = pattern_bytes()
    same = follows = True
    for case in ("off", "home", "left"):
        for n, slot, ok in ((3, 2, 1), (3, 96, 1), (3, 2, 0), (5, 2, 1), (5, 96, 1), (5, 2, 0x5a5a5a00), (9, 2, 1)):
            stack = [kit(n), BUF, n]
            sets = {2: n, 3: slot}
            hooks = {LOADER: ("load", ok)}
            ra = window(a, KLOAD_SITE, {KLOAD_NEXT}, sets, stack, hooks)
            m = prepared(fresh, case)
            m.kits[KIT_SIZE * n:KIT_SIZE * n + HEAD] = bytes([0xe0 + n % 16]) * HEAD       # what the loader wrote
            load(b, m, da)
            rb = window(b, KLOAD_SITE, {KLOAD_NEXT}, sets, stack, hooks)
            m.loaded(n, slot, ok)
            calls = [("load", c[1][:3]) for c in ra[4]], [("load", c[1][:3]) for c in rb[4]]
            same &= (ra[0] == rb[0] == KLOAD_NEXT and kept(ra, rb) and ra[2] == 0 and ra[3] == rb[3]
                     and calls[0] == calls[1] == [("load", (kit(n), BUF, n))] and ra[1][0] == rb[1][0] == ok)
            follows &= state(b, da) == (bytes(m.kits), m.block())
    check(same, f"{key}: {KLOAD_SITE:#x}: the loader called once with the same arguments, its answer in d0, the stack "
                "and d2-d7/a2-a6 as on the stock OS (21 cases)")
    check(follows, f"{key}: {KLOAD_SITE:#x}: Reload Pattern of the active pattern makes the loaded bytes its own; a "
                   "temp reload, a failed load, another pattern and the mode off do not")


def entry_tests(key, stock, w):
    tweak, info, img, runtime = w
    da = info["perform"]["data_at"]
    a, b = rig(stock), rig(img, runtime)
    fresh = pattern_bytes()
    stack = [RET, 0x11223344, 0x55667788, 0x99aabb07, 0xccddeeff, 0x01020304, 0x05060708, 0x090a0b0c]
    same = follows = True
    for case in ("off", "home", "left"):
        ra = window(a, DROP_SITE, {DROP_NEXT}, {}, stack)
        m = prepared(fresh, case)
        if case != "off":
            m.temp.add(m.home)
        load(b, m, da)
        rb = window(b, DROP_SITE, {DROP_NEXT}, {}, stack)
        m.drop()
        same &= ra[0] == rb[0] == DROP_NEXT and kept(ra, rb) and framed(ra, rb, 4, len(stack)) and not rb[4]
        follows &= state(b, da) == (bytes(m.kits), m.block())
    check(same, f"{key}: {DROP_SITE:#x} to {DROP_NEXT:#x}: the frame, the stack and d2-d7/a2-a6 as the stock "
                "instructions leave them, nothing called")
    check(follows, f"{key}: another project: the mode off, nothing to give back, nothing noted, no kit written")
    hooks = {PROJECT: ("project", PROJ), KIT_CHANGED: ("changed", 0), AUDIO_KIT: ("audio", 0),
             TEMP_KIT_SAVE: ("tempsave", 1)}
    for name, (va, nxt) in OFF_SITES.items():
        same = follows = told = True
        for case in ("off", "home", "left"):
            ra = window(a, va, {nxt}, {}, stack)
            m = prepared(fresh, case)
            if case != "off":
                m.temp.add(3)
            load(b, m, da)
            b.uc.mem_write(PLAY_KIT, struct.pack(">I", kit(m.home)))
            rb = window(b, va, {nxt}, {}, stack, hooks)
            was_on, home = m.on, m.home
            saved = m.toggle(home) if was_on else []
            low = ra[1][1] & 0xff == rb[1][1] & 0xff if name == "clear" else True      # d1's byte, 19(a6)
            wrote = 0 if name == "clear" else 36       # movem.l d2-d6/a2-a5,(sp)
            same &= ra[0] == rb[0] == nxt and kept(ra, rb) and framed(ra, rb, wrote, len(stack)) and low
            follows &= state(b, da) == (bytes(m.kits), m.block())
            calls = [(nm, c[:3]) for nm, c in rb[4] if nm in ("audio", "changed", "tempsave")]
            if was_on:
                told &= (len(calls) == 2 + len(saved) and calls[0][0] == "audio" and calls[0][1][0] == kit(home)
                         and calls[1] == ("changed", (PROJ + 116, home, 0))
                         and calls[2:] == [("tempsave", (PROJ, 1, n)) for n in saved])
            else:
                told &= not calls
        check(same, f"{key}: {name} {va:#x} to {nxt:#x}: the frame, the stack and d2-d7/a2-a6 as the stock instructions "
                    "leave them")
        check(follows, f"{key}: {name}: the mode off first, every kit has its own bytes")
        check(told, f"{key}: {name}: the audio side's call with the playing kit, the kit's change notice, then the "
                    "temp-saved pattern's kit to the temp slot again; with the mode off nothing")


# --- 10. the popup ---------------------------------------------------------------------------------------------------
def popup_tests(key, stock, w):
    tweak, info, img, runtime = w
    da = info["perform"]["data_at"]
    b = rig(img, runtime)
    names = ("string", "new", "popup", "views", "target", "present", "drop", "sdrop")
    hooks = {STRING: ("string", 0), NEW: ("new", 0), POPUP: ("popup", 0), VIEWS: ("views", VIEWS_OBJ),
             TARGET: ("target", TARGET_OBJ), PRESENT: ("present", 0), DROP: ("drop", 0), STRING_DROP: ("sdrop", 0)}
    load(b, Model(pattern_bytes()), da)
    b.uc.mem_write(PLAY_KIT, struct.pack(">I", kit(3)))
    b.hold(K_SETTINGS, True)
    b.uc.mem_write(VIEWS_UP, bytes(4))
    r = pat_case(b, 1, extra=dict(hooks))
    quiet = r[0] == EPILOGUE and not [n for n, _ in b.calls if n in names] and state(b, da)[1][0] == 1
    pat_case(b, 0, extra=dict(hooks))
    check(quiet, f"{key}: the switch before the views are up: the mode on, no popup")
    b.uc.mem_write(VIEWS_UP, struct.pack(">I", 0x93e80000))
    for text, on in (("Perform Kit OFF", 0), ("Perform Kit ON", 1)):
        heap = b.heap
        r = pat_case(b, 1, extra=dict(hooks))
        calls = [(n, a) for n, a in b.calls if n in names]
        pop, holder = heap, (heap + 0x9c + 15) & ~15
        order = [n for n, _ in calls] == ["string", "new", "popup", "new", "views", "target", "present", "drop", "sdrop"]
        ok = order and r[0] == EPILOGUE and r[4] and state(b, da)[1][0] == on
        if order:
            sref = calls[0][1][0]
            pair = calls[6][1][1]
            ok &= b.cstr(calls[0][1][1]) == text
            ok &= calls[1][1][0] == 0x9c and calls[3][1][0] == 16
            ok &= calls[2][1][:2] == (pop, sref)
            ok &= calls[5][1][0] == VIEWS_OBJ
            ok &= calls[6][1][0] == TARGET_OBJ and calls[6][1][2] == 0
            ok &= (b.u32(pair), b.u32(pair + 4)) == (pop, holder)
            ok &= [b.u32(holder + 4 * i) for i in range(4)] == [POPUP_HOLDER_VT, 1, 1, pop]
            ok &= calls[7][1][0] == pair + 4 and calls[8][1][0] == sref
            if not on:
                before = [n for n, _ in b.calls]
                ok &= before.index("changed") < before.index("string")
        check(ok, f"{key}: the switch with the views up: « {text} », the string, 0x9c bytes, the popup's constructor, "
                  f"the holder ({POPUP_HOLDER_VT:#x}, 1, 1, the popup), presented on the views' target, the reference "
                  "and the string dropped; the handler ends as handled, the registers kept")
        pat_case(b, 0, extra=dict(hooks))


# --- 11. the mark on the main screen ------------------------------------------------------------------------------
PIXELS = BITMAP + 0x100


def main_draw(u, shown):
    """MainScreenView's draw through its slot, the draw behind it stubbed: (the calls of that draw, the bitmap's words
    after, the stack and the registers kept)."""
    import test_shortcuts as SH
    words = [0x10000 + i for i in range(128 * 2)]
    u.uc.mem_write(BITMAP, struct.pack(">IiiiI", 0, 128, 64, 2, PIXELS))
    u.uc.mem_write(PIXELS, struct.pack(">256I", *words))
    u.hooks = {MAIN_DRAW: ("behind", 0), UI_STATE: ("ui", 0x93a20000), VALUE_SHOWN: ("shown", shown)}
    u.calls.clear()
    vals = SH.sentinels(u)
    u.call(u.u32(MAIN_SLOT), VIEW, BITMAP)
    ok = [u.uc.reg_read(r) & 0xffffffff for r in SH.KEPT] == vals and u.sp_ok and not u.bad
    return ([a[:2] for n, a in u.calls if n == "behind"], list(struct.unpack(">256I", u.uc.mem_read(PIXELS, 1024))),
            words, ok)


def mark_tests(key, stock, w):
    tweak, info, img, runtime = w
    da = info["perform"]["data_at"]
    a, b = rig(stock), rig(img, runtime)
    fresh = pattern_bytes()
    same = drawn = kept_view = True
    for on in (0, 1):
        for shown in (0, 1):
            ra = main_draw(a, shown)
            m = Model(fresh)
            if on:
                m.toggle(3)
            load(b, m, da)
            rb = main_draw(b, shown)
            m.view = VIEW
            same &= ra[0] == rb[0] == [(VIEW, BITMAP)] and ra[3] and rb[3] and ra[1] == ra[2]
            want = list(rb[2])
            if on and not shown:
                want[0:2], want[2:4] = [0xaaaaaaaa] * 2, [0x55555555] * 2
            drawn &= rb[1] == want
            kept_view &= state(b, da) == (bytes(m.kits), m.block())
    check(same, f"{key}: {MAIN_SLOT:#x}: the draw behind called once with (view, bitmap), as the stock slot calls the "
                "stock draw; the stack and d2-d7/a2-a6 kept, no access outside memory")
    check(drawn, f"{key}: the mode on and no value window: columns 0 and 1 hold the checkerboard (0xaaaaaaaa, "
                 "0x55555555), every other word as the draw behind left it; the mode off or a value window open: "
                 "no word changes")
    check(kept_view, f"{key}: the view kept in the data block, nothing else changed")
    m = Model(fresh)
    load(b, m, da)
    m.view = VIEW
    b.uc.mem_write(da, m.block())
    b.uc.mem_write(PLAY_KIT, struct.pack(">I", kit(3)))
    b.hold(K_SETTINGS, True)
    asked = True
    for _ in range(2):                                # on, then off
        pat_case(b, 1, extra={NEEDS_REDRAW: ("redraw", 0)})
        asked &= [c[:1] for n, c in b.calls if n == "redraw"] == [(VIEW,)]
        pat_case(b, 0)
    check(asked, f"{key}: the switch, on and off: the kept view asked for a redraw once")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--dry", action="store_true", help="section 1 only (the builds, no Unicorn)")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    builds = {}
    print("1. the build")
    for key, sel, kw in SELECTIONS:
        w = composed(stock, sel, True, **kw)
        wo = composed(stock, sel, False, **kw) if sel or kw else None
        builds[key] = w
        build_tests(key, w, wo, bool(kw.get("resample")))
    if not args.dry:
        for n, (title, fn) in enumerate((("the sequencer's writes of the playing kit", seq_tests),
                                         ("the interface's kit selection", ui_tests),
                                         ("SETTINGS + PATTERN", gesture_tests),
                                         ("the key code accessor", accessor_tests),
                                         ("the start of the kit serializer", ser_tests),
                                         ("the kit's save to a slot", ksave_tests),
                                         ("the kit's load from a slot", kload_tests),
                                         ("another project, pattern paste and clear", entry_tests),
                                         ("the popup", popup_tests),
                                         ("the mark on the main screen", mark_tests)), 2):
            print(f"{n}. {title}")
            for key in ("perform", "resample+perform"):
                fn(key, stock, builds[key])
    print("\nALL OK" if not t7.FAIL else f"\n{len(t7.FAIL)} FAILED: " + "; ".join(t7.FAIL[:6]))
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
