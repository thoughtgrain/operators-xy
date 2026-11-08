#!/usr/bin/env python3
"""Clew's screen (pass 05 v2) over the audio demo, drawn by gen_clew.py, the generator behind the stills and the
handoff, so it's the device's drawing: one wave (the playing's swell, then each repeat's) under a compressor line
that steps down, dipping with the gain reduction and the ducking, the room rippling on each step's tail.

What's sounding comes from the send's input levels, which sim/scope.cpp writes while it runs toro and Clew's engine
code on a computer. The device page needs an SDK change before it receives them (handoff.md).

The score: toro plays a phrase at 120 BPM through Clew and a control changes every 8 s. Page 2 controls (Motion,
Tone) show the second header page; the Order change shows Shift held for 1.5 s.

The soundtrack is a SIMULATION: Clew's and toro's engine code run on a computer, not a recording of an OP-XY.

    python3 anim_device.py <out.mp4>
"""
import hashlib
import os
import subprocess
import sys
import tempfile
from multiprocessing import Pool
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import gen_clew  # noqa: E402

FPS, SEC, HALF = 30, 8.0, 0.021          # the header helper's ease: halve the distance every 21 ms
SECTIONS = [
    ('Dry', [0, 0, 0, 0, 0.5, 0, 1, 0.5624, 0]),
    ('Squeeze 70', [0.7, 0, 0, 0, 0.5, 0, 1, 0.5624, 0]),
    ('+ Echo, dotted 1/8', [0.7, 0.6875, 0, 0, 0.5, 0, 1, 0.5624, 0]),
    ('+ Space 60', [0.7, 0.6875, 0.6, 0, 0.5, 0, 1, 0.5624, 0]),
    ('+ Blend 100', [0.7, 0.6875, 0.6, 1, 0.5, 0, 1, 0.5624, 0]),
    ('+ Motion 70, Tone -40 (page 2)', [0.7, 0.6875, 0.6, 1, 0.3, 0.7, 1, 0.5624, 0]),
    ('Order: FX first (Shift held)', [0.7, 0.6875, 0.6, 1, 0.3, 0.7, 1, 0.5624, 1]),
]
DUR = len(SECTIONS) * SEC
FONT = '/usr/share/fonts/opentype/inter/Inter-Regular.otf'


def score(peaks):
    """per frame: the eased controls, the header page, Shift and the section title, stepped like the device"""
    out, shown = [], list(SECTIONS[0][1])
    phase = sway = 0.0
    for i in range(int(DUR * FPS)):
        t = i / FPS
        k = min(len(SECTIONS) - 1, int(t / SEC))
        title, target = SECTIONS[k]
        keep = 0.5 ** ((1 / FPS) / HALF)
        shown = [b + (a - b) * keep for a, b in zip(shown, target)]
        shown = [b if abs(a - b) < 1e-3 else a for a, b in zip(shown, target)]    # settled: stop exactly
        shift = k == 6 and t - k * SEC < 1.5
        page = 1 if k == 5 else 0
        lv = gen_clew.live(shown, peaks[0], int(t / gen_clew.WIN_S))
        phase, sway = gen_clew.advance(phase, sway, lv, FPS)
        out.append((tuple(round(v, 4) for v in shown), page, shift, title, lv, phase, sway))
    return out


def render(job):
    svg, png = job
    with tempfile.NamedTemporaryFile('w', suffix='.svg', delete=False) as f:
        f.write(svg)
    subprocess.run(['rsvg-convert', '-w', '960', '-h', '440', f.name, '-o', png], check=True)
    os.unlink(f.name)


def main():
    out = sys.argv[1]
    folder = Path(tempfile.mkdtemp(dir=Path(out).resolve().parent))
    gen_clew.build_sim()
    wav, peaks_txt = str(folder / 'demo.wav'), str(folder / 'peaks.txt')
    subprocess.run([str(gen_clew.SIM_BIN), 'demo', wav, peaks_txt], check=True)
    frames = score(gen_clew.read_peaks(peaks_txt))
    svgs = [gen_clew.frame_svg(list(c), page=p, shift=s, lv=lv, phase=ph, sway=sw) for c, p, s, _, lv, ph, sw in frames]
    unique = {}
    for svg in svgs:
        unique.setdefault(hashlib.sha1(svg.encode()).hexdigest(), svg)
    with Pool() as pool:
        pool.map(render, [(svg, str(folder / f'{h}.png')) for h, svg in unique.items()], chunksize=4)
    big, small = ImageFont.truetype(FONT, 22), ImageFont.truetype(FONT, 15)
    for i, (fr, svg) in enumerate(zip(frames, svgs)):
        title = fr[3]
        h = hashlib.sha1(svg.encode()).hexdigest()
        im = Image.new('RGB', (960, 440 + 56), (10, 10, 10))
        im.paste(Image.open(folder / f'{h}.png').convert('RGB'), (0, 0))
        d = ImageDraw.Draw(im)
        d.text((16, 452), title, fill='#CDCDCD', font=big)
        d.text((944, 450), 'audio: simulated (engine code on a computer, not an OP-XY)', fill='#646464', font=small, anchor='ra')
        d.text((944, 470), 'levels: needs an SDK change to reach the page', fill='#646464', font=small, anchor='ra')
        im.save(folder / f'f{i:05d}.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(folder / 'f%05d.png'), '-i', wav,
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                    '-metadata', 'comment=Audio is simulated: Clew and toro engine code run on a computer, not recorded from an OP-XY.',
                    '-shortest', out], check=True)
    for f in folder.iterdir():
        f.unlink()
    folder.rmdir()
    changed = sum(1 for a, b in zip(svgs, svgs[1:]) if a != b)
    print(f'{out}: {len(frames)} frames, {len(unique)} distinct, {changed} frame changes')


if __name__ == '__main__':
    main()
