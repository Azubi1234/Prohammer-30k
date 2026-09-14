from pathlib import Path
import xml.etree.ElementTree as ET
import re

# Revision 55 final runner.
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); INDEX=Path('index.xml')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()

def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def pts(e):
    cs=e.find(C('costs'))
    return next((x for x in cs.findall(C('cost')) if x.get('typeId')=='pts'),None) if cs is not None else None
def constraint(e,typ):
    cs=e.find(C('constraints'))
    return next((x for x in cs.findall(C('constraint')) if x.get('type')==typ and x.get('field')=='selections'),None) if cs is not None else None
def ensure_constraints(e):
    cs=e.find(C('constraints'))
    if cs is None: cs=ET.SubElement(e,C('constraints'))
    return cs

def migrate(unit_id, entry_id, group_id, base, label):
    u=by_id(unit_id); e=by_id(entry_id); g=by_id(group_id)
    assert u is not None and e is not None and g is not None,(unit_id,entry_id,group_id)
    pc=pts(e); up=pts(u); mx=constraint(e,'max')
    assert pc is not None and up is not None and mx is not None
    old_extra_max=int(float(mx.get('value','0'))); per=float(pc.get('value','0')); old_unit=float(up.get('value','0'))
    total_max=base+old_extra_max

    e.set('name',label); e.set('type','model'); e.set('defaultAmount',str(base))
    mx.set('value',str(total_max))
    mn=constraint(e,'min')
    if mn is None:
        ET.SubElement(ensure_constraints(e),C('constraint'),{
            'id':entry_id+'-min-total','type':'min','value':str(base),'field':'selections','scope':'parent',
            'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    else: mn.set('value',str(base))

    gmx=constraint(g,'max')
    if gmx is not None: gmx.set('value',str(total_max))
    gmn=constraint(g,'min')
    if gmn is None:
        ET.SubElement(ensure_constraints(g),C('constraint'),{
            'id':group_id+'-min-total','type':'min','value':str(base),'field':'selections','scope':'parent',
            'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    else: gmn.set('value',str(base))

    up.set('value',str(old_unit-base*per))

    shifted=0
    for x in cr.iter():
        if x.get('childId')==entry_id and x.get('field')=='selections':
            try:
                nv=float(x.get('value','0'))+base
                x.set('value',str(int(nv)) if nv.is_integer() else str(nv))
                shifted+=1
            except ValueError:
                pass
    return f'{u.get("name")}: {label} now starts at {base}, max {total_max}, +{per:g} pts/model; shifted {shifted} quantity conditions; minimum unit price preserved.'

report=[]
report.append(migrate('da22-deathwing-companions','da22-dwc-extra','da22-dwc-extra-g',5,'Deathwing Companions'))
report.append(migrate('da22-interemptors','da22-int-extra','da22-int-extra-g',5,'Interemptors'))

cr.set('revision','55'); cr.set('gameSystemRevision','25'); gr.set('revision','25')
comment=cr.find(C('comment'))
if comment is not None: comment.text='Revision 55: Dark Angels Deathwing Companions and Dreadwing Interemptors now show actual starting squad sizes rather than Additional model counters.'
ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
ET.register_namespace('',GNS); gt.write(GST,encoding='UTF-8',xml_declaration=True)
idx=INDEX.read_text(encoding='utf-8')
idx=re.sub(r'(dataType="gamesystem"[^>]*dataRevision=")\d+("/>)',r'\g<1>25\2',idx)
idx=re.sub(r'(dataType="catalogue"[^>]*dataRevision=")\d+("/>)',r'\g<1>55\2',idx)
INDEX.write_text(idx,encoding='utf-8')

cat_ids={e.get('id') for e in cr.iter() if e.get('id')}; gst_ids={e.get('id') for e in gr.iter() if e.get('id')}
assert len(cat_ids)==len([e for e in cr.iter() if e.get('id')]),'duplicate CAT IDs'
assert len(gst_ids)==len([e for e in gr.iter() if e.get('id')]),'duplicate GST IDs'
for root,own,other,label in [(cr,cat_ids,gst_ids,'CAT'),(gr,gst_ids,cat_ids,'GST')]:
    broken=[]
    for x in root.iter():
        for a in ('targetId','childId'):
            v=x.get(a)
            if v and v not in own and v not in other: broken.append((x.get('id'),a,v))
    assert not broken,f'{label} broken refs: {broken[:20]}'
assert by_id('da22-dwc-extra').get('name')=='Deathwing Companions'
assert by_id('da22-dwc-extra').get('defaultAmount')=='5'
assert by_id('da22-int-extra').get('name')=='Interemptors'
assert by_id('da22-int-extra').get('defaultAmount')=='5'
assert '<ns0:' not in CAT.read_text(encoding='utf-8') and '<ns0:' not in GST.read_text(encoding='utf-8')
Path('inspection-r55-da-unique-squad-sizes.txt').write_text('\n'.join(report)+'\nValidation: CAT55/GST25, canonical namespaces, no broken references.\n',encoding='utf-8')
print('\n'.join(report)); print('Revision 55 validation passed.')
