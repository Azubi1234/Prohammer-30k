from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse(CAT).getroot()
def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
for uid in ['tactical-unit','veteran-unit','destroyer-unit','terminator-unit','recon-unit','breacher-unit']:
    u=by_id(uid); print('\nUNIT',uid,u.get('name') if u is not None else None)
    if u is None:continue
    for g in u.iter(C('selectionEntryGroup')):
        if 'transport' in (g.get('name') or '').lower(): print(ET.tostring(g,encoding='unicode')[:9000])
    for l in u.iter(C('entryLink')):
        if any(s in (l.get('name') or '').lower() for s in ['rhino','drop pod','dreadclaw','land raider','spartan']): print('DIRECTLINK',ET.tostring(l,encoding='unicode')[:3000])
