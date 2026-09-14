from pathlib import Path
import subprocess,sys,xml.etree.ElementTree as ET

# Final Rev53 runner: handles the two nested/clone squad counters left after the global pass.
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
subprocess.run([sys.executable,'.github/build/rev53_unit_sizes_and_sonic_hss.py'])
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()

def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def pts(e):
    cs=e.find(C('costs'))
    return next((x for x in cs.findall(C('cost')) if x.get('typeId')=='pts'),None) if cs is not None else None
def constraint(e,t):
    cs=e.find(C('constraints'))
    return next((x for x in cs.findall(C('constraint')) if x.get('type')==t and x.get('field')=='selections'),None) if cs is not None else None
def convert(unit_id,additional_id,base):
    u=by_id(unit_id); a=by_id(additional_id)
    assert u is not None and a is not None,(unit_id,additional_id)
    mx=constraint(a,'max'); pc=pts(a); up=pts(u); assert mx is not None and pc is not None and up is not None
    extra=int(float(mx.get('value','0'))); per=float(pc.get('value','0')); old=float(up.get('value','0'))
    a.set('name','Squad Models'); a.set('defaultAmount',str(base)); mx.set('value',str(base+extra))
    mn=constraint(a,'min')
    if mn is None:
        cs=a.find(C('constraints'))
        if cs is None:cs=ET.SubElement(a,C('constraints'))
        ET.SubElement(cs,C('constraint'),{'id':a.get('id')+'-min-total','type':'min','value':str(base),'field':'selections','scope':'parent','shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    else:mn.set('value',str(base))
    up.set('value',str(old-base*per))
    rs=a.find(C('rules'))
    if rs is not None:
        for r in list(rs):
            if (r.get('name') or '').lower()=='additional model':rs.remove(r)
        if len(rs)==0:a.remove(rs)
    print(f'Converted clone {u.get("name")}: {base}-{base+extra} models, +{per:g} each.')

convert('r52-ec-third-kakophoni-troops','r52-ec-third-kako-r41-unit-iii-2-kakophoni-squad-additional',6)
convert('r52-ec-ful-phoenix-retinue','r52-ec-ful-phoenix-retinue-r41-unit-iii-1-phoenix-terminator-squad-additional',5)

ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
ET.register_namespace('',GNS); gt.write(GST,encoding='UTF-8',xml_declaration=True)
remaining=[(e.get('id'),e.get('name')) for e in cr.iter(C('selectionEntry')) if (e.get('name') or '').strip().lower()=='additional model']
assert not remaining,remaining
cat_ids={e.get('id') for e in cr.iter() if e.get('id')}; gst_ids={e.get('id') for e in gr.iter() if e.get('id')}
for root,own,other,label in [(cr,cat_ids,gst_ids,'CAT'),(gr,gst_ids,cat_ids,'GST')]:
    broken=[]
    for e in root.iter():
        for a in ('targetId','childId'):
            v=e.get(a)
            if v and v not in own and v not in other:broken.append((e.get('id'),a,v))
    assert not broken,f'{label} broken refs: {broken[:20]}'
assert '<ns0:' not in CAT.read_text(encoding='utf-8') and '<ns0:' not in GST.read_text(encoding='utf-8')
report=Path('inspection-r53-unit-sizes-sonic.txt')
old=report.read_text(encoding='utf-8') if report.exists() else ''
report.write_text(old+'Final runner: converted 3rd Company Kakophoni clone and Fulgrim Phoenix Terminator retinue to total Squad Models counters.\nValidation: no Additional model entries remain; Sonic HSS weapon group present; CAT53/GST23 valid.\n',encoding='utf-8')
print('Revision 53 final validation passed.')
