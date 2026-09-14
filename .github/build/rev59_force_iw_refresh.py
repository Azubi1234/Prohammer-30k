from pathlib import Path
import xml.etree.ElementTree as ET
import re

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); INDEX=Path('index.xml')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()

# Revision 58 already contains the corrected total-model counters. Bump BOTH catalogue and game-system
# revisions so New Recruit cannot remain on the cached Revision 57 data.
cr.set('revision','59'); cr.set('gameSystemRevision','27'); gr.set('revision','27')
comment=cr.find(C('comment'))
if comment is not None:
    comment.text='Revision 59: force New Recruit refresh of corrected Iron Warriors total-model squad counters.'

ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
ET.register_namespace('',GNS); gt.write(GST,encoding='UTF-8',xml_declaration=True)

idx=INDEX.read_text(encoding='utf-8')
idx=re.sub(r'(dataType="gamesystem"[^>]*dataRevision=")\d+("/>)',r'\g<1>27\2',idx)
idx=re.sub(r'(dataType="catalogue"[^>]*dataRevision=")\d+("/>)',r'\g<1>59\2',idx)
INDEX.write_text(idx,encoding='utf-8')

# Verify the four IW units are in total-model format, not Additional-model format.
expected={
 'r41-unit-iv-0-tyrant-siege-terminator-squad':('Tyrant Siege Terminators',5,10),
 'r41-unit-iv-1-iron-havoc-squad':('Iron Havocs',5,10),
 'r41-unit-iv-2-dominator-cohort':('Dominator Cohort Models',5,10),
 'r41-unit-iv-3-iron-circle-domitar-ferrum-maniple':('Domitar-Ferrum Battle-Automata',1,6),
}

def by_id(i): return next((x for x in cr.iter() if x.get('id')==i),None)
def cv(e,t):
    cs=e.find(C('constraints'))
    if cs is None:return None
    c=next((x for x in cs.findall(C('constraint')) if x.get('type')==t and x.get('field')=='selections'),None)
    return c.get('value') if c is not None else None

report=[]
for uid,(label,mn,mx) in expected.items():
    u=by_id(uid); assert u is not None,uid
    models=[e for e in u.findall(C('selectionEntries')+'/'+C('selectionEntry')) if e.get('type')=='model']
    m=next((e for e in models if e.get('name')==label),None); assert m is not None,(uid,[e.get('name') for e in models])
    assert int(float(m.get('defaultAmount') or 0))==mn,(uid,'default',m.get('defaultAmount'))
    assert int(float(cv(m,'min') or 0))==mn,(uid,'min',cv(m,'min'))
    assert int(float(cv(m,'max') or 0))==mx,(uid,'max',cv(m,'max'))
    assert not (m.get('name') or '').startswith('Additional ')
    report.append(f'{u.get("name")}: {label} {mn}-{mx}, default {mn}.')

# No visible quantity counter anywhere may be named Additional X.
for e in cr.iter(C('selectionEntry')):
    nm=(e.get('name') or '').strip()
    if nm.startswith('Additional ') and not nm.startswith(('Additional Armoury','Additional Wargear','Additional Weapon')):
        mx=cv(e,'max')
        if mx is not None and float(mx)>1:
            raise AssertionError(f'Legacy Additional-model quantity remains: {e.get("id")} {nm} max={mx}')

cat=CAT.read_text(encoding='utf-8'); gst=GST.read_text(encoding='utf-8')
assert '<ns0:' not in cat and '<ns0:' not in gst
assert '<catalogue xmlns="http://www.battlescribe.net/schema/catalogueSchema"' in cat
assert '<gameSystem xmlns="http://www.battlescribe.net/schema/gameSystemSchema"' in gst
report.append('CAT59 / GST27; canonical namespaces; no legacy Additional-model quantity counters.')
Path('inspection-r59-force-refresh.txt').write_text('\n'.join(report)+'\n',encoding='utf-8')
print('\n'.join(report))
