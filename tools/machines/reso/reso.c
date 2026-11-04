/* Reso: a tuned resonator on every track whose sound chose it (Track FX, notes/75), id 4 of the builder's filter
 * slot (tools/machines/fltslot/), which calls it after Volume + Dist with the track's block and its smoothed k 28 to
 * k 31: p-locks, the LFO and the velocity move the values as they move any parameter.
 *
 * A comb: one line a track, read a period back and fed again, damped in the loop, so that noise and hits ring at a
 * pitch with all its harmonics. Each frame: the input less its DC (a blocker at about 15 Hz, so that a kick's net
 * area does not pile up in the loop's DC mode), scaled so that noise comes out as loud as it went in; the line read
 * Dint frames back and delayed by the rest of the period with a first-order allpass (no loss, whatever the fraction);
 * a one-pole lowpass (the damping); times the loop's gain, plus the input, written back. The output crossfades from
 * the input to the comb.
 *
 * Pitch, k 28 (RETRIG + SWEEP): the MIDI note, 0 .. 127 in 8.8 (60 = C4, 69 = A4 = 440 Hz), 8 Hz to 12.5 kHz; under
 * about 20 Hz the comb is a short metallic echo. Its start word is C4 (the filter slot gives it to a sound that steps
 * to Reso, fltslot 0.8). Amount, k 29 (RETRIG + CONTOUR): 0 the input untouched, bit for bit (the start: the slot's
 * neutral word), 127 the comb alone. Tone, k 30 (RETRIG + COLOR): the damping's cutoff in harmonics of the pitch, from
 * 4 at 0 (dull: the harmonics die fast, the pitch rings) to 256 at 126, none at 127 (every harmonic rings as long as
 * the pitch). Decay, k 31 (RETRIG + SHAPE): the time the pitch takes to fall by 60 dB, 20 ms to 10 s, exponential
 * (0.46 s at 64), the same on every pitch. (Since 0.3, the maintainer's choice: the colour of the sound on COLOR and
 * its strength, the comb's feedback, on SHAPE, as the stock machines have them; Decay on COLOR and Tone, then called
 * Brightness, on SHAPE before.)
 *
 * The period is right at the pitch: the damping's pole gives it exactly the phase P of its table there, q = sin(P) /
 * sin(w0 + P), and the line is read P / w0 frames earlier; the allpass's coefficient for the fraction D of a frame is
 * (1 - D) / (1 + D) (RESO_ETA), exact at low pitches, a few cents sharp at the top (+5 at 8 kHz). The damping's loss
 * at the pitch, cos(P + w0/2) / cos(w0/2), is given back in the loop's gain, so that Decay holds whatever the
 * tone, as long as the gain stays under 1 - 2^-12 (its DC mode); past that (a dull or high pitch held long) the
 * pitch decays sooner. The coefficients are worked out when a word has moved, from tables by value, in product forms
 * that do not cancel at low pitches.
 *
 * Every product goes through the EMAC in signed fractional mode, truncating (MACSR 0xa0, as the slot calls it). On the
 * device everything but reso_reset is in reso_cf.S (since 0.4): reso_process, the block, with the frame loop (MAC with
 * load, 19 instructions a frame, 18 on three frames in four), and reso_work_out, the coefficients. This file holds the
 * same as C for the host (RESO_HOST), the proof's model: the same integer steps, the same products in the same order
 * in the same accumulator, the EMAC as tools/emu/emac.py executes it (each product truncated to 2^-23 of an LSB, the
 * accumulator read as acc >> 31, saturated), so that both give the same bits. The comb is saturated at full scale
 * wherever it is read, so the loop never runs away nor wraps.
 *
 * Off (Amount 0): the block is not touched and the comb starts again from silence (its line is cleared lazily: each
 * block clears what it reads that was written before, at most 33 frames, eight a store on the device). A silent block
 * once the comb's output has stayed under an RMS of 2^-15 of full scale (-90 dB) block after block for a whole line:
 * the same. The RMS since 0.4 from every fourth frame (0, 4, .. 28; every frame in 0.2 and 0.3, each frame's level in
 * 0.1): a rung-out comb may be let go a block sooner or later, its tail under -90 dB. A note (triggered) changes
 * nothing: the comb rings on.
 *
 * Contract (fltslot.c): reso_process(block, words, track, triggered), block 32 frames of 32 bits changed in place;
 * reso_reset(track). C ABI.
 *
 * License: MIT (LICENSE next to this file). */
#include <stddef.h>
#include <stdint.h>
#include "reso_tab.h"

