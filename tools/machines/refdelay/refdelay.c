/* REFD: model27's reference effect for the delay slot (notes/68, step F1, §16). It proves the effect slots: the
 * mixer's call of the delay reaches it through the builder's dispatcher (tools/machines/fxslot/) when the pattern
 * has chosen it, with the stock effect's arguments, and its output is the slot's return. Never offered to users.
 *
 * A short echo: a line of 4 096 stereo frames (85 ms at 48 kHz), fed back with the slot's Fdbk. The line is the delay
 * slot's (notes/68 §16): the composer reserves it in the payload's variables for the slot's effects that ask for one,
 * shared since one plays at a time, and resolves fx_line, its address, as REFD's patch point; REFD asks for 32 768
 * bytes ("line" in its manifest). Each frame and channel:
 *
 *     d = line[pos];  out = d;  line[pos] = in + 2 g (d >> 8),  g = Fdbk >> 8 (0..127), saturated to 32 bits
 *
 * The arithmetic is exact and modelled bit for bit by tools/emu/test_fxslot.py (2 g (d >> 8) stays within 32 bits:
 * |d >> 8| <= 2^23 and 2 g <= 254). Time is not read: the echo's length is fixed.
 *
 * Contract (notes/68 §1.1, §2, §11): refd_process(out, in, params), called as the stock delay 0x40057488 is: out and
 * in are 32 stereo frames of 32 bits, L at +0 and R at +4; params is P + 428, Time at +0 and Fdbk at +2, 8.8 words.
 * refd_reset() empties the line, 32 KB, short enough for the block it runs in; the slot calls it when REFD is chosen,
 * so that neither an old echo nor another effect's use of the line comes back. The C ABI keeps d2-d7/a2-a6, as the
 * stock effect does; no EMAC.
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>

#define LEN 4096                            /* frames of the line, a power of two */

extern int32_t fx_line[];                   /* the slot's line: L and R interleaved, 2 * LEN words; zero at start-up */
#define line fx_line
static uint32_t pos;                        /* the next frame read and written */

static int32_t sat_add(int32_t a, int32_t b)
{
	int32_t s = (int32_t)((uint32_t)a + (uint32_t)b);
	if (((a ^ s) & (b ^ s)) < 0)
		s = a < 0 ? INT32_MIN : INT32_MAX;
	return s;
}

void refd_process(int32_t *out, const int32_t *in, const int16_t *params)
{
	int32_t g2 = 2 * (params[1] >> 8);      /* twice Fdbk, 0..254 */
	uint32_t p = pos;
	for (int f = 0; f < 32; f++) {
		for (int c = 0; c < 2; c++) {
			int32_t d = line[2 * p + c];
			out[2 * f + c] = d;
			line[2 * p + c] = sat_add(in[2 * f + c], (d >> 8) * g2);
		}
		p = (p + 1) & (LEN - 1);
	}
	pos = p;
}

void refd_reset(void)
{
	for (int i = 0; i < 2 * LEN; i++)
		line[i] = 0;
	pos = 0;
}
