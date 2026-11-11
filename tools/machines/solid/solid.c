/* SOLID for model27 (notes/71): an added machine, a bank of modes struck by a mallet, a noise burst or sustained
 * noise. model27's own work (durchgemacht and Claude), MIT, LICENSE next to this file; the sound was settled by ear
 * in a float prototype over three rounds with the maintainer (notes/71 §2), this is its fixed point, checked against
 * it wave for wave on the host (§4).
 *
 * SOLID_MODES modes, each a rotating phasor z <- r e^(jw) z + u, struck by an exciter u; the output is the sum of
 * the modes' imaginary parts, weighted by the pickup and the material's signature. Once a block of 32 frames:
 *
 *     SHAPE    Body: the material, gliding String > Membrane > Marimba > Bar > Bell > Glass (log-interpolated tables)
 *     COLOR    Bright: an exponent on the material's signature; 64 plays it as it is, lower is darker and
 *              shorter above
 *     SWEEP    Pickup: the point the body is heard at, |sin(pi k p)| over the modes
 *     CONTOUR  Exciter: soft to hard mallet (0..63), a noise burst of 3..150 ms (64..95), sustained noise (96..127)
 *     DECAY    the body's T60, 20 ms .. 8 s
 *     drop     (RETRIG + SWEEP, not wired yet: 0) the pitch falls from up to 24 semitones, scaled by velocity^2
 *
 * A strike halves the ringing body; a strike on another note or material while the body rings damps it by 12 dB
 * over 5 blocks first and strikes after them (the maintainer's choice of round 2). The exciter only knows the past:
 * a burst's level comes from its expected spectrum (tools/gen_solid.py), not from the burst itself.
 *
 * The voice plays at full level: the OS applies the trig's velocity after the voice loop (STANDARD.md §2.4). The
 * velocity only shapes the sound, a harder mallet, a deeper drop; SOLID reads it from the OS's gain of the block.
 *
 * The stock chain (notes/71 §3, §9): the amp envelope is set up the way TONE sets it but held open (its decay factor
 * 0x80000001, x (1 - 2^-31) a block), since the body has its own decay and GATE (the body is damped to 0.12 s when
 * the note ends). So the VCA would only multiply by 1, and in a trig's block cut the ringing body to 0: SOLID does
 * not call it. PUNCH as TONE sets it, its output stage at 1/2 (6 dB above TONE's); off, SOLID halves the block itself
 * instead of calling it. The ringing modes' loop is ring_cf.S on the device, ring() on the host: the same bits.
 *
 * Every product goes through the EMAC in signed fractional mode, never with a scale factor: on the device mac.l /
 * msac.l / movclr.l, on the host (SOLID_HOST) the same arithmetic as tools/emu/emac.py executes it, as in POTS
 * (notes/69). render saves MACSR, sets 0xa0 and gives MACSR back with acc0 empty, as SAMPLE's filter does: the stock
 * chain and the stock machines accumulate into acc0 without clearing it. Formats: the modes and the output Q27
 * (1.0 = 2^27, Q31 full scale on the bus), coefficients Q31, logarithms log2 in Q24, knobs 8.8. Plain C99, no
 * libc, no float, no 64-bit arithmetic on the device. Tables: solid_tables.h (tools/gen_solid.py). */
#include <stdint.h>
#include "solid_tables.h"

#ifndef SOLID_MODES
#define SOLID_MODES 8
#endif
#ifndef SUS_SLOPE
#define SUS_SLOPE 192               /* the sustained exciter feeds mode k by ratio^(-0.75), Q8 (round 2: -1.5) */
#endif
#define BLOCK 32
#define CHOKE_BLOCKS 5
#define IDLE (1 << 10)              /* -102 dB: below it the body is silent */
#define KNOB_MAX (127 << 8)

#ifdef SOLID_HOST
enum { D_VEL_IN = 1, D_CLICK_IMPULSE = 2 };
static int32_t dbg_flags;           /* the proofs' switches */
static int32_t dbg_slope = SUS_SLOPE;
long long solid_work;               /* mode-blocks rendered: what the device's load will scale with */
#define FLAG(x) (dbg_flags & (x))
#define SLOPE dbg_slope
#else
#define FLAG(x) 0
#define SLOPE SUS_SLOPE
#endif

