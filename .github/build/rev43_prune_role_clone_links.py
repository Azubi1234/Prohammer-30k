import xml.etree.ElementTree as ET
from pathlib import Path
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot()
ids={e.get('id') for e in cr.iter() if e.get('id')}|{e.get('id') for e in gr.iter() if e.get('id')}
removed=[]
for parent in list(cr.iter()):
    for node in list(parent):
        # Only prune unresolved target links inside generated r43 role copies.
        inside=False
        p=parent
        # ElementTree has no parent pointers, so identify by generated node id itself.
        if node.get('id','').startswith('r43-ws-bike-troops-') or node.get('id','').startswith('r43-ws-sagyar-ebon-troops-'):
            inside=True
        target=node.get('targetId')
        if inside and target and target not in ids:
            removed.append((node.get('id'),target)); parent.remove(node)
ET.ElementTree(cr).write(CAT,encoding='UTF-8',xml_declaration=True)
print('Pruned obsolete unresolved links from r43 role clones:',removed)
