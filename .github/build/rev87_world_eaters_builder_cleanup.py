from pathlib import Path
import re
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); IDX=Path('index.xml'); OUT=Path('inspection-r87-world-eaters-builder-cleanup.txt')
NS='http://www.battlescribe.net/schema/catalogueSchema'; ET.register_namespace('',NS); C=lambda t:f'{{{NS}}}{t}'
ct=ET.parse(CAT); root=ct.getroot()
assert root.get('revision')=='86', root.get('revision')
assert root.get('gameSystemRevision')=='51', root.get('gameSystemRevision')

def byid(i): return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t):
 x=p.find(C(t))
 if x is None:x=ET.SubElement(p,C(t))
 return x
def parent_map(): return {c:p for p in root.iter() for c in p}
def setpts(e,v):
 cs=ensure(e,'costs'); pts=next((x for x in cs.findall(C('cost')) if x.get('typeId')=='pts'),None)
 if pts is None: pts=ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
 else: pts.set('name','Points'); pts.set('value',str(v))
def set_constraint(e,typ,val,id_):
 cs=ensure(e,'constraints')
 for x in list(cs):
  if x.get('field')=='selections' and x.get('type')==typ: cs.remove(x)
 ET.SubElement(cs,C('constraint'),{'id':id_,'type':typ,'value':str(val),'field':'selections','scope':'parent','shared':'true','percentValue':'false','includeChildSelections':'true','includeChildForces':'false'})
def slug(s):return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def wipe_prefix(e,pfx):
 for p in list(e.iter()):
  for x in list(p):
   if (x.get('id') or '').startswith(pfx):p.remove(x)
def add_rule(e,id_,name,text):
 rs=ensure(e,'rules'); old=next((x for x in rs.findall(C('rule')) if x.get('id')==id_),None)
 if old is not None:rs.remove(old)
 r=ET.SubElement(rs,C('rule'),{'id':id_,'name':name,'hidden':'false'});ET.SubElement(r,C('description')).text=text
 return r
def locked_group(u,slug_,name,items):
 g=ET.SubElement(ensure(u,'selectionEntryGroups'),C('selectionEntryGroup'),{'id':f'r87-we-{slug_}-{slug(name)}','name':name,'hidden':'false','collective':'false','import':'true'})
 es=ET.SubElement(g,C('selectionEntries'))
 for n,desc in items:
  i=f'r87-we-{slug_}-{slug(name)}-{slug(n)}';e=ET.SubElement(es,C('selectionEntry'),{'id':i,'name':n,'type':'upgrade','hidden':'false','import':'true','defaultAmount':'1'})
  setpts(e,0);set_constraint(e,'min',1,i+'-min');set_constraint(e,'max',1,i+'-max')
  if desc:add_rule(e,i+'-rule',n,desc)
 return g
def scrub_source_blob(u):
 removed=0
 for p in list(u.iter()):
  rs=p.find(C('rules'))
  if rs is None:continue
  for r in list(rs):
   nm=(r.get('name') or '').strip().lower(); d=r.find(C('description')); tx=(d.text or '').lower() if d is not None else ''
   if nm.startswith('source entry') or ('force organisation:' in tx and 'wargear:' in tx and 'special rules:' in tx):
    rs.remove(r);removed+=1
 return removed
def models(u):return [e for e in u.iter(C('selectionEntry')) if e.get('type')=='model']
def maxsel(e):
 return max([float(c.get('value','0')) for c in e.findall('./'+C('constraints')+'/'+C('constraint')) if c.get('field')=='selections' and c.get('type')=='max'] or [0])
def remove_node(node):
 pm=parent_map();p=pm.get(node)
 if p is not None:p.remove(node)
