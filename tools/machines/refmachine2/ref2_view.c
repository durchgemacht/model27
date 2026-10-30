/* REF2's views and UI hooks (notes/63 §2, steps B4c and B4d, §22): the template for a machine that draws on the main
   screen, in the knob view and over a held trig's note, runs on the screen's tick and hears of the files the browser
   opens, next to another machine that does too (SAMPLE).

   - ref2_main_draw takes the place of MainScreenView's draw (vtable entry 0x400ffe30, stock 0x4001b22a). On a
     REF2 track it draws the stock main screen, then the Octave as "OCT +1" in the free band of its right half, with a
     dot that blinks with the tick, and left of it the switches that are on (notes/63 §16): "S" Square (RETRIG +
     PUNCH), "O" Tone open (RETRIG + GATE), "SO" both; for a few redraws after the browser opened a file on that
     track, the file's name instead.
   - ref2_knob_draw takes the place of the knob view's draw (vtable entry 0x4010053c, stock 0x4001e40a). While
     RETRIG + COLOR turns the Octave on a REF2 track, it draws the Octave as five boxes, -2 to +2, the current one
     filled; any other value shows as before.
   - ref2_note_draw takes the place of NoteVelocityView's draw (vtable entry 0x40102578, stock 0x400299de), which
     shows a held trig's note, velocity and length over the left half while a trig is held: on a REF2 track it draws
     that, then turns over a 2 x 2 mark in the panel's lower right corner, x 58..59, rows 3..4 (notes/63 §22).
   - ref2_hook_tick takes the place of jsr 0x40076be4 at 0x400075f0, in the screen's redraw (about 30 times a
     second): it counts the ticks, asks the main screen for a redraw when the dot changes on a REF2 track, and returns
     0x40076be4(view), the getter it replaces.
   - ref2_hook_open (ref2_open.S) takes the place of jsr 0x400a3052 at 0x400a6602, where the browser reads the file
     it opens: on a REF2 track it keeps the file's name (ref2_open_track, ref2_open_name), then the stock code opens
     the file as before (REF2 takes no file).

   A build with REF2 alone writes these entries and hooks; a build in which another machine takes them too goes through
   the builder's dispatchers (tools/machines/dispatch/), which call the draws and the browser's hook for REF2 tracks
   only and every tick. Either way each one checks the track itself and does the stock work otherwise, as SAMPLE's do.

   The screen is 128 x 64, y = 0 at the bottom. The stock main screen (0x4001b22a): the left half a lit panel with the
   track's lines; the right half dark, "TRn" centred at x 96 on rows 34..42, the pan bar on rows 21..29, the level bar
   on rows 8..16, and while 0x40a744c8 is set a sign at x 65, rows 58..; rows 44..56 of the right half are free, and
   the label takes rows 46..54 (x 79..113 for "OCT +1"), the switches x 65..77 on the same rows, the dot x 120..121,
   rows 49..50. Plain C99, no libc. */
#include <stdint.h>

typedef int32_t s32;
typedef int16_t s16;
typedef uint32_t u32;

/* The build's machine number for REF2, a patch point the composer resolves (its value is the symbol's address). */
extern char ref2_machine_index[];
#define REF2_MACHINE    ((s32)(long)ref2_machine_index)
#define OCT_DESCRIPTOR  1                   /* RETRIG + COLOR, the builder's first shortcut (notes/63 §3.2) */
#define SOUND_OCT       76                  /* sound: k 28, the Octave, 8.8, signed */
#define SOUND_SW        84                  /* sound: k 32, the switches: 0x100 Square, 0x200 Tone open */
#define MACHINE_AT      38                  /* sound: k 9's high byte, the machine */

/* The OS, as SAMPLE's machine/os.h reads it. */
#define MAIN_DRAW(v, b)     ((void (*)(void *, void *))0x4001b22a)(v, b)
#define KNOB_DRAW(v, b)     ((void (*)(void *, void *))0x4001e40a)(v, b)
#define NOTE_DRAW(v, b)     ((void (*)(void *, void *))0x400299de)(v, b)      /* draws only while a trig is held */
#define KNOB_PARAM(v)       (*(const s32 *)((const char *)(v) + 0x230))     /* the shown parameter's descriptor */
#define UI_STATE()          ((void *(*)(void))0x400cf9a8)()
#define VALUE_SHOWN()       (((char (*)(void *))0x4006b704)(UI_STATE()) != 0)   /* UIStates + 88 */
#define TRIG_HELD()         (((char (*)(void *))0x4006b736)(UI_STATE()) != 0)   /* UIStates + 356 */
#define FONT_MAKE(f, g)     ((void (*)(void *, const void *))0x40072260)(f, g)
#define FONT_DROP(f)        ((void (*)(void *))0x40072080)(f)
#define FONT_SMALL          ((const void *)0x40140ab0)                      /* 5 x 9 pixels */
#define FONT_MEDIUM         ((const void *)0x4014120c)                      /* 7 x 9 pixels */
#define DRAW_TEXT           ((void (*)(void *, void *, s32, s32, s32, const char *, ...))0x40071a04)
/* View::setNeedsRedraw (0x40076082): the view's byte +20, then its screen's +32; MainScreenView's 1 Hz timer calls it
   (0x4001bffc). 0x40076be4(view) reads the screen's +32: whether it needs drawing. */
