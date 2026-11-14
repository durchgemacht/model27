/* The host test of Perform Kit's logic (perform.c compiled for the host with PK_HOST, its OS calls replaced by
 * host_os.h's stand-ins): the copies at the change, at the interface's kit selection and at mode off, the pool left
 * alone, two changes in a row, and SETTINGS + PATTERN. It does not run the OS's code; tools/emu/test_perform.py does.
 *
 *   cc -std=c99 -Wall -Wextra -Werror -DPK_HOST -o /tmp/test_perform test_perform.c && /tmp/test_perform
 *
 * License: MIT (LICENSE next to this file). */
#include <stdio.h>
#include <string.h>
#include "perform.c"

pk_t pk_data;
volatile uint8_t pk_held;
uint8_t host_kits[KITS * KIT_SIZE];
static uint8_t stock[KITS * KIT_SIZE];
uint8_t *host_play_kit;
uint32_t host_key_held, host_pattern, host_masked;
uint8_t host_project[256];
static uint32_t changed_n, changed_calls, audio_calls, masked_at_audio;
static uint8_t *changed_obj, *audio_kit;
static int failed, checks;

static uint32_t temp_calls, temp_seen[8], temp_own;
static int own(uint32_t n);

uint32_t host_temp_save(uint8_t *project, uint32_t temp, uint32_t n)
{
	if (project == host_project && temp == 1 && temp_calls < 8) {
		temp_seen[temp_calls] = n;
		temp_own += (uint32_t)own(n);               /* saved with its own bytes */
	}
	temp_calls++;
	return 1;
}

uint8_t *pk_ser_c(uint8_t *kit);
void pk_ksave_c(uint32_t n, uint32_t slot);
void pk_loaded_c(uint32_t n, uint32_t slot, uint32_t ok);
void pk_off_c(void);
void pk_drop_c(void);
void pk_change_c(uint8_t *kit);
void pk_ui_c(void);
void pk_toggle(void);
uint32_t pk_pattern_c(void *event);

void host_kit_changed(uint8_t *obj, uint32_t n, uint32_t info)
{
	(void)info;
	changed_obj = obj;
	changed_n = n;
	changed_calls++;
}

void host_audio_kit(uint8_t *kit)
{
	audio_kit = kit;
	audio_calls++;
	masked_at_audio = host_masked;
}

#define CHECK(c, what) do { checks++; if (!(c)) { failed++; printf("FAIL %s (line %d)\n", what, __LINE__); } } while (0)

static void reset(void)
{
	uint32_t i;

	for (i = 0; i < sizeof host_kits; i++)
		host_kits[i] = (uint8_t)(i * 2654435761u >> 13);
	memcpy(stock, host_kits, sizeof stock);
	memset(&pk_data, 0, sizeof pk_data);
	pk_held = 0;
	host_key_held = host_pattern = host_masked = 0;
	changed_calls = audio_calls = temp_calls = temp_own = 0;
	host_play_kit = KIT(0);
}

static int head_is(uint32_t n, const uint8_t *bytes) { return !memcmp(KIT(n), bytes, HEAD); }
static int own(uint32_t n) { return !memcmp(KIT(n), stock + KIT_SIZE * n, KIT_SIZE); }
static int pool_own(uint32_t n) { return !memcmp(KIT(n) + HEAD, stock + KIT_SIZE * n + HEAD, KIT_SIZE - HEAD); }

static void tweak(uint32_t n, uint32_t at, uint8_t v) { KIT(n)[at] = v; }

