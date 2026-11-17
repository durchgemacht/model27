/* TERRA for model27 (notes/85): wave terrain synthesis after Mutable Instruments Plaits' WaveTerrainEngine.
 *
 * Origin and licence: the terrains, the path and the AUX output are Plaits' WaveTerrainEngine
 * (plaits/dsp/engine2/wave_terrain_engine.cc), the path's oscillator its FastSineOscillator (the quadrature "magic
 * circle"), terrains 6 to 8 read Plaits' wavetable data wav_integrated_waves (plaits/resources.cc, copied into
 * terra_tables.h by tools/gen_terra.py): Mutable Instruments Plaits, Copyright 2016-2021 Emilie Gillet, MIT licence
 * (eurorack 08460a6, LICENSE-Plaits). Their algorithms are written anew here in fixed point; no line of the C++ is
 * copied. The EMAC arrangement, ex2 and l2inc are SOLID's and CHIPS' (model27). This file: model27 (durchgemacht and
 * Claude), MIT.
 *
 * A point goes round a path over a surface z = f(x, y); the height under it is the sound. The knobs (the
 * maintainer's layout of 2026-11-17, notes/85 §4): COLOR the surface (Plaits' HARMONICS: eight terrains, cross-faded
 * between neighbours as Plaits does), SHAPE the path's radius (TIMBRE: 0.1 .. 1.0, smaller at high notes), SWEEP its
 * shift in x (MORPH: the centre from -1 to +0.9, the path narrowed towards the edge), CONTOUR the mix of AUX into OUT
 * (Plaits' second output, Sine(1 + (y + z) / 2), linearly). One point a sample (no oversampling: the maintainer's
 * choice after listening, notes/85 §3). DECAY, GATE and PUNCH are the stock amp chain as on TONE; while the envelope
 * is closed and no trig comes, the core is not called and stands still. A trig does not reset the path (as Plaits).
 *
 * The core is step 1's (_scratch/terrain-machine/terrain.c) with the chosen variant only (A, 1x, the mix): the same
 * bits (notes/85 §5). Differences from Plaits on purpose: the pitch as every Cycles machine (A4 = 440 Hz at 48 kHz) and
 * the path's step 2 sin(pi f) exact (Plaits' Fast2Sin is up to 7 cents off); a block of 32 frames, the step constant
 * over it, radius, shift, surface and mix ramped per sample; divisions by a 64-entry reciprocal table after
 * normalizing, Sine the Cycles' own 256-entry table in its SRAM (0x8000eee4), Squash(Sine(p), 2) one table; the
 * oscillator's invariant x^2 + y^2 + e x y kept at 1 within 2^-12; the wavetable terrains clamp outside -1 .. 1.
 *
 * Arithmetic: every product through the EMAC in signed fractional mode (MACSR 0xa0: saturating, truncating), on the
 * device mac.l / movclr.l, on the host (TERRA_HOST) the same arithmetic in __int128. Coordinates Q29, heights Q30, the
 * oscillator Q30, phases uint32. The core's output is Q(27 + TERRA_OSH): 1.0 = Plaits' engine full scale; on the
 * device TERRA_OSH is 2 (notes/85 §4.3), the host's proof of step 1's bits builds it with 0. Plain C99, no libc, no
 * float, no 64-bit arithmetic on the device. */
#include <stdint.h>
#include "terra_tables.h"

#define BLOCK 32
#define KNOB_MAX (127 << 8)
#define ONE29 (1 << 29)
#define ONE30 (1 << 30)
#define MAX_INC 0x2a000000u         /* f0 < 0.164: e = 2 sin(pi f) stays below 1 (Q31) */
#ifndef TERRA_OSH
#define TERRA_OSH 2                 /* the output Q(27 + TERRA_OSH) */
#endif

/* --- the EMAC (as solid.c, chips.c, maxsaw.c) ---------------------------------------------------------------- */
#ifdef TERRA_HOST
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
#define SIN256 SIN256_T             /* the host's copy of the Cycles' table (gen_terra.py --cycles checks it) */
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
#define SIN256 ((const int32_t *)SIN_SRAM)          /* the Cycles' sine in its internal SRAM: no cache line */
#endif
static inline int32_t mul(int32_t a, int32_t b) { mac(a, b); return movclr(); }          /* a b / 2^31 */
static inline int32_t clamp(int32_t x, int32_t lo, int32_t hi) { return x < lo ? lo : x > hi ? hi : x; }
static inline int32_t iabs(int32_t x) { return x < 0 ? -x : x; }

