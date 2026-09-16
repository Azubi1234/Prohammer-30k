from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot()
def byid(root,i):return next((x for x in root.iter() if x.get('id')==i),None)
def tag(x):return x.tag.split('}')[-1]
def text(x):
    vals=[]
    for d in x.iter():
        if d.text and d.text.strip():vals.append(d.text.strip().replace('\n',' | '))
    return ' || '.join(vals)
u=byid(cr,'r41-unit-ix-8-aster-crohne')
out=[]
out.append(f'ROOT {u.get("id")} {u.get("name")} rev={cr.get("revision")}')
for x in u.iter():
    if x is u:continue
    t=tag(x);i=x.get('id');n=x.get('name');target=x.get('targetId');typ=x.get('type') or x.get('typeId')
    if t in ('rule','infoLink','infoGroup','profile','selectionEntry','entryLink') or 'source' in (n or '').lower():
        out.append(f'{t} id={i} name={n} target={target} type={typ} hidden={x.get("hidden")} text={text(x)[:1200]}')
        if target:
            y=byid(cr,target) or byid(gr,target)
            if y is not None:out.append(f'  TARGET {tag(y)} id={y.get("id")} name={y.get("name")} type={y.get("type") or y.get("typeId")} text={text(y)[:1800]}')
# Also find every object anywhere whose name/description references Aster Crohne or Source Entry.
for root,label in ((cr,'CAT'),(gr,'GST')):
    for x in root.iter():
        blob=((x.get('name') or '')+' '+text(x)).lower()
        if ('aster crohne' in blob or 'source entry' in blob) and x not in list(u.iter()):
            out.append(f'GLOBAL {label} {tag(x)} id={x.get("id")} name={x.get("name")} target={x.get("targetId")} type={x.get("type") or x.get("typeId")} text={text(x)[:1800]}')
Path('inspection-r75-crohne-source-entry.txt').write_text('\n'.join(out),encoding='utf-8')
print('\n'.join(out))