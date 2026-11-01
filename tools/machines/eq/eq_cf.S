/* EQ's frame loops for the ColdFire (MCF5441x, EMAC), see eq.c: biquads in direct form I over the block's 32 frames
   in place. eq.c holds the same arithmetic as C for the host; the two agree bit for bit by construction (each product
   floored to 2^-39, a band's sum read floored to Q31 and saturated, then doubled with saturation).

   A band's coefficients (eq.c): b2 b0 b1 a1 a2, over 2^shift in Q31; its states: x1 x2 y1 y2, the last two frames of
   its input and of its output. Per frame: acc = b2 x2 + b0 x + b1 x1 - a1 y1 - a2 y2, which is y / 2^shift, read and
   doubled shift times by add.l, an overflow giving full scale with the sign it had: a boost clips, it does not wrap.
   Two frames a turn, the second with the states' roles turned round, so that nothing is moved: x_n goes into the
   register of x2 once b2 x2 is in the accumulator, y_n into the one of y2 once a2 y2 is.
   MACSR is 0xa0 (fractional, saturating) as the filter slot calls a Track FX. Both keep d2-d7/a2-a6 and MACSR and
   leave the accumulators they use at zero. */

	.section .text.eq_frames,"ax"	/* a section of its own, like -ffunction-sections (Level B builders keep file order) */
	.p2align 2

/* void eq_frames(const int32_t *c, int32_t *s, int32_t *block, uint32_t shift): one band, shift 1 or 2. The
   coefficients in a2-a6 (b2 b0 b1 a1 a2), the states in d1-d4 (x1 x2 y1 y2). */
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
	bne	10f
	moveq	#16, %d0			/* two frames a turn */

/* over 2: one doubling */
1:	mac.l	%a2, %d2, %acc0			/* b2 x2 */
	move.l	(%a0), %d2			/* x */
	mac.l	%a3, %d2, %acc0			/* + b0 x */
	mac.l	%a4, %d1, %acc0			/* + b1 x1 */
	msac.l	%a5, %d3, %acc0			/* - a1 y1 */
	msac.l	%a6, %d4, %acc0			/* - a2 y2 */
	movclr.l %acc0, %d4			/* y / 2 */
	add.l	%d4, %d4			/* y */
	bvs	20f
2:	move.l	%d4, (%a0)+
	mac.l	%a2, %d1, %acc0			/* the next frame: x1 is in d2, x2 in d1, y1 in d4, y2 in d3 */
	move.l	(%a0), %d1
	mac.l	%a3, %d1, %acc0
	mac.l	%a4, %d2, %acc0
	msac.l	%a5, %d4, %acc0
	msac.l	%a6, %d3, %acc0
	movclr.l %acc0, %d3
	add.l	%d3, %d3
	bvs	30f
3:	move.l	%d3, (%a0)+
	subq.l	#1, %d0
	bne	1b
	bra	9f

/* over 4: two doublings */
10:	moveq	#16, %d0
4:	mac.l	%a2, %d2, %acc0
	move.l	(%a0), %d2
	mac.l	%a3, %d2, %acc0
	mac.l	%a4, %d1, %acc0
	msac.l	%a5, %d3, %acc0
	msac.l	%a6, %d4, %acc0
	movclr.l %acc0, %d4			/* y / 4 */
	add.l	%d4, %d4
	bvs	40f
5:	add.l	%d4, %d4
	bvs	50f
6:	move.l	%d4, (%a0)+
	mac.l	%a2, %d1, %acc0
	move.l	(%a0), %d1
	mac.l	%a3, %d1, %acc0
	mac.l	%a4, %d2, %acc0
	msac.l	%a5, %d4, %acc0
	msac.l	%a6, %d3, %acc0
	movclr.l %acc0, %d3
	add.l	%d3, %d3
	bvs	60f
7:	add.l	%d3, %d3
	bvs	70f
8:	move.l	%d3, (%a0)+
	subq.l	#1, %d0
	bne	4b

