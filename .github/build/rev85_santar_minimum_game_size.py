from pathlib import Path
import re
import xml.etree.ElementTree as ET

CAT = Path('Legiones Astartes.cat')
IDX = Path('index.xml')
OUT = Path('inspection-r85-santar-minimum-game-size.txt')

NS = 'http://www.battlescribe.net/schema/catalogueSchema'
ET.register_namespace('', NS)
C = lambda tag: f'{{{NS}}}{tag}'

ct = ET.parse(CAT)
root = ct.getroot()

if root.get('revision') != '84' or root.get('gameSystemRevision') != '51':
    raise RuntimeError(
        f'Expected live CAT84 / GSTref51, got CAT{root.get("revision")} / GSTref{root.get("gameSystemRevision")}'
    )

SANTAR_ID = 'r41-unit-x-6-gabriel-santar'
CONSTRAINT_ID = 'r79-ih-santar-1500'

santar = next((e for e in root.iter(C('selectionEntry')) if e.get('id') == SANTAR_ID), None)
if santar is None:
    raise RuntimeError('Gabriel Santar selection entry not found')

constraints = santar.find(C('constraints'))
if constraints is None:
    raise RuntimeError('Gabriel Santar has no constraints container')

minimum = next((x for x in constraints.findall(C('constraint')) if x.get('id') == CONSTRAINT_ID), None)
if minimum is None:
    raise RuntimeError('Gabriel Santar 1500-point restriction not found')

before = dict(minimum.attrib)

# R79 accidentally encoded the game-size restriction as a minimum number of
# Santar selections in the roster, producing New Recruit's nonsensical
# (1/1500) display.  The restriction is instead against the roster's declared
# Points LIMIT: Santar is legal only in games of 1500 points or more.
minimum.set('field', 'limit::points')
minimum.set('scope', 'roster')
minimum.set('type', 'min')
minimum.set('value', '1500')
minimum.set('percentValue', 'false')
minimum.set('shared', 'true')
minimum.set('includeChildSelections', 'true')
minimum.set('includeChildForces', 'true')

after = dict(minimum.attrib)

# Preserve the independent unique-character cap.  Do not turn a minimum game
# size into a per-X-points allowance.
max_one = [
    x for x in constraints.findall(C('constraint'))
    if x.get('field') == 'selections' and x.get('type') == 'max' and x.get('value') in ('1', '1.0')
]
if not max_one:
    raise RuntimeError('Gabriel Santar no longer has a max-1 selection constraint')

# Permanent regression checks: there must be no 1500-valued SELECTION count
# constraint left on Santar, and exactly one roster-point-limit gate.
bad_ratio = [
    x for x in constraints.findall(C('constraint'))
    if x.get('field') == 'selections' and x.get('value') in ('1500', '1500.0')
]
if bad_ratio:
    raise RuntimeError('Malformed 1/1500 selection-count restriction still present')

limit_gates = [
    x for x in constraints.findall(C('constraint'))
    if x.get('field', '').lower() == 'limit::points'
    and x.get('scope') == 'roster'
    and x.get('type') == 'min'
    and x.get('value') in ('1500', '1500.0')
]
if len(limit_gates) != 1:
    raise RuntimeError(f'Expected exactly one 1500+ roster-points-limit gate, found {len(limit_gates)}')

root.set('revision', '85')
ct.write(CAT, encoding='utf-8', xml_declaration=True)

# Defensive New Recruit namespace normalization.  Earlier ElementTree passes
# in this repository have produced ns0: prefixes that New Recruit can cache
# incorrectly, so keep the catalogue in canonical default-namespace form.
text = CAT.read_text(encoding='utf-8')
text = text.replace(f'xmlns:ns0="{NS}"', f'xmlns="{NS}"')
text = text.replace('<ns0:', '<').replace('</ns0:', '</')
m = re.search(rf'<(ns\d+):catalogue\s+xmlns:\1="{re.escape(NS)}"', text)
if m:
    pfx = m.group(1)
    text = text.replace(f'xmlns:{pfx}="{NS}"', f'xmlns="{NS}"')
    text = text.replace(f'<{pfx}:', '<').replace(f'</{pfx}:', '</')
if re.search(r'<ns\d+:', text):
    raise RuntimeError('Generated namespace prefix remains in catalogue')
CAT.write_text(text, encoding='utf-8')

# Bump only the catalogue revision in the data index.  GST stays at 51.
idx = IDX.read_text(encoding='utf-8')
idx, n = re.subn(
    r'(filePath="Legiones Astartes\.cat"[^>]*dataRevision=")84(" )',
    r'\g<1>85\g<2>',
    idx,
    count=1,
)
if n != 1:
    raise RuntimeError('Failed to bump Legiones Astartes catalogue index revision 84 -> 85')
IDX.write_text(idx, encoding='utf-8')

# Reparse final files and verify the intended live state.
final_root = ET.parse(CAT).getroot()
final_santar = next((e for e in final_root.iter(C('selectionEntry')) if e.get('id') == SANTAR_ID), None)
final_constraints = final_santar.find(C('constraints')) if final_santar is not None else None
if final_constraints is None:
    raise RuntimeError('Final Santar constraints missing')
final_gate = next((x for x in final_constraints.findall(C('constraint')) if x.get('id') == CONSTRAINT_ID), None)
assert final_root.get('revision') == '85'
assert final_root.get('gameSystemRevision') == '51'
assert final_gate is not None
assert final_gate.get('field', '').lower() == 'limit::points'
assert final_gate.get('scope') == 'roster'
assert final_gate.get('type') == 'min'
assert final_gate.get('value') in ('1500', '1500.0')
assert not any(
    x.get('field') == 'selections' and x.get('value') in ('1500', '1500.0')
    for x in final_constraints.findall(C('constraint'))
)
assert any(
    x.get('field') == 'selections' and x.get('type') == 'max' and x.get('value') in ('1', '1.0')
    for x in final_constraints.findall(C('constraint'))
)

OUT.write_text(
    'Revision 85 — Gabriel Santar minimum game-size correction\n'
    'CAT=85 GSTref=51\n\n'
    f'Entry: {santar.get("name")} ({SANTAR_ID})\n'
    f'Old 1500 restriction: {before}\n'
    f'New 1500 restriction: {after}\n\n'
    'Result:\n'
    '- Removed the accidental minimum-1500 SELECTIONS semantics that rendered as (1/1500).\n'
    '- The 1500 threshold now checks the roster Points LIMIT instead.\n'
    '- Santar remains a unique max-1 character; this does not scale to 2 at 3000, 3 at 4500, etc.\n'
    '- Below a declared 1500-point game limit Santar is illegal; at 1500+ he is legal, subject to his normal max-1 cap.\n',
    encoding='utf-8',
)
print(OUT.read_text(encoding='utf-8'))
