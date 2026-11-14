/* Perform Kit, a part of model27's builder, with entries.S (the plan of 2026-11-14, _scratch/perform-kit/plan.md; the
 * note's number is fixed when it moves into notes/). Addresses are VAs of OS 1.13. Steps P1 (the switch and the
 * pattern change) and P2 / P3 (saving, loading, the temp slot, paste, clear and another project).
 *
 * With the mode on, a pattern change keeps the sounds as they are, tweaked: the six track sounds, the six levels and
 * the four effect values, bytes 0..693 of a kit (head +0..27, sounds +28..627, effect block +628..693). The pool of
 * the 64 lock sounds (+694..) is never touched, so each pattern's sound locks play their own sounds.
 *
 * The copy way: the OS goes on playing and editing the active pattern's kit (0x409c9c80 + 7094 n), as on the stock
 * OS, and the part moves the tweaked bytes into it.
 *   - Mode on (pk_toggle): own <- the playing pattern's kit 0..693; home = that pattern.
 *   - The change, in the sequencer's interrupt (pk_change_c, from entries.S's pk_seq_*, at the four writes of the
 *     playing kit 0x40a78888, before the audio side is told): the new pattern's own bytes are kept, the tweaked
 *     bytes copied into its kit; the pattern left keeps the tweaked bytes until the interface has left it.
 *   - The interface's kit selection (pk_ui_c, from pk_ui at 0x4000f36a, before it binds the new kit): the bytes once
 *     more (a knob turned across the change wrote into the kit left), then the pattern left gets its own bytes back.
 *     A second change before that makes pk_change_c give them back itself.
 *   - Mode off (pk_toggle): home's kit 0..693 <- its own bytes; the audio side's cached pointers cleared
 *     (0x4005950e: the six sounds, the six levels and the effect block are taken again at the next note), and the
 *     kit's change notice (0x400d1f98), which refreshes the interface and the kit's mirror.
 * The switch shows the OS's popup, "Perform Kit ON" or "Perform Kit OFF" (popup, as RESAMPLE's save.c and the OS's
 * own 0x4000d750 show one: 0x400747c0 on 0x9c bytes, its holder 0x400fbf40, presented on the views' target); paste
 * and clear, which switch the mode off, do not: the OS shows its own message right after.
 * While the mode is on, the main screen shows it, whoever draws it (pk_main, in MainScreenView's draw slot, vtable
 * entry 0x400ffe30, stock 0x4001b22a): pk_main calls the draw the build would have there otherwise (next, written by
 * the composer: the stock draw, a machine's own main draw as SAMPLE's, or the dispatcher's), then paints a
 * checkerboard stripe over the two leftmost columns, the screen's full height, straight into the bitmap (as the
 * OS's fill 0x40070dea reads it: +4 width, +8 height, +12 the words a column, +16 the data, a column's words one
 * after the other, a row's bit 31 - (row & 31)); not while a value window is open, when the stock draw draws
 * nothing. A switch asks the main view, kept from its last draw, for a redraw (0x40076082).
 * SETTINGS + PATTERN switches (pk_pattern_c, from pk_pattern at 0x40020ad0, PatternGridView's PATTERN case): with
 * SETTINGS held, PATTERN's press toggles the mode and is taken, with its repeats and its release, so the pattern
 * selection is not armed. SETTINGS is held when isKeyHeld(13) says so or its last event does (pk_held, a byte the
 * composer names: this part's own, kept by pk_code at the key code accessor 0x4007240c, or RESAMPLE's when that part
 * is in the build and holds the accessor).
 *
 * What is saved (steps P2 and P3). Nothing of the mode is permanent until the pattern is saved:
 *   - Every serialization of a kit goes through 0x4005b2ae(buffer, kit, 0) (the whole project for Save Project and
 *     the backup at power off, the kit's mirror, a SysEx dump). Its start goes to pk_ser -> pk_ser_c, which hands it,
 *     for home's kit and for the kit of the pattern left, a copy with the pattern's own bytes in 0..693 (big).
 *   - A pattern's own save calls it from 0x400100ba (0x4001002c(project, temp, n)), which goes to pk_ksave ->
 *     pk_ksave_c and then into the serializer past pk_ser: Save Pattern (the project's slot) makes the tweaked bytes
 *     home's own first, so they are saved and stay; a temp save (slot 96) saves the tweaked bytes and notes the
 *     pattern.
 *   - A kit loaded from a slot (0x400107a4, the loader 0x4005d080, in 0x400106de) goes through pk_kload ->
 *     pk_loaded_c: Reload Pattern from the project makes the loaded bytes home's own; a temp reload does not.
 *   - Mode off saves the kit of every pattern noted to the temp slot again, now with its own bytes, so what was
 *     temp-saved inside the mode does not come back after it.
 *   - Pattern paste and clear (0x40010c7a, 0x4001190c, 0x40011a7e) switch the mode off first (pk_off_c); another
 *     project (0x4000eb12, called by the three functions that replace the project) drops the mode without writing
 *     a kit (pk_drop_c).
 *
 * The data block (pk_data, part.json "data"), zero at boot:
 *   +0 on    the mode
 *   +1 home  the pattern whose kit holds the tweaked bytes
 *   +2 left1 1 + the pattern left whose own bytes are still to be given back, 0: none
 *   +3 which the buffer that holds home's own bytes; the other holds the pattern left's
 *   +4 taken PATTERN's press was taken, its release is to be taken
 *   +5 held  SETTINGS' last event was down (pk_code)
 *   +8 buf   two buffers of 696 bytes
 *   +1400 temp  a bit per pattern temp-saved inside the mode
 *   +1412 view  the main view, from its last draw
 *   +1416 next  the main draw behind pk_main, written by the composer
 *   +1420 big   a kit, for the serializer's copy
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>

#define HEAD 694u                                   /* a kit without its pool */
#define KIT_SIZE 7094u
#define KITS 96u