/* --- the EMAC (as pots.c) ----------------------------------------------------------------------------------- */
#ifdef SOLID_HOST
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
/* A mul() empties the accumulator: never call one inside a run of mac. */
static inline int32_t mul(int32_t a, int32_t b) { mac(a, b); return movclr(); }          /* b Q31 */

static inline int32_t clamp(int32_t x, int32_t lo, int32_t hi) { return x < lo ? lo : x > hi ? hi : x; }
static inline int32_t fr31(int32_t x16) { return x16 >= 65536 ? 0x7fffffff : x16 << 15; }   /* 0..1 Q16 to Q31 */
static inline int32_t lerp(int32_t a, int32_t b, int32_t f31) { return a + mul(b - a, f31); }
static inline int32_t kmap(int32_t k, int32_t span) { return mul(clamp(k, 0, KNOB_MAX) << 16, span); }

static int32_t lg2(uint32_t x, int qx)              /* log2(x / 2^qx) in Q24, x > 0 */
{
	int p = 31 - clz32(x);
	uint32_t m = x << (31 - p);
	int i = (int)((m >> 25) & 63);
	int32_t f = (int32_t)((m >> 9) & 0xffff);
	return ((p - qx) << 24) + LOG2_T[i] + mul(LOG2_T[i + 1] - LOG2_T[i], f << 15);
}

static uint32_t ex2(int32_t l, int q)               /* 2^(l / 2^24) x 2^q; 2^32 - 1 above, 0 below 1 */
{
	int e = (l >> 24) + q - 30;
	uint32_t f = (uint32_t)l & 0xffffff;
	int j = (int)(f >> 16);                         /* 256 steps: 1e-6, a thousandth of a cent */
	uint32_t m = EXP2_T[j] + (uint32_t)mul((int32_t)(EXP2_T[j + 1] - EXP2_T[j]), (int32_t)((f & 0xffff) << 15));

	if (e >= 2)
		return 0xffffffffu;
	if (e >= 0)
		return m << e;
	return e <= -32 ? 0 : m >> -e;
}

static int32_t ex2_31(int32_t l, int q)
{
	uint32_t v = ex2(l, q);
	return v > 0x7fffffff ? 0x7fffffff : (int32_t)v;
}

static int32_t sin_t(uint32_t ph)                   /* sin(2 pi ph / 2^32), Q31 */
{
	uint32_t x = ph & 0x3fffffff, i;
	int32_t y;

	if (ph & 0x40000000)
		x = 0x40000000 - x;
	if (x >= 0x40000000) {
		y = SIN_T[256];
	} else {
		i = x >> 22;
		y = SIN_T[i] + mul(SIN_T[i + 1] - SIN_T[i], (int32_t)((x & 0x3fffff) << 9));
	}
	return ph & 0x80000000 ? -y : y;
}

static inline int32_t l2note(int32_t note)          /* log2 Hz of a note in semitones << 16 */
{
	return L2_440 + (note - (69 << 16)) * 64 / 3;
}

/* --- the voice ---------------------------------------------------------------------------------------------- */
struct knobs {              /* one block's inputs, from the voice and the parameters */
	int32_t strike;         /* 1 a strike in this block, 2 one on another note or material, else 0 */
	int32_t note;           /* the note played, semitones << 16 */
	int32_t color, shape, sweep, contour, decay, drop;     /* 8.8, 0 .. 127 */
	int32_t vel;            /* the strike's velocity, Q15 */
	int32_t gate;           /* GATE on */
	int32_t released;       /* the note has ended */
};

struct mode {                /* ring_cf.S reads it: zr +0, zi +4, c +8, s +12, a +16, 24 bytes */
	int32_t zr, zi;         /* the phasor, Q27 */
	int32_t c, s;           /* r cos w, r sin w, Q31 */
	int32_t a;              /* the output's weight, Q31 */
	int32_t bs;             /* the sustained exciter's weight, Q31 */
};
typedef char mode_layout[sizeof(struct mode) == 24 && __builtin_offsetof(struct mode, a) == 16 ? 1 : -1];

