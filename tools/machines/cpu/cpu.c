/* The CPU page of model27's builder, with entries.S (notes/78). Addresses are VAs of OS 1.13.
 *
 * The measure (step 1 of notes/78 §6): entries.S's cpu_probe takes the audio interrupt's call of the audio function
 * (0x40059382, jsr 0x4005979e: the voices, Volume + Dist and the Track FX, the mix and the effects) and times it with
 * the DMA timer 0 (0xfc07000c, 135.168 MHz: a block of 32 frames at 48 kHz is 90 112 ticks, notes/23 §5), then calls
 * cpu_block with the block's busy ticks. The interrupt runs once a block, driven by the codec, so a share is the busy
 * ticks over the nominal block, as fltslot's own measure counts it: the shares add up. What the interrupt does outside
 * the audio function is not counted (notes/78 §4.1).
 *
 * Over a window of 750 blocks (0.5 s), cpu_block keeps the busy ticks and the dearest block; at the window's end it
 * writes the average and that peak as tenths of a percent of a block, with the two shares the build's other parts
 * measure:
 *   - the Track FX (the filter slot, tools/machines/fltslot/): fltslot times its own run (fl_measure) and keeps the
 *     last window's average in its data block; the composer writes the address of that word here (fl_avg), or 0 when
 *     the build has no Track FX. Its window is fltslot's, out of step with this one by less than 0.5 s;
 *   - the effect slots (tools/machines/fxslot/, since its 0.7): fxslot adds the ticks of each slot's run to a counter
 *     that runs from boot (its busy); the composer writes its address here (fx_busy), or 0 without effects. The
 *     difference since the last window's end, over the window, is the slots' share in this one.
 * And the dearest block since the counter was last cleared (top, top_t): the page clears it when it opens (step 2),
 * so that its PEAK is the worst block since then. windows counts the windows ended, for the page's redraw.
 *
 * cpu_block runs in the audio interrupt, after the audio function, about 20 instructions a block and some 30 more at a
 * window's end. It keeps its state in the part's data block (a part has no variables of its own): written by the
 * composer, zero at boot but for the two addresses.
 *
 * The page (step 2 of notes/78 §6), as Model-TG builds its System page (TinyGregAudio, MIT; its mm_open, mm_key and
 * mm_enc in src/model_tg.s, notes/78 §2): entries.S's cpu_cfg adds the row CPU to the device configuration list, whose
 * press calls cpu_open. The page is the stock machine-select page (0x400a22b0, 0xd0 bytes) with its first two vtable
 * pointers set to a private copy of its vtable group (0x40117918..0x401179c8, here in the data block), in which the
 * destructors (entries.S: forget the page, then the stock ones), the key handler, the render and the encoder handler are
 * ours; it is presented as the stock opener presents a page. Return closes it (as the machine page closes), every other
 * key goes to the stock view's dispatch (0x40075f3c) and every knob but DATA to the stock base (0x4006fb90), as the
 * machine page passes them on; DATA does nothing. The render draws the whole screen from the data block: CPU and the
 * average with a bar (a mark at 85 %, where notes/25 found the interface short of time), PEAK (the top), TRACK FX and
 * EFFECTS, "--" when the build has not that part.
 *
 * The redraw (step 3): the OS calls every view of its view stack's method +0x2c on a timer (0x40005970 ->
 * 0x400778e2, registered at 0x40006ec6 with 30; the knob view counts its popup down there, the machine-select page has
 * an empty one, 0x40075f2e). The page's is cpu_tick: when a window has ended since the last redraw, it asks for one
 * (View::setNeedsRedraw, 0x40076082), so twice a second while the page is up and never when it is not. The page's
 * opening clears the top, so that PEAK is the worst block since then.
 *
 * License: MIT (LICENSE next to this file; the page's mechanics follow Model-TG's, MIT, LICENSE-Model-TG). */
#include <stdint.h>

#define WINDOW 750u                                 /* blocks a window, 0.5 s */
#define WINDOW_TICKS 67584u                         /* 750 blocks of 90 112 ticks, over 1000: a window's 0.1 % */
#define TOP_TICKS 0x00400000u                       /* past it (46 blocks) a block counts as that: no overflow */

struct data {
	uint32_t fl_avg;                            /* +0 the filter slot's last average (0.1 %, 16 bits), or 0 */
	uint32_t fx_busy;                           /* +4 the effect slots' running ticks (32 bits), or 0 */
	uint32_t ret;                               /* +8 the probe's return address */
	uint32_t t0;                                /* +12 the block's start */
	uint32_t sum, peak;                         /* +16 the window's busy ticks and its dearest block */
	uint32_t top;                               /* +24 the dearest block since the last clear */
	uint32_t fx_last;                           /* +28 the effect slots' ticks at the last window's end */
	uint16_t n;                                 /* +32 the window's blocks */
	uint16_t avg, win_peak, top_t;              /* +34 the last window's average and peak, the top: 0.1 % */
	uint16_t trackfx, effects;                  /* +40 the Track FX' and the effect slots' shares, 0.1 % */
	uint16_t windows, drawn;                    /* +44 the windows ended; their count at the page's last redraw */
	void *page;                                 /* +48 the page while it is up, else 0 */
	uint32_t vt[44];                            /* +52 its vtable group, a copy of 0x40117918..0x401179c8 */
};                                                  /* 228 bytes */

