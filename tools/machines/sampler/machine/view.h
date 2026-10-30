/* SAMPLE's view on the Model:Cycles' main screen, see view.c. */
#ifndef VIEW_H
#define VIEW_H

#include <stdint.h>

/* The OS's Bitmap as far as the view uses it (constructor 0x40070172). */
typedef struct {
    const void *vtable;
    int32_t width, height;
    int32_t pitch;                      /* 32-bit words per column */
    uint32_t *words;                    /* pixel (x, y): bit 31 - (y & 31) of words[x * pitch + y / 32] */
} smp_bitmap;

/* The view of a SAMPLE sound: its sample's waveform with start and end marked, its name above. */
void smp_view_draw(smp_bitmap *b, const char *sound);

/* In place of the draw methods of MainScreenView, of the knob view and of NoteVelocityView (vtable
   entries +16). */
void smp_main_draw(void *view, smp_bitmap *b);
void smp_knob_draw(void *view, smp_bitmap *b);
void smp_note_draw(void *view, smp_bitmap *b);

/* Cutoff's value as text, -64..63 with 0 in the middle, when the selected track plays SAMPLE; the
   stock 0..127 otherwise (the object is SNARE's SWEEP's too). Installed into the object by
   smp_view_install, which the tick calls; it does its work once. */
int32_t smp_fmt_cutoff(void *self, int32_t value, char *buf);
void smp_view_install(void);

#endif
