/* EQ on the ColdFire (MCF5441x, EMAC), see eq.c: eq_process, the block (since 0.6; the frame loops alone before), with
   the shelves' and the bell's coefficients and the three bands' loop, and eq_frames for a band alone: biquads in
   direct form I over the block's 32 frames in place. eq.c holds the same as C for the host; the two agree bit for bit
   by construction (the same integer steps; each product floored to 2^-39, a band's sum read floored to Q31 and
   saturated, then doubled with saturation).

   A band's coefficients (eq.c): b2 b0 b1 a1 a2, over 2^shift in Q31; its states: x1 x2 y1 y2, the last two frames of
   its input and of its output. Per frame: acc = b2 x2 + b0 x + b1 x1 - a1 y1 - a2 y2, which is y / 2^shift, read and
   doubled shift times by add.l, an overflow giving full scale with the sign it had: a boost clips, it does not wrap.
   Frames come in turns with the states' roles turned round, so that nothing is moved: x_n goes into the register of
   x2 once b2 x2 is in the accumulator, y_n into the one of y2 once a2 y2 is; four frames a turn of the loop (since
   0.3, two before). The frames are macros (FRAME1, FRAME3), the loops' variants by the doublings (LOOP1, LOOP3).
   Since 0.6 the frame's input comes in with the first product (MAC with load into the register it reads, as Reso's
   loop does) and the three bands' coefficients with the products from their fixed places, so that no pointer is set
   back: 25 instructions a frame for the three bands, 9 for one (27 and 10 before). MACSR is 0xa0 (fractional,
   saturating) as the filter slot calls a Track FX. Both keep d2-d7/a2-a6 and MACSR and leave the accumulators they
   use at zero. */

	.section .text.eq_frames,"ax"	/* a section of its own, like -ffunction-sections (Level B builders keep file order) */
	.p2align 2

/* y doubled, saturated: an overflow (V) gives full scale with the sign the value had, which the wrapped result has
   the other way round (N). The fix sits apart (subsection 1), so that the usual path is a branch not taken. */
	.macro	DOUBLE y
	add.l	\y, \y
	bvs	8f
9:
	.subsection 1
8:	bmi	7f
	move.l	#0x80000000, \y
	bra	9b
7:	move.l	#0x7fffffff, \y
	bra	9b
	.subsection 0
	.endm

/* One frame of one band (coefficients in a2-a6: b2 b0 b1 a1 a2): xo holds x2 and takes x, xn holds x1; yo holds y2
   and takes y, yn holds y1; sh doublings. */
	.macro	FRAME1 xo, xn, yo, yn, sh
	mac.l	%a2, \xo, (%a0), \xo, %acc0	/* b2 x2; x, loaded after the product read x2 */
	mac.l	%a3, \xo, %acc0			/* + b0 x */
	mac.l	%a4, \xn, %acc0			/* + b1 x1 */
	msac.l	%a5, \yn, %acc0			/* - a1 y1 */
	msac.l	%a6, \yo, %acc0			/* - a2 y2 */
	movclr.l %acc0, \yo			/* y / 2^shift */
	DOUBLE	\yo
	.if	\sh == 2
	DOUBLE	\yo
	.endif
	move.l	\yo, (%a0)+
	.endm

/* Four frames of one band, the states back in their registers after them. */
	.macro	LOOP1 sh
	moveq	#8, %d0
1:	FRAME1	%d2, %d1, %d4, %d3, \sh
	FRAME1	%d1, %d2, %d3, %d4, \sh
	FRAME1	%d2, %d1, %d4, %d3, \sh
	FRAME1	%d1, %d2, %d3, %d4, \sh
	subq.l	#1, %d0
	bne	1b
	.endm

/* void eq_frames(const int32_t *c, int32_t *s, int32_t *block, uint32_t shift): one band, shift 1 or 2. The
   coefficients in a2-a6, the states in d1-d4 (x1 x2 y1 y2). */
	.globl	eq_frames
eq_frames:
	lea	-32(%sp), %sp
	movem.l	%d2-%d4/%a2-%a6, (%sp)
	movea.l	36(%sp), %a1
	movem.l	(%a1), %a2-%a6			/* b2 b0 b1 a1 a2 */
	movea.l	40(%sp), %a1
	movem.l	(%a1), %d1-%d4			/* x1 x2 y1 y2 */
	movea.l	44(%sp), %a0			/* block */
	move.l	#0, %acc0
	move.l	48(%sp), %d0			/* shift */
	subq.l	#1, %d0
	bne	2f
	LOOP1	1
	bra	3f
