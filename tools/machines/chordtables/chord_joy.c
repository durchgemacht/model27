/* Chord Joy: chords of a key on TRIG 1-8, the chord's character on TRIG 9-16, for CHORD's tracks (OS 1.13).
 *
 * MACHINES + PUNCH switches it per sound (the shortcut layer's switch, bit 8 of k 32, sound +84). With the switch
 * on, on a CHORD track, in keyboard mode, FUNC, TRACK, PATTERN and MACHINES not held:
 *   TRIG 1-8   the degrees I ii iii IV V vi vii° I' of the major scale on the note TRIG 1 plays on the stock
 *              keyboard (KBT and Transpose's octave included): SHAPE set to the degree's chord, then the stock
 *              keyboard handler plays the key of the degree's root (an event copied, its key code moved).
 *   TRIG 9-16  while a degree is held: the chord's character (9 up-left .. 16 down-right, see DIRS below); the
 *              chord is struck again with the new SHAPE. Released: SHAPE back to the degree's plain chord, no new
 *              note and nothing recorded. Without a degree held they do nothing.
 * The note, its velocity, retrig, live recording and the release are the stock keyboard's; SHAPE goes through the
 * track's parameter object (vtable 0x400fd134, its set method 0x4000ba7a), as a knob turned, which records a lock
 * of SHAPE on the step while REC + PLAY runs (0x4000f4b8). Every other key, track, mode or combination goes to the
 * entry behind (cj_next_keys: Transpose's tr_keys or the stock 0x4001a0d2) unchanged.
 * The audio side smooths every knob's word over many blocks (0x40058474); a live note on the same sound keeps the
 * glide, so the chord would start as the old one and slide to the new. Each SHAPE set here also puts the track's
 * smoothing state at the new word, as the OS does when a note brings another sound (0x400582d0): the note starts on
 * its chord (notes/87 §7).
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>

typedef uint32_t (*keys_fn)(void *, uint8_t *);

#define KEY_HELD ((uint32_t (*)(uint32_t))0x4007faf4)          /* (logical key) -> 1 while held */
#define UI_STATE ((uint8_t *(*)(void))0x400cf9a8)
#define GRID_MODE ((uint32_t (*)(uint8_t *))0x4006b978)
#define SELECT_ARMED ((uint32_t (*)(uint8_t *))0x4006bb18)
#define PROJECT ((uint8_t *(*)(void))0x400cf866)
#define PROJECT_TRACKS ((void *(*)(void *))0x4000eb90)
#define ACTIVE_TRACK ((uint32_t (*)(void *))0x40012442)        /* the keyboard's own: the selected track, 0..5 */
#define PARAM_SET ((void (*)(void *, uint32_t, uint32_t, uint32_t, uint32_t))0x4000ba7a)

#define K_FUNC 1
#define K_TRACK 2
#define K_PATTERN 3
#define K_MACHINES 5
#define CODE_TRIG1 16                               /* TRIG n is 15 + n */
#define TRACK_AT 212                                /* the project's track t at +212 + 68 t */
#define TRACK_SIZE 68
#define SOUND_METHOD 40                             /* its vtable +40: the track's sound */
#define MACHINE_AT 38                               /* sound: the machine */
#define SWITCHES_AT 84                              /* sound: k 32, bit 8 MACHINES + PUNCH */
#define CHORD 5
#define SHAPE_DESC 72                               /* CHORD's SHAPE */
#define PARAM_VTABLE 0x400fd134u
#define EV_COPY 32                                  /* the key event's bytes copied (code +12, flags +16) */
#define SHAPE_K 12                                  /* descriptor 72's k (0x4010dce0 + 56 * 72 + 4) */
#define SMOOTH_STATE 0x800011e8u                    /* the smoothing's state: word j's long, value << 16 */
#define SMOOTH_J(t, k) (7 + 33 * (t) + (k))         /* j of track t's k, as 0x400582d0 and 0x40059534 count */

extern char cj_next_keys[];                         /* the key handler behind: Transpose's, or the stock one */
#define NEXT ((keys_fn)(uint32_t)cj_next_keys)

/* The degrees' roots in semitones from TRIG 1 and their quality: 0 major, 1 minor, 2 diminished. */
static const uint8_t ROOT[8] = {0, 2, 4, 5, 7, 9, 11, 12};
static const uint8_t QUAL[8] = {0, 1, 1, 0, 0, 1, 2, 0};
/* SHAPE's row per quality and direction: 0 none, then TRIG 9..16 = up-left Aug, up Flip, up-right Dom7, left Dark,
 * right Jazzy, down-left Sweet (6th), down Open (sus4), down-right Lush (add9). Rows of CHORD's table (3 minor,
 * 4 Major, 5 sus2, 6 sus4, 7 m7, 8 dominant 7, 10 Maj7, 12 dim7, 13 madd9, 14 Madd9, 15 m6, 16 M6, 19 mb5,
 * 21 m7b5, 23 M#5, 27 m9no5). */
static const uint8_t DIRS[3][9] = {
	{4, 23, 3, 8, 3, 10, 16, 6, 14},            /* major */
	{3, 23, 4, 8, 19, 7, 15, 6, 13},            /* minor */
	{19, 23, 3, 8, 12, 21, 5, 6, 27},           /* diminished */
};

