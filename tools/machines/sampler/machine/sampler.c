/* SAMPLE: a sampler machine for the Elektron Model:Cycles, OS 1.13 - the audio side.

   A trig plays the sample its sound names once (one shot), or in a loop, forward or reverse, through
   the core in src/smp_core.c and hands the result to the Cycles' own chain: its 2:1 decimator (0x400a9f58), then the amp
   envelope, VCA and PUNCH, set up the way TONE (0x400aa7b8) and Modded-Cycles' MACRO set them.
   Last comes SAMPLE's own filter (src/smp_filter.c), as on the Model:Samples, where the filter is
   the last stage of a track. Which sample: the note's sound names it in its parameters k 26/27,
   read from the copy the audio side keeps before any smoothing (TARGETS); pool.c has loaded it,
   or the note stays silent.

   Contract of the voice loop (Modded-Cycles notes/14 and notes/43): sampler_update(pmod, v, p),
   then sampler_render(out, v), once per block of 32 frames at 48 kHz. pmod is the trig's note in
   semitones << 16, v the track's voice (0x31c bytes), p its parameters as 8.8 words (+0x14 PITCH,
   +0x16 COLOR, +0x18 SHAPE, +0x1a SWEEP, +0x1c CONTOUR, +0x1e PUNCH, +0x22 FINE, +0x24 DECAY);
   v+0x34 / v+0x38 hold the trig of this block / of the previous one; out takes 32 int32 (Q31).
   Like every machine, the sound starts in the block after the trig: the VCA keeps the trig's own
   block silent. A trig that cuts a voice still sounding brings the new note in over its first
   block, from silence, as the Model:Samples' level stage does (0x400a7266 there): the cut goes out
   in 0.67 ms, the new note comes in in 0.67 ms.

   Knobs: PITCH, FINE and the trig's note set the pitch as on every machine; note 60 at PITCH 64
   and FINE 64 plays the sample as recorded (a sample at another rate keeps its pitch). COLOR =
   start, SHAPE = length, both 0 to 120 as on the Model:Samples (SMP_SPAN in pool.h): moving the
   start keeps the length. SWEEP = cutoff (64 = open, below a lowpass, above a highpass) and
   CONTOUR = resonance, as the Model:Samples' CUTOFF and RESONANCE. DECAY, GATE and PUNCH are the
   stock amp chain. The filter keeps running on silence while its resonance rings out.

   Two switches, in builds with model27's shortcut layer (SMP_SWITCHES): RETRIG + PUNCH = Loop, the
   window again and again with a hard seam, asked every block, so it acts on a note that plays;
   RETRIG + GATE = Reverse, the window from its end to its start, from the next trig on. A loop
   plays until the amp envelope has closed. */
#include <stdint.h>
#include "smp_core.h"
#include "smp_filter.h"
#include "os.h"
#include "pool.h"

#define VSTRIDE     0x31c
#define MARK_OFF    0x2c                        /* cleared by the voice reset when the machine changes */
#define MARK        0x534d5031                  /* 'SMP1' */
#define ROOT        (60 << 16)                  /* the note that plays a sample as recorded */
#define IDLE_LEVEL  (1 << 14)                   /* amp envelope below -102 dB */

/* The switches (SW_LOOP, SW_REVERSE in pool.h), read in the sound the note plays (CUR_SND(t), +20 +
   2 * 32), or in the copy of its 66 bytes when that is 0 (a preview note), not in p, which the OS
   smooths block by block. */
#ifdef SMP_SWITCHES
static uint32_t note_switches(int t)
{
    const char *snd = (const char *)CUR_SND(t);

    return (uint16_t)(snd ? *(const volatile int16_t *)(snd + SOUND_K32) : *(const int16_t *)(TARGETS(t) + 64));
}
#else
#define note_switches(t) ((void)(t), 0u)
#endif

