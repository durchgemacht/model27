/* Composes added machines in the browser: the port of tools/compose.py's path without the toolchain (notes/61,
 * increments B3a to B3c). The Python composer is the reference; tools/webcompose_check.sh compares the two byte for
 * byte, and a change to how one composes goes into the other in the same commit.
 *
 * B3a: a package's object reaches the page laid out once at offset 0 by tools/relocate.py (layout(), bundle()):
 * its code and tables in hex, each relocation as [position, base, addend] (base "code", "bss", "abs", or the name of
 * a patch point), the symbols the composer needs as [base, offset], the variables' size. place() puts it at the
 * build's addresses, as relocate.apply() does.
 *
 * B3b: the registrar's part of a build comes as a frame per number of machines (tools/machines/registrar/frame.json,
 * compose.frames()): the writes and the reloc that do not depend on which machines, the layout, the runtime, the boot
 * stub template. fill() adds what does (the data block, the descriptors, the parameter block, the payload parts, the
 * segments, the boot stub), reading the stock values in the user's own MAIN OS (MCBuilder.mainOsOf), as compose.fill()
 * reads them in the official file. compose() is compose.compose(): the packages (compose.web_package()) placed one
 * after the other, registered together, their hooks and vtable entries added, the conflicts computed against the
 * tweaks given. It returns the tweak, which MCBuilder.build() applies like any other.
 *
 * B4e (notes/63): the builder's parts (compose.web_part(): the shortcut layer, the dispatchers) come laid out once like
 * a package; shortcutLayer() and dispatchLayer() place them and write their data blocks and sites as
 * compose.shortcut_layer() and compose.dispatch_layer() do, in the builds whose machines need them.
 *
 * C2 (notes/65): the declared claims. A package's and a part's come with them (tools/claims.py's to_json form), the
 * tweaks' as a map by id. claimClashes() is claims.clashes(): the same saved slot, key combination, descriptor or
 * formatter, so a build also conflicts with the tweaks whose claims clash with its own, and a build whose own packages
 * clash is refused.
 *
 * License: MIT (the repository's LICENSE).
 *
 * Wrapped in an IIFE: in a classic <script>, top-level declarations are global and would collide.
 */
