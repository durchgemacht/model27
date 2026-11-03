/* The entries of model27's CPU page, with cpu.c (notes/78): a part the composer adds to a build when its card is
 * ticked. Built once by tools/gen_parts.py into cpu.o and placed by tools/relocate.py like a package; the composer
 * writes the data block right after it and resolves cpu_data, the block's address, as a patch point. Addresses are
 * VAs of OS 1.13.
 *
 *   cpu_probe  jsr from 0x40059382 in place of jsr 0x4005979e, the audio interrupt's (0x40058c5e) call of the audio
 *              function, its argument (the block's frame, fp - 44) on the stack. The return address goes to the data
 *              block, so that the audio function sees the stack exactly as from the call replaced (as syntakt-meter's
 *              probe, notes/23 §5); the timer is read before and after it, then cpu_block(busy). d0 comes back as the
 *              audio function left it; d2-d7/a2-a6 are kept (C ABI); d1, a0 and a1 are free after a call, and the
 *              interrupt uses none of them after this one (0x40059388: pea 0x20 ; pea 0x40fe4b90 ; jsr 0x40002912).
 *              The EMAC is not touched. Reached only from the audio interrupt, which does not nest: one return
 *              address in the data block is enough.
 *   cpu_cfg    jmp from 0x40032aee in place of movem.l 24(sp),d2-d6/a2-a6, the end of the device configuration list's
 *              constructor (DeviceSettingsMenuView, 0x40032726: USB mode, LCD, LED, Contrast), the list in a2: adds the
 *              row CPU with cpu_add_row, then the instruction replaced and the constructor's end at 0x40032af4 (lea
 *              128(sp),sp ; rts). Model-TG's cfg_hook.
 *   cpu_add_row (list, row): a row of the list from {label, value, turn, press}, its four closures built as the OS's
 *              list menus build theirs (the managers 0x4002f136 and 0x4002f188), the item constructed (0x400734b0),
 *              added to the list (0x40072ce6) and the closures let go (0x400cf044). Model-TG's lm_add_row, unchanged.
 *   cpu_lab    the row's label, "CPU", into the string a0 points to (0x400f980c), a0 back in d0: Model-TG's gm_lab.
 *   cpu_nop    its value and its turn: none (Model-TG's sys_nop).
 *   cpu_press  its press: cpu_open (cpu.c), the page.
 *   cpu_dtor0, cpu_dtor1
 *              the page's destructors (its vtable +0x00 and +0x04): the page forgotten, then the stock ones
 *              (0x400f43ca, 0x400f4486) with the stack as they were called. cpu_dtor0_th, cpu_dtor1_th: the same from
 *              the +4 base (this - 4), in place of 0x400f447c and 0x400f44c0, which go to the stock ones directly.
 *   cpu_enc    the page's encoder handler (this, event), in place of 0x400a28b4: DATA's turn (0x4006f6ce) does
 *              nothing; any other goes to the base's handler 0x4006fb90 with this + 4, as the stock one passes it.
 *              cpu_enc_th: from the +4 base, as 0x400a2926.
 *
 * License: MIT (LICENSE next to this file); cpu_cfg, cpu_add_row, cpu_lab, cpu_nop and the page's destructors and
 * encoder handler follow Model-TG's (TinyGregAudio, MIT, LICENSE-Model-TG). */

	.section .text.cpu_probe, "ax"
	.p2align 2
	.globl	cpu_probe
cpu_probe:
	move.l	(%sp)+, cpu_data+8		/* the return address */
	move.l	0xfc07000c, %d0
	move.l	%d0, cpu_data+12		/* the block's start */
	jsr	0x4005979e			/* the audio function, the call replaced */
	move.l	%d0, -(%sp)			/* its return value */
	move.l	0xfc07000c, %d1
	sub.l	cpu_data+12, %d1		/* the block's busy ticks */
	move.l	%d1, -(%sp)
	jsr	cpu_block
	addq.l	#4, %sp
	move.l	(%sp)+, %d0
	move.l	cpu_data+8, -(%sp)
	rts

	.section .text.cpu_cfg, "ax"
	.p2align 2
	.globl	cpu_cfg
cpu_cfg:
	lea	-16(%sp), %sp
	movem.l	%d0-%d1/%a0-%a1, (%sp)
	pea	cpu_row
	move.l	%a2, -(%sp)			/* the list */
	jsr	cpu_add_row
	addq.l	#8, %sp
	movem.l	(%sp), %d0-%d1/%a0-%a1
	lea	16(%sp), %sp
	movem.l	24(%sp), %d2-%d6/%a2-%a6	/* the instruction replaced */
	jmp	0x40032af4			/* the constructor's end */

