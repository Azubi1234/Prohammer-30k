from pathlib import Path
import xml.etree.ElementTree as ET
import re

CAT=Path('Legiones Astartes.cat')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse(CAT).getroot(); top=cr.find(C('selectionEntries'))
parent={c:p for p in cr.iter() for c in p}
report=[]; flags=[]

def constraints(e):
    cs=e.find(C('constraints')); out=[]
    if cs is not None:
        for c in cs.findall(C('constraint')):
            if c.get('field')=='selections': out.append((c.get('type'),c.get('value'),c.get('scope')))
    return out

def pts(e):
    cs=e.find(C('costs')); out=[]
    if cs is not None: out=[c.get('value') for c in cs.findall(C('cost')) if c.get('typeId')=='pts']
    return out

def conval(e,typ):
    return next((v for t,v,s in constraints(e) if t==typ),None)

def ancestor_group(e):
    x=parent.get(e)
    while x is not None:
        if x.tag==C('selectionEntryGroup'): return x
        if x.tag==C('selectionEntry') and x.get('type')=='unit': return None
        x=parent.get(x)
    return None

units=list(top) if top is not None else []
for u in units:
    if u.get('type')!='unit': continue
    uid=u.get('id',''); name=u.get('name','')
    models=[]; add_entries=[]
    for e in u.iter(C('selectionEntry')):
        if e is u: continue
        nm=(e.get('name') or '')
        if e.get('type')=='model': models.append((e.get('id'),nm,e.get('defaultAmount'),constraints(e),pts(e)))
        if nm.startswith('Additional ') and not nm.startswith(('Additional Armoury','Additional Wargear','Additional Weapon')):
            add_entries.append((e.get('id'),nm,e.get('type'),e.get('defaultAmount'),constraints(e),pts(e)))
    if models or add_entries:
        report.append(f'UNIT {uid} :: {name}')
        for x in models: report.append(f'  MODEL {x}')
        for x in add_entries: report.append(f'  ADDITIONAL {x}')
        report.append('')

    for x in add_entries:
        maxv=next((v for t,v,s in x[4] if t=='max'),None)
        if maxv and float(maxv)>1: flags.append((uid,name,*x,'legacy Additional quantity remains'))

    # An expandable model counter used as the unit's quantity must have a real start count.
    # Optional alternate models inside a constrained choice group are allowed to default to zero.
    for mid,mn,default,con,cost in models:
        maxv=next((v for t,v,s in con if t=='max'),None); minv=next((v for t,v,s in con if t=='min'),None)
        if not maxv or float(maxv)<=1: continue
        if default not in (None,'0') or (minv not in (None,'0')): continue
        e=next(z for z in u.iter(C('selectionEntry')) if z.get('id')==mid)
        g=ancestor_group(e)
        group_has_min=g is not None and conval(g,'min') not in (None,'0')
        sibling_default=False
        if g is not None:
            sibling_default=any((s.get('defaultAmount') not in (None,'0')) for s in g.iter(C('selectionEntry')) if s is not e)
        if not (group_has_min and sibling_default):
            flags.append((uid,name,mid,mn,'expandable model counter starts at zero without an alternate default'))

report.insert(0,f'Top-level unit entries audited: {sum(1 for u in units if u.get("type")=="unit")}')
report.insert(1,f'UI-standard flags: {len(flags)}')
report.insert(2,'')
report.append('=== FLAGS ===')
for f in flags: report.append(repr(f))
Path('inspection-r56-all-unit-sizes.txt').write_text('\n'.join(report)+'\n',encoding='utf-8')
print(f'AUDITED {sum(1 for u in units if u.get("type")=="unit")} top-level units')
print(f'FLAGS {len(flags)}')
for f in flags: print(f)
if flags: raise SystemExit(1)
