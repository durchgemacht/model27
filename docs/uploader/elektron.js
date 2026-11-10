/* model27's uploader: the Elektron SysEx file protocol as the Model:Cycles OS 1.13 handles it
   natively, and the sample file format. Plain functions without browser APIs, shared by the page
   (app.js) and the host tests (tools/uploader/, Node).

   From Cycles One-Shot's upload page (github.com/durchgemacht/cycles-one-shot, uploader/, MIT,
   text in ../flasher/LICENSE-One-Shot.txt), moved here unchanged but for this comment. Since release 0.57 it
   also tells audio files apart and reads AIFF (audioInfo, toWav).

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

    /* ---- audio files, before the browser decodes them --------------------------------------------------------------
       The browsers with Web MIDI (Chrome, Edge, Opera: Chromium) decode WAV, but neither AIFF nor a WAV of 64-bit
       floats. Tried in Chromium 152 on 10/11/2026: PCM of 8 to 32 bits, 32-bit floats, A-law and μ-law, 1 to 6
       channels, 4 to 384 kHz and a WAV cut off before its end decode; an AIFF, 64-bit floats, IMA and MS ADPCM and a
       WAV without frames do not. So the page reads AIFF itself and hands the browser the same samples as a WAV
       (toWav). audioInfo says what a file is from its bytes, for that and for the page's messages. */

    function tag4(b, p) {
        return p + 4 <= b.length ? String.fromCharCode(b[p], b[p + 1], b[p + 2], b[p + 3]) : "";
    }

    function le16(b, p) { return b[p] | (b[p + 1] << 8); }
    function le32(b, p) { return (b[p] | (b[p + 1] << 8) | (b[p + 2] << 16) | (b[p + 3] << 24)) >>> 0; }
    function be16(b, p) { return (b[p] << 8) | b[p + 1]; }

    /* AIFF's rate, an 80-bit extended float: NaN when it is negative, infinite or not a number. */
    function ext80(b, p) {
        var e = ((b[p] & 0x7f) << 8) | b[p + 1];

        if (b[p] & 0x80 || e === 0x7fff)
            return NaN;
        return (readU32(b, p + 2) * 4294967296 + readU32(b, p + 6)) * Math.pow(2, e - 16383 - 63);
    }

    /* The chunks of a RIFF or IFF file from p: each(id, start, length), the length cut to what the file holds. The
       walk stops at a chunk longer than the rest of the file (cut off, or a WAV streamed without its length). */
    function chunks(b, p, le, each) {
        var len;

        while (p + 8 <= b.length) {
            len = le ? le32(b, p + 4) : readU32(b, p + 4);
            each(tag4(b, p), p + 8, Math.min(len, b.length - p - 8));
            if (len > b.length - p - 8)
                return;
            p += 8 + len + (len & 1);
        }
    }

    /* The compressed formats a WAV may name, for the message when the browser cannot decode one. */
    var WAV_CODECS = { 2: "MS ADPCM", 0x11: "IMA ADPCM", 0x31: "GSM 6.10", 0x50: "MPEG", 0x55: "MP3" };

    /* AIFF-C's compression types the page hands on: byte order, kind of sample, bytes a sample (0: from the sample
       size). The others are compressed in ways the browser cannot decode in a WAV; AIFC_CODECS names some. */
    var AIFC_TYPES = {
        "NONE": ["be", "int", 0], "twos": ["be", "int", 0], "sowt": ["le", "int", 0],
        "in24": ["be", "int", 3], "in32": ["be", "int", 4], "42ni": ["le", "int", 3], "23ni": ["le", "int", 4],
        "raw ": ["be", "uint", 1],
        "fl32": ["be", "float", 4], "FL32": ["be", "float", 4], "fl64": ["be", "float", 8], "FL64": ["be", "float", 8],
        "ulaw": ["be", "ulaw", 1], "ULAW": ["be", "ulaw", 1], "alaw": ["be", "alaw", 1], "ALAW": ["be", "alaw", 1]
    };
    var AIFC_CODECS = { "ima4": "IMA ADPCM", "MAC3": "MACE 3:1", "MAC6": "MACE 6:1", "GSM ": "GSM", "agsm": "GSM",
                        "Qclp": "QUALCOMM PureVoice", "QDMC": "QDesign", "QDM2": "QDesign", "alac": "Apple Lossless" };

    function wavInfo(b) {
        var info = { kind: "wav", compressed: false, codec: "", frames: null, layout: null, broken: false },
            fmt = null, data = null, tag, bytes;

        chunks(b, 12, true, function (id, at, len) {
            if (id === "fmt " && len >= 16 && !fmt)
                fmt = { tag: le16(b, at), channels: le16(b, at + 2), rate: le32(b, at + 4), align: le16(b, at + 12),
                        bits: le16(b, at + 14), sub: len >= 40 ? le16(b, at + 24) : 0 };
            if (id === "data" && !data)
                data = { at: at, len: len };
        });
        if (!fmt || !data || !fmt.channels || !fmt.rate || !fmt.align) {
            info.broken = true;
            return info;
        }
        info.channels = fmt.channels;
        info.rate = fmt.rate;
        tag = fmt.tag === 0xfffe ? fmt.sub : fmt.tag;
        bytes = fmt.align / fmt.channels;
        if (tag !== 1 && tag !== 3 && tag !== 6 && tag !== 7) {
            info.compressed = true;
            info.codec = WAV_CODECS[tag] || "";
            return info;
        }
        if (bytes !== Math.floor(bytes) || bytes < 1 || bytes > 8) {
            info.broken = true;
            return info;
        }
        info.layout = { at: data.at, order: "le", bytes: bytes,
                        type: tag === 3 ? "float" : tag === 6 ? "alaw" : tag === 7 ? "ulaw" : bytes === 1 ? "uint" : "int" };
        info.frames = Math.floor(data.len / fmt.align);
        return info;
    }

    function aiffInfo(b, aifc) {
        var info = { kind: "aiff", compressed: false, codec: "", frames: null, layout: null, broken: false },
            comm = null, ssnd = null, how, bytes;

        chunks(b, 12, false, function (id, at, len) {
            if (id === "COMM" && len >= 18 && !comm)
                comm = { channels: be16(b, at), frames: readU32(b, at + 2), bits: be16(b, at + 6), rate: ext80(b, at + 8),
                         type: !aifc ? "NONE" : len >= 22 ? tag4(b, at + 18) : "" };
            if (id === "SSND" && len >= 8 && !ssnd)
                ssnd = { at: at + 8 + readU32(b, at), len: len - 8 - readU32(b, at) };
        });
        if (!comm || !comm.channels || !(comm.rate >= 1)) {
            info.broken = true;
            return info;
        }
        info.channels = comm.channels;
        info.rate = comm.rate;
        how = AIFC_TYPES[comm.type];
        if (!how || (how[1] === "uint" && comm.bits > 8)) {
            info.compressed = true;
            info.codec = AIFC_CODECS[comm.type] || comm.type.replace(/[^ -~]/g, "").trim();
            return info;
        }
        if (comm.frames === 0) {                /* no sound: SSND may be missing */
            info.frames = 0;
            return info;
        }
        bytes = how[2] || Math.ceil(comm.bits / 8);
        if (!ssnd || ssnd.len < 0 || bytes < 1 || (how[1] === "float" ? bytes !== 4 && bytes !== 8 : bytes > 4)) {
            info.broken = true;
            return info;
        }
        info.layout = { at: ssnd.at, order: how[0], type: how[1], bytes: bytes };
        info.frames = Math.min(comm.frames, Math.floor(ssnd.len / (bytes * comm.channels)));
        return info;
    }

    /* What a file is, from its bytes: kind "empty", "wav", "aiff", "mp3", "flac", "ogg", "opus", "m4a", "aac" or
       "unknown". For a WAV or an AIFF also its channels, rate and frames (null when not known), compressed and the
       codec's name ("" when unknown) for one the page cannot hand on, the samples' layout {at, order, type, bytes},
       and broken when its header makes no sense. */
    function audioInfo(b) {
        var form = tag4(b, 8);

        if (!b.length)
            return { kind: "empty" };
        if (tag4(b, 0) === "RIFF" && form === "WAVE")
            return wavInfo(b);
        if (tag4(b, 0) === "FORM" && (form === "AIFF" || form === "AIFC"))
            return aiffInfo(b, form === "AIFC");
        if (tag4(b, 0) === "fLaC")
            return { kind: "flac" };
        if (tag4(b, 0) === "OggS")
            return { kind: tag4(b, 28) + tag4(b, 32) === "OpusHead" ? "opus" : "ogg" };
        if (tag4(b, 4) === "ftyp")
            return { kind: "m4a" };
        if (tag4(b, 0).slice(0, 3) === "ID3")
            return { kind: "mp3" };
        if (b.length >= 2 && b[0] === 0xff && (b[1] & 0xf6) === 0xf0)      /* ADTS: sync, layer 0 */
            return { kind: "aac" };
        if (b.length >= 2 && b[0] === 0xff && (b[1] & 0xe0) === 0xe0)      /* an MPEG audio frame's sync */
            return { kind: "mp3" };
        return { kind: "unknown" };
    }

    /* How many frames a WAV or an AIFF becomes at another rate, as the browser resamples it; null when not known. */
    function framesAt(info, rate) {
        return info.frames === null || info.frames === undefined || !info.rate ? null
            : Math.ceil(info.frames * rate / info.rate);
    }

    /* The WAV the browser decodes for an AIFF (8-bit samples made unsigned, the others little-endian, 64-bit floats
       made 32-bit) or for a WAV of 64-bit floats; null for a file that goes to the browser as it is. info: from
       audioInfo, with a layout. */
    function toWav(b, info) {
        var L = info.layout, n, bytes, size, out, dv, src, p, q, i, k;

        if (!L || (info.kind === "wav" && !(L.type === "float" && L.bytes === 8)))
            return null;
        n = info.frames * info.channels;
        bytes = L.type === "float" && L.bytes === 8 ? 4 : L.bytes;
        size = n * bytes;
        out = new Uint8Array(44 + size + (size & 1));
        dv = new DataView(out.buffer);
        dv.setUint32(0, 0x52494646);                                       /* RIFF */
        dv.setUint32(4, out.length - 8, true);
        dv.setUint32(8, 0x57415645);                                       /* WAVE */
        dv.setUint32(12, 0x666d7420);                                      /* fmt  */
        dv.setUint32(16, 16, true);
        dv.setUint16(20, L.type === "float" ? 3 : L.type === "alaw" ? 6 : L.type === "ulaw" ? 7 : 1, true);
        dv.setUint16(22, info.channels, true);
        dv.setUint32(24, Math.round(info.rate), true);
        dv.setUint32(28, Math.round(info.rate) * info.channels * bytes, true);
        dv.setUint16(32, info.channels * bytes, true);
        dv.setUint16(34, 8 * bytes, true);
        dv.setUint32(36, 0x64617461);                                      /* data */
        dv.setUint32(40, size, true);
        p = L.at;
        if (L.bytes === 8) {
            src = new DataView(b.buffer, b.byteOffset, b.byteLength);
            for (i = 0, q = 44; i < n; i++, p += 8, q += 4)
                dv.setFloat32(q, src.getFloat64(p, L.order === "le"), true);
        } else if (bytes === 1)
            for (i = 0; i < n; i++)
                out[44 + i] = L.type === "int" ? b[p + i] ^ 0x80 : b[p + i];
        else if (L.order === "le")
            out.set(b.subarray(p, p + size), 44);
        else
            for (i = 0, q = 44; i < n; i++, p += bytes)
                for (k = bytes - 1; k >= 0; k--)
                    out[q++] = b[p + k];
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
    exports.audioInfo = audioInfo;
    exports.framesAt = framesAt;
    exports.toWav = toWav;
    exports.CYCLE = CYCLE;
    exports.TABLE_MAX = TABLE_MAX;
    exports.WAVETABLES = WAVETABLES;
    exports.tableFrames = tableFrames;
    exports.startsWithSine = startsWithSine;
    exports.TABLES = TABLES;
    exports.tableNumber = tableNumber;
    exports.playsFirst = playsFirst;
})(typeof module !== "undefined" && module.exports ? module.exports : (window.Elektron = {}));
