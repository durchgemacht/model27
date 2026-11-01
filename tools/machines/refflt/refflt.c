/* REFF: model27's reference filter (the track filters, notes/72 §10). It proves the filter slot: the audio
 * block's call of Volume + Dist reaches the builder's part (tools/machines/fltslot/), which calls REFF on the tracks
 * whose sound chose id 255, with the track's block, its smoothed k 28 to k 31 and whether a note started on it. Never
 * offered to users.
 *
 * A one-pole lowpass per track, then an attenuation; k 28 sets the pole, k 29 the attenuation, k 30 and k 31 are not
 * read. Each frame x of the track's block:
 *
 *     y += ((x >> 1) - (y >> 1)) >> (s - 1),   s = 1 + (k28 >> 12) (1 to 8; a negative word counts as 0)
 *     out = y - (y >> 7) g,                     g = k29 >> 8 (0 to 127; a negative word counts as 0)
 *
 * and a note that starts on the track (triggered) sets y to the block's first frame before the block. The arithmetic
 * is exact within 32 bits and modelled bit for bit by tools/emu/test_fltslot.py: (x >> 1) - (y >> 1) and y plus it
 * stay within 32 bits, and |(y >> 7) g| < 2^31.
 *
 * Contract (fltslot.c): reff_process(block, words, track, triggered), block 32 frames of 32 bits filtered in place;
 * reff_reset(track) forgets the track's state. The C ABI keeps d2-d7/a2-a6; no EMAC.
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>

#define TRACKS 6
#define FRAMES 32

static int32_t lp[TRACKS];                          /* y, per track */

void reff_reset(uint32_t track)
{
	if (track < TRACKS)
		lp[track] = 0;
}

void reff_process(int32_t *block, const int16_t *words, uint32_t track, uint32_t triggered)
{
	int32_t c = words[0] < 0 ? 0 : words[0], r = words[1] < 0 ? 0 : words[1];
	int32_t s = 1 + (c >> 12), g = r >> 8, y;
	if (track >= TRACKS)
		return;
	y = triggered ? block[0] : lp[track];
	for (int n = 0; n < FRAMES; n++) {
		y += ((block[n] >> 1) - (y >> 1)) >> (s - 1);
		block[n] = y - (y >> 7) * g;
	}
	lp[track] = y;
}