static uint32_t ex2(int32_t l, int q)               /* 2^(l / 2^24) x 2^q; 2^32 - 1 above, 0 below 1 */
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

static inline int32_t kx(int32_t k)                 /* the knob 0 .. 127 << 8 as 0 .. 1, Q31 (as SWARM) */
{
	k = clamp(k, 0, KNOB_MAX);
	return k * 66052 + ((k * 2064) >> 16);
}

/* --- the functions the terrains are made of ------------------------------------------------------------------ */
static inline int32_t sin_i(uint32_t ph)            /* sin(2 pi ph / 2^32), Q31, interpolated */
{
	uint32_t i = ph >> 24;
	return SIN256[i] + mul(SIN256[i + 1] - SIN256[i], (int32_t)((ph << 8) >> 1));
}

static inline int32_t sqs_i(uint32_t ph)            /* Squash(sin(2 pi ph / 2^32), 2), Q31, interpolated */
{
	uint32_t i = ph >> 24;
	return SQS256_T[i] + mul(SQS256_T[i + 1] - SQS256_T[i], (int32_t)((ph << 8) >> 1));
}

static inline int32_t rec27(int32_t d)              /* 1 / d, d and the result Q27, 1/16 <= d < 16 */
{
	int n = clz32((uint32_t)d);
	uint32_t m = (uint32_t)d << n;                  /* the mantissa in [1, 2), Q31 unsigned */
	uint32_t i = (m >> 25) & 63;
	int32_t r = RCP64_T[i] + mul(RCP64_T[i + 1] - RCP64_T[i], (int32_t)((m << 7) >> 1));

	return n >= 8 ? r << (n - 8) : r >> (8 - n);
}

/* --- the eight terrains: X, Y Q29 in, the height Q30 out (wave_terrain_engine.cc, Terrain) -------------------- */
static inline int32_t t0(int32_t X, int32_t Y)      /* (Squash(Sine(1.273 x), 2) - Sine(0.637 y (x + 1.571))) 0.57 */
{
	int32_t a = sqs_i((uint32_t)mul(X, K0_X) << 4);
	int32_t b = sin_i((uint32_t)mul(mul(Y, X + C0_1571), K0_Y) << 5);

	return mul((a >> 1) - (b >> 1), K0_057);
}

static inline int32_t t1(int32_t X, int32_t Y)      /* Sine(Sine(0.637 (x + y)) / (0.2 + (xy)^2) 0.159) */
{
	int32_t xy = mul(X, Y);
	int32_t in = sin_i((uint32_t)mul(X + Y, K1_S) << 3);
	int32_t r = rec27((mul(xy, xy) << 4) + C1_02);

	return sin_i((uint32_t)mul(mul(in, K_0159), r) << 5) >> 1;
}

static inline int32_t t2(int32_t X, int32_t Y)      /* Sine(Sine(2.387 xy) / (0.35 + (xy)^2) 0.159) */
{
	int32_t xy = mul(X, Y);
	int32_t in = sin_i((uint32_t)mul(xy, K2_XY) << 7);
	int32_t r = rec27((mul(xy, xy) << 4) + C2_035);

	return sin_i((uint32_t)mul(mul(in, K_0159), r) << 5) >> 1;
}

static inline int32_t t3(int32_t X, int32_t Y)      /* Sine(xy / (2 + |5 (x - 0.25)(y + 0.25)|) 6.366) */
{
	int32_t xy = mul(X, Y);
	int32_t w = iabs(mul(X - C_025, Y + C_025));
	int32_t r = rec27(C3_2 + 5 * w);

	return sin_i((uint32_t)mul(mul(xy, K3_6366), r) << 12) >> 1;
}

static inline int32_t t4(int32_t X, int32_t Y)      /* Sine(0.159 / (0.17 + |y - 0.25|) + 0.477 / (0.35 + |(x + 0.5)(y + 1.5)|)) */
{
	int32_t r1 = rec27((iabs(Y - C_025) >> 2) + C4_017);
	int32_t r2 = rec27(iabs(mul(X + C_05, Y + C_15)) + C2_035);

	return sin_i(((uint32_t)mul(r1, K_0159) + (uint32_t)mul(r2, K_0477)) << 5) >> 1;
}

