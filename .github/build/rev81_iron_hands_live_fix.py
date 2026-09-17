from pathlib import Path
import copy,re,xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r81-iron-hands-live-fix.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS);ET.register_namespace('',GNS);ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT);cr=ct.getroot();gt=ET.parse(GST);gr=gt.getroot();it=ET.parse(IDX);ir=it.getroot()
if cr.get('revision')!='80' or gr.get('revision')!='47': raise RuntimeError(f'Expected CAT80/GST47, got CAT{cr.get("revision")}/GST{gr.get("revision")}')
LEG='legion-x'; HEAD='r25-rite-x-0-the-head-of-the-gorgon'; BITTER='r25-rite-x-1-company-of-bitter-iron'; FERRUS='r41-unit-x-7-x-ferrus-manus-the-gorgon'; AUTEK='r41-unit-x-5-autek-mor'; IMM='r41-unit-x-0-medusan-immortal-squad'
def byid(root,i):return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t,Q=C):
 x=p.find(Q(t));
 if x is None:x=ET.SubElement(p,Q(t))
 return x
def wipe(p,t,Q=C):
 x=p.find(Q(t));
 if x is not None:p.remove(x)
def setpts(e,v):
 cs=ensure(e,'costs');[cs.remove(x) for x in list(cs)];ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def constraint(p,i,typ,val,scope='parent',Q=C,field='selections'):
 return ET.SubElement(ensure(p,'constraints',Q),Q('constraint'),{'id':i,'type':typ,'value':str(val),'field':field,'scope':scope,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_rule(p,i,n,t):
 rs=ensure(p,'rules');r=ET.SubElement(rs,C('rule'),{'id':i,'name':n,'hidden':'false'});ET.SubElement(r,C('description')).text=t;return r
def slug(s):return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def remove_prefix(root,pfx):
 for p in list(root.iter()):
  for x in list(p):
   if (x.get('id') or '').startswith(pfx):p.remove(x)
def show_if(e,i,conds):
 e.set('hidden','true');m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'});cg=ET.SubElement(ET.SubElement(m,C('conditionGroups')),C('conditionGroup'),{'type':'and'});cs=ET.SubElement(cg,C('conditions'))
 for typ,val,scope,child in conds:ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def hide_if(e,i,child):
 m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'true','field':'hidden'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def find_named(name):
 return next((e for e in cr.iter(C('selectionEntry')) if (e.get('name') or '').strip().lower()==name.lower()),None)
def stripcats(e):wipe(e,'categoryLinks')
def direct_models(u):return [x for x in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if x.get('type')=='model']
def scrub_source(u):
 n=0
 for p in list(u.iter()):
  for container_tag,item_tag in [('rules','rule'),('infoLinks','infoLink')]:
   box=p.find(C(container_tag))
   if box is not None:
    for x in list(box):
     nm=(x.get('name') or '').lower();desc=' '.join((d.text or '') for d in x.findall('.//'+C('description'))).lower()
     if nm.startswith('source entry') or ('force organisation:' in desc and 'wargear:' in desc):box.remove(x);n+=1
 return n
remove_prefix(cr,'r81-ih-');remove_prefix(gr,'r81-ih-')
# 1 presentation hardening
canon=[IMM,'r41-unit-x-1-gorgon-terminator-squad','r41-unit-x-2-morlock-terminator-squad','r41-unit-x-3-venerable-forge-lord','r41-unit-x-4-shadrak-meduson',AUTEK,'r41-unit-x-6-gabriel-santar',FERRUS]
cleaned=0
for u in cr.iter(C('selectionEntry')):
 if u.get('type')=='unit' and any(k in (u.get('id') or '') for k in canon): cleaned+=scrub_source(u)
# ensure no direct profiles on named character shells; move to their locked model child if needed
for uid,key in [(AUTEK,'autek'),(FERRUS,'ferrus')]:
 u=byid(cr,uid);ps=u.find(C('profiles')) if u is not None else None
 if u is not None and ps is not None and len(ps):
  models=direct_models(u);m=models[0] if models else ET.SubElement(ensure(u,'selectionEntries'),C('selectionEntry'),{'id':f'r81-ih-{key}-model','name':u.get('name'),'type':'model','hidden':'false','import':'true','defaultAmount':'1'})
  if not models:constraint(m,f'r81-ih-{key}-model-min','min',1);constraint(m,f'r81-ih-{key}-model-max','max',1)
  dst=ensure(m,'profiles');[dst.append(x) for x in list(ps)];u.remove(ps)
# 2 Dangerous Weaponry: remove old standalone substitution links, add Grav Gun directly beside Flamer in Special Weapons groups
removed_grav=0
for p in list(cr.iter()):
 els=p.find(C('entryLinks'))
 if els is not None:
  for l in list(els):
   if l.get('targetId')=='r44-ih-graviton-substitution' or (l.get('id') or '').startswith('r80-ih-grav-special-'):
    els.remove(l);removed_grav+=1
grav=byid(cr,'gear-graviton-gun')
if grav is None:raise RuntimeError('Missing shared Graviton Gun')
added_grav=0
for g in list(cr.iter(C('selectionEntryGroup'))):
 if 'special weapon' not in (g.get('name') or '').lower():continue
 children=list(g.findall('./'+C('entryLinks')+'/'+C('entryLink')))+list(g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')))
 flam=next((x for x in children if (x.get('name') or '').strip().lower()=='flamer'),None)
 if flam is None:continue
 links=ensure(g,'entryLinks');lid=f'r81-ih-grav-{added_grav}'
 l=ET.SubElement(links,C('entryLink'),{'id':lid,'name':'Graviton Gun','type':'selectionEntry','targetId':'gear-graviton-gun','hidden':'true','import':'true'})
 # copy flamer max quantity if present; parent group remains the overall special-weapon cap
 mx=next((c for c in flam.findall('./'+C('constraints')+'/'+C('constraint')) if c.get('type')=='max'),None);constraint(l,lid+'-max','max',mx.get('value') if mx is not None else 99)
 setpts(l,15);show_if(l,lid+'-show',[('atLeast',1,'roster',LEG)]);added_grav+=1
# 3 Ferrus: real fixed wargear/profile package
fer=byid(cr,FERRUS)
if fer is None:raise RuntimeError('Missing Ferrus')
# remove any previous R79/R80 fixed local wargear we can identify by exact names under direct child upgrades, leaving retinues/model intact
ses=ensure(fer,'selectionEntries')
for x in list(ses):
 if x.get('type')=='upgrade' and (x.get('name') or '') in ('Medusan Carapace','Forgebreaker','Living Metal Hands','Frag Grenades','Cortex Controller','Nuncio Vox','Twin-linked Meltagun','Twin-linked Plasma Gun','Heavy Flamer'):ses.remove(x)
def fixed_local(name,ruletext=None):
 e=ET.SubElement(ses,C('selectionEntry'),{'id':'r81-ih-ferrus-'+slug(name),'name':name,'type':'upgrade','hidden':'false','import':'true','defaultAmount':'1'});setpts(e,0);constraint(e,e.get('id')+'-min','min',1);constraint(e,e.get('id')+'-max','max',1)
 if ruletext:add_rule(e,e.get('id')+'-rule',name,ruletext)
 return e
def clone_fixed(source_name,newname,extra_rule=None,strength=None):
 src=find_named(source_name)
 if src is None:return fixed_local(newname,extra_rule)
 e=copy.deepcopy(src)
 for z in e.iter():
  if z.get('id'):z.set('id','r81-ih-ferrus-'+slug(newname)+'-'+z.get('id'))
 e.set('id','r81-ih-ferrus-'+slug(newname));e.set('name',newname);e.set('type','upgrade');e.set('hidden','false');e.set('defaultAmount','1');stripcats(e);wipe(e,'constraints');constraint(e,e.get('id')+'-min','min',1);constraint(e,e.get('id')+'-max','max',1);setpts(e,0)
 if strength:
  for ch in e.iter(C('characteristic')):
   if (ch.get('name') or '').lower()=='strength':ch.text=strength
 if extra_rule:add_rule(e,e.get('id')+'-extra',newname,extra_rule)
 ses.append(e);return e
fixed_local('Medusan Carapace','Counts as Primarch Armour. It incorporates a Twin-linked Meltagun, Twin-linked Plasma Gun, Heavy Flamer, Cortex Controller and Nuncio Vox. Ferrus Manus may fire up to two incorporated weapons in each Shooting phase.')
clone_fixed('Thunder Hammer','Forgebreaker','Master-crafted Thunder Hammer with Armourbane.')
clone_fixed('Power Weapon','Living Metal Hands','Ferrus may use his Living Metal Hands instead of Forgebreaker. Their attacks are Power Weapon attacks resolved at Strength 8.','8')
clone_fixed('Frag Grenades','Frag Grenades')
clone_fixed('Meltagun','Twin-linked Meltagun','This weapon is Twin-linked.')
clone_fixed('Plasma Gun','Twin-linked Plasma Gun','This weapon is Twin-linked.')
clone_fixed('Heavy Flamer','Heavy Flamer')
clone_fixed('Cortex Controller','Cortex Controller')
clone_fixed('Nuncio Vox','Nuncio Vox')
# reinforce full current Ferrus named rules as distinct rules, not source dump
rs=ensure(fer,'rules')
for r in list(rs):
 if (r.get('id') or '').startswith('r81-ih-ferrus-rule-'):rs.remove(r)
for n,t in [
('Primarch','Ferrus Manus uses the universal Primarch rules in Forces of the Legions.'),('Legiones Astartes (Iron Hands)','Ferrus Manus counts as a member of the X Legion for rules and effects that refer to Iron Hands.'),('The Gorgon','Ferrus Manus has Feel No Pain (5+).'),('Master of the Forge','Ferrus Manus has Battlesmith and succeeds on a 3+. He may repair friendly Vehicles, Dreadnoughts and Battle-Automata as appropriate.'),('Forged for War','After both armies are selected but before deployment, nominate one friendly Iron Hands Vehicle or Dreadnought which is not a Lord of War. It gains +1 Structure Point for the battle. If it does not normally use Structure Points, determine its normal Structure Point value using the standard ProHammer rules before applying this bonus.')]:add_rule(fer,'r81-ih-ferrus-rule-'+slug(n),n,t)
# 4 Rites: rebuild visibility, named rules, and enforceable parts
head=byid(cr,HEAD);bitter=byid(cr,BITTER)
for r in (head,bitter):
 wipe(r,'modifiers');wipe(r,'rules')
show_if(head,'r81-ih-head-visible',[('atLeast',1,'roster',LEG)])
show_if(bitter,'r81-ih-bitter-visible',[('atLeast',1,'roster',LEG),('atLeast',1,'roster','allegiance-loyalist')])
for k,n,t in [('ground','Ground of Choice','All Iron Hands Infantry units gain Stubborn while at least half of the unit’s surviving models are within the Iron Hands deployment zone.'),('relic','Relics of War','All Iron Hands Vehicles in the Detachment receive Blessed Autosimulacra at no additional points cost.'),('scions','Scions of Iron','Any Iron Hands Infantry unit of ten models or fewer which may normally select a Rhino as a Dedicated Transport may instead select a Land Raider Phobos or Land Raider Proteus as a Dedicated Transport at normal points cost. Normal Transport Capacity restrictions apply.'),('encirclement','Armoured Encirclement','Iron Hands Vehicles with the Tank unit type gain Outflank if placed in Reserve. A Dedicated Transport carrying a unit may Outflank with its passengers as one Reserve entry.'),('limits','Limitations','No more than one Fast Attack choice. No more than one Consul, excluding Forge Lords. No Allied Detachment drawn from another Space Marine Legion.')]:add_rule(head,'r81-ih-head-'+k,n,t)
for k,n,t in [('company','Company of Immortals','Medusan Immortal Squads may be selected as Troops and fulfil compulsory Troops selections. At least one compulsory Troops choice must be a Medusan Immortal Squad.'),('hatred','Immortal Hatred','All units with Legiones Astartes (Iron Hands) gain Hatred against Traitor forces.'),('duty','Bitter Duty','A Medusan Immortal Squad gains Fearless while the majority of its surviving models are within the enemy deployment zone.'),('purpose','No Death Without Purpose','When a Medusan Immortal Squad is destroyed while the majority of its models were within the enemy deployment zone immediately before destruction, every friendly Iron Hands unit within 6 inches may immediately re-roll any failed Morale or Pinning test required as a result.'),('limits','Limitations','Loyalist Iron Hands only. No Allied Detachment. Ferrus Manus may not be included.')]:add_rule(bitter,'r81-ih-bitter-'+k,n,t)
# Head Fast Attack max1
flfast=byid(gr,'fl-fast')
if flfast is not None:
 mx=next((x for x in flfast.findall('./'+G('constraints')+'/'+G('constraint')) if x.get('type')=='max'),None)
 if mx is not None:
  m=ET.SubElement(ensure(flfast,'modifiers',G),G('modifier'),{'id':'r81-ih-head-fast-max','type':'set','value':'1','field':mx.get('id')});cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
# Head max1 non-Forge Consul via hidden category
cats=ensure(gr,'categoryEntries',G);CC='r81-ih-nonforge-consul';cat=ET.SubElement(cats,G('categoryEntry'),{'id':CC,'name':'Head of the Gorgon — non-Forge Consul','hidden':'true'})
consulgrp=byid(cr,'hq-centurion-consuls');consul_count=0
if consulgrp is not None:
 for e in consulgrp.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')):
  if e.get('id')=='hq-consul-forge' or 'forge lord' in (e.get('name') or '').lower():continue
  cls=ensure(e,'categoryLinks');ET.SubElement(cls,C('categoryLink'),{'id':f'r81-ih-consul-cat-{consul_count}','name':'Head of the Gorgon — non-Forge Consul','hidden':'true','targetId':CC,'primary':'false'});consul_count+=1
force=byid(gr,'force-standard')
if force is not None:
 cl=ET.SubElement(ensure(force,'categoryLinks',G),G('categoryLink'),{'id':'r81-ih-head-consul-limit','name':'Head of the Gorgon — non-Forge Consul','hidden':'true','targetId':CC});c=constraint(cl,'r81-ih-head-consul-max','max',99,Q=G);m=ET.SubElement(ensure(cl,'modifiers',G),G('modifier'),{'id':'r81-ih-head-consul-set','type':'set','value':'1','field':c.get('id')});cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
# Blessed Autosimulacra free + compulsory while Head active
forced_auto=0
for l in cr.iter(C('entryLink')):
 if l.get('targetId')!='r44-ih-autosimulacra':continue
 mods=ensure(l,'modifiers');m=ET.SubElement(mods,C('modifier'),{'id':f'r81-ih-auto-free-{forced_auto}','type':'set','value':'0','field':'pts'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'});c=constraint(l,f'r81-ih-auto-min-{forced_auto}','min',0);m2=ET.SubElement(mods,C('modifier'),{'id':f'r81-ih-auto-force-{forced_auto}','type':'set','value':'1','field':c.get('id')});cs2=ET.SubElement(m2,C('conditions'));ET.SubElement(cs2,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'});forced_auto+=1
# Scions: discard prior r79/r80 Scions entries then add Phobos/Proteus only where a Rhino choice already exists, inheriting Rhino visibility logic
for p in list(cr.iter()):
 ses2=p.find(C('selectionEntries'))
 if ses2 is not None:
  for x in list(ses2):
   if 'scions' in (x.get('id') or '') and ('phobos' in (x.get('id') or '') or 'proteus' in (x.get('id') or '')):ses2.remove(x)
ph=find_named('Land Raider Phobos');pr=find_named('Land Raider Proteus');scions=0
if ph is not None and pr is not None:
 for g in list(cr.iter(C('selectionEntryGroup'))):
  if 'dedicated transport' not in (g.get('name') or '').lower():continue
  rhinos=[x for x in list(g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')))+list(g.findall('./'+C('entryLinks')+'/'+C('entryLink'))) if 'rhino' in (x.get('name') or '').lower()]
  if not rhinos:continue
  rh=rhinos[0]
  for base,label in ((ph,'Land Raider Phobos (Scions of Iron)'),(pr,'Land Raider Proteus (Scions of Iron)')):
   x=copy.deepcopy(base);pref=f'r81-ih-scions-{scions}-'
   for z in x.iter():
    if z.get('id'):z.set('id',pref+z.get('id'))
   x.set('id',pref+slug(label));x.set('name',label);x.set('type','upgrade');stripcats(x);setpts(x,250 if 'Phobos' in label else 200)
   # inherit Rhino hide logic, then additionally hide unless Head is selected
   wipe(x,'modifiers');
   rhmods=rh.find(C('modifiers'))
   if rhmods is not None:
    mods=ensure(x,'modifiers');
    for mm in list(rhmods):mods.append(copy.deepcopy(mm))
   x.set('hidden',rh.get('hidden','false'));m=ET.SubElement(ensure(x,'modifiers'),C('modifier'),{'id':pref+'head-hide','type':'set','value':'true','field':'hidden'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'lessThan','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
   ensure(g,'selectionEntries').append(x);scions+=1
# Bitter Troops clone: make existing role clone function and enforce >=1
role=byid(cr,'r42-role-x-1-effects-company-of-immortals-medusan-immortal-squads-r41-unit-x-0-medusan-immortal-squad')
if role is None:raise RuntimeError('Missing Bitter Iron Immortal role clone')
wipe(role,'modifiers');show_if(role,'r81-ih-bitter-role-show',[('atLeast',1,'roster',LEG),('atLeast',1,'roster',BITTER)])
catsr=ensure(role,'categoryLinks')
for c in catsr.findall(C('categoryLink')):c.set('primary','false')
tro=next((c for c in catsr.findall(C('categoryLink')) if c.get('targetId')=='cat-troops'),None)
if tro is None:tro=ET.SubElement(catsr,C('categoryLink'),{'id':'r81-ih-bitter-troops','name':'Troops','hidden':'false','targetId':'cat-troops','primary':'true'})
else:tro.set('primary','true')
BC='r81-ih-bitter-comp';bcat=ET.SubElement(cats,G('categoryEntry'),{'id':BC,'name':'Company of Bitter Iron — compulsory Immortal','hidden':'true'});ET.SubElement(catsr,C('categoryLink'),{'id':'r81-ih-bitter-comp-cat','name':'Company of Bitter Iron — compulsory Immortal','hidden':'true','targetId':BC,'primary':'false'})
if force is not None:
 cl=ET.SubElement(ensure(force,'categoryLinks',G),G('categoryLink'),{'id':'r81-ih-bitter-comp-link','name':'Company of Bitter Iron — compulsory Immortal','hidden':'true','targetId':BC});c=constraint(cl,'r81-ih-bitter-comp-min','min',0,Q=G);m=ET.SubElement(ensure(cl,'modifiers',G),G('modifier'),{'id':'r81-ih-bitter-comp-set','type':'set','value':'1','field':c.get('id')});cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':BITTER,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
# Ferrus unavailable under Bitter Iron
hide_if(fer,'r81-ih-bitter-hide-ferrus',BITTER)
# revisions
cr.set('revision','81');cr.set('gameSystemRevision','48');gr.set('revision','48')
for e in ir.iter(I('dataIndexEntry')):
 if e.get('filePath')=='Legiones Astartes.cat':e.set('dataRevision','81')
 if e.get('filePath')=='Prohammer 30k.gst':e.set('dataRevision','48')
# validation
ids=set();dups=[]
for root in (cr,gr):
 for e in root.iter():
  i=e.get('id')
  if i:
   if i in ids:dups.append(i)
   ids.add(i)
if dups:raise RuntimeError('Duplicate IDs '+str(dups[:20]))
assert not any(l.get('targetId')=='r44-ih-graviton-substitution' for l in cr.iter(C('entryLink')))
assert added_grav>0 and scions>0 and forced_auto>0 and consul_count>0
assert fer.find(C('profiles')) is None
assert len([x for x in fer.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if (x.get('id') or '').startswith('r81-ih-ferrus-')])>=8
ET.indent(ct,space='  ');ET.indent(gt,space='  ');ET.indent(it,space='  ');ct.write(CAT,encoding='utf-8',xml_declaration=True);gt.write(GST,encoding='utf-8',xml_declaration=True);it.write(IDX,encoding='utf-8',xml_declaration=True);ET.parse(CAT);ET.parse(GST);ET.parse(IDX)
OUT.write_text(f'''Revision 81 — Iron Hands live correction\nCAT=81 GST=48\n\nPresentation\n- Scrubbed {cleaned} remaining Iron Hands Source Entry/source-dump nodes and revalidated Autek/Ferrus top-level profile placement.\n\nDangerous Weaponry\n- Removed {removed_grav} old standalone Graviton-substitution links.\n- Added Graviton Gun directly inside {added_grav} existing Special Weapons groups which already contain a Flamer; each costs 15 points and only appears for Iron Hands.\n\nFerrus Manus\n- Added real fixed wargear entries for Medusan Carapace, Forgebreaker, Living Metal Hands, Frag Grenades, Twin-linked Meltagun, Twin-linked Plasma Gun, Heavy Flamer, Cortex Controller and Nuncio Vox.\n- Reasserted Primarch, Legiones Astartes (Iron Hands), The Gorgon, Master of the Forge and Forged for War as distinct rules.\n- Existing Primarch retinue choices remain intact.\n\nRites\n- Head of the Gorgon: Fast Attack max 1; non-Forge Consuls max 1 ({consul_count} Consul upgrades tagged); Blessed Autosimulacra free and compulsory through {forced_auto} existing vehicle links; Scions of Iron rebuilt with {scions} conditional Phobos/Proteus entries which inherit the parent Rhino visibility/capacity logic.\n- Company of Bitter Iron: Loyalist-only visibility; repaired Immortal Troops clone; at least one compulsory Immortal enforced; Ferrus excluded.\n- Battlefield-state and Allied-Detachment restrictions remain explicit rules where New Recruit cannot reliably infer them.\n''',encoding='utf-8');print(OUT.read_text())
