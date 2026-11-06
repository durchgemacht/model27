/* The machine shortcuts and the sound record chain of model27's builder (notes/63 §3, step B4b; the switches, §16):
 * a part the composer adds to a build when one of its machines declares a shortcut. Assembled once by
 * tools/gen_parts.py into shortcuts.o and placed by tools/relocate.py like a package; the composer writes the data
 * block right after it and resolves sc_data, the block's address, as a patch point. Addresses are VAs of OS 1.13.
 *
 *   sc_knob  entry +0x7c of ParameterPageView's vtable (0x401005a8; stock 0x4001e814, the knob -> descriptor lookup,
 *            which holds the registrar's knob_vec). The OS's three calls go through it: a knob turned (0x4001f6ee),
 *            TRACK + knob (0x4001d716), the popup at a track change (0x4001f090) (notes/47 §3.2). MACHINES held +
 *            COLOR, SHAPE, SWEEP or CONTOUR, on a track whose machine declared a shortcut on that knob, gives that
 *            shortcut's descriptor (1 to 4, the OS's unused "Error" ones), its fields and formatter written first.
 *            Anything else gives the stock answer, and so does a held FUNC (fine adjust), TRACK (Control All), LFO
 *            (its destination) or trig (a p-lock), so that a shortcut value is never p-locked or an LFO destination
 *            (notes/63 §9).
 *   sc_save2, sc_save1, sc_load
 *            the sound record functions: save version 2 (0x4005afa0), version 1 (0x4005b054), load (0x4005aecc).
 *            Each runs the next of the chain as if it were the function (a package's own wrapper, SAMPLE's, or the
 *            stock body), then copies k 28..31 of the sound into record slots 28..31 (save) or back (load), when the
 *            function did its work. The stock save keeps only k 0..22 and the load clears k 0..32 and reads slots
 *            0..23 (notes/47 §4.1). The switches too: k 32 into record slot 18 (save), slot 18 back into k 32 and
 *            k 0, where the stock load puts slot 18 and which nothing uses, cleared (load).
 *   sc_press jmp from 0x4001ac4a, over its first 6 bytes (lea -12(sp),sp ; moveq #1,d1): the function PUNCH's and
 *            GATE's presses call (0x4001c2d2, 0x4001caa2), (view, parameter 44 or 45), which switches PUNCH or GATE
 *            on the selected track, or on all six with TRACK held (Control All). MACHINES held, TRACK not, on a track
 *            whose machine declared that press: flips the machine's switch, asks for a new LED frame and returns to
 *            the caller, PUNCH or GATE left as they were; since 0.5 (notes/63 §27), with a trig held, the switch of
 *            each held step instead, as a p-lock of k 32 (sc_locks). Anything else: the 6 bytes, then the stock body.
 *   sc_leds  jsr from 0x4001cc86, over 6 bytes (move.l d0,d5 ; tst.l d2 ; seq d0) of MainScreenView's LED method,
 *            where d2 holds PUNCH and d0 GATE of the selected track (d4) and d0's byte then picks LED 19's state.
 *            MACHINES held, TRACK not, on a track whose machine declared a press: that key's LED shows the machine's
 *            switch instead (since 0.5, with a trig held, the first held step's: sc_shown). Returns with d5 and d0's
 *            byte as the 6 bytes leave them.
 *   sc_mach  jsr from 0x4001ca1e, over 6 bytes (move.l d3,-(sp) ; jsr (a3) ; addq.l #4,sp) of MainScreenView's MACHINES
 *            case (0x4001c252): a3 the "fresh press" test (0x400724a0), d3 the event, a2 the view; the stock code then
 *            toggles the MACHINES list on d0 != 0 (0x4001ca2a: opens it, or closes it when it is open, 0x40077da8 with
 *            its flag) and passes the event on otherwise (0x4001c608). Reached on a fresh press without FUNC and
 *            without a held trig, and on every other MACHINES event. Since 0.4 (the key map of 2026-10-31: MACHINES
 *            held is the level of the track's machine), on a track whose machine declared a shortcut or a switch, a
 *            press that would open the list opens nothing yet and ends the handler as taken (0x4001c2a8); the release
 *            opens it when no shortcut or switch acted while MACHINES was held (or the PRESET browser when sc_mtrig
 *            took the press, since 0.5). A press while the list is open closes
 *            it at once, as on the stock OS. Elsewhere, the stock test's answer: the stock toggle on the press. Since
 *            0.6, in a build with Transpose, every track is such a track (sc_level, sc_data +0x1c).
 *   sc_mtrig jmp from 0x4001c274 over 6 bytes (jsr 0x400cf9a8, the UI's state) of MainScreenView's MACHINES case, where
 *            the stock code asks, on a fresh press without FUNC, whether a trig is held, then goes to the PRESET browser
 *            (0x4001c996) or on to 0x4001ca1e (sc_mach). Since the layer's 0.5 (notes/63 §26): a trig held on a track
 *            whose machine declared a switch opens nothing yet and ends the handler as taken; the release opens the
 *            browser, from the handler's own path, when no switch acted while MACHINES was held (sc_mach). Written with
 *            the press and the LEDs, in the builds with a switch. Elsewhere the stock answer.
 *   sc_steplock jmp from 0x40022eac over move.l d3,-(sp) and the first 4 bytes of jsr 0x400724a0, in the step keys'
 *            handler (0x40022382), which sees the keys before MainScreenView: with a step held, PUNCH or GATE lands
 *            there and the stock code toggles a p-lock of PUNCH or GATE on the held steps (notes/63 §29). Since the
 *            layer's 0.5, MACHINES held, TRACK not, on a track whose machine declared that press: the switch locked
 *            instead (sc_locks), the hold marked, the LEDs asked, the press taken. Written with the press and the
 *            LEDs, in the builds with a switch. Elsewhere the stock lock of PUNCH or GATE.
 *   sc_gridleds jsr from 0x40022112 over jsr 0x400cfc5e in PatternGridView's LED method (0x40021d22), reached only
 *            with a trig held, after its lambda (0x400217d6) set the bits of a byte of the method's frame for the LEDs
 *            of the list 0x40100a94: bit 1 LED 19 (PUNCH) when a held step has a p-lock of PUNCH, bit 2 LED 20 (GATE);
 *            the loop at 0x4002211c lights them next, over MainScreenView's (notes/63 §30). Since the layer's 0.5,
 *            MACHINES held, TRACK not, on a track whose machine declared a press: that key's bit shows the first held
 *            step's switch (sc_shown), as sc_leds does. Then the stock call. Written with the press, in the builds with
 *            a switch.
 *   sc_conv, sc_ptab
 *            the pattern's p-lock rows (notes/47 §4.3; the filter slot's fl_conv and fl_ptab up to its 0.10, here since
 *            the layer's 0.5, notes/63 §25), in every build with the layer. The pattern's file keeps a row per index
 *            and track, the index of k from 0x4010ee4c (23 entries, read without a bound by the full save 0x4005b95c
 *            and the update of one p-lock 0x4005ba90: a p-lock of k >= 23 landed on LFO Speed, Multiplier...; k 32's,
 *            on index 9, which loads on k 9, the machine). The two leas' operands (0x4005b998, 0x4005baca) point at
 *            sc_ptab: k 0..22 as the OS, 23..31 -> 24..32 and 32 -> 18, indices the OS never writes. sc_conv, a jmp
 *            from 0x4005aa34 over moveq #23,d2 ; cmp.l d0,d2 ; bcc.s 0x4005aa46 in 0x4005aa1a (track, index -> k),
 *            tracks 0..5: index 18 -> k 32, 24..32 -> k = index - 1, 0..23 through the stock table, beyond 32 none.
 *            The official OS loads index 18 on k 0, which nothing reads, and 24..32 on nothing.
 *
 * The four values live in k 28..31 of the sound (+76..+83) and record slots 28..31 (+84..+91), for every sound: they
 * mean what the track's machine says (notes/63 §3.2). The descriptors 1 to 4 keep the machine -1 of the stock ones,
 * so that the tables built at boot (rows, CC, NRPN, LFO destinations) leave them out; a machine change resets only
 * the five parameters of the machine's record (0x40014072), so the values stay (notes/63 §9, notes/64 §3). The
 * switches live in k 32 of the sound (+84): bit 8 MACHINES + PUNCH, bit 9 MACHINES + GATE, and in record slot 18 (+64)
 * (notes/63 §16.4). A machine reads them in the sound its note plays, not in its parameters, which the OS smooths.
 *
 * sc_data, filled by the composer (part.json, "data"):
 *   +0x00 next of save2, +0x04 next of save1, +0x08 next of load (0 = the stock body)
 *   +0x0c the descriptor table the OS uses (the build's moved copy)
 *   +0x10 first machine (byte), +0x11 number of machines (byte), +0x12 a MACHINES press waits for its release (1 the
 *         list, 2 the PRESET browser, since 0.5), +0x13 a shortcut or a switch acted while it was held (both 0 at boot,
 *         written by sc_mach, sc_mtrig, sc_knob, sc_press)
 *   +0x14 per machine, one byte: the presses it declared, bit 0 PUNCH, bit 1 GATE (8 machines at most)
 *   +0x1c since 0.6, bit 0: MACHINES is a held key on every track, not only on the machines' (a build with
 *         Transpose, whose part marks +0x13 when it acts); three bytes 0
 *   +0x20 per machine, per knob COLOR, SHAPE, SWEEP, CONTOUR, 24 bytes: long name, short name, minimum, maximum,
 *         default (8.8), formatter; a long name of 0: no shortcut on that knob
 *
 * License: MIT (LICENSE next to this file). */

	.equ	LOOKUP, 0x4001e814		/* the stock knob -> descriptor lookup */
	.equ	KEY_HELD, 0x4007faf4		/* (logical key code) -> 1 while the key is held */
	.equ	K_FUNC, 1
	.equ	K_TRACK, 2
	.equ	K_LEVEL, 5			/* MACHINES, the layer's key since 0.3 (the key map of 2026-10-31); RETRIG, 4, up to 0.2 */
	.equ	K_LFO, 8
	.equ	UI_STATE, 0x400cf9a8		/* the UI's state */
	.equ	TRIG_HELD, 0x4006b736		/* (state) -> non-zero byte while a trig is held (+356) */
	.equ	TRACK_MACHINE, 0x4001e318	/* (view, track or -1 for the active one) -> that track's machine */
	.equ	UI_OBJ, 0x40a71754		/* the descriptors' interface objects, 100 bytes each */
	.equ	DSTRIDE, 0x38			/* a descriptor */
	.equ	ENTRY, 24			/* a shortcut in sc_data */
	.equ	FIRST, 0x10			/* sc_data: first machine, number of machines, presses, shortcuts */
	.equ	COUNT, 0x11
	.equ	PRESSES, 0x14
	.equ	EVERY, 0x1c			/* since 0.6: bit 0, MACHINES a held key on every track (Transpose) */
	.equ	ENTRIES, 0x20
	.equ	PROJECT, 0x400cf866		/* the project singleton */
	.equ	PROJECT_TRACKS, 0x4000eb90	/* project -> its track selection */
	.equ	ACTIVE_TRACK, 0x40012412	/* track selection -> the selected track, 0..5 */
	.equ	TRACK_AT, 212			/* the project's track t at +212 + t * 68; its sound from method +40 */
	.equ	TRACK_STRIDE, 68
	.equ	MACHINE_AT, 38			/* sound: k 9's high byte, the machine */
	.equ	SWITCHES_AT, 84			/* sound: k 32, the switches */
	.equ	PRESS_BODY, 0x4001ac50		/* 0x4001ac4a after the 6 bytes sc_press takes */
	.equ	PENDING, 0x12			/* sc_data: a MACHINES press waits for its release */
	.equ	USED, 0x13			/* sc_data: a shortcut or a switch acted while MACHINES was held */
	.equ	KEY_RELEASED, 0x40072470	/* (event) -> 1 for a release */
	.equ	KEY_TAKEN, 0x4001c2a8		/* MainScreenView's key handler: d2 = 1 (taken), its end */
	.equ	BROWSER, 0x4001c996		/* its MACHINES case: the PRESET browser pushed, then its end */
	.equ	MACH_SITE, 0x4001ca1e		/* its MACHINES case after the held-trig test: jsr sc_mach */
	.equ	SEQ_OF, 0x4000f23e		/* (project) -> the selected track's sequence: +44 the pattern's locks, +56 its track */
	.equ	SEQ_LENGTH, 0x40016402		/* (sequence) -> the pattern's length in steps */
	.equ	LOCK_SET, 0x4001646a		/* (sequence, step, k, value) -> 1: the lock written, the pattern's file told */
	.equ	LOCK_CLEAR, 0x400164b0		/* (sequence, step, k) -> 1: the lock cleared */
	.equ	EDIT_BEGIN, 0x4006b740		/* (state, 1): what the stock knob lock does before its writes */
	.equ	EDIT_END, 0x4006b954		/* (state): after them; the held trigs' release then toggles nothing */
	.equ	HELD_HI, 348			/* the UI's state: the held steps, 32..63 */
	.equ	HELD_LO, 352			/* 0..31 */
	.equ	LOCK_K, 32			/* the switches' k */
	.equ	KEY_CODE, 0x4007240c		/* (event) -> its key's code: 6 PUNCH, 7 GATE */
	.equ	FRESH, 0x400724a0		/* (event) -> 1 for a fresh press */
	.equ	STEP_TAKEN, 0x40022ff2		/* the step keys' handler: d2 = 1 (taken), its end */
	.equ	STEP_STOCK, 0x40022ebc		/* the same: its lock of PUNCH or GATE on the held steps */
	.equ	MACHINES_VT, 0x40117920	/* the MACHINES list's vtable */
	.equ	CONTROLLER_AT, 44		/* MainScreenView: its controller, whose views are a list at +20 (node: +0 next, +8 view) */
	.equ	VIEWS_AT, 20
	.equ	VIEW_LEDS, 0x400760ba		/* (view): its LEDs changed, redo the LED frame (notes/58 §3) */
	.equ	GRID_STOCK, 0x400cfc5e		/* what PatternGridView's LED method calls at 0x40022112, (d3) */
	.equ	GRID_BITS, 91			/* sc_gridleds' sp on entry: the method's frame at + 28, its LEDs' byte at + 63 */

	.globl	sc_knob, sc_save2, sc_save1, sc_load, sc_press, sc_leds, sc_conv, sc_ptab

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
	pea	K_LEVEL
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
	mvz.b	FIRST(%a2), %d1			/* first machine */
	sub.l	%d1, %d0
	bmi.w	9f
	mvz.b	COUNT(%a2), %d1			/* machines */
	cmp.l	%d1, %d0
	bcc.w	9f
	lsl.l	#2, %d0
	add.l	%d2, %d0			/* machine * 4 + knob */
	mulu.w	#ENTRY, %d0
	lea	ENTRIES(%a2,%d0.l), %a0		/* its shortcut */
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
	move.b	#1, USED(%a2)			/* MACHINES acted as a modifier */
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

