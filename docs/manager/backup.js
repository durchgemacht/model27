/* model27's manager: a project backup of the Model:Cycles, as CONFIG > BACKUP or request 0x6F
   sends it (notes/77 §2): the 96 patterns (type 0x50, index 0 to 95, in order), then the settings
   (0x54), each message with its checksum and length. No page code; shared by the page and the host
   tests. */
(function (exports, S) {
    "use strict";

    var PATTERNS = 96;
    var PATTERN = 0x50, SETTINGS = 0x54;
    var SHOWN = 5;                  /* problems listed one by one; the rest are counted */

    /* What keeps messages from being a whole backup, in words; none when they are one. */
    function problems(msgs) {
        var out = [], i, t;

        if (msgs.length !== PATTERNS + 1)
            out.push(msgs.length + " messages instead of " + (PATTERNS + 1));
        for (i = 0; i < msgs.length; i++) {
            t = S.dumpType(msgs[i]);
            if (t < 0)
                out.push("message " + (i + 1) + " is not a Model:Cycles backup message");
            else if (!S.dumpOk(msgs[i]))
                out.push("message " + (i + 1) + " is damaged (checksum or length)");
            else if (i < PATTERNS && (t !== PATTERN || msgs[i][9] !== i))
                out.push("message " + (i + 1) + " should be pattern " + (i + 1) + (t === PATTERN ?
                         ", is pattern " + (msgs[i][9] + 1) : ", is type " + t.toString(16).toUpperCase()));
            else if (i === PATTERNS && t !== SETTINGS)
                out.push("message " + (i + 1) + " should be the settings, is type " + t.toString(16).toUpperCase());
            else if (i > PATTERNS)
                out.push("message " + (i + 1) + " is one too many");
        }
        if (out.length > SHOWN + 1)
            out = out.slice(0, SHOWN).concat(["and " + (out.length - SHOWN) + " more"]);
        return out;
    }

    function whole(msgs) {
        return !problems(msgs).length;
    }

    /* A backup's id: the SHA-256 of its bytes. The same project gives the same backup, so the same id. */
    function id(msgs) {
        return S.sha256(S.join(msgs));
    }

    /* The settings message of a whole backup: what the Cycles answers request 0x64 with once a
       restore is in. */
    function settings(msgs) {
        var last = msgs[msgs.length - 1];

        return last && S.dumpType(last) === SETTINGS ? last : null;
    }

    exports.PATTERNS = PATTERNS;
    exports.PATTERN = PATTERN;
    exports.SETTINGS = SETTINGS;
    exports.problems = problems;
    exports.whole = whole;
    exports.id = id;
    exports.settings = settings;
})(typeof module !== "undefined" && module.exports ? module.exports : (window.Backup = {}),
   typeof module !== "undefined" && module.exports ? require("./sysex.js") : window.Sysex);
