from pathlib import Path
import re
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat')
GST=Path('Prohammer 30k.gst')
INDEX=Path('index.xml')
CNS='http://www.battlescribe.net/schema/catalogueSchema'
GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'
G=lambda t:f'{{{GNS}}}{t}'

ct=ET.parse(CAT); cr=ct.getroot()
gt=ET.parse(GST); gr=gt.getroot()
REPORT=[]
def note(s): REPORT.append(s); print(s)
def by_id(root,id_): return next((e for e in root.iter() if e.get('id')==id_),None)
def ensure(p,tag,ns=CNS):
    q=f'{{{ns}}}{tag}'; x=p.find(q)
    if x is None:x=ET.SubElement(p,q)
    return x
def remove_prefixed(root,prefix):
    n=0
    for p in list(root.iter()):
        for x in list(p):
            if (x.get('id') or '').startswith(prefix): p.remove(x); n+=1
    return n
def add_rule(e,id_,name,text):
    rs=ensure(e,'rules'); r=ET.SubElement(rs,C('rule'),{'id':id_,'name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=text; return r
def hide_when_legion(e,id_,legion_id):
    mods=ensure(e,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':id_,'type':'set','value':'true','field':'hidden'})
    cs=ET.SubElement(m,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':legion_id,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return m
def set_constraint_when_legion(e,id_,constraint_id,value,legion_id):
    mods=ensure(e,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':id_,'type':'set','value':str(value),'field':constraint_id})
    cs=ET.SubElement(m,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':legion_id,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return m

note(f'Removed old r62 CAT nodes: {remove_prefixed(cr,"r62-")}')

leg=by_id(cr,'legion-sw')
chap=by_id(cr,'hq-consul-chaplain')
lib=by_id(cr,'hq-consul-librarian')
hqcat=by_id(cr,'cat-hq')
assert leg is not None,'Space Wolves Legion selector legion-sw not found'
assert chap is not None,'Legion Chaplain Consul not found'
assert lib is not None,'Legion Librarian Consul not found'
assert hqcat is not None,'HQ category not found'

# VI Legion rules — source is Forces of the Legions, pages 58–59.
add_rule(leg,'r62-sw-hunters','Hunters of Fenris',
         'All non-vehicle units with the Legiones Astartes (Space Wolves) special rule gain the Counter-Attack and Acute Senses special rules.')
add_rule(leg,'r62-sw-odds','No Matter the Odds',
         'Space Wolves units ignore negative Leadership modifiers applied to Break Tests caused by losing close combat. Other Leadership modifiers apply normally.')
add_rule(leg,'r62-sw-feud','Blood Feud',
         'Space Wolves models always hit Dark Angels and Thousand Sons models on a 3+ in close combat unless they would normally hit on a better result. Dark Angels and Thousand Sons models likewise always hit Space Wolves models on a 3+ in close combat unless they would normally hit on a better result.')
add_rule(leg,'r62-sw-organisation','Legion Organisation',
         'A Space Wolves Detachment must include one HQ selection for every full or partial 750 points in the army: up to 750 points — 1 HQ; 751–1,500 points — 2 HQ; 1,501–2,250 points — 3 HQ; 2,251–3,000 points — 4 HQ. This replaces the normal minimum and maximum number of HQ selections. The normal restriction on models with Master of the Legion still applies. Space Wolves may not select Legion Chaplain Consuls or Legion Librarian Consuls; their roles are instead fulfilled by Wolf Priests and Rune Priests.')

# Generic Chaplain and Librarian are unavailable to Space Wolves.
hide_when_legion(chap,'r62-sw-hide-chaplain','legion-sw')
hide_when_legion(lib,'r62-sw-hide-librarian','legion-sw')

# The source explicitly permits 4 HQ at 2,251–3,000 points. The catalogue's normal
# HQ maximum is 3, so lift that ceiling to 4 for Space Wolves. The point-tiered
# minimum remains represented by the Legion Organisation rule because this catalogue
# has no established/safe total-roster-points condition to drive 1/2/3/4 dynamically.
hqmax=next((x for x in hqcat.findall('./'+C('constraints')+'/'+C('constraint')) if x.get('type')=='max'),None)
assert hqmax is not None,'HQ max constraint not found'
set_constraint_when_legion(hqcat,'r62-sw-hq-max-four',hqmax.get('id'),4,'legion-sw')

# Revision/index. GST is unchanged.
cr.set('revision','62')
comment=cr.find(C('comment'))
if comment is not None: comment.text='Revision 62: implement Space Wolves Legion rules, organisation and Consul restrictions from Forces of the Legions.'
ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
idx=INDEX.read_text(encoding='utf-8')
idx=re.sub(r'(dataType="catalogue"[^>]*dataRevision=")\d+("/>)',r'\g<1>62\2',idx)
INDEX.write_text(idx,encoding='utf-8')

# Validation.
cat_ids=[x.get('id') for x in cr.iter() if x.get('id')]
gst_ids=[x.get('id') for x in gr.iter() if x.get('id')]
assert len(cat_ids)==len(set(cat_ids)),'Duplicate CAT IDs'
assert len(gst_ids)==len(set(gst_ids)),'Duplicate GST IDs'
all_ids=set(cat_ids)|set(gst_ids); broken=[]
for root in (cr,gr):
    for x in root.iter():
        for a in ('targetId','childId'):
            v=x.get(a)
            if v and v not in all_ids: broken.append((x.get('id'),a,v))
assert not broken,broken[:20]
cattext=CAT.read_text(encoding='utf-8')
assert '<ns0:' not in cattext
assert '<catalogue xmlns="http://www.battlescribe.net/schema/catalogueSchema"' in cattext
for rid in ('r62-sw-hunters','r62-sw-odds','r62-sw-feud','r62-sw-organisation','r62-sw-hide-chaplain','r62-sw-hide-librarian','r62-sw-hq-max-four'):
    assert by_id(cr,rid) is not None,rid
assert cr.get('revision')=='62'
assert gr.get('revision')=='29'

note('Revision 62 validation PASS: Space Wolves base Legion rules attached to legion-sw.')
note('Generic Chaplain Consul and Librarian Consul hide when VI — Space Wolves is selected.')
note('Space Wolves HQ maximum becomes 4; exact 1/2/3/4 minimum-by-points requirement is displayed in Legion Organisation and left manual rather than inventing an unsupported total-points condition.')
note('GST unchanged at revision 29; catalogue advanced to revision 62.')
Path('inspection-r62-space-wolves-base.txt').write_text('\n'.join(REPORT)+'\n',encoding='utf-8')
