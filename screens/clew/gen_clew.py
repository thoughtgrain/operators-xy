#!/usr/bin/env python3
"""Clew's screen (pass 05 v2): one wave, the playing's swell then each repeat's, under a compressor line stepping
down, one step per encoder column; the first step dips with the gain reduction, the later ones with the ducking, and
the room ripples along each step's tail.

The design is authored the way the device will draw it, so the frames here become panel.svg.fragment with no
redrawing:

  paths 0..3   the wave, one mutable outline per column (32 samples along it, 32 back 1 px below: a closed ribbon)
  nodes 4..11  the SDK's two-page header bar
  treads       4 steps x 12 cells; each cell is a flat segment or one cycle of ripple at three heights and three phases (10 nodes, one
               shown), authored at the cell's left end on the step line, so a cell only ever translates
  risers       3 risers x 6 segments of 7 px, stacked from one step down to the next; spare segments hidden

Every frame comes from pose(controls, live, phase, sway). live() works out what's sounding from the send's input
peaks and the tempo; effect pages don't receive those yet (it needs an SDK change, handoff.md), so sim/scope.cpp
stands in for them by running toro's and Clew's engine code on a computer.

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
CELLS = 12
CELL_W = 117 / CELLS
WIGGLE = [0, 1.5, 3.0, 4.5]                 # ripple heights: flat, low, mid, high (one 9.75 px cycle per cell; taller folds the 1 px ribbon)
PHASES = 3                                  # the ripple travels a third of a cycle at a time
VARIANTS = 1 + 3 * PHASES                   # flat, then each height at each phase
RISER_SEG, RISER_N = 7.0, 6

# palette: (name, fill, stroke, width). Paths draw hollow, so their fill is none.
PALETTE = [('P_WAVE', 'none', G[5], 1.5), ('P_WAVE_DRY', 'none', G[7], 2.0),
           ('P_TREAD', G[5], G[5], 0.3), ('P_RIPPLE', G[4], G[4], 0.3)]
P = {n: k for k, (n, *_r) in enumerate(PALETTE)}

N_PATH = 0
N_HDR = 4
N_CELL = N_HDR + 8                          # tread t, cell j, variant v: N_CELL + (t * CELLS + j) * VARIANTS + v
N_RISER = N_CELL + 4 * CELLS * VARIANTS            # riser r, segment s: N_RISER + r * RISER_N + s
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
WIN_S = WINDOW / 44100
HISTORY = 128                               # windows of input the page keeps in view: about 4.1 s
SR = 44100
PERIOD = 117 / 7                            # the wave's drawn cycle: seven per column, as fine as 32 samples allow


def live(c, inp, head, bpm=120.0):
    """what's sounding, worked out from the send's input peaks (oldest first, `head` the newest) and the tempo:
    the playing's swell, each repeat's (the input a delay time ago, at Echo's level), the room, the ducking and
    the gain reduction. The device does this from the levels the SDK change would give it."""
    sq, echo, space, blend, tone, motion, dry, attack, order = c

    def x(i, spread=0):
        got = [inp[j] for j in range(i - spread, i + spread + 1) if 0 <= j < len(inp)]
        return 1.6 * max(got) if got else 0.0
    step = 60.0 / bpm / 4
    div = DIVS[min(7, int(echo * 8))]
    delay = div * step / WIN_S                                      # in windows
    level = min(1.0, echo * 8) * 0.8 if echo > 0.01 else 0.0
    fb = 0.15 + 0.6 * echo
    swells = [x(head) * dry] + [x(head - round(k * delay), 2) * level * fb ** (k - 1) for k in range(1, 4)]
    decay = (0.25 + 3 * space * space) / WIN_S
    room = space * 0.29 * sum(x(head - j) * math.exp(-j / decay) for j in range(HISTORY))
    follower = min(1.0, x(head) / 0.6)
    return {'swells': swells, 'room': min(1.2, room), 'duck': blend * follower, 'gr': sq * follower}


def advance(phase, sway, lv, fps=30):
    """the wave's phase and the steps' sway move only while something sounds, so silence is still"""
    energy = min(1.0, 4 * (sum(lv['swells']) + lv['room']))
    return phase + 2 * math.pi * 0.9 / fps * energy, sway + 2 * math.pi * 0.3 / fps * energy


def pose(c, lv=None, phase=0.0, sway=0.0):
    """everything the screen draws for controls c (eight controls and Order, each 0..1) and what's sounding (lv,
    from live(); None is silence). phase and sway advance only while it sounds (advance())."""
    sq, echo, space, blend, tone, motion, dry, attack, order = c
    tone = 2 * tone - 1
    lv = lv or {'swells': [0.0] * 4, 'room': 0.0, 'duck': 0.0, 'gr': 0.0}
    fx_first = order > 0.5                                          # FX first: the compressor presses the tails too

    # the compressor line: steps down from Squeeze's ceiling; the first dips with the gain reduction, the later
    # ones with the ducking (with FX first, all with the gain reduction); Motion sways them while it sounds
    base = 64 - 40 * sq
    sw = motion * 3 * math.sin(sway)
    tread_y, limits = [], []
    for k in range(4):
        lim = base * 0.82 ** k
        if k == 0 or fx_first:
            lim -= lv['gr'] * 10 * sq
        else:
            lim -= lv['duck'] * 16
        lim = max(4.0, lim)
        limits.append(lim)
        y = C_Y - lim + ((sw if k % 2 else -sw) if k > 0 else 0)
        tread_y.append(float(round(y)))

    # the tails: the far part of each step ripples with the room, more on the later steps, travelling with the
    # phase. Tone: darker shorter and lower (the room damps sooner), brighter taller.
    reach = int(round(CELLS * (0.15 + 0.75 * space) * (1 - 0.4 * max(0.0, -tone)))) if space > 0.01 else 0   # darker damps sooner
    turn = int(math.floor(1.3 * phase / (2 * math.pi / PHASES))) % PHASES   # the ripple travels with the phase
    cells = []                                                      # (tread, cell, variant, x, y)
    for k in range(4):
        amp = (1.0 + 7 * lv['room']) * (0.6 + 0.4 * k / 3) if reach else 0.0
        if fx_first:
            amp = min(amp, 1.0)
        first = CELLS - reach
        for j in range(CELLS):
            x = COL_X[k] + j * CELL_W
            v = 0
            if reach and j >= first:
                a = amp * (1 + 0.5 * tone) * (j - first + 1) / reach   # grows along the tail; Tone: brighter taller
                h = 0 if a < 0.75 else (1 if a < 2.25 else (2 if a < 3.75 else 3))
                v = h + 3 * turn if h else 0
            if k == 0 and j * CELL_W + CELL_W / 2 < 3 + attack * 80:
                v = -1                                              # Attack: the first step starts late
            cells.append((k, j, v, round(x * 2) / 2, tread_y[k]))

    risers = []
    for k in range(3):
        top, bot = min(tread_y[k], tread_y[k + 1]), max(tread_y[k], tread_y[k + 1])
        gap = bot - top
        n = 0 if gap < 3 else min(RISER_N, int(math.ceil(gap / RISER_SEG)))
        risers.append([(COL_X[k + 1], max(top, min(top + s * RISER_SEG, bot - RISER_SEG))) for s in range(n)])

    # the wave: one line, a swell per step (the playing, then each repeat), each pressed by its step
    amps = [80 * v for v in lv['swells']]
    att_px = 3 + attack * 80
    waves = []
    for k in range(4):
        pts = []
        for s in range(SAMPLES):
            x = COL_X[k] + 117 * s / (SAMPLES - 1)
            env = 1.2                                               # the line never quite vanishes
            for j in range(4):
                d0 = x - COL_X[j]
                if d0 >= -2:
                    d0 = max(0.0, d0)
                    fade = 0.022 if j == 0 else 0.022 * (1 - 0.5 * tone)   # Tone: darker repeats die sooner
                    env = max(env, amps[j] * (1 - math.exp(-d0 / 4)) * math.exp(-d0 * fade))
            v = env * math.sin(2 * math.pi * (x - COL_X[0]) / PERIOD - phase)
            if k == 0 and x - COL_X[0] < att_px:
                v *= 1 + 0.8 * attack                               # the transient the compressor didn't catch
                v = max(-limits[0] - 20, min(limits[0] + 20, v))   # a slow attack lets the note's start out
            else:
                v = soft(v, max(1.5, limits[k] - 2))
            v = max(-62.0, min(62.0, v))                            # the outline stays within 64 px of its origin
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


def cell_shape(v):
    """a cell's outline, relative to its left end on the tread: flat, or one cycle of ripple at a height and phase"""
    if v == 0:
        return ribbon([(0, 0), (CELL_W, 0)], 1.5)
    h, ph = WIGGLE[(v - 1) % 3 + 1], (v - 1) // 3
    pts = [(CELL_W * t / 12, -h * math.sin(2 * math.pi * t / 12 - 2 * math.pi * ph / PHASES)) for t in range(13)]
    return ribbon(pts, 1.0)


