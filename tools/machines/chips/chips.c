/* CHIPS for model27 (notes/83): an added machine, Plaits' hard-synced square and its 32-step triangle bass, with an
 * arpeggio inside the note, as old sound chips play chords, and a pitch sweep at every trig.
 *
 * Origin and license: the square and the bass follow Plaits' SuperSquareOscillator and NESTriangleOscillator<5>
 * (plaits/dsp/oscillator/super_square_oscillator.h, nes_triangle_oscillator.h), the slave's ratio and
 * shape = MORPH x 0.995 Plaits' ChiptuneEngine (plaits/dsp/engine2/chiptune_engine.cc): Mutable Instruments Plaits,
 * eurorack 08460a6, MIT, Copyright 2016-2021 Emilie Gillet (LICENSE-Plaits next to this file). Their steps are the
 * template, written anew here in fixed point; no line of its C++ is copied as is. The chords are Plaits' chord bank's
 * (plaits/dsp/chords/chord_bank.cc: its names, its notes folded into one octave as its Sort does; the tables from
 * tools/gen_chips.py); the arpeggio inside the note and the sweep are not Plaits'. This file: model27's own work
 * (durchgemacht and Claude), MIT,
 * LICENSE next to this file. The fixed point was checked against Plaits' unchanged oscillators on the host
 * (notes/83 §3).
 *
 *     COLOR    Wave: the square's waveform, Plaits' MORPH: below 64 a narrowing pulse, 64 about a square, above it
 *              the synced square's overtones (shape = COLOR / 127 x 0.995)
 *     SHAPE    Chord: Plaits' eleven chords within one octave, a zone of 11 or 12 values each over 0 to 127, its
 *              name on the display: OCT (one tone, a mono synth), 5, SUS (sus4), m, m7, m9, m11, 69, M9, M7, M
 *              (notes/83 §10, §11)
 *     SWEEP    Sweep: at every trig the note starts above (over 64) or below (under 64) its pitch, by
 *              ((SWEEP - 64) / 63)^2 x 48 semitones, and falls onto it exponentially (30 ms); 64 none
 *     CONTOUR  Arp: the arpeggio's tempo, no off (SHAPE's OCT is one tone; the maintainer's choice of
 *              2026-11-16, notes/83 §9); 0 to 63 a division of the song's tempo (1/4 from 0 to 9, then 1/4T, 1/8,
 *              1/8T, 1/16, 1/16T, 1/32, 9 values each); 64 to 127 free, 16 to 64 changes a second, exponential
 *     MACHINES + PUNCH   the bass on: the triangle an octave below the tone the arpeggio plays, with the sweep
 *     MACHINES + GATE    the arpeggio up and down (off: up)
 *     PUNCH    the stock PUNCH, and the bass as loud as the square at its peak (off: 6 dB below)
 *     DECAY, GATE: the stock amp chain, set up the way TONE sets it, PUNCH's output stage too (TONE's level; the
 *              maintainer took SOLID's 6 dB back out on 2026-11-15, notes/83 §7)
 *
 * The arpeggio starts on the root at every trig; its first change comes one step later. Its changes fall on a
 * block's start; the frequency changes there, phase-continuous. The oscillators run on (no phase reset at a trig, as
 * Plaits); while the envelope is closed and no trig comes, the core is not called and stands still, as SWARM's.
 * The maintainer's choices of 2026-11-15 (notes/83 §2).
 *
 * Once a block of 32 frames: the arpeggio's clock (a phase step a block), the sweep (a factor a block), the
 * frequencies through ex2 only when their note or COLOR moved. Per frame: the square (Plaits' steps, the slave's
 * phase counted in half periods so that each edge is one carry), the bass (its phase counted within a step so that
 * each step is one carry, the step's level from a table; above 750 Hz Plaits' fade to a naive triangle with integrated
 * BLEPs). Plaits' polyBLEP at every edge and step, the BLEP's time t = x / inc a product with a reciprocal kept with
 * the frequency, not a division.
 *
 * Every fractional product goes through the EMAC in signed fractional mode (MACSR 0xa0: saturating, truncating), on
 * the device mac.l / movclr.l, on the host (CHIPS_HOST) the same arithmetic as tools/emu/emac.py executes it, as in
 * solid.c. chips_render saves MACSR, sets 0xa0 and gives MACSR back with acc0 empty: the stock chain accumulates into
 * acc0 without clearing it. Formats: phases uint32 (1.0 = 2^32, the wrap the carry), the BLEPs' time Q30, the output
 * Q27 (1.0 = 2^27; Q31 on the bus): the square +-0.5, the bass +-0.47 (PUNCH off +-0.23); logarithms log2 in Q24,
 * notes semitones << 16, knobs 8.8. Plain C99, no libc, no float, no 64-bit arithmetic on the device. Tables:
 * chips_tables.h (tools/gen_chips.py). */
