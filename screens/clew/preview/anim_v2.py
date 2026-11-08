#!/usr/bin/env python3
"""Clew, pass 05 v2 animated: one rippling wave under a stepped compressor line, driven by the same performance as
the audio demo (toro playing a phrase at 120 BPM through Clew, one control added every 8 s).

The picture follows a small model of Clew, worked out from the note schedule and the section's controls:
  - swell 0 is the playing (its level times Dry); swell k is the k-th repeat, arriving k delay times after each
    note at Echo's level times feedback^(k-1)
  - Echo sets the repeat spacing on screen (the stairs widen with longer note lengths)
  - Squeeze lowers the steps (each presses its swell); the first step also dips with the live gain reduction
  - Blend dips the later steps while the playing is loud (the ducking), so the tails are pressed and swell back
  - Space sets how far each step's ripple runs and how strongly it ripples after notes; Tone its grain; Motion a
    slow sway of the steps
  - nothing moves when nothing sounds: the wave's ripple advances only with energy

The soundtrack is a SIMULATION: Clew's and toro's engine code run on a computer, not a recording of an OP-XY.

    python3 anim_v2.py <clew-demo.wav> <out.mp4>
"""
import math, os, subprocess, sys, tempfile
from multiprocessing import Pool
from PIL import Image, ImageDraw, ImageFont

G = ['#000000', '#323232', '#4B4B4B', '#646464', '#7D7D7D', '#969696', '#AFAFAF', '#CDCDCD']
FPS, SEC, SS = 30, 8.0, 3
SECTIONS = [
    ('Dry', [0, 0, 0, 0, 0.5, 0, 1, 0.5624, 0]),
    ('Squeeze 70', [0.7, 0, 0, 0, 0.5, 0, 1, 0.5624, 0]),
    ('+ Echo, dotted 1/8', [0.7, 0.6875, 0, 0, 0.5, 0, 1, 0.5624, 0]),
    ('+ Space 60', [0.7, 0.6875, 0.6, 0, 0.5, 0, 1, 0.5624, 0]),
    ('+ Blend 100', [0.7, 0.6875, 0.6, 1, 0.5, 0, 1, 0.5624, 0]),
    ('+ Motion 70, Tone -40', [0.7, 0.6875, 0.6, 1, 0.3, 0.7, 1, 0.5624, 0]),
    ('Order: FX first', [0.7, 0.6875, 0.6, 1, 0.3, 0.7, 1, 0.5624, 0.75]),
]
DIVS = [1, 1.5, 2, 3, 4, 6, 8, 16]                       # sixteenths: 1/32 .. 1/2
STEP = 60.0 / 120 / 4
DUR = len(SECTIONS) * SEC

# the phrase, as in the audio demo: per bar eight 16ths (loud, quiet), a held quarter, then a rest
NOTES = []
bar = 0
while bar * 16 * STEP < DUR:
    for s in range(9):
        NOTES.append(((bar * 16 + s) * STEP, 0.7 if s == 8 else (0.22 if s % 2 else 0.8), STEP * 1.8 if s == 8 else STEP * 0.6))
    bar += 1


def params(t):
    k = min(len(SECTIONS) - 1, int(t / SEC))
    a, b = SECTIONS[max(0, k - 1)][1], SECTIONS[k][1]
    x = min(1.0, (t - k * SEC) / 0.6) if k else 1.0
    return [a[i] + (b[i] - a[i]) * x for i in range(9)], SECTIONS[k][0], b


def shape(tau, length):
    if tau < 0: return 0.0
    att = 1 - math.exp(-tau / 0.008)
    return att * (math.exp(-max(0.0, tau - length) / 0.06) if tau > length else 1.0) * math.exp(-tau / 0.9)


def level(t, delay=0.0, back=1.2):
    return sum(a * shape(t - tn - delay, ln) for tn, a, ln in NOTES if t - back - delay < tn <= t - delay)


