/* The entry of model27's RESAMPLE recorder, with resample.c (notes/79, step R1): a part the composer
 * adds to a build when its card is ticked. Built once by tools/gen_parts.py into resample.o and placed
 * by tools/relocate.py like a package; the composer writes the data block right after it and resolves rs_data, the
 * block's address, as a patch point. Addresses are VAs of OS 1.13.
 *
 *   rs_mix  jsr from 0x40059872 in place of jsr 0x400567ba, the audio function's call of the mixer, its two
 *           arguments on the stack (the output buffer 0x4a3ed080 + (a3[40] << 8), then a2, the smoothed parameters);
 *           a3 is the audio function's frame (its +16 the tracks triggered in the block, notes/72 §2). Idle or taken
 *           (the data block's state not 1 or 2), it jumps to the mixer, which returns to the caller: 7 instructions.
 *           Armed or recording: rs_pre(0x80001858, triggered) with the six tracks' buffers before the mixer, the
 *           mixer with its arguments copied, rs_post(0x8000b990, 0x8000ba90, triggered) with the main bus and the USB
 *           input after it, and d0 back as the mixer left it. d2-d7/a2-a6 are kept (C ABI); d1, a0 and a1 are free
 *           after the call (0x40059878: lea 20(sp),sp ; movea.l (sp)+,a2 ; movea.l (sp)+,a3 ; rts). The EMAC is
 *           not touched (resample.c compiles to none). Reached only from the audio interrupt, which does not nest.
 *
 * License: MIT (LICENSE next to this file). */

	.section .text.rs_mix, "ax"
	.p2align 2
	.globl	rs_mix
rs_mix:
	moveq	#0, %d0
	move.b	rs_data+16, %d0			/* the state: 1 armed, 2 recording */
	subq.l	#1, %d0
	moveq	#1, %d1
	cmp.l	%d1, %d0
	bls.s	1f
	jmp	0x400567ba			/* the mixer, as the call replaced */
1:	move.l	16(%a3), -(%sp)			/* the tracks triggered in the block, kept */
	move.l	(%sp), -(%sp)
	pea	0x80001858			/* the six tracks' buffers */
	jsr	rs_pre
	addq.l	#8, %sp
	move.l	12(%sp), -(%sp)			/* the mixer's arguments: a2's value, then the output */
	move.l	12(%sp), -(%sp)
	jsr	0x400567ba
	addq.l	#8, %sp
	move.l	%d0, -(%sp)			/* what the mixer returned */
	move.l	4(%sp), -(%sp)			/* the tracks triggered */
	pea	0x8000ba90			/* the USB input */
	pea	0x8000b990			/* the main bus */
	jsr	rs_post
	lea	12(%sp), %sp
	move.l	(%sp)+, %d0
	addq.l	#4, %sp
	rts
