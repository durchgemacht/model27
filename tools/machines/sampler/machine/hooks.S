/* SAMPLE's ways into the Model:Cycles OS 1.13 that need assembly. The tick (smp_hook_tick) is C, in
   pool.c. machine/build.py writes the jumps to these places. */

	.section .text.smp_hooks,"ax"	/* a section of its own, like -ffunction-sections (Level B builders keep file order) */
	.p2align 2		/* the alignment plain .text had */

/* The browser opens a file (0x400a6602: jsr 0x400a3052 becomes jsr smp_hook_open). On entry
   a0 = &result, 4(sp) = &handle {inode, id, size, -}, and a2 points at the browser, whose word +664
   is the track it loads into. smp_browser_open(result, handle, track) fills the result when the file
   is a sample and the track plays SAMPLE; otherwise the OS reads the file as a preset, as before.
   Either way d0 = a0 = &result on return, like the original. */
	.globl	smp_hook_open
smp_hook_open:
	move.l	%a0, -(%sp)
	movea.l	(%a2), %a1
	move.l	664(%a1), -(%sp)	/* track */
	move.l	12(%sp), -(%sp)		/* &handle */
	move.l	8(%sp), -(%sp)		/* &result */
	jsr	smp_browser_open
	lea	12(%sp), %sp
	movea.l	(%sp)+, %a0
	tst.l	%d0
	beq.s	1f
	move.l	%a0, %d0
	rts
1:	jmp	0x400a3052

/* The browser's cursor rests on a file (0x400a6426 in the preview 0x400a63ac: jsr 0x400a3052 becomes jsr
   smp_hook_preview). The same call as at the open, a0 = &result, 4(sp) = &handle, but a2 is the browser itself, its
   word +664 the track. smp_browser_open fills the result when the file is a sample and the track plays SAMPLE: the
   OS then copies that sound into its preview buffer and marks it (0x400a647c), so the pad and the TRIG keys play the
   sample, as they play a preset under the cursor; otherwise the OS reads the file as a preset, as before. Either way
   d0 = a0 = &result on return, like the original. */
	.globl	smp_hook_preview
smp_hook_preview:
	move.l	%a0, -(%sp)
	move.l	664(%a2), -(%sp)	/* track */
	move.l	12(%sp), -(%sp)		/* &handle */
	move.l	8(%sp), -(%sp)		/* &result */
	jsr	smp_browser_open
	lea	12(%sp), %sp
	movea.l	(%sp)+, %a0
	tst.l	%d0
	beq.s	1f
	move.l	%a0, %d0
	rts
1:	jmp	0x400a3052

/* The pads' notes (since 0.16): 0x4001d05e(view, track, note, velocity, speed) plays a pad's note and
   0x4001d0fc(view, track, note) ends it, each called only by the pads' handler (0x4001d180, at 0x4001d38e and
   0x4001d3ba). Their first two instructions (lea -16(sp),sp ; moveq #5,d1 and lea -12(sp),sp ; moveq #5,d0) become a
   jsr here, which notes the track's pad in smp_pad_held (sampler.c), does those two instructions and goes on. The TRIG
   keys play their notes elsewhere (0x40019edc, 0x40019cb4), so they never count as a held pad. d0, d1, a0 and a1 are
   free at both entries.

   A held pad would mute its track: the audio side drops a note of a lower rank than the one holding the track
   (0x40058e4e), the sequencer's are rank 1 (0x40054b7e) and the notes played live rank 2 (0x4005894a), and a live note
   holds its track until its note-off (same rank and note, 0x40058f4c). So when smp_pad_frees(track) says the PRESET
   browser marks a sample for the pad's track, the pad's note gets its note-off at once, as the Model:Samples' browser
   does (0x400a4088 right after 0x400a3fac): 0x4008145e(track, note, 0x40), what 0x4001d0fc sends, without its end of
   a live recording (0x400827a8, still at the release). The track takes its trigs again and the note plays on (with
   GATE on it no longer holds); the note-off at the release is then dropped by the audio side (its rank or note no
   longer matches). For that the hook runs the rest of 0x4001d05e as a subroutine, on a copy of its five arguments
   (its tail call into the recording, 0x4008273c, writes over them). */
	.globl	smp_hook_pad_on
