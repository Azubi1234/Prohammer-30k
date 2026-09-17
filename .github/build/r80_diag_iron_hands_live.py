from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); OUT=Path('inspection-r80-iron-hands-live.txt')
NS='http://www.battlescribe.net/schema/catalogueSchema'; GS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{NS}}}{t}'; G=lambda t:f'{{{GS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot(); PM={c:p for p in cr.iter() for c in p}
ids=['r41-unit-x-5-autek-mor','r41-unit-x-7-x-ferrus-manus-the-gorgon','r25-rite-x-0-the-head-of-the-gorgon','r25-rite-x-1-company-of-bitter-iron','hq-praetor','hq-centurion','tactical-unit','veteran-unit','hs-heavy-support-squad']
def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def dump(e,depth=0,maxd=6):
    if e is None:return ['<missing>']
    out=[]; ind='  '*depth; attrs=' '.join(f'{k}={e.get(k)}' for k in ('id','name','type','targetId','hidden','defaultAmount') if e.get(k)!=None)
    out.append(ind+e.tag.split('}')[-1]+' '+attrs)
    if depth>=maxd:return out
    for x in list(e):
        if x.tag.split('}')[-1] in ('selectionEntries','selectionEntryGroups','entryLinks','rules','profiles','infoLinks','modifiers','constraints','categoryLinks'):
            out.append(ind+'  '+x.tag.split('}')[-1]+':')
            for z in list(x):out+=dump(z,depth+2,maxd)
    return out
L=[f'CAT={cr.get("revision")} GSTREF={cr.get("gameSystemRevision")} GST={gr.get("revision")}']
for i in ids:
    L+=['\n===' + i + '===']+dump(byid(cr,i),0,7)
L+=['\n=== SOURCE ENTRY AUT/MANUS MATCHES ===']
for e in cr.iter():
    n=(e.get('name') or '')
    txt=' '.join((d.text or '') for d in e.findall('.//'+C('description')))
    if 'Source Entry: Autek Mor' in n or 'Source Entry: Ferrus' in n or 'Source Entry: Autek Mor' in txt or 'Source Entry: Ferrus' in txt:
        p=PM.get(e); L.append(f'{e.tag.split("}")[-1]} {e.get("id")} {n} PARENT={p.get("id") if p is not None else None}::{p.get("name") if p is not None else None}')
L+=['\n=== GRAVITON LOCATIONS ===']
for e in cr.iter():
    if 'graviton' in (e.get('name') or '').lower():
        p=PM.get(e); L.append(f'{e.tag.split("}")[-1]} {e.get("id")} {e.get("name")} PARENT={p.get("id") if p is not None else None}::{p.get("name") if p is not None else None}')
L+=['\n=== R79 RITE OBJECTS ===']
for e in list(cr.iter())+list(gr.iter()):
    if (e.get('id') or '').startswith('r79-ih-') and any(k in (e.get('id') or '') for k in ('head','bitter','scions')):
        L.append(f'{e.tag.split("}")[-1]} {e.get("id")} {e.get("name")} {e.get("type")} {e.get("value")} child={e.get("childId")} field={e.get("field")} scope={e.get("scope")}')
OUT.write_text('\n'.join(L),encoding='utf-8'); print('\n'.join(L))
