#!/usr/bin/env python3
"""Turns a wavetable WAV into a file CHORD Tables plays (notes/66 §4, step W5).

CHORD Tables reads /Wavetables/01 to /Wavetables/64 on the +Drive: mono sample files of k x 256 samples, k single-cycle
frames, k = 1 to 32. The stock CHORD frames have nothing above harmonic 40, are at full level, and start on a rising
zero crossing with their neighbours in phase, so that SWEEP's crossfade between two frames does not dip. This tool
makes any wavetable WAV like that:

  1. reads a WAV (8, 16, 24 or 32-bit integer PCM or 32-bit float, any number of channels, mixed to mono) and cuts it
     into frames of --frame samples (2 048, the common wavetable size, when the length allows it, else 256);
  2. keeps 32 frames at most (--frames), evenly picked;
  3. for each frame, takes harmonics 1 to --harmonics (40) by a discrete Fourier transform and synthesises 256
     samples from them: no DC, nothing above the last harmonic, whatever the input's frame size;
  4. turns each frame so that its fundamental starts in sine phase (0, rising), the same for every frame
     (--no-align leaves the phases);
  5. scales each frame to full level (--keep-levels scales the whole table once, keeping the frames' relative levels);
  6. writes a 48 kHz mono 16-bit WAV of k x 256 samples (-o), for One-Shot's uploader, which keeps a 48 kHz WAV's length
     (notes/66 §11.4), and/or the +Drive's sample file (--device): the 64-byte header, the frames big-endian, 16 zero
     bytes, as the uploader writes it and the loader reads it.

Name the files on the +Drive 01 to 64 in a folder Wavetables (the uploader makes the folder and keeps the typed name).

    python3 tools/wavetable.py table.wav -o 01.wav [--device 01.smp] [--frame 2048] [--frames 32] [--harmonics 40]
                               [--no-align] [--keep-levels]
    python3 tools/wavetable.py --self-test

Plain Python, no extra package.
"""
import argparse
import cmath
import math
import pathlib
import struct
import sys

CYCLE = 256                 # samples of a frame on the +Drive
MAX_FRAMES = 32             # frames the loader takes
FULL = 32767
RATE = 48000


# --- WAV in and out ---------------------------------------------------------------------------------------------------
def read_wav(data):
    """RIFF/WAVE bytes -> (rate, mono samples as floats in -1..1)."""
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("not a RIFF/WAVE file")
    pos, fmt, pcm = 12, None, None
    while pos + 8 <= len(data):
        cid, size = data[pos:pos + 4], struct.unpack_from("<I", data, pos + 4)[0]
        body = data[pos + 8:pos + 8 + size]
        if cid == b"fmt ":
            tag, chans, rate, _br, _ba, bits = struct.unpack_from("<HHIIHH", body)
            if tag == 0xFFFE and len(body) >= 26:
                tag = struct.unpack_from("<H", body, 24)[0]     # WAVE_FORMAT_EXTENSIBLE: the sub-format
            fmt = (tag, chans, rate, bits)
        elif cid == b"data":
            pcm = body
        pos += 8 + size + (size & 1)
    if not fmt or pcm is None:
        raise ValueError("no fmt or data chunk")
    tag, chans, rate, bits = fmt
    width = bits // 8
    if tag not in (1, 3) or chans < 1 or (tag == 3 and bits != 32) or (tag == 1 and width not in (1, 2, 3, 4)):
        raise ValueError(f"unsupported WAV: format {tag}, {bits} bits")
    n = len(pcm) // (width * chans)
    out = []
    for i in range(n):
        acc = 0.0
        for c in range(chans):
            p = (i * chans + c) * width
            if tag == 3:
                v = struct.unpack_from("<f", pcm, p)[0]
            elif width == 1:
                v = (pcm[p] - 128) / 128.0
            elif width == 2:
                v = struct.unpack_from("<h", pcm, p)[0] / 32768.0
            elif width == 3:
                v = int.from_bytes(pcm[p:p + 3], "little", signed=True) / 8388608.0
            else:
                v = struct.unpack_from("<i", pcm, p)[0] / 2147483648.0
            acc += v
        out.append(acc / chans)
    return rate, out


