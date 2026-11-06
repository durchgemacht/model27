/* Transpose, a part of model27's builder, with entries.S (the plan of 2026-11-05, _scratch/machines-transpose/plan.md;
 * the note's number is fixed when it moves into notes/). Addresses are VAs of OS 1.13.
 *
 * MACHINES held in keyboard mode (GRID RECORDING off, no pattern selection armed), on the active track:
 *   - TRIG 15 / 16 move the TRIG keyboard an octave down / up, two at most either way, on top of KBT (TRACK SETUP),
 *     which is never written: tr_kbt adds 12 semitones an octave where the keyboard reads KBT (0x4001a164), clamped
 *     to KBT's own -60..+60. The keyboard's note is key index + 52 + KBT (0x4001a236), so only the keys move; the
 *     sequencer never reads KBT.
 *   - TRIG 8 / 9 / 11 / 12 make the track's pitch jump -7 / -5 / +5 / +7 semitones from its PITCH; the key of the
 *     jump in force pressed again goes back to 0. tr_pitch adds 0x100 a semitone to the PITCH word (k 10) of the
 *     smoother's output (0x400597a8 -> 0x40058474, the words at 0x8000100c + 14 + 66 t + 20), which the voices read in
 *     the same block: the jump is at once, on the note that plays, on p-locked steps too, and the smoother's state is
 *     not touched. The sum is clamped to PITCH's range, 0x2800..0x5800 (-24..+24).
 *   - The six keys' LEDs show it (tr_leds): TRIG 15 / 16 dim at 0, mid at one octave, full at two; the jump in force
 *     full, the three others dim. The states are set at the start of the LED frame, before every view, so they win
 *     (0x40005f86 keeps the first state). Dim and mid are states 0x102 and 0x202, which the OS treats as on (the base
 *     bit) and which its blink leaves alone; tr_leds also puts their bits in two masks per latch row.
 *   - The dimming (step P2), notes/45 §6's principle written anew: the panel interrupt's LED step 0 (0x40059dea,
 *     once a cycle of 1 ms) goes to tr_led (entries.S) -> tr_led_c, which loads the latch rows with a masked LED out
 *     of their turn, a dim LED lit 1 cycle of n, a mid one 2 of n (n = 4: 1/4 and 1/2 at 250 Hz; 3: 1/3 and 2/3 at
 *     333 Hz), the rows' phases staggered, each write 2 us apart by PIT3's counter. Every other LED of the row keeps
 *     what the stock turn latched last, at the same instants. Without a mask, and once every row holds its stock byte
 *     again, the step does what the stock one does.
 *   - tr_keys takes those presses and their releases, sets the shortcut layer's +0x13 (a shortcut acted while MACHINES
 *     was held), so that MACHINES' release does not open the MACHINES list, and asks for a new LED frame. Every other
 *     key, mode or held combination goes to the stock key handler (0x4001a0d2) unchanged.
 * The values are per track, in RAM only: tr_pitch clears them all when the playing pattern's number changes (read in
 * every audio block, so an old jump never sounds into the new pattern).
 *
 * The data block (tr_data, part.json "data"), written by the composer and zero at boot but for sc:
 *   +0  sc     the shortcut layer's data block (its +0x13 marks MACHINES used), 0 without the layer
 *   +4  last   the playing pattern's number when last seen (0xffffffff: none)
 *   +8  oct    per track the octave, -2..+2 (signed bytes)
 *   +14 jump   per track the jump in force: 0 none, 1..4 the keys TRIG 8, 9, 11, 12
 *   +20 held   the keys whose press this part took (bit 0..3 TRIG 8, 9, 11, 12, bit 4 TRIG 15, bit 5 TRIG 16)
 *   +21 any    a mask is set; +24 m1, +32 m2 the masks per latch row (dim, mid), written by tr_leds every frame
 *   +40 latched, +48 cur  per row the byte the stock turn latched last and the byte the latch holds (tr_led_c)
 *   +56 ph, +57 known (rows latched once), +58 n (the period, written by the composer), +59 dirty (a row dimmed)
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>

#define KEY_HELD ((uint32_t (*)(uint32_t))0x4007faf4)          /* (logical key) -> 1 while held */
#define UI_STATE ((uint8_t *(*)(void))0x400cf9a8)
#define GRID_MODE ((uint32_t (*)(uint8_t *))0x4006b978)       /* (state) -> byte: GRID RECORDING (+357, +358) */
#define SELECT_ARMED ((uint32_t (*)(uint8_t *))0x4006bb18)    /* (state) -> byte: the pattern selection (+389) */
#define PROJECT ((void *(*)(void))0x400cf866)
#define PROJECT_TRACKS ((void *(*)(void *))0x4000eb90)
#define ACTIVE_TRACK ((uint32_t (*)(void *))0x40012442)        /* the keyboard's own: the selected track, 0..5 */
#define KB_KEYS ((uint32_t (*)(void *, void *))0x4001a0d2)    /* KeyboardView's stock key handler */
#define KBT_GET ((int32_t (*)(void *))0x40016da6)              /* (track holder) -> KBT, -60..+60 */
#define SMOOTHER ((int16_t *(*)(void *))0x40058474)            /* the parameters' smoother, -> its output words */
#define LED_SET ((void (*)(void *, uint32_t, uint32_t, uint32_t))0x40005f86)   /* (leds, led, state, colour) */
#define VIEW_LEDS ((void (*)(void *))0x400760ba)              /* a new LED frame */
#define PLAYING (*(uint8_t *volatile *)0x40a7887c)            /* the playing pattern, its number at +30706 */
#define LED_COLOUR 0x404a8c68u                                 /* what TrackSelectionView passes along */
#define LED_BITS 0x4010abf8u                                   /* logical LED -> bit of the 7 latch bytes, or -1 */