/* the wavetable data read as a terrain (TerrainLookupWT): x the wave (64), y the place in it (128); the data are
 * integrated, differentiated here as Plaits does (DIFFERENTIATE_WAVE_DATA), x 1/1024 */
static inline int32_t twt(int32_t X, int32_t Y, const int16_t *bank)
{
	int32_t s = clamp((Y + ONE29) >> 7, 0, 128 << 16);              /* the place, Q16 */
	int32_t w = clamp(mul(X + ONE29, KWT), 0, (63 << 16) - 1);      /* the wave, Q16 */
	const int16_t *p = bank + (w >> 16) * 132 + (s >> 16);
	int32_t sf = (s & 0xffff) << 15;
	int32_t a = p[0], b = p[1], c = p[2];
	int32_t v0 = ((b - a) << 16) + mul((c - b - b + a) << 16, sf);  /* Q16 */
	int32_t v1;

	a = p[132];
	b = p[133];
	c = p[134];
	v1 = ((b - a) << 16) + mul((c - b - b + a) << 16, sf);
	return (v0 + mul(v1 - v0, (w & 0xffff) << 15)) << 4;
}

static inline __attribute__((always_inline)) int32_t terrain(int k, int32_t X, int32_t Y)
{
	/* a chain of tests, not a switch: GCC's jump table addresses pc-relative with an index, which the ColdFire
	 * interpreter of the proofs (_scratch/cfemu) cannot run */
	if (k >= 5)                                     /* Plaits: bank 2 - (k - 5) */
		return twt(X, Y, WT_T + (7 - k) * 64 * 132);
	if (k < 2)
		return k == 0 ? t0(X, Y) : t1(X, Y);
	if (k == 2)
		return t2(X, Y);
	return k == 3 ? t3(X, Y) : t4(X, Y);
}

/* --- the voice ---------------------------------------------------------------------------------------------- */
struct terra_in {               /* one block's inputs */
	int32_t note;           /* semitones << 16 */
	int32_t harm, timbre, morph, mix;       /* 8.8, 0 .. 127: COLOR, SHAPE, SWEEP, CONTOUR */
};

struct terra_voice {
	int32_t x, y;           /* the path's oscillator, Q30, invariant x^2 + y^2 + e x y = 1 */
	int32_t e;              /* its step 2 sin(pi f), Q31 */
	int32_t note;           /* the note e and inc are for */
	uint32_t inc;           /* the phase step a sample, Q32 */
	int32_t ax, ay, off;    /* x scale amp (1 - |off|) and y scale amp (Q30), x offset (Q29), at the last sample */
	int32_t tz;             /* the surface's position, Q24 (0 .. 6.9999), at the last sample */
	int32_t mx;             /* the mix to AUX, Q31, at the last sample */
	int32_t fresh;          /* no block yet: the targets are taken at once */
};

static void terra_init(struct terra_voice *v)
{
	v->x = ONE30;
	v->y = 0;
	v->e = 0;
	v->note = INT32_MIN;
	v->inc = 0;
	v->ax = v->ay = v->off = v->tz = v->mx = 0;
	v->fresh = 1;
}

/* 2 sin(pi f) for f = inc / 2^32 < 1/6, Q31: s = pi f, s (1 - s^2/6 (1 - s^2/20 (1 - s^2/42))) x 2 */
#define PI4 1686629713              /* pi / 4, Q31 */
#define R42 51130563                /* 1 / 42, Q31 */
#define R20 107374182               /* 1 / 20, Q31 */
#define R6 357913941                /* 1 / 6, Q31 */
static int32_t step_e(uint32_t inc)
{
	int32_t s = mul((int32_t)(inc >> 1), PI4) << 2;                 /* pi f, Q31 */
	int32_t s2 = mul(s, s);
	int32_t c = ONE30 - (mul(s2, R42) >> 1);

	c = ONE30 - mul(mul(s2, R20), c);
	c = ONE30 - mul(mul(s2, R6), c);
	return mul(s, c) << 2;
}

