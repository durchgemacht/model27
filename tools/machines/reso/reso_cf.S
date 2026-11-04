/* Reso on the ColdFire (MCF5441x, EMAC), see reso.c: reso_process, the comb of one block, 32 frames in place, and
   reso_work_out, the coefficients (both since 0.4; the frame loop alone, reso_frames, before). reso.c holds the same
   as C for the host (RESO_HOST), the proof's model; the two agree bit for bit by construction: the same integer steps,
   the same products in the same accumulator, each truncated to 2^-23 of an LSB, sums floored to Q31 when read,
   saturated (MACSR 0xa0, as the filter slot calls a filter).

   The track's state (reso.c, struct track): +16 kq, +20 q, +24 nrm, +28 rdc, +32 gt, +36 ia, +40 amt, the constants in
   the order the frame loop loads them; +44 eta; the states +48 x1, +52 v1, +56 lp, +60 hp; +68 w, +72 fill, +76 quiet,
   +80 dint; +84 the three words the coefficients are for, +90 set (the first 16 bytes and +64 are the host model's).

   The frame loop, four frames a turn: the input in d0 and d1 in turn (this frame's, the one before), the window in a4
   and a5 in turn (the frame dint + 1 back, the next one), v1 d2, lp d3, hp d4, y d5, eta d6. Every other constant
   comes into a6 on the MAC before its first use (MAC with load), and so do the input and the window's next frame:
   19 instructions a frame; y^2 goes into acc1 on the first frame of each four only (FRAME, then FRAMEQ: 18), the
   silence test's energy since 0.4. The window is read one frame ahead (the line has a frame more for it).

   License: MIT (LICENSE next to this file). */

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
	mac.l	%d5, %d5, %acc1		/* the block's energy */			; \
	move.l	%d5, (%a2)+		/* the line */					; \
	movclr.l %acc0, %d5							; \
	move.l	%d5, (%a0)+

/* the same without the energy (three frames in four) */
#define FRAMEQ(X, X1, U0, U1) \
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
	movclr.l %acc0, %d5							; \
	move.l	%d5, (%a0)+


/* void reso_process(int32_t *block, const int16_t *words, uint32_t track, uint32_t triggered): reso.c's, in
   assembly since 0.4: the per-block bookkeeping in registers (GCC kept it on the stack), the frame loop inline, the
   silence test stopping at the first frame that is not 0, the line's lazy clearing eight frames a movem, the copy of
   the line's first 32 frames by movem; reso_work_out when a word has moved. Keeps d2-d7/a2-a6 and MACSR; leaves acc0
   and acc1 at zero. */
#define TRACKS 6
#define LEN 5920
#define TOP 0x7f00
#define AMT 66052
#define ONE 0x7fffffff
#define QUIET_E 16			/* every fourth frame's y^2 / 2^31 at an RMS of 2^-15 */
#define LINE_BYTES 23812		/* (LEN + 33) * 4 */
#define S_SIZE 92
#define S_IA 36
#define S_AMT 40
#define S_ETA 44
#define S_X1 48
#define S_W 68
#define S_FILL 72
#define S_QUIET 76
#define S_DINT 80
#define S_KEY0 84
#define S_KEY1 86
#define S_KEY2 88
#define S_SET 90

	.section .text.reso_cf,"ax"
	.p2align 2
	.globl	reso_process
reso_process:
	move.l	12(%sp),%d0			/* track */
	moveq	#TRACKS-1,%d1
	cmp.l	%d0,%d1
	bcs	.Lret
	mulu.w	#S_SIZE,%d0
	lea	reso_state,%a0
	adda.l	%d0,%a0				/* st */
	movea.l	8(%sp),%a1			/* words */
	mvs.w	2(%a1),%d1			/* Amount */
	ble	.Loff
	lea	-44(%sp),%sp
	movem.l	%d2-%d7/%a2-%a6,(%sp)
	movea.l	%a0,%a3
	cmpi.l	#TOP,%d1
	ble.s	1f
	move.l	#TOP,%d1
