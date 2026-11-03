#!/usr/bin/env python3
"""The RESAMPLE recorder on the host (notes/79, step R1, proof 5): tools/machines/resample/resample.c compiled with
the host's C compiler (RS_HOST: the data block an array, the RAM claim a buffer the test gives), and driven block by
block as entries.S's rs_mix drives it on the machine: rs_pre with the six tracks' buffers and the tracks triggered,
then rs_post with the main bus and the USB input.

  1. the data block's layout as part.json declares it;
  2. arming: the source, a track always mono, USB's TRIG as LEVEL, the levels from the dB table in each source's
     scale, the longest take at most what the buffer holds, refused while armed or recording;
  3. idle and taken: nothing written; the take's own source only (a track's buffer and its bit, main, USB);
  4. the start: TRIG on the source's bit (main: any track's), NOW at once, LEVEL with the eight blocks before it from
     the ring (fewer when fewer came), oldest first;
  5. main and USB: stereo as {L, R}, mono as (L >> 1) + (R >> 1);
  6. the end: LENGTH exactly (the words after it untouched), RECORD with the block after the request, a full
     buffer, SILENT after 250 ms below -72 dB once 50 ms are in, the tail cut after the last block over -90 dB; the
     peak (full scale included), the meter's level; stop, cancel and release;
  7. the save: the 64-byte header, NORM's shift and gain (the peak at -0.3 dB, no sample past full scale), the
     16-bit words big-endian, saturated and counted.

No Unicorn, no numpy, no firmware: a C compiler (cc) and python3.

    python3 tools/emu/resample_host.py
"""
import ctypes
import json
import math
import pathlib
import random
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PART = HERE.parent / "machines" / "resample"
BLOCK, RATE = 32, 48000
IDLE, ARMED, REC, TAKEN = range(4)
TRIG, LEVEL, NOW = range(3)
SILENT, LENGTH, RECORD = range(3)
END_NONE, END_SILENT, END_LENGTH, END_RECORD, END_FULL = range(5)
MAIN, USB = 6, 7
RING_BYTES = 2304
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  FAIL  ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


class Data(ctypes.Structure):
    _fields_ = [("buf", ctypes.c_uint32), ("cap", ctypes.c_uint32), ("ring", ctypes.c_uint32),
                ("shift", ctypes.c_uint8 * 3), ("pad0", ctypes.c_uint8), ("state", ctypes.c_uint8),
                ("src", ctypes.c_uint8), ("stereo", ctypes.c_uint8), ("start", ctypes.c_uint8),
                ("stop", ctypes.c_uint8), ("req", ctypes.c_uint8), ("end", ctypes.c_uint8),
                ("ring_n", ctypes.c_uint8), ("ring_at", ctypes.c_uint8), ("pad1", ctypes.c_uint8 * 3),
                ("thr", ctypes.c_uint32), ("sil", ctypes.c_uint32), ("cut", ctypes.c_uint32),
                ("limit", ctypes.c_uint32), ("frames", ctypes.c_uint32), ("peak", ctypes.c_uint32),
                ("quiet", ctypes.c_uint32), ("loud", ctypes.c_uint32), ("level", ctypes.c_uint32)]


def build():
    cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if not cc:
        sys.exit("!! no C compiler (cc)")
    tmp = pathlib.Path(tempfile.mkdtemp())
    lib = tmp / "resample.so"
    subprocess.run([cc, "-std=c99", "-O2", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC", "-DRS_HOST",
                    "-o", str(lib), str(PART / "resample.c")], check=True)
    return ctypes.CDLL(str(lib))


