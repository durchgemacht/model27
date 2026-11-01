/* EQ: a three-band equalizer on every track whose sound chose it (Track FX, notes/76), id 5 of the builder's filter
 * slot (tools/machines/fltslot/), which calls it after Volume + Dist with the track's block and its smoothed k 28 to
 * k 31: p-locks, the LFO and the velocity move the bands as they move any parameter.
 *
 * Low, k 28 (RETRIG + SWEEP, CC 74): a low shelf at 100 Hz. High, k 29 (RETRIG + CONTOUR, CC 71): a high shelf at
 * 8 kHz. Mid, k 30 (RETRIG + COLOR): a bell's gain. Mid Freq, k 31 (RETRIG + SHAPE): the bell's centre, 1000 Hz *
 * 5^((k - 64) / 64): 200 Hz at 0, 1 kHz at 64, about 4.9 kHz at 127. Every gain is 12 dB * (k - 64) / 64: -12 dB at
 * 0, flat at 64 (the word 0x4000), +11.8 dB at 127. High starts at 64 too (its start word, fltslot 0.8: CONTOUR's
 * neutral word is 0), so a sound that steps to EQ is flat on every band. The bands are the Audio EQ Cookbook's: the
 * shelves with the slope S = 1, the bell with Q 1, constant Q (a cut is the mirror of the same boost). They run Low,
 * then Mid, then High.
 *
 * Each band is a biquad in direct form I on the EMAC (eq_cf.S): y = b0 x + b1 x1 + b2 x2 - a1 y1 - a2 y2, its
 * coefficients over 2 (Low and Mid: all of them under 2) or over 4 (High: b0 reaches 2.5 at +12 dB), the sum read and
 * doubled once or twice, saturated: a boost of a hot track clips at full scale, it does not wrap. The coefficients
 * come from tables (eq_tab.h, written by tools/gen_eq.py): Low and High by gain at every knob step, the word's low
 * byte between two; Mid by gain every 8 knob steps and centre every 4, bilinear (at most 0.05 dB from the Cookbook's
 * bell). Each band's last coefficient comes from the others, so that the band is flat where it should be whatever the
 * tables' rounding: Low at the top of the spectrum, High at DC, Mid at both. They are worked out only when a value
 * has moved.
 *
 * Flat (every gain at 64): the block is not touched, bit for bit, and the states follow the input, so that a gain
 * turned away from 64 starts from where the signal is; a band at 64 while another is not is skipped in the same way.
 * With all three on, one loop runs them frame by frame (eq_frames3: about 30 instructions a frame instead of 35);
 * otherwise each band that is on runs over the block (eq_frames). A silent block (all 32 frames 0) whose states have
 * rung out (under 2^14, -102 dB, as Samples') is left silent and the states are cleared. reset(track) clears the
 * states; the next block starts them at its first frame. The trig bit is not read: an equalizer has no notes.
 *
 * Everything here is the device's but the frame loops, eq_frames and eq_frames3: eq_cf.S on the ColdFire, and below
 * (#ifndef __mcoldfire__) their model for the host with the EMAC's arithmetic in fractional, saturating mode (each
 * product floored to 2^-39, the sum read floored to Q31 and saturated), so that the host build is the proof's model,
 * bit for bit (tools/emu/test_fltslot.py).
 *
 * Contract (fltslot.c): eq_process(block, words, track, triggered), block 32 frames of 32 bits changed in place,
 * called with MACSR 0xa0 and the accumulators clear; eq_reset(track). C ABI.
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>
#include "eq_tab.h"                                 /* EQ_LOW, EQ_HIGH, EQ_MID, written by tools/gen_eq.py */

#define TRACKS 6
#define FRAMES 32
#define CENTRE 0x4000                               /* flat */
#define TOP 0x7f00
#define RING (1 << 14)                              /* 2^-17 of full scale: under it a band has rung out */
#define LOW 0
#define MID 1
#define HIGH 2
#define B2 0                                        /* a band's coefficients in the loops' order */
#define B0 1
#define B1 2
#define A1 3
#define A2 4

struct track {
	int32_t s[3][4];                            /* each band's x1 x2 y1 y2: its input's and its output's last two
	                                               frames, the newest first; a band's x is the band ahead's y */
	int32_t c[3][5];                            /* each band's coefficients over 2^shift, Q31: b2 b0 b1 a1 a2 */
	int16_t w[4];                               /* the words the coefficients were worked out for, -1 after a
	                                               reset */
	uint8_t set;                                /* 0 after a reset: the next block that is not flat starts the
	                                               states at its first frame */
};

