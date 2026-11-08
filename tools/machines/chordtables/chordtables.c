/* CHORD Tables: the stock CHORD machine of the Model:Cycles OS 1.13 plays wavetables from the +Drive (notes/66).

   Since 0.3 (notes/66 §27 to §31) the pattern chooses one table for every CHORD track, and the whole table takes the
   stock table's place in SRAM: SWEEP, an LFO on it included, then reads SRAM as on the stock OS.

   - The choice: PATTERN + SWEEP on a CHORD track steps the shown pattern's byte 36 through 0..127, two steps a table
     (the table is the value / 2: 0 the stock table, 1 to 63 the files /Wavetables/01 to /Wavetables/63); byte 37 is a
     check, 0x5a + byte 36 (notes/66 §27.10, §28). The OS saves the header's 64 bytes but loads and initializes only
     its own fields, so ct_load and ct_init (entries.S) keep the two bytes in the pattern's loader and initializer.
     ct_knob, in front of the knob lookup, gives descriptor 10 (an unused "Error" one, notes/66 §28.3) for PATTERN +
     SWEEP on CHORD (descriptor 73) so that the popup shows the table; ct_keys, at the encoder handler's question for
     TRACK, steps on descriptor 10 before any edit; ct_release ends the pattern selection's wait as the effect slots
     do. All five are chain hooks (notes/66 §30.2): the composer puts them in front of the parts that take the same
     sites, and each calls the entry behind it, or does the stock work when there is none.
   - The audio (cw_setup in place of jsr 0x400a8080 at 0x400ab15e, CHORD's one call for its two frames, notes/66
     §1.1): every call reads the playing pattern's choice. The table wanted gets the list the voices read at once
     (step 1 of notes/66 §27.3): a position whose SRAM slot already holds the wanted frame reads the slot, any other
     reads the table's buffer in SDRAM, and the render brings the new frames in by its own transition (§29.4). Then
     each call moves one position home: the wanted frame copied into its slot once no CHORD sub-voice points at the
     slot, and at once every sub-voice pointer to the buffer's frame (+168, +172 and the previous pair +176, +180)
     moved to the slot, the same content, so the render sees no change (§29.6). The slots are the stock table's own
     SRAM frames, positions 2 to 31; position 0 is the OS's sine and position 1 stays in SDRAM, as in the stock
     table (§19.1, §28.5). With the stock table wanted and every slot home, the stock function itself runs.
   - The move, once, on the screen's tick: the stock frames copied into the RAM claim (STOCK), so that the stock
     table can come back home the same way.
   - The loader (ct_hook_tick in place of jsr 0x40076be4 at 0x400075f0, the screen's redraw, about 30 Hz; with SAMPLE
     through the builder's tick dispatcher): the files /Wavetables/01 to /63, one per tick, once the drive is mounted
     and again whenever the drive's file index changes. A file is a sample file (64-byte header, big-endian 16-bit),
     mono, of k x 256 samples, k = 1 to 32. Its first frame must be a sine (the OS's, within 4 steps): if it is not,
     the OS's sine goes in front of its frames (notes/66 §27.10, §28.5). The frames are spread over the 32 positions
     SWEEP reaches by linear crossfades, each 257 Q31 samples with the last equal to the first.
   - Memory: the RAM claim 0x43400000..0x43700000 holds one file as read, 71 buffers of a table each (63 tables and 8
     spare), then the stock frames' copy. A table is published by one 32-bit write of its slot; the buffer it
     replaces is reused once it is not the table wanted and no voice points into it.

   The file system calls follow One-Shot's tick (tools/machines/sampler/machine/pool.c): the tick takes its own
   lock (the redraw also runs from another task) and leaves the drive alone while the running task holds the file
   system's lock or the drive is not mounted. Plain C99, no libc.

   License: MIT (LICENSE next to this file). */
#include <stdint.h>

