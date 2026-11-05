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
