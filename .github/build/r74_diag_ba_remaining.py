from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat');OUT=Path('inspection-r74-ba-remaining.txt');NS='http://www.battlescribe.net/schema/catalogueSchema';C=lambda t:f'{{{NS}}}{t}'
r=ET.parse(CAT).getroot();PM={c:p for p in r.iter() for c in p};L=[];a=L.append
def byid(i):return next((e for e in r.iter() if e.get('id')==i),None)
def owner(e):
 p=e
 while p is not None:
  if p.tag==C('selectionEntry') and p.get('type')=='unit':return p
  p=PM.get(p)
 return None
def cons(e):
 cs=e.find(C('constraints'));return [(x.get('id'),x.get('type'),x.get('value'),x.get('scope')) for x in cs.findall(C('constraint'))] if cs is not None else []
def mods(e):
 out=[];ms=e.find(C('modifiers'))
 if ms is not None:
  for m in ms.findall(C('modifier')):out.append((m.get('id'),m.get('type'),m.get('field'),m.get('value'),[(c.get('type'),c.get('value'),c.get('scope'),c.get('childId')) for c in m.findall('.//'+C('condition'))]))
 return out
def cats(e):
 cs=e.find(C('categoryLinks'));return [(x.get('name'),x.get('targetId'),x.get('primary')) for x in cs.findall(C('categoryLink'))] if cs is not None else []
for uid in ('hq-praetor','hq-centurion','r41-unit-ix-7-dominion-zephon','r41-unit-ix-11-ix-sanguinius-the-great-angel'):
 u=byid(uid);a(f'\n=== {uid} {u.get("name") if u is not None else "MISSING"} ===')
 if u is None:continue
 for e in u.iter():
  if e.tag not in (C('selectionEntry'),C('entryLink'),C('selectionEntryGroup')):continue
  n=(e.get('name') or '').lower();i=(e.get('id') or '').lower()
  if any(k in n or k in i for k in ('jump pack','warlord','jump-pack','jump')):
   a(f'{e.tag.split("}")[-1]} {e.get("id")} | {e.get("name")} -> {e.get("targetId")} hidden={e.get("hidden")} cons={cons(e)} mods={mods(e)} cats={cats(e)}')
# all shared entries named Jump Pack
a('\n=== ALL SHARED/LOCAL JUMP PACK DEFINITIONS ===')
for e in r.iter(C('selectionEntry')):
 if (e.get('name') or '').strip().lower()=='jump pack':a(f'{e.get("id")} type={e.get("type")} owner={owner(e).get("id") if owner(e) is not None else ""} cons={cons(e)} mods={mods(e)}')
# Blade / power weapon structure HQs
a('\n=== HQ POWER WEAPON / BLADE STRUCTURE ===')
for uid in ('hq-praetor','hq-centurion'):
 u=byid(uid)
 for e in u.iter():
  if e.tag not in (C('selectionEntry'),C('entryLink'),C('selectionEntryGroup')):continue
  n=(e.get('name') or '').lower()
  if 'power weapon' in n or 'blade of perdition' in n:a(f'{uid}: {e.tag.split("}")[-1]} {e.get("id")} | {e.get("name")} -> {e.get("targetId")} hidden={e.get("hidden")} cons={cons(e)} mods={mods(e)}')
OUT.write_text('\n'.join(L),encoding='utf-8');print(OUT.read_text())