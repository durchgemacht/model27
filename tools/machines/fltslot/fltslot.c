/* The filter slot of model27's builder, with entries.S (the track filters, notes/72). Addresses are VAs of
 * OS 1.13.
 *
 * Every track can run a filter after Volume + Dist, the place of the Model:Samples' own filter. Each sound chooses one
 * by id in the low byte of its k 32 (0 none, 1 to 239 the filters, 240 to 255 the references; bits 8 and 9 are the
 * machine's switches, notes/63 §16); a build holds at most two filters, laid out by the composer in the data block's
 * table. The id is read in the sound the track's note plays (*0x800017ec[t], its k 32 at +84, as SAMPLE reads its
 * switches), or in the copy of that sound's 66 bytes the audio side keeps (0x800015ae + 66 t) when there is none: not
 * in the smoothed words, which glide. Id 0, or an id the build does not hold: the track is not touched, bit for bit.
 *
 * fl_run, called by entries.S's fl_post in every audio block after Volume + Dist: for each track, the filter its sound
 * chose filters the track's block in place: process(block, words, track, triggered), words the track's smoothed k 28
 * to k 31 (the filter's four values, p-locks, LFO and velocity in them), triggered 1 when a note started on the track
 * in this block. When a track changes filter (another id, or a sound that chose another), the block is run through
 * both, the one that stops on a copy of the input, the one that starts after its reset, and faded from the first to
 * the second across the block's 32 frames (weights 31 - n and n + 1 over 32, on the samples shifted down by 6 bits:
 * within 32 bits whatever the samples); "none" is the input itself. The stopping filter is then reset, so that it
 * starts afresh when the track comes back to it.
 *
 * The values (since 0.2, the key map's RETRIG level): k 28 to k 31 are real parameters of every machine, descriptors
 * 1 to 4 (the OS's unused "Error" ones), as many as the build's filters declare: group 7 (every machine), 0..127 in
 * 8.8, defaults k 28 at the centre, k 29 at 0, k 30 and k 31 at the centre, k 28 on CC 74 and NRPN 1:20, k 29 on
 * CC 71 and NRPN 1:21. fl_boot writes their rows, the composer's, into the stock table and the one the OS uses before
 * the OS builds its parameter tables from them at boot (rows by machine, CC, NRPN, LFO destinations, a new sound's
 * defaults). fl_knob, ParameterPageView's knob lookup (behind the shortcut layer's or the stock one): RETRIG held +
 * SWEEP, CONTOUR, COLOR or SHAPE gives descriptor 1, 2, 3 or 4 when the build has it, also with FUNC (fine), TRACK
 * (Control All), LFO (the destination) or a trig held (a p-lock): their names and formatters are those of the filter
 * the track's sound chose, or of the build's first filter. RETRIG held + PITCH alone gives descriptor 5, the filter's
 * type, display only (group -1, k 0: the OS builds nothing on it, and an edit that slipped through would write the
 * unused k 0): its popup names the type through fl_fmt_type, and the encoder handler's turn reaches fl_step
 * (entries.S's fl_keys at 0x4001f886) before any edit, which steps the selected track's sound's id through none and
 * the build's filters, four detents a step, as the effect slots step theirs. LFO + RETRIG + a knob makes the value
 * the LFO's destination through fl_lfo_desc (since 0.4: that gesture has a knob list of its own, 0x4001eaa2). The
 * pattern's p-locks of k 23 and above
 * (the OS saves them onto other parameters or loses them, notes/47 §4.3): fl_ptab and entries.S's fl_conv.
 *
 * The record (since 0.3): entries.S's wrappers of the three sound record functions run in front of the shortcut
 * layer's, which copies k 28..31 into record slots 28..31 and k 32 into slot 18 for every sound (notes/63 §3, §16).
 * fl_saved then stores each value relative to its neutral word (the descriptor's default, XOR: the centre for k 28,
 * k 30 and k 31, 0 for k 29), so that a record that never held it (the official OS's, an older build's) loads the
 * neutral one; a value no filter of the build declares is stored as 0, its neutral after the load, so that a sound
 * made here holds no 0 there for a later filter that declares it. The LFO's and the velocity's destinations on a value
 * (k 28 to 27 + params) cannot go through the OS's tables (its save indexes 0x4010ee4c with no bound, notes/47 §4.2,
 * and the load gives back k 5 to 8): fl_saved writes "none" there (slot 0) and keeps them in slot 18, bits 10-12
 * (the LFO's, 1 for k 28) and 13-15 (the velocity's); fl_loaded, after the layer's load, puts them back and clears
 * those bits in k 32, and undoes the XOR. The official OS reads "none", and slot 18 on its unused k 0.
 *
 * Contract of a filter (a package whose uses name the point "track.filter"): process(int32_t *block, const int16_t
 * *words, uint32_t track, uint32_t triggered) and reset(uint32_t track), C ABI (d2-d7/a2-a6 kept); a filter keeps a
 * state per track (0 to 5) in its own variables. process is called with MACSR 0xa0 (fractional, saturating) and
 * acc0-acc3 clear, and may leave the EMAC as it likes: fl_post restores what the OS had.
 *
 * The load (since 0.5): fl_run times itself with the DMA timer 0 (135.168 MHz, a block is 90 112 ticks) and keeps, for
 * windows of 750 blocks (0.5 s), the average and the peak of its share of a block, the filters' and its own, in tenths
 * of a percent. A measuring build (the composer's diag) shows them instead of the values: Filter Cutoff's popup the
 * average, the type's popup the peak. In every other build they are counted and not shown.
 *
 * The state is in the part's data block (a part has no variables of its own): written by the composer, zero at boot.
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>

#define TRACKS 6
#define ENTRIES 4                                   /* none, then the build's filters (the composer allows two) */
#define PARAMS 4                                    /* k 28 to k 31, descriptors 1 to 4 */
#define FRAMES 32
#define TYPE_DESC 5                                 /* the type's descriptor, display only */
#define DETENTS 4                                   /* in one direction, for one step */
#define PAUSE 54067200u                             /* 0.4 s of the DMA timer 0 (notes/23 §5) */
#define TIMER (*(volatile uint32_t *)0xfc07000c)
#define BLOCK_TICKS 90112u                          /* a block of 32 frames at 48 kHz, in ticks of the timer */
#define WINDOW 750u                                 /* blocks a window, 0.5 s */
#define TRK ((int32_t *)0x80001858)                 /* the tracks' blocks after Volume + Dist, 32 frames each */
#define CUR_SND(t) (((const uint8_t *volatile *)0x800017ec)[t])   /* the sound the track's note plays, or 0 */
#define TARGETS(t) ((const uint8_t *)0x800015ae + 66 * (t))      /* the copy of its 66 bytes, k 0 to k 32 */
#define SOUND_K32 84                                /* a sound's k 32 (its parameters start at +20) */
#define WORDS(p, t) ((const int16_t *)((p) + 14 + 66 * (t) + 2 * 28))   /* the smoothed k 28 of track t */
#define KEY_HELD ((int32_t (*)(uint32_t))0x4007faf4)            /* (logical key) -> 1 while held */
#define K_FUNC 1
#define K_TRACK 2
#define K_RETRIG 4
#define K_LFO 8
#define UI_STATE ((void *(*)(void))0x400cf9a8)
#define TRIG_HELD ((uint8_t (*)(void *))0x4006b736)             /* (state) -> non-zero while a trig is held */
#define PROJECT ((uint8_t *(*)(void))0x400cf866)                /* the project singleton */
#define PROJECT_TRACKS ((void *(*)(uint8_t *))0x4000eb90)       /* project -> its track selection */
#define ACTIVE_TRACK ((int32_t (*)(void *))0x40012412)          /* track selection -> the selected track */
#define UI_OBJ(i) ((uint8_t *)0x40a71754 + 100 * (i))           /* descriptor i's interface object */
#define DSTRIDE 0x38