1:	move.l	#AMT,%d0
	muls.l	%d0,%d1				/* amt */
	move.l	%d1,S_AMT(%a3)
	move.l	#ONE,%d0
	sub.l	%d1,%d0
	move.l	%d0,S_IA(%a3)			/* ia = 1 - amt */
	move.l	S_QUIET(%a3),%d0
	cmpi.l	#LEN,%d0
	bcc	.Lscan				/* rung out: is the block silent too? */
.Lkeys:
	tst.b	S_SET(%a3)
	beq.s	.Lwork
	move.w	(%a1),%d0
	cmp.w	S_KEY0(%a3),%d0
	bne.s	.Lwork
	move.w	4(%a1),%d0
	cmp.w	S_KEY1(%a3),%d0
	bne.s	.Lwork
	move.w	6(%a1),%d0
	cmp.w	S_KEY2(%a3),%d0
	beq.s	.Lline
.Lwork:
	move.l	%a1,-(%sp)
	move.l	%a3,-(%sp)
	jsr	reso_work_out
	addq.l	#8,%sp
.Lline:
	move.l	56(%sp),%d0			/* track (12 + 44) */
	mulu.w	#LINE_BYTES,%d0
	lea	reso_line,%a2
	adda.l	%d0,%a2				/* ln */
	move.l	S_W(%a3),%d3			/* w */
	move.l	S_DINT(%a3),%d2			/* dint */
	move.l	#LEN-1,%d0
	add.l	%d3,%d0
	sub.l	%d2,%d0				/* the window's first frame: w + LEN - dint - 1 */
	cmpi.l	#LEN,%d0
	bcs.s	1f
	subi.l	#LEN,%d0
1:	lea	(%a2,%d0.l*4),%a1		/* the window */
	move.l	%d3,%d0
	bne.s	1f
	move.l	#LEN,%d0			/* at the line's start, into its copy: the reads see it */
1:	lea	(%a2,%d0.l*4),%a2		/* where the block is written */
	move.l	S_FILL(%a3),%d4
	cmpi.l	#LEN,%d4
	bcc.s	.Lframes
	addq.l	#1,%d2
	sub.l	%d4,%d2				/* the frames of the window written before the comb started */
	ble.s	.Lframes
	moveq	#33,%d0
	cmp.l	%d0,%d2
	ble.s	1f
	move.l	%d0,%d2
1:	movea.l	%a1,%a4				/* d2 frames from the window's first set to 0, eight a store */
	moveq	#0,%d0
	move.l	%d0,%d3
	move.l	%d0,%d4
	move.l	%d0,%d5
	move.l	%d0,%d6
	move.l	%d0,%d7
	movea.l	%d0,%a5
	movea.l	%d0,%a6
	subq.l	#8,%d2
	blt.s	3f
2:	movem.l	%d0/%d3-%d7/%a5-%a6,(%a4)
	lea	32(%a4),%a4
	subq.l	#8,%d2
	bge.s	2b
3:	addq.l	#8,%d2
	beq.s	.Lframes
4:	move.l	%d0,(%a4)+
	subq.l	#1,%d2
	bne.s	4b
.Lframes:
	movea.l	48(%sp),%a0			/* the block (4 + 44) */
	move.l	S_ETA(%a3),%d6			/* eta */
	movem.l	S_X1(%a3),%d1-%d4		/* x1, v1, lp, hp */
	move.l	#0,%acc1
	movea.l	(%a1)+,%a4			/* the window's first two frames */
	movea.l	(%a1)+,%a5
	moveq	#8,%d7
