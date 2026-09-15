from pathlib import Path
import xml.etree.ElementTree as ET
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse(Path('Legiones Astartes.cat')).getroot()
def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
for i in ['hq-praetor-ret-honour-land','hq-centurion-ret-command-land','veteran-transport','r60-ws-dark-transport']:
    x=by_id(i)
    print('\nID',i,'FOUND',x is not None,'TAG',x.tag if x is not None else None,'NAME',x.get('name') if x is not None else None)
    if x is not None:
        print(ET.tostring(x,encoding='unicode')[:12000])
