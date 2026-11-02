/* model27's manager (notes/77): one project per firmware on the Model:Cycles. Web MIDI to the
   Cycles; the library in IndexedDB (store.js); backups on request 0x6F, checked whole (backup.js);
   flashing over USB with the flasher's core (../flasher/flasher.js, window.MCFlasher); restores
   checked by the settings the Cycles answers afterwards (notes/77 §3).
   The page: the Cycles' card, the firmwares as tiles; over the page the switch, a firmware's
   history and the first start. */
(function () {
    "use strict";
    var S = window.Sysex, B = window.Backup, F = window.MCFlasher, L = window.Library;
    /* SHA-256 of a .syx -> its name, for the firmwares anyone can download (none is hosted here) */
    var KNOWN = {
        "44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c": "Model:Cycles OS 1.13 (official)"
    };
    var ANSWER_MS = 5000;           /* a backup's first message comes within this */
    var SILENCE_MS = 3000;          /* an unfinished backup ends this long after its last message */
    var SETTLE_MS = 60000;          /* a restore's settings come within this */
    var RESTORE_BPS = 200000;       /* a restore goes in at about this many bytes a second (2.4 MB in 11 to 13 s, notes/77 §3) */
    var GONE_MS = 180000;           /* after a flash, the Cycles goes to write within this (the user presses YES) */
    var BACK_MS = 180000;           /* and comes back within this */
    var BOOT_MS = 2500;             /* time to start before it is asked who it is (as model27's flasher) */
    var TRANSFER_MS = 10000;        /* the warning about another program stays this long after its last message */
    /* Why this browser cannot talk to the Cycles, as the flasher tells it (noMidi): the page has no other way, so it
       says so at once and keeps only the library (add, export, import) */
    var NO_MIDI = typeof window.isSecureContext !== "undefined" && !window.isSecureContext ? "insecure" :
                  !navigator.requestMIDIAccess ? "none" : null;
    var NO_MIDI_TEXT = {
        none: "This browser has no Web MIDI, so the Manager can't talk to your Cycles: backing up, flashing and switching " +
              "all go over USB from this page. Open it in Chrome, Edge or Opera on a computer.",
        insecure: "Web MIDI needs a secure page, so this one can't talk to your Cycles. Open the online version, or serve " +
                  "the docs folder with python3 -m http.server."
    };
    var CHECK = "M7 1h1v1h-1zM6 2h2v1h-2zM0 3h1v1h-1zM5 3h2v1h-2zM0 4h2v1h-2zM4 4h2v1h-2zM1 5h4v1h-4zM2 6h2v1h-2z";

    var lib = new L.Store(L.indexedDB());
    var state = {
        access: null, input: null, output: null, feed: null,
        identity: null, asked: false,   /* who answered, and whether the page asked */
        seq: 1, rpc: null,              /* the Transfer-protocol request waiting for its answer */
        capture: null,                  /* a backup coming in */
        onCapture: null,                /* who shows a backup's progress */
        settings: null,                 /* a restore waiting for the settings */
        portWait: null,                 /* a flash waiting for the Cycles to go, or to come back */
        builds: [], backups: {}, device: { build: null, sure: false },
        busy: false, flow: null, transferTimer: null, persisted: false, log: [],
        view: null, viewBuild: null,    /* over the page: "switch", "history" (of viewBuild) or "setup" */
        menu: null, renaming: null, renamingBackup: null, chooseHere: false, showPorts: false,
        setup: null
    };

    function $(id) { return document.getElementById(id); }

    /* The one status line, under the header; every message also goes to the protocol. Good news
       goes again after a while, problems stay until the next message. */
    function show(text, kind) {
        $("status").textContent = text;
        $("status").className = "status" + (kind === "bad" || kind === "warn" ? " " + kind : "");
        $("status").hidden = false;
        clearTimeout(state.statusTimer);
        if (kind === "ok")
            state.statusTimer = setTimeout(function () { $("status").hidden = true; }, 10000);
        log(text);
    }

    /* The status line only, for progress that would flood the protocol. */
    function progress(text) {
        clearTimeout(state.statusTimer);
        $("status").textContent = text;
        $("status").className = "status";
        $("status").hidden = false;
    }

    /* The protocol: what happened, with the time, to copy and paste in one piece. */
    function log(text) {
        var line = new Date().toLocaleTimeString() + "  " + text;

        state.log.push(line);
        $("log").textContent += ($("log").textContent ? "\n" : "") + line;
        $("log").scrollTop = $("log").scrollHeight;
        if ($("flow-log")) {
            $("flow-log").textContent = $("log").textContent;
            $("flow-log").scrollTop = $("flow-log").scrollHeight;
        }
    }
    function kb(n) { return n >= 1048576 ? (n / 1048576).toFixed(1) + " MB" : n >= 1024 ? (n / 1024).toFixed(1) + " KB" : n + " B"; }
    function when(iso) { return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }); }
    function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
    function build(id) { return state.builds.filter(function (b) { return b.key === id; })[0] || null; }
    function nameOf(id) { var b = build(id); return b ? "“" + b.name + "”" : "an unknown firmware"; }
    function label(x) { return x.name || when(x.made); }
    function sentence(s) { return s.charAt(0).toUpperCase() + s.slice(1) + "."; }
    function ready() { return !!(state.input && state.output && state.identity && state.identity.id === 27); }
    function two(n) { return String(n).padStart(2, "0"); }
    function currentOf(b) { return b ? (state.backups[b.key] || []).filter(function (x) { return x.key === b.current; })[0] || null : null; }
    /* A firmware's project as the user knows it: by its name on the Cycles. */
    function projectOf(id) { var b = build(id); return b && b.slotName ? b.slotName : "its project"; }

    /* "today 15:12", "yesterday 9:03", or the date. */
    function ago(iso) {
        var d = new Date(iso), now = new Date(), y = new Date(now), t = d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });

        y.setDate(now.getDate() - 1);
        if (d.toDateString() === now.toDateString())
            return "today " + t;
        if (d.toDateString() === y.toDateString())
            return "yesterday " + t;
        return when(iso);
    }

    function el(tag, props, kids) {
        var e = document.createElement(tag);

        Object.keys(props || {}).forEach(function (k) {
            if (k === "text")
                e.textContent = props[k];
            else if (k === "class")
                e.className = props[k];
            else if (k.indexOf("-") >= 0)
                e.setAttribute(k, props[k]);
            else
                e[k] = props[k];
        });
        (kids || []).forEach(function (c) { if (c) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
        return e;
    }

    /* kind: "", "ghost", "inv"; size: "", "sm", "big" */
    function button(text, onclick, opts) {
        opts = opts || {};
        return el("button", { type: "button", text: text, onclick: onclick, disabled: !!opts.disabled, title: opts.title || "",
                              className: opts.cls || ("btn" + (opts.kind ? " " + opts.kind : "") + (opts.size ? " " + opts.size : "")) });
    }

    function mark(svgPath) {
        var ns = "http://www.w3.org/2000/svg", s = document.createElementNS(ns, "svg"), p = document.createElementNS(ns, "path");

        s.setAttribute("viewBox", "0 0 8 8");
        s.setAttribute("width", "16");
        s.setAttribute("height", "16");
        s.setAttribute("shape-rendering", "crispEdges");
        s.setAttribute("aria-hidden", "true");
        p.setAttribute("d", svgPath);
        p.setAttribute("fill", "currentColor");
        s.appendChild(p);
        return s;
    }

    function dots() {
        var ns = "http://www.w3.org/2000/svg", s = document.createElementNS(ns, "svg");

        s.setAttribute("viewBox", "0 0 16 4");
        s.setAttribute("width", "18");
        s.setAttribute("height", "5");
        s.setAttribute("shape-rendering", "crispEdges");
        s.setAttribute("aria-hidden", "true");
        [0, 6, 12].forEach(function (x) {
            var r = document.createElementNS(ns, "rect");

            r.setAttribute("x", x); r.setAttribute("y", 0); r.setAttribute("width", 4); r.setAttribute("height", 4);
            r.setAttribute("fill", "currentColor");
            s.appendChild(r);
        });
        return s;
    }

    function save(bytes, name) {
        var url = URL.createObjectURL(new Blob([bytes], { type: "application/octet-stream" })), a = el("a", { href: url, download: name });

        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    }

    function fileName(base) {
        return S.fileName(base, new Date()).replace(/\.syx$/, "");
    }

    /* ---- MIDI ---------------------------------------------------------------------------- */

    function likely(p) { return /cycles|elektron/i.test(p.name + " " + (p.manufacturer || "")); }
    function present(p) { return p && p.state !== "disconnected"; }

    function fillPorts() {
        [["in", state.access.inputs], ["out", state.access.outputs]].forEach(function (pair) {
            var sel = $(pair[0]), keep = sel.value, ports = Array.from(pair[1].values()).filter(present), pick = keep;

            sel.innerHTML = "";
            ports.forEach(function (p) { sel.appendChild(el("option", { value: p.id, text: p.name })); });
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
        state.access.onstatechange = onPortChange;
        fillPorts();
        await usePorts();
    }

    /* The ports picked, listened to afresh (a Cycles back from a restart may come back as the same
       port object); asks the Cycles who it is unless a switch is running, which asks itself. */
    async function usePorts() {
        var input = state.access.inputs.get($("in").value) || null, output = state.access.outputs.get($("out").value) || null;

        if (!present(input))
            input = null;
        if (!present(output))
            output = null;
        if (state.input && state.input !== input)
            state.input.onmidimessage = null;
        state.input = input;
        state.feed = S.assembler(onSysex);
        if (input) {
            input.onmidimessage = function (ev) { state.feed(ev.data, ev.timeStamp); };
            if (input.open)
                input.open().catch(function () {});
        }
        state.output = output;
        state.identity = null;
        state.asked = false;
        render();
        if (input && output && !state.flow)
            await identify();
    }

    function onPortChange(e) {
        var p = e && e.port, w = state.portWait;

        if (p && p.state === "disconnected" && ((state.input && p.id === state.input.id) || (state.output && p.id === state.output.id)))
            lost();
        if (w && p && ((w.kind === "gone" && p.state === "disconnected" && w.ids.indexOf(p.id) >= 0) ||
                       (w.kind === "back" && p.state === "connected" && likely(p)))) {
            state.portWait = null;
            clearTimeout(w.timer);
            w.resolve();
        }
        fillPorts();
        if (state.portWait || state.flow)
            return;
        if (state.access.inputs.get($("in").value) !== state.input || state.access.outputs.get($("out").value) !== state.output ||
            (state.input && !present(state.input)))
            usePorts();
    }

    /* The Cycles went away: a backup coming in, a restore waiting for its settings and a request
       waiting for its answer give up at once instead of at their timeouts. */
    function lost() {
        var c = state.capture, w = state.settings, r = state.rpc, why = "the Cycles went away (USB)";

        if (c) {
            state.capture = null;
            clearTimeout(c.timer);
            c.reject(new Error(why));
        }
        if (w) {
            state.settings = null;
            clearTimeout(w.timer);
            w.resolve("gone");
        }
        if (r) {
            state.rpc = null;
            clearTimeout(r.timer);
            r.reject(new F.XferError("gone", why));
        }
    }

    function waitPort(kind, ms) {
        return new Promise(function (resolve, reject) {
            state.portWait = { kind: kind, resolve: resolve, reject: reject,
                               ids: [state.input && state.input.id, state.output && state.output.id],
                               timer: setTimeout(function () { state.portWait = null; reject(new Error("timeout")); }, ms) };
        });
    }

    /* Stops waiting for the Cycles with the reason given (an Error or a Stop). */
    function giveUpWait(reason) {
        var w = state.portWait;

        if (!w)
            return;
        state.portWait = null;
        clearTimeout(w.timer);
        w.reject(reason);
    }

    /* Every whole SysEx from the Cycles: answers to the page's own requests, a backup coming in,
       the settings after a restore. Transfer-protocol traffic the page did not ask for comes from
       another program. */
    function onSysex(msg) {
        var r = state.rpc, m = F.xferParse(msg), t;

        if (m) {
            if (r && m.length > 4 && ((m[2] << 8) | m[3]) === r.seq && m[4] === r.type) {
                state.rpc = null;
                clearTimeout(r.timer);
                r.resolve(m);
            } else
                otherProgram();
            return;
        }
        t = S.dumpType(msg);
        if (state.settings && t === B.SETTINGS) {
            var w = state.settings;

            state.settings = null;
            clearTimeout(w.timer);
            w.resolve(msg);
        } else if (state.capture && (t === B.PATTERN || t === B.SETTINGS))
            captured(msg);
    }

    function otherProgram() {
        if ($("transfer").hidden)
            log("Something else talks to the Cycles: Transfer-protocol messages the page did not ask for (Elektron Transfer, " +
                "or this page in another tab or window).");
        $("transfer").hidden = false;
        clearTimeout(state.transferTimer);
        state.transferTimer = setTimeout(function () { $("transfer").hidden = true; }, TRANSFER_MS);
    }

    /* One Transfer-protocol request (as model27's flasher sends it); resolves with the answer's payload. */
    function rpc(body, timeout) {
        return new Promise(function (resolve, reject) {
            var r = { seq: state.seq, type: body[0] | 0x80, resolve: resolve, reject: reject }, payload;

            if (state.rpc)
                return reject(new Error("still waiting for the Cycles' last answer"));
            if (!state.output)
                return reject(new Error("no MIDI output"));
            state.seq = (state.seq + 1) & 0xffff;
            payload = new Uint8Array(4 + body.length);
            payload[0] = r.seq >> 8;
            payload[1] = r.seq & 255;
            payload.set(body, 4);
            r.timer = setTimeout(function () {
                if (state.rpc === r)
                    state.rpc = null;
                reject(new F.XferError("timeout"));
            }, timeout || 8000);
            state.rpc = r;
            try {
                state.output.send(F.xferFrame(payload));
            } catch (e) {
                clearTimeout(r.timer);
                state.rpc = null;
                reject(new F.XferError("gone", e.message));
            }
        });
    }

    var session = { request: function (body, timeout) { return rpc(body, timeout); } };

    async function identify() {
        var id;

        state.asked = true;
        try {
            id = state.identity = await F.xferIdentify(session);
            log("Identify: device id " + id.id + ", “" + id.name + "”, version “" + id.version + "”.");
            if (id.id !== 27 && !state.flow)
                show("This answers as " + (id.device || "device " + id.id) + ": the page works with a Model:Cycles on its own OS.", "bad");
        } catch (e) {
            state.identity = null;
            if (!state.flow)
                show("The Cycles does not answer (" + e.message + "). Quit Elektron Transfer if it is open, then press Ask again.", "bad");
        }
        render();
        return state.identity;
    }

    /* ---- backups and restores ------------------------------------------------------------ */

    /* The project the Cycles plays now, asked for with request 0x6F: its messages. */
    function requestBackup() {
        return new Promise(function (resolve, reject) {
            var c = { msgs: [], resolve: resolve, reject: reject };

            c.timer = setTimeout(function () {
                state.capture = null;
                reject(new Error("the Cycles did not answer within " + ANSWER_MS / 1000 + " s"));
            }, ANSWER_MS);
            state.capture = c;
            state.output.send(S.request(0x6f, 0));
        });
    }

    function captured(msg) {
        var c = state.capture;

        c.msgs.push(msg);
        clearTimeout(c.timer);
        if (state.onCapture)
            state.onCapture(c.msgs.length);
        if (c.msgs.length === B.PATTERNS + 1 && S.dumpType(msg) === B.SETTINGS)
            return endCapture();
        c.timer = setTimeout(endCapture, SILENCE_MS);
    }

    function endCapture() {
        var c = state.capture;

        state.capture = null;
        clearTimeout(c.timer);
        c.resolve(c.msgs);
    }

    /* A backup of the project on the Cycles, as the current project of the firmware it runs. */
    async function backupNow(buildId) {
        var t0 = performance.now(), msgs = await requestBackup(), problems = B.problems(msgs), r;

        log("Backup: " + msgs.length + " messages, " + kb(S.size(msgs)) + " in " + ((performance.now() - t0) / 1000).toFixed(1) +
            " s, " + (problems.length ? "not whole: " + problems.join("; ") : "whole") + ".");
        if (problems.length)
            throw new Error("the backup is not whole: " + problems.join("; "));
        r = await lib.addBackup(buildId, S.join(msgs), msgs.length);
        log("Kept for " + nameOf(buildId) + (r.added ? " as a new backup." : ": the same as the backup of " + when(r.was) + "."));
        await refresh();
        return r;
    }

    /* Sends a backup and waits for the settings the Cycles then answers with: they come once it is
       through and must be those sent. The page hands the messages over in under a second and the
       Cycles says nothing until it is through, so the progress follows the time a restore takes
       (RESTORE_BPS), at most 99 % until the answer: onStep(pct, sent), sent once all is handed over.
       Resolves with the seconds it took. */
    async function restore(bytes, onStep) {
        var msgs = S.split(bytes), problems = B.problems(msgs), t0 = performance.now(), est = 1000 * bytes.length / RESTORE_BPS,
            got, i, tick;

        function pct() { return Math.min(99, Math.round(100 * (performance.now() - t0) / est)); }

        if (problems.length)
            throw new Error("the backup is not whole: " + problems.join("; "));
        for (i = 0; i < msgs.length; i++) {
            state.output.send(msgs[i]);
            if (onStep && i % 8 === 0)
                onStep(pct(), false);
            await sleep(0);
        }
        log("Restore: " + msgs.length + " messages, " + kb(bytes.length) + " handed over in " +
            ((performance.now() - t0) / 1000).toFixed(1) + " s; asking for the settings.");
        if (onStep) {
            onStep(pct(), true);
            tick = setInterval(function () { onStep(pct(), true); }, 250);
        }
        try {
            got = await new Promise(function (resolve) {
                state.settings = { resolve: resolve, timer: setTimeout(function () { state.settings = null; resolve(null); }, SETTLE_MS) };
                state.output.send(S.request(0x64, 0));
            });
        } finally {
            clearInterval(tick);
        }
        if (got === "gone")
            throw new Error("the Cycles went away during the restore; connect it again and send the project once more");
        if (!got)
            throw new Error("the Cycles did not say within " + SETTLE_MS / 1000 + " s that it is through; check what it plays");
        log("Restore: the settings came after " + ((performance.now() - t0) / 1000).toFixed(1) + " s, " +
            (S.compare([B.settings(msgs)], [got]).identical ? "the same as those sent." : "different from those sent."));
        if (!S.compare([B.settings(msgs)], [got]).identical)
            throw new Error("the Cycles answered with other settings than those sent; check what it plays");
        return Math.round((performance.now() - t0) / 1000);
    }

    /* What to do on the Cycles so that its project list marks the project it plays: a restore sets
       what the Cycles plays, not its slot, so the list still marks the project loaded before, and the
       Cycles' quick save would write into that one. */
    function slotAdvice(b) {
        return b && b.slot ? "To keep the Cycles' project list right, save it there into slot " + two(b.slot) + " as " +
                             (b.slotName || "its name") + " (select Save, answer “Overwrite?” with Yes)." :
                             "To keep the Cycles' project list right, save it from the project list into a slot of its own; " +
                             "the quick save would write into the slot of the project loaded before.";
    }

    async function backupButton() {
        var d = state.device.build, r;

        state.busy = true;
        state.onCapture = function (n) { progress("Receiving the project: " + n + " of " + (B.PATTERNS + 1) + " messages…"); };
        render();
        show("Asking the Cycles for its project…");
        try {
            r = await backupNow(d);
            show(r.added ? "Backed up: the current project of " + nameOf(d) + "." :
                           "Backed up: the same project as the backup of " + ago(r.was) + ".", "ok");
        } catch (e) {
            show("No backup: " + e.message + ".", "bad");
        }
        state.onCapture = null;
        state.busy = false;
        render();
    }

    async function sendBackup(x) {
        var d = state.device.build, bytes, secs;

        if (!window.confirm("Send “" + label(x) + "” to the Cycles?\n\nIt replaces the project the Cycles plays now. " +
                            (d ? "The page backs that one up first. " : "The page cannot back it up first: it does not know which firmware is on the Cycles. ") +
                            (d && d !== x.build ? "\n\nThis backup was made on " + nameOf(x.build) + ", the Cycles runs " + nameOf(d) +
                                                  ": tracks may play other machines. " : "") +
                            "\n\nStop the Cycles' sequencer first."))
            return;
        closeView();
        state.busy = true;
        render();
        try {
            if (d) {
                show("Backing up the project on the Cycles first…");
                await backupNow(d);
            }
            bytes = await lib.backupData(x.key);
            secs = await restore(bytes, function (pct, sent) {
                progress((sent ? "Sent. The Cycles takes it in (about 12 s): " : "Sending the project: ") + pct + " %");
            });
            if (d === x.build)
                await lib.setCurrent(x.build, x.key);
            await refresh();
            show("“" + label(x) + "” is on the Cycles, checked, after " + secs + " s. " + slotAdvice(d === x.build ? build(d) : null), "ok");
        } catch (e) {
            show("Not done: " + e.message + ".", "bad");
        }
        state.busy = false;
        render();
    }

    /* ---- firmwares ----------------------------------------------------------------------- */

    async function addFiles(files) {
        var i, f, bytes, v, hash, r, said = [];

        for (i = 0; i < files.length; i++) {
            f = files[i];
            bytes = new Uint8Array(await f.arrayBuffer());
            try {
                v = F.verify(bytes);
            } catch (e) {
                said.push(f.name + ": " + e.message);
                continue;
            }
            if (v.product !== 0x11) {
                said.push(f.name + " is for a " + v.name + "; the page works with the Model:Cycles only");
                continue;
            }
            hash = await S.sha256(bytes);
            r = await lib.addBuild(bytes, KNOWN[hash] || f.name.replace(/\.syx$/i, ""));
            said.push(r.added ? "added " + r.build.name : f.name + " is already here as “" + r.build.name + "”");
        }
        await keep();
        await refresh();
        if (said.length)
            show(said.map(sentence).join(" "), said.some(function (s) { return /^added/.test(s); }) ? "ok" : "warn");
    }

    async function removeBuild(b) {
        var n = (state.backups[b.key] || []).length;

        if (!window.confirm("Remove the firmware “" + b.name + "”" + (n ? " and its " + n + " backup" + (n > 1 ? "s" : "") : "") +
                            " from this browser? Export first to keep them."))
            return;
        closeView();
        await lib.removeBuild(b.key);
        await refresh();
        show("Removed “" + b.name + "”.", "ok");
    }

    async function removeBackup(x) {
        if (!window.confirm("Delete the backup of " + when(x.made) + " from this browser?"))
            return;
        await lib.removeBackup(x.key);
        await refresh();
    }

    /* Ask the browser to keep the library when it runs short of space. */
    async function keep() {
        if (!state.persisted && navigator.storage && navigator.storage.persist)
            state.persisted = await navigator.storage.persist();
    }

    /* ---- switching ----------------------------------------------------------------------- */

    /* A step's state on the left; the protocol keeps it. */
    function step(i, how, note) {
        var s = state.flow.steps[i];

        s.how = how;
        log("Step " + (i + 1) + " (" + s.text + "), " + how + (note ? ": " + note : "."));
        renderFlow();
    }

    /* What the right side shows: { title, huge, text, items, progress, result }. */
    function setPanel(p) {
        state.flow.panel = p;
        renderFlow();
    }

    /* Buttons (and fields) under the panel; resolves with the value of the button pressed. */
    function ask(actions) {
        return new Promise(function (resolve) {
            state.flow.actions = actions;
            state.flow.answer = function (v) { state.flow.actions = []; state.flow.answer = null; renderFlow(); resolve(v); };
            renderFlow();
        });
    }

    function Stop(title, text) { this.title = title; this.message = text; }

    /* The switch's last step: the user saves the project in the firmware's slot on the Cycles and
       says which slot that is, the first time, so that the page can tell next time. */
    async function saveInSlot(target, has) {
        var b = build(target), flow = state.flow, v, slot = b && b.slot ? String(b.slot) : "", name = b ? b.slotName : "", first = [], warn = "";

        if (!has)
            first.push("Make this firmware's project on the Cycles, or keep the one it plays.");
        step(4, "doing");
        for (;;) {
            if (b && b.slot)
                setPanel({ title: "Save it in slot " + two(b.slot), text: warn, items: first.concat([
                    "Open the project list on the Cycles.",
                    "Choose slot " + two(b.slot) + ", select Save and answer “Overwrite?” with Yes.",
                    "Type the name " + (b.slotName || "you gave it") + ". The Cycles suggests the name of the project loaded before: change it."]) });
            else
                setPanel({ title: "Save it in a slot of its own", text: warn, items: first.concat([
                    "Open the project list on the Cycles.",
                    "Choose a slot for this firmware, select Save and answer “Overwrite?” with Yes.",
                    "Give it a name of its own. The Cycles suggests the name of the project loaded before: change it.",
                    "Enter the slot and the name here: next time the page tells you."]) });
            v = await ask((b && b.slot ? [] : [{ input: "slot", caption: "Slot on the Cycles", value: slot, size: 4 },
                                                { input: "slotName", caption: "Name there", value: name, size: 12 }])
                          .concat([{ label: "Saved there", value: "saved", kind: "", size: "big" },
                                   { label: "Skip", value: "skip", kind: "ghost", size: "big" }]));
            if (v !== "saved")
                break;
            if (b && b.slot) {
                step(4, "done", "saved in slot " + two(b.slot));
                return true;
            }
            slot = ((flow.inputs && flow.inputs.slot) || "").trim();
            name = ((flow.inputs && flow.inputs.slotName) || "").trim();
            if (!/^[1-9][0-9]*$/.test(slot.replace(/^0+(?=\d)/, ""))) {
                warn = "Enter the number of the slot you saved it in, and its name, or press Skip.";
                continue;
            }
            b = await lib.updateBuild(target, { slot: slot, slotName: name });
            await refresh();
            step(4, "done", "saved in slot " + two(b.slot) + (b.slotName ? " as " + b.slotName : ""));
            return true;
        }
        step(4, "done", "skipped");
        return false;
    }

    async function switchTo(target) {
        var from = state.device.build, toB = build(target), flow, data, v, id, res, cur, secs, r, i, choice, quarter, t0, saved;

        state.menu = null;
        flow = state.flow = {
            title: "Switching to " + toB.name, from: "from " + (build(from) ? build(from).name : "?"), cancel: false, actions: [],
            panel: {}, steps: [
                { text: "Stop the sequencer", how: "doing" },
                { text: "Back up " + projectOf(from), how: "todo" },
                { text: "Flash " + toB.name, how: "todo" },
                { text: "Bring back " + projectOf(target), how: "todo" },
                { text: toB.slot ? "Save it in slot " + two(toB.slot) : "Save it in its slot", how: "todo" }
            ] };
        state.busy = true;
        state.view = "switch";
        log("Switching from " + nameOf(from) + " to " + nameOf(target) + ".");
        render();
        try {
            setPanel({ title: "Stop the sequencer on the Cycles", text: "While a project comes in, the Cycles stutters if it plays." });
            if (await ask([{ label: "It's stopped", value: "go", size: "big" }, { label: "Cancel", value: "cancel", kind: "ghost", size: "big" }]) === "cancel")
                throw new Stop("Not switched", "Nothing has changed.");
            step(0, "done");

            for (;;) {
                step(1, "doing");
                setPanel({ title: "Backing up " + projectOf(from), text: "The page asks the Cycles for the project it plays now.", progress: 0 });
                state.onCapture = function (n) {
                    setPanel({ title: "Backing up " + projectOf(from), text: "The page asks the Cycles for the project it plays now.",
                               progress: Math.round(100 * n / (B.PATTERNS + 1)) });
                };
                try {
                    r = await backupNow(from);
                    step(1, "done", r.added ? "kept as its current project" : "the same as the backup of " + when(r.was));
                    break;
                } catch (e) {
                    step(1, "failed", e.message);
                    setPanel({ title: "No backup", text: sentence(e.message) + " Without a backup, the project on the Cycles is lost " +
                                                     "once the other firmware's project comes back." });
                    choice = await ask([{ label: "Try again", value: "again", size: "big" },
                                        { label: "Go on without", value: "skip", kind: "ghost", size: "big" },
                                        { label: "Cancel", value: "cancel", kind: "ghost", size: "big" }]);
                    if (choice === "cancel")
                        throw new Stop("Not switched", "Nothing has changed.");
                    if (choice === "skip") {
                        step(1, "done", "left out");
                        break;
                    }
                } finally {
                    state.onCapture = null;
                }
            }

            step(2, "doing");
            setPanel({ title: "Checking " + toB.name, text: "The file, and that a Model:Cycles answers." });
            data = await lib.buildData(target);
            v = F.verify(data);
            if (v.product !== 0x11)
                throw new Error("this file is for a " + v.name);
            id = await F.xferIdentify(session);
            if (id.id !== 27)
                throw new Error("the device answers as " + (id.device || "device " + id.id) + ", not as a Model:Cycles on its own OS");
            log("Flash: " + kb(data.length) + ", " + v.count + " packets, checked; the Cycles answers as device " + id.id +
                ", version “" + id.version + "”.");
            var sendText = "About " + Math.round(F.fastSeconds(data) / 5) * 5 + " seconds. The Cycles checks every block as it comes in.";

            setPanel({ title: "Sending " + toB.name, text: sendText, progress: 0 });
            flow.actions = [{ label: "Stop sending", value: "stop", kind: "ghost", size: "sm" }];
            flow.answer = function () { flow.cancel = true; flow.actions = []; renderFlow(); };
            quarter = 0;
            res = await F.upgradeFast(session, data, {
                isCancelled: function () { return flow.cancel; },
                onProgress: function (done, total) {
                    var pct = Math.floor(100 * done / total);

                    setPanel({ title: "Sending " + toB.name, text: sendText, progress: pct });
                    if (Math.floor(pct / 25) > quarter) {
                        quarter = Math.floor(pct / 25);
                        log("Flash: " + pct + " % sent.");
                    }
                }
            });
            flow.actions = [];
            flow.answer = null;
            log("Flash: " + (res.cancelled ? "stopped" : "sent") + " after " + res.blocks + " blocks, " + kb(res.sent) + " in " +
                res.seconds.toFixed(1) + " s.");
            if (res.cancelled)
                throw new Stop("Stopped", "The Cycles keeps " + nameOf(from) + ". If it still shows its upgrade screen, turn it " +
                                          "off and on: it starts with its firmware and its project.");
            setPanel({ title: "Press YES on the Cycles", huge: true,
                       text: "It then writes the firmware and restarts by itself. Don't turn it off." });
            t0 = performance.now();
            flow.actions = [{ label: "I answered NO", value: "no", kind: "ghost", size: "sm" }];
            flow.answer = function () {
                giveUpWait(new Stop("Not switched", "You answered NO: the Cycles keeps " + nameOf(from) + " and its project."));
            };
            renderFlow();
            try {
                await waitPort("gone", GONE_MS);
            } catch (e) {
                if (e instanceof Stop)
                    throw e;
                throw new Error("the Cycles did not restart within " + GONE_MS / 60000 + " minutes. If it still asks, confirm " +
                                "with YES, then say which firmware is on it");
            } finally {
                flow.actions = [];
                flow.answer = null;
            }
            log("Flash: the Cycles went away " + ((performance.now() - t0) / 1000).toFixed(1) + " s after the last block.");
            setPanel({ title: "Restarting…", text: "The Cycles comes back with " + toB.name + ". Don't turn it off." });
            try {
                await waitPort("back", BACK_MS);
            } catch (e) {
                throw new Error("the Cycles did not come back within " + BACK_MS / 60000 + " minutes. Once it is back, connect " +
                                "it and say which firmware is on it");
            }
            log("Flash: the Cycles came back " + ((performance.now() - t0) / 1000).toFixed(1) + " s after the last block.");
            await sleep(BOOT_MS);
            fillPorts();
            await usePorts();
            for (i = 0; i < 4 && !(await identify()); i++)
                await sleep(1000);
            await lib.setDevice(target, true);
            await refresh();
            step(2, "done", "back, OS " + (state.identity ? state.identity.version : "?"));

            step(3, "doing");
            cur = await lib.current(target);
            if (!cur)
                step(3, "done", "this firmware has no project yet");
            else {
                setPanel({ title: "Bringing back " + projectOf(target), text: "The page sends this firmware's project and checks that it arrived.",
                           progress: 0 });
                secs = await restore(await lib.backupData(cur.key), function (pct, sent) {
                    setPanel({ title: "Bringing back " + projectOf(target),
                               text: sent ? "Sent. The Cycles takes it in, about 12 seconds…" : "The page sends this firmware's project and checks that it arrived.",
                               progress: pct });
                });
                step(3, "done", "in and checked after " + secs + " s");
            }
            saved = await saveInSlot(target, !!cur);
            toB = build(target);
            flow.title = "Switched to " + toB.name;
            setPanel({ title: "Done", result: { label: "On your Cycles now", big: toB.name,
                       meta: [toB.slotName ? "Project " + toB.slotName : (cur ? "Its project" : "No project yet"),
                              toB.slot ? "Slot " + two(toB.slot) + (saved ? "" : " (not saved there)") : "No slot given",
                              cur ? "checked" : ""].filter(Boolean).join(" · ") } });
            show("Switched to " + nameOf(target) + ".", "ok");
        } catch (e) {
            var at = flow.steps.filter(function (s) { return s.how === "doing"; })[0];

            if (e instanceof Stop) {
                if (at)
                    at.how = "todo";
                flow.title = e.title;
                setPanel({ title: e.title, text: e.message });
                show(e.title + ": " + e.message, "warn");
            } else {
                if (at)
                    at.how = "failed";
                flow.title = "The switch stopped";
                setPanel({ title: "The switch stopped", text: sentence(e.message) });
                show("The switch stopped: " + e.message + ".", "bad");
            }
        }
        state.busy = false;
        render();
        await ask([{ label: "Back to the overview", value: "close", size: "big" }]);
        state.flow = null;
        closeView();
    }

    /* ---- the first start ----------------------------------------------------------------- */

    function openSetup() {
        state.menu = null;
        state.setup = { n: 1, pick: state.device.build || (state.builds[0] && state.builds[0].key) || null,
                        slot: "", name: "", pct: -1, result: null, error: "" };
        var b = build(state.setup.pick);

        if (b) {
            state.setup.slot = b.slot ? two(b.slot) : "";
            state.setup.name = b.slotName || "";
        }
        state.view = "setup";
        render();
    }

    async function setupBackup() {
        var st = state.setup, r;

        st.pct = 0;
        st.error = "";
        state.busy = true;
        state.onCapture = function (n) { st.pct = Math.round(100 * n / (B.PATTERNS + 1)); renderSetupBar(); };
        render();
        try {
            r = await backupNow(st.pick);
            st.result = r;
        } catch (e) {
            st.error = sentence(e.message);
            st.pct = -1;
        }
        state.onCapture = null;
        state.busy = false;
        render();
    }

    async function setupNext() {
        var st = state.setup;

        if (st.n === 3 && st.pick) {
            await lib.setDevice(st.pick, true);
            if (st.slot.trim())
                await lib.updateBuild(st.pick, { slot: st.slot, slotName: st.name });
            await refresh();
        }
        st.n = Math.min(4, st.n + 1);
        render();
    }

    function closeView() {
        state.view = null;
        state.viewBuild = null;
        state.renamingBackup = null;
        render();
    }

    /* ---- library ------------------------------------------------------------------------- */

    async function exportLibrary() {
        save(await lib.exportZip(), fileName("cycles-library") + ".zip");
        show("Exported the library.", "ok");
    }

    async function importLibrary(file) {
        var r;

        try {
            r = await lib.importZip(new Uint8Array(await file.arrayBuffer()));
        } catch (e) {
            show(file.name + ": " + e.message + ".", "bad");
            return;
        }
        await keep();
        await refresh();
        show("Imported " + r.builds + " firmware" + (r.builds === 1 ? "" : "s") + " and " + r.backups + " backup" +
             (r.backups === 1 ? "" : "s") + (r.skipped.length ? ". Left out: " + r.skipped.join("; ") : "") + ".",
             r.skipped.length ? "warn" : "ok");
    }

    async function refresh() {
        var all = await lib.db.all("backups"), n = 0;

        state.builds = await lib.builds();
        state.device = await lib.device();
        state.backups = {};
        all.sort(function (a, b) { return a.made < b.made ? 1 : -1; }).forEach(function (x) {
            (state.backups[x.build] = state.backups[x.build] || []).push(x);
            n++;
        });
        render();
        var text = "Library in this browser: " + state.builds.length + " firmware" + (state.builds.length === 1 ? "" : "s") +
                   " · " + n + " backup" + (n === 1 ? "" : "s");

        if (navigator.storage && navigator.storage.estimate) {
            var e = await navigator.storage.estimate();

            if (navigator.storage.persisted)
                state.persisted = await navigator.storage.persisted();
            text += " · " + kb(e.usage || 0) + (state.persisted ? "" : " (the browser may clear it when short of space: export it)");
        }
        $("usage").textContent = text;
    }

    /* ---- page ---------------------------------------------------------------------------- */

    function render() {
        renderChip();
        renderDevice();
        renderTiles();
        $("export").disabled = state.busy || !state.builds.length;
        $("import").disabled = state.busy;
        $("setup-open").disabled = state.busy;
        renderView();
    }

    function renderChip() {
        var ok = ready(), id = state.identity, c = $("chip");

        c.className = "chip" + (ok ? "" : " off");
        c.disabled = state.busy || !!NO_MIDI;
        $("chip-text").textContent = NO_MIDI ? "No Web MIDI" : !state.access ? "Connect the Cycles" : ok ? "Cycles connected · OS " + id.version :
                                     id ? "Not a Model:Cycles" : !(state.input && state.output) ? "Pick the MIDI ports" :
                                     state.asked ? "No answer" : "Asking…";
        c.setAttribute("aria-expanded", String(!$("ports").hidden));
        $("ports").hidden = !(state.access && (state.showPorts || !ok));
    }

    function renderDevice() {
        var box = $("device"), d = state.device.build, b = build(d), cur = currentOf(b), col, acts, sel;

        box.innerHTML = "";
        col = el("div", { class: "col" }, [el("div", { class: "label", text: "On your Cycles" })]);
        acts = el("div", { class: "acts" });
        box.appendChild(col);
        box.appendChild(acts);
        if (!state.builds.length) {
            col.appendChild(el("div", { class: "dname", text: "No firmware yet" }));
            col.appendChild(el("div", { class: "meta", text: "Add the firmware files you flash, then say which one is on the Cycles." }));
            acts.appendChild(button("Set up", openSetup, { kind: "inv", size: "big", disabled: state.busy }));
            return;
        }
        if (!b || state.chooseHere) {
            col.appendChild(el("div", { class: "dname", text: b ? b.name : "Not known yet" }));
            col.appendChild(el("div", { class: "meta", text: "The Cycles cannot tell which firmware it runs. Say it once; after that " +
                                                              "the page keeps track." }));
            sel = el("select", { "aria-label": "Firmware on the Cycles" });
            state.builds.forEach(function (x) { sel.appendChild(el("option", { value: x.key, text: x.name })); });
            sel.value = d || state.builds[0].key;
            acts.appendChild(sel);
            acts.appendChild(button("That's the one", async function () {
                state.chooseHere = false;
                await lib.setDevice(sel.value, true);
                await refresh();
            }, { kind: "inv", disabled: state.busy }));
            if (b)
                acts.appendChild(button("Cancel", function () { state.chooseHere = false; render(); }, { cls: "lnk" }));
            return;
        }
        col.appendChild(el("div", { class: "dname", text: b.name }));
        col.appendChild(el("div", { class: "meta" }, [
            el("span", {}, b.slotName ? ["Project ", el("b", { text: b.slotName })] : [cur ? "Its project" : "No project yet"]),
            el("span", {}, b.slot ? ["Slot ", el("b", { text: two(b.slot) })] : ["No slot given"]),
            el("span", { text: cur ? "Backed up " + ago(cur.made) : "Not backed up yet" })
        ]));
        acts.appendChild(button("Not this one?", function () { state.chooseHere = true; render(); }, { cls: "lnk", disabled: state.busy }));
        acts.appendChild(button("Back up now", backupButton, { kind: "inv", size: "big", disabled: state.busy || !ready(),
                                                               title: ready() ? "" : NO_MIDI ? "No Web MIDI in this browser" : "Connect the Cycles first" }));
    }

    function renderTiles() {
        var box = $("tiles");

        box.innerHTML = "";
        state.builds.forEach(function (b) { box.appendChild(tile(b)); });
        box.appendChild(addTile());
    }

    function tile(b) {
        var here = state.device.build === b.key, list = state.backups[b.key] || [], cur = currentOf(b), head, title, more, go, why, t;

        if (state.renaming === b.key) {
            title = el("input", { class: "rename", value: b.name, "aria-label": "Name of the firmware" });
            var done = async function (keepIt) {
                if (state.renaming !== b.key)
                    return;
                state.renaming = null;
                if (keepIt)
                    await lib.updateBuild(b.key, { name: title.value });
                await refresh();
            };
            title.onkeydown = function (ev) {
                if (ev.key === "Enter")
                    done(true);
                else if (ev.key === "Escape")
                    done(false);
            };
            title.onblur = function () { done(true); };
            setTimeout(function () { title.focus(); title.select(); }, 0);
        } else
            title = el("h3", { text: b.name });
        more = el("button", { type: "button", class: "more", "aria-label": "More for " + b.name, "aria-haspopup": "true",
                              "aria-expanded": String(state.menu === b.key), disabled: state.busy,
                              onclick: function (ev) { ev.stopPropagation(); state.menu = state.menu === b.key ? null : b.key; render(); } },
                     [dots()]);
        head = el("div", { class: "head" }, [
            el("div", { style: "display: flex; flex-direction: column; align-items: flex-start; gap: 8px; min-width: 0; flex: 1" },
               [here ? el("span", { class: "tag", text: "On the Cycles" }) : null, title]),
            more]);
        why = NO_MIDI ? "Needs Web MIDI: Chrome, Edge or Opera on a computer." : !ready() ? "Connect the Cycles first." : !state.device.build ? "Say first which firmware is on the Cycles." : "";
        go = el("div", { class: "go" }, here ?
            [button("On the Cycles now", null, { disabled: true, size: "big" })] :
            [button("Switch to this", function () { switchTo(b.key); }, { size: "big", disabled: state.busy || !!why }),
             why && !state.busy ? el("span", { class: "small", text: why }) : null]);
        t = el("article", { class: "tile" + (here ? " here" : "") }, [
            head,
            el("dl", { class: "facts" }, [
                el("dt", { text: "Project" }), el("dd", { text: b.slotName || (cur ? "unnamed" : "none yet") }),
                el("dt", { text: "Slot" }), el("dd", { text: b.slot ? two(b.slot) : "not given" }),
                el("dt", { text: "Backed up" }), el("dd", { text: cur ? ago(cur.made) : "never", style: "font-weight: 400" })
            ]),
            go
        ]);
        if (state.menu === b.key)
            t.appendChild(el("div", { class: "menu", role: "menu" }, [
                menuItem("History · " + list.length + " backup" + (list.length === 1 ? "" : "s"), function () { openHistory(b.key); }),
                menuItem("Rename", function () { state.menu = null; state.renaming = b.key; render(); }, "sep"),
                menuItem("Slot on the Cycles…", function () { openHistory(b.key); }),
                menuItem("Save .syx", async function () { state.menu = null; render(); save(await lib.buildData(b.key), fileName(b.name) + ".syx"); }),
                menuItem("Remove", function () { state.menu = null; removeBuild(b); }, "sep")
            ]));
        return t;
    }

    function menuItem(text, onclick, cls) {
        return el("button", { type: "button", role: "menuitem", class: cls || "", text: text, onclick: onclick });
    }

    function addTile() {
        var box = el("div", { class: "addtile" }, [
            button("+ Add firmware", function () { $("add-file").click(); }, { kind: "ghost", disabled: state.busy }),
            el("span", { class: "small", text: "Drop a .syx here or choose one. It stays in this browser." })
        ]);

        dropTarget(box);
        return box;
    }

    function dropTarget(box) {
        box.ondragover = function (ev) { ev.preventDefault(); box.classList.add("drag"); };
        box.ondragleave = function () { box.classList.remove("drag"); };
        box.ondrop = function (ev) {
            ev.preventDefault();
            box.classList.remove("drag");
            if (!state.busy && ev.dataTransfer && ev.dataTransfer.files.length)
                addFiles(Array.from(ev.dataTransfer.files));
        };
    }

    function openHistory(id) {
        state.menu = null;
        state.view = "history";
        state.viewBuild = id;
        render();
    }

    /* ---- over the page ------------------------------------------------------------------- */

    function renderView() {
        var o = $("overlay");

        o.hidden = !state.view;
        document.body.style.overflow = state.view ? "hidden" : "";
        if (!state.view) {
            o.innerHTML = "";
            o.dataset.mode = "";
            return;
        }
        if (state.view === "switch")
            return renderFlow();
        o.dataset.mode = state.view;
        o.className = "overlay" + (state.view === "history" ? " side" : "");
        o.innerHTML = "";
        o.appendChild(state.view === "history" ? historyView() : setupView());
    }

    function historyView() {
        var b = build(state.viewBuild), list = b ? state.backups[b.key] || [] : [], slot, name, rows;

        if (!b) {
            setTimeout(closeView, 0);
            return el("div");
        }
        slot = el("input", { value: b.slot ? two(b.slot) : "", size: 4, disabled: state.busy });
        name = el("input", { value: b.slotName || "", size: 10, disabled: state.busy });
        var store = async function () {     /* without redrawing, which would take the focus away */
            Object.assign(b, await lib.updateBuild(b.key, { slot: slot.value, slotName: name.value }));
            slot.value = b.slot ? two(b.slot) : "";
            renderDevice();
            renderTiles();
        };

        slot.onchange = store;
        name.onchange = store;
        rows = list.map(function (x) {
            var renaming = state.renamingBackup === x.key, input;

            if (renaming) {
                input = el("input", { value: x.name, placeholder: "a name for this backup", size: 18 });
                input.onkeydown = async function (ev) {
                    if (ev.key === "Enter" || ev.key === "Escape") {
                        ev.stopPropagation();       /* Escape ends the naming, not the history */
                        if (ev.key === "Enter")
                            await lib.renameBackup(x.key, input.value);
                        state.renamingBackup = null;
                        await refresh();
                    }
                };
                setTimeout(function () { input.focus(); }, 0);
            }
            return el("div", { class: "hrow" }, [
                el("div", { class: "what" }, [
                    el("div", { style: "font-weight: 700", text: ago(x.made) + (x.name ? " · " + x.name : "") }),
                    el("div", { class: "small", text: x.messages + " messages · " + kb(x.bytes) })
                ]),
                x.key === b.current ? el("span", { class: "tag", text: "Current" }) :
                    button("Make current", async function () { await lib.setCurrent(b.key, x.key); await refresh(); },
                           { kind: "ghost", size: "sm", disabled: state.busy }),
                button("Send to the Cycles", function () { sendBackup(x); },
                       { kind: "ghost", size: "sm", disabled: state.busy || !ready(),
                         title: ready() ? "" : NO_MIDI ? "No Web MIDI in this browser" : "Connect the Cycles first" }),
                el("div", { class: "links" }, renaming ? [el("label", { class: "field" }, ["Name", input])] : [
                    button("Name it", function () { state.renamingBackup = x.key; render(); }, { cls: "lnk" }),
                    button("Save .syx", async function () { save(await lib.backupData(x.key), fileName(b.name + " " + label(x)) + ".syx"); },
                           { cls: "lnk" }),
                    button("Delete", function () { removeBackup(x); }, { cls: "lnk", disabled: state.busy })
                ])
            ]);
        });
        return el("aside", { class: "drawer", role: "dialog", "aria-modal": "true", "aria-labelledby": "history-title" }, [
            el("div", { class: "head" }, [
                el("div", { style: "display: flex; flex-direction: column; gap: 6px; min-width: 0" }, [
                    el("div", { class: "small", style: "font-weight: 700; text-transform: uppercase", text: "History" }),
                    el("h1", { id: "history-title", text: b.name })
                ]),
                el("button", { type: "button", class: "close", "aria-label": "Close", text: "×", onclick: closeView })
            ]),
            el("div", { class: "boxed" }, [
                el("label", { class: "field" }, ["Slot on the Cycles", slot]),
                el("label", { class: "field" }, ["Name there", name]),
                el("span", { class: "small", style: "flex: 1 1 160px", text: "After a switch the page says to save its project there." })
            ]),
            el("section", { "aria-label": "Backups" }, [el("h2", { style: "font-size: 16px; margin-bottom: 8px", text: "Backups" })]
                .concat(rows.length ? rows : [el("p", { class: "small", text: "No backups yet. They come with Back up now and with every switch." })])
                .concat([el("p", { class: "small", style: "margin: 12px 0 0", text: "Send replaces the project on the Cycles; the page backs that one up first." })])),
            el("div", { style: "display: flex; flex-wrap: wrap; gap: 10px; margin-top: auto; padding-top: 16px; border-top: 3px solid var(--ink)" }, [
                button("Save the firmware .syx", async function () { save(await lib.buildData(b.key), fileName(b.name) + ".syx"); },
                       { kind: "ghost", size: "sm" }),
                button("Remove this firmware", function () { removeBuild(b); }, { kind: "ghost", size: "sm", disabled: state.busy })
            ])
        ]);
    }

    function setupView() {
        var st = state.setup, n = st.n, card, next = null, pips;

        pips = el("div", { class: "pips", "aria-hidden": "true" }, [1, 2, 3, 4].map(function (i) { return el("div", { class: "pip" + (i <= n ? " on" : "") }); }));
        card = el("section", { class: "card" });
        if (n === 1) {
            card.appendChild(el("h2", { text: "Connect your Model:Cycles" }));
            card.appendChild(el("p", { text: "Plug it in over USB and quit Elektron Transfer: the two cannot talk to it at the same time. " +
                                             "The browser asks for MIDI access once." }));
            if (NO_MIDI)
                card.appendChild(el("p", { style: "font-weight: 700", text: NO_MIDI_TEXT[NO_MIDI] }));
            card.appendChild(el("div", { class: "actions", style: "margin-top: 0" }, [
                button(ready() ? "Connected" : "Connect", function () { if (!state.access) connect(); else usePorts(); },
                       { size: "big", disabled: state.busy || ready() || !!NO_MIDI }),
                ready() ? el("span", { style: "display: inline-flex; align-items: center; gap: 10px; font-weight: 700" },
                             [el("span", { class: "dot", "aria-hidden": "true" }), "Model:Cycles · OS " + state.identity.version]) :
                state.asked ? el("span", { text: "No answer. Quit Elektron Transfer and press Connect again." }) : null
            ]));
            next = { ok: ready() };
        } else if (n === 2) {
            var drop = el("div", { class: "drop" }, [
                button("Choose .syx files", function () { $("add-file").click(); }, { kind: "ghost", disabled: state.busy }),
                el("span", { class: "small", text: "or drop them here" })
            ]);

            dropTarget(drop);
            card.appendChild(el("h2", { text: "Add the firmwares you use" }));
            card.appendChild(el("p", { text: "The .syx files you flash: the official OS from elektron.se, the builds you download from " +
                                             "the Flasher, any build for the Model:Cycles. They stay in this browser." }));
            card.appendChild(drop);
            if (state.builds.length)
                card.appendChild(el("ul", { class: "list" }, state.builds.map(function (b) {
                    return el("li", {}, [el("b", { style: "text-transform: uppercase", text: b.name }),
                                         el("span", { class: "small", text: (KNOWN[b.key] ? "recognized" : "checked") + " · " + kb(b.bytes) })]);
                })));
            next = { ok: state.builds.length > 0 };
        } else if (n === 3) {
            card.appendChild(el("h2", { text: "Which one is on your Cycles now?" }));
            card.appendChild(el("p", { text: "The Cycles cannot tell which firmware it runs. Say it once; after that the page keeps track." }));
            card.appendChild(el("fieldset", { style: "margin: 0; padding: 0; border: 0; display: flex; flex-direction: column; gap: 10px" },
                [el("legend", { class: "vh", text: "Firmware on the Cycles" })].concat(state.builds.map(function (b) {
                    var r = el("input", { type: "radio", name: "here", checked: st.pick === b.key });

                    r.onchange = function () {
                        st.pick = b.key;
                        st.slot = b.slot ? two(b.slot) : "";
                        st.name = b.slotName || "";
                        render();
                    };
                    return el("label", { class: "choice" + (st.pick === b.key ? " on" : "") }, [r, b.name]);
                }))));
            var slot = el("input", { value: st.slot, size: 4 }), name = el("input", { value: st.name, size: 10 });

            slot.oninput = function () { st.slot = slot.value; };
            name.oninput = function () { st.name = name.value; };
            card.appendChild(el("div", { style: "display: flex; flex-wrap: wrap; align-items: flex-end; gap: 12px" }, [
                el("label", { class: "field" }, ["Its slot on the Cycles", slot]),
                el("label", { class: "field" }, ["Name there", name]),
                el("span", { class: "small", style: "flex: 1 1 200px", text: "The slot that holds its project, so that the page can say " +
                                                                              "where to save it after a switch." })
            ]));
            next = { ok: !!st.pick };
        } else {
            var b = build(st.pick);

            card.appendChild(el("h2", { text: "Back up its project" }));
            card.appendChild(el("p", { text: "The page asks the Cycles for the project it plays now and keeps it as the project of " +
                                             (b ? b.name : "this firmware") + "." }));
            if (st.result)
                card.appendChild(el("div", { class: "result" }, [
                    el("div", { class: "label", style: "font-weight: 700; font-size: 13px; text-transform: uppercase", text: "Backed up" }),
                    el("div", { class: "big", text: (b && b.slotName ? b.slotName + " · " : "") + "project of " + (b ? b.name : "") }),
                    el("div", { text: st.result.backup.messages + " messages · " + kb(st.result.backup.bytes) + " · whole" })
                ]));
            else if (st.pct >= 0)
                card.appendChild(el("div", { class: "bar" }, [
                    el("div", { class: "track" }, [el("div", { class: "fill", id: "setup-fill", style: "width: " + st.pct + "%" })]),
                    el("span", { class: "pct", id: "setup-pct", text: st.pct + " %" })
                ]));
            if (st.error)
                card.appendChild(el("p", { style: "font-weight: 700", text: st.error }));
            card.appendChild(el("div", { class: "actions", style: "margin-top: 0" }, st.result ?
                [button("Open the overview", closeView, { size: "big" })] :
                [button(st.error ? "Try again" : "Back up now", setupBackup, { size: "big", disabled: state.busy || !ready() || st.pct >= 0 })]));
        }
        card.appendChild(el("div", { class: "nav", style: "margin-top: auto" }, [
            button("Back", function () { st.n = Math.max(1, n - 1); st.pct = -1; st.result = null; st.error = ""; render(); },
                   { kind: "ghost", size: "sm", disabled: n === 1 || state.busy }),
            next ? button("Next", setupNext, { size: "sm", disabled: !next.ok || state.busy }) : null
        ]));
        return el("div", { class: "setup", role: "dialog", "aria-modal": "true", "aria-label": "Set up" }, [
            el("div", { class: "shead" }, [
                el("div", { class: "stitle", text: "Set up · step " + n + " of 4" }),
                el("button", { type: "button", class: "close", "aria-label": "Close the setup", text: "×", onclick: closeView, disabled: state.busy })
            ]),
            pips,
            card
        ]);
    }

    function renderSetupBar() {
        var st = state.setup;

        if ($("setup-fill")) {
            $("setup-fill").style.width = st.pct + "%";
            $("setup-pct").textContent = st.pct + " %";
        } else
            render();
    }

    /* The switch over the page: its steps on the left, the one to do now on the right. Built once;
       the parts are redrawn, the buttons only when they change (a button replaced between press
       and release never gets its click: the panel redraws after every block sent). */
    function renderFlow() {
        var f = state.flow, o = $("overlay");

        if (!f || state.view !== "switch")
            return;
        if (o.dataset.mode !== "switch") {
            o.dataset.mode = "switch";
            o.className = "overlay";
            o.innerHTML = "";
            o.appendChild(el("div", { class: "dialog", role: "dialog", "aria-modal": "true", "aria-labelledby": "flow-title" }, [
                el("div", { class: "dhead" }, [el("h1", { id: "flow-title" }), el("span", { id: "flow-from", class: "small" })]),
                el("div", { class: "dbody" }, [
                    el("ol", { id: "steps", class: "steps" }),
                    el("div", { class: "panel" }, [el("div", { id: "panel-body", style: "display: flex; flex-direction: column; gap: 18px" }),
                                                   el("div", { id: "panel-actions", class: "actions" })])
                ]),
                el("div", { class: "dfoot" }, [
                    el("button", { type: "button", id: "flow-details", class: "lnk", "aria-expanded": "false", text: "Details ▸",
                                   onclick: function () {
                                       var open = $("flow-logbox").hidden;

                                       $("flow-logbox").hidden = !open;
                                       this.textContent = open ? "Details ▾" : "Details ▸";
                                       this.setAttribute("aria-expanded", String(open));
                                   } }),
                    el("div", { id: "flow-logbox", class: "logbox", hidden: true, style: "margin-top: 10px" }, [
                        el("pre", { id: "flow-log", class: "log", text: $("log").textContent }),
                        el("div", {}, [button("Copy protocol", copyLog, { kind: "ghost", size: "sm" })])
                    ])
                ])
            ]));
        }
        $("flow-title").textContent = f.title;
        $("flow-from").textContent = f.from;
        $("steps").innerHTML = "";
        f.steps.forEach(function (s, i) {
            $("steps").appendChild(el("li", { class: s.how }, [
                el("span", { class: "mark", "aria-hidden": "true" }, s.how === "done" ? [mark(CHECK)] : [s.how === "failed" ? "!" : String(i + 1)]),
                el("span", { text: s.text }),
                el("span", { class: "vh", text: s.how === "done" ? " (done)" : s.how === "doing" ? " (now)" : s.how === "failed" ? " (failed)" : "" })
            ]));
        });
        var p = f.panel || {}, body = $("panel-body"), act = $("panel-actions");

        body.innerHTML = "";
        if (p.title)
            body.appendChild(el("h2", { class: p.huge ? "huge" : "", text: p.title }));
        if (p.text)
            body.appendChild(el("p", { text: p.text }));
        if (p.items)
            body.appendChild(el("ol", {}, p.items.map(function (t) { return el("li", { text: t }); })));
        if (p.progress !== undefined && p.progress !== null)
            body.appendChild(el("div", { class: "bar" }, [
                el("div", { class: "track" }, [el("div", { class: "fill", style: "width: " + p.progress + "%" })]),
                el("span", { class: "pct", text: p.progress + " %" })
            ]));
        if (p.result)
            body.appendChild(el("div", { class: "result" }, [
                el("div", { style: "font-weight: 700; font-size: 13px; text-transform: uppercase", text: p.result.label }),
                el("div", { class: "big", text: p.result.big }),
                el("div", { text: p.result.meta })
            ]));
        var key = (f.actions || []).map(function (a) { return a.input ? a.input + "=" + a.value : a.label; }).join("|");

        if (act.dataset.key === key)
            return;
        act.dataset.key = key;
        act.innerHTML = "";
        (f.actions || []).forEach(function (a) {
            if (a.input) {
                act.appendChild(el("label", { class: "field" }, [a.caption, el("input", { name: a.input, value: a.value || "", size: a.size || 10 })]));
                return;
            }
            act.appendChild(button(a.label, function () {
                var now = state.flow, vals = {};

                Array.from(act.querySelectorAll("input")).forEach(function (i) { vals[i.name] = i.value; });
                if (now) {
                    now.inputs = vals;
                    if (now.answer)
                        now.answer(a.value);
                }
            }, { kind: a.kind, size: a.size }));
        });
    }

    async function copyLog() {
        var b = this;

        try {
            await navigator.clipboard.writeText(state.log.join("\n"));
            b.textContent = "Copied";
        } catch (e) {
            window.getSelection().selectAllChildren($("log"));
            b.textContent = "Selected: copy with ⌘C";
        }
        setTimeout(function () { b.textContent = "Copy protocol"; }, 2000);
    }

    $("chip").onclick = function () {
        if (!state.access)
            connect();
        else {
            state.showPorts = !state.showPorts;
            render();
        }
    };
    $("retry").onclick = usePorts;
    $("in").onchange = usePorts;
    $("out").onchange = usePorts;
    $("copy-log").onclick = copyLog;
    $("log-open").onclick = function () {
        $("logbox").hidden = !$("logbox").hidden;
        this.setAttribute("aria-expanded", String(!$("logbox").hidden));
    };
    $("setup-open").onclick = openSetup;
    $("add-file").onchange = function () { addFiles(Array.from(this.files)); this.value = ""; };
    $("export").onclick = exportLibrary;
    $("import").onclick = function () { $("import-file").click(); };
    $("import-file").onchange = function () { if (this.files[0]) importLibrary(this.files[0]); this.value = ""; };
    document.addEventListener("click", function (ev) {
        if (state.menu && !ev.target.closest(".menu") && !ev.target.closest(".more")) {
            state.menu = null;
            render();
        }
    });
    document.addEventListener("keydown", function (ev) {
        if (ev.key !== "Escape")
            return;
        if (state.menu) {
            state.menu = null;
            render();
        } else if ((state.view === "history" || state.view === "setup") && !state.busy && !state.renamingBackup)
            closeView();
    });
    window.addEventListener("beforeunload", function (ev) {
        if (state.busy) {
            ev.preventDefault();
            ev.returnValue = "";
        }
    });
    if (NO_MIDI) {
        $("nomidi").textContent = NO_MIDI_TEXT[NO_MIDI];
        $("nomidi").hidden = false;
    }
    refresh().then(function () {
        if (!state.builds.length && !NO_MIDI)
            openSetup();
    }).catch(function (e) { show("The library cannot be opened: " + e.message, "bad"); });
})();
