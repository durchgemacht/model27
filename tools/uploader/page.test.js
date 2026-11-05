/* Host test of the uploader page (docs/uploader/app.js) against a stand-in Cycles that answers the file
   commands from memory, with a minimal DOM: connect, list, make a folder, convert and upload, skip and rename,
   check what arrived, select and delete, find the way back by the path. tools/webuploader_check.sh */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const DOCS = path.join(__dirname, "..", "..", "docs", "uploader");
const E = require(path.join(DOCS, "elektron.js"));

let failures = 0;
function check(cond, what) {
    if (!cond) {
        failures++;
        console.log("FAIL: " + what);
    }
}

/* ---- a minimal DOM ---------------------------------------------------------------------- */
function element(id) {
    const el = {
        id, textContent: "", className: "", value: "", disabled: false, hidden: false, maxLength: 0, type: "",
        children: [], onclick: null, ondblclick: null, onchange: null, oninput: null, onsubmit: null, onkeydown: null,
        onblur: null, title: "", files: [], attrs: {}, style: {}, draggable: false,
        appendChild(c) { this.children.push(c); return c; },
        setAttribute(k, v) { this.attrs[k] = String(v); },
        focus() { this.focused = true; },
        select() {},
        blur() { if (this.onblur) this.onblur(); },
        click() { if (this.onclick) return this.onclick(); },
        get innerHTML() { return this._html || ""; },
        set innerHTML(v) { this._html = v; this.children = []; }
    };
    return el;
}
const ids = ["status", "nomidi", "chip", "chip-text", "ports", "in", "out", "retry", "src", "remove-sel", "pick", "chooser",
             "files", "upload", "path", "select-mode", "del-sel", "mkdir", "refresh", "newdir", "dirname", "mkdir-ok", "mkdir-cancel",
             "folder", "src-mkdir", "pick-dir", "chooser-dir", "overall", "overall-fill", "dst"];
const elements = {};
ids.forEach(id => { elements[id] = element(id); });
/* hidden in index.html until the page shows them */
["status", "nomidi", "ports", "newdir", "overall"].forEach(id => { elements[id].hidden = true; });

/* ---- a stand-in Cycles ------------------------------------------------------------------ */
const drive = new Map([["/", { folder: true }], ["/factory", { folder: true, protect: true }],
                       ["/incoming", { folder: true }]]);
const open = new Map();
let nextId = 7, log = [];
function children(dir) {
    const pre = dir === "/" ? "/" : dir + "/";
    return [...drive.keys()].filter(p => p !== dir && p.startsWith(pre) && !p.slice(pre.length).includes("/"));
}
function answer(m) {
    const seq = (m[0] << 8) | m[1], type = m[4], body = m.slice(5);
    const out = (bytes) => [0, 99, (seq >> 8) & 255, seq & 255, type | 0x80].concat(bytes);
    const str = (b, p) => { let e = p; while (b[e] !== 0) e++; return E.decodeText(b.slice(p, e)); };
    log.push(type);
    switch (type) {
    case E.TYPE.PING:
        return out([1]);
    case E.TYPE.READ_DIR: {
        const dir = str(body, 0), bytes = [];
        if (!drive.has(dir) || !drive.get(dir).folder)
            return out([]);
        children(dir).forEach(p => {
            const it = drive.get(p);
            bytes.push(...E.u32(it.folder ? 0 : 0x1235), ...E.u32(it.folder ? 0 : it.data.length),
                       it.protect ? 1 : 0, it.folder ? 0x44 : 0x46, ...E.encodeText(p.slice(p.lastIndexOf("/") + 1)), 0);
        });
        return out(bytes);
    }
    case E.TYPE.CREATE_DIR: {
        const p = str(body, 0);
        if (drive.has(p))
            return out([0]);
        drive.set(p, { folder: true });
        return out([1]);
    }
    case E.TYPE.OPEN_WRITE: {
        const size = E.readU32(body, 0), p = str(body, 4), parent = E.parentPath(p);
        if (!drive.has(parent) || drive.get(parent).protect)
            return out([0, ...E.encodeText("Write protected"), 0]);
        open.set(nextId, { path: p, size, data: new Uint8Array(size) });
        return out([1, ...E.u32(nextId++)]);
    }
    case E.TYPE.WRITE: {
        const id = E.readU32(body, 0), len = E.readU32(body, 4), off = E.readU32(body, 8), f = open.get(id);
        if (!f || off + len > f.size || len > E.BLOCK)
            return out([0]);
        f.data.set(body.slice(12, 12 + len), off);
        return out([1]);
    }
    case E.TYPE.CLOSE_WRITE: {
        const id = E.readU32(body, 0), f = open.get(id);
        if (!f)
            return out([0]);
        open.delete(id);
        drive.set(f.path, { folder: false, data: f.data });
        return out([1]);
    }
    /* a file marked inUse stands for the one the Cycles sometimes refuses until it restarts */
    case E.TYPE.DELETE_FILE: {
        const p = str(body, 0), it = drive.get(p);
        if (!it || it.folder || drive.get(E.parentPath(p)).protect)
            return out([0]);
        if (it.inUse)
            return out([0, ...E.encodeText("File in use"), 0]);
        drive.delete(p);
        return out([1]);
    }
    case E.TYPE.DELETE_DIR: {
        const p = str(body, 0), it = drive.get(p);
        if (p === "/" || !it || !it.folder || it.protect || children(p).length)
            return out([0]);
        drive.delete(p);
        return out([1]);
    }
    }
    return out([0]);
}
let silent = false;      /* a Cycles that stops answering */
const input = { id: "in1", name: "Elektron Model:Cycles", manufacturer: "Elektron", onmidimessage: null };
const output = {
    id: "out1", name: "Elektron Model:Cycles", manufacturer: "Elektron",
    send(bytes) {
        if (silent)
            return;
        const m = E.unframe(Uint8Array.from(bytes));
        const reply = E.frame(answer(m));
        /* in two pieces, with a clock byte in between, as MIDI may deliver it */
        setTimeout(() => {
            input.onmidimessage({ data: Uint8Array.from([...reply.slice(0, 5), 0xf8]) });
            input.onmidimessage({ data: reply.slice(5) });
        }, 0);
    }
};
const access = { inputs: new Map([["in1", input]]), outputs: new Map([["out1", output]]), onstatechange: null };

