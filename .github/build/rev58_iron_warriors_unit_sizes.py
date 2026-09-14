from pathlib import Path
import xml.etree.ElementTree as ET
import re

CAT=Path('Legiones Astartes.cat'); INDEX=Path('index.xml')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot()
parent={c:p for p in cr.iter() for c in p}
report=[]

def cost(e):
    cs=e.find(C('costs'))
    return next((x for x in cs.findall(C('cost')) if x.get('typeId')=='pts'),None) if cs is not None else None

def constraint(e,typ):
    cs=e.find(C('constraints'))
    return next((x for x in cs.findall(C('constraint')) if x.get('type')==typ and x.get('field')=='selections'),None) if cs is not None else None

def ensure_constraint(e,typ,v,suffix):
    c=constraint(e,typ)
    if c is None:
        cs=e.find(C('constraints'))
        if cs is None: cs=ET.SubElement(e,C('constraints'))
        c=ET.SubElement(cs,C('constraint'),{'id':e.get('id')+suffix,'type':typ,'value':str(v),'field':'selections','scope':'parent','shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    else:c.set('value',str(v))
    return c

def nearest_unit(e):
    x=parent.get(e)
    while x is not None:
        if x.tag==C('selectionEntry') and x.get('type')=='unit': return x
        x=parent.get(x)
    return None

def shift_conditions(child_id,delta):
    n=0
    for x in cr.iter():
        if x.get('childId')==child_id and x.get('field')=='selections' and x.get('value') is not None:
            try:
                x.set('value',str(int(float(x.get('value'))+delta)))
                n+=1
            except ValueError: pass
    return n

def set_parent_points(u,newv):
    c=cost(u); assert c is not None,u.get('id')
    c.set('value',str(int(newv) if float(newv).is_integer() else newv))

# Revision 57 rebuilt these entries but accidentally reintroduced the old
# implicit-base + "Additional ..." UI.  Convert every occurrence, including
# nested retinue clones, to the project-wide total-model standard.
SPECS={
    'Additional Tyrant Siege Terminator':(5,10,'Tyrant Siege Terminators'),
    'Additional Iron Havoc':(5,10,'Iron Havocs'),
    'Additional Dominator':(5,10,'Dominator Cohort Models'),
    'Additional Domitar-Ferrum':(1,6,'Domitar-Ferrum Battle-Automata'),
}

changed=0
for e in list(cr.iter(C('selectionEntry'))):
    nm=(e.get('name') or '').strip()
    if nm not in SPECS: continue
    base,total_max,label=SPECS[nm]
    mx=constraint(e,'max'); pc=cost(e); u=nearest_unit(e)
    assert mx is not None and pc is not None and u is not None,(e.get('id'),nm)
    per=float(pc.get('value')); old=float(cost(u).get('value'))
    e.set('name',label); e.set('type','model'); e.set('defaultAmount',str(base))
    ensure_constraint(e,'min',base,'-r58-min'); ensure_constraint(e,'max',total_max,'-r58-max')
    # Move the included models' cost from the parent into the visible model counter.
    set_parent_points(u,old-base*per)
    shifted=shift_conditions(e.get('id'),base)
    report.append(f'{u.get("name")}: {nm} -> {label} {base}-{total_max}; {per:g} pts/model; parent minimum preserved; shifted {shifted} model-count conditions.')
    changed+=1

assert changed>=4, f'Expected at least four Iron Warriors counters, changed {changed}'

# Hard guard: no legacy Additional-model quantity may remain anywhere in the catalogue.
legacy=[]
for e in cr.iter(C('selectionEntry')):
    nm=(e.get('name') or '').strip()
    if not nm.startswith('Additional ') or nm.startswith(('Additional Armoury','Additional Wargear','Additional Weapon')): continue
    mx=constraint(e,'max')
    if mx is not None and float(mx.get('value','0'))>1: legacy.append((e.get('id'),nm,mx.get('value')))
assert not legacy, f'Legacy Additional-model counters remain: {legacy[:20]}'

# Explicit source-backed Iron Warriors checks, including any nested clone.
for e in cr.iter(C('selectionEntry')):
    nm=(e.get('name') or '').strip()
    if nm not in {v[2] for v in SPECS.values()}: continue
    spec=next(v for v in SPECS.values() if v[2]==nm)
    base,total_max,_=spec
    assert e.get('defaultAmount')==str(base),(e.get('id'),nm,'default')
    assert constraint(e,'min') is not None and int(float(constraint(e,'min').get('value')))==base,(e.get('id'),nm,'min')
    assert constraint(e,'max') is not None and int(float(constraint(e,'max').get('value')))==total_max,(e.get('id'),nm,'max')

cr.set('revision','58')
comment=cr.find(C('comment'))
if comment is not None: comment.text='Revision 58: Iron Warriors squad-size repair. Tyrants, Iron Havocs, Dominators and Iron Circle now display actual starting unit size rather than Additional-model counters.'
ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
idx=INDEX.read_text(encoding='utf-8')
idx=re.sub(r'(dataType="catalogue"[^>]*dataRevision=")\d+("/>)',r'\g<1>58\2',idx)
INDEX.write_text(idx,encoding='utf-8')

# Namespace/ID/reference sanity.
text=CAT.read_text(encoding='utf-8')
assert '<ns0:' not in text
assert '<catalogue xmlns="http://www.battlescribe.net/schema/catalogueSchema"' in text
ids=[x.get('id') for x in cr.iter() if x.get('id')]
assert len(ids)==len(set(ids)),'duplicate catalogue IDs'
idset=set(ids)
broken=[]
for x in cr.iter():
    if x.tag==C('entryLink') and x.get('targetId') and x.get('targetId') not in idset: broken.append((x.get('id'),x.get('targetId')))
assert not broken,f'broken catalogue entryLinks: {broken[:20]}'

report.append(f'Converted {changed} Iron Warriors Additional-model counters; zero legacy quantity counters remain catalogue-wide.')
Path('inspection-r58-iron-warriors-unit-sizes.txt').write_text('\n'.join(report)+'\n',encoding='utf-8')
print('\n'.join(report))
