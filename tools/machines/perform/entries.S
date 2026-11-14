/* The entries of Perform Kit, with perform.c (the plan of 2026-11-14, _scratch/perform-kit/plan.md): a part the
 * composer adds to a build when its card is ticked. Built once by tools/gen_parts.py into perform.o and placed by
 * tools/relocate.py like a package; the composer writes the data block right after it and resolves pk_data, the
 * block's address, and pk_held, the byte that says SETTINGS' last event was down, as patch points. Addresses are VAs
 * of OS 1.13. MainScreenView's draw slot (vtable entry 0x400ffe30) goes to perform.c's pk_main directly, a C function
 * in the OS's ABI.
 *
 *   pk_seq_d0, pk_seq_d2, pk_seq_fp  jsr from the four writes of the playing kit, each 6 bytes, in the sequencer:
 *            0x40054d6a  move.l d0,0x40a78888   the queued pattern's turn, in the interrupt 0x40054c1e
 *            0x40055510  move.l (a6),0x40a78888 at the stop
 *            0x4005571e  move.l (a6),0x40a78888 the chain's next entry
 *            0x40055c62  move.l d2,0x40a78888   set at once, 0x40055c38 (stopped)
 *            Each tells pk_change_c the kit about to play, then does the write replaced, so N, Z, V and C are the
 *            write's, as in the stock code; X, which the write leaves alone, is saved around the C call. Every
 *            register is kept (an interrupt's code).
 *   pk_ui    jmp from 0x4000f36a in place of lea -12(sp),sp ; movem.l d2-d4,(sp) (8 bytes, the jmp and a nop), the
 *            start of the interface's kit selection: pk_ui_c, the two instructions, back at 0x4000f372. d0/d1/a0/a1
 *            are free at a function's start.
 *   pk_pattern jsr from 0x40020ad0 in place of lea 0x400cf9a8,a3 (6 bytes), the first instruction of
 *            PatternGridView's PATTERN case (the handler 0x40020a7a: a2 the view, d2 the event, a link frame). When
 *            pk_pattern_c takes the event, the handler ends as handled: d3 = 1 and its epilogue 0x400212c6, which
 *            restores from the frame, so the return address left on the stack does no harm. Otherwise a3 as the
 *            instruction replaced sets it, and back.
 *   pk_ser   jmp from 0x4005b2ae in place of lea -28(sp),sp ; movem.l d2-d3/a2-a6,(sp) (8 bytes, the jmp and a nop), the
 *            start of the kit serializer (buffer, kit, 0): pk_ser_c gives the kit to serialize, written over the
 *            argument, then the two instructions, back at 0x4005b2b6.
 *   pk_ksave jsr from 0x400100ba in place of jsr 0x4005b2ae, in the kit's save to a slot (0x4001002c: d4 the pattern,
 *            d2 the slot, 96 the temp slot; the serializer's arguments on the stack): pk_ksave_c, then into the
 *            serializer past pk_ser, with the stack as the call replaced left it.
 *   pk_kload jsr from 0x400107a4 in place of jsr 0x4005d080, the loader (kit, buffer, pattern), in the kit's load from
 *            a slot (0x400106de: d2 the pattern, d3 the slot): the loader with the same arguments, pk_loaded_c, and
 *            the loader's d0 back.
 *   pk_drop  jmp from 0x4000eb12 in place of link.w a6,#-8 ; move.l a3,-(sp) (6 bytes), the function the three
 *            project functions call (0x4000f90e, 0x4000fbc8, 0x40010262): pk_drop_c, the two instructions, back at
 *            0x4000eb18.
 *   pk_off_paste, pk_off_cut, pk_off_clear  jmp from 0x40010c7a and 0x4001190c (link.w a6,#-60 ; movem.l
 *            d2-d6/a2-a5,(sp)) and 0x40011a7e (link.w a6,#-76 ; move.b 19(a6),d1), 8 bytes each (the jmp and a nop),
 *            the starts of the functions that paste or clear a pattern with its kit: pk_off_c, the two
 *            instructions, back at 0x40010c82, 0x40011914, 0x40011a86.
 *   pk_code  jmp from 0x4007240c in place of movea.l 4(sp),a0 ; move.l 12(a0),d0, the key event's code accessor, as
 *            RESAMPLE's rs_code: on SETTINGS' events the flags' bit 0 goes to the data block's held (+5). Written only
 *            in a build without RESAMPLE; with it the composer points pk_held at RESAMPLE's byte.
 *
 * License: MIT (LICENSE next to this file). */

