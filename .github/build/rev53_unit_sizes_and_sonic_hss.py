from pathlib import Path
import xml.etree.ElementTree as ET
import re

# Revision 53: display total squad size, not only additional models.
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); INDEX=Path('index.xml')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()
top=cr.find(C('selectionEntries')); assert top is not None
REPORT=[]
def note(s): REPORT.append(s); print(s)
def ensure(p,tag):
    x=p.find(C(tag))
    if x is None:x=ET.SubElement(p,C(tag))
    return x
def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def points(e):
    cs=e.find(C('costs'))
    if cs is None:return None
    return next((c for c in cs.findall(C('cost')) if c.get('typeId')=='pts'),None)
def source_text(e):
    rs=e.find(C('rules'))
    if rs is None:return ''
    for r in rs.findall(C('rule')):
        if (r.get('name') or '').lower()=='source entry':
            d=r.find(C('description')); return (d.text or '') if d is not None else ''
    return ''
def base_count_from_source(txt):
    if not txt or 'Unit Composition:' not in txt:return None
    part=txt.split('Unit Composition:',1)[1]
    stops=['Unit Type:','Wargear:','Special Rules:','Dedicated Transport:','OPTIONS','Options','RESTRICTIONS','Restrictions']
    end=len(part)
    for s in stops:
        i=part.find(s)
        if i>=0:end=min(end,i)
    block=part[:end]
    nums=[int(x) for x in re.findall(r'[•\-]\s*(\d+)\s+',block)]
    return sum(nums) if nums else None

def direct_additional(e):
    ses=e.find(C('selectionEntries'))
    if ses is None:return None
    return next((s for s in ses.findall(C('selectionEntry')) if (s.get('name') or '').strip().lower()=='additional model'),None)
def max_constraint(e):
    cs=e.find(C('constraints'))
    if cs is None:return None
    return next((c for c in cs.findall(C('constraint')) if c.get('type')=='max' and c.get('field')=='selections'),None)
def min_constraint(e):
    cs=e.find(C('constraints'))
    if cs is None:return None
    return next((c for c in cs.findall(C('constraint')) if c.get('type')=='min' and c.get('field')=='selections'),None)