def state(t):
    p, title, target = params(t)
    sq, echo, space, blend, tone, motion, dry, attack, order = p
    tone = 2 * tone - 1
    div = DIVS[min(7, int(echo * 8))] if echo > 0.01 else 6
    delay = div * STEP
    fb = 0.15 + 0.6 * echo
    elevel = min(1.0, echo * 8) * 0.8
    x_in = level(t)
    swells = [x_in * dry]
    for k in range(1, 4):
        swells.append(level(t, k * delay) * elevel * fb ** (k - 1))
    room = space * sum(a * math.exp(-(t - tn) / (0.25 + 3 * space * space)) for tn, a, ln in NOTES if t - 4 < tn <= t)
    follower = min(1.0, level(t) / 0.6)
    return dict(t=t, title=title, target=target, sq=sq, echo=echo, space=space, blend=blend, tone=tone, motion=motion,
                order=order, swells=swells, room=min(1.2, room), duck=blend * follower, gr=sq * follower, div=div)


def energy(t):
    s = state(t)
    return sum(s['swells']) + s['room']


# the wave's phase advances only with sound, so the rest frame never moves
PHASE = [0.0]
for i in range(1, int(DUR * FPS) + 1):
    PHASE.append(PHASE[-1] + 2 * math.pi * 0.9 / FPS * min(1.0, energy(i / FPS) * 4))


def squeeze(v, limit):
    a = abs(v)
    if a <= limit * 0.6: return v
    over = a - limit * 0.6
    return math.copysign(limit * 0.6 + over / (1 + over / (limit * 0.4)), v)


fonts = {}
def font(px, light=True):
    key = (px, light)
    if key not in fonts:
        fonts[key] = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-%s.otf' % ('Light' if light else 'Regular'), int(px * SS))
    return fonts[key]


def header(d, s):
    def fmt(i, v):
        if i == 1: return {1: '1/32', 1.5: '3/64', 2: '1/16', 3: '3/32', 4: '1/8', 6: '3/16', 8: '1/4', 16: '1/2'}[s['div']] if v > 0.01 else 'off'
        if i == 4: return f'{round((2 * v - 1) * 100):+d}' if abs(2 * v - 1) > 0.005 else '0'
        if i == 7: return f'{0.5 * 60 ** v:.1f}'
        return f'{round(v * 100)}'
    v = s['target']
    page2 = s['title'].startswith('+ Motion')
    for i in range(8):
        d.rectangle((60 * i * SS, 0, (60 * i + 60) * SS, 20 * SS), fill=G[i])
    names = ['squeeze', 'echo', 'space', 'blend', 'tone', 'motion', 'dry', 'attack']
    top = range(4, 8) if page2 else range(0, 4)
    low = range(0, 4) if page2 else range(4, 8)
    for k, i in enumerate(top):
        c = '#CBCBCB' if k < 2 else '#000000'
        d.text(((5 + 120 * k) * SS, 10 * SS), names[i], fill=c, font=font(10), anchor='ls')
        d.text(((65 + 120 * k) * SS, 17.4 * SS), fmt(i, v[i]), fill=c, font=font(20), anchor='ls')
    for k, i in enumerate(low):
        d.text(((5 + 120 * k) * SS, 33 * SS), names[i], fill='#5A5A5A', font=font(10), anchor='ls')
        d.text(((65 + 120 * k) * SS, 33 * SS), fmt(i, v[i]), fill='#707070', font=font(13), anchor='ls')


