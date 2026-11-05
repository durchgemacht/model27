/* The entries of model27's filter slot, with fltslot.c (the track filters, notes/72): a part the composer
 * adds to a build when one of its packages is a filter. Built once by tools/gen_parts.py into fltslot.o and placed by
 * tools/relocate.py like a package; the composer writes the data block right after it and resolves fl_data, the
 * block's address, as a patch point. Addresses are VAs of OS 1.13.
 *
 *   fl_post    jsr from 0x40059852 in place of jsr 0x40056f58, Volume + Dist, in the audio function 0x4005979e after
 *              the voice loop: 4(sp) the tracks' blocks (0x80001858, six of 32 frames of 32 bits, mono), 8(sp) and a2
 *              the smoothed parameters (track t's k at a2 + 14 + 66 t + 2 k: p-locks, LFO and velocity in them), a3
 *              the block's message, whose +16 is the tracks triggered in the block (bit t, as the voice loop gets it at
 *              0x4005980e). Runs Volume + Dist with the stack it expects, then fl_run(a2, triggered), which filters
 *              each track whose sound chose a filter of the build. When a filter ran, MACSR goes back to what the OS
 *              had and acc0-acc3 to zero: the next stage (0x40056ea8) accumulates in acc0 without clearing it first.
 *              When none ran, the EMAC is as Volume + Dist left it. d2-d7/a2-a6 are kept (C ABI); d0, d1, a0 and a1
 *              are free after the call replaced.
 *   fl_boot    jsr from 0x4004486c in place of jsr 0x4005a274, where the OS builds its parameter tables once at boot
 *              (rows by machine, CC, NRPN, LFO destinations, a new sound's defaults) from the descriptors: fl_rows()
 *              writes the build's descriptors first, then the builder runs with the caller's return address. Since 0.2.
 *   fl_keys    jsr from 0x4001f886 in place of pea 2 ; jsr (a4), where ParameterPageView's encoder handler (0x4001f4f0)
 *              asks whether TRACK is held (a4 = isKeyHeld 0x4007faf4) on every knob turn that reaches it, before any
 *              edit: d3 is the descriptor under the knob, -38(fp) the step (16 bits, signed), fp the handler's frame.
 *              On descriptor 5, the type (RETRIG + PITCH, fl_knob) or a knob without a value (since 0.10; fl_step
 *              does not step then), fl_step(step), then the handler's end at 0x4001f96a with d4 = 0: no edit (as the
 *              effect slots' fx_keys ends there). The handler's edits (a turn or FUNC at 0x4001f950, a held trig's
 *              p-lock at 0x4001f962, Control All at 0x4001f912) all come after this site. Anything else: the effect
 *              slots' fx_keys when the build has them (keys_next, entered as from the site), else isKeyHeld(2) as the
 *              handler asked, with the stack it expects. Since 0.2.
 *   (fl_conv and fl_ptab, the pattern's p-lock rows of k 23 and above, since 0.2: the shortcut layer's sc_conv and
 *              sc_ptab since 0.11, the layer's 0.5, which every filter build carries; notes/63 §25.)
 *   fl_lfo     jsr from 0x4001ead8 in place of move.l (a0,d2.l*4),d2 ; tst.l a0, in ParameterPageView's LFO + a knob
 *              (0x4001eaa2, which sets the LFO's destination from the knob turned with LFO held): a0 the knob list the
 *              OS has just built (0x4000bf42, the machine record's descriptors, 12 of them), d2 the knob (0 PITCH, 1
 *              DECAY, 2..5 COLOR..CONTOUR). It does not ask the knob lookup, so RETRIG never reached it: d2 =
 *              fl_lfo_desc(knob, the list's descriptor), the filter's value with RETRIG held, then tst.l a0 as the
 *              instructions replaced, for the beq that follows (the list freed when there is one). a0 kept; d0, d1, a1
 *              are free there. Since 0.4. When fl_lfo_desc set lfo_keep (a knob the selected track's filter has no
 *              value on, or none; since 0.10): the list freed as the routine frees it, then the routine's end at
 *              0x4001eccc (movem from its stack, lea 60(sp), rts) with no destination set, as for a knob past 11.
 *   fl_save2, fl_save1, fl_load
 *              jmp from the sound record functions' first 8 bytes (lea -12(sp),sp ; movem.l a2-a4,(sp)): save version 2
 *              (0x4005afa0), version 1 (0x4005b054), load (0x4005aecc), in front of the shortcut layer's wrappers
 *              (rec_next in the data block, which the composer takes from the layer: they run the next of their chain,
 *              SAMPLE's wrapper or the stock body, then copy k 28..32). Each pushes a copy of the function's arguments
 *              and its second half as the return address, then enters the layer's wrapper as if it were the function;
 *              back in the second half, when the function did its work (d0's byte 1), fl_saved(record, sound) or
 *              fl_loaded(sound, record), d0 kept. Since 0.3.
 *
 * License: MIT (LICENSE next to this file). */

	.section .text.fl_post, "ax"
	.p2align 2
	.globl	fl_post
