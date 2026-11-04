/* The RESAMPLE part's data block, shared by resample.c (the recorder), page.c (the page) and save.c (the save):
 * notes/79. The composer
 * writes it after the part's code (part.json's "data"); zero at boot but for what the composer gives it.
 *
 * License: MIT (LICENSE next to this file). */
#ifndef RESAMPLE_H
#define RESAMPLE_H
#include <stdint.h>

enum { IDLE, ARMED, REC, TAKEN };                   /* state */
enum { SRC_MAIN = 6, SRC_USB = 7 };                 /* src: 0..5 a track */
enum { START_TRIG, START_LEVEL, START_NOW };
enum { STOP_SILENT, STOP_LENGTH, STOP_RECORD };
enum { END_NONE, END_SILENT, END_LENGTH, END_RECORD, END_FULL };

struct data {
	/* the recorder (resample.c) */
	uint32_t buf;                               /* +0 the take's words (composer: the RAM claim after the ring) */
	uint32_t cap;                               /* +4 how many */
	uint32_t ring;                              /* +8 LEVEL's ring: 9 blocks of 64 words (composer) */
	uint8_t shift[3];                           /* +12 full scale 2^31 >> shift: a track, main, USB (composer) */
	uint8_t pad0;
	volatile uint8_t state;                     /* +16 IDLE, ARMED (by the UI), REC, TAKEN (by the audio) */
	uint8_t src;                                /* +17 0..5 a track, 6 main, 7 USB */
	uint8_t stereo;                             /* +18 two words a frame (main and USB only) */
	uint8_t start;                              /* +19 START_* */
	uint8_t stop;                               /* +20 STOP_* */
	volatile uint8_t req;                       /* +21 the page's RECORD while recording: end the take */
	uint8_t end;                                /* +22 END_*: why the take ended */
	uint8_t ring_n;                             /* +23 blocks in the ring */
	uint8_t ring_at;                            /* +24 the ring's next block */
	uint8_t pad1[3];
	uint32_t thr;                               /* +28 LEVEL's threshold, a magnitude */
	uint32_t sil;                               /* +32 the silence level */
	uint32_t cut;                               /* +36 the tail's */
	uint32_t limit;                             /* +40 the take's most frames */
	uint32_t frames;                            /* +44 frames in the take */
	uint32_t peak;                              /* +48 its largest magnitude */
	uint32_t quiet;                             /* +52 frames below the silence level since the last block over it */
	uint32_t loud;                              /* +56 frames up to the end of the last block over the tail's level */
	uint32_t level;                             /* +60 the last block's largest magnitude, for the page's meter */
	/* the page (page.c) */
	uint32_t page;                              /* +64 the page while it is up, else 0 */
	uint8_t src_set;                            /* +68 the settings, as the eight knobs set them: SOURCE 0..7 */
	uint8_t start_set;                          /* +69 START_* (TRIG shown as LEVEL for USB) */
	uint8_t thr_set;                            /* +70 THRESH, dB below full scale: 12..60 */
	uint8_t stereo_set;                         /* +71 STEREO (main and USB only) */
	uint8_t stop_set;                           /* +72 STOP_* */
	uint8_t length_set;                         /* +73 LENGTH, seconds: 1..40 (20 stereo) */
	uint8_t norm_set;                           /* +74 NORM (for the save, notes/79 §3.3) */
	uint8_t to_track;                           /* +75 TO Tn (for the save, notes/79 §4) */
	uint8_t settled;                            /* +76 the settings set once, at the first opening */
	uint8_t drawn;                              /* +77 the state at the last redraw */
	uint8_t sample;                             /* +78 SAMPLE's machine number in this build, 0xff without (composer) */
	uint8_t set_held;                           /* +79 SETTINGS held, as its events say (entries.S's rs_code) */
	uint32_t vt[44];                           /* +80 the page's vtable group, a copy of 0x40117918..0x401179c8 */
	/* the save (save.c) */
	uint8_t saving;                             /* +256 the take is being written */
	uint8_t asked;                              /* +257 the name editor came up for this take */
	uint8_t exists;                             /* +258 the name given is taken: the editor again, NAME EXISTS */
	uint8_t act;                                /* +259 what the next UI-task message does: ACT_* */
	uint8_t which;                              /* +260 the message posted last, 0 or 1 */
	uint8_t grid_set;                           /* +261 the page turned GRID RECORDING on (page.c) */
	uint8_t pad3[2];
	char name[16];                              /* +264 the take's name, at most 12 characters */
	char path[32];                              /* +280 "/recordings/" and the name */
	uint32_t fw;                                /* +312 the FileWriter while the file is open */
	uint32_t pos;                               /* +316 the take's words written */
	uint32_t total;                             /* +320 its words */
	uint32_t sh;                                /* +324 the save's shift */
	uint32_t gain;                              /* +328 and gain (NORM, Q15; 0 as heard) */
	uint32_t conv;                              /* +332 32 KiB for the 16-bit pieces: the RAM claim's end (composer) */
	struct msg {                                /* a message to the UI task (type 6: a callback, 0x400081fa) */
		uint8_t type;
		uint8_t pad[3];
		uint32_t data, zero, manager, callback, arg;
		volatile uint32_t busy;             /* +0x18 queued or running; the UI task clears it after */
	} msg[2];                                   /* +336 */
	uint8_t pad4[120];
};                                                  /* 512 bytes */

enum { ACT_NONE, ACT_EDITOR, ACT_SAVE, ACT_WRITE, ACT_CLOSE };

#ifdef RS_HOST
extern uint8_t *rs_host_mem;                        /* the RAM claim on the host: buf and ring count from it */
extern uint32_t rs_data[128];
#define WORDS(a) ((int32_t *)(rs_host_mem + (a)))
#else
extern char rs_data[];
#define WORDS(a) ((int32_t *)(a))
#endif
#define D ((struct data *)rs_data)

void rs_arm(uint32_t src, uint32_t stereo, uint32_t start, uint32_t stop, uint32_t thr_db, uint32_t seconds);
void rs_stop(void);
void rs_cancel(void);
void rs_release(void);
uint32_t rs_db(uint32_t mag, uint32_t sh);
void rs_header(uint8_t *h, uint32_t frames, uint32_t stereo);
void rs_norm(uint32_t peak, uint32_t *s, uint32_t *g);
uint32_t rs_pcm16(uint8_t *out, const int32_t *x, uint32_t words, uint32_t s, uint32_t g);
void rs_ask_name(void);                             /* save.c: the name editor, in the UI task */
void rs_grid_back(void);                            /* page.c: GRID RECORDING as it was before the page armed */
uint32_t rs_selected(void);                         /* page.c: the selected track, 0..5 */
int rs_to_track_ok(void);                           /* page.c: TO Tn applies (SAMPLE plays on the selected track) */

#endif