(function () {
"use strict";

const BASE = 0x40000400;                          // where the MAIN OS runs (builder.js, tools/build.py)
const STOCK_EXTENDED = { CHORD: 5 };              // compose.STOCK_EXTENDED: the stock machines a package may extend

function fromHex(s) {
  // two hexadecimal digits per byte, as everywhere in the page (builder.js); anything else is refused
  if (typeof s !== "string" || s.length % 2 || /[^0-9a-fA-F]/.test(s))
    throw new Error(`invalid hexadecimal: ${String(s).slice(0, 24)}`);
  const out = new Uint8Array(s.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = parseInt(s.substr(i * 2, 2), 16);
  return out;
}
function hex(bytes) {                             // bytes.hex()
  let s = "";
  for (const b of bytes) s += b.toString(16).padStart(2, "0");
  return s;
}
const hx = (v) => "0x" + v.toString(16);          // f"{v:#x}"
const align4 = (x) => Math.ceil(x / 4) * 4;
const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
function u32(b, o) { return ((b[o] << 24) | (b[o + 1] << 16) | (b[o + 2] << 8) | b[o + 3]) >>> 0; }
function put32(b, o, v) { b[o] = v >>> 24; b[o + 1] = (v >>> 16) & 255; b[o + 2] = (v >>> 8) & 255; b[o + 3] = v & 255; }
function be32(v) { const b = new Uint8Array(4); put32(b, 0, v); return b; }
function concat(...arrs) {
  const out = new Uint8Array(arrs.reduce((n, a) => n + a.length, 0));
  let o = 0;
  for (const a of arrs) { out.set(a, o); o += a.length; }
  return out;
}
function bytesOf(...xs) {                         // bytes([...]): each value a byte, or refused
  for (const x of xs) if (!Number.isInteger(x) || x < 0 || x > 255) throw new Error(`${x}: not a byte`);
  return Uint8Array.from(xs);
}
function checkOverlaps(writes) {                  // writes in address order
  for (let k = 1; k < writes.length; k++)
    if (writes[k - 1].off + writes[k - 1].new.length / 2 > writes[k].off)
      throw new Error(`writes overlap at ${hx(BASE + writes[k].off)}`);
}

// relocate.apply(): the bundle's code at codeAt, its variables at bssAt (both 4-aligned), its patch points' symbols
// from values ({ symbol: number }). Returns { blob, symbols, bssEnd }.
function place(bundle, codeAt, bssAt, values = {}) {
  if (codeAt % 4 || bssAt % 4)
    throw new Error(`placed at 0x${codeAt.toString(16)} / 0x${bssAt.toString(16)}: code and variables start 4-aligned`);
  const bases = Object.assign(Object.create(null), { code: codeAt, bss: bssAt, abs: 0 });
  const blob = fromHex(bundle.code);
  const dv = new DataView(blob.buffer);
  for (const [pos, base, add] of bundle.relocs) {
    let v;
    if (base in bases) v = bases[base] + add;
    else if (Object.prototype.hasOwnProperty.call(values, base)) v = values[base] + add;
    else throw new Error(`undefined symbol ${base}: not one of this build's patch points`);
    dv.setUint32(pos, v >>> 0, false);
  }
  const symbols = {};
  for (const [name, [base, off]] of Object.entries(bundle.symbols)) symbols[name] = bases[base] + off;
  return { blob, symbols, bssEnd: bssAt + bundle.bss };
}

// compose.frame_of(): the frame of n machines out of frame.json, its writes in address order
function frameOf(frames, n) {
  if (frames.schema !== "model27-registrar-frame/0.1") throw new Error(`registrar frame: schema ${frames.schema}`);
  if (n === 0) {                                  // extensions only (notes/66 §3): nothing registered
    if (!frames.alone) throw new Error("no registrar frame without an added machine");
    return { n: 0, layout: frames.layout, stub: frames.stub, writes: frames.alone.writes.slice(), reloc: [] };
  }
  if (!has(frames.by_n, String(n))) throw new Error(`no registrar frame for ${n} machines`);
  const own = frames.by_n[String(n)];
  return { n, layout: frames.layout, stock: frames.stock, runtime: frames.runtime, stub: frames.stub,
           writes: frames.writes.concat(own.writes).sort((a, b) => a.off - b.off), reloc: own.reloc };
}

// compose.parameter_block(): the runtime's parameter block for this build (registrar.S), header and one entry per
// machine
function parameterBlock(fr, machines) {
  const lay = fr.layout, rt = fr.runtime;
  const n = machines.length, first = lay.first, nm = first + n, regs = rt.regs_at;
  if (n > rt.max_machines) throw new Error(`${n} machines: the runtime's block holds ${rt.max_machines}`);
  const parts = [bytesOf(n, first, first + n - 1, nm),
                 be32(76 + 5 * n),                                   // last
                 be32(lay.data + 12 * nm),                           // knob_tab
                 be32(regs + rt.regs_header + rt.entry_size * n)];   // machines_end
  machines.forEach((m, i) => {
    const e = new Uint8Array(rt.entry_size);
    e.set(bytesOf(first + i, m.image, 76 + 5 * i, 76 + 5 * i - 51), 0);
    put32(e, 4, lay.recs + 0x60 * i);                                // rec
    put32(e, 8, m.knob_hook || 0);                                   // knob_hook
    parts.push(e);
  });
  const out = concat(...parts);
  if (out.length > rt.regs_header + rt.entry_size * rt.max_machines) throw new Error("parameter block too big");
  return out;
}

// gen_syntakt_engines.segments(): the payload's parts to store in the image (pack), their union to within 64 bytes,
// aligned to 4. The rest is zero: the boot hook clears the payload, then copies the segments.
function segments(parts, size, pay) {
  const rs = parts.map((p) => {
    const a = parseInt(p.dest, 16), r = p.syntakt || p.cycles;
    const n = p.hex !== undefined ? p.hex.length / 2 : parseInt(r[1], 16) - parseInt(r[0], 16);
    return [a - (a % 4), align4(a + n)];
  }).sort((x, y) => x[0] - y[0] || x[1] - y[1]);
  const out = [];
  for (const [lo, hi] of rs) {
    const last = out[out.length - 1];
    if (last && lo <= last[1] + 64) last[1] = Math.max(last[1], hi);
    else out.push([lo, hi]);
  }
  if (out[0][0] < pay || out[out.length - 1][1] > pay + size) throw new Error("payload segments outside the payload");
  return out.map(([lo, hi]) => [lo, hi - lo]);
}

// compose.boot_stub(): the boot stub for this build from the template, its three immediates filled in, the segment
// table (address, longs per segment, then 0, 0) appended
function bootStub(fr, src, dst, longs, segs) {
  const st = fr.stub;
  if (parseInt(st.at, 16) !== fr.layout.cave)
    throw new Error(`the stub template is for ${st.at}, the boot hook lives at ${hx(fr.layout.cave)}`);
  const code = fromHex(st.hex);
  put32(code, st.src_at, src);
  put32(code, st.dst_at, dst);
  put32(code, st.longs_at, longs);
  const table = concat(...segs.map(([a, n]) => concat(be32(a), be32(Math.floor(n / 4)))), new Uint8Array(8));
  const stub = concat(code.subarray(0, st.segs_at), table);
  if (fr.layout.cave + stub.length > parseInt(st.end_limit, 16))
    throw new Error(`boot stub of ${stub.length} bytes (${segs.length} segments) does not fit before ${st.end_limit}`);
  return stub;
}

// compose.fill(): the rest of the registrar's part, what depends on the machines: the data block (names, update and
// render addresses, the strings), five descriptors per machine (SNARE's, read in the user's MAIN OS, with the knob
// fields set), the parameter block, the payload parts in their order, the segments and the boot stub. machines: name,
// image, decay, knobs ([long, short, default] or [long, short, default, min, max]), update, render; blobs: [[address,
// bytes]]; bssEnd: end of the variables. Returns { writes, append }.
function fill(fr, mainOs, machines, blobs, bssEnd) {
  const lay = fr.layout, stock = fr.stock, rt = fr.runtime;
  const n = machines.length, first = lay.first;
  if (n !== fr.n) throw new Error(`a frame for ${fr.n} machines, ${n} given`);
  for (const m of machines)
    if (m.knobs.length !== 4) throw new Error(`${m.name}: ${m.knobs.length} knobs; a machine has 4 and DECAY, five descriptors`);
  const nm = first + n;
  const rd = (va) => u32(mainOs, va - BASE);
  const mapAt = lay.data + 16 * nm;
  // --- data (as added_machine): names, update/render tables, machine -> record, strings
  const strings = machines.map((m) => m.name).concat(machines.flatMap((m) => m.knobs.flatMap((k) => [k[0], k[1]])));
  const addr = new Map();
  let at = mapAt + align4(nm);
  for (const s of strings) {
    if (!/^[\x00-\x7f]*$/.test(s)) throw new Error(`${s}: names and knob names are ASCII`);
    if (!addr.has(s)) { addr.set(s, at); at += s.length + 1; }
  }
  const stockTable = (va) => Array.from({ length: first }, (_, i) => rd(va + 4 * i));
  const names = stockTable(stock.names).concat(machines.map((m) => addr.get(m.name)));
  const upd = stockTable(stock.update).concat(machines.map((m) => m.update));
  const rnd = stockTable(stock.render).concat(machines.map((m) => m.render));
  const recs = Array.from({ length: nm }, (_, i) => i + 1);
  const data = concat(...[names, upd, rnd, recs].map((t) => concat(...t.map((x) => be32(x)))),
                      mainOs.subarray(stock.map - BASE, stock.map - BASE + first),
                      Uint8Array.from({ length: nm - first }, (_, i) => first + i), new Uint8Array(align4(nm) - nm),
                      ...[...addr.keys()].map((s) => concat(Uint8Array.from(s, (ch) => ch.charCodeAt(0)), new Uint8Array(1))));
  if (lay.data + data.length > lay.descn) throw new Error("data past DESCN");
  // --- 5 descriptors per machine, modelled on SNARE's
  const ds = lay.dstride, descs = [];
  const snare = (k) => mainOs.slice(stock.snare_desc + k * ds - BASE, stock.snare_desc + (k + 1) * ds - BASE);
  for (const m of machines) {
    m.knobs.forEach(([long, short, dflt, ...rng], k) => {
      const e = snare(k);
      put32(e, 0x00, 6);
      if (rng.length) { put32(e, 0x08, rng[0] << 8); put32(e, 0x0c, rng[1] << 8); }
      put32(e, 0x10, dflt << 8);
      put32(e, 0x2c, addr.get(long));
      put32(e, 0x34, addr.get(short));
      descs.push(e);
    });
    const e = snare(4);
    put32(e, 0x10, m.decay << 8);
    descs.push(e);
  }
  // --- payload: the packages, the runtime, its parameter block, the data, the descriptors
  const regs = rt.regs_at, code = fromHex(rt.hex);
  if (lay.stubs + code.length > regs) throw new Error("the runtime runs into its parameter block");
  const block = parameterBlock(fr, machines);
  if (regs + block.length > lay.data) throw new Error("parameter block past DATA");
  const part = (a, b) => ({ dest: hx(a), hex: hex(b) });
  const parts = blobs.filter(([a]) => a < lay.stubs).map(([a, b]) => part(a, b)).concat([
    part(lay.stubs, code),
    part(regs, block),
    part(lay.data, data),
    { dest: hx(lay.descn), cycles: [hx(stock.desc), hx(stock.desc + lay.ndesc * ds)] },
    part(lay.descn + lay.ndesc * ds, concat(...descs)),
  ], blobs.filter(([a]) => a >= lay.stubs).map(([a, b]) => part(a, b)));
  const size = bssEnd - lay.pay;
  const segs = segments(parts, size, lay.pay);
  const end = lay.image_end, added = segs.reduce((s, [, k]) => s + k, 0);
  if (end + added > lay.end_limit) throw new Error(`${added} bytes added: the image would pass ${hx(lay.end_limit)}`);
  const stub = bootStub(fr, end, lay.pay, Math.floor(size / 4), segs);
  if (stub.length > lay.stub_room) throw new Error("boot stub too big for its mask");
  const cave = lay.cave - BASE, free = mainOs.subarray(cave, cave + stub.length);
  if (free.length !== stub.length || !free.every((b) => b === 0xff)) throw new Error("the boot stub's place is taken");
  const writes = fr.writes.map((w) => ({ ...w })).concat([{ off: cave, old: "ff".repeat(stub.length), new: hex(stub) }]);
  writes.sort((a, b) => a.off - b.off);
  checkOverlaps(writes);
  return { writes, append: { at: hx(end), dest: hx(lay.pay), size, parts, reloc: fr.reloc.map((r) => [...r]),
                             pack: segs.map(([a, k]) => [hx(a), k]) } };
}

// compose.fill_alone(): a build without an added machine (notes/66 §3), the payload parts (the packages and the parts
// of the builder, nothing of the registrar's), the segments and the boot stub
function fillAlone(fr, mainOs, blobs, bssEnd) {
  const lay = fr.layout;
  const parts = blobs.slice().sort(([a], [b]) => a - b).map(([a, b]) => ({ dest: hx(a), hex: hex(b) }));
  const size = bssEnd - lay.pay;
  const segs = segments(parts, size, lay.pay);
  const end = lay.image_end, added = segs.reduce((s, [, k]) => s + k, 0);
  if (end + added > lay.end_limit) throw new Error(`${added} bytes added: the image would pass ${hx(lay.end_limit)}`);
  const stub = bootStub(fr, end, lay.pay, Math.floor(size / 4), segs);
  if (stub.length > lay.stub_room) throw new Error("boot stub too big for its mask");
  const cave = lay.cave - BASE, free = mainOs.subarray(cave, cave + stub.length);
  if (free.length !== stub.length || !free.every((b) => b === 0xff)) throw new Error("the boot stub's place is taken");
  const writes = fr.writes.map((w) => ({ ...w })).concat([{ off: cave, old: "ff".repeat(stub.length), new: hex(stub) }]);
  writes.sort((a, b) => a.off - b.off);
  checkOverlaps(writes);
  return { writes, append: { at: hx(end), dest: hx(lay.pay), size, parts, reloc: [],
                             pack: segs.map(([a, k]) => [hx(a), k]) } };
}

// compose.patch_values(), the symbol form: the build's values for the package's patch points
function patchValues(p, values) {
  const out = {};
  for (const pp of p.patch_points || []) {
    if (!has(values, pp.kind)) throw new Error(`${p.id}: patch point kind ${pp.kind} unknown`);
    if (!pp.symbol) throw new Error(`${p.id}: patch points as defines cannot be applied to a committed object: use symbols`);
    out[pp.symbol] = values[pp.kind];
  }
  return out;
}

const ramClaims = (p) => p.uses.filter((u) => u.point === "memory.ram").map((u) => u.range.map((x) => parseInt(x, 16)));

// compose.check_ram_claims(): two packages never claim the same RAM
function checkRamClaims(packages) {
  const claims = packages.flatMap((p) => ramClaims(p).map(([lo, hi]) => [p.id, lo, hi]));
  claims.forEach(([a, lo, hi], i) => {
    for (const [b, lo2, hi2] of claims.slice(i + 1))
      if (a !== b && lo < hi2 && lo2 < hi)
        throw new Error(`${a} and ${b} claim the same RAM: ${hx(lo)}..${hx(hi)} and ${hx(lo2)}..${hx(hi2)}`);
  });
}

// compose.package_writes(): the package's own hooks (jsr/jmp into its code) and vtable entries, each checked against
// the stock bytes. That a vtable entry is the only reference to its method is a property of the stock OS, which the
// Python composer checks on every build (notes/61 §4); here the entry's stock bytes are checked like any write's.
// The hooks and entries at the addresses in skip are left out: the shortcut layer chains them, a dispatcher takes them.
function packageWrites(p, mainOs, syms, skip = new Set()) {
  const sym = (s) => { if (!has(syms, s)) throw new Error(`${p.id}: no symbol ${s}`); return syms[s]; };
  const writes = [];
  for (const u of p.uses) {
    if ("hook" in u) {
      if (skip.has(parseInt(u.hook.at, 16))) continue;
      const h = u.hook, va = parseInt(h.at, 16), old = fromHex(h.stock), target = be32(sym(h.symbol));
      const nw = h.op === "jsr" ? concat(bytesOf(0x4e, 0xb9), target) : concat(bytesOf(0x4e, 0xf9), target, bytesOf(0x4e, 0x71));
      if (nw.length !== old.length) throw new Error(`${p.id}: hook at ${hx(va)}: ${nw.length} bytes for ${old.length}`);
      const here = mainOs.subarray(va - BASE, va - BASE + old.length);
      if (hex(here) !== hex(old)) throw new Error(`${p.id}: ${hx(va)}: ${hex(old)} expected, ${hex(here)} found`);
      writes.push({ off: va - BASE, old: hex(old), new: hex(nw) });
    } else if ("vtable" in u) {
      const vt = u.vtable, va = parseInt(vt.at, 16), method = parseInt(vt.stock_ptr, 16);
      if (skip.has(va)) continue;
      if (u32(mainOs, va - BASE) !== method) throw new Error(`${p.id}: ${hx(va)}: not the stock entry ${hx(method)}`);
      writes.push({ off: va - BASE, old: hex(be32(method)), new: hex(be32(sym(vt.symbol))) });
    }
  }
  return writes;
}

// The parts of the builder (notes/63 §3 to §5, B4b to B4e): code compiled once, laid out once with all its roots
// (compose.web_part(): its bundle, its sites, its data block's layout), placed after the packages, its data block
// right after its code.
const asciiz = (s) => concat(Uint8Array.from(s, (ch) => ch.charCodeAt(0)), new Uint8Array(1));
function placePart(part, at, codeEnd, values) {   // relocate.apply() of the part, its patch points from values (by kind)
  const pv = {};
  for (const pp of part.patch_points) pv[pp.symbol] = values[pp.kind];
  const { blob, symbols } = place(part.bundle, at, at, pv);
  if (at + blob.length > codeEnd) throw new Error(`${part.id}: code ends at ${hx(at + blob.length)}, past ${hx(codeEnd)}`);
  const out = {};
  for (const r of part.roots) out[r] = symbols[r];
  return { code: blob, symbols: Object.assign(out, pv) };
}

// compose.shortcut_uses(): the shortcuts the machines declare, checked against the builder's list (notes/63 §1.3, §5):
// [[machine's position, knob's position in the list, param]]. 0 is every shortcut's default.
function shortcutUses(packages, part) {
  const sc = part.shortcut, [lo, hi] = sc.range, out = [];
  packages.forEach((p, i) => {
    const seen = new Set();
    for (const u of p.uses) {
      if (u.point !== "shortcut") continue;
      const where = `${p.id}: shortcut ${u.key} + ${u.knob}`;
      if (u.key !== sc.key || !sc.knobs.includes(u.knob))
        throw new Error(`${where}: not on the builder's list, ${sc.key} + ${sc.knobs.join(", ")} (notes/63 §1.3)`);
      if (seen.has(u.knob)) throw new Error(`${where}: declared twice`);
      seen.add(u.knob);
      const prm = u.param, names = [prm.long || "", prm.short || ""];
      if (!names.every((x) => x && /^[\x20-\x7e]*$/.test(x)) || names[1].length > 4)
        throw new Error(`${where}: a long name and a short name of 4 characters at most, in printable ASCII`);
      const rng = [prm.min, prm.max, has(prm, "default") ? prm.default : 0];
      if (!rng.every(Number.isInteger) || !(lo <= rng[0] && rng[0] <= 0 && rng[1] >= 0 && rng[1] <= hi) || rng[0] === rng[1])
        throw new Error(`${where}: integers min <= 0 <= max, from ${lo} to ${hi}`);
      if (rng[2] !== 0) throw new Error(`${where}: default ${rng[2]}; a shortcut's default is 0 (notes/63 §11)`);
      out.push([i, sc.knobs.indexOf(u.knob), prm]);
    }
  });
  return out;
}

// compose.shortcut_layer(): the part placed at at, its data block after its code (the next of each record function's
// chain, the descriptor table, the machines, their shortcuts per knob, the strings), the knob lookup's vtable entry
// and the three sound record functions jumping into it; a package's wrapper over a record function becomes the next
// of the chain and its write is left out. Returns { blob, symbols, writes, skip, info }.
function shortcutLayer(mainOs, part, packages, symsOf, uses, at, codeEnd, first, descn) {
  const d = part.data, sc = part.shortcut, sites = part.sites;
  const dataAt = align4(at + part.bundle.code.length / 2);
  const nexts = [], skip = new Set();
  for (const s of sites.record) {
    const va = parseInt(s.at, 16), here = hex(mainOs.subarray(va - BASE, va - BASE + 8));
    if (here !== s.stock) throw new Error(`${hx(va)}: ${s.stock} expected, ${here} found`);
    const hooked = packages.flatMap((p) => p.uses.filter((u) => "hook" in u && parseInt(u.hook.at, 16) === va)
      .map((u) => [p, u.hook]));
    if (hooked.length > 1)
      throw new Error(`${hooked.map(([p]) => p.id).join(", ")} all hook ${hx(va)}: one wrapper behind the shortcut layer`);
    if (hooked.length) {
      const [p, h] = hooked[0];
      if (h.op !== "jmp" || h.stock !== s.stock)
        throw new Error(`${p.id}: its hook at ${hx(va)} is not a wrapper over the function's first 8 bytes`);
      nexts.push(symsOf[p.id][h.symbol]);
      skip.add(va);
    } else nexts.push(0);
  }
  const nk = sc.knobs.length, es = d.entry_size;
  const entries = new Uint8Array(es * nk * packages.length);
  const strAt = dataAt + d.entries + entries.length, addr = new Map();
  let strEnd = strAt;
  for (const [i, k, prm] of uses) {
    for (const x of [prm.long, prm.short])
      if (!addr.has(x)) { addr.set(x, strEnd); strEnd += x.length + 1; }
    let fmt = parseInt(sc.formatter, 16);
    if (has(prm, "format")) {
      fmt = symsOf[packages[i].id][prm.format];
      if (fmt === undefined) throw new Error(`${packages[i].id}: formatter ${prm.format} is not a symbol of the package (keep it)`);
    }
    const o = es * (nk * i + k);
    [addr.get(prm.long), addr.get(prm.short), prm.min << 8, prm.max << 8, (has(prm, "default") ? prm.default : 0) << 8, fmt]
      .forEach((v, j) => put32(entries, o + 4 * j, v));
  }
  const head = new Uint8Array(d.entries);
  nexts.forEach((v, j) => put32(head, d.next + 4 * j, v));
  put32(head, d.descn, descn);
  head[d.first] = first;
  head[d.count] = packages.length;
  const data = concat(head, entries, ...[...addr.keys()].map(asciiz));
  if (dataAt + data.length > codeEnd) throw new Error(`the shortcut layer ends at ${hx(dataAt + data.length)}, past ${hx(codeEnd)}`);
  const { code, symbols } = placePart(part, at, codeEnd, { shortcut_data: dataAt });
  const kv = sites.knob, va = parseInt(kv.vtable, 16), method = parseInt(kv.stock_ptr, 16);
  if (u32(mainOs, va - BASE) !== method) throw new Error(`${hx(va)}: not the stock entry ${hx(method)}`);
  for (const p of packages)
    if (p.uses.some((u) => "vtable" in u && parseInt(u.vtable.at, 16) === va))
      throw new Error(`${p.id}: replaces the knob lookup (${hx(va)}), which the shortcut layer takes`);
  const writes = [{ off: va - BASE, old: hex(be32(method)), new: hex(be32(symbols[kv.symbol])) }];
  for (const s of sites.record)
    writes.push({ off: parseInt(s.at, 16) - BASE, old: s.stock,
                  new: hex(concat(bytesOf(0x4e, 0xf9), be32(symbols[s.symbol]), bytesOf(0x4e, 0x71))) });
  return { blob: concat(code, new Uint8Array(dataAt - at - code.length), data), symbols, writes, skip,
           info: { id: part.id, code_at: at, code: code.length, data_at: dataAt, data: data.length, shortcuts: uses.length } };
}

// compose.dispatch_layer(): each point of the part that two or more packages take (their vtable entries, or their
// hooks, at the same address) gets the part's dispatcher there, and the data block after the part's code lists each
// package's method by machine; a point one package takes keeps the package's own entry or hook. The part is placed
// whole. Returns null when no point is shared, else { blob, symbols, writes, skip, info }.
function dispatchLayer(mainOs, part, packages, symsOf, at, codeEnd, first) {
  const d = part.data, sites = part.sites, shared = [];
  for (const [name, s] of Object.entries(sites)) {
    const kind = "vtable" in s ? "vtable" : "hook", va = parseInt(s[kind], 16), users = [];
    packages.forEach((p, i) => { for (const u of p.uses) if (kind in u && parseInt(u[kind].at, 16) === va) users.push([i, p, u[kind]]); });
    for (const [, p, h] of users) {
      const same = kind === "vtable" ? h.stock_ptr === s.stock_ptr : h.stock === s.stock && h.op === s.op;
      if (!same) throw new Error(`${p.id}: its ${kind} at ${hx(va)} is not the dispatcher's (${name})`);
    }
    if (users.length > 1) shared.push([name, users]);
  }
  if (!shared.length) return null;
  if (packages.length > d.max_machines) throw new Error(`${packages.length} machines: the dispatchers' tables hold ${d.max_machines}`);
  const dataAt = align4(at + part.bundle.code.length / 2);
  const block = new Uint8Array(d.size);
  block[d.first] = first;
  block[d.count] = packages.length;
  for (const [name, users] of shared)
    for (const [i, p, h] of users) put32(block, sites[name].table + 4 * i, symsOf[p.id][h.symbol]);
  if (dataAt + block.length > codeEnd) throw new Error(`the dispatchers end at ${hx(dataAt + block.length)}, past ${hx(codeEnd)}`);
  const { code, symbols } = placePart(part, at, codeEnd, { dispatch_data: dataAt });
  const writes = [], skip = new Set();
  for (const [name] of shared) {
    const s = sites[name], target = be32(symbols[s.symbol]);
    if ("vtable" in s) {
      const va = parseInt(s.vtable, 16), method = parseInt(s.stock_ptr, 16);
      if (u32(mainOs, va - BASE) !== method) throw new Error(`${hx(va)}: not the stock entry ${hx(method)}`);
      writes.push({ off: va - BASE, old: hex(be32(method)), new: hex(target) });
      skip.add(va);
    } else {
      const va = parseInt(s.hook, 16), here = hex(mainOs.subarray(va - BASE, va - BASE + s.stock.length / 2));
      if (s.op !== "jsr" || here !== s.stock) throw new Error(`${hx(va)}: ${s.op} ${s.stock} expected, ${here} found`);
      writes.push({ off: va - BASE, old: s.stock, new: hex(concat(bytesOf(0x4e, 0xb9), target)) });
      skip.add(va);
    }
  }
  return { blob: concat(code, new Uint8Array(dataAt - at - code.length), block), symbols, writes, skip,
           info: { id: part.id, code_at: at, code: code.length, data_at: dataAt, data: block.length,
                   points: Object.fromEntries(shared.map(([n, users]) => [n, users.map(([, p]) => p.id)])) } };
}

// tools/claims.py's rules (notes/65 §5), on the claims in its to_json form. A scope "all" meets every scope, a machine
// itself; a situation "any" meets every situation.
const meet = (s, t) => s === "all" || t === "all" || s === t;
const situationsMeet = (s, t) => s === "any" || t === "any" || s === t;

function rangesText(nums) {                       // claims._ranges(): "28-31", "18, 27, 30-31"
  const out = [];
  for (const n of [...new Set(nums)].sort((a, b) => a - b)) {
    if (out.length && n === out[out.length - 1][1] + 1) out[out.length - 1][1] = n;
    else out.push([n, n]);
  }
  return out.map(([a, b]) => (a === b ? `${a}` : `${a}-${b}`)).join(", ");
}

// claims.resolve(): a package's claims with its machine named, "machine" becoming "machine:<id>"
function resolveClaims(c, pid) {
  const s = (x) => (x === "machine" ? `machine:${pid}` : x);
  const out = Object.assign({}, c);
  for (const key of ["sound_slots", "record_slots", "descriptors"])
    if (c[key]) out[key] = c[key].map(([n, t]) => [n, s(t)]);
  if (c.saved) out.saved = c.saved.map(([w, b, t]) => [w, b, s(t)]);
  if (c.formatters) out.formatters = c.formatters.map(([o, t, k]) => [o, s(t), k]);
  if (c.views) out.views = c.views.map(([v, t, h]) => [v, s(t), h]);
  if (c.gestures) out.gestures = c.gestures.map((g) => Object.assign({}, g, { scope: s(g.scope) }));
  return out;
}

// claims.clashes(): why two holders' claims cannot be installed together, empty when they can
function claimClashes(a, b) {
  const out = [];
  for (const [key, label] of [["sound_slots", "k"], ["record_slots", "record slots"], ["descriptors", "descriptors"]]) {
    const hit = [];
    for (const [n, s] of a[key] || []) for (const [m, t] of b[key] || []) if (n === m && meet(s, t)) hit.push(n);
    if (hit.length) out.push(`${label} ${rangesText(hit)}`);
  }
  const saved = new Set();
  for (const [w, , s] of a.saved || []) for (const [w2, , t] of b.saved || []) if (w === w2 && meet(s, t)) saved.add(w);
  for (const w of [...saved].sort()) out.push(`saved bytes: ${w}`);
  const objects = new Set();                      // one formatter per interface object: the scope does not narrow it
  for (const [o] of a.formatters || []) for (const [o2] of b.formatters || []) if (o === o2) objects.add(o);
  for (const o of [...objects].sort((x, y) => x - y)) out.push(`the formatter of interface object ${o}`);
  if (a.plock_rows && b.plock_rows) out.push("the p-lock rows of k >= 23");
  const ma = a.midi || {}, mb = b.midi || {};
  const cc = [...new Set(ma.cc || [])].filter((x) => (mb.cc || []).includes(x)).sort((x, y) => x - y);
  const nrpn = [...new Set(ma.nrpn || [])].filter((x) => (mb.nrpn || []).includes(x)).sort();
  if (cc.length) out.push(`CC ${cc.join(", ")}`);
  if (nrpn.length) out.push(`NRPN ${nrpn.join(", ")}`);
  for (const [lo, hi] of a.ram || [])
    for (const [lo2, hi2] of b.ram || [])
      if (lo < hi2 && lo2 < hi) out.push(`RAM ${hx(Math.max(lo, lo2))}..${hx(Math.min(hi, hi2))}`);
  for (const g of a.gestures || [])
    for (const h of b.gestures || []) {
      if (!(meet(g.scope, h.scope) && situationsMeet(g.situation, h.situation))) continue;
      if (g.meaning && g.meaning === h.meaning) continue;        // the same claim twice is allowed
      const mine = new Set(g.atoms.map((x) => x.join("|")));
      if (h.atoms.some((x) => mine.has(x.join("|")))) out.push(`${g.combo} against ${h.combo}`);
    }
  return out;
}

// claims.beyond_shortcuts(): a package's claims without what its shortcuts take through the shortcut layer
function beyondShortcuts(c, p, part) {
  const sc = part.shortcut, ks = new Set(), rs = new Set(), own = new Set();
  for (const u of p.uses)
    if (u.point === "shortcut" && sc.knobs.includes(u.knob)) {
      const i = sc.knobs.indexOf(u.knob);
      ks.add(sc.sound_slots[i]);
      rs.add(sc.record_slots[i]);
      own.add(`${u.key}|${u.knob}`);
    }
  const out = Object.assign({}, c);
  if (c.sound_slots) out.sound_slots = c.sound_slots.filter(([n]) => !ks.has(n));
  if (c.record_slots) out.record_slots = c.record_slots.filter(([n]) => !rs.has(n));
  if (c.gestures) out.gestures = c.gestures.filter((g) => !g.atoms.every((x) => own.has(x.join("|"))));
  return out;
}

// claims.build_holders(): [name, claims, claims to compare with the parts, is a part] for each package, its machine
// named, then the shortcut layer when the build carries it
// claims.own_scope(): the machine a package's scope "machine" names, its id or the stock machine it extends
const ownScope = (p) => { const s = p.uses.find((u) => u.point === "machine.stock"); return s ? s.machine : p.id; };

function buildHolders(packages, layerPart) {
  const out = packages.map((p) => {
    const c = resolveClaims(p.claims || {}, ownScope(p));
    return [p.id, c, layerPart ? beyondShortcuts(c, p, layerPart) : c, false];
  });
  if (layerPart) out.push([layerPart.id, layerPart.claims || {}, layerPart.claims || {}, true]);
  return out;
}

// claims.check_build(): two holders of one build that clash
function checkBuildClaims(holders) {
  const out = [];
  holders.forEach(([a, ca, xa, pa], i) => holders.slice(i + 1).forEach(([b, cb, xb, pb]) => {
    const why = claimClashes(pb ? xa : ca, pa ? xb : cb);
    if (why.length) out.push(`${a} and ${b}: ${why.join(", ")}`);
  }));
  return out;
}

// claims.claim_conflicts(): {tweak id: reasons} for the tweaks whose claims clash with a holder of the build
function claimConflicts(holders, against) {
  const out = {};
  for (const [tid, tc] of Object.entries(against)) {
    const why = holders.flatMap(([, c]) => claimClashes(c, tc));
    if (why.length) out[tid] = why;
  }
  return out;
}

// compose.computed_conflicts(): the ids of the given tweaks this build cannot be installed with (other bytes at the
// same address, or a payload in one of the RAM ranges), plus the declared ones
function computedConflicts(writes, ram, declared, tweaks) {
  const mine = new Map();
  for (const w of writes) fromHex(w.new).forEach((b, i) => mine.set(w.off + i, b));
  const ids = new Set(declared);
  for (const t of tweaks) {
    if (!t.id) continue;
    let clash = (t.writes || []).some((w) => fromHex(w.new).some((b, i) => mine.has(w.off + i) && mine.get(w.off + i) !== b));
    const ap = t.append;
    if (ap && !clash) {
      const lo = parseInt(ap.dest, 16), hi = lo + ap.size;
      clash = ram.some(([a, b]) => lo < b && a < hi);
    }
    if (clash) ids.add(t.id);
  }
  return ids;
}

// compose.compose() without the toolchain: mainOs = the user's MAIN OS (MCBuilder.mainOsOf), frames = frame.json,
// packages = compose.web_package() of each machine, in order (machines 6, 7, ...), tweaks = what the conflicts are
// computed against, parts = compose.web_part() of the builder's parts by id (the shortcut layer, the dispatchers),
// needed only by the builds that use them, claims = the declared claims of those tweaks by id (tools/claims.py's
// tweak_claims). Returns { tweak, info }.
function compose(mainOs, frames, packages, tweaks = [], parts = {}, claims = {}) {
  if (!packages.length) throw new Error("name at least one machine");
  const ids = packages.map((p) => p.id);
  if (new Set(ids).size !== ids.length) throw new Error("a machine is named twice");
  const lay = frames.layout, pay = lay.pay, first = lay.first;
  // added machines are numbered 6, 7, ... in the order given; an extension of a stock machine (notes/66 §3) has the
  // stock machine's number: CHORD, 5, right before them. The tables by machine (the shortcut layer's, the
  // dispatchers') start at the extension when there is one; without one, they are the packages in the order given.
  const kindOf = (p) => {
    const mc = p.uses.find((u) => u.point === "machine"), st = p.uses.find((u) => u.point === "machine.stock");
    if (mc && st) throw new Error(`${p.id}: an added machine or an extension of a stock machine, not both`);
    if (!mc && !st) throw new Error(`${p.id}: no 'machine' entry in uses: not an added machine`);
    if (st && !has(STOCK_EXTENDED, st.machine))
      throw new Error(`${p.id}: machine.stock ${st.machine}: only ${Object.keys(STOCK_EXTENDED).join(", ")} can be extended`);
    return { mc, st };
  };
  const added = packages.filter((p) => kindOf(p).mc), exts = packages.filter((p) => kindOf(p).st);
  if (new Set(exts.map((p) => kindOf(p).st.machine)).size !== exts.length)
    throw new Error(`${exts.map((p) => p.id).join(", ")}: two packages extend the same stock machine`);
  const table = exts.concat(added);
  const tabFirst = exts.length ? STOCK_EXTENDED[kindOf(exts[0]).st.machine] : first;
  const machines = [], blobs = [], symsOf = {}, info = [];
  let codeCursor = pay, bssCursor = pay + lay.bss_off;
  packages.forEach((p) => {
    const codeAt = align4(codeCursor), bssAt = align4(bssCursor);
    const { mc, st } = kindOf(p), i = added.indexOf(p);
    const values = patchValues(p, mc ? { machine_index: first + i, descriptor_base: 76 + 5 * i } : {});
    const { blob, symbols: syms, bssEnd } = place(p.bundle, codeAt, bssAt, values);
    if (codeAt + blob.length > lay.stubs)
      throw new Error(`${p.id}: code and tables end at ${hx(codeAt + blob.length)}, past ${hx(lay.stubs)}`);
    if (mc)
      machines.push({ name: mc.name, image: mc.image, decay: mc.decay_default,
                      knobs: mc.knobs.map((k) => [k.long, k.short, k.default].concat("min" in k ? [k.min, k.max] : [])),
                      update: syms[p.symbols.update], render: syms[p.symbols.render] });
    blobs.push([codeAt, blob]);
    symsOf[p.id] = syms;
    info.push({ id: p.id, index: mc ? first + i : STOCK_EXTENDED[st.machine], desc: mc ? 76 + 5 * i : null,
                extends: mc ? null : st.machine, code_at: codeAt, code: blob.length, bss_at: bssAt,
                bss: bssEnd - bssAt });
    codeCursor = codeAt + blob.length;
    bssCursor = bssEnd;
  });
  let layer = null, dispatch = null;              // the shortcut layer, the dispatchers: in the builds that need them
  if (packages.some((p) => p.uses.some((u) => u.point === "shortcut"))) {
    if (!parts.shortcuts) throw new Error("a machine declares a shortcut, and the page lacks the shortcut layer");
    const at = align4(codeCursor);
    layer = shortcutLayer(mainOs, parts.shortcuts, table, symsOf, shortcutUses(table, parts.shortcuts), at,
                          lay.stubs, tabFirst, added.length ? lay.descn : frames.stock.desc);
    blobs.push([at, layer.blob]);
    codeCursor = at + layer.blob.length;
  }
  if (table.length > 1) {
    const at = align4(codeCursor);
    if (parts.dispatch) dispatch = dispatchLayer(mainOs, parts.dispatch, table, symsOf, at, lay.stubs, tabFirst);
    else {
      const sites = packages.flatMap((p) => p.uses.filter((u) => "hook" in u || "vtable" in u)
        .map((u) => ("hook" in u ? u.hook : u.vtable).at));
      if (new Set(sites).size !== sites.length) throw new Error("two machines take the same point, and the page lacks the dispatchers");
    }
    if (dispatch) {
      blobs.push([at, dispatch.blob]);
      codeCursor = at + dispatch.blob.length;
    }
  }
  for (const p of packages)                       // a package's RAM claim must lie outside the payload
    for (const [lo, hi] of ramClaims(p))
      if (lo < bssCursor && pay < hi)
        throw new Error(`${p.id}: the payload (${hx(pay)}..${hx(bssCursor)}) runs into its RAM claim ${hx(lo)}..${hx(hi)}`);
  checkRamClaims(packages);
  const { writes, append } = machines.length ? fill(frameOf(frames, machines.length), mainOs, machines, blobs, bssCursor)
    : fillAlone(frameOf(frames, 0), mainOs, blobs, bssCursor);
  const skip = new Set([...(layer ? layer.skip : []), ...(dispatch ? dispatch.skip : [])]);
  for (const p of packages) writes.push(...packageWrites(p, mainOs, symsOf[p.id], skip));
  for (const x of [layer, dispatch]) if (x) writes.push(...x.writes);
  writes.sort((a, b) => a.off - b.off);
  checkOverlaps(writes);
  const ram = [[pay, bssCursor]].concat(...packages.map(ramClaims));
  const tid = ids.join("+");
  const declared = packages.flatMap((p) => p.conflicts_declared || [])
    .concat(layer ? parts.shortcuts.conflicts_declared || [] : []);   // none since notes/65 C2: computed
  const holders = buildHolders(packages, layer ? parts.shortcuts : null);       // notes/65: the claims
  const clash = checkBuildClaims(holders);
  if (clash.length) throw new Error(`the build's own claims clash (notes/65): ${clash.join("; ")}`);
  const pool = new Set(tweaks.filter((t) => t.id).map((t) => t.id));
  const others = Object.fromEntries(Object.entries(claims).filter(([i]) => pool.has(i) && !ids.includes(i)));
  const byClaims = claimConflicts(holders, others);
  const conflicts = [...new Set([...computedConflicts(writes, ram, declared, tweaks), ...Object.keys(byClaims)])]
    .filter((x) => x !== tid).sort();
  const symbols = {};
  for (const p of packages)
    for (const k of [p.symbols.update, p.symbols.render, ...(p.keep || [])]) symbols[k] = hx(symsOf[p.id][k]);
  for (const x of [layer, dispatch])
    if (x) for (const [k, v] of Object.entries(x.symbols)) symbols[k] = hx(v);
  const tweak = {
    id: tid,
    order: Math.min(...packages.map((p) => p.order)),
    name: packages.length > 1 ? packages.map((p) => p.name).join(" + ") : packages[0].name,
    description: [`Composed in the browser by composer.js (notes/61): ${info.map((x) => (x.extends
      ? `${x.id} extending ${x.extends} (machine ${x.index})` : `${x.id} as machine ${x.index}`)).join(", ")}, `
      + (machines.length ? "registered together through the registrar runtime"
        : "nothing registered (no added machine, notes/66 §3)") + ", as tools/compose.py composes them."],
    device: "Model:Cycles",
    os: "1.13",
    section: 3,
    version: packages.map((p) => p.version).join("+"),
    conflicts,
    writes,
    append,
    symbols,
  };
  return { tweak, info: { pay, end: bssCursor, image: append.pack.reduce((s, [, k]) => s + k, 0), packages: info,
                          part: layer && layer.info, dispatch: dispatch && dispatch.info, byClaims } };
}

const API = { place, frameOf, fill, fillAlone, segments, bootStub, parameterBlock, packageWrites, shortcutUses, shortcutLayer,
              dispatchLayer, computedConflicts, resolveClaims, claimClashes, buildHolders, checkBuildClaims,
              claimConflicts, compose, fromHex };
if (typeof module !== "undefined" && module.exports) module.exports = API;
if (typeof window !== "undefined") window.MCComposer = API;
})();