def wav_bytes(samples, rate=RATE):
    """48 kHz mono 16-bit WAV."""
    pcm = struct.pack(f"<{len(samples)}h", *samples)
    fmt = struct.pack("<HHIIHH", 1, 1, rate, rate * 2, 2, 16)
    return (b"RIFF" + struct.pack("<I", 4 + 8 + len(fmt) + 8 + len(pcm)) + b"WAVE" + b"fmt " +
            struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(pcm)) + pcm)


def device_bytes(samples):
    """The +Drive's sample file: a 64-byte header (+1 0 = mono, +4 bytes of audio, +8 rate, +16 last frame, +20 0x7f =
    no loop; big-endian), the frames as big-endian 16-bit, 16 zero bytes (One-Shot TECHNICAL §7)."""
    head = bytearray(64)
    struct.pack_into(">III", head, 4, 2 * len(samples), RATE, 0)
    struct.pack_into(">I", head, 16, len(samples) - 1)
    head[20] = 0x7f
    return bytes(head) + struct.pack(f">{len(samples)}h", *samples) + bytes(16)


def loader_accepts(data):
    """What CHORD Tables' loader takes (tools/machines/chordtables/chordtables.c, load_one): mono, k x 256 samples,
    k = 1 to 32, the file at least as long as its header says. -> frames k, or 0."""
    if len(data) < 64:
        return 0
    n = struct.unpack_from(">I", data, 4)[0]
    if data[1] or not n or n % (2 * CYCLE) or n > 2 * CYCLE * MAX_FRAMES or len(data) < 64 + n:
        return 0
    return n // (2 * CYCLE)


# --- the frames ---------------------------------------------------------------------------------------------------------
def harmonics(frame, count):
    """Complex amplitudes of harmonics 1..count of one cycle (x = sum of Re(c_h e^(i h t)))."""
    n = len(frame)
    out = []
    for h in range(1, count + 1):
        if 2 * h >= n:
            out.append(0j)
            continue
        acc = 0j
        w = -2j * math.pi * h / n
        for m, x in enumerate(frame):
            acc += x * cmath.exp(w * m)
        out.append(2 * acc / n)
    return out


def synth(coef, n=CYCLE):
    out = []
    for m in range(n):
        t = 2 * math.pi * m / n
        out.append(sum((c * cmath.exp(1j * h * t)).real for h, c in enumerate(coef, 1)))
    return out


def align(coef, prev_turn):
    """Turns a frame so that its fundamental is in sine phase (starts at 0, rising): c_h * e^(-i h a), with a chosen so
    that arg(c_1) becomes -pi/2. Without a fundamental, the previous frame's turn. -> (coefficients, turn)."""
    if abs(coef[0]) > 1e-6 * max(abs(c) for c in coef):
        turn = cmath.phase(coef[0]) + math.pi / 2
    else:
        turn = prev_turn
    return [c * cmath.exp(-1j * h * turn) for h, c in enumerate(coef, 1)], turn


def convert(samples, frame=None, frames=None, count=40, do_align=True, keep_levels=False):
    """Mono samples (floats) -> (the table, k x 256 16-bit samples; a report)."""
    n = len(samples)
    if frame is None:
        frame = 2048 if n >= 2048 and n % 2048 == 0 else CYCLE
    if n < frame or n % frame:
        raise ValueError(f"{n} samples are not whole frames of {frame}: give --frame")
    total = n // frame
    k = min(total, frames or MAX_FRAMES, MAX_FRAMES)
    picks = [round(j * (total - 1) / (k - 1)) for j in range(k)] if k > 1 else [0]
    shapes, turn = [], 0.0
    for p in picks:
        coef = harmonics(samples[p * frame:(p + 1) * frame], count)
        if do_align:
            coef, turn = align(coef, turn)
        shapes.append(synth(coef))
    peaks = [max(abs(x) for x in s) or 1.0 for s in shapes]
    gains = [FULL / max(peaks)] * k if keep_levels else [FULL / p for p in peaks]
    table = []
    for s, g in zip(shapes, gains):
        table += [max(-32768, min(FULL, int(round(x * g)))) for x in s]
    report = (f"{n} samples, frames of {frame}: {total} frame(s), {k} kept"
              + (f" (frames {picks})" if k < total else "") + f"; harmonics 1 to {count}"
              + ("; phases aligned" if do_align else "") + ("; levels kept" if keep_levels else "; each frame at full level"))
    return table, report


