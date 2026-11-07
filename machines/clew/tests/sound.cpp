// Sound checks for Clew, compiled for the host and run by python sdk.py test --machine <folder>.
// They check: silence and an empty send stay silent, the buffer is cleared before it's read, the echo lands on the
// tempo's note length and Echo 0 has none, Squeeze evens out loud and quiet with Squeeze 0 transparent, Blend ducks
// the tails while playing and lets them back after, every tail decays, Tone darkens, Order matters, and the state
// fits.
#include "../fx.cpp"
#include <cmath>
#include <cstdio>
#include <vector>

static int failures = 0;
#define CHECK(ok, ...) do { if (!(ok)) { std::printf("FAIL: "); std::printf(__VA_ARGS__); std::printf("\n"); ++failures; } } while (0)

static opxy::i32 words[clew::kWords];
static opxy::i32 q(double f) { return static_cast<opxy::i32>(f * 2147483647.0); }

struct Settings {
    double squeeze = 0, echo = 0, space = 0, blend = 0, tone = 0.5, motion = 0, dry = 1, attack = 0.5624, order = 0;
    void words_into(opxy::i32* p) const {
        const double v[9] = { squeeze, echo, space, blend, tone, motion, dry, attack, order };
        for (int k = 0; k < 9; ++k) p[k] = q(v[k]);
    }
};

// Runs from initialize for `seconds`; input(n) feeds both sides. Returns left and right.
template <class Input>
static void run(const Settings& s, double seconds, Input input, std::vector<double>& l, std::vector<double>& r,
                unsigned bpm_x10 = 1200, bool with_buffer = true)
{
    static clew::State state;
    clew::initialize(state);
    opxy::i32 p[9]; s.words_into(p);
    const opxy::Buffer buffer{ with_buffer ? words : nullptr, with_buffer ? clew::kWords : 0u };
    const opxy::Transport transport{ bpm_x10, 0, true };
    const unsigned blocks = static_cast<unsigned>(seconds * 44100 / opxy::block_frames);
    opxy::i32 bl[opxy::block_frames], br[opxy::block_frames];
    l.clear(); r.clear();
    for (unsigned b = 0; b < blocks; ++b) {
        for (unsigned i = 0; i < opxy::block_frames; ++i) bl[i] = br[i] = q(input(b * opxy::block_frames + i));
        clew::process(state, buffer, transport, bl, br, p);
        for (unsigned i = 0; i < opxy::block_frames; ++i) { l.push_back(bl[i] / 2147483648.0); r.push_back(br[i] / 2147483648.0); }
    }
}
static double peak(const std::vector<double>& x, size_t a, size_t b) { double m = 0; for (size_t i = a; i < b && i < x.size(); ++i) m = std::fmax(m, std::fabs(x[i])); return m; }
static double rms(const std::vector<double>& x, size_t a, size_t b) { double m = 0; size_t n = 0; for (size_t i = a; i < b && i < x.size(); ++i, ++n) m += x[i] * x[i]; return n ? std::sqrt(m / n) : 0; }
static double db(double v) { return 20 * std::log10(v + 1e-12); }
static const size_t kSettle = 12 * opxy::block_frames + 64;        // the buffer clears in 12 blocks

