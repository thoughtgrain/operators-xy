#pragma once
#include <opxy/audio.hpp>

// iris for the OP-XY: the voice's state. The sound lives in engine.cpp.
// Copyright (c) 2026 briannhinton. MIT.
namespace iris {
struct Voice {
    opxy::u32 ph[4];           // one phase per band (sine, triangle, square, saw), 2^32 = one cycle
    opxy::i32 g[4];            // each band's mix weight at the end of the last block, Q15 (ramped across blocks)
    opxy::i32 low, band;       // state-variable low-pass, Q15
    opxy::i32 f_last;          // cutoff coefficient of the last block, 0 = none yet (no sweep or fade on a new note)
};
struct Shared {
    opxy::u32 reserved;        // nothing is shared between voices yet; kept a whole word so the size is stable
};
}
