/* Sample memory of SAMPLE: the samples its sounds name, loaded from the +Drive.

   The UI side (smp_ui_tick, about 30 times a second, never two at once) finds every SAMPLE sound in
   the 96 kits and their pools, the tracks' and the one the browser marks for the pad and the TRIG keys,
   loads the samples they name and frees those nothing names any more.
   It is the only writer of the slot table. The audio side only looks up READY slots (smp_find): a
   slot becomes READY once its data is complete, and stops being READY before its memory is reused,
   so neither side ever sees the other's half-done work.

   A sound names a sample by the file's id (a hash of its content with bit 0 set, inode word 12) and
   the inode it was found at, in its parameters k 25..27: +70 inode, +72 id high, +74 id low. When the
   inode no longer holds that id, the file system's own index of ids says where the file is now. */
#ifndef POOL_H
#define POOL_H

#include <stdint.h>

/* SAMPLE's index among the machines: the build sets it. With CM_SYMBOLS it is the address of an undefined
   symbol that the composer resolves when it places the compiled object (a Level B builder, which never
   compiles: the object is built once and composed many times); otherwise a compile-time constant. */
#ifdef CM_SYMBOLS
extern char cm_machine_index[];
#define SAMPLE_MACHINE ((int)(long)cm_machine_index)
#elif !defined(SAMPLE_MACHINE)
#define SAMPLE_MACHINE 6
#endif
#define SLOTS 128
/* Start (COLOR) and Length (SHAPE) as on the Model:Samples (0x400a62dc there): 8.8 words from 0 to
   120.0; a trig plays from Start / 120 of the sample to (Start + Length) / 120, at most to its end. */
#define SMP_SPAN (120 << 8)
#define SMP_COLUMNS 105                 /* the waveform's width on the screen: stretches of a sample */
/* The switches, bits of the sound's k 32 (+84; model27's notes/63 §16): model27's shortcut layer
   flips them on MACHINES + PUNCH and MACHINES + GATE (RETRIG up to its 0.2) and saves them with the
   sound; since its 0.5, with trigs held, it locks them per step instead (a p-lock of k 32, notes/63
   §27), whose word also says which switches it holds. Only builds with that layer read them
   (SMP_SWITCHES): elsewhere k 32 may belong to another mod (Modded-Cycles' lfo-plus keeps k 28..32). */
#define SW_LOOP     0x100               /* MACHINES + PUNCH: the window again and again */
#define SW_REVERSE  0x200               /* MACHINES + GATE: from its end to its start */
#define SW_LOOP_LOCKED    0x400         /* in a lock: it holds Loop, at its SW_LOOP */
#define SW_REVERSE_LOCKED 0x800         /* in a lock: it holds Reverse, at its SW_REVERSE */
#define SOUND_K32   84

enum {
    SLOT_FREE,                          /* unused */
    SLOT_WANT,                          /* a sound names it; look for the file next */
    SLOT_LOADING,                       /* memory taken, reading */
    SLOT_READY,                         /* complete: the audio side may play it */
    SLOT_FAILED,                        /* not found or not a sample: given up until chosen again */
    SLOT_NOMEM,                         /* no room in the pool yet */
    SLOT_RETIRING                       /* on its way out; the audio side starts nothing on it */
};

typedef struct {
    volatile uint32_t state;
    uint32_t id;                        /* the file's id */
    uint32_t ino;                       /* the inode it was last found at */
    uint32_t seen;                      /* the last scan that found a sound naming it */
    char *mem;                          /* its memory in the pool, or 0 */
    uint32_t size;                      /* bytes of memory it holds */
    uint32_t bytes;                     /* audio bytes in the file (both channels if stereo) */
    uint32_t done;                      /* audio bytes read so far */
    uint32_t stereo;
    uint32_t rate;                      /* the file's sample rate, Hz */
    /* READY: what the audio side plays */
    const int16_t *pcm;                 /* mono frames */
    int32_t frames;
    uint32_t rate_q16;                  /* rate / 48 kHz, Q16.16 */
} smp_slot;

extern smp_slot smp_slots[SLOTS];

/* The id a sound names (0 if none) and the inode it was found at. */
uint32_t smp_sound_id(const char *sound);
uint32_t smp_sound_ino(const char *sound);

/* Audio side: the READY slot that holds the sample with this id, or 0. */
const smp_slot *smp_find(uint32_t id);

/* Screen: the state of the sample with this id (SLOT_FREE while no slot holds it) and, once READY,
   the lowest and highest frame of each of its SMP_COLUMNS stretches (lo > hi: no frames). */
int smp_view_state(uint32_t id, const int16_t **lo, const int16_t **hi);

/* UI side. */
void smp_ui_tick(void);
int smp_browser_open(void **result, const uint32_t *handle, int32_t track);
void smp_after_save(char *record, const char *sound);
void smp_after_load(char *sound, const char *record);

/* From the bridge (sampler.c): does a voice play from memory in [lo, hi)? */
int smp_voices_use(const void *lo, const void *hi);

/* The pads held, by track (sampler.c): set and cleared by the pads' own note functions (hooks.S), cleared by the tick
   while the browser marks nothing. */
extern volatile uint8_t smp_pad_held[6];

/* From the bridge (sampler.c): the pad of track t was just pressed; nonzero when its note gets its note-off at once
   (hooks.S), so the sequencer's trigs reach the track while it is held. */
int smp_pad_frees(int t);
int smp_key_frees(int t);                       /* a TRIG key's note too (hooks.S, smp_hook_key_on) */

#endif