BASE_OVERRIDES={
 'r41-unit-iii-0-palatine-blade-squad':5,
 'r41-unit-iii-1-phoenix-terminator-squad':5,
 'r41-unit-iii-2-kakophoni-squad':6,
 'r41-unit-iii-3-sun-killer-squad':5,
}
converted=[]; unresolved=[]
for unit in list(top):
    add=direct_additional(unit)
    if add is None:continue
    base=BASE_OVERRIDES.get(unit.get('id')) or base_count_from_source(source_text(unit))
    mx=max_constraint(add); pc=points(add); up=points(unit)
    if base is None or mx is None or pc is None or up is None:
        unresolved.append((unit.get('id'),unit.get('name'),base,mx is not None,pc is not None,up is not None)); continue
    extra=int(float(mx.get('value','0'))); per=float(pc.get('value','0')); base_cost=float(up.get('value','0')); total=base+extra
    add.set('name','Squad Models'); add.set('defaultAmount',str(base)); mx.set('value',str(total))
    mn=min_constraint(add)
    if mn is None:
        cs=ensure(add,'constraints')
        ET.SubElement(cs,C('constraint'),{'id':add.get('id')+'-min-total','type':'min','value':str(base),'field':'selections','scope':'parent','shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    else: mn.set('value',str(base))
    up.set('value',str(base_cost - base*per))
    rs=add.find(C('rules'))
    if rs is not None:
        for r in list(rs):
            if (r.get('name') or '').lower()=='additional model':rs.remove(r)
        if len(rs)==0:add.remove(rs)
    converted.append((unit.get('name'),base,total,per,base_cost))

sonic=by_id('r52-ec-sonic-hss')
if sonic is None:
    sonic=next((e for e in list(top) if 'sonic weaponry' in (e.get('name') or '').lower() and 'heavy support' in (e.get('name') or '').lower()),None)
if sonic is not None:
    sgs=ensure(sonic,'selectionEntryGroups')
    for g in list(sgs):
        if g.get('id')=='r53-ec-sonic-weapons':sgs.remove(g)
    g=ET.SubElement(sgs,C('selectionEntryGroup'),{'id':'r53-ec-sonic-weapons','name':'Sonic Heavy Weapons','hidden':'false','collective':'false','import':'true'})
    cs=ET.SubElement(g,C('constraints')); ET.SubElement(cs,C('constraint'),{'id':'r53-ec-sonic-weapons-max','type':'max','value':'4','field':'selections','scope':'parent','shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    ses=ET.SubElement(g,C('selectionEntries'))
    for iid,name,cost,desc in [
        ('r53-ec-sonic-blaster','Sonic Blaster',15,'Replace one model’s normal Heavy Weapon with a Sonic Blaster.'),
        ('r53-ec-doom-siren','Doom Siren',20,'Replace one model’s normal Heavy Weapon with a Doom Siren.'),
        ('r53-ec-blastmaster','Blastmaster',35,'Replace one model’s normal Heavy Weapon with a Blastmaster.'),
    ]:
        s=ET.SubElement(ses,C('selectionEntry'),{'id':iid,'name':name,'type':'upgrade','hidden':'false','import':'true'})
        c=ET.SubElement(s,C('constraints')); ET.SubElement(c,C('constraint'),{'id':iid+'-max','type':'max','value':'4','field':'selections','scope':'parent','shared':'true','includeChildSelections':'true','includeChildForces':'false'})
        costs=ET.SubElement(s,C('costs')); ET.SubElement(costs,C('cost'),{'name':'Points','typeId':'pts','value':str(cost)})
        rules=ET.SubElement(s,C('rules')); r=ET.SubElement(rules,C('rule'),{'id':iid+'-rule','name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=desc
    note('Sonic Weaponry Heavy Support Squad: restored Sonic Blaster, Doom Siren and Blastmaster choices, maximum four total.')
else: note('WARNING: Sonic Weaponry Heavy Support Squad not found.')

cr.set('revision','53'); cr.set('gameSystemRevision','23'); gr.set('revision','23')
comment=cr.find(C('comment'))
if comment is not None:comment.text='Revision 53: total squad-size counters replace Additional model entries; Emperor’s Children Sonic Heavy Support weapon choices restored.'
ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
ET.register_namespace('',GNS); gt.write(GST,encoding='UTF-8',xml_declaration=True)
idx=INDEX.read_text(encoding='utf-8'); idx=re.sub(r'(dataType="gamesystem"[^>]*dataRevision=")\d+("/>)',r'\g<1>23\2',idx); idx=re.sub(r'(dataType="catalogue"[^>]*dataRevision=")\d+("/>)',r'\g<1>53\2',idx); INDEX.write_text(idx,encoding='utf-8')

cat_ids={e.get('id') for e in cr.iter() if e.get('id')}; gst_ids={e.get('id') for e in gr.iter() if e.get('id')}
assert len(cat_ids)==len([e for e in cr.iter() if e.get('id')]),'duplicate CAT IDs'
assert len(gst_ids)==len([e for e in gr.iter() if e.get('id')]),'duplicate GST IDs'
for root,own,other,label in [(cr,cat_ids,gst_ids,'CAT'),(gr,gst_ids,cat_ids,'GST')]:
    broken=[]
    for e in root.iter():
        for a in ('targetId','childId'):
            v=e.get(a)
            if v and v not in own and v not in other:broken.append((e.get('id'),a,v))
    assert not broken,f'{label} broken refs: {broken[:20]}'
text=CAT.read_text(encoding='utf-8'); gsttext=GST.read_text(encoding='utf-8')
assert '<ns0:' not in text and '<ns0:' not in gsttext
assert cr.get('revision')=='53' and gr.get('revision')=='23' and cr.get('gameSystemRevision')=='23'
assert not any((s.get('name') or '').strip().lower()=='additional model' for s in cr.iter(C('selectionEntry'))),'Additional model entries remain'
note(f'Converted {len(converted)} imported squads to total Squad Models counters.')
if unresolved: note('Unresolved Additional model entries: '+repr(unresolved[:20]))
for name,base,total,per,old in converted: note(f'{name}: starts at {base}, max {total}, +{per:g} pts/model; old minimum cost {old:g} preserved.')
Path('inspection-r53-unit-sizes-sonic.txt').write_text('\n'.join(REPORT)+'\n',encoding='utf-8')
print('Revision 53 validation passed.')