extern char cpu_data[];
#define D ((struct data *)cpu_data)

/* ticks as tenths of a percent of a block: ticks * 1000 / 90 112 = ticks * 125 / 11 264. */
static uint16_t share(uint32_t ticks)
{
	uint32_t s;
	if (ticks > TOP_TICKS)
		ticks = TOP_TICKS;
	s = ticks * 125u / 11264u;
	return (uint16_t)(s > 0xffffu ? 0xffffu : s);
}

/* entries.S's cpu_probe, after the audio function: busy its ticks in this block. */
void cpu_block(uint32_t busy)
{
	if (busy > TOP_TICKS)
		busy = TOP_TICKS;
	D->sum += busy;
	if (busy > D->peak)
		D->peak = busy;
	if (busy > D->top) {
		D->top = busy;
		D->top_t = share(busy);
	}
	if (++D->n < WINDOW)
		return;
	D->avg = (uint16_t)(D->sum / WINDOW_TICKS);
	D->win_peak = share(D->peak);
	if (D->fl_avg)
		D->trackfx = *(const volatile uint16_t *)D->fl_avg;
	if (D->fx_busy) {
		uint32_t now = *(const volatile uint32_t *)D->fx_busy;
		D->effects = (uint16_t)((now - D->fx_last) / WINDOW_TICKS);
		D->fx_last = now;
	}
	D->sum = D->peak = 0;
	D->n = 0;
	D->windows++;
}

/* --- the page ---------------------------------------------------------------------------------------------------- */
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
#define KEY_CLICK(e) ((int32_t (*)(void *))0x40072434)(e)           /* the event's flag bit 4 */
#define KEY_STOCK(v, e) ((uint32_t (*)(void *, void *))0x40075f3c)(v, e)
#define NEEDS_REDRAW(v) ((void (*)(void *))0x40076082)(v)          /* View::setNeedsRedraw */
#define K_RETURN 12
#define CLOSE_AT 0x28                               /* the view's close, in its primary vtable (0x40076126) */

extern char cpu_dtor0[], cpu_dtor1[], cpu_dtor0_th[], cpu_dtor1_th[], cpu_enc[], cpu_enc_th[];
uint32_t cpu_key(void *page, void *event);
void cpu_render(void *page, void *b);
void cpu_tick(void *page);

/* The row's press (entries.S's cpu_press): the page, unless it is up already, the view machinery is not, or this is
   not the interface's thread (an interrupt level above 0). */
void cpu_open(void)
{
	uint32_t sr, *holder;
	char *page;
	void *pair[2];

	__asm__ volatile("move.w %%sr, %0" : "=d"(sr));
	if (sr & 0x0700 || D->page || !VIEWS_UP)
		return;
	for (int i = 0; i < VT_WORDS; i++)
		D->vt[i] = VT_SRC[i];
	D->vt[VT_DTOR0] = (uint32_t)cpu_dtor0;
	D->vt[VT_DTOR1] = (uint32_t)cpu_dtor1;
	D->vt[VT_KEY] = (uint32_t)cpu_key;
	D->vt[VT_RENDER] = (uint32_t)cpu_render;
	D->vt[VT_TICK] = (uint32_t)cpu_tick;
	D->vt[VT_ENC] = (uint32_t)cpu_enc;
	D->vt[VT_DTOR0_TH] = (uint32_t)cpu_dtor0_th;
	D->vt[VT_DTOR1_TH] = (uint32_t)cpu_dtor1_th;
	D->vt[VT_ENC_TH] = (uint32_t)cpu_enc_th;
	page = NEW(PAGE_SIZE);
	if (!page)
		return;
	PAGE_CTOR(page);
	__asm__ volatile("move.w %0, %%sr" : : "d"(sr | 0x0700) : "memory");    /* PEAK counts from now */
	D->top = 0;
	D->top_t = 0;
	__asm__ volatile("move.w %0, %%sr" : : "d"(sr) : "memory");
	D->drawn = D->windows;
	*(uint32_t **)page = &D->vt[VT_DTOR0];      /* the primary vtable */
	*(uint32_t **)(page + 4) = &D->vt[VT_BASE4];
	D->page = page;
	holder = NEW(16);
	holder[0] = HOLDER_VT;
	holder[1] = holder[2] = 1;
	holder[3] = (uint32_t)page;
	pair[0] = page;
	pair[1] = holder;
	PRESENT(TARGET(VIEWS()), pair, 0);
	DROP(&pair[1]);
}

/* The page's key handler: Return closes it, as the machine page closes; any other key the stock view's. */
uint32_t cpu_key(void *page, void *event)
{
	if (KEY_CODE(event) != K_RETURN)
		return KEY_STOCK(page, event);
	if (KEY_CLICK(event))
		(*(void (**)(void *))(*(char **)page + CLOSE_AT))(page);
	return 1;
}

