# Clew · handoff

For whoever writes `machines/clew/display.cpp`, `panel.svg.fragment` and `nodes.h`. The frames in `frames/` are
authored in the device's structure, so the artwork is `frames/rest.svg` with its preview groups removed; generate it
from `gen_clew.py` rather than editing it by hand. Every number below comes from `pose()` in `gen_clew.py`, which is
the reference: if this file and `pose()` disagree, `pose()` wins and this file gets fixed.

The design is pass 05 v2: one wave under a compressor line that steps down, one step per encoder column.

## What the page can and can't see

An effect page's input holds `slots` (all eight controls as Q31), `shift`, `choices` (Order), `elapsed`, `track` and
`reduced_motion`. It has no notes, levels or tempo, so the picture is drawn from the settings alone and nothing moves
unless a control does. Don't read `held_notes` or the note serials: they're 0 on a send.

## `definition.json`

```json
"display": {"stateBytes": 64, "stateAlignment": 4,
            "paths": 4, "points": 64, "nodes": 202, "texts": 16, "palette": 4}
```

## Coordinates

- The wave's centre line is y 150. Columns run from x `6 + 117k`, k = 0..4 (6, 123, 240, 357, 474).
- Column k's step is tread k; risers sit at the column edges x 123, 240, 357.
- Controls as 0..1: squeeze `sq`, echo `e`, space `sp`, blend `b`, motion `m`, dry `d`, attack `a`; tone `t` is
  -1..+1 (bipolar); Order `fx` is 1 for FX first.

## Node map

| index | part | driven by | channel |
| --- | --- | --- | --- |
| path 0 | the first swell (the playing), column 0 | Dry, Attack, Squeeze | shape |
| paths 1–3 | the repeat swells, columns 1–3 | Echo, Blend, Tone (2–3 only), Squeeze, Order | shape |
| 4–11 | header bars | `page_header()` | the SDK's |
| 12–171 | tread cells: tread t, cell j, variant v at `12 + (t·10 + j)·4 + v` | Squeeze, Motion, Space, Blend, Tone, Attack, Order | position; one variant shown |
| 172–201 | riser segments: riser r, segment s at `172 + r·10 + s` | follows the treads | position; spare ones hidden |

Cell variants, each authored at the cell's left end on the tread line (a cell is 11.7 px wide): v0 a flat 1.5 px
ribbon (`P_TREAD`); v1–v3 arches of 2.5 / 4.5 / 7.0 px (`P_RIPPLE`), up on even j and down on odd j. Show one
variant and hide the other three; a cell only ever translates. Riser segments are 1.5 × 4 px.

## The pose, step by step

**Steps.** `base = 64 − 40·sq`. Tread k's limit is `max(5, base·0.82^k)`; its y is `150 − limit`, plus Motion's
stagger `7·m` (down on odd k, up on even k > 0), rounded to a whole pixel.

**Ripple.** `reach = round(10·(0.2 + 0.6·sp)·(1 − 0.5·max(0, −t)))` cells at each tread's far end, none when
`sp ≤ 0.02`. Arch size `amp = 1 + 2·sp`, capped at 1 with FX first. Along the tail, `u = (j − first + 1)/reach`:
the cell drops `42·b·u` px (0 with FX first), never lower than `150 − 8 − 6u`, and its variant is
`clamp(round(amp·(0.5 + 0.5u)) + lift, 1, 3)` where `lift` is 1 when `t > 0.33`; when `t < −0.33` only every
other cell of the tail ripples (the rest stay flat). Cells before the tail are v0.

**Attack.** In tread 0, hide every cell whose left end is within `3 + 40·a` px of x 6: the step starts late.

**Risers.** From the last cell of tread k to tread k+1's y, 4 px segments stacked from the top, up to 10, the last
one pulled up to end on the lower step; none when the gap is under 3 px (the steps meet). Hide the rest.

**Swells.** Standing sizes from the settings: `level = min(1, 8e)·0.8`, `fb = 0.15 + 0.6e`; sizes
`[d, level, level·fb, level·fb²]`, scaled by 40 for column 0 and 36 for the rest. Column k's 32 samples at
`x = COL_X[k] + 117·s/31`, `dx = x − COL_X[k]`:

```
rise  = 5 (column 0) or 5 + 30·b (repeats)
env   = max(1.2, size · (1 − exp(−dx/rise)) · exp(−0.012·dx))
cyc   = 5 for columns 0 and 1; round(5 + t) for columns 2 and 3
v     = env · sin(2π · cyc · dx / 117)
if column 0 and dx < 3 + 40·a:  v ·= 1.6            (the start that escapes the squeeze)
else: v = soft(v, max(2, lim − 2)), lim = tread k's limit, or min(that, 10) on columns 1–3 with FX first
point = (x, 150 − v), then the same points 1 px lower in reverse: a closed 64-point ribbon
```

`soft(v, L)` passes `|v| ≤ 0.6L` and bends the rest: `0.6L + over/(1 + over/(0.4L))` with the sign kept. Place each
path at its column's centre (`COL_X[k] + 58.5`, 150) with points relative to it, which keeps them inside ±64 px.
Every column starts and ends on a zero crossing, so the four paths join without a step.

## Palette

| entry | name | fill / stroke | width | for |
| --- | --- | --- | --- | --- |
| 0 | `P_WAVE` | none / `#969696` | 1.5 | paths 1–3 |
| 1 | `P_WAVE_DRY` | none / `#CDCDCD` | 2.0 | path 0, the one brightest element |
| 2 | `P_TREAD` | `#969696` / `#969696` | 0.3 | flat cells |
| 3 | `P_RIPPLE` | `#7D7D7D` / `#7D7D7D` | 0.3 | arches |

Riser segments carry their own `#969696` fill (they're nodes, not palette entries); the floor (x 6–474, y 205.5–206.5, `#4B4B4B`) is static and unbound.

## Text slots

0–15 are the two-page header's (`page_header()`, slots in column order). Captions: amounts with `header_amount`;
Echo as the division name (`1/32 3/64 1/16 3/32 1/8 3/16 1/4 1/2`, `off` at 0); Tone signed (`-100`..`+100`, `0`);
Attack in ms with one decimal (`0.5`..`30.0`, mapping `0.5·60^a`). While `shift` is 1, the edited row (`line`) shows
`order` and `comp` / `fx` in its first column and leaves the other three empty (as the stock header does on a
page with a Shift row; frame `shift-order-fx.svg`). The helper doesn't do this, so write those slots after it.

## `DisplayState` (64 bytes)

| member | bytes | what |
| --- | --- | --- |
| `PageHeader header` | 20 | the SDK helper's state |
| `i32 shown[9]` | 36 | eight controls and Order as Q16 0..1, eased towards `slots` / `choices` |
| `u32 track, initialized` | 8 | snap on the first frame and on a track change |

Each frame: ease every `shown` value towards its target with the header's curve (halve the distance every 21 ms,
settled at 0.15 s), or snap when `!initialized`, the track changed or `reduced_motion` is set. Then run the pose on
`shown`. When every value equals its target, nothing changes and the frame writes nothing.

## Path key policy

Key each path by the eased values that shape it, never by `elapsed`:

| path | key from |
| --- | --- |
| 0 | Dry, Attack, Squeeze |
| 1 | Echo, Blend, Squeeze, Order |
| 2, 3 | Echo, Blend, Tone's cycle count, Squeeze, Order |

A nonzero key, as the SDK requires (add 1).

## Budget

0 changed nodes at rest. Turning a control: Squeeze is the heaviest, 12.3 a frame on average when turned slowly and
40.5 (peak 46) when turned fast, only while the knob moves; Order switches 32 nodes once. Run
`python3 gen_clew.py budget` after any change.

## Open device checks

From `review.md`, all **pending device**:

- Photos at rest and at the heaviest setting (Squeeze turning fast); there's no playing state.
- The redraw cost of turning Squeeze fast.
- Seams where risers meet steps and where cells meet each other.
- Header captions measured in Univers Next Pro Light (`3/64`, `30.0`, `comp`).
- The Shift row in the edited header row while Shift is held.
