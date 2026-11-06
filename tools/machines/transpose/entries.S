/* The entries of Transpose, with transpose.c (the plan of 2026-11-05, _scratch/machines-transpose/plan.md): a part the
 * composer adds to a build when its card is ticked, always with the shortcut layer. Built once by tools/gen_parts.py
 * into transpose.o and placed by tools/relocate.py like a package; the composer writes the data block right after it
 * and resolves tr_data, the block's address, as a patch point. Addresses are VAs of OS 1.13.
 *
 * The composer's other writes call transpose.c directly, each a C call in the OS's ABI:
 *   0x400ff9cc  KeyboardView's key handler (its vtable +8, stock 0x4001a0d2) -> tr_keys (view, event).
 *   0x400597a8  jsr 0x40058474 (the smoother, its argument on the stack, its output in d0) -> jsr tr_pitch.
 *
 *   tr_kbt   jsr from 0x4001a164 in place of jsr 0x40016da6 (the KBT getter), in KeyboardView's key handler: the
 *            track holder on the stack as the getter's argument, d3 the note's track (0x40012442, read at
 *            0x4001a152; the note goes to that track at 0x4001a23a). Returns KBT plus the track's octave in d0
 *            (tr_kbt_c); d2-d7/a2-a6 kept (C ABI); the handler uses none of d1, a0, a1 after the call.
 *   tr_frame jsr from 0x40006a76 in place of jsr 0x40076ca2 (the views set their LEDs), in the LED frame 0x40006a4a,
 *            after its reset of the states (0x4000602a, its argument, the LED object, still on the stack): 4(sp) the
 *            views' argument, 8(sp) the LED object. Sets the six keys' states first (tr_leds), then jumps to the
 *            views with the stack as the call replaced left it, so they return to the frame.
 *
 * License: MIT (LICENSE next to this file). */

	.section .text.tr_kbt, "ax"
	.p2align 2
	.globl	tr_kbt
tr_kbt:
	move.l	%d3, -(%sp)			/* the note's track */
	move.l	8(%sp), -(%sp)			/* the track holder */
	jsr	tr_kbt_c
	addq.l	#8, %sp
	rts

	.section .text.tr_frame, "ax"
	.p2align 2
	.globl	tr_frame
tr_frame:
	move.l	8(%sp), -(%sp)			/* the LED object */
	jsr	tr_leds
	addq.l	#4, %sp
	jmp	0x40076ca2			/* the views, as from the call replaced */
