"""The RESAMPLE page's screens as the mockup draws them (notes/79 §2.4, §10.2): its three pixel fonts (3 x 5, 4 x 7,
5 x 7, our own, not the OS's) and its coordinates, rows from the top. tools/emu/test_resample.py compares the part's
render (tools/machines/resample/page.c) with these, pixel for pixel. The values are formatted as the part formats them
(the seconds in tenths, cut, not rounded). License: MIT."""

W, H = 128, 64
F3 = {
    "A": "010 101 111 101 101", "B": "110 101 110 101 110", "C": "011 100 100 100 011", "D": "110 101 101 101 110",
    "E": "111 100 110 100 111", "F": "111 100 110 100 100", "G": "011 100 101 101 011", "H": "101 101 111 101 101",
    "I": "111 010 010 010 111", "J": "001 001 001 101 010", "K": "101 101 110 101 101", "L": "100 100 100 100 111",
    "M": "101 111 111 101 101", "N": "110 101 101 101 101", "O": "010 101 101 101 010", "P": "110 101 110 100 100",
    "Q": "010 101 101 111 011", "R": "110 101 110 101 101", "S": "011 100 010 001 110", "T": "111 010 010 010 010",
    "U": "101 101 101 101 111", "V": "101 101 101 101 010", "W": "101 101 111 111 101", "X": "101 101 010 101 101",
    "Y": "101 101 010 010 010", "Z": "111 001 010 100 111", "0": "111 101 101 101 111", "1": "010 110 010 010 111",
    "2": "110 001 010 100 111", "3": "110 001 010 001 110", "4": "101 101 111 001 001", "5": "111 100 110 001 110",
    "6": "011 100 111 101 111", "7": "111 001 010 010 010", "8": "111 101 111 101 111", "9": "111 101 111 001 110",
    "-": "000 000 111 000 000", ".": "000 000 000 000 010", ":": "000 010 000 010 000", "/": "001 001 010 100 100",
    "%": "101 001 010 100 101", "+": "000 010 111 010 000", ">": "100 010 001 010 100", " ": "000 000 000 000 000",
}

F4 = {
    "A": "0110 1001 1001 1111 1001 1001 1001", "B": "1110 1001 1001 1110 1001 1001 1110",
    "C": "0110 1001 1000 1000 1000 1001 0110", "D": "1110 1001 1001 1001 1001 1001 1110",
    "E": "1111 1000 1000 1110 1000 1000 1111", "F": "1111 1000 1000 1110 1000 1000 1000",
    "G": "0110 1001 1000 1011 1001 1001 0111", "H": "1001 1001 1001 1111 1001 1001 1001",
    "I": "1110 0100 0100 0100 0100 0100 1110", "J": "0111 0010 0010 0010 0010 1010 0100",
    "K": "1001 1010 1100 1000 1100 1010 1001", "L": "1000 1000 1000 1000 1000 1000 1111",
    "M": "1001 1111 1111 1001 1001 1001 1001", "N": "1001 1101 1101 1011 1011 1001 1001",
    "O": "0110 1001 1001 1001 1001 1001 0110", "P": "1110 1001 1001 1110 1000 1000 1000",
    "Q": "0110 1001 1001 1001 1011 1010 0101", "R": "1110 1001 1001 1110 1100 1010 1001",
    "S": "0111 1000 1000 0110 0001 0001 1110", "T": "1110 0100 0100 0100 0100 0100 0100",
    "U": "1001 1001 1001 1001 1001 1001 0110", "V": "1001 1001 1001 1001 1001 0110 0110",
    "W": "1001 1001 1001 1001 1111 1111 1001", "X": "1001 1001 0110 0110 0110 1001 1001",
    "Y": "1010 1010 1010 0100 0100 0100 0100", "Z": "1111 0001 0010 0100 1000 1000 1111",
    "0": "0110 1001 1011 1101 1001 1001 0110", "1": "0100 1100 0100 0100 0100 0100 1110",
    "2": "0110 1001 0001 0010 0100 1000 1111", "3": "1110 0001 0001 0110 0001 0001 1110",
    "4": "0010 0110 1010 1010 1111 0010 0010", "5": "1111 1000 1110 0001 0001 1001 0110",
    "6": "0110 1000 1000 1110 1001 1001 0110", "7": "1111 0001 0010 0010 0100 0100 0100",
    "8": "0110 1001 1001 0110 1001 1001 0110", "9": "0110 1001 1001 0111 0001 0001 0110",
    "-": "0000 0000 0000 1110 0000 0000 0000", ".": "0000 0000 0000 0000 0000 1100 1100",
    " ": "0000 0000 0000 0000 0000 0000 0000",
}

F5 = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110", "D": "11100 10010 10001 10001 10001 10010 11100",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 10001 11001 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 10001 01010 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    "-": "00000 00000 00000 11111 00000 00000 00000", ".": "00000 00000 00000 00000 00000 01100 01100",
    ":": "00000 01100 01100 00000 01100 01100 00000", "/": "00000 00001 00010 00100 01000 10000 00000",
    "%": "11000 11001 00010 00100 01000 10011 00011", "+": "00000 00100 00100 11111 00100 00100 00000",
    " ": "00000 00000 00000 00000 00000 00000 00000",
}


def blank():
    return [[0] * W for _ in range(H)]


def px(fb, x, y, v=1):
    if 0 <= x < W and 0 <= y < H:
        fb[y][x] = v


