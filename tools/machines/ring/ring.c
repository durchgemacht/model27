/* Ring: a ring modulator on every track whose sound chose it (Track FX, notes/74), id 3 of the builder's filter slot
 * (tools/machines/fltslot/), which calls it after Volume + Dist with the track's block and its smoothed k 28 to k 31:
 * p-locks, the LFO and the velocity move the values as they move any parameter.
 *
 * Freq, k 28 (RETRIG + SWEEP): the carrier's frequency, the value a MIDI note, f = 440 * 2^((v - 69) / 12): 0 is
 * 8.2 Hz, 60 middle C (262 Hz), 64 (the centre, where a sound starts) E4 (330 Hz), 127 12.5 kHz. A 32-bit phase adds
 * inc = f / 48 kHz * 2^32 each frame (RING_INC, one step a semitone, the word's low byte between two).
 *
 * Mix, k 29 (RETRIG + CONTOUR): 0 dry (the slot's neutral word, so a new sound starts there), 127 the ring alone;
 * between them the output is x * (1 - m + m * c), which at the middle is an amplitude modulation (the input stays, at
 * half, with its sidebands) and at the top the ring modulation x * c (the input gone, its sidebands only). m = Mix in
 * Q15 (0 .. 32768), c the carrier in Q15.
 *
 * Wave, k 30 (RETRIG + COLOR; called Shape until 0.3, renamed so that it is not taken for the SHAPE knob beside
 * it): the carrier's wave, sine at 0 (its start word: the filter slot gives it to a sound that
 * steps to Ring, fltslot 0.8), then the sine driven into a clip towards a square: c = clip(c * D) with
 * D = 1 + 15 (v / 127)^2, 16 at 127 (in 8.8, 256 .. 4096). Towards the square the ring is up to 3 dB louder and, at
 * high frequencies, aliases. k 31 is not read.
 *
 * The carrier: a cosine table of 2048 steps (RING_COS, Q15, each step's value at its middle), the phase's top 11 bits
 * the step, not interpolated, so that phase 0 is the carrier's peak (since 0.3: 256 steps and the next 8 bits between
 * two before; the steps' phase noise lies about 60 dB under 0.2's output, 51 dB at Wave 127, where the clip steepens
 * the edges; the effect's strength is the same, notes/74 §13). A note (triggered) starts the phase again at 0, so that
 * every hit sounds the same and its attack comes through at any frequency; so does a reset (the track coming to Ring).
 *
 * Off (Mix 0): the block is not touched, bit for bit; the phase moves on by the block, so that a Mix that opens in the
 * middle of a note finds the carrier where it would have been. A block whose frames are all 0 (its first one, then
 * the or of the others) is 0 out: only the phase moves on. Otherwise the whole block runs (since 0.3; 0.2 skipped the
 * frames of 0 at the start, which give 0 at any gain).
 *
 * A frame times the gain g = 1 - m + m * c (Q15, -32767 .. 32767 whenever Mix is on) is floor(x * g / 2^15): on the
 * device one product on the EMAC (g << 16 in Q31, signed, fractional and truncating, as tools/emu/emac.py executes
 * it; MACSR and acc0 set here as the slot calls), on the host the same split at 16 bits (0.1's arithmetic). The gain's
 * shift is a mask (floor(m c / 2^15) << 16 is 2 m c with its low 16 bits cleared). Since 0.3 the frames run in
 * ring_cf.S on the device, a loop of one frame with the block's values in registers, and frames() below is its model
 * on the host: about a third fewer instructions than 0.2. Every other product and sum stays within 32 bits, so the same
 * file compiled for the host is the proof's model, bit for bit (tools/emu/test_fltslot.py).
 *
 * Contract (fltslot.c): ring_process(block, words, track, triggered), block 32 frames of 32 bits changed in place;
 * ring_reset(track). C ABI; the EMAC is free (fl_post restores what the OS had).
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>
#include "ring_tab.h"                               /* RING_INC[129], RING_COS[2048], written by tools/gen_ring.py */