#define K19 1020054733              /* 1.9, Q29 */
#define K105 107374182              /* 0.05, Q31 */
#define K69999 117439807            /* 8 - 1.0001 = 6.9999 (as float in Plaits), Q24 */
#define R01 214748365               /* 0.1, Q31 */
#define K09 1932735283              /* 0.9, Q31 */
#define INV_TOL (1 << 17)           /* the invariant's tolerance, 2^-12 of 1.0 (Q29) */

struct ramp {                   /* the block's ramps: the values before the first sample (with the remainder), the steps */
	int32_t ax, ay, off, tz, mx, dax, day, doff, dtz, dmx;
};

/* The block's loop. kind 1: terrain k0c alone; kind 2: k0c cross-faded to k0c + 1 by frc; kind 0: the surface moves,
 * chosen per sample. Called with constants for kind and k0c, so that each call becomes its own loop with its
 * terrains inlined and no test per point. aux gets each sample's AUX phase for the mix after the loop. */
static inline __attribute__((always_inline)) void loop(struct terra_voice *v, int32_t *out, const struct ramp *r,
							const int kind, const int k0c, const int32_t frc, uint32_t *aux)
{
	const int32_t e = v->e, dax = r->dax, day = r->day, doff = r->doff, dtz = r->dtz;
	int32_t x = v->x, y = v->y, cax = r->ax, cay = r->ay, coff = r->off, ctz = r->tz;

	for (int i = 0; i < BLOCK; i++) {
		int k0 = k0c;
		int32_t fr = frc, X, Y, z;

		cax += dax;
		cay += day;
		coff += doff;
		if (kind == 0) {                        /* Plaits: z0 + (z1 - z0) fraction */
			ctz += dtz;
			k0 = ctz >> 24;
			fr = (ctz & 0xffffff) << 7;
		}
		x += mul(e, y);
		y -= mul(e, x);
		X = mul(x, cax) + coff;
		Y = mul(y, cay);
		z = terrain(k0, X, Y);
		if (kind == 2 || (kind == 0 && fr))
			z += mul(terrain(k0 + 1, X, Y) - z, fr);
		out[i] = z >> (3 - TERRA_OSH);                          /* OUT */
		aux[i] = (((uint32_t)Y << 1) + (uint32_t)z) << 1;       /* AUX's phase: (y + z) / 2 cycles */
	}
	v->x = x;
	v->y = y;
}

/* AUX mixed in after the loop (only in blocks with the mix above 0): out += (sin(phase) - out) mix */
static void mix_aux(int32_t *out, const uint32_t *aux, const struct ramp *r)
{
	int32_t cmx = r->mx;

	for (int i = 0; i < BLOCK; i++) {
		cmx += r->dmx;
		if (cmx)
			out[i] += mul((sin_i(aux[i]) >> (4 - TERRA_OSH)) - out[i], cmx);
	}
}

#define ONE(k) loop(v, out, &r, 1, k, 0, aux)
#define TWO(k) loop(v, out, &r, 2, k, fr, aux)

static void run(struct terra_voice *v, int32_t *out, int32_t ax, int32_t ay, int32_t off, int32_t tz, int32_t mx)
{
	struct ramp r;
	uint32_t aux[BLOCK];
	int k0 = tz >> 24, mix = mx != 0 || v->mx != 0;
	int32_t fr = (tz & 0xffffff) << 7;

	/* the ramps: the remainder of the division by 32 at the first sample, so that 32 steps end on the target */
	r.dax = (ax - v->ax) >> 5;
	r.day = (ay - v->ay) >> 5;
	r.doff = (off - v->off) >> 5;
	r.dtz = (tz - v->tz) >> 5;
	r.dmx = (mx - v->mx) >> 5;
	r.ax = ax - (r.dax << 5);
	r.ay = ay - (r.day << 5);
	r.off = off - (r.doff << 5);
	r.tz = tz - (r.dtz << 5);
	r.mx = mx - (r.dmx << 5);
	v->ax = ax;
	v->ay = ay;
	v->off = off;
	v->tz = tz;
	v->mx = mx;
	if (r.dtz != 0)
		loop(v, out, &r, 0, 0, 0, aux);         /* the surface moves within the block */
	else if (fr == 0) {
		if (k0 < 4) {
			if (k0 < 2) { if (k0 == 0) ONE(0); else ONE(1); }
			else { if (k0 == 2) ONE(2); else ONE(3); }
		} else {
			if (k0 < 6) { if (k0 == 4) ONE(4); else ONE(5); }
			else { if (k0 == 6) ONE(6); else ONE(7); }
		}
	} else {
		if (k0 < 4) {
			if (k0 < 2) { if (k0 == 0) TWO(0); else TWO(1); }
			else { if (k0 == 2) TWO(2); else TWO(3); }
		} else {
			if (k0 == 4) TWO(4); else if (k0 == 5) TWO(5); else TWO(6);
		}
	}
	if (mix)
		mix_aux(out, aux, &r);
}

