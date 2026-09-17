from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); OUT=Path('inspection-r86-world-eaters-diagnostic.txt')
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

def conditions(e):
    out=[]
    for c in e.iter(C('condition')):
        out.append(f"{c.get('type')} {c.get('value')} {c.get('field')} scope={c.get('scope')} child={c.get('childId')}")
    return '; '.join(out)

def dump_unit(e):
    add('\n'+'='*100); add(f"UNIT {e.get('id')} | {e.get('name')} | hidden={e.get('hidden')} | cost={costs(e)} | {constraints(e)}")
    cats=[f"{x.get('name')}->{x.get('targetId')}" for x in e.findall('./'+C('categoryLinks')+'/'+C('categoryLink'))]
    if cats:add('  CATEGORIES '+', '.join(cats))
    for p in e.findall('./'+C('profiles')+'/'+C('profile')):
        vals=[]
        for ch in p.findall('./'+C('characteristics')+'/'+C('characteristic')): vals.append(f"{ch.get('name')}={ch.text}")
        add(f"  TOP PROFILE {p.get('id')} | {p.get('name')} :: {' '.join(vals)}")
    for r in e.findall('./'+C('rules')+'/'+C('rule')):
        d=r.find(C('description')); tx=(d.text or '') if d is not None else ''
        add(f"  TOP RULE {r.get('id')} | {r.get('name')} :: {tx[:900]}")
    for g in e.iter(C('selectionEntryGroup')):
        add(f"  GROUP {g.get('id')} | {g.get('name')} | hidden={g.get('hidden')} | {constraints(g)} | conds={conditions(g)}")
        for x in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')):
            add(f"    ENTRY {x.get('id')} | {x.get('name')} | hidden={x.get('hidden')} | cost={costs(x)} | {constraints(x)} | conds={conditions(x)}")
        for x in g.findall('./'+C('entryLinks')+'/'+C('entryLink')):
            add(f"    LINK {x.get('id')} | {x.get('name')} -> {x.get('targetId')} | hidden={x.get('hidden')} | {constraints(x)} | conds={conditions(x)}")
    for x in e.findall('./'+C('entryLinks')+'/'+C('entryLink')):
        add(f"  TOP LINK {x.get('id')} | {x.get('name')} -> {x.get('targetId')} | hidden={x.get('hidden')} | {constraints(x)} | conds={conditions(x)}")

needles=('world eaters','world eater','blood frenzy','death from above','butchery','slaughter','chainaxe','caedere','rampager','red butcher','kharn','khârn','ehrlen','ehrelen','darr','surlak','kargos','delvarus','angron','berserker assault','crimson path')
add('\n=== MATCH INDEX ===')
for e in cr.iter():
    nm=(e.get('name') or '').lower(); id_=(e.get('id') or '').lower();
    desc=''
    d=e.find(C('description')) if e.tag==C('rule') else None
    if d is not None and d.text: desc=d.text.lower()
    if any(n in nm or n in id_ or n in desc for n in needles): add(path(e))

add('\n=== TOP-LEVEL WORLD EATERS / XII UNITS ===')
top=cr.find(C('selectionEntries'))
if top is not None:
    for e in top.findall(C('selectionEntry')):
        uid=e.get('id') or ''; nm=e.get('name') or ''; text=(uid+' '+nm).lower()
        if uid.startswith('r41-unit-xii-') or any(n in text for n in needles): dump_unit(e)

add('\n=== WORLD EATERS CONDITIONAL LINKS ON GENERIC CORE UNITS ===')
for uid in ('hq-praetor','hq-centurion','tactical-unit','assault-unit','breacher-unit','veteran-unit','destroyer-unit','hs-heavy-support-squad','command-unit','term-command-unit'):
    u=next((x for x in cr.iter() if x.get('id')==uid),None)
    if u is None: continue
    found=[]
    for x in u.iter():
        xid=(x.get('id') or '').lower(); nm=(x.get('name') or '').lower(); target=(x.get('targetId') or '').lower(); blob=xid+' '+nm+' '+target
        if 'r45-' in xid and ('we-' in xid or any(n in blob for n in ('chainaxe','caedere','world eater'))): found.append(x)
    if found:
        add(f'[{uid} | {u.get("name")}]')
        for x in found:add(path(x)+' | conds='+conditions(x))

add('\n=== XII RITES / FORCE ORG MODIFIERS ===')
for root,name in ((cr,'CAT'),(gr,'GST')):
    for e in root.iter():
        nm=(e.get('name') or '').lower(); id_=e.get('id') or ''
        if ('berserker assault' in nm or 'crimson path' in nm or id_.startswith('r25-rite-xii') or 'r45-we-berserker' in id_):
            add(f'{name}: {e.tag.split("}")[-1]}[{id_}::{e.get("name") or ""}] hidden={e.get("hidden")} field={e.get("field")} value={e.get("value")} target={e.get("targetId")}')

add('\n=== XII SOURCE-ENTRY AGGREGATE / IMPLEMENTATION RISKS ===')
if top is not None:
    for e in top.findall(C('selectionEntry')):
        if not (e.get('id') or '').startswith('r41-unit-xii-'): continue
        for r in e.iter(C('rule')):
            rn=(r.get('name') or ''); d=r.find(C('description')); tx=(d.text or '') if d is not None else ''
            if rn.lower().startswith('source entry') or ('wargear:' in tx.lower() and 'special rules:' in tx.lower()):
                add(f"{e.get('id')} | {e.get('name')} :: AGGREGATE SOURCE RULE: {tx[:1200]}")

add('\n=== LIKELY POINT-THRESHOLD CHARACTER CONSTRAINTS ===')
if top is not None:
    for e in top.findall(C('selectionEntry')):
        if not (e.get('id') or '').startswith('r41-unit-xii-'): continue
        for c in e.findall('./'+C('constraints')+'/'+C('constraint')):
            if c.get('scope')=='roster' or c.get('value') not in (None,'1','1.0'):
                add(f"{e.get('id')} | {e.get('name')} :: {constraints(e)}")

OUT.write_text('\n'.join(L),encoding='utf-8')
print('\n'.join(L[-320:]))
