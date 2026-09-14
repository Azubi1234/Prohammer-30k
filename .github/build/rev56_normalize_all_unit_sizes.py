from pathlib import Path
import xml.etree.ElementTree as ET
import re

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); INDEX=Path('index.xml')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()
parent={c:p for p in cr.iter() for c in p}
report=[]

def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def cost(e):
    cs=e.find(C('costs'))
    return next((x for x in cs.findall(C('cost')) if x.get('typeId')=='pts'),None) if cs is not None else None
def ensure_cost(e,v):
    cs=e.find(C('costs'))
    if cs is None: cs=ET.SubElement(e,C('costs'))
    c=next((x for x in cs.findall(C('cost')) if x.get('typeId')=='pts'),None)
    if c is None: c=ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':fmt(v)})
    else: c.set('value',fmt(v))
    return c
def constraint(e,typ):
    cs=e.find(C('constraints'))
    return next((x for x in cs.findall(C('constraint')) if x.get('type')==typ and x.get('field')=='selections'),None) if cs is not None else None
def ensure_constraint(e,typ,v,suffix):
    c=constraint(e,typ)
    if c is None:
        cs=e.find(C('constraints'))
        if cs is None: cs=ET.SubElement(e,C('constraints'))
        c=ET.SubElement(cs,C('constraint'),{'id':e.get('id')+suffix,'type':typ,'value':fmt(v),'field':'selections','scope':'parent','shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    else: c.set('value',fmt(v))
    return c
def fmt(v):
    f=float(v)
    return str(int(f)) if f.is_integer() else str(f)
def nearest_unit(e):
    x=parent.get(e)
    while x is not None:
        if x.tag==C('selectionEntry') and x.get('type')=='unit': return x
        x=parent.get(x)
    return None
def shift_conditions(child_id,delta,new_child_id=None):
    n=0
    for x in cr.iter():
        if x.get('childId')==child_id and x.get('field')=='selections' and x.get('value') is not None:
            try: x.set('value',fmt(float(x.get('value'))+delta))
            except ValueError: pass
            if new_child_id: x.set('childId',new_child_id)
            n+=1
        elif x.get('childId')==child_id and new_child_id:
            x.set('childId',new_child_id); n+=1
    return n
def remove_entry(e):
    p=parent.get(e)
    assert p is not None
    p.remove(e)

def merge_included_additional(included_id,additional_id,label):
    inc=by_id(included_id); add=by_id(additional_id)
    assert inc is not None and add is not None,(included_id,additional_id)
    u=nearest_unit(inc); assert u is not None
    base=int(float(inc.get('defaultAmount') or constraint(inc,'min').get('value')))
    old_inc_max=int(float(constraint(inc,'max').get('value')))
    extra=int(float(constraint(add,'max').get('value')))
    assert old_inc_max==base,(included_id,base,old_inc_max)
    per=float(cost(add).get('value')); uc=cost(u); assert uc is not None
    old=float(uc.get('value'))
    inc.set('name',label); inc.set('defaultAmount',str(base))
    ensure_constraint(inc,'min',base,'-r56-min'); ensure_constraint(inc,'max',base+extra,'-r56-max')
    ensure_cost(inc,per)
    uc.set('value',fmt(old-base*per))
    shifted=shift_conditions(additional_id,base,included_id)
    remove_entry(add)
    report.append(f'{u.get("name")}: {label} {base}-{base+extra} plus existing fixed squad leader; {per:g} pts/model; minimum cost preserved; {shifted} dependent references migrated.')

def convert_addonly_total(entry_id,base,total_max,label,group_id=None):
    e=by_id(entry_id); assert e is not None,entry_id
    u=nearest_unit(e); assert u is not None,entry_id
    pc=cost(e); uc=cost(u); assert pc is not None and uc is not None,(entry_id,'cost')
    per=float(pc.get('value')); old=float(uc.get('value'))
    e.set('name',label); e.set('type','model'); e.set('defaultAmount',str(base))
    ensure_constraint(e,'min',base,'-r56-min'); ensure_constraint(e,'max',total_max,'-r56-max')
    uc.set('value',fmt(old-base*per))
    shifted=shift_conditions(entry_id,base)
    if group_id:
        g=by_id(group_id); assert g is not None,group_id
        ensure_constraint(g,'min',base,'-r56-min'); ensure_constraint(g,'max',total_max,'-r56-max')
    report.append(f'{u.get("name")}: {label} now shows total {base}-{total_max}; {per:g} pts/model; minimum cost preserved; {shifted} dependent thresholds shifted.')

def merge_existing_model_add(base_id,add_id,label):
    b=by_id(base_id); a=by_id(add_id); assert b is not None and a is not None,(base_id,add_id)
    base=int(float(b.get('defaultAmount') or 1)); extra=int(float(constraint(a,'max').get('value')))
    b.set('name',label); b.set('defaultAmount',str(base))
    ensure_constraint(b,'min',base,'-r56-min'); ensure_constraint(b,'max',base+extra,'-r56-max')
    shifted=shift_conditions(add_id,base,base_id)
    remove_entry(a)
    report.append(f'{nearest_unit(b).get("name")}: {label} {base}-{base+extra}; removed separate Additional counter; {shifted} dependent references migrated.')

# Core squads and every Rite/role clone copied from them.
for args in [
 ('veteran-included','veteran-additional','Legion Veterans'),
 ('terminator-included','terminator-additional','Legion Terminators'),
 ('destroyer-included','destroyer-additional','Legion Destroyers'),
 ('fa-seeker-included','fa-seeker-add','Legion Seekers'),
 ('fa-bike-included','fa-bike-add','Legion Bikers'),
 ('fa-sky-included','fa-sky-add','Legion Sky Hunters'),
 ('r35-pride-veteran-veteran-included','r35-pride-veteran-veteran-additional','Legion Veterans'),
 ('r35-pride-terminator-terminator-included','r35-pride-terminator-terminator-additional','Legion Terminators'),
 ('r35-destroyer-troops-destroyer-included','r35-destroyer-troops-destroyer-additional','Legion Destroyers'),
 ('r35-sky-troops-fa-sky-included','r35-sky-troops-fa-sky-add','Legion Sky Hunters'),
 ('r42-role-v-0-effects-ride-like-the-wind-legion-sky-hunter-jetbike-squadrons-fa-sky-included','r42-role-v-0-effects-ride-like-the-wind-legion-sky-hunter-jetbike-squadrons-fa-sky-add','Legion Sky Hunters'),
 ('r42-role-xiv-0-effects-superior-firepower-legion-veteran-squads-veteran-included','r42-role-xiv-0-effects-superior-firepower-legion-veteran-squads-veteran-additional','Legion Veterans'),
 ('r43-ws-bike-troops-fa-bike-included','r43-ws-bike-troops-fa-bike-add','Legion Bikers'),
 ('r45-dg-bike-fa-bike-included','r45-dg-bike-fa-bike-add','Legion Bikers'),
]: merge_included_additional(*args)

# Honour Guard retinues: 1 fixed Champion + 2-9 Honour Guard = 3-10 total models.
for args in [
 ('hq-praetor-ret-honour-base','hq-praetor-ret-honour-add','Legion Honour Guard'),
 ('r52-ec-eid-honour-hq-praetor-ret-honour-base','r52-ec-eid-honour-hq-praetor-ret-honour-add','Legion Honour Guard'),
 ('r52-ec-ful-honour-hq-praetor-ret-honour-base','r52-ec-ful-honour-hq-praetor-ret-honour-add','Legion Honour Guard'),
]: merge_included_additional(*args)

# Entries that previously represented only the number added beyond an implicit included base.
for args in [
 ('hs-hss-additional',5,10,'Squad Models',None),
 ('r42-role-xiv-0-legion-heavy-support-squads-hs-hss-additional',5,10,'Squad Models',None),
 ('r52-ec-sonic-hss-hs-hss-additional',5,10,'Squad Models',None),
 ('r40-da-eskaton-interemptor-da22-int-extra',5,15,'Interemptors','r40-da-eskaton-interemptor-da22-int-extra-g'),
 ('da22-dwtc-extra',5,10,'Terminator Companions','da22-dwtc-extra-g'),
 ('da22-cen-extra',5,10,'Knight Cenobites','da22-cen-extra-g'),
 ('r30-prae-castellax-extra',1,5,'Castellax Battle-Automata',None),
 ('r30-prae-vorax-extra',1,6,'Vorax Battle-Automata',None),
]: convert_addonly_total(*args)

# Artillery squadrons: 1-3 vehicles, all one type. The base model already carries the first model's cost.
for args in [
 ('hs-art-whirlwind','hs-art-whirlwind-additional','Legion Whirlwinds'),
 ('hs-art-basilisk','hs-art-basilisk-additional','Legion Basilisks'),
 ('hs-art-medusa','hs-art-medusa-additional','Legion Medusas'),
 ('r42-role-iv-1-legion-artillery-tank-squadron-hs-art-whirlwind','r42-role-iv-1-legion-artillery-tank-squadron-hs-art-whirlwind-additional','Legion Whirlwinds'),
 ('r42-role-iv-1-legion-artillery-tank-squadron-hs-art-basilisk','r42-role-iv-1-legion-artillery-tank-squadron-hs-art-basilisk-additional','Legion Basilisks'),
 ('r42-role-iv-1-legion-artillery-tank-squadron-hs-art-medusa','r42-role-iv-1-legion-artillery-tank-squadron-hs-art-medusa-additional','Legion Medusas'),
]: merge_existing_model_add(*args)

# Land Raider Battle Squadron is 1-3 mixed Phobos/Proteus, with max one Achilles.
# Give the entry a real starting model while keeping the mixed-pattern group min/max 1-3.
lr_ph=by_id('hs-lr-phobos'); lr_pr=by_id('hs-lr-proteus'); lr_ac=by_id('hs-lr-achilles'); lr_g=by_id('hs-lr-patterns')
assert all(x is not None for x in (lr_ph,lr_pr,lr_ac,lr_g))
lr_ph.set('defaultAmount','1'); ensure_constraint(lr_ph,'max',3,'-r56-max')
ensure_constraint(lr_g,'min',1,'-r56-min'); ensure_constraint(lr_g,'max',3,'-r56-max')
report.append('Legion Land Raider Battle Squadron: now opens with 1 Phobos by default; mixed pattern group remains 1-3 total, Achilles max 1.')

# Revisions/index.
cr.set('revision','56'); cr.set('gameSystemRevision','26'); gr.set('revision','26')
comment=cr.find(C('comment'))
if comment is not None: comment.text='Revision 56: catalogue-wide squad-size normalization. Actual starting model counts are displayed; legacy Additional model counters removed from core units, Rites, retinues and vehicle squadrons.'
ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
ET.register_namespace('',GNS); gt.write(GST,encoding='UTF-8',xml_declaration=True)
idx=INDEX.read_text(encoding='utf-8')
idx=re.sub(r'(dataType="gamesystem"[^>]*dataRevision=")\d+("/>)',r'\g<1>26\2',idx)
idx=re.sub(r'(dataType="catalogue"[^>]*dataRevision=")\d+("/>)',r'\g<1>56\2',idx)
INDEX.write_text(idx,encoding='utf-8')

# Hard validation of references/ids/namespaces.
cat_ids=[e.get('id') for e in cr.iter() if e.get('id')]; gst_ids=[e.get('id') for e in gr.iter() if e.get('id')]
assert len(cat_ids)==len(set(cat_ids)),'duplicate CAT IDs'; assert len(gst_ids)==len(set(gst_ids)),'duplicate GST IDs'
catset=set(cat_ids); gstset=set(gst_ids)
for root,own,other,label in [(cr,catset,gstset,'CAT'),(gr,gstset,catset,'GST')]:
    broken=[]
    for x in root.iter():
        for a in ('targetId','childId'):
            v=x.get(a)
            if v and v not in own and v not in other: broken.append((x.get('id'),a,v))
    assert not broken,f'{label} broken refs: {broken[:30]}'
text=CAT.read_text(encoding='utf-8'); gsttext=GST.read_text(encoding='utf-8')
assert '<ns0:' not in text and '<ns0:' not in gsttext
assert '<catalogue xmlns="http://www.battlescribe.net/schema/catalogueSchema"' in text
assert '<gameSystem xmlns="http://www.battlescribe.net/schema/gameSystemSchema"' in gsttext

# No remaining genuine visible squad-size entry may be named Additional ... .
allowed_additional_prefixes=('Additional Armoury','Additional Wargear','Additional Weapon')
remaining=[]
for e in cr.iter(C('selectionEntry')):
    nm=(e.get('name') or '').strip()
    if nm.startswith('Additional ') and not nm.startswith(allowed_additional_prefixes):
        mx=constraint(e,'max')
        if mx is not None and float(mx.get('value','0'))>1: remaining.append((e.get('id'),nm,e.get('type'),mx.get('value')))
assert not remaining,f'Remaining possible Additional-model counters: {remaining}'

# Source-backed caps for all structures changed in this pass.
checks={
 'veteran-included':(4,9),'terminator-included':(4,9),'destroyer-included':(4,9),'fa-seeker-included':(4,9),
 'fa-bike-included':(2,9),'fa-sky-included':(2,9),'hs-hss-additional':(5,10),
 'r30-prae-castellax-extra':(1,5),'r30-prae-vorax-extra':(1,6),
 'da22-dwtc-extra':(5,10),'da22-cen-extra':(5,10),'r40-da-eskaton-interemptor-da22-int-extra':(5,15)
}
for iid,(mn,mx) in checks.items():
    e=by_id(iid); assert e is not None,iid
    assert int(float(e.get('defaultAmount')))==mn,(iid,e.get('defaultAmount'),mn)
    assert int(float(constraint(e,'min').get('value')))==mn,(iid,'min')
    assert int(float(constraint(e,'max').get('value')))==mx,(iid,'max')

Path('inspection-r56-catalogue-unit-sizes.txt').write_text('\n'.join(report)+f'\n\nValidated {sum(1 for e in cr.find(C("selectionEntries")) if e.get("type")=="unit")} top-level catalogue units.\nNo legacy Additional-model quantity counters remain.\nSource-backed core/DA/Praevian caps asserted. CAT56/GST26; canonical namespaces; no duplicate IDs; no broken references.\n',encoding='utf-8')
print('\n'.join(report)); print('REVISION 56 HARD VALIDATION PASSED')