#define K_FUNC 1
#define K_TRACK 2
#define K_MACHINES 5
#define USED 0x13                                           /* the shortcut layer's data block */
#define PITCH_AT 34                                         /* track t's PITCH word: 14 + 66 t + 2 * 10 */
#define PITCH_MIN 0x2800
#define PITCH_MAX 0x5800
#define FULL 2u                                             /* LED states: on, mid, dim */
#define MID 0x202u
#define DIM 0x102u

struct data {
	uint8_t *sc;                                /* +0 */
	uint32_t last;                              /* +4 */
	int8_t oct[6];                              /* +8 */
	uint8_t jump[6];                            /* +14 */
	uint8_t held;                               /* +20 */
	uint8_t any;                                /* +21 a dim or mid LED in m1 / m2 */
	uint8_t pad[2];
	uint8_t m1[8];                              /* +24 per latch row, the LEDs lit 1 cycle of n (dim) */
	uint8_t m2[8];                              /* +32 per latch row, the LEDs lit 2 cycles of n (mid) */
	uint8_t latched[8];                         /* +40 per row, the byte the stock turn latched last (1 = off) */
	uint8_t cur[8];                             /* +48 per row, the byte the latch holds now */
	uint8_t ph;                                 /* +56 the phase, 0..n-1 */
	uint8_t known;                              /* +57 the rows latched once since boot (bits) */
	uint8_t n;                                  /* +58 cycles of 1 ms a period: 4 (250 Hz) or 3 (333 Hz) */
	uint8_t dirty;                              /* +59 a row holds a dimmed byte */
};                                                  /* 60 bytes */

extern char tr_data[];
#define D ((volatile struct data *)tr_data)

/* Byte by byte: the playing pattern's number may be only 2-aligned (as fxslot reads it). */
static uint32_t rd32(const volatile uint8_t *p)
{
	return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 | p[3];
}

/* The bit of a key this part answers, by its code (TRIG n is 15 + n), or -1. */
static int key_bit(uint32_t code)
{
	switch (code) {
	case 23: return 0;                          /* TRIG 8: -7 */
	case 24: return 1;                          /* TRIG 9: -5 */
	case 26: return 2;                          /* TRIG 11: +5 */
	case 27: return 3;                          /* TRIG 12: +7 */
	case 30: return 4;                          /* TRIG 15: an octave down */
	case 31: return 5;                          /* TRIG 16: an octave up */
	default: return -1;
	}
}

/* A jump's semitones as PITCH's 8.8 word: 1..4 = -7, -5, +5, +7. */
static int32_t jump_word(uint32_t j)
{
	int32_t s = (j == 1 || j == 4) ? 0x700 : 0x500;
	return j <= 2 ? -s : s;
}

/* MACHINES held, FUNC and TRACK not, in keyboard mode. */
static int active(void)
{
	uint8_t *st;
	if (!KEY_HELD(K_MACHINES) || KEY_HELD(K_FUNC) || KEY_HELD(K_TRACK))
		return 0;
	st = UI_STATE();
	if (!st || (GRID_MODE(st) & 0xff) || (SELECT_ARMED(st) & 0xff))
		return 0;
	return 1;
}

