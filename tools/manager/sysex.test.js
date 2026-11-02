/* Host tests of the SysEx helpers (sysex.js): tools/webmanager_check.sh */
"use strict";
const S = require("../../docs/manager/sysex.js");

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
function throws(f, pattern) {
    try {
        f();
    } catch (e) {
        return pattern.test(e.message);
    }
    return false;
}
const u8 = a => new Uint8Array(a);

const m1 = u8([0xf0, 0x00, 0x20, 0x3c, 0x0c, 0x00, 0x53, 0x01, 0x02, 0xf7]);
const m2 = u8([0xf0, 0x00, 0x20, 0x3c, 0x0c, 0x00, 0x53, 0x03, 0xf7]);
const m3 = u8([0xf0, 0x00, 0x20, 0x3c, 0x0c, 0x00, 0x54, 0x7f, 0x7f, 0x7f, 0xf7]);

/* split and join */
{
    const raw = S.join([m1, m2, m3]);
    const msgs = S.split(raw);

    check(raw.length === m1.length + m2.length + m3.length, "join puts the messages end to end");
    check(msgs.length === 3 && same(msgs[0], m1) && same(msgs[1], m2) && same(msgs[2], m3),
          "split gives the messages back, F0 and F7 included");
    check(same(S.join(msgs), raw), "split then join gives the file back byte for byte");
    check(S.size(msgs) === raw.length, "size counts every byte");
}
check(S.split(u8([])).length === 0, "an empty file holds no messages");
check(S.split(u8([0x00, 0x7f])).length === 0, "bytes without F0 hold no messages");
check(S.split(u8([0x00, ...m1, 0x12, ...m2])).length === 2, "bytes between messages are skipped");
check(throws(() => S.split(u8([0xf0, 0x00, 0x20])), /no end/), "a message without F7 is an error");
check(throws(() => S.split(u8([0xf0, 0x00, 0x90, 0x01, 0xf7])), /cut off by 0x90 at byte 2/),
      "a status byte inside a message is an error");
check(throws(() => S.split(u8([0xf0, 0x01, 0xf0, 0x02, 0xf7])), /cut off by 0xf0/),
      "an F0 inside a message is an error");

/* assembler */
{
    const got = [], feed = S.assembler((m, t) => got.push([m, t]));

    feed(m1, 10);
    check(got.length === 1 && same(got[0][0], m1) && got[0][1] === 10, "a whole message comes out as it went in");
    feed(m2.subarray(0, 4), 20);
    feed(m2.subarray(4), 30);
    check(got.length === 2 && same(got[1][0], m2) && got[1][1] === 30,
          "a message in two pieces comes out once, with the time of the piece that ended it");
    feed(u8([0xf0, 0x00, 0xf8, 0x20, 0xfe, 0x3c, 0xf7]), 40);
    check(got.length === 3 && same(got[2][0], [0xf0, 0x00, 0x20, 0x3c, 0xf7]),
          "real-time bytes inside a message are dropped, the message is kept");
    feed(S.join([m1, m3]), 50);
    check(got.length === 5 && same(got[3][0], m1) && same(got[4][0], m3), "two messages in one piece come out as two");
    feed(u8([0x90, 0x40, 0x7f, 0xf7]), 60);
    check(got.length === 5, "notes and an F7 without F0 give nothing");
    feed(u8([0xf0, 0x01, 0x02, 0x90, 0x40, 0x7f, 0xf7]), 70);
    check(got.length === 5, "a message cut off by a status byte is dropped");
    feed(m2, 80);
    check(got.length === 6 && same(got[5][0], m2), "after a dropped message the next one comes out whole");
}

/* hex, head and groups */
check(S.hex(u8([0x00, 0x0a, 0xff])) === "00 0a ff", "hex writes two digits per byte");
check(S.head(m1, 6) === "00 20 3c 0c 00 53", "head starts after F0");
check(S.head(m2, 20) === "00 20 3c 0c 00 53 03", "head stops before F7");
{
    const g = S.groups([m1, m2, m3, m1], 6);

    check(g.length === 3, "messages in a row that start alike form one group: " + g.length);
    check(g[0].count === 2 && g[0].bytes === m1.length + m2.length && g[0].first === 0, "the first group holds m1 and m2");
    check(g[1].head === "00 20 3c 0c 00 54" && g[1].first === 2, "the second group is m3");
    check(g[2].count === 1 && g[2].first === 3, "a head seen before starts a new group when another came between");
}

/* compare */
{
    const r = S.compare([m1, m2], [m1.slice(), m2.slice()]);

    check(r.identical && !r.diffs.length && !r.onlyA && !r.onlyB, "copies are identical");
}
{
    const b = m1.slice();

    b[7] = 0x11;
    b[8] = 0x12;
    const r = S.compare([m1, m2], [b, m2]);

    check(!r.identical && r.diffs.length === 1, "one changed message is one difference");
    check(r.diffs[0].index === 0 && r.diffs[0].bytes === 2 && r.diffs[0].first === 7 && r.diffs[0].last === 8,
          "the difference says how many bytes and where");
}
{
    const longer = u8([...m2.subarray(0, 8), 0x04, 0x05, 0xf7]);
    const r = S.compare([m2], [longer]);

    check(r.diffs.length === 1 && r.diffs[0].lengthA === 9 && r.diffs[0].lengthB === 11,
          "messages of different length differ");
    check(r.diffs[0].bytes === 3 && r.diffs[0].first === 8 && r.diffs[0].last === 10,
          "the F7 moved and two bytes more: 3 bytes from byte 8 to 10 (" + JSON.stringify(r.diffs[0]) + ")");
}
{
    const r = S.compare([m1, m2, m3], [m1]);

    check(!r.identical && !r.diffs.length && r.onlyA === 2 && r.onlyB === 0, "extra messages in A are counted");
    check(S.compare([m1], [m1, m2]).onlyB === 1, "extra messages in B are counted");
}

