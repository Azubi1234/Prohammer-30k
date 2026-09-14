import xml.etree.ElementTree as ET,re
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse('Legiones Astartes.cat').getroot(); top=cr.find(C('selectionEntries'))
parent={c:p for p in cr.iter() for c in p}

def cons(e):
 cs=e.find(C('constraints')); return [] if cs is None else [(x.get('type'),x.get('value'),x.get('field'),x.get('scope')) for x in cs.findall(C('constraint'))]
def costs(e):
 cs=e.find(C('costs')); return [] if cs is None else [(x.get('typeId'),x.get('value')) for x in cs.findall(C('cost'))]
def top_unit(e):
 x=e; last=None
 while x is not None:
  if x.tag==C('selectionEntry') and x.get('type')=='unit': last=x
  x=parent.get(x)
 return last
for e in cr.iter(C('selectionEntry')):
 nm=e.get('name','')
 if not re.search(r'\b(additional|extra)\b',nm,re.I): continue
 u=top_unit(e)
 print('ENTRY',e.get('id'),repr(nm),'type',e.get('type'),'default',e.get('defaultAmount'),'con',cons(e),'cost',costs(e),'UNIT',u.get('id') if u is not None else None,repr(u.get('name')) if u is not None else None,'PARENT',parent.get(e).tag.split('}')[-1] if parent.get(e) is not None else None,parent.get(e).get('id') if parent.get(e) is not None else None,parent.get(e).get('name') if parent.get(e) is not None else None)
# rerun
