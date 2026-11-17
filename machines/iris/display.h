#pragma once
#include <opxy/page_header.hpp>

// iris for the OP-XY: the rainbow screen's state. Matches resources.display in definition.json.
// Copyright (c) 2026 briannhinton. MIT.
namespace iris {
using Frame = opxy::draw::Frame<4, 64, 140, 8, 5>;   // paths, points, nodes, texts, palette
struct DisplayState {
    opxy::draw::PageHeader header;     // 20 bytes
    opxy::i32 eased[6];                // the six controls as drawn, Q10, easing toward the knobs
    opxy::i32 travel;                  // how far a held note has carried the mix line, Q10 cycles (wrapped)
    opxy::i32 speed;                   // its speed, Q10 cycles per second (0.8 while held, easing to 0 after)
    opxy::u32 key;                     // the key last written to the four mix outlines; 0 = none yet
    opxy::u32 initialized;
};                                     // 20 + 24 + 16 = 60 bytes
}