typedef void (*fl_fn)(int32_t *block, const int16_t *words, uint32_t track, uint32_t triggered);
typedef void (*fl_reset_fn)(uint32_t track);
typedef uint32_t (*lookup_fn)(void *view, uint32_t knob, uint32_t func, int32_t track);

struct names { uint32_t longn, shortn, fmt; };
struct entry {
	uint32_t id, process, reset, tag;           /* tag: the type's name on screen, 3 characters at most */
	struct names p[PARAMS];                     /* the values' names and formatters, k 28 to k 31 */
};                                                  /* 64 bytes */
struct data {
	uint32_t count;                             /* +0 the entries, the first one none */
	uint32_t params;                            /* +4 the build's values: descriptors 1 to params */
	uint32_t knob_next;                         /* +8 the lookup behind this one: the shortcut layer's, or the stock */
	uint32_t keys_next;                         /* +12 the effect slots' fx_keys at 0x4001f886, or 0 */
	uint32_t desc[2];                           /* +16 the stock descriptor table, the one the OS uses */
	struct entry e[ENTRIES];                    /* +24 entry 0 none (the first filter's names), then the filters by id */
	uint32_t rows[PARAMS + 1][14];              /* +280 the rows of descriptors 1 to 4, then 5, as fl_boot writes them */
	uint8_t cur[TRACKS];                        /* +560 the entry each track ran in its last block */
	uint8_t acc, last_dir;                      /* +566 the type's detents */
	uint32_t last_time;                         /* +568 */
	int32_t old[FRAMES];                        /* +572 in a change, the stopping filter's block */
	uint16_t neutral[PARAMS];                   /* +700 each value's neutral word, the record's XOR (since 0.3) */
	uint32_t rec_next[3];                       /* +708 the shortcut layer's save2, save1 and load wrappers */
	uint8_t diag, spare2[3];                    /* +720 1 in a measuring build (since 0.5) */
	uint32_t sum, peak;                         /* +724 the window's ticks and its dearest block */
	uint16_t n, avg_t, peak_t, spare3;          /* +732 its blocks; the last window's average and peak, 0.1 % */
};                                                  /* 740 bytes */

