# Clew · motion

The wave is the send's audio, so most of the motion here comes from the playing. That needs the send's levels on
the page, which open-xy doesn't provide yet (`handoff.md`, The SDK change); every row marked *levels* waits for it.

Vocabulary from `opxy/patterns.md`: **scroll** (moves with time at a fixed rate), **ease** (exponential, settles in
0.15 s), **snap** (jump to the end state).

| trigger | what moves | from → to | how | reduced motion / track change |
| --- | --- | --- | --- | --- |
| sound comes in (*levels*) | the wave (paths 0–3) | the newest 31.9 ms enters at the right edge; everything shifts left one window (7.8 px) | scroll, 31.3 windows a second; its drawn cycles travel with it | the wave still shows the levels but doesn't scroll: it redraws once a second |
| loud input (*levels*) | the steps over it | down by 1.2 px per dB of gain reduction, until it rests on the wave; back up as that part scrolls out | 4 px steps, so a step moves only when the change is worth seeing | same, once a second |
| the room ringing (*levels*) | ripple on each step's tail | arches appear while Space and the output there are high enough, and walk one cell every six frames, each step a little out of phase | walk, 5 cells a second | still arches, no walk |
| playing with Blend up (*levels*) | the tail cells | lean down by up to 28 px with how hard that part was played | follows the scroll | same, once a second |
| sound stops | everything | the wave scrolls out to a flat line; the steps rise back to the ceiling; the ripple stops when the room is gone | as above, then nothing | snap |
| turn Squeeze | the steps' ceiling | 64 → 24 px above the centre line | ease 0.15 s | snap |
| turn Space, Tone | the ripple's reach and grain | reach 2 → 8 cells; dark skips every other cell, bright adds a notch | ease the reach | snap |
| turn Motion | steps 1–3 | stagger 0 → 7 px | ease 0.15 s | snap |
| turn Attack | each step's first cells | the step starts 3 → 43 px late | ease 0.15 s | snap |
| turn Echo, Blend, Dry | nothing directly | they change the sound, and the wave shows it as it scrolls in | — | — |
| Order (Shift) | the tails | FX first: no lean, lowest ripple | ease 0.15 s | snap |
| page press | header only | the SDK's two-page header swaps rows | `page_header()` | the helper snaps |
| hold Shift | the header's edited row | `order` and `comp` / `fx` | text, no ease | same |

Gate:

- Nothing moves at rest: yes. In silence the levels are 0 and every ease has settled, so nothing changes. The wave
  scrolls only while sound is on screen and stops about 1.9 s after the last of it, which is the note-response rule
  (motion lasts as long as the sound does).
- Every ease settles in 0.15–0.2 s: yes, 0.15 s.
- Held-note motion lasts as long as the sound: yes, the scroll and the ripple follow the audio, not a timer.
- Reduced motion and track change: the controls snap; the wave keeps showing the levels but redraws once a second
  instead of scrolling, and the ripple doesn't walk.
