# Clew · handoff

For whoever writes `machines/clew/display.cpp`, `panel.svg.fragment` and `nodes.h`. The frames in `frames/` are
authored in the device's structure, so the artwork is `frames/rest.svg` with its preview groups removed; generate it
from `gen_clew.py` rather than editing it by hand. `pose()` in `gen_clew.py` is the reference: if this file and
`pose()` disagree, `pose()` wins and this file gets fixed.

The design is pass 05 v2 with the wave as the audio: Clew's output scrolling from right to left, a compressor line
stepping over it (one step per encoder column) that comes down onto what's loud, and the room rippling on each
step's tail.

## The SDK change it needs first

An effect page's input has `slots`, `shift`, `choices`, `elapsed`, `track` and `reduced_motion`, and no audio.
This design needs the send's levels, so it waits for an open-xy pull request (against `staging`) that adds them.
What I'd propose there:

- **What:** for each send (14, 15), the peak of the effect's input and of its output over every 22 blocks
  (1408 samples, 31.9 ms), the last 64 of each, and a running count of windows.
- **Where it's measured:** in the platform's effect wrapper (`sdk/platform/opxy-1.2.1/fx_object.cpp.in`), around
  the effect's `process`: the input's peak before it, the output's after. That's two compares per sample on the
  audio thread and a word written per window, with no allocation, locks or calls.
- **How the page gets it:** `send_controls()` in `screen.hpp` copies the ring into the page's input, as it does the
  slots. A torn read costs one window's peak for one frame, so it needs no lock.
- **Input fields (proposal):** `u8 level_in[64]`, `u8 level_out[64]` (peak × 255 of full scale, oldest first) and
  `u32 level_head` (windows so far). 132 bytes. Synth pages read zeros.
- Like every SDK change, it needs its own docs (`docs/display.md`, Effect pages), a test, the firmware build and
  release verification, and the maintainer's review.

Until it lands, `sim/scope.cpp` writes the same numbers from the engine code on a computer.

## `definition.json`

```json
"display": {"stateBytes": 64, "stateAlignment": 4,
            "paths": 4, "points": 64, "nodes": 202, "texts": 16, "palette": 4}
```

## Coordinates

- The wave's centre line is y 150. Columns run from x `6 + 117k`, k = 0..4 (6, 123, 240, 357, 474).
- The screen shows the last 60 windows (about 1.9 s), 15 per column, oldest at the left.
- `in[i]`, `out[i]`: those windows' peaks, 0..1 (`level / 255`). Controls as 0..1: `sq`, `sp`, `b`, `m`, `a`;
  `t` is Tone, -1..+1; `fx` is 1 for FX first.

## Node map

| index | part | driven by |
| --- | --- | --- |
| paths 0–3 | the wave, one per column; path 3 is the newest | `out` |
| 4–11 | header bars | `page_header()` |
| 12–171 | step cells: step k, cell j, variant v at `12 + (k·10 + j)·4 + v` | Squeeze, `in`, `out`, Space, Blend, Tone, Attack, Motion, Order |
| 172–201 | riser segments: riser r, segment s at `172 + r·10 + s` | follows the steps |

Cell variants, each authored at the cell's left end on the step line (11.7 px wide): v0 a flat 1.5 px ribbon
(`P_TREAD`); v1–v3 arches of 2.5 / 4.5 / 7.0 px (`P_RIPPLE`), up on even j and down on odd j. Show one variant, hide
the other three; a cell only translates. Riser segments are 1.5 × 4 px.

## The pose, step by step

**Steps.** `thr = −3 − 30·sq` dB, `ratio = 1 + 7·sq`. For column k: `gr = max(0, 20·log10(max(in[15k..15k+14])) −
thr)·(1 − 1/ratio)`; `top = 60·max(out[15k..15k+14]) + 3`; `limit = max(5, top, (64 − 40·sq)·0.9^k − 1.2·gr)`,
rounded to 4 px. The step's y is `150 − limit`, plus Motion's stagger `7·m` (down on odd k, up on even k > 0).