/* (record, sound) on the stack: k 28..31 (+76) into record slots 28..31 (+84) and the switches, k 32 (+84), into
 * record slot 18 (+64), when the save did its work (d0's byte 1; 0 for a null record or sound, which the stock
 * functions check). */
sc_post_save:
	tst.b	%d0
	beq.s	1f
	movea.l	(%sp), %a0			/* record */
	movea.l	4(%sp), %a1			/* sound */
	move.l	76(%a1), %d1
	move.l	%d1, 84(%a0)
	move.l	80(%a1), %d1
	move.l	%d1, 88(%a0)
	move.w	SWITCHES_AT(%a1), %d1
	move.w	%d1, 64(%a0)
1:	addq.l	#8, %sp
	rts

/* (sound, record) on the stack: record slots 28..31 back into k 28..31, which the load cleared, and slot 18 into
 * k 32, k 0 (where the stock load put slot 18) cleared, when it loaded (d0's byte 1; 0 for a null pointer or a record
 * of another version than 2, and the sound is then left as it was). */
sc_post_load:
	tst.b	%d0
	beq.s	1f
	movea.l	(%sp), %a1			/* sound */
	movea.l	4(%sp), %a0			/* record */
	move.l	84(%a0), %d1
	move.l	%d1, 76(%a1)
	move.l	88(%a0), %d1
	move.l	%d1, 80(%a1)
	move.w	64(%a0), %d1
	move.w	%d1, SWITCHES_AT(%a1)
	clr.w	20(%a1)				/* k 0 */
