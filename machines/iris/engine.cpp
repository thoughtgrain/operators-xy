/* iris for the OP-XY: four waveforms at one pitch, laid side by side like the bands of a rainbow. A mixing window
 * slides along them (Morph) and opens to let the neighbours bleed in (Overlap); Spread detunes the bands from each
 * other so they beat. Named for Iris, the goddess of the rainbow.
 *
 * Signal path per voice: four oscillators (sine, triangle, square, saw, in order of harmonic content) -> weighted
 * mix -> 2-pole state-variable low-pass -> output. The OP-XY's own envelope, filter and effects come after.
 *
 * The page                                       The Shift row (Shift + encoder)
 *   Morph    window centre: sine .. tri .. square .. saw     Skew   one breakpoint for sine, triangle and square
 *   Overlap  window width: two neighbours .. all four        Phase  each band's phase offset from the one before
 *   Spread   band detune, outer bands +-50 cents             (encoders 3 and 4 have nothing on the row)
 *   Tone     low-pass that follows the note: from 1.4x the note (almost a sine) to 128x (open)
 *
 * The mix. The bands sit at positions 0..3 and Morph puts the window's centre anywhere between them. Each band's
 * weight is a triangle kernel, 1 - distance / width, with width 1 band at Overlap 0 (a plain crossfade between the
 * two nearest bands, so Morph is a smooth scan) up to 4 bands at Overlap 100 (all four sound, the far ones at a
 * quarter). The weights are renormalised to sum to one every block, so opening Overlap thickens the sound without
 * making it louder, and ramped across the block so turning Morph doesn't zipper.
 *
 * Skew moves one breakpoint from half a cycle down to 5 %: the sine and triangle run their first half faster (a
 * phase-distortion lean toward a ramp), the square becomes a narrowing pulse. The saw has no breakpoint to move.
 * Each band's DC from the warp is known exactly (2b - 1 times the half-wave's mean), so it's subtracted per band
 * rather than with a high-pass that would thump on a note start.
 * Phase offsets band i by i eighth-cycles times the setting, so it only matters where bands overlap: there it
 * hollows some harmonics and reinforces others (harmonic n of band i moves by n x 45 degrees). An eighth, not a
 * quarter: quarter steps cancel the fundamental of four equal bands outright. All four bands start in phase on
 * every note, so at the defaults nothing cancels.
 *
 * The bands are trimmed to a similar loudness (sine 0.82, square 0.6, triangle and saw 1.0), so Morph changes
 * the colour, not the level.
 *
 * Tone follows the note: the low-pass sits a set number of octaves above the fundamental (0.5 .. 7.5), so it means
 * "how many harmonics get through" at every pitch, which is what the four bands differ in.
 *
 * Square and saw are band-limited with a polynomial BLEP at each jump; sine and triangle have no jumps to fix.
 * Integers only. Divisions happen once per block (weights, the BLEP reciprocal, the skew slopes), never per sample.
 * Copyright (c) 2026 briannhinton. MIT. */
#include "core.h"
#include <opxy/q31.hpp>

