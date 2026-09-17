from pathlib import Path
import re
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); IDX=Path('index.xml'); OUT=Path('inspection-r88-world-eaters-source-dump-cleanup.txt')
NS='http://www.battlescribe.net/schema/catalogueSchema'; ET.register_namespace('',NS); C=lambda t:f'{{{NS}}}{t}'
ct=ET.parse(CAT); root=ct.getroot()
if root.get('revision')!='87' or root.get('gameSystemRevision')!='51':
    raise RuntimeError(f'Expected CAT87/GSTref51, got CAT{root.get("revision")}/GSTref{root.get("gameSystemRevision")}')

def byid(i): return next((e for e in root.iter() if e.get('id')==i),None)
def parent_map(): return {c:p for p in root.iter() for c in p}
def norm(s): return re.sub(r'\s+',' ',(s or '').strip()).lower()
def elem_text(e):
    parts=[]
    for d in e.iter():
        if d.text and d.text.strip(): parts.append(d.text.strip())
    return ' '.join(parts)
def source_blob_text(s):
    low=norm(s)
    markers=sum(k in low for k in ('force organisation:','unit type:','wargear:','special rules:'))
    return markers>=3

def target_units():
    names={
      'Rampager Squad','Red Butcher Squad','Red Hand Destroyer Mortalis Squad','World Eaters Inductii Squad',
      'Devourer Terminator Squad','Triarii Breacher Squad','Khârn the Bloody','Kharn the Bloody','Shabran Darr',
      'Gahlan Surlak','Kargos, the Bloodspitter','Kargos the Bloodspitter','Captain Ehrlen','Delvarus',
      'XII — Angron, the Red Angel','Angron, the Red Angel','Angron the Red Angel'
    }
    out=[]
    for e in root.iter(C('selectionEntry')):
        if e.get('type')!='unit': continue
        eid=e.get('id') or ''; nm=(e.get('name') or '').strip()
        if eid.startswith('r41-unit-xii-') or nm in names:
            out.append(e)
        elif ('r42-role-xii' in eid or 'r46-al-reward' in eid) and any(k in norm(nm) for k in ('rampager','red butcher','red hand destroyer','inductii','devourer','triarii')):
            out.append(e)
    # de-duplicate by object identity
    seen=set(); uniq=[]
    for e in out:
        if id(e) not in seen: seen.add(id(e)); uniq.append(e)
    return uniq

# Full catalogue ID map is needed because old imports sometimes expose a shared
# Source Entry through infoLinks rather than a local <rule> node.
idmap={e.get('id'):e for e in root.iter() if e.get('id')}
removed=[]

def is_source_node(x):
    tag=x.tag.split('}')[-1]
    nm=norm(x.get('name'))
    txt=elem_text(x)
    if nm.startswith('source entry'): return True
    if source_blob_text(txt): return True
    if tag=='profile':
        tname=norm(x.get('typeName'))
        if tname in ('rules','rule','source entry') and source_blob_text(txt): return True
    if tag=='infoLink':
        target=idmap.get(x.get('targetId'))
        if target is not None:
            tnm=norm(target.get('name')); ttxt=elem_text(target)
            if tnm.startswith('source entry') or source_blob_text(ttxt): return True
    return False

def scrub_unit(u):
    count=0
    # Repeat because removing a wrapper can expose no new nodes but keeps logic simple.
    changed=True
    while changed:
        changed=False
        pm={c:p for p in u.iter() for c in p}
        for x in list(u.iter()):
            if x is u: continue
            tag=x.tag.split('}')[-1]
            if tag not in ('rule','profile','infoLink','selectionEntry','entryLink'): continue
            if not is_source_node(x): continue
            p=pm.get(x)
            if p is not None:
                removed.append(f'{u.get("id")} | {u.get("name")} :: removed {tag} {x.get("id")} | {x.get("name")}')
                p.remove(x); count+=1; changed=True; break
    return count

units=target_units()
for u in units: scrub_unit(u)

