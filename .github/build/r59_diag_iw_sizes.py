from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse(CAT).getroot(); top=cr.find(C('selectionEntries'))
parent={c:p for p in cr.iter() for c in p}

def cons(e):
    cs=e.find(C('constraints')); out=[]
    if cs is not None:
        for c in cs.findall(C('constraint')):
            if c.get('field')=='selections': out.append((c.get('type'),c.get('value'),c.get('scope')))
    return out

def costs(e):
    cs=e.find(C('costs')); out=[]
    if cs is not None:
        for c in cs.findall(C('cost')):
            if c.get('typeId')=='pts': out.append(c.get('value'))
    return out

def chain(e):
    a=[]; x=parent.get(e)
    while x is not None:
        if x.tag in (C('selectionEntry'),C('selectionEntryGroup')):
            a.append((x.tag.split('}')[-1],x.get('id'),x.get('name'),x.get('type'),x.get('defaultAmount'),cons(x),costs(x)))
        x=parent.get(x)
    return a

names=('TYRANT SIEGE TERMINATOR SQUAD','IRON HAVOC SQUAD','DOMINATOR COHORT','IRON CIRCLE DOMITAR-FERRUM MANIPLE')
lines=[]
for u in list(top):
    if (u.get('name') or '').upper() not in names: continue
    lines.append(f"UNIT {u.get('id')} :: {u.get('name')} :: pts={costs(u)}")
    for e in u.iter(C('selectionEntry')):
        if e is u: continue
        if e.get('type')=='model' or 'Additional ' in (e.get('name') or '') or 'Dominator Cohort Models' in (e.get('name') or '') or 'Tyrant Siege Terminators' in (e.get('name') or '') or 'Iron Havocs' in (e.get('name') or '') or 'Domitar-Ferrum Battle-Automata' in (e.get('name') or ''):
            lines.append(f"  ENTRY id={e.get('id')} name={e.get('name')} type={e.get('type')} default={e.get('defaultAmount')} cons={cons(e)} pts={costs(e)}")
            for x in chain(e)[:3]: lines.append(f"    PARENT {x}")
    for g in u.iter(C('selectionEntryGroup')):
        if 'Squad' in (g.get('name') or '') or 'Size' in (g.get('name') or ''):
            lines.append(f"  GROUP id={g.get('id')} name={g.get('name')} cons={cons(g)}")
    lines.append('')

# Compare known working core HSS and EC/IW entries.
for key in ('hs-heavy-support-squad','r41-unit-iii-0-palatine-blade-squad'):
    u=next((x for x in cr.iter(C('selectionEntry')) if x.get('id')==key),None)
    if u is None: continue
    lines.append(f"REFERENCE UNIT {u.get('id')} :: {u.get('name')} :: pts={costs(u)}")
    for e in u.iter(C('selectionEntry')):
        if e is u:continue
        if e.get('type')=='model':lines.append(f"  MODEL id={e.get('id')} name={e.get('name')} default={e.get('defaultAmount')} cons={cons(e)} pts={costs(e)}")
    lines.append('')

Path('inspection-r59-iw-size-diagnostic.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
