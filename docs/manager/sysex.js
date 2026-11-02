/* model27's manager: SysEx helpers without page code, shared by the page and the host tests
   (tools/manager/, Node).

   A capture is what the Model:Cycles sends from CONFIG > BACKUP (manual 12.5) or on request:
   complete SysEx messages, F0 to F7 each, kept as they came and sent back unchanged. */
(function (exports) {
    "use strict";

    var WIRE_BYTES_PER_SEC = 31250 / 10;    /* 8N1 on the MIDI wire */
    var CYCLES = [0x00, 0x20, 0x3c, 0x11, 0x00];   /* after F0: Elektron, then the Model:Cycles' product id */
    var RPC = [0xf0, 0x00, 0x20, 0x3c, 0x10, 0x00]; /* the Transfer protocol's messages */

    /* The messages of a .syx, F0..F7 each. Bytes between messages are skipped; a message without
       its F7, or with another status byte inside, is an error. */
    function split(raw) {
        var msgs = [], i = 0, a, k;

        for (;;) {
            a = raw.indexOf(0xf0, i);
            if (a < 0)
                return msgs;
            for (k = a + 1; k < raw.length && raw[k] < 0x80; k++)
                ;
            if (k >= raw.length)
                throw new Error("SysEx at byte " + a + " has no end (F7)");
            if (raw[k] !== 0xf7)
                throw new Error("SysEx at byte " + a + " is cut off by 0x" + raw[k].toString(16) + " at byte " + k);
            msgs.push(raw.subarray(a, k + 1));
            i = k + 1;
        }
    }

    /* The messages as one .syx. */
    function join(msgs) {
        var n = msgs.reduce(function (s, m) { return s + m.length; }, 0), out = new Uint8Array(n), p = 0;

        msgs.forEach(function (m) {
            out.set(m, p);
            p += m.length;
        });
        return out;
    }

    function size(msgs) {
        return msgs.reduce(function (s, m) { return s + m.length; }, 0);
    }

    /* Puts SysEx back together from MIDI input, which may deliver it in pieces with real-time bytes
       (F8 and up) in between. Calls onMessage(msg, time) with time from the piece that held the F7.
       Anything outside a SysEx is dropped, so are a SysEx cut off by another status byte and an F7
       without its F0. */
    function assembler(onMessage) {
        var rx = null;

        return function (data, time) {
            var i, b;

            for (i = 0; i < data.length; i++) {
                b = data[i];
                if (b === 0xf0)
                    rx = [0xf0];
                else if (b === 0xf7) {
                    if (rx) {
                        rx.push(0xf7);
                        onMessage(new Uint8Array(rx), time);
                        rx = null;
                    }
                } else if (b >= 0xf8)
                    ;
                else if (b >= 0x80)
                    rx = null;
                else if (rx)
                    rx.push(b);
            }
        };
    }

    function hex(bytes) {
        return Array.prototype.map.call(bytes, function (b) {
            return b.toString(16).padStart(2, "0");
        }).join(" ");
    }

    /* A message's first bytes after F0: the maker (00 20 3C for Elektron), then the device's own. */
    function head(msg, n) {
        return hex(msg.subarray(1, Math.min(msg.length - 1, 1 + n)));
    }

    /* Messages in a row that start alike, as one entry: { head, count, bytes, first } with first the
       index of the entry's first message. */
    function groups(msgs, n) {
        var out = [];

        msgs.forEach(function (m, i) {
            var h = head(m, n), last = out[out.length - 1];

            if (last && last.head === h) {
                last.count++;
                last.bytes += m.length;
            } else
                out.push({ head: h, count: 1, bytes: m.length, first: i });
        });
        return out;
    }

    /* Where captures a and b differ: the messages whose bytes differ, each with how many bytes and the
       first and last of them (a length difference counts as that many bytes, from the shorter end),
       and how many messages one has more than the other. */
    function compare(a, b) {
        var n = Math.min(a.length, b.length), diffs = [], i, k;

        for (i = 0; i < n; i++) {
            var x = a[i], y = b[i], m = Math.min(x.length, y.length), count = 0, first = -1, last = -1;

            for (k = 0; k < m; k++)
                if (x[k] !== y[k]) {
                    count++;
                    if (first < 0)
                        first = k;
                    last = k;
                }
            if (x.length !== y.length) {
                count += Math.abs(x.length - y.length);
                if (first < 0)
                    first = m;
                last = Math.max(x.length, y.length) - 1;
            }
            if (count)
                diffs.push({ index: i, bytes: count, first: first, last: last, lengthA: x.length, lengthB: y.length });
        }
        return {
            identical: !diffs.length && a.length === b.length,
            diffs: diffs,
            onlyA: Math.max(0, a.length - b.length),
            onlyB: Math.max(0, b.length - a.length)
        };
    }

    /* How long to wait after sending n bytes: pace 1 is the time a MIDI cable takes for them, 0.25 a
       quarter of it, 0 no wait. */
    function waitMs(n, pace) {
        return pace > 0 ? n / WIRE_BYTES_PER_SEC * 1000 * pace : 0;
    }

    /* A file name from a label and a date: label-YYYY-MM-DD-HHMMSS.syx, the label without characters
       file systems refuse. */
    function fileName(label, d) {
        function two(n) { return String(n).padStart(2, "0"); }

        label = String(label || "").trim().replace(/[\/\\:*?"<>|\u0000-\u001f]+/g, "-") || "capture";
        return label + "-" + d.getFullYear() + "-" + two(d.getMonth() + 1) + "-" + two(d.getDate()) + "-" +
               two(d.getHours()) + two(d.getMinutes()) + two(d.getSeconds()) + ".syx";
    }

    /* The dump type of a Model:Cycles message: 0x50 a pattern, 0x54 the settings, 0x60 and up a
       request; -1 for any other message. */
    function dumpType(msg) {
        var k;

        if (msg.length < 15)
            return -1;
        for (k = 0; k < CYCLES.length; k++)
            if (msg[1 + k] !== CYCLES[k])
                return -1;
        return msg[6];
    }

    /* Whether a dump's checksum and length are right: the checksum is the sum of the bytes from 10
       to the checksum, the length the message's minus 10, both modulo 2^14 in two 7-bit bytes. */
    function dumpOk(msg) {
        var n = msg.length, sum = 0, k;

        if (dumpType(msg) < 0)
            return false;
        for (k = 10; k < n - 5; k++)
            sum += msg[k];
        return ((msg[n - 5] << 7) | msg[n - 4]) === (sum & 0x3fff) &&
               ((msg[n - 3] << 7) | msg[n - 2]) === ((n - 10) & 0x3fff);
    }

    /* A dump request as the OS 1.13 reads it (Midi::handleSysexDumpRequest at 0x40083602): the
       type, 01 01, an index, no data, then checksum 0 and length 5. 0x6F asks for the whole
       project (patterns 0 to 95, then the settings), 0x60 for one pattern, 0x64 for the settings. */
    function request(type, index) {
        return new Uint8Array([0xf0, 0x00, 0x20, 0x3c, 0x11, 0x00, type, 0x01, 0x01, (index || 0) & 0x7f,
                               0x00, 0x00, 0x00, 0x05, 0xf7]);
    }

    /* 7-bit packing of the Transfer protocol: each group of up to 7 bytes follows a byte that holds
       their top bits, the group's first byte in bit 6. */
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

    /* A Transfer-protocol request without a body: our sequence number, two zero bytes, the type
       (0x01 ping, 0x02 the OS version), as model27's flasher sends it. */
    function rpc(seq, type) {
        return new Uint8Array(RPC.concat(encode7([(seq >>> 8) & 255, seq & 255, 0, 0, type]), [0xf7]));
    }

    /* The decoded payload of a Transfer-protocol message, or null. A reply carries the request's
       sequence number in bytes 2..3 and its type | 0x80 in byte 4. */
    function rpcReply(msg) {
        var k;

        if (msg.length < 8 || msg[msg.length - 1] !== 0xf7)
            return null;
        for (k = 0; k < RPC.length; k++)
            if (msg[k] !== RPC[k])
                return null;
        return decode7(msg.subarray(RPC.length, msg.length - 1));
    }

    /* The NUL-terminated text at byte o of a payload. */
    function rpcText(m, o) {
        var s = "", i;

        for (i = o; i < m.length && m[i]; i++)
            s += String.fromCharCode(m[i]);
        return s;
    }

    /* SHA-256 of some bytes as 64 hex digits (Web Crypto, in browsers and in Node). */
    async function sha256(bytes) {
        var d = new Uint8Array(await globalThis.crypto.subtle.digest("SHA-256", bytes));

        return hex(d).replace(/ /g, "");
    }

    exports.WIRE_BYTES_PER_SEC = WIRE_BYTES_PER_SEC;
    exports.sha256 = sha256;
    exports.dumpType = dumpType;
    exports.dumpOk = dumpOk;
    exports.request = request;
    exports.encode7 = encode7;
    exports.decode7 = decode7;
    exports.rpc = rpc;
    exports.rpcReply = rpcReply;
    exports.rpcText = rpcText;
    exports.split = split;
    exports.join = join;
    exports.size = size;
    exports.assembler = assembler;
    exports.hex = hex;
    exports.head = head;
    exports.groups = groups;
    exports.compare = compare;
    exports.waitMs = waitMs;
    exports.fileName = fileName;
})(typeof module !== "undefined" && module.exports ? module.exports : (window.Sysex = {}));