struct voice {
	struct mode m[SOLID_MODES];
	int32_t nm;             /* modes below 0.45 fs this block (the lowest first) */
	int32_t active;         /* the body rings or an exciter runs */
	uint32_t rng;
	int32_t vel, note, contour, choke, pending;            /* the strike's; blocks of choke left, a strike waiting */
	int32_t drop;           /* exp(-te / tau) since the strike, Q31 */
	int32_t m_n, m_w, m_amp;                /* mallet: frame, width, peak (Q27) */
	uint32_t m_ph, m_inc;
	int32_t c_n, c_env, c_prev, c_amp;      /* click */
	int32_t b_n, b_len, b_fo, b_k, b_lp;    /* noise burst: frame, length, fade-out, gain (Q28), the one-pole */
	uint32_t b_ph, b_inc;
	int32_t s_n, s_hold, s_lp, s_amp;       /* sustained noise: frame, end of the hold, the one-pole, gain (Q28) */
	int32_t s_on, s_gate;                   /* it runs; it is held until the note ends (GATE) */
	int32_t c_ok, c_note, c_shape, c_color, c_decay, c_sweep, c_cap, c_sus;   /* what the coefficients are for */
	int32_t c_dropf;                        /* the drop's factor a block, from DECAY */
};

/* The exciter's 32 frames: imp drives every mode, sus each mode by its bs, click goes to the output. One set for
 * every voice: the voice loop renders one track after the other. */
static int32_t imp[BLOCK], sus[BLOCK], click[BLOCK];

static uint32_t rnd(struct voice *v)
{
	v->rng = v->rng * 1664525u + 1013904223u;
	return v->rng;
}

static int32_t tri30(struct voice *v)               /* (u1 + u2) / 2 in Q30: variance 1/6 */
{
	int32_t a = (int32_t)rnd(v) >> 2;
	return a + ((int32_t)rnd(v) >> 2);
}

/* The exciter of the strike recorded in v, with the block's knobs k. CONTOUR 0..63: a mallet whose contact lasts
 * 0.35 to 0.03 of a period, its fundamental struck at the same level on every note, with a click that grows with
 * hardness; 64..95: a hard mallet fading out under a noise burst of 3 to 150 ms; 96..127: the 150 ms burst fading
 * into sustained noise, held while the note is (GATE) or a third of the body's T60. */
static void excite(struct voice *v, const struct knobs *k)
{
	int32_t c = clamp(v->contour, 0, KNOB_MAX), h, mw, bw, sw, u, ve, lf0;

	ve = FLAG(D_VEL_IN) ? fr31((v->vel + 1) << 1) : 0x7fffffff;
	if (c <= 63 << 8) {
		c = clamp(c + (v->vel - 24576) * 5 / 32, 0, 63 << 8);     /* velocity: +-20 on CONTOUR around 0.75 */
		h = c * 256 / 63;
		mw = 65536, bw = sw = 0, u = 0;
	} else if (c <= 95 << 8) {
		u = clamp((c - (64 << 8)) * 256 / 31, 0, 65536);
		h = 65536, mw = (65536 - u) * 3 / 10, bw = 65536, sw = 0;
	} else {
		sw = clamp((c - (96 << 8)) * 256 / 31, 0, 65536);
		h = 65536, mw = 0, bw = 65536 - sw, u = 65536;
	}
	lf0 = l2note(v->note);
	if (mw) {
		int32_t lq = L2_Q_SOFT + mul(fr31(h), Q_SPAN), w, qe, i, gm, a, h31;

		w = clamp((int32_t)((ex2(lq + L2_SR - lf0, 8) + 128) >> 8), 2, 480);
		qe = ex2_31(lg2((uint32_t)w, 0) + lf0 - L2_SR, 24);           /* the contact in periods of f0 */
		i = clamp(qe >> 18, 0, 63);
		gm = lerp(G_MALLET[i], G_MALLET[i + 1], qe >= 1 << 24 ? 0x7fffffff : (qe & 0x3ffff) << 13);
		a = mul(sin_t(0x40000000u / (uint32_t)w), gm) >> 1;          /* sin(pi / 2w) = 1 / the pulse's sum */
		v->m_amp = mul(mul(a, fr31(mw)), ve);
		v->m_w = w;
		v->m_n = 0;
		v->m_inc = 0x80000000u / (uint32_t)w;
		v->m_ph = v->m_inc >> 1;
		h31 = fr31(h);
		v->c_amp = mul(mul(FLAG(D_CLICK_IMPULSE) ? CLICK_AMP1 : CLICK_AMP, mul(h31, h31)), ve);
		v->c_n = 0;
		v->c_env = 0x7fffffff;
		v->c_prev = 0;
	}
	if (bw) {
		int32_t len = (int32_t)ex2(L2_BL0 + mul(fr31(u), BL_SPAN), 0), fo, s8, g, i, kk;

		len = len < 16 ? 16 : len;
		fo = len * 3 / 10;
		s8 = ((len - 24 - fo) << 8) + 2093 + 96 * (fo - 1) + 128;     /* the window's energy, Q8 */
		i = clamp(v->note >> 16, 0, 127);
		g = lerp(G_BURST[i], G_BURST[i + 1], (v->note & 0xffff) << 15);
		kk = mul(B_NS, ex2_31(-(lg2((uint32_t)s8, 8) >> 1), 31));
		kk = mul(mul(kk, BURST_GAIN << 1), fr31(bw));
		v->b_k = mul(mul(kk, g) << 3, ve);
		v->b_len = len;
		v->b_fo = fo;
		v->b_n = 0;
		v->b_lp = 0;
		v->b_inc = 0x80000000u / (uint32_t)(fo - 1);
		v->b_ph = 0;
	}
	if (sw) {
		if (v->s_on && v->s_n < S_ATT + v->s_hold)                    /* a held exciter goes on from its level */
			v->s_n = v->s_n < S_ATT ? v->s_n : S_ATT - 1;
		else
			v->s_n = 0, v->s_lp = 0;
		v->s_gate = k->gate;
		v->s_hold = k->gate ? 0x3fffffff
		            : clamp((int32_t)ex2(L2_T60_LO + kmap(k->decay, T60_SPAN) + L2_HOLD3, 0) - S_ATT, 0, 0x3fffffff);
		v->s_amp = mul(mul(S_NS, fr31(sw)), ve);
		v->s_on = 1;
	}
}

