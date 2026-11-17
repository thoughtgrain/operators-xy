#!/usr/bin/env python3
"""panel.svg.fragment and nodes.h for iris on the OP-XY: the rainbow screen.

The design is operator-design screens/iris (brief, frames, handoff); its frames come from gen_frames.py there, and
this file shares its geometry constants. If you change one, change both.

What's authored here:
  - nodes 0..3: the mix line's four mutable outlines (64 points each), drawn at the defaults. display() rewrites them.
  - nodes 4..11: the SDK's two-page header bar.
  - nodes 12..75: raw band cycles, 16 per band (sine, triangle, square, saw). Every cycle of a band is the same shape:
    one cycle of its wave bent to its rest radius, authored at the top of the bow (turn 0) about its own origin on the
    arc. display() moves, turns and scales each one into place.
  - nodes 76..139: the same chains with each cycle rounded to a hump (what gets through when Tone cuts that band).
  - the black ground mask under the horizon, then the horizon: static art, not nodes. They never move, and a
    bound mask would take its palette entry's paint (paint recolours a fill), turning it grey.

    python3 gen_panel.py          # writes panel.svg.fragment, nodes.h and the display block in definition.json
Copyright (c) 2026 briannhinton. MIT."""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = 'iris'

CX, CY = 240.0, 204.0                     # the bow's centre, on the horizon
RADII = [156.0, 140.0, 124.0, 108.0]      # sine, triangle, square, saw
CYCLES = [11, 13, 14, 16]                 # cycles across the half-turn: denser inward
AMP_BAND, AMP_MIX = 4.5, 5.0              # radial wave height, px
BAND_W, MIX_W, HAIR_W = 1.5, 2.5, 1.2     # line, subject, hairline
KINDS = ['sine', 'tri', 'square', 'saw']
START = {'sine': 0.0, 'tri': 0.0, 'square': 0.25, 'saw': 0.0}
PER_BAND = 16
DEFAULTS = {'morph': 0.3333, 'overlap': 0.25, 'spread': 0.0, 'tone': 0.7, 'skew': 0.0, 'phase': 0.0}

N_MIX, N_HDR = 0, 4
N_RAW = N_HDR + 8
N_ROUND = N_RAW + 4 * PER_BAND
NODES = N_ROUND + 4 * PER_BAND

G = ['#000000', '#323232', '#4B4B4B', '#646464', '#7D7D7D', '#969696', '#AFAFAF', '#CDCDCD']
# (fill, stroke, width): ribbons stroke in their own fill, a hair wide, so a 1.5 px line stays about 1.5 px
PALETTE = [(G[6], G[6], 0.2), (G[7], G[7], 0.2), (G[3], G[3], 0.2), (G[4], G[4], 0.2), (G[5], G[5], 0.2)]
PALETTE_NAMES = ['P_MIX', 'P_MIX_HELD', 'P_BAND_LO', 'P_BAND_MID', 'P_BAND_HI']


def polar(r, phi):
    return CX + r * math.cos(phi), CY - r * math.sin(phi)


def ribbon(line, hw):
    n = len(line)
    left, right = [], []
    for k in range(n):
        if k in (0, n - 1):
            a, b = (line[0], line[1]) if k == 0 else (line[-2], line[-1])
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            nx, ny, m = -dy / L, dx / L, 1.0
        else:
            ax, ay = line[k][0] - line[k - 1][0], line[k][1] - line[k - 1][1]
            bx, by = line[k + 1][0] - line[k][0], line[k + 1][1] - line[k][1]
            La, Lb = math.hypot(ax, ay), math.hypot(bx, by)
            n1, n2 = (-ay / La, ax / La), (-by / Lb, bx / Lb)
            sx, sy = n1[0] + n2[0], n1[1] + n2[1]
            Ls = math.hypot(sx, sy) or 1e-9
            nx, ny = sx / Ls, sy / Ls
            m = min(1.0 / max(nx * n1[0] + ny * n1[1], 1e-6), 2.0)
        left.append((line[k][0] + nx * hw * m, line[k][1] + ny * hw * m))
        right.append((line[k][0] - nx * hw * m, line[k][1] - ny * hw * m))
    return left + right[::-1]


def dedupe(line, gap=0.3):
    out = [line[0]]
    for q in line[1:]:
        if math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) >= gap:
            out.append(q)
    return out


def cycle_line(kind, r, phi0, dphi, t0):
    """One cycle's centreline, as gen_frames.py draws it (skew 0: the bands are drawn raw)."""
    e = 0.01
    if kind == 'sine':
        pts = [(k / 24, math.sin(2 * math.pi * (t0 + k / 24))) for k in range(25)]
    else:
        keys = {'tri': [(0, 0), (0.25, 1), (0.75, -1), (1, 0)],
                'square': [(0, 1), (0.25 - e, 1), (0.25 + e, -1), (0.75 - e, -1), (0.75 + e, 1), (1, 1)],
                'saw': [(0, 0), (0.5 - e, 1), (0.5 + e, -1), (1, 0)]}[kind]
        pts, seg_len = [], abs(dphi) * r
        for (u0, v0), (u1, v1) in zip(keys, keys[1:]):
            m = max(1, int(math.ceil(math.hypot((u1 - u0) * seg_len, (v1 - v0) * AMP_BAND) / 3.0)))
            pts += [(u0 + (u1 - u0) * s / m, v0 + (v1 - v0) * s / m) for s in range(m)]
        pts.append(keys[-1])
    return dedupe([polar(r + AMP_BAND * v, phi0 + dphi * u) for u, v in pts])


def f(v):
    s = f'{v:.3f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '', '-') else s


def d_of(poly, ox, oy):
    return 'M ' + ' L '.join(f'{f(x - ox)} {f(y - oy)}' for x, y in poly) + ' Z'


def mix_rest():
    """The defaults' mix line (triangle with a little sine and square), as four 64-point outlines."""
    v = DEFAULTS
    c, width = v['morph'] * 3, 1 + 3 * v['overlap']
    w = [max(0.0, 1 - abs(i - c) / width) for i in range(4)]
    w = [x / sum(w) for x in w]
    fc = 2 ** (0.5 + 3 * v['tone'])
    gain = lambda n: 1 / math.sqrt(1 + (n / fc) ** 4)

    def series(kind, x):
        if kind == 'sine':
            return gain(1) * math.sin(x)
        s = 0.0
        for n in range(1, 13):
            if kind == 'tri' and n % 2:
                s += gain(n) * (-1) ** ((n - 1) // 2) * math.sin(n * x) / n ** 2 * 8 / math.pi ** 2
            elif kind == 'square' and n % 2:
                s += gain(n) * math.sin(n * x) / n * 4 / math.pi
            elif kind == 'saw':
                s += gain(n) * (-1) ** (n + 1) * math.sin(n * x) / n * 2 / math.pi
        return s
    i0 = min(int(c), 2)
    r_mix = RADII[i0] + (RADII[i0 + 1] - RADII[i0]) * (c - i0)
    n_mix = CYCLES[i0] + (CYCLES[i0 + 1] - CYCLES[i0]) * (c - i0)
    out = []
    for q in range(4):
        line = []
        for k in range(32):
            u = (q + k / 31) / 4
            val = sum(w[i] * series(kd, 2 * math.pi * (n_mix * u)) for i, kd in enumerate(KINDS) if w[i] > 0)
            line.append(polar(r_mix + AMP_MIX * val, math.pi * (1 - u)))
        out.append((ribbon(line, MIX_W / 2), polar(r_mix, math.pi * (1 - (q + 0.5) / 4))))
    return out


def header_fragment():
    o = ['<!-- SDK two-page header: keep this block before machine artwork below y=38. -->',
         '<path d="M0,0 L480,0 L480,38 L0,38 Z" fill="#000000" stroke="none"/>']
    for i in range(8):
        o.append(f'<path id="{PREFIX}_node_{N_HDR + i}" transform="matrix(1 0 0 1 {60 * i} 0)" d="M0,0 L60,0 L60,20 L0,20 Z" fill="{G[i]}" stroke="{G[i]}" stroke-width="0.5"/>')
    rows = [(5, 10, '10px', None), (65, 17.4, '20px', None), (5, 33, '10px', '#5A5A5A'), (65, 33, '13px', '#707070')]
    for r, (x0, y, size, ink) in enumerate(rows):
        for k in range(4):
            col = ink or ('#CBCBCB' if k < 2 else '#000000')
            o.append(f'<text id="{PREFIX}_text_{4 * r + k}" transform="matrix(1 0 0 1 {x0 + 120 * k} {y})" fill="{col}" font-family="UniversNextPro-Light" font-size="{size}">-</text>')
    return o


def main():
    o = [f'<g id="{PREFIX}_panel">'] + header_fragment()
    # band chains: one cycle, authored at the top of the bow (turn 0), centred on its own origin on the arc
    for first, rounded in ((N_RAW, False), (N_ROUND, True)):
        for b, kind in enumerate(KINDS):
            r, dphi = RADII[b], -math.pi / CYCLES[b]
            line = cycle_line('sine' if rounded else kind, r, math.pi / 2 - dphi / 2, dphi, START[kind])
            ox, oy = polar(r, math.pi / 2)
            d = d_of(ribbon(line, BAND_W / 2), ox, oy)
            grey = PALETTE[3 if b == 1 else 2][0]
            for k in range(PER_BAND):
                o.append(f'<path id="{PREFIX}_node_{first + PER_BAND * b + k}" transform="matrix(1 0 0 1 {f(ox)} {f(oy)})" d="{d}" fill="{grey}" stroke="{grey}" stroke-width="0.2"/>')
    hy = CY + 0.6
    mask = [(-200, HAIR_W / 2), (200, HAIR_W / 2), (200, 220 - hy), (-200, 220 - hy)]
    hz = [(-200, -HAIR_W / 2), (200, -HAIR_W / 2), (200, HAIR_W / 2), (-200, HAIR_W / 2)]
    o.append(f'<path transform="matrix(1 0 0 1 {f(CX)} {f(hy)})" d="{d_of(mask, 0, 0)}" fill="#000000" stroke="none"/>')
    o.append(f'<path transform="matrix(1 0 0 1 {f(CX)} {f(hy)})" d="{d_of(hz, 0, 0)}" fill="{G[2]}" stroke="none"/>')
    # the mix line last, so it's drawn over the bands
    for q, (poly, (ox, oy)) in enumerate(mix_rest()):
        o.append(f'<path id="{PREFIX}_node_{N_MIX + q}" transform="matrix(1 0 0 1 {f(ox)} {f(oy)})" d="{d_of(poly, ox, oy)}" fill="{G[6]}" stroke="{G[6]}" stroke-width="0.2"/>')
    for i, (fill, stroke, width) in enumerate(PALETTE):
        o.append(f'<path id="{PREFIX}_palette_{i}" transform="matrix(1 0 0 1 640 320)" d="M0,0 L4,0 L4,4 L0,4 Z" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
    o.append('</g>')
    (HERE / 'panel.svg.fragment').write_text('\n'.join(o) + '\n', encoding='utf-8')

    q10 = lambda v: int(round(v * 1024))
    h = ('#pragma once\n// iris for the OP-XY: node indices and the bow\'s geometry, written by gen_panel.py.\n'
         '// Edit the generator, not this file.\nnamespace iris {\n')
    h += (f'enum {{ N_MIX = {N_MIX}, N_HDR = {N_HDR}, N_RAW = {N_RAW}, N_ROUND = {N_ROUND}, PER_BAND = {PER_BAND}, '
          f'N_TOTAL = {NODES} }};\n')
    h += 'enum { ' + ', '.join(f'{n} = {k}' for k, n in enumerate(PALETTE_NAMES)) + f', PALETTE_N = {len(PALETTE)} }};\n'
    h += '// Q10 px: the bow\'s centre, each band\'s rest radius, the wave heights and the mix ribbon\'s half width\n'
    h += f'const int CX_Q10 = {q10(CX)}, CY_Q10 = {q10(CY)};\n'
    h += 'const int RADIUS_Q10[4] = { ' + ', '.join(str(q10(r)) for r in RADII) + ' };\n'
    h += 'const int CYCLES_N[4] = { ' + ', '.join(str(c) for c in CYCLES) + ' };\n'
    h += f'const int AMP_MIX_Q10 = {q10(AMP_MIX)}, MIX_HALF_W_Q10 = {q10(MIX_W / 2)};\n'
    h += '}\n'
    (HERE / 'nodes.h').write_text(h, encoding='utf-8')

    definition = json.loads((HERE / 'definition.json').read_text(encoding='utf-8'))
    definition['resources']['display'].update({'paths': 4, 'points': 64, 'nodes': NODES, 'texts': 16, 'palette': len(PALETTE)})
    (HERE / 'definition.json').write_text(json.dumps(definition, indent=2) + '\n', encoding='utf-8')
    print(f'{NODES} nodes, {len(PALETTE)} palette entries')


if __name__ == '__main__':
    main()
