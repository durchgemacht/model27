/* CHORD Tables: the stock CHORD machine of the Model:Cycles OS 1.13 plays wavetables from the +Drive (notes/66).

   An extension of CHORD (machine 5), not an added machine: the builder's shortcut layer gives CHORD's tracks
   RETRIG + SWEEP = Wavetable, 0 to 64, kept in k 30 and saved with the sound; 0 is the stock table. SWEEP still
   moves through the table's frames.

   - cw_setup takes the place of jsr 0x400a8080 at 0x400ab15e, the one call through which CHORD's update gets its
     two frames (notes/66 §1.1). In the block a note starts (v + 0x38 set: the block after the trig, or the machine
     change, notes/66 §11.6) it latches the track's table from k 30 of the sound the note plays (CUR_SNDS[t] + 80),
     or of the targets when CUR_SNDS[t] is 0 (a preview note). Without a table it calls the stock function;
     with one it does that function's work on the table's frames: frames SWEEP >> 10 and the next, the crossfade
     (SWEEP & 1023) << 21, the index, in the four sub-voices.
   - ct_hook_tick takes the place of jsr 0x40076be4 at 0x400075f0, in the screen's redraw (UI task, about 30 times
     a second; with SAMPLE, through the builder's tick dispatcher). The loader reads the files /Wavetables/01 to
     /Wavetables/64 one per tick, once the drive is mounted and again whenever the drive's file index changes. A file
     is a sample file (64-byte header, big-endian 16-bit), mono, of k x 256 samples, k = 1 to 32: k single-cycle
     frames, spread over the 32 frames SWEEP reaches by linear crossfades, each frame 257 Q31 samples with the last
     equal to the first. A file kept under the same id is not read again; another file, a missing one or one that
     is not k x 256 mono samples empties its slot, and its tracks play the stock table from their next note.
   - Memory: the RAM claim 0x43400000..0x43700000 holds one file as read, then 72 buffers of a table each (64
     slots and 8 spare), then the stock frames' copy. A table is published by one 32-bit write of its slot; the
     buffer it replaces is reused only once no track's latch and no voice's frame pointer reaches into it (the audio
     interrupt runs to its end before the UI task looks).
   - The frames CHORD plays are read in SRAM (0.2, notes/66 §19): a table's frames in SDRAM cost 110 to 121 lines
     of the 8 KB data cache a block for each track (§18.1). The stock table's 30 frames in SRAM, read by CHORD
     alone, become a pool of slots, once the tick has copied them into the RAM claim (the move). From then on
     cw_setup maps each frame a track plays, at Wavetable 0 by the stock selector's rule, to the address the render
     reads: a slot holding a copy of it, or a slot no voice points at, copied in. The render also reads the
     previous block's two frames when the frame changes (+176, +180): a slot any voice points at is never written,
     and a frame keeps its pointer while a voice points at it, so the render decides as it would on the frames' own
     addresses and the sound is the stock OS's at Wavetable 0 and 0.1's with a table, sample for sample. Which
     slots a voice may point at is kept per voice (pin), from its own 16 pointers when it remaps (notes/66 §22).

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
#define V_STARTS        0x38                        /* set in the block a note starts */
#define SUB_STRIDE      120                         /* CHORD's four sub-voices */
#define CHORD_SETUP     ((void (*)(char *, const char *))0x400a8080)
#define CUR_SND(t)      (((const char *volatile *)0x800017ec)[t])   /* the sound a track's note plays, or 0 */
#define TARGETS(t)      ((const char *)0x800015ae + 66 * (t))       /* its 66 bytes, k 0..32 */
#define SOUND_K30       80                          /* a sound: +20 + 2 * 30 */
#define TARGETS_K30     60
#define P_SWEEP         0x1a
#define CHORD_MACHINE   5                           /* a voice's machine, at +0 */
#define SUB_FRAMES      168                         /* a sub-voice's +168 f0, +172 f1, +176 and +180 the previous */
#define STOCK_TABLE     ((const u32 *)0x40118590)   /* the selector's: frame n (1..32) at entry n - 1 */
#define SINE            0x8000eee4u                 /* the selector's answer outside 1..32 */
#define SRAM_LO         0x80000000u                 /* the internal SRAM, 64 KB, not cached */
#define SRAM_HI         0x80010000u
#define IN_SRAM(a)      ((u32)(a) - SRAM_LO < SRAM_HI - SRAM_LO)

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
#define TABLES          64                          /* RETRIG + SWEEP 1..64: /Wavetables/01 .. 64 */
#define FRAMES          32                          /* SWEEP >> 10 reaches 0..31; pointer 32 repeats 31 */
#define FRAME_LEN       257
#define POINTERS        (FRAMES + 1)
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
#define RETIRED         0xff                        /* replaced, until no latch and no voice points into it */
#define STOCK           BUF(BUFFERS)                /* the stock frames' copy: 33 pointers, then the frames */
#define POOL_MAX        32
#define KB_SHIFT        10                          /* frames are 1 028 bytes apart: one starts in a KB at most */
#define KBS             ((SRAM_HI - SRAM_LO) >> KB_SHIFT)
#define MOVED           1                           /* ct_moved: the pool is in use */
#define READY           2                           /* the tick has copied the frames; the audio adopts them */
#define REFUSED         0xff                        /* the stock table is not as expected: 0.1's way for good */