2:	LOOP1	2
3:	movea.l	40(%sp), %a1
	movem.l	%d1-%d4, (%a1)			/* x1 x2 y1 y2: after a count of frames divisible by 4, in their registers */
	movem.l	(%sp), %d2-%d4/%a2-%a6
	lea	32(%sp), %sp
	rts

/* One frame of the three bands, each in an accumulator of its own (acc0 Low, acc1 Mid, acc2 High). The states:
   x2 x1 the input's, s1o s1n Low's output (Mid's input), s2o s2n Mid's (High's input), s3o s3n High's (the output),
   the older then the newer of each. The coefficients come with the products from their places in c (a1, fixed: since
   0.6, no pointer to set back) into ca and cb in turn; Low's b0 stays in a2, so that the first product loads the
   frame's input instead. ca holds Low's b2 at the frame's start and again at its end. hd: High's doublings. */
	.macro	FRAME3 x2, x1, s1o, s1n, s2o, s2n, s3o, s3n, ca, cb, hd
	mac.l	\ca, \x2, (%a0), \x2, %acc0	/* Low: b2 x2; x */
	mac.l	%a2, \x2, 8(%a1), \cb, %acc0	/* + b0 x; b1 */
	mac.l	\cb, \x1, 12(%a1), \ca, %acc0	/* + b1 x1; a1 */
	msac.l	\ca, \s1n, 16(%a1), \cb, %acc0	/* - a1 y1; a2 */
	msac.l	\cb, \s1o, 20(%a1), \ca, %acc0	/* - a2 y2; Mid's b2 */
	mac.l	\ca, \s1o, 24(%a1), \cb, %acc1	/* Mid: b2 x2, before Low's y overwrites it; b0 */
	movclr.l %acc0, \s1o			/* Low's y / 2 */
	DOUBLE	\s1o
	mac.l	\cb, \s1o, 28(%a1), \ca, %acc1	/* + b0 x; b1 */
	mac.l	\ca, \s1n, 32(%a1), \cb, %acc1	/* + b1 x1; a1 */
	msac.l	\cb, \s2n, 36(%a1), \ca, %acc1	/* - a1 y1; a2 */
	msac.l	\ca, \s2o, 40(%a1), \cb, %acc1	/* - a2 y2; High's b2 */
	mac.l	\cb, \s2o, 44(%a1), \ca, %acc2	/* High: b2 x2; b0 */
	movclr.l %acc1, \s2o			/* Mid's y / 2 */
	DOUBLE	\s2o
	mac.l	\ca, \s2o, 48(%a1), \cb, %acc2	/* + b0 x; b1 */
	mac.l	\cb, \s2n, 52(%a1), \ca, %acc2	/* + b1 x1; a1 */
	msac.l	\ca, \s3n, 56(%a1), \cb, %acc2	/* - a1 y1; a2 */
	msac.l	\cb, \s3o, (%a1), \ca, %acc2	/* - a2 y2; the next frame's Low b2 */
	movclr.l %acc2, \s3o			/* High's y / 2^shift */
	DOUBLE	\s3o
	.if	\hd == 2
	DOUBLE	\s3o
	.endif
	move.l	\s3o, (%a0)+
	.endm

/* Four frames of the three bands: every other one with the pairs' roles turned round; end: the block's end. */
	.macro	LOOP3 hd, end
1:	FRAME3	%d1, %d0, %d3, %d2, %d5, %d4, %d7, %d6, %a3, %a4, \hd
	FRAME3	%d0, %d1, %d2, %d3, %d4, %d5, %d6, %d7, %a3, %a4, \hd
	FRAME3	%d1, %d0, %d3, %d2, %d5, %d4, %d7, %d6, %a3, %a4, \hd
	FRAME3	%d0, %d1, %d2, %d3, %d4, %d5, %d6, %d7, %a3, %a4, \hd
	cmpa.l	\end, %a0
	bne	1b
	.endm


/* void eq_process(int32_t *block, const int16_t *words, uint32_t track, uint32_t triggered): eq.c's, in assembly since
   0.6: the flat test, the states' start after a reset, the silence test, the words compared as they come, the
   coefficients of the bands that moved (eq_shelf, eq_bell below: the same integer steps as eq.c's shelf and bell),
   the three bands' loop inline (LOOP3), a band alone through eq_frames. The state 128 bytes a track (eq.c). Keeps
   d2-d7/a2-a6 and MACSR; leaves the accumulators at zero. */