extern char fl_data[];
#define D ((struct data *)fl_data)

static uint32_t index_of(uint32_t id)
{
	for (uint32_t i = 1; i < D->count; i++)
		if (D->e[i].id == id)
			return i;
	return 0;
}

/* The entry of the filter the track's sound chose, 0 for none or an id the build does not hold. */
static uint32_t chosen(uint32_t t)
{
	const volatile uint8_t *snd = CUR_SND(t);
	return index_of(snd ? snd[SOUND_K32 + 1] : TARGETS(t)[64 + 1]);
}

static void run(uint32_t i, int32_t *block, const int16_t *words, uint32_t t, uint32_t triggered)
{
	__asm__ volatile("move.l #0xa0, %%macsr\n\t"
	                 "move.l #0, %%acc0\n\t"
	                 "move.l #0, %%acc1\n\t"
	                 "move.l #0, %%acc2\n\t"
	                 "move.l #0, %%acc3" : : : "memory");
	((fl_fn)D->e[i].process)(block, words, t, triggered);
}

static void reset(uint32_t i, uint32_t t)
{
	if (D->e[i].reset)
		((fl_reset_fn)D->e[i].reset)(t);
}

/* One block's ticks into the window; at its end, the average and the peak as tenths of a percent of a block. */
void fl_measure(uint32_t ticks)
{
	D->sum += ticks;
	if (ticks > D->peak)
		D->peak = ticks;
	if (++D->n < WINDOW)
		return;
	D->avg_t = (uint16_t)((D->sum / WINDOW) * 1000u / BLOCK_TICKS);
	D->peak_t = (uint16_t)(D->peak * 1000u / BLOCK_TICKS);
	D->sum = D->peak = 0;
	D->n = 0;
}

static int filter_blocks(const uint8_t *params, uint32_t triggered);

