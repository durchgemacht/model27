/* Crush: a sample-rate and bit reduction on every track whose sound chose it (Track FX, notes/73), id 2 of the
 * builder's filter slot (tools/machines/fltslot/), which calls it after Volume + Dist with the track's block and its
 * smoothed k 28 to k 31: p-locks, the LFO and the velocity move the values as they move any parameter.
 *
 * Rate, k 28 (RETRIG + SWEEP): off at the centre; a = |word - centre| in 8.8 (0 to 64) takes one frame in 2^(6a/64),
 * down to 1/64 of 48 kHz at the left end and about 1/60 at the right. To the right of the centre a hard hold: each
 * taken frame is held until the next (aliasing). To the left a soft one: the output runs on a line from the frame taken
 * before to the last one, a hold later. A 16.16 clock adds inc = 65536 / 2^(6a/64) each frame (CRUSH_INC, 65 steps
 * of a, the word's low byte between two) and takes the frame when it passes 65536; at a step of one frame both sides
 * give the input itself. A note (triggered) starts the clock again, so that the block's first frame is taken; so does
 * the first block after a reset (the track coming to Crush), so that it does not hold the reset's 0.
 *
 * Bits, k 29 (RETRIG + CONTOUR): off at the top (127, its start word: the filter slot gives it to a sound that steps
 * to Crush, fltslot 0.8), fewer bits to the left, one bit at 0: 8 - 7 b / 127 bits with b = 127 - the word, in
 * 8.8 (since 0.4: 16 - 15 b / 127 before, whose upper half was hardly heard): half the frame rounded to the nearest
 * multiple of 2^(s-1) and doubled, s = 32 - bits (mid-tread: small values to 0, no offset; one bit is the
 * three levels -FS, 0, +FS, the top one held at +FS); between two whole bit counts the output blends the two
 * roundings, so that the knob moves without steps. Rate first, then Bits. k 30 and k 31 are not read.
 *
 * Both off (Rate at the centre, Bits at the top): the block is not touched, bit for bit, and the hold
 * keeps the block's last frame with its clock at 0, so that Rate turned on later holds the latest frame. A silent
 * block (all 32 frames 0) with a silent hold gives 0 whatever the values: only the clock moves on; the block is looked
 * at only when the hold is silent (since 0.3), and only when its first and last frames are 0 (since 0.5).
 *
 * Since 0.5 the same output as 0.4, bit for bit, in fewer instructions (notes/73 §20): the soft line's value
 * p + floor(d t / 2^16) is one product on the EMAC, floor(d (t << 15) / 2^31); the clock runs at 16.16 << 16, so
 * that a take is its carry and so is the line's end (t held at 65536: the taken frame itself); with the hard hold
 * Bits round the taken frame once, when it is taken, rather than every frame; Rate and Bits run in one pass over the
 * block. (0.3: the soft line's terms worked out at each take, the line split at 16 bits a frame.)
 *
 * The product on the EMAC (signed, fractional, truncating, from a clear acc0, MACSR 0xa0 as the slot calls) is
 * computed for the host in 64 bits, as tools/emu/emac.py executes it; every other product and sum stays within
 * 32 bits, so the same file compiled for the host is the proof's model, bit for bit (tools/emu/test_fltslot.py).
 *
 * Contract (fltslot.c): crush_process(block, words, track, triggered), block 32 frames of 32 bits changed in place;
 * crush_reset(track). C ABI; the EMAC is free (fl_post restores what the OS had).
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>
#include "crush_tab.h"                              /* CRUSH_INC[65], written by tools/gen_crush.py */

#define TRACKS 6
#define FRAMES 32
#define CENTRE 0x4000
#define TOP 0x7f00
#define ONE 65536u                                  /* the clock's frame */

struct track {
	uint32_t ph;                                /* the clock, 0 .. 65535; 65536 after a reset */
	int32_t cur, prev;                          /* the last taken frame and the one before */
};

static struct track state[TRACKS];

void crush_reset(uint32_t track)
{
	if (track < TRACKS) {
		state[track].ph = ONE;              /* the next block's first frame taken */
		state[track].cur = state[track].prev = 0;
	}
}

static int32_t clamp(int32_t w)
{
	return w < 0 ? 0 : w > TOP ? TOP : w;
}

/* x on a grid of 2^s (s 16 .. 31): half of x rounded to the nearest multiple of 2^(s-1), doubled, the top level held. */
static int32_t grid(int32_t x, uint32_t s)
{
	uint32_t step = 1u << (s - 1);
	int32_t r = (int32_t)(((uint32_t)(x >> 1) + (step >> 1)) & ~(step - 1));
	return r > 0x3fffffff ? 0x7fffffff : r * 2;
}

/* x between two whole bit counts: the roundings on 2^s and 2^(s+1) blended by f / 256. */
static inline int32_t blend(int32_t x, uint32_t s, int32_t f)
{
	int32_t lo = grid(x, s);
	return lo + ((grid(x, s + 1) - lo) >> 8) * f;
}

