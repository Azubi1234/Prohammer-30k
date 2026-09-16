from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); OUT=Path('inspection-r71-nl-structure.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot(); PM={c:p for p in cr.iter() for c in p}
L=[]; add=L.append

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def owner_entry(e):
 p=e
 while p is not None and p.tag!=C('selectionEntry'): p=PM.get(p)
 return p
def cons(e,ns=CNS):
 Q=lambda t:f'{{{ns}}}{t}'
 return '; '.join(f"{x.get('type')}={x.get('value')} field={x.get('field')} scope={x.get('scope')} child={x.get('childId')}" for x in e.findall('./'+Q('constraints')+'/'+Q('constraint')))
def dumpmods(e,ns=CNS):
 Q=lambda t:f'{{{ns}}}{t}'
 for m in e.findall('./'+Q('modifiers')+'/'+Q('modifier')):
  add(f"  MOD id={m.get('id')} type={m.get('type')} field={m.get('field')} value={m.get('value')}")
  for c in m.iter(Q('condition')): add(f"    COND {c.get('type')} {c.get('value')} field={c.get('field')} scope={c.get('scope')} child={c.get('childId')}")
def cats(e): return ','.join((x.get('name') or x.get('targetId') or '') for x in e.findall('./'+C('categoryLinks')+'/'+C('categoryLink')))
def costs(e): return ','.join(f"{x.get('name')}:{x.get('typeId')}={x.get('value')} id={x.get('id')}" for x in e.findall('./'+C('costs')+'/'+C('cost')))

add(f"CAT={cr.get('revision')} GST={gr.get('revision')} GSTREF={cr.get('gameSystemRevision')}")
add('\n=== RITES EXACT ===')
for e in cr.iter(C('selectionEntry')):
 i=e.get('id') or ''; n=e.get('name') or ''
 if i.startswith('r25-rite-viii') or ('terror assault' in n.lower() or 'horror cult' in n.lower()):
  add(f"{i} | {n} | type={e.get('type')} hidden={e.get('hidden')} cats={cats(e)} {cons(e)}")
  dumpmods(e)
add('\n=== VIII ROLE CLONES ===')
for e in cr.iter(C('selectionEntry')):
 i=e.get('id') or ''
 if i.startswith('r42-role-viii'):
  add(f"{i} | {e.get('name')} | hidden={e.get('hidden')} cats={cats(e)} cost={costs(e)} {cons(e)}")
  dumpmods(e)

add('\n=== ALLEGIANCE OBJECTS / CONDITIONS ===')
for e in list(cr.iter())+list(gr.iter()):
 n=(e.get('name') or '').lower(); i=e.get('id') or ''; ch=e.get('childId') or ''
 if any(k in n for k in ('traitor','loyalist','allegiance')) or any(k in i.lower() for k in ('traitor','loyalist','allegiance')) or any(k in ch.lower() for k in ('traitor','loyalist','allegiance')):
  add(f"{e.tag.split('}')[-1]} id={i} name={e.get('name')} type={e.get('type')} child={ch} field={e.get('field')} value={e.get('value')}")

add('\n=== SERGEANT ARMOURY GROUPS ===')
seen=set()
for g in cr.iter(C('selectionEntryGroup')):
 n=(g.get('name') or '').lower()
 if 'sergeant armoury' in n or ('armoury' in n and any(k in n for k in ('sergeant','character'))):
  o=owner_entry(g); key=(g.get('id'),o.get('id') if o is not None else '')
  if key in seen: continue
  seen.add(key)
  add(f"OWNER {o.get('id') if o is not None else '?'} | {o.get('name') if o is not None else '?'} :: GROUP {g.get('id')} | {g.get('name')} | {cons(g)}")
  for l in g.findall('./'+C('entryLinks')+'/'+C('entryLink')): add(f"  LINK {l.get('id')} | {l.get('name')} -> {l.get('targetId')} | {cons(l)}")
  for x in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')): add(f"  ENTRY {x.get('id')} | {x.get('name')} cost={costs(x)} | {cons(x)}")

add('\n=== PER-MODEL / COST MODIFIER EXAMPLES ===')
cnt=0
for e in cr.iter():
 mods=e.find(C('modifiers'))
 if mods is None: continue
 for m in list(mods):
  if m.get('field') in ('pts','points') or m.get('type') in ('increment','decrement'):
   o=owner_entry(e)
   add(f"OWNER={o.get('id') if o is not None else '?'} {o.get('name') if o is not None else '?'} NODE={e.get('id')} {e.get('name')} COST={costs(e)}")
   dumpmods(e); cnt+=1
   if cnt>=30: break
 if cnt>=30: break
add(f"COST_MOD_EXAMPLES={cnt}")

add('\n=== NIGHT LORDS UNIQUE CHILD STRUCTURES ===')
for ident in ['r41-unit-viii-0-terror-squad','r41-unit-viii-1-night-raptor-squad','r41-unit-viii-2-contekar-terminator-elite','r41-unit-viii-3-atramentar-flay-clade']:
 u=byid(cr,ident); add(f"UNIT {ident} | {u.get('name') if u is not None else 'MISSING'} | cost={costs(u) if u is not None else ''}")
 if u is None: continue
 for x in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')):
  add(f"  MODEL/ENTRY {x.get('id')} | {x.get('name')} type={x.get('type')} default={x.get('defaultAmount')} cost={costs(x)} {cons(x)}")
 for g in u.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')):
  add(f"  GROUP {g.get('id')} | {g.get('name')} | {cons(g)}")
  for x in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')): add(f"    ENTRY {x.get('id')} | {x.get('name')} cost={costs(x)} {cons(x)}")
  for l in g.findall('./'+C('entryLinks')+'/'+C('entryLink')): add(f"    LINK {l.get('id')} | {l.get('name')} -> {l.get('targetId')} {cons(l)}")
 for l in u.findall('./'+C('entryLinks')+'/'+C('entryLink')): add(f"  TOPLINK {l.get('id')} | {l.get('name')} -> {l.get('targetId')} {cons(l)}")

add('\n=== GENERIC TERMINATOR / TERROR TRANSPORT PATTERNS ===')
for ident in ['terminator-unit','hq-praetor-ret-termcommand','hq-centurion-ret-command','r41-unit-viii-0-terror-squad','r41-unit-viii-2-contekar-terminator-elite','r41-unit-viii-3-atramentar-flay-clade']:
 u=byid(cr,ident); add(f"UNIT {ident} | {u.get('name') if u is not None else 'MISSING'}")
 if u is None: continue
 for g in u.iter(C('selectionEntryGroup')):
  if 'transport' in (g.get('name') or '').lower() or 'land raider' in (g.get('name') or '').lower():
   add(f"  GROUP {g.get('id')} | {g.get('name')} {cons(g)}")
   for l in g.findall('./'+C('entryLinks')+'/'+C('entryLink')): add(f"    LINK {l.get('id')} | {l.get('name')} -> {l.get('targetId')} {cons(l)}")
   for x in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')): add(f"    ENTRY {x.get('id')} | {x.get('name')} type={x.get('type')} cost={costs(x)} {cons(x)}")
 for l in u.iter(C('entryLink')):
  if any(k in (l.get('name') or '').lower() for k in ('rhino','drop pod','dreadclaw','land raider','spartan')): add(f"  TRANSLINK {l.get('id')} | {l.get('name')} -> {l.get('targetId')} {cons(l)}")

add('\n=== CHARACTER RETINUE PATTERNS ===')
for ident in ['r41-unit-viii-4-jago-sevatarion','r41-unit-viii-5-kheron-ophion','r41-unit-viii-6-malcharion-the-war-sage','r41-unit-viii-7-shang','r41-unit-viii-9-viii-konrad-curze-the-night-haunter','r41-unit-vii-0-sigismund']:
 u=byid(cr,ident); add(f"CHAR {ident} | {u.get('name') if u is not None else 'MISSING'}")
 if u is None: continue
 for g in u.iter(C('selectionEntryGroup')):
  if 'retinue' in (g.get('name') or '').lower() or 'command' in (g.get('name') or '').lower():
   add(f"  GROUP {g.get('id')} | {g.get('name')} {cons(g)}")
   for l in g.findall('./'+C('entryLinks')+'/'+C('entryLink')): add(f"    LINK {l.get('id')} | {l.get('name')} -> {l.get('targetId')} {cons(l)}")
   for x in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')): add(f"    ENTRY {x.get('id')} | {x.get('name')} type={x.get('type')} cost={costs(x)} {cons(x)}")
 for l in u.iter(C('entryLink')):
  if any(k in (l.get('name') or '').lower() for k in ('command squad','retinue','atramentar','contekar','terror squad')): add(f"  LINK {l.get('id')} | {l.get('name')} -> {l.get('targetId')} {cons(l)}")

OUT.write_text('\n'.join(L),encoding='utf-8')
print('\n'.join(L))
