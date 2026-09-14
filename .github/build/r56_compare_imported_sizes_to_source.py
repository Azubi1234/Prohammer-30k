import xml.etree.ElementTree as ET,re
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
cr=ET.parse('Legiones Astartes.cat').getroot(); top=cr.find(C('selectionEntries'))

def con(e,t):
 cs=e.find(C('constraints'))
 if cs is None:return None
 x=next((x for x in cs.findall(C('constraint')) if x.get('type')==t and x.get('field')=='selections'),None)
 return x.get('value') if x is not None else None

def source(u):
 for r in u.iter(C('rule')):
  if (r.get('name') or '').strip().lower()=='source entry':
   d=r.find(C('description')); return (d.text or '') if d is not None else ''
 return ''
for u in list(top):
 if u.get('type')!='unit' or not u.get('id','').startswith('r41-unit-'):continue
 counters=[]
 for e in u.iter(C('selectionEntry')):
  if e.get('type')=='model' and con(e,'max') and float(con(e,'max'))>1 and e.get('defaultAmount'):
   counters.append((e.get('name'),e.get('defaultAmount'),con(e,'min'),con(e,'max')))
 if not counters:continue
 txt=source(u)
 print('\n###',u.get('id'),u.get('name'),'COUNTERS',counters,'SOURCE_LEN',len(txt))
 if txt:
  for pat in [r'Unit Composition\s*:?.{0,300}',r'Squad\s*:?.{0,250}',r'squad consists.{0,220}',r'consists of.{0,220}',r'up to \w+ additional.{0,120}',r'up to \d+ additional.{0,120}']:
   m=re.search(pat,txt,re.I|re.S)
   if m: print('HINT', ' '.join(m.group(0).split())[:500])
