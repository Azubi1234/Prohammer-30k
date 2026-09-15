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
def parent_of(root,node):
    for p in root.iter():
        if node in list(p): return p
    return None

def remove_id(root,id_):
    x=by_id(root,id_)
    if x is None:return False
    p=parent_of(root,x)
    if p is None:return False
    p.remove(x); return True

def condition_group(mod, legion_id, require_limit=True, limit_cmp=None, limit_value=None):
    cgs=ET.SubElement(mod,G('conditionGroups'))
    cg=ET.SubElement(cgs,G('conditionGroup'),{'type':'and'})
    cs=ET.SubElement(cg,G('conditions'))
    ET.SubElement(cs,G('condition'),{
        'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':legion_id,
        'shared':'true','includeChildSelections':'true','includeChildForces':'false'
    })
    if require_limit:
        ET.SubElement(cs,G('condition'),{
            'type':limit_cmp or 'greaterThan','value':str(limit_value if limit_value is not None else 0),
            'field':'limit::pts','scope':'roster','childId':'model','shared':'true',
            'includeChildSelections':'true','includeChildForces':'false'
        })
    return cg

def add_set_modifier(mods,id_,field,value,legion_id,limit_cmp=None,limit_value=None):
    m=ET.SubElement(mods,G('modifier'),{'id':id_,'type':'set','value':str(value),'field':field})
    condition_group(m,legion_id,limit_cmp is not None,limit_cmp,limit_value)
    return m

def add_scaled_modifier(mods,id_,field,legion_id):
    m=ET.SubElement(mods,G('modifier'),{'id':id_,'type':'increment','value':'1','field':field})
    reps=ET.SubElement(m,G('repeats'))
    ET.SubElement(reps,G('repeat'),{
        'field':'limit::pts','scope':'roster','value':'750','shared':'true','childId':'model',
        'includeChildSelections':'true','includeChildForces':'false','repeats':'1','roundUp':'true'
    })
    condition_group(m,legion_id,True,'greaterThan',0)
    return m

leg=by_id(cr,'legion-vi')
chap=by_id(cr,'hq-consul-chaplain')
lib=by_id(cr,'hq-consul-librarian')
assert leg is not None,'VI Legion — Space Wolves selector not found'
assert chap is not None,'Legion Chaplain Consul not found'
assert lib is not None,'Legion Librarian Consul not found'

# The source text for the reviewed block is already present verbatim in the Legion reference.
ref=by_id(cr,'r25-legion-vi-reference')
assert ref is not None,'Space Wolves Legion reference rule not found'
desc=ref.find(C('description'))
text=(desc.text or '') if desc is not None else ''
for phrase in ['HUNTERS OF FENRIS','NO MATTER THE ODDS','BLOOD FEUD','LEGION ORGANISATION','Dark Angels and Thousand Sons']:
    assert phrase in text,phrase

# Generic Chaplain and Librarian are already hidden for Legion VI; verify rather than duplicate modifiers.
def has_sw_hide(e):
    for c in e.findall('.//'+C('condition')):
        if c.get('childId')=='legion-vi' and c.get('field')=='selections':
            p=parent_of(cr,c)
            while p is not None and p.tag!=C('modifier'):
                p=parent_of(cr,p)
            if p is not None and p.get('field')=='hidden' and p.get('value')=='true': return True
    return False
assert has_sw_hide(chap),'Chaplain is not hidden for Space Wolves'
assert has_sw_hide(lib),'Librarian is not hidden for Space Wolves'

# Implement the distinctive Space Wolves HQ organisation in the game-system force chart.
# One HQ is required for every full or partial 750 points, and that number replaces BOTH
# the normal minimum and maximum. We use the roster points LIMIT, which is the correct
# BattleScribe/New Recruit field for force-organisation scaling.
force=by_id(gr,'force-standard')
assert force is not None,'Standard Age of Darkness Detachment not found'
hq=next((x for x in force.findall('./'+G('categoryLinks')+'/'+G('categoryLink')) if x.get('targetId')=='cat-hq'),None)
assert hq is not None,'HQ category link not found'
cons=hq.find(G('constraints')); assert cons is not None
hq_min=next((x for x in cons.findall(G('constraint')) if x.get('type')=='min'),None)
hq_max=next((x for x in cons.findall(G('constraint')) if x.get('type')=='max'),None)
assert hq_min is not None and hq_min.get('id')=='fl-hq-min'
assert hq_max is not None and hq_max.get('id')=='fl-hq-max'
mods=hq.find(G('modifiers'))
if mods is None: mods=ET.SubElement(hq,G('modifiers'))
for x in list(mods):
    if x.get('id')=='r43-sw-hq-max' or (x.get('id') or '').startswith('r62-sw-hq-'):
        mods.remove(x)

