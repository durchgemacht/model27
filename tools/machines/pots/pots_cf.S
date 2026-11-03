/* POTS's decimator for the ColdFire (MCF5441x, EMAC), see pots.c (notes/69 §24): 48 -> 6 kHz by a second-order CIC,
   the triangle (1, 2 .. 8 .. 2, 1) over 15 frames, as two sums a loop frame on the EMAC (MAC with load). pots.c's
   pots_cic() is its model for the host; the two agree bit for bit (each product j w 2^24 exact, read as acc >> 31).

   void pots_cic(const int32_t *in, int32_t *x, int32_t *r): the block's 32 frames (L, R words) to its 4 loop frames.
   For the loop frame's 8 frames k = 0..7 (L and R each): acc0 = sum (8 - k) w / 128, acc1 = sum k w / 128; the loop
   frame is acc0 + the last loop frame's acc1 (*r, kept between blocks): (L + R) / 2 for a constant input. MACSR
   0xa0 as pots_process sets it. 36 instructions a loop frame; nothing read past the block. Keeps d2-d7/a2-a6;
   leaves acc0 and acc1 at zero.

   License: MIT (LICENSE next to this file). */

/* one frame's L or R word in X (loaded), the next one loaded into Y: acc0 by (8 - k), acc1 by k (none at k = 0) */
#define W0(X, Y, C8)		mac.l	X, C8, (%a0)+, Y, %acc0
#define WK(X, Y, CA, CB)	mac.l	X, CA, %acc0 ; mac.l X, CB, (%a0)+, Y, %acc1
#define WL(X, CA, CB)		mac.l	X, CA, %acc0 ; mac.l X, CB, %acc1

	.section .text.pots_cic,"ax"
	.p2align 2
	.globl	pots_cic
pots_cic:
	lea	-40(%sp), %sp
	movem.l	%d2-%d7/%a2-%a5, (%sp)
	movem.l	44(%sp), %a0-%a1		/* in, x */
	movea.l	52(%sp), %a4			/* r */
	lea	16(%a1), %a5			/* x's end: 4 loop frames */
	move.l	#0x1000000, %d2			/* c1 .. c8: j 2^24 */
	move.l	#0x2000000, %d3
	move.l	#0x3000000, %d4
	move.l	#0x4000000, %d5
	move.l	#0x5000000, %d6
	move.l	#0x6000000, %d7
	movea.l	#0x7000000, %a2
	movea.l	#0x8000000, %a3
1:	move.l	(%a0)+, %d0			/* the loop frame's first word */
	/* k = 0: L, R by 8 */
	W0(%d0, %d1, %a3)
	W0(%d1, %d0, %a3)
	/* k = 1 .. 7: by 8 - k and k */
	WK(%d0, %d1, %a2, %d2)
	WK(%d1, %d0, %a2, %d2)
	WK(%d0, %d1, %d7, %d3)
	WK(%d1, %d0, %d7, %d3)
	WK(%d0, %d1, %d6, %d4)
	WK(%d1, %d0, %d6, %d4)
	WK(%d0, %d1, %d5, %d5)
	WK(%d1, %d0, %d5, %d5)
	WK(%d0, %d1, %d4, %d6)
	WK(%d1, %d0, %d4, %d6)
	WK(%d0, %d1, %d3, %d7)
	WK(%d1, %d0, %d3, %d7)
	WK(%d0, %d1, %d2, %a2)
	WL(%d1, %d2, %a2)			/* the loop frame's last word: no load */
	movclr.l %acc0, %d1
	add.l	(%a4), %d1			/* + the last loop frame's acc1 */
	move.l	%d1, (%a1)+
	movclr.l %acc1, %d1
	move.l	%d1, (%a4)
	cmpa.l	%a5, %a1
	bne	1b
	movem.l	(%sp), %d2-%d7/%a2-%a5
	lea	40(%sp), %sp
	rts
