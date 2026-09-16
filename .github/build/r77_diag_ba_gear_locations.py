from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat')
OUT=Path('inspection-r77-ba-gear-locations.txt')
NS='http://www.battlescribe.net/schema/catalogueSchema'
C=lambda t:f'{{{NS}}}{t}'
root=ET.parse(CAT).getroot()
parent={c:p for p in root.iter() for c in p}

TARGETS={'r44-ba-death-mask','r44-ba-inferno-pistol','r44-ba-blade-perdition','r74-ba-blade-exchange'}
NAMES=('Death Mask','Inferno Pistol','Blade of Perdition')

def path(e):
    parts=[];x=e
    while x is not None:
        tag=x.tag.split('}')[-1]
        nm=x.get('name') or ''
        i=x.get('id') or ''
        tid=x.get('targetId') or ''
        parts.append(f'{tag}[name={nm!r}, id={i!r}, target={tid!r}]')
        x=parent.get(x)
    return ' <- '.join(parts)

rows=[]
for e in root.iter():
    nm=e.get('name') or ''
    tid=e.get('targetId') or ''
    if tid in TARGETS or any(n in nm for n in NAMES):
        rows.append(path(e))

OUT.write_text(f'CAT revision={root.get("revision")}\nMatches={len(rows)}\n\n'+'\n'.join(rows)+'\n',encoding='utf-8')
print(OUT.read_text())