typedef int32_t s32;
typedef uint32_t u32;
typedef int16_t s16;
typedef uint8_t u8;

/* --- the audio side ------------------------------------------------------------------------------------------------ */
#define VOICE0          0x42308828u                 /* voice of track 0; one per track, 0x31c apart */
#define VSTRIDE         0x31c
#define SUB_STRIDE      120                         /* CHORD's four sub-voices */
#define SUB_FRAMES      168                         /* a sub-voice's +168 f0, +172 f1, +176 and +180 the previous */
#define CHORD_SETUP     ((void (*)(char *, const char *))0x400a8080)
#define P_SWEEP         0x1a
#define STOCK_TABLE     ((const u32 *)0x40118590)   /* the selector's: frame n (1..32) at entry n - 1 */
#define SINE            0x8000eee4u                 /* the selector's answer outside 1..32 */
#define SRAM_LO         0x80000000u                 /* the internal SRAM, 64 KB, not cached */
#define SRAM_HI         0x80010000u
#define IN_SRAM(a)      ((u32)(a) - SRAM_LO < SRAM_HI - SRAM_LO)

/* --- the patterns, the keys, the descriptors ----------------------------------------------------------------------- */
#define ROOT            (*(u8 *volatile *)0x40fe4228)   /* the patterns' singleton (notes/42 §5) */
#define PLAYING         (*(u8 *volatile *)0x40a7887c)   /* the playing pattern */
#define SHOWN           ((u8 *(*)(u8 *))0x4000f208)     /* the shown pattern's object, from the singleton */
#define HDR             36                          /* the header's byte 36: the value 0..127; 37: 0x5a + byte 36 */
#define VALUES          128
#define KEY_HELD        ((s32 (*)(u32))0x4007faf4)  /* (logical key) -> 1 while held */
#define K_PATTERN       3
#define SWEEP_DESC      73                          /* Chord Sweep (notes/66 §28.1) */
#define TABLE_DESC      10                          /* an unused "Error" descriptor, display only (notes/66 §28.3) */
#define STOCK_DESC      0x4010dce0u                 /* the stock descriptor table, 0x38 bytes an entry */
#define DSTRIDE         0x38
#define UI_OBJ(i)       ((u8 *)0x40a71754 + 100 * (i))      /* descriptor i's interface object (notes/47 §3.3) */
#define K0_RANGE        0x7f00                      /* the display's range, as the Track FX' type (fltslot) */

typedef u32 (*lookup_fn)(void *view, u32 knob, u32 func, s32 track);

extern char ct_next_knob[];                         /* the knob lookup behind ct_knob: a part's, or the stock one */
extern char ct_desc_used[];                         /* the descriptor table the OS uses (a copy with an added machine) */

/* --- the file system on the +Drive (One-Shot's os.h, notes/66 §11.2, §11.3) ----------------------------------------- */
#define FS_MOUNTED      (*(volatile u32 *)0x40f07cf4)
#define FS_LOCK_HOLDER  (*(void *volatile *)0x40fe6df0)
#define RUNNING_TASK    (*(void *volatile *)0x422fef30)
#define FS_OPEN(path, mode, h)  ((s32 (*)(const char *, const char *, u32 *))0x4007bc5e)(path, mode, h)
#define FS_CLOSE(h)     ((s32 (*)(u32 *))0x4007bc1c)(h)
#define FS_ENTRY(ino, h)        ((s32 (*)(u32, u32 *))0x4007de78)(ino, h)     /* {inode, id, size, -} */
#define FS_READ(buf, n, h)      ((s32 (*)(void *, u32, u32 *))0x4007baaa)(buf, n, h)
#define INDEX_COUNT     (*(const volatile u32 *)0x401fb8a0)
#define INDEX           ((const volatile u32 *)0x401fb8a4)           /* pairs {id, inode} */
#define INDEX_MAX       8192
#define TICK_STOCK      ((u32 (*)(void *))0x40076be4)

