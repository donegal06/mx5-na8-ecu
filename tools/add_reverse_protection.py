"""
Insert an ideal-diode reverse-polarity stage on ECU pin 1B in the Hellen NA6/94
schematic (KiCad 6 format):

  1B (connector) --+-- D901 SMCJ33CA (bidir TVS) -- GND
                   |
                   +-- Q901 NCEP078N10AK source / U901 LM74700 ANODE + EN
  Q901 drain / U901 CATHODE --> 1B_PROT --> F1, F2, F3 (all existing fuses)
  U901 GATE -> Q901 gate, U901 VCAP -- C901 100n -- 1B (VCAP to ANODE)

The connector wire to the fuses is split; the connector side keeps label 1B,
the fuse side (and the F2 label) become 1B_PROT. New parts are connected with
local labels placed exactly on pin endpoints.

Usage: python3 add_reverse_protection.py <path/to/hellen64_NA6_94.kicad_sch>
"""
import re, sys, uuid

path = sys.argv[1]
s = open(path).read()
U = lambda: str(uuid.uuid4())
EFF = '(effects (font (size 1.27 1.27)))'
EFFH = '(effects (font (size 1.27 1.27)) hide)'

def pin(ptype, x, y, ang, length, name, num):
    return (f'        (pin {ptype} line (at {x} {y} {ang}) (length {length})\n'
            f'          (name "{name}" {EFF})\n'
            f'          (number "{num}" {EFF})\n        )\n')

def poly(points, width=0.254, fill='none'):
    pts = ' '.join(f'(xy {x} {y})' for x, y in points)
    return (f'        (polyline (pts {pts})\n'
            f'          (stroke (width {width}) (type default) (color 0 0 0 0))\n'
            f'          (fill (type {fill}))\n        )\n')

def libsym(full, short, ref, val, graphics, pins, extra=''):
    return (f'    (symbol "{full}" {extra}(in_bom yes) (on_board yes)\n'
            f'      (property "Reference" "{ref}" (id 0) (at 0 8.89 0)\n        {EFF}\n      )\n'
            f'      (property "Value" "{val}" (id 1) (at 0 -10.16 0)\n        {EFF}\n      )\n'
            f'      (property "Footprint" "" (id 2) (at 0 0 0)\n        {EFFH}\n      )\n'
            f'      (property "Datasheet" "" (id 3) (at 0 0 0)\n        {EFFH}\n      )\n'
            f'      (symbol "{short}_0_1"\n{graphics}      )\n'
            f'      (symbol "{short}_1_1"\n{pins}      )\n    )\n')

# ---------------------------------------------------------------- library symbols
LM_PINS = {  # number: (name, type, x, y, angle)
    '6': ('ANODE', 'power_in', -10.16, 2.54, 0),
    '3': ('EN', 'input', -10.16, -2.54, 0),
    '4': ('CATHODE', 'power_in', 10.16, 2.54, 180),
    '5': ('GATE', 'output', 10.16, 0, 180),
    '1': ('VCAP', 'passive', 10.16, -2.54, 180),
    '2': ('GND', 'power_in', 0, -7.62, 90),
}
lm = libsym('mx5:LM74700', 'LM74700', 'U', 'LM74700',
            '        (rectangle (start -7.62 5.08) (end 7.62 -5.08)\n'
            '          (stroke (width 0.254) (type default) (color 0 0 0 0))\n'
            '          (fill (type background))\n        )\n',
            ''.join(pin(t, x, y, a, 2.54, n, k) for k, (n, t, x, y, a) in LM_PINS.items()))

Q_PINS = {'1': ('G', -5.08, 0, 0), '2': ('D', 2.54, 5.08, 270), '3': ('S', 2.54, -5.08, 90)}
qg = (poly([(-2.54, 0), (0.254, 0)]) + poly([(0.254, 1.905), (0.254, -1.905)]) +
      poly([(0.762, 2.286), (0.762, -2.286)], 0.508) +
      poly([(0.762, 1.524), (2.54, 1.524), (2.54, 2.54)]) +
      poly([(0.762, -1.524), (2.54, -1.524), (2.54, -2.54)]) +
      poly([(0.762, 0), (2.54, 0), (2.54, -1.524)]))
