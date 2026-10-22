/* The machine shortcuts and the sound record chain of model27's builder (notes/63 §3, step B4b): a part the composer
 * adds to a build when one of its machines declares a shortcut. Assembled once by tools/gen_parts.py into
 * shortcuts.o and placed by tools/relocate.py like a package; the composer writes the data block right after it and
 * resolves sc_data, the block's address, as a patch point. Addresses are VAs of OS 1.13.
 *
 *   sc_knob  entry +0x7c of ParameterPageView's vtable (0x401005a8; stock 0x4001e814, the knob -> descriptor lookup,
 *            which holds the registrar's knob_vec). The OS's three calls go through it: a knob turned (0x4001f6ee),
 *            TRACK + knob (0x4001d716), the popup at a track change (0x4001f090) (notes/47 §3.2). RETRIG held + COLOR,
 *            SHAPE, SWEEP or CONTOUR, on a track whose machine declared a shortcut on that knob, gives that
 *            shortcut's descriptor (1 to 4, the OS's unused "Error" ones), its fields and formatter written first.
 *            Anything else gives the stock answer, and so does a held FUNC (fine adjust), TRACK (Control All), LFO
 *            (its destination) or trig (a p-lock), so that a shortcut value is never p-locked or an LFO destination
 *            (notes/63 §9).
 *   sc_save2, sc_save1, sc_load
 *            the sound record functions: save version 2 (0x4005afa0), version 1 (0x4005b054), load (0x4005aecc).
 *            Each runs the next of the chain as if it were the function (a package's own wrapper, SAMPLE's, or the
 *            stock body), then copies k 28..31 of the sound into record slots 28..31 (save) or back (load), when the
 *            function did its work. The stock save keeps only k 0..22 and the load clears k 0..32 and reads slots
 *            0..23 (notes/47 §4.1).
 *
 * The four values live in k 28..31 of the sound (+76..+83) and record slots 28..31 (+84..+91), for every sound: they
 * mean what the track's machine says (notes/63 §3.2). The descriptors 1 to 4 keep the machine -1 of the stock ones,
 * so that the tables built at boot (rows, CC, NRPN, LFO destinations) leave them out; a machine change resets only
 * the five parameters of the machine's record (0x40014072), so the values stay (notes/63 §9, notes/64 §3).
 *
 * sc_data, filled by the composer (part.json, "data"):
 *   +0x00 next of save2, +0x04 next of save1, +0x08 next of load (0 = the stock body)
 *   +0x0c the descriptor table the OS uses (the build's moved copy)
 *   +0x10 first machine (byte), +0x11 number of machines (byte)
 *   +0x14 per machine, per knob COLOR, SHAPE, SWEEP, CONTOUR, 24 bytes: long name, short name, minimum, maximum,
 *         default (8.8), formatter; a long name of 0: no shortcut on that knob
 *
 * License: MIT (LICENSE next to this file). */

	.equ	LOOKUP, 0x4001e814		/* the stock knob -> descriptor lookup */
	.equ	KEY_HELD, 0x4007faf4		/* (logical key code) -> 1 while the key is held */
	.equ	K_FUNC, 1
	.equ	K_TRACK, 2
	.equ	K_RETRIG, 4
	.equ	K_LFO, 8
	.equ	UI_STATE, 0x400cf9a8		/* the UI's state */
	.equ	TRIG_HELD, 0x4006b736		/* (state) -> non-zero byte while a trig is held (+356) */
	.equ	TRACK_MACHINE, 0x4001e318	/* (view, track or -1 for the active one) -> that track's machine */
	.equ	UI_OBJ, 0x40a71754		/* the descriptors' interface objects, 100 bytes each */
	.equ	DSTRIDE, 0x38			/* a descriptor */
	.equ	ENTRY, 24			/* a shortcut in sc_data */

	.globl	sc_knob, sc_save2, sc_save1, sc_load

	.section .text.sc_knob, "ax"
	.p2align 2
sc_knob:
	move.l	16(%sp), -(%sp)			/* (view, knob, FUNC, track) to the stock lookup */
	move.l	16(%sp), -(%sp)
	move.l	16(%sp), -(%sp)
	move.l	16(%sp), -(%sp)
	jsr	LOOKUP
	lea	16(%sp), %sp
	lea	-16(%sp), %sp
	movem.l	%d2-%d4/%a2, (%sp)		/* now view at 20(sp), knob 24, FUNC 28, track 32 */
	move.l	%d0, %d4			/* the stock answer */
	move.l	24(%sp), %d2
	subq.l	#4, %d2				/* COLOR, SHAPE, SWEEP, CONTOUR -> 0..3 */
	moveq	#3, %d0
	cmp.l	%d2, %d0
	bcs.w	9f
	pea	K_RETRIG
	jsr	KEY_HELD
	addq.l	#4, %sp
	tst.l	%d0
	beq.w	9f
	lea	sc_off, %a2			/* the keys that keep the stock parameter */
1:	mvz.b	(%a2)+, %d0
	beq.s	2f
	move.l	%d0, -(%sp)
	jsr	KEY_HELD
	addq.l	#4, %sp
	tst.l	%d0
	beq.s	1b
	bra.w	9f
