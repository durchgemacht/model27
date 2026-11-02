/* Host tests of the flashing core as the manager uses it (docs/flasher/flasher.js, the flasher's own;
   tools/webflash_check.sh compares its .syx checks with mtlib): tools/webmanager_check.sh;
   OS_SYX=<official model-cycles_OS1.13.syx> adds the real file. */
"use strict";
const F = require("../../docs/flasher/flasher.js");
const S = require("../../docs/manager/sysex.js");
const { check, same, throws, rejects, done, u8 } = require("./lib.js");

/* A made-up firmware file for product 0x11: a head announcing n packets, n packets of 128 bytes
   with mtlib's checksum, a tail. */
function firmware(n, product) {
    const [, dev, V, C0] = F.PRODUCTS[0x11];
    const msgs = [];

    msgs.push(u8([0xf0, 0x00, 0x20, 0x3c, product || 0x11, dev, 0x7f, 0x01, 0, 0, 0, 0, (n >> 14) & 0x7f, (n >> 7) & 0x7f, n & 0x7f, 0xf7]));
    for (let k = 0; k < n; k++) {
        const m = new Uint8Array(128);

        m[0] = 0xf0;
        m.set([0x00, 0x20, 0x3c, 0x11, dev, 0x7f, 0x03], 1);
        for (let i = 8; i < 126; i++)
            m[i] = (i * 5 + k) & 0x7f;
        m[126] = F.packetChecksum(m, V, C0);
        m[127] = 0xf7;
        msgs.push(m);
    }
    msgs.push(u8([0xf0, 0x00, 0x20, 0x3c, product || 0x11, dev, 0x7f, 0x02, 0xf7]));
    return S.join(msgs);
}

/* A stand-in for a Transfer session: answers each request with replies[i], keeps the bodies. */
function session(replies) {
    const bodies = [];

    return {
        bodies,
        request(body) {
            bodies.push(Uint8Array.from(body));
            const r = replies[bodies.length - 1];
            return r instanceof Error ? Promise.reject(r) : Promise.resolve(u8(r));
        }
    };
}

