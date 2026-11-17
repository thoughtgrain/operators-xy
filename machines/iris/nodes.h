#pragma once
// iris for the OP-XY: node indices and the bow's geometry, written by gen_panel.py.
// Edit the generator, not this file.
namespace iris {
enum { N_MIX = 0, N_HDR = 4, N_RAW = 12, N_ROUND = 76, PER_BAND = 16, N_TOTAL = 140 };
enum { P_MIX = 0, P_MIX_HELD = 1, P_BAND_LO = 2, P_BAND_MID = 3, P_BAND_HI = 4, PALETTE_N = 5 };
// Q10 px: the bow's centre, each band's rest radius, the wave heights and the mix ribbon's half width
const int CX_Q10 = 245760, CY_Q10 = 208896;
const int RADIUS_Q10[4] = { 159744, 143360, 126976, 110592 };
const int CYCLES_N[4] = { 11, 13, 14, 16 };
const int AMP_MIX_Q10 = 5120, MIX_HALF_W_Q10 = 1280;
}
