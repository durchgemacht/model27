/* Max Saw for model27 (notes/84): seven sawtooths after Adam Szabo's analysis of the Super Saw
 * ("How to Emulate the Super Saw", BSc thesis, KTH 2010).
 *
 * Origin: Szabo measured the synthesizer and published the model as numbers and formulas; nothing of his text or of any
 * firmware is used. Seven sawtooths: the centre (his osc 4) at the note, six around it at his offsets (table 1) times his
 * detune curve (an 11th-degree polynomial of the knob); the centre's and the side oscillators' gains from his two mix
 * polynomials; the seven summed and sent through a high-pass at the fundamental that follows the pitch; at every trig a
 * random phase for each oscillator (free running). His sawtooths are not band-limited: the aliasing is part of the
 * sound, the high-pass removes what folds below the fundamental. The tables (maxsaw_tables.h) are computed from those
 * formulas by tools/gen_maxsaw.py. This file: model27 (durchgemacht and Claude), MIT.
 *
 * Our choices (notes/84 §4, §7): a 2-pole state-variable high-pass (TPT, Butterworth), naive sawtooths (the
 * maintainer's choice of 2026-11-16 after listening); the pitch as every Cycles machine computes it (A = 440 Hz at
 * 48 kHz); the knobs read once a block of 32 frames, the gains ramped across the block, the frequencies stepped; a trig
 * sets the gains at once. The knobs (the maintainer's layout of 2026-11-16): COLOR Detune, SHAPE Mix, SWEEP Tone (the
 * high-pass's cutoff against the fundamental, 16 steps an octave, Szabo's at 32), CONTOUR Phase (the random phases'
 * width at a trig: 0 all equal, 127 fully random as Szabo's), MACHINES + PUNCH Sub (a switch, notes/84 §13: an eighth
 * oscillator, a naive sawtooth two octaves below the note through a 2-pole low-pass at the note, added after the
 * high-pass; the centre and the high-pass stay at the note). DECAY, GATE and PUNCH are the stock amp chain as on TONE; its output stage is set for
 * Max Saw's level (maxsaw_update). While the envelope is closed and no trig comes, the core is not called and stands
 * still, as SWARM's and CHIPS'.
 *
 * Arithmetic: every fractional product through the EMAC in signed fractional mode (MACSR 0xa0: saturating, truncating),
 * on the device mac.l / movclr.l, on the host (MSAW_HOST) the same arithmetic in __int128, as SWARM, CHIPS and SOLID have
 * it. Phases uint32, the sawtooth is the phase read as int32 (Q31), gains Q27, coefficients Q31. The core's output is
 * Q27, a single sawtooth at gain 1 = 1.0. Plain C99, no libc, no float and no 64-bit arithmetic on the device. On the
 * device the block's frame loops are assembly (maxsaw_cf.S, notes/84 §11), on the host the C loop in msaw_block. */
#include <stdint.h>
#include "maxsaw_tables.h"

#define NOSC 7
#define CENTRE 3                    /* Szabo's osc 4 */
#define BLOCK 32
#define KNOB_MAX (127 << 8)
#define INC_MAX 0x40000000u         /* the centre at most 12 kHz */

/* --- the EMAC (as swarm.c, chips.c, solid.c) ---------------------------------------------------------------- */
#ifdef MSAW_HOST
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
#else
static inline void emac_start(void)
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
#endif
/* A mul() empties the accumulator: never call one inside a run of mac. */
static inline int32_t mul(int32_t a, int32_t b) { mac(a, b); return movclr(); }

static inline int32_t clamp(int32_t x, int32_t lo, int32_t hi) { return x < lo ? lo : x > hi ? hi : x; }

static inline uint32_t ex2(int32_t l, int q)        /* 2^(l / 2^24) x 2^q; 2^32 - 1 above, 0 below 1 (solid.c) */
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

static inline int32_t knob_tab(const int32_t *t, int32_t k)    /* a table of 128 (+1) read at an 8.8 knob */
{
	int32_t i, f;

	k = clamp(k, 0, KNOB_MAX);
	i = k >> 8;
	f = (k & 0xff) << 23;
	return t[i] + mul(t[i + 1] - t[i], f);
}

