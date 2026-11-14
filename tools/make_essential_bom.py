#!/usr/bin/env python3
"""Make the 'essential' JLC BOM from the CI-generated BOM: same board, but leave off the
on-board wideband (wbo module), the electronic-throttle H-bridge U5 and the SD card.
The CPL file is unchanged; JLC just reports the dropped designators as not in the BOM."""
import csv, re, sys
src = sys.argv[1] if len(sys.argv) > 1 else 'boards/hellen64_NA6_94-d/board/hellen64_NA6_94-d-BOM.csv'
dst = sys.argv[2] if len(sys.argv) > 2 else 'jlc-essential/hellen64_NA6_94-d-BOM-essential.csv'
def dropped(ref):
    if re.fullmatch(r'(C6(0\d|1[0-6])|D60[0-3]|R6([01]\d|2[0-8])|U60[0-4]|Q60[01])', ref): return 'wideband'
    if ref == 'U5': return 'ETB H-bridge'
    if ref in ('J450', 'C450', 'C451', 'R450'): return 'SD card'
    return None
rows = list(csv.reader(open(src)))
out = [rows[0]]; gone = {}; types_before = types_after = 0
for r in rows[1:]:
    refs = [x.strip() for x in r[1].split(',')]
    keep = [x for x in refs if not dropped(x)]
    for x in refs:
        if dropped(x): gone.setdefault(dropped(x), []).append(x)
    if len(r) > 3 and r[3]: types_before += 1
    if keep:
        out.append([r[0], ', '.join(keep)] + r[2:])
        if len(r) > 3 and r[3]: types_after += 1
csv.writer(open(dst, 'w', newline=''), quoting=csv.QUOTE_ALL).writerows(out)
for k, v in gone.items(): print(k, len(v), ' '.join(v))
print('part types', types_before, '->', types_after)
