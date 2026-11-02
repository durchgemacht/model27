/* model27's manager: the export file, a ZIP without compression ("stored"), written and
   read without a library. Unzipped by any tool, it gives the .syx files and library.json as they
   are. No page code; shared by the page and the host tests. Limits of a ZIP without ZIP64: under
   4 GB and 65 535 files. */
(function (exports) {
    "use strict";

    var LOCAL = 0x04034b50, CENTRAL = 0x02014b50, END = 0x06054b50;
    var UTF8 = 0x0800;              /* general purpose flag: names in UTF-8 */
    var CRC_TABLE = null;

    /* CRC-32 as ZIP and zlib compute it. */
    function crc32(data) {
        var c = 0xffffffff, i, n, k;

        if (!CRC_TABLE) {
            CRC_TABLE = new Uint32Array(256);
            for (n = 0; n < 256; n++) {
                k = n;
                for (i = 0; i < 8; i++)
                    k = k & 1 ? 0xedb88320 ^ (k >>> 1) : k >>> 1;
                CRC_TABLE[n] = k >>> 0;
            }
        }
        for (i = 0; i < data.length; i++)
            c = CRC_TABLE[(c ^ data[i]) & 0xff] ^ (c >>> 8);
        return (c ^ 0xffffffff) >>> 0;
    }

    /* A date as MS-DOS keeps it: [time, date], local time, two seconds apart, from 1980. */
    function dos(d) {
        var y = Math.max(1980, d.getFullYear());

        return [(d.getHours() << 11) | (d.getMinutes() << 5) | (d.getSeconds() >> 1),
                ((y - 1980) << 9) | ((d.getMonth() + 1) << 5) | d.getDate()];
    }

    /* entries: [{ name, data: Uint8Array, date }]; returns the ZIP's bytes. */
    function write(entries) {
        var enc = new TextEncoder(), parts = [], central = [], offset = 0, size = 0, out, p, cd;

        if (entries.length > 0xffff)
            throw new Error("too many files for a ZIP: " + entries.length);
        entries.forEach(function (e) {
            var name = enc.encode(e.name), t = dos(e.date || new Date()), crc = crc32(e.data),
                head = new Uint8Array(30 + name.length), dv = new DataView(head.buffer),
                dir = new Uint8Array(46 + name.length), dd = new DataView(dir.buffer);

            dv.setUint32(0, LOCAL, true);
            dv.setUint16(4, 10, true);              /* version needed: 1.0, stored */
            dv.setUint16(6, UTF8, true);
            dv.setUint16(8, 0, true);               /* stored */
            dv.setUint16(10, t[0], true);
            dv.setUint16(12, t[1], true);
            dv.setUint32(14, crc, true);
            dv.setUint32(18, e.data.length, true);
            dv.setUint32(22, e.data.length, true);
            dv.setUint16(26, name.length, true);
            head.set(name, 30);

            dd.setUint32(0, CENTRAL, true);
            dd.setUint16(4, 20, true);              /* made by: 2.0 */
            dd.setUint16(6, 10, true);
            dd.setUint16(8, UTF8, true);
            dd.setUint16(12, t[0], true);
            dd.setUint16(14, t[1], true);
            dd.setUint32(16, crc, true);
            dd.setUint32(20, e.data.length, true);
            dd.setUint32(24, e.data.length, true);
            dd.setUint16(28, name.length, true);
            dd.setUint32(42, offset, true);
            dir.set(name, 46);

            parts.push(head, e.data);
            central.push(dir);
            offset += head.length + e.data.length;
            if (offset > 0xffffffff)
                throw new Error("too big for a ZIP without ZIP64");
        });
        cd = offset;
        central.forEach(function (d) { parts.push(d); size += d.length; });
        p = new Uint8Array(22);
        new DataView(p.buffer).setUint32(0, END, true);
        new DataView(p.buffer).setUint16(8, entries.length, true);
        new DataView(p.buffer).setUint16(10, entries.length, true);
        new DataView(p.buffer).setUint32(12, size, true);
        new DataView(p.buffer).setUint32(16, cd, true);
        parts.push(p);
        out = new Uint8Array(parts.reduce(function (s, x) { return s + x.length; }, 0));
        offset = 0;
        parts.forEach(function (x) { out.set(x, offset); offset += x.length; });
        return out;
    }

    /* The entries of a ZIP: [{ name, data, date }]. Only stored files are read: a compressed one,
       a damaged file or a wrong CRC is an error. */
    function read(bytes) {
        var dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength), dec = new TextDecoder(),
            e = -1, i, n, p, out = [];

        for (i = bytes.length - 22; i >= Math.max(0, bytes.length - 22 - 0xffff); i--)
            if (dv.getUint32(i, true) === END) {
                e = i;
                break;
            }
        if (e < 0)
            throw new Error("not a ZIP file");
        n = dv.getUint16(e + 10, true);
        p = dv.getUint32(e + 16, true);
        for (i = 0; i < n; i++) {
            var method, crc, csize, size, nlen, xlen, clen, local, name, start, data, t, d;

            if (p + 46 > bytes.length || dv.getUint32(p, true) !== CENTRAL)
                throw new Error("damaged ZIP: entry " + (i + 1) + " of " + n);
            method = dv.getUint16(p + 10, true);
            t = dv.getUint16(p + 12, true);
            d = dv.getUint16(p + 14, true);
            crc = dv.getUint32(p + 16, true);
            csize = dv.getUint32(p + 20, true);
            size = dv.getUint32(p + 24, true);
            nlen = dv.getUint16(p + 28, true);
            xlen = dv.getUint16(p + 30, true);
            clen = dv.getUint16(p + 32, true);
            local = dv.getUint32(p + 42, true);
            name = dec.decode(bytes.subarray(p + 46, p + 46 + nlen));
            p += 46 + nlen + xlen + clen;
            if (/\/$/.test(name))
                continue;                           /* a folder */
            if (method !== 0 || csize !== size)
                throw new Error(name + " is compressed; only files stored without compression can be read");
            if (local + 30 > bytes.length || dv.getUint32(local, true) !== LOCAL)
                throw new Error("damaged ZIP: " + name);
            start = local + 30 + dv.getUint16(local + 26, true) + dv.getUint16(local + 28, true);
            if (start + size > bytes.length)
                throw new Error("damaged ZIP: " + name + " is cut off");
            data = bytes.slice(start, start + size);
            if (crc32(data) !== crc)
                throw new Error("damaged ZIP: " + name + " fails its CRC");
            out.push({ name: name, data: data,
                       date: new Date(1980 + (d >> 9), ((d >> 5) & 15) - 1, d & 31, t >> 11, (t >> 5) & 63, (t & 31) * 2) });
        }
        return out;
    }

    exports.crc32 = crc32;
    exports.write = write;
    exports.read = read;
})(typeof module !== "undefined" && module.exports ? module.exports : (window.Zip = {}));
