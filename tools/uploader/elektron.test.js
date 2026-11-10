/* Host tests of the uploader's protocol and file format (docs/uploader/elektron.js): tools/webuploader_check.sh */
"use strict";
const E = require("../../docs/uploader/elektron.js");

let failures = 0;
function check(cond, what) {
    if (!cond) {
        failures++;
        console.log("FAIL: " + what);
    }
}
function same(a, b) {
    if (a.length !== b.length)
        return false;
    for (let i = 0; i < a.length; i++)
        if (a[i] !== b[i])
            return false;
    return true;
}
function rand(n, seed) {
    const out = new Uint8Array(n);
    let x = seed;
    for (let i = 0; i < n; i++) {
        x = (x * 1103515245 + 12345) >>> 0;
        out[i] = x >>> 24;
    }
    return out;
}

/* 7-bit packing */
check(same(E.encode7([0x80, 0x01]), [0x40, 0x00, 0x01]), "the first byte's top bit goes into bit 6");
check(same(E.encode7([1, 2, 3, 4, 5, 6, 0xff, 0x81]), [0x01, 1, 2, 3, 4, 5, 6, 0x7f, 0x40, 0x01]),
      "the 7th byte's top bit goes into bit 0; a new group starts after 7");
for (let n = 0; n <= 60; n++) {
    const src = rand(n, n + 1), enc = E.encode7(src);
    check(enc.length === n + Math.ceil(n / 7), "length of " + n + " bytes packed: " + enc.length);
    check(enc.every(b => b < 0x80), "packed bytes stay below 0x80 (" + n + ")");
    check(same(E.decode7(enc), src), "unpacking gives the bytes back (" + n + ")");
}
{
    const big = rand(E.BLOCK + 20, 99);
    check(same(E.decode7(E.encode7(big)), big), "a whole write block survives packing");
}

/* framing and messages */
{
    const msg = E.request(0x1234, E.TYPE.OPEN_WRITE, [1, 2, 0x80]);
    check(same(msg, [0x12, 0x34, 0, 0, 0x43, 1, 2, 0x80]), "request: sequence, two zeros, type, body");
    const sx = E.frame(msg);
    check(same(sx.slice(0, 6), E.HEADER) && sx[sx.length - 1] === 0xf7, "frame: Elektron header and F7");
    check(same(E.unframe(sx), msg), "unframe gives the message back");
    const other = Uint8Array.from(sx);
    other[4] = 0x11;
    check(E.unframe(other) === null, "another header is not ours");
    check(E.unframe(sx.slice(0, -1)) === null, "a SysEx without F7 is not ours");
    const reply = new Uint8Array([0, 7, 0x12, 0x34, 0xc3, 1, 0, 0, 0, 9]);
    check(E.replySeq(reply) === 0x1234 && E.replyOk(reply) && E.readU32(reply, 6) === 9,
          "a reply: our sequence in bytes 2..3, status 1, then the file's id");
    const refusal = new Uint8Array([0, 8, 0, 1, 0xc3].concat([0], Array.from(Buffer.from("No space")), [0]));
    check(!E.replyOk(refusal) && E.replyText(refusal) === "No space", "a refusal and its text");
}
check(same(E.u32(0x01020304), [1, 2, 3, 4]) && E.readU32([0xff, 0xfe, 0xfd, 0xfc], 0) === 0xfffefdfc,
      "u32 big-endian both ways");

/* text and paths */
check(same(E.encodeText("Kick é€"), [0x4b, 0x69, 0x63, 0x6b, 0x20, 0xe9, 0x80]), "Windows-1252, € as 0x80");
check(same(E.encodeText("日"), [0x3f]), "what Windows-1252 cannot hold becomes ?");
check(E.decodeText([0x4b, 0xe9, 0x80]) === "Ké€", "and back");
check(same(E.pathBytes("/a"), [0x2f, 0x61, 0]), "a path ends with a 0");
check(E.normalizePath("samples//kicks/") === "/samples/kicks" && E.normalizePath("") === "/", "normalized paths");
check(E.joinPath("/", "x") === "/x" && E.joinPath("/a", "x") === "/a/x", "joined paths");
check(E.parentPath("/a/b") === "/a" && E.parentPath("/a") === "/" && E.parentPath("/") === "/", "parent folders");
check(E.cleanName("kick 01.wav") === "kick 01", "the name drops the extension");
check(E.cleanName("a/b\\c.aif") === "a_b_c", "no slashes in a name");
check(E.cleanName("x".repeat(80) + ".wav").length === E.NAME_MAX, "names stop at " + E.NAME_MAX);