static inline int32_t hp_tab(const int32_t *t, int32_t n)      /* the high-pass's tables at a cutoff note << 16 */
{
	int32_t i, f;

	n = clamp(n - HP_LO * 65536, 0, ((HP_N - 1) << 16) - 1);
	i = n >> 16;
	f = (n & 0xffff) << 15;
	return t[i] + mul(t[i + 1] - t[i], f);
}

/* --- the state ---------------------------------------------------------------------------------------------- */
struct knobs {
	int32_t note;           /* semitones << 16, 69 = A 440 Hz */
	int32_t detune, mix;    /* 8.8, 0 .. 127 << 8 */
	int32_t tone, phase;    /* 8.8, 0 .. 127 << 8 */
	int32_t sub;            /* 0 off; 1, 2: the Sub that many octaves below the note (the switch: 0 or 2) */
};

struct msaw {
	uint32_t ph[NOSC];      /* phases; read as int32, the sawtooths (Q31) */
	uint32_t inc[NOSC];     /* their steps a frame */
	int32_t gc, gs;         /* the centre's and each side oscillator's gain now, Q27 */
	int32_t s1, s2;         /* the high-pass's state, Q27 */
	uint32_t sph;           /* the Sub's phase (read as int32, its sawtooth), then its low-pass's state, Q27: in this */
	int32_t l1, l2;         /* order (msaw_sub) */
	uint32_t rng;
	int32_t fresh;          /* the next block sets the gains at once (after init and a trig) */
};

static inline uint32_t rnd(struct msaw *s)
{
	s->rng = s->rng * 1664525u + 1013904223u;
	return s->rng;
}

/* A trig: a random phase for every oscillator (Szabo p. 21: free running, a new random phase at each trigger), its
 * width the Phase knob's: at 127 the whole cycle (Szabo's), at 0 all seven at phase 0 (the sawtooths at their middle,
 * rising: every trig the same, a hard attack and the flanging of Szabo's figure 19). The Sub starts at phase 0 (its
 * sawtooth's middle, rising) at every trig, whatever Phase; its low-pass keeps its state. */
static void msaw_trig(struct msaw *s, int32_t phase)
{
	int32_t amt = clamp(phase, 0, KNOB_MAX) * PHASE_K;
	int i;

	emac_start();
	for (i = 0; i < NOSC; i++)
		s->ph[i] = (uint32_t)mul((int32_t)rnd(s), amt);
	s->sph = 0;
	s->fresh = 1;
}

static void msaw_init(struct msaw *s, uint32_t seed)
{
	uint8_t *p = (uint8_t *)s;
	unsigned i;

	for (i = 0; i < sizeof *s; i++)
		p[i] = 0;
	s->rng = seed;
	msaw_trig(s, KNOB_MAX);
}

/* The knobs into increments and gain targets, once a block; gives the centre's increment (the note's). */
static uint32_t params(struct msaw *s, const struct knobs *k, int32_t *gct, int32_t *gst)
{
	int32_t loct = mul((k->note - (69 << 16)) << 7, Q_TWELFTH) << 1;  /* octaves from A 440, Q24 (to 2^-23) */
	uint32_t inc0 = ex2(L2_440 + loct + L2_INC, 0);
	int32_t y = knob_tab(DETY_T, k->detune);
	int i;

	if (inc0 > INC_MAX)
		inc0 = INC_MAX;
	for (i = 0; i < NOSC; i++)
		s->inc[i] = inc0 + (uint32_t)mul((int32_t)inc0, mul(OFF_T[i], y));
	*gct = knob_tab(MIXC_T, k->mix) >> 4;
	*gst = knob_tab(MIXS_T, k->mix) >> 4;
	return inc0;
}

#ifndef MSAW_HOST
/* The frame loops in assembly (maxsaw_cf.S); the host runs the C loops of msaw_block, the proofs' model. */
void msaw_saws(uint32_t *ph, const uint32_t *inc, int32_t *out, int32_t gc, int32_t gs, int32_t dgc, int32_t dgs);
void msaw_sub(int32_t *sb, uint32_t *st, uint32_t sinc, const int32_t *cf);
void msaw_hpf(int32_t *out, int32_t *st, const int32_t *cf, const int32_t *sb);
#endif