5:	FRAME(%d0, %d1, %a4, %a5)
	FRAMEQ(%d1, %d0, %a5, %a4)
	FRAMEQ(%d0, %d1, %a4, %a5)
	FRAMEQ(%d1, %d0, %a5, %a4)
	subq.l	#1,%d7
	bne	5b
	movem.l	%d1-%d4,S_X1(%a3)		/* the last input (an odd frame's), v1, lp, hp */
	movclr.l %acc1,%d7			/* the energy, sum y^2 / 2^31, saturated */
	move.l	S_W(%a3),%d0
	bne.s	6f
	movem.l	-128(%a2),%d1-%d6/%a4-%a5	/* a2 = ln + LEN + 32: the line's first 32 frames from their copy */
	movem.l	%d1-%d6/%a4-%a5,-23808(%a2)
	movem.l	-96(%a2),%d1-%d6/%a4-%a5
	movem.l	%d1-%d6/%a4-%a5,-23776(%a2)
	movem.l	-64(%a2),%d1-%d6/%a4-%a5
	movem.l	%d1-%d6/%a4-%a5,-23744(%a2)
	movem.l	-32(%a2),%d1-%d6/%a4-%a5
	movem.l	%d1-%d6/%a4-%a5,-23712(%a2)
	moveq	#32,%d0
	bra.s	7f
6:	addi.l	#32,%d0
	cmpi.l	#LEN,%d0
	bcs.s	7f
	moveq	#0,%d0
7:	move.l	%d0,S_W(%a3)
	move.l	S_FILL(%a3),%d0
	cmpi.l	#LEN,%d0
	bcc.s	8f
	addi.l	#32,%d0
	move.l	%d0,S_FILL(%a3)
8:	moveq	#QUIET_E,%d0
	cmp.l	%d0,%d7
	bcs.s	9f
	clr.l	S_QUIET(%a3)			/* the block's RMS at 2^-15 of full scale or more */
	bra.s	.Lout
9:	move.l	S_QUIET(%a3),%d0
	cmpi.l	#LEN,%d0
	bcc.s	.Lout
	addi.l	#32,%d0
	move.l	%d0,S_QUIET(%a3)
.Lout:
	movem.l	(%sp),%d2-%d7/%a2-%a6
	lea	44(%sp),%sp
.Lret:	rts

.Lscan:						/* the first frame, then the rest or-ed */
	movea.l	48(%sp),%a0
	move.l	(%a0)+,%d0
	bne	.Lkeys
	.rept	31
	or.l	(%a0)+,%d0
	.endr
	bne	.Lkeys
	clr.l	S_FILL(%a3)			/* silent: the comb starts again from nothing */
	move.l	#LEN,%d0
	move.l	%d0,S_QUIET(%a3)
	clr.l	S_X1(%a3)
	clr.l	S_X1+4(%a3)
	clr.l	S_X1+8(%a3)
	clr.l	S_X1+12(%a3)
	bra.s	.Lout

.Loff:						/* off: untouched, the comb starts again from nothing */
	clr.l	S_FILL(%a0)
	move.l	#LEN,%d0
	move.l	%d0,S_QUIET(%a0)
	clr.l	S_X1(%a0)
	clr.l	S_X1+4(%a0)
	clr.l	S_X1+8(%a0)
	clr.l	S_X1+12(%a0)
	rts

/* void reso_work_out(struct track *c, const int16_t *words): reso.c's work_out, in assembly since 0.4: the same integer
   steps and the same EMAC products in the same order (each mul a mac and a movclr, mul2 two macs), so the same bits;
   the words clamped here and kept (key, set). The tables through reso_tab (reso.c). Keeps d2-d7/a2-a6; acc0 left at
   zero. */
#define S_KQ 16
#define S_Q 20
#define S_NRM 24
#define S_RDC 28
#define S_GT 32
#define G_MAX 0x7ff7ffff		/* ONE - 2^19 */
#define R_DC 0x7fbfffff			/* ONE - 2^22 */
/* the word at OFF(a1), clamped to 0 .. TOP, into D */
#define CLAMPW(OFF, D, L) \
	mvs.w	OFF(%a1), D		; \
	cmpi.l	#TOP, D			; \
	bls.s	L			; \
	move.l	#TOP, D			; \
	tst.w	OFF(%a1)		; \
	bpl.s	L			; \
	moveq	#0, D			; \
