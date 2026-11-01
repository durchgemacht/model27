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
 * at only when the hold is silent (since 0.3). The soft line's terms change only when a frame is taken, so they are
 * worked out then rather than every frame (since 0.3: the same output, bit for bit, in about half the instructions).
 *
 * Every product and sum stays within 32 bits (the soft line on half the frames, its product split at 16 bits), so the
 * same file compiled for the host is the proof's model, bit for bit (tools/emu/test_fltslot.py). No EMAC.
 *
 * Contract (fltslot.c): crush_process(block, words, track, triggered), block 32 frames of 32 bits changed in place;
 * crush_reset(track). C ABI.
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

void crush_process(int32_t *block, const int16_t *words, uint32_t track, uint32_t triggered)
{
	struct track *st;
	int32_t r = clamp(words[0]) - CENTRE, b = TOP - clamp(words[1]), last, cur, prev;   /* b: bits taken */
	uint32_t inc = ONE, ph;
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
	if (!st->cur && !st->prev) {                /* a silent hold: is the block silent too? */
		int32_t any = 0;
		for (n = 0; n < FRAMES; n++)
			any |= block[n];
		if (!any) {
			st->ph = r ? (st->ph + FRAMES * inc) & (ONE - 1) : 0;
			return;
		}
	}
	ph = st->ph;
	cur = st->cur;
	prev = st->prev;
	if (r > 0) {                                /* the hard hold */
		for (n = 0; n < FRAMES; n++) {
			ph += inc;
			if (ph >= ONE) {
				ph -= ONE;
				prev = cur;
				cur = block[n];
			}
			block[n] = cur;
		}
	} else if (r < 0) {                         /* the soft hold: a line from prev to cur, its terms at each take */
		int32_t p = prev >> 1, d = (cur >> 1) - p, dh = d >> 16;
		uint32_t dl = (uint32_t)d & 0xffff;
		for (n = 0; n < FRAMES; n++) {
			uint32_t t;
			ph += inc;
			if (ph >= ONE) {
				ph -= ONE;
				prev = cur;
				cur = block[n];
				p = prev >> 1;
				d = (cur >> 1) - p;
				dh = d >> 16;
				dl = (uint32_t)d & 0xffff;
			}
			t = ph + inc > ONE ? ONE : ph + inc;
			block[n] = 2 * (p + dh * (int32_t)t + (int32_t)((dl * t) >> 16));
		}
	} else {                                    /* Rate off: the hold follows the input */
		ph = 0;
		cur = prev = last;
	}
	st->ph = ph;
	st->cur = cur;
	st->prev = prev;
	if (b) {
		uint32_t e = 6144 + (uint32_t)b * 7 / 127, s = e >> 8;        /* 24.0 .. 31.0 in 8.8 (0.4) */
		int32_t f = (int32_t)(e & 0xff);
		if (f)
			for (n = 0; n < FRAMES; n++) {
				int32_t lo = grid(block[n], s);
				block[n] = lo + ((grid(block[n], s + 1) - lo) >> 8) * f;
			}
		else
			for (n = 0; n < FRAMES; n++)
				block[n] = grid(block[n], s);
	}
}
