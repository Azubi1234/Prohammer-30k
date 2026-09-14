from pathlib import Path
import xml.etree.ElementTree as ET
import re

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); INDEX=Path('index.xml')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()

def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def pts(e):
    cs=e.find(C('costs'))
    return next((x for x in cs.findall(C('cost')) if x.get('typeId')=='pts'),None) if cs is not None else None
def maxc(e):
    cs=e.find(C('constraints'))
    return next((x for x in cs.findall(C('constraint')) if x.get('type')=='max' and x.get('field')=='selections'),None) if cs is not None else None

def ensure_cost(e,value):
    cs=e.find(C('costs'))
    if cs is None: cs=ET.SubElement(e,C('costs'))
    c=next((x for x in cs.findall(C('cost')) if x.get('typeId')=='pts'),None)
    if c is None: c=ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(value)})
    else: c.set('value',str(value))
    return c

# Merge the old "included + additional" Dark Angels model counters into a single
# expandable model counter, matching the post-Rev53 squad-size presentation.
# The Sergeant remains a separate fixed model where the unit already used that structure.
MAPPINGS=[
 ('r40-da-vow-veteran','r40-da-vow-veteran-veteran-included','r40-da-vow-veteran-veteran-additional','Legion Veterans'),
 ('r40-da-vow-terminator','r40-da-vow-terminator-terminator-included','r40-da-vow-terminator-terminator-additional','Legion Terminators'),
 ('r40-da-eskaton-destroyer','r40-da-eskaton-destroyer-destroyer-included','r40-da-eskaton-destroyer-destroyer-additional','Legion Destroyers'),
 ('r40-da-arrow-bike','r40-da-arrow-bike-fa-bike-included','r40-da-arrow-bike-fa-bike-add','Legion Bikers'),
 ('r40-da-arrow-sky','r40-da-arrow-sky-fa-sky-included','r40-da-arrow-sky-fa-sky-add','Legion Sky Hunters'),
 ('r40-da-serpent-seeker','r40-da-serpent-seeker-fa-seeker-included','r40-da-serpent-seeker-fa-seeker-add','Legion Seekers'),
]
report=[]
for uid,incid,addid,newname in MAPPINGS:
    u=by_id(uid); inc=by_id(incid); add=by_id(addid)
    assert u is not None and inc is not None and add is not None,(uid,incid,addid)
    imx=maxc(inc); amx=maxc(add); ap=pts(add); up=pts(u)
    assert imx is not None and amx is not None and ap is not None and up is not None,uid
    base=int(float(inc.get('defaultAmount') or imx.get('value')))
    extra=int(float(amx.get('value'))); per=float(ap.get('value')); old=float(up.get('value'))
    inc.set('name',newname); inc.set('defaultAmount',str(base)); imx.set('value',str(base+extra))
    ensure_cost(inc,per)
    # Offset the newly costed included models so the existing minimum squad price is unchanged.
    up.set('value',str(old-base*per))
    parent=next((p for p in cr.iter() if add in list(p)),None); assert parent is not None
    parent.remove(add)
    report.append(f'{u.get("name")}: {newname} now {base}-{base+extra} plus fixed Sergeant; +{per:g} pts per model above the minimum. Minimum unit price preserved at {old:g} pts.')

# Existing Dark Angels Tactical/Assault Rite clones already use expandable base model counters
# (9-19 Marines + 1 Sergeant), and Predator squadrons already use a 1-3 tank counter, so leave them untouched.
cr.set('revision','54'); cr.set('gameSystemRevision','24'); gr.set('revision','24')
comment=cr.find(C('comment'))
if comment is not None: comment.text='Revision 54: Dark Angels squad-size counters normalized to show included models directly; separate Additional model counters removed.'
ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
ET.register_namespace('',GNS); gt.write(GST,encoding='UTF-8',xml_declaration=True)
idx=INDEX.read_text(encoding='utf-8')
idx=re.sub(r'(dataType="gamesystem"[^>]*dataRevision=")\d+("/>)',r'\g<1>24\2',idx)
idx=re.sub(r'(dataType="catalogue"[^>]*dataRevision=")\d+("/>)',r'\g<1>54\2',idx)
INDEX.write_text(idx,encoding='utf-8')

cat_ids={e.get('id') for e in cr.iter() if e.get('id')}; gst_ids={e.get('id') for e in gr.iter() if e.get('id')}
assert len(cat_ids)==len([e for e in cr.iter() if e.get('id')]),'duplicate CAT IDs'
assert len(gst_ids)==len([e for e in gr.iter() if e.get('id')]),'duplicate GST IDs'
for root,own,other,label in [(cr,cat_ids,gst_ids,'CAT'),(gr,gst_ids,cat_ids,'GST')]:
    broken=[]
    for e in root.iter():
        for a in ('targetId','childId'):
            v=e.get(a)
            if v and v not in own and v not in other: broken.append((e.get('id'),a,v))
    assert not broken,f'{label} broken refs: {broken[:20]}'
assert all(by_id(addid) is None for _,_,addid,_ in MAPPINGS)
assert '<ns0:' not in CAT.read_text(encoding='utf-8') and '<ns0:' not in GST.read_text(encoding='utf-8')
assert cr.get('revision')=='54' and cr.get('gameSystemRevision')=='24' and gr.get('revision')=='24'
Path('inspection-r54-da-unit-sizes.txt').write_text('\n'.join(report)+'\nValidation: CAT54/GST24; canonical namespaces; no broken references; all six Dark Angels Additional model counters removed.\n',encoding='utf-8')
print('\n'.join(report)); print('Revision 54 validation passed.')