L:
/* N = divq(N, D) (reso.c): N / D in Q31 to 2^-14, ONE when N >= D, 0 when N is 0; D, T1, T2, T3 changed */
#define DIVQ(N, D, T1, T2, T3, X) \
	cmp.l	D, N			; \
	bcc.s	X##1			; \
	tst.l	N			; \
	beq.s	X##3			; \
	move.l	N, T1			; \
	ff1	T1			; \
	subq.l	#1, T1			; \
	move.l	D, T2			; \
	ff1	T2			; \
	subq.l	#1, T2			; \
	lsl.l	T1, N			; \
	lsl.l	T2, D			; \
	moveq	#15, T3			; \
	lsr.l	T3, D			; \
	divu.l	D, N			; \
	moveq	#16, T3			; \
	sub.l	T1, T3			; \
	add.l	T2, T3			; \
	bmi.s	X##2			; \
	move.l	#0x80000000, T1		; \
	lsr.l	T3, T1			; \
	cmp.l	T1, N			; \
	bcc.s	X##1			; \
	lsl.l	T3, N			; \
	bra.s	X##3			; \
X##2:	neg.l	T3			; \
	lsr.l	T3, N			; \
	bra.s	X##3			; \
X##1:	move.l	#ONE, N			; \
X##3:

	.section .text.reso_wo,"ax"	/* a section of its own: reso_process calls it by its address */
	.p2align 2
	.globl	reso_work_out