static struct {
	uint8_t degree;                             /* the degree key held, 1..8, 0 none */
	uint8_t dir;                                /* the direction key held, 1..8, 0 none */
	uint8_t track;                              /* the track of the degree's press */
	uint8_t sounding;                           /* the degree whose root key the stock handler holds, 0 none */
	uint8_t taken;                              /* bits of TRIG 1..16 whose press this part took (16 bits) */
	uint8_t taken_hi;
} S;

static uint8_t *track_holder(uint8_t *project, uint32_t t)
{
	return project + TRACK_AT + TRACK_SIZE * t;
}

static uint8_t *sound_of(uint8_t *holder)
{
	uint32_t *vt = *(uint32_t **)holder;
	return ((uint8_t *(*)(void *))vt[SOUND_METHOD / 4])(holder);
}

/* The selected track when Chord Joy answers it, else 6. */
static uint32_t joy_track(void)
{
	uint8_t *p, *st, *snd;
	uint32_t t;
	if (KEY_HELD(K_FUNC) || KEY_HELD(K_TRACK) || KEY_HELD(K_PATTERN) || KEY_HELD(K_MACHINES))
		return 6;
	st = UI_STATE();
	if (!st || (GRID_MODE(st) & 0xff) || (SELECT_ARMED(st) & 0xff))
		return 6;
	p = PROJECT();
	if (!p)
		return 6;
	t = ACTIVE_TRACK(PROJECT_TRACKS(p));
	if (t > 5)
		return 6;
	snd = sound_of(track_holder(p, t));
	if (!snd || snd[MACHINE_AT] != CHORD || !(snd[SWITCHES_AT] & 1))   /* bit 8 of the big-endian word */
		return 6;
	return t;
}

static void set_shape(uint32_t t, uint32_t row, uint32_t record)
{
	uint8_t *p = PROJECT();
	uint32_t obj[2];
	if (!p)
		return;
	obj[0] = PARAM_VTABLE;
	obj[1] = (uint32_t)track_holder(p, t);
	PARAM_SET(obj, SHAPE_DESC, row << 8, t, record);
	*(volatile uint32_t *)(SMOOTH_STATE + 4 * SMOOTH_J(t, SHAPE_K)) = (row << 8) << 16;
}

/* The stock handler sees the degree's root key, pressed or released, as the key event ev says. */
static void root_key(void *view, const uint8_t *ev, uint32_t degree, uint32_t press)
{
	uint8_t copy[EV_COPY];
	uint32_t i;
	for (i = 0; i < EV_COPY; i++)
		copy[i] = ev[i];
	*(uint32_t *)(copy + 12) = CODE_TRIG1 + ROOT[degree - 1];
	*(uint32_t *)(copy + 16) = press ? (*(const uint32_t *)(ev + 16) | 1) & ~0x28u
	                                 : *(const uint32_t *)(ev + 16) & ~0x29u;
	NEXT(view, copy);
}

static void strike(void *view, const uint8_t *ev, uint32_t record)
{
	uint32_t d = S.degree;
	if (S.sounding) {                           /* the root that sounds, maybe another degree's (keys overlapped) */
		root_key(view, ev, S.sounding, 0);
		S.sounding = 0;
	}
	set_shape(S.track, DIRS[QUAL[d - 1]][S.dir], record);
	root_key(view, ev, d, 1);
	S.sounding = (uint8_t)d;
}

static int taken(uint32_t k)
{
	return k < 8 ? (S.taken >> k) & 1 : (S.taken_hi >> (k - 8)) & 1;
}

static void mark(uint32_t k, int on)
{
	uint8_t *b = k < 8 ? &S.taken : &S.taken_hi;
	uint8_t m = (uint8_t)(1u << (k & 7));
	*b = on ? (uint8_t)(*b | m) : (uint8_t)(*b & ~m);
}

/* KeyboardView's key handler (its vtable +8, 0x400ff9cc): (view, event), 1 when taken. */
uint32_t cj_keys(void *view, uint8_t *ev)
{
	uint32_t code = *(const uint32_t *)(ev + 12), flags = *(const uint32_t *)(ev + 16), k, t;
	if (code < CODE_TRIG1 || code > CODE_TRIG1 + 15)
		return NEXT(view, ev);
	k = code - CODE_TRIG1;                      /* 0..15 */
	if (!(flags & 1)) {                         /* a release: ours when its press was */
		if (!taken(k))
			return NEXT(view, ev);
		mark(k, 0);
		if (k < 8) {
			if (S.degree == k + 1) {
				if (S.sounding)
					root_key(view, ev, S.sounding, 0);
				S.degree = S.dir = S.sounding = 0;
			}
		} else if (S.dir == k - 7) {
			S.dir = 0;
			if (S.degree)               /* snap back, no new note, nothing recorded */
				set_shape(S.track, DIRS[QUAL[S.degree - 1]][0], 0);
		}
		return 1;
	}
	if (flags & 0x28)                           /* a repeat or a long press: ours when the press was */
		return taken(k) ? 1 : NEXT(view, ev);
	if ((t = joy_track()) > 5)
		return NEXT(view, ev);
	mark(k, 1);
	if (k < 8) {
		S.degree = (uint8_t)(k + 1);
		S.dir = 0;
		S.track = (uint8_t)t;
		strike(view, ev, 1);
	} else if (S.degree && S.track == t) {
		S.dir = (uint8_t)(k - 7);
		strike(view, ev, 1);
	}
	return 1;
}
