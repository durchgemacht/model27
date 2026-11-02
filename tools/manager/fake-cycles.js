/* A stand-in Model:Cycles for trying the page in a browser without one. It replaces Web MIDI with a
   device that answers backup requests (0x6F the project, 0x64 the settings, once it is through
   with what came before), takes backups, answers the Transfer protocol's ping and version, takes
   an OS upgrade block by block and then goes away and comes back as a restart does.

   For tests only, never loaded by the page (docs/manager/; this folder is not on the site): serve
   the repository's root, open /docs/manager/ and load /tools/manager/fake-cycles.js into it by hand
   (a script element or the console), then FakeCycles.install(opts) before pressing Connect. opts: { project: messages,
   settleMs (how long it takes a backup in), restartMs, yes: false (never confirms an upgrade),
   mute: true (does not answer backup requests) }. */
window.FakeCycles = (function () {
    "use strict";
    var S = window.Sysex, F = window.MCFlasher;

    function dump(type, index, data) {
        var sum = data.reduce(function (s, b) { return s + b; }, 0) & 0x3fff, n = 15 + data.length;

        return new Uint8Array([0xf0, 0x00, 0x20, 0x3c, 0x11, 0x00, type, 0x01, 0x01, index].concat(data,
                              [sum >> 7, sum & 0x7f, ((n - 10) & 0x3fff) >> 7, (n - 10) & 0x7f, 0xf7]));
    }

    /* A made-up project: 96 patterns and the settings, each a little different by seed. */
    function project(seed) {
        var msgs = [], i, k, d;

        for (i = 0; i < 96; i++) {
            d = [];
            for (k = 0; k < 60; k++)
                d.push((k * 3 + i + seed) & 0x7f);
            msgs.push(dump(0x50, i, d));
        }
        d = [];
        for (k = 0; k < 30; k++)
            d.push((k + seed * 7) & 0x7f);
        msgs.push(dump(0x54, 0, d));
        return msgs;
    }

    function ascii(s) { return Array.from(s, function (c) { return c.charCodeAt(0); }); }
    function be32(b, o) { return ((b[o] << 24) | (b[o + 1] << 16) | (b[o + 2] << 8) | b[o + 3]) >>> 0; }

    function install(opts) {
        var dev, input, output, access;

        opts = opts || {};
        dev = { project: opts.project || project(1), incoming: [], busyUntil: 0, os: null, flashed: [], heard: [] };
        input = { id: "fake-in", name: "Elektron Model:Cycles", manufacturer: "Elektron", state: "connected",
                  onmidimessage: null, open: function () { return Promise.resolve(input); } };
        output = { id: "fake-out", name: "Elektron Model:Cycles", manufacturer: "Elektron", state: "connected",
                   open: function () { return Promise.resolve(output); }, send: receive };
        access = { inputs: new Map([[input.id, input]]), outputs: new Map([[output.id, output]]), onstatechange: null };
        navigator.requestMIDIAccess = function () { return Promise.resolve(access); };

        function emit(msg, delay) {
            setTimeout(function () {
                if (input.state === "connected" && input.onmidimessage)
                    input.onmidimessage({ data: msg, timeStamp: performance.now() });
            }, delay || 1);
        }

        function reply(req, body) {
            var payload = [0, 0, req[0], req[1], req[4] | 0x80].concat(body);

            emit(new Uint8Array([0xf0, 0x00, 0x20, 0x3c, 0x10, 0x00].concat(S.encode7(payload), [0xf7])));
        }

        function setState(s) {
            input.state = output.state = s;
            [input, output].forEach(function (p) { if (access.onstatechange) access.onstatechange({ port: p }); });
        }

        function restart() {
            setState("disconnected");
            setTimeout(function () { setState("connected"); }, opts.restartMs || 800);
        }

        function receive(m) {
            var t, p, body, len, off, data;

            if (output.state !== "connected")
                throw new Error("the port is disconnected");
            m = Uint8Array.from(m);
            t = S.dumpType(m);
            if (t >= 0)
                dev.heard.push(t.toString(16));
            if (t === 0x6f && !opts.mute)
                dev.project.forEach(function (x, i) { emit(x, 2 + i); });
            else if (t === 0x64 && !opts.mute)
                emit(dev.project[dev.project.length - 1], Math.max(1, dev.busyUntil - performance.now()));
            else if (t === 0x50 || t === 0x54) {
                dev.incoming.push(m);
                dev.busyUntil = performance.now() + (opts.settleMs || 300);
                if (t === 0x54) {
                    dev.project = dev.incoming;
                    dev.incoming = [];
                }
            } else if (t < 0 && (p = S.rpcReply(m))) {
                dev.heard.push("rpc " + p[4].toString(16));
                body = p.subarray(5);
                if (p[4] === 0x01)
                    reply(p, [27, 0].concat(ascii("Model Cycles"), [0]));
                else if (p[4] === 0x02)
                    reply(p, [0, 0, 0, 0, 0].concat(ascii("1.13"), [0]));
                else if (p[4] === 0x50) {
                    dev.os = { size: body[0] | (body[1] << 8) | (body[2] << 16) | (body[3] << 24), got: 0 };
                    reply(p, [0]);
                } else if (p[4] === 0x51) {
                    len = be32(body, 4);
                    off = be32(body, 8);
                    data = body.subarray(12, 12 + len);
                    if (F.crc32(data, 0xffffffff) !== be32(body, 0) || off !== dev.os.got) {
                        reply(p, [0, 0, 0, 0, 2]);
                        return;
                    }
                    dev.os.got += len;
                    reply(p, [0, 0, 0, 0, dev.os.got >= dev.os.size ? 1 : 0]);
                    if (dev.os.got >= dev.os.size) {
                        dev.flashed.push(dev.os.size);
                        if (opts.yes !== false)
                            setTimeout(restart, 300);
                    }
                }
            }
        }

        return { dev: dev, input: input, output: output, access: access, restart: restart };
    }

    return { install: install, project: project, dump: dump };
})();
