from pathlib import Path
import subprocess, sys, xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'

# The main cleanup intentionally performs its full mutation before its final hard-reference audit.
# Run it, then repair the two inherited HSS modifiers that referenced heavy-weapon choices removed
# by the new Sonic Weaponry HSS entry, and perform the final audit here.
p=subprocess.run([sys.executable,'.github/build/rev52_emperors_children_cleanup.py'])
if not CAT.exists() or not GST.exists():
    raise SystemExit(p.returncode or 1)

ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()
ids={e.get('id') for e in cr.iter() if e.get('id')}
removed=[]
for parent in list(cr.iter()):
    for child in list(parent):
        if child.tag!=C('modifier'): continue
        bad=[]
        for cond in child.iter(C('condition')):
            ref=cond.get('childId')
            if ref and ref.startswith('r52-ec-sonic-hss-') and ref not in ids:
                bad.append(ref)
        if bad:
            parent.remove(child); removed.extend(bad)

# Also catch nested modifiers under modifier containers.
changed=True
while changed:
    changed=False; ids={e.get('id') for e in cr.iter() if e.get('id')}
    for parent in list(cr.iter()):
        for child in list(parent):
            if child.tag!=C('modifier'): continue
            bad=[c.get('childId') for c in child.iter(C('condition')) if c.get('childId') and c.get('childId').startswith('r52-ec-sonic-hss-') and c.get('childId') not in ids]
            if bad:
                parent.remove(child); removed.extend(bad); changed=True

ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
ET.register_namespace('',GNS); gt.write(GST,encoding='UTF-8',xml_declaration=True)

cat_text=CAT.read_text(encoding='utf-8'); gst_text=GST.read_text(encoding='utf-8')
assert '<ns0:' not in cat_text and '<ns0:' not in gst_text
assert '<catalogue xmlns="http://www.battlescribe.net/schema/catalogueSchema"' in cat_text
assert '<gameSystem xmlns="http://www.battlescribe.net/schema/gameSystemSchema"' in gst_text
assert cr.get('revision')=='52' and cr.get('gameSystemRevision')=='22' and gr.get('revision')=='22'

def validate(root,other=None):
    allids=[e.get('id') for e in root.iter() if e.get('id')]
    assert len(allids)==len(set(allids)), 'duplicate IDs'
    ids=set(allids); otherids={e.get('id') for e in other.iter() if e.get('id')} if other is not None else set()
    broken=[]
    for e in root.iter():
        for a in ('targetId','childId'):
            v=e.get(a)
            if v and v not in ids and v not in otherids:
                broken.append((e.get('id'),a,v))
    return broken
cb=validate(cr,gr); gb=validate(gr)
assert not cb, f'broken CAT refs: {cb[:20]}'
assert not gb, f'broken GST refs: {gb[:20]}'

report=Path('inspection-r52-ec-cleanup.txt')
old=report.read_text(encoding='utf-8') if report.exists() else ''
report.write_text(old + f'Runner repair: pruned {len(set(removed))} obsolete inherited Sonic-HSS heavy-weapon references.\nFinal validation: CAT52/GST22, canonical namespaces, duplicate IDs 0, broken references 0.\n',encoding='utf-8')
print(f'Revision 52 final validation passed; pruned {len(set(removed))} inherited references.')