1:	addq.l	#8, %sp
	rts

/* The switches (notes/63 §16). The composer writes jmp sc_press over 0x4001ac4a's first 6 bytes; on entry the
 * function's arguments are at 4(sp) (the view, MainScreenView) and 8(sp) (the parameter, 44 PUNCH or 45 GATE). */
	.section .text.sc_press, "ax"
	.p2align 2
sc_press:
	move.l	%d2, -(%sp)			/* now view at 8(sp), parameter at 12(sp) */
	move.l	12(%sp), %d2
	subi.l	#44, %d2			/* PUNCH 0, GATE 1 */
	moveq	#1, %d0
	cmp.l	%d2, %d0
	bcs.w	8f
	pea	K_LEVEL
	jsr	KEY_HELD
	addq.l	#4, %sp
	tst.l	%d0
	beq.w	8f
	pea	K_TRACK				/* TRACK keeps Control All */
	jsr	KEY_HELD
	addq.l	#4, %sp
	tst.l	%d0
	bne.w	8f
	bsr.w	sc_selected
	bsr.w	sc_track
	btst	%d2, %d1			/* the machine declared this press */
	beq.w	8f
	move.l	%a0, -(%sp)			/* the sound */
	jsr	UI_STATE
	move.l	%d0, -(%sp)
	jsr	TRIG_HELD
	addq.l	#4, %sp
	movea.l	(%sp)+, %a0
	tst.b	%d0
	beq.s	1f
	bsr.w	sc_locks			/* a trig held: the switch of each held step, as a lock */
	bra.s	2f
