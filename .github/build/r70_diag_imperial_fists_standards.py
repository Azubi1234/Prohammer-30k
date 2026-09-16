from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat')
OUT=Path('inspection-r70-if-standards-diagnostic-compact.txt')
NS='http://www.battlescribe.net/schema/catalogueSchema'
C=lambda t:f'{{{NS}}}{t}'
root=ET.parse(CAT).getroot()
PM={c:p for p in root.iter() for c in p}
L=[]
def add(s=''): L.append(s)
def by_id(i): return next((e for e in root.iter() if e.get('id')==i),None)
def owner_entry(e):
    p=e
    while p is not None and p.tag!=C('selectionEntry'): p=PM.get(p)
    return p

def cost(e):
    return ','.join((c.get('value') or '') for c in e.findall('./'+C('costs')+'/'+C('cost')))
def cons(e):
    out=[]
    for c in e.findall('./'+C('constraints')+'/'+C('constraint')):
        out.append(f"{c.get('type')}={c.get('value')} field={c.get('field')} scope={c.get('scope')}")
    return '; '.join(out)
def children(g):
    for x in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')):
        add(f"    ENTRY {x.get('id')} | {x.get('name')} | cost={cost(x)} | {cons(x)}")
    for x in g.findall('./'+C('entryLinks')+'/'+C('entryLink')):
        add(f"    LINK {x.get('id')} | {x.get('name')} -> {x.get('targetId')} | {cons(x)}")

def groups_of(entry, needles=None):
    if entry is None: return
    add(f"ENTRY {entry.get('id')} | {entry.get('name')}")
    for g in entry.iter(C('selectionEntryGroup')):
        n=g.get('name') or ''
        if needles is None or any(q.lower() in n.lower() for q in needles):
            add(f"  GROUP {g.get('id')} | {n} | {cons(g)}")
            children(g)

add(f"CAT revision {root.get('revision')} GST ref {root.get('gameSystemRevision')}")
add('\n=== PRAETOR/CENTURION ARMOURY + WEAPONS ===')
for i in ('hq-praetor','hq-centurion'):
    groups_of(by_id(i),['armour','weapon','wargear'])

add('\n=== GENERIC SERGEANT / RETINUE ARMOURY CANDIDATES ===')
for i in ('tactical-unit','breacher-unit','veteran-unit','terminator-unit','hq-centurion-ret-command','hq-praetor-ret-termcommand','hq-praetor-ret-honour'):
    groups_of(by_id(i),['armour','weapon','sergeant','character','wargear'])

add('\n=== ALL ARMOURY GROUP OWNERS RELEVANT TO GENERIC MARINES ===')
seen=set()
for g in root.iter(C('selectionEntryGroup')):
    n=(g.get('name') or '')
    if 'armoury' not in n.lower(): continue
    o=owner_entry(g)
    if o is None: continue
    on=o.get('name') or ''
    if any(k in on.lower() for k in ('praetor','centurion','sergeant','terminator','command squad','honour guard','veteran','tactical','breacher')):
        key=(o.get('id'),g.get('id'))
        if key in seen: continue
        seen.add(key)
        add(f"OWNER {o.get('id')} | {on} :: GROUP {g.get('id')} | {n} | {cons(g)}")
        children(g)

add('\n=== LAND RAIDER PATTERN STRUCTURE ===')
lr=by_id('hs-land-raider')
groups_of(lr,['land raider pattern','pattern','transport'])
if lr is not None:
    for e in lr.iter(C('selectionEntry')):
        if any(k in (e.get('name') or '').lower() for k in ('phobos','proteus','achilles','crusader')):
            add(f"  LR ENTRY {e.get('id')} | {e.get('name')} | cost={cost(e)} | {cons(e)}")
            for r in e.iter(C('rule')):
                d=r.find(C('description'))
                txt=(d.text or '') if d is not None else ''
                if 'transport' in (r.get('name') or '').lower() or 'capacity' in txt.lower(): add(f"    RULE {r.get('name')}: {txt[:500]}")

add('\n=== HAMMERFALL GENERIC INFANTRY CANDIDATES ===')
for ident in ('tactical-unit','assault-unit','breacher-unit','recon-unit','veteran-unit','terminator-unit','destroyer-unit','techmarine-covenant','rapier-unit','fa-seeker','hs-heavy-support-squad','hq-centurion-ret-command','hq-praetor-ret-termcommand','hq-praetor-ret-honour'):
    e=by_id(ident)
    if e is None: add(f"{ident} | MISSING"); continue
    # collect rules/profiles text hints for unit type
    hints=[]
    for r in e.iter(C('rule')):
        nm=r.get('name') or ''
        d=r.find(C('description')); tx=(d.text or '') if d is not None else ''
        if 'unit type' in nm.lower() or 'infantry' in tx.lower() or 'artillery' in tx.lower(): hints.append((nm+': '+tx)[:220])
    add(f"{ident} | {e.get('name')} | hints={' || '.join(hints[:3])}")

add('\n=== IMPERIAL FISTS KNOWN GAP STRUCTURES ===')
for ident in ('r41-unit-vii-0-templar-brethren-squad','r41-unit-vii-1-phalanx-warder-squad','r41-unit-vii-2-huscarl-terminator-retinue','r41-unit-vii-3-tarantula-sentry-gun-battery','r64-if-templar-troops'):
    e=by_id(ident)
    if e is None: add(f'{ident} MISSING'); continue
    add(f"{ident} | {e.get('name')}")
    for g in e.findall('.//'+C('selectionEntryGroup')):
        if any(k in (g.get('name') or '').lower() for k in ('armoury','replacement','weapon','transport')):
            add(f"  GROUP {g.get('id')} | {g.get('name')} | {cons(g)}"); children(g)

OUT.write_text('\n'.join(L),encoding='utf-8')
print('\n'.join(L))
