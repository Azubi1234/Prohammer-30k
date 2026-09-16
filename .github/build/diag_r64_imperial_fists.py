from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot()
print('CATREV',cr.get('revision'),'GSTREV',gr.get('revision'))
print('\nVII IMPORTED UNITS')
for e in cr.iter(C('selectionEntry')):
    if (e.get('id') or '').startswith('r41-unit-vii-'):
        cats=[(x.get('targetId'),x.get('name'),x.get('primary')) for x in e.findall('./'+C('categoryLinks')+'/'+C('categoryLink'))]
        print(e.get('id'),repr(e.get('name')),'type=',e.get('type'),'cats=',cats)
print('\nVII RITES')
for e in cr.iter():
    if 'rite-vii' in (e.get('id') or ''):
        print(e.tag.split('}')[-1],e.get('id'),repr(e.get('name')))
print('\nR44 IF LINKS/ENTRIES')
for e in cr.iter():
    if (e.get('id') or '').startswith('r44-if-') or ((e.get('id') or '').startswith('r44-') and 'if-' in (e.get('id') or '')):
        print(e.tag.split('}')[-1],e.get('id'),repr(e.get('name')),'target=',e.get('targetId'))
print('\nCORE TARGETS')
for ident in ['hq-praetor','hq-centurion','hq-centurion-consuls','tactical-unit','assault-unit','breacher-unit','recon-unit','veteran-unit','terminator-unit','fa-seeker','hs-heavy-support-squad','hs-land-raider','hs-spartan','transport-rhino','transport-drop-pod','transport-dreadclaw','fl-fast','fl-troops','fl-elites','fl-hq','fl-heavy']:
    obj=next((e for e in cr.iter() if e.get('id')==ident),None)
    if obj is None: obj=next((e for e in gr.iter() if e.get('id')==ident),None)
    print(ident,'=>',obj.tag.split('}')[-1] if obj is not None else None,repr(obj.get('name')) if obj is not None else None)
print('\nCOMMAND / TERMINATOR / FORTIFICATION TARGETS')
for e in cr.iter(C('selectionEntry')):
    n=(e.get('name') or '').lower(); i=(e.get('id') or '').lower()
    if ('command squad' in n or 'honour guard' in n or 'terminator armour' in n or 'fortification' in n or 'bunker' in n or 'defence line' in n):
        print(e.get('id'),repr(e.get('name')),'type=',e.get('type'))
print('\nPRAETOR/CENTURION GROUPS')
for uid in ['hq-praetor','hq-centurion']:
    u=next((e for e in cr.iter(C('selectionEntry')) if e.get('id')==uid),None)
    print('UNIT',uid)
    if u is not None:
        for g in u.iter(C('selectionEntryGroup')):
            print(' group',g.get('id'),repr(g.get('name')))
        for e in u.iter(C('selectionEntry')):
            if e is not u and ('armour' in (e.get('name') or '').lower() or 'shield' in (e.get('name') or '').lower()):
                print(' option',e.get('id'),repr(e.get('name')))
print('\nALLEGIANCE')
for e in cr.iter():
    if 'allegiance' in (e.get('id') or '').lower() or 'allegiance' in (e.get('name') or '').lower():
        print(e.tag.split('}')[-1],e.get('id'),repr(e.get('name')))
# trigger 2
