#!/usr/bin/env python3
"""Plan + check placement of U901/Q901/D901/C901 (reverse-polarity stage) on the
Hellen NA6 frame PCB.  Pure geometry check against existing copper (no KiCad)."""
import re, math, json, sys
PCB = sys.argv[1] if len(sys.argv) > 1 else 'hellen64_NA6_94.kicad_pcb'
s = open(PCB).read()
nets = dict(re.findall(r'\n  \(net (\d+) "([^"]*)"\)', s))

def tr(X, Y, A, px, py):
    r = math.radians(A)
    return (X + px*math.cos(r) + py*math.sin(r), Y - px*math.sin(r) + py*math.cos(r))

# ---------------------------------------------------------------- existing copper
items = []   # dict(kind, layer set, geom, net, tag)
for m in re.finditer(r'\n  \(footprint "([^"]+)"(?: (?:locked|placed))* \(layer "([^"]+)"\)', s):
    st = m.start() + 3; d = 0; j = st
    while True:
        c = s[j]
        if c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: break
        j += 1
    blk = s[st:j+1]
    at = re.search(r'\n    \(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
    X, Y, A = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
    ref = (re.search(r'\(fp_text reference "([^"]+)"', blk) or re.search(r'"Reference" "([^"]+)"', blk)).group(1)
    for p in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)(?: (?:locked|placed))* \(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\) \(size ([\d.]+) ([\d.]+)\)(.*?)\n      \)?', blk):
        typ, shp = p.group(2), p.group(3)
        px, py = float(p.group(4)), float(p.group(5)); pa = float(p.group(6) or 0)
        w, h = float(p.group(7)), float(p.group(8))
        rest = blk[p.end():p.end()+400]
        nm = re.search(r'\(net \d+ "([^"]*)"\)', p.group(9) + rest[:200])
        net = nm.group(1) if nm and 'pad "' not in (p.group(9)+rest[:200])[:nm.start()] else ''
        lay = re.search(r'\(layers ([^)]*)\)', p.group(9) + rest)
        lays = lay.group(1) if lay else ''
        L = set()
        if '*.Cu' in lays or typ == 'thru_hole': L = {'F', 'B'}
        else:
            if 'F.Cu' in lays: L.add('F')
            if 'B.Cu' in lays: L.add('B')
        if not L: continue
        cx, cy = tr(X, Y, A, px, py)
        ang = (pa) % 180   # pad angle in file already includes footprint rotation
        if abs(ang - 90) < 1: w, h = h, w
        if shp in ('circle',) or typ == 'np_thru_hole':
            items.append(dict(k='circ', L=L, g=(cx, cy, max(w, h)/2), net=net, tag=f'{ref}.{p.group(1)}'))
        else:
            items.append(dict(k='rect', L=L, g=(cx-w/2, cy-h/2, cx+w/2, cy+h/2), net=net, tag=f'{ref}.{p.group(1)}'))
seg_re = r'\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(width ([\d.]+)\) \(layer "([FB])\.Cu"\) \(net (\d+)\)'
for m in re.finditer(seg_re, s):
    x1, y1, x2, y2, w = map(float, m.groups()[:5])
    items.append(dict(k='seg', L={m.group(6)}, g=(x1, y1, x2, y2, w/2), net=nets[m.group(7)], tag='trk'))
for m in re.finditer(r'\(via \(at ([-\d.]+) ([-\d.]+)\) \(size ([\d.]+)\)[^\n]*\(net (\d+)\)', s):
    x, y, dd = map(float, m.groups()[:3])
    items.append(dict(k='circ', L={'F', 'B'}, g=(x, y, dd/2), net=nets[m.group(4)], tag='via'))