/* --- the tables --------------------------------------------------------------------------------------------------- */
#define TABLES          63                          /* the value / 2 = 1..63: /Wavetables/01 .. 63 */
#define FRAMES          32                          /* SWEEP >> 10 reaches 0..31; pointer 32 repeats 31 */
#define FRAME_LEN       257
#define POINTERS        (FRAMES + 1)
#define FIRST_SLOT      2                           /* positions 2..31 live in the stock table's SRAM frames */
#define CYCLE           256                         /* samples of a frame in a file */
#define FILE_MAX        32                          /* frames in a file */
#define HEADER          64
#define BUFFERS         (TABLES + 8)
#define RAM             0x43400000u                 /* the RAM claim, to 0x43700000 */
#define STAGE_BYTES     (FILE_MAX * CYCLE * 2)
#define BUF_BYTES       ((POINTERS * 4 + FRAMES * FRAME_LEN * 4 + 15) & ~15u)
#define STAGE           ((s16 *)RAM)
#define BUF(b)          ((u32 *)(RAM + STAGE_BYTES + (u32)(b) * BUF_BYTES))
#define FREE            0
#define RETIRED         0xff                        /* replaced, until it is not wanted and no voice points into it */
#define STOCK           BUF(BUFFERS)                /* the stock frames' copy: 33 pointers, then the frames */
#define MOVED           1                           /* ct_moved: the stock frames are copied, tables may come */
#define REFUSED         0xff                        /* the stock table is not as expected: the stock table for good */
#define SINE_STEPS      4                           /* a file's first frame within this of the OS's sine is a sine */

/* The state, roots of the object so that a proof finds them in the composed tweak's symbols. */
u32 *volatile ct_slot[TABLES];                      /* table n + 1: its pointer list, or 0 */
u32 ct_slot_id[TABLES];                             /* the id of the file it came from */
u8 ct_owner[BUFFERS];                               /* FREE, 1 + the slot it holds, or RETIRED */
u32 ct_scan;                                        /* 1..63: the file the tick reads next; 0: none */
volatile u32 ct_moved;                              /* 0, MOVED or REFUSED */
const u32 *volatile ct_tag[FRAMES];                 /* position i (2..31): the list whose frame i its slot holds */
const u32 *volatile ct_want;                        /* the list the voices' list was made for (STOCK, or a buffer) */
u32 ct_list[POINTERS];                              /* what the voices read: per position, its slot or the wanted list's */
volatile u32 ct_away;                               /* bit i: position i not home yet (its slot holds another frame) */
u32 ct_copies;                                      /* frames copied into the slots since boot, for the proof */
static u32 cursor;                                  /* the position tried last */
static u32 sig_count, sig_sum;                      /* the file index when the scan started */
static u8 seen;                                     /* a scan has started since the drive was mounted */
static volatile unsigned char busy;
static const char long_name[] = "Wavetable", short_name[] = "WAVE";

/* --- the patterns ---------------------------------------------------------------------------------------------------- */

static u32 irq_off(void)
{
	u32 sr, masked;

	__asm__ volatile ("move.w %%sr, %0" : "=d"(sr));
	masked = sr | 0x0700;
	__asm__ volatile ("move.w %0, %%sr" : : "d"(masked) : "memory");
	return sr;
}

static void irq_restore(u32 sr)
{
	__asm__ volatile ("move.w %0, %%sr" : : "d"(sr) : "memory");
}

static int valid(const volatile u8 *h)
{
	return h[HDR] < VALUES && h[HDR + 1] == (u8)(0x5a + h[HDR]);
}

static void put(volatile u8 *h, u32 v)
{
	u32 sr = irq_off();

	h[HDR] = (u8)v;
	h[HDR + 1] = (u8)(0x5a + v);
	irq_restore(sr);
}

