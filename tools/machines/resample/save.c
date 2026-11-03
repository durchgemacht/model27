/* The RESAMPLE page's save (notes/79 §4, §11; step R3), with page.c and resample.c. Addresses are VAs of OS 1.13.
 *
 * Everything here runs in the UI task, which may wait on the drive: the master UI task (0x40007d46) takes messages from
 * the queue 0x404a9154, and one of type 6 carries a callback, called with its closure and its word at +0x14
 * (0x400081fa); its +0x18 is cleared once it has run. The page posts one (rs_ask_name, from its key handler or its
 * periodic method), and each step of the save posts the next on the other of two messages, the one running being
 * released only after its callback returns. That is Model-TG's save of a resampled take (TinyGregAudio, MIT: its
 * sv_post / sv_run, rs_name_open, rs_save_do), whose way through the OS this follows:
 *
 * - ACT_EDITOR: the stock name editor (ModelsNameView, as the pattern rename opens it at 0x4002c92a): ctor
 *   0x40041152(editor, title, name, prompt, 0, 12, draw, save) on 0xac bytes, the three Strings by 0x400f980c and
 *   dropped after, the two std::functions {data, 0, manager, invoker} copied by the editor and released after
 *   (0x400cf044); presented on the screen the page is on, above it (0x4007722a(TARGET(VIEWS()), editor, 0): the
 *   generic holder 0x400fbf24, then 0x4007700e, as the page itself). The stock renames present it through their
 *   parent (0x40076220(parent + 0x38, editor, 0)), which does nothing when the parent's +0x38 + 0x2c is 0, as it is
 *   for a page presented as ours (the first test on the machine, notes/79 §11). Prefilled with the first free
 *   REC-nnn, or the name given when it was taken, its title then NAME EXISTS (the title is shown while the name is
 *   edited; the prompt is the question the editor asks on confirming, "Save recording as REC-001?", YES / ABORT /
 *   EDIT). Backing out calls nothing: the page under it shows the take as NOT SAVED. The save invoker gets the name
 *   (a String: its characters at *(char **)).
 * - ACT_SAVE: a name that exists (open 0x4007bc5e(path, "r", fh) succeeds; closed 0x4007bc1c) opens the editor
 *   again; else the stock FileWriter (ctor 0x4007c7ca(fw, path, size) on 0x8110 bytes, which makes the folder; vtable
 *   +0x0c flush, +0x10 write, +0x14 commit, +0x18 abort and delete, +0x1c an error; dtor 0x4007c76a) and the header.
 *   The FileWriter mutes the audio while it lives, as every stock save does (notes/79 §4).
 * - ACT_WRITE: 16 384 words of the take into 16-bit in the 32 KiB at the claim's end and written, one piece a message
 *   (a write only fills the FileWriter's 32 KiB buffer, so each piece is written and flushed: Model-TG's rs_fw_put).
 * - ACT_CLOSE: the 16 zero bytes after the frames, then commit, or abort on an error; the take let go, the page closed
 *   and the OS's popup (0x400747c0 on 0x9c bytes, its holder 0x400fbf40, as 0x4000d750 shows "Lock mem full!")
 *   saying where it went; after an error the take stays and the popup says so. Should a step find no free message,
 *   the file is given up the same way, so that the FileWriter (and the mute) never outlives the save.
 *
 * License: MIT (LICENSE next to this file; the save's way through the OS follows Model-TG's, MIT, LICENSE-Model-TG). */
#include "resample.h"

#define NEW(n) ((void *(*)(uint32_t))0x400802e0)(n)                 /* operator new */
#define DELETE(p) ((void (*)(void *))0x400802ec)(p)
#define ALLOC(n) ((uint32_t (*)(uint32_t))0x40080064)(n)            /* a closure's data, released by its manager */
#define MANAGER 0x4002f136u                                          /* the closures' generic manager */
#define FREE_CLOSURE(c) ((void (*)(void *))0x400cf044)(c)
#define STRING(s, c, tag) ((void (*)(void *, const char *, void *))0x400f980c)(s, c, tag)
#define STRING_DROP(s) ((void (*)(void *))0x400f7d5c)(s)
#define POST(q, m) ((void (*)(uint32_t, void *))0x40001fba)(q, m)
#define MQ_MAIN 0x404a9154u                                          /* the master UI task's queue */
#define EDITOR_SIZE 0xac
#define EDITOR(e, t, n, p, z, len, draw, save) \
	((void (*)(void *, void *, void *, void *, uint32_t, uint32_t, void *, void *))0x40041152)(e, t, n, p, z, len, draw, save)
