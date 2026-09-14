import xml.etree.ElementTree as ET
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse('Legiones Astartes.cat').getroot(); parent={c:p for p in cr.iter() for c in p}
IDS=['veteran-unit','terminator-unit','destroyer-unit','fa-seeker','fa-bike','fa-sky-hunter','hs-heavy-support-squad','hq-praetor','hs-land-raider','hs-artillery','r35-pride-veteran-veteran-unit','r35-pride-terminator-terminator-unit','r35-destroyer-troops-destroyer-unit','r35-sky-troops-fa-sky-hunter','r40-da-eskaton-interemptor','r42-role-v-0-effects-ride-like-the-wind-legion-sky-hunter-jetbike-squadrons-fa-sky-hunter','r42-role-xiv-0-effects-superior-firepower-legion-veteran-squads-veteran-unit','r42-role-xiv-0-legion-heavy-support-squads-hs-heavy-support-squad','r43-ws-bike-troops','r45-dg-bike','r52-ec-sonic-hss','da22-deathwing-term-comp','da22-cenobium']
def cons(e):
 cs=e.find(C('constraints')); return [] if cs is None else [(x.get('type'),x.get('value'),x.get('field'),x.get('scope')) for x in cs.findall(C('constraint'))]
def costs(e):
 cs=e.find(C('costs')); return [] if cs is None else [(x.get('typeId'),x.get('value')) for x in cs.findall(C('cost'))]
for uid in IDS:
 u=next((e for e in cr.iter(C('selectionEntry')) if e.get('id')==uid),None)
 print('\n###',uid, u.get('name') if u is not None else 'MISSING')
 if u is None: continue
 print('UNIT default',u.get('defaultAmount'),'cost',costs(u),'con',cons(u))
 for e in u.iter(C('selectionEntry')):
  if e is u: continue
  nm=e.get('name','')
  if e.get('type')=='model' or 'additional' in nm.lower() or 'extra' in nm.lower() or 'squad model' in nm.lower() or 'legion veteran' in nm.lower() or 'legion terminator' in nm.lower() or 'legion biker' in nm.lower() or 'sky hunter' in nm.lower() or 'interemptor' in nm.lower() or 'companion' in nm.lower() or 'cenobite' in nm.lower():
   print(' SE',e.get('id'),repr(nm),e.get('type'),'default',e.get('defaultAmount'),'cost',costs(e),'con',cons(e))
 for g in u.iter(C('selectionEntryGroup')):
  nm=g.get('name','')
  if 'squad' in nm.lower() or 'size' in nm.lower(): print(' GR',g.get('id'),repr(nm),'con',cons(g))
# trigger
