/* model27's manager: the library (notes/77 §4). Builds, each with its backups and its
   current one; the bytes of each .syx; which build is on the Cycles. Exported to one ZIP and
   imported from it. The logic runs on a backend with get, put, delete and all per store, each
   record under its "key": memory() for the host tests, indexedDB() for the page. No page code. */
(function (exports, S, Z) {
    "use strict";

    var STORES = ["builds", "backups", "files", "meta"];
    var FORMAT = "pfm-library", VERSION = 1;

    /* builds:  { key: id, name, added, bytes, current: backup key or null, notes, slot, slotName };
                id = SHA-256; slot and slotName: the project slot on the Cycles that holds this
                build's project (a number, or null when not given), and the name it has there
       backups: { key: build + "/" + hash, hash, build, name, made, bytes, messages }
       files:   { key: "build/" + id or "backup/" + hash, data }; a backup's bytes once, however
                many builds hold the same backup
       meta:    { key: "device", build, sure } */
    function Store(db) {
        this.db = db;
    }

    function now() { return new Date().toISOString(); }
    function byAdded(a, b) { return a.added < b.added ? -1 : a.added > b.added ? 1 : 0; }
    function newestFirst(a, b) { return a.made < b.made ? 1 : a.made > b.made ? -1 : 0; }

    Store.prototype.builds = async function () {
        return (await this.db.all("builds")).sort(byAdded);
    };

    Store.prototype.build = function (id) {
        return this.db.get("builds", id);
    };

    /* A firmware's bytes as a build. The same bytes twice are one build: the one already there. */
    Store.prototype.addBuild = async function (data, name, added) {
        var id = await S.sha256(data), old = await this.db.get("builds", id), b;

        if (old)
            return { build: old, added: false };
        b = { key: id, name: name || id.slice(0, 8), added: added || now(), bytes: data.length, current: null, notes: "",
              slot: null, slotName: "" };
        await this.db.put("files", { key: "build/" + id, data: data });
        await this.db.put("builds", b);
        return { build: b, added: true };
    };

    /* changes: { name, notes, slot, slotName }; a slot that is not a whole number from 1 up is none. */
    Store.prototype.updateBuild = async function (id, changes) {
        var b = await this.need(id), n;

        if (changes.name !== undefined)
            b.name = String(changes.name).trim() || b.name;
        if (changes.notes !== undefined)
            b.notes = String(changes.notes);
        if (changes.slot !== undefined) {
            n = Number(String(changes.slot === null ? "" : changes.slot).trim());
            b.slot = String(changes.slot === null ? "" : changes.slot).trim() && Number.isInteger(n) && n >= 1 ? n : null;
        }
        if (changes.slotName !== undefined)
            b.slotName = String(changes.slotName).trim();
        await this.db.put("builds", b);
        return b;
    };

    Store.prototype.buildData = async function (id) {
        var f = await this.db.get("files", "build/" + id);

        return f ? f.data : null;
    };

    /* A build, its file and its backups; the Cycles no longer counts as holding it. */
    Store.prototype.removeBuild = async function (id) {
        var list = await this.backups(id), d = await this.device(), i;

        for (i = 0; i < list.length; i++)
            await this.dropBackup(list[i]);
        await this.db.delete("files", "build/" + id);
        await this.db.delete("builds", id);
        if (d.build === id)
            await this.setDevice(null, false);
    };

    Store.prototype.need = async function (id) {
        var b = await this.db.get("builds", id);

        if (!b)
            throw new Error("no such build: " + id);
        return b;
    };

    /* A build's backups, the newest first. */
    Store.prototype.backups = async function (build) {
        return (await this.db.all("backups")).filter(function (x) { return x.build === build; }).sort(newestFirst);
    };

    Store.prototype.backup = function (key) {
        return this.db.get("backups", key);
    };

    Store.prototype.current = async function (build) {
        var b = await this.need(build);

        return b.current ? this.db.get("backups", b.current) : null;
    };

    /* A backup's bytes for a build; it becomes that build's current one. The same backup again is
       the one already there, made now; was is when it was made before. messages: how many messages
       it holds. */
    Store.prototype.addBackup = async function (build, data, messages, name, made) {
        var b = await this.need(build), hash = await S.sha256(data), key = build + "/" + hash,
            old = await this.db.get("backups", key), was = old ? old.made : null, x;

        if (!await this.db.get("files", "backup/" + hash))
            await this.db.put("files", { key: "backup/" + hash, data: data });
        x = old || { key: key, hash: hash, build: build, name: name || "", bytes: data.length, messages: messages };
        x.made = made || now();
        await this.db.put("backups", x);
        b.current = key;
        await this.db.put("builds", b);
        return { backup: x, added: !old, was: was };
    };

    Store.prototype.backupData = async function (key) {
        var x = await this.db.get("backups", key), f = x && await this.db.get("files", "backup/" + x.hash);

        return f ? f.data : null;
    };

    Store.prototype.renameBackup = async function (key, name) {
        var x = await this.db.get("backups", key);

        if (!x)
            throw new Error("no such backup: " + key);
        x.name = String(name).trim();
        await this.db.put("backups", x);
        return x;
    };

    Store.prototype.setCurrent = async function (build, key) {
        var b = await this.need(build), x = key ? await this.db.get("backups", key) : null;

        if (key && (!x || x.build !== build))
            throw new Error("backup " + key + " is not one of this build's");
        b.current = key || null;
        await this.db.put("builds", b);
    };

    /* A backup goes; if it was its build's current one, the newest left takes its place. */
    Store.prototype.removeBackup = async function (key) {
        var x = await this.db.get("backups", key), b, left;

        if (!x)
            return;
        await this.dropBackup(x);
        b = await this.db.get("builds", x.build);
        if (b && b.current === key) {
            left = await this.backups(x.build);
            b.current = left.length ? left[0].key : null;
            await this.db.put("builds", b);
        }
    };

    /* The record, and its bytes once no other build's backup has the same. */
    Store.prototype.dropBackup = async function (x) {
        await this.db.delete("backups", x.key);
        if (!(await this.db.all("backups")).some(function (y) { return y.hash === x.hash; }))
            await this.db.delete("files", "backup/" + x.hash);
    };

    /* Which build the Cycles holds, and whether the page is sure of it (it flashed it, or the user
       said so). */
    Store.prototype.device = async function () {
        var d = await this.db.get("meta", "device");

        return d ? { build: d.build, sure: d.sure } : { build: null, sure: false };
    };

    Store.prototype.setDevice = function (build, sure) {
        return this.db.put("meta", { key: "device", build: build || null, sure: !!(build && sure) });
    };

    /* Everything as one ZIP: library.json, builds/<id>.syx, backups/<hash>.syx. */
    Store.prototype.exportZip = async function (date) {
        var builds = await this.builds(), backups = await this.db.all("backups"), seen = {}, files = [], i, d;

        date = date || new Date();
        for (i = 0; i < builds.length; i++)
            files.push({ name: "builds/" + builds[i].key + ".syx", data: await this.buildData(builds[i].key), date: date });
        for (i = 0; i < backups.length; i++)
            if (!seen[backups[i].hash]) {
                seen[backups[i].hash] = true;
                files.push({ name: "backups/" + backups[i].hash + ".syx", data: await this.backupData(backups[i].key), date: date });
            }
        d = await this.device();
        files.unshift({ name: "library.json", date: date, data: new TextEncoder().encode(JSON.stringify({
            format: FORMAT, version: VERSION, exported: date.toISOString(), device: d,
            builds: builds, backups: backups.sort(newestFirst)
        }, null, 1)) });
        return Z.write(files);
    };

    /* What an export holds that this library lacks is added; what it already has stays as it is.
       A file whose bytes do not match its name is left out. The device is taken only if this library
       knows of none. Returns { builds, backups, skipped: [reasons] }. */
    Store.prototype.importZip = async function (bytes) {
        var entries = Z.read(bytes), files = {}, lib, out = { builds: 0, backups: 0, skipped: [] }, fresh = {}, i, b, x, data, d;

        entries.forEach(function (e) { files[e.name] = e.data; });
        if (!files["library.json"])
            throw new Error("not an export of this manager: library.json is missing");
        lib = JSON.parse(new TextDecoder().decode(files["library.json"]));
        if (lib.format !== FORMAT || lib.version > VERSION)
            throw new Error("not an export this version can read (" + lib.format + " " + lib.version + ")");
        for (i = 0; i < lib.builds.length; i++) {
            b = lib.builds[i];
            data = files["builds/" + b.key + ".syx"];
            if (await this.db.get("builds", b.key))
                continue;
            if (!data || await S.sha256(data) !== b.key) {
                out.skipped.push("build " + b.name + ": its file is missing or damaged");
                continue;
            }
            await this.db.put("files", { key: "build/" + b.key, data: data });
            await this.db.put("builds", { key: b.key, name: b.name, added: b.added, bytes: data.length, current: null, notes: b.notes || "",
                                          slot: Number.isInteger(b.slot) && b.slot >= 1 ? b.slot : null, slotName: b.slotName || "" });
            fresh[b.key] = b.current;
            out.builds++;
        }
        for (i = 0; i < lib.backups.length; i++) {
            x = lib.backups[i];
            data = files["backups/" + x.hash + ".syx"];
            if (await this.db.get("backups", x.key))
                continue;
            if (!await this.db.get("builds", x.build)) {
                out.skipped.push("a backup of a build that is not there");
                continue;
            }
            if (!data || await S.sha256(data) !== x.hash) {
                out.skipped.push("backup " + (x.name || x.made) + ": its file is missing or damaged");
                continue;
            }
            if (!await this.db.get("files", "backup/" + x.hash))
                await this.db.put("files", { key: "backup/" + x.hash, data: data });
            await this.db.put("backups", { key: x.key, hash: x.hash, build: x.build, name: x.name || "", made: x.made,
                                           bytes: data.length, messages: x.messages });
            out.backups++;
        }
        for (b in fresh)
            if (fresh[b] && await this.db.get("backups", fresh[b]))
                await this.setCurrent(b, fresh[b]);
        d = await this.device();
        if (!d.build && lib.device && lib.device.build && await this.db.get("builds", lib.device.build))
            await this.setDevice(lib.device.build, lib.device.sure);
        return out;
    };

    /* ---- backends ------------------------------------------------------------------------ */

    /* In memory, records copied in and out as IndexedDB does. */
    function memory() {
        var maps = {};

        STORES.forEach(function (s) { maps[s] = new Map(); });
        function copy(v) { return v === undefined ? undefined : structuredClone(v); }
        return {
            get: function (s, k) { return Promise.resolve(copy(maps[s].get(k))); },
            put: function (s, v) { maps[s].set(v.key, copy(v)); return Promise.resolve(); },
            delete: function (s, k) { maps[s].delete(k); return Promise.resolve(); },
            all: function (s) { return Promise.resolve(Array.from(maps[s].values()).map(copy)); }
        };
    }

    /* IndexedDB, one database with the four stores. */
    function indexedDB(name) {
        var opening = new Promise(function (resolve, reject) {
            var r = globalThis.indexedDB.open(name || "project-and-firmware-manager", 1);

            r.onupgradeneeded = function () {
                STORES.forEach(function (s) {
                    if (!r.result.objectStoreNames.contains(s))
                        r.result.createObjectStore(s, { keyPath: "key" });
                });
            };
            r.onsuccess = function () { resolve(r.result); };
            r.onerror = function () { reject(r.error); };
            r.onblocked = function () { reject(new Error("the library is open in another tab with an older version")); };
        });

        function run(s, mode, f) {
            return opening.then(function (db) {
                return new Promise(function (resolve, reject) {
                    var t = db.transaction(s, mode), r = f(t.objectStore(s));

                    t.oncomplete = function () { resolve(r.result); };
                    t.onerror = function () { reject(t.error); };
                    t.onabort = function () { reject(t.error || new Error("aborted")); };
                });
            });
        }
        return {
            get: function (s, k) { return run(s, "readonly", function (o) { return o.get(k); }); },
            put: function (s, v) { return run(s, "readwrite", function (o) { return o.put(v); }).then(function () {}); },
            delete: function (s, k) { return run(s, "readwrite", function (o) { return o.delete(k); }).then(function () {}); },
            all: function (s) { return run(s, "readonly", function (o) { return o.getAll(); }); }
        };
    }

    exports.Store = Store;
    exports.memory = memory;
    exports.indexedDB = indexedDB;
    exports.FORMAT = FORMAT;
})(typeof module !== "undefined" && module.exports ? module.exports : (window.Library = {}),
   typeof module !== "undefined" && module.exports ? require("./sysex.js") : window.Sysex,
   typeof module !== "undefined" && module.exports ? require("./zip.js") : window.Zip);
