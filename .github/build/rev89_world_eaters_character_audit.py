from pathlib import Path
import re, xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); IDX=Path('index.xml'); OUT=Path('inspection-r89-world-eaters-character-audit.txt')
NS='http://www.battlescribe.net/schema/catalogueSchema'; ET.register_namespace('',NS); C=lambda t:f'{{{NS}}}{t}'
ct=ET.parse(CAT); root=ct.getroot()
if root.get('revision')!='88' or root.get('gameSystemRevision')!='51':
    raise RuntimeError(f'Expected CAT88/GSTref51, got CAT{root.get("revision")}/GSTref{root.get("gameSystemRevision")}')

def byid(i): return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t):
    x=p.find(C(t))
    if x is None:x=ET.SubElement(p,C(t))
    return x
def wipe(p,t):
    x=p.find(C(t))
    if x is not None:p.remove(x)
def norm(s): return re.sub(r'\s+',' ',(s or '').strip()).lower()
def slug(s): return re.sub(r'[^a-z0-9]+','-',norm(s)).strip('-')
def setpts(e,v):
    cs=ensure(e,'costs')
    for x in list(cs): cs.remove(x)
    ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def constraint(e,id_,typ,val,field='selections',scope='parent',children=True):
    return ET.SubElement(ensure(e,'constraints'),C('constraint'),{'id':id_,'type':typ,'value':str(val),'field':field,'scope':scope,'shared':'true','percentValue':'false','includeChildSelections':'true' if children else 'false','includeChildForces':'false'})
def add_rule(e,id_,name,text):
    r=ET.SubElement(ensure(e,'rules'),C('rule'),{'id':id_,'name':name,'hidden':'false'});ET.SubElement(r,C('description')).text=text;return r
def add_entry(parent,id_,name,cost=0,default=None,minv=None,maxv=1,rule=None):
    e=ET.SubElement(ensure(parent,'selectionEntries'),C('selectionEntry'),{'id':id_,'name':name,'type':'upgrade','hidden':'false','import':'true',**({'defaultAmount':str(default)} if default is not None else {})})
    setpts(e,cost)
    if minv is not None:constraint(e,id_+'-min','min',minv)
    if maxv is not None:constraint(e,id_+'-max','max',maxv)
    if rule:add_rule(e,id_+'-rule',name,rule)
    return e
def group(parent,id_,name,minv=None,maxv=None):
    g=ET.SubElement(ensure(parent,'selectionEntryGroups'),C('selectionEntryGroup'),{'id':id_,'name':name,'hidden':'false','collective':'false','import':'true'})
    if minv is not None:constraint(g,id_+'-min','min',minv,children=True)
    if maxv is not None:constraint(g,id_+'-max','max',maxv,children=True)
    return g
def locked_group(parent,pfx,name,items):
    g=group(parent,pfx+'-'+slug(name),name)
    for idx,(nm,desc) in enumerate(items):
        add_entry(g,f'{pfx}-{slug(name)}-{idx}-{slug(nm)}',nm,0,1,1,1,desc or None)
    return g
def option_group(parent,pfx,items):
    g=group(parent,pfx+'-options','Options')
    for idx,(nm,cost,desc) in enumerate(items):add_entry(g,f'{pfx}-opt-{idx}-{slug(nm)}',nm,cost,None,None,1,desc or None)
    return g
def choice_group(parent,pfx,name,items):
    g=group(parent,pfx+'-'+slug(name),name,1,1)
    out=[]
    for idx,(nm,cost,default,desc) in enumerate(items):out.append(add_entry(g,f'{pfx}-{slug(name)}-{idx}-{slug(nm)}',nm,cost,1 if default else None,None,1,desc or None))
    return g,out
def remove_prefix(node,pfx):
    for p in list(node.iter()):
        for x in list(p):
            if (x.get('id') or '').startswith(pfx):p.remove(x)
def remove_named_groups(u,names):
    box=u.find(C('selectionEntryGroups'))
    if box is None:return
    for g in list(box):
        if norm(g.get('name')) in {norm(x) for x in names}:box.remove(g)
