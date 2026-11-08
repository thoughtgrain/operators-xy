# Clew · review

Pass 05 v2 as built by `gen_clew.py` (28 frames, `contact.png`), checked against the sketch the owner picked
(`preview/clew-v2-anim.mp4`). The playing frames use what's sounding at 4.3 s into the phrase, worked out from the
input levels `sim/scope.cpp` writes (toro's and Clew's engine code on a computer). Anything only a device can show
is **pending device**; anything waiting for the SDK change is **pending SDK**.

## The blocker

The design follows the playing, and effect pages don't receive it (open-xy `docs/display.md`, Effect pages).
Without the SDK change in `handoff.md`, the page could only draw the rest frame. That change is a separate pull
request to open-xy, not written yet.

## Against the sketch

Stills from both videos at 6, 21, 37 and 45 s, side by side at 1:1. Same subject, same layout, same motion. The
differences:

- The wave's cycle is 16.7 px, not 11: a mutable outline holds 32 points along a 117 px column, and an 11 px cycle at
  that spacing breaks the SDK's path rules (3 points a cycle).
- The tails' ripple is one 9.75 px cycle per cell, moving a third of a cycle every ~6.6 frames, instead of a smooth
  travelling sine: the cells are fixed artwork that can only be placed, not reshaped.
- The step layout is fixed to the encoder columns; the sketch widened the steps with longer echoes. The device can't
  reshape the cells, and the column layout ties each step to a control's column.
- The swells come from the simulated audio's levels, so they're as big as the playing really is; the sketch used a
  model of the notes.
- The sketch swayed the steps on a timer even in silence; here they sway only while something sounds.

## Craft, side by side

`playing.svg` beside `operator-design/library/theseus-tower/frames/rest.svg`, both at 1:1.

| question | answer |
| --- | --- |
| Every element drawn in the named language (scope trace under a ruled ceiling)? | Yes. |
| Line weights match the table at every zoom? | Yes. The first swell 2.0 px, the rest of the wave and the steps 1.5 px, ripple 1.0 px, risers 1.5 px. Parts only translate. |
| Exactly one brightest element? | Yes: the first swell (the playing), `#CDCDCD`. |
| Anything look like an icon? | No. |
| Sits in the same set as the reference? | Yes: mid-grey line drawing on black, one bright part. |

## Accessibility checklist

- [x] Every frame viewed at 1:1: contact sheet and spot checks of rest, playing, c2-000, c2-100, c8-000, c8-100, and
      four stills of the preview against the sketch.
- [x] Text: only the SDK header.
- [x] Meaningful non-text parts ≥ 3:1: `#7D7D7D` 5.1:1 (ripple), `#969696` 7.1:1, `#CDCDCD` 13.2:1. The floor,
      `#4B4B4B` 2.4:1, is ground.
- [x] No part under ~3 px; no repeated lines closer than ~3 px: the wave's cycle is 16.7 px; the ripple's 9.75 px.
- [x] No state by shade alone.
- [x] Each control visibly different at 0 / 50 / 100 while playing, and `perceptibility.py` passes: squeeze 4.52 %,
      echo 2.57, space 3.84, blend 2.21, tone 2.52, motion 1.83, dry 3.72, attack 2.83; note response 6.49.
- [ ] Visual travel matches the audible score: Squeeze (4) and Space (4) show more than Echo (5), which only just
      clears its floor (2.57 against 2.50) at this moment of the phrase. Every control clears its floor, so I kept the
      sketch's proportions.
- [x] Nothing moves at rest; nothing flashes more than 3×/s: the ripple flips about twice a second.
- [x] Reduced-motion end states differ by more than shade.
- [x] Labels ≤ 8 characters, lower case. Captions in Univers Next Pro Light: **pending device**.
- [x] No red.
- [ ] Device photos: **pending SDK**, then **pending device**.

## Before you submit (open-xy PR #260, house rules)

- [ ] ~20 changed nodes a frame on average while notes sound, 0 at rest: 22.7 at the defaults; 25.1 at Space 100;
      27.2 at Echo, Space and Blend 100 (peaks 71 / 91 / 92, the frames where every tail's ripple moves). Over, to
      keep the sketch's travelling ripple. 0 at rest.
      The device cost: **pending device**.
- [x] A path's key changes only when its points do (handoff, Path keys).
- [x] Moving fills: none.
- [x] Path rules: `lint_frame.py` 0 errors, 0 warnings on all 28 frames.
- [ ] Touching parts: risers, cells and the wave are separate nodes. Seams: **pending device**.
- [x] No on/off controls; no grey-only differences.
