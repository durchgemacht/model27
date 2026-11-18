/* VOSIM (working name) for model27 (notes/86): Braids' VOSIM oscillator with formant tracking and a decaying window.
 *
 * Origin and licence: the oscillator is Mutable Instruments Braids' DigitalOscillator::RenderVosim, with
 * ComputePhaseIncrement and the tables lut_bell, wav_sine, lut_oscillator_increments (braids/digital_oscillator.cc,
 * braids/resources.cc, copied into vosim_tables.h by tools/gen_vosim.py), carried over integer for integer;
 * Interpolate824 is stmlib's (utils/dsp.h): Copyright 2012 Emilie Gillet, MIT licence (eurorack 08460a6, stmlib
 * e3bd7c9, LICENSE-Braids). The formant tracking, the window family, its level and the DC stage are model27's; the
 * EMAC helpers TERRA's and SOLID's. This file: model27 (durchgemacht and Claude), MIT.
 *
 * Two sine formants (the second at half the level), windowed over each period of the note and restarted at its start,
 * as Braids does. The knobs (the maintainer's decisions of 2026-11-18, notes/86 §2): COLOR formant 1 (Braids' TIMBRE),
 * SHAPE formant 2 (Braids' COLOR): the knob's value is the formant's MIDI note (69 = 440 Hz); SWEEP the formants
 * follow the note, 0 fixed as Braids, 127 fully (reversed for a test and back, notes/86 §10), linearly in semitones, agreeing at C5 (MIDI 60), held below Braids'
 * table end (13.3 kHz); CONTOUR the window, from Braids' bell (0) in 16 steps to an e-curve that falls by 24 dB over
 * the period (127), the steps' level made up (3.5 dB at the end). The DC: the window's offset is taken out by the
 * mean of the last period, each sample weighted by its phase step. 48 kHz, one point a sample. DECAY, GATE and PUNCH
 * are the stock amp chain as on TONE; while the envelope is closed and no trig comes, the core is not called.
 * A trig does not restart them, as Braids without sync (the maintainer's decision, 2026-11-18, notes/86 §6);
 * VOSIM_RESET 1 would restart carrier and formants at a trig (Braids' sync), kept as an option at no cost.
 *
 * The core is step 1's (_scratch/vosim-machine/vosim.c) with the chosen variant only: the same bits, Braids' scale
 * (int16 full scale = 32768) up to the output, which goes onto the bus << VOSIM_OSH (notes/86 §4). With SWEEP 0 and
 * CONTOUR 0 it is Braids' RenderVosim with every phase increment doubled (Braids runs at 96 kHz), bit for bit; with
 * VOSIM_RESET a trig is Braids' sync on the block's first sample. Plain C99, no libc, no float, no 64-bit arithmetic
 * on the device; the products of the DC stage through the EMAC (MACSR 0xa0), on the host (VOSIM_HOST) the same
 * arithmetic in __int128. */
#include <stdint.h>
#include "vosim_tables.h"

#define BLOCK 32
#define KNOB_MAX (127 << 8)
#define REF_PITCH (60 * 128)        /* SWEEP: fixed and tracking formants agree at C5, 1/128 semitone */
#define TOP_PITCH (128 * 128 - 1)   /* Braids' table end: MIDI 128 - 1/128 (13.29 kHz) */
#ifndef VOSIM_OSH
#define VOSIM_OSH 14                /* the output: Braids' scale << 14, Q29 (notes/86 §4.3) */
#endif
#ifndef VOSIM_RESET
#define VOSIM_RESET 0               /* runs on through a trig: 0, decided (notes/86 §6); 1 restarts at a trig */
#endif
#ifndef VOSIM_ASM
#define VOSIM_ASM 1                 /* the device's sample loop from vosim_cf.S (notes/86 §4.4), the host's always C */
#endif
#if VOSIM_ASM && !defined(VOSIM_HOST) && VOSIM_OSH != 14
#error "vosim_cf.S shifts the output by 14"
#endif

