/* REFR: model27's reference effect for the reverb slot (notes/68, step F1). It proves the effect slots on the
 * reverb's call as REFD does on the delay's: reached through the builder's dispatcher (tools/machines/fxslot/) when
 * the device has chosen it, with the stock effect's arguments, its output the slot's return. Never offered to users.
 *
 * Not a reverb: a one-pole low-pass per channel whose speed follows the slot's Size. Each frame and channel:
 *
 *     y += ((in >> 1) - (y >> 1)) >> (s - 1),  out = y,  s = 1 + (Size >> 4) (1..8)
 *
 * The arithmetic is exact and modelled bit for bit by tools/emu/test_fxslot.py (in >> 1 and y >> 1 lie within
 * -2^30..2^30 - 1, so their difference and y + it stay within 32 bits). Tone is not read.
 *
 * Contract (notes/68 §1.1, §2, §11): refr_process(out, in, params), called as the stock reverb 0x400579c4 is: out
 * and in are 32 stereo frames of 32 bits, L at +0 and R at +4; params is P + 432: Size's integer part in the byte at
 * +0 (0..127, the byte the stock reverb reads), Tone at +2. refr_reset() clears the filter; the slot calls it when
 * the device chooses REFR. The C ABI keeps d2-d7/a2-a6, as the stock effect does; no EMAC.
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>

static int32_t y[2];                        /* L, R; the boot hook zeroes the payload's variables */

void refr_process(int32_t *out, const int32_t *in, const int8_t *params)
{
	int k = (params[0] & 0x7f) >> 4;        /* s - 1, 0..7 */
	for (int f = 0; f < 32; f++) {
		for (int c = 0; c < 2; c++) {
			int32_t v = y[c];
			v += ((in[2 * f + c] >> 1) - (v >> 1)) >> k;
			y[c] = v;
			out[2 * f + c] = v;
		}
	}
}

void refr_reset(void)
{
	y[0] = y[1] = 0;
}
