/* The RESAMPLE page's recorder in model27's builder, with entries.S (notes/79; step R1: the capture in RAM). Addresses
 * are VAs of OS 1.13.
 *
 * Where the audio is taken (notes/79 §3.1): entries.S's rs_mix takes the audio function's call of the mixer
 * (0x40059872, jsr 0x400567ba). Before the mixer, rs_pre gets the six tracks' buffers (0x80001858 + 128 t, 32 int32 a
 * track, mono: after Volume + Dist and the Track FX, before level, pan and the sends) and the tracks triggered in the
 * block (the audio function's frame + 16); after it, rs_post gets the main bus (0x8000b990, 32 frames of {L, R} int32,
 * scaled x4 at 0x40056b42, without USB) and the USB input (0x8000b990 + 256, copied there at 0x40056b48 from
 * 0x40fe4cf0). Both hand the source the page chose to rs_block. Idle, rs_mix goes straight to the mixer.
 *
 * The take (notes/79 §3.2, §3.3): armed, a block starts it when its source is triggered (TRIG: the track's bit; MAIN:
 * any track's), passes the threshold (LEVEL: the eight blocks before it come along from a ring, 256 frames, so that the
 * attack is whole) or at once (NOW). Recording, each block goes into the buffer, 32 bits as the mixer has them, a word
 * a frame or two (L, R) for a stereo take of MAIN or USB, a mono one of them as (L + R) / 2. It ends on the page's
 * RECORD (req), at its longest (limit: LENGTH, at most what the buffer holds) or, with STOP SILENT, once 50 ms are in
 * and 250 ms stay below -72 dB, the tail cut after the last block over -90 dB. The state then says TAKEN, and the page
 * (later steps) names and saves it; nothing here touches the drive.
 *
 * The levels are magnitudes in each source's own scale: full scale is 2^31 >> shift, the shift per kind of source
 * (track, main, USB) written by the composer from part.json: a track 3, SAMPLE's full scale in the track's buffer
 * (its interpolator's rows sum to 32768: a full-scale sample comes out at 2^30 at 96 kHz; the OS's 2:1 decimator
 * 0x400a9f58 doubles it, the VCA keeps it, PUNCH 0x400a967a takes a quarter with PUNCH off, and the voice loop halves
 * every track, 0x400a7e2c: 2^28), main and USB 0 (the output's and the USB input's full scale); the save maps that full
 * scale to 16-bit full scale (notes/79 §3.3, §12).
 *
 * The UI task arms (rs_arm), asks the end (rs_stop), drops (rs_cancel) and, once the take is saved, lets it go
 * (rs_release); the audio interrupt only reads what the UI writes before it sets the state, and the UI only reads what
 * the audio side leaves when the state says TAKEN. For the save: rs_header and rs_pcm16 write the file in the format
 * SAMPLE plays (a 64-byte header, big-endian 16-bit frames; Cycles One-Shot's uploader writes the same), as heard or,
 * with NORM, the take's peak at -0.3 dB (rs_norm).
 *
 * A part keeps its state in its data block (the composer writes it after the code): no variables of its own. The audio
 * side runs in the audio interrupt, none of it EMAC: idle 7 instructions a block (entries.S); armed or recording about
 * 900 for a track and 1 600 for a stereo take of main or USB, and once, in the block a LEVEL take starts in, about 7
 * 800 for the ring's copy (counted with cfemu, 2026-11-03; the proof's count decides). RS_HOST builds the same code on
 * the host for tools/emu/resample_host.py.
 *
 * License: MIT (LICENSE next to this file). */
#include "resample.h"

#define BLOCK 32u                                   /* frames a block */
#define RING 9u                                     /* LEVEL's ring, in blocks: this one and the eight before it */
#define RATE 48000u
#define MIN_FRAMES 2400u                            /* 50 ms before SILENT may end a take */
#define QUIET_FRAMES 12000u                         /* 250 ms below the silence level end it */
#define SIL_DB 72                                   /* the silence level, -72 dB */
#define CUT_DB 90                                   /* the tail is cut after the last block over -90 dB */
#define NORM_PEAK 31655u                            /* -0.3 dB of 16-bit full scale */

#ifdef RS_HOST
uint8_t *rs_host_mem;
uint32_t rs_data[128];
#endif

/* 2^31 * 10^(-3k / 20): the magnitude of -3k dB of full scale, k = 0..32. */
static const uint32_t db_mag[33] = {
	2147483648u, 1520301996u, 1076291389u, 761955951u, 539423504u, 381882595u, 270352174u, 191394682u,
	135497058u, 95924571u, 67909396u, 48076170u, 34035322u, 24095163u, 17058069u, 12076188u, 8549286u,
	6052431u, 4284793u, 3033401u, 2147484u, 1520302u, 1076291u, 761956u, 539424u, 381883u, 270352u,
	191395u, 135497u, 95925u, 67909u, 48076u, 34035u,
};