#include <stdint.h>
#include "chips_tables.h"

#define BLOCK 32
#define KNOB_MAX (127 << 8)
#define HALF 0x80000000u
#define ONE (1 << 27)               /* the square's high, Q27 (Plaits' 1.0 before 2x - 1) */
#define T1 (1 << 30)                /* 1.0 of the BLEPs' time, Q30 */
#define KX 1090785345               /* 2^44 / 16128: mul(a << 17, KX) << 1 = a / (63 << 8), Q31 */

/* --- the EMAC (as solid.c) ---------------------------------------------------------------------------------- */
#ifdef CHIPS_HOST
typedef __int128 wide;
static wide acc;
#define TRUNC(p) ((p) & ~(wide)0x7fffff)
static inline void emac_start(void) { acc = 0; }
static inline void mac(int32_t a, int32_t b) { acc += TRUNC((wide)a * b); }
static inline int32_t movclr(void)
{
	wide v = acc >> 31;
	acc = 0;
	return v > INT32_MAX ? INT32_MAX : v < INT32_MIN ? INT32_MIN : (int32_t)v;
}
static inline int clz32(uint32_t x) { return __builtin_clz(x); }
#else
static inline void emac_start(void)                 /* signed, fractional, saturating, truncating; acc0 empty */
{
	__asm__ volatile("move.l #0xa0,%%macsr\n\tmove.l #0,%%acc0" : : : "memory");
}
static inline void mac(int32_t a, int32_t b) { __asm__ volatile("mac.l %0,%1,%%acc0" : : "r"(a), "r"(b)); }
static inline int32_t movclr(void)
{
	int32_t r;
	__asm__ volatile("movclr.l %%acc0,%0" : "=d"(r));
	return r;
}
static inline int clz32(uint32_t x)                 /* ff1: the first set bit counted from the top */
{
	int r = (int)x;
	__asm__("ff1.l %0" : "+d"(r));
	return r;
}
#endif
static inline int32_t mul(int32_t a, int32_t b) { mac(a, b); return movclr(); }          /* a b / 2^31 */
static inline int32_t clamp(int32_t x, int32_t lo, int32_t hi) { return x < lo ? lo : x > hi ? hi : x; }

static uint32_t ex2(int32_t l, int q)               /* 2^(l / 2^24) x 2^q; 2^32 - 1 above, 0 below 1 (solid.c) */
{
	int e = (l >> 24) + q - 30;
	uint32_t f = (uint32_t)l & 0xffffff;
	int j = (int)(f >> 16);
	uint32_t m = EXP2_T[j] + (uint32_t)mul((int32_t)(EXP2_T[j + 1] - EXP2_T[j]), (int32_t)((f & 0xffff) << 15));

	if (e >= 2)
		return 0xffffffffu;
	if (e >= 0)
		return m << e;
	return e <= -32 ? 0 : m >> -e;
}

static inline int32_t l2inc(int32_t note)           /* log2 of the phase step (Q32) of a note in semitones << 16, Q24 */
{
	return L2_INC0 + (note - (69 << 16)) * 64 / 3;
}

/* --- the voice ---------------------------------------------------------------------------------------------- */
struct chips_in {               /* one block's inputs */
	int32_t trig;           /* a trig starts a note in this block */
	int32_t note;           /* semitones << 16 */
	int32_t color, shape, sweep, contour;           /* 8.8, 0 .. 127 */
	int32_t bass;           /* MACHINES + PUNCH: the bass on */
	int32_t updown;         /* MACHINES + GATE: the arpeggio up and down */
	int32_t bpm;            /* the song's tempo, 8.8 (the divisions) */
	int32_t punch;          /* PUNCH: the bass as loud as the square at its peak; off 6 dB below */
};

struct freq {                   /* an oscillator's frequency this block */
	uint32_t inc;           /* the phase step, Q32, 2^16 .. 2^30 (Plaits' kMaxFrequency 0.25) */
	int32_t sh;             /* inc << sh in [2^30, 2^31) */
	int32_t r;              /* 2^61 / (inc << sh): mul(x << sh, r) = x / inc in Q30 */
};

