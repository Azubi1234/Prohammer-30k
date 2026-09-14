from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot()
keys=('emperor','palatine','phoenix','kakophoni','sun killer','lucius','eidolon','tarvitz','fabius','rylanor','fulgrim','command squad','honour guard','heavy support squad','praetor','centurion','allegiance','maru skara','3rd company')
lines=[]
lines.append(f"CAT rev={cr.get('revision')} GSR={cr.get('gameSystemRevision')} GST rev={gr.get('revision')}")
lines.append('\n=== MATCHING SELECTION ENTRIES / LINKS / GROUPS ===')
for e in cr.iter():
    nm=(e.get('name') or '').lower(); tag=e.tag.split('}')[-1]
    if any(k in nm for k in keys) and tag in ('selectionEntry','entryLink','selectionEntryGroup','categoryLink'):
        lines.append(f"{tag:20} id={e.get('id')} name={e.get('name')} type={e.get('type')} target={e.get('targetId')} hidden={e.get('hidden')} primary={e.get('primary')}")

lines.append('\n=== EC TOP ENTRIES STRUCTURE ===')
top=cr.find(C('selectionEntries'))
for e in list(top) if top is not None else []:
    nm=(e.get('name') or '').lower()
    if e.get('id','').startswith('r41-unit-iii-') or any(k in nm for k in ('lucius','eidolon','tarvitz','fabius','rylanor','fulgrim','kakophoni','sun killer')):
        lines.append(f"\nENTRY {e.get('id')} :: {e.get('name')} type={e.get('type')} hidden={e.get('hidden')}")
        for ch in list(e):
            lines.append(f"  {ch.tag.split('}')[-1]}")
            if ch.tag==C('rules'):
                for r in ch.findall(C('rule')): lines.append(f"    RULE {r.get('id')} :: {r.get('name')}")
            if ch.tag==C('selectionEntries'):
                for s in ch.findall(C('selectionEntry')): lines.append(f"    SEL {s.get('id')} :: {s.get('name')} type={s.get('type')}")
            if ch.tag==C('selectionEntryGroups'):
                for g in ch.findall(C('selectionEntryGroup')):
                    lines.append(f"    GROUP {g.get('id')} :: {g.get('name')}")
                    for s in g.findall('.//'+C('selectionEntry')): lines.append(f"      SEL {s.get('id')} :: {s.get('name')}")
                    for l in g.findall('.//'+C('entryLink')): lines.append(f"      LINK {l.get('id')} :: {l.get('name')} -> {l.get('targetId')}")
            if ch.tag==C('entryLinks'):
                for l in ch.findall(C('entryLink')): lines.append(f"    LINK {l.get('id')} :: {l.get('name')} -> {l.get('targetId')}")
            if ch.tag==C('categoryLinks'):
                for l in ch.findall(C('categoryLink')): lines.append(f"    CAT {l.get('name')} -> {l.get('targetId')} primary={l.get('primary')}")

lines.append('\n=== GST FORCE LINKS ===')
for e in gr.iter():
    if e.tag in (G('categoryLink'),G('forceEntry')):
        nm=(e.get('name') or '').lower()
        if any(k in nm for k in ('heavy','troop','hq','elite','fast','fortification','lord')):
            lines.append(f"{e.tag.split('}')[-1]} id={e.get('id')} name={e.get('name')} target={e.get('targetId')}")

Path('inspection-r52-ec-diagnostic.txt').write_text('\n'.join(lines), encoding='utf-8')
print('\n'.join(lines[:180]))
