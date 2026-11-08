# Clew · handoff

For whoever writes `machines/clew/display.cpp`, `panel.svg.fragment` and `nodes.h`. The frames in `frames/` are
authored in the device's structure, so the artwork is `frames/rest.svg` with its preview groups removed; generate it
from `gen_clew.py` rather than editing it by hand. `pose()` in `gen_clew.py` is the reference: if this file and
`pose()` disagree, `pose()` wins and this file gets fixed.

The design is pass 05 v2 as the owner picked it: one wave (the playing's swell on the first step, each repeat's on
the next) under a compressor line that steps down, one step per encoder column; the first step dips with the gain
reduction, the later ones with the ducking, and the room ripples along each step's tail.

## The SDK change it needs first

An effect page's input has `slots`, `shift`, `choices`, `elapsed`, `track` and `reduced_motion`, and nothing about
what's playing. This design needs it, so it waits for an open-xy pull request (against `staging`). What I'd propose:

- **What:** for each send (14, 15), the peak of the effect's input over every 22 blocks (1408 samples, 31.9 ms), the
  last 128 (about 4 s), a running count of windows, and the tempo the effect's `process` already gets
  (`Transport::bpm_x10`).
- **Where it's measured:** in the platform's effect wrapper (`sdk/platform/opxy-1.2.1/fx_object.cpp.in`), before
  the effect's `process`: one compare per sample and one byte written per window on the audio thread, with no
  allocation, locks or calls.
- **How the page gets it:** `send_controls()` in `screen.hpp` copies it into the page's input, as it does the
  slots. A torn read costs one window for one frame, so it needs no lock.
- **Input fields (proposal):** `u8 level_in[128]` (peak × 255 of full scale, oldest first), `u32 level_head`
  (windows so far) and `u32 bpm_x10`. 136 bytes. Synth pages read zeros.
- Like every SDK change, it needs its docs (`docs/display.md`, Effect pages), a test, the firmware build and release
  verification, and the maintainer's review.

Until it lands, `sim/scope.cpp` writes the same peaks from the engine code on a computer.

## `definition.json`

```json
"display": {"stateBytes": 64, "stateAlignment": 4,
            "paths": 4, "points": 64, "nodes": 442, "texts": 16, "palette": 4}
```

## Coordinates

- The wave's centre line is y 150. Columns run from x `6 + 117k`, k = 0..4 (6, 123, 240, 357, 474).
- Controls as 0..1: `sq`, `e` (Echo), `sp`, `b`, `m`, `d` (Dry), `a`; `t` is Tone, -1..+1; `fx` is 1 for FX first.
- `in(i)`: window i's input peak, 0..1 (`level_in / 255`), 0 outside the history; `h` the newest window.

## Node map

| index | part | driven by |
| --- | --- | --- |
| paths 0–3 | the wave, one per column; path 0 carries the playing's swell | what's sounding, Squeeze, Tone, Attack |
| 4–11 | header bars | `page_header()` |
| 12–411 | step cells: step k, cell j, variant v at `12 + (k·10 + j)·10 + v` | Squeeze, the gain reduction and ducking, Space, the room, Tone, Motion, Attack, Order |
| 412–441 | riser segments: riser r, segment s at `412 + r·10 + s` | follows the steps |

Cell variants, each authored at the cell's left end on the step line (11.7 px wide): v0 a flat 1.5 px ribbon
(`P_TREAD`); then one cycle of ripple (`P_RIPPLE`, 1.0 px ribbons) at height h (1.5 / 3.5 / 6.0 px, h = 1..3) and
phase p (0, ⅓, ⅔ of a cycle on, p = 0..2), as variant `h + 3p`. Show one variant, hide the others; a cell only
translates. Riser segments are 1.5 × 4 px.

## What's sounding

Each frame, from the levels (`x(i) = 1.6 · max(in(i−s..i+s))`, s = 0 unless given):

```
delay   = division(e) · (60 / bpm / 4) / 0.0319          windows; division as stock's note lengths, in 16ths
level   = e > 0.01 ? min(1, 8e) · 0.8 : 0;   fb = 0.15 + 0.6e
swell0  = x(h) · d;   swellk = x(h − round(k·delay), s = 2) · level · fb^(k−1),  k = 1..3
room    = min(1.2, sp · 0.29 · Σ_{j<128} x(h − j) · exp(−j · 0.0319 / (0.25 + 3·sp²)))
follow  = min(1, x(h) / 0.6);   duck = b · follow;   gr = sq · follow
energy  = min(1, 4 · (Σ swells + room))
phase  += 2π · 0.9 / fps · energy;   sway += 2π · 0.3 / fps · energy        (kept in DisplayState)
```

