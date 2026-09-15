from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse(CAT).getroot()
def parent_of(target):
    for p in cr.iter():
        for c in list(p):
            if c is target:return p

def show(q):
    print('\n###',q)
    q=q.lower()
    for e in cr.iter():
        if q in (e.get('name') or '').lower():
            p=parent_of(e)
            print(e.tag.split('}')[-1],e.get('id'),repr(e.get('name')),'type',e.get('type'),'parent',p.tag.split('}')[-1] if p is not None else None,p.get('id') if p is not None else None)
            if e.tag==C('selectionEntry'):
                print(ET.tostring(e,encoding='unicode')[:3000])
for q in ['loyalist','traitor','allegiance','artillery tank','rapier','spartan assault','land raider battle','fortification','slow and purposeful','immobile','assault squad']:
    show(q)
