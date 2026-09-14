from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET
import re

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); INDEX=Path('index.xml')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()
top=cr.find(C('selectionEntries')); shared=cr.find(C('sharedSelectionEntries'))
assert top is not None and shared is not None

REPORT=[]
def note(s): REPORT.append(s); print(s)
def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def gby_id(i): return next((e for e in gr.iter() if e.get('id')==i),None)
def top_by_name(text):
    q=text.lower()
    return next((e for e in list(top) if q in (e.get('name') or '').lower()),None)
def any_by_name(text):
    q=text.lower()
    return next((e for e in cr.iter() if q in (e.get('name') or '').lower()),None)
def ensure(p,tag,ns=CNS):
    q=f'{{{ns}}}{tag}'; x=p.find(q)
    if x is None: x=ET.SubElement(p,q)
    return x
def wipe(p,tag):
    x=p.find(C(tag))
    if x is not None: p.remove(x)
def add_cost(e,v,id_=None):
    cs=ensure(e,'costs'); c=ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
    if id_: c.set('id',id_)
    return c
def add_constraint(e,id_,kind,val,scope='parent',inc=True):
    cs=ensure(e,'constraints'); return ET.SubElement(cs,C('constraint'),{'id':id_,'type':kind,'value':str(val),'field':'selections','scope':scope,'shared':'true','includeChildSelections':'true' if inc else 'false','includeChildForces':'false'})
