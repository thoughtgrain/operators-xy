# Clew · review

Pass 05 v2 with the wave as the audio, as built by `gen_clew.py` (28 frames, `contact.png`). The playing frames
use levels from `sim/scope.cpp` (toro's and Clew's engine code on a computer) at 5.75 s into the phrase, the rest
after a bar, while its echoes and room ring. Anything only a device can show is **pending device**; anything that
waits for the SDK change is **pending SDK**.

## The blocker

The design needs the send's levels on the page, and effect pages don't get them (open-xy `docs/display.md`,
Effect pages). Without the SDK change in `handoff.md`, the page could only draw the rest frame. That change is a
separate pull request to open-xy, and it isn't written yet.

## Craft, side by side

`playing.svg` beside `operator-design/library/theseus-tower/frames/rest.svg`, both at 1:1.

| question | answer |
| --- | --- |
| Every element drawn in the named language (scope trace under a ruled ceiling)? | Yes. The wave is a scope trace of the output; the ceiling is ruled steps with risers; the room is ripple on the ruling. |
| Line weights match the table at every zoom? | Yes. The newest column 2.0 px, the rest of the wave and the steps 1.5 px, ripple arches 1.0 px ribbons, risers 1.5 px. Parts only translate. |
| Exactly one brightest element? | Yes: the newest part of the wave (the right-hand column), `#CDCDCD`. |
| Anything look like an icon? | No. |
| Sits in the same set as the reference? | Yes: mid-grey line drawing on black with one bright part. Clew is busier while it plays, since the wave fills the width; at rest it's as quiet as theseus. |

No labels, as before: every part moves with the audio or a control.

## Accessibility checklist

- [x] Every frame viewed at 1:1 (480 × 220): contact sheet at 1:1; spot checks of rest, playing, c1-100, c2-000,
      c2-100, c3-100, c4-100, order-fx, and six stills from the preview.
- [x] Text ≥ 8 px, ≥ 10 px for anything read during play: only the SDK header has text.
- [x] Text greys ≥ 4.5:1: the header is the SDK's own.
- [x] Meaningful non-text parts ≥ 3:1 on black: `#7D7D7D` 5.1:1 (ripple), `#969696` 7.1:1 (wave, steps, risers),
      `#CDCDCD` 13.2:1 (newest wave). The floor, `#4B4B4B` 2.4:1, is ground.
- [x] No part under ~3 px; no repeated lines closer than ~3 px: the wave's drawn cycle is 31 px; the smallest parts
      are 4 px riser segments and 11.7 px cells.
- [x] No state shown by shade alone: the bright column is "newest", and it's also where the sound enters, so its
      position says the same thing.
- [x] Each control visibly different at 0 / 50 / 100, and `perceptibility.py` passes: squeeze 8.14 %, echo 7.85,
      space 11.26, blend 8.69, tone 5.80, motion 4.19, dry 5.93, attack 7.19; note response (rest → playing) 7.69.
      Every span ≥ 329 px.
- [ ] Visual travel matches the audible score: Space (4) moves the most and Echo (5) is fourth. While it plays, the
      room fills the whole wave and raises the line, so Space shows more than its score. Every control clears its
      floor; I've left the order as the audio gives it rather than shrink the room's picture.
- [x] Nothing moves at rest; nothing flashes more than 3×/s: silence changes 0 nodes; the ripple walks 5 cells a
      second, a travelling ripple, not a flash.
- [x] Reduced-motion end states differ by more than shade.
- [x] Labels ≤ 8 characters, lower case. Value captions in Univers Next Pro Light: **pending device**.
- [x] No red: four greys plus the floor.
- [ ] Device photos at rest, playing and the heaviest setting: **pending SDK**, then **pending device**.

## Before you submit (open-xy PR #260, house rules)

- [ ] ~20 changed nodes a frame on average while notes sound, 0 at rest: 18.4 at the defaults, 22.9 at Space 100,
      23.2 at Space and Squeeze 100 (peaks 38 / 51 / 53); 0 at rest. The heaviest settings are a little over. The
      cost on the device: **pending device**.
- [x] A path's key changes only when its points do: the wave's points change every window while sound is on screen
      and never in silence (handoff, Path keys).
- [x] Moving fills: none.
- [x] Near-reversal, point spacing, closing edge, ≤ 64 points per path: `lint_frame.py` 0 errors, 0 warnings on
      all 28 frames.
- [ ] Touching parts share one outline or transform: risers, cells and the wave are separate nodes on whole or half
      pixels. Seams: **pending device**.
- [x] No on/off controls.
- [x] No grey-only differences.

## What's simulated

The levels. `sim/scope.cpp` runs the same toro phrase through Clew's engine code that the audio demo does and
writes the peaks a 22-block window would give. The display code that reads them is the same one the device would
run, but whether the device's levels look like these is **pending SDK** and **pending device**.
