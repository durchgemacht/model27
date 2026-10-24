/* What SAMPLE uses of the Model:Cycles OS 1.13. Each address was read in the OS's code; host tests
   (machine/test_sampler.c) replace this file with machine/host_os.h. */
#ifndef OS_H
#define OS_H

#include <stdint.h>

#ifdef SAMPLER_HOST
#include "host_os.h"
#else

/* --- voices and the audio side --------------------------------------------------------------- */
#define VOICE0      ((uintptr_t)0x42308828)     /* voice of track 0; one per track, 0x31c apart */
#define AMP_ENV(v)          ((void (*)(char *))0x400a9252)(v)
#define VCA(o, v)           ((void (*)(int32_t *, char *))0x400a9430)(o, v)
#define PUNCH(o, v)         ((void (*)(int32_t *, char *))0x400a967a)(o, v)
#define DECIMATE(v, in, o)  ((void (*)(char *, int32_t *, int32_t *))0x400a9f58)(v, in, o)
#define LUT_DECAY           ((const int32_t *)0x4011d84c)       /* DECAY -> factor per block (TONE's) */
#define DECIMATOR_STATE(v)  (*(int32_t **)((v) + 0x318))        /* its 8 + 4 frames for this voice */
/* The 66 bytes of parameters (k 0..32) of the sound a track plays, as the audio side copies them
   when a note's sound changes (0x40058a0a), before any smoothing. */
#define TARGETS(t)          ((const char *)0x800015ae + 66 * (t))
/* The sound whose parameters a track holds (0x800015a0 + (147 + t) * 4); 0 makes the next note
   copy its sound again (the OS does that itself after a preview note, 0x4005910e). */
#define CUR_SND(t)          (((void *volatile *)0x800017ec)[t])

/* --- sounds and kits --------------------------------------------------------------------------- */
/* A track's live sound: owner = the project singleton + 212 + t * 68, then the function at +40 of
   its vtable (the firmware's own derivation at 0x40023f0a; Model-TG and Modded-Cycles use the same
   walk). */
static inline char *os_sound(int t)
{
    char *owner = ((char *(*)(void))0x400cf866)();
    char *track;
    void **vt;

    if (!owner)
        return 0;
    track = owner + 212 + t * 68;
    vt = *(void ***)track;
    return vt && vt[10] ? ((char *(*)(char *))vt[10])(track) : 0;
}
/* The kits of the 96 patterns: 6 track sounds at +28, then the pool of 64 sounds at +694. */
#define KIT(n)              ((char *)0x409c9c80 + 7094 * (n))
#define KITS                96
#define KIT_SOUNDS          28
#define KIT_POOL            694
#define POOL_SOUNDS         64
/* The kit the audio side plays (0x800017e4, set by its kit message at 0x40058ddc), apart from the 96:
   the working copy of the current pattern's kit. Its pool holds the sounds that sound locks play. */
#define PLAY_KIT            (*(char *volatile *)0x800017e4)

/* --- the file system on the +Drive ------------------------------------------------------------ */
/* Set once the file system is mounted (0x40f07cf4; its calls check it). */
#define FS_MOUNTED          (*(volatile uint32_t *)0x40f07cf4)
/* Its lock (0x40fe6df0, taken by 0x40001cc4, given back by 0x40001df6): +0 the task that holds it;
   0x422fef30 is the running task. The lock lets its holder in again but does not count, so an inner
   give-back would free it while the outer work goes on. */
#define FS_LOCK_HOLDER      (*(void *volatile *)0x40fe6df0)
#define RUNNING_TASK        (*(void *volatile *)0x422fef30)
/* Fills {inode, id, size, inode word 16} from an inode number, under the file system's lock;
   0 if it is a file, -1 otherwise (0x4007de78). */
#define FS_ENTRY(ino, h)    ((int32_t (*)(uint32_t, uint32_t *))0x4007de78)(ino, h)
/* Reads len bytes at the handle's position {inode, position, -, open != 0} into buf and moves the
   position on; follows the file's chunk map through the file system's cache, under its lock.
   Returns the bytes read, or -1 (0x4007baaa). */
#define FS_READ(buf, len, fh)  ((int32_t (*)(void *, uint32_t, uint32_t *))0x4007baaa)(buf, len, fh)
/* Its index of files by id (the id is a hash of the file's content, bit 0 set; inode word 12): pairs
   {id, inode} at 0x401fb8a4, sorted by id, built at mount from the drive's table of ids (0x4007e042)
   and built again whenever a file is finished. FS_FIND_ID gives the pair's number, or -1
   (0x4007dc30, a binary search); call it under the lock. The OS's own resolver of file references
   (0x4007e3a0) looks there for a file that left its inode. */
