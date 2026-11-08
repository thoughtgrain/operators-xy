#!/usr/bin/env python3
"""Clew, revision pass 05: the stepped ceiling (pass 04 v1) with one continuous rippling wave. The playing and its
echoes are swells along a single wave; a compressor line steps down across the screen, pressing each swell; the room
ripples on the line. Five variations, each taking its direction from design_pass_start.

  v1  stairs falling on a diagonal, seen from below (treads as thin slabs), the wave threading under them
  v2  the whole width: one wave and four treads edge to edge; the note's swell brightest
  v3  a centred funnel: treads stepping down from above and up from below, the wave squeezed between, its ripple
      crowding towards the middle
  v4  the stairs as a solid cut in section over a low wave near the horizon; the first echo's swell brightest
  v5  isometric slabs, one per encoder column, with the wave running beneath as a ribbon; the source brightest

    python3 gen.py        # writes v1..v5/rest.svg
"""
import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('frames02', HERE.parent / '02-frames' / 'gen.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
Frame, G, HAIR, LINE, SUBJ = base.Frame, base.G, base.HAIR, base.LINE, base.SUBJ


def squeeze(v, limit):
    a = abs(v)
    if a <= limit * 0.6:
        return v
    over = a - limit * 0.6
    return math.copysign(limit * 0.6 + over / (1 + over / (limit * 0.4)), v)


def envelope(x, x0, spacing, amps, attack=4.0, fall=0.022):
    """the wave's size at x: a swell for the note at x0 and one per echo, every `spacing` px, each smaller"""
    e = 0.0
    for k, a in enumerate(amps):
        d = x - (x0 + k * spacing)
        if d >= 0:
            e = max(e, a * (1 - math.exp(-d / attack)) * math.exp(-d * fall))
    return e


def wave(x0, x1, centre, env, limit, period=11.0, step=0.5):
    """one continuous wave from x0 to x1: centre(x), size env(x) pressed to limit(x)"""
    pts, x = [], x0
    while x <= x1:
        v = env(x) * math.sin(2 * math.pi * (x - x0) / period)
        pts.append((x, centre(x) - squeeze(v, max(1.5, limit(x)))))
        x += step
    return pts


def ripple(F, x0, x1, y, amp, waves, col, w=HAIR, n=80):
    pts = [(x0 + (x1 - x0) * k / n, y + amp * (k / n) * math.sin(k / n * waves * 2 * math.pi)) for k in range(n + 1)]
    F.line(pts, w, col)


def split_by(F, pts, cuts, styles):
    """draws one polyline in pieces (sharing ends) so one stretch can be brighter: cuts are x positions"""
    edges = [pts[0][0]] + cuts + [pts[-1][0] + 1]
    for k in range(len(edges) - 1):
        seg = [p for p in pts if edges[k] <= p[0] <= edges[k + 1] + 0.5]
        if len(seg) > 1:
            F.line(seg, *styles[k])


def treads_limit(treads, centre_y):
    def lim(x):
        for (a, b, y) in treads:
            if a <= x < b:
                return centre_y - y - 2
        return centre_y - treads[-1][2] - 2
    return lim


def v1_diagonal():
    F = Frame()
    # stairs falling from upper left to lower right, seen from below: each tread a thin slab showing its underside
    treads = [(24, 124, 64), (124, 224, 92), (224, 324, 120), (324, 424, 148)]
    for k, (a, b, y) in enumerate(treads):
        F.poly([(a, y), (b, y), (b + 6, y + 4), (a + 6, y + 4)], '#000000', G[4], HAIR)
        if k < 3:
            F.line([(b, y), (b, treads[k + 1][2])], HAIR, G[4])
        ripple(F, a + (b - a) * 0.5, b, y + 4, 3, 4, G[3])
    # the wave threads under the stairs on the diagonal: its centre falls with them
    # the wave threads under the stairs, its centre falling with them and each tread pressing its swell
    centre = lambda x: 96 + (x - 24) * 0.21
    lim = lambda x: next((centre(x) - y - 6 for (a, b, y) in treads if a <= x < b), 6)
    env = lambda x: envelope(x, 26, 100, [40, 32, 25, 18], fall=0.016)
    F.line(wave(26, 424, centre, env, lim, period=13.0, step=0.4), LINE, G[5])
    return F


def v2_full():
    F = Frame()
    treads = [(6, 120, 100), (120, 240, 112), (240, 360, 122), (360, 474, 130)]
    for k, (a, b, y) in enumerate(treads):
        F.line([(a, y), (a + (b - a) * 0.5, y)], LINE, G[5])
        ripple(F, a + (b - a) * 0.5, b, y, 3 + k, 4 + k, G[4])
        if k < 3:
            F.line([(b, y), (b, treads[k + 1][2])], LINE, G[5])
    c = 150
    pts = wave(8, 472, lambda x: c, lambda x: envelope(x, 10, 120, [62, 48, 36, 26]), treads_limit(treads, c))
    split_by(F, pts, [70], [(SUBJ, G[7]), (LINE, G[5])])     # the note's swell: the brightest part
    F.line([(6, 206), (474, 206)], HAIR, G[2])
    return F


def v3_funnel():
    F = Frame()
    cx, c = 240, 126
    # treads from above step down and from below step up, narrowing towards the middle and opening again
    gaps = [52, 40, 28, 18, 28, 40]
    xs = [cx - 150 + 50 * k for k in range(7)]
    for k, g in enumerate(gaps):
        a, b = xs[k], xs[k + 1]
        F.line([(a, c - g), (b, c - g)], LINE, G[5])
        F.line([(a, c + g), (b, c + g)], LINE, G[5])
        if k < len(gaps) - 1:
            g2 = gaps[k + 1]
            F.line([(b, c - g), (b, c - g2)], HAIR, G[4]); F.line([(b, c + g), (b, c + g2)], HAIR, G[4])
    def lim(x):
        for k in range(len(gaps)):
            if xs[k] <= x < xs[k + 1]:
                return gaps[k] - 3
        return 50
    # the wave: its ripple crowds closer together towards the middle (the density gradient)
    pts, x = [], xs[0] - 30
    phase = 0.0
    while x <= xs[-1] + 30:
        period = 6 + 12 * min(1, abs(x - cx) / 160)
        phase += 2 * math.pi * 0.5 / period
        env = 44 * math.exp(-max(0, x - xs[0]) * 0.004)
        pts.append((x, c - squeeze(env * math.sin(phase), lim(x))))
        x += 0.5
    F.line(pts, LINE, G[6])
    return F


def v4_section():
    F = Frame()
    hz = 204
    F.line([(6, hz), (474, hz)], HAIR, G[3])
    # the stairs as a solid mass above, cut in section: hatched, its stepped underside pressing a low wave
    treads = [(6, 120, 120), (120, 240, 134), (240, 360, 146), (360, 474, 156)]
    outline = []
    for (a, b, y) in treads:
        outline += [(a, y), (b, y)]
    F.line(outline, LINE, G[5])
    for k, (a, b, y) in enumerate(treads):
        x = a + 3
        while x < b - 4:
            F.line([(x, y - 3), (x + 8, y - 14)], HAIR * 0.9, G[2])
            x += 6
        ripple(F, a + (b - a) * 0.55, b - 2, y + 3, 2 + k * 0.8, 4, G[3])
    c = 180
    pts = wave(8, 472, lambda x: c, lambda x: envelope(x, 10, 120, [40, 32, 24, 18]), treads_limit(treads, c))
    split_by(F, pts, [130, 200], [(LINE, G[5]), (SUBJ, G[7]), (LINE, G[4])])    # the first echo's swell: brightest
    return F


def v5_iso():
    F = Frame()
    def P(x, y, z):                  # x across, z into the screen, y up
        return (22 + x + z * 0.5, 176 - y - z * 0.36)
    # one slab per encoder column, each a step lower, thin, with depth
    steps = [(0, 95, 62), (105, 200, 54), (210, 305, 47), (315, 400, 41)]
    for k, (a, b, y) in enumerate(steps):
        F.poly([P(a, y, 0), P(b, y, 0), P(b, y - 5, 0), P(a, y - 5, 0)], '#000000', G[4], HAIR)
        F.poly([P(b, y, 0), P(b, y, 60), P(b, y - 5, 60), P(b, y - 5, 0)], '#000000', G[3], HAIR)
        F.poly([P(a, y, 0), P(b, y, 0), P(b, y, 60), P(a, y, 60)], '#000000', G[5], HAIR)
        ripple(F, *P(a + (b - a) * 0.5, y, 0)[0:1], *P(b, y, 0)[0:1], P(b, y, 0)[1] + 0.0, 3, 4, G[3]) if False else None
        pts = [P(a + (b - a) * (0.5 + 0.5 * t / 60), y + 2 * (t / 60) * math.sin(t / 60 * 8 * math.pi), 60) for t in range(61)]
        F.line(pts, HAIR, G[4])                                   # the room rippling along the slab's back edge
    # the wave beneath, a ribbon at mid depth: its centre at y = 30, pressed under each slab
    def lim(x):
        for (a, b, y) in steps:
            if a <= x < b + 10:
                return y - 5 - 26 - 2
        return 7
    env = lambda x: envelope(x, 4, 110, [34, 27, 21, 16])
    pts3 = wave(4, 410, lambda x: 26, env, lim)
    pts = [P(x, 26 + (26 - y), 30) for (x, y) in pts3]
    split_by(F, pts, [P(54, 0, 30)[0]], [(SUBJ, G[7]), (LINE, G[5])])            # the source: brightest
    return F


if __name__ == '__main__':
    for name, fn in (('v1', v1_diagonal), ('v2', v2_full), ('v3', v3_funnel), ('v4', v4_section), ('v5', v5_iso)):
        d = HERE / name; d.mkdir(exist_ok=True)
        (d / 'rest.svg').write_text(fn().svg(), encoding='utf-8')