/* -db dB (db >= 0, in steps of 3, past 96 as 96) in a source of full scale 2^31 >> sh. */
static uint32_t level_of(uint32_t db, uint32_t sh)
{
	uint32_t k = db / 3u;
	return db_mag[k > 32u ? 32u : k] >> sh;
}

/* A magnitude mag in a source of full scale 2^31 >> sh as dB below full scale, in steps of 3 (0..96): for the page's
 * meter. */
uint32_t rs_db(uint32_t mag, uint32_t sh)
{
	uint32_t k = 0;
	while (k < 32u && mag < db_mag[k] >> sh)
		k++;
	return 3u * k;
}

static uint32_t mag(int32_t x)
{
	uint32_t s = (uint32_t)(x >> 31);
	return ((uint32_t)x ^ s) - s;
}

/* n frames of a block x into w: a track (one word a frame), or main / USB ({L, R} a frame) kept as two words or
 * summed to one. Returns their largest magnitude. */
static uint32_t take(int32_t *w, const int32_t *x, uint32_t n, uint32_t in_stereo, uint32_t out_stereo)
{
	uint32_t i, p = 0, m;
	int32_t v;
	if (!in_stereo || out_stereo) {
		n <<= in_stereo;
		for (i = 0; i < n; i++) {
			v = x[i];
			w[i] = v;
			m = mag(v);
			if (m > p)
				p = m;
		}
		return p;
	}
	for (i = 0; i < n; i++) {
		v = (x[2 * i] >> 1) + (x[2 * i + 1] >> 1);
		w[i] = v;
		m = mag(v);
		if (m > p)
			p = m;
	}
	return p;
}

/* n frames more in the take, p their largest magnitude. */
static void count(struct data *d, uint32_t n, uint32_t p)
{
	d->frames += n;
	if (p > d->peak)
		d->peak = p;
	if (p >= d->cut)
		d->loud = d->frames;
	if (p >= d->sil)
		d->quiet = 0;
	else if (d->frames > MIN_FRAMES)
		d->quiet += n;
}

static uint32_t room(const struct data *d)
{
	uint32_t left = d->limit - d->frames;
	return left < BLOCK ? left : BLOCK;
}

/* A block of the chosen source: x its samples, in_stereo whether it has {L, R} frames, hit whether it was triggered. */
static void rs_block(const int32_t *x, uint32_t in_stereo, uint32_t hit)
{
	struct data *d = D;
	uint32_t ch = d->stereo ? 2u : 1u, p, n, b, k;
	int32_t *buf = WORDS(d->buf), *ring = WORDS(d->ring), *w;

	if (d->state == ARMED) {
		w = ring + 2u * BLOCK * d->ring_at;
		p = take(w, x, BLOCK, in_stereo, ch == 2u);
		d->level = p;
		if (!(d->start == START_NOW || (d->start == START_TRIG && hit) || (d->start == START_LEVEL && p >= d->thr))) {
			d->ring_at = (uint8_t)((d->ring_at + 1u) % RING);
			if (d->ring_n < RING - 1u)
				d->ring_n++;
			return;
		}
		d->frames = d->peak = d->quiet = d->loud = 0;
		d->req = 0;
		d->end = END_NONE;
		k = d->start == START_LEVEL ? d->ring_n : 0u;      /* the blocks before this one, oldest first */
		b = (d->ring_at + RING - k) % RING;
		while (k-- && (n = room(d)) != 0) {
			w = ring + 2u * BLOCK * b;
			count(d, n, take(buf + ch * d->frames, w, n, ch - 1u, ch == 2u));
			b = (b + 1u) % RING;
		}
		n = room(d);
		count(d, n, take(buf + ch * d->frames, ring + 2u * BLOCK * d->ring_at, n, ch - 1u, ch == 2u));
		d->state = REC;
	} else if (d->state == REC) {
		n = room(d);
		p = take(buf + ch * d->frames, x, n, in_stereo, ch == 2u);
		d->level = p;
		count(d, n, p);
	} else {
		return;
	}
	if (d->req)
		d->end = END_RECORD;
	else if (d->frames >= d->limit)
		d->end = d->stop == STOP_LENGTH ? END_LENGTH : END_FULL;
	else if (d->stop == STOP_SILENT && d->quiet >= QUIET_FRAMES) {
		d->frames = d->loud;
		d->end = END_SILENT;
	} else
		return;
	d->req = 0;
	d->state = TAKEN;
}

/* entries.S's rs_mix, before the mixer: the six tracks' buffers and the tracks triggered in the block. */
void rs_pre(const int32_t *tracks, uint32_t triggered)
{
	struct data *d = D;
	if ((d->state == ARMED || d->state == REC) && d->src < SRC_MAIN)
		rs_block(tracks + BLOCK * d->src, 0, triggered >> d->src & 1u);
}

