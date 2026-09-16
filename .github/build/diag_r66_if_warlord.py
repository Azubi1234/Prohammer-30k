import xml.etree.ElementTree as ET
from pathlib import Path
CAT=Path('Legiones Astartes.cat')
CNS='http://www.battlescribe.net/schema/catalogueSchema'
C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse(CAT).getroot()
byid=lambda i: next((e for e in cr.iter() if e.get('id')==i),None)
print('CATREV',cr.get('revision'))
for uid in ['hq-praetor','hq-centurion']:
    u=byid(uid); print('\n',uid,u.get('name') if u is not None else None)
    if u is None: continue
    for e in u.iter():
        n=(e.get('name') or '')
        low=n.lower()
        if any(k in low for k in ['power weapon','rending weapon','relic blade','boarding shield','teleportation transponder','vigil pattern storm shield']):
            print(e.tag.split('}')[-1],e.get('id'),repr(n),'target=',e.get('targetId'),'hidden=',e.get('hidden'))
print('\nNAMED IF LINKS')
for uid in ['r41-unit-vii-4-sigismund-first-captain','r41-unit-vii-5-fafnir-rann','r41-unit-vii-6-alexis-polux','r41-unit-vii-7-camba-diaz','r41-unit-vii-8-evander-garrius']:
    u=byid(uid); print('\n',uid,u.get('name') if u is not None else None)
    if u is None: continue
    for e in u.iter(C('entryLink')):
        print('entryLink',e.get('id'),repr(e.get('name')),'target=',e.get('targetId'),'hidden=',e.get('hidden'))
