#!/usr/bin/env python3
"""Generate the book's five static, accessible mathematical support diagrams."""
import argparse
import html
import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'book-src/figures'

def text(x, y, value, size=23, anchor='middle'):
    return f'<text x="{x:g}" y="{y:g}" font-size="{size}" text-anchor="{anchor}" font-family="Noto Sans CJK TC, PingFang TC, Microsoft JhengHei, sans-serif">{html.escape(value)}</text>'

def line(x1,y1,x2,y2,dash=''):
    return f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="black" stroke-width="2"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'

def polygon(points, opacity):
    return '<polygon points="'+' '.join(f'{x:g},{y:g}' for x,y in points)+f'" fill="black" fill-opacity="{opacity}" stroke="black" stroke-width="2"/>'

def arrow(x1,y,x2):
    sign=1 if x2>x1 else -1
    return line(x1,y,x2,y)+f'<polyline points="{x2-11*sign:g},{y-7:g} {x2:g},{y:g} {x2-11*sign:g},{y+7:g}" fill="none" stroke="black" stroke-width="2"/>'

def svg(title, desc, body, w=680,h=440):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">\n<title id="title">{html.escape(title)}</title>\n<desc id="desc">{html.escape(desc)}</desc>\n<rect width="{w}" height="{h}" fill="white"/>\n'+body+'\n</svg>\n'

def figures():
    result={}
    a=(200,260);b=(360,260);c=(280,260-80*math.sqrt(3));r=160
    assert all(abs(math.dist(p,q)-r)<1e-10 for p,q in [(a,b),(a,c),(b,c)])
    body=''
    for j,(x,y) in enumerate([a,b]):
        body+=f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="black" stroke-opacity="0.4" stroke-width="2"'+(' stroke-dasharray="8 5"' if j else '')+'/>'
    body+=polygon([a,b,c],0.07)
    for (x,y),label,dy in [(a,'A',30),(b,'B',30),(c,'C',-14)]:
        body+=f'<circle cx="{x:g}" cy="{y:g}" r="4"/>'+text(x,y+dy,label)
    body+=text(280,321,'AB = AC = BC',25)
    result['euclid-circles.svg']=svg('兩圓構造等邊三角形','兩圓中心為 A、B，半徑均為 AB。上交點是 C；交點存在性須由正文另外交代。',body,w=560,h=440)

    body=text(155,35,'切開',25)+text(490,35,'重新拼合',25)
    # Equal scale, with exact 12:21 and 6:21 dimensions.
    x,y,k=65,75,15
    body+=polygon([(x,y+21*k),(x+6*k,y+21*k),(x+6*k,y)],.14)
    body+=polygon([(x+6*k,y+21*k),(x+12*k,y+21*k),(x+6*k,y)],.42)
    body+=line(x+6*k,y,x+6*k,y+21*k,'6 5')
    body+=text(x+3*k,418,'6')+text(x+9*k,418,'6')+text(25,235,'21')
    x2=445
    body+=polygon([(x2,y),(x2,y+21*k),(x2+6*k,y+21*k)],.42)
    body+=polygon([(x2,y),(x2+6*k,y),(x2+6*k,y+21*k)],.14)
    body+=text(x2+3*k,418,'6')+text(x2+6*k+35,235,'21')+arrow(300,230,395)
    assert 12*21/2==6*21
    result['triangle-area.svg']=svg('同面積的切割與拼合','底 12 高 21 的等腰三角形沿高度切開。兩個直角三角形拼成寬 6 高 21 的長方形。兩圖使用相同比例。',body)

    body=text(290,35,'5 × 5 → 6 × 6',25)
    for row in range(6):
        for col in range(6):
            old=row<5 and col<5; x=120+48*col;y=78+48*row
            body+=f'<circle cx="{x}" cy="{y}" r="13" fill="black" fill-opacity="{0.18 if old else 0.88}"/>'
    body+='<circle cx="360" cy="318" r="22" fill="none" stroke="black" stroke-width="2" stroke-dasharray="4 3"/>'
    body+=text(290,389,'新增：6 + 6 − 1 = 11',26)
    body+=text(495,138,'原有 25 顆',23)+text(495,220,'新增 11 顆',23)+text(495,310,'角落算一次',23)
    assert sum(row==5 or col==5 for row in range(6) for col in range(6))==11
    result['odd-square.svg']=svg('正方形添邊','淡色 25 顆保留原正方形；下排和右排新增 11 顆。虛線圈標示只應計算一次的共用角落。',body)

    x0,y0,w,h=70,360,500,270
    body=line(x0,y0,x0+w+15,y0)+line(x0,y0,x0,y0-h-15)
    body+=line(x0,y0-h/2,x0+w,y0-h/2,'4 6')+text(35,y0-h/2+7,'1/2',20)
    body+=text(x0-15,y0+28,'0',20)+text(x0+w,y0+28,'1',20)+text(x0+w+25,y0+9,'x',22)
    body+=text(44,78,'y',22)
    dashes=['','10 5','2 5','12 4 2 4']
    for idx,n in enumerate([1,2,4,8]):
        points=[(x0+w*j/200,y0-h*(j/200)**n) for j in range(200)]
        body+='<polyline points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in points)+'" fill="none" stroke="black" stroke-width="2"'+(f' stroke-dasharray="{dashes[idx]}"' if dashes[idx] else '')+'/>'
        lx=80+idx*145
        body+=line(lx,36,lx+34,36,dashes[idx])+text(lx+43,43,f'n={n}',21,'start')
    body+=f'<circle cx="{x0+w}" cy="{y0-h}" r="5" fill="white" stroke="black" stroke-width="2"/>'
    result['powers-limit.svg']=svg('固定輸入與整段範圍','x、x²、x⁴、x⁸ 在零到一之間的曲線。越靠近一，各條曲線仍有高於二分之一的區域。右上空心點表示本節先不包含 x 等於一。',body)

    body=text(115,38,'證明者',25)+text(545,38,'驗證者',25)
    body+=line(115,60,115,350,'5 5')+line(545,60,545,350,'5 5')
    body+=arrow(115,115,545)+text(330,95,'① 先送出 H',24)
    body+=arrow(545,215,115)+text(330,195,'② 再隨機選 b',24)
    body+=arrow(115,315,545)+text(330,295,'③ 回覆對應 s',24)
    body+=text(330,401,'順序是健全性論證的一部分',23)
    result['protocol-order.svg']=svg('互動證明的訊息順序','先由證明者送 H；驗證者之後才隨機選 b；證明者最後送對應 s。這是現場互動，不是離線模擬器製造紀錄的順序。',body)
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');args=ap.parse_args()
    expected=figures()
    if args.check:
        for name,content in expected.items():
            if not (OUT/name).exists() or (OUT/name).read_text()!=content: raise SystemExit('Stale figure: '+name)
        print('PASS: five generated figures match their sources and geometry assertions.')
    else:
        OUT.mkdir(parents=True,exist_ok=True)
        for name,content in expected.items():
            tmp=OUT/(name+'.tmp');tmp.write_text(content,encoding='utf-8');tmp.replace(OUT/name)
        print('Built five static SVG figures.')
if __name__=='__main__': main()
