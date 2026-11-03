/* POTS for model27's delay slot (notes/69): a mono delay whose repeats go down an old telephone line on every pass.
 * model27's own work (durchgemacht and Claude), MIT, LICENSE next to this file; the sound was settled by ear in a float
 * prototype (notes/69 §2), its fixed point checked against it wave for wave (§12.2); since 0.2 the loop runs at 6 kHz
 * with cheaper parts, for about a third of 0.1's load, chosen by ear on a listening page (§24).
 *
 * Each loop frame, everything from the read to the write inside the feedback:
 *
 *     read      line[w - D], D from Time by the stock formula, slewing as Digital Delay's
 *     scatter   + a second tap 3..18 loop frames (24..144 at 48 kHz) further back, wandering, a whole frame
 *     shift     a Hilbert pair (2 + 2 sections, 300 Hz to 2.7 kHz) and a phasor: the repeat moves up 2 Hz a pass,
 *               the speed wandering +-40 %
 *     fading    +-6 dB, wandering; now and then a dropout of -18 dB for 8..25 ms
 *     receiver  a 2-pole high pass at 350 Hz, so that no bass sets the codec's steps; the codec (G.711 mu-law,
 *               8 bits), faded out as the tail falls from -40 to -52 dB; +6 dB at 1.5 kHz, the loudest frequency at
 *               unity; the band's top is the loop's Nyquist, 3 kHz
 *     leveler   3:1 above 0.25 in the loop; on the echo a make-up towards 0.15, 0.6..2.5, x 1.5
 *     feedback  Digital Delay's curve x 1.20 (FB_MAX)
 *     sender    the skewed clip (c(3 s + 0.12) - c(0.12)) / 3, c(x) = x - 4 x^3 / 27; a 200 Hz high pass
 *
 * Before the sender, outside the loop, a limiter holds the send at the level v6 was tuned at (0.5, the median machine
 * at Delay Send 127): the peak of the send as it comes (L / 2 + R / 2, every 4th frame), a 0.2 s release, the gain
 * ramped over the block. Under that level the send passes as it is.
 *
 * The loop at 6 kHz (notes/69 §24): 48 -> 6 kHz by a second-order CIC (the triangle 1, 2 .. 8 .. 2, 1 over 15 frames,
 * pots_cf.S), 6 -> 48 kHz by a line from each loop frame to the next. The control (the leveler's gains, the fading,
 * the scatter and the shift's speed, the phasor's level) takes one part a block in turn, each ramped over 16 loop
 * frames. Samples Q2.29 (1.0 = 2^29, the codec's full scale); the send bus carries 1.0 as K_BUS (measured, §12.4),
 * IN_GAIN_Q29 and OUT_GAIN_Q30 take it in and the echo out. Every product goes through the EMAC in signed fractional
 * mode, never with a scale factor: on the device mac.l / msac.l / movclr.l, on the host (POTS_HOST) the same
 * arithmetic as tools/emu/emac.py executes it (each product truncated to 2^-23 of an LSB, the accumulator read as
 * acc >> 31, saturated), so that both give the same bits. Tables and constants: pots_tables.h (tools/gen_pots.py).
 *
 * The state is reached through a base register (stp()) and the filters' last two values are kept by slot (the
 * frame's parity, w & 1, names the older one, which is read and then overwritten), so that nothing is shifted: the
 * code is smaller, and in the cache model of notes/27 a cold code line costs about ten instructions (§23, §24).
 *
 * A full-scale bus must not wrap anywhere (notes/69 §14.1): the input and the feedback are added saturating, the
 * clip clamps its input, the filters run on the EMAC (saturated when read), the echo is held at +-0.75 of full scale.
 * Built with -fwrapv on both sides.
 *
 * Contract (notes/68 §15.3, §16.3): pots_process(out, in, params), called as the stock delay 0x40057488 is, params
 * P + 428 (Time at +0, Fdbk at +2, x 256). The line is the delay slot's, LINE_FRAMES words, shared with the slot's other
 * effects: after pots_reset a frame is read only once it was written since (n counts them). pots_reset() only marks
 * the state. The C ABI keeps d2-d7/a2-a6; the EMAC is free (MACSR and acc0 are set here, the mixer sets MACSR again
 * after the call). */
