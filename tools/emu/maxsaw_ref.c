/* Max Saw's core on the host, for tools/emu/test_maxsaw.py (notes/84 §10): tools/machines/maxsaw/maxsaw.c
 * compiled with MSAW_HOST, the EMAC as tools/emu/emac.py executes it. One call plays a track from the state
 * maxsaw_render gives a fresh voice (msaw_init with the track's seed) through n blocks of the 7 words maxsaw_update
 * takes from the voice (trig: the block of +0x38; note, Detune, Mix, Tone, Phase, Sub 0 or 2), as maxsaw_render
 * runs them: the trig's new phases with that block's Phase, then the core. It writes what msaw_block gives
 * maxsaw_render: 32 frames a block, Q27, before the bus and the amp chain. The blocks maxsaw_render pauses (the
 * envelope closed, no trig) are left out by the caller: the core does not run in them.
 *
 *     cc -O2 -std=c99 -fwrapv -I tools/machines/maxsaw -shared -fPIC tools/emu/maxsaw_ref.c
 */
#define MSAW_HOST 1
#include "maxsaw.c"

void maxsaw_ref_render(const int32_t *in, int nblocks, int32_t *out, uint32_t seed)
{
	static struct msaw s;
	int b;

	msaw_init(&s, seed);
	for (b = 0; b < nblocks; b++) {
		const int32_t *p = in + 7 * b;
		struct knobs k = { p[1], p[2], p[3], p[4], p[5], p[6] };

		if (p[0])
			msaw_trig(&s, k.phase);
		msaw_block(&s, &k, out + BLOCK * b);
	}
}