9:	movea.l	40(%sp), %a1
	movem.l	%d1-%d4, (%a1)			/* x1 x2 y1 y2: after an even count of frames, in their own registers */
	movem.l	(%sp), %d2-%d4/%a2-%a6
	lea	32(%sp), %sp
	rts

/* An overflow of a doubling: the wrapped result has the other sign (N), full scale with the right one. */
20:	bmi	21f
	move.l	#0x80000000, %d4
	bra	2b
21:	move.l	#0x7fffffff, %d4
	bra	2b
30:	bmi	31f
	move.l	#0x80000000, %d3
	bra	3b
31:	move.l	#0x7fffffff, %d3
	bra	3b
40:	bmi	41f
	move.l	#0x80000000, %d4
	bra	5b
41:	move.l	#0x7fffffff, %d4
	bra	5b
50:	bmi	51f
	move.l	#0x80000000, %d4
	bra	6b
51:	move.l	#0x7fffffff, %d4
	bra	6b
60:	bmi	61f
	move.l	#0x80000000, %d3
	bra	7b
61:	move.l	#0x7fffffff, %d3
	bra	7b
70:	bmi	71f
	move.l	#0x80000000, %d3
	bra	8b
71:	move.l	#0x7fffffff, %d3
	bra	8b

/* void eq_frames3(const int32_t (*c)[5], int32_t (*s)[4], int32_t *block): Low (over 2), Mid (over 2) and High (over 4), frame
   by frame, each band in an accumulator of its own: acc0, acc1, acc2. The states in d0-d7: the input's x1 x2 (d0 d1),
   Low's output (d2 d3, Mid's input), Mid's (d4 d5, High's input), High's (d6 d7, the output). The 15 coefficients
   (c, in the order of the products: Low's b2 b0 b1 a1 a2, Mid's, High's) come one after the other with the products,
   each product loading the next one (a MAC with load), into a3 and a4 in turn; the pointer goes back to c before the
   frame's last product, which loads the next frame's first. A band's b2 x2 goes into its accumulator before the band
   ahead writes its newest frame over x2. a0 the block, a1 the pointer, a2 c, a5 the block's end. The states s are
   each band's x1 x2 y1 y2 (eq.c), a band's x being the band ahead's y: read from Low's x and y and the others' y,
   written back to all of them. */
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

11:	mac.l	%a3, %d1, (%a1)+, %a4, %acc0	/* Low: b2 x2, loads b0 */
	move.l	(%a0), %d1			/* x */
	mac.l	%a4, %d1, (%a1)+, %a3, %acc0	/* + b0 x */
	mac.l	%a3, %d0, (%a1)+, %a4, %acc0	/* + b1 x1 */
	msac.l	%a4, %d2, (%a1)+, %a3, %acc0	/* - a1 y1 */
	msac.l	%a3, %d3, (%a1)+, %a4, %acc0	/* - a2 y2 */
	mac.l	%a4, %d3, (%a1)+, %a3, %acc1	/* Mid: b2 x2, before Low's y overwrites it */
	movclr.l %acc0, %d3			/* Low's y / 2 */
	add.l	%d3, %d3
	bvs	80f
12:	mac.l	%a3, %d3, (%a1)+, %a4, %acc1	/* + b0 x */
	mac.l	%a4, %d2, (%a1)+, %a3, %acc1	/* + b1 x1 */
	msac.l	%a3, %d4, (%a1)+, %a4, %acc1	/* - a1 y1 */
	msac.l	%a4, %d5, (%a1)+, %a3, %acc1	/* - a2 y2 */
	mac.l	%a3, %d5, (%a1)+, %a4, %acc2	/* High: b2 x2 */
	movclr.l %acc1, %d5			/* Mid's y / 2 */
	add.l	%d5, %d5
	bvs	81f
