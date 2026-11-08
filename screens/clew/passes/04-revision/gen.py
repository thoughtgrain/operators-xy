#!/usr/bin/env python3
"""Clew, revision pass 04: five versions of the owner's direction from pass 03 v3. The playing is a wave that
echoes in decaying repeats; a line angling down across the screen is the compressor, pressing the waves under it;
the compressor line carries the room as a tail that ripples, or ripples inside the line as it comes down.

  v1  stepped ceiling, one step per column; each tread ripples (column-affine, flat plan, the first echo brightest)
  v2  a ceiling on the diagonal with the mass above it cut in section; its end runs on as a rippling tail
      (off-axis diagonal, section cut, the source wave brightest)
  v3  the echoes as a receding isometric waterfall, the compressor a sloping plane whose far edge ripples
      (full field, three-quarter isometric, negative space)
  v4  a lid pivoting down over a centred wave, its tail drooping and rippling off the end
      (centred hero, low angle, the first peak brightest)
  v5  the descending line is itself the ripple, denser as it falls; the waves on a low horizon beneath
      (low horizon, front elevation, density gradient)

    python3 gen.py        # writes v1..v5/rest.svg
"""
import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('frames02', HERE.parent / '02-frames' / 'gen.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
Frame, G, HAIR, LINE, SUBJ = base.Frame, base.G, base.HAIR, base.LINE, base.SUBJ


def burst(x0, length, amp, cycles=5, n=150, decay=3.0):
    """a struck wave: (t, value) with a quick attack and a decaying envelope, value in -amp..amp"""
    out = []
    for k in range(n):
        t = k / (n - 1)
        env = math.exp(-t * decay) * (1 - math.exp(-t * 30))
        out.append((x0 + t * length, amp * env * math.sin(t * cycles * 2 * math.pi)))
    return out


def squeeze(v, limit):
    """soft-knee limit of a value's size to `limit`"""
    a = abs(v)
    if a <= limit * 0.6:
        return v
    over = a - limit * 0.6
    return math.copysign(limit * 0.6 + over / (1 + over / (limit * 0.4)), v)


def ripple_line(F, pts, amp, waves, col, w=HAIR, grow=True):
    """a line along `pts` with a sine ripple across it, its size growing (or shrinking) along the way"""
    out = []
    n = len(pts)
    for k, (x, y) in enumerate(pts):
        ax, ay = pts[max(0, k - 1)]; bx, by = pts[min(n - 1, k + 1)]
        dx, dy = bx - ax, by - ay; ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        a = amp * ((k / (n - 1)) if grow else (1 - k / (n - 1)))
        r = a * math.sin(k / (n - 1) * waves * 2 * math.pi)
        out.append((x + nx * r, y + ny * r))
    F.line(out, w, col)


def v1_steps():
    F = Frame()
    # one column per step: the playing, then three echoes; the ceiling steps down a column at a time
    treads = [(0, 98), (120, 106), (240, 113), (360, 119)]   # each tread presses its wave's peaks
    for c, (x, ty) in enumerate(treads):
        base_y = 130
        amp = [36, 28, 21, 15][c]
        pts = burst(x + 12, 100, amp)
        limit = base_y - ty - 2
        F.line([(px, base_y - squeeze(v, limit)) for px, v in pts], SUBJ if c == 1 else LINE, G[7] if c == 1 else G[5] if c == 0 else G[4])
        # the tread: a ceiling across the column whose far half ripples (the room on the line)
        flat = [(x + 6 + 50 * k / 12, ty) for k in range(13)]
        F.line(flat, LINE, G[5])
        rip = [(x + 56 + 52 * k / 60, ty) for k in range(61)]
        ripple_line(F, rip, 3 + c, 4 + c, G[4], HAIR)
        if c < 3:                                              # the riser down to the next tread
            F.line([(x + 108, ty), (x + 126, treads[c + 1][1])], LINE, G[5])
    F.line([(6, 186), (474, 186)], HAIR, G[2])
    return F


def v2_ceiling():
    F = Frame()
    # the ceiling: a straight line falling from upper left to lower right; the mass above it cut in section (hatched)
    x0, y0, x1, y1 = 10, 58, 330, 152
    def ceil_y(x): return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    for k in range(0, 60):
        x = x0 + k * 6
        if x > x1: break
        F.line([(x, ceil_y(x) - 3), (x + 9, ceil_y(x) - 18)], HAIR * 0.9, G[2])
    F.line([(x0, y0), (x1, y1)], LINE, G[5])
    # past its end the line runs on as the room's tail, rippling and fading
    pts = [(x1 + k * 1.57, y1 + 10 * (k / 90)) for k in range(91)]
    ripple_line(F, pts, 7, 6, G[4], HAIR, grow=False)
    # the waves under it, each pressed to the ceiling's height where it sits; the source (first) brightest
    base_y = 160
    for r, (x, amp) in enumerate([(20, 44), (98, 36), (176, 28), (254, 22)]):
        pts = burst(x, 74, amp, cycles=4)
        limit = base_y - ceil_y(x + 20) - 6
        F.line([(px, base_y - squeeze(v, limit)) for px, v in pts], SUBJ if r == 0 else LINE if r == 1 else HAIR, G[7] if r == 0 else G[5] if r == 1 else G[4])
    F.line([(6, 210), (474, 210)], HAIR, G[2])
    return F


def v3_waterfall():
    F = Frame()
    s = 1.0
    def P(x, d, v):                       # x along the wave, d back in depth, v up
        return (60 + x * 0.9 + d * 0.9, 168 - d * 0.55 - v)
    # each echo a trace further back, smaller; the compressor a sloping plane over them, rippling at its far edge
    for r in range(4, -1, -1):
        d = r * 34
        amp = 40 * 0.72 ** r
        limit = 30 - r * 4
        pts = burst(0, 200, amp, cycles=6)
        F.line([P(px, d, squeeze(v, limit)) for px, v in pts], SUBJ if r == 0 else HAIR, G[7] if r == 0 else [G[5], G[4], G[3], G[3]][r - 1])
    # the plane's near and side edges, sloping down as it goes back
    F.line([P(-10, -6, 36), P(210, -6, 36)], LINE, G[5])
    F.line([P(210, -6, 36), P(210, 150, 18)], HAIR, G[4])
    F.line([P(-10, -6, 36), P(-10, 150, 18)], HAIR, G[3])
    ripple_line(F, [P(-10 + 220 * k / 100, 150, 18) for k in range(101)], 5, 7, G[4], HAIR)
    return F


def v4_lid():
    F = Frame()
    cx, base_y = 240, 150
    # a lid pivoting down over the wave from a pivot at the left; its end droops into a rippling tail
    px, py = 96, 70
    ang = math.radians(16)
    ex, ey = px + 230 * math.cos(ang), py + 230 * math.sin(ang)
    F.line([(px, py), (ex, ey)], LINE, G[5])
    F.ring(px, py, 5, 5, HAIR, G[5], n=16)
    F.line([(px, py + 5), (px, 206)], HAIR, G[3])
    tail = [(ex + 70 * k / 80, ey + 40 * (k / 80) ** 1.6) for k in range(81)]
    ripple_line(F, tail, 6, 5, G[4], HAIR, grow=False)
    # the wave under it, pressed: the first peak, where the note lands, brightest
    def lid_y(x): return py + (x - px) * math.tan(ang)
    pts = burst(120, 210, 52, cycles=6)
    out = [(x, base_y - squeeze(v, base_y - lid_y(x) - 6)) for x, v in pts]
    F.line(out[:12], SUBJ, G[7])
    F.line(out[11:], LINE, G[5])
    # two echoes to the right, beyond the lid, smaller
    for r, (x, amp) in enumerate([(340, 26), (410, 16)]):
        F.line([(px2, base_y - v) for px2, v in burst(x, 60, amp)], HAIR, G[4] if r == 0 else G[3])
    F.line([(30, 206), (450, 206)], HAIR, G[2])
    return F


def v5_falling_ripple():
    F = Frame()
    hz = 192
    F.line([(6, hz), (474, hz)], HAIR, G[3])
    # the compressor line falls from top left to the horizon and is itself the ripple: tighter and denser as it falls
    pts = []
    n = 160
    for k in range(n):
        t = k / (n - 1)
        x, y = 16 + t * 440, 52 + t * 76
        phase = 40 * t ** 1.8                         # the waves crowd together as it falls: the density gradient
        r = 5 * math.sin(phase) * (0.3 + 0.7 * t)
        pts.append((x - r * 0.4, y + r))
    F.line(pts, LINE, G[6])
    # the playing and its echoes on the horizon, each pressed under the falling line
    def line_y(x): return 52 + (x - 16) / 440 * 76
    c = 150
    for r, (x, amp) in enumerate([(24, 40), (130, 32), (236, 24), (342, 18)]):
        ps = burst(x, 90, amp)
        F.line([(px, c - squeeze(v, max(4, c - line_y(px) - 14))) for px, v in ps], LINE if r < 2 else HAIR, [G[5], G[5], G[4], G[3]][r])
    return F


if __name__ == '__main__':
    for name, fn in (('v1', v1_steps), ('v2', v2_ceiling), ('v3', v3_waterfall), ('v4', v4_lid), ('v5', v5_falling_ripple)):
        d = HERE / name; d.mkdir(exist_ok=True)
        (d / 'rest.svg').write_text(fn().svg(), encoding='utf-8')