1:	addq.l	#8, %d2				/* its switch: bit 8 or 9 of k 32 */
	mvz.w	SWITCHES_AT(%a0), %d1
	bchg	%d2, %d1
	move.w	%d1, SWITCHES_AT(%a0)
2:	lea	sc_data, %a1
	move.b	#1, USED(%a1)			/* MACHINES acted as a modifier */
	move.l	8(%sp), -(%sp)			/* the view: PUNCH's or GATE's LED follows */
	jsr	VIEW_LEDS
	addq.l	#4, %sp
	move.l	(%sp)+, %d2
	rts					/* to the press's caller: PUNCH or GATE stays */
8:	move.l	(%sp)+, %d2
	lea	-12(%sp), %sp			/* the 6 bytes, then the stock body */
	moveq	#1, %d1
	jmp	PRESS_BODY

/* The composer writes jsr sc_leds over 6 bytes of MainScreenView's LED method (0x4001cc86). On entry d0 is GATE, d2
 * PUNCH, d4 the selected track; d5 must leave with GATE and d0's byte with seq of PUNCH, as the 6 bytes leave them.
 * d2 is written right after (move.l fp,d2), the rest is kept. In sc_press's section, so that the bsr to the two
 * helpers below stay inside one section (a part's object carries only R_68K_32 relocations). */
	.p2align 2
sc_leds:
	move.l	%d0, %d5			/* GATE */
	move.l	%d3, -(%sp)
	pea	K_LEVEL
	jsr	KEY_HELD
	addq.l	#4, %sp
	tst.l	%d0
	beq.s	9f
	pea	K_TRACK
	jsr	KEY_HELD
	addq.l	#4, %sp
	tst.l	%d0
	bne.s	9f
	move.l	%d4, %d0
	bsr.w	sc_track
	move.l	%d1, %d3			/* the presses the machine declared */
	beq.s	9f
	mvz.w	SWITCHES_AT(%a0), %d1
	bsr.w	sc_shown			/* with a trig held, the first held step's */
	btst	#0, %d3
	beq.s	1f
	move.l	%d1, %d2
	andi.l	#0x100, %d2			/* PUNCH's LED: the machine's switch */