/* ---- the browser around the page -------------------------------------------------------- */
const tone = new Float32Array(48000);
for (let i = 0; i < tone.length; i++)
    tone[i] = 0.5 * Math.sin(2 * Math.PI * 440 * i / 48000);
/* a wavetable of two frames of 256, a sine then a saw: what model27's tools/wavetable.py makes */
const table = Float32Array.from({ length: 512 }, (_, k) => (k < 256 ? 0.999 * Math.sin(2 * Math.PI * k / 256)
                                                                  : (k - 256) / 128 - 1));
const sawFirst = Float32Array.from([...table.slice(256), ...table.slice(0, 256)]);
class OfflineAudioContext {
    constructor(ch, len, rate) { this.rate = rate; }
    async decodeAudioData(buf) {
        const kind = new Uint8Array(buf)[0];
        if (kind === 0x57)                                         /* "W": the wavetable, mono */
            return { numberOfChannels: 1, sampleRate: this.rate, length: table.length, getChannelData: () => table };
        if (kind === 0x58)                                         /* "X": the same frames, the saw first */
            return { numberOfChannels: 1, sampleRate: this.rate, length: sawFirst.length, getChannelData: () => sawFirst };
        if (kind !== 0x52)
            throw new Error("not audio");
        return { numberOfChannels: 2, sampleRate: this.rate, length: tone.length,
                 getChannelData: (c) => (c === 0 ? tone : new Float32Array(tone.length)) };
    }
}
function file(name, firstByte, type) {
    return { name, size: 1000, type: type === undefined ? "audio/wav" : type,
             arrayBuffer: async () => Uint8Array.from([firstByte, 1, 2]).buffer };
}
/* a file as Add folder hands it over, with its path in the folder picked; one that is not audio by its name and type */
const rel = (p, b) => Object.assign(file(p.split("/").pop(), b, /\.wav$/.test(p) ? "audio/wav" : ""), { webkitRelativePath: p });
/* what a drop from the computer hands over: entries, folders read a batch at a time */
const fileEntry = (name, b) => ({ isFile: true, isDirectory: false, name,
                                  file(ok) { ok(file(name, b, /\.wav$/.test(name) ? "audio/wav" : "text/plain")); } });
const dirEntry = (name, kids) => ({ isFile: false, isDirectory: true, name, createReader() {
    let given = 0;
    return { readEntries(ok) { ok(given++ ? [] : kids); } };
} });
const fromDisk = (...entries) => ({ types: ["Files"], items: entries.map(e => ({ kind: "file", webkitGetAsEntry: () => e })), files: [] });
const sandbox = {
    window: null,
    document: {
        getElementById: (id) => elements[id],
        createElement: () => element(""),
        addEventListener: () => {}
    },
    navigator: { requestMIDIAccess: async () => access },
    OfflineAudioContext, setTimeout, clearTimeout, console, Uint8Array, Int16Array, Float32Array, DataView,
    Array, Math, Promise, Error, String, Object, Map,
    addEventListener: () => {}
};
sandbox.window = sandbox;
/* a new folder: New folder opens the field under the path, its name typed, Make it */
const submit = { preventDefault() {} };
function newFolder(name) {
    elements.mkdir.onclick();
    check(!elements.newdir.hidden && elements.mkdir.disabled && elements.dirname.focused, "New folder opens the name field");
    elements.dirname.value = name;
    return elements.newdir.onsubmit(submit);
}
let confirmAnswer = true, asked = [];
sandbox.window.confirm = (text) => { asked.push(text); return confirmAnswer; };
vm.createContext(sandbox);
for (const f of ["elektron.js", "app.js"])
    vm.runInContext(fs.readFileSync(path.join(DOCS, f), "utf8"), sandbox, { filename: f });

const settle = () => new Promise(r => setTimeout(r, 20));
async function until(cond, what) {
    for (let i = 0; i < 500 && !cond(); i++)
        await settle();
    check(cond(), what);
}
const under = (dir) => [...drive.keys()].filter(p => p === dir || p.startsWith(dir + "/"));
const kinds = (from) => log.slice(from).filter(t => t === E.TYPE.DELETE_FILE || t === E.TYPE.DELETE_DIR);