/* floor(a * b / 2^31): mac.l and movclr.l on the device, the same in 64 bits on the host. */
static inline int32_t frac(int32_t a, int32_t b)
{
#ifdef __mcoldfire__
	int32_t r;
	__asm__ volatile("mac.l %1,%2,%%acc0\n\tmovclr.l %%acc0,%0" : "=d"(r) : "r"(a), "r"(b));
	return r;
#else
	return (int32_t)(((int64_t)a * b) >> 31);
#endif
}

/* A frame's output: as it is, on a whole bit count, or between two; BITS picks the loop for the block's count. */
#define PLAIN(v) (v)
#define GRID(v) grid((v), s)
#define BLEND(v) blend((v), s, f)
#define BITS(LOOP) if (f) LOOP(BLEND) else LOOP(GRID)

/* The hard hold: the taken frame, with Bits, held until the next take. */
#define HARD(OUT) {                                                                                                  \
	int32_t held = OUT(cur);                                                                                     \
	for (n = 0; n < FRAMES; n++) {                                                                               \
		ph += inc;                                                                                           \
		if (ph >= ONE) {                                                                                     \
			ph -= ONE;                                                                                   \
			prev = cur;                                                                                  \
			cur = block[n];                                                                              \
			held = OUT(cur);                                                                             \
		}                                                                                                    \
		block[n] = held;                                                                                     \
	} }

/* The soft hold: p + floor(d t / 2^16) with t = min(ph + inc, ONE), p and d at half scale; the clock as P = ph << 16
 * and I = inc << 16, so that P + I carries where ph + inc passes ONE (a take) and where t is held at ONE (the line's
 * end, the taken frame itself), and t << 15 is (P + I) >> 1. */
#define SOFT(OUT) {                                                                                                  \
	int32_t p = prev >> 1, ch = cur >> 1, d = ch - p;                                                            \
	uint32_t P = ph << 16, I = inc << 16;                                                                        \
	for (n = 0; n < FRAMES; n++) {                                                                               \
		uint32_t t;                                                                                          \
		P += I;                                                                                              \
		if (P < I) {                                                                                         \
			prev = cur;                                                                                  \
			cur = block[n];                                                                              \
			p = prev >> 1;                                                                               \
			ch = cur >> 1;                                                                               \
			d = ch - p;                                                                                  \
		}                                                                                                    \
		t = P + I;                                                                                           \
		block[n] = OUT(2 * (t < I ? ch : p + frac(d, (int32_t)(t >> 1))));                                    \
	}                                                                                                            \
	ph = P >> 16; }

void crush_process(int32_t *block, const int16_t *words, uint32_t track, uint32_t triggered)
{
	struct track *st;
	int32_t r = clamp(words[0]) - CENTRE, b = TOP - clamp(words[1]), last, cur, prev, f = 0;   /* b: bits taken */
	uint32_t inc = ONE, ph, s = 0;
	int n;
	if (track >= TRACKS)
		return;
	st = &state[track];
	last = block[FRAMES - 1];
	if (!r && !b) {                             /* off: untouched */
		st->ph = 0;
		st->cur = st->prev = last;
		return;
	}
	if (r) {
		uint32_t a = (uint32_t)(r < 0 ? -r : r), k = a >> 8;
		inc = k >= 64 ? CRUSH_INC[64] : CRUSH_INC[k] - (((CRUSH_INC[k] - CRUSH_INC[k + 1]) * (a & 0xff)) >> 8);
		if (triggered || st->ph >= ONE)     /* a note, or a reset: the first frame taken, and the next as */
			st->ph = ONE - 1;           /* early as the rate lets */
	}
	if (!st->cur && !st->prev && !(block[0] | last)) {     /* a silent hold: is the block silent too? */
		int32_t any = 0;
		for (n = 1; n < FRAMES - 1; n++)
			any |= block[n];
		if (!any) {
			st->ph = r ? (st->ph + FRAMES * inc) & (ONE - 1) : 0;
			return;
		}
	}
	if (b) {
		uint32_t e = 6144 + (uint32_t)b * 7 / 127;              /* 24.0 .. 31.0 in 8.8 (0.4) */
		s = e >> 8;
		f = (int32_t)(e & 0xff);
	}
	ph = st->ph;
	cur = st->cur;
	prev = st->prev;
	if (r > 0) {                                /* the hard hold */
		if (!b)
			HARD(PLAIN)
		else
			BITS(HARD)
	} else if (r < 0) {                         /* the soft hold */
		if (!b)
			SOFT(PLAIN)
		else
			BITS(SOFT)
	} else {                                    /* Rate off: the hold follows the input, Bits alone */
		ph = 0;
		cur = prev = last;
		if (f)
			for (n = 0; n < FRAMES; n++)
				block[n] = BLEND(block[n]);
		else
			for (n = 0; n < FRAMES; n++)
				block[n] = GRID(block[n]);
	}
	st->ph = ph;
	st->cur = cur;
	st->prev = prev;
}
