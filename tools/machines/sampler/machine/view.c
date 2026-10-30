/* SAMPLE's view on the main screen: on the left a column with the current pattern's number, the
   track's number and its level; to its right the selected track's sample as a waveform, the start
   and end of what a trig plays marked on it, and above it the sound's name (the browser names the
   sound after the sample it opens).

   It takes the place of MainScreenView while that shows the track, and of the knob view while that
   shows Start or Length (COLOR or SHAPE), so the markers follow those two knobs as they turn. Any
   other knob shows its value as before. While a trig is held, the OS's NoteVelocityView covers the
   left half with the trig's note, velocity and length; when Start or Length turns then, the view
   takes the whole screen as without a held trig, its markers on the held trig's locks and its sample
   and name a sound lock's, and NoteVelocityView stays away until the value is gone. Tracks on other
   machines keep the stock views. In builds with the switches (SMP_SWITCHES), the name's box ends with
   L while Loop is on and R while Reverse is. */
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

/* The screen, y counted from the bottom (a set pixel is lit). On the left a column 21 pixels wide
   and as high as the screen, its marks lit: at the top the current pattern's number, dark in a lit
   box; below it a box with TRAK and the track's number; at the bottom the track's level as a bar in
   a frame with ticks. To its right, 2 dark columns on, the name's box along the top in the
   look of the OS's own browser title (0x400a539c: its title in the small font at 2, 53, then
   0x40070efc turns rows 51..63 over): lit, 13 rows high, its corners rounded off, the name in dark
   letters 2 pixels in, 101 pixels for a name of 15 characters, 89 at most. The OS's text is 9 rows
   high from the y it is given, capitals included, so the name has 2 rows of box above and below.
   The waveform below the name, its SMP_COLUMNS columns (pool.h) from the same column on. */
#define BAR_TOP     63                  /* the top boxes' highest row, the screen's top */
#define BAR_Y       (BAR_TOP - 12)      /* their lowest, 13 rows down */
#define COL_X0      0                   /* the column */
#define COL_X1      20
#define COL_MID     ((COL_X0 + COL_X1) / 2)
#define TRACK_Y0    29                  /* the track's box, rows 29..48 */
#define TRACK_Y1    48
#define METER_X0    6                   /* the level's frame, rows 0..26 */
#define METER_X1    14
#define METER_Y1    26
#define METER_ROWS  23                  /* its bar: rows 2..24 at most, columns 8..12 */
#define NAME_X0     (COL_X1 + 3)
#define NAME_X1     127
#define NAME_Y      (BAR_Y + 2)         /* the name's text, small font */
#define WAVE_X0     NAME_X0             /* the waveform's first column */
#define WAVE_MID    25                  /* its zero line */
#define WAVE_HALF   24                  /* rows above and below it: 1..49, a free row under the bar */
#define TEXT_X      (WAVE_X0 + SMP_COLUMNS / 2)
#define TEXT_Y      (WAVE_MID - 4)      /* a message instead of the waveform, medium font, centred */
#define SWITCH_X    119                 /* the switches' letters at the box's right end, 3 x 5 each: L at
                                           119..121, R at 123..125, past the longest name (25..113) */
#define SWITCH_TOP  (BAR_TOP - 4)       /* rows 55..59, the box's middle */

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

static void dark(smp_bitmap *b, int x, int y)
{
    if ((unsigned)x < (unsigned)b->width && (unsigned)y < (unsigned)b->height)
        b->words[x * b->pitch + (y >> 5)] &= ~(0x80000000u >> (y & 31));
}

/* Every pixel from (x0, y0) to (x1, y1), lit or dark. */
static void fill(smp_bitmap *b, int x0, int y0, int x1, int y1, int lit)
{
    int x, y;

    for (x = x0; x <= x1; x++)
        for (y = y0; y <= y1; y++)
            if (lit)
                pixel(b, x, y);
            else
                dark(b, x, y);
}

