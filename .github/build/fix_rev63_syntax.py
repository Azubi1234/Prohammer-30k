from pathlib import Path

p=Path('.github/build/rev63_space_wolves_full.py')
s=p.read_text(encoding='utf-8')
old="""def transport_names(unit):
    out=[]
    for g in unit.iter(C('selectionEntryGroup')):
        if g.get('name')=='Dedicated Transport':
            for l in g.iter(C('entryLink')): out.append(l.get('name'))
            for e in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')): out.append(e.get('name'))
    return out
"""
new="""def transport_names(unit):
    out=[]
    for g in unit.iter(C('selectionEntryGroup')):
        if g.get('name')=='Dedicated Transport':
            links=g.find(C('entryLinks'))
            if links is not None:
                for l in links.findall(C('entryLink')): out.append(l.get('name'))
            entries=g.find(C('selectionEntries'))
            if entries is not None:
                for e in entries.findall(C('selectionEntry')): out.append(e.get('name'))
    return out
"""
if old not in s:
    raise SystemExit('Expected transport_names block not found')
p.write_text(s.replace(old,new),encoding='utf-8')
print('Fixed Dedicated Transport audit to inspect only direct transport choices.')
