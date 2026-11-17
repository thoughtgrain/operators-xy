/* iris for the OP-XY: the rainbow screen. Four grey bands are the four waveforms that go in (sine outermost, then
 * triangle, square, saw innermost, as a real bow orders its wavelengths) and the one bright line is what comes out:
 * the mix, computed from the engine's own maths, riding at the radius Morph sets.
 *   Morph    the bright line walks inward across the bow, sine band to saw band, and takes that band's shape
 *   Overlap  the bands pull in toward the bright line; at 100 they crowd it and their waves cross
 *   Spread   each band's cycles stretch or shrink along its arc, so crests fall out of line, and the bright line
 *            swells and thins round the bow where the detuned bands beat
 *   Tone     the bright line's corners round off, and band by band from the inside the teeth melt into humps
 *   Skew     (Shift + encoder 1) the bright line leans; on the square it narrows to spikes
 *   Phase    (Shift + encoder 2) the bands slide along their arcs, band i by i/8 of a cycle; the bright line hollows
 *            where bands overlap
 *   Shift    held: the header's four slots show skew and phase (encoders 3 and 4 have nothing on the row); nothing
 *            below the header moves. Shift replaces the header's contents, it never adds a row
 *   a note   the bright line brightens and travels along the arc while any note is held, then settles
 *
 * The design and its frames live in operator-design, screens/iris (handoff.md is the spec this follows). The art is
 * retained (panel.svg.fragment from gen_panel.py, indices in nodes.h). The bands are chains of one-cycle nodes that
 * only move, turn and scale; the bright line is the four mutable outlines, rewritten only when its key changes, so
 * nothing redraws at rest. Integer maths only, Q10 throughout. Copyright (c) 2026 briannhinton. MIT. */
#include "display.h"
#include "nodes.h"
#include <opxy/q31.hpp>
#include <opxy/synth_shift.hpp>

