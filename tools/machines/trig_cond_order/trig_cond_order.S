/* Trig Cond in another order on the knob (notes/70). Linked by trig_cond_order.ld into a freed sprite mask; the
 * writes on the OS are in tools/gen_trig_cond_order.py (VTABLE, HOOK), and so is the order (ORDER, written into
 * tco_order).
 *
 * A trig keeps one condition code, 0 to 63, in byte 516 + step of its pattern track (0x40015fd0, 0x40016010):
 * 0-7 FILL !FILL PRE !PRE NEI !NEI 1st !1st, 8-28 1% to 99%, 29-63 1:2 to 8:8. The sequencer (0x400913f0) and the
 * names (0x401090b4) go by that code, and so did the knob: a trig held + CHANCE steps the code itself. Here the
 * knob steps a position in tco_order instead, and the value window's five dots show that position; the code stored,
 * played and shown stays the stock one, so patterns are the same with and without the mod. */
	.globl	tco_step, tco_dots, tco_order

	.section .text.trig_cond_order, "ax"

/* d0 = a code 0..63: d1 = its position in tco_order, a0 = tco_order. tco_order holds each code once. */
pos:
	lea	tco_order, %a0
	moveq	#-1, %d1
1:	addq.l	#1, %d1
	cmp.b	(%a0,%d1.l), %d0
	bne.s	1b
	rts

/* TrigParameterSet's "value + delta" method (vtable entry 0x400fd218, stock 0x4000a980), which ParameterSet's knob
 * step (0x4000a5f8) calls as f(set, desc, value, delta) between reading the trig's value and writing it back; value
 * and delta are 8.8, the new value comes back in d0. d0-d1/a0-a1 are scratch (the OS's ABI).
 *   - desc 19 (Trig Cond), value = code << 8 with code 0..63: the code's position moves by delta >> 8, clamped to
 *     0..63, and the code at the new position comes back, << 8. The stock method does the same in the codes' own
 *     order: (code << 8) + delta clamped to 0..0x3f00, stored >> 8 (0x4000abdc), so code + (delta >> 8) clamped.
 *   - anything else (another descriptor, no lock: value -1): the stock method, with the same arguments. */
tco_step:
	moveq	#19, %d0
	cmp.l	8(%sp), %d0
	bne.s	9f
	move.l	12(%sp), %d0
	asr.l	#8, %d0			/* the code */
	moveq	#63, %d1
	cmp.l	%d0, %d1
	bcs.s	9f			/* not 0..63: the stock method */
	bsr.s	pos
	move.l	16(%sp), %d0
	asr.l	#8, %d0
	add.l	%d0, %d1
	bpl.s	2f
	moveq	#0, %d1
2:	moveq	#63, %d0
	cmp.l	%d0, %d1
	ble.s	3f
	move.l	%d0, %d1
3:	mvz.b	(%a0,%d1.l), %d0
	lsl.l	#8, %d0
	rts
9:	jmp	0x4000a980

/* 0x4001d91c, in the value window (ParameterPageView's vtable +0x90, 0x4001d818; d2 = descriptor, d5 = value):
 * jsr tco_dots in place of movea.l d5,a0 ; lsl.l #3,d4 ; lsl.l #6,d0. The window then lights dot
 * (a0 - min) * 5 / (max - min + 1) of five. For Trig Cond with a code 0..63, a0 = the code's position << 8, so the
 * dots follow the knob's order; else a0 = d5, as the stock code. d0, d1 and the other registers are kept. */
tco_dots:
	movea.l	%d5, %a0
	lsl.l	#3, %d4
	lsl.l	#6, %d0
	cmpi.l	#19, %d2
	bne.s	9f
	move.l	%d0, -(%sp)
	move.l	%d1, -(%sp)
	move.l	%d5, %d0
	asr.l	#8, %d0
	moveq	#63, %d1
	cmp.l	%d0, %d1
	bcs.s	8f			/* not a code: a0 = d5 */
	bsr.s	pos
	lsl.l	#8, %d1
	movea.l	%d1, %a0
8:	move.l	(%sp)+, %d1
	move.l	(%sp)+, %d0
9:	rts

	.section .data.trig_cond_order, "a"
tco_order:				/* position -> code, written by the generator */
	.space	64
