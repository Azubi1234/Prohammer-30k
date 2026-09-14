from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse(CAT).getroot(); top=cr.find(C('selectionEntries'))
lines=[]
for e in list(top):
    eid=e.get('id',''); nm=e.get('name','')
    if eid.startswith('r41-unit-v-') or 'white scars' in nm.lower() or nm.lower() in ('golden keshig squadron','ebon keshig','dark sons of death','falcon’s claws','falcon\'s claws','qin xa, master of the keshig','targutai yesugei','shiban khan','hibou khan','hasik noyan-khan','v — jaghatai khan, the warhawk'):
        lines.append(f"UNIT {eid} :: {nm} :: type={e.get('type')} hidden={e.get('hidden')}")
        for r in e.findall('.//'+C('rule')):
            if (r.get('name') or '').strip().lower()=='source entry': lines.append('  SOURCE_ENTRY')
        for s in e.iter(C('selectionEntry')):
            if s is e: continue
            sn=s.get('name','')
            if s.get('type')=='model' or sn.startswith('Additional '):
                cons=[]
                cs=s.find(C('constraints'))
                if cs is not None:
                    cons=[(x.get('type'),x.get('value')) for x in cs.findall(C('constraint')) if x.get('field')=='selections']
                lines.append(f"  MODEL {s.get('id')} :: {sn} :: default={s.get('defaultAmount')} :: cons={cons}")
        lines.append('')
Path('inspection-r60-white-scars-diagnostic.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
