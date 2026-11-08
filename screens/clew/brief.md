# Clew · screen brief

> Copy to `screens/<machine-id>/brief.md`. Fill phase by phase; don't skip a gate. Protocol: `opxy/protocol.md`.

## 0 · Screen or stock page?

- Subject in one sentence: the playing and its tails (the echoes and the room), and how the playing holds the tails down. Clew has one object the sound acts on, the space around what comes in, and every control changes it, so it earns a page of its own.

## 1 · Intake

| | |
| --- | --- |
| Machine id | `clew` |
| Kind | effect (the SDK contract) |
| Category | effect (`opxy/categories.md`) |
| Colour | grey (default; `colour_policy`: grey only) |
| Sounds like | A compressor that evens out a track, into a tempo-synced delay and a small room. With Blend up the echoes and room duck under the playing and swell back into the gaps. |
| Controls | 8, two pages (`press: page`), plus a Shift row of one enum (Order) |
| Control source | existing XY definition, `machines/clew/definition.json` (new machine, so 1A is skipped) |

### Colour roles (only when the harness allows colour)

Skip for grey machines. Two to four hues, each with one job; the grey column is what `panel.grayscale.svg.fragment` uses, and the last column is the cue that still separates them without colour.

| role | colour | its grey | cue besides colour |
| --- | --- | --- | --- |
| | | | |

### 1A · Port map (skip if an XY definition already exists)

| source control | source range / curve / default | XY slot | label | mapping | display | default | fate | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | keep / split / merge / drop | |

Integer conversion (e.g. OP-1 0..32767 from the top 15 bits of Q31): …

### 1B · Definition review

`lint_definition` (MCP) → 0 errors, 1 warning, 2 notes. Warnings resolved or justified:

| warning | resolution |
| --- | --- |
| `Attack` looks like an envelope control | Kept: it's the compressor's and the ducking's own time constant, not a note envelope; no stock module sets how fast a send's compressor catches a note. |
| note: no presets | To add with the screen work: Clean (defaults), Bloom, Slap, Hall, Pump. |
| note: effect resources | `bufferBytes` 367,868 and `transport` 1, checked by `sdk.py test`. |

| check | verdict | reason |
| --- | --- | --- |
| Names say what rises clockwise | pass | Squeeze, Echo, Space, Blend, Motion, Dry, Attack all rise; Tone is bipolar (dark ← 0 → thin). |
| Header values in real units, ≤ ~5 chars | change | Echo's dotted lengths would read `1/16.` (5 chars, ~64 px). On Clew's own page the header writes them as fractions (`3/64`, `3/32`, `3/16`), all ≤ 4 chars. Attack as `0.5`–`30` ms. |
| Defaults plainest useful; presets sound good (by ear) | pending device | Defaults are a light glue with a short echo and room (Squeeze 35, Echo 1/8, Space 35, Blend 50, Motion 20); presets pending. |
| Engine page holds only the sound's own parameters | pass | Attack justified above. |
| Page 1 holds what's played most | pass | Squeeze, Echo, Space, Blend; they're also the four the send LFOs reach. |
| Port parity: nothing silently lost | n/a | New machine. |
| Saved sounds compatible (if released) | n/a | Unreleased. |
| `id` final | pending owner | `clew` is a working name. |

### Captions

| # | label (≤ 8, lower) | range | unit | default | caption at 0 / 50 / 100 | est. width @20px | fits 53px? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | squeeze | 0–100 | % | 35 | 0 / 50 / 100 | 3 × 12.8 = 38 | yes |
| 2 | echo | 1/32–1/2 | note length | 1/8 | 1/32 / 1/8 / 1/2 (dotted as 3/64, 3/32, 3/16) | 4 × 12.8 = 51 | yes |
| 3 | space | 0–100 | % | 35 | 0 / 50 / 100 | 38 | yes |
| 4 | blend | 0–100 | % | 50 | 0 / 50 / 100 | 38 | yes |
| 5 | tone | -100–+100 | | 0 | -100 / 0 / +100 | 51 | yes |
| 6 | motion | 0–100 | % | 20 | 0 / 50 / 100 | 38 | yes |
| 7 | dry | 0–100 | % | 100 | 0 / 50 / 100 | 38 | yes |
| 8 | attack | 0.5–30 | ms | 5 | 0.5 / 3.9 / 30 | 38 | yes |
| S | order | 2 choices | | comp first | comp / fx | 4 × 12.8 = 51 | yes |

