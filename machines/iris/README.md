# iris

A new OP-XY synth engine, not a port. Four waveforms play at one pitch, sine, triangle, square and saw, in order of how many harmonics they carry, like the bands of a rainbow from red to violet. A mixing window slides along them and opens up to let the neighbours bleed in. It's named for Iris, the goddess of the rainbow.

| Page 1 | | Page 2 (press any encoder) | |
|---|---|---|---|
| Morph | where the window sits: sine → triangle → square → saw | Skew | one breakpoint: the sine and triangle lean, the square narrows to a pulse (the saw has nothing to lean) |
| Overlap | how wide the window is: a crossfade between two neighbours → all four at once | Phase | each band slips up to an eighth of a cycle behind the one before; only heard where bands overlap |
| Spread | detunes the bands apart, outer ones ±50 cents, so they beat | | |
| Tone | a low-pass that follows the note, from almost a sine to fully open | | |

## How the sound works

The engine is in `engine.cpp` and the voice state in `core.h`. It's integer-only, like toro, and every division happens once per block, never inside the sample loop.

- **The mix.** Each band's weight is a triangle kernel around Morph's position, as wide as Overlap says (1 to 4 bands). I renormalise the weights so they always sum to one, which means opening Overlap thickens the sound without making it louder. The weights are also ramped across each 64-sample block, so sweeping Morph doesn't zipper.
- **Level.** I trim the bands to a similar loudness (sine ×0.82, square ×0.6), so Morph changes the colour and not the volume. The test holds every band within 3 dB of the triangle.
- **Skew.** I warp the phase at one breakpoint, which leaves the waves lopsided. The DC that adds is known exactly for each band (2b − 1 times the half-wave's mean), so I subtract it there rather than adding a high-pass that would thump on note starts.
- **Phase.** Each band is offset by up to an eighth of a cycle. My first version used quarter steps, and that cancels four equal bands' fundamental outright (about −11 dB), so I halved it.
- **Tone.** It's key-tracked, from 0.5 to 7.5 octaves above the note. It means "how many harmonics get through", which is exactly what the four bands differ in, and it doesn't go silent on high notes the way a fixed cutoff did.
- **Aliasing.** The square and saw are band-limited with a polynomial BLEP at each jump. The reciprocal comes from the block's first pitch, so the correction is a few multiplies.

## Status

- `engine.cpp`, `core.h`, `definition.json`, `machine.json` and `tests/sound.cpp` are drafted. The sound checks pass on the host. I built them against a small stand-in for `opxy/audio.hpp`, not the SDK itself, so the first run of `python sdk.py test --machine machines/iris` is still to do.
- The screen comes from the design in operator-design `screens/iris/`, where the subject pass is open. `display.cpp`, `display.h`, `gen_panel.py`, `nodes.h` and `panel.svg.fragment` follow its handoff, and `resources.display` in `definition.json` is a placeholder until then.
- Defaults and presets (Arc, Glass, Prism, Reed, Bow, Hollow) are set from the DSP. I haven't heard them on a device yet.