#define V32(o)      (*(int32_t *)(v + (o)))
#define P16(o)      (*(const int16_t *)(p + (o)))

static smp_voice voices[6];
static smp_filter filters[6];
static uint32_t rates[6];                       /* each voice's sample rate / 48 kHz, Q16.16 */
static uint8_t cut[6];                          /* a trig cut the voice while it sounded */
static int16_t scratch[SMP_SCRATCH];
/* The decimator reads 8 frames of history and then the block at 96 kHz; it fills the history in
   itself from the voice's state (v+0x318) and stores it back. */
static int32_t buf[8 + SMP_BLOCK2X];

/* 2^(i/12) as Q16.16 */
static const uint32_t SEMITONE[13] = {
    65536, 69433, 73562, 77936, 82570, 87480, 92682, 98193, 104032, 110218, 116772, 123715, 131072,
};

static int track_of(const char *v)
{
    return (int)(((uintptr_t)v - VOICE0) / VSTRIDE);
}

static uint32_t mag(int32_t x)
{
    return x < 0 ? 0u - (uint32_t)x : (uint32_t)x;
}

static int32_t span(const char *p, int off)    /* 8.8 word -> 0..SMP_SPAN, fraction kept */
{
    int32_t k = P16(off);

    return k < 0 ? 0 : k > SMP_SPAN ? SMP_SPAN : k;
}

/* x * k / SMP_SPAN for k = 0..SMP_SPAN, without overflow for any frame count */
static int32_t share(int32_t x, int32_t k)
{
    return x / SMP_SPAN * k + x % SMP_SPAN * k / SMP_SPAN;
}

/* 2^(d/12) as Q16.16 for d semitones (Q16); linear within a semitone (0.7 cents at most). */
static uint32_t ratio_of(int32_t d)
{
    int32_t oct = 0;
    uint32_t s, f, r;

    while (d < 0) {
        d += 12 << 16;
        oct--;
    }
    while (d >= 12 << 16) {
        d -= 12 << 16;
        oct++;
    }
    s = (uint32_t)d >> 16;
    f = (uint32_t)d & 0xffff;
    r = SEMITONE[s] + (((SEMITONE[s + 1] - SEMITONE[s]) * f) >> 16);
    return oct >= 0 ? r << oct : r >> -oct;
}

/* a * b >> 16 from 16-bit parts (the ColdFire has no 64-bit product); a < 2^24, b < 2^20 */
static uint32_t mul_q16(uint32_t a, uint32_t b)
{
    uint32_t ah = a >> 16, al = a & 0xffff, bh = b >> 16, bl = b & 0xffff;

    return ((ah * bh) << 16) + ah * bl + al * bh + ((al * bl) >> 16);
}

/* A trig: play the sample the note's sound names, from COLOR's start for SHAPE's length; the
   Model:Samples' rule (0x400a62dc): the end at Start + Length, at most the sample's end. flags:
   SMP_LOOP, SMP_REVERSE. */
static void start(int t, char *v, const char *p, int flags)
{
    const uint16_t *k = (const uint16_t *)(TARGETS(t) + 52);   /* k 26/27: the sample's id */
    const smp_slot *sl = smp_find((uint32_t)k[0] << 16 | k[1]);
    int32_t *state = DECIMATOR_STATE(v);
    int32_t from, to, i;

    if (!sl) {                                  /* none, or not loaded yet: silence */
        voices[t].active = 0;
        return;
    }
    from = span(p, 0x16);
    to = from + span(p, 0x18);
    if (to > SMP_SPAN)
        to = SMP_SPAN;
    smp_trigger(&voices[t], sl->pcm, sl->frames, share(sl->frames, from), share(sl->frames, to), flags);
    rates[t] = sl->rate_q16;
    for (i = 0; i < 12; i++)                   /* no tail of the previous sound */
        state[i] = 0;
}

