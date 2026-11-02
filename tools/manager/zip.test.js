/* Host tests of the export file (zip.js): tools/webmanager_check.sh. With the system's zip and unzip, it also checks
   that they read what zip.js writes and that zip.js reads what zip writes. */
"use strict";
const Z = require("../../docs/manager/zip.js");
const { check, same, throws, done, u8 } = require("./lib.js");
const fs = require("fs"), os = require("os"), path = require("path"), { execFileSync } = require("child_process");

const date = new Date(2026, 10, 2, 14, 30, 58);
const files = [
    { name: "library.json", data: new TextEncoder().encode('{"format":"pfm-library","version":1}'), date },
    { name: "builds/44fe5862.syx", data: Uint8Array.from({ length: 70000 }, (_, i) => (i * 7) & 0xff), date },
    { name: "backups/ä ö ü.syx", data: u8([0xf0, 0x7f, 0xf7]), date },
    { name: "empty.txt", data: u8([]), date },
];

check(Z.crc32(new TextEncoder().encode("123456789")) === 0xcbf43926, "CRC-32 of 123456789 is CBF43926");
check(Z.crc32(u8([])) === 0, "CRC-32 of nothing is 0");

const zip = Z.write(files);
const back = Z.read(zip);

check(back.length === files.length, "every file comes back: " + back.length);
files.forEach((f, i) => {
    check(back[i].name === f.name, "name " + f.name + " (UTF-8)");
    check(same(back[i].data, f.data), "bytes of " + f.name);
    check(back[i].date.getTime() === date.getTime(), "date of " + f.name + " (to two seconds): " + back[i].date);
});
check(zip.length === files.reduce((s, f) => s + 30 + 46 + new TextEncoder().encode(f.name).length * 2 + f.data.length, 22),
      "stored, nothing added: headers, names and bytes only");
check(Z.read(Z.write([])).length === 0, "an empty ZIP");

{
    const bad = zip.slice();

    bad[30 + "library.json".length + 3] ^= 1;
    check(throws(() => Z.read(bad), /library\.json fails its CRC/), "a changed byte fails the CRC");
    check(throws(() => Z.read(u8([1, 2, 3])), /not a ZIP file/), "not a ZIP at all");
    check(throws(() => Z.read(zip.subarray(0, zip.length - 30)), /not a ZIP file|damaged/), "a cut-off ZIP");
}

/* the system's tools, if there are any */
function have(tool) {
    try {
        execFileSync("which", [tool], { stdio: "ignore" });
        return true;
    } catch (e) {
        return false;
    }
}
if (have("unzip") && have("zip")) {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "pfm-zip-"));
    const ours = path.join(dir, "ours.zip");

    fs.writeFileSync(ours, zip);
    const list = execFileSync("unzip", ["-t", ours]).toString();

    check(/No errors detected/.test(list), "unzip -t finds no errors in what zip.js writes");
    fs.mkdirSync(path.join(dir, "in", "builds"), { recursive: true });
    fs.writeFileSync(path.join(dir, "in", "builds", "a.syx"), files[1].data);
    fs.writeFileSync(path.join(dir, "in", "library.json"), files[0].data);
    execFileSync("zip", ["-0", "-q", "-r", "-X", path.join(dir, "theirs.zip"), "."], { cwd: path.join(dir, "in") });
    const theirs = Z.read(new Uint8Array(fs.readFileSync(path.join(dir, "theirs.zip"))));
    const a = theirs.find(e => e.name === "builds/a.syx");

    check(a && same(a.data, files[1].data), "zip.js reads a ZIP made by zip -0: " + theirs.map(e => e.name));
    execFileSync("zip", ["-9", "-q", "-r", "-X", path.join(dir, "packed.zip"), "."], { cwd: path.join(dir, "in") });
    check(throws(() => Z.read(new Uint8Array(fs.readFileSync(path.join(dir, "packed.zip")))), /compressed/),
          "a compressed ZIP is refused with a clear reason");
    fs.rmSync(dir, { recursive: true });
} else
    console.log("(zip/unzip not found: skipped the check against the system's tools)");

done();