/* A lit outline from (x0, y0) to (x1, y1), its corner pixels left dark. */
static void frame(smp_bitmap *b, int x0, int y0, int x1, int y1)
{
    fill(b, x0 + 1, y0, x1 - 1, y0, 1);
    fill(b, x0 + 1, y1, x1 - 1, y1, 1);
    fill(b, x0, y0 + 1, x0, y1 - 1, 1);
    fill(b, x1, y0 + 1, x1, y1 - 1, 1);
}

/* The column's own letters, not the OS's: digits and A to F of 5 x 7 pixels in the shapes of the
   classic character LCD, a row per byte from the top, bit 4 the leftmost column; and TRAK of 3 x 5. */
static const unsigned char DIGITS[16][7] = {
    {0x0e, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0e}, {0x04, 0x0c, 0x04, 0x04, 0x04, 0x04, 0x0e},
    {0x0e, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1f}, {0x1f, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0e},
    {0x02, 0x06, 0x0a, 0x12, 0x1f, 0x02, 0x02}, {0x1f, 0x10, 0x1e, 0x01, 0x01, 0x11, 0x0e},
    {0x06, 0x08, 0x10, 0x1e, 0x11, 0x11, 0x0e}, {0x1f, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08},
    {0x0e, 0x11, 0x11, 0x0e, 0x11, 0x11, 0x0e}, {0x0e, 0x11, 0x11, 0x0f, 0x01, 0x02, 0x0c},
    {0x0e, 0x11, 0x11, 0x11, 0x1f, 0x11, 0x11}, {0x1e, 0x11, 0x11, 0x1e, 0x11, 0x11, 0x1e},
    {0x0e, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0e}, {0x1c, 0x12, 0x11, 0x11, 0x11, 0x12, 0x1c},
    {0x1f, 0x10, 0x10, 0x1e, 0x10, 0x10, 0x1f}, {0x1f, 0x10, 0x10, 0x1e, 0x10, 0x10, 0x10},
};
static const unsigned char TRAK[4][5] = {
    {7, 2, 2, 2, 2}, {6, 5, 6, 5, 5}, {2, 5, 7, 5, 5}, {5, 5, 6, 5, 5},
};

/* The columns a glyph uses: from bit 4 - first to bit 4 - last; blank columns at its sides are left
   out, so 1 is 3 pixels wide. */
static int glyph_span(const unsigned char *g, int *first)
{
    int bits = 0, r, lo = 0, hi = 4;

    for (r = 0; r < 7; r++)
        bits |= g[r];
    while (lo < 4 && !(bits & (0x10 >> lo)))
        lo++;
    while (hi > lo && !(bits & (0x10 >> hi)))
        hi--;
    *first = lo;
    return hi - lo + 1;
}

