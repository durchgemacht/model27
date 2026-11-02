/* Shared by the host tests: checks that count failures, and the report at the end. */
"use strict";

let failures = 0;

function check(cond, what) {
    if (!cond) {
        failures++;
        console.log("FAIL: " + what);
    }
}

function same(a, b) {
    if (!a || !b || a.length !== b.length)
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

async function rejects(p, pattern) {
    try {
        await p;
    } catch (e) {
        return pattern.test(e.message);
    }
    return false;
}

function done() {
    if (failures) {
        console.log(failures + " failed");
        process.exit(1);
    }
    console.log("ALL OK");
}

const u8 = a => new Uint8Array(a);

/* A Model:Cycles dump message: type, index and data, with its checksum and length. */
function dump(type, index, data) {
    const sum = data.reduce((s, b) => s + b, 0) & 0x3fff, n = 15 + data.length;

    return u8([0xf0, 0x00, 0x20, 0x3c, 0x11, 0x00, type, 0x01, 0x01, index, ...data,
               sum >> 7, sum & 0x7f, ((n - 10) & 0x3fff) >> 7, (n - 10) & 0x7f, 0xf7]);
}

/* A whole made-up project backup: 96 patterns and the settings, each with a little data. */
function project(seed) {
    const msgs = [];

    for (let i = 0; i < 96; i++)
        msgs.push(dump(0x50, i, Array.from({ length: 40 }, (_, k) => (k * 3 + i + seed) & 0x7f)));
    msgs.push(dump(0x54, 0, Array.from({ length: 20 }, (_, k) => (k + seed) & 0x7f)));
    return msgs;
}

module.exports = { check, same, throws, rejects, done, u8, dump, project };
