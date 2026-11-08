# Clew previews

**The audio in both videos is simulated**: Clew's and toro's engine code run on a computer, not a recording from an
OP-XY. Both play the same 56 s performance: toro plays a phrase at 120 BPM through Clew, with one control changed
every 8 s (dry, Squeeze 70, Echo at a dotted eighth, Space 60, Blend 100, Motion 70 with Tone -40, then Order FX
first).

## `clew-device.mp4`: the screen

`python3 anim_device.py clew-device.mp4`. Pass 05 v2 built for the device, drawn by `gen_clew.py`, the generator
behind the stills and the handoff. What's sounding is worked out from the input levels `sim/scope.cpp` writes in
the same run as the audio. The device page needs an SDK change before it receives them (`handoff.md`). Page 2
controls show the second header page; the Order change shows Shift held for 1.5 s. Where it differs from the sketch,
and why, is in `review.md`.

## `clew-v2-anim.mp4`: pass 05's sketch

Made by `anim_v2.py` from a small model of Clew: the version the owner picked, and the reference for the build.