struct chips_voice {
	uint32_t mp, h;         /* the square: master phase; the slave's phase within its half period, sp << 1 */
	int32_t nx, hi;         /* its next output sample (Q27, -ONE/2 .. ONE/2 plus the BLEPs), the slave high */
	uint32_t bq, bs;        /* the bass: phase within the step (bp << 5), the step 0 .. 31 */
	int32_t bnx, blv, bon;  /* its next output sample, the step's level (output), it runs */
	int32_t bsh;            /* its level: a step is 2^bsh (PUNCH on BASS_SHIFT, off one less) */
	struct freq m, s, b;
	uint32_t aph, arate;    /* the arpeggio's clock */
	int32_t p, idx;         /* its position (0 .. up and down 2n - 3), the chord's tone it plays */
	int32_t c_contour, c_bpm;
	int32_t swd, swf, sw;   /* the sweep: depth (semitones << 16), what is left of it (Q31), this block's offset */
	int32_t c_key, c_color, c_bkey;                 /* the notes and COLOR the frequencies are for */
};

/* The bass's step level in the output (Q27, offset -7.5 steps) for a step of 2^sh (the table: 2^23) */
#define BLV(s, sh) (BASS_LV[s] >> (BASS_SHIFT - (sh)))

static inline int32_t chord_of(int32_t shape)      /* SHAPE (8.8) -> its chord: eleven zones of 0 .. 127 */
{
	return (clamp(shape, 0, KNOB_MAX) * NCHORD) >> 15;
}

static void chips_init(struct chips_voice *v)   /* Plaits' Init: phases 0, next sample 0 (here with its offset) */
{
	for (unsigned i = 0; i < sizeof *v; i++)
		((uint8_t *)v)[i] = 0;
	v->nx = -(ONE >> 1);
	v->c_key = v->c_bkey = INT32_MIN;
	v->c_contour = -1;
}

static void freq_set(struct freq *o, int32_t l)
{
	uint32_t r;

	l = clamp(l, 16 << 24, 30 << 24);
	o->inc = ex2(l, 0);
	o->sh = clz32(o->inc) - 1;
	r = ex2((61 << 24) - l - (o->sh << 24), 0);
	o->r = r > 0x7fffffff ? 0x7fffffff : (int32_t)r;
}

static inline int32_t tq(uint32_t x, const struct freq *o)     /* x / inc, Q30; x < inc */
{
	int32_t t = mul((int32_t)(x << o->sh), o->r);

	return t > T1 ? T1 : t;
}

static inline int32_t sq(int32_t t) { return mul(t, t); }       /* t^2 in Q29 for t in Q30 */

static int32_t lratio(int32_t color)                /* log2 of the slave's ratio, Q24 */
{
	int32_t c = clamp(color, 0, KNOB_MAX), i = c >> 8;

	return LR_T[i] + mul(LR_T[i + 1] - LR_T[i], (c & 255) << 23);
}

static int32_t sweep_depth(int32_t sweep)            /* semitones << 16, signed */
{
	int32_t d = clamp(sweep, 0, KNOB_MAX) - (64 << 8), a = d < 0 ? -d : d, x, y;

	if (a > 63 << 8)
		a = 63 << 8;
	x = mul(a << 17, KX);
	x = x >= 1 << 30 ? 0x7fffffff : x << 1;
	y = mul(mul(x, x), SW_MAX);
	return d < 0 ? -y : y;
}

static uint32_t arp_rate(const struct chips_in *k)  /* the clock's step a block, Q32 */
{
	int32_t f;

	if (k->contour < MIX_SPLIT << 8)                /* 0 .. 63: a division of the song's tempo, rounded up, so that
	                                                 * a change on a block's start comes in that block */
		return (uint32_t)mul(k->bpm << 14, MIX_K[MIX_Z[k->contour >> 8]]) + 1;
	f = mul((k->contour - (MIX_SPLIT << 8)) << 17, KX);   /* 64 .. 127 free: (CONTOUR - 64) / 63 */
	f = f >= 1 << 30 ? 0x7fffffff : f << 1;
	return ex2(RL0 + mul(f, RSPAN) + L2_BLK, 0);
}

/* SuperSquareOscillator::Render for one block at a constant frequency: Plaits' steps, the divisions at the edges a
 * product with the reciprocal, each slave edge one carry of h. */
