from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot()
def by_id(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
for i in ['legion-vi','r25-consul-vi-wolf-priest-consul','r25-consul-vi-rune-priest-consul']:
    x=by_id(cr,i); print('\nNODE',i,'FOUND',x is not None)
    if x is not None: print(ET.tostring(x,encoding='unicode')[:18000])
print('\nGAME SYSTEM CATEGORY ENTRIES')
for e in gr.iter(G('categoryEntry')):
    print(e.get('id'),e.get('name'),ET.tostring(e,encoding='unicode')[:3000])
print('\nCATALOGUE FORCE ENTRIES')
for f in cr.iter(C('forceEntry')):
    print('FORCE',f.get('id'),f.get('name')); print(ET.tostring(f,encoding='unicode')[:10000])
print('\nGAME SYSTEM FORCE ENTRIES')
for f in gr.iter(G('forceEntry')):
    print('FORCE',f.get('id'),f.get('name')); print(ET.tostring(f,encoding='unicode')[:10000])
print('\nPOINT-COST CONDITIONS / MODIFIERS')
for root,label,ns in [(cr,'CAT',CNS),(gr,'GST',GNS)]:
    for e in root.iter():
        attrs=' '.join(f'{k}={v}' for k,v in e.attrib.items())
        if 'pts' in attrs.lower() or 'point' in attrs.lower():
            tag=e.tag.split('}')[-1]
            if tag in ('condition','constraint','modifier','conditionGroup'):
                print(label,tag,e.attrib)
