/* A stand-in Model:Cycles for trying the uploader in a browser without one. It replaces Web MIDI with a device
   that answers the file commands from memory, by the same rules as page.test.js: a protected /factory, /incoming,
   a few folders and samples to look at.

   For tests only, never loaded by the page (docs/uploader/; this folder is not on the site): serve the repository's
   root, open /docs/uploader/ and load /tools/uploader/fake-cycles.js into it by hand (a script element or the
   console), then FakeDrive.install(opts) before pressing Connect the Cycles. opts: { mute: true (answers nothing),
   delayMs (how long each answer takes, 15 by default) }. */
window.FakeDrive = (function () {
    "use strict";
    var E = window.Elektron;

    function install(opts) {
        var o = opts || {}, delay = o.delayMs === undefined ? 15 : o.delayMs, open = new Map(), nextId = 7;
        var drive = new Map([
            ["/", { folder: true }], ["/factory", { folder: true, protect: true }],
            ["/factory/Kick", { folder: false, data: new Uint8Array(96080) }],
            ["/incoming", { folder: true }], ["/My Samples", { folder: true }],
            ["/My Samples/Drums", { folder: true }],
            ["/My Samples/Drums/Kick 01", { folder: false, data: new Uint8Array(96080) }],
            ["/My Samples/Drums/Snare 02", { folder: false, data: new Uint8Array(48080) }],
            ["/My Samples/Pad", { folder: false, data: new Uint8Array(960080) }]
        ]);

        function children(dir) {
            var pre = dir === "/" ? "/" : dir + "/";

            return Array.from(drive.keys()).filter(function (p) {
                return p !== dir && p.indexOf(pre) === 0 && p.slice(pre.length).indexOf("/") < 0;
            });
        }
        function str(b, p) { var e = p; while (b[e] !== 0) e++; return E.decodeText(b.slice(p, e)); }
        function answer(m) {
            var seq = (m[0] << 8) | m[1], type = m[4], body = Array.from(m.slice(5)), p, it, bytes, id, f;

            function out(b) { return [0, 99, (seq >> 8) & 255, seq & 255, type | 0x80].concat(b); }
            switch (type) {
            case E.TYPE.PING:
                return out([1]);
            case E.TYPE.READ_DIR:
                p = str(body, 0);
                bytes = [];
                if (!drive.has(p) || !drive.get(p).folder)
                    return out([]);
                children(p).forEach(function (c) {
                    var x = drive.get(c);

                    bytes = bytes.concat(E.u32(x.folder ? 0 : 0x1235), E.u32(x.folder ? 0 : x.data.length),
                                         [x.protect ? 1 : 0, x.folder ? 0x44 : 0x46],
                                         E.encodeText(c.slice(c.lastIndexOf("/") + 1)), [0]);
                });
                return out(bytes);
            case E.TYPE.CREATE_DIR:
                p = str(body, 0);
                if (drive.has(p))
                    return out([0]);
                drive.set(p, { folder: true });
                return out([1]);
            case E.TYPE.OPEN_WRITE:
                p = str(body, 4);
                if (!drive.has(E.parentPath(p)) || drive.get(E.parentPath(p)).protect)
                    return out([0].concat(E.encodeText("Write protected"), [0]));
                open.set(nextId, { path: p, size: E.readU32(body, 0), data: new Uint8Array(E.readU32(body, 0)) });
                return out([1].concat(E.u32(nextId++)));
            case E.TYPE.WRITE:
                id = E.readU32(body, 0);
                f = open.get(id);
                if (!f)
                    return out([0]);
                f.data.set(body.slice(12, 12 + E.readU32(body, 4)), E.readU32(body, 8));
                return out([1]);
            case E.TYPE.CLOSE_WRITE:
                id = E.readU32(body, 0);
                f = open.get(id);
                if (!f)
                    return out([0]);
                open.delete(id);
                drive.set(f.path, { folder: false, data: f.data });
                return out([1]);
            case E.TYPE.DELETE_FILE:
                p = str(body, 0);
                it = drive.get(p);
                if (!it || it.folder || drive.get(E.parentPath(p)).protect)
                    return out([0]);
                drive.delete(p);
                return out([1]);
            case E.TYPE.DELETE_DIR:
                p = str(body, 0);
                it = drive.get(p);
                if (p === "/" || !it || !it.folder || it.protect || children(p).length)
                    return out([0]);
                drive.delete(p);
                return out([1]);
            }
            return out([0]);
        }

        var input = { id: "in1", name: "Elektron Model:Cycles (stand-in)", manufacturer: "Elektron", onmidimessage: null };
        var output = {
            id: "out1", name: "Elektron Model:Cycles (stand-in)", manufacturer: "Elektron",
            send: function (raw) {
                var reply;

                if (o.mute)
                    return;
                reply = E.frame(answer(E.unframe(Uint8Array.from(raw))));
                setTimeout(function () { if (input.onmidimessage) input.onmidimessage({ data: reply }); }, delay);
            }
        };
        var access = { inputs: new Map([["in1", input]]), outputs: new Map([["out1", output]]), onstatechange: null };

        Object.defineProperty(navigator, "requestMIDIAccess", {
            value: function () { return Promise.resolve(access); }, configurable: true
        });
        return { drive: drive };
    }

    return { install: install };
})();
