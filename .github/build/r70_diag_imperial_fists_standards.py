from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat')
OUT=Path('inspection-r70-if-standards-diagnostic.txt')
NS='http://www.battlescribe.net/schema/catalogueSchema'
C=lambda t:f'{{{NS}}}{t}'
root=ET.parse(CAT).getroot()
lines=[]
add=lines.append

def by_id(i):
    return next((e for e in root.iter() if e.get('id')==i),None)

def parent_map():
    return {c:p for p in root.iter() for c in p}
PM=parent_map()

def nearest_entry(e):
    cur=e
    while cur is not None:
        if cur.tag in (C('selectionEntry'),C('selectionEntryGroup'),C('entryLink')) and cur.get('name'):
            return cur
        cur=PM.get(cur)
    return None

def dump(node,depth=0,maxdepth=4):
    if node is None:
        add('  <missing>'); return
    ind='  '*depth
    attrs=[]
    for k in ('id','name','type','targetId','hidden','defaultAmount'):
        if node.get(k) is not None: attrs.append(f'{k}={node.get(k)}')
    if node.tag in (C('constraint'),C('modifier'),C('condition')):
        for k in ('type','value','field','scope','childId'):
            if node.get(k) is not None and f'{k}={node.get(k)}' not in attrs: attrs.append(f'{k}={node.get(k)}')
    add(ind+node.tag.split('}')[-1]+' '+ ' | '.join(attrs))
    if depth>=maxdepth:return
    for ch in list(node):
        if ch.tag in (C('selectionEntries'),C('selectionEntryGroups'),C('entryLinks'),C('constraints'),C('modifiers'),C('conditions'),C('conditionGroups'),C('costs'),C('categoryLinks')):
            add(ind+'  '+ch.tag.split('}')[-1]+':')
            for x in list(ch): dump(x,depth+2,maxdepth)

add(f'Catalogue revision={root.get("revision")} GST revision={root.get("gameSystemRevision")}')
add('')
for ident in ['hq-praetor','hq-centurion','tactical-unit','assault-unit','breacher-unit','recon-unit','veteran-unit','terminator-unit','fa-seeker','hs-heavy-support-squad','hs-land-raider','hq-centurion-ret-command','hq-praetor-ret-termcommand','hq-praetor-ret-honour']:
    add('='*90); add(f'ID {ident}')
    dump(by_id(ident),0,5)

add('\n'+'='*90+'\nARMOURY GROUP INDEX')
for g in root.iter(C('selectionEntryGroup')):
    n=(g.get('name') or '')
    if 'armour' in n.lower() or 'weapon' in n.lower():
        owner=PM.get(g)
        while owner is not None and owner.tag!=C('selectionEntry'):
            owner=PM.get(owner)
        if owner is not None:
            add(f'OWNER {owner.get("id")} :: {owner.get("name")} | GROUP {g.get("id")} :: {n}')
            # immediate selectable children/links only
            se=g.find(C('selectionEntries'))
            if se is not None:
                for x in list(se): add(f'  ENTRY {x.get("id")} :: {x.get("name")} cost='+','.join(c.get('value','') for c in x.findall('./'+C('costs')+'/'+C('cost'))))
            el=g.find(C('entryLinks'))
            if el is not None:
                for x in list(el): add(f'  LINK {x.get("id")} :: {x.get("name")} -> {x.get("targetId")}')

add('\n'+'='*90+'\nLAND RAIDER PATTERN GROUPS')
for g in root.iter(C('selectionEntryGroup')):
    if 'land raider pattern' in (g.get('name') or '').lower():
        owner=PM.get(g)
        while owner is not None and owner.tag!=C('selectionEntry'):
            owner=PM.get(owner)
        add(f'OWNER {owner.get("id") if owner is not None else None} :: {owner.get("name") if owner is not None else None}')
        dump(g,0,5)

add('\n'+'='*90+'\nTOP-LEVEL UNIT INDEX')
top=root.find(C('selectionEntries'))
if top is not None:
    for u in top.findall(C('selectionEntry')):
        cats=[]
        cl=u.find(C('categoryLinks'))
        if cl is not None:
            for c in cl.findall(C('categoryLink')):
                if c.get('primary')=='true': cats.append(c.get('name') or c.get('targetId'))
        if cats:
            add(f'{u.get("id")} | {u.get("name")} | {",".join(cats)}')

add('\n'+'='*90+'\nGENERIC UNIT CANDIDATES FOR HAMMERFALL')
keywords=('command','honour','destroyer','apothe','techmarine','terminator','tactical','assault','breacher','recon','veteran','seeker','heavy support','rapier')
if top is not None:
    for u in top.findall(C('selectionEntry')):
        n=(u.get('name') or '').lower()
        if any(k in n for k in keywords):
            add(f'{u.get("id")} | {u.get("name")}')

OUT.write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(lines[-120:]))
