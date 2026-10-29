/* Browser smoke test (jsdom) of model27's web flasher: loads the real page and its scripts, fakes Web MIDI, and walks
 * through the 4 steps (choose, OS file, connect over USB, flash). The fake Model:Cycles answers the Elektron Transfer
 * protocol (fast method) with its own decoder and zlib's CRC, and keeps every byte it is sent, to compare with the
 * firmware. Only the page's own files are loaded (the web font is skipped): no network is needed beyond npm.
 * Run through tools/webflash_smoke.sh (installs jsdom in a temp folder).
 *   node tools/webflash_smoke.js <synth_dir> [model-cycles_OS1.13.syx] [model-samples_OS1.13.syx]
 * The optional official files are told apart by their names. The Model:Cycles OS checks each combination of the
 * REF_MAINOS sample against its reference hash, and each mod against REF_MODS (app.js, notes/49); with the
 * Model:Samples OS, the "Samples OS" tab and the Mods tab on a Model:Samples are checked end to end
 * (REF_SAMPLES_ON_CYCLES, tools/mods_for_samples.py). model27 offers two cards, SAMPLE and Control All Config
 * (OFFERED in tools/gen_flasher_tweaks.py); SAMPLE is a machine card, composed in the page from its package
 * (composer.js, notes/61). The checks of Modded-Cycles' other cards are in this file's history. */
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");
const { pathToFileURL } = require("url");
const { JSDOM, VirtualConsole, requestInterceptor } = require("jsdom");

// The page's own files only: the web font (Google Fonts) and anything else remote gets an empty answer, so the test
// needs no network and a blocked request is not reported as a JS error (jsdom 29: tools/webflash_smoke.sh pins it).
const LOCAL_ONLY = { interceptors: [requestInterceptor((request, { element }) => (request.url.startsWith("file:") ? undefined
  : new Response("", { headers: { "Content-Type": element && element.localName === "link" ? "text/css" : "text/plain" } })))] };

const FLASH = path.join(__dirname, "..", "docs", "flasher");
const SYNTH = process.argv[2];
const REAL = process.argv.slice(3);
const REAL_ST = REAL.find((f) => /syntakt/i.test(path.basename(f)));
const ST_NAME = REAL_ST ? path.basename(REAL_ST) : "Syntakt_OS1.42.syx";
const ST_VERSION = (/OS(\d+\.\d+)/.exec(ST_NAME) || [])[1];   // "1.42" or "1.41": both official, same engines
const REAL_SMP = REAL.find((f) => /samples/i.test(path.basename(f)));
const REAL_OS = REAL.find((f) => f !== REAL_ST && f !== REAL_SMP);
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
// SMOKE_SHARD=k/n (tools/webflash_smoke.sh with SMOKE_JOBS=n): part k of the combinations of section 6; the other
// sections run in part 0 only; each part writes what it built to SMOKE_SEEN and the script checks the coverage
const [SHARD_K, SHARD_N] = (process.env.SMOKE_SHARD || "0/1").split("/").map(Number);
const MAIN = SHARD_K === 0;

// Tick exactly the given Syntakt engines (the card is turned on first; ticking before unticking
// never empties the list, which would turn the card off).
async function pickEngines(doc, codes) {
  if (!doc.getElementById("feat-syntakt").checked) { doc.getElementById("feat-syntakt").click(); await wait(5); }
  for (const want of [true, false]) {
    for (const cb of [...doc.querySelectorAll('input[name="eng-syntakt"]')].map((x) => x.value)) {
      const box = doc.getElementById("eng-" + cb);                 // re-query: the cards are re-rendered
      if (codes.includes(cb) === want && box.checked !== want) { box.click(); await wait(5); }
    }
  }
}

// The cards to tick for a REF_MAINOS key (tweak ids joined with "+"): tweak id -> its card and the choice in it (a variant,
// or the Syntakt engines of a combination, alone or with Model-TG), including the tweak a card takes with another one ("with").
function cardsOf(w, key) {
  const own = {}, feats = w.MC_TWEAKS.features;
  const cardsOfKey = (k) => k.split("+").map((id) => feats.find((x) => x.id === id));
  for (const f of feats) {
    if (f.engines) for (const c of f.combos) {
      own[c.id] = own[c.tg] = { f, engines: c.engines };
      for (const k of f.joined || [])          // MACRO, ACID with the engines (notes/50, notes/54 §11): all the cards
        own[c[k].id] = own[c[k].tg] = { f, engines: c.engines, also: cardsOfKey(k) };
    }
    else if (f.package) own[f.package] = { f };   // a machine card (notes/61): a composed key names each package
    else {
      for (const v of f.variants) own[v.id] = { f, variant: v.id };
      for (const [k, v] of Object.entries(f.versions || {}))     // MACRO with ACID: both cards
        own[v.id] = own[v.tg] = { f, variant: f.variants[0].id, also: cardsOfKey(k) };
    }
  }
  for (const f of feats)
    for (const alt of Object.values(f.with || {})) if (!own[alt]) own[alt] = f.engines ? { f } : { f, variant: f.variants[0].id };
  const sel = new Map();
  for (const id of key.split("+")) {
    sel.set(own[id].f.id, own[id]);
    for (const g of own[id].also || []) sel.set(g.id, { f: g, variant: g.variants[0].id });
  }
  return sel;
}

// Tick exactly the cards of a key (off first: a card held by another one is locked until that one goes off), then the
// variant or the engines of each, and wait for the build.
async function tickKey(w, doc, key) {
  const sel = cardsOf(w, key);
  for (let round = 0; round < 3; round++) {
    for (const want of [false, true])
      for (const f of w.MC_TWEAKS.features) {
        const cb = doc.getElementById("feat-" + f.id);       // re-query: the cards are re-rendered
        if (sel.has(f.id) === want && cb.checked !== want && !cb.disabled) { cb.click(); await wait(5); }
      }
    for (const [id, o] of sel) {
      if (o.engines) await pickEngines(doc, o.engines);
      else if (o.variant) {
        const r = doc.querySelector(`input[name="var-${id}"][value="${o.variant}"]`);
        if (r && !r.checked) { r.click(); await wait(5); }
      }
    }
    await settle(w);
    if (w.MCFlasherApp.state.buildKey === key) return;
  }
}

// Elektron Transfer protocol, written apart from flasher.js (Elektroid's packing: a byte with the
// high bits of the next 7, first one in bit 6).
const XHEAD = [0xf0, 0x00, 0x20, 0x3c, 0x10, 0x00];
function unpack(src) {
  const out = [];
  for (let i = 0; i < src.length; i += 8)
    for (let k = 1; k < 8 && i + k < src.length; k++) out.push(src[i + k] | ((src[i] << k) & 0x80));
  return Uint8Array.from(out);
}
function pack(src) {
  const out = [];
  for (let j = 0; j < src.length; j += 7) {
    const grp = Array.from(src.slice(j, j + 7));
    out.push(grp.reduce((hi, b, k) => hi | ((b >> 7) << (6 - k)), 0), ...grp.map((b) => b & 0x7f));
  }
  return Uint8Array.from([...XHEAD, ...out, 0xf7]);
}
const be = (m, o) => ((m[o] << 24) | (m[o + 1] << 16) | (m[o + 2] << 8) | m[o + 3]) >>> 0;
const cstr = (str) => [...Buffer.from(str, "latin1"), 0];

// A Model:Cycles on USB: answers ping, version, OS upgrade start and blocks like the real one
// (src/connectors/elektron.c), and records what it receives.
function fakeDevice(opts, reply) {
  const dev = Object.assign({ id: 27, name: "Model Cycles", version: "1.13", startStatus: 0, writeError: -1, silent: false,
    pings: 0, starts: 0, blocks: 0, received: null, size: 0, next: 0, bad: [] }, opts);
  dev.handle = (d) => {
    if (d.length < 8 || XHEAD.some((b, k) => d[k] !== b)) return;           // not for the Transfer protocol
    const m = unpack(d.subarray(6, d.length - 1));
    const head = [0, 0, m[0], m[1], m[4] | 0x80];
    let r = null;
    if (m[4] === 0x01) { dev.pings++; r = [...head, dev.id, 1, 0, ...cstr(dev.name)]; }
    else if (m[4] === 0x02) r = [...head, 0, 0, 0, 0, 0, ...cstr(dev.version)];
    else if (m[4] === 0x50) {
      dev.starts++;
      dev.size = m[5] | (m[6] << 8) | (m[7] << 16) | (m[8] << 24);      // little-endian, as Elektroid's memcpy
      if (Buffer.from(m.subarray(9, 16)).toString("latin1") !== "sysex\0\x01") dev.bad.push("start tail");
      dev.received = new Uint8Array(dev.size); dev.next = 0; dev.blocks = 0;
      r = [...head, dev.startStatus, ...(dev.startStatus ? cstr("No space") : [0])];
    } else if (m[4] === 0x51) {
      const crc = be(m, 5), len = be(m, 9), off = be(m, 13), data = m.subarray(17);
      if (data.length !== len || off !== dev.next || len > 0x800 || crc !== zlib.crc32(data, 0xffffffff) >>> 0)
        dev.bad.push(`block ${dev.blocks}: len ${len}/${data.length}, offset ${off}/${dev.next}`);
      dev.received.set(data, off);
      dev.next = off + len;
      const op = dev.blocks === dev.writeError ? 2 : dev.next >= dev.size ? 1 : 0;
      dev.blocks++;
      r = [...head, 0, 0, 0, 0, op];
    }
    if (r && !dev.silent) setTimeout(() => reply(pack(r)), 1);
  };
  return dev;
}