1:	btst	#1, %d3
	beq.s	9f
	move.l	%d1, %d5
	andi.l	#0x200, %d5			/* GATE's LED: the machine's switch */
9:	move.l	(%sp)+, %d3
	tst.l	%d2
	seq	%d0
	rts

/* The switches as p-locks of k 32 (since 0.5, notes/63 §27): d2 the switch (0 Loop on PUNCH, 1 Reverse on GATE), a0
 * the selected track's sound. For each held step below the pattern's length, its switch flipped against what the
 * step plays: the lock's when the lock holds that switch, else the sound's. A lock's word holds bits 8 and 9, the
 * values, and bits 10 and 11, which switches it holds (the maintainer's E1); a switch flipped back to the sound's
 * value leaves the lock, and a lock that holds none is cleared (E2). Around the writes what the stock knob lock does
 * (EDIT_BEGIN, EDIT_END), so that the trig's release does not toggle it. Keeps d2..d7, a2..a6. */
sc_locks:
	lea	-32(%sp), %sp
	movem.l	%d2-%d7/%a2-%a3, (%sp)
	move.l	%d2, %d7			/* the switch */
	mvz.w	SWITCHES_AT(%a0), %d6		/* the sound's word */
	jsr	UI_STATE
	movea.l	%d0, %a3			/* the UI's state */
	pea	1
	move.l	%a3, -(%sp)
	jsr	EDIT_BEGIN
	addq.l	#8, %sp
	jsr	PROJECT
	move.l	%d0, -(%sp)
	jsr	SEQ_OF
	movea.l	%d0, %a2			/* the selected track's sequence */
	move.l	%a2, (%sp)
	jsr	SEQ_LENGTH
	addq.l	#4, %sp
	move.l	%d0, %d5			/* the pattern's length */
	moveq	#0, %d4				/* the step */
10:	cmp.l	%d5, %d4
	bge.w	19f
	move.l	%d4, %d0
	move.l	HELD_LO(%a3), %d1
	moveq	#32, %d2
	cmp.l	%d2, %d0
	blt.s	11f
	sub.l	%d2, %d0
	move.l	HELD_HI(%a3), %d1
11:	btst	%d0, %d1
	beq.w	18f				/* not held */
	bsr.w	sc_lockword
	move.l	%d0, %d3			/* the step's lock, -1 none */
	moveq	#0, %d1
	tst.l	%d3
	bmi.s	12f
	move.l	%d3, %d1
	andi.l	#0xf00, %d1			/* what the lock holds */
12:	move.l	%d7, %d0
	addq.l	#8, %d0				/* the value's bit */
	moveq	#0, %d2				/* what the step plays: the sound's... */
	btst	%d0, %d6
	beq.s	13f
	moveq	#1, %d2
13:	addq.l	#2, %d0				/* ... or the lock's, when it holds the switch */
	btst	%d0, %d1
	beq.s	14f
	subq.l	#2, %d0
	moveq	#0, %d2
	btst	%d0, %d1
	beq.s	14f
	moveq	#1, %d2
14:	moveq	#1, %d0
	eor.l	%d0, %d2			/* flipped */
	move.l	%d7, %d0
	addq.l	#8, %d0
	btst	%d0, %d6			/* the sound's value */
	beq.s	15f
	tst.l	%d2
	bne.s	16f				/* the sound's again: the lock lets the switch go */
	bra.s	17f
15:	tst.l	%d2
	beq.s	16f
17:	bclr	%d0, %d1			/* the lock holds the switch, its value flipped */
	tst.l	%d2
	beq.s	1f
	bset	%d0, %d1
1:	addq.l	#2, %d0
	bset	%d0, %d1
	bra.s	2f
16:	bclr	%d0, %d1
	addq.l	#2, %d0
	bclr	%d0, %d1
2:	move.l	%d1, %d0
	andi.l	#0xc00, %d0
	bne.s	3f
	tst.l	%d3				/* holds no switch: cleared, if there was one */
	bmi.s	18f
	pea	LOCK_K
	move.l	%d4, -(%sp)
	move.l	%a2, -(%sp)
	jsr	LOCK_CLEAR
	lea	12(%sp), %sp
	bra.s	18f
3:	move.l	%d1, -(%sp)
	pea	LOCK_K
	move.l	%d4, -(%sp)
	move.l	%a2, -(%sp)
	jsr	LOCK_SET
	lea	16(%sp), %sp
18:	addq.l	#1, %d4
	bra.w	10b
19:	move.l	%a3, -(%sp)
	jsr	EDIT_END
	addq.l	#4, %sp
	movem.l	(%sp), %d2-%d7/%a2-%a3
	lea	32(%sp), %sp
	rts

/* a2 a sequence, d4 a step -> d0 the step's lock of k 32 (sign-extended, -1 none or no pattern), read as the OS's
 * lock functions read it (0x4000dece): the pattern's locks from the method at +40 of the vtable of the object at +44,
 * the track at +56, the word at + 4385 t + 68 step + 2 k. Keeps d2..d7, a2..a6. */
