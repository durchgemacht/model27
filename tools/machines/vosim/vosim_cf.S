/* VOSIM on the ColdFire (MCF5441x), see vosim.c: the sample loop of one block, 32 frames, in two forms:
   vosim_loop_bell (CONTOUR's first step: Braids' bell, Interpolate824(lut_bell) >> 1) and vosim_loop_half (a step of
   FAM_H, at half scale, 15 bits of the phase). vosim.c holds the same loop as C (loop()), which the host builds and the
   proofs compare with; the two agree bit for bit by construction: the same integer steps (the interpolations' products
   in muls.l, the window's in mulu.l, both operands >= 0), the DC stage's two products through the EMAC as vosim.c's
   mul() (MACSR 0xa0, set by vosim_block before the call).

   void vosim_loop_bell(struct vosim_voice *v, int32_t *out, const int16_t *sine, const uint16_t *bell);
   void vosim_loop_half(struct vosim_voice *v, int32_t *out, const int16_t *sine, const uint16_t *step);

   The voice (vosim.c, struct vosim_voice): +0 phase, +4 inc, +8 fp0, +12 fp1, +16 fi0, +20 fi1, +24 acc, +28 off.
   Registers in the loop: a5 phase, a3 inc, d1 fp0, d2 fp1, a4 the period's sum in this block, a6 off, a0 out,
   a1 the sine, a2 the window, d0 the output's shift (14); d3 to d7 the work. fi0, fi1, acc and the end of out on the
   stack. 58 instructions a sample, the period's start apart (GCC's loop of vosim.c: 77).

   License: MIT (LICENSE next to this file). */

#define FI0 44
#define FI1 48
#define ACC 52
#define END 56
#define ARG 64			/* v, out, sine, window */

/* d4 = (P >> 8) & 0xffff (the fraction), d5 = P >> 24 (the entry); P a data register or a5 through d4 */
#define SPLIT \
	move.l	%d4, %d5						; \
	swap	%d5							; \
	mvz.w	%d5, %d5		/* P >> 24 */				; \
	mvz.w	%d4, %d4		/* (P >> 8) & 0xffff */

/* R = Interpolate824(sine, P): a + ((b - a) f >> 16); d3 a, d4 f, d5 the entry */
#define SINE(R) \
	mvs.w	%a1@(0,%d5:l:2), %d3					; \
	mvs.w	%a1@(2,%d5:l:2), R					; \
	sub.l	%d3, R							; \
	muls.l	%d4, R							; \
	swap	R			/* >> 16, arithmetic */			; \
	ext.l	R							; \
	add.l	%d3, R

/* the two formants into d6: 24576 + (sine(fp0) >> 1) + (sine(fp1) >> 2) */
#define FORMANTS \
	add.l	%sp@(FI0), %d1		/* fp0 += fi0 */			; \
	move.l	%d1, %d4						; \
	lsr.l	#8, %d4							; \
	SPLIT								; \
	SINE(%d6)							; \
	asr.l	#1, %d6							; \
	addi.l	#24576, %d6						; \
	add.l	%sp@(FI1), %d2		/* fp1 += fi1 */			; \
	move.l	%d2, %d4						; \
	lsr.l	#8, %d4							; \
	SPLIT								; \
	SINE(%d7)							; \
	asr.l	#2, %d7							; \
	add.l	%d7, %d6

/* the rest of a sample: s = s w >> 15, the period's start, the sum, the output; then the next sample or the end */
#define TAIL(L) \
	mulu.l	%d7, %d6		/* s w, both >= 0 */			; \
	lsr.l	#8, %d6							; \
	lsr.l	#7, %d6							; \
	cmpa.l	%a3, %a5		/* phase < inc: a new period */		; \
	bcs.w	L##_start						; \
L##_back:								; \
	adda.l	%d6, %a4		/* sum += s */				; \
	sub.l	%a6, %d6						; \
	asl.l	%d0, %d6		/* (s - off) << 14 */			; \
	move.l	%d6, %a0@+						; \
	cmpa.l	%sp@(END), %a0						; \
	bne.w	L##_loop						; \
	bra.w	L##_done						; \
