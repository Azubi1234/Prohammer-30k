import xml.etree.ElementTree as ET
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse('Legiones Astartes.cat').getroot()

def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
for uid in ['da22-deathwing-companions','da22-interemptors']:
    u=by_id(uid)
    print('\nUNIT',uid, u.get('name') if u is not None else 'MISSING')
    if u is None: continue
    for s in u.iter(C('selectionEntry')):
        if s is u: continue
        cs=s.find(C('constraints')); con=[]
        if cs is not None: con=[(c.get('type'),c.get('value'),c.get('scope'),c.get('field')) for c in cs.findall(C('constraint'))]
        costs=s.find(C('costs')); pts=[]
        if costs is not None: pts=[(c.get('typeId'),c.get('value')) for c in costs.findall(C('cost'))]
        print(' SE',s.get('id'),repr(s.get('name')),s.get('type'),'default',s.get('defaultAmount'),'con',con,'costs',pts)
    for g in u.iter(C('selectionEntryGroup')):
        cs=g.find(C('constraints')); con=[]
        if cs is not None: con=[(c.get('type'),c.get('value'),c.get('scope'),c.get('field')) for c in cs.findall(C('constraint'))]
        print(' GROUP',g.get('id'),repr(g.get('name')),'con',con)