fl_post:
	move.l	8(%sp), -(%sp)			/* the smoothed parameters */
	move.l	8(%sp), -(%sp)			/* the tracks' blocks */
	jsr	0x40056f58			/* Volume + Dist, the call replaced */
	addq.l	#8, %sp
	move.l	%macsr, %d0
	move.l	%d0, -(%sp)			/* the OS's MACSR */
	move.l	16(%a3), -(%sp)			/* the tracks triggered in this block */
	move.l	%a2, -(%sp)			/* the smoothed parameters */
	jsr	fl_run
	addq.l	#8, %sp
	move.l	(%sp)+, %d1
	tst.l	%d0
	beq.s	1f				/* no filter ran */
	move.l	%d1, %macsr
	move.l	#0, %acc0
	move.l	#0, %acc1
	move.l	#0, %acc2
	move.l	#0, %acc3
1:	rts

	.section .text.fl_boot, "ax"
	.p2align 2
	.globl	fl_boot
fl_boot:
	jsr	fl_rows
	jmp	0x4005a274			/* the builder, returning to 0x40044872 */

	.section .text.fl_keys, "ax"
	.p2align 2
	.globl	fl_keys
fl_keys:
	moveq	#5, %d0				/* the type's descriptor */
	cmp.l	%d3, %d0
	bne.s	2f
	mvs.w	-38(%fp), %d0			/* the step */
	move.l	%d0, -(%sp)
	jsr	fl_step
	addq.l	#4, %sp
	moveq	#0, %d4				/* the handler's return value, as after Control All */
	jmp	0x4001f96a			/* its end: restores its registers from fp and returns */
2:	move.l	fl_data+12, %d0			/* keys_next: the effect slots' fx_keys */
	beq.s	3f
	movea.l	%d0, %a0
	jmp	(%a0)
3:	move.l	(%sp), %a1			/* the return address */
	move.l	#2, (%sp)			/* TRACK's code, where the replaced pea put it */
	move.l	%a1, -(%sp)
	jmp	0x4007faf4			/* isKeyHeld(2), returning to the handler */

	.section .text.fl_lfo, "ax"
	.p2align 2
	.globl	fl_lfo
fl_lfo:
	move.l	%a0, -(%sp)			/* the knob list */
	move.l	(%a0,%d2.l*4), -(%sp)		/* its descriptor for the knob */
	move.l	%d2, -(%sp)			/* the knob */
	jsr	fl_lfo_desc
	addq.l	#8, %sp
	move.l	%d0, %d2
	movea.l	(%sp)+, %a0
	tst.b	fl_data+1042			/* lfo_keep: a knob without a value (since 0.10) */
	bne.s	1f
	tst.l	%a0				/* the instruction replaced */
	rts
1:	addq.l	#4, %sp				/* the return address: the routine's end instead, no destination set */
	tst.l	%a0
	beq.s	2f
	move.l	%a0, -(%sp)
	jsr	0x400802ec			/* the list freed, as the routine frees it at 0x4001eae2 */
	addq.l	#4, %sp
2:	jmp	0x4001eccc			/* its end: restores its registers from the stack and returns */

	.section .text.fl_record, "ax"
	.p2align 2
	.globl	fl_save2, fl_save1, fl_load
fl_save2:
	movea.l	fl_data+1028, %a0		/* rec_next: the layer's sc_save2 */
	bra.s	1f
fl_save1:
	movea.l	fl_data+1032, %a0		/* the layer's sc_save1 */
1:	move.l	8(%sp), -(%sp)			/* (record, sound) */
	move.l	8(%sp), -(%sp)
	pea	fl_post_save
	jmp	(%a0)
fl_load:
	movea.l	fl_data+1036, %a0		/* the layer's sc_load */
	move.l	8(%sp), -(%sp)			/* (sound, record) */
	move.l	8(%sp), -(%sp)
	pea	fl_post_load
	jmp	(%a0)

/* (record, sound) or (sound, record) on the stack, d0 the function's result: 1 in its byte when it did its work. */
fl_post_save:
	tst.b	%d0
	beq.s	1f
	move.l	%d0, -(%sp)
	move.l	8(%sp), -(%sp)
	move.l	8(%sp), -(%sp)
	jsr	fl_saved
	addq.l	#8, %sp
	move.l	(%sp)+, %d0
1:	addq.l	#8, %sp
	rts
fl_post_load:
	tst.b	%d0
	beq.s	1f
	move.l	%d0, -(%sp)
	move.l	8(%sp), -(%sp)
	move.l	8(%sp), -(%sp)
	jsr	fl_loaded
	addq.l	#8, %sp
	move.l	(%sp)+, %d0
1:	addq.l	#8, %sp
	rts