/* The state, roots of the object so that a proof finds them in the composed tweak's symbols. */
u32 *volatile ct_slot[TABLES];                      /* table n + 1: its pointer list, or 0 */
u32 ct_slot_id[TABLES];                             /* the id of the file it came from */
const u32 *volatile ct_latch[6];                    /* each track's table, latched at its note's start; 0: stock */
u8 ct_owner[BUFFERS];                               /* FREE, 1 + the slot it holds, or RETIRED */
u32 ct_scan;                                        /* 1..64: the file the tick reads next; 0: none */
volatile u32 ct_moved;                              /* 0, READY, MOVED or REFUSED */
u32 ct_pool_addr[POOL_MAX];                         /* slot k: its address in SRAM, a stock frame's */
u32 volatile ct_pool_tag[POOL_MAX];                 /* the frame slot k holds a copy of; 0: none */
u32 ct_pool_n;                                      /* slots, 30 on the OS 1.13 */
u32 ct_fallback;                                    /* frames read where they are for want of a free slot */
static u8 kb_slot[KBS];                             /* 1 + the slot whose frame starts in that KB of SRAM, or 0 */
static u32 cursor;                                  /* the slot taken last */
static u32 last_src[6][2], last_ptr[6][2];          /* a track's two sources and pointers in its last block */
static u32 pin[6];                                  /* the slots a voice may point at until its next remap */
static u32 far[6];                                  /* 1: it may point at a frame outside SRAM */
static u32 sig_count, sig_sum;                      /* the file index when the scan started */
static u8 seen;                                     /* a scan has started since the drive was mounted */
static volatile unsigned char busy;

/* --- the audio side ------------------------------------------------------------------------------------------------ */

static const u32 *table_of(s32 t)
{
	const char *snd = CUR_SND(t);
	s32 w = snd ? *(const volatile s16 *)(snd + SOUND_K30) : *(const s16 *)(TARGETS(t) + TARGETS_K30);
	s32 n = w >> 8;                                 /* 8.8 */

	return n >= 1 && n <= TABLES ? ct_slot[n - 1] : 0;
}

/* 1 + the slot whose frame starts at a, or 0 for an address that is no slot's. */
static u32 slot_of(u32 a)
{
	u32 k;

	if (!IN_SRAM(a))
		return 0;
	k = kb_slot[(a - SRAM_LO) >> KB_SHIFT];
	return k && ct_pool_addr[k - 1] == a ? k : 0;
}

static u32 slot_bit(u32 a)
{
	u32 k = slot_of(a);

	return k ? 1u << (k - 1) : 0;
}