/* folder listing */
{
    const entry = (hash, size, prot, type, name) =>
        E.u32(hash).concat(E.u32(size), [prot, type], E.encodeText(name), [0]);
    const m = new Uint8Array([0, 1, 0, 2, 0x94].concat(
        entry(0, 0, 1, 0x44, "factory"), entry(0, 0, 0, 0x44, "incoming"), entry(0x1235, 281330, 0, 0x46, "Kick é")));
    const items = E.parseDir(m);
    check(items.length === 3, "three entries");
    check(items[0].folder && items[0].writeProtected && items[0].name === "factory", "a protected folder");
    check(items[1].folder && !items[1].writeProtected, "a folder");
    check(!items[2].folder && items[2].size === 281330 && items[2].hash === 0x1235 && items[2].name === "Kick é",
          "a file with size, hash and name");
    let threw = false;
    try { E.parseDir(m.slice(0, m.length - 1)); } catch (e) { threw = true; }
    check(threw, "a listing cut short is refused");
}

/* audio and the sample file */
{
    const mixed = E.mixDown([Float32Array.from([1, 0.5]), Float32Array.from([0, -0.5])]);
    check(mixed[0] === 0.5 && mixed[1] === 0, "channels are averaged");
    const q = E.toInt16(Float32Array.from([1, -1, 0.5, -0.25, 2, -2, 0.00001]));
    check(same(q, [32767, -32768, 16384, -8192, 32767, -32768, 0]), "16-bit: rounded and clipped");

    const frames = Int16Array.from([0, 1, -1, 32767, -32768]);
    const f = E.sampleFile(frames, E.RATE);
    const dv = new DataView(f.buffer);
    check(f.length === 64 + 10 + 16, "header, frames and 16 zero bytes");
    check(f[0] === 0 && f[1] === 0, "mono");
    check(dv.getUint32(4) === 10 && dv.getUint32(8) === 48000 && dv.getUint32(16) === 4 && f[20] === 0x7f,
          "header: audio bytes, rate, last frame, no loop");
    check(dv.getInt16(64) === 0 && dv.getInt16(66) === 1 && dv.getInt16(68) === -1 && dv.getInt16(70) === 32767 &&
          dv.getInt16(72) === -32768, "frames big-endian");
    check(f.slice(74).every(b => b === 0), "16 zero bytes at the end");

    /* what SAMPLE's parse_header (machine/pool.c) takes: even length, all of it in the file, a rate
       between 4 and 192 kHz */
    const len = dv.getUint32(4), rate = dv.getUint32(8);
    check(len > 0 && !(len & 1) && len <= f.length - 64 && rate >= 4000 && rate <= 192000, "SAMPLE accepts the header");
}

/* a table's first frame, for CHORD Tables (model27 notes/66 §16): a sine in sine phase, or not */
{
    const frame = (f) => Int16Array.from({ length: E.CYCLE }, (_, k) => Math.round(32767 * f(2 * Math.PI * k / E.CYCLE)));
    const sine = frame(Math.sin), table = Int16Array.from([...sine, ...frame(t => (t / Math.PI) - 1)]);
    check(E.startsWithSine(sine) && E.startsWithSine(table), "a sine, and a table that starts with one, start with a sine");
    const lsb = Int16Array.from(sine, (v, k) => v + (k % 3) - 1);
    check(E.startsWithSine(lsb), "a sine one step off here and there (the browser's rounding) still is one");
    check(!E.startsWithSine(frame(Math.cos)), "a cosine is not a sine in sine phase");
    check(!E.startsWithSine(frame(t => 0.9 * Math.sin(t) + 0.1 * Math.sin(2 * t))), "a sine with harmonic 2 is not");
    check(!E.startsWithSine(frame(t => (t / Math.PI) - 1)), "a saw is not");
    check(!E.startsWithSine(frame(t => 0.5 * Math.sin(t) + 0.1)), "a sine with DC is not");
    check(!E.startsWithSine(sine.slice(0, 200)), "fewer than 256 samples are not");
    check(E.WAVETABLES === "/Wavetables", "the folder CHORD Tables reads");
    const n = (len) => E.tableFrames(new Int16Array(len));
    check(n(256) === 1 && n(512) === 2 && n(32 * 256) === 32, "1, 2 and 32 frames of 256: what CHORD Tables plays");
    check(n(0) === 0 && n(300) === 0 && n(33 * 256) === 0 && n(48000) === 0 && n(255) === 0,
          "nothing, 300, 33 frames, 48000 (a second of sound) and 255 samples: it cannot play them");
}

