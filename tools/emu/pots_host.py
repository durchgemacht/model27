#!/usr/bin/env python3
"""POTS on the host (notes/69 §8, §14): tools/machines/pots/pots.c compiled with the host's C compiler (POTS_HOST, at
the manifest's rate), which is the model tools/emu/test_fxslot.py compares the device's object with, block for block;
and the measurements that settled v6 in the float prototype (notes/69 §2, §12.3) taken again on that build, against
v6's numbers.

The host build is pots.c's own arithmetic, the EMAC as tools/emu/emac.py executes it: once test_fxslot.py finds the
device's object giving the same bits as this build, what is measured here holds for the device. The sources are
synthesized as the prototype's were (a pluck phrase, a minor-seventh stab, one bright note: band-limited saws).

    python3 tools/emu/pots_host.py       # the measurements against v6: numpy and a C compiler, no Unicorn, no firmware
"""
import atexit
import ctypes
import json
import math
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parent / "machines" / "pots"
SR, BLOCK = 48000, 32
D_SCAT, D_FADE, D_CODEC, D_LEVEL, D_RX, D_TX = 1, 2, 4, 8, 16, 32
ALL_OFF = D_SCAT | D_FADE | D_CODEC | D_LEVEL | D_RX | D_TX
_TMP = []


def _manifest():
    return json.loads((PKG / "manifest.json").read_text(encoding="utf-8"))


def _built():
    """The host build, compiled once a run: the manifest's defines, POTS_HOST, -fwrapv as on the device."""
    if not _TMP:
        d = pathlib.Path(tempfile.mkdtemp(prefix="pots-host-"))
        atexit.register(shutil.rmtree, d, True)
        defs = [f"-D{k}={v}" for k, v in _manifest()["build"].get("defines", {}).items()]
        cc = shutil.which("cc") or shutil.which("gcc") or "cc"
        out = d / "pots.so"
        r = subprocess.run([cc, "-O2", "-std=c99", "-fwrapv", "-Wall", "-Wextra", "-Werror", "-DPOTS_HOST", *defs,
                            f"-I{PKG}", "-shared", "-fPIC", "-o", str(out), str(PKG / "pots.c")],
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit("!! the host build of pots.c failed:\n" + r.stderr)
        _TMP[:] = [d, out, 0]
    return _TMP


def load():
    """A fresh copy of the host build: its own statics (the state, the line, the random generator), as the device's
    effect starts from the payload's cleared variables."""
    t = _built()
    t[2] += 1
    copy = t[0] / f"pots-{t[2]}.so"
    shutil.copy(t[1], copy)
    lib = ctypes.CDLL(str(copy))
    lib.pots_process.argtypes = [ctypes.c_void_p] * 3
    lib.pots_render.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int,
                                ctypes.c_int32, ctypes.c_uint32]
    lib.pots_host_tempo.argtypes = [ctypes.c_int32]
    return lib


class Pots:
    """The delay slot's model of POTS for test_fxslot.py: x (64 bus words), params (Time, Fdbk x 256) -> the 64 words
    the device's pots_process writes."""
    tempo = 14400                                # the OS's, set from the image by test_fxslot.py

    def __init__(self):
        self.lib = load()
        self.lib.pots_host_tempo(self.tempo)
        self.out, self.inp, self.par = (ctypes.c_int32 * 64)(), (ctypes.c_int32 * 64)(), (ctypes.c_int16 * 2)()

    def reset(self):
        self.lib.pots_reset()

    def __call__(self, x, params):
        self.inp[:] = [int(v) for v in x]
        self.par[:] = [int(v) for v in params]
        self.lib.pots_process(self.out, self.inp, self.par)
        return list(self.out)


# --- the measurements against v6 ------------------------------------------------------------------------------------
TABLES = (PKG / "pots_tables.h").read_text(encoding="utf-8")
K_BUS = int(re.search(r"#define K_BUS (\d+)", TABLES).group(1))           # the send bus's 1.0 (notes/69 §12.5)
OUT_SCALE = int(re.search(r"#define OUT_GAIN_Q30 (\d+)", TABLES).group(1)) / (1 << 30) * (1 << 29)
LOOP_RATE = SR // _manifest()["build"].get("defines", {}).get("POTS_RATE", 2)