/* r = exp(-d) from log2 d, Q31: the series where d is small (a long T60 needs 1 - r to the last bit), else 2^x */
static int32_t decay_r(int32_t ld)
{
	int32_t d, d2, d3, d4;

	if (ld < -(4 << 24)) {
		d = ex2_31(ld, 31);
		d2 = mul(d, d);
		d3 = mul(d2, d);
		d4 = mul(d3, d);
		return 0x7fffffff - d + (d2 >> 1) - d3 / 6 + d4 / 24;
	}
	if (ld > 3 << 24)
		return 0;
	return ex2_31(-ex2_31(ld + L2_LOG2E, 24), 31);
}

/* The modes for this block: frequencies, decays, output and input weights. */
static void coeffs(struct voice *v, const struct knobs *k)
{
	int32_t lf0, x, seg, f31, ce, lt, p31, sum = 0, sc, kk, cap, semis;

	semis = mul(mul((clamp(k->drop, 0, KNOB_MAX) * 6192) >> 7, (v->vel * v->vel) << 1), v->drop);
	lf0 = l2note(v->note + semis);
	x = clamp(k->shape, 0, KNOB_MAX) * 1280 / 127;                  /* 5 shape / 127, Q16 */
	seg = x >> 16;
	f31 = fr31(x & 0xffff);
	if (seg >= 5)
		seg = 4, f31 = 0x7fffffff;
	ce = ex2_31((16384 - clamp(k->color, 0, KNOB_MAX)) * 8192 / 5, 28);   /* 2^((64 - COLOR) / 40), Q28 */
	lt = L2_T60_LO + kmap(k->decay, T60_SPAN) + lerp(LDAMP[seg], LDAMP[seg + 1], f31);
	cap = k->gate && k->released;
	p31 = 0x40000000 - clamp(k->sweep, 0, KNOB_MAX) * 31705;        /* (0.5 - 0.48 SWEEP / 127) 2^31 */
	for (kk = 0; kk < SOLID_MODES; kk++) {
		struct mode *m = &v->m[kk];
		int32_t lr = lerp(LR[seg][kk], LR[seg + 1][kk], f31), lf = lf0 + lr, lsa, lsd, lk, r, s, c, e, rg, w;
		uint32_t inc;

		if (lf >= L2_LIVE)
			break;
		lsa = mul(lerp(LSA[seg][kk], LSA[seg + 1][kk], f31), ce) << 3;
		lsd = mul(lerp(LSD[seg][kk], LSD[seg + 1][kk], f31), ce) << 3;
		lk = lt + lsd;
		if (cap && lk > L2_T_GATE)
			lk = L2_T_GATE;
		r = decay_r(L2_DK - lk);
		if (v->choke)
			r = mul(r, CHOKE_Q);
		inc = ex2(lf + L2_INC, 0);
		s = sin_t(inc);
		c = sin_t(inc + 0x40000000u);
		e = 0x7fffffff - mul(c, c) - mul(s, s);                     /* 1 - |table|^2: one Newton step to 1 */
		rg = r + mul(r, e >> 1);
		m->c = mul(c, rg);
		m->s = mul(s, rg);
		s = sin_t((uint32_t)(kk + 1) * (uint32_t)p31);
		w = mul(s < 0 ? -s : s, 2040109466) + 107374182;           /* 0.95 |sin(pi k p)| + 0.05 */
		m->a = mul(w, ex2_31(lsa, 31));
		sum += mul(m->a, m->a) >> 4;
		if (v->s_on)
			m->bs = ex2_31((lg2((uint32_t)(0x7fffffff - mul(r, r)) | 1, 31) >> 1) - (lr >> 8) * SLOPE, 31);
	}
	for (x = kk; x < v->nm; x++)                                    /* modes gone above 0.45 fs */
		v->m[x].zr = v->m[x].zi = 0;
	v->nm = kk;
	if (sum <= 0)
		return;
	sc = ex2_31(-(lg2((uint32_t)sum, 27) >> 1), 26);                 /* 1 / |a|, Q26 */
	for (x = 0; x < kk; x++) {
		int32_t t = mul(v->m[x].a, sc);                         /* a / |a|, at most 1 */

		v->m[x].a = mul((t > 0x3ffffff ? 0x3ffffff : t) << 5, GAIN);
	}
}