# ---------------------------------------------------------------- plan
P = {}
# footprint positions (KiCad orientation: CCW positive)
P['D901'] = (28.35, 41.3, 0)
P['Q901'] = (31.5, 31.95, 270)
P['U901'] = (25.9, 29.85, 0)
P['C901'] = (25.3, 27.2, 0)
FP = {   # local pads: num, x, y, w, h, net
 'D901': [('1', -3.4, 0, 2.5, 3.3, '/1B'), ('2', 3.4, 0, 2.5, 3.3, 'GND')],
 'Q901': [('1', -4.2, -2.28, 2.2, 1.2, '/RP_GATE'), ('3', -4.2, 2.28, 2.2, 1.2, '/1B'), ('2', 2.1, 0, 6.4, 5.8, '/1B_PROT')],
 'U901': [('1', -1.1375, -0.95, 1.325, 0.6, '/RP_VCAP'), ('2', -1.1375, 0, 1.325, 0.6, 'GND'), ('3', -1.1375, 0.95, 1.325, 0.6, '/1B'),
          ('4', 1.1375, 0.95, 1.325, 0.6, '/1B_PROT'), ('5', 1.1375, 0, 1.325, 0.6, '/RP_GATE'), ('6', 1.1375, -0.95, 1.325, 0.6, '/1B')],
 'C901': [('1', -0.79, 0, 0.85, 0.85, '/RP_VCAP'), ('2', 0.79, 0, 0.85, 0.85, '/1B')],
}
CRT = {'D901': (4.9, 3.35), 'Q901': (5.55, 3.5), 'U901': (2.05, 1.7), 'C901': (1.3, 0.65)}
new = []
padpos = {}
for ref, (X, Y, A) in P.items():
    for num, px, py, w, h, net in FP[ref]:
        cx, cy = tr(X, Y, A, px, py)
        if abs(A % 180 - 90) < 1: w, h = h, w
        new.append(dict(k='rect', L={'F'}, g=(cx-w/2, cy-h/2, cx+w/2, cy+h/2), net=net, tag=f'{ref}.{num}'))
        padpos[f'{ref}.{num}'] = (round(cx, 3), round(cy, 3))
T = [
 ('/1B', 'F', 1.6, [(37.0893, 28.62534), (36.0, 25.65), (29.8, 25.65), (29.22, 26.9)]),   # pin 1B -> Q901 S (over G)
 ('/1B', 'F', 1.6, [(29.8, 25.65), (26.2, 25.65)]),                                      # TVS feed vias
 ('/1B', 'F', 0.4, [(26.5, 27.2), (28.7, 27.2)]),                                        # C901.2 -> S
 ('/1B', 'F', 0.3, [(27.5, 28.9), (28.8, 28.6)]),                                        # ANODE -> S
 ('/1B', 'F', 0.2, [(24.7625, 30.8), (25.9, 30.8), (25.9, 28.9), (26.7, 28.9)]),        # EN -> ANODE under chip
 ('/RP_VCAP', 'F', 0.3, [(24.51, 27.2), (24.7625, 28.9)]),
 ('/RP_GATE', 'F', 0.3, [(27.6, 29.85), (33.2, 29.85), (33.78, 29.3), (33.78, 28.6)]),  # GATE under Q901 body
 ('/1B_PROT', 'F', 0.3, [(27.6, 30.8), (28.2, 31.3), (28.9, 31.3)]),                    # CATHODE -> tab
 ('/1B_PROT', 'F', 2.0, [(31.5, 35.6), (43.2, 35.6)]),                                   # tab -> F3.1
 ('/1B_PROT', 'F', 2.0, [(42.7, 35.6), (42.7, 38.3)]),                                   # -> F1.1
 ('/1B_PROT', 'F', 2.0, [(38.03, 35.6), (38.03, 38.0)]),                                 # -> F2.2
 ('/1B', 'B', 2.0, [(27.5, 25.65), (26.5, 26.65), (26.5, 38.4), (25.2, 38.9)]),          # TVS feed on bottom
 ('/1B', 'B', 2.0, [(24.3, 38.9), (26.1, 38.9)]),
 ('/1B', 'F', 2.0, [(24.3, 38.9), (26.1, 38.9)]),
 ('/1B', 'F', 2.0, [(25.2, 38.9), (25.2, 40.5)]),                                        # into D901.1
 ('GND', 'F', 0.3, [(24.7625, 29.85), (23.75, 29.85)]),                                  # U901 GND -> via
 ('GND', 'F', 1.0, [(31.0, 38.9), (32.0, 38.9)]),                                        # D901.2 vias
 ('GND', 'F', 1.0, [(31.5, 38.9), (31.5, 40.5)]),
 ('/2D', 'F', 2.0, [(38.8, 26.0), (52.25, 26.0)]),
 ('/2D', 'B', 1.5, [(38.8, 26.0), (35.0, 26.0), (34.2, 26.8), (34.2, 37.6), (34.13, 38.3)]),
 ('+12V', 'B', 0.508, [(29.35, 43.45), (29.35, 24.55), (33.75, 20.15)]),
]
V = [('/2D', 38.8, 26.0), ('+12V', 29.35, 43.45), ('+12V', 33.75, 20.15),
     ('/1B', 26.6, 25.65), ('/1B', 27.5, 25.65), ('/1B', 28.4, 25.65),
     ('/1B', 24.3, 38.9), ('/1B', 25.2, 38.9), ('/1B', 26.1, 38.9),
     ('GND', 23.75, 29.85), ('GND', 31.0, 38.9), ('GND', 32.0, 38.9)]