smp_hook_pad_on:
	move.l	12(%sp), %d1		/* the track: (sp) our return, 4 the caller's, 8 the view */
	moveq	#5, %d0
	cmp.l	%d0, %d1
	bhi.s	9f			/* not a track: the function returns at once */
	lea	smp_pad_held, %a1
	moveq	#1, %d0
	move.b	%d0, (%a1,%d1.l)
	movea.l	(%sp)+, %a1		/* 0x4001d064; now (sp) the caller's return, 4 view, 8 track, 12 note */
	move.l	20(%sp), -(%sp)		/* the five arguments again, speed first */
	move.l	20(%sp), -(%sp)
	move.l	20(%sp), -(%sp)
	move.l	20(%sp), -(%sp)
	move.l	20(%sp), -(%sp)
	lea	1f(%pc), %a0
	move.l	%a0, -(%sp)		/* the rest returns here */
	lea	-16(%sp), %sp
	moveq	#5, %d1
	jmp	(%a1)
1:	lea	20(%sp), %sp		/* the copies */
	move.l	8(%sp), -(%sp)		/* track */
	jsr	smp_pad_frees
	addq.l	#4, %sp
	tst.l	%d0
	beq.s	2f
	moveq	#0x40, %d0
	move.l	%d0, -(%sp)
	move.l	16(%sp), -(%sp)		/* note */
	move.l	16(%sp), -(%sp)		/* track */
	jsr	0x4008145e
	lea	12(%sp), %sp
2:	rts
9:	movea.l	(%sp)+, %a1		/* back into 0x4001d064 */
	lea	-16(%sp), %sp
	moveq	#5, %d1
	jmp	(%a1)

/* A TRIG key plays its note in CHROMATIC mode: 0x40019e7a(view, track, note, velocity, speed), called only by the
   keyboard's handler (0x40019f6e); its first 6 bytes (lea -16(sp),sp ; moveq #5,d0) become jsr smp_hook_key_on. The
   same as the pad's: the rest runs as a subroutine on a copy of the arguments, then, when smp_key_frees(track) says
   the PRESET browser marks a sample for the key's track, the active one, the note's note-off at once
   (0x4008145e(track, note, 0x40), what 0x40019c84 sends). The track's trigs then play on, in the track's own sample
   (the key is not a held pad), and the next one cuts the key's note. */
	.globl	smp_hook_key_on
smp_hook_key_on:
	move.l	12(%sp), %d1		/* the track */
	moveq	#5, %d0
	cmp.l	%d0, %d1
	bhi.s	9f
	movea.l	(%sp)+, %a1		/* 0x40019e80; now (sp) the caller's return, 4 view, 8 track, 12 note */
	move.l	20(%sp), -(%sp)		/* the five arguments again, speed first */
	move.l	20(%sp), -(%sp)
	move.l	20(%sp), -(%sp)
	move.l	20(%sp), -(%sp)
	move.l	20(%sp), -(%sp)
	lea	1f(%pc), %a0
	move.l	%a0, -(%sp)		/* the rest returns here */
	lea	-16(%sp), %sp
	moveq	#5, %d0
	jmp	(%a1)
1:	lea	20(%sp), %sp		/* the copies */
	move.l	8(%sp), -(%sp)		/* track */
	jsr	smp_key_frees
	addq.l	#4, %sp
	tst.l	%d0
	beq.s	2f
	moveq	#0x40, %d0
	move.l	%d0, -(%sp)
	move.l	16(%sp), -(%sp)		/* note */
	move.l	16(%sp), -(%sp)		/* track */
	jsr	0x4008145e
	lea	12(%sp), %sp
