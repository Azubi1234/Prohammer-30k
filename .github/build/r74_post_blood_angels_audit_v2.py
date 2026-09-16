from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); OUT=Path('inspection-r74-blood-angels-post.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema';GNS='http://www.battlescribe.net/schema/gameSystemSchema';C=lambda t:f'{{{CNS}}}{t}';G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot();gr=ET.parse(GST).getroot();PM={c:p for p in cr.iter() for c in p};assert cr.get('revision')=='74' and gr.get('revision')=='42'
L=[];a=L.append
IDS={'dawn':'r41-unit-ix-0-dawnbreaker-cohort','pal':'r41-unit-ix-1-crimson-paladin-squad','tears':'r41-unit-ix-2-angel-s-tears-squad','ofanim':'r41-unit-ix-3-ofanim-court','grav':'r41-unit-ix-4-grav-chariot-squadron','guard':'r41-unit-ix-5-sanguinary-guard','ral':'r41-unit-ix-6-raldoron-the-blooded','zephon':'r41-unit-ix-7-dominion-zephon','crohne':'r41-unit-ix-8-aster-crohne','azk':'r41-unit-ix-9-azkaellon','amit':'r41-unit-ix-10-nassir-amit-the-flesh-tearer','sang':'r41-unit-ix-11-ix-sanguinius-the-great-angel'}
def byid(root,i):return next((e for e in root.iter() if e.get('id')==i),None)
def cost(e):
 cs=e.find(C('costs')) if e is not None else None;return [x.get('value') for x in cs.findall(C('cost'))] if cs is not None else []
def cons(e,T=C):
 cs=e.find(T('constraints')) if e is not None else None;return [(x.get('id'),x.get('type'),x.get('value'),x.get('field'),x.get('scope')) for x in cs.findall(T('constraint'))] if cs is not None else []
def rules(e):return [x.get('name') for x in e.findall('./'+C('rules')+'/'+C('rule'))] if e is not None else []
def mods(e,T=C):
 out=[];ms=e.find(T('modifiers')) if e is not None else None
 if ms is not None:
  for m in ms.findall(T('modifier')):out.append((m.get('id'),m.get('type'),m.get('field'),m.get('value'),[(c.get('type'),c.get('value'),c.get('scope'),c.get('childId')) for c in m.findall('.//'+T('condition'))],[(r.get('value'),r.get('scope'),r.get('childId')) for r in m.findall('.//'+T('repeat'))]))
 return out
def cats(e):
 cs=e.find(C('categoryLinks')) if e is not None else None;return [(x.get('name'),x.get('targetId'),x.get('primary')) for x in cs.findall(C('categoryLink'))] if cs is not None else []
def models(e):return [x for x in e.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if x.get('type')=='model'] if e is not None else []
def find_under(u,needle,tag='selectionEntry'):
 low=needle.lower();T=C(tag);return next((e for e in u.iter(T) if low in (e.get('name') or '').lower()),None)
def owner(e):
 p=e
 while p is not None:
  if p.tag==C('selectionEntry') and p.get('type')=='unit':return p
  p=PM.get(p)
 return None
A={k:byid(cr,v) for k,v in IDS.items()};assert all(v is not None for v in A.values())
a('=== CANONICAL PRESENTATION ===')
for k,u in A.items():
 bad=[r.get('name') for r in u.findall('./'+C('rules')+'/'+C('rule')) if (r.get('name') or '').lower().startswith('source entry') or (r.get('name') or '').lower()=='special rules'];tp=u.findall('./'+C('profiles')+'/'+C('profile'))
 a(f'{k}: hidden={u.get("hidden")} top_profiles={len(tp)} bad_rules={bad} model_children={[m.get("name") for m in models(u)]} rules={rules(u)}');assert not bad and not tp
expected={'dawn':(5,10,35),'pal':(3,5,45),'tears':(5,10,30),'ofanim':(3,5,50),'guard':(3,6,55)}
for k,(mn,mx,pts) in expected.items():
 m=models(A[k])[0];d={x[1]:float(x[2]) for x in cons(m) if x[1] in ('min','max')};assert d.get('min')==mn and d.get('max')==mx and float(cost(m)[0])==pts
m=byid(cr,'r74-ba-grav-models');d={x[1]:float(x[2]) for x in cons(m)};assert d.get('min')==1 and d.get('max')==3 and float(cost(m)[0])==65
assert A['guard'].get('hidden')=='true' and A['azk'].get('hidden')=='true'

a('\n=== PER-MODEL / QUANTITY OPTIONS ===')
for k,names in {'dawn':['Krak grenades','Melta bombs'],'tears':['Krak grenades','Melta bombs'],'ofanim':['Krak grenades','Melta bombs','Jump Packs'],'guard':['Krak grenades','Melta bombs']}.items():
 for name in names:
  e=find_under(A[k],name);a(f'{k} {name}: id={e.get("id") if e is not None else None} cost={cost(e)} mods={mods(e)}');assert e is not None
  if name!='Jump Packs':assert (not cost(e) or float(cost(e)[0])==0) and any(x[1]=='increment' and x[5] for x in mods(e))
for gid in ('r74-ba-tears-special','r74-ba-pal-heavy','r74-ba-pal-melee'):
 g=byid(cr,gid);a(f'{gid}: cons={cons(g)} mods={mods(g)} choices={[x.get("name") for x in g.findall("./"+C("selectionEntries")+"/"+C("selectionEntry"))] if g is not None else []}');assert g is not None

a('\n=== ARMOURY / CONSUL ===')
rh=byid(cr,'transport-rhino');cont=byid(cr,'contemptor-unit');pr=byid(cr,'r25-consul-ix-sanguinary-high-priest-consul');assert rh is not None and cont is not None and pr is not None
rhits=[(x.get('id'),x.get('name'),x.get('targetId'),mods(x)) for x in rh.iter(C('entryLink')) if 'over-charged' in (x.get('name') or '').lower()];a(f'Rhino Over-charged={rhits}');assert any(x[2]=='r44-ba-overcharged-engines' for x in rhits)
dam=[u for u in cr.iter(C('selectionEntry')) if u.get('type')=='unit' and 'damocles' in (u.get('name') or '').lower()]
for u in dam:
 bad=[x for x in u.iter(C('entryLink')) if x.get('targetId')=='r44-ba-overcharged-engines'];a(f'Damocles {u.get("id")}: bad_overcharged_links={len(bad)}');assert not bad
fj=[x for x in cont.iter(C('entryLink')) if x.get('targetId')=='r44-ba-furioso-jump-pack'];a(f'Contemptor Furioso link={[(x.get("id"),mods(x)) for x in fj]}');assert fj
a(f'High Priest rules={rules(pr)} fixed={[x.get("name") for x in pr.findall("./"+C("selectionEntries")+"/"+C("selectionEntry"))]}');assert {'Legion Support Officer','Apothecarion','Sanguinius’ Chosen'}<=set(rules(pr))

a('\n=== RETINUES / CHARACTERS ===')
for k in ('ral','zephon','crohne','amit','sang'):
 u=A[k];rgs=[(g.get('name'),[x.get('name') for x in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry'))]) for g in u.iter(C('selectionEntryGroup')) if 'retinue' in (g.get('name') or '').lower()];a(f'{k}: model={[m.get("name") for m in models(u)]} retinues={rgs}');assert models(u)
pra=byid(cr,'hq-praetor');pg=[x for x in pra.iter(C('selectionEntry')) if x.get('name')=='Sanguinary Guard Squad' and (x.get('id') or '').startswith('r74-ba-pra-')];a(f'Praetor Sanguinary Guard={[(x.get("id"),x.get("hidden"),mods(x)) for x in pg]}');assert pg

a('\n=== RITES ===')
rv=byid(cr,'r74-ba-rev-vet-veteran-unit');assert rv is not None;a(f'Revelation Veteran hidden={rv.get("hidden")} cats={cats(rv)} mods={mods(rv)}');assert any(x[1]=='cat-troops' and x[2]=='true' for x in cats(rv))
for cid in ('r74-ba-cat-revelation-comp','r74-ba-cat-sorrows-comp'):
 ce=byid(gr,cid);link=byid(gr,'r74-ba-fl-'+cid);a(f'{cid}: cat={ce is not None} constraints={cons(link,G)} mods={mods(link,G)}');assert ce is not None and link is not None
heavy=byid(gr,'fl-heavy');hm=[x for x in mods(heavy,G) if (x[0] or '').startswith('r74-ba-')];a(f'Heavy mods={hm}');assert any(x[0]=='r74-ba-rev-heavy-max' for x in hm)

a('\n=== SANGUINIUS ===')
sa=A['sang'];a(f'rules={rules(sa)} model={[m.get("name") for m in models(sa)]} modifiers={mods(sa)}');assert {'Primarch','Legiones Astartes (Blood Angels)','Angelic Charge','Sire of the Blood Angels','The Angel Descends'}<=set(rules(sa));assert any(c[3]=='allegiance-loyalist' for m in mods(sa) for c in m[4])

a('\n=== CONTEMPTOR DCCW STRUCTURE FOR FOLLOW-UP ===')
for g in cont.iter(C('selectionEntryGroup')):
 text=(g.get('name') or '').lower()+' '+ ' '.join((x.get('name') or '').lower() for x in g.iter(C('selectionEntry')))
 if any(w in text for w in ('dreadnought close combat','power fist','close combat weapon','gravis fist')):
  a(f'GROUP {g.get("id")} {g.get("name")} cons={cons(g)} mods={mods(g)}')
  for e in g.iter(C('selectionEntry')):a(f'  ENTRY {e.get("id")} {e.get("name")} cost={cost(e)} cons={cons(e)} mods={mods(e)}')

a('\n=== WARLORD / HQ JUMP-PACK STRUCTURE FOR FOLLOW-UP ===')
for e in cr.iter(C('selectionEntry')):
 n=(e.get('name') or '').lower();o=owner(e)
 if 'warlord' in n or ('jump pack' in n and o is not None and o.get('id') in ('hq-praetor','hq-centurion')):a(f'{e.get("id")} {e.get("name")} owner={o.get("id") if o is not None else ""} cons={cons(e)} mods={mods(e)}')
OUT.write_text('\n'.join(L),encoding='utf-8');print('\n'.join(L))
