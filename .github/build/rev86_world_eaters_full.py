from pathlib import Path
import re
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml')
OUT=Path('inspection-r86-world-eaters-full.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()
assert cr.get('revision')=='85', cr.get('revision')
assert cr.get('gameSystemRevision')=='51', cr.get('gameSystemRevision')

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t,ns=CNS):
 q=f'{{{ns}}}{t}'; x=p.find(q)
 if x is None:x=ET.SubElement(p,q)
 return x
def set_cost(e,v):
 cs=ensure(e,'costs'); c=next((x for x in cs.findall(C('cost')) if x.get('typeId')=='pts'),None)
 if c is None:c=ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
 else:c.set('value',str(v)); c.set('name','Points')
def add_rule(e,id_,name,text):
 rs=ensure(e,'rules'); old=next((r for r in rs.findall(C('rule')) if r.get('id')==id_),None)
 if old is not None:rs.remove(old)
 r=ET.SubElement(rs,C('rule'),{'id':id_,'name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=text; return r
def add_constraint(e,id_,typ,val,field='selections',scope='parent',children='false',forces='false'):
 cs=ensure(e,'constraints'); old=next((x for x in cs.findall(C('constraint')) if x.get('id')==id_),None)
 if old is not None:cs.remove(old)
 return ET.SubElement(cs,C('constraint'),{'id':id_,'type':typ,'value':str(val),'field':field,'scope':scope,'shared':'true','percentValue':'false','includeChildSelections':children,'includeChildForces':forces})
def add_condition_modifier(e,id_,field,value,conds):
 ms=ensure(e,'modifiers'); old=next((x for x in ms.findall(C('modifier')) if x.get('id')==id_),None)
 if old is not None:ms.remove(old)
 m=ET.SubElement(ms,C('modifier'),{'id':id_,'type':'set','value':str(value),'field':field}); cgs=ET.SubElement(m,C('conditionGroups')); cg=ET.SubElement(cgs,C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(cg,C('conditions'))
 for typ,val,scope,child,cf in conds:
  ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':cf,'scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
 return m
def add_cat(e,id_,target,name):
 cats=ensure(e,'categoryLinks'); old=next((x for x in cats.findall(C('categoryLink')) if x.get('id')==id_),None)
 if old is not None:cats.remove(old)
 ET.SubElement(cats,C('categoryLink'),{'id':id_,'name':name,'hidden':'false','targetId':target,'primary':'false'})
def unit(uid):
 e=byid(cr,uid)
 if e is None:raise RuntimeError('Missing '+uid)
 return e

def additional(e,cost,maxn=None):
 cand=[x for x in e.iter(C('selectionEntry')) if (x.get('name') or '').lower().startswith('additional model')]
 if not cand:return False
 x=cand[0]; set_cost(x,cost)
 if maxn is not None:
  cons=ensure(x,'constraints'); mx=next((c for c in cons.findall(C('constraint')) if c.get('type')=='max' and c.get('field')=='selections'),None)
  if mx is not None:mx.set('value',str(maxn))
 return True

def clean_squadwide_scaling(e,base_count):
 # Old importer charged only the parsed base unit for per-model options. Make the visible base charge correct and add a note so roster totals remain auditable.
 for x in e.iter(C('selectionEntry')):
  nm=x.get('name') or ''
  m=re.search(r'\(base unit; \+([0-9]+) pts/model\)',nm)
  if not m:continue
  pp=int(m.group(1)); set_cost(x,pp*base_count)
  add_rule(x,'r86-scaled-'+x.get('id'),'Per-model cost',f'This upgrade costs +{pp} points per model. The displayed base cost covers the unit\'s starting {base_count} models; add +{pp} points for each additional model selected.')

# ---------- Correct XII Legion unit costs / sizes ----------
# Source values from the current Forces of the Legions document. Devourers explicitly confirmed by the project owner.
fixes={
 'r41-unit-xii-0-rampager-squad':(110,22,5),
 'r41-unit-xii-1-red-butcher-squad':(300,60,5),
 'r41-unit-xii-2-red-hand-destroyer-mortalis-squad':(160,22,5),
 'r41-unit-xii-3-world-eaters-inductii-squad':(130,13,10),
 'r41-unit-xii-4-devourer-terminator-squad':(225,45,5),
 'r41-unit-xii-5-triarii-breacher-squad':(155,27,5),
}
for uid,(base,extra,bc) in fixes.items():
 e=unit(uid); set_cost(e,base); additional(e,extra); clean_squadwide_scaling(e,bc)

# Red Butchers are 0-1.
rb=unit('r41-unit-xii-1-red-butcher-squad'); add_constraint(rb,'r86-red-butcher-unique','max',1,'selections','roster','false','true')

# Fix rite-specific / Rewards of Treachery copies that inherit these units.
name_fix={
 'RAMPAGER SQUAD':(110,22,5),
 'RED BUTCHER SQUAD':(300,60,5),
 'RED HAND DESTROYER MORTALIS SQUAD':(160,22,5),
 'WORLD EATERS INDUCTII SQUAD':(130,13,10),
 'DEVOURER TERMINATOR SQUAD':(225,45,5),
 'TRIARII BREACHER SQUAD':(155,27,5),
}
for e in cr.iter(C('selectionEntry')):
 nm=(e.get('name') or '').upper()
 for key,(base,extra,bc) in name_fix.items():
  if nm==key or nm.startswith(key+' —'):
   set_cost(e,base); additional(e,extra); clean_squadwide_scaling(e,bc)

# Kharn: unique and only legal in games of 1500+ points.
kh=unit('r41-unit-xii-6-kharn-the-bloody'); set_cost(kh,180)
add_constraint(kh,'r86-kharn-1500','min',1500,'limit::points','roster','true','true')
add_rule(kh,'r86-kharn-1500-note','Minimum Game Size','Khârn the Bloody may only be selected in an army with a declared points limit of 1,500 points or greater.')

# ---------- Rites of War ----------
bers=unit('r25-rite-xii-0-berserker-assault'); crimson=unit('r25-rite-xii-1-the-crimson-path')
add_rule(bers,'r86-berserker-full','Berserker Assault — Effects & Limitations',
'''THE RED HAND\nRampager Squads may be selected as Troops choices and may fulfil compulsory Troops selections. Legion Assault Squads may fulfil compulsory Troops selections normally.\n\nHEADLONG ASSAULT\nWorld Eaters Infantry and Jump Infantry units gain Fleet. A unit with Fleet may charge after making an Advance move, following the normal ProHammer rules.\n\nWEAPONS OF THE PITS\nWorld Eaters models in Legion Assault Squads and Rampager Squads may purchase Chainaxes for +2 points per model instead of the normal +4 points.\n\nBLOOD FORWARD\nA non-Vehicle World Eaters unit must declare a charge during its Assault phase if it is normally eligible to charge and at least one enemy unit is within its current charge distance. If more than one legal target is available, the World Eaters player chooses which unit is charged.\n\nLIMITATIONS\nThe army's compulsory Troops choices must be Legion Assault Squads or Rampager Squads. At least one compulsory Troops choice must be a Rampager Squad. The army's Warlord must be equipped with a Chainaxe, Caedere Weapon, Rending Weapon, Power Weapon or another close-combat weapon. The Detachment may include no more than one Heavy Support choice and may not include a Fortification.''')
add_rule(crimson,'r86-crimson-full','The Crimson Path — Effects & Limitations',
'''FORLORN HOPE\nWorld Eaters Infantry models gain Feel No Pain (5+) while within the enemy deployment zone. If a model already possesses Feel No Pain, improve it by one step while it remains within the enemy deployment zone, to a maximum of 3+.\n\nUNTO DEATH\nWorld Eaters Independent Characters gain It Will Not Die while within the enemy deployment zone. If a Character already possesses It Will Not Die, it instead regains a lost Wound on a 4+ while within the enemy deployment zone.\n\nTHE PATH MUST END IN BLOOD\nAt the end of the battle, if the World Eaters have no surviving non-Vehicle unit at least partially within the enemy deployment zone, the opposing player gains +150 Victory Points. If the opposing army has completely destroyed more World Eaters units than the World Eaters have completely destroyed enemy units, the opposing player gains another +150 Victory Points. These penalties only apply in missions using Victory Points.\n\nLIMITATIONS\nThe Detachment may not include units with Slow and Purposeful, Immobile units, Fortifications, or an Allied Detachment drawn from another Space Marine Legion.''')

# Existing Berserker Assault Heavy Support cap: enforce/update it directly in GST.
flh=byid(gr,'fl-heavy'); hmax=byid(gr,'fl-heavy-max')
if flh is None or hmax is None: raise RuntimeError('Heavy Support force link missing')
mods=ensure(flh,'modifiers',GNS)
for x in list(mods):
 if x.get('id') in ('r45-we-berserker-heavy-max','r86-we-berserker-heavy-max'): mods.remove(x)
m=ET.SubElement(mods,G('modifier'),{'id':'r86-we-berserker-heavy-max','type':'set','value':'1','field':'fl-heavy-max'}); cs=ET.SubElement(m,G('conditions')); ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':'r25-rite-xii-0-berserker-assault','shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Make the existing Troops-role Rampager copy unequivocally active only under Berserker Assault and fix its cost.
rite_ramp=byid(cr,'r42-role-xii-0-effects-the-red-hand-rampager-squads-r41-unit-xii-0-rampager-squad')
if rite_ramp is not None:
 set_cost(rite_ramp,110); additional(rite_ramp,22); clean_squadwide_scaling(rite_ramp,5)
 rite_ramp.set('hidden','true')
 add_condition_modifier(rite_ramp,'r86-berserker-rampager-show','hidden','false',[
  ('atLeast',1,'roster','legion-xii','selections'),('atLeast',1,'roster','r25-rite-xii-0-berserker-assault','selections')])

# ---------- Angron, the Red Angel / Daemon Primarch ----------
daemon=unit('r41-unit-xii-13-angron-the-red-angel'); set_cost(daemon,650)
# Remove the unwieldy aggregate source block and replace with discrete builder-readable rules.
rs=ensure(daemon,'rules')
for r in list(rs):
 if (r.get('name') or '').lower().startswith('source entry'): rs.remove(r)
for rid,name,text in [
 ('r86-angron-daemon','Daemon','Angron is a Daemon. He uses the Daemon rules in addition to the special rules listed here.'),
 ('r86-angron-flight','Daemonic Flight','Angron may move up to 12" in the Movement phase and may move over intervening models and terrain. Angron may never join another unit and no model may join him.'),
 ('r86-angron-blades','Blades of the Red Angel','Counts as a pair of Master-crafted Power Weapons. Angron receives the normal +1 Attack for fighting with two close-combat weapons. Against Vehicles, attacks made with the Blades have Armourbane. Against Monstrous Creatures and models with Toughness 6 or greater, Angron may re-roll failed To Wound rolls.'),
 ('r86-angron-blood','Blood Calls to Blood','Angron never begins the battle on the battlefield and does not make normal Reserve rolls. Keep a cumulative total of unsaved Wounds inflicted on enemy models by friendly World Eaters models in close combat. Only Wounds actually suffered count; excess Wounds do not. Shooting and psychic shooting do not contribute. At the end of each World Eaters Assault phase roll to summon Angron: 0–9 Wounds: cannot be summoned; 10–19: 6+; 20–29: 5+; 30–39: 4+; 40–49: 3+; 50+: 2+. If successful, Angron arrives at the beginning of the controlling player’s next turn. If not previously summoned, he automatically arrives at the beginning of Turn 5.'),
 ('r86-angron-descends','The Red Angel Descends','When Angron arrives, deploy him using Deep Strike. He does not scatter. Angron may declare a charge in the same turn he arrives and retains all bonus Attacks and other benefits normally gained for charging.'),
 ('r86-angron-nails','The Nails Sing','While Angron is on the battlefield, all units gain +1 Attack during the first round of a close combat in which they charged. Any unit composed entirely of models wearing Power Armour or Artificer Armour may charge enemies up to 8" away instead of 6". These benefits affect friend and foe alike. World Eaters additionally suffer: Compulsory Charge — if an eligible enemy is within charge distance, the unit must charge the nearest eligible enemy; No Restraint — a World Eaters unit that wins combat must Pursue a Falling Back enemy unless physically or mission-wise impossible; Bloodward Consolidation — if the enemy is destroyed and no Pursuit is possible, Consolidate as directly as possible toward the nearest enemy unit.'),
 ('r86-angron-armour','Daemonic Armour','Angron has the 2+ Armour Save and 4+ Invulnerable Save shown in his profile.'),
 ('r86-angron-restrict','Restrictions','Angron, the Red Angel may only be selected in a World Eaters army. An army may not include both Angron, the Red Angel and Angron in his mortal form.'),
]: add_rule(daemon,rid,name,text)

# Add the standard core special rules as discrete reminders, not one source paragraph.
for n in ('Fear','Fearless','Fleet','Furious Charge','Eternal Warrior','Adamantium Will','Master of the Legion'):
 add_rule(daemon,'r86-angron-core-'+re.sub('[^a-z0-9]+','-',n.lower()),n,f'Angron, the Red Angel has the {n} special rule.')

# Explicitly gate Daemon Angron to World Eaters and prevent both forms in the same roster even outside normal LoW limits.
daemon.set('hidden','true')
add_condition_modifier(daemon,'r86-angron-daemon-show','hidden','false',[('atLeast',1,'roster','legion-xii','selections')])
# Mutual exclusion via roster selection modifiers.
add_condition_modifier(daemon,'r86-angron-daemon-hide-mortal','hidden','true',[('atLeast',1,'roster','r41-unit-xii-12-xii-angron-the-red-angel','selections')])
mortal=unit('r41-unit-xii-12-xii-angron-the-red-angel')
add_condition_modifier(mortal,'r86-angron-mortal-hide-daemon','hidden','true',[('atLeast',1,'roster','r41-unit-xii-13-angron-the-red-angel','selections')])

# Remove duplicate old 1500 selection-count style errors anywhere in XII named characters if present.
for e in [unit(f'r41-unit-xii-{i}-'+s) for i,s in [(6,'kharn-the-bloody'),(7,'shabran-darr'),(8,'gahlan-surlak'),(9,'kargos-the-bloodspitter'),(10,'captain-ehrlen'),(11,'delvarus')]]:
 cons=e.find(C('constraints'))
 if cons is None:continue
 for c in list(cons):
  if c.get('field')=='selections' and c.get('value') in ('1500','1500.0'):cons.remove(c)

# Revisions
cr.set('revision','86'); ct.write(CAT,encoding='utf-8',xml_declaration=True); gt.write(GST,encoding='utf-8',xml_declaration=True)
# canonical namespace cleanup
for p,ns,tag in [(CAT,CNS,'catalogue'),(GST,GNS,'gameSystem')]:
 text=p.read_text(encoding='utf-8')
 text=text.replace(f'xmlns:ns0="{ns}"',f'xmlns="{ns}"').replace('<ns0:','<').replace('</ns0:','</')
 p.write_text(text,encoding='utf-8')
idx=IDX.read_text(encoding='utf-8'); idx,n=re.subn(r'(filePath="Legiones Astartes\.cat"[^>]*dataRevision=")85(" )',r'\g<1>86\g<2>',idx,count=1)
if n!=1: raise RuntimeError('index revision bump failed')
IDX.write_text(idx,encoding='utf-8')

# Final validation
rr=ET.parse(CAT).getroot(); assert rr.get('revision')=='86'; assert rr.get('gameSystemRevision')=='51'
for uid,(base,extra,bc) in fixes.items():
 e=byid(rr,uid); pts=next(c for c in e.findall('./'+C('costs')+'/'+C('cost')) if c.get('typeId')=='pts'); assert float(pts.get('value'))==base
 a=[x for x in e.iter(C('selectionEntry')) if (x.get('name') or '').lower().startswith('additional model')]
 assert a, uid+' no additional model'; ap=next(c for c in a[0].findall('./'+C('costs')+'/'+C('cost')) if c.get('typeId')=='pts'); assert float(ap.get('value'))==extra
kh=byid(rr,'r41-unit-xii-6-kharn-the-bloody'); assert any(c.get('field','').lower()=='limit::points' and c.get('type')=='min' and c.get('value') in ('1500','1500.0') for c in kh.findall('./'+C('constraints')+'/'+C('constraint')))
daemon=byid(rr,'r41-unit-xii-13-angron-the-red-angel'); assert len([r for r in daemon.findall('./'+C('rules')+'/'+C('rule'))])>=10
OUT.write_text('Revision 86 — World Eaters full implementation\nCAT=86 GSTref=51\n\nFixed base/additional costs:\n- Rampagers 110 +22/model\n- Red Butchers 300 +60/model, 0-1\n- Red Hand Destroyers 160 +22/model\n- Inductii 130 +13/model\n- Devourers 225 +45/model\n- Triarii 155 +27/model\n\nKharn:\n- 180 points\n- proper roster Points Limit minimum 1500\n\nRites of War:\n- Berserker Assault complete rules text; Rampager Troops copy corrected; Heavy Support max 1 enforced\n- Crimson Path complete rules text and limitations\n\nAngron, the Red Angel:\n- 650 points\n- aggregate import block replaced by discrete rules\n- World Eaters-only visibility\n- mortal/daemon forms mutually exclusive\n- full Blood Calls to Blood summoning table, Deep Strike/charge arrival, Daemonic Flight, Blades and The Nails Sing included\n',encoding='utf-8')
print(OUT.read_text())