#define TRACKS 6
#define CENTRE 0x4000
#define TOP 0x7f00
#define RING 0x4000
#define S_C 48
#define S_W0 108			/* Low's word */
#define S_W1 112			/* High's */
#define S_W2 116			/* Mid's gain */
#define S_W3 120			/* Mid's centre */
#define S_SET 124
#define S_HS 125
/* D clamped to 0 .. TOP (eq.c's clamp) */
#define CLAMP(D, L) \
	cmpi.l	#TOP, D			; \
	bls.s	L			; \
	tst.l	D			; \
	bmi.s	L##z			; \
	move.l	#TOP, D			; \
	bra.s	L			; \
L##z:	moveq	#0, D			; \
L:
/* the state at OFF(a5) under RING either way, else the block is played (d1 RING, d2 2 RING) */
#define QUIETB(OFF) \
	move.l	OFF(%a5), %d0		; \
	add.l	%d1, %d0		; \
	cmp.l	%d2, %d0		; \
	bcc	.Lplay
/* a band's states follow f1 (d0) and f2 (d1): x1 x2 y1 y2 = f1 f2 f1 f2 */
#define FOLLOW(R, OFF) \
	move.l	%d0, OFF(R)		; \
	move.l	%d1, OFF+4(R)		; \
	move.l	%d0, OFF+8(R)		; \
	move.l	%d1, OFF+12(R)
/* the three bands' setup (eq_frames3's before 0.6): the states into d0-d7, the block a0, its end a6, c a1, Low's b0 a2 and b2 a3 */
#define SETUP3 \
	movem.l	(%a5), %d0-%d3		; \
	movem.l	24(%a5), %d4-%d5	; \
	movem.l	40(%a5), %d6-%d7	; \
	movea.l	%a4, %a0		; \
	lea	128(%a0), %a6		; \
	lea	S_C(%a5), %a1		; \
	movea.l	4(%a1), %a2		; \
	movea.l	(%a1), %a3		; \
	move.l	#0, %acc0		; \
	move.l	#0, %acc1		; \
	move.l	#0, %acc2

	.section .text.eq_proc,"ax"
	.p2align 2
	.globl	eq_process
eq_process:
	move.l	12(%sp),%d0			/* track */
	moveq	#TRACKS-1,%d1
	cmp.l	%d0,%d1
	bcs	.Lret
	lsl.l	#7,%d0
	lea	eq_state,%a0
	adda.l	%d0,%a0				/* t */
	movea.l	8(%sp),%a1			/* words */
	moveq	#0,%d0				/* the bands that are on: Low 1, Mid 2, High 4 */
	move.w	4(%a1),%d1
	cmpi.w	#CENTRE,%d1
	beq.s	1f
	moveq	#1,%d0
1:	move.w	2(%a1),%d1
	cmpi.w	#CENTRE,%d1
	beq.s	1f
	addq.l	#2,%d0
1:	move.w	6(%a1),%d1
	cmpi.w	#CENTRE,%d1
	beq.s	1f
	addq.l	#4,%d0
1:	tst.l	%d0
	beq	.Lflat
	lea	-44(%sp),%sp
	movem.l	%d2-%d7/%a2-%a6,(%sp)
	movea.l	%a0,%a5				/* t */
	movea.l	%a1,%a6				/* words */
	move.l	%d0,%d7				/* on */
	movea.l	48(%sp),%a4			/* block */
	tst.b	S_SET(%a5)
	bne.s	2f
	move.l	(%a4),%d0			/* after a reset: the states start at the first frame */
	move.l	%d0,%d1
	move.l	%d0,%d2
	move.l	%d0,%d3
	movem.l	%d0-%d3,(%a5)
	movem.l	%d0-%d3,16(%a5)
	movem.l	%d0-%d3,32(%a5)
	moveq	#1,%d0
	move.b	%d0,S_SET(%a5)
