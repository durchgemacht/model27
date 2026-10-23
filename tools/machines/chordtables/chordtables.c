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
     slots and 8 spare). A table is published by one 32-bit write of its slot; the buffer it replaces is reused only
     once no track's latch points at it (the audio interrupt runs to its end before the UI task looks).

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
#define RETIRED         0xff                        /* replaced, until no latch points at it */

/* The state, roots of the object so that a proof finds them in the composed tweak's symbols. */
u32 *volatile ct_slot[TABLES];                      /* table n + 1: its pointer list, or 0 */
u32 ct_slot_id[TABLES];                             /* the id of the file it came from */
const u32 *volatile ct_latch[6];                    /* each track's table, latched at its note's start; 0: stock */
u8 ct_owner[BUFFERS];                               /* FREE, 1 + the slot it holds, or RETIRED */
u32 ct_scan;                                        /* 1..64: the file the tick reads next; 0: none */
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
	if (!ptrs) {
		CHORD_SETUP(v, p);                      /* the stock table, as the stock OS plays it */
		return;
	}
	sweep = *(const s16 *)(p + P_SWEEP);
	if (sweep < 0) {                                /* the stock function would take the sine: the first frame */
		i = 0;
		xf = 0;
	} else {
		i = sweep >> 10;                        /* 0..31 */
		xf = ((u32)sweep & 1023) << 21;
	}
	f0 = ptrs[i];
	f1 = ptrs[i + 1];
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

static void reclaim(void)
{
	s32 b;

	for (b = 0; b < BUFFERS; b++)
		if (ct_owner[b] == RETIRED && !latched(BUF(b)))
			ct_owner[b] = FREE;
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