#define TRACKS 6
#define FRAMES 32
#define TOP 0x7f00
#define SINE 256                                    /* Wave's drive at 0, 1.0 in 8.8 */

static uint32_t phase[TRACKS];                      /* the carrier's phase, 2^32 a period, 0 its peak */

/* the block's values, in the order ring_cf.S loads them (movem.l to d4-d7/a0/a2-a3) */
struct run {
	int32_t m2;                                 /* twice Mix in Q15, 2 .. 65536 (even, so the gain's low half is 0) */
	int32_t drive;                              /* Wave's drive in 8.8, 256 .. 4096 */
	uint32_t inc, ph;                           /* the phase's step, the phase at the block's first frame */
	int32_t *block;
	const int16_t *cos;                         /* RING_COS */
	int32_t k16;                                /* (32768 - Mix) << 16 */
};

void ring_reset(uint32_t track)
{
	if (track < TRACKS)
		phase[track] = 0;
}

static int32_t clamp(int32_t w)
{
	return w < 0 ? 0 : w > TOP ? TOP : w;
}

#ifdef __mcoldfire__
void ring_sine(const struct run *r);                /* ring_cf.S: the block, the sine */
void ring_shape(const struct run *r);               /* the same with Wave's clip */
#else
/* floor(x * g / 2^15) for g16 = g << 16, g -32767 .. 32767: the split at 16 bits, each term and the sum within 32 bits */
static int32_t product(int32_t x, int32_t g16)
{
	int32_t g = g16 >> 16;
	return 2 * ((x >> 16) * g) + (((x & 0xffff) * g) >> 15);
}

/* ring_cf.S's loop, frame by frame */
static void frames(const struct run *r, int shape)
{
	uint32_t ph = r->ph;
	int n;
	for (n = 0; n < FRAMES; n++) {
		int32_t c = r->cos[ph >> 21];
		if (shape) {
			c = (c * r->drive) >> 8;
			c = c > 32767 ? 32767 : c < -32767 ? -32767 : c;
		}
		r->block[n] = product(r->block[n], r->k16 + (int32_t)((uint32_t)(r->m2 * c) & 0xffff0000u));
		ph += r->inc;
	}
}
#endif

void ring_process(int32_t *block, const int16_t *words, uint32_t track, uint32_t triggered)
{
	static struct run r;                        /* not on the stack, so that GCC keeps no frame pointer */
	uint32_t f = (uint32_t)clamp(words[0]), w = (uint32_t)clamp(words[1]), s = (uint32_t)clamp(words[2]), n0 = f >> 8;
	uint32_t inc, ph;
	int n;
	if (track >= TRACKS)
		return;
	inc = RING_INC[n0] + ((RING_INC[n0 + 1] - RING_INC[n0]) >> 8) * (f & 0xff);
	ph = triggered ? 0 : phase[track];
	phase[track] = ph + FRAMES * inc;           /* the carrier runs on by the block, played or not */
	if (!w)                                     /* off: untouched */
		return;
	if (!block[0]) {                            /* a silent block: its first frame, then the or of the others */
		int32_t any = 0;
		for (n = 1; n < FRAMES; n++)
			any |= block[n];
		if (!any)
			return;
	}
	r.m2 = 2 * (int32_t)(w * 128 / 127);
	r.k16 = (int32_t)((uint32_t)(65536 - r.m2) << 15);
	r.drive = s ? (int32_t)(SINE + s * s / TOP * 3840 / TOP) : SINE;    /* at 0 no divisions */
	r.inc = inc;
	r.ph = ph;
	r.block = block;
	r.cos = RING_COS;
#ifdef __mcoldfire__
	__asm__ volatile("move.l #0xa0,%%macsr\n\tmove.l #0,%%acc0" : : : "memory");   /* as the slot calls */
	if (r.drive == SINE)
		ring_sine(&r);
	else
		ring_shape(&r);
#else
	frames(&r, r.drive != SINE);
#endif
}