/* The playing pattern's header, or 0. Its number is read byte by byte: a pattern may be only 2-aligned (fxslot.c). */
static const volatile u8 *playing_header(void)
{
	u8 *root = ROOT, *p = PLAYING;
	u32 n;

	if (!root || !p)
		return 0;
	n = (u32)p[30706] << 24 | (u32)p[30707] << 16 | (u32)p[30708] << 8 | p[30709];
	if (n >= 96)
		return 0;
	return *(u8 *volatile *)(root + 5192 + 732 * n + 60);
}

/* The shown pattern's header and its header object (for the notify), or 0. */
static volatile u8 *shown_header(u8 **object)
{
	u8 *root = ROOT, *p;

	if (!root || !(p = SHOWN(root)))
		return 0;
	*object = p + 44;
	return *(u8 *volatile *)(*object + 16);
}

/* entries.S's ct_load, in the loader after its fields: dst the working pattern's header, src the saved one's. */
void ct_hdr_load(volatile u8 *dst, const volatile u8 *src)
{
	put(dst, valid(src) ? src[HDR] : 0);
}

/* entries.S's ct_init, in the initializer of a new pattern's header. */
void ct_hdr_init(volatile u8 *h)
{
	put(h, 0);
}

/* The popup's value (descriptor 10's formatter): the shown pattern's table, 0 to 63. */
void ct_fmt(void *fn, s32 v, char *buf)
{
	u8 *object;
	const volatile u8 *h = shown_header(&object);
	u32 n = h && valid(h) ? h[HDR] >> 1 : 0;

	(void)fn;
	(void)v;
	if (n >= 10)
		*buf++ = (char)('0' + n / 10);
	*buf++ = (char)('0' + n % 10);
	*buf = 0;
}

/* ParameterPageView's knob lookup (its vtable's +0x7c, 0x401005a8), in front of the one behind it: PATTERN held + SWEEP
   on a CHORD track (descriptor 73) gives descriptor 10, display only: group -1 and k 0 (the OS builds nothing on it, an
   edit would write the unused k 0), no CC, the names and this package's formatter, the knob's steps of Chord Sweep. */
u32 ct_knob(void *view, u32 knob, u32 func, s32 track)
{
	u32 d = ((lookup_fn)(u32)ct_next_knob)(view, knob, func, track), k;
	u8 *o = UI_OBJ(TABLE_DESC);

	if (d != SWEEP_DESC || !KEY_HELD(K_PATTERN))
		return d;
	for (k = 0; k < 2; k++) {
		volatile u32 *row = (volatile u32 *)((k ? (u32)ct_desc_used : STOCK_DESC) + DSTRIDE * TABLE_DESC);

		row[1] = 0;                             /* k 0 */
		row[2] = 0;
		row[3] = K0_RANGE;
		row[4] = 0;
		row[5] = 0;
		row[6] = 0xffffffffu;                   /* no CC (the stock row carries CC 99 / 98) */
		row[7] = 0xffffffffu;                   /* no NRPN */
		row[8] = 0;
		row[0x2c / 4] = (u32)long_name;
		row[0x34 / 4] = (u32)short_name;
	}
	*(volatile u32 *)(o + 0x10) = *(volatile u32 *)(UI_OBJ(SWEEP_DESC) + 0x10);    /* the knob's steps */
	*(volatile u32 *)(o + 0x20) = (u32)ct_fmt;
	*(volatile u32 *)(o + 0x2c) = 0;                /* no "Error" picture */
	return TABLE_DESC;
}

/* entries.S's ct_keys on descriptor 10: the handler's step moves the shown pattern's value, 0..127, two a table. The
   step is the interface object's (0x4006f96a), in 8.8 as the parameters' values: 0x100 a detent, more for a fast turn
   (notes/70 §2); a finer step (FUNC) still moves one. */
