/* The effect slots of model27's builder, with entries.S (notes/68 §2, §9, §11, §14; steps F1, F2 and F2b). Addresses
 * are VAs of OS 1.13.
 *
 * The choice is the pattern's (notes/68 §14): bytes 29 and 30 of its 64-byte header hold the delay slot's id and the
 * reverb slot's, byte 31 a check, 0x5a + byte 29 + byte 30. A header whose check fails chooses the stock effects. The
 * OS saves the header's 64 bytes but loads only its fields (0x4005b3b4: bytes 0..28 and 38) and a new pattern's header
 * keeps the rest (0x40061526): fx_hdr_load and fx_hdr_init, called from entries.S in the loader and the initializer,
 * copy the three bytes when the check holds and choose the stock effects otherwise. Every write of the three bytes is
 * done with the interrupts masked, so the audio never reads half of one.
 *
 * fx_run, called for each slot in every audio block (entries.S): reads the playing pattern's choice (the playing
 * pattern *0x40a7887c, its number at +30706, its object in the patterns' singleton *0x40fe4228 at +5192 + 732 n, its
 * header at the object's +60, notes/42 §5); when it is not the one the slot's parameters are named after, names them
 * after it; then runs the slot's chosen effect, or the stock one for id 0 or an id the build does not hold. When the
 * slot changes effect: the stock effect that stops gets one block of silence (its return thrown away), so that the DMA
 * that writes its lines from its buffers (0x400573fa, 0x40057942) writes silence while it does not play; the effect
 * that starts gets its reset, if it has one.
 *
 * fx_step, the gesture (entries.S's fx_track): TRACK + Delay Time (descriptor 37) or TRACK + Reverb Size (39), on a
 * slot that has an effect in this build. Four detents in one direction make one step; the count starts again after a
 * change of direction or of slot, or 0.4 s without a detent (the DMA timer 0, 135.168 MHz). A step moves the shown
 * pattern's choice (0x4000f208 on the singleton, its header object at +44, the header at that object's +16) to the
 * next or previous entry of the slot's table (the stock effect first, then the effects by id), and stops at the ends.
 * Each change writes the header and calls its notify (the header object's vtable entry 4, as the stock setters do);
 * when the shown pattern is the playing one, it also names the slot's two parameters after the effect at once (their
 * descriptors' long and short names and group, in the stock table and in the one the OS uses when the build moved it;
 * their interface objects' formatters).
 *
 * The state is in the part's data block (a part has no variables of its own): written by the composer, zero at boot.
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>

#define SLOTS 2
#define ENTRIES 8
#define DETENTS 4                                   /* in one direction, for one step */
#define PAUSE 54067200u                             /* 0.4 s of the DMA timer 0 (notes/23 §5) */
#define TIMER (*(volatile uint32_t *)0xfc07000c)
#define ROOT (*(uint8_t *volatile *)0x40fe4228)    /* the patterns' singleton (notes/42 §5) */
#define PLAYING (*(uint8_t *volatile *)0x40a7887c) /* the playing pattern */
#define SHOWN ((uint8_t *(*)(uint8_t *))0x4000f208)    /* the shown pattern's object, from the singleton */
#define HDR 29                                      /* the header's bytes 29..31: the delay's id, the reverb's, check */
#define OBJECT(i) (0x40a71754u + 100u * (uint32_t)(i))  /* descriptor i's interface object (notes/47 §3.3) */
#define FIRST_DESC(slot) ((slot) ? 39u : 37u)       /* Reverb Size (knob 14) or Delay Time (knob 15), notes/68 §8 */

typedef void (*fx_fn)(int32_t *out, const int32_t *in, const void *params);

struct entry { uint32_t id, process, reset; };
struct slot { uint32_t count; struct entry e[ENTRIES]; };
struct names { uint32_t longa, shorta, longb, shortb, group, fmta, fmtb; };
struct data {
	struct slot slot[SLOTS];                    /* +0 the delay slot, +100 the reverb slot; entry 0 the stock effect */
	uint32_t desc[2];                           /* +200 the descriptor tables the names go into */
	struct names names[SLOTS][ENTRIES];         /* +208 by slot and entry */
	int32_t zeros[64];                          /* +656 silence, also the parameters of a silent block */
	int32_t scratch[64];                        /* +912 the stock effect's return in that block */
	uint8_t cur[SLOTS], played[SLOTS], acc, last_slot, last_dir;   /* +1168: cur, the ids the names are of */
	uint32_t last_time;                         /* +1176 */
};                                                  /* 1180 bytes */

extern char fx_data[];
#define D ((struct data *)fx_data)

static uint32_t index_of(const struct slot *s, uint32_t id)
{
	for (uint32_t i = 0; i < s->count; i++)
		if (s->e[i].id == id)
			return i;
	return 0;
}