/* entries.S's fl_post: params the smoothed parameters (the audio function's a2), triggered the block's triggered
 * tracks (bit t). Returns 1 when a filter ran, 0 when no track was touched. Timed (fl_measure). */
int fl_run(const uint8_t *params, uint32_t triggered)
{
	uint32_t t0 = TIMER;
	int ran = filter_blocks(params, triggered);
	fl_measure(TIMER - t0);
	return ran;
}

static int filter_blocks(const uint8_t *params, uint32_t triggered)
{
	int ran = 0;
	for (uint32_t t = 0; t < TRACKS; t++, triggered >>= 1) {
		int32_t *block = TRK + FRAMES * t;
		const int16_t *words = WORDS(params, t);
		uint32_t i = chosen(t), was = D->cur[t], n;
		if (i == was) {
			if (i) {
				run(i, block, words, t, triggered & 1);
				ran = 1;
			}
			continue;
		}
		D->cur[t] = (uint8_t)i;
		for (n = 0; n < FRAMES; n++)
			D->old[n] = block[n];
		if (was)
			run(was, D->old, words, t, triggered & 1);
		if (i) {
			reset(i, t);
			run(i, block, words, t, triggered & 1);
		}
		for (n = 0; n < FRAMES; n++)
			block[n] = ((D->old[n] >> 6) * (int32_t)(FRAMES - 1 - n) + (block[n] >> 6) * (int32_t)(n + 1)) * 2;
		if (was)
			reset(was, t);
		ran = 1;
	}
	return ran;
}

/* entries.S's fl_boot, before the OS builds its parameter tables: the rows of the build's descriptors 1 to params and
 * of descriptor 5 into the stock table and the one the OS uses (the same table in a build without an added machine). */
void fl_rows(void)
{
	for (uint32_t k = 0; k < 2; k++) {
		for (uint32_t r = 0; r <= PARAMS; r++) {
			uint32_t d = r < PARAMS ? r + 1 : TYPE_DESC;
			volatile uint32_t *row = (volatile uint32_t *)(D->desc[k] + DSTRIDE * d);
			if (r < PARAMS && r >= D->params)
				continue;
			for (uint32_t j = 0; j < 14; j++)
				row[j] = D->rows[r][j];
		}
	}
}

static int32_t selected(void)
{
	uint8_t *p = PROJECT();
	return p ? ACTIVE_TRACK(PROJECT_TRACKS(p)) : -1;
}

/* Track t's sound in the project (the project's track at +212 + 68 t, the sound from the method at +40 of its
 * vtable, as the shortcut layer and the dispatchers find it), or 0. */
static uint8_t *sound_of(int32_t t)
{
	uint8_t *p, *track;
	void **vt;
	if (t < 0 || t >= TRACKS || !(p = PROJECT()))
		return 0;
	track = p + 212 + 68 * t;
	vt = *(void ***)track;
	return vt && vt[10] ? ((uint8_t *(*)(uint8_t *))vt[10])(track) : 0;
}

/* The entry whose names the values show on track t: its sound's filter, or the build's first one. */
static uint32_t named(int32_t t)
{
	uint8_t *snd = sound_of(t < 0 ? selected() : t);
	uint32_t i = snd ? index_of(snd[SOUND_K32 + 1]) : 0;
	return i;
}

static void name_value(uint32_t p, uint32_t i)
{
	const struct names *n = &D->e[i].p[p];
	for (uint32_t k = 0; k < 2; k++) {
		volatile uint32_t *row = (volatile uint32_t *)(D->desc[k] + DSTRIDE * (p + 1));
		row[0x2c / 4] = n->longn;
		row[0x34 / 4] = n->shortn;
	}
	*(volatile uint32_t *)(UI_OBJ(p + 1) + 0x20) = n->fmt;
	*(volatile uint32_t *)(UI_OBJ(p + 1) + 0x2c) = 0;       /* no "Error" picture */
}

void fl_fmt_type(void *fn, int32_t v, char *buf);

