from pathlib import Path
import xml.etree.ElementTree as ET
from collections import Counter

CAT=Path('Legiones Astartes.cat')
GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'
GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'
G=lambda t:f'{{{GNS}}}{t}'
ET.register_namespace('',CNS); ET.register_namespace('',GNS)
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()

# Force New Recruit to treat this as a complete source/game-system update, not just a catalogue-only revision.
cr.set('revision','50')
gr.set('revision','20')
cr.set('gameSystemRevision','20')

# Add a harmless visible source marker inside Army Configuration so the user can verify that NR actually loaded this data.
def byid(root,i):
    return next((e for e in root.iter() if e.get('id')==i),None)
config=byid(cr,'config-army')
assert config is not None
ses=config.find(C('selectionEntries'))
if ses is None: ses=ET.SubElement(config,C('selectionEntries'))
marker=byid(cr,'r50-data-marker')
if marker is None:
    marker=ET.SubElement(ses,C('selectionEntry'),{
        'id':'r50-data-marker','name':'Data Revision 50 loaded — Legion packages refreshed',
        'type':'upgrade','hidden':'false','import':'true'
    })
    cons=ET.SubElement(marker,C('constraints'))
    ET.SubElement(cons,C('constraint'),{
        'id':'r50-data-marker-max','type':'max','value':'1','field':'selections','scope':'parent',
        'shared':'true','includeChildSelections':'false','includeChildForces':'false'
    })

# Validate the exact White Scars / Thousand Sons material is still structurally present after R49.
required=[
 'r41-unit-v-0-golden-keshig-squadron','r41-unit-v-1-ebon-keshig',
 'r41-unit-xv-0-sekhmet-terminator-cabal','r41-unit-xv-1-khenetai-occult-blade-cabal',
 'r43-hq-praetor-ws-glaive','r43-hq-praetor-ws-lance',
 'r45-hq-praetor-r45-ts-force-weapon','r45-cult-hq-praetor'
]
for i in required: assert byid(cr,i) is not None,i

# Every imported R41 Legion unit must now have a primary battlefield role.
for e in cr.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')):
    if e.get('id','').startswith('r41-unit-'):
        cls=e.findall('./'+C('categoryLinks')+'/'+C('categoryLink'))
        assert cls and any(x.get('primary')=='true' for x in cls),(e.get('id'),'missing primary category')

# Hard integrity checks.
ids=[]
for root,label in [(cr,'CAT'),(gr,'GST')]:
    xs=[e.get('id') for e in root.iter() if e.get('id')]
    dup=[x for x,n in Counter(xs).items() if n>1]
    assert not dup,(label,dup[:20])
    ids.extend(xs)
ids=set(ids)
broken=[]
for e in cr.iter():
    for a in ('targetId','childId'):
        v=e.get(a)
        if v and v not in ids: broken.append((e.get('id'),a,v))
assert not broken,broken[:50]
assert cr.get('gameSystemRevision')==gr.get('revision')=='20'

ct.write(CAT,encoding='UTF-8',xml_declaration=True)
gt.write(GST,encoding='UTF-8',xml_declaration=True)
Path('inspection-r50-source-refresh.txt').write_text(
    'REVISION 50 — FULL NEW RECRUIT SOURCE REFRESH\n'
    'CAT revision=50\nGST revision=20\nCAT gameSystemRevision=20\n'
    'Visible marker: Data Revision 50 loaded — Legion packages refreshed\n'
    'White Scars / Thousand Sons required entries: PRESENT\nBroken refs: 0\n',encoding='utf-8')
print('REV50: CAT=50 GST=20 gameSystemRevision=20; marker added; integrity PASS')