# v6, the float prototype (notes/69 §2, §12.3), with what the port may differ by
V6 = {
    "decay_s": {40: 2.55, 64: 4.85, 90: 20.1, 100: 23.3, 110: None, 127: None},   # None: not dead after 25 s
    "tail_25s": (1491, 0.1),                     # the centroid, % of the energy above 2 kHz
    "colour_hz": [983, 1165, 1286, 1341, 1380, 1415, 1455],
    "octaves_db": {250: -42.8, 500: -8.2, 1000: -1.3, 2000: -9.7, 4000: -32.4},
    "level_db": {"pluck": -27.8, "stab": -32.5},
    "codec_db": {1: (-38.4, -60.6), 3: (-33.2, -62.7), 6: (-26.3, -58.8), 15: (-19.7, -59.0)},
    "peak_127_db": -5.6,
}
# The codec's error has the same power at either rate; at 24 kHz it lies in half the band, so up to 3 dB more of it
# passes the receiver (measured, notes/69 §14.2: +3 dB at 1 to 6 s, nothing at 15 s; the 48 kHz loop within 1 dB of
# v6). The grain is allowed that much more above v6's in the band.
CODEC_RATE_DB = 10 * math.log10(SR / LOOP_RATE)
TOL = {"decay": 0.10, "tail_hz": 0.03, "tail_pct": 1.0, "colour": 0.03, "octave_db": 1.0, "level_db": 1.0,
       "codec_db": 2.0, "peak_db": 0.5, "image_db": 45.0}


def tone(f, dur, decay, bright):
    """A band-limited saw whose upper harmonics die faster (bright: decay rate per harmonic number)."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, int(14000 / f) + 1):
        x += np.sin(2 * math.pi * k * f * t) / k * np.exp(-t * bright * k)
    return x * np.exp(-t / decay) * np.minimum(t / 0.003, 1.0)


def note_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(buf, x, at):
    i = int(at * SR)
    buf[i:i + len(x)] += x[:len(buf) - i]


def norm(x, peak):
    return x * (peak / np.max(np.abs(x)))


def detuned(m, cents):
    return note_hz(m) * 2 ** (cents / 1200)


def src_stab(dur):
    x = np.zeros(int(dur * SR))
    for m in (60, 63, 67, 70):
        for det in (-8, 8):
            place(x, tone(detuned(m, det), 1.2, 0.35, 0.35), 0.2)
    return norm(x, 0.5), 1.0


def src_pluck(dur, at=0.2, repeats=1):
    x = np.zeros(int(dur * SR))
    for r in range(repeats):
        for i, m in enumerate((60, 67, 70, 74, 75, 74, 70, 67)):
            place(x, tone(note_hz(m), 0.8, 0.22, 1.2), at + 2.0 * r + 0.25 * i)
    return norm(x, 0.45), at + 2.0 * repeats


def src_note(dur):
    x = np.zeros(int(dur * SR))
    place(x, tone(note_hz(60), 0.4, 0.15, 0.25), 0.2)
    return norm(x, 0.5), 0.6


def render_bus(x, time, fdbk, off=0, theta_hz=0.0, seed=7):
    """The bus words the slot returns (left channel) for a mono send x on the prototype's scale, put on the bus at
    K_BUS, Time and Fdbk held."""
    n = len(x)
    frames = n + (-n) % BLOCK
    bus = np.zeros((frames, 2), np.int32)
    bus[:n, 0] = bus[:n, 1] = np.clip(np.round(x * K_BUS), -(1 << 31), (1 << 31) - 1)
    params = np.ascontiguousarray(np.tile(np.array([time << 8, fdbk << 8], np.int16), (frames // BLOCK, 1)))
    out = np.zeros_like(bus)
    theta = int(round(2 * math.pi * theta_hz / LOOP_RATE * (1 << 31))) if theta_hz else 0
    load().pots_render(bus.ctypes.data, out.ctypes.data, frames, params.ctypes.data, off, theta, seed)
    return out[:n, 0]


def render(x, time, fdbk, **kw):
    """The return on the prototype's scale (the echo's 6 dB taken off again), to set beside v6's numbers."""
    return render_bus(x, time, fdbk, **kw).astype(float) / OUT_SCALE


