import xml.etree.ElementTree as ET
from pathlib import Path
CAT=Path('Legiones Astartes.cat')
NS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{NS}}}{t}'
r=ET.parse(CAT).getroot()
byid=lambda i: next((e for e in r.iter() if e.get('id')==i),None)
def rec(e,depth=0,maxd=5):
    if e is None or depth>maxd:return
    tag=e.tag.split('}')[-1]
    if tag in ('selectionEntry','selectionEntryGroup','entryLink','constraint','modifier','condition','rule'):
        print('  '*depth,tag,'id=',e.get('id'),'name=',repr(e.get('name')),'type=',e.get('type'),'hidden=',e.get('hidden'),'default=',e.get('defaultAmount'),'target=',e.get('targetId'),'field=',e.get('field'),'scope=',e.get('scope'),'value=',e.get('value'))
    for x in list(e): rec(x,depth+1,maxd)
for ident in ['r41-unit-vii-4-sigismund-first-captain','r41-unit-vi-7-hvarl-red-blade']:
    u=byid(ident); print('\n###',ident, u.get('name') if u is not None else None)
    rec(u,0,6)