reso_work_out:
	lea	-40(%sp),%sp
	movem.l	%d2-%d7/%a2-%a5,(%sp)
	movea.l	44(%sp),%a0			/* c */
	movea.l	48(%sp),%a1			/* words */
	lea	reso_tab,%a3
	/* the pitch: L, sin and cos of w0 / 2 */
	CLAMPW(0, %d0, .Lw1)
	move.l	%d0,%d1
	lsr.l	#8,%d1				/* n */
	mvz.b	%d0,%d2				/* f */
	moveq	#23,%d7
	lsl.l	%d7,%d0
	andi.l	#0x7f800000,%d0			/* f << 23 */
	movea.l	(%a3),%a2			/* RESO_L */
	move.l	(%a2,%d1.l*4),%d3
	move.l	%d3,%d4
	sub.l	4(%a2,%d1.l*4),%d4
	mulu.l	%d2,%d4
	lsr.l	#8,%d4
	sub.l	%d4,%d3
	movea.l	%d3,%a5				/* L, 20.12 */
	movea.l	4(%a3),%a2			/* RESO_SH */
	move.l	(%a2,%d1.l*4),%d4
	move.l	4(%a2,%d1.l*4),%d5
	sub.l	%d4,%d5
	mac.l	%d5,%d0,%acc0
	movclr.l %acc0,%d5
	add.l	%d5,%d4				/* sh */
	movea.l	8(%a3),%a2			/* RESO_CH */
	move.l	(%a2,%d1.l*4),%d5
	move.l	4(%a2,%d1.l*4),%d6
	sub.l	%d5,%d6
	mac.l	%d6,%d0,%acc0
	movclr.l %acc0,%d6
	add.l	%d6,%d5				/* ch */
	/* the tone: P */
	CLAMPW(4, %d0, .Lw2)
	move.l	%d0,%d1
	lsr.l	#8,%d1				/* n */
	movea.l	12(%a3),%a2			/* RESO_P */
	move.l	(%a2,%d1.l*4),%d2
	move.l	%d2,%d6
	sub.l	4(%a2,%d1.l*4),%d6
	mvz.b	%d0,%d3				/* f */
	mulu.l	%d3,%d6
	lsr.l	#8,%d6
	sub.l	%d6,%d2				/* P, turns, Q32 */
	beq	.Lnodamp
	lsl.l	%d7,%d0
	andi.l	#0x7f800000,%d0			/* f << 23 */
	movea.l	16(%a3),%a2			/* RESO_SP2 */
	move.l	(%a2,%d1.l*4),%d3
	move.l	4(%a2,%d1.l*4),%d6
	sub.l	%d3,%d6
	mac.l	%d6,%d0,%acc0
	movclr.l %acc0,%d6
	add.l	%d6,%d3				/* s2 */
	movea.l	20(%a3),%a2			/* RESO_CP2 */
	move.l	(%a2,%d1.l*4),%d6
	move.l	4(%a2,%d1.l*4),%d1
	sub.l	%d6,%d1
	mac.l	%d1,%d0,%acc0
	movclr.l %acc0,%d1
	add.l	%d1,%d6				/* c2 */
	mac.l	%d3,%d6,%acc0			/* sp = 2 s2 c2 */
	mac.l	%d3,%d6,%acc0
	movclr.l %acc0,%d0
	mac.l	%d3,%d3,%acc0			/* cq = 1 - 2 s2 s2 */
	mac.l	%d3,%d3,%acc0
	movclr.l %acc0,%d1
	move.l	#ONE,%d7
	sub.l	%d1,%d7
	mac.l	%d4,%d5,%acc0			/* sw = 2 sh ch */
	mac.l	%d4,%d5,%acc0
	movclr.l %acc0,%a3
	mac.l	%d4,%d4,%acc0			/* cw = 1 - 2 sh sh */
	mac.l	%d4,%d4,%acc0
	movclr.l %acc0,%d1
	movea.l	#ONE,%a4
	suba.l	%d1,%a4
	mac.l	%d7,%d5,%acc0			/* cp = cos(P + w0/2) */
	msac.l	%d0,%d4,%acc0
	movclr.l %acc0,%d1
	mac.l	%a3,%d7,%acc0			/* swp = sin(w0 + P) */
	mac.l	%a4,%d0,%acc0
	movclr.l %acc0,%a3
	mac.l	%d4,%d6,%acc0			/* shp = sin((w0 + P) / 2) */
	mac.l	%d5,%d3,%acc0
	movclr.l %acc0,%a4
	mac.l	%d1,%d4,%acc0			/* kq = divq(2 cp sh, swp) */
	mac.l	%d1,%d4,%acc0
	movclr.l %acc0,%d0
	move.l	%a3,%d4
	DIVQ(%d0, %d4, %d5, %d6, %d7, .Lq)
	move.l	%d0,S_KQ(%a0)
	move.l	#ONE,%d4
	sub.l	%d0,%d4
	move.l	%d4,S_Q(%a0)
	mac.l	%a4,%d3,%acc0			/* dmp = divq(2 shp s2, cp) */
	mac.l	%a4,%d3,%acc0
	movclr.l %acc0,%d0
	DIVQ(%d0, %d1, %d5, %d6, %d7, .Ld)
	movea.l	%d0,%a4				/* dmp */
	lsr.l	#1,%d2				/* tau = (P / 2) L */
	mac.l	%d2,%a5,%acc0
	movclr.l %acc0,%d2
	bra.s	.Ldamped
.Lnodamp:
	move.l	#ONE,%d0
	move.l	%d0,S_KQ(%a0)
	clr.l	S_Q(%a0)
	moveq	#0,%d2				/* tau */
	suba.l	%a4,%a4				/* dmp */
.Ldamped:
	/* the line read dint frames back, then the allpass */
	move.l	%a5,%d0
	sub.l	%d2,%d0				/* D = L - tau */
	cmpi.l	#6144,%d0
	bcc.s	1f
	move.l	#6144,%d0
