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

if (failures) {
    console.log(failures + " check(s) failed");
    process.exit(1);
}
console.log("all uploader tests passed");
