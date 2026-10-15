"""Render the homepage's vector illustrations from captured App tip examples."""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = json.loads((Path(__file__).with_name('home_tip_examples.json')).read_text())
INK, BLUE, RED = '#243344', '#3678d3', '#b83432'


def text(x, y, value, size=17, color=INK, anchor='middle'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" dominant-baseline="central">{html.escape(str(value))}</text>'


def visible(body, start, end):
    return f'<g opacity="0"><set attributeName="opacity" to="1" begin="{start}s"/><set attributeName="opacity" to="0" begin="{end}s"/>{body}</g>'


def rect(x, y, w, h, color=BLUE, width=3, radius=0, dash=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="none" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>'


def state(name, slot=0):
    ex = EXAMPLES[name]
    givens = list(map(int, ex['grid']))
    fills, deleted = givens.copy(), set()
    for action in ex['setup']:
        if action.get('slot', 0) != slot or 'choice' not in action:
            continue
        c = action['choice']; i = c['row'] * 9 + c['col']; value = c['label'] + 1
        if action['id'] == 'SET_FILL': fills[i] = value
        if action['id'] == 'DELETE_NOTE': deleted.add((i, value))
    notes = []
    for i, value in enumerate(fills):
        r, c = divmod(i, 9)
        peers = {r*9+k for k in range(9)} | {k*9+c for k in range(9)} | {(r//3*3+a)*9+c//3*3+b for a in range(3) for b in range(3)}
        notes.append([] if value else [n for n in range(1, 10) if n not in {fills[j] for j in peers} and (i, n) not in deleted])
    return givens, fills, notes


def board(name, x=85, y=12, cell=50, rows=9, slot=0):
    givens, fills, notes = state(name, slot)
    body = f'<rect x="{x}" y="{y}" width="{9*cell}" height="{rows*cell}" fill="#fbfcfe"/>'
    for i in range(rows*9):
        r, c = divmod(i, 9); xx, yy = x+c*cell, y+r*cell
        if givens[i]: body += f'<rect x="{xx}" y="{yy}" width="{cell}" height="{cell}" fill="#f0f3f7"/>'
        if fills[i]: body += text(xx+cell/2, yy+cell/2, fills[i], cell*.64, INK if givens[i] else '#365d92')
        else:
            for n in notes[i]: body += text(xx+((n-1)%3+.5)*cell/3, yy+((n-1)//3+.5)*cell/3, n, cell*.22)
    for k in range(10):
        body += f'<path d="M{x+k*cell},{y}v{rows*cell}" stroke="{INK if k%3==0 else "#9da6b2"}" stroke-width="{2.3 if k%3==0 else .65}"/>'
    for k in range(rows+1):
        body += f'<path d="M{x},{y+k*cell}h{9*cell}" stroke="{INK if k%3==0 else "#9da6b2"}" stroke-width="{2.3 if k%3==0 else .65}"/>'
    return body


def caption(lines, start, end):
    if isinstance(lines, str): lines = [lines]
    height = 28+len(lines)*22
    body = f'<rect x="22" y="{472-height}" width="576" height="{height}" rx="15" fill="#fff" stroke="#d4dbe5"/>'
    for i, line in enumerate(lines): body += text(310, 488-height+i*22, line, 17)
    return visible(body, start, end)


def finger(points, times, down, up):
    # The complete finger moves as one shape; there is no shortening on contact.
    values = ';'.join(f'{x} {y}' for x,y in points)
    end = times[-1]
    keys = ';'.join(str(t/end) for t in times)
    touch = f'<circle r="17" fill="#3e96ff" fill-opacity=".3" stroke="{BLUE}" stroke-width="2"/>'
    hand = '<path d="M0,0 C-7,-9 -14,-5 -10,3 L8,31 L2,26 C-6,20 -13,27 -6,35 L13,56 C25,69 48,59 48,44 L44,25 C42,17 35,15 31,20 C28,12 20,12 17,17 L4,1 Z" fill="#fff" stroke="#202d39" stroke-width="2.5" stroke-linejoin="round"/>'
    return f'<g><animateTransform attributeName="transform" type="translate" values="{values}" keyTimes="{keys}" dur="{end}s" fill="freeze" calcMode="linear"/>{visible(touch,down,up)}{hand}</g>'


def wrap(name, title, description, body, duration):
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 480" role="img" aria-labelledby="{name}-vector-title {name}-vector-description" data-duration="{duration}">
<title id="{name}-vector-title">{html.escape(title)}</title><desc id="{name}-vector-description">{html.escape(description)}</desc>
<style>text{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}svg{{background:#fff}} </style>
<rect width="620" height="480" rx="12" fill="#fff"/>{body}</svg>'''
    (ROOT/'home-assets'/f'{name}.svg').write_text(svg+'\n')
    page = ROOT/'index.html'
    source = page.read_text()
    pattern = f'<!-- home-tip:{name} -->.*?<!-- /home-tip:{name} -->'
    source, count = re.subn(pattern, lambda _: f'<!-- home-tip:{name} -->{svg}<!-- /home-tip:{name} -->', source, flags=re.S)
    if count != 1: raise ValueError(f'Missing or repeated illustration slot: {name}')
    page.write_text(source)


def touch():
    b = board('action-hold')
    b += visible(rect(185,212,50,50), .3, 3.3)
    popup = '<rect x="162" y="30" width="168" height="190" rx="13" fill="white" stroke="#b3bdca"/>' + text(246,44,'FILL',11)
    for n in range(1,10): popup += text(190+(n-1)%3*56,80+(n-1)//3*56,n,28)
    popup += visible('<rect x="275" y="166" width="52" height="51" rx="10" fill="#428bfa" fill-opacity=".5"/>',5,8.8)
    popup += visible('<rect x="275" y="110" width="52" height="51" rx="10" fill="#428bfa" fill-opacity=".5"/>',9.3,12.3)
    for cx,cy,start in [(302,192,4),(302,136,8.3)]:
        popup += visible(f'<circle cx="{cx}" cy="{cy}" r="23" fill="none" stroke="{BLUE}" stroke-width="3" stroke-dasharray="145" stroke-dashoffset="145"><animate attributeName="stroke-dashoffset" from="145" to="0" begin="{start}s" dur="1s" fill="freeze"/></circle>',start,start+1.05)
    b += visible(popup,3.3,12.3)
    b += visible('<rect x="187" y="214" width="46" height="46" fill="#fbfcfe"/>'+text(210,237,6,32,'#365d92'),12.3,16)
    b += visible(finger([(290,330),(210,237),(210,237),(245,272),(245,272),(270,237),(270,237),(284,250)],[0,1,3.4,4,8.3,9.3,12.3,12.6],3.4,12.3),2.4,13.4)
    b += caption(['Drag and hold to open the label picker.'],.2,3.2)
    b += caption('Move south-east for 9.',3.4,8.2)
    b += caption('Move to 6, wait for the ring, then lift.',8.4,12.2)
    b += caption('The selected label fills the cell.',12.4,15.8)
    wrap('touch','Fill directly on the grid','Animated vector illustration using the App drag-and-hold tip puzzle. Drag direction selects 9, then 6; lifting fills 6.',b,16)


def overlay():
    b = ''
    for i in range(6):
        x=28+i*97; color=['#303947','#7f78d9','#c48a29','#39a8ca','#8d4ec6','#347fcd'][i]
        b += text(x+32,18,i+1,16,color)
        if i<2:
            b += f'<rect x="{x}" y="32" width="64" height="64" rx="8" fill="#f3f5f8" stroke="{color}" stroke-width="2"/>'
            for k in range(1,3): b+=f'<path d="M{x+k*64/3},32v64 M{x},{32+k*64/3}h64" stroke="{color}" stroke-width=".8"/>'
        else:b+=f'<path d="M{x+18},95v-38l14,-17 14,17v38z" fill="{color}"/>'
    b+=board('action-overlay',31,130,62,4)
    marks=''
    for action in EXAMPLES['action-overlay']['setup']:
        c=action.get('choice')
        if not c:continue
        r,col,n=c['row'],c['col'],c['label']+1
        x=31+col*62+((n-1)%3+.5)*62/3;y=130+r*62+((n-1)//3+.5)*62/3
        if action['id']=='SET_FILL':marks+=f'<circle cx="{x}" cy="{y}" r="9" fill="{"#a8a2ef" if col==2 and r==0 else "none"}" stroke="#7f78d9" stroke-width="2"/>'
        elif action['id']=='DELETE_NOTE':marks+=f'<path d="M{x-9},{y}h18" stroke="#7f78d9" stroke-width="2"/>'
    b+=visible(marks,5.2,12.5)
    b+=visible(rect(26,125,568,253,'#7f78d9',3,0,'8 5'),3.5,5.2)
    b+=visible(finger([(205,135),(157,78),(157,78),(290,160),(290,160),(310,182)],[0,1,3.1,4.8,5.2,5.5],3.1,5.2),2,6.1)
    b+=visible(finger([(210,135),(157,78),(157,78),(169,90)],[0,11.6,12.3,12.6],12,12.3),10.7,13.2)
    b+=caption('Drag board 2 over your original board.',.2,5.1)
    b+=caption(['Circles show its fills; lines show removed notes.','The solid disc marks its first fill.'],5.4,10.5)
    b+=caption('Tap board 2 to remove the overlay.',10.7,12.4)
    b+=caption('The marks disappear. Your original is unchanged.',12.7,15.8)
    wrap('overlay','Look at what a try board changed','Vector illustration using the App overlay tip puzzle. Drag a copied board onto the original; see its fills and eliminated notes, then remove the overlay.',b,16)


def definite():
    b=board('action-pill',116,53,43)
    b+='<rect x="116" y="12" width="100" height="28" rx="9" fill="#e0f1e6"/>'+text(166,26,'Definite',16,'#267449')
    _, fills, notes=state('action-pill'); moves=[]
    houses=[[r*9+c for c in range(9)]for r in range(9)]+[[r*9+c for r in range(9)]for c in range(9)]+[[(r+a)*9+c+d for a in range(3)for d in range(3)]for r in [0,3,6]for c in [0,3,6]]
    for house in houses:
        for n in range(1,10):
            spots=[i for i in house if n in notes[i]]
            if len(spots)==1 and not any(i==spots[0] and label==n for i,label,_ in moves):moves.append((spots[0],n,house))
    assert len(moves) >= 3, 'The Definite illustration needs three actual enforced moves'
    for k,(i,n,house) in enumerate(moves[:3]):
        r,c=divmod(i,9);start=3+k*4
        xs=[j%9 for j in house];ys=[j//9 for j in house]
        mark=rect(116+min(xs)*43,53+min(ys)*43,(max(xs)-min(xs)+1)*43,(max(ys)-min(ys)+1)*43)
        mark+=rect(116+c*43+((n-1)%3)*43/3,53+r*43+((n-1)//3)*43/3,43/3,43/3)
        b+=visible(mark,start,start+3.8)
    b+=caption('Tap Definite to focus on an enforced move.',.2,2.8)
    b+=caption('Only one place remains for this label in the set.',3,6.8)
    b+=caption('Tap again to visit another enforced move.',7,14.9)
    wrap('definite','Find enforced moves in your notes','Vector illustration from the App Definite example. Each highlighted set has one remaining place for its indicated label. The examples are derived from current fills and notes.',b,15)


def invalid():
    _, _, notes = state('warning-crowded-cell')
    assert [i for i in range(9) if 4 in notes[i]] == [0]
    assert [i for i in range(0,81,9) if 7 in notes[i]] == [0]
    b=board('warning-crowded-cell',116,12,43)
    b+=visible(rect(116,12,387,43,RED),.2,4.2)
    b+=visible(rect(116,12,43,387,RED),4.4,8.4)
    b+=visible(rect(116,12,43,43,RED),8.6,15)
    for n in [4,7]:b+=rect(116+((n-1)%3)*43/3,12+((n-1)//3)*43/3,43/3,43/3,RED,2)
    b+=caption('Row 1 has only one place left for 4.',.2,4.2)
    b+=caption('Column 1 has only one place left for 7.',4.4,8.4)
    b+=caption(['Both are forced into the same cell.','The red boxes show the conflict.'],8.6,14.8)
    wrap('invalid','See why two enforced moves conflict','Vector illustration using the App crowded-cell tip. Row 1 forces 4 and column 1 forces 7 into row 1 column 1; one cell cannot hold both.',b,15)


if __name__ == '__main__':
    for render in (touch, overlay, definite, invalid):render()
