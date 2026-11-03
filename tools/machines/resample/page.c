/* The RESAMPLE page (notes/79 §2; step R2), with resample.c and entries.S. Addresses are VAs of OS 1.13.
 *
 * Opening: entries.S's hook at 0x40024482, TransportView's toggle of GRID RECORDING on a fresh press of RECORD
 * (0x4002439a, without FUNC; PatternGridView keeps RECORD with PAGE or a held step for Copy Page and Copy Trigs), calls
 * rs_key with the UIStates: with SETTINGS held the page opens and GRID RECORDING stays as it was; else the two stock
 * calls (0x4006ba90(uis, 0), the toggle 0x4006ba20(uis)). SETTINGS is held when isKeyHeld(13) says so or its events
 * do (entries.S's rs_code, the key code accessor's hook): on the device isKeyHeld alone missed it (notes/79 §10.1).
 * The release of SETTINGS after RECORD is not a tap, so the settings menu stays closed (notes/79 §1).
 *
 * The page is the stock machine-select page with its first two vtable pointers at a private copy of its vtable group,
 * as the CPU page builds its own (tools/machines/cpu/, notes/78 §2 and §9; Model-TG's System page, TinyGregAudio, MIT):
 * ours are the destructors (entries.S: forget the page, then the stock ones), the key handler, the render, the periodic
 * method and the encoder handler. Keys: RECORD arms, cancels or ends the take, and on a finished one asks for the name
 * editor; RETURN (a tap) and SETTINGS + RECORD close the page (an armed take dropped, a finished one too), but while
 * recording they end the take; every other key goes to the stock view's dispatch (0x40075f3c), as the machine page
 * passes PUNCH and GATE on, so that a held trig + PAGE reaches PatternGridView and Trig Preview plays under the page.
 * Knobs, while idle: PITCH SOURCE, DECAY START, COLOR THRESH, SHAPE STEREO, SWEEP
 * STOP, CONTOUR LENGTH, DELAY SEND NORM, REVERB SEND TO Tn (notes/79 §2.3); DATA does nothing; the other knobs go to the
 * base (0x4006fb90), as on the stock page. A value that does not apply shows "---" and its knob changes nothing.
 *
 * The periodic method (the view stack's +0x2c, on the OS's timer, as the CPU page's): a redraw while armed or recording
 * (the meter, the seconds) and when the state changed since the last one. The render draws the whole screen in the OS's
 * small font (5 pixels a character, 9 rows) and its medium one (7, for the big line): notes/79 §2.4, the mockup laid on
 * the OS's fonts.
 *
 * When a take ends, the periodic method asks for the name editor once (save.c, in the UI task); confirmed, the take is
 * written (SAVING, its progress) and the page closes; backed out of, the page shows it as NOT SAVED, where RECORD asks
 * for the editor again and RETURN drops it (notes/79 §2.2, §11). While it is written, RECORD and RETURN do nothing.
 *
 * License: MIT (LICENSE next to this file; the page's mechanics follow Model-TG's, MIT, LICENSE-Model-TG). */
#include "resample.h"

