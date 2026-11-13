#!/usr/bin/env python3
"""Convert a KiCad 10 Excellon file (METRIC or INCH, decimal, routed slots) to the format
the hellen-one gerbmerge expects (INCH,TZ 2:4 leading-zero suppressed, G85 slots)."""
import re, sys
src, dst = sys.argv[1], sys.argv[2]
L = open(src).read().splitlines()
metric = 'METRIC' in L
assert metric or 'INCH' in L, 'unknown units'
inch = (lambda mm: mm / 25.4) if metric else (lambda v: v)
co = lambda v: str(int(round(inch(float(v)) * 10000)))
out = []; header = True; route = None; last = (None, None)
for l in L:
    if header:
        if l.startswith('; FORMAT='):
            out.append('; FORMAT={2:4/ absolute / inch / suppress leading zeros}'); continue
        if l in ('METRIC', 'INCH'): out.append('INCH,TZ'); continue
        m = re.match(r'^T(\d+)C([\d.]+)$', l)
        if m: out.append(f'T{m.group(1)}C{inch(float(m.group(2))):.4f}'); continue
        out.append(l)
        if l == '%': header = False
        continue
    m = re.match(r'^(G00|G01)?X([-\d.]+)Y([-\d.]+)$', l)
    if m:
        g, x, y = m.groups()
        if g == 'G00': route = [(x, y)]; continue
        if g == 'G01':
            assert route is not None and len(route) == 1, 'multi-segment route not supported'
            route.append((x, y)); continue
        out.append(f'X{co(x)}Y{co(y)}'); continue
    if l == 'M15': assert route and len(route) == 1; continue
    if l == 'M16':
        (x1, y1), (x2, y2) = route
        out.append(f'X{co(x1)}Y{co(y1)}G85X{co(x2)}Y{co(y2)}'); route = None; continue
    if l == 'M30': out += ['T0', 'M30']; continue
    if re.match(r'^(T\d+|G05|G90|;.*)$', l): out.append(l); continue
    raise SystemExit(f'unhandled line: {l!r}')
open(dst, 'w').write('\n'.join(out) + '\n')
print('ok', len(out), 'lines')