/* The exciter's block; returns 1 when imp carries a mallet or a burst in it, | 2 when click carries the click (the
 * buffers a block does not use are left as they are). */
static int exciter_block(struct voice *v)
{
	int n, f = 0;

	if (v->m_n < v->m_w || v->b_n < v->b_len) {
		f |= 1;
		for (n = 0; n < BLOCK; n++)
			imp[n] = 0;
	}
	if (v->c_n < CLICK_N) {
		f |= 2;
		for (n = 0; n < BLOCK; n++)
			click[n] = 0;
	}
	if (v->s_on)
		for (n = 0; n < BLOCK; n++)
			sus[n] = 0;
	for (n = 0; n < BLOCK && v->m_n < v->m_w; n++, v->m_n++) {
		imp[n] = mul(v->m_amp, sin_t(v->m_ph));
		v->m_ph += v->m_inc;
	}
	for (n = 0; n < BLOCK && v->c_n < CLICK_N; n++, v->c_n++) {
		int32_t x = FLAG(D_CLICK_IMPULSE) ? (v->c_n ? 0 : 0x7fffffff) : (int32_t)rnd(v), xe, d;

		xe = mul(x, v->c_env);
		d = (xe >> 1) - (v->c_prev >> 1);
		v->c_prev = xe;
		v->c_env = mul(v->c_env, CLICK_DEC);
		click[n] = mul(d, v->c_amp);
	}
	for (n = 0; n < BLOCK && v->b_n < v->b_len; n++, v->b_n++) {
		int32_t w, x = tri30(v);

		v->b_lp += mul(x - v->b_lp, B_LP);
		if (v->b_n < 24) {
			w = v->b_n * 93368854;                              /* n / 23 */
		} else if (v->b_n >= v->b_len - v->b_fo) {
			w = (1 << 30) + (sin_t(v->b_ph + 0x40000000u) >> 1);     /* (1 + cos) / 2 */
			v->b_ph += v->b_inc;
		} else {
			w = 0x7fffffff;
		}
		imp[n] += mul(mul(v->b_lp, w), v->b_k);
	}
	if (v->s_on) {
		for (n = 0; n < BLOCK; n++, v->s_n++) {
			int32_t e, j = v->s_n - S_ATT - v->s_hold, x = tri30(v);

			if (v->s_n < S_ATT)
				e = v->s_n * (0x7fffffff / (S_ATT - 1));
			else if (j < 0)
				e = 0x7fffffff;
			else if (j < S_REL)
				e = 0x7fffffff - j * (0x7fffffff / (S_REL - 1));
			else {
				v->s_on = 0;
				break;
			}
			v->s_lp += mul(x - v->s_lp, S_LP);
			sus[n] = mul(mul(v->s_lp, e), v->s_amp);
		}
	}
	return f;
}