# Remove empty containers left by the legacy source dump, but keep all actual
# Wargear / Special Rules / Options structures intact.
for u in units:
    for p in list(u.iter()):
        for tag in ('rules','profiles','infoLinks','entryLinks','selectionEntries','selectionEntryGroups'):
            box=p.find(C(tag))
            if box is not None and len(box)==0:
                p.remove(box)

# Conservative sibling de-duplication: only remove entries that are literally the
# same visible choice (same normalized name, same type, same points) under the same
# parent. This catches importer leftovers without collapsing genuinely distinct choices.
deduped=[]
def pts(e):
    c=next((c for c in e.findall('./'+C('costs')+'/'+C('cost')) if c.get('typeId')=='pts'),None)
    return c.get('value') if c is not None else '0'
for u in units:
    for p in list(u.iter()):
        for box_tag,item_tag in [('selectionEntries','selectionEntry'),('entryLinks','entryLink')]:
            box=p.find(C(box_tag))
            if box is None: continue
            seen={}
            for x in list(box.findall(C(item_tag))):
                if x.get('hidden')=='true': continue
                key=(norm(x.get('name')),x.get('type') or '',pts(x) if item_tag=='selectionEntry' else x.get('targetId') or '')
                if not key[0]: continue
                if key in seen:
                    # Never collapse model counters here; model normalization is handled by the permanent audit.
                    if item_tag=='selectionEntry' and x.get('type')=='model': continue
                    box.remove(x); deduped.append(f'{u.get("name")} :: {item_tag} {x.get("name")}');
                else: seen[key]=x

# Hard validation: no World Eaters target may still render an old aggregate Source Entry.
fail=[]
for u in units:
    for x in u.iter():
        tag=x.tag.split('}')[-1]
        if tag in ('rule','profile','infoLink','selectionEntry','entryLink') and is_source_node(x):
            fail.append(f'{u.get("name")} :: {tag} {x.get("name")} {x.get("id")}')
if fail:
    raise RuntimeError('Source-entry material survived cleanup:\n'+'\n'.join(fail))

# Delvarus is the regression case reported from the live UI.
delv=[u for u in units if norm(u.get('name'))=='delvarus']
if not delv: raise RuntimeError('No Delvarus unit found for regression check')
for u in delv:
    assert not any(is_source_node(x) for x in u.iter() if x is not u), 'Delvarus still has Source Entry aggregate'
    groups={norm(g.get('name')) for g in u.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup'))}
    assert 'wargear' in groups and 'special rules' in groups, f'Delvarus structured groups missing: {groups}'

root.set('revision','88'); ct.write(CAT,encoding='utf-8',xml_declaration=True)
raw=CAT.read_text(encoding='utf-8').replace(f'xmlns:ns0="{NS}"',f'xmlns="{NS}"').replace('<ns0:','<').replace('</ns0:','</')
if '<ns0:' in raw: raise RuntimeError('Namespace prefix survived')
CAT.write_text(raw,encoding='utf-8')
idx=IDX.read_text(encoding='utf-8')
idx,n=re.subn(r'(filePath="Legiones Astartes\.cat"[^>]*dataRevision=")87(" )',r'\g<1>88\g<2>',idx,count=1)
if n!=1: raise RuntimeError('Failed to bump index 87 -> 88')
IDX.write_text(idx,encoding='utf-8')

OUT.write_text(
    'Revision 88 — World Eaters hard Source Entry cleanup\n'
    'CAT=88 GSTref=51\n\n'
    f'Target units checked: {len(units)}\n'
    f'Legacy aggregate nodes removed: {len(removed)}\n'
    f'Exact duplicate visible choices removed: {len(deduped)}\n\n'
    'REMOVED SOURCE NODES\n' + ('\n'.join(removed) if removed else '(none found)') + '\n\n'
    'DEDUPLICATED CHOICES\n' + ('\n'.join(deduped) if deduped else '(none)') + '\n\n'
    'Regression check: every Delvarus entry now has structured Wargear and Special Rules groups and no aggregate Source Entry rule/profile/infoLink.\n',
    encoding='utf-8'
)
print(OUT.read_text(encoding='utf-8'))