sc_lockword:
	move.l	44(%a2), %d0
	beq.s	1f
	movea.l	%d0, %a0
	move.l	%a0, -(%sp)
	movea.l	(%a0), %a1
	movea.l	40(%a1), %a1
	jsr	(%a1)
	addq.l	#4, %sp
	tst.l	%d0
	beq.s	1f
	movea.l	%d0, %a0
	move.l	56(%a2), %d0
	bmi.s	1f
	mulu.w	#4385, %d0
	adda.l	%d0, %a0
	move.l	%d4, %d0
	mulu.w	#68, %d0
	adda.l	%d0, %a0
	mvs.w	2 * LOCK_K(%a0), %d0
	rts
1:	moveq	#-1, %d0
	rts

/* d1 the sound's switches (k 32), with a trig held -> d1 the first held step's: for each switch the lock's value
 * when the step's lock holds it, else the sound's (since 0.5). d0, a0 and a1 are free; keeps d2..d7, a2..a6. */
sc_shown:
	lea	-16(%sp), %sp
	movem.l	%d2-%d4/%a2, (%sp)
	move.l	%d1, %d2			/* the sound's */
	jsr	UI_STATE
	movea.l	%d0, %a2
	move.l	%d0, -(%sp)
	jsr	TRIG_HELD
	addq.l	#4, %sp
	tst.b	%d0
	beq.s	8f
	moveq	#0, %d4
	move.l	HELD_LO(%a2), %d0
	bne.s	1f
	moveq	#32, %d4
	move.l	HELD_HI(%a2), %d0
	beq.s	8f
1:	move.l	%d0, %d1			/* its lowest bit: the first held step */
	neg.l	%d1
	and.l	%d0, %d1
	ff1	%d1
	moveq	#31, %d0
	sub.l	%d1, %d0
	add.l	%d0, %d4
	jsr	PROJECT
	move.l	%d0, -(%sp)
	jsr	SEQ_OF
	addq.l	#4, %sp
	movea.l	%d0, %a2
	bsr.w	sc_lockword
	tst.l	%d0
	bmi.s	8f
	move.l	%d2, %d1
	btst	#10, %d0
	beq.s	2f
	bclr	#8, %d1
	btst	#8, %d0
	beq.s	2f
	bset	#8, %d1
2:	btst	#11, %d0
	beq.s	9f
	bclr	#9, %d1
	btst	#9, %d0
	beq.s	9f
	bset	#9, %d1
	bra.s	9f
8:	move.l	%d2, %d1
9:	movem.l	(%sp), %d2-%d4/%a2
	lea	16(%sp), %sp
	rts

/* jmp from 0x40022eac in the step keys' handler (0x40022382): PUNCH or GATE with a step held, where the stock code
 * asks for a fresh press, then toggles a p-lock of PUNCH or GATE on every held step. d3 the event, a2 the handler's
 * view, the stack balanced; keeps d2..d7, a2..a6 for the stock code. */
	.globl	sc_steplock
sc_steplock:
	move.l	%d3, -(%sp)
	jsr	FRESH
	addq.l	#4, %sp
	tst.b	%d0
	beq.w	9f				/* not a fresh press: taken, as the stock code */
	pea	K_LEVEL
	jsr	KEY_HELD
	addq.l	#4, %sp
	tst.l	%d0
	beq.w	8f
	pea	K_TRACK
	jsr	KEY_HELD
	addq.l	#4, %sp
	tst.l	%d0
	bne.w	8f
	move.l	%d3, -(%sp)
	jsr	KEY_CODE
	addq.l	#4, %sp
	subq.l	#6, %d0				/* PUNCH 0, GATE 1 */
	moveq	#1, %d1
	cmp.l	%d0, %d1
	bcs.w	8f
	move.l	%d2, -(%sp)
	move.l	%d0, %d2
	bsr.w	sc_selected
	bsr.w	sc_track			/* a0 the sound, d1 the presses its machine declared */
	btst	%d2, %d1
	beq.s	7f
	bsr.w	sc_locks			/* the switch locked on the held steps */
	lea	sc_data, %a1
	move.b	#1, USED(%a1)			/* MACHINES acted as a modifier */
	move.l	%a2, -(%sp)
	jsr	VIEW_LEDS
	addq.l	#4, %sp
	move.l	(%sp)+, %d2
9:	jmp	STEP_TAKEN
7:	move.l	(%sp)+, %d2
8:	jmp	STEP_STOCK			/* the stock lock of PUNCH or GATE */

/* jsr from 0x40022112 in PatternGridView's LED method (see the head of this file), over jsr 0x400cfc5e, its argument
 * d3 already pushed: on entry the return address, then that argument, then the method's frame B (its sp after its
 * prologue, 0x40022110 having it at sp + 20), whose byte B + 63 holds the bits of the LEDs 0x12, 0x13 (PUNCH), 0x14
 * (GATE), 0x15, 0x1b (the list 0x40100a94) that the loop at 0x4002211c lights. MACHINES held, TRACK not, on a track whose machine
 * declared a press: that key's bit set to the first held step's switch. Then 0x400cfc5e(d3), a tail call that returns
 * to the method. Keeps d2..d7, a2..a6. */
	.globl	sc_gridleds