/* One mode through the block. with_imp and with_sus are constants at each call: the loop without the inputs the block
 * does not have (adding 0 changes nothing: every variant gives the same bits). */
static inline __attribute__((always_inline)) int32_t ring(struct mode *m, int32_t *out, int with_imp, int with_sus,
                                                         int32_t peak)
{
	int32_t zr = m->zr, zi = m->zi, c = m->c, s = m->s, a = m->a, bs = m->bs, t;
	int n;

	for (n = 0; n < BLOCK; n++) {
		int32_t u = 0;

		if (with_imp)
			u = imp[n];
		if (with_sus)
			u += mul(bs, sus[n]);
		mac(zr, c);
		msac(zi, s);
		t = movclr();
		if (with_imp || with_sus)
			t += u;
		mac(zr, s);
		mac(zi, c);
		zi = movclr();
		zr = t;
		out[n] += mul(zi, a);
	}
	m->zr = zr;
	m->zi = zi;
	zr = zr < 0 ? -zr : zr;
	zi = zi < 0 ? -zi : zi;
	peak = zr > peak ? zr : peak;
	return zi > peak ? zi : peak;
}

/* Two ringing modes with no input, one pass: on the device ring_cf.S, the same products in the same accumulators'
 * order and each output product read on its own, so the same bits as two ring() (the output's two additions in
 * another order: integers). */
#ifdef SOLID_HOST
static void solid_ring2(struct mode *m, int32_t *out)
{
	ring(m, out, 0, 0, 0);
	ring(m + 1, out, 0, 0, 0);
}
#else
void solid_ring2(struct mode *m, int32_t *out);
#endif

static inline int32_t peak_of(const struct mode *m, int32_t peak)
{
	int32_t r = m->zr < 0 ? -m->zr : m->zr, i = m->zi < 0 ? -m->zi : m->zi;

	peak = r > peak ? r : peak;
	return i > peak ? i : peak;
}

/* One block of the voice into out (Q27). */
static void solid_block(struct voice *v, const struct knobs *k, int32_t *out)
{
	int32_t peak = 0;
	int n, kk, sus_on, ex;

	emac_start();
	if (k->strike) {
		v->vel = clamp(k->vel, 0, 32767);
		v->note = clamp(k->note, 0, 127 << 16);
		v->contour = k->contour;
		v->drop = 0x7fffffff;
		if (k->strike == 2 && v->active) {          /* a body that still rings: damped first, struck after */
			v->choke = CHOKE_BLOCKS;
			v->pending = 1;
		} else {
			for (kk = 0; kk < v->nm; kk++)
				v->m[kk].zr >>= CONTACT_SHIFT, v->m[kk].zi >>= CONTACT_SHIFT;
			v->pending = 0;
			excite(v, k);
		}
		v->active = 1;
	}
	if (v->pending && !v->choke) {
		v->pending = 0;
		excite(v, k);
	}
	if (v->s_gate && k->released) {                 /* GATE: the held exciter fades out once the note ends */
		v->s_hold = v->s_n > S_ATT ? v->s_n - S_ATT : 0;
		v->s_gate = 0;
	}
	if (!v->active) {
		for (n = 0; n < BLOCK; n++)
			out[n] = 0;
		return;
	}
	{                                               /* the coefficients only when one of their inputs moved */
		int32_t cap = k->gate && k->released;

		if (!v->c_ok || v->c_note != v->note || v->c_shape != k->shape || v->c_color != k->color
		    || v->c_decay != k->decay || v->c_sweep != k->sweep || v->c_cap != cap || v->c_sus != v->s_on) {
			coeffs(v, k);
			/* the drop falls exp(-te / tau), tau = 0.03 + 0.2 DECAY / 127 s: its factor a block */
			v->c_dropf = ex2_31(-ex2_31(L2_DROPK - lg2((uint32_t)(503316 + ((clamp(k->decay, 0, KNOB_MAX) * 6605)
			                                                                >> 6)), 24), 24), 31);
			v->c_note = v->note, v->c_shape = k->shape, v->c_color = k->color, v->c_decay = k->decay;
			v->c_sweep = k->sweep, v->c_cap = cap, v->c_sus = v->s_on;
			v->c_ok = 1;
		}
		if (v->choke || k->drop)                /* r damped while choking, the pitch falling: every block */
			v->c_ok = 0;
	}
	if (v->choke)
		v->choke--;
	sus_on = v->s_on;
	ex = exciter_block(v);
	if (ex & 2)
		for (n = 0; n < BLOCK; n++)
			out[n] = click[n];
	else
		for (n = 0; n < BLOCK; n++)
			out[n] = 0;
	if (sus_on && (ex & 1))
		for (kk = 0; kk < v->nm; kk++)
			peak = ring(&v->m[kk], out, 1, 1, peak);
	else if (sus_on)
		for (kk = 0; kk < v->nm; kk++)
			peak = ring(&v->m[kk], out, 0, 1, peak);
	else if (ex & 1)
		for (kk = 0; kk < v->nm; kk++)
			peak = ring(&v->m[kk], out, 1, 0, peak);
	else {                                          /* only ringing: two modes a pass */
		for (kk = 0; kk + 1 < v->nm; kk += 2) {
			solid_ring2(&v->m[kk], out);
			peak = peak_of(&v->m[kk + 1], peak_of(&v->m[kk], peak));
		}
		if (kk < v->nm)
			peak = ring(&v->m[kk], out, 0, 0, peak);
	}
#ifdef SOLID_HOST
	solid_work += v->nm;
#endif
	v->drop = mul(v->drop, v->c_dropf);
	if (!v->pending && !v->choke && v->m_n >= v->m_w && v->c_n >= CLICK_N && v->b_n >= v->b_len && !v->s_on
	    && peak < IDLE) {
		for (kk = 0; kk < SOLID_MODES; kk++)
			v->m[kk].zr = v->m[kk].zi = 0;
		v->active = 0;
	}
}

