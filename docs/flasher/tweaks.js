/* Genere par tools/gen_flasher_tweaks.py depuis tweaks/model-cycles_OS1.13/.
 * NE PAS editer a la main : relance le script apres avoir change un tweak. */
window.MC_TWEAKS = {
 "device": {
  "device": "Model:Cycles",
  "os": "1.13",
  "section_sha256": "cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98",
  "stock_syx_sha256": "44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c",
  "cave_refs_ok": [
   {
    "ref": "0x40148564",
    "lo": "0x401485f0",
    "hi": "0x4014862e",
    "why": "pointeur vers la table caractere -> glyphe (256 x 16 bits, 0xFFFF = pas de glyphe) de la petite police de chiffres (0-9 % . /) ; les entrees des caracteres de controle 1..31 ne sont jamais dessinees (largeur 0 dans la table 0x401487ee). browser-scroll (drumkilla) y ecrit 16 o."
   }
  ]
 },
 "tweaks": [
  {
   "id": "control-all-config",
   "order": 49,
   "name": "Control All : choix des pistes",
   "description": [
    "TRACK + TRIG 1-6 retire la piste 1-6 de Control All (TRACK tenu + potard) ou l'y remet ; TRACK tenu, les TRIG 1-6 s'allument pour les pistes qui suivent et restent éteints pour les autres.",
    "La piste active suit toujours, comme sur les Digitakt et Digitone. Les pistes écartées gardent aussi leur machine, leur destination de LFO et PUNCH/GATE quand on les change TRACK tenu.",
    "Choix en RAM seulement : après l'allumage, toutes les pistes suivent de nouveau, comme à l'origine.",
    "Code de Control All Config v1.0 (durchgemacht, MIT, https://github.com/durchgemacht/cycles-control-all-config) dans quatre masques de sprites 48×22 libérés (tools/sprites.py) : 164 o en 0x4018b9c8, 78 o en 0x4018bb48, 138 o en 0x4018cbc8, 114 o en 0x4018d038. Généré par tools/gen_control_all_config.py, notes/58."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "conflicts": [],
   "version": "v1.0",
   "source": "https://github.com/durchgemacht/cycles-control-all-config/tree/fb3969bc98c6496a45cd9b5bd639c88b70a6dd50",
   "symbols": {
    "cac_mask": "0x4018b9cc",
    "cac_held": "0x4018b9cd",
    "cac_skip": "0x4018b9ce",
    "cac_loop1": "0x4018ba00",
    "cac_loop2": "0x4018ba24",
    "cac_loop3": "0x4018ba48",
    "cac_loop4": "0x4018bb48",
    "cac_loop5": "0x4018bb6c",
    "cac_keys": "0x4018cbc8",
    "cac_leds": "0x4018d038"
   },
   "writes": [
    {
     "off": 108666,
     "old": "2f022f034e92",
     "new": "4ef94018bb48"
    },
    {
     "off": 119202,
     "old": "20522f032f02",
     "new": "4ef94018ba24"
    },
    {
     "off": 119544,
     "old": "20522668007c",
     "new": "4ef94018ba00"
    },
    {
     "off": 124882,
     "old": "205248780020",
     "new": "4ef94018ba48"
    },
    {
     "off": 664472,
     "old": "2f022f054e94",
     "new": "4ef94018bb6c"
    },
    {
     "off": 706962,
     "old": "4018d038",
     "new": "4014b364"
    },
    {
     "off": 707022,
     "old": "4018cbc8",
     "new": "4014b364"
    },
    {
     "off": 707624,
     "old": "4018bb48",
     "new": "4014b364"
    },
    {
     "off": 707656,
     "old": "4018b9c8",
     "new": "4014b364"
    },
    {
     "off": 1051368,
     "old": "40024078",
     "new": "4018cbc8"
    },
    {
     "off": 1051544,
     "old": "40023d8c",
     "new": "4018d038"
    },
    {
     "off": 1619400,
     "old": "fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00",
     "new": "4341433100007200123afffa010167242f004eb9400cf8662f004eb94000eb902e804eb940012412588f221fb280670470014e7570004e7520024ebaffca4a80660c20522668007c4ef94001d6fe52827006b08266e24ef94001d75420024ebaffa64a80660c20522f032f024ef94001d5a852827006b08266e24ef94001d5d8200b4ebaff824a80660c2052487800204ef94001ebd8528b7006b08b66e24ef94001ebfe"
    },
    {
     "off": 1619784,
     "old": "fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00ffff",
     "new": "20024ebafe824a80660c2f022f034e924ef94001ac8052827006b08266e24ef94001ac8a20024ebafe5e4a80660c2f022f054e944ef9400a279e528206840000000c7006b08266dc4ef9400a27e2"
    },
    {
     "off": 1624008,
     "old": "fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00ffff",
     "new": "206f00082028000c7202b081660842394018b9cd606e721090817205b0816264222800100801000067360281000000286642720012394018b9cc014113c14018b9cc720012394018b9cd01c113c14018b9cd2f2f00044eb9400760ba588f6020720012394018b9cd0181671813c14018b9cd600c720012394018b9cd0101670470014e754ef940024078"
    },
    {
     "off": 1625144,
     "old": "fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00ffff",
     "new": "2f2f000c2f2f000c2f2f000c4eb940023d8c4fef000c4feffff448d7040c246f00184eb9400cfaf426007400720012394018b9cc70020501670270014879404a8c682f00200252802f002f034eb940005f864fef0010700122025281e3a8819252827006b08266c44cd7040c4fef000c4e75"
    }
   ]
  },
  {
   "id": "trig-preview",
   "order": 2,
   "name": "Trig preview (TRIG + PAGE)",
   "description": [
    "With the sequencer stopped or paused, hold a step and press PAGE: the step sounds with its own note, length, p-locks and sound-lock.",
    "The page does not turn.",
    "It sounds regardless of the trig condition and probability, and through a muted track. The trig is not erased."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "writes": [
    {
     "off": 139502,
     "old": "2f034eb9400724a0",
     "new": "4ef9401489fa4e71"
    },
    {
     "off": 1345018,
     "old": "ffff",
     "new": "4fef"
    },
    {
     "off": 1345021,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "d448d77cfc202e000c2f004eb9400724a0588f4a0067000158202e000c2f004eb940072490588f4a00660001444eb94005481ae288650001384eb9400cf9a826402f0b4eb94006b978588f4a00670001202f0b4eb94006bb18588f4a00660001102f0b4eb94006bdfe588f4a00670001004eb9400cf8662f004eb94000eb90588f2f004eb940012412588f2400203940a7887c4a80670000d82840203940a788884a80670000ca2002e3882200e789d081e589d081e389d081e589d0812a4cdbc01c2d02cf70641b4002cf487800012f0b4eb94006b740508f282b01607a0076000704670000542e03de85204dd1c7122802042f0170"
    },
    {
     "off": 1345268,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "1140020442a742a72f07203940a788882f002f0c2f024eb9400548ce4fef0018221f204dd1c7114102044a8067000014204072022141000c2f004eb940092116588f52830c83000000206600"
    },
    {
     "off": 1345345,
     "old": "ffffffffffffffffffffffffffffff",
     "new": "9e4a856600000c7a20282b015c6000"
    },
    {
     "off": 1345361,
     "old": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
     "new": "8c1b4602cf7000154000744cd77cfc4fef002c74014ef940022ff44cd77cfc4fef002c2f034eb9400724a04ef9400224f6"
    }
   ]
  },
  {
   "id": "trig-cond-order",
   "order": 80,
   "name": "Trig conditions in another order on the knob",
   "description": [
    "A trig held + CHANCE goes through the trig conditions as FILL, !FILL, PRE, !PRE, NEI, !NEI, 1st, !1st, then 1:2 to 8:8, then 1% to 99% (stock: the percentages before the A:B conditions).",
    "Only the knob's order changes: a trig keeps the same condition code as in the stock OS, plays it and shows its name the same way, so patterns are the same with and without the tweak, both ways. The first turn on a trig without a condition still gives FILL; fast turns and FUNC step as many positions as the stock knob steps codes.",
    "The five dots under the value follow the new order too, like a scroll bar of the list.",
    "TrigParameterSet's \"value + delta\" method (its vtable entry) goes to the tweak's code for Trig Cond only; every other parameter keeps the stock method. A 6-byte detour in the value window (0x4001d91c) gives the dots the position in the new order instead of the code, for Trig Cond only.",
    "Code and order in a freed 48x22 sprite mask (tools/sprites.py): 178 bytes at 0x40152d38. Written by tools/gen_trig_cond_order.py, notes/70."
   ],
   "device": "Model:Cycles",
   "os": "1.13",
   "section": 3,
   "symbols": {
    "tco_step": "0x40152d4a",
    "tco_dots": "0x40152d82",
    "tco_order": "0x40152daa"
   },
   "writes": [
    {
     "off": 120092,
     "old": "2045e78ced88",
     "new": "4eb940152d82"
    },
    {
     "off": 758566,
     "old": "40152d38",
     "new": "4014b364"
    },
    {
     "off": 1035800,
     "old": "4000a980",
     "new": "40152d4a"
    },
    {
     "off": 1386808,
     "old": "fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00ffff",
     "new": "41f940152daa72ff5281b030180066f84e757013b0af0008662a202f000ce080723fb280651e61d8202f0010e080d2806a027200703fb2806f02220071b01800e1884e754ef94000a9802045e78ced880c820000001366182f002f012005e080723fb28065066198e1892041221f201f4e7500010203040506071d1e1f202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f08090a0b0c0d0e0f101112131415161718191a1b1c"
    }
   ]
  }
 ],
 "features": [
  {
   "id": "control-all-config",
   "label": "Control All : choix des pistes",
   "desc": "TRACK + TRIG 1-6 retire une piste de Control All (TRACK tenu + potard) ou l'y remet ; TRACK tenu, les TRIG 1-6 montrent les pistes qui suivent. La piste active suit toujours. Choix en RAM.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/cycles-control-all-config"
   },
   "cat": "live",
   "variants": [
    {
     "id": "control-all-config",
     "label": null
    }
   ],
   "license": "LICENSE-Control-All-Config.txt"
  },
  {
   "id": "trig-preview",
   "label": "Ecoute d'un pas (TRIG + PAGE)",
   "desc": "Sequenceur a l'arret (ou en pause), maintiens un pas et appuie sur PAGE : le pas joue avec sa note, sa longueur et ses p-locks.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "drumkilla",
    "repo": "drumkilla/elektron-model-tweaks"
   },
   "cat": "seq",
   "variants": [
    {
     "id": "trig-preview",
     "label": null
    }
   ],
   "license": "LICENSE-elektron-model-tweaks.txt"
  },
  {
   "id": "sampler",
   "label": "SAMPLE machine (Cycles One-Shot)",
   "desc": "One extra machine after Chord: a one-shot sampler for samples on the +Drive. Pick the sample in the PRESET browser (FUNC + MACHINE); it is saved with the sound. While the cursor rests on a sample, the pad and the TRIG keys play it; hold the pad and the track's trigs play it too. COLOR = Start, SHAPE = Length, SWEEP = a DJ-style filter (lowpass / off / highpass), CONTOUR = Reso; the main screen shows the waveform with the start and end marked.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/cycles-one-shot"
   },
   "cat": "sound",
   "package": "sampler",
   "license": "LICENSE-One-Shot.txt"
  },
  {
   "id": "solid",
   "label": "SOLID",
   "desc": "One extra machine after Chord that plays struck sounds: eight modes struck by a mallet, a noise burst or held noise. COLOR = Bright, SHAPE = Body (string, skin, marimba, bar, bell, glass, gliding), SWEEP = Pickup, CONTOUR = Exciter; DECAY is how long the body rings, GATE damps it when the note ends.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/model27"
   },
   "cat": "sound",
   "package": "solid"
  },
  {
   "id": "chips",
   "label": "CHIPS",
   "desc": "One extra machine after Chord that plays chiptune: a square wave that arpeggiates one of Plaits' eleven chords, with a pitch sweep at every trig and a stepped triangle bass. COLOR = Wave, SHAPE = Chord (OCT is one note), SWEEP = Sweep, CONTOUR = Arp (1/4 to 1/32 with the tempo, then 16 to 64 notes a second); MACHINES + PUNCH the bass, MACHINES + GATE up and down.",
   "status": "tested",
   "credit": {
    "kind": "based",
    "who": "Émilie Gillet",
    "repo": "pichenettes/eurorack"
   },
   "cat": "sound",
   "package": "chips",
   "license": "LICENSE-Plaits.txt"
  },
  {
   "id": "maxsaw",
   "label": "MAXSAW",
   "desc": "One extra machine after Chord that plays a huge, wide sawtooth sound: seven sawtooths detuned around the note, with a sub two octaves down. COLOR = Detune, SHAPE = Mix, SWEEP = Tone, CONTOUR = Phase; MACHINES + PUNCH the sub.",
   "status": "tested",
   "credit": {
    "kind": "based",
    "who": "Adam Szabo",
    "url": "https://www.adamszabo.com/internet/adam_szabo_how_to_emulate_the_super_saw.pdf"
   },
   "cat": "sound",
   "package": "maxsaw"
  },
  {
   "id": "terra",
   "label": "TERRA",
   "desc": "One extra machine after Chord that plays wave terrain synthesis: a point circles over a surface and the height under it is the sound. Eight surfaces, five smooth and three made of Plaits' wavetables. COLOR = Surface, SHAPE = Radius, SWEEP = Shift, CONTOUR = Aux (Plaits' second output mixed in).",
   "status": "tested",
   "credit": {
    "kind": "based",
    "who": "Émilie Gillet",
    "repo": "pichenettes/eurorack"
   },
   "cat": "sound",
   "package": "terra",
   "license": "LICENSE-Plaits.txt"
  },
  {
   "id": "vosim",
   "label": "VOSIM",
   "desc": "One extra machine after Chord that plays VOSIM: two vocal-like formants, restarted on every period of the note, from soft vowels to buzzing tones. COLOR = F1 (the first formant), SHAPE = F2 (the second), SWEEP = Follow (the formants follow the note), CONTOUR = Window (from a round to a fading pulse).",
   "status": "experimental",
   "credit": {
    "kind": "based",
    "who": "Émilie Gillet",
    "repo": "pichenettes/eurorack"
   },
   "cat": "sound",
   "package": "vosim",
   "license": "LICENSE-Braids.txt"
  },
  {
   "id": "chordtables",
   "label": "CHORD Tables",
   "desc": "CHORD plays wavetables from the +Drive, one table per pattern: the files 01 to 63 in a folder Wavetables. On a CHORD track, PATTERN + SWEEP picks the pattern's table (0 = CHORD's own, two steps of the knob a table); every CHORD track of the pattern plays it, and SWEEP moves through its waveforms.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/model27"
   },
   "cat": "sound",
   "package": "chordtables"
  },
  {
   "id": "digidelay",
   "label": "Digital Delay (effect)",
   "desc": "A second delay for the delay slot: bright and clean, up to 5.4 s, each repeat a little thinner in the lows. Hold PATTERN and turn Delay Time to switch the pattern's delay between the stock Delay and Digital; Time and Fdbk keep their knobs.",
   "status": "tested",
   "credit": {
    "kind": "based",
    "who": "gialloinfuso",
    "repo": "gialloinfuso/PPPCCC-M-S-Mods"
   },
   "cat": "sound",
   "package": "digidelay",
   "license": "LICENSE-PPPCCC.txt"
  },
  {
   "id": "pots",
   "label": "POTS (effect)",
   "desc": "A delay whose repeats go down an old telephone line: each pass darker and narrower, a little out of tune, fading and now and then dropping out, with a coarse grain on the tail. Hold PATTERN and turn Delay Time to switch the pattern's delay between the stock Delay, Digital and POTS; Time and Fdbk keep their knobs.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/model27"
   },
   "cat": "sound",
   "package": "pots"
  },
  {
   "id": "smpfilter",
   "label": "LP/HP Filter",
   "desc": "A DJ-style filter on any track, modelled on the filter of the Model:Samples, after Volume + Dist: lowpass below the centre of Cutoff, highpass above, off in the middle, with resonance. Hold RETRIG and turn PITCH to give a sound the filter; RETRIG + SWEEP is Cutoff, RETRIG + CONTOUR is Reso, with p-locks, LFO and CC 74 / 71.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/cycles-one-shot"
   },
   "cat": "sound",
   "package": "smpfilter",
   "license": "LICENSE-One-Shot.txt"
  },
  {
   "id": "crush",
   "label": "Crush (Track FX)",
   "desc": "A sample-rate and bit reduction on any track, after Volume + Dist. Hold RETRIG and turn PITCH to give a sound Crush; RETRIG + SWEEP is Rate (off at 0, a hard hold to the right, a softer one to the left), RETRIG + CONTOUR is Bits (off at 127, fewer to the left, one bit at 0), with p-locks, LFO and CC 74 / 71.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/model27"
   },
   "cat": "sound",
   "package": "crush"
  },
  {
   "id": "ring",
   "label": "Ring (Track FX)",
   "desc": "A ring modulator on any track, after Volume + Dist. Hold RETRIG and turn PITCH to give a sound Ring; RETRIG + SWEEP is Freq (the carrier's note, 0 to 127), RETRIG + CONTOUR is Mix (0 dry, 127 the ring alone), RETRIG + COLOR is Wave (sine to square), with p-locks, LFO and CC 74 / 71 / 75.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/model27"
   },
   "cat": "sound",
   "package": "ring"
  },
  {
   "id": "reso",
   "label": "Reso (Track FX)",
   "desc": "A tuned resonator on any track, after Volume + Dist. Hold RETRIG and turn PITCH to give a sound Reso; RETRIG + SWEEP is Pitch (the MIDI note, 60 = C4), RETRIG + CONTOUR Amount (0 off), RETRIG + COLOR Tone, RETRIG + SHAPE Decay, with p-locks, LFO and CC 74 / 71 / 75 / 76.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/model27"
   },
   "cat": "sound",
   "package": "reso"
  },
  {
   "id": "eq",
   "label": "EQ (Track FX)",
   "desc": "A three-band equalizer on any track, after Volume + Dist. Hold RETRIG and turn PITCH to give a sound the EQ; RETRIG + SWEEP is the Mid's frequency, RETRIG + CONTOUR its gain, RETRIG + COLOR the Low shelf, RETRIG + SHAPE the High shelf, each 12 dB either way, with p-locks, LFO and CC 74 / 71 / 75 / 76.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/model27"
   },
   "cat": "sound",
   "package": "eq"
  },
  {
   "id": "cpu",
   "label": "CPU page",
   "desc": "A page that shows how much of the Model:Cycles' time the sound takes. SETTINGS, then the list with USB mode, LCD, LED and Contrast: its last row, CPU, opens it; Return closes it. CPU is the share of the last half second, with a bar and a mark at 85 %, where the screen and the knobs start to lag; PEAK the dearest moment since the page opened; TRACK FX and EFFECTS their own shares.",
   "status": "tested",
   "credit": {
    "kind": "based",
    "who": "TinyGregAudio",
    "repo": "TinyGregAudio/Model-TG"
   },
   "cat": "screen",
   "part": "cpu",
   "license": "LICENSE-Model-TG.txt"
  },
  {
   "id": "resample",
   "label": "RESAMPLE",
   "desc": "SETTINGS + RECORD opens a page that records a track, the main mix or USB and saves the take as a sample in /recordings, named in the stock name editor; TO Tn puts it on the selected SAMPLE track.",
   "status": "tested",
   "credit": {
    "kind": "based",
    "who": "TinyGregAudio",
    "repo": "TinyGregAudio/Model-TG"
   },
   "cat": "sound",
   "part": "resample",
   "license": "LICENSE-Model-TG.txt"
  },
  {
   "id": "transpose",
   "label": "Transpose",
   "desc": "MACHINES + TRIG 15 / 16 move the TRIG keyboard an octave down / up, two at most; MACHINES + TRIG 8 / 9 / 11 / 12 make the active track's pitch jump -7 / -5 / +5 / +7 semitones, at once; the keys' LEDs dim, mid or full show it; the MACHINES menu opens on the release of MACHINES.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/model27"
   },
   "cat": "live",
   "part": "transpose"
  },
  {
   "id": "perform",
   "label": "Perform Kit",
   "desc": "SETTINGS + PATTERN switches a mode in which a pattern change no longer changes the sound: the next pattern's trigs play on the sounds you have right now; a checkered stripe at the left edge of the screen shows it. Nothing is kept unless the pattern is saved.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/model27"
   },
   "cat": "live",
   "part": "perform"
  },
  {
   "id": "trig-cond-order",
   "label": "Trig conditions, A:B before the percentages",
   "desc": "A trig held + CHANCE goes FILL ... !1st, then 1:2 ... 8:8, then 1% ... 99%, and the five dots under the value follow that order. A trig keeps the same condition as on the stock OS.",
   "status": "tested",
   "credit": {
    "kind": "by",
    "who": "durchgemacht",
    "repo": "durchgemacht/model27"
   },
   "cat": "seq",
   "variants": [
    {
     "id": "trig-cond-order",
     "label": null
    }
   ]
  }
 ],
 "packages": {
  "sampler": {
   "id": "sampler",
   "name": "SAMPLE machine: sampler for samples on the +Drive, one shot or loop, forward or reverse (Cycles One-Shot 0.18)",
   "order": 27,
   "version": "0.18",
   "symbols": {
    "update": "sampler_update",
    "render": "sampler_render"
   },
   "keep": [
    "smp_hook_open",
    "smp_hook_preview",
    "smp_hook_pad_on",
    "smp_hook_pad_off",
    "smp_hook_key_on",
    "smp_hook_key_off",
    "smp_hook_save2",
    "smp_hook_save1",
    "smp_hook_load",
    "smp_hook_tick",
    "smp_main_draw",
    "smp_knob_draw",
    "smp_note_draw",
    "smp_hook_pan",
    "smp_hook_pan_all",
    "sample_pictures",
    "sample_hook_tick"
   ],
   "patch_points": [
    {
     "symbol": "cm_machine_index",
     "kind": "machine_index"
    },
    {
     "symbol": "cm_descriptor_base",
     "kind": "descriptor_base"
    }
   ],
   "uses": [
    {
     "point": "machine",
     "name": "SAMPLE",
     "image": 4,
     "pictures": "sample_pictures",
     "decay_default": 127,
     "knobs": [
      {
       "long": "Start",
       "short": "STRT",
       "default": 0,
       "min": 0,
       "max": 120
      },
      {
       "long": "Length",
       "short": "LEN",
       "default": 120,
       "min": 0,
       "max": 120
      },
      {
       "long": "Cutoff",
       "short": "FREQ",
       "default": 64
      },
      {
       "long": "Reso",
       "short": "RESO",
       "default": 0
      }
     ]
    },
    {
     "point": "shortcut",
     "key": "MACHINES",
     "press": "PUNCH"
    },
    {
     "point": "shortcut",
     "key": "MACHINES",
     "press": "GATE"
    },
    {
     "point": "browser.open",
     "hook": {
      "at": "0x400a6602",
      "stock": "4eb9400a3052",
      "op": "jsr",
      "symbol": "smp_hook_open"
     }
    },
    {
     "point": "pad.note",
     "hook": {
      "at": "0x4001d05e",
      "stock": "4feffff07205",
      "op": "jsr",
      "symbol": "smp_hook_pad_on"
     }
    },
    {
     "point": "pad.note",
     "hook": {
      "at": "0x4001d0fc",
      "stock": "4feffff47005",
      "op": "jsr",
      "symbol": "smp_hook_pad_off"
     }
    },
    {
     "point": "key.note",
     "hook": {
      "at": "0x40019e7a",
      "stock": "4feffff07005",
      "op": "jsr",
      "symbol": "smp_hook_key_on"
     }
    },
    {
     "point": "key.note",
     "hook": {
      "at": "0x40019c84",
      "stock": "4feffff07005",
      "op": "jsr",
      "symbol": "smp_hook_key_off"
     }
    },
    {
     "point": "browser.preview",
     "hook": {
      "at": "0x400a6426",
      "stock": "4eb9400a3052",
      "op": "jsr",
      "symbol": "smp_hook_preview"
     }
    },
    {
     "point": "sound.record",
     "hook": {
      "at": "0x4005afa0",
      "stock": "4feffff448d71c00",
      "op": "jmp",
      "symbol": "smp_hook_save2"
     }
    },
    {
     "point": "sound.record",
     "hook": {
      "at": "0x4005b054",
      "stock": "4feffff448d71c00",
      "op": "jmp",
      "symbol": "smp_hook_save1"
     }
    },
    {
     "point": "sound.record",
     "hook": {
      "at": "0x4005aecc",
      "stock": "4feffff448d71c00",
      "op": "jmp",
      "symbol": "smp_hook_load"
     }
    },
    {
     "point": "screen.tick",
     "hook": {
      "at": "0x400075f0",
      "stock": "4eb940076be4",
      "op": "jsr",
      "symbol": "sample_hook_tick"
     }
    },
    {
     "point": "main.pan",
     "hook": {
      "at": "0x4001ab14",
      "stock": "2f032f02d880",
      "op": "jsr",
      "symbol": "smp_hook_pan"
     }
    },
    {
     "point": "main.pan",
     "hook": {
      "at": "0x4001ab52",
      "stock": "2f022800d887",
      "op": "jsr",
      "symbol": "smp_hook_pan_all"
     }
    },
    {
     "point": "view.main",
     "vtable": {
      "at": "0x400ffe30",
      "stock_ptr": "0x4001b22a",
      "symbol": "smp_main_draw"
     }
    },
    {
     "point": "view.knob",
     "vtable": {
      "at": "0x4010053c",
      "stock_ptr": "0x4001e40a",
      "symbol": "smp_knob_draw"
     }
    },
    {
     "point": "view.note",
     "vtable": {
      "at": "0x40102578",
      "stock_ptr": "0x400299de",
      "symbol": "smp_note_draw"
     }
    },
    {
     "point": "memory.ram",
     "range": [
      "0x43800000",
      "0x46700000"
     ]
    }
   ],
   "conflicts_declared": [
    "sample-preview",
    "sample-preview-st"
   ],
   "claims": {
    "sound_slots": [
     [
      25,
      "machine"
     ],
     [
      26,
      "machine"
     ],
     [
      27,
      "machine"
     ],
     [
      32,
      "machine"
     ]
    ],
    "record_slots": [
     [
      18,
      "machine"
     ],
     [
      24,
      "machine"
     ],
     [
      25,
      "machine"
     ],
     [
      26,
      "machine"
     ],
     [
      27,
      "machine"
     ]
    ],
    "formatters": [
     [
      53,
      "all",
      "Cutoff"
     ]
    ],
    "pictures": [
     [
      53,
      "all",
      "Cutoff"
     ],
     [
      54,
      "all",
      "Reso"
     ]
    ],
    "ram": [
     [
      1132462080,
      1181745152
     ]
    ],
    "views": [
     [
      "main",
      "machine",
      ""
     ],
     [
      "knob",
      "machine",
      ""
     ],
     [
      "note",
      "machine",
      ""
     ]
    ],
    "gestures": [
     {
      "combo": "MACHINES + PUNCH",
      "atoms": [
       [
        "MACHINES",
        "PUNCH"
       ]
      ],
      "situation": "any",
      "scope": "machine",
      "meaning": "Loop",
      "replaces": null
     },
     {
      "combo": "MACHINES + GATE",
      "atoms": [
       [
        "MACHINES",
        "GATE"
       ]
      ],
      "situation": "any",
      "scope": "machine",
      "meaning": "Reverse",
      "replaces": null
     }
    ]
   },
   "bundle": {
    "code": "4fefff9848d77cfc246f0070263c0000031c240a0682bdcf77d84c432002783c266f00742f6f006c004c20024c024800e5882a040685000000002840d9fc800017ec20544a886700051a362800542002e78877c32040d1fc423087fc082800000003672c70424c0208002040d1fc800015ee30100800000a670e22000883000802810000010086810800000b660003ea223c534d5031b2aa002c660003f6712b00247c444c0268004df9000000004a806d0003c071c0207c4011d84c41f00c00255002504aaa003867000366203c012c0f26223c001f7c5c2e3c7fffffff207c82581e4b227c803ef8b82540027825400274254102842541028025470294254702902548027c254902884a6b001e670003fc22142e3c200000002079800017e42a7c20000000254702a47e424c027800227c600000007001254d029c2a7c800015e2254902a02540004843f9000000002a7578004a3128006600056442012e2a03182f470060420041f9000000001181280041f9000000001180280041f900000000118028002f0d4eb9000000002f400044588f4a8067000294322b00162003ee887e02ce8070093f4100442203e0a920477e01c2872e08716f00442f4000348e812f4700500c80000078006e0004d04aaf00346d000554322b00183f41003273410c81000078006e0004984a816d000556d2af00342f41002e0c81000078006e000374206f0040720e4c0218002028002c41f9000000002f400048202f0050e2882e2f00482f4100542f400064203c000078004c4078014c407807302f0044226f00542a6f0054dbc83b6f003200023b6f006600042f41005c2f4700582e2f0034222f005c2b47000633808800202f005c4c0708002e2f002e4c0718002f400044202f00342041222f00584c0108004c0718002e2f00442f40005c203c0000780022414c40780722082f4700544c4018012041222f0054d2af005c2b41000a2f2f0050487098002f014bf9000000002f2f0054206f00502f2800282f054eb900000000226f0058202f007806800000003041e90030226f00782b902c004fef00184299b08966fa43f9000000004a31280067084aaa0034670001dce08b7e01ce832f072f054eb900000000716b0022508f736b00140680ffffc000e788e189d0810680ffc00000d0af004c0c80007f00006f0000fa707f484020752c004a88670000fe2208260873c1424348430680ffc40000204142814a806c0000be0680000c000053814a806df42e004247484771c049f90000000022747c0028747c0499c92e0c4c07080042404840d0894a816d0001a8e3a8220042414841224132083e09c2c0c0c3c6c73e08424148412840300948434243c0c741f40800d1c3487018002f054eb900000000508f43f648004aa9001c670e4aaa003466084aaa00386700035c716b001c0686000000002f400074736b001a2f46006c4cd77cfc2f4100704fef00684ef90000000042b6481c4bf9000000006000fed00c80000c00006d00ff480680fff40000528160ec4a806c00ff0820752c0042804a886600ff0676010680ffc4000042814a806d00ff1060c842806000fc3e08830009028000000200223c534d50318680b2aa002c6700fc0e420741f9000000007c444c0268004df90000000042b6481c1187280041f9000000001187280041f9000000001187280041f900000000118728002046d1fc000000002f084eb900000000588f227c534d50312549002c712b00244a806c00fbc46000ff7e4200138028004a946600fe1c72012541003c6000fe1222142e3c200000002079800017e42a7c7fffffff254702a47e424c027800227c200000004280254d029c2a7c800015e2254902a02540004843f9000000002a7578004a3128006700fc08600001664481e2a86000fe567e424c027800227c800015ee363178006000fada206f0040720e4c0218002e3c000078002028002c2f47002e41f9000000002f400048202f0050e2882f4100542e2f00482f400064203c000078004c4078014c407807302f0044226f00542a6f0054dbc83b6f003200023b6f006600042f41005c2f4700582e2f0034222f005c2b47000633808800202f005c4c0708002e2f002e4c0718002f400044202f00342041222f00584c0108004c0718002e2f00442f40005c203c0000780022414c40780722082f4700544c4018012041222f0054d2af005c2b41000a2f2f0050487098002f014bf9000000002f2f0054206f00502f2800282f054eb900000000226f0058202f007806800000003041e90030226f00782b902c004fef00186000fc82223c00007800d2af00342f41002e0c81000078006f00fb6c6000feda322b0018203c000078002f4000343f41003273410c81000078006f00fb3260c4b4b940a700c46600fa96227940fb5a044a896700fa8a71a900260c80000000006600fa7c2f092f4100402f48003c4eb9000000002f6a03180064588f222f003c206f003808000000671cb08d67184a8167144a8867107e644c02780041f0781cb1c16700026242016000fa3e322b001842af00343f41003273410c81000078006f00faac6000ff3e4281d2af00342f41002e0c81000078006f00faac6000fe1a306b00162269002c760e70ff4c023800b08957c149f9000000003a6b00182f4900447f48717438002f4700404481b0876700025a714d73812f40004c2f410050223648382e3c000078004c4718004c4718013988380041f43800314d0002316f005200042f410048222f004cbe816d0001764a816d0001767effbeaf00446700026ed2b438060c81000078006e0001642e2f00484c0108004c017800223c000078002a474c410800d08d90b4380a2f002f054eb900000000508f4bf9000000004a3528006700fbe04ab6481c6700fbd84aaa00346600fbd04aaa00386600fbc841f9000000004a302800660001422079800017e44a88670002967064780c4c02080042074c02480045f9000000004870081c4eb9000000002f004eb900000000508f1b87280041f9000000002240700121894800158028004a896700fb6ad9c34a6c00046700029e736b00160c81000078006f000284223c00007800716b00180c80000078006f00021a203c00007800d0810c80000078006f06203c000078002a29002c263c000078002e3c000078000686000000004c4358024c43580526014c0238004c0028004c0518004c0508004c4738034c472802d68121834804d48021824808716b001c2f400074736b001a2f46006c4cd77cfc2f4100704fef00684ef90000000022076000fe8e42816000fe882e2f0048223c000078004c0108004c017800223c000078002a474c410800d08d90b4380a2f002f054eb900000000508f6000fe9672012a406000f7dcb4b940a700c46600feb8207940fb5a044a886700feac71a800260c80000000006600fe9e2f084eb900000000588f080000006700fe8c716b001c0686000000002f400074736b001a2f46006c4cd77cfc2f4100704fef00684ef90000000043f438007f4d7381716900022f4900482f47004c2f410050be806600fd98226f004871690004b0816600fd8a4bf9000000004a3528006600fe14716b001c0686000000002f400074736b001a2f46006c4cd77cfc2f4100704fef00684ef900000000206f0040b1fc000078006f7e307c7800d2880c81000078006f06223c000078002e014c0078004bf90000000022472e084c007800202f00484c01080022082f4700442e2f00484c0718002f40004020092041223c000078004c4108002240202f00444c410800222f004048711800487008002f054eb9000000004fef000c4a3528006700f9346000fd524a886c8291c86000ff7e4a806c00fdea42806000fde442017601700c0686000000004c02080041f9000000001b8128001183280041f90000000042b00800716b001c2f400074736b001a2f46006c4cd77cfc2f4100704fef00684ef9000000004a816c00fd8042816000fd7a222c00066000fd724fefffac48d77cfc246f005c223c0000031c240a0682bdcf77d84c4120027a3c7844262f0058286a00384c0258004c0248002a45dbfc000000000684000000004aaa0034660002a84a8c6600036441f9000000004aad001c6700048a202a02304a806d0004ac0c8000003fff6214202a02344a806d0004f60c8000003fff6300046447f90000000041f9000000004a332800660003324206118628004879000000004879000000002f0d4eb9000000002f034879000000002f0a4eb9400a9f582f0a4eb9400a92522f0a2f034eb9400a94304fef002449f9000000004a342800670001ea2043721f20184a806d000324ea807cff4c01080053812140fffcbc8166e6420741f9000000001987280049f058004aac001c670003fe720c4c0218004df900000000227618004a89670003e8202c0008286c00042f40003c2f4c0044908c4a806f0003d049f900000000d9c12229002c2f410048222c0008286c0004b2af00486f04222f0048b28c6f0003a84df058002c2e000c4c406807202e00242c2900302f4000502f47004c2f4600404a80670003c8202f003c538090872f40002c4df9000000004aaf0040670003ce2f4e004c20362c004a806762b0af0040675ce0882f40003c202f0040e9882f4000404aaf003c66067c012f46003c202f003c2e2f00404c407007202f002c7c0c2f4700402e2f002ceca8028700000fff2f47003c2e2f00402c2f003c4c0708004c0768007e0ceeaed0862f40002c2f4c003cb9ef002c6c082c6f002c2f4e003cb2af003c6e08200153802f40003c4df058004aae002856c04aaf005056c671007f064480d080448780872f002f012f0c2f2f00542f2900282f0d2f41004c2f4800482f4900504eb9000000004fef0018206f0030226f00384aae002467000296202f003453802a6f004cd1c590af003c43e900302b912c002140000c700e4c0208003c7c01801a28001f214e00202040d1fc00000000208c178528002f0a2f034eb9400a967a2f4300642f4400604cef7cfc00084fef005c4ef9000000004a8c6700009c41f90000000047f9000000004a302800670001604206387c0001178628002245d3fc000000004a9156c04480118028004879000000004879000000002f0d4eb9000000002f034879000000002f0a4eb9400a9f582f0a4eb9400a92522f0a2f034eb9400a94304fef00244a8c6700fd742043428120184a806d0000c2ea804c01080052812140fffc7020b0816700fd5420184a806ce6600000a447f9000000004a332800670000b44207387c000141f900000000178728006000ff6441f9000000001030280047f9000000004a00670000c6420111812800178128004879000000004879000000002f0d4eb9000000002f034879000000002f0a4eb9400a9f582f0a4eb9400a92522f0a2f034eb9400a94304fef0024204342816000ff5806800000001fea807cff4c01080053812140fffcbc816600fcbe6000fcd406800000001fea804c01080052812140fffc7020b0816600ff3c6000fc8a2245d3fc000000004a9156c041f90000000044806000febc4a33280056c12245d3fc0000000042074a9156c07301178728004480448128416000fe9842064a33280056c111802800178628007301448128414879000000004879000000002f0d4eb9000000002f034879000000002f0a4eb9400a9f582f0a4eb9400a92522f0a2f034eb9400a94304fef00244a8c6700fbf86000fe8242b0581c200320430680000000804298b08866fa2f044eb900000000588f4a80667e4cd77cfc4fef00544e7544806000fb5242b0581c4205178528006000fdaa2a6f004cd1c543e90030202f003c908c2b912c002140000c700e4c0208003c7c01801a28001f214e00202040d1fc00000000208c6000fd6e2e2f0044deaf004c2f47002c6000fc3844800c8000003fff6200fb0c6000ff6a2f4e004c6000fc9c2f43005c2f4400584cd77cfc4fef00544ef900000000598f2f0272ff206f000c2028002cb280674c22680014243c000001c1220952814c02180090a8000cb0816e324a806f3a22094841424175e80018484042402f42000475e8001082af0004204191c241f008ff20084c410000241f588f4e75241f203c000001c0588f4e75241f4280588f4e754fefffb0206f005448d77cfc246f005c2a68000422680008260922280014968d2c680018240e2f4d003842424842266f00602a68002c2f4900342828000c2f4100304aa80028670002c67affba8d670004d243f9000000002f2f00542f4900484e91588f0c800000017f6f00059e226f005470ff206f00542340002c200252802228001024002a01ed8a424548452c2900342f41003c220455819480224543f12801202f0030ed8824094242484290af0030d4802e025c872f4200402a47dbc14a816d0002aa4a876f000086200142854c430802286f00542f4e00482f4b004cb28d6c0002c82047200391c59082b1c06c022008204d91c1b1c06c022008282c002426544a84670003702c40ddc54a806f2041f25a002a2f003406857fffffff9a8243f2ea0047f35a0030d3558bb1c966f82a0ed2804a866d08d082b680670002984282bdc76d982c6f0048266f004c206f0054262800202f08226f00484e91588f91c822402800203c000155564c0048007018242f003c2202e0a94be9ffc02f4d002c286f0058c2fc000c303318003a3318023e3318043c331806c1f28a00cbf28a02cff28a04cdf28a06d0853a3318083233180ad087d086cbf28a08c3f28a0ad085d0810c830000017f6f7cb3fc0000017f6f00022c28802002d08eb08255c2d1ef00305389588c0684fffeaaaa750291c2b3ef002c670000d2240070182202e0a9c2fc000c303318003a3318023e3318043c331806c1f28a00cbf28a02cff28a04cdf28a06d0853a3318083233180ad087d086cbf28a08c3f28a0ad085d0810c830000017f6e844a836f0002162c3c000155567e0a4c0368002a3c0000c000eeae32069a86c2c67c0feca9c2c5d281eca9b3fc0000017f6f00018c4a806d0001b22c007a0f028600007fffeaa84c0108004c061800eaa9d0810c830000017f5fc12880730196812002d08eb08255c2d1ef00305389588c0684fffeaaaa750291c2b3ef002c6600ff32220eed89226f0054d1e9000c2029002c234300202348000cd2af003c2341001072ffb280670001ae5388b1c06f08226f005442a9001c4cd77cfc70014fef00504e7572ffb28d67000260206f00542002528024002c280034206f0054ed8a43f900000000222800102a01424548452f4900442f41003c2204558194802242202f003043f15801ed8824094242484290af0030d4802e025c872f4200404a816c00fd5a206f0054242800304a82660001822204200ad2815880204a90814258b1c066fa7a0242819a84ba876c00fdb8286f00542f4e00482f4b004cb28d6d00fd3c2c6f0048266f004cba876c00fd982a6f004041f25a0043f2da0c4258b3c86700fd844258b3c866f26000fd7a4a816f00fd664a8467082f4600342c2f0038262f003496862f4600387cff4282bdc76d00fce46000fd48223c000080004a896f667e0a2c04eeae2e3c0000c0003a069e86cac67c0fecadcac7da85ecad4c051800eca94a806c00fe522a00448520057e0f028000007fffeead4c0158004c0108000c830000017f5fc1eea87301d0854480288096816000fe484281b3fc0000017f6e00fe10609642816000fe084a806f1c206f0038d1c24df0080041f38a0043f25a0047f3ea0032d8b1cb66fa2c40ddc56000fc942429000824492269000422029289b2886e00fe50262a0034200890812540000c4a836d1a4aaa0024670001a4206f005472ff2543000821410034220392894c410802206f005470012142000c4cd77cfc2140003070014fef00504e7520014c4308024a82670001504a876f00fc44286f0054d48342852f4e00482f4b004c6000fbc02c280034200241f90000000052802f480044206f00542400ed8a222800102a01424548452f41003c220455819480202f0030224543f12801ed8824094242484290af0030d4802e025c872f4200406000fb4a3c02206f0054200252802a002e3c00000180ed8d222800102401424248422f41003c72ff21410034ccfc0180220455819a80204541f02801242f003042464846202f00304c072800ed882a08204241f068024245484590af00302408d4844c432802206f0054da802e0570ff2f4500405c8752822c024c0368002146002cb0866700009643f9000000002a467cff2f4900446000fab8206f00542002528024002c280034206f0054ed8a222800102a01424548452f41003c2204558194802242202f003043f15801ed8824094242484290af0030d4802e025c872f4200406000fd1442854a876f00faf4286f00542f4e00482f4b004c6000fd3a2a6f005472ff206f005422432b430004214100342602220392896000fe5441f9000000002a47dbc12f4800446000fa244feffff448d7001c202f0020242f0018206f0010222f0024b4806c022002262f001c4a836d0000aeb0835ec27801c88120af0014214300042140000842a8000c42a80010750222442144002444822142001c4a846740226f0018b3ef00206f3c93c97402c282214900202401e28a214200284a81663e78ff9083214400342140002c4cd7001c42a80030216f001800384fef000c4e754aaf001c6ec67402c282327c0180214900202401e28a214200284a8167c278ff70ff214400342140002c4cd7001c42a80030216f001800384fef000c4e7542836000ff504aaf000856c0206f000471004480214000284e752f02202f000c206f00080c8000000400641c203c000004002200740fe5a97411e4a8241f21400014214100184e750c800008000063e270084840740f2200e5a97411e4a8241f21400014214100184e754feffff42f0a2f02206f00184aa8001c670000944aa800306600008c222800082028002c226800042f4100109289b2806674b0af001c676e2f082f48000c2f4900104eb900000000588f206f0008226f000c0c800000017f6f4c3028001822280014243c000001804c021800c0fc018042404840244045f21802200ad0a8000cb0af001c6c04202f001c4aa800246720222f0010b0816d38242f00109481214200042141002c241f245f4fef000c4e75222800389289b0816d0cd3c1214900082141002c60e02200d3c12149000860f0242f0010220094812142000460c44fefffe8206f001c48d7001c4aa8001c670a2268002c70ffb089670a4cd7001c4fef00184e7520280038b0af00246e46222f00204a816d4ab2806ce02428000c2f42000c4aa80024673c262800082f43001096812f430014b4836c4821410004b0af0010670222404cd7001c214900344fef00184e75222f0020202f00244a816cb6428160b228280004240094842f4200142f440010b4af000c6f0821400008200160bc226f000c280098812f44000c93ef0014214000087001214100042140003024094c44280378ff214400342143000c4cd7001c4fef00184e75206f00042028001c4a80671e4879000000002f2f00102f2f00102f084eb9000000004fef001070014e75206f000822080681000001004298b28867ec4298b28866f460e4206f000442a80004429042a8001442a8001042a8000c42a8000842a8002c42a8002842a8002442a8002042a8003c42a8003842a8003442a8003042a8001842a8001c42a800404e754fefffc4226f004448d7047c206f00402809b3fc00007f006f60283c00007f0020040680ffffc000242800184a8066604a82673c202800384a806700043a220076e14c43180121680030000821680034000c42a8001442a8001042a8002c2140002042a80038214100242168003c00284cd7047c4fef003c4e754a896ca2428420040680ffffc000242800184a8067a0262f00480c8300007f006e0001ae4a836d0003782203e6837a0beaa17783c2fc04082c010681000000000686000000002f4300342f46001c2f4100204a806d0001ae26002200ee81d68377830c80000000ff6e00036a7c177a02eda8283c7fffffff2f44002c2f450038224152897bc979c1246f0020e78de78c222f00202245d5c5d3ef001c2f4a0018d28424412f490028d8af001c2252246f00182a1224442f520030246f00289a892f4500202c2f0020e0862a122441222a00049aaf0030246f00182f4600202f45001c2a2a000424449a81282a00042f450024246f00282c2f0024e0862a2a00049a842f4500182a2f001ce0852f4600242f45001c2a2f0018e0852f4500182a2f001c2c2f00204c0358004c0368002f45001c2f4600202a2f00182c2f00244c0358004c036800262f001cd3ef0020d6af0030d885d28693c392842a09e081e0852c2f00344c0658004c061800d6852241d3c44a82660001b022007a1f4c4518017c0142a80004429021460040214300082149000c42a8001442a8001042a8002c2142002021410024214300302149003421400038216f002c0028216f002c003c216f003800184cd7047c4fef003c4e75263c00007f007a0b2203e683eaa17783c2fc04082c010681000000000686000000002f4300342f46001c2f4100204a806c00fe5626042204ee81d6837783b3fc00003f006f0001d27a012f450038203c00004000224152897bc990847817e9a8e78d79c1246f0020222f002042af002ce78c2245d5c5d3ef001c2f4a0018d2842f4900282441d8af001c2252246f00182a1224442f520030246f00289a892f4500202c2f0020e0862a122441222a00049aaf0030246f00182f4600202f45001c2a2a000424449a81282a00042f450024246f00282a2a00049a842f4500182a2f001ce0852f45001c2a2f0018e0852f4500182c2f0024e0862a2f001c2f4600242c2f00204c0358004c0368002f45001c2a2f00182f4600202c2f00244c035800d3ef00204c036800262f001cd6af0030d885d28693c392842a09e081e0852c2f00344c0658004c061800d6852241d3c44a826700fe54282f002c741f7a1f21680030000898a8003c21680034000c2168003c00284c4248042428003821400038216f002c003c21420020220092824c4518012a039aa800302144002c214300302c099ca80034ea852141002421490034ea862f45001c2f460020216f001c0010216f00200014216f003800186000fe2842832203e6837a0beaa17783c2fc04082c010681000000000686000000002f4300342f46001c2f4100204a806c00fc8a6000fe32203c7fffffff78022f40002c2f4400386000fc9a7c0142af002c203c7fffffff2f4600386000fc864cd7047c42a80004429042a8001442a8001042a8000c42a8000842a8002c42a8002842a8002442a8002042a8003c42a8003442a8003042a8001842a8001c42a800404fef003c4e75206f0004202800184a80671020104a806d220c8000003fff6f0470014e75202800044a806d1a0c8000003fff5ec0710044804e7544800c8000003fff6edc60de44800c8000003fff5ec07100448060e2206f0004226f0008202800184a8067664aa80040671253804a80675c4280208042a8000442a80040203c7fffffffb0a80020671470022140001c2f4900082f4800044ef9000000004aa8002466e64aa8002c66e0202800284a80662c4a8056c0710044802140001c2f4900082f4800044ef9000000004e752011e28042a8000442a80040208060a00c807fffffff67cc700260a200004fefffd448d75cfca9802f400028a93c000000a0226f0030206f0034241126290004282900082a29000c2c2900102e290014247c80000000287c7fffffff70202229001c0c81000000016700005c0c8100000002670000aa2210e281a102a6040800a6040800a301a6850900a6850900a1c2a48a0800a3cba103a6440800a6440800a1c3a102a6040800a6040800a1c1a101a20c0800a1c120c1d886da8753806600ffb6600000de2210e281a102a6040800a6040800a301a6850900a6850900a1c2a48a0800a3cba103a6440800a6440800a1c3a102a6040800a6040800a1cba101a20c0800a64a0800a64c0900a1c120c1d886da8753806600ffae600000862c2900202e2900282210e281a102a6040800a6040800a301a6850900a6850900a1c2a48a0800a3cba103a6440800a6440800a1c3a102a6040800a6040800a1cea101ac4a0800ac4a0800a1cba10ea6470800a1cea10ea20a0800a1cba101a6460800a1c1a101a20c0800a1c120c1d8a90010daa90014dca90024dea9002c53806600ff86228223430004202f0028a9004cd75cfc4fef002c4e75598f2f027005222f000cb0816408241f4280588f4e7541f9000000004a30180067ecb2b940a700c466e4207940fb5a044a8867da71a800260c800000000066ce2f082f4100084eb900000000588f222f00040800000067b6420241f9000000007001226f0010528911821800340941f90000000011821800241f588f4e75598f2f027005222f000cb0816408241f4280588f4e75b2b940a700c466f0207940fb5a044a8867e671a800260c800000000066da2f082f4100084eb900000000588f222f00040800000067c2420241f9000000007001226f0010528911821800340941f90000000011821800241f588f4e752f027205202f0008b280651641f900000000222f000c528175b008007381b2826704241f4e75420174011181080041f90000000011820800241f4e75222f0004226f000841f9000000004aa8001c670a2010b2806204b3c0621041e8003cb1fc0000000066e442804e7570014e752f02206f0008202800044a80676e122800013241738153814a8167667201c2804a816658723fb2af000c6450222f000c0681ffffffc0b08162420c8002f00000623a2068000822080681fffff0600c810002de60622622097401b581226f001022807001226f00142288206f00184a0157c1241f7301448120814e75241f42804e75720360984feffff0226f001448d70c0c2429004808020000660a4cd70c0c4fef00104e7541f900000000428045f90000000072344c0018004ab218006704b490676e528041e80034b1fc0000000066e2428072344c0018004ab21800671652800c800000008067b272344c0018004ab2180066ea77e90046c0fc00342582180420437601258818082583180042b2181042b218142040d1fc0000000043f9000000002151000c4cd70c0c4fef00104e75c0fc003420407004d1fc00000000b0b2180066d847f2180875e90046b49367cc760125831800268243f9000000002151000c60c24fefffec48d71c0c242f001824422642263c0000000049f90000000045ea004247eb029a71920c80000000006608486affda4e94588f45ea0064b7ca66e62442068200001bdc45ea02dc47f9000000007192b0836608486affda4e93588f45ea0064b5c266ea4cd71c0c4fef00144e754e56ff6052b900000000207940fb5a0448d71c3cb1f900000000670003b042b9000000004a8867000094428043f90000000075300800733108005280b282667c7264b28066ec23c8000000002439000000004eb9400cf8664a80676076444c03280022020681000000d4d081224020514a886748206800284a8867402f004e90588f4a806736244073aa00260c8100000000662822790000000072142041700541e8ffbab0886504528160f041f218007056139018005281b08166e02279000000004a896600031841f9000000002d48ff982639800017e4243c409c9c80267940fb5a0445f9000000002f024e92068200001bb6588f0c8240a700c066ec4a8367062f034e92588f243c000000d445f9000000004eb9400cf8664a806730d082224020514a886726206800284a88671e2f004e90588f20404a80671271a800260c800000000066062f084e92588f0682000000440c820000026c66b84a8b6700032671ab00260c8000000000670002c645f900000000267c800017e8243c000000d497ca4eb9400cf8664a80672cd082224020514a886722206800284a88671a2f004e90588f4a806710284073ac00260c8100000000670001aa4280068200000044b09a67082540fffc42b3a8000c820000026c66ae45f900000000428347f90000000074344c032800206eff984ab02800672e227900000000b3d267247003b0b02800670001647206b2b028006700015a286eff9842aa000442aa000842b42800528345ea0034b5fc0000000066b44ab940f07cf4670001182039422fef30b0b940fe6df06700010847f90000000042837a3472024c035800226eff9841ebfff02d48ff8020315800b280670002f87405b4806700023a53804a80660004ec45f15800260a5083486effa020432f104eb94007de78508f242a00044a806608b4aeffa4670005a22f3c40fe6df04eb940001cc42f024eb94007dc30508f4a806d0004f2e7882040d1fc401fb8a824102f3c40fe6df04eb940001df6588f4a82670004e0486effa02f024eb94007de78508f4a80660004cc206eff9824705804b5eeffa4660004bc218258087001486effb0487800402d42ffb0260e0683ffffffc02f0342aeffb442aeffb8242effa82d40ffbc4eb94007baaa4fef000c7240b28067000542206eff9874042182580042004cee1c3cff6013c0000000004e5e4e75202c00486000fe54206eff98780621842800202a00042240d3ea00082f092f004e93508f4a80671e206eff987003528345ea003421802800b5fc000000006600fe426000fe8a226eff98528342aa000442aa000842b1280045ea0034b5fc000000006600fe1e6000fe664a886600fc7c2279000000004a896700fcec45f900000000428042b90000000041f9000000002d4aff9872344c001800286eff9852804ab418006704b3d0674a41e80034b1fc0000000066de2639800017e4243c409c9c80267940fb5a0445f9000000006000fcb82f0b267c800017e84eb90000000045f900000000588f243c000000d497ca6000fd307004b0b418006600fc74206eff987001243c409c9c8045f900000000218018002639800017e4267940fb5a046000fc66428041f90000000042017406118108005280b4806700fcd442017406118108005280b48066e26000fcc2282b000872fc5684c881243c4380000041f90000000095ca202800042202d2844a8067182250d089b289631022005681b480640874fcc481347c000141e80034b1fc0000000066d00c824670000062000268203c467000009082b0846500025a4a8a66ac26824a8267000250202eff80048000000000e480223c89d89d9a206eff984c0108002184581422402040d3fc00000000d1fc0000000006800000000030fc7fff32fc8000b08866f4206eff98740221825800486effa0246eff98d5c52f2a00084eb94007de78508f4a806600020c226a0004b3eeffa466000200202a001c242a001894800c82000200006200023e246eff98d5c5222a0010d2802d6a0008ffc0486effc076012f020680000000402f012d40ffc442aeffc82d43ffcc4eb94007baaa4fef000cb48066000242202a001cd480266a00102d42ff904aaa0020660002d2e28ae288222a0018e2892d42ff842d40ff882d41ff8c70697668242eff88222eff8c4c0028004c412002b682650000ce202eff80048000000000e4802601223cc4ec4ecd283c89d89d9a4c0238004c0018004c0408002d4bff7c2d45ff9c2a03d282d2810680000000002d40ff9420012041068000000000d1fc000000002d48ff802640200574694c420000b0aeff846462206eff803813daaeff8c3250b0aeff886404202eff88220576694c431001b2aeff846304222eff84b2806324246eff7c41f20a0045f21a003218714477497541b4806c023801b4836f023241b1ca66e836c4286eff8054aeff8038c9b7eeff946690266eff7c2a2eff9c202eff90206eff98d1c52140001cb0a800186600fc4a22280024243c0000bb8078fc263c0000bb804c4210004c421001242eff8c214b0028216eff8c002cd48248404240484142415682c8824c43000021440014808121400030206eff9878034200218458004cee1c3cff6013c0000000004e5e4e754293528347eb0034b7fc000000006600fada42004cee1c3cff6013c0000000004e5e4e75246eff98700142b258002580580042b2581042b2581442004cee1c3cff6013c0000000004e5e4e752f3c40fe6df04eb940001df6588f206eff9870042180580042004cee1c3cff6013c0000000004e5e4e7574024842246eff98d5c5222a0010d2802d6a0008ffc0486effc076010680000000402f022f012d40ffc442aeffc82d43ffcc4eb94007baaa4fef000cb4806700fdc2206eff98700442aa001042aa001442b058002180580042004cee1c3cff6013c0000000004e5e4e75224370012411260e486effb0487800402d42ffb00683ffffffc02f0342aeffb442aeffb8242effa82d40ffbc4eb94007baaa4fef000c7240b2806600fac2486b0010486b0014486b00082f022f034eb9000000004fef00144a806700faa2226eff9870052380580042b1581c42004cee1c3cff6013c0000000004e5e4e75e488222eff90e4892d40ff882d41ff84b081641e41f30c0043f30a0045f31c007150736800025888d081e28032c0b5c866ee206eff9820305818e4882d40ff8c6000fd04206f0004202800484e752f032f02242f000c08020000672a41f900000000428043f900000000723476034c001800b6b118006716528041e80034b1fc0000000066e4241f4280261f4e75b49066e6c0fc0034241f261f0680000000004e754e56ffa470052f02b0ae00106500013a4ab940f07cf4670001302239422fef30b2b940fe6df0670001204eb9400cf8664a8067000114222e001074444c0218000681000000d4d081224020514a88670000f8206800284a88670000ee2f004e90588f2d40ffa44a80670000de204071a800260c8000000000660000ce226e000c7270202900080680ffffffd0b280640000b87001c0a900044a80670000ac486effb07401487800402d51ffb0486effc042aeffb442aeffb82d42ffbc4eb94007baaa4fef000c7240b280667c486effb0206e000c486effac486effa82f280008486effc04eb9000000004fef00144a80674e41f900000000226effa452aeffa410d9b1fc0000000066ee206e000c242e001043e8000233d10000000022280004206e000823c20000000023c10000000023c10000000020bc0000000042a80004242effa04e5e4e75242effa042804e5e4e75226f0004206f00084a8967104a88670c71a800260c800000000067024e7533680046004c700133680048004e3368004a0050334000524e75206f0008226f00044a88670c4a8967087002b0a8000467024e7571a900260c800000000066f23368004c00463368004e004833680050004a4a68005266da303c4000334000204e752f02242f00080802000066064280241f4e7541f900000000428043f90000000072344c0018004ab118006704b4906712528041e80034b1fc0000000066e2428060cc7403b4b11800670820311800241f4e75c0fc0034243cc4ec4ec5206f000ce4804c020800c0fc00d224000682000000002082206f001006800000000020802031180060c8598f2eaf00084eb9000000004af90000000056c04a00670c2f570008588f4ef940076be44eb9000000002f570008588f4ef940076be42f032f02206f000c428222085e8171988480b1c166f808020004662044c26b6444c2676e080200016676226f00107001241f307c0004261f22884e7591c8700408020000662053807210e0a1b1c06726c2824a8167f0226f00109088241f52802288261f4e75226f00107005241f90882288261f4e75226f00107001241f2288261f4e75307c000170040802000067b660d4307c000270040802000067a860c6307c00030802000066bc226f00107001241f307c0003261f22884e754fefffd848d73cfc222f00302c2f0038206f002c2a2f0034286f003c246f0040bc816d5e2a46260c528d5283b9c56d4c2268000420054a8a6658b3c163387e1f2c00ea86ce80b0a80008642a2428000c5280226800104c012800d4862c3c80000000eeae4686cdb12c00b680670e22680004b3c162c85280b08366be5281bbc166aa4cd73cfc4fef00284e755280b08367eab3c163f67e1f2c00ea86ce80b0a8000864e82428000c5280226800104c012800d4862c3c80000000eeae8db12c00b08367b82268000460c84fefffec48d7043c242f00204878000145f9000000002f022a2f002c53852f05282f00242f02262f002c52832f032f044e924878000152822f2f00442f052f2f004c2f032f044e924fef003048780001262f002c53832f032f2f00242f022f2f002c2f044e92487800012f032f2f00442f022f2f004c2f044e924cef043c00304fef00444e754fefffd048d77cfc206f0040246f0034286f0038266f004416106774704c750342817100b0826700011a52814bf9000000001035180066ea7039b0826d00012c20020680ffffffd02200e7892c419dc0ddfc00000000486f002c2f0e4eb9000000002e2f0044226f003491c8508f4a806e28528853877207b28866f2206f0040528849f4080116102f4800404a03668c4cd77cfc4fef00304e752a0093ccda8c220c77b6880028097410d881e8a2c4834a8266145281b28566e8528853877207b28867b8220c60da242a00044a8b6736b48163e0781f2607ea83c887beaa000864d2242a000c4c0128005281d483e58a263c80000000e8abd4aa00102a428795b285669e60b4b48163aa781f2607ea83c887beaa0008649c242a000c4c0128005281d483e58a263c80000000e8ab4683d4aa00102a42c795b2856600ff666000ff7ac2fc0007486f002c2c41ddfc000000002f0e4eb9000000002e2f0044226f0034508f91c86000ff0620030680ffffffc971002200e7892c419dc0ddfc000000006000fed2598f2f0a2f024eb9400cf8664a80676a2f004eb94000eb902f004eb940012412508f22007005b08165502f4100084eb9400cf866222f00084a80673e74444c0218000681000000d4d081224020514a886728206800284a8867202f004e90588f4a806716204073a800260c81000000006608241f245f588f4e75241f4280245f588f4e754fefffe848d7441c262f001c242f0020246f00244eb9000000004a80676ee08222020681ffffffc04a816d48240f068200000014428393c92042780a52894c4418004c44180106800000003010c04a8166e841f128004df238001ce0b48866fa42012003d089158108004cd7441c4fef00184e75724076019282240f06820000001414bc002d93c9204260ae2f4a00242f4200202f43001c4cd7441c4fef00184ef9400456c84fefffe82f0a246f00202f6f002400142f6f002800182f6f002c00042f6f003000082f6f0034000c2f6f003800104eb9000000004a806744202a0004b092673c487800012f2f00142f0a4eb9400720584fef000c72012f4100302f6f000c002c2f6f000800282f4000242f6f00040020245f4fef00184ef940071da4226f00142f6f001000302f6f000c002c2f6f000800282f6f000400242f6f00180020245f4fef00184ed12f2f00142f2f00142f2f00142f2f00142f2f00142f3c400466a22f3c40fe36384eb9000000004fef001c4e752f2f00142f2f00142f2f00142f2f00142f2f00142f3c400466f02f3c40fe35f44eb9000000004fef001c4e754fefffd048d77cfc246f0040226f0034282f00382a6f003c2a2f0044121267207030730141f9000000007100b081671a101866f6122a0001528a58844a0166e04cd77cfc4fef00304e7591fc0000000049f08c002e0d91c824044280d9fc0000000073b488007c04e0a6c2864a81661a528052827c03bc8066e8528853877005b08867b02404428060d8222900044a856740b28263da721fc2872641bea9000864ce2229000c2c3c8000000052804c02180052825281e5892f41002c220be2ae266f002cd7e900108d937c03bc80669260a8b282639a7c1fcc87bea9000864902229000c52804c02180052825281e5892f41002c223c80000000266f002ceca97c03d7e900104681c393bc806600ff546000ff68598f2f0a2f02487800012f2f001c4878007f2f2f0020246f0020487800422f0a4eb9000000004fef0018202a00047242b280640000ca242f0014b4aa0008645e202a000c7442222f0014ea81206a00104c020800741fc4af00142241d081223c80000000e4a9747f4681c3b00c00202a0004b4806422202a0008b0af00146322206a000c2008ef889088206a0010d089c3b00c00202a00047242b2806460202a0008b0af00186356741f7242c4af0018202a000c206a00104c010800223c800000002f420008242f0018ea82d0822242242f0008e4a94681c3b00c00707fb0aa0004641a242f0018b4aa00086410246a000c200aef88908ad089c3b00c00241f245f588f4e754e56ffa048d73cfc246e000c2f0a42aeffda42aeffde4eb900000000588f206e000828002028000443e8000c4c1108004a806f1a2648206800102d4bffcc43f00c004298b1c966fa2d6effcc0008428041ea000443eeffef2d6e0008ffcc121052884a01670a12c152807210b28066ee42013e2a00542d6effcc000845f9000000001d8108ef0807000866000432367c000145f90000000008070009660004224a8467442f3c40140ab0260e0683ffffffe62f034eb940072260486effef48790000000042a748780035487800192f032f2e00084eb940071a044fef00202e834eb940072080588f206e00087433222800042d48ffcc761f7017c6822a3c80000000e6adb2806320226effccb4a9000864162229000c206900104c0018005281bbb01c002229000452800c800000008066d252827040b08266bc206effcc70172d480008b081640000a07233b2a80008640000967a17727f2028000c2248206800104c050800528041f00c00203c00001000b19020290004b28064267a33baa9000864642229000c2001ef88206900102c3c0000100090815280bdb00c00202900047217b2806440206e00087a3fbaa8000864342028000c2248206800107a7f4c0108007201b3b00c04baa9000464187c3fbca9000864102229000c2001ef8890817201b3b00c044eb9400cf8664a80670009102f007c054eb94000eb902f004eb940012412508f2a002d40ffd4bc80640005c442aeffd0487800014878003f487800144878003342a745f9000000002f2e00084e924fef0018206e00084aa8000467747033b0a80008646c22680010223cffffefff7c14c3a9000420280004bc8064207033b0a80008644c2028000c2648206800104c0608005280c3b00c00202b00044a806730206e0008703fb0a80008642470fe7214c1a90004b2a8000464167c3fbca80008640e2028000c4c01080072fec3b10c044eb9400cfd0e2f004eb94006a96c588f24004a806d0003f2e882220002818000000f0682000000411e021d42ffe24a806d0003585281700a4c4018024c40180142060681000000300682000000301d41ffe31d42ffe41d46ffe54a07670003603a7cffff2c2e0008260e43eeffe20683ffffffe62d49ffcc47f90000000049f9000000002d49ffc87507704c42817100b4806700021a52811034180066f07039b0826d0002360682ffffffd02202e78992820681000000002f032f014e93508f206effc852884bf508011e102d48ffc84a0766b4538d200d6a02528042a7720a2f2effcc4878003c2d46000847f900000000e28092802f012f2e00084eb90000000048780030487800144878001d42a72f2e00084e934fef00287005b0aeffd46400030c4878001a74014878000e42a7487800062f2e00084e934fef00142d6e0008ffcc487800012f02487800032f02487800012f2effcc4e92487800012f02487800132f024878001150822f2effcc4e924fef00307021b08266c82d6effcc00084aaeffd06e00016c486effde486effda2f044eb9000000004fef000c4a846700019c7203b2806700044859804a80670003922f3c4014120c240e0682ffffffe62f024eb94007226048790000000048790000000048780002487800154878004b2f022f2e00084eb940071a044fef00202e824eb940072080588f4cee3cfcffa04e5e4e7597cb200b204ae588761b2d44ffd02d4affd42d6e0008ffcc22407b98240942810682000000777004e2a05281c0854a80663652827003b08166ec53837216b28366d8246effd47001282effd05a8a2d6effcc0008b08b6700fb8a367c0001080700096700fb7e609a246effcc2a434bed0020b4aa000464ba203c80000000e6a8bbea000864ac282a000c4c02480052822a44528d280de58c2a44dbea001081957003b08166806092c2fc00072f030681000000002f014e93508f206effc852881e104bf508012d48ffc84a076600fdb46000fdfc24070682ffffffc975022202e78992820681000000006000fdc62c2effd05386cdfc0016727e487800014c4168062046486800024878000c48780002487800082f2e00084e924fef0018486effde486effda2f044eb9000000004fef000c4a846600fe682f3c4014120c240e0682ffffffe62f024eb94007226048790000000048790000000048780002487800154878004b2f022f2e00084eb940071a044fef00202e824eb940072080588f6000fe747cf053818286700a4206528152814c4018024c4018011d46ffe50681000000300682000000301d41ffe31d42ffe44a076600fca441eeffe2720b42a72d48ffcc2f2effcc4878003c2f0147f9000000002f2e00084eb90000000048780030487800144878001d42a72f2e00084e934fef00287005b0aeffd46500fd20602606820000000fe882220002818000000f0682000000411e021d42ffe24a806c00fc0c6000ff5e72544206487800012f2effcc4878002d48780007200506800000003149f9000000002f2e00081d41ffe21d40ffe31d46ffe44e944eb9400cf8664fef001420404a80670001442f05486800744eb9400097f0204022504878001c2f002069001c4e90e08022000681ffffffc026014a816d000140240370634fef0010b0836d0000e27a0a7c094c4528004c4528020680000000301a00bc836c0000e420020680000000304a816d000326e18848780001720c2f2effcc487800252f012f2e000810053d40ffe24e944fef00144878001a74014878000e42a7487800062f2e00084e934fef00142d6e0008ffcc6000fc284eb9400cf86620404a806700fa322f05486800744eb940009c5a508f71002d40ffd06000fa1e2f3c4014120c240e0682ffffffe62f024eb94007226048790000000048790000000048780002487800154878004b2f022f2e00084eb940071a044fef00202e824eb940072080588f6000fc6e7a0a74634c4528004c4528027c090680000000301a00bc836d00ff204a816d00024a6600026e703042054878000172092f2effcc487800252f01e1882f2e000810053d40ffe24e944fef00146000ff1c4483240370634fef0010b0836c00fec2609e2a2e0010daae00140c85000078006f062a3c00007800246effda7601266effde280a204a284b0684000000d22d6e0008ffcc7158735c240044822241b0816e0eb6816f0222432609b4896f022602b1c466e03c2e0012223c000078007417cbfc006993c90685000077ffcdfc00694c4168064c4158052d45ffd0301a321b7f407941b8876c7a528952820c820000008066e82a2effd024062d6effcc00087068b0866c027468224506820000001770012e3c8000000043e900162d6e0008ffcc246effccb4aa00046424b0aa0008641e262a000c781fc8802200ea814c023800206a0010d2832607e8ab87b01c000800000066000100ba866e0000bc528060c0c3fc0018c1fc00182e014c4378074c430800b0876e00ff70b3eeffd05dc1bc895fc4204706800000001941e8001a44814484c8814a0467422a6effccb4ad0004642c286effccb0ac000864222e2c000c7a1fca802200ea814c027800286c0010d2872e3c80000000eaaf8fb41c005280b1c06700ff124a0466be2e000687ffffffe722076a025281e281d289828708010000660a286effccb4ac000465a45280b08866d6528952820c82000000806600feca6000fede266effccb3eb00046400ff3c286effccb0ac00086400ff30781fc880260922004bec000cea814c153800206c00105280d2832607e8ab87b01c006000fece52807232b2806600fec44cee3cfcffa04e5e4e754205e1884878000172022f2effcc487800252f012f2e000810053d40ffe24e944fef00146000fcda4205e1884878000172102f2effcc487800252f012f2e000810053d40ffe24e944fef00146000fcb272ff7aff2d41ffd442aeffd06000f7084feffff42f6f001000082f6f001400044eb9000000004a8067182e804eb9400cf9a82f004eb94006b704588f20574a0067162f6f000400142f6f000800104fef000c4ef94001b22a7168002c0c80000078006e444a806d562f007168002a0c80000078006e184a806d562f002f082f2f00104eb9000000004fef001c4e75203c000078002f002f082f2f00104eb9000000004fef001c4e75203c000078002f007168002a0c80000078006fba60d042802f007168002a0c80000078006fa860be42802f002f082f2f00104eb9000000004fef001c4e754fefffd448d73cfc266f00302f6f003400284eb9000000002a2b023042b90000000024404a806700017e4eb9400cf9a82f004eb94006b704588f4a0067000168283c00000000ba84670a0c8500000000660001544eb9400cf9a82f004eb94006b736588f4a006700017a4eb9400cf8664a80670000962f004eb94000f23e2f004eb940016402508f2c004a806f7c42822e3c000000004eb9400cf9a8761f223c00000160b6826c06223c0000015c204020301800721fc282030067482f042f024879000000004eb94001d7842f072f0248790000000028404eb94001d7842f0242a726004eb94001e2464fef00202a4070ffb08d6672ba84670000c470ffb083660000c25282bc82668c776a002a2843776a002c71aa00260c8000000000660000860c83000078006e00011c4a836d00016a2f03b9fc000078006e00011c4a8c6d0001382f0c76012f0a2f2f00344eb90000000023c3000000004fef00104cd73cfc4fef002c4e75bc826f9e4a8d6d5a4eb9400cf8664a80672c2f0d2040486800744eb940009c4a508f204022504a896714226900284a89670c2f004e91588f24404a8066242f4b00304cd73cfc2f6f002800344fef002c4ef94001e40ab08c6700ff42bc826f00ff4270ffb08c670000da70ffb0836600ff3c776a002c6000ff34716a002c0c80000078006f50203c000078002f00716a002a0c80000078006f22203c000078002f002f0a2f2f00344eb9000000004fef00104cd73cfc4fef002c4e754a806ce042802f002f0a2f2f00344eb9000000004fef001060dc4a806cb2428060ae263c000078002f03b9fc000078006f00fee8387c780076012f0c2f0a2f2f00344eb90000000023c3000000004fef00106000fee699cc2f0c76012f0a2f2f00344eb90000000023c3000000004fef00106000fec642832f03b9fc000078006f00fe9860ae716a002a284070ffb0836600fe5e6000ff204e56ffe82f032f024ab90000000067144eb9400cf9a82f004eb94006b736588f4a0066522f2e000c2f2e00084eb9400299de508f4eb9000000002d40fff04a8067284eb9400cf9a82f004eb94006b736588f4a0067144eb9400cf9a82f004eb94006b704588f4a006732242effe0262effe44e5e4e754eb9400cf9a82f004eb94006b704588f4a0066aa2f2e000c2f2e00084eb9400299de508f609842aeffe876ff42824eb9400cf9a8721f2040b2826c0001d2701fc0822228015c0101670c70ffb083670001b452aeffe852827240b28266d070ffb0836790206efff073e800542d41ffec4eb9400cf8664a8067542f004eb94000f23e487800202f032f004eb94001591e4fef00104a806d360800000a6716222effec24000282000001000881000884812d42ffec0800000b6714222effec0280000002000881000980812d40ffec42a74878003f4878007f42a7487800402f2e000c4eb90000000070204fef0018223c535445502d41fff772081d40fffb20035280b2836c0001282200760a4c431801307c000674070681000000301d41fffc760a4c43080170010681000000301d8188f7b0aeffe86c0a722b1d8128f724085482420341f9000000001d8328f77542e58a4878003f487800332f2e000c4e9042a7486efff74878003b703f9082e2802040486800422f2e000c4eb900000000242effec4fef0020222effec02820000010008010008660000e0e08a7001b5802f0048790000000048780027487800452f2e000c4eb900000000242effec222effec4fef001402820000020008010009666670097201e0aab5812f0148790000000048780012487800452f2e000c4eb9000000004fef0014242effe0262effe44e5e4e75260252aeffe86000fe4a202801600500670a70ffb083670a52aeffe852826000fe0a260252aeffe860f2307c000574066000feea48780016487800072f2e000c41f9000000004e904fef000c70097201e0aab5812f0148790000000048780012487800452f2e000c4eb9000000004fef001460804878002b4878001c2f2e000c41f900000000e08a4e904fef000c7001b5802f0048790000000048780027487800452f2e000c4eb900000000242effec222effec4fef0014028200000200080100096700ff0a6000ff6c598f2f027405202f0010d0af00142f400004b4af000c640a202f0004241f588f4e754eb9400cf8664a8067ec222f000c74444c0218000681000000d4d081224020514a8867d2206800284a8867ca2f004e90588f4a8067c0204071a800260c800000000066b2202f00100800000867a8242f00140c82000001ff6e20242f00140c82fffffe016c90203c00000100d1af0004202f0004241f588f4e75203cffffff00d1af0004202f0004241f588f4e752039000000007207b280673a08000000660e223c400456c8b2b940a72c28672808000001660e223c400466a2b2b940a72c68673244c0670e223c400466f0b2b940a72ccc673c4e7572018081223c0000000023c140a72c2823c0000000000800000166d060c072028081223c0000000023c140a72c6823c00000000044c067c660b6223c0000000023c140a72ccc7204828023c1000000004e7500002f0822522f2902982f2f000c2f2f00084eb9000000004fef000c205f4a80670420084e754ef9400a30522f082f2a02982f2f000c2f2f00084eb9000000004fef000c205f4a80670420084e754ef9400a3052222f000c7005b280626043f900000000700113801800225f2f2f00142f2f00142f2f00142f2f00142f2f001441fa000c2f084feffff072054ed14fef00142f2f000c2f2f000c4eb900000000508f4a80671670402f002f2f00102f2f00104eb94008145e4fef000c4e75225f4feffff072054ed1222f000c7005b2806254225f2f2f00142f2f00142f2f00142f2f00142f2f001441fa000c2f084feffff070054ed14fef00142f2f000c2f2f000c4eb900000000508f4a80671670402f002f2f00102f2f00104eb94008145e4fef000c4e75225f4feffff070054ed1222f000c7005b280621a43f9000000007000138018002f2f00102f014eb900000000508f225f4feffff470054ed12f2f00102f2f00104eb900000000508f225f4feffff070054ed122572e832f022f092f04600822572e822f092f072f002f034eb9000000004fef000c28004e752f2f00082f2f0008487a00104feffff448d71c004ef94005afa82f002f2f00082f2f00084eb900000000508f201f508f4e752f2f00082f2f0008487a00104feffff448d71c004ef94005b05c2f002f2f00082f2f00084eb900000000508f201f508f4e752f2f00082f2f0008487a00104feffff448d71c004ef94005aed42f002f2f00082f2f00084eb900000000508f201f508f4e754fefffc448d77cfc2f6f004000384ab900000000660000f04ab940fe32cc670000e6223940fe32ccb2b940fe32d0670000d643f90000000047f90000000010290003207940fe32cc4a00670000a61829000471802f4000344a046700009671917da900017ba900027984c0fc001c2c467c209c8599cc0685ffffffdf24700810260ed68c774342802f4600302f4e002cd683222f00309280ea8124057e1fd480c487d28322321c000501673073a900067c1f74207fa900052041d1c022080681ffffffdfc2869488ea82de8c7f472c42740141f67a00e3aa85b38c005280b88066b02c2f0030528c2c6f002cb9ef0034668e5e89b3fc000000006600ff42700123c0000000004cd77cfc2f6f003800404fef003c4ef900000000ef5c192c6e9f1993ef420004ef6e18c16ea21a00ef30ffffef8018576ea31a6eef1ffff9ef9217ed6ea41adcef0efff3efa417846ea31b4beefdffedefb7171b6ea21bb9eeecffe7efc916b26e9f1c28eedcffe2efdc164a6e9b1c97eeccffdcefef15e16e971d07eebdffd5f00315796e911d77eeadffcff01615126e8a1de7ee9effc9f02914ab6e821e58ee8fffc3f03d14446e7a1ec8ee81ffbcf05113dd6e701f3aee72ffb6f06513776e651fabee65ffaff07913126e59201dee57ffa8f08e12ac6e4c208fee49ffa2f0a212476e3e2101ee3dff9bf0b711e36e2f2173ee30ff94f0cb117f6e1f21e6ee24ff8df0e0111b6e0e2259ee18ff86f0f510b76dfc22cdee0cff7ff10a10546dea2340ee00ff78f11f0ff26dd523b4edf5ff71f1350f8f6dc02428edebff69f14a0f2e6daa249cede0ff62f1600ecc6d932510edd6ff5bf1750e6c6d7b2585edccff53f18b0e0b6d6225faedc3ff4bf1a10dab6d48266fedbaff43f1b70d4b6d2d26e4edb1ff3cf1cd0cec6d112759eda9ff34f1e30c8d6cf427cfeda1ff2cf1f90c2f6cd62845ed9aff23f2100bd16cb728bbed92ff1bf2260b746c972930ed8cff13f23d0b176c7629a7ed85ff0af2530abb6c542a1ded7fff02f2690a5f6c322a93ed7afef9f2800a046c0e2b0aed74fef0f29709a86be92b81ed6ffee8f2ae094e6bc32bf8ed6bfedef2c408f46b9d2c6eed67fed6f2db089b6b752ce6ed63feccf2f208426b4c2d5ded60fec3f30907e96b232dd4ed5dfebaf32007916af82e4bed5bfeb1f33707396acd2ec3ed59fea7f34e06e36aa12f3aed57fe9df366068c6a732fb2ed56fe93f37d06366a453029ed55fe8af39405e16a1630a1ed55fe7ff3ab058c69e63118ed55fe76f3c3053869b53190ed55fe6bf3da04e469833208ed56fe61f3f1049069503280ed58fe57f409043e691d32f7ed59fe4cf42003eb68e8336fed5cfe42f437039a68b333e7ed5efe37f44f0349687c345eed62fe2cf46602f8684534d6ed66fe21f47d02a8680d354eed6afe16f495025867d435c6ed6efe0bf4ac020a679a363ded73fe00f4c301bb676036b5ed79fdf4f4db016d6724372ded7efde9f4f2012066e837a4ed85fdddf50900d466aa381ced8cfdd1f5210088666c3893ed93fdc5f538003c662e390aed9bfdb9f54ffff165ee3981eda4fdadf567ffa665ad39f9edacfda1f57eff5d656c3a70edb5fd94f595ff1465293ae7edbffd88f5acfecb64e63b5dedcafd7cf5c3fe8364a23bd4edd5fd6ff5dafe3b645e3c4bede0fd62f5f2fdf464183cc1edecfd55f609fdae63d23d37edf8fd48f620fd68638b3dadee05fd3bf637fd2363433e24ee12fd2df64efcde62fa3e9aee20fd20f665fc9a62b13f0fee2efd13f67bfc5762673f85ee3dfd05f692fc14621c3ffaee4dfcf7f6a9fbd261d0406fee5dfce9f6c0fb90618440e4ee6dfcdbf6d6fb4f61374159ee7efccdf6edfb0f60e941cdee90fcbef703facf609a4242eea2fcb0f71afa90604b42b6eeb4fca1f730fa515ffb432aeec7fc93f746fa135faa439eeedbfc84f75df9d65f584411eeeffc75f773f9995f064484ef04fc66f789f95d5eb344f7ef19fc57f79ff9215e5f456aef2ffc48f7b5f8e65e0b45dcef45fc39f7cbf8ac5db6464eef5cfc29f7e1f8725d6046c0ef74fc19f7f6f8395d0a4731ef8cfc0af80cf8005cb347a2efa5fbfaf822f7c85c5b4813efbefbeaf837f7915c034884efd7fbdaf84df75a5baa48f4eff2fbc9f862f7245b504964f00dfbb9f877f6ee5af649d4f028fba9f88cf6b95a9c4a43f044fb98f8a2f6855a404ab2f060fb87f8b6f65159e44b21f07efb76f8ccf61e59874b8ff09bfb65f8e0f5ec592a4bfcf0bafb54f8f5f5ba58cc4c6af0d8fb43f90af588586d4cd7f0f8fb32f91ef558580e4d44f118fb20f932f52857af4db0f138fb0ff947f4f8574e4e1cf15afafdf95bf4c956ee4e87f17cfaebf96ff49b568d4ef2f19efad9f983f46d562b4f5df1c1fac7f997f44055c84fc8f1e4fab5f9abf41455655031f208faa3f9bff3e85502509af22dfa90f9d2f3bd549e5103f252fa7ef9e6f3925439516cf278fa6bf9f9f36853d451d4f29ffa58fa0cf33e536f523bf2c6fa46fa1ff316530952a2f2edfa33fa33f2ed52a25309f316fa1ffa46f2c6523b536ff33efa0cfa58f29f51d453d4f368f9f9fa6bf278516c5439f392f9e6fa7ef2525103549ef3bdf9d2fa90f22d509a5502f3e8f9bffaa3f20850315565f414f9abfab5f1e44fc855c8f440f997fac7f1c14f5d562bf46df983fad9f19e4ef2568df49bf96ffaebf17c4e8756eef4c9f95bfafdf15a4e1c574ef4f8f947fb0ff1384db057aff528f932fb20f1184d44580ef558f91efb32f0f84cd7586df588f90afb43f0d84c6a58ccf5baf8f5fb54f0ba4bfc592af5ecf8e0fb65f09b4b8f5987f61ef8ccfb76f07e4b2159e4f651f8b6fb87f0604ab25a40f685f8a2fb98f0444a435a9cf6b9f88cfba9f02849d45af6f6eef877fbb9f00d49645b50f724f862fbc9eff248f45baaf75af84dfbdaefd748845c03f791f837fbeaefbe48135c5bf7c8f822fbfaefa547a25cb3f800f80cfc0aef8c47315d0af839f7f6fc19ef7446c05d60f872f7e1fc29ef5c464e5db6f8acf7cbfc39ef4545dc5e0bf8e6f7b5fc48ef2f456a5e5ff921f79ffc57ef1944f75eb3f95df789fc66ef0444845f06f999f773fc75eeef44115f58f9d6f75dfc84eedb439e5faafa13f746fc93eec7432a5ffbfa51f730fca1eeb442b6604bfa90f71afcb0eea24242609afacff703fcbeee9041cd60e9fb0ff6edfccdee7e41596137fb4ff6d6fcdbee6d40e46184fb90f6c0fce9ee5d406f61d0fbd2f6a9fcf7ee4d3ffa621cfc14f692fd05ee3d3f856267fc57f67bfd13ee2e3f0f62b1fc9af665fd20ee203e9a62fafcdef64efd2dee123e246343fd23f637fd3bee053dad638bfd68f620fd48edf83d3763d2fdaef609fd55edec3cc16418fdf4f5f2fd62ede03c4b645efe3bf5dafd6fedd53bd464a2fe83f5c3fd7cedca3b5d64e6fecbf5acfd88edbf3ae76529ff14f595fd94edb53a70656cff5df57efda1edac39f965adffa6f567fdadeda4398165eefff1f54ffdb9ed9b390a662e003cf538fdc5ed933893666c0088f521fdd1ed8c381c66aa00d4f509fddded8537a466e80120f4f2fde9ed7e372d6724016df4dbfdf4ed7936b5676001bbf4c3fe00ed73363d679a020af4acfe0bed6e35c667d40258f495fe16ed6a354e680d02a8f47dfe21ed6634d6684502f8f466fe2ced62345e687c0349f44ffe37ed5e33e768b3039af437fe42ed5c336f68e803ebf420fe4ced5932f7691d043ef409fe57ed58328069500490f3f1fe61ed563208698304e4f3dafe6bed55319069b50538f3c3fe76ed55311869e6058cf3abfe7fed5530a16a1605e1f394fe8aed5530296a450636f37dfe93ed562fb26a73068cf366fe9ded572f3a6aa106e3f34efea7ed592ec36acd0739f337feb1ed5b2e4b6af80791f320febaed5d2dd46b2307e9f309fec3ed602d5d6b4c0842f2f2fecced632ce66b75089bf2dbfed6ed672c6e6b9d08f4f2c4fedeed6b2bf86bc3094ef2aefee8ed6f2b816be909a8f297fef0ed742b0a6c0e0a04f280fef9ed7a2a936c320a5ff269ff02ed7f2a1d6c540abbf253ff0aed8529a76c760b17f23dff13ed8c29306c970b74f226ff1bed9228bb6cb70bd1f210ff23ed9a28456cd60c2ff1f9ff2ceda127cf6cf40c8df1e3ff34eda927596d110cecf1cdff3cedb126e46d2d0d4bf1b7ff43edba266f6d480dabf1a1ff4bedc325fa6d620e0bf18bff53edcc25856d7b0e6cf175ff5bedd625106d930eccf160ff62ede0249c6daa0f2ef14aff69edeb24286dc00f8ff135ff71edf523b46dd50ff2f11fff78ee0023406dea1054f10aff7fee0c22cd6dfc10b7f0f5ff86ee1822596e0e111bf0e0ff8dee2421e66e1f117ff0cbff94ee3021736e2f11e3f0b7ff9bee3d21016e3e1247f0a2ffa2ee49208f6e4c12acf08effa8ee57201d6e591312f079ffafee651fab6e651377f065ffb6ee721f3a6e7013ddf051ffbcee811ec86e7a1444f03dffc3ee8f1e586e8214abf029ffc9ee9e1de76e8a1512f016ffcfeead1d776e911579f003ffd5eebd1d076e9715e1efefffdceecc1c976e9b164aefdcffe2eedc1c286e9f16b2efc9ffe7eeec1bb96ea2171befb7ffedeefd1b4b6ea31784efa4fff3ef0e1adc6ea417edef92fff9ef1f1a6e6ea31857ef80ffffef301a006ea218c1ef6e0004ef4219936e9f192cef5c000abe387fae6110000b78737fada7a4000c3f487face1ab000d13937fac0e4b000df63b7fab2c9d000ee83b7faa3ba9000fea9c7fa93a670010fe787fa827bc001224ff7fa7027c00135f737fa5c9630014af2e7fa47b1c0016159e7fa316390017944e7fa1993100192ce07fa00263001ae1147f9e5012001cb2c77f9c8063001ea3f77f9a915a0020b6c47f9880d80022ed727f964c9d00254a6e7f93f2400027d04b7f916f2d002a81cd7f8ec0a8002d61e37f8be3c1003073b17f88d5590033ba8f7f85921c00373a117f82167a003af6057f7e5ea8003ef27d7f7a669b004333cf7f762a000047be9a7f71a43d004c97cd7f6cd0690051c4ab7f67a94600574ad27f62293f005d303c7f5c4a5d00637b4a7f560648006a32c97f4f563a00715dfb7f4832fb007904977f4094d900812edc7f3873a10089e5917f2fc6950093320e7f268467009d1e4a7f1ca32b00a7b4e27f12185100b301247f06d89600bf0f177efad80200cbeb8b7eee09d100d9a4247ee0607100e847657ed1cd6e00f7e4bd7ec2416a01088c987eb1ac0b011a506d7e9ffbef012d42cb7e8d1e990141776e7e790067015703497e638c7a016dfca07e4cacaa01867b127e34496f01a097b47e1a49d401bc6d1c7dfe935d01da177f7de109f901f9b4bd7dc18fe7021b647b7da005a5023f483a7d7c49db026583677d563942028e3b777d2dae8f02b997fd7d02825e02e7c2ba7cd48b1c0318e7ba7ca39cf0034d35647c6f89a70384dc907c3820a203c0109b7bfd2ebf03ff07747bbe7e4d0441f9ae7b7bd6fa0489228c7b34fdc804d4c0087ae9b505052512d97a99bc45057a5e737a44d06405d4e90279eaab870634fb5c798b0530069ae0ee7925924a0706e7a078ba054907795fae78480e5307f29b7577cf5b6e0872ef33774f98c208fab0b976c870e5098a370e76398d3e0a21d9fa75a296700ac1f184750334e30b6ad551745b11610c1cdbf573a9d5c40cd85a1f72ef2dcd0d9da1ad722ac8070e6d00a5715c56d70f46c003708391a2102b22756fa0361b111a62e36eb209ae1214b2e06db8db14131a38f46cb48406142b0ec36ba4eb0f15473f136a8a0587166ec3be6963d9a317a1837e6832809918df4fb666f628e01a27e22b65af186b1b7adac3645daeeb1cd7bd55630267fd1e3def94619ddd301facb7386030c7ea212338635ebc02ed22a074705d408b912423493e5bbf827725aa71095a3a2ba52734830258b1edf528bff4b7572851ab2a4b1c6a559efe252bd4346a5417b67d2d595f96529455192ed8aef95116c60b305028a84fa1004e31bdcfb24e34fdda331fad2a4cd4b2ad3473da174b8202f635b88a114a3eb88b36ec1633490c780a380d081b47ecb5f7391a246b46e0ac523a12745a45e951153af54dcc45074e2a3bc2596c443afb5c3c79964343845abb000ab330650c9b26000b6cae650c277e000c32bb650bac01000d0631650b2829000de7f7650a9b63000ed906650a0516000fda656509649d0010ed306508b948001212946508025a00134bd465073f0c00149a4665066e860015ff5965058fe500177c966504a2330019139e6503a46d001ac62f6502957d001c962665017439001e857f65003f650020965964fef5ae0022caf664fd95ad002525c264fc1ddf0027a94f64fa8ca9002a585d64f8e056002d35dd64f71710003044ef64f52ee5003388eb64f325be0037056364f0f965003abe2564eea779003eb73f64ec2d730042f50864e988a100477c1e64e6b621004c517064e3b2e300517a4164e07b9e0056fc2c64dd0cd6005cdd2d64d962d0006323a864d579930069d66b64d14ce30070fcb764ccd83c00789e4b64c816cc0080c36764c30371008974d764bd98b30092bbfe64b7d0bd009ca2d864b1a55700a7340e64ab0fe300b27afb64a4095200be83b5649c8a2100cb5b1f64948a4f00d90ef2648c015700e7adcc6482e62600f7473c64792f140107ebd1646ed1da0119ad2d6463c38b012c9e126457f8840140d273644b646901565f8b643dfa15016d5be8642fab8f0185df8864206a0001a003e5641025a601bbe41263fecdc501d99ccd63ec509d01f94c9863d89b59021b13d263c39a01023f14ce63ad376f026573ed63955d3a028e57bc637bf3ad02b9e90b6360e1b202e8530863440cc60319c35d632558e8034e6a4e6304a88a03867acc62e1dc8303c22a9b62bcd3fd0401b26362956c6c04454dcf626b817c048d3ba6623eed0b04d9bddb620f871b052b19a561dd25ca0581978f61a79d4f05dd8380616ebff7063f2cc961325e2406a6e62260f24656071505a460ae45300789e4c16066258c0805e0256019b0910889579d5fc8adce0914ade15f72e36409a8485d5f1816330a448edd5eb80a190ae9eb335e5282340b98c8bb5de7413d0c5193d05d7609ea0d14b9235cfe9f600de2a4f35c80c5c00ebbc2235bfc42c00fa079325b70de5c10912f035ade639e118e437a5a44a18012980ff159a36be913aee57158fa9cbf14d30aba584a15211604ba0e5791beaf17441ec256d18cfd1891528b56097f1819ec5a8c5539a1331b55242254620e5f1ccb81655382f26c1e4f256b529c8bd91fdfa04851af2dd1217c5acc50bb4246232492044fc14c0824d752914ec1e8ee269373c54dbdd3f8285792b54cb5e7742a220d304bab1f172bf0fccf4a9e9a0b2dc2323149919cef2f933095488593b931612a1a477c13873328fcff4676dc3834e732624577d9cf3697ff504481255e3837491a4395053a39c0ae7442b5ebe93b2f976441e674e03c7f4ead41295d9e3dab282c408178d43eaeb8853ff198243f8622b23f7c6776402e7fbe3f24337f40a662333eea942240ee70463ecff564000aba8c4f6f7f78000b748d4f6f37cf000c3b264f6eeb4d000d0f314f6e999d000df1984f6e4266000ee3524f6de547000fe5694f6d81da0010f8f94f6d17b300121f314f6ca65d001359524f6c2d5b0014a8b74f6bac2800160ecf4f6b223800178d244f6a8ef2001925584f69f1b5001ad92c4f6949d6001caa7d4f68969b001e9b4b4f67d7400020adb44f670af50022e4004f6630d80025409b4f6547fc0027c61b4f644f62002a77424f6345f9002d57044f622aa0003068864f60fc200033af244f5fb93000372e724f5e606e003aea444f5cf063003ee6ae4f5b677c0043280b4f59c40d0047b3024f58044e004c8c854f5626570051b9e24f542820005740bb4f52077d005d27164f4fc220006373614f4d5591006a2c744f4abf2f007159a04f47fc2d007902b04f45098d00812ff54f41e4200089ea4c4f3e888000933b2a4f3af30d009d2ca44f371fed00a7c9794f330b0200b31d1f4f2eafeb00bf33cc4f2a09fb00cc1a864f25143b00d9df2a4f1fc95f00e890814f1a23c200f83e4a4f141d650108f94a4f0dafe3011ad3614f06d470012ddf924eff83cf0142321f4ef7b64f0157e0964eef63c1016f01e74ee683740187ae7c4edd0c2901a200494ed2f40f01be12eb4ec830b901dc03ba4ebcb71601fbf1e64eb07b68021dfe944ea3713d02424cf34e958b600269025f4e86bbd60292467e4e76f3d102be435c4e6623a702ed258e4e543ac6031f1c524e4127ad035459af4e2cd7e1038d129a4e1737e303c97f164e0033280409da564de7b40e044e62e34dcda3d404975ab84db1ea9604e5076c4d946f430537b2474d751799058fa86b4d53c82305ed3ae54d3064350650becf4d0acdf206ba8d5e4ce2e648072b03f14cb88cff07a284204c8ba0c1082173b54c5bff2808a83cae4c2984d509374d234bf40d8b09cf172d4bbb74500a7010b54b7f93960b1ab3384b4045710bcf7b774afd63cf0c8ee90a4ab6c8c40d597dde4a6c4edb0e2fbd964a1dd17e0f122cc349cb2d6110014ffb4974410d10fdaac34918ed6e1207be4048b91685132007b64854a4261446fec047eb82ce157d1347477da49916c2ab1e470b025218181f4b46939c99197db8dc46177d321af3ad594596b8701c7a1aa045116ec11e1102404487ce651fb8442543fa1540216f9892436892e22336894842d3aab0250c69cf423bd63e26f04eb941a1a7dd28e103ce4105cd5f2add01084069131c2ce25e423fcc67402eeec5943f30dd6930ff645e3e97b2af3310db2d3e02521a351f2cc13d7259a23725ad013ce99fb5391ef0f93c6a39553b04c1fc3bf6808d3cd017323b911ae43e791ab03b3cfec53ff741f43afd75d6414185113ad61848424ec4c23acab9db431674743adf3bb44391a16d3b172d7b43bc6dce3b751d504398040f3bf96db5432cd28f3ca094fa000ac3d53e667aa0000b7e793e664e43000c45c13e661ee6000d1a873e65ec53000dfdb53e65b654000ef0443e657cad000ff3403e653f1f001107c53e64fd6700122f033e64b73c00136a3d3e646c510014bace3e641c54001622283e63c6ee0017a1d53e636bc000193b7a3e630a67001af0da3e62a278001cc3d33e623381001eb6673e61bd090020cab93e613e8d002303103e60b783002561dc3e6027580027e9b73e5f8d6d002a9d653e5ee91b002d7fdf3e5e39ac0030944c3e5d7e630033de0c3e5cb671003760ba3e5be0fd003b202d3e5afd1e003f207f3e5a09db004366113e59062a0047f5903e57f0f1004cd3f63e56c902005206973e558d1a0057931f3e543be3005d7f9f3e52d3ed0063d28b3e5153b2006a92ca3e4fb9910071c7b83e4e03ce0079792e3e4c308f0081af8c3e4a3ddb008a73c03e4829960093cf523e45f183009dcc6a3e43933f00a875e13e410c3d00b3d7433e3e59c600bffce53e3b78f700ccf3e93e3866ba00daca523e351fca00e98f0e3e31a0a700f952083e2de59a010a24363e29eaaf011c17ab3e25abb0012f3fa93e2124220143b0b43e1c4f43015980a63e1728020170c6c33e11a8fe01899bd23e0bcc7e01a41a333e058c7001c05df83dfee26301de85003df7c77e01feaf103df0347f0220fdf43de821b6024595993ddf86fb026c9c2f3dd65bac02963a4b3dcc96a602c29b053dc22e4202f1ec213db7184903245e303dab49f3035a24b93d9eb7e40393765e3d91561e03d08d063d8318060411a6083d73f059045702503d63d12a04a0e68e3d52abe004ef9b603d40713305436d7b3d2d1129059cadd33d187b1a05fbb1ca3d029db10660d3513ceb66ed06cc710d3cd2c42c073eee7c3cb8a23207b8b40d3c9ced34083a2f393c7f90ed08c3d2963c6078af095615d83c3f8f7c09f175d73c1cc02b0a9674783bf7f58c0b4598943bd11a940bff6dc73ba81a9a0cc4842b3b7ce1930d956ff83b4f5c640e72c90d3b1f79360f5d2a4e3aed27e4105530e13ab85a70115b7b393a81058e1270a7ea3a4721431395543c3a0aa99b14ca1a7839cb9f75160f8fda398a096d176642223945f4e418ceb4ad38ff772b1a495d0838b6aecc1bd69ee4386bc5061d76c750381eef6b1f2a071c37d071b920f06c3f37809fdd22c9da19372fe04024b6005736deae4e26b45050368d9d4628c3f08a363d5b692ae3ae2235eeb5792d11ebd535a29ab62f4c8e3b355a21493190e50b35168b4833db910234d94c543628666d34a40ffd38724c893478c0e53ab31a5d345990c13ce372c9344901283efaa2e83449ece840ee885d345f914b42b3891d348d95ca443cac3b34d80f08457bec3f354376b94662e82d35d48b7a46e42852368fffaf46f53b163779c8704691ef153893bc6045c0bedb39db102d4497d5b73b445a54000ac1b731388fd8000b7c3831387444000c435b313856d2000d17f931383762000dfafe313815d1000eed613137f1fa000ff02f3137cbb6001104823137a2db00122b8b3137773d0013668e313748aa0014b6e5313716f100161e023136e1db00179d6e3136a92c001936d031366ca9001aebe831362c0d001cbe963135e712001eb0dc31359d6d0020c4dc31354ecc0022fcdd3134fadb00255b503134a13c0027e2ce3134418e002a961d3133db69002d783331336e5b00308c3a3132f9f00033d59231327da6003757d53131f8f7003b16dc31316b51003f16c13130d41a00435be6313032ae0047eaf7312f865c004cc8f4312ece690051fb2e312e0a0d00578755312d3872005d737b312c58b50063c617312b69e3006a8614312a6af90071bacf31295ae300796c273128387b0081a27f31270287008a66cd3125b7b90093c29d312456ac009dc0203122dde600a86a3531214bd000b3cc76311f9ebc00bff33f311dd4e000ccebc3311bec5200dac4123119e30900e98b2c3117b6dd00f951113115657e010a26cf3112ec7a011c1e9131104936012f4bbb310d78eb0143c2f2310a78a801599a3a3107454c0170e9053103db810189c850310037c201a452b730fc564e01c0a49330f8332b01dedc1130f3ca2201ff195330ef16bb02217e8d30ea143b0246302230e4bda1026d54cb30df0da0029715b730d8fea102c39eb030d28aba02f31e4230cbabb20325c5e530c45af6035bca2430bc91a0039562cc30b4486b03d2cb1630ab77b9041441d930a2178e045a09b630981f8f04a4694f308d870504f3ab75308244da05481f5b30764f9e05a218ce30699d8c0601f062305c2488066803ab304dda3006d4b56c303eb3dc07486dc8302ea6b107c39a6f301da7ab0846aec7300babb308d224152ff8a7b5096679942fe490b90a0434952fcf5c080aabe0812fb8ff530b5e0ee12fa170e10c1b574a2f88a7c80ce457392f6e9c2f0db9b1df2f53479a0e9c0fc72f36a5450f8c1e652f18b28d108a8f742ef96f68119818332ed8def212b570572eb7081013e350d12e93f626152272302e6fb9f416738ab52e4a6a8117d74bec2e24263e194e5fc92dfd143e1ad965212dd565a71c78eb682dad57511e2d6d8d2d8533a31ff74bcf2d5d54af21d6c4452d36269b23cbe9f62d102a5f25d69a1a2cebf8eb27f66f402cca46b92a2ab1e42cabe7e72c7246032c91d4ea2ecb95152c7d2ff2313473e32c6f4b1633aa03752c69af7036288c932c6e253f38ab55242c7ebd353b2c6f3c2c9ddafc3da4821d2cce40f6400a8e7c2d131d0c4253b18a2d7015f94472ed992de957d9465905402e839d7a47f47fe32f4431604931fe6f3030dcaf49fd1ffb314fb0754a42592c32a682b149f24af63439d31549073dab360a88dc478d1cbf3811a4aa45aae0fc3a3913fb000ab8fa26eb134c000b72e526eb021d000c396826eaefc4000d0d5c26eadc2d000defaa26eac742000ee14b26eab0ed000fe34a26ea99150010f6c126ea7fa000121cdf26ea6472001356e726ea476d0014a63326ea287200160c3326ea075d00178a7126e9e40c0019229026e9be57001ad65026e99615001ca79126e96b1b001e985126e93d380020aab326e90c3a0022e0fc26e8d7ed00253d9a26e8a0160027c32526e86479002a746126e824d5002d544426e7e0e3003065f526e7985a0033acd126e74aeb00372c7226e6f841003ae8ac26e6a002003ee59a26e641ce0043279a26e5dd3e0047b35726e571e5004c8dcc26e4ff4e0051bc4b26e484fc0057448026e4026c005d2c7a26e3770e00637aaf26e2e24d006a360726e24387007165dd26e19a110079120e26e0e534008142fc26e0242d008a019926df562c0093577226de7a55009d4eb726dd8fba00a7f24626dc956200b34db826db8a4000bf6d6c26da6d3900cc5e9626d93d1c00da2f4826d7f8a800e8ee8826d69e8600f8ac5a26d52d48010979d226d3a36b011b692726d1ff52012e8dc626d03f470142fc6426ce61780158cb1626cc63f90170116426ca44bb0188e86326c8019401a36ad026c5983501bfb52626c3062f01dde5bf26c048ed01fe1cf026bd5db302207d2926ba419e02452b1326b6f1a2026c4db926b36a8802960eab26afa8ec02c29a2226aba93d02f21f2b26a767bb0324cfd526a2e076035ae157269e0f4f03948c472698eff603d20cc526937dea0413a2b0268db47c045991de26878ecd04a4224c268107d404f3a05f267a1a5d05485d172672c11205a2ae4e266af67c0602eef52662b50b06697f4f2659f72306d6c52f2650b721074b2c362646ef6e07c7260b263c9a8d084b2a9b2631b33008d7b8482626344e096d5421261a19450a0c8a0a260d5df80ab5ece225fffefa0b6a169b25f1f9bd0c29a84a25e34ccc0cf54a2125d3f80e0dcdab5825c3fd120eb381fe25b35f6d0fa78aab25a2252110aa880d2590571a11bd4245257e01c012e08614256b3599141523c32558080d155bedb62544944316b5b6a92530fc2718234f6d251d699019a58421250a0f9e1b3d18ba24f72c451ceac4c224e50a1e1eaf2e1624d4027f208ae27824c47fe3227e4fb524b700be2489ba0224ac1ac126ad304624a47ea628e87dc424a0fca92b3b18b624a289bc2da40d0d24aa45a23021e2b424b9822032b27e4924d1cb7a3552fb5824f4f26637ff7ee0252517cb3ab300fb2564ba863d670c9225b6c76140137474261eab6f42adfe3f26a06876452a05892740aac947781de52804de7c4985c1cc28f340054b3d2a122a12e01c4c8581142b6b8b5a4d43ccce2d0577eb4d5d29f12ee880174cbb4a48311a7a4d4b547c9f339bd7ff49385020366114e8469f924e39475942000aae9c1eca590b000b67d41eca4e55000c2d981eca42e4000d00c01eca36ad000de2351eca29a3000ed2ef1eca1bb7000fd3f71eca0cd90010e6661ec9fcfa00120b6b1ec9ec08001344481ec9d9f0001492551ec9c69f0015f7011ec9b200001773d31ec99bfc00190a6f1ec9847a001abc931ec96b61001c8c1d1ec95096001e7b091ec933fb00208b771ec915700022bfac1ec8f4d600251a141ec8d20700279d441ec8acde002a4bff1ec88532002d29371ec85ad8003038101ec82da200337be71ec7fd5f0036f8501ec7c9d9003ab1201ec792d9003eaa6b1ec758230042e88e1ec71977004770311ec6d691004c464a1ec68f28005170281ec642ef0056f3741ec5f194005cd6381ec59abf00631ee81ec53e110069d4651ec4db260070fe091ec471950078a3ab1ec400ec0080cda81ec388b1008984f11ec308640092d30c1ec27f7c009cc2261ec1ed6600a75d191ec1518800b2af7b1ec0ab3b00bec5a61ebff9cf00cbaccc1ebf3c8a00d972fe1ebe72a300e8273e1ebd9b4800f7d98f1ebcb59701089b061ebbc0a2011a7ddd1ebabb6a012d95811eb9a4e20141f6ad1eb87bee0157b77b1eb73f5d016eef7e1eb5edf10187b7d61eb4865401a22b4f1eb3072001be66791eb16eda01dc87c51eafbbf101fcafa61eadecbe021f00af1eabff8402439fb71ea9f26f026ab3fc1ea7c3920294674b1ea570e802c0e6281ea2f85502f05ff81ea057a30323072d1e9d8c84035911791e9a94940392b7fd1e976d5603d0377d1e94143a0411d0961e9086990457c7f91e8cc1bf04a266a51e88c2e704f1fa231e8487460546d4ca1e800c0a05a14dfd1e7b4e650601c26e1e764b95066894691e7100e906d62c131e6b6bd4074af7b71e6589f807c76c091e5f5935084c04701e58d7c208d943481e520444096fb2271e4addea0a0fe21a1e4364910aba6bdd1e3b98ec0b6ff00a1e337cb30c3117431e2b12dd0cfe92461e225fe00dd919f71e196a010ec16f4e1e1039a90fb85b311e06d9d510beae251dfd588c11d53fd81df3c77012fcee761dea3c6514369dc21de0d257158335dd1dd7aa1816e3a1ad1dceeb6e1858cccf1dc6c64419e3a0fe1dbf74181b8502c21db9399d1d3dcd4f1db468ab1f0ecd5b1db1628520f8baab1db09a7f22fc30181db299242519a1b01db7ffec275150791dc18da429a33b561dd023ac2c0f0c661de4cc382e9402071e00c1d73130d2821e25787a33e3892f1e54a86136a95ba21e905b4b397e752a1edafc743c5db6c91f376be13f4069831fa9159b421de12b20340d4f44eb0e5c20dd2e92479a001f21aa41464a19599722a220034c53c85623ccdb634e2f97b62533ceb14f8e9c4126e18f17504ee9d128e1884f504d28ef2b3ef1044f69fa7c2e0273ce4d94998a312d588a4add1e1634b00910478db28238594630000aa5391859f387000b5dcf1859ecd9000c22e61859e5b8000cf5561859de1b000dd6061859d5fb000ec5ef1859cd4d000fc6161859c40a0010d7971859ba260011fb9e1859af960013336b1859a45000148056185998460015e3cd18598b6c00175f5618597db40018f49318596f0e001aa54018595f6a001c733a18594eb8001e607d18593ce500206f26185929dd0022a1781859158d0024f9dd1858ffdd00277ae91858e8b6002a275c1858cffe002d02261858b59c00300e691858997100334f7f18587b600036c8fa18585b48003a7eab18583906003e74a5185814740042af411857ed6b004733231857c3c1004c05401857974800512ae1185767d10056a9ad18573529005c87ab1856ff180062cb491856c56500697b65185687d100709f551856461b00783eec1855fffd008062841855b52b0089130618556555009259f718551028009c417e1854b54900a6d4711854545700b21e621853ecee00be2ba818537e9f00cb096e185308f900d8c5c518528b8100e76fa9185205b400f7171d185177090107cd321850deee0119a42118503cc7012caf59184f8ff101410393184ed7be0156b6ee184e1375016de100184d425601869af1184c639201a0ff94184b765201bd2b86184a79b301db3d4918496cc401fb556118484e8b021d967a18471e000242258a1845da0f026929f4184481980292cdb01843137102bf3d7718418e6002eea8ec183ff124032142d0183e3a700357412a183c68ee0390dd84183a7b4203ce551b18387008040fe91e183645dc0455dee31833fb5704a0802a18318f1804f01b5f182effc5054503de182c4c15059f9236182972d306002478182672e606671e8018234b5e06d4ea43181ffb820749f81f181c82d607c6bf2a1818e135084bbd86181516df08d978b11811249509707dd6180d0bb20a1162141808ce4f0abcc2d318046f660b7345fa17fff3050c359a3717fb5e800d04772417f6b8b10de09d6f17f20a440ecad6e617ed5e080fc3f66c17e8c15e10ccd7d217e444a511e65f8417dffbcf13117a0b17dbfefd144f1b5117d86b4115a03d9417d5637e1705e00817d3116d188104f917d1a6d51a12af6917d15ef51bbbdff617d280301d7d90f217d55e0a1f58b16217da5b82214e1eb817e1eddc235e9cf717ec9ffc258accd117fb165e27d31f53180e13f32a37c68618267fec2cb8a23b18456cd42f55281e186c213d320c45eb189c225d34dc3c4d18d7413037c2709e191faaba3abb33611977fc343dc178d419e35c2f40ce80791a6599bf43d9683a1b03530e46d6a7ba1bc2246349b7716b1ca8e0504c68fa0e1dbfcff04ed3aebd1f10f64c50da725c20a849f3525a1e322293c6d35329c80d24e319c8531cd75f27a668595208e2842aeb43614fd2b1c52eb603674c86d8f732f47dca487f0ddc37661574000a9db9133ee06d000b55ce133edc45000c1a5a133ed7d4000cec37133ed317000dcc4a133ece07000ebb8b133ec89f000fbb00133ec2db0010cbc2133ebcb20011eefd133eb61e001325f1133eaf19001471f5133ea79a0015d474133e9f9900174ef6133e970e0018e31a133e8def001a929d133e8433001c5f58133e79cd001e4b47133e6eb400205885133e62db00228955133e56360024e01f133e48b500275f74133e3a4c002a0a14133e2ae9002ce2ec133e1a7d002fed1e133e08f500332c00133df63e0036a323133de245003a5656133dccf3003e49a9133db63100428172133d9de700470254133d83fb004bd140133d68500050f37e133d4aca00566eb1133d2b47005c48db133d09a80062886b133ce5c600693439133cbf7d00705399133c96a30077ee59133c6b0d00800cd0133c3c8d0088b7e5133c0af20091f918133bd608009bda8e133b9d9700a66718133b616400b1aa44133b213000bdb067133adcba00ca86aa133a93bb00d83b16133a45e800e6dcab1339f2f100f67b6513399a840107285513393c470118f5b31338d7dc012bf6ec13386ce1014040bc1337faed0155e94213378191016d08181337005a0185b66b133676cf01a00f141335e46e01bc2eba133548b201da33e91334a30f01fa3f371333f2f3021c7361133337c60240f574133270eb0267ecef13319dbf029183ed1330bd9a02bde751132fcfd002ed46ef132ed3b3031fd5c1132dc8930355ca15132cadbd038f5dc6132b828203ccce71132a4633040e5db51328f82c0454516b132797ce049ef3ec1326248804ee945713249ddc054386d313230365059e24e0132154d905fecda3131f92170665e634131dbb2f06d3d9f7131bd06a07491af11319d25d07c6221e1317c1f4084b6fcc1315a08b08d98bf713136ffb097106a5131132bf0a12783b130eec0b0abe81da130c9ff40b75cdb0130a53990c390f4313080d560d0903b81305d5000de672091303b4270ed22b2b1301b66a0fcd0a2212ffe9d310d7f3f312fe5f4a11f3d77912fd2b161321ad0a12fc6579146275e212fc2b6215b73b4812fc9f4717210d5c12fdea1f18a1017213003c8e1a382fe71303d0441be7b1451308e9a51db09a9a130fd9be1f93f8b81319009c2192ca311324d01b23adf7bc1333cf4f25e64a8613469ea5283c6012135dfce32ab09ae8137acd572d430f5a139e1f6e2ff36b4e13c9382832c0d7d813fd9dde35a9d2f4143d271738abff57148a0d453bc3e7b914e704903eecb25915575a36421fc09015df1b584554359216834686487e5ea2174a0aa44b8ef6d1183b15b34e7241f0195ff4f6510efff61ac4841f534549551c77602754ed891d1e8a3d4355d81ab52111d23655cebc562424af5e549a57df27d7a7035211e3cc2c3531c44e39ab3e312b552e4977bd5e366a386a000a98240f331be6000b4fd90f33194f000c13ff0f33168c000ce56e0f331399000dc50c0f331072000eb3d00f330d15000fb2c00f33097e0010c2f40f3305a90011e5980f33019200131beb0f32fd33001467420f32f8890015c90a0f32f38f001742c90f32ee3e0018d61c0f32e891001a84c00f32e283001c508e0f32dc0b001e3b800f32d524002047b10f32cdc5002277620f32c5e70024ccfa0f32bd8100274b0a0f32b48b0029f44f0f32aaf9002ccbb60f32a0c3002fd45e0f3295dc0033119e0f328a39003687040f327dce003a385d0f32708d003e29b70f32626800425f690f32534f0046de110f324333004baaa00f3232020050ca5b0f321fa9005642e20f320c16005c1a380f31f733006256c60f31e0eb0068ff650f31c92500701b640f31afc90077b28f0f3194bb007fcd3d0f3177e0008874500f31591a0091b1460f313848009b8e400f31154900a616100f30eff900b154400f30c83100bd55220f309dca00ca25dc0f30709700d7d4790f30406d00e66ff30f300d1c00f608470f2fd6700106ae850f2f9c35011874e30f2f5e33012b6ed10f2f1c2f013fb10a0f2ed5ea015551b10f2e8b25016c68600f2e3b9a01850e4b0f2de703019f5e510f2d8d1701bb75200f2d2d8701d971500f2cc80601f973800f2c5c40021b9e820f2be9e2024017720f2b7096026705e90f2af0050290941f0f2a67d602bcef160f29d7b202ec46cc0f293f43031ece6a0f289e330354bc780f27f434038e4b110f2740fa03cbb8220f268442040d45a20f25bdd5045339d50f24ed87049ddf900f24134004ed86800f232efc054283710f2240d5059d30a40f21490305fdee190f2047eb066521eb0f1f3e2106d338a40f1e2c770748a5990f1d140a07c5e34e0f1bf64b084b73cf0f1ad51608d9e11a0f19b2c60971bd800f1892480a13a4080f17773c0ac038d50f1666150b7829820f15643d0c3c2d830f1478460d0d06750f13aa1e0deb806b0f13034e0ed872270f128f430fd4bd470f125ba810e14e520f1278c711ff1ca70f12fa09132f2a450f13f67c1472835c0f15898415ca3d9c0f17d3991737772a0f1afb3918bb55350f1f2dfe1a5701fe0f24a1ef1c0baa3e0f2b970a1dda79b90f34592d1fc496cb0f3f424e21cb1cb70f4cbd4423ef14580f5d491426316ad10f717d0a2892e5c40f8a0dc42b1414580fa7d36b2db53c4e0fcbd188307642030ff740cc33568a16102b9b893654d2eb106aad91396f03c110b6a8ab3ca1ee7411123f0d3fe9000a1180c5de433ddb21120662694697d5cf12a8457649eb52f6136cf9204d28ed7b145cc662503c6b3d15823776530b704616eab9df5573f64d18a75a7b574aae3c1acd7f065859c69f1d77492558615a4720c2d318571c7eb824ce747b5451358929ae59d64ff63d102f54cacc4a795ee635645f74000a942c0bff4229000b4b9d0bff408d000c0f7a0bff3ed5000ce09b0bff3cff000dbfe60bff3b0a000eae520bff38f2000face30bff36b70010bcb20bff34550011deea0bff31ca001314cb0bff2f1200145fa80bff2c2c0015c0ee0bff291300173a210bff25c50018cce00bff223e001a7ae60bff1e7a001c460c0bff1a75001e304b0bff162b00203bbd0bff119600226aa30bff0cb20024bf620bff077a00273c8b0bff01e80029e4da0bfefbf6002cbb3c0bfef59e002fc2ce0bfeeed80032fee50bfee79e003673100bfedfe7003a231a0bfed7ac003e13100bfecee3004247470bfec5840046c45d0bfebb83004b8f410bfeb0d80050ad360bfea575005623dc0bfe9950005bf9330bfe8c5b006233a30bfe7e890068da040bfe6fcc006ff3a30bfe60130077884b0bfe4f4f007fa0500bfe3d6f008844940bfe2a6000917e920bfe160e009b586b0bfe006600a5dcee0bfde95100b117a40bfdd0b800bd14de0bfdb68400c9e1c10bfd9a9a00d78c560bfd7cdf00e623970bfd5d3600f5b7810bfd3b83010659240bfd17a501181ab60bfcf17c012b0fa80bfcc8e5013f4cb70bfc9dbc0154e8070bfc6fdc016bf9380bfc3f1e018499810bfc0b5a019ee3c70bfbd46801baf4c00bfb9a1b01d8eb0b0bfb5c4b01f8e7570bfb1acb021b0c7f0bfad56f023f7fb30bfa8c0d0266689f0bfa3e7a028ff1920bf9ec8d02bc47ac0bf9961f02eb9b0d0bf93b0e031e1f050bf8db3a03540a490bf8768b038d972d0bf80cf003cb03dd0bf79e62040c929a0bf72ae5045289fe0bf6b290049d35440bf6358704ece48a0bf5b40a0541ed270bf52e71059ca9f40bf4a53705fd7ba50bf418ff0664c9240bf38a9d06d2ffe80bf2fb1d0748945a0bf26bd007c602350bf1de5b084bccf10bf154c108da80280bf0d17c0972b0050bf0578a0a14f9ae0befea8e0ac203b30bef8eea0b7a7e740bef49e00c3f24910bef21bc0d10bb440bef1e050df012bf0bef47b50ede06790befa9780fdb7d6a0bf04ffd10e96a320bf14a531208cb210bf2aa52133aaa1a0bf4851f14801c450bf6f3c315da41800bfa13e0174a43820bfe088818d1549b0c02fb411a70adee0c091d361c298d140c10a8ac1dfd30f00c19e2c31fecd58a0c251d9321f9aead0c32bac32424e0f90c432ebc266f78fc0c57049028da5fe00c6ee2e12b664cee0c8b91fc2e13b3300cae039130e2aa040cd75c8e33d2cf4d0d0901b636e321670d44a7fd3a11ce810d8c69df3d5bf6220de2e37840bd58a70e4b57d6442fef090ec9e2db47ab63410f63bc544b245f43101f92784e8ba555110603fa51cce1a31222436654cd23b81382edb25768f460153b183b5972171b1763856d5aad57f61a1bb3275ad19fd31d89de66598b982921d7bb1a568d9dee2726d35451bb61702d72d5a54b845ed634544f32000a917009770a99000b48b109770999000c0c5c09770887000cdd4809770764000dbc5a0977062c000eaa88097704df000fa8d90977037c0010b863097702010011da510977006c00130fe20976febc00145a6b0976fcef0015bb580976fb020017342b0976f8f50018c6850976f6c4001a741e0976f46d001c3ed10976f1ee001e28940976ef43002033830976ec6b002261dd0976e9620024b6080976e624002732930976e2af0029da390976defe002cafe80976db0d002fb6bb0976d6d90032f2080976d25d0036655b0976cd93003a147f0976c878003e03820976c305004236b70976bd350046b2ba0976b701004b7c7a0976b0630050993a0976a95500560e980976a1ce005be294097699c700621b94097691380068c07009768818006fd87309767e5d00776b68097673fe007f81a1097668f00088240009765d2800915bff0976509a009b33bd0976433b00a5b609097634fc00b0ee6c097625d000bce936097615a900c9b38b0976047800d75b750975f22c00e5efec0975deb600f580ef0975ca0201061f8d0975b4000117ddff09759c9d012acfb6097583c5013f0972097569630154a15909754d64016baf1009752fb101844bd009751036019e92860974eedd01ba9fed0974cb9001d892af0974a63a01f88b8309747ec7021aad5009745521023f1d5709742937026603530973faf8028f89a80973ca5702bbdd8e0973974802eb2f42097361c5031db235097329ce03539d430972ef67038d2aed0972b2a003ca999309727390040c2bb40972325c045228320971ef38049cda960971aa6904ec93610971644b0541a85509711d54059c74cb0970d61905fd5a0809708f530664bf9d097049e906d313c1097006f60748cbbc096fc7d307c66445096f8e22084c61f8096f5bde08db51be096f33680973c93f096f179a0a166757096f0be00ac3d489096f144e0b7cc376096f35bf0c41f148096f75fb0d142626096fdbdf0df4359809706f8d0ee2fee009713aac0fe16d4d097248a510f078700973a6fc1211243c097565ab1344810109779796148bab36097a531515e7cb0e097db293175a13bd0981d55018e3c2600986e04a1a861c69098cff541c426d75099466661e1a0463099d5338200e2f7009a80f352220372e09b4f1de245157f409c463c526a2b96a09d6e237291563b409ed03db2baa31960a077e872e61bebb0a272eae313c51130a4d20f03439bbe80a7a9e7c37593abe0ab13d563a9941a20af2f5cf3df73f830b423f44416f4e180ba236dc44fbc92b0c16d4474894c4950ca5322b4c2f552a0d53f22c4fbc9c1c0e2bc7ba53287eed0f38385e5657f0771088a3b15926ae171231a44d5b6463f5144ecc245cd170d0170485505d1c5bab1a8138a95be362421efb28fc58c32ed724a490505386f19b2b8852164c988708333a5fa4000a8f98077700c8000b46ba07770029000c0a430776ff7f000cdb0a0776feca000db9f60776fe08000ea7fb0776fd3a000fa6200776fc5d0010b57b0776fb710011d7370776fa7600130c940776f96a001456e40776f84b0015b7950776f719001730280776f5d30018c23d0776f477001a6f8e0776f303001c39f30776f176001e23640776efce00202dfb0776ee0a00225bf70776ec280024afbe0776ea2500272bdf0776e8000029d3150776e5b6002ca84b0776e344002fae9f0776e0a90032e9640776dde100365c280776dae9003a0ab30776d7be003df9140776d45e00422b9c0776d0c40046a6e90776cced004b6fe80776c8d400508bdb0776c476005600600776bfce005bd3760776bad700620b830776b58c0068af5e0776afe8006fc6520776a9e5007758290776a37d007f6d3507769cab00880e56077695670091450807768daa009b1b680776856d00a59c4507767ca900b0d3270776735400bccc5f0776696800c9951107765edb00d73b47077653a300e5cdf9077647b800f55d2707763b0f0105f9e207762d9f0117b66307761f5d012aa61d0776103d013eddd207760037015473ac0775ef3e016b7f520775dd4901841a030775ca4c019e5eaf0775b63e01ba6a1a0775a11401d85af307758ac601f851fb0775734c021a722507755aa0023ee0bc077540be0265c58c077525a2028f4b090775094f02bb9e810774ebc702eaf0470774cd16031d73e80774ad470353606107748c72038cf05807746ab203ca62590774482f040bf9130774251b0451fba5077401b8049cb5da0773de5504ec78800773bb58054199b10773993f059c752e077378a105fd6cb307735a390664e85607733ee806d356ec077327bf07492e6d0773160407c6ec6007730b3f084d164a0773094508dc3a22077312460974eec2077328da0a17d46a077350190ac5952e07738bad0b7ee57c0773dff00c44848d077452070d173ce20774e8090df7e4b30775a92b0ee75e5307769def0fe698910777d06410f68efe07794c6912184a1d077b2008134cdf70077d5bd2149571620780135b15f32eee07835dcb176753070787568418f323a4078c1df21a97f0560791da851c57104d0798b9dd1e31dfa807a0f23a2029bbd707aac440223ffedf07b67d232475f92707c4795d26cce97507d5280e2945f2a107e90f422be20e530800d1642ea1fc13081d343931862b8b083f29f1348ea0a70867dd0837bacfc30898bfff3b096f6208d3a26c3e783c1c091acd724203aa1709712abd45a67d8709da7a61495940e60a5b9e324d118ba60afb03f950c106420bc13c77545410a30cb9d2d157afe5840df47f405ab00bfe0f86d5755d22ea53118e89ea5ec57e0b14343b8c5f3f064617ae07345e1fe67d1c3f37245aedc951222d5bbe55564a74299885b44db543ff32173dce000a8e5f05e2d1e4000b456c05e2d182000c08de05e2d118000cd98e05e2d0a7000db86005e2d02f000ea64a05e2cfaf000fa45205e2cf260010b38e05e2ce940011d52a05e2cdf800130a6305e2cd510014548f05e2cc9f0015b51705e2cbe100172d8005e2cb170018bf6805e2ca3f001a6c8905e2c958001c36bb05e2c862001e1ff505e2c75b00202a5205e2c6430022581105e2c5170024ab9605e2c3d80027277205e2c2840029ce5e05e2c118002ca34505e2bf95002fa94605e2bdf70032e3b205e2bc3e0036561705e2ba67003a043f05e2b872003df23605e2b65b0042244e05e2b42000469f2405e2b1c0004b67a505e2af370050831305e2ac840055f70b05e2a9a4005bc98d05e2a693006200fd05e2a34f0068a43305e29fd4006fba7905e29c1f00774b9905e2982d007f5fe405e293fa0088003c05e28f820091361a05e28ac1009b0b9d05e285b200a58b9305e2805100b0c18505e27a9a00bcb9c305e2748800c9817205e26e1500d7269c05e2673d00e5b83b05e25ffa00f5464f05e258480105e1e905e2502001179d4505e2477d012a8bd705e23e5b013ec26505e234b30154571905e22a82016b619f05e21fc10183fb3905e2146e019e3edd05e2088401ba495405e1fc0001d8395305e1eee101f82fa305e1e125021a4f4005e1d2cf023ebd8105e1c3e10265a23c05e1b460028f27f705e1a45502bb7c0f05e193cb02eaceeb05e182d3031d542f05e17181035342f305e15ff2038cd5fc05e14e4903ca4bf805e13cb1040be7c205e12b600451f0a405e11a9a049cb2a505e10ab004ec7ece05e0fc060541ab8305e0ef13059c94d705e0e46a05fd9ce505e0dcb706652c3305e0d8cb06d3b21105e0d99f0749a50905e0e05b07c7834505e0ee61084dd30905e1055408dd232205e1272409760b6505e1561f0a192d2a05e194fd0ac733cb05e1e6f80b80d52705e24fdd0c46d22005e2d42b0d19f71b05e3792f0dfb1c7605e4452e0eeb26fe05e53f890feb085405e670f910fbbf4105e7e3c7121e57f605e9a4161353ec2c05ebc03d149da31a05ee492915fcb14005f152e2177257db05f4f51618ffe41c05f94bd71aa6adda05fe786f1c6815c80604a2701e4582f3060bf8f420405f650614b434225a13af061f17762494010e062b738126ef79d7063a29a6296db7a5064bafab2c0fcebf066094c12ed69de5067987fc31c2b98c069760bf34d4512606bb29e5380b0cbf06e630a53b65e072071a18b73ee2d26e0758f7e7427eaecc07a57c434634a296080321a949fdb44808767dce4dd00b880905ad78519df2fc09b8f306555474bb0a9b9e6e58d963630bbd61e75c088f8d0d3443765eafdb470f1f62f06089f33711aab1e0613819e3151324c9603de84219a8d3275d098b231fc66ac957269a4027a6d1cb4ed9ca4230ebc9e9000a8d9204a3ef6f000b449104a3ef32000c07f504a3eef0000cd89504a3eeaa000db75704a3ee60000ea52f04a3ee10000fa32404a3edbb0010b24c04a3ed600011d3d204a3ed00001308f504a3ec980014530804a3ec2a0015b37604a3ebb400172bc404a3eb360018bd8e04a3eab0001a6a9004a3ea21001c34a104a3e989001e1db804a3e8e6002027ef04a3e8380022558604a3e77f0024a8e104a3e6b90027248f04a3e5e60029cb4c04a3e505002ca00004a3e415002fa5cb04a3e3150032dffe04a3e2040036522704a3e0e1003a000f04a3dfab003dedc204a3de6000421f9204a3dcff00469a1c04a3db88004b624d04a3d9f700507d6604a3d84d0055f10504a3d687005bc32804a3d4a30061fa3604a3d2a000689d0304a3d07c006fb2dc04a3ce350077438a04a3cbc9007f575d04a3c9350087f73804a3c67700912c9404a3c38e009b018f04a3c07600a580f904a3bd2e00b0b65a04a3b9b100bcae0204a3b5ff00c9751804a3b21400d719a504a3adee00e5aaa504a3a98900f5381704a3a4e40105d31004a39ffc01178dcb04a39acd012a7bbf04a39557013eb1b304a38f97015445d604a3898b016b4fd304a383320183e8f304a37c8b019e2c2f04a3759601ba365304a36e5501d8261d04a366c801f81c5a04a35ef3021a3c0f04a356da023eaa9c04a34e8502658fe104a345fc028f167104a33d4a02bb6bb604a3347e02eac02804a32bac031d477e04a322ea035338e604a31a56038ccf3e04a3121303ca495104a30a4c040bea1b04a303370451f90f04a2fd12049cc25c04a2f82b04ec974104a2f4dd0541ce5d04a2f397059cc40304a2f4db05fdda9e04a2f94506657b0a04a3019106d414fe04a30e99074a1f7504a3216407c8192104a33b27084e88da04a35d5008ddfe1e04a389910977118604a3c1e80a1a654f04a408b00ac8a5d604a460b20b828a2304a4cd350c48d46b04a552170d1c529604a5f3e60dfddec004a6b8010eee5faf04a7a4be0feec94904a8c19511001ced04aa1753122369c204abb05d1359cce504ad98f614a4717104afdf9e1604905604b29576177b6fef04b5ceca190a634804b9a3a51ab2c8f904be30981c76097904c3979b1e5594cf04ca012f2052df6a04d19dc0226f5de804daa75c24ac7f9204e563db270ba72504f227a0298e217e050159102c351999051375192f01891c0529150e31f424840542f662350d41a6056204ed384cb6c3058768d33bb1afec05b4996a3f3a775f05eb776342e42c4b062e717146aa61440680b8504a86989706e689af4e6f8fa107659d925258429f0805c812562e861808d1eb6459d9008209d964e75d3433f10b3234b3600e28c30cfc350c62203fc00f65b6c3630722ce12b16649623b138d173b55465f130d9f1d74246c58f512c925b6818550052c952fb90328000a8d0d03a86fc7000b440303a86fa1000c075e03a86f78000cd7f403a86f4d000db6ab03a86f1e000ea47803a86eed000fa26003a86eb80010b17b03a86e800011d2f403a86e440013080803a86e040014520b03a86dbf0015b26903a86d7600172aa503a86d290018bc5c03a86cd5001a694a03a86c7d001c334503a86c1e001e1c4603a86bb90020266503a86b4e002253e303a86adb0024a72303a86a60002722b403a869de0029c95203a86953002c9de603a868be002fa38f03a868200032dd9e03a8677700364fa003a866c40039fd5f03a86604003deae703a8653800421c8a03a8645e004696e503a86377004b5ee303a86280005079c703a8617a0055ed2f03a86063005bbf1803a85f390061f5e803a85dfd0068987603a85cad006fae0c03a85b4800773e7403a859cc007f51ff03a858390087f18f03a8568d0091269d03a854c6009afb4903a852e500a57a6003a850e600b0af6d03a84eca00bca6c003a84c8e00c96d8003a84a3100d711b603a847b200e5a26003a8451000f52f7d03a8424a0105ca2403a83f5f0117849003a83c4d012a723b03a83915013ea7ed03a835b501543bd703a8322f016b45a803a82e830183deaa03a82ab1019e21db03a826bc01ba2c0b03a822a601d81bfb03a81e7301f8128103a81a27021a32a603a815c9023ea1d103a81160026587ed03a80cf7028f0f9503a8089a02bb664003a8045902eabc7203a80046031d45f403a7fc7803533a0403a7f90b038cd39303a7f62003ca518703a7f3e0040bf6f603a7f27b04520b7003a7f22a049cdb4b03a7f33304ecb7ed03a7f5e70541f82403a7faa8059cf87a03a801e805fe1b9703a80c320665ca9e03a81a2606d4759703a82c84074a93db03a8442e07c8a48403a8622e084f2ee603a887c008dec30703a8b6570977fa2103a8efa80a1b772503a935b70ac9e74203a98ae20b84026b03a9f1f50c4a8be703aa6e390d1e52d203ab038f0e0032ac03abb6880ef113d203ac8c830ff1ebf803ad8bd61103be9103aebbfc12279d2603b025c4135ea78d03b1d39814aa0c0003b3d1c5160b070703b62ed81782e31b03b8fc0d1912f80a03bc4dd91abca9e303c03c881c81677503c4e50c1e62a81c03ca69f42061e8cc03d0f49f2280a81703d8b6be24c060ea03e1ec3c272283b203ecdda729a86d7803f9e34b2c535c71040969372f246139041bf483321c4bed04322a4d353b93d1044cd915388237ea046d057a3bef964f0493fbb93f82370b04c3681d4337860f04fd798c470b75b3054513274af7ffe3059e14af4ef4770f060dc5b852f48f4c069b76e156e6fa99075177e65ab35cdd083e939d5e3739e209785f3d61414f970b1ecf88638aa1320d61a46364aca6ac1087fe7d641602b614f8a14b610784c21b3a0cbb5abf09d823caaa1c51366a262e7ffaaa000a8cb802e221ad000b43a802e22195000c06fd02e2217c000cd78c02e22161000db63c02e22144000ea40202e22126000fa1e302e221050010b0f602e220e20011d26502e220bd0013077002e220950014516902e2206b0015b1bc02e2203d001729ed02e2200d0018bb9902e21fda001a687902e21fa3001c326702e21f68001e1b5902e21f2a0020256a02e21ee7002252d702e21ea00024a60602e21e540027218502e21e040029c80f02e21dae002c9c9002e21d52002fa22302e21cf00032dc1b02e21c8800364e0502e21c190039fbab02e21ba3003de91902e21b2600421aa002e21aa0004694dd02e21a12004b5cbc02e2197a0050778002e218d90055eac602e2182e005bbc8c02e217780061f33702e216b60068959f02e215e9006fab0d02e2150f00773b4c02e21428007f4ead02e213330087ee1102e2122f009122f302e2111c009af77202e20ff900a5765c02e20ec500b0ab3b02e20d8100bca26102e20c2a00c968f402e20ac100d70cff02e2094600e59d7f02e207b700f52a7602e206150105c4fa02e2045f01177f4902e20296012a6cdd02e200ba013ea28002e1fecc0154366502e1fccb016b403d02e1fabb0183d95402e1f89d019e1cac02e1f67301ba271902e1f44101d8175e02e1f20b01f80e5702e1efd7021a2f1202e1edaa023e9efd02e1eb8d0265860a02e1e98a028f0edb02e1e7ad02bb66f102e1e60402eabedc02e1e4a1031d4a7002e1e39a035340fa02e1e306038cdd7d02e1e30503ca5eef02e1e3ba040c087f02e1e551045221d502e1e7fb049cf76402e1ebf504ecdab202e1f186054222b302e1f902059d2c1e02e202ce05fe59ca02e20f5e0666151402e21f3d06d4ce4502e2330e074afd0002e24b9307c920b402e269af084fc11502e28e6c08df6e9902e2bb060978c2f902e2f0ef0a1c61b602e331da0acaf8a502e37fca0b85407702e3dd190c4bfd4a02e44c8f0d1fff3502e4d16f0e0222d002e56f930ef351bf02e62b830ff4832702e70a961106bc2602e81318122b102b02e94c761362a13c02eabf7714aea01602ec767a16104c2202ee7dc71788f32d02f0e3e91919f0d902f3ba281ac4ada502f715101c8a9d8302fb0d221e6d3dca02ffbfa9206e126703054fc3228ea216030be7b224d0715f0313ba842734fc0c031d063229bdaca8032816572c6bd190033547c02f408ed803450d20323ccc380357f54b35611dd0036eb3a838ada634038a2bbb3c21efa403ab81223fbcb97203d42e19437bb5460406239a475b2dec0443f7fe4b558e1904912bca4f62b83804f290ec53771778056ee85d57824390060fd7015b6cf79906e367f65f15f31e07fe7567624d1c6c098085a164cbe9890b99e8ae6629f8420e94e65c65ce2c0f12e15bf962e4c907191ac6d05c820da221e6175a526c78332d41ca7e0001000000010f3900011f5a000130700001428a000155b800016a0a00017f91000196600001ae8a0001c8240001e343000200002573004e4f2053414d504c45004e4f5420464f554e44004c4f4144494e47004c4f4f5000524556004010052c0404040407060506050507050505070206020207070107040707010301070505070101070407010707040705070701010202070507050707050701070702020202070407010707040604070705070404000207020030313233343536373839545345502b001010101010101f0e11111111110e1e11111e1010101e11111e14121111111111110a044c4f505256000e11131519110e040c040404040e0e11010204081f1f02040201110e02060a121f02021f101e0101110e0608101e11110e1f0102040808080e11110e11110e0e11110f01020c0e1111111f11111e11111e11111e0e11101010110e1c12111111121c1f10101e10101f1f10101e101010000000000000000000000000401173c8000000190000001600000001000000000000000000000000fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00000000000000000000000000001fe0000007f00007ffc0001f8000000ffc0000001f8000001f800001f8000003c0000000fc0000000e0000003c000000e0000000e000000038000000180000003800000060000000600000000000000000000000000000401173c8000000220000002200000002000000000000000000000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000000000000000000000000000000000000000ff000000000000007ffc0000000000000ffe00000000000ffffc0000000001ffff000000000007fc00000000000003ff00000000000000fffe00000000000003ffc00000000000000fc0000000000000ffc000000000001ffe0000000000003f800000000000003e000000000000001fe000000000000003fc000000000000001e000000000000007c00000000000003f800000000000007c00000000000000f0000000000000007c000000000000001f00000000000000078000000000000007800000000000001f000000000000003c00000000000000300000000000000038000000000000001c0000000000000000000000000000000000000000000401173c8000000300000002100000002000000000000000000000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff8000000003000018050000030c000305180003080003051c00021807030520000318000305240003040003052800031c0003052c00030007180500070308000305180701180703051c070308070305200703000e3005000e0200153005001501001c3005001c",
    "relocs": [
     [
      4522,
      "code",
      4324
     ],
     [
      5250,
      "code",
      4324
     ],
     [
      5760,
      "code",
      4324
     ],
     [
      5968,
      "code",
      4324
     ],
     [
      6116,
      "code",
      4324
     ],
     [
      6518,
      "code",
      4324
     ],
     [
      6906,
      "code",
      20532
     ],
     [
      6922,
      "code",
      4438
     ],
     [
      7214,
      "code",
      24636
     ],
     [
      7220,
      "code",
      23604
     ],
     [
      7642,
      "code",
      24636
     ],
     [
      7648,
      "code",
      23604
     ],
     [
      8102,
      "code",
      24636
     ],
     [
      8108,
      "code",
      23604
     ],
     [
      8394,
      "code",
      8476
     ],
     [
      8440,
      "code",
      8476
     ],
     [
      8910,
      "bss",
      390
     ],
     [
      8944,
      "cm_machine_index",
      0
     ],
     [
      8958,
      "code",
      12020
     ],
     [
      8978,
      "bss",
      0
     ],
     [
      8998,
      "bss",
      6
     ],
     [
      9058,
      "cm_machine_index",
      0
     ],
     [
      9072,
      "code",
      12020
     ],
     [
      9092,
      "bss",
      0
     ],
     [
      9112,
      "bss",
      6
     ],
     [
      9140,
      "bss",
      6
     ],
     [
      9174,
      "bss",
      0
     ],
     [
      9196,
      "bss",
      1436
     ],
     [
      9222,
      "bss",
      1796
     ],
     [
      54,
      "bss",
      1436
     ],
     [
      170,
      "bss",
      1436
     ],
     [
      332,
      "bss",
      390
     ],
     [
      362,
      "bss",
      384
     ],
     [
      372,
      "bss",
      372
     ],
     [
      382,
      "bss",
      378
     ],
     [
      394,
      "code",
      12030
     ],
     [
      532,
      "bss",
      914
     ],
     [
      716,
      "bss",
      1004
     ],
     [
      736,
      "code",
      6132
     ],
     [
      778,
      "bss",
      0
     ],
     [
      808,
      "code",
      6350
     ],
     [
      916,
      "code",
      41148
     ],
     [
      998,
      "code",
      6370
     ],
     [
      1034,
      "bss",
      1028
     ],
     [
      1064,
      "code",
      7032
     ],
     [
      1074,
      "bss",
      1004
     ],
     [
      1174,
      "bss",
      998
     ],
     [
      1186,
      "bss",
      1436
     ],
     [
      1200,
      "bss",
      372
     ],
     [
      1210,
      "bss",
      378
     ],
     [
      1220,
      "bss",
      384
     ],
     [
      1232,
      "bss",
      1028
     ],
     [
      1240,
      "code",
      6960
     ],
     [
      1350,
      "bss",
      390
     ],
     [
      1424,
      "bss",
      914
     ],
     [
      1608,
      "bss",
      1004
     ],
     [
      1628,
      "code",
      6132
     ],
     [
      1754,
      "cm_machine_index",
      0
     ],
     [
      1774,
      "code",
      12020
     ],
     [
      1908,
      "bss",
      914
     ],
     [
      2066,
      "code",
      6450
     ],
     [
      2074,
      "bss",
      384
     ],
     [
      2112,
      "bss",
      390
     ],
     [
      2152,
      "bss",
      378
     ],
     [
      2162,
      "code",
      12020
     ],
     [
      2170,
      "code",
      12030
     ],
     [
      2182,
      "bss",
      300
     ],
     [
      2288,
      "bss",
      1028
     ],
     [
      2368,
      "code",
      7032
     ],
     [
      2426,
      "code",
      6450
     ],
     [
      2472,
      "cm_machine_index",
      0
     ],
     [
      2484,
      "code",
      12020
     ],
     [
      2504,
      "bss",
      1028
     ],
     [
      2534,
      "code",
      7032
     ],
     [
      2584,
      "bss",
      384
     ],
     [
      2602,
      "bss",
      1028
     ],
     [
      2632,
      "code",
      7032
     ],
     [
      2676,
      "bss",
      384
     ],
     [
      2754,
      "code",
      6672
     ],
     [
      2804,
      "bss",
      1028
     ],
     [
      2814,
      "bss",
      378
     ],
     [
      2828,
      "bss",
      300
     ],
     [
      2866,
      "code",
      7032
     ],
     [
      2944,
      "bss",
      1436
     ],
     [
      2950,
      "bss",
      1028
     ],
     [
      2970,
      "bss",
      1436
     ],
     [
      3022,
      "bss",
      372
     ],
     [
      3028,
      "bss",
      998
     ],
     [
      3048,
      "bss",
      396
     ],
     [
      3054,
      "bss",
      44
     ],
     [
      3062,
      "code",
      6892
     ],
     [
      3070,
      "bss",
      12
     ],
     [
      3106,
      "bss",
      378
     ],
     [
      3152,
      "bss",
      1436
     ],
     [
      3180,
      "bss",
      300
     ],
     [
      3220,
      "bss",
      300
     ],
     [
      3310,
      "bss",
      1004
     ],
     [
      3522,
      "code",
      6132
     ],
     [
      3596,
      "bss",
      924
     ],
     [
      3636,
      "code",
      8326
     ],
     [
      3648,
      "bss",
      998
     ],
     [
      3654,
      "bss",
      372
     ],
     [
      3680,
      "bss",
      1464
     ],
     [
      3696,
      "bss",
      396
     ],
     [
      3702,
      "bss",
      44
     ],
     [
      3710,
      "code",
      6892
     ],
     [
      3718,
      "bss",
      12
     ],
     [
      3802,
      "bss",
      372
     ],
     [
      3822,
      "bss",
      998
     ],
     [
      3836,
      "bss",
      998
     ],
     [
      3846,
      "bss",
      372
     ],
     [
      3868,
      "bss",
      396
     ],
     [
      3874,
      "bss",
      44
     ],
     [
      3882,
      "code",
      6892
     ],
     [
      3890,
      "bss",
      12
     ],
     [
      3996,
      "bss",
      1464
     ],
     [
      4006,
      "bss",
      998
     ],
     [
      4026,
      "bss",
      1464
     ],
     [
      4076,
      "bss",
      396
     ],
     [
      4082,
      "bss",
      44
     ],
     [
      4090,
      "code",
      6892
     ],
     [
      4098,
      "bss",
      12
     ],
     [
      4166,
      "code",
      8246
     ],
     [
      4252,
      "bss",
      924
     ],
     [
      4320,
      "code",
      8326
     ],
     [
      9404,
      "bss",
      55702
     ],
     [
      9412,
      "bss",
      55698
     ],
     [
      9440,
      "bss",
      62358
     ],
     [
      9518,
      "bss",
      55698
     ],
     [
      9524,
      "bss",
      1934
     ],
     [
      9552,
      "bss",
      55698
     ],
     [
      9584,
      "bss",
      1934
     ],
     [
      9612,
      "cm_machine_index",
      0
     ],
     [
      9618,
      "code",
      9370
     ],
     [
      9634,
      "cm_machine_index",
      0
     ],
     [
      9670,
      "code",
      9370
     ],
     [
      9712,
      "bss",
      1934
     ],
     [
      9728,
      "bss",
      1806
     ],
     [
      9738,
      "bss",
      1806
     ],
     [
      9752,
      "bss",
      1810
     ],
     [
      9778,
      "bss",
      1806
     ],
     [
      9784,
      "bss",
      1802
     ],
     [
      9848,
      "cm_machine_index",
      0
     ],
     [
      9856,
      "bss",
      1806
     ],
     [
      9896,
      "bss",
      1798
     ],
     [
      9908,
      "bss",
      55698
     ],
     [
      9936,
      "code",
      9594
     ],
     [
      9978,
      "code",
      9370
     ],
     [
      10028,
      "cm_machine_index",
      0
     ],
     [
      10066,
      "cm_machine_index",
      0
     ],
     [
      10076,
      "bss",
      1910
     ],
     [
      10140,
      "cm_machine_index",
      0
     ],
     [
      10178,
      "bss",
      55710
     ],
     [
      10186,
      "code",
      9186
     ],
     [
      10208,
      "bss",
      1934
     ],
     [
      10260,
      "bss",
      62366
     ],
     [
      10294,
      "bss",
      55714
     ],
     [
      10564,
      "bss",
      1796
     ],
     [
      10630,
      "bss",
      62366
     ],
     [
      10666,
      "bss",
      62366
     ],
     [
      10686,
      "bss",
      1798
     ],
     [
      10698,
      "bss",
      55698
     ],
     [
      10706,
      "bss",
      1798
     ],
     [
      10712,
      "bss",
      55702
     ],
     [
      10748,
      "bss",
      62358
     ],
     [
      10774,
      "code",
      9594
     ],
     [
      10792,
      "code",
      9370
     ],
     [
      10798,
      "bss",
      1910
     ],
     [
      10840,
      "code",
      9594
     ],
     [
      10868,
      "bss",
      390
     ],
     [
      10924,
      "bss",
      55714
     ],
     [
      10972,
      "bss",
      62370
     ],
     [
      11020,
      "bss",
      55698
     ],
     [
      11050,
      "bss",
      1938
     ],
     [
      11056,
      "bss",
      28818
     ],
     [
      11062,
      "bss",
      29028
     ],
     [
      11286,
      "bss",
      55698
     ],
     [
      11334,
      "bss",
      29028
     ],
     [
      11348,
      "bss",
      28818
     ],
     [
      11354,
      "bss",
      1938
     ],
     [
      11594,
      "bss",
      1796
     ],
     [
      11612,
      "bss",
      62370
     ],
     [
      11630,
      "bss",
      1796
     ],
     [
      11670,
      "bss",
      1796
     ],
     [
      11712,
      "bss",
      1796
     ],
     [
      11818,
      "bss",
      1796
     ],
     [
      11906,
      "code",
      9236
     ],
     [
      11944,
      "bss",
      1796
     ],
     [
      12046,
      "bss",
      55702
     ],
     [
      12054,
      "bss",
      55698
     ],
     [
      12080,
      "bss",
      62358
     ],
     [
      12108,
      "bss",
      55698
     ],
     [
      12230,
      "cm_machine_index",
      0
     ],
     [
      12344,
      "code",
      9236
     ],
     [
      12358,
      "bss",
      1810
     ],
     [
      12374,
      "bss",
      1910
     ],
     [
      12394,
      "bss",
      1880
     ],
     [
      12408,
      "bss",
      1802
     ],
     [
      12414,
      "bss",
      1882
     ],
     [
      12420,
      "bss",
      1798
     ],
     [
      12426,
      "bss",
      1810
     ],
     [
      12474,
      "cm_machine_index",
      0
     ],
     [
      12540,
      "cm_machine_index",
      0
     ],
     [
      12600,
      "bss",
      55702
     ],
     [
      12608,
      "bss",
      55698
     ],
     [
      12636,
      "bss",
      62358
     ],
     [
      12690,
      "bss",
      28818
     ],
     [
      12702,
      "bss",
      1938
     ],
     [
      12722,
      "code",
      19532
     ],
     [
      12728,
      "bss",
      1796
     ],
     [
      12752,
      "code",
      9706
     ],
     [
      13176,
      "code",
      12956
     ],
     [
      13338,
      "code",
      41380
     ],
     [
      13374,
      "code",
      41386
     ],
     [
      13386,
      "code",
      12768
     ],
     [
      13626,
      "code",
      41345
     ],
     [
      13634,
      "code",
      12768
     ],
     [
      13674,
      "code",
      41386
     ],
     [
      13790,
      "cm_machine_index",
      0
     ],
     [
      13836,
      "code",
      13682
     ],
     [
      14028,
      "code",
      13682
     ],
     [
      14180,
      "code",
      13980
     ],
     [
      14224,
      "code",
      13980
     ],
     [
      14272,
      "code",
      41330
     ],
     [
      14310,
      "code",
      41330
     ],
     [
      14328,
      "code",
      41254
     ],
     [
      14544,
      "code",
      12956
     ],
     [
      14796,
      "code",
      12020
     ],
     [
      14898,
      "code",
      41244
     ],
     [
      14920,
      "code",
      41249
     ],
     [
      14964,
      "code",
      41200
     ],
     [
      15328,
      "code",
      12956
     ],
     [
      15590,
      "code",
      12768
     ],
     [
      15596,
      "code",
      41380
     ],
     [
      15648,
      "code",
      41386
     ],
     [
      15706,
      "code",
      13158
     ],
     [
      15722,
      "code",
      13292
     ],
     [
      15874,
      "code",
      12580
     ],
     [
      15928,
      "code",
      41223
     ],
     [
      15934,
      "code",
      41200
     ],
     [
      16162,
      "code",
      41345
     ],
     [
      16216,
      "code",
      41386
     ],
     [
      16284,
      "code",
      12580
     ],
     [
      16322,
      "code",
      41203
     ],
     [
      16328,
      "code",
      41200
     ],
     [
      16450,
      "code",
      13158
     ],
     [
      16460,
      "code",
      13292
     ],
     [
      16568,
      "code",
      14234
     ],
     [
      16840,
      "code",
      41213
     ],
     [
      16846,
      "code",
      41200
     ],
     [
      17624,
      "code",
      13682
     ],
     [
      17722,
      "code",
      14772
     ],
     [
      17748,
      "code",
      14772
     ],
     [
      17810,
      "code",
      14772
     ],
     [
      17840,
      "code",
      13682
     ],
     [
      17850,
      "bss",
      62358
     ],
     [
      17886,
      "cm_descriptor_base",
      0
     ],
     [
      17896,
      "cm_descriptor_base",
      1
     ],
     [
      17966,
      "cm_descriptor_base",
      1
     ],
     [
      18014,
      "code",
      41240
     ],
     [
      18030,
      "code",
      41240
     ],
     [
      18102,
      "cm_machine_index",
      0
     ],
     [
      18156,
      "code",
      14772
     ],
     [
      18162,
      "bss",
      62358
     ],
     [
      18350,
      "code",
      14772
     ],
     [
      18384,
      "code",
      14772
     ],
     [
      18436,
      "code",
      14772
     ],
     [
      18442,
      "bss",
      62358
     ],
     [
      18468,
      "code",
      14772
     ],
     [
      18474,
      "bss",
      62358
     ],
     [
      18530,
      "bss",
      62358
     ],
     [
      18574,
      "code",
      13682
     ],
     [
      18866,
      "code",
      12956
     ],
     [
      18964,
      "code",
      14510
     ],
     [
      19018,
      "code",
      14234
     ],
     [
      19058,
      "code",
      41231
     ],
     [
      19076,
      "code",
      13292
     ],
     [
      19116,
      "code",
      41236
     ],
     [
      19134,
      "code",
      13292
     ],
     [
      19220,
      "code",
      14510
     ],
     [
      19242,
      "code",
      41236
     ],
     [
      19260,
      "code",
      13292
     ],
     [
      19284,
      "code",
      14510
     ],
     [
      19304,
      "code",
      41231
     ],
     [
      19322,
      "code",
      13292
     ],
     [
      19452,
      "cm_machine_index",
      0
     ],
     [
      19534,
      "bss",
      62354
     ],
     [
      19610,
      "code",
      13814
     ],
     [
      19622,
      "bss",
      62354
     ],
     [
      19640,
      "code",
      14146
     ],
     [
      19652,
      "bss",
      62354
     ],
     [
      19664,
      "code",
      14190
     ],
     [
      19680,
      "bss",
      62354
     ],
     [
      19706,
      "code",
      12114
     ],
     [
      19746,
      "code",
      12114
     ],
     [
      19782,
      "bss",
      390
     ],
     [
      19842,
      "code",
      8886
     ],
     [
      19946,
      "code",
      9012
     ],
     [
      20002,
      "bss",
      390
     ],
     [
      20020,
      "code",
      9126
     ],
     [
      20046,
      "code",
      9126
     ],
     [
      20088,
      "code",
      19356
     ],
     [
      20138,
      "code",
      12452
     ],
     [
      20188,
      "code",
      12452
     ],
     [
      20238,
      "code",
      12508
     ],
     [
      41498,
      "code",
      42310
     ],
     [
      41502,
      "code",
      41738
     ],
     [
      41506,
      "code",
      41510
     ],
     [
      41526,
      "code",
      41638
     ],
     [
      41530,
      "code",
      41538
     ],
     [
      41754,
      "code",
      42038
     ],
     [
      41758,
      "code",
      41766
     ],
     [
      42326,
      "bss",
      62366
     ],
     [
      42330,
      "code",
      42338
     ],
     [
      20266,
      "bss",
      62362
     ],
     [
      20302,
      "code",
      42722
     ],
     [
      20308,
      "bss",
      62366
     ],
     [
      20496,
      "code",
      42820
     ],
     [
      20508,
      "bss",
      62362
     ],
     [
      20528,
      "code",
      12714
     ]
    ],
    "symbols": {
     "sampler_update": [
      "code",
      0
     ],
     "sampler_render": [
      "code",
      2890
     ],
     "smp_hook_open": [
      "code",
      19688
     ],
     "smp_hook_preview": [
      "code",
      19730
     ],
     "smp_hook_pad_on": [
      "code",
      19770
     ],
     "smp_hook_pad_off": [
      "code",
      19990
     ],
     "smp_hook_key_on": [
      "code",
      19886
     ],
     "smp_hook_key_off": [
      "code",
      20036
     ],
     "smp_hook_save2": [
      "code",
      20100
     ],
     "smp_hook_save1": [
      "code",
      20150
     ],
     "smp_hook_load": [
      "code",
      20200
     ],
     "smp_hook_tick": [
      "code",
      12714
     ],
     "smp_main_draw": [
      "code",
      17606
     ],
     "smp_knob_draw": [
      "code",
      17820
     ],
     "smp_note_draw": [
      "code",
      18520
     ],
     "smp_hook_pan": [
      "code",
      20062
     ],
     "smp_hook_pan_all": [
      "code",
      20074
     ],
     "sample_pictures": [
      "code",
      41498
     ],
     "sample_hook_tick": [
      "code",
      20250
     ]
    },
    "bss": 62752
   }
  },
  "solid": {
   "id": "solid",
   "name": "SOLID: a bank of modes struck by a mallet, a noise burst or sustained noise, from string to glass",
   "order": 71,
   "version": "0.1",
   "symbols": {
    "update": "solid_update",
    "render": "solid_render"
   },
   "keep": [
    "solid_pictures",
    "solid_hook_tick"
   ],
   "patch_points": [],
   "uses": [
    {
     "point": "machine",
     "name": "SOLID",
     "image": 3,
     "decay_default": 80,
     "pictures": "solid_pictures",
     "knobs": [
      {
       "long": "Solid Bright",
       "short": "BRIT",
       "default": 64
      },
      {
       "long": "Solid Body",
       "short": "BODY",
       "default": 51
      },
      {
       "long": "Solid Pickup",
       "short": "PICK",
       "default": 40
      },
      {
       "long": "Solid Exciter",
       "short": "EXCT",
       "default": 30
      }
     ]
    },
    {
     "point": "screen.tick",
     "hook": {
      "at": "0x400075f0",
      "stock": "4eb940076be4",
      "op": "jsr",
      "symbol": "solid_hook_tick"
     }
    }
   ],
   "conflicts_declared": [],
   "claims": {},
   "bundle": {
    "code": "4fefffe448d70c7c226f0024243c0000031c22090681bdcf77d84c421001246f0028263c4d4f4431b6a9002c674e243c000001604c0128002042d1fc0000000020080680000001604218b08866fa203c9e3779b94c0108002042d1fc0000000047f900000000283c4d4f443142b31c0006801234567820802344002c4aa90038676a2c3c012c0f26203c001f7c5c243c7fffffff263c82581e4b283c803ef8b82346027823460274234002842340028023420294234202902343027c234402884a6a001e670001702c3c200000007601203c60000000243c400000002346029c234002a0234202a423430048243c8000000123420250716a0014756a0022e188204241e8c0002608e78bd0af0020d0830680ffc000000c80007f00006f0000e0707f4840742c382a00204c0128007d6a00167b6a001847f900000000278628087d6a001a4a4456c3278628107d6a001c278028042786281477037d6a00242785280c44832786281842b3281c278328244aa90038670a41f90000000042b01c004aa9003c67084aa900346700009a4a44677841f9000000004ab01c0056c37703448341f3280042b32800214300284aa900386740227c40fe4c90787f77711a00b8836d4a4a836d000094c7fc01022143002041f900000000b0b01c0067000096760243f9000000002783280021801c0023851c004cd70c7c4fef001c4e754a806c00ff2242806000ff1c42836094767fc7fc01022143002041f900000000b0b01c0066bc604e41f900000000760121831c006000ff5a283c7fffffff2c3c20000000203c400000002344029c234602a0234002a442a900486000fe924283c7fc01022143002041f900000000b0b01c006600ff6e43f900000000260596b11c000683000000ff0c83000001fe621276012783280021801c0023851c006000ff5676022783280021801c0023851c006000ff444fefff6c48d77cfc202f009c243c0000031c0680bdcf77d84c420000263c00000160722c4c0038004c0018002043d1fc000000002f4300404a906600106841f9000000002f4100482f4800584ab0180067000ce0a9812f410090206f0040d1fc00000000246f0048d5fc000000002f480064a93c000000a0a13c00000000226f0058286f00482071c8004a88670000d4222a00200c8100007fff6e00110e4a816d0011782a6f0058242f0048226f0064266f0040d7fc0000000020352804234100cc0c80007f00006e0010aa4a806d001116243c7fffffff7602286f0058222f0048226f0040d3fc0000000026804bf41814234200e0235500d4b688670011a0206f0040d1fc0000000020104a806f2a74184c020800206f006443f008002010220020280004e281e28041e800182141ffe82140ffecb3c866e4206f0040d1fc0000000042902f0a2f2f00684eb900000000508f7001206f0040d1fc000000002080206f0040d1fc000000004aa800dc67084aa800d867001292206f0040d1fc000000004aa8013866000a16206f0040d1fc000000004a9067000a4e206f0058d1ef0048222800242f41005c4a81670e4aa8002856c0710044802f40005c226f0058206f0040d1fc00000000242800d0d3ef00482f42008c2629000c286900082f4300782f4c007c4aa8013c6708b4a80140670012f2206f0058226f00482030981c206f0040d1fc0000000022100c8000007f006e000ab84a806d000b52c1fc18304c011800ee80d281a2000800a1c0206f0040d1fc000000002210a2000800a1c0d0af008c74032a2f00780680ffbb0000ed884c420800068008c807312f4000680c8500007f006e000a424aaf00786d000adecbfc0500767f4c43580570052405484248c2b08267000f50720fe3ad2e02528202857fff80004878001c222f00800c8100007f006f000dc4223c00007f00203c0000400076059081720de3a849f9000000004c4308002f004e942f40005c508f4a806d000f70206f0058226f0048207098182f4800802f480088b1fc00007f006f000ca4223c00007f002f410088223c08b64043202f008848404240a2000800a1c141f90000000020307c0020702c0091c0aa080800a1c47fc7206f00580681fa5b2c3e226f0048d084d280ed8f20709810246f00402608d5fc000000002f4800842f41006c2647d7fc00000000b1fc00007f006f000ca6263c00007f0075c2c7fc8427202f004006800000000022402040ed8a43e900d8428641e801342f4700440683400000002c472a47ddfc00000000dbfc0000000042af00502f4300602f42003c2f4900702f4800742e03204b91ef0044226f003c2413203098009082aa000800a1c0d480282f0068d8820c840e6614106e0001a8204e588b91ef0044201e223098009280aa010800a1c1d081222f0054a2000800a1c3e78b204d91ef0044201d2230980092802f43004caa010800a1c1262f0054d081a6000800a1c0e788d0af006c4aaf005c670009ec0c80fcf0ec586f0009e2203cfcf0ec58223cf33ccad94878001f92802f014e94508f22004a806d0010ec227c7fffffff93c0a2010800a1c32f43002ca2030800a1c0a2000800a1c176fa2f4100344c430800262f00342f40003070184c4038032f430034262f002ce283d689d6af0030d6af0034206f00704a90670c227c7ee55036a2430800a1c342a70684107302422f044e942f002f4000444eb900000000222f00440681400000002f0128004eb900000000a0000800a1c12241a8040800a1c12041223c7fffffff92899288e281a2030800a1c1d283a2000800a1c02480a2040800a1c02540000452862f074eb9000000004a806d0006c8223c7999999aa2000800a1c44878001f2f2f00644e940684066666664fef001c4a806d000724a0040800a1c025400008a0000800a1c0e880206f0074d1af00504a90660006acdeaf006045ea00187008b0866600fe32206f0040d1fc000000002010b0866f24340672184c010800d0af0064c4fc00182042d1ef006442a80004429041e80018b08866f2206f0040d1fc0000000020864aaf00506f684878001b2f2f00544eb9000000004878001ae28044802f004e944fef00104a806d000f524a866740ccfc0018206f0040d1fc00000000227c333333332206d2882410a0020800a1c20c8203ffffff6f06243c03ffffffeb8aa2420800a1c2208241e80018b28866d8302f008a48780018263cf5fa5f7ec1fc19cdec8006800007ae142f004eb9000000004878001896802f034e944fef00104a806d000f304878001f44802f004e94508f4a806d000bd0206f0040d1fc000000002140015c7001216f008c0140216f00780144216f007c01482140013c216f0080014c216f00840150216f005c0154216801340158206f0040d1fc00000000202800d84a8066000a8e226f0058286f00484ab1c81c66000bdc206f0040d1fc000000002a680134262800e42a2800e82f4d0048ba836e0c2028010cb0a801086f000cf041f9000000004298b1fc0000000066f672012f410050206f0040d1fc0000000024100c820000008f6e000a2041f9000000004298b1fc0000000066f672022f4100444aaf0048671041f9000000004298b1fc0000000066f6266f0040d7fc000000002c0b0686000000ec45f9000000004deb00f04bf90000000049eb00f4b6856c2628162f044e9520462210a0010800a1c0d894528324c0274300e42c84588fb5fc0000000066d6206f0040d1fc0000000043f9000000002a3c7cb5ae9449e800fc47e801004be801040c820000008f6e4c202800c8223c0019660d26144c01080006803c6ef35f214000c8a6000800a1c422132004e281e28026849081aa030800a1c322152883a2000800a1c0528222c0214200f8b3fc0000000066ac266f0040d7fc00000000242b0108283c0590b2162c0b0686000001102a0b24464c02480049f90000000006850000011c4deb010c4beb01182c3c000000002056b4886c70202b00c8263c0019660d2215227c45a3d1c64c03080006803c6ef35f4c003800e48006833c6ef35f2e03e487274300c8d0879081a2400800a1c0d2802a817017b0826d0005082004a0010800a1c0222b0114a2000800a1c0d09452822742010806840590b21628c0b9fc00000000668a24464aaf0048670000e0286f0040d9fc00000000242c0124223cfff776e62c2c01282a3c0008891a263c001113574c0218004c0658004c023800202c00c828020684fffff8802c7c342cbbbb988643f90000000047ec012cda814bec01300685c00442ff223c0019660d4c01080020432200203c0019660d06813c6ef35f4c01080006803c6ef35f0c820000077f6f124a846d0004fc0c8400000eff6e000c3a20452e00e481e4872c13d2879286ac410800a1c1dc812686a0460800a1c12055a0410800a1c1528222c1294201240683001113570685fff776e65284b3fc000000006680294000c8206f00984aaf0044660004f247e800804298b1cb66fa206f0040d1fc0000000022102f4800444aaf0048670004fa4aaf005067000a304a816f000bee42af00502c6f00649bcd42af00482f4b005445f900000000226f009841f900000000242e0004282e0008262e000c286e0010266e00142016220020182a1aaa0b0800a1c7a8010800a6020900a1c6d0872a012200d286a6050800a8020800a1c2a8420800a1c0d09122c0b1fc0000000066c820012c812d4200044a826d000a52bbc26f02240d4a806d000a4c2a42b0826f022a4052af0048286f0048226f00444dee0018b9d16d00ff6a266f00542f4d0050206f0040d1fc00000000202800e02228015ca2000800a1c0214000e04aa800dc66604aa800d8665a2a6800e8bbe800e46e50203c0000008fb0a800f86c442228010cb2a801086e3a4aa801346634242f00500c82000003ff6e28206f0064202f004006800000000042a80004429041e80018b1c066f2206f0040d1fc000000004290206f009c4aa80048670005c8206f00982018223c7fffffff0c8007ffffff6e0e0c80f80000006d0005962200e9892141fffcb7c866da2f2f009c4eb9400a92522f2f00a02f2f00a04eb9400a967a4fef000c222f0090a9014cd77cfc4fef00944e75226f0058286f00484ab1c8286700f5de202801240c80000007806c06203c000007800680fffff88021400128206f0040d1fc000000004290206f0040d1fc000000004a906600f5b6206f009847e800804298b1cb6700ff484298b1cb66f26000ff3e4480223c7999999aa2000800a1c44878001f2f2f00644e940684066666664fef001c4a806c00f93a6058a6030800a1c1203c7fffffffe0829081720182804878001f2f014eb9000000004878001f2202e280e5899481ed8a2042487008004e944fef00104a806d0000ba2540000cdeaf006045ea00187008b0866600f7446000f910203c7fffffffa0040800a1c025400008a0000800a1c0e880206f0074d1af00504a906700f8da60802a3c00007f00767fcbfc05004c43580570052405484248c2b0826600f5c46000050e203c00007f00c1fc18304c011800ee80d281a2000800a1c0206f0040d1fc000000002210a2000800a1c0d0af008c74032a2f00780680ffbb0000ed884c420800068008c807312f4000680c8500007f006f00f54c6088203c7fffffff2540000c6000ff40206f009820080680000000804298b1c06700fe524298b1c066f26000fe484285cbfc0500767f4c43580570052405484248c2b0826600f5246000046e4280c1fc18304c011800ee80d281a2000800a1c0206f0040d1fc000000002210a2000800a1c0d0af008c74032a2f00780680ffbb0000ed884c420800068008c807312f4000680c8500007f006f00f4b06000feec91d2203c7fffffffb4886d00faf0204526102243d3fc400000002f092f41003c4eb900000000d6ab0120588f2045e2802083222f0038068040000000a0010800a1c0222b0114a2000800a1c0d09452822742010806840590b21628c0b9fc000000006600fa4a6000fabc0c80f73ccada6c00f61e0c80f03ccad96d000086263cf3c428154878001896802f034e94508f4a806d00029c44804878001f2f004e94508f26004a806c00f64c263c7fffffff6000f6422e00e481e4872c13207c7fffffffd2879286ac410800a1c1dc812686a0460800a1c12055a0410800a1c1528222c1294201240683001113570685fff776e65284b3fc000000006600fa8c6000fb0842836000f5ee20dab5fc0000000066f6266f0098206f0040d1fc00000000221047eb00802f4800444aaf00486600fb0a4aaf0050670003d24a816f0006f642af00502c6f004499cc2f4b0044246f00642a6f0048266f00982212224b202a0004262a0008242a000c2e2a001041f9000000002c18a6010800a4000900a1c528012206d285a4040800a6000800a1c0ae000800a1c4d89122c4b1fc0000000066d22481254000044a806d00048eb9c06f02200c4a816d00047c2840b2806f022841528d45ea0018bbd66d8e266f00442f4c00506000fb244aaf00806c00f36242af0088223c08b64043202f008848404240a2000800a1c141f90000000020307c0020702c0091c0aa080800a1c47fc7206f00580681fa5b2c3e226f0048d084d280ed8f20709810246f00402608d5fc000000002f4800842f41006c2647d7fc00000000b1fc00007f006e00f35e4aaf00846c00f35c75c24283c7fc8427202f0040068000000000ed8a2240204043e900d8428641e801342f4700440683400000002c472a47ddfc00000000dbfc0000000042af00502f42003c2f4300602f4900702f4800742e036000f3564aaf00806c00f23e4281203c0000400076059081720de3a849f9000000004c4308002f004e942f40005c508f4a806c00f23c600001a641f9000000002f4100482f480058a981206f0040d1fc000000002f4100902f480064246f0048d5fc00000000a93c000000a0a13c00000000226f0058286f00482071c8004a886700f0766000efa0203c800000016000fd60223c800000002141fffcb7c86600fa446000fa66206f009820180c8007ffffff6f26203c07ffffffe7882140fffcb7c866e62f2f009c4eb9400a9252588f222f0090a9016000fa540c80f80000006cd8203cf8000000e7882140fffcb7c866b860d042af00446000f5f2538042a8013c214000d86000f578286f0058243c7fffffff222f00487602707f4840226f0040d3fc000000004bf41814234200e02680235500d4b6886600ef5c600000f62a6f0058223c00007fff242f0048226f0064266f0040d7fc0000000020352804234100cc0c80007f00006f00eef6609a2a3c7fffffff7e046000f0b6286f00584280222f0048243c7fffffff226f0040d3fc00000000268076024bf41814234200e0235500d4b6886600eeec600000862a6f00584281242f0048226f0064266f0040d7fc0000000020352804234100cc0c80007f00006f00ee8a6000ff2e223c7fffffff2f4100546000f086203c7fffffff206f0040d1fc000000002140015c7001216f008c0140216f00780144216f007c01482140013c216f0080014c216f00840150216f005c01542168013401586000f42a4aa900c46700ee5c70057201206f0040d1fc00000000234000d87001234100dc20806000eea042a8013c6000f4207001b0816c00032c286f00644285242f0050262f00982a6f004445f9000000002f032f0c4e9220144a806d0000f0222c00044a816d0000da508fb2806f022001222c00184a816d0000ceb2806f022001222c001c4a816d0000b2b2806f022001b0826f0224002215200549ec003056805485b2806eaa2f420050b2856f00f77272184c01580045f900000000222f004043f900000000206f0098d285d5c1202a000422311800242a0008226a000c282a0010a4010800a24009002601a1c1a2430800a4000800a1c0a8000800a1c3d69020c3b7c866dcdaaf004049f90000000029815800298058044a816d0002344a806d000224b0816e000210b2af00506f00f6f02f4100506000f6e844816000ff4c44816000ff2444816000ff30222c000444804a816c00ff1260e644816000fb8244806000fb7042af00506000f32242a800dc2f0a2f2f00684eb900000000508f206f0040d1fc000000004aa801386700ed606000f7704a816f00f6862f4b00482a6f00649dce266f005049f90000000041f9000000002215226f0098202d0004262d0008242d000c246d00102e2d00142818a8070800a1c6a6010800a4000900a1c528012206d285a4040800a6000800a1c0a4400800a1c4d89122c4b1cc66d02a812b4000044a806d30b7c06f02200b4a816d222640b2806f022641206f0044528e4bed0018bdd06d862f4b0050266f00486000f5ec448160da448060cc44826000f5ac44806000f5b2b6a801446600ed0ab9e801486600ed022a690018bbe8014c6600ecf622690010b3e801506600ecea222f005cb2a801546600ecde24280134b4a801586700f1a2206f0058226f00482030981c206f0040d1fc0000000022100c8000007f006f00ecd26000f784203c7fffffff6000f0a893c9223c7fffffffa2010800a1c32f43002ca2030800a1c0a2000800a1c176fa2f4100344c430800262f00342f40003070184c4038032f430034262f002ce283d689d6af0030d6af00346000ef144878001f203c800000012f004e94508f4a806c00f0d06000fc9a206f0040d1fc00000000214000c842a801346000f3fc2200b2af00506f00f4e06000fdee4480b0816f00fdde60e844814a806c00fdce60ec42af00506000f4c042856000fd442f0a2f027419202f000c220004c1224145f900000000e3a82200e4a9743fed88c28202807fff800020721c0022321c049288a0010800a1c0721f7418928992af00102440e5a9241f2001d088d08a245f4e752f0a2f027418202f000c2200e4a145f900000000028000ffffff2041720fd1ef001043e8ffe2240042424842e3a822322c0024322c0402807fff80009481a0020800a1c07401b4896d26d2804a896c1470e1b0896e22741e94882001e4a8241f245f4e7524092001e5a8241f245f4e75241f70ff245f4e75241f4280245f4e752f0a2f02206f000c200802803fffffff22080801001e670e4a806748243c400000009480200222007409e5a945f90000000022417216e2a822320c0024720c04200995c102807ffffe00a00a0800a1c0d0814a886d06241f245f4e75241f4480245f4e75203c7fffffff4a886ce860ec4fefffc448d70cfc246f0040222a00d4262a00d04a816d0001d220010c8100007f006e0002f80c8100003f006e00026c206a00cc41e8a00041f08c0022084a886d00023aea81d0810c8000003f006e0001b24a806d00023e7540783f7c0320030680ffbb0000ed88e18a4c4428024c460800068008c807312f40002c0c8200010000670001b22a02700fe1ad42847401484242af0038203cfc74a769a0050800a1c0487800087e0106800e0942ad90af003047f9000000002f004e93508f068000000080e088be80640002662f4000340c80000001e06e0007122f6f0034002842a72c3c0000000020462f2f002c2f4600384e9048780018d0af00380680f07302422f004e934fef00100c8000ffffff6200025e22007c0deda97e12eea043f900000000204122310c0022710c04200893c102807fffe000a0090800a1c02c2f0028d280203c400000004c4600002f002f4100244eb900000000222f0024a2000800a1c0e280588f0c82000100006700024c720fe3aaa4000800a1c1203c7fffffffa0010800a1c22c2f0028223c80000000254200ec256f003400e84c46100142aa00e42401e28a254100f4254200f0aa050800a1c2223c03a910f1a4010800a1c1a0010800a1c12541010442aa00f8254000fc42aa01004aaf0038660002824cd70cfc4fef003c4e75206a00cc428041e8a00041f08c0022084a886c00fe46607a203c00003f00783f754020030680ffbb0000ed887c03e18a4c4428024c460800068008c807312f40002c0c82000100006600fe52428442af00382a3c7fffffff203cfc74a769a0050800a1c0487800087e0106800e0942ad90af003047f9000000002f004e93508f068000000080e088be80640000ba6000fe5206810000001fea81d0810c8000003f006f00fdc46000ff7042806000fdc00c8100005f006e00050822030681ffbb0000ed897e030680ffffc000e1884c471801068108c807312f41002c72e2b2806f000162720148414284243c00004ccc2a3c7fffffff203cfc74a7692f410038a0050800a1c0487800087e0106800e0942ad90af003047f9000000002f004e93508f068000000080e088be8064186000fdb2203c00007f000c8100003f006e00ff706000fd0272027e022f4100342c3c000000002f47002842a72f2f002c2f46003820464e9048780018d0af00380680f07302422f004e934fef00100c8000ffffff6300fda6227c01edcb1a223c2e1234e6203c7fffffffa0090800a1c02c2f0028d280203c400000004c4600002f002f4100244eb900000000222f0024a2000800a1c0e280588f0c82000100006600fdb8243c7fffffffa4000800a1c1203c7fffffffa0010800a1c22c2f0028223c80000000254200ec256f003400e84c46100142aa00e42401e28a254100f4254200f0aa050800a1c2223c03a910f1a4010800a1c1a0010800a1c12541010442aa00f8254000fc42aa01004aaf00386700fdb660322800741f4c424804207c000100007e0a91c441f08a0024084c4728024a82660003e841f90000000047f9000000002f4800300c8400010000670003a22204700fe1a9428278014844203c05a4d3c2a0010800a1c042a70680072b80342f004e93508f22407010b0896f04327c001041f19a007c0a7e7f2003484048c022084c4618012a015385be806c000178707f7c0fedab41f9000000002e300c0020300c04908702837fff8000a6000800a1c320090680ffffffe89081e1887c60d6874c056800487800082046d1c0486808ad206f00382f4100282f49002c4e904878001fe28044802f004e934fef0010222f0020226f00244a806d00020a207c401cced4a0080800a1c020400c8400010000670002107c0fedac203c4ccccccca0080800a1c0a8000800a1c0a6000800a1c0207c7fffffffe788a0400800a1c3203c800000004c450000254301142549010c2541011042aa010842aa01182540012042aa011c4a826700fc4c4aaa0134677a202a0124222a012806810000077fb0816e680c800000077f6f06203c0000077f206f00442540012420280024254001384a80670000d8203c3fffffff254001280c820001000067000120700fe1aa203c26bb447ba4000800a1c0223c7fffffffa2000800a1c0720125400130254101344cd70cfc4fef003c4e75206f004442aa012442aa012c20280024254001384a8066a460784a806c00fe887c0f4280edab41f9000000002e300c0020300c04908702837fff8000a6000800a1c320090680ffffffe89081e1887c60d6874c056800487800082046d1c0486808ad206f00382f4100282f49002c4e904878001fe28044802f004e934fef0010222f0020226f00244a806c00fe866000008a202800180c8000007f006f00014a203c00007f0048404240223c08b64043a2000800a1c042a70680085269e22f004eb900000000508f0680fffff8800c803fffffff6e00fee64a806c00fee64280254001280c82000100006600fee4243c7fffffff203c26bb447ba4000800a1c0223c7fffffffa2000800a1c0720125400130254101346000fede203c7fffffff207c401cced4a0080800a1c020400c84000100006600fdf4283c7fffffff203c4ccccccca0080800a1c0a8000800a1c0a6000800a1c0207c7fffffffe788a0400800a1c3203c800000004c450000254301142549010c2541011042aa010842aa01182540012042aa011c4a826600fdf26000fa380680ffffa000e18872e2b2806e5e2400781f4c4428020c82000100006700fdce7801484441f900000000223c7fffffff47f9000000002f48003098826000fc8e223c000001e02f4100342f6f003400286000f8e44a806c00feba42806000feb44282223c7fffffff6000fc6241f900000000428278014844223c7fffffff47f9000000002f4800306000fc427c0148462a3c7fffffff203cfc74a7692f460038a0050800a1c0487800087e0106800e0942ad90af003047f9000000002f004e93508f068000000080e088be806400fab86000f8504fefffd448d77cfc206f0030226f0034a3c0a5c0a7c04cd0000f246800104ce800f000182668002849e90080a4000800a6800800a6010900a4810800ac040810ae840810ae050910ac850810a1c0a3c1a5c4a7c5a4410800a6c50800a1cda3cedbcedbd122cdb3cc66c248d0000348e8003000184cd77cfc4fef002c4e754fefffc448d77cfc2f6f004000384ab900000000660000f04ab940fe32cc670000e6223940fe32ccb2b940fe32d0670000d643f90000000047f90000000010290003207940fe32cc4a00670000a61829000471802f4000344a046700009671917da900017ba900027984c0fc001c2c467c209c8599cc0685ffffffdf24700810260ed68c774342802f4600302f4e002cd683222f00309280ea8124057e1fd480c487d28322321c000501673073a900067c1f74207fa900052041d1c022080681ffffffdfc2869488ea82de8c7f472c42740141f67a00e3aa85b38c005280b88066b02c2f0030528c2c6f002cb9ef0034668e5e89b3fc000000006600ff42700123c0000000004cd77cfc2f6f003800404fef003c4ef940076be4100000001000ef581003bdcb10086c98100efdd6101774741021d43d102e21d9103c62d4104c9da5105ed9ae10731f49108977cf10a1ed9f10bc8c2810d95ffb10f876cd1119df8f113daa781163e918118cae6a11b80eea11e620ab1216fb6d124ab8bf1281741612bb4af012f85cfa1338cc33137cbd1d13c456e5140fc39c145f306e14b2cde2150ad01d15676f3115c8e76d162f79c0169b6c19170d09dc1784a463180293881887363f1912f34b19a639fd1a4183101ae5519c1b92342f1c48c6001d09b04e1dd5abef1ead83131f92134620844fb4218543d12296165123b80c9f24ec8ee126352c902793a1e02909de072a9a0a9b2c4694402e1234e6300000000ddd8a650ddd8be20ddd8d8e0ddd8f6e0ddd91890ddd93e60ddd968d0ddd99870ddd9cdf0ddda09f0ddda4d50ddda98e0dddaedc0dddb4d00dddbb7f0dddc2ff0dddcb6a0dddd4dd0ddddf790dddeb600dddf8bd0dde07bc0dde18910dde2b750dde40aa0dde58760dde732c0dde91260ddeb2ca0dded88c0ddf02ec0ddf327a0ddf67d80ddfa3bb0ddfe6ee0de032570de086f40de0e5e40de150680de1c7e90de24dfa0de2e45d0de38d0e0de44a410de51e710de60c610de7172a0de842420de991840deb09400decae460dee85f30df0963f0df2e5cf0df57c070df8611b0dfb9e240dff3d340e0349700e07cf230e0cdbd70e127e710e18c7450e1fc82d0e2794a60e3041dc0e39e6c20e449c1d0e507c8f0e5da4960e6c32900e7c46a60e8e02bf0ea18a5f0eb702800ece91610ee85e4d0f0491560f2353140f44cc510f6925c20f9087b60fbb19d10fe902c8101a6826104f6e1e1088376210c4e50b11059680114a696c119379b311e0e1621232b89c1289157212e40baa1343ac5c13a8056314112085147f024114f1a8201569064e15e5044e1665784416ea2071177299ea17fe5377188c7ab1191be0ba19aad21f1a36db151abc6cc61b3651101b9cce171be449801bfb2d601bc7060c1b2283b919e651e418216ae116a1c837167c9c6116c73d35168c1d2a170aa0331837d4d01864e9c017e836c818ae7c531a3caf65000000000005b9e6000b5d6a0010eb39001663f7001bc842002118b1002655d4002b80340030985800359ebc003a93dd003f782d00444c1f0049101f004dc493005269e100570069005b88870060029600646eea0068cdd8006d1fb0007164bf00759d500079c9ab007dea160081fed400860828008a0650008df9890091e20f0095c01a009993e3009d5da000a11d8400a4d3c200a8808c00ac241100afbe8000b3500400b6d8cb00ba58ff00bdd0c800c1404f00c4a7ba00c8073100cb5ed700ceaed000d1f74000d5384800d8720900dba4a400ded03900e1f4e500e512c700e829fb00eb3a9f00ee44cd00f148a100f4463600f73da400fa2f0400fd1a710100000040000000402c6be94058f6a84085a05140b268fa40df50b8410c57a241397dcc4166c34c4194283941c1aca741ef50ae421d1462424af7da4278fb2b42a71e6c42d561b44303c518433248ae4360ec8d438fb0cb43be957f43ed9ac0441cc0a3444c0740447b6ead44aaf70244daa054450a6abb453a564d456a6323459a915245cae0f245fb521a462be4e2465c9961468d6fae46be67e046ef82104720be5547521cc647839d7b47b5408c47e706114818ee22484af8d6487d264648af768a48e1e9ba49147fee4947393f497a15c449ad159849e038d04a137f884a46e9d64a7a77d44aae299b4ae1ff434b15f8e64b4a169c4b7e587e4bb2bea54be7492b4c1bf8294c50cbb84c85c3f14cbae0ef4cf022ca4d25899c4d5b157e4d90c68b4dc69cdd4dfc988c4e32b9b44e69006e4e9f6cd44ed5ff004f0cb70c4f4395144f7a99304fb1c37c4fe9141350208b0e50582888508fec9c50c7d76550ffe8fe513821825170810b51a907b451e1b59a521a8ad752538786528cabc352c5f7aa52ff6b55533906e05372ca6853acb60753e6c9da542105fd545b6a8b5495f7a154d0ad5a550b8bd4554693295581c37855bd1cdb55f89f7056344b52567020a056ac1f7556e847ef57249a2957611642579dbc5757da8c83581786e65854ab9b5891fac158cf7474590d18d3594ae7fb5988e20959c7071c5a0557515a43d2c65a82799a5ac14bea5b0049d45b3f73775b7ec8f25bbe4a615bfdf7e55c3dd19c5c7dd7a45cbe0a1c5cfe69235d3ef4d75d7fad595dc092c75e01a53f5e42e4e35e8451d05ec5ec265f07b4055f49a98c5f8bccdb5fce1e1260109d5160534ab76096266560d9307b611c6919615fd05e61a3666d61e72b65622b1f66626f429262b3950962f816eb633cc85b6381a97863c6ba64640bfb4164516c2e64970d4f64dcdec36522e0ad6569132f65af766a65f60a7f663ccf926683c5c366caed356712460b6759d06567a18c6867e97a34683199ed6879ebb668c26fb1690b260169540ec9699d2a2c69e6784d6a2ff94f6a79ad566ac394856b0daeff6b57fce96ba27e656bed33996c381ca66c8339b26cce8ae16d1a10576d65ca386db1b8a86dfddbcc6e4a33c96e96c0c36ee382de6f307a416f7da7106fcb096f7018a18570666f7670b473687102ad8071511de4719fc4b971eea226723db650728d015d72dc8374732c3cba737c2d5573cc556d741cb528746d4cac74be1c20750f23ab7560637475b1dba276038c5b765575c876a7980f76f9f359774c87cc779f559077f25cce78459dac7899185478ecccec7940bb9e7994e49279e947ef7a3de5df7a92be8b7ae7d21a7b3d20b67b92aa887be86fba7c3e70737c94acde7ceb25237d41d96e7d98c9e67deff6b67e4760097e9f06067ef6e8da7f4f08ae7fa765ad800000000000000000c90f8801921d20025b26d703242abf03ed26e604b6195d057f00350647d97c0710a34507d95b9e08a2009a096a90490a3308bd0afb68050bc3ac350c8bd35e0d53db920e1bc2e40ee387660fab272b1072a0481139f0cf120116d512c8106f138edbb1145576b1151bdf8615e2144516a81305176dd9de183366e918f8b83c19bdcbf31a82a0261b4732ef1c0b826a1ccf8cb31d934fe51e56ca1e1f19f97b1fdcdc1b209f701c2161b3a02223a4c522e541af23a6887f2467775825280c5e25e845b626a8218627679df42826b92828e5714b29a3c4852a61b1012b1f34eb2bdc4e6f2c98fbba2d553afc2e110a622ecc681e2f8752623041c76130fbc54d31b54a5e326e54c73326e2c333def28734968250354d905736041ad936ba2014376f9e46382493b038d8fe93398cdd323a402dd23af2eeb73ba51e293c56ba703d07c1d63db832a63e680b2c3f1749b83fc5ec984073f21d4121589b41ce1e65427a41d04325c13543d09aed447acd50452456bd45cd358f46756828471cece747c3c22f4869e665490f57ee49b415334a581c9e4afb6c984b9e03904c3fdff44ce100344d8162c44e2106174ebfe8a54f5e08e34ffb654d5097fc5e5133cc9451ced46e5269126e53028518539b2af05433027d54ca0a4b556040e255f5a4d2568a34a9571deefa57b0d2565842dd5458d40e8c5964649859f3de125a82799a5b1035cf5b9d11545c290acc5cb420e05d3e52375dc79d7c5e50015d5ed77c8a5f5e0db35fe3b38d60686ccf60ec3830616f146c61f1003f6271fa6962f201ac637114cc63ef3290646c59bf64e889266563bf9265ddfbd366573cbb66cf81206746c7d867bd0fbd683257ab68a69e816919e320698c246c69fd614a6a6d98a46adcc9646b4af2796bb812d16c2429606c8f351c6cf934fc6d6227fa6dca0d146e30e34a6e96a99d6efb5f126f5f02b26fc193857023109a708378ff70e2cbc671410805719e2cd271fa394972552c8572af05a77307c3d0735f662673b5ebd1740b53fb745f9dd174b2c8847504d3457555bd4c75a585cf75f42c0b7641af3d768e0ea676d9498977235f2d776c4edb77b417df77fab989784033297884841478c7aba27909a92d794a7c12798a23b179c89f6e7a05eead7a4210d87a7d055b7ab6cba47aef63237b26cb4f7b5d039e7b920b897bc5e2907bf888307c29fbee7c5a3d507c894bde7cb727247ce3ceb27d0f42187d3980ec7d628ac67d8a5f407db0fdf87dd6668f7dfa98a87e1d93ea7e3f57ff7e5fe4937e7f39577e9d55fc7eba3a397ed5e5c67ef058607f0991c47f2191b47f3857f67f4de4517f62368f7f754e807f872bf37f97cebd7fa736b47fb563b37fc255967fce0c3e7fd8878e7fe1c76b7fe9cbc07ff094787ff621827ffa72d17ffd885a7fff62167fffffff00000000fed91653ff7c44ef0000000000ad961f00d9165300000000fff183beffe39374ffd624f2ffc92f1effbca9c7ffb08d8dffa4d3c2ff997659ff8e6fcbff83bb11ff79538eff6f3506ff655b95ff5bc3a4ff5269e100000000ffad961fff6a3fe6ff315130ff000000fed47fccfead961ffe8a62b0fe6a3fe6fe4caffcfe315130fe17d605fe000000fde99c09fdd47fccfdc087d300000000fe435639fd435639fcad961ffc4caffcfc000000fbc087d3fb8a62b0fb5b2c3efb315130fb0bb9cafae99c09faca6144faad961ffa92e050fa79f7d800000000ffd624f2ffb08d8dff8e6fcbff6f3506ff5269e1ff37b413ff1ecb9aff077623fef183befedccc92fec92f1efeb68ef5fea4d3c2fe93e88afe83bb1100000000ffea46c7ffcb1243ffa66666ff88d558ff817066ff7183a6ff478b37ff253823ff0848befeefc598fedab167fec7905afeb5f837fea59cf3fe96464000000000ffa2c156ff5faed0ff2e6981ff07f7b8fee881c9fecd6d84feb556fffe9f69a4fe8b1c52fe781175fe660667fe54ca07fe443722fe3430e8fe24a09b00000000ff4ccccdfee3f987fe99999afe5fe916fe30c654fe08ec08fde66666fdc7f30efdacb5e2fd9411e2fd7d9321fd68e196fd55b8d5fd43e29dfd33333300000000ffd624f2ffb08d8dff8e6fcbff6f3506ff5269e1ff37b413ff1ecb9aff077623fef183befedccc92fec92f1efeb68ef5fea4d3c2fe93e88afe83bb1100000000ffd91653fed91653fcf0ec58fc900635fc435639fc03de0cfbcdb8eafb9e8277fb74a769fb4f1003fb2cf242fb0db77dfaf0ec58fad63689fabd4e1100000000ff912993ff3c05eafef6e15afebca9c7fe8a62b0fe5e23acfe36a19ffe12f1b4fdf2674cfdd47fccfdb8d5fefd9f19ddfd870b0bfd7074fcfd5b2c3e00000000ffe39374ffc92f1e00000000ff997659ff83bb11ff6f3506ff5bc3a4ff494b3bff37b413ff26e9adff16da39ff077623fef8afb1feea7ac4fedccc9200000000ff26e9adfe9f19ddfe3c05eafdedfaf7fdad961ffd76c53dfd470c77fd1ccb25fcf6e15afcd47fccfcb50c41fc9810e2fc7d319afc642514fc4caffc0000000001002a84019631640200d4310253bcef0297adbf02d15281030374e2032fe10e0357d112037c24c6039d814a03bc63dc03d92db403f42bbb040d9bd00000000000ac0bc5011838280132e1b401685c75018b6cf801a8690601ceb2cc01d8ee8501ddec6a020566d1020bf7bb0214afcc0233b3be02346ca70245c8360000000001fe2612034cd4e904067719049ab154051616be057fcaac05dc3ea3062e67100678548906bb870506f91e3a0731f7520766bffe0798032007c631880000000001767dd9026f1aff0328bd3003bcf76b04385cd404a210c204fe84ba0550ad26059a9aa005ddcd1c061b645006543d690689061506ba493706e8779f00000000003e11350097398b01000000015479e001699a4b01971a25020f04870271167702c3c2740309cb7203460523037cacb603aef1ac03ddad490409806f000000000136d0e2021663f702baa053033ac64603a3a4b803fde849044e335804974a8804daf6f0051a7079055695530590093d05c7483805fcb24f06309350000000000000000000000000401173c8000000190000001600000001000000000000000000000000fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc00fffffc000000000000000000000f80000033e00000555000008ef0000095d8000103f8000001d4003ffcec00776e58007fee2800d54f4800eedf1000d55f2000aa9f4000d55f0000801f0000911f0000800f0000400e0000400e00003ffc00000000000000000000401173c8000000220000002200000002000000000000000000000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000ffffffffc0000000000000000000000000003fc0000000000000d5700000000000010bb800000000000255540000000000040eee00000000000955550000000000080bfb00000000001455f58000000000100bfe80000000001055f580000000000003ba800000001ffffd55800000003fffdeae8000000077771f55800000007fffbf20800000005dddbf55000000007fffbf0100000000d5553f9200000000bbbb7f8400000000d5557f8800000000aaaa7fb000000000d5557f800000000080007f8000000000d5557f800000000080007f800000000091113f800000000040003f000000000040003f000000000040003f000000000040001f000000000020001e00000000001ffffc00000000000000000000000000401173c8000000300000002100000002000000000000000000000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000ffffffff80000000030000300500000300071805000702180703051807011c0703051c0703001503052007022407030524070228070305280703000e3005000e0200153005001502001c3005001c",
    "relocs": [
     [
      6344,
      "code",
      10006
     ],
     [
      6424,
      "code",
      10266
     ],
     [
      6582,
      "code",
      11294
     ],
     [
      6828,
      "code",
      6408
     ],
     [
      6876,
      "code",
      6326
     ],
     [
      6936,
      "code",
      9230
     ],
     [
      6990,
      "code",
      6536
     ],
     [
      7256,
      "code",
      6408
     ],
     [
      7418,
      "code",
      6408
     ],
     [
      7474,
      "code",
      6326
     ],
     [
      7576,
      "code",
      6536
     ],
     [
      7754,
      "code",
      6326
     ],
     [
      7760,
      "code",
      6408
     ],
     [
      7866,
      "code",
      9490
     ],
     [
      8246,
      "code",
      9490
     ],
     [
      8400,
      "code",
      6408
     ],
     [
      8648,
      "code",
      6326
     ],
     [
      8660,
      "code",
      6408
     ],
     [
      8720,
      "code",
      6326
     ],
     [
      8738,
      "code",
      6408
     ],
     [
      8794,
      "code",
      6408
     ],
     [
      60,
      "bss",
      336
     ],
     [
      92,
      "bss",
      536
     ],
     [
      98,
      "bss",
      0
     ],
     [
      312,
      "bss",
      72
     ],
     [
      376,
      "bss",
      0
     ],
     [
      404,
      "bss",
      0
     ],
     [
      468,
      "bss",
      48
     ],
     [
      484,
      "bss",
      24
     ],
     [
      538,
      "bss",
      48
     ],
     [
      552,
      "bss",
      0
     ],
     [
      616,
      "bss",
      48
     ],
     [
      630,
      "bss",
      24
     ],
     [
      738,
      "bss",
      532
     ],
     [
      754,
      "bss",
      72
     ],
     [
      786,
      "bss",
      336
     ],
     [
      796,
      "bss",
      72
     ],
     [
      872,
      "bss",
      544
     ],
     [
      922,
      "bss",
      336
     ],
     [
      952,
      "bss",
      528
     ],
     [
      1010,
      "bss",
      556
     ],
     [
      1024,
      "code",
      6648
     ],
     [
      1038,
      "bss",
      532
     ],
     [
      1050,
      "bss",
      336
     ],
     [
      1074,
      "bss",
      336
     ],
     [
      1092,
      "bss",
      532
     ],
     [
      1146,
      "bss",
      336
     ],
     [
      1210,
      "bss",
      540
     ],
     [
      1256,
      "bss",
      560
     ],
     [
      1396,
      "code",
      6408
     ],
     [
      1482,
      "code",
      12322
     ],
     [
      1536,
      "bss",
      344
     ],
     [
      1552,
      "code",
      13114
     ],
     [
      1584,
      "bss",
      336
     ],
     [
      1620,
      "code",
      12730
     ],
     [
      1626,
      "code",
      12346
     ],
     [
      1936,
      "code",
      6536
     ],
     [
      1956,
      "code",
      6536
     ],
     [
      2020,
      "code",
      6536
     ],
     [
      2122,
      "bss",
      528
     ],
     [
      2174,
      "bss",
      528
     ],
     [
      2196,
      "code",
      6326
     ],
     [
      2236,
      "bss",
      352
     ],
     [
      2320,
      "code",
      6326
     ],
     [
      2368,
      "bss",
      336
     ],
     [
      2430,
      "bss",
      336
     ],
     [
      2466,
      "bss",
      336
     ],
     [
      2504,
      "bss",
      2704
     ],
     [
      2512,
      "bss",
      2832
     ],
     [
      2530,
      "bss",
      584
     ],
     [
      2548,
      "bss",
      2448
     ],
     [
      2556,
      "bss",
      2576
     ],
     [
      2576,
      "bss",
      2576
     ],
     [
      2584,
      "bss",
      2704
     ],
     [
      2596,
      "bss",
      336
     ],
     [
      2610,
      "bss",
      2704
     ],
     [
      2620,
      "code",
      6536
     ],
     [
      2664,
      "bss",
      2832
     ],
     [
      2676,
      "bss",
      336
     ],
     [
      2682,
      "bss",
      2448
     ],
     [
      2782,
      "bss",
      2576
     ],
     [
      2794,
      "bss",
      336
     ],
     [
      2826,
      "bss",
      2704
     ],
     [
      2846,
      "bss",
      2448
     ],
     [
      2962,
      "bss",
      2832
     ],
     [
      2984,
      "bss",
      336
     ],
     [
      3048,
      "bss",
      2576
     ],
     [
      3190,
      "bss",
      2704
     ],
     [
      3228,
      "bss",
      528
     ],
     [
      3280,
      "bss",
      2576
     ],
     [
      3290,
      "bss",
      2704
     ],
     [
      3368,
      "bss",
      2832
     ],
     [
      3444,
      "bss",
      336
     ],
     [
      3538,
      "bss",
      528
     ],
     [
      3562,
      "bss",
      532
     ],
     [
      3716,
      "bss",
      648
     ],
     [
      3728,
      "bss",
      532
     ],
     [
      3834,
      "code",
      6326
     ],
     [
      3998,
      "bss",
      560
     ],
     [
      4154,
      "bss",
      560
     ],
     [
      4246,
      "code",
      6536
     ],
     [
      4306,
      "bss",
      2832
     ],
     [
      4458,
      "bss",
      2704
     ],
     [
      4480,
      "bss",
      2576
     ],
     [
      4496,
      "bss",
      528
     ],
     [
      4580,
      "bss",
      2704
     ],
     [
      4624,
      "bss",
      2832
     ],
     [
      4718,
      "code",
      12322
     ],
     [
      4772,
      "bss",
      344
     ],
     [
      4788,
      "code",
      13114
     ],
     [
      4824,
      "bss",
      336
     ],
     [
      4860,
      "code",
      12730
     ],
     [
      4866,
      "code",
      12346
     ],
     [
      4922,
      "code",
      6408
     ],
     [
      4952,
      "bss",
      72
     ],
     [
      4972,
      "bss",
      336
     ],
     [
      4990,
      "bss",
      72
     ],
     [
      5184,
      "bss",
      336
     ],
     [
      5236,
      "bss",
      544
     ],
     [
      5294,
      "bss",
      336
     ],
     [
      5344,
      "bss",
      544
     ],
     [
      5396,
      "bss",
      336
     ],
     [
      5474,
      "bss",
      532
     ],
     [
      5530,
      "code",
      8822
     ],
     [
      5638,
      "bss",
      336
     ],
     [
      5648,
      "bss",
      336
     ],
     [
      5722,
      "bss",
      336
     ],
     [
      5832,
      "code",
      6648
     ],
     [
      5844,
      "bss",
      336
     ],
     [
      5882,
      "bss",
      2704
     ],
     [
      5888,
      "bss",
      2576
     ],
     [
      6122,
      "bss",
      540
     ],
     [
      6262,
      "bss",
      336
     ],
     [
      13498,
      "code",
      14310
     ],
     [
      13502,
      "code",
      13738
     ],
     [
      13506,
      "code",
      13510
     ],
     [
      13526,
      "code",
      13638
     ],
     [
      13530,
      "code",
      13538
     ],
     [
      13754,
      "code",
      14038
     ],
     [
      13758,
      "code",
      13766
     ],
     [
      14326,
      "bss",
      2836
     ],
     [
      14330,
      "code",
      14338
     ],
     [
      8964,
      "bss",
      2832
     ],
     [
      9000,
      "code",
      14722
     ],
     [
      9006,
      "bss",
      2836
     ],
     [
      9194,
      "code",
      14792
     ],
     [
      9206,
      "bss",
      2832
     ]
    ],
    "symbols": {
     "solid_update": [
      "code",
      0
     ],
     "solid_render": [
      "code",
      690
     ],
     "solid_pictures": [
      "code",
      13498
     ],
     "solid_hook_tick": [
      "code",
      8948
     ]
    },
    "bss": 3220
   }
  },
  "chips": {
   "id": "chips",
   "name": "CHIPS: a chip square with an arpeggio inside the note, a pitch sweep and a stepped triangle bass, after Plaits",
   "order": 84,
   "version": "0.1",
   "symbols": {
    "update": "chips_update",
    "render": "chips_render"
   },
   "keep": [
    "chips_ui_format",
    "chips_ui_draw"
   ],
   "patch_points": [
    {
     "symbol": "chips_descriptor_base",
     "kind": "descriptor_base"
    }
   ],
   "uses": [
    {
     "point": "machine",
     "name": "CHIPS",
     "image": 4,
     "decay_default": 64,
     "knobs": [
      {
       "long": "Chips Wave",
       "short": "WAVE",
       "default": 64
      },
      {
       "long": "Chips Chord",
       "short": "CHRD",
       "default": 0
      },
      {
       "long": "Chips Sweep",
       "short": "SWEP",
       "default": 64
      },
      {
       "long": "Chips Arp",
       "short": "ARP",
       "default": 41
      }
     ]
    },
    {
     "point": "knob.text",
     "vtable": {
      "at": "0x400fd170",
      "stock_ptr": "0x4000a70e",
      "symbol": "chips_ui_format",
      "shared": [
       "0x400fd108",
       "0x400fd1d8",
       "0x400fd240"
      ]
     },
     "chain": "chips_next_fmt"
    },
    {
     "point": "knob.draw",
     "vtable": {
      "at": "0x400fd174",
      "stock_ptr": "0x4000a66a",
      "symbol": "chips_ui_draw",
      "shared": [
       "0x400fd10c",
       "0x400fd1dc",
       "0x400fd244"
      ]
     },
     "chain": "chips_next_draw"
    },
    {
     "point": "shortcut",
     "key": "MACHINES",
     "press": "PUNCH"
    },
    {
     "point": "shortcut",
     "key": "MACHINES",
     "press": "GATE"
    }
   ],
   "conflicts_declared": [],
   "claims": {
    "sound_slots": [
     [
      32,
      "machine"
     ]
    ],
    "record_slots": [
     [
      18,
      "machine"
     ]
    ],
    "gestures": [
     {
      "combo": "MACHINES + PUNCH",
      "atoms": [
       [
        "MACHINES",
        "PUNCH"
       ]
      ],
      "situation": "any",
      "scope": "machine",
      "meaning": "Bass",
      "replaces": null
     },
     {
      "combo": "MACHINES + GATE",
      "atoms": [
       [
        "MACHINES",
        "GATE"
       ]
      ],
      "situation": "any",
      "scope": "machine",
      "meaning": "Up-down",
      "replaces": null
     }
    ]
   },
   "bundle": {
    "code": "4fefffec48d70c1c226f001c243c0000031c22090681bdcf77d84c421001246f0020263c43485031b6a9002c674c747c4c0128002042d1fc00000000200806800000007c4218b08866fa2042203c80000000d1fc00000000283cfc00000074ff21440008263c4348503121400078214000702142005c2343002c712a00244a806d00020071c0207c4011d84c362a001e41f00c00235002504aa900386762283c012c0f26203c001f7c5c243c7fffffff2344027823440274283c82581e4b2340028423400280203c803ef8b823420294234202902344027c234002884a43670001fc243c200000007001283c600000002342029c234402a0234202a42340004870284c01080041f900000000756a0014796a0022e18a0684ffffc000e78c47f00804d4af0018d4840682ffc00000218208040c82007f00006f0000e8747f4842796a001626824aa9003856c221840808796a00182184080c796a001a750221840810796a001c448221820800218408142801e58c2244d3fc800017ec22514a89670000ec342900542801e78c75c22244d3fc423087fc082900000003672c78424c0418002241d3fc800015ee32110801000a670e28010882000802840000010084840801000b660000c04a4356c12602e08b7809e8aa7801c8837601c68273014481218408182183081c21810824243940149310b4b900000000670000cc2202780feb8923c2000000004c4418014cd70c1c2181082023c1000000004fef00144e754a826c00ff1a796a0016428226824aa9003856c221840808796a00182184080c796a001a750221840810796a001c448221820800218408142801e58c2244d3fc800017ec22514a896600ff1874424c012800247c800015ee343228006000ff0842806000fdfe02810000020008820009780984814a4356c12602e08be8aa78017301c8837601c682448121810824218408182183081c243940149310b4b9000000006600ff384cd70c1c223900000000218108204fef00144e75283c20000000243c7fffffff2342029c234402a0234402a442a900486000fe064fefffa8206f006048d77cfc4aa80034664a4aa800386644202802304a806d000cd40c8000003fff6232226f0060202902344a806d000cf60c8000003fff621c206f005c20080680000000804298b1c066fa4cd77cfc4fef00584e75202f0060243c0000031c0680bdcf77d84c420000a983787c4c0048002f4300502444d5fc000000002f440034a93c000000a0a13c000000007a284c00580041f9000000002430580c2f45003c0c8200007f006e0005184a826d000544c5fc000b720f41f900000000266f003c43f9000000002031b800e2a277b028002a034ab1b81c670004be7802b8836c0004b65385da854a806600058641f9000000002f480038206f0038226f003cd3fc0000000028290014d1ef00342c28004cb8a8005c660a20680060b1e90020676c0c8400003fff6f000e62200472110680ffffc000e3a8223c41041041a2000800a1c00c803fffffff6e000b66d080223c02000000a2000800a1c00680197302422f004eb900000000226f0040588f41f90000000022309820206f0038d1ef0034214000502144005c21410060206f00382206d1ef0034d2a80050202800542141004cb28665000838b0856c00083ab0836d049a802005206f0038d1ef003422280068214000584a81672622680064a2090800a1c3227c7d2fda7ea2410800a1c10c81000800006d000848214100682203068000000000204071302c00206f0038226f003cd3fc0000000048404240d1ef00342141006cd0a90004d0812f400040b0a80070660c20680074b1e90008670000a0202f00400680ffbb0000ed88740349f9000000004c4208002640d7fc193b09732f0b262f00380683000000002f034e94226f0044508f41f9000000002430980820020c8200007f006f00070a203c00007f0026007217e3abe08041f90000000022300c0020300c04908102837f800000a6000800a1c0d28048731800262f00380683000000002f034e94508f206f0038d1ef0034216f0040007021420074206f0038222f0034d1ef0034226f003826680034200bd080227118002a28000c222800042c280028206800082f49004428404a85670006ea2c6f005c263c04000000202f00442a4c226f005c4dee0080d086b08664000476282a002c2400e9aa282a0030a8020800a1c20c82400000006f06243c40000000e289781f2e3c400000009e8228412205e9a9280c8284ae0b0800a1c4d8842841d9c4b9c4650002b44a85660005a24a8c6d0002aea40b0800a1c128082043e589263cfc00000022c4bdc9668ceb8e226f0038266f0038d3ef003423410004222f0034dcaf0044234800082345000c206f003cd1fc00000000278618004aa80018670006424aa800246600087a74162f42004c206f0038226f0034242f00400682fff4000047f09878b493672c202f00400680ffaf0000ed887603d3fc000000004c4308000680193b09732f002f094eb9000000002682508f206f0038d1ef00344aa800206600060c20280014721743f9000000007a01282f004c928420310c00e2a021440024214500202140001c21400018226f0038d3ef00342229004028690010206900180c8104000000620006282429001c76172a290014200ceb89226f005c47f900000000b6af004c6700029026057c0f5283cc83d081b280630004907a1fca832e002808ea8f24335c00e2824a866700048e282a0044e9af282a0048a8070800a1c40c84400000006f06283c40000000a8040800a1c62e3c40000000e0869e84ae070800a1c7e087080300046600047428065889d888204291c7d9a9fffcbdc9668aeb89226f0038d3ef003423480018234500142342001c206f0038d9c1226f0034218c9810206f005c2018223c7fffffff0c8007ffffff6e0e0c80f80000006d0002b42200e9892141fffcbdc866da2f2f00604eb9400a92522f2f00642f2f00644eb9400a94302f2f006c2f2f006c4eb9400a967a202f0064a9004fef00144cd77cfc4fef00584e754a80660000d641f9000000002f4800387001b0836d00fb4a266f00384280222f003442b318546000fbf0243c00007f00720fc5fc000b41f900000000266f003c43f9000000002031b800e2a277b028002a034ab1b81c67a86000faea4282c5fc000b720f41f900000000266f003c43f9000000002031b800e2a277b028002a034ab1b81c6700ff7a6000faba4a8c6c0001f4387c0001a4020800a1c4e6842f440030280898af0030ae070800a1c7e6872047d1c34a8c660001c8a40b0800a1c1e5894a8566000212263cfc00000022c4bdc96600fcb66000fd2641f900000000266f003c2f480038d1ef003443f9000000002031b81042a8005442a8004c0c8000007f006e0005ba4a806d0006700680ffffc00022004a806d0006520c8100003f006e0005d47811e9a9207c41041041a0410800a1c10c813fffffff6e00059ad281a2010800a1c1207c00300000a0410800a1c14a806d00060e206f0038226f0034218198644a816706223c7fffffff266f0038282f0034278148686000fe92280858892042d9a9fffcbdc96700fdea26057c0f5283d081cc83b28063e27a1fca832e002808ea8f24335c004a8667000216282a0044e9af282a0048a8070800a1c40c84400000006f06283c40000000a8040800a1c62e3c40000000ee869e84ae070800a1c7ee87080300046600029428065889d888204291c7d9a9fffcbdc9668e6000fd74d28db28d640000e62401e28a2e2a0038282a003cefaaa8020800a1c20c82400000006f06243c40000000a4020800a1c7283c40000000e6879882a8040800a1c2e68228084a856700013e2043d1c2448374019887b58541f03a0022c4bdc96600fb246000fb94223c800000002141fffcbdc86600fd266000fd4826082044280bd8814a8567000092b8816470222a0038e3ac222a003ca2040800a1c10c81400000006f06223c40000000a2010800a1c5e6852e3c4000000028089e819885ae070800a1c1e6812041d1c3a40b0800a1c1e589d1fcf8000000263cfc000000428522c4bdc96600fa9e6000fb0e2808204322c4bdc96600fa8e6000fafea40b0800a1c1428528082043e589d1fcf8000000263cfc00000060c84a846c00fac42e2a0038068480000000222a003cefaca2040800a1c10c81400000006f06223c40000000a2010800a1c4e6842e3c400000009e81d888ae070800a1c1e681204391c1a40b0800a1c1263cfc000000e58922c4bdc96600fa106000fa804a8c6c00ff7e99cc6000fd0c204391c244837401d887b58541f03a006000fec2280858892042d9a9fffcbdc96600fb546000fbc658892042d9a9fffcbdc96600fb426000fbb458892042d9a9fffcbdc96600fdbe6000fba22808588998862042d1c7d9a9fffcbdc96600fb186000fb8a4a826c00f8fa428026007217e3abe08041f90000000022300c0020300c04908102837f800000a6000800a1c0d28048731800262f00380683000000002f034e94508f206f0038d1ef0034216f00400070214200746000f8f45280ba806e00030042a8005442806000f7c82c6f005c263cfc000000202f00442a4c226f005c4dee00806000f916206f005c42a900206000fb202808588998862042d1c7d9a9fffcbdc96600fcfc6000fae042a8006822036000f7b820280024b0af004c6700fa1622280018b0af004c6c00059ad281206f003843f900000000d1ef003420280014216f004c002421410018721792af004c20310c00e2a02140001c226f0038d3ef00342229004028690010206900180c81040000006300f9dc20290014741b2e2f004c760f280cea8ce5a8efab741e94878084e2832f4300302f4000540c8107ffffff6200050e20010680fc000000e988263c400000009680e4a32f430044e98b2f43003ce4a02400e98a2a429bc0200dd080a2000800a1c3781b202f0054e8a84aaf00546c047a1fbb807c1beda82e2f003ca0070800a1c02840264399ef0030226f005c242f005420022f4a00402600d0814a826d0002242a004a806d000330b183781be8ab670003e22e00e8af7c1b4283280824472a07edaf2c2f003cae060800a1c7284799ef0030d68c4a8a670001b44aaf0044670001ac2800028407ffffff246f00402e2a00442c2a00482f470048efacac040800a1c40c84400000006f06283c40000000247c400000007e0f95c4be8565000394a8040800a1c4d8842a2f0044a8050800a1c4d888a44a0800a1c5da852e2f0044aa070800a1c596852a00b08264064a8b660001b8aa0d0800a1c558892045d481d1c3d9a9fffcbdc96600ff2ceb89226f00387417202f005494af004cd3ef00342348001841f900000000d0812600721be2abeb8822303c00e4a1206f005c234300142341001c234000106000f8ec76172f43004c6000f786203c00007f000680ffffc00022004a806c00fa4a60000096223c7fffffffa2010800a1c1207c00300000a0410800a1c14a806c00fa66606e7811223c00003f00e9a9207c41041041a0410800a1c10c813fffffff6ec26000fa28203c7fffffff223c02000000a2000800a1c00680197302422f004eb900000000226f0040588f41f900000000223098206000f496214000546000f4c444800c8000003fff6200f35e6000f32844816000f9f044810c8100003f006f00f9b06000ff7e42800680ffffc00022004a806c00f99260de44806000f308b08265662a004a806c00febe2a0044856a00feb62a3c7fffffffaa0d0800a1c558892045d481d1c3d9a9fffcbdc96600fdda6000feacb183781be8ab670001b82a00e8ad4a806d0000d426000283f80000002c2f003ca6060800a1c396af0030280828434a856600fde64a8b6796206f00402a2800442c2800482f4500482e2f00482a00efadac050800a1c50c85400000006f062a3c400000002e3c400000009e85e2872f47002cae070800a1c6dc86ac060800a1c7de87207c0c00000091ef002cd1c624472e06e287d1c72c089c8adc86ac0b0800a1c6e285d886aa050800a1c6dc86ac060800a1c7de87207c0c00000091c5d1c62f4700482e06e287d1c72a089aaf0048da85aa0b0800a1c5d6852a004a806c00fdb26000fef2780f7e1fc885bb874283244428087c1bedaf2c2f003cae060800a1c7284799ef0030d68c4a8a6700febc6000fd067c1becad4a8b67ca246f004026000683800000002c2a0044282a0048edaba8030800a1c40c84400000006f06283c400000002e3c400000009e84e287ae070800a1c6dc86ac060800a1c3d68324432606e2832843263c0c0000009687d686d68c968ad683a60b0800a1c3e28491c3a8040800a1c6dc86ac060800a1c7de872606e2832443263c0c0000009684d686d68a9687d683a60b0800a1c3780f7e1fc885bb874483244428086000ff362808260c2a004a806c00fcc86000fe082808260caa0d0800a1c558892045d481d1c3d9a9fffcbdc96600fbea6000fcbca8040800a1c4d8842a2f0044a8050800a1c528089885a44a0800a1c5da852e2f0044aa070800a1c5d685b0826400fdb84a8b6700fdb26000fe20226f003c200441f900000000e0807e0e2230982041f90000000071b0080041f90000000022402001efa820709c00a0400800a1c0206f00385280d1ef0034214000502144005c214100606000f1b642af003c203c4000000042af00446000fb02206f0038e28143f900000000d1ef00342028001421410018721792af004c20310c00e2a0216f004c00242140001c6000fa664feffff0202f0014220048d7040ce081246f00184a806d4e2001747fb4816d000090763fb6816d4c41f90000000071b00800c0fc00062240d3fc000000001211677a91c8d1ca1081528920085288121166f47201928ad081d5c042124cd7040c4fef00104e7591c8723143f900000000d1ca60d243f900000000740a71b108c0307c0002724843f9000000004c4208034c420800d1ca0683000000300680000000302f43000c1480156f000f00016096707f763fb6816dbc6000ff6e421242804cd7040c4fef00104e752f0372182f02202f000c2600e2a3720f43f900000000028000ffffff204341e8ffe2240042424842e3a822312c0022712c0402807fff800093c1a0090800a1c07401b4886d26d2804a886c1470e1b0886e22741e94832001e4a8241f261f4e7524082001e5a8241f261f4e75241f70ff261f4e75241f4280261f4e754feffff048d70c0c242f0018246f00140c821e0000006f44243c1e0000002f02761847f9000000004e93207c3d000000220091c204c153812401e7aa24802541000491c22f084e93508f4a806d4c254000084cd70c0c4fef00104e750c82100000006cba243c1000000076182f0247f9000000004e93207c3d000000220091c204c153812401e7aa24802541000491c22f084e93508f4a806cb4203c7fffffff254000084cd70c0c4fef00104e75518f2f0a2f02222f001c242f00182f41000c206f0014246f00200c820000000067240c8200000000671c2f4a00202f41001c2f4200182f480014241f245f508f4ef9000000002f022f48000c4eb94004df40588f22402029001c206f00084a80677e2f2f000c22502f022f08206900184e904fef000c4a00661a203c401253262f4000182f4a0014241f245f508f4ef9400cb9e40c8200000000674c202f000c0c8000007f006f56203c00007f00c1fc000b720de2a802800003fffc2040d1fc000000001210673e224a1281528824095289121066f47001908ad082d5c04212241f245f508f4e752f4a00182f6f000c0014241f245f508f4ef9000000004a806cac428060a84212428060d44fefffe82f0e2f02242f003c202f00282f42000c222f0024226f002c206f00302c6f00342f6f003800080c8000000000670000900c8000000000672c2f42003c2f4e00342f6f000800382f4800302f49002c2f4000282f410024241f2c5f4fef00184ef900000000486f00182f094eb9000000002f3c40141b08486f001c4eb940072260486f0028487900000000487800022f2f00282f2f0028486f00342f0e4eb940071a044fef002c486f00104eb940072080588f241f70012c5f4fef00184e75241f42802c5f4fef00184e75485a00257300312f34000000312f34540000312f38000000312f38540000312f31360000312f31365400312f33320000fc400000fcc00000fd400000fdc00000fe400000fec00000ff400000ffc000000040000000c000000140000001c000000240000002c000000340000003c0000003c000000340000002c000000240000001c000000140000000c0000000400000ffc00000ff400000fec00000fe400000fdc00000fd400000fcc00000fc400000000000000000000000000101010101010101010202020202020202020303030303030303030404040404040404040505050505050505050606060606060606060174d3b8022f3d9402e9a76f045e7b2705d34edf08bcf64e0ba69dbe101011111112121313141414151516161717181819191a1b1b1c1c1d1e1e1f202021222323242526272728292a2b2c2d2e2f3031323335363738393b3c3d3f404f43540035000000535553006d0000006d3700006d3900006d313100363900004d3900004d3700004d0000000102030304040404040403000000000007000000050700000307000003070a0002030a0003050a000204090002040b0004070b0004070000ff07504fff0cd51cff12451cff17a0eaff1ce919ff221e37ff2740ccff2c515aff31505eff363e50ff3b1ba3ff3fe8c5ff44a621ff49541dff4df31cff52837cff57059aff5b79ccff5fe068ff6439c0ff688623ff6cc5ddff70f938ff75207bff793bebff7d4bcbff81505aff8549d8ff893881ff8d1c8fff90f63aff94c5baff988b44ff9c470bff9ff941ffa3a217ffa741bcffaad85effae6629ffb1eb48ffb567e5ffb8dc29ffbc483bffbfac42ffc30864ffc65cc5ffc9a988ffcceed0ffd02cbeffd36374ffd69311ffd9bbb4ffdcdd7bffdff885ffe30cedffe61ad1ffe9224affec2375ffef1e6bfff21345fff5021cfff7eb09ffface24fffdab820000030a000081670001b8a10003a6e70006495b00099c27000d9a8700123ee4001782ed001d5fae0023cdb1002ac51600323db3003a2f2900429106004b5ad20054842a005e04d30067d4c40071ec36007c43b00086d40c0091967f009c849b00a7985300b2cbfb00be1a4500c97e4600d4f36c00e0757f00ec009d00f7913601032406010eb615011a44ad0125cd5a01314de4013cc44b01482ec301538baf015ed9a1016a17510175439f01805d8c018b6439019656e501a134e801abfdb301b6b0cc01c14dce01cbd46701d6445301e09d5e01eadf6101f50a4401ff1df602091a720212ffbb021ccddd022684ea023024fb0239ae2f024320a8024c7c8f0255c20f40000000402c6be94058f6a84085a05140b268fa40df50b8410c57a241397dcc4166c34c4194283941c1aca741ef50ae421d1462424af7da4278fb2b42a71e6c42d561b44303c518433248ae4360ec8d438fb0cb43be957f43ed9ac0441cc0a3444c0740447b6ead44aaf70244daa054450a6abb453a564d456a6323459a915245cae0f245fb521a462be4e2465c9961468d6fae46be67e046ef82104720be5547521cc647839d7b47b5408c47e706114818ee22484af8d6487d264648af768a48e1e9ba49147fee4947393f497a15c449ad159849e038d04a137f884a46e9d64a7a77d44aae299b4ae1ff434b15f8e64b4a169c4b7e587e4bb2bea54be7492b4c1bf8294c50cbb84c85c3f14cbae0ef4cf022ca4d25899c4d5b157e4d90c68b4dc69cdd4dfc988c4e32b9b44e69006e4e9f6cd44ed5ff004f0cb70c4f4395144f7a99304fb1c37c4fe9141350208b0e50582888508fec9c50c7d76550ffe8fe513821825170810b51a907b451e1b59a521a8ad752538786528cabc352c5f7aa52ff6b55533906e05372ca6853acb60753e6c9da542105fd545b6a8b5495f7a154d0ad5a550b8bd4554693295581c37855bd1cdb55f89f7056344b52567020a056ac1f7556e847ef57249a2957611642579dbc5757da8c83581786e65854ab9b5891fac158cf7474590d18d3594ae7fb5988e20959c7071c5a0557515a43d2c65a82799a5ac14bea5b0049d45b3f73775b7ec8f25bbe4a615bfdf7e55c3dd19c5c7dd7a45cbe0a1c5cfe69235d3ef4d75d7fad595dc092c75e01a53f5e42e4e35e8451d05ec5ec265f07b4055f49a98c5f8bccdb5fce1e1260109d5160534ab76096266560d9307b611c6919615fd05e61a3666d61e72b65622b1f66626f429262b3950962f816eb633cc85b6381a97863c6ba64640bfb4164516c2e64970d4f64dcdec36522e0ad6569132f65af766a65f60a7f663ccf926683c5c366caed356712460b6759d06567a18c6867e97a34683199ed6879ebb668c26fb1690b260169540ec9699d2a2c69e6784d6a2ff94f6a79ad566ac394856b0daeff6b57fce96ba27e656bed33996c381ca66c8339b26cce8ae16d1a10576d65ca386db1b8a86dfddbcc6e4a33c96e96c0c36ee382de6f307a416f7da7106fcb096f7018a18570666f7670b473687102ad8071511de4719fc4b971eea226723db650728d015d72dc8374732c3cba737c2d5573cc556d741cb528746d4cac74be1c20750f23ab7560637475b1dba276038c5b765575c876a7980f76f9f359774c87cc779f559077f25cce78459dac7899185478ecccec7940bb9e7994e49279e947ef7a3de5df7a92be8b7ae7d21a7b3d20b67b92aa887be86fba7c3e70737c94acde7ceb25237d41d96e7d98c9e67deff6b67e4760097e9f06067ef6e8da7f4f08ae7fa765ad80000000",
    "relocs": [
     [
      4938,
      "code",
      6046
     ],
     [
      4954,
      "code",
      5876
     ],
     [
      5004,
      "code",
      5876
     ],
     [
      5014,
      "code",
      6138
     ],
     [
      5032,
      "code",
      5870
     ],
     [
      5116,
      "code",
      6818
     ],
     [
      5258,
      "code",
      5098
     ],
     [
      5334,
      "code",
      5098
     ],
     [
      56,
      "bss",
      248
     ],
     [
      84,
      "bss",
      248
     ],
     [
      264,
      "bss",
      8
     ],
     [
      502,
      "bss",
      4
     ],
     [
      518,
      "bss",
      4
     ],
     [
      536,
      "bss",
      0
     ],
     [
      704,
      "bss",
      4
     ],
     [
      718,
      "bss",
      0
     ],
     [
      892,
      "bss",
      248
     ],
     [
      920,
      "bss",
      8
     ],
     [
      956,
      "code",
      6246
     ],
     [
      966,
      "bss",
      8
     ],
     [
      1010,
      "bss",
      248
     ],
     [
      1028,
      "bss",
      8
     ],
     [
      1128,
      "code",
      5098
     ],
     [
      1140,
      "bss",
      8
     ],
     [
      1270,
      "code",
      6257
     ],
     [
      1290,
      "bss",
      8
     ],
     [
      1350,
      "code",
      5222
     ],
     [
      1374,
      "bss",
      288
     ],
     [
      1390,
      "bss",
      8
     ],
     [
      1426,
      "code",
      6302
     ],
     [
      1464,
      "bss",
      300
     ],
     [
      1728,
      "bss",
      8
     ],
     [
      1800,
      "bss",
      312
     ],
     [
      1820,
      "code",
      5222
     ],
     [
      1852,
      "code",
      5918
     ],
     [
      1936,
      "code",
      5918
     ],
     [
      2210,
      "bss",
      248
     ],
     [
      2258,
      "code",
      6246
     ],
     [
      2268,
      "bss",
      8
     ],
     [
      2304,
      "code",
      6246
     ],
     [
      2314,
      "bss",
      8
     ],
     [
      2422,
      "bss",
      248
     ],
     [
      2440,
      "bss",
      8
     ],
     [
      3228,
      "code",
      6302
     ],
     [
      3266,
      "bss",
      300
     ],
     [
      3422,
      "code",
      5918
     ],
     [
      3880,
      "code",
      5918
     ],
     [
      4048,
      "code",
      5098
     ],
     [
      4060,
      "bss",
      8
     ],
     [
      4758,
      "bss",
      8
     ],
     [
      4772,
      "code",
      6046
     ],
     [
      4782,
      "code",
      6110
     ],
     [
      4854,
      "code",
      5918
     ],
     [
      5424,
      "chips_descriptor_base",
      1
     ],
     [
      5432,
      "chips_descriptor_base",
      3
     ],
     [
      5462,
      "chips_next_fmt",
      0
     ],
     [
      5546,
      "chips_descriptor_base",
      3
     ],
     [
      5588,
      "code",
      6202
     ],
     [
      5646,
      "code",
      4896
     ],
     [
      5708,
      "chips_descriptor_base",
      1
     ],
     [
      5718,
      "chips_descriptor_base",
      3
     ],
     [
      5764,
      "chips_next_draw",
      0
     ],
     [
      5776,
      "code",
      4896
     ],
     [
      5802,
      "code",
      5873
     ]
    ],
    "symbols": {
     "chips_update": [
      "code",
      0
     ],
     "chips_render": [
      "code",
      764
     ],
     "chips_ui_format": [
      "code",
      5396
     ],
     "chips_ui_draw": [
      "code",
      5664
     ]
    },
    "bss": 992
   }
  },
  "maxsaw": {
   "id": "maxsaw",
   "name": "Max Saw: seven sawtooths after Adam Szabo's analysis of the Super Saw",
   "order": 85,
   "version": "0.2",
   "symbols": {
    "update": "maxsaw_update",
    "render": "maxsaw_render"
   },
   "keep": [],
   "patch_points": [],
   "uses": [
    {
     "point": "machine",
     "name": "MAXSAW",
     "image": 5,
     "decay_default": 80,
     "knobs": [
      {
       "long": "MaxSaw Detune",
       "short": "DET",
       "default": 64
      },
      {
       "long": "MaxSaw Mix",
       "short": "MIX",
       "default": 95
      },
      {
       "long": "MaxSaw Tone",
       "short": "TONE",
       "default": 32
      },
      {
       "long": "MaxSaw Phase",
       "short": "PHAS",
       "default": 127
      }
     ]
    },
    {
     "point": "shortcut",
     "key": "MACHINES",
     "press": "PUNCH"
    }
   ],
   "conflicts_declared": [],
   "claims": {
    "sound_slots": [
     [
      32,
      "machine"
     ]
    ],
    "record_slots": [
     [
      18,
      "machine"
     ]
    ],
    "gestures": [
     {
      "combo": "MACHINES + PUNCH",
      "atoms": [
       [
        "MACHINES",
        "PUNCH"
       ]
      ],
      "situation": "any",
      "scope": "machine",
      "meaning": "Sub",
      "replaces": null
     }
    ]
   },
   "bundle": {
    "code": "4feffff448d7040c206f0014243c0000031c20080680bdcf77d84c420000226f0018263c4d585331b6a8002c6710720145f9000000002143002c15810800732900244a816d0001b273c1247c4011d84c45f21c00215202504aa80038676a243c012c0f26263c001f7c5c223c7fffffff2142027821420274243c82581e4b2143028421430280263c803ef8b821410294214102902142027c214302884a69001e6700015c223c200000002141029c243c60000000263c7fffffff7201214202a0214302a4214100487369001474184c00280045f90000000077690022e1890683ffffc000e78bd2af0010d28326010683ffc00000258328000c83007f00006f0000a0727f4841776900162583280477690018258128007369001a258328087769001c2581280c2200e589258328102241d3fc800017ec22514a89670000a6322900542600e78b73c12243d3fc423087fc082900000003672276424c0038002243d3fc800015ee36110803000a670c088100080283000001008283ee897602c681258328144aa8003856c141f9000000004481118108004cd7040c4fef000c4e7522034a836c00ff607769001642812583280477690018258128007369001a258328087769001c2581280c2200e589258328102241d3fc800017ec22514a896600ff5e76424c003800223c800015ee2243323118006000ff4c42816000fe4c243c7fffffff263c200000002142029c214302a0214202a442a800486000feac2f02206f000c4aa80034663c4aa800386636202802304a806d560c8000003fff6226202802344a806d520c8000003fff6216206f000820080680000000804298b08866fa241f4e752008243c0000031c0680bdcf77d84c4200002f002f082f2f00104eb9000000004fef000c241f4e7544800c8000003fff62ce60a6448060aa4fefffa048d77cfc242f006ca980725c4c0218002f40003843f90000000028012c410684000000004a312800660006c6264172184c02180045f900000000d7fc0000000049f90000000041f9000000004a342800660002e02e3018142f47002ca93c000000a0a13c000000002a30180020050680ffbb0000ef88227c0aaaaaaba2400800a1c2d482701843f9000000000682193b09732602e0a2028300ffffff700f2c020686ffffffe22e0342474847e1ab20317c0022717c0402837fff800093c0a6090800a1c37e01be866d000340d0834a866c00039876e1b6866e0006ae761e9682e6a80c80400000006200038c2c00243018040c8200007f006f000326243c00007f002e02ec8f7617e7aa43f90000000002870003fffc02827f8000002631780043f9000000002271780093c3a4090800a1c243f900000000d6822e3c000000002419a6020800a1c2a4060800a1c2d48026c2b3c766ea2c3018080c8600007f006f0005042c3c00007f002406ec8a7e17efae47f90000000002820003fffc02867f80000026025883227328002e3338009e89ac070800a1c747f900000000d3c72e3338002433280026099e82e883ac070800a1c6d486e88243f2e8004aa9005867000506234300382342003c42a900582f4200342f43003042af004842af00442230180c0c8100007f006f00046e223c00007f000681ffffe0002e3c000000c04c071800d2850681002400000c8100afffff6f00026e223c00afffff2c017e0f42464846efa94bf900000000e58e02817fff800020465888267568002275880093cba2090800a1c749f900000000d7c7227468002e3488002f4b00409e89a2070800a1c747f900000000d3c72c336800207388002f49003c91c6a2080800a1c12e0edc810687000000004aaf002c6e0002702f2f00482f2f00482f2f003c2f2f003c2f2f00742f072f044eb9000000004fef001c2a0f06850000005042802f00223c3504f3342f05200e0680000000002f002f2f00702f41006c2f6f005000602f6f004c00642f4600684eb900000000ddca2d4300382d42003c2f2f00784eb9400a92522f2f007c2f2f007c4eb9400a94302f2f00842f2f00844eb9400a967a262f005ca9034cef7cfc00244fef00844e752a3018100c8500007f006e0005324a856d0005e2203c000102044c005800a93c000000a0a13c000000002032e8542244263c0019660d4c03080006803c6ef35faa000800a1c322c3b3cb66e442057c012e3018142580e85442b2e8482586e858198528002f47002ca93c000000a0a13c000000002a30180020050680ffbb0000ef88227c0aaaaaaba2400800a1c2d482701843f9000000000682193b09732602e0a2028300ffffff700f2c020686ffffffe22e0342474847e1ab20317c0022717c0402837fff800093c0a6090800a1c37e01be866c00fcc4243018042c3c4000000020060c8200007f006e00fcde4a826c00fcde42822e02ec8f7617e7aa43f90000000002870003fffc02827f8000002631780043f9000000002271780093c3a4090800a1c243f900000000d6822e3c000000006000fcd8eda80c80400000006300fc78203c400000002c006000fc6e4a816c00fd9642812c017e0f42464846efa94bf900000000e58e02817fff800020465888267568002275880093cba2090800a1c749f900000000d7c7227468002e3488002f4b00409e89a2070800a1c747f900000000d3c72c336800207388002f49003c91c6a2080800a1c12e0edc810687000000004aaf002c6f00fd942045d1fc00240000b1fc00afffff6e0002cc4a886d00038022082a08424148412241720fe3ad22052a09e58d02817fff80002075580022452f48004c41e900042a7588009bef004ca20d0800a1c5daaf004c2a7498002f4500502a3488009a8da2050800a1c5dbc5227398002a3388002f4d00549a89a2050800a1c1d3c1223c0abe27962a0f0685000000502f41005c72022f4900582f05206f0030b2886d0001f02208e2a8204ed1fc000000002f002f084879000000004eb9000000002f2f00582f2f00582f2f004c2f2f004c2f2f00842f072f044eb9000000004fef002c203c000000002f00223c3504f3342f05200e0680000000002f002f2f00702f41006c2f6f005000602f6f004c00642f4600684eb900000000ddca2d4300382d42003c2f2f00784eb9400a92522f2f007c2f2f007c4eb9400a94302f2f00842f2f00844eb9400a967a262f005ca9034cef7cfc00244fef00844e754a816c00fb9642816000fb904a866c00fb0042862406ec8a7e17efae47f90000000002820003fffc02867f80000026025883227328002e3338009e89ac070800a1c747f900000000d3c72e3338002433280026099e82e883ac070800a1c6d486e88243f2e8004aa900586600fafe2c2900382e039e862269003cea872f4600302c029c89ea862f4900342f4700442f4600486000faf2223c9e3779b94c0218002004204406800000005c4218b1c066fa45f9000000000681000055a72581e854a93c000000a0a13c000000002032e854264e2044d7fc00000000263c7ffffc002a3c0019660d4c05080006803c6ef35fa6000800a1c120c1b1cb66e442067e0172182580e85442b2e8482587e8584c02180049f9000000001386280041f9000000004a3428006700f8d26000fbac428642806000f960307c00022208e2a8204ed1fc000000002f002f084879000000004eb9000000002f2f00582f2f00582f2f004c2f2f004c2f2f00842f072f044eb9000000004fef002c203c000000006000fe0c207c00afffff22082a08424148412241720fe3ad22052a09e58d02817fff80002075580022452f48004c41e900042a7588009bef004ca20d0800a1c5daaf004c2a7498002f4500502a3488009a8da2050800a1c5dbc5227398002a3388002f4d00549a89a2050800a1c1d3c1223c0abe27962a0f0685000000502f41005c72022f4900582f05206f0030b2886c00fd386000ff22203c000102042a3c00007f004c005800a93c000000a0a13c000000002032e85422446000face91c822082a08424148412241720fe3ad22052a09e58d02817fff80002075580022452f48004c41e900042a7588009bef004ca20d0800a1c5daaf004c2a7498002f4500502a3488009a8da2050800a1c5dbc5227398002a3388002f4d00549a89a2050800a1c1d3c1223c0abe27962a0f0685000000502f41005c72022f4900582f05206f0030b2886c00fc826000fe6c203c0001020442854c005800a93c000000a0a13c000000002032e85422446000fa1c4fefffd448d77cfc2c6f00304cd6007f2a6f0034206f003843e800802e2f003c246f0040266f0044286f0048de8bd5cca4400800d095a4410800d2ad0004a4420800d4ad0008ae030800d6ad000ca4440800d8ad0010a4450800daad0014a4460800dcad0018a1ce20cede8bd5cca4400800d095a4410800d2ad0004a4420800d4ad0008ae030800d6ad000ca4440800d8ad0010a4450800daad0014a4460800dcad0018a1ce20ceb1c966802c6f003048d6007f4cd77cfc4fef002c4e754fefffd848d73cfc206f002c43e800802a6f00302e15282d00042a2d00082a6f00382c15246d0004266d0008286d000c2a6f0034a8470800de8da1c19285a8060800a20a0800a1c2a80a0800a20b0800a1c3d6854484d882d8824485da83da8320c3a8470800de8da1c19285a8060800a20a0800a1c2a80a0800a20b0800a1c3d6854484d882d8824485da83da8320c3b1c966a02a6f00302a872b4400042b4500084cd73cfc4fef00284e754fefffd448d77cfc206f003043e800802a6f003428152a2d00042c6f00382c16246e0004266e0008286e000c202f003c660000a4201022009285a8060800a20a0800a1c2a80a0800a20b0800a1c3d6854484d882d8824485da83da83a40c0800a1c1908290819083d0806812223c7fffffff4a806b06223c80000000200120c0201022009285a8060800a20a0800a1c2a80a0800a20b0800a1c3d6854484d882d8824485da83da83a40c0800a1c1908290819083d0806812223c7fffffff4a806b06223c80000000200120c0b1c96600ff64600000a62c40201022009285a8060800a20a0800a1c2a80a0800a20b0800a1c3d6854484d882d8824485da83da83a40c0800a1c1908290819083d09ed0806812223c7fffffff4a806b06223c80000000200120c0201022009285a8060800a20a0800a1c2a80a0800a20b0800a1c3d6854484d882d8824485da83da83a40c0800a1c1908290819083d09ed0806812223c7fffffff4a806b06223c80000000200120c0b1c96600ff602a842b4500044cd77cfc4fef002c4e7540000000402c6be94058f6a84085a05140b268fa40df50b8410c57a241397dcc4166c34c4194283941c1aca741ef50ae421d1462424af7da4278fb2b42a71e6c42d561b44303c518433248ae4360ec8d438fb0cb43be957f43ed9ac0441cc0a3444c0740447b6ead44aaf70244daa054450a6abb453a564d456a6323459a915245cae0f245fb521a462be4e2465c9961468d6fae46be67e046ef82104720be5547521cc647839d7b47b5408c47e706114818ee22484af8d6487d264648af768a48e1e9ba49147fee4947393f497a15c449ad159849e038d04a137f884a46e9d64a7a77d44aae299b4ae1ff434b15f8e64b4a169c4b7e587e4bb2bea54be7492b4c1bf8294c50cbb84c85c3f14cbae0ef4cf022ca4d25899c4d5b157e4d90c68b4dc69cdd4dfc988c4e32b9b44e69006e4e9f6cd44ed5ff004f0cb70c4f4395144f7a99304fb1c37c4fe9141350208b0e50582888508fec9c50c7d76550ffe8fe513821825170810b51a907b451e1b59a521a8ad752538786528cabc352c5f7aa52ff6b55533906e05372ca6853acb60753e6c9da542105fd545b6a8b5495f7a154d0ad5a550b8bd4554693295581c37855bd1cdb55f89f7056344b52567020a056ac1f7556e847ef57249a2957611642579dbc5757da8c83581786e65854ab9b5891fac158cf7474590d18d3594ae7fb5988e20959c7071c5a0557515a43d2c65a82799a5ac14bea5b0049d45b3f73775b7ec8f25bbe4a615bfdf7e55c3dd19c5c7dd7a45cbe0a1c5cfe69235d3ef4d75d7fad595dc092c75e01a53f5e42e4e35e8451d05ec5ec265f07b4055f49a98c5f8bccdb5fce1e1260109d5160534ab76096266560d9307b611c6919615fd05e61a3666d61e72b65622b1f66626f429262b3950962f816eb633cc85b6381a97863c6ba64640bfb4164516c2e64970d4f64dcdec36522e0ad6569132f65af766a65f60a7f663ccf926683c5c366caed356712460b6759d06567a18c6867e97a34683199ed6879ebb668c26fb1690b260169540ec9699d2a2c69e6784d6a2ff94f6a79ad566ac394856b0daeff6b57fce96ba27e656bed33996c381ca66c8339b26cce8ae16d1a10576d65ca386db1b8a86dfddbcc6e4a33c96e96c0c36ee382de6f307a416f7da7106fcb096f7018a18570666f7670b473687102ad8071511de4719fc4b971eea226723db650728d015d72dc8374732c3cba737c2d5573cc556d741cb528746d4cac74be1c20750f23ab7560637475b1dba276038c5b765575c876a7980f76f9f359774c87cc779f559077f25cce78459dac7899185478ecccec7940bb9e7994e49279e947ef7a3de5df7a92be8b7ae7d21a7b3d20b67b92aa887be86fba7c3e70737c94acde7ceb25237d41d96e7d98c9e67deff6b67e4760097e9f06067ef6e8da7f4f08ae7fa765ad800000000000000a0000000b0000000c0000000e0000000f000000110000001300000016000000180000001b0000001e00000022000000260000002b00000030000000360000003d000000440000004d00000056000000610000006d0000007a000000890000009a000000ac000000c2000000d9000000f400000112000001330000015900000183000001b3000001e80000022300000266000002b20000030600000365000003cf00000447000004cc000005630000060c000006c90000079e0000088c0000099800000ac400000c1600000d9000000f39000011160000132d000015850000182700001b1b00001e6c000022240000265100002b00000030420000362800003cc60000443400004c89000055e30000606100006c260000795b0000882d000098cd0000ab730000c0600000d7d80000f22d00010fb6000130d7000155ff00017fac0001ae6a0001e2d500021d9e00025f890002a9720002fc520003593c0003c1660004362a0004b90c00054bbf0005f0270006a864000776d500085e200009613d000a837d000bc891000d349e000ecc400010949e0012937a0014cf3d00174f0e001a1ae8001d3bab0020bb3f0024a4a700290427002de76000335d7d00397753004047980047e30a005060b00059da0800646b54007033d5007d561b008bf858009c44b300ae69ab00c29a7c00d90f8b00f206dd010dc493012c936d014ec55c0174b413019ec1a601cd59340200ef8e023a03fa027920e902bedcc6030bdaca0360cbd703be6f640425946e04971a850513f2e0059d218b0633beb806d8f833078e12fc08546d33092d803e0a1ae3660b1e4eed0c399fce0d6edc560ec039c71030235c11c1430013768c3a155349e5175b2f7919926ef71bfdd4bc1ea2eb262188284d24b529382832fefb2c0c93fb304f3202350b357c3a54ff1840463c6846ffa9db4eab7ce35780b19e61c778c76679cfd76679cfd76679cfd76679cfd76679cfd70002310c00025267000275bf00029b300002c2db0002ece2000319680003489400037a8e0003af800003e79800042306000461fc0004a4b00004eb5b000536390005858b0005d9930006329a000690eb0006f4d700075eb30007ceda000845ab0008c38b000948e60009d62d000a6bd9000b0a69000bb264000c645a000d20e2000de89d000ebc34000f9c5b001089d30011856400128fe40013aa360014d54b00161220001761c20018c550001a3df5001bccf3001d739b001f335400210d9a002303ff0025182b00274be10029a0ff002c197c002eb77000317d1000346cb3003788d1003ad40b003e5126004203100045ece5004a11ee004e75a300531bb300580800005d3ea70062c40200689caa006ecd7d00755b9e007c4c7c0083a5d7008b6dbf0093aaa0009c634000a59ec600af64c100b9bd2e00c4b07700d0478200dc8baf00e986e400f743910105ccb601152deb0125736a0136aa110148df6b015c21bd0170800801860a11019cd06f01b4e48e01ce58b801e940200205aee70223ba27024377f80264ff7b028868de02adcd6502d5476d02fef277032aeb2603594f47038a3dcf03bdd6e103f43bc6042d8eee0469f3ea04a98f6104ec87080533018f057d269405cb1e84061d128706732c5a06cd962b072c7a660790038807f85bdd0865ad3c08d820bb094fde5509cd0c8b0a4fcff20ad84ac00b669c3e0bfae03e0c952e750d3599d00ddc2fb30e88f7320f3bf0330ff5128910b44cf611798428124491a21315429713eb56b614c67eed15a65c14168a7d8f17725fdd185d6b12194af1351a3a2c881b2a3d9f1c1a29431d08d6131df509c31edd65d61fc063b8209c4fe6216f43f122371edd22f17b67239ba36e24327f8e24b28194251787fd255cb7ea257c4a03256f44fd252d1e5e24ab365223dc1de722ae8e37210be8f71ed6040c1be3dc0b17fc8b7a12cf7e35103b0712103b0712103b0712103b0712103b07127ffce6867ffcb7587ffc855c7ffc50677ffc184c7ffbdcdb7ffb9de17ffb5b297ffb14797ffac9957ffa7a3e7ffa262f7ff9cd207ff96ec67ff90ad07ff8a0e97ff830b67ff7b9d87ff73be87ff6b67d7ff629227ff593617ff4f4b87ff44ca17ff39a8d7ff2dde37ff216027ff1423f7ff061e77fef74397fee786b7fed6da67fec53067feb279b7fe9ea647fe89a557fe7364d7fe5bd1e7fe42d867fe286317fe0c5b57fdeea957fdcf33c7fdaddfd7fd8a9127fd6529a7fd3d8987fd138f07fce71677fcb7fa07fc861197fc5132b7fc193087fbdddb77fb9f0117fb5c6bf7fb15e3b7facb2c67fa7c06c7fa282f97f9cf5fe7f9714c87f90da5d7f8a41777f8344837f7bdd997f74067b7f6bb8897f62ecc47f599bc37f4fbdaf7f454a3a7f3a389e7f2e7f907f22153c7f14ef3c7f0702917ef843997ee8a6067ed81cd67ec69a477eb40fd07ea06e117e8ba4ca7e75a2d07e5e56007e45ab2f7e2b8e1e7e0fe96e7df2a68b7dd3ada27db2e58d7d9033c37d6b7c477d44a1937d1b84887cf004597cc1fe767c914e767c5dce057c2754cb7bedb8557bb0cc017b7060e37b2c45b07ae446a57a982d707a47c11679f2c5df7998fd3e793a25b878d5fad3786c34ff77fc89857786aa74770a46987687096575fc9afa756aa01174d0ba07742e86da7383a13572cfa07e721218f0714a9bb17078b7006f9bf65d6eb3e2c56dc002f26cbfdba96bb2f0146a98c2236970d300683aa38c66f5b4e765a18907643da35562c9895f6144c3875faeddc15e0768535c4df8975a8229c158a39d9956b1fd3054acf98952944c2e5067b7b04e27080b4bd212ea4968b7d146eae01944587ee041b190d03ef61bed3c262f663941e3ac36495ae8333cc250301c54ba2ce85f5929a149bf2647a30422dc36dd1f602f091bd54828183e2537149ed47410fda5010d64832509e339d8069343b1039e64880292177b0292177b0292177b0292177b0292177b05adfb5006f7cd16083e9f92098272c50ac346b00c011b510d3bf0a90e73c6b80fa89d7e10da74fb12094d2f1335261a145dffbb1583da1416a6b52417c690ea18e36d6819fd4a9c1b1428881c28072a1d38e6841e46c6941f51a75b205988da215e6b0f22604dfb235f319e245b15f82553fb092649e0d1273cc74f282cae85291996722a037f162aea68702bce52822caf3d4a2d8d28ca2e6815002f4001ee3014ef9230e6dded31b5ccff3281bcc9334aad4934109e8034d3906e359383133650766e370a6a8137c15f4b387554cc39264b0439d441f23a7f39983b2731f43bcc2b083c6e24d23d0d1f533da91a8c3e42167b3ed813213f6b107e3ffb0e9240880d5d41120cdf41990d18421d0e08429e0faf431c120d43971522440f18ed44841d7044f622a94565289a45d12f41463a36a046a03eb5470347824763510547c05b3f481a6630487171d848c57e3749168b4d4964991a49afa79e49f7b6d94a3cc6cb4a7ed7734abde8d34af9faea4b330db74b69213c4b9c35774bcc4a6a4bf960134c2376734c4a8d8b4c6ea5594c8fbdde4cadd71a4cc8f10d4ce10bb74cf627184d0843304d175fff4d237d844d2c9bc14d32bab54d35da5f4d35fac14d331bd94d2d3da94d24602f4d18836d4d09a7614cf7cc0c4ce2f16e4ccb17884cb03e584c9265df4c718e1d4c4db7124c26e0bd4bfd0b204bd0363a4ba0620b4ba0620b7fb98c7e7f2ab2207e9bd7c27e0cfd647d7e23067cef48a77c606e497bd193eb7b42b98d7ab3df2f7a2504d179962a7379075014787875b677e99b58775ac0fa76cbe69c763d0c3e75ae31e0751f578174907d237401a2c57372c86772e3ee09725513ab71c6394d71375eee70a884907019aa326f8acfd46efbf5766e6d1b186dde40b96d4f665b6cc08bfd6c31b19f6ba2d7416b13fce36a85228569f6482669676dc868d8936a6849b90c67badeae672c0450669d29f2660e4f93657f753564f09ad76461c07963d2e61b63440bbd62b5315f6226570061977ca26108a2446079c7e65feaed885f5c132a5ecd38cc5e3e5e6d5daf840f5d20a9b15c91cf535c02f4f55b741a975ae540395a5665da59c78b7c5938b11e58a9d6c0581afc62578c220456fd47a5566e6d4755df92e95550b88b54c1de2d543303cf53a4297153154f12528674b451f79a565168bff850d9e59a504b0b3c4fbc30de4f2d567f4e9e7c214e0fa1c34d80c7654cf1ed074c6312a94bd4384b4b455dec4ab6838e4a27a9304998ced24909f474487b1a1647ec3fb8475d655946ce8afb463fb09d45b0d63f4521fbe1449321834404472543756cc642e692684257b80a41c8ddac413a034e40ab28f0401c4e923f8d74333efe99d53e6fbf773de0e5193d520abb3cc3305d3c3455fe3ba57ba03b16a1423a87c6e439f8ec86396a122838db37ca38db37ca0062aecb00e4ea1101261be4013fdba10144db130142484a0140f959014668590155855b016f639b0193c6a201c193ac01f72b340232ae300272320302b3e61002f62d580337ae5603775b0b03b472e603ee7ffb042550d10458efd00489993304b7b04a04e3b497050e37480537d16e05611b3a058aa46e05b4ee1c05e065cc060d6201063c2019066cc369069f558c06d3c7ae0709f4c50741a47b077a8eb107b45f6a07eebaf60829423a086396ef089d5fb708d64be7090e16f409448b6c0979855a09acf42709dedbd10a0f55830a3e8f910a6cccd60a9a63770ac7bb280af54aeb0b2396730b532b240b849cdf0bb8829a0bef72f10c2a00b40c68b7940cac190b0cf499840d429de90d96799b0df06cec0e50a4210eb7370a0f24292f0f976a9c1010d938109042bb1115671a119ffb67122fad1a12c42594135d0dce13fa121b149ae5c5153f467615e6ff351691eadf173ff5ec17f11f5318a57880195d242c1a1853f61ad744cb1b9a39ee1c6176c11d2d374c1dfda7ac1ed2da9e1facbf6d208b179a216d6cd8225307d8233ae8bb2423c211250bf76b25f1a0d126d2948d27ac78fc287ce05d294170c029f81aac2a9f61342b36b6ad2bbef1822c3add0c2cafeabf2d27086c2dada0e02e56cc922f3cb8bc30824bb232550df934ef604d389b07573db416b344ac459b4e0eb85b5a844a8b6ad8670b7ffe7b8e7ffe7b8ef1eac317f7f36781fd80408200000000028c7bb907f509010dc1003b",
    "relocs": [
     [
      696,
      "bss",
      0
     ],
     [
      706,
      "bss",
      156
     ],
     [
      728,
      "bss",
      156
     ],
     [
      734,
      "bss",
      184
     ],
     [
      740,
      "bss",
      6
     ],
     [
      746,
      "bss",
      12
     ],
     [
      810,
      "code",
      3806
     ],
     [
      942,
      "code",
      8002
     ],
     [
      964,
      "code",
      8006
     ],
     [
      982,
      "code",
      8518
     ],
     [
      990,
      "code",
      8546
     ],
     [
      1046,
      "code",
      7486
     ],
     [
      1084,
      "code",
      6970
     ],
     [
      1226,
      "code",
      6258
     ],
     [
      1260,
      "code",
      5546
     ],
     [
      1288,
      "code",
      4834
     ],
     [
      1320,
      "bss",
      184
     ],
     [
      1358,
      "code",
      3050
     ],
     [
      1390,
      "bss",
      220
     ],
     [
      1422,
      "code",
      3412
     ],
     [
      1640,
      "code",
      3806
     ],
     [
      1748,
      "code",
      8002
     ],
     [
      1770,
      "code",
      8006
     ],
     [
      1788,
      "code",
      8518
     ],
     [
      1796,
      "code",
      8546
     ],
     [
      1848,
      "code",
      6258
     ],
     [
      1882,
      "code",
      5546
     ],
     [
      1910,
      "code",
      4834
     ],
     [
      1942,
      "bss",
      184
     ],
     [
      2124,
      "bss",
      228
     ],
     [
      2134,
      "bss",
      708
     ],
     [
      2140,
      "code",
      3240
     ],
     [
      2170,
      "code",
      3050
     ],
     [
      2180,
      "bss",
      708
     ],
     [
      2198,
      "bss",
      220
     ],
     [
      2230,
      "code",
      3412
     ],
     [
      2330,
      "code",
      7486
     ],
     [
      2368,
      "code",
      6970
     ],
     [
      2478,
      "bss",
      156
     ],
     [
      2514,
      "bss",
      184
     ],
     [
      2576,
      "bss",
      6
     ],
     [
      2586,
      "bss",
      12
     ],
     [
      2622,
      "bss",
      228
     ],
     [
      2632,
      "bss",
      708
     ],
     [
      2638,
      "code",
      3240
     ],
     [
      2668,
      "code",
      3050
     ],
     [
      2678,
      "bss",
      708
     ],
     [
      50,
      "bss",
      0
     ],
     [
      212,
      "bss",
      12
     ],
     [
      396,
      "bss",
      6
     ],
     [
      642,
      "code",
      670
     ]
    ],
    "symbols": {
     "maxsaw_update": [
      "code",
      0
     ],
     "maxsaw_render": [
      "code",
      542
     ]
    },
    "bss": 836
   }
  },
  "terra": {
   "id": "terra",
   "name": "TERRA: wave terrain synthesis after Plaits",
   "order": 86,
   "version": "0.1",
   "symbols": {
    "update": "terra_update",
    "render": "terra_render"
   },
   "keep": [],
   "patch_points": [],
   "uses": [
    {
     "point": "machine",
     "name": "TERRA",
     "image": 4,
     "decay_default": 64,
     "knobs": [
      {
       "long": "Terra Surface",
       "short": "SURF",
       "default": 0
      },
      {
       "long": "Terra Radius",
       "short": "RAD",
       "default": 64
      },
      {
       "long": "Terra Shift",
       "short": "SHFT",
       "default": 64
      },
      {
       "long": "Terra Aux",
       "short": "AUX",
       "default": 0
      }
     ]
    }
   ],
   "conflicts_declared": [],
   "claims": {},
   "bundle": {
    "code": "4feffff048d70c0c206f0018243c0000031c20080680bdcf77d84c420000226f001c263c54524131b6a8002c6754742c4c002800223c00000000263c400000002441264227831800267c80000000720142b2280442b22808258b280c42b2281042b2282442b2282042b2281c42b2281842b2281425812828243c545241312142002c732900244a816d00012473c1247c4011d84c45f21c00215202504aa80038676a263c012c0f26267c001f7c5c223c7fffffff21430278243c82581e4b21430274263c803ef8b8214b0284214b028021410294214102902142027c214302884a69001e670000ce267c200000007601223c60000000243c7fffffff214b029c214102a0214202a42143004874144c02080041f9000000007369001475690022e189244245eac000260ae78bd2af0014d2832441d5fcffc00000218a0800b5fc007f00006f32727f4841756900167769001821810800218208047569001c218308087369001a218208104cd70c0c2181080c4fef00104e75220a4a8a6ccc7569001677690018428121810800218208047569001c218308087369001a218208104cd70c0c2181080c4fef00104e7542816000feda267c7fffffff223c20000000214b029c214102a0214b02a442a800486000ff3a2f02206f000c4aa80034663c4aa800386636202802304a806d560c8000003fff6226202802344a806d520c8000003fff6216206f000820080680000000804298b08866fa241f4e752008243c0000031c0680bdcf77d84c4200002f002f082f2f00104eb9000000004fef000c241f4e7544800c8000003fff62ce60a6448060aa4fefff0448d77cfc202f0108a9812f410074a93c000000a0a13c000000007614742c4c0038004c00280041f90000000045f900000000227038002f42005cb3f2280c66001286286f005c45f9000000002272c800a2490800a1c0244cd5fc00000000222a0004a2010800a1c4a2090800a1c22a2a00082f450040a4050800a1c2d084d08224000682e00200000c82000400006326243c600000009480a4090800a1c0d08043f9000000002380c800a4010800a1c0d08025400004286f005c2230380845f9000000002432c8100c8100007f006f001020223c00007f003801203c000102044c0018002030380cc9fc0810484448c42244d3c10c8000007f006f000fe8203c00007f003a00223c000102044c01080022303804cbfc0810484548c5da800c8100007f006f000f44223c00007f003001283c000102044c041800c1fc0810484048c0d081223c06666666a2000800a1c40c821fffffff62000f462202e589a2010800a1c12c3c7fffffff9c81223c73333333a2090800a1c1ac010800a1c1227c7fffffff06810ccccccd93c2a2410800a1c2223c3ccccccda2050800a1c10681e00000002c014a816d00123e2a3c200000009a86da85aa020800a1c7227c7fffffffe28293c4b3c06d000f46d084227c06fffd3fa2400800a1c4203038100c8000007f006f000e78203c00007f0036002a3c000102044c050800206f005cd1fc00000000c7fc0810484348c3d6802f4300684aa80028671821470014214200182141001c214400202143002442a8002841f90000000076e02442284720042c47226f005c267098002049d1fc0000000095e8001899e80014224193e8001c2a0aca832c0ccc83260990a800202a68000421470014214200182141001c214400202f4500387ae09dc62c01c6852a280024216f006800242f45006c2a00ea852f4500582a0cea8528429c8399ef00382f4600382f45004c2a0aea852f4500502a2f00688aaf006c2f4500782a09ea852f4500544aaf005867000e4272e0c08145ef00fc41ef007c2f4a0034244e2c4c2f4800702f6f010000442f48003c43f9000000002f46002c98807418d8af0058262f0054d5ef004c20042204ef88e4a1ddef00502a2f0040d7af002c02807fffff802f400038aa450800a1c0d7c0a6450800a1c09bc0a44b0800a1c0206f002cd1c0ac4d0800a1c27c04bc816d0004a47e01be816c0003207002b08167000b1a57814a816700064820020680f80000004a806d0002a4e48076197c3f0680015c28f6220004c1e3a82a00e6adef88ca86e28826315c002a315c049a83a0050800a1c07e07d680be816c0002a65181e3ab22022008068130000000068010000000a2000800a1c04a806d00020e068002cccccd2a00721904c5eba87e3f2c00e2aeef88cc87e28822316c002c316c049c81a0060800a1c0d2807007b0856c0002105185eba92a3c145a1cacaa030800a1c02c3c3d0e5604ac010800a1c17e11d2802601eeab700de1a9287c8000eee40283000003fce28920343800287c8000eee8263438009680a2030800a1c1d081e2804aaf0038670000ea26020683200000002203ee810c834000007f6f0007ae223c0080000026017a0febab484148c1287c20000000d9c802837fff80002f410060223c000084007a7e4845aa0c0800a1c70c87003f00006d0004602e3c003effff2a072841484548c5cafc0084daaf00607bc541f45a00d1fc00000000736800027d6800047b509c819c81dc8548464246a6060800a1c692854841424128467b68010a7d68010c9c859c852f41006073680108dc819a81222f0060d28c48464246a6060800a1c37c0f48454245edafda8302877fff80009a81ae050800a1c3d283e9899280262f0038a6010800a1c1d0812040e28041f02a00286f004458af004428c02208d281206f003c58af003c20c1b1ef00346600fd94286f005c45f900000000258bc800258dc8044aaf007866000e602f2f01044eb9400a9252206f010826280034242800382f082f2f010842a8003442a800384eb9400a94302f2f01102f2f0110226f011823430034234200384eb9400a967a202f0088a9004cef7cfc00144fef01104e754480068002cccccd2a00721904c5eba87e3f2c00e2aeef88cc87e28822316c002c316c049c81a0060800a1c0d2807007b0856d00fdf470089085e0a16000fdee4480e48076197c3f0680015c28f6220004c1e3a82a00e6adef88ca86e28826315c002a315c049a83a0050800a1c07e07d680be816d00fd5e70089081e0a322022008068130000000068010000000a2000800a1c04a806c00fd5c6000ff644a81660005ce203c5178d4fea0080800a1c12601700ce98be1a97a1849f900000000eaabe28920343c0026343c049680a2030800a1c6220806813245a1cba2020800a1c1263c5189374ca6010800a1c372117e0d2a03e2adefab287c8000eee40285000003fce28b22345800287c8000eee82a3458009a81a6050800a1c3d086d283e281e2809081223c48f5c28fa2000800a1c04aaf00386700fe302e08de82a4080800a1c3223c5189374ca2070800a1c17c137e0b2a01ecadefa9287c8000eee42c3c8000eee80285000003fce28920452a30c8002070680091c5a2080800a1c1da81a6030800a1c1e9897e1906810199999a260104c3e7a92c01eeae7e3fef89cc87e28920716c002c316c049c88a2060800a1c17c07d288bc836c000c2a5183e7a92e3c145a1cacae050800a1c3a2030800a1c37a117c0d2203eaa90281000003fcedab2e3c8000eee4287c8000eee82041223078002070c800e28b91c1a6080800a1c3d283e281262f00389280a6010800a1c1d0816000fd5020020680200000002600ee830c804000007f6f00019c263c00800000287c20000000707e4840d9c8a00c0800a1c70c87003f00006d00016e2e3c003effff20072a03484048c0484548c52c3c00004200c0fc00842f4500607a079a814c0658007c0fedabd0af0060204571c041f00a0002837fff8000d1fc00000000716800027d6800047b509c809c80dc8548464246a6060800a1c69085484042402f4600647b68010a7d68010c9c859c852f40003071680108dc809a80202f003048464246d0af0064a6060800a1c6484542452f4600647c0fedafdaaf006402877fff80009a80ae050800a1c5d085e9884aaf00386700fc5c7a069a81223c000042004c0518007a7e4845aa0c0800a1c70c87003f00006c00fba44a876c00fba442872a072841484548c5cafc0084daaf00607bc541f45a00d1fc00000000736800027d6800047b509c819c81dc8548464246a6060800a1c692854841424128467b68010a7d68010c9c859c852f41006073680108dc819a81222f0060d28c48464246a6060800a1c37c0f48454245edafda8302877fff80009a81ae050800a1c3d283e9896000fb9e4a876c00fe9642876000fe904a836c00fe6842836000fe62a4080800a1c6220220080681080000000680f8000000a2000800a1c04a806d00014e2840721949f40c007e3f200c068010000000260004c3e7a82a00e2adef88ca87e28822315c002a315c049a81a0050800a1c0d2807007b0836c0001505183e7a9263c65db22d1a6060800a1c0a2000800a1c17a0a7c142601eaabeda9287c8000eee40283000003fce28920343800287c8000eee8263438009680a2030800a1c1d081e2804aaf00386700fae622020681f80000004a816d000156e48176197e3f0681015c28f62a0104c5eba92c01e6aeef89cc87e28926316c002c316c049c83a2060800a1c1d6817207b2856c00015851852202d1fc10000000ebab068130000000a2080800a1c14a816d0000a8068102cccccd2a017e1904c5eba92c01eeae7e3fef89cc87e28920716c002c316c049c88a2060800a1c17c07d288bc856c0000aa5185eba92e3c145a1cacae030800a1c5207c3d0e5604a0410800a1c3d6857a117c0d2203eaa96000fc9a44802840721949f40c007e3f200c068010000000260004c3e7a82a00e2adef88ca87e28822315c002a315c049a81a0050800a1c0d2807007b0836d00feb470089083e0a16000feae4481068102cccccd2a017e1904c5eba92c01eeae7e3fef89cc87e28920716c002c316c049c88a2060800a1c17c07d288bc856d00ff5a7c089c85eca12e3c145a1cacae030800a1c5207c3d0e5604a0410800a1c3d6856000ff544481e48176197e3f0681015c28f62a0104c5eba92c01e6aeef89cc87e28926316c002c316c049c83a2060800a1c1d6817207b2856d00feac7208d1fc100000009285e2a32202068130000000a2080800a1c14a816c00feaa6000ff4c4a816c00f856428126017a0f484148c1ebab287c20000000d9c82f410060223c0000840002837fff80006000f850a4080800a1c5203c5189374c2e08de82a0070800a1c07c132600ecab7c0beda8287c8000eee40283000003fce2882c343800287c8000eee8263438009686a0030800a1c0dc802f460060aa050800a1c0e9887c1906800199999a2a0004c5eba82600ecab7c3fef88c686e28828713c0026313c04968ca0030800a1c0260cd6807007b0856c0004205185ebab2a2f00602c3c145a1cacac050800a1c0a6000800a1c370117c0d2a03e0adedab287c8000eee40285000003fce28b20345800287c8000eee82a3458009a80a6050800a1c3d083e2804aaf00386700f81e7601b681660000a6a4080800a1c3223c4c624dd3a2030800a1c17c0f2a01ecadeda92e3c8000eee4287c8000eee80285000003fce28920452c3078002070c80091c6a2080800a1c1dc81a6030800a1c1e9897e19068102cccccd260104c3e7a92a01eead7e3fef89ca87e28920715c002a315c049a88a2050800a1c1d1c17207b2836c000a6c51832a08287c145a1cace7ad2045a8460800a1c1a0410800a1c37a117c0d2203eaa96000f9e652814a816600f940223c5178d4fea2080800a1c126017a0ce98beba97c1849f900000000ecabe2892c343c0026343c049686a2030800a1c5d1fc3245a1cba0420800a1c1207c5189374ca0410800a1c37e112203eea97e0defab287c8000eee40281000003fc2e3c8000eee8e28b20412230c8002070780091c1a6080800a1c3da86d283e281e2859a81223c48f5c28fa2050800a1c1262f00389280a6010800a1c1d0816000f6caa4080800a1c3203c4c624dd3a0030800a1c07a0f2200eaa9eba8287c8000eee40281000003fce2882a341800287c8000eee8223418009285a0010800a1c0da80a6030800a1c0e98872197e3f068002cccccd260004c3e7a82c00e2aeef88cc87e28822316c002c316c049c81a0060800a1c0d2807007b0836c0002065183e7a9263c145a1caca6050800a1c0a2000800a1c17a117c0d2601eaabeda9287c8000eee40283000003fce28920343800287c8000eee8263438009680a2030800a1c1d081e2804aaf00386700f5fea4080800a1c52202d1fcf8000000068108000000a2080800a1c14a816d00008c28417e1941f41c002208068110000000260104c3e7a92c01eeae7e3fef89cc87e28920716c002c316c049c88a2060800a1c17c07d288bc836c00008e5183e7a92e3c65db22d1ae050800a1c3a2030800a1c37a0a7c142203eaa90281000003fcedab2e3c8000eee4287c8000eee82041223078002070c800e28b91c1a6080800a1c3d283e2816000f7f4448128417e1941f41c002208068110000000260104c3e7a92c01eeae7e3fef89cc87e28920716c002c316c049c88a2060800a1c17c07d288bc836d00ff767c089c83eca12e3c65db22d1ae050800a1c3a2030800a1c37a0a7c142203eaa96000ff704a806c00f18c42806000f1864a816c00f0c042813001283c000102044c041800c1fc0810484048c0d081223c06666666a2000800a1c40c821fffffff6300f0be4286223c73333333a2090800a1c1ac010800a1c1227c7fffffff06810ccccccd93c2a2410800a1c2223c3ccccccda2050800a1c10681e00000002c014a816c00f0ce600003064a806c00f01c42806000f0164a816c00efe442816000efde70089085e0a36000fbde70089083e0a16000fdf8203c7fffffff6000f0b620047218ef88e2a402807fffff802f40003c4a80660003467403b4846d00070a7601b6846c000f4c55844a8467001ad82c2f01002e3c8000eee4282f003843ef007c2f490070244941ef00fcddef004c2f480044d9ef0050d8af0054202f004043f9000000002f46003caa400800a1c0222f0040d7c0a6410800a1c09bc0ac4b0800a1c0d084a84d0800a1c3a6000800a1c622030680f8000000068108000000a2000800a1c04a806d00146a20407a1941f00c002008068010000000220004c1e3a82400eaaa7a3fef88c485e28820712c0024312c049488a0020800a1c0d1c0700874079081b4816c00146c51812a08243c65db22d1e3ad2045a4060800a1c0a0400800a1c17a0a7c142001eaa8eda9243c8000eee80280000003fce2892040203078002070280091c0a2080800a1c1d0812200e281e480204141f03a002208d281206f003c58af003c20c024c1b5ef00446700f308ddef004cd9ef0050d8af0054202f0040aa400800a1c0222f0040d7c0a6410800a1c09bc0ac4b0800a1c0d084a84d0800a1c3a6000800a1c622030680f8000000068108000000a2000800a1c04a806c00ff066000136a20090680ffbb0000ed8874037a187c0f45f9000000004c4208000680193b09732800eaa0028400ffffff24000682ffffffe22a0442454845edac22325c002a325c0402847fff80009a81a8050800a1c47e01be826d000a94d2844a826c000a7a78e1b8826e0009ee741e94802001e4a867000a6e0c802a0000006306203c2a0000002200e289246f005cd5fc0000000025400010203c6487ed51a0010800a1c0e588a0000800a1c1243c030c30c3a4010800a1c2283c06666666a8010800a1c4e2822a3c400000009a82aa040800a1c4243c15555555a4010800a1c1243c400000009484a4010800a1c2223c400000009282a2000800a1c0e5882549000c254000086000ec787c089c83eca12e3c145a1cacae050800a1c3a2030800a1c36000f3d444866000edc0262f006874e0222f00684280266f0100247c8000eee496af006c286f0070227c8000eee8c483ea839282d2834a81661258800c80000000806700f168d2834a8167ee243408007a182802eaace18ae58ce28a20724800283148009888a4040800a1c2d488e48228330800204291c4a2080800a1c2d8822784080058800c800000008066b86000f11c7003b0846c0006207004b084670023185b844a8467002782202f005445ef007c43ef00fcddef004cd9ef0050222f00402f4a00702f6f010000442f490048d1af0038aa410800a1c0d7c0a6410800a1c09bc0ac4b0800a1c1a84d0800a1c520050680200000002400ee820c804000007f6f0001bc243c00800000226f0038d3c1767e4843d3fc20000000a6090800a1c40c84003f00006d0001be283c003effff20042c02484048c0484648c67e0fefaac0fc008402827fff8000d08671c0d0802040d1fc000000007168000277680004735096809680d68148434243a4030800a1c39081484042402f4300587368010a7768010c7f68010896819681d68748434243d0af0058a4030800a1c392877e0f48414241efacd28302847fff80009280a8010800a1c1d081e988207c007e0000a0490800a1c70c87003f00006d0001c02e3c003effff2207484148c1c2fc0084d28673c1d2812041d1fc000000007368000279680004775098819881d88348444244a4040800a1c49283484142417768010a7d680108d2847968010c98839883d88648444244a4040800a1c29686780f48434243e9afd68202877fff80009681ae030800a1c2d282e9892c2f003c9280ac010800a1c1d0812040e28041f05a00226f004458af004422c02208d28124c1b5ef00486700ef1a202f0054ddef004cd9ef0050222f0040d1af0038aa410800a1c0d7c0a6410800a1c09bc0ac4b0800a1c1a84d0800a1c520050680200000002400ee820c804000007f6e00fe484a826c00fe48226f0038d3c1767e48434282d3fc20000000a6090800a1c40c84003f00006c00fe464a846c00fe46428420042c02484048c0484648c67e0fefaac0fc008402827fff8000d08671c0d0802040d1fc000000007168000277680004735096809680d68148434243a4030800a1c39081484042402f4300587368010a7768010c7f68010896819681d68748434243d0af0058a4030800a1c392877e0f48414241efacd28302847fff80009280a8010800a1c1d081e988207c007e0000a0490800a1c70c87003f00006c00fe444a876c00fe4442872207484148c1c2fc0084d28673c1d2812041d1fc000000007368000279680004775098819881d88348444244a4040800a1c49283484142417768010a7d680108d2847968010c98839883d88648444244a4040800a1c29686780f48434243e9afd68202877fff80009681ae030800a1c2d282e9892c2f003c9280ac010800a1c1d0812040e28041f05a00226f004458af004422c02208d28124c1b5ef00486600fe426000ed56720892832e08e2a7287c145a1cac2047a8460800a1c1a0410800a1c36000f5927005b0846d0005f441ef007c7204246f01002f480070b284670019f22a2f0038224841ef00fc2f48003cddef004cd9ef0050daaf00542e2f0040aa470800a1c0d7c0a6470800a1c09bc0ac4b0800a1c1a84d0800a1c620060680200000002800ee840c804000007f6f000114283c008000002005d081727e4841068020000000a2000800a1c30c83003f00006d000116263c003effff20032204484048c0484148c1740fe5acc0fc008402847fff8000d08171c0d0802040d1fc000000007168000275680004735094809480d48148424242a8020800a1c29081484042402f4200407368010a7568010c948194812f40003871680108d4809280202f003848424242d0af0040a8020800a1c2780f48414241e9abd28202837fff80009280a6010800a1c1d081e9882040e28041f06a0024c02208d28122c1b3ef003c6700ebf6ddef004cd9ef0050daaf0054aa470800a1c0d7c0a6470800a1c09bc0ac4b0800a1c1a84d0800a1c620060680200000002800ee840c804000007f6e00fef04a846c00fef02005d081727e48414284068020000000a2000800a1c30c83003f00006c00feee4a836c00feee428320032204484048c0484148c1740fe5acc0fc008402847fff8000d08171c0d0802040d1fc000000007168000275680004735094809480d48148424242a8020800a1c29081484042402f4200407368010a7568010c948194812f40003871680108d4809280202f003848424242d0af0040a8020800a1c2780f48414241e9abd28202837fff80009280a6010800a1c1d081e9882040e28041f06a0024c02208d28122c1b3ef003c6600feec6000eadc7201b2846c0007ce55844a84670013d4202f00542e3c8000eee443ef007c2f4900702c3c8000eee841ef00fc2f490058ddef004c2f480048d9ef005043f900000000222f00402f6f01000044d1af0038aa410800a1c0d7c0a6410800a1c09bc0ac4b0800a1c0206f0038d1c0a84d0800a1c3a6080800a1c5200822030680f8000000068108000000a2000800a1c04a806d000a162440721945f20c00200a068010000000240004c2e5a82800e2ac723fef88c881e28822314c0028314c049881a0040800a1c07807d280b8826c000a185182e5a9247c65db22d1a4450800a1c0a2000800a1c0720a78142400e2aae9a80282000003fce288244222327800243268009481a0020800a1c2d2822003e2810680f80000004a806d000a1ae48074190680015c28f6280004c4e9a82a00e4ad743fef88ca82e28824315c002a315c049a82a0050800a1c07a07d480ba846c000a1c5184e9aa2003d1fc100000000680300000002442a0080800a1c04a806d000880068002cccccd2800741904c4e9a82a00e4ad743fef88ca82e28820715c002a315c049a88a0050800a1c07a07d088ba846c0008825184e9a8207c145a1caca04a0800a1c4247c3d0e5604a4400800a1c2d48478117a0d2002e8a8ebaa0280000003fce28a2040203078002070680091c0a4080800a1c2d082e280242f003c9081a4000800a1c0d0812040e28041f03a00246f004458af004424c02208d281206f005858af005820c1b1ef00486700e8ba202f0054ddef004cd9ef0050222f0040d1af0038aa410800a1c0d7c0a6410800a1c09bc0ac4b0800a1c0206f0038d1c0a84d0800a1c3a6080800a1c5200822030680f8000000068108000000a2000800a1c04a806c00fe1c6000082c246f005c7001d5fc0000000025400010203c6487ed514281a0010800a1c0e588a0000800a1c1243c030c30c3a4010800a1c2283c06666666a8010800a1c4e2822a3c400000009a82aa040800a1c4243c15555555a4010800a1c1243c400000009484a4010800a1c2223c400000009282a2000800a1c0e5882549000c254000086000e2a62001e5a86600f59670012200e2896000f59e246f005c203c2a000000d5fc0000000025400010223c15000000203c6487ed51a0010800a1c0e588a0000800a1c1243c030c30c3a4010800a1c2283c06666666a8010800a1c4e2822a3c400000009a82aa040800a1c4243c15555555a4010800a1c1243c400000009484a4010800a1c2223c400000009282a2000800a1c0e5882549000c254000086000e2085d844a84670016a02a2f003843ef007c41ef00fcddef004cd9ef0050daaf0054246f01002e2f00402f4900702f48003caa470800a1c0d7c0a6470800a1c09bc0ac4b0800a1c1a84d0800a1c620060680200000002800ee840c804000007f6f000114283c008000002005d081727e4841068020000000a2000800a1c30c83003f00006d000116263c003effff20032204484048c0484148c1740fe5acc0fc008402847fff8000d08171c0d0802040d1fc000000007168000275680004735094809480d48148424242a8020800a1c29081484042402f4200407368010a7568010c948194812f40003871680108d4809280202f003848424242d0af0040a8020800a1c2780f48414241e9abd28202837fff80009280a6010800a1c1d081e9882040e28041f06a0024c02208d28122c1b3ef003c6700e606ddef004cd9ef0050daaf0054aa470800a1c0d7c0a6470800a1c09bc0ac4b0800a1c1a84d0800a1c620060680200000002800ee840c804000007f6e00fef04a846c00fef02005d081727e48414284068020000000a2000800a1c30c83003f00006c00feee4a836c00feee428320032204484048c0484148c1740fe5acc0fc008402847fff8000d08171c0d0802040d1fc000000007168000275680004735094809480d48148424242a8020800a1c29081484042402f4200407368010a7568010c948194812f40003871680108d4809280202f003848424242d0af0040a8020800a1c2780f48414241e9abd28202837fff80009280a6010800a1c1d081e9882040e28041f06a0024c02208d28122c1b3ef003c6600feec6000e4ec4a846600064c45ef00fc282f00382c3c5189374c41ef007c2f4a00442e3c48f5c28f2f4800702f6f0100003c224845f900000000ddef004cd9ef0050d8af0054202f0040aa400800a1c0222f0040d7c0a6410800a1c09bc0ac4b0800a1c02044d1c0a84d0800a1c3243c5178d4fea4080800a1c124017a0ce98aeba97018e0aae28920322c0024322c049480a2020800a1c12f410038d1fc3245a1cba0430800a1c1ac010800a1c27a112202eaa97a0debaa2a3c8000eee40281000003fce28a2041223058002a3c8000eee82070580091c1a4080800a1c2d0af0038d282e281e2809081ae000800a1c02040e28041f03a002208d281206f003c58af003c20c022c1b3ef00446700e3e2ddef004cd9ef0050d8af0054202f0040aa400800a1c0222f0040d7c0a6410800a1c09bc0ac4b0800a1c02044d1c0a84d0800a1c3243c5178d4fea4080800a1c124017a0ce98aeba97018e0aae28920322c0024322c049480a2020800a1c12f410038d1fc3245a1cba0430800a1c1ac010800a1c27a112202eaa97a0debaa2a3c8000eee40281000003fce28a2041223058002a3c8000eee82070580091c1a4080800a1c2d0af0038d282e281e2809081ae000800a1c02040e28041f03a002208d281206f003c58af003c20c022c1b3ef00446600fe566000e3084a84660005d245ef00fc43f9000000002f4a00482c3c8000eee42f4900582e3c8000eee845f900000000226f003841ef007c2f4a0038244d2a482f4800702f6f01000044ddef004cd9ef0050d3ef0054202f0040a4400800a1c0222f0040d7c0a6410800a1c095c0ac4b0800a1c02209d280a84a0800a1c3243c5178d4fea4010800a1c228027a0ce98cebaa7018206f0038e0ace28a20304c0028304c049880a4040800a1c22041d1fc3245a1cb2f420060a0430800a1c2283c5189374ca8020800a1c27a112802eaac7a0debaa0284000003fce28a20442a306800283078009885a4040800a1c2d0af00602045d1c22408e282283c48f5c28fe2809082a8000800a1c4a6010800a1c5207c5189374cd283a0410800a1c074132200e4a9740be5a80281000003fce288204124306800223078009282a0010800a1c0d4802f420060aa050800a1c0e9887419206f005806800199999a220004c1e3a82a00e4ad743fef88ca82e28824305c002a305c049a82a0050800a1c02042d1c0700874079081b4816c0013362a085181e3ad2045242f00602a3c145a1cacaa020800a1c0a0400800a1c174117a0d2001e4a8eba90280000003fce2892040203068002070780091c0a2080800a1c1d081e280222f003c9084a2000800a1c0d0842040e28041f03a002208d281206f004458af004420c02ac1bbef00486600fe4a286f005c2a4a45f900000000258bc800258dc8044aaf00786700e10a6000ef644480068002cccccd2800741904c4e9a82a00e4ad743fef88ca82e28820715c002a315c049a88a0050800a1c07a07d088ba846d00f7827a089a84eaa0207c145a1caca04a0800a1c4247c3d0e5604a4400800a1c2d48478117a0d2002e8a8ebaa0280000003fce28a2040203078002070680091c0a4080800a1c2d082e280242f003c9081a4000800a1c0d0812040e28041f03a00246f004458af004424c02208d281206f005858af005820c1b1ef00486600f7806000e03444802440721945f20c00200a068010000000240004c2e5a82800e2ac723fef88c881e28822314c0028314c049881a0040800a1c07807d280b8826d00f5ec70089082e0a1247c65db22d1a4450800a1c0a2000800a1c0720a78142400e2aae9a80282000003fce288244222327800243268009481a0020800a1c2d2822003e2810680f80000004a806c00f5ea4480e48074190680015c28f6280004c4e9a82a00e4ad743fef88ca82e28824315c002a315c049a82a0050800a1c07a07d480ba846d00f5e87008d1fc100000009084e0a220030680300000002442a0080800a1c04a806c00f5e66000fe60448020407a1941f00c002008068010000000220004c1e3a82400eaaa7a3fef88c485e28820712c0024312c049488a0020800a1c0d1c0700874079081b4816d00eb982208e0a1243c65db22d12041a4060800a1c0a0400800a1c17a0a7c142001eaa8eda9243c8000eee80280000003fce2892040203078002070280091c0a2080800a1c1d0812200e281e480204141f03a002208d281206f003c58af003c20c024c1b5ef00446600eb9a6000de9c43ef007c2f4900702a3c8000eee424492e3c8000eee843f9000000002f490044224d2a6f003841ef00fc2f4800482f6f0100003cddef004cd9ef0050dbef0054202f0040a2400800a1c0222f0040d7c0a6410800a1c093c0ac4b0800a1c0d08da8490800a1c4a8000800a1c3243c5189374cd084a4000800a1c07c13740b2200eca9e5a80281000003fce288204124305800223078009282a0010800a1c0d480a6030800a1c0e9887c19206f004406800199999a220004c1e3a82600ecab7c3fef88c686e2882c303c0026303c049686a0030800a1c02046d1c0700876079081b6816c000f7651812c08263c145a1cace3ae2046a6020800a1c0a0400800a1c17c11740d2001eca8e5a90280000003fce2892040203058002070780091c0a2080800a1c1d0812200e281e480204141f04a002208d281206f003c58af003c20c024c1b5ef00486600feec286f005c2a4945f900000000258bc800258dc8044aaf00786700dd506000ebaa202f0054247c8000eee443ef007c2f4900702e3c8000eee82f4900442c3c145a1cac41ef00fcddef004c2f48004843f900000000d9ef0050222f00402f6f01000058d1af0038aa410800a1c0d7c0a6410800a1c09bc0ac4b0800a1c0282f0038d880a84d0800a1c3a6040800a1c22a3c5189374c2004d083aa000800a1c07a132200eaa97a0beba80281000003fce2882a3218002041223078009285a0010800a1c02045d1c0a4020800a1c0e988721906800199999a240004c2e5a82a00e2ad723fef88ca81e28822315c002a315c049a81a0050800a1c07a07d280ba826c0001d25182e5a9ac080800a1c0a2000800a1c074117a0d2200e4a9eba80281000003fce28820412230a8002070780091c1a0080800a1c0d280e281a6040800a1c2207c4c624dd3a0420800a1c07a0f2800eaaceba80284000003fce28820442830a8002070780091c4a0080800a1c0d8802f440060a4020800a1c0e9887819068002cccccd240004c2e5a82a00e8ad783fef88ca84e28820715c002a315c049a88a0050800a1c07a07d088ba826c0001d45182e5a8206f0060ac080800a1c2a0020800a1c278117a0d2002e8a8ebaa0280000003fce28a20402030a8002070780091c0a4080800a1c2d082e280242f003c9081a4000800a1c0d0812040e28041f03a002208d281206f005858af005820c0206f004458af004420c1b1ef00486700db30202f0054ddef004cd9ef0050222f0040d1af0038aa410800a1c0d7c0a6410800a1c09bc0ac4b0800a1c0282f0038d880a84d0800a1c3a6040800a1c22a3c5189374c2004d083aa000800a1c07a132200eaa97a0beba80281000003fce2882a3218002041223078009285a0010800a1c02045d1c0a4020800a1c0e988721906800199999a240004c2e5a82a00e2ad723fef88ca81e28822315c002a315c049a81a0050800a1c07a07d280ba826d00fe3270089082e0a1ac080800a1c0a2000800a1c074117a0d2200e4a9eba80281000003fce28820412230a8002070780091c1a0080800a1c0d280e281a6040800a1c2207c4c624dd3a0420800a1c07a0f2800eaaceba80284000003fce28820442830a8002070780091c4a0080800a1c0d8802f440060a4020800a1c0e9887819068002cccccd240004c2e5a82a00e8ad783fef88ca84e28820715c002a315c049a88a0050800a1c07a07d088ba826d00fe307a089a82eaa0206f0060ac080800a1c2a0020800a1c278117a0d2002e8a8ebaa0280000003fce28a20402030a8002070780091c0a4080800a1c2d082e280242f003c9081a4000800a1c0d0812040e28041f03a002208d281206f005858af005820c0206f004458af004420c1b1ef00486600fe2e6000d95841ef007c282f003824482f4800702a3c8000eee443f90000000041ef00fc2f4900382e3c8000eee82f480044ddef004cd9ef0050224dd8af0054202f00402f6f0100003ca2400800a1c0222f0040d7c0a6410800a1c093c0ac4b0800a1c0a8490800a1c22a42d084a4000800a1c32c3c4c624dd3ac030800a1c0740f2200e4a9e5a80281000003fce288204124305800223078009282a0010800a1c0d480a6030800a1c0e9887c19206f0038068002cccccd220004c1e3a82600ecab7c3fef88c686e2882c303c0026303c049686a0030800a1c02046d1c0700876079081b6816c00011651812c08263c145a1cace3ae2046a6020800a1c0a0400800a1c17c11740d2001eca8e5a90280000003fce2892040203058002070780091c0a2080800a1c1d0812200e281e480204141f0da002208d281206f003c58af003c20c024c1b5ef00446700fac0ddef004cd9ef0050d8af0054202f0040a2400800a1c0222f0040d7c0a6410800a1c093c0ac4b0800a1c0a8490800a1c22a42d084a4000800a1c32c3c4c624dd3ac030800a1c0740f2200e4a9e5a80281000003fce288204124305800223078009282a0010800a1c0d480a6030800a1c0e9887c19206f0038068002cccccd220004c1e3a82600ecab7c3fef88c686e2882c303c0026303c049686a0030800a1c02046d1c0700876079081b6816d00feee2208e0a1263c145a1cac2041a6020800a1c0a0400800a1c17c11740d2001eca8e5a90280000003fce2892040203058002070780091c0a2080800a1c1d0812200e281e480204141f0da002208d281206f003c58af003c20c024c1b5ef00446600fef06000f9aa2e2f00382c3c8000eee841ef007c45ef00fcddef004cd9ef0050deaf0054202f00402f4800702f6f010000582f4a004843f9000000002f480044aa400800a1c0222f0040d7c0a6410800a1c09bc0ac4b0800a1c02047d1c0a84d0800a1c3a6080800a1c2283c4c624dd3a8020800a1c07a0f2200eaa9eba8247c8000eee40281000003fce288283218002441223268009284a0010800a1c0d880a4020800a1c0e9887219068002cccccd240004c2e5a82a00e2ad723fef88ca81e28822315c002a315c049a81a0050800a1c07a07d280ba826c0001d05182e5a9247c145a1caca4440800a1c0a2000800a1c07211780d2400e2aae9a8247c8000eee40282000003fce288223228002442243268009481a0020800a1c0d280e281a6080800a1c02f4000382003d1fcf8000000068008000000a0080800a1c04a806d0001d22440781941f20c002008068010000000240004c2e5a82a00e8ad783fef88ca84e28820715c002a315c049a88a0050800a1c07a07d088ba826c0001d45182e5a8242f0038283c65db22d1a8020800a1c2a0020800a1c27a0a78142002eaa8e9aa2a3c8000eee40280000003fce28a2040203058002070680091c0a4080800a1c2d082e280242f003c9081a4000800a1c0d0812040e28041f03a00246f005858af005824c02208d281206f004458af004420c1b1ef00486700d502ddef004cd9ef0050deaf0054202f0040aa400800a1c0222f0040d7c0a6410800a1c09bc0ac4b0800a1c02047d1c0a84d0800a1c3a6080800a1c2283c4c624dd3a8020800a1c07a0f2200eaa9eba8247c8000eee40281000003fce288283218002441223268009284a0010800a1c0d880a4020800a1c0e9887219068002cccccd240004c2e5a82a00e2ad723fef88ca81e28822315c002a315c049a81a0050800a1c07a07d280ba826d00fe3470089082e0a1247c145a1caca4440800a1c0a2000800a1c07211780d2400e2aae9a8247c8000eee40282000003fce288223228002442243268009481a0020800a1c0d280e281a6080800a1c02f4000382003d1fcf8000000068008000000a0080800a1c04a806c00fe3244802440781941f20c002008068010000000240004c2e5a82a00e8ad783fef88ca84e28820715c002a315c049a88a0050800a1c07a07d088ba826d00fe307a089a82eaa0242f0038283c65db22d1a8020800a1c2a0020800a1c27a0a78142002eaa8e9aa2a3c8000eee40280000003fce28a2040203058002070680091c0a4080800a1c2d082e280242f003c9081a4000800a1c0d0812040e28041f03a00246f005858af005824c02208d281206f004458af004420c1b1ef00486600fe2e6000d32a2a2f00382e3c3d0e560443ef00fc2f4900442f4a003cddef004cd9ef005043f900000000daaf0054246f0040aa4a0800a1c0d7c0a64a0800a1c09bc0ac4b0800a1c02445d5c0a84d0800a1c420040680f80000004a806d0001e0e48074197c3f0680015c28f6220004c1e3a82600e4abef88c686e28824313c0026313c049682a0030800a1c0d4807007b0816c0001e251812004d5fc10000000e3aa068030000000a00a0800a1c04a806d0000e4068002cccccd26007c1904c3e7a82200eca97c3fef88cc81e28822316c0024716c0495c1a00a0800a1c0d2807007b0836c0000e65183e7a9263c145a1caca6020800a1c2ae010800a1c07c11d0822400ecaa720de3a8247c8000eee40282000003fce28822322800247c8000eee8243228009481a0020800a1c0d2802001e280e481244045f24a00200ad080246f003c58af003c24c120c0b1ef00446700d1dcddef004cd9ef0050daaf0054246f0040aa4a0800a1c0d7c0a64a0800a1c09bc0ac4b0800a1c02445d5c0a84d0800a1c420040680f80000004a806c00fed0600000aa4480068002cccccd26007c1904c3e7a82200eca97c3fef88cc81e28822316c0024716c0495c1a00a0800a1c0d2807007b0836d00ff1e70089083e0a1263c145a1caca6020800a1c2ae010800a1c07c11d0822400ecaa720de3a8247c8000eee40282000003fce28822322800247c8000eee8243228009481a0020800a1c0d2802001e280e481244045f24a00200ad080246f003c58af003c24c120c0b1ef00446600ff1c6000d0f24480e48074197c3f0680015c28f6220004c1e3a82600e4abef88c686e28824313c0026313c049682a0030800a1c0d4807007b0816d00fe227008d5fc100000009081e0a22004068030000000a00a0800a1c04a806c00fe206000fefe41ef007c2a2f003822482f48007041ef00fcddef004cd9ef00502f48003cdaaf0054246f01002e2f0040aa470800a1c0d7c0a6470800a1c09bc0ac4b0800a1c1a84d0800a1c620060680200000002800ee840c804000007f6f000114283c008000002005d081727e4841068020000000a2000800a1c30c83003f00006d000116263c003effff20032204484048c0484148c1740fe5acc0fc008402847fff8000d08171c0d0802040d1fc000000007168000275680004735094809480d48148424242a8020800a1c29081484042402f4200407368010a7568010c948194812f40003871680108d4809280202f003848424242d0af0040a8020800a1c2780f48414241e9abd28202837fff80009280a6010800a1c1d081e9882040e28041f06a0024c02208d28122c1b3ef003c6700cf66ddef004cd9ef0050daaf0054aa470800a1c0d7c0a6470800a1c09bc0ac4b0800a1c1a84d0800a1c620060680200000002800ee840c804000007f6e00fef04a846c00fef02005d081727e48414284068020000000a2000800a1c30c83003f00006c00feee4a836c00feee428320032204484048c0484148c1740fe5acc0fc008402847fff8000d08171c0d0802040d1fc000000007168000275680004735094809480d48148424242a8020800a1c29081484042402f4200407368010a7568010c948194812f40003871680108d4809280202f003848424242d0af0040a8020800a1c2780f48414241e9abd28202837fff80009280a6010800a1c1d081e9882040e28041f06a0024c02208d28122c1b3ef003c6600feec6000ce4c2208e0a120416000eccc2208e0a1263c145a1cac2041a6020800a1c0a0400800a1c17c11740d2001eca8e5a90280000003fce2892040203058002070780091c0a2080800a1c1d0812200e281e480204141f04a002208d281206f003c58af003c20c024c1b5ef00486600ef7a6000f08c41ef007c2e2f003824482f48007041ef00fcddef004cd9ef00502f480048deaf0054202f00402f6f0100004443f900000000aa400800a1c0d7c0222f0040a6410800a1c09bc0ac4b0800a1c0d0872f400038a84d0800a1c620060680f80000004a806d000222e4807419783f0680015c28f6220004c1e3a82600e4abef88c684e28824313c0026313c049682a0030800a1c07a07d480ba816c0002245181e3aa202f00382206068010000000068130000000a2000800a1c04a806d000226068002cccccd2600721904c3e7a87a3f2800e2acef88c885e28822314c0028314c049881a0040800a1c0d2807007b0836c0002285183e7a9263c145a1caca6020800a1c2283c3d0e5604a8010800a1c07a11d0822200eaa9740de5a8207c8000eee40281000003fce2882a301800207c8000eee8223018009285a0010800a1c0da8020060680200000002800e285ee840c804000007f6f00022a283c00800000206f0038d1fc20000000707e4840a0080800a1c30c83003f00006d00022c263c003effff20032204484048c0484148c1740fe5acc0fc008402847fff8000d08171c0d0802040d1fc000000007168000275680004735094809480d48148424242a8020800a1c29081484042402f4200387368010a7568010c948194812f40005871680108d4809280202f005848424242d0af0038a8020800a1c2780f48414241e9abd28202837fff80009280a6010800a1c1d081e988222f003c9085a2000800a1c0d0852040e28041f06a002208d281206f004458af004420c024c1b5ef00486700cb9addef004cd9ef0050deaf0054202f0040aa400800a1c0222f0040d7c0a6410800a1c09bc0ac4b0800a1c0d0872f400038a84d0800a1c620060680f80000004a806c00fde24480e4807419783f0680015c28f6220004c1e3a82600e4abef88c684e28824313c0026313c049682a0030800a1c07a07d480ba816d00fde070089081e0a2202f00382206068010000000068130000000a2000800a1c04a806c00fdde4480068002cccccd2600721904c3e7a87a3f2800e2acef88c885e28822314c0028314c049881a0040800a1c0d2807007b0836d00fddc70089083e0a1263c145a1caca6020800a1c2283c3d0e5604a8010800a1c07a11d0822200eaa9740de5a8207c8000eee40281000003fce2882a301800207c8000eee8223018009285a0010800a1c0da8020060680200000002800e285ee840c804000007f6e00fdda4a846c00fdda206f00384284707e4840d1fc20000000a0080800a1c30c83003f00006c00fdd84a836c00fdd8428320032204484048c0484148c1740fe5acc0fc008402847fff8000d08171c0d0802040d1fc000000007168000275680004735094809480d48148424242a8020800a1c29081484042402f4200387368010a7568010c948194812f40005871680108d4809280202f005848424242d0af0038a8020800a1c2780f48414241e9abd28202837fff80009280a6010800a1c1d081e988222f003c9085a2000800a1c0d0852040e28041f06a002208d281206f004458af004420c024c1b5ef00486600fdd66000c96a41ef007c202f005424482f48007041ef00fcddef004cd9ef00502f480048222f00402f6f01000044d1af0038aa410800a1c0d7c0a6410800a1c09bc0ac4b0800a1c1a84d0800a1c520050680200000002400ee820c804000007f6f0001bc243c00800000226f0038d3c1767e4843d3fc20000000a6090800a1c40c84003f00006d0001be283c003effff20042c02484048c0484648c67e0fefaac0fc008402827fff8000d08671c0d0802040d1fc000000007168000277680004735096809680d68148434243a4030800a1c39081484042402f4300587368010a7768010c7f68010896819681d68748434243d0af0058a4030800a1c392877e0f48414241efacd28302847fff80009280a8010800a1c1d081e988207c007e0000a0490800a1c70c87003f00006d0001c02e3c003effff2207484148c1c2fc0084d28673c1d2812041d1fc000000007368000279680004775098819881d88348444244a4040800a1c49283484142417768010a7d680108d2847968010c98839883d88648444244a4040800a1c29686780f48434243e9afd68202877fff80009681ae030800a1c2d282e9892c2f003c9280ac010800a1c1d0812040e28041f05a00226f004458af004422c02208d28124c1b5ef00486700c798202f0054ddef004cd9ef0050222f0040d1af0038aa410800a1c0d7c0a6410800a1c09bc0ac4b0800a1c1a84d0800a1c520050680200000002400ee820c804000007f6e00fe484a826c00fe48226f0038d3c1767e48434282d3fc20000000a6090800a1c40c84003f00006c00fe464a846c00fe46428420042c02484048c0484648c67e0fefaac0fc008402827fff8000d08671c0d0802040d1fc000000007168000277680004735096809680d68148434243a4030800a1c39081484042402f4300587368010a7768010c7f68010896819681d68748434243d0af0058a4030800a1c392877e0f48414241efacd28302847fff80009280a8010800a1c1d081e988207c007e0000a0490800a1c70c87003f00006c00fe444a876c00fe4442872207484148c1c2fc0084d28673c1d2812041d1fc000000007368000279680004775098819881d88348444244a4040800a1c49283484142417768010a7d680108d2847968010c98839883d88648444244a4040800a1c29686780f48434243e9afd68202877fff80009681ae030800a1c2d282e9892c2f003c9280ac010800a1c1d0812040e28041f05a00226f004458af004422c02208d28124c1b5ef00486600fe426000c5d47fffffff7e07e07e7c1f07c27a44c6b07878787876b981db7507507573615a2471c71c7270381c0e6eb3e4536d3a06d46bca1af36a63bd826906906967b23a54666666666522c3f363e7063e62b2e43e61861862606060605f417d065e2932065d1745d15c0b81705b05b05b5a05a05a590b216458160581572620ae563b48c25555555554741fac5397829d52bf5a8151eb851f511be196505050504f88b2f44ec4ec4f4e04e04e4d4873ed4c8f8d294bda12f74b27ed364a7904a849cd42e249249249487ede0547dc11f7473c1ab7469ee58446046046456c797e44d720454444444443b3d5b04325c53f429a042a421084214189374c4104104140810204400000000000000005fd16180b7053a5106ac6c314facabe192c8b461d0a6ad0209d535023ecf66b270000f229dc448b2c86d9932f043aef31585cfa3386c09335928300377e6b46394cf5683b005bf43c9aa01a3e1d909f3f8acfce40e3d89a422a030c435e8818448284f64596fe10469ce18a4795098648803e1b495f37104a329d6b4afb0ccc4bb914a44c6d394a4d17f4f14db9b8844e52ec6e4ee3f1494f6d207a4feeccc7506942d050dcc9895149a29f51b00ad752103a64526a653552bebb37530d689953569601539a68c053d90302541283f6544707f55476a8a254a17d0954c799b754e910d65505f23e551e4b875532281b5541913d554c8e19555323c755555555555323c7554c8e195541913d5532281b551e4b875505f23e54e910d654c799b754a17d095476a8a2544707f5541283f653d90302539a68c053569601530d689952bebb37526a653552103a6451b00ad75149a29f50dcc989506942d04feeccc74f6d207a4ee3f1494e52ec6e4db9b8844d17f4f14c6d394a4bb914a44afb0ccc4a329d6b495f371048803e1b47950986469ce18a4596fe10448284f6435e8818422a030c40e3d89a3f8acfce3e1d909f3c9aa01a3b005bf4394cf568377e6b46359283003386c09331585cfa2f043aef2c86d99329dc448b270000f223ecf66b209d53501d0a6ad0192c8b4614facabe106ac6c30b7053a505fd161800000000fa02e9e8f48fac5bef95393deb053542e6d374bae2f59530df62acb0dc130995d8ffff0ed623bb75d379266dd0fbc511cea7a306cc793f6dca6d7d00c88194bac6b30a98c4ffa40cc3655fe6c1e26f61c0753032bf1c2766bdd5fcf4bca177e8bb7d7b0aba6901f0b9631e76b86af67ab77fc1e5b6a0c8f0b5cd6295b504f334b446eb5cb392c6b6b2e80b0fb246477cb1ad1392b11c0eb7b092df86b0113339af96bd30af233677aeb65d61ae4ff529adefc59cad959acbad4144c9acf29767aca969ffac659740ac26fcfeabed7c0aabb8f80bab89575eab5e82f7ab386649ab16ef2aaafa0dc2aae1b479aacdd7e5aabe6ec3aab371e7aaacdc39aaaaaaabaaacdc39aab371e7aabe6ec3aacdd7e5aae1b479aafa0dc2ab16ef2aab386649ab5e82f7ab89575eabb8f80babed7c0aac26fcfeac659740aca969ffacf29767ad4144c9ad959acbadefc59cae4ff529aeb65d61af233677af96bd30b0113339b092df86b11c0eb7b1ad1392b246477cb2e80b0fb392c6b6b446eb5cb504f334b5cd6295b6a0c8f0b77fc1e5b86af67ab9631e76ba6901f0bb7d7b0abca177e8bdd5fcf4bf1c2766c0753032c1e26f61c3655fe6c4ffa40cc6b30a98c88194baca6d7d00cc793f6dcea7a306d0fbc511d379266dd623bb75d8ffff0edc130995df62acb0e2f59530e6d374baeb053542ef95393df48fac5bfa02e9e80000000040000000402c6be94058f6a84085a05140b268fa40df50b8410c57a241397dcc4166c34c4194283941c1aca741ef50ae421d1462424af7da4278fb2b42a71e6c42d561b44303c518433248ae4360ec8d438fb0cb43be957f43ed9ac0441cc0a3444c0740447b6ead44aaf70244daa054450a6abb453a564d456a6323459a915245cae0f245fb521a462be4e2465c9961468d6fae46be67e046ef82104720be5547521cc647839d7b47b5408c47e706114818ee22484af8d6487d264648af768a48e1e9ba49147fee4947393f497a15c449ad159849e038d04a137f884a46e9d64a7a77d44aae299b4ae1ff434b15f8e64b4a169c4b7e587e4bb2bea54be7492b4c1bf8294c50cbb84c85c3f14cbae0ef4cf022ca4d25899c4d5b157e4d90c68b4dc69cdd4dfc988c4e32b9b44e69006e4e9f6cd44ed5ff004f0cb70c4f4395144f7a99304fb1c37c4fe9141350208b0e50582888508fec9c50c7d76550ffe8fe513821825170810b51a907b451e1b59a521a8ad752538786528cabc352c5f7aa52ff6b55533906e05372ca6853acb60753e6c9da542105fd545b6a8b5495f7a154d0ad5a550b8bd4554693295581c37855bd1cdb55f89f7056344b52567020a056ac1f7556e847ef57249a2957611642579dbc5757da8c83581786e65854ab9b5891fac158cf7474590d18d3594ae7fb5988e20959c7071c5a0557515a43d2c65a82799a5ac14bea5b0049d45b3f73775b7ec8f25bbe4a615bfdf7e55c3dd19c5c7dd7a45cbe0a1c5cfe69235d3ef4d75d7fad595dc092c75e01a53f5e42e4e35e8451d05ec5ec265f07b4055f49a98c5f8bccdb5fce1e1260109d5160534ab76096266560d9307b611c6919615fd05e61a3666d61e72b65622b1f66626f429262b3950962f816eb633cc85b6381a97863c6ba64640bfb4164516c2e64970d4f64dcdec36522e0ad6569132f65af766a65f60a7f663ccf926683c5c366caed356712460b6759d06567a18c6867e97a34683199ed6879ebb668c26fb1690b260169540ec9699d2a2c69e6784d6a2ff94f6a79ad566ac394856b0daeff6b57fce96ba27e656bed33996c381ca66c8339b26cce8ae16d1a10576d65ca386db1b8a86dfddbcc6e4a33c96e96c0c36ee382de6f307a416f7da7106fcb096f7018a18570666f7670b473687102ad8071511de4719fc4b971eea226723db650728d015d72dc8374732c3cba737c2d5573cc556d741cb528746d4cac74be1c20750f23ab7560637475b1dba276038c5b765575c876a7980f76f9f359774c87cc779f559077f25cce78459dac7899185478ecccec7940bb9e7994e49279e947ef7a3de5df7a92be8b7ae7d21a7b3d20b67b92aa887be86fba7c3e70737c94acde7ceb25237d41d96e7d98c9e67deff6b67e4760097e9f06067ef6e8da7f4f08ae7fa765ad80000000",
    "relocs": [
     [
      640,
      "bss",
      50688
     ],
     [
      646,
      "bss",
      50808
     ],
     [
      672,
      "bss",
      50808
     ],
     [
      690,
      "bss",
      50808
     ],
     [
      762,
      "bss",
      50808
     ],
     [
      792,
      "bss",
      50808
     ],
     [
      1112,
      "bss",
      50808
     ],
     [
      1162,
      "bss",
      50808
     ],
     [
      1188,
      "bss",
      50808
     ],
     [
      1366,
      "code",
      16892
     ],
     [
      1838,
      "bss",
      0
     ],
     [
      2004,
      "bss",
      50808
     ],
     [
      2298,
      "code",
      17152
     ],
     [
      2768,
      "bss",
      0
     ],
     [
      2958,
      "bss",
      0
     ],
     [
      4182,
      "code",
      17152
     ],
     [
      5076,
      "code",
      16892
     ],
     [
      5424,
      "code",
      18180
     ],
     [
      5546,
      "bss",
      50808
     ],
     [
      6034,
      "bss",
      16896
     ],
     [
      6184,
      "bss",
      0
     ],
     [
      6480,
      "bss",
      16896
     ],
     [
      6632,
      "bss",
      0
     ],
     [
      6996,
      "bss",
      33792
     ],
     [
      7274,
      "bss",
      33792
     ],
     [
      7474,
      "code",
      16892
     ],
     [
      8058,
      "bss",
      50808
     ],
     [
      8212,
      "bss",
      50808
     ],
     [
      8516,
      "bss",
      0
     ],
     [
      8794,
      "bss",
      0
     ],
     [
      8980,
      "code",
      17152
     ],
     [
      9428,
      "code",
      16892
     ],
     [
      9454,
      "code",
      17152
     ],
     [
      9932,
      "bss",
      50808
     ],
     [
      10572,
      "code",
      16892
     ],
     [
      10886,
      "bss",
      50808
     ],
     [
      10958,
      "code",
      16892
     ],
     [
      11918,
      "code",
      16892
     ],
     [
      12552,
      "code",
      16892
     ],
     [
      13510,
      "code",
      16892
     ],
     [
      14308,
      "bss",
      16896
     ],
     [
      14586,
      "bss",
      16896
     ],
     [
      14882,
      "code",
      16892
     ],
     [
      15258,
      "bss",
      33792
     ],
     [
      15814,
      "bss",
      33792
     ],
     [
      16148,
      "bss",
      33792
     ],
     [
      16298,
      "bss",
      16896
     ],
     [
      16594,
      "bss",
      33792
     ],
     [
      16746,
      "bss",
      16896
     ],
     [
      54,
      "bss",
      50808
     ],
     [
      276,
      "bss",
      50688
     ],
     [
      568,
      "code",
      596
     ]
    ],
    "symbols": {
     "terra_update": [
      "code",
      0
     ],
     "terra_render": [
      "code",
      468
     ]
    },
    "bss": 51072,
    "far": "afb4af1eaebaae87ae87aebaaf1eafb4b07cb175b29eb3f7b57fb735b918bb26bd5fbfc1c24ac4fac7cecac5cdddd113d466d7d5db5cdefae2ace670ea44ee25f211f606fa01fe00020005ff09fa0def11db15bc19901d54210624a4282b2b9a2eed3223353b38323b063db6403f42a144da46e848cb4a814c094d624e8b4f84504c50e2514651795179514650e2504c4f844e8b4d624c094a8148cb46e844da42a1403f3db63b063832353b32232eed2b9a282b24a421061d54199015bc11db0def09fa05ff0200fe00fa01f606f211ee25ea44e670e2acdefadb5cd7d5d466d113cdddcac5c7cec4fac24abfc1bd5fbb26b918b735b57fb3f7b29eb175b07cafb4af1eaebaae87d99fd876d7aed74ad74ad7aed876d99fdb27dd0adf43e1cce4a1e7b8eb0cee93f245f619fa05fe00020005fb09e70dbb116d14f418481b5f1e3420bd22f624d92661278a285228b628b62852278a266124d922f620bd1e341b5f184814f4116d0dbb09e705fb0200fe00fa05f619f245ee93eb0ce7b8e4a1e1ccdf43dd0adb27d99fd876d7aed74ad74ad7aed876d99fdb27dd0adf43e1cce4a1e7b8eb0cee93f245f619fa05fe00020005fb09e70dbb116d14f418481b5f1e3420bd22f624d92661278a285228b628b62852278a266124d922f620bd1e341b5f184814f4116d0dbb09e705fb0200fe00fa05f619f245ee93eb0ce7b8e4a1e1ccdf43dd0adb27d99fd876d7aed74ae858e6a2e579e4e3e4e3e579e6a2e858ea91ed41f058f3c7f779fb5aff55035407400b040e8c11c2149616f818db1a341afc1b2e1ac919d11849163a13b110ba0d6709c905f50200fe00fa0bf637f299ef46ec4fe9c6e7b7e62fe537e4d2e504e5cce725e908eb6aee3ef174f4fcf8c0fcac00ab04a608870c390fa812bf156f17a8195e1a871b1d1b1d1a87195e17a8156f12bf0fa80c39088704a600abfcacf8c0f4fcf174ee3eeb6ae908e725e5cce504e4d2e537e62fe7b7e9c6ec4fef46f299f637fa0bfe00020005f509c90d6710ba13b1163a184919d11ac91b2e1afc1a3418db16f8149611c20e8c0b0407400354ff55fb5af779f3c7f058ed41ea91e858e6a2e579e4e3f03aee01ec79ebb2ebb2ec79ee01f03af30ef662fa14fe00020005ec099e0cf20fc611ff1387144e144e138711ff0fc60cf2099e05ec0200fe00fa14f662f30ef03aee01ec79ebb2ebb2ec79ee01f03af30ef662fa14fe00020005ec099e0cf20fc611ff1387144e144e138711ff0fc60cf2099e05ec0200fe00fa14f662f30ef03aee01ec79ebb2ebb2ec79ee01f03af30ef662fa14fe00020005ec099e0cf20fc611ff1387144e144e138711ff0fc60cf2099e05ec0200fe00fa14f662f30ef03aee01ec79ebb2ebb2ec79ee01f03af30ef662fa14fe00020005ec099e0cf20fc611ff1387144e144e138711ff0fc60cf2099e05ec0200fe00fa14f662f30ef03aee01ec79ebb2f554f2a4f0c2efc9efc9f0c2f2a4f554f8a7fc6c0067045c080e0b440dce0f84104b10190ef00ce10a0d069f02cbfeccfae0f742f42bf1c9f041efabf00ff168f3a1f698fa1ffe00020005e109680c5f0e980ff110550fbf0e370bd508be05200134fd35f961f5f3f31ff110efe7efb5f07cf232f4bcf7f2fba4ff99039407590aac0d5c0f3e103710370f3e0d5c0aac07590394ff99fba4f7f2f4bcf232f07cefb5efe7f110f31ff5f3f961fd350134052008be0bd50e370fbf10550ff10e980c5f096805e10200fe00fa1ff698f3a1f168f00fefabf041f1c9f42bf742fae0fecc02cb069f0a0d0ce10ef01019104b0f840dce0b44080e045c0067fc6cf8a7f554f2a4f0c2efc9f8fef5e7f3aef284f284f3aef5e7f8fefcb000ab0498081f0af30cd50d9d0d390bb1092705d40200fe00fa2cf6d9f44ff2c7f263f32bf50df7e1fb68ff55035007020a190c520d7c0d7c0c520a1907020350ff55fb68f7e1f50df32bf263f2c7f44ff6d9fa2cfe00020005d409270bb10d390d9d0cd50af3081f049800abfcb0f8fef5e7f3aef284f284f3aef5e7f8fefcb000ab0498081f0af30cd50d9d0d390bb1092705d40200fe00fa2cf6d9f44ff2c7f263f32bf50df7e1fb68ff55035007020a190c520d7c0d7c0c520a1907020350ff55fb68f7e1f50df32bf263f2c7f44ff6d9fa2cfe00020005d409270bb10d390d9d0cd50af3081f049800abfcb0f8fef5e7f3aef284fbcaf85cf5d2f479f479f5d2f85cfbcaffb703ab073309e20b6a0b9c0a73081104be00dcfce1f944f66ff4baf455f54ef787fabdfe910290064209390b1c0bb20aea08dc05c40200fe00fa3cf724f516f44ef4e4f6c7f9befd70016f054308790ab20bab0b46099106bc031fff24fb42f7eff58df464f496f61ef8cdfc550049043607a40a2e0b870b870a2e07a404360049fc55f8cdf61ef496f464f58df7effb42ff24031f06bc09910b460bab0ab208790543016ffd70f9bef6c7f4e4f44ef516f724fa3cfe00020005c408dc0aea0bb20b1c093906420290fe91fabdf787f54ef455f4baf66ff944fce100dc04be08110a730b9c0b6a09e2073303abffb7fbcaf85cf5d2f479fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2d99fd876d7aed74ad74ad7aed876d99fdb27dd0adf43e1cce4a1e7b8eb0cee93f245f619fa05fe00020005fb09e70dbb116d14f418481b5f1e3420bd22f624d92661278a285228b628b62852278a266124d922f620bd1e341b5f184814f4116d0dbb09e705fb0200fe00fa05f619f245ee93eb0ce7b8e4a1e1ccdf43dd0adb27d99fd876d7aed74ad74ad7aed876d99fdb27dd0adf43e1cce4a1e7b8eb0cee93f245f619fa05fe00020005fb09e70dbb116d14f418481b5f1e3420bd22f624d92661278a285228b628b62852278a266124d922f620bd1e341b5f184814f4116d0dbb09e705fb0200fe00fa05f619f245ee93eb0ce7b8e4a1e1ccdf43dd0adb27d99fd876d7aed74ae858e6a2e579e4e3e4e3e579e6a2e858ea91ed41f058f3c7f779fb5aff55035407400b040e8c11c2149616f818db1a341afc1b2e1ac919d11849163a13b110ba0d6709c905f50200fe00fa0bf637f299ef46ec4fe9c6e7b7e62fe537e4d2e504e5cce725e908eb6aee3ef174f4fcf8c0fcac00ab04a608870c390fa812bf156f17a8195e1a871b1d1b1d1a87195e17a8156f12bf0fa80c39088704a600abfcacf8c0f4fcf174ee3eeb6ae908e725e5cce504e4d2e537e62fe7b7e9c6ec4fef46f299f637fa0bfe00020005f509c90d6710ba13b1163a184919d11ac91b2e1afc1a3418db16f8149611c20e8c0b0407400354ff55fb5af779f3c7f058ed41ea91e858e6a2e579e4e3f03aee01ec79ebb2ebb2ec79ee01f03af30ef662fa14fe00020005ec099e0cf20fc611ff1387144e144e138711ff0fc60cf2099e05ec0200fe00fa14f662f30ef03aee01ec79ebb2ebb2ec79ee01f03af30ef662fa14fe00020005ec099e0cf20fc611ff1387144e144e138711ff0fc60cf2099e05ec0200fe00fa14f662f30ef03aee01ec79ebb2ebb2ec79ee01f03af30ef662fa14fe00020005ec099e0cf20fc611ff1387144e144e138711ff0fc60cf2099e05ec0200fe00fa14f662f30ef03aee01ec79ebb2ebb2ec79ee01f03af30ef662fa14fe00020005ec099e0cf20fc611ff1387144e144e138711ff0fc60cf2099e05ec0200fe00fa14f662f30ef03aee01ec79ebb2f8fef5e7f3aef284f284f3aef5e7f8fefcb000ab0498081f0af30cd50d9d0d390bb1092705d40200fe00fa2cf6d9f44ff2c7f263f32bf50df7e1fb68ff55035007020a190c520d7c0d7c0c520a1907020350ff55fb68f7e1f50df32bf263f2c7f44ff6d9fa2cfe00020005d409270bb10d390d9d0cd50af3081f049800abfcb0f8fef5e7f3aef284f284f3aef5e7f8fefcb000ab0498081f0af30cd50d9d0d390bb1092705d40200fe00fa2cf6d9f44ff2c7f263f32bf50df7e1fb68ff55035007020a190c520d7c0d7c0c520a1907020350ff55fb68f7e1f50df32bf263f2c7f44ff6d9fa2cfe00020005d409270bb10d390d9d0cd50af3081f049800abfcb0f8fef5e7f3aef284fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2f5f2f77afa4efe00020005b208860a0e0a0e088605b20200fe00fa4ef77af5f2033fff53fba1f968f968fba1ff53033f061406db05530200fe00faadf925f9ecfcc100ad045f06980698045f00adfcc1f9ecf925faadfe000200055306db0614033fff53fba1f968f968fba1ff53033f061406db05530200fe00faadf925f9ecfcc100ad045f06980698045f00adfcc1f9ecf925faadfe000200055306db0614033fff53fba1f968f968fba1ff53033f061406db05530200fe00faadf925f9ecfcc100ad045f06980698045f00adfcc1f9ecf925faadfe000200055306db0614033fff53fba1f968f968fba1ff53033f061406db05530200fe00faadf925f9ecfcc100ad045f06980698045f00adfcc1f9ecf925faadfe000200055306db0614033fff53fba1f96804d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2cfb2cfe00020004d404d40200fe00fb2c0200038800b4fd02fd0200b403880200fe00fc78ff4c02fe02feff4cfc78fe000200038800b4fd02fd0200b403880200fe00fc78ff4c02fe02feff4cfc78fe000200038800b4fd02fd0200b403880200fe00fc78ff4c02fe02feff4cfc78fe000200038800b4fd02fd0200b403880200fe00fc78ff4c02fe02feff4cfc78fe000200038800b4fd02fd0200b403880200fe00fc78ff4c02fe02feff4cfc78fe000200038800b4fd02fd0200b403880200fe00fc78ff4c02fe02feff4cfc78fe000200038800b4fd02fd0200b403880200fe00fc78ff4c02fe02feff4cfc78fe000200038800b4fd02fd0200b403880200fe00fc78ff4c02fe02feff4cfc78fe000200038800b4fd02fba6f7def4ecf34ff34ff4ecf7defba6ffa6034205ff079407fa0760061f049b03340227018e015801580154011a0087ff96fe5ffd0bfbcefad8fa4cfa39fa9dfb69fc84fdd5ff4400bc022b037c0497056305c705b40528043202f501a1006aff79fee6feacfea8fea8fe72fdd9fcccfb65f9e1f8a0f806f86cfa01fcbe005a045a08220b140cb10cb10b140822045a005afcbefa01f86cf806f8a0f9e1fb65fcccfdd9fe72fea8fea8feacfee6ff79006a01a102f50432052805b405c705630497037c022b00bcff44fdd5fc84fb69fa9dfa39fa4cfad8fbcefd0bfe5fff960087011a015401580158018e02270334049b061f076007fa079405ff0342ffa6fba6f7def4ecf34ffffffbfff89cf6acf6acf89cfbffffff03ab0638073806ac04f902be009eff11fe44fe1ffe55fe8ffe8ffe44fdcbfd64fd52fdc1feb7000f018802d803c1041d03e6032b020e00b6ff4afdf2fcd5fc1afbe3fc3ffd28fe78fff10149023f02ae029c023501bc0171017101ab01e101bc00efff62fd42fb07f954f8c8f9c8fc5500010401076409540954076404010001fc55f9c8f8c8f954fb07fd42ff6200ef01bc01e101ab0171017101bc0235029c02ae023f0149fff1fe78fd28fc3ffbe3fc1afcd5fdf2ff4a00b6020e032b03e6041d03c102d80188000ffeb7fdc1fd52fd64fdcbfe44fe8ffe8ffe55fe1ffe44ff11009e02be04f906ac0738063803abfffffbfff89cf6ac0291fe91fac6f879f879fac6fe910291057c067e058303230059fe19fcf5fcf4fdb3fea1ff4aff8aff8aff9c000400ce01c4028802bf023d0115ff96fe25fd21fcc3fd16fdffff4a00b6020102ea033d02df01db006afeebfdc3fd41fd78fe3cff32fffc00640076007600b6015f024d030c030b01e7ffa7fcddfa7df982fa84fd6f016f053a07870787053a016ffd6ffa84f982fa7dfcddffa701e7030b030c024d015f00b6007600760064fffcff32fe3cfd78fd41fdc3feeb006a01db02df033d02ea020100b6ff4afdfffd16fcc3fd21fe25ff960115023d02bf028801c400ce0004ff9cff8aff8aff4afea1fdb3fcf4fcf5fe19005903230583067e057c0291fe91fac6f879048a01a9fda9fad4fad4fda901a9048a04c90284ff41fce4fc86fdecffee015601a0011e0080003a003a001bff99fedffe70fec0ffd3012a020e02010104ff91fe54fdd2fe37ff5100af01c9022e01ac006ffefcfdfffdf2fed6002d0140019001210067ffe5ffc6ffc6ff80fee2fe60feaa00120214037a031c00bffd7cfb37fb76fe570257052c052c0257fe57fb76fb37fd7c00bf031c037a02140012feaafe60fee2ff80ffc6ffc6ffe50067012101900140002dfed6fdf2fdfffefc006f01ac022e01c900afff51fe37fdd2fe54ff9101040201020e012affd3fec0fe70fedfff99001b003a003a0080011e01a00156ffeefdecfc86fce4ff41028404c9048a01a9fda9fad4045a0358ff58fbc4fbc4ff580358045a01bcfe01fc58fdcc00a8026101ea003fff0bfefeff89ffdaffda0008009e011900c5ff9dfe84fe7affaa012e01d9012cffaefe72fe4aff4500bb01b6018e0052fed4fe27fed200560186017c0063ff3bfee7ff62fff8002600260077010200f5ffc1fe16fd9fff58023403a801fffe44fba6fca800a8043c043c00a8fca8fba6fe4401ff03a80234ff58fd9ffe16ffc100f50102007700260026fff8ff62fee7ff3b0063017c01860056fed2fe27fed40052018e01b600bbff45fe4afe72ffae012c01d9012effaafe7afe84ff9d00c50119009e0008ffdaffdaff89fefeff0b003f01ea026100a8fdccfc58fe0101bc045a0358ff58fbc4fff50317016efd6efd6e016e0317fff5fd25fedb020201c7ff16fe43fffd01300078ff8aff9effeeffee002d00900026ff38ff500091011f0002fed1ff5100c90124fff0fedaff5000b001260010fedcff3700af012ffffefee1ff6f00b000c8ffdaff70ffd30012001200620076ff88fed0000301bd00eafe39fdfe012502db000bfce9fe9202920292fe92fce9000b02db0125fdfefe3900ea01bd0003fed0ff880076006200120012ffd3ff70ffda00c800b0ff6ffee1fffe012f00afff37fedc0010012600b0ff50fedafff0012400c9ff51fed10002011f0091ff50ff3800260090002dffeeffeeff9eff8a00780130fffdfe43ff1601c70202fedbfd25fff50317016efd6efd8e00e10249fe49fe49024900e1fd8e00000230ff4efe61010d00f4fef7ff9c00bc0013ffaefff5fff5003d003cff78ffc700ca000eff12002d00f1ff9eff22008700c4ff63ff5200ae009dff3cff7900de0062ff0fffd300eefff2ff3600390088ffc4ffc3000b000b0052ffedff4400640109ff0cfef3019f00b2fdd000000272ff1ffdb701b701b7fdb7ff1f02720000fdd000b2019ffef3ff0c01090064ff44ffed0052000b000bffc3ffc400880039ff36fff200eeffd3ff0f006200deff79ff3c009d00aeff52ff6300c40087ff22ff9e00f1002dff12000e00caffc7ff78003c003dfff5fff5ffae001300bcff9cfef700f4010dfe61ff4e02300000fd8e00e10249fe4901cefdce01c8ff51ff5101c8fdce01ceff33ff9f0145fe6d0145ff6affe10091ff5e006affe0fff9fff90038ffa3004ffffbff9d00b4ff4300700015ff6b00d1ff550033005bff4600baffa5ffcd00abff2f0095ffebff9000bdff4c00630005ffb1005dffc8000700070020ff9600a2ff6f001f0096febb0193febb006100cdfe320232fe3800af00affe380232fe3200cd0061febb0193febb0096001fff6f00a2ff96002000070007ffc8005dffb100050063ff4c00bdff90ffeb0095ff2f00abffcdffa500baff46005b0033ff5500d1ff6b00150070ff4300b4ff9dfffb004fffa30038fff9fff9ffe0006aff5e0091ffe1ff6a0145fe6d0145ff9fff3301cefdce01c8ff51bc94bb96baebba96ba96baebbb96bc94bde4bf84c170c3a5c61fc8d9cbcfcefbd258d5dfd98bdd55e136e528e924ed24f121f515f8fafcca007f041407830aca0de310cc138015fe18441a501c211db81f142036212021d22250229d22ba22ac2276221d21a4211020661fa91ee01e0e1d371c611b901ac71a0a195d18c3183e17d1177d1745172817281745177d17d1183e18c3195d1a0a1ac71b901c611d371e0e1ee01fa92066211021a4221d227622ac22ba229d225021d2212020361f141db81c211a50184415fe138010cc0de30aca07830414007ffccaf8faf515f121ed24e924e528e136dd55d98bd5dfd258cefbcbcfc8d9c61fc3a5c170bf84bde4bc94bb96baebba96c701c59ec4afc436c436c4afc59ec701c8d1cb0acda2d090d3c9d744daf2dec8e2b9e6b8eab8eeadf28bf647f9d7fd330053033105c708130a130bc60d2e0e4e0f280fc21022104e104e10290fe90f950f350ed20e720e1d0dd90dac0d980da20dcc0e170e840f100fb9107e115a124813431446154a164a1740182618f619ac1a431ab71b061b2e1b2e1b061ab71a4319ac18f618261740164a154a144613431248115a107e0fb90f100e840e170dcc0da20d980dac0dd90e1d0e720ed20f350f950fe91029104e104e10220fc20f280e4e0d2e0bc60a13081305c703310053fd33f9d7f647f28beeadeab8e6b8e2b9dec8daf2d744d3c9d090cda2cb0ac8d1c701c59ec4afc436d553d335d1c1d103d103d1c1d335d553d806db38decce2a4e6a0eaa0ee86f238f59ff8a8fb47fd74ff2e0079015e01eb022f023c0227020201e001cf01dc02110274030503c304a705aa06c107e008fb0a050af50bc10c640cd80d1f0d3a0d2e0d010cbe0c6e0c1a0bcf0b930b6f0b690b830bbe0c180c8b0d130da60e3c0ecb0f4b0fb20ffb102110210ffb0fb20f4b0ecb0e3c0da60d130c8b0c180bbe0b830b690b6f0b930bcf0c1a0c6e0cbe0d010d2e0d3a0d1f0cd80c640bc10af50a0508fb07e006c105aa04a703c303050274021101dc01cf01e002020227023c022f01eb015e0079ff2efd74fb47f8a8f59ff238ee86eaa0e6a0e2a4deccdb38d806d553d335d1c1d103e234df29dcfadbd6dbd6dcfadf29e234e5dbe9d4edd4f196f4e1f78ff98ffae4fba5fbf4fbfdfbeefbeefc1cfc8bfd40fe30ff4a00740193028e035303d9042004320420040003e703e7040d045f04d90571061906bf075007c008060821081507ee07bb078b076e076e079007d4083308a0090e096d09b109d209ce09a80969091e08d4089a087a087a089a08d4091e096909a809ce09d209b1096d090e08a0083307d40790076e076e078b07bb07ee08150821080607c0075006bf0619057104d9045f040d03e703e7040004200432042003d90353028e01930074ff4afe30fd40fc8bfc1cfbeefbeefbfdfbf4fba5fae4f98ff78ff4e1f196edd4e9d4e5dbe234df29dcfadbd6ee17ea1ce6e4e518e518e6e4ea1cee17f217f577f7d4f920f994f99bf9a1f9f7fab9fbd0fd03fe0ffec5ff1bff27ff1bff27ff6efff300a1015001d80225023702280219022b026d02d8035403c2040a0422041403f903ed04040443049b04f505380555054b052a050b0503051f055905a105df05ff05fa05d705aa058a058705a605db061106340634061105db05a60587058a05aa05d705fa05ff05df05a10559051f0503050b052a054b0555053804f5049b0443040403ed03f904140422040a03c2035402d8026d022b021902280237022501d8015000a1fff3ff6eff27ff1bff27ff1bfec5fe0ffd03fbd0fab9f9f7f9a1f99bf994f920f7d4f577f217ee17ea1ce6e4e518f72ef3a8efa8ecfbecfbefa8f3a8f72ef91ff99bf999fa01fb07fc32fcf1fd21fd1dfd56fdeefe9fff11ff29ff23ff4affb50032007f008b0082009f00f101510188018c0180019601d90225024e024a023d024d028502c302e102d802c702d403020336034b033d032a0332035a0385039303800369036e039103b503bb03a30389038a03a903c603c603a9038a038903a303bb03b50391036e0369038003930385035a0332032a033d034b0336030202d402c702d802e102c30285024d023d024a024e022501d901960180018c0188015100f1009f0082008b007f0032ffb5ff4aff23ff29ff11fe9ffdeefd56fd1dfd21fcf1fc32fb07fa01f999f99bf91ff72ef3a8efa8ecfbfa07f945f5c2f1c2f1c2f5c2f945fa07fa21fb3ffc48fc65fc96fd55fdcefdcdfe0ffe9afecffecdff1aff7cff8cff95ffe3002300210037008000a3009c00bf00fc01080104012f015c0159015e018c01a7019d01ac01d701e101d601ee0211020c02060225023b022e02300250025802470252026e0268025a026d027f026f0267027e0284026f026f0284027e0267026f027f026d025a0268026e02520247025802500230022e023b02250206020c021101ee01d601e101d701ac019d01a7018c015e0159015c012f0104010800fc00bf009c00a30080003700210023ffe3ff95ff8cff7cff1afecdfecffe9afe0ffdcdfdcefd55fc96fc65fc48fb3ffa21fa07f945f5c2f1c2fc59fb6ffb18f718f718fb18fb6ffc59fcecfd21fdc2fdc2fe46fe50fea0fec9fee8ff2bff2cff73ff73ffa7ffb8ffd0fff6fff800270023004a00510066007c007f00a0009b00bb00bb00ce00db00de00f600f0010a01060117011d01210132012c0141013a014a014a014f015901530164015a01690164016a016f01690176016a0178016f01740174016f0178016a01760169016f016a01640169015a016401530159014f014a014a013a0141012c01320121011d01170106010a00f000f600de00db00ce00bb00bb009b00a0007f007c00660051004a00230027fff8fff6ffd0ffb8ffa7ff73ff73ff2cff2bfee8fec9fea0fe50fe46fdc2fdc2fd21fcecfc59fb6ffb18f718d4dbd29dd0ffd025d025d0ffd29dd4dbd788da6cdd56e019e29ce4d7e6d2e8a6ea79ec72eeb6f15ff479f7fdfbd3ffd303cc078a0add0da10fc2113f122b12a812e3130d135313d814ae15d5173918b61a201b421bf01c061b711a3018571608137310cb0e400bfa0a0f08850751065705720479034801c5ffe6fdb3fb46f8c9f670f471f2fdf238f238f2fdf471f670f8c9fb46fdb3ffe601c50348047905720657075108850a0f0bfa0e4010cb1373160818571a301b711c061bf01b421a2018b6173915d514ae13d81353130d12e312a8122b113f0fc20da10add078a03ccffd3fbd3f7fdf479f15feeb6ec72ea79e8a6e6d2e4d7e29ce019dd56da6cd788d4dbd29dd0ffd025e6eee398e0b1defcdefce0b1e398e6eeea09eca4eeedf15af451f7eefbeeffd6033605e307fd09d20b970d470e9d0f3f0f010e030ca90b650a7309b108b106fe0466012ffe05fbaefab4fb1cfc6cfde8fef2ff4fff39ff30ffa600c3024e03d604f7058c05be05e0062e06a4070106ed0638050203ad02a4022001f701b500ddff37fcfffadaf987f987fadafcffff3700dd01b501f7022002a403ad0502063806ed070106a4062e05e005be058c04f703d6024e00c3ffa6ff30ff39ff4ffef2fde8fc6cfb1cfab4fbaefe05012f046606fe08b109b10a730b650ca90e030f010f3f0e9d0d470b9709d207fd05e30336ffd6fbeef7eef451f15aeeedeca4ea09e6eee398e0b1defcf0a7edabea50e7f7e7f7ea50edabf0a7f30ef5aaf921fd2100c2037c058b075e08e1099a094808480729060d04a802d80108ffd1ff4bfefdfe8afe49fee3006301db0237017200bb0149031004c005150405029601b0014a00c1ffcefedffe87fec9ff28ff55ff8e0035013802140270028502c60330033b028f018e00ff011000fbffd7fdc5fc14fc14fdc5ffd700fb011000ff018e028f033b033002c602850270021401380035ff8eff55ff28fec9fe87fedfffce00c1014a01b002960405051504c00310014900bb0172023701db0063fee3fe49fe8afefdff4bffd1010802d804a8060d072908480948099a08e1075e058b037c00c2fd21f921f5aaf30ef0a7edabea50e7f7f552f2c6ef69ec77ec77ef69f2c6f552f83dfc3d001b02d504dd068a0735069e0586045c02cd0100ffbeff2cfecdfeb5ff640083015001f302e40391033d029e02a3025a0064fde5fd5ffee60017ffe9ffcd00b501a901dc01e70239022f018200da00820000ff52ff1bff62ff93ffba005a01270173017c01d602030159009900b400b2ff29fd2dfd2dff2900b200b400990159020301d6017c01730127005affbaff93ff62ff1bff520000008200da0182022f023901e701dc01a900b5ffcdffe90017fee6fd5ffde50064025a02a3029e033d039102e401f301500083ff64feb5fecdff2cffbe010002cd045c0586069e0735068a04dd02d5001bfc3df83df552f2c6ef69ec77f8d6f624f327efd5efd5f327f624f8d6fcd6009102f504d405aa050203eb028e00cbff9aff1cfee0ff5e0068012e01f602a40280021301ac00b2ffe1ffceff70ff6500a300e9ff99fffa01f6021a00e9009c004eff85ff76ffc1ffce005000f401160142015800da006b0026ff9cff68ffabffbe001600c900f30108016600ef004e00a7fff7fde2fde2fff700a7004e00ef0166010800f300c90016ffbeffabff68ff9c0026006b00da01580142011600f40050ffceffc1ff76ff85004e009c00e9021a01f6fffaff9900e900a3ff65ff70ffceffe100b201ac0213028002a401f6012e0068ff5efee0ff1cff9a00cb028e03eb050205aa04d402f50091fcd6f8d6f624f327efd5fbf1f87bf5daf258f258f5daf87bfbf1fff10265043304800386024e0096ff7fff16ff28001600eb01b3022e01dc017500a1ffe1ffabff73fffe008e00eb01a20140012e0114fec2fe670021fff0001a00ef00df012300f6006a0036ffb1ff9fffcefff4008300b700d900de00680032ffccff93ffd0ffd7005f00b100b0010a006b00500061fe5ffe5f00610050006b010a00b000b1005fffd7ffd0ff93ffcc0032006800de00d900b70083fff4ffceff9fffb10036006a00f6012300df00ef001afff00021fe67fec20114012e014001a200eb008efffeff73ffabffe100a1017501dc022e01b300eb0016ff28ff16ff7f0096024e0386048004330265fff1fbf1f87bf5daf258fe81fa81f801f490f490f801fa81fe810168034903ab02b2015fffd7ff48ff30000a00d4019701b4015200aaffe7ffa9ff9900360099012b011700e80063ffe5ffdfffa000b5ff93ffd90167006a005fffd7ffc0ffe8001c0096009e00c200580026ffc1ffc2ffdc0027007e009000a0003c0018ffb3ffd5ffdd0042007e009200ac00120082fec5fec50082001200ac0092007e0042ffddffd5ffb30018003c00a00090007e0027ffdcffc2ffc10026005800c2009e0096001cffe8ffc0ffd7005f006a0167ffd9ff9300b5ffa0ffdfffe5006300e80117012b00990036ff99ffa9ffe700aa015201b4019700d4000aff30ff48ffd7015f02b203ab03490168fe81fa81f801f4900016fc16f93df5d3f5d3f93dfc1600160247035602720120ffabff3bff8200750138018901290075ffd2ff99ffe8006c00f000f900c30029ffe6ffad0024005400f2008b00edff47ff040048ffe200a1008300b00038000cffbdffe80015006f008300730027ffe5ffc9ffe3002c00610083004e0020ffccffe0ffe10057005100a80014007aff08ff08007a001400a800510057ffe1ffe0ffcc0020004e00830061002cffe3ffc9ffe5002700730083006f0015ffe8ffbd000c003800b0008300a1ffe20048ff04ff4700ed008b00f200540024ffadffe6002900c300f900f0006cffe8ff99ffd200750129018901380075ff82ff3bffab01200272035602470016fc16f93df5d3a508a3e0a303a281a281a303a3e0a508a675a81da9fdac0fae4eb0b9b34ab601b8d9bbd1bee7c217c560c8c1cc37cfc1d35dd709dac4de8ce261e63fea26ee15f20af604fa01fe00020005ff09fc0df611eb15da19c11d9f2174253c28f72ca3303f33c9373f3aa03de94119442f472749ff4cb64f4751b253f1560357e3598b5af85c205cfd5d7f5d7f5cfd5c205af8598b57e3560353f151b24f474cb649ff4727442f41193de93aa0373f33c9303f2ca328f7253c21741d9f19c115da11eb0df609fc05ff0200fe00fa01f604f20aee15ea26e63fe261de8cdac4d709d35dcfc1cc37c8c1c560c217bee7bbd1b8d9b601b34ab0b9ae4eac0fa9fda81da675a508a3e0a303a281ce05cba7c9d8c8b3c8b3c9d8cba7ce05d0cdd3f1d75adafedecae2b6e6afeaafeea4f282f634f9abfcacff330168034c04e4061906da0751079007a4079807750743070a06d506ac06ac06d80719076f07d3084808ca095f0a050ac50ba50cca0e110f5d109611ac126712c512f212f812e212b31274122511ce116f110e10ac10510ffd0fb90f8b0f8b0fb90ffd105110ac110e116f11ce1225127412b312e212f812f212c5126711ac10960f5d0e110cca0ba50ac50a05095f08ca084807d3076f071906d806ac06ac06d5070a07430775079807a40790075106da061904e4034c0168ff33fcacf9abf634f282eea4eaafe6afe2b6decadafed75ad3f1d0cdce05cba7c9d8c8b3ec51e919e68be4d8e4d8e68be919ec51eff0f3d6f7d6fbceff9202d9056b074408790912092408e40847077506b9064f060b05f9061b066106b9072a07c208450860084507f6078006c205cd04c203bc02d2023e01bf0124008a000cffbfffe90048009b0092003effa4fed1fdf3fd2ffca0fc0dfb60fafbfadefae0fafafb23fb54fb88fbb7fbdafbdafbb7fb88fb54fb23fafafae0fadefafbfb60fc0dfca0fd2ffdf3fed1ffa4003e0092009b0048ffe9ffbf000c008a012401bf023e02d203bc04c205cd06c2078007f608450860084507c2072a06b90661061b05f9060b064f06b90775084708e40924091208790744056b02d9ff92fbcef7d6f3d6eff0ec51e919e68be4d8f0b6ed2bea4ae854e854ea4aed2bf0b6f493f893fc70ffd50260041505080559053504bd043d04050402044004b30571063106d2071d073406ed066205dc054b04a2043d03fb03d603d303f4040b040803b3036302f0023f013f001cff2afee4ff06ff3eff51ff4aff49ff47fef8fe8bfe2bfdb8fd1cfcaafc41fbfdfbfbfc0dfc33fc5dfc87fca8fca8fc87fc5dfc33fc0dfbfbfbfdfc41fcaafd1cfdb8fe2bfe8bfef8ff47ff49ff4aff51ff3eff06fee4ff2a001c013f023f02f0036303b30408040b03f403d303d603fb043d04a2054b05dc066206ed0734071d06d20631057104b3044004020405043d04bd05350559050804150260ffd5fc70f893f493f0b6ed2bea4ae854f957f566f20cefa7efa7f20cf566f957fd5700ff039104fc0567051a046203bf0377038803df046d04cb04cb046b03d402f00214015f00ea00aa0079009500780013ff99feeafe45fdd0fda4fd99fdd4fe16fe55fe58fe55fe13fd7cfcf8fd44fdf9fe93fef7ff7affd6fffaffdbffccfff30005003f00a90119017c01d601f601ef01d601b7019b019b01b701d601ef01f601d6017c011900a9003f0005fff3ffccffdbfffaffd6ff7afef7fe93fdf9fd44fcf8fd7cfe13fe55fe58fe55fe16fdd4fd99fda4fdd0fe45feeaff99001300780095007900aa00ea015f021402f003d4046b04cb04cb046d03df0388037703bf0462051a056704fc039100fffd57f957f566f20cefa7fe23fa23f68bf3d9f3d9f68bfa23fe2301ae03f004bd048403aa02f002a702c603250359031702790181008bffd9ff8dff7cff89ff6cff24feadfe15fdeffdfdfe33fe99fed8fefbfef8feeafefaff44ffa0004300b600f5011b00d2005700a2012a01610183019c01550107009a003e00470045003b0030fff8ff9bff47fef8feddfee7fefcff14ff14fefcfee7feddfef8ff47ff9bfff80030003b00450047003e009a01070155019c01830161012a00a2005700d2011b00f500b60043ffa0ff44fefafeeafef8fefbfed8fe99fe33fdfdfdeffe15feadff24ff6cff89ff7cff8dffd9008b0181027903170359032502c602a702f003aa048404bd03f001aefe23fa23f68bf3d9ff3afb3af77bf494f494f77bfb3aff3a023a03a203b903130280027002ca0346035f02fa022a015500c2007e007100630009ff81fee7fe89fe6ffe7cfecafee4fec5fe90fe6dfe89fed4ff50ffa1ffddffdffff20028006800d6010100b100e9011500ef00ff011e0125012000c6006e003a001000050004fffeffc3ff7aff2fff01ff01ff14ff2aff2aff14ff01ff01ff2fff7affc3fffe000400050010003a006e00c601200125011e00ff00ef011500e900b1010100d600680028fff2ffdfffddffa1ff50fed4fe89fe6dfe90fec5fee4fecafe7cfe6ffe89fee7ff81000900630071007e00c20155022a02fa035f034602ca02700280031303b903a2023aff3afb3af77bf4940187fdc5f9c5f684f684f9c5fdc501870362039202c002270224028d02b1023c01500068ffe5ffceffceff93ff12fe9cfe6afe96fef1ff27ff29fef7ff25ff82fffb005e0085007f007d009c00d9010700fa00ce00970081007e007cffdcffe1ffc1ff7fff7aff76ff74ff53ff28ff12ff5cff9bffd2ffe2ffe6ffe8001b005e009f00b300a70093009300a700b3009f005e001bffe8ffe6ffe2ffd2ff9bff5cff12ff28ff53ff74ff76ff7aff7fffc1ffe1ffdc007c007e0081009700ce00fa010700d9009c007d007f0085005efffbff82ff25fef7ff29ff27fef1fe96fe6afe9cff12ff93ffceffceffe500680150023c02b1028d0224022702c0039203620187fdc5f9c5f684d19acfe1ceb6ce1ece1eceb6cfe1d19ad3d6d689d9a2dd11e0c3e4a3e89dec9df08ff462f804fb68fe80014503b005bc076908ba09b30a5a0ab90ad90ac60a8b0a3509cf096408fe08a508610837082a083d086e08bc092409a10a2e0ac40b5e0bf50c820d010d6c0dc00dfb0e1b0e200e0c0de10da30d550cfe0ca20c470bf10ba70b6b0b410b2b0b2b0b410b6b0ba70bf10c470ca20cfe0d550da30de10e0c0e200e1b0dfb0dc00d6c0d010c820bf50b5e0ac40a2e09a1092408bc086e083d082a0837086108a508fe096409cf0a350a8b0ac60ad90ab90a5a09b308ba076905bc03b00145fe80fb68f804f462f08fec9de89de4a3e0c3dd11d9a2d689d3d6d19acfe1ceb6ce1ec8d8c6adc52ec46bc46bc52ec6adc8d8cb9aced7d271d64bda46de46e234e5ffe99aed00f02ff32df600f8b2fb4dfdd8005a02d5054507a509ea0c050de60f7e10bb119211fa11ef117610970f620dee0c530aaf091e07be06a705ee05a105c80662076808cc0a790c590e53104b122b13df15561687176e180d186c18941896187f185e1841183018301841185e187f18961894186c180d176e1687155613df122b104b0e530c590a7908cc0768066205c805a105ee06a707be091e0aaf0c530dee0f621097117611ef11fa119210bb0f7e0de60c0509ea07a5054502d5005afdd8fb4df8b2f600f32df02fed00e99ae5ffe234de46da46d64bd271ced7cb9ac8d8c6adc52ec46bd186ceaecca7cb9acb9acca7ceaed186d4fbd8d3dcd3e0c8e48be806eb33ee19f0cdf366f5fcf8a0fb56fe1900d2036205a4077208ac093e09260871073f05c0042a02b7019c0102010201a102d20477066308660a510bfc0d4c0e360ebf0efb0f090f090f1c0f5b0fd2107f1152122e12ef136f138f1338126511200f840dba0bf50a68094108a408a409410a680bf50dba0f84112012651338138f136f12ef122e1152107f0fd20f5b0f1c0f090f090efb0ebf0e360d4c0bfc0a5108660663047702d201a101020102019c02b7042a05c0073f08710926093e08ac077205a4036200d2fe19fb56f8a0f5fcf366f0cdee19eb33e806e48be0c8dcd3d8d3d4fbd186ceaecca7cb9ad352cfeccd66cc0dcc0dcd66cfecd352d736db36df01e266e554e7e0ea32ec7deee9f18cf460f742fa00fc5ffe32ff5ffff0000affedffe2002c00f902530422062d082609bf0ab50ae80a5c093d07d406790581052c059906c108780a7e0c890e580fc010b6114b11a511f61267130f13ea14d6159e160615d714f6136511500efe0ccb0b150a240a240b150ccb0efe1150136514f615d71606159e14d613ea130f126711f611a5114b10b60fc00e580c890a7e087806c10599052c0581067907d4093d0a5c0ae80ab509bf0826062d0422025300f9002cffe2ffed000afff0ff5ffe32fc5ffa00f742f460f18ceee9ec7dea32e7e0e554e266df01db36d736d352cfeccd66cc0dd18bcddbcb00c96fc96fcb00cddbd18bd58bd96cdcf1e017e30ee618e96ded1ff109f4dbf832fab5fc39fcd2fccefca2fcc7fd93ff23015003c0060007ae089108ae084307ac0743074307b208610901094008ec080806d105b20520057806e1093b0c2d0f3711df13cb14de1538152214f414f0152c158815bf1580149112ea10bd0e720c890b730b730c890e7210bd12ea1491158015bf1588152c14f014f41522153814de13cb11df0f370c2d093b06e10578052005b206d1080808ec09400901086107b20743074307ac084308ae089107ae060003c00150ff23fd93fcc7fca2fccefcd2fc39fab5f832f4dbf109ed1fe96de618e30ee017dcf1d96cd58bd18bcddbcb00c96fe02adc2ad87bd644d644d87bdc2ae02ae370e57ae673e6ffe7dde984ec00ef05f239f566f892fbd7ff32025e04e1064e068605e1051204d30589070d08c009e009f008fe07980680063e06d707cc0868082506fe057704590448056e0768097c0af70b7d0b280a5f0995090508ab085e081107ea083a09400ae50ca60dbb0d760ba508c205d403fe03fe05d408c20ba50d760dbb0ca60ae50940083a07ea0811085e08ab090509950a5f0b280b7d0af7097c0768056e04480459057706fe0825086807cc06d7063e0680079808fe09f009e008c0070d058904d3051205e10686064e04e1025eff32fbd7f892f566f239ef05ec00e984e7dde6ffe673e57ae370e02adc2ad87bd644e9f2e5f2e208df9ddf9de208e5f2e9f2ecc3edcded4dec1aeb2beb20ec12edb2ef97f18df3a0f5fcf8a2fb3ffd42fe22fdb8fc71fb25fab6fb9cfda0fff601a802140145ffe7fee5fee5ffec015d0256023300f3ff3bfe0afe2fffe402b305ba081d097009d309c909dd0a590b310c320d420e8d106e132a169e1a1e1cab1d641c05192015f613ec13ec15f619201c051d641cab1a1e169e132a106e0e8d0d420c320b310a5909dd09c909d30970081d05ba02b3ffe4fe2ffe0aff3b00f302330256015dffecfee5fee5ffe70145021401a8fff6fda0fb9cfab6fb25fc71fdb8fe22fd42fb3ff8a2f5fcf3a0f18def97edb2ec12eb20eb2bec1aed4dedcdecc3e9f2e5f2e208df9df986f6bef3c8f1e0f1e0f3c8f6bef986fb1ffb45fa85f9e4fa4afc09febe019903da053c060206bc07d509480a9d0b380aca0990084107a30815093e0a3509f407ed04680068fd31fba3fbc6fccdfd83fcf3fae7f7f7f534f392f36ef470f5d1f6daf74bf76ef7d5f8eefab4fcacfe38ff02ff43ffa600eb036406b009d70bc80bea0a76086606f406f408660a760bea0bc809d706b0036400ebffa6ff43ff02fe38fcacfab4f8eef7d5f76ef74bf6daf5d1f470f36ef392f534f7f7fae7fcf3fd83fccdfbc6fba3fd310068046807ed09f40a35093e081507a3084109900aca0b380a9d094807d506bc0602053c03da0199febefc09fa4af9e4fa85fb45fb1ff986f6bef3c8f1e0d132cf5ecd8fcc6ccc6ccd8fcf5ed132d295d380d463d5dbd856dbcadfbbe37ce68ee8e9eaf6ed53f06af433f833fbbffe5b0005012b0270044606ad09300b2c0c2f0c3c0bcb0b850be20ce90e2a0f060f0e0e480d2e0c670c6e0d460e7d0f710fb10f3c0e880e380ec0101d11da134e140313f513931380142b15911739187d18e5186e178c16e016e0178c186e18e5187d17391591142b1380139313f51403134e11da101d0ec00e380e880f3c0fb10f710e7d0d460c6e0c670d2e0e480f0e0f060e2a0ce90be20b850bcb0c3c0c2f0b2c093006ad04460270012b0005fe5bfbbff833f433f06aed53eaf6e8e9e68ee37cdfbbdbcad856d5dbd463d380d295d132cf5ecd8fcc6ce2b8deb8db41d93bd93bdb41deb8e2b8e665e941eb4aecd7ee59f014f20af40af5e0f77ef903faa1fc6ffe4ffff60114018a0187017701cb02ba041c057c0651064e058c048203c803c80486059e068106bd0640055c049d047d0526066207c008d3096b09a009c00a0f0aa60b660c150c8b0cce0d0a0d660dd90e150da30c2509980674039101d601d60391067409980c250da30e150dd90d660d0a0cce0c8b0c150b660aa60a0f09c009a0096b08d307c006620526047d049d055c064006bd0681059e048603c803c80482058c064e0651057c041c02ba01cb01770187018a0114fff6fe4ffc6ffaa1f903f77ef5e0f40af20af014ee59ecd7eb4ae941e665e2b8deb8db41d93bd9c9d5c9d270d085d085d270d5c9d9c9ddb1e10de3cee635e898eb2fedfcf0d5f38cf609f85bfaa0fce8ff1e010f028703780409048c054e066d07bc08d709560909081706f80638063806fc082d094509d609bf093608a8087e08e609c60acf0baf0c3a0c7c0ca30cdb0d310d8d0dc70dc80d9b0d650d470d330ce80c080a4a07b604ba0210007d007d021004ba07b60a4a0c080ce80d330d470d650d9b0dc80dc70d8d0d310cdb0ca30c7c0c3a0baf0acf09c608e6087e08a8093609bf09d60945082d06fc0638063806f808170909095608d707bc066d054e048c040903780287010fff1efce8faa0f85bf609f38cf0d5edfceb2fe898e635e3cee10dddb1d9c9d5c9d270d085db9ad79ad435d23ed23ed435d79adb9adf70e2afe55ee7d3ea72ed6af0a3f3cef69ef8edfad3fc8afe42000501b1031c04360523062a078809400b020c4a0c9e0bd40a3a087b075b075b087e0a4b0c050d050d050c320b0c0a1909ac09c30a210a7d0ab20aca0aef0b3a0b9e0be00bc10b220a1e08fc0801073f067d0551035f009cfd6dfa95f8e6f8e6fa95fd6d009c035f0551067d073f080108fc0a1e0b220bc10be00b9e0b3a0aef0aca0ab20a7d0a2109c309ac0a190b0c0c320d050d050c050a4b087e075b075b087b0a3a0bd40c9e0c4a0b0209400788062a05230436031c01b10005fe42fc8afad3f8edf69ef3cef0a3ed6aea72e7d3e55ee2afdf70db9ad79ad435d23edf64db8ed87bd6c3d6c3d87bdb8edf64e364e720ea6bed4defe6f24bf47df66cf811f97cfad5fc49fdf1ffc30193032a04680554061306d407ae088c093a097f094608ae080707ad07df089e09af0abb0b740bbc0bae0b830b710b8d0bc20be00bc10b5d0ad20a540a0b09ff0a140a1609db094c086d074805da040701acfebffb68f812f557f3cbf3cbf557f812fb68febf01ac040705da0748086d094c09db0a160a1409ff0a0b0a540ad20b5d0bc10be00bc20b8d0b710b830bae0bbc0b740abb09af089e07df07ad080708ae0946097f093a088c07ae06d4061305540468032a0193ffc3fdf1fc49fad5f97cf811f66cf47df24befe6ed4dea6be720e364df64db8ed87bd6c3e9bde652e3cae272e272e3cae652e9bdeda7f1a7f55cf87dfadffc79fd60fdbffdcafdb5fdabfdc5fe0bfe74fef2ff70ffe1003d008600c90113017201ed0284033003e00483050a056c05a905ca05dc05f10618065906b4071f078e07f1083e0871089008ab08d3091809820a090a920af40afb0a71092b0714043500b8fce8f924f5d7f362f213f213f362f5d7f924fce800b804350714092b0a710afb0af40a920a090982091808d308ab08900871083e07f1078e071f06b40659061805f105dc05ca05a9056c050a048303e00330028401ed0172011300c90086003dffe1ff70fef2fe74fe0bfdc5fdabfdb5fdcafdbffd60fc79fadff87df55cf1a7eda7e9bde652e3cae272f73bf39af0d9ef5cef5cf0d9f39af73bfb3bff14024e049805cc05f60549041302ae0168007d00090009006200ec017901e702210224020001cb019f018c019d01cb02080241026202620241020801cb019d018c019f01cb02000224022101e7017900ec006200090009007d016802ae0413054905f605cc0498024eff14fb3bf73bf39af0d9ef5cef5cf0d9f39af73bfb3bff14024e049805cc05f60549041302ae0168007d00090009006200ec017901e702210224020001cb019f018c019d01cb02080241026202620241020801cb019d018c019f01cb02000224022101e7017900ec006200090009007d016802ae0413054905f605cc0498024eff14fb3bf73bf39af0d9ef5cf669f269ef0aed1ced1cef0af269f669fa34fd2dff17000e0062006a00630068007c009a00ba00d400d4009c0010ff2ffe25fd4cfd15fddfffc802a005f009290bd50db80ed50f530f530ed50db80bd5092905f002a0ffc8fddffd15fd4cfe25ff2f0010009c00d400d400ba009a007c00680063006a0062000eff17fd2dfa34f669f269ef0aed1ced1cef0af269f669fa34fd2dff17000e0062006a00630068007c009a00ba00d400d4009c0010ff2ffe25fd4cfd15fddfffc802a005f009290bd50db80ed50f530f530ed50db80bd5092905f002a0ffc8fddffd15fd4cfe25ff2f0010009c00d400d400ba009a007c00680063006a0062000eff17fd2dfa34f669f269ef0aed1ca06f9e9a9d299bce9bce9d299e9aa06fa265a4a1a6fca98eac3baf15b206b51eb849bb95bef1c269c5efc98bcd34d0efd4b3d886dc61e047e432e826ec1cf019f415f815fc120011040b08030bf40fe213c617a31b741f3d22f726a52a432dd1314d34b6380a3b483e6d417a446a473e49f14c844ef1513953575549570a589859eb5b005bcb5c445c445bcb5b0059eb5898570a5549535751394ef14c8449f1473e446a417a3e6d3b48380a34b6314d2dd12a4326a522f71f3d1b7417a313c60fe20bf40803040b0011fc12f815f415f019ec1ce826e432e047dc61d886d4b3d0efcd34c98bc5efc269bef1bb95b849b51eb206af15ac3ba98ea6fca4a1a265a06f9e9a9d299bcecc5dcb9acaf6ca74ca2bcc2bcdd1cfdfd1cfd3fed61bd865daa3dd02df57e1c6e42be6a5e916eb97ee0ef092f30cf58ff807fa87fcfbff7301df044e06ae09100b630db50ff712371465169018a81aba1cba1eb22095226f243425ee279129272aa52c152d6a2eb02fda30f231ec32d23398344834d43548359635c735cf35b6356d34fe3456337d325030dc2f2a2d4c2b3a290626a52427217e1ebe1bd618db15b912890f310bd1084604bc0100fd57f957f618f5b5f51bf48df3daf329f25cf18df0a6efbdeec0edbfecadeb98ea75e94fe81ce6e7e5a9e468e321e1d8e089df3bdde9dc99db48d9f9d8abd763d61dd4ded3a5d275d14dd032cf23ce24cd36cc5dcb9acaf6ca74a411a0819d8b9a069a069d8ba081a411a76eab25aebfb295b655ba41be1bc215c5fdc9fdcdedd1ecd5dbd9d4ddbce1a9e585e960ed2af0f0f4a3f84efbe5ff7102e9065109a40ce4100f1323162119051bd11e802117238d25ea28232a412c372e122fc0315332b433f9350735f936ad3746379837d037b8378636f8365535403422326a30cf2e192e1930cf326a34223540365536f8378637b837d03798374636ad35f9350733f932b431532fc02e122c372a41282325ea238d21171e801bd1190516211323100f0ce409a4065102e9ff71fbe5f84ef4a3f0f0ed2ae960e585e1a9ddbcd9d4d5dbd1eccdedc9fdc5fdc215be1bba41b655b295aebfab25a76ea411a0819d8b9a06c592c324c11bbea4bea4c11bc324c592c7d5ca50ccaecf30d199d41cd688d905db6bdddee03ae29de4e9e738e96feba7edc6efe3f1e4f3e3f5c5f7a2f960fb18fcb0fe40ffae01130254038c049c05a40680075507f9089b0901097009910ccf10cf146a18091b6b1ebc21d924dc27ad2a5e2cde2f383160335d352636be381f39483a343add3b3d3b3d3add3a343948381f36be3526335d31602f382cde2a5e27ad24dc21d91ebc1b6b1809146a10cf0ccf099109700901089b07f90755068005a4049c038c02540113ffaefe40fcb0fb18f960f7a2f5c5f3e3f1e4efe3edc6eba7e96fe738e4e9e29de03adddedb6bd905d688d41cd199cf30ccaeca50c7d5c592c324c11bbea4cda8cb86c9b9c781c781c9b9cb86cda8cf9dd1bcd3bcd5d2d7d0d9d8dbcbddbfdfa0e17be345e503e6b1e84fe9ddeb56ecc1ee11ef57f07bf198f28bf37ff43df507f586f632f649f854fc54ffbc034e068f09d70ce10fe312b0156a17f51a671cac1ed220cd22a4245225d727342862296a2a3c2aea2b5a2ba92bb12b9a2b2f2aad29bc28ce271c271c28ce29bc2aad2b2f2b9a2bb12ba92b5a2aea2a3c296a2862273425d7245222a420cd1ed21cac1a6717f5156a12b00fe30ce109d7068f034effbcfc54f854f649f632f586f507f43df37ff28bf198f07bef57ee11ecc1eb56e9dde84fe6b1e503e345e17bdfa0ddbfdbcbd9d8d7d0d5d2d3bcd1bccf9dcda8cb86c9b9c781caffcaa9ca59ca19c9ffcc4cce21d04fd246d46ad665d879da69dc66de41e022e1e1e3a0e53fe6d7e84fe9bceb09ec48ed66ee72ef5ef034f0ebf185f208f257f2f4f6cffa9bfe5401da054f088f0bbb0eb21194143e16d2192d1b711d781f68211922b124072546263d271e27b0283128572876282427ea26f3286b2b6e2db6300131d4337d34b6359c3602362635ed357934b633bd327c31062f512d682b4528ee266423a520b81d941a4d16c4132d0f2d0bdc0b9d0aff0a65097d088f075d061f04a5031d015bff8dfd87fb74f92df6dbf454f1c5ef02ec3be93ee641e30ddfe0dc77d91fd57fd20cce1ecd1dcd5acd26cd19ccdacca8cc59cc0fcbb4cb5dcaffcaa9ca59ca19cba3c96dc78bc52fc52fc78bc96dcba3cd9fcfc3d1bbd3c7d5add79cd966db31dcd8de7adff9e16de2bee400e520e62ce716e7e8e899e92de9a3ea05ed77f177f515f8bafc1aff73028b059608630b1f0d9b100612301446161917d919511ab71bd11cdc1d901e401e861ee21e941f8523182615290d2ba72e1d3040323133d335363648370e377b377b370e3648353633d3323130402e1d2ba7290d261523181f851e941ee21e861e401d901cdc1bd11ab7195117d916191446123010060d9b0b1f08630596028bff73fc1af8baf515f177ed77ea05e9a3e92de899e7e8e716e62ce520e400e2bee16ddff9de7adcd8db31d966d79cd5add3c7d1bbcfc3cd9fcba3c96dc78bc52fd050ce77ccd4caaacaaaccd4ce77d050d1e4d37dd4e5d639d768d870d95eda12dabddb11db80db48dd03e0b0e3b2e6cae985ec2dee8ff0caf2cef49af63bf794f8d4f9b0fa99facefce900e9043207850a6f0d3a0fb311fa13fe15be1748187e198f1a301ad21ab41c6e200222d1259c27f02a172bdd2d602e8f2f682ff8301f30092f6a2eae2d0d2d0d2eae2f6a3009301f2ff82f682e8f2d602bdd2a1727f0259c22d120021c6e1ab41ad21a30198f187e174815be13fe11fa0fb30d3a0a6f0785043200e9fce9facefa99f9b0f8d4f794f63bf49af2cef0caee8fec2de985e6cae3b2e0b0dd03db48db80db11dabdda12d95ed870d768d639d4e5d37dd1e4d050ce77ccd4caaaae45aa98a77ba37ba37ba77baa98ae45b193b52eb88bbc1cbf7cc303c661c9dbcd33d0a0d3eed74dda8edddce10fe44ce76eea97eda8f0bcf3b9f6b7f99ffc86ff56022504dd07920a310cca0f4e11cc1433169318dd1b1e1d491f6921742372255b273628fb2ab22c522de12f5a30c13211334d3471358036763755381838c3395039c13a103a3e3a3e3a1039c1395038c338183755367635803471334d321130c12f5a2de12c522ab228fb2736255b237221741f691d491b1e18dd1693143311cc0f4e0cca0a31079204dd0225ff56fc86f99ff6b7f3b9f0bceda8ea97e76ee44ce10fdddcda8ed74dd3eed0a0cd33c9dbc661c303bf7cbc1cb88bb52eb193ae45aa98a77ba37bd320d0fecef0cbd3cb1dcdd5d026d320d601d949dc87e00de38de743eaf2eecbf29cf68cfa71fe6e025e065e0a4e0e481230161b19f11dc4217f253228c82c522fbb33113643395b3c4a3f1841b84430467048804a504be14d244e154e974e844df24d0b4bd04a55489946a84481422e3fae3d093a3e3754344a31262de72a93272a23b020251c8e18eb1540118e0dd70a1e066502affefefb54f7b4f422f09fed30e9d6e699e379e07eddabdb0bd8a3d684d4c8d395d2b4d21ad1b1d17cd16ad17ed1abd1f6d251d2c5d340d3cfd460d4ffd59ad63fd6dbd77dd810d8a6d927d9a8da0fda72dab5daf2db07db14daf2dac5da60d9edd938d874d75fd63dd4b2d320d0fecef0cbd3c1e2beabbc0ab921b921bc0abeabc1e2c50bc88ecc0bcfc6d37bd75cdb34df2ce317e717eb07ef03f2eaf6d4faa5fe71021f05c0093c0ca20fdd12f915e0189d1b181d5a1f4620de21e2225c2278224821d42129204a1f401e0d1cb91b4419b6180f1656148b12b510d30eed0d010b17092f074e057803b001fa005cfedafd79fc42fb3bfa73f9f5f9f5fa73fb3bfc42fd79feda005c01fa03b00578074e092f0b170d010eed10d312b5148b1656180f19b61b441cb91e0d1f40204a212921d422482278225c21e220de1f461d5a1b18189d15e012f90fdd0ca2093c05c0021ffe71faa5f6d4f2eaef03eb07e717e317df2cdb34d75cd37bcfc6cc0bc88ec50bc1e2beabbc0ab921ce03ca9cc7d2c4d9c4d9c7d2ca9cce03d164d520d8d5dcc2e0a2e4a2e88cec83f05bf42ef7d7fb68fec001ed04cd0764098e0b290bf10c450c310bda0b3b0a7209770862072c05eb0497034601f100acff73fe59fd5efc97fc06fbcafbf7fce2fe510018021f045b06bc093c0bce0e6f111313b7165018da1b4c1da01fcc21ca238b2508262926df26df26292508238b21ca1fcc1da01b4c18da165013b711130e6f0bce093c06bc045b021f0018fe51fce2fbf7fbcafc06fc97fd5efe59ff7300ac01f10346049705eb072c086209770a720b3b0bda0c310c450bf10b29098e076404cd01edfec0fb68f7d7f42ef05bec83e88ce4a2e0a2dcc2d8d5d520d164ce03ca9cc7d2c4d9d422d090cda1ca92ca92cda1d090d422d7afdb92df66e366e748eb35eef1f29bf5fbf927fbe3fe34ffa0003f005b0020ff97fedefdf8fcfefbf0fae6f9e2f8faf835f7aaf76df79cf891fa53fc79fef601a3047e076a0a670d5c104a131715c318331a631c2d1d821dfd1da01cca1b941a181865168c1498129710920e9b0cb90b00097c084b07810781084b097c0b000cb90e9b109212971498168c18651a181b941cca1da01dfd1d821c2d1a63183315c31317104a0d5c0a67076a047e01a3fef6fc79fa53f891f79cf76df7aaf835f8faf9e2fae6fbf0fcfefdf8fedeff970020005b003fffa0fe34fbe3f927f5fbf29beef1eb35e748e366df66db92d7afd422d090cda1ca92d8a7d833d7aad611d5e1d8f2dbe8df8be327e719eaf4eef4f2c7f697fa1efd78005e02dd04750510050c04a603e902fb01e000b6ff80fe5cfd4dfc73fbdcfbaefc23fda2ffb6023204ec07d80ada0de810ec13dc16a1192e1b671d341e601e7d1dd01cb01b3019731784157c136411530f520d7d0bde0a9b09d209f90af70c610e211013122b14501678188d1a851c471dc71ee01f7e1f351dec1c1819da1752149211af0eb80bbe08d006000362010fff23fdedfdbafe13feceffc700ee0229037004a905ce06c3078107e607de0726055f02d9ffe7fc94f90bf54df17eed99e9c5e5fbe267df03dc09d985d809d746d6fad6f0d728d76fd7dad82ad885d89bd8a7d833d7aad611d79ed3e2d0cccda0cda0d0ccd3e2d79edb52df52e335e72feaf1ee99f1e5f4daf72df881f8e7f8e5f876f7d9f705f629f53ff472f3bff356f342f3cef55df7a7fa4afd3d0051038306ae09d10cc60f8a11f113ee1522154214b513c0127710ff0f600dba0c140a8d092e0823077b07a708cf0a7b0c7f0ebd111c138a15f018401a601c401dbb1eb51eb51dbb1c401a60184015f0138a111c0ebd0c7f0a7b08cf07a7077b0823092e0a8d0c140dba0f6010ff127713c014b51542152213ee11f10f8a0cc609d106ae03830051fd3dfa4af7a7f55df3cef342f356f3bff472f53ff629f705f7d9f876f8e5f8e7f881f72df4daf1e5ee99eaf1e72fe335df52db52d79ed3e2d0cccda0dd8ed98ed62bd2bed2bed62bd98edd8ee15ee542e8a6eb9fed35ed97ed5decd7ec2beb95eb3feb71ecd1ef77f28cf5faf966fcc4ffbd0234035b033f029401910073ff61fe98fe4fff3b0166040706fb09f20cd70f5a1159120a117510540ed80d440bb90a7b09b90a2f0be20e0d1088130915751783190819441836169f14ab12a1109d0ee90dae0dae0ee9109d12a114ab169f18361944190817831575130910880e0d0be20a2f09b90a7b0bb90d440ed810541175120a11590f5a0cd709f206fb04070166ff3bfe4ffe98ff61007301910294033f035b0234ffbdfcc4f966f5faf28cef77ecd1eb71eb3feb95ec2becd7ed5ded97ed35eb9fe8a6e542e15edd8ed98ed62bd2bef7fcf779f6f6f61bf598f56cf597f617f6e9f80bf977fb2afd1eff4d01b0044006f609c90cb10fa612a01595187d1b501e06209622f92528271c28cf2a3c2b5d2c302caf2cda2caf2c2b2b512a1f289926c0249822251f6b1c70193b15d1123b0e7f0aa506b602bbfebbfabff6d0f2f7ef3beba4e83ae505e20bdf51dcdedab6d8ddd756d625d54ad4c7d49bd4c6d546d618d73ad8a7da5adc4ede7de0e0e370e625e8f8ebe0eed6f1cff4c4f7adfa80fd35ffc502280457064b07fe096b08e8086407e1075e06db065705d4055104ce044a03c7034402c1023d01ba013700b40030ffadff2afea6fe23fda0fd1dfc99fc16fb93fb10fa8cfa09f986f903f87ff7fcf779f6f6f61bf556f4e6f477f478f408f409f478f551f691f830fa26fc6bfef301b404a107ad0acc0dee1106140816e519911bff1e261ffa2174228b233b237e235222b521aa20311e501c0b1969167413340fb50c02082904350035fc36f847f474f0caed57ea25e740e4b0e27fe0b2df4fde59ddd4ddbede17dedbe007e193e379e5afe82aeae1edc6f0cef3e9f70cfa27fd2e001402ca0546077c09620aee0c1a0cde0d370d210c9c0ba60a43087608070798072806b9064a05db056b04fc048d041d03ae033f02d0026001f10182011200a30034ffc4ff55fee6fe77fe07fd98fd29fcb9fc4afbdbfb6cfafcfa8dfa1ef9aef93ff8d0f861f7f1f782f713f6a3f634f5c5f556f4e6f477f478f34bf310f2d6f20df1d3f225f303f465f642f890fb3ffe40018104ef08740bfe0f7612c815e018ad1b1c1d211ead1fb72039202d1f941e6f1cc31a9817f914f311950df20a1b06260226fe30fa5af6b7f359f053edb4eb89e9dde8b8e81ee813e895e99feb2bed2fef9ff26cf584f8d6fc4effd7035d06cb0a0c0d0d0fbc120a13e7154916261679163f15761423124c0ff90d360a11069a02e4ff01fec6fe8bfe50fe15fddbfda0fd65fd2afcf0fcb5fc7afc3ffc05fbcafb8ffb54fb19fadffaa4fa69fa2ef9f4f9b9f97ef943f908f8cef893f858f81df7e3f7a8f76df732f6f8f6bdf682f647f60cf5d2f597f55cf521f4e7f4acf471f436f3fcf3c1f386f34bf310f2d6f20df63df63ef640f57af57bf644f7cdfa07fcdb002f03e107ce0bce0fba136c16c019941bce1d571e201e211d5b1bd6199f16ce137d0fce0be507e803ff0050fcfffa2ef7f7f672f5acf5adf676f7fffa39fd0d0061041307ff0bff0fec139e16f219c61c001d891e521e531d8d1c0819d1170013af10000c17081a04310082fd31fa60f829f6a3f5def5dff5e1f5e2f5e4f5e5f5e7f5e8f5eaf5ecf5edf5eff5f0f5f2f5f3f5f5f5f6f5f8f5faf5fbf5fdf5fef600f601f603f604f606f608f609f60bf60cf60ef60ff611f613f614f616f617f619f61af61cf61df61ff621f622f624f625f627f628f62af62bf62df62ff630f632f633f635f636f638f639f63bf63df63ef640f57af982f966f949f83af81df8f2faabfd2b004b03d8079a0b570ed311d6143115be1664161614d812bb0fdd0c6a0894049400a6fd04f9e5f777f5dcf52df572f6a5f8b2fb77fec90272063a09e30d350ffa1207133a137f12d011350ec70ba8080604180018fc42f8cff5f1f3d4f296f248f2eef47bf6d6f9d9fd55011200f500d800bb009e008100640047002b000efff1ffd4ffb7ff9aff7dff60ff43ff27ff0afeedfed0feb3fe96fe79fe5cfe40fe23fe06fde9fdccfdaffd92fd75fd58fd3cfd1ffd02fce5fcc8fcabfc8efc71fc55fc38fc1bfbfefbe1fbc4fba7fb8afb6dfb51fb34fb17fafafaddfac0faa3fa86fa6afa4dfa30fa13f9f6f9d9f9bcf99ff982f966f949f83afc81fc7bfc75faeafae4fc64ff2f02d606cb0a720d3d0ebd0eb70d2c0a5606a402a4fef1fc1bfa90fa8afc0afed5027c06710a180ce30e630e5d0cd209fc064a024afe97fbc1fa36fa30fbb0fe7b0222061709be0c890e090e030c7809a205f001f0fe3dfe37fe32fe2cfe27fe21fe1bfe16fe10fe0afe05fdfffdfafdf4fdeefde9fde3fdddfdd8fdd2fdcdfdc7fdc1fdbcfdb6fdb0fdabfda5fda0fd9afd94fd8ffd89fd83fd7efd78fd73fd6dfd67fd62fd5cfd56fd51fd4bfd46fd40fd3afd35fd2ffd29fd24fd1efd19fd13fd0dfd08fd02fcfcfcf7fcf1fcecfce6fce0fcdbfcd5fccffccafcc4fcbffcb9fcb3fcaefca8fca2fc9dfc97fc92fc8cfc86fc81fc7bfc75faea0027002c0032fd67fd6d004304430719071e0454005ffd94fd9a007004700746074b0481008cfdc1fdc7009d049d0773077804ae00b9fdeefdf400ca04ca07a007a504db00e6fe1bfe21fe27fe2cfe32fe38fe3dfe43fe48fe4efe54fe59fe5ffe65fe6afe70fe75fe7bfe81fe86fe8cfe92fe97fe9dfea2fea8feaefeb3feb9febffec4fecafecffed5fedbfee0fee6feecfef1fef7fefcff02ff08ff0dff13ff19ff1eff24ff2aff2fff35ff3aff40ff46ff4bff51ff57ff5cff62ff67ff6dff73ff78ff7eff84ff89ff8fff94ff9affa0ffa5ffabffb1ffb6ffbcffc1ffc7ffcdffd2ffd8ffdeffe3ffe9ffeefff4fffaffff0005000b00100016001b00210027002c0032fd67006000600060fc60fc6000600060fc60fc6000600060fc60fc6000600060fc60fc6000600060fc60fc6000600060fc60fc600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060006000600060fc60f140f0f5f0b1f071f032f0a0f1b4f363f5a2f860fb8aff0c02cf06bc0abc0eb71295164019a41cad1f4b21712312242724ab249d23fe22d321241efb1c661973163312b80f150b5e07a704030084fd3bfa38f78af53bf354f1def0dcf04ff037f090f154f27bf3fbf5c7f7d4fa12fc72fee5015b03c6061708400a340bea0d590e770f420fb40fce0f8f0efb0e160ce60b7209c507e705e403c7019aff6afd42fb2bf930f759f5aef435f2f3f1ecf121f093f041f028f045f094f10ff1aff26ef345f42bf519f609f6f2f7cff89af94ef9e7fa61fabbfaf3fb09fafefad4fa8bfa28f9aef921f885f7ddf72ff67ef5cef522f47ef3e3f354f2d1f25af1f1f193f140f0f5f0b1f071f6a1f68af66af644f61cf6e9f89bfb18fe3b01da05c309c30da6113b145516cd1886196c197618a4170414aa11b60e4c0a9806c60304ff7ffc5ff9c7f7d2f694f616f659f754f8f4fb22fdbc009e03a206a009700bef0dfe0f84107010b710590f5b0dcb0bbf095106a003cc00f7fe43fbcef9b3f808f6dcf639f620f68ef778f8cbfa74fc59fe5f006a025f042405a306ca078c07e007c5073d0652050f038701ccfff4fe15fc45fa97f91ef7e7f6fcf664f620f62ff689f725f7f6f8ecf9fafb0dfc17fd09fdd6fe76fee0ff11ff09fec9fe57fdbafcfafc23fb3ffa58f978f8a8f7eff752f6d4f677f639f617f60ef618f630f64ff66ff68df6a3f6aef6aef6a1f68af66af644f946f915f8eef8cff8b2f9d2fc0fff3102ee06ee0ad60e4f110c12d2137b12fb11600ed00b8307c403e30035fd05fa95f915f89df932fabffd1b000b034b068e098c0c010db90e8e0e710d670b890901060902e1ffcdfd0cfad8f95af8adf8d8f9cffb77fda5002202b60523073408bb099809bb092107dc060903d20166fefafcc1fae6f98ef8cff8b2f932fa3dfbb6fd76ff52011e02b203e904ab04e9049f03d702a40121ff71fdb7fc17fab1f99ff8f1f8aff8d9f962fa38fb43fc67fd87fe88ff54ffd9000efff2ff87fedbfdfdfd01fbfdfb05fa2af97bf901f8bff8b4f8d9f923f987f9f6fa63fac1fb08fb32fb3dfb29fafbfabafa6cfa1af9caf983f946f915f8eef8cffba7fb7afb5afb43fb30fcef001f041c081c0b580d320d520bb508ae04d200dffd90fb82fb0ffc43fed7024405dc08eb0ada0b4e0a3307c3047800f2fddcfbc4fb0afbc5fdc700a403c9069608820931088406a003e400d7fe0afc02fb19fb71fceeff3d01e604610633070406b0054903180089fe16fc33fb34fb3ffc47fe0f0038025203f504d004bd03c302140006fdfafc50fb53fb28fbccfd17febf006e01cd029b02b2021100dbff4cfdb1fc53fb6efb25fb7afc53fd7dfeb8ffc4006e0097003bff6ffe5cfd37fc33fb7dfb2dfb49fbc0fc72fd35fde0fe51fe75fe47fdd5fd36fc89fbedfb79fb3afb33fb59fb9cfbe6fc25fc4bfc52fc3cfc11fbdbfba7fb7afb5afb43fce6fcbffca2fc8ffc81fec5028b068509590a16087f05220122fdd3fc49fcfbffa0034806b008b308a50690032bff99fd08fc4bfd92006303c1068407bf070b04aa016afe62fc8ffc81fe2f00fd03ef0604068c055c02dfffedfd7efc5bfcd9febf015e03ce053b052d03ae0141feb8fce5fc5cfd3dff2e017e0361043503b60213ffdcfdcdfc8ffc81fd9aff6e015802af03020239009dfeb7fd29fc6dfcb6fdddff7500ec01c301b500cbff58fdd6fcc3fc6efce8fdf9ff3b003f00ab0060ff7cfe4dfd37fc8ffc81fd04fde0fec1ff5aff78ff17fe5afd82fcd3fc7efc93fcfcfd8bfe09fe4bfe3dfde9fd6efcf5fca0fc80fc92fcc3fcf9fd1cfd21fd0bfce6fcbffca2fc8ffcf3fcfefd02fcfbfcefff720366071808f6083a05380138fde7fca2fde3011404cf077d07fe061e02afff21fcf0fcfaff2c028b05a30722066c03d20070fdaffcaffdce0083039e05cb0620047f019bfeacfce9fd02fedd01a40424054c04a40277ffb3fd7ffcbdfdb2ffe602610412044402e70093fe42fce6fd06fe8400b1029c037402e10127ff02fd56fccbfd8eff3e01190253026a0159ff97fde1fce7fd05fe20ffb3010c019a0124ffe2fe5dfd34fcd8fd63fe8affc600900093ffd5fea7fd89fcebfd00fdb2fea8ff73ffbfff6efea9fdc3fd18fce5fd2ffdcafe69fec8febffe59fdc4fd3cfcf1fcf6fd39fd91fdd3fde3fdbffd7bfd34fd03fcf0fcf3fcfefd02fcfbfda3fd84fd69fd59fd4e00030403073507f205dd020ffe7efcf8fe3901890526072f069a03b8000afd72fd3aff6f02de05b8068404dd01a3fe7ffd09fdf300b303d105ad055302f8ffd5fd85fd2ffeed01cb0444051103cc0123fe74fd1bfdbbfff0028b042e04020225ff8ffd93fd2bfe7c00ca02da039a02ac0090fe5cfd2dfd90ff41015402b202a7013fff38fd99fd2dfe1dffdc017b0221017dffeafe37fd3efd71fea5002e013b01440048fecefd96fd35fdcdff01002700a60041ff30fe02fd4bfd5cfe1bff18ffcbffd9ff40fe52fd89fd40fd8dfe39fee1ff2cfef7fe64fdbefd55fd51fda4fe15fe63fe68fe27fdc4fd70fd4dfd5bfd85fda9fdb4fda3fd84fd69fd59fe96fe99fe88fe7afe74023105060377ff77fdef00ad043c043600a9fdf6ff600312047501d9fe7afe7401b7043002d3ff57fe00006103780371005efe08ff3f026e039f0160fe7afe74013e035a022fff36fe12001602b302ad0013fe1aff1f01ca02c800e6fe7afe7400c50283018bff15fe24ffcb01ee01e8ffc8fe2bfefe012601f2006dfe7afe74004b01ad00e7fef5fe35ff80012a0124ff7dfe3dfedd0082011cfff4fe7afe74ffd200d70043fed4fe47ff350065005fff31fe4ffebdffde0046ff7afe7afe74ff590001ffa0feb4fe59fee9ffa1ff9bfee6fe60fe9cff3aff70ff01fe7afe74fedfff2bfefcfe93fe6afe9efedcfed6fe9bfe72fe7bfe96fe99fe88fe7aec42ec38ec29ec11ebbfec28ed42eefdf14af415f74bfad4fe9c028b068b0a860e69121f159818c51b991e09200e21a322c5237423b2238322ee21fc20b41f231d531b50192816e5149512410ff60dbc0b9b099c07c406170499034c022f01430085fff3ff89ff43ff1dff10ff1aff33ff57ff81ffaeffd8fffd001a002c0034002e001dffffffd6ffa3ff67ff25fedffe97fe4ffe09fdc6fd89fd54fd25fd00fce3fccefcc0fcbafcb9fcbcfcc0fcc5fcc7fcc5fcbdfcabfc8ffc67fc31fbecfb98fb33fabffa3af9a7f906f858f7a0f6dff617f54bf47df3b0f2e6f222f165f0b2f00aef6feee1ee63edf3ed93ed42ecffecc9eca0ec81ec6bec5cec51ec4aec42ec38ec29ec11f95cf938f90bf8daf8bcfa41fd1c00d404d408870b6c0d2a0d9d0cd60b1508c20651043602cc024c02c1040d05ea07fc09dd0b340bbd0b580a0c0803058402e80088feb2fd9dfd5efdecff1f00ba02740405053205d205da055404640339020c010e00680030006600f901c802aa037303fd043003fe036f029601900081ff8bfec9fe4dfe1efe36fe83fef0ff64ffc70007001c0003ffc4ff6aff06fea6fe59fe27fe12fe17fe2ffe4ffe6dfe7ffe7efe66fe3afdfefdb7fd6dfd28fcebfcb9fc92fc74fc5afc42fc28fc0afbe7fbc2fb9dfb7cfb61fb4dfb42fb3cfb3afb36fb2cfb1afafcfad3faa1fa6afa32f9fef9d2f9b1f99cf991f98cf989f983f974f95cf938f90bf8dafb93fb80fb51fb18fb04fd4101000500080609430897068b041c025701f60321056807ea09b10a0408ad060702d90011fe70fe4dff7f0170035b049004b303d3025f00f7002d005501660303049e05ad05da051a03b2021600bf0003fffd0085014801e8021f01d501270056ffabff62ff8e001b00d6017e01e001e6019701160090002bfff8fff5000b001e0017ffecffa6ff55ff0ffee3fed4fedcfeeefefcfefdfef4fee6fedcfeddfee6feeffeecfed3fea2fe5ffe19fde1fdc2fdbffdd0fde3fde6fdcdfd96fd4bfd02fccffcc0fcd8fd09fd3ffd60fd5bfd2cfcdcfc83fc38fc0ffc0ffc2ffc5bfc7afc78fc4ffc04fbacfb5dfb2cfb22fb3afb62fb86fb93fb80fb51fb18faabfa91fa75fa5bfa44fc14ff57035707460a6e0c520cc60bee0a2a07f905d6041a02ec024601fd01d901ae0169011b00ed011001ad02ce045506000776085b086b078d05d803980137ff27fdcbfd5bfddfff2900e602b2042d0514054b04df03ff02eb01e40117009b006900670073006c00460003ffbaff89ff8dffd70060011001bd0237025802090151004bff29fe23fd6afd1efd48fdd4fe9bff6c00160076007c002effa4ff01fe67fdf2fdaefd98fda3fdb9fdc6fdbffda0fd73fd47fd2afd2afd48fd7cfdb5fddefde4fdbbfd63fce8fc5dfbddfb7efb50fb58fb8dfbdefc33fc76fc96fc8afc56fc05fba8fb4ffb08fadafac4fabffac2fac3fabcfaabfa91fa75fa5be9cde95ce8f0e88ee831e990ec57f007f407f7bdfaa6fc67fcdbfc12fa50f7fdf597f397f268f250f36af5a4f8c2fc6b003603ba069f08a809bc09e9095d085f0742065c05f20635073708ec0b2f0dc1105f12c014a915f21687167115cf14d013ac129e11d611771190121d130414211545164116ec172916ea1634151813b5123310b80f680e5c0da20d390d140d1c0d320d360d0d0ca10be60ade09920816068404f70387024801450081fff4ff90ff42fef4fe92fe0cfd58fc74fb65fa38f8fcf7c4f6a0f5a0f4ccf428f3aff35af31cf2e6f2a9f259f1eff168f0c4f00cef49ee86edd0ed30ecaeec4aec06ebd9ebbeebaaeb93eb71eb3feaf9eaa2ea3be9cde95ce8f0e88efb0bfafcfafdfafffaecfd1200b404b407fa09cf0a0c0912078d062c0553050504f304ab03dd028300ebff95fefeff6a00c2029b0463059205e6056f048903aa0332034103aa040d0400034301e0002dfeadfddcfe07ff2500e202bb042a04da04b803f702ef01f9014f00f600c90092002aff8efee2fe67fe57fed0ffbe00e301e902830288020101220035ff7fff21ff18ff3aff52ff38fee2fe67fdf8fdc8fdf4fe7bff35ffe8005b006b0015ff78fec5fe2afdc7fd9dfd99fd9cfd8dfd63fd2cfd01fcfefd31fd93fe09fe6afe94fe74fe0ffd7ffceafc74fc30fc21fc33fc4ffc5cfc52fc35fc15fc03fc0cfc2ffc5efc84fc8dfc6efc2bfbd3fb7bfb35fb0bfafcfafdfafffda8fd93fda7fdbafdb101b104da0405018a018204180586036bfff1feca0084025b023f0138016002cf03bc031701bc00f100cb00ab008a00e601a201f901ae018a0214028101b8001dff6a006a01c101aa0069fffb014702b60247004eff1dfff4016a0168ffffff38003f01cf01f0008eff6fffc600bf00d7ffebff3fffac009500dd005effdeffe100180004ffb4ff8cff9fffadffa4ffbbfff90006ffa9ff3bff40ffa1ffb9ff41fec5fef5ffa2ffe9ff64feb9febeff57ff9aff13fe63fe66ff0cff72ff17fe79fe63fed9ff24fed4fe49fe28fe7efec5fea1fe4dfe34fe61fe81fe63fe2cfe14fe1cfe1ffe12fe09fe0cfe04fdebfddafde3fdedfdd6fda8fd93fda7fdbafe5cfe8afe76fe45fe3e023e032500cb0169048203e20021ff6c019c0166ff480019030a0347013f0112024b017eff7fff9c0135017800d20151023e01d100b7006f00940057003b00ae011501310154014200ae00450072006cfff40021010a01370076005a010000baff97ff90009f00afffcafffe011a00e9ffa5ff95008d0059ff41ff7d00b0009cff8dffa700930045ff28ff4400380018ff45ff7d0054001dff41ff50ffeeffb7ff11ff3fffdaffbdff3dff55ffb2ff7eff0fff1fff66ff4fff19ff32ff5bff41ff17ff15ff15fefffef8fefefef6fef2ff03fefdfed4fec9fee2fed3fea1fea5fed5fecafe90fe94fec3feacfe68fe6dfea0fe8dfe52fe5cfe8afe76fe45e78fe758e71ae6d5e66ae8e0ec58f02df424f824fc20001003f007be0b760f1812a2161219681ca01fb5229f253e2726283528f0297a29d029d7293f2800264223e821361e671b9118be15f3133510880df30b88098d082f070a05fc04fc0408031d023b01630096ffd9ff3afed9feb4fea9feaffed1ff2effc4003b004f004000250005ffe1ffbaff90ff64ff36ff05fed3fe9efe66fe2dfdf1fdb2fd6cfd18fcd0fcccfce0fcf8fd0bfd12fcfefcb8fc4efbd6fb58fad7fa54f9d0f94cf8c6f83ff7b5f724f67ff5a6f4b8f3c8f2dbf1faf124f053ef87eebeedf9ed37ec7bebc5eb1aea85ea0de9a5e946e8f5e8c6e8a6e88be86fe851e831e80ee7e8e7bee78fe758e71ae6d5f659f606f5baf58af561f8d5fcc000c004b708960c440f380f5e0e820d7f0c6d0b550a3d094d099a0a380b0e0bde0ca60d610df50d460c1e09d5072e048901f5ff88fdf6fd3dfd2cfea3007a0259042a059e061f067e06b205f8050b041d03510367039303ab038304000492051004cf045903dc035802b601690014ff38fec2fe5bfe04fddafe01fec1ff60ff7aff87ff90ff95ff94ff70fee7fed4fecffec9fec0feadfe7cfe56fe23fddefd97fd50fd0afcc5fc82fc5ffc21fbe2fba3fb66fb2bfafafabffa6afa4bfa31fa18fa00f9e9f9defa16fa2afa14f9f9f9dbf9baf98ff921f8a5f851f81af7e6f7b5f788f77ff78df797f77cf750f721f6f0f6b1f659f606f5baf58af999f94ff90ff90bf8f0fca700a704a3086e0a29096a087d0785069f077109b50ace0baa0c540b3f088e057f027cffb4fe94fe5fff6e018503a5046304ce03ef0301025802dc0382054c070e07c00734068204e6030001c401220096006f010a00eb00ca00fa0115005c006f00a900e701300233027c02a502a90257017a011200b6005e0009ffd0ff81ff32fee8feadfebbfed0fee1fef1fefdfed8fecdfed5feddfee7ff3aff5aff29fef1feb3fe12fd6cfd2ffcfafccdfd09fd4efd3afd2ffd1ffcadfc37fc17fc0cfc0cfc64fcbdfce6fcd4fca3fc21fb9dfb2afafffaeafb15fb41fb65fb48fb0bfaacfa51f9fbf9d9f9e9fa13fa3bfa5efa6afa2ef9e5f999f94ff90ff90bf914f909f917f91ef902fcb000ad04ad08960c420e080f480ffb0da40a4e072505a2044b030701d600c4ffe80040010001cf02a3038805a207f50a0c0ace0a3f094a071104c2027a0046fe3bfd1dfde6ff8b014a030504a9056105bd05ee054a043502ba021e019c012000ab003dffdbff6bff44ff68ff96ffce0097019f029502f7031702dd01d200b0ff8efe75fd6cfcb5fd0cfd84fe35fef5ffac0002000d0007ffa1ff0dfe78fe30fdf5fdbcfd85fd51fd22fce5fcaffc84fc79fc76fcaafd15fd7afda1fd9dfd8cfd1efc8cfbf8fb68fadefa72fa92fac2faf6fb31fb73fb96fb86fb6ffb34fadbfa84fa5ffa40fa1df9faf9d9f9b9f992f96ff94df92df914f909f917f91eeacdea76ea40ea0be9b4ecf2f0b9f4b0f8b0fca10061033902460067fe73fc87faaef8f6f79df866fafffe05010e040706e709900ad10b4c0a52091907db06a60589050a0576063708250a300c330e230fcf10881114113f10740f940eb50dee0de00df90e210ebd0ffb113d126c1321138513d313ff138212801153102a0f480e5f0d730c920c4a0c360c150b9b0b140a8b09fc095b082806de05d204db03e802f90210014100f20096001effa4ff2cfeb2fe35fd9efcaafbd2fafefa2bf95cf890f7caf729f6b9f64cf5e2f579f510f4a8f43df3b8f30af25bf1adf102f059efb5ef12ee9cee46edf9edb6ed7fed53ed2fed16ecceec7aec26ebd1eb7deb28eacdea76ea40ea0bfa9cfa89fa76fa63fa4dfe130213060909c40b620bf20a8708e60687053003ee030803dc0362027d019900d9013301fd02c3038804440462039f03f5046203dd045d04f8057e0531044a0240003afe70fda9fe56fffd01ae035604db0546056004a7032f01f40176010500ac00d20034ff7eff06ff23ff62fffd0091012101a801ab015601050063ffc6ffd3ffed0004ffe6ff7cfe95fdfffdb3fd7bfde1fe93ff47fff40089008c0026ff69fea9fe2dfdf8fdc9fda0fd99fd36fd16fd10fd0efd1ffd6dfdb8fdfffe3efe22fdabfd38fccdfc6cfc5dfc54fc4bfc37fc05fbd9fbb5fb94fb78fba0fbdcfc16fc4afc65fc1ffbd0fb77fb21faf2fad5fabafaa2fa9cfa89fa76fa63fd77fd3dfd08fd17fd0c010c04e50442036c04860571054a024efeecfdc5007001ad0289025503540522042f031d020a0119003a00e101b10297034e0291022c01cd02020142ff33febb007d024c029301be01b20285033901aafff3fe9dffc9013e00b8fff4002b016701f6016b0011ffb2003c008700b70027005f00cc00d2008b0031ffecffa2ff6aff8e000d0031ffc1ffd4ffc20030fffbff23fec7ff27ffdaffeaff64fef5ff910000ff8afed6fe34fe93ff12ff07fe93fe71fee8ff5aff38feabfe87fe95feabfeaafe53fe55fe5efe64fe59fe30fe18fdfefde4fdd1fe12fe12fdf3fde2fde2fe15fe03fdb2fd68fd69fd97fd96fd59fd20fd48fd71fd77fd3dfd08fd17fe09fe2ffe2bfe06fdfe01fe02da021104450587034dffb9ff1700050063ffa601630426044b025801be00f9ff9dff8200b10196021a02cb027c01b700c60008ff6ffff8011d01b7014101960225018effdfff5e007b00df003800b5022201a70031005600efffacfef90042017e00ce001000b5013d0001feebffce00b60010ffe900ea00cdffc4ff86000fffdaff40ff6c0041005cffc7ffa20003ffceff57ff5aff87ff9affa9ffc1ffa8ff81ff5dff3cff1fff30ff40ff3fff4bff8cff72fef6fedaff26ff22fec5feceff37ff3bfecafeb9fefefeddfe74fea3fef9feb6fe6afeb0feeafe91fe3afe6efea9fe68fe2cfe68fe97fe52fe2cfe52fe4bfe10fe09fe2ffe2bfe068a008600820085e089c18da19182956299439d23a104a4e4a8c5aca5b086b466b847bc27c008c3e8c7c9cba9cf8ad36ad74bdb2bdf0ce2ece6cdeaadee8ef26ef64ffa2ffe1001f005d109b10d921172155319331d1420f424d528b52c963076345738373c183ff843d947b94b9a4f7a535b573b5b1c5efc62dd66bd6a9e6e7e725f763f7a207e007a00760072006e006a00660062005e005a00560052004e004a00460042003e003a00360032002e002a00260022001e001a00160012000e000a0006000200fe00fa00f600f200ee00ea00e600e200de00da00d600d200ce00ca00c600c200be00ba00b600b200ae00aa00a600a2009e009a00960092008e008a008600820085e09ba798d496009a009e00a200a600aa00ae00b200b600ba00be00c200c600ca00ce00d200d600da00de00e200e600ea00ee00f200f600fa00fe00020006000a000e00120016001a001e00220026002a002e00320036003a003e00420046004a004e00520056005a005e00620066006a00672c645961855eb15bde590a56375363508f4dbc4ae848144541426d3f9a3cc639f2371f344b31772ea42bd028fd2629235520821dae1ada1807153312600f8c0cb809e50711043d016afe96fbc3f8eff61bf348f074eda0eacde7f9e526e252df7edcabd9d7d703d430d15cce89cbb5c8e1c60ec33ac066bd93babfb7ecb518b244af71ac9da9c9a6f6a422a14f9e7b9ba798d496009a00ac31aa18a800ac00b000b400b800bc00c000c400c800cc00d000d400d800dc00e000e400e800ec00f000f400f800fc000000040008000c001000140018001c002000240028002c003000340038003c004000440048004c0050005400580055e853cf51b74f9e4d864b6e4955473d4525430c40f43edb3cc33aab3892367a3462324930312e182c0029e827cf25b7239e21861f6e1d551b3d1925170c14f412db10c30eab0c920a7a08620649043102180000fde8fbcff9b7f79ef586f36ef155ef3ded25eb0ce8f4e6dbe4c3e2abe092de7adc62da49d831d618d400d1e8cfcfcdb7cb9ec986c76ec555c33dc125bf0cbcf4badbb8c3b6abb492b27ab062ae49ac31aa18a800ac00c0c7bf64be00c200c600ca00ce00d200d600da00de00e200e600ea00ee00f200f600fa00fe00020006000a000e00120016001a001e00220026002a002e00320036003a003e004200409c3f393dd53c713b0d39aa384636e2357f341b32b731542ff02e8c2d282bc52a6128fd279a263624d2236e220b20a71f431de01c7c1b1819b5185116ed1589142612c2115e0ffb0e970d330bcf0a6c090807a4064104dd0379021600b2ff4efdeafc87fb23f9bff85cf6f8f594f431f2cdf169f005eea2ed3eebdaea77e913e7afe64be4e8e384e220e0bddf59ddf5dc92db2ed9cad866d703d59fd43bd2d8d174d010ceaccd49cbe5ca81c91ec7bac656c4f3c38fc22bc0c7bf64be00c200cc23cb12ca00ce00d200d600da00de00e200e600ea00ee00f200f600fa00fe00020006000a000e00120016001a001e00220026002a002e003200360034ee33dd32cb31b930a72f962e842d722c602b4f2a3d292b2819270825f624e423d222c121af209d1f8b1e7a1d681c561b441a331921180f16fd15ec14da13c812b611a510930f810e700d5e0c4c0b3a0a290917080506f305e204d003be02ac019b0089ff77fe65fd54fc42fb30fa1ef90df7fbf6e9f5d7f4c6f3b4f2a2f190f07fef6dee5bed4aec38eb26ea14e903e7f1e6dfe5cde4bce3aae298e186e075df63de51dd3fdc2edb1cda0ad8f8d7e7d6d5d5c3d4b1d3a0d28ed17cd06acf59ce47cd35cc23cb12ca00ce00df3ade9dde00e200e600ea00ee00f200f600fa00fe00020006000a000e00120016001a001e002200216320c6202a1f8d1ef01e531db61d191c7d1be01b431aa61a09196c18d01833179616f9165c15bf1523148613e9134c12af1212117610d9103c0f9f0f020e650dc90d2c0c8f0bf20b550ab90a1c097f08e2084507a8070c066f05d20535049803fb035f02c20225018800eb004effb2ff15fe78fddbfd3efca1fc05fb68facbfa2ef991f8f4f858f7bbf71ef681f5e4f547f4abf40ef371f2d4f237f19bf0fef061efc4ef27ee8aedeeed51ecb4ec17eb7aeaddea41e9a4e907e86ae7cde730e694e5f7e55ae4bde420e383e2e7e24ae1ade110e073dfd6df3ade9dde00e200ee9bee4dee00f200f600fa00fe00020006000a000e00120011b31165111810ca107d102f0fe20f940f470efa0eac0e5f0e110dc40d760d290cdb0c8e0c410bf30ba60b580b0b0abd0a700a2209d50988093a08ed089f0852080407b70769071c06cf0681063405e60599054b04fe04b00463041603c8037b032d02e00292024501f701aa015d010f00c200740027ffd9ff8cff3efef1fea3fe56fe09fdbbfd6efd20fcd3fc85fc38fbeafb9dfb50fb02fab5fa67fa1af9ccf97ff931f8e4f897f849f7fcf7aef761f713f6c6f678f62bf5def590f543f4f5f4a8f45af40df3bff372f325f2d7f28af23cf1eff1a1f154f106f0b9f06cf01eefd1ef83ef36eee8ee9bee4dee00f200f653f62af600fa00fe00020006000a0009d609ad098309590930090608dd08b3088908600836080c07e307b907900766073c071306e906bf0696066c0643061905ef05c6059c05720549051f04f604cc04a20479044f042503fc03d203a9037f0355032c030202d802af0285025c0232020801df01b5018b01620138010f00e500bb00920068003e0015ffebffc2ff98ff6eff45ff1bfef1fec8fe9efe75fe4bfe21fdf8fdcefda4fd7bfd51fd28fcfefcd4fcabfc81fc57fc2efc04fbdbfbb1fb87fb5efb34fb0afae1fab7fa8efa64fa3afa11f9e7f9bdf994f96af941f917f8edf8c4f89af870f847f81df7f4f7caf7a0f777f74df723f6faf6d0f6a7f67df653f62af600fa009d8b99d296e0953d953d96e099d29d8ba180a54ba8caac11af54b2c3b671ba50be3cc217c5d3c97bcd28d0f0d4dbd8dbdcdae0c7e49be860ec26effbf3e0f7cafba7ff6a031206a70a370dca115d14e618561ba51ed321e824f027ef2ae22dbd30753304356b37b539ea3c0d3e1a400441c3435244b745fb47244836492949f44a8e4af64b334b4e4b4e4b334af64a8e49f449294836472445fb44b7435241c340043e1a3c0d39ea37b5356b330430752dbd2ae227ef24f021e81ed31ba5185614e6115d0dca0a3706a70312ff6afba7f7caf3e0effbec26e860e49be0c7dcdad8dbd4dbd0f0cd28c97bc5d3c217be3cba50b671b2c3af54ac11a8caa54ba1809d8b99d296e0953da7f2a47aa24fa1a4a1a4a24fa47aa7f2abdbaf75b282b531b7dabacdbe30c1efc5c8c97fccfbd052d3b3d748db1cdf1ce31ce6f5ea9fee2cf1bcf568f933fd0700c1044c07a30ad90e051136146817881a7d1d391fc02220246c26aa28d62ae12cba2e5c2fcf311e3256337a34863571363436d0374c37b238093852388c38b438cb38d638d938da38da38d938d638cb38b4388c3852380937b2374c36d0363435713486337a3256311e2fcf2e5c2cba2ae128d626aa246c22201fc01d391a7d1788146811360e050ad907a3044c00c1fd07f933f568f1bcee2cea9fe6f5e31cdf1cdb1cd748d3b3d052ccfbc97fc5c8c1efbe30bacdb7dab531b282af75abdba7f2a47aa24fa1a4b639b338b20bb1eeb1eeb20bb338b639ba0cbd4abf9ec16bc330c55cc83bcbbccf70d2e2d5ebd8b6db91dec5e271e671ea6fee24f17ef4a5f7d2fb31fec9027205ec090f0bd90e6d10f1137d160b187b1aab1c891e221f8b20dc221f234d2457253225dd266326d0272f278327c927ff2824283c284b2855285c28622865286628672867286728672867286728672867286628652862285c2855284b283c282427ff27c92783272f26d0266325dd25322457234d221f20dc1f8b1e221c891aab187b160b137d10f10e6d0bd9090f05ec0272fec9fb31f7d2f4a5f17eee24ea6fe671e271dec5db91d8b6d5ebd2e2cf70cbbcc83bc55cc330c16bbf9ebd4aba0cb639b338b20bb1eec7a7c565c50cc50cc50cc50cc565c7a7cb4fcdf0cf4ad01ad0e2d211d41fd731daa0dd98dfe5e1d9e3e2e672e9d1edd1f1cef53cf80dfa88fd0dffe403200679097f0bf30de60f8f112412c3146515e2171317f318961915198419ea1a431a881ab71ad31ae51af11afa1b001b051b081b091b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b0a1b091b081b051b001afa1af11ae51ad31ab71a881a4319ea19841915189617f3171315e2146512c311240f8f0de60bf3097f06790320ffe4fd0dfa88f80df53cf1ceedd1e9d1e672e3e2e1d9dfe5dd98daa0d731d41fd211d0e2d01acf4acdf0cb4fc7a7c565c50cc50cd9d8d891d889d889d889d889d891d9d8dd2fdee9df5edf88dfafe009e117e372e665e898e9eceadfebe9ed8df063f463f85ffb50fd4bfed5006b0270050c07da0a230ba50c980d480de80e900f3b0fc810231054106e107e108a1094109c10a110a310a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a410a310a1109c1094108a107e106e105410230fc80f3b0e900de80d480c980ba50a2307da050c0270006bfed5fd4bfb50f85ff463f063ed8debe9eadfe9ece898e665e372e117e009dfafdf88df5edee9dd2fd9d8d891d889d889e940e8d8e8d8e8d8e8d8e8d8e8d8e940ec0aecc8ecd6ecd8ecd9ece1ed28ee8cf0b8f1eef25ff298f2ddf38af58df98dfd83ffae00a8014001e102e6049a069107e0087108aa08c908e208fd091a092d09350938093809390939093909390939093909390939093909390939093909390939093909390939093909390939093909390939093909390939093909390939093909390939093909390939093909390939093909390939093909390939093909390939093909390939093809380935092d091a08fd08e208c908aa087107e00691049a02e601e1014000a8ffaefd83f98df58df38af2ddf298f25ff1eef0b8ee8ced28ece1ecd9ecd8ecd6ecc8ec0ae940e8d8e8d8e8d8f37ef374f374f374f374f374f374f37ef570f593f594f594f594f594f599f614f742f7a0f7acf7b0f7b4f7d1f8d4fcd400c201ee022b0241025b029d0357044e04bb04d004d304d404d504d504d604d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d704d604d504d504d404d304d004bb044e0357029d025b0241022b01ee00c2fcd4f8d4f7d1f7b4f7b0f7acf7a0f742f614f599f594f594f594f594f593f570f37ef374f374f374f89cf89cf89cf89cf89cf89cf89cf89cf98ef98ff98ff98ff98ff98ff98ff99ef9f7fa00fa00fa00fa00fa01fa42fe42021d027502790279027a027e02a002dc02e702e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e802e702dc02a0027e027a027902790275021dfe42fa42fa01fa00fa00fa00fa00f9f7f99ef98ff98ff98ff98ff98ff98ff98ef89cf89cf89cf89cd247d04dcee5ce00ce00cee5d04dd247d4cfd7e2db50df06e2ebe6e7eae7eee4f2c1f665f9befcdaffa702200440060c077b089f09810a200a740a9a0aa60a960a600a1509c4096c09040898083007cc076e071f06d6069e06800681069606c10716078007fb0889092e09d80a870b3f0bfb0ca60d4d0df60e980f250fa51017107910be10f0110c110c10f010be107910170fa50f250e980df60d4d0ca60bfb0b3f0a8709d8092e088907fb0780071606c1069606810680069e06d6071f076e07cc083008980904096c09c40a150a600a960aa60a9a0a740a200981089f077b060c04400220ffa7fcdaf9bef665f2c1eee4eae7e6e7e2ebdf06db50d7e2d4cfd247d04dcee5ce00d307d106cfa1ceaeceaecfa1d106d307d5b3d8e1dc44dff3e3eae7eaebd2efc1f39ff742faacfdfc011503eb068708f50b270d190edb106d11bf12e413d81495151415601573153d14d8143d135d125911320fef0e9a0d4a0c020ac3099d089707ac06cd0610056b04c9042e039e0312027d01e7015900c00024ff9aff20fe9ffe32fde4fdb0fd8cfd8cfdb0fde4fe32fe9fff20ff9a002400c0015901e7027d0312039e042e04c9056b061006cd07ac0897099d0ac30c020d4a0e9a0fef11321259135d143d14d8153d157315601514149513d812e411bf106d0edb0d190b2708f5068703eb0115fdfcfaacf742f39fefc1ebd2e7eae3eadff3dc44d8e1d5b3d307d106cfa1ceaee1b7df48dd87dc5cdc5cdd87df48e1b7e4dfe896ec7ef07ef47ef857fbe0ff1001dc0435061e07a908c8097f09e80a1009f2099b09170867079106b005be04b903ae02c401f7013e00ab0058004f007900d801820265037704a305e3072b085f09700a440ad20b180b0c0a9b09d108c5077c05fd046202bf011aff85fe17fcdafbc9faf8fa6efa25fa25fa6efaf8fbc9fcdafe17ff85011a02bf046205fd077c08c509d10a9b0b0c0b180ad20a440970085f072b05e304a303770265018200d80079004f005800ab013e01f702c403ae04b905be06b0079108670917099b09f20a1009e8097f08c807a9061e043501dcff10fbe0f857f47ef07eec7ee896e4dfe1b7df48dd87dc5ccda5cc40cb77ca6cca6ccb77cc40cda5cfb1d21dd4acd7afdb0fde9ee23de61eea1bee07f207f5fef9bdfd6a00e3041c070209b90c350e4d1006119c12f1139b143314b914cf1485143513db131e1247117a10970f860e840da00cad0bc90b010a5909d80958090208cb08960885088d089d08c20906093b097509cc0a260a5a0a760ac00af20ae00ae00af20ac00a760a5a0a2609cc0975093b090608c2089d088d0885089608cb0902095809d80a590b010bc90cad0da00e840f861097117a1247131e13db1435148514cf14b91433139b12f1119c10060e4d0c3509b90702041c00e3fd6af9bdf5fef207ee07ea1be61ee23dde9edb0fd7afd4acd21dcfb1cda5cc40cb77ca6ce40ce15ede7bdb38db38de7be15ee40ce7a8eba8ee77f026f1b0f2cef34df323f276f1d4f195f1dff258f313f4bcf764fa0bfc5dfed5015c03360462056a06370679065a060b05d605f20644069f07460835091409e40abc0ba60c9d0d520da40dc30dee0ded0d590c590b640a88096d0810076407770785079c084809680a750b360bcc0c5c0cc20cc20c5c0bcc0b360a7509680848079c0785077707640810096d0a880b640c590d590ded0dee0dc30da40d520c9d0ba60abc09e4091408350746069f064405f205d6060b065a06790637056a04620336015cfed5fc5dfa0bf764f4bcf313f258f1dff195f1d4f276f323f34df2cef1b0f026ee77eba8e7a8e40ce15ede7bdb38e0a4dea7db4dd7f3d7f3db4ddea7e0a4e258e4a7e73eea63ee60f260f550f75cf941fb18fca8fe27ffcf017402a5030a02dc02f403d1050f060b069306bd06c006f307bc08c3097409da0a720b2a0b8f0bbf0c220cd30d5d0d4d0cd10c490bad0af20a4a099d088206fc05a804bd03d902c6020001cc01bb019001a10210027e02b002d3030d033f033f030d02d302b0027e021001a1019001bb01cc020002c603d904bd05a806fc0882099d0a4a0af20bad0c490cd10d4d0d5d0cd30c220bbf0b8f0b2a0a7209da097408c307bc06f306c006bd0693060b050f03d102f402dc030a02a50174ffcffe27fca8fb18f941f75cf550f260ee60ea63e73ee4a7e258e0a4dea7db4dd7f3d05ed01bcebacc87cc87cebad01bd05ed14ed3a7d636d8cfdb9adedde1f7e4f3e815ebd9efd9f37cf642f91afcba0081036705f408a80b420d991009125c143e159b16ef186b19c21ab41b4c1b8d1b931bb31bab1b4f1a9c198d183d172f163214a8129c10ab0ef60d320b4109520756052f034001c10039fe8afd0efbbefa98f9f6f99ff903f859f859f903f99ff9f6fa98fbbefd0efe8a003901c10340052f075609520b410d320ef610ab129c14a81632172f183d198d1a9c1b4f1bab1bb31b931b8d1b4c1ab419c2186b16ef159b143e125c10090d990b4208a805f403670081fcbaf91af642f37cefd9ebd9e815e4f3e1f7dedddb9ad8cfd636d3a7d14ed05ed01bcebacc87d301d21ad166cfc5cfc5d166d21ad301d519d7a2d9e7dcd6e02fe39fe70eeac7ee99f27cf67cfa4cfde00189055208860b6f0e9e1169139315e11811199b1afc1c681d701df31e901ee91eb41e611e121d3a1c021adb197917c315fc140e11ce0f7a0d300aae082d05a303060063fdedfbaaf953f6fef50ff338f160eff8eeeaedc5ece8ec71ec39ec39ec71ece8edc5eeeaeff8f160f338f50ff6fef953fbaafded0063030605a3082d0aae0d300f7a11ce140e15fc17c319791adb1c021d3a1e121e611eb41ee91e901df31d701c681afc199b181115e1139311690e9e0b6f088605520189fde0fa4cf67cf27cee99eac7e70ee39fe02fdcd6d9e7d7a2d519d301d21ad166cfc5f96df67bf30def0def0df30df67bf96dfc0aff0f020905030743083507cc06ac05690417026501050027001b008300de00e700ec00d700ac0095fffaff0dfe4ffe11fdd4fd34fc9dfca5fd78fe58ff1dff84ffe80082010d0191022902b002ee03050343032f0329033b02e002820254023501c700d6fff3ff6dfee4fe0cfd4cfce0fc76fbdcfb4efb4efbdcfc76fce0fd4cfe0cfee4ff6dfff300d601c702350254028202e0033b0329032f0343030502ee02b002290191010d0082ffe8ff84ff1dfe58fd78fca5fc9dfd34fdd4fe11fe4fff0dfffa009500ac00d700ec00e700de0083001b0027010502650417056906ac07cc0835074305030209ff0ffc0af96df67bf30def0df790f599f2e8eee8eee8f2e8f599f790f92afaf8fc68fdb0002003b905b106840666061e0572051e051e0511047d038902450111ffadfea4fe19fe0bfdf1fe09fe5efec3fecafeb2ff21002d011d01b101f1023e027d02b302f60390044804df04db04990400039f034c02a301fa017e00ee000dfedafdebfd66fd03fc85fc47fc40fc08fb65facffacffb65fc08fc40fc47fc85fd03fd66fdebfeda000d00ee017e01fa02a3034c039f0400049904db04df0448039002f602b3027d023e01f101b1011d002dff21feb2fecafec3fe5efe09fdf1fe0bfe19fea4ffad011102450389047d0511051e051e0572061e0666068405b103b90020fdb0fc68faf8f92af790f599f2e8eee8fc15f91af574f174f174f574f91afc15fe9a014c03c405c206bc06980526031d0110fefefc80fa16f949faf7fcdefe72ff9300ce020b03460421045603df033d02a301dc00bfffc0ff76fff600b8015e01a501e7024d02a702b902800242020801b400fcffebff08fe7cfe66fe87fec1fedcfedefef5ff14ff55ff71ff64ff70ff78ff50febdfe38fe38febdff50ff78ff70ff64ff71ff55ff14fef5fedefedcfec1fe87fe66fe7cff08ffeb00fc01b402080242028002b902a7024d01e701a5015e00b8fff6ff76ffc000bf01dc02a3033d03df045604210346020b00ceff93fe72fcdefaf7f949fa16fc80fefe0110031d0526069806bc05c203c4014cfe9afc15f91af574f174f85df544f181ed81ed81f181f544f85dfb12fde700a80393067c088a090e0851074b069a058f04070270016e0099ff8cfe6ffd85fc9cfb5bfa7cfb23fc29fd47fe56ff1cff8bfff200cc01d9029902ce029102390204020e023c029a030c0351035c02ff026401d4016600c8ffeeff36fea9fe39fdf7fdd8fdf4fe3afe9fff2dffc7001efffdffcfffcffffd001effc7ff2dfe9ffe3afdf4fdd8fdf7fe39fea9ff36ffee00c8016601d4026402ff035c0351030c029a023c020e02040239029102ce029901d900ccfff2ff8bff1cfe56fd47fc29fb23fa7cfb5bfc9cfd85fe6fff8c0099016e02700407058f069a074b0851090e088a067c039300a8fde7fb12f85df544f181ed81fa35f6e8f2e8ef0cef0cf2e8f6e8fa35fcb9ff78028b059407ee090808a9074405950406027801270069007900ef013d016101e80273027b0178ffbcfe08fcc4fbe7faebf968f7d1f741f8d9fb54fd7cff3800ba024b03d1050005b905fd05aa04d803b80278017700d20075004d0026ffedffbdffc2ffe5fff8ffbdff5cff0cfeebfed3fe74fe00fe00fe74fed3feebff0cff5cffbdfff8ffe5ffc2ffbdffed0026004d007500d20177027803b804d805aa05fd05b9050003d1024b00baff38fd7cfb54f8d9f741f7d1f968faebfbe7fcc4fe08ffbc0178027b027301e80161013d00ef007900690127027804060595074408a9090807ee0594028bff78fcb9fa35f6e8f2e8ef0cfae5f803f473f073f073f473f803fae5fd04ff4a01be043106380750071305e7044b02c701630057ffbaffafffb4ff9eff6eff94fff500340013ffc2ff87ffb4002b009f0073ffd4ff3dfefdfefdfee1fea4fe97fe8dfe5afdf1fe8b0082025f038503e403b8039b03bb03df03a702d8018f0032ff38fec2fea5fe68fe0bfdf8fe3ffe81fe6cfe3efe3efe6cfe81fe3ffdf8fe0bfe68fea5fec2ff380032018f02d803a703df03bb039b03b803e40385025f0082fe8bfdf1fe5afe8dfe97fea4fee1fefdfefdff3dffd40073009f002bffb4ff87ffc200130034fff5ff94ff6eff9effb4ffafffba0057016302c7044b05e7071307500638043101beff4afd04fae5f803f473f073fa65f720f36fef6fef6ff36ff720fa65fcf2ff7f022804d006da07ad06fb057603a801e40015fe8dfdbbfddefe41fe85feb5ff29ffd7006f009e00630007fff00026003dffd2ff5bff8e00a30220035d042504f005df067a06470569046b033d019effb0fd9bfbbefa13f944fa37fb8ffcd1fdf6ff110021013001dd01fe01b301130031ff38fe97fe97ff380031011301b301fe01dd01300021ff11fdf6fcd1fb8ffa37f944fa13fbbefd9bffb0019e033d046b05690647067a05df04f00425035d022000a3ff8eff5bffd2003d0026fff000070063009e006fffd7ff29feb5fe85fe41fddefdbbfe8d001501e403a8057606fb07ad06da04d00228ff7ffcf2fa65f720f36fef6ff771f3f7eff7ec36ec36eff7f3f7f771fa74fd5e006f03ab0696083e08450769063f04c80300016a0098008000a300b000b300de0113011d010000cb0081004f0025ffd2ff57fefdff2effec00e901a501f8024b02ce036e03ff047a04fa05760598054304bc040202de0145ff8ffe07fc87fb3ffa4ef9a2f8fdf8d0fa4ffcc5fee2fff5fff6ffb5ffb5fff6fff5fee2fcc5fa4ff8d0f8fdf9a2fa4efb3ffc87fe07ff8f014502de040204bc05430598057604fa047a03ff036e02ce024b01f801a500e9ffecff2efefdff57ffd20025004f008100cb0100011d011300de00b300b000a300800098016a030004c8063f07690845083e069603ab006ffd5efa74f771f3f7eff7ec36af8aaef1ae8cae4fae4fae8caef1af8ab053b14eb279b3d5b55db714b8f9bb0dbd47bfabc235c4e6c7bccab5cdccd103d45ad7c9db50def0e2a3e668ea3eee1ff20df603fa00fe000200060009fd0df311e115c219981d5d211024b028372ba62efd3234354b38443b1a3dcb405542b944f3470748ec4aa34c2b4d874eb24fad5076510f517451b151b15174510f50764fad4eb24d874c2b4aa348ec470744f342b940553dcb3b1a3844354b32342efd2ba6283724b021101d5d199815c211e10df309fd06000200fe00fa00f603f20dee1fea3ee668e2a3def0db50d7c9d45ad103cdcccab5c7bcc4e6c235bfabbd47bb0db8f9b714b55db3d5b279b14eb053af8aaef1ae8cae4fd884d6cdd59bd4e5d4e5d59bd6cdd884daaedd57e065e3c9e76feb48ef3ff33af72bfb06febc02340559081d0a7b0c670dd30ec40f3b0f3a0ebf0dd00c780ac408c3068304140185feeafc4ff9cdf778f566f3a4f23cf13df0b1f0a5f115f20cf384f577f7e1fab1fddd0157051108f70cf310f314e118aa1c3e1f8c22872518273a28dc29f22a7d2a7d29f228dc273a251822871f8c1c3e18aa14e110f30cf308f705110157fdddfab1f7e1f577f384f20cf115f0a5f0b1f13df23cf3a4f566f778f9cdfc4ffeea01850414068308c30ac40c780dd00ebf0f3a0f3b0ec40dd30c670a7b081d05590234febcfb06f72bf33aef3feb48e76fe3c9e065dd57daaed884d6cdd59bd4e5ba13b85ab68db4e4b4e4b68db85aba13bbe4be59c119c3f8c710caabce7bd20ad5a1d978dd6ce116e47ae7d5eb0dee04f0acf33af59ef7a3f93ffadcfc83fdccfeabff59001500bd0121015601a8022d02e303e1054106c9085d0a2b0c520ed911a214ac17f11b7e1f44232227222b0c2ebb323d35b838fd3be93ea9411e434244f0465c479b488d488d479b465c44f04342411e3ea93be938fd35b8323d2ebb2b0c272223221f441b7e17f114ac11a20ed90c520a2b085d06c9054103e102e3022d01a80156012100bd0015ff59feabfdccfc83fadcf93ff7a3f59ef33af0acee04eb0de7d5e47ae116dd6cd978d5a1d20ace7bcaabc710c3f8c119be59bbe4ba13b85ab68db4e4d828d472d072cd41cd41d072d472d828da44db1cdb36db5adc45de2ae091e313e566e7caea1cec44ee29efbef126f27cf417f669f913fb94fd7efe9fff6e003d019e03c90681091d0b0c0c3d0ce70d7c0e0a0ea90f58100310e8122513ee15d4173417a6170b15cb149113f314351545169d178517ba172f1638157b15471595160e168516ed1754175416ed1685160e15951547157b1638172f17ba1785169d1545143513f3149115cb170b17a6173415d413ee122510e810030f580ea90e0a0d7c0ce70c3d0b0c091d068103c9019e003dff6efe9ffd7efb94f913f669f417f27cf126efbeee29ec44ea1ce7cae566e313e091de2adc45db5adb36db1cda44d828d472d072cd41c4a0c0c8bdb4bbd2bbd2bdb4c0c8c4a0c871cbdcce95d09cd1e1d2a6d305d34ed3bbd48bd5edd80edadcde43e213e60eea0eedeaf181f4b1f768f9a6fb77fd04fe70ffde0179036005a708540b5a0ea6120a154a18291a901c6c1dcf1ecc1f781fe32032208020f721b322d8245d2630282629ef2b512c252c5a2c042b402a2428f027c426d6265c265c26d627c428f02a242b402c042c5a2c252b5129ef28262630245d22d821b320f7208020321fe31f781ecc1dcf1c6c1a901829154a120a0ea60b5a085405a703600179ffdefe70fd04fb77f9a6f768f4b1f181edeaea0ee60ee213de43dadcd80ed5edd48bd3bbd34ed305d2a6d1e1d09cce95cbdcc871c4a0c0c8bdb4bbd2e425e0bddcbdd90dd90ddcbde0bde425e733ea6bedc5f05ef213f3d1f54df62ff6e4f7f8f96afb0ffcd9ff0b014603120510073108d609d40a0409d609a9091c084507a80722066e05df05e8063406b4077d082d089f08a107ff07760751070b0689063205f305cb05ce05d906010641067206ab06bb06b306ab0620055104140263013800d500a700a700d50138026304140551062006ab06b306bb06ab06720641060105d905ce05cb05f306320689070b0751077607ff08a1089f082d077d06b4063405e805df066e072207a80845091c09a909d60a0409d408d60731051003120146ff0bfcd9fb0ff96af7f8f6e4f62ff54df3d1f213f05eedc5ea6be733e425e0bddcbdd90ddb68d9cfd9fdd5fdd5fdd9fdd9cfdb68de3bdfc9e1afe4d5e836ea2eed70f111f323f5daf8fdfb89fde300d7032f050b073e09360b430cdf0e630fe010e9120d1299132c13b613d2140013b61322128a121e110f0fdd0f610e470cd60c070b990a1f08e608dd0754060605c1044c02d801ce0064fefafde7fd0ffbf1fb24fa58f970f8e7f897f8a6f8a6f897f8e7f970fa58fb24fbf1fd0ffde7fefa006401ce02d8044c05c10606075408dd08e60a1f0b990c070cd60e470f610fdd110f121e128a132213b6140013d213b6132c1299120d10e90fe00e630cdf0b430936073e050b032f00d7fde3fb89f8fdf5daf323f111ed70ea2ee836e4d5e1afdfc9de3bdb68d9cfd9fdd5fdeec2edc2ef6aeb6aeb6aef6aedc2eec2f0bdf14ef1f2f380f533f602f6cbf886f937f9eafb7afc22fca4fe12ff08ff6d00d301fd02510377049d04c30564066a06f206e507760829082b07c907f9081f073107500764066405e506190586050b053204b104aa0420042f04ae03970383035d02d10294025701c3018a011f00a100af005e006f00560056006f005e00af00a1011f018a01c30257029402d1035d0383039704ae042f042004aa04b10532050b0586061905e50664076407500731081f07f907c9082b0829077606e506f2066a056404c3049d0377025101fd00d3ff6dff08fe12fca4fc22fb7af9eaf937f886f6cbf602f533f380f1f2f14ef0bdeec2edc2ef6aeb6ab28fb198b0c9b035b035b0c9b198b28fb38fb4a5b5c4b6f6b83bb9b6bb70bd7bbfd2c263c51ac7deca95cd4ad00ad2ebd5fbd945dcc1e06ce42be7f9ebc4ef78f310f6a6fa55fe21020b06040a040e0111e715a819381c951fd3230d265029a22cf83044336e3665391b3b8c3dbf3fca41b4438a4551471348bf4a3b4b6f4c534cee4d4a4d774d844d844d774d4a4cee4c534b6f4a3b48bf47134551438a41b43fca3dbf3b8c391b3665336e30442cf829a22650230d1fd31c95193815a811e70e010a040604020bfe21fa55f6a6f310ef78ebc4e7f9e42be06cdcc1d945d5fbd2ebd00acd4aca95c7dec51ac263bfd2bd7bbb70b9b6b83bb6f6b5c4b4a5b38fb28fb198b0c9b035d57fd3ccd26fd18bd18bd26fd3ccd57fd75ad962db9bde31e130e4a2e867ec5ff05ff44ff819fbc9ff71032e06fa0ab50e3d1172144316b618db1ac31c741def1f221ffe2062204a1fc61efe1e161d151be91a8218c216aa144d11d90f650d010ab2086d062b03d0015afedbfc72fa43f857f6a7f524f3bff262f113efe7eefcee55edf5edc1edacedacedc1edf5ee55eefcefe7f113f262f3bff524f6a7f857fa43fc72fedb015a03d0062b086d0ab20d010f6511d9144d16aa18c21a821be91d151e161efe1fc6204a20621ffe1f221def1c741ac318db16b6144311720e3d0ab506fa032eff71fbc9f819f44ff05fec5fe867e4a2e130de31db9bd962d75ad57fd3ccd26fd18bb3b0b252b14bb0a2b0a2b14bb252b3b0b53fb708b90cbb62be12c11ec474c7f9cb97cf3ad2ded688da47de29e21fe61fea0aedcdf15af4bbf7fbfb2dfe580173046d073909cf0c2c0e5c106f127a1480167a18611a1d1bab1d131e6f1fd4214822c5244525b72713285329742a8f2bad2cd42e032f2a302c310431b2324332cc334c33c33423345b345b342333c3334c32cc324331b23104302c2f2a2e032cd42bad2a8f29742853271325b7244522c521481fd41e6f1d131bab1a1d1861167a1480127a106f0e5c0c2c09cf0739046d0173fe58fb2df7fbf4bbf15aedcdea0ae61fe21fde29da47d688d2decf3acb97c7f9c474c11ebe12bb62b90cb708b53fb3b0b252b14bb0a2b858b509b27fb105b105b27fb509b858bc17c014c414c7eecb7bcec1d1cad4b1d783da46dcfbdfa6e252e505e7b9ea6bed16efccf295f572f848fafcfd7dffc401d103ae0569070d08a60a4e0c170df70fdf11ca13bf15c617d719eb1bff1e1f204a22742478263427882874290429562985299f29b429db2a232a862af32b642bd42c3f2c962cc82cc82c962c3f2bd42b642af32a862a2329db29b4299f29852956290428742788263424782274204a1e1f1bff19eb17d715c613bf11ca0fdf0df70c170a4e08a6070d056903ae01d1ffc4fd7dfafcf848f572f295efcced16ea6be7b9e505e252dfa6dcfbda46d783d4b1d1cacec1cb7bc7eec414c014bc17b858b509b27fb105dc9ed911d631d473d473d631d911dc9ee07be47be858ebd6eee9f1b0f43ff695f8b7fab4fc95fe61000b018602c103bb048f05720677079208a5098b0a210a4709fd096308a907f2074e06d8069606780674068706bd0710076a07c4082708a1093209d70a720ad90ae20a7c09b908bb07a706a705de055804f6049c0443040e0409041f0430043504350430041f0409040e0443049c04f6055805de06a707a708bb09b90a7c0ae20ad90a7209d7093208a1082707c4076a071006bd068706740678069606d8074e07f208a9096309fd0a470a21098b08a5079206770572048f03bb02c10186000bfe61fc95fab4f8b7f695f43ff1b0eee9ebd6e858e47be07bdc9ed911d631d473f050ee7dea7de6b3e6b3ea7dee7df050f0def1eef33bf3aaf399f45df625f7fbf96afafefcf6fed300350126017e00e3ffa0fec2fefa000d016c02cc03af035b01a5ff89fe45fe32fee1ffeb010c01f5027302db0393046b04cd0488041c042c04f3065e081d09950a3509f5092f081906c105b605e5076f09100948080906a6061f0628060705b905b906070628061f06a6080909480910076f05e505b606c10819092f09f50a350995081d065e04f3042c041c048804cd046b039302db027301f5010cffebfee1fe32fe45ff8901a5035b03af02cc016c000dfefafec2ffa000e3017e01260035fed3fcf6fafef96af7fbf625f45df399f3aaf33bf1eef0def050ee7dea7de6b3e753e5c8e1c8ddd3ddd3e1c8e5c8e753e7abe8d4ea59eadceaceebc9edf3f00df197f359f5b8f80bf9bcfadffb82fb59fa94fa22faadfc10fdd4ffb20122014d0008fe5cfd90fdf4ff0e00780202035b044d052b066007bf08a008ca08cb094a0a790c310e1a0fb910a910e210920fd20ec40e150e9f105e120a1251113e10040f810f800f6e0f3d0f3d0f6e0f800f811004113e1251120a105e0e9f0e150ec40fd2109210e210a90fb90e1a0c310a79094a08cb08ca08a007bf0660052b044d035b02020078ff0efdf4fd90fe5c0008014d0122ffb2fdd4fc10faadfa22fa94fb59fb82fadff9bcf80bf5b8f359f197f00dedf3ebc9eaceeadcea59e8d4e7abe753e5c8e1c8ddd3b46fb30bb00fad24ad24b00fb30bb46fb52ab6b8b8b9ba1fbb2dbd07bfcac29dc52ec80ccb6fcedcd1efd4d2d7a1da18dc31de75e164e4f6e8d8ecd8f09bf39bf5c7f7cbfa5dfd97012704eb08db0cb91040139e17311ae51e41210e239d2667299d2d1d309e33d1367738913a473ba23ca53db13f4d418643a544e24533453b458346014662468a468a466246014583453b453344e243a541863f4d3db13ca53ba23a473891367733d1309e2d1d299d2667239d210e1e411ae51731139e10400cb908db04eb0127fd97fa5df7cbf5c7f39bf09becd8e8d8e4f6e164de75dc31da18d7a1d4d2d1efcedccb6fc80cc52ec29dbfcabd07bb2dba1fb8b9b6b8b52ab46fb30bb00fad24d79fd4a3d274d130d130d274d4a3d79fdb1bdef1e2e3e6e3eac7ee8bf218f574f892fb79fe1d0084029c045f05c406bd073c073106a205a2044902bb0110ff60fdc0fc3ffae8f9c9f8eff85ff80ff80cf84bf8c5f973fa57fb7bfcedfec300fe0388063e09000bac0e2910651265142615a516e117e318b8195c19df1a4a1aa51af71b3b1b6f1b8c1b8c1b6f1b3b1af71aa51a4a19df195c18b817e316e115a51426126510650e290bac0900063e038800fefec3fcedfb7bfa57f973f8c5f84bf80cf80ff85ff8eff9c9fae8fc3ffdc0ff60011002bb044905a206a20731073c06bd05c4045f029c0084fe1dfb79f892f574f218ee8beac7e6e3e2e3def1db1bd79fd4a3d274d130e344e032dddedc45dc45dddee032e344e6a3e9f6ed68f120f4e7f8e7fccc001802c404c706180732085009420a260ac10acc0a940a3109a9095d093608cc08280702053903290106fed6fcebfb1af91bf70cf4ebf2daf159f08ff079f14df2b3f46bf68ef8f9fbb1fee2025705bf08fb0bb20dcd0f94110c12441379146914e3150814c6144e14171417144e14c6150814e3146913791244110c0f940dcd0bb208fb05bf0257fee2fbb1f8f9f68ef46bf2b3f14df079f08ff159f2daf4ebf70cf91bfb1afcebfed60106032905390702082808cc0936095d09a90a310a940acc0ac10a26094208500732061804c702c40018fcccf8e7f4e7f120ed68e9f6e6a3e344e032dddedc45e3a3e039dd93dbc9dbc9dd93e039e3a3e757eaf4ee9ef27df656fa56fe31018b047006e008cd0aa80ca10e81105111d312ab13211354134b1359137a1363132a1295117c103a0ed90d4c0bc90a1d07e1052101d9fe36fadcf806f5d1f467f385f2eff2d8f324f3cff4f8f668f7d8f930fa28facbfb87fc77fda9ff4a00e90232033803c503ee0411041103ee03c50338023200e9ff4afda9fc77fb87facbfa28f930f7d8f668f4f8f3cff324f2d8f2eff385f467f5d1f806fadcfe3601d9052107e10a1d0bc90d4c0ed9103a117c1295132a1363137a1359134b1354132112ab11d310510e810ca10aa808cd06e00470018bfe31fa56f656f27dee9eeaf4e757e3a3e039dd93dbc9dca5d8d2d5b3d3cad3cad5b3d8d2dca5e09ee483e82eeba1eecbf1b4f465f6f5f978fbfcfe9b0165045c076d0a640d060f3210eb12431358144715331633176218d11a891c731e6f20612225237d2403236221861eab1b3f17a4141310960d2c09da069e036e0035fcdff95bf5a6f1bbedbbea03e6f6e4f7e41be42ce4cfe5afe693e757e7f0e848e848e7f0e757e693e5afe4cfe42ce41be4f7e6f6ea03edbbf1bbf5a6f95bfcdf0035036e069e09da0d2c1096141317a41b3f1eab218623622403237d222520611e6f1c731a8918d117621633153314471358124310eb0f320d060a64076d045c0165fe9bfbfcf978f6f5f465f1b4eecbeba1e82ee483e09edca5d8d2d5b3d3cae1cfddcfda6fd860d860da6fddcfe1cfe5a6e8f2eb8eeda1ef5cf0fbf2aef49bf6c2f925fbaefe4e00e2036905e5085b0ad60d4a0f9411a4136114ce15f91704180318f819d81a9e1b521bfe1c851ca51c101a9f186e15d01314107e0e290c0e0a120819060a03bb0113fdf8fa5ff671f27ceef6ec3aea87e9d3e9d5ea30eaa6eb10eb70ebb7ebe7ebe7ebb7eb70eb10eaa6ea30e9d5e9d3ea87ec3aeef6f27cf671fa5ffdf8011303bb060a08190a120c0e0e29107e131415d0186e1a9f1c101ca51c851bfe1b521a9e19d818f81803170415f914ce136111a40f940d4a0ad6085b05e5036900e2fe4efbaef925f6c2f49bf2aef0fbef5ceda1eb8ee8f2e5a6e1cfddcfda6fd860dff2dbf2d875d63ad63ad875dbf2dff2e3b7e6dce916ea9eebeaed61ef1ef134f39ef62bf869fa21fb3dfbe7fc5dfcfefe24ffe201f5041c063c082b09c40b120c390d510e510f52108411e913451459150f153c14c513c21286115210330f190e080ce20b8109d307e805c6036900fefee0fd58fc73fc3ffcb7fd92fe76ff41fff6009f0114014e014e0114009ffff6ff41fe76fd92fcb7fc3ffc73fd58fee000fe036905c607e809d30b810ce20e080f1910331152128613c214c5153c150f1459134511e910840f520e510d510c390b1209c4082b063c041c01f5ffe2fe24fcfefc5dfbe7fb3dfa21f869f62bf39ef134ef1eed61ebeaea9ee916e6dce3b7dff2dbf2d875d63ae4a9e1b5df15dd25dd25df15e1b5e4a9e81aec1af00af3cff7b1fbb0ff34020e04850684079c07b4071905fd045e028e0104ffedfef7fe41fe1afe8aff440052020e0474071809dd0cea0fed124413bf14ae151f14c5139011ef10030d940a990761041900a4fd3dfa5cf840f6c7f5e4f5d1f65ef730f831f9adfb8dfd6dff2800e7029203b70434043403b7029200e7ff28fd6dfb8df9adf831f730f65ef5d1f5e4f6c7f840fa5cfd3d00a4041907610a990d94100311ef139014c5151f14ae13bf12440fed0cea09dd07180474020e0052ff44fe8afe1afe41fef7ffed0104028e045e05fd071907b4079c06840485020eff34fbb0f7b1f3cff00aec1ae81ae4a9e1b5df15dd25f4e4f1caeeafebebebebeeaff1caf4e4f712f777f791f86dfa41fdc601c6046a05a8055303ae029a02c703e305ae06d3063d048502240013ffd5012f030104aa051c041902c901ef024e0455069f07c6078e05a3029f0043ff2eff58007500edffeafdf1fb66f957f929fa99fcaefe9dff43fe75fd66fcd7fd9f00360343058106a0061c0488037d037d0488061c06a0058103430036fd9ffcd7fd66fe75ff43fe9dfcaefa99f929f957fb66fdf1ffea00ed0075ff58ff2e0043029f05a3078e07c6069f0455024e01ef02c90419051c04aa0301012fffd5001302240485063d06d305ae03e302c7029a03ae055305a8046a01c6fdc6fa41f86df791f777f712f4e4f1caeeafebebf255ef76ecc9e9d4e9d4ecc9ef76f255f655f910fa30fc41fee500c7030f05ac069c05fb04d902bbffedfdfcfce2fbe6fb73fb66fac4f9f0f9e9fa6ffb77fdbf00b9031d050806af0752073f079b0837087708aa08ae07c60623047802f101b000f700b00093006a001affbdff90ff99ffd3004d00f4017b01c001ec021302220240029302db02e402e402db029302400222021301ec01c0017b00f4004dffd3ff99ff90ffbd001a006a009300b000f701b002f10478062307c608ae08aa08770837079b073f075206af0508031d00b9fdbffb77fa6ff9e9f9f0fac4fb66fb73fbe6fce2fdfcffed02bb04d905fb069c05ac030f00c7fee5fc41fa30f910f655f255ef76ecc9e9d4ec91e8d7e4d7e17ae17ae4d7e8d7ec91f001f256f3a3f50ff6d9f92cfc61ff90018b024801c2fff4fdbefbedfa9df9f6f9cef95ef85ef721f5b6f47cf454f59df7befa2cfcc4ff3e0166036705740789099e0bb50d760e590e280d0e0b59095b075d05ba049903b702f802a0029f029302af036204a4064708580ab00ce60ebe100c10a810be10a810a810be10a8100c0ebe0ce60ab00858064704a4036202af0293029f02a002f803b7049905ba075d095b0b590d0e0e280e590d760bb5099e0789057403670166ff3efcc4fa2cf7bef59df454f47cf5b6f721f85ef95ef9cef9f6fa9dfbedfdbefff401c20248018bff90fc61f92cf6d9f50ff3a3f256f001ec91e8d7e4d7e17ae4f0e14cde00db58db58de00e14ce4f0e8f0ec0eee00f014f284f4e4f772f9e6fb38fb3efa38f82ef5c8f3f3f2c6f223f233f284f275f262f2c1f387f4ecf781fae0fe34015c0440064c07ba093a0aa90bbc0cb70d600d190c3c0b690a750988094f099209c60a380aee0b550b9b0c510d330e000f1a104610e9114911c9121b124f12db135c13701370135c12db124f121b11c9114910e910460f1a0e000d330c510b9b0b550aee0a3809c60992094f09880a750b690c3c0d190d600cb70bbc0aa9093a07ba064c0440015cfe34fae0f781f4ecf387f2c1f262f275f284f233f223f2c6f3f3f5c8f82efa38fb3efb38f9e6f772f4e4f284f014ee00ec0ee8f0e4f0e14cde00db58bdb2bbb1b9a8b6e7b6e7b9a8bbb1bdb2c156c4e3c7cdcba2cf3ad17bd424d72fd8add976dacfdb7fdb86dc59dd51ddb4ded8e0e3e279e43ee725ea3ded48f12bf52bf88dfc4000320351064009b60cd10f70124614d416ed19511bb01d5e1f15213122fd248f2661281d29ab2b6e2d442f0730fc330734d4367f381139503a613b793c5f3ce63d213d213ce63c5f3b793a6139503811367f34d4330730fc2f072d442b6e29ab281d2661248f22fd21311f151d5e1bb0195116ed14d412460f700cd109b6064003510032fc40f88df52bf12bed48ea3de725e43ee279e0e3ded8ddb4dd51dc59db86db7fdacfd976d8add72fd424d17bcf3acba2c7cdc4e3c156bdb2bbb1b9a8b6e7c945c6ebc4e0c2d7c2d7c4e0c6ebc945cc8ccf79d19ad435d72ad9a7dc06de74e014e0dce156e177e138e149e1cae26fe375e515e6c8e89ceb0cede1f0c7f44bf84bfbedff5c02e805d308050a550c890e2c0fe911e8137314b016231768186819cb1b821d281f0c212b22f9249e266b27fb29282a892bf02cd42db22ecd2f682f96301a3070303030303070301a2f962f682ecd2db22cd42bf02a89292827fb266b249e22f9212b1f0c1d281b8219cb18681768162314b0137311e80fe90e2c0c890a55080505d302e8ff5cfbedf84bf44bf0c7ede1eb0ce89ce6c8e515e375e26fe1cae149e138e177e156e0dce014de74dc06d9a7d72ad435d19acf79cc8cc945c6ebc4e0c2d7b9f8b7a4b573b3d4b3d4b573b7a4b9f8bc31bde3bf04c052c23fc4bac793ca94cd58cf88d12ad29dd443d62ed878db47de55e13be3f1e6a8e965ec51efa5f36df76dfb62ff3502d60625092f0c4b0f8912b615cf18dd1ba81e05202b223e2440264828762aaa2cbd2e9e305431f5337c34f73682380f396a3a903b973c693cfe3d7a3df43e423e5c3e5c3e423df43d7a3cfe3c693b973a90396a380f368234f7337c31f530542e9e2cbd2aaa287626482440223e202b1e051ba818dd15cf12b60f890c4b092f062502d6ff35fb62f76df36defa5ec51e965e6a8e3f1e13bde55db47d878d62ed443d29dd12acf88cd58ca94c793c4bac23fc052bf04bde3bc31b9f8b7a4b573b3d4b412b219b091af7aaf7ab091b219b412b661b8b8bb00bd78c01ac2c5c577c822caa1cceacef0d0d7d2ced4e7d733d9d1dcb0dfa3e2a4e5cee917ec7df019f3f8f7f8fbf5ffea03c607620acc0e2711711492179a1a911d501fcb222524612683289e2ac32ce42eea30d1329b345135ed376838dc3a3b3b653c6f3d6c3e383ed33f5f3fcd400e402e402e400e3fcd3f5f3ed33e383d6c3c6f3b653a3b38dc376835ed3451329b30d12eea2ce42ac3289e2683246122251fcb1d501a91179a149211710e270acc076203c6ffeafbf5f7f8f3f8f019ec7de917e5cee2a4dfa3dcb0d9d1d733d4e7d2ced0d7cef0cceacaa1c822c577c2c5c01abd78bb00b8b8b661b412b219b091af7ab30cb164afd4ae8dae8dafd4b164b30cb4d0b64fb76ab8c9bac7bd4bc03ac385c6dcc9ecccadcf5bd230d54fd8cbdcabe0abe472e7f4eb5feebbf214f5abf98dfd5e00f0047007c90ac10d8f1081137e1660193d1c051e7a20a022a424a326ae28c42ad62cd32e9e3025318832ee3446358e36e03823392a3a003abb3b493bb33c223c9f3cff3d2c3d2c3cff3c9f3c223bb33b493abb3a00392a382336e0358e344632ee318830252e9e2cd32ad628c426ae24a322a420a01e7a1c05193d1660137e10810d8f0ac107c9047000f0fd5ef98df5abf214eebbeb5fe7f4e472e0abdcabd8cbd54fd230cf5bccadc9ecc6dcc385c03abd4bbac7b8c9b76ab64fb4d0b30cb164afd4ae8d421145e949d94dd94a994762443a411b3e033afc37fd350532162f372c60299126d2241b216c1ecd1c3619af173014b912530ff40da50b5f092806fa04db02c500bffec1fcd2faecf916f748f58af3d4f22ef090ef02ed85ec0feaa9e94ce7fee6c1e58be466e350e243e146e059df74de9fdddadd1ddc70dbd3db46dac1da4dd9e8d994d94fd913d8e6d8cad8bed8c2d8d6d8f1d91dd95ad9a6da02da6edaeadb77dc13dcc0dd7cde49df1ee002e0f7e1fce311e436e573e6c0e81ee98beb08ec96ee33efe1f19ef36cf54af738f93efb54fd7affb001f6044c06bb09390bc80e66111513db16b219991c901f9f22be25ed29342c8c2ff3336b36fa3a9a3e49421145e949d94dd972fd76fd7afd7efd7b0d771d732d6f3d6b4d675d636d5f7d5b8c579c53ac4fbc4bcc47dc43ec3ffc3c0c381c342c303c2c4c285c246c207c1c8b189b14ab10bb0ccb08db04eb00fbfd0bf91bf52bf13bed4be95be56be17bdd8ad99ad5aad1bacdcac9dac5eac1fabe0aba1ab62ab23aae4aaa5aa66aa27a9e899a9996a992b98ec98ad986e982f982fd86fd8afd8efd92fd96fd9afd9efda2fda6fdaafdaefdb2fdb6fdbafdbefdc2fdc6fdcafdcefdd2fdd6fddafddefde2fde6fdeafdeefdf2fdf6fdfafdfefd02fd06fd0afd0efd12fd16fd1afd1efd22fd26fd2afd2efd32fd36fd3afd3efd42fd46fd4afd4efd52fd56fd5afd5efd62fd66fd6afd6efd72fd76fd7afd7efd2403278a2b422f332b33276323cb20641d2d1a26175714b8124a10040dee0c080a4a08b50747060204e503e8030b024f01b2012e00c2006d00310005ffe9ffddffd9ffdeffeafff6000a00160022002700230017fffbffcfff93ff3efed2fe4efdb1fcf5fc18fb1bf9fef8b9f74bf5b6f3f8f212effcedb6eb48e8a9e5dae2d3df9cdc35d89dd4cdd0cdd4bed876dbfddf55e27ce56be82aeab9ed20ef56f15cf33af4f0f67ef7e4f921fa3efb3bfc18fcd5fd7afe07fe7bfed8ff24ff61ff8dffb1ffcdffe2fff6000a001e0033004f0073009f00dc0128018501f90286032b03e804c505c206df081c09820b100cc60ea410aa12e0154717d61a951d8420ab2403278a2b422f33b42db2a7b121af9caf9fafa3afa6afaaafadafb1afb4afb8b13db2c1b446b5cbb750b8d5ba5abbdebeb4c18ac460c736ca0ccce2cfb8d28ed63dd9ecdd9ae149e4f8e8a7ec55f004f403f802fc01000003ff07fe0bfd0ffc13ab17591b081eb72266261429c32d723048331e35f438ca3ba03e76414c442245a6472b48b04a354bba4d3f4ec35048504c504f50535056505a505d506150644edf4d594bd34a4d48c7474145bc4436415f3e883bb138da3603332c30552d7e29ce261e226f1ebf1b0f175f13b010000c00080004000000fc00f800f400f000ec50e8a1e4f1e141dd91d9e2d632d282cfabccd4c9fdc726c44fc178bea1bbcaba44b8bfb739b5b3b42db2a7b121af9cafb4af1faebbae87ae83aeb7af1bafb0b074b169b297b3ecb571b727b90dbb1bbd51bfb0c236c4e5c7bccab3cdcad101d458d7c8db4fdeefe29fe666ea3eee1ef20ef606f9fefdfe01fe05fe09f60dee11de15be19961d5d210d24ad28342ba42efb3232354938403b173dc6404c42ab44e146ef48d54a8b4c104d654e934f88504c50e151455179517d514950e550504f8c4e974d694c144a8f48d946f344e542af40503dca3b1b3844354d32362eff2ba8283824b121111d61199a15c211e20df209fa06020202fe02fa02f60af212ee22ea42e66ae2a3def3db53d7ccd45cd105cdcecab7c7c0c4e9c23abfb4bd55bb1fb911b72bb575b3f0b29bb16db078afb4af1faebbae87c9b3c9afc9abc9a7c9aac9aec9b2c9b6c9bac9c6c9e2ca06ca43ca8fcafbcb88cc34cd09ce0ecf43d0b0d24ed424d63ad888db0eddcde0c4e3ebe742eac1ee69f231f610fa00fe000200060009f00dcf1197153f18be1c151f3c223324f2277829c62bdc2db22f5030bd31f232f733cc34783505357135bd35fa361e363a3646364a364e36523656365936553651364d3649363d362135fd35c035743508347b33ce32f931f430bf2f522db42bde29c8277a24f322341f3d1c1618bf153f11980dd009f006000200fe00fa00f610f230ee68eac1e741e3eae0c3ddccdb0dd886d638d422d24cd0aecf41ce0ccd07cc32cb85caf8ca8cca40ca03c9dfc9c3c9b7c9b3c9afc9abc9a7d485d481d47dd479d47dd481d485d489d48dd491d495d499d4a5d4b1d4c5d4e9d51dd569d5d6d662d717d7fcd919da6edc03dde1e007e26de51ce813eb4aeeb9f259f620fa08fe00020005f809e00da7114714b617ed1ae41d931ff9221f23fd259226e7280428e9299e2a2a2a972ae32b172b3b2b4f2b5b2b672b6b2b6f2b732b772b7b2b7f2b832b872b832b7f2b7b2b772b722b6e2b6a2b5e2b522b3e2b1a2ae52a992a2d29a028eb280626e9259423fe22201ffa1d941ae517ee14b711470da809e005f80200fe00fa08f620f258eeb9eb49e812e51be26ce006dde0dc02da6cd917d7fad715d660d5d3d567d51bd4e6d4c2d4aed4a2d496d492d48ed489d485d481d47dd4790ba007e004000000fc00f820f460f0c1ed41e9e2e6a3e384e085dda6dae7d850d5dad384d14dcf37cd41cb6bc9b6c820c6abc555c420c30bc216c141c08dbff8bf84bf2fbefbbee7befbbf2fbf84bff8c08dc141c216c30bc420c555c6abc820c9b6cb6bcd41cf37d14dd384d5dad850dae7dda6e085e384e6a3e9e2ed41f0c1f460f820fc000000040007e00ba00f3f12bf161e195d1c7c1f7b225a251927b02a262c7c2eb330c932bf3495364a37e039553aab3be03cf53dea3ebf3f734008407c40d141054119410540d1407c40083f733ebf3dea3cf53be03aab395537e0364a349532bf30c92eb32c7c2a2627b02519225a1f7b1c7c195d161e12bf0f3f0ba007e0040000001bbe1f6d23452745240620d61dbe1abf17d014f812390f8a0cf30a74080d05bf0388016aff63fd75fb9ff9e0f83af6adf537f3e1f2a4f17ef079ef8ceebeee09ed75ecf8ec9bec57ec32ec2eec4aec7eecd2ed46eddaee8fef64f058f16df2a2f3f7f56df702f8b8fa95fc93feb100f8035e05ec089b0b720e69118814c7182e1bbe1f6d23452745240620d61dbe1abf17d014f812390f8a0cf30a74080d05bf0388016aff63fd75fb9ff9e0f83af6adf537f3e1f2a4f17ef079ef8ceebeee09ed75ecf8ec9bec57ec32ec2eec4aec7eecd2ed46eddaee8fef64f058f16df2a2f3f7f56df702f8b8fa95fc93feb100f8035e05ec089b0b720e69118814c7182e1bbe1f6d2345274532fb36fb3afb3efb3b1b373a335a2f7a2b9927b923d81ff81c181837145710770c9608b604d600f5fd15f934f554f174ed93e9b3e5d3e1f2de12da31d651d271ce90cab0c6d0c2efc2fbc6fbcafbcefbd2fbd6fbdafbdefbe2fbe6fbeafbeefbf2fbf6fbfafbfefb02fb06fb0afb0efb12fb16fb1afb1efb22fb26fb2afb2efb32fb36fb3afb3efb3b1b373a335a2f7a2b9927b923d81ff81c181837145710770c9608b604d600f5fd15f934f554f174ed93e9b3e5d3e1f2de12da31d651d271ce90cab0c6d0c2efc2fbc6fbcafbcefbd2fbd6fbdafbdefbe2fbe6fbeafbeefbf2fbf6fbfafbfefb02fb06fb0afb0efb12fb16fb1afb1efb22fb26fb2afb2efb32fb36fb3afb3efb0d9c10ab142317fb13fb10640d350a6607f805ea043402cf01ba00ed0059fffdffd1ffc5ffd1ffee0012002f003b002f0003ffa7ff13fe46fd31fbccfa16f808f59af2cbef9cec05e805ebddef55f264f514f762f959fafffc54fd62fe37fed4ff48ff95ffc9ffee00120037006b00b8012c01c9029e03ac050106a7089e0aec0d9c10ab142317fb13fb10640d350a6607f805ea043402cf01ba00ed0059fffdffd1ffc5ffd1ffee0012002f003b002f0003ffa7ff13fe46fd31fbccfa16f808f59af2cbef9cec05e805ebddef55f264f514f762f959fafffc54fd62fe37fed4ff48ff95ffc9ffee00120037006b00b8012c01c9029e03ac050106a7089e0aec0d9c10ab142317fbdc5fdad9d954d7ced7d1d7d5d7d8d7dcd961dae6dc6addefe0c5e39be671e947ecf6f0a5f453f802fc01000003ff07fe0bad0f5b130a16b9198f1c651f3b22112396251a269f28242828282b282f283226ac252723a1221b1f441c6d199616bf130f0f5f0bb0080004000000fc00f800f450f0a1ecf1e941e66ae393e0bcdde5dc5fdad9d954d7ced7d1d7d5d7d8d7dcd961dae6dc6addefe0c5e39be671e947ecf6f0a5f453f802fc01000003ff07fe0bad0f5b130a16b9198f1c651f3b22112396251a269f28242828282b282f283226ac252723a1221b1f441c6d199616bf130f0f5f0bb0080004000000fc00f800f450f0a1ecf1e941e66ae393e0bcdde5dc5fdad9d954d7ced99bd86ed7a9d745d748d7add871d99edb24dd09df3fe1c6e49ce7b3eb0aee92f241f619fa08fe00020005f809e70dbf116e14f6184d1b641e3a20c122f724dc2662278f285328b828bb28572792266524df22f920c31e3c1b65184e14f7116f0dc009e805f80200fe00fa08f618f240ee91eb09e7b2e49be1c4df3ddd07db21d99bd86ed7a9d745d748d7add871d99edb24dd09df3fe1c6e49ce7b3eb0aee92f241f619fa08fe00020005f809e70dbf116e14f6184d1b641e3a20c122f724dc2662278f285328b828bb28572792266524df22f920c31e3c1b65184e14f7116f0dc009e805f80200fe00fa08f618f240ee91eb09e7b2e49be1c4df3ddd07db21d99bd86ed7a9d745e4f6e4dae4d6e4d2e4d6e4dae4dde4f9e535e5a2e64ee753e8c0ea96ece4efa3f2caf649fa10fe00020005f009b70d36105d131c156a174018ad19b21a5e1acb1b071b231b261b2a1b2e1b2a1b261b0a1acd1a6119b418af1741156c131d105e0d3709b805f00200fe00fa10f648f2c9efa2ece3ea94e8bfe751e64ce59fe533e4f6e4dae4d6e4d2e4d6e4dae4dde4f9e535e5a2e64ee753e8c0ea96ece4efa3f2caf649fa10fe00020005f009b70d36105d131c156a174018ad19b21a5e1acb1b071b231b261b2a1b2e1b2a1b261b0a1acd1a6119b418af1741156c131d105e0d3709b805f00200fe00fa10f648f2c9efa2ece3ea94e8bfe751e64ce59fe533e4f6e4dae4d6e4d2ea43ea3fea3bea37ea3bea3fea43ea47ea52ea66ea9aeb07ebbbecd8ee6ef094f342f679fa18fe00020005e809870cbe0f6c11921328144514f91566159a15ae15b915bd15c115c515c915c515c115bd15b0159c156814fb1447132911940f6e0cbf098805e80200fe00fa18f678f341f092ee6cecd7ebb9eb05ea98ea64ea50ea43ea3fea3bea37ea3bea3fea43ea47ea52ea66ea9aeb07ebbbecd8ee6ef094f342f679fa18fe00020005e809870cbe0f6c11921328144514f91566159a15ae15b915bd15c115c515c915c515c115bd15b0159c156814fb1447132911940f6e0cbf098805e80200fe00fa18f678f341f092ee6cecd7ebb9eb05ea98ea64ea50ea43ea3fea3bea370be4088504e50105fd05f945f5c6f287ef88ecc9ea52e81ce626e470e2fbe1c6e0d1e01cdfa8df73df88dfdce070e145e25ae3b0e545e71be931eb88ee1ef0fdf41cf77bfb1bfefb02fb06bb0a3a0d791078133715ae17e419da1b901d051e3a1f2f1fe42058208d207820241f901ebb1da61c501abb18e516cf147811e20f030be4088504e50105fd05f945f5c6f287ef88ecc9ea52e81ce626e470e2fbe1c6e0d1e01cdfa8df73df88dfdce070e145e25ae3b0e545e71be931eb88ee1ef0fdf41cf77bfb1bfefb02fb06bb0a3a0d791078133715ae17e419da1b901d051e3a1f2f1fe42058208d207820241f901ebb1da61c501abb18e516cf147811e20f030be4088504e50105"
   }
  },
  "vosim": {
   "id": "vosim",
   "name": "VOSIM: Braids' VOSIM oscillator with formant tracking",
   "order": 87,
   "version": "0.1",
   "symbols": {
    "update": "vosim_update",
    "render": "vosim_render"
   },
   "keep": [],
   "patch_points": [],
   "uses": [
    {
     "point": "machine",
     "name": "VOSIM",
     "image": 4,
     "decay_default": 64,
     "knobs": [
      {
       "long": "Vosim F1",
       "short": "FRM1",
       "default": 77
      },
      {
       "long": "Vosim F2",
       "short": "FRM2",
       "default": 86
      },
      {
       "long": "Vosim Follow",
       "short": "TRCK",
       "default": 0
      },
      {
       "long": "Vosim Window",
       "short": "WIND",
       "default": 0
      }
     ]
    }
   ],
   "conflicts_declared": [],
   "claims": {},
   "bundle": {
    "code": "4feffff448d70c04206f0014243c0000031c20080680bdcf77d84c420000226f0018267c564f5331b7e8002c673e2400223c00000000eb8a2441264242b31800223c00002fcf42b2281442b2281042b2280c42b2280842b228042581281c42b22818243c564f53312142002c732900244a816d00012273c1247c4011d84c45f21c00215202504aa80038676a267c012c0f26223c001f7c5c243c7fffffff214b0278214b0274267c82581e4b2141028421410280223c803ef8b82142029421420290214b027c214102884a69001e670000cc243c200000002142029c267c60000000223c7fffffff7401214b02a0214102a4214200487369001474184c02080041f90000000075690022e1890682ffffc000e78ad2af0010d28224010682ffc00000218208000c82007f00006f32727f484175690016218208047569001821810800218208087569001c7369001a218208104cd70c042181080c4fef000c4e7522024a826ccc756900164281218208047569001821810800218208087569001c7369001a218208104cd70c042181080c4fef000c4e7542816000fedc267c7fffffff223c20000000214b029c214102a0214b02a442a800486000ff3c2f02206f000c4aa80034663c4aa800386636202802304a806d560c8000003fff6226202802344a806d520c8000003fff6216206f000820080680000000804298b08866fa241f4e752008243c0000031c0680bdcf77d84c4200002f002f082f2f00104eb9000000004fef000c241f4e7544800c8000003fff62ce60a6448060aa2f02202f00080c8000003fff6f06203c00003fff0680ffffc000428106800000060052814a806df4740fc480e88043f90000000020710c0020310c0490884c020800241fe880d088e2a84e754fefffd448d73cfc246f0034282f0038a987701872094c040800eb8c41f9000000002630080043f00800068300000100e2a37d6900067b69000a2229000c2a447743e286e285dbfc000000000c8100007f006f000202223c00007f00243c000102054c02180024300810424148410c8200007f006f0000d2243c00007f00203c000102054c0028002f03700b2f41002c49f90000000047f90000000042424842068200000400e0aa4e94588fd080222f0028278048044a81660000d42f064e942e852c004e94dc86588fd0802786481027804814a93c000000a0a13c000000004a82660001084879000000004879000000002f2f00382f0d4eb9000000004fef00102f0a4eb9400a9252262a0034242a00382f0a2f2f003842aa003442aa00384eb9400a94302f0a2f2f004025430034254200384eb9400a967aa9074cef3cfc00144fef00404e754a826c00ff32203c0001020542824c0028002f03700b2f41002c49f90000000047f90000000042424842068200000400e0aa4e94588fd080222f0028278048044a816700ff300683ffffe2004c013800720fe2a3dc830c8600003fff6e0000ce4a866d0000f42f064e94588fda832c00dc860c8500003fff6e0000a04a856d0000ca2f054e94588fd0802786481027804814a93c000000a0a13c000000004a826700fefc5382c4fc02020682000000002f024879000000002f2f00382f0d4eb9000000004fef00102f0a4eb9400a9252262a0034242a00382f0a2f2f003842aa003442aa00384eb9400a94302f0a2f2f004025430034254200384eb9400a967aa9074cef3cfc00144fef00404e754a816c00fe0242816000fdfc2a3c00003fff2f054e94588fd0806000ff602c3c00003fffda832f064e94588f2c00dc860c8500003fff6f00ff3660d042852f054e94588fd0806000ff3442862f064e94588fda832c00dc860c8500003fff6f00ff0e60a84fefffc448d77cfc206f00402a5026680004222800082428000c2f680010002c2f68001400302f68001800342c68001c226f0048246f004c206f004449e800802f4c003899cc700edbcbd2af002c2801e08c2a0448457bc579c477715a007d715a029c834c046800484648c6dc83e286068600006000d4af00302802e08c2a0448457bc579c477715a007f715a029e834c047800484748c7de83e487dc87280de08c2a0448457bc579c477f25a007ff25a029e834c047800484748c7de83e2874c076000e08eee8ebbcb65000016d9c69c8ee1a620c6b1ef00386600ff6c6000002e720074007c00260ce183280be28ca8030800a1c3d6af0034068300000080e0832c4342af003499cc6000ffc2260ce183280be28ca8030800a1c3d6af0034226f0040228d234100082342000c23430018234e001c4cd77cfc4fef003c4e754fefffc448d77cfc206f00402a5026680004222800082428000c2f680010002c2f68001400302f68001800342c68001c226f0048246f004c206f004449e800802f4c003899cc700edbcbd2af002c2801e08c2a0448457bc579c477715a007d715a029c834c046800484648c6dc83e286068600006000d4af00302802e08c2a0448457bc579c477715a007f715a029e834c047800484748c7de83e487dc87280de08c2a0448457bc5e28c028400007fff77f25a007ff25a029e834c047800e087ee87de834c076000e08eee8ebbcb65000016d9c69c8ee1a620c6b1ef00386600ff686000002e720074007c00260ce183280be28ca8030800a1c3d6af0034068300000080e0832c4342af003499cc6000ffc2260ce183280be28ca8030800a1c3d6af0034226f0040228d234100082342000c23430018234e001c4cd77cfc4fef003c4e752370783423b2366023f46e812437217a247a502e24bdfb83250224602546cbae258bf25825d1994a2617c172265e6bbf26a5992326ed4a92273580ff277e3d6327c780b428114bef285ba00e28a67e1028f1e6f4293ddbbc298a5d6c29d76d0a2a250b9b2a733a2a2ac1f9c22b114b6f2b6130412bb1a9492c02b7992c545c472ca698692cf96d192d4cdb712da0e48f2df589912e4acb992ea0abca2ef72b492f4e4b3f2fa60cd42ffe71353057798f30b12713310b7af23166766331c21a9b321e68d4327b624832d9083733375bde33965e8233f61166345675d234b78d0f35195867357bd92b35df10aa3643003736a7a927370d0cd337732c9537da09c93841a5d038aa020b39131fdf397d00b339e7a5f03a5311043abf435c3b2c3e6b3b9a03a53c0894823c77f27a3ce81f0a3d591bb23dcae9f43e3d8b543eb1015a3f254d903f9a718540106ec7408746eb40fefb8641778e3241f10089426b542c42e68abb4362a5dd43dfa739445d907a44dc634e455c216745dccc78465e663b46e0f0698100810a81278159819c81f7826082e18373841984d3859d867e87708873898c8ab48bf08d3d8e9e900e9190932494c7967d98429a179bfc9df19ff4a208a428a657a896aadfad39af9db20eb48cb715b9aabc4abef2c1a8c465c72cc9fcccd4cfb5d29cd58cd880db7dde7ee183e491e79feab3edcaf0e4f3fff71efa3efd5e007e03a106c109df0cfe101b1334164b195f1c6e1f7922812581287e2b722e62314a3429370239d23c983f58420a44b5475449ea4c714eef516253c6561d586a5aa65cd55ef7610a630d650266e768bc6a826c356ddb6f6e70f0726173c0750e76497773788b798e7a817b5f7c2c7ce57d8b7e1e7e9c7f097f607fa77fd57ff57ffe7ff57fd57fa77f607f097e9c7e1e7d8b7ce57c2c7b5f7a81798e788b77737649750e73c0726170f06f6e6ddb6c356a8268bc66e76502630d610a5ef75cd55aa6586a561d53c651624eef4c7149ea475444b5420a3f583c9839d237023429314a2e622b72287e258122811f791c6e195f164b1334101b0cfe09df06c103a1007efd5efa3ef71ef3fff0e4edcaeab3e79fe491e183de7edb7dd880d58cd29ccfb5ccd4c9fcc72cc465c1a8bef2bc4ab9aab715b48cb20eaf9dad39aadfa896a657a428a2089ff49df19bfc9a179842967d94c793249190900e8e9e8d3d8bf08ab4898c88738770867e859d84d38419837382e1826081f7819c81598127810a81000000029e0a5f16f127cf3c4a538b6c9d867ba014b85ece58e11eefe9fa20ff56fffefff8ffedffdcffc5ffa9ff87ff60ff33ff00fec8fe8afe47fdfefdb0fd5cfd02fca3fc3efbd4fb65faf0fa76f9f6f971f8e6f857f7c2f727f688f5e3f539f48af3d5f31cf25ef19af0d2f004ef32ee5aed7eec9debb7eacde9dee8eae7f1e6f4e5f2e4ece3e2e2d3e1bfe0a8df8cde6cdd48dc1fdaf3d9c2d88ed756d61ad4dad396d24fd104cfb5ce63cd0ecbb5ca59c8f9c796c630c4c7c35bc1edc07bbf06bd8ebc14ba97b918b796b612b48bb302b177afe9ae59acc8ab34a99fa807a66ea4d3a337a1999ff99e599cb69b13996e97c89621947a92d191278f7d8dd28c278a7a88ce8721857383c68218806a7ebd7d0f7b6179b47807765a74ad730271566fac6e026c596ab06909676365bd6419627660d55f355d965bf95a5d58c3572b55945400526d50dc4f4e4dc14c374aaf492a47a7462644a8432c41b3403d3eca3d5a3bec3a82391a37b6365534f7339c324530f12fa12e542d0b2bc62a842946280c26d525a32474234a222421021fe41eca1db41ca31b961a8e198a188b1790169a15a814bb13d312f01211113710630f930ec80e020d410c850bce0b1c0a6f09c80926088907f1075f06d2064a05c7054a04d3046103f4038d032b02cf0278022601db01950154011900e400b4008a00650046002d0019000b000200000000",
    "relocs": [
     [
      620,
      "code",
      1990
     ],
     [
      678,
      "bss",
      8224
     ],
     [
      720,
      "bss",
      8368
     ],
     [
      794,
      "code",
      572
     ],
     [
      800,
      "bss",
      8368
     ],
     [
      880,
      "code",
      2892
     ],
     [
      886,
      "code",
      2378
     ],
     [
      898,
      "code",
      1346
     ],
     [
      1004,
      "code",
      572
     ],
     [
      1010,
      "bss",
      8368
     ],
     [
      1148,
      "bss",
      0
     ],
     [
      1156,
      "code",
      2378
     ],
     [
      1168,
      "code",
      1666
     ],
     [
      50,
      "bss",
      8368
     ],
     [
      258,
      "bss",
      8224
     ],
     [
      544,
      "code",
      648
     ]
    ],
    "symbols": {
     "vosim_update": [
      "code",
      0
     ],
     "vosim_render": [
      "code",
      444
     ]
    },
    "bss": 8560,
    "far": "083401c9067d0da616de21b92dc23a7b476654035fd86a72736c7a707f3b81a081da81c181a5818781658142811b80f280c78099806880357fff7fc77f8c7f4e7f0d7ecb7e867e3e7df47da87d597d077cb37c5c7c047ba97b4b7aeb7a897a2479be795478e9787c780b7799772576af763675bc753e74bf743f73bc733772af7226719b710e70806fef6f5c6ec86e326d996cff6c646bc76b276a8769e56941689b67f4674c66a165f56548649a63ea6339628661d2611d60665fae5ef65e3b5d805cc45c065b485a8859c859065844578156bd55f75531546b53a452dc52135149507f4fb44ee94e1d4d514c844bb84ae94a1c494d487f47b046e146124542447343a342d34203413340633f933ec33df43d243c553b853ab639e83919384b377d36b035e33516344a337f32b431e9312030562f8e2ec62dff2d392c742baf2aeb2a27296628a427e42725266625aa24ee2433237922c022092152209d1fea1f371e861dd61d281c7b1bd01b251a7d19d51930188c17ea174916aa160c157014d7143e13a81313127f11ef115f10d210460fbd0f340eaf0e2b0da90d290cac0c300bb70b3f0aca0a5609e60977090a08a0083807d2076e070d06ae065105f6059e054904f604a50457040b03c1037b033602f402b50279023e020701d201a001700143011a00f200ce00ac008d007100580042002f001f0011000800020000000010d40270081f103e1a4625ba321f3efa4bd1582f63a76dd3765c7cf88170839e83bc838c8359832582ed82b38277823981f781b4816e812680dc808f80407fef7f9b7f457eed7e927e367dd77d767d127cad7c457bdc7b707b027a937a2179ad793778bf784577c9774b76cc764a75c7754174ba743173a6731a728c71fc716a70d670426fab6f136e796dde6d416ca36c036b616abe6a1a697568ce6826677c66d16625657864c96419636862b66203614f60995fe35f2b5e735dba5cff5c445b895acb5a0d594f589057d0570f564e558c54c954065341527d51b950f3502d4f664ea04dd94d114c494b814ab949f04927485e479546cc46024538446f43a542dc42114148407f3fb53eec3e223d593c913bc83b003a38397138a937e2371c3656359034cb34063342327e31bb30f930372f762eb62df62d372c792bbb2aff2a43298828ce2815275c26a525ee2539248523d12320226e21be210f20621fb51f0a1e601db71d0f1c691bc41b211a7e19dd193e18a01803176816ce163615a0150b147713e5135512c6123911ae1125109c10160f910f0e0e8e0e0e0d910d160c9c0c240bae0b3a0ac80a5809ea097e091408ac084607e20780072006c20666060d05b60561050e04bd046f042303d90391034c030a02ca028c0251021801e201ae017c014d012200f800d200af008e00700055003e002a0019000c00030000000019e203530a2913541e2f2a3536e743d150825c90679c714f795e7f8e83af85a285a5855d851484c88479842883d68381832b82d28276821981ba815980f5809080287fbf7f537ee77e777e067d937d1e7ca87c2e7bb57b387aba7a3b79b9793678b1782a77a27718768c75ff757074e0744e73bb7326729071f8715f70c470286f8b6eec6e4c6dab6d086c646bc06b196a7269ca6920687567c9671c666e65bf650f645e63ac62f96246619160db60255f6e5eb65dfd5d445c8a5bcf5b145a58599b58dd5820576156a255e35524546353a252e1521f515d509b4fd84f164e534d8f4ccc4c084b444a8049bd48f84834476f46ab45e64522445e439942d64211414e408a3fc73f033e403d7d3cba3bf83b363a7439b338f23832377236b235f33534347633b932fb323f318330c8300d2f532e9a2de12d292c722bbc2b062a51299d28ea2838278626d52626257724ca241d237122c7221d217420cd20261f811edc1e3a1d971cf71c571bb91b1b1a8019e5194c18b3181d178716f3166115cf153f14b114241398130d128511fe117810f410710ff00f710ef30e760dfc0d830d0c0c960c210baf0b3f0ad00a6309f7098e092608c1085c07fa079a073b06de0684062b05d50580052d04dd048e044203f703af036a032602e402a50268022d01f401be018b015b012c010100d800b2008f006f00520039002400120004000000002364048a0cb7170022ae2f373c244907557d61296bba74e77c75823185f787b08795873586d38670860a85a2853984cd846183f18381830e829a822481ac813380b7803a7fbb7f3b7eb97e367db17d2a7ca27c187b8d7b007a7279e2795178bf782b779676ff766875ce7534749873fb735d72be721d717c70d970356f906eea6e426d9a6cf26c476b9c6af06a43699668e76838678766d66624657164be640a6355629f61e96132607a5fc25f0a5e515d975cdd5c225b665aab59ef5932587657b856fa563d557e54c054015342528351c3510450444f844ec44e044d444c844bc34b034a43498248c248024742468245c245024442438342c44205414640883fc93f0b3e4d3d903cd33c173b5a3a9f39e33928386d37b336fa3641358834d03419336232ac31f63140308c2fd92f252e732dc12d112c602bb02b022a5329a628fa284e27a426fa265125a92502245c23b72312226f21cd212b208a1feb1f4d1eb01e131d781cde1c451bae1b171a8119ec195918c7183717a71718168b15ff157414eb146313dc135612d2125011ce114e10cf10510fd50f5b0ee20e6a0df40d7f0d0c0c9a0c290bba0b4d0ae10a770a0f09a8094308df087d081c07bd0760070406ab065305fc05a80555050504b60468041d03d4038d0348030502c302850247020c01d4019f016b013a010b00df00b60090006d004e0032001b0008000000002d5e06320fe91b5e27d834d241e14ea45ac765fb7002789d7fa084e2884a89c4898c89138899881d879f8720869f861d85998514848d8405837b82f0826481d6814680b580237f907efb7e657dce7d357c9c7c017b667ac87a2a798a78ea784877a67702765e75b87511746a73c27318726e71c37117706a6fbc6f0e6e5f6daf6cfe6c4d6b9b6ae96a35698168cd6817676266ac65f5653d648663cd6315625c61a260e8602e5f735eb85dfc5d415c855bc95b0c5a4f599258d55818575b569d55e05522546453a652e8522a516c50ae4fef4f314e734db54cf84c3a4b7c4abe4a024944488747ca470e4652459644da441e436342a841ed413340793fc03f063e4e3d953cde3c263b6f3ab93a02394d389837e3372f367c35c93516346433b33303325331a430f530472f9a2eee2e422d972ced2c432b9a2af22a4b29a428ff285a27b62712267025cf252e248e23ef235122b42218217d20e320491fb11f191e831ded1d591cc61c331ba21b121a8219f4196718db185017c6173d16b6162f15aa152614a3142113a0132112a2122511a9112e10b5103d0fc60f500edc0e680df60d860d160ca80c3c0bd00b660afd0a960a3109cc0969090708a7084807ea078e073406db0684062e05da0587053604e60498044c040203b90372032d02ea02a90268022b01f001b6017f014b011800e900bb0091006b00470028000c0000000037d4087413e920912dc63b18482a54af60646b0c74757c7182df87a28aa68be28b8a8af88a6589d0893a88a2880a877086d58639859c84fd845e83bd831c827981d68131808b7fe57f3d7e957dec7d427c977bea7b3e7a9079e27933788377d27722767075bd750a745673a272ed7237718170ca70136f5c6ea36dea6d316c786bbe6b046a49698e68d26817675b669f65e26525646863ab62ee6230617360b55ff75f385e7b5dbc5cfd5c3f5b815ac25a045945588657c85709564b558d54cf54115352529551d7511a505c4fa04ee34e264d694cad4bf24b364a7a49c04905484a479046d7461d456444ac43f4433c428541ce411740613fac3ef73e433d8f3cdb3c283b763ac43a12396238b23802375436a535f8354b349f33f33348329d31f3314a30a22ffb2f532ead2e082d632cbf2c1c2b7a2ad82a37299728f8285927bb271f268325e8254d24b4241b238422ed225721c2212e209b20081f771ee61e571dc81d3a1cae1c211b961b0d1a8419fc197518ef186a17e6176316e1166015e0156214e3146713eb137012f7127e12071190111b10a610330fc10f500ee10e720e040d970d2c0cc20c590bf10b8a0b250ac10a5e09fb099b093b08dc087f082307c8076f071706c0066b061705c30572052204d30486043a03ef03a7035f031902d402920251021201d401990160012900f300c000910065003c00140000000042cc0b8918ea26c23498421c4f0d5b31665b705c7914806486338a708d0e8e078d908ce38c368b888ad88a28897888c68814876086ac85f88542848c83d6831e826681ad80f4803a7f807ec57e097d4d7c917bd37b167a59799b78dc781d775d769e75dd751d745d739b72db7219715870956fd36f116e4f6d8c6cca6c076b446a8169be68fb6838677566b265ef652c646863a662e2621f615c60995fd85f155e535d905ccf5c0d5b4b5a8a59c859085847578656c656065546548853c9530a524c518d50d050134f564e994ddd4d224c664bab4af14a37497e48c5480d4754469d45e64530447a43c44310425c41a840f540423f903edf3e2e3d7e3cce3c1f3b723ac33a16396a38be3814376936c03617356f34c73420337a32d53230318d30e930472fa52f042e642dc52d262c892beb2b4f2ab42a19297f28e6284e27b72720268a25f6256224ce243c23aa2319228a21fb216d20df20531fc71f3d1eb31e2b1da21d1b1c951c101b8b1b081a851a0319831903188418061789170d16911617159e152514ae143713c1134d12d9126611f41183111310a410360fc90f5d0ef10e870e1e0db60d4e0ce80c830c1e0bbb0b580af70a970a3709d9097b091f08c30869081007b70760070a06b50660060d05bb056b051b04cc047e043203e7039c0353030c02c60280023d01fa01b9017a013c010000c7008e00590022000000004e490fbf1f2d2e1e3c6c49f5569862346caf75f07de48477899e8d4d8f8090358f9d8ed68e0e8d458c7d8bb48aea8a208955888a87bf86f48629855c849183c482f7822a815c80907fc27ef57e277d597c8b7bbd7aef7a217953788477b776e8761b754d747e73b072e272157147707a6fac6edf6e126d456c786bac6adf6a146948687c67b166e6661b6551648763bd62f3622b6162609a5fd25f0a5e435d7c5cb65bf05b2a5a6559a058dd58195756569355d1550f544e538d52cd520e514e50904fd24f154e584d9b4ce04c264b6b4ab149f84940488847d0471a466445af44fa4446439342e0422f417d40cd401d3f6e3ec03e123d653cb93c0d3b633ab93a10396738bf3818377236cd3628358534e1343f339d32fd325d31be311f30812fe52f492eae2e132d792ce12c492bb22b1b2a8629f1295d28cb283827a72716268725f8256a24dd245023c5233a22b0222721a021192092200c1f871f041e801dff1d7d1cfd1c7d1bfe1b801b031a871a0b19911916189e182617af173816c3164e15db156714f51484141313a4133512c7125a11ed1182111710ae10450fdd0f760f0f0ea90e440de00d7e0d1b0cb90c590bf90b9a0b3c0ade0a810a2509ca0970091708be0866080e07b90763070e06ba0666061505c30572052204d20484043603e8039c0351030602bc0273022a01e3019a0154010f00c900850038000000005a51157d270336e1456b52bd5eda69c073687bcb82e488ab8d1e903991fd926b91b290cf8fec8f098e268d438c608b7c8a9a89b788d587f28710862d854c846a838982a781c680e580057f257e457d657c867ba67ac879ea790c782e77517674759874bc73e07305722a715170766f9d6ec46ded6d156c3e6b676a9169bc68e76812673e666b659964c663f563246254618560b65fe75f195e4d5d815cb55bea5b205a56598d58c557fe5737567155ac54e854235360529e51dd511c505c4f9c4ede4e204d634ca74beb4b314a7749be4906484e479746e2462d457844c54412436142b04200415040a23ff43f473e9c3df03d463c9d3bf43b4d3aa53a00395a38b63813377036cf362d358d34ee345033b33316327a31df314530ac30142f7c2ee52e502dbb2d272c932c012b702adf2a4f29c1293228a52819278d2702267925f0256824e1245a23d5235022cc224921c7214520c520451fc61f481ecb1e4e1dd31d581cde1c651bec1b741aff1a881a13199f192b18b8184617d5176516f51686161815aa153e14d2146713fd1393132b12c2125b11f5118f112a10c510610ffe0f9c0f3b0ed90e790e1a0dbb0d5d0cff0ca20c460beb0b900b350adb0a820a2a09d2097b092308ce0878082307ce077a072606d30681062e05dc058b053a04e80497044803f703a70357030802b70267021501c40172011c00c6005d0000000066e91d5330d1414d4fc25c9067e771e17a8c81f188178d0190b59335948594ab93cf92cf91d090d28fd48ed68dd98cdd8be18ae689ec88f287f9870086098512841b8324822f813b80487f557e627d707c807b8f7aa179b278c477d776eb76007516742c7343725b7174708d6fa86ec36ddf6cfc6c1a6b396a596979689b67bd66e06604652964506376629e61c760f0601b5f475e725da05cce5bfd5b2e5a5f599158c457f8572c5662559a54d2540a5344527f51ba50f750354f734eb34df34d354c774bbb4aff4a44498a48d2481b476346ae45f94546449243e14330428041d1412340763fca3f1e3e753dcb3d243c7c3bd63b303a8c39e9394638a53804376536c63629358c34f0345533bb3322328b31f3315d30c830342fa02f0e2e7c2dec2d5c2ccd2c3f2bb22b262a9b2a10298728fe287727f0276a26e5266125de255c24da245923da235a22dc225f21e2216720ec20721ff91f801f091e921e1c1da81d331cbf1c4c1bda1b691af91a891a1a19ac193f18d3186617fb1791172816be165615ee1588152214bc145713f41390132e12cb1269120911a8114910ea108c102e0fd10f740f180ebd0e620e080dae0d550cfd0ca40c4c0bf50b9e0b470af20a9c0a4709f2099e094a08f608a2084e07fb07a90756070306b1065f060c05b90565051304bf046a041503c00368031102b5025801f901920126009a00000000741628063d164db65ba1678d71d17aa1822188658d7f917a94639640971896f295f494d793bb92a19187906f8f578e418d2c8c188b0689f488e387d486c785b984ae83a382998191808a7f847e807d7d7c7a7b797a79797a787d77817686758c7494739c72a671b270be6fcc6eda6dea6cfb6c0e6b226a37694d6864677d669765b164ce63eb630a622a614b606e5f915eb65ddd5d045c2c5b565a8159ad58da58095738566a559c54cf5404533a527151a950e2501c4f584e954dd34d134c534b954ad74a1b496048a647ed4737468045cb4517446443b24302425241a440f7404a3f9f3ef53e4c3da43cfe3c593bb43b103a6e39cd392d388e37ef375236b6361c358134e9345133ba3324328f31fc316930d730462fb72f282e9b2e0e2d822cf72c6d2be42b5c2ad52a4f29ca294628c2284027bf273e26be264025c2254524c9244e23d4235a22e2226a21f3217d2108209320211fad1f3c1eca1e5a1deb1d7c1d0e1ca11c351bc91b5e1af41a8b1a2219bb195318ed1887182217be175b16f71695163315d21573151314b4145613f7139a133d12e21286122c11d11177111e10c5106e10160fbe0f680f120ebc0e670e110dbd0d690d150cc20c6f0c1b0bc90b770b250ad30a810a3009df098d093b08ea0899084807f607a4075206ff06ac0657060305ad055604fd04a3044703e80384031d02b1023901b500ff0000000081df369e4c705c78694773d97cac840e8a2e8f2a931e9618982a995c99b79943982196e595ac9475933f920b90d98fa98e7a8d4d8c218af889d088a98785866285418421830381e880cd7fb47e9e7d887c747b627a5279437837772b762275197413730e720b710970096f0b6e0e6d136c196b226a2b693768436752666265736487639b62b161c960e25ffd5f1a5e375d575c785b9a5abe59e3590a5832575d568855b454e354125343527551aa50df50164f4e4e874dc24cfe4c3c4b7b4abb49fd4940488447ca4712465a45a444ef443b438942d84228417a40cd40213f763ecd3e253d7e3cd73c333b903aee3a4d39ad390f387137d5373a36a03608357034da344433b0331d328b31fb316b30dc304e2fc22f362eac2e222d9a2d132c8d2c072b832b002a7e29fc297d28fd287f28022785270a268f2616259d252524af243923c4235022dd226b21f92189211920aa203c1fcf1f631ef71e8c1e231db91d521ce91c831c1c1bb81b531aef1a8c1a2a19c91967190818a8184917eb178e173016d51679161e15c4156a151114b91461140a13b3135d130712b2125d120911b51162111010be106b101a0fca0f780f290ed80e890e3a0deb0d9c0d4d0cff0cb10c630c150bc80b7a0b2d0adf0a910a4309f509a70959090908ba086a081907c70774072006ca0672061905be055e04fc0492042303ad0326028b01a50000000090484a8a5fa76e0a78f4819988918e3492b9964698f59adc9c099c889c629b9d9a5498fb97a4964f94fc93ad925f91138fca8e838d3f8bfd8abe89808845870c85d584a1836e823e81117fe57ebb7d947c6e7b4c7a2a790c77f076d575bd74a673937280717070626f566e4c6d446c3e6b3a6a376937683a673c6642654a6453635f626c617b608c5f9e5eb45dca5ce35bfc5b195a3659555876579956be55e5550d54365363528f51be50ef50214f554e8a4dc14cf94c344b704aad49ec492c486f47b246f7463e458644cf441b436742b54204415540a83ffb3f503ea73dff3d583cb23c0f3b6c3acb3a2a398c38ee385237b8371e368535ef355834c53431339f330e327f31f0316330d7304b2fc22f392eb22e2c2da62d232c9f2c1e2b9d2b1d2a9e2a2129a4292828ad283427bc274426ce265825e4257024fd248c241b23ac233d22ce226121f5218a212020b6204d1fe51f7f1f191eb31e4f1dec1d881d271cc51c641c051ba61b471aea1a8d1a3119d6197b192218c81870181817c1176b171516bf166b161715c41571151f14cd147c142b13db138b133c12ed12a01252120511b9116c112010d4108a103f0ff50faa0f610f170ece0e850e3c0df30dab0d630d1a0cd20c8a0c420bf90bb10b680b1e0ad50a8c0a4209f709ab095f091008c10871082007cb0774071b06bc065b05f1057f0504047403c902ba000000009f5865b977b282f08af690fc959999229bcd9dbc9f099fc6a0019fc49f179e009c919b1899a2982f96bf955393e99282911e8fbd8e608d058bad8a58890687b7866a852083d98295815480157ed97da07c697b357a0478d577a9768075597434731371f370d66fbb6ea36d8e6c7a6b6a6a5b694f6845673e6638653564356337623a614060495f545e605d6e5c7f5b925aa759be58d857f25710562e55505473539952bf51e9511350404f6f4e9f4dd24d064c3c4b744aad49e94926486547a646e8462c457244ba4402434d429941e8413740883fdb3f303e853ddc3d353c903bec3b493aa83a08396a38ce3832379836ff366935d3353e34ab3419338932fa326d31e0315430ca30422fba2f342eaf2e2b2da92d272ca72c282baa2b2d2ab12a3729bd294528ce285827e3276f26fd268b261a25aa253b24cd246023f42389232022b6224f21e72182211c20b820541ff21f901f301ecf1e701e121db51d581cfc1ca11c471bed1b941b3c1ae61a8f1a3919e51990193d18e91898184617f517a51756170716b8166b161e15d21586153b14f014a5145c141313ca1383133b12f412ae1268122211dc11981153110f10cc1088104510020fc00f7d0f3b0efa0eb80e770e350df40db20d720d300cef0cad0c6b0c290be70ba40b600b1c0ad80a910a4a0a0209b8096b091c08ca0875081a07b7074d06d8064d05a2048300000000af148ad395c79bd09fa7a232a3dfa4e7a571a591a55ba4d8a413a312a1d9a06d9ed69d3d9ba79a15988796fd957793f4927590fa8f828e0e8c9e8b3189c8886286ff85a0844482ec819780467ef77dab7c637b1f79dd789e7763762a74f573c272937167703d6f166df26cd16bb36a97697f6869675666456537642c6323621d611960195f1a5e1e5d255c2e5b395a475957586a577e569555ae54ca53e85309522b514f50764f9e4eca4df64d254c574b8a4abf49f6492f486a47a846e64627456a44af43f5433e428741d3412140703fc13f143e6a3dc03d183c723bcd3b293a8839e8394a38ad3812377936e1364a35b43522348f33fe336f32e1325531c9314030b830312fab2f272ea42e222da22d232ca52c282bad2b332aba2a4229cc295628e2286f27fd278b271d26ae264025d4256924ff2495242c23c5235f22fa2296223321d0216f210f20b020511ff41f971f3b1ee11e871e2e1dd51d7e1d281cd21c7d1c291bd51b831b311ae11a911a4119f319a41958190b18c01874182a17e11798174f170716c1167a163415f015ab1567152414e1149f145d141c13dc139c135c131e12e012a11264122711ea11ae1171113710fc10c21086104c10130fda0fa10f680f300ef70ebe0e870e4f0e170ddf0da60d6e0d360cfe0cc50c8c0c520c170bdb0ba00b620b220ae10a9d0a540a0709b4095808eb0862077600000000bf84bd75bb6db96ab76cb574b381b194afacadc9abecaa13a840a672a4a8a2e3a1249f699db39c029a5598ad9709956a93cf923990a78f1a8d908c0b8a8b890e8795862084b0834381db80767f157db77c5e7b0879b67867771d75d574927351721470db6fa46e726d426c166aed69c768a467856668654f64386325621461075ffc5ef55def5ced5bee5af159f85900580b571a562a553d5453536b528651a350c34fe54f0a4e304d594c854bb24ae34a154949487f47b846f44630456f44b143f44339428041ca411540623fb13f023e553da93d003c593bb33b0f3a6c39cc392d389037f4375a36c2362c35973504347233e2335332c6323b31b0312830a1301c2f972f142e932e132d942d172c9b2c212ba72b2f2ab92a4329cf295c28ea287a280b279d273026c4265a25f02588252124bb245623f2238f232d22cd226d220f21b1215420f9209e20451fec1f941f3d1ee71e931e3e1deb1d991d481cf71ca81c591c0b1bbe1b721b261adc1a921a491a0119b91973192c18e718a3185f181c17da17981757171816d81699165b161e15e115a51569152e14f414ba14821449141113db13a4136d1338130412d0129c12681236120411d311a111711141111210e310b410871059102c10000fd40fa80f7d0f520f280eff0ed50ead0e850e5c0e350e0e0de80dc10d9b0d760d510d2d0d080ce50cc10c9e0c7b0c590c370c15"
   }
  },
  "chordtables": {
   "id": "chordtables",
   "name": "CHORD Tables: the stock CHORD machine plays wavetables from the +Drive, one table per pattern, PATTERN + SWEEP picks it",
   "order": 36,
   "version": "0.4",
   "symbols": {
    "update": "cw_setup",
    "render": "ct_hook_tick"
   },
   "keep": [
    "ct_knob",
    "ct_keys",
    "ct_release",
    "ct_load",
    "ct_init",
    "ct_tick",
    "ct_step",
    "ct_fmt",
    "ct_hdr_load",
    "ct_hdr_init",
    "ct_slot",
    "ct_slot_id",
    "ct_owner",
    "ct_scan",
    "ct_moved",
    "ct_tag",
    "ct_want",
    "ct_list",
    "ct_away",
    "ct_copies",
    "ct_slot_ino",
    "ct_found",
    "ct_listing"
   ],
   "patch_points": [
    {
     "symbol": "ct_desc_used",
     "kind": "desc_used"
    }
   ],
   "uses": [
    {
     "point": "machine.stock",
     "machine": "CHORD"
    },
    {
     "point": "chord.waves",
     "hook": {
      "at": "0x400ab15e",
      "stock": "4eb9400a8080",
      "op": "jsr",
      "symbol": "cw_setup"
     }
    },
    {
     "point": "screen.tick",
     "hook": {
      "at": "0x400075f0",
      "stock": "4eb940076be4",
      "op": "jsr",
      "symbol": "ct_hook_tick"
     }
    },
    {
     "point": "knob.lookup",
     "vtable": {
      "at": "0x401005a8",
      "stock_ptr": "0x4001e814",
      "symbol": "ct_knob"
     },
     "chain": "ct_next_knob"
    },
    {
     "point": "keys.encoder",
     "hook": {
      "at": "0x4001f886",
      "stock": "487800024e94",
      "op": "jsr",
      "symbol": "ct_keys"
     },
     "chain": "ct_next_keys"
    },
    {
     "point": "pattern.release",
     "hook": {
      "at": "0x40020dca",
      "stock": "202a00847207",
      "op": "jsr",
      "symbol": "ct_release"
     },
     "chain": "ct_next_release"
    },
    {
     "point": "pattern.load",
     "hook": {
      "at": "0x4005b4b0",
      "stock": "156b00260026",
      "op": "jsr",
      "symbol": "ct_load"
     },
     "chain": "ct_next_load"
    },
    {
     "point": "pattern.init",
     "hook": {
      "at": "0x4006155e",
      "stock": "420011400026",
      "op": "jsr",
      "symbol": "ct_init"
     },
     "chain": "ct_next_init"
    },
    {
     "point": "memory.ram",
     "range": [
      "0x43400000",
      "0x43700000"
     ]
    }
   ],
   "conflicts_declared": [],
   "claims": {
    "descriptors": [
     [
      10,
      "machine"
     ]
    ],
    "saved": [
     [
      "pattern, header +36",
      2,
      "all"
     ]
    ],
    "ram": [
     [
      1128267776,
      1131413504
     ],
     [
      2147490908,
      2147513524
     ],
     [
      2147535552,
      2147543776
     ]
    ],
    "gestures": [
     {
      "combo": "PATTERN + SWEEP",
      "atoms": [
       [
        "PATTERN",
        "SWEEP"
       ]
      ],
      "situation": "params",
      "scope": "machine",
      "meaning": "the pattern's wavetable, on CHORD's tracks",
      "replaces": "disarms the pattern selection, then edits SWEEP as without PATTERN"
     }
    ]
   },
   "bundle": {
    "code": "4fefffb848d73cfc2a6f004c220d2f6f0050002c0681bdcf77d80c81000012a7620a7001b0b90000000067182f4d004c4cd73cfc2f6f002c00504fef00484ef9400a8080247940fe4228207940a7887c4a8a67444a886740222877f2705fb0816536243c000002dc4c021800068100001484207218004a88671e4a2800246d181428002512280024758206810000005a7381b282670002e0207900000000b1fc43640b70670000f2207c43640b707202283c8000eee443e80004267cbfee7a7423c400000000247c4011859423d100000000d7c8428443f900000000200d7601e3ab49f900000000b1f41c00670002362433a800888352812382a800588ab5fc4011860c66d823c40000000043f9000000002a4023d10000000023c8000000004ab90000000066000098b1fc43640b70676e7015780a206f002c7368001a2401e8a1e1aa70202041528802827fe00000b0816500020077c845f90000000022721c0026323c00200d06800000027c41ed009c2168001c00202149000c2143001020822141001c41e80078b08866e44cd73cfc4fef00484e754ab90000000066204ab900000000668a2f4d004c4cd73cfc2f6f002c00504fef00484ef9400a8080227900000000200d2a390000000026050685000000212f490034528322457e1f7a01ce83efad2205c2b9000000004a816700014a280706843fffffffe58c243c42308ab02644d7fc401185902213244245eafe20b29267000124b2aa00046700011cb2aa00086700011445ea0078b2aaff9467000108b5c266da06820000031c0c8242309d5866c6226f00342a402f4b003c70202f47003449f148042f45004426412f40003824542f4c0040284a2f4a00304cd404fe49ec002048d304fe47eb0020538066ec269445f900000000202f0034267c423088d0286f004025890c00226f003c200d26142c11428279c2428143f34c005281b691676658897804b88166f206820000001e7278b28266de47eb031cb7fc42309b7866d0286f00342a40226f003c701f45f9000000002591cc00b08c670000de222f00444681c3b900000000202f003452b90000000023c000000000b1fc43640b706600fe186000fe8222866096241252812382a800588ab5fc4011860c6600fda86000fdcc5283b6896600fe9c2a40b1fc43640b706600fde46000fe4e227c8000eee478202609b8886500fe0491c877c845f90000000026323c006000fdf273a80024e2896700fd1a538141f9000000004ab01c006700fd0a20701c00b1f9000000006700fd84283c8000eee4720243e80004267cbfee7a7423c400000000247c4011859423d100000000d7c8428443f900000000200d6000fd0e202f0034227c4011860823d100000000222f00444681c3b90000000023c00000000052b9000000006000ff16598f202f00084af90000000056c14a01660a2e804eb90000000020172f400008588f4ef940076be442b9000000004aaf00046708700113c00000000041f9000000004298b1fc0000000066f648790000000048790000000042b9000000004eb94007aa78508f4a8057c17301448123c1000000004a806708700123c0000000004e75203940fe42282f032f024a8067342f004eb94000f208588f4a80672622402069003c4a88671c4a2800246d161228002510280024738106800000005a7180b08167147030206f00141080420011400001241f261f4e7573a80024760ae28924014c4320004c43200220420680000000307409b48164ce226f0014220806810000003012c12f490014206f00141080420011400001241f261f4e754e56ff5c48d73cfc4ab9000000006700029a47f900000000244b223c43404000283c0000000049f900000000719a0c80000000ff672e068100008110b5c466ec4ab940f07cf466000098420713c700000000420313c3000000004cee3cfcff5c4e5e4e75b2b90000000067ca2a7c42308828762a75c3428041f52c002250528093c15888b3fc0000810f63aa7404b48066ea06830000001e0c83000000a266d44bed031cbbfc42309ad066c67002b2b40c00671e52807620b68066f242050681000081101545ffffb5c46600ff606000ff7042b40c0076205280b68066d060dc4ab940f07cf46700ff6a2079422fef30b1f940fe6df06700ff5a2039401fb8a022400c80000020006304327c20004a806714207c401fb8a442804281d09052815088b28965f6223900000000528123c1000000004a3900000000670ab3f900000000670006de72014878000123c90000000023c00000000013c1000000004eb900000000588f4ab900000000660005922039000000004a806700fed82a002240e58d528928000684000000401c390000000042024bf9000000002445d5fc00000000261220452845d1fc000000002a09d9fc0000000055854a83670002604a066606b6946700022e4a02670623c00000000045f90000000025835c00486effa02f034eb94007de78508f41f9000000002d40ff904a80660004c04ab05c006712226effa441f900000000b3f05c00670002602c0e0686ffffffb02f06700148780040486effc02d43ffb042aeffb442aeffb82d40ffbc4eb94007baaa4fef000c7240b280660002504a2effc166000248242effc4200253800c8000003fff620002362e020287000001ff2d47ff8c4a8766000224068000000041b0aeffa86200021642844a3348006700031452847e47be8466f0420342b25c0013c3000000004cee3cfcff5c4e5e4e752039401185900680800000000c80000100006500010c203940118608b0b94011860c660000fc20394011859422000681800000000c8100010000640006680c808000eee46700065e227c40118598720320112040d1fc80000000b1fc00010000640006420c808000eee467000638207c401185945888b0a8fffc67000368b3c866f2528143e800047820b88166c22a3c8000eee4700223c543640b70207c40118590287c43640b7823d043640b74247c43640bf44bf900000000267cfcad7a1c91c8d7cc2253d3c8259188005888b1fc0000040466ee28ca227c43640b702b890c00d5c85280b5fc4364846c66cc247c43640bec23d243640bf0700147f90000000023c000000000223c43404000244b283c0000000049f9000000006000fc64223c000000ff47f90000000023c100000000283c00000000244b223c4340400049f9000000006000fc3a723eb28065562209588a740152815280588c5888b2846700056c261222412a0955854a836600fda44ab55c00672624355c0042b55c0022020681bcbfc00042904a8267102e3c000081104c47100150c2178218004294763eb68064aa4202420342b90000000013c20000000013c3000000004cee3cfcff5c4e5e4e752039000000007e3ebe8065d44203528023c00000000013c3000000004cee3cfcff5c4e5e4e7541f90000000020305c0042b05c0041f90000000042b05c002239000000004a80670000d20680bcbfc000263c000081107a3e4c43000050c417840800ba816500ff7a528123c100000000420313c3000000004cee3cfcff5c4e5e4e7571680200761f548890814c0208004c430800d0814840424028c0b3cc671273504a8266dc54884841424128c1b3cc66ee262eff8c255204002acadc8545ea04040683fffffbfc43e90404b3c7660001222a2eff982205226eff94528141f90000000020305c0022bc8000eee42369007c008021895c0041f90000000043eeffa4282eff9c21915c00178148002239000000004a806600ff32703eb0816500fec0528123c1000000006000ff442f0670012f027e402f3c434000002d43ffb02d47ffb442aeffb82d40ffbc4eb94007baaa4fef000cb4806600fecc32047e09eeaa227c8000eee4207c43400000c2fc81102a41dbfc434040002d4dff94760f7e012c112006e6a05488484648c67768fffec0875889d0860c8000007fff6f06203c00007fff9680200376085880b68065000236b1fc4340020066c27e0153822c2eff8c263cbcbfbf7c2d47ff902d45ff98244122412e01d5fc43404084d3fc4340448406874340c50496812d44ff9c2a022006721f4c4100024c4100007809284a06800021a000e9a820407001b0aeff906600020a2d43ff8c6000fe84263c000000ff47f90000000023c300000000223c43404000244b283c0000000049f9000000006000f97620305c0042b05c0041f90000000042b05c002239000000004a80670002580680bcbfc0002a3c000081104c45000050c717870800703eb0816500fd5e528123c1000000006000fde2741045f9000000002f3c4364cb804879000000004eb94007ab26508f4a806f0001ec71b94364cb9478090680ffffffd0b880650000a477b94364cb9522030681ffffffd0b8816500009073b94364cb960681ffffffd0b881647e7a0a4c050800204341f008cf703e2a08b088656a2c394364cb804a86676071f94364cb8453804a8067542f064eb94007ecc2588f28004a8066442005e1882240d3fc43648c804ab25c00674c12394364cb9420494a01670001de267c4364cb9497c91010770152887f00be83660001781233880066ec10107180b0846e1a53824a826600ff2a420313c3000000004cee3cfcff5c4e5e4e7525865c00267c4364cb9491c81030b800670e138088005288b1fc000000ff66ec42035382138388004a826600feea60beb0b9000000006600f91c4ab9000000006600fecc2039000000004a806600f93c743fb4816400f80a42a74eb900000000588f6000f91052825382263cbcbfbf7c2d45ff98244122412e01d5fc434040842c2eff8cd3fc4340448406874340c50496812d44ff9c2a026000fdd62d45ff88721e2d4aff84b286642a7368fe004a82675271507a1f90814c0208004c450800d0814840424028c0b3cc67425488721eb28665d6200cd08306808000eee42440780f20122200e8a17a01484048c0c285d2800c8100007fff6f06223c00007fff4a8266ae4841424128c1b9c966be2a2eff88246eff846000fc1c760123c300000000420342b90000000013c3000000004cee3cfcff5c4e5e4e75783eb8816500fb1e528123c1000000006000fba279817180b0846f00fe906000fea6243c000000ff47f90000000023c200000000223c43404000244b283c0000000049f9000000006000f6b6420323c90000000013c3000000004cee3cfcff5c4e5e4e7510117180b0846f00fe406000fe562f02206f000c226f00084a2800246d161228002510280024738106800000005a7180b0816720725a91c840c0240000820000070046c23408134200241341002546c0241f4e75102800243040220806810000005a40c0240000820000070046c23408134200241341002546c0241f4e75206f000440c0220000810000070046c1420111410024725a1141002546c04e75598f2f2f00142f2f00142f2f00142f2f00144eb9000000004fef001022007049b081660000d6487800032f4100044eb94007faf4588f22174a80670000be307c7f0042b94010df1470ff42b94010df18720a23c84010df1c42b94010df2042b94010df2423c04010df2823c04010df2c203c0000000042b94010df3041f90000000023c84010df3c307c7f0023c04010df4470ff42b90000000042b90000000023c80000000042b90000000042b90000000023c00000000023c000000000203c0000000042b90000000041f90000000023c800000000207c40a733e823c000000000203c0000000023d040a71b4c23c040a71b5c42b940a71b682001588f4e75203940fe4228518f2f024a80670000a62f004eb94000f208588f4a806700009622402069003c4a886700008a222f001043e9002c2f4900084a816d0000d2e081660a4aaf00106f0000f272014a2800246d26142800251f42000414280024324275af00042f42000443e9005a34097582b4af0004670000a840c2224200820000070046c2747fb4816d304a816d561141002406810000005a11410025220946c122402069002c42a72f2f000c206800104e90508f241f508f4e75727f1141002406810000005a11410025220946c122402069002c42a72f2f000c206800104e90508f60d042811141002406810000005a11410025220946c122402069002c42a72f2f000c206800104e90508f60a60681000000ffe0816600ff346000ff2675a80024d28240c2224200820000070046c2747fb4816c00ff5460804aaf001056c173014a2800246c00ff0a6000ff2c4af90000000056c04a0066064ef9000000004e7500000c830000000a6616716effda2f004eb900000000588f78004ef94001f96a2f3c000000004a9767024e75588f22572ebc000000022f094ef94007faf42f3c000000004a9767024e75588f422a007c202a008472074e7500004feffff048d70303203c00000000670a22404cd701034e916006156b002600262f0b2f0a4eb900000000508f4cd703034fef00104e7500004feffff048d70303223c00000000670a22414cd701034e9160064200114000264cd703032f084eb900000000588f4cd703034fef001042004e752f576176657461626c6573005741564500576176657461626c6500",
    "relocs": [
     [
      1064,
      "bss",
      18
     ],
     [
      1078,
      "bss",
      22
     ],
     [
      1084,
      "bss",
      320
     ],
     [
      1092,
      "bss",
      572
     ],
     [
      1100,
      "bss",
      2
     ],
     [
      1106,
      "code",
      4726
     ],
     [
      1112,
      "bss",
      316
     ],
     [
      1134,
      "bss",
      312
     ],
     [
      1146,
      "bss",
      316
     ],
     [
      1316,
      "bss",
      308
     ],
     [
      1326,
      "bss",
      824
     ],
     [
      1340,
      "bss",
      895
     ],
     [
      1346,
      "bss",
      180
     ],
     [
      1384,
      "bss",
      23
     ],
     [
      1392,
      "bss",
      0
     ],
     [
      1408,
      "bss",
      176
     ],
     [
      1602,
      "bss",
      18
     ],
     [
      1610,
      "bss",
      18
     ],
     [
      1616,
      "bss",
      23
     ],
     [
      1624,
      "bss",
      28
     ],
     [
      1640,
      "bss",
      28
     ],
     [
      1646,
      "bss",
      24
     ],
     [
      1652,
      "bss",
      23
     ],
     [
      1658,
      "code",
      1062
     ],
     [
      1666,
      "bss",
      312
     ],
     [
      1676,
      "bss",
      316
     ],
     [
      1704,
      "bss",
      22
     ],
     [
      1712,
      "bss",
      1148
     ],
     [
      1720,
      "bss",
      316
     ],
     [
      1732,
      "bss",
      892
     ],
     [
      1740,
      "bss",
      568
     ],
     [
      1768,
      "bss",
      316
     ],
     [
      1774,
      "bss",
      572
     ],
     [
      1798,
      "bss",
      1148
     ],
     [
      1824,
      "bss",
      896
     ],
     [
      1974,
      "bss",
      0
     ],
     [
      2170,
      "bss",
      180
     ],
     [
      2242,
      "bss",
      824
     ],
     [
      2248,
      "bss",
      308
     ],
     [
      2262,
      "bss",
      895
     ],
     [
      2268,
      "bss",
      180
     ],
     [
      2284,
      "bss",
      824
     ],
     [
      2290,
      "bss",
      308
     ],
     [
      2296,
      "bss",
      895
     ],
     [
      2310,
      "bss",
      180
     ],
     [
      2416,
      "bss",
      316
     ],
     [
      2422,
      "bss",
      22
     ],
     [
      2428,
      "bss",
      0
     ],
     [
      2444,
      "bss",
      316
     ],
     [
      2460,
      "bss",
      316
     ],
     [
      2466,
      "bss",
      0
     ],
     [
      2482,
      "bss",
      1148
     ],
     [
      2496,
      "bss",
      896
     ],
     [
      2506,
      "bss",
      316
     ],
     [
      2550,
      "bss",
      316
     ],
     [
      2558,
      "bss",
      0
     ],
     [
      2666,
      "bss",
      1148
     ],
     [
      2692,
      "bss",
      896
     ],
     [
      2714,
      "bss",
      316
     ],
     [
      2736,
      "bss",
      316
     ],
     [
      2992,
      "bss",
      824
     ],
     [
      2998,
      "bss",
      308
     ],
     [
      3012,
      "bss",
      895
     ],
     [
      3018,
      "bss",
      180
     ],
     [
      3036,
      "bss",
      896
     ],
     [
      3046,
      "bss",
      316
     ],
     [
      3090,
      "bss",
      316
     ],
     [
      3102,
      "bss",
      320
     ],
     [
      3114,
      "bss",
      2
     ],
     [
      3326,
      "bss",
      0
     ],
     [
      3390,
      "bss",
      24
     ],
     [
      3400,
      "bss",
      312
     ],
     [
      3410,
      "bss",
      316
     ],
     [
      3432,
      "code",
      1062
     ],
     [
      3626,
      "bss",
      316
     ],
     [
      3634,
      "bss",
      312
     ],
     [
      3640,
      "bss",
      0
     ],
     [
      3666,
      "bss",
      316
     ],
     [
      3696,
      "bss",
      824
     ],
     [
      3702,
      "bss",
      308
     ],
     [
      3716,
      "bss",
      895
     ],
     [
      3722,
      "bss",
      180
     ],
     [
      3734,
      "bss",
      316
     ],
     [
      3740,
      "bss",
      0
     ],
     [
      3932,
      "ct_next_knob",
      0
     ],
     [
      4026,
      "code",
      4738
     ],
     [
      4038,
      "code",
      4743
     ],
     [
      4062,
      "ct_desc_used",
      564
     ],
     [
      4068,
      "ct_desc_used",
      568
     ],
     [
      4074,
      "ct_desc_used",
      572
     ],
     [
      4080,
      "ct_desc_used",
      576
     ],
     [
      4086,
      "ct_desc_used",
      580
     ],
     [
      4092,
      "ct_desc_used",
      584
     ],
     [
      4098,
      "ct_desc_used",
      588
     ],
     [
      4104,
      "code",
      4738
     ],
     [
      4110,
      "ct_desc_used",
      592
     ],
     [
      4116,
      "code",
      4743
     ],
     [
      4122,
      "ct_desc_used",
      604
     ],
     [
      4134,
      "ct_desc_used",
      612
     ],
     [
      4140,
      "code",
      1152
     ],
     [
      38,
      "bss",
      308
     ],
     [
      154,
      "bss",
      176
     ],
     [
      194,
      "bss",
      44
     ],
     [
      206,
      "bss",
      48
     ],
     [
      216,
      "bss",
      -1074890080
     ],
     [
      228,
      "bss",
      180
     ],
     [
      264,
      "bss",
      40
     ],
     [
      270,
      "bss",
      168
     ],
     [
      278,
      "bss",
      172
     ],
     [
      284,
      "bss",
      176
     ],
     [
      290,
      "bss",
      40
     ],
     [
      346,
      "bss",
      44
     ],
     [
      410,
      "bss",
      40
     ],
     [
      418,
      "bss",
      40
     ],
     [
      450,
      "bss",
      176
     ],
     [
      458,
      "bss",
      32
     ],
     [
      490,
      "bss",
      40
     ],
     [
      650,
      "bss",
      180
     ],
     [
      744,
      "bss",
      44
     ],
     [
      766,
      "bss",
      40
     ],
     [
      776,
      "bss",
      36
     ],
     [
      782,
      "bss",
      32
     ],
     [
      874,
      "bss",
      44
     ],
     [
      900,
      "bss",
      1148
     ],
     [
      918,
      "bss",
      176
     ],
     [
      946,
      "bss",
      44
     ],
     [
      958,
      "bss",
      48
     ],
     [
      968,
      "bss",
      -1074890080
     ],
     [
      990,
      "bss",
      172
     ],
     [
      1002,
      "bss",
      40
     ],
     [
      1008,
      "bss",
      32
     ],
     [
      1014,
      "bss",
      36
     ],
     [
      4504,
      "bss",
      0
     ],
     [
      4516,
      "code",
      1306
     ],
     [
      1030,
      "bss",
      0
     ],
     [
      1044,
      "code",
      1306
     ],
     [
      4540,
      "code",
      4168
     ],
     [
      4556,
      "ct_next_keys",
      0
     ],
     [
      4586,
      "ct_next_release",
      0
     ],
     [
      4622,
      "ct_next_load",
      0
     ],
     [
      4650,
      "code",
      3768
     ],
     [
      4678,
      "ct_next_init",
      0
     ],
     [
      4708,
      "code",
      3880
     ]
    ],
    "symbols": {
     "cw_setup": [
      "code",
      0
     ],
     "ct_hook_tick": [
      "code",
      1022
     ],
     "ct_knob": [
      "code",
      3912
     ],
     "ct_keys": [
      "code",
      4524
     ],
     "ct_release": [
      "code",
      4584
     ],
     "ct_load": [
      "code",
      4612
     ],
     "ct_init": [
      "code",
      4668
     ],
     "ct_tick": [
      "code",
      4502
     ],
     "ct_step": [
      "code",
      4168
     ],
     "ct_fmt": [
      "code",
      1152
     ],
     "ct_hdr_load": [
      "code",
      3768
     ],
     "ct_hdr_init": [
      "code",
      3880
     ],
     "ct_slot": [
      "bss",
      1148
     ],
     "ct_slot_id": [
      "bss",
      896
     ],
     "ct_owner": [
      "bss",
      824
     ],
     "ct_scan": [
      "bss",
      316
     ],
     "ct_moved": [
      "bss",
      308
     ],
     "ct_tag": [
      "bss",
      180
     ],
     "ct_want": [
      "bss",
      176
     ],
     "ct_list": [
      "bss",
      44
     ],
     "ct_away": [
      "bss",
      40
     ],
     "ct_copies": [
      "bss",
      36
     ],
     "ct_slot_ino": [
      "bss",
      572
     ],
     "ct_found": [
      "bss",
      320
     ],
     "ct_listing": [
      "bss",
      312
     ]
    },
    "bss": 1400
   }
  },
  "digidelay": {
   "id": "digidelay",
   "name": "Digital Delay: PPPCCC's bright, clean delay of up to 5.4 s, for the delay slot",
   "order": 39,
   "version": "0.1",
   "symbols": {
    "update": "digi_process",
    "render": "digi_reset"
   },
   "keep": [],
   "patch_points": [
    {
     "symbol": "fx_line",
     "kind": "fx_line"
    }
   ],
   "uses": [
    {
     "point": "fx.delay",
     "id": 1,
     "process": "digi_process",
     "reset": "digi_reset",
     "line": 1048576,
     "params": [
      {
       "long": "Digi Time",
       "short": "TIME"
      },
      {
       "long": "Digi Fdbk",
       "short": "FDBK"
      }
     ],
     "name": "Digital",
     "short": "DIGI"
    }
   ],
   "conflicts_declared": [],
   "claims": {},
   "bundle": {
    "code": "4fefffc0206f004c48d77cfc1228000248814a416d00033036017150243c0000bb80780a7e0f207c401493100680000001004c020800c3fc0306c7fc0102e8a0283c0000038434034c040800c5c3eea22e00700fc5c34c507807e0a29282e2812f47003474202f41003cb4876300028876202f4300342639000000004a836700029a206f004426390000000022790000000047e801002879000000002439000000002c3900000000246f00482f4b003847f900000000202f0034780d90892200e8a1670001b2d3c1b3cc620001782003908902800003ffff7e0f22330c0020012a01028000007fffda852801eea42e2f003c2f41002c4c0748004c0708002e01bb872f4500302c477e0feea02e2a0004e687d0842812e6842a40d8872e04de80bf80bf84c0844a806d0000ba28072007e884e680d8802002e682e8809e842807d0822407d480b584b580c8804a846d000084280298862004ea80988027843c00dc80b9fc000400006402528c4a8e6d00011c202f002ce5882200bb816b0001382200d2852801b184b385c8854a846d000088214100042081528302830003ffff5088508ab1ef00386600ff0c23c30000000023cc0000000023c20000000023c60000000023c9000000004cd77cfc4fef00404e75de879f87243c7fffffffbf826000ff702e0dde879f870a877fffffff28072007e884e680d8802002e682e8809e842807d0822407d480b584b580c8804a846c00ff3e60bcd0809180223c7fffffff528302830003ffff5088508ab1812141fffc2141fff8b1ef00386600fe786000ff6a2812e6842e2a0004e68742809dce42af0030d8872e04de80bf804285bf8442af002c9bcd4281c0844a806c00febc6000ff704a806700fe4e7003c0834a8057c0710093c06000fe3ed2819381528302830003ffff5088508a0a817fffffff2141fffc2141fff8b1ef00386600fe066000fef822054aaf00306d00008e06817fffffff2001bb80c0814a806c00fec2223c7fffffff528321410004208102830003ffff5088508ab1ef00386600fdc66000feb8282f00340c840003fc006300fd742639000000002e3c0003fc002f4700344a836600fd6a206f0044700123c000000000226f003499cc47e8010042862f4b00384282246f004847f9000000006000fd7242416000fcce0681800000004a856c00fe3c223c80000000528321410004208102830003ffff5088508ab1ef00386600fd406000fe3242b9000000004e75",
    "relocs": [
     [
      120,
      "bss",
      0
     ],
     [
      136,
      "bss",
      4
     ],
     [
      142,
      "bss",
      8
     ],
     [
      152,
      "bss",
      12
     ],
     [
      158,
      "bss",
      16
     ],
     [
      164,
      "bss",
      20
     ],
     [
      178,
      "fx_line",
      0
     ],
     [
      430,
      "bss",
      4
     ],
     [
      436,
      "bss",
      12
     ],
     [
      442,
      "bss",
      16
     ],
     [
      448,
      "bss",
      20
     ],
     [
      454,
      "bss",
      8
     ],
     [
      774,
      "bss",
      0
     ],
     [
      802,
      "bss",
      0
     ],
     [
      830,
      "fx_line",
      0
     ],
     [
      894,
      "bss",
      0
     ]
    ],
    "symbols": {
     "digi_process": [
      "code",
      0
     ],
     "digi_reset": [
      "code",
      892
     ]
    },
    "bss": 24
   },
   "cost": {
    "emulation": {
     "first": 2621,
     "mean": 3131,
     "max": 3131,
     "reset": 2,
     "pattern": "notes/68 §17: instructions per block of the process called alone after its reset (the reset counted apart), on the OS 1.13 in tools/emu/test_fxslot.py section 6 (mcengine.py's counter): noise of +-2^28 into both channels, Time 0 and Fdbk 96 for the delay, Size 64 and Tone 96 for the reverb (x 256), the first block, then the mean and maximum over 21 blocks after 32 more"
    },
    "device": {
     "status": "not measured"
    }
   }
  },
  "pots": {
   "id": "pots",
   "name": "POTS: a delay whose repeats go down an old telephone line, for the delay slot",
   "order": 70,
   "version": "0.2",
   "symbols": {
    "update": "pots_process",
    "render": "pots_reset"
   },
   "keep": [],
   "patch_points": [
    {
     "symbol": "fx_line",
     "kind": "fx_line"
    }
   ],
   "uses": [
    {
     "point": "fx.delay",
     "id": 2,
     "process": "pots_process",
     "reset": "pots_reset",
     "line": 131072,
     "params": [
      {
       "long": "POTS Time",
       "short": "TIME"
      },
      {
       "long": "POTS Fdbk",
       "short": "FDBK"
      }
     ],
     "name": "POTS",
     "short": "POTS"
    }
   ],
   "conflicts_declared": [],
   "claims": {},
   "bundle": {
    "code": "4fefffa848d77cfc263c0000000024432c6f005c266f0060206f0064a93c000000a0a13c000000007150223c0000bb80740a283c00000384227c401493104c010800068000bb8000e4a04c0408004c5108007220b280630005d47020122800025880e6882f40003048814a416d0006983401780fc3fc03062c3c0000999ac5fc01023002c1c2e8a0c1c2e8a09280e2814c0168002f4600344a926700069a486a00cc240f06820000004c2f022f0b4eb90000000042844fef000c41eb01002013e280222b0004e28147eb0020d0814a806d000548b0846f022800b1cb66e0202a000891c82a0059854bf9000000002243b0a9000c62000530222900049280028100007fff22351c004a816d0005145380b2886f022041b08566d62a2a007c20089085b1c56f000b04e280222a00dcda8070032545007cc0815281254100dc0c850051eb846e00050e0c8500147ae16f0006ac22052c3c000002150681ffeb851f4c0168007e022f460038be80670006ee7203b28067000b704a8067000cfa486a00904eb900000000223c7f8fe1c7a2000800a1c0ec802f004eb900000000508f222a00c44a816f000bb2e6805381254100c490aa0088e880254000e8202a00d4b8806e0c223c7f92c5f9a2000800a1c4202a00d8254400d40c840760eff06f000a167c0fecac223c0760eff04c4410010c8100007fff62000a4248414241207c4563a7fda2080800a1c128019880e484286a00d0204343ee01002f42002c2f44003c283c62bafd00254100d82f4900402f4a0044246f002cd0af003c58af002c221aa0010800a0010800a0010800a0010800a1c62a280004760122280008242f00309481c685b2af003067107e0aeea266047401b782d28221410008b2a8000c6200095e242800049481028200007fff22752c002428008c2e0242474847d287b2a8000c620007e42e2800049e81028700007fff247c78d10da422357c00a44908002e3c2a492b2dae010800a1c143f03c00d4a800ece281247c24584f9e2142008c2401262900102e290018d48723410010a4420800a1c29483260223420018243c6ad06413d6a90020a4030800a1c396872e290028247c45d1c0aa2341002824290030d28223430020a4410800a1c192872e0123410030223c0a3a69efdea90038a2070800a1c19282234100382e2800402428006c21430040a4070800a407080026280070a6010800a6010800a1c1246800f0a44208002e2800f4ae030900a1c7a4430800246800f4a4420800a1c324280088214300702147006ca4010800a4010800a4010800a4010800a1c37e0122054681c287d4a800e8214200882e2900442469004c24301c4422301c4c23430044a8030800a8070800a8020900a8020900243c5f56c73aa4010800a4010800223c4c3e658aa20a0900a1c22342004c26024a826d0005164a836d0005167e0e2203eea90c831fdeffff6306223c00007f7b0681000000847e1b260104c39e83eea97e189e837678e789c283068100000084efa97e0e0681ffffff7cefa94a826d0004fc262f00389282a6010800a1c1d282243c55a55b07a4010800263cff9e433924290054a6020800263c2a05fa252429005ca602090023410054a1c12341005c26280080a6010800a1c222680084a2410800a2410800a2410800a2410800a1c1d6a800e0d3e800e42e2f00342143008021490084ae020800ae020800a1c324062e06d483b587b583ce834a876d0004fe0c82eeb851ec6d0006fc22420c820eb851eb6f06227c0eb851eb43f19a002409d3fc000218df068203d70a3da4020800a1c3a4030800a1c2263c4bda12f7a6020800a1c2e58a93c2243c2aaaaaaba4090800a1c2227c67d01db526280068a2430800a242080026280064a243090021420064a1c2214200682b825c00242800045282028200007fff2268000c21420004b3fc00007fff620652892149000c227c760eff00a2410800a2410800a1c20c82600000006f00045c243c60000000260c2202e683e6814dee0040928347f4180045f318002e01de8a2c01dc872a01da862601d6852241d3c3d2892d4bffc02d4bffc42d4affc82d4affcc2d47ffd02d47ffd42d46ffd82d46ffdc2d45ffe02d45ffe42d43ffe82d43ffec2d49fff02d49fff42d41fff82d41fffcbdef00406700046628426000fc1c44806000fab644816000faea42816000fae40c800003fc006300fa2812280002203c0003fc005880e6882f40003048814a416c00fa22600000b47c01bc80670006ca7e02be80670001f04a80660006740c85080000006f0007702f0549f9000000004e94223cfe0000009280203c55566cf4a2000800a1c047f9000000002f004e93508f0c801fffffff6e0007a2223c7fffffff2f4100382f052c004e94e58e223cfd4356399280e2812f014e93508f0c80500000006e0001520c80133333336d00073e223c60000000a2000800a2000800a1c09caa008090aa0084e886e880254600e0254000e46000fab84241780f2c3c0000999a3401c3fc0306c5fc01023002c1c2e8a0c1c2e8a09280e2814c0168002f4600344a926600f96a204320082248222800c80680000000f84299b3c066fa4a816700050070017c0b227c7ffcb9247e38243c4563a7fd283c0cf34b79214100c8223c200000002080203c7fffffff2149006c227c00ae4c26214000f021400080203c000000bc2141008821410084223c000002ee214200d8243c000a800021440098283c00000232214600a0214700a4214900b0214000b8214100bc2142008c214400c0216f00300008486a00cc240f06820000004c2f022f0b4eb90000000042844fef000c41eb01006000f8c47201b280670005d87c0242af0038bc80674e4a80660004d42c3c7fffffff0c85000002196e00065a203c50000000223c60000000a2000800a2000800a1c09caa008090aa0084e886e880254600e0254000e46000f96c2c3c7fffffff2f460038486a00a87efe4eb900000000720f4841c087068040000000a2000800a1c62a2a00742005d080918072034841bb8092aa008cd286e881d080254100ec223c5999999a068080000000a2000800a1c6222a00782001d0809180207c26666666b380d080068080000000a0400800a1c006850017f0aa0681003c435325410078223c3333333325450074d086a2000800a1c1203c0044a10fa2000800a1c006800044a10fa0000800a1c1e281254000f4203c7fffffff588f9081254000f06000f8a244836a00faee223c00007fff7e1b260104c39e83eea97e189e837678e789c283068100000084efa97e0e0681ffffff7cefa94481262f00389282a6010800a1c1d282243c55a55b07a4010800263cff9e433924290054a6020800263c2a05fa252429005ca602090023410054a1c12341005c26280080a6010800a1c222680084a2410800a2410800a2410800a2410800a1c1d6a800e0d3e800e42e2f00342143008021490084ae020800ae020800a1c324062e06d483b587b583ce834a876c00fb064a866d000204243c2ffffffe227c2c2b0ea06000fb1c0c82a00000006c00fba4243ca0000000260c2202e683e6814dee0040928347f4180045f318002e01de8a2c01dc872a01da862601d6852241d3c3d2892d4bffc02d4bffc42d4affc82d4affcc2d47ffd02d47ffd42d46ffd82d46ffdc2d45ffe02d45ffe42d43ffe82d43ffec2d49fff02d49fff42d41fff82d41fffcbdef00406600fb9e246f0044254200d04cd77cfc4fef00584e754281247c78d10da4a44908002e3c2a492b2dae010800a1c143f03c00d4a800ece281247c24584f9e2142008c2401262900102e290018d48723410010a4420800a1c29483260223420018243c6ad06413d6a90020a4030800a1c396872e290028247c45d1c0aa2341002824290030d28223430020a4410800a1c192872e0123410030223c0a3a69efdea90038a2070800a1c19282234100382e2800402428006c21430040a4070800a407080026280070a6010800a6010800a1c1246800f0a44208002e2800f4ae030900a1c7a4430800246800f4a4420800a1c324280088214300702147006ca4010800a4010800a4010800a4010800a1c37e0122054681c287d4a800e8214200882e2900442469004c24301c4422301c4c23430044a8030800a8070800a8020900a8020900243c5f56c73aa4010800a4010800223c4c3e658aa20a0900a1c22342004c26024a826c00f82e6000fd3e93c96000f6b0243cd0000001227ccc2b0ea36000f91a223c4563a7fd28019880e48443ee01002043286a00d02f44003c283c62bafd002f42002c254100d82f4900402f4a00446000f60c223c0037b4a2a2000800a1c06000f4f2223c7fff0000207c4563a7fda2080800a1c16000f5bc72077001227c7ffcb9247c0b243c4563a7fd7e38283c0cf34b79214100c8223c200000002080203c7fffffff2149006c227c00ae4c26214000f021400080203c000000bc2141008821410084223c000002ee214200d8243c000a800021440098283c00000232214600a0214700a4214900b0214000b8214100bc2142008c214400c0216f003000086000fafe223c7fffffff2f410038203c7ffcb924a0000800a1c0206a006ca0480800222a0070a2010800a1c59085e280a0080800a1c5d1c52548006ca0010800a1c0d280254100706000f49a223c7fffffff2f410038486a00904eb900000000223c7f8fe1c7a2000800a1c0ec802f004eb900000000508f222a00c44a816e00f452222a00c05381254100c04a816e00f44a7c0d7e112043e680222800c82a01edad90aa0088e880b3852205eea9bb812a01eb8db38522052e01edaf42454845b387cafc00077211424548452c07e2aebf865685254500c42a06eb8dbd85220542414841214500c8254000e8c2fc052142414841068100000232254100c06000f3e442af00386000f39e2c3c7fffffff2f4600382f0549f9000000004e9447f900000000223cfd4356399280e2812f014e93508f0c80500000006f00f8c06000fa0c203c13333333223c60000000a2000800a2000800a1c09caa008090aa0084e886e880254600e0254000e46000f3762e3c7fffffff2f4700382f054e942c07223cfd4356399280e2812f014e93508f0c80500000006f00f8646000f9b02c3c7fffffff2f0549f9000000004e9447f900000000223cfd4356399280e2812f014e93508f0c80500000006f00f8306000f97c41f90000000042904e754feffff4202f0010220004c148d7040ce3a8741a761f204145f9000000002200e4a9eb88c681220002817fff800024323c0020323c049082a2000800a1c0720276189288e7a9d081d0824cd7040c4fef000c4e752f0a2f027418222f000c2001e4a0740c45f900000000028100ffffff22402001e5a820407013e0a120321c0024721c04220895c002817fff8000a20a0800a1c17401b4896d24d081b4896710220974e15581b4816e0c72019289e2a0241f245f4e75241f4280245f4e75241f203c7fffffff245f4e75518f2f02206f00102028000c53802140000c4a806f1c201022280004928022680008a2410800a1c1241fd0812080508f4e75202800102428001494802f420004740d2f40000843f900000000222900c82001e5a87411b3802200e4a9740db1812001eb88b380234000c8222900c8068080000000e280e5a9242900c821400004b58174112001e4a8b3802200eb89b181200142404840234100c8222f0004226800084c0108002228000442404840d0af00082140000c20109280a2410800a1c1d081241f2080508f4e754fefffd848d73cfc4cef0300002c286f00344be90010243c01000000263c02000000283c030000002a3c040000002c3c050000002e3c06000000247c07000000267c080000002018a298b800a098b801a4400800a2182800a4410800a0182801ae000800a2183800ae010800a0183801ac000800a2184800ac010800a0184801aa000800a2185800aa010800a0185801a8000800a2186800a8010800a0186801a6000800a2187800a6010800a0187801a4000800a218a800a4010800a4c10800a1c1d29422c1a3c12881b3cd6600ff784cd73cfc4fef00284e75400000004166c34c42d561b4444c074045cae0f247521cc648e1e9ba4a7a77d44c1bf8294dc69cdd4f7a99305138218252ff6b5554d0ad5a56ac1f755891fac15a82799a5c7dd7a45e8451d06096266562b3950964dcdec36712460b69540ec96ba27e656dfddbcc70666f7672dc83747560637477f25cce7a92be8b7d41d96e7fffffff00000000000b5d6a001663f7002118b1002b803400359ebc003f782d0049101f005269e1005b888700646eea006d1fb000759d50007dea1600860828008df9890095c01a009d5da000a4d3c200ac241100b3500400ba58ff00c1404f00c8073100ceaed000d5384800dba4a400e1f4e500e829fb00ee44cd00f4463600fa2f0401000000",
    "relocs": [
     [
      3790,
      "code",
      4518
     ],
     [
      3866,
      "code",
      4386
     ],
     [
      4038,
      "bss",
      0
     ],
     [
      10,
      "bss",
      0
     ],
     [
      176,
      "code",
      4168
     ],
     [
      234,
      "fx_line",
      0
     ],
     [
      388,
      "code",
      3966
     ],
     [
      410,
      "code",
      3848
     ],
     [
      1656,
      "code",
      3764
     ],
     [
      1684,
      "code",
      3848
     ],
     [
      2026,
      "code",
      4168
     ],
     [
      2148,
      "code",
      3966
     ],
     [
      3380,
      "code",
      3966
     ],
     [
      3402,
      "code",
      3848
     ],
     [
      3568,
      "code",
      3764
     ],
     [
      3576,
      "code",
      3848
     ],
     [
      3712,
      "code",
      3764
     ],
     [
      3720,
      "code",
      3848
     ],
     [
      3756,
      "bss",
      0
     ]
    ],
    "symbols": {
     "pots_process": [
      "code",
      0
     ],
     "pots_reset": [
      "code",
      3754
     ]
    },
    "bss": 248
   },
   "cost": {
    "emulation": {
     "first": 1778,
     "mean": 1646,
     "max": 1682,
     "reset": 3,
     "pattern": "notes/68 §17: instructions per block of the process called alone after its reset (the reset counted apart), on the OS 1.13 in tools/emu/test_fxslot.py section 6 (mcengine.py's counter): noise of +-2^28 into both channels, Time 0 and Fdbk 96 for the delay, Size 64 and Tone 96 for the reverb (x 256), the first block, then the mean and maximum over 21 blocks after 32 more"
    },
    "device": {
     "status": "not measured"
    }
   }
  },
  "smpfilter": {
   "id": "smpfilter",
   "name": "Samples: the Model:Samples' filter on every track, lowpass below the centre of Cutoff, highpass above",
   "order": 72,
   "version": "0.4",
   "symbols": {
    "update": "smpf_process",
    "render": "smpf_reset"
   },
   "keep": [],
   "patch_points": [],
   "uses": [
    {
     "point": "track.filter",
     "id": 1,
     "process": "smpf_process",
     "reset": "smpf_reset",
     "name": "Samples",
     "short": "SMP",
     "params": [
      {
       "long": "Filter Cutoff",
       "short": "CUTO",
       "format": "cutoff"
      },
      {
       "long": "Filter Reso",
       "short": "RESO",
       "format": "int"
      }
     ]
    }
   ],
   "conflicts_declared": [],
   "claims": {},
   "bundle": {
    "code": "4fefffe4700548d70c04206f00242f6f00200014b0af0028650000e0222f0028744a45f9000000004c02180030103268000247f218004a2b0048670000c8756b00447140b08267000104754922422f092f002641d7fc000000002f0b2f48001c2f4100184eb900000000206f001c70014fef000c3750004437680002004617400048222f000c4ab21818676e203218004a806d0000b20c8000003fff6e36203218044a806d00014a0c8000003fff6e24206f00144a90661c2028007c4a806614226f0014588843e9007c8098b3c866fa4a80671e4cd70c040681000000002f6f001400242f4100204fef001c4ef90000000042b2180442b218004cd70c044fef001c4e75754971402641d7fc0000000022422f092f002f0b2f48001c2f4100184eb900000000206f001c70014fef000c3750004437680002004617400048222f000c6000ff4244806000ff4c756b00462f42001875492242b4af00186600fef04aab00106600fee84aab00146600fee04aab00246600fed84aab002c6600fed0242b0030b4ab00086600fec4242b0034b4ab000c6600feb847f21800242b0038b4ab00206600fea8242b003cb4ab00286700fed42f092f002641d7fc000000002f0b2f48001c2f4100184eb900000000206f001c70014fef000c3750004437680002004617400048222f000c6000fe9844806000feb4598f7005b0af00086404588f4e75202f0008724a4c0108002040d1fc000000002f082f4800044eb9000000004200206f0004588f11400048588f4e75206f000442a80004429042a8001442a8001042a8000c42a8000842a8002c42a8002842a8002442a8002042a8003c42a8003842a8003442a8003042a8001842a8001c42a800404e754fefffc4226f004448d7047c206f00402809b3fc00007f006f60283c00007f0020040680ffffc000242800184a8066604a82673c202800384a806700043a220076e14c43180121680030000821680034000c42a8001442a8001042a8002c2140002042a80038214100242168003c00284cd7047c4fef003c4e754a896ca2428420040680ffffc000242800184a8067a0262f00480c8300007f006e0001ae4a836d0003782203e6837a0beaa17783c2fc04082c010681000000000686000000002f4300342f46001c2f4100204a806d0001ae26002200ee81d68377830c80000000ff6e00036a7c177a02eda8283c7fffffff2f44002c2f450038224152897bc979c1246f0020e78de78c222f00202245d5c5d3ef001c2f4a0018d28424412f490028d8af001c2252246f00182a1224442f520030246f00289a892f4500202c2f0020e0862a122441222a00049aaf0030246f00182f4600202f45001c2a2a000424449a81282a00042f450024246f00282c2f0024e0862a2a00049a842f4500182a2f001ce0852f4600242f45001c2a2f0018e0852f4500182a2f001c2c2f00204c0358004c0368002f45001c2f4600202a2f00182c2f00244c0358004c036800262f001cd3ef0020d6af0030d885d28693c392842a09e081e0852c2f00344c0658004c061800d6852241d3c44a82660001b022007a1f4c4518017c0142a80004429021460040214300082149000c42a8001442a8001042a8002c2142002021410024214300302149003421400038216f002c0028216f002c003c216f003800184cd7047c4fef003c4e75263c00007f007a0b2203e683eaa17783c2fc04082c010681000000000686000000002f4300342f46001c2f4100204a806c00fe5626042204ee81d6837783b3fc00003f006f0001d27a012f450038203c00004000224152897bc990847817e9a8e78d79c1246f0020222f002042af002ce78c2245d5c5d3ef001c2f4a0018d2842f4900282441d8af001c2252246f00182a1224442f520030246f00289a892f4500202c2f0020e0862a122441222a00049aaf0030246f00182f4600202f45001c2a2a000424449a81282a00042f450024246f00282a2a00049a842f4500182a2f001ce0852f45001c2a2f0018e0852f4500182c2f0024e0862a2f001c2f4600242c2f00204c0358004c0368002f45001c2a2f00182f4600202c2f00244c035800d3ef00204c036800262f001cd6af0030d885d28693c392842a09e081e0852c2f00344c0658004c061800d6852241d3c44a826700fe54282f002c741f7a1f21680030000898a8003c21680034000c2168003c00284c4248042428003821400038216f002c003c21420020220092824c4518012a039aa800302144002c214300302c099ca80034ea852141002421490034ea862f45001c2f460020216f001c0010216f00200014216f003800186000fe2842832203e6837a0beaa17783c2fc04082c010681000000000686000000002f4300342f46001c2f4100204a806c00fc8a6000fe32203c7fffffff78022f40002c2f4400386000fc9a7c0142af002c203c7fffffff2f4600386000fc864cd7047c42a80004429042a8001442a8001042a8000c42a8000842a8002c42a8002842a8002442a8002042a8003c42a8003442a8003042a8001842a8001c42a800404fef003c4e75206f0004226f0008202800184a8067664aa80040671253804a80675c4280208042a8000442a80040203c7fffffffb0a80020671470022140001c2f4900082f4800044ef9000000004aa8002466e64aa8002c66e0202800284a80662c4a8056c0710044802140001c2f4900082f4800044ef9000000004e752011e28042a8000442a80040208060a00c807fffffff67cc700260a24fefffd448d75cfca9802f400028a93c000000a0226f0030206f0034241126290004282900082a29000c2c2900102e290014247c80000000287c7fffffff70202229001c0c81000000016700005c0c8100000002670000aa2210e281a102a6040800a6040800a301a6850900a6850900a1c2a48a0800a3cba103a6440800a6440800a1c3a102a6040800a6040800a1c1a101a20c0800a1c120c1d886da8753806600ffb6600000de2210e281a102a6040800a6040800a301a6850900a6850900a1c2a48a0800a3cba103a6440800a6440800a1c3a102a6040800a6040800a1cba101a20c0800a64a0800a64c0900a1c120c1d886da8753806600ffae600000862c2900202e2900282210e281a102a6040800a6040800a301a6850900a6850900a1c2a48a0800a3cba103a6440800a6440800a1c3a102a6040800a6040800a1cea101ac4a0800ac4a0800a1cba10ea6470800a1cea10ea20a0800a1cba101a6460800a1c1a101a20c0800a1c120c1d8a90010daa90014dca90024dea9002c53806600ff86228223430004202f0028a9004cd75cfc4fef002c4e75000abe387fae6110000b78737fada7a4000c3f487face1ab000d13937fac0e4b000df63b7fab2c9d000ee83b7faa3ba9000fea9c7fa93a670010fe787fa827bc001224ff7fa7027c00135f737fa5c9630014af2e7fa47b1c0016159e7fa316390017944e7fa1993100192ce07fa00263001ae1147f9e5012001cb2c77f9c8063001ea3f77f9a915a0020b6c47f9880d80022ed727f964c9d00254a6e7f93f2400027d04b7f916f2d002a81cd7f8ec0a8002d61e37f8be3c1003073b17f88d5590033ba8f7f85921c00373a117f82167a003af6057f7e5ea8003ef27d7f7a669b004333cf7f762a000047be9a7f71a43d004c97cd7f6cd0690051c4ab7f67a94600574ad27f62293f005d303c7f5c4a5d00637b4a7f560648006a32c97f4f563a00715dfb7f4832fb007904977f4094d900812edc7f3873a10089e5917f2fc6950093320e7f268467009d1e4a7f1ca32b00a7b4e27f12185100b301247f06d89600bf0f177efad80200cbeb8b7eee09d100d9a4247ee0607100e847657ed1cd6e00f7e4bd7ec2416a01088c987eb1ac0b011a506d7e9ffbef012d42cb7e8d1e990141776e7e790067015703497e638c7a016dfca07e4cacaa01867b127e34496f01a097b47e1a49d401bc6d1c7dfe935d01da177f7de109f901f9b4bd7dc18fe7021b647b7da005a5023f483a7d7c49db026583677d563942028e3b777d2dae8f02b997fd7d02825e02e7c2ba7cd48b1c0318e7ba7ca39cf0034d35647c6f89a70384dc907c3820a203c0109b7bfd2ebf03ff07747bbe7e4d0441f9ae7b7bd6fa0489228c7b34fdc804d4c0087ae9b505052512d97a99bc45057a5e737a44d06405d4e90279eaab870634fb5c798b0530069ae0ee7925924a0706e7a078ba054907795fae78480e5307f29b7577cf5b6e0872ef33774f98c208fab0b976c870e5098a370e76398d3e0a21d9fa75a296700ac1f184750334e30b6ad551745b11610c1cdbf573a9d5c40cd85a1f72ef2dcd0d9da1ad722ac8070e6d00a5715c56d70f46c003708391a2102b22756fa0361b111a62e36eb209ae1214b2e06db8db14131a38f46cb48406142b0ec36ba4eb0f15473f136a8a0587166ec3be6963d9a317a1837e6832809918df4fb666f628e01a27e22b65af186b1b7adac3645daeeb1cd7bd55630267fd1e3def94619ddd301facb7386030c7ea212338635ebc02ed22a074705d408b912423493e5bbf827725aa71095a3a2ba52734830258b1edf528bff4b7572851ab2a4b1c6a559efe252bd4346a5417b67d2d595f96529455192ed8aef95116c60b305028a84fa1004e31bdcfb24e34fdda331fad2a4cd4b2ad3473da174b8202f635b88a114a3eb88b36ec1633490c780a380d081b47ecb5f7391a246b46e0ac523a12745a45e951153af54dcc45074e2a3bc2596c443afb5c3c79964343845abb000ab330650c9b26000b6cae650c277e000c32bb650bac01000d0631650b2829000de7f7650a9b63000ed906650a0516000fda656509649d0010ed306508b948001212946508025a00134bd465073f0c00149a4665066e860015ff5965058fe500177c966504a2330019139e6503a46d001ac62f6502957d001c962665017439001e857f65003f650020965964fef5ae0022caf664fd95ad002525c264fc1ddf0027a94f64fa8ca9002a585d64f8e056002d35dd64f71710003044ef64f52ee5003388eb64f325be0037056364f0f965003abe2564eea779003eb73f64ec2d730042f50864e988a100477c1e64e6b621004c517064e3b2e300517a4164e07b9e0056fc2c64dd0cd6005cdd2d64d962d0006323a864d579930069d66b64d14ce30070fcb764ccd83c00789e4b64c816cc0080c36764c30371008974d764bd98b30092bbfe64b7d0bd009ca2d864b1a55700a7340e64ab0fe300b27afb64a4095200be83b5649c8a2100cb5b1f64948a4f00d90ef2648c015700e7adcc6482e62600f7473c64792f140107ebd1646ed1da0119ad2d6463c38b012c9e126457f8840140d273644b646901565f8b643dfa15016d5be8642fab8f0185df8864206a0001a003e5641025a601bbe41263fecdc501d99ccd63ec509d01f94c9863d89b59021b13d263c39a01023f14ce63ad376f026573ed63955d3a028e57bc637bf3ad02b9e90b6360e1b202e8530863440cc60319c35d632558e8034e6a4e6304a88a03867acc62e1dc8303c22a9b62bcd3fd0401b26362956c6c04454dcf626b817c048d3ba6623eed0b04d9bddb620f871b052b19a561dd25ca0581978f61a79d4f05dd8380616ebff7063f2cc961325e2406a6e62260f24656071505a460ae45300789e4c16066258c0805e0256019b0910889579d5fc8adce0914ade15f72e36409a8485d5f1816330a448edd5eb80a190ae9eb335e5282340b98c8bb5de7413d0c5193d05d7609ea0d14b9235cfe9f600de2a4f35c80c5c00ebbc2235bfc42c00fa079325b70de5c10912f035ade639e118e437a5a44a18012980ff159a36be913aee57158fa9cbf14d30aba584a15211604ba0e5791beaf17441ec256d18cfd1891528b56097f1819ec5a8c5539a1331b55242254620e5f1ccb81655382f26c1e4f256b529c8bd91fdfa04851af2dd1217c5acc50bb4246232492044fc14c0824d752914ec1e8ee269373c54dbdd3f8285792b54cb5e7742a220d304bab1f172bf0fccf4a9e9a0b2dc2323149919cef2f933095488593b931612a1a477c13873328fcff4676dc3834e732624577d9cf3697ff504481255e3837491a4395053a39c0ae7442b5ebe93b2f976441e674e03c7f4ead41295d9e3dab282c408178d43eaeb8853ff198243f8622b23f7c6776402e7fbe3f24337f40a662333eea942240ee70463ecff564000aba8c4f6f7f78000b748d4f6f37cf000c3b264f6eeb4d000d0f314f6e999d000df1984f6e4266000ee3524f6de547000fe5694f6d81da0010f8f94f6d17b300121f314f6ca65d001359524f6c2d5b0014a8b74f6bac2800160ecf4f6b223800178d244f6a8ef2001925584f69f1b5001ad92c4f6949d6001caa7d4f68969b001e9b4b4f67d7400020adb44f670af50022e4004f6630d80025409b4f6547fc0027c61b4f644f62002a77424f6345f9002d57044f622aa0003068864f60fc200033af244f5fb93000372e724f5e606e003aea444f5cf063003ee6ae4f5b677c0043280b4f59c40d0047b3024f58044e004c8c854f5626570051b9e24f542820005740bb4f52077d005d27164f4fc220006373614f4d5591006a2c744f4abf2f007159a04f47fc2d007902b04f45098d00812ff54f41e4200089ea4c4f3e888000933b2a4f3af30d009d2ca44f371fed00a7c9794f330b0200b31d1f4f2eafeb00bf33cc4f2a09fb00cc1a864f25143b00d9df2a4f1fc95f00e890814f1a23c200f83e4a4f141d650108f94a4f0dafe3011ad3614f06d470012ddf924eff83cf0142321f4ef7b64f0157e0964eef63c1016f01e74ee683740187ae7c4edd0c2901a200494ed2f40f01be12eb4ec830b901dc03ba4ebcb71601fbf1e64eb07b68021dfe944ea3713d02424cf34e958b600269025f4e86bbd60292467e4e76f3d102be435c4e6623a702ed258e4e543ac6031f1c524e4127ad035459af4e2cd7e1038d129a4e1737e303c97f164e0033280409da564de7b40e044e62e34dcda3d404975ab84db1ea9604e5076c4d946f430537b2474d751799058fa86b4d53c82305ed3ae54d3064350650becf4d0acdf206ba8d5e4ce2e648072b03f14cb88cff07a284204c8ba0c1082173b54c5bff2808a83cae4c2984d509374d234bf40d8b09cf172d4bbb74500a7010b54b7f93960b1ab3384b4045710bcf7b774afd63cf0c8ee90a4ab6c8c40d597dde4a6c4edb0e2fbd964a1dd17e0f122cc349cb2d6110014ffb4974410d10fdaac34918ed6e1207be4048b91685132007b64854a4261446fec047eb82ce157d1347477da49916c2ab1e470b025218181f4b46939c99197db8dc46177d321af3ad594596b8701c7a1aa045116ec11e1102404487ce651fb8442543fa1540216f9892436892e22336894842d3aab0250c69cf423bd63e26f04eb941a1a7dd28e103ce4105cd5f2add01084069131c2ce25e423fcc67402eeec5943f30dd6930ff645e3e97b2af3310db2d3e02521a351f2cc13d7259a23725ad013ce99fb5391ef0f93c6a39553b04c1fc3bf6808d3cd017323b911ae43e791ab03b3cfec53ff741f43afd75d6414185113ad61848424ec4c23acab9db431674743adf3bb44391a16d3b172d7b43bc6dce3b751d504398040f3bf96db5432cd28f3ca094fa000ac3d53e667aa0000b7e793e664e43000c45c13e661ee6000d1a873e65ec53000dfdb53e65b654000ef0443e657cad000ff3403e653f1f001107c53e64fd6700122f033e64b73c00136a3d3e646c510014bace3e641c54001622283e63c6ee0017a1d53e636bc000193b7a3e630a67001af0da3e62a278001cc3d33e623381001eb6673e61bd090020cab93e613e8d002303103e60b783002561dc3e6027580027e9b73e5f8d6d002a9d653e5ee91b002d7fdf3e5e39ac0030944c3e5d7e630033de0c3e5cb671003760ba3e5be0fd003b202d3e5afd1e003f207f3e5a09db004366113e59062a0047f5903e57f0f1004cd3f63e56c902005206973e558d1a0057931f3e543be3005d7f9f3e52d3ed0063d28b3e5153b2006a92ca3e4fb9910071c7b83e4e03ce0079792e3e4c308f0081af8c3e4a3ddb008a73c03e4829960093cf523e45f183009dcc6a3e43933f00a875e13e410c3d00b3d7433e3e59c600bffce53e3b78f700ccf3e93e3866ba00daca523e351fca00e98f0e3e31a0a700f952083e2de59a010a24363e29eaaf011c17ab3e25abb0012f3fa93e2124220143b0b43e1c4f43015980a63e1728020170c6c33e11a8fe01899bd23e0bcc7e01a41a333e058c7001c05df83dfee26301de85003df7c77e01feaf103df0347f0220fdf43de821b6024595993ddf86fb026c9c2f3dd65bac02963a4b3dcc96a602c29b053dc22e4202f1ec213db7184903245e303dab49f3035a24b93d9eb7e40393765e3d91561e03d08d063d8318060411a6083d73f059045702503d63d12a04a0e68e3d52abe004ef9b603d40713305436d7b3d2d1129059cadd33d187b1a05fbb1ca3d029db10660d3513ceb66ed06cc710d3cd2c42c073eee7c3cb8a23207b8b40d3c9ced34083a2f393c7f90ed08c3d2963c6078af095615d83c3f8f7c09f175d73c1cc02b0a9674783bf7f58c0b4598943bd11a940bff6dc73ba81a9a0cc4842b3b7ce1930d956ff83b4f5c640e72c90d3b1f79360f5d2a4e3aed27e4105530e13ab85a70115b7b393a81058e1270a7ea3a4721431395543c3a0aa99b14ca1a7839cb9f75160f8fda398a096d176642223945f4e418ceb4ad38ff772b1a495d0838b6aecc1bd69ee4386bc5061d76c750381eef6b1f2a071c37d071b920f06c3f37809fdd22c9da19372fe04024b6005736deae4e26b45050368d9d4628c3f08a363d5b692ae3ae2235eeb5792d11ebd535a29ab62f4c8e3b355a21493190e50b35168b4833db910234d94c543628666d34a40ffd38724c893478c0e53ab31a5d345990c13ce372c9344901283efaa2e83449ece840ee885d345f914b42b3891d348d95ca443cac3b34d80f08457bec3f354376b94662e82d35d48b7a46e42852368fffaf46f53b163779c8704691ef153893bc6045c0bedb39db102d4497d5b73b445a54000ac1b731388fd8000b7c3831387444000c435b313856d2000d17f931383762000dfafe313815d1000eed613137f1fa000ff02f3137cbb6001104823137a2db00122b8b3137773d0013668e313748aa0014b6e5313716f100161e023136e1db00179d6e3136a92c001936d031366ca9001aebe831362c0d001cbe963135e712001eb0dc31359d6d0020c4dc31354ecc0022fcdd3134fadb00255b503134a13c0027e2ce3134418e002a961d3133db69002d783331336e5b00308c3a3132f9f00033d59231327da6003757d53131f8f7003b16dc31316b51003f16c13130d41a00435be6313032ae0047eaf7312f865c004cc8f4312ece690051fb2e312e0a0d00578755312d3872005d737b312c58b50063c617312b69e3006a8614312a6af90071bacf31295ae300796c273128387b0081a27f31270287008a66cd3125b7b90093c29d312456ac009dc0203122dde600a86a3531214bd000b3cc76311f9ebc00bff33f311dd4e000ccebc3311bec5200dac4123119e30900e98b2c3117b6dd00f951113115657e010a26cf3112ec7a011c1e9131104936012f4bbb310d78eb0143c2f2310a78a801599a3a3107454c0170e9053103db810189c850310037c201a452b730fc564e01c0a49330f8332b01dedc1130f3ca2201ff195330ef16bb02217e8d30ea143b0246302230e4bda1026d54cb30df0da0029715b730d8fea102c39eb030d28aba02f31e4230cbabb20325c5e530c45af6035bca2430bc91a0039562cc30b4486b03d2cb1630ab77b9041441d930a2178e045a09b630981f8f04a4694f308d870504f3ab75308244da05481f5b30764f9e05a218ce30699d8c0601f062305c2488066803ab304dda3006d4b56c303eb3dc07486dc8302ea6b107c39a6f301da7ab0846aec7300babb308d224152ff8a7b5096679942fe490b90a0434952fcf5c080aabe0812fb8ff530b5e0ee12fa170e10c1b574a2f88a7c80ce457392f6e9c2f0db9b1df2f53479a0e9c0fc72f36a5450f8c1e652f18b28d108a8f742ef96f68119818332ed8def212b570572eb7081013e350d12e93f626152272302e6fb9f416738ab52e4a6a8117d74bec2e24263e194e5fc92dfd143e1ad965212dd565a71c78eb682dad57511e2d6d8d2d8533a31ff74bcf2d5d54af21d6c4452d36269b23cbe9f62d102a5f25d69a1a2cebf8eb27f66f402cca46b92a2ab1e42cabe7e72c7246032c91d4ea2ecb95152c7d2ff2313473e32c6f4b1633aa03752c69af7036288c932c6e253f38ab55242c7ebd353b2c6f3c2c9ddafc3da4821d2cce40f6400a8e7c2d131d0c4253b18a2d7015f94472ed992de957d9465905402e839d7a47f47fe32f4431604931fe6f3030dcaf49fd1ffb314fb0754a42592c32a682b149f24af63439d31549073dab360a88dc478d1cbf3811a4aa45aae0fc3a3913fb000ab8fa26eb134c000b72e526eb021d000c396826eaefc4000d0d5c26eadc2d000defaa26eac742000ee14b26eab0ed000fe34a26ea99150010f6c126ea7fa000121cdf26ea6472001356e726ea476d0014a63326ea287200160c3326ea075d00178a7126e9e40c0019229026e9be57001ad65026e99615001ca79126e96b1b001e985126e93d380020aab326e90c3a0022e0fc26e8d7ed00253d9a26e8a0160027c32526e86479002a746126e824d5002d544426e7e0e3003065f526e7985a0033acd126e74aeb00372c7226e6f841003ae8ac26e6a002003ee59a26e641ce0043279a26e5dd3e0047b35726e571e5004c8dcc26e4ff4e0051bc4b26e484fc0057448026e4026c005d2c7a26e3770e00637aaf26e2e24d006a360726e24387007165dd26e19a110079120e26e0e534008142fc26e0242d008a019926df562c0093577226de7a55009d4eb726dd8fba00a7f24626dc956200b34db826db8a4000bf6d6c26da6d3900cc5e9626d93d1c00da2f4826d7f8a800e8ee8826d69e8600f8ac5a26d52d48010979d226d3a36b011b692726d1ff52012e8dc626d03f470142fc6426ce61780158cb1626cc63f90170116426ca44bb0188e86326c8019401a36ad026c5983501bfb52626c3062f01dde5bf26c048ed01fe1cf026bd5db302207d2926ba419e02452b1326b6f1a2026c4db926b36a8802960eab26afa8ec02c29a2226aba93d02f21f2b26a767bb0324cfd526a2e076035ae157269e0f4f03948c472698eff603d20cc526937dea0413a2b0268db47c045991de26878ecd04a4224c268107d404f3a05f267a1a5d05485d172672c11205a2ae4e266af67c0602eef52662b50b06697f4f2659f72306d6c52f2650b721074b2c362646ef6e07c7260b263c9a8d084b2a9b2631b33008d7b8482626344e096d5421261a19450a0c8a0a260d5df80ab5ece225fffefa0b6a169b25f1f9bd0c29a84a25e34ccc0cf54a2125d3f80e0dcdab5825c3fd120eb381fe25b35f6d0fa78aab25a2252110aa880d2590571a11bd4245257e01c012e08614256b3599141523c32558080d155bedb62544944316b5b6a92530fc2718234f6d251d699019a58421250a0f9e1b3d18ba24f72c451ceac4c224e50a1e1eaf2e1624d4027f208ae27824c47fe3227e4fb524b700be2489ba0224ac1ac126ad304624a47ea628e87dc424a0fca92b3b18b624a289bc2da40d0d24aa45a23021e2b424b9822032b27e4924d1cb7a3552fb5824f4f26637ff7ee0252517cb3ab300fb2564ba863d670c9225b6c76140137474261eab6f42adfe3f26a06876452a05892740aac947781de52804de7c4985c1cc28f340054b3d2a122a12e01c4c8581142b6b8b5a4d43ccce2d0577eb4d5d29f12ee880174cbb4a48311a7a4d4b547c9f339bd7ff49385020366114e8469f924e39475942000aae9c1eca590b000b67d41eca4e55000c2d981eca42e4000d00c01eca36ad000de2351eca29a3000ed2ef1eca1bb7000fd3f71eca0cd90010e6661ec9fcfa00120b6b1ec9ec08001344481ec9d9f0001492551ec9c69f0015f7011ec9b200001773d31ec99bfc00190a6f1ec9847a001abc931ec96b61001c8c1d1ec95096001e7b091ec933fb00208b771ec915700022bfac1ec8f4d600251a141ec8d20700279d441ec8acde002a4bff1ec88532002d29371ec85ad8003038101ec82da200337be71ec7fd5f0036f8501ec7c9d9003ab1201ec792d9003eaa6b1ec758230042e88e1ec71977004770311ec6d691004c464a1ec68f28005170281ec642ef0056f3741ec5f194005cd6381ec59abf00631ee81ec53e110069d4651ec4db260070fe091ec471950078a3ab1ec400ec0080cda81ec388b1008984f11ec308640092d30c1ec27f7c009cc2261ec1ed6600a75d191ec1518800b2af7b1ec0ab3b00bec5a61ebff9cf00cbaccc1ebf3c8a00d972fe1ebe72a300e8273e1ebd9b4800f7d98f1ebcb59701089b061ebbc0a2011a7ddd1ebabb6a012d95811eb9a4e20141f6ad1eb87bee0157b77b1eb73f5d016eef7e1eb5edf10187b7d61eb4865401a22b4f1eb3072001be66791eb16eda01dc87c51eafbbf101fcafa61eadecbe021f00af1eabff8402439fb71ea9f26f026ab3fc1ea7c3920294674b1ea570e802c0e6281ea2f85502f05ff81ea057a30323072d1e9d8c84035911791e9a94940392b7fd1e976d5603d0377d1e94143a0411d0961e9086990457c7f91e8cc1bf04a266a51e88c2e704f1fa231e8487460546d4ca1e800c0a05a14dfd1e7b4e650601c26e1e764b95066894691e7100e906d62c131e6b6bd4074af7b71e6589f807c76c091e5f5935084c04701e58d7c208d943481e520444096fb2271e4addea0a0fe21a1e4364910aba6bdd1e3b98ec0b6ff00a1e337cb30c3117431e2b12dd0cfe92461e225fe00dd919f71e196a010ec16f4e1e1039a90fb85b311e06d9d510beae251dfd588c11d53fd81df3c77012fcee761dea3c6514369dc21de0d257158335dd1dd7aa1816e3a1ad1dceeb6e1858cccf1dc6c64419e3a0fe1dbf74181b8502c21db9399d1d3dcd4f1db468ab1f0ecd5b1db1628520f8baab1db09a7f22fc30181db299242519a1b01db7ffec275150791dc18da429a33b561dd023ac2c0f0c661de4cc382e9402071e00c1d73130d2821e25787a33e3892f1e54a86136a95ba21e905b4b397e752a1edafc743c5db6c91f376be13f4069831fa9159b421de12b20340d4f44eb0e5c20dd2e92479a001f21aa41464a19599722a220034c53c85623ccdb634e2f97b62533ceb14f8e9c4126e18f17504ee9d128e1884f504d28ef2b3ef1044f69fa7c2e0273ce4d94998a312d588a4add1e1634b00910478db28238594630000aa5391859f387000b5dcf1859ecd9000c22e61859e5b8000cf5561859de1b000dd6061859d5fb000ec5ef1859cd4d000fc6161859c40a0010d7971859ba260011fb9e1859af960013336b1859a45000148056185998460015e3cd18598b6c00175f5618597db40018f49318596f0e001aa54018595f6a001c733a18594eb8001e607d18593ce500206f26185929dd0022a1781859158d0024f9dd1858ffdd00277ae91858e8b6002a275c1858cffe002d02261858b59c00300e691858997100334f7f18587b600036c8fa18585b48003a7eab18583906003e74a5185814740042af411857ed6b004733231857c3c1004c05401857974800512ae1185767d10056a9ad18573529005c87ab1856ff180062cb491856c56500697b65185687d100709f551856461b00783eec1855fffd008062841855b52b0089130618556555009259f718551028009c417e1854b54900a6d4711854545700b21e621853ecee00be2ba818537e9f00cb096e185308f900d8c5c518528b8100e76fa9185205b400f7171d185177090107cd321850deee0119a42118503cc7012caf59184f8ff101410393184ed7be0156b6ee184e1375016de100184d425601869af1184c639201a0ff94184b765201bd2b86184a79b301db3d4918496cc401fb556118484e8b021d967a18471e000242258a1845da0f026929f4184481980292cdb01843137102bf3d7718418e6002eea8ec183ff124032142d0183e3a700357412a183c68ee0390dd84183a7b4203ce551b18387008040fe91e183645dc0455dee31833fb5704a0802a18318f1804f01b5f182effc5054503de182c4c15059f9236182972d306002478182672e606671e8018234b5e06d4ea43181ffb820749f81f181c82d607c6bf2a1818e135084bbd86181516df08d978b11811249509707dd6180d0bb20a1162141808ce4f0abcc2d318046f660b7345fa17fff3050c359a3717fb5e800d04772417f6b8b10de09d6f17f20a440ecad6e617ed5e080fc3f66c17e8c15e10ccd7d217e444a511e65f8417dffbcf13117a0b17dbfefd144f1b5117d86b4115a03d9417d5637e1705e00817d3116d188104f917d1a6d51a12af6917d15ef51bbbdff617d280301d7d90f217d55e0a1f58b16217da5b82214e1eb817e1eddc235e9cf717ec9ffc258accd117fb165e27d31f53180e13f32a37c68618267fec2cb8a23b18456cd42f55281e186c213d320c45eb189c225d34dc3c4d18d7413037c2709e191faaba3abb33611977fc343dc178d419e35c2f40ce80791a6599bf43d9683a1b03530e46d6a7ba1bc2246349b7716b1ca8e0504c68fa0e1dbfcff04ed3aebd1f10f64c50da725c20a849f3525a1e322293c6d35329c80d24e319c8531cd75f27a668595208e2842aeb43614fd2b1c52eb603674c86d8f732f47dca487f0ddc37661574000a9db9133ee06d000b55ce133edc45000c1a5a133ed7d4000cec37133ed317000dcc4a133ece07000ebb8b133ec89f000fbb00133ec2db0010cbc2133ebcb20011eefd133eb61e001325f1133eaf19001471f5133ea79a0015d474133e9f9900174ef6133e970e0018e31a133e8def001a929d133e8433001c5f58133e79cd001e4b47133e6eb400205885133e62db00228955133e56360024e01f133e48b500275f74133e3a4c002a0a14133e2ae9002ce2ec133e1a7d002fed1e133e08f500332c00133df63e0036a323133de245003a5656133dccf3003e49a9133db63100428172133d9de700470254133d83fb004bd140133d68500050f37e133d4aca00566eb1133d2b47005c48db133d09a80062886b133ce5c600693439133cbf7d00705399133c96a30077ee59133c6b0d00800cd0133c3c8d0088b7e5133c0af20091f918133bd608009bda8e133b9d9700a66718133b616400b1aa44133b213000bdb067133adcba00ca86aa133a93bb00d83b16133a45e800e6dcab1339f2f100f67b6513399a840107285513393c470118f5b31338d7dc012bf6ec13386ce1014040bc1337faed0155e94213378191016d08181337005a0185b66b133676cf01a00f141335e46e01bc2eba133548b201da33e91334a30f01fa3f371333f2f3021c7361133337c60240f574133270eb0267ecef13319dbf029183ed1330bd9a02bde751132fcfd002ed46ef132ed3b3031fd5c1132dc8930355ca15132cadbd038f5dc6132b828203ccce71132a4633040e5db51328f82c0454516b132797ce049ef3ec1326248804ee945713249ddc054386d313230365059e24e0132154d905fecda3131f92170665e634131dbb2f06d3d9f7131bd06a07491af11319d25d07c6221e1317c1f4084b6fcc1315a08b08d98bf713136ffb097106a5131132bf0a12783b130eec0b0abe81da130c9ff40b75cdb0130a53990c390f4313080d560d0903b81305d5000de672091303b4270ed22b2b1301b66a0fcd0a2212ffe9d310d7f3f312fe5f4a11f3d77912fd2b161321ad0a12fc6579146275e212fc2b6215b73b4812fc9f4717210d5c12fdea1f18a1017213003c8e1a382fe71303d0441be7b1451308e9a51db09a9a130fd9be1f93f8b81319009c2192ca311324d01b23adf7bc1333cf4f25e64a8613469ea5283c6012135dfce32ab09ae8137acd572d430f5a139e1f6e2ff36b4e13c9382832c0d7d813fd9dde35a9d2f4143d271738abff57148a0d453bc3e7b914e704903eecb25915575a36421fc09015df1b584554359216834686487e5ea2174a0aa44b8ef6d1183b15b34e7241f0195ff4f6510efff61ac4841f534549551c77602754ed891d1e8a3d4355d81ab52111d23655cebc562424af5e549a57df27d7a7035211e3cc2c3531c44e39ab3e312b552e4977bd5e366a386a000a98240f331be6000b4fd90f33194f000c13ff0f33168c000ce56e0f331399000dc50c0f331072000eb3d00f330d15000fb2c00f33097e0010c2f40f3305a90011e5980f33019200131beb0f32fd33001467420f32f8890015c90a0f32f38f001742c90f32ee3e0018d61c0f32e891001a84c00f32e283001c508e0f32dc0b001e3b800f32d524002047b10f32cdc5002277620f32c5e70024ccfa0f32bd8100274b0a0f32b48b0029f44f0f32aaf9002ccbb60f32a0c3002fd45e0f3295dc0033119e0f328a39003687040f327dce003a385d0f32708d003e29b70f32626800425f690f32534f0046de110f324333004baaa00f3232020050ca5b0f321fa9005642e20f320c16005c1a380f31f733006256c60f31e0eb0068ff650f31c92500701b640f31afc90077b28f0f3194bb007fcd3d0f3177e0008874500f31591a0091b1460f313848009b8e400f31154900a616100f30eff900b154400f30c83100bd55220f309dca00ca25dc0f30709700d7d4790f30406d00e66ff30f300d1c00f608470f2fd6700106ae850f2f9c35011874e30f2f5e33012b6ed10f2f1c2f013fb10a0f2ed5ea015551b10f2e8b25016c68600f2e3b9a01850e4b0f2de703019f5e510f2d8d1701bb75200f2d2d8701d971500f2cc80601f973800f2c5c40021b9e820f2be9e2024017720f2b7096026705e90f2af0050290941f0f2a67d602bcef160f29d7b202ec46cc0f293f43031ece6a0f289e330354bc780f27f434038e4b110f2740fa03cbb8220f268442040d45a20f25bdd5045339d50f24ed87049ddf900f24134004ed86800f232efc054283710f2240d5059d30a40f21490305fdee190f2047eb066521eb0f1f3e2106d338a40f1e2c770748a5990f1d140a07c5e34e0f1bf64b084b73cf0f1ad51608d9e11a0f19b2c60971bd800f1892480a13a4080f17773c0ac038d50f1666150b7829820f15643d0c3c2d830f1478460d0d06750f13aa1e0deb806b0f13034e0ed872270f128f430fd4bd470f125ba810e14e520f1278c711ff1ca70f12fa09132f2a450f13f67c1472835c0f15898415ca3d9c0f17d3991737772a0f1afb3918bb55350f1f2dfe1a5701fe0f24a1ef1c0baa3e0f2b970a1dda79b90f34592d1fc496cb0f3f424e21cb1cb70f4cbd4423ef14580f5d491426316ad10f717d0a2892e5c40f8a0dc42b1414580fa7d36b2db53c4e0fcbd188307642030ff740cc33568a16102b9b893654d2eb106aad91396f03c110b6a8ab3ca1ee7411123f0d3fe9000a1180c5de433ddb21120662694697d5cf12a8457649eb52f6136cf9204d28ed7b145cc662503c6b3d15823776530b704616eab9df5573f64d18a75a7b574aae3c1acd7f065859c69f1d77492558615a4720c2d318571c7eb824ce747b5451358929ae59d64ff63d102f54cacc4a795ee635645f74000a942c0bff4229000b4b9d0bff408d000c0f7a0bff3ed5000ce09b0bff3cff000dbfe60bff3b0a000eae520bff38f2000face30bff36b70010bcb20bff34550011deea0bff31ca001314cb0bff2f1200145fa80bff2c2c0015c0ee0bff291300173a210bff25c50018cce00bff223e001a7ae60bff1e7a001c460c0bff1a75001e304b0bff162b00203bbd0bff119600226aa30bff0cb20024bf620bff077a00273c8b0bff01e80029e4da0bfefbf6002cbb3c0bfef59e002fc2ce0bfeeed80032fee50bfee79e003673100bfedfe7003a231a0bfed7ac003e13100bfecee3004247470bfec5840046c45d0bfebb83004b8f410bfeb0d80050ad360bfea575005623dc0bfe9950005bf9330bfe8c5b006233a30bfe7e890068da040bfe6fcc006ff3a30bfe60130077884b0bfe4f4f007fa0500bfe3d6f008844940bfe2a6000917e920bfe160e009b586b0bfe006600a5dcee0bfde95100b117a40bfdd0b800bd14de0bfdb68400c9e1c10bfd9a9a00d78c560bfd7cdf00e623970bfd5d3600f5b7810bfd3b83010659240bfd17a501181ab60bfcf17c012b0fa80bfcc8e5013f4cb70bfc9dbc0154e8070bfc6fdc016bf9380bfc3f1e018499810bfc0b5a019ee3c70bfbd46801baf4c00bfb9a1b01d8eb0b0bfb5c4b01f8e7570bfb1acb021b0c7f0bfad56f023f7fb30bfa8c0d0266689f0bfa3e7a028ff1920bf9ec8d02bc47ac0bf9961f02eb9b0d0bf93b0e031e1f050bf8db3a03540a490bf8768b038d972d0bf80cf003cb03dd0bf79e62040c929a0bf72ae5045289fe0bf6b290049d35440bf6358704ece48a0bf5b40a0541ed270bf52e71059ca9f40bf4a53705fd7ba50bf418ff0664c9240bf38a9d06d2ffe80bf2fb1d0748945a0bf26bd007c602350bf1de5b084bccf10bf154c108da80280bf0d17c0972b0050bf0578a0a14f9ae0befea8e0ac203b30bef8eea0b7a7e740bef49e00c3f24910bef21bc0d10bb440bef1e050df012bf0bef47b50ede06790befa9780fdb7d6a0bf04ffd10e96a320bf14a531208cb210bf2aa52133aaa1a0bf4851f14801c450bf6f3c315da41800bfa13e0174a43820bfe088818d1549b0c02fb411a70adee0c091d361c298d140c10a8ac1dfd30f00c19e2c31fecd58a0c251d9321f9aead0c32bac32424e0f90c432ebc266f78fc0c57049028da5fe00c6ee2e12b664cee0c8b91fc2e13b3300cae039130e2aa040cd75c8e33d2cf4d0d0901b636e321670d44a7fd3a11ce810d8c69df3d5bf6220de2e37840bd58a70e4b57d6442fef090ec9e2db47ab63410f63bc544b245f43101f92784e8ba555110603fa51cce1a31222436654cd23b81382edb25768f460153b183b5972171b1763856d5aad57f61a1bb3275ad19fd31d89de66598b982921d7bb1a568d9dee2726d35451bb61702d72d5a54b845ed634544f32000a917009770a99000b48b109770999000c0c5c09770887000cdd4809770764000dbc5a0977062c000eaa88097704df000fa8d90977037c0010b863097702010011da510977006c00130fe20976febc00145a6b0976fcef0015bb580976fb020017342b0976f8f50018c6850976f6c4001a741e0976f46d001c3ed10976f1ee001e28940976ef43002033830976ec6b002261dd0976e9620024b6080976e624002732930976e2af0029da390976defe002cafe80976db0d002fb6bb0976d6d90032f2080976d25d0036655b0976cd93003a147f0976c878003e03820976c305004236b70976bd350046b2ba0976b701004b7c7a0976b0630050993a0976a95500560e980976a1ce005be294097699c700621b94097691380068c07009768818006fd87309767e5d00776b68097673fe007f81a1097668f00088240009765d2800915bff0976509a009b33bd0976433b00a5b609097634fc00b0ee6c097625d000bce936097615a900c9b38b0976047800d75b750975f22c00e5efec0975deb600f580ef0975ca0201061f8d0975b4000117ddff09759c9d012acfb6097583c5013f0972097569630154a15909754d64016baf1009752fb101844bd009751036019e92860974eedd01ba9fed0974cb9001d892af0974a63a01f88b8309747ec7021aad5009745521023f1d5709742937026603530973faf8028f89a80973ca5702bbdd8e0973974802eb2f42097361c5031db235097329ce03539d430972ef67038d2aed0972b2a003ca999309727390040c2bb40972325c045228320971ef38049cda960971aa6904ec93610971644b0541a85509711d54059c74cb0970d61905fd5a0809708f530664bf9d097049e906d313c1097006f60748cbbc096fc7d307c66445096f8e22084c61f8096f5bde08db51be096f33680973c93f096f179a0a166757096f0be00ac3d489096f144e0b7cc376096f35bf0c41f148096f75fb0d142626096fdbdf0df4359809706f8d0ee2fee009713aac0fe16d4d097248a510f078700973a6fc1211243c097565ab1344810109779796148bab36097a531515e7cb0e097db293175a13bd0981d55018e3c2600986e04a1a861c69098cff541c426d75099466661e1a0463099d5338200e2f7009a80f352220372e09b4f1de245157f409c463c526a2b96a09d6e237291563b409ed03db2baa31960a077e872e61bebb0a272eae313c51130a4d20f03439bbe80a7a9e7c37593abe0ab13d563a9941a20af2f5cf3df73f830b423f44416f4e180ba236dc44fbc92b0c16d4474894c4950ca5322b4c2f552a0d53f22c4fbc9c1c0e2bc7ba53287eed0f38385e5657f0771088a3b15926ae171231a44d5b6463f5144ecc245cd170d0170485505d1c5bab1a8138a95be362421efb28fc58c32ed724a490505386f19b2b8852164c988708333a5fa4000a8f98077700c8000b46ba07770029000c0a430776ff7f000cdb0a0776feca000db9f60776fe08000ea7fb0776fd3a000fa6200776fc5d0010b57b0776fb710011d7370776fa7600130c940776f96a001456e40776f84b0015b7950776f719001730280776f5d30018c23d0776f477001a6f8e0776f303001c39f30776f176001e23640776efce00202dfb0776ee0a00225bf70776ec280024afbe0776ea2500272bdf0776e8000029d3150776e5b6002ca84b0776e344002fae9f0776e0a90032e9640776dde100365c280776dae9003a0ab30776d7be003df9140776d45e00422b9c0776d0c40046a6e90776cced004b6fe80776c8d400508bdb0776c476005600600776bfce005bd3760776bad700620b830776b58c0068af5e0776afe8006fc6520776a9e5007758290776a37d007f6d3507769cab00880e56077695670091450807768daa009b1b680776856d00a59c4507767ca900b0d3270776735400bccc5f0776696800c9951107765edb00d73b47077653a300e5cdf9077647b800f55d2707763b0f0105f9e207762d9f0117b66307761f5d012aa61d0776103d013eddd207760037015473ac0775ef3e016b7f520775dd4901841a030775ca4c019e5eaf0775b63e01ba6a1a0775a11401d85af307758ac601f851fb0775734c021a722507755aa0023ee0bc077540be0265c58c077525a2028f4b090775094f02bb9e810774ebc702eaf0470774cd16031d73e80774ad470353606107748c72038cf05807746ab203ca62590774482f040bf9130774251b0451fba5077401b8049cb5da0773de5504ec78800773bb58054199b10773993f059c752e077378a105fd6cb307735a390664e85607733ee806d356ec077327bf07492e6d0773160407c6ec6007730b3f084d164a0773094508dc3a22077312460974eec2077328da0a17d46a077350190ac5952e07738bad0b7ee57c0773dff00c44848d077452070d173ce20774e8090df7e4b30775a92b0ee75e5307769def0fe698910777d06410f68efe07794c6912184a1d077b2008134cdf70077d5bd2149571620780135b15f32eee07835dcb176753070787568418f323a4078c1df21a97f0560791da851c57104d0798b9dd1e31dfa807a0f23a2029bbd707aac440223ffedf07b67d232475f92707c4795d26cce97507d5280e2945f2a107e90f422be20e530800d1642ea1fc13081d343931862b8b083f29f1348ea0a70867dd0837bacfc30898bfff3b096f6208d3a26c3e783c1c091acd724203aa1709712abd45a67d8709da7a61495940e60a5b9e324d118ba60afb03f950c106420bc13c77545410a30cb9d2d157afe5840df47f405ab00bfe0f86d5755d22ea53118e89ea5ec57e0b14343b8c5f3f064617ae07345e1fe67d1c3f37245aedc951222d5bbe55564a74299885b44db543ff32173dce000a8e5f05e2d1e4000b456c05e2d182000c08de05e2d118000cd98e05e2d0a7000db86005e2d02f000ea64a05e2cfaf000fa45205e2cf260010b38e05e2ce940011d52a05e2cdf800130a6305e2cd510014548f05e2cc9f0015b51705e2cbe100172d8005e2cb170018bf6805e2ca3f001a6c8905e2c958001c36bb05e2c862001e1ff505e2c75b00202a5205e2c6430022581105e2c5170024ab9605e2c3d80027277205e2c2840029ce5e05e2c118002ca34505e2bf95002fa94605e2bdf70032e3b205e2bc3e0036561705e2ba67003a043f05e2b872003df23605e2b65b0042244e05e2b42000469f2405e2b1c0004b67a505e2af370050831305e2ac840055f70b05e2a9a4005bc98d05e2a693006200fd05e2a34f0068a43305e29fd4006fba7905e29c1f00774b9905e2982d007f5fe405e293fa0088003c05e28f820091361a05e28ac1009b0b9d05e285b200a58b9305e2805100b0c18505e27a9a00bcb9c305e2748800c9817205e26e1500d7269c05e2673d00e5b83b05e25ffa00f5464f05e258480105e1e905e2502001179d4505e2477d012a8bd705e23e5b013ec26505e234b30154571905e22a82016b619f05e21fc10183fb3905e2146e019e3edd05e2088401ba495405e1fc0001d8395305e1eee101f82fa305e1e125021a4f4005e1d2cf023ebd8105e1c3e10265a23c05e1b460028f27f705e1a45502bb7c0f05e193cb02eaceeb05e182d3031d542f05e17181035342f305e15ff2038cd5fc05e14e4903ca4bf805e13cb1040be7c205e12b600451f0a405e11a9a049cb2a505e10ab004ec7ece05e0fc060541ab8305e0ef13059c94d705e0e46a05fd9ce505e0dcb706652c3305e0d8cb06d3b21105e0d99f0749a50905e0e05b07c7834505e0ee61084dd30905e1055408dd232205e1272409760b6505e1561f0a192d2a05e194fd0ac733cb05e1e6f80b80d52705e24fdd0c46d22005e2d42b0d19f71b05e3792f0dfb1c7605e4452e0eeb26fe05e53f890feb085405e670f910fbbf4105e7e3c7121e57f605e9a4161353ec2c05ebc03d149da31a05ee492915fcb14005f152e2177257db05f4f51618ffe41c05f94bd71aa6adda05fe786f1c6815c80604a2701e4582f3060bf8f420405f650614b434225a13af061f17762494010e062b738126ef79d7063a29a6296db7a5064bafab2c0fcebf066094c12ed69de5067987fc31c2b98c069760bf34d4512606bb29e5380b0cbf06e630a53b65e072071a18b73ee2d26e0758f7e7427eaecc07a57c434634a296080321a949fdb44808767dce4dd00b880905ad78519df2fc09b8f306555474bb0a9b9e6e58d963630bbd61e75c088f8d0d3443765eafdb470f1f62f06089f33711aab1e0613819e3151324c9603de84219a8d3275d098b231fc66ac957269a4027a6d1cb4ed9ca4230ebc9e9000a8d9204a3ef6f000b449104a3ef32000c07f504a3eef0000cd89504a3eeaa000db75704a3ee60000ea52f04a3ee10000fa32404a3edbb0010b24c04a3ed600011d3d204a3ed00001308f504a3ec980014530804a3ec2a0015b37604a3ebb400172bc404a3eb360018bd8e04a3eab0001a6a9004a3ea21001c34a104a3e989001e1db804a3e8e6002027ef04a3e8380022558604a3e77f0024a8e104a3e6b90027248f04a3e5e60029cb4c04a3e505002ca00004a3e415002fa5cb04a3e3150032dffe04a3e2040036522704a3e0e1003a000f04a3dfab003dedc204a3de6000421f9204a3dcff00469a1c04a3db88004b624d04a3d9f700507d6604a3d84d0055f10504a3d687005bc32804a3d4a30061fa3604a3d2a000689d0304a3d07c006fb2dc04a3ce350077438a04a3cbc9007f575d04a3c9350087f73804a3c67700912c9404a3c38e009b018f04a3c07600a580f904a3bd2e00b0b65a04a3b9b100bcae0204a3b5ff00c9751804a3b21400d719a504a3adee00e5aaa504a3a98900f5381704a3a4e40105d31004a39ffc01178dcb04a39acd012a7bbf04a39557013eb1b304a38f97015445d604a3898b016b4fd304a383320183e8f304a37c8b019e2c2f04a3759601ba365304a36e5501d8261d04a366c801f81c5a04a35ef3021a3c0f04a356da023eaa9c04a34e8502658fe104a345fc028f167104a33d4a02bb6bb604a3347e02eac02804a32bac031d477e04a322ea035338e604a31a56038ccf3e04a3121303ca495104a30a4c040bea1b04a303370451f90f04a2fd12049cc25c04a2f82b04ec974104a2f4dd0541ce5d04a2f397059cc40304a2f4db05fdda9e04a2f94506657b0a04a3019106d414fe04a30e99074a1f7504a3216407c8192104a33b27084e88da04a35d5008ddfe1e04a389910977118604a3c1e80a1a654f04a408b00ac8a5d604a460b20b828a2304a4cd350c48d46b04a552170d1c529604a5f3e60dfddec004a6b8010eee5faf04a7a4be0feec94904a8c19511001ced04aa1753122369c204abb05d1359cce504ad98f614a4717104afdf9e1604905604b29576177b6fef04b5ceca190a634804b9a3a51ab2c8f904be30981c76097904c3979b1e5594cf04ca012f2052df6a04d19dc0226f5de804daa75c24ac7f9204e563db270ba72504f227a0298e217e050159102c351999051375192f01891c0529150e31f424840542f662350d41a6056204ed384cb6c3058768d33bb1afec05b4996a3f3a775f05eb776342e42c4b062e717146aa61440680b8504a86989706e689af4e6f8fa107659d925258429f0805c812562e861808d1eb6459d9008209d964e75d3433f10b3234b3600e28c30cfc350c62203fc00f65b6c3630722ce12b16649623b138d173b55465f130d9f1d74246c58f512c925b6818550052c952fb90328000a8d0d03a86fc7000b440303a86fa1000c075e03a86f78000cd7f403a86f4d000db6ab03a86f1e000ea47803a86eed000fa26003a86eb80010b17b03a86e800011d2f403a86e440013080803a86e040014520b03a86dbf0015b26903a86d7600172aa503a86d290018bc5c03a86cd5001a694a03a86c7d001c334503a86c1e001e1c4603a86bb90020266503a86b4e002253e303a86adb0024a72303a86a60002722b403a869de0029c95203a86953002c9de603a868be002fa38f03a868200032dd9e03a8677700364fa003a866c40039fd5f03a86604003deae703a8653800421c8a03a8645e004696e503a86377004b5ee303a86280005079c703a8617a0055ed2f03a86063005bbf1803a85f390061f5e803a85dfd0068987603a85cad006fae0c03a85b4800773e7403a859cc007f51ff03a858390087f18f03a8568d0091269d03a854c6009afb4903a852e500a57a6003a850e600b0af6d03a84eca00bca6c003a84c8e00c96d8003a84a3100d711b603a847b200e5a26003a8451000f52f7d03a8424a0105ca2403a83f5f0117849003a83c4d012a723b03a83915013ea7ed03a835b501543bd703a8322f016b45a803a82e830183deaa03a82ab1019e21db03a826bc01ba2c0b03a822a601d81bfb03a81e7301f8128103a81a27021a32a603a815c9023ea1d103a81160026587ed03a80cf7028f0f9503a8089a02bb664003a8045902eabc7203a80046031d45f403a7fc7803533a0403a7f90b038cd39303a7f62003ca518703a7f3e0040bf6f603a7f27b04520b7003a7f22a049cdb4b03a7f33304ecb7ed03a7f5e70541f82403a7faa8059cf87a03a801e805fe1b9703a80c320665ca9e03a81a2606d4759703a82c84074a93db03a8442e07c8a48403a8622e084f2ee603a887c008dec30703a8b6570977fa2103a8efa80a1b772503a935b70ac9e74203a98ae20b84026b03a9f1f50c4a8be703aa6e390d1e52d203ab038f0e0032ac03abb6880ef113d203ac8c830ff1ebf803ad8bd61103be9103aebbfc12279d2603b025c4135ea78d03b1d39814aa0c0003b3d1c5160b070703b62ed81782e31b03b8fc0d1912f80a03bc4dd91abca9e303c03c881c81677503c4e50c1e62a81c03ca69f42061e8cc03d0f49f2280a81703d8b6be24c060ea03e1ec3c272283b203ecdda729a86d7803f9e34b2c535c71040969372f246139041bf483321c4bed04322a4d353b93d1044cd915388237ea046d057a3bef964f0493fbb93f82370b04c3681d4337860f04fd798c470b75b3054513274af7ffe3059e14af4ef4770f060dc5b852f48f4c069b76e156e6fa99075177e65ab35cdd083e939d5e3739e209785f3d61414f970b1ecf88638aa1320d61a46364aca6ac1087fe7d641602b614f8a14b610784c21b3a0cbb5abf09d823caaa1c51366a262e7ffaaa000a8cb802e221ad000b43a802e22195000c06fd02e2217c000cd78c02e22161000db63c02e22144000ea40202e22126000fa1e302e221050010b0f602e220e20011d26502e220bd0013077002e220950014516902e2206b0015b1bc02e2203d001729ed02e2200d0018bb9902e21fda001a687902e21fa3001c326702e21f68001e1b5902e21f2a0020256a02e21ee7002252d702e21ea00024a60602e21e540027218502e21e040029c80f02e21dae002c9c9002e21d52002fa22302e21cf00032dc1b02e21c8800364e0502e21c190039fbab02e21ba3003de91902e21b2600421aa002e21aa0004694dd02e21a12004b5cbc02e2197a0050778002e218d90055eac602e2182e005bbc8c02e217780061f33702e216b60068959f02e215e9006fab0d02e2150f00773b4c02e21428007f4ead02e213330087ee1102e2122f009122f302e2111c009af77202e20ff900a5765c02e20ec500b0ab3b02e20d8100bca26102e20c2a00c968f402e20ac100d70cff02e2094600e59d7f02e207b700f52a7602e206150105c4fa02e2045f01177f4902e20296012a6cdd02e200ba013ea28002e1fecc0154366502e1fccb016b403d02e1fabb0183d95402e1f89d019e1cac02e1f67301ba271902e1f44101d8175e02e1f20b01f80e5702e1efd7021a2f1202e1edaa023e9efd02e1eb8d0265860a02e1e98a028f0edb02e1e7ad02bb66f102e1e60402eabedc02e1e4a1031d4a7002e1e39a035340fa02e1e306038cdd7d02e1e30503ca5eef02e1e3ba040c087f02e1e551045221d502e1e7fb049cf76402e1ebf504ecdab202e1f186054222b302e1f902059d2c1e02e202ce05fe59ca02e20f5e0666151402e21f3d06d4ce4502e2330e074afd0002e24b9307c920b402e269af084fc11502e28e6c08df6e9902e2bb060978c2f902e2f0ef0a1c61b602e331da0acaf8a502e37fca0b85407702e3dd190c4bfd4a02e44c8f0d1fff3502e4d16f0e0222d002e56f930ef351bf02e62b830ff4832702e70a961106bc2602e81318122b102b02e94c761362a13c02eabf7714aea01602ec767a16104c2202ee7dc71788f32d02f0e3e91919f0d902f3ba281ac4ada502f715101c8a9d8302fb0d221e6d3dca02ffbfa9206e126703054fc3228ea216030be7b224d0715f0313ba842734fc0c031d063229bdaca8032816572c6bd190033547c02f408ed803450d20323ccc380357f54b35611dd0036eb3a838ada634038a2bbb3c21efa403ab81223fbcb97203d42e19437bb5460406239a475b2dec0443f7fe4b558e1904912bca4f62b83804f290ec53771778056ee85d57824390060fd7015b6cf79906e367f65f15f31e07fe7567624d1c6c098085a164cbe9890b99e8ae6629f8420e94e65c65ce2c0f12e15bf962e4c907191ac6d05c820da221e6175a526c78332d41ca7e",
    "relocs": [
     [
      530,
      "bss",
      0
     ],
     [
      542,
      "code",
      562
     ],
     [
      36,
      "bss",
      0
     ],
     [
      86,
      "bss",
      0
     ],
     [
      102,
      "code",
      634
     ],
     [
      218,
      "bss",
      0
     ],
     [
      238,
      "code",
      1848
     ],
     [
      268,
      "bss",
      0
     ],
     [
      290,
      "code",
      634
     ],
     [
      444,
      "bss",
      0
     ],
     [
      460,
      "code",
      634
     ],
     [
      816,
      "code",
      3438
     ],
     [
      822,
      "code",
      2406
     ],
     [
      1244,
      "code",
      3438
     ],
     [
      1250,
      "code",
      2406
     ],
     [
      1704,
      "code",
      3438
     ],
     [
      1710,
      "code",
      2406
     ],
     [
      1916,
      "code",
      1996
     ],
     [
      1962,
      "code",
      1996
     ]
    ],
    "symbols": {
     "smpf_process": [
      "code",
      0
     ],
     "smpf_reset": [
      "code",
      502
     ]
    },
    "bss": 444
   },
   "cost": {
    "emulation": {
     "lowpass": 844,
     "highpass": 898,
     "centre": 52,
     "glide": 1388,
     "silent": 165,
     "first": 1422,
     "pattern": "instructions per track and block, Samples' own code only (smpf_process, smp_filter_set, smp_filter_run, the frame loop), on the OS 1.13 in tools/emu/test_fltslot.py's filter_cost (mcengine.py's counter): all six tracks on it, the stock machines playing, a state held for 8 blocks after 8 of warm-up (lowpass Cutoff 32, highpass 96, centre 64, glide: Cutoff 48 / 88 and Reso every block; silent: no note played, the filter set and rung out), the maximum, and the block in which the tracks come to it from none (its reset and first block); the filter slot's own instructions apart"
    },
    "device": {
     "status": "not measured"
    }
   }
  },
  "crush": {
   "id": "crush",
   "name": "Crush: a sample-rate and bit reduction on every track, Rate on SWEEP and Bits on CONTOUR",
   "order": 73,
   "version": "0.5",
   "symbols": {
    "update": "crush_process",
    "render": "crush_reset"
   },
   "keep": [],
   "patch_points": [],
   "uses": [
    {
     "point": "track.filter",
     "id": 2,
     "process": "crush_process",
     "reset": "crush_reset",
     "name": "Crush",
     "short": "CRU",
     "params": [
      {
       "long": "Crush Rate",
       "short": "RATE",
       "format": "cutoff"
      },
      {
       "long": "Crush Bits",
       "short": "BITS",
       "format": "int",
       "start": 32512
      }
     ]
    }
   ],
   "conflicts_declared": [],
   "claims": {},
   "bundle": {
    "code": "4fefffc0700548d73cfc262f004c246f0044206f0048b083650000de7b500c8500007f006e0001f04a856d0002087d6800020685ffffc00020060c8600007f006e0001b84a866d000206223c00007f00242a007c92804a85660000a80c8600007eff6e000446780c4c0438004bf90000000041f538004aa800046600022c4aa800086600022420028092660006b6207c00010000280a428043ea000406840000007c8099b3c466fa4a80670006b60c8600007eff6f0002ce20353800223538084a856f000490240193c9220a068100000080d0880c8000010000650a24090680ffff0000225224c9b28a66e62b8038002b8938042b8238084cd73cfc4fef00404e7520054a856d0001842800e08c7e40be8467000186718043f90000000020714c002e089eb14c044c070800e08891c04aaf005067000130700c4c0038004bf900000000267c0000ffff2b8b380047f53800226b00044a89660001f8282b00084a8466000368200280926700ff280c8600007eff6f0002102035380042824a856e00ff482a082e094840424048454245e2872c02e28647ea0080204791c628002200d88520072e062c092241b885641222122e062001e287e28024062c01204091c7d885b885650001ac2204e289a2080800a1c1d287d28124c1b7ca66ceeb8d200922462b8938042b823808d085424048402b8038006000ff00203c00007f00223c00007f00242a007c92804a856600fef26000fe487d6800022a3c00007f000685ffffc00020060c8600007f006f00fe1460c67d68000242850685ffffc00020060c8600007f006f00fdfa60ac4280223c00007f00242a007c92804a856600fea26000fdf87e014847780c4c0438004bf900000000beb538006200fed2267c0000ffff2b8b38006000fec444802800e08c7e40be846600fe7e307c04004aaf005067c26000fe92c2fc0007787f4c4410012c01e0897d86264147eb0018284628067a01200b2c055380e1ae2e064486e28f4a8c67000286220be3ad43ea00802005e28844852040201ae2802200d287c2860c813fffffff6e50d281d088c0850c803fffffff6e28d0809081e0804c040800d0812540fffcb5c966cc224242802b8038002b8938042b8238086000fdca203c7fffffff9081e0804c040800d0812540fffcb5c966a060d2223c7fffffff60aa0c8600007eff6f2c20353800242b00084a856f00fe1e220a0681000000806000fd602200d28124c1b7ca6600fe2e6000fe5c93c9c2fc0007283538087c7f203538002f4400304c4610012801e0897984264147eb001828444a856f0001fa0681000000177a01e3ad2409e2822c05e28e44852206d282c2854a84670001200c813fffffff6e000444d28128412e0b7201efa92e01e28f44812f41002cd487c48126470c823fffffff6e0003ee22022e0ad2812f430034242f0030068700000080262f002c2f4d00302a45928ce0814c041800d28c28462c04d0880c8000010000653a2a122205e281240d0680ffff00002801d88cc8820c843fffffff6e52d884d28bc2830c813fffffff6e2ed281240922459284e0814c061800d28424c1b5c766b62a6f0030262f00342b8038002b8938042b8238086000fc6e223c7fffffff9284e081240922454c061800d28460cc283c7fffffff60a87c0c4c06380043f90000000042b1380023823808238238044cd73cfc4fef00404e750c8600007eff6f00feb22035380024044a856f00fca4220a0681000000806000fbe60c813fffffff6e0002ded281242f00302e0a068700000080d0880c8000010000651e28122204e2810680ffff00002409d286c2850c813fffffff6e1ad281224424c1be8a66d22b8038002b8938042b8238086000fbb6223c7fffffff224424c1be8a66b460e04a85660002d870ff7201e1a941ea0080201ae2802801e28c4481d084c0810c803fffffff6e1cd0802540fffcb1ca6700fd98201ae280d084c0810c803fffffff6fe4203c7fffffff2540fffcb1ca66e26000fd764a856700fd160681000000177c01e3ae48404240242f00302a09e282e285220848414241204591c22e064486e28f2f4000342f4600284a84670000da2c0b700147ea00802f4b0038eda8266f0034d7c1286f00302f6f002800302c00e28e44802f40002c2f46003c2c052a02240b266f003c2f4d003c2a472e042809226f00382f430038b282631220122a042c00e285e28628442800204691c5d481b282620001542002e288a0080800a1c0d085d080e2802600d68dc6af00300c833fffffff6e00014ad08bc0af002cd6830c803fffffff6e00014ed0809083e0804c070800d08324c0b5c9669ceb89202f003422442a6f003c240c262f00382f4c00302b8938042b823808d081424048402b8038006000fa3e28432c052a022409262f0028226f0030282f0034d88147ea0080b284631220122a022c00e285e28622422400204691c5d881b2846200008e2004e288a0080800a1c0d085d080e280d087c0830c803fffffff6e000082d08024c0b5cb66bceb89202f0034260c2f4900302242242f00302b8938042b823808d081424048402b8038006000f9b830017e7fc0fc00074c4700002200e0887381264047eb0018284128016000fb624a85670000c02008eb88d0b5380071c02b8038004cd73cfc4fef00404e752006d080e280d087c0830c803fffffff6f80203c7fffffff6000ff7a2006d080e2802600d68dc6af00300c833fffffff6f00febad08bc0af002c263c7fffffff0c803fffffff6f00feb6203c7fffffff6000feae2e0a223c7fffffff242f00300687000000806000fd1e223c7fffffff928ce081242f00302e0a2f4d00302f4300344c041800262f002c0687000000802a45d28c28462c046000fc10287c7fffffff6000fbba42802b8038006000ff482a0893c9484042404845424524012e092c02e287e28647ea0080204791c628002200d88520072e062c0922416000f94e7005b0af00046520202f0004720c41f9000000004c0108007201484142b0080842b00804218108004e75000100000000efe50000e0cd0000d2a80000c5670000b8fc0000ad580000a2700000983800008ea4000085ab00007d420000756000006dfe000067120000609600005a82000054d100004f7b00004a7a000045cb0000416700003d490000396e000035d10000326e00002f4200002c4900002980000026e300002471000022260000200000001dfd00001c1a00001a55000018ad0000171f000015ab0000144e00001307000011d5000010b500000fa800000eac00000dc000000ce200000c1300000b5000000a9a000009ef0000094f000008b90000082d000007a90000072e000006ba0000064e000005e80000058900000530000004dc0000048e0000044500000400",
    "relocs": [
     [
      2160,
      "bss",
      0
     ],
     [
      110,
      "bss",
      0
     ],
     [
      282,
      "code",
      2186
     ],
     [
      320,
      "bss",
      0
     ],
     [
      626,
      "bss",
      0
     ],
     [
      1202,
      "bss",
      0
     ]
    ],
    "symbols": {
     "crush_process": [
      "code",
      0
     ],
     "crush_reset": [
      "code",
      2144
     ]
    },
    "bss": 72
   },
   "cost": {
    "emulation": {
     "off": 36,
     "hard": 327,
     "soft": 952,
     "bits": 615,
     "glide": 994,
     "silent": 166,
     "dense": 1066,
     "first": 978,
     "pattern": "instructions per track and block, Crush's own code only, on the OS 1.13 in tools/emu/test_fltslot.py's filter_cost (mcengine.py's counter): all six tracks on it, the stock machines playing, a state held for 8 blocks after 8 of warm-up (off: Rate 0 and Bits 127; hard: Rate 48 with Bits 47; soft: Rate -48 with Bits 47; bits: Bits 47 alone; glide: Rate and Bits jumping every block, across the centre; silent: no note played, Rate and Bits on; dense: Rate -1 with Bits 95, a frame taken nearly every frame on the soft side, since 0.5), the maximum, and the block in which the tracks come to it from none (its reset and first block); the filter slot's own instructions apart"
    },
    "device": {
     "status": "not measured"
    }
   }
  },
  "ring": {
   "id": "ring",
   "name": "Ring: a ring modulator on every track, Freq on SWEEP, Mix on CONTOUR and the carrier's Wave on COLOR",
   "order": 74,
   "version": "0.3",
   "symbols": {
    "update": "ring_process",
    "render": "ring_reset"
   },
   "keep": [],
   "patch_points": [],
   "uses": [
    {
     "point": "track.filter",
     "id": 3,
     "process": "ring_process",
     "reset": "ring_reset",
     "name": "Ring",
     "short": "RNG",
     "params": [
      {
       "long": "Ring Freq",
       "short": "FREQ",
       "format": "int"
      },
      {
       "long": "Ring Mix",
       "short": "MIX",
       "format": "int"
      },
      {
       "long": "Ring Wave",
       "short": "WAVE",
       "format": "int",
       "start": 0
      }
     ]
    }
   ],
   "conflicts_declared": [],
   "claims": {},
   "bundle": {
    "code": "4fefffe4206f002848d71c0c246f00207405266f00242f6f002c0016b4886500014271530c8000007f006e00014c4a806d0001862400e08a718049f900000000362b000222742c0022342c049289342b0004e0893f4300144c0108003f42001a2400d4894aaf00166600010247f90000000022738c002002eb88d08927808c004a6f00146f0000dc20124a806618220a06810000008041ea00048098b28866fa4a80670000be716f00140c8000007f006e0001a271c0767fef884c43000072014841760fd0809280e7a923c00000000023c1000000004a6f001a6f00011a716f001a0c8000007f006f06203c00007f00c0c0263c00007f0049f90000000023c20000000023c90000000023ca0000000023cc000000004c430000c0fc0f004c43000006800000010023c000000000a93c000000a0a13c00000000203c00000100b0b900000000670000f4263c000000002f4300204cd71c0c4fef001c4ef9000000004cd71c0c4fef001c4e7593c947f9000000006000ff00203c00007f002400e08a718049f900000000362b000222742c0022342c049289342b0004e0893f4300144c0108003f42001a2400d4894aaf001666b86000feb642802400e08a718049f900000000362b000222742c0022342c049289342b0004e0893f4300144c0108003f42001a2400d4894aaf00166600ff7c6000fe78203c0000010049f90000000023c00000000023c20000000023c90000000023ca0000000023cc00000000a93c000000a0a13c00000000203c00000100b0b9000000006600ff10243c000000002f4200204cd71c0c4fef001c4ef900000000203c00007f00767f71c0ef884c43000072014841760fd0809280e7a923c00000000023c1000000004a6f001a6f00ff746000fe58202f00047205b280650a41f90000000042b00c004e7500004fefffe048d71cf8226f00244cd10df0761543e800802007e6a871720a004c0408000280ffff0000d08b2850a8400800a1c020c0de86b1c966dc4cd71cf84fef00204e754fefffe048d71cf8226f00244cd10df0761543e800802007e6a871720a004c050800e0800c8000007fff6f06203c00007fff0c80ffff80016c06203cffff80014c0408000280ffff0000d08b2850a8400800a1c020c0de86b1c966ba4cd71cf84fef00204e757fff7fff7ffe7ffd7ffc7ffa7ff87ff67ff47ff17fee7feb7fe77fe37fdf7fda7fd57fd07fca7fc47fbe7fb87fb17faa7fa27f9b7f937f8a7f827f797f707f667f5c7f527f487f3d7f327f267f1b7f0f7f027ef67ee97edc7ece7ec07eb27ea47e957e867e777e677e577e477e367e257e147e027df17ddf7dcc7db97da67d937d807d6c7d577d437d2e7d197d047cee7cd87cc17cab7c947c7d7c657c4d7c357c1d7c047beb7bd27bb87b9e7b847b697b4f7b337b187afc7ae07ac47aa87a8b7a6d7a507a327a1479f679d779b879997979795a7939791978f878d778b6789478737850782e780b77e877c577a1777d77597735771076eb76c676a0767a7654762d760775e075b8759175697541751874f074c6749d7474744a742073f573ca739f73747349731d72f172c47298726b723e721071e271b471867158712970fa70ca709b706b703a700a6fd96fa86f776f456f146ee16eaf6e7c6e4a6e166de36daf6d7b6d476d136cde6ca96c746c3e6c086bd26b9c6b656b2f6af86ac06a896a516a1969e069a8696f693668fc68c36889684f681467da679f6764672866ed66b16675663865fc65bf65826544650764c9648b644c640e63cf63906351631162d162916251621161d0618f614e610c60cb6089604760045fc25f7f5f3c5ef85eb55e715e2d5de95da55d605d1b5cd65c915c4b5c055bbf5b795b335aec5aa55a5e5a1759cf5988594058f858af5867581e57d5578b574256f856af5664561a55d05585553a54ef54a45458540c53c15374532852dc528f524251f551a8515a510c50be507050224fd44f854f364ee74e984e484df94da94d594d094cb84c684c174bc64b754b244ad24a804a2f49dd498a493848e54893484047ed479a474646f3469f464b45f745a3454e44f944a5445043fb43a5435042fa42a5424f41f941a2414c40f6409f40483ff13f9a3f433eeb3e933e3c3de43d8c3d333cdb3c833c2a3bd13b783b1f3ac63a6c3a1339b93960390638ab385137f7379c374236e7368c363135d6357b351f34c43468340c33b1335532f8329c324031e33187312a30cd307030132fb62f582efb2e9d2e402de22d842d262cc82c6a2c0b2bad2b4e2af02a912a3229d32974291528b5285627f72797273726d82678261825b8255824f82497243723d72376231522b5225421f32192213120d0206f200d1fac1f4a1ee91e871e261dc41d621d001c9e1c3c1bda1b781b161ab41a5119ef198c192a18c718651802179f173c16d91676161315b0154d14ea1487142413c0135d12fa1296123311cf116c110810a410410fdd0f790f150eb10e4e0dea0d860d220cbe0c5a0bf60b920b2d0ac90a650a01099d093808d40870080b07a7074306de067a061605b1054d04e80484041f03bb035602f2028d022901c4016000fb00970032ffceff69ff05fea0fe3cfdd7fd73fd0efcaafc45fbe1fb7cfb18fab3fa4ff9eaf986f922f8bdf859f7f5f790f72cf6c8f663f5fff59bf537f4d3f46ef40af3a6f342f2def27af216f1b2f14ff0ebf087f023efbfef5ceef8ee94ee31edcded6aed06eca3ec40ebdceb79eb16eab3ea50e9ede98ae927e8c4e861e7fee79be739e6d6e674e611e5afe54ce4eae488e426e3c4e362e300e29ee23ce1dae179e117e0b6e054dff3df91df30decfde6ede0dddacdd4bdcebdc8adc29dbc9db69db08daa8da48d9e8d988d928d8c9d869d809d7aad74bd6ebd68cd62dd5ced56fd510d4b2d453d3f5d396d338d2dad27cd21ed1c0d163d105d0a8d04acfedcf90cf33ced6ce79ce1dcdc0cd64cd08ccabcc4fcbf4cb98cb3ccae1ca85ca2ac9cfc974c919c8bec864c809c7afc755c6fac6a0c647c5edc594c53ac4e1c488c42fc3d6c37dc325c2cdc274c21cc1c4c16dc115c0bdc066c00fbfb8bf61bf0abeb4be5ebe07bdb1bd5bbd06bcb0bc5bbc05bbb0bb5bbb07bab2ba5dba09b9b5b961b90db8bab866b813b7c0b76db71bb6c8b676b623b5d1b580b52eb4dcb48bb43ab3e9b398b348b2f7b2a7b257b207b1b8b168b119b0cab07bb02cafdeaf90af42aef4aea6ae58ae0badbead71ad24acd8ac8cac3fabf4aba8ab5cab11aac6aa7baa30a9e6a99ca951a908a8bea875a82ba7e2a799a751a708a6c0a678a631a5e9a5a2a55ba514a4cda487a441a3fba3b5a36fa32aa2e5a2a0a25ba217a1d3a18fa14ba108a0c4a081a03e9ffc9fb99f779f359ef49eb29e719e309def9daf9d6f9d2f9cef9caf9c709c319bf29bb49b759b379af99abc9a7e9a419a0499c8998b994f991398d8989c9861982697ec97b19777973d970496ca96919658962095e795af95779540950894d1949b9464942e93f893c2938c9357932292ed92b992859251921d91ea91b691849151911f90ec90bb9089905890278ff68fc68f958f658f368f068ed78ea88e7a8e4c8e1e8df08dc28d958d688d3c8d0f8ce38cb78c8c8c618c368c0b8be08bb68b8c8b638b3a8b108ae88abf8a978a6f8a488a2089f989d389ac89868960893a891588f088cb88a78883885f883b881887f587d287b0878d876c874a8729870886e786c786a68687866786488629860a85ec85ce85b0859385758558853c8520850484e884cd84b18497847c84628448842e841583fc83e383cb83b3839b8383836c8355833f8328831282fc82e782d282bd82a982948280826d825a824782348221820f81fe81ec81db81ca81b981a981998189817a816b815c814e8140813281248117810a80fe80f180e580da80ce80c380b880ae80a4809a80908087807e8076806d8065805e8056804f80488042803c80368030802b80268021801d801980158012800f800c800a80088006800480038002800180018001800180028003800480068008800a800c800f801280158019801d80218026802b80308036803c80428048804f8056805e8065806d8076807e80878090809a80a480ae80b880c380ce80da80e580f180fe810a8117812481328140814e815c816b817a8189819981a981b981ca81db81ec81fe820f822182348247825a826d8280829482a982bd82d282e782fc83128328833f8355836c8383839b83b383cb83e383fc8415842e84488462847c849784b184cd84e885048520853c85588575859385b085ce85ec860a862986488667868786a686c786e787088729874a876c878d87b087d287f58818883b885f888388a788cb88f08915893a8960898689ac89d389f98a208a488a6f8a978abf8ae88b108b3a8b638b8c8bb68be08c0b8c368c618c8c8cb78ce38d0f8d3c8d688d958dc28df08e1e8e4c8e7a8ea88ed78f068f368f658f958fc68ff690279058908990bb90ec911f9151918491b691ea921d9251928592b992ed93229357938c93c293f8942e9464949b94d195089540957795af95e796209658969196ca9704973d977797b197ec98269861989c98d89913994f998b99c89a049a419a7e9abc9af99b379b759bb49bf29c319c709caf9cef9d2f9d6f9daf9def9e309e719eb29ef49f359f779fb99ffca03ea081a0c4a108a14ba18fa1d3a217a25ba2a0a2e5a32aa36fa3b5a3fba441a487a4cda514a55ba5a2a5e9a631a678a6c0a708a751a799a7e2a82ba875a8bea908a951a99ca9e6aa30aa7baac6ab11ab5caba8abf4ac3fac8cacd8ad24ad71adbeae0bae58aea6aef4af42af90afdeb02cb07bb0cab119b168b1b8b207b257b2a7b2f7b348b398b3e9b43ab48bb4dcb52eb580b5d1b623b676b6c8b71bb76db7c0b813b866b8bab90db961b9b5ba09ba5dbab2bb07bb5bbbb0bc05bc5bbcb0bd06bd5bbdb1be07be5ebeb4bf0abf61bfb8c00fc066c0bdc115c16dc1c4c21cc274c2cdc325c37dc3d6c42fc488c4e1c53ac594c5edc647c6a0c6fac755c7afc809c864c8bec919c974c9cfca2aca85cae1cb3ccb98cbf4cc4fccabcd08cd64cdc0ce1dce79ced6cf33cf90cfedd04ad0a8d105d163d1c0d21ed27cd2dad338d396d3f5d453d4b2d510d56fd5ced62dd68cd6ebd74bd7aad809d869d8c9d928d988d9e8da48daa8db08db69dbc9dc29dc8adcebdd4bddacde0dde6edecfdf30df91dff3e054e0b6e117e179e1dae23ce29ee300e362e3c4e426e488e4eae54ce5afe611e674e6d6e739e79be7fee861e8c4e927e98ae9edea50eab3eb16eb79ebdcec40eca3ed06ed6aedcdee31ee94eef8ef5cefbff023f087f0ebf14ff1b2f216f27af2def342f3a6f40af46ef4d3f537f59bf5fff663f6c8f72cf790f7f5f859f8bdf922f986f9eafa4ffab3fb18fb7cfbe1fc45fcaafd0efd73fdd7fe3cfea0ff05ff69ffce0032009700fb016001c40229028d02f2035603bb041f048404e8054d05b10616067a06de074307a7080b087008d40938099d0a010a650ac90b2d0b920bf60c5a0cbe0d220d860dea0e4e0eb10f150f790fdd104110a41108116c11cf1233129612fa135d13c01424148714ea154d15b01613167616d9173c179f1802186518c7192a198c19ef1a511ab41b161b781bda1c3c1c9e1d001d621dc41e261e871ee91f4a1fac200d206f20d02131219221f3225422b52315237623d72437249724f8255825b82618267826d82737279727f7285628b52915297429d32a322a912af02b4e2bad2c0b2c6a2cc82d262d842de22e402e9d2efb2f582fb63013307030cd312a318731e33240329c32f8335533b1340c346834c4351f357b35d63631368c36e73742379c37f7385138ab3906396039b93a133a6c3ac63b1f3b783bd13c2a3c833cdb3d333d8c3de43e3c3e933eeb3f433f9a3ff14048409f40f6414c41a241f9424f42a542fa435043a543fb445044a544f9454e45a345f7464b469f46f34746479a47ed4840489348e54938498a49dd4a2f4a804ad24b244b754bc64c174c684cb84d094d594da94df94e484e984ee74f364f854fd45022507050be510c515a51a851f55242528f52dc5328537453c1540c545854a454ef553a558555d0561a566456af56f85742578b57d5581e586758af58f85940598859cf5a175a5e5aa55aec5b335b795bbf5c055c4b5c915cd65d1b5d605da55de95e2d5e715eb55ef85f3c5f7f5fc260046047608960cb610c614e618f61d062116251629162d163116351639063cf640e644c648b64c965076544658265bf65fc6638667566b166ed67286764679f67da6814684f688968c368fc6936696f69a869e06a196a516a896ac06af86b2f6b656b9c6bd26c086c3e6c746ca96cde6d136d476d7b6daf6de36e166e4a6e7c6eaf6ee16f146f456f776fa86fd9700a703a706b709b70ca70fa71297158718671b471e27210723e726b729872c472f1731d73497374739f73ca73f57420744a7474749d74c674f0751875417569759175b875e07607762d7654767a76a076c676eb771077357759777d77a177c577e8780b782e78507873789478b678d778f879197939795a7979799979b879d779f67a147a327a507a6d7a8b7aa87ac47ae07afc7b187b337b4f7b697b847b9e7bb87bd27beb7c047c1d7c357c4d7c657c7d7c947cab7cc17cd87cee7d047d197d2e7d437d577d6c7d807d937da67db97dcc7ddf7df17e027e147e257e367e477e577e677e777e867e957ea47eb27ec07ece7edc7ee97ef67f027f0f7f1b7f267f327f3d7f487f527f5c7f667f707f797f827f8a7f937f9b7fa27faa7fb17fb87fbe7fc47fca7fd07fd57fda7fdf7fe37fe77feb7fee7ff17ff47ff67ff87ffa7ffc7ffd7ffe7fff7fff000b29a6000bd393000c879a000d4656000e1069000ee681000fc9530010b9a30011b83c0012c5f90013e3c0001512860016534c0017a72600190f34001a8cac001c20d3001dcd02001f92a7002173450023707800258bf20027c781002a250c002ca698002f4e4b00321e6900351958003841a6003b9a04003f254e0042e68b0046e0f0004b17e5004f8f0100544a1700594d31005e9c9600643cd2006a32b10070834c00773407007e4a9b0085cd15008dc1e100962fc9009f1e0300a8942e00b29a6200bd392d00c879a300d4656200e1069700ee680f00fc9536010b9a2b011b83c2012c5f93013e3c060151285d016534c3017a725a0190f34701a8cac301c20d2f01dcd01d01f92a6d02173456023707830258bf26027c780b02a250ba02ca698702f4e4b40321e68d0351958603841a5d03b9a03a03f254d9042e68ac046e0f0704b17e4b04f8f0170544a1730594d30d05e9c9680643cd1b06a32b0d070834ba0773407507e4a9b2085cd15708dc1e0d0962fc9609f1e02d0a8942e70b29a61a0bd392d00c879a350d46561a0e1069740ee680e90fc9536410b9a2af11b83c1a12c5f92c13e3c05a151285ce16534c3517a725a0190f346a1a8cac341c20d2e81dcd01d31f92a6c82173455e23707835258bf25927c780b52a250b9c2ca6986a2f4e4b3f321e68d4351958683841a5d13b9a03a63f254d9142e68abc46e0f069",
    "relocs": [
     [
      660,
      "bss",
      28
     ],
     [
      60,
      "code",
      4938
     ],
     [
      110,
      "bss",
      28
     ],
     [
      204,
      "bss",
      0
     ],
     [
      210,
      "bss",
      24
     ],
     [
      250,
      "code",
      842
     ],
     [
      256,
      "bss",
      8
     ],
     [
      262,
      "bss",
      12
     ],
     [
      268,
      "bss",
      16
     ],
     [
      274,
      "bss",
      20
     ],
     [
      298,
      "bss",
      4
     ],
     [
      322,
      "bss",
      4
     ],
     [
      332,
      "bss",
      0
     ],
     [
      350,
      "code",
      740
     ],
     [
      368,
      "bss",
      28
     ],
     [
      390,
      "code",
      4938
     ],
     [
      450,
      "code",
      4938
     ],
     [
      510,
      "code",
      842
     ],
     [
      516,
      "bss",
      4
     ],
     [
      522,
      "bss",
      8
     ],
     [
      528,
      "bss",
      12
     ],
     [
      534,
      "bss",
      16
     ],
     [
      540,
      "bss",
      20
     ],
     [
      564,
      "bss",
      4
     ],
     [
      574,
      "bss",
      0
     ],
     [
      592,
      "code",
      672
     ],
     [
      626,
      "bss",
      0
     ],
     [
      632,
      "bss",
      24
     ]
    ],
    "symbols": {
     "ring_process": [
      "code",
      0
     ],
     "ring_reset": [
      "code",
      648
     ]
    },
    "bss": 52
   },
   "cost": {
    "emulation": {
     "off": 42,
     "sine": 442,
     "shape": 635,
     "glide": 634,
     "silent": 143,
     "first": 449,
     "pattern": "instructions per track and block, Ring's own code only, on the OS 1.13 in tools/emu/test_fltslot.py's filter_cost (mcengine.py's counter): all six tracks on it, the stock machines playing, a state held for 8 blocks after 8 of warm-up (off: Mix 0; sine: Freq 64, Mix 95, Wave 0; shape: the same with Wave 127; glide: Freq, Mix and Wave jumping every block, Wave never 0; silent: no note played, Mix and Wave on), the maximum of the six tracks' sum over six (one of the six is silent in these scenes, notes/74 §4), and the block in which the tracks come to it from none (its reset and first block); the filter slot's own instructions apart"
    },
    "device": {
     "status": "not measured"
    }
   }
  },
  "reso": {
   "id": "reso",
   "name": "Reso: a tuned resonator on every track, Pitch on SWEEP, Amount on CONTOUR, Tone on COLOR, Decay on SHAPE",
   "order": 75,
   "version": "0.4",
   "symbols": {
    "update": "reso_process",
    "render": "reso_reset"
   },
   "keep": [],
   "patch_points": [],
   "uses": [
    {
     "point": "track.filter",
     "id": 4,
     "process": "reso_process",
     "reset": "reso_reset",
     "name": "Reso",
     "short": "RES",
     "params": [
      {
       "long": "Reso Pitch",
       "short": "PTCH",
       "format": "int",
       "start": 15360
      },
      {
       "long": "Reso Amount",
       "short": "AMT",
       "format": "int"
      },
      {
       "long": "Reso Tone",
       "short": "TONE",
       "format": "int"
      },
      {
       "long": "Reso Decay",
       "short": "DEC",
       "format": "int"
      }
     ]
    }
   ],
   "conflicts_declared": [],
   "claims": {},
   "bundle": {
    "code": "202f000c7205b280650002e2c0fc005c41f900000000d1c0226f0008736900026f0003384fefffd448d77cfc26480c8100007f006f06223c00007f00203c000102044c00180027410028203c7fffffff908127400024202b004c0c80000017206400028c4a2b005a671c3011b06b0054661430290004b06b0056660a30290006b06b0058670c2f092f0b4eb900000000508f202f0038c0fc5d0445f900000000d5c0262b0044242b0050203c0000171fd08390820c8000001720650604800000172043f20c0020036606203c0000172045f20c00282b00480c8400001720643a528294846f347021b4806f02240028497000260028002a002c002e002a402c4051826d0c48d460f949ec002051826cf45082670628c0538266fa206f00302c2b002c4ceb001e0030a33c0000000028592a597e08a10ca090680daceb69020010a1c2acebe8020014acebe8030018a1c3a8d9e901acebe800001cacebe8040020a184acebe8030024a1c5acebe8000028ac450800aa85080024c5a1c520c5a10da290680caceb69020010a1c2acebe8020014acebe8030018a1c3aad9e900acebe801001cacebe8040020a184acebe8030024a1c5acebe8010028ac45080024c5a1c520c5a10ca090680daceb69020010a1c2acebe8020014acebe8030018a1c3a8d9e901acebe800001cacebe8040020a184acebe8030024a1c5acebe8000028ac45080024c5a1c520c5a10da290680caceb69020010a1c2acebe8020014acebe8030018a1c3aad9e900acebe801001cacebe8040020a184acebe8030024a1c5acebe8010028ac45080024c5a1c520c553876600fee048eb001e0030a3c7202b004466344cea307eff8048ea307ea3004cea307effa048ea307ea3204cea307effc048ea307ea3404cea307effe048ea307ea360702060100680000000200c80000017206502700027400044202b00480c8000001720640a068000000020274000487010be80650642ab004c6016202b004c0c8000001720640a0680000000202740004c4cd77cfc4fef002c4e75206f003020186600fd6e80988098809880988098809880988098809880988098809880988098809880988098809880988098809880988098809880988098809880988098809880986600fd2c42ab0048203c000017202740004c42ab003042ab003442ab003842ab003c608a42a80048203c000017202140004c42a8003042a8003442a8003842a8003c4e757005b0af00046536202f0004725c4c010800223c000017202040d1fc00000000420042a800482141004c42a8003842a8003442a8003c42a800301140005a4e7500004fefffd848d73cfc206f002c226f003047f90000000071510c8000007f00630c203c00007f004a516a0270002200e08975807e17efa802807f800000245326321c00280398b21c044c024000e08c96842a43246b000428321c002a321c049a84a0050800a1c5d885246b00082a321c002c321c049c85a0060800a1c6da86716900040c8000007f00630e203c00007f004a6900046a0270002200e089246b000c24321c002c029cb21c0477804c036000e08e948667000146efa802807f800000246b001026321c002c321c049c83a0060800a1c6d686246b00142c321c0022321c049286a0010800a1c1dc81ac030800ac030800a1c0a6030800a6030800a1c12e3c7fffffff9e81aa040800aa040800a1cba8040800a8040800a1c1287c7fffffff99c1aa070800a8000900a1c1ae0b0800a00c0800a1cbac040800a6050800a1cca8010800a8010800a1c0280bb084643a4a80673c2a0004c553852c0404c65386eba8edac7e0feeac4c4400007e109e85de866b102a3c80000000eeadb085640aefa8600c4487eea86006203c7fffffff21400010283c7fffffff988021440014a60c0800a60c0800a1c0b081643a4a80673c2a0004c553852c0104c65386eba8eda97e0feea94c4100007e109e85de866b102a3c80000000eeadb085640aefa8600c4487eea86006203c7fffffff2840e28aaa420800a1c26012203c7fffffff2140001042a80014740099cc200d90820c80000018006406203c000018000480000008002200760ce6a921410050028000000fff2200ec897619e7a802807e00000047f900000000246b001c24321c0026321c049682a0030800a1c3d4832142002c716900060c8000007f00630e203c00007f004a6900066a0270002200e0897180246b001824321c00260296b21c04e08b4c0030009483200ded88a4000800a1c220027218e2a8721eb081622a220248417381246b002026321c00280398b21c04720fe3aa02827fff8000a4040800a1c49684e0a360027600a6030800a1c0223c7fffffff92806f3a200104c0538074fec082e1a924017817e8aae18902817fffff00246b002428322c002a322c049a84a2050800a1c5d885e288e0a421440018600442a80018a8430800a1c0223c7ff7ffff9283b0816f08203c7ff7ffff6002d08321400020203c7fbfffff2140001c3151005431690004005631690006005870011140005a4cd73cfc4fef00284e750000000000000000000000000000000000000000000000000000000000000000000000000000000000000000080000000b504f330ddb3d741000000011e3779c13988e14152a7faa16a09e6618000000194c583b1a8872941bb67ae81cd82b441deeea111efbdeb12000000020fc1ecd21f0ed9a22df066923c6ef3724a91d722585f8b3265ddceb27311c282800000028cacabe2991b85d2a54ff542b14d1492bd15ba42c8ac80b2d413ccd2df4dd432ea5ca1b2f5421a33000000030a97f673150b84a31f5c1833298b0763339993333d88e943475a2543510e52835aa66d33642363936d86170376cf5d13800000038918c003921a53a39b056893a3daa413ac9aa3c3b545fdf3bddd4233c660f993ced1a733d72fc8b3df7bd633e7b642f3efdf7d73f7f7efd40000000407f80fe40fe07d9417b9a3c41f83d9b4273f73642eecc1f4368c13643e1db33445a1ea344d18fe94548334545be0cd24633208746a7723e471b05ad478dde6e4800000048716dc348e22b0049523ae449c1a0864a305ee54a9e78e94b0bf1654b78cb1a4be508b14c50acc34cbbb9d64d26325f4d9018c14df96f504e6238504eca75f64f322a674f9957bc500000005066253150cbc93f5130ee105195957c51f9c153525d735652c0ad3e532370b95385bf6b53e79aef544904d654a9fea7550a89e3556aa80155ca5a6e5629a293568881cd56e6f97557450adb57a2b74958000000585ce63d58b96b34591590165971560a59ccbe345a27c9b25a82799a5adcceff5b36caef5b906e705be9ba865c42b02d5c9b50615cf39c145d4b94375da339b55dfa8d765e51905c5ea843465efea7105f54bc915faa849c6000000060552f8a60aa140260feae2d6152fece61a706a161fac664624e3ece62a1709462f45c68634702fa639964f663eb8305643d5dd0648ef5f964e04c22653160eb658234f165d2c8cd66231d186673326666c3094c6712a25a6761fe2067b11d2968000000684ea72e689d133a68eb44a869393bfb6986f9b469d47e516a21ca506a6ede2c6abbba5e6b085f606b54cda66ba105a56bed07d16c38d49a6c846c726ccfcfc56d1aff016d65fa926db0c2e16dfb58566e45bb5a6e8fec526ed9eba16f23b9ad6f6d56d56fb6c37c7000000070490cc07091ea1870da986571231800716b694571b38c8a71fb822872434a75728ae5c572d2546d731996c17360ad1273a797b173ee56ee7434eb1a747b548274c193737507a83a754d93237593547875d8ec83761e5b8d7663a1df76a8bfbf76edb574773283437777297277bba84678000000784430e478883b3478cc1f31790fdd1c795375347996e7b879da34e67a1d5cfe7a60603a7aa33ed97ae5f9157b288f2b7b6b01537bad4fc97bef7ac57c3182817c7367347cb529167cf6c85d7d3845417d799ff77dbad8b57dfbefae7e3ce5187e7db9267ebe6c0c7efefdfb7f3f6f267f7fbfc07fbfeff87fffffff7fffffff7fa765ad7f4f08ae7ef6e8da7e9f06067e4760097deff6b67d98c9e67d41d96e7ceb25237c94acde7c3e70737be86fba7b92aa887b3d20b67ae7d21a7a92be8b7a3de5df79e947ef7994e4927940bb9e78ecccec7899185478459dac77f25cce779f5590774c87cc76f9f35976a7980f765575c876038c5b75b1dba275606374750f23ab74be1c20746d4cac741cb52873cc556d737c2d55732c3cba72dc8374728d015d723db65071eea226719fc4b971511de47102ad8070b4736870666f767018a1856fcb096f6f7da7106f307a416ee382de6e96c0c36e4a33c96dfddbcc6db1b8a86d65ca386d1a10576cce8ae16c8339b26c381ca66bed33996ba27e656b57fce96b0daeff6ac394856a79ad566a2ff94f69e6784d699d2a2c69540ec9690b260168c26fb16879ebb6683199ed67e97a3467a18c686759d0656712460b66caed356683c5c3663ccf9265f60a7f65af766a6569132f6522e0ad64dcdec364970d4f64516c2e640bfb4163c6ba646381a978633cc85b62f816eb62b39509626f4292622b1f6661e72b6561a3666d615fd05e611c691960d9307b6096266560534ab760109d515fce1e125f8bccdb5f49a98c5f07b4055ec5ec265e8451d05e42e4e35e01a53f5dc092c75d7fad595d3ef4d75cfe69235cbe0a1c5c7dd7a45c3dd19c5bfdf7e55bbe4a615b7ec8f25b3f73775b0049d45ac14bea5a82799a5a43d2c65a05575159c7071c5988e209594ae7fb590d18d358cf74745891fac15854ab9b581786e657da8c83579dbc575761164257249a2956e847ef56ac1f75567020a056344b5255f89f7055bd1cdb5581c37855469329550b8bd454d0ad5a5495f7a1545b6a8b542105fd53e6c9da53acb6075372ca68533906e052ff6b5552c5f7aa528cabc352538786521a8ad751e1b59a51a907b45170810b5138218250ffe8fe50c7d765508fec9c5058288850208b0e4fe914134fb1c37c4f7a99304f4395144f0cb70c4ed5ff004e9f6cd44e69006e4e32b9b44dfc988c4dc69cdd4d90c68b4d5b157e4d25899c4cf022ca4cbae0ef4c85c3f14c50cbb84c1bf8294be7492b4bb2bea54b7e587e4b4a169c4b15f8e64ae1ff434aae299b4a7a77d44a46e9d64a137f8849e038d049ad1598497a15c44947393f49147fee48e1e9ba48af768a487d2646484af8d64818ee2247e7061147b5408c47839d7b47521cc64720be5546ef821046be67e0468d6fae465c9961462be4e245fb521a45cae0f2459a9152456a6323453a564d450a6abb44daa05444aaf702447b6ead444c0740441cc0a343ed9ac043be957f438fb0cb4360ec8d433248ae4303c51842d561b442a71e6c4278fb2b424af7da421d146241ef50ae41c1aca7419428394166c34c41397dcc410c57a240df50b840b268fa4085a0514058f6a8402c6be9400000002aaaaaab28e83f57272f0539257eb50323d70a3d2237c32b20a0a0a11f1165e71d89d89e1c09c09c1a90e7d9191f1a5117b425ed164fda6c14f2094f139a85c41249249210fdbc090fb823ee0e78356d0d3dcb090c08c08c0ad8f2fc09ae408a088888890767ab5f064b8a7e053408530421084203126e98020820820102040800000000ff01fc08fe07e07efd119679fc1f07c2fb301eccfa44c6b0f95ceb24f8787878f7975b90f6b981dbf5ded953f5075075f432d63ef3615a24f292cc15f1c71c72f0fe3c07f0381c0eef74ae26eeb3e453edf5b0f7ed3a06d4ec80d902ebca1af3eb15c06bea63bd82e9b4069be9069069e85b4fe6e7b23a54e70b453ce6666666550a968550fae9b14d1ce36f496e24bf45ec6b9b4295919a3f678a9b3c606384397e411436bf5eb834220d7d31a4b3032f45c8842d03d9e22add84c628d177c426de718e2503402d233ec047218fdc6d1ff58c6e1e6ed4b81cfac5bc1b987b5c1a471c5f1905d9ec17d3ef0a16b0a028159b3aac1493148013978bb112a8060511c3f0a210eabfb0101bee050f56fcd20e9b73570de8de9a0d3ed11c0c9ce2990c02afca0b6fda230ae4079d0a5ee27d09e0192209675dd008f4667f0886ecb4081ead4f07bb6865075ce1190702dd7606ad264c065b870d060dcdad05c3ca84057d5033053a338204fa4b4c04bd706304837d76044c4efd0417c32403e5b9b303b613fc0388b4c8035d804703345bf9030d2ea702e7e04b02c45a0402a2860c02824fa50263a30e02466d79022a9cfd0210208e01f6e7ec01dee3a201c804f601b23de3019d810e0189c1c00176f3de01650be00153fecc0143c22d01344c0f012592f701178dde010a342c00fd7db100f162a200e5db9200dae17100d06d8300c6795f00bcfeec00b3f85900ab601f00a330f7009b65de0093fa0c008ce8f400862e41007fc5d30079abbd0073dc3f006e53cb00690efc00640a97005f4388005ab6e2005661da005241c8004e5426004a968a004706a90043a25500406778003d5418003a665200379c5b0034f47c00326d1500300498002db98d002b8a8b0029763a7f0a7cd47f1984217f27a9807f34f92d7f417ed77f4d45a77f58583f7f62c0c17f6c88cd7f75b98d7f7e5bb07f8677757f8e14ac7f953abd7f9bf0a87fa23d0d7fa8262e7fadb1f67fb2e5fb7fb7c7827fbc5b837fc0a6ad7fc4ad6c7fc873e97fcbfe0f7fcf4f8d7fd26bdd7fd556427fd811cf7fdaa1677fdd07c17fdf476b7fe162ca7fe35c1f7fe535887fe6f1007fe890677fea157b7feb81e37fecd7297fee16c07fef42037ff05a3a7ff160967ff256367ff33c287ff413687ff4dce47ff599797ff649f87ff6ef247ff789b47ff81a547ff8a1a47ff9203c7ff996a97ffa056f7ffa6d0b7ffacdf07ffb288c7ffb7d457ffbcc7b7ffc16887ffc5bbf7ffc9c707ffcd8e47ffd11607ffd46267ffd77717ffda57b7ffdd0787ffdf89c7ffe1e147ffe410d7ffe61af7ffe80217ffe9c867ffeb7017ffecfb17ffee6b47ffefc257fff101e7fff22b77fff34087fff44257fff53227fff61137fff6e087fff7a127fff85407fff8fa17fff99417fffa22f7fffaa747fffb21d7fffb9347fffbfc27fffc5d07fffcb677fffd08f7fffd54e7fffd9ad7fffddb27fffe1617fffe4c27fffe7da7fffeaad7fffed407fffef987ffff1b87ffff3a57ffff5627ffff6f17ffff8577ffff9977ffffab27ffffbab7ffffc867ffffd437ffffde67ffffe6f7ffffee27fffff3f7fffff887fffffbe7fffffe37ffffff97fffffff7fffffff0fa3b3810f27ac780eaf234d0e3a06060dc8425b0d59c5c70cee7d9c0c86570f0c213f4e0bbf23850b5ff0f20b0394ea0aa9fce80a53169109fecfbc09ad167d095dd9270911065108c68cde087e5bfa0838632607f4923107b2d942077328d6073571be06f9a52806bfb497068791e706512f50061c7f5d05e974f605b8035605881e0f0559b90b052cc8830501410704d7177504ae40fe0486b31e046063a0043b489a0417586c03f489bd03d2d37a03b22cd703928d480373ec860356428803398781031db3e40302c05d02e8a5d302cf5d6202b6e05f029f285202882ef80271ee3d025c604002477f4e023345e1021faea0020cb45d01fa521401e882e801d7422401c68b3901b659be01a6a96c019776200188bbd7017a76b1016ca2eb015f3ce2015241110145ac0e01397a8e012da95c0122356201171ba2010c59340101eb4a00f7cf2d00ee023b00e481ea00db4bc200d25d6000c9b47600c14ec700b92a2a00b1448800a99bd800a22e25009af98a0093fc2f008d344d0086a02d00803e23007a0c92007409ec006e34ad00688b5f00630c98005db6fa00588930005381f4004ea0070049e235004547550040ce47003c75f400383d4d0034234f003026fc002c475f0028838c0024da9d00214bb6001dd5fe001a78a8001732e9001403fe0010eb2d000de7be000af90100081e4c000556f90002a269000000000000000009fb385b09abaf29095e6c0b0913627808ca85c80883c941083f202207fc7dac07bbd529077d19f207403f7b0705395306cbfb2b069478dd065ea66c062a780b05f7e21e05c6d93c059752340569420a053c9dfe05115b8904e7705e04bed26d049777e104715723044c66d504289dd60405f34103e45e6d03c3d6e703a4547a0385cf2903683f2c034b9cf6032fe12f031504b202fb009102e1ce1002c966a402b1c3f4029adfd70284b451026f3b95025a700302464c240232caae021fe67d020d9a9901fbe22c01eab88a01da192a01c9ffa701ba67be01ab4d51019cac5f018e81090180c78e01737c4c01669bbe015a227a014e0d34014258b7013701ec012c05d2012161810117122a010d15130103679a00fa072f00f0f15b00e823b800df9bf600d757d600cf552c00c791de00c00be300b8c14200b1b01200aad67c00a432b6009dc305009785bb0091793b008b9bf20085ec5c00806900007b10720075e1510070da49006bfa0e00673f610062a90d005e35e70059e4cc0055b4a30051a45e004db2f50049df6a004628c800428e1f003f0e89003ba92600385d20003529a500320de9002f092b002c1aac002941b500267d930023cd9d0021312a001ea79b001c30530019cabc001776430015325d0012fe800010da27000ec4d4000cbe09000ac5500008da340006fc4500052b160003663e0001ad5800000000000000007ffffecd7ffffea77ffffe7d7ffffe4d7ffffe187ffffddc7ffffd997ffffd4e7ffffcf97ffffc9a7ffffc307ffffbb87ffffb327ffffa9c7ffff9f37ffff9357ffff8607ffff7717ffff6647ffff5377ffff3e57ffff26a7ffff0c07fffeee17fffecc97fffea6e7fffe7ca7fffe4d37fffe17f7fffddc37fffd9927fffd4dd7fffcf947fffc9a67fffc2fe7fffbb867fffb3237fffa9b97fff9f297fff934d7fff85fd7fff770c7fff66467fff53737fff3e517fff26997fff0bfa7ffeee187ffecc8d7ffea6e67ffe7ca37ffe4d337ffe17f47ffddc307ffd991a7ffd4dcd7ffcf9487ffc9a697ffc2feb7ffbb8647ffb32397ffa9ba07ff9f2967ff934d97ff85fe07ff770d37ff664817ff537537ff3e5447ff269d17ff0bfe77feee1d87fecc93f7fea6ef47fe7caeb7fe4d41d7fe1806a7fddc4727fd993747fd4df1d7fcf975c7fc9aa267fc303407fbb8bf27fb32ac17fa9c3137f9f34d27f935bfd7f8610307f7724197f6664e37f5399867f3e820d7f26d6ba7f0c471d7eee79007ecd07417ea780807e7d65ac7e4e28607e1929127dddb50e7d9b04357d50367e7cfc512f7c9e3bc67c34bc977bbe75057b39dd617aa5405c79feb60879441e6d78731b9b77890b477682ffe8755db96674159d5572a6aed6710c863d6f4248936d429f3f6b07b00d688b160565c5db8d62b0768e5f42c7635b741bcb573b371f528e61a1001188c9001293b30013ae7d0014da1800161783001767cf0018cc19001a4594001bd580001d7d34001f3e1a002119b2002311910025276700275cfa0029b430002c2f06002ecf9d0031983200348b260037aaff003afa67003e7c330042336200462320004a4eca004eb9f10053685b00585e07005d9f330063305c00691643006f55f30075f4c1007cf857008466b2008c462a00949d7b009d73c400a6d09200b0bbe400bb3e3400c6607d00d22c4000deab9200ebe91f00f9f0370108ccd501188bac01293a2d013ae699014da0080161767701767ad8018cbf1d01a4564901bd548101d7cf1c01f3dcb50211953d0231121402526e180275c5c1029b373602c2e26702ece92b03196f5603489add037a93f403af852e03e79ba2042307110461fa0b04a4aa1b04eb4ff3053627990585709505d96e2d063267900690a81606f47f78075e420f07ce49130844f2e108c2a3400947c3a909d4c3940a6a18c60b083f9c0bafbb660c6116b00d1ce39c0de3bc310eb642b30f9521ed10810d81117ac22d1283060e139aa8ce14c283d115fb7a4a1746793718a477451a1674951b9d7a4a1d3a99f01eeeec9920bb91b422a1ad7a24a266fa26bee58b28f84dad2b4fbd192dc645f1305ce8e333148dfa35edfc0738e9ce393c0867b03f49e4b842ae093146342bd449db1dce4da10e2851836885557eae8b598e4b7c5dac616561d18f78016eefc6015a57900146e74301348e4101233ce00112e4510103769f00f4e69c00e727d400da2e8c00cdefac00c260be00b777e300ad2bc800a373a1009a472100919e70008972290081bb50007a734e007393ea006d17460066f7d60061305f005bbbf2005695e40051b9d1004d23900048cf380044b9140040dda8003d39a70039c9f500368ba300337beb00309830002dddf9002b4af20028dce8002691c80024679c00225c8a00206ed4001e9cd3001ce4fb001b45d10019bdf500184c180016eefc0015a57900146e74001348e4001233ce00112e450010376a000f4e6a000e727d000da2e9000cdefb000c260c000b777e000ad2bd000a373a0009a472000919e70008972300081bb50007a7350007393f0006d17400066f7d000613060005bbbf0005695e00051b9d0004d23900048cf300044b9100040dda0003d39a00039c9f000368ba000337bf000309830002dde00002b4af00028dcf0002691d0002467a000225c9000206ed0001e9cd0001ce500001b45d00019bdf000184c100016ef000015a58000146e70001348e0001233d000112e4000103770000f4e70000e7280000da2f0000cdf00000c2610000b7780000ad2c0000a37400009a470000919e00008972000081bb00007a730000739400006d17000066f80000613000005bbc00005696000051ba00004d24000048cf000044b9000040de00003d3a000039ca",
    "relocs": [
     [
      918,
      "bss",
      142872
     ],
     [
      1840,
      "code",
      7292
     ],
     [
      1844,
      "code",
      6776
     ],
     [
      1848,
      "code",
      6260
     ],
     [
      1852,
      "code",
      5744
     ],
     [
      1856,
      "code",
      5228
     ],
     [
      1860,
      "code",
      4712
     ],
     [
      1864,
      "code",
      4196
     ],
     [
      1868,
      "code",
      3936
     ],
     [
      1872,
      "code",
      2908
     ],
     [
      1876,
      "code",
      1880
     ],
     [
      18,
      "bss",
      142872
     ],
     [
      140,
      "code",
      956
     ],
     [
      156,
      "bss",
      0
     ],
     [
      974,
      "code",
      1840
     ],
     [
      1538,
      "code",
      1840
     ]
    ],
    "symbols": {
     "reso_process": [
      "code",
      0
     ],
     "reso_reset": [
      "code",
      890
     ]
    },
    "bss": 143424
   },
   "cost": {
    "emulation": {
     "off": 18,
     "mid": 590,
     "low": 612,
     "high": 583,
     "glide": 830,
     "silent": 70,
     "first": 855,
     "pattern": "instructions per track and block, Reso's own code only, on the OS 1.13 in tools/emu/test_fltslot.py's filter_cost (mcengine.py's counter): all six tracks on it, the stock machines playing, a state held for 8 blocks after 8 of warm-up (off: Amount 0; mid: C4, Amount 127, Tone and Decay 64; low: C1 with Tone 32 and Decay 127, the line still being cleared; high: C7, the same; glide: every word jumping every block, the coefficients worked out each time; silent: no note played), the maximum, and the block in which the tracks come to it from none (its reset and first block); the filter slot's own instructions apart"
    },
    "device": {
     "status": "not measured"
    }
   }
  },
  "eq": {
   "id": "eq",
   "name": "EQ: a three-band equalizer on every track, a sweepable Mid on SWEEP and CONTOUR, Low and High shelves on COLOR and SHAPE",
   "order": 76,
   "version": "0.6",
   "symbols": {
    "update": "eq_process",
    "render": "eq_reset"
   },
   "keep": [],
   "patch_points": [],
   "uses": [
    {
     "point": "track.filter",
     "id": 5,
     "process": "eq_process",
     "reset": "eq_reset",
     "name": "EQ",
     "short": "EQ",
     "params": [
      {
       "long": "EQ_mid Freq",
       "short": "MIDF",
       "format": "int"
      },
      {
       "long": "EQ_mid Gain",
       "short": "MIDG",
       "format": "cutoff",
       "start": 16384
      },
      {
       "long": "EQ_low Gain",
       "short": "LOWG",
       "format": "cutoff"
      },
      {
       "long": "EQ_high Gain",
       "short": "HIGG",
       "format": "cutoff"
      }
     ]
    }
   ],
   "conflicts_declared": [],
   "claims": {},
   "bundle": {
    "code": "202f000c7205b2806500072eef8841f900000000d1c0226f00087000322900040c41400067027001322900020c41400067025480322900060c414000670258804a80670006f64fefffd448d77cfc2a482c492e00286f00304a2d007c661e201422002400260048d5000f48ed000f001048ed000f002070011b40007c223c00004000243c000080002015d081b082640000d4202d0028d081b082640000c8202d0004d081b082640000bc202d0008d081b082640000b0202d000cd081b082640000a4202d0018d081b08264000098202d001cd081b0826400008c202d002cd081b08264000080204c20186600007880988098809880988098809880988098809880988098809880988098809880988098809880988098809880988098809880988098809880988098809880986600003672002a802b4100042b4000082b41000c2b4000102b4100142b4000182b41001c2b4000202b4100242b4000282b41002c600005ce08070000673e716e0004b0ad006c67342b40006c0c8000007f00630e4a806b08203c00007f006002700020790000000043ed0030223c4000000095ca97cb4eb900000000080700016750716e00027356b0ad00746606b2ad0078673e2b4000742b4100780c8000007f00630e4a806b08203c00007f00600270000c8100007f00630e4a816b08223c00007f006002720043ed00444eb900000000080700026754716e0006b0ad0070674a2b4000700c8000007f00630e4a806b08203c00007f0060027000720297cbb0b9000000006c067201367c00011b41007d20790000000043ed0058223c20000000347c00014eb9000000007007be806600042c7001b02d007d660001fe4cd5000f4ced003000184ced00c00028204c4de8008043ed0030246900042651a13c00000000a33c00000000a53c00000000a290180ba8e9180a0008a6e9080c000ca8e9290b0010a6e9390c0014a869380b0018a1c3d683690004b8a669380c001ca869280b0020a669490c0024a869590b0028a6e9581c002ca3c5da85690004aaa8e9581b0030a6e9481c0034a8e9691b0038a6d1791ca5c7de87690004a420c7a090080ba8e9080a0008a6e9180c000ca8e9390b0010a6e9290c0014a869280b0018a1c2d48269000490a669280c001ca869380b0020a669590c0024a869490b0028a6e9481c002ca3c4d88469000482a8e9481b0030a6e9581c0034a8e9791b0038a6d1691ca5c6dc866900047c20c6a290180ba8e9180a0008a6e9080c000ca8e9290b0010a6e9390c0014a869380b0018a1c3d68369000468a669380c001ca869280b0020a669490c0024a869590b0028a6e9581c002ca3c5da856900045aa8e9581b0030a6e9481c0034a8e9691b0038a6d1791ca5c7de876900045420c7a090080ba8e9080a0008a6e9180c000ca8e9390b0010a6e9290c0014a869280b0018a1c2d48269000440a669280c001ca869380b0020a669590c0024a869490b0028a6e9481c002ca3c4d88469000432a8e9481b0030a6e9581c0034a8e9791b0038a6d1691ca5c6dc866900042c20c6b1ce6600fe3c600002124cd5000f4ced003000184ced00c00028204c4de8008043ed0030246900042651a13c00000000a33c00000000a53c00000000a290180ba8e9180a0008a6e9080c000ca8e9290b0010a6e9390c0014a869380b0018a1c3d683690003dca669380c001ca869280b0020a669490c0024a869590b0028a6e9581c002ca3c5da85690003cea8e9581b0030a6e9481c0034a8e9691b0038a6d1791ca5c7de87690003c8de87690003da20c7a090080ba8e9080a0008a6e9180c000ca8e9390b0010a6e9290c0014a869280b0018a1c2d482690003c6a669280c001ca869380b0020a669590c0024a869490b0028a6e9481c002ca3c4d884690003b8a8e9481b0030a6e9581c0034a8e9791b0038a6d1691ca5c6dc86690003b2dc86690003c420c6a290180ba8e9180a0008a6e9080c000ca8e9290b0010a6e9390c0014a869380b0018a1c3d683690003b0a669380c001ca869280b0020a669490c0024a869590b0028a6e9581c002ca3c5da85690003a2a8e9581b0030a6e9481c0034a8e9691b0038a6d1791ca5c7de876900039cde87690003ae20c7a090080ba8e9080a0008a6e9180c000ca8e9390b0010a6e9290c0014a869280b0018a1c2d4826900039aa669280c001ca869380b0020a669590c0024a869490b0028a6e9481c002ca3c4d8846900038ca8e9481b0030a6e9581c0034a8e9791b0038a6d1691ca5c6dc8669000386dc866900039820c6b1ce6600fe2448d5000f48ed003c001048ed00f00020600000a8080700006718487800012f0c4855486d00304eb9000000004fef00106016202c007c222c00782a802b4100042b4000082b41000c08070001671a487800012f0c486d0010486d00444eb9000000004fef00106018202c007c222c00782b4000102b4100142b4000182b41001c08070002671c71ad007d2f002f0c486d0020486d00584eb9000000004fef00106018202c007c222c00782b4000202b4100242b4000282b41002c4cd77cfc4fef002c4e75226f00042029007c22290078208021410004214000082141000c2140001021410014214000182141001c2140002021410024214000282141002c70011140007c4e756b00000c263c800000006000fb3e263c7fffffff6000fb346b00000c2a3c800000006000fb4c2a3c7fffffff6000fb426b00000c2e3c800000006000fb522e3c7fffffff6000fb486b00000c243c800000006000fb66243c7fffffff6000fb5c6b00000c283c800000006000fb74283c7fffffff6000fb6a6b00000c2c3c800000006000fb7a2c3c7fffffff6000fb706b00000c263c800000006000fb8e263c7fffffff6000fb846b00000c2a3c800000006000fb9c2a3c7fffffff6000fb926b00000c2e3c800000006000fba22e3c7fffffff6000fb986b00000c243c800000006000fbb6243c7fffffff6000fbac6b00000c283c800000006000fbc4283c7fffffff6000fbba6b00000c2c3c800000006000fbca2c3c7fffffff6000fbc06b00000c263c800000006000fc1a263c7fffffff6000fc106b00000c2a3c800000006000fc282a3c7fffffff6000fc1e6b00000c2e3c800000006000fc2e2e3c7fffffff6000fc246b00000c2e3c800000006000fc1c2e3c7fffffff6000fc126b00000c243c800000006000fc30243c7fffffff6000fc266b00000c283c800000006000fc3e283c7fffffff6000fc346b00000c2c3c800000006000fc442c3c7fffffff6000fc3a6b00000c2c3c800000006000fc322c3c7fffffff6000fc286b00000c263c800000006000fc46263c7fffffff6000fc3c6b00000c2a3c800000006000fc542a3c7fffffff6000fc4a6b00000c2e3c800000006000fc5a2e3c7fffffff6000fc506b00000c2e3c800000006000fc482e3c7fffffff6000fc3e6b00000c243c800000006000fc5c243c7fffffff6000fc526b00000c283c800000006000fc6a283c7fffffff6000fc606b00000c2c3c800000006000fc702c3c7fffffff6000fc666b00000c2c3c800000006000fc5e2c3c7fffffff6000fc54202f00047205b2806524ef8842012040d1fc00000000700148401141007c2140006c2140007021400074214000784e754fefffe048d77c1c226f00244cd17c00226f00284cd1001e206f002ca13c00000000202f00305380660000867008a490280aa40b0800a20c0800a60d0900a80e0900a1c4d8846900011220c4a290180aa20b0800a40c0800a80d0900a60e0900a1c3d6836900010c20c3a490280aa40b0800a20c0800a60d0900a80e0900a1c4d8846900010620c4a290180aa20b0800a40c0800a80d0900a60e0900a1c3d6836900010020c353806600ff846000009a7008a490280aa40b0800a20c0800a60d0900a80e0900a1c4d884690000eed8846900010020c4a290180aa20b0800a40c0800a80d0900a60e0900a1c3d683690000fad6836900010c20c3a490280aa40b0800a20c0800a60d0900a80e0900a1c4d88469000106d8846900011820c4a290180aa20b0800a40c0800a80d0900a60e0900a1c3d68369000112d6836900012420c353806600ff6c226f002848d1001e4cd77c1c4fef00204e756b00000c283c800000006000fee4283c7fffffff6000feda6b00000c263c800000006000feea263c7fffffff6000fee06b00000c283c800000006000fef0283c7fffffff6000fee66b00000c263c800000006000fef6263c7fffffff6000feec6b00000c283c800000006000ff08283c7fffffff6000fefe6b00000c283c800000006000fef6283c7fffffff6000feec6b00000c263c800000006000fefc263c7fffffff6000fef26b00000c263c800000006000feea263c7fffffff6000fee06b00000c283c800000006000fef0283c7fffffff6000fee66b00000c283c800000006000fede283c7fffffff6000fed46b00000c263c800000006000fee4263c7fffffff6000feda6b00000c263c800000006000fed2263c7fffffff6000fec800002400e88a0282000007f0d1c27180242800109490e0824c002800d49092822628001496a80004e0834c003800d6a800042828001898a80008e0844c004800d8a800082a28001c9aa8000ce0854c005800daa8000cd2852c039c84200a67024486d286200b670ad281d482d683d884da8548d1003e4e752400760be6a2c4fc018c2601780ae8a3c6fc000cd483207900000000d1c2e6807180e48173812428000c9490e0824c012800d4902c2801989ca8018ce0864c016800dca8018c9c82e0864c006800d4862628001096a80004e0834c013800d6a800042c28019c9ca80190e0864c016800dca801909c83e0864c006800d6862828001498a80008e0844c014800d8a800082c2801a09ca80194e0864c016800dca801949c84e0864c006800d8862a049a82068540000000228523420004234300082343000c234400104e750000711c0000000000000000000000003ec7c325834ce60c3cbe0b5c3ea7a80283a50d923c684adf3e845b1b840643223c0a02363e5d910384716ced3ba267ee3e32f8a384e7864f3b30a3703e043b178569a1633ab3cca93dd0fb9b85f8e8aa3a2aebd73d98d7968696a0ae3994f99e3d5b66ba874429ac38f0df693d183b5188030136383d78313ccee2b388d4c3cb377991bc3c7ee5f889bb2e4d36a3ee713c27cae58ab81f5d35bb47da3bc9152c8bcd987e34be51f53b6248008cfdbf0233abbf6e3af2e8138e4adc9e328246f13a7a7e038fb75fa93140a99e39f899409145dae92fe5bad4396cd38092f904e92e70695e38d6d4b994d3b6cd2cdfca17383657b296d8eaa42b332418378b2f1b990bb93e2969fe6336d54b3b9b6f579627842ef23614c00a9e07140b2581eb203549cbbda0d653902363d90f3474dd94a3e08f4d212b21e233969cd9a72953301ed9846e32afefedaab43e2e1c7167ff31c2033cae85053d19f5eeff30ce5026b29f7a56176b09582fd6a3d4b707994014d586c62edd265cbbc19c6a123b29d42de462aec0d21cdd0fa2bd1c3ef322e283098c253d016b2c3ed76d06835af7273cb2693e3eb8f1cd83b4cf403c5b80c93e976f088417ee233bfbf5163e729d60848542463b92fac33e4a303384fdd0a13b1fb74e3e1dd5718582b6773aa140bf3ded359686152b3d3a169d8d3db7f3b286b6828e397ec4c03d7dad9887682e2b38d89e6e3d3dfc2f882bc0033823049e3cf873e98902ec3f375cc4ae3caca58189ef8b3c3684a1593c5a1eea8af39b7e359955713c006c938c11437c349997783b9f1b058d4ad34133841e383b35b8e18ea2c5da3257a6723ac3d954901bc26a3112f9dc3a49170191b89cf72fb4f77939c5177d937c56be2e3c9d7939378f4d956a1e1f2ca914aa38a0468397854e0e2af9bd9037ff1de399d16d13292e3f213754149e9c522bf12746970d369f4e8a9f0b640e25432b7f35e11ac9a20115fc2324de1b3519facfa537687820ed1ff5344aa9a2a8b2a8931e9e064c33742348ac774bde1c3a5fb43297ac57b089f5dd19c5c99b31b6d9a7b4ef82771744c65230d39873b9ad179914bcd41f2ff0374fbec84120123486da3f1cb92b82cb84763d3f784d3f053fbd8316b3ec3cf6b3cc3eeb6a9c8369b9fc3ca69fe83ecf00db83c564513c4e8c273eafc4fd842a94e53bedb9f13e8d74cc849a43d43b835c013e67c92e8515814e3b0e95f93e3e7617859d77b23a8e7c153e112a7e86336dc13a0213223ddf907186d8c8ed396850ba3da94d49878f0fcb38c01bd53d6e01fc8857ec9938084dd93d2d4b9f89352fd3373fb4223ce6c41f8a28d2d5366512473c9a03388b34fa85357725143c469fbc8c5bf9ea3474a6773bec31278da054b7335c527b3b8a51a68f04c1ad322ced783b20a082908c2cca30e54b9e3aaec5089239b9302f8459fe3a3472019410c2c12e09293639b169ab9614df452c72f9db392582539849df3a2ac14aa53890ab789ab3ce2b28f3e86f37f2f38c9d56f2b7270afffc374c8e30a037ce702507315b369ddaf9a35b1dd222e9a4d335e76c93a6c5d8e620b42112352a1048aa7d35421e6922783466d5d6ae86aa841c0bf35c339f1797b2e7fae619a0c56c32d4833eb7a74208172ccca832092371bccb0cf514b65d353f44cd9c8292682a3d78999c3f316e3482d7d4703d359a083f1c1a7883248ad73cebd8223f04a2c683794d853c9aaf2a3eead39083d6f2683c416cd93ece7533843e65213bdf50c23eaf4bce84b0a9173b738bcc3e8d1723852edbb13afd3fcf3e67928985ba36cb3a7b7f573e3e74f08654134439ed4db13e1170f386fdebcc39519f3c3de0351587b95fd538a75a1e3daa6c10888836b337ed57763d6fbd61896c62e2372265213d2fcdf78a680571364548363cea41308b7d71883554c0513c9eba128caf2ffd344f8be63c4cdcdd8e0002f433346dac3bf451038f72e9703202335e3b94c386910b22cd30b7bdf63b2de9d092cc32072f540b803abf850f94b9e0c32dd642c03a49662396d842012c3dc0b539cb7213992bb46c2a8a281e3945a7259bb8e44b28bb72fc38b8227d9e84cd1626d2061838232654a194baef24cec67d378720b5a4ee4c4722b330b636e4b2aea897744f208171c9363cb80aac967f241e3c81cd35904f78b0f219171be8404134e0e368b5b15b1919899297343033d1badbdf21172686093f6ba622825dd76d3dad2ef63f5c44c3829df0ae3d6f84003f4b54a282e4d1223d2b9a343f38af7183332ff13ce0d7fe3f242bab8389d7803c8e96e43f0d9c6783e9a7633c3422d83ef4d136845396903bd0b9a83ed9960184c8b5ba3b638a763ebbb2f4854a31ed3aebb56a3e9aec7485d957623a684b863e7703258677949039d84ec73e4fb40c87267d81393ab2933e24b8bc87e7cf6c388e5c933df5c7b888bd748d37d2261a3dc294eb89a988453704de1d3d8ad25d8aae5b7536254bfe3d4e311b8bce7916353233323d0c62698d0caafe342a58063cc5193c8e6bfece330c85963c780c178fefcaf031d795353c24f746919bb39a308a77743bcb9f959373afb92f243eef3b6bd57a957c0da42da42d0f3b0578d197b977992c09c0ed3a987d159a30f7c82a54c8623a24ee409ce7fc0c2885736939aaf6299fe45943269c69c8392ae284a32c4e88249ae30a38a52b67a6c688ae2282c0b3381a7a69aaba26ba2056aab5378bb250af0ec08c1e1a2e5136f9f779b3cc71771bd1dfc83666b938b8fbe97019837fe53f91874e822d79163ddd918c3f860e6d8268a7b43da4d2b23f796b0e82aa23a83d664f613f6b804982f299a83d2178a53f5c2ebd8342c9143cd5b3433f4b5469839b85f03c82570d3f38cc8e83fdbb2e3c26ae3f3f246f90846a6d213bc1f4eb3f0e12df84e2bc403b53588a3ef588e98567e8293ad9f7b43edaa11585fb52f83a54e20d3ebd27d3869e84f039c3187d3e9ce6b28753307939238dc43e79a49b881b36863875277d3e53262188f8ab4e37b6bfbb3e292dfa89eddb7336e7274a3dfb7d988afd5183360528cc3dc9d6078c29dbd8350f8cd53d93f8f68d7692d034051f293d59aa118ee6df4932e4b5613d1ab0a7907e815131ad37183cd6d9b2924196fc305da7e73c8dfa3d9434a3332ef533503c3ff23e965c94672d733ae43becaff298becb022bd766b83b9433aa9b611f792a21b86a3b3694309e49e7f32852a0b13ad403b0a17ffd87266b17b13a6cd52ba50ac159246cb8043a018289a8f222062259dca13992b33bad3ea2512035c1c83921439db1f9628f1e04a96b38ae4d33b72c2f1a1bcc040a3fb6b4b98200fa443e0a14453faf153c82379f483dd5e0623fa6aec1827420553d9c59ca3f9d6ddf82b720433d5cfb963f933d7c830153f33d17353c3f8806b0835384613cca69e63f7bb0ae83ae90f03c75efbc3f6e20ae841371fc3c190f4d3f5f39d484833bb43bb3030a3f4edd2984ff214d3b42f6dc3f3ce98e8588788d3ac807f73f293bc08620bdbc3a4144d73f13ae5f86c9980639adad9b3efc1a128784de4b390c34c13ee255ad88549c76385bc05b3ec6367a893b194e379b2bee3ea790998a3adcdb36c94b023e8637838b56b74635e4ecac3e61feb78c91c84a34ece0243e3aba938def871f33dffaa43e10416b8f73cad632bd1ed03de26ce09122d30b318345d73db11b78930150da30318a823d7c329695146fe32ec7368b3d43a0c29761df3c2d43d25d3d07605e99efda1c2ba7377a3cc77ac09cc5302229f1a5cb3c840bbd9fe94d062823dbed3c3d45b0a3643fd8263f32b83bf375fca73ec1f92445bc1f3ba70a17ab823e7f223a65b93b58952fb038db1320211f683b08d68ab56d84471dff070e3fdb715e81d80e093e3304183fd7a2a7820a83883e0300f93fd3704082426bde3dce14c83fced05e8280608b3d93c4173fc9b85a82c50c843d5388803fc41c9e83112e423d0ccff13fbdf09983659a1e3cbefbfa3fb726b383c33cee3c6961293fafb03f842b1efd3c0b46753fa77d74849e675e3ba3e4c53f9e7d63851e5fa63b32669c3f949df885ac781d3ab5e7f73f89cbf9864a4c703a2d76733f7df31486f9a8e9399811c33f70fdec87bc904838f4ac9e3f62d63f8895423b38422e313f53650789864286377f744b3f4292bf8a9260da36ab564f3f3047b18bbcc16b35c4a9353f1c6c5e8d08e63634ca44b93f06ea078e7ab8f933bb09fc3eefab51901695c13295ebcf3ed69d1c91e155f73159f8ef3ebbaf7893e05bc5300668773e9ed6db96199da62e9aa8d13e800d839893b1d22d16716d3e5f551e9b55d9632b79d7813e3cb8b59e680ada29c566203e184ed8a1d2fbf727fa39dc3df23c21a5a02ad2261a203b3dcab607a9d9e68f2427bb6c3da20611ae8b586a2226aaa63d788d81b3c08e87201bb8424000000081b26d093e58a8644000000081e106923e2c8263400000008214b15c3dfbd54a40000000824dfe1f3dc62e9a40000000828d8e6c3d8b117d4000000082d416c73d49f61740000000832261043d0248d14000000083794ef13cb369b24000000083d9dd673c5cabbc40000000844527b13bfd54664000000084bc6b743b949b314000000085410d123b21a9664000000085d49ca33aa39a0e400000008678db8a3a197a3a40000000872fc2c3398249a44000000087fb89eb38dcfbd54000000088deaf1e382879e14000000089dbffb33763a4e9400000008af6a1e2368d5987400000008c321f5535a4745c400000008d9270a334a7d7f7400000008f1c09af339674584000000090d3e6cc326f504e4000000092bf9a803131950b4000000094e55bb52fdc9c3640000000974c14162e7000cd4000000099fb6e3a2cebb340400000009cfbe34c2b50110440000000a056c7e4299e000840000000a41657bb27d70e6d40000000a845c05725fd96e440000000acf12ae32414ea5f40000000b225c62e22217ffa4024a38f818fd5293e7b434e402876de81bae0283e52ace4402caedd81eaa1fa3e25ea314031558c821fa3153df49114403675d7825a7c333dbe2dbc403c1ba2829bd86e3d8241f1404253de82e4779d3d40446640492c988335310f3cf7a00b4050b508838ef69f3ca7b36c4058fd9e83f2d83d3c4fd01540621811846207f33bef3a1d406c176584ddde723b8527c940770fed8567e04d3b10c1634083174e8601c3dc3a91214f4090447186ad77f03a05547c409eaf6f876d2b60396c5b3940ae71708843558c38c52a9e40bfa4798932bfeb380eae9d40d263258a3e90aa3747ccf040e6c8448b6a5672366f691440fcee608cba1560358469804114ef168e3255163485be66412ee24b8fd82fe833726a47414add2891b162fe32498c9e4168f0de93c45f2e310a6f0a4189292196185a4b2fb4955841ab8a5b98b5608c2e47d0c241d00f7d9ba4658b2cc456de41f6a77a9eef546f2b2adca8421f3246a2a11ec0297cb61942497d65a6c5c98427bbfad442753fe8ab6a789425ebb0ae42a215cab09d786f240ffce640499f97817009323e9b120f405151948197cd583e75c3784059ce9581c3f4953e4c9caa40632add81f4ffa13e1f3b61406d7c93822b7ee93ded34404078dbe0826814a73db612254085631382ab77423d79557e40932eca82f6740c3d36739640a25e0e8349f2683cecd5f440b3127883a6f7603c9bd9b840c57049840ea9c33c42cf1a40d99e86848256e23be0f8f540efc700850377f43b758c884108165d8593b8473affb1674122bc068634fc483a7e81b3413fea0a86e9698f39f10abe415fd4e387b36fef39564e1a4182b31f8895d3c538ad435641a8bcd78993b98037f4da7241d22aff8ab0b28d372bff5641ff36708bf0cba236519e6b423016a78d589c843564aaa74265002e8eed592634642556429e229590b4e411334f27ea42dba5e592b5e1ef3224f03e431da78d94f7cdd230e4efae4364368e97830de92f8edd7243af4ef39a6108092e22ccc043fed45a9d9c356d2ca1472b44528b8aa14034ff2b0b6bd944aa12dda559db76296314264504d970a9f740b327aafe87456214c7af27ca1a25e700a2406f38ad8152d0883eb84d4a407adbaa817790253e9604204087b24b81a065613e7030894095db6e81cdc9b63e46779640a578d0820045c93e1875db40b6af4e8238737b3de5bec140c9a7188277004a3daddbdd40de8bed82bcb0193d704c4840f58d57830a60543d2c83f4410edede83610b9c3ce1eb0e412ab83983c1cdf83c8fdd6a4149557c842de9b33c35aa09416af73184a6ccec3bd292c0418fe26c852e18043b65cc0941b860c185c5a4f73aee7d1c41e4c020866f8fce3a6bc05442155290872e403b39dca404424a6db38804748f39402bdd42846a1488f54e1d3895530042c3a2238a045f2d37db0ef7430870d68b35ba99371053c043532fd48c8e051d3634193443a435138e1288583545620f43fbcfca8fc94779344344eb445a449691b91559332cf79e44bfc8af93e9abc83201dd5d452c7bfc9663c39630c1982745a061e799312cc12f6c1df1461b58a89c5ce6032e01d23f469d0eec9ff332e72c83a4b04724f780a401af462af3354647b23ac9a8975f462952ff454843a59eadc4bac827a68bac4095b4e38137f6d23ed3295b40a562578159ef363eb3a83d40b6af13817fb5993e90e49b40c9c4ed81a9bcb33e6a8a6340ded1ae81d885df3e403d9340f60764820ca32a3e119996410f9cb28246b9b43dde309f412bcd26828784753da58b04414ad98782cfd76a3d672695416d082e8320a34d3d2275f94192a546837af9d53cd6e01c41bc031883e012b03c83bfa641e97a3c8451513a3c28628f421b69b884d04b1e3bc409e14252370c855ecff63b55e9a9428e4e0d85fef2193add293342d0209c86b310b53a58e3a943182617877de35939c8292a4366da7b88628722392a008e43bcbd2489648da8387d69ea441a4f048a880dcb37c1621d448010458bd1b67c36f4e79b44ee7d208d46e393361700c3456609c98eedb4953526c41145e71d3990cd25653423629a46720a9a92ed287c330c35404707091e9556c24e31e0cd1447a629f59814252f30a10791484f4c079b30ccd62f4d273549020d2c9eb998702de5f14049bdb86fa2bce1ee2c6cd1554a8130eba74a91082ae403f54b4ad8acac742869294ec8f840bd5c42811f4bb63eebd6a140d1350c813eb5863ecee4da40e71c7e8161ab263eaef2ff40ff47dc818899043e8bb3644119f17d81b3f9ab3e64d0f44137593581e457d53e39ee974157c4c3821a50c73e0aa697417b803f825697133dd689f941a2de8e8299f5d03d9d1fda41ce39ca82e554523d5de4d241fdf3b18339ba803d184a5542327604839855de3ccbb629426c32d384027f653c7781f342aba4c08479c2543c1afadd42f14f0f84ffe40e3bb56174433dbd9f8596ed373b45e9be439184998641343c3acbbba743ed3fd88701696a3a45f3e2445191ef87daa4d239b3a55544bf22af88d076153913db4645369d0289e6f65338659c6e45b8ac0b8b22dc5937a7ef3a4645f73a8c89932436d9df7a46df1d2e8e2152be35fa85d74784ad1d8ff13b5c3509117648371e6c920172833404d43948f6c61d945b41b532ed522549c3c9ad9709361831c2548e4a9e0eed9a174000308401a34b85284c9d92d1392f32f92f4c783cffa18af8622dd0775e4d75ec59a610776b2c5e7e864e7c2b7bab35d2f72ae0093440e6794a8108a2923f0281c240fea5f88125b2183ee7eaf741195534814610543eca91704136c833816a23d53eaa2d7641574671819260cf3e867068417b1e3481bf4b223e5f043041a2a51581f178b63e338aa641ce38928229943d3e039cf841fe3e9c8268606d3dcecb064233262982aebbb73d949ac3426d67bf82fda4b23d5487a242ad85f883563f313d0e01fc42f40df183b9da373cc06e9c434197a88429f6f03c6b26574396c62f84a850c33c0d75d043f447b38536e6bd3ba69d76445ad53785d806713b35d1c944cb3200868e58993aba3c0545462a81875cef953a32fb4c45cc92af8847580d399f267c465f43958951abea38fdcede46ff17e78a80a7ce384e03e447ace7668bd9c333378ed843486980b38d634b3b36bf68b44935a14d8f24803235dee4cc4a11eb3e9125b57434ec9a534afed7ff9370736f33e803ad4bfca80b960f9aec32d0d9ed4d0b4e77990f88c231a72b4b4e2a57d29c7e3865306b76be4f58cb7da06b638e2f1ecdba50950689a4e89c8c2dc2fd0551dc8eeaaa09604f2c5abe024111597580f3d2333f1753f5412e0aa1810eb7b23efee7d4414db793812cb3833ee3f1964170ae0e814e26c13ec62f084197436181737fb73ea5579041c1d504819d3be23e811b9d41f0c94581cbea483e59241b42248ffa82002e3b3e2d11d9425da334823ac28e3dfc7cee429c87f9827c7d583dc6f42242e1cef082c6545d3d8bfc53432e15148319623c3d4b0fe3438204458376ec753d039e3a43de53cf83e06a853cb50b524443c8bd84578e263c5eaf7344b335fd84de4cf93bffd712452d7c338576ebc33b97c2f845b3892686240b783b25a8c3464656a286e8b8533aa8b3d146e6e8a987c87b3c3a2006d147964aba88c76dae398abe1348558bee89ea506c38e7f2d64925b9a28b36a51c3836bfd24a07d8448cb2caf73776475b4afcd9d68e661e8836a5bb714c0591a390591c4c35c4683d4d22a473929585db34d1c1794e547499952688e433cd73764f9b08ee9818e6ea32b7786050f5edc39b7b1c42319032ad52640eb79f5d842330588d9f53e3880ba3d2770e2f1224f855716e07a8ee5ff32dbf752b413e4dc580e0b49c3f2a7339415fbc7780f99c973f1405334184a658811566e03efb414841ad666b81346f823edfea6741da609381571f4a3ec1bd8f420c0258817dedbf3ea071434242c3b281a9637f3e7bb507427f27e181da1cf43e5330cc42c1be4a8210cd8d3e26845d430b2358824e43863df546cb435c015882936c523dbf05d443b5115182e159d93d83455644171bcb8339488f3d417ec64482f97c839ca6ae3cf920c244f993c9840d1c9b3ca98eb4457be509848c96ce3c5220a6460af879851d515a3bf2235046a7e9b685c1e55d3b88d86b4753e39e867d58a33b15777448101e6087532fb63a972ef948dddc87884782af3a0d269649be66a1895f1501397681dd4ab305348a9f708138d264664bbcf8848c0f03d9381ff7554cdd6d938db54466375e70b54e156fc48f9ad375368d1d234f65d64191c9a67e35ab6c4550cf2c41944d31b934b900b652519307973293e233b5c42453ec9c6a9a88c19f32a20077559f1c529e60ae1f317e7f045766ef89a2cd6dc7304caeeb5940b5d6a7e44ebf2f0ed3fb0cfb591bfcea2c74e173e4d30acd10d70d2a3e82fcca0f60e19af1e90abf1a920d59d0bbfca93650e1c21f0f0ab12d190d8a1241fc879db6e1e96c380aa348980dbb059cfc6541f5e210d9590a956d3b0decad57fc421f61e23866630a879b2e0e1f0c0cfc1e323fe260134a0a79d29d0e52245afbf976c2e287e0000a6c13b60e85f8ecfbd3e911e2afcc770a5e5ea50eba8c75fbad853de2d7d89f0a50b3960eefe1b2fb86474ce30004690a4312b70f25fb6bfb5e2b2fe3284fc50a357c340f5cdc70fb352cc9e350baa40a27f03a0f94879cfb0b47e9e37944f40a1a6ef70fccffd4fae0784ee3a1eea40a0cf89710064808fab4b9a5e3cab7a209ff8d4710406330fa880788e3f39fdd09f22d36107b5452fa5a5d81e41ca74109e4d88f10b71e7cfa2bb704e445cdbb09d78f8210f3c4c9f9fc0f75e46f133809ca523a11314a5cf9cb6224e49877a309bd20e6116fb267f999aa4ce4c1fae809affbb311af0023f966e316e4eb9cf109a2e2cf11ef36d7f9330798e5155da90995d667123059d6f8fe12d0e53f3cfa0988d6a912726c7df8c7fface5693acd097be3c312b57237f890c901e593570b096efde212f96e77f8586992e5bd919c09622535133e64c1f81edc0ae5e7ea67095559e8138458a3f7e41b01e612615509489c2a13cb4db6f7a820f6e63cf64c093bec29141347a2f76ae854e667a933092f4a11145c4a1cf72c6b6ee69279ee0922b61114a658e3f6eca480e6bd68640916305714f177c6f6ab8db0e6e874780909b911153daaa0f669210be7139e1008fd506b158af55bf6255885e73ee50f08f0f69515d95bebf5e02dfde76a495808e4abba1628e256f5999b36e795cace08d8700a16798caef55199dce7c1695308cc43b116cb5f12f5082381e7ed24c808c026de171e5db2f4bd319de818fd0f08b419bd17728ccaf470bd8ee844f20908a81c7c17c7f0a6f422c098e8710394089c2f49181e8da1f3d333e5e89d31920890525018766825f3821082e8c97be1088485c018cf84aaf32f4f61e8f5e25f0878c9c41929e7b8f2dae95ae92264eb086d1e8b198595e9f284d725e94f03620861844119e293e3f22d1162e97bbda10855fb141a40e65ef1d39090e9a89384084a832f1aa09223f1784d12e9d584e8083f1cc01b019c09f11b3f2eea0291a70833c7f31b6408fbf0bc5f0bea2fb99d082884f51bc7ddf1f05ba4b1ea5cfca3081d53f21c2d1ff7eff90809ea8a5a95081235171c93d428ef9480deeab7d34a0807288f1cfbffb4ef2e06d9eae5669c07fc2e871d65a7d8eec59184eb13146407f147291dd0d1e6ee5b1848eb40dc7807e672a31e3d8342edee926ceb6ebeb007dbb1201eabc161ed7ff717eb9cbae307d102ca1f1b91cbed0f3d4cebcad0e807c667ce1f8cfa1bec9c5beeebf9009307bbe05620000000ec2749baec2749ba07b16c8d2074a93aebaffd4bec55ac3107a70c9e20eafb9feb366d19ec8427ce079cc0b32162fd17eaba8f77ecb2bc63079288f721dcb39eea3c5a92ece169c30788659422582546e9bbc473ed102fc2077e56b322d55832e938c2fded3f0e3107745c7f2354529de8b34beced6e04e3076a772223d51ad7e82b54d6ed9d13a70760a6c32457b741e7a0d329edcc3a500756eb8d24dc2e58e713bc2bedfb78ac074d45a9256286a8e68404fbee2ace8c0743b53e25eac6d8e5f1a28dee5a3bbf073a3a762674f5a3e55c89afee89c0140730d578270119dbe4c4af01eeb95b580727866c278f3a68e42a06fbeee90d59071e4d7a281f5e4ae38c85e9ef18d5e607152aca28b18c99e2ec1fedef48b4c9070c1e822945cc83e248c8fcef78a9d1070328c929dc254fe1a274dcefa8b4c806fa49c62a749e5be0f9172aefd8d57906f181a02b0f3f1ee04ca351f0090bb006e8d07b2bac0f2adf9d0c92f039573806e0367e2c4b1626deea45fbf069b7d906d7b3ce2cec5bd5de34426cf09a2d5d06cf48902d8fe814dd7af496f0cab78e06c6f4e92e35c2d8dcbe4ef7f0fb563406beb8fe2eddf431dbfe43ddf12c091706b694f32f88844bdb3ac564f15ccfff06ae88ea30357b6cda73c575f18daab306a6950930e4e1f4d9a935c5f1be98f9069eb9713196c060d8db07d7f1ef9a980696f647324b1f48d8092cf7f220af57068f4bab33020760d733963df251d6fa0687b9c133bb817bd65a348cf2831146068040aa34779685d57cf88ff2b45e010678e08835364f8bd49bd2baf2e5bcee0671997b35f7b5b4d3b6b34bf3172dd1066a6ba436bbd247d2cd8a43f348b06e066357243782aea9d1e0476ff37a4487065c5c1a384c545dd0eeda5ff3abe9e006557aa53918cd06cff93268f3dda03a064eb2e639e82264ceff3ea5f40f6757064804fa3aba5e5ace00edf3f4413ef9064171003b8f8ae9ccfe2ef5f47326e1063af7163c67b231cbf6f00ef4a51ecf0634975a3d42de76caeb1f63f4d72683062e51e83e211a1bc9daaadaf5093dbf062826dd3f026fa5c8c58019f53b6440062216553fe6e9bbc7ab8c86f56d99c7061c206c40ce9327c68cbd45f59fde130616453f41b976d5c568ff37f5d230e1061084e642a79fd3c4403efcf60491f1060adf7e43991955c31268edf63700ff0605551f448deeb1c1df6922f6697dca05ffe5e545862b62c0a72b6af69c080e05fa91e74681db08bf699b50f6ce9f8905f5593e47810968be26a416f70143f705f03c044883c26dbcde30b8f733f51505eb3a4f498a1226bb902be9f766b29d05e654374a9404cbba3c800ff7997c4d05e189d34ba1a6bab8e31748f7cc51e005dcdb394cb30478b783db67f7ff330f05d8487f4dc82ab3b61eb5f2f8321f9705d3d1ba4ee1263fb4b39020f865173205cf77003f957ff181aa52e081ac64cd3e5922933f9738ee81a80e3681aa16a53e5b61a23f98f13081a5cca981a7cbaa3e5d9dae3f9aa8ba81a38e3681a583d73e5fd6ba3f9c5f8f81a152d881a33f293e620cca3f9e15b2819f1a8b81a0fd9a3e643fe23f9fcb26819ce54c819ebf263e6670063fa17fef819ab316819c83ca3e689d3a3fa33411819883e6819a4b803e6ac7823fa4e78d819657b7819816453e6ceee13fa69a6781942e858195e4153e6f135b3fa84ca48192084d8193b4ea3e7134f53fa9fe44818fe50b819188c23e7353b13fabaf4d818dc4bb818f5f983e756f943fad5fc1818ba758818d39683e7788a13faf0fa281898cdf818b162d3e799edd3fb0bef68187754d8188f5e43e7bb24a3fb26dbd8185609d8186d8893e7dc2ec3fb41bfd81834ecc8184be173e7fd0c83fb5c9b781813fd68182a68b3e81dbe03fb776f0817f33b7818091e03e83e4383fb923a9817d2a6c817e80133e85e9d53fbacfe7817b23f0817c71203e87ecb93fbc7bad81792040817a65023e89ece83fbe26fd81771f5981785bb73e8bea663fbfd1da81752137817655393e8de5363fc17c49817325d6817451853e8fdd5b3fc3264c81712d33817250983e91d2da3fc4cfe6816f37498170526d3e93c5b63fc6791b816d4417816e57013e95b5f13fc821ed816b5397816c5e503e97a3913fc9ca5f816965c6816a68563e998e973fcb727681677aa28168750f3e9b77083fcd1a3381659226816684783e9d5ce63fcec19a8163ac4f8164968d3e9f40363fd068ae8161c91a8162ab4a3ea120fb3fd20f73815fe8828160c2ac3ea2ff373fd3b5eb815e0a86815edcaf3ea4daef3fd55c1a815c2f21815cf94f3ea6b4253fd70202815a5650815b18893ea88ade3fd8a7a78158800f81593a593eaa5f1b3fda4d0c8156ac5c81575ebc3eac30e13fdbf2348154db33815585ae3eae00333fdd972281530c918153af2c3eafcd143fdf3bd9815140728151db313eb197863fe0e05d814f76d3815009bb3eb35f8f3fe284b0814dafb1814e3ac73eb5252f3fe428d6814beb09814c6e503eb6e86c3fe5ccd1814a28d8814aa4533eb8a9483fe770a68148691a8148dccd3eba67c53fe914568146abcc814717bb3ebc23e83feab7e58144f0ec814555183ebdddb33fec5b5681433875814394e33ebf95293fedfead814182658141d7173ec14a4e3fefa1ec813fceb981401bb03ec2fd253ff14517813e1d6d813e62ad3ec4adb03ff2e830813c6e7f813cac093ec65bf33ff48b3b813ac1ec813af7c13ec807f03ff62e3b813917b0813945d23ec9b1ab3ff7d13381376fc9813796393ecb59273ff974268135ca348135e8f33eccfe663ffb1718813426ed81343dfc3ecea16c3ffcba0a813285f1813295503ed0423c3ffe5d018130e73f8130eeee3ed1e0d840000000812f4ad2812f4ad23ed37d434001a309812db0a8812da8f83ed5178140034621812c18be812c095e3ed6af934004e949812a8311812a6c013ed8457e40068c858128ef9f8128d0dd3ed9d94440082fd981275e64812737ef3edb6ae84009d3478125cf5d8125a1343edcfa6c400b76d28124428981240caa3ede87d3400d1a7e8122b7e381227a4d3ee01321400ebe4e81212f6a8120ea1a3ee19c5840106244811fa91a811f5c0f3ee3237b40120665811e24f1811dd0283ee4a88c4013aab3811ca2ec811c46623ee62b8e40154f31811b2309811abebb3ee7ac854016f3e38119a5448119392f3ee92b72401898cb8118299b8117b5bc3eeaa859401a3ded8116b00c8116345e3eec233c401be34c811538938114b5143eed9c1d401d88eb8113c32f811337d93eef1301401f2ecd81124fdc8111bcab3ef087e84020d4f68110de97811043883ef1fad640227b68810f6f5f810ecc6d3ef36bce40242227810e0231810d57563ef4dad14025c936810c970a810be4413ef647e440277098810b2de8810a732b3ef7b307402918508109c6c8810904123ef91c3e402ac062810861a8810796f23efa838c402c68d08106fe8581062bca3efbe8f3402e119e81059d5c8104c2953efd4c75402fbad081043e2c81035b533efeae15403164678102e0f18101f5ff3f000dd540330e68810185ab810092973f016bb94034b8d581002c5580ff31193f02c7c2403663b280fed4ed80fdd1823f0421f340380f0380fd7f7280fc73d03f057a4e4039bac980fc2be180fb17ff3f06d0d6403b670980fada3780f9be0d3f08258e403d13c680f98a7380f865f83f097877403ec10380f83c9180f70fbc3f0ac99440406ec380f6f09080f5bb593f0c18e840421d0980f5a66e80f468ca3f0d66754043cbd980f45e2780f3180d3f0eb23d40457b3680f317ba80f1c9213f0ffc4340472b2380f1d32580f07c023f1144884048dba480f0906580ef30ad3f128b10404a8cbb80ef4f7880ede7223f13cfdd404c3e6c80ee105c80ec9f5c3f1512f1404df0ba80ecd30e80eb59593f16544e404fa3a980eb978e80ea15183f1793f64051573c80ea5dd780e8d2963f18d1ed40530b7680e925e980e791d03f1a0e334054c05a80e7efc180e652c33f1b48cc405675ed80e6bb5d80e5156f3f1c81ba40582c3080e588bb80e3d9cf3f1db8fe4059e32780e457d880e29fe23f1eee9c405b9ad680e328b380e167a63f202295405d534080e1fb4b80e031183f2154eb405f0c6980e0cf9b80defc363f2285a14060c65380dfa5a480ddc8fd3f23b4b94062810380de7d6180dc976c3f24e23540643c7a80dd56d380db677f3f260e174065f8be80dc31f680da39353f2738624067b5d080db0ec980d90c8c3f286117406973b680d9ed4980d7e1813f298838406b327180d8cd7680d6b8113f2aadc9",
    "relocs": [
     [
      2606,
      "bss",
      0
     ],
     [
      3596,
      "code",
      12404
     ],
     [
      3600,
      "code",
      10340
     ],
     [
      3604,
      "code",
      3608
     ],
     [
      16,
      "bss",
      0
     ],
     [
      400,
      "code",
      3596
     ],
     [
      420,
      "code",
      3272
     ],
     [
      506,
      "code",
      3390
     ],
     [
      558,
      "code",
      3592
     ],
     [
      576,
      "code",
      3600
     ],
     [
      596,
      "code",
      3272
     ],
     [
      1694,
      "code",
      2636
     ],
     [
      1748,
      "code",
      2636
     ],
     [
      1806,
      "code",
      2636
     ],
     [
      3414,
      "code",
      3604
     ]
    ],
    "symbols": {
     "eq_process": [
      "code",
      0
     ],
     "eq_reset": [
      "code",
      2588
     ]
    },
    "bss": 768
   },
   "cost": {
    "emulation": {
     "flat": 38,
     "low": 350,
     "mid": 353,
     "high": 351,
     "all": 767,
     "boost": 819,
     "glide": 912,
     "glide4": 958,
     "silent": 117,
     "first": 937,
     "pattern": "instructions per track and block, EQ's own code only (eq_process, the coefficients, eq_frames), on the OS 1.13 in tools/emu/test_fltslot.py's filter_cost (mcengine.py's counter): all six tracks on it, the stock machines playing, a state held for 8 blocks after 8 of warm-up (flat: every band at its centre; low, mid, high: that band alone, +6 dB, Mid at 2.2 kHz; all: Low and High +6 dB, Mid -6 dB at 450 Hz; boost: the same with High at +12 dB, over 4 (since 0.3); glide: the four values jumping every block, every band across its centre; glide4: the same with High over +9.2 dB in both, over 4 (since 0.6: the dearest case, which glide did not reach); silent: no note played, every band on), the maximum, and the block in which the tracks come to it from none (its reset and first block); the filter slot's own instructions apart"
    },
    "device": {
     "status": "not measured"
    }
   }
  }
 },
 "registrar": {
  "schema": "model27-registrar-frame/0.1",
  "description": [
   "The registrar's part of a build that depends on the number of machines only (notes/61 §3): for n = 1 to",
   "6, the writes (moved tables, bounds, the jumps and the call into the runtime, the marks), the reloc of the",
   "Algorithm parameter's maximum; once, the layout, the runtime, the boot stub template and the stock",
   "addresses whose values fill() reads in the user's own MAIN OS. Written by tools/gen_registrar.py --cycles",
   "from compose.frame(); docs/flasher/composer.js fills it like compose.fill(). \"alone\": the writes of a",
   "build without an added machine, extensions of a stock machine only (compose.frame_alone(), notes/66 §3)."
  ],
  "layout": {
   "pay": 1124073472,
   "bss_off": 221184,
   "first": 6,
   "stubs": 1124282368,
   "data": 1124284416,
   "descn": 1124286464,
   "recs": 1124293632,
   "end_limit": 1075838976,
   "image_end": 1075487040,
   "cave": 1075235560,
   "stub_room": 1024,
   "ndesc": 76,
   "dstride": 56
  },
  "stock": {
   "names": 1074886628,
   "update": 1074890280,
   "render": 1074890256,
   "map": 1074890304,
   "desc": 1074846944,
   "snare_desc": 1074849800
  },
  "runtime": {
   "at": 1124282368,
   "hex": "724cb08165000020b0b943033784650470004e75724c90817205b0816504908160f67233d0814e75202f00046100ffd272644c010800068040a717544e75202f00046100ffbc72644c010800068040a71768487940a715002f2f000c2f004eb9400ddf604fef000c203c40a715004e757405b481651075b943033782b480650c4ef94005a8fa4ef94005a9284ef94005a91c41f943033790b1f94303378c640ab210670841e8001060ee91c84e75224122006100ffde2208671c71a800012228000c670e2041223098006706200172014e75610472014e752200e589eb88908141fa000a20709800d0904e7540fe32cc40fe384c40fe37f061b44a8167da4e7561ac4a8166104a806c0270007205b2806c02700160c24e75200372006100ffda48780001487800174878002045f940071da42f002f024e924fef0030200372046100ffb628004878000148780022487800602f042f024e924fef00144ef9400a268041e8000a2f082f2e0010200272086100ff3c4a81661220026a0270007205b2806c0270056100ff504ef9400a4dece08072046100ff6a4ef94001b6ac72086100ff5e4ef9400a40c272086100ff524ef9400a4fcc202f0004220053816100fed2220866167206b28064027001724c4c010800068040a715404e7571a80003206800046000003e202f000422006100fea2220866267205b280651041f9401091b4713008007206b28064027001724c4c010800068040a715404e7571a80003206800044a28004c6600005e2f022f0a24482400487940a715d82f0a4eb9400f8f02508f487940a715dc486a00044eb9400f8f02508f41f940a715e043ea000872102f0120187233b0816d087237b2806d02d08222c053976aea588f70011540004c204a245f241f20084e7545f940070c4e47f940070efc42852805720b7007b8806d04988072042004e788908406800000005028015884487800012f042f002f0159802f002f02b68566044e9360024e924fef0018528571b943033783b08566b84ef9400a26f2202f0024226a006873b943033782b280640470004e7573b943033781b0816d1e2279430337882f0822006100fd7e2208670a22280008670420414e90205f4e7541f943033790b1f94303378c641473a80002b08165065681b081630841e8001060e491c84e75202f00046100ffd42208670471904e75b0b943033784650270002200e789ed88908141f943034000203008004e757006b0856500002e43f943033790b3f94303378c641873a90002b481650a5681b48162047b91600643e9001060e04ef94005a3844ef94005a346",
   "regs_at": 1124284288,
   "regs_header": 16,
   "entry_size": 16,
   "max_machines": 6
  },
  "stub": {
   "at": "0x4016cae8",
   "end_limit": "0x4016cba8",
   "hex": "43f97b5b5b52203c7c5c5c534299538066fa41f97a5a5a5143fa00262209224120290004670c2251508122d8538066fa60ec4feffff048d700f04ef9400004ba",
   "src_at": 20,
   "dst_at": 2,
   "longs_at": 8,
   "segs_at": 64
  },
  "writes": [
   {
    "off": 178,
    "old": "4feffff048d700f0",
    "new": "4ef94016cae84e71"
   },
   {
    "off": 42318,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 44564,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 44598,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 45036,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 45182,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 45346,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 45666,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 45812,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 45968,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 111244,
    "old": "e0804a806c04",
    "new": "4ef943033190"
   },
   {
    "off": 119278,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 120066,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 121906,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 124122,
    "old": "202f0020226a0068",
    "new": "4eb9430332e84e71"
   },
   {
    "off": 126766,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 140932,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 141062,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 170632,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 176184,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 289124,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 318272,
    "old": "704c222f0004",
    "new": "4ef943033028"
   },
   {
    "off": 318300,
    "old": "7206202f0004",
    "new": "4ef9430331b6"
   },
   {
    "off": 318326,
    "old": "7205202f0004",
    "new": "4ef9430331e8"
   },
   {
    "off": 318370,
    "old": "704c222f0004",
    "new": "4ef94303303e"
   },
   {
    "off": 319278,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 368318,
    "old": "40a79418",
    "new": "43035800"
   },
   {
    "off": 368350,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 368418,
    "old": "40a79418",
    "new": "43035800"
   },
   {
    "off": 368448,
    "old": "7005b085643e",
    "new": "4ef94303337c"
   },
   {
    "off": 368528,
    "old": "40a79418",
    "new": "43035800"
   },
   {
    "off": 368554,
    "old": "40a7ada4",
    "new": "43035a00"
   },
   {
    "off": 368884,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 368906,
    "old": "724c202f0004",
    "new": "4ef94303334e"
   },
   {
    "off": 368918,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 368952,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 368994,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 369010,
    "old": "7205",
    "new": "7206"
   },
   {
    "off": 369050,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 369112,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 369162,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 369204,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 369274,
    "old": "4010dce8",
    "new": "43034008"
   },
   {
    "off": 369338,
    "old": "40a79418",
    "new": "43035800"
   },
   {
    "off": 369392,
    "old": "40a79418",
    "new": "43035800"
   },
   {
    "off": 369534,
    "old": "4010dd00",
    "new": "43034020"
   },
   {
    "off": 369546,
    "old": "4010dd00",
    "new": "43034020"
   },
   {
    "off": 369596,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 369628,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 369668,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 369702,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 369736,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 369770,
    "old": "4010dce0",
    "new": "43034000"
   },
   {
    "off": 369904,
    "old": "7405b4816532",
    "new": "4ef943033070"
   },
   {
    "off": 369938,
    "old": "40a7ada4",
    "new": "43035a00"
   },
   {
    "off": 664084,
    "old": "401177e4",
    "new": "43033800"
   },
   {
    "off": 664120,
    "old": "eb8c48780001",
    "new": "4ef943033118"
   },
   {
    "off": 670882,
    "old": "b2806c047005",
    "new": "4ef94303319e"
   },
   {
    "off": 674244,
    "old": "700541e8000a",
    "new": "4ef943033162"
   },
   {
    "off": 674732,
    "old": "b2806c047005",
    "new": "4ef9430331aa"
   },
   {
    "off": 724230,
    "old": "4016cae8",
    "new": "40154ae4"
   }
  ],
  "by_n": {
   "1": {
    "writes": [
     {
      "off": 42302,
      "old": "744c",
      "new": "7451"
     },
     {
      "off": 42334,
      "old": "744c",
      "new": "7451"
     },
     {
      "off": 42372,
      "old": "704b",
      "new": "7050"
     },
     {
      "off": 42578,
      "old": "704b",
      "new": "7050"
     },
     {
      "off": 44552,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 44586,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 45028,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 45174,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 45338,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 45658,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 45804,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 45960,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 46406,
      "old": "704b",
      "new": "7050"
     },
     {
      "off": 82852,
      "old": "7005",
      "new": "7006"
     },
     {
      "off": 83114,
      "old": "7205",
      "new": "7206"
     },
     {
      "off": 83122,
      "old": "7005",
      "new": "7006"
     },
     {
      "off": 119266,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 120046,
      "old": "704b",
      "new": "7050"
     },
     {
      "off": 120078,
      "old": "704b",
      "new": "7050"
     },
     {
      "off": 121894,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 126758,
      "old": "704c",
      "new": "7051"
     },
     {
      "off": 140924,
      "old": "704c",
      "new": "7051"
     },
     {
      "off": 141054,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 170616,
      "old": "744c",
      "new": "7451"
     },
     {
      "off": 170648,
      "old": "744c",
      "new": "7451"
     },
     {
      "off": 176176,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 289116,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 319262,
      "old": "704b",
      "new": "7050"
     },
     {
      "off": 319418,
      "old": "704c",
      "new": "7051"
     },
     {
      "off": 368312,
      "old": "487800c0",
      "new": "487800e0"
     },
     {
      "off": 368488,
      "old": "704c",
      "new": "7051"
     },
     {
      "off": 368872,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 368940,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 368982,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 369026,
      "old": "724b",
      "new": "7250"
     },
     {
      "off": 369100,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 369150,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 369192,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 369244,
      "old": "704c",
      "new": "7051"
     },
     {
      "off": 369318,
      "old": "7205",
      "new": "7206"
     },
     {
      "off": 369514,
      "old": "724b",
      "new": "7250"
     },
     {
      "off": 369578,
      "old": "724b",
      "new": "7250"
     },
     {
      "off": 369616,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 369656,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 369690,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 369724,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 369758,
      "old": "724c",
      "new": "7251"
     },
     {
      "off": 664032,
      "old": "7005",
      "new": "7006"
     },
     {
      "off": 664296,
      "old": "7006",
      "new": "7007"
     },
     {
      "off": 686444,
      "old": "40118628",
      "new": "4303381c"
     },
     {
      "off": 686522,
      "old": "7205",
      "new": "7206"
     },
     {
      "off": 686532,
      "old": "40118640",
      "new": "43033870"
     },
     {
      "off": 686580,
      "old": "7005",
      "new": "7006"
     },
     {
      "off": 686614,
      "old": "40118610",
      "new": "43033838"
     }
    ],
    "reloc": [
     [
      "0x43034904",
      "00000500",
      "00000600"
     ]
    ]
   },
   "2": {
    "writes": [
     {
      "off": 42302,
      "old": "744c",
      "new": "7456"
     },
     {
      "off": 42334,
      "old": "744c",
      "new": "7456"
     },
     {
      "off": 42372,
      "old": "704b",
      "new": "7055"
     },
     {
      "off": 42578,
      "old": "704b",
      "new": "7055"
     },
     {
      "off": 44552,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 44586,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 45028,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 45174,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 45338,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 45658,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 45804,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 45960,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 46406,
      "old": "704b",
      "new": "7055"
     },
     {
      "off": 82852,
      "old": "7005",
      "new": "7007"
     },
     {
      "off": 83114,
      "old": "7205",
      "new": "7207"
     },
     {
      "off": 83122,
      "old": "7005",
      "new": "7007"
     },
     {
      "off": 119266,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 120046,
      "old": "704b",
      "new": "7055"
     },
     {
      "off": 120078,
      "old": "704b",
      "new": "7055"
     },
     {
      "off": 121894,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 126758,
      "old": "704c",
      "new": "7056"
     },
     {
      "off": 140924,
      "old": "704c",
      "new": "7056"
     },
     {
      "off": 141054,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 170616,
      "old": "744c",
      "new": "7456"
     },
     {
      "off": 170648,
      "old": "744c",
      "new": "7456"
     },
     {
      "off": 176176,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 289116,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 319262,
      "old": "704b",
      "new": "7055"
     },
     {
      "off": 319418,
      "old": "704c",
      "new": "7056"
     },
     {
      "off": 368312,
      "old": "487800c0",
      "new": "48780100"
     },
     {
      "off": 368488,
      "old": "704c",
      "new": "7056"
     },
     {
      "off": 368872,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 368940,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 368982,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 369026,
      "old": "724b",
      "new": "7255"
     },
     {
      "off": 369100,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 369150,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 369192,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 369244,
      "old": "704c",
      "new": "7056"
     },
     {
      "off": 369318,
      "old": "7205",
      "new": "7207"
     },
     {
      "off": 369514,
      "old": "724b",
      "new": "7255"
     },
     {
      "off": 369578,
      "old": "724b",
      "new": "7255"
     },
     {
      "off": 369616,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 369656,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 369690,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 369724,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 369758,
      "old": "724c",
      "new": "7256"
     },
     {
      "off": 664032,
      "old": "7005",
      "new": "7007"
     },
     {
      "off": 664226,
      "old": "7850428545f9",
      "new": "4ef94303328c"
     },
     {
      "off": 686444,
      "old": "40118628",
      "new": "43033820"
     },
     {
      "off": 686522,
      "old": "7205",
      "new": "7207"
     },
     {
      "off": 686532,
      "old": "40118640",
      "new": "43033880"
     },
     {
      "off": 686580,
      "old": "7005",
      "new": "7007"
     },
     {
      "off": 686614,
      "old": "40118610",
      "new": "43033840"
     }
    ],
    "reloc": [
     [
      "0x43034904",
      "00000500",
      "00000700"
     ]
    ]
   },
   "3": {
    "writes": [
     {
      "off": 42302,
      "old": "744c",
      "new": "745b"
     },
     {
      "off": 42334,
      "old": "744c",
      "new": "745b"
     },
     {
      "off": 42372,
      "old": "704b",
      "new": "705a"
     },
     {
      "off": 42578,
      "old": "704b",
      "new": "705a"
     },
     {
      "off": 44552,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 44586,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 45028,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 45174,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 45338,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 45658,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 45804,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 45960,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 46406,
      "old": "704b",
      "new": "705a"
     },
     {
      "off": 82852,
      "old": "7005",
      "new": "7008"
     },
     {
      "off": 83114,
      "old": "7205",
      "new": "7208"
     },
     {
      "off": 83122,
      "old": "7005",
      "new": "7008"
     },
     {
      "off": 119266,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 120046,
      "old": "704b",
      "new": "705a"
     },
     {
      "off": 120078,
      "old": "704b",
      "new": "705a"
     },
     {
      "off": 121894,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 126758,
      "old": "704c",
      "new": "705b"
     },
     {
      "off": 140924,
      "old": "704c",
      "new": "705b"
     },
     {
      "off": 141054,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 170616,
      "old": "744c",
      "new": "745b"
     },
     {
      "off": 170648,
      "old": "744c",
      "new": "745b"
     },
     {
      "off": 176176,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 289116,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 319262,
      "old": "704b",
      "new": "705a"
     },
     {
      "off": 319418,
      "old": "704c",
      "new": "705b"
     },
     {
      "off": 368312,
      "old": "487800c0",
      "new": "48780120"
     },
     {
      "off": 368488,
      "old": "704c",
      "new": "705b"
     },
     {
      "off": 368872,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 368940,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 368982,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 369026,
      "old": "724b",
      "new": "725a"
     },
     {
      "off": 369100,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 369150,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 369192,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 369244,
      "old": "704c",
      "new": "705b"
     },
     {
      "off": 369318,
      "old": "7205",
      "new": "7208"
     },
     {
      "off": 369514,
      "old": "724b",
      "new": "725a"
     },
     {
      "off": 369578,
      "old": "724b",
      "new": "725a"
     },
     {
      "off": 369616,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 369656,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 369690,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 369724,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 369758,
      "old": "724c",
      "new": "725b"
     },
     {
      "off": 664032,
      "old": "7005",
      "new": "7008"
     },
     {
      "off": 664226,
      "old": "7850428545f9",
      "new": "4ef94303328c"
     },
     {
      "off": 686444,
      "old": "40118628",
      "new": "43033824"
     },
     {
      "off": 686522,
      "old": "7205",
      "new": "7208"
     },
     {
      "off": 686532,
      "old": "40118640",
      "new": "43033890"
     },
     {
      "off": 686580,
      "old": "7005",
      "new": "7008"
     },
     {
      "off": 686614,
      "old": "40118610",
      "new": "43033848"
     }
    ],
    "reloc": [
     [
      "0x43034904",
      "00000500",
      "00000800"
     ]
    ]
   },
   "4": {
    "writes": [
     {
      "off": 42302,
      "old": "744c",
      "new": "7460"
     },
     {
      "off": 42334,
      "old": "744c",
      "new": "7460"
     },
     {
      "off": 42372,
      "old": "704b",
      "new": "705f"
     },
     {
      "off": 42578,
      "old": "704b",
      "new": "705f"
     },
     {
      "off": 44552,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 44586,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 45028,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 45174,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 45338,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 45658,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 45804,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 45960,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 46406,
      "old": "704b",
      "new": "705f"
     },
     {
      "off": 82852,
      "old": "7005",
      "new": "7009"
     },
     {
      "off": 83114,
      "old": "7205",
      "new": "7209"
     },
     {
      "off": 83122,
      "old": "7005",
      "new": "7009"
     },
     {
      "off": 119266,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 120046,
      "old": "704b",
      "new": "705f"
     },
     {
      "off": 120078,
      "old": "704b",
      "new": "705f"
     },
     {
      "off": 121894,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 126758,
      "old": "704c",
      "new": "7060"
     },
     {
      "off": 140924,
      "old": "704c",
      "new": "7060"
     },
     {
      "off": 141054,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 170616,
      "old": "744c",
      "new": "7460"
     },
     {
      "off": 170648,
      "old": "744c",
      "new": "7460"
     },
     {
      "off": 176176,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 289116,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 319262,
      "old": "704b",
      "new": "705f"
     },
     {
      "off": 319418,
      "old": "704c",
      "new": "7060"
     },
     {
      "off": 368312,
      "old": "487800c0",
      "new": "48780140"
     },
     {
      "off": 368488,
      "old": "704c",
      "new": "7060"
     },
     {
      "off": 368872,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 368940,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 368982,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 369026,
      "old": "724b",
      "new": "725f"
     },
     {
      "off": 369100,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 369150,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 369192,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 369244,
      "old": "704c",
      "new": "7060"
     },
     {
      "off": 369318,
      "old": "7205",
      "new": "7209"
     },
     {
      "off": 369514,
      "old": "724b",
      "new": "725f"
     },
     {
      "off": 369578,
      "old": "724b",
      "new": "725f"
     },
     {
      "off": 369616,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 369656,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 369690,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 369724,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 369758,
      "old": "724c",
      "new": "7260"
     },
     {
      "off": 664032,
      "old": "7005",
      "new": "7009"
     },
     {
      "off": 664226,
      "old": "7850428545f9",
      "new": "4ef94303328c"
     },
     {
      "off": 686444,
      "old": "40118628",
      "new": "43033828"
     },
     {
      "off": 686522,
      "old": "7205",
      "new": "7209"
     },
     {
      "off": 686532,
      "old": "40118640",
      "new": "430338a0"
     },
     {
      "off": 686580,
      "old": "7005",
      "new": "7009"
     },
     {
      "off": 686614,
      "old": "40118610",
      "new": "43033850"
     }
    ],
    "reloc": [
     [
      "0x43034904",
      "00000500",
      "00000900"
     ]
    ]
   },
   "5": {
    "writes": [
     {
      "off": 42302,
      "old": "744c",
      "new": "7465"
     },
     {
      "off": 42334,
      "old": "744c",
      "new": "7465"
     },
     {
      "off": 42372,
      "old": "704b",
      "new": "7064"
     },
     {
      "off": 42578,
      "old": "704b",
      "new": "7064"
     },
     {
      "off": 44552,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 44586,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 45028,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 45174,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 45338,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 45658,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 45804,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 45960,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 46406,
      "old": "704b",
      "new": "7064"
     },
     {
      "off": 82852,
      "old": "7005",
      "new": "700a"
     },
     {
      "off": 83114,
      "old": "7205",
      "new": "720a"
     },
     {
      "off": 83122,
      "old": "7005",
      "new": "700a"
     },
     {
      "off": 119266,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 120046,
      "old": "704b",
      "new": "7064"
     },
     {
      "off": 120078,
      "old": "704b",
      "new": "7064"
     },
     {
      "off": 121894,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 126758,
      "old": "704c",
      "new": "7065"
     },
     {
      "off": 140924,
      "old": "704c",
      "new": "7065"
     },
     {
      "off": 141054,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 170616,
      "old": "744c",
      "new": "7465"
     },
     {
      "off": 170648,
      "old": "744c",
      "new": "7465"
     },
     {
      "off": 176176,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 289116,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 319262,
      "old": "704b",
      "new": "7064"
     },
     {
      "off": 319418,
      "old": "704c",
      "new": "7065"
     },
     {
      "off": 368312,
      "old": "487800c0",
      "new": "48780160"
     },
     {
      "off": 368488,
      "old": "704c",
      "new": "7065"
     },
     {
      "off": 368872,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 368940,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 368982,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 369026,
      "old": "724b",
      "new": "7264"
     },
     {
      "off": 369100,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 369150,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 369192,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 369244,
      "old": "704c",
      "new": "7065"
     },
     {
      "off": 369318,
      "old": "7205",
      "new": "720a"
     },
     {
      "off": 369514,
      "old": "724b",
      "new": "7264"
     },
     {
      "off": 369578,
      "old": "724b",
      "new": "7264"
     },
     {
      "off": 369616,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 369656,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 369690,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 369724,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 369758,
      "old": "724c",
      "new": "7265"
     },
     {
      "off": 664032,
      "old": "7005",
      "new": "700a"
     },
     {
      "off": 664226,
      "old": "7850428545f9",
      "new": "4ef94303328c"
     },
     {
      "off": 686444,
      "old": "40118628",
      "new": "4303382c"
     },
     {
      "off": 686522,
      "old": "7205",
      "new": "720a"
     },
     {
      "off": 686532,
      "old": "40118640",
      "new": "430338b0"
     },
     {
      "off": 686580,
      "old": "7005",
      "new": "700a"
     },
     {
      "off": 686614,
      "old": "40118610",
      "new": "43033858"
     }
    ],
    "reloc": [
     [
      "0x43034904",
      "00000500",
      "00000a00"
     ]
    ]
   },
   "6": {
    "writes": [
     {
      "off": 42302,
      "old": "744c",
      "new": "746a"
     },
     {
      "off": 42334,
      "old": "744c",
      "new": "746a"
     },
     {
      "off": 42372,
      "old": "704b",
      "new": "7069"
     },
     {
      "off": 42578,
      "old": "704b",
      "new": "7069"
     },
     {
      "off": 44552,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 44586,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 45028,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 45174,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 45338,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 45658,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 45804,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 45960,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 46406,
      "old": "704b",
      "new": "7069"
     },
     {
      "off": 82852,
      "old": "7005",
      "new": "700b"
     },
     {
      "off": 83114,
      "old": "7205",
      "new": "720b"
     },
     {
      "off": 83122,
      "old": "7005",
      "new": "700b"
     },
     {
      "off": 119266,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 120046,
      "old": "704b",
      "new": "7069"
     },
     {
      "off": 120078,
      "old": "704b",
      "new": "7069"
     },
     {
      "off": 121894,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 126758,
      "old": "704c",
      "new": "706a"
     },
     {
      "off": 140924,
      "old": "704c",
      "new": "706a"
     },
     {
      "off": 141054,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 170616,
      "old": "744c",
      "new": "746a"
     },
     {
      "off": 170648,
      "old": "744c",
      "new": "746a"
     },
     {
      "off": 176176,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 289116,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 319262,
      "old": "704b",
      "new": "7069"
     },
     {
      "off": 319418,
      "old": "704c",
      "new": "706a"
     },
     {
      "off": 368312,
      "old": "487800c0",
      "new": "48780180"
     },
     {
      "off": 368488,
      "old": "704c",
      "new": "706a"
     },
     {
      "off": 368872,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 368940,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 368982,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 369026,
      "old": "724b",
      "new": "7269"
     },
     {
      "off": 369100,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 369150,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 369192,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 369244,
      "old": "704c",
      "new": "706a"
     },
     {
      "off": 369318,
      "old": "7205",
      "new": "720b"
     },
     {
      "off": 369514,
      "old": "724b",
      "new": "7269"
     },
     {
      "off": 369578,
      "old": "724b",
      "new": "7269"
     },
     {
      "off": 369616,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 369656,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 369690,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 369724,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 369758,
      "old": "724c",
      "new": "726a"
     },
     {
      "off": 664032,
      "old": "7005",
      "new": "700b"
     },
     {
      "off": 664226,
      "old": "7850428545f9",
      "new": "4ef94303328c"
     },
     {
      "off": 686444,
      "old": "40118628",
      "new": "43033830"
     },
     {
      "off": 686522,
      "old": "7205",
      "new": "720b"
     },
     {
      "off": 686532,
      "old": "40118640",
      "new": "430338c0"
     },
     {
      "off": 686580,
      "old": "7005",
      "new": "700b"
     },
     {
      "off": 686614,
      "old": "40118610",
      "new": "43033860"
     }
    ],
    "reloc": [
     [
      "0x43034904",
      "00000500",
      "00000b00"
     ]
    ]
   }
  },
  "alone": {
   "writes": [
    {
     "off": 178,
     "old": "4feffff048d700f0",
     "new": "4ef94016cae84e71"
    },
    {
     "off": 724230,
     "old": "4016cae8",
     "new": "40154ae4"
    }
   ]
  }
 },
 "parts": {
  "shortcuts": {
   "id": "shortcuts",
   "version": "0.6",
   "roots": [
    "sc_knob",
    "sc_save2",
    "sc_save1",
    "sc_load",
    "sc_press",
    "sc_leds",
    "sc_mach",
    "sc_conv",
    "sc_ptab",
    "sc_mtrig",
    "sc_steplock",
    "sc_gridleds"
   ],
   "patch_points": [
    {
     "symbol": "sc_data",
     "kind": "shortcut_data"
    }
   ],
   "data": {
    "next": 0,
    "descn": 12,
    "first": 16,
    "count": 17,
    "presses": 20,
    "every": 28,
    "entries": 32,
    "entry_size": 24,
    "pending": 18,
    "used": 19,
    "max_machines": 8
   },
   "bundle": {
    "code": "2f2f00102f2f00102f2f00102f2f00104eb94001e8144fef00104feffff048d7041c2800242f001859827003b082650000f2487800054eb94007faf4588f4a80670000e045fa00e8719a67122f004eb94007faf4588f4a8067ee600000c64eb9400cf9a82f004eb94006b736588f4a00660000b02f2f00202f2f00184eb94001e318508f45f90000000073aa001090816b00009073aa0011b08164000086e588d082c0fc001841f208204a90670000747601d6822003c0fc0038226a000cd3c0701cd0822340000420280008234000082028000c2340000c202800102340001042a9001470ff234000182340001c42a9002020102340002c20280004234000342003c0fc006443f940a71754d3c0202800142340002042a9002c157c00010013280320044cd7041c4fef00104e750102080000002f2f00082f2f0008487a006020390000000066524feffff448d71c004ef94005afa82f2f00082f2f0008487a003e20390000000066304feffff448d71c004ef94005b05c2f2f00082f2f0008487a0042203900000000660e4feffff448d71c004ef94005aed420404ed04a00671e2057226f00042229004c2141005422290050214100583229005431410040508f4e754a0067222257206f0004222800542341004c2228005823410050322800403341005442690014508f4e7500002f02242f000c04820000002c7001b0826500007a487800054eb94007faf4588f4a8067000068487800024eb94007faf4588f4a80660000566100037e6100039c0501670000482f084eb9400cf9a82f004eb94006b736588f205f4a00670661000096600c508273e8005405413141005443f900000000137c000100132f2f00084eb9400760ba588f241f4e75241f4feffff472014ef94001ac5000002a002f03487800054eb94007faf4588f4a80673e487800024eb94007faf4588f4a80662e2004610003162601672473e800546100016808030000670824010282000001000803000167082a01028500000200261f4a8257c04e754fefffe048d70cfc2e027de800544eb9400cf9a82640487800012f0b4eb94006b740508f4eb9400cf8662f004eb94000f23e24402e8a4eb940016402588f2a007800b8856c0000b02004222b01607420b0826d069082222b015c010167000092610000a8260072004a836b082203028100000f0020075080740001066702740154800101670a558074000101670274017001b18220075080010667064a82661460044a82670e01814a82670201c1548001c160060181548001812001028000000c0066184a836b28487800202f042f0a4eb9400164b04fef000c60142f01487800202f042f0a4eb94001646a4fef001052846000ff4e2f0b4eb94006b954588f4cd70cfc4fef00204e75202a002c672e20402f082250226900284e91588f4a80671c2040202a00386b14c0fc1121d1c02004c0fc0044d1c0716800404e7570ff4e754feffff048d7041c24014eb9400cf9a824402f004eb94006b736588f4a0067647800202a016066087820202a015c675422004481c28004c1701f9081d8804eb9400cf8662f004eb94000f23e588f24406100ff764a806b2c22020800000a670e0881000808000008670408c100080800000b67120881000908000009670808c10009600222024cd7041c4fef00104e752f034eb9400724a0588f4a0067000066487800054eb94007faf4588f4a806700005c487800024eb94007faf4588f4a806600004a2f034eb94007240c588f5d807201b280650000362f022400610000a2610000c0050167226100fdd443f900000000137c000100132f0a4eb9400760ba588f241f4ef940022ff2241f4ef940022ebc2f03487800054eb94007faf4588f4a806754487800024eb94007faf4588f4a8066446100004a610000682601673873e800546100feba71af005f08030000670e0880000108010008670408c0000108030001670e0880000208010009670408c000021f40005f261f4ef9400cfc5e4eb9400cf8664a8067142f004eb94000eb902e804eb940012412588f4e7570ff4e752f0224007205b28265544eb9400cf8664a80674ac4fc0044d4800682000000d4204220106738224020290028673022402f024e91588f4a806724204071a8002643f90000000073a9001090816b1073a90011b081640873b10814241f4e75720070ff241f4e752f034e93588f4a006736610000ba4a806720610000f64a80661843f900000000137c0001001242290013588f4ef94001c2a843f9000000004229001270014e752f034eb940072470588f43f9000000004a00672273a90012671c422900124a29001366125581670470014e75588f74014ef94001c99670004e754eb9400cf9a82f004eb94006b736588f4a0067326100fee86100ff064a81672043f900000000137c00020012422900132f0a4eb9400760ba588f4ef94001c2a84ef94001c9964ef94001ca1e41f90000000008280000001c66326100fea26100fec04a8166264a806b1ee588c0fc001841f90000000041f0082072034a90660c41e8001853816af470004e7570014e75202a002c672a204043e800142051b1c9671e202800086714224020110c80401179206710226a002c43e90014205060de70004e7570014e7500007412b48067207417b480640e7420b480650e53804ef94005aa504ef94005aa464ef94005aa3a70204ef94005aa500000000000000000000100000002000000030000000400000005000000060000000700000008000000090000000a0000000b0000000c0000000d0000000e0000000f0000001000000011000000130000001400000015000000160000001700000018000000190000001a0000001b0000001c0000001d0000001e0000001f0000002000000012",
    "relocs": [
     [
      134,
      "sc_data",
      0
     ],
     [
      322,
      "sc_data",
      0
     ],
     [
      356,
      "sc_data",
      4
     ],
     [
      390,
      "sc_data",
      8
     ],
     [
      610,
      "sc_data",
      0
     ],
     [
      1302,
      "sc_data",
      0
     ],
     [
      1548,
      "sc_data",
      0
     ],
     [
      1612,
      "sc_data",
      0
     ],
     [
      1636,
      "sc_data",
      0
     ],
     [
      1660,
      "sc_data",
      0
     ],
     [
      1740,
      "sc_data",
      0
     ],
     [
      1784,
      "sc_data",
      0
     ],
     [
      1820,
      "sc_data",
      0
     ]
    ],
    "symbols": {
     "sc_knob": [
      "code",
      0
     ],
     "sc_save2": [
      "code",
      308
     ],
     "sc_save1": [
      "code",
      342
     ],
     "sc_load": [
      "code",
      376
     ],
     "sc_press": [
      "code",
      496
     ],
     "sc_leds": [
      "code",
      652
     ],
     "sc_mach": [
      "code",
      1584
     ],
     "sc_conv": [
      "code",
      1908
     ],
     "sc_ptab": [
      "code",
      1956
     ],
     "sc_mtrig": [
      "code",
      1706
     ],
     "sc_steplock": [
      "code",
      1208
     ],
     "sc_gridleds": [
      "code",
      1338
     ]
    },
    "bss": 0
   },
   "sites": {
    "knob": {
     "vtable": "0x401005a8",
     "stock_ptr": "0x4001e814",
     "symbol": "sc_knob"
    },
    "record": [
     {
      "at": "0x4005afa0",
      "stock": "4feffff448d71c00",
      "symbol": "sc_save2"
     },
     {
      "at": "0x4005b054",
      "stock": "4feffff448d71c00",
      "symbol": "sc_save1"
     },
     {
      "at": "0x4005aecc",
      "stock": "4feffff448d71c00",
      "symbol": "sc_load"
     }
    ],
    "press": [
     {
      "at": "0x4001ac4a",
      "stock": "4feffff47201",
      "op": "jmp",
      "symbol": "sc_press"
     },
     {
      "at": "0x4001cc86",
      "stock": "2a004a8257c0",
      "op": "jsr",
      "symbol": "sc_leds"
     },
     {
      "at": "0x4001c274",
      "stock": "4eb9400cf9a8",
      "op": "jmp",
      "symbol": "sc_mtrig"
     },
     {
      "at": "0x40022eac",
      "stock": "2f034eb94007",
      "op": "jmp",
      "symbol": "sc_steplock"
     },
     {
      "at": "0x40022112",
      "stock": "4eb9400cfc5e",
      "op": "jsr",
      "symbol": "sc_gridleds"
     }
    ],
    "keys": [
     {
      "at": "0x4001ca1e",
      "stock": "2f034e93588f",
      "op": "jsr",
      "symbol": "sc_mach"
     }
    ],
    "conv": {
     "jmp": "0x4005aa34",
     "stock": "7417b480640c",
     "symbol": "sc_conv"
    },
    "ptab": {
     "operands": [
      "0x4005b998",
      "0x4005baca"
     ],
     "stock": "0x4010ee4c",
     "symbol": "sc_ptab"
    }
   },
   "shortcut": {
    "key": "MACHINES",
    "knobs": [
     "COLOR",
     "SHAPE",
     "SWEEP",
     "CONTOUR"
    ],
    "descriptors": [
     1,
     2,
     3,
     4
    ],
    "sound_slots": [
     28,
     29,
     30,
     31
    ],
    "record_slots": [
     28,
     29,
     30,
     31
    ],
    "range": [
     -128,
     127
    ],
    "formatter": "0x400456c8",
    "presses": [
     "PUNCH",
     "GATE"
    ],
    "press_bits": [
     8,
     9
    ],
    "press_sound_slot": 32,
    "press_record_slot": 18
   },
   "claims": {
    "sound_slots": [
     [
      28,
      "all"
     ],
     [
      29,
      "all"
     ],
     [
      30,
      "all"
     ],
     [
      31,
      "all"
     ],
     [
      32,
      "all"
     ]
    ],
    "record_slots": [
     [
      18,
      "all"
     ],
     [
      28,
      "all"
     ],
     [
      29,
      "all"
     ],
     [
      30,
      "all"
     ],
     [
      31,
      "all"
     ]
    ],
    "descriptors": [
     [
      1,
      "all"
     ],
     [
      2,
      "all"
     ],
     [
      3,
      "all"
     ],
     [
      4,
      "all"
     ]
    ],
    "plock_rows": true,
    "gestures": [
     {
      "combo": "MACHINES + COLOR/SHAPE/SWEEP/CONTOUR",
      "atoms": [
       [
        "MACHINES",
        "COLOR"
       ],
       [
        "MACHINES",
        "CONTOUR"
       ],
       [
        "MACHINES",
        "SHAPE"
       ],
       [
        "MACHINES",
        "SWEEP"
       ]
      ],
      "situation": "params",
      "scope": "all",
      "meaning": "the shortcut of the track's machine",
      "replaces": null
     },
     {
      "combo": "MACHINES + PUNCH/GATE",
      "atoms": [
       [
        "MACHINES",
        "GATE"
       ],
       [
        "MACHINES",
        "PUNCH"
       ]
      ],
      "situation": "any",
      "scope": "all",
      "meaning": "the switch of the track's machine",
      "replaces": null
     },
     {
      "combo": "MACHINES",
      "atoms": [
       [
        "",
        "MACHINES"
       ]
      ],
      "situation": "any",
      "scope": "all",
      "meaning": "on the tracks of a machine with a shortcut or a switch (on every track in a build with Transpose, since 0.6), the MACHINES list opens on the release, unless a shortcut or a switch acted",
      "replaces": "the toggle of the MACHINES list on the press (a press while it is open still closes it at once)"
     },
     {
      "combo": "TRIG 1-16 + MACHINES",
      "atoms": [
       [
        "TRIG 1",
        "MACHINES"
       ],
       [
        "TRIG 10",
        "MACHINES"
       ],
       [
        "TRIG 11",
        "MACHINES"
       ],
       [
        "TRIG 12",
        "MACHINES"
       ],
       [
        "TRIG 13",
        "MACHINES"
       ],
       [
        "TRIG 14",
        "MACHINES"
       ],
       [
        "TRIG 15",
        "MACHINES"
       ],
       [
        "TRIG 16",
        "MACHINES"
       ],
       [
        "TRIG 2",
        "MACHINES"
       ],
       [
        "TRIG 3",
        "MACHINES"
       ],
       [
        "TRIG 4",
        "MACHINES"
       ],
       [
        "TRIG 5",
        "MACHINES"
       ],
       [
        "TRIG 6",
        "MACHINES"
       ],
       [
        "TRIG 7",
        "MACHINES"
       ],
       [
        "TRIG 8",
        "MACHINES"
       ],
       [
        "TRIG 9",
        "MACHINES"
       ]
      ],
      "situation": "any",
      "scope": "all",
      "meaning": "on the tracks of a machine with a switch, the PRESET browser opens on the release of MACHINES, unless a switch acted",
      "replaces": "the PRESET browser on the press"
     },
     {
      "combo": "TRIG 1-16 + MACHINES + PUNCH/GATE",
      "atoms": [
       [
        "MACHINES+TRIG 1",
        "GATE"
       ],
       [
        "MACHINES+TRIG 1",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 10",
        "GATE"
       ],
       [
        "MACHINES+TRIG 10",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 11",
        "GATE"
       ],
       [
        "MACHINES+TRIG 11",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 12",
        "GATE"
       ],
       [
        "MACHINES+TRIG 12",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 13",
        "GATE"
       ],
       [
        "MACHINES+TRIG 13",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 14",
        "GATE"
       ],
       [
        "MACHINES+TRIG 14",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 15",
        "GATE"
       ],
       [
        "MACHINES+TRIG 15",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 16",
        "GATE"
       ],
       [
        "MACHINES+TRIG 16",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 2",
        "GATE"
       ],
       [
        "MACHINES+TRIG 2",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 3",
        "GATE"
       ],
       [
        "MACHINES+TRIG 3",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 4",
        "GATE"
       ],
       [
        "MACHINES+TRIG 4",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 5",
        "GATE"
       ],
       [
        "MACHINES+TRIG 5",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 6",
        "GATE"
       ],
       [
        "MACHINES+TRIG 6",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 7",
        "GATE"
       ],
       [
        "MACHINES+TRIG 7",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 8",
        "GATE"
       ],
       [
        "MACHINES+TRIG 8",
        "PUNCH"
       ],
       [
        "MACHINES+TRIG 9",
        "GATE"
       ],
       [
        "MACHINES+TRIG 9",
        "PUNCH"
       ]
      ],
      "situation": "any",
      "scope": "all",
      "meaning": "on the tracks of a machine with a switch, that switch of each held step as a p-lock of k 32",
      "replaces": null
     }
    ]
   }
  },
  "dispatch": {
   "id": "dispatch",
   "version": "0.4",
   "roots": [
    "dp_main",
    "dp_knob",
    "dp_tick",
    "dp_open",
    "dp_note"
   ],
   "patch_points": [
    {
     "symbol": "dp_data",
     "kind": "dispatch_data"
    }
   ],
   "data": {
    "first": 0,
    "count": 1,
    "size": 164,
    "max_machines": 8
   },
   "bundle": {
    "code": "518f2f3c4001b22a2f6f001000042f6f001400084879000000004eb9000000002f6f000c001822402f6f000800144fef00104ed1518f2f3c4001e40a2f6f001000042f6f001400084879000000004eb9000000002f6f000c001822402f6f000800144fef00104ed12f024eb9400cf8664a80673e7205b2af00086536222f000874444c0218000681000000d4d081224020514a88671c206800284a8867142f004e90588f4a80670a204071a80026241f4e75241f70ff4e752f024eb9400cf8664a80673e2f004eb94000eb902f004eb9400124122f004eb90000000075b90000000073b9000000004fef000c9082b0816410206f000820300c004a806704241f4e75202f000c241f4e75518f2f3c400299de2f6f001000042f6f001400084879000000004eb9000000002f6f000c001822402f6f000800144fef00104ed14feffff048d7041c282f00144a3900000000672077b90000000045f9000000004282205a4a8867062f044e90588f5282b68266ee2f4400144cd7041c4fef00104ef940076be42f02206f000820502f2802984eb90000000073b900000000588f41f90000000075909082b280630c20300c644a806704241f4e75241f203c400a30524e7500002f082f0a4eb900000000588f205f22404ed1",
    "relocs": [
     [
      216,
      "code",
      104
     ],
     [
      222,
      "dp_data",
      0
     ],
     [
      228,
      "dp_data",
      1
     ],
     [
      22,
      "dp_data",
      4
     ],
     [
      28,
      "code",
      184
     ],
     [
      74,
      "dp_data",
      36
     ],
     [
      80,
      "code",
      184
     ],
     [
      288,
      "dp_data",
      132
     ],
     [
      294,
      "code",
      184
     ],
     [
      332,
      "dp_data",
      1
     ],
     [
      340,
      "dp_data",
      1
     ],
     [
      346,
      "dp_data",
      68
     ],
     [
      402,
      "code",
      104
     ],
     [
      408,
      "dp_data",
      1
     ],
     [
      416,
      "dp_data",
      0
     ],
     [
      458,
      "code",
      388
     ]
    ],
    "symbols": {
     "dp_main": [
      "code",
      0
     ],
     "dp_knob": [
      "code",
      52
     ],
     "dp_tick": [
      "code",
      318
     ],
     "dp_open": [
      "code",
      452
     ],
     "dp_note": [
      "code",
      266
     ]
    },
    "bss": 0
   },
   "sites": {
    "view.main": {
     "vtable": "0x400ffe30",
     "stock_ptr": "0x4001b22a",
     "symbol": "dp_main",
     "table": 4
    },
    "view.knob": {
     "vtable": "0x4010053c",
     "stock_ptr": "0x4001e40a",
     "symbol": "dp_knob",
     "table": 36
    },
    "screen.tick": {
     "hook": "0x400075f0",
     "stock": "4eb940076be4",
     "op": "jsr",
     "symbol": "dp_tick",
     "table": 68
    },
    "browser.open": {
     "hook": "0x400a6602",
     "stock": "4eb9400a3052",
     "op": "jsr",
     "symbol": "dp_open",
     "table": 100
    },
    "view.note": {
     "vtable": "0x40102578",
     "stock_ptr": "0x400299de",
     "symbol": "dp_note",
     "table": 132
    }
   }
  },
  "fxslot": {
   "id": "fxslot",
   "version": "0.7",
   "roots": [
    "fx_delay",
    "fx_reverb",
    "fx_keys",
    "fx_release",
    "fx_load",
    "fx_init",
    "fx_early",
    "fx_late"
   ],
   "patch_points": [
    {
     "symbol": "fx_data",
     "kind": "fx_data"
    }
   ],
   "data": {
    "entries": 8,
    "size": 1184,
    "slots": [
     0,
     100
    ],
    "desc": 200,
    "names": 208,
    "state": 1168,
    "busy": 1180
   },
   "bundle": {
    "code": "7000600270012f2f000c2f2f000c2f2f000c2f004eb9000000004fef00104e754fefffe8726448d70c04246f001c200a4c01080074012040d1fc000000002250b489640000b6203c000000e05888220a4c001800200a0680000000002640428075ab049041e8000cb4a8fff4670000c85280b08966ee42802041d1c0d1fc000000004a8a677e203c000008c0227c40a72714247c40a726b02f40000c243c000008882f490014203c000000002f4a0010223c000000002440225a200a45f12800d3ef000c2550002c25680010003025680004003423680008002c2368001000302368000c0034b08166cc266f0010226f001426a8001422a800184cd70c044fef00184e75203c00000850227c40a7264c247c40a725e82f40000c243c000008182f490014203c000000002f4a0010223c000000006080741c4c0208006000ff3a203940fe4228207940a7887c2f024a8067244a886724222877f2745fb481651a243c000002dc4c021800204006810000148420301800241f4e75241f42804e75598f2f0a2f02206f0014226f00101228001f1028001d73811f40000b1028001e142f000b344245f2085a200a7180b081672640c0220000810000070046c14201745a1341001d1341001e1342001f46c0241f245f588f4e751228001e1028001d304040c0240000820000070046c2340845f0185a1342001d1341001e2f4a0008136f000b001f46c0241f245f588f4e75206f000440c0220000810000070046c142011141001d1141001e725a1141001f46c04e754fefffec7264202f001848d70c042439fc07000c4c0108002f4200102440d5fc000000004eb90000000020404a80671e1228001f1028001d738132401028001e43f1085a20097180b081670000f2266f0018d7fc0000000075ab049093c942814280b082660000ba22524a89671641ea0004428041e8000cb2a8fff4670c5280b08966f0222a00044280142b049230427582b282670000cc34084a026624487900000000206a00084879000000004879000000002f4000184e904fef000c202f000c2200740c52814c021800207218004a88670a2f40000c4e90202f000c720c4c01080041f2080717500492207208082f2f00242f2f00242f2f00244e902039fc07000c4cef0c04000cd0b90000000090af001c23c0000000004fef00204e753009174004902f2f00182f4100104eb900000000588f222f000c6000ff2c222f0018266f0018d7fc0000000075ab04901230181d718132412200b0826700ff0a60be720c4c010800207208082f2f00242f2f00242f2f00244e902039fc07000c4cef0c04000cd0b90000000090af001c23c0000000004fef00204e754fefffdc7225202f002848d7440cb280676c7427b480665a3c7c0001200e76644c030800720141f900000000b2b0080064402239fc07000c4aaf002c6f4475b9000000007001bdc26744340e13c000000000700123c10000000013c20000000013c00000000070014cd7440c4fef00244e754cd7440c42804fef00244e759dce609a75b9000000007002bdc266bc778075b9000000002f43001cb68266ac200190b9000000000c800339000062000178103900000000340e23c10000000076035280738013c200000000b68164924201203940fe422813c1000000004a8067862f004eb94000f2082f400018588f4a806700ff7420402268003c4a896700ff681229001f1429001d1029001e7381244245f2085a200a7180b0816700013491c81229001f1429001d1029001e36087381204241f0085a1f43002220087180b0816700011842001f400023300ec0fc00642440d5fc0000000020122f4a00184a806700ff0441ea0004428175b7e82241e8000cb4a8fff4670000c25281b28066ee7201b2af001c6600fede42815281b0816300fed4760c4c031800206f001845f018071f92e822122f0023142f002240c0260000830000070046c3244141f2285a1342001d1341001e32081341001f46c0246f0014206a002c42a7486a002c206800102f4900184e904eb900000000508fb0af00106600fe7040c2200200800000070046c043f7e82241f900000000d1ce115104902f0e4eb90000000046c27001588f6000fe44360e700123c10000000013c3000000006000fe287401b4af001c6700ff4a4a816700fe1e53816000ff461029001d30406000fec81029001e6000fee60000487800034eb94007faf4588f4a80671c716effda2f002f034eb900000000508f4a80670878004ef94001f96a22572ebc000000022f094ef94007faf4422a007c202a008472074e75156b002600264feffff048d703032f0b2f0a4eb900000000508f4cd703034fef00104e754200114000264feffff048d703032f084eb900000000588f4cd703034fef00104e7500002f0a4eb94005802e588f4ef9400a7d4aa93c00000020a1c0a3c14e75",
    "relocs": [
     [
      58,
      "fx_data",
      0
     ],
     [
      88,
      "fx_data",
      0
     ],
     [
      126,
      "fx_data",
      208
     ],
     [
      168,
      "fx_data",
      200
     ],
     [
      178,
      "fx_data",
      208
     ],
     [
      294,
      "fx_data",
      200
     ],
     [
      304,
      "fx_data",
      208
     ],
     [
      596,
      "fx_data",
      0
     ],
     [
      602,
      "code",
      320
     ],
     [
      648,
      "fx_data",
      0
     ],
     [
      724,
      "fx_data",
      656
     ],
     [
      734,
      "fx_data",
      656
     ],
     [
      740,
      "fx_data",
      912
     ],
     [
      832,
      "fx_data",
      1180
     ],
     [
      842,
      "fx_data",
      1180
     ],
     [
      868,
      "code",
      32
     ],
     [
      892,
      "fx_data",
      0
     ],
     [
      956,
      "fx_data",
      1180
     ],
     [
      966,
      "fx_data",
      1180
     ],
     [
      1016,
      "fx_data",
      0
     ],
     [
      1040,
      "fx_data",
      1173
     ],
     [
      1054,
      "fx_data",
      1174
     ],
     [
      1062,
      "fx_data",
      1176
     ],
     [
      1068,
      "fx_data",
      1173
     ],
     [
      1074,
      "fx_data",
      1172
     ],
     [
      1108,
      "fx_data",
      1173
     ],
     [
      1122,
      "fx_data",
      1174
     ],
     [
      1138,
      "fx_data",
      1176
     ],
     [
      1154,
      "fx_data",
      1172
     ],
     [
      1162,
      "fx_data",
      1176
     ],
     [
      1174,
      "fx_data",
      1173
     ],
     [
      1192,
      "fx_data",
      1172
     ],
     [
      1316,
      "fx_data",
      0
     ],
     [
      1466,
      "code",
      320
     ],
     [
      1498,
      "fx_data",
      0
     ],
     [
      1512,
      "code",
      32
     ],
     [
      1532,
      "fx_data",
      1176
     ],
     [
      1538,
      "fx_data",
      1173
     ],
     [
      22,
      "code",
      564
     ],
     [
      1614,
      "code",
      976
     ],
     [
      1680,
      "code",
      384
     ],
     [
      1714,
      "code",
      528
     ]
    ],
    "symbols": {
     "fx_delay": [
      "code",
      0
     ],
     "fx_reverb": [
      "code",
      4
     ],
     "fx_keys": [
      "code",
      1588
     ],
     "fx_release": [
      "code",
      1648
     ],
     "fx_load": [
      "code",
      1660
     ],
     "fx_init": [
      "code",
      1696
     ],
     "fx_early": [
      "code",
      1732
     ],
     "fx_late": [
      "code",
      1748
     ]
    },
    "bss": 0
   },
   "slots": {
    "fx.delay": {
     "hook": "0x4005699c",
     "stock": "4eb940057488",
     "symbol": "fx_delay",
     "stock_fn": "0x40057488",
     "descriptors": [
      37,
      38
     ],
     "formatters": [
      "0x4004dfda",
      "0x40045ab8"
     ]
    },
    "fx.reverb": {
     "hook": "0x40056a2c",
     "stock": "4eb9400579c4",
     "symbol": "fx_reverb",
     "stock_fn": "0x400579c4",
     "descriptors": [
      39,
      40
     ],
     "formatters": [
      "0x40045a68",
      "0x4004e00e"
     ]
    }
   },
   "track": {
    "hook": "0x4001f886",
    "stock": "487800024e94",
    "symbol": "fx_keys"
   },
   "release": {
    "hook": "0x40020dca",
    "stock": "202a00847207",
    "symbol": "fx_release"
   },
   "load": {
    "hook": "0x4005b4b0",
    "stock": "156b00260026",
    "symbol": "fx_load"
   },
   "init": {
    "hook": "0x4006155e",
    "stock": "420011400026",
    "symbol": "fx_init"
   },
   "early": {
    "hook": "0x4005981e",
    "stock": "4eb9400a7d4a",
    "symbol": "fx_early"
   },
   "late": {
    "hook": "0x400567d8",
    "stock": "4eb94005802e",
    "symbol": "fx_late"
   },
   "formatter_sites": {
    "0x4004dfda": [
     "0x400de32a",
     "203c4004dfda"
    ],
    "0x40045ab8": [
     "0x400de762",
     "203c40045ab8"
    ],
    "0x40045a68": [
     "0x400de732",
     "41f940045a68"
    ],
    "0x4004e00e": [
     "0x400de396",
     "41f94004e00e"
    ]
   },
   "int_format": "0x400456c8",
   "cost": {
    "emulation": {
     "stock": {
      "fx.delay": {
       "first": 2659,
       "max": 2659,
       "mean": 2659
      },
      "fx.reverb": {
       "first": 8205,
       "max": 8205,
       "mean": 8205
      }
     },
     "overhead": {
      "fx.delay": {
       "effect": 93,
       "silence": 2659,
       "stock": 87,
       "switch": 206
      },
      "fx.reverb": {
       "effect": 92,
       "silence": 8205,
       "stock": 86,
       "switch": 204
      }
     },
     "pattern": "notes/68 §17: instructions per block on the OS 1.13 in tools/emu/test_fxslot.py section 6 (mcengine.py's counter), noise of +-2^28 into both channels, Time 0 and Fdbk 96 for the delay, Size 64 and Tone 96 for the reverb (x 256): stock, the stock effect, the first block, then the mean and maximum over 21 blocks after 32 more; overhead, what the slot adds at most, with the stock choice (stock) and with an effect (effect), in the block of a switch besides the effect's first block, its reset and the stock effect's block of silence (switch), and that block of silence (silence)"
    }
   },
   "claims": {
    "saved": [
     [
      "pattern, header +29",
      3,
      "all"
     ]
    ],
    "gestures": [
     {
      "combo": "PATTERN + REVERB-SIZE/DELAY-TIME",
      "atoms": [
       [
        "PATTERN",
        "DELAY-TIME"
       ],
       [
        "PATTERN",
        "REVERB-SIZE"
       ]
      ],
      "situation": "params",
      "scope": "all",
      "meaning": "the shown pattern's effect in the reverb or delay slot",
      "replaces": "the knob's edit while PATTERN is held; the pattern selection is disarmed as in the stock OS, and since 0.6 it no longer waits after PATTERN is released"
     }
    ]
   }
  },
  "fltslot": {
   "id": "fltslot",
   "version": "0.12",
   "roots": [
    "fl_post",
    "fl_run",
    "fl_boot",
    "fl_knob",
    "fl_keys",
    "fl_fmt_cut",
    "fl_fmt_type",
    "fl_save2",
    "fl_save1",
    "fl_load",
    "fl_lfo",
    "fl_measure"
   ],
   "patch_points": [
    {
     "symbol": "fl_data",
     "kind": "fl_data"
    }
   ],
   "data": {
    "entries": 9,
    "size": 1144,
    "start": 1060,
    "nvals": 1132,
    "na": 1041,
    "lfo_keep": 1042,
    "count": 0,
    "params": 4,
    "knob_next": 8,
    "keys_next": 12,
    "desc": 16,
    "entry": 24,
    "entry_size": 64,
    "rows": 600,
    "cur": 880,
    "acc": 886,
    "old": 892,
    "neutral": 1020,
    "rec_next": 1028,
    "diag": 1040,
    "sum": 1044,
    "peak": 1048,
    "n": 1052,
    "avg_t": 1054,
    "peak_t": 1056
   },
   "bundle": {
    "code": "2f2f00082f2f00084eb940056f58508fa9802f002f2b00102f0a4eb900000000508f221f4a80671aa901a13c00000000a33c00000000a53c00000000a73c000000004e754fefffd048d77cfc2039fc07000c2c3c80001858286f003495ca2c6f003842852f40002c283c0000000049ec004647f9000000004bf90000000020050680e00005fbe588224020514a88670001ca1028005577804a006700015622157001b081640001c841f900000000700141e80040b6a8ffc0670001565280b28066ee75b358004a82670000aa4280120045f9000000002600204a22461781580020d9b1c466fa4a82660000c64a836746ed8b207538204a8867062f054e90588fa93c000000a0a13c00000000a33c00000000a53c00000000a73c000000007201200ec0812f002f052075381c2f0c2f064e904fef0010204642817e1f261aec832010ec809e8152814c0738004c010800d083d08020c07020b08166de4a826710ed8a207528204a8867062f054e90588f347c0001220ee289528506860000008049ec00422c410c8680001b586600fef02439fc07000c94af002c2f024eb900000000200a4cef7cfc00044fef00344e75a93c000000a0a13c00000000a33c00000000a53c00000000a73c000000007201200ec0812f002002ed882f052075081c2f0c4879000000004e904fef00106000fefc75b358004a826700ff7a420145f900000000204a2246178158006000fed275b35800b4806600feb6a93c000000a0a13c00000000a33c00000000a53c00000000a73c000000007401220ec282ed88347c00012f012f052075081c2f0c2f064e904fef00106000ff1c3005207c800015efc0fc0042103008006000fe2a75b358004a826700fefe420145f9000000004283204a2246178158006000fe54598f2f027005222f000cb081653a2f4100044eb9400cf866222f00044a80672874444c0218000681000000d4d081204022504a896712226900284a89670a2f40000c241f588f4ed1241f4280588f4e752f0a2f024ab9000000006760202f000c227c40a717d872384282ed882040d1fc0000000024415282d5f90000000041e8000c2568fff4002c2568fff800342441068100000038d5f9000000002568fff4002c2568fff8003422a8fffc42a9000c43e90064b4b90000000065b8241f245f4e754eb9400cf8664a8067542f004eb94000eb902f004eb940012412508f2f004eb900000000588f4a80672c204071a800554a8067242279000000007201b289641641f90000000041e80040b0a8ffc0670a5281b28966f042804e7520014e7570ff60ba4feffff448d7001c4a390000000067084a3900000000674a4eb9000000004a390000000067044a806624ed8843f900000000206f00182231082492881030180010c066f84cd7001c4fef000c4e75206f001820bc2d2d2d004cd7001c4fef000c4e7571f9000000007263b280645c0c80000003e7623e2200760a4c43100174644c4200002801740a4c424003206f001806800000003010804200220306810000003011410001114000024cd7001c4fef000c4e757039206f0018723910804200114100011140000260e0740a4c4200014c420000762e4202206f001806800000003006810000003010801141000211430001114200034cd7001c4fef000c4e752f032f02222f000c2001d0b90000000023c000000000b2b900000000630623c100000000323900000000528175c133c1000000000c82000002ed634c263c000002ee4c4300004243243c000003e822390000000042b90000000042b9000000004c0218004c020800243c0001600033c3000000004c4210014c42000033c10000000033c000000000241f261f4e752f0b2f0a47f90000000095ca42817004b0816714b2b900000000650c528145ea00387004b08166ec206b001043f90000000093c841f0a838200806800000003820f18800b08866f852817005b081670645ea003860b8588bb7fc0000000066aa245f265f4e754feffff42f022f2f00202f2f00202079000000002f2f00202f2f00204e902f40001c70024fef0010b0af00186750222f001874035981b4816538487800042f4100084eb94007faf4588f222f00044a80672041f90000000073b018004aaf00206d0000ccb2b900000000640652812f41000c202f000c241f4fef000c4e75487800044eb94007faf4588f4a8067e47001b0b90000000064da487800014eb94007faf4588f4a8066ca487800024eb94007faf4588f4a8066ba487800084eb94007faf4588f4a8066aa4eb9400cf9a82f004eb94006b736588f4a006696420120390000000020790000000013c10000000072052140014420790000000021400144207c40a717c823d040a71958203c0000000023c040a7196842b940a719742f41000c202f000c241f4fef000c4e752f4100044eb9000000002f002f40000c4eb90000000041f900000000202f000cd1c075a8046c588f222f0004b4816200ff0e4a806750ed88720141f9000000002030082413c10000000020790000000072052140014420790000000021400144207c40a717c823d040a71958203c0000000023c040a7196842b940a719742f41000c6000ff70720120390000000013c10000000060b44200518f222f000c558113c0000000007003b0816516487800042f4100044eb94007faf4588f22174a806608202f0010508f4e7541f900000000123018001f4100074eb9000000002f002f4000044eb90000000073af000b202f00040680000000002040588f71a8046cb081630c102f000752807180508f4e75700113c000000000202f001060a84feffff448d7001c206f00184a39000000006654222f00140681ffffc0002001e0804a816d347809b8806c102200740a4c42180106810000003010c1780a4c44080142000681000000301081114000014cd7001c4fef000c4e7510fc002d44807809b8806cd660c471f9000000007263b28064420c80000003e7626c2200740a4c42100178644c4400002601780a4c44300242030680000000301080220206810000003011410001114300024cd7001c4fef000c4e75740a4c4200014c420000762e420406800000003006810000003010801141000211430001114400034cd7001c4fef000c4e757239703942031141000110801143000260b24fefffdc48d70c042239fc07000c4aaf00286f0001aa70014a3900000000662675b900000000204275802f42000cb488671e13c000000000700123c10000000013c0000000004cd70c044fef00244e75200190b9000000000c800339000062d810390000000023c100000000740352807380b48164ca420013c0000000004eb9400cf8664a80670002182f004eb94000eb902f004eb940012412508f2f004eb900000000588f24404a80679a71aa00554a806700011041f900000000720122502f480010b2896400ff7e41f900000000720141e80040b0a8ffc0670001225281b3c166ee7201b2af000c6600ff5a720142802f410014222f0014206f0010ed8943f0181b155100554ab9000000006700009a75ef001647ea004c2f4b0010223c800015e642af0018e78a2042d1fc000000002f480020206f0020343018003f42000e4a806600013441f90000000075f01800224275ef000e2042b489670000de2408e08a206f00102241266f0010116f000f000116822f42001c207c800017ecb5d0670000b0588843e90042b1fc8000180466ec52af0018226f0018548154af0010b3f900000000658c4cd70c042f6f001400284fef00244ef90000000070026000fe567401b4af000c6600fe7a41f900000000720122502f4800102f410014b3ef00146300fe60222f0014ed89206f001043f0181b155100556000ff0c7401b4af000c670000a02641538b200bed88206f00102f4b001443f0081b155100554a8b678620014ab9000000006600fee46000ff7832af000e6000ff4c52af0018242f0018b4b9000000006400ff5e206f0020548154af00103430180041f9000000003f42000e75f01800224275ef000e2042b4896600feea60c220422408206f0010e08a266f00102241116f000f000116822f42001c207c800017ec6000fee270ff6000fdf8240152822f4200142001b3ef00146200ff326000fd8c4fefffe8428048d70c3c246f001c226f002047f90000000041ea005443e9004c362a00407ba9ffd02829000c0283000003ffb0b900000000647034330a003211548852805489b5812401e08a1141ffff72041142fffeb28066d820390000000022050681ffffffe4b0816312720a0685ffffffe5e3ad424186853541002422040681ffffffe4b28064120684ffffffe5700de1ac420186841541005e354300404cd70c3c4fef00184e75420142025488528054891141ffff72041142fffeb2806600ff7060944fefffec700a48d7043c246f00182a0a43f90000000006850000005441ea004c382a005475c42602e0ab700de0aa7007c680301032195488b3802200e0891140ffff1141fffeb1c566e84a836708b6b90000000063344a82671cb4b9000000006214424006820000001b1542005b354000581540005a0284000003ff354400544cd7043c4fef00144e75420006830000001b1543001c1540001d60ba00004eb9000000004ef94005a2747005b0836616716effda2f004eb900000000588f78004ef94001f96a203900000000670420404ed022572ebc000000022f094ef94007faf42f082f302c002f024eb900000000508f2400205f4a390000000066044a884e75588f4a88670a2f084eb9400802ec588f4ef94001eccc000020790000000060062079000000002f2f00082f2f0008487a00184ed02079000000002f2f00082f2f0008487a00204ed04a0067142f002f2f00082f2f00084eb900000000508f201f508f4e754a0067142f002f2f00082f2f00084eb900000000508f201f508f4e7502030001",
    "relocs": [
     [
      740,
      "fl_data",
      4
     ],
     [
      766,
      "fl_data",
      40
     ],
     [
      776,
      "fl_data",
      16
     ],
     [
      806,
      "fl_data",
      20
     ],
     [
      836,
      "fl_data",
      4
     ],
     [
      880,
      "code",
      654
     ],
     [
      902,
      "fl_data",
      0
     ],
     [
      914,
      "fl_data",
      88
     ],
     [
      956,
      "fl_data",
      1040
     ],
     [
      964,
      "fl_data",
      1041
     ],
     [
      972,
      "code",
      848
     ],
     [
      978,
      "fl_data",
      1041
     ],
     [
      992,
      "fl_data",
      0
     ],
     [
      1046,
      "fl_data",
      1056
     ],
     [
      1214,
      "fl_data",
      1044
     ],
     [
      1220,
      "fl_data",
      1044
     ],
     [
      1226,
      "fl_data",
      1048
     ],
     [
      1234,
      "fl_data",
      1048
     ],
     [
      1240,
      "fl_data",
      1052
     ],
     [
      1250,
      "fl_data",
      1052
     ],
     [
      1282,
      "fl_data",
      1048
     ],
     [
      1288,
      "fl_data",
      1048
     ],
     [
      1294,
      "fl_data",
      1044
     ],
     [
      1314,
      "fl_data",
      1052
     ],
     [
      1328,
      "fl_data",
      1056
     ],
     [
      1334,
      "fl_data",
      1054
     ],
     [
      106,
      "fl_data",
      1020
     ],
     [
      116,
      "fl_data",
      880
     ],
     [
      122,
      "fl_data",
      0
     ],
     [
      170,
      "fl_data",
      88
     ],
     [
      210,
      "fl_data",
      892
     ],
     [
      414,
      "code",
      1202
     ],
     [
      484,
      "fl_data",
      892
     ],
     [
      512,
      "fl_data",
      892
     ],
     [
      636,
      "fl_data",
      892
     ],
     [
      1350,
      "fl_data",
      0
     ],
     [
      1366,
      "fl_data",
      4
     ],
     [
      1390,
      "fl_data",
      544
     ],
     [
      1434,
      "fl_data",
      8
     ],
     [
      1462,
      "fl_data",
      8
     ],
     [
      1530,
      "code",
      3568
     ],
     [
      1548,
      "fl_data",
      4
     ],
     [
      1592,
      "fl_data",
      0
     ],
     [
      1670,
      "fl_data",
      868
     ],
     [
      1676,
      "fl_data",
      16
     ],
     [
      1682,
      "fl_data",
      1041
     ],
     [
      1694,
      "fl_data",
      20
     ],
     [
      1716,
      "code",
      946
     ],
     [
      1754,
      "code",
      848
     ],
     [
      1766,
      "code",
      734
     ],
     [
      1772,
      "fl_data",
      0
     ],
     [
      1808,
      "fl_data",
      0
     ],
     [
      1818,
      "fl_data",
      1041
     ],
     [
      1824,
      "fl_data",
      16
     ],
     [
      1836,
      "fl_data",
      20
     ],
     [
      1858,
      "code",
      946
     ],
     [
      1886,
      "fl_data",
      868
     ],
     [
      1892,
      "fl_data",
      1041
     ],
     [
      1910,
      "fl_data",
      1042
     ],
     [
      1952,
      "code",
      3568
     ],
     [
      1966,
      "code",
      848
     ],
     [
      1978,
      "code",
      734
     ],
     [
      1992,
      "fl_data",
      0
     ],
     [
      2024,
      "fl_data",
      1042
     ],
     [
      2048,
      "fl_data",
      1040
     ],
     [
      2140,
      "fl_data",
      1054
     ],
     [
      2310,
      "fl_data",
      1041
     ],
     [
      2318,
      "fl_data",
      887
     ],
     [
      2336,
      "fl_data",
      887
     ],
     [
      2344,
      "fl_data",
      888
     ],
     [
      2350,
      "fl_data",
      886
     ],
     [
      2368,
      "fl_data",
      888
     ],
     [
      2382,
      "fl_data",
      886
     ],
     [
      2388,
      "fl_data",
      888
     ],
     [
      2406,
      "fl_data",
      886
     ],
     [
      2444,
      "code",
      654
     ],
     [
      2468,
      "fl_data",
      0
     ],
     [
      2488,
      "fl_data",
      88
     ],
     [
      2550,
      "fl_data",
      4
     ],
     [
      2586,
      "fl_data",
      2147479102
     ],
     [
      2614,
      "fl_data",
      2147479062
     ],
     [
      2704,
      "fl_data",
      4
     ],
     [
      2726,
      "code",
      734
     ],
     [
      2748,
      "fl_data",
      0
     ],
     [
      2836,
      "fl_data",
      4
     ],
     [
      2866,
      "fl_data",
      4
     ],
     [
      2890,
      "fl_data",
      2147479062
     ],
     [
      3004,
      "fl_data",
      1020
     ],
     [
      3036,
      "fl_data",
      4
     ],
     [
      3076,
      "fl_data",
      4
     ],
     [
      3200,
      "fl_data",
      1020
     ],
     [
      3262,
      "fl_data",
      4
     ],
     [
      3274,
      "fl_data",
      4
     ],
     [
      28,
      "code",
      68
     ],
     [
      3342,
      "code",
      1344
     ],
     [
      3366,
      "code",
      2284
     ],
     [
      3382,
      "fl_data",
      12
     ],
     [
      3418,
      "code",
      1898
     ],
     [
      3430,
      "fl_data",
      1042
     ],
     [
      3466,
      "fl_data",
      1028
     ],
     [
      3474,
      "fl_data",
      1032
     ],
     [
      3494,
      "fl_data",
      1036
     ],
     [
      3528,
      "code",
      2984
     ],
     [
      3556,
      "code",
      3182
     ]
    ],
    "symbols": {
     "fl_post": [
      "code",
      0
     ],
     "fl_run": [
      "code",
      68
     ],
     "fl_boot": [
      "code",
      3340
     ],
     "fl_knob": [
      "code",
      1446
     ],
     "fl_keys": [
      "code",
      3352
     ],
     "fl_fmt_cut": [
      "code",
      2034
     ],
     "fl_fmt_type": [
      "code",
      946
     ],
     "fl_save2": [
      "code",
      3464
     ],
     "fl_save1": [
      "code",
      3472
     ],
     "fl_load": [
      "code",
      3492
     ],
     "fl_lfo": [
      "code",
      3408
     ],
     "fl_measure": [
      "code",
      1202
     ]
    },
    "bss": 0
   },
   "post": {
    "hook": "0x40059852",
    "stock": "4eb940056f58",
    "symbol": "fl_post"
   },
   "boot": {
    "hook": "0x4004486c",
    "stock": "4eb94005a274",
    "symbol": "fl_boot"
   },
   "keys": {
    "hook": "0x4001f886",
    "stock": "487800024e94",
    "symbol": "fl_keys"
   },
   "lfo": {
    "hook": "0x4001ead8",
    "stock": "24302c004a88",
    "symbol": "fl_lfo"
   },
   "knob": {
    "vtable": "0x401005a8",
    "stock_ptr": "0x4001e814",
    "symbol": "fl_knob"
   },
   "record": [
    {
     "at": "0x4005afa0",
     "stock": "4feffff448d71c00",
     "symbol": "fl_save2",
     "next": "sc_save2"
    },
    {
     "at": "0x4005b054",
     "stock": "4feffff448d71c00",
     "symbol": "fl_save1",
     "next": "sc_save1"
    },
    {
     "at": "0x4005aecc",
     "stock": "4feffff448d71c00",
     "symbol": "fl_load",
     "next": "sc_load"
    }
   ],
   "values": {
    "descriptors": [
     1,
     2,
     3,
     4
    ],
    "sound_slots": [
     28,
     29,
     30,
     31
    ],
    "knobs": [
     "SWEEP",
     "CONTOUR",
     "COLOR",
     "SHAPE"
    ],
    "defaults": [
     16384,
     0,
     16384,
     16384
    ],
    "cc": [
     "0x004affff",
     "0x0047ffff",
     "0x004bffff",
     "0x004cffff"
    ],
    "nrpn": [
     "0x94",
     "0x95",
     "0x96",
     "0x97"
    ],
    "sort": [
     72,
     73,
     74,
     75
    ],
    "group_name": "0x40129882",
    "flags": "0x600",
    "max": 32512
   },
   "type": {
    "descriptor": 5,
    "long": "Track FX",
    "short": "TYPE",
    "none": "OFF",
    "key": "RETRIG",
    "knob": "PITCH"
   },
   "formats": {
    "int": "0x400456c8",
    "centre": "0x40045bd6",
    "cutoff": "fl_fmt_cut"
   },
   "most": 8,
   "claims": {
    "sound_slots": [
     [
      28,
      "all"
     ],
     [
      29,
      "all"
     ],
     [
      30,
      "all"
     ],
     [
      31,
      "all"
     ]
    ],
    "record_slots": [
     [
      28,
      "all"
     ],
     [
      29,
      "all"
     ],
     [
      30,
      "all"
     ],
     [
      31,
      "all"
     ]
    ],
    "descriptors": [
     [
      1,
      "all"
     ],
     [
      2,
      "all"
     ],
     [
      3,
      "all"
     ],
     [
      4,
      "all"
     ]
    ],
    "midi": {
     "cc": [
      74,
      71,
      75,
      76
     ],
     "nrpn": [
      "1:20",
      "1:21",
      "1:22",
      "1:23"
     ]
    },
    "gestures": [
     {
      "combo": "RETRIG + SWEEP/CONTOUR/COLOR/SHAPE",
      "atoms": [
       [
        "RETRIG",
        "COLOR"
       ],
       [
        "RETRIG",
        "CONTOUR"
       ],
       [
        "RETRIG",
        "SHAPE"
       ],
       [
        "RETRIG",
        "SWEEP"
       ]
      ],
      "situation": "params",
      "scope": "all",
      "meaning": "the track filter's values: Cutoff, Reso, Env depth, AD",
      "replaces": null
     },
     {
      "combo": "RETRIG + PITCH",
      "atoms": [
       [
        "RETRIG",
        "PITCH"
       ]
      ],
      "situation": "params",
      "scope": "all",
      "meaning": "the sound's filter: none or one of the build's",
      "replaces": null
     },
     {
      "combo": "LFO + RETRIG + SWEEP/CONTOUR/COLOR/SHAPE",
      "atoms": [
       [
        "LFO+RETRIG",
        "COLOR"
       ],
       [
        "LFO+RETRIG",
        "CONTOUR"
       ],
       [
        "LFO+RETRIG",
        "SHAPE"
       ],
       [
        "LFO+RETRIG",
        "SWEEP"
       ]
      ],
      "situation": "params",
      "scope": "all",
      "meaning": "the track filter's value becomes the LFO's destination",
      "replaces": null
     }
    ]
   }
  },
  "cpu": {
   "id": "cpu",
   "version": "0.3",
   "roots": [
    "cpu_probe",
    "cpu_block",
    "cpu_cfg"
   ],
   "patch_points": [
    {
     "symbol": "cpu_data",
     "kind": "cpu_data"
    }
   ],
   "data": {
    "size": 228,
    "fl_avg": 0,
    "fx_busy": 4,
    "ret": 8,
    "t0": 12,
    "sum": 16,
    "peak": 20,
    "top": 24,
    "fx_last": 28,
    "n": 32,
    "avg": 34,
    "win_peak": 36,
    "top_t": 38,
    "trackfx": 40,
    "effects": 42,
    "windows": 44,
    "drawn": 46,
    "page": 48,
    "vt": 52
   },
   "bundle": {
    "code": "23df000000002039fc07000c23c0000000004eb94005979e2f002239fc07000c92b9000000002f014eb900000000588f201f2f39000000004e752f032f02202f000c0c80004000006304704048402200d2b90000000023c100000000b0b900000000630623c000000000b0b900000000631e747d4c00280023c000000000263c00002c0020024c43000033c000000000303900000000528077c033c0000000000c83000002ed63000092243c000108004c42100120390000000033c1000000000c80004000006278767d4c030800243c00002c002079000000004c42000033c0000000004a88670633d0000000002079000000004a8867202210200190b900000000263c0001080023c1000000004c43000033c000000000303900000000424142b90000000042b900000000528033c10000000033c000000000241f261f4e7570404840767d243c00002c002079000000004c0308004c42000033c0000000004a88678a608230390000000073f900000000226f0004204173c0b288671033c0000000002f4900044ef9400760824e75518f2f0e2f3c40140ab04def00082f0e4eb9400722602f2f00284879000000002f2f002c206f0024202800080680fffffff790af002c2f002f2f002c2f0e2f084eb940071a044fef00202e8e4eb940072080588f2c5f508f4e754fefffd8202f003c48d7403c4a80660000ba222f0038760a4c431001240f06820000001422427a0a528928014c4540034c4540042043260041e8003052803a081345ffff7a09ba81640a22047606b68066d47605280f06840000001c20422244d1c012e0b1c266fa222f00387a0a4df9000000004c451002722e7a250682000000301f81081c42001f85381f1f82381e1f8038202f2f0034487800102f2f0038487800022f2f003c4e962f04487800142f2f004c4878007d2f2f00504e964cef403c00284fef00504e75303c2d2d4201280f06840000001c4df9000000003f40001c1f41001e2f2f0034487800102f2f0038487800022f2f003c4e962f04487800142f2f004c4878007d2f2f00504e964cef403c00284fef00504e75598f2f02242f00102f6f000c00042f024eb94007240c588f720cb28067142f4200102f6f0004000c241f588f4ef940075f3c2f024eb940072434588f4a8067122f2f0004226f00082051206800284e90588f241f7001588f4e754fefffd448d73cfc246f0034202a000441ea000c4c1008004a806f0e206a001043f00c004298b1c966fa71f90000000042a747f9000000002f00487900000000487800012f0a4e934fef001438390000000071c40c80000003e86304383c03e8c8fc007a243c000003e87002222a0008263c80000000206a00042a012c082a444c424004224424010682fffffff3b08864502a02781fc484ea857c0cbc816400010e222a000c206a00104c001800d2852a03e4ad8bb01c00206a00042c08222a000824012a010682ffffffefb08864127a1f2c02ea86ca82b282620000e82a012c0852807e7ebe80669c740d56897002b086645a200553809082b08564507a1f787dca80ea80206a000c2c3c80000000222a00102840200641f48a002841eaa881b48c00206a0008200853809082b8aa0004641ab08864167a1fca80ea80eaae2a2a000c4c045800d0858db40c00bbfc000003e76300009e7003b0aa00046430206a00082208538192827a1f2c01ea86ca81b288641a222a000c206a00104c001800d2862c3c80000000eaae8db01c005280b3c066c452827010b08267687202b2aa000464b22a2a00086000ff4824017a1f0682ffffffef2c02ea86ca82b2826300ff1c222a000c2403eaaa206a00107e7e4c0018005280d28685b01c00222a00082a01206a00042c08be806600fe986000fef82a2a000852822c2a00047810b8826600feea7a6abaaa000464000092307c000a222a00082001538024007a1f948826085e8328029083ca82ea84b481642c202a000c7c6a223c80000000eaa94c060800226a0010d08483b10c00202a0008220053809083bcaa00046428741f2600ea83c480b280631c202a000c7e6a223c80000000e4a94c070800226a0010d08383b10c00700bb0886714307c000b726ab2aa00046408222a00086000ff7a71f90000000042a72f00487900000000487800162f0a4e934ab90000000057c073f900000000710044802f002f01487900000000487800212f0a4e934fef00284ab90000000057c073f900000000710044802f002f014879000000004878002c2f0a4e934cef3cfc00144fef00404e754e56fff040c120010280000007004a8066084ab90000000067044e5e4e754ab940fe417867f4227c401178e441f90000000093fc0000000020f18800b1fc0000000066f4487800d0203c0000000041f90000000043f90000000023c80000000023c90000000041f90000000043f90000000023c000000000203c0000000023c80000000023c90000000023c000000000203c0000000041f90000000043f90000000023c00000000023c80000000023c9000000002d41fff44eb9400802e0588f2d40fff04a806700ff522f004eb9400a22b0222efff4200100800000070046c0424042b90000000033c00000000046c141f90000000033d000000000226efff0203c0000000022bc00000000234000044878001023c9000000004eb9400802e0226efff02040700120bc401000c421400004214000082149000c2d49fff82d48fffc4eb9400d09742f004eb9400060d842a7486efff82f004eb94007700e486efffc4eb9400cf23c4fef001c4e5e4e754feffff048d703034879000000002f0a4eba0018508f4cd703034fef00104cef7c7c00184ef940032af44e56ffc04feffff048d73810282e000c49f9400800644beeffc0487800014e94588f2a8042ad0004203c4002f1362b400008204420102b40000c487800044e94588f204020ae00082b40001042ad0014203c4002f1882b40001820442028000c2b40001c487800014e94588f2b40002042ad0024203c4002f1362b4000282044202800042b40002c487800044e94588f204020ae00082b40003042ad0034203c4002f1882b4000382044202800082b40003c487800544e94588f2640487800084878ffff486d0030486d0020486d00102f0d2f0b4eb9400734b04fef001c2f0b2f2e00084eb940072ce6508f486d00304eb9400cf044588f486d00204eb9400cf044588f486d00104eb9400cf044588f2f0d4eb9400cf044588f4cd738104e5e4e7543f9000000004e56fffc2f02486effff2f0924082f084eb9400f980c4fef000c2002242efff84e5e4e7570004e754eb90000000070004e7542b9000000004ef9400f43ca42b9000000004ef9400f448659af000460e259af000460e859af00042f2f00084eb94006f6ce588f4a00660a58af00044ef94006fb9070014e750000257300435055005045414b00545241434b2046580045464645435453000000000000000000000000000000000000000043505500",
    "relocs": [
     [
      360,
      "cpu_data",
      44
     ],
     [
      366,
      "cpu_data",
      46
     ],
     [
      384,
      "cpu_data",
      46
     ],
     [
      428,
      "code",
      2476
     ],
     [
      602,
      "code",
      400
     ],
     [
      708,
      "code",
      400
     ],
     [
      908,
      "cpu_data",
      34
     ],
     [
      916,
      "code",
      490
     ],
     [
      924,
      "code",
      2479
     ],
     [
      942,
      "cpu_data",
      34
     ],
     [
      1538,
      "cpu_data",
      38
     ],
     [
      1548,
      "code",
      2483
     ],
     [
      1562,
      "cpu_data",
      0
     ],
     [
      1570,
      "cpu_data",
      40
     ],
     [
      1584,
      "code",
      2488
     ],
     [
      1602,
      "cpu_data",
      4
     ],
     [
      1610,
      "cpu_data",
      42
     ],
     [
      1624,
      "code",
      2497
     ],
     [
      82,
      "cpu_data",
      16
     ],
     [
      88,
      "cpu_data",
      16
     ],
     [
      94,
      "cpu_data",
      20
     ],
     [
      102,
      "cpu_data",
      20
     ],
     [
      108,
      "cpu_data",
      24
     ],
     [
      122,
      "cpu_data",
      24
     ],
     [
      140,
      "cpu_data",
      38
     ],
     [
      146,
      "cpu_data",
      32
     ],
     [
      156,
      "cpu_data",
      32
     ],
     [
      182,
      "cpu_data",
      20
     ],
     [
      188,
      "cpu_data",
      34
     ],
     [
      214,
      "cpu_data",
      0
     ],
     [
      224,
      "cpu_data",
      36
     ],
     [
      234,
      "cpu_data",
      40
     ],
     [
      240,
      "cpu_data",
      4
     ],
     [
      254,
      "cpu_data",
      28
     ],
     [
      266,
      "cpu_data",
      28
     ],
     [
      276,
      "cpu_data",
      42
     ],
     [
      282,
      "cpu_data",
      44
     ],
     [
      290,
      "cpu_data",
      20
     ],
     [
      296,
      "cpu_data",
      16
     ],
     [
      304,
      "cpu_data",
      32
     ],
     [
      310,
      "cpu_data",
      44
     ],
     [
      334,
      "cpu_data",
      0
     ],
     [
      348,
      "cpu_data",
      36
     ],
     [
      1668,
      "cpu_data",
      48
     ],
     [
      1694,
      "cpu_data",
      52
     ],
     [
      1700,
      "cpu_data",
      0
     ],
     [
      1710,
      "cpu_data",
      228
     ],
     [
      1722,
      "code",
      2404
     ],
     [
      1728,
      "code",
      2416
     ],
     [
      1734,
      "code",
      774
     ],
     [
      1740,
      "cpu_data",
      64
     ],
     [
      1746,
      "cpu_data",
      68
     ],
     [
      1752,
      "code",
      358
     ],
     [
      1758,
      "code",
      2444
     ],
     [
      1764,
      "cpu_data",
      60
     ],
     [
      1770,
      "code",
      864
     ],
     [
      1776,
      "cpu_data",
      104
     ],
     [
      1782,
      "cpu_data",
      128
     ],
     [
      1788,
      "cpu_data",
      76
     ],
     [
      1794,
      "code",
      2428
     ],
     [
      1800,
      "code",
      2434
     ],
     [
      1806,
      "code",
      2440
     ],
     [
      1812,
      "cpu_data",
      140
     ],
     [
      1818,
      "cpu_data",
      144
     ],
     [
      1824,
      "cpu_data",
      148
     ],
     [
      1876,
      "cpu_data",
      24
     ],
     [
      1882,
      "cpu_data",
      38
     ],
     [
      1890,
      "cpu_data",
      44
     ],
     [
      1896,
      "cpu_data",
      46
     ],
     [
      1906,
      "cpu_data",
      140
     ],
     [
      1912,
      "cpu_data",
      60
     ],
     [
      1926,
      "cpu_data",
      48
     ],
     [
      2,
      "cpu_data",
      8
     ],
     [
      14,
      "cpu_data",
      12
     ],
     [
      34,
      "cpu_data",
      12
     ],
     [
      42,
      "code",
      58
     ],
     [
      52,
      "cpu_data",
      8
     ],
     [
      2026,
      "code",
      2508
     ],
     [
      2350,
      "code",
      2524
     ],
     [
      2396,
      "code",
      1648
     ],
     [
      2508,
      "code",
      2348
     ],
     [
      2512,
      "code",
      2390
     ],
     [
      2516,
      "code",
      2390
     ],
     [
      2520,
      "code",
      2394
     ],
     [
      2406,
      "cpu_data",
      48
     ],
     [
      2418,
      "cpu_data",
      48
     ]
    ],
    "symbols": {
     "cpu_probe": [
      "code",
      0
     ],
     "cpu_block": [
      "code",
      58
     ],
     "cpu_cfg": [
      "code",
      2016
     ]
    },
    "bss": 0
   },
   "probe": {
    "hook": "0x40059382",
    "stock": "4eb94005979e",
    "symbol": "cpu_probe"
   },
   "row": {
    "jmp": "0x40032aee",
    "stock": "4cef7c7c0018",
    "symbol": "cpu_cfg"
   },
   "order": 78
  },
  "resample": {
   "id": "resample",
   "version": "0.4",
   "roots": [
    "rs_mix",
    "rs_pre",
    "rs_post",
    "rs_key",
    "rs_code",
    "rs_arm",
    "rs_stop",
    "rs_cancel",
    "rs_release",
    "rs_db",
    "rs_header",
    "rs_norm",
    "rs_pcm16"
   ],
   "patch_points": [
    {
     "symbol": "rs_data",
     "kind": "rs_data"
    }
   ],
   "data": {
    "size": 512,
    "buf": 0,
    "cap": 4,
    "ring": 8,
    "shift": 12,
    "state": 16,
    "src": 17,
    "stereo": 18,
    "start": 19,
    "stop": 20,
    "req": 21,
    "end": 22,
    "ring_n": 23,
    "ring_at": 24,
    "thr": 28,
    "sil": 32,
    "cut": 36,
    "limit": 40,
    "frames": 44,
    "peak": 48,
    "quiet": 52,
    "loud": 56,
    "level": 60,
    "page": 64,
    "src_set": 68,
    "start_set": 69,
    "thr_set": 70,
    "stereo_set": 71,
    "stop_set": 72,
    "length_set": 73,
    "norm_set": 74,
    "to_track": 75,
    "settled": 76,
    "drawn": 77,
    "sample": 78,
    "set_held": 79,
    "vt": 80,
    "saving": 256,
    "asked": 257,
    "exists": 258,
    "act": 259,
    "which": 260,
    "grid_set": 261,
    "name": 264,
    "path": 280,
    "fw": 312,
    "pos": 316,
    "total": 320,
    "sh": 324,
    "gain": 328,
    "conv": 332,
    "msg": 336
   },
   "bundle": {
    "code": "700010390000000053807201b08163064ef9400567ba2f2b00102f174879800018584eb900000000508f2f2f000c2f2f000c4eb9400567ba508f2f002f2f000448798000ba9048798000b9904eb9000000004fef000c201f588f4e7571b9000000002f0253804a80671071b90000000055804a806704241f4e7510390000000074057380b48165ee4880242f000ce2aa720171c0c481ef882f0242a7d0af00102f004eb9000000004fef000c241f4e754feffff4222f001c48d7040c262f00184a81674a4aaf0020664442804a83673477c3226f00104280206f0014e78bd6882210e28124280004e2825088d2822401d482958222c1b5819282b28063022001b1c366dc4cd7040c4fef000c4e752003e3a867f073c0206f00144280226f001045f01c0022182401d482958222c1b5819282b28063022001b1ca66e84cd7040c4fef000c4e754fefffdc48d7041c4a3900000000672e71b900000000307c000224790000000053804a80672e71b90000000055804a80670000c04cd7041c4fef00244e7571b900000000307c000124790000000053804a8066d27402b48857c073b900000000227900000000e1892f490020710044802f40001c2f002f2f0030487800202f2f0034487118002f4800244eb9000000001439000000004fef0014720223c000000000206f00107782b2836700018c73b9000000004a026600027e4aaf00306600039e528176094c43100210390000000013c20000000074077380b4816500ff564cd7041c528013c0000000004fef00244e7522390000000076202439000000009481b682650000e47602b68857c026084c031800710044802f002f2f00302f022f2f003448721c004eb9000000004fef00142202d2b90000000023c00000000023c100000000b0b900000000630623c000000000b0b900000000650623c100000000b0b90000000064580c81000009606306d5b9000000004a39000000006650207900000000103900000000b1f9000000006200014a718053804a806700032042017004740313c10000000013c00000000013c2000000004cd7041c4fef00244e7542b9000000004a390000000067b042017003740313c10000000013c00000000013c20000000060ce76027420b68857c026084c031800710044802f002f2f00302f022f2f003448721c004eb9000000004fef00142202d2b90000000023c00000000023c100000000b0b9000000006300ff226000ff184201243900000000538842b900000000762042b90000000042b90000000042b9000000002f48001413c10000000013c100000000b682650001e273b900000000200ae1892f2f001c2f2f00182f02206f002c487018002f004eb9000000004fef00142202d2b90000000023c100000000b0b900000000630623c000000000b0b900000000650623c100000000b0b900000000655042b900000000700213c0000000006000fe9c4a006600fd52243c00002edfb4b9000000006400fd4242017001740341f90000000023d00000000013c10000000013c00000000013c2000000006000fe9e0c810000096063ae7002d5b90000000013c0000000006000fe4453834a836600fd86b0b9000000006500fd7c420379b90000000043e8ffff42b90000000042b90000000042b90000000042b9000000002f49001413c30000000013c3000000004a846700015a2001068000000009740990844c42000324084281e58a2f420018207900000000702024089481b08264027420202f00184c010800d08ab288670000f82203e1892f2f001c2f2f00182f02206f002c487018002f004eb9000000004fef00142202d2b90000000023c100000000b0b900000000630623c000000000b0b900000000650623c100000000b0b9000000006500008e42b9000000002003740952804c42000353844a846600ff72202f0018762024390000000094814c01080073b900000000d08ab6826400fe3074206000fe2a73b90000000074206000fe1c4203243900000000538842b900000000702042b90000000042b90000000042b9000000002f48001413c30000000013c300000000b0826400fde27420200a6000fddc0c81000009606300ff72d5b9000000006000ff6873b9000000006000fdbe42017002740313c10000000013c00000000013c2000000006000fce02439000000007020b08265b2200a6000fd902f02226f00084280242f000c41f90000000058882228fffce4a9b3c1640e52807220b28066ec241f70604e75c0fc0003241f4e7571b9000000002f02206f0008226f000c222f001053804a80670c71b90000000055804a80661271b9000000007406b48067205f804a806704241f4e75740142af00102f42000c2f490008241f4ef900000000703f7401c2802f42000c2f4800084a8156c1730144812f410010241f4ef90000000073b900000000518f2f032f02202f001453814a816700011673b90000000055814a81670001087207b2806500010022007405b4806302720541f900000000760573b0180713c0000000002241b680650000e44200420113c0000000001f41000f122f001f202f0024760313c10000000041ef002372204c43000013d000000000b2806402702041f90000000020300c002409e4a8223c00010945e4a92f40000a203c00083b20e4a8262f000a23c100000000204020390000000023c30000000023c8000000004a2f000f6702e2882200243c0000bb804c421001b2af00286508202f00284c02080042014242420323c00000000042b90000000042b90000000042b90000000042b90000000042b90000000013c100000000720133c20000000013c30000000013c100000000241f261f508f4e754aaf001856c15f8044811f41000f13c1000000004a806600ff144aaf001c6600ff0c72016000ff0a71b90000000053804a80671871b90000000055804a8067024e75700113c0000000004e75420013c0000000004e75420013c0000000004e7571b90000000057804a8067024e75420013c0000000004e752f02226f0008200920490680000000404218b08866fa4aaf0010673a72014aaf000c56c0307c0004240813410001727f710013410014222f000cd081234000104c01280023420004243c0000bb8023420008241f4e7542014aaf000c56c0307c0002240813410001727f710013410014222f000cd081234000104c01280023420004243c0000bb8023420008241f4e752f032f02242f000c4a8267340c82000100006540428052802202e0a90c810001000064f2243c3dd380004c412002206f00102080206f00142082241f261f4e75206f0010701f2080206f00142082241f261f4e752202243c3dd380004c412002428060ca4fefffe848d7047c246f00242a2f0028282f002c4a8a676a226f00204283206f001c45f1ac002219eaa14a8467084c041800700fe0a150c0747f0c8100007fff6e2e2c01e08e420074800c81ffff80006d1e1406100154881142fffe1140ffffb5c966c220034cd7047c4fef00184e75548852831142fffe1140ffffb5c966a660e2428320034cd7047c4fef00184e754fefffe048d7403c202f00287a0a2400260f4c4520014c4520020683000000162043280f2c6f002406840000002043e8000106810000003010817209b28064262002b889672024007a0a4c4520014c452002204943e8000106810000003010817209b28065da202e0028528843f608007a26ba806d0c52802d40002812e0b68866ee42011d8108004cd7403c4fef00204e751039000000004feffff42f027403226f001473802041b48167222200538173817401b481651e2f490014241f13c0000000004fef000c4ef9400760824a3900000000671a4a390000000066da73b900000000b1c166d0241f4fef000c4e754a390000000066c072012f40000c2f4800042f49000813c1000000004eb900000000202f000c206f0004226f000860b64200598f13c0000000004eb9400cf9a820404a28016567244a280166671e42a72f002f4000084eb94006ba90206f00082f084eb94006ba204fef000c588f4e75598f2f032f02242f00142f6f001000082f024eb94007240c588f720cb280673e7609b68066224a390000000066102f024eb9400724a0588f4a0066000090241f7001261f588f4e752f4200142f6f00080010241f261f588f4ef940075f3c4a390000000066d82f024eb940072434588f4a8067ca71b90000000055804a80670000a271b9000000007402b480670000cc7603b680670000ba53804a8066064eb9000000004a390000000067064eb900000000226f000820512f09206800284e90588f241f7001261f588f4e754878000d4eb94007faf4588f4a8066984a3900000000669012390000000074027181b480673065424a01676c4eb9000000004a390000000067064eb9000000002f2f00084eb940076082588f241f7001261f588f4e754eb9000000002f2f00084eb940076082588f60e257804a8066d04eb9000000002f2f00084eb940076082588f60c84eb9000000006000ff4c4eb9000000006000ff424240760733c0000000004eb9400cf9a873b90000000020412400123900000000b688670000d64a016600009422404a29016567084a2901666600008442a72f024eb94006ba902f024eb94006ba204fef000c20421028016567084a28016656c0448073b90000000075b90000000013c00000000071b90000000020417607224212390000000075b900000000b688674673812f0071b9000000002f092f022f012f002f084eb9000000004fef00182f2f00084eb940076082588f6000fef875b90000000071b9000000007381224275b90000000060bc4a0166b62f00720171b9000000002f092f022f012f002f084eb9000000004fef001860b44a0166c071b90000000073b90000000075b9000000002f002241720171b9000000002f092f022f012f002f084eb9000000004fef00186000ff7c4fefffa848d77cfc206f006c226f005c2a6f0070286f0074121067000122206f0060340d102800011f400053102800024880c5c0712f00532f4200542400e58a908206800000000c2f40004a7041730142af004691c87100b081670001a4528845f9000000001032880066ea702b2f4000464a2f00536f0000ac7018720c2f4000422f410036302f0048206f00601f500052266f0068d7cdc0fc00072040d1fc00000000712f00522f48003e2f40004e7203206f006071280003b2806700010259804a806700011a206f003e71902f40002e4a2f00526f34200b908d41ebffff2f4000322c6f004e538e2a2f006426052f48003ad68d202f002e220e03006648538ed68dda8d70ffb08e66ea222f004ad7cd57af003659af004252af003eb2af0036668c206f006c5288202f005412102f48006cd1af00644a016600ff104cd77cfc4fef00584e75242f003ab4af00326dae24432005282f0032538ab5c56d4ab0a90004643e20690008220853819284741f2c01ea86c481b28864282229000c206900104c001800d28641f01c002c3c80000000e4ae2406468222104a8c671a828620815280b08366b65284b7c46700ff502005b5c56ca860f0c282208160e4246f0046740741f900000000222f003671f0aa00e2a0c4802f42002e6000fef4246f0046740f41f900000000222f00422030ac00e2a8c4802f42002e6000fed42f4800466000fe6c4fefffdc48d71cfc262f00302e2f0038226f0028286f002c246f0034282f003cbe836d5e2647240a528b5282200cb5cc6d4ab0a90004643e206900082208538192837e1f2c01ea86ce81b28864282229000c206900104c001800d28641f01c002c3c80000000eeae2e06468722104a84671a828620815280b48066b65283b68b66aa4cd71cfc4fef00244e75c287208160e44fefffec428048d7041c206f0018246f0020b0a80004643a2268000822090681ffffffce2401781fc284ea827831b88964202828000c4c0048002244d3c22409e58a2242243c80000000e2aad3e80010859154800c800000008066b64aaf001c672e48780001487800012f2f002448780036487800024879000000002f082f48002c4eb9000000004fef001c206f00104a8a67364a12673c428052804a32080066f8e58848780001727f487800012f0a4878003692802f014879000000002f084eb9000000004fef001c4cd7041c4fef00144e7548780001727f487800012f0a487800362f014879000000002f084eb9000000004fef001c60d04fefffec48d70c0c4878000148780001487900000000487800014878000248790000000041f900000000246f0030266f00342f0a4e904fef001c4a8b674c4a13670000f6428052804a33080066f8e588727f2040928053884aaf002066000082262f0020700141f900000000b1832f03487800012f0b487800022f014879000000002f0a4e904fef001c4280b0aa0004643a206a000822080681fffffff52401761fc283ea82760ab6886420262a000c4c0038002043d1c22408e58a2042243c80000000e2aad1ea0010859054800c800000008066b64cd70c0c4fef00144e7548780001707c487800074878007f4878000190882f002f0a2f4100284eb9000000004fef00187001262f0020222f001041f900000000b1832f03487800012f0b487800022f014879000000002f0a4e904fef001c6000ff54307cffff727f4aaf00206700ff1c60984fefffe848d7041c243c000012c0222f002020014c420000740a246f001c28004c4240040c81000752ff62722f0478262f0a41f9000000002f40001c2f4800184e90508f222a00282241202f0014206f0010b8816d0c742e52892549002815821800760a4c4300014204158498002f012f0a4e90508f7226202a0028b2806d2c74534203220052812541002815820800158318004cd7041c4fef00184e752f042f0a4eb900000000508f60ca42032200158318004cd7041c4fef00184e75123900000000598f2f0a2f02206f0010202800284a01670000b6738153814a81667a4aaf0014670000d8724f43f90000000045f0080052897426b4806d0c52802140002814c1121166ec4201243c0000bb80118108002039000000004c4200002f002f082f4800104eb900000000206f00107226508f20280028b2806d0000927453220052812141002811820800420011801800241f245f588f4e7543f90000000022007426b4806de42200528121410028119908002001b3fc0000000066e2420011801800241f245f588f4e7543f90000000022007426b4806db22200528121410028119908002001b3fc0000000066e2420011801800241f245f588f4e75725343f90000000045f008006000ff282200420011801800241f245f588f4e754e56fe2c223c0000000048d71c7c240e0682fffffe742042263c000000002d41fe58203c000000002d43fe5c2a3c000000002d40fe542c3c0000000045f9000000002d45fe607a0742aefe9c429842984298429842984298429842984298429041f9000000002d46fe642d48fe682d4afe6c123900000000103900000000282e000877812243ba83670003fc7180260e0683fffffea020432d40fe4c421042a8002841e8002cb1ce66f27007c28041f900000000266efec820701c001210670004a6420545eefea0d5cb200b52887c26bc806d00048c14c112107a0152804a0166ea2d40fec84201246efe4c41f9000000002070ac0045f60800266efef41541fea012106700046c49eefecc45f4b8004205200b52887c26bc806d00045014c112107a0152804a0166ea420141f608002d40fef47001266eff201141feccb0aefe4c6700044849eefef845f4b80042012a0b200b41f90000000056857c26bc806d0004ac14d872015280ba8066ee420141f6080045f9000000002d40ff202d4afe4c1141fef87005b089640002ac724f246eff4c4a390000000067000304420541f900000000200a43eeff2352887c26bc806d0003281381080112107a0152804a0166e82d40ff4c420141f608007a11246eff781141ff2441f90000000071b9000000003200c2fcaaabeaa9c3fc00039081718020700c001210670002da4205200a43eeff4f52887c26bc806d0002c21381080112107a0152804a0166e82d40ff78420141f60800246efe4c1141ff5071b9000000002f00486eff7c4e92508f202effa47226b2806d0003f87a5341f60800220052812d41ffa41145ff7c420041f618001140ff7c4a3900000000670002024205724f226effd0200941f90000000052887c26bc806d00025e1d8108a812107a0152804a0166e82d40ffd042011d8108a871b9000000002479800017e40c80000000ff673a4a8a67364eb9400cf8667a062f004eb94000eb902f004eb940012412508f22004c45100673b9000000002006c0fc006471b20842b280670001c2722d4205226efffc200941f90000000052887c26bc806d0001ea1d8108d412107a0152804a0166e842012a3c544f20547c042d45fe747a062d40fffc2d46fe9c47f9000000001d8108d44eb9400cf8662f004eb94000eb902f004eb940012412246efe4c4c4500012041486800012f024e9242a742a72f042d42fe704eb900000000428245eefe544fef001c7003c082eb8852802d40fe4c7003b0826c5e487800014878000152822f124878001f588a2f2efe4c4879000000002f044e9348780001487800012f03487800262f2efe4c4879000000002f044e934fef00387208b282677a700306830000002cc082eb8852802d40fe4c7003b0826da2201a528248780001487800012f004878000d2f2efe4c4879000000002f044e9348780001487800012f034878001406830000002c2f2efe4c4879000000002f044e934fef00386000ff48246eff4c200a722d420541f90000000043eeff236000fd5e4879000000004879000000002f044eb9000000004fef000c4cee1c7cfe2c4e5e4e75226effd020094205724f41f9000000006000fdfe4a006600fc027c01260e0683fffffea02d46fe4c20436000fbfe420541f900000000200a43eeff236000fcfc4a390000000066000174226efffc2009724e420541f9000000006000fe344a056600fd4a200a6000fd484a056600fce4200a6000fce24a056600fdae20096000fdac4a056600fe22420120092a3c544f20547c042d45fe747a062d46fe9c47f9000000001d8108d44eb9400cf8662f004eb94000eb902f004eb940012412246efe4c4c4500012041486800012f024e9242a742a72f042d42fe704eb900000000428245eefe544fef001c6000fe204a056600fb7e200b6000fb7c4a056600fbba4201200b41f608007001266eff201141feccb0aefe4c6600fbbc7226200bb28b6d0e7a2dd7ce52802d40ff201745fef8420641f6080045f9000000002d4afe4c1146fef871b9000000002f00486efef82d49fe504e92508f202eff207226226efe50b2806d287a442200528141f608007c272d41ff201145fef8bc8167587a4241f6180054802d40ff201145fef8420141f608001141fef86000fb7a4a016600fb5c4201200b41f6080045f9000000002d4afe4c1141fef86000fb5a226efffc20097259420541f9000000006000fcc222006000fc184201702741f608001141fef86000fb304fefffe448d71c3c266f0024260b246f00205c83242f002c4aaf00286600026c487800012f0b4878007c2f0b487800032f0a49f9000000004e94487800012f034878007c2f03487800032f0a4e944fef0030487800012f03487800032f0b487800032f0a4e94487800012f034878007c2f0b4878007c2f0a4e944fef003070ffb08266124aaf00306600018a4cd71c3c4fef001c4e75723cb2826402743c203cffffff127a784c020800262a00042403222a000822410680000038044c45000020405888b1c3640000dc2001908b5280b081640002922400761fc08343ea000cea8222084c111800226a0010d282243c80000000e0aa85b11c00262a00042403222a000820012241908bb1c364000096280b5e84b2806300025c721fc28043ea000c260824004c113800ea82226a00102003d082243c80000000e2aa85b10c00262a00042403222a00082001538022419084b1c3644e280b5084b081640002262400761fc08343ea000cea8222084c111800226a0010d282243c80000000e0aa85b11c00262a00042403222a00082001538022419084b1c3640ab081650001f2224124037821b88b57c0220b528144804a00670001a67627200953809081b4886340741f2800ea84c480b3c0633443ea000c20084c110800226a0010d08443f10c00283c80000000e4ac28442404200c46822811c084c4844a806604240c848422825281b6816700fe7c226a0008242a000460a4487800014878000148790000000047eb000a2f0b487800034879000000002f0a49f9000000004e9448780001487800014879000000002f0b4878003a4879000000002f0a4e944fef003848780001487800014879000000002f0b487800724879000000002f0a4e944fef001c4cd71c3c4fef001c4e7571b9000000007205b280620000ca41f90000000071b0080749f9000000002f002f2f002c4eb900000000487800012f0b4878007c2f0b4878000328002f0a4e944fef0020487800012f034878007c2f03487800032f0a4e94487800012f03487800032f0b487800032f0a4e944fef0030487800012f03763b4878007c2f0b4878007c2f0a4e944fef0018b6846500fd66203cffffff124c040800787848780001486b00050680000038044c440000204048680004486b0001487800042f0a4e944fef001870ffb0826700fd306000fd3e76296000fe5a70056000ff342001280b908b5e84b2806200fda8200153809084280b5084b0816500fdde200153809084b0816400fe122400761f43ea000cea82c08322084c111800226a0010d282243c80000000e0aa85b11c00226a0008242a00046000fde64fefff8448d7443c2c6f0084202e000441ee000c4c1008004a806f0e206e001043f00c004298b1c966fa71b9000000007202b280670004607403b480670001cc53804a8067122f4e00804cd7443c4fef007c4ef90000000042af005042a7487900000000260f06830000005842af005c42af006042af006442af006842af006c42af007042af007442af007842af007c42af00802f0e4eb9000000004fef000c71b90000000053804a806700075441f900000000428052804a30080066f87a064c050800223c0000008148780001487800012f084878000f45f900000000928022016a025281e2812f014879000000002f0e4e924fef001c103900000000720741f900000000c08122700c0042801211671e20434280108152801231080052884a016700076e7427b48066ea2f42007842041f8408504a390000000067000732420474202243220041f900000000d3c052887a27ba816700072c12c21410780152814a0266ea2f41007842001f80185042a72f034eb900000000508f4a2f00506700084420434280528852804a1866fae588223c00000081928022016a025281e28148780001487800012f034878001a2f014879000000002f0e4e924fef001c71b90000000053804a80670006ce4878000170ff2f002f3900000000487800212f0e4eb9000000004879000000004879000000002f0e4eb9000000004fef00204cd7443c4fef007c4e754a3900000000670004a0243900000000260f42af005006830000005042af005442af005842af005c42af006042af006442af006842af006c42af007042af007442af00784a8266027401283900000000b4846402280242a74879000000002f0e4eb9000000004fef000c4a39000000006700076441f9000000001010220852884a0066f670060481000000004c001800203c00000081908120006a025280e28048780001487800014879000000004878000f2f004879000000002f0e45f9000000004e9248780001487800014879000000004878001a4878002a4879000000002f0e4e924fef003848780001487800214878007c48780021487800032f0e4eb90000000048780001487800274878007c48780027487800032f0e4eb9000000004fef003048780001487800274878000348780021487800032f0e4eb90000000048780001487800274878007c487800214878007c2f0e4eb9000000004fef003048780001487800262002223c000000eed0804c041800d48122024c40100120414868000448780022487800042f0e2f4000304eb90000000072264c014800202f003094844c4020022f0274262f034eb900000000202f009822004fef0020b4806d0c782552812f4100781f84085042051f8518504a2f00506700063a41ef0051428052804a1866fae588223c0000008148780001487800012f034878002a928022016a025281e2812f014879000000002f0e4e924fef001c4280b0ae00046434206e000822080681ffffffce2601741fc282ea837a31ba88641a242e000c206e00104c002800d483263c80000000e2ab87b02c0054800c800000008066bc4878000148780001487900000000487800364878001e4879000000002f0e4e924fef001c4cd7443c4fef007c4e75243900000000260f45ef002406830000005042af00502f42001c42af002842af002c42af003042af003442af003842af003c42af004042af004442af004842af004c42af005442af005842af005c42af006042af006442af006842af006c42af007042af007442af007842924a8267000196243900000000b4af001c62000180487800014879000000002f0e4eb9000000002f39000000002f0a4eb9000000004fef00144a2f00246700040641ef0025428052804a1866fa7a064c050800223c0000008248780001487800022f0a4878000d45f900000000d0809280e2812f014879000000002f0e4e92487800012f034eb9000000004fef00242039000000004a80660002724a2f0050670003e641ef0051428052804a1866fae588223c0000008148780001487800012f034878001d928022016a025281e2812f014879000000002f0e4e9242a74878ffff2f3900000000487800232f0e4eb9000000004fef00307004b0ae00046434206e000822080681ffffffd22801761fc283ea847a2dba88641a262e000c206e00104c003800d684283c80000000e2ac89b03c005480727cb28066be202f001c263c000000ee4c03280048780001d0804878002dd4af00244c4020022042486800044878002c487800042f0e4eb9000000004879000000004879000000002f0e4eb9000000004fef00244cd7443c4fef007c4e75242f001c6000fe7c24390000000078012f44001cb4af001c6300fe6860e242a74879000000002f0e42af005c42af006042af006442af006842af006c42af007042af007442af007842af007c42af008042af00844eb900000000487800014878000148790000000048780010487800254879000000002f0e45f9000000004e924fef0024260f0683000000542eb9000000002f034eb900000000508f4a39000000006700019c42027220282f0078224341f900000000d3c4200452887a26ba806d0001a212c11210740152804a0166ea420142022f400078283c000000002243d3c041f9000000001f81085022007a26ba816d00016412d874015281b1c466ee2f41007842001f8018504a2f00506700024220434280528852804a1866fae588223c0000008148780001487800012f034878001c928022016a025281e2812f014879000000002f0e4e924879000000004879000000002f0e4eb9000000004fef00284cd7443c4fef007c4e7541f90000000042806000f8ac73b9000000007805b8816200010641f90000000073b018072f012f004eb900000000508f4a806600fd6842012a2f007820452805200543f900000000d1c32f4500205c847a26ba806d000176528010d97201b88066ee42012f4000781f8108506000fd2e224322004204742041f900000000d3c06000f8ce4a04670000b82f4500786000f8da2f4000786000f89871b900000000487800012f002f3900000000487800212f0e4eb9000000004879000000004879000000002f0e4eb9000000004fef00206000f92e282f007822434202722041f900000000d3c420046000fe644a026600fea422006000fea24a026600fe68420120042243420241f900000000d3c0283c000000001f81085022006000fe66720541f90000000073b018072f012f004eb900000000508f4a806600fc626000fef822006000f826487800017241487800022f0a4878000d2f014879000000002f0e45f9000000004e92487800012f034eb9000000004fef00242039000000004a806700fc1a6000fe86487800017240487800012f034878001d2f014879000000002f0e4e9242a74878ffff2f3900000000487800232f0e4eb9000000004fef003070046000fc3672406000f7d84a016600fe924201202f00201f8108506000fbbe70406000f8c6487800017240487800012f034878001c2f014879000000002f0e4e924879000000004879000000002f0e4eb9000000004fef00286000fdda487800017240487800012f034878002a2f014879000000002f0e4e924fef001c42806000f9e22f032f0274064eb9400cf8662f004eb94000eb902f004eb940012412508f22004c421003241f2003261f4e7571b900000000598f2f032079800017e42f020c80000000ff674e4a88674a2f48000874064eb9400cf8662f004eb94000eb902f004eb940012412508f22004c421003206f0008123900000000241f2003c0fc0064261f10300842b3804a0057c071004480588f4e75241f4280261f588f4e754feffff02f032f027409206f0020222f001c2028000cb4806d0000bc7601b6806c0000a8206800104a886700009e14390000000032426600009255804a886f0000ae327c00017604b680670000b27604b680650001107402b480670002227603b680670001f24a80670001bc71b90000000074072f400010103900000000b4af0010670002f0718074ffd089b480670002d27602b6806c02700213c00000000010390000000071807405b4af0010650000987628b6806408702813c0000000002f014eb940076082588f241f7001261f4fef00104e7558812f4800202f41001c241f261f4fef00104ef94006fb907404b4806700022c327cffff6000ff5271b90000000052807402b4806c027002324010390000000075b9000000002f420010360913c30000000071807405b4af001064806014760cb6886f04307c000c3408718013c200000000163900000000304334084a02664a7428b4806400ff6470286000ff587406b4806700008a5f804a80674a71b9000000007628d088b6806c34702875b90000000013c0000000007605b6826400ff2c4a39000000006700ff227614b6806400ff1a701413c0000000006000ff0e4a806eca700160c62f4100082f49000c4eb900000000222f00084a806600010810390000000075b9000000002f42001074057180b4af00106400fec46000ff567001b08957c075b9000000002f420010740532401039000000002609448313c3000000007180b4af00106400fe926000ff2471b900000000760741f108081039000000002408c483718013c2000000002f4200107405b4af00106400fe626000fef471b9000000007405b480640000ac7601b68957c04480304013c00000000071b9000000006000fed471b90000000014390000000076072f400010103900000000b6af0010670000b0778253834a836600fe002608e58b75b90000000091c3d1c2763cb6886c0000de307c003c360813c30000000071807405b4af00106400fdde6000fe707601b6af000c57c310390000000075b9000000002f4200107405324371802609448313c300000000b4af00106400fdaa6000fe3c71b9000000007628b6806500fd9e6000fda271b900000000204053804a886600fdd8360975b9000000001039000000002f42001013c3000000006000fdde75827601b682645e143900000000718030426000fdf0428013c0000000001039000000006000fd344a0066627601b6896700008a700113c000000000103900000000304071b9000000006000fdb8740cb4886f00ff22307c000c360813c3000000006000ff1a2408e58a77b90000000091c2d1c3743cb4886c00fd6e307c003c7180340813c2000000006000fd70758076012042b682671e7402b488669876ffb68957c0548013c0000000001039000000003040608eb6896600ff7c700213c00000000010390000000030406000ff764e56fff42f02242e00084878000d2d42fff44eb94007faf4588f4a80660a4a39000000006700015640c00280000007004a80660001404ab900000000660001364ab940fe41786700012c4a390000000067000146227c401178c841f90000000093fc0000000020f18800b1fc0000000066f4487800d0243c0000000041f90000000043f90000000023c200000000203c0000000023c800000000243c0000000023c90000000023c000000000203c0000000023c200000000243c0000000041f90000000043f90000000023c80000000023c90000000023c00000000023c2000000004eb9400802e0588f2d40fff44a80670000822f0074014eb9400a22b050c0206efff443f9000000002149000420bc000000004878001023c80000000013c0000000004eb9400802e0226efff4204020bc401000c421420004214200082149000c2d49fff82d40fffc4eb9400d09742f004eb9400060d842a7486efff82f004eb94007700e486efffc4eb9400cf23c4fef001c242efff04e5e4e7542a72f024eb94006ba90508f2d420008242efff04e5e4ef94006ba204eb9400cf86674062f004eb94000eb902f004eb940012412508f227c401178c84c4200017028740a41f90000000093fc0000000013c10000000033c000000000700133c20000000013c0000000006000fe7e4a390000000067064ef9000000004e75103900000000518f2f0274013040701c2208b58173814c0108002240d3fc000000004a91670a30087380701c4c0108002040d1fc000000004aa80168667a4878000113c100000000740643ef001713d1000000002f41000c2f4800084eb940080064206f0008227c4002f136114201507401222f000c21400154203c0000000021400160c2fc001c2142016842a801582149015c42a801640681000000002f012f3c404a91544eb940001fba4fef000c241f7001508f4e75241f4280508f4e754e56ffec2f0a2f024ab940fe41786700009a486efff4240e0682fffffff02f2e00082f024eb9400f980c4878009c4eb9400802e04fef00102d40ffec4a8067602f022f004eb9400747c0487800104eb9400802e0204070012140000421400008202effec20bc400fbf402d48fffc2140000c2d40fff84eb9400d09742f004eb9400060d842a7486efff82f004eb94007700e486efffc4eb9400cf23c4fef00202f024eb9400f7d5c588f242effe4246effe84e5e4e754feffff02f0e2f02206f00202c504a8e677e42801236080043ef000b20494a016710740cb480670a10c152801236080066f041f108004a80670e73207420b481661a53804a8066f274022f42001c241f2c5f4fef00104ef900000000420141f9000000001f81080b101152894a00670a10c0b1fc0000000066ee421074022f42001c241f2c5f4fef00104ef900000000428043ef000b41f10800609a4e754aaf000467422079000000007014225042a742a7227108002f084e912f39000000004eb94007c76a2f39000000004eb9400802ec42b90000000042004fef001413c0000000004e752079000000007018225042a742a7227108002f084e912f39000000004eb94007c76a2f39000000004eb9400802ec42b90000000042004fef001413c0000000004e7520790000000022502f2f00082f2f00082f08206900104e90207900000000225042a742a72f082069000c4e904fef00184e754e56ff7c48d7043c4eb90000000045f90000000073b9000000007003b081670001406500008a7401b481670001e055814a81660001ce41f9000000002d48ff9043f900000000101152894a00670004e810c0b1fc0000000066ec701f4202206eff9011820800240e0682ffffffd82f022f3c40126ce42f084eb94007bc5e4fef000c4a80660003502f024eb94007bc1c70014cee043cff7c588f72012d41000813c0000000004e5e4ef90000000059814a816600014e207900000000227c53617665203c2054300a247c64206f6e2d49ffc82d40ffd02d4affcc42aeffd442a8000c42a8000842a800044290487800102f084eb900000000240e0682ffffffc8207900000000225042a742a72f082069001c4e904a0057c1730144812f012d40ff944eb9000000004fef00184a2eff97670002342039000000004a80670a2f004eb940076082588f4cee043cff7c223c000000002d4100084e5e4ef90000000020390000000024390000000094800c82000040006200036a4a82674ae5882602d6832f39000000002f39000000002f02d0922d43ff982f002f39000000002d41ff944eb9000000002f2eff982f39000000004eb900000000d5b9000000004fef001c222eff942039000000004a8067122f002d41ff944eb940076082588f222eff942a3900000000bab900000000620272042f014eb900000000588f4a80670002aa4cee043cff7c4e5e4e75227c4002f136203c00000000223c0000000042aeffb842aeffbc2d49ffc02d40ffc442aeffc842aeffcc2d49ffd02d41ffd44ab90000000067bc71b90000000057804a8066b04a3900000000670003bc41eeffb043eeffd8203c000000002d48ffa02d49ff9c486effa9247c400f980c2f00486effac4e92486effaa487900000000240e0682ffffffc82f2effa04e92486effab4879000000002f2eff9c4e924fef0024487800014eb940080064487800012d40ffb84eb940080064487800ac2d40ffc84eb9400802e04fef000c24404a80670004c82f02220e0681ffffffb82f014878000c42a72f2eff9c2f2effa0486effac2f002d41ff944eb9400411524fef00204eb9400d09742f004eb9400060d842a72f0a247c400cf0442f004eb94007722a4fef0010222eff942f014e922f024e92486effac247c400f7d5c4e922f2effa04e922f2eff9c4e924fef00144cee043cff7c4e5e4e754a3900000000660002184eb9000000002079000000004a88671222502f08206900284e907030588f1d40ffd241eeffd82d48ff9c43f900000000206eff9c428012310800670003b210c152807427b48066ee702742041d8408d82f2eff9c4eb9000000004cee043cff7c588f4e5e4e754a390000000056c0223900000000420242b900000000710013c2000000004480e1a923c1000000004a39000000006600016071b9000000007605b6806302700571b20807781042b900000000988023c4000000002f3c000081104eb9400802e0588f4a806700008c223900000000068100000028d281740123c0000000002f014879000000002f0013c2000000004eb94007c7ca71b9000000002f002f39000000002f39000000004eb900000000487800402f39000000004eb9000000004fef0020487800034eb900000000588f4a806600fd5a42a74eb900000000588f2039000000004a80670a2f004eb940076082588f2a3c000000002d4500084cee043cff7c4e5e4ef900000000e5882f39000000002f3900000000243c000040002f02283c000080002d44ff98d0922f002f39000000002d41ff944eb9000000002f2eff982f39000000004eb900000000d5b9000000004fef001c222eff946000fc92200804800000000041f90000000043f900000000121052884a016700fb0a138108015280721fb28066ea701f6000faf84879000000004879000000002f39000000004eb9000000004fef000c6000fea64eb9000000004a80670001f445eeffb82f0a2f3c40126ce44879000000004eb94007bc5e4fef000c4a80660001d22f0a246effb84eb94007bc1c43eeffd82f092f0a2d49ff9c4eb94007de784fef000c4a80660002047001c0aeffdc4a80660002264eb9000000002079000000004a886700fda222502f08206900284e907230588f43f9000000001d41ffd26000fd8c41f90000000078012d48ff90223cfffffee8928a263c5245432d2a3c3030300041eeffb043eeffd82d43ffb0243c000000002d44ff982d45ffb42d41ffa42d48ffa02d49ff9c45f900000000700a786443f900000000222eff984c4010034c401001202eff984c4400002043780a26014c443005068000000030e18841e80030360841f900000000220506810000003010011d43ffb63d40ffb4101052884a00677c12c0b3c266f2721f4205206eff90118518002f2eff9c2f3c40126ce42f084eb94007bc5e4fef000c4a80661e2f2eff9c4eb94007bc1c52aeff98222eff98588f0c81000003e86600ff62226effa041f900000000101152894a00670a10c0b1fc0000000066ee42104a3900000000660001ae203c000000006000fb40206effa4d1c9226effa093c810318800220852884a006700ff741180a800781fb88866e8721f6000ff64226eff9cd3c041f900000000121052884a016700fc4812c152807627b68066ec70276000fc384eb9000000002079000000004a886600fbec43eeffd82d49ff9c43f9000000006000fbfa220e0681ffffffb82f01247c400cf0444e922f024e92486effac247c400f7d5c4e922f2effa04e922f2eff9c4e924fef00146000fb804eb9000000002079000000004a886700fbac22502f08206900284e907030588f43f9000000001d40ffd26000fb964eb9000000002d40ff984eb9400cf8664a8067be222eff98764420404c0318000681000000d4d1c122504a8967a4202900284a80679c2f0820404e90588f4a8067902240732900262041733900000000b2886600ff7e334a004620405889068000000014216effdc004820494218b1c066fa41f900000000101052884a00670a12c0b1fc0000000066ee4eb900000000246eff9820790000000045ea00314a88670c22502f08206900284e90588f300a224272ff1d40ffd2b2aeff986700fad0206eff9c42806000fad2203c000000006000f9944a390000000067024e75487800014eb900000000588f4e75206f0004700db0a8000c660c7001c0a8001013c0000000002028000c4e75000042b9000000004ef9400f43ca42b9000000004ef9400f448659af000460e259af000460e859af00044ef900000000800000005a9df7ac4026e73d2d6a866f2026f31016c310e3101d3f2e0b68737a0813856205b7b15b040c371402dd958a0207567a016fa9bb0104491500b8449c008273a6005c5a4f00416179002e49390020c49c001732ae00106c43000ba06400083b200005d3bb000420100002eba300021149000176b5000109450000bbcc000084f3524553414d504c450053544f505320415420004f46200053544f5053205748454e2053494c454e54005245434f52442053544f5053002d2d2d004f4646004f4e004e4f0059455300534f55524345005354415254005448524553480053544552454f0053544f50004c454e475448004e4f524d0052455455524e3a20434c4f5345005245434f52443a2041524d002d3630002d333000304442005741495420464f52204c4556454c005741495420464f522054524947002053544552454f2020202000204d4f4e4f2020202000202053544552454f0020204d4f4e4f0041524d4544005245434f52443a2043414e43454c00524543002020434c49500052455455524e3a2053544f50005245434f52443a2053544f5000534156494e47002f5245434f5244494e47530057524954494e4720544f202b445249564500554e5341564544004e4f54205341564544002020494e204d454d4f52590052455455524e3a2044495343415244005245434f52443a20534156450053494c454e54005245434f52440054524947004c4556454c004e4f57005431005432005433005434005435005436004d41494e00555342000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000507060504070504030504030e11111f1111111e11111e11111e0e11101010110e1c12111111121c1f10101e10101f1f10101e1010100e11101711110f1111111f1111110e04040404040e0702020202120c111214181412111010101010101f111b1515111111111119151311110e11111111110e1e11111e1010100e11111115120d1e11111e1412110f10100e01011e1f0404040404041111111111110e11111111110a041111111515150a11110a040a11111111110a0404041f01020408101f0e11131519110e040c040404040e0e11010204081f1f02040201110e02060a121f02021f101e0101110e0608101e11110e1f0102040808080e11110e11110e0e11110f01020c0000001f00000000000000000c0c000c0c000c0c0000010204081000181902040813030004041f04040000000000000000000000000000000699f9990e99e99e069888960e99999e0f88e88f0f88e8880698b9970999f9990e44444e072222a409ac8ca90888888f09ff999909ddbb99069999960e99e88806999ba50e99eca90788611e0e444444099999960999996609999ff9099666990aaa44440f12488f069bd99604c4444e0691248f0e11611e026aaf220f8e11960688e9960f12244406996996069971160000e000000000cc0000000000000000000000000000000000000000000000002bed6bae39236b6e79a779a4396b5bed7497126a5bad49275fed6b6d2b6a6ba42b7b6bad388e74925b6f5b6a5bfd5aad5a9272a77b6f2c9762a7628e5bc9798e39ef72927bef7bce01c00002041012a452a505d0445400004142434445464748494a4b4c4d4e4f505152535455565758595a303132333435363738392d2e3a2f252b3e20004e616d652065786973747300526573616d706c650053617665640a002f7265636f7264696e67732f0053617665207265636f7264696e672061730053617665206661696c656400",
    "relocs": [
     [
      336,
      "rs_data",
      18
     ],
     [
      344,
      "rs_data",
      16
     ],
     [
      354,
      "rs_data",
      0
     ],
     [
      366,
      "rs_data",
      16
     ],
     [
      390,
      "rs_data",
      16
     ],
     [
      400,
      "rs_data",
      0
     ],
     [
      418,
      "rs_data",
      24
     ],
     [
      424,
      "rs_data",
      8
     ],
     [
      466,
      "code",
      176
     ],
     [
      472,
      "rs_data",
      19
     ],
     [
      484,
      "rs_data",
      60
     ],
     [
      502,
      "rs_data",
      24
     ],
     [
      530,
      "rs_data",
      23
     ],
     [
      536,
      "rs_data",
      24
     ],
     [
      558,
      "rs_data",
      23
     ],
     [
      570,
      "rs_data",
      44
     ],
     [
      578,
      "rs_data",
      40
     ],
     [
      624,
      "code",
      176
     ],
     [
      636,
      "rs_data",
      44
     ],
     [
      642,
      "rs_data",
      60
     ],
     [
      648,
      "rs_data",
      44
     ],
     [
      654,
      "rs_data",
      48
     ],
     [
      662,
      "rs_data",
      48
     ],
     [
      668,
      "rs_data",
      36
     ],
     [
      676,
      "rs_data",
      56
     ],
     [
      682,
      "rs_data",
      32
     ],
     [
      698,
      "rs_data",
      52
     ],
     [
      704,
      "rs_data",
      21
     ],
     [
      712,
      "rs_data",
      40
     ],
     [
      718,
      "rs_data",
      20
     ],
     [
      724,
      "rs_data",
      44
     ],
     [
      750,
      "rs_data",
      21
     ],
     [
      756,
      "rs_data",
      22
     ],
     [
      762,
      "rs_data",
      16
     ],
     [
      778,
      "rs_data",
      52
     ],
     [
      784,
      "rs_data",
      21
     ],
     [
      798,
      "rs_data",
      21
     ],
     [
      804,
      "rs_data",
      22
     ],
     [
      810,
      "rs_data",
      16
     ],
     [
      852,
      "code",
      176
     ],
     [
      864,
      "rs_data",
      44
     ],
     [
      870,
      "rs_data",
      60
     ],
     [
      876,
      "rs_data",
      44
     ],
     [
      882,
      "rs_data",
      48
     ],
     [
      898,
      "rs_data",
      40
     ],
     [
      906,
      "rs_data",
      56
     ],
     [
      914,
      "rs_data",
      52
     ],
     [
      920,
      "rs_data",
      48
     ],
     [
      926,
      "rs_data",
      44
     ],
     [
      936,
      "rs_data",
      21
     ],
     [
      942,
      "rs_data",
      22
     ],
     [
      954,
      "rs_data",
      24
     ],
     [
      984,
      "code",
      176
     ],
     [
      996,
      "rs_data",
      44
     ],
     [
      1002,
      "rs_data",
      44
     ],
     [
      1008,
      "rs_data",
      48
     ],
     [
      1016,
      "rs_data",
      48
     ],
     [
      1022,
      "rs_data",
      36
     ],
     [
      1030,
      "rs_data",
      56
     ],
     [
      1036,
      "rs_data",
      32
     ],
     [
      1044,
      "rs_data",
      52
     ],
     [
      1052,
      "rs_data",
      16
     ],
     [
      1074,
      "rs_data",
      52
     ],
     [
      1090,
      "rs_data",
      56
     ],
     [
      1096,
      "rs_data",
      44
     ],
     [
      1102,
      "rs_data",
      21
     ],
     [
      1108,
      "rs_data",
      22
     ],
     [
      1114,
      "rs_data",
      16
     ],
     [
      1134,
      "rs_data",
      52
     ],
     [
      1140,
      "rs_data",
      16
     ],
     [
      1158,
      "rs_data",
      28
     ],
     [
      1170,
      "rs_data",
      23
     ],
     [
      1180,
      "rs_data",
      56
     ],
     [
      1186,
      "rs_data",
      52
     ],
     [
      1192,
      "rs_data",
      48
     ],
     [
      1198,
      "rs_data",
      44
     ],
     [
      1208,
      "rs_data",
      21
     ],
     [
      1214,
      "rs_data",
      22
     ],
     [
      1252,
      "rs_data",
      40
     ],
     [
      1310,
      "code",
      176
     ],
     [
      1322,
      "rs_data",
      44
     ],
     [
      1328,
      "rs_data",
      44
     ],
     [
      1334,
      "rs_data",
      48
     ],
     [
      1342,
      "rs_data",
      48
     ],
     [
      1348,
      "rs_data",
      36
     ],
     [
      1356,
      "rs_data",
      56
     ],
     [
      1362,
      "rs_data",
      32
     ],
     [
      1372,
      "rs_data",
      52
     ],
     [
      1402,
      "rs_data",
      40
     ],
     [
      1414,
      "rs_data",
      24
     ],
     [
      1434,
      "rs_data",
      24
     ],
     [
      1448,
      "rs_data",
      40
     ],
     [
      1456,
      "rs_data",
      56
     ],
     [
      1464,
      "rs_data",
      52
     ],
     [
      1470,
      "rs_data",
      48
     ],
     [
      1476,
      "rs_data",
      44
     ],
     [
      1486,
      "rs_data",
      21
     ],
     [
      1492,
      "rs_data",
      22
     ],
     [
      1522,
      "rs_data",
      52
     ],
     [
      1532,
      "rs_data",
      24
     ],
     [
      1548,
      "rs_data",
      21
     ],
     [
      1554,
      "rs_data",
      22
     ],
     [
      1560,
      "rs_data",
      16
     ],
     [
      1570,
      "rs_data",
      40
     ],
     [
      1600,
      "code",
      15330
     ],
     [
      94,
      "rs_data",
      16
     ],
     [
      108,
      "rs_data",
      16
     ],
     [
      124,
      "rs_data",
      17
     ],
     [
      164,
      "code",
      326
     ],
     [
      1640,
      "rs_data",
      16
     ],
     [
      1666,
      "rs_data",
      16
     ],
     [
      1678,
      "rs_data",
      17
     ],
     [
      1716,
      "code",
      326
     ],
     [
      1750,
      "code",
      326
     ],
     [
      1756,
      "rs_data",
      16
     ],
     [
      1780,
      "rs_data",
      16
     ],
     [
      1812,
      "rs_data",
      0
     ],
     [
      1824,
      "rs_data",
      17
     ],
     [
      1842,
      "rs_data",
      18
     ],
     [
      1862,
      "rs_data",
      19
     ],
     [
      1878,
      "rs_data",
      20
     ],
     [
      1890,
      "code",
      15330
     ],
     [
      1928,
      "rs_data",
      36
     ],
     [
      1936,
      "rs_data",
      4
     ],
     [
      1942,
      "rs_data",
      28
     ],
     [
      1948,
      "rs_data",
      32
     ],
     [
      1994,
      "rs_data",
      40
     ],
     [
      2000,
      "rs_data",
      60
     ],
     [
      2006,
      "rs_data",
      56
     ],
     [
      2012,
      "rs_data",
      52
     ],
     [
      2018,
      "rs_data",
      48
     ],
     [
      2024,
      "rs_data",
      44
     ],
     [
      2030,
      "rs_data",
      21
     ],
     [
      2038,
      "rs_data",
      22
     ],
     [
      2044,
      "rs_data",
      24
     ],
     [
      2050,
      "rs_data",
      16
     ],
     [
      2078,
      "rs_data",
      18
     ],
     [
      2104,
      "rs_data",
      16
     ],
     [
      2116,
      "rs_data",
      16
     ],
     [
      2132,
      "rs_data",
      21
     ],
     [
      2142,
      "rs_data",
      16
     ],
     [
      2152,
      "rs_data",
      16
     ],
     [
      2160,
      "rs_data",
      16
     ],
     [
      2176,
      "rs_data",
      16
     ],
     [
      2718,
      "rs_data",
      16
     ],
     [
      2762,
      "rs_data",
      77
     ],
     [
      2778,
      "rs_data",
      257
     ],
     [
      2786,
      "rs_data",
      256
     ],
     [
      2794,
      "rs_data",
      77
     ],
     [
      2812,
      "rs_data",
      256
     ],
     [
      2834,
      "rs_data",
      257
     ],
     [
      2840,
      "code",
      15228
     ],
     [
      2864,
      "rs_data",
      261
     ],
     [
      2962,
      "rs_data",
      256
     ],
     [
      3018,
      "rs_data",
      256
     ],
     [
      3040,
      "rs_data",
      16
     ],
     [
      3054,
      "rs_data",
      16
     ],
     [
      3082,
      "code",
      2148
     ],
     [
      3088,
      "rs_data",
      261
     ],
     [
      3096,
      "code",
      2858
     ],
     [
      3144,
      "rs_data",
      79
     ],
     [
      3152,
      "rs_data",
      16
     ],
     [
      3172,
      "code",
      2102
     ],
     [
      3178,
      "rs_data",
      261
     ],
     [
      3186,
      "code",
      2858
     ],
     [
      3214,
      "code",
      2102
     ],
     [
      3240,
      "code",
      15228
     ],
     [
      3260,
      "code",
      2158
     ],
     [
      3270,
      "code",
      2102
     ],
     [
      3284,
      "rs_data",
      257
     ],
     [
      3296,
      "rs_data",
      68
     ],
     [
      3306,
      "rs_data",
      69
     ],
     [
      3378,
      "rs_data",
      68
     ],
     [
      3384,
      "rs_data",
      70
     ],
     [
      3390,
      "rs_data",
      261
     ],
     [
      3396,
      "rs_data",
      73
     ],
     [
      3408,
      "rs_data",
      69
     ],
     [
      3414,
      "rs_data",
      72
     ],
     [
      3428,
      "rs_data",
      71
     ],
     [
      3444,
      "code",
      1754
     ],
     [
      3470,
      "rs_data",
      70
     ],
     [
      3476,
      "rs_data",
      73
     ],
     [
      3486,
      "rs_data",
      72
     ],
     [
      3502,
      "rs_data",
      71
     ],
     [
      3518,
      "code",
      1754
     ],
     [
      3534,
      "rs_data",
      73
     ],
     [
      3540,
      "rs_data",
      70
     ],
     [
      3546,
      "rs_data",
      72
     ],
     [
      3558,
      "rs_data",
      71
     ],
     [
      3574,
      "code",
      1754
     ],
     [
      3684,
      "code",
      16534
     ],
     [
      3746,
      "code",
      15962
     ],
     [
      4042,
      "code",
      16446
     ],
     [
      4074,
      "code",
      16270
     ],
     [
      4372,
      "code",
      15958
     ],
     [
      4384,
      "code",
      3586
     ],
     [
      4438,
      "code",
      15958
     ],
     [
      4446,
      "code",
      3586
     ],
     [
      4484,
      "code",
      15958
     ],
     [
      4492,
      "code",
      3586
     ],
     [
      4520,
      "code",
      15462
     ],
     [
      4534,
      "code",
      15950
     ],
     [
      4540,
      "code",
      3586
     ],
     [
      4606,
      "code",
      3586
     ],
     [
      4628,
      "code",
      15958
     ],
     [
      4756,
      "code",
      4106
     ],
     [
      4776,
      "code",
      3586
     ],
     [
      4798,
      "code",
      15958
     ],
     [
      4882,
      "code",
      2570
     ],
     [
      4994,
      "code",
      2570
     ],
     [
      5022,
      "rs_data",
      20
     ],
     [
      5066,
      "code",
      15481
     ],
     [
      5108,
      "rs_data",
      40
     ],
     [
      5126,
      "code",
      2570
     ],
     [
      5178,
      "code",
      15503
     ],
     [
      5206,
      "code",
      15515
     ],
     [
      5228,
      "code",
      15485
     ],
     [
      5256,
      "code",
      15502
     ],
     [
      5280,
      "code",
      15471
     ],
     [
      5314,
      "code",
      15541
     ],
     [
      5334,
      "code",
      15547
     ],
     [
      5344,
      "code",
      15534
     ],
     [
      5354,
      "code",
      15554
     ],
     [
      5364,
      "code",
      15561
     ],
     [
      5370,
      "code",
      15573
     ],
     [
      5406,
      "code",
      15566
     ],
     [
      5424,
      "rs_data",
      68
     ],
     [
      5430,
      "rs_data",
      69
     ],
     [
      5484,
      "code",
      15918
     ],
     [
      5546,
      "code",
      15906
     ],
     [
      5650,
      "code",
      15516
     ],
     [
      5682,
      "code",
      2570
     ],
     [
      5714,
      "rs_data",
      71
     ],
     [
      5726,
      "code",
      15524
     ],
     [
      5782,
      "code",
      15894
     ],
     [
      5788,
      "rs_data",
      72
     ],
     [
      5870,
      "rs_data",
      73
     ],
     [
      5926,
      "rs_data",
      74
     ],
     [
      5946,
      "code",
      15524
     ],
     [
      5986,
      "rs_data",
      78
     ],
     [
      6042,
      "rs_data",
      78
     ],
     [
      6074,
      "code",
      15516
     ],
     [
      6128,
      "code",
      3586
     ],
     [
      6188,
      "code",
      4502
     ],
     [
      6244,
      "code",
      15958
     ],
     [
      6272,
      "code",
      15954
     ],
     [
      6338,
      "code",
      15958
     ],
     [
      6372,
      "code",
      15954
     ],
     [
      6400,
      "code",
      15516
     ],
     [
      6414,
      "code",
      15578
     ],
     [
      6420,
      "code",
      15592
     ],
     [
      6428,
      "code",
      4252
     ],
     [
      6458,
      "code",
      15520
     ],
     [
      6496,
      "code",
      15520
     ],
     [
      6512,
      "rs_data",
      75
     ],
     [
      6532,
      "code",
      15527
     ],
     [
      6606,
      "code",
      3586
     ],
     [
      6666,
      "code",
      4502
     ],
     [
      6758,
      "code",
      2570
     ],
     [
      6772,
      "rs_data",
      70
     ],
     [
      6874,
      "code",
      2570
     ],
     [
      6902,
      "code",
      15530
     ],
     [
      6984,
      "code",
      4106
     ],
     [
      7474,
      "code",
      15604
     ],
     [
      7490,
      "code",
      15958
     ],
     [
      7498,
      "code",
      3586
     ],
     [
      7514,
      "code",
      15608
     ],
     [
      7526,
      "code",
      15958
     ],
     [
      7548,
      "code",
      15612
     ],
     [
      7560,
      "code",
      15958
     ],
     [
      7584,
      "rs_data",
      17
     ],
     [
      7598,
      "rs_data",
      0
     ],
     [
      7608,
      "code",
      4106
     ],
     [
      7620,
      "code",
      1586
     ],
     [
      7936,
      "rs_data",
      16
     ],
     [
      7976,
      "code",
      5308
     ],
     [
      7988,
      "code",
      15683
     ],
     [
      8044,
      "code",
      4502
     ],
     [
      8054,
      "rs_data",
      19
     ],
     [
      8068,
      "code",
      15631
     ],
     [
      8110,
      "code",
      3586
     ],
     [
      8128,
      "code",
      15950
     ],
     [
      8142,
      "rs_data",
      17
     ],
     [
      8150,
      "code",
      15918
     ],
     [
      8204,
      "rs_data",
      18
     ],
     [
      8222,
      "code",
      15645
     ],
     [
      8266,
      "code",
      5020
     ],
     [
      8328,
      "code",
      15958
     ],
     [
      8342,
      "rs_data",
      19
     ],
     [
      8364,
      "rs_data",
      60
     ],
     [
      8376,
      "code",
      6932
     ],
     [
      8382,
      "code",
      15578
     ],
     [
      8388,
      "code",
      15689
     ],
     [
      8396,
      "code",
      4252
     ],
     [
      8416,
      "rs_data",
      256
     ],
     [
      8426,
      "rs_data",
      320
     ],
     [
      8490,
      "rs_data",
      316
     ],
     [
      8504,
      "code",
      15741
     ],
     [
      8512,
      "code",
      4502
     ],
     [
      8522,
      "rs_data",
      264
     ],
     [
      8532,
      "rs_data",
      265
     ],
     [
      8550,
      "rs_data",
      264
     ],
     [
      8584,
      "rs_data",
      264
     ],
     [
      8596,
      "code",
      15950
     ],
     [
      8604,
      "code",
      3586
     ],
     [
      8620,
      "code",
      15748
     ],
     [
      8634,
      "code",
      15958
     ],
     [
      8670,
      "code",
      4106
     ],
     [
      8698,
      "code",
      4106
     ],
     [
      8730,
      "code",
      4106
     ],
     [
      8758,
      "code",
      4106
     ],
     [
      8818,
      "code",
      4106
     ],
     [
      8846,
      "code",
      2570
     ],
     [
      8938,
      "code",
      15958
     ],
     [
      9030,
      "code",
      15760
     ],
     [
      9044,
      "code",
      15958
     ],
     [
      9068,
      "rs_data",
      40
     ],
     [
      9182,
      "rs_data",
      44
     ],
     [
      9200,
      "code",
      15704
     ],
     [
      9208,
      "code",
      4502
     ],
     [
      9214,
      "rs_data",
      44
     ],
     [
      9222,
      "code",
      4830
     ],
     [
      9278,
      "code",
      3586
     ],
     [
      9292,
      "code",
      15950
     ],
     [
      9308,
      "code",
      5020
     ],
     [
      9318,
      "rs_data",
      48
     ],
     [
      9384,
      "code",
      15958
     ],
     [
      9400,
      "rs_data",
      60
     ],
     [
      9412,
      "code",
      6932
     ],
     [
      9538,
      "code",
      4106
     ],
     [
      9544,
      "code",
      15715
     ],
     [
      9550,
      "code",
      15728
     ],
     [
      9558,
      "code",
      4252
     ],
     [
      9586,
      "rs_data",
      44
     ],
     [
      9610,
      "code",
      15778
     ],
     [
      9662,
      "code",
      4502
     ],
     [
      9676,
      "code",
      15786
     ],
     [
      9690,
      "code",
      15950
     ],
     [
      9698,
      "code",
      3586
     ],
     [
      9718,
      "rs_data",
      44
     ],
     [
      9726,
      "code",
      4830
     ],
     [
      9734,
      "rs_data",
      18
     ],
     [
      9754,
      "code",
      15667
     ],
     [
      9794,
      "code",
      15807
     ],
     [
      9804,
      "code",
      15796
     ],
     [
      9898,
      "code",
      15958
     ],
     [
      9908,
      "code",
      15808
     ],
     [
      9914,
      "code",
      15824
     ],
     [
      9922,
      "code",
      4252
     ],
     [
      9942,
      "code",
      15616
     ],
     [
      9954,
      "rs_data",
      17
     ],
     [
      9968,
      "rs_data",
      0
     ],
     [
      9982,
      "code",
      1586
     ],
     [
      10008,
      "code",
      15708
     ],
     [
      10062,
      "code",
      15657
     ],
     [
      10096,
      "rs_data",
      70
     ],
     [
      10108,
      "rs_data",
      60
     ],
     [
      10120,
      "code",
      6932
     ],
     [
      10126,
      "code",
      15578
     ],
     [
      10132,
      "code",
      15689
     ],
     [
      10140,
      "code",
      4252
     ],
     [
      10164,
      "code",
      15676
     ],
     [
      10204,
      "code",
      15796
     ],
     [
      10212,
      "code",
      15807
     ],
     [
      10230,
      "rs_data",
      0
     ],
     [
      10244,
      "code",
      1586
     ],
     [
      10286,
      "code",
      15950
     ],
     [
      10294,
      "code",
      3586
     ],
     [
      10308,
      "code",
      5020
     ],
     [
      10318,
      "rs_data",
      48
     ],
     [
      10352,
      "code",
      15958
     ],
     [
      10368,
      "rs_data",
      60
     ],
     [
      10380,
      "code",
      6932
     ],
     [
      10446,
      "code",
      15958
     ],
     [
      10456,
      "code",
      15808
     ],
     [
      10462,
      "code",
      15824
     ],
     [
      10470,
      "code",
      4252
     ],
     [
      10502,
      "code",
      15958
     ],
     [
      10566,
      "rs_data",
      78
     ],
     [
      10636,
      "rs_data",
      78
     ],
     [
      10726,
      "rs_data",
      16
     ],
     [
      10788,
      "rs_data",
      68
     ],
     [
      10800,
      "rs_data",
      69
     ],
     [
      10834,
      "rs_data",
      69
     ],
     [
      10840,
      "rs_data",
      73
     ],
     [
      10866,
      "rs_data",
      73
     ],
     [
      10934,
      "rs_data",
      72
     ],
     [
      10952,
      "rs_data",
      73
     ],
     [
      10958,
      "rs_data",
      68
     ],
     [
      10970,
      "rs_data",
      72
     ],
     [
      11002,
      "rs_data",
      70
     ],
     [
      11008,
      "rs_data",
      71
     ],
     [
      11050,
      "rs_data",
      73
     ],
     [
      11066,
      "rs_data",
      68
     ],
     [
      11072,
      "rs_data",
      73
     ],
     [
      11086,
      "rs_data",
      71
     ],
     [
      11106,
      "rs_data",
      73
     ],
     [
      11132,
      "code",
      10564
     ],
     [
      11148,
      "rs_data",
      73
     ],
     [
      11154,
      "rs_data",
      68
     ],
     [
      11186,
      "rs_data",
      68
     ],
     [
      11200,
      "rs_data",
      73
     ],
     [
      11210,
      "rs_data",
      74
     ],
     [
      11230,
      "rs_data",
      68
     ],
     [
      11242,
      "rs_data",
      73
     ],
     [
      11254,
      "rs_data",
      68
     ],
     [
      11278,
      "rs_data",
      68
     ],
     [
      11302,
      "rs_data",
      71
     ],
     [
      11308,
      "rs_data",
      73
     ],
     [
      11318,
      "rs_data",
      68
     ],
     [
      11324,
      "rs_data",
      69
     ],
     [
      11336,
      "rs_data",
      73
     ],
     [
      11364,
      "rs_data",
      70
     ],
     [
      11388,
      "rs_data",
      70
     ],
     [
      11418,
      "rs_data",
      73
     ],
     [
      11424,
      "rs_data",
      68
     ],
     [
      11444,
      "rs_data",
      75
     ],
     [
      11462,
      "rs_data",
      73
     ],
     [
      11480,
      "rs_data",
      72
     ],
     [
      11498,
      "rs_data",
      68
     ],
     [
      11504,
      "rs_data",
      73
     ],
     [
      11514,
      "rs_data",
      72
     ],
     [
      11532,
      "rs_data",
      71
     ],
     [
      11548,
      "rs_data",
      69
     ],
     [
      11554,
      "rs_data",
      73
     ],
     [
      11578,
      "rs_data",
      69
     ],
     [
      11584,
      "rs_data",
      71
     ],
     [
      11592,
      "rs_data",
      73
     ],
     [
      11616,
      "rs_data",
      70
     ],
     [
      11630,
      "rs_data",
      70
     ],
     [
      11656,
      "rs_data",
      70
     ],
     [
      11690,
      "rs_data",
      69
     ],
     [
      11696,
      "rs_data",
      71
     ],
     [
      11714,
      "rs_data",
      69
     ],
     [
      11720,
      "rs_data",
      71
     ],
     [
      11762,
      "rs_data",
      79
     ],
     [
      11786,
      "rs_data",
      64
     ],
     [
      11806,
      "rs_data",
      76
     ],
     [
      11822,
      "rs_data",
      80
     ],
     [
      11828,
      "rs_data",
      0
     ],
     [
      11838,
      "rs_data",
      256
     ],
     [
      11850,
      "code",
      15284
     ],
     [
      11856,
      "code",
      15296
     ],
     [
      11862,
      "code",
      2922
     ],
     [
      11868,
      "rs_data",
      88
     ],
     [
      11874,
      "code",
      7892
     ],
     [
      11880,
      "rs_data",
      92
     ],
     [
      11886,
      "code",
      2716
     ],
     [
      11892,
      "rs_data",
      96
     ],
     [
      11898,
      "rs_data",
      104
     ],
     [
      11904,
      "code",
      15314
     ],
     [
      11910,
      "rs_data",
      132
     ],
     [
      11916,
      "code",
      15320
     ],
     [
      11922,
      "code",
      10678
     ],
     [
      11928,
      "code",
      15308
     ],
     [
      11934,
      "rs_data",
      156
     ],
     [
      11940,
      "rs_data",
      168
     ],
     [
      11946,
      "rs_data",
      172
     ],
     [
      11952,
      "rs_data",
      176
     ],
     [
      11992,
      "rs_data",
      168
     ],
     [
      12002,
      "rs_data",
      88
     ],
     [
      12012,
      "rs_data",
      64
     ],
     [
      12018,
      "rs_data",
      77
     ],
     [
      12180,
      "rs_data",
      80
     ],
     [
      12186,
      "rs_data",
      0
     ],
     [
      12192,
      "rs_data",
      68
     ],
     [
      12198,
      "rs_data",
      69
     ],
     [
      12206,
      "rs_data",
      72
     ],
     [
      12212,
      "rs_data",
      76
     ],
     [
      12222,
      "rs_data",
      261
     ],
     [
      12230,
      "code",
      2858
     ],
     [
      15894,
      "code",
      15837
     ],
     [
      15898,
      "code",
      15566
     ],
     [
      15902,
      "code",
      15844
     ],
     [
      15906,
      "code",
      15851
     ],
     [
      15910,
      "code",
      15856
     ],
     [
      15914,
      "code",
      15862
     ],
     [
      15918,
      "code",
      15866
     ],
     [
      15922,
      "code",
      15869
     ],
     [
      15926,
      "code",
      15872
     ],
     [
      15930,
      "code",
      15875
     ],
     [
      15934,
      "code",
      15878
     ],
     [
      15938,
      "code",
      15881
     ],
     [
      15942,
      "code",
      15884
     ],
     [
      15946,
      "code",
      15889
     ],
     [
      12238,
      "rs_data",
      260
     ],
     [
      12266,
      "rs_data",
      360
     ],
     [
      12288,
      "rs_data",
      0
     ],
     [
      12304,
      "rs_data",
      260
     ],
     [
      12316,
      "rs_data",
      259
     ],
     [
      12360,
      "code",
      12956
     ],
     [
      12390,
      "rs_data",
      336
     ],
     [
      12698,
      "code",
      12236
     ],
     [
      12706,
      "rs_data",
      264
     ],
     [
      12726,
      "rs_data",
      279
     ],
     [
      12750,
      "code",
      12236
     ],
     [
      12776,
      "rs_data",
      312
     ],
     [
      12798,
      "rs_data",
      312
     ],
     [
      12810,
      "rs_data",
      312
     ],
     [
      12822,
      "rs_data",
      312
     ],
     [
      12834,
      "rs_data",
      256
     ],
     [
      12842,
      "rs_data",
      312
     ],
     [
      12864,
      "rs_data",
      312
     ],
     [
      12876,
      "rs_data",
      312
     ],
     [
      12888,
      "rs_data",
      312
     ],
     [
      12900,
      "rs_data",
      256
     ],
     [
      12908,
      "rs_data",
      312
     ],
     [
      12932,
      "rs_data",
      312
     ],
     [
      12966,
      "code",
      12220
     ],
     [
      12972,
      "rs_data",
      0
     ],
     [
      12978,
      "rs_data",
      259
     ],
     [
      13012,
      "rs_data",
      280
     ],
     [
      13022,
      "code",
      16607
     ],
     [
      13040,
      "rs_data",
      311
     ],
     [
      13118,
      "rs_data",
      258
     ],
     [
      13126,
      "code",
      12236
     ],
     [
      13140,
      "rs_data",
      332
     ],
     [
      13200,
      "code",
      12906
     ],
     [
      13214,
      "rs_data",
      312
     ],
     [
      13248,
      "code",
      12768
     ],
     [
      13266,
      "rs_data",
      64
     ],
     [
      13292,
      "code",
      16638
     ],
     [
      13304,
      "code",
      12428
     ],
     [
      13310,
      "rs_data",
      316
     ],
     [
      13316,
      "rs_data",
      320
     ],
     [
      13344,
      "rs_data",
      328
     ],
     [
      13350,
      "rs_data",
      324
     ],
     [
      13366,
      "rs_data",
      332
     ],
     [
      13376,
      "code",
      2426
     ],
     [
      13386,
      "rs_data",
      332
     ],
     [
      13392,
      "code",
      12906
     ],
     [
      13398,
      "rs_data",
      316
     ],
     [
      13412,
      "rs_data",
      64
     ],
     [
      13440,
      "rs_data",
      320
     ],
     [
      13446,
      "rs_data",
      316
     ],
     [
      13458,
      "code",
      12236
     ],
     [
      13488,
      "code",
      12766
     ],
     [
      13494,
      "code",
      12610
     ],
     [
      13532,
      "rs_data",
      64
     ],
     [
      13540,
      "rs_data",
      16
     ],
     [
      13552,
      "rs_data",
      258
     ],
     [
      13570,
      "code",
      16579
     ],
     [
      13606,
      "rs_data",
      264
     ],
     [
      13630,
      "code",
      16620
     ],
     [
      13828,
      "rs_data",
      75
     ],
     [
      13838,
      "code",
      2158
     ],
     [
      13844,
      "rs_data",
      64
     ],
     [
      13880,
      "code",
      16600
     ],
     [
      13922,
      "code",
      12428
     ],
     [
      13940,
      "rs_data",
      18
     ],
     [
      13948,
      "rs_data",
      44
     ],
     [
      13956,
      "rs_data",
      316
     ],
     [
      13964,
      "rs_data",
      258
     ],
     [
      13974,
      "rs_data",
      320
     ],
     [
      13980,
      "rs_data",
      74
     ],
     [
      13990,
      "rs_data",
      17
     ],
     [
      14010,
      "rs_data",
      328
     ],
     [
      14018,
      "rs_data",
      324
     ],
     [
      14044,
      "rs_data",
      320
     ],
     [
      14060,
      "rs_data",
      312
     ],
     [
      14068,
      "rs_data",
      280
     ],
     [
      14076,
      "rs_data",
      256
     ],
     [
      14088,
      "rs_data",
      18
     ],
     [
      14096,
      "rs_data",
      44
     ],
     [
      14102,
      "rs_data",
      332
     ],
     [
      14108,
      "code",
      2182
     ],
     [
      14118,
      "rs_data",
      332
     ],
     [
      14124,
      "code",
      12906
     ],
     [
      14138,
      "code",
      12236
     ],
     [
      14154,
      "code",
      12768
     ],
     [
      14162,
      "rs_data",
      64
     ],
     [
      14182,
      "code",
      16638
     ],
     [
      14200,
      "code",
      12428
     ],
     [
      14208,
      "rs_data",
      328
     ],
     [
      14214,
      "rs_data",
      324
     ],
     [
      14242,
      "rs_data",
      332
     ],
     [
      14252,
      "code",
      2426
     ],
     [
      14262,
      "rs_data",
      332
     ],
     [
      14268,
      "code",
      12906
     ],
     [
      14274,
      "rs_data",
      316
     ],
     [
      14294,
      "rs_data",
      280
     ],
     [
      14300,
      "rs_data",
      264
     ],
     [
      14306,
      "rs_data",
      279
     ],
     [
      14340,
      "rs_data",
      328
     ],
     [
      14346,
      "rs_data",
      324
     ],
     [
      14352,
      "rs_data",
      48
     ],
     [
      14358,
      "code",
      2326
     ],
     [
      14372,
      "code",
      10564
     ],
     [
      14396,
      "rs_data",
      280
     ],
     [
      14470,
      "code",
      2158
     ],
     [
      14476,
      "rs_data",
      64
     ],
     [
      14502,
      "code",
      16600
     ],
     [
      14516,
      "rs_data",
      280
     ],
     [
      14560,
      "rs_data",
      311
     ],
     [
      14586,
      "rs_data",
      279
     ],
     [
      14596,
      "rs_data",
      280
     ],
     [
      14646,
      "code",
      16607
     ],
     [
      14756,
      "rs_data",
      264
     ],
     [
      14772,
      "rs_data",
      279
     ],
     [
      14782,
      "rs_data",
      258
     ],
     [
      14792,
      "code",
      16591
     ],
     [
      14850,
      "rs_data",
      264
     ],
     [
      14882,
      "code",
      2158
     ],
     [
      14888,
      "rs_data",
      64
     ],
     [
      14908,
      "code",
      16600
     ],
     [
      14972,
      "code",
      2158
     ],
     [
      14978,
      "rs_data",
      64
     ],
     [
      15004,
      "code",
      16600
     ],
     [
      15018,
      "code",
      10520
     ],
     [
      15092,
      "rs_data",
      78
     ],
     [
      15132,
      "rs_data",
      264
     ],
     [
      15148,
      "rs_data",
      276
     ],
     [
      15156,
      "code",
      2158
     ],
     [
      15166,
      "rs_data",
      64
     ],
     [
      15220,
      "code",
      16579
     ],
     [
      15230,
      "rs_data",
      256
     ],
     [
      15244,
      "code",
      12236
     ],
     [
      4,
      "rs_data",
      16
     ],
     [
      36,
      "code",
      92
     ],
     [
      78,
      "code",
      1638
     ],
     [
      15272,
      "rs_data",
      79
     ],
     [
      15286,
      "rs_data",
      64
     ],
     [
      15298,
      "rs_data",
      64
     ],
     [
      15326,
      "code",
      10678
     ]
    ],
    "symbols": {
     "rs_mix": [
      "code",
      0
     ],
     "rs_pre": [
      "code",
      92
     ],
     "rs_post": [
      "code",
      1638
     ],
     "rs_key": [
      "code",
      11730
     ],
     "rs_code": [
      "code",
      15252
     ],
     "rs_arm": [
      "code",
      1754
     ],
     "rs_stop": [
      "code",
      2102
     ],
     "rs_cancel": [
      "code",
      2148
     ],
     "rs_release": [
      "code",
      2158
     ],
     "rs_db": [
      "code",
      1586
     ],
     "rs_header": [
      "code",
      2182
     ],
     "rs_norm": [
      "code",
      2326
     ],
     "rs_pcm16": [
      "code",
      2426
     ]
    },
    "bss": 0
   },
   "order": 79,
   "mix": {
    "hook": "0x40059872",
    "stock": "4eb9400567ba",
    "symbol": "rs_mix"
   },
   "key": {
    "hook": "0x40024482",
    "stock": "42a72f034eb94006ba902f034eb94006ba204fef000c",
    "symbol": "rs_key"
   },
   "code": {
    "hook": "0x4007240c",
    "stock": "206f00042028",
    "symbol": "rs_code"
   },
   "ram": [
    "0x42800000",
    "0x43000000"
   ],
   "ring_bytes": 2304,
   "conv_bytes": 32768,
   "shift": {
    "track": 3,
    "main": 0,
    "usb": 0
   },
   "claims": {
    "ram": [
     [
      1115684864,
      1124073472
     ]
    ],
    "gestures": [
     {
      "combo": "SETTINGS + RECORD",
      "atoms": [
       [
        "SETTINGS",
        "RECORD"
       ]
      ],
      "situation": "any",
      "scope": "all",
      "meaning": "opens the RESAMPLE page (RECORD on it arms, RETURN or SETTINGS + RECORD closes it)",
      "replaces": "the toggle of GRID RECORDING while SETTINGS is held (notes/79 §1)"
     }
    ]
   }
  },
  "transpose": {
   "id": "transpose",
   "version": "0.3",
   "roots": [
    "tr_keys",
    "tr_kbt",
    "tr_pitch",
    "tr_frame",
    "tr_led",
    "tr_reload"
   ],
   "patch_points": [
    {
     "symbol": "tr_data",
     "kind": "transpose_data"
    }
   ],
   "data": {
    "size": 60,
    "sc": 0,
    "last": 4,
    "oct": 8,
    "jump": 14,
    "held": 20,
    "any": 21,
    "m1": 24,
    "m2": 32,
    "latched": 40,
    "cur": 48,
    "ph": 56,
    "known": 57,
    "n": 58,
    "dirty": 59,
    "n_value": 4
   },
   "bundle": {
    "code": "4fefffe42f027408226f00282f6f002400102029000c0680ffffffe9b480656a41f90000000020700c0070ffb088675a2408720120290010e5a97401c4802f42001408000000662e103900000000c0814a006736103900000000468174012f420014c28013c100000000202f0014241f4fef001c4e757428c0824a806722103900000000c0814a0066e02f4900282f6f00100024241f4fef001c4ef94001a0d22f48000c2f4900082f4100044eb900000000206f000c226f00082f4000184a8067c82f48000c74062f4900084eb900000000222f0004206f000c226f0008b48067a814390000000043f9000000008282740113c10000000022085981b481643c75b1080e220852812f4200187581b4af001867501381080e4a91670870012051114000132f2f00104eb9400760ba588f202f0014241f4fef001c4e75733108087405b488670674ff2f420018d2af001874feb4816e167402b4816c0272021381080860b442011381080e60ac72fe1381080860a42f032f2f00084eb900000000508f4e754eb9400cf8664a80671a2f004eb94000eb902f004eb940012442508f7206b28065024e7570064e752f02222f000c2001068010042afee588204024102f3c404a8c682f2f00142f012f2f00144eb940005f864fef00107037b0826518206f0010b1fc000001026710206f0010b1fc000002026720241f4e757007c082e682206f0014d1c2121024007001e5a880811080241f4e757007c082e682206f0018d1c2121024007001e5a88081108060e22f0a247c4007faf4487800054e92588f4a806748487800014e92588f4a80663c487800024e92588f4a8066304eb9400cf9a824404a8067242f004eb94006b978588f4a0066162f0a4eb94006bb18588f245f4a0057c0710044804e75245f42804e752f2f00044eb940016da6588f7205b2af00086516226f000841f900000000123098084881c3fc000cd081723cb2806c04703c4e7572c4b2806ff870c44e754feffff048d7041c2f2f00144eb940058474588f207940a7887c4a88670000d6122877f2142877f3162877f479a877f5244479827418e5a97583260448434243e18a8283260a82838282b2b9000000006700009223c100000000428145f90000000042047406158418081584180e5281b48166ee2240428143e9002275b2180e4a82673077517801b88267467804b882674c55824a826640307cfb00d1c3b1fc000027ff6f24b1fc000058006f04307c58003288528143e900427406b48166bc4cd7041c4fef00104e75307c2800328860e2307cf90060c4307c050060be307c070060b82240428145f90000000043e90022608872ff6000ff522f022f2f00182f2f00182f2f00182f2f00182f2f00184eb9400107d84fef00144a006716428141f90000000042021182180e52817406b48166f2241f4e754fefffd448d7440c42af001c42af002042af002442af00284aaf0030670a4eb9000000004a8066484203240f06820000002445f90000000042814def001c2042101e1580181814188082158218205281740880831600b48166e64a0056c04cd7440c448013c0000000004fef002c4e754eb90000000045f90000000072062f400014b280670000c2242f0014713228084a806d0000ca240f0682000000242f02223c000000004def00202f0e487801024878000f2f2f00402f41002c2f40002420414e904fef0014202f00104a80670000c253804a80670001122f0270022f0e2f00487800102f2f0040206f002c4e904fef001491c8222f00142608528371b2180e223c00000102b680670000aa7001b088650000ac2f022f0e2f01486800082f2f0040206f002c4e904fef0014222f001420432608528371b2180e223c00000102b68066c8606e240f06820000002442034def001c428120426000fee4240f72ff068200000024b280670000a22f024def00202f0e487800024878000f2f2f004041f9000000002f48002c4e904fef0014203c000001022f022f0e2f00487800102f2f0040206f002c4e904fef001491c86000ff4272027001b0886400ff582f022f0e2f01486800092f2f0040206f002c4e904fef00147004b0836600ff504203204242816000fe582f02203c000002022f0e2f00487800102f2f0040206f002c4e904fef001491c86000feea2f02203c000000004def00202f0e487802024878000f2f2f00402f40002c20404e904fef0014203c000001026000ff5c70ff4fefffd448d73cfc2a6f00307c012e2f003445f900000000320defae33c08c0000001f41002b28464a3900000000660a4a3900000000670001e671b900000000740622005581b4816402700412390000000077815283b68065000172420122474283428213c10000000073b9000000000501670000c8183228282203b68065069280b28064fa4a816600016c7b847db22830ba86670000a6e18d2c052a02eb8d8c8533c68c0000024e717bf9fc08c004367c003f7df9fc08c0042045538b91c64a886d00011ab1fc0000010f6e044a8b66e27a0833c58c00000a4e717bf9fc08c004367c003f7df9fc08c0042045538b91c64a886d0000f0b1fc0000010f6e044a8b66e27cf733c68c0000064e717bf9fc08c004367c003f7df9fc08c0042045538b91c64a886d0000c6b1fc0000010f6e044a8b66e2828415812830528252837207b2826600ff24b3c0650693c0b3c064fa4a89671a103278187401b489670000e0123278202c0d808171808c802a46102f002b320d2c0c42831580782815817830200d428171801439000000008c8213c60000000075b900000000030267141432183018321828b9824a0256c275024482868252817407b48166da13c3000000004cd73cfc4fef002c4e7552812247428213c100000000d3c36000fe8e41e82c016000fee241e82c016000ff0c41e82c016000ff361a32281853814a8167101232282082852a018a847b856000fe80220482851c0122057b866000fe721581782815817830200d12390000000082864cd73cfc13c1000000004fef002c4e7571802a0d2c0c42838a80102f002b2a45320d15807828200d71801581783042811439000000008c8213c6000000006000ff262f2f00084eb900000000588f4ef940076ca200002f092f02720012002f014eb900000000508f225f720078154ef940059df40000000000000001ffffffff0000000200000003ffffffffffffffff0000000400000005",
    "relocs": [
     [
      34,
      "code",
      2286
     ],
     [
      74,
      "tr_data",
      20
     ],
     [
      86,
      "tr_data",
      20
     ],
     [
      102,
      "tr_data",
      20
     ],
     [
      128,
      "tr_data",
      20
     ],
     [
      174,
      "code",
      562
     ],
     [
      206,
      "code",
      388
     ],
     [
      228,
      "tr_data",
      20
     ],
     [
      234,
      "tr_data",
      0
     ],
     [
      244,
      "tr_data",
      20
     ],
     [
      686,
      "tr_data",
      0
     ],
     [
      798,
      "tr_data",
      4
     ],
     [
      808,
      "tr_data",
      4
     ],
     [
      816,
      "tr_data",
      0
     ],
     [
      956,
      "tr_data",
      0
     ],
     [
      1012,
      "tr_data",
      0
     ],
     [
      1066,
      "code",
      562
     ],
     [
      1086,
      "tr_data",
      0
     ],
     [
      1136,
      "tr_data",
      21
     ],
     [
      1148,
      "code",
      388
     ],
     [
      1154,
      "tr_data",
      0
     ],
     [
      1196,
      "code",
      428
     ],
     [
      1422,
      "code",
      428
     ],
     [
      1564,
      "code",
      428
     ],
     [
      1630,
      "tr_data",
      0
     ],
     [
      1652,
      "tr_data",
      21
     ],
     [
      1660,
      "tr_data",
      59
     ],
     [
      1670,
      "tr_data",
      58
     ],
     [
      1688,
      "tr_data",
      56
     ],
     [
      1712,
      "tr_data",
      56
     ],
     [
      1718,
      "tr_data",
      57
     ],
     [
      2004,
      "tr_data",
      57
     ],
     [
      2012,
      "tr_data",
      57
     ],
     [
      2018,
      "tr_data",
      57
     ],
     [
      2056,
      "tr_data",
      59
     ],
     [
      2078,
      "tr_data",
      56
     ],
     [
      2164,
      "tr_data",
      57
     ],
     [
      2176,
      "tr_data",
      57
     ],
     [
      2220,
      "tr_data",
      57
     ],
     [
      2228,
      "tr_data",
      57
     ],
     [
      380,
      "code",
      660
     ],
     [
      2242,
      "code",
      1034
     ],
     [
      2268,
      "code",
      1608
     ]
    ],
    "symbols": {
     "tr_keys": [
      "code",
      0
     ],
     "tr_kbt": [
      "code",
      372
     ],
     "tr_pitch": [
      "code",
      722
     ],
     "tr_frame": [
      "code",
      2236
     ],
     "tr_led": [
      "code",
      2256
     ],
     "tr_reload": [
      "code",
      972
     ]
    },
    "bss": 0
   },
   "sites": {
    "keys": {
     "vtable": "0x400ff9cc",
     "stock_ptr": "0x4001a0d2",
     "symbol": "tr_keys"
    },
    "kbt": {
     "at": "0x4001a164",
     "stock": "4eb940016da6",
     "op": "jsr",
     "symbol": "tr_kbt"
    },
    "pitch": {
     "at": "0x400597a8",
     "stock": "4eb940058474",
     "op": "jsr",
     "symbol": "tr_pitch"
    },
    "frame": {
     "at": "0x40006a76",
     "stock": "4eb940076ca2",
     "op": "jsr",
     "symbol": "tr_frame"
    },
    "led": {
     "at": "0x40059dea",
     "stock": "76ff781533c38c000000",
     "op": "jmp",
     "symbol": "tr_led"
    },
    "reload_tap": {
     "at": "0x4001c19c",
     "stock": "4eb9400107d8",
     "op": "jsr",
     "symbol": "tr_reload"
    },
    "reload_yes": {
     "at": "0x4001b884",
     "stock": "4eb9400107d8",
     "op": "jsr",
     "symbol": "tr_reload"
    },
    "reload_menu": {
     "at": "0x4002cad0",
     "stock": "4eb9400107d8",
     "op": "jsr",
     "symbol": "tr_reload"
    }
   },
   "order": 81,
   "claims": {
    "gestures": [
     {
      "combo": "MACHINES + TRIG 8/TRIG 9/TRIG 11/TRIG 12",
      "atoms": [
       [
        "MACHINES",
        "TRIG 11"
       ],
       [
        "MACHINES",
        "TRIG 12"
       ],
       [
        "MACHINES",
        "TRIG 8"
       ],
       [
        "MACHINES",
        "TRIG 9"
       ]
      ],
      "situation": "keys",
      "scope": "all",
      "meaning": "the active track's pitch jumps -7 / -5 / +5 / +7 semitones from its PITCH; the jump in force again: back",
      "replaces": "plays the note on the TRIG keyboard, as without MACHINES"
     },
     {
      "combo": "MACHINES + TRIG 15/TRIG 16",
      "atoms": [
       [
        "MACHINES",
        "TRIG 15"
       ],
       [
        "MACHINES",
        "TRIG 16"
       ]
      ],
      "situation": "keys",
      "scope": "all",
      "meaning": "the TRIG keyboard an octave down / up, two at most, on top of KBT",
      "replaces": "plays the note on the TRIG keyboard, as without MACHINES"
     }
    ]
   }
  },
  "perform": {
   "id": "perform",
   "version": "0.4",
   "roots": [
    "pk_seq_d0",
    "pk_seq_d2",
    "pk_seq_fp",
    "pk_ui",
    "pk_pattern",
    "pk_code",
    "pk_ser",
    "pk_ksave",
    "pk_kload",
    "pk_drop",
    "pk_off_paste",
    "pk_off_cut",
    "pk_off_clear",
    "pk_main"
   ],
   "patch_points": [
    {
     "symbol": "pk_data",
     "kind": "perform_data"
    },
    {
     "symbol": "pk_held",
     "kind": "perform_held"
    }
   ],
   "data": {
    "size": 8516,
    "on": 0,
    "home": 1,
    "left1": 2,
    "which": 3,
    "taken": 4,
    "held": 5,
    "buf": 8,
    "buf_bytes": 696,
    "temp": 1400,
    "temp_bytes": 12,
    "big": 1420,
    "view": 1412,
    "next": 1416
   },
   "bundle": {
    "code": "4fefffec48d7030342c12f4100102f004eb900000000588f222f001044c14cd703034fef001423c040a788884e754fefffec48d7030342c12f4100102f024eb900000000588f222f001044c14cd703034fef001423c240a788884e754fefffec48d7030342c12f4100102f164eb900000000588f222f001044c14cd703034fef001423d640a788884e754e56ffec2f0a2f024ab940fe41786700009a486efff4240e0682fffffff02f2e00082f024eb9400f980c4878009c4eb9400802e04fef00102d40ffec4a8067602f022f004eb9400747c0487800104eb9400802e0204070012140000421400008202effec20bc400fbf402d48fffc2140000c2d40fff84eb9400d09742f004eb9400060d842a7486efff82f004eb94007700e486efffc4eb9400cf23c4fef00202f024eb9400f7d5c588f242effe4246effe84e5e4e751239000000002f0a2f024a01674671b90000000074017381b5805381c2fc1bb6c0fc02b80681409c9c8022412440d5fc00000000200a204a0680000002b422d8b08866fa42002041316a02b402b413c000000000241f245f4e754fefffe848d7007c2f6f001c001440c4200400800000070046c04eb90000000077b90000000073b9000000003403c2fc02b806810000000020012041c4fc1bb60680000002b40682409c9c80224222d8b08866fa4200204143e802b42042315102b413c0000000002f39800017e44eb94005950e46c44eb9400cf86642a72f0342822040486800744eb9400d1f984fef00102002e68841f9000000007207c282d1c0162805787001e3a87983030467204680c083114005784eb9400cf8662f02487800012f004eb94001002c4fef000c52827060b08266ba2039000000004a80670a2f004eb940076082588f4aaf0014660a4cd7007c4fef00184e754cd7007c41f9000000002f48001c4fef00184ef9000000004fefffe82f032f024a3900000000673e206f0024b1fc409c9c7f633220080680bf6363800c80000a643f62222200243c00001bb64c42100130012f410010c0fc1bb622000681409c9c80b288670a241f261f4fef00184e751239000000001f41001b7381b2af001067e42f40000c2f4100084eb900000000143900000000206f0024222f0008202f000c0680409c9f34324274012609b5832f43001c77833403c4fc02b82242d3fc000000002f49001422d8b08866fa206f0024c2fc1bb643e802b4206f0014315102b4226f00242041d1fc409c9c8020010680409c9f342f48001422d8b08866fa226f0014102f001b41e902b4226f0024335002b443ef001f41ef0013241f528013c000000000261f13d10000000013d0000000004fef00184e754feffff42f024a3900000000670000824a3900000000677840c1200100800000070046c04a39000000006762103900000000675a718075b9000000005380c4fc1bb6c0fc1bb62042d1fc409c9c802240d3fc409c9c802f48000c2f49000820490680409c9f34226f000c22d8b08866fa206f000843e802b4206f000c315102b42f4100044eb900000000222f000446c1241f4fef000c4e75207900000000598f4a88670c2f2f000c2f2f000c4e90508f202f000823c0000000004a390000000067144eb9400cf9a82f004eb94006b704588f4a006704588f4e75206f000c226800104a8967f07001b0a800046ce82028000806800000001f2200ea812e81721fb2806cd22017b0a8000c6eca41f10c002008204920fcaaaaaaaab1c066f64280206f000c22005280d2a8000c207c5555555523881c00b097679c206f000c22005280d2a8000c207c5555555523881c00b09766cc6080518f2f024a3900000000660000b04eb9400cfd0e2f004eb94006a96c588f2400705fb0826500009040c02f40000800800000070046c071b900000000223c00001bb64c021800c0fc02b82041d1fc409c9c802f4800040680000000000681409c9f34224022d8b28866fa226f000413c20000000041e902b422404200335002b413c000000000700113c000000000202f000846c02039000000004a80670a2f004eb940076082588f4879000000004eb900000000588f241f508f4e75487800014eb900000000588f241f508f4e754a390000000066024e7542a74eb900000000588f4e75420041f90000000013c00000000013c0000000004218b1fc0000000066f62039000000004a80670a2f004eb940076082588f4e754fefffdc48d71cfc266f0028760349f900000000203c0000000040c5220500810000070046c11839000000001e141c3900000000123900000000241446c54a07670000ac7984c8fc1bb62044d1fc409c9c80b1cb671e79864a06670000925384c8fc1bb62044d1fc409c9c80b1cb667e7801b981738141f9000000002248244bc2fc02b806810000000022dab3fc0000000066f643eb1bb433d100000000224120d9b1c066fa204143e802b433d10000000040c1280100840000070046c44a3900000000670e2814b982028200ffffff4a82672646c153834a836600ff3e203c000000004cd71cfc4fef00244e75200b4cd71cfc4fef00244e7546c1203c0000000060e0518f2f024a39000000006742705fb0af0010653a73b900000000b2af0010662e7460b4af0014672c40c02f40000400800000070046c04a3900000000670a71b900000000b2806730202f000446c0241f508f4e757007c081e6892041d1fc000000001228057824007001e5a8808111400578241f508f4e75223c00001bb64c01080073b900000000c2fc02b82040d1fc409c9c802f4800080680409c9f34068100000000224122d8b08866fa226f0008202f000441e902b42241335002b446c0608c518f4a3900000000673c4a2f001767367060b0af0010672e73b900000000b2af000c662240c02e8000800000070046c04a3900000000670a71b900000000b2806708201746c0508f4e75223c00001bb64c01080073b900000000c2fc02b82040d1fc409c9c802f4800040680409c9f34068100000000224122d8b08866fa226f0004201741e902b42241335002b446c060b44a3900000000663a2f2f00044eb9400724a0588f4a8067284878000d4eb94007faf4588f4a8066084a39000000006710700113c0000000004eb90000000070014e752f2f00044eb940072470588f4a8067ec420013c000000000700160e24eb9000000004feffff448d7001c4ef94000f3722f024eb900000000588f4a80660847f9400cf9a84e75588f76014ef9400212c6206f0004700db0a8000c660c7001c0a8001013c0000000002028000c4e7500002f2f00084eb900000000588f2f4000084fefffe448d77c0c4ef94005b2b62f022f044eb900000000508f4fefffe448d77c0c4ef94005b2b62f2f000c2f2f000c2f2f000c4eb94005d0804fef000c2f002f002f032f024eb9000000004fef000c201f4e754eb9000000004e56fff82f0b4ef94000eb1800004eb9000000004e56ffc448d73c7c4ef940010c824eb9000000004e56ffc448d73c7c4ef9400119144eb9000000004e56ffb4122e00134ef940011a86506572666f726d204b6974204f464600506572666f726d204b6974204f4e00",
    "relocs": [
     [
      322,
      "pk_data",
      2
     ],
     [
      336,
      "pk_data",
      3
     ],
     [
      368,
      "pk_data",
      8
     ],
     [
      400,
      "pk_data",
      2
     ],
     [
      438,
      "code",
      320
     ],
     [
      444,
      "pk_data",
      1
     ],
     [
      450,
      "pk_data",
      3
     ],
     [
      462,
      "pk_data",
      8
     ],
     [
      510,
      "pk_data",
      0
     ],
     [
      562,
      "pk_data",
      0
     ],
     [
      628,
      "pk_data",
      1412
     ],
     [
      668,
      "code",
      2556
     ],
     [
      682,
      "code",
      138
     ],
     [
      696,
      "pk_data",
      0
     ],
     [
      776,
      "pk_data",
      1
     ],
     [
      802,
      "code",
      320
     ],
     [
      808,
      "pk_data",
      3
     ],
     [
      854,
      "pk_data",
      8
     ],
     [
      952,
      "pk_data",
      2
     ],
     [
      960,
      "pk_data",
      3
     ],
     [
      966,
      "pk_data",
      1
     ],
     [
      984,
      "pk_data",
      0
     ],
     [
      994,
      "pk_data",
      2
     ],
     [
      1014,
      "pk_data",
      0
     ],
     [
      1022,
      "pk_data",
      2
     ],
     [
      1032,
      "pk_data",
      1
     ],
     [
      1110,
      "code",
      320
     ],
     [
      1130,
      "pk_data",
      1416
     ],
     [
      1158,
      "pk_data",
      1412
     ],
     [
      1164,
      "pk_data",
      0
     ],
     [
      1324,
      "pk_data",
      0
     ],
     [
      1374,
      "pk_data",
      3
     ],
     [
      1406,
      "pk_data",
      8
     ],
     [
      1430,
      "pk_data",
      1
     ],
     [
      1448,
      "pk_data",
      2
     ],
     [
      1456,
      "pk_data",
      0
     ],
     [
      1468,
      "pk_data",
      1412
     ],
     [
      1488,
      "code",
      2572
     ],
     [
      1494,
      "code",
      138
     ],
     [
      1512,
      "code",
      410
     ],
     [
      1526,
      "pk_data",
      0
     ],
     [
      1538,
      "code",
      410
     ],
     [
      1550,
      "pk_data",
      1400
     ],
     [
      1556,
      "pk_data",
      0
     ],
     [
      1562,
      "pk_data",
      2
     ],
     [
      1570,
      "pk_data",
      1412
     ],
     [
      1578,
      "pk_data",
      1412
     ],
     [
      1614,
      "pk_data",
      0
     ],
     [
      1620,
      "pk_data",
      2112
     ],
     [
      1638,
      "pk_data",
      1
     ],
     [
      1646,
      "pk_data",
      2
     ],
     [
      1652,
      "pk_data",
      3
     ],
     [
      1718,
      "pk_data",
      1420
     ],
     [
      1732,
      "pk_data",
      8
     ],
     [
      1740,
      "pk_data",
      8512
     ],
     [
      1752,
      "pk_data",
      8512
     ],
     [
      1772,
      "pk_data",
      2112
     ],
     [
      1790,
      "pk_data",
      0
     ],
     [
      1822,
      "pk_data",
      1420
     ],
     [
      1852,
      "pk_data",
      1420
     ],
     [
      1864,
      "pk_data",
      0
     ],
     [
      1880,
      "pk_data",
      1
     ],
     [
      1914,
      "pk_data",
      0
     ],
     [
      1922,
      "pk_data",
      1
     ],
     [
      1952,
      "pk_data",
      0
     ],
     [
      1990,
      "pk_data",
      3
     ],
     [
      2018,
      "pk_data",
      8
     ],
     [
      2056,
      "pk_data",
      0
     ],
     [
      2078,
      "pk_data",
      1
     ],
     [
      2102,
      "pk_data",
      0
     ],
     [
      2110,
      "pk_data",
      1
     ],
     [
      2138,
      "pk_data",
      3
     ],
     [
      2166,
      "pk_data",
      8
     ],
     [
      2200,
      "pk_data",
      4
     ],
     [
      2240,
      "pk_held",
      0
     ],
     [
      2250,
      "pk_data",
      4
     ],
     [
      2256,
      "code",
      1318
     ],
     [
      2284,
      "pk_data",
      4
     ],
     [
      18,
      "code",
      686
     ],
     [
      64,
      "code",
      686
     ],
     [
      110,
      "code",
      686
     ],
     [
      2294,
      "code",
      976
     ],
     [
      2316,
      "code",
      2198
     ],
     [
      2364,
      "pk_data",
      5
     ],
     [
      2382,
      "code",
      1598
     ],
     [
      2412,
      "code",
      1858
     ],
     [
      2464,
      "code",
      2052
     ],
     [
      2478,
      "code",
      1546
     ],
     [
      2498,
      "code",
      1524
     ],
     [
      2518,
      "code",
      1524
     ],
     [
      2538,
      "code",
      1524
     ]
    ],
    "symbols": {
     "pk_seq_d0": [
      "code",
      0
     ],
     "pk_seq_d2": [
      "code",
      46
     ],
     "pk_seq_fp": [
      "code",
      92
     ],
     "pk_ui": [
      "code",
      2292
     ],
     "pk_pattern": [
      "code",
      2312
     ],
     "pk_code": [
      "code",
      2344
     ],
     "pk_ser": [
      "code",
      2376
     ],
     "pk_ksave": [
      "code",
      2406
     ],
     "pk_kload": [
      "code",
      2432
     ],
     "pk_drop": [
      "code",
      2476
     ],
     "pk_off_paste": [
      "code",
      2496
     ],
     "pk_off_cut": [
      "code",
      2516
     ],
     "pk_off_clear": [
      "code",
      2536
     ],
     "pk_main": [
      "code",
      1128
     ]
    },
    "bss": 0
   },
   "sites": {
    "seq_queued": {
     "at": "0x40054d6a",
     "stock": "23c040a78888",
     "op": "jsr",
     "symbol": "pk_seq_d0"
    },
    "seq_stop": {
     "at": "0x40055510",
     "stock": "23d640a78888",
     "op": "jsr",
     "symbol": "pk_seq_fp"
    },
    "seq_chain": {
     "at": "0x4005571e",
     "stock": "23d640a78888",
     "op": "jsr",
     "symbol": "pk_seq_fp"
    },
    "seq_set": {
     "at": "0x40055c62",
     "stock": "23c240a78888",
     "op": "jsr",
     "symbol": "pk_seq_d2"
    },
    "ui": {
     "at": "0x4000f36a",
     "stock": "4feffff448d7001c",
     "op": "jmp",
     "symbol": "pk_ui"
    },
    "pattern": {
     "at": "0x40020ad0",
     "stock": "47f9400cf9a8",
     "op": "jsr",
     "symbol": "pk_pattern"
    },
    "ser": {
     "at": "0x4005b2ae",
     "stock": "4fefffe448d77c0c",
     "op": "jmp",
     "symbol": "pk_ser"
    },
    "ksave": {
     "at": "0x400100ba",
     "stock": "4eb94005b2ae",
     "op": "jsr",
     "symbol": "pk_ksave"
    },
    "kload": {
     "at": "0x400107a4",
     "stock": "4eb94005d080",
     "op": "jsr",
     "symbol": "pk_kload"
    },
    "drop": {
     "at": "0x4000eb12",
     "stock": "4e56fff82f0b",
     "op": "jmp",
     "symbol": "pk_drop"
    },
    "paste": {
     "at": "0x40010c7a",
     "stock": "4e56ffc448d73c7c",
     "op": "jmp",
     "symbol": "pk_off_paste"
    },
    "cut": {
     "at": "0x4001190c",
     "stock": "4e56ffc448d73c7c",
     "op": "jmp",
     "symbol": "pk_off_cut"
    },
    "clear": {
     "at": "0x40011a7e",
     "stock": "4e56ffb4122e0013",
     "op": "jmp",
     "symbol": "pk_off_clear"
    },
    "code": {
     "at": "0x4007240c",
     "stock": "206f00042028",
     "op": "jmp",
     "symbol": "pk_code",
     "unless": "resample"
    }
   },
   "order": 82,
   "main": {
    "vtable": "0x400ffe30",
    "stock_ptr": "0x4001b22a",
    "symbol": "pk_main"
   },
   "claims": {
    "gestures": [
     {
      "combo": "SETTINGS + PATTERN",
      "atoms": [
       [
        "SETTINGS",
        "PATTERN"
       ]
      ],
      "situation": "any",
      "scope": "all",
      "meaning": "switches the Perform Kit mode on and off",
      "replaces": "arms the pattern selection, as PATTERN without SETTINGS"
     }
    ]
   }
  }
 },
 "claims": {
  "control-all-config": {
   "gestures": [
    {
     "combo": "TRACK + TRIG 1-6",
     "atoms": [
      [
       "TRACK",
       "TRIG 1"
      ],
      [
       "TRACK",
       "TRIG 2"
      ],
      [
       "TRACK",
       "TRIG 3"
      ],
      [
       "TRACK",
       "TRIG 4"
      ],
      [
       "TRACK",
       "TRIG 5"
      ],
      [
       "TRACK",
       "TRIG 6"
      ]
     ],
     "situation": "any",
     "scope": "all",
     "meaning": "takes the track out of Control All, or back",
     "replaces": null
    }
   ]
  },
  "trig-preview": {
   "gestures": [
    {
     "combo": "TRIG 1-16 + PAGE",
     "atoms": [
      [
       "TRIG 1",
       "PAGE"
      ],
      [
       "TRIG 10",
       "PAGE"
      ],
      [
       "TRIG 11",
       "PAGE"
      ],
      [
       "TRIG 12",
       "PAGE"
      ],
      [
       "TRIG 13",
       "PAGE"
      ],
      [
       "TRIG 14",
       "PAGE"
      ],
      [
       "TRIG 15",
       "PAGE"
      ],
      [
       "TRIG 16",
       "PAGE"
      ],
      [
       "TRIG 2",
       "PAGE"
      ],
      [
       "TRIG 3",
       "PAGE"
      ],
      [
       "TRIG 4",
       "PAGE"
      ],
      [
       "TRIG 5",
       "PAGE"
      ],
      [
       "TRIG 6",
       "PAGE"
      ],
      [
       "TRIG 7",
       "PAGE"
      ],
      [
       "TRIG 8",
       "PAGE"
      ],
      [
       "TRIG 9",
       "PAGE"
      ]
     ],
     "situation": "grid",
     "scope": "all",
     "meaning": "the held step sounds, sequencer stopped or paused",
     "replaces": "PAGE turns the page"
    }
   ]
  }
 },
 "clash_reasons": {},
 "samples": {
  "syx_sha256": "e11859b68deb7e5e3fe86ab32581212093849c4be5d3950add011eac398a2ce8",
  "main_sha256": "a351392c62ec1c6c3324a807baf46934690d54edfc76029a4b4882541cad1ab2",
  "download": "https://www.elektron.se/support-downloads/modelsamples"
 },
 "syntakt": {
  "download": "https://www.elektron.se/support-downloads/syntakt"
 },
 "shared": []
};
(function (tw) {
  const s = tw.shared || [];
  delete tw.shared;
  const h = (v) => Array.isArray(v) ? v.map(h) : v && typeof v === "object"
    ? ("$shared" in v ? (Array.isArray(s[v.$shared]) ? JSON.parse(JSON.stringify(s[v.$shared])) : s[v.$shared])
      : Object.fromEntries(Object.entries(v).map(([k, x]) => [k, h(x)]))) : v;
  tw.tweaks = tw.tweaks.map(h);
})(window.MC_TWEAKS);