async function load({ midi = true, ports = true, inputs = true, busy = false, secure = true, lang = "en", devName = "Elektron Model:Cycles", device = {} } = {}) {
  const errors = [];
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => errors.push("jsdomError: " + ((e.detail && e.detail.message) || e.message || e)));
  const sent = [];
  const listeners = new Set();
  const dev = fakeDevice(device, (data) => listeners.forEach((f) => f({ data })));
  let access = null, devOut = null, devIn = null;
  const html = fs.readFileSync(path.join(FLASH, "index.html"), "utf8");
  const dom = new JSDOM(html, {
    url: pathToFileURL(path.join(FLASH, "index.html")).href,
    runScripts: "dangerously", resources: LOCAL_ONLY, virtualConsole: vc,
    beforeParse(window) {
      Object.defineProperty(window, "isSecureContext", { value: secure, configurable: true });
      Object.defineProperty(window.navigator, "language", { value: lang, configurable: true });
      window.addEventListener("error", (e) => errors.push("window.onerror: " + ((e.error && e.error.message) || e.message)));
      window.addEventListener("unhandledrejection", (e) => errors.push("unhandled: " + ((e.reason && e.reason.message) || e.reason)));
      if (midi) {
        const outputs = new Map(), ins = new Map();
        if (ports) {
          devOut = { id: "dev", name: devName, manufacturer: "Elektron", state: "connected",
            send: (d) => { sent.push(d.length); dev.handle(d); }, open: () => Promise.resolve(), close: () => Promise.resolve() };
          outputs.set("dev", devOut);
          outputs.set("iface", { id: "iface", name: "USB MIDI Interface", manufacturer: "Acme", send: (d) => sent.push(d.length) });
          devIn = { id: "dev-in", name: devName, manufacturer: "Elektron", state: "connected",
            open: () => (busy ? Promise.reject(new Error("InvalidAccessError: port in use")) : Promise.resolve()),
            close: () => Promise.resolve(), addEventListener: (t, f) => listeners.add(f), removeEventListener: (t, f) => listeners.delete(f) };
          if (inputs) ins.set("dev-in", devIn);
        }
        access = { outputs, inputs: ins, onstatechange: null };
        window.navigator.requestMIDIAccess = () => Promise.resolve(access);
      }
      window.URL.createObjectURL = () => "blob:x";
      window.URL.revokeObjectURL = () => {};
    },
  });
  await wait(300);
  // on a busy machine the scripts can take more than 300 ms to load
  for (let i = 0; i < 200 && !(dom.window.MCFlasherApp && dom.window.MC_TWEAKS && dom.window.MCBuilder); i++) await wait(50);
  return { dom, w: dom.window, doc: dom.window.document, errors, sent, dev, listeners,
    access: () => access, devOut: () => devOut, devIn: () => devIn };
}

// No pause between blocks (50 ms on the real machine): a 2.5 MB file goes through in a few seconds.
function noRest(w) {
  const orig = w.MCFlasher.upgradeFast;
  w.MCFlasher.upgradeFast = (session, raw, opts) => orig(session, raw, Object.assign({}, opts, { restMs: 0 }));
}
const same = (a, b) => !!a && !!b && a.length === b.length && Buffer.compare(Buffer.from(a), Buffer.from(b)) === 0;
async function untilSent(w, ms = 60000) {
  for (let i = 0; i < ms / 50 && w.MCFlasherApp.state.sending; i++) await wait(50);
}

const text = (doc, id) => doc.getElementById(id).textContent;
// text of the elements a selector picks (the Details drawers are always in the page: scope what a check reads)
const textOf = (doc, sel) => [...doc.querySelectorAll(sel)].map((e) => e.textContent).join(" ");
async function settle(w) {
  for (let i = 0; i < 200 && w.MCFlasherApp.state.building; i++) await wait(50);
  await wait(60);
}

