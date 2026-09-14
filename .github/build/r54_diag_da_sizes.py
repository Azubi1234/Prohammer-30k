import xml.etree.ElementTree as ET
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse('Legiones Astartes.cat').getroot(); top=cr.find(C('selectionEntries'))
for u in list(top):
    uid=u.get('id','')
    if not (uid.startswith('r40-da') or uid.startswith('da22-')): continue
    models=[]
    for s in u.iter(C('selectionEntry')):
        if s is u or s.get('type')!='model': continue
        cs=s.find(C('constraints')); con=[]
        if cs is not None: con=[(c.get('type'),c.get('value'),c.get('scope')) for c in cs.findall(C('constraint')) if c.get('field')=='selections']
        costs=s.find(C('costs')); pts=[]
        if costs is not None: pts=[c.get('value') for c in costs.findall(C('cost')) if c.get('typeId')=='pts']
        models.append((s.get('id'),s.get('name'),s.get('defaultAmount'),con,pts))
    if models:
        print('\nUNIT',uid,u.get('name'))
        for m in models: print(' ',m)