int main(void)
{
	uint8_t t[HEAD];
	uint8_t *z;
	uint32_t n;
	host_event press = {{0}, 3, 1}, repeat = {{0}, 3, 9}, release = {{0}, 3, 0};

	/* 1. the mode off: nothing is copied */
	reset();
	pk_change_c(KIT(5));
	pk_ui_c();
	for (n = 0; n < KITS; n++)
		CHECK(own(n), "off: every kit as it was");

	/* 2. on in pattern 3, tweaked, a change to 5 */
	reset();
	host_pattern = 3;
	pk_toggle();
	CHECK(pk_data.on && pk_data.home == 3 && !pk_data.left1, "on: home is the playing pattern");
	CHECK(own(3), "on: the kit is not written");
	tweak(3, 40, 0xa5); tweak(3, 0, 0x11); tweak(3, 693, 0x5a);
	memcpy(t, KIT(3), HEAD);
	pk_change_c(KIT(5));
	CHECK(head_is(5, t), "change: the tweaked bytes in the new pattern's kit");
	CHECK(pool_own(5) && pool_own(3), "change: the pools untouched");
	CHECK(head_is(3, t), "change: the pattern left keeps the tweaked bytes until the interface left it");
	CHECK(pk_data.home == 5 && pk_data.left1 == 4, "change: home 5, pattern 3 to give back");
	tweak(3, 100, 0x77);                            /* a knob, still on the kit left */
	t[100] = 0x77;
	pk_ui_c();
	CHECK(head_is(5, t), "interface: the late knob step reaches the new kit");
	CHECK(own(3), "interface: the pattern left has its own bytes");
	CHECK(!pk_data.left1 && !host_masked, "interface: nothing left to give back, the interrupts as before");
	pk_ui_c();
	CHECK(head_is(5, t) && own(3), "interface: a second call changes nothing");

	/* 3. on to 7 without the interface in between, then 9 */
	pk_change_c(KIT(7));
	pk_change_c(KIT(9));
	CHECK(own(5), "two changes: the first pattern left has its own bytes");
	CHECK(head_is(7, t) && pool_own(7), "two changes: the second keeps the tweaked bytes until the interface left it");
	CHECK(head_is(9, t) && pool_own(9), "two changes: the tweaked bytes in the last kit");
	pk_ui_c();
	CHECK(own(7) && head_is(9, t), "two changes: the interface afterwards");

	/* 4. back and forth before the interface ran */
	pk_change_c(KIT(2));
	pk_change_c(KIT(9));
	CHECK(head_is(2, t) && pool_own(2) && head_is(9, t) && pool_own(9), "there and back: the tweaked bytes in both");
	pk_ui_c();
	CHECK(own(2) && head_is(9, t), "there and back: the interface afterwards");

	/* 5. the same kit again, a pointer that is no kit */
	pk_change_c(KIT(9));
	pk_change_c(KIT(9) + 2);
	pk_change_c(host_kits - 4);
	pk_change_c(KIT(95) + KIT_SIZE);
	CHECK(pk_data.home == 9 && !pk_data.left1 && head_is(9, t), "no change: nothing moves");

	/* 6. mode off: the active pattern's own bytes, the audio side and the interface told */
	host_play_kit = KIT(9);
	pk_toggle();
	CHECK(!pk_data.on, "off: the mode");
	for (n = 0; n < KITS; n++)
		CHECK(own(n), "off: every kit has its own bytes");
	CHECK(audio_calls == 1 && audio_kit == KIT(9) && masked_at_audio, "off: the audio side's caches cleared, masked");
	CHECK(changed_calls == 1 && changed_obj == host_project + 116 && changed_n == 9, "off: the kit's change notice");
	CHECK(!host_masked, "off: the interrupts as before");

	/* 7. off with a pattern still to give back */
	reset();
	host_pattern = 1;
	pk_toggle();
	tweak(1, 300, 0x42);
	pk_change_c(KIT(4));
	pk_toggle();
	for (n = 0; n < KITS; n++)
		CHECK(own(n), "off before the interface ran: every kit has its own bytes");
	CHECK(changed_n == 4, "off before the interface ran: the notice names the active pattern");

	/* 8. SETTINGS + PATTERN */
	reset();
	CHECK(!pk_pattern_c(&press) && !pk_data.on, "PATTERN alone: not taken");
	CHECK(!pk_pattern_c(&release), "PATTERN's release alone: not taken");
	host_key_held = 1;
	CHECK(!pk_pattern_c(&repeat) && !pk_data.on, "a repeat with SETTINGS held: not a press");
	CHECK(pk_pattern_c(&press) && pk_data.on && pk_data.taken, "SETTINGS + PATTERN: on, taken");
	host_key_held = 0;                              /* SETTINGS let go first */
	CHECK(pk_pattern_c(&repeat) && pk_data.on, "the taken press's repeat: taken, no second toggle");
	CHECK(pk_pattern_c(&release) && !pk_data.taken, "its release: taken");
	CHECK(!pk_pattern_c(&press) && pk_data.on, "PATTERN alone afterwards: stock");
	CHECK(!pk_pattern_c(&release), "its release: stock");
	pk_held = 1;                                    /* SETTINGS by its events only */
	CHECK(pk_pattern_c(&press) && !pk_data.on, "SETTINGS by its last event + PATTERN: off");
	CHECK(pk_pattern_c(&release), "its release: taken");

	/* 9. the serializer: the pattern's own bytes for home and for the pattern left */
	reset();
	CHECK(pk_ser_c(KIT(3)) == KIT(3), "serializer, the mode off: the kit itself");
	host_pattern = 3;
	pk_toggle();
	tweak(3, 60, 0x99); tweak(3, 692, 0x33);
	memcpy(t, KIT(3), HEAD);
	z = pk_ser_c(KIT(3));
	CHECK(z == pk_data.big && !memcmp(z, stock + KIT_SIZE * 3, KIT_SIZE), "serializer: home's kit as it was before the mode");
	CHECK(head_is(3, t), "serializer: the kit itself still tweaked");
	CHECK(pk_ser_c(KIT(4)) == KIT(4), "serializer: another pattern's kit itself");
	KIT(3)[HEAD + 10] ^= 0xff;                      /* a sound lock's sound edited: the pool is the pattern's */
	z = pk_ser_c(KIT(3));
	CHECK(!memcmp(z, stock + KIT_SIZE * 3, HEAD) && !memcmp(z + HEAD, KIT(3) + HEAD, KIT_SIZE - HEAD),
	      "serializer: the pool as it is now, the rest the pattern's own");
	KIT(3)[HEAD + 10] ^= 0xff;
	pk_change_c(KIT(8));
	z = pk_ser_c(KIT(3));
	CHECK(z == pk_data.big && !memcmp(z, stock + KIT_SIZE * 3, KIT_SIZE), "serializer: the pattern left, its own bytes");
	z = pk_ser_c(KIT(8));
	CHECK(z == pk_data.big && !memcmp(z, stock + KIT_SIZE * 8, KIT_SIZE), "serializer: the new home, its own bytes");
	pk_ui_c();
	CHECK(pk_ser_c(KIT(3)) == KIT(3) && !host_masked, "serializer: the pattern given back, the kit itself");

	/* 10. a temp save, then Save Pattern */
	pk_ksave_c(8, 96);
	CHECK((pk_data.temp[1] & 1) && !memcmp(pk_ser_c(KIT(8)), stock + KIT_SIZE * 8, KIT_SIZE),
	      "temp save: the pattern noted, its own bytes not changed");
	pk_ksave_c(5, 96); pk_ksave_c(5, 2);
	CHECK(!(pk_data.temp[0] & 0x20), "a save of another pattern: nothing");
	pk_ksave_c(8, 2);
	CHECK(!memcmp(pk_ser_c(KIT(8)), KIT(8), KIT_SIZE) && head_is(8, t), "Save Pattern: the tweaked bytes are the pattern's own");
	pk_toggle();
	CHECK(head_is(8, t) && own(3), "Save Pattern, then off: the saved pattern keeps the tweaked bytes");
	CHECK(temp_calls == 1 && temp_seen[0] == 8, "off: the temp-saved pattern's kit saved to the temp slot again");
	CHECK(!pk_data.temp[1], "off: nothing noted any more");

	/* 11. temp-saved inside the mode in two patterns, off: both saved again with their own bytes */
	reset();
	host_pattern = 1;
	pk_toggle();
	tweak(1, 77, 0x10);
	pk_ksave_c(1, 96);
	pk_change_c(KIT(2));
	pk_ui_c();
	pk_ksave_c(2, 96);
	pk_change_c(KIT(6));
	pk_toggle();
	CHECK(temp_calls == 2 && temp_seen[0] == 1 && temp_seen[1] == 2 && temp_own == 2,
	      "off: both patterns' kits saved to the temp slot with their own bytes");
	for (n = 0; n < KITS; n++)
		CHECK(own(n), "off: every kit has its own bytes");

	/* 12. Reload Pattern, a temp reload, a load that failed */
	reset();
	host_pattern = 4;
	pk_toggle();
	tweak(4, 30, 0x66);
	memset(KIT(4), 0xee, HEAD);                     /* the loader wrote the kit */
	pk_loaded_c(4, 96, 1);
	CHECK(!memcmp(pk_ser_c(KIT(4)), stock + KIT_SIZE * 4, HEAD), "a temp reload: the pattern's own bytes stay");
	pk_loaded_c(4, 2, 0);
	CHECK(!memcmp(pk_ser_c(KIT(4)), stock + KIT_SIZE * 4, HEAD), "a load that failed: the pattern's own bytes stay");
	pk_loaded_c(7, 2, 1);
	CHECK(!memcmp(pk_ser_c(KIT(4)), stock + KIT_SIZE * 4, HEAD), "another pattern reloaded: nothing");
	pk_loaded_c(4, 2, 1);
	CHECK(!memcmp(pk_ser_c(KIT(4)), KIT(4), KIT_SIZE), "Reload Pattern: the loaded bytes are the pattern's own");
	pk_toggle();
	CHECK(KIT(4)[0] == 0xee && KIT(4)[693] == 0xee, "Reload Pattern, then off: the loaded kit stays");

	/* 13. paste or clear: the mode off first; another project: dropped, no kit written */
	reset();
	pk_off_c();
	CHECK(!audio_calls && !changed_calls, "pk_off_c with the mode off: nothing");
	host_pattern = 2;
	pk_toggle();
	tweak(2, 500, 0x01);
	pk_off_c();
	CHECK(!pk_data.on && own(2) && audio_calls == 1 && changed_calls == 1, "pk_off_c: the mode off, the own bytes back");
	pk_toggle();
	tweak(2, 500, 0x01);
	memcpy(t, KIT(2), HEAD);
	pk_ksave_c(2, 96);
	pk_change_c(KIT(3));
	audio_calls = changed_calls = temp_calls = 0;
	pk_drop_c();
	CHECK(!pk_data.on && !pk_data.left1 && !pk_data.temp[0], "another project: the mode dropped");
	CHECK(head_is(2, t) && head_is(3, t) && !audio_calls && !changed_calls && !temp_calls,
	      "another project: no kit written, nothing called");
	CHECK(pk_ser_c(KIT(3)) == KIT(3), "another project: the serializer gets the kits themselves");

	printf("%s, %d checks\n", failed ? "FAILED" : "ALL OK", checks);
	return failed != 0;
}
