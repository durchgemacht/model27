/* POTS for model27's delay slot (notes/69): a mono delay whose repeats go down an old telephone line on every pass.
 * model27's own work (durchgemacht and Claude), MIT, LICENSE next to this file; the sound was settled by ear in a float
 * prototype (notes/69 §2), this is its fixed point, checked against it wave for wave (§12.2).
 *
 * Each loop frame, everything from the read to the write inside the feedback:
 *
 *     read      line[w - D], D from Time by the stock formula, slewing as Digital Delay's
 *     scatter   + a second tap 24..144 frames (at 48 kHz) further back, wandering
 *     shift     a Hilbert pair and a phasor: the repeat moves up 2 Hz a pass, the speed wandering +-40 %
 *     fading    +-6 dB, wandering; now and then a dropout of -18 dB for 8..25 ms
 *     receiver  its 350 Hz high pass (4 poles) first, so that no bass sets the codec's steps (notes/69 §22)
 *     codec     mu-law, 7 bits, faded out as the tail falls from -40 to -52 dB
 *     receiver  then its 3 kHz low pass (4 poles) and +6 dB at 1.5 kHz, the loudest frequency at unity
 *     leveler   3:1 above 0.25 in the loop; on the echo a make-up towards 0.15, 0.6..2.5, x 1.5
 *     feedback  Digital Delay's curve x 1.18
 *     sender    the skewed clip (c(3 s + 0.12) - c(0.12)) / 3, c(x) = x - 4 x^3 / 27; 4 kHz low pass, 200 Hz high pass
 *
 * Before the sender, outside the loop, a limiter holds the send at the level v6 was tuned at (0.5, the median machine
 * at Delay Send 127): the block's peak, a 0.2 s release, the gain ramped over the block; a hotter send no longer drives
 * the clip harder (notes/69 §21, §22). Under that level the send passes as it is.
 *
 * POTS_RATE 2 (the maintainer's choice, notes/69 §12.6): the loop at 24 kHz between a half-band decimator
 * (-1, 0, 9, 16, 9, 0, -1) / 32 and the four-point interpolator; POTS_RATE 1: at 48 kHz. Samples Q2.29 (1.0 = 2^29,
 * the codec's full scale); the send bus carries 1.0 as K_BUS (measured, §12.4), IN_GAIN_Q29 and OUT_GAIN_Q30 take it
 * in and the echo out, 12 dB above the prototype's (§12.5, §17). Every product goes through the EMAC in signed fractional
 * mode, never with a scale factor: on the device mac.l / msac.l / movclr.l, on the host (POTS_HOST) the same
 * arithmetic as tools/emu/emac.py executes it (each product truncated to 2^-23 of an LSB, the accumulator read as
 * acc >> 31, saturated), so that both give the same bits. Tables and constants: pots_tables.h (tools/gen_pots.py).
 *
 * A full-scale bus (8 times the median machine's level, 18 dB above it) must not wrap anywhere (notes/69 §14.1): the
 * host's accumulator is 128 bits wide (emac.py's is unbounded; the device's has 8 bits above 1.0, and the largest sum
 * here, mul29 of two full-scale words, needs 3); the input is held at +-2.0 before the decimator, the feedback added
 * to it saturating, the echo held at +-0.75 of full scale before the interpolator. Below those levels nothing
 * changes: the measurements of §12.3 stay as they were. Built with -fwrapv on both sides.
 *
 * Contract (notes/68 §15.3, §16.3): pots_process(out, in, params), called as the stock delay 0x40057488 is, params
 * P + 428 (Time at +0, Fdbk at +2, x 256). The line is the delay slot's, LINE_FRAMES words, shared with the slot's other
 * effects: after pots_reset a frame is read only once it was written since (n counts them). pots_reset() only marks
 * the state. The C ABI keeps d2-d7/a2-a6; the EMAC is free (MACSR and acc0 are set here, the mixer sets MACSR again
 * after the call). */
#include <stdint.h>

#ifndef POTS_RATE
#define POTS_RATE 2
#endif
#include "pots_tables.h"

#define BLOCK 32
#define MASK (LINE_FRAMES - 1)
#define SHIFT_SIGN 1                /* the shift goes up (checked in the prototype, notes/69 §12.2) */

