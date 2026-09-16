from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); OUT=Path('inspection-r74-ba-models.txt'); NS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{NS}}}{t}'
r=ET.parse(CAT).getroot(); L=[]
def cost(e):
 cs=e.find(C('costs')); return [(x.get('typeId'),x.get('value')) for x in cs.findall(C('cost'))] if cs is not None else []
def cons(e):
 cs=e.find(C('constraints')); return [(x.get('id'),x.get('type'),x.get('value'),x.get('field'),x.get('scope')) for x in cs.findall(C('constraint'))] if cs is not None else []
def mods(e):
 out=[]; ms=e.find(C('modifiers'))
 if ms is not None:
  for m in ms.findall(C('modifier')):
   cond=[(c.get('type'),c.get('value'),c.get('scope'),c.get('childId'),c.get('field')) for c in m.findall('.//'+C('condition'))]
   rep=[(q.get('value'),q.get('repeats'),q.get('scope'),q.get('childId'),q.get('field')) for q in m.findall('.//'+C('repeat'))]
   out.append((m.get('id'),m.get('type'),m.get('field'),m.get('value'),cond,rep))
 return out
for u in r.iter(C('selectionEntry')):
 if u.get('type')=='unit' and ('r41-unit-ix-' in (u.get('id') or '')):
  L.append(f"\nUNIT {u.get('id')} {u.get('name')} cost={cost(u)} cons={cons(u)}")
  for x in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')):
   L.append(f" DIRECT {x.get('type')} {x.get('id')} {x.get('name')} default={x.get('defaultAmount')} hidden={x.get('hidden')} cost={cost(x)} cons={cons(x)} mods={mods(x)}")
   for p in x.findall('./'+C('profiles')+'/'+C('profile')): L.append(f"  PROFILE {p.get('name')}")
  for g in u.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')):
   L.append(f" GROUP {g.get('id')} {g.get('name')} cons={cons(g)} mods={mods(g)}")
OUT.write_text('\n'.join(L),encoding='utf-8'); print(OUT.read_text())