/* The active track as the keyboard finds it, or 6 without a project. */
static uint32_t track(void)
{
	void *p = PROJECT();
	uint32_t t;
	if (!p)
		return 6;
	t = ACTIVE_TRACK(PROJECT_TRACKS(p));
	return t < 6 ? t : 6;
}

/* KeyboardView's key handler (its vtable +8, 0x400ff9cc): (view, event), 1 when taken. */
uint32_t tr_keys(void *view, uint8_t *ev)
{
	uint32_t code = *(const uint32_t *)(ev + 12), flags = *(const uint32_t *)(ev + 16), t;   /* 0x4007240c, +16 */
	int bit = key_bit(code);
	uint8_t m;
	if (bit < 0)
		return KB_KEYS(view, ev);
	m = (uint8_t)(1u << bit);
	if (!(flags & 1)) {                         /* a release: ours when its press was */
		if (D->held & m) {
			D->held &= (uint8_t)~m;
			return 1;
		}
		return KB_KEYS(view, ev);
	}
	if (flags & 0x28)                           /* a repeat or a long press: ours when the press was */
		return (D->held & m) ? 1 : KB_KEYS(view, ev);
	if (!active() || (t = track()) > 5)
		return KB_KEYS(view, ev);
	D->held |= m;
	if (bit == 4 || bit == 5) {
		int o = D->oct[t] + (bit == 5 ? 1 : -1);
		D->oct[t] = (int8_t)(o < -2 ? -2 : o > 2 ? 2 : o);
	} else {
		uint8_t j = (uint8_t)(bit + 1);
		D->jump[t] = D->jump[t] == j ? 0 : j;
	}
	if (D->sc)
		D->sc[USED] = 1;
	VIEW_LEDS(view);
	return 1;
}

/* entries.S's tr_kbt, where the keyboard reads KBT: the track's octave on top, clamped to KBT's range. */
int32_t tr_kbt_c(void *holder, uint32_t t)
{
	int32_t k = KBT_GET(holder);
	if (t < 6)
		k += 12 * D->oct[t];
	return k < -60 ? -60 : k > 60 ? 60 : k;
}

/* The audio function's call of the smoother (0x400597a8): its output, then the jumps on the PITCH words. */
int16_t *tr_pitch(void *targets)
{
	int16_t *w = SMOOTHER(targets);
	const volatile uint8_t *p = PLAYING;
	uint32_t n = p ? rd32(p + 30706) : 0xffffffffu, t;
	if (n != D->last) {                         /* another pattern: back to the set values */
		D->last = n;
		for (t = 0; t < 6; t++) {
			D->oct[t] = 0;
			D->jump[t] = 0;
		}
	}
	for (t = 0; t < 6; t++) {
		uint32_t j = D->jump[t];
		if (j) {
			volatile int16_t *x = (volatile int16_t *)((uint8_t *)w + PITCH_AT + 66 * t);
			int32_t v = *x + jump_word(j);
			*x = (int16_t)(v < PITCH_MIN ? PITCH_MIN : v > PITCH_MAX ? PITCH_MAX : v);
		}
	}
	return w;
}

/* One LED's state, and its bit in the dimming masks: dim in m1, mid in m2, full in neither. */
static void led(void *leds, uint32_t n, uint32_t state, uint8_t *m1, uint8_t *m2)
{
	int32_t bit = *(const int32_t *)(LED_BITS + 4 * n);
	LED_SET(leds, n, state, LED_COLOUR);
	if (bit < 0 || bit >= 56)
		return;
	if (state == DIM)
		m1[bit >> 3] |= (uint8_t)(1u << (bit & 7));
	else if (state == MID)
		m2[bit >> 3] |= (uint8_t)(1u << (bit & 7));
}

/* entries.S's tr_frame, at the start of the LED frame, before the views: the six keys' states, and the masks the
 * panel interrupt dims them with (tr_led_c); none when MACHINES is not held in keyboard mode. */
void tr_leds(void *leds)
{
	uint8_t m1[8] = {0}, m2[8] = {0}, any = 0;
	uint32_t t, i;
	int o;
	if (leds && active() && (t = track()) <= 5) {
		o = D->oct[t];
		led(leds, 15, o < 0 ? (o == -1 ? MID : FULL) : DIM, m1, m2);
		led(leds, 16, o > 0 ? (o == 1 ? MID : FULL) : DIM, m1, m2);
		for (i = 0; i < 4; i++)             /* jump i + 1 on TRIG 8, 9, 11, 12 */
			led(leds, i < 2 ? 8 + i : 9 + i, D->jump[t] == i + 1 ? FULL : DIM, m1, m2);
	}
	for (i = 0; i < 8; i++) {
		D->m1[i] = m1[i];
		D->m2[i] = m2[i];
		any |= m1[i] | m2[i];
	}
	D->any = any ? 1 : 0;
}