/* CHORD Tables 0.4's names (number() and before() in chordtables.c, notes/66 §36.3): the same 17 cases as on the host */
{
    const want = { "07": 7, "07 Glass Pad": 7, "07-glass": 7, "07.wav": 7, "01": 1, "63": 63, "63 x": 63, "7 Glass": 0,
                   "070": 0, "64 Pad": 0, "00": 0, "0": 0, "": 0, "Glass 07": 0, "6": 0, "99": 0, "7": 0 };
    const got = Object.keys(want).filter(k => E.tableNumber(k) !== want[k]);
    check(!got.length && E.TABLES === 63, "a name's table: 07, 07 Glass Pad, 07-glass, 07.wav, 01, 63, 63 x; nothing for " +
          "7 Glass, 070, 64 Pad, 00, 0, an empty name, Glass 07, 6, 99, 7" + (got.length ? "; wrong: " + got : ""));
    check(E.playsFirst("07 Glass", "07 Pad") < 0 && E.playsFirst("07 Pad", "07 Glass") > 0 && E.playsFirst("07", "07") === 0 &&
          E.playsFirst("07", "07 a") < 0 && E.playsFirst("07 Pad", "07 pad") < 0 && E.playsFirst("07 Z", "07 é") < 0,
          "byte order: Glass before Pad, a name before a longer one that starts with it, capitals before small " +
          "letters, é (0xe9) after Z");
}

