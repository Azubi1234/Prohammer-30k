from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); OUT=Path('inspection-r71-night-lords-diagnostic.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot(); PM={c:p for p in cr.iter() for c in p}
L=[]; add=L.append

def cost(e): return ','.join(c.get('value','') for c in e.findall('./'+C('costs')+'/'+C('cost')))
def cons(e):
    return '; '.join(f"{x.get('type')}={x.get('value')} field={x.get('field')} scope={x.get('scope')} child={x.get('childId')}" for x in e.findall('./'+C('constraints')+'/'+C('constraint')))
def cats(e):
    return ', '.join((x.get('name') or x.get('targetId') or '') for x in e.findall('./'+C('categoryLinks')+'/'+C('categoryLink')) if x.get('primary')=='true' or True)
def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def owner(e):
    p=e
    while p is not None and p.tag!=C('selectionEntry'): p=PM.get(p)
    return p

def dump_entry(e,depth=0,maxdepth=4):
    ind='  '*depth
    add(f"{ind}{e.tag.split('}')[-1]} {e.get('id')} | {e.get('name')} | type={e.get('type')} hidden={e.get('hidden')} cost={cost(e)} | {cons(e)}")
    if depth>=maxdepth:return
    for cont in ('selectionEntries','selectionEntryGroups','entryLinks'):
        q=e.find(C(cont))
        if q is None: continue
        add(ind+'  '+cont+':')
        for x in list(q): dump_entry(x,depth+2,maxdepth)

add(f"CAT revision={cr.get('revision')} GST revision={gr.get('revision')} GSTref={cr.get('gameSystemRevision')}")
add('\n=== NIGHT LORDS UNIQUE / CHARACTER / PRIMARCH ENTRIES ===')
needles=('terror squad','night raptor','contekar','atramentar','sevatar','ophion','malcharion','shang','mawdrym','curze','night haunter')
top=cr.find(C('selectionEntries'))
for e in (list(top) if top is not None else []):
    n=(e.get('name') or '').lower()
    if any(k in n for k in needles):
        add('\n'+'-'*100); add(f"TOP {e.get('id')} | {e.get('name')} | cats={cats(e)}")
        dump_entry(e,0,5)
        for r in e.iter(C('rule')):
            d=r.find(C('description')); txt=(d.text or '') if d is not None else ''
            add(f"  RULE {r.get('id')} | {r.get('name')} :: {txt[:600]}")
        for p in e.iter(C('profile')):
            vals=[]
            for c in p.findall('./'+C('characteristics')+'/'+C('characteristic')): vals.append(f"{c.get('name')}={c.text}")
            add(f"  PROFILE {p.get('name')} [{p.get('typeName')}] :: {'; '.join(vals)}")

add('\n=== NIGHT LORDS SHARED ARMOURY OBJECTS ===')
for ident in ('r44-nl-chainglaive','r44-nl-trophies','r44-nl-stealth-ic','r44-nl-stealth-unit','r44-nl-kraken-bolts','r44-nl-transponder-character','r44-nl-transponder-unit'):
    e=byid(cr,ident); add(f"{ident}: {'MISSING' if e is None else e.get('name')+' cost='+cost(e)}")
    if e is not None:
        for r in e.iter(C('rule')):
            d=r.find(C('description')); add('  '+r.get('name')+': '+((d.text or '') if d is not None else ''))

add('\n=== OWNERS / LINKS OF NIGHT LORDS ARMOURY ITEMS ===')
targets={'r44-nl-chainglaive','r44-nl-trophies','r44-nl-stealth-ic','r44-nl-stealth-unit','r44-nl-kraken-bolts','r44-nl-transponder-character','r44-nl-transponder-unit'}
for x in cr.iter(C('entryLink')):
    if x.get('targetId') in targets:
        o=owner(x); add(f"{o.get('id') if o is not None else '?'} | {o.get('name') if o is not None else '?'} :: LINK {x.get('id')} {x.get('name')} -> {x.get('targetId')} hidden={x.get('hidden')} {cons(x)}")
        for m in x.findall('./'+C('modifiers')+'/'+C('modifier')):
            add(f"  MOD {m.get('id')} type={m.get('type')} field={m.get('field')} value={m.get('value')}")
            for c in m.iter(C('condition')): add(f"    COND {c.get('type')} {c.get('value')} scope={c.get('scope')} child={c.get('childId')} field={c.get('field')}")

add('\n=== NIGHT LORDS RITES / ROLE CLONES ===')
for e in cr.iter(C('selectionEntry')):
    n=(e.get('name') or '').lower(); i=e.get('id') or ''
    if ('terror assault' in n or 'horror cult' in n or ('troops' in n and any(k in n for k in ('terror squad','night raptor'))) or 'r25-rite-viii' in i or 'r42-' in i and any(k in n for k in ('terror','raptor'))):
        add(f"{i} | {e.get('name')} | cats={cats(e)} hidden={e.get('hidden')} cost={cost(e)} {cons(e)}")
        for m in e.findall('./'+C('modifiers')+'/'+C('modifier')):
            for c in m.iter(C('condition')): add(f"  MODCOND {c.get('type')} {c.get('value')} scope={c.get('scope')} child={c.get('childId')}")

add('\n=== GST NIGHT LORDS / RITE MODIFIERS ===')
for m in gr.iter(G('modifier')):
    text=' '.join(str(m.get(k) or '') for k in ('id','field','value'))
    conds=list(m.iter(G('condition')))
    if 'nl-' in text or any((c.get('childId') or '').startswith('r25-rite-viii') or c.get('childId')=='legion-viii' for c in conds):
        add(f"MOD {m.get('id')} type={m.get('type')} field={m.get('field')} value={m.get('value')}")
        for c in conds: add(f"  COND {c.get('type')} {c.get('value')} scope={c.get('scope')} child={c.get('childId')} field={c.get('field')}")

add('\n=== SERGEANT / UNIT CANDIDATES ===')
for e in (list(top) if top is not None else []):
    n=(e.get('name') or '')
    if any(k in n.lower() for k in ('tactical squad','assault squad','breacher','reconnaissance','veteran squad','seeker','heavy support squad','destroyer','command squad','honour guard','apothecarion','techmarine','rapier','night raptor','terror squad')):
        models=[x for x in e.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if x.get('type')=='model']
        add(f"{e.get('id')} | {n} | cats={cats(e)} | models="+'; '.join(f"{x.get('id')}:{x.get('name')} default={x.get('defaultAmount')} {cons(x)}" for x in models))

OUT.write_text('\n'.join(L),encoding='utf-8')
print('\n'.join(L[-250:]))
