# Testing Clew on an OP-XY

Checks to run on a device with a firmware that includes Clew, top to bottom, in one project: each section leaves
the project ready for the next. To run only some sections, set up what their first line says. The host tests
(`python ../open-xy/sdk.py test --machine machines/clew`) don't replace these: they can't hear the sound.

Report a failure with the section, the line and what you saw. Note the Clew commit, the SDK commit and the firmware
each full pass used. When a change adds, removes or alters something a person would check on the device, update the
lines here in the same commit.

## Setup

- Build a firmware with Clew ([building firmware](https://github.com/etcetc000/open-xy/blob/staging/docs/build.md#3-add-your-machine))
  and install it.
- Create a new project, **plain**, without Clew: give track 1 a stock sound of its own and save it. Later steps
  load it as a project that never had the machine.
- Create another new project, **qa**, for the pass: don't use a project you care about.
- Track 1: a stock synth playing a phrase with loud and quiet notes and a rest in every bar (16ths for half a bar,
  then a held note, then nothing), at 120 BPM.
- Track 15 (a send): Clew (Shift + track 15's key, then choose it). Turn track 1's send to track 15 to 100.
- Press play, and leave it playing unless a step says otherwise.

## Firmware basics

- [ ] The OP-XY boots, and stock engines, effects, the sequencer and project save/load work
- [ ] Clew is in the effect list of tracks 15 and 16 (Shift + their track keys), as "Clew", and in no other
      track's list

## Its page and controls

- [ ] The send page shows Squeeze / Echo / Space / Blend; pressing any encoder switches to Tone / Motion / Dry /
      Attack and back, and each control keeps its own value
- [ ] Holding Shift shows Order, choosing Comp first or FX first one per detent
- [ ] At the defaults (Squeeze 35, Echo 1/8, Space 35, Blend 50, Tone 0, Motion 20, Dry 100, Attack 5 ms) the
      track sounds evened out, with echoes and a small room that dip while it plays
- [ ] Squeeze 0 → 100: from untouched to tightly levelled; the quiet notes come up towards the loud ones, with no
      pumping at the default Attack
- [ ] Echo through its range: the value reads as note lengths 1/32 → 1/2, the repeats land on the beat at each,
      grow longer as it rises, and slide (not click) when it changes; at 0 there are no repeats
- [ ] Change the tempo while echoes ring: their time follows
- [ ] Space 0 → 100: from no room to a long tail of about three seconds; no ringing or metallic tone
- [ ] Blend 0 → 100 with Echo and Space up: at 0 the tails are steady; at 100 they drop under the notes and swell
      into the rest in each bar
- [ ] Tone -100 → +100: the tails darken to the left and thin out to the right; the dry stays the same
- [ ] Motion 0 → 100: the echoes waver gently in pitch and spread left and right; the room drifts; nothing jumps
- [ ] Dry 100 → 0: the track's own sound fades out of the send, leaving only the tails
- [ ] Attack 0.5 → 30 ms: slower Attack lets the starts of loud notes through before the compressor catches them
- [ ] Order: FX first makes the tails pump with the playing as well; Comp first leaves them free
- [ ] Each control through its whole range, both directions, fast and slow: no clicks, jumps or silence at the ends
- [ ] At extreme settings (Squeeze, Echo, Space and Blend at 100, FX first) the output stays clean: it may get loud
      but doesn't crackle or clip harshly
- [ ] With track 1's send at 0 the track sounds as it does without Clew; raising it to 100 moves the whole track
      into Clew smoothly
- [ ] Stop the sequencer while a note rings: echoes and room ring out naturally, with no click
- [ ] Clew on track 16 too, at the same time as on track 15: each keeps its own values and buffer
- [ ] Choose Clew on a send that just had stock delay or reverb: no burst of the old effect's sound when it starts

## LFOs

- [ ] Track 15's LFO lists Squeeze, Echo, Space and Blend; moving each is heard, and Echo moving through note
      lengths slides rather than clicking

Then turn the LFO off.

## Parameter locks

- [ ] Lock each control on a step (hold the step, turn the knob): it plays on that step, and the page shows the
      lock while the step is held
- [ ] Lock Echo to 1/16 on one step only: that step's echoes are faster; the time slides back after
- [ ] Several locks on one step, and locks on neighbouring steps: each plays as written
- [ ] Clear the locks: the control plays its own value again

## Patterns, scenes and songs

- [ ] Give the track a second pattern with different values: each pattern keeps its own
- [ ] Copy a pattern: the copy holds the same values, and changing one leaves the other alone
- [ ] Switch between the patterns while playing and while stopped: the sound and the page follow at once
- [ ] Make scenes 1 and 2 with the two patterns, and a song of scene 1 then scene 2, looping: each scene plays its
      own values from its first bar, on every pass

Then play scene 1.

## Mute

- [ ] Mute track 15 (hold aux and press its key): it's silent, with no click or tail left behind; unmute: it plays
      as before
- [ ] The same from the mixer
- [ ] Muted in scene 2 only: switching between scenes 1 and 2 mutes and unmutes it

Unmute it everywhere.

## Saving and loading

- [ ] Save **qa**, power off and on, load it: Clew is there with every value and Order as you left them, on each
      pattern
- [ ] Change a value, wait a few seconds and power off without saving: the OP-XY starts normally, and **qa** loads
      as last saved
- [ ] Load **plain**: track 1 has its own sound, nothing of **qa** shows. Load **qa** again: all back
- [ ] While playing, load **plain** and then **qa** again: nothing freezes, no stray values
- [ ] Create a new project: put Clew on a send; it starts at its defaults, Order Comp first
- [ ] On a firmware without Clew, open **qa**: it loads, and the rest of the project plays

## CPU

- [ ] Follow [hardware profiling](https://github.com/etcetc000/open-xy/blob/staging/docs/profiling.md): a profiling
      build from committed source, every required workload collected, and the readout kept with the commit it
      measured
- [ ] Run `sdk.py profile report`: inspect both average CPU (`block_percent`) and worst observed block CPU
      (`peak_percent`), and the workload that produced the spike. Expect Space and Echo high together to be the
      heaviest; above 3.5% on either, make that path lighter before submitting
- [ ] Before submitting, copy the complete generated `cpu` member into the catalog entry; resolve clipped or invalid
      peaks rather than omitting them. Hardware evidence still pending means submission is not ready

## In the builder

Once the catalog entry is merged and released (the beta site from `staging`, open-xy.com from `main`; see
[submitting a machine](https://github.com/etcetc000/open-xy/blob/staging/docs/catalog.md#submit-a-machine)):

- [ ] The machine list shows Clew as Community, with its name, maintainer and description
- [ ] Filtering by effects lists it, and filtering by the other kinds doesn't
- [ ] Searching its name, and each of its keywords, finds it; its details panel lists its keywords
- [ ] Choosing it builds a firmware that includes it, and that firmware passes [Firmware basics](#firmware-basics)

## Known limits

Not failures, but confirm they haven't changed.

- Clew uses the stock send page; it has no screen of its own yet.
- The longest echo is a second: at slow tempos 1/2 (and at very slow ones 1/4) is held to a second.
- The compressor and the ducking listen to what comes into the send, never to the tails, even with FX first.
- The first ~17 ms after Clew is chosen pass only the dry, while it clears its buffer.
