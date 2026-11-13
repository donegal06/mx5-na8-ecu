#!/usr/bin/env python3
"""Coil-on-plug option links for the Hellen64 NA6/94 frame schematic.

Adds two 0805 link footprints (Hellen 'Jumper-Pad-Pad', same as R34/R58):
  R902  OUT_IGN3 -> connector 1T  (P16 pad, empty cavity on non-US manual 94-95)
  R903  OUT_IGN4 -> connector 1U  (P15 pad, empty cavity on non-US manual 94-95)
Both are left unfitted via bom_replace, so the default build is unchanged.
Also names the previously anonymous 1T net (label on the P16 wire).

KiCad 6 (20211123) S-expression edit; run from the repo root.
"""
import re
import sys
import uuid

path = sys.argv[1] if len(sys.argv) > 1 else 'hellen64_NA6_94.kicad_sch'
s = open(path).read()
assert '(reference "R902")' not in s, 'already applied'
assert '(label "1T"' not in s, '1T label already exists'

U = lambda: str(uuid.uuid4())
EFF = '(effects (font (size 1.016 1.016)))'
EFFH = '(effects (font (size 1.524 1.524)) hide)'


def label(text, x, y, ang):
    just = 'right bottom' if ang == 180 else 'left bottom'
    return (f'\n  (label "{text}" (at {x} {y} {ang})\n'
            f'    (effects (font (size 1.27 1.27)) (justify {just}))\n    (uuid {U()})\n  )\n')


inst, paths, labels = [], [], []


def jumper(ref, x, y, net1, net2):
    """Jumper-Pad-Pad: pin1 at (x-5.08, y), pin2 at (x+5.08, y) when unrotated."""
    uid = U()
    fp = 'hellen-one-common:PAD-0805-PAD'
    inst.append(
        f'\n  (symbol (lib_id "hellen-one-common:Jumper-Pad-Pad") (at {x} {y} 0) (unit 1)\n'
        f'    (in_bom yes) (on_board yes)\n    (uuid {uid})\n'
        f'    (property "Reference" "{ref}" (id 0) (at {x} {round(y - 1.905, 3)} 0)\n      {EFF}\n    )\n'
        f'    (property "Value" "Jumper-Pad-Pad" (id 1) (at {x} {round(y + 1.778, 3)} 0)\n      {EFF.replace(")))", ")) hide)")}\n    )\n'
        f'    (property "Footprint" "{fp}" (id 2) (at {x} {round(y + 3.81, 3)} 0)\n      {EFFH}\n    )\n'
        f'    (property "Datasheet" "" (id 3) (at {x} {y} 0)\n      {EFFH}\n    )\n'
        f'    (property "LCSC" "C17477" (id 4) (at {x} {y} 0)\n      {EFFH}\n    )\n'
        f'    (property "MyCommnet" "DNP" (id 5) (at {x} {y} 0)\n      {EFFH}\n    )\n'
        f'    (pin "1" (uuid {U()}))\n    (pin "2" (uuid {U()}))\n  )\n')
    paths.append(f'    (path "/{uid}"\n      (reference "{ref}") (unit 1) (value "Jumper-Pad-Pad") (footprint "{fp}")\n    )\n')
    labels.append(label(net1, round(x - 5.08, 2), y, 180))
    labels.append(label(net2, round(x + 5.08, 2), y, 0))


# 1T: P16 pad wire runs (123.19,153.67)-(93.98,153.67); name it like 1U at x=104.14
assert '(wire (pts (xy 123.19 153.67) (xy 93.98 153.67))' in s
labels.append(label('1T', 104.14, 153.67, 0))
assert '(label "1U" (at 104.14 151.13 0)' in s

jumper('R902', 259.08, 96.52, 'OUT_IGN3', '1T')
jumper('R903', 259.08, 101.6, 'OUT_IGN4', '1U')

note = ('\n  (text "Coil-on-plug option (MX-5 fork): R902 links IGN3 to 1T, R903 links IGN4 to 1U.\\n'
        'Not fitted by default (bom_replace). 1T/1U are empty cavities on non-US manual 94-95 cars.\\n'
        'Fit 0R 0805 (or bridge) only when the coil harness uses those cavities."\n'
        f'    (at 241.3 91.44 0)\n    (effects (font (size 1.27 1.27)) (justify left bottom))\n    (uuid {U()})\n  )\n')

si = s.find('\n  (symbol_instances')
assert si > 0
s = s[:si] + ''.join(inst) + ''.join(labels) + note + s[si:]
pi = s.find('(symbol_instances') + len('(symbol_instances')
s = s[:pi] + '\n' + ''.join(paths).rstrip('\n') + s[pi:]

open(path, 'w').write(s)
print('ok: added', len(inst), 'symbols,', len(labels), 'labels')