#define TRACKS 6
#define FRAMES 32
#define TOP 0x7f00
#define LEN 5920                                    /* the line: the longest period (note 0, 5 871 frames) + 33 */
#define ONE 0x7fffffff
#define G_MAX (ONE - (1 << 19))                     /* 1 - 2^-12: the loop's gain, and so its DC mode's, under 1 */
#define AMT 66052                                   /* Amount's word (0 .. 0x7f00) to Q31 */
#define QUIET_E 16                                  /* sum y^2 / 2^31 over every fourth frame at an RMS of 2^-15 */
#define R_DC (ONE - (1 << 22))                      /* the DC blocker's pole, 1 - 2^-9 (about 15 Hz) */

/* --- the state ---------------------------------------------------------------------------------------------- */
struct track {
	/* the frame loop's (its offsets in reso_cf.S): pointers (the host's model), constants in the order it loads
	 * them, states */
	int32_t *blk, *rp, *wp, *end;               /* +0: the block, the line's window, where it writes, the block's end */
	int32_t kq, q, nrm, rdc, gt, ia, amt;       /* +16: the damping (1 - q, q), the input's scale, the DC blocker's
						       pole, the loop's gain, the output's dry and wet parts */
	int32_t eta;                                /* +44: the allpass */
	int32_t x1, v1, lp, hp;                     /* +48: the last input, the allpass, the damping, the DC blocker */
	uint32_t m;                                 /* +64: the block's energy, sum y^2 / 2^31 (acc1), saturated */
	/* the block's */
	uint32_t w;                                 /* +68: the next frame written, 0 .. LEN - 32, a multiple of 32 */
	uint32_t fill;                              /* +72: frames written since the comb started, up to LEN */
	uint32_t quiet;                             /* +76: frames since a block's RMS last reached 2^-15, up to LEN */
	uint32_t dint;                              /* +80: the line read dint frames back, then the allpass */
	int16_t key[3];                             /* +84: the words of Pitch, Tone and Decay the coefficients are for */
	uint8_t set;                                /* +90: the coefficients are worked out */
};
#ifndef RESO_HOST                                   /* reso_cf.S's offsets (the host's pointers are wider) */
typedef char reso_layout[offsetof(struct track, kq) == 16 && offsetof(struct track, eta) == 44 &&
			 offsetof(struct track, x1) == 48 && offsetof(struct track, m) == 64 &&
			 offsetof(struct track, w) == 68 && offsetof(struct track, fill) == 72 &&
			 offsetof(struct track, quiet) == 76 && offsetof(struct track, dint) == 80 &&
			 offsetof(struct track, key) == 84 && offsetof(struct track, set) == 90 &&
			 sizeof(struct track) == 92 ? 1 : -1];
#endif

/* reso_cf.S reads both (global since 0.4) */
struct track reso_state[TRACKS];
int32_t reso_line[TRACKS][LEN + 33];                /* then the first 32 frames again (read across the end), and a
						       frame the loop reads ahead */

static void silence(struct track *st)               /* the comb starts again from nothing */
{
	st->fill = 0;
	st->quiet = LEN;                            /* the line is silent: what was written before reads as 0 */
	st->x1 = st->hp = st->v1 = st->lp = 0;
}

void reso_reset(uint32_t track)
{
	if (track < TRACKS) {
		silence(&reso_state[track]);
		reso_state[track].set = 0;
	}
}

#ifndef RESO_HOST
/* the tables' addresses for reso_cf.S's reso_work_out (the header's tables are static) */
const void *const reso_tab[10] = {RESO_L, RESO_SH, RESO_CH, RESO_P, RESO_SP2, RESO_CP2, RESO_E, RESO_ETA, RESO_EXP,
				  RESO_SQRT};
#else
/* --- the host's model of reso_cf.S --------------------------------------------------------------------------- */
typedef __int128 wide;
static wide acc, acc1;                              /* acc0, and acc1 the frames' energy */
#define TRUNC(p) ((p) & ~(wide)0x7fffff)
static inline void acc_set(int32_t v) { acc = (wide)v * ((wide)1 << 31); }
static inline void mac(int32_t a, int32_t b) { acc += TRUNC((wide)a * b); }
static inline void msac(int32_t a, int32_t b) { acc -= TRUNC((wide)a * b); }
static inline int32_t acc_get(void)
{
	wide v = acc >> 31;
	return v > INT32_MAX ? INT32_MAX : v < INT32_MIN ? INT32_MIN : (int32_t)v;
}
static inline int32_t movclr(void)
{
	int32_t r = acc_get();
	acc = 0;
	return r;
}
static inline int clz32(uint32_t x) { return __builtin_clz(x); }   /* ff1 */
static inline int32_t mul(int32_t a, int32_t b) { mac(a, b); return movclr(); }               /* a b, Q31 */
static inline int32_t mul2(int32_t a, int32_t b) { mac(a, b); mac(a, b); return movclr(); }   /* 2 a b */