#define NEEDS_REDRAW(v)     ((void (*)(void *))0x40076082)(v)
#define TICK_STOCK(v)       ((u32 (*)(void *))0x40076be4)(v)

/* A Bitmap (constructor 0x40070172): pixel (x, y) is bit 31 - (y & 31) of word x * pitch + y / 32. */
struct bitmap {
	const void *vtable;
	s32 width, height, pitch;
	u32 *words;
};

#define LABEL_X     96                      /* centred in the right half */
#define LABEL_Y     46                      /* rows 46..54 */
#define SW_X        71                      /* the switches, centred left of the label: x 65..77 */
#define DOT_X       120                     /* the dot: x 120..121, rows 49..50 */
#define DOT_Y       49
#define DOT_TICKS   16                      /* the dot changes every 16 ticks, about half a second */
#define MARK_X      58                      /* the held trig's mark: x 58..59, rows 3..4, in NoteVelocityView's panel */
#define MARK_Y      3
#define NAME_DRAWS  6                       /* the opened file's name stays for 6 redraws, about 3 s */
#define NAME_CHARS  10                      /* as many as the band holds */

static u32 ticks;                           /* the screen's ticks, counted by ref2_hook_tick */
static void *main_view;                     /* MainScreenView, as its draw last got it */
static char file_name[16];                  /* the file the browser last opened on a REF2 track */
static s32 file_track = -1, file_draws;     /* its track; the main screen's redraws left that show it */

/* Track t's live sound, if it plays REF2: the project singleton's track + 212 + t * 68, then the method at +40 of
   its vtable (SAMPLE's os_sound). */
static const char *ref2_sound_of(s32 t)
{
	char *project = ((char *(*)(void))0x400cf866)();
	char *track;
	void **vt;
	const char *s;

	if (!project || t < 0 || t > 5)
		return 0;
	track = project + 212 + t * 68;
	vt = *(void ***)track;
	s = vt && vt[10] ? ((const char *(*)(char *))vt[10])(track) : 0;
	return s && (unsigned char)s[MACHINE_AT] == REF2_MACHINE ? s : 0;
}

static s32 selected_track(void)             /* 0x40012412(0x4000eb90(project)), SAMPLE's selected_track */
{
	char *project = ((char *(*)(void))0x400cf866)();

	return project ? ((s32 (*)(void *))0x40012412)(((void *(*)(void *))0x4000eb90)(project)) : -1;
}

static s32 octave(const char *s)                /* k 28 as the voice reads it: -2 .. +2 */
{
	s32 v = *(const s16 *)(s + SOUND_OCT) >> 8;

	return v < -2 ? -2 : (v > 2 ? 2 : v);
}

static void text(struct bitmap *b, const void *glyphs, s32 x, s32 y, const char *s)    /* centred on x */
{
	u32 font[2];

	FONT_MAKE(font, glyphs);
	DRAW_TEXT(b, font, x, y, 2, "%s", s);
	FONT_DROP(font);
}

static void signed_digit(char *out, s32 v)     /* "-2" .. "+2", "0" */
{
	int n = 0;

	if (v)
		out[n++] = v < 0 ? '-' : '+';
	out[n++] = (char)('0' + (v < 0 ? -v : v));
	out[n] = 0;
}

static void pixel(struct bitmap *b, s32 x, s32 y)
{
	if ((u32)x < (u32)b->width && (u32)y < (u32)b->height)
		b->words[x * b->pitch + (y >> 5)] |= 0x80000000u >> (y & 31);
}

