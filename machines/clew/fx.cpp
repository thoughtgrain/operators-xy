#include "core.h"
#include <opxy/q31.hpp>

/* Clew for the OP-XY: a compressor, a tempo-synced delay and a small reverb in one send effect, tied together by
 * one level follower. The follower drives the compressor, and Blend lets the same follower duck the echoes and the
 * room while you play, so the tails swell in the gaps.
 *
 * Page 1 (press any encoder for page 2):
 *   Squeeze  compression: threshold, ratio and make-up on one control; 0 is off
 *   Echo     the delay: the time steps through stock delay's note lengths at the track's tempo, and the repeats
 *            grow with it; at 0 there are none
 *   Space    the room: its size (decay time) and level together; at 0 there is none
 *   Blend    how much the playing ducks the echoes and the room; at 0 they're steady
 * Page 2:
 *   Tone     the tails only: darker to the left (and their repeats and room damp faster), thinner to the right
 *   Motion   a slow wobble in the echoes' time, a drift in the room, both a little apart left and right
 *   Dry      the playing's own level in the box: at 0 only the tails come back
 *   Attack   how fast the compressor and the ducking catch a note, 0.5 to 30 ms
 * Shift row:
 *   Order    Comp first compresses the playing, then echoes and rooms it; FX first compresses the playing and its
 *            tails together. Either way the follower listens to what comes in.
 *
 * Machine.json fixes the stock dry at 0 (dryLevel), so Clew mixes its own dry: at full send the whole track goes
 * through it, like an insert, and at less the rest stays dry around it.
 *
 * Integer only. Level work is in log2 units, Q16 (1.0 = 6.02 dB), once every 16 samples, with the gain ramped
 * between. Copyright (c) 2026 briannhinton. MIT. */