#ifdef POTS_HOST
enum { D_SCAT = 1, D_FADE = 2, D_CODEC = 4, D_LEVEL = 8, D_RX = 16, D_TX = 32, D_SHIFT = 64, D_CLIP = 128 };
static int dbg_off;                 /* stages turned off by the checks */
static int32_t dbg_theta;           /* the shift's step a loop frame, Q31 radians, when not 0 */
static int32_t tempo = 14400;       /* 120 BPM */
#define TEMPO tempo
#define OFF(x) (dbg_off & (x))
#else
#define TEMPO (*(volatile int32_t *)0x40149310)
#define OFF(x) 0
#endif

extern int32_t fx_line[];           /* the delay slot's line: LINE_FRAMES words (notes/68 §16) */

/* --- the EMAC ----------------------------------------------------------------------------------------------- */
#ifdef POTS_HOST
typedef __int128 wide;
static wide acc;
#define TRUNC(p) ((p) & ~(wide)0x7fffff)
static inline void emac_start(void) { acc = 0; }
static inline void mac(int32_t a, int32_t b) { acc += TRUNC((wide)a * b); }
static inline void msac(int32_t a, int32_t b) { acc -= TRUNC((wide)a * b); }
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
static inline void msac(int32_t a, int32_t b) { __asm__ volatile("msac.l %0,%1,%%acc0" : : "r"(a), "r"(b)); }
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
/* A doubled product is two products: the scale factor (mac.l Ry,Rx,<<,ACC) is ignored in fractional mode on the
 * device (notes/69 §16: POTS 0.1 came out 85 dB down), so it is never used. */
static inline void mac2(int32_t a, int32_t b) { mac(a, b); mac(a, b); }
static inline void msac2(int32_t a, int32_t b) { msac(a, b); msac(a, b); }
/* A mul() empties the accumulator: never call one inside a run of mac (the prototype's first fault, §12.2). */
static inline int32_t mul(int32_t a, int32_t b) { mac(a, b); return movclr(); }          /* b Q31 */
static inline int32_t mul30(int32_t a, int32_t b) { mac2(a, b); return movclr(); }       /* b Q30 */
static inline int32_t mul29(int32_t a, int32_t b) { mac2(a, b); mac2(a, b); return movclr(); }   /* b Q29 */

static inline int32_t clamp(int32_t x, int32_t lo, int32_t hi) { return x < lo ? lo : x > hi ? hi : x; }

static inline int32_t add_sat(int32_t a, int32_t b)
{
	int32_t s = (int32_t)((uint32_t)a + (uint32_t)b);
	if ((a ^ s) & (b ^ s) & INT32_MIN)                  /* both of a sign, the sum of the other: it wrapped */
		return a < 0 ? INT32_MIN : INT32_MAX;
	return s;
}

static int32_t lg2(int32_t x)       /* log2(x / 2^29) in Q24, x > 0 */
{
	int p = 31 - clz32((uint32_t)x);
	uint32_t m = (uint32_t)x << (31 - p);
	int i = (int)((m >> 26) & 31);
	int32_t f = (int32_t)((m >> 10) & 0xffff);
	return ((p - 29) << 24) + LOG2_T[i] + mul(LOG2_T[i + 1] - LOG2_T[i], f << 15);
}

static int32_t ex2(int32_t l)       /* 2^(l / 2^24) in Q29, saturated */
{
	int32_t ip = l >> 24, fr = l & 0xffffff;
	int i = fr >> 19;
	int32_t f = (fr >> 3) & 0xffff;
	int32_t e = EXP2_T[i] + mul(EXP2_T[i + 1] - EXP2_T[i], f << 15);   /* Q30, 1..2 */
	if (ip >= 2)
		return INT32_MAX;
	if (ip == 1)
		return e;
	return 1 - ip >= 31 ? 0 : e >> (1 - ip);
}

static int32_t sin_t(uint32_t ph)    /* sin(2 pi ph / 2^32), Q31 */
{
	int i = (int)(ph >> 24);
	int32_t f = (int32_t)((ph >> 8) & 0xffff);
	return SIN_T[i] + mul(SIN_T[i + 1] - SIN_T[i], f << 15);
}