static void square(struct chips_voice *v, int32_t *out)
{
	uint32_t mp = v->mp, h = v->h;
	const uint32_t im = v->m.inc, is = v->s.inc, dh = is << 1;
	int32_t nx = v->nx, hi = v->hi, th, t, a, b;
	int32_t base = hi ? ONE >> 1 : -(ONE >> 1);    /* the next sample without BLEPs */
	int32_t *const end = out + BLOCK;

	do {
		th = nx;
		nx = base;
		mp += im;
		if (mp < im) {                          /* the master wraps: the slave is reset (once a period) */
			int32_t rt = tq(mp, &v->m);
			uint32_t sp = (uint32_t)hi << 31 | h >> 1, s0, spr;
			uint32_t d = (uint32_t)mul((int32_t)is, T1 - rt) << 1;          /* (1 - rt) x slave */
			int tdr;

			spr = sp + d;                                                   /* the slave's phase at the reset */
			tdr = spr < d || (!hi && spr >= HALF);
			if (spr >= HALF) {
				th -= sq(rt) >> 3;
				nx += sq(T1 - rt) >> 3;
			}
			s0 = sp;
			sp += is;
			if (tdr) {
				if (!hi) {
					if (sp >= HALF) {
						t = tq(sp - HALF, &v->s);
						th += sq(t) >> 3;
						nx -= sq(T1 - t) >> 3;
					}
				} else if (sp < s0) {
					t = tq(sp, &v->s);
					th -= sq(t) >> 3;
					nx += sq(T1 - t) >> 3;
				}
			}
			h = (uint32_t)mul((int32_t)is, rt) << 2;                       /* sp = slave x rt, low */
			if (hi)
				nx -= ONE;
			hi = 0;
			base = -(ONE >> 1);
		} else {
			h += dh;
			if (h < dh) {                   /* the slave crosses 0.5 (rises) or 1.0 (falls) */
				t = tq(h >> 1, &v->s);
				a = sq(t) >> 3;
				b = sq(T1 - t) >> 3;
				if (hi) {
					th -= a;
					nx += b;
				} else {
					th += a;
					nx -= b;
				}
				hi ^= 1;
				base = -base;
				nx += base << 1;
			}
		}
		*out++ = th;
	} while (out < end);
	v->mp = mp;
	v->h = h;
	v->nx = nx;
	v->hi = hi;
}

static inline int32_t level(uint32_t ph) { uint32_t s = ph >> 27; return (int32_t)(s & 16 ? s ^ 31 : s); }

/* Integrated BLEP (stmlib polyblep.h), Q30: next(t) = 3/16 - t/2 + 1.5 (t/2)^2 - (t/2)^4, this(t) = next(1 - t) */
static int32_t nib(int32_t t)
{
	int32_t t1 = t >> 1, t2 = mul(t1, t1) << 1, t4 = mul(t2, t2) << 1;

	return (3 << 26) - t1 + t2 + (t2 >> 1) - t4;
}

/* NESTriangleOscillator<5>::Render above f = 1/64, where Plaits fades from the 32 steps to a naive triangle with
 * integrated BLEPs at its corners (rare: the bass above 750 Hz). The steps' part of the level kept for the step. */
static void bass_fade(struct chips_voice *v, int32_t *out)
{
	uint32_t bp = v->bs << 27 | v->bq >> 5, o, s, nv;
	const uint32_t ib = v->b.inc;
	const int sh = v->bsh;
	const int32_t off = (15 << sh) >> 1;
	const int32_t fade = ib >= 1u << 27 ? T1 : (int32_t)((ib - (1u << 26)) << 4);    /* Q30 */
	const int32_t nes = (T1 - fade) >> (30 - sh);   /* a step's height x nes_gain */
	const int32_t tri = (fade >> (30 - sh)) * 15;   /* the naive triangle's height x tri_gain */
	const int32_t dc = mul(tri << 1, (int32_t)ib); /* 4 f tri_gain: the corners' discontinuity */
	int32_t nx = v->bnx, nl = mul(nes << 4, level(bp) << 27) - off, th, t;
	int32_t *const end = out + BLOCK;

	do {
		o = bp;
		bp += ib;
		th = nx;
		nx = nl;
		if (o < HALF && bp >= HALF && dc) {     /* the top corner */
			t = tq(bp - HALF, &v->b);
			th -= mul(dc, nib(T1 - t) << 1);
			nx -= mul(dc, nib(t) << 1);
		}
		if ((o ^ bp) >> 27) {
			s = bp >> 27;
			nx -= nl;                               /* the new step's level instead of the old one's */
			nl = mul(nes << 4, level(bp) << 27) - off;
			nx += nl;
			if ((s & 15) && nes) {
				t = tq(bp & 0x7ffffff, &v->b);
				if (s < 16) {
					th += mul(nes, sq(t) << 1);            /* 0.5 t^2 x nes */
					nx -= mul(nes, sq(T1 - t) << 1);
				} else {
					th -= mul(nes, sq(t) << 1);
					nx += mul(nes, sq(T1 - t) << 1);
				}
			}
			if (bp < o && dc) {                     /* the wrap: the bottom corner */
				t = tq(bp, &v->b);
				th += mul(dc, nib(T1 - t) << 1);
				nx += mul(dc, nib(t) << 1);
			}
		}
		nv = bp < HALF ? bp : (uint32_t)-bp;
		nx += mul(tri, nv > 0x7fffffff ? 0x7fffffff : (int32_t)nv);
		*out++ += th;
	} while (out < end);
	v->bs = bp >> 27;
	v->bq = bp << 5;
	v->bnx = nx;
	v->blv = BLV(v->bs, sh);
}