#define VT_SRC ((const uint32_t *)0x40117918)       /* the machine-select page's vtable group, 0xb0 bytes */
#define VT_WORDS 44
#define VT_DTOR0 (0x08 / 4)                         /* the primary vtable starts at +0x08 of the group */
#define VT_DTOR1 (0x0c / 4)
#define VT_KEY (0x10 / 4)
#define VT_RENDER (0x18 / 4)
#define VT_TICK (0x34 / 4)                          /* +0x2c of the primary vtable: the view stack's periodic call */
#define VT_ENC (0x4c / 4)
#define VT_BASE4 (0x58 / 4)                         /* the +4 base's vtable: its two destructors, its encoder thunk */
#define VT_DTOR0_TH (0x58 / 4)
#define VT_DTOR1_TH (0x5c / 4)
#define VT_ENC_TH (0x60 / 4)
#define PAGE_SIZE 0xd0
#define NEW(n) ((void *(*)(uint32_t))0x400802e0)(n)                 /* operator new */
#define PAGE_CTOR(p) ((void (*)(void *))0x400a22b0)(p)              /* the machine-select page's constructor */
#define VIEWS_UP (*(void *const volatile *)0x40fe4178)            /* the view machinery's singleton, 0 before it is up */
#define VIEWS() ((char *(*)(void))0x400d0974)()                     /* ...its getter */
#define TARGET(v) ((void *(*)(void *))0x400060d8)(v)                /* the screen the pages go on: views + 64 */
#define PRESENT(t, pair, x) ((void (*)(void *, void *, uint32_t))0x4007700e)(t, pair, x)
#define DROP(ref) ((void (*)(void *))0x400cf23c)(ref)               /* a reference let go */
#define HOLDER_VT 0x401000c4u                       /* the reference holder's vtable, as the stock opener 0x4001ca40 */
#define KEY_CODE(e) ((int32_t (*)(void *))0x4007240c)(e)
#define KEY_PRESS(e) ((uint8_t (*)(void *))0x400724a0)(e)           /* a fresh press: bit 0, not bit 3 (repeat) */
#define KEY_CLICK(e) ((int32_t (*)(void *))0x40072434)(e)           /* a tap: the event's flag bit 4 */
#define KEY_HELD(c) ((int32_t (*)(int32_t))0x4007faf4)(c)          /* isKeyHeld */
#define KEY_STOCK(v, e) ((uint32_t (*)(void *, void *))0x40075f3c)(v, e)
#define ENC_BASE(v, e) ((uint32_t (*)(void *, void *))0x4006fb90)(v, e)
#define NEEDS_REDRAW(v) ((void (*)(void *))0x40076082)(v)          /* View::setNeedsRedraw */
#define GRID_PREP(u, x) ((void (*)(void *, uint32_t))0x4006ba90)(u, x)   /* UIStates +359 = x, then its observers */
#define GRID_TOGGLE(u) ((void (*)(void *))0x4006ba20)(u)                 /* GRID RECORDING on or off */
#define PROJECT() ((void *(*)(void))0x400cf866)()
#define PATTERN_OF(p) ((void *(*)(void *))0x4000eb90)(p)
#define TRACK_OF(p) ((uint32_t (*)(void *))0x40012412)(p)          /* the selected track, as Trig Preview finds it */
#define KIT_SOUNDS (*(uint8_t *const volatile *)0x800017e4)        /* the kit's working copy: sound t at +0x1c + 100 t */
#define K_RECORD 9
#define K_RETURN 12
#define K_SETTINGS 13
#define CLOSE_AT 0x28                               /* the view's close, in its primary vtable (0x40076126) */
#define LENGTH_MONO 40
#define LENGTH_STEREO 20

extern char rs_dtor0[], rs_dtor1[], rs_dtor0_th[], rs_dtor1_th[], rs_enc_th[];
uint32_t rs_page_key(void *page, void *event);
uint32_t rs_page_enc(void *page, void *event);
void rs_page_render(void *page, void *b);
void rs_page_tick(void *page);

/* SETTINGS held: the key bitmap's bit or, read in the events' order, its last event (set_held, entries.S's rs_code). */
static int settings_held(void)
{
	return KEY_HELD(K_SETTINGS) || D->set_held;
}

static uint32_t selected(void)
{
	return TRACK_OF(PATTERN_OF(PROJECT())) % 6u;
}

/* TO Tn applies: the build has SAMPLE and the selected track's sound plays it (the machine, k 9's high byte at +38). */
static int to_track_ok(void)
{
	const uint8_t *k = KIT_SOUNDS;
	return D->sample != 0xffu && k && k[0x1c + 100u * selected() + 38u] == D->sample;
}

static uint32_t length_most(void)
{
	return D->src_set >= SRC_MAIN && D->stereo_set ? LENGTH_STEREO : LENGTH_MONO;
}

/* START as it applies: USB has no trigger. */
static uint32_t start_of(void)
{
	return D->src_set == SRC_USB && D->start_set == START_TRIG ? START_LEVEL : D->start_set;
}

