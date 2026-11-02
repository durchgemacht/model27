/* Host tests of the backup checks (backup.js): tools/webmanager_check.sh */
"use strict";
const B = require("../../docs/manager/backup.js");
const S = require("../../docs/manager/sysex.js");
const { check, done, dump, project } = require("./lib.js");

(async () => {
    const p = project(1);

    check(B.whole(p) && !B.problems(p).length, "a made-up project of 96 patterns and the settings is whole");
    check(B.settings(p) === p[96], "its settings are the last message");

    {
        const short = p.slice(0, 95).concat([p[96]]);
        const pr = B.problems(short);

        check(!B.whole(short), "a missing pattern is not whole");
        check(pr[0] === "96 messages instead of 97", "the count comes first: " + pr[0]);
        check(pr.some(s => /message 96 should be pattern 96/.test(s)), "and where it goes wrong: " + pr.join("; "));
    }
    {
        const bad = p.slice();

        bad[21] = p[21].slice();
        bad[21][20] ^= 1;
        check(B.problems(bad).join() === "message 22 is damaged (checksum or length)", "a changed byte: " + B.problems(bad));
    }
    {
        const swapped = p.slice();

        swapped[3] = p[4];
        swapped[4] = p[3];
        const pr = B.problems(swapped);

        check(pr.length === 2 && /message 4 should be pattern 4, is pattern 5/.test(pr[0]), "patterns out of order: " + pr);
    }
    {
        const noSettings = p.slice(0, 96).concat([dump(0x50, 95, [1])]);

        check(B.problems(noSettings).join() === "message 97 should be the settings, is type 50", "no settings at the end");
        check(B.settings(noSettings) === null, "and no settings to compare");
    }
    check(B.problems(p.concat([p[96]])).length === 2, "a message too many: the count and the extra one");
    check(/is not a Model:Cycles backup message/.test(B.problems([new Uint8Array([0xf0, 1, 2, 0xf7])]).join()),
          "another device's message");
    {
        const junk = Array.from({ length: 97 }, () => new Uint8Array([0xf0, 1, 2, 0xf7]));
        const pr = B.problems(junk);

        check(pr.length === 6 && pr[5] === "and 92 more", "many problems: five listed, the rest counted: " + pr.slice(-1));
    }

    check(await B.id(p) === await B.id(project(1)), "the same project gives the same id");
    check(await B.id(p) !== await B.id(project(2)), "another project another id");
    check(await B.id(p) === await S.sha256(S.join(p)), "the id is the SHA-256 of the backup as a .syx");

    if (process.env.BACKUP_SYX) {
        const real = S.split(new Uint8Array(require("fs").readFileSync(process.env.BACKUP_SYX)));

        check(B.whole(real), "the real backup is whole: " + B.problems(real).join("; "));
    }
    done();
})();