def remove_source_artifacts(u):
    removed=[]
    def blob(s):
        lo=norm(s);return sum(k in lo for k in ('force organisation:','unit type:','wargear:','special rules:'))>=3
    changed=True
    while changed:
        changed=False; pm={c:p for p in u.iter() for c in p}
        for x in list(u.iter()):
            if x is u:continue
            tag=x.tag.split('}')[-1]
            if tag not in ('rule','profile','infoLink'):continue
            nm=norm(x.get('name'));tx=' '.join((z.text or '').strip() for z in x.iter() if (z.text or '').strip())
            if nm.startswith('source entry') or blob(tx):
                p=pm.get(x)
                if p is not None:p.remove(x);removed.append((tag,x.get('id'),x.get('name')));changed=True;break
    return removed
def remove_direct_rules(u): wipe(u,'rules')
def direct_profile(u):
    ps=u.find(C('profiles'))
    if ps is None:return None
    return next((p for p in ps.findall(C('profile')) if p.get('typeId')=='prof-model'),None)
def set_model_profile(u,name,vals):
    ps=ensure(u,'profiles'); profs=[p for p in ps.findall(C('profile')) if p.get('typeId')=='prof-model']
    p=profs[0] if profs else ET.SubElement(ps,C('profile'),{'id':'r89-we-'+slug(name)+'-profile','name':name,'typeId':'prof-model','typeName':'Model','hidden':'false'})
    for extra in profs[1:]: ps.remove(extra)
    p.set('name',name);p.set('hidden','false')
    chars=p.find(C('characteristics'))
    if chars is not None:p.remove(chars)
    chars=ET.SubElement(p,C('characteristics'))
    tids={'WS':'model-ws','BS':'model-bs','S':'model-s','T':'model-t','W':'model-w','I':'model-i','A':'model-a','Ld':'model-ld','Sv':'model-sv'}
    for k,v in zip(('WS','BS','S','T','W','I','A','Ld','Sv'),vals): ET.SubElement(chars,C('characteristic'),{'name':k,'typeId':tids[k]}).text=str(v)
    return p
def unique_max1(u,pfx):
    cs=ensure(u,'constraints')
    # remove malformed / duplicate roster max constraints, retain unrelated min game-size gates
    for c in list(cs):
        if c.get('field')=='selections' and c.get('scope')=='roster' and c.get('type')=='max':cs.remove(c)
    constraint(u,pfx+'-unique','max',1,'selections','roster',True)
