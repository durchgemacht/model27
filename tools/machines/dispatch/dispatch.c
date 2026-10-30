/* The dispatchers of model27's builder (notes/63 §4, steps B4c and B4d): a part the composer adds to a build in
   which two or more machines take the same OS point. Compiled once by tools/gen_parts.py into dispatch.o and placed
   by tools/relocate.py like a package; the composer writes the data block (dp_data) right after it and resolves
   dp_data, the block's address, as a patch point. Only the dispatchers of the shared points are placed: a point one
   machine takes keeps that machine's own entry or hook. Addresses are VAs of OS 1.13.

     dp_main   entry +16 of MainScreenView's vtable (0x400ffe30; stock 0x4001b22a, its draw);
     dp_knob   entry +16 of the knob view's vtable (0x4010053c; stock 0x4001e40a, its draw);
     dp_note   entry +16 of NoteVelocityView's vtable (0x40102578; stock 0x400299de, its draw: the held trig's note,
               velocity and length over the left half, while a trig is held);
     dp_tick   0x400075f0, jsr 0x40076be4(view) in the screen's redraw, about 30 times a second;
     dp_open   0x400a6602, jsr 0x400a3052 in the browser, which reads the file it opens (open.S).

   dp_main, dp_knob and dp_note call the draw of the selected track's machine, or the stock draw. dp_tick calls every
   machine's tick, in machine order, then the stock 0x40076be4, a getter (the view's byte +32: whether it needs
   drawing), whose answer it returns; each machine's tick also ends with that getter, harmlessly. dp_open goes to the
   hook of the machine of the track the browser loads into, or to the stock 0x400a3052, with the registers of the
   call. Each machine's method still checks the track itself, as SAMPLE's do: the dispatcher only spares it the calls
   for the other machines' tracks. A track's machine is found as SAMPLE finds it (its machine/view.c): the project
   singleton's track + 212 + t * 68, the sound from the method at +40 of its vtable, the machine in the sound's byte
   +38.

   dp_data, filled by the composer (part.json, "data"):
     +0 first machine (byte), +1 number of machines (byte)
     +4 per machine, MainScreenView's draw; +28 the knob view's draw; +52 the tick; +76 the browser's hook;
     +100 NoteVelocityView's draw (since 0.3)
     (0 = none: the stock method for a draw and the browser, nothing for the tick)

   License: MIT (LICENSE next to this file). Plain C99, no libc. */
#include <stdint.h>

typedef void (*draw_fn)(void *view, void *bitmap);
typedef uint32_t (*tick_fn)(void *view);

struct dp_data {
	uint8_t first, count, pad[2];
	draw_fn main[6];
	draw_fn knob[6];
	tick_fn tick[6];
	void *open[6];
	draw_fn note[6];
};

extern const struct dp_data dp_data;    /* the composer's block, right after this code: a patch point */

#define MAIN_DRAW   ((draw_fn)0x4001b22a)
#define KNOB_DRAW   ((draw_fn)0x4001e40a)
#define NOTE_DRAW   ((draw_fn)0x400299de)
#define TICK_STOCK  ((tick_fn)0x40076be4)
#define OPEN_STOCK  ((void *)0x400a3052)
#define MACHINE_AT  38

/* Track t's machine, or -1 without a project, a track 0..5 or a sound. */
static int32_t machine_of(int32_t t)
{
	char *project = ((char *(*)(void))0x400cf866)();
	char *track;
	void **vt;
	const char *s;

	if (!project || t < 0 || t > 5)
		return -1;
	track = project + 212 + t * 68;
	vt = *(void ***)track;
	s = vt && vt[10] ? ((const char *(*)(char *))vt[10])(track) : 0;
	return s ? (unsigned char)s[MACHINE_AT] : -1;
}

static int32_t selected_machine(void)
{
	char *project = ((char *(*)(void))0x400cf866)();

	if (!project)
		return -1;
	return machine_of(((int32_t (*)(void *))0x40012412)(((void *(*)(void *))0x4000eb90)(project)));
}

static draw_fn pick(const draw_fn *table, draw_fn stock)
{
	int32_t i = selected_machine() - dp_data.first;

	return i >= 0 && i < dp_data.count && table[i] ? table[i] : stock;
}

void dp_main(void *view, void *bitmap)
{
	pick(dp_data.main, MAIN_DRAW)(view, bitmap);
}

void dp_knob(void *view, void *bitmap)
{
	pick(dp_data.knob, KNOB_DRAW)(view, bitmap);
}

void dp_note(void *view, void *bitmap)
{
	pick(dp_data.note, NOTE_DRAW)(view, bitmap);
}

uint32_t dp_tick(void *view)
{
	int32_t i;

	for (i = 0; i < dp_data.count; i++)
		if (dp_data.tick[i])
			dp_data.tick[i](view);
	return TICK_STOCK(view);
}

/* For dp_open (open.S): the method to run for the browser that opens a file, given the browser's pointer (the call's
   a2: its object's +664 is the track it loads into). */
void *dp_open_pick(char **browser)
{
	int32_t i = machine_of(*(const int32_t *)(*browser + 664)) - dp_data.first;

	return i >= 0 && i < dp_data.count && dp_data.open[i] ? dp_data.open[i] : OPEN_STOCK;
}