/* The Sub's block (notes/84 §13): one block for the track that runs, so one for all. */
static int32_t sbuf[BLOCK];

/* One block of 32 frames into out: the seven sawtooths, then the high-pass in place, then the Sub added (when on). On
 * the host out is the core's Q27; on the device maxsaw_cf.S also puts it onto the bus, Q27 x 2 saturated (8.0 full
 * scale), which the host's proofs do after it (to_bus). */
static void msaw_block(struct msaw *s, const struct knobs *k, int32_t *out)
{
	int32_t gct, gst, dgc = 0, dgs = 0, gc, gs, cut, a1, a2, a3, sub = clamp(k->sub, 0, 2);
	uint32_t inc0;
	int f, i;

	emac_start();
	inc0 = params(s, k, &gct, &gst);
	if (s->fresh) {
		s->gc = gct;
		s->gs = gst;
		s->fresh = 0;
	} else {
		dgc = (gct - s->gc) >> 5;
		dgs = (gst - s->gs) >> 5;
	}
	gc = s->gc;
	gs = s->gs;
	/* the high-pass's cutoff: the fundamental moved by Tone, 16 steps an octave */
	cut = k->note + (clamp(k->tone, 0, KNOB_MAX) - TONE_AT) * TONE_Q16;
	a1 = hp_tab(SVA1_T, cut);
	a2 = hp_tab(SVA2_T, cut);
	a3 = hp_tab(SVA3_T, cut);
#ifndef MSAW_HOST
	(void)f;
	(void)i;
	if (sub) {
		/* the Sub: its sawtooth `sub` octaves below the note, through the low-pass at the note (the same TPT
		 * coefficients as the high-pass's), times its level */
		const int32_t lcf[4] = { hp_tab(SVA1_T, k->note), hp_tab(SVA2_T, k->note), hp_tab(SVA3_T, k->note), SUB_GAIN };

		msaw_sub(sbuf, &s->sph, inc0 >> sub, lcf);      /* maxsaw_cf.S: the same as the loop below */
	}
	msaw_saws(s->ph, s->inc, out, gc, gs, dgc, dgs);   /* maxsaw_cf.S: the same as the loops below */
	{
		const int32_t cf[4] = { a1, a2, a3, SVF_KM1 };

		msaw_hpf(out, &s->s1, cf, sub ? sbuf : 0);
	}
#else
	if (sub) {
		int32_t la1 = hp_tab(SVA1_T, k->note), la2 = hp_tab(SVA2_T, k->note), la3 = hp_tab(SVA3_T, k->note);
		uint32_t sinc = inc0 >> sub;

		for (f = 0; f < BLOCK; f++) {
			int32_t x, v1, v2, v3;

			mac((int32_t)s->sph, SUB_GAIN);
			s->sph += sinc;
			x = movclr();
			/* the 2-pole state-variable low-pass (TPT), k = sqrt 2: its v2 */
			v3 = x - s->l2;
			mac(la1, s->l1);
			mac(la2, v3);
			v1 = movclr();
			mac(la2, s->l1);
			mac(la3, v3);
			v2 = s->l2 + movclr();
			s->l1 = 2 * v1 - s->l1;
			s->l2 = 2 * v2 - s->l2;
			sbuf[f] = v2;
		}
	}
	for (f = 0; f < BLOCK; f++) {
		int32_t x, v1, v2, v3;

		gc += dgc;
		gs += dgs;
		for (i = 0; i < NOSC; i++) {
			mac((int32_t)s->ph[i], i == CENTRE ? gc : gs);
			s->ph[i] += s->inc[i];
		}
		x = movclr();
		/* the 2-pole state-variable high-pass (TPT), k = sqrt 2 */
		v3 = x - s->s2;
		mac(a1, s->s1);
		mac(a2, v3);
		v1 = movclr();
		mac(a2, s->s1);
		mac(a3, v3);
		v2 = s->s2 + movclr();
		s->s1 = 2 * v1 - s->s1;
		s->s2 = 2 * v2 - s->s2;
		out[f] = x - v1 - mul(SVF_KM1, v1) - v2;
		if (sub)
			out[f] += sbuf[f];
	}
#endif
	s->gc = gct;
	s->gs = gst;
}

