from pathlib import Path
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

CAT=Path('Legiones Astartes.cat')
GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'
GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'
G=lambda t:f'{{{GNS}}}{t}'
ET.register_namespace('',CNS); ET.register_namespace('',GNS)
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()

LEGIONS={f'legion-{x}' for x in ['i','iii','iv','v','vi','vii','viii','ix','x','xii','xiii','xiv','xv','xvi','xvii','xviii','xix','xx']}

def ensure(p,tag):
    q=C(tag); x=p.find(q)
    if x is None: x=ET.SubElement(p,q)
    return x

def invert(cond):
    typ=cond.get('type'); val=cond.get('value','1')
    if typ=='atLeast': return 'lessThan', val
    if typ=='lessThan': return 'atLeast', val
    if typ=='equalTo': return 'notEqualTo', val
    if typ=='notEqualTo': return 'equalTo', val
    if typ=='atMost':
        try:return 'atLeast',str(float(val)+1).rstrip('0').rstrip('.')
        except:return None
    return None

def conds_from_modifier(m):
    direct=m.find(C('conditions'))
    if direct is not None:
        return list(direct.findall(C('condition')))
    cgs=m.find(C('conditionGroups'))
    if cgs is None:return None
    groups=cgs.findall(C('conditionGroup'))
    if len(groups)!=1 or groups[0].get('type')!='and':return None
    cs=groups[0].find(C('conditions'))
    return list(cs.findall(C('condition'))) if cs is not None else []

def add_hide_unless(el,cond,seq):
    inv=invert(cond)
    if inv is None:return False
    typ,val=inv
    mods=ensure(el,'modifiers')
    m=ET.SubElement(mods,C('modifier'),{'id':f'r48-vis-{seq}','type':'set','value':'true','field':'hidden'})
    cs=ET.SubElement(m,C('conditions'))
    attrs={
        'type':typ,'value':val,'field':cond.get('field','selections'),'scope':cond.get('scope','roster'),
        'childId':cond.get('childId',''),'shared':cond.get('shared','true'),
        'includeChildSelections':cond.get('includeChildSelections','true'),
        'includeChildForces':cond.get('includeChildForces','false')
    }
    ET.SubElement(cs,C('condition'),attrs)
    return True

fixed=[]; seq=0
for el in list(cr.iter()):
    eid=el.get('id','')
    # Dark Angels are already proven working in New Recruit. Leave them byte-for-byte semantically alone.
    if eid.startswith('da22-') or eid.startswith('r40-da-'):continue
    if el.get('hidden')!='true':continue
    mods=el.find(C('modifiers'))
    if mods is None:continue
    candidates=[]
    for m in list(mods.findall(C('modifier'))):
        if m.get('field')!='hidden' or m.get('type')!='set' or m.get('value')!='false':continue
        conds=conds_from_modifier(m)
        if not conds:continue
        if not any(c.get('childId') in LEGIONS for c in conds):continue
        if not all(invert(c) is not None for c in conds):continue
        candidates.append((m,conds))
    if not candidates:continue
    # New Recruit-safe form: base-visible, then hide while any required selector is absent.
    el.set('hidden','false')
    converted=[]
    for m,conds in candidates:
        mods.remove(m)
        for c in conds:
            seq+=1
            assert add_hide_unless(el,c,seq)
            converted.append((c.get('childId'),c.get('scope'),c.get('type'),c.get('value')))
    fixed.append((el.get('id'),el.get('name'),converted))

cr.set('revision','48')

ids=[]
for root,label in [(cr,'CAT'),(gr,'GST')]:
    xs=[e.get('id') for e in root.iter() if e.get('id')]
    dup=[x for x,n in Counter(xs).items() if n>1]
    assert not dup,(label,'duplicate IDs',dup[:30]);ids.extend(xs)
ids=set(ids)
broken=[]
for e in cr.iter():
    for a in ('targetId','childId'):
        v=e.get(a)
        if v and v not in ids:broken.append((e.get('id'),a,v))
assert not broken,broken[:50]
assert cr.get('gameSystemRevision')==gr.get('revision')

by_legion=defaultdict(list)
for eid,name,conds in fixed:
    for child,scope,typ,val in conds:
        if child in ('legion-v','legion-xv'):
            by_legion[child].append((eid,name))
            break
for leg in ('legion-v','legion-xv'):
    assert by_legion[leg],f'No New Recruit visibility gates repaired for {leg}'

def find(i):return next((e for e in cr.iter() if e.get('id')==i),None)
required={
 'legion-v':['r43-ws-power-glaive','r43-ws-warlance','r43-ws-cyber-hawk','r47-ws-horsetail-talisman'],
 'legion-xv':['r45-ts-force-weapon','r45-ts-arcane-litanies','r45-ts-asphyx-ic','r45-ts-brotherhood','r47-ts-prosperine-aether-disc']
}
for leg,targets in required.items():
    for t in targets:assert find(t) is not None,(leg,t)

ct.write(CAT,encoding='UTF-8',xml_declaration=True)
report=['REVISION 48 — NEW RECRUIT LEGION VISIBILITY REPAIR',f'Converted hidden→unhide Legion gates: {len(fixed)}','',f'White Scars repaired gated entries: {len(by_legion["legion-v"])}',f'Thousand Sons repaired gated entries: {len(by_legion["legion-xv"])}','']
for leg,title in [('legion-v','WHITE SCARS'),('legion-xv','THOUSAND SONS')]:
    report.append(title)
    for eid,name in by_legion[leg][:100]:report.append(f'  {eid} :: {name}')
Path('inspection-r48-new-recruit-visibility.txt').write_text('\n'.join(report),encoding='utf-8')
print('\n'.join(report[:8]))
