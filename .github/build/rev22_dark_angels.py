import xml.etree.ElementTree as ET
from copy import deepcopy
from collections import Counter

CAT='Legiones Astartes.cat'
NS='http://www.battlescribe.net/schema/catalogueSchema'
ET.register_namespace('',NS)
q=lambda t:f'{{{NS}}}{t}'
tree=ET.parse(CAT); root=tree.getroot()

def sec(p,tag):
    e=p.find(q(tag))
    if e is None: e=ET.SubElement(p,q(tag))
    return e

def byid(i):
    return next((e for e in root.iter() if e.get('id')==i),None)

def cost(p,v):
    cs=sec(p,'costs')
    ET.SubElement(cs,q('cost'),{'name':'Points','typeId':'pts','value':str(v)})

def constraint(p,cid,typ,val,scope='parent',field='selections',include='true'):
    cs=sec(p,'constraints')
    return ET.SubElement(cs,q('constraint'),{'id':cid,'field':field,'scope':scope,'value':str(val),'percentValue':'false','shared':'true','includeChildSelections':include,'includeChildForces':'false','type':typ})

def rule(p,rid,name,text):
    rs=sec(p,'rules'); r=ET.SubElement(rs,q('rule'),{'name':name,'id':rid,'hidden':'false'})
    ET.SubElement(r,q('description')).text=text
    return r

def profile(p,pid,name,ws,bs,s,t,w,i,a,ld,sv):
    ps=sec(p,'profiles'); pr=ET.SubElement(ps,q('profile'),{'name':name,'typeId':'prof-model','typeName':'Model','hidden':'false','id':pid})
    ch=ET.SubElement(pr,q('characteristics'))
    for n,tid,v in [('WS','model-ws',ws),('BS','model-bs',bs),('S','model-s',s),('T','model-t',t),('W','model-w',w),('I','model-i',i),('A','model-a',a),('Ld','model-ld',ld),('Sv','model-sv',sv)]:
        ET.SubElement(ch,q('characteristic'),{'name':n,'typeId':tid}).text=str(v)
    return pr

def ranged(p,pid,name,rng,s,ap,typ):
    ps=sec(p,'profiles'); pr=ET.SubElement(ps,q('profile'),{'name':name,'typeId':'prof-ranged','typeName':'Ranged Weapon','hidden':'false','id':pid})
    ch=ET.SubElement(pr,q('characteristics'))
    for n,tid,v in [('Range','ranged-range',rng),('S','ranged-s',s),('AP','ranged-ap',ap),('Type','ranged-type',typ)]:
        ET.SubElement(ch,q('characteristic'),{'name':n,'typeId':tid}).text=str(v)
    return pr

def catlink(p,target,name,lid):
    cls=sec(p,'categoryLinks'); return ET.SubElement(cls,q('categoryLink'),{'id':lid,'name':name,'hidden':'false','targetId':target})

def group(p,gid,name,minv=None,maxv=None):
    gs=sec(p,'selectionEntryGroups'); g=ET.SubElement(gs,q('selectionEntryGroup'),{'name':name,'hidden':'false','id':gid,'collective':'false','import':'true'})
    if minv is not None: constraint(g,gid+'-min','min',minv)
    if maxv is not None: constraint(g,gid+'-max','max',maxv)
    return g

def selection(p,sid,name,stype='upgrade',points=None,minv=None,maxv=None):
    ss=sec(p,'selectionEntries'); e=ET.SubElement(ss,q('selectionEntry'),{'type':stype,'import':'true','name':name,'hidden':'false','id':sid})
    if points is not None: cost(e,points)
    if minv is not None: constraint(e,sid+'-min','min',minv)
    if maxv is not None: constraint(e,sid+'-max','max',maxv)
    return e

def link(p,lid,name,target,points=None,maxv=None):
    ls=sec(p,'entryLinks'); e=ET.SubElement(ls,q('entryLink'),{'import':'true','name':name,'hidden':'false','id':lid,'type':'selectionEntry','targetId':target})
    if points is not None: cost(e,points)
    if maxv is not None: constraint(e,lid+'-max','max',maxv)
    return e

