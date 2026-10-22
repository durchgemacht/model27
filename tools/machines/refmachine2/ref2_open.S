/* REF2's browser hook (notes/63 §2, step B4d), with ref2_view.c: 0x400a6602 becomes jsr ref2_hook_open in place of
   jsr 0x400a3052, which reads the file the browser opens (alone; with SAMPLE, the builder's dp_open jumps here for
   REF2 tracks). On a REF2 track it keeps the entry's name for the main screen's label, then the stock code reads the
   file as before: REF2 takes no file.

   The registers are the call's, as SAMPLE's hook takes them: a0 = &result, 4(sp) = &handle, a2 = the browser's
   pointer (its object's +664: the track it loads into, its +640: its list of entries), and the caller's d2..d7; d4
   holds the entry's index here (0x400a6518, read again at 0x400a6622). The name comes the way the browser gets it
   right after the open: the list's method +16, (list, index), writes a std::string at a0; 0x400f7d5c destroys it.

   License: MIT (LICENSE next to this file). */

	.equ	OPEN, 0x400a3052		/* the stock open: reads the file into the result */
	.equ	STRING_DROP, 0x400f7d5c		/* (std::string *) the destructor */

	.section .text.ref2_hook_open, "ax"
	.p2align 2
	.globl	ref2_hook_open
ref2_hook_open:
	move.l	%a0, -(%sp)			/* &result, for the stock open */
	movea.l	(%a2), %a1
	move.l	664(%a1), -(%sp)		/* the track the browser loads into */
	jsr	ref2_open_track			/* non-zero if it plays REF2 */
	addq.l	#4, %sp
	tst.l	%d0
	beq.s	9f
	subq.l	#4, %sp				/* the entry's name, a std::string */
	movea.l	(%a2), %a1
	movea.l	640(%a1), %a1			/* the browser's list */
	move.l	%d4, -(%sp)			/* the entry's index */
	move.l	%a1, -(%sp)
	movea.l	(%a1), %a1
	movea.l	16(%a1), %a1			/* its method +16: the entry's name */
	lea	8(%sp), %a0			/* written into the string */
	jsr	(%a1)
	addq.l	#8, %sp
	move.l	%sp, -(%sp)			/* &name */
	jsr	ref2_open_name			/* keeps its first characters */
	jsr	STRING_DROP			/* then the string goes, the same argument */
	addq.l	#8, %sp
9:	movea.l	(%sp)+, %a0
	jmp	OPEN