13:	mac.l	%a4, %d5, (%a1)+, %a3, %acc2	/* + b0 x */
	mac.l	%a3, %d4, (%a1)+, %a4, %acc2	/* + b1 x1 */
	msac.l	%a4, %d6, (%a1)+, %a3, %acc2	/* - a1 y1 */
	movea.l	%a2, %a1			/* back to c */
	msac.l	%a3, %d7, (%a1)+, %a4, %acc2	/* - a2 y2, loads the next frame's Low b2 */
	movclr.l %acc2, %d7			/* High's y / 4 */
	add.l	%d7, %d7
	bvs	82f
14:	add.l	%d7, %d7
	bvs	83f
15:	move.l	%d7, (%a0)+

	mac.l	%a4, %d0, (%a1)+, %a3, %acc0	/* the next frame: the roles of each pair, and of a3 and a4, turned */
	move.l	(%a0), %d0
	mac.l	%a3, %d0, (%a1)+, %a4, %acc0
	mac.l	%a4, %d1, (%a1)+, %a3, %acc0
	msac.l	%a3, %d3, (%a1)+, %a4, %acc0
	msac.l	%a4, %d2, (%a1)+, %a3, %acc0
	mac.l	%a3, %d2, (%a1)+, %a4, %acc1
	movclr.l %acc0, %d2
	add.l	%d2, %d2
	bvs	84f
16:	mac.l	%a4, %d2, (%a1)+, %a3, %acc1
	mac.l	%a3, %d3, (%a1)+, %a4, %acc1
	msac.l	%a4, %d5, (%a1)+, %a3, %acc1
	msac.l	%a3, %d4, (%a1)+, %a4, %acc1
	mac.l	%a4, %d4, (%a1)+, %a3, %acc2
	movclr.l %acc1, %d4
	add.l	%d4, %d4
	bvs	85f
17:	mac.l	%a3, %d4, (%a1)+, %a4, %acc2
	mac.l	%a4, %d5, (%a1)+, %a3, %acc2
	msac.l	%a3, %d7, (%a1)+, %a4, %acc2
	movea.l	%a2, %a1
	msac.l	%a4, %d6, (%a1)+, %a3, %acc2
	movclr.l %acc2, %d6
	add.l	%d6, %d6
	bvs	86f
18:	add.l	%d6, %d6
	bvs	87f
19:	move.l	%d6, (%a0)+
	cmpa.l	%a5, %a0
	bne	11b

	movea.l	52(%sp), %a1			/* after an even count of frames, each pair in its own registers */
	movem.l	%d0-%d3, (%a1)			/* Low: x, y */
	movem.l	%d2-%d5, 16(%a1)		/* Mid: Low's y, its own */
	movem.l	%d4-%d7, 32(%a1)		/* High: Mid's y, its own */
	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts

80:	bmi	90f
	move.l	#0x80000000, %d3
	bra	12b
90:	move.l	#0x7fffffff, %d3
	bra	12b
81:	bmi	91f
	move.l	#0x80000000, %d5
	bra	13b
91:	move.l	#0x7fffffff, %d5
	bra	13b
82:	bmi	92f
	move.l	#0x80000000, %d7
	bra	14b
92:	move.l	#0x7fffffff, %d7
	bra	14b
83:	bmi	93f
	move.l	#0x80000000, %d7
	bra	15b
93:	move.l	#0x7fffffff, %d7
	bra	15b
84:	bmi	94f
	move.l	#0x80000000, %d2
	bra	16b
94:	move.l	#0x7fffffff, %d2
	bra	16b
85:	bmi	95f
	move.l	#0x80000000, %d4
	bra	17b
95:	move.l	#0x7fffffff, %d4
	bra	17b
86:	bmi	96f
	move.l	#0x80000000, %d6
	bra	18b
96:	move.l	#0x7fffffff, %d6
	bra	18b
87:	bmi	97f
	move.l	#0x80000000, %d6
	bra	19b
97:	move.l	#0x7fffffff, %d6
	bra	19b