/* The panel's port (Rapid GPIO) and PIT3's counter (notes/45 §3). */
#define PORT_DIR (*(volatile uint16_t *)0x8c000000)
#define PORT_DATA (*(volatile uint16_t *)0x8c000002)
#define PORT_CLR (*(volatile uint16_t *)0x8c000006)
#define PORT_SET (*(volatile uint16_t *)0x8c00000a)
#define PCNTR (*(volatile uint16_t *)0xfc08c004)
#define P3 11265                                    /* PIT3's period in counts: PMR 0x2c00 + 1 */
#define WAIT 272                                    /* 2 us at 135.168 MHz, what notes/45 tried on the device */

/* At least WAIT counts of PIT3 from now, 64 reads at most (a counter that stood still cannot hang the interrupt). */
static void wait(void)
{
	int32_t t0, d;
	uint32_t i;
	__asm__ volatile ("nop");                   /* the writes before it finished */
	t0 = PCNTR;
	for (i = 1; i < 64; i++) {                  /* with the first, 64 reads */
		d = t0 - (int32_t)PCNTR;            /* the counter counts down and reloads */
		if (d < 0)
			d += P3;
		if (d >= WAIT)
			return;
	}
}

/* A latch row loaded out of its turn, as the stock steps 0, 1 and 2 load it: the byte and the row, the strobe up,
 * the strobe down. */
static void latch(uint32_t row, uint32_t byte)
{
	PORT_DATA = (uint16_t)(byte << 8 | row << 5);
	wait();
	PORT_SET = 8;
	wait();
	PORT_CLR = 0xfff7;
	wait();
}

/* The LEDs of row r off in phase ph of a period of n: the masks' (dim off from the 2nd cycle, mid from the 3rd), the
 * rows' phases staggered by their number. */
static uint32_t off_bits(uint32_t r, uint32_t ph, uint32_t n)
{
	uint32_t p = ph + r, off = 0;
	while (p >= n)
		p -= n;
	if (p >= 1)
		off |= D->m1[r];
	if (p >= 2)
		off |= D->m2[r];
	return off;
}

/* entries.S's tr_led, the panel interrupt's LED step 0 (0x40059dea), once a cycle of 1 ms: byte the copy's byte of
 * the row whose turn it is (r0, 0..6; 1 = off). DIR first, as the stock step; then, when a mask is set or a row still
 * holds a dimmed byte, the phase steps on and every row whose byte must change is loaded at once, from what the stock
 * turn latched last (latched[]) with the masks' LEDs off; the turn row too, from its last byte, so that its masked
 * LEDs change now as on the other rows and its other LEDs when the stock steps 1 and 2 latch the byte returned (the
 * new one with the masks' LEDs off), at the stock instant (notes/45 §6). */
uint32_t tr_led_c(uint32_t byte, uint32_t r0)
{
	uint32_t n, ph, r, s, dirty = 0;
	PORT_DIR = 0xffff;
	if (!D->any && !D->dirty) {
		D->latched[r0] = (uint8_t)byte;
		D->cur[r0] = (uint8_t)byte;
		D->known |= (uint8_t)(1u << r0);
		return byte;
	}
	n = D->n;
	if (n < 2 || n > 8)
		n = 4;
	ph = D->ph + 1u;
	if (ph >= n)
		ph = 0;
	D->ph = (uint8_t)ph;
	for (r = 0; r < 7; r++) {
		uint32_t v;
		if (!(D->known >> r & 1))
			continue;
		v = (D->latched[r] | off_bits(r, ph, n)) & 0xff;
		if (v != D->cur[r]) {
			latch(r, v);
			D->cur[r] = (uint8_t)v;
		}
	}
	s = (byte | off_bits(r0, ph, n)) & 0xff;    /* the turn row's new byte, latched by the stock steps 1 and 2 */
	D->latched[r0] = (uint8_t)byte;
	D->cur[r0] = (uint8_t)s;
	D->known |= (uint8_t)(1u << r0);
	for (r = 0; r < 7; r++)
		if ((D->known >> r & 1) && D->cur[r] != D->latched[r])
			dirty = 1;
	D->dirty = (uint8_t)dirty;
	return s;
}