L##_start:				/* fp0 = fp1 = s = 0; off = (acc + mul(sum << 8, inc >> 1) + 128) >> 8 */ ; \
	moveq	#0, %d1							; \
	moveq	#0, %d2							; \
	moveq	#0, %d6							; \
	move.l	%a4, %d3						; \
	asl.l	#8, %d3							; \
	move.l	%a3, %d4						; \
	lsr.l	#1, %d4							; \
	mac.l	%d3, %d4, %acc0						; \
	movclr.l %acc0, %d3						; \
	add.l	%sp@(ACC), %d3						; \
	addi.l	#128, %d3						; \
	asr.l	#8, %d3							; \
	movea.l	%d3, %a6		/* off */				; \
	clr.l	%sp@(ACC)		/* acc = 0 */				; \
	suba.l	%a4, %a4		/* sum = 0 */				; \
	bra.w	L##_back						; \
L##_done:

#define ENTRY(L) \
	lea	%sp@(-60), %sp						; \
	movem.l	%d2-%d7/%a2-%a6, %sp@					; \
	movea.l	%sp@(ARG), %a0		/* v */					; \
	movea.l	%a0@, %a5		/* phase */				; \
	movea.l	%a0@(4), %a3		/* inc */				; \
	move.l	%a0@(8), %d1		/* fp0 */				; \
	move.l	%a0@(12), %d2		/* fp1 */				; \
	move.l	%a0@(16), %sp@(FI0)					; \
	move.l	%a0@(20), %sp@(FI1)					; \
	move.l	%a0@(24), %sp@(ACC)					; \
	movea.l	%a0@(28), %a6		/* off */				; \
	movea.l	%sp@(ARG + 8), %a1	/* sine */				; \
	movea.l	%sp@(ARG + 12), %a2	/* window */				; \
	movea.l	%sp@(ARG + 4), %a0	/* out */				; \
	lea	%a0@(128), %a4						; \
	move.l	%a4, %sp@(END)						; \
	suba.l	%a4, %a4		/* sum = 0 */				; \
	moveq	#14, %d0

/* v->phase, fp0, fp1, off; v->acc = acc + mul(sum << 8, inc >> 1) */
#define EXIT \
	move.l	%a4, %d3						; \
	asl.l	#8, %d3							; \
	move.l	%a3, %d4						; \
	lsr.l	#1, %d4							; \
	mac.l	%d3, %d4, %acc0						; \
	movclr.l %acc0, %d3						; \
	add.l	%sp@(ACC), %d3						; \
	movea.l	%sp@(ARG), %a1						; \
	move.l	%a5, %a1@						; \
	move.l	%d1, %a1@(8)						; \
	move.l	%d2, %a1@(12)						; \
	move.l	%d3, %a1@(24)						; \
	move.l	%a6, %a1@(28)						; \
	movem.l	%sp@, %d2-%d7/%a2-%a6					; \
	lea	%sp@(60), %sp						; \
	rts

	.section .text.vosim_loop_bell,"ax"
	.globl	vosim_loop_bell
	.type	vosim_loop_bell, @function
vosim_loop_bell:
	ENTRY(bell)
bell_loop:
	adda.l	%a3, %a5		/* phase += inc */
	FORMANTS
	move.l	%a5, %d4		/* w = Interpolate824(bell, phase) >> 1 */
	lsr.l	#8, %d4
	SPLIT
	mvz.w	%a2@(0,%d5:l:2), %d3
	mvz.w	%a2@(2,%d5:l:2), %d7
	sub.l	%d3, %d7
	muls.l	%d4, %d7
	swap	%d7
	ext.l	%d7
	add.l	%d3, %d7
	asr.l	#1, %d7
	TAIL(bell)
	EXIT
	.size	vosim_loop_bell, . - vosim_loop_bell

	.section .text.vosim_loop_half,"ax"
	.globl	vosim_loop_half
	.type	vosim_loop_half, @function
vosim_loop_half:
	ENTRY(half)
half_loop:
	adda.l	%a3, %a5		/* phase += inc */
	FORMANTS
	move.l	%a5, %d4		/* w = a + ((b - a) ((phase >> 9) & 0x7fff) >> 15) */
	lsr.l	#8, %d4
	move.l	%d4, %d5
	swap	%d5
	mvz.w	%d5, %d5
	lsr.l	#1, %d4
	andi.l	#0x7fff, %d4
	mvz.w	%a2@(0,%d5:l:2), %d3
	mvz.w	%a2@(2,%d5:l:2), %d7
	sub.l	%d3, %d7
	muls.l	%d4, %d7
	asr.l	#8, %d7
	asr.l	#7, %d7
	add.l	%d3, %d7
	TAIL(half)
	EXIT
	.size	vosim_loop_half, . - vosim_loop_half
