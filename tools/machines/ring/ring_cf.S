/* Ring's frame loops for the ColdFire (MCF5441x, EMAC), see ring.c: one block of 32 frames in place. ring.c's
   frames() holds the same loop in C for the host (the proof's model); the two agree bit for bit by construction: the
   carrier RING_COS[ph >> 21], Wave's clip, the gain k16 + (2 Mix c with its low half cleared), the frame times the
   gain on the EMAC (MACSR 0xa0 and acc0 clear, as ring.c sets them, floor(x g16 / 2^31) as 0.2's split gives it).

   void ring_sine(const struct run *r), ring_shape(const struct run *r): r's fields in the order loaded (ring.c):
   +0 m2 (d4), +4 drive (d5), +8 inc (d6), +12 the phase (d7), +16 the block (a0), +20 RING_COS (a2), +24 k16 (a3);
   d3 the shift to the carrier's step (21), a1 the block's end, a4 the frame. Keeps d2-d7/a2-a6 and MACSR; leaves
   acc0 clear.

   A loop of one frame, the frame read where it is written: 13 instructions a frame on the sine, 20 with the clip.
   Four frames a turn with MAC with load saved 2.5 a frame more but doubled the code's lines, which a cold cache reads
   at about 15 cycles each (the model of notes/27 §2): measured, the one-frame loop is the cheaper or equal under
   every assumption (notes/74 §13).

   License: MIT (LICENSE next to this file). */

#define CAR	move.l %d7,%d0 ; lsr.l %d3,%d0 ; mvs.w (%a2,%d0.l*2),%d0
#define CLIP \
	muls.l	%d5,%d0 ; asr.l #8,%d0 ; \
	cmpi.l	#32767,%d0 ; ble.s 8f ; move.l #32767,%d0 ; 8: \
	cmpi.l	#-32767,%d0 ; bge.s 9f ; move.l #-32767,%d0 ; 9:
#define GAIN	muls.l %d4,%d0 ; andi.l #0xffff0000,%d0 ; add.l %a3,%d0
#define OUT	move.l (%a0),%a4 ; mac.l %d0,%a4,%acc0 ; movclr.l %acc0,%d0 ; move.l %d0,(%a0)+ ; add.l %d6,%d7

#define ENTRY(NAME, SHAPE) \
	.section .text.NAME,"ax" ; \
	.p2align 2 ; \
	.globl	NAME ; \
NAME: ; \
	lea	-32(%sp),%sp ; \
	movem.l	%d3-%d7/%a2-%a4,(%sp) ; \
	movea.l	36(%sp),%a1 ; \
	movem.l	(%a1),%d4-%d7/%a0/%a2-%a3 ; \
	moveq	#21,%d3 ; \
	lea	128(%a0),%a1 ; \
1:	CAR ; SHAPE GAIN ; OUT ; \
	cmpa.l	%a1,%a0 ; \
	bne.s	1b ; \
	movem.l	(%sp),%d3-%d7/%a2-%a4 ; \
	lea	32(%sp),%sp ; \
	rts

#define NOCLIP
#define WITHCLIP CLIP ;

/* each in a section of its own, like -ffunction-sections (Level B builders keep file order) */
ENTRY(ring_sine, NOCLIP)
ENTRY(ring_shape, WITHCLIP)