/* NESTriangleOscillator<5>::Render up to f = 1/64 (the bass up to 750 Hz): the 32 steps with a BLEP at each, each step
 * one carry of q. Compiled once for each of the two levels, sh a constant. */
static inline __attribute__((always_inline)) void bass_steps(struct chips_voice *v, int32_t *out, const int sh)
{
	uint32_t q = v->bq, s = v->bs;
	const uint32_t dq = v->b.inc << 5;
	const int r = 30 - sh;
	int32_t nx = v->bnx, lv = v->blv, th, t, a, b;
	int32_t *const end = out + BLOCK;

	do {
		th = nx;
		nx = lv;
		q += dq;
		if (q < dq) {                           /* a step */
			s = (s + 1) & 31;
			nx = lv = BLV(s, sh);
			if (s & 15) {                   /* not at the bottom or the top */
				t = tq(q >> 5, &v->b);
				a = sq(t) >> r;
				b = sq(T1 - t) >> r;
				if (s < 16) {
					th += a;
					nx -= b;
				} else {
					th -= a;
					nx += b;
				}
			}
		}
		*out++ += th;
	} while (out < end);
	v->bq = q;
	v->bs = s;
	v->bnx = nx;
	v->blv = lv;
}

static void bass(struct chips_voice *v, int32_t *out)
{
	if (v->b.inc > 1u << 26)
		bass_fade(v, out);
	else if (v->bsh == BASS_SHIFT)                  /* PUNCH on */
		bass_steps(v, out, BASS_SHIFT);
	else
		bass_steps(v, out, BASS_SHIFT - 1);
}

static void chips_block(struct chips_voice *v, const struct chips_in *k, int32_t *out)
{
	int32_t c, nn, pp, sw, key;

	emac_start();
	c = chord_of(k->shape);
	nn = ARP_N[c];
	pp = k->updown && nn > 2 ? 2 * nn - 2 : nn;
	if (k->trig) {
		v->p = 0;
		v->aph = 0;
		v->swd = sweep_depth(k->sweep);
		v->swf = v->swd ? 0x7fffffff : 0;
	}
	/* the arpeggio: over a chord, at every CONTOUR; one tone (OCT) holds the root */
	if (nn > 1) {
		uint32_t a0 = v->aph;

		if (k->contour != v->c_contour || k->bpm != v->c_bpm) {
			v->arate = arp_rate(k);
			v->c_contour = k->contour;
			v->c_bpm = k->bpm;
		}
		v->aph += v->arate;
		if (v->aph < a0)
			v->p++;
	} else {
		v->p = 0;
	}
	if (v->p >= pp)
		v->p = 0;
	v->idx = v->p < nn ? v->p : pp - v->p;
	/* the sweep */
	sw = 0;
	if (v->swf) {
		sw = mul(v->swd, v->swf);
		v->swf = mul(v->swf, SW_K);
		if (v->swf < SW_CUT)
			v->swf = 0;
	}
	v->sw = sw;
	/* the frequencies, when what they are for moved */
	key = k->note + (ARP_T[4 * c + v->idx] << 16) + sw;
	if (key != v->c_key || k->color != v->c_color) {
		int32_t lm = l2inc(key);

		freq_set(&v->m, lm);
		freq_set(&v->s, lm + lratio(k->color));
		v->c_key = key;
		v->c_color = k->color;
	}
	square(v, out);
	if (k->bass) {                                  /* an octave below the tone the arpeggio plays, with the sweep */
		const int32_t sh = BASS_SHIFT - (k->punch ? 0 : 1);

		key -= 12 << 16;
		if (key != v->c_bkey) {
			freq_set(&v->b, l2inc(key));
			v->c_bkey = key;
		}
		if (!v->bon) {                          /* it starts where it stopped, from its step, without a BLEP */
			v->bsh = sh;
			v->bnx = v->blv = BLV(v->bs, sh);
			v->bon = 1;
		} else if (sh != v->bsh) {              /* PUNCH moved its level: the next sample and the step's level */
			v->bnx = sh > v->bsh ? v->bnx << 1 : v->bnx >> 1;
			v->bsh = sh;
			v->blv = BLV(v->bs, sh);
		}
		bass(v, out);
	} else {
		v->bon = 0;
	}
}