sc_gridleds:
	move.l	%d3, -(%sp)
	pea	K_LEVEL
	jsr	KEY_HELD
	addq.l	#4, %sp
	tst.l	%d0
	beq.s	9f
	pea	K_TRACK
	jsr	KEY_HELD
	addq.l	#4, %sp
	tst.l	%d0
	bne.s	9f
	bsr.w	sc_selected
	bsr.w	sc_track			/* a0 the sound, d1 the presses its machine declared */
	move.l	%d1, %d3
	beq.s	9f
	mvz.w	SWITCHES_AT(%a0), %d1
	bsr.w	sc_shown			/* the first held step's */
	mvz.b	GRID_BITS + 4(%sp), %d0
	btst	#0, %d3
	beq.s	1f
	bclr	#1, %d0				/* PUNCH's LED: the switch */
	btst	#8, %d1
	beq.s	1f
	bset	#1, %d0
1:	btst	#1, %d3
	beq.s	2f
	bclr	#2, %d0				/* GATE's LED: the switch */
	btst	#9, %d1
	beq.s	2f
	bset	#2, %d0
2:	move.b	%d0, GRID_BITS + 4(%sp)
9:	move.l	(%sp)+, %d3
	jmp	GRID_STOCK

/* -> d0 the selected track, 0..5, or -1 without a project. */
sc_selected:
	jsr	PROJECT
	tst.l	%d0
	beq.s	1f
	move.l	%d0, -(%sp)
	jsr	PROJECT_TRACKS
	move.l	%d0, (%sp)
	jsr	ACTIVE_TRACK
	addq.l	#4, %sp
	rts
1:	moveq	#-1, %d0
	rts

/* d0 a track -> a0 its sound and d1 the presses its machine declared (sc_data), or d1 0: no track 0..5, no sound,
 * or a machine outside the table. Found as the dispatchers find it (dispatch.c): the project's track, the sound from
 * the method at +40 of its vtable, the machine in the sound's byte +38. Keeps d2..d7, a2..a6. */
sc_track:
	move.l	%d2, -(%sp)
	move.l	%d0, %d2
	moveq	#5, %d1
	cmp.l	%d2, %d1
	bcs.s	8f
	jsr	PROJECT
	tst.l	%d0
	beq.s	8f
	mulu.w	#TRACK_STRIDE, %d2
	add.l	%d0, %d2
	addi.l	#TRACK_AT, %d2			/* the project's track */
	movea.l	%d2, %a0
	move.l	(%a0), %d0			/* its vtable */
	beq.s	8f
	movea.l	%d0, %a1
	move.l	40(%a1), %d0
	beq.s	8f
	movea.l	%d0, %a1
	move.l	%d2, -(%sp)
	jsr	(%a1)				/* its sound */
	addq.l	#4, %sp
	tst.l	%d0
	beq.s	8f
	movea.l	%d0, %a0
	mvz.b	MACHINE_AT(%a0), %d0
	lea	sc_data, %a1
	mvz.b	FIRST(%a1), %d1
	sub.l	%d1, %d0
	bmi.s	8f
	mvz.b	COUNT(%a1), %d1
	cmp.l	%d1, %d0
	bcc.s	8f
	mvz.b	PRESSES(%a1,%d0.l), %d1
	move.l	(%sp)+, %d2
	rts
8:	moveq	#0, %d1
	moveq	#-1, %d0			/* no machine of the table (sc_level) */
	move.l	(%sp)+, %d2
	rts

/* jsr from 0x4001ca1e in MainScreenView's MACHINES case (see the head of this file): d0 for the stock code's
 * tst.b d0 (toggle the list or not), or the handler's end as taken. Keeps d2..d7, a2..a6. */
	.globl	sc_mach
sc_mach:
	move.l	%d3, -(%sp)
	jsr	(%a3)				/* the stock test: a fresh press? */
	addq.l	#4, %sp
	tst.b	%d0
	beq.s	5f
	bsr.w	sc_level			/* the selected track's machine has a shortcut or a switch? */
	tst.l	%d0
	beq.s	1f
	bsr.w	sc_open				/* the list open: the press closes it, as on the stock OS */
	tst.l	%d0
	bne.s	1f
	lea	sc_data, %a1
	move.b	#1, PENDING(%a1)		/* the list waits for the release */
	clr.b	USED(%a1)
	addq.l	#4, %sp
	jmp	KEY_TAKEN			/* the press taken, nothing toggled */
1:	lea	sc_data, %a1
	clr.b	PENDING(%a1)
	moveq	#1, %d0				/* the stock toggle, at once */
	rts
5:	move.l	%d3, -(%sp)
	jsr	KEY_RELEASED
	addq.l	#4, %sp
	lea	sc_data, %a1
	tst.b	%d0
	beq.s	7f
	mvz.b	PENDING(%a1), %d1
	beq.s	7f
	clr.b	PENDING(%a1)
	tst.b	USED(%a1)
	bne.s	7f
	subq.l	#2, %d1
	beq.s	6f
	moveq	#1, %d0				/* released, nothing acted: the toggle now */
	rts