/* After the mixer: the main bus and the USB input, {L, R} frames. */
void rs_post(const int32_t *bus, const int32_t *usb, uint32_t triggered)
{
	struct data *d = D;
	if (d->state != ARMED && d->state != REC)
		return;
	if (d->src == SRC_MAIN)
		rs_block(bus, 1, (triggered & 0x3fu) != 0);
	else if (d->src == SRC_USB)
		rs_block(usb, 1, 0);
}

/* --- the UI task ---------------------------------------------------------------------------------------------------
 * The page arms: src 0..5 a track, 6 main, 7 USB; stereo for main and USB; start START_*, stop STOP_*; thr_db LEVEL's
 * threshold as dB below full scale (12..60, in steps of 3); seconds the longest take. A track is mono, USB has no
 * trigger (TRIG becomes LEVEL). Only while the state is IDLE or TAKEN; the state is written last. */
void rs_arm(uint32_t src, uint32_t stereo, uint32_t start, uint32_t stop, uint32_t thr_db, uint32_t seconds)
{
	struct data *d = D;
	uint32_t sh, most;
	if (d->state == ARMED || d->state == REC || src > SRC_USB)
		return;
	sh = d->shift[src < SRC_MAIN ? 0 : src - (SRC_MAIN - 1u)];
	d->src = (uint8_t)src;
	d->stereo = (uint8_t)(src >= SRC_MAIN && stereo);
	d->start = (uint8_t)(src == SRC_USB && start == START_TRIG ? START_LEVEL : start);
	d->stop = (uint8_t)stop;
	d->thr = level_of(thr_db, sh);
	d->sil = level_of(SIL_DB, sh);
	d->cut = level_of(CUT_DB, sh);
	most = d->cap / (d->stereo ? 2u : 1u);
	d->limit = seconds > most / RATE ? most : seconds * RATE;
	d->frames = d->peak = d->quiet = d->loud = d->level = 0;
	d->req = 0;
	d->end = END_NONE;
	d->ring_n = d->ring_at = 0;
	d->state = ARMED;
}

/* RECORD while armed (back to idle) or recording (the take ends with the next block). */
void rs_stop(void)
{
	struct data *d = D;
	if (d->state == ARMED)
		d->state = IDLE;
	else if (d->state == REC)
		d->req = 1;
}

/* The page drops the take, armed, recording or taken. */
void rs_cancel(void)
{
	D->state = IDLE;
}

/* The take is saved (or dropped after the save failed): the recorder may arm again. */
void rs_release(void)
{
	struct data *d = D;
	if (d->state == TAKEN)
		d->state = IDLE;
}

/* --- the save -------------------------------------------------------------------------------------------------------
 * The 64-byte header of a sample file of frames frames: +1 stereo (interleaved), +4 its audio bytes, +8 the rate,
 * +16 the last frame, +20 0x7f (no loop); big-endian, the rest zero. The file then holds the frames as big-endian
 * 16-bit words and 16 zero bytes (notes/79 §4). */
static void be32(uint8_t *p, uint32_t v)
{
	p[0] = (uint8_t)(v >> 24);
	p[1] = (uint8_t)(v >> 16);
	p[2] = (uint8_t)(v >> 8);
	p[3] = (uint8_t)v;
}

void rs_header(uint8_t *h, uint32_t frames, uint32_t stereo)
{
	uint32_t i;
	for (i = 0; i < 64u; i++)
		h[i] = 0;
	h[1] = stereo ? 1u : 0u;
	be32(h + 4, frames * (stereo ? 4u : 2u));
	be32(h + 8, RATE);
	be32(h + 16, frames ? frames - 1u : 0u);
	h[20] = 0x7f;
}

/* NORM: the shift and gain (Q15) that put a take of largest magnitude peak at -0.3 dB of 16-bit full scale. The
 * shift keeps peak >> s under 2^16, so that the gain keeps 15 bits; |x >> s| * g stays under NORM_PEAK << 15 < 2^30.
 * A silent take: s 31, g 0 (silence). */
void rs_norm(uint32_t peak, uint32_t *s, uint32_t *g)
{
	uint32_t k = 0;
	if (!peak) {
		*s = 31;
		*g = 0;
		return;
	}
	while ((peak >> k) >= 65536u)
		k++;
	*s = k;
	*g = (NORM_PEAK << 15) / (peak >> k);
}

/* words samples of the take into big-endian 16-bit: as heard (g 0: x >> s, s = 16 - the source's shift), or with
 * NORM's shift and gain; saturated. Returns how many saturated. */
uint32_t rs_pcm16(uint8_t *out, const int32_t *x, uint32_t words, uint32_t s, uint32_t g)
{
	uint32_t i, clipped = 0;
	int32_t v;
	for (i = 0; i < words; i++) {
		v = x[i] >> s;
		if (g)
			v = (v * (int32_t)g) >> 15;
		if (v > 32767) {
			v = 32767;
			clipped++;
		} else if (v < -32768) {
			v = -32768;
			clipped++;
		}
		out[2 * i] = (uint8_t)((uint32_t)v >> 8);
		out[2 * i + 1] = (uint8_t)v;
	}
	return clipped;
}