/* --- the EMAC (as terra.c, solid.c) ------------------------------------------------------------------------- */
#ifdef VOSIM_HOST
typedef __int128 wide;
static wide acc;
#define TRUNC(p) ((p) & ~(wide)0x7fffff)
static inline void emac_start(void) { acc = 0; }
static inline void mac(int32_t a, int32_t b) { acc += TRUNC((wide)a * b); }
static inline int32_t movclr(void)
{
	wide v = acc >> 31;
	acc = 0;
	return v > INT32_MAX ? INT32_MAX : v < INT32_MIN ? INT32_MIN : (int32_t)v;
}
#else
static inline void emac_start(void)                 /* signed, fractional, saturating, truncating; acc0 empty */
{
	__asm__ volatile("move.l #0xa0,%%macsr\n\tmove.l #0,%%acc0" : : : "memory");
}
static inline void mac(int32_t a, int32_t b) { __asm__ volatile("mac.l %0,%1,%%acc0" : : "r"(a), "r"(b)); }
static inline int32_t movclr(void)
{
	int32_t r;
	__asm__ volatile("movclr.l %%acc0,%0" : "=d"(r));
	return r;
}
#endif
static inline int32_t mul(int32_t a, int32_t b) { mac(a, b); return movclr(); }          /* a b / 2^31 */
static inline int32_t clamp(int32_t x, int32_t lo, int32_t hi) { return x < lo ? lo : x > hi ? hi : x; }

/* --- Braids, integer for integer ---------------------------------------------------------------------------- */
/* stmlib Interpolate824(const int16_t *, phase); the result lies between two entries, so its cast to int16_t
 * changes nothing and is left out */
static inline int32_t isine(uint32_t p)
{
	const int16_t *t = WAV_SINE + (p >> 24);
	const int32_t a = t[0];

	return a + (((t[1] - a) * (int32_t)((p >> 8) & 0xffff)) >> 16);
}

/* Interpolate824(lut_bell, phase) >> 1. stmlib computes in uint32 and truncates to uint16; for a falling segment
 * that gives a - ceil(d f / 2^16), which the signed form with an arithmetic shift gives too while (b - a) f fits in
 * int32 (lut_bell steps by 6 622 at most) */
static inline int32_t ibell(uint32_t p)
{
	const uint16_t *q = LUT_BELL + (p >> 24);
	const int32_t a = q[0];

	return (a + (((q[1] - a) * (int32_t)((p >> 8) & 0xffff)) >> 16)) >> 1;
}

/* a window step of FAM_H, already at half scale (up to 49 030): 15 bits of the phase, no shift after */
static inline int32_t ihalf(const uint16_t *t, uint32_t p)
{
	const uint16_t *q = t + (p >> 24);
	const int32_t a = q[0];

	return a + (((q[1] - a) * (int32_t)((p >> 9) & 0x7fff)) >> 15);
}

static uint32_t cpi(int32_t midi_pitch)             /* DigitalOscillator::ComputePhaseIncrement (96 kHz) */
{
	int32_t ref;
	int shifts = 0;
	uint32_t a, b, inc;

	if (midi_pitch >= 128 * 128)
		midi_pitch = 128 * 128 - 1;
	ref = midi_pitch - 128 * 128;
	while (ref < 0) {
		ref += 12 * 128;
		++shifts;
	}
	a = LUT_INC[ref >> 4];
	b = LUT_INC[(ref >> 4) + 1];
	inc = a + ((int32_t)(b - a) * (ref & 0xf) >> 4);
	return inc >> shifts;
}

/* --- the voice ---------------------------------------------------------------------------------------------- */
struct vosim_in {               /* one block's inputs (knobs 8.8, 0 .. 127 << 8) */
	int32_t note;           /* semitones << 16 */
	int32_t color, shape;   /* formants 1 and 2: Braids' parameters */
	int32_t sweep, contour; /* the tracking, the window */
	int32_t trig;           /* a trig starts the note in this block (with VOSIM_RESET) */
};