2:	move.l	#RING,%d1			/* quiet states: is the block silent? */
	move.l	#2*RING,%d2
	QUIETB(0)				/* Low's x1 */
	QUIETB(40)				/* High's y1 */
	QUIETB(4)				/* then every state: Low's x2 */
	QUIETB(8)
	QUIETB(12)
	QUIETB(24)
	QUIETB(28)
	QUIETB(44)
	movea.l	%a4,%a0
	move.l	(%a0)+,%d0
	bne	.Lplay
	.rept	31
	or.l	(%a0)+,%d0
	.endr
	bne	.Lplay
	moveq	#0,%d1				/* silent: left silent, the states cleared */
	FOLLOW(%a5, 0)
	FOLLOW(%a5, 16)
	FOLLOW(%a5, 32)
	bra	.Lout
.Lplay:						/* the coefficients of the bands that are on, when their words moved */
	btst	#0,%d7
	beq.s	3f
	mvs.w	4(%a6),%d0			/* Low */
	cmp.l	S_W0(%a5),%d0
	beq.s	3f
	move.l	%d0,S_W0(%a5)
	CLAMP(%d0, .Lc1)
	movea.l	eq_tab,%a0			/* EQ_LOW */
	lea	S_C(%a5),%a1
	move.l	#0x40000000,%d1
	suba.l	%a2,%a2
	suba.l	%a3,%a3
	jsr	eq_shelf
3:	btst	#1,%d7
	beq.s	4f
	mvs.w	2(%a6),%d0			/* Mid: its gain, its centre */
	mvs.w	(%a6),%d1
	cmp.l	S_W2(%a5),%d0
	bne.s	5f
	cmp.l	S_W3(%a5),%d1
	beq.s	4f
5:	move.l	%d0,S_W2(%a5)
	move.l	%d1,S_W3(%a5)
	CLAMP(%d0, .Lc2)
	CLAMP(%d1, .Lc3)
	lea	S_C+20(%a5),%a1
	jsr	eq_bell
4:	btst	#2,%d7
	beq.s	6f
	mvs.w	6(%a6),%d0			/* High */
	cmp.l	S_W1(%a5),%d0
	beq.s	6f
	move.l	%d0,S_W1(%a5)
	CLAMP(%d0, .Lc4)
	moveq	#2,%d1				/* over 4 from EQ_HIGH_FIT, else over 2 */
	suba.l	%a3,%a3
	cmp.l	eq_high_fit,%d0
	bge.s	7f
	moveq	#1,%d1
	movea.w	#1,%a3				/* every coefficient doubled */
7:	move.b	%d1,S_HS(%a5)
	movea.l	eq_tab+4,%a0			/* EQ_HIGH */
	lea	S_C+40(%a5),%a1
	move.l	#0x20000000,%d1
	movea.w	#1,%a2
	jsr	eq_shelf
6:	moveq	#7,%d0
	cmp.l	%d0,%d7
	bne	.Lbands
	moveq	#1,%d0				/* every band: one loop */
	cmp.b	S_HS(%a5),%d0
	bne	.Lx4
	SETUP3
	LOOP3	1, %a6
	bra	.Lx3
.Lx4:	SETUP3
	LOOP3	2, %a6
.Lx3:	movem.l	%d0-%d3,(%a5)			/* Low: x, y */
	movem.l	%d2-%d5,16(%a5)			/* Mid: Low's y, its own */
	movem.l	%d4-%d7,32(%a5)			/* High: Mid's y, its own */
	bra	.Lout
.Lbands:					/* each band that is on over the block; a flat one's output is its input */
	btst	#0,%d7
	beq.s	1f
	pea	1
	move.l	%a4,-(%sp)
	pea	(%a5)
	pea	S_C(%a5)
	jsr	eq_frames
	lea	16(%sp),%sp
	bra.s	2f
1:	move.l	124(%a4),%d0
	move.l	120(%a4),%d1
	FOLLOW(%a5, 0)
2:	btst	#1,%d7
	beq.s	1f
	pea	1
	move.l	%a4,-(%sp)
	pea	16(%a5)
	pea	S_C+20(%a5)
	jsr	eq_frames
	lea	16(%sp),%sp
	bra.s	2f
1:	move.l	124(%a4),%d0
	move.l	120(%a4),%d1
	FOLLOW(%a5, 16)
2:	btst	#2,%d7
	beq.s	1f
	mvz.b	S_HS(%a5),%d0
	move.l	%d0,-(%sp)
	move.l	%a4,-(%sp)
	pea	32(%a5)
	pea	S_C+40(%a5)
	jsr	eq_frames
	lea	16(%sp),%sp
	bra.s	.Lout
