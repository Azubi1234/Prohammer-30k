from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse(CAT).getroot()

def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def parent_of(target):
    for p in cr.iter():
        for c in list(p):
            if c is target:return p
    return None

def all_names(q):
    q=q.lower()
    for e in cr.iter(C('selectionEntry')):
        if q in (e.get('name') or '').lower():
            p=parent_of(e); print('MATCH',e.get('id'),repr(e.get('name')),'type',e.get('type'),'parent',p.tag.split('}')[-1] if p is not None else None,p.get('id') if p is not None else None,p.get('name') if p is not None else None)

def dump(i,limit=12000):
    e=by_id(i); print('\nDUMP',i,'FOUND',e is not None)
    if e is not None: print(ET.tostring(e,encoding='unicode')[:limit])

for q in ['Rhino','Drop Pod','Dreadclaw','Dreadnought Drop Pod','Legion Command Squad','Terminator Command Squad','Honour Guard Squad','Psychic Hood','Power Weapon','Frost']:
    print('\n###',q); all_names(q)
for i in ['hq-praetor-retinue','hq-centurion-retinue','sgt-armoury','terminator-sgt-armoury','hq-centurion-consuls','r61-librarian-power2','r41-unit-vi-0-grey-slayer-pack','r41-unit-vi-5-varagyr-wolf-guard-terminators']:
    dump(i)