/* Voice t's 16 frame pointers (+168..+180 of its four sub-voices): the slots among them as bits; *out gets 1 when
   one of them is outside SRAM (a frame read where it is). Sub-voices 2 to 4 hold sub-voice 1's pointers unless one
   was switched off for its pitch (notes/66 §19.1): only theirs that differ are looked up. */
static u32 own(u32 t, u32 *out)
{
	const u32 *q = (const u32 *)(VOICE0 + VSTRIDE * t + SUB_FRAMES);
	u32 bits = 0, far = 0, j, i, a;

	for (i = 0; i < 4; i++) {
		bits |= slot_bit(q[i]);
		far |= !IN_SRAM(q[i]);
	}
	for (j = 1; j < 4; j++)
		for (i = 0; i < 4; i++)
			if ((a = q[SUB_STRIDE / 4 * j + i]) != q[i]) {
				bits |= slot_bit(a);
				far |= !IN_SRAM(a);
			}
	*out = far;
	return bits;
}

/* Voice t plays CHORD (its machine at +0). Another machine's voice is never read by CHORD's render, and it comes back
   to CHORD through the reset, its pointers the sine: its pin and far do not count. */
static int chord_voice(u32 t)
{
	return *(const volatile u32 *)(VOICE0 + VSTRIDE * t) == CHORD_MACHINE;
}

/* The adoption, in the audio's first setup after the move: each voice's slots and whether it reads a frame outside
   SRAM, from its pointers. From then on a voice's pointers change only in its own setup (which recomputes them), its
   render (+168 -> +176, +172 -> +180) and the reset (the sine): pin[t] and far[t] hold until its next remap. */
static void __attribute__((noinline)) adopt(void)
{
	u32 t;

	for (t = 0; t < 6; t++)
		pin[t] = chord_voice(t) ? own(t, &far[t]) : (far[t] = 0);
	ct_moved = MOVED;
}

/* Rule 2: the slot holding a copy of s, or 0; first where track t had its two sources, then among all slots. */
static u32 held(u32 t, u32 s)
{
	u32 k, j;

	for (j = 0; j < 2; j++)
		if (s == last_src[t][j]) {
			k = slot_of(last_ptr[t][j]);
			if (k && ct_pool_tag[k - 1] == s)
				return last_ptr[t][j];
		}
	for (k = 0; k < ct_pool_n; k++)
		if (ct_pool_tag[k] == s)
			return ct_pool_addr[k];
	return 0;
}

/* Rule 3: a voice points at s outside SRAM. Only the voices that may (far) are looked at, a frame read where it is
   being rare: from before the move, or for want of a free slot. */
