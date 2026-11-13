/* Sample memory of SAMPLE, see pool.h. */
#include "pool.h"
#include "smp_filter.h"
#include "view.h"
#include "os.h"

#define SOUND_SIZE  100
#define MACHINE_AT  38                  /* sound: machine index (high byte of k 9) */
#define KEY_AT      70                  /* sound: k 25..27 = inode, id high, id low */
#define REC_KEY_AT  76                  /* sound record: slots 24..26 (free in the OS) */
#define REC_FILTER_AT 82                /* sound record: slot 27 (free): 1 once SWEEP means the filter */
#define SWEEP_AT    32                  /* sound: k 6, SAMPLE's cutoff; 0 in sounds from before 0.5 */
#define REC_VERSION 4                   /* sound record: format version (the load takes 2 only) */
#define HEADER      64                  /* sample file: header, then big-endian PCM */
#define READ_BUDGET (128 * 1024)        /* bytes read per tick */
#define RATE_MIN    4000
#define RATE_MAX    192000

#ifndef POOL_BEGIN
/* The sample pool: RAM the Cycles OS leaves unused (the Model:Samples keeps its pool there), above
   the window where the added machines' payload runs (0x43000000, Modded-Cycles' PAY_ALONE). The
   build sets POOL_BASE and POOL_LIMIT; the host tests replace POOL_BEGIN and POOL_END. */
#ifndef POOL_BASE
#define POOL_BASE   0x43800000u
#define POOL_LIMIT  0x46700000u
#endif
#define POOL_BEGIN  ((char *)POOL_BASE)
#define POOL_END    ((char *)POOL_LIMIT)
#endif

/* Keeps the compiler from moving memory accesses across it: what the audio side may read is
   complete before a slot becomes READY, and a slot is RETIRING before the voices are looked at. */
#define BARRIER()   __asm__ volatile ("" : : : "memory")

smp_slot smp_slots[SLOTS];
/* The waveform for the screen: per slot, the lowest and highest frame of each of SMP_COLUMNS equal
   stretches of the sample, gathered as the file is read. */
static int16_t ov_lo[SLOTS][SMP_COLUMNS], ov_hi[SLOTS][SMP_COLUMNS];
static uint32_t generation;             /* scans of the kits so far */
static uint32_t live_id[6];             /* what each track's live sound named at the last tick */
static uint32_t pv_src[SOUND_SIZE / 4]; /* the sound the browser hands to the OS */
static const char *pv_mark;             /* the OS's preview buffer that holds a copy of pv_src, 0 if none does */
static int32_t pv_track;                /* the track whose sound pv_src copies */
static volatile uint32_t retry_id;      /* a file chosen in the browser: try it again if it failed */

/* --- names ----------------------------------------------------------------------------------- */

uint32_t smp_sound_id(const char *s)
{
    const uint16_t *k = (const uint16_t *)(s + KEY_AT);

    return (uint32_t)k[1] << 16 | k[2];
}

uint32_t smp_sound_ino(const char *s)
{
    return ((const uint16_t *)(s + KEY_AT))[0];
}

static int is_sample(const char *s)
{
    return (unsigned char)s[MACHINE_AT] == SAMPLE_MACHINE;
}

const smp_slot *smp_find(uint32_t id)
{
    int i;

    if (!(id & 1))
        return 0;
    for (i = 0; i < SLOTS; i++)
        if (smp_slots[i].state == SLOT_READY && smp_slots[i].id == id)
            return &smp_slots[i];
    return 0;
}

/* --- the file -------------------------------------------------------------------------------- */

static uint32_t be32(const unsigned char *p)
{
    return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 | p[3];
}

/* Header of a sample file of size bytes: +1 1 = stereo (interleaved), +4 audio bytes, +8 rate.
   Returns 1 if it can be played. */
static int parse_header(const unsigned char *h, uint32_t size, uint32_t *bytes, uint32_t *rate,
                        uint32_t *stereo)
{
    uint32_t len = be32(h + 4), r = be32(h + 8), st = h[1] == 1;

    if (len == 0 || len & (st ? 3u : 1u))
        return 0;
    if (size < HEADER || len > size - HEADER || len > (uint32_t)(POOL_END - POOL_BEGIN))
        return 0;
    if (r < RATE_MIN || r > RATE_MAX)
        return 0;
    *bytes = len;
    *rate = r;
    *stereo = st;
    return 1;
}

