# Clew · review

Pass 05 v2 as built by `gen_clew.py` (28 frames, `contact.png`), checked against the sketch the owner picked
(`preview/clew-v2-anim.mp4`). The playing frames use what's sounding at 4.3 s into the phrase, worked out from the
input levels `sim/scope.cpp` writes (toro's and Clew's engine code on a computer). Anything only a device can show
is **pending device**; anything waiting for the SDK change is **pending SDK**.

## The blocker

The design follows the playing, and effect pages don't receive it (open-xy `docs/display.md`, Effect pages).
Without the SDK change in `handoff.md`, the page could only draw the rest frame. That change is a separate pull
request to open-xy, not written yet.

## Against the design

The rest frame beside `passes/05-revision/v2/rest.svg` at 1:1, and four stills of the preview: the same step
heights (50, 38, 29, 22 px), the same swells (62, 48, 36, 26 px), the same half-step ripple growing towards each
riser, the same 11 px wave. The differences:

- The wave's points: 32 along a 117 px column can't sample an 11 px cycle evenly, so they sit on the crests and
  troughs and round the tallest crests. The low stretches read a little more angular than the design's.
- The bright part is the whole first column (one outline), where the design brightens its first 70 px.
- The tails' ripple is one 11.7 px cycle per cell (five on a half step; the design has four to seven), moving a
  third of a cycle every ~6.6 frames instead of sliding smoothly: the cells are fixed artwork that can only be
  placed.
- While playing, the swells grow with the simulated audio, the first step dips with the gain reduction, the later
  ones with the ducking, and the steps sway only while something sounds (the animated sketch swayed in silence too).

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
- [x] No part under ~3 px; no repeated lines closer than ~3 px: the wave's cycle is 11 px; the ripple's 11.7 px.
- [x] No state by shade alone.
- [x] Each control visibly different at 0 / 50 / 100 while playing, and `perceptibility.py` passes: squeeze 9.94 %,
      echo 4.86, space 6.35, blend 4.84, tone 5.56, motion 1.89, dry 6.80, attack 3.94; note response 11.13.
- [ ] Visual travel matches the audible score: Squeeze (4), Dry (4) and Space (4) show more than Echo (5). Every
      control clears its floor, so I kept the design's proportions.
- [x] Nothing moves at rest; nothing flashes more than 3×/s: the ripple moves about five times a second, a travelling ripple rather than a flash.
- [x] Reduced-motion end states differ by more than shade.
- [x] Labels ≤ 8 characters, lower case. Captions in Univers Next Pro Light: **pending device**.
- [x] No red.
- [ ] Device photos: **pending SDK**, then **pending device**.

## Before you submit (open-xy PR #260, house rules)

- [ ] ~20 changed nodes a frame on average while notes sound, 0 at rest: 21.1 at the defaults; 24.1 at Space 100;
      25.9 at Echo, Space and Blend 100 (peaks 74 / 90 / 92, the frames where every tail's ripple moves). Over, to
      keep the design's travelling ripple. 0 at rest.
      The device cost: **pending device**.
- [x] A path's key changes only when its points do (handoff, Path keys).
- [x] Moving fills: none.
- [x] Path rules: `lint_frame.py` 0 errors, 0 warnings on all 28 frames.
- [ ] Touching parts: risers, cells and the wave are separate nodes. Seams: **pending device**.
- [x] No on/off controls; no grey-only differences.