#ifdef CHIPS_HOST
/* --- the proofs' entry -------------------------------------------------------------------------------------- */
static struct chips_voice hv;

/* n blocks of 10 words (struct chips_in), from a fresh voice; out takes 32 frames a block, Q27 */
void chips_host_render(const int32_t *in, int nblocks, int32_t *out)
{
	int b;

	chips_init(&hv);
	for (b = 0; b < nblocks; b++) {
		const int32_t *p = in + 10 * b;
		struct chips_in k = { p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9] };

		chips_block(&hv, &k, out + BLOCK * b);
	}
}

#else
/* --- the machine in the voice loop (STANDARD.md §2) --------------------------------------------------------- */
#define CYC_VOICE0  0x42308828u
#define CYC_VSTRIDE 0x31c
#define MARK_OFF    0x2c
#define MARK        0x43485031                      /* 'CHP1' */

#define AMP_ENV(v)  ((void (*)(char *))0x400a9252)(v)
#define VCA(o, v)   ((void (*)(int32_t *, char *))0x400a9430)(o, v)
#define PUNCH(o, v) ((void (*)(int32_t *, char *))0x400a967a)(o, v)
#define LUT_DECAY   ((const int32_t *)0x4011d84c)   /* DECAY -> the envelope's factor a block (TONE's) */
#define IDLE_LEVEL  (1 << 14)                       /* the amp envelope below -102 dB */
#define TEMPO       (*(const volatile int32_t *)0x40149310)    /* the song's tempo in 1/120 BPM (notes/38) */

/* The switches, k 32 (notes/63 §17.2, §28): read in the sound the note plays (CUR_SND(t), +20 + 2 x 32), or in the
 * copy of its 66 bytes when that is 0 (a preview note), not in p, which the OS smooths block by block. When the trig
 * that plays locked k 32 (LOCKED_K32), the copy holds the lock: each switch it holds takes the lock's value, the other
 * stays the sound's. As SAMPLE's note_switches. */
#define CUR_SND(t)  (((const char *volatile *)0x800017ec)[t])
#define TARGETS(t)  ((const char *)0x800015ae + 66 * (t))
#define LOCKED_K32(t) ((((const volatile uint32_t *)0x423087f8)[2 * (t) + 1]) & 1u)
#define SOUND_K32   84
#define SW_BASS     0x0100                          /* MACHINES + PUNCH */
#define SW_UPDOWN   0x0200                          /* MACHINES + GATE */
#define SW_BASS_LOCKED   0x0400                     /* in a lock: it holds that switch */
#define SW_UPDOWN_LOCKED 0x0800

#define V32(o)      (*(int32_t *)(v + (o)))
#define P16(o)      (*(const int16_t *)(p + (o)))

static struct chips_voice trk[6];
static struct chips_in kin[6];
static int32_t tempo_seen, bpm_seen;                /* the song's tempo, one for every track; 0 none yet (the OS's is
                                                     * at least 30 BPM) */

static inline int track_of(const char *v) { return (int)(((uint32_t)v - CYC_VOICE0) / CYC_VSTRIDE); }
static inline uint32_t mag(int32_t x) { return x < 0 ? 0u - (uint32_t)x : (uint32_t)x; }

static uint32_t note_switches(int t)
{
	const char *snd = CUR_SND(t);
	uint32_t sw = (uint16_t)(snd ? *(const volatile int16_t *)(snd + SOUND_K32) : *(const int16_t *)(TARGETS(t) + 64));

	if (LOCKED_K32(t)) {
		uint32_t lock = *(const volatile uint16_t *)(TARGETS(t) + 64);

		if (lock & SW_BASS_LOCKED)
			sw = (sw & ~(uint32_t)SW_BASS) | (lock & SW_BASS);
		if (lock & SW_UPDOWN_LOCKED)
			sw = (sw & ~(uint32_t)SW_UPDOWN) | (lock & SW_UPDOWN);
	}
	return sw;
}