/* Around pk_change_c: d0/d1/a0/a1 and the condition codes are kept, X among them, which the write replaced leaves as
 * it was and the C code changes. */
	.macro	SAVE
	lea	-20(%sp), %sp
	movem.l	%d0-%d1/%a0-%a1, (%sp)
	move.w	%ccr, %d1
	move.l	%d1, 16(%sp)
	.endm

	.macro	TELL
	jsr	pk_change_c
	addq.l	#4, %sp
	move.l	16(%sp), %d1
	move.w	%d1, %ccr
	movem.l	(%sp), %d0-%d1/%a0-%a1
	lea	20(%sp), %sp
	.endm

	.section .text.pk_seq, "ax"
	.p2align 2
	.globl	pk_seq_d0, pk_seq_d2, pk_seq_fp
pk_seq_d0:
	SAVE
	move.l	%d0, -(%sp)
	TELL
	move.l	%d0, 0x40a78888
	rts
pk_seq_d2:
	SAVE
	move.l	%d2, -(%sp)
	TELL
	move.l	%d2, 0x40a78888
	rts
pk_seq_fp:
	SAVE
	move.l	(%a6), -(%sp)
	TELL
	move.l	(%a6), 0x40a78888
	rts

	.section .text.pk_ui, "ax"
	.p2align 2
	.globl	pk_ui
pk_ui:
	jsr	pk_ui_c
	lea	-12(%sp), %sp			/* the two instructions replaced */
	movem.l	%d2-%d4, (%sp)
	jmp	0x4000f372

	.section .text.pk_pattern, "ax"
	.p2align 2
	.globl	pk_pattern
pk_pattern:
	move.l	%d2, -(%sp)			/* the event */
	jsr	pk_pattern_c
	addq.l	#4, %sp
	tst.l	%d0
	bne.s	1f
	lea	0x400cf9a8, %a3			/* the instruction replaced */
	rts
1:	addq.l	#4, %sp				/* taken: the handler ends as handled */
	moveq	#1, %d3
	jmp	0x400212c6

	.section .text.pk_code, "ax"
	.p2align 2
	.globl	pk_code
pk_code:
	movea.l	4(%sp), %a0
	moveq	#13, %d0			/* SETTINGS */
	cmp.l	12(%a0), %d0
	bne.s	1f
	moveq	#1, %d0
	and.l	16(%a0), %d0			/* the flags' bit 0: down */
	move.b	%d0, pk_data+5
1:	move.l	12(%a0), %d0			/* the code, as the stock accessor returns it */
	rts

	.section .text.pk_ser, "ax"
	.p2align 2
	.globl	pk_ser, pk_ksave
pk_ser:
	move.l	8(%sp), -(%sp)			/* the kit */
	jsr	pk_ser_c
	addq.l	#4, %sp
	move.l	%d0, 8(%sp)
	lea	-28(%sp), %sp			/* the two instructions replaced */
	movem.l	%d2-%d3/%a2-%a6, (%sp)
	jmp	0x4005b2b6
pk_ksave:
	move.l	%d2, -(%sp)			/* the slot */
	move.l	%d4, -(%sp)			/* the pattern */
	jsr	pk_ksave_c
	addq.l	#8, %sp
	lea	-28(%sp), %sp			/* the serializer, past pk_ser */
	movem.l	%d2-%d3/%a2-%a6, (%sp)
	jmp	0x4005b2b6

	.section .text.pk_kload, "ax"
	.p2align 2
	.globl	pk_kload
pk_kload:
	move.l	12(%sp), -(%sp)			/* the loader's three arguments again */
	move.l	12(%sp), -(%sp)
	move.l	12(%sp), -(%sp)
	jsr	0x4005d080
	lea	12(%sp), %sp
	move.l	%d0, -(%sp)			/* its answer, kept */
	move.l	%d0, -(%sp)
	move.l	%d3, -(%sp)			/* the slot */
	move.l	%d2, -(%sp)			/* the pattern */
	jsr	pk_loaded_c
	lea	12(%sp), %sp
	move.l	(%sp)+, %d0
	rts

	.section .text.pk_drop, "ax"
	.p2align 2
	.globl	pk_drop
pk_drop:
	jsr	pk_drop_c
	link.w	%fp, #-8			/* the two instructions replaced */
	move.l	%a3, -(%sp)
	jmp	0x4000eb18

	.section .text.pk_off, "ax"
	.p2align 2
	.globl	pk_off_paste, pk_off_cut, pk_off_clear
pk_off_paste:
	jsr	pk_off_c
	link.w	%fp, #-60
	movem.l	%d2-%d6/%a2-%a5, (%sp)
	jmp	0x40010c82
pk_off_cut:
	jsr	pk_off_c
	link.w	%fp, #-60
	movem.l	%d2-%d6/%a2-%a5, (%sp)
	jmp	0x40011914
pk_off_clear:
	jsr	pk_off_c
	link.w	%fp, #-76
	move.b	19(%fp), %d1
	jmp	0x40011a86