static struct track state[TRACKS];

static const uint8_t SHIFT[3] = {1, 1, 2};          /* the coefficients over 2^shift, by band */

void eq_frames(const int32_t *c, int32_t *s, int32_t *block, uint32_t shift);
void eq_frames3(const int32_t (*c)[5], int32_t (*s)[4], int32_t *block);

/* A band whose output is its input, the newest frame f1 and the one before f2 (flat, or after a reset or silence). */
static void follow(int32_t *s, int32_t f1, int32_t f2)
{
	s[0] = s[2] = f1;
	s[1] = s[3] = f2;
}

void eq_reset(uint32_t track)
{
	if (track < TRACKS) {
		for (int k = 0; k < 3; k++)
			follow(state[track].s[k], 0, 0);
		for (int k = 0; k < 4; k++)
			state[track].w[k] = -1;
		state[track].set = 0;
	}
}

static int32_t clamp(int32_t w)
{
	return w < 0 ? 0 : w > TOP ? TOP : w;
}

/* a + (b - a) * t / 256 for t = 0..255, within 32 bits: 8 bits of the difference dropped (Samples' lerp). */
static int32_t lerp(int32_t a, int32_t b, int32_t t)
{
	return a + ((b - a) >> 8) * t;
}

/* A shelf at the word w from its table (b0 b1 a1 a2): the gain's two rows, the word's low byte between them. b2 from
 * the others: flat at the top of the spectrum (Low, dc 0: b0 - b1 + b2 = 1 - a1 + a2) or at DC (High, dc 1), summed
 * from the small differences b1 - a1 and a2 - b0 so that nothing on the way leaves 32 bits. */
static void shelf(int32_t *c, const int32_t (*tab)[4], int32_t w, int32_t one, int dc)
{
	const int32_t *p = tab[w >> 8], *q = tab[(w >> 8) + 1];
	int32_t t = w & 0xff;
	c[B0] = lerp(p[0], q[0], t);
	c[B1] = lerp(p[1], q[1], t);
	c[A1] = lerp(p[2], q[2], t);
	c[A2] = lerp(p[3], q[3], t);
	c[B2] = one + (dc ? c[A1] - c[B1] : c[B1] - c[A1]) + (c[A2] - c[B0]);
}

/* One coefficient of the bell, bilinear: p its value at the gain row and centre column below the words, the next
 * column 3 on, the next row MID_ROW on. */
#define MID_ROW (3 * (sizeof EQ_MID[0] / sizeof EQ_MID[0][0]))
static int32_t bilerp(const int32_t *p, int32_t ft, int32_t gt)
{
	return lerp(lerp(p[0], p[3], ft), lerp(p[MID_ROW], p[MID_ROW + 3], ft), gt);
}

/* The bell at the gain word g and the centre word f: bilinear in EQ_MID (b0 a1 a2; a row every 8 knob steps, a
 * column every 4). b1 = a1 and b2 = 1 + a2 - b0: flat at DC and at the top. Not inlined: in eq_process GCC runs out
 * of registers over it. */
static void __attribute__((noinline)) bell(int32_t *c, int32_t g, int32_t f)
{
	const int32_t *p = EQ_MID[g >> 11][f >> 10];
	int32_t gt = (g >> 3) & 0xff, ft = (f >> 2) & 0xff;
	c[B0] = bilerp(p, ft, gt);
	c[B1] = c[A1] = bilerp(p + 1, ft, gt);
	c[A2] = bilerp(p + 2, ft, gt);
	c[B2] = (1 << 30) + (c[A2] - c[B0]);
}

/* v under RING either way. */
static int quiet(int32_t v)
{
	return (uint32_t)v + RING < 2 * RING;
}

/* Every state under RING: Low's input, each band's output, which is the next band's input. Asked only once the
 * newest input and output are under it. */
static int rung_out(const int32_t (*s)[4])
{
	if (!quiet(s[0][1]))
		return 0;
	for (int k = 0; k < 3; k++)
		if (!quiet(s[k][2]) || !quiet(s[k][3]))
			return 0;
	return 1;
}

