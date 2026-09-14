import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

# Reuse the source parser/materialiser recovered from the earlier expansion work,
# but apply it safely on top of the current Revision 40 catalogue.  Dark Angels,
# Lords of War and Aeronautica are deliberately left untouched here.
spec = importlib.util.spec_from_file_location('rev25base', '.github/build/rev25_apply.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ctree = ET.parse(m.CAT_PATH)
root = ctree.getroot()

# Remove only the abandoned generated package, if any survived an older build.
m.remove_generated(root)

legion_map = {L['roman']: f"legion-{L['roman'].lower()}" for L in m.LEGIONS}
refs_added, rites_added = m.add_legion_references_and_rites(root, legion_map)
consuls_added = m.add_special_consuls(root, legion_map)

legion_units = 0
for L in m.LEGIONS:
    if L['roman'] == 'I':
        continue  # Dark Angels are already the hand-finished reference implementation.
    lid = legion_map[L['roman']]
    for idx, entry in enumerate(L.get('entries', [])):
        uid = f"r41-unit-{m.slug(L['roman'])}-{idx}-{m.slug(entry['title'])}"
        m.materialise_unit(root, entry, uid, legion_id=lid, allegiance=entry.get('allegiance'))
        legion_units += 1

# Keep the mature current game-system revision.  Revision 40 already contains
# Retinue, Structure Points and the LoW limit, so there is no reason to touch GST.
root.set('revision', '41')
comment = root.find(m.C('comment'))
if comment is None:
    comment = ET.Element(m.C('comment'))
    root.insert(0, comment)
comment.text = ('Revision 41 staging: restored all non-Dark-Angels Legion packages from the final Forces of the Legions source as the foundation for the same hand-finished implementation standard used by Dark Angels. Experimental Wargear and Units remains excluded.')

ctree.write(m.CAT_PATH, encoding='UTF-8', xml_declaration=True)
print(f'REV41 IMPORT: references={refs_added} rites={rites_added} specialist_consuls={consuls_added} legion_units={legion_units}')