static int pointed(u32 s)
{
	const u32 *q;
	u32 t, j, i;

	for (t = 0; t < 6; t++)
		if (far[t] && chord_voice(t))
			for (j = 0, q = (const u32 *)(VOICE0 + VSTRIDE * t + SUB_FRAMES); j < 4; j++, q += SUB_STRIDE / 4)
				for (i = 0; i < 4; i++)
					if (q[i] == s)
						return 1;
	return 0;
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

/* Rules 3 to 5 for a source no slot holds: read where it is while a voice points at it; else copied into a slot
   outside busy (the next one after the last taken); else, no such slot, read where it is. */
static u32 place(u32 s, u32 busy)
{
	u32 free, k;

	if (pointed(s))
		return s;
	free = ~busy & (ct_pool_n == 32 ? ~0u : (1u << ct_pool_n) - 1);
	if (!free) {
		ct_fallback++;
		return s;
	}
	k = free & ~((2u << cursor) - 1) ? free & ~((2u << cursor) - 1) : free;
	k = 31 - __builtin_clz(k & -k);                 /* its lowest bit */
	cursor = k;
	ct_pool_tag[k] = 0;
	copy_frame((s32 *)ct_pool_addr[k], (const s32 *)s);
	ct_pool_tag[k] = s;
	return ct_pool_addr[k];
}

/* Track t's sources s0 and s1 mapped to the pointers the render reads, into last_ptr[t]: off the path of the
   blocks whose frames stay, and out of line so that the audio's code for those stays short. The slots no voice may
   point at are those outside every other voice's pin and outside this voice's own pointers and new ones. */
static void __attribute__((noinline)) remap(u32 t, u32 s0, u32 s1)
{
	u32 a, b, u, mine, outside, busy;

	mine = own(t, &outside);
	far[t] = outside;
	a = IN_SRAM(s0) ? s0 : held(t, s0);             /* rule 1, the sine; rule 2 */
	b = s1 == s0 ? a : IN_SRAM(s1) ? s1 : held(t, s1);
	if (!a || !b) {
		busy = mine | slot_bit(a) | slot_bit(b);
		for (u = 0; u < 6; u++)
			if (u != t && chord_voice(u))
				busy |= pin[u];
		if (!a) {
			a = place(s0, busy);
			busy |= slot_bit(a);
		}
		if (!b)
			b = s1 == s0 ? a : place(s1, busy);
	}
	pin[t] = mine | slot_bit(a) | slot_bit(b);
	far[t] = outside | !IN_SRAM(a) | !IN_SRAM(b);
	last_src[t][0] = s0;
	last_src[t][1] = s1;
	last_ptr[t][0] = a;
	last_ptr[t][1] = b;
}

/* The two pointers the render reads for sources s0 and s1 on track t. */
static void map(u32 t, u32 s0, u32 s1, u32 *p0, u32 *p1)
{
	const u32 *sub = (const u32 *)(VOICE0 + VSTRIDE * t + SUB_FRAMES);

	if (s0 != last_src[t][0] || s1 != last_src[t][1] || sub[0] != last_ptr[t][0] || sub[1] != last_ptr[t][1])
		remap(t, s0, s1);                       /* else the same frames: the voice still points at their slots */
	*p0 = last_ptr[t][0];
	*p1 = last_ptr[t][1];
}

/* The stock selector 0x400a8060 on the stock frames' copy: n = 0..32 its pointer, the sine outside. */
static u32 stock_sel(s32 n)
{
	return (u32)n <= FRAMES ? STOCK[n] : SINE;
}

void cw_setup(char *v, const char *p)
{
	u32 t = ((u32)v - VOICE0) / VSTRIDE;
	const u32 *ptrs;
	s32 sweep, i, j;
	u32 xf, f0, f1;

	if (t > 5) {
		CHORD_SETUP(v, p);
		return;
	}
	if (*(const volatile u32 *)(v + V_STARTS))
		ct_latch[t] = table_of(t);
	ptrs = ct_latch[t];
	sweep = *(const s16 *)(p + P_SWEEP);
	if (ct_moved == READY)
		adopt();
	if (!ptrs && ct_moved != MOVED) {
		CHORD_SETUP(v, p);                      /* the stock table, as the stock OS plays it */
		return;
	}
	if (!ptrs) {                                    /* the stock function's work, on the copy (0x400a8080) */
		i = sweep >> 10;
		xf = ((u32)sweep & 1023) << 21;
		f0 = stock_sel(i);
		f1 = stock_sel(i + 1);
	} else {
		if (sweep < 0) {                        /* the stock function would take the sine: the first frame */
			i = 0;
			xf = 0;
		} else {
			i = sweep >> 10;                /* 0..31 */
			xf = ((u32)sweep & 1023) << 21;
		}
		f0 = ptrs[i];
		f1 = ptrs[i + 1];
	}
	if (ct_moved == MOVED)
		map(t, f0, f1, &f0, &f1);
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

static int latched(const u32 *ptrs)
{
	s32 t;

	for (t = 0; t < 6; t++)
		if (ct_latch[t] == ptrs)
			return 1;
	return 0;
}

/* A voice's frame pointer (+168..+180 of a sub-voice) reaches into [lo, hi). Once none does and no latch holds the
   buffer, none will: a voice gets a buffer's frames only from its latch, or from another voice that points at them. */
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

static void reclaim(void)
{
	s32 b;
	u32 k, lo;

	for (b = 0; b < BUFFERS; b++)
		if (ct_owner[b] == RETIRED && !latched(BUF(b))) {
			lo = (u32)BUF(b);
			if (pointed_into(lo, lo + BUF_BYTES))
				continue;
			for (k = 0; k < ct_pool_n; k++)  /* the slots holding its frames: no longer copies of them */
				if (ct_pool_tag[k] - lo < BUF_BYTES)
					ct_pool_tag[k] = 0;
			ct_owner[b] = FREE;
		}
}

/* The move (notes/66 §19.3), once, on the tick: the stock table's frames in SRAM copied into STOCK, which gets the
   selector's 33 pointers (the sine at 0, frames in SDRAM kept where they are); each of them becomes a slot of the
   pool, tagged with its copy, so a track playing it keeps its pointer. Then READY: the audio's next setup adopts it
   (adopt), so that the voices' pointers are read where they cannot change under the reading. A table not as
   expected (a frame overlapping another's KB, more than POOL_MAX) leaves 0.1's way for good. */
static void move(void)
{
	u32 *ptrs = STOCK;
	s32 *copy = (s32 *)(ptrs + POINTERS);
	u32 n, k, j, src;

	for (k = 0; k < KBS; k++)
		kb_slot[k] = 0;
	ct_pool_n = 0;
	ptrs[0] = SINE;
	for (n = 1; n <= FRAMES; n++) {
		src = STOCK_TABLE[n - 1];
		if (IN_SRAM(src) && src != SINE) {
			for (k = 0; k < ct_pool_n && ct_pool_addr[k] != src; k++)
				;
			if (k == ct_pool_n) {
				u32 kb = (src - SRAM_LO) >> KB_SHIFT;

				if (k == POOL_MAX || kb_slot[kb] || src - SRAM_LO > SRAM_HI - SRAM_LO - 4 * FRAME_LEN) {
					ct_pool_n = 0;
					ct_moved = REFUSED;
					return;
				}
				for (j = 0; j < FRAME_LEN; j++)
					copy[j] = ((const s32 *)src)[j];
				ct_pool_addr[k] = src;
				ct_pool_tag[k] = (u32)copy;
				kb_slot[kb] = (u8)(k + 1);
				ct_pool_n = k + 1;
				copy += FRAME_LEN;
			}
			src = ct_pool_tag[k];
		}
		ptrs[n] = src;
	}
	__asm__ volatile ("" : : : "memory");          /* the copies, pointers and slots before the flag */
	ct_moved = READY;
}

static s32 free_buffer(void)
{
	s32 b;

	for (b = 0; b < BUFFERS; b++)
		if (ct_owner[b] == FREE)
			return b;
	return -1;
}

/* Slot n takes buffer b (-1: none) in one write; the buffer it held waits for the latches. */
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

/* k frames of 256 samples at src spread over the 32 frames of the buffer by linear crossfades, as Q31 with the
   257th sample equal to the first; then the 33 pointers, the last repeating frame 31. */
static void build(u32 *buf, const s16 *src, u32 k)
{
	s32 *frames = (s32 *)(buf + POINTERS);
	u32 s, j;

	for (s = 0; s < FRAMES; s++) {
		s32 *f = frames + s * FRAME_LEN;
		u32 pos = s * (k - 1), i0 = pos / (FRAMES - 1), rem = pos % (FRAMES - 1);
		const s16 *a = src + i0 * CYCLE, *b = rem ? a + CYCLE : a;

		for (j = 0; j < CYCLE; j++) {
			s32 x = a[j] + ((s32)b[j] - a[j]) * (s32)rem / (FRAMES - 1);

			f[j] = (s32)((u32)x << 16);
		}
		f[CYCLE] = f[0];
		buf[s] = (u32)f;
	}
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
			publish(n, -1, 0);              /* gone: its tracks play the stock table */
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