int main()
{
    static_assert(sizeof(clew::State) <= opxy::effect_buffered_state_bytes - 4, "state with a shift row");
    std::vector<double> l, r;
    const double sr = 44100;
    auto sine = [](double hz, double a) { return [=](unsigned n) { return a * std::sin(2 * M_PI * hz * n / 44100.0); }; };
    auto silence = [](unsigned) { return 0.0; };
    auto click = [](unsigned at) { return [=](unsigned n) { return n == at ? 0.5 : 0.0; }; };

    /* silence in, silence out, at heavy settings; and an empty send is silent */
    {
        Settings s; s.squeeze = 1; s.echo = 1; s.space = 1; s.blend = 1; s.motion = 1;
        run(s, 1.0, silence, l, r);
        CHECK(peak(l, 0, l.size()) == 0 && peak(r, 0, r.size()) == 0, "silence should stay silent");
        run(s, 0.1, sine(220, 0.5), l, r, 1200, false);
        CHECK(peak(l, 0, l.size()) == 0, "outside a send the effect should write silence");
    }
    /* while the buffer clears, only the dry comes back, untouched by the compressor */
    {
        Settings s; s.squeeze = 1; s.echo = 1; s.space = 1;
        run(s, 0.01, sine(220, 0.5), l, r);
        bool same = true;
        for (size_t n = 0; n < 12 * opxy::block_frames && n < l.size(); ++n) if (std::fabs(l[n] - 0.5 * std::sin(2 * M_PI * 220 * n / sr)) > 1e-6) same = false;
        CHECK(same, "the first blocks should pass the dry only");
    }
    /* the echo: an eighth at 120 BPM lands 11025 samples later; Echo 0 has none */
    {
        Settings s; s.echo = 4.5 / 8; s.dry = 0;                      // division 4: an eighth
        const unsigned at = 2000;
        run(s, 1.0, click(at), l, r);
        size_t first = 0;
        for (size_t n = 0; n < l.size(); ++n) if (std::fabs(l[n]) > 0.01) { first = n; break; }
        CHECK(first >= at + 11025 - 2 && first <= at + 11025 + 2, "the eighth's repeat should land 11025 samples late (at %zu)", first > at ? first - at : 0);
        std::printf("echo: an eighth at 120 BPM repeats after %zu samples\n", first - at);
        run(s, 1.0, click(at), l, r, 1500);
        first = 0;
        for (size_t n = 0; n < l.size(); ++n) if (std::fabs(l[n]) > 0.01) { first = n; break; }
        CHECK(first >= at + 8820 - 2 && first <= at + 8820 + 2, "at 150 BPM the eighth should land 8820 samples late (at %zu)", first > at ? first - at : 0);
        s.echo = 0;
        run(s, 1.0, click(at), l, r);
        CHECK(peak(l, at + 600, l.size()) < 1e-6, "Echo 0 should leave no repeats (peak %g)", peak(l, at + 600, l.size()));
    }
    /* Squeeze: 24 dB between a loud and a quiet tone comes out much closer; at 0 it's untouched */
    {
        Settings s; s.squeeze = 1;
        run(s, 1.0, sine(220, 0.5), l, r); const double loud = rms(l, 22050, 44100);
        run(s, 1.0, sine(220, 0.5 / 15.85), l, r); const double quiet = rms(l, 22050, 44100);
        const double range = db(loud) - db(quiet);
        CHECK(range < 14, "Squeeze 100 should close 24 dB to under 14 (got %.1f)", range);
        s.squeeze = 0;
        run(s, 1.0, sine(220, 0.5), l, r); const double flat = rms(l, 22050, 44100);
        CHECK(std::fabs(db(flat) - db(0.5 / std::sqrt(2.0))) < 0.1, "Squeeze 0 should be transparent (%.2f dB off)", db(flat) - db(0.5 / std::sqrt(2.0)));
        std::printf("squeeze: 24 dB in comes out %.1f dB apart at 100; 0 is %.2f dB from unity\n", range, db(flat) - db(0.5 / std::sqrt(2.0)));
    }
    /* Blend: while a tone plays its tails sit well under where they'd be unducked; after it stops they come back */
    {
        auto burst = [](unsigned n) { return n < 66150 ? 0.3 * std::sin(2 * M_PI * 330 * n / 44100.0) : 0.0; };
        Settings s; s.echo = 4.5 / 8; s.space = 0.6; s.dry = 0;
        run(s, 3.0, burst, l, r); const double open_during = rms(l, 44100, 66150), open_after = rms(l, 83000, 92000);
        s.blend = 1;
        run(s, 3.0, burst, l, r); const double duck_during = rms(l, 44100, 66150), duck_after = rms(l, 83000, 92000);
        CHECK(db(open_during) - db(duck_during) > 10, "Blend 100 should duck the tails over 10 dB while playing (%.1f)", db(open_during) - db(duck_during));
        CHECK(db(open_after) - db(duck_after) < 6, "the tails should come back once the playing stops (%.1f dB under)", db(open_after) - db(duck_after));
        std::printf("blend: tails %.1f dB down while playing, %.1f dB down 0.4 s after\n", db(open_during) - db(duck_during), db(open_after) - db(duck_after));
    }
    /* every tail dies away, even at the longest room, the most repeats and FX first with full make-up; and the
     * output bends below full scale instead of clipping */
    {
        auto burst = [](unsigned n) { return n < 22050 ? 0.5 * std::sin(2 * M_PI * 220 * n / 44100.0) : 0.0; };
        Settings s; s.echo = 1; s.space = 1; s.motion = 1; s.dry = 0; s.squeeze = 1; s.order = 1;
        run(s, 16.0, burst, l, r);
        const double early = rms(l, 2 * 44100, 3 * 44100), late = rms(l, 15 * 44100, 16 * 44100);
        CHECK(db(early) - db(late) > 30, "the tails should fall over 30 dB from 2 s to 15 s (%.1f)", db(early) - db(late));
        const double top = peak(l, 0, l.size());
        CHECK(top < 0.999, "the output should stay below full scale (%.3f)", top);
        s.squeeze = 0; s.order = 0; s.echo = 0.6;
        run(s, 12.0, burst, l, r);
        CHECK(db(peak(l, 11 * 44100, 12 * 44100)) < -60, "a moderate echo and the longest room should be under -60 dB after 10 s");
        std::printf("decay: %.1f dB from 2 s to 15 s at the extremes; peak %.3f\n", db(early) - db(late), top);
    }
    /* Tone: the dark end takes the top off the tails */
    {
        auto noise = [](unsigned n) { unsigned x = n * 2654435761u; x ^= x >> 13; x *= 0x5bd1e995u; x ^= x >> 15; return n < 4410 ? ((x & 0xFFFF) / 32768.0 - 1) * 0.3 : 0.0; };
        auto top_end = [](const std::vector<double>& x, size_t a, size_t b) { double e = 0; for (size_t i = a + 1; i < b; ++i) e += (x[i] - x[i - 1]) * (x[i] - x[i - 1]); return e; };
        Settings s; s.space = 0.5; s.dry = 0;
        run(s, 1.0, noise, l, r); const double open = top_end(l, 4410, 30000) / (rms(l, 4410, 30000) + 1e-12);
        s.tone = 0;
        run(s, 1.0, noise, l, r); const double dark = top_end(l, 4410, 30000) / (rms(l, 4410, 30000) + 1e-12);
        CHECK(dark < open * 0.3, "Tone -100 should darken the tails (%.3g vs %.3g)", dark, open);
    }
    /* Order: compressing the tails too changes the result */
    {
        auto burst = [](unsigned n) { return n < 22050 ? 0.5 * std::sin(2 * M_PI * 220 * n / 44100.0) : 0.0; };
        Settings s; s.squeeze = 0.8; s.echo = 0.6; s.space = 0.5;
        run(s, 1.0, burst, l, r); const double first = rms(l, 22050, 44100);
        s.order = 1;
        run(s, 1.0, burst, l, r); const double second = rms(l, 22050, 44100);
        CHECK(std::fabs(db(first) - db(second)) > 1, "Order should change the tails (%.2f vs %.2f dB)", db(first), db(second));
    }
    /* Dry 0 with no Echo or Space is silent once the buffer is ready */
    {
        Settings s; s.dry = 0;
        run(s, 0.3, sine(220, 0.5), l, r);
        CHECK(peak(l, kSettle, l.size()) < 1e-6, "Dry 0 with nothing else should be silent");
    }
    if (!failures) std::printf("all Clew checks passed\n");
    return failures ? 1 : 0;
}