#include <stdint.h>

#ifndef POTS_RATE
#define POTS_RATE 8
#endif
#if POTS_RATE != 8
#error "POTS 0.2 runs its loop at 6 kHz (POTS_RATE 8) only; 0.1's rates are in its history (notes/69 §23)"
#endif
#include "pots_tables.h"

#define BLOCK 32
#define MASK (LINE_FRAMES - 1)

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

static int32_t tri(uint32_t ph)     /* a triangle, -1..1 in Q31, its top at ph = 2^31 (the shift's drift) */
{
	uint32_t p = ph ^ (uint32_t)((int32_t)ph >> 31);
	return (int32_t)((p << 1) - 0x80000000u);
}

static inline int32_t mulaw(int32_t x)   /* the codec, G.711 mu-law encoded and decoded on 16 bits: full scale 1.0 */
{
	int32_t a = x < 0 ? -x : x;     /* INT32_MIN stays negative: the top code */
	uint32_t m = (uint32_t)a >> 14;
	if (a < 0 || m > 32635)
		m = 32635;
	m += 0x84;                      /* 132 .. 32767: the top bit 7 .. 14 */
	int e = 24 - clz32(m);          /* the segment, 0 .. 7 */
	uint32_t v = ((((m >> (e + 3)) & 15) << 3) + 0x84) << e;
	int32_t r = (int32_t)(v - 0x84) << 14;
	return x < 0 ? -r : r;
}

/* --- the state ---------------------------------------------------------------------------------------------- */
typedef struct { int32_t v, target, coef; int left, min_blocks, max_blocks; } wander;

struct state {
	uint32_t ready, w, d, n;
	int32_t ha[HIL_N + 1][2], hb[HIL_N + 1][2], a_prev;   /* the Hilbert pair: the input's, then each section's output's
	                                                      * last two, by slot; a_prev chain a's last output */
	int32_t rh[2][2];                               /* the receiver's high pass: its input's and output's last two */
	int32_t px[2], py[2];                           /* its peak: the same */
	int32_t txx, txy;                               /* the sender's high pass: its last input and output */
	int32_t pc, ps;                                 /* the shift's phasor, Q31 */
	uint32_t ph1, ph2;                              /* its speed's slow wander */
	int32_t env, gc, gw, fade_g, scat;              /* Q29, Q31, Q29, Q29, Q16 frames */
	wander fade, sc;
	int gap_wait, gap_on;
	uint32_t rng;
	int32_t cr;                                     /* the CIC: the last loop frame's second sum */
	int32_t yo;                                     /* the echo's last loop frame, where the line out starts */
	int32_t lim, ig;                                /* the limiter: the send's envelope (bus words), the input's gain */
	uint32_t blk;                                   /* the block count: the control's part is blk & 3 */
	int32_t dgc, dgw, dfade, dscat, cs, sn;         /* the ramps of gc, gw, fade_g, scat; the shift's step */
};
static struct state st_;

/* The state through a pointer GCC cannot see through, so that it is reached as d16(An) (4 bytes an access) rather
 * than by absolute addresses (6 to 10 bytes): the same code, a third smaller (notes/69 §24). */
static inline struct state *stp(void)
{
	struct state *p = &st_;
#ifndef POTS_HOST
	__asm__("" : "+a"(p));
#endif
	return p;
}
#define STATE struct state *const sp_ = stp()
#define st (*sp_)

static uint32_t rnd(void)
{
	STATE;
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
	return (d + POTS_RATE / 2) / POTS_RATE;
}

static void init(uint32_t target)
{
	STATE;
	uint32_t keep = st.rng;
	for (unsigned i = 0; i < sizeof st / 4; i++)      /* by words: the state is a multiple of 4 bytes */
		((uint32_t *)&st)[i] = 0;
	st.rng = keep ? keep : 7;
	st.ready = 1;
	st.d = target;
	st.pc = PHASOR_M;
	st.cs = INT32_MAX;
	st.gc = INT32_MAX;
	st.gw = st.fade_g = 1 << 29;
	st.ig = IN_GAIN_Q29;
	st.fade.coef = FADE_COEF;                         /* the wanders count in turns of 4 blocks */
	st.fade.min_blocks = 11;
	st.fade.max_blocks = 56;
	st.sc.coef = SCAT_COEF;
	st.sc.min_blocks = 188;
	st.sc.max_blocks = 750;
	st.scat = SC_MIN_Q16 + (SC_SPAN_Q16 >> 1);
	st.gap_wait = 562;
}