def rms_db(x):
    return 20 * math.log10(max(float(np.sqrt(np.mean(np.square(x)))), 1e-12))


def peak_db(x):
    return 20 * math.log10(max(float(np.max(np.abs(x))), 1e-12))


def tail_after(wet, end, floor_db=-60.0):
    """Seconds after end until the 50 ms windows stay below floor_db; None: not before the render ends."""
    win = int(0.05 * SR)
    lv = [rms_db(wet[i:i + win]) for i in range(0, len(wet) - win, win)]
    above = [i for i, v in enumerate(lv) if v > floor_db]
    if not above:
        return 0.0
    last = (above[-1] + 1) * win / SR
    return None if last >= len(wet) / SR - 0.1 else round(last - end, 2)


def spectrum(seg):
    p = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
    return np.fft.rfftfreq(len(seg), 1 / SR), p


def measure():
    m = {}
    t = np.arange(3 * SR) / SR                   # the shift, every other stage off, 10 Hz: up, the other side under
    f, p = spectrum(render(0.3 * np.sin(2 * math.pi * 1000 * t), 31, 0, off=ALL_OFF, theta_hz=10.0)[SR:2 * SR])
    db = lambda hz: 10 * math.log10(p[int(round(hz))] + 1e-30)
    m["shift"] = dict(strongest_hz=int(f[np.argmax(p)]), image_db=round(db(1010) - db(990), 1))
    x, end = src_pluck(30)
    m["decay_s"] = {}
    for fd in V6["decay_s"]:
        w = render(x, 23, fd)
        ts = tail_after(w, end)
        m["decay_s"][fd] = None if ts is None or rms_db(w[-5 * SR:]) > -60 else ts
    w = render(src_pluck(28)[0], 23, 88)
    f, p = spectrum(w[25 * SR:26 * SR])
    m["tail_25s"] = (int(np.sum(f * p) / p.sum()), round(100 * p[f > 2000].sum() / p.sum(), 1))
    w = render(src_note(6)[0], 31, 90)
    m["colour_hz"] = []
    for k in range(7):
        a = int((0.7 + 0.5 * k) * SR)
        f, p = spectrum(w[a:a + int(0.45 * SR)])
        m["colour_hz"].append(int(np.sum(f * p) / max(p.sum(), 1e-30)))
    pl = src_pluck(10)[0]
    w = render(pl, 23, 72)
    f, p = spectrum(w)
    m["octaves_db"] = {c: round(10 * math.log10(p[(f >= c / 2 ** 0.5) & (f < c * 2 ** 0.5)].sum() / p.sum()), 1)
                       for c in V6["octaves_db"]}
    m["level_db"] = {"pluck": round(rms_db(w), 1), "stab": round(rms_db(render(src_stab(12)[0], 31, 88)), 1)}
    x = src_pluck(28)[0]                         # what the codec adds to the tail, in the band and above 4 kHz
    on, off = render(x, 23, 88), render(x, 23, 88, off=D_CODEC)
    m["codec_db"] = {}
    for t0 in V6["codec_db"]:
        a, z = t0 * SR, (t0 + 2) * SR
        f, pd = spectrum(on[a:z] - off[a:z])
        ref = spectrum(off[a:z])[1].sum() + 1e-30
        m["codec_db"][t0] = (round(10 * math.log10(pd[f <= 4000].sum() / ref + 1e-30), 1),
                             round(10 * math.log10(pd[f > 4000].sum() / ref + 1e-30), 1))
    loud, _end = src_pluck(30, repeats=3)
    m["peak_127_db"] = round(peak_db(render(loud / np.max(np.abs(loud)), 23, 127)), 1)
    m["silence_words"] = int(np.max(np.abs(render_bus(np.zeros(5 * SR), 23, 100))))
    m["return_peak_dbfs"] = round(20 * math.log10(np.max(np.abs(render_bus(loud / np.max(np.abs(loud)) * 0.87, 23,
                                                                           127))) / 2 ** 31), 1)
    return m