#ifdef MSAW_HOST
static struct msaw hs;

/* The proofs' entry: n blocks of 6 words (struct knobs) and a trig flag a block (at its start, with that block's
 * Phase), from init; out takes 32 frames a block, Q27. */
int msaw_host_render(const int32_t *kn, const uint8_t *trig, int nblocks, int32_t *out, uint32_t seed)
{
	int b;

	msaw_init(&hs, seed);
	for (b = 0; b < nblocks; b++) {
		const int32_t *p = kn + 6 * b;
		struct knobs k = { p[0], p[1], p[2], p[3], p[4], p[5] };

		if (trig && trig[b])
			msaw_trig(&hs, k.phase);
		msaw_block(&hs, &k, out + BLOCK * b);
	}
	return (int)sizeof(struct msaw);
}

/* The random numbers the init and each trig draw (before the Phase width): n of seven. */
void msaw_host_phases(uint32_t seed, int n, uint32_t *ph)
{
	int j;

	hs.rng = seed;
	for (j = 0; j < NOSC * n; j++)
		ph[j] = rnd(&hs);
}

#else
/* --- the machine in the voice loop (STANDARD.md §2) --------------------------------------------------------- */
#define CYC_VOICE0  0x42308828u
#define CYC_VSTRIDE 0x31c
#define MARK_OFF    0x2c
#define MARK        0x4d585331                      /* 'MXS1' */
#define SEED0       0x55a7u                         /* the tracks' random numbers: SEED0 + t x 0x9e3779b9 */

#define AMP_ENV(v)  ((void (*)(char *))0x400a9252)(v)
#define VCA(o, v)   ((void (*)(int32_t *, char *))0x400a9430)(o, v)
#define PUNCH(o, v) ((void (*)(int32_t *, char *))0x400a967a)(o, v)
#define LUT_DECAY   ((const int32_t *)0x4011d84c)   /* DECAY -> the envelope's factor a block (TONE's) */
#define IDLE_LEVEL  (1 << 14)                       /* the amp envelope below -102 dB */
/* PUNCH's output stage (+0x2a4, after its drive and the envelope, notes/84 §9): TONE's 0x20000000 x 4. The core's
 * Q27 goes onto the bus x 2 (8 sawtooths in phase before the bus saturates), so a track's output is the core's / 16:
 * a single sawtooth at gain 1 is a TONE voice at full scale - 6 dB. */
#define STAGE       0x7fffffff

/* The switch, k 32 (notes/63 §17.2, §28; as CHIPS's bass): read in the sound the note plays (CUR_SND(t), +20 + 2 x
 * 32), or in the copy of its 66 bytes when that is 0 (a preview note), not in p, which the OS smooths block by block.
 * When the trig that plays locked k 32 (LOCKED_K32), the copy holds the lock: the switch takes the lock's value when
 * the lock holds it. */
#define CUR_SND(t)  (((const char *volatile *)0x800017ec)[t])
#define TARGETS(t)  ((const char *)0x800015ae + 66 * (t))
#define LOCKED_K32(t) ((((const volatile uint32_t *)0x423087f8)[2 * (t) + 1]) & 1u)
#define SOUND_K32   84
#define SW_SUB      0x0100                          /* MACHINES + PUNCH */
#define SW_SUB_LOCKED 0x0400                        /* in a lock: it holds the switch */

#define V32(o)      (*(int32_t *)(v + (o)))
#define P16(o)      (*(const int16_t *)(p + (o)))

static struct msaw trk[6];
static struct knobs kin[6];
static uint8_t trg[6];                              /* a trig in this block: new phases before the core runs */
static uint8_t ini[6];                              /* the track took the machine: a fresh voice before it runs (in
                                                     * render, which keeps MACSR: the init draws through the EMAC) */

static inline int track_of(const char *v) { return (int)(((uint32_t)v - CYC_VOICE0) / CYC_VSTRIDE); }
static inline uint32_t mag(int32_t x) { return x < 0 ? 0u - (uint32_t)x : (uint32_t)x; }