#define FS_LOCK()           ((void (*)(void *))0x40001cc4)((void *)0x40fe6df0)
#define FS_UNLOCK()         ((void (*)(void *))0x40001df6)((void *)0x40fe6df0)
#define FS_FIND_ID(id)      ((int32_t (*)(uint32_t))0x4007dc30)(id)
#define FS_ID_INO(i)        (((const volatile uint32_t *)0x401fb8a8)[2 * (i)])

/* --- the screen -------------------------------------------------------------------------------- */
/* Two views take turns on the main screen; each is drawn through entry +16 of its vtable, the only
   reference to its draw method. MainScreenView (vtable 0x400ffe20, draw 0x4001b22a) shows the track
   with its level and pan while no value is shown. The knob view (vtable 0x4010052c, draw
   0x4001e40a) shows a turned parameter's name and value while one is shown (UIStates+88,
   0x4006b704); its knob handler 0x4001f4f0 keeps that parameter's index at +0x230 (0x4001f73a). */
#define MAIN_DRAW(v, b)     ((void (*)(void *, void *))0x4001b22a)(v, b)
#define KNOB_DRAW(v, b)     ((void (*)(void *, void *))0x4001e40a)(v, b)
#define KNOB_PARAM(v)       (*(const int32_t *)((const char *)(v) + 0x230))
#define VALUE_SHOWN()       (((char (*)(void *))0x4006b704)(((void *(*)(void))0x400cf9a8)()) != 0)
/* A trig is held, so a turned knob edits its locks (UIStates+356, 0x4006b736); the knob view then
   shows the held trigs' locked values (0x4001e5dc). */
#define TRIG_HELD()         (((char (*)(void *))0x4006b736)(((void *(*)(void))0x400cf9a8)()) != 0)
/* The selected track: 0x40012412(0x4000eb90(project)), as in Modded-Cycles' notes 32 and 44. */
static inline int32_t selected_track(void)
{
    char *project = ((char *(*)(void))0x400cf866)();

    if (!project)
        return -1;
    return ((int32_t (*)(void *))0x40012412)(((void *(*)(void *))0x4000eb90)(project));
}
/* The current pattern, 0..95, the way MainScreenView reads it for its pattern number (0x4001b276):
   0x4006a96c(0x400cfd0e()) reads the sequencer's current pattern (0x40054828) and clamps it. */
static inline int32_t current_pattern(void)
{
    return ((int32_t (*)(void *))0x4006a96c)(((void *(*)(void))0x400cfd0e)());
}
/* A Bitmap (constructor 0x40070172): +4 width, +8 height, +12 32-bit words per column, +16 the
   words; pixel (x, y) is bit 31 - (y & 31) of word x * pitch + y / 32, y = 0 at the bottom. Text:
   0x40071a04(bitmap, font, x, y, flags, format, ...), flags 0 = from x on, 2 = centred on x. A font
   object is {0x401117e0, glyphs} (0x40072260, undone by 0x40072080). */
#define FONT_MAKE(f, glyphs) ((void (*)(void *, const void *))0x40072260)(f, glyphs)
#define FONT_DROP(f)        ((void (*)(void *))0x40072080)(f)
#define FONT_SMALL          ((const void *)0x40140ab0)      /* 5 x 9 pixels */
#define FONT_MEDIUM         ((const void *)0x4014120c)      /* 7 x 9 pixels */
#define DRAW_TEXT           ((void (*)(void *, void *, int32_t, int32_t, int32_t, const char *, ...))0x40071a04)
/* The OS's objects of the 76 stock parameters, 100 bytes each from 0x40a71754, built at boot
   (0x400def5c); the accessor 0x4004df40(index) is detoured by the build so that SAMPLE's
   descriptors share SNARE's objects (Modded-Cycles' notes/18). An object's +0x20 is the function
   that writes a value as text: formatter(object + 0x14, value, buffer), called by 0x4000a70e for
   the value window, the TRACK + knob popup and locks. The stock one for 0..127 is 0x400456c8
   (sprintf "%d" of the value >> 8); others show -64..+63 (0x400456ea) or OFF (0x40045bd6). */
typedef int32_t (*smp_formatter)(void *, int32_t, char *);
#define UI_OBJECT(i)        ((char *)0x40a71754 + 100 * (i))
#define UI_FORMATTER(i)     (*(smp_formatter volatile *)(UI_OBJECT(i) + 0x20))
#define FMT_INT             ((smp_formatter)0x400456c8)

#endif
#endif