def against_v6():
    """[(ok, text)]: the measurements of notes/69 §12.3 on the host build, against v6."""
    m, out = measure(), []
    sh = m["shift"]
    out.append((sh["strongest_hz"] == 1010 and sh["image_db"] >= TOL["image_db"],
                f"the shift goes up: a 1 kHz sine, the other stages off, shifted 10 Hz: strongest at "
                f"{sh['strongest_hz']} Hz, the other side {sh['image_db']} dB under (>= {TOL['image_db']:g})"))
    ok = all((m["decay_s"][k] is None) == (v is None) and (v is None or abs(m["decay_s"][k] - v) <= TOL["decay"] * v)
             for k, v in V6["decay_s"].items())
    out.append((ok, "the decay to -60 dB after the pluck phrase, Fdbk " + ", ".join(
        f"{k}: {'> 25' if m['decay_s'][k] is None else m['decay_s'][k]} s "
        f"(v6 {'> 25' if v is None else v})" for k, v in V6["decay_s"].items())
        + f", within {TOL['decay']:.0%}"))
    (hz, pct), (hz6, pct6) = m["tail_25s"], V6["tail_25s"]
    out.append((abs(hz - hz6) <= TOL["tail_hz"] * hz6 and pct <= TOL["tail_pct"],
                f"a tail's end at 25 s: {hz} Hz, {pct} % above 2 kHz (v6 {hz6} Hz, {pct6} %)"))
    ok = all(abs(a - b) <= TOL["colour"] * b for a, b in zip(m["colour_hz"], V6["colour_hz"]))
    out.append((ok, f"the colour, repeats 1 to 7: {m['colour_hz'][0]} -> {m['colour_hz'][-1]} Hz "
                    f"(v6 {V6['colour_hz'][0]} -> {V6['colour_hz'][-1]}), each within {TOL['colour']:.0%}"))
    d = max(abs(m["octaves_db"][c] - v) for c, v in V6["octaves_db"].items())
    out.append((d <= TOL["octave_db"], f"the octave bands 250 Hz to 4 kHz within {d:.1f} dB of v6's "
                                       f"(<= {TOL['octave_db']:g})"))
    ok = all(abs(m["level_db"][k] - v) <= TOL["level_db"] for k, v in V6["level_db"].items())
    out.append((ok, "the echo's level, pluck / stab: " + " / ".join(f"{m['level_db'][k]}" for k in V6["level_db"])
                + " dB (v6 " + " / ".join(f"{v}" for v in V6["level_db"].values()) + ")"))
    ok = all(-TOL["codec_db"] <= m["codec_db"][t][0] - v[0] <= TOL["codec_db"] + CODEC_RATE_DB
             and m["codec_db"][t][1] <= v[1] + TOL["codec_db"] for t, v in V6["codec_db"].items())
    out.append((ok, "the codec's grain in the tail, in the band / above 4 kHz, at " + ", ".join(
        f"{t} s {m['codec_db'][t][0]} / {m['codec_db'][t][1]}" for t in V6["codec_db"]) + " dB (v6 " + ", ".join(
        f"{v[0]} / {v[1]}" for v in V6["codec_db"].values()) + f"): in the band from {TOL['codec_db']:g} dB under "
        f"to {TOL['codec_db'] + CODEC_RATE_DB:.0f} dB over v6's (the loop at {LOOP_RATE // 1000} kHz), above it no "
        f"more than {TOL['codec_db']:g} dB over"))
    out.append((abs(m["peak_127_db"] - V6["peak_127_db"]) <= TOL["peak_db"],
                f"a loud phrase at Fdbk 127: the echo peaks at {m['peak_127_db']} dB (v6 {V6['peak_127_db']})"))
    out.append((m["silence_words"] == 0, f"silence in, 5 s at Fdbk 100: {m['silence_words']} out (exact silence)"))
    return out, m


def main():
    out, m = against_v6()
    for ok, text in out:
        print(f"  {'ok' if ok else 'FAIL'}: {text}")
    print(f"  (the loudest return, SNARE's level at Fdbk 127: {m['return_peak_dbfs']} dBFS on the bus)")
    bad = [t for ok, t in out if not ok]
    print("\nALL OK" if not bad else f"\n{len(bad)} FAILED")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
