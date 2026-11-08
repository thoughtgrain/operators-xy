#!/usr/bin/env python3
"""Clew, frames pass 02: five rest-frame variants of the chosen subject (v4: a cutaway schematic of one box: a gain
valve, a tape loop with a sliding playback head, a coil spring tank and the follower's lever). Each variant takes its
own direction from design_pass_start: composition, camera and where the brightest element sits.

    python3 gen.py        # writes v1..v5/rest.svg
"""
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
G = ['#000000', '#323232', '#4B4B4B', '#646464', '#7D7D7D', '#969696', '#AFAFAF', '#CDCDCD']
HAIR, LINE, SUBJ = 1.0, 1.5, 2.2


def f(v):
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


class Frame:
    def __init__(self):
        self.parts = []

    def path(self, pts, fill, stroke, sw):
        assert 3 <= len(pts) <= 64, len(pts)
        clean = [pts[0]]
        for p in pts[1:]:
            if math.hypot(p[0] - clean[-1][0], p[1] - clean[-1][1]) >= 0.2:
                clean.append(p)
        if math.hypot(clean[0][0] - clean[-1][0], clean[0][1] - clean[-1][1]) < 0.3:
            clean.pop()
        d = 'M ' + ' L '.join(f'{f(x)} {f(y)}' for x, y in clean) + ' Z'
        self.parts.append((d, fill, stroke, sw))

    # an open line as a closed ribbon w px wide
    def line(self, pts, w, col):
        if len(pts) > 31:                       # one ribbon holds 31 points a side at most: split, sharing an end
            for k in range(0, len(pts) - 1, 30):
                self.line(pts[k:k + 31], w, col)
            return
        left, right = [], []
        for k, (x, y) in enumerate(pts):
            ax, ay = pts[max(0, k - 1)]
            bx, by = pts[min(len(pts) - 1, k + 1)]
            dx, dy = bx - ax, by - ay
            n = math.hypot(dx, dy) or 1
            nx, ny = -dy / n * w / 2, dx / n * w / 2
            left.append((x + nx, y + ny)); right.append((x - nx, y - ny))
        self.path(left + right[::-1], col, col, 0.3)

    def poly(self, pts, fill, stroke, sw=HAIR):
        self.path(pts, fill, stroke, sw)

    def rect(self, x, y, w, h, fill, stroke, sw=HAIR):
        self.path([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, stroke, sw)

    def ellipse(self, cx, cy, rx, ry, fill, stroke, sw=HAIR, n=36, a0=0.0, a1=2 * math.pi):
        full = a1 - a0 >= 2 * math.pi - 1e-6
        pts = [(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + (0 if full else 1))]
        self.path(pts, fill, stroke, sw)

    def ring(self, cx, cy, rx, ry, w, col, n=28):
        gap = 0.8 / max(min(rx, ry), 1)
        out = [(cx + (rx + w / 2) * math.cos(a), cy + (ry + w / 2) * math.sin(a)) for a in [gap / 2 + (2 * math.pi - gap) * k / n for k in range(n + 1)]]
        inn = [(cx + (rx - w / 2) * math.cos(a), cy + (ry - w / 2) * math.sin(a)) for a in [gap / 2 + (2 * math.pi - gap) * k / n for k in range(n + 1)]]
        self.path(out + inn[::-1], col, col, 0.3)

    def arc(self, cx, cy, rx, ry, a0, a1, w, col, n=18):
        self.line([(cx + rx * math.cos(a0 + (a1 - a0) * k / n), cy + ry * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)], w, col)

    def text(self, x, y, s, col=G[4], size=10):
        self.parts.append(('TEXT', x, y, s, col, size))

    def svg(self, two_page=True):
        o = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
             '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>',
             '<g id="preview_header">']
        for i in range(8):
            o.append(f'<rect x="{60 * i}" y="0" width="60" height="20" fill="{G[i]}" stroke="none"/>')
        titles, values = ['squeeze', 'echo', 'space', 'blend'], ['35', '1/8', '35', '50']
        for k in range(4):
            c = '#CBCBCB' if k < 2 else '#000000'
            o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * k} 10)" fill="{c}" stroke="none" font-family="UniversNextPro-Light" font-size="10px">{titles[k]}</text>')
            o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * k} 17.44)" fill="{c}" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{values[k]}</text>')
        for k, (t, v) in enumerate(zip(['tone', 'motion', 'dry', 'attack'], ['0', '20', '100', '5.0'])):
            o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * k} 33)" fill="#5A5A5A" stroke="none" font-family="UniversNextPro-Light" font-size="10px">{t}</text>')
            o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * k} 33)" fill="#707070" stroke="none" font-family="UniversNextPro-Light" font-size="13px">{v}</text>')
        o.append('</g>')
        n = 0
        for p in self.parts:
            if p[0] == 'TEXT':
                _, x, y, s, col, size = p
                o.append(f'<text transform="matrix(1 0 0 1 {f(x)} {f(y)})" fill="{col}" stroke="none" font-family="UniversNextPro-Light" font-size="{size}px">{s}</text>')
            else:
                d, fill, stroke, sw = p
                o.append(f'<path id="clew_node_{n}" d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
                n += 1
        o.append('</svg>')
        return '\n'.join(o) + '\n'


# ---------- parts, drawn in elevation (2D) ----------

def reel(F, cx, cy, r, bright=False, spokes=3, rot=0.0):
    F.ellipse(cx, cy, r, r, '#000000', G[5], LINE, n=40)
    F.ring(cx, cy, r * 0.42, r * 0.42, HAIR, G[3], n=24)
    for k in range(spokes):
        a = rot + 2 * math.pi * k / spokes
        F.line([(cx + math.cos(a) * r * 0.2, cy + math.sin(a) * r * 0.2), (cx + math.cos(a) * r * 0.8, cy + math.sin(a) * r * 0.8)], HAIR, G[3])
    F.ellipse(cx, cy, r * 0.16, r * 0.16, '#000000', G[6] if bright else G[4], HAIR, n=16)


def head(F, x, y, w, h, col, sw=LINE, gap_up=True):
    """a tape head: a block with its gap facing the tape"""
    F.rect(x - w / 2, y, w, h, '#000000', col, sw)
    F.line([(x, y + 1), (x, y + h * 0.45)], HAIR, col)


def coil(F, x0, x1, y, h, turns, col, w=LINE):
    """a coil spring seen from the side: a helix, drawn as looped turns, split into ribbons of at most 30 points"""
    n = int(turns * 10)
    pitch = (x1 - x0) / turns
    loop = min(pitch * 0.45, h * 0.35)
    pts = []
    for k in range(n + 1):
        th = 2 * math.pi * k / 10
        pts.append((x0 + pitch * k / 10 - loop * math.sin(th) + loop * math.sin(0), y - h / 2 * math.cos(th)))
    for a in range(0, n, 29):
        F.line(pts[a:a + 30], w, col)


def valve(F, x, y, w, h, gap, col_body, col_jaw):
    """a gate across the path: housing, upper and lower jaw, the gap between them"""
    F.rect(x, y - h / 2, w, h, '#000000', col_body, LINE)
    jaw = (h - gap) / 2 - 3
    F.rect(x + w * 0.3, y - h / 2 + 2, w * 0.4, jaw, '#000000', col_jaw, LINE)
    F.rect(x + w * 0.3, y + h / 2 - 2 - jaw, w * 0.4, jaw, '#000000', col_jaw, LINE)


def lever(F, px, py, length, angle_deg, col, pad_col):
    a = math.radians(angle_deg)
    ex, ey = px + length * math.cos(a), py + length * math.sin(a)
    F.line([(px, py), (ex, ey)], SUBJ * 0.8, col)
    F.ring(px, py, 4, 4, HAIR, col, n=16)
    return ex, ey


def spring_tank(F, x, y, w, h, turns, col_box, col_coil, damper=None):
    F.rect(x, y - h / 2, w, h, '#000000', col_box, HAIR)
    F.rect(x + 3, y - 4, 6, 8, '#000000', col_box, HAIR)
    F.rect(x + w - 9, y - 4, 6, 8, '#000000', col_box, HAIR)
    coil(F, x + 9, x + w - 9, y, h * 0.55, turns, col_coil, HAIR)
    if damper is not None:
        F.rect(damper - 6, y - h / 2 + 1, 12, 5, G[2], G[4], HAIR)


# ---------- the five directions ----------

def v1_section():
    """full-bleed field; section cut; density gradient carries the subject"""
    F = Frame()
    top, bot = 46, 212
    # the housing cut through: hatched walls, dense at the input side thinning to the output
    F.rect(4, top, 472, bot - top, '#000000', G[3], LINE)
    x = 8
    while x < 472:
        step = 3 + 9 * (x - 8) / 464
        F.line([(x, top + 1.5), (x + 6, top + 7)], HAIR * 0.9, G[2])
        F.line([(x, bot - 7), (x + 6, bot - 1.5)], HAIR * 0.9, G[2])
        x += step
    F.line([(10, top + 9), (470, top + 9)], HAIR, G[3]); F.line([(10, bot - 9), (470, bot - 9)], HAIR, G[3])
    y = 128
    # the signal path
    F.line([(10, y), (40, y)], HAIR, G[4])
    valve(F, 40, y, 34, 44, 18, G[4], G[5])
    F.line([(74, y), (96, y)], HAIR, G[4])
    # tape loop with two reels; play head brightest (Echo)
    reel(F, 128, 100, 26); reel(F, 268, 100, 26)
    F.line([(102, 100), (102, y + 2), (294, y + 2), (294, 100)], LINE, G[4])
    head(F, 150, y + 3, 12, 14, G[5])
    head(F, 222, y + 3, 12, 14, G[7], SUBJ)       # the playback head: the brightest part
    F.ring(186, y + 8, 5, 5, HAIR, G[4], n=16)    # guide roller (Motion)
    # the spring tank under, damper pad (Tone)
    spring_tank(F, 96, 172, 200, 22, 22, G[3], G[5], damper=250)
    F.line([(300, y + 2), (318, y + 2)], HAIR, G[4])
    # the follower's lever over both outputs
    ex, ey = lever(F, 330, 76, 110, 18, G[5], G[4])
    F.line([(330, 80), (330, 172), (296, 172)], HAIR, G[3])
    coil(F, 330, 360, 66, 6, 5, G[3], HAIR)       # its spring (Attack)
    F.line([(430, ey + 4), (430, y), (470, y)], HAIR, G[4])
    # bypass (Dry) along the top
    F.line([(26, y), (26, 64), (452, 64), (452, y)], HAIR, G[3])
    F.text(14, y - 6, 'in', G[4]); F.text(450, y - 6, 'out', G[4])
    return F


def iso(p, ox=240, oy=150, s=1.0):
    x, y, z = p
    return (ox + (x - z) * 0.866 * s, oy + (x + z) * 0.5 * s - y * s)


def v2_iso():
    """centred hero; three-quarter isometric; brightest element on the most-played control's part (Echo's head)"""
    F = Frame()
    s = 0.82
    P = lambda x, y, z: iso((x, y, z), 256, 82, s)
    W, D = 200, 110
    # the deck: a slab, its two near faces
    top = [P(0, 0, 0), P(W, 0, 0), P(W, 0, D), P(0, 0, D)]
    F.poly([P(W, 0, 0), P(W, 0, D), P(W, -12, D), P(W, -12, 0)], '#000000', G[3], HAIR)
    F.poly([P(0, 0, D), P(W, 0, D), P(W, -12, D), P(0, -12, D)], '#000000', G[3], HAIR)
    F.poly(top, '#000000', G[4], LINE)
    # the cut-away back wall (section hatched edge)
    F.poly([P(0, 0, 0), P(W, 0, 0), P(W, 46, 0), P(0, 46, 0)], '#000000', G[2], HAIR)

    def flat_ellipse(cx, cz, r, y=0, n=32):
        return [P(cx + r * math.cos(2 * math.pi * k / n), y, cz + r * math.sin(2 * math.pi * k / n)) for k in range(n)]

    def reel3(cx, cz, r):
        F.poly(flat_ellipse(cx, cz, r, 4), '#000000', G[5], LINE)
        F.poly(flat_ellipse(cx, cz, r * 0.4, 4.5, 20), '#000000', G[3], HAIR)
        for k in range(3):
            a = 2 * math.pi * k / 3 + 0.4
            F.line([P(cx + math.cos(a) * r * 0.45, 4.6, cz + math.sin(a) * r * 0.45), P(cx + math.cos(a) * r * 0.85, 4.6, cz + math.sin(a) * r * 0.85)], HAIR, G[3])
    reel3(46, 40, 30); reel3(150, 40, 30)
    # tape along the front of the reels, over the heads
    F.line([P(16, 5, 40), P(16, 5, 82), P(180, 5, 82), P(180, 5, 40)], LINE, G[4])

    def block(x, z, w, d, h, col, sw=HAIR, top_col=None):
        F.poly([P(x + w, 0, z), P(x + w, 0, z + d), P(x + w, h, z + d), P(x + w, h, z)], '#000000', col, sw)
        F.poly([P(x, 0, z + d), P(x + w, 0, z + d), P(x + w, h, z + d), P(x, h, z + d)], '#000000', col, sw)
        F.poly([P(x, h, z), P(x + w, h, z), P(x + w, h, z + d), P(x, h, z + d)], '#000000', top_col or col, sw)
    block(62, 76, 10, 8, 14, G[5])                  # record head
    block(118, 76, 10, 8, 14, G[7], SUBJ)           # playback head: brightest
    F.poly(flat_ellipse(95, 88, 5, 6, 16), '#000000', G[4], HAIR)   # guide roller
    # the spring tank along the back
    block(20, 6, 160, 16, 16, G[3])
    pts = []
    for k in range(41):
        pts.append(P(28 + 144 * k / 40, 8 + (5 if k % 2 else -5) + 8, 14))
    F.line(pts, HAIR, G[5])
    # the valve on the input pipe, front left of the deck
    F.line([P(-40, 0, 100), P(0, 0, 100)], HAIR, G[4])
    block(2, 92, 18, 14, 22, G[4], LINE)
    # the follower's lever above, pivot at the right
    F.line([P(190, 52, 50), P(60, 30, 50)], SUBJ * 0.8, G[5])
    F.ring(*P(190, 52, 50), 4, 4, HAIR, G[5], n=16)
    F.line([P(190, 52, 50), P(190, 0, 50)], HAIR, G[3])
    F.text(*P(-60, 0, 108), 'in', G[4]); F.text(*P(214, 0, 30), 'out', G[4])
    F.line([P(200, 0, 30), P(212, 0, 30)], HAIR, G[4])
    return F


def v3_low():
    """low horizon; low angle; brightest element at the sound source (the input valve)"""
    F = Frame()
    hz = 196
    F.line([(6, hz), (474, hz)], HAIR, G[3])
    # ground marks receding to a vanishing point far right-up: low angle, objects tower over the horizon
    for k in range(7):
        x = 30 + k * 70
        F.line([(x, hz + 2), (x + 14, hz + 14)], HAIR, G[2])
    # input valve, large and close, brightest (where the sound enters)
    F.line([(6, 150), (40, 150)], HAIR, G[4])
    valve(F, 40, 150, 46, 74, 22, G[5], G[7])
    F.rect(52, hz - 12, 22, 12, '#000000', G[4], HAIR)          # its foot
    # the tape transport standing up: two tall reels on a plinth, seen from below (ellipses taller than wide)
    F.rect(120, hz - 16, 210, 16, '#000000', G[4], HAIR)
    for cx in (164, 286):
        F.ellipse(cx, 106, 40, 44, '#000000', G[5], LINE, n=44)
        F.ring(cx, 106, 17, 19, HAIR, G[3], n=24)
        for k in range(3):
            a = 2 * math.pi * k / 3 - 0.3
            F.line([(cx + math.cos(a) * 8, 106 + math.sin(a) * 9), (cx + math.cos(a) * 32, 106 + math.sin(a) * 35)], HAIR, G[3])
        F.line([(cx, 150), (cx, hz - 16)], LINE, G[3])
    F.line([(124, 106), (124, 158), (326, 158), (326, 106)], LINE, G[4])     # tape
    head(F, 200, 159, 12, 16, G[5]); head(F, 252, 159, 12, 16, G[5])
    F.ring(226, 165, 5, 5, HAIR, G[4], n=16)
    # the spring tank on the horizon, receding (shorter towards the right)
    F.poly([(346, hz), (474, hz), (474, hz - 22), (346, hz - 30)], '#000000', G[3], HAIR)
    pts = [(352 + 116 * k / 30, hz - 13 + (5 if k % 2 else -5) - 4 * (1 - k / 30)) for k in range(31)]
    F.line(pts, HAIR, G[5])
    # the lever arching over everything from a tall post
    F.line([(380, hz - 30), (380, 64)], LINE, G[3])
    F.line([(380, 64), (150, 52)], SUBJ * 0.8, G[5])
    F.ring(380, 64, 4, 4, HAIR, G[5], n=16)
    F.line([(86, 150), (120, 150)], HAIR, G[4])
    F.line([(330, 150), (474, 150)], HAIR, G[4])
    F.text(10, 144, 'in', G[4]); F.text(452, 144, 'out', G[4])
    return F


def v4_columns():
    """column-affine (P7): one part per encoder column; front elevation; negative space carries the subject"""
    F = Frame()
    y = 132
    F.line([(8, y), (472, y)], HAIR, G[2])          # the path, quiet, across all four columns
    # column 1 (Squeeze): the valve
    valve(F, 38, y, 44, 60, 20, G[4], G[6])
    # column 2 (Echo): the tape loop, reels above the path, heads on it; the playback head brightest
    reel(F, 152, 92, 20); reel(F, 208, 92, 20)
    F.line([(132, 92), (132, y - 2), (228, y - 2), (228, 92)], LINE, G[4])
    head(F, 160, y - 1, 10, 12, G[5]); head(F, 200, y - 1, 10, 12, G[7], SUBJ)
    F.ring(180, y + 18, 4, 4, HAIR, G[4], n=16)
    # column 3 (Space): the spring tank, standing vertically under the path
    F.rect(282, y + 6, 36, 72, '#000000', G[3], HAIR)
    pts = [(300 + (7 if k % 2 else -7), y + 12 + 60 * k / 24) for k in range(25)]
    F.line(pts, HAIR, G[5])
    F.rect(294, y - 30, 12, 26, '#000000', G[3], HAIR)
    # column 4 (Blend): the follower's lever, pivot near the output, pressing down on the path
    F.line([(450, 70), (370, 112)], SUBJ * 0.8, G[5])
    F.ring(450, 70, 4, 4, HAIR, G[5], n=16)
    F.line([(450, 74), (450, y)], HAIR, G[3])
    F.rect(364, 112, 14, 8, '#000000', G[4], HAIR)
    coil(F, 420, 444, 58, 6, 4, G[3], HAIR)
    F.text(10, y - 6, 'in', G[4]); F.text(452, y + 16, 'out', G[4])
    return F


def v5_plan():
    """off-axis diagonal; top-down plan; brightest element where the note lands (the input)"""
    F = Frame()
    # the path runs on a diagonal from top left to bottom right
    a = math.radians(11)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux

    def P(s, t):
        return (30 + s * ux + t * vx, 84 + s * uy + t * vy)
    F.line([P(0, 0), P(430, 0)], HAIR, G[3])
    # where the note lands: a bright input pad
    F.ellipse(*P(4, 0), 6, 6, '#000000', G[7], SUBJ, n=20)
    # valve seen from above: two jaws either side of the path
    F.poly([P(50, -18), P(80, -18), P(80, -5), P(50, -5)], '#000000', G[5], LINE)
    F.poly([P(50, 5), P(80, 5), P(80, 18), P(50, 18)], '#000000', G[5], LINE)
    # reels in plan: circles beside the path
    for s in (130, 230):
        c = P(s, 42)
        F.ellipse(c[0], c[1], 30, 30, '#000000', G[5], LINE, n=40)
        F.ring(c[0], c[1], 12, 12, HAIR, G[3], n=24)
    F.line([P(100, 42), P(100, 4), P(260, 4), P(260, 42)], LINE, G[4])
    F.poly([P(150, -2), P(160, -2), P(160, 10), P(150, 10)], '#000000', G[5], LINE)
    F.poly([P(200, -2), P(210, -2), P(210, 10), P(200, 10)], '#000000', G[6], LINE)
    # spring tank in plan, on the other side
    F.poly([P(110, -28), P(290, -28), P(290, -52), P(110, -52)], '#000000', G[3], HAIR)
    pts = [P(118 + 164 * k / 36, -40 + (6 if k % 2 else -6)) for k in range(37)]
    F.line(pts, HAIR, G[5])
    # lever across, pivot by the output
    F.line([P(340, -8), P(286, -46)], SUBJ * 0.8, G[5])
    F.ring(*P(340, -8), 4, 4, HAIR, G[5], n=16)
    F.text(*P(-2, 22), 'in', G[4]); F.text(*P(400, -10), 'out', G[4])
    return F


if __name__ == '__main__':
    for name, fn in (('v1', v1_section), ('v2', v2_iso), ('v3', v3_low), ('v4', v4_columns), ('v5', v5_plan)):
        d = HERE / name; d.mkdir(exist_ok=True)
        (d / 'rest.svg').write_text(fn().svg(), encoding='utf-8')
        print(name, 'written')
