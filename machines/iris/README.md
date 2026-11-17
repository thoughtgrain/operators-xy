# iris

A new OP-XY synth engine, not a port. Four waveforms play at one pitch, sine, triangle, square and saw, in order of how many harmonics they carry, like the bands of a rainbow from red to violet. A mixing window slides along them and opens up to let the neighbours bleed in. It's named for Iris, the goddess of the rainbow.

| The page | | The Shift row (hold Shift) | |
|---|---|---|---|
| Morph | where the window sits: sine → triangle → square → saw | Skew (Shift + encoder 1) | one breakpoint: the sine and triangle lean, the square narrows to a pulse (the saw has nothing to lean) |
| Overlap | how wide the window is: a crossfade between two neighbours → all four at once | Phase (Shift + encoder 2) | each band slips up to an eighth of a cycle behind the one before; only heard where bands overlap |
| Spread | detunes the bands apart, outer ones ±50 cents, so they beat | | |
| Tone | a low-pass that follows the note, from almost a sine to fully open | | |

There's one header row. Holding Shift swaps its contents for skew and phase (encoders 3 and 4 have nothing on the row), and letting go puts the page back. That needs SDK 1.13, for the synth Shift row (`synth_shift` in `definition.json`). The engine reads skew and phase as `p[4]` and `p[5]`, after the page's four.

## How the sound works

The engine is in `engine.cpp` and the voice state in `core.h`. It's integer-only, like toro, and every division happens once per block, never inside the sample loop.

- **The mix.** Each band's weight is a triangle kernel around Morph's position, as wide as Overlap says (1 to 4 bands). I renormalise the weights so they always sum to one, which means opening Overlap thickens the sound without making it louder. The weights are also ramped across each 64-sample block, so sweeping Morph doesn't zipper.
- **Level.** I trim the bands to a similar loudness (sine ×0.82, square ×0.6), so Morph changes the colour and not the volume. The test holds every band within 3 dB of the triangle.
- **Skew.** I warp the phase at one breakpoint, which leaves the waves lopsided. The DC that adds is known exactly for each band (2b − 1 times the half-wave's mean), so I subtract it there rather than adding a high-pass that would thump on note starts.
- **Phase.** Each band is offset by up to an eighth of a cycle. My first version used quarter steps, and that cancels four equal bands' fundamental outright (about −11 dB), so I halved it.
- **Tone.** It's key-tracked, from 0.5 to 7.5 octaves above the note. It means "how many harmonics get through", which is exactly what the four bands differ in, and it doesn't go silent on high notes the way a fixed cutoff did.
- **Aliasing.** The square and saw are band-limited with a polynomial BLEP at each jump. The reciprocal comes from the block's first pitch, so the correction is a few multiplies.

## The screen

The screen is a rainbow. Four grey bands are the four waveforms going in, sine on the outside and saw on the inside, the way a real bow orders its wavelengths. One bright line is what comes out: the mix, worked out from the same maths as the engine, sitting at the radius Morph sets. The design, its frames and the handoff this code follows are in my operator-design repository, under `screens/iris/`.

| Control | What moves |
|---|---|
| Morph | the bright line walks inward across the bow and takes each band's shape in turn |
| Overlap | the bands pull in toward the bright line; at 100 they crowd it and their waves cross |
| Spread | each band's cycles stretch or shrink along its arc; the bright line swells and thins where the bands beat |
| Tone | the bright line's corners round off, and the inner bands' teeth melt into humps, band by band |
| Skew | the bright line leans; on the square it narrows to spikes |
| Phase | the bands slide along their arcs, and the bright line hollows where they overlap |
| a note | the bright line brightens and travels along the arc while a note is held, then settles |

How it fits the device: the bands are chains of one-cycle nodes (`gen_panel.py` authors one cycle per band, 16 copies, plus a rounded copy for when Tone cuts the band), which `display.cpp` only moves, turns and scales. The bright line is the four reshapable outlines, a quarter of the arc each, rewritten only when its key changes. So nothing redraws at rest, and while a note is held only those four outlines change. That's 140 nodes and 5 palette entries.

## Status

- **Sound.** `engine.cpp`, `core.h`, `definition.json`, `machine.json` and `tests/sound.cpp` are written, and the sound checks pass on the host. I built them against a small stand-in for `opxy/audio.hpp`, not the SDK itself, so the first `python sdk.py test --machine machines/iris` is still to do.
- **Screen.** `gen_panel.py`, `panel.svg.fragment`, `nodes.h`, `display.h` and `display.cpp` are written, and `tools/panel_lint.py` finds nothing. I ran `display()` on the host against a stand-in for the SDK's draw API, rendered the nodes it placed and compared them with the design frames. They match closely, and the design repo's perceptibility gate passes on that output. Some things come from reading toro, theseus and my design notes rather than the SDK headers, so check them first: `rotation()`'s sign (positive taken as clockwise on screen), `in.held_notes` as the held-note count, `Point` in Q10 px, and the Shift row (the `synth_shift` field's shape, `shift_row(in).values[]`, `page_header` with one row, and the Shift values arriving at the engine as `p[4]` and `p[5]`).
- **Not done yet.** Anything that needs a device: presets by ear, CPU, the redraw cost of rewriting four 64-point outlines every frame while a note is held, caption widths in the device font, and photos.
