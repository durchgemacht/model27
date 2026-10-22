// docs/flasher/composer.js against the Python composer (tools/webcompose_synth.py writes the reference), notes/61.
// Part 1 (B3a): each package and each part of the builder (B4e) placed at every reference placement gives
// relocate.place's bytes, entry symbols and end of the variables. Part 2 (B3b, B4e), with the official file: compose()
// on the file's MAIN OS, with the parts (the shortcut layer, the dispatchers), gives compose.compose()'s
// tweak for each selection (id, order, name, version, the conflicts against the folder's tweaks and the probes,
// writes, append, symbols), MCBuilder.build() makes of it, with the tweaks named on top, the MAIN OS
// compose.build_syx() makes, and fill() gives compose.fill()'s writes and payload for 1 to 6 synthetic machines.
//   node tools/webcompose_check.js <dir with compose.json> [model-cycles_OS1.13.syx, with composed.json in the dir]
const fs = require("fs"), path = require("path");
const C = require("../docs/flasher/composer.js");
const B = require("../docs/flasher/builder.js");

const ref = JSON.parse(fs.readFileSync(path.join(process.argv[2], "compose.json")));
let ok = Object.keys(ref).length > 0;
for (const [id, { bundle, cases }] of Object.entries(ref)) {
  let same = 0;
  for (const c of cases) {
    const r = C.place(bundle, c.code_at, c.bss_at, c.values);
    const bytes = Buffer.from(r.blob).toString("hex") === c.blob;
    const syms = Object.keys(c.symbols).every((k) => r.symbols[k] === c.symbols[k]);
    const end = r.bssEnd === c.bss_end;
    if (bytes && syms && end) same++;
    else console.log(`  ${id} at 0x${c.code_at.toString(16)} / 0x${c.bss_at.toString(16)}: bytes ${bytes}, symbols ${syms}, end ${end}`);
  }
  console.log(`${id}: ${same}/${cases.length} placements identical to relocate.place (bytes, entry symbols, end of the variables)`);
  ok = ok && same === cases.length;
}

// JSON with every object's keys sorted: the same data, whatever order each side wrote its keys in
const canon = (v) => JSON.stringify(v, (_k, x) => (x && typeof x === "object" && !Array.isArray(x)
  ? Object.fromEntries(Object.entries(x).sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))) : x));

if (process.argv[3]) {
  const ref2 = JSON.parse(fs.readFileSync(path.join(process.argv[2], "composed.json")));
  const raw = new Uint8Array(fs.readFileSync(process.argv[3]));
  const mainOs = B.mainOsOf(raw, ref2.device);
  ok = ok && ref2.cases.length > 0;
  for (const c of ref2.cases) {
    const label = c.ids.join("+") + c.with.map((w) => ` + ${w}`).join("");
    try {
      const { tweak } = C.compose(mainOs, ref2.frames, c.ids.map((id) => ref2.packages[id]), ref2.tweaks, ref2.parts,
                                  ref2.claims);
      const differ = Object.keys(c.tweak).filter((k) => canon(tweak[k]) !== canon(c.tweak[k]));
      const built = B.build(raw, ref2.device, [tweak, ...c.with.map((w) => ref2.with[w])]);
      if (built.mainOsSha !== c.main_os) differ.push("MAIN OS");
      console.log(`${label}: ${differ.length ? "DIFFERENT " + differ.join(", ") : "identical"} to compose.py `
        + `(${tweak.writes.length} writes, ${tweak.conflicts.length} conflicts, MAIN OS ${built.mainOsSha.slice(0, 12)})`);
      ok = ok && !differ.length;
    } catch (e) {
      console.log(`${label}: ERROR ${e.message}`);
      ok = false;
    }
  }
  let same = 0;
  for (const f of ref2.fills) {
    const n = f.machines.length;
    try {
      const r = C.fill(C.frameOf(ref2.frames, n), mainOs, f.machines, f.blobs.map(([a, h]) => [a, C.fromHex(h)]),
                       f.bss_end);
      if (canon(r.writes) === canon(f.writes) && canon(r.append) === canon(f.append)) same++;
      else console.log(`  fill of ${n} synthetic machines: writes ${canon(r.writes) === canon(f.writes)}, `
        + `append ${canon(r.append) === canon(f.append)}`);
    } catch (e) {
      console.log(`  fill of ${n} synthetic machines: ERROR ${e.message}`);
    }
  }
  console.log(`fill: ${same}/${ref2.fills.length} synthetic builds of 1 to ${ref2.fills.length} machines identical to compose.fill`);
  ok = ok && ref2.fills.length > 0 && same === ref2.fills.length;
}
process.exit(ok ? 0 : 1);