def hide_unless(u,id_,selector):
    mods=ensure(u,'modifiers');m=ET.SubElement(mods,C('modifier'),{'id':id_,'type':'set','field':'hidden','value':'true'});conds=ET.SubElement(m,C('conditions'));ET.SubElement(conds,C('condition'),{'type':'lessThan','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def hide_if(u,id_,selector):
    mods=ensure(u,'modifiers');m=ET.SubElement(mods,C('modifier'),{'id':id_,'type':'set','field':'hidden','value':'true'});conds=ET.SubElement(m,C('conditions'));ET.SubElement(conds,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_ranged_profile(e,id_,name,rng,s,ap,typ):
    p=ET.SubElement(ensure(e,'profiles'),C('profile'),{'id':id_,'name':name,'hidden':'false','typeId':'prof-ranged','typeName':'Ranged Weapon'});cs=ET.SubElement(p,C('characteristics'))
    for n,tid,v in [('Range','ranged-range',rng),('S','ranged-s',s),('AP','ranged-ap',ap),('Type','ranged-type',typ)]:ET.SubElement(cs,C('characteristic'),{'name':n,'typeId':tid}).text=str(v)
    return p

IDS={
 'kharn':'r41-unit-xii-6-kharn-the-bloody','darr':'r41-unit-xii-7-shabran-darr','surlak':'r41-unit-xii-8-gahlan-surlak','kargos':'r41-unit-xii-9-kargos-the-bloodspitter','ehrlen':'r41-unit-xii-10-captain-ehrlen','delvarus':'r41-unit-xii-11-delvarus','angron':'r41-unit-xii-12-xii-angron-the-red-angel','daemon':'r41-unit-xii-13-angron-the-red-angel'}
U={k:byid(v) for k,v in IDS.items()}
if any(v is None for v in U.values()):raise RuntimeError('Missing World Eaters character(s): '+', '.join(k for k,v in U.items() if v is None))

# Source-confirmed points/profiles.
DATA={
 'kharn':(180,'Khârn',(6,5,4,4,3,5,4,9,'2+/4+')),
 'darr':(150,'Shabran Darr',(6,5,4,4,3,5,3,10,'2+/5+')),
 'surlak':(125,'Gahlan Surlak',(5,5,4,4,2,4,2,9,'3+/5+')),
 'kargos':(120,'Kargos',(5,4,4,4,3,5,3,9,'3+')),
 'ehrlen':(95,'Captain Ehrlen',(5,5,4,4,2,5,3,9,'3+/5+')),
 'delvarus':(120,'Delvarus',(5,4,4,4,2,5,3,9,'3+')),
 'angron':(515,'Angron',(9,6,7,6,6,7,6,10,'1+')),
 'daemon':(650,'Angron, the Red Angel',(9,5,8,7,8,7,8,10,'2+/4++')),
}
removed=[]
for k,u in U.items():
    removed += [(k,)+r for r in remove_source_artifacts(u)]
    # Old R87 display groups are replaced wholesale with one authoritative package.
    remove_prefix(u,'r87-we-'); remove_prefix(u,'r89-we-')
    remove_named_groups(u,('Wargear','Special Rules','Options','Weapon','Primary Weapon','Restrictions'))
    remove_direct_rules(u)
    pts,pname,stats=DATA[k];setpts(u,pts);set_model_profile(u,pname,stats);unique_max1(u,'r89-we-'+k)

# Common rule text.
LEG='Uses the World Eaters Legion special rule.'
IC='Uses the normal Independent Character rules.'

# KHARN — base weapon is The Cutter; Gorechild is an OPTION, not fixed gear.
u=U['kharn'];pfx='r89-we-kharn'
locked_group(u,pfx,'Wargear',[('Artificer Armour','Confers a 2+ Armour Save.'),('Iron Halo','Confers a 4+ Invulnerable Save.'),('Plasma pistol','Uses the normal Plasma pistol profile.'),('Frag grenades','Uses the normal Frag grenade rules.')])
wg,choices=choice_group(u,pfx,'Weapon',[('The Cutter',0,True,'The Cutter is a Power Weapon which grants Khârn +1 Strength.'),('Gorechild',55,False,'Gorechild is a Master-crafted Power Weapon which grants Khârn +3 Strength. At the beginning of the first round of each close combat, roll a D3. Khârn gains that many additional Attacks for that round.')])
gore=choices[1]
locked_group(u,pfx,'Special Rules',[('Legiones Astartes (World Eaters)',LEG),('Independent Character',IC),('Master of the Legion','Uses the normal Master of the Legion rule.'),('The Bloody','Whenever Khârn rolls a natural 1 To Hit in close combat, that attack instead hits the nearest friendly model within 6 inches. If several friendly models are equally close, the opposing player chooses which is hit. Resolve the hit using Khârn’s current Strength and the weapon being used. The friendly model may take any saves normally permitted. Wounds caused in this manner do not count towards the close-combat result. If no friendly model is within 6 inches, the roll of 1 is a miss.'),('Command Retinue','Khârn may select one Legion Command Squad or Rampager Squad as his retinue. The selected unit does not occupy a separate Force Organisation slot.')])
option_group(u,pfx,[('Krak grenades',2,''),('Jump Pack',20,'Changes Khârn to Jump Infantry while equipped.')])
# Gorechild may only be selected if mortal Angron is not using Gorefather & Gorechild; the actual Angron weapon child is added below and linked afterwards.

# SHABRAN DARR
u=U['darr'];pfx='r89-we-darr'
locked_group(u,pfx,'Wargear',[('Artificer Armour','Confers a 2+ Armour Save.'),('Refractor Field','Confers a 5+ Invulnerable Save.'),('Two Bolt pistols','Darr carries two Bolt pistols.'),('Power Weapon','Uses the normal Power Weapon rules.'),('Frag grenades','Uses the normal Frag grenade rules.'),('Rad grenades','Uses the normal Rad grenade rules.')])
locked_group(u,pfx,'Special Rules',[('Legiones Astartes (World Eaters)',LEG),('Independent Character',IC),('Stubborn','Uses the normal Stubborn rule.'),('Dual Pistols','Darr is equipped with two Bolt pistols as listed in his wargear.'),('Master of Destroyers','Shabran Darr may join Legion Destroyer Squads and Red Hand Destroyer Squads despite the normal restrictions imposed by Destroyer Cadre. Darr may select one Red Hand Destroyer Mortalis or Assault Squad as his retinue. The selected squad does not occupy a separate Force Organisation slot.'),('Loyalist Only','Shabran Darr may only be selected in a Loyalist army.')])
option_group(u,pfx,[('Krak grenades',2,''),('Melta bombs',5,'Uses the normal Melta bomb rules.')])

# GAHLAN SURLAK
u=U['surlak'];pfx='r89-we-surlak'
locked_group(u,pfx,'Wargear',[('Power Armour','Confers a 3+ Armour Save.'),('Refractor Field','Confers a 5+ Invulnerable Save.'),('Narthecium','Uses the normal Narthecium rules.'),('Reductor','Uses the normal Reductor rules.'),('Bolt pistol','Uses the normal Bolt pistol profile.'),('Chainsword','Counts as a close-combat weapon.'),('Frag grenades','Uses the normal Frag grenade rules.')])
locked_group(u,pfx,'Special Rules',[('Legiones Astartes (World Eaters)',LEG),('Independent Character',IC),('Apothecary','Uses the normal Apothecary rules.'),('Architect of the Nails','After deployment but before the first turn begins, nominate one friendly World Eaters Infantry unit which is not wearing any form of Terminator Armour. That unit gains Furious Charge for the duration of the battle. A unit enhanced in this manner must declare a charge whenever it is legally able to do so. Only one unit may be enhanced in this manner.'),('Legion Support Officer','Uses the normal Legion Support Officer rule.')])
option_group(u,pfx,[('Krak grenades',2,'')])

# KARGOS
u=U['kargos'];pfx='r89-we-kargos'
locked_group(u,pfx,'Wargear',[('Power Armour','Confers a 3+ Armour Save.'),('Narthecium','Uses the normal Narthecium rules.'),('Reductor','Uses the normal Reductor rules.'),('Chainaxe','An Armour Save better than 4+ is reduced to 4+ against wounds caused by a Chainaxe. Invulnerable Saves are unaffected.'),('Bolt pistol','Uses the normal Bolt pistol profile.'),('Frag grenades','Uses the normal Frag grenade rules.')])
locked_group(u,pfx,'Special Rules',[('Legiones Astartes (World Eaters)',LEG),('Independent Character',IC),('Apothecary','Uses the normal Apothecary rules.'),('Warrior-Apothecary','Kargos may use his Narthecium even while he is in base contact with an enemy model. All other normal Narthecium restrictions continue to apply.'),('Command Retinue','Kargos may select one Legion Command Squad. If Kargos has a Jump Pack, the Command Squad may purchase Jump Packs normally. The selected squad does not occupy a separate Force Organisation slot.')])
option_group(u,pfx,[('Krak grenades',2,''),('Melta bombs',5,'Uses the normal Melta bomb rules.'),('Jump Pack',20,'Changes Kargos to Jump Infantry while equipped.')])

# CAPTAIN EHRLEN
u=U['ehrlen'];pfx='r89-we-ehrlen'
locked_group(u,pfx,'Wargear',[('Power Armour','Confers a 3+ Armour Save.'),('Refractor Field','Confers a 5+ Invulnerable Save.'),('Jump Pack','Ehrlen is Jump Infantry.'),('Rending Weapon','Uses the project Rending Weapon rules.'),('Bolt pistol','Uses the normal Bolt pistol profile.'),('Bionics','Uses the normal Bionics rules.'),('Frag grenades','Uses the normal Frag grenade rules.')])
locked_group(u,pfx,'Special Rules',[('Legiones Astartes (World Eaters)',LEG),('Independent Character',IC),('Loyalist Only','Captain Ehrlen may only be selected in a Loyalist army.'),('Command Retinue','Ehrlen may select one Legion Command Squad as his retinue. Every model in the Command Squad may purchase a Jump Pack for +15 points per model. If Jump Packs are purchased, every model in the squad must receive one and the squad may not select a Dedicated Transport. This Command Squad does not occupy a separate Force Organisation slot.')])
option_group(u,pfx,[('Krak grenades',2,''),('Melta bombs',5,'Uses the normal Melta bomb rules.')])

# DELVARUS
u=U['delvarus'];pfx='r89-we-delvarus'
locked_group(u,pfx,'Wargear',[('Power Armour','Confers a 3+ Armour Save.'),('Caedere Weapon','A Caedere Weapon is a one-handed close-combat weapon at User +1 Strength with Rending. It does not count as a Power Weapon.'),('Bolt pistol','Uses the normal Bolt pistol profile.'),('Boarding Shield','Uses the normal Boarding Shield rules.'),('Frag grenades','Uses the normal Frag grenade rules.')])
locked_group(u,pfx,'Special Rules',[('Legiones Astartes (World Eaters)',LEG),('Independent Character',IC),('Gladiator Champion','Any Triarii Breacher Squad joined by Delvarus gains Stubborn and Furious Charge.'),('Command Retinue','Delvarus may select one Legion Triarii Breacher Squad as his retinue. The selected squad does not occupy a separate Force Organisation slot.')])
# The source mistakenly labels this line “Kargos may take” beneath Delvarus; the listed upgrades are retained as Delvarus options by context.
option_group(u,pfx,[('Krak grenades',2,''),('Melta bombs',5,'Uses the normal Melta bomb rules.')])

# MORTAL ANGRON — clean, source-complete, with actual weapon choice and Spite Furnace profile.
u=U['angron'];pfx='r89-we-angron'
locked_group(u,pfx,'Wargear',[('Armour of Mars','The Armour of Mars counts as Primarch Armour.'),('Frag Grenades','Uses the normal Frag grenade rules.')])
wg,ang_weps=choice_group(u,pfx,'Weapon',[('Gorefather & Gorechild',0,True,'Gorefather and Gorechild are a matched pair of Power Weapons. Attacks made with them are resolved at +1 Strength and have Shred and Armourbane. They count as two close-combat weapons.'),('Widowmaker',0,False,'Widowmaker is a Two-Handed Power Weapon. Attacks made with Widowmaker are resolved at Strength 10 and have Armourbane. All attacks made with Widowmaker are resolved at -2 Initiative.')])
sp=add_entry(ensure(u,'selectionEntryGroups') if False else u,pfx+'-spite-furnace','Spite Furnace',0,1,1,1,'A brutal plasma weapon carried by Angron into the thickest fighting.')
# Move Spite Furnace into a dedicated Wargear entry group rather than leaving it loose.
# Remove the temporary loose node and add it cleanly to the existing Wargear group.
se=u.find(C('selectionEntries')); se.remove(sp)
wggrp=next(g for g in u.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')) if g.get('id')==pfx+'-wargear')
sp=add_entry(wggrp,pfx+'-spite-furnace','Spite Furnace',0,1,1,1,'A brutal plasma weapon carried by Angron into the thickest fighting.')
add_ranged_profile(sp,pfx+'-spite-profile','Spite Furnace','12"','7','2','Pistol, Gets Hot, Master-crafted')
locked_group(u,pfx,'Special Rules',[('Primarch','Angron uses the universal Primarch rules.'),('Legiones Astartes (World Eaters)',LEG),('The Red Angel','If Angron is able to declare a charge during the Assault phase, he must do so. Angron and any unit he has joined may declare charges against enemy units up to 8 inches away instead of 6. They must charge the closest eligible enemy unit to Angron; if two or more are equally close, the World Eaters player chooses. Difficult Terrain does not reduce this charge distance, although Dangerous Terrain is resolved normally.'),('Butcher’s Nails','Angron has Furious Charge and may never voluntarily Withdraw from close combat. Whenever Angron rolls an unmodified 1 To Hit in close combat, that attack instead strikes another friendly model in Angron’s unit. The roll of 1 may not be re-rolled. Resolve the hit using Angron’s current Strength and all rules of the close-combat weapon he is using. If more than one eligible friendly model is present, the opposing player chooses which is struck. Saves are allowed normally and Wounds caused this way do not count toward the close-combat result. If Angron is not accompanied by another friendly model, the roll of 1 is a miss.'),('Sire of the World Eaters','Friendly World Eaters units with at least one model within 12 inches of Angron add +1 to all Pursuit rolls. Such units may also re-roll failed Break Tests caused by losing close combat; the second result must be accepted.'),('The Nails Demand Blood','Each time an enemy unit is completely destroyed during an Assault phase in a close combat involving Angron, increase Angron’s Attacks characteristic by +1 for the remainder of the battle, cumulative to a maximum of +3 Attacks.'),('Primarch Retinue','Angron may select one Legion Honour Guard Squad, Legion Terminator Command Squad or Devourer Terminator Squad as his Primarch Retinue. It does not occupy an additional Force Organisation selection and follows the normal Primarch Retinue rules.')])

# Now that mortal Angron's weapon child exists, enforce Kharn's Gorechild restriction as written.
ang_gore=ang_weps[0]
mods=ensure(gore,'modifiers');m=ET.SubElement(mods,C('modifier'),{'id':'r89-we-kharn-gorechild-angron-lock','type':'set','field':'hidden','value':'true'});conds=ET.SubElement(m,C('conditions'));ET.SubElement(conds,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':ang_gore.get('id'),'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# DAEMON ANGRON — every listed special rule has a real tooltip.
u=U['daemon'];pfx='r89-we-daemon-angron'
locked_group(u,pfx,'Wargear',[('Blades of the Red Angel','The Blades count as a pair of Master-crafted Power Weapons. Angron receives the normal +1 Attack for two close-combat weapons. Against Vehicles they have Armourbane. Against Monstrous Creatures and models with Toughness 6 or greater, Angron may re-roll failed To Wound rolls.'),('Daemonic Armour','Angron has a 2+ Armour Save and a 4+ Invulnerable Save.')])
locked_group(u,pfx,'Special Rules',[('Daemon','Uses the normal Daemon rule.'),('Fear','Uses the normal Fear rule.'),('Fearless','Uses the normal Fearless rule.'),('Fleet','Uses the normal Fleet rule.'),('Furious Charge','Uses the normal Furious Charge rule.'),('Eternal Warrior','Uses the normal Eternal Warrior rule.'),('Adamantium Will','Uses the normal Adamantium Will rule.'),('Master of the Legion','Uses the normal Master of the Legion rule.'),('Daemonic Flight','Angron may move up to 12 inches during the Movement phase and may move over intervening models and terrain while doing so. Angron may never join another unit and no model may join him.'),('Blood Calls to Blood','Angron may never begin the battle on the battlefield and does not make normal Reserve rolls. Keep a cumulative total of unsaved Wounds inflicted on enemy models by friendly World Eaters models in close combat; only Wounds actually suffered count, and shooting or psychic shooting Wounds do not contribute. At the end of each World Eaters Assault phase roll to summon him: 0–9 Wounds: cannot be summoned; 10–19: 6+; 20–29: 5+; 30–39: 4+; 40–49: 3+; 50+: 2+. If successful, Angron arrives at the beginning of the controlling player’s next turn. If not previously summoned, he automatically arrives at the beginning of Turn 5.'),('The Red Angel Descends','When Angron arrives, deploy him using Deep Strike. He does not scatter and may declare a charge during the same turn in which he arrives. He retains all bonus Attacks and other benefits normally gained for charging.'),('The Nails Sing','While Angron is on the battlefield, all units gain +1 Attack during the first round of a close combat in which they charged. Units composed entirely of models in Power Armour or Artificer Armour may declare charges up to 8 inches away instead of 6. These benefits affect friend and foe alike. World Eaters must charge the nearest eligible enemy if one is within charge distance; a World Eaters unit that wins combat must Pursue an enemy that Falls Back unless physically or mission-wise impossible; if the enemy is destroyed and no Pursuit is possible, the World Eaters unit must Consolidate as directly as possible towards the nearest enemy. The Attack from The Nails Sing is cumulative with the normal charge bonus and World Eaters Blood Frenzy.')])
locked_group(u,pfx,'Restrictions',[('World Eaters Only','Angron, the Red Angel may only be selected for a World Eaters army.'),('One Form of Angron','An army may not include both Angron, the Red Angel and Angron in his mortal form.')])

# Functional legion / allegiance visibility and mutual exclusion. Existing legacy modifiers are left intact; these are explicit regression guards.
for k,u in U.items():hide_unless(u,'r89-we-'+k+'-legion','legion-xii')
for k in ('darr','ehrlen'):hide_unless(U[k],'r89-we-'+k+'-loyal','allegiance-loyalist')
hide_if(U['angron'],'r89-we-angron-hide-daemon',IDS['daemon']);hide_if(U['daemon'],'r89-we-daemon-hide-mortal',IDS['angron'])

# Kharn minimum game size: enforce 1500+ as a points LIMIT gate, never a 1/1500 selection ratio.
kh=U['kharn'];cs=ensure(kh,'constraints')
for c in list(cs):
    if c.get('id')=='r79-we-kharn-1500' or (c.get('value') in ('1500','1500.0') and c.get('field')=='selections'):cs.remove(c)
if not any(c.get('field','').lower()=='limit::points' and c.get('scope')=='roster' and c.get('type')=='min' and c.get('value') in ('1500','1500.0') for c in cs.findall(C('constraint'))):
    constraint(kh,'r89-we-kharn-1500','min',1500,'limit::points','roster',True)

# HARD VALIDATION across EVERY World Eaters named character / Primarch.
def source_blob(x):
    nm=norm(x.get('name'));tx=' '.join((z.text or '').strip() for z in x.iter() if (z.text or '').strip());lo=norm(tx)
    return nm.startswith('source entry') or sum(k in lo for k in ('force organisation:','unit type:','wargear:','special rules:'))>=3
report=[]
for k,u in U.items():
    pts,pname,stats=DATA[k]
    cost=next(c for c in u.findall('./'+C('costs')+'/'+C('cost')) if c.get('typeId')=='pts')
    assert float(cost.get('value'))==pts,(k,cost.get('value'),pts)
    assert not any(source_blob(x) for x in u.iter() if x is not u),f'{k}: aggregate Source Entry remains'
    grps=[norm(g.get('name')) for g in u.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup'))]
    assert grps.count('wargear')==1,(k,grps);assert grps.count('special rules')==1,(k,grps)
    # exactly one user-facing Options group where options exist
    should_opts=k in ('kharn','darr','surlak','kargos','ehrlen','delvarus')
    assert grps.count('options')==(1 if should_opts else 0),(k,grps)
    # unique named character cap
    assert any(c.get('field')=='selections' and c.get('scope')=='roster' and c.get('type')=='max' and c.get('value') in ('1','1.0') for c in u.findall('./'+C('constraints')+'/'+C('constraint'))),k
    report.append(f'{pname}: {pts} pts | Wargear OK | Special Rules OK | Options '+('OK' if should_opts else 'n/a')+' | Source dump NONE')
assert any((x.get('name') or '')=='The Cutter' for x in U['kharn'].iter(C('selectionEntry')))
assert any((x.get('name') or '')=='Gorechild' and float(next(c for c in x.findall('./'+C('costs')+'/'+C('cost')) if c.get('typeId')=='pts').get('value'))==55 for x in U['kharn'].iter(C('selectionEntry')))
assert any((x.get('name') or '')=='Stubborn' for x in U['darr'].iter(C('selectionEntry')))
assert any((x.get('name') or '')=='Dual Pistols' for x in U['darr'].iter(C('selectionEntry')))
assert any((x.get('name') or '')=='Spite Furnace' for x in U['angron'].iter(C('selectionEntry')))
assert any((p.get('name') or '')=='Spite Furnace' for p in U['angron'].iter(C('profile')))
for nm in ('Daemon','Fear','Fearless','Fleet','Furious Charge','Eternal Warrior','Adamantium Will','Master of the Legion','Daemonic Flight','Blood Calls to Blood','The Red Angel Descends','The Nails Sing'):
    assert any((x.get('name') or '')==nm for x in U['daemon'].iter(C('selectionEntry'))),('daemon tooltip missing',nm)

root.set('revision','89');ct.write(CAT,encoding='utf-8',xml_declaration=True)
raw=CAT.read_text(encoding='utf-8').replace(f'xmlns:ns0="{NS}"',f'xmlns="{NS}"').replace('<ns0:','<').replace('</ns0:','</')
if '<ns0:' in raw:raise RuntimeError('namespace prefix survived')
CAT.write_text(raw,encoding='utf-8')
idx=IDX.read_text(encoding='utf-8');idx,n=re.subn(r'(filePath="Legiones Astartes\.cat"[^>]*dataRevision=")88(" )',r'\g<1>89\g<2>',idx,count=1)
if n!=1:raise RuntimeError('index bump 88 -> 89 failed')
IDX.write_text(idx,encoding='utf-8')
OUT.write_text('Revision 89 — World Eaters named-character audit\nCAT=89 GSTref=51\n\n'+'\n'.join(report)+'\n\nLegacy source artifacts removed during this pass: '+str(len(removed))+'\nKharn: restored The Cutter as base weapon; Gorechild is +55 option and is blocked while mortal Angron uses Gorefather & Gorechild.\nShabran Darr: restored full wargear, Stubborn, Dual Pistols, Master of Destroyers and Loyalist-only presentation.\nAll six HQ characters plus mortal Angron and Daemon Angron now use one clean Wargear group and one clean Special Rules group.\nDaemon Angron: every listed special rule has an individual tooltip.\n',encoding='utf-8')
print(OUT.read_text(encoding='utf-8'))