namespace iris {
namespace {
using opxy::i32;
using opxy::u32;
using opxy::i64;
typedef unsigned long long u64;

const i32 F_MIN = 300, F_MAX = 29491;   // cutoff coefficient range, Q15 (as toro)
const i32 DAMP = 23170;                 // sqrt(2) in Q14: Butterworth, no resonant peak
const i32 F_CAP = F_MAX - (((DAMP - 2768) * 5764) >> 15);   // Chamberlin stability at that damping
const i32 STATE = 60000;                // filter state clamp: keeps every product below 2^31

inline i32 clampv(i32 v, i32 lim) { return v > lim ? lim : (v < -lim ? -lim : v); }
inline i32 k15(i32 q31) { return q31 < 0 ? 0 : q31 >> 16; }   // a control word as 0..32767

// note frequency as a filter coefficient (2 pi f / fs, Q15) raised by x Q12 octaves (0 .. 7.5)
inline i32 track(u32 inc, i32 x)
{
    const i32 f_note = static_cast<i32>((static_cast<u64>(inc) * 205887u) >> 32);   // 2 pi * 32768
    const i32 n = x >> 12, f = x & 4095;
    const i32 m = 4096 + ((f * (2689 + ((f * 1407) >> 12))) >> 12);
    const i64 c = ((static_cast<i64>(f_note) * m) << n) >> 12;
    return c > F_CAP ? F_CAP : (c < F_MIN ? F_MIN : static_cast<i32>(c));
}
// 2^(x / 4096) as Q12, x in Q12 octaves (-4 .. +4): whole octaves by shift, the fraction by a quadratic
inline i32 exp2q(i32 x)
{
    if (x > 4 * 4096) x = 4 * 4096; else if (x < -4 * 4096) x = -4 * 4096;
    const i32 n = x >> 12, f = x & 4095;
    const i32 m = 4096 + ((f * (2689 + ((f * 1407) >> 12))) >> 12);
    return n >= 0 ? m << n : m >> -n;
}

/* The breakpoint warp behind Skew: phase [0, bp) maps to the first half cycle, [bp, 2^32) to the second. */
struct Warp { u32 bp; u64 r1, r2; };
inline u32 warp(u32 p, const Warp& w)
{
    if (p < w.bp) return static_cast<u32>((static_cast<u64>(p) * w.r1) >> 16);
    return 0x80000000u + static_cast<u32>((static_cast<u64>(p - w.bp) * w.r2) >> 16);
}

// Sine from a parabola with one correction step (error under 0.1 %), Q15, rising through zero at phase 0
inline i32 sine(u32 ph)
{
    const i32 a = static_cast<i32>(ph) >> 16;                       // -32768 .. 32767 over one cycle
    i32 y = ((a * (32768 - (a < 0 ? -a : a))) >> 13);               // 4 a (1 - |a|)
    y = clampv(y, 32767);
    return ((y * 25395) >> 15) + ((((y * (y < 0 ? -y : y)) >> 15) * 7373) >> 15);   // 0.775 y + 0.225 y|y|
}
// Triangle, Q15, rising through zero at phase 0, peak at a quarter
inline i32 tri(u32 ph)
{
    const i32 s = static_cast<i32>(ph + 0x40000000u) >> 16;
    return clampv(((s < 0 ? -s : s) << 1) - 32768, 32767);
}
/* Polynomial BLEP for a jump at t = 0 (t is the phase since the jump). x = t / inc as Q15 via the block's
 * reciprocal, so there's no division here. Returns the correction for a unit (half-height) step, Q15. */
inline i32 blep(u32 t, u32 inc, u64 rcp)
{
    if (t < inc) {
        const i32 x = static_cast<i32>((static_cast<u64>(t) * rcp) >> 32);
        return x + x - ((x * x) >> 15) - 32768;                     // 2x - x^2 - 1
    }
    const u32 back = 0u - t;                                        // phase until the next jump
    if (back < inc) {
        const i32 x = -static_cast<i32>((static_cast<u64>(back) * rcp) >> 32);
        return ((x * x) >> 15) + x + x + 32768;                     // x^2 + 2x + 1
    }
    return 0;
}
}

inline void initialize(Voice& v, Shared&, u32)
{
    for (int i = 0; i < 4; i++) { v.ph[i] = 0; v.g[i] = 0; }
    v.low = 0; v.band = 0; v.f_last = 0;
}
inline void start(Voice& v, Shared& s, u32 owner) { initialize(v, s, owner); }   // every band in phase
inline void destroy(Voice&, Shared&, u32) {}

/* p[0..3] are the page (morph, overlap, spread, tone) and p[4..5] the Shift row (skew, phase), in definition order:
 * parameters, then synth_shift. */
inline void render(Voice& v, Shared&, u32, opxy::Output out, opxy::Parameters p, opxy::Pitch inc)
{
    // Mix weights: triangle kernel of width 1 .. 4 bands round the Morph position, renormalised to sum to 1
    const i32 centre = k15(p[0]) * 3;                       // Q15 band positions, 0 .. 3
    const i32 width = 32768 + k15(p[1]) * 3;                // Q15 bands, 1 .. 4
    i32 g1[4], sum = 0;
    for (int i = 0; i < 4; i++) {
        i32 d = centre - i * 32768; if (d < 0) d = -d;
        const i32 k = 32768 - static_cast<i32>((static_cast<i64>(d) << 15) / width);
        g1[i] = k > 0 ? k : 0;
        sum += g1[i];
    }
    for (int i = 0; i < 4; i++) g1[i] = static_cast<i32>((static_cast<i64>(g1[i]) << 15) / sum);   // sum >= 1/2

    // Spread: band i is detuned by (2i - 3) / 3 x 50 cents x setting, as a Q12 multiplier minus one
    const i32 spread = k15(p[2]);
    i32 det[4];
    for (int i = 0; i < 4; i++) det[i] = exp2q(((2 * i - 3) * spread * 57) >> 15) - 4096;

    // Skew: the breakpoint goes from half a cycle (no warp) down to 5 %
    Warp w;
    w.bp = 0x80000000u - static_cast<u32>((static_cast<i64>(k15(p[4])) * 1932735283LL) >> 15);
    w.r1 = (static_cast<u64>(1) << 47) / w.bp;
    w.r2 = (static_cast<u64>(1) << 47) / (0u - w.bp);
    const i32 e = static_cast<i32>(w.bp - 0x80000000u) >> 16;    // 2b - 1, Q15, -0.9 .. 0
    const i32 dc0 = (e * 20861) >> 15, dc1 = e >> 1, dc2 = e;    // the warp's DC: x 2/pi (sine), 1/2 (tri), 1 (pulse)
    const u32 phoff = static_cast<u32>(k15(p[5])) << 14;    // up to an eighth of a cycle between neighbours

    const i32 f1 = track(inc[0], 2048 + ((k15(p[3]) * 7) >> 3));
    const bool fresh = v.f_last == 0;
    const i32 f0 = fresh ? f1 : v.f_last;
    const i32 fstep = (f1 - f0) >> 6;                       // ramp the cutoff over the 64-sample block
    i32 gs[4], gst[4];
    for (int i = 0; i < 4; i++) { gs[i] = fresh ? g1[i] : v.g[i]; gst[i] = (g1[i] - gs[i]) >> 6; }
    const u64 rcp = inc[0] > 1u ? (static_cast<u64>(1) << 47) / inc[0] : 0;

    i32 f = f0, low = v.low, band = v.band;
    u32 ph0 = v.ph[0], ph1 = v.ph[1], ph2 = v.ph[2], ph3 = v.ph[3];
    for (unsigned n = 0; n < opxy::block_frames; n++) {
        const u32 i = inc[n], is = static_cast<u32>(static_cast<i32>(i >> 12));
        ph0 += i + is * static_cast<u32>(det[0]);
        ph1 += i + is * static_cast<u32>(det[1]);
        ph2 += i + is * static_cast<u32>(det[2]);
        ph3 += i + is * static_cast<u32>(det[3]);
        const u32 q1 = ph1 + phoff, q2 = ph2 + phoff * 2u, q3 = ph3 + phoff * 3u;

        const i32 b0 = (sine(warp(ph0, w)) - dc0) * 26755 >> 15;            // trimmed x 0.82
        const i32 b1 = tri(warp(q1, w)) - dc1;
        i32 b2 = q2 < w.bp ? 32767 : -32767;                // pulse: high until the breakpoint
        b2 += blep(q2, i, rcp) - blep(q2 - w.bp, i, rcp);
        b2 = (clampv(b2, 32767) - dc2) * 19661 >> 15;                         // trimmed x 0.6
        const u32 t3 = q3 + 0x80000000u;                     // saw jumps down at half a cycle
        const i32 b3 = clampv((static_cast<i32>(q3) >> 16) - blep(t3, i, rcp), 32767);

        i32 x = (gs[0] * clampv(b0, 32767) + gs[1] * clampv(b1, 32767) + gs[2] * clampv(b2, 32767) + gs[3] * b3) >> 15;
        x = clampv(x, 32767);
        for (int k = 0; k < 4; k++) gs[k] += gst[k];

        low = clampv(low + ((f * band) >> 15), STATE);
        const i32 high = clampv(x - low - ((DAMP * band) >> 14), 65535);
        band = clampv(band + ((f * (high >> 1)) >> 14), STATE);
        f += fstep;
        const i32 y = (clampv(low, 32767) * 3) >> 2;
        out[n] = y << 15;                                    // Q15 -> Q31 at half scale (|y| <= 24575)
    }
    v.ph[0] = ph0; v.ph[1] = ph1; v.ph[2] = ph2; v.ph[3] = ph3;
    for (int k = 0; k < 4; k++) v.g[k] = g1[k];
    v.low = low; v.band = band; v.f_last = f1;
}
}
