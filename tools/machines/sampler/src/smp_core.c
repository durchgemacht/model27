/* Sample voice, see smp_core.h. */
#include "smp_core.h"

#ifdef SMP_DEBUG
#include <assert.h>
#define SMP_ASSERT(x) assert(x)
#else
#define SMP_ASSERT(x) ((void)0)
#endif

/* Taps reach this many frames back from the playhead (and SMP_TAPS - 1 - BACK forward). */
#define BACK (SMP_TAPS / 2 - 1)

/* 2^25 / SMP_FADE rounded up: a frame count times this, >> 10, is its share of a fade in Q15. */
#define FADE_RECIP (((1u << 25) + SMP_FADE - 1) / SMP_FADE)

void smp_trigger(smp_voice *v, const int16_t *pcm, int32_t length, int32_t start, int32_t end,
                 int flags)
{
    if (end > length)
        end = length;
    if (start < 0)
        start = 0;
    v->pcm = pcm;
    v->start = start;
    v->end = end;
    v->pos = 0;
    v->frac = 0;
    v->active = start < end;
    v->reverse = (flags & SMP_REVERSE) != 0;
    v->fade_in = (v->reverse ? end < length : start > 0) ? 0 : SMP_FADE;
    v->loop = (flags & SMP_LOOP) != 0;
    v->stop = v->loop ? SMP_LOOPING : end - start;
    v->looped = 0;
}

void smp_set_loop(smp_voice *v, int on)
{
    v->loop = on != 0;
}

void smp_set_ratio(smp_voice *v, uint32_t ratio_q16)
{
    if (ratio_q16 > SMP_MAX_RATIO_Q16)
        ratio_q16 = SMP_MAX_RATIO_Q16;
    if (ratio_q16 < SMP_MIN_RATIO_Q16)
        ratio_q16 = SMP_MIN_RATIO_Q16;
    /* At 96 kHz each frame moves half the ratio on; as 32.32 that is the ratio shifted by 15. */
    v->step_int = ratio_q16 >> 17;
    v->step_frac = ratio_q16 << 15;
}

/* A fade's gain n frames in, Q15: 0 at n = 0, 32768 from SMP_FADE on, the S curve 3x^2 - 2x^3
   of x = n / SMP_FADE between. */
static uint32_t fade_gain(int32_t n)
{
    uint32_t x;

    if (n <= 0)
        return 0;
    if (n >= SMP_FADE)
        return 32768;
    x = ((uint32_t)n * FADE_RECIP) >> 10;
    return ((x * x >> 15) * (3u * 32768 - 2 * x)) >> 15;
}

/* a * g / 32768 for g up to 32768, towards zero, without 64-bit arithmetic. */
static int32_t scale(int32_t a, uint32_t g)
{
    uint32_t m = a < 0 ? 0u - (uint32_t)a : (uint32_t)a;
    uint32_t r = (m >> 15) * g + (((m & 0x7fff) * g) >> 15);

    return a < 0 ? -(int32_t)r : (int32_t)r;
}

/* Frames from the block's first until the playhead reaches the end, rounded up (distance and
   step cut to 16 fractional bits, so possibly one more); SMP_FADE + SMP_BLOCK2X while the end
   lies beyond the block and its fade, or the voice loops. */
static int32_t frames_to_end(const smp_voice *v)
{
    int32_t d = v->stop - v->pos;
    uint32_t dq, sq;

    if (v->stop == SMP_LOOPING || d > (int32_t)((SMP_FADE + SMP_BLOCK2X + 1) * (v->step_int + 1)))
        return SMP_FADE + SMP_BLOCK2X;
    if (d <= 0)
        return 0;
    dq = ((uint32_t)d << 16) - (v->frac >> 16);
    sq = (v->step_int << 16) | (v->step_frac >> 16);
    return (int32_t)((dq + sq - 1) / sq);
}

/* Where a loop switched off ends: at the end of the first pass whose end lies at least SMP_FADE
   frames ahead at this step, counted as pos. The frames the fade takes, rounded up, and two more for
   the playhead's fraction and frames_to_end's rounding. */
static int32_t last_stop(const smp_voice *v)
{
    int32_t len = v->end - v->start;
    int32_t need = (int32_t)(SMP_FADE * v->step_int + ((SMP_FADE * (v->step_frac >> 16)) >> 16)) + 2;

    return ((v->pos + need) / len + 1) * len;
}

