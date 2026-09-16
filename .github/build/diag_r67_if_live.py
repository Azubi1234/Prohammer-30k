import xml.etree.ElementTree as ET
from pathlib import Path
CAT=Path('Legiones Astartes.cat')
CNS='http://www.battlescribe.net/schema/catalogueSchema'
C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse(CAT).getroot()
byid=lambda i: next((e for e in cr.iter() if e.get('id')==i),None)
print('REV',cr.get('revision'),'GSR',cr.get('gameSystemRevision'),'TAG',cr.tag)
IDS=[
'r41-unit-vii-0-templar-brethren-squad','r41-unit-vii-1-phalanx-warder-squad','r41-unit-vii-2-huscarl-terminator-retinue','r41-unit-vii-3-tarantula-sentry-gun-battery',
'r41-unit-vii-4-sigismund-first-captain','r41-unit-vii-5-fafnir-rann','r41-unit-vii-6-alexis-polux','r41-unit-vii-7-camba-diaz','r41-unit-vii-8-evander-garrius','r41-unit-vii-9-vii-rogal-dorn-the-praetorian-of-terra']
for uid in IDS:
    u=byid(uid); print('\nENTRY',uid,repr(u.get('name') if u is not None else None))
    if u is None: continue
    print('costs',[(x.get('value'),x.get('typeId')) for x in u.findall('./'+C('costs')+'/'+C('cost'))])
    print('profiles',[(x.get('id'),x.get('name'),x.get('typeName')) for x in u.findall('./'+C('profiles')+'/'+C('profile'))])
    print('rules',[(x.get('id'),x.get('name')) for x in u.findall('./'+C('rules')+'/'+C('rule'))])
    print('sels',[(x.get('id'),x.get('name'),x.get('defaultAmount')) for x in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry'))])
    print('groups',[(x.get('id'),x.get('name')) for x in u.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup'))])
    print('links',[(x.get('id'),x.get('name'),x.get('targetId'),x.get('defaultAmount')) for x in u.findall('./'+C('entryLinks')+'/'+C('entryLink'))])

for uid in ('tactical-unit','hq-praetor','hq-centurion'):
    u=byid(uid); print('\nGENERIC',uid,repr(u.get('name') if u is not None else None))
    if u is None: continue
    for g in u.iter(C('selectionEntryGroup')):
        n=(g.get('name') or '')
        if 'armour' in n.lower() or 'sergeant' in n.lower() or 'wargear' in n.lower():
            print(' GROUP',g.get('id'),repr(n))
            for l in g.findall('./'+C('entryLinks')+'/'+C('entryLink'))[:40]: print('  LINK',l.get('id'),repr(l.get('name')),l.get('targetId'))
