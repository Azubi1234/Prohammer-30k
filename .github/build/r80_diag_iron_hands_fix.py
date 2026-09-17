from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); OUT=Path('inspection-r80-iron-hands-fix-diag.txt')
NS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{NS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot(); PM={c:p for p in cr.iter() for c in p}; L=[]
def a(s=''):L.append(s)
def byid(root,i):return next((e for e in root.iter() if e.get('id')==i),None)
def dump(e,d=0,md=4):
    if e is None:a('  '*d+'<missing>');return
    attrs=' '.join(f'{k}={e.get(k)}' for k in ('id','name','type','targetId','hidden','defaultAmount') if e.get(k) is not None)
    a('  '*d+e.tag.split('}')[-1]+' '+attrs)
    if d>=md:return
    for ch in list(e):
        if ch.tag in (C('selectionEntries'),C('selectionEntryGroups'),C('entryLinks'),C('rules'),C('profiles'),C('constraints'),C('modifiers'),C('conditions'),C('conditionGroups'),C('categoryLinks'),C('costs')):
            a('  '*(d+1)+ch.tag.split('}')[-1]+':')
            for x in list(ch):dump(x,d+2,md)

a(f'CAT={cr.get("revision")} GSTref={cr.get("gameSystemRevision")} GST={gr.get("revision")}')
IDS=['r41-unit-x-0-medusan-immortal-squad','r41-unit-x-1-gorgon-terminator-squad','r41-unit-x-2-morlock-terminator-squad','r41-unit-x-3-venerable-forge-lord','r41-unit-x-4-shadrak-meduson','r41-unit-x-5-autek-mor','r41-unit-x-6-gabriel-santar','r41-unit-x-7-x-ferrus-manus-the-gorgon']
a('\n=== CANONICAL IRON HANDS ===')
for i in IDS:
    a('\n--- '+i+' ---');dump(byid(cr,i),0,5)

a('\n=== ALL SOURCE ENTRY RULES UNDER IRON HANDS IDs/COPIES ===')
for u in cr.iter(C('selectionEntry')):
    uid=u.get('id') or ''
    if any(i in uid for i in IDS):
        for r in u.iter(C('rule')):
            if (r.get('name') or '').lower().startswith('source entry'):
                a(f'{uid} :: {u.get("name")} :: {r.get("id")} :: {r.get("name")}')

a('\n=== GRAVITON SUBSTITUTION LINKS ===')
for e in cr.iter():
    if e.get('targetId')=='r44-ih-graviton-substitution' or e.get('id')=='r44-ih-graviton-substitution':
        p=PM.get(e); owner=p
        while owner is not None and owner.tag!=C('selectionEntry'):owner=PM.get(owner)
        a(f'{e.tag.split("}")[-1]} {e.get("id")} {e.get("name")} owner={owner.get("id") if owner is not None else None}:{owner.get("name") if owner is not None else None} parent={p.get("id") if p is not None else None}:{p.get("name") if p is not None else None}')

a('\n=== SPECIAL WEAPON GROUPS ===')
for g in cr.iter(C('selectionEntryGroup')):
    n=(g.get('name') or '').lower()
    if 'special weapon' in n:
        owner=g
        while owner is not None and owner.tag!=C('selectionEntry'):owner=PM.get(owner)
        a(f'OWNER={owner.get("id") if owner is not None else None}:{owner.get("name") if owner is not None else None} GROUP={g.get("id")}:{g.get("name")}')
        for x in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')):a(f'  ENTRY {x.get("id")} {x.get("name")} default={x.get("defaultAmount")}')
        for x in g.findall('./'+C('entryLinks')+'/'+C('entryLink')):a(f'  LINK {x.get("id")} {x.get("name")} -> {x.get("targetId")}')

a('\n=== RITES ===')
for rid in ('r25-rite-x-0-the-head-of-the-gorgon','r25-rite-x-1-company-of-bitter-iron'):
    a('\n--- '+rid+' ---');dump(byid(cr,rid),0,6)

a('\n=== RITE ROLE CLONES / CATEGORIES ===')
for u in cr.iter(C('selectionEntry')):
    uid=u.get('id') or ''; nm=u.get('name') or ''
    if 'bitter' in uid.lower() or 'immortal' in nm.lower() or 'gorgon' in uid.lower():
        if u.get('type')=='unit':
            cats=[(c.get('targetId'),c.get('primary')) for c in u.findall('./'+C('categoryLinks')+'/'+C('categoryLink'))]
            a(f'{uid} | {nm} | hidden={u.get("hidden")} cats={cats}')
            for m in u.findall('./'+C('modifiers')+'/'+C('modifier')):
                a('  MOD '+ET.tostring(m,encoding='unicode')[:1000])

a('\n=== GST FAST / FORCE STANDARD ===')
for i in ('fl-fast','force-standard'):
    a('\n--- '+i+' ---')
    e=byid(gr,i)
    if e is None:a('<missing>');continue
    a(ET.tostring(e,encoding='unicode')[:12000])
OUT.write_text('\n'.join(L),encoding='utf-8');print('\n'.join(L))