static inline int32_t mulaw(int32_t x)   /* the codec, encoded and decoded: 63 steps a side, full scale 1.0 */
{
	int32_t a = x < 0 ? -x : x;     /* INT32_MIN stays negative: code 0 */
	int code = 0;                   /* the code: how many thresholds a passes, from its bucket's first (notes/69 §20) */
	if (a > 0) {
		int z = clz32((uint32_t)a);
		code = CODEC_IDX[((31 - z) << 3) + (int)((((uint32_t)a << z) >> 28) & 7)];
		while (code < CODEC_STEPS && a >= CODEC_T[code])
			code++;
	}
	return x < 0 ? -CODEC_L[code] : CODEC_L[code];
}

/* --- the state ---------------------------------------------------------------------------------------------- */
typedef struct { int32_t v, target, coef; int left, min_blocks, max_blocks; } wander;

static struct {
	uint32_t ready, w, d, n;
	int32_t ha[HIL_N + 1][2], hb[HIL_N + 1][2], a_prev;  /* x1 x2: the chain's input, then each section's output */
	int32_t rx[7][2];                               /* the same for the receiver: its input, its high pass's two
	                                                 * biquads, the codec's output, then the other three biquads */
	int32_t txlp, txhp;
	int32_t pc, ps;                                 /* the shift's phasor, Q31 */
	uint32_t ph1, ph2;                              /* its speed's slow wander */
	int32_t env, gc, gw, fade_g, scat;              /* Q29, Q31, Q29, Q29, Q16 frames */
	wander fade, sc;
	int gap_wait, gap_on;
	uint32_t rng;
	int32_t dec[4], itp[3];                         /* POTS_RATE 2: the half-band filters' histories (the taps read) */
	int32_t lim, ig;                                /* the limiter: the send's envelope (bus words), the input's gain */
} st;

static uint32_t rnd(void)
{
	st.rng ^= st.rng << 13;
	st.rng ^= st.rng >> 17;
	st.rng ^= st.rng << 5;
	return st.rng;
}

static int32_t rnd_q30(void) { return (int32_t)(rnd() - 0x80000000u) >> 1; }    /* -1..1 */
static int span(int a, int b) { return a + (int)(((rnd() >> 16) * (uint32_t)(b - a)) >> 16); }

static int32_t wander_step(wander *g)
{
	if (--g->left <= 0) {
		g->target = rnd_q30();
		g->left = span(g->min_blocks, g->max_blocks);
	}
	g->v += mul(g->target - g->v, g->coef);
	return g->v;
}

static int32_t gain(int16_t fdbk)     /* Digital Delay's curve, Q15 */
{
	int32_t f = clamp(fdbk >> 8, 0, 127), t = f * 258;
	int32_t c = (t * t) >> 15;
	c = (c * t) >> 15;
	return (3 * t - c) >> 1;
}

static uint32_t knob_delay(int16_t time)   /* the stock delay's formula (notes/68 §16.1), in loop frames */
{
	uint32_t d = (uint32_t)((((int32_t)time + 256) * 48000 >> 10) * 900 / TEMPO);
	d = d > 261120u ? 261120u : d < 32u ? 32u : d;
	return POTS_RATE == 2 ? (d + 1) >> 1 : d;
}

static void init(uint32_t target)
{
	uint32_t keep = st.rng;
	for (unsigned i = 0; i < sizeof st; i++)
		((uint8_t *)&st)[i] = 0;
	st.rng = keep ? keep : 7;
	st.ready = 1;
	st.d = target;
	st.pc = PHASOR_M;
	st.gc = INT32_MAX;
	st.gw = st.fade_g = 1 << 29;
	st.ig = IN_GAIN_Q29;
	st.fade = (wander){0, 0, FADE_COEF, 0, 45, 225};
	st.sc = (wander){0, 0, SCAT_COEF, 0, 750, 3000};
	st.scat = SC_MIN_Q16 + (SC_SPAN_Q16 >> 1);
	st.gap_wait = 2250;
}

/* --- one loop frame ----------------------------------------------------------------------------------------- */
/* A cascade keeps one history per signal: a section's input is the output of the one before, so h[0] holds the
 * input's last two values and h[k + 1] section k's output's. The same products in the same order as four words a
 * section, half the moves, unrolled (notes/69 §20). */
static inline int32_t chain(int32_t (*h)[2], const int32_t *c, int32_t x)   /* allpasses (c - z^-2) / (1 - c z^-2) */
{
	int32_t x2 = h[0][1];
	h[0][1] = h[0][0];
	h[0][0] = x;
#pragma GCC unroll 4
	for (int k = 0; k < HIL_N; k++) {
		int32_t y1 = h[k + 1][0], y2 = h[k + 1][1];
		int32_t y = mul(x + y2, c[k]) - x2;
		h[k + 1][1] = y1;
		h[k + 1][0] = y;
		x = y;
		x2 = y2;
	}
	return x;
}