for net, L, w, pts in T:
    for a, b in zip(pts, pts[1:]):
        new.append(dict(k='seg', L={L}, g=(a[0], a[1], b[0], b[1], w/2), net=net, tag='new trk'))
for net, x, y in V:
    new.append(dict(k='circ', L={'F', 'B'}, g=(x, y, 0.3), net=net, tag='new via'))

# ---------------------------------------------------------------- removals
def is_removed(it):
    if it['tag'] == 'trk':
        x1, y1, x2, y2, r = it['g']
        if it['net'] == '/1B': return True
        if it['net'] == '/2D' and (min(x1, x2) < 36 or (abs(y1-26.0) < 0.1 and min(x1, x2) < 36.0)): return True
        if it['net'] == '/2D' and abs(x1-35.39832) < 0.01 and abs(x2-52.24832) < 0.01: return True
        if it['net'] == '+12V' and (abs(x1-29.35) < 0.01 or abs(x2-29.35) < 0.01) and min(y1, y2) > 20 and max(y1, y2) < 44: 
            return not (abs(x1-33.778254) < 0.01)   # keep the bottom diagonal to M10
    if it['tag'] == 'via' and it['net'] == 'GND':
        x, y, r = it['g']
        for (vx, vy) in [(28.3, 25.4), (30.34832, 28.13034), (33.22332, 39.70034), (23.5, 41.5)]:
            if abs(x-vx) < 0.01 and abs(y-vy) < 0.01: return True
    return False
for it in items:   # nets after Update PCB
    if it['tag'] in ('F1.1', 'F2.2', 'F3.1'): it['net'] = '/1B_PROT'
keep = [it for it in items if not is_removed(it)]
removed = [it for it in items if is_removed(it)]

# ---------------------------------------------------------------- geometry
def seg_seg(p1, p2, q1, q2):
    def dps(p, a, b):
        ax, ay = a; bx, by = b; px, py = p
        dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy
        t = 0 if L2 == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L2))
        return math.hypot(px-ax-t*dx, py-ay-t*dy)
    def inter(a, b, c, d):
        def o(p, q, r): return (q[0]-p[0])*(r[1]-p[1]) - (q[1]-p[1])*(r[0]-p[0])
        return (o(a, b, c)*o(a, b, d) < 0) and (o(c, d, a)*o(c, d, b) < 0)
    if inter(p1, p2, q1, q2): return 0.0
    return min(dps(p1, q1, q2), dps(p2, q1, q2), dps(q1, p1, p2), dps(q2, p1, p2))
def rect_edges(r):
    x0, y0, x1, y1 = r
    return [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
def inside(p, r): return r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]
def dist(a, b):
    ka, kb = a['k'], b['k']; ga, gb = a['g'], b['g']
    if ka == 'circ' and kb == 'circ': return math.hypot(ga[0]-gb[0], ga[1]-gb[1]) - ga[2] - gb[2]
    if ka == 'seg' and kb == 'seg': return seg_seg(ga[:2], ga[2:4], gb[:2], gb[2:4]) - ga[4] - gb[4]
    if ka == 'rect' and kb == 'rect':
        dx = max(gb[0]-ga[2], ga[0]-gb[2], 0); dy = max(gb[1]-ga[3], ga[1]-gb[3], 0)
        return math.hypot(dx, dy) if (dx or dy) else -1
    # mixed: order so that rect (if any) is b, and circ before seg
    if ka == 'rect' or (ka == 'seg' and kb == 'circ'): a, b = b, a; ka, kb = kb, ka; ga, gb = gb, ga
    if ka == 'circ' and kb == 'seg': return seg_seg(ga[:2], ga[:2], gb[:2], gb[2:4]) - ga[2] - gb[4]
    if kb == 'rect':
        if ka == 'circ':
            p, rr = ga[:2], ga[2]
            if inside(p, gb): return -1
            return min(seg_seg(p, p, e0, e1) for e0, e1 in rect_edges(gb)) - rr
        p1, p2, rr = ga[:2], ga[2:4], ga[4]
        if inside(p1, gb) or inside(p2, gb): return -1
        return min(seg_seg(p1, p2, e0, e1) for e0, e1 in rect_edges(gb)) - rr
    raise ValueError((ka, kb))