# --- the self-test --------------------------------------------------------------------------------------------------------
def self_test():
    fails = []

    def case(name, ok):
        print(("ok    " if ok else "FAIL  ") + name)
        if not ok:
            fails.append(name)

    def saw(n, phase, top=200):
        return [sum(math.sin(h * (2 * math.pi * m / n + phase)) / h for h in range(1, top)) * 0.5 for m in range(n)]

    # a saw table of 4 frames of 2048 samples, each frame turned another way, harmonics up to 199
    src = []
    for j in range(4):
        src += saw(2048, 0.7 * j)
    table, rep = convert(src)
    case(f"a 2048-sample table of 4 frames: 4 x 256 samples ({rep})", len(table) == 4 * CYCLE)
    frames_ = [table[i * CYCLE:(i + 1) * CYCLE] for i in range(4)]
    spectra = [[abs(c) for c in harmonics([x / FULL for x in f], 127)] for f in frames_]
    case("nothing above harmonic 40 but rounding (under 3e-4 of full level), no DC",
         all(max(s[40:]) < 3e-4 for s in spectra) and all(abs(sum(f)) / CYCLE < 2 for f in frames_))
    case("each frame at full level", all(max(abs(x) for x in f) == FULL for f in frames_))
    fund = [cmath.phase(harmonics([x / FULL for x in f], 1)[0]) for f in frames_]
    case("every frame's fundamental in sine phase (neighbours in phase)", all(abs(p + math.pi / 2) < 1e-3 for p in fund))
    case("each frame starts on a rising zero crossing", all(abs(f[0]) < 0.02 * FULL and f[1] > f[0] for f in frames_))
    dev = device_bytes(table)
    case("the device file: 64-byte header, mono, 2 048 bytes of audio, 48 kHz, last frame 1 023, no loop, 16 zeros",
         len(dev) == 64 + 2048 + 16 and dev[1] == 0 and struct.unpack_from(">III", dev, 4) == (2048, RATE, 0)
         and struct.unpack_from(">I", dev, 16)[0] == 1023 and dev[20] == 0x7f and dev[-16:] == bytes(16)
         and struct.unpack_from(">h", dev, 64)[0] == table[0])
    case("the loader takes it: 4 frames", loader_accepts(dev) == 4)
    case("the loader refuses a stereo file, 300 samples and 33 frames",
         loader_accepts(dev[:1] + b"\x01" + dev[2:]) == 0 and loader_accepts(device_bytes([0] * 300)) == 0
         and loader_accepts(device_bytes([0] * 33 * CYCLE)) == 0)
    # a 256-sample table under 40 harmonics comes back as it was, but for its level
    small = []                                                      # 768 samples: frames of 256 (no 2048 fits)
    for j in range(3):
        small += [math.sin(2 * math.pi * m / CYCLE + math.pi * 0) * (1 - j / 4) + 0.3 * math.sin(6 * math.pi * m / CYCLE)
                  for m in range(CYCLE)]
    out, _r = convert(small, do_align=False, keep_levels=True)
    g = FULL / max(abs(x) for x in small)
    case("256-sample frames with 3 harmonics, phases and levels kept: the same samples, scaled once",
         all(abs(o - x * g) <= 1 for o, x in zip(out, small)))
    # 64 frames: 32 kept, evenly
    many = []
    for j in range(64):
        many += [math.sin(2 * math.pi * m / CYCLE) * (1 + j) for m in range(CYCLE)]
    out, rep = convert(many, frame=CYCLE, keep_levels=True)        # 16 384 samples would read as 8 x 2048
    lv = [max(abs(x) for x in out[i * CYCLE:(i + 1) * CYCLE]) for i in range(32)]
    case(f"64 frames: 32 kept, the first and the last among them ({rep[:60]}...)",
         len(out) == 32 * CYCLE and lv[-1] == FULL and abs(lv[0] - FULL / 64) <= 1 and lv == sorted(lv))
    # WAV in: 16-bit stereo, 24-bit, float; WAV out
    w16 = wav_bytes(table)
    rate, back = read_wav(w16)
    case("our WAV read back: 48 kHz, the same samples", rate == RATE and [round(x * 32768) for x in back] == table)
    st = bytearray(w16)
    pcm = struct.pack(f"<{2 * len(table)}h", *[v for x in table for v in (x, x)])
    st = (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 2, 44100, 44100 * 4, 4,
          16) + b"data" + struct.pack("<I", len(pcm)) + pcm)
    _r, back = read_wav(bytes(st))
    case("a 16-bit stereo WAV at 44.1 kHz: mixed to mono, the same samples (single cycles have no rate)",
         [round(x * 32768) for x in back] == table)
    p24 = b"".join(int(x * 256).to_bytes(3, "little", signed=True) for x in table)
    w24 = (b"RIFF" + struct.pack("<I", 36 + len(p24)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 1, 1, RATE, RATE * 3, 3,
           24) + b"data" + struct.pack("<I", len(p24)) + p24)
    pf = struct.pack(f"<{len(table)}f", *[x / 32768 for x in table])
    wf = (b"RIFF" + struct.pack("<I", 36 + len(pf)) + b"WAVEfmt " + struct.pack("<IHHIIHH", 16, 3, 1, RATE, RATE * 4, 4,
          32) + b"data" + struct.pack("<I", len(pf)) + pf)
    case("24-bit and 32-bit float WAVs read as the 16-bit one",
         [round(x * 32768) for x in read_wav(w24)[1]] == table and [round(x * 32768) for x in read_wav(wf)[1]] == table)
    print("ALL OK" if not fails else f"{len(fails)} FAIL")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("wav", nargs="?", help="the wavetable WAV")
    ap.add_argument("-o", "--out", help="the 48 kHz mono 16-bit WAV to write, for the uploader")
    ap.add_argument("--device", help="the +Drive sample file to write (digiemu, or a check against the loader)")
    ap.add_argument("--frame", type=int, help="samples per frame in the input (default 2048 when the length allows, "
                                              "else 256)")
    ap.add_argument("--frames", type=int, help=f"frames to keep, evenly picked (at most {MAX_FRAMES})")
    ap.add_argument("--harmonics", type=int, default=40, help="the last harmonic kept (default 40, as the stock frames)")
    ap.add_argument("--no-align", action="store_true", help="leave each frame's phase as it is")
    ap.add_argument("--keep-levels", action="store_true", help="one gain for the table instead of each frame at full level")
    ap.add_argument("--self-test", action="store_true", help="run the checks on synthetic tables")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.wav or not (a.out or a.device):
        ap.error("give a WAV and -o and/or --device (or --self-test)")
    if a.frames is not None and not 1 <= a.frames <= MAX_FRAMES:
        ap.error(f"--frames: 1 to {MAX_FRAMES}")
    if not 1 <= a.harmonics < CYCLE // 2:
        ap.error("--harmonics: 1 to 127")
    _rate, samples = read_wav(pathlib.Path(a.wav).read_bytes())
    table, report = convert(samples, a.frame, a.frames, a.harmonics, not a.no_align, a.keep_levels)
    print(f"{a.wav}: {report}")
    if a.out:
        pathlib.Path(a.out).write_bytes(wav_bytes(table))
        print(f"  wrote {a.out}: {len(table)} samples, 48 kHz mono 16-bit")
    if a.device:
        dev = device_bytes(table)
        if not loader_accepts(dev):
            sys.exit("!! the loader would refuse this file")
        pathlib.Path(a.device).write_bytes(dev)
        print(f"  wrote {a.device}: {len(dev)} bytes, {len(table) // CYCLE} frame(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
