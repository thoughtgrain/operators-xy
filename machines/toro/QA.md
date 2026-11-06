# Testing toro on an OP-XY

These are the checks to run on a device with a firmware that includes toro. Run them top to bottom in one project:
each section leaves the project ready for the next. To run only some sections, set up what their first line says.
The host tests (`python ../open-xy/sdk.py test --machine machines/toro`) don't replace these, because they can't
hear the sound or see the screen.

Report a failure with the section, the line and what you saw. A photo of the screen helps. Note the toro commit,
the SDK commit and the firmware build each full pass used.

When a change adds, removes or alters something a person would check on the device, update the lines here in the
same commit.

## Setup

- Build a firmware with toro ([building firmware](https://github.com/etcetc000/open-xy/blob/staging/docs/build.md#3-add-your-machine))
  and install it.
- Create a new project, **plain**, without toro: give track 1 a stock sound of its own and save it. Later steps
  load it as a project that never had the machine.
- Create another new project, **qa**, for the pass: don't use a project you care about.
- Track 1: toro (Shift + M1 on track 1, then choose it), with one note on step 1 lasting a whole bar, so it sounds
  all the time while the sequencer plays.
- Press play, and leave it playing unless a step says otherwise.

## Firmware basics

- [ ] The OP-XY boots, and stock engines, effects, the sequencer and project save/load work
- [ ] toro is in the engine list of tracks 1-8 (Shift + M1 there), as "Toro", and in no other track's list

## Its page and controls

- [ ] The header shows two pages, Spread / Fold / Cutoff / Res and Shape / Noise / Drive / Aphx; pressing any
      encoder switches pages, and each control keeps its own value
- [ ] Spread reads as a ratio, 1.00 to 1.50: at 1.00 the two oscillators beat slowly, and turning up moves through
      detune towards a fifth
- [ ] Fold 0 to 100: clean at 0, more and more harmonics up to a harsh, folded tone at 100
- [ ] Cutoff 0 to 100 darkens and opens the sound; Res 0 to 100 adds a peak, and high Res with low Cutoff stays
      stable (no runaway, no silence)
- [ ] Shape 0 to 100: saw to triangle, softer at the top
- [ ] Noise 0 to 100: noise into the folder, grittier with Fold up
- [ ] Drive 0 to 100: soft clip, louder and denser, never clipping hard on the output
- [ ] Aphx reads -100 to +100 with 0 at its centre, and at 0 there's no drift on any key
- [ ] Each control through its whole range, both directions: no clicks, jumps or silence at the ends
- [ ] Fast turns: the value keeps up, no flicker or slowdown
- [ ] Every key across the keyboard's octaves starts a note at its pitch, and releasing it ends the note; no note
      gets stuck, also after long holds
- [ ] Chords and fast repeated notes: every note sounds and ends
- [ ] M2 and M3 (envelope and filter) change the sound as on a stock engine

## Aphx and the accent

Stop the sequencer for this section; play by hand.

- [ ] Aphx +50, play one key several times: the same key sounds the same each time at the same place in the
      accent cycle (strong, weak, medium, weak); different keys drift differently
- [ ] Aphx +100: keys are well out of tune with each other, and the top end adds a gritty sample-and-hold crush
- [ ] Aphx -50, play one key several times: every note drifts a different way
- [ ] Aphx +50, play one key eight times in a row: the drift repeats every four notes, one note in four drifts
      furthest, the one two after it a little less, and the two between least
- [ ] Aphx at 0: the four notes sound the same (the accent only deepens Aphx)

Start the sequencer again: program four steps of the same note.

- [ ] Aphx +50: the pattern repeats exactly bar after bar
- [ ] Aphx -50: each step drifts its own way, and differently again on every pass of the pattern
- [ ] Aphx at 0, then lock step 3 to Aphx -60: only step 3 drifts, a different way on each pass

## The screen

- [ ] At rest: a field of stacked slabs below the header, some hollow, one row of tops lit by Res; nothing moves
      while no note plays
- [ ] Each control reshapes the field: Spread adds a beating second wave, Fold folds the heights and wraps the
      field round a drum (almost closed at 100) in twelve even steps, Cutoff adds fine ripples, Res moves the lit row front to back,
      Shape softens the ridges, Noise jitters the columns, Drive flattens the tallest columns, Aphx makes columns
      wander
- [ ] A note: a patch of six slabs lifts with white tops, a ripple spreads a few columns round it and fades,
      and it settles within a second; slabs far from the note don't move
- [ ] Fast notes (16ths at 140 BPM and up): every note answers, no flicker, the field keeps up
- [ ] Fold at 100 with a note: nothing draws over the header
- [ ] The page while playing and while stopped, and after leaving it and coming back: nothing stale, missing or
      drawn twice
- [ ] Reduce motion on (if the OP-XY offers it): notes change the field without the lift and ripple

## Parameter locks

- [ ] Lock each control on a step (hold the step, turn the knob): it plays on that step, and the page shows the
      lock while the step is held
- [ ] Several locks on one step, and locks on neighbouring steps: each plays as written
- [ ] Clear the locks: the control plays its own value again

## LFOs

- [ ] The track's LFO (M4) lists toro's controls by their names, and moving one of them is heard, stopped and
      playing
- [ ] The LFO on Aphx sweeping through 0 crosses from per-step to per-key drift without clicks
- [ ] Rate, depth and shape behave as on a stock engine; turning the LFO off stops the movement

Then turn the LFO off.

## Patterns, scenes and songs

- [ ] Give the track a second pattern with different values: each pattern keeps its own
- [ ] Copy a pattern: the copy holds the same values, and changing one leaves the other alone
- [ ] Switch between the patterns while playing and while stopped: the sound and the page follow at once
- [ ] Make scenes 1 and 2 with the two patterns, and a song of scene 1 then scene 2, looping: each scene plays its
      own values from its first bar, on every pass

Then play scene 1.

## Presets

- [ ] Shift + track key lists toro's presets: Clean, Bull, Drift, Labyrinth and Roll; choosing one sets its values
- [ ] Drift has Aphx right of centre (per key), Roll left of centre (per step), Clean and Bull at centre
- [ ] Save the track's sound as a preset, change it, load the preset: the saved values come back
- [ ] A stock preset loaded on a track holding toro (and the reverse) gives what it says, with no stray values

## Mute

- [ ] Mute the track (hold aux and press the track's key): it's silent, with no click or tail left behind;
      unmute: it plays as before
- [ ] The same from the mixer
- [ ] Muted in scene 2 only: switching between scenes 1 and 2 mutes and unmutes it

Unmute it everywhere.

## Saving and loading

- [ ] Save **qa**, power off and on, load it: toro is there with every value as you left it, on each pattern
- [ ] Change a value, wait a few seconds and power off without saving: the OP-XY starts normally, and **qa** loads
      as last saved
- [ ] Load **plain**: track 1 has its own sound, nothing of **qa** shows. Load **qa** again: all back
- [ ] While playing, load **plain** and then **qa** again: nothing freezes, no stray values
- [ ] Create a new project: put toro on a track; it starts at its defaults (Aphx at 0)
- [ ] On a firmware without toro, open **qa**: it loads, and the rest of the project plays

## CPU

- [ ] Follow [hardware profiling](https://github.com/etcetc000/open-xy/blob/staging/docs/profiling.md): a profiling
      build from the committed source, every required workload collected, and the readout kept with the commit it
      measured
- [ ] Run `sdk.py profile report`: inspect both average CPU (`block_percent`) and worst observed block CPU
      (`peak_percent`), and the workload that produced the spike. Expect the heaviest settings to be Fold, Res and
      Aphx high together with chords; above 3.5% on either, make that path lighter before submitting
- [ ] Before submitting, copy the complete generated `cpu` member into the catalog entry; resolve clipped or
      invalid peaks rather than omitting them. Hardware evidence still pending means the submission is not ready

## In the builder

Once the catalog entry is merged and released (the beta site from `staging`, open-xy.com from `main`; see
[submitting a machine](https://github.com/etcetc000/open-xy/blob/staging/docs/catalog.md#submit-a-machine)):

- [ ] The machine list shows Toro as Community, with its name, maintainer and description
- [ ] Filtering by synths lists it, and filtering by the other kinds doesn't
- [ ] Searching its name, and each of its keywords, finds it; its details panel lists its keywords
- [ ] Choosing it builds a firmware that includes it, and that firmware passes [Firmware basics](#firmware-basics)

## Known limits

Not failures, but confirm they haven't changed.

- The OP-XY gives engines no velocity: toro's accent is its own four-note cycle, not how hard a key was pressed.
- The screen gets note starts but not pitches, so a note's patch lands on eight spots in turn rather than under its
  key.
- The accent cycle counts notes on the track, so a chord advances it once per note in the chord, and a pattern whose
  note count isn't a multiple of four moves its accents along on each pass. The count doesn't restart with play.
