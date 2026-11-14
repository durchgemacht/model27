/* SOLID's card (notes/71 §13): its pixels, set once on the screen's tick. License: MIT. */
#include <stdint.h>

typedef struct {
    uint32_t vtable;
    int32_t width, height, pitch;
    const uint32_t *words, *mask;
    uint32_t cleared;
} solid_bitmap;

uint32_t solid_card_px[96];

/* from, x, y, width, height, to x, to y */
static const uint8_t cells[][7] = {
    {3, 0, 0, 48, 5, 0, 0},
    {3, 0, 7, 24, 5, 0, 7},
    {2, 24, 7, 3, 5, 24, 7},
    {1, 28, 7, 3, 5, 28, 7},
    {3, 0, 21, 3, 5, 32, 7},
    {2, 36, 7, 3, 5, 36, 7},
    {2, 40, 7, 3, 5, 40, 7},
    {3, 0, 14, 48, 5, 0, 14},
    {2, 0, 21, 48, 5, 0, 21},
    {2, 0, 28, 48, 5, 0, 28},
};

static int32_t bit_at(const uint32_t *w, int32_t x, int32_t r)
{
    int32_t y = 32 - r;

    return (int32_t)((w[2 * x + (y >> 5)] >> (31 - (y & 31))) & 1u);
}

/* 0x400075f0, in the screen's redraw: jsr 0x40076be4(view), which says whether the view needs drawing. */
uint32_t solid_hook_tick(void *view)
{
    static int32_t done;
    const solid_bitmap *const volatile *vec = (const solid_bitmap *const volatile *)0x40fe32cc;
    uint32_t i;

    if (!done && vec[0] && vec[1] != vec[0]) {
        for (i = 0; i < sizeof cells / sizeof cells[0]; i++) {
            const uint8_t *c = cells[i];
            const uint32_t *src = vec[0][c[0]].words;
            int32_t x, r;

            for (x = 0; x < c[3]; x++)
                for (r = 0; r < c[4]; r++)
                    if (bit_at(src, c[1] + x, c[2] + r)) {
                        int32_t y = 32 - (c[6] + r);

                        solid_card_px[2 * (c[5] + x) + (y >> 5)] |= 1u << (31 - (y & 31));
                    }
        }
        done = 1;
    }
    return ((uint32_t (*)(void *))0x40076be4)(view);
}