static const uint8_t knob_value[4] = {2, 3, 0, 1};          /* COLOR, SHAPE, SWEEP, CONTOUR -> k 30, 31, 28, 29 */

/* ParameterPageView's knob lookup (its vtable's +0x7c, 0x401005a8): (view, knob, FUNC, track or -1) -> the
 * descriptor under the knob (notes/47 §3.2; PITCH is knob 2, COLOR to CONTOUR 4 to 7). */
uint32_t fl_knob(void *view, uint32_t knob, uint32_t func, int32_t track)
{
	uint32_t d = ((lookup_fn)D->knob_next)(view, knob, func, track);
	if ((knob != 2 && (knob < 4 || knob > 7)) || !KEY_HELD(K_RETRIG))
		return d;
	if (knob == 2) {                            /* the type: RETRIG + PITCH alone */
		if (D->count < 2 || KEY_HELD(K_FUNC) || KEY_HELD(K_TRACK) || KEY_HELD(K_LFO) || TRIG_HELD(UI_STATE()))
			return d;
		uint8_t *o = UI_OBJ(TYPE_DESC);
		*(volatile uint32_t *)(o + 0x10) = *(volatile uint32_t *)(UI_OBJ(1) + 0x10);  /* the knob's steps */
		*(volatile uint32_t *)(o + 0x20) = (uint32_t)fl_fmt_type;
		*(volatile uint32_t *)(o + 0x2c) = 0;
		return TYPE_DESC;
	}
	uint32_t p = knob_value[knob - 4];
	if (p >= D->params)
		return d;
	name_value(p, named(track));
	return p + 1;
}

/* entries.S's fl_lfo, in LFO + a knob (0x4001eaa2), which sets the LFO's destination from the machine record's knob list
 * and not from the knob lookup: knob 0 PITCH, 1 DECAY, 2..5 COLOR..CONTOUR, stock the list's descriptor. With RETRIG
 * held, COLOR to CONTOUR give the filter's values the build has, as fl_knob does; anything else the list's. Since 0.4. */
uint32_t fl_lfo_desc(uint32_t knob, uint32_t stock)
{
	uint32_t p;
	if (knob < 2 || knob > 5 || !KEY_HELD(K_RETRIG))
		return stock;
	p = knob_value[knob - 2];
	return p < D->params ? p + 1 : stock;
}

/* A share in tenths of a percent, three characters: "6.4" below 10 %, "12" from there, "99" at most. */
static void share(uint32_t t, char *buf)
{
	if (t < 100) {
		buf[0] = (char)('0' + t / 10), buf[1] = '.', buf[2] = (char)('0' + t % 10), buf[3] = 0;
		return;
	}
	t = t >= 1000 ? 99 : t / 10;
	buf[0] = (char)('0' + t / 10), buf[1] = (char)('0' + t % 10), buf[2] = 0;
}

/* The type's formatter (fn, v, buffer): the name of the filter the selected track's sound chose, "OFF" for none; in a
 * measuring build the last window's peak load. */
void fl_fmt_type(void *fn, int32_t v, char *buf)
{
	const char *s;
	(void)fn;
	(void)v;
	if (D->diag) {
		share(D->peak_t, buf);
		return;
	}
	s = (const char *)D->e[named(-1)].tag;
	while ((*buf++ = *s++))
		;
}

/* Filter Cutoff's formatter, as SAMPLE's (smp_fmt_cutoff) and the Model:Samples': -64 .. -1 the lowpass side, 0 off,
 * 1 .. 63 the highpass side (since 0.6; L64 .. OFF .. H63 before, too close to Pan's L), three characters at most (the
 * screen shows no more, notes/47 §5); in a measuring build the last window's average load. */
void fl_fmt_cut(void *fn, int32_t v, char *buf)
{
	int32_t d = (v - 0x4000) >> 8;
	(void)fn;
	if (D->diag) {                              /* a measuring build: the last window's average load */
		share(D->avg_t, buf);
		return;
	}
	if (d < 0) {
		*buf++ = '-';
		d = -d;
	}
	if (d >= 10)
		*buf++ = (char)('0' + d / 10);
	*buf++ = (char)('0' + d % 10);
	*buf = 0;
}