1:	move.l	124(%a4),%d0
	move.l	120(%a4),%d1
	FOLLOW(%a5, 32)
.Lout:
	movem.l	(%sp),%d2-%d7/%a2-%a6
	lea	44(%sp),%sp
.Lret:	rts
.Lflat:						/* flat: untouched, the states follow the input */
	movea.l	4(%sp),%a1
	move.l	124(%a1),%d0
	move.l	120(%a1),%d1
	FOLLOW(%a0, 0)
	FOLLOW(%a0, 16)
	FOLLOW(%a0, 32)
	moveq	#1,%d0
	move.b	%d0,S_SET(%a0)
	rts

/* a + ((b - a) >> 8) t (eq.c's lerp), a at OFF(a0), b at OFF + D(a0), t in T, into R */
#define LERPM(OFF, D, T, R) \
	move.l	OFF+D(%a0), R		; \
	sub.l	OFF(%a0), R		; \
	asr.l	#8, R			; \
	muls.l	T, R			; \
	add.l	OFF(%a0), R

/* eq_shelf: eq.c's shelf. a0 the table (EQ_LOW or EQ_HIGH: b0 b1 a1 a2 a row of 16 bytes), a1 c (b2 b0 b1 a1 a2 out),
   d0 the clamped word, d1 one, a2 0 (Low: b1 - a1) or not (High: a1 - b1), a3 not 0: every coefficient doubled.
   Changes d0-d6 and a0. */
	.section .text.eq_co,"ax"
	.p2align 2
eq_shelf:
	move.l	%d0,%d2
	lsr.l	#4,%d2
	andi.l	#0x7f0,%d2
	adda.l	%d2,%a0				/* the gain's row, the next one 16 on */
	mvz.b	%d0,%d0				/* t */
	LERPM(0, 16, %d0, %d2)			/* b0 */
	sub.l	%d2,%d1
	LERPM(4, 16, %d0, %d3)			/* b1 */
	LERPM(8, 16, %d0, %d4)			/* a1 */
	LERPM(12, 16, %d0, %d5)			/* a2 */
	add.l	%d5,%d1
	move.l	%d3,%d6
	sub.l	%d4,%d6				/* b1 - a1 */
	move.l	%a2,%d0
	beq.s	1f
	neg.l	%d6
1:	add.l	%d6,%d1				/* b2: one + (b1 - a1, or a1 - b1) + (a2 - b0) */
	move.l	%a3,%d0
	beq.s	2f
	add.l	%d1,%d1
	add.l	%d2,%d2
	add.l	%d3,%d3
	add.l	%d4,%d4
	add.l	%d5,%d5
2:	movem.l	%d1-%d5,(%a1)
	rts

/* eq_bell: eq.c's bell. a1 c (b2 b0 b1 a1 a2 out), d0 the clamped gain word g, d1 the clamped centre word f. EQ_MID: a
   row of 33 columns every 2^11 of g (396 bytes), a column of b0 a1 a2 every 2^10 of f (12 bytes). Changes d0-d6, a0. */
#define BILERP(OFF, R) \
	LERPM(OFF, 12, %d1, R)		; \
	LERPM(OFF + 396, 12, %d1, %d6)	; \
	sub.l	R, %d6			; \
	asr.l	#8, %d6			; \
	muls.l	%d0, %d6		; \
	add.l	%d6, R
eq_bell:
	move.l	%d0,%d2
	moveq	#11,%d3
	asr.l	%d3,%d2
	mulu.w	#396,%d2
	move.l	%d1,%d3
	moveq	#10,%d4
	asr.l	%d4,%d3
	mulu.w	#12,%d3
	add.l	%d3,%d2
	movea.l	eq_tab+8,%a0			/* EQ_MID */
	adda.l	%d2,%a0
	asr.l	#3,%d0
	mvz.b	%d0,%d0				/* gt */
	asr.l	#2,%d1
	mvz.b	%d1,%d1				/* ft */
	BILERP(0, %d2)				/* b0 */
	BILERP(4, %d3)				/* b1 = a1 */
	BILERP(8, %d4)				/* a2 */
	move.l	%d4,%d5
	sub.l	%d2,%d5
	addi.l	#0x40000000,%d5			/* b2 = 1 + a2 - b0 */
	move.l	%d5,(%a1)
	move.l	%d2,4(%a1)
	move.l	%d3,8(%a1)
	move.l	%d3,12(%a1)
	move.l	%d4,16(%a1)
	rts