def fill(fb, x0, y0, x1, y1, v=1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(fb, x, y, v)


def rect(fb, x0, y0, x1, y1):
    for x in range(x0, x1 + 1):
        px(fb, x, y0)
        px(fb, x, y1)
    for y in range(y0, y1 + 1):
        px(fb, x0, y)
        px(fb, x1, y)


def hdots(fb, y, x0=0, x1=W - 1):
    for x in range(x0, x1 + 1, 2):
        px(fb, x, y)


FONTS = {3: (F3, 3, 4), 4: (F4, 4, 5), 5: (F5, 5, 6)}


def text(fb, f, x, y, s, sc=1, v=1):
    glyphs, w, adv = FONTS[f]
    for ch in s.upper():
        g = glyphs.get(ch, glyphs[" "]).split()
        for yy, row in enumerate(g):
            for xx in range(w):
                if row[xx] == "1":
                    fill(fb, x + xx * sc, y + yy * sc, x + xx * sc + sc - 1, y + yy * sc + sc - 1, v)
        x += adv * sc


def width(f, s, sc=1):
    return (len(s) * FONTS[f][2] - 1) * sc


def centre(fb, f, y, s, sc=1):
    text(fb, f, (W - width(f, s, sc)) // 2, y, s, sc)


def right(fb, f, xr, y, s):
    text(fb, f, xr - width(f, s) + 1, y, s)


def header(fb, label=None, inv=False):
    text(fb, 5, 2, 1, "RESAMPLE")
    if label:
        w = width(3, label)
        x = 125 - w + 1
        if inv:
            fill(fb, x - 2, 1, x + w + 1, 7)
        text(fb, 3, x, 2, label, 1, 0 if inv else 1)
    hdots(fb, 10)


def footer(fb, left, right_):
    hdots(fb, 49)
    if left:
        text(fb, 3, 2, 54, left)
    if right_:
        right(fb, 3, 125, 54, right_)


def db_x(down):
    """dB below full scale as the meter's x: 4 + round((60 - down) / 60 * 119)."""
    return 4 + ((60 - min(down, 60)) * 238 + 60) // 120


def meter(fb, y, down, thr=None, labels=False):
    rect(fb, 3, y, 124, y + 6)
    if down < 60:
        fill(fb, 4, y + 1, db_x(down), y + 5)
    if thr is not None:
        xt = db_x(thr)
        for yy in (y - 2, y - 1, y + 7, y + 8):
            px(fb, xt, yy)
        for yy in range(y + 1, y + 6):
            px(fb, xt, yy, 0 if fb[yy][xt] else 1)
    if labels:
        text(fb, 3, 3, y + 10, "-60")
        centre(fb, 3, y + 10, "-30")
        right(fb, 3, 124, y + 10, "0DB")


SOURCES = ["T1", "T2", "T3", "T4", "T5", "T6", "MAIN", "USB"]
STARTS = ["TRIG", "LEVEL", "NOW"]
STOPS = ["SILENT", "LENGTH", "RECORD"]


def secs(frames):
    t = frames // 4800
    return f"{t // 10}.{t % 10}S" if t < 100 else f"{t // 10}S"


def ends(stop, limit, recording):
    if stop == 0:
        return "STOPS WHEN SILENT"
    if stop == 1:
        return ("OF " if recording else "STOPS AT ") + f"{limit // 48000}S"
    return "RECORD STOPS"


def idle(src, start, thr, stereo, stop, length, norm, selected, to_track_ok, to_track):
    """start as it applies (USB: TRIG shown as LEVEL); thr in dB below full scale; selected the track 0..5."""
    fb = blank()
    header(fb)
    cells = [("SOURCE", SOURCES[src]), ("START", STARTS[start]), ("THRESH", f"-{thr}DB" if start == 1 else "---"),
             ("STEREO", "---" if src < 6 else "ON" if stereo else "OFF"), ("STOP", STOPS[stop]),
             ("LENGTH", f"{length}S"), ("NORM", "ON" if norm else "OFF"),
             (f"TO T{selected + 1}", "---" if not to_track_ok else "YES" if to_track else "NO")]
    for i, (lab, val) in enumerate(cells):
        x, ly = (i % 4) * 32 + 1, 13 if i < 4 else 31
        text(fb, 3, x, ly, lab)
        text(fb, 4, x, ly + 7, val)
    footer(fb, "RECORD: ARM", "RETURN: CLOSE")
    return fb


def armed(src, stereo, start, stop, limit, thr, down):
    fb = blank()
    header(fb, "ARMED")
    centre(fb, 5, 15, "WAIT FOR LEVEL" if start == 1 else "WAIT FOR TRIG")
    centre(fb, 3, 26, SOURCES[src] + (" STEREO" if stereo else " MONO") + "    " + ends(stop, limit, False))
    meter(fb, 33, down, thr if start == 1 else None, True)
    footer(fb, "RECORD: CANCEL", "RETURN: CLOSE")
    return fb


def recording(frames, limit, stop, clip, down):
    fb = blank()
    header(fb, "REC", True)
    centre(fb, 5, 13, secs(frames), 2)
    centre(fb, 3, 29, ends(stop, limit, True) + ("  CLIP" if clip else ""))
    meter(fb, 35, down)
    hdots(fb, 45, 4, 123)
    most = limit or 1
    fill(fb, 4, 44, 4 + (min(frames, most) * 238 + most) // (2 * most), 45)
    footer(fb, "RECORD: STOP", "RETURN: STOP")
    return fb


def taken(frames, stereo):
    fb = blank()
    header(fb, "UNSAVED")
    centre(fb, 5, 16, "NOT SAVED")
    centre(fb, 3, 28, secs(frames) + ("  STEREO" if stereo else "  MONO") + "  IN MEMORY")
    footer(fb, None, "RETURN: DISCARD")
    return fb


def ascii(fb):
    return "\n".join("".join("#" if v else "." for v in row) for row in fb)