def add_rule(e,id_,name,text):
    rs=ensure(e,'rules'); r=ET.SubElement(rs,C('rule'),{'id':id_,'name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=text; return r
def remove_rule_named(e,name):
    rs=e.find(C('rules'))
    if rs is None:return 0
    n=0
    for r in list(rs):
        if (r.get('name') or '').lower()==name.lower(): rs.remove(r); n+=1
    if len(rs)==0:e.remove(rs)
    return n
def fixed(e,id_,name):
    ses=ensure(e,'selectionEntries'); s=ET.SubElement(ses,C('selectionEntry'),{'id':id_,'name':name,'type':'upgrade','hidden':'false','import':'true','defaultAmount':'1'})
    add_constraint(s,id_+'-min','min',1); add_constraint(s,id_+'-max','max',1); return s
def option(group,id_,name,cost=0,maxv=1,rule=None):
    ses=ensure(group,'selectionEntries'); s=ET.SubElement(ses,C('selectionEntry'),{'id':id_,'name':name,'type':'upgrade','hidden':'false','import':'true'})
    add_constraint(s,id_+'-max','max',maxv); add_cost(s,cost)
    if rule:add_rule(s,id_+'-rule',name,rule)
    return s
def group(e,id_,name,maxv=None,roster_max=None):
    gs=ensure(e,'selectionEntryGroups'); g=ET.SubElement(gs,C('selectionEntryGroup'),{'id':id_,'name':name,'hidden':'false','collective':'false','import':'true'})
    if maxv is not None:add_constraint(g,id_+'-max','max',maxv)
    if roster_max is not None:add_constraint(g,id_+'-roster-max','max',roster_max,'roster')
    return g
def rewrite_ids(node,prefix):
    mp={}
    for x in node.iter():
        if x.get('id'):mp[x.get('id')]=prefix+x.get('id')
    for x in node.iter():
        if x.get('id') in mp:x.set('id',mp[x.get('id')])
        for a in ('targetId','childId','field'):
            if x.get(a) in mp:x.set(a,mp[x.get(a)])
def set_primary_cat(e,target,name):
    wipe(e,'categoryLinks'); cs=ET.SubElement(e,C('categoryLinks')); ET.SubElement(cs,C('categoryLink'),{'id':e.get('id')+'-cat','name':name,'targetId':target,'hidden':'false','primary':'true'})
def hide_if_missing(e,child,scope='roster'):
    mods=ensure(e,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':e.get('id')+'-hide-'+child,'type':'set','value':'true','field':'hidden'}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'lessThan','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def clone_nested(src,newid,newname=None):
    c=deepcopy(src); rewrite_ids(c,newid+'-'); c.set('id',newid)
    if newname:c.set('name',newname)
    wipe(c,'categoryLinks'); wipe(c,'modifiers')
    # Nested retinues have no separate FOC slot.
    return c
def transport_group(e,id_,names):
    g=group(e,id_,'Dedicated Transport',1)
    for n in names:
        t=top_by_name(n)
        if t is None: continue
        ls=ensure(g,'entryLinks'); l=ET.SubElement(ls,C('entryLink'),{'id':id_+'-'+re.sub('[^a-z0-9]+','-',n.lower()).strip('-'),'name':t.get('name'),'type':'selectionEntry','targetId':t.get('id'),'hidden':'false','import':'true'}); add_constraint(l,l.get('id')+'-max','max',1)
    return g

def clean_options(e):
    wipe(e,'selectionEntryGroups')
    # Preserve the parser's repeatable Additional model entry only; remove all other child options and rebuild below.
    ses=e.find(C('selectionEntries'))
    if ses is not None:
        for s in list(ses):
            if (s.get('name') or '').lower()!='additional model': ses.remove(s)

def add_summary(e,prefix,wargear,specials):
    # Fixed wargear is represented as mandatory structured selections rather than one pasted source block.
    ses=e.find(C('selectionEntries'))
    if ses is not None:
        for s in list(ses):
            if s.get('id','').startswith(prefix+'-fixed-'):ses.remove(s)
    for i,w in enumerate(wargear):fixed(e,f'{prefix}-fixed-{i}',w)
    for i,(n,t) in enumerate(specials):add_rule(e,f'{prefix}-rule-{i}',n,t)

def find_rite(substr):
    q=substr.lower()
    return next((e for e in cr.iter(C('selectionEntry')) if q in (e.get('name') or '').lower() and 'rite' in e.get('id','')),None)

# Idempotent cleanup of this revision.
for p in list(cr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r52-'):p.remove(x)
for p in list(gr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r52-'):p.remove(x)

maru=find_rite('maru skara'); third=find_rite('3rd company elite')
assert maru is not None, 'Maru Skara Rite not found'
assert third is not None, '3rd Company Elite Rite not found'
note(f'Rites: Maru={maru.get("id")} Third={third.get("id")}')

# Remove obsolete Rev43 loose EC sonic links from generic HSS and HQs; retain shared definitions for reference safety.
for uid in ('hs-heavy-support-squad','hq-praetor','hq-centurion'):
    u=by_id(uid)
    if u is None: continue
    for holder in [u,*list(u.findall('.//'+C('selectionEntryGroup')))]:
        ls=holder.find(C('entryLinks'))
        if ls is None:continue
        for l in list(ls):
            if l.get('id','').startswith('r43-') and ('ec-' in l.get('id','') or 'sonic' in (l.get('name') or '').lower()):ls.remove(l)

# EC imported entries, ordered by the final source.
ids={
'pal':'r41-unit-iii-0-palatine-blade-squad','phoenix':'r41-unit-iii-1-phoenix-terminator-squad','kako':'r41-unit-iii-2-kakophoni-squad','sun':'r41-unit-iii-3-sun-killer-squad','eid':'r41-unit-iii-4-lord-commander-eidolon','tar':'r41-unit-iii-5-saul-tarvitz','luc':'r41-unit-iii-6-captain-lucius','fab':'r41-unit-iii-7-fabius-bile','ryl':'r41-unit-iii-8-rylanor-the-unyielding','ful':'r41-unit-iii-9-fulgrim-the-phoenician'}
# Fall back by names if importer numbering changed.
for k,nm in [('pal','palatine blade'),('phoenix','phoenix terminator'),('kako','kakophoni'),('sun','sun killer'),('eid','lord commander eidolon'),('tar','saul tarvitz'),('luc','captain lucius'),('fab','fabius bile'),('ryl','rylanor'),('ful','fulgrim, the phoenician')]:
    if by_id(ids[k]) is None:
        x=top_by_name(nm)
        if x is not None:ids[k]=x.get('id')
for k,v in ids.items():
    if by_id(v) is None:note(f'WARNING missing {k}: {v}')

# Remove the giant auto-imported Source Entry blocks from all Legion III imported entries.
removed=0
for e in list(top):
    if e.get('id','').startswith('r41-unit-iii-'):removed+=remove_rule_named(e,'Source Entry')
note(f'Removed {removed} Emperor\'s Children Source Entry dumps')

# PALATINE BLADES
pal=by_id(ids['pal'])
if pal is not None:
    clean_options(pal)
    g=group(pal,'r52-ec-pal-options','Squad Options')
    option(g,'r52-ec-pal-power','Power weapon — replace Rending Weapon',10,10)
    option(g,'r52-ec-pal-shield','Combat Shield',5,10)
    option(g,'r52-ec-pal-melta','Melta bombs',5,10)
    option(g,'r52-ec-pal-krak','Krak grenades — select once per squad model',2,10,'The entire squad must take this upgrade; select one for every model currently in the squad.')
    option(g,'r52-ec-pal-jump','Jump Pack — select once per squad model',15,10,'The entire squad must take Jump Packs. The unit becomes Jump Infantry and may not select a Dedicated Transport.')
    add_rule(pal,'r52-ec-pal-duelists','Duelists','When fighting an enemy unit containing one or more Characters or Independent Characters, models in this squad may re-roll close-combat To Hit rolls of 1.')
    add_rule(pal,'r52-ec-pal-primus-armoury','Palatine Primus Armoury','The Palatine Primus may select up to 50 points of additional permitted weapons and wargear from the Space Marine Armoury.')
    transport_group(pal,'r52-ec-pal-transport',['Rhino','Drop Pod','Dreadclaw Drop Pod','Land Raider'])
    add_summary(pal,'r52-ec-pal',['Artificer Armour','Bolt pistol','Rending Weapon','Frag grenades'],[])

# PHOENIX TERMINATORS
ph=by_id(ids['phoenix'])
if ph is not None:
    clean_options(ph); g=group(ph,'r52-ec-ph-options','Options')
    option(g,'r52-ec-ph-doom','Doom Siren (one Phoenix Terminator)',15,1)
    option(g,'r52-ec-ph-harness','Grenade Harness (Phoenix Champion)',10,1)
    add_summary(ph,'r52-ec-ph',['Tartaros Terminator Armour','Phoenix Spear'],[('Implacable Advance','This unit has Implacable Advance.'),('Stubborn','This unit has Stubborn.')])
    transport_group(ph,'r52-ec-ph-transport',['Land Raider','Dreadclaw Drop Pod','Spartan'])

# KAKOPHONI
ka=by_id(ids['kako'])
if ka is not None:
    clean_options(ka); g=group(ka,'r52-ec-ka-options','Options')
    option(g,'r52-ec-ka-blast','Blastmaster — replace one Kakophoni Sonic Blaster',15,4,'One Kakophoni per full three models in the squad may take this option. A 6-model squad may take 2; 9 models may take 3; 12 models may take 4.')
    option(g,'r52-ec-ka-doom','Champion: Doom Siren and bolt pistol — replace Sonic Blaster',0,1)
    option(g,'r52-ec-ka-krak','Krak grenades — select once per squad model',2,12,'The entire squad must take this upgrade; select one for every model currently in the squad.')
    cg=group(ka,'r52-ec-ka-champ','Cacophonic Champion Melee Weapon',1); option(cg,'r52-ec-ka-pw','Power weapon',10); option(cg,'r52-ec-ka-pf','Power fist',15); option(g,'r52-ec-ka-melta','Cacophonic Champion: Melta bombs',5)
    add_summary(ka,'r52-ec-ka',['Power Armour','Sonic Blaster','Frag grenades'],[('Fearless','This unit is Fearless.'),('Cacophony','If an enemy unit suffers one or more casualties from shooting attacks made by this squad, it must take a Pinning test after the squad has finished firing.')])
    add_rule(ka,'r52-ec-ka-traitor','Traitor Only','Kakophoni may only be selected in a Traitor Emperor\'s Children army.')
    transport_group(ka,'r52-ec-ka-transport',['Rhino','Drop Pod','Land Raider'])
    hide_if_missing(ka,'allegiance-traitor')

# SUN KILLERS
sun=by_id(ids['sun'])
if sun is not None:
    clean_options(sun); eg=group(sun,'r52-ec-sun-energy','Energy Weapons',10)
    option(eg,'r52-ec-sun-plasma','Plasma Cannon replacement — select once per squad model',-5,10,'If selected, every model in the squad must replace its Lascannon with a Plasma Cannon. Do not mix this option with Volkite Culverins.')
    option(eg,'r52-ec-sun-volkite','Volkite Culverin replacement — select once per squad model',-15,10,'If selected, every model in the squad must replace its Lascannon with a Volkite Culverin. Do not mix this option with Plasma Cannons.')
    g=group(sun,'r52-ec-sun-options','Options'); option(g,'r52-ec-sun-krak','Krak grenades — select once per squad model',2,10,'The entire squad must take this upgrade; select one for every model currently in the squad.'); option(g,'r52-ec-sun-aa','Sun Killer Prefector: Artificer Armour',10); option(g,'r52-ec-sun-melta','Sun Killer Prefector: Melta bombs',5)
    add_summary(sun,'r52-ec-sun',['Power Armour','Lascannon','Bolt pistol','Frag grenades'],[('Exemplary Marksmen','Once during each friendly Shooting phase, the Sun Killer Squad may re-roll one failed shooting To Hit roll. The second result must be accepted.')])
    transport_group(sun,'r52-ec-sun-transport',['Rhino'])

# Named character clean rules and fixed wargear.
char_data={
'eid':(['Artificer Armour','Iron Halo','Jump Pack','Master-crafted Thunder Hammer','Doom Siren','Bolt pistol','Krak grenades'],[('Legiones Astartes (Emperor\'s Children)','This model has the Emperor\'s Children Legion rules.'),('Independent Character','This model is an Independent Character.'),('Master of the Legion','This model has Master of the Legion.'),('Thunderous Charge','During an Assault phase in which Eidolon charges, attacks made with his Thunder Hammer are resolved at Initiative 5 instead of Initiative 1. This Initiative value already includes any Initiative bonus gained for charging and may not be further increased.')]),
'tar':(['Artificer Armour','Refractor Field','Rending Weapon','Sniper Rifle','Frag grenades'],[('Legiones Astartes (Emperor\'s Children)','This model has the Emperor\'s Children Legion rules.'),('Independent Character','This model is an Independent Character.'),('Hardened Survivor','Saul Tarvitz and any unit he has joined improve any Cover Save they receive by 1, to a maximum of 4+. This does not grant a Cover Save. While Tarvitz and his unit are controlling an Objective, they have Fearless.')]),
'luc':(['Artificer Armour','Refractor Field','Master-crafted Power Weapon','Bolt pistol','Frag grenades'],[('Legiones Astartes (Emperor\'s Children)','This model has the Emperor\'s Children Legion rules.'),('Independent Character','This model is an Independent Character.'),('Honour or Death','If Lucius is in base contact with one or more enemy Independent Characters, he must direct all of his close-combat attacks against one of those Characters. When attacking an enemy Independent Character in close combat, Lucius may re-roll failed To Hit and To Wound rolls.')]),
'fab':(['Power Armour','The Chirurgeon','Xyclos Needler','Frag grenades'],[('Legiones Astartes (Emperor\'s Children)','This model has the Emperor\'s Children Legion rules.'),('Independent Character','This model is an Independent Character.'),('Enhanced Warriors','Before deployment, any number of eligible Space Marine squads may be enhanced for +3 points per model. Units in Terminator Armour may not be enhanced. Roll separately for each enhanced squad after deployment and before the first turn: 1 — make an Armour Save for each model, casualties are removed and survivors gain +1 Strength; 2–5 — +1 Strength and +1 Initiative; 6 — +1 Strength, +1 Initiative and +1 Attack, but surviving models count as casualties for Victory Points.')]),
'ryl':(['Kheres Assault Cannon','Dreadnought Close Combat Weapon with built-in Heavy Flamer','Smoke Launchers','Searchlight'],[('Atomantic Shielding','Rylanor uses the normal Atomantic Shielding rule from the Legion Contemptor Dreadnought entry.'),('Fleet','Rylanor has Fleet.'),('Ancient of Rites','Once per player turn, when Rylanor suffers a Glancing or Penetrating Hit not ignored by Atomantic Shielding, the Emperor\'s Children player may force the opponent to re-roll the resulting Vehicle Damage roll; the second result is accepted. If the mission rolls for first turn, an Emperor\'s Children army containing Rylanor may re-roll that roll once.'),('Living Icon of the Legion','Friendly Emperor\'s Children units with at least one model within 6 inches automatically pass Morale tests, but not Pinning tests. If Rylanor is destroyed, every friendly Emperor\'s Children unit with line of sight to him immediately takes a Pinning test at -1 Leadership.')]),
'ful':(['Gilded Panoply','Firebrand'],[('Primarch','Fulgrim follows the normal Primarch rules.'),('Legiones Astartes (Emperor\'s Children)','Fulgrim has the Emperor\'s Children Legion rules.'),('Gilded Panoply','Counts as Primarch Armour, except Fulgrim has a 5+ Invulnerable Save against ranged attacks and a 3+ Invulnerable Save against close-combat attacks.'),('Sublime Swordsman','When Fulgrim directs close-combat attacks against an enemy model with Weapon Skill 6 or higher, he may re-roll To Hit rolls of 1.'),('Perfect Execution','During an Assault phase in which Fulgrim charged, increase his Initiative and Attacks by +1 for that Assault phase.'),('Sire of Perfection','Once during each player turn, when a friendly Emperor\'s Children unit within 12 inches is selected to shoot or fight, it may re-roll To Hit rolls of 1 for the remainder of that phase.'),('Pride of the Phoenician','When Fulgrim fights an enemy Independent Character or Primarch, he gains +1 Attack against that model for each point by which his WS exceeds its WS, to a maximum of +2 Attacks.')])}
for key,(wg,sr) in char_data.items():
    e=by_id(ids[key])
    if e is None:continue
    # remove any prior r52 fixed selections/rules handled by idempotent pass; keep parsed options such as Krak if useful.
    add_summary(e,'r52-ec-'+key,wg,sr)

# Explicit Krak options for Tarvitz, Lucius and Fabius.
for key in ('tar','luc','fab'):
    e=by_id(ids[key])
    if e is not None:
        g=group(e,f'r52-ec-{key}-options','Options'); option(g,f'r52-ec-{key}-krak','Krak grenades',2)

# Fulgrim weapon choice and retinue.
ful=by_id(ids['ful'])
if ful is not None:
    wg=group(ful,'r52-ec-ful-weapons','Choose Melee Weapon',1); option(wg,'r52-ec-ful-fireblade','Fireblade',0,1,'Master-crafted Power Weapon. Attacks are resolved at +1 Strength and have Shred.'); option(wg,'r52-ec-ful-laer','Blade of the Laer',0,1,'Master-crafted, Two-Handed Power Weapon. Attacks are resolved at Fulgrim\'s normal Strength and have Fleshbane.')

# Slotless real retinues for Lucius and Eidolon.
command_template=by_id('hq-centurion-ret-command'); honour_template=by_id('hq-praetor-ret-honour')
assert command_template is not None and honour_template is not None
luc=by_id(ids['luc'])
if luc is not None:
    rg=group(luc,'r52-ec-luc-retinue','Command Retinue (does not occupy a separate FOC slot)',1); ses=ensure(rg,'selectionEntries'); ret=clone_nested(command_template,'r52-ec-luc-command','Legion Command Squad'); ses.append(ret); add_rule(rg,'r52-ec-luc-ret-rule','Command Retinue','Lucius may select one Legion Command Squad. It occupies no separate Force Organisation slot; Lucius and the Command Squad count as one HQ selection but may deploy and operate separately.')
eid=by_id(ids['eid'])
if eid is not None:
    rg=group(eid,'r52-ec-eid-retinue','Command Retinue (does not occupy a separate FOC slot)',1); ses=ensure(rg,'selectionEntries'); ret=clone_nested(honour_template,'r52-ec-eid-honour','Legion Honour Guard Squad'); jg=group(ret,'r52-ec-eid-honour-jump-group','Eidolon Retinue Upgrade'); option(jg,'r52-ec-eid-honour-jump','Jump Pack — select once per Honour Guard model',15,10,'Every model in the Honour Guard must take this upgrade. The squad becomes Jump Infantry and may not select a Dedicated Transport.'); ses.append(ret); add_rule(rg,'r52-ec-eid-ret-rule','Command Retinue','Eidolon may select one Legion Honour Guard Squad. It occupies no separate Force Organisation slot and Eidolon and the Honour Guard count as one HQ selection.')

# Fulgrim slotless Primarch Retinue: Honour Guard, Terminator Command, or Phoenix Terminators.
if ful is not None:
    rg=group(ful,'r52-ec-ful-retinue','Primarch Retinue (does not occupy a separate FOC slot)',1); ses=ensure(rg,'selectionEntries')
    ses.append(clone_nested(honour_template,'r52-ec-ful-honour','Legion Honour Guard Squad'))
    term_template=by_id('hq-praetor-ret-termcommand') or by_id('hq-centurion-ret-termcommand')
    if term_template is not None:ses.append(clone_nested(term_template,'r52-ec-ful-termcommand','Legion Terminator Command Squad'))
    if ph is not None:ses.append(clone_nested(ph,'r52-ec-ful-phoenix-retinue','Phoenix Terminator Squad'))
    add_rule(rg,'r52-ec-ful-ret-rule','Primarch Retinue','Fulgrim may select one Legion Honour Guard Squad, Legion Terminator Command Squad or Phoenix Terminator Squad. It does not occupy an additional Force Organisation selection.')

# Functional Sonic Weaponry HSS clone. This represents the one/two eligible squads instead of loose max-1 weapon checkboxes.
hss=by_id('hs-heavy-support-squad')
assert hss is not None
sonic=deepcopy(hss); rewrite_ids(sonic,'r52-ec-sonic-hss-'); sonic.set('id','r52-ec-sonic-hss'); sonic.set('name','Legion Heavy Support Squad — Sonic Weaponry'); sonic.set('hidden','false'); sonic.set('import','true')
# Remove inherited heavy-weapon choice groups and any old EC sonic links.
for gs in list(sonic.findall('.//'+C('selectionEntryGroup'))):
    if 'heavy weapon' in (gs.get('name') or '').lower():
        parent=next((p for p in sonic.iter() if gs in list(p)),None)
        if parent is not None:parent.remove(gs)
for holder in sonic.iter():
    ls=holder.find(C('entryLinks'))
    if ls is not None:
        for l in list(ls):
            if 'r43-' in l.get('id','') and ('sonic' in l.get('id','') or 'ec-' in l.get('id','')):ls.remove(l)
set_primary_cat(sonic,'cat-heavy','Heavy Support')
# one squad normally; 3rd Company raises to two
c=add_constraint(sonic,'r52-ec-sonic-hss-roster-max','max',1,'roster')
mods=ensure(sonic,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':'r52-ec-sonic-hss-third-max','type':'set','value':'2','field':c.get('id')}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'force','childId':third.get('id'),'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
hide_if_missing(sonic,'legion-iii'); hide_if_missing(sonic,'allegiance-traitor')
sg=group(sonic,'r52-ec-sonic-hss-weapons','Sonic Weapons — up to four',4); option(sg,'r52-ec-sonic-hss-blaster','Sonic Blaster',15,4); option(sg,'r52-ec-sonic-hss-siren','Doom Siren',20,4); option(sg,'r52-ec-sonic-hss-blastmaster','Blastmaster',35,4)
pg=group(sonic,'r52-ec-sonic-hss-special','Emperor\'s Children Upgrades'); option(pg,'r52-ec-sonic-hss-fearless','Perfect Cacophony — Fearless',20,1,'May be selected when the majority of surviving models in the squad are equipped with Sonic Weapons.')
add_rule(sonic,'r52-ec-sonic-hss-rule','Sonic Weaponry','TRAITOR ONLY. This squad selects up to four Sonic Weapons instead of selecting weapons from its normal Heavy Weapon options. Normally only one such Heavy Support Squad may be selected; 3rd Company Elite permits up to two.')
top.append(sonic)

# One Praetor or Centurion may carry ONE Sonic Blaster or Doom Siren. Build as one shared roster-limited package.
sonic_char=ET.SubElement(shared,C('selectionEntry'),{'id':'r52-ec-sonic-character','name':'Sonic Weaponry (one Praetor or Centurion per army)','type':'upgrade','hidden':'false','import':'true'}); add_constraint(sonic_char,'r52-ec-sonic-character-parent','max',1); add_constraint(sonic_char,'r52-ec-sonic-character-roster','max',1,'roster'); cg=group(sonic_char,'r52-ec-sonic-character-choice','Choose one Sonic Weapon',1); option(cg,'r52-ec-sonic-character-blaster','Sonic Blaster',15); option(cg,'r52-ec-sonic-character-siren','Doom Siren',20); add_rule(sonic_char,'r52-ec-sonic-character-rule','Restriction','TRAITOR ONLY. One Emperor\'s Children Praetor or Centurion in the army may carry one Sonic Weapon.')
for uid in ('hq-praetor','hq-centurion'):
    u=by_id(uid)
    if u is None:continue
    # Put the linked package into a clear EC group.
    ag=group(u,'r52-'+uid+'-ec-armoury','Emperor\'s Children Armoury')
    ls=ensure(ag,'entryLinks'); l=ET.SubElement(ls,C('entryLink'),{'id':'r52-'+uid+'-ec-sonic','name':sonic_char.get('name'),'type':'selectionEntry','targetId':sonic_char.get('id'),'hidden':'false','import':'true'}); add_constraint(l,l.get('id')+'-max','max',1)
    # Hide this group unless EC + Traitor.
    hide_if_missing(ag,'legion-iii'); hide_if_missing(ag,'allegiance-traitor')

# 3RD COMPANY ELITE: Kakophoni become compulsory-capable Troops and gain Relentless.
if ka is not None:
    kt=deepcopy(ka); rewrite_ids(kt,'r52-ec-third-kako-'); kt.set('id','r52-ec-third-kakophoni-troops'); kt.set('name','Kakophoni Squad — 3rd Company Troops'); kt.set('hidden','false'); set_primary_cat(kt,'cat-troops','Troops'); hide_if_missing(kt,'legion-iii'); hide_if_missing(kt,'allegiance-traitor'); hide_if_missing(kt,third.get('id'),'force'); add_rule(kt,'r52-ec-third-kako-relentless','Relentless','CHOSEN OF VAIROSEAN: Kakophoni in a 3rd Company Elite Detachment gain Relentless. This Troops entry may fulfil compulsory Troops selections.'); top.append(kt)
    add_rule(ka,'r52-ec-kako-third-relentless','3rd Company Elite','If this Detachment uses the 3rd Company Elite Rite of War, this Kakophoni Squad gains Relentless.')

# 3rd Company Sonic Assault: real repeatable +2/model purchase on eligible power/artificer-armoured Infantry.
eligible=['tactical-unit','assault-unit','breacher-unit','veteran-unit','destroyer-unit','fa-seeker',ids['pal'],ids['kako'],ids['sun']]
for uid in eligible:
    u=by_id(uid)
    if u is None:continue
    g=group(u,'r52-'+uid+'-third-shrieker','3rd Company Elite — Sonic Assault')
    s=option(g,'r52-'+uid+'-third-shrieker-model','Sonic Shrieker — select once per model in the unit',2,20,'Every eligible model in the unit must purchase this upgrade. This option is available only while using 3rd Company Elite and follows the normal Sonic Shrieker rules.')
    hide_if_missing(g,'legion-iii'); hide_if_missing(g,'allegiance-traitor'); hide_if_missing(g,third.get('id'),'force')

# Clean Rite text: retain source rule but add concise builder-facing implementation notes to the Rite itself.
add_rule(third,'r52-ec-third-builder','New Recruit Effects','Kakophoni are available as compulsory-capable Troops and gain Relentless; eligible Power/Artificer Armoured Infantry gain per-model Sonic Shrieker purchases; up to two Sonic Weaponry Heavy Support Squads may be selected. Army requirements from the Rite still apply: Traitor only, at least one Kakophoni, qualifying Warlord, and no more than one Fortification.')
add_rule(maru,'r52-ec-maru-builder','New Recruit Effects','The army may include no more than two Heavy Support choices. Hidden Blade deployment, arrival turn/edge and Killing Stroke are resolved during play as described by the Rite.')

# Keep the existing Rev43 Maru Heavy Support maximum if present; add it if absent.
def gst_set_category_max(name_contains,value,selector,mid):
    q=name_contains.lower(); link=next((e for e in gr.iter(G('categoryLink')) if q in (e.get('name') or '').lower()),None)
    if link is None:return False
    cons=link.find(G('constraints')); target=None
    if cons is not None:
        target=next((x for x in cons.findall(G('constraint')) if x.get('type')=='max'),None)
    if target is None:return False
    mods=link.find(G('modifiers'))
    if mods is None:mods=ET.SubElement(link,G('modifiers'))
    if any(x.get('id')==mid for x in mods.findall(G('modifier'))):return True
    m=ET.SubElement(mods,G('modifier'),{'id':mid,'type':'set','value':str(value),'field':target.get('id')}); cs=ET.SubElement(m,G('conditions')); ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'}); return True
gst_set_category_max('Heavy Support',2,maru.get('id'),'r52-ec-maru-heavy-max')
gst_set_category_max('Fortification',1,third.get('id'),'r52-ec-third-fort-max')

# Update final EC Legion reference rule text if a Legion III rule block is present.
for e in cr.iter(C('rule')):
    nm=(e.get('name') or '').lower()
    if nm in ('sons of the phoenix','have pride in your colours'):
        parent=next((p for p in cr.iter() if e in list(p)),None)
        if parent is not None:parent.remove(e)
# Add final special-rule references to the Legion III selector.
leg=by_id('legion-iii')
if leg is not None:
    add_rule(leg,'r52-ec-exemplars','Exemplars of War','Emperor\'s Children units gain Crusader. During an Assault phase in which an Emperor\'s Children model charges, it gains +1 Initiative until the end of that Assault phase; this may combine with other Initiative modifiers.')
    add_rule(leg,'r52-ec-purity','Purity Above All','Any Legion Veteran Squad may upgrade its Legion Veteran Sergeant to an Apothecary for +25 points. In addition, up to one Legion Tactical Squad or Legion Assault Squad may upgrade its Legion Sergeant to an Apothecary for +25 points. The Apothecary gains a Narthecium and may purchase a Reductor for +5 points.')
    add_rule(leg,'r52-ec-martial','Martial Pride','Emperor\'s Children units may not voluntarily withdraw from close combat. If they win a close combat and all engaged enemy units retreat, they must Pursue if able and may not take a Restraint Test to Consolidate instead.')

# Revision/source update. Rev51 fixed New Recruit ingestion; preserve canonical default namespaces.
cr.set('revision','52'); cr.set('gameSystemRevision','22'); gr.set('revision','22')
comment=cr.find(C('comment'))
if comment is not None:comment.text='Revision 52: Emperor\'s Children cleanup — structured unit options, functional sonic weapon quantities, 3rd Company Elite roster effects and real character retinues.'
ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
ET.register_namespace('',GNS); gt.write(GST,encoding='UTF-8',xml_declaration=True)

# Update index.xml without namespace-prefix churn.
idx=INDEX.read_text(encoding='utf-8'); idx=re.sub(r'(dataType="gamesystem"[^>]*dataRevision=")\d+("/>)',r'\g<1>22\2',idx); idx=re.sub(r'(dataType="catalogue"[^>]*dataRevision=")\d+("/>)',r'\g<1>52\2',idx); INDEX.write_text(idx,encoding='utf-8')

# Hard validation.
cat_text=CAT.read_text(encoding='utf-8'); gst_text=GST.read_text(encoding='utf-8')
assert '<ns0:' not in cat_text and '<ns0:' not in gst_text
assert '<catalogue xmlns="http://www.battlescribe.net/schema/catalogueSchema"' in cat_text
assert '<gameSystem xmlns="http://www.battlescribe.net/schema/gameSystemSchema"' in gst_text
# Duplicate IDs / broken references across CAT+GST independently.
def validate(root,ns):
    ids=[e.get('id') for e in root.iter() if e.get('id')]; assert len(ids)==len(set(ids)), 'duplicate IDs'
    idset=set(ids); broken=[]
    for e in root.iter():
        for a in ('targetId','childId'):
            v=e.get(a)
            if v and v not in idset:
                # references into the game system are legal from catalogue
                if ns==CNS and v in {x.get('id') for x in gr.iter() if x.get('id')}:continue
                broken.append((e.get('id'),a,v))
    return broken
cb=validate(cr,CNS); gb=validate(gr,GNS)
assert not cb, f'broken CAT refs: {cb[:10]}'
assert not gb, f'broken GST refs: {gb[:10]}'
assert cr.get('revision')=='52' and cr.get('gameSystemRevision')=='22' and gr.get('revision')=='22'
note('Validation: canonical namespaces OK; duplicate IDs 0; broken references 0; CAT52/GST22 synchronized.')
note('Emperor\'s Children cleanup complete: Source Entry dumps removed; unique-unit options rebuilt; Sonic HSS quantity/allowance functional; 3rd Company Troops/Sonic Assault implemented; Lucius/Eidolon/Fulgrim retinues added.')
Path('inspection-r52-ec-cleanup.txt').write_text('\n'.join(REPORT)+'\n',encoding='utf-8')