(async () => {
    /* verify */
    {
        const fw = firmware(5);
        const v = F.verify(fw);

        check(v.product === 0x11 && v.name === "Model:Cycles" && v.count === 5 && v.messages === 7 && v.bytes === fw.length,
              "a made-up firmware passes: " + JSON.stringify(v));
        const bad = fw.slice();

        bad[16 + 128 * 2 + 50] ^= 1;
        check(throws(() => F.verify(bad), /packet 2: bad checksum/), "a changed byte fails its packet's checksum");
        check(throws(() => F.verify(firmware(3, 0x0d)), /unsupported product id 0xd/), "another product is refused");
        const lying = fw.slice();

        lying[14] = 6;
        check(throws(() => F.verify(lying), /announces 6 packets, 5 found/), "a head that announces another count");
        check(throws(() => F.verify(u8([0xf0, 1, 0xf7])), /too few SysEx messages/), "not a firmware at all");
    }

    /* the two copies of the 7-bit packing agree */
    for (let n = 0; n < 40; n++) {
        const src = Uint8Array.from({ length: n }, (_, i) => (i * 73 + n * 11) & 0xff);

        check(same(F.encode7(src), S.encode7(Array.from(src))), "flasher.js and sysex.js pack alike (" + n + ")");
        check(same(F.decode7(F.encode7(src)), src), "flasher.js unpacks what it packs (" + n + ")");
    }

    /* CRC-32 */
    check(F.crc32(new TextEncoder().encode("123456789")) === 0xcbf43926, "CRC-32 of 123456789 is CBF43926");

    /* upgradeFast: the start, then 2 KB blocks with CRC, length and offset, until the machine says done */
    {
        const raw = Uint8Array.from({ length: 5000 }, (_, i) => i & 0xff);
        const s = session([[0, 0, 0, 0, 0xd0, 0], [0, 0, 0, 0, 0xd1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0xd1, 0, 0, 0, 0, 0],
                           [0, 0, 0, 0, 0xd1, 0, 0, 0, 0, 1]]);
        const seen = [];
        const r = await F.upgradeFast(s, raw, { restMs: 0, onProgress: (d, t) => seen.push(d + "/" + t) });

        check(r.blocks === 3 && r.sent === 5000 && !r.cancelled, "5000 bytes go as three blocks: " + JSON.stringify(r));
        check(same(s.bodies[0], [0x50, 0x88, 0x13, 0x00, 0x00, 0x73, 0x79, 0x73, 0x65, 0x78, 0x00, 0x01]),
              "the start: 0x50, the size little-endian, \"sysex\", 1");
        const b = s.bodies[2], dv = new DataView(b.buffer);

        check(b[0] === 0x51 && dv.getUint32(5) === 2048 && dv.getUint32(9) === 2048, "the second block: 2048 bytes at 2048");
        check(dv.getUint32(1) === F.crc32(raw.subarray(2048, 4096), 0xffffffff), "with its CRC");
        check(same(b.subarray(13), raw.subarray(2048, 4096)), "and its bytes");
        check(new DataView(s.bodies[3].buffer).getUint32(5) === 904, "the last block is the rest");
        check(seen.join() === "2048/5000,4096/5000,5000/5000", "progress after each block: " + seen);
    }
    {
        const refused = session([[0, 0, 0, 0, 0xd0, 1, 0x6e, 0x6f, 0]]);

        check(await rejects(F.upgradeFast(refused, u8([1, 2, 3]), { restMs: 0 }), /refused: no/), "a refused start");
        const failing = session([[0, 0, 0, 0, 0xd0, 0], [0, 0, 0, 0, 0xd1, 0x62, 0x61, 0x64, 0, 2]]);

        check(await rejects(F.upgradeFast(failing, u8([1, 2, 3]), { restMs: 0 }), /^write/), "a block the machine cannot write");
        let stop = false;
        const s = session([[0, 0, 0, 0, 0xd0, 0], [0, 0, 0, 0, 0xd1, 0, 0, 0, 0, 0]]);
        const r = await F.upgradeFast(s, new Uint8Array(4096), { restMs: 0, isCancelled: () => stop, onProgress: () => { stop = true; } });

        check(r.cancelled && r.blocks === 1 && r.sent === 2048, "cancelled after the first block: " + JSON.stringify(r));
    }

    /* xferIdentify: the ping's device id and name, then the version */
    {
        const name = Array.from("Model Cycles", c => c.charCodeAt(0));
        const s = session([[0, 0, 0, 0, 0x81, 27, 0, ...name, 0], [0, 0, 0, 0, 0x82, 0, 0, 0, 0, 0, 0x31, 0x2e, 0x31, 0x33, 0]]);
        const id = await F.xferIdentify(s);

        check(id.id === 27 && id.device === "Model:Cycles" && id.product === 0x11 && id.name === "Model Cycles" && id.version === "1.13",
              "identity of a Model:Cycles: " + JSON.stringify(id));
    }

    /* xferOpen: one request at a time, answered by the reply with its sequence number and type */
    {
        const listeners = [], sent = [];
        const input = { addEventListener: (t, f) => listeners.push(f), removeEventListener: () => {} };
        const output = { send: m => sent.push(Uint8Array.from(m)) };
        const ses = await F.xferOpen(input, output);
        const p = ses.request([0x01], 500);
        const req = F.xferParse(sent[0]);

        check(req && req[4] === 0x01, "the request goes out framed for the Transfer protocol");
        const deliver = payload => listeners.forEach(f => f({ data: F.xferFrame(u8(payload)) }));

        deliver([0, 0, req[0], req[1] + 1, 0x81, 99]);
        deliver([0, 0, req[0], req[1], 0x82, 99]);
        deliver([0, 0, req[0], req[1], 0x81, 27]);
        const r = await p;

        check(r[5] === 27, "a reply with another sequence or type is skipped");
        check(await rejects(ses.request([0x02], 20), /timeout/), "no reply: a timeout");
        ses.close();
    }

    /* the manager names the official OS by the hash in device.json */
    const fs = require("fs"), path = require("path"), root = path.join(__dirname, "..", "..");
    const stock = JSON.parse(fs.readFileSync(path.join(root, "tweaks/model-cycles_OS1.13/device.json"), "utf8")).stock_syx_sha256;
    const app = fs.readFileSync(path.join(root, "docs/manager/app.js"), "utf8");

    check(app.indexOf('"' + stock + '": "Model:Cycles OS 1.13 (official)"') >= 0, "the manager's KNOWN holds the stock hash " + stock);

    /* the real official OS, if given */
    if (process.env.OS_SYX) {
        const raw = new Uint8Array(fs.readFileSync(process.env.OS_SYX));
        const v = F.verify(raw);
        const h = await S.sha256(raw);

        check(v.product === 0x11, "the official OS is for the Model:Cycles");
        check(h === stock, "and its SHA-256 is device.json's: " + h);
    }
    done();
})();