static int32_t clamp(int32_t w)
{
	return w < 0 ? 0 : w > TOP ? TOP : w;
}

/* --- the coefficients (reso_work_out in reso_cf.S) --------------------------------------------------------------- */
static int32_t lerp(const int32_t *t, uint32_t w)   /* a table by value at the word w (8.8): between two values */
{
	uint32_t n = w >> 8;
	return t[n] + mul(t[n + 1] - t[n], (int32_t)((w & 0xff) << 23));
}

/* n / d, Q31, to 2^-14 of itself, for 0 <= n, 0 < d */
static int32_t divq(uint32_t n, uint32_t d)
{
	int32_t sn, sd, s;
	uint32_t q;
	if (n >= d)
		return ONE;
	if (!n)
		return 0;
	sn = clz32(n) - 1;                          /* both in [2^30, 2^31) */
	sd = clz32(d) - 1;
	q = (n << sn) / ((d << sd) >> 15);          /* 2^14 .. 2^16 */
	s = 16 - (sn - sd);                         /* at most 16: n < d */
	if (s < 0)
		return (int32_t)(q >> -s);
	return q >= 0x80000000u >> s ? ONE : (int32_t)(q << s);   /* the divisor's truncation can reach 1 */
}

static int32_t exp2neg(uint32_t e)                  /* e Q24 -> 2^-e, Q31 */
{
	uint32_t k = e >> 24, i = (e >> 16) & 0xff;
	int32_t t0;
	if (k > 30)
		return 0;
	t0 = RESO_EXP[i];
	t0 -= mul(t0 - RESO_EXP[i + 1], (int32_t)((e & 0xffff) << 15));
	return t0 >> k;
}

static int32_t sqrtq(int32_t u)                     /* sqrt(u), Q31 */
{
	uint32_t z, x, i;
	int32_t t0;
	if (u <= 0)
		return 0;
	z = ((uint32_t)clz32((uint32_t)u) - 1) & ~1u;   /* an even shift: u << z in [2^29, 2^31) */
	x = (uint32_t)u << z;
	i = x >> 23;
	t0 = RESO_SQRT[i];
	t0 += mul(RESO_SQRT[i + 1] - t0, (int32_t)((x & 0x7fffff) << 8));
	return t0 >> (z >> 1);
}

/* The coefficients for the words of Pitch, Tone and Decay (clamped here), which it keeps. */
static void work_out(struct track *c, const int16_t *words)
{
	uint32_t pitch = (uint32_t)clamp(words[0]), tone = (uint32_t)clamp(words[2]), decay = (uint32_t)clamp(words[3]);
	uint32_t n = pitch >> 8, f = pitch & 0xff, L, P, D, e;
	int32_t sh, ch, kq = ONE, tau = 0, dmp = 0, g, dg;
	L = RESO_L[n] - (((RESO_L[n] - RESO_L[n + 1]) * f) >> 8);          /* the period, 20.12 */
	sh = lerp(RESO_SH, pitch);                                          /* sin, cos of w0 / 2 */
	ch = lerp(RESO_CH, pitch);
	n = tone >> 8;
	f = tone & 0xff;
	P = RESO_P[n] - (((RESO_P[n] - RESO_P[n + 1]) * f) >> 8);          /* the damping's phase, turns, Q32 */
	if (P) {
		int32_t s2 = lerp(RESO_SP2, tone), c2 = lerp(RESO_CP2, tone), sp, cq, sw, cw, cp, swp, shp;
		sp = mul2(s2, c2);                                          /* sin, cos of P and of w0 */
		cq = ONE - mul2(s2, s2);
		sw = mul2(sh, ch);
		cw = ONE - mul2(sh, sh);
		mac(cq, ch);                                                /* cos(P + w0/2) */
		msac(sp, sh);
		cp = movclr();
		mac(sw, cq);                                                /* sin(w0 + P) */
		mac(cw, sp);
		swp = movclr();
		mac(sh, c2);                                                /* sin((w0 + P) / 2) */
		mac(ch, s2);
		shp = movclr();
		kq = divq((uint32_t)mul2(cp, sh), (uint32_t)swp);           /* 1 - q = 2 cos(P + w0/2) sin(w0/2) / sin(w0 + P) */
		dmp = divq((uint32_t)mul2(shp, s2), (uint32_t)cp);          /* 1 / loss - 1 = 2 sin((w0 + P)/2) sin(P/2) / cos(P + w0/2) */
		tau = mul((int32_t)(P >> 1), (int32_t)L);           /* the damping's delay at the pitch, P / w0 frames */
	}
	c->kq = kq;
	c->q = ONE - kq;
	D = L - (uint32_t)tau;
	if (D < 6144)
		D = 6144;                                   /* 1.5 frames: the allpass reads a frame already written */
	c->dint = (D - 2048) >> 12;
	D -= (c->dint << 12) + 2048;                        /* the allpass's delay less half a frame, Q12, 0 .. 4095 */
	n = D >> 6;
	c->eta = RESO_ETA[n] + mul(RESO_ETA[n + 1] - RESO_ETA[n], (int32_t)((D & 63) << 25));
	n = decay >> 8;
	f = decay & 0xff;
	e = RESO_E[n] - (((RESO_E[n] - RESO_E[n + 1]) >> 8) * f);
	e = (uint32_t)mul((int32_t)(L << 6), (int32_t)e);          /* -log2 of the gain a period, Q24 */
	g = exp2neg(e);
	c->nrm = sqrtq(ONE - mul(g, g));                    /* white noise in, as loud out */
	dg = mul(g, dmp);
	c->gt = dg > G_MAX - g ? G_MAX : g + dg;
	c->rdc = R_DC;
	c->key[0] = words[0];
	c->key[1] = words[2];
	c->key[2] = words[3];
	c->set = 1;
}