#define PRESENT_VIEW(t, v, x) ((void (*)(void *, void *, uint32_t))0x4007722a)(t, v, x)  /* holder 0x400fbf24 */
#define FILE_OPEN(path, mode, fh) ((int32_t (*)(const char *, const char *, void *))0x4007bc5e)(path, mode, fh)
#define FILE_CLOSE(fh) ((void (*)(void *))0x4007bc1c)(fh)
#define READ_MODE ((const char *)0x40126ce4)                         /* "r" */
#define FW_SIZE 0x8110
#define FW_CTOR(fw, path, size) ((void (*)(void *, const char *, uint32_t))0x4007c7ca)(fw, path, size)
#define FW_DTOR(fw) ((void (*)(void *))0x4007c76a)(fw)
#define FW_FLUSH 0x0c
#define FW_WRITE 0x10
#define FW_COMMIT 0x14
#define FW_ABORT 0x18
#define FW_ERROR 0x1c
#define POPUP_SIZE 0x9c
#define POPUP(p, s) ((void (*)(void *, void *))0x400747c0)(p, s)
#define POPUP_HOLDER_VT 0x400fbf40u
#define VIEWS_UP (*(void *const volatile *)0x40fe4178)
#define VIEWS() ((char *(*)(void))0x400d0974)()
#define TARGET(v) ((void *(*)(void *))0x400060d8)(v)
#define PRESENT(t, pair, x) ((void (*)(void *, void *, uint32_t))0x4007700e)(t, pair, x)
#define DROP(ref) ((void (*)(void *))0x400cf23c)(ref)
#define NEEDS_REDRAW(v) ((void (*)(void *))0x40076082)(v)
#define CLOSE_AT 0x28                               /* the view's close, in its primary vtable */
#define NAME_MAX 12
#define PIECE 16384u                                /* words a message: 32 KiB of 16-bit */
#define DIR "/recordings/"

typedef char data_is_512[sizeof(struct data) == 512 ? 1 : -1];

struct closure {
	uint32_t data, zero, manager, invoker;
};

void rs_run(void *closure, uint32_t arg);
void rs_named(void *closure, char **name);
void rs_no_draw(void *closure, void *bitmap, int32_t x, int32_t y);

static void copy(char *to, const char *from, int n)
{
	while (n-- > 1 && *from)
		*to++ = *from++;
	*to = 0;
}

static void cat(char *to, const char *a, const char *b, int n)
{
	int i = 0;
	while (i < n - 1 && *a)
		to[i++] = *a++;
	while (i < n - 1 && *b)
		to[i++] = *b++;
	to[i] = 0;
}

/* Calls the FileWriter's method at off. */
static uint32_t fw_call(uint32_t off, void *a, uint32_t b)
{
	char *fw = (char *)D->fw;
	return (*(uint32_t (**)(void *, void *, uint32_t))(*(char **)fw + off))(fw, a, b);
}

static void fw_put(void *p, uint32_t n)
{
	fw_call(FW_WRITE, p, n);
	fw_call(FW_FLUSH, 0, 0);
}

/* Posts act to the UI task on a message that is free, the other one first (the running one is released after it). */
static int post(uint8_t act)
{
	struct data *d = D;
	uint32_t i = d->which ^ 1u;
	struct msg *m;

	if (d->msg[i].busy)
		i ^= 1u;
	m = &d->msg[i];
	if (m->busy)
		return 0;
	d->which = (uint8_t)i;
	d->act = act;
	m->data = ALLOC(1);
	m->zero = 0;
	m->manager = MANAGER;
	m->callback = (uint32_t)rs_run;
	m->arg = 0;
	m->busy = 1;
	m->type = 6;
	POST(MQ_MAIN, m);
	return 1;
}

/* The page's RECORD on a take, or its periodic method when a take has ended: the name editor. */
void rs_ask_name(void)
{
	if (!D->saving)
		post(ACT_EDITOR);
}

static int exists(const char *path)
{
	uint32_t fh[4];
	if (FILE_OPEN(path, READ_MODE, fh))
		return 0;
	FILE_CLOSE(fh);
	return 1;
}

static void popup(const char *text)
{
	char tag[4];
	uint32_t s, *holder;
	void *pair[2];
	char *p;

	if (!VIEWS_UP)
		return;
	STRING(&s, text, tag);
	p = NEW(POPUP_SIZE);
	if (p) {
		POPUP(p, &s);
		holder = NEW(16);
		holder[0] = POPUP_HOLDER_VT;
		holder[1] = holder[2] = 1;
		holder[3] = (uint32_t)p;
		pair[0] = p;
		pair[1] = holder;
		PRESENT(TARGET(VIEWS()), pair, 0);
		DROP(&pair[1]);
	}
	STRING_DROP(&s);
}

/* The first free REC-nnn (001 to 999). */
static void free_name(void)
{
	struct data *d = D;
	char n[8] = "REC-000";

	for (uint32_t i = 1; i <= 999u; i++) {
		n[4] = (char)('0' + i / 100u);
		n[5] = (char)('0' + i / 10u % 10u);
		n[6] = (char)('0' + i % 10u);
		cat(d->path, DIR, n, sizeof d->path);
		if (!exists(d->path))
			break;
	}
	copy(d->name, n, sizeof d->name);
}

