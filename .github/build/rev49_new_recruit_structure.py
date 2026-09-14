from pathlib import Path
import xml.etree.ElementTree as ET
from collections import Counter

CAT=Path('Legiones Astartes.cat')
GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'
GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'
ET.register_namespace('',CNS); ET.register_namespace('',GNS)
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()
top=cr.find(C('selectionEntries')); assert top is not None
ids={e.get('id'):e for e in cr.iter() if e.get('id')}

def ensure(p,t):
    x=p.find(C(t))
    if x is None:x=ET.SubElement(p,C(t))
    return x

def find_group(unit, needle):
    return next((g for g in unit.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')) if needle.lower() in (g.get('name') or '').lower()),None)

def generated_link(l):
    i=l.get('id','')
    return i.startswith(('r43-','r44-','r45-','r46-','r47-'))

def target_is_upgrade(l):
    t=ids.get(l.get('targetId'))
    return t is not None and t.get('type')=='upgrade'

# 1) New Recruit needs a primary battlefield-role category for top-level selectable units.
primary_fixed=[]
for e in top.findall(C('selectionEntry')):
    if not e.get('id','').startswith('r41-unit-'): continue
    cls=e.findall('./'+C('categoryLinks')+'/'+C('categoryLink'))
    if not cls: continue
    if not any(x.get('primary')=='true' for x in cls):
        cls[0].set('primary','true'); primary_fixed.append((e.get('id'),e.get('name'),cls[0].get('targetId')))

# 2) Generated Legion armoury links were attached directly to units. New Recruit is much more reliable
# when options live inside a visible option group (the Dark Angels implementation already follows this pattern).
# For Praetor/Centurion place them in the existing armoury groups; for other units create one explicit Legion group.
moved=[]
for unit in top.findall(C('selectionEntry')):
    rootlinks=unit.find(C('entryLinks'))
    if rootlinks is None: continue
    candidates=[l for l in list(rootlinks) if generated_link(l) and target_is_upgrade(l)]
    if not candidates: continue
    uid=unit.get('id','')
    if uid in ('hq-praetor','hq-centurion'):
        wg=find_group(unit,'Additional Wargear')
        wp=find_group(unit,'Weapon Replacements')
        ar=find_group(unit,'Armour Replacement')
        mob=find_group(unit,'Mobility')
        assert wg is not None and wp is not None and ar is not None and mob is not None
        for l in candidates:
            n=(l.get('name') or '').lower()
            if any(k in n for k in ['spear','axe','blade','glaive','warlance','weapon','chainaxe','crozius','manreaper','dagger','gauntlet']): dest=wp
            elif any(k in n for k in ['armour','armor','mantle']): dest=ar
            elif any(k in n for k in ['jump pack','jetbike','bike','aether-disc','æther-disc','wings']): dest=mob
            else: dest=wg
            ensure(dest,'entryLinks').append(l); rootlinks.remove(l); moved.append((uid,l.get('id'),dest.get('name')))
    else:
        groups=ensure(unit,'selectionEntryGroups')
        gid='r49-legion-upgrades-'+uid
        g=next((x for x in groups.findall(C('selectionEntryGroup')) if x.get('id')==gid),None)
        if g is None:
            g=ET.SubElement(groups,C('selectionEntryGroup'),{'id':gid,'name':'Legion Wargear & Upgrades','hidden':'false','collective':'false','import':'true'})
        dest=ensure(g,'entryLinks')
        for l in candidates:
            dest.append(l); rootlinks.remove(l); moved.append((uid,l.get('id'),g.get('name')))

# 3) Make imported Legion-specific top-level units explicitly importable/selectable in NR.
for e in top.findall(C('selectionEntry')):
    if e.get('id','').startswith('r41-unit-'):
        e.set('import','true')

# Revision bump.
cr.set('revision','49')

# Hard validation.
allids=[]
for root,label in [(cr,'CAT'),(gr,'GST')]:
    xs=[e.get('id') for e in root.iter() if e.get('id')]
    dup=[x for x,n in Counter(xs).items() if n>1]
    assert not dup,(label,dup[:30]); allids.extend(xs)
allids=set(allids); broken=[]
for e in cr.iter():
    for a in ('targetId','childId'):
        v=e.get(a)
        if v and v not in allids:broken.append((e.get('id'),a,v))
assert not broken,broken[:50]
assert cr.get('gameSystemRevision')==gr.get('revision')

# Exact regression checks for the two Legions reported by the user.
for uid in ['r41-unit-v-0-golden-keshig-squadron','r41-unit-v-1-ebon-keshig','r41-unit-xv-0-sekhmet-terminator-cabal','r41-unit-xv-1-khenetai-occult-blade-cabal']:
    e=ids[uid]
    assert any(x.get('primary')=='true' for x in e.findall('./'+C('categoryLinks')+'/'+C('categoryLink'))),(uid,'no primary category')
for uid in ['hq-praetor','hq-centurion']:
    u=ids[uid]
    rootids={l.get('id') for l in u.findall('./'+C('entryLinks')+'/'+C('entryLink'))}
    for lid in ([f'r43-{uid}-ws-glaive',f'r43-{uid}-ws-lance'] if uid=='hq-centurion' else ['r43-hq-praetor-ws-glaive','r43-hq-praetor-ws-lance']):
        assert lid not in rootids,(uid,lid,'still root-level')
    nested={l.get('id') for l in u.findall('.//'+C('selectionEntryGroup')+'/'+C('entryLinks')+'/'+C('entryLink'))}
    assert any('ws-glaive' in (x or '') for x in nested),(uid,'White Scars wargear not grouped')
    assert any('ts-force-weapon' in (x or '') for x in nested),(uid,'Thousand Sons wargear not grouped')

ct.write(CAT,encoding='UTF-8',xml_declaration=True)
report=[
 'REVISION 49 — NEW RECRUIT STRUCTURE REPAIR',
 f'R41 Legion units given primary FOC category: {len(primary_fixed)}',
 f'Generated Legion upgrade links moved into visible option groups: {len(moved)}',
 '',
 'WHITE SCARS / THOUSAND SONS spot checks: PASS',
 'Broken refs: 0',
]
Path('inspection-r49-structure-repair.txt').write_text('\n'.join(report),encoding='utf-8')
print('\n'.join(report))