/* The page's periodic method: a redraw when a window has ended since the last one. */
void cpu_tick(void *page)
{
	uint16_t w = D->windows;

	if (w == D->drawn)
		return;
	D->drawn = w;
	NEEDS_REDRAW(page);
}

/* --- the render: 128 x 64, a Bitmap (0x40070172) whose pixel (x, y), y from the bottom, is bit 31 - (y & 31) of word
   x * pitch + y / 32; the text by the OS in its small font, as REF2's views draw (tools/machines/refmachine2/). */
struct bitmap {
	const void *vtable;
	int32_t width, height, pitch;
	uint32_t *words;
};

#define FONT_MAKE(f, g) ((void (*)(void *, const void *))0x40072260)(f, g)
#define FONT_DROP(f) ((void (*)(void *))0x40072080)(f)
#define FONT_SMALL ((const void *)0x40140ab0)       /* 5 x 9 pixels */
#define DRAW_TEXT ((void (*)(void *, void *, int32_t, int32_t, int32_t, const char *, ...))0x40071a04)
#define LEFT 0x10                                   /* the text's flags: from x, cleared behind (Model-TG's) */
#define RIGHT 0x14                                  /* ...ending at x */
#define TEXT_X0 2
#define TEXT_X1 125
#define ROW_CPU 1                                   /* the lines' top rows, from the screen's top */
#define ROW_PEAK 22
#define ROW_TRACKFX 33
#define ROW_EFFECTS 44
#define BAR_TOP 12                                  /* the bar: rows 12..16, x 2..125, filled inside from x 3 */
#define BAR_X0 2
#define BAR_X1 125
#define BAR_W 122                                   /* the fill at 100 %: x 3..124 */
#define MARK 850                                    /* the mark, 85 %: rows 10..11 and 17..18 */

static void pixel(struct bitmap *b, int32_t x, int32_t row)
{
	int32_t y = b->height - 1 - row;
	if ((uint32_t)x < (uint32_t)b->width && (uint32_t)y < (uint32_t)b->height)
		b->words[x * b->pitch + (y >> 5)] |= 0x80000000u >> (y & 31);
}

static void text(struct bitmap *b, int32_t x, int32_t row, int32_t flags, const char *s)
{
	uint32_t font[2];

	FONT_MAKE(font, FONT_SMALL);
	DRAW_TEXT(b, font, x, b->height - 9 - row, flags, "%s", s);    /* a line 9 pixels tall, y its bottom row */
	FONT_DROP(font);
}

/* tenths of a percent as "72.3%", or "--" for none. */
static void percent(char *out, uint32_t tenths, int none)
{
	char digits[8];
	int n = 0, i = 0;

	if (none) {
		out[0] = out[1] = '-';
		out[2] = 0;
		return;
	}
	uint32_t whole = tenths / 10;
	do {
		digits[n++] = (char)('0' + whole % 10);
		whole /= 10;
	} while (whole && n < 6);
	while (n)
		out[i++] = digits[--n];
	out[i++] = '.';
	out[i++] = (char)('0' + tenths % 10);
	out[i++] = '%';
	out[i] = 0;
}

static void line(struct bitmap *b, int32_t row, const char *label, uint32_t tenths, int none)
{
	char value[12];

	percent(value, tenths, none);
	text(b, TEXT_X0, row, LEFT, label);
	text(b, TEXT_X1, row, RIGHT, value);
}

static void bar(struct bitmap *b, uint32_t tenths)
{
	int32_t fill = (int32_t)((tenths > 1000 ? 1000 : tenths) * BAR_W / 1000);
	int32_t mark = BAR_X0 + 1 + MARK * BAR_W / 1000;

	for (int32_t x = BAR_X0; x <= BAR_X1; x++) {
		pixel(b, x, BAR_TOP);
		pixel(b, x, BAR_TOP + 4);
	}
	for (int32_t r = BAR_TOP + 1; r < BAR_TOP + 4; r++) {
		pixel(b, BAR_X0, r);
		pixel(b, BAR_X1, r);
		for (int32_t x = BAR_X0 + 1; x < BAR_X0 + 1 + fill; x++)
			pixel(b, x, r);
	}
	for (int32_t r = BAR_TOP - 2; r < BAR_TOP; r++) {
		pixel(b, mark, r);
		pixel(b, mark, r + 7);
	}
}

/* The page's render (the stock machine page's is 0x400a24ca): the whole screen. */
void cpu_render(void *page, void *bitmap)
{
	struct bitmap *b = bitmap;
	int32_t n = b->width * b->pitch;

	(void)page;
	for (int32_t i = 0; i < n; i++)
		b->words[i] = 0;
	line(b, ROW_CPU, "CPU", D->avg, 0);
	bar(b, D->avg);
	line(b, ROW_PEAK, "PEAK", D->top_t, 0);
	line(b, ROW_TRACKFX, "TRACK FX", D->trackfx, !D->fl_avg);
	line(b, ROW_EFFECTS, "EFFECTS", D->effects, !D->fx_busy);
}