2:	jsr	UI_STATE
	move.l	%d0, -(%sp)
	jsr	TRIG_HELD
	addq.l	#4, %sp
	tst.b	%d0
	bne.w	9f
	move.l	32(%sp), -(%sp)			/* track */
	move.l	24(%sp), -(%sp)			/* view */
	jsr	TRACK_MACHINE
	addq.l	#8, %sp
	lea	sc_data, %a2
	mvz.b	16(%a2), %d1			/* first machine */
	sub.l	%d1, %d0
	bmi.w	9f
	mvz.b	17(%a2), %d1			/* machines */
	cmp.l	%d1, %d0
	bcc.w	9f
	lsl.l	#2, %d0
	add.l	%d2, %d0			/* machine * 4 + knob */
	mulu.w	#ENTRY, %d0
	lea	20(%a2,%d0.l), %a0		/* its shortcut */
	tst.l	(%a0)
	beq.w	9f
	moveq	#1, %d3
	add.l	%d2, %d3			/* its descriptor, 1..4 */
	move.l	%d3, %d0
	mulu.w	#DSTRIDE, %d0
	movea.l	12(%a2), %a1
	adda.l	%d0, %a1			/* in the table the OS uses; the machine (+0) stays -1 */
	moveq	#28, %d0
	add.l	%d2, %d0
	move.l	%d0, 4(%a1)			/* k 28..31 */
	move.l	8(%a0), %d0
	move.l	%d0, 8(%a1)			/* minimum */
	move.l	12(%a0), %d0
	move.l	%d0, 12(%a1)			/* maximum */
	move.l	16(%a0), %d0
	move.l	%d0, 16(%a1)			/* default */
	clr.l	0x14(%a1)			/* 0 as in every parameter's descriptor (1 in "Error" 1..3) */
	moveq	#-1, %d0
	move.l	%d0, 0x18(%a1)			/* no CC: "Error" 1..3 carry CC 1, 2 and 6, sent when edited */
	move.l	%d0, 0x1c(%a1)			/* no NRPN */
	clr.l	0x20(%a1)			/* 0 as in every parameter's descriptor (the "Error" index 1..4) */
	move.l	(%a0), %d0
	move.l	%d0, 0x2c(%a1)			/* long name */
	move.l	4(%a0), %d0
	move.l	%d0, 0x34(%a1)			/* short name */
	move.l	%d3, %d0
	mulu.w	#100, %d0
	lea	UI_OBJ, %a1
	adda.l	%d0, %a1			/* its interface object */
	move.l	20(%a0), %d0
	move.l	%d0, 0x20(%a1)			/* the formatter */
	clr.l	0x2c(%a1)			/* no special drawing (the "Error" picture) */
	move.l	%d3, %d4
9:	move.l	%d4, %d0
	movem.l	(%sp), %d2-%d4/%a2
	lea	16(%sp), %sp
	rts
sc_off:	.byte	K_FUNC, K_TRACK, K_LFO, 0

/* The record wrappers. The composer writes jmp sc_save2 (sc_save1, sc_load) and a nop over the function's first 8
 * bytes (lea -12(sp),sp ; movem.l a2-a4,(sp)); on entry the function's arguments are at 4(sp) and 8(sp). The
 * wrapper pushes a copy of them and its second half as the return address, then runs the next of the chain: a
 * package's wrapper, which sees a call of the function, or the 8 bytes and the stock body. Back in the second half,
 * d0 is the function's result and is kept. */
	.section .text.sc_record, "ax"
	.p2align 2
sc_save2:
	move.l	8(%sp), -(%sp)
	move.l	8(%sp), -(%sp)
	pea	sc_post_save
	move.l	sc_data, %d0			/* next of save2 */
	bne.s	sc_next
	lea	-12(%sp), %sp
	movem.l	%a2-%a4, (%sp)
	jmp	0x4005afa8
sc_save1:
	move.l	8(%sp), -(%sp)
	move.l	8(%sp), -(%sp)
	pea	sc_post_save
	move.l	sc_data+4, %d0			/* next of save1 */
	bne.s	sc_next
	lea	-12(%sp), %sp
	movem.l	%a2-%a4, (%sp)
	jmp	0x4005b05c
sc_load:
	move.l	8(%sp), -(%sp)
	move.l	8(%sp), -(%sp)
	pea	sc_post_load
	move.l	sc_data+8, %d0			/* next of load */
	bne.s	sc_next
	lea	-12(%sp), %sp
	movem.l	%a2-%a4, (%sp)
	jmp	0x4005aed4
sc_next:
	movea.l	%d0, %a0
	jmp	(%a0)

/* (record, sound) on the stack: k 28..31 (+76) into record slots 28..31 (+84), when the save did its work (d0's
 * byte 1; 0 for a null record or sound, which the stock functions check). */
sc_post_save:
	tst.b	%d0
	beq.s	1f
	movea.l	(%sp), %a0			/* record */
	movea.l	4(%sp), %a1			/* sound */
	move.l	76(%a1), %d1
	move.l	%d1, 84(%a0)
	move.l	80(%a1), %d1
	move.l	%d1, 88(%a0)
1:	addq.l	#8, %sp
	rts

/* (sound, record) on the stack: record slots 28..31 back into k 28..31, which the load cleared, when it loaded (d0's
 * byte 1; 0 for a null pointer or a record of another version than 2, and the sound is then left as it was). */
sc_post_load:
	tst.b	%d0
	beq.s	1f
	movea.l	(%sp), %a1			/* sound */
	movea.l	4(%sp), %a0			/* record */
	move.l	84(%a0), %d1
	move.l	%d1, 76(%a1)
	move.l	88(%a0), %d1
	move.l	%d1, 80(%a1)
1:	addq.l	#8, %sp
	rts