static void editor(void)
{
	struct data *d = D;
	char tag[3];
	uint32_t title, name, prompt;
	struct closure draw = {0, 0, MANAGER, (uint32_t)rs_no_draw}, save = {0, 0, MANAGER, (uint32_t)rs_named};
	void *e;

	if (!d->page || d->state != TAKEN)
		return;
	if (!d->exists)
		free_name();
	STRING(&title, d->exists ? "Name exists" : "Resample", &tag[0]);
	STRING(&name, d->name, &tag[1]);
	STRING(&prompt, "Save recording as", &tag[2]);
	draw.data = ALLOC(1);
	save.data = ALLOC(1);
	e = NEW(EDITOR_SIZE);
	if (e) {
		EDITOR(e, &title, &name, &prompt, 0, NAME_MAX, &draw, &save);
		PRESENT_VIEW(TARGET(VIEWS()), e, 0);
	}
	FREE_CLOSURE(&draw);
	FREE_CLOSURE(&save);
	STRING_DROP(&title);
	STRING_DROP(&name);
	STRING_DROP(&prompt);
}

/* The editor's save: its name, at most 12 characters, without the spaces after it; an empty one keeps the default. */
void rs_named(void *closure, char **name)
{
	struct data *d = D;
	char n[NAME_MAX + 1];
	int k = 0;

	(void)closure;
	for (const char *c = *name; c && *c && k < NAME_MAX; c++)
		n[k++] = *c;
	while (k && n[k - 1] == ' ')
		k--;
	n[k] = 0;
	if (k)
		copy(d->name, n, sizeof d->name);
	post(ACT_SAVE);
}

void rs_no_draw(void *closure, void *bitmap, int32_t x, int32_t y)
{
	(void)closure, (void)bitmap, (void)x, (void)y;
}

static uint32_t shift_of(uint32_t src)
{
	return D->shift[src < SRC_MAIN ? 0 : src - (SRC_MAIN - 1)];
}

/* The FileWriter closed: committed, or aborted (the file deleted). */
static void fw_end(int commit)
{
	struct data *d = D;

	fw_call(commit ? FW_COMMIT : FW_ABORT, 0, 0);
	FW_DTOR((void *)d->fw);
	DELETE((void *)d->fw);
	d->fw = 0;
	d->saving = 0;
}

/* The save's next step, or, should no message be free (the UI task runs and frees them, so never yet seen), the file
   given up: a SAVING page that never ends would keep the FileWriter, and the audio it mutes, forever. */
static void step(uint8_t act)
{
	if (post(act))
		return;
	fw_end(0);
	if (D->page)
		NEEDS_REDRAW((void *)D->page);
	popup("Save failed");
}

static void start(void)
{
	struct data *d = D;
	void *fw;

	cat(d->path, DIR, d->name, sizeof d->path);
	if (exists(d->path)) {                      /* nothing is overwritten: the editor again */
		d->exists = 1;
		post(ACT_EDITOR);
		return;
	}
	d->exists = 0;
	d->total = d->frames << (d->stereo ? 1 : 0);
	d->pos = 0;
	if (d->norm_set)
		rs_norm(d->peak, &d->sh, &d->gain);
	else {
		d->sh = 16u - shift_of(d->src);         /* as heard: full scale to 16-bit full scale */
		d->gain = 0;
	}
	fw = NEW(FW_SIZE);
	if (!fw) {
		popup("Save failed");
		return;
	}
	d->fw = (uint32_t)fw;
	d->saving = 1;
	FW_CTOR(fw, d->path, 64u + 2u * d->total + 16u);
	rs_header((uint8_t *)d->conv, d->frames, d->stereo);
	fw_put((void *)d->conv, 64);
	step(ACT_WRITE);
}

static void write(void)
{
	struct data *d = D;
	uint32_t n = d->total - d->pos;

	if (n > PIECE)
		n = PIECE;
	if (n) {
		rs_pcm16((uint8_t *)d->conv, WORDS(d->buf) + d->pos, n, d->sh, d->gain);
		fw_put((void *)d->conv, 2u * n);
		d->pos += n;
	}
	if (d->page)
		NEEDS_REDRAW((void *)d->page);
	step(d->pos < d->total ? ACT_WRITE : ACT_CLOSE);
}

static void finish(void)
{
	struct data *d = D;
	uint32_t *z = (uint32_t *)d->conv;
	int ok;
	char text[32];

	z[0] = z[1] = z[2] = z[3] = 0;
	fw_put(z, 16);
	ok = !(uint8_t)fw_call(FW_ERROR, 0, 0);
	fw_end(ok);
	if (!ok) {
		if (d->page)
			NEEDS_REDRAW((void *)d->page);
		popup("Save failed");
		return;
	}
	rs_release();
	if (d->page)
		(*(void (**)(void *))(*(char **)d->page + CLOSE_AT))((void *)d->page);
	cat(text, "Saved\n", d->name, sizeof text);
	popup(text);
}

/* The UI task's message: what was posted last. */
void rs_run(void *closure, uint32_t arg)
{
	(void)closure, (void)arg;
	rs_grid_back();                             /* the take has ended: GRID RECORDING as it was before */
	switch (D->act) {
	case ACT_EDITOR:
		editor();
		break;
	case ACT_SAVE:
		start();
		break;
	case ACT_WRITE:
		write();
		break;
	case ACT_CLOSE:
		finish();
		break;
	}
}
