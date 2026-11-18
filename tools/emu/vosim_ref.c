/* VOSIM's core on the host, for tools/emu/test_vosim.py (notes/86 §8): tools/machines/vosim/vosim.c compiled with
 * VOSIM_HOST (its C sample loop, which vosim_cf.S on the device matches bit for bit), the EMAC as tools/emu/emac.py
 * executes it, the output on the bus's scale (VOSIM_OSH 14, Q29) as vosim_render hands it to AMP_ENV, the trig's
 * restart off (VOSIM_RESET 0, decided). One call plays a track from a fresh voice (what vosim_update makes when the
 * track took the machine) through n blocks of 6 words (note, COLOR, SHAPE, SWEEP, CONTOUR, the trig: unused with
 * VOSIM_RESET 0). The blocks vosim_render pauses (the envelope closed, no trig) are left out by the caller: the core
 * does not run in them.
 *
 *     cc -O2 -std=c99 -I tools/machines/vosim -shared -fPIC tools/emu/vosim_ref.c
 */
#define VOSIM_HOST 1
#include "vosim.c"

void vosim_ref_render(const int32_t *in, int nblocks, int32_t *out)
{
	vosim_host_render(in, nblocks, out);
}
