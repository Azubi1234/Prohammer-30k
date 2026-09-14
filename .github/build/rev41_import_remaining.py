import importlib.util
import xml.etree.ElementTree as ET

# Reuse the recovered source parser/materialiser, but apply it safely on top of
# the current catalogue. Dark Angels, Lords of War and Aeronautica are left
# untouched: this pass restores only the other seventeen Legion packages.
spec = importlib.util.spec_from_file_location('rev25base', '.github/build/rev25_apply.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

ctree = ET.parse(m.CAT_PATH)
root = ctree.getroot()
gtree = ET.parse(m.GST_PATH)
groot = gtree.getroot()

# Remove only abandoned output from the old failed expansion attempt.
m.remove_generated(root)
m.remove_generated(groot)

# Revision 40 already has Structure Points and the one-LoW limit, but the
# Retinue display category did not survive the old rollback. Restore it now so
# genuine retinues from every Legion have a valid battlefield-role target.
gcats = m.child(groot, 'categoryEntries', m.GNS)
if m.byid(groot, 'cat-retinue') is None:
    ET.SubElement(gcats, m.G('categoryEntry'), {
        'id':'cat-retinue','name':'Retinue','hidden':'false'
    })
force = m.byid(groot, 'force-standard')
if force is None:
    raise RuntimeError('Standard Age of Darkness Detachment not found')
flinks = m.child(force, 'categoryLinks', m.GNS)
if m.byid(groot, 'fl-retinue') is None:
    ET.SubElement(flinks, m.G('categoryLink'), {
        'id':'fl-retinue','name':'Retinue','hidden':'false','targetId':'cat-retinue'
    })

legion_map = {L['roman']: f"legion-{L['roman'].lower()}" for L in m.LEGIONS}
refs_added, rites_added = m.add_legion_references_and_rites(root, legion_map)
consuls_added = m.add_special_consuls(root, legion_map)

legion_units = 0
for L in m.LEGIONS:
    if L['roman'] == 'I':
        continue  # Dark Angels are the hand-finished reference implementation.
    lid = legion_map[L['roman']]
    for idx, entry in enumerate(L.get('entries', [])):
        uid = f"r41-unit-{m.slug(L['roman'])}-{idx}-{m.slug(entry['title'])}"
        m.materialise_unit(root, entry, uid, legion_id=lid, allegiance=entry.get('allegiance'))
        legion_units += 1

# The GST changed, so bump it once and keep the catalogue reference in lockstep.
groot.set('revision', str(int(groot.get('revision','13')) + 1))
root.set('gameSystemRevision', groot.get('revision'))
root.set('revision', '41')
comment = root.find(m.C('comment'))
if comment is None:
    comment = ET.Element(m.C('comment'))
    root.insert(0, comment)
comment.text = ('Revision 41 staging: restored all non-Dark-Angels Legion packages from the final Forces of the Legions source as the foundation for the same hand-finished implementation standard used by Dark Angels. Experimental Wargear and Units remains excluded.')

ctree.write(m.CAT_PATH, encoding='UTF-8', xml_declaration=True)
gtree.write(m.GST_PATH, encoding='UTF-8', xml_declaration=True)
print(f'REV41 IMPORT: references={refs_added} rites={rites_added} specialist_consuls={consuls_added} legion_units={legion_units} GST={groot.get("revision")}')
