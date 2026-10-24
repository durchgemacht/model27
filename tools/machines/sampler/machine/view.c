/* SAMPLE's view on the main screen: the selected track's sample as a waveform across the whole
   screen, the start and end of what a trig plays marked on it, and above it two boxes: the current
   pattern's number on the left, the sound's name on the right (the browser names the sound after
   the sample it opens).

   It takes the place of MainScreenView while that shows the track, and of the knob view while that
   shows Start or Length (COLOR or SHAPE), so the markers follow those two knobs as they turn. Any
   other knob shows its value as before, and so do Start and Length while a trig is held: the knob
   view then shows the locked value. Tracks on other machines keep the stock views. */
#include "view.h"
#include "pool.h"
#include "os.h"

/* The knob view's index of SAMPLE's Start (its first descriptor): the build sets it, as a symbol or a
   constant (CM_SYMBOLS, see pool.h). */
#ifdef CM_SYMBOLS
extern char cm_descriptor_base[];
#define DESC_START  ((int32_t)(long)cm_descriptor_base)
#elif !defined(DESC_START)
#define DESC_START  76
#endif
#define DESC_LENGTH (DESC_START + 1)
#ifndef CUTOFF_OBJECT
#define CUTOFF_OBJECT 53                /* the parameter object Cutoff shares: SNARE's SWEEP; the build sets it */
#endif

#define SOUND_NAME  4                   /* sound: name, 16 bytes */
#define SOUND_COLOR 42                  /* sound: k 11, COLOR = Start, 8.8 */
#define SOUND_SHAPE 44                  /* sound: k 12, SHAPE = Length, 8.8 */
#define MACHINE_AT  38

/* The screen, y counted from the bottom (a set pixel is lit): along the top two boxes in the look
   of the OS's own browser title (0x400a539c: its title in the small font at 2, 53, then 0x40070efc
   turns rows 51..63 over), each lit, 13 rows high, its corners rounded off, its text in dark letters
   2 pixels in; the waveform below. The OS's text is 9 rows high from the y it is given, capitals
   included, so a text has 2 rows of box above and below. The pattern's box fits its number: every
   one of the 96, A01 to F16, is 17 pixels wide in the small font (3 characters of 5 and 2 gaps).
   The name's box takes the rest, 2 dark columns on: 101 pixels for a name of 15 characters, 89 at
   most. */
#define BAR_TOP     63                  /* the boxes' highest row, the screen's top */
#define BAR_Y       (BAR_TOP - 12)      /* their lowest, 13 rows down */
#define PATTERN_X0  0
#define PATTERN_X1  (PATTERN_X0 + 2 + 17 + 2 - 1)
#define NAME_X0     (PATTERN_X1 + 3)
#define NAME_X1     127
#define NAME_Y      (BAR_Y + 2)         /* the texts, small font */
#define WAVE_MID    25                  /* the waveform's zero line */
#define WAVE_HALF   24                  /* rows above and below it: 1..49, a free row under the bar */
#define TEXT_Y      (WAVE_MID - 4)      /* a message instead of the waveform, medium font, centred */

static void pixel(smp_bitmap *b, int x, int y)
{
    if ((unsigned)x < (unsigned)b->width && (unsigned)y < (unsigned)b->height)
        b->words[x * b->pitch + (y >> 5)] |= 0x80000000u >> (y & 31);
}

static void flip(smp_bitmap *b, int x, int y)
{
    if ((unsigned)x < (unsigned)b->width && (unsigned)y < (unsigned)b->height)
        b->words[x * b->pitch + (y >> 5)] ^= 0x80000000u >> (y & 31);
}

static void blank(smp_bitmap *b)
{
    int32_t i, n = b->width * b->pitch;

    for (i = 0; i < n; i++)
        b->words[i] = 0;
}

static void label(smp_bitmap *b, const void *glyphs, int x, int y, int flags, const char *s)
{
    uint32_t font[2];

    FONT_MAKE(font, glyphs);
    DRAW_TEXT(b, font, x, y, flags, "%s", s);
    FONT_DROP(font);
}

/* A box from column left to right: its text drawn lit on the blank screen, then every pixel of the
   box turned over, so the box is lit and the letters dark, then its four corner pixels dark again. */
static void box(smp_bitmap *b, int left, int right, const char *text)
{
    int x, y;

    if (text)
        label(b, FONT_SMALL, left + 2, NAME_Y, 0, text);
    for (y = BAR_Y; y <= BAR_TOP; y++)
        for (x = left; x <= right; x++)
            flip(b, x, y);
    flip(b, left, BAR_Y);
    flip(b, right, BAR_Y);
    flip(b, left, BAR_TOP);
    flip(b, right, BAR_TOP);
}

/* The current pattern's number as MainScreenView writes it ("%c%02d", 0x4001b44c): its bank A to F,
   then 01 to 16. */
static void pattern_number(char *s)
{
    int32_t p = current_pattern();

    s[0] = (char)('A' + p / 16);
    s[1] = (char)('0' + (p % 16 + 1) / 10);
    s[2] = (char)('0' + (p % 16 + 1) % 10);
    s[3] = 0;
}

static int32_t sound_span(const char *sound, int at)  /* 8.8 word -> 0..SMP_SPAN, fraction kept */
{
    int32_t k = *(const int16_t *)(sound + at);

    return k < 0 ? 0 : k > SMP_SPAN ? SMP_SPAN : k;
}

/* Outside what a trig plays, a quarter of the pixels: every other row counted from the zero line,
   every other column in those rows, one column further on from one such row to the next. No two
   dots touch, each column keeps dots, and a silent stretch still shows as a dotted zero line. */
