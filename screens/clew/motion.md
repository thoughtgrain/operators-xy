# Clew · motion

The page only sees its controls, Shift and the elapsed time (no notes or levels; see the brief, phase 4), so every
motion here starts from a hand on a control. Nothing moves at rest. That also means the note triggers in the
protocol (note on, held, hold ended) have nothing to drive them, and the table says so rather than leaving them out.

Vocabulary from `opxy/patterns.md`: **ease** (exponential, settles in 0.15 s), **snap** (jump to the end state).

| trigger | what moves | from → to | how | reduced motion / track change |
| --- | --- | --- | --- | --- |
| turn Squeeze | all four steps and their risers; the swells under them | each step's height to `64 − 40·squeeze` px above the centre line (×0.82 per later step); swells re-bent under them | ease 0.15 s, steps in whole pixels | snap |
| turn Echo | repeat swells (paths 1–3) | their size to `36 × level`, level from Echo (0 → flat) | ease 0.15 s; the path key changes only when the points do | snap |
| turn Space | ripple at each step's far end | reach 2 → 8 cells, arch height 1 → 3 | ease the reach and height; cells swap variant as they cross a whole step | snap |
| turn Blend | tail cells; repeat swells' rise | tails lean 0 → 42 px towards the wave; swells rise over 5 → 35 px | ease 0.15 s | snap |
| turn Tone | later repeats' cycles; ripple grain | 4 → 5 → 6 cycles in paths 2–3; dark halves the ripple reach and skips every other cell; bright raises each arch a notch | cycle count changes at −33 and +33 (whole cycles keep the wave continuous); reach eases | snap |
| turn Motion | steps 1–3 | stagger 0 → 7 px, alternate steps up and down | ease 0.15 s | snap |
| turn Dry | the first swell (path 0) | 0 → 40 px | ease 0.15 s | snap |
| turn Attack | the first step's start; the first swell under it | the step begins 3 → 43 px late; the swell there 1.6× taller | ease 0.15 s | snap |
| Order (Shift) | tails, ripple, repeat swells | Comp first → FX first: tails stop leaning, ripple drops to its lowest arch, repeats level to a 10 px band; and back | ease 0.15 s, once per change | snap |
| page press | header only | the SDK's two-page header swaps rows | `page_header()`, settles in 0.15 s | snap (the helper does it) |
| hold Shift | header's edited row | shows `order` and its choice while `shift` is 1 | no ease; it's text | same |
| note on / held / hold ended | nothing | the effect page gets no note activity | — | — |

Gate:

- Nothing moves at rest: yes. With every control still, every target is unchanged and every ease has settled, so
  0 nodes change (`gen_clew.py budget`). The elapsed time is only used to run the eases; there's no idle motion.
- Every ease settles in 0.15–0.2 s: yes, 0.15 s (the header helper's curve, halving every 21 ms).
- Held-note motion lasts as long as notes are held: n/a, no note input on effect pages.
- Reduced motion and track change jump to the end state: yes, every row snaps.
