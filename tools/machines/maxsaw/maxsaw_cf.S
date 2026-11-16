/* Max Saw on the ColdFire (MCF5441x, EMAC): the block's two frame loops, see maxsaw.c (msaw_block), which holds
   the same as C for the host (MSAW_HOST), the proof's model. The two agree bit for bit by construction: the same
   products into the same sums in acc0, read once each (each product truncated to 2^-23 of an LSB, the sum floored to
   Q31 and saturated, MACSR 0xa0 as msaw_block set it), the same integer additions (wrapping).

       void msaw_saws(uint32_t *ph, const uint32_t *inc, int32_t *out, int32_t gc, int32_t gs, int32_t dgc, int32_t dgs)

   The seven sawtooths into out[0..31]: per frame gc += dgc, gs += dgs, acc0 += ph[i] x (i == 3 ? gc : gs) for the
   seven (the phase read as int32), ph[i] += inc[i], out[n] = acc0 (movclr.l). The phases in d0-d6 for the block,
   written back at its end. Two frames a pass, 20 instructions a frame.

       void msaw_sub(int32_t *sb, uint32_t *st, uint32_t sinc, const int32_t *cf)

   The Sub (notes/84 §13) into sb[0..31]: st = { sph, l1, l2 }, cf = { a1, a2, a3, gain }; per frame x = sph x gain
   (the phase read as int32), sph += sinc, then the 2-pole state-variable low-pass (TPT) as the high-pass below, its
   v2: sb[n] = v2. Two frames a pass, 18 instructions a frame.

       void msaw_hpf(int32_t *out, int32_t *st, const int32_t *cf, const int32_t *sb)

   The 2-pole state-variable high-pass (TPT) over out[0..31] in place: st = { s1, s2 }, cf = { a1, a2, a3, k - 1 };
   per frame v3 = x - s2, v1 = a1 s1 + a2 v3, v2 = s2 + (a2 s1 + a3 v3), s1 = 2 v1 - s1, s2 = 2 v2 - s2,
   y = x - v1 - (k - 1) v1 - v2, y += sb[n] when sb is not 0 (the Sub), and onto the bus: out[n] = y x 2, saturated
   (8.0 of Q27 full scale), as maxsaw_render does it on the host's model. Two frames a pass, 25 instructions a frame,
   26 with the Sub (the saturation's branch taken only past full scale).

   All three keep d2-d7/a2-a6 and MACSR, use acc0 and leave it empty.

   License: MIT (LICENSE next to this file). */

	.macro	SAW
	add.l	%a3,%d7			/* gc += dgc */
	adda.l	%a4,%a2			/* gs += dgs */
	mac.l	%d0,%a2,%acc0
	add.l	(%a5),%d0
	mac.l	%d1,%a2,%acc0
	add.l	(4,%a5),%d1
	mac.l	%d2,%a2,%acc0
	add.l	(8,%a5),%d2
	mac.l	%d3,%d7,%acc0		/* the centre, Szabo's osc 4 */
	add.l	(12,%a5),%d3
	mac.l	%d4,%a2,%acc0
	add.l	(16,%a5),%d4
	mac.l	%d5,%a2,%acc0
	add.l	(20,%a5),%d5
	mac.l	%d6,%a2,%acc0
	add.l	(24,%a5),%d6
	movclr.l %acc0,%a6
	move.l	%a6,(%a0)+
	.endm

	.section .text.msaw_saws,"ax"
	.globl	msaw_saws
msaw_saws:
	lea	-44(%sp),%sp
	movem.l	%d2-%d7/%a2-%a6,(%sp)
	move.l	48(%sp),%a6		/* ph */
	movem.l	(%a6),%d0-%d6
	move.l	52(%sp),%a5		/* inc */
	move.l	56(%sp),%a0		/* out */
	lea	128(%a0),%a1		/* the block's end */
	move.l	60(%sp),%d7		/* gc */
	move.l	64(%sp),%a2		/* gs */
	move.l	68(%sp),%a3		/* dgc */
	move.l	72(%sp),%a4		/* dgs */
1:	SAW
	SAW
	cmpa.l	%a1,%a0
	bne.s	1b
	move.l	48(%sp),%a6
	movem.l	%d0-%d6,(%a6)		/* the phases */
	movem.l	(%sp),%d2-%d7/%a2-%a6
	lea	44(%sp),%sp
	rts

	.macro	SUBF
	mac.l	%d7,%a4,%acc0		/* sph x gain */
	add.l	%a5,%d7			/* sph += sinc */
	movclr.l %acc0,%d1		/* x */
	sub.l	%d5,%d1			/* v3 = x - l2 */
	mac.l	%d6,%d4,%acc0		/* a1 l1 */
	mac.l	%a2,%d1,%acc0		/* a2 v3 */
	movclr.l %acc0,%d2		/* v1 */
	mac.l	%a2,%d4,%acc0		/* a2 l1 */
	mac.l	%a3,%d1,%acc0		/* a3 v3 */
	movclr.l %acc0,%d3
	add.l	%d5,%d3			/* v2 */
	neg.l	%d4
	add.l	%d2,%d4
	add.l	%d2,%d4			/* l1 = 2 v1 - l1 */
	neg.l	%d5
	add.l	%d3,%d5
	add.l	%d3,%d5			/* l2 = 2 v2 - l2 */
	move.l	%d3,(%a0)+		/* the low-pass's v2 */
	.endm

	.section .text.msaw_sub,"ax"
	.globl	msaw_sub