static void name_slot(int slot)
{
	const struct slot *s = &D->slot[slot];
	if (s->count < 2)                           /* no effect in this slot: the stock names stay */
		return;
	const struct names *n = &D->names[slot][index_of(s, D->cur[slot])];
	uint32_t a = FIRST_DESC(slot);
	for (int t = 0; t < 2; t++) {
		volatile uint32_t *da = (volatile uint32_t *)(D->desc[t] + 0x38u * a);
		volatile uint32_t *db = (volatile uint32_t *)(D->desc[t] + 0x38u * (a + 1));
		da[0x2c / 4] = n->longa;
		da[0x30 / 4] = n->group;
		da[0x34 / 4] = n->shorta;
		db[0x2c / 4] = n->longb;
		db[0x30 / 4] = n->group;
		db[0x34 / 4] = n->shortb;
	}
	*(volatile uint32_t *)(OBJECT(a) + 0x20) = n->fmta;
	*(volatile uint32_t *)(OBJECT(a + 1) + 0x20) = n->fmtb;
}

static uint32_t irq_off(void)
{
	uint32_t sr, masked;
	__asm__ volatile("move.w %%sr, %0" : "=d"(sr));
	masked = sr | 0x0700;
	__asm__ volatile("move.w %0, %%sr" : : "d"(masked) : "memory");
	return sr;
}

static void irq_restore(uint32_t sr)
{
	__asm__ volatile("move.w %0, %%sr" : : "d"(sr) : "memory");
}

static int valid(const volatile uint8_t *h)
{
	return h[HDR + 2] == (uint8_t)(0x5a + h[HDR] + h[HDR + 1]);
}

static void put(volatile uint8_t *h, uint8_t delay, uint8_t reverb)
{
	uint32_t sr = irq_off();
	h[HDR] = delay;
	h[HDR + 1] = reverb;
	h[HDR + 2] = (uint8_t)(0x5a + delay + reverb);
	irq_restore(sr);
}

/* The playing pattern's header, or 0. Its number is read byte by byte: a pattern may be only 2-aligned. */
static const volatile uint8_t *playing_header(void)
{
	uint8_t *root = ROOT, *p = PLAYING;
	if (!root || !p)
		return 0;
	uint32_t n = (uint32_t)p[30706] << 24 | (uint32_t)p[30707] << 16 | (uint32_t)p[30708] << 8 | p[30709];
	if (n >= 96)
		return 0;
	return *(uint8_t *volatile *)(root + 5192 + 732 * n + 60);
}

static uint8_t choice(const volatile uint8_t *h, int slot)
{
	return h && valid(h) ? h[HDR + slot] : 0;
}

/* entries.S's fx_load, in the loader after its fields: dst the working pattern's header, src the saved one's. */
void fx_hdr_load(volatile uint8_t *dst, const volatile uint8_t *src)
{
	if (valid(src))
		put(dst, src[HDR], src[HDR + 1]);
	else
		put(dst, 0, 0);
}

/* entries.S's fx_init, in the initializer of a new pattern's header. */
void fx_hdr_init(volatile uint8_t *h)
{
	put(h, 0, 0);
}

void fx_run(int slot, int32_t *out, const int32_t *in, const void *params)
{
	const struct slot *s = &D->slot[slot];
	uint8_t id = choice(playing_header(), slot);
	if (id != D->cur[slot]) {
		D->cur[slot] = id;
		name_slot(slot);
	}
	const struct entry *e = &s->e[index_of(s, id)];
	if (e->id != D->played[slot]) {
		if (D->played[slot] == 0)               /* the stock effect stops: a block of silence through it */
			((fx_fn)s->e[0].process)(D->scratch, D->zeros, D->zeros);
		if (e->reset)
			((void (*)(void))e->reset)();
		D->played[slot] = (uint8_t)e->id;
	}
	((fx_fn)e->process)(out, in, params);
}

int fx_step(uint32_t desc, int32_t step)
{
	int slot = desc == FIRST_DESC(0) ? 0 : desc == FIRST_DESC(1) ? 1 : -1;
	if (slot < 0 || D->slot[slot].count < 2)
		return 0;                               /* not the slots' gesture: the stock call */
	uint32_t now = TIMER;
	uint8_t dir = step > 0 ? 1 : 2;
	if (slot != D->last_slot || dir != D->last_dir || now - D->last_time > PAUSE)
		D->acc = 0;
	D->last_slot = (uint8_t)slot;
	D->last_dir = dir;
	D->last_time = now;
	if (++D->acc < DETENTS)
		return 1;
	D->acc = 0;
	uint8_t *root = ROOT, *p, *object;
	volatile uint8_t *h;
	if (!root || !(p = SHOWN(root)) || !(h = *(uint8_t *volatile *)((object = p + 44) + 16)))
		return 1;                               /* no pattern shown */
	uint8_t ids[SLOTS] = {choice(h, 0), choice(h, 1)};
	const struct slot *s = &D->slot[slot];
	uint32_t i = index_of(s, ids[slot]);
	if (dir == 1 ? i + 1 >= s->count : i == 0)
		return 1;                               /* at the end of the table */
	ids[slot] = (uint8_t)s->e[dir == 1 ? i + 1 : i - 1].id;
	put(h, ids[0], ids[1]);
	((void (*)(uint8_t *, uint32_t))(*(uint32_t **)object)[4])(object, 0);
	if (h == playing_header()) {                /* what is heard: its names at once */
		uint32_t sr = irq_off();
		D->cur[slot] = ids[slot];
		name_slot(slot);
		irq_restore(sr);
	}
	return 1;
}
