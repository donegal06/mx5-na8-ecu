import re, math, sys, collections
src=open('/home/claude/tools/plan_1b_layout.py').read().split('# ---------------------------------------------------------------- plan')[0]
geo=open('/home/claude/tools/plan_1b_layout.py').read().split('# ---------------------------------------------------------------- geometry')[1].split('bad = []')[0]
g={}; sys.argv=['x',sys.argv[1] if len(sys.argv)>1 else 'hellen64_NA6_94.kicad_pcb']; exec(src,g); exec(geo,g)
items, dist = g['items'], g['dist']
def bbox(it):
    k,q=it['k'],it['g']
    if k=='rect': return q
    if k=='circ': return (q[0]-q[2],q[1]-q[2],q[0]+q[2],q[1]+q[2])
    return (min(q[0],q[2])-q[4],min(q[1],q[3])-q[4],max(q[0],q[2])+q[4],max(q[1],q[3])+q[4])
R=(20,17,50,48)
reg=[it for it in items if (lambda b: b[0]<R[2] and b[2]>R[0] and b[1]<R[3] and b[3]>R[1])(bbox(it))]
print('items in region:', len(reg))
bad=[]
for i,a in enumerate(reg):
    ba=bbox(a)
    for b in reg[i+1:]:
        if not (a['L'] & b['L']): continue
        if a['net'] and a['net']==b['net']: continue
        bb=bbox(b)
        if ba[0]>bb[2]+1 or bb[0]>ba[2]+1 or ba[1]>bb[3]+1 or bb[1]>ba[3]+1: continue
        need = 0.2 if 'GND' in (a['net'],b['net']) else 0.15
        d=dist(a,b)
        if d<need-0.001: bad.append((round(d,3),a['tag'],a['net'],b['tag'],b['net'],[round(v,2) for v in a['g'][:2]]))
print('clearance violations in region:', len(bad))
for x in bad[:30]: print('  ',x)
# connectivity
par={}
def f(x):
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
want=['/1B','/1B_PROT','/RP_GATE','/RP_VCAP','/2D','+12V']
for net in want:
    its=[it for it in items if it['net']==net]
    for i in range(len(its)): par[i]=i
    for i,a in enumerate(its):
        for j in range(i+1,len(its)):
            b=its[j]
            if a['L'] & b['L'] and dist(a,b)<=0.001: par[f(i)]=f(j)
    comps=collections.defaultdict(list)
    for i,it in enumerate(its): comps[f(i)].append(it['tag'])
    groups=[sorted(set(t for t in v if t not in('trk','via','new trk'))) for v in comps.values()]
    groups=[x for x in groups if x] + [['(tracks only: %d)'%len(v)] for v in comps.values() if all(t in('trk','via') for t in v)]
    print(net, 'components:', len(comps)); [print('    ',x[:14]) for x in groups]
    par.clear()