/* cpu_add_row(list, row): Model-TG's lm_add_row. */
cpu_add_row:
	link.w	%fp, #-64
	lea	-16(%sp), %sp
	movem.l	%d4/%a3-%a5, (%sp)
	move.l	12(%fp), %d4			/* the row */
	lea	0x40080064, %a4			/* the allocator, as operator new */
	lea	-64(%fp), %a5			/* the four closures */
	pea	1
	jsr	(%a4)
	addq.l	#4, %sp
	move.l	%d0, (%a5)
	clr.l	4(%a5)
	move.l	#0x4002f136, %d0		/* the generic manager */
	move.l	%d0, 8(%a5)
	movea.l	%d4, %a0
	move.l	(%a0), %d0			/* the label */
	move.l	%d0, 12(%a5)
	pea	4
	jsr	(%a4)
	addq.l	#4, %sp
	movea.l	%d0, %a0
	move.l	8(%fp), (%a0)			/* the list */
	move.l	%d0, 16(%a5)
	clr.l	20(%a5)
	move.l	#0x4002f188, %d0		/* the manager of a closure with an argument */
	move.l	%d0, 24(%a5)
	movea.l	%d4, %a0
	move.l	12(%a0), %d0			/* the press */
	move.l	%d0, 28(%a5)
	pea	1
	jsr	(%a4)
	addq.l	#4, %sp
	move.l	%d0, 32(%a5)
	clr.l	36(%a5)
	move.l	#0x4002f136, %d0
	move.l	%d0, 40(%a5)
	movea.l	%d4, %a0
	move.l	4(%a0), %d0			/* the value */
	move.l	%d0, 44(%a5)
	pea	4
	jsr	(%a4)
	addq.l	#4, %sp
	movea.l	%d0, %a0
	move.l	8(%fp), (%a0)
	move.l	%d0, 48(%a5)
	clr.l	52(%a5)
	move.l	#0x4002f188, %d0
	move.l	%d0, 56(%a5)
	movea.l	%d4, %a0
	move.l	8(%a0), %d0			/* the turn */
	move.l	%d0, 60(%a5)
	pea	0x54				/* the item */
	jsr	(%a4)
	addq.l	#4, %sp
	movea.l	%d0, %a3
	pea	8
	pea	-1
	pea	48(%a5)
	pea	32(%a5)
	pea	16(%a5)
	move.l	%a5, -(%sp)
	move.l	%a3, -(%sp)
	jsr	0x400734b0			/* the item's constructor */
	lea	28(%sp), %sp
	move.l	%a3, -(%sp)
	move.l	8(%fp), -(%sp)
	jsr	0x40072ce6			/* added to the list */
	addq.l	#8, %sp
	pea	48(%a5)
	jsr	0x400cf044			/* the closures let go */
	addq.l	#4, %sp
	pea	32(%a5)
	jsr	0x400cf044
	addq.l	#4, %sp
	pea	16(%a5)
	jsr	0x400cf044
	addq.l	#4, %sp
	move.l	%a5, -(%sp)
	jsr	0x400cf044
	addq.l	#4, %sp
	movem.l	(%sp), %d4/%a3-%a5
	unlk	%fp
	rts

cpu_lab:
	lea	cpu_s_row, %a1
	link.w	%fp, #-4
	move.l	%d2, -(%sp)
	pea	-1(%fp)
	move.l	%a1, -(%sp)
	move.l	%a0, %d2			/* the string to write */
	move.l	%a0, -(%sp)
	jsr	0x400f980c
	lea	12(%sp), %sp
	move.l	%d2, %d0
	move.l	-8(%fp), %d2
	unlk	%fp
	rts
cpu_nop:
	moveq	#0, %d0
	rts
cpu_press:
	jsr	cpu_open
	moveq	#0, %d0
	rts

	.section .rodata.cpu_row, "a"
	.p2align 2
cpu_row:
	.long	cpu_lab, cpu_nop, cpu_nop, cpu_press
cpu_s_row:
	.asciz	"CPU"

	.section .text.cpu_page, "ax"
	.p2align 2
	.globl	cpu_dtor0, cpu_dtor1, cpu_dtor0_th, cpu_dtor1_th, cpu_enc, cpu_enc_th
cpu_dtor0:
	clr.l	cpu_data+48			/* the page is gone */
	jmp	0x400f43ca
cpu_dtor1:
	clr.l	cpu_data+48
	jmp	0x400f4486
cpu_dtor0_th:
	subq.l	#4, 4(%sp)			/* from the +4 base */
	bra.s	cpu_dtor0
cpu_dtor1_th:
	subq.l	#4, 4(%sp)
	bra.s	cpu_dtor1
cpu_enc_th:
	subq.l	#4, 4(%sp)			/* from the +4 base, as 0x400a2926 */
cpu_enc:
	move.l	8(%sp), -(%sp)			/* the event */
	jsr	0x4006f6ce			/* DATA's turn? */
	addq.l	#4, %sp
	tst.b	%d0
	bne.s	1f
	addq.l	#4, 4(%sp)			/* this + 4, as the stock handler passes the event on */
	jmp	0x4006fb90
1:	moveq	#1, %d0				/* DATA: nothing */
	rts
