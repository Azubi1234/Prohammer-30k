from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot()
print('CAT REV',cr.get('revision'),'GST REV',gr.get('revision'))
print('\nLEGION CANDIDATES')
for e in cr.iter(C('selectionEntry')):
    n=(e.get('name') or '').lower(); i=e.get('id','')
    if 'space wolves' in n or i.startswith('legion-'):
        print('ENTRY',i,'::',e.get('name'),'type=',e.get('type'),'hidden=',e.get('hidden'))
print('\nCONSUL CANDIDATES')
for e in cr.iter(C('selectionEntry')):
    n=(e.get('name') or '').lower()
    if 'chaplain' in n or 'librarian' in n or 'consul' in n:
        print('ENTRY',e.get('id'),'::',e.get('name'),'type=',e.get('type'),'hidden=',e.get('hidden'))
print('\nFORCE ENTRIES')
for f in gr.iter(G('forceEntry')):
    print('FORCE',f.get('id'),'::',f.get('name'))
    cs=f.find(G('constraints'))
    if cs is not None:
        for c in cs.findall(G('constraint')):
            print('  CON',c.attrib)
    ms=f.find(G('modifiers'))
    if ms is not None:
        for m in ms.findall(G('modifier')):
            print('  MOD',m.attrib)
            print('   ',ET.tostring(m,encoding='unicode')[:2500])
print('\nPTS COST TYPES')
for e in list(cr.iter())+list(gr.iter()):
    if e.tag.endswith('costType') or e.tag.endswith('cost'):
        if e.get('name')=='Points' or e.get('typeId')=='pts' or e.get('id')=='pts': print(e.tag,e.attrib)
