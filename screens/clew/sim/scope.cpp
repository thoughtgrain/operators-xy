// What Clew's page would see if effect pages received the send's levels (the SDK doesn't give them yet): toro plays
// a phrase at 120 BPM through Clew's own engine code, and this writes the peak of the send's input and of Clew's
// output for every 22-block window (1408 samples, 31.9 ms). gen_clew.py draws its frames from these, and the preview
// video from the demo run.
//
//   scope demo <out.wav> <peaks.txt>                    the 56 s demo, one control changed every 8 s
//   scope const <p0..p8 as 0..1> <seconds> <peaks.txt>  constant controls
//
// Host code, not machine code: it runs both engines on a computer, so its audio is a simulation.
#include "engine.cpp"
#include "fx.cpp"
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

static opxy::i32 words[clew::kWords];
struct Section { const char* title; double v[9]; };
//                            squeeze echo   space blend tone  motion dry attack order
static const Section DEMO[] = {
    { "Dry",                   { 0,   0,     0,    0,    0.5,  0,     1, 0.5624, 0 } },
    { "Squeeze 70",            { 0.7, 0,     0,    0,    0.5,  0,     1, 0.5624, 0 } },
    { "+ Echo: dotted 1/8",    { 0.7, 0.6875,0,    0,    0.5,  0,     1, 0.5624, 0 } },
    { "+ Space 60",            { 0.7, 0.6875,0.6,  0,    0.5,  0,     1, 0.5624, 0 } },
    { "+ Blend 100",           { 0.7, 0.6875,0.6,  1,    0.5,  0,     1, 0.5624, 0 } },
    { "+ Motion 70, Tone -40", { 0.7, 0.6875,0.6,  1,    0.3,  0.7,   1, 0.5624, 0 } },
    { "Order: FX first",       { 0.7, 0.6875,0.6,  1,    0.3,  0.7,   1, 0.5624, 0.75 } },
};
static const double SR = 44100, STEP = 60.0 / 120 / 4, SEC = 8.0;
static const int WINDOW = 22 * 64;

// the phrase: per bar, eight 16ths (loud and quiet alternating), a held note, then a rest
static std::vector<double> phrase(int n) {
    std::vector<double> dry(n, 0.0);
    const double notes[8] = { 110.0, 164.81, 220.0, 196.0, 146.83, 220.0, 261.63, 196.0 };
    static toro::Shared sh;
    const double tp[8] = { 0.06, 0.25, 0.4, 0.2, 0, 0, 0, 0.5 };
    opxy::i32 tparams[8];
    for (int i = 0; i < 8; ++i) tparams[i] = (opxy::i32)(tp[i] * 2147483647.0);
    for (double bar = 0; bar * 16 * STEP < n / SR; bar += 1) {
        for (int s = 0; s < 9; ++s) {
            const double t = (bar * 16 + s) * STEP, len = s == 8 ? STEP * 1.8 : STEP * 0.6;
            const double amp = s == 8 ? 0.7 : (s % 2 ? 0.22 : 0.8);
            const double hz = s == 8 ? notes[(int)bar % 8] : notes[(s + (int)bar) % 8];
            static toro::Voice v;
            toro::initialize(v, sh, 1);
            toro::start(v, sh, 1);
            opxy::u32 pitch[64];
            opxy::i32 out[64];
            for (int i = 0; i < 64; ++i) pitch[i] = (opxy::u32)(hz / SR * 4294967296.0);
            const int s0 = (int)(t * SR) / 64 * 64, ln = (int)(len * SR), rel = (int)(0.08 * SR);
            for (int b = s0; b < s0 + ln + rel && b + 64 <= n; b += 64) {
                toro::render(v, sh, 1, out, tparams, pitch);
                for (int i = 0; i < 64; ++i) {
                    const int a = b + i - s0;
                    double env = a < 100 ? a / 100.0 : 1.0;
                    if (a > ln) env *= std::exp(-(a - ln) / (0.02 * SR));
                    dry[b + i] += out[i] / 2147483648.0 * env * amp;
                }
            }
        }
    }
    double pk = 1e-9;
    for (double x : dry) pk = std::fmax(pk, std::fabs(x));
    for (double& x : dry) x *= 0.5 / pk;   // the phrase peaks at -6 dBFS
    return dry;
}

static void w32(FILE* f, uint32_t x) { std::fwrite(&x, 4, 1, f); }
static void w16(FILE* f, uint16_t x) { std::fwrite(&x, 2, 1, f); }

int main(int argc, char** argv) {
    const bool demo = argc == 4 && !std::strcmp(argv[1], "demo");
    const bool fixed = argc == 13 && !std::strcmp(argv[1], "const");
    if (!demo && !fixed) {
        std::fprintf(stderr, "usage: scope demo <out.wav> <peaks.txt> | scope const <p0..p8> <seconds> <peaks.txt>\n");
        return 2;
    }
    const int sections = sizeof(DEMO) / sizeof(DEMO[0]);
    const double seconds = demo ? sections * SEC : std::atof(argv[11]);
    const int n = (int)(seconds * SR) / WINDOW * WINDOW;
    std::vector<double> dry = phrase(n);
    double fixed_v[9] = {};
    if (fixed) for (int k = 0; k < 9; ++k) fixed_v[k] = std::atof(argv[2 + k]);

    static clew::State st;
    clew::initialize(st);
    std::vector<int16_t> wav(demo ? 2 * n : 0);
    FILE* peaks = std::fopen(argv[demo ? 3 : 12], "w");
    if (!peaks) return 1;
    double in_pk = 0, out_pk = 0;
    for (int b = 0; b < n; b += 64) {
        const double* v = demo ? DEMO[std::min(sections - 1, (int)(b / SR / SEC))].v : fixed_v;
        opxy::i32 p[9], l[64], r[64];
        for (int k = 0; k < 9; ++k) p[k] = (opxy::i32)(v[k] * 2147483647.0);
        for (int i = 0; i < 64; ++i) {
            l[i] = r[i] = (opxy::i32)(dry[b + i] * 2147483647.0);
            in_pk = std::fmax(in_pk, std::fabs(dry[b + i]));
        }
        clew::process(st, opxy::Buffer{ words, clew::kWords }, opxy::Transport{ 1200u, 0u, true }, l, r, p);
        for (int i = 0; i < 64; ++i) {
            const double ol = l[i] / 2147483648.0, orr = r[i] / 2147483648.0;
            out_pk = std::fmax(out_pk, std::fmax(std::fabs(ol), std::fabs(orr)));
            if (demo) { wav[2 * (b + i)] = (int16_t)(ol * 32767); wav[2 * (b + i) + 1] = (int16_t)(orr * 32767); }
        }
        if ((b + 64) % WINDOW == 0) {
            std::fprintf(peaks, "%.4f %.4f\n", in_pk, out_pk);
            in_pk = out_pk = 0;
        }
    }
    std::fclose(peaks);
    if (demo) {
        FILE* f = std::fopen(argv[2], "wb");
        if (!f) return 1;
        std::fwrite("RIFF", 1, 4, f); w32(f, 36 + n * 4); std::fwrite("WAVEfmt ", 1, 8, f); w32(f, 16); w16(f, 1); w16(f, 2);
        w32(f, 44100); w32(f, 44100 * 4); w16(f, 4); w16(f, 16);
        std::fwrite("data", 1, 4, f); w32(f, n * 4); std::fwrite(wav.data(), 2, wav.size(), f);
        std::fclose(f);
    }
    return 0;
}
