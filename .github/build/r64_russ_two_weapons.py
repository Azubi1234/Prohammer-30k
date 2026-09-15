from pathlib import Path
import xml.etree.ElementTree as ET

CAT = Path('Legiones Astartes.cat')
IDX = Path('index.xml')
SRC = Path('.github/build/rev63_space_wolves_full.py')
WF = Path('.github/workflows/apply-r63-space-wolves-full.yml')
INSPECT = Path('inspection-r63-space-wolves-full.txt')

CNS = 'http://www.battlescribe.net/schema/catalogueSchema'
INS = 'http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('', CNS)
ET.register_namespace('', INS)
C = lambda t: f'{{{CNS}}}{t}'
I = lambda t: f'{{{INS}}}{t}'

# Patch the generated catalogue.
ctree = ET.parse(CAT)
cr = ctree.getroot()

def by_id(root, ident):
    return next((e for e in root.iter() if e.get('id') == ident), None)

wg = by_id(cr, 'r63-sw-russ-weapon-choice')
if wg is None:
    raise RuntimeError('Leman Russ weapon-choice group not found')
wg.set('name', "The Wolf King’s Weapons — select two")
constraints = wg.find(C('constraints'))
if constraints is None:
    raise RuntimeError('Leman Russ weapon-choice constraints missing')
seen = set()
for con in constraints.findall(C('constraint')):
    if con.get('type') in ('min', 'max'):
        con.set('value', '2')
        seen.add(con.get('type'))
if seen != {'min', 'max'}:
    raise RuntimeError(f'Unexpected Leman Russ weapon-choice constraints: {seen}')

wg_rule = by_id(cr, 'r63-sw-russ-wg')
if wg_rule is None:
    raise RuntimeError('Leman Russ wargear rule not found')
desc = wg_rule.find(C('description'))
if desc is None or not desc.text:
    raise RuntimeError('Leman Russ wargear description missing')
desc.text = desc.text.replace('and one of: Mjalnar Sword of Balenight, Axe of Helwinter, or Krakenmaw.',
                              'and two of: Mjalnar Sword of Balenight, Axe of Helwinter, or Krakenmaw.')

cr.set('revision', '64')
ctree.write(CAT, encoding='utf-8', xml_declaration=True)
ET.parse(CAT)

# Bump repository index.
itree = ET.parse(IDX)
ir = itree.getroot()
found = False
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath') == 'Legiones Astartes.cat':
        e.set('dataRevision', '64')
        found = True
if not found:
    raise RuntimeError('Catalogue entry missing from index.xml')
itree.write(IDX, encoding='utf-8', xml_declaration=True)
ET.parse(IDX)

# Keep the full Space Wolves source script in sync so a future rebuild preserves the choice.
s = SRC.read_text(encoding='utf-8')
replacements = {
    "and one of: Mjalnar Sword of Balenight, Axe of Helwinter, or Krakenmaw.":
        "and two of: Mjalnar Sword of Balenight, Axe of Helwinter, or Krakenmaw.",
    "wg=group(u,'r63-sw-russ-weapon-choice','The Wolf King’s Weapon — select one',minv=1,maxv=1)":
        "wg=group(u,'r63-sw-russ-weapon-choice','The Wolf King’s Weapons — select two',minv=2,maxv=2)",
    "cr.set('revision','63')": "cr.set('revision','64')",
    "if fp=='Legiones Astartes.cat': e.set('dataRevision','63')":
        "if fp=='Legiones Astartes.cat': e.set('dataRevision','64')",
    "Catalogue revision: 63": "Catalogue revision: 64",
}
for old, new in replacements.items():
    if old not in s:
        raise RuntimeError(f'Expected source text not found: {old}')
    s = s.replace(old, new)
SRC.write_text(s, encoding='utf-8')

# Keep the original full-army workflow valid if it is ever rerun.
w = WF.read_text(encoding='utf-8')
if "grep -q 'dataRevision=\"63\"' index.xml" not in w:
    raise RuntimeError('Expected revision check not found in Space Wolves workflow')
w = w.replace("grep -q 'dataRevision=\"63\"' index.xml", "grep -q 'dataRevision=\"64\"' index.xml")
WF.write_text(w, encoding='utf-8')

# Refresh the inspection summary with the small follow-up change.
if INSPECT.exists():
    text = INSPECT.read_text(encoding='utf-8')
    text = text.replace('Catalogue revision: 63', 'Catalogue revision: 64')
    note = '\nRevision 64 follow-up:\n- Leman Russ must select exactly two of Mjalnar Sword of Balenight, Axe of Helwinter, and Krakenmaw.\n'
    if 'Revision 64 follow-up:' not in text:
        text = text.rstrip() + '\n' + note
    INSPECT.write_text(text, encoding='utf-8')

print('Revision 64 applied: Leman Russ now selects exactly two of his three melee weapons.')
