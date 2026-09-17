from pathlib import Path
import re
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat')
GST=Path('Prohammer 30k.gst')
IDX=Path('index.xml')
OUT=Path('inspection-r90-world-eaters-force-refresh.txt')

CNS='http://www.battlescribe.net/schema/catalogueSchema'
GNS='http://www.battlescribe.net/schema/gameSystemSchema'
ET.register_namespace('',CNS)
ET.register_namespace('',GNS)
C=lambda t:f'{{{CNS}}}{t}'
G=lambda t:f'{{{GNS}}}{t}'

ct=ET.parse(CAT); cr=ct.getroot()
gt=ET.parse(GST); gr=gt.getroot()

if cr.get('revision')!='89' or cr.get('gameSystemRevision')!='51' or gr.get('revision')!='51':
    raise RuntimeError(f'Expected CAT89/GSTref51/GST51, got CAT{cr.get("revision")}/GSTref{cr.get("gameSystemRevision")}/GST{gr.get("revision")}')

def byid(root,i):
    return next((e for e in root.iter() if e.get('id')==i),None)

def text_blob(u):
    vals=[]
    for e in u.iter():
        if e.get('name'): vals.append(e.get('name'))
        if e.text and e.text.strip(): vals.append(e.text.strip())
    return '\n'.join(vals)

chars={
 'r41-unit-xii-6-kharn-the-bloody':'KHÂRN THE BLOODY',
 'r41-unit-xii-7-shabran-darr':'SHABRAN DARR',
 'r41-unit-xii-8-gahlan-surlak':'GAHLAN SURLAK',
 'r41-unit-xii-9-kargos-the-bloodspitter':'KARGOS, THE BLOODSPITTER',
 'r41-unit-xii-10-captain-ehrlen':'CAPTAIN EHRLEN',
 'r41-unit-xii-11-delvarus':'DELVARUS',
 'r41-unit-xii-12-xii-angron-the-red-angel':'XII — ANGRON, THE RED ANGEL',
 'r41-unit-xii-13-angron-the-red-angel':'ANGRON, THE RED ANGEL',
}

lines=[]
for uid,canon_name in chars.items():
    u=byid(cr,uid)
    if u is None: raise RuntimeError('Missing '+uid)
    u.set('name',canon_name)
    # Hard regression: no legacy aggregate source dump anywhere under the character.
    bad=[]
    for e in u.iter():
        nm=(e.get('name') or '').strip().lower()
        tx=(e.text or '').strip().lower()
        if nm.startswith('source entry'):
            bad.append((e.tag.split('}')[-1],e.get('id'),e.get('name')))
        if 'force organisation:' in tx and 'wargear:' in tx and 'special rules:' in tx:
            bad.append((e.tag.split('}')[-1],e.get('id'),'aggregate description'))
    if bad: raise RuntimeError(f'{canon_name} still contains source dump: {bad}')
    # Confirm structured sections exist on every named WE character.
    groups=[(g.get('name') or '') for g in u.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup'))]
    if not any(x=='Wargear' for x in groups): raise RuntimeError(canon_name+' missing Wargear group')
    if not any(x=='Special Rules' for x in groups): raise RuntimeError(canon_name+' missing Special Rules group')
    lines.append(f'{canon_name}: clean structured entry; no Source Entry dump')

# Force New Recruit to invalidate both catalogue-level and game-system-level caches.
# This deliberately changes no rules in the GST; it is a cache-busting revision bump.
gr.set('revision','52')
cr.set('gameSystemRevision','52')
cr.set('revision','90')

# Add/update catalogue comment as an easy raw-file sanity marker.
comment=cr.find(C('comment'))
if comment is None:
    comment=ET.Element(C('comment')); cr.insert(0,comment)
comment.text='Revision 90: World Eaters character cleanup verified; forced full New Recruit refresh by bumping both catalogue and game-system revisions. Gahlan Surlak capitalization corrected.'

ct.write(CAT,encoding='utf-8',xml_declaration=True)
gt.write(GST,encoding='utf-8',xml_declaration=True)

# Normalize default namespaces after ElementTree output.
raw=CAT.read_text(encoding='utf-8').replace(f'xmlns:ns0="{CNS}"',f'xmlns="{CNS}"').replace('<ns0:','<').replace('</ns0:','</')
CAT.write_text(raw,encoding='utf-8')
raw=GST.read_text(encoding='utf-8').replace(f'xmlns:ns0="{GNS}"',f'xmlns="{GNS}"').replace('<ns0:','<').replace('</ns0:','</')
GST.write_text(raw,encoding='utf-8')

idx=IDX.read_text(encoding='utf-8')
idx,n1=re.subn(r'(filePath="Prohammer 30k\.gst"[^>]*dataRevision=")51(" )',r'\g<1>52\g<2>',idx,count=1)
idx,n2=re.subn(r'(filePath="Legiones Astartes\.cat"[^>]*dataRevision=")89(" )',r'\g<1>90\g<2>',idx,count=1)
if n1!=1 or n2!=1: raise RuntimeError(f'index bump failed GST={n1} CAT={n2}')
IDX.write_text(idx,encoding='utf-8')

# Final parse checks.
cr2=ET.parse(CAT).getroot(); gr2=ET.parse(GST).getroot()
assert cr2.get('revision')=='90'
assert cr2.get('gameSystemRevision')=='52'
assert gr2.get('revision')=='52'
assert byid(cr2,'r41-unit-xii-8-gahlan-surlak').get('name')=='GAHLAN SURLAK'

OUT.write_text('Revision 90 — World Eaters forced refresh\nCAT=90 GSTref=52 GST=52\n\n'+'\n'.join(lines)+'\n\nCache-busting action: bumped both catalogue and game-system revisions so New Recruit must rebuild the game data rather than reusing a stale CAT89/GST51 resolved copy.\n',encoding='utf-8')
print(OUT.read_text())