**Ripple.** `reach = round(10·(0.2 + 0.6·sp)·(1 − 0.5·max(0, −t)))` cells at each step's end, none when
`sp ≤ 0.02`. Per column, `room = sp·mean(out[15k+10..15k+14])`, `amp = 3·min(1, 6·room)` (at most 1 with FX first);
`duck = min(1, 3·max(in[15k+11..15k+14]))`; `walk = (frame + ⌊3k/2⌋) / 6`. Along the tail, `u = (j − first + 1) /
reach`: the cell drops `28·b·u·duck` px (0 with FX first), never below `150 − 8 − 6u`. It shows an arch when
`amp ≥ 0.5` and `(j − first + walk) mod (2·every) = 0` (`every` is 2 when `t < −0.33`, else 1), of variant
`clamp(round(amp·(0.5 + 0.5u)) + lift, 1, 3)` with `lift` 1 when `t > 0.33`. Other cells are v0.

**Attack.** Hide each step's cells whose middle is within `3 + 40·a` px of its column's left edge.

**Risers.** From the last cell of step k to step k+1's y, 4 px segments from the top, up to 10, the last pulled up to
end on the lower step; none when the gap is under 3 px. Hide the rest.

**Wave.** Column k's 32 samples at `x = 6 + 117k + 117·s/31`, window position `w = 15k + 15·s/31 − 0.5`:

```
env = 60 · lerp(out, w)                              (between the neighbouring windows)
v   = env · sin(2π · (head − 59 + w) / 4)            (cycles of 4 windows, fixed to the audio so they scroll)
if x − colLeft ≥ 3 + 40·a:  v = soft(v, max(2, limit − 1))
point = (x, 150 − v), then the same points 1 px lower in reverse: a closed 64-point ribbon
```

`soft(v, L)` passes `|v| ≤ 0.6L` and bends the rest: `0.6L + over/(1 + over/(0.4L))`, sign kept. Place each path at
its column's centre (`6 + 117k + 58.5`, 150) with points relative to it. In silence every `out` is 0 and the wave is a
flat line.

## Palette

| entry | name | fill / stroke | width | for |
| --- | --- | --- | --- | --- |
| 0 | `P_WAVE` | none / `#969696` | 1.5 | paths 0–2 |
| 1 | `P_WAVE_NOW` | none / `#CDCDCD` | 2.0 | path 3, the newest audio: the one brightest element |
| 2 | `P_TREAD` | `#969696` / `#969696` | 0.3 | flat cells |
| 3 | `P_RIPPLE` | `#7D7D7D` / `#7D7D7D` | 0.3 | arches |

Riser segments carry their own `#969696`; the floor (x 6–474, y 205.5–206.5, `#4B4B4B`) is static.

## Text slots

0–15 are the two-page header's (`page_header()`). Captions: amounts with `header_amount`; Echo as the division name
(`1/32 3/64 1/16 3/32 1/8 3/16 1/4 1/2`, `off` at 0); Tone signed; Attack in ms with one decimal (`0.5·60^a`). While
`shift` is 1, the edited row (`line`) shows `order` and `comp` / `fx` in its first column and leaves the other three
empty (frame `shift-order-fx.svg`); write those slots after the helper.

## `DisplayState` (64 bytes)

| member | bytes | what |
| --- | --- | --- |
| `PageHeader header` | 20 | the SDK helper's state |
| `i32 shown[9]` | 36 | eight controls and Order as Q16 0..1, eased towards `slots` / `choices` |
| `u32 track, initialized` | 8 | snap on the first frame and on a track change |

Each frame: ease the controls (halve the distance every 21 ms) or snap on the first frame, a track change or
`reduced_motion`; read the levels; run the pose. The levels are read fresh each frame, so they need no state. With
`reduced_motion`, redraw the wave once a second instead of every frame and keep `walk` at 0.

## Path keys

Each wave path's key is `level_head` plus one while any of its 15 windows (and the ones either side, for the
interpolation) is above 0, and stays at its last value once they're all 0, so silence redraws nothing. Never key by
`elapsed`.

## Budget

`python3 gen_clew.py budget`: 0 at rest; 18.4 a frame on average while the phrase plays at the defaults (peak 38);
22.9 at Space 100 (peak 51); 23.2 at Space and Squeeze 100 (peak 53).

## Open checks

- **Pending SDK:** the levels on the page.
- **Pending device:** photos at rest, playing and Space 100; the redraw cost while playing; seams where risers meet
  steps; header captions in Univers Next Pro Light (`3/64`, `30.0`, `comp`); the Shift row in the edited header row.
