#!/usr/bin/env python3
"""Lay out the reverse-polarity stage (U901/Q901/D901/C901) on the Hellen64
NA6/94 frame PCB (KiCad 6 file format, 20211014).

Equivalent of "Update PCB" for these four symbols, plus placement and routing:
  * adds nets /1B_PROT, /RP_GATE, /RP_VCAP; F1.1, F2.2, F3.1 move /1B -> /1B_PROT
  * places the parts in the free strip left of the connector (below J11)
  * removes the old /1B tracks, moves the 2D loop and a +12V run to B.Cu,
    deletes three GND stitching vias in the way
  * routes 1B / 1B_PROT (2 mm), the controller signals and GND vias
Geometry was checked with tools/plan_1b_layout.py.  Run from the repo root.
"""
import json
import re
import sys
import uuid

PCB = 'hellen64_NA6_94.kicad_pcb'
KFP = '/home/claude/ref/kfp'            # KiCad library footprints (kicad-footprints)
s = open(PCB).read()
assert '"Q901"' not in s, 'already applied'
U = lambda: str(uuid.uuid4())

# ------------------------------------------------------------------ nets
netlist = dict((name, int(n)) for n, name in re.findall(r'\n  \(net (\d+) "([^"]*)"\)', s))
last = max(netlist.values())
add = ['/1B_PROT', '/RP_GATE', '/RP_VCAP']
for i, name in enumerate(add, 1):
    netlist[name] = last + i
m = list(re.finditer(r'\n  \(net (\d+) "([^"]*)"\)', s))[-1]
s = s[:m.end()] + ''.join(f'\n  (net {netlist[n]} "{n}")' for n in add) + s[m.end():]
N = lambda name: netlist[name]
n1B, n2D, n12, nGND, nP = N('/1B'), N('/2D'), N('+12V'), N('GND'), N('/1B_PROT')


def fp_block(ref):
    i = s.find(f'(fp_text reference "{ref}"')
    st = s.rfind('\n  (footprint ', 0, i) + 1
    d = 0; j = st
    while True:
        c = s[j]
        if c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: break
        j += 1
    return st, j + 1


# fuse inputs -> /1B_PROT (both the SMD pad and the hand-solder hole share the number)
for ref in ('F1', 'F2', 'F3'):
    a, b = fp_block(ref)
    blk = s[a:b]
    k = blk.count(f'(net {n1B} "/1B")')
    assert k == 2, (ref, k)
    s = s[:a] + blk.replace(f'(net {n1B} "/1B")', f'(net {nP} "/1B_PROT")') + s[b:]

# ------------------------------------------------------------------ removals / layer moves
def drop(pattern, expect):
    global s
    found = list(re.finditer(pattern, s))
    assert len(found) == expect, (pattern, len(found))
    for f in reversed(found):
        s = s[:f.start()] + s[f.end():]

# all /1B tracks (old feed from pad 12 to the fuses)
drop(r'\n  \(segment [^\n]*\(net %d\) \(tstamp [0-9a-f-]+\)\)' % n1B, 10)
# 2D loop round the left end of the connector + the start of the run along y=26
for a, b in [('34.77332 37.78034', '32.14832 35.15534'), ('32.14832 35.15534', '32.14832 29.25534'),
             ('32.14832 29.25534', '35.39832 26.00534'), ('35.39832 26.00534', '52.24832 26.00534')]:
    drop(r'\n  \(segment \(start %s\) \(end %s\) \(width 2\) \(layer "F\.Cu"\) \(net %d\) \(tstamp [0-9a-f-]+\)\)'
         % (re.escape(a), re.escape(b), n2D), 1)
# three GND stitching vias under the new parts
for x, y in [('28.3', '25.4'), ('30.34832', '28.13034'), ('33.22332', '39.70034')]:
    drop(r'\n  \(via \(at %s %s\) [^\n]*\(net %d\) \(tstamp [0-9a-f-]+\)\)' % (re.escape(x), re.escape(y), nGND), 1)
