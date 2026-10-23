/* REFC: model27's reference extension of a stock machine for the Model:Cycles OS 1.13 (notes/66 §3, step W2).

   The smallest package that extends a stock machine instead of adding one, as REF is the smallest added machine: it
   proves the builder's extensions before CHORD Tables uses them, and is never offered to users. It extends CHORD,
   machine 5, and changes nothing that sounds or shows:

   - a shortcut, RETRIG + SWEEP = Wavetable, 0 to 64, declared in the manifest: the builder's shortcut layer shows it
     on CHORD's tracks and saves it in k 30 (record slot 30), as CHORD Tables will read it; REFC only counts;
   - rc_setup takes the place of jsr 0x400a8080 at 0x400ab15e, the one call through which CHORD's update gets its two
     frames (notes/66 §1.1): it counts, then calls the stock function with the same arguments (v, p);
   - rc_hook_tick takes the place of jsr 0x40076be4 at 0x400075f0, in the screen's redraw (about 30 times a second;
     with SAMPLE, through the builder's tick dispatcher): it counts, then returns the getter it replaces, as REF2's
     tick does.

   The two counters are roots of the object, so that a proof finds them in the composed tweak's symbols. Plain C99,
   no libc.

   License: MIT (LICENSE next to this file). */
#include <stdint.h>

typedef uint32_t u32;

#define CHORD_SETUP ((void (*)(void *, const char *))0x400a8080)   /* (v, p): CHORD's two frames into the voice */
#define TICK_STOCK  ((u32 (*)(void *))0x40076be4)                   /* (view): does the screen draw */

u32 rc_setups;                              /* the calls of CHORD's setup through rc_setup */
u32 rc_ticks;                               /* the screen's ticks through rc_hook_tick */

void rc_setup(void *v, const char *p)
{
	rc_setups++;
	CHORD_SETUP(v, p);
}

u32 rc_hook_tick(void *view)
{
	rc_ticks++;
	return TICK_STOCK(view);
}
