import xml.etree.ElementTree as ET
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse('Legiones Astartes.cat').getroot(); parent={c:p for p in cr.iter() for c in p}
IDS=['r30-prae-castellax-extra','r30-prae-vorax-extra','hs-hss-additional','hs-art-whirlwind-additional','hs-lr-phobos','da22-dwtc-extra','da22-cen-extra','hq-praetor-ret-honour-add']
def cons(e):
 cs=e.find(C('constraints')); return [] if cs is None else [(x.get('type'),x.get('value'),x.get('field'),x.get('scope')) for x in cs.findall(C('constraint'))]
def cost(e):
 cs=e.find(C('costs')); return [] if cs is None else [(x.get('typeId'),x.get('value')) for x in cs.findall(C('cost'))]
def show(e,indent=0):
 print(' '*indent,e.tag.split('}')[-1],e.get('id'),repr(e.get('name')),e.get('type'),'default',e.get('defaultAmount'),'con',cons(e),'cost',cost(e))
for iid in IDS:
 e=next((x for x in cr.iter() if x.get('id')==iid),None)
 print('\n###',iid)
 if e is None: print('MISSING'); continue
 p=parent.get(e); gp=parent.get(p) if p is not None else None
 if gp is not None: show(gp,0)
 if p is not None: show(p,2)
 if p is not None:
  for c in list(p):
   if c.tag in (C('selectionEntry'),C('selectionEntryGroup')): show(c,4)
# trigger