/* The page, unless it is up, the view machinery is not, or this is not the interface's thread. */
static void rs_open(void)
{
	uint32_t sr, *holder;
	char *page;
	void *pair[2];
	struct data *d = D;

	__asm__ volatile("move.w %%sr, %0" : "=d"(sr));
	if (sr & 0x0700 || d->page || !VIEWS_UP)
		return;
	if (!d->settled) {                          /* the first opening: the selected track, TRIG, -40 dB, 10 s */
		d->src_set = (uint8_t)selected();
		d->start_set = START_TRIG;
		d->thr_set = 40;
		d->stop_set = STOP_SILENT;
		d->length_set = 10;
		d->settled = 1;
	}
	for (int i = 0; i < VT_WORDS; i++)
		d->vt[i] = VT_SRC[i];
	d->vt[VT_DTOR0] = (uint32_t)rs_dtor0;
	d->vt[VT_DTOR1] = (uint32_t)rs_dtor1;
	d->vt[VT_KEY] = (uint32_t)rs_page_key;
	d->vt[VT_RENDER] = (uint32_t)rs_page_render;
	d->vt[VT_TICK] = (uint32_t)rs_page_tick;
	d->vt[VT_ENC] = (uint32_t)rs_page_enc;
	d->vt[VT_DTOR0_TH] = (uint32_t)rs_dtor0_th;
	d->vt[VT_DTOR1_TH] = (uint32_t)rs_dtor1_th;
	d->vt[VT_ENC_TH] = (uint32_t)rs_enc_th;
	page = NEW(PAGE_SIZE);
	if (!page)
		return;
	PAGE_CTOR(page);
	*(uint32_t **)page = &d->vt[VT_DTOR0];      /* the primary vtable */
	*(uint32_t **)(page + 4) = &d->vt[VT_BASE4];
	d->page = (uint32_t)page;
	d->drawn = 0xff;
	holder = NEW(16);
	holder[0] = HOLDER_VT;
	holder[1] = holder[2] = 1;
	holder[3] = (uint32_t)page;
	pair[0] = page;
	pair[1] = holder;
	PRESENT(TARGET(VIEWS()), pair, 0);
	DROP(&pair[1]);
}

/* entries.S's hook in TransportView's RECORD (0x40024482): the page with SETTINGS held, else the stock toggle. */
void rs_key(void *uis)
{
	if (settings_held()) {
		rs_open();
		return;
	}
	GRID_PREP(uis, 0);
	GRID_TOGGLE(uis);
}

/* The page closed by RETURN or SETTINGS + RECORD: an armed take dropped, a recording one ended and kept, a finished
   one dropped. */
static void close_page(void *page)
{
	switch (D->state) {
	case ARMED:
		rs_cancel();
		break;
	case REC:
		rs_stop();
		break;
	case TAKEN:
		rs_release();
		break;
	}
	(*(void (**)(void *))(*(char **)page + CLOSE_AT))(page);
}

uint32_t rs_page_key(void *page, void *event)
{
	struct data *d = D;
	int32_t code = KEY_CODE(event);
	int back;

	if (code != K_RETURN && code != K_RECORD)
		return KEY_STOCK(page, event);
	if (d->saving)                              /* nothing until the file is written */
		return 1;
	if (code == K_RETURN) {
		if (!KEY_CLICK(event))
			return 1;
		back = 1;
	} else {
		if (!KEY_PRESS(event))              /* its release and repeats: kept from the views below */
			return 1;
		back = settings_held();
	}
	if (back) {                                 /* RETURN's tap, SETTINGS + RECORD */
		if (d->state == REC)
			rs_stop();                  /* the take ends; the name editor follows */
		else {
			close_page(page);
			return 1;
		}
	} else
		switch (d->state) {
		case IDLE:
			d->asked = d->exists = 0;
			rs_arm(d->src_set, d->stereo_set, start_of(), d->stop_set, d->thr_set, d->length_set);
			break;
		case ARMED:
		case REC:
			rs_stop();
			break;
		case TAKEN:
			rs_ask_name();
			break;
		}
	NEEDS_REDRAW(page);
	return 1;
}

static int32_t clamp(int32_t v, int32_t lo, int32_t hi)
{
	return v < lo ? lo : v > hi ? hi : v;
}