def frame(i):
    t = i / FPS
    s = state(t)
    im = Image.new('RGB', (480 * SS, 220 * SS), 'black'); d = ImageDraw.Draw(im)
    header(d, s)
    L = lambda pts, w, col: d.line([(x * SS, y * SS) for x, y in pts], fill=col, width=max(1, round(w * SS)), joint='curve')
    c = 150
    spacing = 72 + 48 * min(1.0, s['echo'] / 0.875) if s['echo'] > 0.01 else 120
    x0 = 10
    base_limit = 64 - 40 * s['sq']
    sway = s['motion'] * 3 * math.sin(t * 2 * math.pi * 0.3)
    steps = []
    for k in range(4):
        a, b = x0 + k * spacing - 4, x0 + (k + 1) * spacing - 4
        if k == 3: b = 474
        lim = base_limit * (0.82 ** k)
        lim -= (s['gr'] * 10 * s['sq']) if k == 0 else (s['duck'] * 16)
        lim = max(4.0, lim)
        y = c - lim + (sway if k % 2 else -sway) * (k > 0)
        steps.append((max(6, a), min(474, b), y, lim))
    # the steps: a riser between treads; the far part of each tread ripples with the room
    for k, (a, b, y, lim) in enumerate(steps):
        reach = 0.25 + 0.6 * s['space']
        solid_end = a + (b - a) * (1 - reach)
        L([(a, y), (solid_end, y)], 1.5, G[5])
        amp = (1.0 + 7 * s['room']) * (0.6 + 0.4 * k / 3) * (s['space'] > 0.01)
        waves = 5 + 3 * (s['tone'] + 1)
        pts = []
        for n in range(41):
            u = n / 40
            pts.append((solid_end + (b - solid_end) * u, y + amp * u * math.sin(u * waves * 2 * math.pi - PHASE[i] * 1.3)))
        L(pts, 1.0, G[4])
        if k < 3:
            L([(b, y), (b, steps[k + 1][2])], 1.5, G[5])
    # the wave: one line, a swell per step, each pressed by its step
    amps = [80 * v for v in s['swells']]
    pts, bright = [], []
    x = 8.0
    while x <= 472:
        k = min(3, max(0, int((x - x0 + 4) // spacing)))
        dx = x - (x0 + k * spacing)
        env = 0.0
        for j in range(4):
            d0 = x - (x0 + j * spacing)
            if d0 >= -2:
                env = max(env, amps[j] * (1 - math.exp(-max(0, d0) / 4)) * math.exp(-max(0, d0) * 0.022))
        env = max(env, 1.2)                                  # the line never quite vanishes
        v = env * math.sin(2 * math.pi * (x - x0) / 11 - PHASE[i])
        lim = steps[k][3] - 2
        y = c - squeeze(v, max(1.5, lim)) if s['order'] < 0.5 or True else c - v
        (bright if x < x0 + 60 and amps[0] > 6 else pts).append((x, y))
        x += 0.6
    if bright:
        L(bright, 2.2, G[7])
        pts.insert(0, bright[-1])
    L(pts, 1.5, G[5])
    L([(6, 206), (474, 206)], 1.0, G[2])
    return im.resize((960, 440), Image.LANCZOS)


def full(i):
    s = state(i / FPS)
    out = Image.new('RGB', (960, 440 + 56), (10, 10, 10))
    out.paste(frame(i), (0, 0))
    d = ImageDraw.Draw(out)
    d.text((16, 452), s['title'], fill='#CDCDCD', font=ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Regular.otf', 22))
    d.text((944, 456), 'audio: simulated (engine code on a computer, not an OP-XY)', fill='#646464',
           font=ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-Regular.otf', 15), anchor='ra')
    return out


def job(args):
    i, folder = args
    full(i).save(os.path.join(folder, f'f{i:05d}.png'))


if __name__ == '__main__':
    wav, out = sys.argv[1], sys.argv[2]
    folder = tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(out)))
    n = int(DUR * FPS)
    with Pool() as p: p.map(job, [(i, folder) for i in range(n)], chunksize=12)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', os.path.join(folder, 'f%05d.png'), '-i', wav,
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                    '-metadata', 'comment=Audio is simulated: Clew and toro engine code run on a computer, not recorded from an OP-XY.',
                    '-shortest', out], check=True)
    print(out)