typedef struct {
	uint8_t on, home, left1, which, taken, held, pad[2];
	uint8_t buf[2][696];
	uint8_t temp[12];
	void *view;
	void (*next)(void *, void *);
	uint8_t big[7096];
} pk_t;

#ifdef PK_HOST                                       /* the host test's stand-ins (test_perform.c) */
#include "host_os.h"
#else
extern pk_t pk_data;
extern volatile uint8_t pk_held;
#define KIT(n) ((uint8_t *)0x409c9c80 + KIT_SIZE * (n))
#define KEY_HELD ((uint32_t (*)(uint32_t))0x4007faf4)                      /* isKeyHeld */
#define SEQ_STATE ((void *(*)(void))0x400cfd0e)
#define PLAYING_PATTERN ((uint32_t (*)(void *))0x4006a96c)                 /* -> 0..95 */
#define PROJECT ((uint8_t *(*)(void))0x400cf866)
#define KIT_CHANGED ((void (*)(uint8_t *, uint32_t, uint32_t))0x400d1f98)  /* (project + 116, kit, 0) */
#define AUDIO_KIT ((void (*)(uint8_t *))0x4005950e)                        /* sets the kit, clears what is cached */
#define PLAY_KIT (*(uint8_t *volatile *)0x800017e4)
#define IS_PRESS ((uint32_t (*)(void *))0x400724a0)                        /* a press, not its repeat */
#define IS_RELEASE ((uint32_t (*)(void *))0x40072470)
#define TEMP_KIT_SAVE ((uint32_t (*)(uint8_t *, uint32_t, uint32_t))0x4001002c)   /* (project, 1, pattern) */
#define NEW(n) ((void *(*)(uint32_t))0x400802e0)(n)                 /* operator new */
#define STRING(s, c, tag) ((void (*)(void *, const char *, void *))0x400f980c)(s, c, tag)
#define STRING_DROP(s) ((void (*)(void *))0x400f7d5c)(s)
#define POPUP_SIZE 0x9c
#define POPUP(p, s) ((void (*)(void *, void *))0x400747c0)(p, s)
#define POPUP_HOLDER_VT 0x400fbf40u
#define VIEWS_UP (*(void *const volatile *)0x40fe4178)
#define VIEWS() ((char *(*)(void))0x400d0974)()
#define TARGET(v) ((void *(*)(void *))0x400060d8)(v)
#define PRESENT(t, pair, x) ((void (*)(void *, void *, uint32_t))0x4007700e)(t, pair, x)
#define DROP(ref) ((void (*)(void *))0x400cf23c)(ref)
#define NEEDS_REDRAW(v) ((void (*)(void *))0x40076082)(v)
#define UI_STATE() ((void *(*)(void))0x400cf9a8)()
#define VALUE_SHOWN() (((char (*)(void *))0x4006b704)(UI_STATE()) != 0)   /* a value window is open */

/* The OS's popup with this text, as tools/machines/resample/save.c shows one. */
static void popup(const char *text)
{
	char tag[4];
	uint32_t s, *holder;
	void *pair[2];
	char *p;

	if (!VIEWS_UP)
		return;
	STRING(&s, text, tag);
	p = NEW(POPUP_SIZE);
	if (p) {
		POPUP(p, &s);
		holder = NEW(16);
		holder[0] = POPUP_HOLDER_VT;
		holder[1] = holder[2] = 1;
		holder[3] = (uint32_t)p;
		pair[0] = p;
		pair[1] = holder;
		PRESENT(TARGET(VIEWS()), pair, 0);
		DROP(&pair[1]);
	}
	STRING_DROP(&s);
}