void ct_step(s32 step)
{
	u8 *object;
	volatile u8 *h = shown_header(&object);
	s32 v, d = step / 256;

	if (!h)
		return;                                 /* no pattern shown */
	if (!d)
		d = step > 0 ? 1 : step < 0 ? -1 : 0;
	v = (valid(h) ? h[HDR] : 0) + d;
	put(h, v < 0 ? 0 : v >= VALUES ? VALUES - 1 : (u32)v);
	((void (*)(u8 *, u32))(*(u32 **)object)[4])(object, 0);    /* the header's notify, as the stock setters */
}

/* --- the audio side ------------------------------------------------------------------------------------------------ */

/* The list wanted by the playing pattern: STOCK, or a loaded table's buffer. */
static const u32 *wanted(void)
{
	const volatile u8 *h = playing_header();
	u32 n;

	if (!h || !valid(h))
		return STOCK;
	n = h[HDR] >> 1;
	return n && ct_slot[n - 1] ? ct_slot[n - 1] : STOCK;
}

static u32 slot(u32 i)
{
	return STOCK_TABLE[i - 1];
}

/* The voices' list for the wanted list w (step 1): a position whose slot holds w's frame reads the slot, any other
   reads w's own frame; position 0 is the sine and 1 is w's, in SDRAM. */
static void relist(const u32 *w)
{
	u32 i, away = 0;

	ct_list[0] = SINE;
	ct_list[1] = w[1];
	for (i = FIRST_SLOT; i < FRAMES; i++) {
		if (ct_tag[i] == w)
			ct_list[i] = slot(i);
		else {
			ct_list[i] = w[i];
			away |= 1u << i;
		}
	}
	ct_list[FRAMES] = ct_list[FRAMES - 1];
	ct_away = away;
	ct_want = w;
}

/* A sub-voice of any voice points at a (+168..+180): its frame is read there, in this block or the next. */
static int pointed(u32 a)
{
	const volatile u32 *v = (const volatile u32 *)(VOICE0 + SUB_FRAMES);
	u32 t, j;

	for (t = 0; t < 6; t++, v += VSTRIDE / 4)
		for (j = 0; j < 4; j++) {
			const volatile u32 *q = v + SUB_STRIDE / 4 * j;

			if (q[0] == a || q[1] == a || q[2] == a || q[3] == a)
				return 1;
		}
	return 0;
}

/* Every sub-voice pointer to from (+168..+180 of every voice) to to: the same content, so the render sees no change. */
static void move_pointers(u32 from, u32 to)
{
	volatile u32 *v = (volatile u32 *)(VOICE0 + SUB_FRAMES);
	u32 t, j, i;

	for (t = 0; t < 6; t++, v += VSTRIDE / 4)
		for (j = 0; j < 4; j++)
			for (i = 0; i < 4; i++)
				if (v[SUB_STRIDE / 4 * j + i] == from)
					v[SUB_STRIDE / 4 * j + i] = to;
}

/* 257 longs from src to dst: 32 moves of 8 longs, then the last one. */
static void copy_frame(s32 *dst, const s32 *src)
{
	u32 n = FRAME_LEN / 8;

	__asm__ volatile ("1:\n\t"
			  "movem.l (%1), %%d1-%%d7/%%a2\n\t"
			  "lea 32(%1), %1\n\t"
			  "movem.l %%d1-%%d7/%%a2, (%0)\n\t"
			  "lea 32(%0), %0\n\t"
			  "subq.l #1, %2\n\t"
			  "bne.s 1b\n\t"
			  "move.l (%1), (%0)"
			  : "+a"(dst), "+a"(src), "+d"(n)
			  :
			  : "d1", "d2", "d3", "d4", "d5", "d6", "d7", "a2", "cc", "memory");
}

/* One position home, the next away one whose slot no sub-voice points at: the wanted frame copied into the slot,
   every pointer to that frame moved to the slot, the list too (step 3 of notes/66 §27.3, §29.6). */