static inline int32_t receiver(int32_t (*h)[2], const int32_t (*c)[5], int n, int32_t x)   /* n of its biquads */
{
	int32_t x1 = h[0][0], x2 = h[0][1];
	h[0][1] = x1;
	h[0][0] = x;
#pragma GCC unroll 3
	for (int k = 0; k < n; k++) {
		int32_t y1 = h[k + 1][0], y2 = h[k + 1][1];
		mac2(x, c[k][0]); mac2(x1, c[k][1]); mac2(x2, c[k][2]); mac2(y1, c[k][3]); mac2(y2, c[k][4]);
		int32_t y = movclr();
		h[k + 1][1] = y1;
		h[k + 1][0] = y;
		x = y;
		x1 = y1;
		x2 = y2;
	}
	return x;
}

static int32_t line_at(uint32_t back)
{
	return back <= st.n ? fx_line[(st.w - back) & MASK] : 0;
}

typedef struct { int32_t target, fb, dgc, dgw, dfade, dscat, grain_w, cs, sn; } blockv;

static int32_t frame(int32_t x_in, const blockv *b)
{
	int32_t diff = (int32_t)(b->target - st.d), step = diff >> (POTS_RATE == 2 ? 12 : 13);
	if (step == 0 && diff != 0 && !(st.w & (POTS_RATE == 2 ? 1 : 3)))
		step = diff > 0 ? 1 : -1;
	st.d += (uint32_t)step;

	int32_t x = line_at(st.d);
	if (!OFF(D_SCAT)) {
		uint32_t k = st.d + ((uint32_t)st.scat >> 16);      /* the second tap, scat (Q16) frames further back */
		int32_t fr = st.scat & 0xffff, a = line_at(k), c = line_at(k + 1);
		int32_t tap = a + (mul((c >> 1) - (a >> 1), fr << 15) << 1);
		mac(x, SC_NORM); mac(tap, SC_GAIN_N);
		x = movclr();
		st.scat += b->dscat;
	}

	/* the shift: the Hilbert pair on x / 2, the phasor turning once a frame */
	int32_t va = chain(st.ha, HIL_A, x >> 1), vb = chain(st.hb, HIL_B, x >> 1);
	int32_t I = st.a_prev, Q = vb;
	st.a_prev = va;
	mac2(I, st.pc);
	if (SHIFT_SIGN > 0) mac2(Q, st.ps); else msac2(Q, st.ps);
	int32_t y = movclr();
	mac(st.pc, b->cs); msac(st.ps, b->sn);
	int32_t pc = movclr();
	mac(st.ps, b->cs); mac(st.pc, b->sn);
	st.ps = movclr();
	st.pc = pc;
	if (OFF(D_SHIFT))
		y = x;

	if (!OFF(D_FADE)) {
		y = mul29(y, st.fade_g);
		st.fade_g += b->dfade;
	}
	if (!OFF(D_RX))
		y = receiver(st.rx, RX_C, 2, y);                 /* the high pass: rx[0..2] */
	if (!OFF(D_CODEC))
		y += mul(mulaw(y) - y, b->grain_w);
	if (!OFF(D_RX))
		y = receiver(st.rx + 3, RX_C + 2, 3, y);         /* the low pass and the peak: rx[3..6] */

	int32_t loop = mul(y, st.gc), wet = mul29(y, st.gw);
	st.gc += b->dgc;
	st.gw += b->dgw;

	int32_t s = add_sat(x_in, mul30(loop, b->fb));
	if (!OFF(D_TX)) {
		/* the skewed clip in Q2.29: u reaches 1.5, u^2 2.25 and u^3 3.375 (Q30 overflowed: the second fault, §12.2) */
		if (!OFF(D_CLIP)) {                             /* the checks of §22 measure without it, the filters kept */
			int32_t u = clamp(s, -CLIP_IN, CLIP_IN);
			u = clamp(DRIVE * u + GRIT_BIAS, -CLIP_U, CLIP_U);
			int32_t u2 = mul29(u, u), u3 = mul29(u2, u);
			int32_t c = u - mul(u3, SAT_K) - SAT_BIAS_OUT;
			s = mul(c, DRIVE_INV_Q31);
		}
		st.txlp += mul(s - st.txlp, TX_LP_K);
		st.txhp += mul(st.txlp - st.txhp, TX_HP_K);
		s = st.txlp - st.txhp;
	}
	fx_line[st.w] = clamp(s, -SAFE, SAFE);
	st.w = (st.w + 1) & MASK;
	if (st.n < LINE_FRAMES)
		st.n++;
	return wet;
}

