from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); OUT=Path('inspection-r74-blood-angels-diag.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot(); PM={c:p for p in cr.iter() for c in p}
L=[]; a=L.append

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def cons(e,T=C):
    out=[]
    cs=e.find(T('constraints'))
    if cs is not None:
        for c in cs.findall(T('constraint')): out.append(f"{c.get('id')}:{c.get('type')}={c.get('value')} field={c.get('field')} scope={c.get('scope')}")
    return '; '.join(out)
def cats(e):
    out=[]; cs=e.find(C('categoryLinks'))
    if cs is not None:
        for c in cs.findall(C('categoryLink')): out.append((c.get('name'),c.get('targetId'),c.get('primary')))
    return out
def cost(e):
    cs=e.find(C('costs'))
    if cs is None:return ''
    return ','.join((x.get('value') or '') for x in cs.findall(C('cost')))
def owner(e):
    p=e
    while p is not None:
        if p.tag==C('selectionEntry') and p.get('type')=='unit': return p
        p=PM.get(p)
    return None
def dump_unit(u):
    a(f"\n=== UNIT {u.get('id')} | {u.get('name')} | type={u.get('type')} hidden={u.get('hidden')} cost={cost(u)} cats={cats(u)} ===")
    for p in u.findall('./'+C('profiles')+'/'+C('profile')):
        a(f"PROFILE {p.get('id')} | {p.get('name')} | {p.get('typeName')}")
    rs=u.find(C('rules'))
    if rs is not None:
        for r in rs.findall(C('rule')):
            d=r.find(C('description')); tx=(d.text or '') if d is not None else ''
            a(f"RULE {r.get('id')} | {r.get('name')} :: {tx[:700]}")
    for g in u.iter(C('selectionEntryGroup')):
        n=g.get('name') or ''
        if any(k in n.lower() for k in ('option','armoury','weapon','wargear','transport','retinue','jump','upgrade')):
            a(f"GROUP {g.get('id')} | {n} | {cons(g)}")
            for x in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')):
                a(f"  ENTRY {x.get('id')} | {x.get('name')} | type={x.get('type')} cost={cost(x)} | {cons(x)}")
            for x in g.findall('./'+C('entryLinks')+'/'+C('entryLink')):
                a(f"  LINK {x.get('id')} | {x.get('name')} -> {x.get('targetId')} | {cons(x)}")
    # list suspicious source-entry or aggregate rules anywhere below
    for r in u.iter(C('rule')):
        n=(r.get('name') or '').lower()
        if 'source entry' in n or n=='special rules' or n=='wargear':
            d=r.find(C('description')); a(f"SUSPECT RULE {r.get('id')} | {r.get('name')} :: {((d.text or '') if d is not None else '')[:500]}")

# Current BA imported package: all r41 IX source entries plus known-named entries by name.
known=('dawnbreaker','crimson paladin','angel\'s tears','angels tears','ofanim','grav chariot','sanguinary guard','raldoron','dominion zephon','aster crohne','azkaellon','nassir amit','sanguinius')
seen=set()
for u in cr.iter(C('selectionEntry')):
    if u.get('type')!='unit': continue
    i=(u.get('id') or '').lower(); n=(u.get('name') or '').lower()
    if 'r41-unit-ix-' in i or any(k in n for k in known):
        if u.get('id') not in seen:
            seen.add(u.get('id')); dump_unit(u)

# BA shared armoury/options and every owner/link.
a('\n=== BLOOD ANGELS SHARED / LINKED OBJECTS ===')
for e in cr.iter():
    i=(e.get('id') or '').lower(); n=(e.get('name') or '').lower()
    if 'r44-ba-' in i or 'blood angels' in n or any(k in n for k in ('death mask','inferno pistol','blade of perdition','over-charged engines','furioso-pattern jump pack','sanguinary high priest')):
        if e.tag in (C('selectionEntry'),C('entryLink'),C('selectionEntryGroup')):
            o=owner(e); a(f"{e.tag.split('}')[-1]} {e.get('id')} | {e.get('name')} target={e.get('targetId')} hidden={e.get('hidden')} cost={cost(e) if e.tag!=C('entryLink') else ''} owner={o.get('name') if o is not None else ''} | {cons(e)}")

# Rites and role clones.
a('\n=== BLOOD ANGELS RITES ===')
for rid in ('r25-rite-ix-0-the-day-of-revelation','r25-rite-ix-1-the-day-of-sorrows'):
    e=byid(cr,rid); a(f"RITE {rid} -> {e.get('name') if e is not None else 'MISSING'}")
    if e is not None:
        for r in e.iter(C('rule')):
            d=r.find(C('description')); a(f"  RULE {r.get('name')} :: {((d.text or '') if d is not None else '')[:900]}")
for u in cr.iter(C('selectionEntry')):
    i=(u.get('id') or '').lower(); n=(u.get('name') or '').lower()
    if ('r44-ba' in i or 'day of revelation' in n or 'day of sorrows' in n) and u.get('type')=='unit':
        a(f"ROLE UNIT {u.get('id')} | {u.get('name')} hidden={u.get('hidden')} cats={cats(u)}")
        for m in u.findall('./'+C('modifiers')+'/'+C('modifier')):
            a(f"  MOD {m.get('id')} type={m.get('type')} field={m.get('field')} value={m.get('value')}")
            for c in m.findall('.//'+C('condition')): a(f"    COND {c.get('type')} {c.get('value')} scope={c.get('scope')} child={c.get('childId')}")

# GST FOC and BA modifiers.
a('\n=== GST STANDARD FOC / BA MODIFIERS ===')
force=byid(gr,'force-standard')
if force is not None:
    for l in force.findall('.//'+G('categoryLink')):
        if l.get('targetId') in ('cat-hq','cat-troops','cat-elites','cat-fast','cat-heavy'):
            a(f"FOC {l.get('id')} {l.get('name')} -> {l.get('targetId')}")
            for c in l.findall('./'+G('constraints')+'/'+G('constraint')): a(f"  CON {c.get('id')} {c.get('type')}={c.get('value')}")
            for m in l.findall('./'+G('modifiers')+'/'+G('modifier')):
                conds=[(c.get('type'),c.get('value'),c.get('scope'),c.get('childId')) for c in m.findall('.//'+G('condition'))]
                if any((x[3] or '').startswith('r25-rite-ix') or x[3]=='legion-ix' for x in conds): a(f"  BA MOD {m.get('id')} type={m.get('type')} field={m.get('field')} value={m.get('value')} conds={conds}")
for ce in gr.iter(G('categoryEntry')):
    if 'blood' in (ce.get('name') or '').lower() or 'revelation' in (ce.get('name') or '').lower() or 'sorrow' in (ce.get('name') or '').lower(): a(f"GST CAT {ce.get('id')} | {ce.get('name')} hidden={ce.get('hidden')}")

OUT.write_text('\n'.join(L),encoding='utf-8'); print('\n'.join(L))
