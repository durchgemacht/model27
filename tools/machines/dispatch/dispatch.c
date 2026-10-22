/* The dispatchers of model27's builder (notes/63 §4, step B4c): a part the composer adds to a build in which two or
   more machines take the same OS point. Compiled once by tools/gen_parts.py into dispatch.o and placed by
   tools/relocate.py like a package; the composer writes the data block (dp_data) right after it and resolves
   dp_data, the block's address, as a patch point. Only the dispatchers of the shared points are placed: a point one
   machine takes keeps that machine's own entry. Addresses are VAs of OS 1.13.

     dp_main   entry +16 of MainScreenView's vtable (0x400ffe30; stock 0x4001b22a, its draw);
     dp_knob   entry +16 of the knob view's vtable (0x4010053c; stock 0x4001e40a, its draw).

   Each one calls the draw of the selected track's machine, from the block, or the stock draw. Each machine's draw
   still checks the track itself and draws the stock view in every case it does not take, as SAMPLE's do: the
   dispatcher only spares it the calls for the other machines' tracks. The track's machine is found as SAMPLE finds
   it (its machine/view.c): the project singleton's track + 212 + t * 68, the sound from the method at +40 of its
   vtable, the machine in the sound's byte +38.

   dp_data, filled by the composer (part.json, "data"):
     +0 first machine (byte), +1 number of machines (byte)
     +4 per machine, MainScreenView's draw, +28 per machine, the knob view's draw (0 = the stock draw)

   License: MIT (LICENSE next to this file). Plain C99, no libc. */
#include <stdint.h>

typedef void (*draw_fn)(void *view, void *bitmap);

struct dp_data {
	uint8_t first, count, pad[2];
	draw_fn main[6];
	draw_fn knob[6];
};

extern const struct dp_data dp_data;    /* the composer's block, right after this code: a patch point */

#define MAIN_DRAW   ((draw_fn)0x4001b22a)
#define KNOB_DRAW   ((draw_fn)0x4001e40a)
#define MACHINE_AT  38

/* The selected track's machine, or -1 without a project, a track 0..5 or a sound. */
static int32_t selected_machine(void)
{
	char *project = ((char *(*)(void))0x400cf866)();
	char *track;
	void **vt;
	const char *s;
	int32_t t;

	if (!project)
		return -1;
	t = ((int32_t (*)(void *))0x40012412)(((void *(*)(void *))0x4000eb90)(project));
	if (t < 0 || t > 5)
		return -1;
	track = project + 212 + t * 68;
	vt = *(void ***)track;
	s = vt && vt[10] ? ((const char *(*)(char *))vt[10])(track) : 0;
	return s ? (unsigned char)s[MACHINE_AT] : -1;
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