def path_d(pts):
    return 'M ' + ' L '.join(f'{f(x)} {f(y)}' for x, y in pts) + ' Z'


def header_values(c):
    sq, echo, space, blend, tone, motion, dry, attack, order = c
    names = {1: '1/32', 1.5: '3/64', 2: '1/16', 3: '3/32', 4: '1/8', 6: '3/16', 8: '1/4', 16: '1/2'}
    return [f'{round(sq * 100)}', names[DIVS[min(7, int(echo * 8))]] if echo > 0.004 else 'off', f'{round(space * 100)}',
            f'{round(blend * 100)}', (f'{round((2 * tone - 1) * 100):+d}' if abs(2 * tone - 1) > 0.005 else '0'),
            f'{round(motion * 100)}', f'{round(dry * 100)}', f'{0.5 * 60 ** attack:.1f}']


def frame_svg(c, page=0, shift=False, lv=None, phase=0.0, sway=0.0):
    p = pose(c, lv, phase, sway)
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
        for var in range(VARIANTS):                                  # a node's own shape never changes
            n = N_CELL + (k * CELLS + j) * VARIANTS + var
            shown = var == v
            pal = 'P_TREAD' if var == 0 else 'P_RIPPLE'
            _, fill, stroke, w = PALETTE[P[pal]]
            if not shown:
                m = 'matrix(1 0 0 1 640 320)'
            else:
                m = f'matrix(1 0 0 1 {f(x)} {f(y)})'
            o.append(f'<path id="{PREFIX}_node_{n}" transform="{m}" d="{path_d(cell_shape(var))}" fill="{fill}" stroke="{stroke}" stroke-width="{w}"/>')
    for r in range(3):
        segs = p['risers'][r]
        for s in range(RISER_N):
            n = N_RISER + r * RISER_N + s
            x, y = segs[s] if s < len(segs) else (640, 320)
            o.append(f'<path id="{PREFIX}_node_{n}" transform="matrix(1 0 0 1 {f(x)} {f(y)})" d="M -0.75 0 L 0.75 0 L 0.75 {f(RISER_SEG)} L -0.75 {f(RISER_SEG)} Z" fill="{G[5]}" stroke="{G[5]}" stroke-width="0.3"/>')
    # the wave: four mutable outlines, each its column's samples and back 1 px below
    for k, pts in enumerate(p['waves']):
        outline = pts + [(x, y + 1.0) for x, y in reversed(pts)]
        pal = 'P_WAVE_DRY' if k == 0 else 'P_WAVE'
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
SNAP_AT = 4.30                                  # seconds: the frames show this moment of the third bar


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
def run(c, seconds):
    """the send's input peaks per window with controls c held from the start"""
    key = (tuple(round(v, 4) for v in c), seconds)
    if key not in _runs:
        import subprocess, tempfile
        build_sim()
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as t:
            name = t.name
        subprocess.run([str(SIM_BIN), 'const', *[f'{v:.6f}' for v in c], f'{seconds:.2f}', name], check=True)
        _runs[key] = read_peaks(name)[0]
        Path(name).unlink()
    return _runs[key]