/* The drive may be used: mounted, and this task is not inside the file system's work already (the
   redraw that runs the tick might come from there; see FS_LOCK_HOLDER in os.h). */
static int drive_ok(void)
{
    return FS_MOUNTED && FS_LOCK_HOLDER != RUNNING_TASK;
}

/* Reads n bytes at pos of the file at inode ino into buf; 1 if all of them came. */
static int read_at(uint32_t ino, uint32_t pos, void *buf, uint32_t n)
{
    uint32_t fh[4];

    fh[0] = ino;
    fh[1] = pos;
    fh[2] = 0;
    fh[3] = 1;                          /* "open" */
    return FS_READ(buf, n, fh) == (int32_t)n;
}

/* --- the browser and the sound records ------------------------------------------------------- */

/* Both ways the browser reads a file come here (hooks.S): opening it (smp_hook_open) and resting the cursor on it
   (smp_hook_preview). A sample file on a SAMPLE track gives the track's sound naming that file instead of a preset;
   the OS then loads it into the track, or marks it for the pad and the TRIG keys, as it does with a preset. */
int smp_browser_open(void **result, const uint32_t *h, int32_t track)
{
    unsigned char head[HEADER];
    uint32_t bytes, rate, stereo;
    uint16_t *key;
    char *s;
    int i;

    if (track < 0 || track > 5 || !drive_ok())
        return 0;
    s = os_sound(track);
    if (!s || !is_sample(s))
        return 0;
    if (h[2] - 48 <= 112 || !(h[1] & 1))        /* a preset (48..160 B), or not a file: as before */
        return 0;
    if (!read_at(h[0], 0, head, HEADER) || !parse_header(head, h[2], &bytes, &rate, &stereo))
        return 0;
    for (i = 0; i < SOUND_SIZE; i++)            /* the track's sound, naming the file */
        ((char *)pv_src)[i] = s[i];
    pv_track = track;
    key = (uint16_t *)((char *)pv_src + KEY_AT);
    key[0] = (uint16_t)h[0];
    key[1] = (uint16_t)(h[1] >> 16);
    key[2] = (uint16_t)h[1];
    retry_id = h[1];
    result[0] = pv_src;                         /* no control block: the OS copies the 100 bytes */
    result[1] = 0;
    return 1;
}

void smp_after_save(char *record, const char *sound)
{
    int i;

    if (!record || !sound || !is_sample(sound))
        return;
    for (i = 0; i < 3; i++)
        ((uint16_t *)(record + REC_KEY_AT))[i] = ((const uint16_t *)(sound + KEY_AT))[i];
    *(uint16_t *)(record + REC_FILTER_AT) = 1;
}

/* The load has cleared k 0..32 of the sound (0x4005af12) and accepts version 2 only. A record
   from before the filter (0.4 and earlier, or the official OS) has SWEEP at 0, which would be a
   closed lowpass: it loads with the filter open. */
void smp_after_load(char *sound, const char *record)
{
    int i;

    if (!record || !sound || *(const int32_t *)(record + REC_VERSION) != 2 || !is_sample(sound))
        return;
    for (i = 0; i < 3; i++)
        ((uint16_t *)(sound + KEY_AT))[i] = ((const uint16_t *)(record + REC_KEY_AT))[i];
    if (*(const uint16_t *)(record + REC_FILTER_AT) == 0)
        *(uint16_t *)(sound + SWEEP_AT) = SMP_FILTER_CENTRE;
}

/* --- slots ----------------------------------------------------------------------------------- */

static smp_slot *slot_of(uint32_t id)
{
    int i;

    for (i = 0; i < SLOTS; i++)
        if (smp_slots[i].state != SLOT_FREE && smp_slots[i].id == id)
            return &smp_slots[i];
    return 0;
}

static void release(smp_slot *sl)
{
    sl->mem = 0;
    sl->size = 0;
    sl->state = SLOT_FREE;
}