class Rec:
    """The recorder with a RAM claim of cap words after the ring, and the sources' buffers."""

    def __init__(self, lib, cap=48000 * 2, shift=(0, 0, 0)):
        self.lib = lib
        self.cap = cap
        self.mem = (ctypes.c_uint8 * (RING_BYTES + 4 * cap + 64))()
        ctypes.c_void_p.in_dll(lib, "rs_host_mem").value = ctypes.addressof(self.mem)
        self.raw = (ctypes.c_uint32 * 16).in_dll(lib, "rs_data")
        ctypes.memset(ctypes.addressof(self.raw), 0, 64)
        self.d = Data.from_address(ctypes.addressof(self.raw))
        self.d.buf, self.d.cap, self.d.ring = RING_BYTES, cap, 0
        for i, s in enumerate(shift):
            self.d.shift[i] = s
        self.tracks = (ctypes.c_int32 * (6 * BLOCK))()
        self.bus = (ctypes.c_int32 * (2 * BLOCK))()
        self.usb = (ctypes.c_int32 * (2 * BLOCK))()
        self.words = (ctypes.c_int32 * (cap + 16)).from_address(ctypes.addressof(self.mem) + RING_BYTES)
        for f in ("rs_pre", "rs_post"):
            getattr(lib, f).restype = None
        lib.rs_arm.restype = lib.rs_stop.restype = lib.rs_cancel.restype = lib.rs_release.restype = None

    def arm(self, src, stereo=0, start=TRIG, stop=SILENT, thr_db=40, seconds=10):
        self.lib.rs_arm(src, stereo, start, stop, thr_db, seconds)

    def block(self, tracks=None, bus=None, usb=None, trig=0):
        """One audio block as rs_mix runs it: tracks [6][32], bus and usb [64] ({L, R}), trig the triggered mask."""
        for t in range(6):
            for i in range(BLOCK):
                self.tracks[BLOCK * t + i] = tracks[t][i] if tracks else 0
        for i in range(2 * BLOCK):
            self.bus[i] = bus[i] if bus else 0
            self.usb[i] = usb[i] if usb else 0
        self.lib.rs_pre(self.tracks, ctypes.c_uint32(trig))
        self.lib.rs_post(self.bus, self.usb, ctypes.c_uint32(trig))

    def take(self, n=None):
        ch = 2 if self.d.stereo else 1
        return list(self.words[:ch * (self.d.frames if n is None else n)])


def const(v, n=BLOCK):
    return [v] * n


def track_block(t, values):
    out = [const(0) for _ in range(6)]
    out[t] = values
    return out


def ramp(seed, n=BLOCK, amp=1 << 28):
    rnd = random.Random(seed)
    return [rnd.randrange(-amp, amp) for _ in range(n)]


def mag(x):
    return abs(x) & 0xffffffff