#ifdef SOLID_HOST
static struct voice hv;

/* The proofs' entry: n blocks of 11 words (struct knobs), from silence; out takes 32 frames a block, Q27. Without
 * D_VEL_IN the velocity of the last strike scales the block afterwards, as the OS does after the voice loop. */
void solid_host_render(const int32_t *blk, int nblocks, int32_t *out, uint32_t seed, int32_t flags, int32_t slope)
{
	int b, n;

	for (unsigned i = 0; i < sizeof hv; i++)
		((uint8_t *)&hv)[i] = 0;
	hv.rng = seed;
	dbg_flags = flags;
	dbg_slope = slope;
	solid_work = 0;
	for (b = 0; b < nblocks; b++) {
		const int32_t *p = blk + 11 * b;
		struct knobs k = { p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10] };

		solid_block(&hv, &k, out + BLOCK * b);
		if (!(flags & D_VEL_IN)) {
			int32_t g = fr31((hv.vel + 1) << 1);

			emac_start();
			for (n = 0; n < BLOCK; n++)
				out[BLOCK * b + n] = mul(out[BLOCK * b + n], g);
		}
	}
}

int solid_host_modes(void) { return SOLID_MODES; }
long long solid_host_work(void) { return solid_work; }

#else
/* --- the machine in the voice loop (STANDARD.md §2) --------------------------------------------------------- */
#define CYC_VOICE0  0x42308828u
#define CYC_VSTRIDE 0x31c
#define MARK_OFF    0x2c
#define MARK        0x4d4f4431                      /* 'MOD1' */

#define AMP_ENV(v)  ((void (*)(char *))0x400a9252)(v)
#define PUNCH(o, v) ((void (*)(int32_t *, char *))0x400a967a)(o, v)
#define VGAIN       ((const int16_t *)0x40fe4c90)   /* the velocity's gain of this block, 0..127, a track each */
#define HOLD_OPEN   ((int32_t)0x80000001)           /* the amp envelope's level x (1 - 2^-31) a block */

#define V32(o)      (*(int32_t *)(v + (o)))
#define P16(o)      (*(const int16_t *)(p + (o)))

static struct voice trk[6];
static struct knobs kin[6];
static int32_t last_note[6], last_shape[6];
static int32_t ended[6];        /* the note has ended since the strike: the voice loop sets v+0x3c for one block only
                                 * (0x400a7da8, from the release mask), the core needs it until the next strike */

