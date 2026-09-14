from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET
import re

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); INDEX=Path('index.xml')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()
top=cr.find(C('selectionEntries')); shared=cr.find(C('sharedSelectionEntries'))
assert top is not None and shared is not None

REPORT=[]
def note(s): REPORT.append(s); print(s)
def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def top_by_name(text):
    q=text.lower()
    return next((e for e in list(top) if q in (e.get('name') or '').lower()),None)
def ensure(p,tag):
    q=C(tag); x=p.find(q)
    if x is None:x=ET.SubElement(p,q)
    return x
def wipe(p,tag):
    x=p.find(C(tag))
    if x is not None:p.remove(x)
def add_constraint(e,id_,kind,val,scope='parent'):
    cs=ensure(e,'constraints')
    return ET.SubElement(cs,C('constraint'),{'id':id_,'type':kind,'value':str(val),'field':'selections','scope':scope,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_cost(e,v,id_=None):
    cs=ensure(e,'costs'); c=ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
    if id_:c.set('id',id_)
    return c
def set_points(e,v):
    cs=ensure(e,'costs')
    for c in list(cs):
        if c.get('typeId')=='pts' or c.get('name')=='Points':cs.remove(c)
    add_cost(e,v)
def add_rule(e,id_,name,text):
    rs=ensure(e,'rules'); r=ET.SubElement(rs,C('rule'),{'id':id_,'name':name,'hidden':'false'})
    ET.SubElement(r,C('description')).text=text
    return r
def remove_rule_named(e,name):
    rs=e.find(C('rules'))
    if rs is None:return 0
    n=0
    for r in list(rs):
        if (r.get('name') or '').strip().lower()==name.lower():
            rs.remove(r); n+=1
    if len(rs)==0:e.remove(rs)
    return n
def fixed(e,id_,name):
    ses=ensure(e,'selectionEntries')
    s=ET.SubElement(ses,C('selectionEntry'),{'id':id_,'name':name,'type':'upgrade','hidden':'false','import':'true','defaultAmount':'1'})
    add_constraint(s,id_+'-min','min',1); add_constraint(s,id_+'-max','max',1)
    return s
def group(e,id_,name,maxv=None):
    gs=ensure(e,'selectionEntryGroups')
    g=ET.SubElement(gs,C('selectionEntryGroup'),{'id':id_,'name':name,'hidden':'false','collective':'false','import':'true'})
    if maxv is not None:add_constraint(g,id_+'-max','max',maxv)
    return g
def option(g,id_,name,cost=0,maxv=1,rule=None):
    ses=ensure(g,'selectionEntries')
    s=ET.SubElement(ses,C('selectionEntry'),{'id':id_,'name':name,'type':'upgrade','hidden':'false','import':'true'})
    mx=add_constraint(s,id_+'-max','max',maxv); add_cost(s,cost,id_+'-pts')
    if rule:add_rule(s,id_+'-rule',name,rule)
    return s,mx
def link(group_or_entry,target,id_,name=None,maxv=1):
    t=by_id(target) if isinstance(target,str) else target
    assert t is not None,target
    ls=ensure(group_or_entry,'entryLinks')
    l=ET.SubElement(ls,C('entryLink'),{'id':id_,'name':name or t.get('name'),'type':'selectionEntry','targetId':t.get('id'),'hidden':'false','import':'true'})
    add_constraint(l,id_+'-max','max',maxv)
    return l
def rewrite_ids(node,prefix):
    mp={}
    for x in node.iter():
        if x.get('id'):mp[x.get('id')]=prefix+x.get('id')
    for x in node.iter():
        if x.get('id') in mp:x.set('id',mp[x.get('id')])
        for a in ('targetId','childId','field'):
            if x.get(a) in mp:x.set(a,mp[x.get(a)])
def clone_nested(src,newid,newname=None):
    c=deepcopy(src); rewrite_ids(c,newid+'-'); c.set('id',newid)
    if newname:c.set('name',newname)
    wipe(c,'categoryLinks'); wipe(c,'modifiers')
    return c
def set_primary_cat(e,target,name):
    wipe(e,'categoryLinks')
    cs=ET.SubElement(e,C('categoryLinks'))
    ET.SubElement(cs,C('categoryLink'),{'id':e.get('id')+'-cat','name':name,'targetId':target,'hidden':'false','primary':'true'})
def hide_if_missing(e,child,scope='roster'):
    mods=ensure(e,'modifiers')
    m=ET.SubElement(mods,C('modifier'),{'id':e.get('id')+'-hide-missing-'+child,'type':'set','value':'true','field':'hidden'})
    cs=ET.SubElement(m,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'lessThan','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def hide_if_present(e,child,scope='force'):
    mods=ensure(e,'modifiers')
    m=ET.SubElement(mods,C('modifier'),{'id':e.get('id')+'-hide-present-'+child,'type':'set','value':'true','field':'hidden'})
    cs=ET.SubElement(m,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def find_rite(substr):
    q=substr.lower()
    return next((e for e in cr.iter(C('selectionEntry')) if q in (e.get('name') or '').lower() and 'rite' in e.get('id','')),None)
def clean_options(e):
    wipe(e,'selectionEntryGroups')
    ses=e.find(C('selectionEntries'))
    if ses is not None:
        for s in list(ses):
            if (s.get('name') or '').strip().lower()!='additional model':ses.remove(s)
def additional(e,cost,maxv,label='Additional model'):
    ses=ensure(e,'selectionEntries')
    s=next((x for x in ses.findall(C('selectionEntry')) if (x.get('name') or '').strip().lower()=='additional model'),None)
    if s is None:
        s=ET.SubElement(ses,C('selectionEntry'),{'id':e.get('id')+'-additional','name':label,'type':'model','hidden':'false','import':'true'})
    s.set('name',label)
    wipe(s,'constraints'); add_constraint(s,s.get('id')+'-max','max',maxv)
    cs=ensure(s,'costs')
    for c in list(cs):
        if c.get('typeId')=='pts' or c.get('name')=='Points':cs.remove(c)
    add_cost(s,cost)
    return s
def scale_max(option_entry,constraint,add_id,base,max_add):
    mods=ensure(option_entry,'modifiers')
    for n in range(1,max_add+1):
        m=ET.SubElement(mods,C('modifier'),{'id':option_entry.get('id')+f'-scale-{n}','type':'set','value':str(base+n),'field':constraint.get('id')})
        cs=ET.SubElement(m,C('conditions'))
        ET.SubElement(cs,C('condition'),{'type':'atLeast','value':str(n),'field':'selections','scope':'parent','childId':add_id,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_summary(e,prefix,wargear,rules):
    for i,w in enumerate(wargear):fixed(e,f'{prefix}-fixed-{i}',w)
    for i,(n,t) in enumerate(rules):add_rule(e,f'{prefix}-rule-{i}',n,t)
def transport_group(e,id_,names):
    g=group(e,id_,'Dedicated Transport',1)
    for n in names:
        t=top_by_name(n)
        if t is not None:link(g,t,id_+'-'+re.sub('[^a-z0-9]+','-',n.lower()).strip('-'))
    return g
def add_slotless_retinue(owner,id_,choices):
    rg=group(owner,id_,'Retinue (does not occupy a separate FOC slot)',1); ses=ensure(rg,'selectionEntries')
    added=[]
    for label,src in choices:
        if src is not None:
            c=clone_nested(src,id_+'-'+re.sub('[^a-z0-9]+','-',label.lower()).strip('-'),label)
            ses.append(c); added.append(label)
    if added:add_rule(rg,id_+'-rule','Retinue',f"{owner.get('name')} may select one of: "+', '.join(added)+'. The selected unit occupies no separate Force Organisation slot.')
    return rg
def gate_two(e,legion,rite):
    e.set('hidden','true')
    mods=ensure(e,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':e.get('id')+'-show','type':'set','value':'false','field':'hidden'})
    cgs=ET.SubElement(m,C('conditionGroups')); cg=ET.SubElement(cgs,C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(cg,C('conditions'))
    for child,scope in ((legion,'roster'),(rite,'force')):
        ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Idempotent cleanup of this revision.
for p in list(cr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r57-'):p.remove(x)

hammer=find_rite('hammer of olympia'); ironfire=find_rite('ironfire')
assert hammer is not None and ironfire is not None
note(f'Rites: Hammer={hammer.get("id")} Ironfire={ironfire.get("id")}')

# Remove obsolete Rev43 loose IW armoury links from the units we rebuild.
for uid in ('hq-praetor','hq-centurion','tactical-unit','assault-unit','breacher-unit','veteran-unit','terminator-unit','fa-seeker','hs-heavy-support-squad'):
    u=by_id(uid)
    if u is None:continue
    for holder in [u,*list(u.findall('.//'+C('selectionEntryGroup')))]:
        ls=holder.find(C('entryLinks'))
        if ls is None:continue
        for l in list(ls):
            if l.get('id','').startswith('r43-') and ('iw-' in l.get('id','') or 'shrapnel' in (l.get('name') or '').lower() or 'servo' in (l.get('name') or '').lower() or 'bionics' in (l.get('name') or '').lower()):
                ls.remove(l)

# Locate all final-source Iron Warriors imported entries.
names={
'tyrant':'tyrant siege terminator squad','havoc':'iron havoc squad','dominator':'dominator cohort',
'circle':'iron circle domitar-ferrum maniple','narik':'nârik dreygur','golg':'erasmus golg',
'vhalen':'kyr vhalen','forrix':'forrix, first captain','kroeger':'kroeger, the bloody-handed',
'pert':'perturabo, the lord of iron'}
ids={}
for k,n in names.items():
    x=top_by_name(n)
    if x is None and k=='narik':x=top_by_name('dreygur')
    if x is None and k=='pert':x=top_by_name('perturabo')
    assert x is not None,f'Missing Iron Warriors entry: {n}'
    ids[k]=x.get('id')
note('Located final-source Iron Warriors entries: '+', '.join(f'{k}={v}' for k,v in ids.items()))

# Remove giant auto-imported source dumps.
removed=0
for e in list(top):
    if e.get('id','').startswith('r41-unit-iv-') or e.get('id') in ids.values():
        removed+=remove_rule_named(e,'Source Entry')
note(f'Removed {removed} Iron Warriors Source Entry dumps')

# Core armoury structured options.
def armoury_group_for(u,prefix,shrapnel=False,servo=False,bionics=False):
    g=group(u,prefix,'Iron Warriors Armoury')
    if shrapnel: option(g,prefix+'-shrapnel','Shrapnel Bolts',5,1,'Bolt Pistols, Bolters, Combi-Bolters, Storm Bolters, Heavy Bolters, Twin-linked Bolters and bolter components of Combi-Weapons carried by models in this unit gain Pinning. May not be combined with Special Issue Ammunition, Hellfire Rounds or another special ammunition type.')
    if servo: option(g,prefix+'-servo','Servo-Arm',30,1,'Follows the normal Servo-Arm rules in the Legiones Astartes Army List. A model equipped with a Jump Pack may not purchase a Servo-Arm.')
    if bionics: option(g,prefix+'-bionics','Bionics',5,1,'Iron Warriors Armoury price; otherwise follows the normal Bionics rules.')
    hide_if_missing(g,'legion-iv')
    return g

for uid in ('hq-praetor','hq-centurion'):
    u=by_id(uid)
    if u is not None:armoury_group_for(u,'r57-'+uid+'-iw',False,True,True)
for uid in ('tactical-unit','breacher-unit','veteran-unit','terminator-unit','fa-seeker','hs-heavy-support-squad'):
    u=by_id(uid)
    if u is not None:armoury_group_for(u,'r57-'+uid+'-iw',True,True,True)
u=by_id('assault-unit')
if u is not None:armoury_group_for(u,'r57-assault-unit-iw',True,False,True)

# TYRANT SIEGE TERMINATORS
ty=by_id(ids['tyrant']); clean_options(ty); set_points(ty,325); ad=additional(ty,65,5,'Additional Tyrant Siege Terminator')
g=group(ty,'r57-iw-tyrant-ranged','Ranged Weapon Replacements')
o,mx=option(g,'r57-iw-tyrant-foeblaster','Foeblaster boltgun — replace Storm bolter',5,5); scale_max(o,mx,ad.get('id'),5,5)
g=group(ty,'r57-iw-tyrant-melee','Melee Weapon Replacements',5)
gmx=g.find(C('constraints')).find(C('constraint')); scale_max(g,gmx,ad.get('id'),5,5)
for nm,cost in [('Power fist — replace Power weapon',5),('Chainfist — replace Power weapon',10)]:
    o,mx=option(g,'r57-iw-tyrant-'+('fist' if nm.startswith('Power') else 'chainfist'),nm,cost,5); scale_max(o,mx,ad.get('id'),5,5)
g=group(ty,'r57-iw-tyrant-master','Tyrant Siege Master'); option(g,'r57-iw-tyrant-harness','Grenade Harness',10)
transport_group(ty,'r57-iw-tyrant-transport',['Land Raider','Dreadclaw Drop Pod','Spartan Assault Tank'])
add_summary(ty,'r57-iw-tyrant',['Cataphractii Terminator Armour','Storm bolter','Power weapon','Cyclone Missile Launcher'],[
('Legiones Astartes (Iron Warriors)','This unit has Legiones Astartes (Iron Warriors).'),
('Coordinated Bombardment','When the squad fires its Cyclone Missile Launchers, it may re-roll one failed To Hit roll made with a Cyclone Missile Launcher during that Shooting phase. A model equipped with a Cyclone Missile Launcher may fire it in addition to its Storm bolter or Foeblaster boltgun in the same Shooting phase; both weapons must target the same enemy unit.')])

# IRON HAVOCS
hv=by_id(ids['havoc']); clean_options(hv); set_points(hv,140); ad=additional(hv,25,5,'Additional Iron Havoc')
g=group(hv,'r57-iw-havoc-heavy','Heavy Weapons',4)
for slug,nm,cost in [('hb','Heavy bolter — replace Bolter',10),('ml','Missile Launcher — replace Bolter',15),('ac','Autocannon — replace Bolter',20),('lc','Lascannon — replace Bolter',30)]: option(g,'r57-iw-havoc-'+slug,nm,cost,4)
g=group(hv,'r57-iw-havoc-squad','Squad Equipment')
for slug,nm,cost in [('krak','Krak grenades — select once per squad model',2),('tank','Tank Hunters — select once per squad model',3)]:
    o,mx=option(g,'r57-iw-havoc-'+slug,nm,cost,5,'The entire squad must take this upgrade; select one for every model currently in the squad.'); scale_max(o,mx,ad.get('id'),5,5)
g=group(hv,'r57-iw-havoc-sergeant','Iron Havoc Sergeant')
option(g,'r57-iw-havoc-signum','Signum',15)
add_rule(g,'r57-iw-havoc-armoury','Sergeant Armoury','The Iron Havoc Sergeant may select up to 50 points of permitted weapons and wargear from the Space Marine Armoury.')
add_summary(hv,'r57-iw-havoc',['Power Armour','Bolter','Bolt pistol','Frag grenades'],[
('Legiones Astartes (Iron Warriors)','This unit has Legiones Astartes (Iron Warriors).'),
('Enhanced Targeting','Iron Havocs have Ballistic Skill 5, as shown in their profile.')])
armoury_group_for(hv,'r57-iw-havoc-armoury-group',True,False,False)

# DOMINATOR COHORT
do=by_id(ids['dominator']); clean_options(do); set_points(do,250); ad=additional(do,50,5,'Additional Dominator')
g=group(do,'r57-iw-dom-melee','Melee Weapon Replacement')
o,mx=option(g,'r57-iw-dom-chainfist','Chainfist — replace Thunder Hammer',0,5); scale_max(o,mx,ad.get('id'),5,5)
g=group(do,'r57-iw-dom-ranged','Ranged Weapon Replacements',5)
gmx=g.find(C('constraints')).find(C('constraint')); scale_max(g,gmx,ad.get('id'),5,5)
for slug,nm,cost in [('volk','Volkite charger — replace Combi-bolter',10),('cf','Combi-flamer — replace Combi-bolter',10),('cm','Combi-meltagun — replace Combi-bolter',15),('cp','Combi-plasma gun — replace Combi-bolter',15)]:
    o,mx=option(g,'r57-iw-dom-'+slug,nm,cost,5); scale_max(o,mx,ad.get('id'),5,5)
hg=group(do,'r57-iw-dom-heavy','Heavy Weapon (one per five models)',1); hmax=hg.find(C('constraints')).find(C('constraint'))
mods=ensure(hg,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':'r57-iw-dom-heavy-scale','type':'set','value':'2','field':hmax.get('id')}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'5','field':'selections','scope':'parent','childId':ad.get('id'),'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
for slug,nm,cost in [('hf','Heavy flamer — replace Combi-bolter',10),('ra','Reaper autocannon — replace Combi-bolter',15),('mm','Multi-Melta — replace Combi-bolter',15)]: option(hg,'r57-iw-dom-heavy-'+slug,nm,cost,2)
g=group(do,'r57-iw-dom-warden','Dominator Warden'); option(g,'r57-iw-dom-harness','Grenade Harness',10)
transport_group(do,'r57-iw-dom-transport',['Land Raider','Dreadclaw Drop Pod','Spartan Assault Tank'])
add_summary(do,'r57-iw-dom',['Cataphractii Terminator Armour','Combi-bolter','Thunder Hammer'],[
('Legiones Astartes (Iron Warriors)','This unit has Legiones Astartes (Iron Warriors).'),
('Stubborn','This unit has Stubborn.'),
('Hatred (Battle-Automata)','Use the normal ProHammer Hatred special rule when fighting enemy Battle-Automata.'),
('Those Once Honoured',"One Dominator Cohort may be selected as Perturabo's personal retinue. If selected in this manner, the squad does not occupy an Elites choice.")])
armoury_group_for(do,'r57-iw-dom-armoury',True,False,False)

# IRON CIRCLE
ic=by_id(ids['circle']); clean_options(ic); set_points(ic,205); additional(ic,205,5,'Additional Domitar-Ferrum')
add_summary(ic,'r57-iw-circle',['Olympia-pattern Bolt Cannon','Graviton Maul','Karceri Battle Shield'],[
('Cybernetica Cortex','This unit has Cybernetica Cortex.'),
('Reactor Blast','This unit has Reactor Blast.'),
('Crusader','This unit has Crusader.'),
('Moving Bulwark','If a Domitar-Ferrum is in base contact with another friendly Domitar-Ferrum from the same unit, both improve their Invulnerable Save from 5+ to 4+. The bonus is lost as soon as the models are no longer in base contact.'),
('Iron Warriors Construct','The Iron Circle counts as an Iron Warriors unit for rules which specifically affect friendly Iron Warriors units. It does not possess the Legiones Astartes special rule.'),
('Karceri Battle Shield','The Karceri Battle Shield grants the Domitar-Ferrum its 5+ Invulnerable Save; this is already included in its profile.'),
('Graviton Maul','Power Weapon. Attacks are resolved at Strength 10 and have Concussive.'),
('Olympia-pattern Bolt Cannon','Range 36", Strength 5, AP4, Heavy 5, Pinning.')])

# CHARACTERS
char_data={
'narik':(140,['Artificer Armour','Refractor Field','Graviton Gauntlet','Master-crafted Bolt Pistol','Frag grenades','Cortex Controller'],[
('Legiones Astartes (Iron Warriors)','This model has Legiones Astartes (Iron Warriors).'),('Independent Character','Nârik Dreygur is an Independent Character.'),('Feel No Pain (5+)','Nârik Dreygur has Feel No Pain (5+).'),('Battlesmith','During the Shooting phase, instead of firing a weapon, Dreygur may attempt to repair a friendly damaged Vehicle with which he is in base contact or embarked upon. On a 5+, remove one Engine Damaged, Weapon Destroyed or Immobilised result.'),('Master of Automata','Dreygur may join a friendly unit of Battle-Automata despite the normal restrictions on Independent Characters joining Monstrous Creatures. While joined, it may use his Leadership for Leadership tests.'),('Cortex Controller','Friendly Battle-Automata with a model within 6" automatically pass any Command Uplink or equivalent control test.'),('Graviton Gauntlet','Power Weapon. Strength 8, Unwieldy, Concussive.')]),
'golg':(175,['Cataphractii Terminator Armour','Extricator','Combi-meltagun','Nuncio Vox'],[
('Legiones Astartes (Iron Warriors)','This model has Legiones Astartes (Iron Warriors).'),('Independent Character','Erasmus Golg is an Independent Character.'),('Master of the Legion','Erasmus Golg has Master of the Legion.'),('Stubborn','Erasmus Golg has Stubborn.'),('Terminator Attack',"If Erasmus Golg is the army's Warlord, Legion Terminator Squads may be selected as Troops choices. They may not fulfil compulsory Troops selections."),('Extricator','Master-crafted Power Weapon. Strength 10, Unwieldy, Armourbane.')]),
'vhalen':(195,['Artificer Armour','Iron Halo','Aegeas','Volkite Charger','Servo-Arm','Cortex Controller','Frag grenades','Melta bombs'],[
('Legiones Astartes (Iron Warriors)','This model has Legiones Astartes (Iron Warriors).'),('Independent Character','Kyr Vhalen is an Independent Character.'),('Master of the Legion','Kyr Vhalen has Master of the Legion.'),('Feel No Pain (5+)','Kyr Vhalen has Feel No Pain (5+).'),('Battlesmith',"Instead of firing in the Shooting phase, Vhalen may repair a friendly damaged Vehicle in base contact or embarked upon. His Servo-Arm improves the normal 5+ repair to 4+. On success remove one Engine Damaged, Weapon Destroyed or Immobilised result."),('Shatterblade','Vhalen and any unit he joins have Stubborn.'),('Cortex Controller','Friendly Battle-Automata with a model within 6" automatically pass any Command Uplink or equivalent control test.'),('Aegeas','Master-crafted Rending Weapon, +2 Strength; attacks also have Blind.')]),
'forrix':(190,['Cataphractii Terminator Armour','Master-crafted Power Fist','Combi-meltagun'],[
('Legiones Astartes (Iron Warriors)','This model has Legiones Astartes (Iron Warriors).'),('Independent Character','Forrix is an Independent Character.'),('Master of the First Grand Battalion','Forrix and any Iron Warriors unit he has joined may re-roll failed Morale tests.'),('Siege Commander','After deployment but before the first turn, nominate one non-Vehicle Iron Warriors Heavy Support unit. It gains Tank Hunters for the battle.')]),
'kroeger':(140,['Artificer Armour','Refractor Field','Power Weapon','Bolt pistol','Frag grenades'],[
('Legiones Astartes (Iron Warriors)','This model has Legiones Astartes (Iron Warriors).'),('Independent Character','Kroeger is an Independent Character.'),('The Bloody-Handed','Kroeger has Furious Charge. Any Iron Warriors unit he has joined also gains Furious Charge while he remains part of the unit.'),('No Surrender',"Whenever Kroeger and his unit win close combat and one or more defeated enemy units Retreat, Kroeger's unit must Pursue if legally permitted. It may not choose to Consolidate instead.")])}
for key,(pts,wg,rr) in char_data.items():
    e=by_id(ids[key]); clean_options(e); set_points(e,pts); add_summary(e,'r57-iw-'+key,wg,rr)
    if key in ('narik','vhalen','kroeger'):
        g=group(e,'r57-iw-'+key+'-options','Options'); option(g,'r57-iw-'+key+'-krak','Krak grenades',2)

# Character retinues.
term_template=by_id('hq-praetor-ret-termcommand') or by_id('hq-centurion-ret-termcommand')
command_template=by_id('hq-centurion-ret-command') or by_id('hq-praetor-ret-command')
honour_template=by_id('hq-praetor-ret-honour')
assert term_template is not None and command_template is not None and honour_template is not None
add_slotless_retinue(by_id(ids['golg']),'r57-iw-golg-retinue',[('Legion Terminator Command Squad',term_template),('Tyrant Siege Terminator Squad',ty),('Dominator Cohort',do)])
add_slotless_retinue(by_id(ids['forrix']),'r57-iw-forrix-retinue',[('Legion Terminator Command Squad',term_template),('Tyrant Siege Terminator Squad',ty)])
add_slotless_retinue(by_id(ids['kroeger']),'r57-iw-kroeger-retinue',[('Legion Command Squad',command_template)])

# Golg Warlord toggle + Terminator Troops clone.
golg=by_id(ids['golg'])
g=group(golg,'r57-iw-golg-warlord-group','Terminator Attack',1)
warlord,_=option(g,'r57-iw-golg-warlord','Erasmus Golg is the army Warlord',0,1,'Enables Legion Terminator Squads as non-compulsory Troops choices.')
term=by_id('terminator-unit')
if term is not None:
    clone=deepcopy(term); rewrite_ids(clone,'r57-iw-golg-term-troops-'); clone.set('id','r57-iw-golg-term-troops'); clone.set('name','Legion Terminator Squad — Terminator Attack'); set_primary_cat(clone,'cat-troops','Troops'); clone.set('hidden','false'); wipe(clone,'modifiers'); hide_if_missing(clone,'legion-iv'); hide_if_missing(clone,warlord.get('id'))
    add_rule(clone,'r57-iw-golg-term-rule','Terminator Attack',"Available only while Erasmus Golg is the army's Warlord. This unit is a Troops choice but may not fulfil a compulsory Troops selection.")
    top.append(clone)

# PERTURABO
pe=by_id(ids['pert']); clean_options(pe); set_points(pe,500)
add_summary(pe,'r57-iw-pert',['The Logos','Forgebreaker','Logos Array','Siege Bombardments'],[
('Primarch','Perturabo has the Primarch special rule.'),('Legiones Astartes (Iron Warriors)','Perturabo has Legiones Astartes (Iron Warriors).'),
('The Logos','Counts as Primarch Armour and incorporates a Nuncio Vox. Once during each friendly Shooting phase, one friendly Iron Warriors Heavy Support unit with at least one model within 12" of Perturabo may re-roll one failed shooting To Hit roll.'),
('Forgebreaker','Master-crafted Thunder Hammer with Armourbane.'),
('Logos Array','Range 30", Strength 6, AP3, Assault 6, Twin-linked, Shred, Pinning.'),
('Siege Bombardments','After deployment zones are determined but before deployment, nominate two terrain features. For each choose Lance Strike (Unlimited, S10 AP1, Ordnance 1, Blast), Melta Torpedo (Unlimited, S8 AP3, Ordnance 1, Blast, Armourbane), or Barrage Bomb (Unlimited, S6 AP4, Ordnance 1, Blast). The two bombardments are one Reserve entry; once available, resolve one plotted bombardment in each subsequent friendly Shooting phase. Place the Blast marker within the nominated terrain feature and scatter normally, doubling arrow scatter; a Hit still scatters by the distance rolled in the small-arrow direction. Counts as Ordnance Barrage and causes Pinning.'),
('Lord of Iron','Perturabo has Tank Hunters and Siege Masters. Any unit he joins gains Tank Hunters while he remains part of it.'),
('Calculated Destruction','Before deployment, nominate one enemy Vehicle, Fortification or Lord of War. Perturabo may re-roll failed Armour Penetration rolls against it for the battle.'),
('Battlefield Calculation','After both armies deploy but before the first turn, nominate one friendly Iron Warriors unit. Reposition it up to 6", remaining entirely within its normal deployment zone; this cannot be used to embark or disembark.')])
add_slotless_retinue(pe,'r57-iw-pert-retinue',[('Legion Honour Guard Squad',honour_template),('Legion Terminator Command Squad',term_template),('Dominator Cohort',do)])

# Rite text and mechanics.
for r in (hammer,ironfire):
    remove_rule_named(r,'Source Entry')

add_rule(hammer,'r57-iw-hammer-iron-line','The Iron Line',"Compulsory Troops choices must be Legion Tactical Squads or Legion Breacher Siege Squads. Compulsory Troops gain Shrapnel Bolts for free.")
add_rule(hammer,'r57-iw-hammer-hail','Hail of Fire','Iron Warriors Tactical Squads and Breacher Siege Squads with Shrapnel Bolts may charge after firing Rapid Fire weapons. A unit doing so receives no +1 Attack for charging. A unit that used Fury of the Legion that turn may not benefit.')
add_rule(hammer,'r57-iw-hammer-fury','Fury of Olympia','Models equipped with Shrapnel Bolts may re-roll To Hit rolls of 1 when firing those weapons at an enemy within 12". Does not apply to Snap Shots.')
add_rule(hammer,'r57-iw-hammer-armour','Armoured Resolve','Iron Warriors Predator Strike Squadrons, Vindicator Siege Tank Squadrons, Land Raiders and Spartan Assault Tanks ignore Crew Shaken and Crew Stunned results. Other Vehicle Damage results apply normally.')
add_rule(hammer,'r57-iw-hammer-limits','Limitations',"The Warlord must possess Master of the Legion. Compulsory Troops must be Tactical Squads or Breacher Siege Squads. No Iron Warriors unit may deploy using Deep Strike, and units required to enter by Deep Strike may not be selected.")

for src_id,label,newid in [('tactical-unit','Legion Tactical Squad — Hammer Compulsory','r57-iw-hammer-tactical'),('breacher-unit','Legion Breacher Siege Squad — Hammer Compulsory','r57-iw-hammer-breacher')]:
    src=by_id(src_id)
    if src is not None:
        c=deepcopy(src); rewrite_ids(c,newid+'-'); c.set('id',newid); c.set('name',label); c.set('hidden','false'); wipe(c,'modifiers'); gate_two(c,'legion-iv',hammer.get('id'))
        g=group(c,newid+'-rite','Hammer of Olympia',1); option(g,newid+'-shrapnel','Shrapnel Bolts — free for compulsory Troops',0,1,'This free option represents The Iron Line and is only for a compulsory Troops selection.')
        add_rule(c,newid+'-rule','Compulsory Troops','Use this version for one of the army’s compulsory Troops selections under The Hammer of Olympia.')
        top.append(c)

for e in list(top):
    nm=(e.get('name') or '').lower()
    if 'drop pod' in nm:
        mods=ensure(e,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':'r57-iw-hammer-hide-'+e.get('id'),'type':'set','value':'true','field':'hidden'})
        cgs=ET.SubElement(m,C('conditionGroups')); cg=ET.SubElement(cgs,C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(cg,C('conditions'))
        for child,scope in (('legion-iv','roster'),(hammer.get('id'),'force')):
            ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

add_rule(ironfire,'r57-iw-ironfire-column','Artillery Column','One Legion Artillery Tank Squadron may be selected as a non-compulsory Troops choice. It does not occupy Heavy Support, may not fulfil compulsory Troops, and is not Scoring unless it would normally be. The normal 0–1 restriction still applies.')
add_rule(ironfire,'r57-iw-ironfire-rolling','Rolling Bombardment','When an Iron Warriors Barrage weapon fires at a point within 12" of a friendly Iron Warriors unit, reduce scatter from 2D6" to D6". After resolving it, place an Ironfire Marker at the final centre point of the Blast marker.')
add_rule(ironfire,'r57-iw-ironfire-walking','Walking the Fire','A later Iron Warriors Barrage weapon does not scatter if its initial target point is within 18" of an Ironfire Marker and within 6" of a friendly Iron Warriors unit. After resolving, place a new Ironfire Marker. If the Shooting phase ends without placing a new Ironfire Marker, remove all Ironfire Markers.')
add_rule(ironfire,'r57-iw-ironfire-ride','Ride the Ironfire','Iron Warriors Infantry units with at least one model within 6" of an Ironfire Marker gain Fearless while that condition remains true.')
add_rule(ironfire,'r57-iw-ironfire-limits','Limitations',"The Warlord must possess Master of the Legion. The army must contain at least one Barrage weapon. If the mission has Attacker/Defender roles, the Iron Warriors must be the Attacker. The army may not include a Fortification.")

art=top_by_name('Legion Artillery Tank Squadron') or top_by_name('Artillery Tank Squadron')
if art is not None:
    c=deepcopy(art); rewrite_ids(c,'r57-iw-ironfire-artillery-'); c.set('id','r57-iw-ironfire-artillery'); c.set('name','Legion Artillery Tank Squadron — Artillery Column'); set_primary_cat(c,'cat-troops','Troops'); c.set('hidden','false'); wipe(c,'modifiers'); gate_two(c,'legion-iv',ironfire.get('id'))
    add_rule(c,'r57-iw-ironfire-artillery-rule','Artillery Column','Non-compulsory Troops. Does not count as Scoring unless it normally would. The normal 0–1 Artillery Tank Squadron restriction still applies.')
    top.append(c)
    hide_if_present(art,ironfire.get('id'),'force')
    note('Ironfire Artillery Column Troops clone created.')
else:
    note('WARNING: Legion Artillery Tank Squadron not found; Rite text added but role clone omitted.')

leg=by_id('legion-iv')
if leg is not None:
    add_rule(leg,'r57-iw-siege','Siege Masters','Non-vehicle Iron Warriors receive +1 Armour Penetration against Fortifications, Buildings, Bunkers, Tank Traps and other immobile AV structures. Iron Warriors trigger enemy Minefields only on a 6. An Iron Warriors unit in a friendly Fortification or Bunker gains Stubborn; no benefit in an enemy-starting Fortification.')
    add_rule(leg,'r57-iw-steel','An Army of Steel and Wrath','Once per detachment, exchange two Fast Attack selections for one additional Heavy Support selection. On the standard chart this gives 0–1 Fast Attack and 0–4 Heavy Support.')
    add_rule(leg,'r57-iw-stubborn','Stubborn Resolve','If a mission uses variable game length and would end, the opposing player may demand one additional complete game turn; on a 3+ play it. This roll is made only once and the battle ends automatically after that extra turn. No effect after a mission-ending objective/action has already occurred.')
    add_rule(leg,'r57-iw-prelim','Preliminary Bombardment','Only in missions already using Preliminary Bombardment: gain one additional bombardment roll per full 500 points in the army. Assign all additional rolls before any are made; multiple may target the same eligible target and are rolled together.')

# Revision bump: CAT only. GST stays revision 26.
cr.set('revision','57')
comment=cr.find(C('comment'))
if comment is not None:comment.text='Revision 57: Iron Warriors cleanup — final-source structured units, armoury, Rites, retinues, Golg Terminator Attack and Ironfire Artillery Column.'
ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
idx=INDEX.read_text(encoding='utf-8')
idx=re.sub(r'(dataType="catalogue"[^>]*dataRevision=")\d+("/>)',r'\g<1>57\2',idx)
INDEX.write_text(idx,encoding='utf-8')

# Validation.
raw=CAT.read_text(encoding='utf-8')
assert '<ns0:' not in raw and raw.lstrip().startswith('<?xml')
assert cr.get('revision')=='57'
ids_all=[x.get('id') for x in cr.iter() if x.get('id')]
dupes=sorted({x for x in ids_all if ids_all.count(x)>1})
assert not dupes,f'duplicate IDs: {dupes[:20]}'
idset=set(ids_all); ext_ids={x.get('id') for x in gr.iter() if x.get('id')}; all_ids=idset|ext_ids
broken=[]
for l in cr.iter(C('entryLink')):
    if l.get('targetId') not in all_ids:broken.append((l.get('id'),l.get('targetId')))
assert not broken,f'broken CAT entryLinks: {broken[:10]}'
for e in ids.values():
    x=by_id(e); assert x is not None
    assert not any((r.get('name') or '').lower()=='source entry' for r in x.findall('.//'+C('rule'))),x.get('name')
assert by_id('r57-iw-golg-term-troops') is not None
assert by_id('r57-iw-ironfire-artillery') is not None or art is None
note('Validation: canonical CAT namespace; duplicate IDs 0; broken catalogue entryLinks 0; CAT57; GST/game-system revision preserved.')
note('Iron Warriors cleanup complete: Source Entry dumps removed, all final unique units/characters structured, armoury cleaned, Hammer/Ironfire mechanics added, retinues added, Golg Terminator Attack and Ironfire Artillery Column functional.')
Path('inspection-r57-iron-warriors-cleanup.txt').write_text('\n'.join(REPORT)+'\n',encoding='utf-8')
