/* SAMPLE's card (notes/60 §25): its pixels, set once on the screen's tick, before One-Shot's tick. model27's, not
   Cycles One-Shot's. License: MIT. */
#include <stdint.h>

typedef struct {
    uint32_t vtable;
    int32_t width, height, pitch;
    const uint32_t *words, *mask;
    uint32_t cleared;
} sample_bitmap;

uint32_t sample_card_px[96];

uint32_t smp_hook_tick(void *view);

/* from, x, y, width, height, to x, to y */
static const uint8_t cells[][7] = {
    {3, 0, 0, 24, 5, 0, 0},
    {3, 12, 0, 3, 5, 24, 0},
    {3, 8, 0, 3, 5, 28, 0},
    {2, 24, 7, 3, 5, 32, 0},
    {3, 24, 0, 3, 5, 36, 0},
    {3, 4, 0, 3, 5, 40, 0},
    {3, 28, 0, 3, 5, 44, 0},
    {3, 0, 7, 24, 5, 0, 7},
    {3, 8, 0, 3, 5, 24, 7},
    {1, 24, 7, 3, 5, 28, 7},
    {3, 8, 7, 3, 5, 32, 7},
    {3, 0, 14, 48, 5, 0, 14},
    {2, 0, 21, 48, 5, 0, 21},
    {1, 0, 28, 48, 5, 0, 28},
};

static int32_t bit_at(const uint32_t *w, int32_t x, int32_t r)
{
    int32_t y = 32 - r;

    return (int32_t)((w[2 * x + (y >> 5)] >> (31 - (y & 31))) & 1u);
}

/* 0x400075f0, in the screen's redraw: the card once, then One-Shot's tick (smp_hook_tick, which ends with
   jsr 0x40076be4(view), whether the view needs drawing). */
uint32_t sample_hook_tick(void *view)
{
    static int32_t card_set;
    const sample_bitmap *const volatile *vec = (const sample_bitmap *const volatile *)0x40fe32cc;
    uint32_t i;

    if (!card_set && vec[0] && vec[1] != vec[0]) {
        for (i = 0; i < sizeof cells / sizeof cells[0]; i++) {
            const uint8_t *c = cells[i];
            const uint32_t *src = vec[0][c[0]].words;
            int32_t x, r;

            for (x = 0; x < c[3]; x++)
                for (r = 0; r < c[4]; r++)
                    if (bit_at(src, c[1] + x, c[2] + r)) {
                        int32_t y = 32 - (c[6] + r);

                        sample_card_px[2 * (c[5] + x) + (y >> 5)] |= 1u << (31 - (y & 31));
                    }
        }
        card_set = 1;
    }
    return smp_hook_tick(view);
}
