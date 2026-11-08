# Clew previews

**The audio in both videos is simulated**: Clew's and toro's engine code run on a computer, not a recording from an
OP-XY. Both play the same 56 s performance: toro plays a phrase at 120 BPM through Clew, with one control changed
every 8 s (dry, Squeeze 70, Echo at a dotted eighth, Space 60, Blend 100, Motion 70 with Tone -40, then Order FX
first).

## `clew-device.mp4`: the screen

`python3 anim_device.py clew-device.mp4`. Drawn by `gen_clew.py`, the generator behind the stills and the handoff:
the wave is Clew's output scrolling in from the right, the step line is the compressor coming down onto it, and the
ripple on each step's tail is the room. The levels come from `sim/scope.cpp`, the same run that makes the audio.
The device page needs an SDK change before it can receive them (`handoff.md`); this is what it draws once it does.
Page 2 controls show the second header page; the Order change shows Shift held for 1.5 s.

## `clew-v2-anim.mp4`: pass 05's sketch

Made by `anim_v2.py` from a small model of Clew before the screen was built: the idea the owner picked.
