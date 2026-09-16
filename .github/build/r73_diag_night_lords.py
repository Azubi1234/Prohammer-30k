from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); OUT=Path('inspection-r73-night-lords-diag.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot()

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def parent_map(root): return {c:p for p in root.iter() for c in p}
def ancestry(root,node):
    pm=parent_map(root); names=[]; cur=node
    while cur is not None:
        names.append(f"{cur.tag.split('}')[-1]}:{cur.get('name','')}[{cur.get('id','')}]")
        cur=pm.get(cur)
    return ' <- '.join(names[:8])

lines=[]
lines.append(f"CAT revision={cr.get('revision')} gameSystemRevision={cr.get('gameSystemRevision')} GST revision={gr.get('revision')}")

# Rule/profile definitions we need to wire as actual links rather than prose dumps.
need=['Legiones Astartes','Infiltrate','Preferred Enemy','Hit & Run','Stubborn','Fearless','Deep Strike','Fear','Stealth','Independent Character','Master of the Legion','Psyker','Night Vision','Feel No Pain']
for root,label,T in [(cr,'CAT',C),(gr,'GST',G)]:
    lines.append(f"\n=== {label} matching definitions ===")
    for e in root.iter():
        n=(e.get('name') or '')
        if any(x.lower() in n.lower() for x in need):
            tag=e.tag.split('}')[-1]
            if tag in ('rule','profile','selectionEntry','selectionEntryGroup','infoLink','categoryEntry'):
                lines.append(f"{tag} id={e.get('id')} name={n} type={e.get('type')} typeId={e.get('typeId')} targetId={e.get('targetId')}")

IDS={
 'terror':'r41-unit-viii-0-terror-squad','raptor':'r41-unit-viii-1-night-raptor-squad','contekar':'r41-unit-viii-2-contekar-terminator-elite','atramentar':'r41-unit-viii-3-atramentar-flay-clade',
 'sevatar':'r41-unit-viii-4-jago-sevatarion','ophion':'r41-unit-viii-5-kheron-ophion','malcharion':'r41-unit-viii-6-malcharion-the-war-sage','shang':'r41-unit-viii-7-shang','mawdrym':'r41-unit-viii-8-flaymaster-mawdrym-llansahai','curze':'r41-unit-viii-9-viii-konrad-curze-the-night-haunter'}
for key,i in IDS.items():
    u=byid(cr,i); lines.append(f"\n=== {key} {i} ===")
    if u is None: lines.append('MISSING'); continue
    lines.append(f"name={u.get('name')} type={u.get('type')} hidden={u.get('hidden')}")
    lines.append('PROFILES:')
    for p in u.iter(C('profile')):
        lines.append(f"  id={p.get('id')} name={p.get('name')} typeName={p.get('typeName')} typeId={p.get('typeId')}")
    lines.append('LOCAL RULES:')
    for r in u.iter(C('rule')):
        desc=r.find(C('description')); lines.append(f"  id={r.get('id')} name={r.get('name')} desc={(desc.text or '')[:180] if desc is not None else ''}")
    lines.append('INFOLINKS:')
    for x in u.iter(C('infoLink')):
        lines.append(f"  id={x.get('id')} name={x.get('name')} type={x.get('type')} targetId={x.get('targetId')}")
    lines.append('STEALTH SELECTORS:')
    for x in u.iter(C('selectionEntry')):
        if 'stealth adept' in (x.get('name') or '').lower(): lines.append('  '+ancestry(cr,x))
    for x in u.iter(C('entryLink')):
        if 'stealth adept' in (x.get('name') or '').lower(): lines.append('  '+ancestry(cr,x)+f" target={x.get('targetId')}")

# Generic unit snapshot for how working units link actual rules/profiles.
for uid in ['tactical-unit','assault-unit','veteran-unit','terminator-unit','hq-praetor','hq-centurion']:
    u=byid(cr,uid); lines.append(f"\n=== GENERIC {uid} {u.get('name') if u is not None else 'MISSING'} ===")
    if u is None: continue
    for p in u.iter(C('profile')):
        lines.append(f"PROFILE {p.get('id')} {p.get('name')} {p.get('typeName')}")
    for x in u.iter(C('infoLink')):
        lines.append(f"INFOLINK {x.get('id')} {x.get('name')} {x.get('type')} -> {x.get('targetId')}")
    for x in u.iter(C('selectionEntry')):
        if 'stealth adept' in (x.get('name') or '').lower(): lines.append('STEALTH '+ancestry(cr,x))

# All top-level unit entries that already received Night Lords Stealth selectors.
lines.append('\n=== ALL R71/R72 STEALTH SELECTORS ===')
for x in cr.iter(C('selectionEntry')):
    if 'stealth adept' in (x.get('name') or '').lower():
        lines.append(ancestry(cr,x))

# Rite and FOC diagnostics.
for rid in ['r25-rite-viii-0-terror-assault','r25-rite-viii-1-horror-cult']:
    r=byid(cr,rid); lines.append(f"\n=== RITE {rid} ===")
    if r is None: lines.append('MISSING'); continue
    lines.append(f"name={r.get('name')} hidden={r.get('hidden')}")
    for rr in r.iter(C('rule')): lines.append(f"RULE {rr.get('name')}")
    for m in r.iter(C('modifier')): lines.append(f"MOD id={m.get('id')} type={m.get('type')} field={m.get('field')} value={m.get('value')}")
    for c in r.iter(C('condition')): lines.append(f"COND type={c.get('type')} value={c.get('value')} scope={c.get('scope')} childId={c.get('childId')}")

lines.append('\n=== RITE CLONES / CATEGORIES ===')
for x in cr.iter(C('selectionEntry')):
    i=x.get('id') or ''
    if i.startswith('r71-nl-ta-') or i.startswith('r71-nl-hc-'):
        cats=[(c.get('name'),c.get('targetId'),c.get('primary')) for c in x.findall('./'+C('categoryLinks')+'/'+C('categoryLink'))]
        lines.append(f"{i} name={x.get('name')} hidden={x.get('hidden')} cats={cats}")
        for c in x.iter(C('condition')): lines.append(f"  COND {c.get('type')} {c.get('value')} {c.get('scope')} {c.get('childId')}")

lines.append('\n=== GST CATEGORIES matching fort / troop / fast / heavy / compulsory ===')
for x in gr.iter(G('categoryEntry')):
    n=(x.get('name') or '').lower()
    if any(k in n for k in ('fort','troop','fast','heavy','terror assault','horror cult','compuls')):
        lines.append(f"CAT id={x.get('id')} name={x.get('name')} hidden={x.get('hidden')}")

for fid in ['force-standard','fl-hq','fl-troops','fl-fast','fl-heavy','fl-fortification','fl-fortifications']:
    x=byid(gr,fid); lines.append(f"\n=== GST {fid} ===")
    if x is None: lines.append('MISSING'); continue
    lines.append(f"tag={x.tag.split('}')[-1]} name={x.get('name')} targetId={x.get('targetId')}")
    for c in x.iter(G('constraint')): lines.append(f"  CONSTRAINT id={c.get('id')} type={c.get('type')} field={c.get('field')} value={c.get('value')} scope={c.get('scope')}")
    for m in x.iter(G('modifier')): lines.append(f"  MOD id={m.get('id')} type={m.get('type')} field={m.get('field')} value={m.get('value')}")
    for c in x.iter(G('condition')): lines.append(f"    COND type={c.get('type')} value={c.get('value')} scope={c.get('scope')} childId={c.get('childId')}")

OUT.write_text('\n'.join(lines),encoding='utf-8')
print(OUT.read_text())
