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
 * Shape, k 30 (RETRIG + COLOR): the carrier's wave, sine at 0 (its start word: the filter slot gives it to a sound that
 * steps to Ring, fltslot 0.8), then the sine driven into a clip towards a square: c = clip(c * D) with
 * D = 1 + 15 (v / 127)^2, 16 at 127 (in 8.8, 256 .. 4096). Towards the square the ring is up to 3 dB louder and, at
 * high frequencies, aliases. k 31 is not read.
 *
 * The carrier: a cosine table of 256 steps (RING_COS, Q15, one more for the step after the last), the phase's top 8
 * bits the step and the next 8 between two, so that phase 0 is the carrier's peak. A note (triggered) starts the phase
 * again at 0, so that every hit sounds the same and its attack comes through at any frequency; so does a reset (the
 * track coming to Ring).
 *
 * Off (Mix 0): the block is not touched, bit for bit; the phase moves on by the block, so that a Mix that opens in the
 * middle of a note finds the carrier where it would have been. The frames of a block before its first non-zero one
 * are 0 in and 0 out: only the phase moves on across them (a silent block costs its scan).
 *
 * Every product and sum stays within 32 bits (the gain g = 1 - m + m * c in Q15 is -32767 .. 32768, its product with
 * a frame split at 16 bits), so the same file compiled for the host is the proof's model, bit for bit
 * (tools/emu/test_fltslot.py). No EMAC.
 *
 * Contract (fltslot.c): ring_process(block, words, track, triggered), block 32 frames of 32 bits changed in place;
 * ring_reset(track). C ABI.
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>
#include "ring_tab.h"                               /* RING_INC[129], RING_COS[257], written by tools/gen_ring.py */

#define TRACKS 6
#define FRAMES 32
#define TOP 0x7f00
#define SINE 256                                    /* Shape's drive at 0, 1.0 in 8.8 */

static uint32_t phase[TRACKS];                      /* the carrier's phase, 2^32 a period, 0 its peak */

void ring_reset(uint32_t track)
{
	if (track < TRACKS)
		phase[track] = 0;
}

static int32_t clamp(int32_t w)
{
	return w < 0 ? 0 : w > TOP ? TOP : w;
}

void ring_process(int32_t *block, const int16_t *words, uint32_t track, uint32_t triggered)
{
	uint32_t f = (uint32_t)clamp(words[0]), w = (uint32_t)clamp(words[1]), s = (uint32_t)clamp(words[2]), n0 = f >> 8;
	uint32_t inc, ph, drive;
	int32_t m, k;
	int n;
	if (track >= TRACKS)
		return;
	inc = RING_INC[n0] + ((RING_INC[n0 + 1] - RING_INC[n0]) >> 8) * (f & 0xff);
	ph = triggered ? 0 : phase[track];
	if (!w) {                                   /* off: untouched, the carrier runs on */
		phase[track] = ph + FRAMES * inc;
		return;
	}
	for (n = 0; !block[n]; )                    /* the silent frames at the block's start */
		if (++n == FRAMES) {
			phase[track] = ph + FRAMES * inc;
			return;
		}
	ph += (uint32_t)n * inc;
	m = (int32_t)(w * 128 / 127);               /* Mix in Q15, 0 .. 32768 */
	k = 32768 - m;
	drive = SINE + s * s / TOP * 3840 / TOP;    /* Shape's drive in 8.8, 256 .. 4096 */
	if (drive == SINE)                          /* the sine */
		for (; n < FRAMES; n++) {
			uint32_t i = ph >> 24, fr = (ph >> 16) & 0xff;
			int32_t a = RING_COS[i], c = a + (((RING_COS[i + 1] - a) * (int32_t)fr) >> 8), g, x = block[n];
			g = k + ((m * c) >> 15);
			block[n] = 2 * ((x >> 16) * g) + (((x & 0xffff) * g) >> 15);
			ph += inc;
		}
	else                                        /* the sine driven into the clip */
		for (; n < FRAMES; n++) {
			uint32_t i = ph >> 24, fr = (ph >> 16) & 0xff;
			int32_t a = RING_COS[i], c = a + (((RING_COS[i + 1] - a) * (int32_t)fr) >> 8), g, x = block[n];
			c = (c * (int32_t)drive) >> 8;
			c = c > 32767 ? 32767 : c < -32767 ? -32767 : c;
			g = k + ((m * c) >> 15);
			block[n] = 2 * ((x >> 16) * g) + (((x & 0xffff) * g) >> 15);
			ph += inc;
		}
	phase[track] = ph;
}