void chips_update(int32_t pmod, char *v, const char *p)
{
	int t = track_of(v);
	struct chips_in *k = &kin[t];
	int32_t dec, note, tempo;
	uint32_t sw;

	if (V32(MARK_OFF) != MARK) {                    /* first block since the track changed machine: a fresh voice */
		chips_init(&trk[t]);
		V32(MARK_OFF) = MARK;
	}
	/* the stock amp chain, set up the way TONE sets it (0x400aa7b8), as ACID, SAMPLE and SWARM do: DECAY, GATE, PUNCH */
	dec = (int8_t)p[0x24];
	dec = dec < 0 ? 0 : dec > 127 ? 127 : dec;
	V32(0x250) = LUT_DECAY[dec];
	if (V32(0x38)) {
		V32(0x274) = V32(0x278) = 0x012c0f26;
		V32(0x280) = V32(0x284) = 0x001f7c5c;
		V32(0x290) = V32(0x294) = 0x7fffffff;
		V32(0x27c) = (int32_t)0x82581e4b;
		V32(0x288) = (int32_t)0x803ef8b8;
		/* PUNCH as TONE sets it (on 0x400aa8de, off 0x400aa8fe), its output stage +0x2a4 at TONE's 1/4: a square
		 * at the core's 0.5 is then 6 dB below TONE's peak and about TONE's RMS (notes/83 §7) */
		if (P16(0x1e)) {
			V32(0x29c) = 0x20000000; V32(0x2a0) = 0x60000000; V32(0x2a4) = 0x20000000;
			V32(0x48) = 1;
		} else {
			V32(0x29c) = 0x7fffffff; V32(0x2a0) = 0x20000000; V32(0x2a4) = 0x20000000;
			V32(0x48) = 0;
		}
	}
	/* the note as every machine computes it: the trig's note + PITCH - 64 + FINE (+-2 semitones) */
	note = pmod + ((int32_t)P16(0x14) << 8) + (((int32_t)P16(0x22) - 0x4000) << 3) - (64 << 16);
	k->note = clamp(note, 0, 127 << 16);
	k->trig = V32(0x38) != 0;                       /* the block after the trig, where the envelope starts */
	k->color = P16(0x16);                           /* Wave */
	k->shape = P16(0x18);                           /* Chord: CHORD's SHAPE, 0 .. 37 */
	k->sweep = P16(0x1a);                           /* Sweep */
	k->contour = P16(0x1c);                         /* Arp */
	sw = note_switches(t);
	k->bass = (sw & SW_BASS) != 0;
	k->updown = (sw & SW_UPDOWN) != 0;
	k->punch = P16(0x1e) != 0;
	tempo = TEMPO;
	if (tempo != tempo_seen) {                      /* 1/120 BPM to BPM 8.8: x 256 / 120 */
		tempo_seen = tempo;
		bpm_seen = tempo * 32 / 15;
	}
	k->bpm = bpm_seen;
}

void chips_render(int32_t *out, char *v)
{
	int t = track_of(v);
	int32_t macsr;
	int n;

	if (!V32(0x34) && !V32(0x38) && mag(V32(0x230)) < IDLE_LEVEL && mag(V32(0x234)) < IDLE_LEVEL) {
		for (n = 0; n < BLOCK; n++)             /* the envelope is closed and no trig: the voice stands still */
			out[n] = 0;
		return;
	}
	__asm__ volatile("move.l %%macsr,%0" : "=d"(macsr));
	chips_block(&trk[t], &kin[t], out);
	for (n = 0; n < BLOCK; n++)                     /* Q27 to Q31, 1.0 full scale on the bus */
		out[n] = out[n] > 0x7ffffff ? 0x7fffffff : out[n] < -0x8000000 ? INT32_MIN : out[n] << 4;
	AMP_ENV(v);
	VCA(out, v);
	PUNCH(out, v);
	__asm__ volatile("move.l %0,%%macsr" : : "d"(macsr));
}

/* --- the knobs' display (notes/83 §8, §11) -----------------------------------------------------------------------
 * A track's parameter object (vtable 0x400fd134) shows a knob's value through entries called with the knob's
 * descriptor d: +60 the text (0x4000a70e: the value window, the TRACK + knob popup, the locks), +64 the value drawn
 * instead of the text in the knob view (0x4000a66a, when the descriptor's interface object has a draw; when it gives
 * 0 the knob view writes the text in the OS's big font, 16 x 22, 0x401429ec, centred). Each takes the descriptor's
 * interface object (0x4004df40(d), 100 bytes from 0x40a71754; the build gives the added machines' descriptors
 * SNARE's). CHIPS goes in front of +60 and +64 (chain hooks: the entry behind them, the stock one or a part's) for two
 * of its descriptors and hands every other one on unchanged:
 *     Chord (SHAPE)  the chord's name: OCT, 5, SUS, m, m7, m9, m11, 69, M9, M7, M (the big font has capitals, digits
 *                    and m, and 3 of its characters fill the box); +64 gives 0, so that the knob view writes it as
 *                    it writes a number.
 *     Arp (CONTOUR)  the divisions 1/4 .. 1/32 (T: triplets), then the free tempo in Hz (rounded), "16HZ" ..
 *                    "64HZ"; in the knob view in the OS's narrow big font (12 x 22, 0x40141b08: capitals and digits,
 *                    5 characters in 60 pixels), centred where the knob view writes a number.
 * The pictures stay the stock ones.
 * The value's check stays the stock one (the object's +24: "ERR" for a value the descriptor does not take). */