Width estimate: characters × 0.64 × 20. Measured in Univers Next Pro Light: pending device.

Page 1 (played most): squeeze, echo, space, blend · Page 2: tone, motion, dry, attack · Shift: order · Repeated controls: none

## 2 · Listen and rank

| # | audible effect across 0 → 100 | score 1–5 |
| --- | --- | --- |
| 1 | Squeeze: from untouched to a 24 dB spread closed to ~3 dB (host test) | 4 |
| 2 | Echo: from no repeats to long, many repeats; time steps through note lengths | 5 |
| 3 | Space: from dry to a 3 s tail | 4 |
| 4 | Blend: tails steady → 10 dB ducked while playing; only heard with Echo or Space up | 3 |
| 5 | Tone: tails darker or thinner; the dry is untouched | 3 |
| 6 | Motion: a gentle wobble in the echoes and room | 2 |
| 7 | Dry: the track's own level in the box, full to none | 4 |
| 8 | Attack: how much of each note's start gets through before the squeeze | 2 |
| S | Order: whether the tails pump with the playing | 2 |

Scored from the DSP and the host tests, not by ear on a device: to confirm with the owner.

## 3 · Subject

Five candidates, one per direction from `design_pass_start` (or by hand: five different pattern × drawing-language pairs that fit the category). Pass record: `passes/01-subject/pass.json`.