6:	addq.l	#4, %sp				/* the PRESET browser (a trig was held on the press, sc_mtrig): the */
	moveq	#1, %d2				/* handler's own path, the event taken, as on the stock press */
	jmp	BROWSER
7:	moveq	#0, %d0				/* as the stock test answered: no toggle */
	rts

/* jmp from 0x4001c274 in MainScreenView's MACHINES case (see the head of this file), on a fresh press without FUNC:
 * the stock code's question, a trig held?, then the PRESET browser at once, unless the selected track's machine
 * declared a switch: then the browser waits for the release (+0x12 = 2) and the press is taken. No trig held: on to
 * 0x4001ca1e, as the stock code. a2 the view, d3 the event, d2 the press; keeps d2..d7, a2..a6. */
	.globl	sc_mtrig
sc_mtrig:
	jsr	UI_STATE
	move.l	%d0, -(%sp)
	jsr	TRIG_HELD
	addq.l	#4, %sp
	tst.b	%d0
	beq.s	8f
	bsr.w	sc_selected
	bsr.w	sc_track			/* d1 the presses its machine declared */
	tst.l	%d1
	beq.s	7f
	lea	sc_data, %a1
	move.b	#2, PENDING(%a1)		/* the browser waits for the release */
	clr.b	USED(%a1)
	move.l	%a2, -(%sp)			/* a new LED frame: PUNCH and GATE show the held step's switches */
	jsr	VIEW_LEDS
	addq.l	#4, %sp
	jmp	KEY_TAKEN			/* the press taken, nothing opened */
7:	jmp	BROWSER				/* the stock answer: the browser at once */
8:	jmp	MACH_SITE			/* no trig held: on, as the stock code */

/* -> d0 1 when the selected track's machine declared a switch or a shortcut on a knob, else 0; since 0.6, 1 on every
 * track in a build with Transpose (sc_data +0x1c, bit 0). */
sc_level:
	lea	sc_data, %a0
	btst	#0, EVERY(%a0)
	bne.s	2f
	bsr.w	sc_selected
	bsr.w	sc_track			/* d1 its presses, d0 its index in the table or -1 */
	tst.l	%d1
	bne.s	2f
	tst.l	%d0
	bmi.s	1f
	lsl.l	#2, %d0
	mulu.w	#ENTRY, %d0
	lea	sc_data, %a0
	lea	ENTRIES(%a0,%d0.l), %a0		/* its four shortcuts */
	moveq	#3, %d1
3:	tst.l	(%a0)
	bne.s	2f
	lea	ENTRY(%a0), %a0
	subq.l	#1, %d1
	bpl.s	3b
1:	moveq	#0, %d0
	rts
2:	moveq	#1, %d0
	rts

/* a2 MainScreenView -> d0 1 when the MACHINES list is among its controller's views, else 0. */
sc_open:
	move.l	CONTROLLER_AT(%a2), %d0
	beq.s	3f
	movea.l	%d0, %a0
	lea	VIEWS_AT(%a0), %a1		/* the list's head node */
	movea.l	(%a1), %a0
1:	cmpa.l	%a1, %a0
	beq.s	3f
	move.l	8(%a0), %d0			/* the node's view */
	beq.s	2f
	movea.l	%d0, %a1
	move.l	(%a1), %d0			/* its vtable */
	cmpi.l	#MACHINES_VT, %d0
	beq.s	4f
	movea.l	CONTROLLER_AT(%a2), %a1
	lea	VIEWS_AT(%a1), %a1
2:	movea.l	(%a0), %a0
	bra.s	1b
3:	moveq	#0, %d0
	rts
4:	moveq	#1, %d0
	rts

/* The pattern's p-lock rows (see the head of this file). The composer writes jmp sc_conv over 0x4005aa34; on entry
 * d0 is the index, d1 the track (0..5), d2 the function's own, pushed at its start; its end (0x4005aa50) pops d2 and
 * returns d0, the k. */
	.section .text.sc_conv, "ax"
	.p2align 2
sc_conv:
	moveq	#18, %d2
	cmp.l	%d0, %d2
	beq.s	3f
	moveq	#23, %d2
	cmp.l	%d0, %d2
	bcc.s	1f
	moveq	#32, %d2
	cmp.l	%d0, %d2
	bcs.s	2f
	subq.l	#1, %d0				/* 24..32: k 23..31 */
	jmp	0x4005aa50
1:	jmp	0x4005aa46			/* 0..23: the stock table */
2:	jmp	0x4005aa3a			/* beyond: 0, as before */
3:	moveq	#32, %d0			/* 18: k 32, the switches */
	jmp	0x4005aa50

/* k -> the index of its p-lock row, in place of 0x4010ee4c: k 0..22 as the OS (index 18 unused), 23..31 -> 24..32,
 * 32 -> 18. */
	.section .rodata.sc_ptab, "a"
	.p2align 2
sc_ptab:
	.long	0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22, 23
	.long	24, 25, 26, 27, 28, 29, 30, 31, 32, 18
