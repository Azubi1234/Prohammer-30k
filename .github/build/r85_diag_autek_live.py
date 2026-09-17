from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); OUT=Path('inspection-r85-autek-live.txt')
NS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{NS}}}{t}'
root=ET.parse(CAT).getroot()
uid='r41-unit-x-5-autek-mor'
u=next((e for e in root.iter(C('selectionEntry')) if e.get('id')==uid),None)
if u is None: raise RuntimeError('Autek not found')
L=[f'CAT revision={root.get("revision")} GSTref={root.get("gameSystemRevision")}', f'Autek id={u.get("id")} name={u.get("name")}']
# dump all rule/info/profile nodes anywhere below Autek
for e in u.iter():
    tag=e.tag.split('}')[-1]
    if tag in ('rule','infoLink','profile','selectionEntry','selectionEntryGroup','entryLink'):
        name=e.get('name'); target=e.get('targetId'); typ=e.get('type');
        if tag in ('rule','infoLink','profile') or (name and ('source' in name.lower() or 'autek' in name.lower())):
            L.append(f'{tag} id={e.get("id")} name={name} target={target} type={typ}')
            if tag=='rule':
                d=e.find(C('description')); L.append('  DESC='+(((d.text or '') if d is not None else '')[:1000]).replace('\n',' '))
# exact source-ish content scan within serialized subtree
sub=ET.tostring(u,encoding='unicode')
L += ['', f'contains literal Source Entry={"Source Entry" in sub}', f'contains Force Organisation={"Force Organisation" in sub}', f'contains BATTLESMITH={"BATTLESMITH" in sub}']
OUT.write_text('\n'.join(L),encoding='utf-8')
print(OUT.read_text(encoding='utf-8'))