namespace clew {
namespace {
using opxy::i32;
using opxy::i64;
using opxy::u32;
const i32 kMaximum = opxy::q31::maximum, kMinimum = -kMaximum - 1;
const u32 kStep = 16;                                   // samples per control step

// buffer layout, in words
const u32 kDiffuseAt[2] = { 2 * kDelay, 2 * kDelay + 71 };
const u32 kRoomBase = 2 * kDelay + 71 + 190;
const u32 kRoomAt[4] = { kRoomBase, kRoomBase + 563, kRoomBase + 563 + 787, kRoomBase + 563 + 787 + 953 };
const u32 kRoomSize[4] = { 563, 787, 953, 1171 + kSwing };
const u32 kClearPerBlock = 8192;                        // the buffer is zeroed in ~12 blocks after initialize

const u32 kSixteenthAtOneTenthBpm = 1653750;            // 44100 * 60 * 10 / 16
const u32 kNoTempo = 1200;
const i32 kShortest = 512 << 8, kLongest = static_cast<i32>((kDelay - 2 - 128) << 8);

// a Q31 product, floored like opxy::q31::multiply but without its rounding checks; never called with both
// arguments at -1
inline i32 multiply(i32 a, i32 b) { return static_cast<i32>((static_cast<i64>(a) * b) >> 31); }
// a one-pole step from `state` towards `x` by `c` (0..1, Q31): always between them, so it can't overflow
inline i32 toward(i32 state, i32 x, i32 c) { return state + static_cast<i32>(((static_cast<i64>(x) - state) * c) >> 31); }
inline i32 saturate(i64 v) { return v > kMaximum ? kMaximum : v < kMinimum ? kMinimum : static_cast<i32>(v); }
inline i32 magnitude(i32 v) { return v == kMinimum ? kMaximum : v < 0 ? -v : v; }
// the output's safety: untouched up to 0.75, then bending smoothly into full scale (0.75 + e - e^2, flat at 1)
// instead of clipping; one multiply, no division
inline i32 limit(i64 v)
{
    const i32 knee = 1610612736, reach = 1073741824;                                 // 0.75, 0.5
    const i64 m = v < 0 ? -v : v;
    if (m <= knee) return static_cast<i32>(v);
    const i32 e = m - knee > reach ? reach : static_cast<i32>(m - knee);
    const i32 y = knee + e - multiply(e, e);
    return v < 0 ? -y : y;
}
inline i32 add(i32 a, i32 b) { return saturate(static_cast<i64>(a) + b); }
inline i32 control(i32 word) { return word < 0 ? 0 : word; }


// log2 of x / 2^31, Q16 (0 at full scale, negative below). Cubic on the mantissa: within 0.0013 (0.008 dB).
inline i32 log2_q16(i32 x)
{
    if (x <= 0) return -32 << 16;
    u32 m = static_cast<u32>(x);
    i32 n = 0;
    if (m < (1u << 15)) { m <<= 16; n += 16; }
    if (m < (1u << 23)) { m <<= 8; n += 8; }
    if (m < (1u << 27)) { m <<= 4; n += 4; }
    if (m < (1u << 29)) { m <<= 2; n += 2; }
    if (m < (1u << 30)) { m <<= 1; n += 1; }
    const i64 f = static_cast<i64>(m - (1u << 30)) >> 14;                     // the mantissa's fraction, Q16
    const i64 p = 93290 + ((f * (-38518 + ((f * 10850) >> 16))) >> 16);
    return static_cast<i32>((f * p) >> 16) - ((n + 1) << 16);
}
// 2^y for y <= 0 (Q16), Q31. Cubic on the fraction: within 0.0001.
inline i32 exp2_q31(i32 y)
{
    if (y >= 0) return kMaximum;
    const i32 down = -y, whole = down >> 16;
    if (whole >= 31) return 0;
    const i64 g = down & 0xFFFF;                                                // Q16
    i64 p = -42423765;
    p = 247599292 + ((p * g) >> 16);
    p = -742038397 + ((p * g) >> 16);
    p = 1073633097 + ((p * g) >> 16);                                           // 2^-g, Q30
    const i64 q = p << 1;
    return saturate(q >> whole);
}
// 2^y for 0 <= y < 3 (Q16), Q28: the compressor's make-up gain
inline i32 exp2_q28(i32 y)
{
    const i32 whole = y >> 16, part = y & 0xFFFF;
    const i32 half = exp2_q31(part - 65536);                                    // 2^(part - 1), Q31
    return half >> (2 - whole);                                                 // 2^part * 2^whole, Q28
}

// the line `delay` (Q8) samples back from `write`, between its two nearest samples
inline i32 tap(const i32* line, u32 size, u32 write, i32 delay)
{
    const u32 whole = static_cast<u32>(delay) >> 8, part = static_cast<u32>(delay) & 255;
    const u32 a = write >= whole ? write - whole : write + size - whole;
    const u32 b = a ? a - 1 : size - 1;
    return (line[a] >> 8) * static_cast<i32>(256 - part) + (line[b] >> 8) * static_cast<i32>(part);
}
// a Schroeder allpass, gain 0.6: spreads a sound in time without colouring it
inline i32 diffuse(i32* line, u32 size, u32& at, i32 x)
{
    const i32 g = 1288490189;
    const i32 d = line[at];
    const i32 w = add(x, multiply(g, d));
    line[at] = w;
    at = at + 1 == size ? 0 : at + 1;
    return add(d, -multiply(g, w));
}
// About a 23 ms glide, so a new delay time slides like tape instead of clicking
inline i32 glide(i32 value, i32 target)
{
    const i32 difference = target - value, step = difference / 1024;
    return value + (step ? step : (difference > 0) - (difference < 0));
}
// a triangle from a phase, -2^30 .. 2^30
inline i32 triangle(u32 phase)
{
    const u32 up = phase < 0x80000000u ? phase : 0xFFFFFFFFu - phase;
    return static_cast<i32>(up) - (1 << 30);
}
}

void initialize(State& state) { state = State(); state.gain = kMaximum; state.wet = kMaximum; }

void process(State& state, opxy::Buffer buffer, const opxy::Transport& transport, opxy::Channel left,
             opxy::Channel right, opxy::Parameters parameters)
{
    if (!buffer.words || buffer.count < kWords) {
        for (unsigned i = 0; i < opxy::block_frames; ++i) left[i] = right[i] = 0;
        return;
    }
    i32* const words = buffer.words;
    const i32 dry = control(parameters[6]);
    if (state.cleared < kWords) {                       // until the buffer is ours, only the dry comes back
        const u32 end = state.cleared + kClearPerBlock < kWords ? state.cleared + kClearPerBlock : kWords;
        for (u32 k = state.cleared; k < end; ++k) words[k] = 0;
        state.cleared = end;
        for (unsigned i = 0; i < opxy::block_frames; ++i) { left[i] = multiply(left[i], dry); right[i] = multiply(right[i], dry); }
        return;
    }

    /* the controls, once a block */
    const i32 s16 = control(parameters[0]) >> 15, e = control(parameters[1]), p16 = control(parameters[2]) >> 15;
    const i32 blend = control(parameters[3]), tone = (control(parameters[4]) >> 15) - 32768;   // tone: Q15, -1..1
    const i32 motion = control(parameters[5]), a16 = control(parameters[7]) >> 15;
    const bool comp_first = ((static_cast<u32>(control(parameters[8])) >> 16) * 2 >> 15) == 0;

    // Squeeze: threshold -3 to -33 dB, ratio 1:1 to 8:1 (on its square), make-up for 40 % of what it takes at full scale
    const i32 threshold = -(32657 + static_cast<i32>((326566LL * s16) >> 16));                 // log2, Q16
    const i64 s2 = (static_cast<i64>(s16) * s16) >> 16, num = 7 * s2;
    const i32 slope = static_cast<i32>((num << 16) / (65536 + num));                            // 1 - 1/ratio, Q16
    const i32 makeup = exp2_q28(static_cast<i32>((((static_cast<i64>(-threshold) * slope) >> 16) * 26214) >> 16));
    // Attack: 0.5 ms * 60^a, as a one-pole coefficient per sample
    const i32 attack = multiply(97391549, exp2_q31(-static_cast<i32>((static_cast<i64>(a16) * 387115) >> 16)));
    const i32 fast_release = 811596, slow_release = 81160;                                      // 60 ms, 600 ms
    const i32 duck_attack = 155826478, duck_release = 3116530;                                  // 5 ms, 250 ms, per step
    const i32 duck_depth = multiply(blend, 1932735283);                                        // 0.9 blend

    // Echo: a note length at the tempo, repeats from 15 % to 75 %, its level up over the first eighth
    const u32 bpm = transport.bpm_x10 ? transport.bpm_x10 : kNoTempo;
    const u32 length = opxy::division_sixteenths[opxy::division(e)] * kSixteenthAtOneTenthBpm;
    i32 delay_target = static_cast<i32>(((length / bpm) << 8) + ((length % bpm) << 8) / bpm);
    delay_target = delay_target < kShortest ? kShortest : delay_target > kLongest ? kLongest : delay_target;
    const i32 feedback_target = add(322122547, multiply(e, 1288490189));
    const i32 echo_level = multiply(e > (kMaximum >> 3) ? kMaximum : e << 3, 1717986918);       // up to 0.8
    // Motion: the echoes' time swings up to 2 ms, a quarter cycle apart left and right; moved once a block and
    // glided between, so the swing costs nothing per sample
    state.wobble += 48696u * opxy::block_frames;                                            // 0.5 Hz
    state.drift += 19478u * opxy::block_frames;                                             // 0.2 Hz
    const i32 wow = multiply(motion, 88 << 8);
    const i32 target_l = delay_target + static_cast<i32>((static_cast<i64>(triangle(state.wobble)) * wow) >> 30);
    const i32 target_r = delay_target + static_cast<i32>((static_cast<i64>(triangle(state.wobble + 0x40000000u)) * wow) >> 30);
    if (!state.delay[0]) { state.delay[0] = target_l; state.delay[1] = target_r; }

    // Space: decay 0.25 to 3.25 s (on its square), each room line's gain for that decay at the room's half rate;
    // level with it
    const i32 rt_ms = 250 + static_cast<i32>((3000LL * ((static_cast<i64>(p16) * p16) >> 16)) >> 16);
    i32 room_gain[4];
    for (int k = 0; k < 4; ++k) room_gain[k] = exp2_q31(-static_cast<i32>(kRoom[k] * 29622u / static_cast<u32>(rt_ms)));
    const i32 room_level = p16 << 15;                                                           // 0..1, Q31

    // Tone: left darkens (to ~700 Hz), right thins (a high-pass up to ~400 Hz); repeats and room damp with it
    const i32 open = 2040109466;                                                                // 0.95
    const i32 low_coefficient = tone < 0 ? multiply(open, exp2_q31(static_cast<i32>((static_cast<i64>(tone) * 432538) >> 16))) : open;
    const i32 floor_coefficient = tone > 0 ? 4294967 + multiply(128849019, tone << 16) : 0;
    const i32 room_damp = 1503238554 + (tone << 14);                                           // 0.7 + 0.25 tone, at half rate
    const i32 echo_damp = 1234803098 + multiply(590558003, tone << 16);                         // 0.575 + 0.275 tone

    // Motion also drifts the last room line by up to 12 of its samples
    const i32 sway = static_cast<i32>((static_cast<i64>(triangle(state.drift)) * multiply(motion, 12 << 8)) >> 30);

    i32* const echo_line[2] = { words, words + kDelay };
    i32* const diffuse_line[2] = { words + kDiffuseAt[0], words + kDiffuseAt[1] };
    i32* const room_line[4] = { words + kRoomAt[0], words + kRoomAt[1], words + kRoomAt[2], words + kRoomAt[3] };

    for (unsigned i = 0; i < opxy::block_frames; ++i) {
        const i32 xl = left[i], xr = right[i];

        /* the follower, and every 16 samples the gains it sets */
        const i32 level = magnitude(xl) > magnitude(xr) ? magnitude(xl) : magnitude(xr);
        state.fast = toward(state.fast, level, level > state.fast ? attack : fast_release);
        state.slow = toward(state.slow, level, level > state.slow ? attack : slow_release);
        if (state.step == 0) {
            const i32 held = state.slow - (state.slow >> 2);                                    // the slow one, 2.5 dB down
            const i32 detected = log2_q16(state.fast > held ? state.fast : held);
            // gain reduction with a 6 dB soft knee
            const i32 over = detected - threshold, knee = 65536;
            i32 reduce = 0;
            if (over >= knee / 2) reduce = static_cast<i32>((static_cast<i64>(over) * slope) >> 16);
            else if (over > -knee / 2) {
                const i64 into = over + knee / 2;
                reduce = static_cast<i32>((((into * into) >> 17) * slope) >> 16);              // slope (over + k/2)^2 / 2k
            }
            const i32 target = exp2_q31(-reduce);
            state.gain_step = (target - state.gain) / static_cast<i32>(kStep);
            // the ducking follows the fast follower alone, so the tails come back as soon as the playing stops:
            // from 0 at -30 dB in to all of it at -6 dB, caught at Attack, let go over 250 ms
            const i32 window = log2_q16(state.fast) + 326566;
            const i32 amount = window <= 0 ? 0 : window >= 261276 ? kMaximum : static_cast<i32>(static_cast<i64>(window) * 8219);
            state.duck = toward(state.duck, amount, amount > state.duck ? duck_attack : duck_release);
            const i32 wet_target = kMaximum - multiply(duck_depth, state.duck);
            state.wet_step = (wet_target - state.wet) / static_cast<i32>(kStep);
        }
        state.step = state.step + 1 == kStep ? 0 : state.step + 1;
        state.gain += state.gain_step;
        state.wet += state.wet_step;
        const i32 gain = state.gain, wet_gain = state.wet;
        auto squeeze = [&](i32 v) { return saturate((static_cast<i64>(multiply(v, gain)) * makeup) >> 28); };

        const i32 sl = comp_first ? squeeze(xl) : xl, sr = comp_first ? squeeze(xr) : xr;

        /* the echoes: a quarter of each side crossing over */
        state.delay[0] = glide(state.delay[0], target_l);
        state.delay[1] = glide(state.delay[1], target_r);
        state.feedback = glide(state.feedback, feedback_target);
        const i32 el = tap(echo_line[0], kDelay, state.write, state.delay[0]);
        const i32 er = tap(echo_line[1], kDelay, state.write, state.delay[1]);
        state.echo_low[0] = toward(state.echo_low[0], el, echo_damp);
        state.echo_low[1] = toward(state.echo_low[1], er, echo_damp);
        const i32 back_l = (state.echo_low[0] >> 2) * 3 + (state.echo_low[1] >> 2);          // weights sum to 1: no overflow
        const i32 back_r = (state.echo_low[1] >> 2) * 3 + (state.echo_low[0] >> 2);
        echo_line[0][state.write] = saturate(static_cast<i64>(sl) + multiply(back_l, state.feedback));
        echo_line[1][state.write] = saturate(static_cast<i64>(sr) + multiply(back_r, state.feedback));
        state.write = state.write + 1 == kDelay ? 0 : state.write + 1;
        const i32 echo_l = multiply(el, echo_level), echo_r = multiply(er, echo_level);

        /* the room, at half rate: both sides and half their echoes, an eighth each, averaged over two samples,
         * diffused, into four lines mixed by a Hadamard matrix; its output interpolated back up */
        const i32 room_input = (sl >> 3) + (sr >> 3) + (echo_l >> 4) + (echo_r >> 4);
        i64 room_l, room_r;
        if (!state.room_odd) {
            state.room_in = room_input;
            room_l = (static_cast<i64>(state.room_prev[0]) + state.room_now[0]) >> 1;
            room_r = (static_cast<i64>(state.room_prev[1]) + state.room_now[1]) >> 1;
        } else {
            const i32 in = diffuse(diffuse_line[1], 190, state.diffuse_at[1],
                                   diffuse(diffuse_line[0], 71, state.diffuse_at[0], (state.room_in >> 1) + (room_input >> 1)));
            i32 r[4];
            for (int k = 0; k < 3; ++k) r[k] = room_line[k][state.room_at[k]];
            r[3] = tap(room_line[3], kRoomSize[3], state.room_at[3], static_cast<i32>((1171 + kSwing / 2) << 8) + sway);
            for (int k = 0; k < 4; ++k) state.damp[k] = toward(state.damp[k], r[k], room_damp);
            // the Hadamard mix, each line's sum of four halves kept wide until its one saturation
            const i64 a = state.damp[0] >> 1, b = state.damp[1] >> 1, c = state.damp[2] >> 1, d = state.damp[3] >> 1;
            const i64 h[4] = { a + b + c + d, a - b + c - d, a + b - c - d, a - b - c + d };
            const i64 feed[4] = { in, -static_cast<i64>(in), 0, 0 };
            for (int k = 0; k < 4; ++k) {
                room_line[k][state.room_at[k]] = saturate(feed[k] + ((h[k] * room_gain[k]) >> 31));
                state.room_at[k] = state.room_at[k] + 1 == kRoomSize[k] ? 0 : state.room_at[k] + 1;
            }
            state.room_prev[0] = state.room_now[0]; state.room_prev[1] = state.room_now[1];
            state.room_now[0] = saturate(((static_cast<i64>(state.damp[0]) + state.damp[2]) * room_level) >> 28);
            state.room_now[1] = saturate(((static_cast<i64>(state.damp[1]) + state.damp[3]) * room_level) >> 28);
            room_l = state.room_prev[0]; room_r = state.room_prev[1];
        }
        state.room_odd ^= 1u;

        /* Tone on the tails, then the ducking */
        i32 tl = saturate(echo_l + room_l), tr = saturate(echo_r + room_r);
        state.tone_low[0] = toward(state.tone_low[0], tl, low_coefficient);
        state.tone_low[1] = toward(state.tone_low[1], tr, low_coefficient);
        tl = state.tone_low[0]; tr = state.tone_low[1];
        if (floor_coefficient) {
            state.tone_floor[0] = toward(state.tone_floor[0], tl, floor_coefficient);
            state.tone_floor[1] = toward(state.tone_floor[1], tr, floor_coefficient);
            tl = saturate(static_cast<i64>(tl) - state.tone_floor[0]); tr = saturate(static_cast<i64>(tr) - state.tone_floor[1]);
        }
        tl = multiply(tl, wet_gain); tr = multiply(tr, wet_gain);

        if (comp_first) {
            left[i] = limit(static_cast<i64>(multiply(sl, dry)) + tl);
            right[i] = limit(static_cast<i64>(multiply(sr, dry)) + tr);
        } else {
            left[i] = limit(squeeze(add(multiply(xl, dry), tl)));
            right[i] = limit(squeeze(add(multiply(xr, dry), tr)));
        }
    }
}
}
