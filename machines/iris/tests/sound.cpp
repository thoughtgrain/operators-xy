// iris's own sound checks, built for the host by python sdk.py test --machine <folder>.
// Sweeps every control over min / mid / max at low and high notes and checks: never above the declared peak,
// no DC lock-up, Morph brightens monotonically from sine to saw, Overlap holds the level while it thickens,
// Spread makes the level beat, Tone darkens, Skew and Phase change the sound only where they should, and the
// voice fits its declared size.
// Copyright (c) 2026 briannhinton. MIT.
#include "../engine.cpp"
#include <cstdio>
#include <cmath>
#include <initializer_list>

static int fails;
#define CHECK(c, ...) do { if (!(c)) { fails++; std::printf("FAIL: "); std::printf(__VA_ARGS__); std::printf("\n"); } } while (0)

struct Stats { double rms, bright, dc, beat; int over; };
/* Plays one note for `blocks` blocks and measures the second half: level, brightness (rms of the difference over
 * rms of the signal), DC, and how much the level swings from one 512-sample window to the next (beating). */
static Stats play(double hz, const opxy::i32 *p, int blocks)
{
    static iris::Voice v; static iris::Shared s;
    opxy::u32 pitch[opxy::block_frames]; opxy::i32 out[opxy::block_frames];
    for (unsigned n = 0; n < opxy::block_frames; n++) pitch[n] = static_cast<opxy::u32>(hz / 44100.0 * 4294967296.0);
    iris::initialize(v, s, 1); iris::start(v, s, 1);
    Stats st = { 0, 0, 0, 0, 0 }; double prev = 0, sum = 0, dsum = 0, mean = 0, win = 0, wmin = 1e30, wmax = 0; long cnt = 0;
    for (int b = 0; b < blocks; b++) {
        iris::render(v, s, 1, out, p, pitch);
        if (b < blocks / 2) continue;
        for (unsigned n = 0; n < opxy::block_frames; n++) {
            const double x = out[n] / 65536.0;
            sum += x * x; dsum += (x - prev) * (x - prev); prev = x; mean += x; cnt++;
            win += x * x;
            if (cnt % 512 == 0) { if (win < wmin) wmin = win; if (win > wmax) wmax = win; win = 0; }
            if (out[n] > 1073741824 || out[n] < -1073741824) st.over++;
        }
    }
    st.rms = std::sqrt(sum / cnt); st.bright = sum > 0 ? std::sqrt(dsum / sum) : 0;
    st.dc = std::fabs(mean / cnt) / (st.rms + 1e-9); st.beat = wmax > 0 ? (wmax - wmin) / wmax : 0;
    return st;
}
static opxy::i32 q(double f) { return f >= 1.0 ? 2147483647 : static_cast<opxy::i32>(f * 2147483647.0); }