bad = []
allnew = new
for i, a in enumerate(allnew):
    for b in keep + allnew[i+1:]:
        if not (a['L'] & b['L']): continue
        if a['net'] and a['net'] == b['net']: continue
        need = 0.2 if 'GND' in (a['net'], b['net']) else 0.15
        d = dist(a, b)
        if d < need: bad.append((round(d, 3), a['tag'], a['net'], b['tag'], b['net']))
# edge clearance (left edge x=21.098)
for a in allnew:
    g = a['g']
    xmin = g[0] if a['k'] == 'rect' else (g[0]-g[2] if a['k'] == 'circ' else min(g[0], g[2]) - g[4])
    if xmin - 21.098 < 0.3: bad.append(('edge', a['tag'], a['net'], round(xmin-21.098, 2)))
# courtyards vs existing footprint bboxes + J11 + housing
fps = json.load(open('/tmp/place/fps.json'))
crt = {}
for ref, (X, Y, A) in P.items():
    hx, hy = CRT[ref]
    if abs(A % 180 - 90) < 1: hx, hy = hy, hx
    crt[ref] = (X-hx, Y-hy, X+hx, Y+hy)
for ref, r in crt.items():
    for f in fps:
        if f['ref'] in P or f['ref'] in ('J11', 'J16'): continue
        b = f['bbox']
        if f['layer'] != 'F.Cu' or f['src'] != 'crt': continue
        if r[0] < b[2] and r[2] > b[0] and r[1] < b[3] and r[3] > b[1]: bad.append(('courtyard', ref, f['ref']))
    # J11 courtyard circle
    cx, cy, R = 26.09832, 16.80534, 4.75
    nx, ny = min(max(cx, r[0]), r[2]), min(max(cy, r[1]), r[3])
    if math.hypot(nx-cx, ny-cy) < R: bad.append(('J11', ref))
    if r[2] > 33.1 and r[1] < 26.4: bad.append(('housing', ref))
for a in crt:
    for b in crt:
        if a < b:
            r, q = crt[a], crt[b]
            if r[0] < q[2] and r[2] > q[0] and r[1] < q[3] and r[3] > q[1]: bad.append(('courtyard', a, b))
# case keep-clear frame: left strip x<23.26 (y 23.6..91.8) and top-left corner above y 23.575 (x<32.76)
for a in allnew:
    if a['net'] == 'GND' and a['k'] != 'rect': pass
    g = a['g']
    if a['k'] == 'rect': xmin, ymin = g[0], g[1]
    elif a['k'] == 'circ': xmin, ymin = g[0]-g[2], g[1]-g[2]
    else: xmin, ymin = min(g[0], g[2])-g[4], min(g[1], g[3])-g[4]
    if xmin < 23.26 and ymin < 91.8: bad.append(('in left keep-clear strip', a['tag'], a['net'], round(xmin, 2)))
    if ymin < 23.575 and xmin < 32.76 and not (a['net'] == '+12V'): bad.append(('above top frame line', a['tag'], a['net'], round(ymin, 2)))
for ref, r in crt.items():
    if r[0] < 23.26 or (r[1] < 23.575 and r[0] < 32.76): bad.append(('courtyard crosses frame', ref, [round(v, 2) for v in r]))
print('pads:', json.dumps(padpos))
print('courtyards:', {k: [round(v, 2) for v in r] for k, r in crt.items()})
print('removed:', [(it['net'], it['tag'], [round(v, 2) for v in it['g']]) for it in removed])
print('VIOLATIONS:', len(bad))
for b in bad: print('  ', b)
json.dump(dict(P=P, padpos=padpos, crt=crt, T=T, V=V, removed=[(it['net'], it['tag'], it['k'], it['g']) for it in removed]), open('/tmp/place/plan.json', 'w'))