void solid_update(int32_t pmod, char *v, const char *p)
{
	uint32_t t = ((uint32_t)v - CYC_VOICE0) / CYC_VSTRIDE;
	struct knobs *k = &kin[t];
	int32_t note, d;

	if (V32(MARK_OFF) != MARK) {                    /* first block since the track changed machine: silence */
		for (unsigned i = 0; i < sizeof trk[t]; i++)
			((uint8_t *)&trk[t])[i] = 0;
		trk[t].rng = 0x12345678u + (uint32_t)t * 0x9e3779b9u;
		ended[t] = 0;
		V32(MARK_OFF) = MARK;
	}
	/* the stock amp chain, set up the way TONE sets it (0x400aa7b8), as MACRO, ACID and SAMPLE do */
	if (V32(0x38)) {
		V32(0x274) = V32(0x278) = 0x012c0f26;
		V32(0x280) = V32(0x284) = 0x001f7c5c;
		V32(0x290) = V32(0x294) = 0x7fffffff;
		V32(0x27c) = 0x82581e4b;
		V32(0x288) = 0x803ef8b8;
		/* PUNCH as TONE sets it (on 0x400aa8de, off 0x400aa8fe), but the output stage +0x2a4 at 1/2, not 1/4:
		 * SOLID 6 dB louder than TONE's chain, up to TONE's peak (the maintainer, 2026-11-11, notes/71 §6) */
		if (P16(0x1e)) {
			V32(0x29c) = 0x20000000; V32(0x2a0) = 0x60000000; V32(0x2a4) = 0x40000000;
			V32(0x48) = 1;
		} else {                                /* off: the output x 1/2 */
			V32(0x29c) = 0x7fffffff; V32(0x2a0) = 0x20000000; V32(0x2a4) = 0x40000000;
			V32(0x48) = 0;
		}
	}
	V32(0x250) = HOLD_OPEN;                         /* not DECAY's: the body decays, the envelope stays open */
	/* the note as every machine computes it: the trig's note + PITCH - 64 + FINE (+-2 semitones) */
	note = pmod + ((int32_t)P16(0x14) << 8) + (((int32_t)P16(0x22) - 0x4000) << 3) - (64 << 16);
	k->note = clamp(note, 0, 127 << 16);
	k->color = P16(0x16);
	k->shape = P16(0x18);
	k->sweep = P16(0x1a);
	k->contour = P16(0x1c);
	k->decay = P16(0x24);
	k->drop = 0;
	k->gate = P16(0x20) != 0;
	if (V32(0x38))                                  /* the strike's block: its note has not ended yet */
		ended[t] = 0;
	if (V32(0x3c) && !V32(0x34))                    /* the note's end, not in a trig's block */
		ended[t] = 1;
	k->released = k->gate && ended[t];
	k->strike = 0;
	if (V32(0x38)) {
		k->vel = clamp(VGAIN[t], 0, 127) * 258;
		d = k->shape - last_shape[t];
		k->strike = k->note != last_note[t] || d >= 256 || d <= -256 ? 2 : 1;
		last_note[t] = k->note;
		last_shape[t] = k->shape;
	}
}

void solid_render(int32_t *out, char *v)
{
	uint32_t t = ((uint32_t)v - CYC_VOICE0) / CYC_VSTRIDE;
	int32_t macsr;
	int n;

	if (!trk[t].active && !kin[t].strike) {         /* nothing rings and nothing is struck */
		for (n = 0; n < BLOCK; n++)
			out[n] = 0;
		return;
	}
	__asm__ volatile("move.l %%macsr,%0" : "=d"(macsr));
	solid_block(&trk[t], &kin[t], out);
	/* No VCA: the envelope is held open at full level, where the VCA only multiplies by 1 (and would cut the ringing
	 * body in a trig's block). PUNCH off multiplies by 4 x 0x20000000 x 0x40000000 = 1/2: SOLID halves the block
	 * itself, Q27 to half the bus (notes/71 §9). */
	if (V32(0x48)) {                                /* PUNCH on: Q27 to Q31, 1.0 full scale, into the stock PUNCH */
		for (n = 0; n < BLOCK; n++)
			out[n] = out[n] > 0x7ffffff ? 0x7fffffff : out[n] < -0x8000000 ? INT32_MIN : out[n] << 4;
		AMP_ENV(v);
		PUNCH(out, v);
	} else {
		for (n = 0; n < BLOCK; n++) {
			int32_t x = clamp(out[n], -0x8000000, 0x7ffffff);

			out[n] = (int32_t)((uint32_t)x << 3);
		}
		AMP_ENV(v);
	}
	__asm__ volatile("move.l %0,%%macsr" : : "d"(macsr));
}
#endif