async function main() {
  let fail = 0;
  const check = (cond, msg) => { console.log((cond ? "  ok  " : "  FAIL ") + msg); if (!cond) fail++; };

  // 1. Page loads cleanly, everything is wired; model27's four cards
  if (MAIN) {
    const { w, doc, errors } = await load();
    check(errors.length === 0, "loads without JS error " + (errors.length ? JSON.stringify(errors) : ""));
    check(typeof w.MCBuilder === "object" && typeof w.MCComposer === "object" && typeof w.MCFlasher === "object",
      "MCBuilder + MCComposer + MCFlasher present");
    const ids = w.MC_TWEAKS.tweaks.map((x) => x.id), cards = w.MC_TWEAKS.features;
    const smp = cards.find((f) => f.id === "sampler") || {}, dd = cards.find((f) => f.id === "digidelay") || {};
    const pots = cards.find((f) => f.id === "pots") || {};
    check(ids.join() === "control-all-config" && cards.map((f) => f.id).join() === "control-all-config,sampler,digidelay,pots"
      && smp.package === "sampler" && !smp.variants && dd.package === "digidelay" && !dd.variants
      && pots.package === "pots" && !pots.variants
      && Object.keys(w.MC_TWEAKS.packages).join() === "sampler,digidelay,pots"
      && Object.keys(w.MC_TWEAKS.parts || {}).join() === "shortcuts,dispatch,fxslot"
      && w.MC_TWEAKS.registrar && w.MC_TWEAKS.registrar.schema === "model27-registrar-frame/0.1"
      && !cards.some((f) => f.engines || f.needs) && !w.MC_TWEAKS.tweaks.some((x) => x.append && x.append.syntakt),
      "MC_TWEAKS: model27's four cards, Control All Config (its tweak), SAMPLE (a machine card), Digital Delay and POTS " +
      "(effect cards): their packages, the registrar's frame and the parts, composed in the page, nothing that needs the " +
      "Syntakt OS: " + ids.join());
    check(/build \d{4}-/.test(text(doc, "build-stamp")), "version stamp shown");
    const srcs = [...doc.querySelectorAll("script[src]")].map((x) => x.getAttribute("src"));
    check(["builder.js", "composer.js", "tweaks.js", "flasher.js", "app.js"].every((f) => srcs.some((x) => x.startsWith(f + "?")))
      && srcs.every((x) => x.endsWith("?v=" + w.MC_BUILD)), "scripts loaded with ?v=<build> (no stale cache): " + srcs.join());
    check(doc.getElementById("compat").hidden, "no compatibility banner in a good browser");
    // display order: by section (Sounds & machines, then Live playing), FEATURES order inside a section; the build
    // keeps FEATURES order (checked in 1b)
    const feats = [...doc.querySelectorAll("#features input[type=checkbox]")].map((c) => c.id);
    check(feats.join() === "feat-sampler,feat-digidelay,feat-pots,feat-control-all-config", "4 feature rows, by section: " + JSON.stringify(feats));
    check(cards.every((f) => doc.querySelector(`#cat-${f.cat || "other"} #mod-${f.id} #feat-${f.id}`)),
      "every feature has a row in its section (cat)");
    const tagOfFeat = (f) => (f.status === "tested" ? "Tested" : "Experimental");
    const tags = cards.map((f) => f.id + ":" + doc.querySelector(`label[for=feat-${f.id}] .tag`).textContent);
    check(tags.join() === cards.map((f) => f.id + ":" + tagOfFeat(f)).join(), "rows tagged as tested or not: " + tags.join());
    check(doc.getElementById("drop3-wrap").hidden, "no Syntakt drop zone: no card needs the Syntakt OS");
    const credits = [...doc.querySelectorAll("#features .credit a")].map((a) => a.href);
    const creditOf = (id) => [...doc.querySelectorAll(`label[for=feat-${id}] .credit a`)].map((a) => a.href);
    check(credits.length === 6
      && creditOf("sampler")[0] === "https://github.com/durchgemacht/cycles-one-shot" && /\/LICENSE-One-Shot\.txt$/.test(creditOf("sampler")[1])
      && creditOf("digidelay")[0] === "https://github.com/gialloinfuso/PPPCCC-Model-Cycles-1.13-Mods"
      && /\/LICENSE-PPPCCC\.txt$/.test(creditOf("digidelay")[1])
      && creditOf("control-all-config")[0] === "https://github.com/durchgemacht/cycles-control-all-config"
      && /\/LICENSE-Control-All-Config\.txt$/.test(creditOf("control-all-config")[1])
      && !creditOf("pots").length && !doc.querySelector("label[for=feat-pots] .credit"),
      "each row credits its author, with a link to the MIT license of the code it carries; POTS, model27's own, none: " +
      JSON.stringify(credits));
    const list = [...doc.querySelectorAll("#credits-list a")].map((a) => a.textContent);
    check(list.join() === "18nelli18/Modded-Cycles,scottmetoyer/ms-multi-output,drumkilla/elektron-model-tweaks,pichenettes/eurorack,RobinSchmidt/Open303,TinyGregAudio/Model-TG,gialloinfuso/PPPCCC-Model-Cycles-1.13-Mods,mischa85/elektron-firmware-tool,dagargo/elektroid,mxldyn/octamax",
      "credits section lists Modded-Cycles first, then the 9 repositories it builds on");
    const lic = [...doc.querySelectorAll("#credits a")].map((a) => a.href).filter((h) => /LICENSE|NOTICES/.test(h));
    check(lic.join() === "https://github.com/18nelli18/Modded-Cycles/blob/main/LICENSE,https://github.com/durchgemacht/model27/blob/main/THIRD-PARTY-NOTICES.md",
      "credits section links Modded-Cycles' MIT license and model27's third-party notices: " + JSON.stringify(lic));
    const box = (id) => doc.getElementById(id);
    const chosen = () => w.MCFlasherApp.chosenTweaks().map((x) => x.id).join();
    // the two cards go together: no exclusion between them, both stay ticked, FEATURES order in the build
    box("feat-sampler").click(); await wait(5);
    const smpAlone = chosen();
    box("feat-control-all-config").click(); await wait(5);
    const both = chosen();
    const bothOn = box("feat-sampler").checked && box("feat-control-all-config").checked && !doc.querySelector("#features .say.clash");
    box("feat-sampler").click(); await wait(5);
    const cacAlone = chosen();
    box("feat-control-all-config").click(); await wait(5);
    check(smpAlone === "sampler" && both === "control-all-config,sampler" && bothOn && cacAlone === "control-all-config" && !chosen().length
      && doc.querySelector('#features a[href$="#sampler"]') && doc.querySelector('#features a[href$="#control-all"]'),
      `SAMPLE alone ${smpAlone}; with Control All Config ${both}, both ticked, no clash; Control All Config alone ${cacAlone}; guide links`);
    // Digital Delay: an effect card, composed with the machine cards into one tweak, at the place of the first of them
    box("feat-digidelay").click(); await wait(5);
    const ddAlone = chosen();
    box("feat-sampler").click(); await wait(5);
    const ddSmp = chosen();
    box("feat-control-all-config").click(); await wait(5);
    const ddAll = chosen();
    const allOn = ["sampler", "digidelay", "control-all-config"].every((i) => box("feat-" + i).checked)
      && !doc.querySelector("#features .say.clash");
    for (const i of ["digidelay", "sampler", "control-all-config"]) { box("feat-" + i).click(); await wait(5); }
    check(ddAlone === "digidelay" && ddSmp === "sampler+digidelay" && ddAll === "control-all-config,sampler+digidelay"
      && allOn && !chosen().length && doc.querySelector('#features a[href$="#digital-delay"]')
      && doc.querySelectorAll('input[name="var-digidelay"]').length === 0,
      `Digital Delay alone ${ddAlone}; with SAMPLE ${ddSmp}, one composed tweak; with Control All Config too ${ddAll}, all ` +
      "ticked, no clash; no sub-choice; its guide link");
    // POTS: a second effect of the same slot, composed with Digital and the machines into one tweak
    box("feat-pots").click(); await wait(5);
    const potsAlone = chosen();
    box("feat-digidelay").click(); await wait(5);
    const potsDd = chosen();
    box("feat-sampler").click(); await wait(5);
    const potsSmp = chosen();
    box("feat-control-all-config").click(); await wait(5);
    const potsAll = chosen();
    const fourOn = ["sampler", "digidelay", "pots", "control-all-config"].every((i) => box("feat-" + i).checked)
      && !doc.querySelector("#features .say.clash");
    for (const i of ["pots", "digidelay", "sampler", "control-all-config"]) { box("feat-" + i).click(); await wait(5); }
    check(potsAlone === "pots" && potsDd === "digidelay+pots" && potsSmp === "sampler+digidelay+pots"
      && potsAll === "control-all-config,sampler+digidelay+pots" && fourOn && !chosen().length
      && doc.querySelector('#features a[href$="#pots"]') && doc.querySelectorAll('input[name="var-pots"]').length === 0
      && /Tested/.test(doc.querySelector("label[for=feat-pots] .tag").textContent),
      `POTS alone ${potsAlone}; with Digital ${potsDd}, one composed tweak; with SAMPLE ${potsSmp}; with Control All ` +
      `Config too ${potsAll}, all ticked, no clash; no sub-choice; its guide link; tagged Tested`);
    box("feat-sampler").click(); await wait(30);
    check(doc.querySelectorAll('input[name="var-sampler"]').length === 0, "SAMPLE: a machine card, no sub-choice");
    check(!!doc.getElementById("tab-samples") && doc.getElementById("panel-samples").hidden && doc.getElementById("drop2-wrap").hidden,
      "Samples OS tab present, its panel and second drop zone hidden in Mods");
    check(/Load your official OS file/.test(text(doc, "missing")), "flash button says what is missing: " + text(doc, "missing"));
    check(doc.getElementById("flash").disabled, "flash button disabled without a file");

    // language switch
    doc.querySelector('.lang button[data-lang="fr"]').click();
    await wait(20);
    check(/Que voulez-vous installer/.test(text(doc, "h1s")) && doc.documentElement.lang === "fr", "FR switch translates the page");
    check(/Control All : choix des pistes/.test(text(doc, "features")) && /SAMPLE machine \(Cycles One-Shot\)/.test(text(doc, "features"))
      && /Digital Delay \(effet\)/.test(text(doc, "features")) && /POTS \(effet\)/.test(text(doc, "features"))
      && /par durchgemacht/.test(text(doc, "features")) && /Testé/.test(text(doc, "features"))
      && doc.querySelector('#features a[href$="#control-all"]') && doc.querySelector('#features a[href$="#sampler"]'),
      "FR switch translates the cards (SAMPLE's texts are in English only), their credits and tags, with their guide links");
    check(/Crédits/.test(text(doc, "credits")) && /boîte à outils/.test(text(doc, "credits")) && /publié sous licence MIT/.test(text(doc, "credits")),
      "FR switch translates the credits section");
    box("feat-sampler").click(); await wait(5);
    doc.querySelector('.lang button[data-lang="en"]').click();
    await wait(20);

    // Connection: USB only, fast method by default, classic as the fallback
    check(doc.querySelectorAll('input[name="method"]').length === 0 && !doc.getElementById("howto-midi")
      && !/MIDI IN|READY TO RECEIVE|TRIG 4/.test(text(doc, "step-connect")), "no MIDI IN route in step 3");
    check(doc.getElementById("m-fast").getAttribute("aria-checked") === "true" && !doc.getElementById("howto-fast").hidden
      && doc.getElementById("howto-usb").hidden && /Close Elektron Transfer/.test(text(doc, "howto-fast"))
      && !/CONFIG › UPGRADE/.test(text(doc, "howto-fast")) && /about 30 seconds/.test(text(doc, "method-note")),
      "fast method by default: its steps (close Transfer, no menu to open)");
    doc.getElementById("allow").click();
    await wait(150);
    const sel = doc.getElementById("port");
    check(!sel.hidden && sel.value === "dev", "Allow MIDI -> Model:Cycles port preselected (" + sel.value + ")");
    check(/Model:Cycles found: OS 1\.13/.test(text(doc, "midi-status")) && doc.getElementById("step-connect").classList.contains("done"),
      "fast: the machine is asked who it is: " + text(doc, "midi-status").slice(0, 50));
    doc.getElementById("m-slow").click();
    await wait(20);
    check(/CONFIG › UPGRADE/.test(text(doc, "howto-usb")) && !doc.getElementById("howto-usb").hidden && doc.getElementById("howto-fast").hidden
      && /USB port is selected/.test(text(doc, "midi-status")) && /5 to 10 minutes/.test(text(doc, "method-note")),
      "classic method: CONFIG › UPGRADE steps, status: " + text(doc, "midi-status").slice(0, 50));
    sel.value = "iface";
    sel.dispatchEvent(new w.Event("change"));
    await wait(20);
    check(/pick the port named/i.test(text(doc, "midi-status")), "another port -> warning");
    doc.getElementById("m-fast").click();
    await wait(20);
    check(/pick the port named/i.test(text(doc, "midi-status")) && w.MCFlasherApp.state.dev.state === "noinput", "fast, another port (output only) -> warning");
    doc.querySelector('.lang button[data-lang="fr"]').click();
    await wait(20);
    check(/Rapide \(USB\)/.test(text(doc, "m-fast")) && /Fermez Elektron Transfer/.test(text(doc, "howto-fast")), "FR: method and steps translated");
    doc.querySelector('.lang button[data-lang="en"]').click();
    await wait(20);
  }

  // 1b. The mod picker: sections, build order, Details, folding, the selection bar, conflicts with Undo, focus,
  // search, French
  if (MAIN) {
    const { w, doc, errors } = await load();
    const app = w.MCFlasherApp;
    const feats = w.MC_TWEAKS.features;
    const box = (id) => doc.getElementById(id);
    const click = async (el) => { el.click(); await wait(5); };
    const ids = () => app.chosenTweaks().map((x) => x.id).join();
    const clearAll = async () => { const b = doc.querySelector("#mod-sel [data-clear]"); if (b) await click(b); };
    const sections = [...doc.querySelectorAll("#features section.grp")].map((g) => g.id.slice(4));
    check(sections.join() === app.CATS.filter((c) => feats.some((f) => (f.cat || "other") === c)).join() && !box("cat-other"),
      "sections in CATS order, no « Other mods » while every mod has a cat: " + sections.join());
    check([...doc.querySelectorAll("#cats a[data-cat]")].map((a) => a.dataset.cat).join() === sections.join()
      && doc.querySelector('#cats a[data-cat="live"]').getAttribute("href") === "#cat-live", "one chip per section, linking to it");
    // the build keeps FEATURES order whatever the display order
    await click(box("feat-sampler"));
    await click(box("feat-control-all-config"));
    check(ids() === "control-all-config,sampler", "build order unchanged (Control All Config ticked after SAMPLE): " + ids());
    check(/2 mods/.test(text(doc, "mod-live")) && doc.querySelector('#cats a[data-cat="sound"] .led.on')
      && doc.querySelector('#cats a[data-cat="live"] .led.on'), "screen readers hear the count; the LED of a section with a ticked mod lights");
    await click(box("feat-sampler"));
    check(!doc.querySelector('#cats a[data-cat="sound"] .led.on') && doc.querySelector('#cats a[data-cat="live"] .led.on'),
      "the LED of a section with no ticked mod is off");
    await clearAll();
    // a mod without a cat lands in « Other mods », at the end
    const cac = feats.find((f) => f.id === "control-all-config"), cacCat = cac.cat;
    delete cac.cat;
    app.applyLang("en");
    check(!!doc.querySelector("#cat-other #feat-control-all-config") && /Other mods/.test(textOf(doc, "#cat-other .grp-h"))
      && [...doc.querySelectorAll("#features section.grp")].pop().id === "cat-other", "a mod without cat goes to « Other mods », last");
    cac.cat = cacCat;
    app.applyLang("en");
    // Details: opens and closes, doesn't tick, holds the guide link
    await click(box("more-control-all-config"));
    const opened = !box("det-control-all-config").hidden && box("more-control-all-config").getAttribute("aria-expanded") === "true"
      && !box("feat-control-all-config").checked && !!doc.querySelector('#det-control-all-config a[href$="#control-all"]')
      && /Status/.test(text(doc, "det-control-all-config"));
    await click(box("more-control-all-config"));
    check(opened && box("det-control-all-config").hidden && box("more-control-all-config").getAttribute("aria-expanded") === "false",
      "Details opens the drawer (description, status, guide link) without ticking, and closes it");
    // folding a section; a folded section still names its ticked mods; its chip unfolds it
    await click(box("feat-control-all-config"));
    await click(box("grp-h-live"));
    const folded = box("grp-live").hidden && box("grp-h-live").getAttribute("aria-expanded") === "false"
      && /Control All/.test(textOf(doc, "#cat-live .grp-sel"));
    await click(doc.querySelector('#cats a[data-cat="live"]'));
    check(folded && !box("grp-live").hidden, "a folded section names its ticked mods, its chip unfolds it");
    await clearAll();
    // the selection bar
    check(/No mod ticked yet/.test(text(doc, "mod-sel")) && !doc.querySelector("#mod-sel .sel-next"), "selection bar, empty");
    await click(box("feat-control-all-config"));
    await click(box("feat-sampler"));
    const counts = textOf(doc, "#mod-sel .sel-c");
    check(/2 mods/.test(counts) && doc.querySelectorAll("#mod-sel .chip").length === 2
      && doc.querySelector("#mod-sel a.sel-next").getAttribute("href") === "#step-file", "selection bar: " + counts);
    await click(doc.querySelector('#mod-sel [data-off="sampler"]'));
    check(ids() === "control-all-config" && !box("feat-sampler").checked && doc.activeElement && doc.activeElement.dataset.off === "control-all-config",
      "× on a chip unticks the mod, the focus goes to the next ×");
    await clearAll();
    check(ids() === "" && /No mod ticked yet/.test(text(doc, "mod-sel")), "« Untick all » empties the selection");
    // notes/65 C4: a reason computed from the claims, said where no hand-written one exists. SAMPLE has its own (its
    // "clash"), so the page's function is asked directly, in English and in French
    const reasons = w.MC_TWEAKS.clash_reasons, hooks = w.MCFlasherApp, lang = hooks.state.lang;
    w.MC_TWEAKS.clash_reasons = { "control-all-config|sampler": [["combo", "TRACK + TRIG 1-6"]] };
    const whyEn = hooks.autoWhy({ id: "sampler" }, { id: "control-all-config" });
    hooks.state.lang = "fr";
    const whyFr = hooks.autoWhy({ id: "sampler" }, { id: "control-all-config" });
    hooks.state.lang = lang;
    w.MC_TWEAKS.clash_reasons = reasons;
    check(reasons && typeof reasons === "object" && !Array.isArray(reasons)
      && whyEn === "both use the buttons TRACK + TRIG 1-6" && whyFr === "les deux utilisent les touches TRACK + TRIG 1-6"
      && hooks.autoWhy({ id: "sampler" }, { id: "control-all-config" }) === "",
      `a computed reason where no hand-written one exists, in English and in French: ${whyEn} / ${whyFr}`);
    // a conflict injected between the two cards (they do go together), said before ticking, then Undo
    cac.excludes = ["sampler"];
    await click(box("feat-sampler"));
    const said = /Doesn't go with the mod “SAMPLE machine \(Cycles One-Shot\)”/.test(textOf(doc, "#mod-control-all-config .say.clash"))
      && /Doesn't go with/.test(textOf(doc, "#det-control-all-config")) && !doc.querySelector("#mod-sampler .say.clash");
    await click(box("feat-control-all-config"));
    const swapped = ids() === "control-all-config"
      && /The mod “SAMPLE machine \(Cycles One-Shot\)” was unticked/.test(textOf(doc, "#mod-control-all-config .say.swap"))
      && /The mod “SAMPLE machine \(Cycles One-Shot\)” was unticked/.test(textOf(doc, "#mod-sel .sel-msg"));
    await click(doc.querySelector("#mod-control-all-config [data-undo]"));
    check(said && swapped && ids() === "sampler" && !box("feat-control-all-config").checked && !doc.querySelector(".say.swap")
      && doc.activeElement && doc.activeElement.id === "feat-control-all-config",
      "conflict: said on the row before ticking; ticking unticks the other one, with Undo");
    delete cac.excludes;
    await clearAll();
    // focus stays on the checkbox just ticked, although the rows are rebuilt
    const cb = box("feat-control-all-config");
    cb.focus();
    await click(cb);
    check(box("feat-control-all-config") !== cb && doc.activeElement && doc.activeElement.id === "feat-control-all-config",
      "focus kept on the ticked box after the rebuild");
    await clearAll();
    // search: only from 20 mods
    check(feats.length < 20 && box("mod-find").hidden, `no search field with ${feats.length} mods (it appears from 20)`);
    // French
    app.applyLang("fr");
    await click(box("feat-control-all-config"));
    check(/Jeu en live/.test(textOf(doc, "#cat-live .grp-h")) && /Sons et machines/.test(textOf(doc, "#cat-sound .grp-h"))
      && /Votre sélection/.test(text(doc, "mod-sel")) && /Détails/.test(textOf(doc, "#more-control-all-config"))
      && /1 mod/.test(textOf(doc, "#mod-sel .sel-c")) && /Rubriques/.test(box("cats").getAttribute("aria-label")),
      "FR: sections, selection bar, Details");
    await clearAll();
    app.applyLang("en");
    check(errors.length === 0, "no JS error in the mod picker " + (errors.length ? JSON.stringify(errors) : ""));
  }


  // 1c. Fast method: a machine that doesn't answer (CONFIG > UPGRADE open, Transfer running), no MIDI input
  if (MAIN) {
    const { doc, dev } = await load({ device: { silent: true } });
    doc.getElementById("allow").click();
    await wait(1300);
    check(/doesn't answer/.test(text(doc, "midi-status")) && dev.pings === 1, "silent machine -> 'doesn't answer' after the 1 s handshake");
    dev.silent = false;
    doc.getElementById("refresh").click();
    await wait(150);
    check(/Model:Cycles found/.test(text(doc, "midi-status")) && dev.pings === 2, "Refresh asks again -> found");
  }
  if (MAIN) {
    const { doc } = await load({ busy: true });
    doc.getElementById("allow").click();
    await wait(100);
    check(/in use by another program: close Elektron Transfer/.test(text(doc, "midi-status")), "port held by another program -> says so");
  }
  if (MAIN) {
    const { doc } = await load({ inputs: false });
    doc.getElementById("allow").click();
    await wait(100);
    check(/no MIDI input from the Model:Cycles/.test(text(doc, "midi-status")), "no MIDI input -> says the fast method needs both directions");
  }

  // 1b. A Model:Cycles running the Samples OS shows up as "Model:Samples": it refuses a Model:Cycles firmware
  if (MAIN) {
    const { doc } = await load({ devName: "Elektron Model:Samples", device: { id: 25, name: "Model Samples" } });
    doc.getElementById("allow").click();
    await wait(150);
    check(doc.getElementById("port").value === "dev" && /Model:Samples found/.test(text(doc, "midi-status")),
      "fast: Model:Samples port -> identified: " + text(doc, "midi-status").slice(0, 60));
    doc.getElementById("m-slow").click();
    await wait(20);
    check(/refuses a Model:Cycles firmware/.test(text(doc, "midi-status")), "classic: Model:Samples port -> warning about the way back");
  }

  // 2. No Web MIDI (Firefox / Safari) -> clear banner
  if (MAIN) {
    const { doc } = await load({ midi: false });
    check(!doc.getElementById("compat").hidden && /Chrome, Edge or Opera/.test(text(doc, "compat")), "no Web MIDI -> banner");
    check(doc.getElementById("allow").disabled, "no Web MIDI -> Allow button disabled");
  }

  // 3. Insecure context (file://) -> clear banner
  if (MAIN) {
    const { doc } = await load({ secure: false });
    check(/secure page/i.test(text(doc, "compat")), "file:// -> banner: " + text(doc, "compat").slice(0, 40));
  }

  // 4. French browser -> French page
  if (MAIN) {
    const { doc } = await load({ lang: "fr-FR" });
    check(doc.documentElement.lang === "fr" && /Flasher Model:Cycles/.test(text(doc, "step-flash") + doc.title), "fr-FR browser -> French page");
  }

  // 5. Build from a synthetic OS, then flash, then stop
  if (SYNTH && MAIN) {
    const env5 = await load();
    const { w, doc, errors, sent } = env5;
    const raw = new Uint8Array(fs.readFileSync(path.join(SYNTH, "synth.syx")));
    const meta = JSON.parse(fs.readFileSync(path.join(SYNTH, "meta.json")));
    const app = w.MCFlasherApp;
    // the synthetic OS stands in for the official one
    w.MC_TWEAKS.device.section_sha256 = meta.section_sha256;
    w.MC_TWEAKS.device.stock_syx_sha256 = w.MCBuilder.hex(w.MCBuilder.sha256(raw));
    for (const k of Object.keys(app.REF_MAINOS)) delete app.REF_MAINOS[k];
    app.loadOs(raw, "synth.syx");
    await wait(20);
    check(/Official Model:Cycles OS 1.13 recognised/.test(text(doc, "file-status")), "OS file recognised as official");
    check(/Select a mod/.test(text(doc, "missing")), "no mod selected -> asks for one");
    doc.getElementById("feat-control-all-config").click();
    await settle(w);
    check(app.state.fw && app.state.fw.kind === "built" && /Firmware ready/.test(text(doc, "file-status")), "mod checked -> firmware built automatically");
    app.setMode("restore");
    await settle(w);
    check(app.state.fw && app.state.fw.kind === "stock", "Official firmware tab -> sends the OS unchanged");
    app.setMode("mods");
    await settle(w);
    check(app.state.fw && app.state.fw.kind === "built", "back to Mods -> built firmware again (cache)");

    doc.getElementById("allow").click();
    await wait(150);
    check(/Tick the box/.test(text(doc, "missing")), "asks for the confirmation box");
    doc.getElementById("ack").click();
    await wait(20);
    check(!doc.getElementById("flash").disabled, "flash button enabled when everything is ready");
    const fastMin = Math.max(1, Math.round(w.MCFlasher.fastSeconds(app.state.fw.raw) / 60));   // 2.5 MB synthetic file: 2 min
    check(text(doc, "summary").endsWith(`via Elektron Model:Cycles · about ${fastMin} min`) && fastMin <= 2 && /confirm on its screen/.test(text(doc, "missing")),
      "fast summary: " + text(doc, "summary"));
    const dl = doc.getElementById("download");
    check(!doc.getElementById("alt").hidden && dl.getAttribute("download") === app.state.fw.name && /Elektron Transfer/.test(text(doc, "alt")),
      "step 4 offers the .syx for Elektron Transfer: " + dl.getAttribute("download"));

    // fast: stop during the transfer (real 50 ms pause between blocks)
    const { dev } = env5;
    doc.getElementById("flash").click();
    await wait(400);
    check(!doc.getElementById("stop").hidden && /Flashing/.test(text(doc, "flash")) && dev.starts === 1 && dev.blocks > 1
      && doc.getElementById("m-slow").disabled, `fast transfer running: ${dev.blocks} blocks acknowledged, method locked`);
    doc.getElementById("stop").click();
    await untilSent(w);
    check(app.state.finished === "stopped" && /Stopped before the end/.test(text(doc, "result")) && dev.next < dev.size,
      "fast: Stop -> clear message, the machine didn't get the whole file");

    // fast: full transfer, byte for byte, then the machine restarts
    noRest(w);
    const fw5 = app.state.fw.raw;
    doc.getElementById("flash").click();
    await untilSent(w);
    check(app.state.finished === "ok" && same(dev.received, fw5) && dev.bad.length === 0 && dev.starts === 2
      && dev.blocks === Math.ceil(fw5.length / 0x800),
      `fast: the machine received the whole .syx, byte for byte, CRC checked (${dev.blocks} blocks) ` + dev.bad.slice(0, 2).join("; "));
    check(/Firmware sent/.test(text(doc, "result")) && /confirm the update on the Model:Cycles screen/.test(text(doc, "after")),
      "fast: success -> confirm on the machine");
    const out5 = env5.devOut(), in5 = env5.devIn();
    out5.state = in5.state = "disconnected";
    env5.access().onstatechange({ port: out5 });
    await wait(20);
    check(/writing the firmware and restarting/.test(text(doc, "after")), "machine gone -> 'writing and restarting'");
    out5.state = in5.state = "connected";
    dev.version = "1.13B";
    env5.access().onstatechange({ port: out5 });
    await wait(2800);
    check(/is back: Model:Cycles OS 1\.13B/.test(text(doc, "after")), "machine back -> asked again: " + text(doc, "after"));

    // fast: refusals
    dev.startStatus = 1;
    doc.getElementById("flash").click();
    await untilSent(w);
    check(app.state.finished === "error" && /refused the update \(“No space”\)/.test(text(doc, "result")), "start refused -> " + text(doc, "result").slice(0, 60));
    dev.startStatus = 0; dev.writeError = 3;
    doc.getElementById("flash").click();
    await untilSent(w);
    check(app.state.finished === "error" && /error while receiving/.test(text(doc, "result")) && dev.blocks === 4, "block refused -> stops there");
    dev.writeError = -1; dev.id = 25;
    doc.getElementById("refresh").click();
    await wait(150);
    check(doc.getElementById("flash").disabled && /can't take this firmware/.test(text(doc, "missing"))
      && /answers as a Model:Samples/.test(text(doc, "midi-status")), "machine answering as a Model:Samples -> nothing sent");
    dev.id = 27;
    doc.getElementById("refresh").click();
    await wait(150);
    check(!doc.getElementById("flash").disabled, "back to a Model:Cycles -> ready");

    // classic method
    doc.getElementById("m-slow").click();
    await wait(20);
    check(/via Elektron Model:Cycles · about \d+ min/.test(text(doc, "summary")) && /Open CONFIG › UPGRADE/.test(text(doc, "missing")),
      "classic summary: " + text(doc, "summary"));

    // stop during a paced transfer
    doc.getElementById("flash").click();
    await wait(400);
    check(!doc.getElementById("stop").hidden && /Flashing/.test(text(doc, "flash")), "during transfer: Stop visible, button busy");
    doc.getElementById("stop").click();
    for (let i = 0; i < 40 && app.state.sending; i++) await wait(50);
    check(app.state.finished === "stopped" && /Stopped/.test(text(doc, "result")), "Stop -> clear 'stopped' message");

    // full transfer at pace 0
    const n0 = sent.length;
    doc.getElementById("pace").value = "0";
    doc.getElementById("pace").dispatchEvent(new w.Event("input"));
    doc.getElementById("flash").click();
    for (let i = 0; i < 200 && app.state.sending; i++) await wait(50);
    const total = w.MCFlasher.splitMessages(app.state.fw.raw).length;
    check(sent.length - n0 === total, `every packet sent (${sent.length - n0}/${total})`);
    check(app.state.finished === "ok" && /Transfer complete/.test(text(doc, "result")) && /UPDATING FLASH/.test(text(doc, "result")),
      "success message shown");
    check(errors.length === 0, "no JS error during the flow " + (errors.length ? JSON.stringify(errors) : ""));
  }

  // 5b. The page's own rules against the sample (notes/49): each card alone and every pair of cards the page lets you
  // tick together, whatever it does with them (a card held by another, a swap), is a combination of REF_MAINOS.
  // No OS needed: the build key is chosenTweaks().
  if (MAIN) {
    const { w, doc, errors } = await load();
    const app = w.MCFlasherApp, feats = w.MC_TWEAKS.features;
    const keyNow = () => app.chosenTweaks().map((x) => x.id).join("+");
    const choices = (f) => (f.engines ? f.combos.map((c) => ({ engines: c.engines })) : f.package ? [{ package: f.package }]
      : f.variants.map((v) => ({ variant: v.id })));
    const clear = async () => {
      for (let round = 0; round < 3; round++)
        for (const f of feats) {
          const cb = doc.getElementById("feat-" + f.id);
          if (cb.checked && !cb.disabled) { cb.click(); await wait(5); }
        }
    };
    const pick = async (f, o) => {                   // false if the page holds the card (included by another one)
      if (o.engines) { await pickEngines(doc, o.engines); return true; }
      const cb = doc.getElementById("feat-" + f.id);
      if (cb.disabled) return false;
      if (!cb.checked) { cb.click(); await wait(5); }
      const r = doc.querySelector(`input[name="var-${f.id}"][value="${o.variant}"]`);
      if (r && !r.checked) { r.click(); await wait(5); }
      return true;
    };
    const reached = new Set(), missing = [];
    for (const [i, f] of feats.entries())
      for (const o of choices(f)) {
        await clear();
        await pick(f, o);
        const one = keyNow();
        reached.add(one);
        if (!app.REF_MAINOS[one]) missing.push(one);
        for (const g of feats.slice(i + 1))
          for (const p of choices(g)) {
            await clear();
            await pick(f, o);
            if (!(await pick(g, p))) continue;
            const k = keyNow();
            reached.add(k);
            if (!app.REF_MAINOS[k]) missing.push(k);
          }
      }
    check(missing.length === 0 && !reached.has(""),
      `the page's singles and pairs are all in the REF_MAINOS sample (${reached.size} combinations)` +
      (missing.length ? `; missing: ${[...new Set(missing)].slice(0, 5).join(", ")}` : ""));
    check(errors.length === 0, "no JS error while ticking every single and pair");
  }

  // 6. Real official OS (notes/49): every combination of REF_MAINOS (each card alone, every pair, the largest ones) is
  // reached by ticking its cards and must match its reference hash; on every build each mod is checked against REF_MODS,
  // so a combination outside the list builds too, mod by mod; and a mod that is not the Python one is refused
  if (REAL_OS) {
    const { w, doc, errors } = await load();
    const app = w.MCFlasherApp;
    app.loadOs(new Uint8Array(fs.readFileSync(REAL_OS)), "model-cycles_OS1.13.syx");
    await wait(20);
    if (REAL_ST) app.loadSyntakt(new Uint8Array(fs.readFileSync(REAL_ST)), ST_NAME);
    await wait(20);
    const needsSt = (key) => /sdvintage|syntakt/.test(key);
    const offered = Object.keys(app.REF_MAINOS).filter((k) => REAL_ST || !needsSt(k));
    // the machine cards: one entry per non-empty set of them, in card order (the tweak tools/compose.py composes)
    const mc = w.MC_TWEAKS.features.filter((f) => f.package).map((f) => f.package);
    const sets = [...Array((1 << mc.length) - 1).keys()].map((k) => mc.filter((_, i) => ((k + 1) >> i) & 1).join("+"));
    check(Object.keys(app.REF_MODS).length === w.MC_TWEAKS.tweaks.length + sets.length
      && w.MC_TWEAKS.tweaks.every((x) => app.REF_MODS[x.id] && /^[0-9a-f]{64}$/.test(app.REF_MODS[x.id].w)
        && !!x.append === /^[0-9a-f]{64}$/.test(app.REF_MODS[x.id].p || ""))
      && sets.every((id) => app.REF_MODS[id] && /^[0-9a-f]{64}$/.test(app.REF_MODS[id].w) && /^[0-9a-f]{64}$/.test(app.REF_MODS[id].p)),
      `REF_MODS: the writes of each of the ${w.MC_TWEAKS.tweaks.length} tweaks, and the payload of those that append one; ` +
      `writes and payload of each of the ${sets.length} sets of machine cards (${sets.join(", ")})`);
    const seen = new Set();
    let idx = -1;
    const mine = () => ++idx % SHARD_N === SHARD_K;   // this part's share of the combinations
    for (const key of Object.keys(app.REF_MAINOS)) {
      if (!REAL_ST && needsSt(key)) continue;          // the real Syntakt engines need the Syntakt OS
      if (!mine()) continue;
      await tickKey(w, doc, key);
      const f = app.state.fw;
      seen.add(app.state.buildKey);
      check(app.state.buildKey === key && f && f.kind === "built" && f.ref && f.modsRef,
        `real OS: ${key} matches its reference hash, each mod checked`);
    }
    if (MAIN) {
      // three cards together, not in the sample: built, each mod checked, no whole-firmware reference
      const plain = w.MC_TWEAKS.features.filter((f) => !f.engines && !f.excludes && !f.includes && !f.requires && !f.with)
        .map((f) => f.package || f.variants[0].id);
      const three = [...Array(plain.length).keys()].flatMap((i) => [...Array(plain.length).keys()].flatMap((j) =>
        [...Array(plain.length).keys()].map((k) => (i < j && j < k ? [plain[i], plain[j], plain[k]].join("+") : null))))
        .find((k) => k && !app.REF_MAINOS[k]);
      if (three) {
        await tickKey(w, doc, three);
        const f = app.state.fw;
        check(app.state.buildKey === three && f && f.kind === "built" && !f.ref && f.modsRef
          && /Each mod checked against its reference build/.test(text(doc, "file-status")),
          `real OS: ${three} (not in the sample) builds, each mod checked: ${text(doc, "file-status").slice(0, 80)}`);
      } else console.log(`  skip three cards outside the sample: ${plain.length} plain cards offered`);
    }
    if (MAIN) {
      // SAMPLE is composed in the page (composer.js, on the OS file's MAIN OS) into the tweak tools/compose.py makes
      await tickKey(w, doc, "sampler");
      const f = app.state.fw;
      check(app.state.buildKey === "sampler" && f && f.kind === "built" && f.sha === app.REF_MAINOS["sampler"] && f.modsRef
        && /Composed sampler: sampler as machine 6, 126 writes, 40508 bytes added to the OS\./.test(text(doc, "log")),
        "real OS: SAMPLE composed in the page (machine 6, 126 writes, 40 508 bytes), its MAIN OS REF_MAINOS[\"sampler\"], " +
        "its tweak checked against REF_MODS");
    }
    if (SHARD_N === 1)
      check(seen.size === offered.length && offered.every((k) => seen.has(k)),
        `REF_MAINOS: the ${seen.size} combinations of the sample all built` + (REAL_ST ? "" : " (without the Syntakt engines: no Syntakt OS given)"));
    else {
      fs.writeFileSync(process.env.SMOKE_SEEN, JSON.stringify({ seen: [...seen], offered }));
      console.log(`  (part ${SHARD_K + 1}/${SHARD_N}: ${seen.size} combinations built; coverage checked over all parts)`);
    }
    check(errors.length === 0, "no JS error with the real OS");
  }
  if (REAL_OS && MAIN) {
    // a mod whose writes or payload differ from the Python ones is refused (fresh page: builds are cached per key)
    const { w, doc, errors } = await load();
    const app = w.MCFlasherApp;
    app.loadOs(new Uint8Array(fs.readFileSync(REAL_OS)), "model-cycles_OS1.13.syx");
    await wait(20);
    const cw = app.REF_MODS["control-all-config"].w, sp = app.REF_MODS["sampler"].p;
    app.REF_MODS["control-all-config"].w = "0".repeat(64);
    app.REF_MODS["sampler"].p = "0".repeat(64);
    await tickKey(w, doc, "control-all-config");
    check(!app.state.fw && /control-all-config : ecritures differentes de la reference/.test(app.state.fwError || ""),
      "a mod whose writes differ from REF_MODS is refused: " + app.state.fwError);
    await tickKey(w, doc, "sampler");
    check(!app.state.fw && /sampler : charge utile differente de la reference/.test(app.state.fwError || ""),
      "a mod whose payload differs from REF_MODS is refused: " + app.state.fwError);
    app.REF_MODS["control-all-config"].w = cw;
    app.REF_MODS["sampler"].p = sp;
    check(errors.length === 0, "no JS error when a mod is refused");
  }

  // 7. "Samples OS" tab with both official files
  if (REAL_OS && REAL_SMP && MAIN) {
    const env7 = await load();
    const { w, doc, errors, sent } = env7;
    const app = w.MCFlasherApp;
    const cyc = new Uint8Array(fs.readFileSync(REAL_OS)), smp = new Uint8Array(fs.readFileSync(REAL_SMP));
    doc.getElementById("tab-samples").click();
    await wait(20);
    check(!doc.getElementById("panel-samples").hidden && !doc.getElementById("drop2-wrap").hidden
      && /Load both official OS files/.test(text(doc, "h2s")), "Samples OS tab: panel, second drop zone, step 2 title");
    app.loadSamples(cyc, "model-cycles_OS1.13.syx");               // wrong file in the second zone
    await wait(20);
    check(/not the official Model:Samples OS/.test(text(doc, "file2-status")), "a Cycles file in the Samples zone is refused");
    app.loadOs(smp, "model-samples_OS1.13.syx");                   // wrong file in the first zone
    await settle(w);
    check(/first file must be the official/.test(text(doc, "file-status")) && /first file must be/.test(text(doc, "missing")),
      "a Samples file in the Cycles zone is refused for this tab");
    app.loadOs(cyc, "model-cycles_OS1.13.syx");
    app.loadSamples(smp, "model-samples_OS1.13.syx");
    await settle(w);
    const f = app.state.fw;
    const sha = f && w.MCBuilder.hex(w.MCBuilder.sha256(f.raw));
    check(f && f.kind === "samples" && sha === app.REF_SAMPLES_ON_CYCLES, "both files -> reference build (" + (sha || "").slice(0, 16) + ")");
    check(/Model:Samples OS for your Model:Cycles/.test(text(doc, "file-status")) && /recognised/.test(text(doc, "file2-status")),
      "status lines for both files");
    doc.getElementById("m-slow").click();
    doc.getElementById("allow").click();
    await wait(80);
    doc.getElementById("ack").click();
    await wait(20);
    check(/MIDI interface for the way back/.test(text(doc, "missing")) && doc.getElementById("flash").disabled,
      "flash blocked until the MIDI-interface box is ticked");
    doc.getElementById("samples-ack").click();
    await wait(20);
    check(!doc.getElementById("flash").disabled && /Model:Samples OS \(for Model:Cycles\)/.test(text(doc, "summary")), "then ready: " + text(doc, "summary"));
    doc.getElementById("tab-mods").click();
    await settle(w);
    check(app.state.fw === null && /Select a mod/.test(text(doc, "missing")), "back to Mods: the Samples build is not sent");
    doc.getElementById("tab-samples").click();
    await settle(w);
    doc.getElementById("pace").value = "0";
    doc.getElementById("pace").dispatchEvent(new w.Event("input"));
    const n0 = sent.length;
    doc.getElementById("flash").click();
    for (let i = 0; i < 200 && app.state.sending; i++) await wait(50);
    check(sent.length - n0 === w.MCFlasher.splitMessages(app.state.fw.raw).length && /restarts as a Model:Samples/.test(text(doc, "result")),
      "full transfer + Samples message");
    noRest(w);
    doc.getElementById("m-fast").click();
    await wait(150);
    doc.getElementById("flash").click();
    await untilSent(w);
    check(app.state.finished === "ok" && same(env7.dev.received, app.state.fw.raw) && env7.dev.bad.length === 0
      && /restarts as a Model:Samples/.test(text(doc, "result")), "fast: the Samples OS build reaches the Model:Cycles byte for byte");
    doc.querySelector('.lang button[data-lang="fr"]').click();
    await wait(20);
    check(/OS Samples/.test(text(doc, "tab-samples")) && doc.getElementById("drop2-title").textContent === "model-samples_OS1.13.syx",
      "FR: tab translated, loaded file name kept");
    check(errors.length === 0, "no JS error in the Samples OS flow " + (errors.length ? JSON.stringify(errors) : ""));
  }

  // 7b. "Samples OS" tab, for a Model:Samples: the Cycles OS (notes/41), then its way back, over USB
  if (REAL_OS && REAL_SMP && MAIN) {
    const env = await load({ devName: "Elektron Model:Samples", device: { id: 25, name: "Model Samples" } });
    const { w, doc, errors } = env;
    const app = w.MCFlasherApp;
    const cyc = new Uint8Array(fs.readFileSync(REAL_OS)), smp = new Uint8Array(fs.readFileSync(REAL_SMP));
    doc.getElementById("tab-samples").click();
    doc.getElementById("smp-dir-smp").click();
    await wait(20);
    check(!doc.getElementById("smp-pane-smp").hidden && doc.getElementById("smp-pane-cyc").hidden
      && /Experimental/.test(text(doc, "smp-pane-smp")), "Model:Samples → Cycles OS: its own pane, tagged experimental");
    app.loadOs(cyc, "model-cycles_OS1.13.syx");
    app.loadSamples(smp, "model-samples_OS1.13.syx");
    await settle(w);
    let f = app.state.fw, sha = f && w.MCBuilder.hex(w.MCBuilder.sha256(f.raw));
    check(f && f.kind === "cos" && f.raw[4] === 0x0f && sha === app.REF_CYCLES_ON_SAMPLES,
      "both files -> Cycles OS for Model:Samples, reference build (" + (sha || "").slice(0, 16) + ")");
    doc.getElementById("allow").click();
    await wait(150);
    doc.getElementById("ack").click();
    await wait(20);
    check(/backup/.test(text(doc, "missing")) && doc.getElementById("flash").disabled, "flash blocked until the backup box is ticked");
    doc.getElementById("cos-ack").click();
    await wait(20);
    check(!doc.getElementById("flash").disabled && /Model:Cycles OS \(for Model:Samples\)/.test(text(doc, "summary")),
      "then ready: " + text(doc, "summary"));
    doc.getElementById("flash").click();
    await untilSent(w);
    check(app.state.finished === "ok" && same(env.dev.received, f.raw) && /restarts as a <b>Model:Cycles<\/b>|restarts as a Model:Cycles/.test(text(doc, "result")),
      "fast: the Cycles OS reaches the Model:Samples byte for byte");
    check(/Model:Samples screen/.test(text(doc, "result")), "after sending: confirm on the Model:Samples screen");

    // the machine now answers as a Model:Cycles: the way-there file is refused, the way back is accepted
    env.dev.id = 27;
    doc.getElementById("refresh").click();
    await wait(150);
    check(/nothing to install/.test(text(doc, "midi-status")) && doc.getElementById("flash").disabled,
      "way-there file vs a machine answering Model:Cycles: nothing sent");
    doc.getElementById("smp-dir-back").click();
    await settle(w);
    f = app.state.fw; sha = f && w.MCBuilder.hex(w.MCBuilder.sha256(f.raw));
    check(f && f.kind === "sback" && f.raw[4] === 0x11 && sha === app.REF_SAMPLES_BACK,
      "way back: official Samples OS in the Cycles packing, reference build (" + (sha || "").slice(0, 16) + ")");
    check(same(w.MCBuilder.unwrap(f.raw).stream, w.MCBuilder.unwrap(smp).stream), "way back: same content as the official Samples OS");
    await wait(150);
    check(!doc.getElementById("flash").disabled && /Model:Samples asks/.test(text(doc, "missing")),
      "way back: ready without an extra box: " + text(doc, "missing"));
    doc.getElementById("flash").click();
    await untilSent(w);
    check(app.state.finished === "ok" && same(env.dev.received, f.raw) && /own OS/.test(text(doc, "result")),
      "fast: the way back reaches the machine byte for byte");
    env.dev.id = 25;
    doc.getElementById("refresh").click();
    await wait(150);
    check(/nothing to bring back/.test(text(doc, "midi-status")), "way back vs a machine already on the Samples OS: nothing sent");
    check(errors.length === 0, "no JS error in the Model:Samples flow " + (errors.length ? JSON.stringify(errors) : ""));
  }

  // 7b-bis. Step 3 names the machine being flashed (the tab and machine chosen), and the port after the OS it runs
  {
    const { w, doc, errors } = await load({ devName: "Acme Synth" });
    const app = w.MCFlasherApp;
    noRest(w);
    doc.getElementById("allow").click();
    await wait(150);
    const seen = () => [text(doc, "flash"), text(doc, "midi-status"), doc.querySelector('[data-i18n-html="hf1"]').textContent,
      doc.querySelector('[data-i18n-html="hu3"]').textContent].join(" | ");
    check(/Flash the Model:Cycles/.test(seen()) && /Connect the Model:Cycles/.test(seen()) && /port named “Model:Cycles”/.test(seen())
      && !/Model:Samples/.test(seen()), "Mods tab, Model:Cycles: step 3 names the Model:Cycles: " + text(doc, "midi-status"));
    for (const [m, port] of [["smp", "Model:Samples"], ["cos", "Model:Cycles"]]) {
      doc.getElementById("mach-" + m).click();
      await wait(20);
      check(/Flash the Model:Samples/.test(seen()) && /Connect the Model:Samples/.test(seen()) && /the Model:Samples/i.test(text(doc, "midi-status"))
        && !/the Model:Cycles/i.test(text(doc, "midi-status")) && new RegExp("port named “" + port + "”").test(seen()),
        `Mods tab, ${m}: step 3 names the Model:Samples, port “${port}”: ` + seen());
    }
    app.setMode("samples");
    for (const [d, dev, port] of [["cyc", "Model:Cycles", "Model:Cycles"], ["smp", "Model:Samples", "Model:Samples"], ["back", "Model:Samples", "Model:Cycles"]]) {
      doc.getElementById("smp-dir-" + d).click();
      await wait(20);
      check(new RegExp("Flash the " + dev).test(seen()) && new RegExp("the " + dev, "i").test(text(doc, "midi-status"))
        && new RegExp("port named “" + port + "”").test(seen()), `Samples OS tab, ${d}: names the ${dev}, port “${port}”`);
    }
    app.applyLang("fr");
    await wait(20);
    check(/Flasher le Model:Samples/.test(text(doc, "flash")) && /le Model:Samples/i.test(text(doc, "midi-status")), "in French too: " + text(doc, "midi-status"));
    app.applyLang("en");
    app.setMode("mods");
    doc.getElementById("mach-cyc").click();
    await wait(20);
    check(/Flash the Model:Cycles/.test(seen()) && !errors.length, "back to the Model:Cycles, no JS error " + errors.join(" "));
  }

  // 7c. Mods tab on a Model:Samples (notes/57): always the Model:Cycles OS, packed for the machine. The two files must be
  // byte for byte those of tools/mods_for_samples.py for the same SAMPLE build (SHA-256 below: tools/build.py -t sampler,
  // then tools/mods_for_samples.py on its output).
  if (REAL_OS && REAL_SMP && MAIN) {
    const MFS = { smp: "46f9acdbf07f56058fae84ef4beaa67556adae6de2c3f3b558fa927880cfaa45",
                  cos: "0fecd30e68a26bc7de140a7087bcbde49783efea91433d18292059cfa9caef23" };
    const env = await load({ devName: "Elektron Model:Samples", device: { id: 25, name: "Model Samples" } });
    const { w, doc, errors } = env;
    const app = w.MCFlasherApp;
    noRest(w);
    const cyc = new Uint8Array(fs.readFileSync(REAL_OS)), smp = new Uint8Array(fs.readFileSync(REAL_SMP));
    check(app.state.machine === "cyc" && doc.getElementById("mach-pane").hidden && doc.getElementById("drop2-wrap").hidden
      && doc.getElementById("mach-cyc").getAttribute("aria-checked") === "true", "Mods tab: Model:Cycles by default, no Samples pane");
    doc.getElementById("mach-smp").click();
    await wait(20);
    check(!doc.getElementById("mach-pane").hidden && /Tested/.test(text(doc, "mach-pane")) && !doc.getElementById("drop2-wrap").hidden
      && /Load both official OS files/.test(text(doc, "h2s")) && !doc.getElementById("mach-w-smp").hidden
      && doc.getElementById("mach-w-cos").hidden, "Model:Samples on its OS: pane tagged tested, second drop zone");
    app.loadOs(cyc, "model-cycles_OS1.13.syx");
    doc.getElementById("feat-sampler").click();
    await settle(w);
    check(!app.state.fw && /official Model:Samples OS below/.test(text(doc, "file-status"))
      && /Model:Samples OS file, to load/.test(text(doc, "mod-sel")), "SAMPLE ticked, no Samples file yet: asked for it");
    app.loadSamples(smp, "model-samples_OS1.13.syx");
    await settle(w);
    let f = app.state.fw, sha = f && w.MCBuilder.hex(w.MCBuilder.sha256(f.raw));
    check(f && f.kind === "built" && f.machine === "smp" && f.raw[4] === 0x0f && f.ref && f.sha === app.REF_MAINOS["sampler"]
      && sha === MFS.smp && /_for-samples_smp-os\.syx$/.test(f.name),
      "SAMPLE for a Model:Samples on its OS = tools/mods_for_samples.py _smp-os (" + (sha || "").slice(0, 16) + ")");
    check(/Packed for your Model:Samples \(on its own OS\)/.test(text(doc, "file-status")), "status line: " + text(doc, "file-status").slice(-60));
    doc.getElementById("allow").click();
    await wait(150);
    doc.getElementById("ack").click();
    await wait(20);
    check(/backup/.test(text(doc, "missing")) && doc.getElementById("flash").disabled, "flash blocked until the backup box is ticked");
    doc.getElementById("mach-ack").click();
    await wait(20);
    check(!doc.getElementById("flash").disabled && /\(for Model:Samples\)/.test(text(doc, "summary")) && /Model:Samples asks/.test(text(doc, "missing")),
      "then ready: " + text(doc, "summary"));
    doc.getElementById("flash").click();
    await untilSent(w);
    check(app.state.finished === "ok" && same(env.dev.received, f.raw) && /with your mods/.test(text(doc, "result")),
      "fast: the modded Cycles OS reaches the Model:Samples byte for byte");

    // now it answers as a Model:Cycles: the Samples-OS packing is refused, the Cycles-OS packing (change mods) is sent
    env.dev.id = 27;
    doc.getElementById("refresh").click();
    await wait(150);
    check(/already on the Cycles OS/.test(text(doc, "midi-status")) && doc.getElementById("flash").disabled,
      "Samples-OS packing vs a machine answering Model:Cycles: nothing sent");
    doc.getElementById("mach-cos").click();
    await settle(w);
    f = app.state.fw; sha = f && w.MCBuilder.hex(w.MCBuilder.sha256(f.raw));
    check(f && f.machine === "cos" && f.raw[4] === 0x11 && f.raw[8] === 0x0c && sha === MFS.cos && !doc.getElementById("mach-w-cos").hidden,
      "Model:Samples on the Cycles OS = tools/mods_for_samples.py _cyc-os (" + (sha || "").slice(0, 16) + ")");
    await wait(150);
    check(!doc.getElementById("flash").disabled, "ready for a machine answering Model:Cycles: " + text(doc, "missing"));
    doc.getElementById("flash").click();
    await untilSent(w);
    check(app.state.finished === "ok" && same(env.dev.received, f.raw), "fast: the change of mods reaches the machine byte for byte");
    env.dev.id = 25;
    doc.getElementById("refresh").click();
    await wait(150);
    check(/on its own OS/.test(text(doc, "midi-status")) && doc.getElementById("flash").disabled,
      "Cycles-OS packing vs a machine answering Model:Samples: nothing sent");

    // back to Model:Cycles: the usual build, and a machine answering Model:Samples is pointed to step 1
    doc.getElementById("mach-cyc").click();
    await settle(w);
    f = app.state.fw;
    check(f && !f.machine && f.raw[4] === 0x11 && f.sha === app.REF_MAINOS["sampler"] && doc.getElementById("mach-pane").hidden
      && doc.getElementById("drop2-wrap").hidden && /choose it in step 1/.test(text(doc, "midi-status")),
      "Model:Cycles again: plain build; a Model:Samples answering is told to pick it in step 1");
    doc.querySelector('.lang button[data-lang="fr"]').click();
    doc.getElementById("mach-smp").click();
    await settle(w);
    check(/sous son OS/.test(text(doc, "mach-smp")) && /Des mods sur un Model:Samples/.test(text(doc, "mach-pane"))
      && /Emballé pour votre Model:Samples/.test(text(doc, "file-status")), "FR: machine picker and status translated");
    app.setMachine("cyc");                                         // remembered by the page: leave the default for the next sections
    check(errors.length === 0, "no JS error in the mods-on-Model:Samples flow " + (errors.length ? JSON.stringify(errors) : ""));
  }

  console.log(fail ? `\nFAILED (${fail})` : "\nALL OK");
  process.exit(fail ? 1 : 0);
}
main();