# +12V run up the strip -> B.Cu (same path)
for a, b in [('29.35 43.45', '29.35 24.55'), ('29.35 24.55', '33.75 20.15')]:
    pat = r'\(segment \(start %s\) \(end %s\) \(width 0\.508\) \(layer "F\.Cu"\) \(net %d\)' % (re.escape(a), re.escape(b), n12)
    assert len(re.findall(pat, s)) == 1, a
    s = re.sub(pat, lambda mm: mm.group(0).replace('"F.Cu"', '"B.Cu"'), s)

# ------------------------------------------------------------------ new copper
segs, vias = [], []
def track(net, layer, w, pts):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        segs.append(f'  (segment (start {x1} {y1}) (end {x2} {y2}) (width {w}) (layer "{layer}.Cu") (net {N(net)}) (tstamp {U()}))')
def via(net, x, y):
    vias.append(f'  (via (at {x} {y}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net {N(net)}) (tstamp {U()}))')

track('/1B', 'F', 2, [(37.0893, 28.62534), (35.9, 27.45), (32.0, 27.0)])          # pin 1B -> D901.1
track('/1B', 'F', 2, [(30.6, 26.9), (27.42, 29.6)])                                 # D901.1 -> Q901 S
track('/1B', 'F', 0.4, [(25.0, 29.75), (26.9, 29.75)])                              # C901.2 -> S
track('/1B', 'F', 0.3, [(25.6, 31.3), (26.9, 31.1)])                                # U901 ANODE -> S
track('/1B', 'F', 0.2, [(22.9625, 33.35), (24.1, 33.35), (24.1, 31.45), (24.9, 31.45)])  # EN -> ANODE
track('/RP_VCAP', 'F', 0.3, [(23.01, 29.75), (22.9625, 31.45)])                     # C901.1 -> VCAP
track('/RP_GATE', 'F', 0.3, [(25.6, 32.4), (31.98, 32.4), (31.98, 30.9)])           # GATE (under Q901)
track('/1B_PROT', 'F', 0.3, [(25.6, 33.35), (26.5, 33.7), (27.2, 33.7)])            # CATHODE -> tab
track('/1B_PROT', 'F', 2, [(31.5, 35.6), (43.2, 35.6)])                             # tab -> F3.1
track('/1B_PROT', 'F', 2, [(42.7, 35.6), (42.7, 38.3)])                             # -> F1.1
track('/1B_PROT', 'F', 2, [(38.03, 35.6), (38.03, 38.0)])                           # -> F2.2
track('GND', 'F', 0.3, [(22.9625, 32.4), (21.9, 32.4)])                             # U901 GND -> via
track('GND', 'F', 1, [(22.5, 24.3), (22.5, 26.7)])                                  # D901 GND via strip
track('GND', 'F', 1, [(22.5, 25.5), (24.2, 25.5)])
track('/2D', 'F', 2, [(38.8, 26.00534), (52.24832, 26.00534)])                      # 2D resumes on top
track('/2D', 'B', 1.5, [(38.8, 26.00534), (35.0, 26.0), (34.2, 26.8), (34.2, 37.6), (34.13, 38.3)])  # to F2.1 hole
for net, x, y in [('/2D', 38.8, 26.00534), ('+12V', 29.35, 43.45), ('+12V', 33.75, 20.15),
                  ('GND', 21.9, 32.4), ('GND', 22.5, 24.3), ('GND', 22.5, 25.5), ('GND', 22.5, 26.7)]:
    via(net, x, y)

# ------------------------------------------------------------------ footprints
sym = json.load(open('/tmp/place/symbols.json'))
pinnets = json.load(open('/tmp/place/pinnets.json'))
pinfn = {'U901': {'1': ('VCAP', 'passive'), '2': ('GND', 'power_in'), '3': ('EN', 'input'),
                  '4': ('CATHODE', 'power_in'), '5': ('GATE', 'output'), '6': ('ANODE', 'power_in')},
         'Q901': {'1': ('G', 'passive'), '2': ('D', 'passive'), '3': ('S', 'passive')},
         'D901': {'1': ('A1', 'passive'), '2': ('A2', 'passive')},
         'C901': {'1': (None, 'passive'), '2': (None, 'passive')}}
PLACE = {'D901': (27.6, 25.5, 180, (27.6, 25.5)), 'Q901': (29.7, 34.5, 270, (29.7, 31.3)),
         'U901': (24.1, 32.4, 0, (24.1, 35.0)), 'C901': (23.8, 29.75, 0, (23.8, 28.55))}