/* A sound: if it plays SAMPLE and names a sample, the sample is wanted. */
static void note(const char *s)
{
    smp_slot *sl;
    uint32_t id;
    int i;

    if (!is_sample(s))
        return;
    id = smp_sound_id(s);
    if (!(id & 1))
        return;
    sl = slot_of(id);
    if (!sl) {
        for (i = 0; i < SLOTS && smp_slots[i].state != SLOT_FREE; i++)
            ;
        if (i == SLOTS)
            return;                             /* every slot in use: later */
        sl = &smp_slots[i];
        sl->id = id;
        sl->ino = smp_sound_ino(s);
        sl->mem = 0;
        sl->size = 0;
        sl->state = SLOT_WANT;
    } else if (sl->state == SLOT_FAILED && smp_sound_ino(s) != sl->ino) {
        sl->ino = smp_sound_ino(s);             /* named at another inode now (chosen again): try anew */
        sl->state = SLOT_WANT;
    }
    sl->seen = generation;
}

static void scan_kit(const char *kit)
{
    int i;

    for (i = 0; i < 6; i++)
        note(kit + KIT_SOUNDS + SOUND_SIZE * i);
    for (i = 0; i < POOL_SOUNDS; i++)
        note(kit + KIT_POOL + SOUND_SIZE * i);
}

/* Every sound that could be played: the kits of the 96 patterns, the kit the audio side plays, the
   tracks' live sounds, and the sound the browser marks for the pad and the TRIG keys (a sample under its
   cursor, smp_browser_open), so that it loads while the cursor rests on it and is freed once the cursor
   moves on or the browser closes. */
static void scan_kits(void)
{
    const char *kit = PLAY_KIT, *marked = PREVIEW_SOUND;
    int n;

    for (n = 0; n < KITS; n++)
        scan_kit(KIT(n));
    if (kit)
        scan_kit(kit);
    for (n = 0; n < 6; n++) {
        const char *s = os_sound(n);

        if (s)
            note(s);
    }
    if (marked)
        note(marked);
    else                                        /* nothing marked: no pad counts as held for it (a lost let-go) */
        for (n = 0; n < 6; n++)
            smp_pad_held[n] = 0;
}

/* After the browser loads a sound into a track the track keeps the same sound object, so the audio
   side would not copy its parameters again; clearing its sound makes the next note do it. */
static void refresh_live(void)
{
    int t;

    for (t = 0; t < 6; t++) {
        const char *s = os_sound(t);
        uint32_t id = s && is_sample(s) ? smp_sound_id(s) : 0;

        if (id != live_id[t]) {
            live_id[t] = id;
            CUR_SND(t) = 0;
        }
    }
}

/* A file chosen in the browser that had failed before (it may have come back at the same inode). */
static void take_retry(void)
{
    uint32_t id = retry_id;
    smp_slot *sl;

    if (!id)
        return;
    retry_id = 0;
    sl = slot_of(id);
    if (sl && sl->state == SLOT_FAILED)
        sl->state = SLOT_WANT;
}

/* Slots no sound names any more give their memory back, unless a voice still plays from it. */
static void retire_unseen(void)
{
    int i;

    for (i = 0; i < SLOTS; i++) {
        smp_slot *sl = &smp_slots[i];

        if (sl->state == SLOT_FREE || sl->seen == generation)
            continue;
        if (sl->state == SLOT_READY || sl->state == SLOT_RETIRING) {
            sl->state = SLOT_RETIRING;          /* first: the audio side starts nothing new on it */
            BARRIER();
            if (smp_voices_use(sl->mem, sl->mem + sl->size))
                sl->state = SLOT_READY;         /* still playing: next tick */
            else
                release(sl);
        } else
            release(sl);                        /* not READY: the audio side never saw it */
    }
}

/* First fit: the lowest place for size bytes past every slot that holds memory. */
static char *alloc(uint32_t size)
{
    char *at = POOL_BEGIN;
    int i, moved;

    size = (size + 3) & ~3u;
    do {
        moved = 0;
        for (i = 0; i < SLOTS; i++) {
            const smp_slot *s = &smp_slots[i];

            if (s->size && s->mem < at + size && s->mem + s->size > at) {
                at = (char *)(((uintptr_t)(s->mem + s->size) + 3) & ~(uintptr_t)3);
                moved = 1;
            }
        }
        if (at > POOL_END || (uint32_t)(POOL_END - at) < size)
            return 0;
    } while (moved);
    return at;
}

