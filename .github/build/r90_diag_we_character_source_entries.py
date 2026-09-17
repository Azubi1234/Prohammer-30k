from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat')
OUT=Path('inspection-r90-we-character-source-entry-diagnostic.txt')
NS='http://www.battlescribe.net/schema/catalogueSchema'
C=lambda t:f'{{{NS}}}{t}'
root=ET.parse(CAT).getroot()
PM={c:p for p in root.iter() for c in p}
IDMAP={e.get('id'):e for e in root.iter() if e.get('id')}

chars={
'r41-unit-xii-6-kharn-the-bloody':'Kharn',
'r41-unit-xii-7-shabran-darr':'Shabran Darr',
'r41-unit-xii-8-gahlan-surlak':'Gahlan Surlak',
'r41-unit-xii-9-kargos-the-bloodspitter':'Kargos',
'r41-unit-xii-10-captain-ehrlen':'Captain Ehrlen',
'r41-unit-xii-11-delvarus':'Delvarus',
'r41-unit-xii-12-xii-angron-the-red-angel':'Angron',
'r41-unit-xii-13-angron-the-red-angel':'Angron, the Red Angel',
}

def path(e):
    out=[]; x=e
    while x is not None and x is not root:
        out.append(f"{x.tag.split('}')[-1]}[{x.get('id') or ''}::{x.get('name') or ''}]")
        x=PM.get(x)
    return ' <- '.join(out)

def desc(e):
    parts=[]
    for d in e.findall('.//'+C('description')):
        if d.text: parts.append(d.text.strip())
    return '\n'.join(parts)

def suspicious(e):
    nm=(e.get('name') or '').lower()
    tx=desc(e).lower()
    return ('source entry' in nm or 'source entry' in tx or
            ('force organisation:' in tx and 'wargear:' in tx) or
            ('unit type:' in tx and 'special rules:' in tx and 'wargear:' in tx))

L=[]
L.append(f"CAT revision={root.get('revision')} GSTref={root.get('gameSystemRevision')}")
for uid,label in chars.items():
    u=IDMAP.get(uid)
    L.append('\n'+'='*120)
    L.append(f"{label} | {uid} | FOUND={u is not None}")
    if u is None: continue
    L.append(f"unit name={u.get('name')} hidden={u.get('hidden')}")
    # Direct groups and rules
    for g in u.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')):
        L.append(f"GROUP {g.get('id')} | {g.get('name')} | children={len(list(g))}")
    for r in u.findall('./'+C('rules')+'/'+C('rule')):
        d=r.find(C('description')); tx=(d.text or '') if d is not None else ''
        L.append(f"DIRECT RULE {r.get('id')} | {r.get('name')} :: {tx[:500]}")
    # Any suspicious descendant node
    sus=[]
    for e in u.iter():
        if suspicious(e): sus.append(e)
        target=e.get('targetId')
        if target and target in IDMAP and suspicious(IDMAP[target]):
            sus.append(e)
            L.append(f"LINK TO SUSPICIOUS TARGET: {path(e)} -> {target} :: target={IDMAP[target].get('name')}")
    L.append(f"SUSPICIOUS DESCENDANTS={len(sus)}")
    for e in sus:
        L.append('  '+path(e))
        if e.get('targetId'): L.append(f"    targetId={e.get('targetId')} targetName={(IDMAP.get(e.get('targetId')).get('name') if IDMAP.get(e.get('targetId')) is not None else 'MISSING')}")
        tx=desc(e)
        if tx: L.append('    DESC='+tx[:1200].replace('\n',' | '))
    # list infoLinks/entryLinks/profile refs and names so New Recruit display provenance can be seen
    for tag in ('infoLink','entryLink','profile','selectionEntry'):
        for e in u.iter(C(tag)):
            nm=e.get('name') or ''
            if tag in ('infoLink','entryLink') or 'source' in nm.lower():
                tgt=e.get('targetId') or ''
                tnm=IDMAP.get(tgt).get('name') if tgt and IDMAP.get(tgt) is not None else ''
                L.append(f"{tag.upper()} {e.get('id')} | {nm} | target={tgt}::{tnm} | {path(e)}")

# Global nodes specifically mentioning Delvarus / Source Entry to catch duplicates outside canonical entry
L.append('\n'+'='*120)
L.append('GLOBAL DELVARUS / SOURCE ENTRY NODES')
for e in root.iter():
    nm=(e.get('name') or '')
    tx=desc(e)
    if 'delvarus' in nm.lower() or ('source entry' in nm.lower() and 'delvarus' in tx.lower()) or ('delvarus' in tx.lower() and ('force organisation:' in tx.lower() or 'wargear:' in tx.lower())):
        L.append(path(e))
        if tx: L.append('  DESC='+tx[:1600].replace('\n',' | '))
        if e.get('targetId'):
            tgt=IDMAP.get(e.get('targetId'))
            L.append(f"  target={e.get('targetId')}::{tgt.get('name') if tgt is not None else 'MISSING'}")

OUT.write_text('\n'.join(L),encoding='utf-8')
print('\n'.join(L[-500:]))