static void home_one(void)
{
	const u32 *w = ct_want;
	u32 n, i;

	for (n = 0; n < FRAMES; n++) {
		i = (cursor + 1 + n) & (FRAMES - 1);
		if (!(ct_away & (1u << i)) || pointed(slot(i)))
			continue;
		copy_frame((s32 *)slot(i), (const s32 *)w[i]);
		ct_tag[i] = w;
		move_pointers(w[i], slot(i));
		ct_list[i] = slot(i);
		if (i == FRAMES - 1)
			ct_list[FRAMES] = slot(i);
		ct_away &= ~(1u << i);
		ct_copies++;
		cursor = i;
		return;
	}
}

/* The stock selector 0x400a8060 on a list: n = 0..32 its pointer, the sine outside. */
static u32 sel(const u32 *list, s32 n)
{
	return (u32)n <= FRAMES ? list[n] : SINE;
}

void cw_setup(char *v, const char *p)
{
	u32 t = ((u32)v - VOICE0) / VSTRIDE;
	const u32 *w;
	s32 sweep, i, j;
	u32 xf, f0, f1;

	if (t > 5 || ct_moved != MOVED) {
		CHORD_SETUP(v, p);                      /* before the move: the stock table, as the stock OS plays it */
		return;
	}
	w = wanted();
	if (w != ct_want)
		relist(w);                              /* step 1: the new table's frames at once */
	if (ct_away)
		home_one();
	if (w == STOCK && !ct_away) {
		CHORD_SETUP(v, p);                      /* the stock table at home: the stock function */
		return;
	}
	sweep = *(const s16 *)(p + P_SWEEP);        /* the stock function's work (0x400a8080), on the list */
	i = sweep >> 10;
	xf = ((u32)sweep & 1023) << 21;
	f0 = sel(ct_list, i);
	f1 = sel(ct_list, i + 1);
	for (j = 0; j < 4; j++) {
		char *s = v + SUB_STRIDE * j;

		*(u32 *)(s + 188) = *(u32 *)(s + 184);
		*(u32 *)(s + 168) = f0;
		*(u32 *)(s + 172) = f1;
		*(u32 *)(s + 156) = xf;
		*(u32 *)(s + 184) = (u32)i;
	}
}

/* --- the loader --------------------------------------------------------------------------------------------------- */

static int lock(void)
{
	unsigned char was;

	__asm__ volatile ("tas %1\n\tsne %0" : "=d"(was), "+m"(busy) : : "cc");
	return !was;
}

static int drive_ok(void)
{
	return FS_MOUNTED && FS_LOCK_HOLDER != RUNNING_TASK;
}

/* n bytes at pos of the file at inode ino into buf; 1 if all of them came (One-Shot's read_at). */
static int read_at(u32 ino, u32 pos, void *buf, u32 n)
{
	u32 fh[4];

	fh[0] = ino;
	fh[1] = pos;
	fh[2] = 0;
	fh[3] = 1;
	return FS_READ(buf, n, fh) == (s32)n;
}

/* A voice's frame pointer (+168..+180 of a sub-voice) reaches into [lo, hi). */
static int pointed_into(u32 lo, u32 hi)
{
	const char *v = (const char *)VOICE0;
	u32 t, j, i;

	for (t = 0; t < 6; t++, v += VSTRIDE)
		for (j = 0; j < 4; j++)
			for (i = 0; i < 4; i++) {
				u32 a = *(const volatile u32 *)(v + SUB_STRIDE * j + SUB_FRAMES + 4 * i);

				if (a - lo < hi - lo)
					return 1;
			}
	return 0;
}

/* A retired buffer is free once it is not the table wanted and no voice points into it: no list can reach it any
   more (it is in no slot), and the slots holding its frames are no longer copies of a wanted frame. */
static void reclaim(void)
{
	s32 b;
	u32 i, lo;

	for (b = 0; b < BUFFERS; b++)
		if (ct_owner[b] == RETIRED && ct_want != BUF(b)) {
			lo = (u32)BUF(b);
			if (pointed_into(lo, lo + BUF_BYTES))
				continue;
			for (i = FIRST_SLOT; i < FRAMES; i++)
				if (ct_tag[i] == BUF(b))
					ct_tag[i] = 0;
			ct_owner[b] = FREE;
		}
}