static uint32_t rate_q16(uint32_t rate)
{
    return (rate / 48000) << 16 | ((rate % 48000) << 16) / 48000;
}

/* Found at sl->ino: read the header; next, take memory. */
static void open_file(smp_slot *sl, uint32_t size)
{
    unsigned char head[HEADER];

    if (!read_at(sl->ino, 0, head, HEADER) || !parse_header(head, size, &sl->bytes, &sl->rate, &sl->stereo)) {
        sl->state = SLOT_FAILED;
        return;
    }
    sl->done = 0;
    sl->state = SLOT_NOMEM;
}

/* Stereo becomes mono in place as it arrives (n bytes at from, both multiples of 4): frame f
   (bytes 4f..4f+3) goes to bytes 2f..2f+1, which only frames before it held. */
static void mix(smp_slot *sl, uint32_t from, uint32_t n)
{
    int16_t *pcm = (int16_t *)sl->mem;
    uint32_t f;

    for (f = from / 4; f < (from + n) / 4; f++)
        pcm[f] = (int16_t)((pcm[2 * f] + pcm[2 * f + 1]) >> 1);
}

static void overview_start(const smp_slot *sl)
{
    int i = (int)(sl - smp_slots), c;

    for (c = 0; c < SMP_COLUMNS; c++) {
        ov_lo[i][c] = 32767;
        ov_hi[i][c] = -32768;
    }
}

/* Mono frames [f0, f1) of the sample are in: they go into their columns. A column covers frames
   [c * frames / SMP_COLUMNS, (c + 1) * frames / SMP_COLUMNS); the products stay below 2^32 because
   the pool holds at most 2^25 frames. */
static void overview_add(const smp_slot *sl, uint32_t f0, uint32_t f1)
{
    const int16_t *pcm = (const int16_t *)sl->mem;
    uint32_t frames = sl->stereo ? sl->bytes / 4 : sl->bytes / 2, c;
    int i = (int)(sl - smp_slots);

    for (c = f0 * SMP_COLUMNS / frames; c < SMP_COLUMNS; c++) {
        uint32_t a = c * frames / SMP_COLUMNS, b = (c + 1) * frames / SMP_COLUMNS, f;
        int16_t lo = ov_lo[i][c], hi = ov_hi[i][c];

        if (a >= f1)
            break;
        if (a < f0)
            a = f0;
        if (b > f1)
            b = f1;
        for (f = a; f < b; f++) {
            if (pcm[f] < lo)
                lo = pcm[f];
            if (pcm[f] > hi)
                hi = pcm[f];
        }
        ov_lo[i][c] = lo;
        ov_hi[i][c] = hi;
    }
}

int smp_view_state(uint32_t id, const int16_t **lo, const int16_t **hi)
{
    const smp_slot *sl;

    if (!(id & 1) || !(sl = slot_of(id)))
        return SLOT_FREE;
    if (sl->state == SLOT_READY) {
        *lo = ov_lo[sl - smp_slots];
        *hi = ov_hi[sl - smp_slots];
    }
    return (int)sl->state;
}

/* The whole file is in: a stereo one gives back the half it no longer needs, then the audio side
   may play it. */
static void finish(smp_slot *sl)
{
    uint32_t frames = sl->stereo ? sl->bytes / 4 : sl->bytes / 2;

    sl->pcm = (const int16_t *)sl->mem;
    sl->frames = (int32_t)frames;
    sl->size = (frames * 2 + 3) & ~3u;
    sl->rate_q16 = rate_q16(sl->rate);
    BARRIER();
    sl->state = SLOT_READY;
}

/* The inode that holds the file with this id now, from the file system's index; 0 if none. */
static uint32_t find_id(uint32_t id)
{
    uint32_t ino = 0;
    int32_t i;

    FS_LOCK();
    i = FS_FIND_ID(id);
    if (i >= 0)
        ino = FS_ID_INO(i);
    FS_UNLOCK();
    return ino;
}

