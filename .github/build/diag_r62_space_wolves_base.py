from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse(CAT).getroot()

def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def parent_of(node):
    for p in cr.iter():
        if node in list(p): return p
    return None

def dump_node(i):
    x=by_id(i)
    print('\nNODE',i,'FOUND',x is not None)
    if x is None:return
    print(' TAG',x.tag.split('}')[-1],'NAME',x.get('name'),'TYPE',x.get('type'),'HIDDEN',x.get('hidden'))
    p=parent_of(x)
    print(' PARENT',p.tag.split('}')[-1] if p is not None else None,p.get('id') if p is not None else None,p.get('name') if p is not None else None)
    if p is not None:
        for ch in list(p):
            print('   SIB',ch.tag.split('}')[-1],ch.get('id'),ch.get('name'),ch.get('type'),ch.get('hidden'))
    print(' XML',ET.tostring(x,encoding='unicode')[:8000])

for i in ['legion-v','legion-ws','legion-da','hq-consul-chaplain','hq-consul-librarian','cat-hq']:
    dump_node(i)

print('\nSPACE WOLVES NAMED OBJECTS')
for e in cr.iter():
    if 'space wolves' in (e.get('name') or '').lower() or 'space wolf' in (e.get('name') or '').lower():
        print(e.tag.split('}')[-1],e.get('id'),e.get('name'),e.get('type'),e.get('hidden'))

print('\nCATEGORY ENTRIES')
for e in cr.iter(C('categoryEntry')):
    print(e.get('id'),e.get('name'),ET.tostring(e,encoding='unicode')[:3000])