/* A text of digits and A to F centred on column mid, 1 pixel between characters, top row at top. */
static void digits(smp_bitmap *b, int mid, int top, const char *s, int lit)
{
    const unsigned char *g;
    int width = -1, x, first, w, r, c, i;

    for (i = 0; s[i]; i++)
        width += glyph_span(DIGITS[s[i] <= '9' ? s[i] - '0' : s[i] - 'A' + 10], &first) + 1;
    x = mid - (width - 1) / 2;
    for (i = 0; s[i]; i++) {
        g = DIGITS[s[i] <= '9' ? s[i] - '0' : s[i] - 'A' + 10];
        w = glyph_span(g, &first);
        for (r = 0; r < 7; r++)
            for (c = 0; c < w; c++)
                if (g[r] & (0x10 >> (first + c))) {
                    if (lit)
                        pixel(b, x + c, top - r);
                    else
                        dark(b, x + c, top - r);
                }
        x += w + 1;
    }
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

/* The switches that are on, their letters lit for box() to turn dark with the name: L for Loop, R for
   Reverse, each in its own place. */
static void switch_letters(smp_bitmap *b, const char *sound)
{
#ifdef SMP_SWITCHES
    static const unsigned char LETTERS[2][5] = { {4, 4, 4, 4, 7}, {6, 5, 6, 5, 5} };   /* L, R, as TRAK */
    uint32_t sw = *(const uint16_t *)(sound + SOUND_K32);
    int i, r, c;

    for (i = 0; i < 2; i++)
        if (sw & (i ? SW_REVERSE : SW_LOOP))
            for (r = 0; r < 5; r++)
                for (c = 0; c < 3; c++)
                    if (LETTERS[i][r] & (4 >> c))
                        pixel(b, SWITCH_X + 4 * i + c, SWITCH_TOP - r);
#else
    (void)b;
    (void)sound;
#endif
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

/* The column for track t (0..5), lit marks on the dark screen. The pattern's box fills rows 51..63
   but its corners, as the name's box does, its number dark in it (rows 54..60). The track's box is
   an outline with TRAK (rows 41..45) and the track's number (rows 32..38). The level's frame has 4
   ticks on each side (rows 1, 9, 17, 25), and its bar grows from row 2 with the track's level as
   MainScreenView reads it: 0 empty, any other value at least a row, 127 all 23. */
static void column(smp_bitmap *b, int32_t t)
{
    char s[4];
    int32_t level = t >= 0 && t <= 5 ? track_level(t) : 0, rows;
    int i, r, c;

    fill(b, COL_X0, BAR_Y, COL_X1, BAR_TOP, 1);
    dark(b, COL_X0, BAR_Y);
    dark(b, COL_X1, BAR_Y);
    dark(b, COL_X0, BAR_TOP);
    dark(b, COL_X1, BAR_TOP);
    pattern_number(s);
    digits(b, COL_MID, BAR_TOP - 3, s, 0);

    frame(b, COL_X0, TRACK_Y0, COL_X1, TRACK_Y1);
    for (i = 0; i < 4; i++)
        for (r = 0; r < 5; r++)
            for (c = 0; c < 3; c++)
                if (TRAK[i][r] & (4 >> c))
                    pixel(b, COL_MID - 7 + 4 * i + c, TRACK_Y1 - 3 - r);
    if (t >= 0 && t <= 5) {
        s[0] = (char)('1' + t);
        s[1] = 0;
        digits(b, COL_MID, TRACK_Y0 + 9, s, 1);
    }

    frame(b, METER_X0, 0, METER_X1, METER_Y1);
    for (i = 0; i < 4; i++) {
        fill(b, COL_X0 + 1, 1 + 8 * i, COL_X0 + 3, 1 + 8 * i, 1);
        fill(b, COL_X1 - 3, 1 + 8 * i, COL_X1 - 1, 1 + 8 * i, 1);
    }
    rows = level <= 0 ? 0 : 1 + (level > 127 ? 126 : level - 1) * (METER_ROWS - 1) / 126;
    if (rows)
        fill(b, METER_X0 + 2, 2, METER_X1 - 2, 1 + rows, 1);
}

static int32_t clamp_span(int32_t k)                  /* 8.8 word -> 0..SMP_SPAN, fraction kept */
{
    return k < 0 ? 0 : k > SMP_SPAN ? SMP_SPAN : k;
}

static int32_t sound_span(const char *sound, int at)
{
    return clamp_span(*(const int16_t *)(sound + at));
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
                pixel(b, WAVE_X0 + c, y);
    }
    for (y = WAVE_MID - WAVE_HALF; y <= WAVE_MID + WAVE_HALF; y++) {
        pixel(b, WAVE_X0 + (s < SMP_COLUMNS ? s : SMP_COLUMNS - 1), y);   /* Start 120: at the very end */
        if (!(y & 1) && e > s)
            pixel(b, WAVE_X0 + e - 1, y);
    }
}

/* The view of sound with start and length (0..SMP_SPAN) marked. */
static void draw_view(smp_bitmap *b, const char *sound, int32_t start, int32_t length)
{
    const int16_t *lo = 0, *hi = 0;
    uint32_t id = smp_sound_id(sound);
    char name[17];
    int i, state;

    blank(b);
    for (i = 0; i < 16 && sound[SOUND_NAME + i]; i++)
        name[i] = sound[SOUND_NAME + i];
    name[i] = 0;
    switch_letters(b, sound);
    box(b, NAME_X0, NAME_X1, id ? name : 0);    /* without a sample, the name is still the sound's old one */
    column(b, selected_track());
    state = smp_view_state(id, &lo, &hi);
    if (!id)
        label(b, FONT_MEDIUM, TEXT_X, TEXT_Y, 2, "NO SAMPLE");
    else if (state == SLOT_READY)
        waveform(b, lo, hi, start, length);
    else if (state == SLOT_FAILED)
        label(b, FONT_MEDIUM, TEXT_X, TEXT_Y, 2, "NOT FOUND");
    else
        label(b, FONT_MEDIUM, TEXT_X, TEXT_Y, 2, "LOADING");
}

void smp_view_draw(smp_bitmap *b, const char *sound)
{
    draw_view(b, sound, sound_span(sound, SOUND_COLOR), sound_span(sound, SOUND_SHAPE));
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

/* --- with a trig held ------------------------------------------------------------------------- */

/* What the held trigs play while Start or Length (param) turns, found the way the knob view finds
   the value it shows (0x4001e40a through 0x4006be48 and 0x4001d66e): the first held step with a lock
   of param or a sound lock; without one, the track's sound and its own values. A step's sound is
   its sound lock's, if it has one; where the step has no lock of Start or Length, that sound's own
   value stands (0x4001e160). Values are 8.8 words. */
typedef struct {
    const char *sound;
    int32_t start, length;
} smp_held;

static void find_held(int32_t param, const char *track_sound, smp_held *h)
{
    int32_t n, count = step_count(), start = -1, length = -1, pool = -1;

    for (n = 0; n < count; n++) {
        if (!step_held(n))
            continue;
        start = step_lock(n, DESC_START);
        length = step_lock(n, DESC_LENGTH);
        pool = step_sound_lock(n);
        if (pool != -1 || (param == DESC_START ? start : length) != -1)
            break;
    }
    if (n >= count)
        start = length = pool = -1;
    h->sound = pool >= 0 ? os_pool_sound(pool) : track_sound;
    h->start = start;
    h->length = length;
    if (h->sound && start == -1)
        h->start = *(const int16_t *)(h->sound + SOUND_COLOR);
    if (h->sound && length == -1)
        h->length = *(const int16_t *)(h->sound + SOUND_SHAPE);
}

/* Set while the knob view shows SAMPLE's view for a held trig. The OS draws every view on each
   redraw, the knob view before NoteVelocityView, so this is new for each one. */
static int held_shown;

void smp_knob_draw(void *view, smp_bitmap *b)
{
    const char *s = sample_sound();
    int32_t p = KNOB_PARAM(view);
    smp_held h;

    held_shown = 0;
    if (!s || !VALUE_SHOWN() || (p != DESC_START && p != DESC_LENGTH)) {
        KNOB_DRAW(view, b);
        return;
    }
    if (!TRIG_HELD()) {
        smp_view_draw(b, s);
        return;
    }
    find_held(p, s, &h);
    if (!h.sound || (unsigned char)h.sound[MACHINE_AT] != SAMPLE_MACHINE) {
        KNOB_DRAW(view, b);                     /* a sound lock of another machine */
        return;
    }
    draw_view(b, h.sound, clamp_span(h.start), clamp_span(h.length));
    held_shown = 1;
}

void smp_note_draw(void *view, smp_bitmap *b)
{
    if (!held_shown || !TRIG_HELD() || !VALUE_SHOWN())
        NOTE_DRAW(view, b);
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