q = libsym('mx5:Q_NMOS_GDS', 'Q_NMOS_GDS', 'Q', 'Q_NMOS_GDS', qg,
           ''.join(pin('passive', x, y, a, 2.54, n, k) for k, (n, x, y, a) in Q_PINS.items()),
           '(pin_names (offset 0) hide) ')

tg = (poly([(-2.54, 1.27), (-2.54, -1.27), (0, 0), (-2.54, 1.27)]) +
      poly([(2.54, 1.27), (2.54, -1.27), (0, 0), (2.54, 1.27)]) +
      poly([(-0.508, 1.778), (0, 1.27), (0, -1.27), (0.508, -1.778)]))
tvs = libsym('mx5:D_TVS_Bidir', 'D_TVS_Bidir', 'D', 'D_TVS_Bidir', tg,
             pin('passive', -5.08, 0, 0, 2.54, 'A1', '1') + pin('passive', 5.08, 0, 180, 2.54, 'A2', '2'),
             '(pin_numbers hide) (pin_names (offset 0) hide) ')

ls_end = s.find('\n  )\n', s.find('(lib_symbols'))
assert 'mx5:LM74700' not in s, 'already applied'
s = s[:ls_end] + '\n' + lm + q + tvs.rstrip('\n') + s[ls_end:]

# ---------------------------------------------------------------- split the 1B wire
old_wire = re.search(r'\n  \(wire \(pts \(xy 118\.11 199\.39\) \(xy 93\.98 199\.39\)\)\n.*?\n  \)\n', s, re.S)
assert old_wire, 'connector wire not found'
def wire(x1, y1, x2, y2):
    return (f'\n  (wire (pts (xy {x1} {y1}) (xy {x2} {y2}))\n'
            f'    (stroke (width 0) (type solid) (color 0 0 0 0))\n    (uuid {U()})\n  )\n')
s = s[:old_wire.start()] + wire(93.98, 199.39, 101.6, 199.39) + wire(106.68, 199.39, 118.11, 199.39) + s[old_wire.end():]

def label(text, x, y, ang):
    just = 'right bottom' if ang == 180 else 'left bottom'
    return (f'\n  (label "{text}" (at {x} {y} {ang})\n'
            f'    (effects (font (size 1.27 1.27)) (justify {just}))\n    (uuid {U()})\n  )\n')

# existing label 1B on that wire -> move to the connector-side wire end
m = re.search(r'\n  \(label "1B" \(at 104\.14 199\.39 0\)\n.*?\n  \)\n', s, re.S)
assert m
s = s[:m.start()] + label('1B', 101.6, 199.39, 180) + label('1B_PROT', 106.68, 199.39, 0) + s[m.end():]
# F2-side label 1B -> 1B_PROT (wideband heater feed is protected too)
n_before = s.count('(label "1B" (at 124.46 55.88 180)')
assert n_before == 1
s = s.replace('(label "1B" (at 124.46 55.88 180)', '(label "1B_PROT" (at 124.46 55.88 180)')

# ---------------------------------------------------------------- instances
inst = []
paths = []

def place(lib, ref, val, fp, lcsc, x, y, pins, extra_props=''):
    uid = U()
    pin_s = ''.join(f'    (pin "{p}" (uuid {U()}))\n' for p in pins)
    inst.append(
        f'\n  (symbol (lib_id "{lib}") (at {x} {y} 0) (unit 1)\n'
        f'    (in_bom yes) (on_board yes)\n    (uuid {uid})\n'
        f'    (property "Reference" "{ref}" (id 0) (at {x} {round(y - 8.89, 2)} 0)\n      {EFF}\n    )\n'
        f'    (property "Value" "{val}" (id 1) (at {x} {round(y + 10.16, 2)} 0)\n      {EFF}\n    )\n'
        f'    (property "Footprint" "{fp}" (id 2) (at {x} {y} 0)\n      {EFFH}\n    )\n'
        f'    (property "Datasheet" "" (id 3) (at {x} {y} 0)\n      {EFFH}\n    )\n'
        f'    (property "LCSC" "{lcsc}" (id 4) (at {x} {y} 0)\n      {EFFH}\n    )\n'
        f'{pin_s}  )\n')
    paths.append(f'    (path "/{uid}"\n      (reference "{ref}") (unit 1) (value "{val}") (footprint "{fp}")\n    )\n')