def playing_at(c, at=SNAP_AT, fps=30):
    """(live, phase, sway) at `at` seconds, with the phase and sway run from the start as the device would"""
    inp = run(c, at + 0.2)
    phase = sway = 0.0
    lv = None
    for i in range(int(at * fps) + 1):
        lv = live(c, inp, int(i / fps / WIN_S))
        phase, sway = advance(phase, sway, lv, fps)
    return lv, phase, sway


def write_frames():
    out = HERE / 'frames'
    out.mkdir(exist_ok=True)
    for old in out.glob('*.svg'):
        old.unlink()

    def playing(c, **kw):
        lv, phase, sway = playing_at(c)
        return frame_svg(c, lv=lv, phase=phase, sway=sway, **kw)
    (out / 'rest.svg').write_text(frame_svg(DEFAULTS))                # silence
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
    import re
    pat = re.compile(rf'id="{PREFIX}_node_(\d+)" transform="([^"]+)" d="([^"]+)"')
    inp = run(c, seconds + 0.2)
    phase = sway = 0.0
    prev, counts = None, []
    for i in range(int(seconds * fps)):
        lv = live(c, inp, int(i / fps / WIN_S))
        phase, sway = advance(phase, sway, lv, fps)
        if i < 2 * fps:
            continue
        now = {m[0]: m[1:] for m in pat.findall(frame_svg(c, lv=lv, phase=phase, sway=sway))}
        if prev:
            counts.append(sum(now[k] != prev[k] for k in now))
        prev = now
    return sum(counts) / len(counts), max(counts)


def budget():
    """changed nodes per frame at rest and while the phrase plays (defaults and the heaviest settings)"""
    print('rest (silence, controls still): 0')
    for label, c in [('playing, defaults', DEFAULTS),
                     ('playing, Space 100', DEFAULTS[:2] + [1.0] + DEFAULTS[3:]),
                     ('playing, Echo, Space, Blend 100', [DEFAULTS[0], 1.0, 1.0, 1.0] + DEFAULTS[4:])]:
        avg, peak = playing_budget(list(c))
        print(f'{label:34s} avg {avg:5.1f} peak {peak:3d}')


if __name__ == '__main__':
    if sys.argv[1:] == ['frames']:
        write_frames()
    elif sys.argv[1:] == ['budget']:
        budget()
    else:
        sys.exit(__doc__)
