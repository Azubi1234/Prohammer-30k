import xml.etree.ElementTree as ET
from pathlib import Path
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot()
print('REVS',cr.get('revision'),gr.get('revision'))
print('\nBOARDING / SHIELD / TRANSPONDER MATCHES')
for e in cr.iter():
    n=(e.get('name') or '').lower(); i=(e.get('id') or '')
    if 'boarding shield' in n or 'vigil pattern storm shield' in n or 'teleportation transponder' in n or 'teleport transponder' in n:
        print(e.tag.split('}')[-1],i,repr(e.get('name')),'target=',e.get('targetId'))
print('\nFORTIFICATION-LIKE CATALOGUE ENTRIES')
for e in cr.iter(C('selectionEntry')):
    n=(e.get('name') or '').lower();
    cats=[(x.get('targetId'),x.get('name'),x.get('primary')) for x in e.findall('./'+C('categoryLinks')+'/'+C('categoryLink'))]
    if 'fortification' in n or 'bunker' in n or 'defence line' in n or 'defense line' in n or any('fort' in ((x[1] or '').lower()) for x in cats):
        print(e.get('id'),repr(e.get('name')),'cats=',cats)
print('\nGST FORCE CATEGORY LINKS')
force=next((e for e in gr.iter() if e.get('id')=='force-standard'),None)
if force is not None:
    for l in force.findall('./'+G('categoryLinks')+'/'+G('categoryLink')):
        print(l.get('id'),repr(l.get('name')),'target=',l.get('targetId'))
print('\nGENERIC HQ WEAPON/SHIELD OPTIONS')
for uid in ('hq-praetor','hq-centurion'):
    u=next((e for e in cr.iter(C('selectionEntry')) if e.get('id')==uid),None)
    print('UNIT',uid)
    if u is not None:
        for e in u.iter(C('selectionEntry')):
            n=(e.get('name') or '').lower()
            if any(k in n for k in ('boarding shield','power weapon','relic blade','rending','paragon','charna','storm shield')):
                print(' ',e.get('id'),repr(e.get('name')))
print('\nIMPERIAL FISTS NAMED CHARACTERS')
for e in cr.iter(C('selectionEntry')):
    if (e.get('id') or '').startswith('r41-unit-vii-') and any(k in (e.get('name') or '').upper() for k in ('SIGISMUND','FAFNIR','POLUX','DIAZ','GARRIUS')):
        print(e.get('id'),repr(e.get('name')))