extern char chips_descriptor_base[];                /* Wave's descriptor, the build's value; Chord +1, Arp +3 */
extern char chips_next_fmt[], chips_next_draw[];   /* the entries behind CHIPS's */
#define DESC_CHORD  ((int32_t)(long)chips_descriptor_base + 1)
#define DESC_ARP    ((int32_t)(long)chips_descriptor_base + 3)

typedef int32_t (*fmt_entry)(void *, int32_t, int32_t, char *);
typedef int32_t (*draw_entry)(void *, int32_t, int32_t, int32_t, void *, int32_t, int32_t);
typedef int32_t (*value_check)(void *, int32_t, int32_t);

#define UI_STATE(d) (((char *(*)(int32_t))0x4004df40)(d))     /* the descriptor's interface object */
#define CHECK(obj)  (*(value_check *)(*(char **)(obj) + 24))   /* the object's +24 */
#define STRCPY      ((int32_t (*)(char *, const char *))0x400cb9e4)
#define ERR_TEXT    ((const char *)0x40125326)                  /* "ERR" */
#define FONT_MAKE(f, g) ((void (*)(void *, const void *))0x40072260)(f, g)
#define FONT_DROP(f) ((void (*)(void *))0x40072080)(f)
#define FONT_NARROW ((const void *)0x40141b08)                  /* 12 x 22 pixels, capitals and digits */
#define DRAW_TEXT   ((void (*)(void *, void *, int32_t, int32_t, int32_t, const char *, ...))0x40071a04)

static const char MIX_NAME[7][6] = { "1/4", "1/4T", "1/8", "1/8T", "1/16", "1/16T", "1/32" };

static int32_t arp_text(int32_t value, char *out)  /* CONTOUR's text, 6 characters at most */
{
	int32_t c = clamp(value >> 8, 0, 127), n = 0, hz;
	const char *s;

	if (c < MIX_SPLIT) {
		s = MIX_NAME[MIX_Z[c]];
	} else {
		hz = FREE_HZ[c - MIX_SPLIT];
		out[n++] = (char)('0' + hz / 10);
		out[n++] = (char)('0' + hz % 10);
		s = "HZ";
	}
	while (*s)
		out[n++] = *s++;
	out[n] = 0;
	return n;
}

static int32_t chord_text(int32_t value, char *out)    /* SHAPE's text: the chord's name */
{
	const char *s = CHORD_NAME[chord_of(value)];
	int32_t n = 0;

	while (*s)
		out[n++] = *s++;
	out[n] = 0;
	return n;
}

static int32_t knob_text(int32_t d, int32_t value, char *out)
{
	return d == DESC_ARP ? arp_text(value, out) : chord_text(value, out);
}

int32_t chips_ui_format(void *obj, int32_t d, int32_t value, char *out)
{
	if (d != DESC_CHORD && d != DESC_ARP)
		return ((fmt_entry)(long)chips_next_fmt)(obj, d, value, out);
	if (!*(int32_t *)(UI_STATE(d) + 0x1c))
		return 0;
	if (!(CHECK(obj)(obj, d, value) & 0xff))
		return STRCPY(out, ERR_TEXT);
	return knob_text(d, value, out);
}

int32_t chips_ui_draw(void *obj, int32_t d, int32_t value, int32_t flags, void *canvas, int32_t x, int32_t y)
{
	uint32_t font[2];
	char text[8];

	if (d == DESC_CHORD)                            /* the knob view writes the name in its big font */
		return 0;
	if (d != DESC_ARP)
		return ((draw_entry)(long)chips_next_draw)(obj, d, value, flags, canvas, x, y);
	arp_text(value, text);
	FONT_MAKE(font, FONT_NARROW);
	DRAW_TEXT(canvas, font, x, y, 2, "%s", text);
	FONT_DROP(font);
	return 1;
}
#endif
