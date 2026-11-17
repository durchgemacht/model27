/* TERRA's core on the host, for tools/emu/test_terra.py (notes/85 §7): tools/machines/terra/terra.c compiled with
 * TERRA_HOST, the EMAC as tools/emu/emac.py executes it, the output on the bus's scale (TERRA_OSH 2, Q29) as
 * terra_render hands it to AMP_ENV. One call plays a track from a fresh voice (what terra_update makes when the track
 * took the machine) through n blocks of the 5 words terra_update takes from the voice (note, COLOR, SHAPE, SWEEP,
 * CONTOUR). The blocks terra_render pauses (the envelope closed, no trig) are left out by the caller: the core does
 * not run in them.
 *
 *     cc -O2 -std=c99 -I tools/machines/terra -shared -fPIC tools/emu/terra_ref.c
 */
#define TERRA_HOST 1
#define TERRA_OSH 2
#include "terra.c"

void terra_ref_render(const int32_t *in, int nblocks, int32_t *out)
{
	terra_host_render(in, nblocks, out);
}
