/* CHORD Tables' chain hooks (notes/66 §30.2, §31): the entries the composer puts in front of whatever the build has at
 * the same sites (the effect slots', the filter slot's), each calling the entry behind it, whose address the composer
 * resolves into the symbol ct_next_<site>, or doing the stock work when that symbol is 0. Addresses are VAs of OS 1.13.
 *
 *   ct_keys    jsr from 0x4001f886 in place of pea 2 ; jsr (a4), where ParameterPageView's encoder handler (0x4001f4f0)
 *              asks whether TRACK is held, on every knob turn that reaches it, before any edit: d3 is the descriptor the
 *              knob lookup gave, -38(fp) the step (16 bits, signed). On descriptor 10 (ct_knob gives it for PATTERN +
 *              SWEEP on a CHORD track), ct_step(step), then the handler's end at 0x4001f96a with d4 = 0: no edit, as
 *              the effect slots' fx_keys and the filter slot's fl_keys end. Anything else: the entry behind (fl_keys or
 *              fx_keys, entered as from the site), else isKeyHeld(2) as the handler asked, with the stack it expects.
 *   ct_release jsr from 0x40020dca in place of move.l 132(a2),d0 ; moveq #7,d1, in PatternAndBankSelectView's key
 *              handler where PATTERN is released without opening the selection's window: the effect slots' fx_release
 *              when the build has it (the same work), else clears the view's +124 (waiting for a pattern) and runs the
 *              two instructions (notes/68 §23): PATTERN + SWEEP leaves no selection waiting.
 *   ct_load    jsr from 0x4005b4b0 in place of move.b 38(a3),38(a2), in the pattern header's loader (0x4005b3b4): a2 the
 *              working header, a3 the saved one, d0 = 1. The entry behind (fx_load: byte 38 and the effect slots'
 *              bytes) or the instruction replaced, then ct_hdr_load(a2, a3); d0-d1/a0-a1 kept.
 *   ct_init    jsr from 0x4006155e in place of clr.b d0 ; move.b d0,38(a0), in a new header's initializer (0x40061526):
 *              a0 the header. The entry behind (fx_init) or the instructions replaced, then ct_hdr_init(a0); goes on at
 *              0x40061564 with a0 and d0's low byte 0, as the instructions replaced leave them.
 *   (ct_knob, the knob lookup's vtable entry, is C: chordtables.c.)
 *
 * Every jump to an entry behind goes through the stack (the address pushed, then rts), so that no register changes.
 *
 * License: MIT (LICENSE next to this file). */

	.section .text.ct_keys, "ax"
	.p2align 2
	.globl	ct_keys
ct_keys:
	cmpi.l	#10, %d3			/* descriptor 10: PATTERN + SWEEP on CHORD (ct_knob) */
	bne.s	1f
	mvs.w	-38(%fp), %d0			/* the step */
	move.l	%d0, -(%sp)
	jsr	ct_step
	addq.l	#4, %sp
	moveq	#0, %d4				/* the handler's return value, as after Control All */
	jmp	0x4001f96a			/* its end: restores its registers from fp and returns */
1:	move.l	#ct_next_keys, -(%sp)
	tst.l	(%sp)
	beq.s	2f
	rts					/* into the entry behind, as from the site */
2:	addq.l	#4, %sp
	move.l	(%sp), %a1			/* the stock question: the return address */
	move.l	#2, (%sp)			/* TRACK's code, where the replaced pea put it */
	move.l	%a1, -(%sp)
	jmp	0x4007faf4			/* isKeyHeld(2), returning to the handler */

	.section .text.ct_release, "ax"
	.p2align 2
	.globl	ct_release
ct_release:
	move.l	#ct_next_release, -(%sp)
	tst.l	(%sp)
	beq.s	1f
	rts					/* fx_release, the same work */
1:	addq.l	#4, %sp
	clr.b	124(%a2)			/* the selection no longer waits */
	move.l	132(%a2), %d0			/* the instructions replaced */
	moveq	#7, %d1
	rts

	.section .text.ct_load, "ax"
	.p2align 2
	.globl	ct_load
ct_load:
	lea	-16(%sp), %sp
	movem.l	%d0-%d1/%a0-%a1, (%sp)
	move.l	#ct_next_load, %d0
	beq.s	1f
	move.l	%d0, %a1
	movem.l	(%sp), %d0-%d1/%a0		/* the loader's registers, for the entry behind */
	jsr	(%a1)				/* fx_load: byte 38 and the effect slots' bytes, registers kept */
	bra.s	2f
1:	move.b	38(%a3), 38(%a2)		/* the instruction replaced */
2:	move.l	%a3, -(%sp)			/* the saved header */
	move.l	%a2, -(%sp)			/* the working header */
	jsr	ct_hdr_load
	addq.l	#8, %sp
	movem.l	(%sp), %d0-%d1/%a0-%a1
	lea	16(%sp), %sp
	rts

	.section .text.ct_init, "ax"
	.p2align 2
	.globl	ct_init
ct_init:
	lea	-16(%sp), %sp
	movem.l	%d0-%d1/%a0-%a1, (%sp)
	move.l	#ct_next_init, %d1
	beq.s	1f
	move.l	%d1, %a1
	movem.l	(%sp), %d0-%d1/%a0		/* a0 the header, as the entry behind wants it */
	jsr	(%a1)				/* fx_init: byte 38 cleared and the effect slots' bytes */
	bra.s	2f
1:	clr.b	%d0				/* the instructions replaced */
	move.b	%d0, 38(%a0)
2:	movem.l	(%sp), %d0-%d1/%a0-%a1		/* a0 the header again */
	move.l	%a0, -(%sp)
	jsr	ct_hdr_init
	addq.l	#4, %sp
	movem.l	(%sp), %d0-%d1/%a0-%a1
	lea	16(%sp), %sp
	clr.b	%d0				/* d0's low byte 0, as the instructions replaced leave it */
	rts