static uint32_t note_switches(int t)
{
	const char *snd = CUR_SND(t);
	uint32_t sw = (uint16_t)(snd ? *(const volatile int16_t *)(snd + SOUND_K32) : *(const int16_t *)(TARGETS(t) + 64));

	if (LOCKED_K32(t)) {
		uint32_t lock = *(const volatile uint16_t *)(TARGETS(t) + 64);

		if (lock & SW_SUB_LOCKED)
			sw = (sw & ~(uint32_t)SW_SUB) | (lock & SW_SUB);
	}
	return sw;
}

void maxsaw_update(int32_t pmod, char *v, const char *p)
{
	int t = track_of(v);
	struct knobs *k = &kin[t];
	int32_t dec, note;

	if (V32(MARK_OFF) != MARK) {                    /* first block since the track changed machine: a fresh voice */
		ini[t] = 1;
		V32(MARK_OFF) = MARK;
	}
	/* the stock amp chain, set up the way TONE sets it (0x400aa7b8), as CHIPS, SWARM and SAMPLE do: DECAY, GATE, PUNCH */
	dec = (int8_t)p[0x24];
	dec = dec < 0 ? 0 : dec > 127 ? 127 : dec;
	V32(0x250) = LUT_DECAY[dec];
	if (V32(0x38)) {
		V32(0x274) = V32(0x278) = 0x012c0f26;
		V32(0x280) = V32(0x284) = 0x001f7c5c;
		V32(0x290) = V32(0x294) = 0x7fffffff;
		V32(0x27c) = (int32_t)0x82581e4b;
		V32(0x288) = (int32_t)0x803ef8b8;
		/* PUNCH as TONE sets it (on 0x400aa8de, off 0x400aa8fe), its output stage +0x2a4 Max Saw's (STAGE) */
		if (P16(0x1e)) {
			V32(0x29c) = 0x20000000; V32(0x2a0) = 0x60000000; V32(0x2a4) = STAGE;
			V32(0x48) = 1;
		} else {
			V32(0x29c) = 0x7fffffff; V32(0x2a0) = 0x20000000; V32(0x2a4) = STAGE;
			V32(0x48) = 0;
		}
	}
	/* the note as every machine computes it: the trig's note + PITCH - 64 + FINE (+-2 semitones) */
	note = pmod + ((int32_t)P16(0x14) << 8) + (((int32_t)P16(0x22) - 0x4000) << 3) - (64 << 16);
	k->note = clamp(note, 0, 127 << 16);
	k->detune = P16(0x16);                          /* COLOR */
	k->mix = P16(0x18);                             /* SHAPE */
	k->tone = P16(0x1a);                            /* SWEEP */
	k->phase = P16(0x1c);                           /* CONTOUR */
	k->sub = (note_switches(t) & SW_SUB) ? 2 : 0;
	trg[t] = V32(0x38) != 0;                        /* the block after the trig, where the envelope starts */
}

/* A block that is not paused: its own function, so that the pause's path in maxsaw_render saves no registers. */
static __attribute__((noinline)) void render_live(int32_t *out, char *v, int t)
{
	int32_t macsr;

	__asm__ volatile("move.l %%macsr,%0" : "=d"(macsr));
	if (ini[t]) {
		msaw_init(&trk[t], SEED0 + (uint32_t)t * 0x9e3779b9u);
		ini[t] = 0;
	}
	if (trg[t]) {
		msaw_trig(&trk[t], kin[t].phase);
		trg[t] = 0;
	}
	msaw_block(&trk[t], &kin[t], out);              /* onto the bus: Q27 x 2, saturated (msaw_hpf, maxsaw_cf.S) */
	AMP_ENV(v);
	VCA(out, v);
	PUNCH(out, v);
	__asm__ volatile("move.l %0,%%macsr" : : "d"(macsr));
}

void maxsaw_render(int32_t *out, char *v)
{
	int n;

	if (!V32(0x34) && !V32(0x38) && mag(V32(0x230)) < IDLE_LEVEL && mag(V32(0x234)) < IDLE_LEVEL) {
		for (n = 0; n < BLOCK; n++)             /* the envelope is closed and no trig: the voice stands still */
			out[n] = 0;
		return;
	}
	render_live(out, v, track_of(v));
}
#endif
