#!/usr/bin/env python3
"""Clew, revision pass 03: five more designs, each a different subject from pass 02's cutaway schematic, each taking
its composition, camera and emphasis from design_pass_start.

  v1  isometric room floor (P10): a note lands as a block, echoes march back in rows, the room a low relief
  v2  echo plates (P4): glass plates receding from the playing, seen from a low angle, the room as hatching
  v3  scope staircase (P3): the playing's burst and its echoes stepping down a diagonal, the room a fine tail
  v4  atlas plan (P15): a full-bleed cell field seen from above, the source star, echo stars along an ecliptic
  v5  chamber section (P1): one vaulted room cut through, the playing a point inside, echo paths bouncing

    python3 gen.py        # writes v1..v5/rest.svg
"""
import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('frames02', HERE.parent / '02-frames' / 'gen.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
Frame, G, HAIR, LINE, SUBJ = base.Frame, base.G, base.HAIR, base.LINE, base.SUBJ


def v1_floor():
    """low horizon; three-quarter isometric; brightest element where the note lands"""
    F = Frame()
    s = 14.0

    def P(x, y, z):            # x right and down, z left and down (toward the viewer), y up; the floor sits low
        return (196 + (x - z) * 0.866 * s, 108 + (x + z) * 0.5 * s * 0.62 - y)
    NX, NZ = 16, 7
    for i in range(NX + 1):
        F.line([P(i, 0, 0), P(i, 0, NZ)], HAIR * 0.8, G[1])
    for k in range(NZ + 1):
        F.line([P(0, 0, k), P(NX, 0, k)], HAIR * 0.8, G[1])

    def block(i, k, h, top, edge, sw=HAIR):
        a, b, c, d = P(i, 0, k), P(i + 1, 0, k), P(i + 1, 0, k + 1), P(i, 0, k + 1)
        at, bt, ct, dt = P(i, h, k), P(i + 1, h, k), P(i + 1, h, k + 1), P(i, h, k + 1)
        F.poly([d, c, ct, dt], '#000000', edge, sw)
        F.poly([b, c, ct, bt], '#000000', edge, sw)
        F.poly([at, bt, ct, dt], top, edge, sw)
    import random
    rnd = random.Random(7)
    note = (1, 5)
    echoes = {}
    for r in range(4):                                  # each repeat a row of two, further back and lower
        for j in range(2):
            echoes[(4 + 3 * r, 4 - r + j)] = 30 - 7 * r
    cells = sorted([(i, k) for i in range(NX) for k in range(NZ)], key=lambda c: (c[0] + c[1], c[0]))
    for (i, k) in cells:                                 # back to front
        if (i, k) == note:
            block(i, k, 44, G[7], G[6], SUBJ)            # the note's block, where it lands: the brightest part
        elif (i, k) in echoes:
            block(i, k, echoes[(i, k)], G[3], G[5], LINE)
        elif i > 3 and rnd.random() < 0.28:
            block(i, k, 4 + rnd.random() * 5, '#000000', G[3])   # the room's low relief
    F.text(20, 206, 'in', G[4]); F.text(446, 150, 'out', G[4])
    return F


def v2_plates():
    """column-affine (P7); low angle; density gradient carries the subject"""
    F = Frame()
    hz = 200
    vx, vy = 520, 140                                     # the vanishing point, off to the right and low
    # the room behind: hatching that thins with distance (the density gradient)
    x = 250
    while x < 474:
        F.line([(x, 52), (x + 10, 70)], HAIR * 0.9, G[2])
        x += 4 + (x - 250) * 0.06
    F.line([(6, hz), (474, hz)], HAIR, G[2])
    # plates: the playing at the front (column 1), each repeat further back and smaller toward the vanishing point
    for r, px in enumerate([60, 150, 228, 296, 352]):
        t = (px - 20) / (vx - 20)
        top_y, bot_y = 56 + (vy - 56) * t * 0.6, hz - (hz - vy) * t * 0.4
        w = 16 * (1 - t * 0.7)
        col = G[6] if r == 0 else G[5] if r == 1 else G[4] if r < 4 else G[3]
        F.poly([(px - w / 2, top_y), (px + w / 2, top_y + 3), (px + w / 2, bot_y - 3), (px - w / 2, bot_y)], '#000000', col, LINE if r < 2 else HAIR)
        F.line([(px - w / 2, top_y + (bot_y - top_y) * 0.15), (px + w / 2, top_y + (bot_y - top_y) * 0.15 + 2)], HAIR, col)
    # the clamp on the front plate (Squeeze), in column 1
    F.rect(34, 106, 14, 54, '#000000', G[5], LINE); F.rect(72, 106, 14, 54, '#000000', G[5], LINE)
    F.line([(48, 133), (52, 133)], LINE, G[5]); F.line([(68, 133), (72, 133)], LINE, G[5])
    F.line([(30, 98), (90, 98)], SUBJ * 0.8, G[7])          # the clamp's bar: the brightest part
    F.text(10, 214, 'in', G[4]); F.text(440, 214, 'room', G[4])
    return F


def v3_staircase():
    """off-axis diagonal; front elevation; brightest element on the most-played control's part (the first echo)"""
    F = Frame()
    # a faint graticule
    for x in range(40, 470, 48):
        F.line([(x, 46), (x, 210)], HAIR * 0.7, G[1])
    # bursts stepping down and right: the playing, then each repeat a step lower and smaller
    steps = [(30, 80, 30), (130, 112, 22), (222, 140, 16), (306, 164, 11), (384, 184, 7)]
    for r, (x0, base_y, amp) in enumerate(steps):
        pts = []
        for k in range(60):
            t = k / 59
            env = math.exp(-t * 3.2) * (1 - math.exp(-t * 40))
            pts.append((x0 + t * 80, base_y - amp * env * math.sin(t * 46)))
        col = G[5] if r == 0 else G[7] if r == 1 else G[4]
        F.line(pts, SUBJ if r == 1 else LINE, col)
        F.line([(x0, base_y + 8), (x0 + 84, base_y + 8)], HAIR, G[2])
    # the room: a fine trace hanging below the staircase, smeared
    pts = [(30 + k * 7.4, 104 + k * 1.6 + 3 * math.sin(k * 1.7) * math.exp(-k / 40)) for k in range(60)]
    F.line(pts, HAIR, G[3])
    F.text(30, 62, 'in', G[4])
    return F


def v4_atlas():
    """full-bleed field; top-down plan; brightest element at the sound source"""
    F = Frame()
    cell, x0, y0, cols, rows = 22, 9, 44, 21, 8
    import random
    rnd = random.Random(3)
    src = (2, 4)
    ecl = [(2 + 4 * k, 4 - (k % 2)) for k in range(5)]
    for r in range(rows):
        for c in range(cols):
            d = min(math.hypot(c - ex, r - ey) for ex, ey in ecl)
            x, y = x0 + c * cell, y0 + r * cell
            if (c, r) == src:
                F.rect(x + 2, y + 2, cell - 4, cell - 4, G[7], G[7], HAIR)       # the source: brightest
            elif (c, r) in ecl:
                k = ecl.index((c, r)); g = [5, 4, 4, 3][min(3, k - 1)]
                inset = 3 + k * 1.2
                F.rect(x + inset, y + inset, cell - 2 * inset, cell - 2 * inset, G[g], G[g], HAIR)
            elif d < 2.6 and rnd.random() < 0.45:
                F.rect(x + 3, y + 3, cell - 6, cell - 6, G[2], G[2], HAIR)          # the room: lit cells round the echoes
            else:
                F.rect(x + 1, y + 1, cell - 2, cell - 2, '#000000', G[1], HAIR * 0.6)
    # the ecliptic, dotted
    for k in range(len(ecl) - 1):
        (a, b), (c, d) = ecl[k], ecl[k + 1]
        ax, ay = x0 + a * cell + cell / 2, y0 + b * cell + cell / 2
        bx, by = x0 + c * cell + cell / 2, y0 + d * cell + cell / 2
        for t in (0.35, 0.65):
            F.rect(ax + (bx - ax) * t - 1.6, ay + (by - ay) * t - 1.6, 3.4, 3.4, G[4], G[4], 0.3)
    return F


def v5_chamber():
    """centred hero; section cut; negative space carries the subject"""
    F = Frame()
    cx, floor_y, w, h, t = 240, 200, 250, 132, 12
    # the chamber's wall in section: an arch, hatched in its thickness
    outer = [(cx - w / 2 - t, floor_y)] + [(cx + (w / 2 + t) * math.cos(a), floor_y - 30 - (h - 30 + t) * math.sin(a)) for a in [math.pi - math.pi * k / 30 for k in range(31)]] + [(cx + w / 2 + t, floor_y)]
    inner = [(cx - w / 2, floor_y)] + [(cx + (w / 2) * math.cos(a), floor_y - 30 - (h - 30) * math.sin(a)) for a in [math.pi - math.pi * k / 30 for k in range(31)]] + [(cx + w / 2, floor_y)]
    F.poly(outer[:32], '#000000', G[4], LINE)
    F.poly(outer[31:] + [outer[31]], '#000000', G[4], LINE) if False else None
    F.line(inner, LINE, G[5])
    for k in range(0, 31, 2):
        a = math.pi - math.pi * k / 30
        p0 = (cx + (w / 2) * math.cos(a), floor_y - 30 - (h - 30) * math.sin(a))
        p1 = (cx + (w / 2 + t) * math.cos(a + 0.05), floor_y - 30 - (h - 30 + t) * math.sin(a + 0.05))
        F.line([p0, p1], HAIR, G[3])
    F.line([(cx - w / 2 - t - 20, floor_y), (cx + w / 2 + t + 20, floor_y)], LINE, G[4])
    # the playing: a point on the floor, left of centre
    sx, sy = cx - 60, floor_y - 6
    F.ellipse(sx, sy, 4, 4, G[7], G[7], HAIR, n=16)
    # echo paths: rays out to the vault and back, fading
    for r, (a, g) in enumerate([(1.25, 5), (2.0, 4), (0.75, 3)]):
        hx = cx + (w / 2) * math.cos(a); hy = floor_y - 30 - (h - 30) * math.sin(a)
        F.line([(sx + 5 * math.cos(a), sy - 5 * math.sin(a)), (hx, hy), (cx + 100 - r * 40, floor_y - 2)], HAIR, G[g])
    # a curtain on the right wall (Tone) and the door left open low on the left (Dry)
    F.rect(cx + w / 2 - 10, floor_y - 92, 6, 62, G[2], G[3], HAIR)
    F.text(cx - w / 2 - t - 18, floor_y - 6, 'in', G[4]); F.text(cx + w / 2 + t + 2, floor_y - 6, 'out', G[4])
    return F


if __name__ == '__main__':
    for name, fn in (('v1', v1_floor), ('v2', v2_plates), ('v3', v3_staircase), ('v4', v4_atlas), ('v5', v5_chamber)):
        d = HERE / name; d.mkdir(exist_ok=True)
        (d / 'rest.svg').write_text(fn().svg(), encoding='utf-8')