/* the Cycles' side: rows of icon, name, size and, for a folder, its › */
const shown = () => elements.path.attrs["data-path"];
const crumbs = () => elements.path.children.filter(c => /^crumb/.test(c.className));
const crumbText = () => crumbs().map(c => c.textContent);
/* a row's part by its class: box, pix, nm, size, open */
const part = (li, cls) => li.children.find(c => c.className.split(" ")[0] === cls);
const rowName = (li) => (part(li, "nm") ? part(li, "nm").children[0].textContent : li.textContent);
const folderNames = () => elements.folder.children.map(rowName);
const row = (name) => elements.folder.children.find(li => part(li, "nm") && rowName(li) === name);
const sel = () => elements.folder.children.filter(li => / sel$/.test(li.className)).map(rowName);
let stopped = false;
const event = (mods) => Object.assign({ stopPropagation() { stopped = true; }, preventDefault() {}, target: elements.folder }, mods);
const click = (name, mods) => row(name).onclick(event(mods));
const key = (list, k, mods) => elements[list].onkeydown(Object.assign({ key: k, preventDefault() {}, target: elements[list] }, mods));
const confirmed = (yes) => { confirmAnswer = yes; };

/* the list to upload: rows of icon, name (and a line saying why), state */
const files = () => elements.files.children.filter(li => li.children.length === 4);
const fname = (i) => files()[i].children[2].children[0];
const fwhy = (i) => (files()[i].children[2].children[1] || { textContent: "" }).textContent;
const fstate = (i) => files()[i].children[3];
/* the list as a tree: each row's name and depth, a row by its name */
const tree = () => files().map(li => "  ".repeat((parseInt(li.style.paddingLeft, 10) - 6) / 18) + li.children[2].children[0].textContent);
const lrow = (name) => files().find(li => li.children[2].children[0].textContent === name);
const lstate = (name) => lrow(name).children[3];
const halt = { preventDefault() {}, stopPropagation() {} };
const dragRow = (name) => lrow(name).ondragstart({ dataTransfer: { setData() {} } });
const internal = () => Object.assign({ dataTransfer: { types: ["text/plain"] } }, halt);
const clearList = () => {
    key("files", "a", { metaKey: true });
    elements["remove-sel"].onclick();
};
const add = (...list) => {
    elements.chooser.files = list;
    elements.chooser.onchange();
};
const uploaded = (n) => until(() => new RegExp("of " + n + " uploaded").test(elements.status.textContent), "the upload of " + n + " ends");

