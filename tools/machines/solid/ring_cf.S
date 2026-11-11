/* SOLID on the ColdFire (MCF5441x, EMAC): solid_ring2, two ringing modes with no input through one block of 32 frames,
   see solid.c (ring, solid_ring2). solid.c holds the same as C for the host (SOLID_HOST), the proof's model; the two
   agree bit for bit by construction: the same products into the same sums, each sum in an accumulator of its own and
   read once (each product truncated to 2^-23 of an LSB, the sum floored to Q31 and saturated, MACSR 0xa0 as
   solid_block set it), each output product read on its own and added to the frame as integers.

       void solid_ring2(struct mode *m, int32_t *out)

   struct mode (solid.c): +0 zr, +4 zi, +8 c, +12 s, +16 a, 24 bytes; m[0] and m[1]. Per frame, mode 1 in d0 zr, d1 zi
   with c d2, s d3, its weight a2; mode 2 in d4 zr, d5 zi with c d6, s d7, weight a3:

       zr' = zr c - zi s     (acc0, acc2)        zi' = zr s + zi c     (acc1, acc3)
       out += zi1' a1 + zi2' a2                  (acc0, acc1, read apart, added as integers)

   21 instructions a frame for two modes (two passes of the C loop: 26), the eight products of the rotations issued
   before the first read. Keeps d2-d7/a2-a6 and MACSR; leaves the four accumulators empty (and empties acc1 .. acc3
   first: the C around it only uses acc0).

   License: MIT (LICENSE next to this file). */

	.section .text.solid_ring2,"ax"
	.globl	solid_ring2
solid_ring2:
	lea	-44(%sp),%sp
	movem.l	%d2-%d7/%a2-%a6,(%sp)
	move.l	48(%sp),%a0		/* m */
	move.l	52(%sp),%a1		/* out */
	movclr.l %acc1,%d0		/* the accumulators the C does not use: empty */
	movclr.l %acc2,%d0
	movclr.l %acc3,%d0
	movem.l	(%a0),%d0-%d3		/* zr1, zi1, c1, s1 */
	move.l	16(%a0),%a2		/* a1 */
	movem.l	24(%a0),%d4-%d7		/* zr2, zi2, c2, s2 */
	move.l	40(%a0),%a3		/* a2 */
	lea	128(%a1),%a4		/* the block's end */
1:	mac.l	%d0,%d2,%acc0		/* zr1 c1 */
	mac.l	%d0,%d3,%acc1		/* zr1 s1 */
	msac.l	%d1,%d3,%acc0		/* - zi1 s1 */
	mac.l	%d1,%d2,%acc1		/* + zi1 c1 */
	mac.l	%d4,%d6,%acc2		/* zr2 c2 */
	mac.l	%d4,%d7,%acc3		/* zr2 s2 */
	msac.l	%d5,%d7,%acc2		/* - zi2 s2 */
	mac.l	%d5,%d6,%acc3		/* + zi2 c2 */
	movclr.l %acc0,%d0		/* zr1' */
	movclr.l %acc1,%d1		/* zi1' */
	movclr.l %acc2,%d4		/* zr2' */
	movclr.l %acc3,%d5		/* zi2' */
	mac.l	%d1,%a2,%acc0		/* zi1' a1 */
	mac.l	%d5,%a3,%acc1		/* zi2' a2 */
	movclr.l %acc0,%a5
	movclr.l %acc1,%a6
	adda.l	%a6,%a5
	adda.l	(%a1),%a5		/* + the frame so far */
	move.l	%a5,(%a1)+
	cmpa.l	%a4,%a1
	bne.s	1b
	movem.l	%d0-%d1,(%a0)		/* zr1, zi1 */
	movem.l	%d4-%d5,24(%a0)		/* zr2, zi2 */
	movem.l	(%sp),%d2-%d7/%a2-%a6
	lea	44(%sp),%sp
	rts