static void terra_block(struct terra_voice *v, const struct terra_in *in, int32_t *out)
{
	int32_t ax, ay, off, tz, mx;

	emac_start();
	if (in->note != v->note) {                      /* the step, only when the note moved */
		uint32_t inc = ex2(l2inc(in->note), 0);

		if (inc > MAX_INC)
			inc = MAX_INC;
		if (inc == 0)
			inc = 1;
		v->inc = inc;
		v->e = step_e(inc);
		v->note = in->note;
	}
	{                                               /* the invariant back to 1 when the rounding moved it */
		int32_t c = mul(v->x, v->x) + mul(v->y, v->y) + mul(v->e, mul(v->x, v->y));     /* Q29 */

		if (c > ONE29 + INV_TOL || c < ONE29 - INV_TOL) {
			int32_t s = 3 * (1 << 29) - c;          /* 1.5 - c / 2, Q30 */

			v->x = mul(v->x, s) << 1;
			v->y = mul(v->y, s) << 1;
		}
	}
	{                                               /* radius, shift, surface, mix: the targets of this block */
		uint32_t inc = v->inc;
		int32_t t = kx(in->timbre), m = kx(in->morph), h = kx(in->harm), h5 = mul(h, K105);
		int32_t att = inc < (1u << 29) ? 0x7fffffff - mul((int32_t)(inc << 2), (int32_t)(inc << 2)) : 0;
		int32_t amp = mul(R01 + mul(mul(t, K09), att), 0x7fffffff - (int32_t)inc);      /* Q31 */

		off = mul(m, K19) - ONE29;
		ax = mul(amp, (ONE29 - iabs(off)) << 1);
		ay = amp >> 1;
		tz = mul(h > 0x7fffffff - h5 ? 0x7fffffff : h + h5, K69999);  /* min(h x 1.05, 1) x 6.9999 */
		mx = kx(in->mix);
	}
	if (v->fresh) {                                 /* the first block starts on its targets */
		v->ax = ax;
		v->ay = ay;
		v->off = off;
		v->tz = tz;
		v->mx = mx;
		v->fresh = 0;
	}
	run(v, out, ax, ay, off, tz, mx);
}

#ifdef TERRA_HOST
/* --- the host's entries (the proofs, notes/85 §5) ------------------------------------------------------------ */
/* n blocks of 5 int32 (note, COLOR, SHAPE, SWEEP, CONTOUR) through one fresh voice, 32 int32 a block out */
void terra_host_render(const int32_t *in, int n, int32_t *out)
{
	struct terra_voice v;

	terra_init(&v);
	for (int b = 0; b < n; b++) {
		struct terra_in k = { in[5 * b], in[5 * b + 1], in[5 * b + 2], in[5 * b + 3], in[5 * b + 4] };

		terra_block(&v, &k, out + BLOCK * b);
	}
}

/* the same with the voice kept between calls (a track that pauses: the proofs call it only for blocks not paused) */
static struct terra_voice hv[6];

void terra_host_reset(int t)
{
	terra_init(&hv[t]);
}

void terra_host_block(int t, const int32_t *in, int32_t *out)
{
	struct terra_in k = { in[0], in[1], in[2], in[3], in[4] };

	terra_block(&hv[t], &k, out);
}

#else
/* --- the machine in the voice loop (STANDARD.md §2) --------------------------------------------------------- */
#define CYC_VOICE0  0x42308828u
#define CYC_VSTRIDE 0x31c
#define MARK_OFF    0x2c
#define MARK        0x54524131                      /* 'TRA1' */