/* --- one loop frame ----------------------------------------------------------------------------------------- */
/* allpasses (c - z^-2) / (1 - c z^-2); h[0] the input's last two, h[k + 1] section k's output's, slot p the older:
 * read, then overwritten with the new value */
static inline int32_t chain(int32_t (*h)[2], const int32_t *c, int32_t x, int p)
{
	int32_t x2 = h[0][p];
	h[0][p] = x;
	for (int k = 0; k < HIL_N; k++) {
		int32_t y2 = h[k + 1][p];
		int32_t y = mul(x + y2, c[k]) - x2;
		h[k + 1][p] = y;
		x = y;
		x2 = y2;
	}
	return x;
}

static int32_t line_at(uint32_t back)
{
	STATE;
	return back <= st.n ? fx_line[(st.w - back) & MASK] : 0;
}

/* The CIC of 48 -> 6 kHz, the triangle (1, 2 .. 8 .. 2, 1) over 15 frames: for each loop frame's 8 frames (k = 0..7,
 * L and R) acc0 = sum (8 - k) w / 128 and acc1 = sum k w / 128; the loop frame is acc0 + the last one's acc1, which
 * *r keeps: (L + R) / 2 for a constant input. pots_cf.S on the device (MAC with load); here its model. */
#ifdef POTS_HOST
static void pots_cic(const int32_t *in, int32_t *x, int32_t *r)
{
	for (int i = 0; i < LOOP_FRAMES; i++, in += 16) {
		for (int k = 0; k < 16; k++)
			mac(in[k], (8 - (k >> 1)) << 24);
		int32_t a0 = movclr();
		for (int k = 2; k < 16; k++)
			mac(in[k], (k >> 1) << 24);
		x[i] = (int32_t)((uint32_t)a0 + (uint32_t)*r);
		*r = movclr();
	}
}
#else
void pots_cic(const int32_t *in, int32_t *x, int32_t *r);
#endif

typedef struct { int32_t target, fb, grain_w; } blockv;

static int32_t frame(int32_t x_in, const blockv *b)
{
	STATE;
	int32_t diff = (int32_t)(b->target - st.d);
	if (diff) {                                         /* Time slides; two instructions a frame while it stands */
		int32_t step = diff >> 10;
		if (step == 0 && !(st.w & 1))
			step = diff > 0 ? 1 : -1;
		st.d += (uint32_t)step;
	}

	int32_t x = line_at(st.d);
	if (!OFF(D_SCAT)) {                                 /* the second tap, scat (Q16) frames further back */
		int32_t tap = line_at(st.d + ((uint32_t)st.scat >> 16));
		mac(x, SC_NORM); mac(tap, SC_GAIN_N);
		x = movclr();
		st.scat += st.dscat;
	}

	/* the shift: the Hilbert pair on x / 2, the phasor turning once a frame */
	int p = (int)(st.w & 1);
	int32_t va = chain(st.ha, HIL_A, x >> 1, p), vb = chain(st.hb, HIL_B, x >> 1, p);
	int32_t I = st.a_prev, Q = vb;
	st.a_prev = va;
	mac2(I, st.pc);
	mac2(Q, st.ps);
	int32_t y = movclr();
	mac(st.pc, st.cs); msac(st.ps, st.sn);
	int32_t pc = movclr();
	mac(st.ps, st.cs); mac(st.pc, st.sn);
	st.ps = movclr();
	st.pc = pc;
	if (OFF(D_SHIFT))
		y = x;

	if (!OFF(D_FADE)) {
		y = mul29(y, st.fade_g);
		st.fade_g += st.dfade;
	}
	if (!OFF(D_RX)) {                                   /* the high pass: b0 (x - 2 x' + x'') - a1 y' - a2 y'' */
		int32_t x1 = st.rh[0][p ^ 1], x2 = st.rh[0][p], y1 = st.rh[1][p ^ 1], y2 = st.rh[1][p];
		st.rh[0][p] = y;
		mac(y, HP_B0); mac(x2, HP_B0); msac(x1, HP_B0); msac(x1, HP_B0);
		mac(y1, HP_A1H); mac(y1, HP_A1H); msac(y2, HP_A2);
		y = st.rh[1][p] = movclr();
	}
	if (!OFF(D_CODEC))
		y += mul(mulaw(y) - y, b->grain_w);
	if (!OFF(D_RX)) {                                   /* the peak at fs / 4: b0 x + b2 x'' - a2 y'' */
		mac(y, PK_B0); mac(st.px[p], PK_B2); msac(st.py[p], PK_A2);
		st.px[p] = y;
		y = st.py[p] = movclr();
	}

	int32_t loop = mul(y, st.gc), wet = mul29(y, st.gw);
	st.gc += st.dgc;
	st.gw += st.dgw;
	int32_t s = add_sat(x_in, mul30(loop, b->fb));
	if (!OFF(D_TX)) {
		if (!OFF(D_CLIP)) {                             /* u within +-1.5 by one clamp; (u / 4)^3 in Q31 */
			int32_t u = DRIVE * clamp(s, CLIP_LO, CLIP_HI) + GRIT_BIAS;
			int32_t u3 = mul(mul(u, u), u);
			int32_t c = u - (mul(u3, SAT_K4) << 2) - SAT_BIAS_OUT;
			s = mul(c, DRIVE_INV_Q31);
		}
		mac(st.txy, TX_HP_A); mac(s, TX_HP_A); msac(st.txx, TX_HP_A);
		st.txx = s;
		s = st.txy = movclr();
	}
	fx_line[st.w] = OFF(D_TX | D_CLIP) ? clamp(s, -SAFE, SAFE) : s;   /* the sender keeps it under 1.0 */
	st.w = (st.w + 1) & MASK;
	if (st.n < LINE_FRAMES)
		st.n++;
	return wet;
}