/* --- one block ---------------------------------------------------------------------------------------------- */
void pots_process(int32_t *out, const int32_t *in, const int16_t *params)
{
	blockv b;
	emac_start();
	b.target = (int32_t)knob_delay(params[0]);
	b.fb = gain(params[1]) * FB_MAX;                      /* Q15 x Q15 = Q30 */
	if (!st.ready)
		init((uint32_t)b.target);

	/* the leveler looks at this block's frames on the line before playing them */
	int32_t peak = 0;
	for (int i = 0; i < LOOP_FRAMES; i++) {
		int32_t v = line_at(st.d - (uint32_t)i);
		v = v < 0 ? -v : v;
		if (v > peak)
			peak = v;
	}
	st.env += peak > st.env ? (peak - st.env) >> 1 : mul(peak - st.env, ENV_REL);
	int32_t gc1 = INT32_MAX, gw1 = 1 << 29;
	if (!OFF(D_LEVEL)) {
		if (st.env > (1 << 27)) {                       /* above 0.25: 3:1 */
			int32_t g = ex2(mul(COMP_EXP, COMP_THR_L2 - lg2(st.env)));
			gc1 = g >= (1 << 29) ? INT32_MAX : g << 2;
		}
		gw1 = st.env > 537 ? clamp(ex2((LEV_TARGET_L2 - lg2(st.env)) >> 1), LEV_MIN, LEV_MAX) : LEV_MAX;
		gw1 = mul30(gw1, WET_GAIN);
	}
	b.dgc = (gc1 - st.gc) >> LOOP_SHIFT;
	b.dgw = (gw1 - st.gw) >> LOOP_SHIFT;
	b.grain_w = st.env >= GATE_HI ? INT32_MAX : st.env <= GATE_LO ? 0
	            : (int32_t)(((uint32_t)(st.env - GATE_LO) >> 6) * 65536u / ((uint32_t)(GATE_HI - GATE_LO) >> 6)) << 15;

	int32_t fade1 = OFF(D_FADE) ? 1 << 29 : ex2(mul(wander_step(&st.fade), FADE_L2) >> 6);
	if (!OFF(D_FADE)) {
		if (st.gap_on > 0) {
			st.gap_on--;
			fade1 >>= 3;
		} else if (--st.gap_wait <= 0) {
			st.gap_on = span(12, 38);
			st.gap_wait = span(2250, 7500);
			fade1 >>= 3;
		}
	}
	b.dfade = (fade1 - st.fade_g) >> LOOP_SHIFT;
	int32_t v = wander_step(&st.sc);
	int32_t s1 = SC_MIN_Q16 + mul(((v >> 1) + (1 << 29)) << 1, SC_SPAN_Q16);
	b.dscat = (s1 - st.scat) >> LOOP_SHIFT;

	/* the shift's speed: 2 Hz x (1 + 0.4 (0.7 sin + 0.3 sin)) */
	int32_t m = mul(sin_t(st.ph1), DRIFT_W1) + mul(sin_t(st.ph2), DRIFT_W2);
	st.ph1 += DRIFT_INC1;
	st.ph2 += DRIFT_INC2;
	int32_t th = THETA0 + mul(THETA0, mul(m, DRIFT_D));
#ifdef POTS_HOST
	if (dbg_theta)
		th = dbg_theta;
#endif
	b.cs = INT32_MAX - (mul(th, th) >> 1);
	b.sn = th;
	int32_t m2 = mul(PHASOR_M, PHASOR_M);                 /* before the run of mac below */
	mac(st.pc, st.pc); mac(st.ps, st.ps);
	int32_t e = (m2 - movclr()) >> 1;
	st.pc += mul(st.pc, e);
	st.ps += mul(st.ps, e);

	/* the limiter: the block's peak on the send (L / 2 + R / 2, bus words) before playing it, the input's gain ramped
	 * over the block to hold it at LIM_BUS; IN_GAIN_Q29 itself, and no ramp, while the send stays under */
	int32_t pk = 0;
#pragma GCC unroll 4
	for (int i = 0; i < BLOCK; i++) {
		int32_t v = (in[2 * i] >> 1) + (in[2 * i + 1] >> 1);
		v = v < 0 ? -v : v;
		if (v > pk)
			pk = v;
	}
	st.lim = pk > st.lim ? pk : mul(st.lim, LIM_REL);
	int32_t ig = st.ig, ig1 = IN_GAIN_Q29;
	if (st.lim > LIM_BUS) {
		int32_t g = ex2(LIM_L2 - lg2(st.lim));
		ig1 = mul(IN_GAIN_Q29, g >= (1 << 29) ? INT32_MAX : g << 2);
	}
	int32_t dig = (ig1 - ig) >> LOOP_SHIFT;
	st.ig = ig1;

#if POTS_RATE == 1
	for (int i = 0; i < BLOCK; i++) {
		ig += dig;
		int32_t x = clamp(mul29((in[2 * i] >> 1) + (in[2 * i + 1] >> 1), ig), -SAFE, SAFE);
		int32_t y = clamp(mul30(frame(x, &b), OUT_GAIN_Q30), -OUT_MAX, OUT_MAX);
		out[2 * i] = out[2 * i + 1] = y;
	}
#else
	/* the histories in locals for the block (notes/69 §20): the decimator's inputs 1, 2, 3 and 5 frames before this
	 * pair (h0, h1, h2, h4, the taps it reads); the interpolator's last three loop frames (p1..p3, the newest last) */
	int32_t h0 = st.dec[0], h1 = st.dec[1], h2 = st.dec[2], h4 = st.dec[3];
	int32_t p1 = st.itp[0], p2 = st.itp[1], p3 = st.itp[2];
	for (int i = 0; i < LOOP_FRAMES; i++) {
		ig += dig;
		int32_t x0 = clamp(mul29((in[4 * i] >> 1) + (in[4 * i + 1] >> 1), ig), -SAFE, SAFE);
		int32_t x1 = clamp(mul29((in[4 * i + 2] >> 1) + (in[4 * i + 3] >> 1), ig), -SAFE, SAFE);
		/* the decimator's sums then stay under 1.2 x 2^30 */
		int32_t x = -(x1 >> 5) + 9 * (h0 >> 5) + (h1 >> 1) + 9 * (h2 >> 5) - (h4 >> 5);
		h4 = h2;
		h2 = h0;
		h1 = x0;
		h0 = x1;
		int32_t y = clamp(mul30(frame(x, &b), OUT_GAIN_Q30), -OUT_MAX, OUT_MAX);   /* its sums under 0.94 */
		int32_t odd = -(p1 >> 4) + 9 * (p2 >> 4) + 9 * (p3 >> 4) - (y >> 4);
		out[4 * i] = out[4 * i + 1] = p2;
		out[4 * i + 2] = out[4 * i + 3] = odd;
		p1 = p2;
		p2 = p3;
		p3 = y;
	}
	st.dec[0] = h0; st.dec[1] = h1; st.dec[2] = h2; st.dec[3] = h4;
	st.itp[0] = p1; st.itp[1] = p2; st.itp[2] = p3;
#endif
}

void pots_reset(void)
{
	st.ready = 0;
}

#ifdef POTS_HOST
int32_t fx_line[LINE_FRAMES];

/* The proofs' entry: in, out frames x 2 (bus words); params (Time, Fdbk) x 256 a block; from silence. */
void pots_render(const int32_t *in, int32_t *out, int frames, const int16_t *params, int off, int32_t theta,
                 uint32_t seed)
{
	for (unsigned i = 0; i < sizeof st; i++)
		((uint8_t *)&st)[i] = 0;
	for (unsigned i = 0; i < LINE_FRAMES; i++)
		fx_line[i] = 0;
	st.rng = seed;
	dbg_off = off;
	dbg_theta = theta;
	for (int k = 0; k < frames / BLOCK; k++)
		pots_process(out + 2 * BLOCK * k, in + 2 * BLOCK * k, params + 2 * k);
}

int pots_rate(void) { return POTS_RATE; }

void pots_host_tempo(int32_t t) { tempo = t; }    /* the OS's word at 0x40149310 */
#endif
