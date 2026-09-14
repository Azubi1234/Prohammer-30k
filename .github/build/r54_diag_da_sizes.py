import xml.etree.ElementTree as ET
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse('Legiones Astartes.cat').getroot()
parent={c:p for p in cr.iter() for c in p}
found=0
for s in cr.iter(C('selectionEntry')):
    if (s.get('name') or '').strip().lower()!='additional model': continue
    x=parent.get(s); unit=None
    while x is not None:
        if x.tag==C('selectionEntry') and x.get('type')=='unit': unit=x; break
        x=parent.get(x)
    if unit is None: continue
    uid=unit.get('id','')
    if not (uid.startswith('r40-da') or 'dark angel' in (unit.get('name') or '').lower()): continue
    found+=1
    print('\nUNIT',uid,unit.get('name'),'unit default',unit.get('defaultAmount'))
    costs=unit.find(C('costs'))
    if costs is not None: print(' unit costs',[(c.get('typeId'),c.get('value')) for c in costs.findall(C('cost'))])
    print(' ADD',s.get('id'),s.get('type'),'default',s.get('defaultAmount'))
    cs=s.find(C('constraints'))
    if cs is not None: print(' constraints',[(c.get('type'),c.get('value'),c.get('scope')) for c in cs.findall(C('constraint'))])
    costs=s.find(C('costs'))
    if costs is not None: print(' add costs',[(c.get('typeId'),c.get('value')) for c in costs.findall(C('cost'))])
    rules=unit.find(C('rules'))
    if rules is not None:
        for r in rules.findall(C('rule')):
            d=r.find(C('description')); txt=(d.text or '') if d is not None else ''
            if 'composition' in txt.lower() or 'additional' in txt.lower(): print(' rule',r.get('name'),txt[:1000].replace('\n',' | '))
print('\nFOUND',found,'Dark Angels Additional model entries')
