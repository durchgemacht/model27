/* The entries of model27's effect slots, with fxslot.c (notes/68 §2, §9, §11, §14; F1, F2, F2b): a part the composer
 * adds to a build when one of its packages is an effect. Built once by tools/gen_parts.py into fxslot.o and placed by
 * tools/relocate.py like a package; the composer writes the data block right after it and resolves fx_data, the
 * block's address, as a patch point. Addresses are VAs of OS 1.13.
 *
 *   fx_delay   jsr from 0x4005699c in place of jsr 0x40057488, the mixer's call of the delay
 *   fx_reverb  jsr from 0x40056a2c in place of jsr 0x400579c4, the mixer's call of the reverb
 *              Both are entered with the stack the mixer built for the stock effect: the return address, out (the
 *              slot's return, 32 stereo frames of 32 bits), in (the send bus 0x8000b990) and params (P + 428 or
 *              P + 432, notes/68 §1.2, §8.1). They call fx_run(slot, out, in, params), which runs the effect the
 *              device has chosen for the slot, or the stock one, and return to the mixer. d2-d7/a2-a6 are kept (C
 *              ABI), as the stock effects keep them.
 *   fx_track   jsr from 0x4001f89a in place of jsr 0x4005a5cc, in ParameterPageView's encoder handler (0x4001f4f0),
 *              reached only while TRACK is held (notes/68 §8.4): 4(sp) is the descriptor under the knob, the caller's
 *              d4 the step (16 bits, signed), fp the handler's frame. fx_step(descriptor, step) takes TRACK + Delay
 *              Time (descriptor 37) and TRACK + Reverb Size (39) when the build has an effect in that slot; the
 *              handler then ends at 0x4001f96a with d4 = 0, its return value after Control All too: no edit, no
 *              Control All, and the popup it has already set up (0x4001f708..0x4001f76e) shows the slot's parameter
 *              under the chosen effect's name. Anything else: the stock call, jmp 0x4005a5cc with its argument.
 *   fx_load    jsr from 0x4005b4b0 in place of move.b 38(a3),38(a2), in the pattern header's loader (0x4005b3b4) after
 *              its last field: a2 the working pattern's header, a3 the saved one's, d0 = 1 its return value. Copies
 *              byte 38 as the loader did, then fx_hdr_load(a2, a3) the effects' bytes; the loader goes on at
 *              0x4005b4b6 with its registers.
 *   fx_init    jsr from 0x4006155e in place of clr.b d0; move.b d0,38(a0), in a new pattern header's initializer
 *              (0x40061526): a0 the header. Does the same, then fx_hdr_init(a0); the initializer goes on at 0x40061564
 *              with d0 = 0 and a0, as it uses them.
 *   fx_early   jsr from 0x4005981e in place of jsr 0x400a7d4a, the block's call of the voice loop (notes/68 §21): runs
 *              the effects' per-block setup 0x4005802e first, with a2 the block's state as the output stage would
 *              (its a3, the same object), then jumps to the voice loop with the stack as the caller built it. The
 *              setup starts the delay line's read on the eDMA, which the output stage then waits for (0x4005697e):
 *              started here, the transfer runs while the voices render. Model-TG's idea and analysis (TinyGregAudio,
 *              MIT; its fx_early in src/model_tg.s): the setup reads only what the effects left last block and the
 *              delay time at P + 428, set before this call, and nothing until the output stage touches what it does.
 *   fx_late    jsr from 0x400567d8 in place of jsr 0x4005802e, where the output stage ran the setup: leaves what the
 *              setup leaves, MACSR 0x20 and acc0, acc1 clear (it ends with movclr of both and that MACSR), d0 and d1
 *              free after a call.
 *
 * License: MIT (LICENSE next to this file). */

	.section .text.fx_delay, "ax"
	.p2align 2
	.globl	fx_delay
	.globl	fx_reverb
fx_delay:
	moveq	#0, %d0				/* the delay slot */
	bra.s	1f
fx_reverb:
	moveq	#1, %d0				/* the reverb slot */
1:	move.l	12(%sp), -(%sp)			/* params */
	move.l	12(%sp), -(%sp)			/* in */
	move.l	12(%sp), -(%sp)			/* out */
	move.l	%d0, -(%sp)
	jsr	fx_run
	lea	16(%sp), %sp
	rts

	.section .text.fx_track, "ax"
	.p2align 2
	.globl	fx_track
fx_track:
	move.l	%d4, -(%sp)			/* the step */
	move.l	8(%sp), -(%sp)			/* the descriptor */
	jsr	fx_step
	addq.l	#8, %sp
	tst.l	%d0
	bne.s	1f
	jmp	0x4005a5cc			/* not the slots' gesture: the stock call, with its argument */
1:	moveq	#0, %d4				/* the handler's return value, as after Control All */
	jmp	0x4001f96a			/* its end: restores its registers from fp and returns */

	.section .text.fx_load, "ax"
	.p2align 2
	.globl	fx_load
fx_load:
	move.b	38(%a3), 38(%a2)		/* the instruction replaced */
	lea	-16(%sp), %sp
	movem.l	%d0-%d1/%a0-%a1, (%sp)
	move.l	%a3, -(%sp)			/* the saved header */
	move.l	%a2, -(%sp)			/* the working header */
	jsr	fx_hdr_load
	addq.l	#8, %sp
	movem.l	(%sp), %d0-%d1/%a0-%a1
	lea	16(%sp), %sp
	rts

	.section .text.fx_init, "ax"
	.p2align 2
	.globl	fx_init
fx_init:
	clr.b	%d0				/* the instructions replaced */
	move.b	%d0, 38(%a0)
	lea	-16(%sp), %sp
	movem.l	%d0-%d1/%a0-%a1, (%sp)
	move.l	%a0, -(%sp)			/* the header */
	jsr	fx_hdr_init
	addq.l	#4, %sp
	movem.l	(%sp), %d0-%d1/%a0-%a1
	lea	16(%sp), %sp
	rts

	.section .text.fx_early, "ax"
	.p2align 2
	.globl	fx_early
	.globl	fx_late
fx_early:
	move.l	%a2, -(%sp)			/* the block's state */
	jsr	0x4005802e			/* the effects' setup: the reverb's taps, the delay's read on the eDMA */
	addq.l	#4, %sp
	jmp	0x400a7d4a			/* the voice loop, its arguments as the caller pushed them */
fx_late:
	move.l	#0x20, %macsr			/* what the setup leaves */
	movclr.l	%acc0, %d0
	movclr.l	%acc1, %d1
	rts