int smp_voices_use(const void *lo, const void *hi)
{
    int t;

    for (t = 0; t < 6; t++)
        if (voices[t].active && (const void *)voices[t].pcm >= lo && (const void *)voices[t].pcm < hi)
            return 1;
    return 0;
}

void sampler_update(int32_t pmod, char *v, const char *p)
{
    int t = track_of(v);
    smp_voice *sv = &voices[t];
    uint32_t sw = note_switches(t);
    int32_t dec, n;

    if (V32(MARK_OFF) != MARK) {                /* first block since the track changed machine */
        sv->active = 0;
        cut[t] = 0;
        smp_filter_reset(&filters[t]);
        V32(MARK_OFF) = MARK;
    }
    /* the stock amp chain, set up like TONE and MACRO */
    dec = (int8_t)p[0x24];
    dec = dec < 0 ? 0 : dec > 127 ? 127 : dec;
    V32(0x250) = LUT_DECAY[dec];
    if (V32(0x38)) {
        V32(0x274) = V32(0x278) = 0x012c0f26;
        V32(0x280) = V32(0x284) = 0x001f7c5c;
        V32(0x290) = V32(0x294) = 0x7fffffff;
        V32(0x27c) = (int32_t)0x82581e4b;
        V32(0x288) = (int32_t)0x803ef8b8;
        if (P16(0x1e)) {
            V32(0x29c) = 0x20000000;
            V32(0x2a0) = 0x60000000;
            V32(0x2a4) = 0x20000000;
            V32(0x48) = 1;
        } else {
            V32(0x29c) = 0x7fffffff;
            V32(0x2a0) = 0x20000000;
            V32(0x2a4) = 0x20000000;
            V32(0x48) = 0;
        }
        start(t, v, p, (sw & SW_LOOP ? SMP_LOOP : 0) | (sw & SW_REVERSE ? SMP_REVERSE : 0));
    }
    smp_set_loop(sv, (sw & SW_LOOP) != 0);
    /* note = PITCH - 64 + the trig's note + FINE (+-2 semitones), as on every machine */
    n = ((int32_t)P16(0x14) << 8) + (((int32_t)P16(0x22) - 0x4000) << 3) - (64 << 16) + pmod;
    n = n < 0 ? 0 : n > 127 << 16 ? 127 << 16 : n;
    smp_set_ratio(sv, mul_q16(ratio_of(n - ROOT), rates[t] ? rates[t] : 1u << 16));
    /* the filter follows SWEEP and CONTOUR, smoothed by the OS like every knob */
    smp_filter_set(&filters[t], P16(0x1a), P16(0x1c));
}

void sampler_render(int32_t *out, char *v)
{
    int t = track_of(v);
    smp_voice *sv = &voices[t];
    smp_filter *fl = &filters[t];
    int i, in;

    /* nothing to play: no trig, and the sample has ended or the amp envelope is closed; then the
       voice is done, a loop too, and no longer holds its sample in memory */
    if (!V32(0x34) && !V32(0x38)
        && (!sv->active || (mag(V32(0x230)) < IDLE_LEVEL && mag(V32(0x234)) < IDLE_LEVEL))) {
        sv->active = 0;
        for (i = 0; i < SMP_BLOCK; i++)
            out[i] = 0;
        if (smp_filter_ringing(fl))             /* the resonance dies away on silence */
            smp_filter_run(fl, out);
        return;
    }
    in = V32(0x38) && cut[t];                   /* this block's note cut one that still sounded */
    cut[t] = V32(0x34) && sv->active;           /* this block's trig cuts the voice: the VCA takes it out */
    smp_render(sv, buf + 8, scratch);
    DECIMATE(v, buf, out);
    AMP_ENV(v);
    VCA(out, v);
    if (in)                                     /* in from silence over the block, frame i at i / 32 */
        for (i = 0; i < SMP_BLOCK; i++)
            out[i] = out[i] / SMP_BLOCK * i;
    PUNCH(out, v);
    smp_filter_run(fl, out);
}