/* A knob's turn of delta detents on setting k (0 SOURCE .. 7 TO Tn), while idle. */
static void turn(uint32_t k, int32_t delta)
{
	struct data *d = D;
	int32_t dir = delta > 0 ? 1 : -1;

	switch (k) {
	case 0:
		d->src_set = (uint8_t)((d->src_set + 8 + dir) % 8);
		break;
	case 1:
		if (d->src_set == SRC_USB)                 /* LEVEL, NOW */
			d->start_set = start_of() == START_LEVEL && dir > 0 ? START_NOW
			             : start_of() == START_NOW && dir < 0 ? START_LEVEL : (uint8_t)start_of();
		else
			d->start_set = (uint8_t)clamp(d->start_set + dir, START_TRIG, START_NOW);
		break;
	case 2:
		if (start_of() == START_LEVEL)
			d->thr_set = (uint8_t)clamp(d->thr_set - 3 * delta, 12, 60);
		break;
	case 3:
		if (d->src_set >= SRC_MAIN)
			d->stereo_set = dir > 0;
		break;
	case 4:
		d->stop_set = (uint8_t)clamp(d->stop_set + dir, STOP_SILENT, STOP_RECORD);
		break;
	case 5:
		d->length_set = (uint8_t)clamp(d->length_set + delta, 1, 40);
		break;
	case 6:
		d->norm_set = dir > 0;
		break;
	case 7:
		if (to_track_ok())
			d->to_track = dir > 0;
		break;
	}
	if (d->length_set > length_most())
		d->length_set = (uint8_t)length_most();
}

/* The page's encoder handler (entries.S's rs_enc_th from the +4 base). The event: +12 the knob (1 DATA, 2 PITCH ..
   9 REVERB SEND), +16 its detents, signed. */
uint32_t rs_page_enc(void *page, void *event)
{
	int32_t knob = *(const int32_t *)((char *)event + 12), delta = *(const int32_t *)((char *)event + 16);

	if (knob > 9)
		return ENC_BASE((char *)page + 4, event);
	if (knob >= 2 && delta && D->state == IDLE) {
		turn((uint32_t)knob - 2u, delta);
		NEEDS_REDRAW(page);
	}
	return 1;
}

void rs_page_tick(void *page)
{
	struct data *d = D;
	uint8_t s = d->state;

	if (s == TAKEN && !d->asked && !d->saving) {    /* a take has ended: the name editor, once */
		d->asked = 1;
		rs_ask_name();
	}
	if (s == ARMED || s == REC || d->saving || s != d->drawn) {
		d->drawn = s;
		NEEDS_REDRAW(page);
	}
}

/* --- the render: 128 x 64, a Bitmap (0x40070172) whose pixel (x, y), y from the bottom, is bit 31 - (y & 31) of word
   x * pitch + y / 32; rows here count from the screen's top. The text in the mockup's own pixel fonts (notes/79 §2.4,
   §10.2): 3 x 5 (4 pixels a character) for the labels, the state, the footer and the small lines, 4 x 7 (5) for the
   knobs' values, 5 x 7 (6) for the title and the big lines. The OS's smallest font is 5 x 9 at 6 pixels a character
   (its width + 1, 0x40072102): too wide for four columns of 32, and all of one size. */
struct bitmap {
	const void *vtable;
	int32_t width, height, pitch;
	uint32_t *words;
};

#define W 128
#define X1 125
#define ROW_FOOT 54