def modifier_condition(p,mid,field,value,ctype,child,scope='roster'):
    ms=sec(p,'modifiers'); m=ET.SubElement(ms,q('modifier'),{'type':'set','value':str(value),'field':field})
    cs=ET.SubElement(m,q('conditions'))
    ET.SubElement(cs,q('condition'),{'type':ctype,'value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return m

def hide_unless(p,child='legion-i'):
    modifier_condition(p,'x','hidden','true','lessThan',child)

def add_shared(sid,name,ruletext=None,weapon=None):
    shared=sec(root,'sharedSelectionEntries')
    if byid(sid) is not None: return byid(sid)
    e=ET.SubElement(shared,q('selectionEntry'),{'type':'upgrade','import':'true','name':name,'hidden':'false','id':sid})
    if weapon:
        ranged(e,'prof-'+sid,name,*weapon)
    if ruletext: rule(e,'rule-'+sid,name,ruletext)
    return e

def add_root_unit(uid,name,points,cat='cat-elites'):
    roots=sec(root,'selectionEntries')
    e=ET.SubElement(roots,q('selectionEntry'),{'type':'unit','import':'true','name':name,'hidden':'false','id':uid})
    cost(e,points); catlink(e,cat,{'cat-hq':'HQ','cat-elites':'Elites','cat-low':'Lords of War'}.get(cat,cat),uid+'-cat')
    hide_unless(e)
    return e

def add_named(uid,name,points,stats,wing,extra_rules,wargear):
    e=add_root_unit(uid,name,points,'cat-hq'); constraint(e,uid+'-rostermax','max',1,scope='roster')
    profile(e,uid+'-prof',name,*stats)
    rule(e,uid+'-wargear','Wargear',wargear)
    rule(e,uid+'-base','Special Rules','Legiones Astartes (Dark Angels); Independent Character; Master of the Legion; Stubborn; '+wing+'.')
    for rid,rname,text in extra_rules: rule(e,uid+'-'+rid,rname,text)
    return e

# Remove any previous rev22 additions to make the patch rerunnable.
for parent in list(root.iter()):
    for child in list(parent):
        cid=child.get('id','')
        if cid.startswith('da22-') or cid.startswith('da-wing-'):
            parent.remove(child)

# Legion I configuration rules.
legion=byid('legion-i')
assert legion is not None
rule(legion,'da22-mastery','Mastery of the Blade','When a Dark Angels model fights in close combat using a sword-type weapon against an enemy model with equal Weapon Skill, it hits on a 3+ instead of 4+. Sword-type weapons include Chainswords, Power Weapons, Force Weapons, Rending Weapons and Dark Angels weapons stated to count as swords; not Power Fists, Thunder Hammers, Lightning Claws or other clearly non-sword weapons.')
rule(legion,'da22-hexagrammaton','The Hexagrammaton','Every Dark Angels unit must be assigned to one Wing: Stormwing, Deathwing, Dreadwing, Ironwing, Firewing or Ravenwing. A unit normally belongs to only one. A Dedicated Transport has the same Wing as the unit that purchased it. Fixed-Wing units and named characters may not choose another Wing. Independent Characters retain their own Wing and do not confer it.')
rule(legion,'da22-armoury-summary','Dark Angels Armoury','Dark Angels gain access to the Legion-specific armoury where the relevant base weapon or Armoury access permits it: Calibanite Warblades, Terranic Greatswords, Ancient Plasma Weaponry, Plasma Repeaters, Plasma Burners, Stasis Shells, Molecular Acid Shells and Teleportation Transponders. Eligibility and prices are represented on the relevant options where implemented.')

# Universal Rite: Primarch's Chosen.
rites=byid('config-rites'); assert rites is not None
pc=selection(rites,'da22-rite-primarchs-chosen',"Rite of War — Primarch's Chosen")
rule(pc,'da22-rule-primarchs-chosen',"Primarch's Chosen",'''Requirements: include the Primarch of the Legion; the Primarch is Warlord; army at least 1,500 points. Effects: the Primarch fulfils the compulsory HQ requirement and may be fielded from 1,500 points; Legion Veteran and Terminator Squads may be Troops and must provide the two compulsory Troops; the Primarch may take an Honour Guard or appropriate Legion bodyguard as a slotless retinue. Limitations: no other Lord of War; no Allied Detachment; no more than one other Master of the Legion; at least half the army's non-vehicle units must have Legiones Astartes; if the Primarch is destroyed all other units in the Detachment cease to be Scoring for the rest of the battle, but may contest.''')

# Dark Angels Rites, gated by Legion choice and sharing the existing max-one Rite group.
da_rites=[
('storm','The Storm of War','''Effects: A 20-model Legion Tactical or Assault Squad may include one Legion Centurion at normal cost; he occupies no HQ slot, becomes part of the squad, may not leave, take a Consul upgrade or be Warlord, and must be Stormwing. Stationary Stormwing units gain their Stormwing re-roll during normal Shooting as well as First Fire/Overwatch. A Stormwing Infantry unit containing a Stormwing Character is Stubborn. Limitations: Warlord must be Stormwing; compulsory Troops must be 20-model Stormwing Tactical or Assault Squads; those compulsory units may not take Dedicated Transports.'''),
('vow','The Unbroken Vow','''Effects: Legion Veteran and Terminator Squads may be Troops and compulsory. A Deathwing unit within 6" of an Objective gains Feel No Pain (6+), or improves existing Feel No Pain one step to max 4+. A Deathwing Independent Character within 12" of an Objective gains +1 Attack. Place an additional Oath Objective as close as possible to battlefield centre. Limitations: Warlord Deathwing; compulsory Troops Veteran/Terminator Deathwing. At battle end enemy gains 150 VP if Dark Angels do not control Oath Objective, or 300 VP if enemy controls it, in missions using Victory Points.'''),
('eskaton','The Eskaton Imperative','''Effects: Legion Destroyer Squads and Dreadwing Interemptor Squads may be Troops and compulsory. Open ground outside deployment zones is Difficult Terrain. Before deployment place up to three Eskaton Markers outside deployment zones, at least 6" from an edge and 12" apart; within 6" is also Dangerous Terrain. Dreadwing Infantry gain Move Through Cover and Dreadwing models re-roll failed Dangerous Terrain tests. Enemy units within 12" and line of sight of the Warlord suffer -1 Leadership; Fearless unaffected. Limitations: Warlord Dreadwing; compulsory Troops Destroyers/Interemptors Dreadwing. Enemy gains 150 VP at battle end for an eligible unit remaining in its deployment zone, 300 if that unit is Scoring, in VP missions.'''),
('steel','The Steel Fist','''Effects: Legion Predator Strike Squadrons may be Troops and compulsory. Ironwing Infantry of 10 or fewer may buy Land Raider Phobos/Proteus as Dedicated Transport; 11-20 may buy a Spartan, normal capacities apply. A Transport carrying an Ironwing Independent Character gains 6+ invulnerable against shooting, or improves an existing invulnerable by one to max 4+. Limitations: Warlord Ironwing; compulsory Troops Ironwing Predators; every transportable Infantry unit begins embarked; max one Fast Attack choice.'''),
('arrow',"The Seeker's Arrow",'''Effects: Legion Bike and Sky Hunter Jetbike Squadrons may be Troops and compulsory. Ravenwing Infantry, Bikes and Jetbikes gain Outflank; Ravenwing Bikes/Jetbikes gain Hit & Run. At start of each Dark Angels turn choose +2" Turbo-Boost/Advance, +2" charge distance, or +2" Consolidation for all Ravenwing units until next Dark Angels turn. Limitations: Warlord Ravenwing; compulsory Troops Ravenwing Bike/Sky Hunter units; max one Heavy Support; no Vehicle unless Fast, Skimmer or both.'''),
('serpent',"The Serpent's Bane",'''Effects: nominate three enemy Priority Targets after armies are selected, chosen from HQ, Elites or Lords of War (or as many as possible). Firewing models attacking a Priority Target re-roll To Hit rolls of 1 and To Wound rolls of 1; against Vehicles re-roll Armour Penetration rolls of 1 instead of To Wound. A Firewing Independent Character gains +1 Attack in melee with a Priority Target. Up to three Firewing Troops units gain Infiltrate. Legion Seeker Squads may be Troops and compulsory. Limitations: Warlord Firewing; compulsory Troops must be Firewing Seeker or Assault Squads. Enemy gains 150 VP for each Priority Target still on battlefield at battle end in VP missions.''')]
for key,name,text in da_rites:
    e=selection(rites,'da22-rite-'+key,'Dark Angels Rite of War — '+name)
    hide_unless(e); rule(e,'da22-rite-'+key+'-rule',name,text)

# Mandatory Wing chooser on generic top-level units; Dedicated Transports inherit their purchaser's Wing.
wing_text={
'Stormwing':'First Fire/Overwatch: re-roll To Hit rolls of 1 with Bolters, Bolt Pistols, Storm Bolters, Foeblaster Boltguns and bolter component of combi-weapons.',
'Deathwing':'With a sword-type weapon against an enemy whose Weapon Skill is higher than the model’s own, re-roll To Hit rolls of 1 in close combat.',
'Dreadwing':'Flame, Plasma and Volkite attacks against this unit are -1 Strength (minimum 1); against Dreadwing Vehicles/Dreadnoughts this also reduces Armour Penetration Strength.',
'Ironwing':'Re-roll Armour Penetration rolls of 1 against enemy Vehicles. Ironwing Vehicles firing Snap Shots hit on 5+ instead of 6+.',
'Firewing':'Re-roll To Hit rolls of 1 when attacking an enemy unit containing an Independent Character, in shooting and close combat.',
'Ravenwing':'Dark Angels Bikes and Jetbikes gain Skilled Rider; Dark Angels Land Speeders gain Jink.'}
roots=sec(root,'selectionEntries')
for unit in roots.findall(q('selectionEntry')):
    if unit.get('type')!='unit' or unit.get('id','').startswith('da22-'): continue
    gid='da-wing-'+unit.get('id')
    g=group(unit,gid,'Hexagrammaton Wing',minv=0,maxv=1)
    hide_unless(g)
    modifier_condition(g,'x',gid+'-min','1','atLeast','legion-i')
    for idx,(wn,txt) in enumerate(wing_text.items()):
        w=selection(g,f'{gid}-{idx}',wn,maxv=1); rule(w,f'{gid}-{idx}-rule',wn,txt)

# Dark Angels shared weapons/wargear.
add_shared('da22-warblade','Calibanite Warblade','Strength User +1; Power Weapon. Counts as a sword-type weapon for Mastery of the Blade and Deathwing rules.')
add_shared('da22-greatsword','Terranic Greatsword','Strength User +2; Power Weapon, Two-Handed, Murderous Strike. Natural To Wound roll of 6 causes Instant Death. Counts as a sword-type weapon.')
add_shared('da22-plasma-pistol','Calibanite Plasma Pistol',weapon=('12"','6','2','Pistol'))
add_shared('da22-plasma-gun','Calibanite Plasma Gun',weapon=('24"','6','2','Rapid Fire'))
add_shared('da22-plasma-cannon','Calibanite Plasma Cannon',weapon=('36"','6','2','Heavy 1, Blast'))
add_shared('da22-plasma-repeater','Plasma Repeater',weapon=('12"','6','2','Salvo 2/3, Twin-linked, Gets Hot'))
add_shared('da22-plasma-burner','Plasma Burner','Plasma Flame: may re-roll failed To Hit rolls when making Overwatch; roll once for number of generated shots each time it fires.',('12"','4','2','Assault D3+1, Ignores Cover, Plasma Flame'))
add_shared('da22-stasis-missile','Stasis Shell — Missile','Stasis Anomaly: if a unit is hit, all models in it have Initiative 1 until end of current player turn; multiple anomalies do not stack.',('48"','4','6','Heavy 1, Blast, Stasis Anomaly'))
add_shared('da22-stasis-grenade','Stasis Shell — Grenade','Stasis Anomaly: if a unit is hit, all models in it have Initiative 1 until end of current player turn; multiple anomalies do not stack.',('24"','2','-','Assault 1, Blast, Stasis Anomaly'))
add_shared('da22-acid-hb','Molecular Acid Heavy Bolter','Fleshbane. A Twin-linked Heavy Bolter using Molecular Acid Shells remains Twin-linked.',('36"','5','4','Heavy 3, Fleshbane'))
add_shared('da22-transponders','Teleportation Transponders','A model/unit equipped with these may deploy using Deep Strike even if the mission normally forbids it. Terminator unit +15 points; Terminator Independent Character +10 points; an IC intending to Deep Strike with a unit buys separately.')
add_shared('da22-plasma-caster','Plasma-caster','Plasma Flame: failed To Hit rolls may be re-rolled when firing Overwatch.',('12"','4','2','Assault 2, Ignores Cover, Plasma Flame'))
add_shared('da22-plasma-incinerator','Plasma Incinerator with Suspensor Web','When several identical Plasma Burners/Incinerators fire, roll once for shots and use it for every weapon of that type. Plasma Flame permits re-rolling failed Overwatch To Hit rolls.',('18"','4','2','Heavy D3+4, Ignores Cover, Plasma Flame'))
add_shared('da22-needle-pistol','Needle Pistol',weapon=('12"','2','5','Pistol, Poisoned, Rending'))
add_shared('da22-charge-blade','Calibanite Charge-blade','Grants +1 Strength and Rending. Supercharged Blades: at start of an Assault phase while engaged, the Cabal may make all Charge-blades also Power Weapons until phase end; each Enigmatus rolling one or more natural 1s To Hit suffers one S4 hit after its attacks, normal saves allowed.')

# HQ Dark Angels Armoury options.
for prefix in ['hq-praetor','hq-centurion']:
    sg=byid(prefix+'-single'); tg=byid(prefix+'-two')
    if sg is not None:
        e=link(sg,'da22-'+prefix+'-warblade','Calibanite Warblade','da22-warblade',25,maxv=1); hide_unless(e)
    if tg is not None:
        e=link(tg,'da22-'+prefix+'-greatsword','Terranic Greatsword','da22-greatsword',35,maxv=1); hide_unless(e)

# Add Ancient Plasma alternatives to every direct generic Plasma Pistol/Gun/Cannon entryLink while retaining its original constraints/modifiers.
def bump_points(e,delta):
    for c in e.iter(q('cost')):
        if c.get('typeId')=='pts': c.set('value',str(float(c.get('value','0'))+delta).rstrip('0').rstrip('.'))

def clone_plasma(target,new_target,new_name,suffix,delta=0):
    candidates=[(p,x) for p in root.iter() for x in list(p) if x.tag==q('entryLink') and x.get('targetId')==target and not x.get('id','').startswith('da22-')]
    for n,(p,x) in enumerate(candidates):
        y=deepcopy(x); y.set('id',f'da22-alt-{suffix}-{n}'); y.set('targetId',new_target); y.set('name',new_name); y.set('hidden','false')
        if delta: bump_points(y,delta)
        hide_unless(y); p.append(y)
clone_plasma('gear-plasma-pistol','da22-plasma-pistol','Calibanite Plasma Pistol','pp')
clone_plasma('gear-plasma-gun','da22-plasma-gun','Calibanite Plasma Gun','pg')
clone_plasma('gear-plasma-gun','da22-plasma-repeater','Plasma Repeater','pr',10)
clone_plasma('gear-plasma-gun','da22-plasma-burner','Plasma Burner','pb',5)
clone_plasma('gear-plasma-cannon','da22-plasma-cannon','Calibanite Plasma Cannon','pc')

# DEATHWING COMPANION DETACHMENT
u=add_root_unit('da22-deathwing-companions','Deathwing Companion Detachment',175)
profile(u,'da22-dwc-prof','Deathwing Companion','5','4','4','4','1','4','2','9','2+')
profile(u,'da22-dwc-oath-prof','Oathbearer','5','4','4','4','2','4','2','10','2+/5+')
rule(u,'da22-dwc-wg','Wargear','4 Deathwing Companions + 1 Oathbearer. Artificer Armour, Calibanite Warblade, Bolter, Bolt Pistol, Frag Grenades; Oathbearer additionally has a Refractor Field.')
rule(u,'da22-dwc-rules','Special Rules','Legiones Astartes (Dark Angels); Deathwing (fixed); Stubborn; Death-sworn Companions; Deathwing Retinue.')
rule(u,'da22-dwc-deathsworn','Death-sworn Companions','While an eligible Dark Angels Independent Character is joined, once per phase when that Character suffers an unsaved Wound, remove one Companion within 2" instead and ignore the Wound. Use before rolling D3 for a Massive Wound.')
rule(u,'da22-dwc-ret','Deathwing Retinue','May replace a Legion Command/Honour Guard retinue for an eligible Dark Angels Praetor or named character. It does not occupy a separate Force Organisation slot when selected as that retinue.')
ex=group(u,'da22-dwc-extra-g','Squad Size',maxv=5); selection(ex,'da22-dwc-extra','Additional Deathwing Companion','upgrade',35,maxv=5)
mg=group(u,'da22-dwc-melee','Calibanite Warblade Replacements',maxv=10); link(mg,'da22-dwc-terr','Terranic Greatsword','da22-greatsword',10,maxv=10); link(mg,'da22-dwc-fist','Power Fist','gear-power-fist',5,maxv=10)
rg=group(u,'da22-dwc-ranged','Bolter Replacements',maxv=10)
for lid,n,t,c in [('cf','Combi-Flamer','gear-combi-flamer',10),('cv','Combi-Volkite Charger','gear-combi-volkite',10),('cm','Combi-Meltagun','gear-combi-melta',15),('cp','Combi-Plasma Gun','gear-combi-plasma',15),('pp','Plasma Pistol','gear-plasma-pistol',15)]: link(rg,'da22-dwc-'+lid,n,t,c,maxv=10)
selection(rg,'da22-dwc-aegis','Cytheron Aegis','upgrade',10,maxv=10); rule(u,'da22-dwc-aegis-rule','Cytheron Aegis','Bearer has 4+ Invulnerable Save against shooting and 5+ in close combat; occupies one hand and prevents two-weapon bonus. If at least two Aegis bearers are present, at start of Assault phase the unit may deploy them until next Movement phase: whole unit gains 4++ shooting/5++ melee and engaged enemies suffer -1 Initiative; Aegis bearers make no close-combat attacks. Ends if fewer than two remain.')
wg=group(u,'da22-dwc-unitwg','Unit Wargear',maxv=3); selection(wg,'da22-dwc-melta','Melta Bombs — entire squad','upgrade',0,maxv=1); rule(byid('da22-dwc-melta'),'da22-dwc-melta-note','Cost','+5 points per model; apply the appropriate total when building the unit.'); selection(wg,'da22-dwc-jump','Jump Packs — entire squad','upgrade',0,maxv=1); rule(byid('da22-dwc-jump'),'da22-dwc-jump-note','Restriction','Only if associated Character has a Jump Pack; +15 points per model; unit then may not take a transport.'); selection(wg,'da22-dwc-krak','Krak Grenades — entire squad','upgrade',0,maxv=1); rule(byid('da22-dwc-krak'),'da22-dwc-krak-note','Cost','+2 points per model.')
tr=group(u,'da22-dwc-transport','Dedicated Transport',maxv=1)
for lid,n,t in [('rh','Rhino','transport-rhino'),('dp','Drop Pod','transport-drop-pod'),('dc','Dreadclaw Drop Pod','transport-dreadclaw'),('lr','Land Raider','hs-land-raider')]: link(tr,'da22-dwc-tr-'+lid,n,t,maxv=1)

# DEATHWING TERMINATOR COMPANIONS
u=add_root_unit('da22-deathwing-term-comp','Deathwing Terminator Companion Detachment',225)
profile(u,'da22-dwtc-prof','Deathwing Terminator Companion','5','4','4','4','1','4','2','9','2+')
profile(u,'da22-dwtc-oath-prof','Terminator Oathbearer','5','4','4','4','2','4','2','10','2+')
rule(u,'da22-dwtc-wg','Wargear','4 Terminator Companions + 1 Terminator Oathbearer. Entire unit chooses Tartaros or Cataphractii Terminator Armour at no additional cost. Combi-bolter and Calibanite Warblade.')
rule(u,'da22-dwtc-rules','Special Rules','Legiones Astartes (Dark Angels); Deathwing (fixed); Stubborn; Death-sworn Companions; Deathwing Retinue.')
rule(u,'da22-dwtc-ret','Deathwing Retinue','May replace a Legion Terminator Command Squad for an eligible Dark Angels Character wearing the same Terminator Armour pattern; no separate FOC slot.')
ex=group(u,'da22-dwtc-extra-g','Squad Size',maxv=5); selection(ex,'da22-dwtc-extra','Additional Terminator Companion','upgrade',40,maxv=5)
arm=group(u,'da22-dwtc-armour','Terminator Armour Pattern',minv=1,maxv=1); selection(arm,'da22-dwtc-tart','Tartaros Terminator Armour',maxv=1); selection(arm,'da22-dwtc-cat','Cataphractii Terminator Armour',maxv=1)
mg=group(u,'da22-dwtc-melee','Calibanite Warblade Replacements',maxv=10); link(mg,'da22-dwtc-terr','Terranic Greatsword','da22-greatsword',10,maxv=10); link(mg,'da22-dwtc-fist','Power Fist','gear-power-fist',5,maxv=10); link(mg,'da22-dwtc-th','Thunder Hammer','gear-thunder',10,maxv=10)
pg=group(u,'da22-dwtc-pair','Replace both Combi-Bolter and Calibanite Warblade',maxv=10); link(pg,'da22-dwtc-claws','Pair of Lightning Claws','gear-pair-claws',15,maxv=10)
rg=group(u,'da22-dwtc-ranged','Combi-Bolter Replacements',maxv=10)
for lid,n,t,c in [('cf','Combi-Flamer','gear-combi-flamer',10),('cv','Combi-Volkite Charger','gear-combi-volkite',10),('cm','Combi-Meltagun','gear-combi-melta',15),('cp','Combi-Plasma Gun','gear-combi-plasma',15)]: link(rg,'da22-dwtc-'+lid,n,t,c,maxv=10)
wg=group(u,'da22-dwtc-wargear','Wargear',maxv=2); link(wg,'da22-dwtc-gh','Grenade Harness (Oathbearer)','gear-grenade-harness',10,maxv=1); link(wg,'da22-dwtc-trans','Teleportation Transponders — whole squad','da22-transponders',15,maxv=1)
tr=group(u,'da22-dwtc-transport','Dedicated Transport',maxv=1)
for lid,n,t in [('lr','Land Raider','hs-land-raider'),('dc','Dreadclaw Drop Pod','transport-dreadclaw'),('sp','Spartan Assault Tank','hs-spartan')]: link(tr,'da22-dwtc-tr-'+lid,n,t,maxv=1)

# INNER CIRCLE KNIGHTS CENOBIUM
u=add_root_unit('da22-cenobium','Inner Circle Knights Cenobium',275)
profile(u,'da22-cen-prof','Knight Cenobite','5','4','4','4','1','4','2','9','2+')
profile(u,'da22-cen-pre-prof','Order Preceptor','6','4','4','4','1','4','2','10','2+')
ranged(u,'da22-cen-caster-prof','Plasma-caster','12"','4','2','Assault 2, Ignores Cover, Plasma Flame')
rule(u,'da22-cen-wg','Wargear','4 Knight Cenobites + 1 Order Preceptor; Cataphractii Terminator Armour; Terranic Greatsword; Plasma-caster.')
rule(u,'da22-cen-rules','Special Rules','Legiones Astartes (Dark Angels); Stubborn; Adamantium Will; Inner Circle; Order Exemplars; Uncompromising Discipline.')
rule(u,'da22-cen-inner','Inner Circle','The unit may not select a Hexagrammaton Wing. Order Exemplars replaces the normal Wing benefit.')
rule(u,'da22-cen-disc','Uncompromising Discipline','Knights Cenobium may enter and fire Overwatch despite wearing Cataphractii Terminator Armour. All other Cataphractii restrictions apply.')
ex=group(u,'da22-cen-extra-g','Squad Size',maxv=5); selection(ex,'da22-cen-extra','Additional Knight Cenobite','upgrade',45,maxv=5)
mg=group(u,'da22-cen-melee','Weapon Replacements',maxv=10); link(mg,'da22-cen-th','Thunder Hammer (replaces Terranic Greatsword)','gear-thunder',0,maxv=10)
wg=group(u,'da22-cen-pre-wg','Order Preceptor Wargear',maxv=2); link(wg,'da22-cen-gh','Grenade Harness','gear-grenade-harness',10,maxv=1); link(wg,'da22-cen-dw','Digital Weapons','gear-hq-digital',10,maxv=1)
orders=group(u,'da22-cen-orders','Order Exemplars',minv=1,maxv=1)
order_data=[('augurs','Augurs of Weakness','+1 Strength when making Armour Penetration rolls against vehicles with AV11+.'),('icons','Icons of Resolve','If charged, each model gains +1 Attack during that Assault phase.'),('guardians','Guardians of Sanctity','When making Deny the Witch, roll 2D6 and use the highest before modifiers.'),('slayers','Slayers of Kings','Against enemy units whose majority WS is 5+, re-roll To Hit rolls of 1 in close combat.'),('hunters','Hunters of Beasts','Against T5 re-roll To Wound rolls of 1; against T6+ re-roll all failed To Wound rolls.'),('reapers','Reapers of Hosts','A model beginning its Initiative step in base contact with more than one enemy gains +1 Attack for that Assault phase.'),('breakers','Breakers of Witches','Re-roll failed To Hit and To Wound rolls in close combat against Psykers, Brotherhoods of Psykers and Daemons.')]
for key,n,t in order_data:
    o=selection(orders,'da22-order-'+key,n,maxv=1); rule(o,'da22-order-'+key+'-rule',n,t)
tr=group(u,'da22-cen-transport','Dedicated Transport',maxv=1); link(tr,'da22-cen-lr','Land Raider (5 models)','hs-land-raider',maxv=1); link(tr,'da22-cen-sp','Spartan Assault Tank (up to 10 models)','hs-spartan',maxv=1)

# DREADWING INTEREMPTORS
u=add_root_unit('da22-interemptors','Dreadwing Interemptor Squad',160)
profile(u,'da22-int-prof','Interemptor','4','4','4','4','1','4','1','9','3+')
profile(u,'da22-int-pre-prof','Interemptor Praefectus','4','4','4','4','1','4','2','10','3+')
rule(u,'da22-int-wg','Wargear','4 Interemptors + 1 Interemptor Praefectus; Power Armour; Plasma Burner; Chainsword; Frag Grenades; Rad Grenades.')
rule(u,'da22-int-rules','Special Rules','Legiones Astartes (Dark Angels); Dreadwing (fixed); Stubborn; Bitter Duty. Only a Dark Angels Independent Character assigned to the Dreadwing may join this unit.')
ex=group(u,'da22-int-extra-g','Squad Size',maxv=10); selection(ex,'da22-int-extra','Additional Interemptor','upgrade',25,maxv=10)
hg=group(u,'da22-int-heavy','Special Weapon Replacement — one per five models',maxv=1); hmax=byid('da22-int-heavy-max'); modifier_condition(hg,'x','da22-int-heavy-max','2','atLeast','da22-int-extra',scope='parent'); # overwritten below with threshold modifiers
# Replace first modifier condition value threshold manually.
cond=hg.find(q('modifiers')).find(q('modifier')).find(q('conditions')).find(q('condition')); cond.set('value','5')
modifier_condition(hg,'x','da22-int-heavy-max','3','atLeast','da22-int-extra',scope='parent'); hg.find(q('modifiers')).findall(q('modifier'))[-1].find(q('conditions')).find(q('condition')).set('value','10')
selection(hg,'da22-int-radmiss','Missile Launcher with Suspensor Web, Rad Missiles and Stasis Missiles','upgrade',15,maxv=3); link(hg,'da22-int-inc','Plasma Incinerator with Suspensor Web','da22-plasma-incinerator',15,maxv=3)
eq=group(u,'da22-int-eq','Squad Equipment',maxv=2); link(eq,'da22-int-vex','Legion Vexilla','gear-vexilla',10,maxv=1); link(eq,'da22-int-nuncio','Nuncio-Vox','gear-nuncio',10,maxv=1)
ph=group(u,'da22-int-phosphex','Interemptor Praefectus',maxv=3); link(ph,'da22-int-ph','Phosphex Bomb','gear-phosphex-bomb',10,maxv=3)
selection(u,'da22-int-krak','Krak Grenades — entire squad (+2 points per model)','upgrade',0,maxv=1)
tr=group(u,'da22-int-transport','Dedicated Transport — squad of 10 or fewer',maxv=1)
for lid,n,t in [('rh','Rhino','transport-rhino'),('dp','Drop Pod','transport-drop-pod'),('dc','Dreadclaw Drop Pod','transport-dreadclaw'),('lr','Land Raider','hs-land-raider')]: link(tr,'da22-int-tr-'+lid,n,t,maxv=1)

# FIREWING ENIGMATUS CABAL
u=add_root_unit('da22-enigmatus','Firewing Enigmatus Cabal',150)
profile(u,'da22-enig-prof','Firewing Enigmatus','5','4','4','4','2','5','3','10','3+')
ranged(u,'da22-enig-needle-prof','Needle Pistol','12"','2','5','Pistol, Poisoned, Rending')
rule(u,'da22-enig-wg','Wargear','3 Firewing Enigmatii; Power Armour; Calibanite Charge-blade; Needle Pistol; Shroud Bombs; Enigmatus-pattern Jump Pack. All models are Characters and Jump Infantry.')
rule(u,'da22-enig-rules','Special Rules','Legiones Astartes (Dark Angels); Firewing (fixed); Scout; Hatred (Characters).')
rule(u,'da22-enig-charge','Calibanite Charge-blade / Supercharged Blades','Charge-blade grants +1 Strength and Rending. At start of an Assault phase while engaged, the unit may supercharge: blades additionally count as Power Weapons until phase end. Each Enigmatus rolling one or more natural 1s To Hit takes one S4 hit after resolving attacks; normal Armour Saves apply.')
rule(u,'da22-enig-shroud','Shroud Bombs','Defensive Grenades. In addition, an enemy non-vehicle unit attempting to charge must pass a Leadership test or may not charge the Cabal that phase. Night Vision and Daemon models ignore this additional effect.')
rule(u,'da22-enig-jump','Enigmatus-pattern Jump Pack','Normal Jump Infantry. If the Cabal moved using Jump Packs in its preceding Movement phase it has a 5+ Cover Save against shooting unless better. When it declares a charge after moving with Jump Packs, the target may not Stand & Shoot; this does not prevent Overwatch established earlier in the turn.')
selection(u,'da22-enig-gl','Grenade Launcher with Frag, Krak and Stasis Grenades (one model)','upgrade',20,maxv=1)

# Named Dark Angels characters.
add_named('da22-corswain','Corswain, Seneschal of the First Legion',200,('7','5','4','4','3','5','4','10','2+/4+'),'Deathwing',[
('blade','The Blade','Master-crafted Power Weapon. At start of each Assault phase while engaged choose: one-handed grants +1 Strength and permits Bolt Pistol as second close-combat weapon; or two-handed resolves attacks at Strength 6 and grants no two-weapon bonus.'),
('paladin','Paladin of Glory','When directing attacks against an enemy Character or Independent Character, always hits on 3+ unless normally better. Natural To Wound roll of 6 with The Blade against such a model inflicts Massive Wound (D3).'),
('seneschal','Seneschal of the First Legion','May select a Deathwing Companion Detachment as retinue. That retinue may increase every Companion and Oathbearer WS by +1 to max WS6 for +5 points per model. Corswain and retinue count as one HQ selection.')], 'Armour of the Forest; Iron Halo; Bolt Pistol; The Blade; Frag Grenades. May take Krak Grenades +2 points.')
add_named('da22-sedras','Marduk Sedras, Lord of the Twenty-Third Order',225,('6','5','4','4','3','4','4','10','2+/4+'),'Dreadwing',[
('deathworlds','Death of Worlds','Two-Handed Power Weapon. Attacks are Strength 6. Natural To Wound rolls of 5 or 6 inflict Massive Wound (D3).'),
('ancient','Ancient of War','After deployment but before first turn nominate one enemy faction. Sedras and friendly Dark Angels units with a model within 6" may re-roll To Hit rolls of 1 and To Wound rolls of 1 against models of that faction in Shooting and Assault.'),
('eskaton','Eskaton','Always Dreadwing. Sedras and any Dark Angels unit he joins gain the Siege Specialists Veteran Skill.'),
('ret','Cenobium Retinue','One Inner Circle Knights Cenobium may be his personal retinue without a separate FOC slot; Sedras and the Cenobium count as one HQ selection.')], 'Regalia of the Shattered Sceptre (Cataphractii Terminator Armour); Combi-volkite; Death of Worlds; Grenade Harness.')
add_named('da22-redloss','Farith Redloss',185,('6','5','4','4','3','5','3','10','2+/4+'),'Dreadwing',[
('voted','Voted-Lieutenant of the Dreadwing','Always Dreadwing. May select one Dreadwing Interemptor Squad as retinue; it occupies no separate Elites choice and Redloss may join it despite Bitter Duty. They count as one HQ selection.'),
('exterm','Extermination Protocol','Once per battle at beginning of Dark Angels Shooting phase choose Redloss own unit or one friendly Dreadwing unit with a model within 12". Until phase end models in it re-roll To Wound rolls of 1 and Armour Penetration rolls of 1 with Flame, Plasma or Volkite weapons; second result accepted.')], 'Artificer Armour; Iron Halo; Terranic Greatsword; Plasma Pistol; Rad Grenades; 2 Phosphex Bombs; Frag Grenades. May take Krak Grenades +2 points.')
add_named('da22-holguin','Holguin',190,('6','5','4','4','3','4','3','10','2+/4+'),'Deathwing',[
('voted','Voted-Lieutenant of the Deathwing','Always Deathwing. May select a Deathwing Terminator Companion Detachment as personal retinue without a separate FOC slot; together count as one HQ selection.'),
('line','Unbroken Line','While joined to a friendly Dark Angels unit, that unit gains Counter-Attack. If charged while controlling an Objective or occupying a fortification, ruin or building, Holguin may re-roll To Hit rolls of 1 that Assault phase.'),
('sword','Master-crafted Terranic Greatsword','Uses the normal Terranic Greatsword rules and is additionally Master-crafted.')], 'Cataphractii Terminator Armour; Combi-bolter; Master-crafted Terranic Greatsword; Grenade Harness.')

# LION EL'JONSON
u=add_root_unit('da22-lion',"Lion El'Jonson, The First",550,'cat-low'); constraint(u,'da22-lion-rostermax','max',1,scope='roster'); hide_unless(u,'allegiance-loyalist')
profile(u,'da22-lion-prof',"Lion El'Jonson",'9','6','6','6','6','7','6','10','1+/4++')
ranged(u,'da22-lion-fusil','Fusil Actinaeus','18"','7','2','Salvo 2/4, Twin-linked, Blind')
rule(u,'da22-lion-base','Primarch / Restrictions','Primarch; Legiones Astartes (Dark Angels). Loyalist Dark Angels only. As a Primarch: Lord of War, normally 2,000+ points, Primary Detachment only, maximum one Primarch, must be Warlord; Independent Character, Eternal Warrior, Fear, Fearless, Adamantium Will, Fleet, It Will Not Die, Master of the Legion.')
rule(u,'da22-lion-panoply','Leonine Panoply','Counts as Primarch Armour (1+ Armour, 4+ Invulnerable). The first failed Invulnerable Save made by the Lion during each player turn may be re-rolled.')
wg=group(u,'da22-lion-blade','Choose Weapon',minv=1,maxv=1)
ls=selection(wg,'da22-lion-sword','The Lion Sword',maxv=1); rule(ls,'da22-lion-sword-rule','The Lion Sword','Master-crafted, Two-Handed Power Weapon; attacks at +1 Strength with Fleshbane and Lance; sword-type for Dark Angels rules.')
wb=selection(wg,'da22-lion-wolf','The Wolf Blade',maxv=1); rule(wb,'da22-lion-wolf-rule','The Wolf Blade','Two-Handed Power Weapon; attacks at +3 Strength with Shred; sword-type for Dark Angels rules.')
rule(u,'da22-lion-stasis','Stasis Grenades','If the Lion and joined unit successfully charge, or are successfully charged, all enemy units engaged as a result are Initiative 1 until end of current player turn. Neither Assault nor Defensive Grenades.')
rule(u,'da22-lion-focus','An Absolute Focus','May never require worse than 4+ To Hit in close combat regardless of enemy Weapon Skill or modifiers.')
rule(u,'da22-lion-point','The Point of the Blade','The Lion and any unit he joins may declare charges against enemy units up to 8" away instead of 6". Difficult Terrain does not reduce this; Dangerous Terrain resolves normally.')
rule(u,'da22-lion-choler',"The Lion's Choler",'At 4 Wounds or fewer, +1 Attack. At 2 Wounds or fewer, +2 Attacks instead. Not cumulative.')
rule(u,'da22-lion-knight','Knight of Knights','Each Assault phase in which he directs attacks against an enemy Independent Character or Primarch, re-roll one failed To Hit OR one failed To Wound against such a model; second result accepted.')
rule(u,'da22-lion-ret','Primarch Retinue','May select one Legion Honour Guard, Legion Terminator Command Squad, Deathwing Companion Detachment or Deathwing Terminator Companion Detachment as a slotless Primarch Retinue. Terminator Companions may be selected despite the Lion not wearing Terminator Armour.')

# Catalogue metadata and validation.
root.set('revision','22')
comment=root.find(q('comment'))
if comment is None: comment=ET.SubElement(root,q('comment'))
comment.text='Revision 22: Added Dark Angels Legion integration: mandatory Hexagrammaton Wings, Legion armoury foundations and plasma alternatives, six Legion Rites, unique formations, named characters and Lion El Jonson.'
readme=root.find(q('readme'))
if readme is not None: readme.text='Core Legiones Astartes catalogue with Army Configuration, generic HQ/Consuls and the first Legion expansion. Selecting I — Dark Angels unlocks Hexagrammaton Wing choices, Dark Angels Rites, armoury options, unique units, named characters and the Lion while retaining the standard Legion roster.'
ET.indent(tree,space='  ')
tree.write(CAT,encoding='UTF-8',xml_declaration=True)
# Reparse and reject duplicate IDs.
r=ET.parse(CAT).getroot(); ids=[e.get('id') for e in r.iter() if e.get('id')]; d=[k for k,v in Counter(ids).items() if v>1]
assert not d, 'duplicate IDs: '+','.join(d[:20])
assert r.get('revision')=='22'
for eid in ['da22-deathwing-companions','da22-deathwing-term-comp','da22-cenobium','da22-interemptors','da22-enigmatus','da22-corswain','da22-sedras','da22-redloss','da22-holguin','da22-lion','da22-rite-storm','da22-rite-serpent']:
    assert byid(eid) is not None,eid
print('Revision 22 Dark Angels build complete; IDs',len(ids))
