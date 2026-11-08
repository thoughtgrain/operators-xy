# Clew previews

**The audio in both videos is simulated**: Clew's and toro's engine code run on a computer, not a recording from an
OP-XY. Both play the same 56 s performance: toro plays a phrase at 120 BPM through Clew, with one control changed
every 8 s (dry, Squeeze 70, Echo at a dotted eighth, Space 60, Blend 100, Motion 70 with Tone -40, then Order FX
first).

## `clew-device.mp4`: the built screen

Made by `anim_device.py` from `gen_clew.py`, the generator behind the stills and the handoff, so it shows what
`display.cpp` will draw. An effect page sees its controls, Shift and the time, never the playing, so the picture
changes only when a control does, easing over 0.15 s (`motion.md`), and stays still while the notes play. Page 2
controls show the second header page; the Order change shows Shift held for 1.5 s, with Order in the edited row.

## `clew-v2-anim.mp4`: pass 05's sketch

Made by `anim_v2.py` from a small model of Clew before the screen was built. It drew the swells rising with each
note and the tails ducking under the playing. That's what the sound does, but the device page can't follow it, so
this video is the idea, not the screen.
