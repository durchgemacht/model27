/* Samples: the Model:Samples' filter on every track whose sound chose it (the track filters, notes/72,
 * §13), filter id 1 of the builder's filter slot (tools/machines/fltslot/). It is SAMPLE's filter as it is: Cycles
 * One-Shot's src/smp_filter.c, smp_filter_cf.S and smp_filter_tab.c, compiled from SAMPLE's package
 * (tools/machines/sampler/src/, the same files as the One-Shot commit its manifest names), whose header tells its
 * laws: a 2-pole lowpass below the centre of Cutoff, a highpass above it, nothing at the centre, the resonance on
 * Reso, measured on the Model:Samples OS 1.13 and rebuilt with model27's own formulas.
 *
 * Here it runs after Volume + Dist, once per track and block, on the track's smoothed k 28 (Cutoff) and k 29 (Reso):
 * p-locks, the LFO and the velocity move it as they move any parameter. One state per track, in this package's
 * variables, cleared at boot (mode off) and by smpf_reset when the track comes to this filter. Every block the knob
 * words set the block's targets and the block is filtered in place; the filter glides from the last block's targets,
 * so the knob, a p-lock or an LFO can cross the centre or jump sides without a click, and at the centre the block
 * passes untouched, bit for bit, once the dry/wet weight has glided to 0. The frame loop is the EMAC's in fractional,
 * saturating mode; it sets MACSR itself and gives it back. k 30 and k 31 are not read (Env depth and AD come later,
 * under the same id). The trig bit is not read either.
 *
 * Two savings (since 0.2, the load on the machine with six filters): smp_filter_set is skipped while the words are
 * those of the last block and the filter has settled on them (no glide left in its coefficients or weights): it
 * would write the same fields again, so the output is the same bit for bit. And a silent block (all 32 frames 0) is
 * not run once the filter has rung out (smp_filter_ringing: its states below 2^-17 of full scale, -102 dB): the
 * states are cleared and the block stays silent, where the filter would have given values under that level. A filter
 * that has just started (prime) starts from the first block that is not silent.
 *
 * Contract (fltslot.c): smpf_process(block, words, track, triggered), block 32 frames of 32 bits filtered in place,
 * words the track's smoothed k 28..31; smpf_reset(track). C ABI.
 *
 * License: MIT (LICENSE next to this file). */
#include <stdint.h>
#include "smp_filter.h"

#define TRACKS 6

struct track {
	smp_filter f;
	int16_t cutoff, reso;                       /* the words of the last smp_filter_set */
	uint8_t set;                                /* 0 after a reset: the next block sets */
};

static struct track state[TRACKS];

static int settled(const smp_filter *f)
{
	return !f->df2 && !f->dq2 && !f->dwet && !f->dmix && f->f2 == f->f2t && f->q2 == f->q2t && f->wet == f->wett
	       && f->mix == f->mixt;
}

void smpf_reset(uint32_t track)
{
	if (track < TRACKS) {
		smp_filter_reset(&state[track].f);
		state[track].set = 0;
	}
}

void smpf_process(int32_t *block, const int16_t *words, uint32_t track, uint32_t triggered)
{
	struct track *s;
	int32_t any = 0;
	(void)triggered;
	if (track >= TRACKS)
		return;
	s = &state[track];
	if (!s->set || words[0] != s->cutoff || words[1] != s->reso || !settled(&s->f)) {
		smp_filter_set(&s->f, words[0], words[1]);
		s->cutoff = words[0];
		s->reso = words[1];
		s->set = 1;
	}
	for (int n = 0; n < SMP_FILTER_BLOCK; n++)
		any |= block[n];
	if (!any && !smp_filter_ringing(&s->f)) {   /* silent, and the filter has rung out */
		s->f.l = s->f.b = 0;
		return;
	}
	smp_filter_run(&s->f, block);
}