struct vosim_voice {
	uint32_t phase, inc, fp0, fp1, fi0, fi1;    /* Braids' phase_, phase_increment_, formant phases and steps */
	int32_t acc;            /* the period's mean so far, the blocks done, Q8 */
	int32_t off;            /* the offset taken out: the last period's mean */
};
/* vosim_cf.S reads the voice at +0 phase .. +28 off: eight words in this order */
typedef char vosim_voice_layout[sizeof(struct vosim_voice) == 32 && __builtin_offsetof(struct vosim_voice, off) == 28
				? 1 : -1];

static void vosim_init(struct vosim_voice *v)
{
	v->phase = v->inc = v->fp0 = v->fp1 = v->fi0 = v->fi1 = 0;
	v->off = (24576 * WMEAN_BELL) >> 15;        /* the bell's DC: the first period starts near zero */
	v->acc = 0;
}

static inline int32_t knob_q15(int32_t k)           /* 8.8 knob 0 .. 127 -> Q15 0 .. 32768 (127 = 1.0 exactly) */
{
	return (int32_t)(((uint32_t)clamp(k, 0, KNOB_MAX) * 66053u) >> 16);
}

#if VOSIM_ASM && !defined(VOSIM_HOST)
void vosim_loop_bell(struct vosim_voice *v, int32_t *out, const int16_t *sine, const uint16_t *bell);
void vosim_loop_half(struct vosim_voice *v, int32_t *out, const int16_t *sine, const uint16_t *step);
#define LOOP(v, out, half, ta) ((half) ? vosim_loop_half(v, out, WAV_SINE, ta) : vosim_loop_bell(v, out, WAV_SINE, ta))
#else
#define LOOP(v, out, half, ta) loop(v, out, half, ta)
#endif

/* One block. half: 0 Braids' bell (exact), 1 a step of FAM_H (ta). Each a loop of its own; vosim_cf.S the same. */
static inline __attribute__((always_inline)) void loop(struct vosim_voice *v, int32_t *out, const int half,
						       const uint16_t *ta)
{
	uint32_t phase = v->phase, fp0 = v->fp0, fp1 = v->fp1;
	const uint32_t inc = v->inc, fi0 = v->fi0, fi1 = v->fi1;
	int32_t acc = v->acc, off = v->off, sum = 0;
	int i;

	for (i = 0; i < BLOCK; ++i) {
		int32_t s, w;

		phase += inc;
		fp0 += fi0;
		s = 24576 + (isine(fp0) >> 1);
		fp1 += fi1;
		s += isine(fp1) >> 2;
		w = half ? ihalf(ta, phase) : ibell(phase);
		s = (int32_t)(((uint32_t)s * (uint32_t)w) >> 15);    /* both >= 0 */
		if (phase < inc) {                          /* a new period: the formants restart, Braids' 0 */
			fp0 = 0;
			fp1 = 0;
			s = 0;
			off = (acc + mul(sum << 8, (int32_t)(inc >> 1)) + 128) >> 8;
			acc = 0;
			sum = 0;
		}
		sum += s;
		out[i] = (s - off) << VOSIM_OSH;
	}
	v->phase = phase;
	v->fp0 = fp0;
	v->fp1 = fp1;
	v->acc = acc + mul(sum << 8, (int32_t)(inc >> 1));  /* this block's part of the period's mean, Q8 */
	v->off = off;
}

