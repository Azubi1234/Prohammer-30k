from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat');OUT=Path('inspection-r83-scions-candidates.txt');NS='http://www.battlescribe.net/schema/catalogueSchema';C=lambda t:f'{{{NS}}}{t}'
r=ET.parse(CAT).getroot();ids=['tactical-unit','breacher-unit','recon-unit','veteran-unit','destroyer-unit','fa-seeker','hs-heavy-support-squad','hq-praetor-ret-command','hq-praetor-ret-honour','hq-centurion-ret-command','techmarine-covenant','r41-unit-x-0-medusan-immortal-squad']
def byid(i):return next((e for e in r.iter() if e.get('id')==i),None)
L=[]
for i in ids:
 u=byid(i);L.append('\n=== '+i+' '+(u.get('name') if u is not None else 'MISSING')+' ===')
 if u is None:continue
 for g in u.iter(C('selectionEntryGroup')):
  nm=g.get('name') or ''
  if 'transport' in nm.lower():
   L.append('GROUP '+str((g.get('id'),nm,g.get('hidden'))))
   for x in list(g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')))+list(g.findall('./'+C('entryLinks')+'/'+C('entryLink'))):L.append('  '+str((x.tag.split('}')[-1],x.get('id'),x.get('name'),x.get('targetId'),x.get('hidden'),x.get('type'))))
OUT.write_text('\n'.join(L),encoding='utf-8');print('\n'.join(L))