2:	rts
9:	movea.l	(%sp)+, %a1		/* back into 0x40019e80 */
	lea	-16(%sp), %sp
	moveq	#5, %d0
	jmp	(%a1)

	.globl	smp_hook_pad_off
smp_hook_pad_off:
	move.l	12(%sp), %d1		/* the track */
	moveq	#5, %d0
	cmp.l	%d0, %d1
	bhi.s	1f
	lea	smp_pad_held, %a1
	moveq	#0, %d0
	move.b	%d0, (%a1,%d1.l)
1:	movea.l	(%sp)+, %a1		/* back into 0x4001d102 */
	lea	-12(%sp), %sp
	moveq	#5, %d0
	jmp	(%a1)

/* FUNC + LEVEL/DATA on the main screen, MainScreenView's encoder handler (0x4001aa4e): before the OS
   sets a track's pan (0x4000b274), the new value comes from smp_pan_step(track, pan, step) (view.c)
   instead of pan + step. On one track (0x4001ab14: move.l d3,-(sp) ; move.l d2,-(sp) ; add.l d0,d4
   becomes jsr smp_hook_pan) d3 is the track, d2 the kit, d0 the pan, d4 the step; with TRACK held, for
   each track (0x4001ab52, after its move.l d3,-(sp): move.l d2,-(sp) ; move.l d0,d4 ; add.l d7,d4
   becomes jsr smp_hook_pan_all) the step is d7. Each leaves the stack as the bytes it replaces (d2 on
   d3) and d4 the value; d0, d1, a0 and a1 are free there (the OS calls 0x400097f0 next). */
	.globl	smp_hook_pan
smp_hook_pan:
	move.l	(%sp), %a1		/* the return */
	move.l	%d3, (%sp)		/* move.l d3,-(sp) */
	move.l	%d2, -(%sp)		/* move.l d2,-(sp) */
	move.l	%a1, -(%sp)
	move.l	%d4, -(%sp)		/* the step */
	bra.s	1f

	.globl	smp_hook_pan_all
smp_hook_pan_all:
	move.l	(%sp), %a1		/* the return, over the d3 the OS pushed */
	move.l	%d2, (%sp)		/* move.l d2,-(sp) */
	move.l	%a1, -(%sp)
	move.l	%d7, -(%sp)		/* the step */
1:	move.l	%d0, -(%sp)		/* the pan */
	move.l	%d3, -(%sp)		/* the track */
	jsr	smp_pan_step
	lea	12(%sp), %sp
	move.l	%d0, %d4
	rts

/* The sound record functions: save version 2 (0x4005afa0) and 1 (0x4005b054), arguments (record,
   sound), and load (0x4005aecc), arguments (sound, record). Their first 8 bytes (lea -12(sp),sp ;
   movem.l a2-a4,(sp)) become a jmp here. The hook runs the function's body with a copy of its two
   arguments and a return into its second half, which calls after(first, second) and returns the
   function's own result. */
	.macro	around name, body, after
	.globl	\name
\name:
	move.l	8(%sp), -(%sp)		/* copy of the second argument */
	move.l	8(%sp), -(%sp)		/* copy of the first */
	pea	9f
	lea	-12(%sp), %sp		/* the 8 bytes the jmp replaced */
	movem.l	%a2-%a4, (%sp)
	jmp	\body
9:	move.l	%d0, -(%sp)		/* the function's result */
	move.l	8(%sp), -(%sp)
	move.l	8(%sp), -(%sp)
	jsr	\after
	addq.l	#8, %sp
	move.l	(%sp)+, %d0
	addq.l	#8, %sp			/* the copies */
	rts
	.endm

	around	smp_hook_save2, 0x4005afa8, smp_after_save
	around	smp_hook_save1, 0x4005b05c, smp_after_save
	around	smp_hook_load, 0x4005aed4, smp_after_load