def normalize_models(u,label,base,total,ppm,overhead):
 ms=[m for m in models(u) if maxsel(m)>1 or (m.get('name') or '').lower() in ('squad models','additional model',label.lower())]
 preferred=[m for m in ms if (m.get('name') or '').strip().lower()==label.lower()]
 if not preferred:
  preferred=[m for m in ms if (m.get('name') or '').strip().lower() not in ('squad models','additional model')]
 if preferred: keep=preferred[0]
 else:
  keep=ET.SubElement(ensure(u,'selectionEntries'),C('selectionEntry'),{'id':f'r87-we-{slug(label)}-models','name':label,'type':'model','hidden':'false','import':'true'})
 for m in list(ms):
  if m is not keep:remove_node(m)
 keep.set('name',label);keep.set('defaultAmount',str(base));keep.set('hidden','false');setpts(keep,ppm)
 set_constraint(keep,'min',base,keep.get('id')+'-r87-min');set_constraint(keep,'max',total,keep.get('id')+'-r87-max')
 setpts(u,overhead)
 return keep
def add_scaled_cost(opt,per,model_id):
 setpts(opt,0)
 ms=ensure(opt,'modifiers')
 for x in list(ms):
  if (x.get('id') or '').startswith('r86-scaled-cost-') or (x.get('id') or '').startswith('r87-we-scaled-'):ms.remove(x)
 mid='r87-we-scaled-'+slug(opt.get('id') or opt.get('name') or 'x')
 m=ET.SubElement(ms,C('modifier'),{'id':mid,'type':'increment','field':'pts','value':str(per)})
 reps=ET.SubElement(m,C('repeats'));ET.SubElement(reps,C('repeat'),{'field':'selections','scope':'root-entry','value':'1','percentValue':'false','shared':'true','includeChildSelections':'true','includeChildForces':'false','childId':model_id,'repeats':'1','roundUp':'false'})
def cleanup_per_model(u,model_id):
 for x in u.iter(C('selectionEntry')):
  if x is u:continue
  nm=x.get('name') or ''
  m=re.search(r'\(base unit;\s*\+([0-9]+) pts/model\)',nm,re.I)
  if m:
   x.set('name',nm[:m.start()].strip());add_scaled_cost(x,int(m.group(1)),model_id)
  elif nm.strip().lower() in ('jump packs','krak grenades','melta bombs','frag grenades'):
   # Only convert if an existing R86 per-model helper/rule marks it as squad-wide.
   desc=' '.join((d.text or '') for d in x.findall('.//'+C('description')))
   mm=re.search(r'costs \+([0-9]+) points per model',desc,re.I)
   if mm:add_scaled_cost(x,int(mm.group(1)),model_id)