void ref2_main_draw(void *view, void *b)
{
	s32 t = selected_track();
	const char *s = ref2_sound_of(t);
	char label[NAME_CHARS + 1];
	int i;

	main_view = view;
	MAIN_DRAW(view, b);                     /* draws nothing while a value window is open */
	if (!s || VALUE_SHOWN())
		return;
	if (file_draws > 0 && t == file_track) {
		file_draws--;
		for (i = 0; i < NAME_CHARS && file_name[i]; i++)
			label[i] = file_name[i];
		label[i] = 0;
		text(b, FONT_SMALL, LABEL_X, LABEL_Y, label);
		return;
	}
	label[0] = 'O';                         /* "OCT " by hand: an initialised array may become a memcpy call */
	label[1] = 'C';
	label[2] = 'T';
	label[3] = ' ';
	signed_digit(label + 4, octave(s));
	text(b, FONT_SMALL, LABEL_X, LABEL_Y, label);
	i = 0;                                  /* the switches that are on, k 32 */
	if (*(const s16 *)(s + SOUND_SW) & 0x100)
		label[i++] = 'S';
	if (*(const s16 *)(s + SOUND_SW) & 0x200)
		label[i++] = 'O';
	label[i] = 0;
	if (i)
		text(b, FONT_SMALL, SW_X, LABEL_Y, label);
	if ((ticks / DOT_TICKS) & 1) {
		pixel(b, DOT_X, DOT_Y);
		pixel(b, DOT_X + 1, DOT_Y);
		pixel(b, DOT_X, DOT_Y + 1);
		pixel(b, DOT_X + 1, DOT_Y + 1);
	}
}

/* --- the knob view: OCTAVE, then five boxes 16 pixels wide, 8 apart, the current one filled, each value under its box */
#define BOX_W       16
#define BOX_STEP    24
#define BOX_LEFT    8                       /* (128 - 5 * 16 - 4 * 8) / 2 */
#define BOX_BOTTOM  20
#define BOX_TOP     35

static void blank(struct bitmap *b)
{
	s32 i, n = b->width * b->pitch;

	for (i = 0; i < n; i++)
		b->words[i] = 0;
}

static void box(struct bitmap *b, s32 x0, s32 filled)
{
	s32 x, y, x1 = x0 + BOX_W - 1;

	for (x = x0; x <= x1; x++)
		for (y = BOX_BOTTOM; y <= BOX_TOP; y++)
			if (filled || x == x0 || x == x1 || y == BOX_BOTTOM || y == BOX_TOP)
				pixel(b, x, y);
}

static void octave_view(struct bitmap *b, s32 oct)
{
	char digit[4];
	s32 v;

	blank(b);
	text(b, FONT_MEDIUM, 64, 50, "OCTAVE");
	for (v = -2; v <= 2; v++) {
		s32 x0 = BOX_LEFT + (v + 2) * BOX_STEP;

		box(b, x0, v == oct);
		signed_digit(digit, v);
		text(b, FONT_SMALL, x0 + BOX_W / 2, 6, digit);
	}
}

void ref2_knob_draw(void *view, void *b)
{
	const char *s = ref2_sound_of(selected_track());

	if (s && VALUE_SHOWN() && !TRIG_HELD() && KNOB_PARAM(view) == OCT_DESCRIPTOR)
		octave_view(b, octave(s));
	else
		KNOB_DRAW(view, b);
}

void ref2_note_draw(void *view, void *b)
{
	struct bitmap *bm = b;
	s32 x, y;

	NOTE_DRAW(view, b);
	if (!ref2_sound_of(selected_track()) || !TRIG_HELD())
		return;
	for (x = MARK_X; x <= MARK_X + 1; x++)
		for (y = MARK_Y; y <= MARK_Y + 1; y++)
			bm->words[x * bm->pitch + (y >> 5)] ^= 0x80000000u >> (y & 31);
}

/* --- the tick and the browser (step B4d) ------------------------------------------------------------------------ */

u32 ref2_hook_tick(void *view)
{
	ticks++;
	if (!(ticks % DOT_TICKS) && main_view && ref2_sound_of(selected_track()) && !VALUE_SHOWN())
		NEEDS_REDRAW(main_view);            /* so that the dot's change shows */
	return TICK_STOCK(view);
}

/* ref2_open.S asks whether the browser opens a file on a REF2 track, then hands over the entry's name: the
   browser's std::string, a pointer to its characters. */
s32 ref2_open_track(s32 t)
{
	if (!ref2_sound_of(t))
		return 0;
	file_track = t;
	return 1;
}

void ref2_open_name(char *const *name)
{
	const char *p = *name;
	int i;

	for (i = 0; i < (int)sizeof(file_name) - 1 && p && p[i]; i++)
		file_name[i] = p[i];
	file_name[i] = 0;
	file_draws = NAME_DRAWS;
}
