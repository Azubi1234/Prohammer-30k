from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); OUT=Path('inspection-r71-night-lords-support.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot(); L=[]; a=L.append

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def primary(e):
    x=e.find(C('categoryLinks'))
    if x is None:return ''
    return ','.join((c.get('name') or c.get('targetId') or '') for c in x.findall(C('categoryLink')) if c.get('primary')=='true')
def cons(e,T=C):
    out=[]
    q=e.find(T('constraints'))
    if q is not None:
        for c in q.findall(T('constraint')): out.append(f"{c.get('id')}:{c.get('type')}={c.get('value')} field={c.get('field')} scope={c.get('scope')}")
    return '; '.join(out)

a('=== CAT ALLEGIANCE / TRAITOR / LOYALIST OBJECTS ===')
for e in cr.iter():
    n=(e.get('name') or '').lower(); i=(e.get('id') or '').lower()
    if 'traitor' in n or 'loyalist' in n or 'allegiance' in n or 'traitor' in i or 'loyal' in i:
        a(f"{e.tag.split('}')[-1]} {e.get('id')} | {e.get('name')} | target={e.get('targetId')} hidden={e.get('hidden')} {cons(e)}")

a('\n=== GST FORCE / CATEGORY LINKS ===')
force=byid(gr,'force-standard')
if force is not None:
    for e in force.iter():
        if e.tag in (G('categoryLink'),G('constraint')):
            a(f"{e.tag.split('}')[-1]} {e.get('id')} | {e.get('name')} -> {e.get('targetId')} | {cons(e,G) if e.tag==G('categoryLink') else f'{e.get("type")}={e.get("value")} field={e.get("field")} scope={e.get("scope")}'}")

a('\n=== GST CATEGORY ENTRIES FORT/HQ/ALLEGIANCE ===')
for e in gr.iter(G('categoryEntry')):
    n=(e.get('name') or '').lower()
    if any(k in n for k in ('fort','headquarters','hq','alleg','traitor','loyal')): a(f"{e.get('id')} | {e.get('name')} hidden={e.get('hidden')}")

a('\n=== GENERIC RETINUE / HQ SOURCES ===')
top=cr.find(C('selectionEntries'))
for e in list(top) if top is not None else []:
    n=(e.get('name') or '').lower(); i=e.get('id') or ''
    if any(k in n for k in ('command squad','honour guard','veteran squad','terminator command')) or i in ('hq-praetor','hq-centurion'):
        a(f"{i} | {e.get('name')} | primary={primary(e)} | hidden={e.get('hidden')} {cons(e)}")

a('\n=== ALL TOP HQ ENTRIES ===')
for e in list(top) if top is not None else []:
    if 'HQ' in primary(e): a(f"{e.get('id')} | {e.get('name')} | {cons(e)}")

a('\n=== STANDARD UNIT GROUP NAMES FOR SERGEANT ARMOURY ===')
for ident in ('tactical-unit','assault-unit','breacher-unit','recon-unit','veteran-unit','destroyer-unit','fa-seeker','hs-heavy-support-squad'):
    e=byid(cr,ident); a(f'ENTRY {ident} {e.get("name") if e is not None else "MISSING"}')
    if e is not None:
        for g in e.iter(C('selectionEntryGroup')):
            n=g.get('name') or ''
            if any(k in n.lower() for k in ('sergeant','armoury','weapon','wargear')): a(f"  GROUP {g.get('id')} | {n} | {cons(g)}")

OUT.write_text('\n'.join(L),encoding='utf-8'); print('\n'.join(L))