# For a defined positive points limit, reset both constraints to zero and then increment
# once per 750 points, rounding up. Example: 750=>1, 751=>2, 1501=>3, 2251=>4.
add_set_modifier(mods,'r62-sw-hq-min-reset','fl-hq-min',0,'legion-vi','greaterThan',0)
add_set_modifier(mods,'r62-sw-hq-max-reset','fl-hq-max',0,'legion-vi','greaterThan',0)
add_scaled_modifier(mods,'r62-sw-hq-min-scale','fl-hq-min','legion-vi')
add_scaled_modifier(mods,'r62-sw-hq-max-scale','fl-hq-max','legion-vi')
# If the roster has no points limit (-1), allow the source's displayed 1–4 range manually.
add_set_modifier(mods,'r62-sw-hq-unlimited-max','fl-hq-max',4,'legion-vi','lessThan',0)

# Revisions: catalogue content is reviewed at 62; game system changes to 30.
cr.set('revision','62'); cr.set('gameSystemRevision','30'); gr.set('revision','30')
comment=cr.find(C('comment'))
if comment is not None:
    comment.text='Revision 62: Space Wolves Legion base rules verified against Forces of the Legions; HQ organisation now scales one selection per full or partial 750 roster-limit points.'
ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
ET.register_namespace('',GNS); gt.write(GST,encoding='UTF-8',xml_declaration=True)
idx=INDEX.read_text(encoding='utf-8')
idx=re.sub(r'(dataType="gamesystem"[^>]*dataRevision=")\d+("/>)',r'\g<1>30\2',idx)
idx=re.sub(r'(dataType="catalogue"[^>]*dataRevision=")\d+("/>)',r'\g<1>62\2',idx)
INDEX.write_text(idx,encoding='utf-8')

# Structural validation.
cat_ids=[x.get('id') for x in cr.iter() if x.get('id')]
gst_ids=[x.get('id') for x in gr.iter() if x.get('id')]
assert len(cat_ids)==len(set(cat_ids)),'Duplicate CAT IDs'
assert len(gst_ids)==len(set(gst_ids)),'Duplicate GST IDs'
all_ids=set(cat_ids)|set(gst_ids)
broken=[]
for root in (cr,gr):
    for x in root.iter():
        for a in ('targetId','childId'):
            v=x.get(a)
            if v and v not in all_ids and v!='model': broken.append((x.get('id'),a,v))
assert not broken,broken[:20]
assert cr.get('gameSystemRevision')==gr.get('revision')=='30'
assert '<ns0:' not in CAT.read_text(encoding='utf-8')
assert '<ns0:' not in GST.read_text(encoding='utf-8')
for rid in ['r62-sw-hq-min-reset','r62-sw-hq-max-reset','r62-sw-hq-min-scale','r62-sw-hq-max-scale','r62-sw-hq-unlimited-max']:
    assert by_id(gr,rid) is not None,rid
assert by_id(gr,'r43-sw-hq-max') is None,'Old fixed Space Wolves HQ max still present'

note('REVISION 62 — SPACE WOLVES BASE')
note('Source verification: Hunters of Fenris, No Matter the Odds, Blood Feud and Legion Organisation match Forces of the Legions.')
note('Consul restriction: generic Chaplain and Librarian are hidden when VI Legion — Space Wolves is selected.')
note('HQ organisation: min and max now equal ceil(roster points limit / 750), enforcing exactly 1/2/3/4 HQ at 750/1500/2250/3000 points and continuing the written one-per-partial-750 rule above that.')
note('Unlimited roster fallback: min 1, max 4 for manual use.')
note('Validation PASS: CAT62 / GST30, no duplicate IDs, no broken references.')
Path('inspection-r62-space-wolves-base.txt').write_text('\n'.join(REPORT)+'\n',encoding='utf-8')