/* entries.S's fl_keys, at the encoder handler's question for TRACK (0x4001f886) on descriptor 5: step, the handler's
 * step (16 bits, signed). Four detents in one direction make one step; the count starts again after a change of
 * direction or 0.4 s without a detent. A step moves the selected track's sound's id to the next or previous entry
 * of the table (none first, then the filters by id) and stops at the ends; an id the build does not hold counts as
 * none. The audio reads it in the next block. */
void fl_step(int32_t step)
{
	uint32_t now = TIMER;
	uint8_t dir = step > 0 ? 1 : 2, *snd;
	if (dir != D->last_dir || now - D->last_time > PAUSE)
		D->acc = 0;
	D->last_dir = dir;
	D->last_time = now;
	if (++D->acc < DETENTS)
		return;
	D->acc = 0;
	if (!(snd = sound_of(selected())))
		return;
	uint32_t i = index_of(snd[SOUND_K32 + 1]);
	if (dir == 1 ? i + 1 >= D->count : i == 0)
		return;                                 /* at the end of the table */
	snd[SOUND_K32 + 1] = (uint8_t)D->e[dir == 1 ? i + 1 : i - 1].id;
}

static uint32_t rd16(const uint8_t *a)
{
	return (uint32_t)a[0] << 8 | a[1];
}

static void wr16(uint8_t *a, uint32_t v)
{
	a[0] = (uint8_t)(v >> 8);
	a[1] = (uint8_t)v;
}

/* entries.S's fl_save2 and fl_save1, after the layer's wrapper and the save (version 2 or 1) did their work: the
 * record's slots 28..31 (+84) relative to the neutral words, the values no filter declares at 0; the destinations on
 * a value into slot 18 (+64), bits 10-12 and 13-15, and "none" in their own places, slot 4 (+36, the LFO's slot << 8)
 * and +94 (the velocity's slot), as the save writes them for k 0. */
void fl_saved(uint8_t *rec, const uint8_t *snd)
{
	uint32_t s18 = rd16(rec + 64) & 0x03ff, lfo = snd[28];
	uint32_t vel = (uint32_t)snd[88] << 24 | (uint32_t)snd[89] << 16 | (uint32_t)snd[90] << 8 | snd[91];
	for (uint32_t p = 0; p < PARAMS; p++)
		wr16(rec + 84 + 2 * p, p < D->params ? rd16(snd + 76 + 2 * p) ^ D->neutral[p] : 0);
	if (lfo - 28 < D->params) {
		s18 |= (lfo - 27) << 10;
		wr16(rec + 36, 0);
	}
	if (vel - 28 < D->params) {
		s18 |= (vel - 27) << 13;
		rec[94] = 0;
	}
	wr16(rec + 64, s18);
}

/* entries.S's fl_load, after the layer's wrapper and the load did their work: k 28..31 from the XOR back to words,
 * the destinations kept in k 32's bits 10-15 (the layer copied slot 18 there) back on k 4's high byte (+28, as the
 * load writes a destination, k << 8) and the long at +88, those bits cleared. A destination the build has no value
 * for stays the load's, none. */
void fl_loaded(uint8_t *snd, const uint8_t *rec)
{
	uint32_t k32 = rd16(snd + 84), l = k32 >> 10 & 7, v = k32 >> 13 & 7;
	(void)rec;
	for (uint32_t p = 0; p < PARAMS; p++)
		wr16(snd + 76 + 2 * p, rd16(snd + 76 + 2 * p) ^ D->neutral[p]);
	if (l && l <= D->params)
		wr16(snd + 28, (27 + l) << 8);
	if (v && v <= D->params) {
		snd[88] = snd[89] = snd[90] = 0;
		snd[91] = (uint8_t)(27 + v);
	}
	wr16(snd + 84, k32 & 0x03ff);
}
