/* Digital Delay for model27's delay slot (notes/68 §18): PPPCCC's digital delay, bright and clean, up to 5.4 s, each
 * repeat a little thinner in the lows. From PPPCCC's Model:Cycles 1.13 Mods 2.0.0 (gialloinfuso, commit db7a846f,
 * patch 06 delay-fx: src/gen_digidelay_113.py, src/gen_fx4.py, src/v2/g2_delayfx.py), MIT, LICENSE next to this
 * file. Ported to C as an effect package by durchgemacht and Claude, same license: the arithmetic is PPPCCC's, step
 * for step, so that the sound is theirs bit for bit (tools/emu/test_fxslot.py compares it with their own code).
 *
 * Mono: the send's two channels summed (each / 8), one line of 262 144 frames (5.46 s at 48 kHz), the same repeat
 * on both outputs. Each frame:
 *
 *     the delay slews towards the knob's: by 1/8192 of the distance, or one frame every fourth frame when closer;
 *     d   = line[w - delay]                              (what was written that long ago, 0 before it was written)
 *     x   = d g / 32768 + in                             saturated; g = (3 t - t^3) / 2, t = Fdbk 0..127 x 258
 *     lp  = 13/16 x + 3/16 lp                            a low-pass of about 12.8 kHz, saturated
 *     hp += (lp - hp) / 32;  line[w] = (lp - hp) 31/32   a high-pass of about 240 Hz, in the feedback
 *     out = 6 d                                          saturated, on both channels
 *
 * The knob's delay, in frames, is the stock delay's (0x4005802e reads the same word): ((Time + 256) 48000 / 1024)
 * 900 / tempo, the tempo the OS keeps at 0x40149310, between 32 and 261 120 frames. PPPCCC adds the exact triplets of
 * their delay-notes patch when it is installed; model27 has no such patch, so the + 256 is the stock one.
 *
 * Contract (notes/68 §15.3, §16.3): digi_process(out, in, params), called as the stock delay 0x40057488 is, params
 * P + 428 (Time at +0, Fdbk at +2, x 256). The line is the delay slot's, 1 MiB (one word a frame: the delay is mono),
 * shared with the slot's other effects: after digi_reset its content is someone else's, so a frame is read only once
 * it was written since the reset (n counts them). digi_reset() only marks the state: the first block after it starts
 * again from silence, as PPPCCC's first block does. The C ABI keeps d2-d7/a2-a6, as the stock delay does. */
#include <stdint.h>

#define FRAMES 0x40000u                     /* the line, a power of two */
#define MASK (FRAMES - 1)
#define LONGEST 261120u                     /* frames, PPPCCC's 0x3fc00 */
#define SHORTEST 32u
#define TEMPO (*(volatile int32_t *)0x40149310)

extern int32_t fx_line[];                   /* the delay slot's line: FRAMES words (notes/68 §16) */

static struct {
	uint32_t ready;                         /* 0 at start-up and after digi_reset */
	uint32_t w;                             /* the frame written next */
	uint32_t delay;                         /* the delay now, frames */
	uint32_t n;                             /* frames written since the reset, up to FRAMES */
	int32_t lp, hp;
} st;

static int32_t sat(int32_t a, int32_t b)
{
	int32_t s = (int32_t)((uint32_t)a + (uint32_t)b);
	if (((a ^ s) & (b ^ s)) < 0)
		s = a < 0 ? INT32_MIN : INT32_MAX;
	return s;
}

static int32_t gain(int16_t fdbk)
{
	int32_t f = fdbk >> 8;
	if (f < 0)
		f = 0;
	if (f > 127)
		f = 127;
	int32_t t = f * 258;
	int32_t c = (t * t) >> 15;
	c = (c * t) >> 15;
	return (3 * t - c) >> 1;
}

static uint32_t knob_delay(int16_t time)
{
	uint32_t d = (uint32_t)((((int32_t)time + 256) * 48000 >> 10) * 900 / TEMPO);
	if (d > LONGEST)
		d = LONGEST;
	if (d < SHORTEST)
		d = SHORTEST;
	return d;
}

void digi_process(int32_t *out, const int32_t *in, const int16_t *params)
{
	int32_t g = gain(params[1]);
	uint32_t target = knob_delay(params[0]);
	if (!st.ready) {
		st.ready = 1;
		st.w = st.n = 0;
		st.lp = st.hp = 0;
		st.delay = target;
	}
	uint32_t w = st.w, delay = st.delay, n = st.n;
	int32_t lp = st.lp, hp = st.hp;
	for (int f = 0; f < 32; f++) {
		int32_t diff = (int32_t)(target - delay), step = diff >> 13;
		if (step == 0 && diff != 0 && !(w & 3))
			step = diff > 0 ? 1 : -1;
		delay += (uint32_t)step;
		int32_t d = delay <= n ? fx_line[(w - delay) & MASK] : 0;
		int32_t x = (int32_t)((uint32_t)((d >> 15) * g) + (uint32_t)(((d & 0x7fff) * g) >> 15));
		x = sat(x, (in[2 * f] >> 3) + (in[2 * f + 1] >> 3));
		int32_t q = x >> 3, p = lp >> 3;
		lp = sat(x - (q + (q >> 1)), p + (p >> 1));
		int32_t h = (int32_t)((uint32_t)lp - (uint32_t)hp), e = h >> 5;
		hp = (int32_t)((uint32_t)hp + (uint32_t)e);
		fx_line[w] = (int32_t)((uint32_t)h - (uint32_t)e);
		if (n < FRAMES)
			n++;
		int32_t y2 = sat(d, d), y4 = sat(y2, y2);
		out[2 * f] = out[2 * f + 1] = sat(y4, y2);
		w = (w + 1) & MASK;
	}
	st.w = w;
	st.delay = delay;
	st.n = n;
	st.lp = lp;
	st.hp = hp;
}

void digi_reset(void)
{
	st.ready = 0;
}