LIB = {'Q901': 'Package_TO_SOT_SMD.pretty/TO-252-2.kicad_mod', 'D901': 'Diode_SMD.pretty/D_SMC.kicad_mod',
       'U901': 'Package_TO_SOT_SMD.pretty/SOT-23-6.kicad_mod'}
MODEL = {'Q901': 'Package_TO_SOT_SMD.3dshapes/TO-252-2.wrl', 'D901': 'Diode_SMD.3dshapes/D_SMC.wrl',
         'U901': 'Package_TO_SOT_SMD.3dshapes/SOT-23-6.wrl'}


def ql(layer_list):
    return ' '.join(f'"{l}"' for l in layer_list.split())


def rel_text(ref, rot, absxy):
    """Reference text position in footprint-local coordinates for an absolute target."""
    import math
    X, Y = PLACE[ref][0], PLACE[ref][1]
    dx, dy = absxy[0] - X, absxy[1] - Y
    r = math.radians(rot)
    # inverse of X = x cos + y sin ; Y = -x sin + y cos
    lx = dx * math.cos(r) - dy * math.sin(r)
    ly = dx * math.sin(r) + dy * math.cos(r)
    return round(lx, 4), round(ly, 4)


def pad_line(ref, num, rest_attrs, rot, local_ang, typ, shape, at_xy, size, layers):
    ang = (local_ang + rot) % 360
    ang_s = '' if ang == 0 else f' {ang:g}'
    net = ''
    pf = ''
    if num:
        nn = '/' + pinnets[ref][num] if pinnets[ref][num] != 'GND' else 'GND'
        net = f' (net {N(nn)} "{nn}")'
        fn, pt = pinfn[ref][num]
        pf = (f' (pinfunction "{fn}")' if fn else '') + f' (pintype "{pt}")'
    return (f'    (pad "{num}" {typ} {shape} (at {at_xy[0]} {at_xy[1]}{ang_s}) (size {size[0]} {size[1]}) '
            f'(layers {ql(layers)}){rest_attrs}\n     {net}{pf} (tstamp {U()}))')


def lib_footprint(ref):
    X, Y, rot, txt = PLACE[ref]
    src = open(f'{KFP}/{LIB[ref]}').read()
    name = sym[ref]['fp']
    tedit = re.search(r'\(tedit ([0-9A-Fa-f]+)\)', src).group(1)
    descr = re.search(r'\(descr "([^"]*)"\)', src).group(1)
    tags = re.search(r'\(tags "([^"]*)"\)', src).group(1)
    tx, ty = rel_text(ref, rot, txt)
    out = [f'  (footprint "{name}" (layer "F.Cu")',
           f'    (tedit {tedit}) (tstamp {U()})',
           f'    (at {X} {Y}{"" if rot == 0 else " " + str(rot)})',
           f'    (descr "{descr}")', f'    (tags "{tags}")',
           f'    (property "LCSC" "{sym[ref]["lcsc"]}")',
           f'    (property "Sheetfile" "hellen64_NA6_94.kicad_sch")', f'    (property "Sheetname" "")',
           f'    (path "/{sym[ref]["uuid"]}")', '    (attr smd)',
           f'    (fp_text reference "{ref}" (at {tx} {ty}) (layer "F.SilkS")',
           '      (effects (font (size 0.8 0.8) (thickness 0.15)))', f'      (tstamp {U()})', '    )',
           f'    (fp_text value "{sym[ref]["value"]}" (at 0 0{"" if rot == 0 else " " + str(rot)}) (layer "F.Fab")',
           '      (effects (font (size 1 1) (thickness 0.15)))', f'      (tstamp {U()})', '    )']
    for m in re.finditer(r'\(fp_text user (\S+) \(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\) \(layer (\S+)\)\s*\(effects \(font \(size ([\d.]+) ([\d.]+)\) \(thickness ([\d.]+)\)\)\)', src):
        out += [f'    (fp_text user "{m.group(1).replace('%R', '${REFERENCE}')}" (at {m.group(2)} {m.group(3)}{"" if rot == 0 else " " + str(rot)}) (layer "{m.group(5)}")',
                f'      (effects (font (size {m.group(6)} {m.group(7)}) (thickness {m.group(8)})))', f'      (tstamp {U()})', '    )']
    for m in re.finditer(r'\(fp_line \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(layer (\S+)\) \(width ([\d.]+)\)\)', src):
        out.append(f'    (fp_line (start {m.group(1)} {m.group(2)}) (end {m.group(3)} {m.group(4)}) '
                   f'(layer "{m.group(5)}") (width {m.group(6)}) (tstamp {U()}))')
    for m in re.finditer(r'\(pad (\S+) (\w+) (\w+) \(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\) \(size ([\d.]+) ([\d.]+)\) \(layers ([^)]*)\)([^\n]*)\)', src):
        num = m.group(1).strip('"')
        extra = m.group(10).strip()
        extra = (' ' + extra) if extra else ''
        out.append(pad_line(ref, num, extra, rot, float(m.group(6) or 0), m.group(2), m.group(3),
                            (m.group(4), m.group(5)), (m.group(7), m.group(8)), m.group(9)))
    out += [f'    (model "${{KICAD6_3DMODEL_DIR}}/{MODEL[ref]}"', '      (offset (xyz 0 0 0))',
            '      (scale (xyz 1 1 1))', '      (rotate (xyz 0 0 0))', '    )', '  )']
    return '\n'.join(out)


