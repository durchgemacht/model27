/* EQ's frame loops for the ColdFire (MCF5441x, EMAC), see eq.c: biquads in direct form I over the block's 32 frames
   in place. eq.c holds the same arithmetic as C for the host; the two agree bit for bit by construction (each product
   floored to 2^-39, a band's sum read floored to Q31 and saturated, then doubled with saturation).

   A band's coefficients (eq.c): b2 b0 b1 a1 a2, over 2^shift in Q31; its states: x1 x2 y1 y2, the last two frames of
   its input and of its output. Per frame: acc = b2 x2 + b0 x + b1 x1 - a1 y1 - a2 y2, which is y / 2^shift, read and
   doubled shift times by add.l, an overflow giving full scale with the sign it had: a boost clips, it does not wrap.
   Frames come in turns with the states' roles turned round, so that nothing is moved: x_n goes into the register of
   x2 once b2 x2 is in the accumulator, y_n into the one of y2 once a2 y2 is; four frames a turn of the loop (since
   0.3, two before). The frames are macros (FRAME1, FRAME3), the loops' variants by the doublings (LOOP1, LOOP3).
   MACSR is 0xa0 (fractional, saturating) as the filter slot calls a Track FX. Both keep d2-d7/a2-a6 and MACSR and
   leave the accumulators they use at zero. */

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
	mac.l	%a2, \xo, %acc0			/* b2 x2 */
	move.l	(%a0), \xo			/* x */
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
   the older then the newer of each. The coefficients come with the products, each product loading the next one
   from (a1)+ into ca and cb in turn: ca holds Low's b2 at the frame's start, cb at its end. reset: a1 back to c (a2)
   before the last product, which then loads Low's b2 from the start. hd: High's doublings. */
	.macro	FRAME3 x2, x1, s1o, s1n, s2o, s2n, s3o, s3n, ca, cb, reset, hd
	mac.l	\ca, \x2, (%a1)+, \cb, %acc0	/* Low: b2 x2, loads b0 */
	move.l	(%a0), \x2			/* x */
	mac.l	\cb, \x2, (%a1)+, \ca, %acc0	/* + b0 x */
	mac.l	\ca, \x1, (%a1)+, \cb, %acc0	/* + b1 x1 */
	msac.l	\cb, \s1n, (%a1)+, \ca, %acc0	/* - a1 y1 */
	msac.l	\ca, \s1o, (%a1)+, \cb, %acc0	/* - a2 y2 */
	mac.l	\cb, \s1o, (%a1)+, \ca, %acc1	/* Mid: b2 x2, before Low's y overwrites it */
	movclr.l %acc0, \s1o			/* Low's y / 2 */
	DOUBLE	\s1o
	mac.l	\ca, \s1o, (%a1)+, \cb, %acc1	/* + b0 x */
	mac.l	\cb, \s1n, (%a1)+, \ca, %acc1	/* + b1 x1 */
	msac.l	\ca, \s2n, (%a1)+, \cb, %acc1	/* - a1 y1 */
	msac.l	\cb, \s2o, (%a1)+, \ca, %acc1	/* - a2 y2 */
	mac.l	\ca, \s2o, (%a1)+, \cb, %acc2	/* High: b2 x2 */
	movclr.l %acc1, \s2o			/* Mid's y / 2 */
	DOUBLE	\s2o
	mac.l	\cb, \s2o, (%a1)+, \ca, %acc2	/* + b0 x */
	mac.l	\ca, \s2n, (%a1)+, \cb, %acc2	/* + b1 x1 */
	msac.l	\cb, \s3n, (%a1)+, \ca, %acc2	/* - a1 y1 */
	.if	\reset
	movea.l	%a2, %a1			/* back to c */
	.endif
	msac.l	\ca, \s3o, (%a1)+, \cb, %acc2	/* - a2 y2, loads the next frame's Low b2 */
	movclr.l %acc2, \s3o			/* High's y / 2^shift */
	DOUBLE	\s3o
	.if	\hd == 2
	DOUBLE	\s3o
	.endif
	move.l	\s3o, (%a0)+
	.endm

/* Four frames of the three bands: every other one with the pairs' and a3/a4's roles turned round. */
	.macro	LOOP3 hd
1:	FRAME3	%d1, %d0, %d3, %d2, %d5, %d4, %d7, %d6, %a3, %a4, 1, \hd
	FRAME3	%d0, %d1, %d2, %d3, %d4, %d5, %d6, %d7, %a4, %a3, 1, \hd
	FRAME3	%d1, %d0, %d3, %d2, %d5, %d4, %d7, %d6, %a3, %a4, 1, \hd
	FRAME3	%d0, %d1, %d2, %d3, %d4, %d5, %d6, %d7, %a4, %a3, 1, \hd
	cmpa.l	%a5, %a0
	bne	1b
	.endm

/* void eq_frames3(const int32_t *c, int32_t (*s)[4], int32_t *block, uint32_t hshift): Low (over 2), Mid (over 2) and
   High (over 2^hshift), frame by frame. c: the 15 coefficients in the order of the products (Low's b2 b0 b1 a1 a2,
   Mid's, High's). The states s are each band's x1 x2 y1 y2 (eq.c), a band's x being the band ahead's y: read
   from Low's x and y and the others' y, written back to all of them. a0 the block, a1 the pointer, a2 c, a5 the
   block's end. */
	.globl	eq_frames3
eq_frames3:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	52(%sp), %a1
	movem.l	(%a1), %d0-%d3			/* Low's x1 x2 y1 y2 */
	movem.l	24(%a1), %d4-%d5		/* Mid's y1 y2 */
	movem.l	40(%a1), %d6-%d7		/* High's y1 y2 */
	movea.l	56(%sp), %a0			/* block */
	lea	128(%a0), %a5			/* its end */
	movea.l	48(%sp), %a2			/* c */
	movea.l	%a2, %a1
	movea.l	(%a1)+, %a3			/* Low's b2 */
	move.l	#0, %acc0
	move.l	#0, %acc1
	move.l	#0, %acc2
	movea.l	60(%sp), %a6			/* hshift */
	cmpa.l	#1, %a6
	bne	2f
	LOOP3	1
	bra	3f
2:	LOOP3	2
3:	movea.l	52(%sp), %a1			/* after an even count of frames, each pair in its own registers */
	movem.l	%d0-%d3, (%a1)			/* Low: x, y */
	movem.l	%d2-%d5, 16(%a1)		/* Mid: Low's y, its own */
	movem.l	%d4-%d7, 32(%a1)		/* High: Mid's y, its own */
	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts
