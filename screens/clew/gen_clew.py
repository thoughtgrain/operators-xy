#!/usr/bin/env python3
"""Clew's screen (pass 05 v2): the send's audio as one wave, scrolling from right to left, under a compressor line
that steps down onto it, one step per encoder column, with the room rippling on each step's tail.

The design is authored the way the device will draw it, so the frames here become panel.svg.fragment with no
redrawing:

  paths 0..3   the wave, one mutable outline per column (32 samples along it, 32 back 1 px below: a closed ribbon)
  nodes 4..11  the SDK's two-page header bar
  treads       4 steps x 10 cells; each cell is a flat segment or a ripple arch of one of three heights (4 nodes, one
               shown), authored at the cell's left end on the step line, so a cell only ever translates
  risers       3 risers x 10 segments of 4 px, stacked from one step down to the next; spare segments hidden

Every frame comes from pose(controls, scope): the controls, and the send's input and output peaks over the last
1.9 s. Effect pages don't receive those peaks yet (it needs an SDK change, handoff.md), so sim/scope.cpp stands in
for them by running toro's and Clew's engine code on a computer.

    python3 gen_clew.py frames     # writes frames/*.svg (rest, playing, c1..c8 at 0/50/100 while playing, order-fx)
    python3 gen_clew.py budget     # changed nodes per frame at rest and while the phrase plays
"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = 'clew'
G = ['#000000', '#323232', '#4B4B4B', '#646464', '#7D7D7D', '#969696', '#AFAFAF', '#CDCDCD']

# layout
C_Y = 150                                   # the wave's centre line
COL_X = [6 + 117 * k for k in range(5)]     # column edges: 6 .. 474
SAMPLES = 32                                # wave samples per column (64 points with the way back)
CELLS = 10
CELL_W = 117 / CELLS
BUMPS = [0, 2.5, 4.5, 7.0]                  # ripple arch heights: flat, low, mid, high
RISER_SEG, RISER_N = 4.0, 10

# palette: (name, fill, stroke, width). Paths draw hollow, so their fill is none.
PALETTE = [('P_WAVE', 'none', G[5], 1.5), ('P_WAVE_NOW', 'none', G[7], 2.0),
           ('P_TREAD', G[5], G[5], 0.3), ('P_RIPPLE', G[4], G[4], 0.3)]
P = {n: k for k, (n, *_r) in enumerate(PALETTE)}

N_PATH = 0
N_HDR = 4
N_CELL = N_HDR + 8                          # tread t, cell j, variant v: N_CELL + (t * CELLS + j) * 4 + v
N_RISER = N_CELL + 4 * CELLS * 4            # riser r, segment s: N_RISER + r * RISER_N + s
NODES = N_RISER + 3 * RISER_N

DEFAULTS = [0.35, 0.6, 0.35, 0.5, 0.5, 0.2, 1.0, 0.5624, 0.0]
NAMES = ['squeeze', 'echo', 'space', 'blend', 'tone', 'motion', 'dry', 'attack']
DIVS = [1, 1.5, 2, 3, 4, 6, 8, 16]


def soft(v, limit):
    """the compressor's knee on the drawing: a value's size bends towards `limit`"""
    a = abs(v)
    if a <= limit * 0.6:
        return v
    over = a - limit * 0.6
    return math.copysign(limit * 0.6 + over / (1 + over / (limit * 0.4)), v)


WINDOW = 22 * 64                            # one level window: 1408 samples, 31.9 ms
WINDOWS = 60                                # on screen: 15 per column, about 1.9 s
PX_FS = 60                                  # the wave's height for a full-scale peak
CYCLE = 4                                   # the drawn wave's cycle, in windows (31 px)
SR = 44100


def pose(c, scope=None, head=0, tick=0):
    """everything the screen draws for controls c (eight controls and Order, each 0..1) and the send's levels

    scope: (inp, out), the last WINDOWS peaks of the send's input and of Clew's output, oldest first, 0..1 of full
    scale; None is silence. head: the newest window's running count, so the wave's cycles travel with the audio.
    tick: the frame count, which walks the ripple along the tails while the room sounds.
    """
    sq, echo, space, blend, tone, motion, dry, attack, order = c
    tone = 2 * tone - 1
    inp, out = scope if scope else ([0.0] * WINDOWS, [0.0] * WINDOWS)
    fx_first = order > 0.5                                          # FX first: the compressor presses the tails too

    # the compressor line: one step per column, at Squeeze's ceiling, pushed down by the gain reduction that
    # column's input caused (the engine's threshold and ratio) until it rests on the wave; Motion staggers the steps
    thr_db, ratio = -3 - 30 * sq, 1 + 7 * sq
    base = 64 - 40 * sq
    stagger = motion * 7
    tread_y, limits = [], []
    for k in range(4):
        pk = max(inp[15 * k:15 * k + 15])
        over = max(0.0, 20 * math.log10(pk + 1e-6) - thr_db)
        gr = over * (1 - 1 / ratio)                                 # dB of gain reduction
        top = PX_FS * max(out[15 * k:15 * k + 15]) + 3              # it comes down onto the wave, never through it
        lim = max(5.0, top, base * 0.9 ** k - 1.2 * gr)
        lim = 4 * round(lim / 4)                                    # 4 px steps: fewer redraws as the audio scrolls
        limits.append(lim)
        y = C_Y - lim + (stagger if k % 2 else -stagger * (k > 0))
        tread_y.append(float(round(y)))

    # the tails: ripple on the last `reach` cells of each step while the room sounds there (Space times Clew's
    # output over that column's last windows); it walks along the tail as time passes. Blend leans the tail down
    # by how hard that column's input played (the ducking). Tone: darker is shorter and broader, brighter sharper.
    reach = int(round(CELLS * (0.2 + 0.6 * space) * (1 - 0.5 * max(0.0, -tone)))) if space > 0.02 else 0
    every = 2 if tone < -0.33 else 1
    lift = 1 if tone > 0.33 else 0
    cells = []                                                      # (tread, cell, variant, x, y)
    for k in range(4):
        room = space * sum(out[15 * k + 10:15 * k + 15]) / 5
        amp = 3 * min(1.0, room * 6)
        if fx_first:
            amp = min(amp, 1)
        duck = min(1.0, 3 * max(inp[15 * k + 11:15 * k + 15]))
        walk = (tick + 3 * k // 2) // 6                             # one cell every six frames, the steps out of step
        first = CELLS - reach
        for j in range(CELLS):
            x = COL_X[k] + j * CELL_W
            y = tread_y[k]
            v = 0
            if j >= first and reach:
                u = (j - first + 1) / reach                         # 0..1 along the tail
                y += 0 if fx_first else blend * 28 * u * duck
                y = min(y, C_Y - 8 - 6 * u)                         # it stays above the wave's line
                if amp >= 0.5 and (j - first + walk) % (2 * every) == 0:
                    v = max(1, min(3, int(round(amp * (0.5 + 0.5 * u))) + lift))
            if j * CELL_W + CELL_W / 2 < 3 + attack * 40:
                v = -1                                              # Attack: each step starts late, a peak gets out
            cells.append((k, j, v, round(x * 2) / 2, float(round(y))))

    risers = []
    for k in range(3):
        y0 = cells[k * CELLS + CELLS - 1][4]
        y1 = tread_y[k + 1]
        top, bot = min(y0, y1), max(y0, y1)
        gap = bot - top
        n = 0 if gap < 3 else min(RISER_N, int(math.ceil(gap / RISER_SEG)))   # under 3 px the steps meet: no riser
        risers.append([(COL_X[k + 1], max(top, min(top + s * RISER_SEG, bot - RISER_SEG))) for s in range(n)])

    # the wave: Clew's output, oldest at the left, newest at the right. Its envelope is the output's peaks; its
    # cycles are the drawing's (CYCLE windows each), fixed to the audio so they scroll with it. The output is
    # compressed already, so the step only touches its peaks, and not where Attack starts it late.
    att_px = 3 + attack * 40
    waves = []
    for k in range(4):
        pts = []
        for s in range(SAMPLES):
            x = COL_X[k] + 117 * s / (SAMPLES - 1)
            w = 15 * k + 15 * s / (SAMPLES - 1) - 0.5               # window position, its centre at .5
            i = max(0, min(WINDOWS - 2, int(math.floor(w))))
            t = max(0.0, min(1.0, w - i))
            env = PX_FS * (out[i] * (1 - t) + out[i + 1] * t)
            v = env * math.sin(2 * math.pi * (head - (WINDOWS - 1) + w) / CYCLE)
            d = x - COL_X[k]
            if d >= att_px:
                v = soft(v, max(2.0, limits[k] - 1))                # the output is compressed already: a light touch
            pts.append((x, C_Y - v))
        waves.append(pts)
    return {'tread_y': tread_y, 'cells': cells, 'risers': risers, 'waves': waves}


# ---------- the drawing ----------

def f(v):
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def ribbon(pts, w):
    left, right = [], []
    for k, (x, y) in enumerate(pts):
        ax, ay = pts[max(0, k - 1)]; bx, by = pts[min(len(pts) - 1, k + 1)]
        dx, dy = bx - ax, by - ay; n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n * w / 2, dx / n * w / 2
        left.append((x + nx, y + ny)); right.append((x - nx, y - ny))
    return left + right[::-1]


def cell_shape(v, up):
    """a cell's outline, relative to its left end on the tread: flat, or an arch of height BUMPS[v]"""
    if v == 0:
        return ribbon([(0, 0), (CELL_W, 0)], 1.5)
    h = BUMPS[v] * (-1 if up else 1)
    pts = [(CELL_W * t / 10, h * math.sin(math.pi * t / 10)) for t in range(11)]
    return ribbon(pts, 1.0)


def path_d(pts):
    return 'M ' + ' L '.join(f'{f(x)} {f(y)}' for x, y in pts) + ' Z'


def header_values(c):
    sq, echo, space, blend, tone, motion, dry, attack, order = c
    names = {1: '1/32', 1.5: '3/64', 2: '1/16', 3: '3/32', 4: '1/8', 6: '3/16', 8: '1/4', 16: '1/2'}
    return [f'{round(sq * 100)}', names[DIVS[min(7, int(echo * 8))]] if echo > 0.004 else 'off', f'{round(space * 100)}',
            f'{round(blend * 100)}', (f'{round((2 * tone - 1) * 100):+d}' if abs(2 * tone - 1) > 0.005 else '0'),
            f'{round(motion * 100)}', f'{round(dry * 100)}', f'{0.5 * 60 ** attack:.1f}']


def frame_svg(c, page=0, shift=False, scope=None, head=0, tick=0):
    p = pose(c, scope, head, tick)
    vals = header_values(c)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="220" viewBox="0 0 480 220">',
         '<g id="preview_canvas"><rect x="0" y="0" width="480" height="220" fill="#000000" stroke="none"/></g>',
         '<g id="preview_header">']
    for i in range(8):
        o.append(f'<path id="{PREFIX}_node_{N_HDR + i}" transform="matrix(1 0 0 1 {60 * i} 0)" d="M 0 0 L 60 0 L 60 20 L 0 20 Z" fill="{G[i]}" stroke="{G[i]}" stroke-width="0.5"/>')
    top = range(4, 8) if page else range(4)
    low = range(4) if page else range(4, 8)
    for k, i in enumerate(top):
        col = '#CBCBCB' if k < 2 else '#000000'
        name, val = NAMES[i], vals[i]
        if shift:                                                   # Shift held: the edited row shows the Shift row
            name, val = ('order', 'fx' if c[8] > 0.5 else 'comp') if k == 0 else ('', '')
        if name:
            o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * k} 10)" fill="{col}" stroke="none" font-family="UniversNextPro-Light" font-size="10px">{name}</text>')
            o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * k} 17.44)" fill="{col}" stroke="none" font-family="UniversNextPro-Light" font-size="20px">{val}</text>')
    for k, i in enumerate(low):
        o.append(f'<text transform="matrix(1 0 0 1 {5 + 120 * k} 33)" fill="#5A5A5A" stroke="none" font-family="UniversNextPro-Light" font-size="10px">{NAMES[i]}</text>')
        o.append(f'<text transform="matrix(1 0 0 1 {65 + 120 * k} 33)" fill="#707070" stroke="none" font-family="UniversNextPro-Light" font-size="13px">{vals[i]}</text>')
    o.append('</g>')
    o.append(f'<path d="M 6 205.5 L 474 205.5 L 474 206.5 L 6 206.5 Z" fill="{G[2]}" stroke="{G[2]}" stroke-width="0.3"/>')   # the floor, static
    # treads: every variant of every cell is a node; the one shown sits on the tread, the rest park off screen
    for (k, j, v, x, y) in p['cells']:
        up = j % 2 == 0                                              # the node's own shape never changes
        for var in range(4):
            n = N_CELL + (k * CELLS + j) * 4 + var
            shown = var == v
            pal = 'P_TREAD' if var == 0 else 'P_RIPPLE'
            _, fill, stroke, w = PALETTE[P[pal]]
            if not shown:
                m = 'matrix(1 0 0 1 640 320)'
            else:
                m = f'matrix(1 0 0 1 {f(x)} {f(y)})'
            o.append(f'<path id="{PREFIX}_node_{n}" transform="{m}" d="{path_d(cell_shape(var, up))}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"/>')
    for r in range(3):
        segs = p['risers'][r]
        for s in range(RISER_N):
            n = N_RISER + r * RISER_N + s
            x, y = segs[s] if s < len(segs) else (640, 320)
            o.append(f'<path id="{PREFIX}_node_{n}" transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="M -0.75 0 L 0.75 0 L 0.75 {f(RISER_SEG)} L -0.75 {f(RISER_SEG)} Z" fill="{G[5]}" stroke="{G[5]}" stroke-width="0.3"/>')
    # the wave: four mutable outlines, each its column's samples and back 1 px below
    for k, pts in enumerate(p['waves']):
        outline = pts + [(x, y + 1.0) for x, y in reversed(pts)]
        pal = 'P_WAVE_NOW' if k == 3 else 'P_WAVE'
        _, fill, stroke, w = PALETTE[P[pal]]
        ox = (COL_X[k] + COL_X[k + 1]) / 2                          # each outline's points stay within 64 px of its origin
        rel = [(x - ox, y - C_Y) for x, y in outline]
        o.append(f'<path id="{PREFIX}_node_{N_PATH + k}" transform="matrix(1 0 0 1 {f(ox)} {C_Y})" d="{path_d(rel)}" fill="none" stroke="{stroke}" stroke-width="{w}"/>')
    for i, (name, fill, stroke, w) in enumerate(PALETTE):
        o.append(f'<path id="{PREFIX}_palette_{i}" transform="matrix(1 0 0 1 640 320)" d="M 0 0 L 4 0 L 4 4 L 0 4 Z" fill="{G[0] if fill == "none" else fill}" stroke="{stroke}" stroke-width="{w}"/>')
    o.append('</svg>')
    return '\n'.join(o) + '\n'




# ---------- the levels: Clew's own engine on a computer, standing in for what the SDK doesn't send yet ----------

SIM = HERE / 'sim'
SIM_BIN = SIM / '.build' / 'scope'
SNAP_AT = 5.75                                  # seconds: the frames show the bar that ends here, its tails ringing


def build_sim():
    src = [SIM / 'scope.cpp', HERE.parents[1] / 'machines' / 'clew' / 'fx.cpp', HERE.parents[1] / 'machines' / 'toro' / 'engine.cpp']
    if SIM_BIN.exists() and all(SIM_BIN.stat().st_mtime > f.stat().st_mtime for f in src):
        return
    import subprocess
    sdk = Path(__import__('os').environ.get('OPXY_SDK', HERE.parents[2] / 'open-xy'))
    if not (sdk / 'sdk' / 'include').exists():
        sdk = HERE.parents[3] / 'etcetc000' / 'open-xy'
    SIM_BIN.parent.mkdir(exist_ok=True)
    machines = HERE.parents[1] / 'machines'
    subprocess.run(['g++', '-O2', '-std=c++17', f'-I{machines / "toro"}', f'-I{machines / "clew"}',
                    f'-I{sdk / "sdk" / "include"}', str(SIM / 'scope.cpp'), '-o', str(SIM_BIN)], check=True)


def read_peaks(path):
    rows = [line.split() for line in Path(path).read_text().splitlines() if line.strip()]
    return [float(a) for a, _ in rows], [float(b) for _, b in rows]


_runs = {}
def levels(c, at=SNAP_AT):
    """the send's last WINDOWS input and output peaks at `at` seconds, with controls c held from the start"""
    key = tuple(round(v, 4) for v in c)
    if key not in _runs:
        import subprocess, tempfile
        build_sim()
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as t:
            name = t.name
        subprocess.run([str(SIM_BIN), 'const', *[f'{v:.6f}' for v in c], f'{at + 0.1:.2f}', name], check=True)
        _runs[key] = read_peaks(name)
        Path(name).unlink()
    inp, out = _runs[key]
    head = int(at * SR / WINDOW)
    return (inp[head - WINDOWS + 1:head + 1], out[head - WINDOWS + 1:head + 1]), head


def write_frames():
    out = HERE / 'frames'
    out.mkdir(exist_ok=True)
    for old in out.glob('*.svg'):
        old.unlink()
    def playing(c, **kw):
        scope, head = levels(c)
        return frame_svg(c, scope=scope, head=head, tick=0, **kw)
    (out / 'rest.svg').write_text(frame_svg(DEFAULTS))                # silence: nothing has come in
    (out / 'playing.svg').write_text(playing(DEFAULTS))
    for n in range(8):                                                  # every control's frames while it plays
        for v in (0.0, 0.5, 1.0):
            c = list(DEFAULTS); c[n] = v
            (out / f'c{n + 1}-{int(v * 100):03d}.svg').write_text(playing(c, page=1 if n >= 4 else 0))
    c = list(DEFAULTS); c[8] = 1.0
    (out / 'order-fx.svg').write_text(playing(c))
    (out / 'shift-order-fx.svg').write_text(playing(c, shift=True))
    print(f'{NODES} nodes ({len(list(out.glob("*.svg")))} frames)')


def playing_budget(c, seconds=6.0, fps=30):
    """changed nodes per frame while the phrase plays through Clew at controls c, from the second bar on"""
    import re, subprocess, tempfile
    pat = re.compile(rf'id="{PREFIX}_node_(\d+)" transform="([^"]+)" d="([^"]+)"')
    build_sim()
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as t:
        name = t.name
    subprocess.run([str(SIM_BIN), 'const', *[f'{v:.6f}' for v in c], f'{seconds:.2f}', name], check=True)
    inp, out = read_peaks(name)
    Path(name).unlink()
    prev, counts = None, []
    for i in range(int(2.0 * fps), int(seconds * fps) - 1):
        head = int(i / fps * SR / WINDOW)
        scope = (inp[head - WINDOWS + 1:head + 1], out[head - WINDOWS + 1:head + 1])
        now = {m[0]: m[1:] for m in pat.findall(frame_svg(c, scope=scope, head=head, tick=i))}
        if prev:
            counts.append(sum(now[k] != prev[k] for k in now))
        prev = now
    return sum(counts) / len(counts), max(counts)


def budget():
    """changed nodes per frame: at rest, while playing (defaults and the heaviest settings), and per control turn"""
    print('rest (silence, controls still): 0')
    for label, c in [('playing, defaults', DEFAULTS),
                     ('playing, Space 100', DEFAULTS[:2] + [1.0] + DEFAULTS[3:]),
                     ('playing, Space 100 + Squeeze 100', [1.0, DEFAULTS[1], 1.0] + DEFAULTS[3:])]:
        avg, peak = playing_budget(list(c))
        print(f'{label:34s} avg {avg:5.1f} peak {peak:3d}')


if __name__ == '__main__':
    if sys.argv[1:] == ['frames']:
        write_frames()
    elif sys.argv[1:] == ['budget']:
        budget()
    else:
        sys.exit(__doc__)
