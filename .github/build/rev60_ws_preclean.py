from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
t=ET.parse(CAT); r=t.getroot()
removed=[]
for p in list(r.iter()):
    for x in list(p):
        xid=x.get('id','')
        target=x.get('targetId','')
        # Remove old Rev43 White Scars links/groups as well as links targeting the old Rev43 WS shared entries.
        if (xid.startswith('r43-') and ('-ws-' in xid or xid.startswith('r43-ws-'))) or target.startswith('r43-ws-'):
            p.remove(x); removed.append((x.tag.split('}')[-1],xid,target))
ET.register_namespace('',CNS); t.write(CAT,encoding='UTF-8',xml_declaration=True)
print(f'Removed {len(removed)} legacy Rev43 White Scars nodes/links')
for row in removed: print(row)