/* The move (notes/66 §31), once, on the tick: the stock table's frames 2..31, in SRAM, copied into STOCK with the
   selector's 33 pointers (the sine at 0, frame 1 where the OS has it); each slot holds the stock frame, its tag STOCK.
   A table not as expected leaves the stock table for good. */
static void move(void)
{
	u32 *ptrs = STOCK;
	s32 *copy = (s32 *)(ptrs + POINTERS);
	u32 i, j;

	if (IN_SRAM(STOCK_TABLE[0]) || STOCK_TABLE[FRAMES - 1] != STOCK_TABLE[FRAMES - 2]) {
		ct_moved = REFUSED;
		return;
	}
	for (i = FIRST_SLOT; i < FRAMES; i++) {
		if (!IN_SRAM(slot(i)) || slot(i) == SINE) {
			ct_moved = REFUSED;
			return;
		}
		for (j = FIRST_SLOT; j < i; j++)
			if (slot(i) == slot(j)) {
				ct_moved = REFUSED;
				return;
			}
	}
	ptrs[0] = SINE;
	ptrs[1] = STOCK_TABLE[0];
	for (i = FIRST_SLOT; i < FRAMES; i++, copy += FRAME_LEN) {
		for (j = 0; j < FRAME_LEN; j++)
			copy[j] = ((const s32 *)slot(i))[j];
		ptrs[i] = (u32)copy;
		ct_tag[i] = STOCK;
	}
	ptrs[FRAMES] = ptrs[FRAMES - 1];
	__asm__ volatile ("" : : : "memory");          /* the copies, pointers and tags before the flag */
	ct_moved = MOVED;
}

static s32 free_buffer(void)
{
	s32 b;

	for (b = 0; b < BUFFERS; b++)
		if (ct_owner[b] == FREE)
			return b;
	return -1;
}

/* Slot n takes buffer b (-1: none) in one write; the buffer it held is retired. */
static void publish(u32 n, s32 b, u32 id)
{
	u32 *old = ct_slot[n];

	ct_slot[n] = b >= 0 ? BUF(b) : 0;
	ct_slot_id[n] = b >= 0 ? id : 0;
	if (b >= 0)
		ct_owner[b] = (u8)(1 + n);
	if (old)
		ct_owner[((u32)old - (u32)BUF(0)) / BUF_BYTES] = RETIRED;
}

/* The OS's sine as 16 bits, rounded (its peak 32 768 kept at 32 767). */
static s32 sine16(u32 m)
{
	s32 x = (((const s32 *)SINE)[m] >> 16) + ((((const s32 *)SINE)[m] >> 15) & 1);

	return x > 32767 ? 32767 : x;
}

/* The file's first frame is the OS's sine, each sample within SINE_STEPS (notes/66 §28.5). */
static int starts_with_sine(const s16 *src)
{
	u32 m;

	for (m = 0; m < CYCLE; m++) {
		s32 d = src[m] - sine16(m);

		if (d > SINE_STEPS || d < -SINE_STEPS)
			return 0;
	}
	return 1;
}

/* Sample m of source frame f: with the sine put in front, frame 0 is the OS's sine and frame f is the file's f - 1. */
static s32 sample(const s16 *src, u32 front, u32 f, u32 m)
{
	if (front)
		return f ? src[(f - 1) * CYCLE + m] : sine16(m);
	return src[f * CYCLE + m];
}

/* k frames of 256 samples at src (the OS's sine in front when the first is not one) spread over the 32 frames of the
   buffer by linear crossfades, as Q31 with the 257th sample equal to the first; then the 33 pointers, the sine at 0,
   the last repeating frame 31. */
