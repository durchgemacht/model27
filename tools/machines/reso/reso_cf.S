/* Reso's frame loop for the ColdFire (MCF5441x, EMAC), see reso.c: the comb of one block, 32 frames in place.
   reso.c's frames() holds the same loop as C for the host (RESO_HOST); the two agree bit for bit by construction:
   the same products in the same accumulator, each truncated to 2^-23 of an LSB, sums floored to Q31 when read,
   saturated (MACSR 0xa0, as the filter slot calls a filter).

   void reso_frames(struct track *st): the track's state (reso.c): +0 the block, +4 the line's window (the frame
   dint + 1 back, then the next ones), +8 where the line is written, +12 the block's end; the constants in the order
   the loop loads them, +16 kq, +20 q, +24 nrm, +28 rdc, +32 gt, +36 ia, +40 amt; +44 eta; the states +48 x1,
   +52 v1, +56 lp, +60 hp; +64 out, the frames' y + THR or-ed together.

   Two frames a turn: the input in d0 and d1 in turn (this frame's, the one before), the window in a4 and a5 in turn
   (the frame dint + 1 back, the next one), v1 d2, lp d3, hp d4, y d5, eta d6, the or d7. Every other constant comes
   into a6 on the MAC before its first use (MAC with load), and so do the input and the window's next frame: 20
   instructions a frame. The window is read one frame ahead (the line has a frame more for it). Keeps d2-d7/a2-a6
   and MACSR; leaves acc0 at zero.

   License: MIT (LICENSE next to this file). */

#define THR 65536		/* reso.c's */

/* one frame: X the input, X1 the one before, U0 the window's frame dint + 1 back, U1 the next one */
#define FRAME(X, X1, U0, U1) \
	move.l	U0, %acc0		/* the allpass: U0 + eta (U1 - v1) */		; \
	mac.l	U1, %d6, (%a0), X, %acc0	/* the input */			; \
	msac.l	%d2, %d6, 16(%a3), %a6, %acc0	/* kq */			; \
	movclr.l %acc0, %d2		/* v1 */					; \
	mac.l	%d2, %a6, 20(%a3), %a6, %acc0	/* the damping: kq v1; q */	; \
	mac.l	%d3, %a6, 24(%a3), %a6, %acc0	/* + q lp; nrm */		; \
	movclr.l %acc0, %d3		/* lp */					; \
	msac.l	X1, %a6, (%a1)+, U0, %acc0	/* the input less its DC: - nrm x1; the window's next frame */ ; \
	mac.l	X, %a6, 28(%a3), %a6, %acc0	/* + nrm x; rdc */		; \
	mac.l	%d4, %a6, 32(%a3), %a6, %acc0	/* + rdc hp; gt */		; \
	move.l	%acc0, %d4		/* hp */					; \
	mac.l	%d3, %a6, 36(%a3), %a6, %acc0	/* the comb: hp + gt lp; ia */	; \
	movclr.l %acc0, %d5		/* y */						; \
	mac.l	X, %a6, 40(%a3), %a6, %acc0	/* the output: ia x; amt */	; \
	mac.l	%d5, %a6, %acc0		/* + amt y */					; \
	move.l	%d5, (%a2)+		/* the line */					; \
	add.l	#THR, %d5							; \
	or.l	%d5, %d7		/* under 2^17 while |y| < THR */		; \
	movclr.l %acc0, %d5							; \
	move.l	%d5, (%a0)+

	.section .text.reso_cf,"ax"	/* a section of its own, like -ffunction-sections (Level B builders keep file order) */
	.p2align 2
	.globl	reso_frames
reso_frames:
	lea	-44(%sp), %sp
	movem.l	%d2-%d7/%a2-%a6, (%sp)
	movea.l	48(%sp), %a3			/* st */
	movem.l	(%a3), %a0-%a2			/* the block, the window, the line */
	move.l	44(%a3), %d6			/* eta */
	movem.l	48(%a3), %d1-%d4		/* x1, v1, lp, hp */
	moveq	#0, %d7
	movea.l	(%a1)+, %a4			/* the window's first two frames */
	movea.l	(%a1)+, %a5
1:	FRAME(%d0, %d1, %a4, %a5)
	FRAME(%d1, %d0, %a5, %a4)
	cmpa.l	12(%a3), %a0
	bne	1b
	movem.l	%d1-%d4, 48(%a3)		/* the last input (an odd frame's), v1, lp, hp */
	move.l	%d7, 64(%a3)
	movem.l	(%sp), %d2-%d7/%a2-%a6
	lea	44(%sp), %sp
	rts