static void vosim_block(struct vosim_voice *v, const struct vosim_in *k, int32_t *out)
{
	const int32_t pitch = (int16_t)((k->note + 256) >> 9);        /* Braids' pitch, 1/128 semitone */
	const int32_t p0 = (int16_t)k->color >> 1, p1 = (int16_t)k->shape >> 1;
	const int32_t t = knob_q15(k->sweep), j = (knob_q15(k->contour) * 16 + 16384) >> 15;

	v->inc = cpi(pitch) << 1;                       /* Braids' 96 kHz step, doubled for 48 kHz */
	if (VOSIM_RESET && k->trig) {                   /* Braids' sync: the first sample's phase is 0 */
		v->phase = 0u - v->inc;
		v->acc = v->off << 8;                   /* that restart keeps the offset: it ends no whole period */
	}
	if (t == 0) {
		v->fi0 = cpi(p0) << 1;
		v->fi1 = cpi(p1) << 1;
	} else {
		const int32_t tr = ((pitch - REF_PITCH) * t) >> 15;

		v->fi0 = cpi(clamp(p0 + tr, 0, TOP_PITCH)) << 1;
		v->fi1 = cpi(clamp(p1 + tr, 0, TOP_PITCH)) << 1;
	}
	emac_start();
	if (j == 0)
		LOOP(v, out, 0, LUT_BELL);
	else
		LOOP(v, out, 1, FAM_H[j - 1]);
}

#ifdef VOSIM_HOST
/* --- the host's entries (the proofs, notes/86 §5) ----------------------------------------------------------- */
/* n blocks of 6 int32 (note, COLOR, SHAPE, SWEEP, CONTOUR, trig) through one fresh voice, 32 int32 a block out */
void vosim_host_render(const int32_t *in, int n, int32_t *out)
{
	struct vosim_voice v;

	vosim_init(&v);
	for (int b = 0; b < n; b++) {
		const int32_t *p = in + 6 * b;
		struct vosim_in k = { p[0], p[1], p[2], p[3], p[4], p[5] };

		vosim_block(&v, &k, out + BLOCK * b);
	}
}

/* the same with the voice kept between calls (a track that pauses: the proofs call it only for blocks not paused) */
static struct vosim_voice hv[6];

void vosim_host_reset(int t)
{
	vosim_init(&hv[t]);
}

void vosim_host_block(int t, const int32_t *in, int32_t *out)
{
	struct vosim_in k = { in[0], in[1], in[2], in[3], in[4], in[5] };

	vosim_block(&hv[t], &k, out);
}

#else
/* --- the machine in the voice loop (STANDARD.md §2), as TERRA's (notes/85 §4.2, §9) ----------------------------- */
#define CYC_VOICE0  0x42308828u
#define CYC_VSTRIDE 0x31c
#define MARK_OFF    0x2c
#define MARK        0x564f5331                      /* 'VOS1' */

#define AMP_ENV(v)  ((void (*)(char *))0x400a9252)(v)
#define VCA(o, v)   ((void (*)(int32_t *, char *))0x400a9430)(o, v)
#define PUNCH(o, v) ((void (*)(int32_t *, char *))0x400a967a)(o, v)
#define LUT_DECAY   ((const int32_t *)0x4011d84c)   /* DECAY -> the envelope's factor a block (TONE's) */
#define IDLE_LEVEL  (1 << 14)                       /* the amp envelope below -102 dB */
/* PUNCH's output stage (+0x2a4, notes/84 §9.3): TERRA's 0x7fffffff (TONE's x 4). The core's Braids scale goes onto
 * the bus << 14 (Q29: Braids' int16 full scale = 1/4 of the bus, as TERRA puts Plaits' full scale), so a track's
 * output is Braids' full scale a TONE voice at full scale - 18 dB; after the DC stage the peaks reach about 1.8 of
 * that (+5.3 dB): 6.8 dB under the bus's full scale, past PUNCH's limit (a third of it) only at the brightest
 * decaying windows. Measured in step 3 (notes/86 §8.1). */
#define STAGE       0x7fffffff

#define V32(o)      (*(int32_t *)(v + (o)))
#define P16(o)      (*(const int16_t *)(p + (o)))

static struct vosim_voice trk[6];
static struct vosim_in kin[6];

static inline int track_of(const char *v) { return (int)(((uint32_t)v - CYC_VOICE0) / CYC_VSTRIDE); }
static inline uint32_t mag(int32_t x) { return x < 0 ? 0u - (uint32_t)x : (uint32_t)x; }