void eq_process(int32_t *block, const int16_t *words, uint32_t track, uint32_t triggered)
{
	struct track *t;
	int32_t lo, hi, mg, mf;
	uint32_t on;
	int k;
	(void)triggered;
	if (track >= TRACKS)
		return;
	t = &state[track];
	if (words[0] == CENTRE && words[1] == CENTRE && words[2] == CENTRE) {   /* flat: untouched, the states */
		int32_t f1 = block[FRAMES - 1], f2 = block[FRAMES - 2];         /* follow the input */
		for (k = 0; k < 3; k++)
			follow(t->s[k], f1, f2);
		t->set = 1;
		return;
	}
	on = (words[0] != CENTRE) | (words[2] != CENTRE) << MID | (words[1] != CENTRE) << HIGH;
	if (!t->set) {                              /* after a reset: the states start at the first frame */
		for (k = 0; k < 3; k++)
			follow(t->s[k], block[0], block[0]);
		t->set = 1;
	}
	if (quiet(t->s[0][0]) && quiet(t->s[HIGH][2]) && rung_out(t->s)) {   /* quiet states: is the block silent? */
		int32_t any = 0;
		for (k = 0; k < FRAMES; k += 4)
			any |= block[k] | block[k + 1] | block[k + 2] | block[k + 3];
		if (!any) {
			for (k = 0; k < 3; k++)
				follow(t->s[k], 0, 0);
			return;
		}
	}
	lo = clamp(words[0]);
	hi = clamp(words[1]);
	mg = clamp(words[2]);
	mf = clamp(words[3]);
	/* the coefficients of the bands that are on, when their words moved (a flat band's wait) */
	if (on & 1 << LOW && lo != t->w[0]) {
		t->w[0] = (int16_t)lo;
		shelf(t->c[LOW], EQ_LOW, lo, 1 << 30, 0);
	}
	if (on & 1 << MID && (mg != t->w[2] || mf != t->w[3])) {
		t->w[2] = (int16_t)mg;
		t->w[3] = (int16_t)mf;
		bell(t->c[MID], mg, mf);
	}
	if (on & 1 << HIGH && hi != t->w[1]) {
		t->w[1] = (int16_t)hi;
		shelf(t->c[HIGH], EQ_HIGH, hi, 1 << 29, 1);
	}
	if (on == 7) {                              /* every band: one loop */
		eq_frames3(t->c, t->s, block);
		return;
	}
	for (k = 0; k < 3; k++, on >>= 1) {
		if (on & 1)
			eq_frames(t->c[k], t->s[k], block, SHIFT[k]);
		else                                /* flat: its output is its input */
			follow(t->s[k], block[FRAMES - 1], block[FRAMES - 2]);
	}
}

#ifndef __mcoldfire__
/* The host model of eq_cf.S: the EMAC in fractional, saturating mode (MACSR 0xa0), its accumulator here in units of
 * 2^-39: each product of two Q31 values floored to 2^-39, the sum exact, read floored to Q31 and saturated; then the
 * doublings of the loop's add.l, saturated as its overflow branches do. */
typedef int64_t acc_t;

static acc_t prod(int32_t a, int32_t b)
{
	return ((acc_t)a * b) >> 23;
}

static int32_t sat(acc_t v)
{
	return v > INT32_MAX ? INT32_MAX : v < INT32_MIN ? INT32_MIN : (int32_t)v;
}

void eq_frames(const int32_t *c, int32_t *s, int32_t *block, uint32_t shift)
{
	int32_t x1 = s[0], x2 = s[1], y1 = s[2], y2 = s[3];
	for (int n = 0; n < FRAMES; n++) {
		int32_t x = block[n], y;
		acc_t acc = prod(c[B2], x2) + prod(c[B0], x) + prod(c[B1], x1) - prod(c[A1], y1) - prod(c[A2], y2);
		y = sat(acc >> 8);
		for (uint32_t k = 0; k < shift; k++)
			y = sat((acc_t)y * 2);
		block[n] = y;
		x2 = x1;
		x1 = x;
		y2 = y1;
		y1 = y;
	}
	s[0] = x1;
	s[1] = x2;
	s[2] = y1;
	s[3] = y2;
}

/* The three bands frame by frame on the device; band by band here, the same arithmetic in each band's accumulator. */
void eq_frames3(const int32_t (*c)[5], int32_t (*s)[4], int32_t *block)
{
	for (int k = 0; k < 3; k++)
		eq_frames(c[k], s[k], block, SHIFT[k]);
}
#endif