/* --- the block (reso_process in reso_cf.S) ------------------------------------------------------------------- */
/* The frames, as reso_cf.S runs them: the same products, in the same accumulator. */
static void frames(struct track *st)
{
	int32_t *b = st->blk, *rp = st->rp, *wp = st->wp, u0 = *rp++, x1 = st->x1, v1 = st->v1, lp = st->lp,
		hp = st->hp;
	acc1 = 0;
	while (b != st->end) {
		int32_t x = *b, u1 = *rp++, y;
		acc_set(u0);                                /* the allpass: u0 + eta (u1 - v1) */
		mac(u1, st->eta);
		msac(v1, st->eta);
		v1 = movclr();
		mac(v1, st->kq);                            /* the damping */
		mac(lp, st->q);
		lp = movclr();
		msac(x1, st->nrm);                          /* the input less its DC, scaled */
		mac(x, st->nrm);
		mac(hp, st->rdc);
		hp = acc_get();
		mac(lp, st->gt);                            /* the comb */
		y = movclr();
		*wp++ = y;
		mac(x, st->ia);                             /* the output */
		mac(y, st->amt);
		if (!((b - st->blk) & 3))                   /* the block's energy from every fourth frame (acc1) */
			acc1 += TRUNC((wide)y * y);
		*b++ = movclr();
		x1 = x;
		u0 = u1;
	}
	st->x1 = x1;
	st->v1 = v1;
	st->lp = lp;
	st->hp = hp;
	acc1 >>= 31;
	st->m = acc1 > INT32_MAX ? INT32_MAX : (uint32_t)acc1;
}

void reso_process(int32_t *block, const int16_t *words, uint32_t track, uint32_t triggered)
{
	struct track *st;
	int32_t *ln, amt;
	uint32_t w, start;
	int n;
	(void)triggered;
	if (track >= TRACKS)
		return;
	st = &reso_state[track];
	amt = clamp(words[1]) * AMT;
	if (!amt) {                                         /* off: untouched */
		silence(st);
		return;
	}
	if (st->quiet >= LEN) {                             /* rung out: is the block silent too? */
		int32_t any = 0;
		for (n = 0; n < FRAMES; n++)
			any |= block[n];
		if (!any) {
			silence(st);
			return;
		}
	}
	if (!st->set || words[0] != st->key[0] || words[2] != st->key[1] || words[3] != st->key[2])
		work_out(st, words);
	ln = reso_line[track];
	w = st->w;
	start = w + LEN - st->dint - 1;                     /* the window's first frame: dint + 1 back */
	if (start >= LEN)
		start -= LEN;
	if (st->fill < LEN) {                               /* the frames of the window written before the comb started */
		int32_t nz = (int32_t)st->dint + 1 - (int32_t)st->fill;
		for (n = 0; n < (nz > FRAMES + 1 ? FRAMES + 1 : nz); n++)
			ln[start + n] = 0;
	}
	st->blk = block;
	st->end = block + FRAMES;
	st->rp = &ln[start];
	st->wp = &ln[w ? w : LEN];                          /* at the line's start, into its copy: the reads see it */
	st->ia = ONE - amt;
	st->amt = amt;
	frames(st);
	if (!w)                                             /* the line's first 32 frames from their copy */
		for (n = 0; n < FRAMES; n++)
			ln[n] = ln[LEN + n];
	st->w = w + FRAMES < LEN ? w + FRAMES : 0;
	if (st->fill < LEN)
		st->fill += FRAMES;
	if (st->m >= QUIET_E)                               /* the block's RMS at 2^-15 of full scale or more */
		st->quiet = 0;
	else if (st->quiet < LEN)
		st->quiet += FRAMES;
}
#endif