def dynamic_cap_by_models(x,model_id,threshold,low,high):
 cs=ensure(x,'constraints')
 for c in list(cs):
  if c.get('type')=='max' and c.get('field')=='selections':cs.remove(c)
 cid='r87-we-'+slug(x.get('id') or x.get('name'))+'-max';ET.SubElement(cs,C('constraint'),{'id':cid,'type':'max','value':str(low),'field':'selections','scope':'parent','shared':'true','percentValue':'false','includeChildSelections':'true','includeChildForces':'false'})
 mods=ensure(x,'modifiers');mid=cid+'-at-'+str(threshold)
 for m in list(mods):
  if m.get('id')==mid:mods.remove(m)
 mod=ET.SubElement(mods,C('modifier'),{'id':mid,'type':'set','field':cid,'value':str(high)});conds=ET.SubElement(mod,C('conditions'));ET.SubElement(conds,C('condition'),{'type':'atLeast','value':str(threshold),'field':'selections','scope':'root-entry','childId':model_id,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

SQUADS={
 'r41-unit-xii-0-rampager-squad':('Rampager',5,10,22,0),
 'r41-unit-xii-1-red-butcher-squad':('Red Butcher',5,10,60,0),
 'r41-unit-xii-2-red-hand-destroyer-mortalis-squad':('Red Hand Destroyer',5,10,22,50),
 'r41-unit-xii-3-world-eaters-inductii-squad':('Inductii',10,20,13,0),
 'r41-unit-xii-4-devourer-terminator-squad':('Devourer',5,10,45,0),
 'r41-unit-xii-5-triarii-breacher-squad':('Triarii Breacher',5,10,27,20),
}
# Also normalize exact-named rite / Rewards copies so the bad duplicate size controls cannot survive elsewhere.
NAMECFG={
 'rampager squad':('Rampager',5,10,22,0),'red butcher squad':('Red Butcher',5,10,60,0),'red hand destroyer mortalis squad':('Red Hand Destroyer',5,10,22,50),'world eaters inductii squad':('Inductii',10,20,13,0),'devourer terminator squad':('Devourer',5,10,45,0),'triarii breacher squad':('Triarii Breacher',5,10,27,20)}
normalized=[]
for e in root.iter(C('selectionEntry')):
 if e.get('type')!='unit':continue
 base_name=(e.get('name') or '').split(' — ')[0].strip().lower()
 cfg=None
 if e.get('id') in SQUADS:cfg=SQUADS[e.get('id')]
 elif base_name in NAMECFG and ('r42-role-xii' in (e.get('id') or '') or 'r46-al-reward' in (e.get('id') or '')):cfg=NAMECFG[base_name]
 if cfg:
  m=normalize_models(e,*cfg);cleanup_per_model(e,m.get('id'));normalized.append((e,m,cfg))

# Red Hand option cleanup: source says one special pistol/missile and one phosphex per five models.
red=byid('r41-unit-xii-2-red-hand-destroyer-mortalis-squad'); redm=next(m for m in models(red) if (m.get('name') or '')=='Red Hand Destroyer')
for x in red.iter(C('selectionEntry')):
 nm=(x.get('name') or '').strip(); low=nm.lower()
 if low=='and rad missiles':x.set('name','Missile launcher with Suspensor Web and Rad Missiles');low=x.get('name').lower()
 if any(k in low for k in ('volkite serpenta','hand flamer','plasma pistol','missile launcher with suspensor web')) and x.get('type')!='model':dynamic_cap_by_models(x,redm.get('id'),10,1,2)
 if 'one phosphex bomb' in low:dynamic_cap_by_models(x,redm.get('id'),10,1,2)

# Remove source dumps from every canonical XII unit/character, then build clean source-derived packages.
canon=[e for e in root.iter(C('selectionEntry')) if (e.get('id') or '').startswith('r41-unit-xii-')]
removed=sum(scrub_source_blob(e) for e in canon)
for e in canon:wipe_prefix(e,'r87-we-')

PKG={
'r41-unit-xii-0-rampager-squad':(
 [('Power Armour',''),('Bolt pistol',''),('Chainaxe','An Armour Save better than 4+ is reduced to 4+ against wounds caused by a Chainaxe; Invulnerable Saves are unaffected.')],
 [('Legiones Astartes (World Eaters)','Uses the World Eaters Legion special rule.')]),
'r41-unit-xii-1-red-butcher-squad':(
 [('Cataphractii Terminator Armour',''),('Two Power weapons','')],
 [('Legiones Astartes (World Eaters)','Uses the World Eaters Legion special rule.'),('Fearless','Uses the normal Fearless special rule.'),('Ravening Madmen','Red Butchers always hit models with a Weapon Skill on a 3+ in close combat, and enemy models likewise always hit Red Butchers on a 3+. This does not affect attacks against targets without Weapon Skill and does not override a better fixed To Hit result. Red Butchers never count as a Scoring Unit.')]),
'r41-unit-xii-2-red-hand-destroyer-mortalis-squad':(
 [('Power Armour',''),('Two Bolt pistols',''),('Chainaxe','An Armour Save better than 4+ is reduced to 4+ against wounds caused by a Chainaxe; Invulnerable Saves are unaffected.'),('Frag grenades',''),('Rad grenades','')],
 [('Legiones Astartes (World Eaters)','Uses the World Eaters Legion special rule.'),('Counter-Attack','Uses the normal Counter-Attack special rule.'),('Dual Pistols','The unit is equipped with two Bolt pistols as listed in its wargear.'),('Destroyer Cadre','This unit follows the Destroyer Cadre rules and restrictions.')]),
'r41-unit-xii-3-world-eaters-inductii-squad':(
 [('Power Armour',''),('Bolt pistol',''),('Chainsword','')],
 [('Legiones Astartes (World Eaters)','Uses the World Eaters Legion special rule.'),('Nails-Broken','If an Inductii Squad is able to declare a charge during the Assault phase, it must do so. If more than one enemy unit may legally be charged, the World Eaters player chooses the target normally.')]),
'r41-unit-xii-4-devourer-terminator-squad':(
 [('Cataphractii Terminator Armour',''),('Combi-bolter',''),('Power weapon','')],
 [('Legiones Astartes (World Eaters)','Uses the World Eaters Legion special rule.'),('Stubborn','Uses the normal Stubborn special rule.'),('Devourers','Angron may select one Devourer Terminator Squad as his retinue.')]),
'r41-unit-xii-5-triarii-breacher-squad':(
 [('Power Armour',''),('Bolt pistol',''),('Chainaxe','An Armour Save better than 4+ is reduced to 4+ against wounds caused by a Chainaxe; Invulnerable Saves are unaffected.'),('Boarding Shield',''),('Frag grenades','')],
 [('Legiones Astartes (World Eaters)','Uses the World Eaters Legion special rule.'),('Counter-Attack','Uses the normal Counter-Attack special rule.'),('Breachers','Uses the normal Breachers special rule.')]),
}
for uid,(wg,sr) in PKG.items():
 u=byid(uid);locked_group(u,slug(uid),'Wargear',wg);locked_group(u,slug(uid),'Special Rules',sr)

# Named character packages: clean builder presentation instead of a full source paragraph.
CHARS={
'r41-unit-xii-6-kharn-the-bloody':(
 [('Artificer Armour',''),('Iron Halo',''),('Gorechild','Gorechild is a Master-crafted Power Weapon which grants Khârn +3 Strength. At the beginning of the first round of each close combat, roll a D3; Khârn gains that many additional Attacks for that round.'),('Plasma pistol',''),('Frag grenades','')],
 [('Legiones Astartes (World Eaters)','Uses the World Eaters Legion special rule.'),('Independent Character','Uses the normal Independent Character rules.'),('The Bloody','Whenever Khârn rolls a natural 1 To Hit in close combat, that attack instead hits the nearest friendly model within 6 inches. If several are equally close, the opposing player chooses. Resolve the hit using Khârn’s current Strength and weapon. Saves are allowed normally; these Wounds do not count toward combat result. If no friendly model is within 6 inches, the roll of 1 is a miss.'),('Command Retinue','Khârn may select one Legion Command Squad or Rampager Squad as his retinue. The selected unit does not occupy a separate Force Organisation slot.')]),
'r41-unit-xii-7-shabran-darr':(
 [],[('Legiones Astartes (World Eaters)','Uses the World Eaters Legion special rule.'),('Independent Character','Uses the normal Independent Character rules.'),('Master of Destroyers','Shabran Darr may join Legion Destroyer Squads and Red Hand Destroyer Squads despite the normal restrictions imposed by Destroyer Cadre. Darr may select one Red Hand Destroyer Mortalis or Assault Squad as his retinue; it does not occupy a separate Force Organisation slot.')]),
'r41-unit-xii-8-gahlan-surlak':(
 [('Power Armour',''),('Refractor Field',''),('Narthecium',''),('Reductor',''),('Bolt pistol',''),('Chainsword',''),('Frag grenades','')],
 [('Legiones Astartes (World Eaters)','Uses the World Eaters Legion special rule.'),('Independent Character','Uses the normal Independent Character rules.'),('Apothecary','Uses the normal Apothecary rules.'),('Architect of the Nails','After deployment but before the first turn begins, nominate one friendly World Eaters Infantry unit not wearing Terminator Armour. That unit gains Furious Charge for the battle and must declare a charge whenever legally able. Only one unit may be enhanced in this manner.'),('Legion Support Officer','Uses the normal Legion Support Officer rule.')]),
'r41-unit-xii-9-kargos-the-bloodspitter':(
 [('Power Armour',''),('Narthecium',''),('Reductor',''),('Chainaxe','An Armour Save better than 4+ is reduced to 4+ against wounds caused by a Chainaxe; Invulnerable Saves are unaffected.'),('Bolt pistol',''),('Frag grenades','')],
 [('Legiones Astartes (World Eaters)','Uses the World Eaters Legion special rule.'),('Independent Character','Uses the normal Independent Character rules.'),('Apothecary','Uses the normal Apothecary rules.'),('Warrior-Apothecary','Kargos may use his Narthecium even while he is in base contact with an enemy model. All other normal Narthecium restrictions continue to apply.'),('Command Retinue','Kargos may select one Legion Command Squad. If Kargos has a Jump Pack, the Command Squad may purchase Jump Packs normally. The selected squad does not occupy a separate Force Organisation slot.')]),
'r41-unit-xii-10-captain-ehrlen':(
 [('Power Armour',''),('Refractor Field',''),('Jump Pack',''),('Rending Weapon',''),('Bolt pistol',''),('Bionics',''),('Frag grenades','')],
 [('Legiones Astartes (World Eaters)','Uses the World Eaters Legion special rule.'),('Independent Character','Uses the normal Independent Character rules.'),('Loyalist Only','Captain Ehrlen may only be selected in a Loyalist army.'),('Command Retinue','Ehrlen may select one Legion Command Squad as his retinue. Every model in the Command Squad may purchase a Jump Pack for +15 points per model. If Jump Packs are purchased, every model must receive one and the squad may not select a Dedicated Transport. The Command Squad does not occupy a separate Force Organisation slot.')]),
'r41-unit-xii-11-delvarus':(
 [('Power Armour',''),('Caedere Weapon','A Caedere Weapon is a one-handed close-combat weapon at User +1 Strength with Rending; it is not a Power Weapon.'),('Bolt pistol',''),('Boarding Shield',''),('Frag grenades','')],
 [('Legiones Astartes (World Eaters)','Uses the World Eaters Legion special rule.'),('Independent Character','Uses the normal Independent Character rules.'),('Gladiator Champion','Any Triarii Breacher Squad joined by Delvarus gains Stubborn and Furious Charge.'),('Command Retinue','Delvarus may select one Legion Triarii Breacher Squad as his retinue. The selected squad does not occupy a separate Force Organisation slot.')]),
}
for uid,(wg,sr) in CHARS.items():
 u=byid(uid)
 if u is None:continue
 if wg:locked_group(u,slug(uid),'Wargear',wg)
 locked_group(u,slug(uid),'Special Rules',sr)

# Daemon Angron: source-listed wargear and every listed special rule gets an actual rule tooltip.
ang=byid('r41-unit-xii-13-angron-the-red-angel')
if ang is None:raise RuntimeError('Daemon Angron missing')
# Keep the R86 source-faithful discrete rules but expose them as locked tooltip entries too.
def ruletext(name):
 r=next((r for r in ang.findall('./'+C('rules')+'/'+C('rule')) if (r.get('name') or '')==name),None);d=r.find(C('description')) if r is not None else None;return (d.text or '') if d is not None else ''
locked_group(ang,'angron-daemon','Wargear',[
 ('Blades of the Red Angel',ruletext('Blades of the Red Angel')),('Daemonic Armour','Angron has the 2+ Armour Save and 4+ Invulnerable Save shown in his profile.')])
locked_group(ang,'angron-daemon','Special Rules',[(n,ruletext(n) or ('Uses the normal '+n+' special rule.')) for n in ('Daemon','Fear','Fearless','Fleet','Furious Charge','Eternal Warrior','Adamantium Will','Master of the Legion','Daemonic Flight','Blood Calls to Blood','The Red Angel Descends','The Nails Sing')])

# Clean labels globally within canonical XII entries.
for u in canon:
 for x in u.iter(C('selectionEntry')):
  nm=x.get('name') or ''
  x.set('name',re.sub(r'\s+',' ',nm).strip())

# Validation: no source blobs; no duplicate squad counters; source totals remain exact.
for u in canon:
 for r in u.iter(C('rule')):
  nm=(r.get('name') or '').lower();d=r.find(C('description'));tx=(d.text or '').lower() if d is not None else ''
  assert not nm.startswith('source entry'), (u.get('name'),r.get('name'))
  assert not ('force organisation:' in tx and 'wargear:' in tx and 'special rules:' in tx),u.get('name')
for uid,(label,base,total,ppm,overhead) in SQUADS.items():
 u=byid(uid); expandable=[m for m in models(u) if maxsel(m)>1]
 assert len(expandable)==1,(uid,[(m.get('name'),maxsel(m)) for m in expandable])
 m=expandable[0];assert m.get('name')==label;assert m.get('defaultAmount')==str(base);assert maxsel(m)==total
 p=next(c for c in m.findall('./'+C('costs')+'/'+C('cost')) if c.get('typeId')=='pts');assert float(p.get('value'))==ppm
 up=next(c for c in u.findall('./'+C('costs')+'/'+C('cost')) if c.get('typeId')=='pts');assert float(up.get('value'))==overhead
 assert overhead+base*ppm=={'r41-unit-xii-0-rampager-squad':110,'r41-unit-xii-1-red-butcher-squad':300,'r41-unit-xii-2-red-hand-destroyer-mortalis-squad':160,'r41-unit-xii-3-world-eaters-inductii-squad':130,'r41-unit-xii-4-devourer-terminator-squad':225,'r41-unit-xii-5-triarii-breacher-squad':155}[uid]
assert not any((m.get('name') or '').lower() in ('squad models','additional model') and maxsel(m)>1 for u in [byid(i) for i in SQUADS] for m in models(u))
assert any((r.get('name') or '')=='Blood Calls to Blood' for r in ang.iter(C('rule')))
ehr=byid('r41-unit-xii-10-captain-ehrlen');assert any((g.get('name') or '')=='Special Rules' for g in ehr.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')))

root.set('revision','87');ct.write(CAT,encoding='utf-8',xml_declaration=True)
raw=CAT.read_text(encoding='utf-8').replace(f'xmlns:ns0="{NS}"',f'xmlns="{NS}"').replace('<ns0:','<').replace('</ns0:','</');CAT.write_text(raw,encoding='utf-8')
idx=IDX.read_text(encoding='utf-8');idx,n=re.subn(r'(filePath="Legiones Astartes\.cat"[^>]*dataRevision=")86(" )',r'\g<1>87\g<2>',idx,count=1)
if n!=1:raise RuntimeError('index revision bump failed')
IDX.write_text(idx,encoding='utf-8')
OUT.write_text(f'''Revision 87 — World Eaters builder cleanup\nCAT=87 GSTref=51\nSource blobs removed: {removed}\n\nSquad-size UI normalized to ONE source-correct model counter:\n- Rampagers 5–10 @ 22/model (110 starting total)\n- Red Butchers 5–10 @ 60/model (300 starting total)\n- Red Hand Destroyers 5–10 @ 22/model + 50 fixed (160 starting total)\n- Inductii 10–20 @ 13/model (130 starting total)\n- Devourers 5–10 @ 45/model (225 starting total)\n- Triarii 5–10 @ 27/model + 20 fixed (155 starting total)\n\nPresentation:\n- Removed Source Entry dump rules from all XII canonical entries\n- Added structured Wargear and Special Rules sections to unique squads and named characters\n- Captain Ehrlen now has clean wargear, Loyalist Only and Command Retinue tooltips\n- Daemon Angron now exposes every source-listed special rule and wargear item as a clickable tooltip entry\n- Red Hand missile option renamed correctly and its one-per-five limits scale 1/2 at 5/10 models\n- Squad-wide per-model upgrade labels/cost helpers cleaned up\n''',encoding='utf-8')
print(OUT.read_text())