static void build(u32 *buf, const s16 *src, u32 k)
{
	s32 *frames = (s32 *)(buf + POINTERS);
	u32 front = !starts_with_sine(src), n = k + front, s, j;

	for (s = 0; s < FRAMES; s++) {
		s32 *f = frames + s * FRAME_LEN;
		u32 pos = s * (n - 1), i0 = pos / (FRAMES - 1), rem = pos % (FRAMES - 1);

		for (j = 0; j < CYCLE; j++) {
			s32 a = sample(src, front, i0, j), b = rem ? sample(src, front, i0 + 1, j) : a;
			s32 x = a + (b - a) * (s32)rem / (FRAMES - 1);

			f[j] = (s32)((u32)x << 16);
		}
		f[CYCLE] = f[0];
		buf[s] = (u32)f;
	}
	buf[0] = SINE;
	buf[FRAMES] = buf[FRAMES - 1];
}

/* Slot n from /Wavetables/<n + 1, two digits>. 1 when the slot is done, 0 to try again at the next tick (no free
   buffer yet). */
static int load_one(u32 n)
{
	static const char dir[] = "/Wavetables/";
	char path[sizeof dir + 2];
	u8 head[HEADER];
	u32 fh[4], h[4], ino, bytes, i;
	s32 b;

	for (i = 0; i < sizeof dir - 1; i++)
		path[i] = dir[i];
	path[i] = (char)('0' + (n + 1) / 10);
	path[i + 1] = (char)('0' + (n + 1) % 10);
	path[i + 2] = 0;
	if (FS_OPEN(path, "r", fh) != 0) {
		if (ct_slot[n])
			publish(n, -1, 0);              /* gone: its patterns play the stock table */
		return 1;
	}
	ino = fh[0];
	FS_CLOSE(fh);
	if (FS_ENTRY(ino, h) != 0) {
		publish(n, -1, 0);
		return 1;
	}
	if (ct_slot[n] && ct_slot_id[n] == h[1])
		return 1;                               /* the same file: kept */
	if (!read_at(ino, 0, head, HEADER)) {
		publish(n, -1, 0);
		return 1;
	}
	bytes = (u32)head[4] << 24 | (u32)head[5] << 16 | (u32)head[6] << 8 | head[7];
	if (head[1] || !bytes || bytes % (CYCLE * 2) || bytes > STAGE_BYTES || h[2] < HEADER + bytes) {
		publish(n, -1, 0);                      /* stereo, or not k x 256 samples: no table */
		return 1;
	}
	b = free_buffer();
	if (b < 0)
		return 0;
	if (!read_at(ino, HEADER, STAGE, bytes)) {
		publish(n, -1, 0);
		return 1;
	}
	build(BUF(b), STAGE, bytes / (CYCLE * 2));
	publish(n, b, h[1]);
	return 1;
}

void ct_tick(void)
{
	u32 c, s, i;

	if (!lock())
		return;
	if (!ct_moved)
		move();
	reclaim();
	if (!FS_MOUNTED)
		seen = 0;                               /* scan again once it is mounted */
	else if (drive_ok()) {
		c = INDEX_COUNT;
		if (c > INDEX_MAX)
			c = INDEX_MAX;
		for (s = 0, i = 0; i < c; i++)
			s += INDEX[2 * i];
		if (!seen || c != sig_count || s != sig_sum) {
			sig_count = c;
			sig_sum = s;
			seen = 1;
			ct_scan = 1;                    /* the files may have changed: read them again */
		}
		if (ct_scan && load_one(ct_scan - 1))
			ct_scan = ct_scan < TABLES ? ct_scan + 1 : 0;
	}
	busy = 0;
}

/* 0x400075f0, in the screen's redraw: jsr 0x40076be4(view), which says whether the view needs drawing; the tick
   runs first. */
u32 ct_hook_tick(void *view)
{
	ct_tick();
	return TICK_STOCK(view);
}