/* --- one block ---------------------------------------------------------------------------------------------- */
void pots_process(int32_t *out, const int32_t *in, const int16_t *params)
{
	STATE;
	blockv b;
	int32_t xin[LOOP_FRAMES];
	emac_start();
	b.target = (int32_t)knob_delay(params[0]);
	b.fb = gain(params[1]) * FB_MAX;                      /* Q15 x Q15 = Q30 */
	if (!st.ready)
		init((uint32_t)b.target);

	/* 48 -> 6 kHz; the limiter's peak on the send as it comes, L / 2 + R / 2 every 4th frame (the band-limited frames
	 * hardly show a beat's peaks, which v6's limiter was tuned on) */
	pots_cic(in, xin, &st.cr);
	int32_t pk = 0;
	for (const int32_t *q = in; q < in + 2 * BLOCK; q += 8) {
		int32_t v = (q[0] >> 1) + (q[1] >> 1);
		v = v < 0 ? -v : v;
		if (v > pk)
			pk = v;
	}

	/* the leveler's envelope: it looks at this block's frames on the line before playing them */
	int32_t peak = 0;
	for (int i = 0; i < LOOP_FRAMES; i++) {
		int32_t v = line_at(st.d - (uint32_t)i);
		v = v < 0 ? -v : v;
		if (v > peak)
			peak = v;
	}
	st.env += peak > st.env ? (peak - st.env) >> 1 : mul(peak - st.env, ENV_REL);
	b.grain_w = st.env >= GATE_HI ? INT32_MAX : st.env <= GATE_LO ? 0 : (st.env - GATE_LO) * GATE_K;

	/* the control, one part a block in turn: each target once in 4 blocks, ramped over the 16 loop frames that follow */
	switch (st.blk++ & 3) {
	case 0: {                                           /* the leveler's gains */
		int32_t gc1 = INT32_MAX, gw1 = 1 << 29;
		if (!OFF(D_LEVEL)) {
			if (st.env > (1 << 27)) {                   /* above 0.25: 3:1 */
				int32_t g = ex2(mul(COMP_EXP, COMP_THR_L2 - lg2(st.env)));
				gc1 = g >= (1 << 29) ? INT32_MAX : g << 2;
			}
			gw1 = st.env > 537 ? clamp(ex2((LEV_TARGET_L2 - lg2(st.env)) >> 1), LEV_MIN, LEV_MAX) : LEV_MAX;
			gw1 = mul30(gw1, WET_GAIN);
		}
		st.dgc = (gc1 - st.gc) >> (LOOP_SHIFT + 2);
		st.dgw = (gw1 - st.gw) >> (LOOP_SHIFT + 2);
		break;
	}
	case 1: {                                           /* the fading and its dropouts */
		int32_t fade1 = OFF(D_FADE) ? 1 << 29 : ex2(mul(wander_step(&st.fade), FADE_L2) >> 6);
		if (!OFF(D_FADE)) {
			if (st.gap_on > 0) {
				st.gap_on--;
				fade1 >>= 3;
			} else if (--st.gap_wait <= 0) {
				st.gap_on = span(3, 10);
				st.gap_wait = span(562, 1875);
				fade1 >>= 3;
			}
		}
		st.dfade = (fade1 - st.fade_g) >> (LOOP_SHIFT + 2);
		break;
	}
	case 2: {                                           /* the scatter's wander; the shift's speed, 2 Hz x (1 + 0.4 (0.7
		                                                 * tri + 0.3 tri)) */
		int32_t v = wander_step(&st.sc);
		int32_t s1 = SC_MIN_Q16 + mul(((v >> 1) + (1 << 29)) << 1, SC_SPAN_Q16);
		st.dscat = (s1 - st.scat) >> (LOOP_SHIFT + 2);
		int32_t m = mul(tri(st.ph1), DRIFT_W1) + mul(tri(st.ph2), DRIFT_W2);
		st.ph1 += DRIFT_INC1;
		st.ph2 += DRIFT_INC2;
		int32_t th = THETA0 + mul(THETA0, mul(m, DRIFT_D));
#ifdef POTS_HOST
		if (dbg_theta)
			th = dbg_theta;
#endif
		st.cs = INT32_MAX - (mul(th, th) >> 1);
		st.sn = th;
		break;
	}
	default: {                                          /* the phasor held on its circle */
		int32_t m2 = mul(PHASOR_M, PHASOR_M);           /* before the run of mac below */
		mac(st.pc, st.pc); mac(st.ps, st.ps);
		int32_t e = (m2 - movclr()) >> 1;
		st.pc += mul(st.pc, e);
		st.ps += mul(st.ps, e);
	}
	}

	/* the limiter, every block: the input's gain LIM_BUS / lim (a division), IN_GAIN_Q29 itself while the send stays
	 * under, ramped over the block */
	st.lim = pk > st.lim ? pk : mul(st.lim, LIM_REL);
	int32_t ig = st.ig, ig1 = IN_GAIN_Q29;
	if (st.lim > LIM_BUS) {
		uint32_t r = (uint32_t)LIM_BUS / ((uint32_t)st.lim >> 15);
		ig1 = mul(IN_GAIN_Q29, (int32_t)((r > 32767 ? 32767 : r) << 16));
	}
	int32_t dig = (ig1 - ig) >> LOOP_SHIFT;
	st.ig = ig1;

	/* the loop, and 6 -> 48 kHz: a line over 8 frames from each loop frame's echo to the next */
	int32_t yo = st.yo, *q = out;
	for (int i = 0; i < LOOP_FRAMES; i++) {
		ig += dig;
		int32_t x = mul29(xin[i], ig);                  /* the feedback's sum saturates, the clip clamps */
		int32_t y = clamp(mul30(frame(x, &b), OUT_GAIN_Q30), -OUT_MAX, OUT_MAX);
		int32_t d = (y >> 3) - (yo >> 3), o = yo;
#pragma GCC unroll 8
		for (int k = 0; k < 8; k++) {
			o += d;
			*q++ = o;
			*q++ = o;
		}
		yo = y;
	}
	st.yo = yo;
}

void pots_reset(void)
{
	STATE;
	st.ready = 0;
}

#ifdef POTS_HOST
int32_t fx_line[LINE_FRAMES];

/* The proofs' entry: in, out frames x 2 (bus words); params (Time, Fdbk) x 256 a block; from silence. */
void pots_render(const int32_t *in, int32_t *out, int frames, const int16_t *params, int off, int32_t theta,
                 uint32_t seed)
{
	STATE;
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
