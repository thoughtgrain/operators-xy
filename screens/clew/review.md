# Clew · review

Pass 05 v2 as built by `gen_clew.py` (27 frames, `contact.png`). Every answer below points at a frame or a number;
anything only a device can show is **pending device**.

## Craft, side by side

Rest frame beside `operator-design/library/theseus-tower/frames/rest.svg`, both at 1:1.

| question | answer |
| --- | --- |
| Every element drawn in the named language (scope trace under a ruled ceiling)? | Yes. The wave is one trace; the ceiling is ruled steps with risers; the room is drawn as ripple on the ruling, not as a separate object. |
| Line weights match the table at every zoom? | Yes. Subject (the dry swell) 2.0 px; the rest of the wave and the steps 1.5 px; ripple arches 1.0 px ribbons; risers 1.5 px. Every part only translates, so no stroke scales. |
| Exactly one brightest element? | Yes: the first swell, `#CDCDCD` (`P_WAVE_DRY`). Everything else is `#969696` or `#7D7D7D`. |
| Anything look like an icon? | No. The ripple arches are the closest risk; at 1:1 they read as a wavy edge on the step, not as symbols. |
| Sits in the same set as the reference? | Yes. Both are line drawings in mid greys on black with one bright part. Clew is flatter (front elevation, no depth), which suits a signal picture. |

Not taken from `craft.md`: labels. An atlas or schematic would label its parts, but every part here moves or
disappears with a control (Echo off removes the repeats), so a fixed label would be wrong at some setting. I left the
drawing unlabelled; the header names every control.

## Accessibility checklist

- [x] Every frame viewed at 1:1 (480 × 220), not enlarged: contact sheet built at 1:1; spot checks of rest, c1-100,
      c2-000, c2-100, c3-100, c4-000, c4-100, c5-000, c5-100, c6-100, c7-000, c8-100, order-fx.
- [x] Text ≥ 8 px everywhere, ≥ 10 px for anything read during play: only the SDK header has text (10 / 20 / 13 px).
- [x] Text greys ≥ 4.5:1: the header is the SDK's own.
- [x] Meaningful non-text parts ≥ 3:1 on black: `#7D7D7D` 5.1:1 (ripple), `#969696` 7.1:1 (wave, steps, risers),
      `#CDCDCD` 13.2:1 (first swell). The floor line is `#4B4B4B` 2.4:1, but it's ground and carries no meaning.
- [x] No part under ~3 px; no repeated lines closer than ~3 px: the smallest parts are 4 px riser segments and
      11.7 px cells; the lowest ripple arch is 2.5 px tall on an 11.7 px cell, part of the step's edge rather than a
      part of its own. The wave's peaks are at least 19.5 px apart (6 cycles in 117 px, the finest Tone).
- [x] No state or control effect shown by shade alone: no control changes a shade. Order changes position and
      shape.
- [x] Each control visibly different at 0 / 50 / 100, and `perceptibility.py` passes: squeeze 2.65 %, echo 2.70,
      space 2.11, blend 2.73, tone 2.44, motion 1.64, dry 1.93, attack 1.22 (floors 1.6 / 2.5 / 1.6 / 1.2 / 1.2 /
      0.8 / 1.6 / 0.8); every span ≥ 101 px.
- [x] Visual travel matches the audible score: the score-5 control (Echo) has the second-largest change and every
      score-2 control the smallest. Blend (score 3) reads a little larger than Echo (2.73 against 2.70) because it
      moves both the tails and the swells' rise; Squeeze (4) above Echo. Both are within a few hundredths, and
      neither drops Echo under its floor, so I kept them.
- [x] Nothing moves at rest; nothing flashes more than 3×/s: 0 changed nodes at rest (`gen_clew.py budget`); no
      flashing at all.
- [x] Reduced-motion end states differ by more than shade: every end state is a different position or shape.
- [x] Labels ≤ 8 characters, lower case: squeeze, echo, space, blend, tone, motion, dry, attack, order. Value
      captions measured in Univers Next Pro Light: **pending device**.
- [x] No red anywhere in machine artwork: four greys, `#7D7D7D` to `#CDCDCD`, plus the `#4B4B4B` floor.
- [ ] Device photos at rest, playing, heaviest setting: **pending device**.

## Before you submit (open-xy PR #260, house rules)

- [x] Redraw ~20 changed nodes a frame on average while notes sound, 0 at rest: notes don't redraw this page at all.
      Turning Squeeze fast is 40.5 average, peak 46, only while the knob moves; slow it's 12.3. The cost on the
      device: **pending device**.
- [x] Change a path's key only when its points change: each wave path's key is a hash of the controls that shape it
      (handoff, Path keys), never the time.
- [x] Moving fills: none. Cells and risers are filled ribbons but only translate.
- [x] Near-reversal, point spacing, closing edge, one subpath ≤ 64 points: `lint_frame.py` 0 errors, 0 warnings
      on all 27 frames.
- [ ] Touching parts share one outline or the same transform: the risers meet the step ends and the cells meet each
      other as separate nodes, each placed on whole or half pixels from the same numbers, so they line up in the
      previews. A hairline seam on the device is possible: **pending device**.
- [x] No on/off controls: Echo fades its repeats to flat; Tone's cycle count is stepped at ±33 but its ripple reach
      eases; Order is a switch by nature and moves three things.
- [x] Grey-only differences: none.

## What the frames can't show

The note response. The protocol asks for `playing.svg` and a rest → playing check, but an effect page's input has
no note activity or level (open-xy `docs/display.md`, Effect pages), so there's no playing frame. Pass 05's animation
drew the swells rising and the tails ducking with the playing; the device page won't do that. If open-xy later gives
effect pages a send level, the swell sizes and step heights are where a live term would go, on top of the
settings (that's what pass 05's animation model did).
