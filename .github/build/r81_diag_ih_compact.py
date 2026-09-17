from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); OUT=Path('inspection-r81-ih-compact.txt')
NS='http://www.battlescribe.net/schema/catalogueSchema'; GS='http://www.battlescribe.net/schema/gameSystemSchema'; C=lambda t:f'{{{NS}}}{t}'; G=lambda t:f'{{{GS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot(); PM={c:p for p in cr.iter() for c in p}
def owner(e):
 p=e
 while p is not None and p.tag!=C('selectionEntry'): p=PM.get(p)
 return p
def line(e):
 p=PM.get(e); o=owner(e); return f'{e.tag.split("}")[-1]} id={e.get("id")} name={e.get("name")} type={e.get("type")} target={e.get("targetId")} hidden={e.get("hidden")} parent={p.get("id") if p is not None else None}::{p.get("name") if p is not None else None} owner={o.get("id") if o is not None else None}::{o.get("name") if o is not None else None}'
L=[f'CAT={cr.get("revision")} GST={gr.get("revision")}']
for title,term in [('GRAVITON','graviton'),('SPECIAL WEAPON GROUPS','special weapon'),('FERRUS','ferrus'),('AUTek source','source entry'),('BITTER','bitter'),('GORGON RITE','head of the gorgon')]:
 L+=['\n==='+title+'===']
 for e in cr.iter():
  if term in ((e.get('name') or '')+' '+(e.get('id') or '')).lower(): L.append(line(e))
for i in ['r41-unit-x-7-x-ferrus-manus-the-gorgon','r41-unit-x-5-autek-mor','r25-rite-x-0-the-head-of-the-gorgon','r25-rite-x-1-company-of-bitter-iron']:
 u=next((e for e in cr.iter() if e.get('id')==i),None); L+=['\n===DIRECT '+i+'===']
 if u is not None:
  for x in list(u):
   L.append(x.tag.split('}')[-1]+' '+str([(z.get('id'),z.get('name'),z.get('type'),z.get('targetId'),z.get('hidden'),z.get('defaultAmount')) for z in list(x)[:30]]))
L+=['\n===GST RITE OBJECTS===']
for e in gr.iter():
 if any(k in ((e.get('name') or '')+' '+(e.get('id') or '')).lower() for k in ('bitter','gorgon','fast attack','consul')): L.append(f'{e.tag.split("}")[-1]} id={e.get("id")} name={e.get("name")} type={e.get("type")} value={e.get("value")} field={e.get("field")} child={e.get("childId")} scope={e.get("scope")}')
OUT.write_text('\n'.join(L),encoding='utf-8'); print('\n'.join(L))
