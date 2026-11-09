/* model27's uploader: the page. Web MIDI to the Model:Cycles, the folders on its +Drive, audio converted in the
   browser and written with the device's own file commands (elektron.js).
   From Cycles One-Shot's upload page (github.com/durchgemacht/cycles-one-shot, uploader/, MIT, text in
   ../flasher/LICENSE-One-Shot.txt): the same requests and checks, in the site's page (the manager's connect chip and
   status line). The page: the files to upload on the left, as a tree of folders; the Cycles' folder on the right.
   Rows are selected with a click (⌘/Ctrl, Shift for more), then deleted or removed together; rows dragged onto a
   folder of the list move into it, onto the Cycles' side they are uploaded there, with their folders. */
(function () {
    "use strict";
    var E = window.Elektron;
    var POOL = 63 * 1024 * 1024;    /* SAMPLE's sample memory: a bigger file would never load */
    /* Why this browser cannot talk to the Cycles, as the manager tells it */
    var NO_MIDI = typeof window.isSecureContext !== "undefined" && !window.isSecureContext ? "insecure" :
                  !navigator.requestMIDIAccess ? "none" : null;
    var NO_MIDI_TEXT = {
        none: "This browser has no Web MIDI, so this page can't talk to your Cycles. Open it in Chrome, Edge or Opera " +
              "on a computer.",
        insecure: "Web MIDI needs a secure page, so this one can't talk to your Cycles. Open the online version, or serve " +
                  "the docs folder with python3 -m http.server."
    };
    var state = {
        access: null, input: null, output: null, seq: 1, pending: null, rx: null,
        path: "/", items: [], busy: false, connected: false, asked: false,
        showPorts: false, naming: false,
        sel: [], anchor: -1,                    /* the names selected on the Cycles, the row Shift starts from */
        selecting: false,                       /* Select is on: a box on each row, a click picks instead of opening */
        tree: { dir: true, name: "", kids: [], open: true, up: null },   /* the list to upload */
        fsel: [], fanchor: -1, renaming: null,  /* the nodes selected in it, the row Shift starts from, the one renamed */
        drag: null,                             /* the nodes being dragged */
        alerting: false, alertBack: null        /* the window of a warning or a problem is open; where focus goes back */
    };

    function $(id) { return document.getElementById(id); }
    function hex(n) { return "0x" + n.toString(16).padStart(2, "0"); }

    /* The one status line, under the header: news plain, a warning dashed, a problem inverted. A warning or a problem
       also opens a window over the page, which stays until OK (the maintainer's wish of 2026-11-08: the line alone was
       easy to miss); rows: the files it is about, { name, why }. */
    function show(text, kind, rows) {
        $("status").textContent = text;
        $("status").className = "status" + (kind ? " " + kind : "");
        $("status").hidden = false;
        if (kind === "warn" || kind === "bad")
            alertBox(text, kind, rows || []);
    }

    var ALERT_ROWS = 12;    /* the files named in the window; the list on the page has them all */

    /* The window: its title Warning, or Problem once a problem is in it; a second message while it is open goes under
       the first. A dialog (showModal: the page behind it is inert), closed by OK or Escape. */
    function alertBox(text, kind, rows) {
        var d = $("alert"), body = $("alert-body"), p = document.createElement("p"), ul, li, b, why, i;

        if (!state.alerting) {
            body.innerHTML = "";
            d.className = "alert";
            state.alertBack = document.activeElement || null;
        }
        if (kind === "bad")
            d.className = "alert bad";
        $("alert-h").textContent = /\bbad\b/.test(d.className) ? "Problem" : "Warning";
        p.textContent = text;
        body.appendChild(p);
        if (rows.length) {
            ul = document.createElement("ul");
            for (i = 0; i < rows.length && i < ALERT_ROWS; i++) {
                li = document.createElement("li");
                b = document.createElement("b");
                b.textContent = rows[i].name;
                why = document.createElement("span");
                why.textContent = rows[i].why;
                li.appendChild(b);
                li.appendChild(why);
                ul.appendChild(li);
            }
            if (rows.length > ALERT_ROWS) {
                li = document.createElement("li");
                li.textContent = "And " + (rows.length - ALERT_ROWS) + " more: see the list.";
                ul.appendChild(li);
            }
            body.appendChild(ul);
        }
        if (!state.alerting) {
            state.alerting = true;
            if (typeof d.showModal === "function")
                d.showModal();
            else
                d.hidden = false;
        }
        $("alert-ok").focus();
    }
    function closeAlert() {
        var d = $("alert");

        if (!state.alerting)
            return;
        if (typeof d.close === "function" && d.open)
            d.close();          /* onclose follows */
        else {
            d.hidden = true;
            alertClosed();
        }
    }
    function alertClosed() {
        var back = state.alertBack;

        state.alerting = false;
        state.alertBack = null;
        if (back && typeof back.focus === "function" && document.body && document.body.contains &&
            document.body.contains(back))
            back.focus();
    }
    function kb(n) { return n >= 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.ceil(n / 1024) + " KB"; }

    /* ---- MIDI ---------------------------------------------------------------------------- */

    function likely(p) { return /cycles|elektron/i.test(p.name + " " + (p.manufacturer || "")); }

    function fillPorts() {
        [["in", state.access.inputs], ["out", state.access.outputs]].forEach(function (pair) {
            var sel = $(pair[0]), keep = sel.value, ports = Array.from(pair[1].values()), pick = keep;

            sel.innerHTML = "";
            ports.forEach(function (p) {
                var o = document.createElement("option");

                o.value = p.id;
                o.textContent = p.name;
                sel.appendChild(o);
            });
            if (!ports.some(function (p) { return p.id === pick; })) {
                var guess = ports.filter(likely)[0] || ports[0];

                pick = guess ? guess.id : "";
            }
            sel.value = pick;
        });
    }

    async function connect() {
        if (NO_MIDI) {
            show(NO_MIDI_TEXT[NO_MIDI], "bad");
            return;
        }
        try {
            state.access = await navigator.requestMIDIAccess({ sysex: true });
        } catch (e) {
            show("MIDI access was refused (" + e.message + "). Allow MIDI with SysEx for this page.", "bad");
            return;
        }
        state.access.onstatechange = function () { fillPorts(); render(); };
        fillPorts();
        await usePorts();
    }

    async function usePorts() {
        if (state.input)
            state.input.onmidimessage = null;
        state.input = state.access.inputs.get($("in").value) || null;
        state.output = state.access.outputs.get($("out").value) || null;
        state.connected = false;
        state.asked = false;
        if (!state.input || !state.output) {
            show("Pick the Model:Cycles as MIDI input and output.", "bad");
            render();
            return;
        }
        state.input.onmidimessage = onMidi;
        state.asked = true;
        try {
            await send(E.TYPE.PING, [], 3000);
            state.connected = true;
            state.showPorts = false;
            $("status").hidden = true;     /* the chip says it; what the line said before is past */
            await listDir(state.path);
        } catch (e) {
            show("The Cycles does not answer: " + e.message + ". Close Elektron Transfer if it is open: it holds the " +
                 "USB connection.", "bad");
        }
        render();
    }

    /* SysEx may come in pieces, with real-time bytes in between. */
    function onMidi(ev) {
        var d = ev.data, i;

        for (i = 0; i < d.length; i++) {
            var b = d[i];

            if (b === 0xf0)
                state.rx = [0xf0];
            else if (b === 0xf7) {
                if (state.rx) {
                    state.rx.push(0xf7);
                    reply(new Uint8Array(state.rx));
                    state.rx = null;
                }
            } else if (b < 0xf8 && state.rx)
                state.rx.push(b);
        }
    }

    function reply(sysex) {
        var m = E.unframe(sysex), w = state.pending;

        if (!m || !w || E.replySeq(m) !== w.seq)
            return;
        state.pending = null;
        clearTimeout(w.timer);
        if (m[4] !== (w.type | 0x80))
            w.reject(new Error("unexpected reply " + hex(m[4]) + " to " + hex(w.type)));
        else
            w.resolve(m);
    }

    /* One request at a time; resolves with the reply's message. */
    function send(type, body, timeout) {
        return new Promise(function (resolve, reject) {
            var seq, w;

            if (!state.output)
                return reject(new Error("no MIDI output"));
            if (state.pending)
                return reject(new Error("still waiting for the last reply"));
            seq = state.seq;
            state.seq = (state.seq + 1) & 0xffff;
            w = { seq: seq, type: type, resolve: resolve, reject: reject };
            w.timer = setTimeout(function () {
                if (state.pending === w)
                    state.pending = null;
                reject(new Error("no reply within " + timeout / 1000 + " s"));
            }, timeout);
            state.pending = w;
            try {
                state.output.send(E.frame(E.request(seq, type, body)));
            } catch (e) {
                clearTimeout(w.timer);
                state.pending = null;
                reject(e);
            }
        });
    }

    /* ---- the Cycles' folders --------------------------------------------------------------- */

    /* A folder's entries, without moving the page there. */
    async function readDir(path) {
        return E.parseDir(await send(E.TYPE.READ_DIR, E.pathBytes(path), 5000));
    }

    function byKind(a, b) {
        return !!a.dir !== !!b.dir || !!a.folder !== !!b.folder ? (a.dir || a.folder ? -1 : 1) : a.name.localeCompare(b.name);
    }

    /* Shows a folder; listed again, it keeps what is still selected, opened anew it starts with nothing selected. */
    async function listDir(path) {
        var items = await readDir(path), same = path === state.path;

        state.path = path;
        state.items = items.sort(byKind);
        state.sel = same ? state.sel.filter(function (n) { return items.some(function (x) { return x.name === n; }); }) : [];
        if (!same)
            state.anchor = -1;
        render();
        return state.items;
    }

    /* The name typed in the field under the path, made in the folder shown and opened. */
    async function makeFolder() {
        var name = E.cleanName(($("dirname").value || "") + ".x"), m;   /* cleanName drops only the dummy extension */

        if (!name) {
            show("Type a name for the new folder.", "warn");
            return;
        }
        m = await send(E.TYPE.CREATE_DIR, E.pathBytes(E.joinPath(state.path, name)), 5000);
        if (!E.replyOk(m))
            throw new Error(E.replyText(m) || "the Cycles did not make the folder");
        state.naming = false;
        $("dirname").value = "";
        await listDir(E.joinPath(state.path, name));
        show("Folder " + state.path + " made.", "ok");
    }

    /* What the page offers no delete for: what the Cycles marks protected, and /incoming, which it
       makes when it formats its drive (the files in it can go). */
    function kept(it) {
        return it.writeProtected || (state.path === "/" && it.folder && it.name === "incoming");
    }

    /* The Cycles deletes only an empty folder, so its contents go first, one request at a time. */
    async function remove(path, folder) {
        var items, m, i;

        if (folder) {
            items = await readDir(path);
            for (i = 0; i < items.length; i++)
                await remove(E.joinPath(path, items[i].name), items[i].folder);
        }
        show("Deleting " + path + "…");
        m = await send(folder ? E.TYPE.DELETE_DIR : E.TYPE.DELETE_FILE, E.pathBytes(path), 30000);
        if (!E.replyOk(m))
            throw new Error("the Cycles did not delete " + path + (E.replyText(m) ? ": " + E.replyText(m) : ""));
    }

    function plural(n, one) { return n + " " + one + (n === 1 ? "" : "s"); }
    function sentence(s) { return s.charAt(0).toUpperCase() + s.slice(1) + "."; }

    /* The selected samples and folders, after one question; the first one the Cycles refuses stops it. */
    async function deleteSelected() {
        var here = state.path, picked, files, dirs, question, i, items;

        picked = state.items.filter(function (it) { return state.sel.indexOf(it.name) >= 0 && !kept(it); });
        if (!picked.length)
            return;
        files = picked.filter(function (it) { return !it.folder; }).length;
        dirs = picked.length - files;
        question = picked.length === 1 ? (picked[0].folder ? "Delete the folder “" + picked[0].name + "” and everything in it from the Cycles?"
                                                           : "Delete “" + picked[0].name + "” from the Cycles?")
                                       : "Delete " + [files ? plural(files, "sample") : "", dirs ? plural(dirs, "folder") : ""]
                                             .filter(Boolean).join(" and ") + (dirs ? " with everything in them" : "") + " from the Cycles?";
        if (!window.confirm(question + " This cannot be undone."))
            return;
        try {
            for (i = 0; i < picked.length; i++)
                await remove(E.joinPath(here, picked[i].name), picked[i].folder);
        } catch (e) {
            await listDir(here).catch(function () {});   /* show what is left */
            throw e;
        }
        items = await listDir(here);
        picked.forEach(function (it) {
            if (items.some(function (x) { return x.name === it.name; }))
                throw new Error(it.name + " is still in the folder afterwards");
        });
        show(picked.length === 1 ? "Deleted " + E.joinPath(here, picked[0].name) + "."
                                 : "Deleted " + plural(picked.length, "item") + " from " + here + ".", "ok");
    }

    /* ---- the list to upload: a tree -------------------------------------------------------- */

    /* A node is a folder { dir: true, name, kids, open, up } or a file { name, file, up }; both carry how their upload
       went: state (what the row shows), why (a line under the name), kind ("ok", "warn", "skip", "bad"), done (a file
       written or skipped, a folder there on the Cycles). The list itself is a folder without a name, state.tree. */
    var AUDIO = /\.(wav|wave|aif|aiff|aifc|mp3|flac|ogg|oga|opus|m4a|aac)$/i;

    function isAudio(f) { return f.name.charAt(0) !== "." && (AUDIO.test(f.name) || /^audio\//.test(f.type || "")); }
    function node(up, props) {
        var n = { name: "", up: up, state: "", why: "", kind: "", done: false };

        Object.keys(props).forEach(function (k) { n[k] = props[k]; });
        up.kids.push(n);
        return n;
    }
    /* The folder of that name in up, made if there is none: what is added twice goes into the same folder. */
    function folderIn(up, name) {
        return up.kids.filter(function (k) { return k.dir && k.name === name; })[0] ||
               node(up, { dir: true, name: name, kids: [], open: true });
    }
    function fileIn(up, f) { return node(up, { name: E.cleanName(f.name), file: f }); }
    /* Is a inside folder b (at any depth)? */
    function within(a, b) {
        for (var d = a.up; d; d = d.up)
            if (d === b)
                return true;
        return false;
    }
    /* The nodes, without those that are inside another one of them. */
    function topsOf(nodes) {
        return nodes.filter(function (n) { return !nodes.some(function (m) { return m !== n && within(n, m); }); });
    }
    function detach(n) { n.up.kids.splice(n.up.kids.indexOf(n), 1); }
    function filesIn(d) { return d.kids.reduce(function (s, n) { return s + (n.dir ? filesIn(n) : 1); }, 0); }
    function doneIn(d) { return d.kids.reduce(function (s, n) { return s + (n.dir ? doneIn(n) : n.done ? 1 : 0); }, 0); }
    function dirsToMake(d) { return d.kids.reduce(function (s, n) { return s + (n.dir ? (n.done ? 0 : 1) + dirsToMake(n) : 0); }, 0); }

    /* The rows as the list shows them: each open folder followed by what is in it, folders first. */
    function visible() {
        var out = [];

        (function walk(d, depth) {
            d.kids.slice().sort(byKind).forEach(function (n) {
                out.push({ n: n, depth: depth });
                if (n.dir && n.open)
                    walk(n, depth + 1);
            });
        })(state.tree, 0);
        return out;
    }

    /* Where Add files, Add folder and New folder put things: the one folder selected, else the list itself. */
    function target() {
        return state.fsel.length === 1 && state.fsel[0].dir ? state.fsel[0] : state.tree;
    }

    function leftOut(n) {
        if (n)
            show(plural(n, "file") + " left out: not audio.", "warn");
    }

    /* Files from the chooser into a folder of the list; from Add folder they come with their folders
       (webkitRelativePath). Audio only. Returns what was added at the top. */
    function addFiles(list, into) {
        var out = 0, tops = [];

        Array.from(list).forEach(function (f) {
            var parts = (f.webkitRelativePath || "").split("/").filter(Boolean), d = into, k;

            if (!isAudio(f)) {
                out++;
                return;
            }
            for (k = 0; k < parts.length - 1; k++) {
                d = folderIn(d, E.cleanName(parts[k] + ".x"));
                if (!k && tops.indexOf(d) < 0)
                    tops.push(d);
            }
            if (d === into)
                tops.push(fileIn(d, f));
            else
                fileIn(d, f);
        });
        into.open = true;
        leftOut(out);
        render();
        return tops;
    }

    /* A folder's entries as the browser hands them over, a batch at a time. */
    function readAll(dir) {
        return new Promise(function (resolve, reject) {
            var reader = dir.createReader(), out = [];

            (function more() {
                reader.readEntries(function (list) {
                    if (!list.length)
                        return resolve(out);
                    out = out.concat(Array.from(list));
                    more();
                }, reject);
            })();
        });
    }

    /* A dropped file or folder (an entry) into a folder of the list; a folder without audio in it is left out. */
    async function addEntry(entry, into, count) {
        var d, had, kids, i, f;

        if (entry.isDirectory) {
            had = into.kids.some(function (k) { return k.dir && k.name === E.cleanName(entry.name + ".x"); });
            d = folderIn(into, E.cleanName(entry.name + ".x"));
            kids = await readAll(entry);
            for (i = 0; i < kids.length; i++)
                await addEntry(kids[i], d, count);
            if (!had && !d.kids.length) {
                detach(d);
                return null;
            }
            return d;
        }
        f = await new Promise(function (resolve, reject) { entry.file(resolve, reject); });
        if (!isAudio(f)) {
            count.out++;
            return null;
        }
        return fileIn(into, f);
    }

    /* What a drop from the computer brings, taken while the event lasts: entries where the browser gives them
       (folders too), else the files. */
    function dropped(dt) {
        var entries = [];

        Array.from((dt && dt.items) || []).forEach(function (it) {
            var e = it.kind === "file" && it.webkitGetAsEntry ? it.webkitGetAsEntry() : null;

            if (e)
                entries.push(e);
        });
        return entries.length ? { entries: entries } : { files: Array.from((dt && dt.files) || []) };
    }

    async function addDropped(d, into) {
        var count = { out: 0 }, tops = [], i, n;

        if (!d.entries)
            return addFiles(d.files, into);
        for (i = 0; i < d.entries.length; i++) {
            n = await addEntry(d.entries[i], into, count);
            if (n && tops.indexOf(n) < 0)
                tops.push(n);
        }
        into.open = true;
        leftOut(count.out);
        render();
        return tops;
    }

    function fromComputer(dt) {
        return !!dt && Array.from(dt.types || []).indexOf("Files") >= 0;
    }

    /* Rows dragged onto a folder of the list go into it; a folder never into itself or a folder inside it. */
    function moveInto(nodes, into) {
        topsOf(nodes).forEach(function (n) {
            if (n === into || n.up === into || within(into, n))
                return;
            detach(n);
            n.up = into;
            into.kids.push(n);
        });
        into.open = true;
        render();
    }

    function uniqueName(up, base) {
        var name = base, k = 2;

        while (up.kids.some(function (x) { return x.name === name; }))
            name = base + " " + k++;
        return name;
    }

    /* A new folder in the list, named at once. */
    function newListFolder() {
        var into = target(), d = folderIn(into, uniqueName(into, "New folder"));

        into.open = true;
        state.fsel = [d];
        startRename(d);
        renderTools();
    }

    function removeFiles() {
        topsOf(state.fsel).forEach(detach);
        state.fsel = [];
        state.fanchor = -1;
        render();
    }

    /* ---- uploading --------------------------------------------------------------------------- */

    /* Decoded by the browser at the Cycles' rate, its channels averaged: the 16-bit frames. */
    async function convert(file) {
        var ctx = new OfflineAudioContext(1, 1, E.RATE), buf, ch = [], c;

        buf = await ctx.decodeAudioData(await file.arrayBuffer());
        for (c = 0; c < buf.numberOfChannels; c++)
            ch.push(buf.getChannelData(c));
        return E.toInt16(E.mixDown(ch));
    }

    function unplayable(n) {
        var e = new Error("CHORD Tables plays " + E.CYCLE + " to " + E.CYCLE * E.TABLE_MAX + " samples in steps of " +
                          E.CYCLE + ", this file has " + n);

        e.unplayable = true;
        return e;
    }

    /* A row's state while it goes: only its own text changes, the list is drawn again when it is through. */
    function progress(n, text) {
        n.state = text;
        if (n.stateEl)
            n.stateEl.textContent = text;
        else
            renderFiles();
    }

    function overall(done, total) {
        $("overall").hidden = total === undefined;
        if (total !== undefined)
            $("overall-fill").style.width = Math.round(100 * done / total) + "%";
    }

    /* A folder's listing, read once per upload and again after each write into it; cache: by path. */
    async function listing(dir, cache) {
        if (!cache[dir])
            cache[dir] = await readDir(dir);
        return cache[dir];
    }

    /* A folder on the Cycles, made unless it is there already. */
    async function ensureDir(path, cache) {
        var up = E.parentPath(path), name = path.slice(path.lastIndexOf("/") + 1), m,
            there = (await listing(up, cache)).filter(function (x) { return x.name === name; })[0];

        if (there) {
            if (!there.folder)
                throw new Error("a sample named " + name + " is already in " + up);
            return;
        }
        m = await send(E.TYPE.CREATE_DIR, E.pathBytes(path), 5000);
        if (!E.replyOk(m))
            throw new Error(E.replyText(m) || "the Cycles did not make the folder " + path);
        cache[up] = null;
        cache[path] = [];
    }

    function two(n) { return (n < 10 ? "0" : "") + n; }

    /* What CHORD Tables will do otherwise than the file says, in /Wavetables (notes/66 §36): a name without a number
       01 to 63 it does not play; of two files with one number it plays the name first in byte order; a table whose
       first frame is no sine gets the OS's sine in front of it (§27.10). items: the folder before this file. "" when
       it plays the file as it is. */
    function tableWarning(name, frames, items) {
        var n = E.tableNumber(name), said = [], others, first;

        if (!n)
            return "CHORD Tables plays only names that start with 01 to 63, such as 07 Glass Pad, so it does not play " +
                   "this one";
        others = items.filter(function (x) { return !x.folder && x.name !== name && E.tableNumber(x.name) === n; });
        if (others.length) {
            first = others.reduce(function (a, b) { return E.playsFirst(a.name, b.name) <= 0 ? a : b; });
            said.push(E.playsFirst(name, first.name) < 0
                ? "CHORD Tables plays this one as table " + two(n) + ", not " + others.map(function (x) { return x.name; })
                      .join(" or ") + ": its name comes first"
                : "table " + two(n) + " already has " + first.name + ", which CHORD Tables plays: its name comes first");
        }
        if (!E.startsWithSine(frames))
            said.push("its first waveform is not a sine, so CHORD Tables puts a sine in front of it, which SWEEP plays " +
                      "at the far left");
        return said.join("; ");
    }

    /* One file into a folder of the Cycles. A name already in that folder is skipped: the sample there stays as it
       is. part(f): how far it got, 0 to 1. */
    async function upload(entry, dir, cache, part) {
        var path = E.joinPath(dir, entry.name), items, frames, data, m, id, off, chunk, found, warn = "";

        if (!entry.name)
            throw new Error("give it a name");
        items = await listing(dir, cache);
        if (items.some(function (x) { return x.name === entry.name; })) {
            entry.done = entry.skipped = true;
            entry.kind = "skip";
            entry.why = "Something named " + entry.name + " is already in " + dir + "; it stays as it is.";
            progress(entry, "skipped");
            return;
        }
        progress(entry, "converting");
        try {
            frames = await convert(entry.file);
        } catch (e) {
            throw new Error("the browser cannot read this audio file");
        }
        data = E.sampleFile(frames, E.RATE);
        /* CHORD Tables plays this folder: a file it cannot play is not written; one it will not play as the file is
           written with a warning (tableWarning) */
        if (dir === E.WAVETABLES) {
            if (!E.tableFrames(frames))
                throw unplayable(frames.length);
            warn = tableWarning(entry.name, frames, items);
        }
        if (data.length - 80 > POOL)
            throw new Error("too long: SAMPLE holds up to 63 MB, this is " + kb(data.length));
        progress(entry, "opening");
        m = await send(E.TYPE.OPEN_WRITE, E.u32(data.length).concat(E.pathBytes(path)), 10000);
        if (!E.replyOk(m))
            throw new Error(E.replyText(m) || "the Cycles did not open the file");
        id = E.readU32(m, 6);
        for (off = 0; off < data.length; off += E.BLOCK) {
            chunk = data.subarray(off, Math.min(off + E.BLOCK, data.length));
            m = await send(E.TYPE.WRITE, E.u32(id).concat(E.u32(chunk.length), E.u32(off), Array.from(chunk)), 10000);
            if (!E.replyOk(m))
                throw new Error("writing stopped at byte " + off);
            progress(entry, Math.floor((off + chunk.length) * 100 / data.length) + " %");
            part((off + chunk.length) / data.length);
        }
        progress(entry, "finishing");
        m = await send(E.TYPE.CLOSE_WRITE, E.u32(id).concat(E.u32(data.length)), 60000);
        if (!E.replyOk(m))
            throw new Error(E.replyText(m) || "the Cycles did not finish the file");
        items = cache[dir] = await readDir(dir);
        if (dir === state.path) {
            state.items = items.slice().sort(byKind);
            renderFolder();
        }
        found = items.filter(function (x) { return !x.folder && x.name === entry.name; })[0];
        if (!found)
            throw new Error("the file is not in the folder afterwards");
        if (found.size !== data.length)
            throw new Error("the Cycles has " + found.size + " bytes, " + data.length + " were sent");
        entry.done = true;
        entry.kind = warn ? "warn" : "ok";
        entry.why = warn ? "Warning: " + warn + "." : "";
        progress(entry, "done · " + kb(data.length));
    }

    /* What uploading these nodes into base does, in order: each folder before what is in it; written files and
       folders already made are left out. */
    function jobs(nodes, base, out) {
        nodes.slice().sort(byKind).forEach(function (n) {
            var path = E.joinPath(base, n.name);

            if (n.dir) {
                if (!n.done || filesIn(n) > doneIn(n) || dirsToMake(n)) {
                    out.push({ dir: true, node: n, path: path });
                    jobs(n.kids, path, out);
                }
            } else if (!n.done)
                out.push({ node: n, into: base, path: path });
        });
        return out;
    }

    /* The nodes, with everything in them, into a folder of the Cycles; their folders are made there. */
    async function uploadNodes(nodes, base) {
        var list = jobs(topsOf(nodes), base, []), files = list.filter(function (j) { return !j.dir; }), cache = {},
            broken = [], ok = 0, warned = 0, refused = 0, skipped = 0, made = 0, k = 0, said, notes, j, i;

        if (!list.length)
            return;
        if (files.length)
            overall(0, files.length);
        for (i = 0; i < list.length; i++) {
            j = list[i];
            j.node.kind = j.node.why = "";
            if (broken.some(function (b) { return j.path.indexOf(b + "/") === 0; })) {
                j.node.kind = "bad";
                j.node.why = "Its folder could not be made on the Cycles.";
                progress(j.node, "failed");
                k += j.dir ? 0 : 1;
                continue;
            }
            if (j.dir) {
                try {
                    await ensureDir(j.path, cache);
                    j.node.done = true;
                    made++;
                } catch (e) {
                    broken.push(j.path);
                    j.node.kind = "bad";
                    j.node.why = sentence(e.message);
                }
                renderFiles();
                continue;
            }
            show("Uploading " + j.path + " (" + (k + 1) + " of " + files.length + ")…");
            overall(k, files.length);
            try {
                await upload(j.node, j.into, cache, function (f) { overall(k + f, files.length); });
                if (j.node.skipped)
                    skipped++;
                else
                    ok++;
                if (j.node.kind === "warn")
                    warned++;
            } catch (e) {
                if (e.unplayable)
                    refused++;
                j.node.kind = "bad";
                j.node.why = sentence(e.message);
                progress(j.node, "failed");
            }
            k++;
            renderFiles();
        }
        overall();
        await listDir(state.path);
        if (!files.length) {
            show(broken.length ? "The folder could not be made." : plural(made, "folder") + " made in " + base + ".",
                 broken.length ? "bad" : "ok", list.filter(function (x) { return x.node.kind === "bad" && x.node.why; })
                                                 .map(function (x) { return { name: x.path, why: x.node.why }; }));
            return;
        }
        notes = list.filter(function (x) { return x.node.kind && x.node.kind !== "ok" && x.node.why; })
                    .map(function (x) { return { name: x.path, why: x.node.why }; });
        said = ok + " of " + files.length + " uploaded to " + base + ".";
        if (skipped)
            said += " " + skipped + " skipped: the name is already there.";
        if (refused)
            said += " " + refused + " not uploaded: CHORD Tables cannot play it.";
        if (warned)
            said += " " + warned + " with a warning.";
        show(said, ok + skipped !== files.length ? "bad" : warned || skipped ? "warn" : "ok", notes);
    }

    /* ---- selecting ----------------------------------------------------------------------- */

    /* A click picks one row, ⌘/Ctrl adds or takes one, Shift takes the run from the last one clicked; rows that
       cannot be picked (the Cycles' protected ones) are left out. keys: the rows' keys in order; can: whether a row
       can be picked. Returns the new selection. */
    function pick(sel, anchor, keys, i, ev, can) {
        var a, b, k, out;

        if (ev && ev.shiftKey && anchor >= 0) {
            a = Math.min(anchor, i);
            b = Math.max(anchor, i);
            out = ev.metaKey || ev.ctrlKey ? sel.slice() : [];
            for (k = a; k <= b; k++)
                if (can(k) && out.indexOf(keys[k]) < 0)
                    out.push(keys[k]);
            return out;
        }
        if (!can(i))
            return sel;
        if (ev && (ev.metaKey || ev.ctrlKey))
            return sel.indexOf(keys[i]) >= 0 ? sel.filter(function (x) { return x !== keys[i]; }) : sel.concat([keys[i]]);
        return [keys[i]];
    }

    function names() { return state.items.map(function (it) { return it.name; }); }
    function canPick(k) { return !kept(state.items[k]); }

    /* A Shift-click with nothing clicked before starts the run there. */
    function selectRow(i, ev) {
        state.sel = pick(state.sel, state.anchor, names(), i, ev, canPick);
        if (!(ev && ev.shiftKey) || state.anchor < 0)
            state.anchor = i;
        renderFolder();
        renderTools();
        if ($("folder").focus)
            $("folder").focus();
    }

    function selectFile(i, ev) {
        var keys = visible().map(function (r) { return r.n; });

        state.fsel = pick(state.fsel, state.fanchor, keys, i, ev, function () { return true; });
        if (!(ev && ev.shiftKey) || state.fanchor < 0)
            state.fanchor = i;
        renderFiles();
        renderTools();
        if ($("files").focus)
            $("files").focus();
    }

    function openFolder(it) { return guarded(function () { return listDir(E.joinPath(state.path, it.name)); })(); }

    /* ---- dragging ------------------------------------------------------------------------ */

    /* Rows of the list dragged (state.drag) or files from the computer: onto a folder of the list they go into it, onto
       the Cycles' side they are uploaded, into the folder under the pointer or the one open. */
    function into(elm, on) {
        elm.className = elm.className.replace(/ into$/, "") + (on ? " into" : "");
    }

    function onList(dir, elm) {
        return {
            over: function (ev) {
                if (state.busy || !(state.drag || fromComputer(ev.dataTransfer)))
                    return;
                ev.preventDefault();
                ev.stopPropagation();
                if (elm)
                    into(elm, true);
            },
            leave: function () {
                if (elm)
                    into(elm, false);
            },
            drop: function (ev) {
                var d;

                ev.preventDefault();
                ev.stopPropagation();
                if (elm)
                    into(elm, false);
                $("src").className = "pane src";
                if (state.busy)
                    return;
                if (state.drag) {
                    moveInto(state.drag, dir);
                    state.drag = null;
                    return;
                }
                d = dropped(ev.dataTransfer);
                return addDropped(d, dir);
            }
        };
    }

    function onCycles(path, elm) {
        return {
            over: function (ev) {
                if (state.busy || !state.connected || !(state.drag || fromComputer(ev.dataTransfer)))
                    return;
                ev.preventDefault();
                ev.stopPropagation();
                into(elm, true);
            },
            leave: function () { into(elm, false); },
            drop: function (ev) {
                var nodes = state.drag, d = nodes ? null : dropped(ev.dataTransfer);

                ev.preventDefault();
                ev.stopPropagation();
                into(elm, false);
                $("src").className = "pane src";
                state.drag = null;
                if (state.busy)
                    return;
                if (!state.connected)       /* nothing to upload to yet: files from the computer join the list */
                    return d ? addDropped(d, state.tree) : undefined;
                if (nodes)
                    return guarded(uploadNodes)(nodes, path());
                return guarded(async function () { await uploadNodes(await addDropped(d, state.tree), path()); })();
            }
        };
    }

    function wire(elm, h) {
        elm.ondragover = h.over;
        elm.ondragleave = h.leave;
        elm.ondrop = h.drop;
    }

    /* ---- the page ------------------------------------------------------------------------ */

    /* Runs fn while nothing else runs; its error goes to the status line. */
    function guarded(fn) {
        return async function () {
            var args = arguments;

            if (state.busy)
                return;
            state.busy = true;
            render();
            try {
                await fn.apply(null, args);
            } catch (e) {
                show(e.message, "bad");
            } finally {
                state.busy = false;
                overall();
                render();
            }
        };
    }

    function el(tag, cls, text) {
        var e = document.createElement(tag);

        if (cls)
            e.className = cls;
        if (text !== undefined)
            e.textContent = text;
        return e;
    }

    function renderChip() {
        var c = $("chip");

        c.className = "chip" + (state.connected ? "" : " off");
        c.disabled = state.busy || !!NO_MIDI;
        $("chip-text").textContent = NO_MIDI ? "No Web MIDI" : !state.access ? "Connect the Cycles" :
                                     state.connected ? "Cycles connected" :
                                     !(state.input && state.output) ? "Pick the MIDI ports" :
                                     state.busy && state.asked ? "Asking…" : "No answer";
        $("ports").hidden = !(state.access && (state.showPorts || !state.connected));
        c.setAttribute("aria-expanded", String(!$("ports").hidden));
    }

    /* +Drive › My Samples › Drums: every part but the last one opens its folder. */
    function renderPath() {
        var nav = $("path"), parts = state.path === "/" ? [] : state.path.slice(1).split("/"), i, to, last, b;

        nav.innerHTML = "";
        nav.setAttribute("data-path", state.path);
        for (i = 0; i <= parts.length; i++) {
            to = "/" + parts.slice(0, i).join("/");
            last = i === parts.length;
            if (i)
                nav.appendChild(el("span", "sep", "›"));
            b = el(last ? "span" : "button", "crumb" + (last ? " here" : ""), i ? parts[i - 1] : "+Drive");
            if (last)
                b.setAttribute("aria-current", "location");
            else {
                b.type = "button";
                b.disabled = state.busy || !state.connected;
                b.onclick = (function (p) { return guarded(function () { return listDir(p); }); })(to);
            }
            nav.appendChild(b);
        }
    }

    function renderFolder() {
        var list = $("folder");

        list.innerHTML = "";
        list.className = "rows" + (state.selecting && state.connected ? " selecting" : "");
        if (!state.connected) {
            list.innerHTML = '<li class="empty">Connect the Cycles to see its folders.</li>';
            return;
        }
        state.items.forEach(function (it, i) {
            var on = state.sel.indexOf(it.name) >= 0,
                li = el("li", (it.folder ? "folder" : "file") + (kept(it) ? " kept" : "") + (on ? " sel" : "")),
                name = el("span", "nm"), open;

            li.setAttribute("aria-selected", String(on));
            name.appendChild(el("b", "", it.name));
            li.appendChild(el("span", "box" + (kept(it) ? " off" : "")));   /* shown while Select is on */
            li.appendChild(el("span", "pix " + (it.folder ? "dir" : "smp")));
            li.appendChild(name);
            li.appendChild(el("span", "size", it.folder ? (it.writeProtected ? "protected" : "") : kb(it.size)));
            if (it.folder) {
                open = el("span", "open", "›");     /* says the row opens; the whole row does it */
                open.setAttribute("aria-hidden", "true");
                li.appendChild(open);
                li.title = state.selecting ? "" : "Open " + it.name;
                if (!kept(it))
                    wire(li, onCycles(function () { return E.joinPath(state.path, it.name); }, li));
            }
            /* a click opens a folder and selects a sample; with ⌘/Ctrl or Shift it selects either. While Select is on,
               a click adds or takes a row, Shift a run. The second click of a double-click is dropped: it would land
               in the folder just opened */
            li.onclick = function (ev) {
                if (state.busy || (ev && ev.detail > 1))
                    return;
                if (state.selecting)
                    return selectRow(i, { metaKey: true, shiftKey: !!(ev && ev.shiftKey) });
                if (it.folder && !(ev && (ev.metaKey || ev.ctrlKey || ev.shiftKey)))
                    return openFolder(it);
                selectRow(i, ev);
            };
            list.appendChild(li);
        });
        if (!state.items.length)
            list.innerHTML = '<li class="empty">' + (state.path === "/" ? "The drive is empty." : "This folder is empty.") + "</li>";
    }

    function startRename(n) {
        var box;

        if (state.busy || n.done)
            return;
        state.renaming = n;
        renderFiles();
        box = $("files").querySelector && $("files").querySelector("input.rename");
        if (box) {
            box.focus();
            box.select();
        }
    }

    function endRename(n, typed) {
        if (state.renaming !== n)
            return;
        if (typed !== null)
            n.name = E.cleanName(typed + ".x") || n.name;
        state.renaming = null;
        renderFiles();
        if ($("files").focus)
            $("files").focus();
    }

    /* What a row of the list says on its right: a file its size or how far it got, a folder how many files are in it
       and how many are through. */
    function rowState(n) {
        var all, done;

        if (!n.dir)
            return { text: n.state || kb(n.file.size), kind: n.kind };
        all = filesIn(n);
        done = doneIn(n);
        if (n.kind === "bad")
            return { text: "failed", kind: "bad" };
        if (!all)
            return { text: n.done ? "made" : "empty", kind: n.done ? "ok" : "" };
        if (done === all)
            return { text: plural(all, "file"), kind: "ok" };
        return { text: done ? done + " of " + all : plural(all, "file"), kind: "" };
    }

    function renderFiles() {
        var list = $("files"), rows = visible();

        list.innerHTML = "";
        rows.forEach(function (r, i) {
            var n = r.n, on = state.fsel.indexOf(n) >= 0, li = el("li", (n.dir ? "folder" : "file") + (on ? " sel" : "")),
                name = el("span", "nm"), tw, st, said = rowState(n), input;

            li.style.paddingLeft = 6 + 18 * r.depth + "px";
            li.setAttribute("aria-selected", String(on));
            if (n.dir && n.kids.length) {
                tw = el("button", "twisty", n.open ? "▾" : "▸");
                tw.type = "button";
                tw.title = n.open ? "Close " + n.name : "Open " + n.name;
                tw.onclick = function (ev) {
                    if (ev)
                        ev.stopPropagation();
                    n.open = !n.open;
                    renderFiles();
                };
            } else
                tw = el("span", "twisty");
            li.appendChild(tw);
            li.appendChild(el("span", "pix " + (n.dir ? "dir" : "smp")));
            if (state.renaming === n) {
                input = el("input", "rename");
                input.value = n.name;
                input.maxLength = E.NAME_MAX;
                input.setAttribute("aria-label", n.dir ? "Name of the folder on the Cycles" : "Name on the Cycles");
                /* Enter or leaving the field takes the name, Escape keeps the old one; a typed name keeps its dots
                   (cleanName drops only the dummy extension) */
                input.onkeydown = function (ev) {
                    if (ev.key === "Enter" || ev.key === "Escape") {
                        if (ev.preventDefault)
                            ev.preventDefault();
                        endRename(n, ev.key === "Enter" ? input.value : null);
                    }
                };
                input.onblur = function () { endRename(n, input.value); };
                name.appendChild(input);
            } else
                name.appendChild(el("b", "", n.name));
            if (n.why)
                name.appendChild(el("span", "why", n.why));
            li.appendChild(name);
            st = el("span", "state" + (said.kind ? " " + said.kind : ""), said.text);
            n.stateEl = n.dir ? null : st;
            li.appendChild(st);
            li.onclick = function (ev) {
                if (!state.busy && state.renaming !== n)
                    selectFile(i, ev);
            };
            /* a double-click opens or closes a folder with something in it, else renames the row */
            li.ondblclick = function () {
                if (n.dir && n.kids.length) {
                    n.open = !n.open;
                    renderFiles();
                } else
                    startRename(n);
            };
            /* a row dragged takes the selection with it, or itself alone if it is not selected */
            li.draggable = !state.busy && state.renaming !== n;
            li.ondragstart = function (ev) {
                if (state.fsel.indexOf(n) < 0) {
                    state.fsel = [n];
                    state.fanchor = i;
                    Array.from(list.children).forEach(function (c) { c.className = c.className.replace(/ sel$/, ""); });
                    li.className += " sel";
                }
                state.drag = state.fsel.slice();
                if (ev && ev.dataTransfer) {
                    ev.dataTransfer.effectAllowed = "copyMove";
                    ev.dataTransfer.setData("text/plain", state.drag.map(function (x) { return x.name; }).join("\n"));
                }
            };
            li.ondragend = function () {
                state.drag = null;
                render();
            };
            if (n.dir)
                wire(li, onList(n, li));
            list.appendChild(li);
        });
        if (!rows.length)
            list.innerHTML = '<li class="drop-here">Drop audio files or folders here, or Add files.</li>';
    }

    /* The tools follow the selection; Upload names how many files go where. */
    function renderTools() {
        var ready = state.connected && !state.busy, n = filesIn(state.tree) - doneIn(state.tree), dirs = dirsToMake(state.tree),
            del = state.items.filter(function (it) { return state.sel.indexOf(it.name) >= 0 && !kept(it); }).length;

        $("select-mode").disabled = !ready;
        $("select-mode").setAttribute("aria-pressed", String(state.selecting));
        $("del-sel").textContent = del ? "Delete " + del : "Delete";
        $("del-sel").disabled = !ready || !del;
        $("remove-sel").textContent = state.fsel.length ? "Remove " + state.fsel.length : "Remove";
        $("remove-sel").disabled = state.busy || !state.fsel.length;
        $("upload").textContent = "Upload " + (n ? plural(n, "file") + " " : dirs ? plural(dirs, "folder") + " " : "") + "→ " + state.path;
        $("upload").disabled = !ready || !(n || dirs);
    }

    function render() {
        var ready = state.connected && !state.busy;

        renderChip();
        $("in").disabled = $("out").disabled = $("retry").disabled = state.busy || !state.access;
        $("mkdir").disabled = !ready || state.naming;
        $("refresh").disabled = !ready;
        $("newdir").hidden = !state.naming;
        $("dirname").disabled = $("mkdir-ok").disabled = !ready;
        $("pick").disabled = $("pick-dir").disabled = $("src-mkdir").disabled = state.busy;
        renderPath();
        renderFolder();
        renderFiles();
        renderTools();
    }

    /* ⌘/Ctrl+A picks all, Escape none, Delete or Backspace deletes (Cycles, after asking) or removes (list),
       Enter opens the one folder picked (Cycles) or renames the one row picked (list). Keys typed into a field are
       its own. */
    function listKeys(onDelete, all, none, enter) {
        return function (ev) {
            if (ev.target && ev.target.tagName === "INPUT")
                return;
            if ((ev.metaKey || ev.ctrlKey) && (ev.key === "a" || ev.key === "A")) {
                ev.preventDefault();
                all();
            } else if (ev.key === "Escape")
                none();
            else if (ev.key === "Delete" || ev.key === "Backspace") {
                ev.preventDefault();
                onDelete();
            } else if (ev.key === "Enter") {
                ev.preventDefault();
                enter();
            } else
                return;
            renderTools();
        };
    }

    $("chip").onclick = function () {
        if (!state.access)
            return guarded(connect)();
        state.showPorts = !state.showPorts;
        render();
    };
    $("in").onchange = $("out").onchange = $("retry").onclick = guarded(usePorts);
    $("mkdir").onclick = function () {
        state.naming = true;
        render();
        if ($("dirname").focus)
            $("dirname").focus();
    };
    $("mkdir-cancel").onclick = function () {
        state.naming = false;
        $("dirname").value = "";
        render();
    };
    $("newdir").onsubmit = function (ev) {
        if (ev)
            ev.preventDefault();
        return guarded(makeFolder)();
    };
    $("refresh").onclick = guarded(function () { return listDir(state.path); });
    $("del-sel").onclick = guarded(deleteSelected);
    /* Select on: boxes, a click picks; off again: nothing stays selected */
    $("select-mode").onclick = function () {
        state.selecting = !state.selecting;
        if (!state.selecting)
            state.sel = [];
        state.anchor = -1;
        renderFolder();
        renderTools();
    };
    $("remove-sel").onclick = removeFiles;
    $("src-mkdir").onclick = newListFolder;
    $("pick").onclick = function () { $("chooser").click(); };
    $("pick-dir").onclick = function () { $("chooser-dir").click(); };
    $("chooser").onchange = function () { addFiles($("chooser").files, target()); $("chooser").value = ""; };
    $("chooser-dir").onchange = function () { addFiles($("chooser-dir").files, target()); $("chooser-dir").value = ""; };
    $("upload").onclick = guarded(function () { return uploadNodes(state.tree.kids, state.path); });
    $("folder").onkeydown = listKeys(
        function () {
            if (state.connected && !state.busy)
                guarded(deleteSelected)();
        },
        function () {
            state.sel = state.items.filter(function (it) { return !kept(it); }).map(function (it) { return it.name; });
            renderFolder();
        },
        function () {
            state.sel = [];
            renderFolder();
        },
        function () {
            var one = state.items.filter(function (it) { return state.sel.indexOf(it.name) >= 0; });

            if (one.length === 1 && one[0].folder)
                openFolder(one[0]);
        });
    $("files").onkeydown = listKeys(
        function () {
            if (!state.busy)
                removeFiles();
        },
        function () {
            state.fsel = visible().map(function (r) { return r.n; });
            renderFiles();
        },
        function () {
            state.fsel = [];
            renderFiles();
        },
        function () {
            if (state.fsel.length === 1)
                startRename(state.fsel[0]);
        });
    /* the list's side takes what is dropped into the list itself; the Cycles' side uploads into the folder shown */
    wire($("src"), onList(state.tree, null));
    wire($("dst"), onCycles(function () { return state.path; }, $("folder")));
    /* files dropped anywhere else on the page join the list; its side shows it while they are over the page */
    document.addEventListener("dragover", function (e) {
        e.preventDefault();
        if (fromComputer(e.dataTransfer))
            $("src").className = "pane src drag";
    });
    document.addEventListener("dragleave", function (e) {
        if (!e.relatedTarget)
            $("src").className = "pane src";
    });
    document.addEventListener("drop", function (e) {
        e.preventDefault();
        $("src").className = "pane src";
        if (!state.busy && fromComputer(e.dataTransfer))
            addDropped(dropped(e.dataTransfer), state.tree);
    });
    window.addEventListener("beforeunload", function (ev) {
        if (state.busy) {
            ev.preventDefault();
            ev.returnValue = "";
        }
    });
    $("alert-ok").onclick = closeAlert;
    $("alert").onclose = alertClosed;               /* OK, or Escape on the dialog */
    if (NO_MIDI) {
        $("nomidi").textContent = NO_MIDI_TEXT[NO_MIDI];
        $("nomidi").hidden = false;
    }
    render();
})();
