# Clew v2 animation (pass 05 v2)

`clew-v2-anim.mp4` shows pass 05's v2: one rippling wave under a compressor line stepping down, one step per encoder
column. It plays the same 56 s performance as the audio demo: toro plays a phrase at 120 BPM through Clew, with one
control added every 8 s (dry, Squeeze 70, Echo at a dotted eighth, Space 60, Blend 100, Motion 70 with Tone -40,
then Order FX first).

**The audio is simulated**: Clew's and toro's engine code run on a computer, not a recording from an OP-XY.

The picture comes from a small model of Clew (`anim_v2.py`), not from `display.cpp`, which doesn't exist yet. The
playing is the first swell, each repeat a swell a step further on, arriving one delay time later. Squeeze lowers the
steps; the first also dips with the gain reduction. Blend dips the later steps while the playing is loud. Space sets
how far and how strongly each step's tail ripples, Tone its grain, Motion a slow sway. The wave's ripple only
advances while there's sound, so the rest frame doesn't move.