/* audio files (release 0.57): what a file is from its bytes, and the WAV the browser gets for an AIFF */
{
    const A = require("./audiofiles.js");
    const kind = (bytes) => E.audioInfo(Uint8Array.from(bytes)).kind;
    check(kind([]) === "empty", "no bytes: empty");
    check(kind(A.ascii("fLaC\0\0\0\x22")) === "flac" && kind([...A.ascii("OggS"), ...new Array(24).fill(0), ...A.ascii("\x01vorbis")]) === "ogg" &&
          kind([...A.ascii("OggS"), ...new Array(24).fill(0), ...A.ascii("OpusHead")]) === "opus" &&
          kind([0, 0, 0, 0x20, ...A.ascii("ftypM4A ")]) === "m4a" && kind(A.ascii("ID3\x04\0")) === "mp3" &&
          kind([0xff, 0xfb, 0x90, 0x64]) === "mp3" && kind([0xff, 0xf1, 0x50, 0x80]) === "aac",
          "FLAC, OGG, Opus, M4A, MP3 with an ID3 tag or a frame, AAC (ADTS) by their first bytes");
    check(kind(A.ascii("RIFF\0\0\0\0AVI LIST")) === "unknown" && kind(A.ascii("MThd\0\0\0\x06")) === "unknown" &&
          kind([0x52, 1, 2]) === "unknown", "a RIFF that is no WAVE, a MIDI file, three bytes: unknown");

    /* an AIFF as the forum's file: mono, 16 bits, 48 kHz; big-endian samples become little-endian */
    const s16 = [0, 1, -1, 32767, -32768, 12345, -12345];
    const be = s16.flatMap(v => A.be16(v & 0xffff)), le = s16.flatMap(v => A.le16(v & 0xffff));
    let f = A.aiff({ frames: 7, data: be }), info = E.audioInfo(f), w = E.toWav(f, info), h = A.wavHeader(w);
    check(info.kind === "aiff" && info.channels === 1 && info.rate === 48000 && info.frames === 7 && !info.compressed &&
          !info.broken && info.layout.order === "be" && info.layout.type === "int" && info.layout.bytes === 2,
          "AIFF 16 bits: one channel, 48000, 7 frames, big-endian: " + JSON.stringify(info));
    check(h.riff === "RIFF" && h.wave === "WAVE" && h.fmt === "fmt " && h.fmtLen === 16 && h.data === "data" &&
          h.size === w.length - 8 && h.tag === 1 && h.ch === 1 && h.rate === 48000 && h.byteRate === 96000 && h.align === 2 &&
          h.bits === 16 && h.dataLen === 14 && w.length === 44 + 14 + 0, "its WAV header: PCM, 1 channel, 48000, 16 bits, 14 bytes");
    check(w.length === 58 && same(w.slice(44), le), "its samples, little-endian, as they were");
    check(E.framesAt(info, 48000) === 7 && E.framesAt({ frames: 441, rate: 44100 }, 48000) === 480 &&
          E.framesAt({ frames: null, rate: 44100 }, 48000) === null && E.framesAt({ kind: "mp3" }, 48000) === null,
          "frames at 48 kHz: as many, 441 at 44.1 kHz make 480, none known for a file without a header");

    /* 8 bits: AIFF's are signed, WAV's unsigned */
    f = A.aiff({ frames: 4, bits: 8, data: [0x00, 0x7f, 0x80, 0xff] });
    info = E.audioInfo(f);
    w = E.toWav(f, info);
    check(A.wavHeader(w).bits === 8 && A.wavHeader(w).align === 1 && same(w.slice(44, 48), [0x80, 0xff, 0x00, 0x7f]) &&
          w.length === 48, "8 bits: 0, 127, -128, -1 become 128, 255, 0, 127");
    f = A.aiff({ frames: 3, bits: 8, data: [0x00, 0x80, 0xff] });
    w = E.toWav(f, E.audioInfo(f));
    check(w.length === 48 && A.wavHeader(w).dataLen === 3 && A.wavHeader(w).size === 40 && w[47] === 0,
          "an odd number of bytes is padded, the chunk's length stays odd");

    /* 24 and 32 bits, stereo, 44.1 kHz: each sample's bytes reversed */
    f = A.aiff({ ch: 2, frames: 2, bits: 24, rate: 44100, data: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] });
    info = E.audioInfo(f);
    w = E.toWav(f, info);
    h = A.wavHeader(w);
    check(info.channels === 2 && info.rate === 44100 && info.frames === 2 && h.ch === 2 && h.rate === 44100 &&
          h.bits === 24 && h.align === 6 && h.byteRate === 44100 * 6 && same(w.slice(44), [3, 2, 1, 6, 5, 4, 9, 8, 7, 12, 11, 10]),
          "24 bits, stereo, 44.1 kHz: " + JSON.stringify(h));
    f = A.aiff({ ch: 3, frames: 1, bits: 32, data: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] });
    w = E.toWav(f, E.audioInfo(f));
    check(A.wavHeader(w).ch === 3 && A.wavHeader(w).bits === 32 && same(w.slice(44), [4, 3, 2, 1, 8, 7, 6, 5, 12, 11, 10, 9]),
          "32 bits, three channels");
    f = A.aiff({ frames: 2, bits: 12, data: [0x12, 0x30, 0xab, 0xc0] });
    w = E.toWav(f, E.audioInfo(f));
    check(A.wavHeader(w).bits === 16 && same(w.slice(44), [0x30, 0x12, 0xc0, 0xab]), "12 bits in two bytes (low bits 0): as 16");

    /* the rates COMM holds as an 80-bit float, the old Macintosh one too */
    const rates = [8000, 11025, 22050, 32000, 44100, 48000, 88200, 96000, 192000, 22254.545454545];
    const wrong = rates.filter(r => Math.abs(E.audioInfo(A.aiff({ frames: 1, data: [0, 0], rate: r })).rate - r) > 1e-6);
    check(!wrong.length, "rates read from COMM: " + rates.join(", ") + (wrong.length ? "; wrong: " + wrong : ""));
    f = A.aiff({ frames: 1, data: [0, 0], rate: 22254.545454545 });
    check(A.wavHeader(E.toWav(f, E.audioInfo(f))).rate === 22255, "a rate with a fraction is rounded for the WAV");

    /* AIFF-C: the types handed on, little-endian ones as they are, floats; the compressed ones named */
    f = A.aiff({ type: "sowt", frames: 7, data: le });
    w = E.toWav(f, E.audioInfo(f));
    check(A.wavHeader(w).tag === 1 && same(w.slice(44), le), "AIFF-C sowt (little-endian): the bytes as they are");
    f = A.aiff({ type: "NONE", frames: 7, data: be });
    check(same(E.toWav(f, E.audioInfo(f)).slice(44), le), "AIFF-C NONE: as AIFF");
    f = A.aiff({ type: "twos", frames: 7, data: be });
    check(same(E.toWav(f, E.audioInfo(f)).slice(44), le), "AIFF-C twos: as AIFF");
    f = A.aiff({ type: "in24", frames: 1, bits: 24, data: [1, 2, 3] });
    check(same(E.toWav(f, E.audioInfo(f)).slice(44, 47), [3, 2, 1]), "AIFF-C in24");
    f = A.aiff({ type: "23ni", frames: 1, bits: 32, data: [1, 2, 3, 4] });
    check(same(E.toWav(f, E.audioInfo(f)).slice(44), [1, 2, 3, 4]), "AIFF-C 23ni (32 bits, little-endian)");
    f = A.aiff({ type: "raw ", frames: 2, bits: 8, data: [0x00, 0xff] });
    check(same(E.toWav(f, E.audioInfo(f)).slice(44), [0x00, 0xff]), "AIFF-C raw (8 bits, unsigned): as they are");
    const fl = [0.5, -0.25, 1, -1, 0.1];
    const fl32 = new DataView(new ArrayBuffer(20)), fl64 = new DataView(new ArrayBuffer(40));
    fl.forEach((v, i) => { fl32.setFloat32(4 * i, v); fl64.setFloat64(8 * i, v); });
    f = A.aiff({ type: "fl32", frames: 5, bits: 32, data: Array.from(new Uint8Array(fl32.buffer)) });
    w = E.toWav(f, E.audioInfo(f));
    check(A.wavHeader(w).tag === 3 && A.wavHeader(w).bits === 32 &&
          fl.every((v, i) => new DataView(w.buffer).getFloat32(44 + 4 * i, true) === Math.fround(v)), "AIFF-C fl32: 32-bit floats");
    f = A.aiff({ type: "fl64", frames: 5, bits: 64, data: Array.from(new Uint8Array(fl64.buffer)) });
    w = E.toWav(f, E.audioInfo(f));
    check(A.wavHeader(w).tag === 3 && A.wavHeader(w).bits === 32 && A.wavHeader(w).align === 4 && w.length === 44 + 20 &&
          fl.every((v, i) => new DataView(w.buffer).getFloat32(44 + 4 * i, true) === Math.fround(v)),
          "AIFF-C fl64: 64-bit floats become 32-bit ones, which the browser decodes");
    f = A.aiff({ type: "ulaw", frames: 3, bits: 16, data: [0xff, 0x80, 0x00] });
    w = E.toWav(f, E.audioInfo(f));
    check(A.wavHeader(w).tag === 7 && A.wavHeader(w).bits === 8 && A.wavHeader(w).align === 1 && same(w.slice(44, 47), [0xff, 0x80, 0x00]),
          "AIFF-C ulaw (its sample size 16): μ-law bytes in a WAV, one a sample");
    f = A.aiff({ type: "alaw", ch: 2, frames: 1, bits: 16, data: [0xd5, 0x55] });
    w = E.toWav(f, E.audioInfo(f));
    check(A.wavHeader(w).tag === 6 && A.wavHeader(w).align === 2 && same(w.slice(44, 46), [0xd5, 0x55]), "AIFF-C alaw, stereo");
    info = E.audioInfo(A.aiff({ type: "ima4", frames: 64, data: new Array(34).fill(0) }));
    check(info.compressed && info.codec === "IMA ADPCM" && !info.layout && E.toWav(new Uint8Array(0), info) === null,
          "AIFF-C ima4: compressed, named IMA ADPCM, not handed on");
    info = E.audioInfo(A.aiff({ type: "XYZ\x01", frames: 1, data: [0, 0] }));
    check(info.compressed && info.codec === "XYZ", "an unknown type: compressed, named by its printable letters: " + info.codec);
    check(E.audioInfo(A.aiff({ type: "raw ", frames: 1, bits: 16, data: [0, 0] })).compressed, "raw of 16 bits: not handed on");

    /* the file's own oddities: chunks before COMM, SSND first, an offset, cut off, no sound, no COMM */
    f = A.aiff({ frames: 2, data: [0, 1, 0, 2], before: A.iff("NAME", A.ascii("odd")), offset: 3 });
    check(same(E.toWav(f, E.audioInfo(f)).slice(44), [1, 0, 2, 0]), "an odd chunk before COMM (padded), SSND with an offset");
    f = A.aiff({ frames: 2, data: [0, 1, 0, 2], ssndFirst: true });
    check(same(E.toWav(f, E.audioInfo(f)).slice(44), [1, 0, 2, 0]), "SSND before COMM");
    f = A.aiff({ frames: 100, data: [0, 1, 0, 2, 0, 3] });
    info = E.audioInfo(f);
    check(info.frames === 3 && E.toWav(f, info).length === 44 + 6, "COMM says 100 frames, the file holds 3: 3, as Chromium does with a WAV");
    f = A.aiff({ frames: 4, data: [0, 1, 0, 2, 0, 3, 0, 4] }).slice(0, -3);
    check(E.audioInfo(f).frames === 2, "a file cut off in its SSND: the whole frames left");
    check(E.audioInfo(A.aiff({ frames: 0 })).frames === 0, "no frames and no SSND: no sound");
    check(E.audioInfo(Uint8Array.from([...A.ascii("FORM"), 0, 0, 0, 4, ...A.ascii("AIFF")])).broken, "no COMM: broken");
    check(E.audioInfo(A.aiff({ frames: 5 })).broken, "frames but no SSND: broken");
    check(E.audioInfo(A.aiff({ frames: 1, bits: 40, data: [0, 0, 0, 0, 0] })).broken, "40-bit samples: broken");

    /* WAV: most go as they are; 64-bit floats become 32-bit; the compressed ones are named */
    info = E.audioInfo(A.wav({ data: le }));
    check(info.kind === "wav" && info.frames === 7 && info.rate === 48000 && info.channels === 1 && !info.compressed &&
          E.toWav(A.wav({ data: le }), info) === null, "a WAV of 16 bits: 7 frames, to the browser as it is");
    info = E.audioInfo(A.wav({ ch: 2, bits: 24, rate: 44100, data: new Array(12).fill(0), ext: true,
                               before: A.riff("LIST", A.ascii("odd")) }));
    check(info.frames === 2 && info.channels === 2 && info.rate === 44100 && info.layout.type === "int" && info.layout.bytes === 3,
          "an extensible WAV after an odd LIST chunk: 2 frames of 24 bits, stereo");
    info = E.audioInfo(A.wav({ data: le, claim: 0xffffffff }));
    check(info.frames === 7, "a WAV streamed without its length: the frames the file holds");
    check(E.audioInfo(A.wav({ data: [] })).frames === 0, "a WAV without frames");
    f = A.wav({ tag: 3, bits: 64, data: Array.from(new Uint8Array(fl64.buffer).slice(0, 40)).flatMap((_, i, a) => i % 8 ? [] : a.slice(i, i + 8).reverse()) });
    info = E.audioInfo(f);
    w = E.toWav(f, info);
    check(info.layout.type === "float" && info.layout.bytes === 8 && A.wavHeader(w).tag === 3 && A.wavHeader(w).bits === 32 &&
          fl.every((v, i) => new DataView(w.buffer).getFloat32(44 + 4 * i, true) === Math.fround(v)),
          "a WAV of 64-bit floats becomes one of 32-bit floats");
    info = E.audioInfo(A.wav({ tag: 0x11, bits: 4, data: new Array(16).fill(0) }));
    check(info.compressed && info.codec === "IMA ADPCM" && E.toWav(new Uint8Array(0), info) === null, "IMA ADPCM: named");
    info = E.audioInfo(A.wav({ tag: 2, bits: 4, data: [0, 0], ext: true }));
    check(info.compressed && info.codec === "MS ADPCM", "MS ADPCM as an extensible WAV's subformat: named");
    info = E.audioInfo(A.wav({ tag: 0x1234, data: [0, 0] }));
    check(info.compressed && info.codec === "", "an unknown tag: compressed, no name");
    check(E.audioInfo(Uint8Array.from([...A.ascii("RIFF"), 4, 0, 0, 0, ...A.ascii("WAVE")])).broken, "no fmt: broken");
    info = E.audioInfo(A.wav({ tag: 6, bits: 8, data: [1, 2] }));
    check(info.layout.type === "alaw" && E.toWav(A.wav({ tag: 6, bits: 8, data: [1, 2] }), info) === null, "A-law WAV: as it is");
    check(E.framesAt(E.audioInfo(A.bigWav(1000, 44100)), 48000) === Math.ceil(1000 * 48000 / 44100), "a big WAV's frames at 48 kHz");
}

if (failures) {
    console.log(failures + " check(s) failed");
    process.exit(1);
}
console.log("all uploader tests passed");
