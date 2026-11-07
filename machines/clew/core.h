#pragma once
#include <opxy/effect.hpp>

// Clew for the OP-XY: a compressor, a tempo-synced delay and a small reverb in one send effect.
// Copyright (c) 2026 briannhinton. MIT.
namespace clew {
// The send slot's buffer, in words: two delay lines of a second each, then the room, which runs at half the
// sample rate: two allpass diffusers and four lines (the last with room to swing for Motion).
// definition.json: bufferBytes = 4 * kWords.
const opxy::u32 kDelay = 44100;
const opxy::u32 kDiffuse[2] = { 71, 190 };
const opxy::u32 kRoom[4] = { 563, 787, 953, 1171 };
const opxy::u32 kSwing = 32;                       // extra words on the last room line
const opxy::u32 kWords = 2 * kDelay + 71 + 190 + 563 + 787 + 953 + 1171 + kSwing;

struct State {
    opxy::u32 cleared;                 // buffer words zeroed since initialize: the buffer is never cleared for us
    opxy::u32 step;                    // samples into the current 16-sample control step
    opxy::i32 fast, slow;              // the level follower: fast and slow release, Q31
    opxy::i32 gain, gain_step;         // the compressor's gain, Q31, ramped across each control step
    opxy::i32 duck;                    // how much the playing ducks the tails, Q31
    opxy::i32 wet, wet_step;           // the tails' level after ducking, Q31, ramped
    opxy::u32 write;                   // the delay lines' write position
    opxy::i32 delay[2];                // each side's delay time, Q8 samples, gliding
    opxy::i32 feedback;                // gliding, Q31
    opxy::i32 echo_low[2];             // the repeats' tone filters
    opxy::u32 wobble, drift;           // Motion's two slow oscillators
    opxy::u32 diffuse_at[2], room_at[4];
    opxy::i32 damp[4];                 // the room lines' damping filters
    opxy::u32 room_odd;                // the room runs on every other sample
    opxy::i32 room_in;                 // the first sample of each pair, averaged into the room's input
    opxy::i32 room_prev[2], room_now[2];    // its last two outputs, interpolated between
    opxy::i32 tone_low[2], tone_floor[2];   // Tone on the tails: a low-pass, and the low end a high-pass removes
};
static_assert(sizeof(State) <= opxy::effect_buffered_state_bytes - 4, "a shift row takes 4 bytes of the state");

void initialize(State& state);
void process(State& state, opxy::Buffer buffer, const opxy::Transport& transport, opxy::Channel left,
             opxy::Channel right, opxy::Parameters parameters);
}