static inline uint32_t irq_off(void)
{
	uint32_t sr, masked;
	__asm__ volatile("move.w %%sr, %0" : "=d"(sr));
	masked = sr | 0x0700;
	__asm__ volatile("move.w %0, %%sr" : : "d"(masked) : "memory");
	return sr;
}
static inline void irq_back(uint32_t sr)
{
	__asm__ volatile("move.w %0, %%sr" : : "d"(sr) : "memory");
}
#endif

#define K_SETTINGS 13u

/* Bytes 0..693, 173 long words and a word; a kit starts at an even address. */
static void head_copy(uint8_t *to, const uint8_t *from)
{
	uint32_t *d = (uint32_t *)(void *)to;
	const uint32_t *s = (const uint32_t *)(const void *)from;
	uint32_t i;

	for (i = 0; i < HEAD / 4; i++)
		*d++ = *s++;
	*(uint16_t *)(void *)d = *(const uint16_t *)(const void *)s;
}

/* A whole kit, 1773 long words and a word. */
static void kit_copy(uint8_t *to, const uint8_t *from)
{
	uint32_t *d = (uint32_t *)(void *)to;
	const uint32_t *s = (const uint32_t *)(const void *)from;
	uint32_t i;

	for (i = 0; i < KIT_SIZE / 4; i++)
		*d++ = *s++;
	*(uint16_t *)(void *)d = *(const uint16_t *)(const void *)s;
}

/* The pattern left gets its own bytes back; called with the interrupts masked, or in the sequencer's interrupt. */
static void give_back(pk_t *D)
{
	if (D->left1) {
		head_copy(KIT(D->left1 - 1u), D->buf[D->which ^ 1u]);
		D->left1 = 0;
	}
}

/* entries.S's pk_seq_*: the sequencer is about to play the kit `kit` (a write of 0x40a78888), in its interrupt. */
void pk_change_c(uint8_t *kit)
{
	pk_t *D = &pk_data;
	uint32_t n;

	if (!D->on || kit < KIT(0))
		return;
	n = (uint32_t)(kit - KIT(0)) / KIT_SIZE;
	if (n >= KITS || KIT(n) != kit || n == D->home)
		return;
	give_back(D);                                   /* a second change before the interface ran */
	head_copy(D->buf[D->which ^ 1u], KIT(n));       /* the new pattern's own bytes */
	head_copy(KIT(n), KIT(D->home));                /* the tweaked bytes into its kit */
	D->left1 = (uint8_t)(D->home + 1u);
	D->which ^= 1u;
	D->home = (uint8_t)n;
}

/* entries.S's pk_ui, at the start of the interface's kit selection (0x4000f36a), before it binds another kit. */
void pk_ui_c(void)
{
	pk_t *D = &pk_data;
	uint32_t sr;

	if (!D->on || !D->left1)
		return;
	sr = irq_off();
	if (D->on && D->left1) {
		head_copy(KIT(D->home), KIT(D->left1 - 1u));   /* what a knob wrote into the kit left since the change */
		give_back(D);
	}
	irq_back(sr);
}

/* The main screen is drawn again, with or without the mark. */
static void redraw(pk_t *D)
{
	if (D->view)
		NEEDS_REDRAW(D->view);
}

/* A bitmap as the OS's drawing reads it (0x40070dea). */
typedef struct {
	uint32_t head;
	int32_t width, height, stride;              /* stride: the words of a column */
	uint32_t *data;
} pk_bitmap;

#define STRIPE 2                                    /* columns */

/* The checkerboard stripe over the leftmost columns: column x's words alternate from bit 31 or bit 30. */
static void stripe(pk_bitmap *b)
{
	int32_t words = (b->height + 31) >> 5, x, i;

	if (!b->data || b->width < STRIPE || words < 1 || words > b->stride)
		return;
	for (x = 0; x < STRIPE; x++)
		for (i = 0; i < words; i++)
			b->data[x * b->stride + i] = x & 1 ? 0x55555555u : 0xaaaaaaaau;
}

/* MainScreenView's draw (vtable entry 0x400ffe30): the draw behind it, then the stripe while the mode is on. */
void pk_main(void *view, void *bitmap)
{
	pk_t *D = &pk_data;

	if (D->next)
		D->next(view, bitmap);
	D->view = view;
	if (D->on && !VALUE_SHOWN())
		stripe(bitmap);
}

/* The mode off: home's own bytes back, the audio side and the interface told, then the temp slot's kits of the
 * patterns temp-saved inside the mode saved again, with their own bytes; say: with the popup. */