/* The glyphs, a row each from the top, the left pixel the highest bit: F3 three bits a row, F4 four, F5 a byte. */
static const char CHARS[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.:/%+> ";
static const uint16_t F3[44] = {
	0x2bed, 0x6bae, 0x3923, 0x6b6e, 0x79a7, 0x79a4, 0x396b, 0x5bed, 0x7497, 0x126a, 0x5bad,
	0x4927, 0x5fed, 0x6b6d, 0x2b6a, 0x6ba4, 0x2b7b, 0x6bad, 0x388e, 0x7492, 0x5b6f, 0x5b6a,
	0x5bfd, 0x5aad, 0x5a92, 0x72a7, 0x7b6f, 0x2c97, 0x62a7, 0x628e, 0x5bc9, 0x798e, 0x39ef,
	0x7292, 0x7bef, 0x7bce, 0x01c0, 0x0002, 0x0410, 0x12a4, 0x52a5, 0x05d0, 0x4454, 0x0000,
};
static const uint32_t F4[44] = {
	0x699f999, 0xe99e99e, 0x6988896, 0xe99999e, 0xf88e88f, 0xf88e888, 0x698b997, 0x999f999,
	0xe44444e, 0x72222a4, 0x9ac8ca9, 0x888888f, 0x9ff9999, 0x9ddbb99, 0x6999996, 0xe99e888,
	0x6999ba5, 0xe99eca9, 0x788611e, 0xe444444, 0x9999996, 0x9999966, 0x9999ff9, 0x9966699,
	0xaaa4444, 0xf12488f, 0x69bd996, 0x4c4444e, 0x691248f, 0xe11611e, 0x26aaf22, 0xf8e1196,
	0x688e996, 0xf122444, 0x6996996, 0x6997116, 0x000e000, 0x00000cc, 0x0000000, 0x0000000,
	0x0000000, 0x0000000, 0x0000000, 0x0000000,
};
static const uint8_t F5[44][7] = {
	{0x0e, 0x11, 0x11, 0x1f, 0x11, 0x11, 0x11},	/* A */
	{0x1e, 0x11, 0x11, 0x1e, 0x11, 0x11, 0x1e},	/* B */
	{0x0e, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0e},	/* C */
	{0x1c, 0x12, 0x11, 0x11, 0x11, 0x12, 0x1c},	/* D */
	{0x1f, 0x10, 0x10, 0x1e, 0x10, 0x10, 0x1f},	/* E */
	{0x1f, 0x10, 0x10, 0x1e, 0x10, 0x10, 0x10},	/* F */
	{0x0e, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0f},	/* G */
	{0x11, 0x11, 0x11, 0x1f, 0x11, 0x11, 0x11},	/* H */
	{0x0e, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0e},	/* I */
	{0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0c},	/* J */
	{0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11},	/* K */
	{0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1f},	/* L */
	{0x11, 0x1b, 0x15, 0x15, 0x11, 0x11, 0x11},	/* M */
	{0x11, 0x11, 0x19, 0x15, 0x13, 0x11, 0x11},	/* N */
	{0x0e, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0e},	/* O */
	{0x1e, 0x11, 0x11, 0x1e, 0x10, 0x10, 0x10},	/* P */
	{0x0e, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0d},	/* Q */
	{0x1e, 0x11, 0x11, 0x1e, 0x14, 0x12, 0x11},	/* R */
	{0x0f, 0x10, 0x10, 0x0e, 0x01, 0x01, 0x1e},	/* S */
	{0x1f, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04},	/* T */
	{0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0e},	/* U */
	{0x11, 0x11, 0x11, 0x11, 0x11, 0x0a, 0x04},	/* V */
	{0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0a},	/* W */
	{0x11, 0x11, 0x0a, 0x04, 0x0a, 0x11, 0x11},	/* X */
	{0x11, 0x11, 0x11, 0x0a, 0x04, 0x04, 0x04},	/* Y */
	{0x1f, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1f},	/* Z */
	{0x0e, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0e},	/* 0 */
	{0x04, 0x0c, 0x04, 0x04, 0x04, 0x04, 0x0e},	/* 1 */
	{0x0e, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1f},	/* 2 */
	{0x1f, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0e},	/* 3 */
	{0x02, 0x06, 0x0a, 0x12, 0x1f, 0x02, 0x02},	/* 4 */
	{0x1f, 0x10, 0x1e, 0x01, 0x01, 0x11, 0x0e},	/* 5 */
	{0x06, 0x08, 0x10, 0x1e, 0x11, 0x11, 0x0e},	/* 6 */
	{0x1f, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08},	/* 7 */
	{0x0e, 0x11, 0x11, 0x0e, 0x11, 0x11, 0x0e},	/* 8 */
	{0x0e, 0x11, 0x11, 0x0f, 0x01, 0x02, 0x0c},	/* 9 */
	{0x00, 0x00, 0x00, 0x1f, 0x00, 0x00, 0x00},	/* - */
	{0x00, 0x00, 0x00, 0x00, 0x00, 0x0c, 0x0c},	/* . */
	{0x00, 0x0c, 0x0c, 0x00, 0x0c, 0x0c, 0x00},	/* : */
	{0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x00},	/* / */
	{0x18, 0x19, 0x02, 0x04, 0x08, 0x13, 0x03},	/* % */
	{0x00, 0x04, 0x04, 0x1f, 0x04, 0x04, 0x00},	/* + */
	{0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00},	/* > */
	{0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00},	/*   */
};

struct font {
	int8_t w, h, adv, kind;
};

static const struct font T3 = {3, 5, 4, 3}, T4 = {4, 7, 5, 4}, T5 = {5, 7, 6, 5};

static void pixel(struct bitmap *b, int32_t x, int32_t row, int on)
{
	int32_t y = b->height - 1 - row;
	if ((uint32_t)x < (uint32_t)b->width && (uint32_t)y < (uint32_t)b->height) {
		uint32_t *w = &b->words[x * b->pitch + (y >> 5)], bit = 0x80000000u >> (y & 31);
		*w = on ? *w | bit : *w & ~bit;
	}
}

static int lit(struct bitmap *b, int32_t x, int32_t row)
{
	int32_t y = b->height - 1 - row;
	return (uint32_t)x < (uint32_t)b->width && (uint32_t)y < (uint32_t)b->height
	       && b->words[x * b->pitch + (y >> 5)] & 0x80000000u >> (y & 31);
}

static void fill(struct bitmap *b, int32_t x0, int32_t r0, int32_t x1, int32_t r1, int on)
{
	for (int32_t r = r0; r <= r1; r++)
		for (int32_t x = x0; x <= x1; x++)
			pixel(b, x, r, on);
}

static void dots(struct bitmap *b, int32_t row, int32_t x0, int32_t x1)
{
	for (int32_t x = x0; x <= x1; x += 2)
		pixel(b, x, row, 1);
}

static int32_t len(const char *s)
{
	int32_t n = 0;
	while (s[n])
		n++;
	return n;
}

static uint32_t glyph_row(const struct font *f, int32_t i, int32_t r)
{
	if (f->kind == 3)
		return F3[i] >> (3 * (4 - r)) & 7u;
	if (f->kind == 4)
		return F4[i] >> (4 * (6 - r)) & 15u;
	return F5[i][r];
}

/* A character's glyph; one the fonts do not have is a space. */
static int32_t glyph_of(char c)
{
	int32_t i = 0;
	while (CHARS[i] && CHARS[i] != c)
		i++;
	return CHARS[i] ? i : (int32_t)sizeof CHARS - 2;
}

static int32_t width(const struct font *f, const char *s, int32_t sc)
{
	return (len(s) * f->adv - 1) * sc;
}

/* s from x (its left), its glyphs sc pixels a dot; on 0 draws it dark (on a lit box). */
static void text(struct bitmap *b, const struct font *f, int32_t x, int32_t row, const char *s, int32_t sc, int on)
{
	for (; *s; s++, x += f->adv * sc) {
		int32_t i = glyph_of(*s);
		for (int32_t r = 0; r < f->h; r++) {
			uint32_t bits = glyph_row(f, i, r);
			for (int32_t c = 0; c < f->w; c++)
				if (bits >> (f->w - 1 - c) & 1u)
					fill(b, x + c * sc, row + r * sc, x + c * sc + sc - 1, row + r * sc + sc - 1, on);
		}
	}
}

static void centre(struct bitmap *b, const struct font *f, int32_t row, const char *s, int32_t sc)
{
	text(b, f, (W - width(f, s, sc)) / 2, row, s, sc, 1);
}

static void right(struct bitmap *b, const struct font *f, int32_t xr, int32_t row, const char *s)
{
	text(b, f, xr - width(f, s, 1) + 1, row, s, 1, 1);
}

/* A small string builder. */
struct str {
	char s[40];
	int n;
};

static void put(struct str *o, const char *s)
{
	while (*s && o->n < 39)
		o->s[o->n++] = *s++;
	o->s[o->n] = 0;
}

static void num(struct str *o, uint32_t v)
{
	char d[10];
	int n = 0;
	do {
		d[n++] = (char)('0' + v % 10u);
		v /= 10u;
	} while (v && n < 10);
	while (n && o->n < 39)
		o->s[o->n++] = d[--n];
	o->s[o->n] = 0;
}

/* frames as seconds: "2.4S" (tenths), "12S" from 10 s. */
static void seconds(struct str *o, uint32_t frames)
{
	uint32_t tenths = frames / 4800u;
	if (tenths < 100u) {
		num(o, tenths / 10u);
		put(o, ".");
		num(o, tenths % 10u);
	} else {
		num(o, tenths / 10u);
	}
	put(o, "S");
}

static const char *const SOURCES[8] = {"T1", "T2", "T3", "T4", "T5", "T6", "MAIN", "USB"};
static const char *const STARTS[3] = {"TRIG", "LEVEL", "NOW"};
static const char *const STOPS[3] = {"SILENT", "LENGTH", "RECORD"};

/* The title, the state at the right (inverted: dark on a lit box), the rule under them. */
static void head(struct bitmap *b, const char *state, int inverted)
{
	text(b, &T5, 2, 1, "RESAMPLE", 1, 1);
	if (state) {
		int32_t w = width(&T3, state, 1), x = X1 - w + 1;
		if (inverted)
			fill(b, x - 2, 1, x + w + 1, 7, 1);
		text(b, &T3, x, 2, state, 1, !inverted);
	}
	dots(b, 10, 0, W - 1);
}

static void foot(struct bitmap *b, const char *left, const char *right_)
{
	dots(b, 49, 0, W - 1);
	if (left)
		text(b, &T3, 2, ROW_FOOT, left, 1, 1);
	if (right_)
		right(b, &T3, X1, ROW_FOOT, right_);
}

static uint32_t shift_of(uint32_t src)
{
	return D->shift[src < SRC_MAIN ? 0 : src - (SRC_MAIN - 1)];
}

/* dB below full scale (0..60) as the meter's x: 4 + round((60 - db) / 60 x 119). */
static int32_t db_x(uint32_t db)
{
	if (db > 60u)
		db = 60u;
	return 4 + (int32_t)(((60u - db) * 238u + 60u) / 120u);
}

/* The source's level as a bar, -60 dB to full scale, LEVEL's threshold (thr_db >= 0) as a mark across it, and with
   labels its scale under it. */
static void meter(struct bitmap *b, int32_t row, uint32_t level, int32_t thr_db, int labels)
{
	uint32_t db = level ? rs_db(level, shift_of(D->src)) : 96u;

	fill(b, 3, row, 124, row, 1);
	fill(b, 3, row + 6, 124, row + 6, 1);
	fill(b, 3, row, 3, row + 6, 1);
	fill(b, 124, row, 124, row + 6, 1);
	if (db < 60u)
		fill(b, 4, row + 1, db_x(db), row + 5, 1);
	if (thr_db >= 0) {
		int32_t x = db_x((uint32_t)thr_db);
		pixel(b, x, row - 2, 1);
		pixel(b, x, row - 1, 1);
		pixel(b, x, row + 7, 1);
		pixel(b, x, row + 8, 1);
		for (int32_t r = row + 1; r <= row + 5; r++)
			pixel(b, x, r, !lit(b, x, r));
	}
	if (labels) {
		text(b, &T3, 3, row + 10, "-60", 1, 1);
		centre(b, &T3, row + 10, "-30", 1);
		right(b, &T3, 124, row + 10, "0DB");
	}
}

static void idle(struct bitmap *b)
{
	struct data *d = D;
	struct str v[8], t = {{0}, 0};
	const char *labels[8] = {"SOURCE", "START", "THRESH", "STEREO", "STOP", "LENGTH", "NORM", 0};
	uint32_t s = start_of();

	for (int i = 0; i < 8; i++)
		v[i].n = 0, v[i].s[0] = 0;
	put(&v[0], SOURCES[d->src_set & 7]);
	put(&v[1], STARTS[s]);
	if (s == START_LEVEL) {
		put(&v[2], "-");
		num(&v[2], d->thr_set);
		put(&v[2], "DB");
	} else
		put(&v[2], "---");
	put(&v[3], d->src_set < SRC_MAIN ? "---" : d->stereo_set ? "ON" : "OFF");
	put(&v[4], STOPS[d->stop_set % 3]);
	num(&v[5], d->length_set);
	put(&v[5], "S");
	put(&v[6], d->norm_set ? "ON" : "OFF");
	put(&v[7], !to_track_ok() ? "---" : d->to_track ? "YES" : "NO");
	put(&t, "TO T");
	num(&t, selected() + 1u);
	labels[7] = t.s;
	head(b, 0, 0);
	for (int i = 0; i < 8; i++) {                  /* as the knobs lie: PITCH DECAY COLOR SHAPE, SWEEP CONTOUR and on */
		int32_t x = 1 + 32 * (i % 4), row = i < 4 ? 13 : 31;
		text(b, &T3, x, row, labels[i], 1, 1);
		text(b, &T4, x, row + 7, v[i].s, 1, 1);
	}
	foot(b, "RECORD: ARM", "RETURN: CLOSE");
}

/* How the take ends: "STOPS WHEN SILENT", at its length (armed "STOPS AT 10S", recording "OF 10S"), "RECORD STOPS". */
static void ends(struct str *o, int recording)
{
	struct data *d = D;
	if (d->stop == STOP_SILENT)
		put(o, "STOPS WHEN SILENT");
	else if (d->stop == STOP_LENGTH) {
		put(o, recording ? "OF " : "STOPS AT ");
		num(o, d->limit / 48000u);
		put(o, "S");
	} else
		put(o, "RECORD STOPS");
}

static void armed(struct bitmap *b)
{
	struct data *d = D;
	struct str t = {{0}, 0};

	head(b, "ARMED", 0);
	centre(b, &T5, 15, d->start == START_LEVEL ? "WAIT FOR LEVEL" : "WAIT FOR TRIG", 1);
	put(&t, SOURCES[d->src & 7]);
	put(&t, d->stereo ? " STEREO    " : " MONO    ");
	ends(&t, 0);
	centre(b, &T3, 26, t.s, 1);
	meter(b, 33, d->level, d->start == START_LEVEL ? (int32_t)d->thr_set : -1, 1);
	foot(b, "RECORD: CANCEL", "RETURN: CLOSE");
}

static void recording(struct bitmap *b)
{
	struct data *d = D;
	struct str t = {{0}, 0}, end = {{0}, 0};
	uint32_t most = d->limit ? d->limit : 1u;
	uint32_t f = d->frames < most ? d->frames : most;   /* at most 2 096 576 x 238: 32 bits */

	head(b, "REC", 1);
	seconds(&t, d->frames);
	centre(b, &T5, 13, t.s, 2);
	ends(&end, 1);
	if (d->peak && rs_db(d->peak, shift_of(d->src)) == 0u)
		put(&end, "  CLIP");                   /* the take reached full scale */
	centre(b, &T3, 29, end.s, 1);
	meter(b, 35, d->level, -1, 0);
	dots(b, 45, 4, 123);
	fill(b, 4, 44, 4 + (int32_t)((f * 238u + most) / (2u * most)), 45, 1);
	foot(b, "RECORD: STOP", "RETURN: STOP");
}

static void taken(struct bitmap *b)
{
	struct data *d = D;
	struct str t = {{0}, 0};

	head(b, "UNSAVED", 0);
	centre(b, &T5, 16, "NOT SAVED", 1);
	seconds(&t, d->frames);
	put(&t, d->stereo ? "  STEREO" : "  MONO");
	put(&t, "  IN MEMORY");
	centre(b, &T3, 28, t.s, 1);
	foot(b, "RECORD: SAVE", "RETURN: DISCARD");
}

/* The save, piece by piece (save.c): the name, the folder, how far, as a bar and in percent. */
static void saving(struct bitmap *b)
{
	struct data *d = D;
	struct str t = {{0}, 0};
	uint32_t most = d->total ? d->total : 1u, p = d->pos < most ? d->pos : most;  /* 2 096 576 x 238: 32 bits */

	head(b, "SAVING", 0);
	centre(b, &T5, 15, d->name, 1);
	centre(b, &T3, 26, "/RECORDINGS", 1);
	fill(b, 3, 33, 124, 33, 1);
	fill(b, 3, 39, 124, 39, 1);
	fill(b, 3, 33, 3, 39, 1);
	fill(b, 124, 33, 124, 39, 1);
	fill(b, 4, 34, 4 + (int32_t)((p * 238u + most) / (2u * most)), 38, 1);
	num(&t, (p * 200u + most) / (2u * most));
	put(&t, "%");
	centre(b, &T3, 42, t.s, 1);
	foot(b, 0, 0);
	centre(b, &T3, ROW_FOOT, "WRITING TO +DRIVE", 1);
}

/* The page's render (the stock machine page's is 0x400a24ca): the whole screen. */
void rs_page_render(void *page, void *bitmap)
{
	struct bitmap *b = bitmap;
	int32_t n = b->width * b->pitch;

	(void)page;
	for (int32_t i = 0; i < n; i++)
		b->words[i] = 0;
	switch (D->state) {
	case ARMED:
		armed(b);
		break;
	case REC:
		recording(b);
		break;
	case TAKEN:
		if (D->saving)
			saving(b);
		else
			taken(b);
		break;
	default:
		idle(b);
	}
}
