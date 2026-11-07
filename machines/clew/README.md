# Clew

A compressor, a tempo-synced delay and a small reverb in one send effect. One level follower listens to what comes
in and drives all three: it sets the compression, and with Blend up it ducks the echoes and the room while you
play, so they swell back in the gaps. The idea comes from the way Chase Bliss's Clean makes a compressor move with
the playing; Clew applies that to the tails, too.

## Controls

Press any encoder to switch pages. Hold Shift for the Order row.

| Page | Control | What it does |
| --- | --- | --- |
| 1 | Squeeze | Compression on one control: threshold -3 to -33 dB, ratio 1:1 to 8:1 and make-up rise together; 0 is off |
| 1 | Echo | The delay. Its time steps through stock delay's note lengths at the track's tempo (1/32 to 1/2) and the repeats grow as it goes up; at 0 there are none |
| 1 | Space | The room: decay from 0.25 to 3.25 s and level together; at 0 there is none |
| 1 | Blend | How much the playing ducks the echoes and the room: at 0 they're steady, at 100 they drop about 10 dB under the notes and come back within a few hundred milliseconds |
| 2 | Tone | The tails only, -100 to +100: darker to the left (and their repeats and room damp faster), thinner to the right |
| 2 | Motion | A slow wobble in the echoes' time (up to 2 ms, a quarter cycle apart left and right) and a drift in the room |
| 2 | Dry | The playing's own level in the box; at 0 only the tails come back |
| 2 | Attack | How fast the compressor and the ducking catch a note, 0.5 to 30 ms |
| Shift | Order | **Comp first** compresses the playing, then echoes and rooms it. **FX first** echoes and rooms it, then compresses the playing and its tails together, so the tails pump with the playing |

The first four are the ones the send's LFOs can reach.

## How it sits on a send

Clew mixes its own dry (`dryLevel` 0 in `machine.json`). At a track's send of 100 the whole track goes through it,
like an insert, and the compressor works on the track itself. At less, the rest of the track stays dry around it.
The compressor and the ducking always listen to what comes into the send.

## How it's built, and why

- **One follower, every 16 samples.** The level follower runs per sample (a fast and a slow release, so short peaks
  recover quickly and sustained notes stay even); the gain and the ducking are worked out in log2 units every 16
  samples and ramped between, which keeps the log and exp maths off the per-sample path.
- **The room runs at half rate.** Four lines mixed by a Hadamard matrix after two allpass diffusers, run on every
  other sample and interpolated back up. That halves its cost, and the tone of a small room doesn't miss what's
  above 11 kHz.
- **Motion is set once a block.** The wobble moves the echoes' delay target and the per-sample glide smooths it, so
  the modulation costs nothing per sample.
- **Its own buffer, cleared first.** The send slot's memory is never cleared for us, so Clew zeroes its 368 KB over
  the first dozen blocks (about 17 ms) and passes only the dry until then.
- **An output safety.** Make-up gain and full tails can add up: above 0.75 the output bends smoothly into full
  scale instead of clipping.

## Checks

```sh
python ../open-xy/sdk.py test --machine machines/clew
```

`tests/sound.cpp` checks that silence and an empty send stay silent; that the dry passes untouched while the buffer
clears; that an eighth at 120 and 150 BPM lands on its sample and Echo 0 has no repeats; that Squeeze 100 closes
24 dB between a loud and a quiet tone to about 3 dB and Squeeze 0 is transparent; that Blend ducks the tails over
10 dB while playing and lets them back after; that every tail decays and the output stays below full scale; that
Tone darkens; and that Order changes the result.

The host CPU estimate varies a lot from run to run on a shared machine, roughly 19,000 to 32,000 instructions per
block against the SDK's aim of 30,000; counting instructions instead of timing them gives about 12,000. Only the
device profile counts.

Device: pending. No hardware CPU record yet.