def gnd(ref, x, y):
    uid = U()
    inst.append(
        f'\n  (symbol (lib_id "power:GND") (at {x} {y} 0) (unit 1)\n'
        f'    (in_bom yes) (on_board yes)\n    (uuid {uid})\n'
        f'    (property "Reference" "{ref}" (id 0) (at {x} {round(y + 6.35, 2)} 0)\n      {EFFH}\n    )\n'
        f'    (property "Value" "GND" (id 1) (at {x} {round(y + 3.81, 2)} 0)\n      {EFF}\n    )\n'
        f'    (property "Footprint" "" (id 2) (at {x} {y} 0)\n      {EFFH}\n    )\n'
        f'    (property "Datasheet" "" (id 3) (at {x} {y} 0)\n      {EFFH}\n    )\n'
        f'    (pin "1" (uuid {U()}))\n  )\n')
    paths.append(f'    (path "/{uid}"\n      (reference "{ref}") (unit 1) (value "GND") (footprint "")\n    )\n')

labels = []
def lab(text, x, y, ang=0):
    labels.append(label(text, round(x, 2), round(y, 2), ang))

# U901 LM74700 at (50.8, 139.7); schematic pin = (X + px, Y - py)
UX, UY = 50.8, 139.7
place('mx5:LM74700', 'U901', 'LM74700QDBVRQ1', 'Package_TO_SOT_SMD:SOT-23-6', 'C2941042', UX, UY, list(LM_PINS))
lab('1B', UX - 10.16, UY - 2.54, 180)          # ANODE
lab('1B', UX - 10.16, UY + 2.54, 180)          # EN (always on)
lab('1B_PROT', UX + 10.16, UY - 2.54, 0)       # CATHODE
lab('RP_GATE', UX + 10.16, UY, 0)              # GATE
lab('RP_VCAP', UX + 10.16, UY + 2.54, 0)       # VCAP
gnd('#PWR0901', UX, UY + 7.62)                 # GND

# Q901 N-MOSFET at (50.8, 121.92): G (-5.08,0), D (2.54,5.08), S (2.54,-5.08)
QX, QY = 50.8, 121.92
place('mx5:Q_NMOS_GDS', 'Q901', 'NCEP078N10AK', 'Package_TO_SOT_SMD:TO-252-2', 'C2686699', QX, QY, list(Q_PINS))
lab('RP_GATE', QX - 5.08, QY, 180)
lab('1B_PROT', QX + 2.54, QY - 5.08, 0)        # drain -> output
lab('1B', QX + 2.54, QY + 5.08, 0)             # source -> input

# C901 100n VCAP-ANODE at (71.12, 139.7): pin1 (0,3.81) pin2 (0,-3.81)
CX, CY = 71.12, 139.7
place('Device:C', 'C901', '100n 50V', 'hellen-one-common:C0603', 'C14663', CX, CY, ['1', '2'])
lab('RP_VCAP', CX, CY - 3.81, 0)
lab('1B', CX, CY + 3.81, 0)

# D901 SMCJ33CA bidirectional TVS 1B-GND at (30.48, 121.92): pins at x-5.08 / x+5.08
DX, DY = 30.48, 121.92
place('mx5:D_TVS_Bidir', 'D901', 'SMCJ33CA', 'Diode_SMD:D_SMC', 'C699040', DX, DY, ['1', '2'])
lab('1B', DX - 5.08, DY, 180)
gnd('#PWR0902', DX + 5.08, DY)

# note text
note = (f'\n  (text "Reverse-polarity + transient protection (MX-5 fork).\\n'
        f'Ideal diode on 1B ahead of fuses F1-F3; bidirectional TVS on the input.\\n'
        f'See bom_replace for D418/U420/D420/F410 changes."\n'
        f'    (at 25.4 106.68 0)\n    (effects (font (size 1.27 1.27)) (justify left bottom))\n    (uuid {U()})\n  )\n')

si = s.find('\n  (symbol_instances')
assert si > 0
s = s[:si] + ''.join(inst) + ''.join(labels) + note + s[si:]
pi = s.find('(symbol_instances') + len('(symbol_instances')
s = s[:pi] + '\n' + ''.join(paths).rstrip('\n') + s[pi:]

open(path, 'w').write(s)
print('ok: added', len(inst), 'symbols,', len(labels), 'labels')
