/* The entries of Transpose, with transpose.c (the plan of 2026-11-05, _scratch/machines-transpose/plan.md): a part the
 * composer adds to a build when its card is ticked, always with the shortcut layer. Built once by tools/gen_parts.py
 * into transpose.o and placed by tools/relocate.py like a package; the composer writes the data block right after it
 * and resolves tr_data, the block's address, as a patch point. Addresses are VAs of OS 1.13.
 *
 * The composer's other writes call transpose.c directly, each a C call in the OS's ABI:
 *   0x400ff9cc  KeyboardView's key handler (its vtable +8, stock 0x4001a0d2) -> tr_keys (view, event).
 *   0x400597a8  jsr 0x40058474 (the smoother, its argument on the stack, its output in d0) -> jsr tr_pitch.
 *   0x4001c19c, 0x4001b884, 0x4002cad0  jsr 0x400107d8 (the pattern's reload, five arguments on the stack, d0's byte
 *               1 when reloaded) -> jsr tr_reload (since 0.3).
 *
 *   tr_kbt   jsr from 0x4001a164 in place of jsr 0x40016da6 (the KBT getter), in KeyboardView's key handler: the
 *            track holder on the stack as the getter's argument, d3 the note's track (0x40012442, read at
 *            0x4001a152; the note goes to that track at 0x4001a23a). Returns KBT plus the track's octave in d0
 *            (tr_kbt_c); d2-d7/a2-a6 kept (C ABI); the handler uses none of d1, a0, a1 after the call.
 *   tr_frame jsr from 0x40006a76 in place of jsr 0x40076ca2 (the views set their LEDs), in the LED frame 0x40006a4a,
 *            after its reset of the states (0x4000602a, its argument, the LED object, still on the stack): 4(sp) the
 *            views' argument, 8(sp) the LED object. Sets the six keys' states first (tr_leds), then jumps to the
 *            views with the stack as the call replaced left it, so they return to the frame.
 *   tr_led   jmp from 0x40059dea in place of moveq #-1,d3 ; moveq #21,d4 ; move.w d3,0x8c000000 (10 bytes, then two
 *            nops), the panel interrupt's LED step 0 (0x40059db8, level 6): d0's byte the copy's byte of the row
 *            whose turn it is (0x40140aa8[d2]), d2 that row, d1 the step (0), a0 the copy. tr_led_c(byte, row) writes
 *            DIR (0xffff) as the stock step, loads the dimmed rows out of their turn and returns the turn row's byte;
 *            back at 0x40059df4 with d0 that byte, d2 the row, d1 0 and d4 21, as the three instructions replaced
 *            leave them (d3 is set again there). The interrupt saved d0-d4/a0; tr_led keeps a1, the C call
 *            d2-d7/a2-a6. Nothing jumps into 0x40059dec..0x40059df3 (notes/45 §8).
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

	.section .text.tr_led, "ax"
	.p2align 2
	.globl	tr_led
tr_led:
	move.l	%a1, -(%sp)
	move.l	%d2, -(%sp)			/* the row */
	moveq	#0, %d1
	move.b	%d0, %d1
	move.l	%d1, -(%sp)			/* its byte */
	jsr	tr_led_c
	addq.l	#8, %sp
	move.l	(%sp)+, %a1
	moveq	#0, %d1				/* the step, as the stock code has it */
	moveq	#21, %d4
	jmp	0x40059df4			/* the stock step 0 goes on: DATA with d0's byte and d2's row */
