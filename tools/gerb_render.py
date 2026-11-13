#!/usr/bin/env python3
"""Minimal Gerber (KiCad RS-274X, mm, FSLAX46Y46) rasteriser for diffing layers.
Usage: gerb_render.py file.gbr out.png [px_per_mm] [xmin ymin xmax ymax] (gerber coords, mm)"""
import re, sys, math
from PIL import Image, ImageDraw
def render(path, ppm=20, box=(-5,-5,160,160)):
    x0,y0,x1,y1=box; W=int((x1-x0)*ppm); H=int((y1-y0)*ppm)
    img=Image.new('L',(W,H),0); d=ImageDraw.Draw(img)
    P=lambda x,y:((x-x0)*ppm,(y1-y)*ppm)
    txt=open(path).read()
    aps={}; cur=None; x=y=0.0; mode='G01'; region=None; pol=255; quad='G75'
    tokens=re.findall(r'%[^%]*%|[^*%\n]+\*',txt)
    def ap_draw(a,cx,cy):
        t,p=a
        if t=='C':
            r=p[0]/2*ppm; X,Y=P(cx,cy); d.ellipse([X-r,Y-r,X+r,Y+r],fill=pol)
        elif t=='R':
            w,h=p[0]/2,p[1]/2; d.rectangle([P(cx-w,cy+h),P(cx+w,cy-h)],fill=pol)
        elif t=='O':
            w,h=p[0],p[1]; r=min(w,h)/2
            if w>h:
                d.rectangle([P(cx-w/2+r,cy+r),P(cx+w/2-r,cy-r)],fill=pol)
                for ex in (cx-w/2+r,cx+w/2-r): X,Y=P(ex,cy); d.ellipse([X-r*ppm,Y-r*ppm,X+r*ppm,Y+r*ppm],fill=pol)
            else:
                d.rectangle([P(cx-r,cy+h/2-r),P(cx+r,cy-h/2+r)],fill=pol)
                for ey in (cy-h/2+r,cy+h/2-r): X,Y=P(cx,ey); d.ellipse([X-r*ppm,Y-r*ppm,X+r*ppm,Y+r*ppm],fill=pol)
        elif t=='P':
            dia,n=p[0],int(p[1]); rot=p[2] if len(p)>2 else 0
            pts=[P(cx+dia/2*math.cos(math.radians(rot+360*i/n)),cy+dia/2*math.sin(math.radians(rot+360*i/n))) for i in range(n)]
            d.polygon(pts,fill=pol)
        else: raise SystemExit('aperture '+t)
    def arcpts(xs,ys,xe,ye,i,j,cw):
        cx,cy=xs+i,ys+j; r=math.hypot(i,j)
        a0=math.atan2(ys-cy,xs-cx); a1=math.atan2(ye-cy,xe-cx)
        if cw:
            if a1>=a0: a1-=2*math.pi
        else:
            if a1<=a0: a1+=2*math.pi
        if abs(xs-xe)<1e-9 and abs(ys-ye)<1e-9: a1=a0+(-2*math.pi if cw else 2*math.pi)
        n=max(8,int(abs(a1-a0)*r*ppm/2)+2)
        return [(cx+r*math.cos(a0+(a1-a0)*k/n),cy+r*math.sin(a0+(a1-a0)*k/n)) for k in range(1,n+1)]
    def stroke(pts):
        a=aps[cur]
        if a[0]!='C': 
            for px,py in pts: ap_draw(a,px,py)
            return
        w=a[1][0]*ppm
        d.line([P(*q) for q in pts],fill=pol,width=max(1,int(round(w))))
        for q in pts: ap_draw(a,*q)
    for tk in tokens:
        if tk.startswith('%'):
            b=tk.strip('%').rstrip('*')
            m=re.match(r'ADD(\d+)([A-Z]+),([^*]*)',b)
            if m: aps[int(m[1])]=(m[2],[float(v) for v in m[3].split('X')]); continue
            if b.startswith('LPC'): pol=0
            elif b.startswith('LPD'): pol=255
            elif b.startswith('AM'): raise SystemExit('aperture macro present')
            continue
        s=tk.rstrip('*')
        if s.startswith('G04') or s=='' : continue
        for g in re.findall(r'G0?([0-9]+)',s.split('X')[0].split('Y')[0].split('D')[0] if not s.startswith(('X','Y','I','J','D')) else ''):
            g=int(g)
            if g in (1,2,3): mode=f'G0{g}'
            elif g==36: region=[]
            elif g==37:
                if region and len(region)>2: d.polygon([P(*q) for q in region],fill=pol)
                region=None
            elif g==75: quad='G75'
        m=re.match(r'^D(\d+)$',s) or re.match(r'^G54D(\d+)$',s)
        if m and int(m[1])>=10: cur=int(m[1]); continue
        m=re.match(r'^(?:G0([123]))?(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?D0([123])$',s)
        if not m: continue
        if m[1]: mode=f'G0{m[1]}'
        nx=int(m[2])/1e6 if m[2] else x; ny=int(m[3])/1e6 if m[3] else y
        i=int(m[4])/1e6 if m[4] else 0; j=int(m[5])/1e6 if m[5] else 0; op=int(m[6])
        if op==2:
            if region is not None:
                if len(region)>2: d.polygon([P(*q) for q in region],fill=pol)
                region=[(nx,ny)]
        elif op==1:
            pts=[(nx,ny)] if mode=='G01' else arcpts(x,y,nx,ny,i,j,mode=='G02')
            if region is not None:
                if not region: region=[(x,y)]
                region+=pts
            else: stroke([(x,y)]+pts)
        elif op==3: ap_draw(aps[cur],nx,ny)
        x,y=nx,ny
    return img
if __name__=='__main__':
    a=sys.argv; ppm=float(a[3]) if len(a)>3 else 20
    box=tuple(map(float,a[4:8])) if len(a)>7 else (-5,-5,160,160)
    render(a[1],ppm,box).save(a[2]); print('ok')