def main():
    lib = build()
    part = json.loads((PART / "part.json").read_text(encoding="utf-8"))
    db = [round(2 ** 31 * 10 ** (-3 * k / 20)) for k in range(33)]

    print("1. the data block")
    offs = {name: getattr(Data, name).offset for name, _ in Data._fields_ if not name.startswith("pad")}
    want = {k: v for k, v in part["data"].items() if k != "size"}
    check(offs == want and ctypes.sizeof(Data) == part["data"]["size"],
          f"the fields at part.json's offsets, {ctypes.sizeof(Data)} bytes")
    check(part["ring_bytes"] == 9 * 2 * BLOCK * 4, f"the ring: 9 blocks of 64 words, {part['ring_bytes']} bytes")

    print("2. arming")
    r = Rec(lib, shift=(1, 2, 3))
    r.arm(2, stereo=1, start=LEVEL, stop=LENGTH, thr_db=24, seconds=1)
    d = r.d
    check((d.state, d.src, d.stereo, d.start, d.stop) == (ARMED, 2, 0, LEVEL, LENGTH),
          "a track: armed, mono whatever was asked")
    check((d.thr, d.sil, d.cut) == (db[8] >> 1, db[24] >> 1, db[30] >> 1),
          "the levels: -24, -72 and -90 dB of the track's full scale (2^31 >> 1)")
    check(d.limit == RATE, "the longest take: 1 s")
    r.arm(5, start=TRIG)
    check(d.src == 2, "refused while armed")
    lib.rs_cancel()
    r.arm(USB, stereo=1, start=TRIG, thr_db=60, seconds=10)
    check((d.src, d.stereo, d.start, d.thr) == (USB, 1, LEVEL, db[20] >> 3), "USB: stereo kept, TRIG as LEVEL, -60 dB "
                                                                             "in USB's scale (2^31 >> 3)")
    check(d.limit == r.cap // 2, f"10 s stereo past the buffer: its {r.cap // 2} frames")
    lib.rs_cancel()
    r.arm(MAIN, stereo=0, seconds=1)
    check((d.stereo, d.limit) == (0, RATE), "main, mono: 1 s")
    lib.rs_cancel()
    r.arm(9)
    check(d.state == IDLE, "a source past USB refused")

    print("3. idle, taken, the take's own source")
    r = Rec(lib)
    for k in range(len(r.words)):
        r.words[k] = 0x55555555
    r.block(tracks=[const(1000 * (t + 1)) for t in range(6)], bus=const(7, 64), usb=const(9, 64), trig=0x3f)
    check(all(w == 0x55555555 for w in r.words[:200]) and r.d.state == IDLE, "idle: nothing written")
    r.arm(3, start=TRIG)
    r.block(tracks=[const(1000 * (t + 1)) for t in range(6)], trig=0x37)
    check(r.d.state == ARMED, "track 4 (src 3) armed: the block that triggers 1, 2, 3, 5, 6 does not start it")
    r.block(tracks=[const(1000 * (t + 1)) for t in range(6)], bus=const(7, 64), trig=0x08)
    check(r.d.state == REC and r.take() == const(4000), "its bit (0x08) starts it with track 4's block, nothing else")
    lib.rs_stop()
    r.block(tracks=[const(1000 * (t + 1)) for t in range(6)])
    check(r.d.state == TAKEN and r.d.frames == 64, "RECORD: taken with the next block")
    before = r.take()
    r.block(tracks=[const(1 << 20) for _ in range(6)], trig=0x3f)
    check(r.take() == before and r.d.frames == 64 and r.d.state == TAKEN, "taken: the next blocks leave it as it is")
    lib.rs_release()
    check(r.d.state == IDLE, "released: idle")

    print("4. the start")
    r = Rec(lib)
    r.arm(MAIN, start=TRIG)
    r.block(bus=const(100, 64), trig=0)
    check(r.d.state == ARMED, "main, TRIG: no track triggered, armed")
    r.block(bus=const(100, 64), trig=0x20)
    check(r.d.state == REC, "main, TRIG: track 6's trigger starts it")
    lib.rs_cancel()
    r.arm(0, start=NOW)
    r.block(tracks=track_block(0, const(5)))
    check(r.d.state == REC and r.take() == const(5), "NOW: the first block")
    lib.rs_cancel()
    r = Rec(lib)
    r.arm(1, start=LEVEL, thr_db=40)
    thr = db[13]
    quiet = [[thr // 4 + 64 * b + i for i in range(BLOCK)] for b in range(12)]
    for b in range(12):
        r.block(tracks=track_block(1, quiet[b]))
    check(r.d.state == ARMED and r.d.ring_n == 8, "LEVEL: twelve blocks under -40 dB, armed, eight in the ring")
    loud = [thr + i for i in range(BLOCK)]
    r.block(tracks=track_block(1, loud))
    want = sum(quiet[4:], []) + loud
    check(r.d.state == REC and r.take() == want, "the block over it starts the take, the eight before it first, "
                                                 "oldest first (288 frames)")
    lib.rs_cancel()
    r.arm(1, start=LEVEL, thr_db=40)
    for b in range(3):
        r.block(tracks=track_block(1, quiet[b]))
    r.block(tracks=track_block(1, [thr - 1] * 31 + [thr]))
    check(r.d.state == REC and r.take() == sum(quiet[:3], []) + [thr - 1] * 31 + [thr],
          "three blocks before it: those three; one sample at the threshold is enough")
    lib.rs_cancel()

    print("5. main and USB")
    lr = [(-(1 << 31)) if i == 0 else (i * 1000003 % (1 << 30)) * (1 if i % 3 else -1) for i in range(64)]
    r = Rec(lib)
    r.arm(MAIN, stereo=1, start=NOW)
    r.block(bus=lr, usb=const(1, 64))
    check(r.take() == lr and r.d.peak == 0x80000000, "main, stereo: the {L, R} words, the peak of -2^31 is 2^31")
    lib.rs_cancel()
    r.arm(MAIN, stereo=0, start=NOW)
    r.block(bus=lr)
    check(r.take() == [(lr[2 * i] >> 1) + (lr[2 * i + 1] >> 1) for i in range(BLOCK)],
          "main, mono: (L >> 1) + (R >> 1)")
    lib.rs_cancel()
    r.arm(USB, stereo=1, start=NOW)
    r.block(bus=const(3, 64), usb=lr)
    check(r.take() == lr, "USB, stereo: USB's words, not main's")
    lib.rs_cancel()

    print("6. the end")
    r = Rec(lib)
    for k in range(len(r.words)):
        r.words[k] = 0x55555555
    r.arm(2, start=NOW, stop=LENGTH, seconds=1)
    blocks = 0
    while r.d.state == REC or blocks == 0:
        r.block(tracks=track_block(2, ramp(blocks)))
        blocks += 1
    check(r.d.end == END_LENGTH and r.d.frames == RATE and blocks == math.ceil(RATE / BLOCK),
          f"LENGTH 1 s: {r.d.frames} frames in {blocks} blocks")
    check(r.words[RATE] == 0x55555555, "the word after the take untouched")
    flat = sum((ramp(b) for b in range(blocks)), [])[:RATE]
    check(r.take() == flat and r.d.peak == max(mag(x) for x in flat), "the take and its peak as the blocks gave them")
    lib.rs_cancel()
    r = Rec(lib, cap=1000)
    r.arm(0, start=NOW, stop=SILENT, seconds=40)
    while r.d.state == REC or r.d.frames == 0:
        r.block(tracks=track_block(0, const(1 << 30)))
    check(r.d.end == END_FULL and r.d.frames == 1000, "a buffer of 1000 words: full at 1000 frames")
    lib.rs_cancel()
    r = Rec(lib)
    r.arm(0, start=NOW, stop=SILENT)
    sil, cut = db[24], db[30]
    seq = [1 << 29] * 100 + [sil + 1] * 3 + [sil - 1] * 5 + [cut] * 2 + [cut - 1] * 1000
    n = 0
    while r.d.state == REC or n == 0:
        r.block(tracks=track_block(0, const(seq[n] if n < len(seq) else 0)))
        n += 1
    loud_end = (100 + 3 + 5 + 2) * BLOCK
    quiet_from = 103 * BLOCK
    check(r.d.end == END_SILENT and r.d.frames == loud_end,
          f"SILENT: ended {n * BLOCK - quiet_from} frames after the last block over -72 dB, cut after the last over "
          f"-90 dB ({r.d.frames} frames)")
    check(n * BLOCK - quiet_from == 12000, "250 ms below -72 dB end it")
    lib.rs_cancel()
    r.arm(0, start=NOW, stop=SILENT)
    n = 0
    while (r.d.state == REC or n == 0) and n < 1000:
        r.block(tracks=track_block(0, const(0)))
        n += 1
    check(r.d.end == END_SILENT and r.d.frames == 0 and n * BLOCK == 2400 + 12000,
          f"silence from the start: ends after 50 ms and 250 ms ({n} blocks), nothing kept")
    lib.rs_cancel()
    r.arm(0, start=NOW, stop=RECORD, seconds=2)
    for b in range(5):
        r.block(tracks=track_block(0, const(10 << 20) if b != 2 else const(-(30 << 20))))
    check(r.d.state == REC and r.d.level == 10 << 20 and r.d.peak == 30 << 20, "the meter's level and the peak")
    lib.rs_stop()
    r.block(tracks=track_block(0, const(1)))
    check(r.d.end == END_RECORD and r.d.frames == 6 * BLOCK, "STOP RECORD: ends with the block after RECORD")
    lib.rs_cancel()
    r.arm(0, start=TRIG)
    lib.rs_stop()
    check(r.d.state == IDLE, "RECORD while armed: idle")

    print("7. the save")
    lib.rs_header.restype = None
    h = (ctypes.c_uint8 * 64)()
    lib.rs_header(h, 48000, 0)
    hb = bytes(h)
    check(hb[1] == 0 and hb[4:8] == (96000).to_bytes(4, "big") and hb[8:12] == (48000).to_bytes(4, "big")
          and hb[16:20] == (47999).to_bytes(4, "big") and hb[20] == 0x7f
          and not any(hb[i] for i in range(64) if i not in (4, 5, 6, 7, 8, 9, 10, 11, 16, 17, 18, 19, 20)),
          "header, 1 s mono: +4 96000 bytes, +8 48000, +16 47999, +20 0x7f, the rest zero")
    lib.rs_header(h, 3, 1)
    hb = bytes(h)
    check(hb[1] == 1 and hb[4:8] == (12).to_bytes(4, "big") and hb[16:20] == (2).to_bytes(4, "big"),
          "header, 3 frames stereo: +1 1, 12 bytes, last frame 2")
    s, g = ctypes.c_uint32(), ctypes.c_uint32()
    lib.rs_pcm16.restype = ctypes.c_uint32
    ok_norm = True
    for peak in (1, 300, 32767, 65535, 65536, 1 << 24, 0x7fffffff, 0x80000000):
        lib.rs_norm(ctypes.c_uint32(peak), ctypes.byref(s), ctypes.byref(g))
        top = min(peak, 0x7fffffff)
        x = (ctypes.c_int32 * 2)(top, -top if peak < 0x80000000 else -(1 << 31))
        out = (ctypes.c_uint8 * 4)()
        clipped = lib.rs_pcm16(out, x, 2, s.value, g.value)
        y = int.from_bytes(bytes(out[:2]), "big", signed=True)
        ok_norm &= clipped == 0 and 31600 <= y <= 31655 and (peak >> s.value) < 65536
    check(ok_norm, "NORM: peaks from 1 to 2^31 at -0.3 dB (31 600 to 31 655), none past full scale")
    lib.rs_norm(ctypes.c_uint32(0), ctypes.byref(s), ctypes.byref(g))
    check((s.value, g.value) == (31, 0), "NORM of silence: shift 31, no gain")
    vals = [0, 1 << 15, -(1 << 15), (1 << 31) - 1, -(1 << 31), 0x12345678, -0x12345678]
    x = (ctypes.c_int32 * len(vals))(*vals)
    out = (ctypes.c_uint8 * (2 * len(vals)))()
    clipped = lib.rs_pcm16(out, x, len(vals), 16, 0)
    got = [int.from_bytes(bytes(out[2 * i:2 * i + 2]), "big", signed=True) for i in range(len(vals))]
    check(got == [v >> 16 for v in vals] and clipped == 0, "as heard, shift 16: x >> 16, big-endian")
    clipped = lib.rs_pcm16(out, x, len(vals), 14, 0)
    got = [int.from_bytes(bytes(out[2 * i:2 * i + 2]), "big", signed=True) for i in range(len(vals))]
    check(got == [max(-32768, min(32767, v >> 14)) for v in vals] and clipped == 2,
          "shift 14: full scale saturated at -32768 and 32767, the two counted")

    print("\nALL OK" if not FAIL else f"\n{len(FAIL)} FAILED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
