/* Host tests of the library (store.js) on its memory backend: tools/webmanager_check.sh */
"use strict";
const L = require("../../docs/manager/store.js");
const S = require("../../docs/manager/sysex.js");
const Z = require("../../docs/manager/zip.js");
const { check, same, rejects, done, u8, project } = require("./lib.js");

const fwA = Uint8Array.from({ length: 3000 }, (_, i) => (i * 3) & 0x7f);
const fwB = Uint8Array.from({ length: 2000 }, (_, i) => (i * 5) & 0x7f);
const p1 = S.join(project(1)), p2 = S.join(project(2)), p3 = S.join(project(3));
const t = n => new Date(Date.UTC(2026, 10, 2, 12, n)).toISOString();

(async () => {
    const lib = new L.Store(L.memory());

    /* builds */
    const a = (await lib.addBuild(fwA, "official 1.13", t(0))).build;
    const b = (await lib.addBuild(fwB, "model27 SAMPLE", t(1))).build;

    check(a.key === await S.sha256(fwA) && a.name === "official 1.13" && a.bytes === 3000 && a.current === null,
          "a build: its SHA-256, a name, no project yet");
    check(!(await lib.addBuild(fwA.slice(), "again")).added, "the same bytes again are the build already there");
    check((await lib.builds()).map(x => x.name).join() === "official 1.13,model27 SAMPLE", "builds in the order added");
    check(same(await lib.buildData(a.key), fwA), "a build's bytes come back");
    await lib.updateBuild(b.key, { name: "  model27 + SAMPLE ", notes: "Gerät ok" });
    check((await lib.build(b.key)).name === "model27 + SAMPLE" && (await lib.build(b.key)).notes === "Gerät ok", "rename, notes");
    await lib.updateBuild(b.key, { name: "   " });
    check((await lib.build(b.key)).name === "model27 + SAMPLE", "an empty name keeps the old one");

    /* the slot on the Cycles */
    check(a.slot === null && a.slotName === "", "a new build has no slot on the Cycles");
    await lib.updateBuild(b.key, { slot: " 03 ", slotName: " M27 " });
    check((await lib.build(b.key)).slot === 3 && (await lib.build(b.key)).slotName === "M27", "slot 03, named M27");
    for (const bad of ["", "0", "-2", "2.5", "x", null]) {
        await lib.updateBuild(a.key, { slot: 4 });
        await lib.updateBuild(a.key, { slot: bad });
        check((await lib.build(a.key)).slot === null, "slot " + JSON.stringify(bad) + " is no slot");
    }

    /* backups and the current one */
    const x1 = (await lib.addBackup(a.key, p1, 97, "first", t(10))).backup;

    check((await lib.build(a.key)).current === x1.key, "a new backup becomes its build's current one");
    const x2 = (await lib.addBackup(a.key, p2, 97, "", t(20))).backup;

    check((await lib.current(a.key)).key === x2.key, "the next one takes over");
    check((await lib.backups(a.key)).map(x => x.key).join() === [x2.key, x1.key].join(), "history: the newest first");
    const again = await lib.addBackup(a.key, p1.slice(), 97, "", t(30));

    check(!again.added && again.backup.key === x1.key && again.backup.made === t(30) && again.backup.name === "first",
          "the same backup again is the one there, made now, its name kept");
    check(again.was === t(10), "and says when it was made before: " + again.was);
    {
        const solo = new L.Store(L.memory()), sb = (await solo.addBuild(fwA)).build;

        check((await solo.addBackup(sb.key, p1, 97)).was === null, "a new backup was not made before");
    }
    check((await lib.backups(a.key)).length === 2 && (await lib.current(a.key)).key === x1.key, "and it is current again");
    check(same(await lib.backupData(x2.key), p2), "a backup's bytes come back");

    /* the same project on two builds: two records, one file */
    const y1 = (await lib.addBackup(b.key, p1, 97, "", t(40))).backup;

    check(y1.key !== x1.key && y1.hash === x1.hash, "the same backup on another build is its own record");
    await lib.removeBackup(x1.key);
    check(same(await lib.backupData(y1.key), p1), "its bytes stay while another build still holds them");
    check((await lib.current(a.key)).key === x2.key, "the current one went: the newest left takes over");
    await lib.removeBackup(y1.key);
    check((await lib.db.get("files", "backup/" + x1.hash)) === undefined, "the bytes go with the last record");
    check((await lib.build(b.key)).current === null, "no backup left: no current one");

    await lib.renameBackup(x2.key, "  vor dem Flash ");
    check((await lib.backup(x2.key)).name === "vor dem Flash", "rename a backup");
    await lib.setCurrent(a.key, null);
    check((await lib.current(a.key)) === null, "no current one, on purpose");
    await lib.setCurrent(a.key, x2.key);
    check(await rejects(lib.setCurrent(b.key, x2.key), /not one of this build's/), "another build's backup cannot be current");
    check(await rejects(lib.addBackup("nope", p3, 97), /no such build/), "a backup needs its build");

    /* the device */
    check((await lib.device()).build === null, "at first the page knows no build on the Cycles");
    await lib.setDevice(b.key, true);
    check(JSON.stringify(await lib.device()) === JSON.stringify({ build: b.key, sure: true }), "it flashed b");

    /* export and import */
    await lib.addBackup(b.key, p3, 97, "B", t(50));
    const zip = await lib.exportZip(new Date(2026, 10, 2, 13, 0, 0));
    const names = Z.read(zip).map(e => e.name);

    check(names[0] === "library.json" && names.filter(n => /^builds\//.test(n)).length === 2 &&
          names.filter(n => /^backups\//.test(n)).length === 2, "the export: library.json, 2 builds, 2 backups: " + names);
    const json = JSON.parse(new TextDecoder().decode(Z.read(zip)[0].data));

    check(json.format === "pfm-library" && json.version === 1 && json.builds.length === 2, "library.json says what it is");

    const other = new L.Store(L.memory());
    const r = await other.importZip(zip);

    check(r.builds === 2 && r.backups === 2 && !r.skipped.length, "a fresh library takes it all: " + JSON.stringify(r));
    check((await other.build(b.key)).name === "model27 + SAMPLE" && (await other.build(b.key)).notes === "Gerät ok", "names and notes");
    check((await other.build(b.key)).slot === 3 && (await other.build(b.key)).slotName === "M27" && (await other.build(a.key)).slot === null,
          "the slots on the Cycles");
    check((await other.current(a.key)).key === x2.key && (await other.current(b.key)).name === "B", "current backups");
    check(same(await other.backupData(x2.key), p2) && same(await other.buildData(b.key), fwB), "bytes");
    check((await other.device()).build === b.key, "the device, as this library knew none");

    const r2 = await other.importZip(zip);

    check(r2.builds === 0 && r2.backups === 0, "the same export again adds nothing");
    await other.updateBuild(a.key, { name: "mine" });
    await other.importZip(zip);
    check((await other.build(a.key)).name === "mine", "what is there stays as it is");

    {
        const entries = Z.read(zip).map(e => e.name.startsWith("backups/") && e.name.includes(x2.hash)
                                        ? { name: e.name, data: u8([0xf0, 0xf7]), date: e.date } : e);
        const fresh = new L.Store(L.memory());
        const r3 = await fresh.importZip(Z.write(entries));

        check(r3.backups === 1 && r3.skipped.length === 1 && /damaged/.test(r3.skipped[0]),
              "a backup whose bytes do not match is left out: " + JSON.stringify(r3));
        check((await fresh.current(a.key)) === null, "and is not current");
    }
    check(await rejects(new L.Store(L.memory()).importZip(Z.write([{ name: "x.txt", data: u8([1]) }])), /library\.json is missing/),
          "not an export");

    /* removing a build takes its backups and the device's claim */
    await lib.removeBuild(b.key);
    check((await lib.builds()).length === 1 && (await lib.backups(b.key)).length === 0, "build b and its backups are gone");
    check((await lib.db.get("files", "build/" + b.key)) === undefined, "and its file");
    check((await lib.device()).build === null, "the Cycles no longer counts as holding it");

    done();
})();