#define AMP_ENV(v)  ((void (*)(char *))0x400a9252)(v)
#define VCA(o, v)   ((void (*)(int32_t *, char *))0x400a9430)(o, v)
#define PUNCH(o, v) ((void (*)(int32_t *, char *))0x400a967a)(o, v)
#define LUT_DECAY   ((const int32_t *)0x4011d84c)   /* DECAY -> the envelope's factor a block (TONE's) */
#define IDLE_LEVEL  (1 << 14)                       /* the amp envelope below -102 dB */
/* PUNCH's output stage (+0x2a4, after its drive and the envelope, notes/84 §9.3): Max Saw's 0x7fffffff (TONE's x 4).
 * The core's Q29 goes onto the bus as it is (TERRA_OSH 2: Plaits' full scale = 1/4 of the bus), so a track's output is
 * the core's / 8: Plaits' full scale a TONE voice at full scale - 18 dB, about TONE's level (notes/85 §4.3, to be
 * measured in step 3). */
#define STAGE       0x7fffffff

#define V32(o)      (*(int32_t *)(v + (o)))
#define P16(o)      (*(const int16_t *)(p + (o)))

static struct terra_voice trk[6];
static struct terra_in kin[6];

static inline int track_of(const char *v) { return (int)(((uint32_t)v - CYC_VOICE0) / CYC_VSTRIDE); }
static inline uint32_t mag(int32_t x) { return x < 0 ? 0u - (uint32_t)x : (uint32_t)x; }

void terra_update(int32_t pmod, char *v, const char *p)
{
	int t = track_of(v);
	struct terra_in *k = &kin[t];
	int32_t dec, note;

	if (V32(MARK_OFF) != MARK) {                    /* first block since the track changed machine: a fresh voice */
		terra_init(&trk[t]);
		V32(MARK_OFF) = MARK;
	}
	/* the stock amp chain, set up the way TONE sets it (0x400aa7b8), as CHIPS, SWARM, MAXSAW and SAMPLE do */
	dec = (int8_t)p[0x24];
	dec = dec < 0 ? 0 : dec > 127 ? 127 : dec;
	V32(0x250) = LUT_DECAY[dec];
	if (V32(0x38)) {
		V32(0x274) = V32(0x278) = 0x012c0f26;
		V32(0x280) = V32(0x284) = 0x001f7c5c;
		V32(0x290) = V32(0x294) = 0x7fffffff;
		V32(0x27c) = (int32_t)0x82581e4b;
		V32(0x288) = (int32_t)0x803ef8b8;
		/* PUNCH as TONE sets it (on 0x400aa8de, off 0x400aa8fe), its output stage +0x2a4 TERRA's (STAGE) */
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
	k->harm = P16(0x16);                            /* COLOR: the surface */
	k->timbre = P16(0x18);                          /* SHAPE: the radius */
	k->morph = P16(0x1a);                           /* SWEEP: the shift */
	k->mix = P16(0x1c);                             /* CONTOUR: AUX */
}

/* A block that is not paused: its own function, so that the pause's path in terra_render saves no registers. */
static __attribute__((noinline)) void render_live(int32_t *out, char *v, int t)
{
	int32_t macsr;

	__asm__ volatile("move.l %%macsr,%0" : "=d"(macsr));
	terra_block(&trk[t], &kin[t], out);             /* onto the bus as it is: Q29 */
	AMP_ENV(v);
	{
		/* The VCA without the trig's flags (0x400a9430), as SWARM's (notes/82 §6.5): in a trig's block (+0x34) it
		 * fades the level to 0, and in the next (+0x38, a full attack) it jumps back to full; TERRA runs on through
		 * the trig, so it would drop out for 0.67 ms and come back with a step, a click. Hidden, the VCA ramps from
		 * the level it had to the envelope's over each block. AMP_ENV before and PUNCH after see the flags
		 * (notes/85 §9). */
		int32_t f34 = V32(0x34), f38 = V32(0x38);

		V32(0x34) = 0;
		V32(0x38) = 0;
		VCA(out, v);
		V32(0x34) = f34;
		V32(0x38) = f38;
	}
	PUNCH(out, v);
	__asm__ volatile("move.l %0,%%macsr" : : "d"(macsr));
}

void terra_render(int32_t *out, char *v)
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
