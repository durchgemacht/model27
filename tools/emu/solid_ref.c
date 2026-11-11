/* SOLID's core on the host, for tools/emu/test_solid.py (notes/71 §7): tools/machines/solid/solid.c compiled with
 * SOLID_HOST, the EMAC as tools/emu/emac.py executes it. One call plays a voice from silence (the state solid_update
 * clears when a track takes the machine, its random generator seeded as there) through n blocks of the 11 words of
 * struct knobs, as solid_update leaves them, and writes what solid_render takes from solid_block: 32 frames a block,
 * Q27, before the bus's saturation, the amp chain and the velocity gain the OS applies after the voice loop. A block
 * with nothing ringing and nothing struck is not rendered, as on the device.
 *
 *     cc -O2 -std=c99 -fwrapv -DSOLID_MODES=8 -I tools/machines/solid -shared -fPIC tools/emu/solid_ref.c
 */
#define SOLID_HOST 1
#include "solid.c"

static struct voice rv;

void solid_ref_render(const int32_t *blk, int nblocks, int32_t *out, uint32_t seed)
{
	int b, n;

	for (unsigned i = 0; i < sizeof rv; i++)
		((uint8_t *)&rv)[i] = 0;
	rv.rng = seed;
	dbg_flags = 0;
	dbg_slope = SUS_SLOPE;
	solid_work = 0;
	for (b = 0; b < nblocks; b++) {
		const int32_t *p = blk + 11 * b;
		struct knobs k = { p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10] };

		if (!rv.active && !k.strike) {          /* solid_render: nothing rings and nothing is struck */
			for (n = 0; n < BLOCK; n++)
				out[BLOCK * b + n] = 0;
			continue;
		}
		solid_block(&rv, &k, out + BLOCK * b);
	}
}

long long solid_ref_work(void) { return solid_work; }
int solid_ref_modes(void) { return SOLID_MODES; }
