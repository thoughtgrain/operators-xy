# Clew · motion

Pass 05 v2's motion, built for the device. Everything the playing drives needs the send's levels on the page, which
open-xy doesn't provide yet (`handoff.md`, The SDK change); those rows are marked *levels*.

Vocabulary from `opxy/patterns.md`: **follow** (tracks a level frame by frame), **ripple** (a phase that advances only
while something sounds), **ease** (exponential, settles in 0.15 s), **snap**.

| trigger | what moves | from → to | how | reduced motion / track change |
| --- | --- | --- | --- | --- |
| a note comes in (*levels*) | the first swell (path 0) | grows to 80 px × the input's peak × Dry, pressed by the first step | follow | follow |
| a delay time later (*levels*) | the next step's swell (paths 1–3) | the same note, at Echo's level and feedback, one step further each repeat | follow | follow |
| loud input (*levels*) | the first step | dips up to 10·sq² px with the gain reduction (all steps with FX first) | follow, whole pixels | follow |
| playing with Blend up (*levels*) | steps 1–3 | dip up to 16 px with the ducking, back in the gaps | follow | follow |
| anything sounding (*levels*) | the wave's cycles | ripple sideways at 0.9 cycles a second | ripple: the phase moves only while it sounds | still |
| the room ringing (*levels*) | the tails' ripple | grows with the room along each tail; moves a third of a cycle every ~6.6 frames, so it travels | ripple, the same phase × 1.3 | still, at its height |
| anything sounding, Motion up (*levels*) | steps 1–3 | sway ±3·motion px, alternate steps opposite, 0.3 cycles a second | ripple: moves only while it sounds | still |
| sound stops | everything | the swells fade with the input, the steps rise back, the phases stop | follow, then nothing | snap |
| turn any control | what it shapes (see the brief) | to its new value | ease 0.15 s | snap |
| page press | header only | the SDK's two-page header swaps rows | `page_header()` | the helper snaps |
| hold Shift | the header's edited row | `order` and `comp` / `fx` | text | same |

Gate:

- Nothing moves at rest: yes. In silence every level is 0, the phases stop and every ease settles, so nothing
  changes. Pass 05's sketch swayed the steps on a timer even in silence; here the sway only moves while something
  sounds, which looks the same while playing.
- Every ease settles in 0.15–0.2 s: yes, 0.15 s.
- Note-driven motion lasts as long as the sound: yes, everything follows the levels.
- Reduced motion and track change: controls snap; the wave still follows the levels (that's the information) but
  its cycles, the ripple and the sway don't travel.