(async () => {
    /* before connecting: the chip offers it, nothing to see or do on the Cycles' side */
    check(elements["chip-text"].textContent === "Connect the Cycles" && elements.chip.className === "chip off" && elements.ports.hidden,
          "before: the chip offers to connect, no ports yet: " + elements["chip-text"].textContent);
    check(elements.status.hidden && elements.nomidi.hidden, "no status line and no Web MIDI warning yet");
    check(/Connect the Cycles/.test(elements.folder.innerHTML), "the Cycles' side asks to connect");
    check(elements.upload.disabled && elements.upload.textContent === "Upload → /", "Upload is off: " + elements.upload.textContent);
    check(elements["del-sel"].disabled && elements.mkdir.disabled && elements.refresh.disabled, "the Cycles' tools are off");
    check(/drop-here/.test(elements.files.innerHTML) && elements["remove-sel"].disabled, "the empty list invites a drop");
    check(JSON.stringify(crumbText()) === '["+Drive"]' && crumbs()[0].className === "crumb here", "the path is the drive");

    /* connect: the chip asks for MIDI, ports picked, ping, root listed */
    elements.chip.onclick();
    await until(() => elements["chip-text"].textContent === "Cycles connected", "connects");
    check(elements.status.hidden, "no status line for it: the chip says it");
    check(elements["chip-text"].textContent === "Cycles connected" && elements.chip.className === "chip", "the chip says so");
    check(elements.in.value === "in1" && elements.out.value === "out1", "the Cycles' ports are picked");
    check(elements.ports.hidden, "the ports hide once the Cycles answers");
    elements.chip.onclick();
    check(!elements.ports.hidden && elements.chip.attrs["aria-expanded"] === "true", "the chip shows the ports again");
    elements.chip.onclick();
    check(elements.ports.hidden, "and hides them");
    check(JSON.stringify(folderNames()) === '["factory","incoming"]', "the root is listed: " + folderNames());
    check(part(row("factory"), "size").textContent === "protected" && row("factory").className === "folder kept",
          "factory shows as protected: " + row("factory").className);
    check(part(row("factory"), "pix").className === "pix dir" && part(row("factory"), "open").textContent === "›",
          "a folder has its icon and its ›");
    check(shown() === "/" && elements["del-sel"].disabled && elements["del-sel"].textContent === "Delete", "nothing selected");

    /* a new folder: no name, no folder; a name, made and entered */
    check(elements.newdir.hidden, "the name field is closed");
    await newFolder("  ");
    check(elements.status.className === "status warn" && /Type a name/.test(elements.status.textContent), "an empty name is asked for");
    check(children("/").length === 2 && !elements.newdir.hidden, "nothing is made, the field stays open");
    elements["mkdir-cancel"].onclick();
    check(elements.newdir.hidden && elements.dirname.value === "", "Cancel closes and empties it");
    newFolder("My Samples");
    await until(() => shown() === "/My Samples", "the new folder is made and entered");
    check(elements.newdir.hidden && elements.dirname.value === "", "the field closes after");
    check(drive.has("/My Samples"), "the stand-in has the folder");
    check(JSON.stringify(crumbText()) === '["+Drive","My Samples"]' && !crumbs()[0].disabled && crumbs()[1].className === "crumb here",
          "the path shows it, the drive is a link: " + crumbText());
    check(elements.folder.children.length === 0 && /This folder is empty\./.test(elements.folder.innerHTML),
          "an empty folder says so: " + elements.folder.innerHTML);

    /* two files: one audio, one not; Upload names how many go where */
    add(file("Kick 01.wav", 0x52), file("notes.txt", 0x00));
    check(files().length === 2 && fname(0).textContent === "Kick 01" && fstate(0).textContent === "1 KB", "two files listed");
    check(elements.upload.textContent === "Upload 2 files → /My Samples" && !elements.upload.disabled,
          "the button names them and the folder: " + elements.upload.textContent);
    elements.upload.onclick();
    await uploaded(2);
    check(elements.status.textContent.indexOf("1 of 2 uploaded") === 0 && elements.status.className === "status bad",
          "one of two: " + elements.status.textContent);
    check(/^done · 94 KB$/.test(fstate(0).textContent) && fstate(0).className === "state ok" && fwhy(0) === "",
          "the audio file is done: " + fstate(0).textContent);
    check(fstate(1).textContent === "failed" && fstate(1).className === "state bad" &&
          fwhy(1) === "The browser cannot read this audio file.", "the other one fails, and says why: " + fwhy(1));
    check(elements.upload.textContent === "Upload 1 file → /My Samples", "the failed one is still to do: " + elements.upload.textContent);

    /* what arrived */
    const got = drive.get("/My Samples/Kick 01");
    check(got && !got.folder, "the file is on the drive under its name");
    if (got) {
        const dv = new DataView(got.data.buffer);
        check(got.data.length === 64 + 96000 + 16, "48000 frames with header and end: " + got.data.length);
        check(dv.getUint32(4) === 96000 && dv.getUint32(8) === 48000 && got.data[1] === 0, "header: bytes, rate, mono");
        let worst = 0;
        for (let i = 0; i < 48000; i++)
            worst = Math.max(worst, Math.abs(dv.getInt16(64 + 2 * i) - Math.round(tone[i] / 2 * 32768)));
        check(worst <= 1, "the frames are the mix of both channels, big-endian (off by " + worst + ")");
    }
    check(log.filter(t => t === E.TYPE.WRITE).length === Math.ceil((64 + 96000 + 16) / E.BLOCK), "written in 8-KiB blocks");

    /* the failed one leaves the list: selected, then Remove */
    files()[1].onclick({});
    check(/ sel$/.test(files()[1].className) && elements["remove-sel"].textContent === "Remove 1" && !elements["remove-sel"].disabled,
          "a click selects it: " + elements["remove-sel"].textContent);
    elements["remove-sel"].onclick();
    check(files().length === 1 && elements["remove-sel"].disabled, "the failed file is removed from the list");
    check(elements.upload.disabled && elements.upload.textContent === "Upload → /My Samples", "nothing left to do");

    /* a name already in the folder is skipped, nothing is written for it */
    let writes = log.length;
    add(file("Kick 01.aif", 0x52));
    elements.upload.onclick();
    await uploaded(1);
    check(fstate(1).textContent === "skipped" && fstate(1).className === "state skip" &&
          /^Something named Kick 01 is already in \/My Samples; it stays as it is\.$/.test(fwhy(1)), "it is skipped: " + fwhy(1));
    check(elements.status.textContent === "0 of 1 uploaded to /My Samples. 1 skipped: the name is already there." &&
          elements.status.className === "status warn", "the status line says so: " + elements.status.textContent);
    check(!log.slice(writes).includes(E.TYPE.OPEN_WRITE), "and nothing is opened for it");
    check(elements.upload.disabled, "a skipped file is not tried again");

    /* renamed by a double-click: Escape keeps the name, Enter takes the new one */
    add(file("Kick 01.wav", 0x52));
    files()[2].ondblclick();
    check(fname(2).className === "rename" && fname(2).value === "Kick 01", "a double-click opens the name");
    fname(2).value = "zzz";
    fname(2).onkeydown({ key: "Escape" });
    check(fname(2).textContent === "Kick 01", "Escape keeps it: " + fname(2).textContent);
    files()[2].ondblclick();
    fname(2).value = "Kick 02.v1";
    fname(2).onkeydown({ key: "Enter" });
    check(fname(2).textContent === "Kick 02.v1", "Enter takes it, dots and all: " + fname(2).textContent);
    files()[0].ondblclick();
    check(fname(0).className !== "rename", "a done file keeps its name");
    elements.upload.onclick();
    await uploaded(1);
    check(drive.has("/My Samples/Kick 02.v1") && /^done/.test(fstate(2).textContent), "it is uploaded under the new name");

    /* writing into a protected folder: the Cycles' refusal shows */
    crumbs()[0].onclick();
    await until(() => shown() === "/", "the drive's link goes to the root");
    check(part(row("factory"), "open").textContent === "›" && row("factory").attrs["aria-selected"] === "false", "a folder row shows its ›");
    click("factory");
    await until(() => shown() === "/factory", "a click anywhere on a folder's row opens it");
    clearList();
    check(files().length === 0, "⌘A and Remove empty the list");
    add(file("Snare.wav", 0x52));
    elements.upload.onclick();
    await uploaded(1);
    check(fstate(0).textContent === "failed" && /Write protected/.test(fwhy(0)), "the refusal is shown: " + fwhy(0));
    check(!/warning/.test(elements.status.textContent), "no warning outside /Wavetables");

    /* /Wavetables, which model27's CHORD Tables plays: a table whose first frame is no sine is told */
    crumbs()[0].onclick();
    await until(() => shown() === "/", "back at the root again");
    newFolder("Wavetables");
    await until(() => shown() === "/Wavetables", "/Wavetables is made and entered");
    clearList();
    add(file("01.wav", 0x57), file("02.wav", 0x58));
    elements.upload.onclick();
    await uploaded(2);
    check(/^done/.test(fstate(0).textContent) && fwhy(0) === "", "01, a sine first: done, no warning: " + fwhy(0));
    check(/^done/.test(fstate(1).textContent) && fstate(1).className === "state warn" &&
          fwhy(1) === "Warning: its first 256 samples are no sine, so CHORD Tables plays no sine at SWEEP 0.",
          "02, a saw first: done, with the warning: " + fwhy(1));
    check(/2 of 2 uploaded to \/Wavetables\. 1 with a warning/.test(elements.status.textContent) &&
          elements.status.className === "status warn", "the status line counts it: " + elements.status.textContent);
    check(drive.has("/Wavetables/01") && drive.has("/Wavetables/02"), "both are on the drive: a warning, not a refusal");

    /* a file CHORD Tables cannot play (a second of tone: 48000 samples, not frames of 256) is not written */
    clearList();
    const before = log.length;
    add(file("03.wav", 0x52), file("04.wav", 0x57));
    elements.upload.onclick();
    await uploaded(2);
    check(fstate(0).className === "state bad" &&
          fwhy(0) === "CHORD Tables plays 256 to 8192 samples in steps of 256, this file has 48000.",
          "03 is refused with the reason: " + fwhy(0));
    check(!drive.has("/Wavetables/03") && drive.has("/Wavetables/04"), "03 is not on the drive, 04 is");
    check(log.slice(before).filter(t => t === E.TYPE.OPEN_WRITE).length === 1, "only 04 was opened for writing");
    check(/1 of 2 uploaded to \/Wavetables\. 1 not uploaded: CHORD Tables cannot play it\./.test(elements.status.textContent) &&
          elements.status.className === "status bad", "the status line says it: " + elements.status.textContent);

    /* selecting on the Cycles: a click, Shift for a run, ⌘ to add or take one */
    check(JSON.stringify(folderNames()) === '["01","02","04"]', "the folder: " + folderNames());
    click("01");
    check(JSON.stringify(sel()) === '["01"]' && row("01").attrs["aria-selected"] === "true" &&
          elements["del-sel"].textContent === "Delete 1" && !elements["del-sel"].disabled, "a click selects one");
    click("04", { shiftKey: true });
    check(JSON.stringify(sel()) === '["01","02","04"]' && elements["del-sel"].textContent === "Delete 3", "Shift selects the run: " + sel());
    click("02", { metaKey: true });
    check(JSON.stringify(sel()) === '["01","04"]', "⌘ takes one out: " + sel());
    click("02", { ctrlKey: true });
    check(JSON.stringify(sel()) === '["01","02","04"]', "Ctrl puts it back: " + sel());
    click("02");
    check(JSON.stringify(sel()) === '["02"]', "a plain click picks only that one: " + sel());
    key("folder", "Escape");
    check(sel().length === 0 && elements["del-sel"].disabled, "Escape clears the selection");

    /* deleting the selection: one question, nothing without a yes */
    click("01");
    click("04", { metaKey: true });
    confirmed(false);
    let from = log.length;
    await elements["del-sel"].onclick();
    check(asked[asked.length - 1] === "Delete 2 samples from the Cycles? This cannot be undone.", "it asks once: " + asked[asked.length - 1]);
    check(kinds(from).length === 0 && drive.has("/Wavetables/01"), "a no deletes nothing");
    check(JSON.stringify(sel()) === '["01","04"]', "and the selection stays");
    confirmed(true);
    from = log.length;
    elements["del-sel"].onclick();
    await until(() => elements.status.textContent === "Deleted 2 items from /Wavetables.", "a yes deletes both: " + elements.status.textContent);
    check(elements.status.className === "status ok", "said plainly");
    check(!drive.has("/Wavetables/01") && !drive.has("/Wavetables/04") && drive.has("/Wavetables/02"), "only those two are gone");
    check(kinds(from).length === 2, "two requests");
    check(JSON.stringify(folderNames()) === '["02"]' && sel().length === 0 && shown() === "/Wavetables",
          "the list shows what is left, nothing selected; the page stays in the folder");

    /* one sample: the question names it */
    click("02");
    confirmed(false);
    await elements["del-sel"].onclick();
    check(asked[asked.length - 1] === "Delete “02” from the Cycles? This cannot be undone.", "one is named: " + asked[asked.length - 1]);
    confirmed(true);

    /* the root: what the Cycles protects and /incoming cannot be selected; ⌘A takes the rest */
    crumbs()[0].onclick();
    await until(() => shown() === "/", "back at the root for deleting");
    click("factory", { metaKey: true });
    click("incoming", { shiftKey: true });
    check(sel().length === 0 && elements["del-sel"].disabled && shown() === "/", "factory and incoming cannot be selected");
    key("folder", "a", { metaKey: true });
    check(JSON.stringify(sel()) === '["My Samples","Wavetables"]' && elements["del-sel"].textContent === "Delete 2", "⌘A: " + sel());
    key("folder", "Backspace", { target: { tagName: "INPUT" } });
    check(JSON.stringify(sel()) === '["My Samples","Wavetables"]', "a key typed into a field is not the list's");
    key("folder", "Escape");

    /* a folder with a folder in it goes with everything in it, the contents first; Backspace deletes */
    drive.set("/My Samples/Hats", { folder: true });
    drive.set("/My Samples/Hats/Hat 1", { folder: false, data: new Uint8Array(80) });
    drive.set("/My Samples/Hats/Hat 2", { folder: false, data: new Uint8Array(80) });
    click("My Samples", { metaKey: true });
    check(JSON.stringify(sel()) === '["My Samples"]' && shown() === "/", "⌘-click selects a folder instead of opening it");
    from = log.length;
    key("folder", "Backspace");
    await until(() => elements.status.textContent === "Deleted /My Samples.", "the folder is deleted: " + elements.status.textContent);
    check(/^Delete the folder “My Samples” and everything in it from the Cycles\?/.test(asked[asked.length - 1]),
          "it asks about the folder and everything in it: " + asked[asked.length - 1]);
    check(under("/My Samples").length === 0, "nothing of it is left: " + under("/My Samples"));
    /* Kick 01, Kick 02.v1, then Hats with its two files: the stand-in lists in the order things were made */
    check(JSON.stringify(kinds(from)) === JSON.stringify([E.TYPE.DELETE_FILE, E.TYPE.DELETE_FILE, E.TYPE.DELETE_FILE,
                                                          E.TYPE.DELETE_FILE, E.TYPE.DELETE_DIR, E.TYPE.DELETE_DIR]),
          "four files, two folders, each folder after its contents: " + kinds(from).map(t => "0x" + t.toString(16)));
    check(!row("My Samples") && shown() === "/", "it leaves the list; the page stays at the root");
    check(drive.has("/Wavetables/02") && drive.has("/incoming"), "the other folders stay");

    /* the Cycles refuses one: it stops there, says why, and lists what is left */
    drive.set("/Kit", { folder: true });
    drive.set("/Kit/a", { folder: false, data: new Uint8Array(80) });
    drive.set("/Kit/b", { folder: false, data: new Uint8Array(80), inUse: true });
    drive.set("/Kit/c", { folder: false, data: new Uint8Array(80) });
    drive.set("/Loose", { folder: false, data: new Uint8Array(80) });
    elements.refresh.onclick();
    await until(() => !!row("Kit") && !!row("Loose"), "the new ones are listed");
    click("Kit", { ctrlKey: true });
    click("Loose", { metaKey: true });
    elements["del-sel"].onclick();
    await until(() => elements.status.className === "status bad", "the refusal ends it");
    check(asked[asked.length - 1] === "Delete 1 sample and 1 folder with everything in them from the Cycles? This cannot be undone.",
          "a mixed selection is counted: " + asked[asked.length - 1]);
    check(elements.status.textContent === "the Cycles did not delete /Kit/b: File in use", "the refusal is shown: " + elements.status.textContent);
    check(!drive.has("/Kit/a") && drive.has("/Kit/b") && drive.has("/Kit/c") && drive.has("/Kit") && drive.has("/Loose"),
          "a went; b, what follows and Loose stay");
    check(!!row("Kit") && shown() === "/", "the folder is still listed");
    check(JSON.stringify(sel()) === '["Kit","Loose"]', "what is left stays selected: " + sel());
    check(!elements.chip.disabled && !elements["del-sel"].disabled, "the page takes clicks again");

    /* a Shift-click with nothing clicked before starts the run there */
    drive.set("/S", { folder: true });
    ["a", "b", "c", "d"].forEach(n => drive.set("/S/" + n, { folder: true }));
    elements.refresh.onclick();
    await until(() => !!row("S"), "S is listed");
    click("S");
    await until(() => shown() === "/S", "into S");
    click("a", { shiftKey: true });
    check(JSON.stringify(sel()) === '["a"]' && shown() === "/S", "a first Shift-click selects that folder: " + sel());
    click("d", { shiftKey: true });
    check(JSON.stringify(sel()) === '["a","b","c","d"]', "a second one the run between: " + sel());
    key("folder", "Escape");

    /* Select: a box on each row, a click picks folders too, Shift a run; off again, nothing stays selected */
    check(!elements["select-mode"].disabled && elements["select-mode"].attrs["aria-pressed"] === "false" &&
          !/selecting/.test(elements.folder.className), "Select is off");
    elements["select-mode"].onclick();
    check(elements["select-mode"].attrs["aria-pressed"] === "true" && elements.folder.className === "rows selecting" &&
          part(row("a"), "box").className === "box", "Select on: the rows show their box");
    click("a");
    check(JSON.stringify(sel()) === '["a"]' && shown() === "/S", "a click picks a folder instead of opening it: " + sel());
    click("c");
    check(JSON.stringify(sel()) === '["a","c"]', "a second click adds one: " + sel());
    click("a");
    check(JSON.stringify(sel()) === '["c"]', "a click again takes it out: " + sel());
    click("d", { shiftKey: true });
    check(JSON.stringify(sel()) === '["a","b","c","d"]' && elements["del-sel"].textContent === "Delete 4",
          "Shift adds the run from the last click: " + sel());
    elements["select-mode"].onclick();
    check(sel().length === 0 && elements.folder.className === "rows" && elements["del-sel"].disabled, "Select off clears the selection");
    click("a");
    await until(() => shown() === "/S/a", "a click opens a folder again");
    crumbs()[0].onclick();
    await until(() => shown() === "/", "back at the root");
    elements["select-mode"].onclick();
    check(part(row("factory"), "box").className === "box off", "protected rows have no box to tick");
    elements["select-mode"].onclick();

    /* the tree: into a folder by a double-click, the next one by Enter, back by the path */
    drive.set("/A", { folder: true });
    drive.set("/A/B", { folder: true });
    drive.set("/A/Kit", { folder: true });          /* the same name as the one selected at the root */
    elements.refresh.onclick();
    await until(() => !!row("A"), "A is listed");
    click("A");
    await until(() => shown() === "/A", "a click opens A");
    check(JSON.stringify(folderNames()) === '["B","Kit"]' && sel().length === 0,
          "A lists B and Kit, nothing selected, not even its Kit: " + folderNames() + " / " + sel());
    click("B", { detail: 2 });
    await new Promise(r => setTimeout(r, 150));
    check(shown() === "/A", "the second click of a double-click does not open what is under it: " + shown());
    click("B", { metaKey: true });
    key("folder", "Enter");
    await until(() => shown() === "/A/B", "Enter opens the selected folder");
    check(JSON.stringify(crumbText()) === '["+Drive","A","B"]', "the path: " + crumbText());
    check(/This folder is empty\./.test(elements.folder.innerHTML), "B is empty and says so");
    crumbs()[1].onclick();
    await until(() => shown() === "/A", "the path's A goes to A");
    crumbs()[0].onclick();
    await until(() => shown() === "/", "its drive goes to the root");
    check(!!row("A") && !!row("Kit") && !!row("factory"), "the root is listed again");

    /* ---- the list as a tree -------------------------------------------------------------- */

    /* Add folder: the folder picked with what is in it, audio only */
    clearList();
    elements["chooser-dir"].files = [rel("Kit A/BD 01.wav", 0x52), rel("Kit A/Snares/SD 01.wav", 0x52),
                                     rel("Kit A/.DS_Store", 0), rel("Kit A/readme.txt", 0)];
    elements["chooser-dir"].onchange();
    check(JSON.stringify(tree()) === JSON.stringify(["Kit A", "  Snares", "    SD 01", "  BD 01"]),
          "the folder comes with its folders, folders first: " + tree());
    check(elements.status.textContent === "2 files left out: not audio." && elements.status.className === "status warn",
          "what is not audio is left out and counted: " + elements.status.textContent);
    check(lstate("Kit A").textContent === "2 files" && lrow("Kit A").children[0].textContent === "▾" &&
          lrow("Kit A").children[1].className === "pix dir", "a folder row counts its files: " + lstate("Kit A").textContent);
    check(elements.upload.textContent === "Upload 2 files → /", "Upload counts the files inside: " + elements.upload.textContent);

    /* its triangle closes and opens it; a double-click too */
    lrow("Kit A").children[0].onclick(halt);
    check(JSON.stringify(tree()) === '["Kit A"]' && lrow("Kit A").children[0].textContent === "▸", "closed: " + tree());
    lrow("Kit A").ondblclick();
    check(tree().length === 4, "a double-click opens it again: " + tree());

    /* files and a folder dropped from the computer onto a folder of the list go into it */
    lrow("Kit A").ondragover(Object.assign({ dataTransfer: { types: ["Files"] } }, halt));
    check(/ into$/.test(lrow("Kit A").className), "the folder shows where they would land");
    lrow("Kit A").ondrop(Object.assign({ dataTransfer: fromDisk(dirEntry("Hats", [fileEntry("HH 01.wav", 0x52), fileEntry("notes.txt", 0)]),
                                                               fileEntry("Clap.wav", 0x52), dirEntry("Docs", [fileEntry("a.pdf", 0)])) }, halt));
    await until(() => !!lrow("Clap"), "the drop is read");
    check(JSON.stringify(tree()) === JSON.stringify(["Kit A", "  Hats", "    HH 01", "  Snares", "    SD 01", "  BD 01", "  Clap"]),
          "Hats and Clap are inside Kit A, Docs (no audio) is left out: " + tree());
    check(elements.status.textContent === "2 files left out: not audio.", "the two others are counted: " + elements.status.textContent);

    /* New folder in the list, named at once; rows dragged onto it move into it */
    key("files", "Escape");
    elements["src-mkdir"].onclick();
    check(!!files().find(li => li.children[2].children[0].className === "rename" && li.children[2].children[0].value === "New folder"),
          "New folder asks for its name");
    const box = files().find(li => li.children[2].children[0].className === "rename").children[2].children[0];
    box.value = "Loops";
    box.onkeydown({ key: "Enter" });
    check(!!lrow("Loops") && lstate("Loops").textContent === "empty", "the folder is named: " + tree());
    check(lrow("Loops").children[0].textContent === "", "an empty folder has no triangle");
    dragRow("Clap");
    lrow("Loops").ondrop(internal());
    check(JSON.stringify(tree()) === JSON.stringify(["Kit A", "  Hats", "    HH 01", "  Snares", "    SD 01", "  BD 01", "Loops", "  Clap"]),
          "Clap moved into Loops: " + tree());
    dragRow("Kit A");
    lrow("Snares").ondrop(internal());
    check(lrow("Kit A").style.paddingLeft === "6px" && lrow("Snares").style.paddingLeft === "24px", "a folder never goes into its own folder");
    /* the selection moves together: ⌘-click two rows, drag one of them */
    lrow("HH 01").onclick({});
    lrow("BD 01").onclick({ metaKey: true });
    dragRow("BD 01");
    lrow("Loops").ondrop(internal());
    check(JSON.stringify(tree()) === JSON.stringify(["Kit A", "  Hats", "  Snares", "    SD 01", "Loops", "  BD 01", "  Clap", "  HH 01"]),
          "both selected rows moved: " + tree());
    /* Enter renames the one row selected; a folder is taken off the list with what is in it */
    lrow("Hats").onclick({});
    key("files", "Enter");
    const hats = files().find(li => li.children[2].children[0].className === "rename").children[2].children[0];
    check(hats.value === "Hats", "Enter opens the name of the selected row");
    hats.onkeydown({ key: "Escape" });
    lrow("Hats").onclick({});
    elements["remove-sel"].onclick();
    check(!lrow("Hats") && JSON.stringify(tree()) === JSON.stringify(["Kit A", "  Snares", "    SD 01", "Loops", "  BD 01", "  Clap", "  HH 01"]),
          "the empty Hats is gone: " + tree());

    /* Upload: the folders are made on the Cycles, each before what is in it */
    newFolder("Lib");
    await until(() => shown() === "/Lib", "the Cycles' folder Lib is made and open");
    check(elements.upload.textContent === "Upload 4 files → /Lib", "Upload: " + elements.upload.textContent);
    from = log.length;
    elements.upload.onclick();
    check(!elements.overall.hidden, "the bar shows while it uploads");
    await uploaded(4);
    check(elements.status.textContent === "4 of 4 uploaded to /Lib." && elements.status.className === "status ok",
          "all four: " + elements.status.textContent);
    check(elements.overall.hidden && elements["overall-fill"].style.width === "100%", "the bar went to its last file and hides: " +
          elements["overall-fill"].style.width);
    check(["/Lib/Kit A", "/Lib/Kit A/Snares", "/Lib/Loops"].every(p => drive.has(p) && drive.get(p).folder) &&
          ["/Lib/Kit A/Snares/SD 01", "/Lib/Loops/BD 01", "/Lib/Loops/Clap", "/Lib/Loops/HH 01"].every(p => drive.has(p) && !drive.get(p).folder),
          "the tree is on the Cycles: " + under("/Lib"));
    const order = log.slice(from).filter(t => t === E.TYPE.CREATE_DIR || t === E.TYPE.OPEN_WRITE);
    check(JSON.stringify(order) === JSON.stringify([E.TYPE.CREATE_DIR, E.TYPE.CREATE_DIR, E.TYPE.OPEN_WRITE, E.TYPE.CREATE_DIR,
                                                    E.TYPE.OPEN_WRITE, E.TYPE.OPEN_WRITE, E.TYPE.OPEN_WRITE]),
          "Kit A, Snares, SD 01, Loops, its three files: " + order.map(t => "0x" + t.toString(16)));
    check(lstate("Kit A").textContent === "1 file" && lstate("Kit A").className === "state ok" && /^done/.test(lstate("Clap").textContent),
          "the folder rows say they are through: " + lstate("Kit A").textContent);
    check(JSON.stringify(folderNames()) === '["Kit A","Loops"]', "the Cycles' side shows them: " + folderNames());
    check(elements.upload.disabled && elements.upload.textContent === "Upload → /Lib", "nothing left to upload");

    /* a row of the list dragged onto a folder on the Cycles' side is uploaded there */
    add(file("Ride.wav", 0x52));
    dragRow("Ride");
    row("Loops").ondragover(internal());
    check(/ into$/.test(row("Loops").className), "the Cycles' folder shows where it would land");
    row("Loops").ondrop(internal());
    await until(() => elements.status.textContent === "1 of 1 uploaded to /Lib/Loops.", "it goes into Loops: " + elements.status.textContent);
    check(drive.has("/Lib/Loops/Ride") && shown() === "/Lib", "Ride is in /Lib/Loops; the page stays in /Lib");
    check(row("Kit A").className.indexOf("into") < 0 && row("Loops").className.indexOf("into") < 0, "no row stays marked");

    /* files from the computer dropped on the Cycles' side join the list and go straight into the folder shown */
    elements.dst.ondrop(Object.assign({ dataTransfer: fromDisk(fileEntry("Tom.wav", 0x52), fileEntry("x.txt", 0)) }, halt));
    await until(() => elements.status.textContent === "1 of 1 uploaded to /Lib.", "Tom goes into /Lib: " + elements.status.textContent);
    check(drive.has("/Lib/Tom") && /^done/.test(lstate("Tom").textContent), "and is on the list as done");

    /* a sample with the name of a folder to make: the folder fails, and what was to go in it */
    drive.set("/Lib/Kit B", { folder: false, data: new Uint8Array(80) });
    elements["chooser-dir"].files = [rel("Kit B/K1.wav", 0x52)];
    key("files", "Escape");
    elements["chooser-dir"].onchange();
    elements.upload.onclick();
    await until(() => elements.status.textContent === "0 of 1 uploaded to /Lib.", "nothing went: " + elements.status.textContent);
    check(elements.status.className === "status bad", "said as a problem");
    check(lstate("Kit B").textContent === "failed" && lrow("Kit B").children[2].children[1].textContent ===
          "A sample named Kit B is already in /Lib.", "the folder says why");
    check(lstate("K1").textContent === "failed" && lrow("K1").children[2].children[1].textContent ===
          "Its folder could not be made on the Cycles.", "its file too");

    /* the Cycles stops answering: Ask again says so, the chip too, and the ports stay in view to pick others */
    silent = true;
    elements.retry.onclick();
    await until(() => /does not answer/.test(elements.status.textContent), "a silent Cycles is told: " + elements.status.textContent);
    check(/Close Elektron Transfer if it is open/.test(elements.status.textContent), "and pointed at Transfer: " + elements.status.textContent);
    check(elements.status.className === "status bad" && elements["chip-text"].textContent === "No answer" &&
          elements.chip.className === "chip off", "the chip says No answer: " + elements["chip-text"].textContent);
    check(!elements.ports.hidden, "the ports stay in view");
    check(/Connect the Cycles/.test(elements.folder.innerHTML) && elements.upload.disabled && elements["del-sel"].disabled,
          "nothing to act on");

    if (failures) {
        console.log(failures + " check(s) failed");
        process.exit(1);
    }
    console.log("all page tests passed");
})();
