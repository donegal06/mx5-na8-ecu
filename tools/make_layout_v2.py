#!/usr/bin/env python3
"""Derive tools/layout_rp_stage_v2.py from v1: placement inside the case keep-clear
frame, TVS fed from the bottom layer, extra via removal, duplicate USB vias removed,
rusEFI URL text shrunk/moved."""
REPO = '/home/claude/mx5-na8-ecu'
v1 = open(f'{REPO}/tools/layout_rp_stage.py').read()
v2 = v1.replace('"""Lay out the reverse-polarity stage',
                '"""(v2: everything inside the case keep-clear silkscreen frame) Lay out the reverse-polarity stage')
old_vias = "for x, y in [('28.3', '25.4'), ('30.34832', '28.13034'), ('33.22332', '39.70034')]:"
assert old_vias in v2
v2 = v2.replace(old_vias, "for x, y in [('28.3', '25.4'), ('30.34832', '28.13034'), ('33.22332', '39.70034'), ('23.5', '41.5')]:")
a = v2.index("track('/1B', 'F', 2, [(37.0893, 28.62534)")
b = v2.index("# ------------------------------------------------------------------ footprints")
routing = r'''track('/1B', 'F', 1.6, [(37.0893, 28.62534), (36.0, 25.65), (29.8, 25.65), (29.22, 26.9)])  # pin 1B -> Q901 S, over G
track('/1B', 'F', 1.6, [(29.8, 25.65), (26.2, 25.65)])                                     # TVS feed vias
track('/1B', 'F', 0.4, [(26.5, 27.2), (28.7, 27.2)])                                       # C901.2 -> S
track('/1B', 'F', 0.3, [(27.5, 28.9), (28.8, 28.6)])                                       # ANODE -> S
track('/1B', 'F', 0.2, [(24.7625, 30.8), (25.9, 30.8), (25.9, 28.9), (26.7, 28.9)])       # EN -> ANODE
track('/RP_VCAP', 'F', 0.3, [(24.51, 27.2), (24.7625, 28.9)])
track('/RP_GATE', 'F', 0.3, [(27.6, 29.85), (33.2, 29.85), (33.78, 29.3), (33.78, 28.6)]) # GATE under Q901
track('/1B_PROT', 'F', 0.3, [(27.6, 30.8), (28.2, 31.3), (28.9, 31.3)])                   # CATHODE -> tab
track('/1B_PROT', 'F', 2, [(31.5, 35.6), (43.2, 35.6)])                                    # tab -> F3.1
track('/1B_PROT', 'F', 2, [(42.7, 35.6), (42.7, 38.3)])                                    # -> F1.1
track('/1B_PROT', 'F', 2, [(38.03, 35.6), (38.03, 38.0)])                                  # -> F2.2
track('/1B', 'B', 2, [(27.5, 25.65), (26.5, 26.65), (26.5, 38.4), (25.2, 38.9)])           # TVS feed, bottom
track('/1B', 'B', 2, [(24.3, 38.9), (26.1, 38.9)])
track('/1B', 'F', 2, [(24.3, 38.9), (26.1, 38.9)])
track('/1B', 'F', 2, [(25.2, 38.9), (25.2, 40.5)])                                         # into D901.1
track('GND', 'F', 0.3, [(24.7625, 29.85), (23.75, 29.85)])                                 # U901 GND -> via
track('GND', 'F', 1, [(31.0, 38.9), (32.0, 38.9)])                                         # D901.2 vias
track('GND', 'F', 1, [(31.5, 38.9), (31.5, 40.5)])
track('/2D', 'F', 2, [(38.8, 26.00534), (52.24832, 26.00534)])                             # 2D resumes on top
track('/2D', 'B', 1.5, [(38.8, 26.00534), (35.0, 26.0), (34.2, 26.8), (34.2, 37.6), (34.13, 38.3)])  # to F2.1 hole
for net, x, y in [('/2D', 38.8, 26.00534), ('+12V', 29.35, 43.45), ('+12V', 33.75, 20.15),
                  ('/1B', 26.6, 25.65), ('/1B', 27.5, 25.65), ('/1B', 28.4, 25.65),
                  ('/1B', 24.3, 38.9), ('/1B', 25.2, 38.9), ('/1B', 26.1, 38.9),
                  ('GND', 23.75, 29.85), ('GND', 31.0, 38.9), ('GND', 32.0, 38.9)]:
    via(net, x, y)

# duplicate USB vias (two pairs drilled twice in the original frame)
for t in ('bd4bb794-59a1-45ee-bdec-f65e015bce6a', 'a91075ae-ce17-4579-b820-8a9307ee22af'):
    drop(r'\n  \(via [^\n]*\(tstamp %s\)\)' % t, 1)
# rusEFI URL on F.SilkS: 2 mm -> 1.5 mm, centre y 62.1 -> 67.0 so it clears Q901/D901
old_url = '(gr_text "http://rusefi.com/s/hellenNA6" (at 31.84832 62.10534 90) (layer "F.SilkS")'
old_eff = '(effects (font (size 2 2) (thickness 0.25)))'
assert s.count(old_url) == 1
i = s.index(old_url); j = s.index(old_eff, i)
assert j - i < 200
s = (s[:i] + old_url.replace('62.10534', '67.0') + s[i + len(old_url):j]
     + '(effects (font (size 1.5 1.5) (thickness 0.2)))' + s[j + len(old_eff):])

'''
v2 = v2[:a] + routing + v2[b:]
old_place = """PLACE = {'D901': (27.6, 25.5, 180, (27.6, 25.5)), 'Q901': (29.7, 34.5, 270, (29.7, 31.3)),
         'U901': (24.1, 32.4, 0, (24.1, 35.0)), 'C901': (23.8, 29.75, 0, (23.8, 28.55))}"""
assert old_place in v2
v2 = v2.replace(old_place, """PLACE = {'D901': (28.35, 41.3, 0, (28.35, 41.3)), 'Q901': (31.5, 31.95, 270, (31.5, 29.85)),
         'U901': (25.9, 29.85, 0, (25.9, 32.3)), 'C901': (25.3, 27.2, 0, (25.3, 24.3))}""")
open(f'{REPO}/tools/layout_rp_stage_v2.py', 'w').write(v2)
print('written')
