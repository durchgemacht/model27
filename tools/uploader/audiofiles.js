/* WAV and AIFF files built byte by byte for the uploader's host tests (elektron.test.js, page.test.js): the layouts of
   the formats' specifications, written here without the page's code. Not a test itself. */
"use strict";

const ascii = (s) => Array.from(s, (c) => c.charCodeAt(0));
const be16 = (n) => [(n >> 8) & 255, n & 255];
const be32 = (n) => [(n >>> 24) & 255, (n >>> 16) & 255, (n >>> 8) & 255, n & 255];
const le16 = (n) => [n & 255, (n >> 8) & 255];
const le32 = (n) => [n & 255, (n >>> 8) & 255, (n >>> 16) & 255, (n >>> 24) & 255];

/* a positive rate as an 80-bit extended float, as AIFF's COMM keeps it */
function ext80(rate) {
    const e = Math.floor(Math.log2(rate)), m = rate / 2 ** e * 2 ** 31, hi = Math.floor(m);
    return [...be16(16383 + e), ...be32(hi), ...be32(Math.round((m - hi) * 2 ** 32))];
}

/* an IFF chunk (big-endian length, padded to even) and a RIFF chunk (little-endian) */
const iff = (id, body) => [...ascii(id), ...be32(body.length), ...body, ...(body.length & 1 ? [0] : [])];
const riff = (id, body) => [...ascii(id), ...le32(body.length), ...body, ...(body.length & 1 ? [0] : [])];

/* An AIFF, or an AIFF-C when type (its compression type) is given. data: the sound bytes as stored; frames: what
   COMM says; before: chunks ahead of COMM; ssndFirst: SSND ahead of COMM; offset: SSND's offset, its bytes skipped. */
function aiff({ ch = 1, frames, bits = 16, rate = 48000, type = null, data = null, before = [], ssndFirst = false,
                offset = 0 }) {
    const comm = iff("COMM", [...be16(ch), ...be32(frames), ...be16(bits), ...ext80(rate),
                              ...(type ? [...ascii(type), 0, 0] : [])]);
    const ssnd = data ? iff("SSND", [...be32(offset), ...be32(0), ...new Array(offset).fill(0x5a), ...data]) : [];
    const body = [...ascii(type ? "AIFC" : "AIFF"), ...before, ...(ssndFirst ? [...ssnd, ...comm] : [...comm, ...ssnd])];
    return Uint8Array.from([...ascii("FORM"), ...be32(body.length), ...body]);
}

/* A WAV. tag: the format tag (with ext, WAVE_FORMAT_EXTENSIBLE carrying it as its subformat); claim: the data chunk's
   length when it is not the data's (a file cut off, or streamed: 0xffffffff); before: chunks ahead of fmt. */
function wav({ tag = 1, ch = 1, rate = 48000, bits = 16, data = [], ext = false, claim = null, before = [] }) {
    const align = ch * Math.ceil(bits / 8);
    const common = [...le16(ch), ...le32(rate), ...le32(rate * align), ...le16(align), ...le16(bits)];
    const fmt = ext ? [...le16(0xfffe), ...common, ...le16(22), ...le16(bits), ...le32(0), ...le16(tag),
                       0, 0, 0, 0, 0x10, 0, 0x80, 0, 0, 0xaa, 0, 0x38, 0x9b, 0x71]
                    : [...le16(tag), ...common];
    const body = [...ascii("WAVE"), ...before, ...riff("fmt ", fmt), ...ascii("data"),
                  ...le32(claim === null ? data.length : claim), ...data];
    return Uint8Array.from([...ascii("RIFF"), ...le32(body.length), ...body]);
}

/* A big WAV without spreading its bytes: mono 16 bits, n frames of silence. */
function bigWav(n, rate = 48000) {
    const head = wav({ rate }), out = new Uint8Array(head.length + 2 * n), dv = new DataView(out.buffer);
    out.set(head);
    dv.setUint32(4, out.length - 8, true);
    dv.setUint32(head.length - 4, 2 * n, true);
    return out;
}

/* What the WAV header at the start of w says (the 44 bytes toWav writes). */
function wavHeader(w) {
    const dv = new DataView(w.buffer, w.byteOffset, w.byteLength), s = (p) => String.fromCharCode(...w.slice(p, p + 4));
    return { riff: s(0), size: dv.getUint32(4, true), wave: s(8), fmt: s(12), fmtLen: dv.getUint32(16, true),
             tag: dv.getUint16(20, true), ch: dv.getUint16(22, true), rate: dv.getUint32(24, true),
             byteRate: dv.getUint32(28, true), align: dv.getUint16(32, true), bits: dv.getUint16(34, true),
             data: s(36), dataLen: dv.getUint32(40, true) };
}

module.exports = { ascii, be16, be32, le16, le32, ext80, iff, riff, aiff, wav, bigWav, wavHeader };
