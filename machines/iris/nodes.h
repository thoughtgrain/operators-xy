#pragma once
// iris for the OP-XY: node indices and the bow's geometry, written by gen_panel.py.
// Edit the generator, not this file.
namespace iris {
enum { N_MIX = 0, N_HDR = 4, N_BAND = 12, PER_BAND = 16, CHAINS = 12, N_TOTAL = 204 };
// band b: chain kind * 4 + b, kind 0 ripple (out of the blend), 1 full height, 2 full height rounded (Tone cut)
enum { P_MIX = 0, P_MIX_HELD = 1, P_BAND_LO = 2, P_BAND_MID = 3, P_BAND_HI = 4, PALETTE_N = 5 };
// Q10 px: the bow's centre, each band's rest radius, the wave heights and the mix ribbon's half width
const int CX_Q10 = 245760, CY_Q10 = 237568;
const int RADIUS_Q10[4] = { 159744, 149504, 139264, 129024 };
const int CYCLES_N[4] = { 11, 13, 14, 16 };
const int AMP_MIX_Q10 = 5120, MIX_HALF_W_Q10 = 1280;
}
