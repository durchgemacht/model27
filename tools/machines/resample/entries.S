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
 *   rs_key  (page.c) jsr from 0x40024482 in place of clr.l -(sp) ; move.l d3,-(sp) ; jsr 0x4006ba90 ; move.l
 *           d3,-(sp) ; jsr 0x4006ba20 ; lea 12(sp),sp, TransportView's toggle of GRID RECORDING (0x4002439a, RECORD
 *           pressed without FUNC; d3 the UIStates): move.l d3,-(sp) ; jsr rs_key ; addq.l #4,sp and six nops, then the
 *           stock bra 0x40024650. Nothing branches into the nops. rs_key makes the two stock calls itself unless
 *           SETTINGS is held (then the page opens); d2-d7/a2-a6 kept (C ABI), d0/d1/a0/a1 are free there, as after
 *           the stock calls.
 *   rs_code jmp from 0x4007240c in place of movea.l 4(sp),a0 ; move.l 12(a0),d0, the key event's code accessor that
 *           every key handler calls (then its rts, unreached), as Model-TG's key_hook takes it (TinyGregAudio, MIT):
 *           the same code in d0, and on SETTINGS's events the flags' bit 0 (down: a press, its repeats, its long
 *           hold; up: the release) kept in the data block's set_held (+79). The events are read in the order they
 *           were pressed, so SETTINGS is held there when RECORD's press is read after it, even when isKeyHeld(13)
 *           says it is not (the maintainer's device, 2026-11-03: GRID RECORDING toggled instead of the page,
 *           notes/79 §10.1). Only a0 and d0 are touched, as by the stock accessor, and its condition codes are the
 *           same (move.l 12(a0),d0 last).
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

	.section .text.rs_code, "ax"
	.p2align 2
	.globl	rs_code
rs_code:
	movea.l	4(%sp), %a0
	moveq	#13, %d0			/* SETTINGS */
	cmp.l	12(%a0), %d0
	bne.s	1f
	moveq	#1, %d0
	and.l	16(%a0), %d0			/* the flags' bit 0: down */
	move.b	%d0, rs_data+79
1:	move.l	12(%a0), %d0			/* the code, as the stock accessor returns it */
	rts

/* The page's destructors (its vtable +0x00 and +0x04), as the CPU page's: the page forgotten (the data block's page,
 * +64), then the stock ones (0x400f43ca, 0x400f4486) with the stack as they were called; rs_dtor0_th, rs_dtor1_th: the
 * same from the +4 base (this - 4), in place of 0x400f447c and 0x400f44c0. rs_enc_th: the encoder handler from the +4
 * base, as 0x400a2926. */
	.section .text.rs_page, "ax"
	.p2align 2
	.globl	rs_dtor0, rs_dtor1, rs_dtor0_th, rs_dtor1_th, rs_enc_th
rs_dtor0:
	clr.l	rs_data+64			/* the page is gone */
	jmp	0x400f43ca
rs_dtor1:
	clr.l	rs_data+64
	jmp	0x400f4486
rs_dtor0_th:
	subq.l	#4, 4(%sp)			/* from the +4 base */
	bra.s	rs_dtor0
rs_dtor1_th:
	subq.l	#4, 4(%sp)
	bra.s	rs_dtor1
rs_enc_th:
	subq.l	#4, 4(%sp)
	jmp	rs_page_enc