## The pose

**Steps.** `limit_k = (64 − 40·sq)·0.77^k`, minus `gr·10·sq` on step 0 (on every step with FX first) and
`duck·16` on steps 1–3; at least 4. y = `150 − limit_k`, plus `±3·m·sin(sway)` on steps 1–3 (odd down, even up),
whole pixels.

**Ripple.** `reach = min(9, round(10·(0.2 + 0.85·sp)·(1 − 0.4·max(0, −t))))` cells at each step's end, none when
`sp ≤ 0.01`. `amp_k = (3 + k)·√min(2, sp/0.35)·(1 + 0.8·room)`, at most 1 with FX first. For a tail cell,
`a = amp_k·(1 + 0.5t)·(j − first + 1)/reach`; height 0 below 0.75, 1 below 2.5, 2 below 4.75, else 3. Variant is
`h + 3p` with `p = ⌊1.3·phase / (2π/3)⌋ mod 3`, so the ripple travels a third of a cycle at a time. Other cells are v0.

**Attack.** `att = 3 + 80·a²` px. Hide step 0's cells that end before `att − 20` px from x 6.

**Risers.** From step k to step k+1 at the column edge, 4 px segments from the top, up to 10, the last pulled up to
end on the lower step; none when the gap is under 3 px.

**Wave.** The swells at rest are the design's: `standing = [62·d, 48·L, 36·L·F, 26·L·F²]` with `L = min(1, 8e)` (0 when
`e ≤ 0.01`) and `F = (0.15 + 0.6e)/0.51`; the playing adds `32·swell_j`. Column k's 32 points: its two ends, a point
0.5 px in from each end at the same height (a short flat, so the outline never turns sharply there), every crest and
trough of the 11 px cycle inside it, then points ⅙ of a half-cycle either side of the tallest crests, until there are
32 (if fewer, split the longest gap). At each:

```
env = max(1.2, max over j of amp_j · (1 − exp(−dj/4)) · exp(−dj·f_j)),   amp_j = standing_j + 32·swell_j,  dj = x − (6 + 117j) ≥ −2 (clamped at 0)
      f_0 = 0.022,  f_j = 0.022·(1 − 0.5t) for the repeats
v   = env · sin(2π·(x − 6)/11 − phase)
step 0 within att px of x 6:       v ·= 1 + 0.8a², held within ±(limit_0 + 20a²)
otherwise:                         v = soft(v, max(1.5, limit_k − 2))
v   = clamp(v, −62, 62);   point (x, 150 − v), then the same 1 px lower in reverse: a closed 64-point ribbon
```

`soft(v, L)` passes `|v| ≤ 0.6L` and bends the rest: `0.6L + over/(1 + over/(0.4L))`, sign kept. Place each path at
its column's centre (`6 + 117k + 58.5`, 150) with points relative to it.

## Palette

| entry | name | fill / stroke | width | for |
| --- | --- | --- | --- | --- |
| 0 | `P_WAVE` | none / `#969696` | 1.5 | paths 1–3 |
| 1 | `P_WAVE_DRY` | none / `#CDCDCD` | 2.0 | path 0, the playing: the one brightest element |
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
| `u16 phase, sway` | 4 | the two phases, as fractions of a turn |
| `u16 track; u8 initialized, pad` | 4 | snap on the first frame and on a track change |

Each frame: ease the controls (halve the distance every 21 ms) or snap on the first frame, a track change or
`reduced_motion`; work out what's sounding; advance the phases (not with `reduced_motion`); run the pose.

## Path keys

Each wave path's key is a running count that goes up by one on every frame its points change: while anything
sounds (`energy > 0`) or a control it depends on eases. In silence it stays put, so nothing redraws. Never key by
`elapsed`.

## Budget

`python3 gen_clew.py budget`: 0 at rest; 21.1 a frame on average while the phrase plays at the defaults (peak 74);
24.1 at Space 100 (peak 90); 25.9 at Echo, Space and Blend 100 (peak 92). The peaks are the ripple moving on every
tail at once, about every 6.6 frames.

## Open checks

- **Pending SDK:** the levels on the page.
- **Pending device:** photos at rest, playing and Echo, Space and Blend at 100; the redraw cost while playing; seams where risers meet
  steps; header captions in Univers Next Pro Light (`3/64`, `30.0`, `comp`); the Shift row in the edited header row.