static void mode_off(pk_t *D, uint32_t say)
{
	uint32_t sr, n;

	sr = irq_off();
	give_back(D);
	n = D->home;
	head_copy(KIT(n), D->buf[D->which]);
	D->on = 0;
	AUDIO_KIT(PLAY_KIT);
	irq_back(sr);
	KIT_CHANGED(PROJECT() + 116, n, 0);
	for (n = 0; n < KITS; n++)
		if (D->temp[n >> 3] & (1u << (n & 7u))) {
			D->temp[n >> 3] &= (uint8_t)~(1u << (n & 7u));
			TEMP_KIT_SAVE(PROJECT(), 1, n);
		}
	redraw(D);
	if (say)
		popup("Perform Kit OFF");
}

/* The mode on or off. */
void pk_toggle(void)
{
	pk_t *D = &pk_data;
	uint32_t sr, n;

	if (D->on) {
		mode_off(D, 1);
		return;
	}
	n = PLAYING_PATTERN(SEQ_STATE());
	if (n >= KITS)
		return;
	sr = irq_off();
	head_copy(D->buf[D->which], KIT(n));
	D->home = (uint8_t)n;
	D->left1 = 0;
	D->on = 1;
	irq_back(sr);
	redraw(D);
	popup("Perform Kit ON");
}

/* entries.S's pk_off_*: a pattern is about to be pasted or cleared. */
void pk_off_c(void)
{
	if (pk_data.on)
		mode_off(&pk_data, 0);                      /* the OS shows its own message right after */
}

/* entries.S's pk_drop: the project is being replaced; no kit is written. */
void pk_drop_c(void)
{
	pk_t *D = &pk_data;
	uint32_t i;

	D->on = 0;
	D->left1 = 0;
	for (i = 0; i < sizeof D->temp; i++)
		D->temp[i] = 0;
	redraw(D);
}

/* entries.S's pk_ser, the start of the kit serializer: the kit to serialize, big for home's and the pattern left's,
 * with the pattern's own bytes. The state is read and checked again with the interrupts masked; the copy is not. */
uint8_t *pk_ser_c(uint8_t *kit)
{
	pk_t *D = &pk_data;
	uint32_t sr, tries, on, home, left1, which, same;
	const uint8_t *own;

	for (tries = 0; tries < 3; tries++) {
		sr = irq_off();
		on = D->on; home = D->home; left1 = D->left1; which = D->which;
		irq_back(sr);
		if (!on)
			return kit;
		if (kit == KIT(home))
			own = D->buf[which];
		else if (left1 && kit == KIT(left1 - 1u))
			own = D->buf[which ^ 1u];
		else
			return kit;
		kit_copy(D->big, kit);
		head_copy(D->big, own);
		sr = irq_off();
		same = D->on && D->home == home && D->left1 == left1 && D->which == which;
		irq_back(sr);
		if (same)
			break;
	}
	return D->big;
}

/* entries.S's pk_ksave, a pattern's kit about to be saved to a slot (96: the temp slot). */
void pk_ksave_c(uint32_t n, uint32_t slot)
{
	pk_t *D = &pk_data;
	uint32_t sr;

	if (!D->on || n >= KITS || n != D->home)
		return;
	if (slot == 96u) {
		D->temp[n >> 3] |= (uint8_t)(1u << (n & 7u));
		return;
	}
	sr = irq_off();
	if (D->on && n == D->home)
		head_copy(D->buf[D->which], KIT(n));        /* Save Pattern: the tweaked bytes are the pattern's own */
	irq_back(sr);
}

/* entries.S's pk_kload, after a pattern's kit was loaded from a slot (ok: the loader's answer). */
void pk_loaded_c(uint32_t n, uint32_t slot, uint32_t ok)
{
	pk_t *D = &pk_data;
	uint32_t sr;

	if (!D->on || !(ok & 0xffu) || slot == 96u || n != D->home)
		return;
	sr = irq_off();
	if (D->on && n == D->home)
		head_copy(D->buf[D->which], KIT(n));        /* Reload Pattern: the loaded bytes are the pattern's own */
	irq_back(sr);
}

/* entries.S's pk_pattern, PatternGridView's PATTERN case: 1 when the event is taken. */
uint32_t pk_pattern_c(void *event)
{
	pk_t *D = &pk_data;

	if (D->taken) {                                 /* the press was taken: its repeats and its release too */
		if (IS_RELEASE(event))
			D->taken = 0;
		return 1;
	}
	if (!IS_PRESS(event) || !(KEY_HELD(K_SETTINGS) || pk_held))
		return 0;
	D->taken = 1;
	pk_toggle();
	return 1;
}