/* pacing and file names */
check(Math.abs(S.waitMs(3125, 1) - 1000) < 1e-9, "pace 1: 3125 bytes take a second, as on a MIDI cable");
check(Math.abs(S.waitMs(3125, 0.25) - 250) < 1e-9, "pace 0.25: a quarter of it");
check(S.waitMs(3125, 0) === 0, "pace 0: no wait");
{
    const d = new Date(2026, 10, 2, 9, 5, 7);

    check(S.fileName("SAMPLE test", d) === "SAMPLE test-2026-11-02-090507.syx", "file name: label, date and time");
    check(S.fileName("a/b:c", d) === "a-b-c-2026-11-02-090507.syx", "characters file systems refuse become '-'");
    check(S.fileName("  ", d) === "capture-2026-11-02-090507.syx", "an empty label becomes 'capture'");
}

/* dumps and requests */
function dump(type, index, data) {
    const sum = data.reduce((s, b) => s + b, 0) & 0x3fff, n = 15 + data.length;
    return u8([0xf0, 0x00, 0x20, 0x3c, 0x11, 0x00, type, 0x01, 0x01, index, ...data,
               sum >> 7, sum & 0x7f, ((n - 10) & 0x3fff) >> 7, (n - 10) & 0x7f, 0xf7]);
}
{
    const p = dump(0x50, 21, [0x7f, 0x7f, 0x01, 0x40]);

    check(S.dumpType(p) === 0x50, "a pattern dump is type 0x50");
    check(S.dumpOk(p), "a dump with the right checksum and length passes");
    const bad = p.slice();
    bad[11] ^= 1;
    check(!S.dumpOk(bad), "a changed data byte fails the checksum");
    const big = dump(0x50, 0, new Array(300).fill(0x7f));
    check(S.dumpOk(big), "a checksum above 2^7 is split in two 7-bit bytes");
    check(S.dumpType(m1) === -1 && !S.dumpOk(m1), "a message of another device or too short is no dump");
    check(S.dumpType(u8([0xf0, 0x00, 0x20, 0x3c, 0x10, 0x00, 0x6f, 1, 1, 0, 0, 0, 0, 5, 0xf7])) === -1,
          "a Transfer-protocol message is no dump");
}
check(same(S.request(0x6f, 0), [0xf0, 0x00, 0x20, 0x3c, 0x11, 0x00, 0x6f, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x05, 0xf7]),
      "the project request: type 6F, no data, checksum 0, length 5");
check(S.dumpOk(S.request(0x6f, 0)) && S.dumpType(S.request(0x64, 0)) === 0x64, "a request passes the checks the OS makes");
check(S.request(0x60, 95)[9] === 95, "a pattern request carries the pattern's index");

/* the Transfer protocol */
for (let n = 0; n <= 30; n++) {
    const src = Array.from({ length: n }, (_, i) => (i * 37 + n) & 0xff);
    check(same(S.decode7(u8(S.encode7(src))), src), "7-bit packing round trip (" + n + " bytes)");
}
check(same(S.rpc(1, 0x01), [0xf0, 0x00, 0x20, 0x3c, 0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x01, 0xf7]),
      "a ping with sequence 1, as the uploader and the flasher send it");
check(same(S.rpc(0x1234, 0x02).subarray(6, 12), [0x00, 0x12, 0x34, 0x00, 0x00, 0x02]), "the sequence number is big-endian");
{
    const reply = S.rpc(7, 0x81);
    const m = S.rpcReply(reply);

    check(m && m[1] === 7 && m[4] === 0x81, "a reply's payload is unpacked");
    check(S.rpcReply(m1) === null, "a dump is no Transfer-protocol reply");
    check(S.rpcText(u8([0x41, 0x42, 0x00, 0x43]), 0) === "AB", "text stops at its NUL");
}

/* a real backup, if one is given: BACKUP_SYX=path tools/webmanager_check.sh */
if (process.env.BACKUP_SYX) {
    const msgs = S.split(new Uint8Array(require("fs").readFileSync(process.env.BACKUP_SYX)));

    check(msgs.length === 97, "a project backup is 97 messages: " + msgs.length);
    check(msgs.every(S.dumpOk), "every message of the backup passes its checksum and length");
    check(msgs.slice(0, 96).every((m, i) => S.dumpType(m) === 0x50 && m[9] === i), "patterns 0 to 95 in order");
    check(S.dumpType(msgs[96]) === 0x54, "then the settings");
}

(async () => {
    check(await S.sha256(new TextEncoder().encode("abc")) ===
          "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "SHA-256 of abc, as FIPS 180-2 gives it");
    check((await S.sha256(u8([]))).length === 64, "SHA-256 as 64 hex digits");

    if (failures) {
        console.log(failures + " failed");
        process.exit(1);
    }
    console.log("ALL OK");
})();
