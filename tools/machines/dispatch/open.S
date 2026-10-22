/* dp_open, the browser's dispatcher (notes/63 §4, step B4d), with dispatch.c: 0x400a6602 becomes jsr dp_open in
   place of jsr 0x400a3052, which reads the file the browser opens. The registers are the call's, as SAMPLE's hook
   takes them: a0 = &result, 4(sp) = &handle, a2 = the browser's pointer (its object's +664: the track it loads into),
   and the caller's d2..d7 (d4: the entry's index). dp_open keeps them all, asks dp_open_pick for the method of that
   track's machine, or the stock 0x400a3052, and jumps there as if it had been called.

   License: MIT (LICENSE next to this file). */

	.section .text.dp_open, "ax"
	.p2align 2
	.globl	dp_open
dp_open:
	move.l	%a0, -(%sp)			/* &result */
	move.l	%a2, -(%sp)			/* the browser */
	jsr	dp_open_pick
	addq.l	#4, %sp
	movea.l	(%sp)+, %a0
	movea.l	%d0, %a1
	jmp	(%a1)