static int quarter(int32_t c, int32_t y)
{
    int32_t dy = y - WAVE_MID;

    return !(dy % 2) && !((c + dy / 2) % 2);
}

/* The waveform scaled to its own peak: the part a trig plays in full, the rest in a quarter of
   its pixels; a solid line at the start, a dotted one at the last column played. Columns follow the
   engine's rule (SMP_SPAN in pool.h): the start at Start / 120 of the sample, the end at
   (Start + Length) / 120, at most the sample's end. */
static void waveform(smp_bitmap *b, const int16_t *lo, const int16_t *hi, int32_t start, int32_t length)
{
    int32_t peak = 1, c, y, s, e, end = start + length > SMP_SPAN ? SMP_SPAN : start + length;

    for (c = 0; c < SMP_COLUMNS; c++) {
        if (lo[c] > hi[c])
            continue;
        if (-lo[c] > peak)
            peak = -lo[c];
        if (hi[c] > peak)
            peak = hi[c];
    }
    s = start * SMP_COLUMNS / SMP_SPAN;                 /* the column of the first frame played */
    e = (end * SMP_COLUMNS + SMP_SPAN - 1) / SMP_SPAN;  /* past the column of the last one */
    for (c = 0; c < SMP_COLUMNS; c++) {
        int32_t top, bottom, in = c >= s && c < e;

        if (lo[c] > hi[c])
            continue;
        top = WAVE_MID + hi[c] * WAVE_HALF / peak;
        bottom = WAVE_MID + lo[c] * WAVE_HALF / peak;
        for (y = bottom; y <= top; y++)
            if (in || quarter(c, y))
                pixel(b, c, y);
    }
    for (y = WAVE_MID - WAVE_HALF; y <= WAVE_MID + WAVE_HALF; y++) {
        pixel(b, s < SMP_COLUMNS ? s : SMP_COLUMNS - 1, y);   /* Start 120: at the very end */
        if (!(y & 1) && e > s)
            pixel(b, e - 1, y);
    }
}

void smp_view_draw(smp_bitmap *b, const char *sound)
{
    const int16_t *lo = 0, *hi = 0;
    uint32_t id = smp_sound_id(sound);
    char name[17], pattern[4];
    int i, state;

    blank(b);
    for (i = 0; i < 16 && sound[SOUND_NAME + i]; i++)
        name[i] = sound[SOUND_NAME + i];
    name[i] = 0;
    pattern_number(pattern);
    box(b, PATTERN_X0, PATTERN_X1, pattern);
    box(b, NAME_X0, NAME_X1, id ? name : 0);    /* without a sample, the name is still the sound's old one */
    state = smp_view_state(id, &lo, &hi);
    if (!id)
        label(b, FONT_MEDIUM, 64, TEXT_Y, 2, "NO SAMPLE");
    else if (state == SLOT_READY)
        waveform(b, lo, hi, sound_span(sound, SOUND_COLOR), sound_span(sound, SOUND_SHAPE));
    else if (state == SLOT_FAILED)
        label(b, FONT_MEDIUM, 64, TEXT_Y, 2, "NOT FOUND");
    else
        label(b, FONT_MEDIUM, 64, TEXT_Y, 2, "LOADING");
}

/* The selected track's live sound, if it plays SAMPLE. */
static const char *sample_sound(void)
{
    int32_t t = selected_track();
    const char *s;

    if (t < 0 || t > 5)
        return 0;
    s = os_sound(t);
    return s && (unsigned char)s[MACHINE_AT] == SAMPLE_MACHINE ? s : 0;
}

void smp_main_draw(void *view, smp_bitmap *b)
{
    const char *s = sample_sound();

    if (s && !VALUE_SHOWN())
        smp_view_draw(b, s);
    else
        MAIN_DRAW(view, b);
}

void smp_knob_draw(void *view, smp_bitmap *b)
{
    const char *s = sample_sound();
    int32_t p = KNOB_PARAM(view);

    if (s && VALUE_SHOWN() && !TRIG_HELD() && (p == DESC_START || p == DESC_LENGTH))
        smp_view_draw(b, s);
    else
        KNOB_DRAW(view, b);
}

/* --- Cutoff's value ------------------------------------------------------------------------- */

/* Cutoff shows -64..63 as on the Model:Samples: the lowpass side below zero, 0 off, the highpass
   side above. SAMPLE's descriptors share SNARE's parameter objects, so the formatter asks whether
   the selected track plays SAMPLE and otherwise writes the stock 0..127. value is the 8.8 word. */
int32_t smp_fmt_cutoff(void *self, int32_t value, char *buf)
{
    int32_t v = (value >> 8) - 64, n = 0;
    char digits[4];
    int i = 0;

    if (!sample_sound())
        return FMT_INT(self, value, buf);
    if (v < 0) {
        buf[n++] = '-';
        v = -v;
    }
    do {
        digits[i++] = (char)('0' + v % 10);
        v /= 10;
    } while (v);
    while (i)
        buf[n++] = digits[--i];
    buf[n] = 0;
    return n;
}

/* Puts smp_fmt_cutoff into the shared object, once the OS has built it with the stock formatter
   in place (anything else there is left alone). The tick calls this; it is done after the first
   screen redraw. */
void smp_view_install(void)
{
    static int done;

    if (done)
        return;
    if (UI_FORMATTER(CUTOFF_OBJECT) == FMT_INT) {
        UI_FORMATTER(CUTOFF_OBJECT) = smp_fmt_cutoff;
        done = 1;
    }
}
