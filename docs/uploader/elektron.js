/* model27's uploader: the Elektron SysEx file protocol as the Model:Cycles OS 1.13 handles it
   natively, and the sample file format. Plain functions without browser APIs, shared by the page
   (app.js) and the host tests (tools/uploader/, Node).

   From Cycles One-Shot's upload page (github.com/durchgemacht/cycles-one-shot, uploader/, MIT,
   text in ../flasher/LICENSE-One-Shot.txt), moved here unchanged but for this comment.

   Facts used, not code: the message framing and the file commands follow ModdedTransfer
   (github.com/ktwzk/modded-transfer, WTFPL), which follows Elektroid. The Cycles answers the raw
   twins of the Model:Samples' sample commands, 0x14 for 0x10 and so on (Model-TG's rpc_map, MIT);
   the OS 1.13 lists 0x16 and 0x24, the twins of the deletes 0x12 and 0x20, among the types it takes.
   The OS hashes a file when it closes it after writing (0x4007c022 -> 0x4007e2f6); its browser and
   SAMPLE only see files with that hash. */
(function (exports) {
    "use strict";

    var HEADER = [0xf0, 0x00, 0x20, 0x3c, 0x10, 0x00];
    var TYPE = {
        PING: 0x01,
        READ_DIR: 0x14,
        CREATE_DIR: 0x15,
        DELETE_DIR: 0x16,           /* an empty folder only */
        DELETE_FILE: 0x24,
        OPEN_WRITE: 0x43,
        CLOSE_WRITE: 0x44,
        WRITE: 0x45
    };
    var BLOCK = 0x2000;             /* bytes per write */
    var RATE = 48000;               /* every sample is written at the Cycles' own rate */
    var NAME_MAX = 64;

    /* 7-bit packing: each group of up to 7 bytes follows a byte that holds their top bits, the
       group's first byte in bit 6. The last group is not padded. */
    function encode7(src) {
        var out = [], i, k;

        for (i = 0; i < src.length; i += 7) {
            var n = Math.min(7, src.length - i), top = 0, group = [];

            for (k = 0; k < n; k++) {
                if (src[i + k] & 0x80)
                    top |= 1 << (6 - k);
                group.push(src[i + k] & 0x7f);
            }
            out.push(top);
            Array.prototype.push.apply(out, group);
        }
        return out;
    }

    function decode7(src) {
        var out = [], i, k;

        for (i = 0; i < src.length; i += 8)
            for (k = 0; k < 7 && i + k + 1 < src.length; k++)
                out.push((src[i + k + 1] & 0x7f) | ((src[i] & (1 << (6 - k))) ? 0x80 : 0));
        return new Uint8Array(out);
    }

    function frame(msg) {
        return new Uint8Array(HEADER.concat(encode7(msg), [0xf7]));
    }

    /* The message inside a SysEx from the device, or null if it is not one of these. */
    function unframe(sysex) {
        var i;

        if (sysex.length < 8 || sysex[sysex.length - 1] !== 0xf7)
            return null;
        for (i = 0; i < HEADER.length; i++)
            if (sysex[i] !== HEADER[i])
                return null;
        return decode7(sysex.subarray ? sysex.subarray(6, sysex.length - 1) : sysex.slice(6, -1));
    }

    function u32(n) {
        return [(n >>> 24) & 255, (n >>> 16) & 255, (n >>> 8) & 255, n & 255];
    }

    function readU32(a, p) {
        return ((a[p] << 24) | (a[p + 1] << 16) | (a[p + 2] << 8) | a[p + 3]) >>> 0;
    }

    /* A request: our sequence number (big-endian), two zero bytes, the type, the body. */
    function request(seq, type, body) {
        return new Uint8Array([(seq >>> 8) & 255, seq & 255, 0, 0, type].concat(body || []));
    }

    /* A reply carries the request's sequence number in bytes 2..3 and the request's type | 0x80 in
       byte 4; byte 5 is 1 when the device did what was asked. */
    function replySeq(m) {
        return ((m[2] << 8) | m[3]) >>> 0;
    }

    function replyOk(m) {
        return m.length > 5 && m[5] === 1;
    }

    /* Whatever text a refusal carries after its status byte. */
    function replyText(m) {
        return decodeText(Array.prototype.slice.call(m, 6).filter(function (b) { return b !== 0; })).trim();
    }

    /* Paths and names travel as Windows-1252; a character it cannot hold becomes '?'. */
    var CP1252 = {
        0x20ac: 0x80, 0x201a: 0x82, 0x0192: 0x83, 0x201e: 0x84, 0x2026: 0x85, 0x2020: 0x86, 0x2021: 0x87,
        0x02c6: 0x88, 0x2030: 0x89, 0x0160: 0x8a, 0x2039: 0x8b, 0x0152: 0x8c, 0x017d: 0x8e, 0x2018: 0x91,
        0x2019: 0x92, 0x201c: 0x93, 0x201d: 0x94, 0x2022: 0x95, 0x2013: 0x96, 0x2014: 0x97, 0x02dc: 0x98,
        0x2122: 0x99, 0x0161: 0x9a, 0x203a: 0x9b, 0x0153: 0x9c, 0x017e: 0x9e, 0x0178: 0x9f
    };
    var CP1252_BACK = {};
    Object.keys(CP1252).forEach(function (k) { CP1252_BACK[CP1252[k]] = +k; });

    function encodeText(s) {
        var out = [];

        Array.from(s).forEach(function (c) {
            var cp = c.codePointAt(0);

            if (cp < 0x80 || (cp >= 0xa0 && cp <= 0xff))
                out.push(cp);
            else if (CP1252[cp] !== undefined)
                out.push(CP1252[cp]);
            else
                out.push(0x3f);
        });
        return out;
    }

    function decodeText(bytes) {
        return Array.prototype.map.call(bytes, function (b) {
            return String.fromCodePoint(CP1252_BACK[b] !== undefined ? CP1252_BACK[b] : b);
        }).join("");
    }

    function pathBytes(path) {
        return encodeText(path).concat([0]);
    }

    /* The reply to READ_DIR: from byte 5, per entry its hash and size (u32 each), write protection,
       type ('D' for a folder), name and a 0. */
    function parseDir(m) {
        var items = [], p = 5;

        while (p < m.length) {
            var end, hash, size, prot, type;

            if (p + 10 > m.length)
                throw new Error("malformed folder listing");
            hash = readU32(m, p);
            size = readU32(m, p + 4);
            prot = m[p + 8];
            type = m[p + 9];
            p += 10;
            for (end = p; end < m.length && m[end] !== 0; end++)
                ;
            if (end >= m.length)
                throw new Error("malformed name in folder listing");
            if (end > p)
                items.push({
                    name: decodeText(m.subarray ? m.subarray(p, end) : m.slice(p, end)),
                    size: size, hash: hash, writeProtected: prot !== 0, folder: type === 0x44
                });
            p = end + 1;
        }
        return items;
    }

    function normalizePath(p) {
        p = String(p || "/").trim().replace(/\\/g, "/");
        if (p.charAt(0) !== "/")
            p = "/" + p;
        p = p.replace(/\/+/g, "/");
        if (p.length > 1)
            p = p.replace(/\/+$/, "");
        return p;
    }

    function joinPath(dir, name) {
        return normalizePath((dir === "/" ? "" : dir) + "/" + name);
    }

    function parentPath(p) {
        var i;

        p = normalizePath(p);
        i = p.lastIndexOf("/");
        return i <= 0 ? "/" : p.slice(0, i);
    }

    /* A name for the drive: the file's name without its extension, without '/', '\' or control
       characters, at most NAME_MAX characters. */
    function cleanName(s) {
        var dot;

        s = String(s || "");
        dot = s.lastIndexOf(".");
        if (dot > 0)
            s = s.slice(0, dot);
        s = s.replace(/[\/\\\u0000-\u001f\u007f]/g, "_").trim();
        return Array.from(s).slice(0, NAME_MAX).join("");
    }

    /* Channels to one by averaging. */
    function mixDown(channels) {
        var n = channels[0].length, out = new Float32Array(n), c, i;

        for (c = 0; c < channels.length; c++)
            for (i = 0; i < n; i++)
                out[i] += channels[c][i] / channels.length;
        return out;
    }

    /* Floats (-1..1) to 16-bit, rounded and clipped. */
    function toInt16(f) {
        var out = new Int16Array(f.length), i;

        for (i = 0; i < f.length; i++) {
            var v = Math.round(f[i] * 32768);

            out[i] = v > 32767 ? 32767 : v < -32768 ? -32768 : v;
        }
        return out;
    }

    /* The sample file the Model:Samples and Transfer write: a 64-byte header (+1 0 = mono, +4 bytes of
       audio, +8 rate, +16 last frame, +20 0x7f = no loop; big-endian), the frames as big-endian 16-bit,
       then 16 zero bytes. */
    function sampleFile(frames, rate) {
        var bytes = frames.length * 2, out = new Uint8Array(64 + bytes + 16), dv = new DataView(out.buffer), i;

        dv.setUint32(4, bytes);
        dv.setUint32(8, rate);
        dv.setUint32(16, frames.length > 0 ? frames.length - 1 : 0);
        out[20] = 0x7f;
        for (i = 0; i < frames.length; i++)
            dv.setInt16(64 + 2 * i, frames[i]);
        return out;
    }

    /* CHORD Tables (model27, notes/66) plays the files of /Wavetables as wavetables: frames of 256 samples, the
       first one on SWEEP 0, which is a sine on the stock CHORD. Whether a table's first frame is a sine: harmonic 1
       in sine phase (0, rising), DC and every other harmonic under a thousandth of it (model27's
       tools/wavetable.py, starts_with_sine). frames: 16-bit samples. */
    var CYCLE = 256, TABLE_MAX = 32, WAVETABLES = "/Wavetables";

    /* The frames of 256 a file holds as CHORD Tables' loader reads it (load_one in model27's
       tools/machines/chordtables/chordtables.c): 1 to 32, or 0 when it cannot play the file at all. The page
       always writes mono, the loader's other rule. */
    function tableFrames(frames) {
        var n = frames.length;

        return n > 0 && n % CYCLE === 0 && n / CYCLE <= TABLE_MAX ? n / CYCLE : 0;
    }

    /* The table a name plays as since CHORD Tables 0.4 (number() in chordtables.c, notes/66 §36.3): two digits 01 to
       63, then no digit ("07", "07 Glass Pad"); 0 for any other name. */
    var TABLES = 63;

    function tableNumber(name) {
        var m = /^([0-9][0-9])(?![0-9])/.exec(String(name)), n = m ? +m[1] : 0;

        return n >= 1 && n <= TABLES ? n : 0;
    }

    /* Of two names with one number, CHORD Tables plays the one first in byte order, the bytes as the Cycles keeps the
       name (Windows-1252; before() in chordtables.c): negative when a comes first. */
    function playsFirst(a, b) {
        var x = encodeText(a), y = encodeText(b), i;

        for (i = 0; i < x.length && i < y.length; i++)
            if (x[i] !== y[i])
                return x[i] - y[i];
        return x.length - y.length;
    }

    function startsWithSine(frames) {
        var re = [], im = [], h, k, a, h1, rest = 0, dc = 0;

        if (frames.length < CYCLE)
            return false;
        for (k = 0; k < CYCLE; k++)
            dc += frames[k] / 32767;
        for (h = 1; h < CYCLE / 2; h++) {
            re[h] = 0;
            im[h] = 0;
            for (k = 0; k < CYCLE; k++) {
                a = 2 * Math.PI * h * k / CYCLE;
                re[h] += frames[k] / 32767 * Math.cos(a);
                im[h] -= frames[k] / 32767 * Math.sin(a);
            }
            re[h] *= 2 / CYCLE;
            im[h] *= 2 / CYCLE;
            if (h > 1)
                rest = Math.max(rest, Math.hypot(re[h], im[h]));
        }
        h1 = Math.hypot(re[1], im[1]);
        return h1 > 0.5 && Math.abs(Math.atan2(im[1], re[1]) + Math.PI / 2) < 0.05 &&
               Math.abs(dc) / CYCLE < 1e-3 * h1 && rest < 1e-3 * h1;
    }

    exports.HEADER = HEADER;
    exports.TYPE = TYPE;
    exports.BLOCK = BLOCK;
    exports.RATE = RATE;
    exports.NAME_MAX = NAME_MAX;
    exports.encode7 = encode7;
    exports.decode7 = decode7;
    exports.frame = frame;
    exports.unframe = unframe;
    exports.u32 = u32;
    exports.readU32 = readU32;
    exports.request = request;
    exports.replySeq = replySeq;
    exports.replyOk = replyOk;
    exports.replyText = replyText;
    exports.encodeText = encodeText;
    exports.decodeText = decodeText;
    exports.pathBytes = pathBytes;
    exports.parseDir = parseDir;
    exports.normalizePath = normalizePath;
    exports.joinPath = joinPath;
    exports.parentPath = parentPath;
    exports.cleanName = cleanName;
    exports.mixDown = mixDown;
    exports.toInt16 = toInt16;
    exports.sampleFile = sampleFile;
    exports.CYCLE = CYCLE;
    exports.TABLE_MAX = TABLE_MAX;
    exports.WAVETABLES = WAVETABLES;
    exports.tableFrames = tableFrames;
    exports.startsWithSine = startsWithSine;
    exports.TABLES = TABLES;
    exports.tableNumber = tableNumber;
    exports.playsFirst = playsFirst;
})(typeof module !== "undefined" && module.exports ? module.exports : (window.Elektron = {}));
