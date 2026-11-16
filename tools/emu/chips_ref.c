/* CHIPS's core on the host, for tools/emu/test_chips.py (notes/83 §5): tools/machines/chips/chips.c compiled with
 * CHIPS_HOST, the EMAC as tools/emu/emac.py executes it. One call plays a track from the state chips_update gives it
 * when it takes the machine (Plaits' Init) through n blocks of the 10 words of struct chips_in (trig, note, color,
 * shape, sweep, contour, bass, updown, bpm, punch), as chips_update leaves them, and writes what chips_block gives
 * chips_render: 32 frames a block, Q27, before the bus's saturation and the amp chain. The blocks chips_render pauses
 * (the envelope closed, no trig) are left out by the caller: the core does not run in them.
 *
 *     cc -O2 -std=c99 -fwrapv -I tools/machines/chips -shared -fPIC tools/emu/chips_ref.c
 */
#define CHIPS_HOST 1
#include "chips.c"

void chips_ref_render(const int32_t *in, int nblocks, int32_t *out)
{
	chips_host_render(in, nblocks, out);
}
