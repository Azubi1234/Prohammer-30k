from pathlib import Path
import xml.etree.ElementTree as ET
import re

CAT=Path('Legiones Astartes.cat')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse(CAT).getroot(); top=cr.find(C('selectionEntries'))

report=[]; flags=[]

def constraints(e):
    cs=e.find(C('constraints')); out=[]
    if cs is not None:
        for c in cs.findall(C('constraint')):
            if c.get('field')=='selections': out.append((c.get('type'),c.get('value'),c.get('scope')))
    return out

def pts(e):
    cs=e.find(C('costs')); out=[]
    if cs is not None:
        out=[c.get('value') for c in cs.findall(C('cost')) if c.get('typeId')=='pts']
    return out

def source_entry_text(u):
    for r in u.iter(C('rule')):
        if (r.get('name') or '').strip().lower()=='source entry':
            d=r.find(C('description'))
            return (d.text or '') if d is not None else ''
    return ''

def source_size_hint(txt):
    if not txt: return ''
    pats=[
        r'Squad\s*:\s*[^\n]{0,220}', r'Squad\s+consists[^\n]{0,220}', r'Unit Composition\s*:[^\n]{0,220}',
        r'between\s+\w+\s+and\s+\w+[^\n]{0,100}', r'between\s+\d+\s+and\s+\d+[^\n]{0,100}',
        r'consists of\s+\d+[^\n]{0,160}'
    ]
    hits=[]
    for p in pats:
        m=re.search(p,txt,re.I)
        if m: hits.append(' '.join(m.group(0).split()))
    return ' | '.join(dict.fromkeys(hits))

units=list(top) if top is not None else []
for u in units:
    if u.get('type')!='unit': continue
    uid=u.get('id',''); name=u.get('name','')
    models=[]; suspicious=[]; groups=[]
    for e in u.iter(C('selectionEntry')):
        if e is u: continue
        nm=(e.get('name') or '')
        if e.get('type')=='model':
            models.append((e.get('id'),nm,e.get('defaultAmount'),constraints(e),pts(e)))
        if re.search(r'\b(additional|extra)\b',nm,re.I):
            suspicious.append((e.get('id'),nm,e.get('type'),e.get('defaultAmount'),constraints(e),pts(e)))
    for g in u.iter(C('selectionEntryGroup')):
        nm=g.get('name') or ''
        if re.search(r'squad size|additional|extra',nm,re.I): groups.append((g.get('id'),nm,constraints(g)))

    hint=source_size_hint(source_entry_text(u))
    if models or suspicious or groups:
        report.append(f'UNIT {uid} :: {name}')
        if models:
            for x in models: report.append(f'  MODEL {x}')
        if suspicious:
            for x in suspicious: report.append(f'  SUSPECT {x}')
        if groups:
            for x in groups: report.append(f'  GROUP {x}')
        if hint: report.append(f'  SOURCE_HINT {hint}')
        report.append('')

    # Hard UI-standard flags: any additional/extra model quantity entry, or a squad-size group whose selectable counter begins at 0/None.
    for sid,nm,typ,default,con,cost in suspicious:
        maxv=next((v for t,v,s in con if t=='max'),None)
        if maxv and float(maxv)>0:
            flags.append((uid,name,sid,nm,typ,default,con,cost,'additional/extra quantity entry remains'))
    for mid,mn,default,con,cost in models:
        minv=next((v for t,v,s in con if t=='min'),None)
        maxv=next((v for t,v,s in con if t=='max'),None)
        if maxv and float(maxv)>1 and (default in (None,'0') and (minv in (None,'0'))):
            flags.append((uid,name,mid,mn,'model',default,con,cost,'expandable model counter starts at zero'))

report.insert(0,f'Top-level unit entries audited: {sum(1 for u in units if u.get("type")=="unit")}')
report.insert(1,f'UI-standard flags: {len(flags)}')
report.insert(2,'')
report.append('=== FLAGS ===')
for f in flags: report.append(repr(f))
Path('inspection-r56-all-unit-sizes.txt').write_text('\n'.join(report)+'\n',encoding='utf-8')
print(f'AUDITED {sum(1 for u in units if u.get("type")=="unit")} top-level units')
print(f'FLAGS {len(flags)}')
for f in flags: print(f)