1:	subi.l	#2048,%d0
	move.l	%d0,%d1
	moveq	#12,%d3
	lsr.l	%d3,%d1
	move.l	%d1,S_DINT(%a0)
	andi.l	#4095,%d0			/* D, Q12 */
	move.l	%d0,%d1
	lsr.l	#6,%d1				/* n */
	moveq	#25,%d3
	lsl.l	%d3,%d0
	andi.l	#0x7e000000,%d0			/* (D & 63) << 25 */
	lea	reso_tab,%a3
	movea.l	28(%a3),%a2			/* RESO_ETA */
	move.l	(%a2,%d1.l*4),%d2
	move.l	4(%a2,%d1.l*4),%d3
	sub.l	%d2,%d3
	mac.l	%d3,%d0,%acc0
	movclr.l %acc0,%d3
	add.l	%d3,%d2
	move.l	%d2,S_ETA(%a0)
	/* the decay: the gain a period */
	CLAMPW(6, %d0, .Lw3)
	move.l	%d0,%d1
	lsr.l	#8,%d1				/* n */
	mvz.b	%d0,%d0				/* f */
	movea.l	24(%a3),%a2			/* RESO_E */
	move.l	(%a2,%d1.l*4),%d2
	move.l	%d2,%d3
	sub.l	4(%a2,%d1.l*4),%d3
	lsr.l	#8,%d3
	mulu.l	%d0,%d3
	sub.l	%d3,%d2
	move.l	%a5,%d0
	lsl.l	#6,%d0
	mac.l	%d0,%d2,%acc0			/* e = (L << 6) E, -log2 of the gain, Q24 */
	movclr.l %acc0,%d2
	move.l	%d2,%d0
	moveq	#24,%d1
	lsr.l	%d1,%d0				/* k */
	moveq	#30,%d1
	cmp.l	%d1,%d0
	bhi.s	.Lg0
	move.l	%d2,%d1
	swap	%d1
	mvz.b	%d1,%d1				/* i */
	movea.l	32(%a3),%a2			/* RESO_EXP */
	move.l	(%a2,%d1.l*4),%d3
	move.l	%d3,%d4
	sub.l	4(%a2,%d1.l*4),%d4
	moveq	#15,%d1
	lsl.l	%d1,%d2
	andi.l	#0x7fff8000,%d2
	mac.l	%d4,%d2,%acc0
	movclr.l %acc0,%d4
	sub.l	%d4,%d3
	asr.l	%d0,%d3				/* g = 2^-e */
	bra.s	.Lg1
.Lg0:	moveq	#0,%d3
.Lg1:	mac.l	%d3,%d3,%acc0			/* nrm = sqrt(1 - g g) */
	movclr.l %acc0,%d0
	move.l	#ONE,%d1
	sub.l	%d0,%d1
	ble.s	.Ln0
	move.l	%d1,%d0
	ff1	%d0
	subq.l	#1,%d0
	moveq	#-2,%d2
	and.l	%d2,%d0				/* z */
	lsl.l	%d0,%d1				/* x */
	move.l	%d1,%d2
	moveq	#23,%d4
	lsr.l	%d4,%d2				/* i */
	lsl.l	#8,%d1
	andi.l	#0x7fffff00,%d1
	movea.l	36(%a3),%a2			/* RESO_SQRT */
	move.l	(%a2,%d2.l*4),%d4
	move.l	4(%a2,%d2.l*4),%d5
	sub.l	%d4,%d5
	mac.l	%d5,%d1,%acc0
	movclr.l %acc0,%d5
	add.l	%d5,%d4
	lsr.l	#1,%d0
	asr.l	%d0,%d4
	move.l	%d4,S_NRM(%a0)
	bra.s	.Ln1
.Ln0:	clr.l	S_NRM(%a0)
.Ln1:	mac.l	%d3,%a4,%acc0			/* the loss given back: gt = g + g dmp, at most G_MAX */
	movclr.l %acc0,%d0
	move.l	#G_MAX,%d1
	sub.l	%d3,%d1
	cmp.l	%d1,%d0
	ble.s	1f
	move.l	#G_MAX,%d0
	bra.s	2f
1:	add.l	%d3,%d0
2:	move.l	%d0,S_GT(%a0)
	move.l	#R_DC,%d0
	move.l	%d0,S_RDC(%a0)
	move.w	(%a1),S_KEY0(%a0)		/* the words the coefficients are for */
	move.w	4(%a1),S_KEY1(%a0)
	move.w	6(%a1),S_KEY2(%a0)
	moveq	#1,%d0
	move.b	%d0,S_SET(%a0)
	movem.l	(%sp),%d2-%d7/%a2-%a5
	lea	40(%sp),%sp
	rts