| candidate | pattern | drawing language | subject in one sentence | what each control moves | verdict |
| --- | --- | --- | --- | --- | --- |
| v1 | P4 | patent section | A stack of glass echo plates in section, receding into the screen: the front plate is the playing, held in a clamp, and each plate behind is one repeat, set back by the delay time, with the room as a hatched back wall the stack fades into. | Squeeze: the clamp's jaws close on the front plate and press its height down, from loose to tight. Echo: the plates' spacing is the note length (1/32 close, 1/2 far apart) and more plates stand as the repeats grow; at 0 only the front plate. Space: the back wall recedes and gains hatching lines, from none to a deep, dense wall. Blend: while playing, the plates behind the front one sink down out of the light; in the gaps they rise back. Tone: the plates taper with depth: steeply (dark, top cut away) to the left, squarer to the right. Motion: the plates sway left and right out of line with each other. Dry: the front plate's height, down to a thin sliver at 0. Attack: the clamp's lead-in bevel: long and gradual at slow attack, short and sharp at fast. Order (Shift): the clamp moves from the front plate to around the whole stack. | Plates in a stack can read as a wavetable display rather than echoes; a clamp is close to an icon if drawn loosely. |
| v2 | P10 | hidden-line isometric | An isometric floor of slabs as the room: a note lands as a raised block at the front, its echoes are rows of lower blocks marching back across the floor at the delay spacing, and the reverb is a fine low relief that spreads from them. | Squeeze: every block's height is clipped to a plateau that comes down as it rises, so tall and short notes even out. Echo: the rows' spacing is the note length and their count the repeats; 0 leaves the floor flat behind the note. Space: how far the relief spreads across the floor and how slowly it flattens. Blend: while playing, the echo rows and relief sink into the floor; in the gaps they rise again. Tone: the relief's fine detail: rough, many small bumps to the right, smooth broad swells to the left. Motion: the echo rows bend sideways in a slow S across the floor. Dry: the note's own front block, from full height to flush with the floor. Attack: the plateau's edge: a soft ramp into the clip at slow attack, a hard step at fast. Order (Shift): with FX first the plateau also caps the echo rows and relief, not only the note's block. | Close to toro's look, so the two machines may read as one; field-wide sinking on every note is costly in redraw. |
| v3 | P15 | star atlas | A star chart of the send: the playing is a bright star plotted on the left, each echo a fainter star repeated along a dotted ecliptic at the delay spacing, and the room a scatter of square cell-stars around them, labelled like an atlas plate. | Squeeze: the main star's magnitude marks pull in, so loud and soft notes plot the same size. Echo: the copies' spacing along the ecliptic is the note length and their count the repeats. Space: how many cell-stars fill the field and how far they spread. Blend: while playing the copies and cells dim to faint; in the gaps they brighten back. Tone: the cell-stars' grain: single fine points to the right, clumped runs to the left. Motion: the ecliptic wavers, its dotted line bending. Dry: the main star's size, down to a hollow ring at 0. Attack: the main star's halo: tight at fast attack, a soft wide ring at slow. Order (Shift): the atlas plate's label switches between COMP FIRST and FX FIRST, and the magnitude marks move to the whole field. | Brightness-only changes (Blend, Space) lean on shade; an atlas with no sky subject is decoration. |
| v4 | P1 | engineering schematic | A cutaway schematic of one box: a gain valve the playing passes through, a tape loop with a moving playback head for the echoes, and a coil spring tank for the room, linked by a single lever from the level follower that dips the tape and spring outputs while playing. | Squeeze: the valve's gate closes across the signal path, from fully open to a narrow slot. Echo: the playback head slides along the tape away from the record head; the distance is the note length, and more loops of tape show as repeats grow; at 0 the head lifts off. Space: the spring stretches and gains coils, from a short stub to a long tank. Blend: the follower's lever tips further while playing, pressing the tape and spring outputs down; it lifts in the gaps. Tone: a damper pad moves onto the spring and tape, from touching hard (dark) to clear and then a thin felt (bright). Motion: the tape's guide roller swings, wavering the tape path. Dry: a bypass link from input to output thickens from absent to full width. Attack: the lever's spring: a stiff short spring at fast attack, a long soft one at slow. Order (Shift): the valve slides from before the tape and spring to after them on the path. | Many parts to fit in 480 x 220 at legible weights; three mechanisms may compete for the brightest element. |
| v5 | P13 | oscilloscope trace | The rule drawn as a scope: the playing's level is a bright envelope trace across the screen and the tails are a second, finer trace held beneath it, captured under the playing while it's loud and rising into the space it leaves in the gaps. | Squeeze: a threshold line drops and the bright trace's peaks flatten against it. Echo: decaying copies of each peak repeat to the right at the note length's spacing. Space: the fine trace's tail stretches longer and smoother after each peak. Blend: how far the bright trace pushes the fine one down where they overlap. Tone: the fine trace's grain: jagged high detail to the right, smooth to the left. Motion: the echo copies drift a little early and late around their spacing. Dry: the bright trace's height, down to a flat line at 0. Attack: the slope of the flattening at each peak's start: a sharp corner at fast attack, a rounded lead-in at slow. Order (Shift): the threshold line extends under the fine trace too. | Outside the effect column for P13: its case is that Clew's rule (the playing holds the tails down) is itself a capture; but a scope trace is P3's ground, and two traces may read as a meter. |

Chosen: pending the owner's pick (uniqueness check passed: every pair differs in pattern and language, word overlap ≤ 0.12).

## 4 · Map and budget

| # | score | channel | part (node) | travel 0 → 100 | what the player sees |
| --- | --- | --- | --- | --- | --- |
| 1 | | | | | |

```json
"display": {"stateBytes": 0, "stateAlignment": 4,
            "paths": 0, "points": 0, "nodes": 0, "texts": 0, "palette": 0}
```

| case | changed nodes / frame |
| --- | --- |
| at rest | 0 |
| playing, defaults | |
| playing, heaviest setting (name it) | avg … · peak … |