/* Moves one slot on: the first that needs work, within this tick's budget. */
static void load_step(void)
{
    uint32_t h[4];
    int i;

    for (i = 0; i < SLOTS; i++) {
        smp_slot *sl = &smp_slots[i];
        uint32_t n, ino;

        switch (sl->state) {
        case SLOT_WANT:
            if (FS_ENTRY(sl->ino, h) != 0 || h[1] != sl->id) {
                ino = find_id(sl->id);          /* no longer at its inode: where the index has it */
                if (!ino || FS_ENTRY(ino, h) != 0 || h[1] != sl->id) {
                    sl->state = SLOT_FAILED;
                    return;
                }
                sl->ino = ino;
            }
            open_file(sl, h[2]);
            return;
        case SLOT_NOMEM:
            sl->mem = alloc(sl->bytes);
            if (!sl->mem)
                continue;                       /* no room yet: let the others go on */
            sl->size = (sl->bytes + 3) & ~3u;
            overview_start(sl);
            sl->state = SLOT_LOADING;
            /* fall through */
        case SLOT_LOADING:
            if (FS_ENTRY(sl->ino, h) != 0 || h[1] != sl->id) {
                release(sl);                    /* the file went away under us: start again */
                sl->state = SLOT_WANT;
                return;
            }
            n = sl->bytes - sl->done;
            if (n > READ_BUDGET)
                n = READ_BUDGET;
            if (!read_at(sl->ino, HEADER + sl->done, sl->mem + sl->done, n)) {
                release(sl);
                sl->state = SLOT_FAILED;
                return;
            }
            if (sl->stereo)
                mix(sl, sl->done, n);
            overview_add(sl, sl->done / (sl->stereo ? 4 : 2), (sl->done + n) / (sl->stereo ? 4 : 2));
            sl->done += n;
            if (sl->done == sl->bytes)
                finish(sl);
            return;
        default:
            break;
        }
    }
}

/* --- the tick -------------------------------------------------------------------------------- */

/* The redraw that calls the tick also runs from another task (a screen copy), so the tick takes a
   lock and skips a round when it is already running. */
static volatile unsigned char busy;

static int lock(void)
{
#ifdef SAMPLER_HOST
    if (busy)
        return 0;
    busy = 1;
    return 1;
#else
    unsigned char was;

    __asm__ volatile ("tas %1\n\tsne %0" : "=d"(was), "+m"(busy) : : "cc");
    return !was;
#endif
}

/* The marked sound follows the track's knobs. The OS copies the sound the browser hands out (pv_src) into one of its
   two preview buffers and marks it; a preview note then takes its 66 parameter bytes from that copy (0x40058a0a, after
   every preview note, 0x4005910e), so without this the pad would play the knobs as they were when the cursor arrived
   on the file (a knob turned meanwhile reaches a note that already plays, 0x40059534 writes the voice's target, but
   not the next one). While the marked sound is that copy (the same bytes when first seen, then the same buffer), its
   parameters but the sample's key take the track's sound's, every tick; a preset marked (another content) is left
   alone, as are its name and the rest. */
static void refresh_mark(void)
{
    const char *m = PREVIEW_SOUND, *s;
    int i;

    if (m != pv_mark) {
        pv_mark = 0;
        if (m) {
            for (i = 0; i < SOUND_SIZE && m[i] == ((const char *)pv_src)[i]; i++)
                ;
            if (i == SOUND_SIZE)
                pv_mark = m;
        }
    }
    if (!pv_mark)
        return;
    s = os_sound(pv_track);
    if (!s || !is_sample(s))
        return;
    for (i = 20; i < 20 + 66; i++)
        if (i < KEY_AT || i >= KEY_AT + 6)
            ((char *)pv_mark)[i] = s[i];
}

void smp_ui_tick(void)
{
    smp_view_install();
    if (!lock())
        return;
    generation++;
    refresh_mark();
    take_retry();
    scan_kits();
    refresh_live();
    retire_unseen();
    if (drive_ok())
        load_step();
    busy = 0;
}

#ifndef SAMPLER_HOST
/* 0x400075f0, in the screen's redraw (UI task, about 30 times a second): jsr 0x40076be4(view), which
   says whether the view needs drawing; it now runs the tick first. */
uint32_t smp_hook_tick(void *view)
{
    smp_ui_tick();
    return ((uint32_t (*)(void *))0x40076be4)(view);
}
#endif