/* Copies the frames the next block reads into scratch, in the order they play, so the inner loop
   needs no bounds checks: the window's frames, forward or reverse, again from its other end past
   the end of a pass while the voice loops (and before its first frame once it has looped), zeros
   anywhere else. Returns how many frames it wrote. */
static int32_t fetch(const smp_voice *v, int16_t *scratch)
{
    /* The last of the 64 frames sits 63 steps on. The fraction carries at most once a step;
       the top 16 bits of fraction and step, rounded up, bound the carries from above. */
    uint32_t carries = ((v->frac >> 16) + 1u + 63u * ((v->step_frac >> 16) + 1u)) >> 16;
    int32_t n = (int32_t)(63u * v->step_int + carries) + SMP_TAPS;
    int32_t len = v->end - v->start, m = v->pos - BACK, k = 0, r, run, i;
    int32_t lim = v->stop == SMP_LOOPING ? m + n : v->stop;    /* one past the last frame that plays */

    if (m < 0 && !v->looped) {          /* before the first frame played */
        for (; m < 0; m++)
            scratch[k++] = 0;
    }
    r = m % len;                        /* the frame of the window m plays, counted as pos */
    if (r < 0)
        r += len;
    while (k < n && m < lim) {
        run = len - r;
        if (run > n - k)
            run = n - k;
        if (run > lim - m)
            run = lim - m;
        if (v->reverse) {
            const int16_t *x = v->pcm + v->end - 1 - r;

            for (i = 0; i < run; i++)
                scratch[k + i] = x[-i];
        } else {
            const int16_t *x = v->pcm + v->start + r;

            for (i = 0; i < run; i++)
                scratch[k + i] = x[i];
        }
        k += run;
        m += run;
        r = 0;
    }
    for (; k < n; k++)
        scratch[k] = 0;
    return n;
}

int smp_render_with(smp_voice *v, int32_t *out, int16_t *scratch,
                    const int16_t (*table)[SMP_TAPS])
{
    uint32_t f, ip, si, sf;
    int32_t k, n, fi, rem;

    if (!v->active) {
        for (k = 0; k < SMP_BLOCK2X; k++)
            out[k] = 0;
        return 0;
    }
    if (v->loop) {                      /* loops from its next end on, unless the fade-out has begun */
        if (v->stop != SMP_LOOPING && frames_to_end(v) >= SMP_FADE)
            v->stop = SMP_LOOPING;
    } else if (v->stop == SMP_LOOPING) {
        v->stop = last_stop(v);
    }
    n = fetch(v, scratch);
    SMP_ASSERT(n <= (int32_t)SMP_SCRATCH);
    (void)n;

    f = v->frac;
    ip = 0;
    si = v->step_int;
    sf = v->step_frac;
    fi = v->fade_in;
    rem = frames_to_end(v);
    for (k = 0; k < SMP_BLOCK2X; k++, rem--) {
        const int16_t *c = table[f >> 24];
        const int16_t *x = scratch + ip;
        uint32_t g;

        SMP_ASSERT(ip + SMP_TAPS <= (uint32_t)n);
        out[k] = c[0] * x[0] + c[1] * x[1] + c[2] * x[2] + c[3] * x[3] + c[4] * x[4]
               + c[5] * x[5];
        if (fi < SMP_FADE || rem < SMP_FADE) {
            uint32_t gain = fade_gain(fi);

            if (rem < SMP_FADE)
                gain = (gain * fade_gain(rem)) >> 15;
            out[k] = scale(out[k], gain);
            fi += fi < SMP_FADE;
        }
        g = f + sf;
        ip += si + (g < f);
        f = g;
    }
    v->pos += (int32_t)ip;
    v->frac = f;
    v->fade_in = fi;
    if (v->stop == SMP_LOOPING) {
        int32_t len = v->end - v->start;

        if (v->pos >= len) {            /* round the window, the overshoot carried over */
            v->pos %= len;
            v->looped = 1;
        }
    } else if (v->pos - BACK >= v->stop) {      /* every tap of the next frame is past the end */
        v->active = 0;
    }
    return 1;
}

int smp_render(smp_voice *v, int32_t *out, int16_t *scratch)
{
    return smp_render_with(v, out, scratch, smp_coeffs);
}
