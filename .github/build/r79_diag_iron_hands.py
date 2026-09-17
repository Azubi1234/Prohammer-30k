from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); OUT=Path('inspection-r79-iron-hands-diagnostic.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot(); PM={c:p for p in cr.iter() for c in p}
L=[]; add=L.append
add(f'CAT revision={cr.get("revision")} GST ref={cr.get("gameSystemRevision")} GST revision={gr.get("revision")}')

def path(e):
    parts=[]; x=e
    while x is not None and x is not cr:
        nm=x.get('name') or ''; id_=x.get('id') or ''; tg=x.tag.split('}')[-1]
        if nm or id_: parts.append(f"{tg}[{id_}::{nm}]")
        x=PM.get(x)
    return ' <- '.join(parts)

def costs(e):
    return ','.join(f"{c.get('name')}={c.get('value')}" for c in e.findall('./'+C('costs')+'/'+C('cost')))

def constraints(e):
    return '; '.join(f"{c.get('type')}={c.get('value')} field={c.get('field')} scope={c.get('scope')} child={c.get('childId')}" for c in e.findall('./'+C('constraints')+'/'+C('constraint')))

def dump_unit(e):
    add('\n'+'='*90); add(f"UNIT {e.get('id')} | {e.get('name')} | cost={costs(e)} | {constraints(e)}")
    for p in e.findall('./'+C('profiles')+'/'+C('profile')): add(f"  TOP PROFILE {p.get('id')} | {p.get('name')}")
    for r in e.findall('./'+C('rules')+'/'+C('rule')):
        d=r.find(C('description')); tx=(d.text or '') if d is not None else ''
        add(f"  TOP RULE {r.get('id')} | {r.get('name')} :: {tx[:350]}")
    for g in e.iter(C('selectionEntryGroup')):
        add(f"  GROUP {g.get('id')} | {g.get('name')} | hidden={g.get('hidden')} | {constraints(g)}")
        for x in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')):
            add(f"    ENTRY {x.get('id')} | {x.get('name')} | cost={costs(x)} | {constraints(x)}")
        for x in g.findall('./'+C('entryLinks')+'/'+C('entryLink')):
            add(f"    LINK {x.get('id')} | {x.get('name')} -> {x.get('targetId')} | {constraints(x)}")

# Identify every likely Iron Hands object currently present.
needles=('iron hands','medusan','gorgon','morlock','ferrus','santar','meduson','autek','castrmen','orth','forge lord','bitter iron','head of the gorgon','albian power gladius','splinter bolts','blessed autosimulacra','mechadendrites')
matches=[]
for e in cr.iter():
    nm=(e.get('name') or '').lower(); id_=(e.get('id') or '').lower();
    desc=' '
    d=e.find(C('description')) if e.tag in (C('rule'),C('infoLink')) else None
    if d is not None and d.text: desc=d.text.lower()
    if any(n in nm or n in id_ or n in desc for n in needles): matches.append(e)
add('\n=== MATCH INDEX ===')
for e in matches: add(path(e))

# Top level units likely belonging to Legion X or imported around Iron Hands.
top=cr.find(C('selectionEntries'))
if top is not None:
    for e in top.findall(C('selectionEntry')):
        uid=e.get('id') or ''; nm=e.get('name') or ''
        text=(uid+' '+nm).lower()
        if any(n in text for n in needles) or uid.startswith('r41-unit-x-'):
            dump_unit(e)

add('\n=== SOURCE ENTRY / AGGREGATE RULE RISKS INSIDE IRON HANDS MATCHED UNITS ===')
for e in cr.iter(C('selectionEntry')):
    uid=e.get('id') or ''; nm=e.get('name') or ''; text=(uid+' '+nm).lower()
    if e.get('type')!='unit' or not (uid.startswith('r41-unit-x-') or any(n in text for n in needles)): continue
    for r in e.iter(C('rule')):
        rn=(r.get('name') or ''); d=r.find(C('description')); tx=(d.text or '') if d is not None else ''
        if rn.lower().startswith('source entry') or ('force organisation:' in tx.lower() and 'wargear:' in tx.lower() and 'special rules:' in tx.lower()):
            add(f"{uid} | {nm} :: {path(r)}")

add('\n=== CURRENT LEGION X CONDITIONAL LINKS ON GENERIC PRAETOR/CENTURION ===')
for uid in ('hq-praetor','hq-centurion'):
    u=next((x for x in cr.iter() if x.get('id')==uid),None)
    if u is None: continue
    add(f'[{uid}]')
    for x in u.iter():
        xid=x.get('id') or ''; nm=x.get('name') or ''; target=x.get('targetId') or ''
        blob=(xid+' '+nm+' '+target).lower()
        if any(n in blob for n in ('iron','bionic','servo-arm','mechadend','gladius','splinter','autosimulacra')):
            add(path(x))

add('\n=== RITE CANDIDATES ===')
for e in cr.iter():
    nm=(e.get('name') or '').lower(); id_=e.get('id') or ''
    if 'head of the gorgon' in nm or 'company of bitter iron' in nm:
        add(path(e))

OUT.write_text('\n'.join(L),encoding='utf-8')
print('\n'.join(L[-220:]))