def c0603(ref):
    X, Y, rot, txt = PLACE[ref]
    tx, ty = rel_text(ref, rot, txt)
    pads = '\n'.join(pad_line(ref, n, ' (roundrect_rratio 0.09999988235)', rot, 0, 'smd', 'roundrect',
                              (x, 0), ('0.850001', '0.850001'), 'F.Cu F.Paste F.Mask')
                     for n, x in (('1', -0.790001), ('2', 0.790001)))
    return '\n'.join([
        f'  (footprint "hellen-one-common:C0603" (layer "F.Cu")', f'    (tedit 0) (tstamp {U()})',
        f'    (at {X} {Y})', f'    (property "LCSC" "{sym[ref]["lcsc"]}")',
        '    (property "Sheetfile" "hellen64_NA6_94.kicad_sch")', '    (property "Sheetname" "")',
        f'    (path "/{sym[ref]["uuid"]}")',
        f'    (fp_text reference "{ref}" (at {tx} {ty}) (layer "F.SilkS")',
        '      (effects (font (size 0.8 0.8) (thickness 0.15)))', f'      (tstamp {U()})', '    )',
        f'    (fp_text value "{sym[ref]["value"]}" (at 0 1.3) (layer "F.SilkS") hide',
        '      (effects (font (size 0.820001 0.820001) (thickness 0.17)) (justify left bottom))', f'      (tstamp {U()})', '    )',
        f'    (fp_line (start 0 -0.349986) (end 0 0.399999) (layer "F.SilkS") (width 0.2) (tstamp {U()}))',
        pads,
        '    (model ":hellen-one-models:0603 cap.STEP"', '      (offset (xyz 0.000081 0.000078 0))',
        '      (scale (xyz 1 1 1))', '      (rotate (xyz -90 -0 0))', '    )', '  )'])


fps_txt = '\n'.join([lib_footprint('D901'), lib_footprint('Q901'), lib_footprint('U901'), c0603('C901')])
# insert after the last footprint
last_fp = s.rfind('\n  (footprint ')
st, en = None, None
d = 0; j = last_fp + 1
while True:
    c = s[j]
    if c == '(': d += 1
    elif c == ')':
        d -= 1
        if d == 0: break
    j += 1
s = s[:j+1] + '\n' + fps_txt + s[j+1:]
# insert copper after the last via (tracks/vias section)
lv = list(re.finditer(r'\n  \(via [^\n]*\)\)', s))[-1]
s = s[:lv.end()] + '\n' + '\n'.join(segs + vias) + s[lv.end():]

# sanity: balanced parens
d = 0
for c in s:
    if c == '(': d += 1
    elif c == ')': d -= 1
    assert d >= 0
assert d == 0
open(PCB, 'w').write(s)
print('ok:', len(segs), 'segments,', len(vias), 'vias, 4 footprints; nets', {n: N(n) for n in add})