int main()
{
    static_assert(sizeof(iris::Voice) == 44, "definition.json voiceBytes");
    static_assert(sizeof(iris::Shared) == 4, "definition.json sharedBytes");
    const double D[6] = { 1.0 / 3, 0.25, 0, 0.7, 0, 0 };
    opxy::i32 p[6];
    auto set = [&](int k, double val) { for (int i = 0; i < 6; i++) p[i] = q(D[i]); if (k >= 0) p[k] = q(val); };

    // Every control at min / mid / max, low and high notes: no overs, no DC, never silent
    const double hz[3] = { 55.0, 440.0, 2093.0 };
    for (int k = 0; k < 6; k++) for (double val : { 0.0, 0.5, 1.0 }) for (double h : hz) {
        set(k, val); const Stats st = play(h, p, 200);
        CHECK(st.over == 0, "control %d at %.1f, %.0f Hz: %d samples over the declared peak", k, val, h, st.over);
        CHECK(st.dc < 0.05, "control %d at %.1f, %.0f Hz: DC %.3f of rms", k, val, h, st.dc);
        CHECK(st.rms > 500, "control %d at %.1f, %.0f Hz: nearly silent (rms %.0f)", k, val, h, st.rms);
    }
    // All controls at max together
    for (int i = 0; i < 6; i++) p[i] = q(1.0);
    for (double h : hz) { const Stats st = play(h, p, 200); CHECK(st.over == 0 && st.rms > 500, "all at max, %.0f Hz", h); }

    // Morph brightens monotonically sine -> triangle -> square -> saw, with Overlap closed and Tone open
    double last = 0;
    for (int m = 0; m <= 3; m++) {
        set(0, m / 3.0); p[1] = 0; p[3] = q(1.0);
        const Stats st = play(220.0, p, 200);
        std::printf("morph band %d: rms %.0f bright %.4f\n", m, st.rms, st.bright);
        CHECK(st.bright > last * 1.03, "morph: band %d isn't brighter than band %d", m, m - 1);
        last = st.bright;
    }
    // Overlap thickens without getting much louder: level within 3 dB from 0 to 100 at the triangle
    { set(1, 0.0); const Stats a = play(220.0, p, 200); set(1, 1.0); const Stats b = play(220.0, p, 200);
      std::printf("overlap 0 / 100: rms %.0f / %.0f, bright %.4f / %.4f\n", a.rms, b.rms, a.bright, b.bright);
      CHECK(b.rms / a.rms < 1.42 && b.rms / a.rms > 0.70, "overlap: level moved more than 3 dB");
      CHECK(b.bright > a.bright * 1.1, "overlap: opening it at the triangle should bring in the brighter bands"); }
    // Spread beats: level swings window to window when the bands are spread and overlapping, not when they're not
    { set(2, 0.0); p[1] = q(1.0); const Stats a = play(44100.0 / 256, p, 1400); set(2, 1.0); p[1] = q(1.0); const Stats b = play(44100.0 / 256, p, 1400);
      std::printf("spread 0 / 100: beat %.3f / %.3f\n", a.beat, b.beat);
      CHECK(a.beat < 0.05, "spread 0: the level shouldn't beat"); CHECK(b.beat > 0.2, "spread 100: the bands should beat"); }
    // Tone darkens, saw band
    { set(3, 0.2); p[0] = q(1.0); const Stats a = play(220.0, p, 200); set(3, 1.0); p[0] = q(1.0); const Stats b = play(220.0, p, 200);
      std::printf("tone 20 / 100: bright %.4f / %.4f\n", a.bright, b.bright);
      CHECK(b.bright > a.bright * 1.5, "tone: opening the filter should brighten clearly"); }
    // Skew: brightens the sine and the square; leaves the saw alone
    for (int band : { 0, 2, 3 }) {
        set(4, 0.0); p[0] = q(band / 3.0); p[1] = 0; p[3] = q(1.0); const Stats a = play(220.0, p, 200);
        set(4, 1.0); p[0] = q(band / 3.0); p[1] = 0; p[3] = q(1.0); const Stats b = play(220.0, p, 200);
        std::printf("skew 0 / 100 on band %d: bright %.4f / %.4f\n", band, a.bright, b.bright);
        if (band == 3) CHECK(std::fabs(b.bright / a.bright - 1) < 0.01, "skew: the saw should be unchanged");
        else CHECK(b.bright > a.bright * 1.2, "skew: band %d should sharpen", band);
    }
    // Phase: inaudible on one band, changes the sound where bands overlap
    { set(5, 0.0); p[0] = 0; p[1] = 0; const Stats a = play(220.0, p, 200); set(5, 1.0); p[0] = 0; p[1] = 0; const Stats b = play(220.0, p, 200);
      CHECK(std::fabs(b.rms / a.rms - 1) < 0.01, "phase: one band alone shouldn't change");
      set(5, 0.0); p[1] = q(1.0); p[0] = q(0.5); const Stats c = play(220.0, p, 200);
      set(5, 1.0); p[1] = q(1.0); p[0] = q(0.5); const Stats d = play(220.0, p, 200);
      std::printf("phase 0 / 100, all bands: rms %.0f / %.0f, bright %.4f / %.4f\n", c.rms, d.rms, c.bright, d.bright);
      CHECK(std::fabs(d.rms / c.rms - 1) > 0.05 || std::fabs(d.bright / c.bright - 1) > 0.05, "phase: should change the overlapped sound");
      CHECK(d.rms / c.rms > 0.5, "phase: shouldn't drop the level more than 6 dB"); }
    // Morph keeps the level: every band within 3 dB of the triangle, Tone open
    { double r[4]; for (int m = 0; m <= 3; m++) { set(0, m / 3.0); p[1] = 0; p[3] = q(1.0); r[m] = play(220.0, p, 200).rms; }
      for (int m = 0; m <= 3; m++) CHECK(r[m] / r[1] < 1.42 && r[m] / r[1] > 0.70, "morph: band %d is %.1f dB off the triangle", m, 20 * std::log10(r[m] / r[1])); }
    // Tone follows the note: the same setting darkens a low and a high note alike
    { set(3, 0.3); const Stats lo = play(110.0, p, 200); set(3, 0.3); const Stats hi = play(880.0, p, 200);
      std::printf("tone 30 at 110 / 880 Hz: rms %.0f / %.0f\n", lo.rms, hi.rms);
      CHECK(hi.rms / lo.rms > 0.7 && hi.rms / lo.rms < 1.42, "tone: should track the note"); }

    if (fails) std::printf("%d check(s) failed\n", fails); else std::printf("iris: all sound checks pass\n");
    return fails ? 1 : 0;
}