namespace iris {
namespace {
using opxy::i32;
using opxy::i64;
using opxy::u32;
using namespace opxy::draw;
typedef unsigned long long u64;

const i32 NH = 12;                                   /* harmonics the mix line can carry (it resolves ~5) */
const i32 HALF_TURN = 1800;                          /* tenths of a degree */

inline i32 q10(i32 q31) { return q31 < 0 ? 0 : q31 >> 21; }
inline i32 iabs(i32 v) { return v < 0 ? -v : v; }
inline i32 expneg(i32 x)                             /* e^-x, x Q10 >= 0, -> Q10 (as toro) */
{
    if (x <= 0) return unit;
    const i32 y = static_cast<i32>((static_cast<u32>(x) * 1477u) >> 10), n = y >> 10;
    if (n >= 10) return 0;
    const i32 t = (y & 1023), t2 = (t * t) >> 10, t3 = (t2 * t) >> 10;
    return (unit - ((t * 709) >> 10) + ((t2 * 246) >> 10) - ((t3 * 57) >> 10)) >> n;
}
inline u32 isqrt64(u64 v)
{
    u64 r = 0, b = static_cast<u64>(1) << 62;
    while (b > v) b >>= 2;
    while (b) { if (v >= r + b) { v -= r + b; r = (r >> 1) + b; } else r >>= 1; b >>= 2; }
    return static_cast<u32>(r);
}
inline i32 exp2_q10(i32 x)                           /* 2^(x / 1024), x Q10 >= 0, -> Q10 */
{
    const i32 n = x >> 10, f = x & 1023;
    const i32 m = 1024 + ((f * (672 + ((f * 352) >> 10))) >> 10);
    return m << n;
}
inline i32 lerp_band(const int* v, i32 c)            /* v at band position c (Q10, 0 .. 3), v in any unit */
{
    i32 i = c >> 10; if (i > 2) i = 2;
    const i32 f = c - (i << 10);
    return v[i] + static_cast<i32>((static_cast<i64>(v[i + 1] - v[i]) * f) >> 10);
}
/* Skew's breakpoint warp on a phase (Q10 cycles, 0 .. 1023): [0, b) -> first half, [b, 1) -> second. b Q10. */
inline i32 warp(i32 t, i32 b)
{
    return t < b ? (t * 512) / b : 512 + ((t - b) * 512) / (unit - b);
}
inline u32 mix_key(const i32* e, i32 travel)
{
    u32 h = 2166136261u;
    for (int k = 0; k < 6; ++k) { h ^= static_cast<u32>(e[k]); h *= 16777619u; }
    h ^= static_cast<u32>(travel >> 2); h *= 16777619u;
    return h | 1u;                                    /* never 0: a frame needs a nonzero key */
}
}

inline void display_reset(DisplayState& st)
{
    st.header.reset();
    for (int k = 0; k < 6; ++k) st.eased[k] = 0;
    st.travel = 0; st.speed = 0; st.key = 0; st.initialized = 0;
}

inline void display(DisplayState& st, const Input& in, Frame& fr)
{
    /* header: one row. While Shift is held its four slots show the Shift row (skew, phase, then nothing) in place of
     * the page's titles and values; release puts the page back. We pass the Shift row's captions to page_header
     * ourselves rather than passing the row, which would stack it under the page (operator-design constraints.md,
     * Shift in the header). The Shift row's values come from synth_shift.hpp; the engine reads them after the four
     * page parameters. */
    const auto row = shift_row(in);
    const opxy::i32 shift_word[2] = { row.values[0], row.values[1] };              /* skew, phase (Q31) */
    const char* const page_titles[4] = { "Morph", "Overlap", "Spread", "Tone" };
    const char* const shift_titles[4] = { "Skew", "Phase", "", "" };
    const char* titles[4];
    char values[4][header_capacity];
    for (u32 i = 0; i < 4; ++i) {
        titles[i] = row.held ? shift_titles[i] : page_titles[i];
        if (!row.held) header_amount(values[i], header_capacity, in.slots[i]);
        else if (i < 2) header_amount(values[i], header_capacity, shift_word[i]);
        else values[i][0] = 0;
    }
    const opxy::u8 slots[1][4] = { { 0, 1, 2, 3 } };
    page_header(st.header, in, fr, titles, values, N_HDR, slots);

    /* ease the controls (tau 0.05 s), and the held note's travel; reduced motion and the first frame jump */
    const bool still = in.reduced_motion != 0;
    const i32 dt = clamp(in.elapsed * 1000 / unit, 1, 100);                       /* ms */
    const i32 k_ease = still || !st.initialized ? unit : unit - expneg((dt * unit) / 50);
    for (int k = 0; k < 6; ++k) {
        const i32 target = q10(k < 4 ? in.slots[k] : shift_word[k - 4]);
        st.eased[k] += ((target - st.eased[k]) * k_ease) >> 10;
        if (iabs(target - st.eased[k]) <= 1) st.eased[k] = target;               /* settle exactly: rest is still */
    }
    const bool held = in.held_notes != 0;
    {
        const i32 goal = held && !still ? 819 : 0;                                /* 0.8 cycles a second */
        const i32 tau = held ? 50 : 60;                                           /* ms: in fast, out over ~0.2 s */
        st.speed += ((goal - st.speed) * (unit - expneg((dt * unit) / tau))) >> 10;
        if (iabs(goal - st.speed) <= 4) st.speed = goal;
        st.travel = (st.travel + st.speed * dt / 1000) & 0xFFFFF;                 /* wrap: whole cycles look the same */
    }
    st.initialized = 1;
    const i32 morph = st.eased[0], overlap = st.eased[1], spread = st.eased[2];
    const i32 tone = st.eased[3], skew = st.eased[4], phase = st.eased[5];

    /* the engine's window: a triangle kernel of width 1 + 3 overlap about morph x 3, normalised to sum 1 */
    const i32 c = morph * 3, width = unit + 3 * overlap;
    i32 w[4], wsum = 0, wmax = 1;
    for (int i = 0; i < 4; ++i) {
        const i32 d = iabs(c - i * unit);
        const i32 k = unit - static_cast<i32>((static_cast<i64>(d) << 10) / width);
        w[i] = k > 0 ? k : 0; wsum += w[i];
    }
    for (int i = 0; i < 4; ++i) { w[i] = (w[i] << 10) / wsum; if (w[i] > wmax) wmax = w[i]; }
    const i32 r_mix = lerp_band(RADIUS_Q10, c);                                   /* Q10 px */
    static const int CYCLES_Q10[4] = { 11 * 1024, 13 * 1024, 14 * 1024, 16 * 1024 };
    const i32 n_mix = lerp_band(CYCLES_Q10, c);                                   /* Q10 cycles */

    /* the bands: chains of one-cycle nodes, raw or rounded (Tone's cut), placed round their arcs */
    static const i32 CUT_BELOW[4] = { -1, 205, 461, 666 };                         /* tone 0.20, 0.45, 0.65; sine never */
    for (int b = 0; b < 4; ++b) {
        const i32 r = RADIUS_Q10[b] + static_cast<i32>((static_cast<i64>(r_mix - RADIUS_Q10[b]) * ((819 * overlap) >> 10)) >> 10);
        const i32 stretch = unit + ((123 * spread >> 10) * (2 * b - 3)) / 2;       /* 1 + 0.12 spread (b - 1.5) */
        const i32 n_b = (CYCLES_N[b] << 20) / stretch;                             /* Q10 cycles round the half-turn */
        const i32 dphi = (HALF_TURN << 20) / n_b;                                  /* tenths, Q10 */
        const i32 shift = ((phase * b) >> 3) & 1023;                               /* b/8 of a cycle x phase, Q10 */
        const i32 scale = static_cast<i32>((static_cast<i64>(r) * CYCLES_N[b] << 20) / (static_cast<i64>(RADIUS_Q10[b]) * n_b));
        i32 level = (3 * w[b] + wmax / 2) / wmax;                                  /* 0 .. 3, by mix weight */
        const bool cut = tone < CUT_BELOW[b];
        if (cut && level > 0) level--;
        const u32 paint = level >= 3 ? P_BAND_HI : level == 2 ? P_BAND_MID : P_BAND_LO;
        const u32 show = cut ? N_ROUND : N_RAW, park = cut ? N_RAW : N_ROUND;
        for (int k = 0; k < PER_BAND; ++k) {
            const u32 n = static_cast<u32>(PER_BAND * b + k);
            hide(fr, park + n);
            /* cycle j = k - 1 (one spare on each side for the wrap); its mid-angle, in tenths Q10 */
            const i64 mid = (static_cast<i64>(HALF_TURN) << 10) - ((static_cast<i64>(k - 1) * unit + 512 + shift) * dphi >> 10);
            if (mid - dphi / 2 >= (static_cast<i64>(HALF_TURN) << 10) || mid + dphi / 2 <= 0) { hide(fr, show + n); continue; }
            const i32 a = static_cast<i32>(mid >> 10);                             /* tenths */
            const i32 x = CX_Q10 + static_cast<i32>((static_cast<i64>(r) * sine(a + 900)) >> 10);
            const i32 y = CY_Q10 - static_cast<i32>((static_cast<i64>(r) * sine(a)) >> 10);
            place(fr, show + n, x, y, scale, paint, fill_and_stroke);
            turn(fr, show + n, rotation(900 - a));                                 /* authored at the top of the bow */
        }
    }
    /* the ground mask and the horizon are static art, authored after the bands so they hide cycles below ground */

    /* the mix line: rewritten only when its key changes, so it's still at rest */
    const u32 key = mix_key(st.eased, st.travel);
    if (key != st.key) {
        st.key = key;
        /* the waves' Fourier coefficients x Tone's drawn low-pass (Q14): fc = 2^(0.5 + 3 tone) harmonics */
        const i32 fc = exp2_q10(512 + 3 * tone);
        i32 coef[4][NH + 1];
        for (int n = 1; n <= NH; ++n) {
            const i64 ratio = (static_cast<i64>(n) << 20) / fc;                    /* Q10 */
            const i64 r2 = (ratio * ratio) >> 10, r4 = (r2 * r2) >> 10;            /* Q10 */
            const i32 g = static_cast<i32>(isqrt64((static_cast<u64>(1) << 40) / static_cast<u64>(1024 + r4) >> 10));   /* Q10 */
            const i32 sgn_tri = ((n - 1) / 2) & 1 ? -1 : 1, sgn_saw = (n & 1) ? 1 : -1;
            coef[0][n] = n == 1 ? (g << 4) : 0;                                                  /* sine */
            coef[1][n] = (n & 1) ? sgn_tri * ((13281 * g >> 10) / (n * n)) : 0;                /* 8 / pi^2 / n^2 */
            coef[2][n] = (n & 1) ? (20861 * g >> 10) / n : 0;                                  /* 4 / pi / n */
            coef[3][n] = sgn_saw * ((10430 * g >> 10) / n);                                     /* 2 / pi / n */
        }
        const i32 b_skew = 512 - ((461 * skew) >> 10);                             /* breakpoint 0.5 .. 0.05 */
        for (int q = 0; q < 4; ++q) {
            i32 cx[32], cy[32];                                                     /* centreline, Q10 px */
            for (int k = 0; k < 32; ++k) {
                const i32 u = ((q * 31 + k) * unit) / 124;                         /* 0 .. 1 across the half-turn */
                i32 v = 0;                                                         /* Q14 */
                for (int i = 0; i < 4; ++i) {
                    if (!w[i]) continue;
                    const i32 stretch = unit + ((123 * spread >> 10) * (2 * i - 3)) / 2;
                    i32 t = static_cast<i32>((((static_cast<i64>(n_mix) * u) >> 10) * stretch) >> 10) - st.travel + ((phase * i) >> 3);
                    t &= 1023;
                    if (i != 3 && b_skew != 512) t = warp(t, b_skew);
                    const i32 x = (t * 3600) >> 10;                                /* tenths */
                    i32 s = 0;
                    for (int n = 1; n <= NH; ++n) if (coef[i][n]) s += (coef[i][n] * sine((n * x) % 3600)) >> 10;
                    v += (w[i] * s) >> 10;
                }
                const i32 rr = r_mix + ((AMP_MIX_Q10 * v) >> 14);
                const i32 a = HALF_TURN - ((HALF_TURN * u) >> 10);
                cx[k] = CX_Q10 + static_cast<i32>((static_cast<i64>(rr) * sine(a + 900)) >> 10);
                cy[k] = CY_Q10 - static_cast<i32>((static_cast<i64>(rr) * sine(a)) >> 10);
            }
            /* origin: the quarter's middle on the arc; points relative to it, a mitred ribbon round the centreline */
            const i32 am = HALF_TURN - (HALF_TURN * (2 * q + 1)) / 8;
            const i32 ox = CX_Q10 + static_cast<i32>((static_cast<i64>(r_mix) * sine(am + 900)) >> 10);
            const i32 oy = CY_Q10 - static_cast<i32>((static_cast<i64>(r_mix) * sine(am)) >> 10);
            Point* p = fr.paths[q].points;
            for (int k = 0; k < 32; ++k) {
                const int k0 = k ? k - 1 : 0, k1 = k < 31 ? k + 1 : 31;
                i64 nx, ny, m = unit;
                if (k == 0 || k == 31) {
                    const i64 dx = cx[k1] - cx[k0], dy = cy[k1] - cy[k0], L = isqrt64(static_cast<u64>(dx * dx + dy * dy)) + 1;
                    nx = (-dy << 10) / L; ny = (dx << 10) / L;
                } else {
                    const i64 ax = cx[k] - cx[k0], ay = cy[k] - cy[k0], bx = cx[k1] - cx[k], by = cy[k1] - cy[k];
                    const i64 La = isqrt64(static_cast<u64>(ax * ax + ay * ay)) + 1, Lb = isqrt64(static_cast<u64>(bx * bx + by * by)) + 1;
                    const i64 n1x = (-ay << 10) / La, n1y = (ax << 10) / La, n2x = (-by << 10) / Lb, n2y = (bx << 10) / Lb;
                    const i64 sx = n1x + n2x, sy = n1y + n2y, Ls = isqrt64(static_cast<u64>(sx * sx + sy * sy)) + 1;
                    nx = (sx << 10) / Ls; ny = (sy << 10) / Ls;
                    const i64 cosh = (nx * n1x + ny * n1y) >> 10;                  /* mitre 1 / cos, capped at 2 */
                    m = cosh > 512 ? (static_cast<i64>(unit) << 10) / cosh : 2 * unit;
                }
                const i64 off = (static_cast<i64>(MIX_HALF_W_Q10) * m) >> 10;
                p[k].x = cx[k] + static_cast<i32>((nx * off) >> 10) - ox;          p[k].y = cy[k] + static_cast<i32>((ny * off) >> 10) - oy;
                p[63 - k].x = cx[k] - static_cast<i32>((nx * off) >> 10) - ox;     p[63 - k].y = cy[k] - static_cast<i32>((ny * off) >> 10) - oy;
            }
            fr.paths[q].key = key;
            place(fr, N_MIX + q, ox, oy, unit, held ? P_MIX_HELD : P_MIX, fill_and_stroke);
        }
    } else {
        for (int q = 0; q < 4; ++q) {
            const i32 am = HALF_TURN - (HALF_TURN * (2 * q + 1)) / 8;
            place(fr, N_MIX + q, CX_Q10 + static_cast<i32>((static_cast<i64>(r_mix) * sine(am + 900)) >> 10),
                  CY_Q10 - static_cast<i32>((static_cast<i64>(r_mix) * sine(am)) >> 10), unit, held ? P_MIX_HELD : P_MIX, fill_and_stroke);
        }
    }
}
}