msaw_sub:
	lea	-40(%sp),%sp
	movem.l	%d2-%d7/%a2-%a5,(%sp)
	move.l	44(%sp),%a0		/* sb */
	lea	128(%a0),%a1		/* the block's end */
	move.l	48(%sp),%a5		/* st */
	move.l	(%a5),%d7		/* sph */
	move.l	(4,%a5),%d4		/* l1 */
	move.l	(8,%a5),%d5		/* l2 */
	move.l	56(%sp),%a5		/* cf */
	move.l	(%a5),%d6		/* a1 */
	move.l	(4,%a5),%a2		/* a2 */
	move.l	(8,%a5),%a3		/* a3 */
	move.l	(12,%a5),%a4		/* gain */
	move.l	52(%sp),%a5		/* sinc */
1:	SUBF
	SUBF
	cmpa.l	%a1,%a0
	bne.s	1b
	move.l	48(%sp),%a5
	move.l	%d7,(%a5)
	move.l	%d4,(4,%a5)
	move.l	%d5,(8,%a5)
	movem.l	(%sp),%d2-%d7/%a2-%a5
	lea	40(%sp),%sp
	rts

	.macro	HP sub
	move.l	(%a0),%d0		/* x */
	move.l	%d0,%d1
	sub.l	%d5,%d1			/* v3 = x - s2 */
	mac.l	%d6,%d4,%acc0		/* a1 s1 */
	mac.l	%a2,%d1,%acc0		/* a2 v3 */
	movclr.l %acc0,%d2		/* v1 */
	mac.l	%a2,%d4,%acc0		/* a2 s1 */
	mac.l	%a3,%d1,%acc0		/* a3 v3 */
	movclr.l %acc0,%d3
	add.l	%d5,%d3			/* v2 */
	neg.l	%d4
	add.l	%d2,%d4
	add.l	%d2,%d4			/* s1 = 2 v1 - s1 */
	neg.l	%d5
	add.l	%d3,%d5
	add.l	%d3,%d5			/* s2 = 2 v2 - s2 */
	mac.l	%a4,%d2,%acc0		/* (k - 1) v1 */
	movclr.l %acc0,%d1
	sub.l	%d2,%d0
	sub.l	%d1,%d0
	sub.l	%d3,%d0			/* y = x - v1 - (k - 1) v1 - v2 */
	.if \sub
	add.l	(%a6)+,%d0		/* the Sub */
	.endif
	add.l	%d0,%d0			/* onto the bus: y x 2, saturated */
	bvc.s	8f
	move.l	#0x7fffffff,%d1		/* an overflow flips the sign: negative now, so it was positive */
	tst.l	%d0
	bmi.s	7f
	move.l	#0x80000000,%d1
7:	move.l	%d1,%d0
8:	move.l	%d0,(%a0)+
	.endm

	.section .text.msaw_hpf,"ax"
	.globl	msaw_hpf
msaw_hpf:
	lea	-44(%sp),%sp
	movem.l	%d2-%d7/%a2-%a6,(%sp)
	move.l	48(%sp),%a0		/* out */
	lea	128(%a0),%a1
	move.l	52(%sp),%a5		/* st */
	move.l	(%a5),%d4		/* s1 */
	move.l	(4,%a5),%d5		/* s2 */
	move.l	56(%sp),%a6		/* cf */
	move.l	(%a6),%d6		/* a1 */
	move.l	(4,%a6),%a2		/* a2 */
	move.l	(8,%a6),%a3		/* a3 */
	move.l	(12,%a6),%a4		/* k - 1 */
	move.l	60(%sp),%d0		/* the Sub's block, or 0 */
	bne.w	2f
1:	HP	0
	HP	0
	cmpa.l	%a1,%a0
	bne.w	1b
	bra.w	9f
2:	move.l	%d0,%a6
3:	HP	1
	HP	1
	cmpa.l	%a1,%a0
	bne.w	3b
9:	move.l	%d4,(%a5)
	move.l	%d5,(4,%a5)
	movem.l	(%sp),%d2-%d7/%a2-%a6
	lea	44(%sp),%sp
	rts
