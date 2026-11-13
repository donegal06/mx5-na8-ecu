#!/usr/bin/env python3
"""Cosmetic tidy of the reverse-polarity block in the schematic (no net changes):
- LM74700 symbol: CATHODE and GATE swap rows so ANODE/CATHODE names don't collide;
  the two net labels on those pins swap with them (pin numbers/nets unchanged).
- Q901 reference/value and U901 value moved clear of each other."""
import re
p = 'hellen64_NA6_94.kicad_sch'
s = open(p).read()
# 1) symbol pins: CATHODE (4) at (10.16, 2.54) <-> GATE (5) at (10.16, 0)
a = '(pin power_in line (at 10.16 2.54 180) (length 2.54)\n          (name "CATHODE"'
b = '(pin output line (at 10.16 0 180) (length 2.54)\n          (name "GATE"'
assert s.count(a) == 1 and s.count(b) == 1
s = s.replace(a, '(pin power_in line (at 10.16 0 180) (length 2.54)\n          (name "CATHODE"')
s = s.replace(b, '(pin output line (at 10.16 2.54 180) (length 2.54)\n          (name "GATE"')
# labels on U901's right side (UX+10.16 = 60.96): y 137.16 = old CATHODE row, y 139.7 = old GATE row
la = '(label "1B_PROT" (at 60.96 137.16 0)'
lb = '(label "RP_GATE" (at 60.96 139.7 0)'
assert s.count(la) == 1 and s.count(lb) == 1
s = s.replace(la, '(label "RP_GATE" (at 60.96 137.16 0)').replace(lb, '(label "1B_PROT" (at 60.96 139.7 0)')
# 2) text positions
def move_prop(ref, prop, val, at, justify_left=True):
    global s
    i = s.find(f'(property "Reference" "{ref}"'); st = s.rfind('\n  (symbol (lib_id', 0, i)
    en = s.find('(pin "', i)
    blk = s[st:en]
    m = re.search(r'\(property "%s" "%s" \(id (\d)\) \(at [-\d. ]+\)\n      \(effects \(font \(size ([\d.]+) ([\d.]+)\)\)\)' % (prop, re.escape(val)), blk)
    assert m, (ref, prop)
    new = (f'(property "{prop}" "{val}" (id {m.group(1)}) (at {at[0]} {at[1]} 0)\n'
           f'      (effects (font (size {m.group(2)} {m.group(3)})){" (justify left)" if justify_left else ""})')
    s = s[:st] + blk[:m.start()] + new + blk[m.end():] + s[en:]
move_prop('Q901', 'Reference', 'Q901', (55.88, 120.65))
move_prop('Q901', 'Value', 'NCEP078N10AK', (55.88, 123.19))
move_prop('U901', 'Value', 'LM74700QDBVRQ1', (55.88, 147.32))
d = 0
for c in s:
    d += (c == '(') - (c == ')'); assert d >= 0
assert d == 0
open(p, 'w').write(s)
print('ok')