void vosim_update(int32_t pmod, char *v, const char *p)
{
	int t = track_of(v);
	struct vosim_in *k = &kin[t];
	int32_t dec, note;

	if (V32(MARK_OFF) != MARK) {                    /* first block since the track changed machine: a fresh voice */
		vosim_init(&trk[t]);
		V32(MARK_OFF) = MARK;
	}
	/* the stock amp chain, set up the way TONE sets it (0x400aa7b8), as TERRA, CHIPS, SWARM, MAXSAW and SAMPLE do */
	dec = (int8_t)p[0x24];
	dec = dec < 0 ? 0 : dec > 127 ? 127 : dec;
	V32(0x250) = LUT_DECAY[dec];
	if (V32(0x38)) {
		V32(0x274) = V32(0x278) = 0x012c0f26;
		V32(0x280) = V32(0x284) = 0x001f7c5c;
		V32(0x290) = V32(0x294) = 0x7fffffff;
		V32(0x27c) = (int32_t)0x82581e4b;
		V32(0x288) = (int32_t)0x803ef8b8;
		/* PUNCH as TONE sets it (on 0x400aa8de, off 0x400aa8fe), its output stage +0x2a4 VOSIM's (STAGE) */
		if (P16(0x1e)) {
			V32(0x29c) = 0x20000000; V32(0x2a0) = 0x60000000; V32(0x2a4) = STAGE;
			V32(0x48) = 1;
		} else {
			V32(0x29c) = 0x7fffffff; V32(0x2a0) = 0x20000000; V32(0x2a4) = STAGE;
			V32(0x48) = 0;
		}
	}
	/* the note as every machine computes it: the trig's note + PITCH - 64 + FINE (+-2 semitones) */
	note = pmod + ((int32_t)P16(0x14) << 8) + (((int32_t)P16(0x22) - 0x4000) << 3) - (64 << 16);
	k->note = clamp(note, 0, 127 << 16);
	k->color = P16(0x16);                           /* COLOR: formant 1 */
	k->shape = P16(0x18);                           /* SHAPE: formant 2 */
	k->sweep = P16(0x1a);                           /* SWEEP: the tracking */
	k->contour = P16(0x1c);                         /* CONTOUR: the window */
#if VOSIM_RESET
	k->trig = V32(0x38) != 0;                       /* the block after the trig, where the envelope starts (CHIPS') */
#endif
}

/* A block that is not paused: its own function, so that the pause's path in vosim_render saves no registers. */
static __attribute__((noinline)) void render_live(int32_t *out, char *v, int t)
{
	int32_t macsr;

	__asm__ volatile("move.l %%macsr,%0" : "=d"(macsr));
	vosim_block(&trk[t], &kin[t], out);             /* onto the bus: Q29 */
	AMP_ENV(v);
	{
		/* The VCA without the trig's flags (0x400a9430), as TERRA's and SWARM's (notes/85 §9): it would fade the
		 * level to 0 in a trig's block (+0x34) and jump back to full in the next (+0x38); hidden, it ramps from the
		 * level it had to the envelope's over each block. AMP_ENV before and PUNCH after see the flags. */
		int32_t f34 = V32(0x34), f38 = V32(0x38);

		V32(0x34) = 0;
		V32(0x38) = 0;
		VCA(out, v);
		V32(0x34) = f34;
		V32(0x38) = f38;
	}
	PUNCH(out, v);
	__asm__ volatile("move.l %0,%%macsr" : : "d"(macsr));
}

void vosim_render(int32_t *out, char *v)
{
	int n;

	if (!V32(0x34) && !V32(0x38) && mag(V32(0x230)) < IDLE_LEVEL && mag(V32(0x234)) < IDLE_LEVEL) {
		for (n = 0; n < BLOCK; n++)             /* the envelope is closed and no trig: the voice stands still */
			out[n] = 0;
		return;
	}
	render_live(out, v, track_of(v));
}
#endif
