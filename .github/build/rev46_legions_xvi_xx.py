from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET
import re

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ET.register_namespace('',CNS); ET.register_namespace('',GNS)
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()
top=cr.find(C('selectionEntries')); shared=cr.find(C('sharedSelectionEntries')); assert top is not None and shared is not None

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def cby(i): return byid(cr,i)
def gby(i): return byid(gr,i)
def ensure(p,t,ns=CNS):
    q=f'{{{ns}}}{t}'; x=p.find(q)
    if x is None:x=ET.SubElement(p,q)
    return x
def add_cost(e,v): ET.SubElement(ensure(e,'costs'),C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def add_constraint(e,id_,typ,val,scope='parent',children='true'):
    return ET.SubElement(ensure(e,'constraints'),C('constraint'),{'id':id_,'type':typ,'value':str(val),'field':'selections','scope':scope,'shared':'true','includeChildSelections':children,'includeChildForces':'false'})
def add_rule(e,id_,name,text):
    r=ET.SubElement(ensure(e,'rules'),C('rule'),{'id':id_,'name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=text
def add_conditions(e,hide,conds,id_=None):
    a={'type':'set','value':'true' if hide else 'false','field':'hidden'}
    if id_:a['id']=id_
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),a); gs=ET.SubElement(m,C('conditionGroups')); g=ET.SubElement(gs,C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(g,C('conditions'))
    for typ,val,scope,ch in conds:ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':ch,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def gate(e,legion,extra=()): e.set('hidden','true'); add_conditions(e,False,[('atLeast',1,'roster',legion),*extra])
def shared_up(id_,name,pts,text,roster_max=None,maxv=1):
    e=ET.SubElement(shared,C('selectionEntry'),{'id':id_,'name':name,'type':'upgrade','hidden':'false','import':'true'}); add_cost(e,pts); add_constraint(e,id_+'-max','max',maxv)
    if roster_max is not None:add_constraint(e,id_+'-rmax','max',roster_max,'roster')
    add_rule(e,id_+'-rule',name,text); return e
def link(uid,target,id_,legion,extra=(),name=None,maxv=1):
    u=cby(uid);t=cby(target)
    if u is None or t is None:return None
    l=ET.SubElement(ensure(u,'entryLinks'),C('entryLink'),{'id':id_,'name':name or t.get('name'),'type':'selectionEntry','targetId':target,'hidden':'true','import':'true'});add_constraint(l,id_+'-max','max',maxv);gate(l,legion,extra);return l
def gst_set(link,constraint_id,val,selector,id_):
    l=gby(link); assert l is not None
    m=ET.SubElement(ensure(l,'modifiers',GNS),G('modifier'),{'id':id_,'type':'set','value':str(val),'field':constraint_id});cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def find_top(text):
    t=text.lower();return next((e for e in list(top) if t in (e.get('name') or '').lower()),None)
def rewrite_ids(n,prefix):
    mp={}
    for e in n.iter():
        if e.get('id'):mp[e.get('id')]=prefix+e.get('id')
    for e in n.iter():
        if e.get('id') in mp:e.set('id',mp[e.get('id')])
    for e in n.iter():
        for a in ('targetId','childId','field'):
            if e.get(a) in mp:e.set(a,mp[e.get(a)])
def prune_missing(n):
    valid={e.get('id') for e in cr.iter() if e.get('id')}
    for p in list(n.iter()):
        for x in list(p):
            if x.get('targetId') and x.get('targetId') not in valid:p.remove(x)
def set_primary_cat(e,target,name):
    old=e.find(C('categoryLinks'))
    if old is not None:e.remove(old)
    cs=ET.SubElement(e,C('categoryLinks'));ET.SubElement(cs,C('categoryLink'),{'id':e.get('id')+'-cat','targetId':target,'name':name,'hidden':'false','primary':'true'})
def hide_if(entry,selector,id_):
    e=cby(entry) if isinstance(entry,str) else entry
    if e is None:return
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':id_,'type':'set','value':'true','field':'hidden'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'force','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Clean this revision pass if re-run.
for p in list(cr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r46-'):p.remove(x)
for p in list(gr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r46-'):p.remove(x)

# XVI — SONS OF HORUS
soh_bane_ic=shared_up('r46-soh-banestrike-character','Banestrike Ammunition',5,'+5 points per eligible model. For Bolter/Foeblaster Boltgun/Combi-Bolter/Storm Bolter/Combi-Weapon: range becomes 18”, AP4, retains normal shots/type, and natural To Wound rolls of 6 are AP3. Cannot combine with Special Issue Ammunition or another ammunition type.')
soh_bane_unit=shared_up('r46-soh-banestrike-model','Banestrike Ammunition — eligible model',5,'Sons of Horus Seeker or Justaerin unit. Every eligible model in the squad must purchase the upgrade; models without an eligible bolt weapon neither pay nor benefit. 18”/AP4 with Banestrike; natural To Wound 6 is AP3.',maxv=20)
soh_blade=shared_up('r46-soh-culling-blade','Cthonian Culling Blade',10,'Sons of Horus Independent Character or squad Sergeant. User Strength, Rending (5+); against Vehicles Rending triggers only on a natural Armour Penetration roll of 6. Does not count as a Power Weapon.')
soh_chain=shared_up('r46-soh-chainaxe','Chainaxe',4,'Sons of Horus Character eligible to select a Close Combat Weapon. Uses the normal Chainaxe rules from the Legiones Astartes Army List.')
soh_trans_ic=shared_up('r46-soh-transponder-character','Teleportation Transponders',10,'Sons of Horus Independent Character wearing Terminator Armour. Grants Deep Strike even if the mission would not normally permit it.')
soh_trans_unit=shared_up('r46-soh-transponder-unit','Teleportation Transponders',15,'Sons of Horus unit composed entirely of models in Terminator Armour. Grants Deep Strike even if the mission would not normally permit it.')
for uid in ['hq-praetor','hq-centurion']:
    for it in [soh_bane_ic,soh_blade,soh_chain,soh_trans_ic]:link(uid,it.get('id'),f'r46-{uid}-{it.get("id")}','legion-xvi')
for uid in ['fa-seeker','r41-unit-xvi-0-justaerin-terminator-squad']:
    link(uid,soh_bane_unit.get('id'),f'r46-{uid}-soh-banestrike','legion-xvi',maxv=20)
for uid in ['terminator-unit','r41-unit-xvi-0-justaerin-terminator-squad']:
    link(uid,soh_trans_unit.get('id'),f'r46-{uid}-soh-trans','legion-xvi')
# The Long March's Terminator non-compulsory Troops role and Black Reaving Reavers are already materialised by Revision 42.

# XVII — WORD BEARERS
wb_crozius=shared_up('r46-wb-accursed-crozius','Accursed Crozius',40,'Word Bearers Praetor or Centurion. User Strength, Power Weapon. Grants a 4+ Invulnerable Save and counts as a Personal Icon/Summoning Point. The bearer counts as a Dark Apostle for The Dark Shepherds.')
wb_tainted=shared_up('r46-wb-tainted-weapon','Tainted Weapon',15,'Choose instead of a Power Weapon at the same points cost. User Strength, Specialist Weapon, Tainted Strike: any unsaved wound becomes a Massive Wound and inflicts D3 Wounds. It is not a Power Weapon and does not ignore Armour Saves.')
wb_lore=shared_up('r46-wb-burning-lore','Burning Lore',30,'Word Bearers Praetor, Centurion, Chaplain or Diabolist that is not already a Psyker. Becomes Psyker (Mastery Level 1) and selects one power from Biomancy or Telepathy.')
wb_hex=shared_up('r46-wb-hex-bolts','Hex-Bolts',5,'Word Bearers Infantry unit with Bolt weapons. Bolt Pistols, Bolters, Combi-Bolters, Storm Bolters and bolter components of Combi-Weapons gain Soul Blaze. Cannot combine with Special Issue Ammunition or another ammunition upgrade.')
wb_icon=shared_up('r46-wb-icon-chaos-undivided','Icon of Chaos Undivided',30,'One model in a Command, Veteran or Terminator Squad may carry the Icon. It is a Summoning Point for Daemonic Covenant and friendly non-Daemon Word Bearers within 6” gain Fearless.')
wb_dark=shared_up('r46-wb-dark-channelling','Dark Channelling',25,'Requires at least one Diabolist in the Detachment. Before the first turn roll D6: 1–3 Zealot; 4–5 +1 Strength; 6 Daemon (and the unit ceases to be Scoring; in VP missions it also counts as destroyed at battle end). Effects apply only to the upgraded squad.')
for uid in ['hq-praetor','hq-centurion']:
    for it in [wb_crozius,wb_tainted,wb_lore]:link(uid,it.get('id'),f'r46-{uid}-{it.get("id")}','legion-xvii')
for uid in ['tactical-unit','assault-unit','breacher-unit','veteran-unit','terminator-unit','fa-seeker']:
    link(uid,wb_hex.get('id'),f'r46-{uid}-wb-hex','legion-xvii')
for uid in ['veteran-unit','terminator-unit']:
    link(uid,wb_icon.get('id'),f'r46-{uid}-wb-icon','legion-xvii')
# Diabolist Consul, source-defined +35.
consuls=cby('hq-centurion-consuls'); assert consuls is not None
wb_diab=ET.SubElement(ensure(consuls,'selectionEntries'),C('selectionEntry'),{'id':'r46-wb-diabolist','name':'Diabolist Consul','type':'upgrade','hidden':'true','import':'true'});add_cost(wb_diab,35);add_constraint(wb_diab,'r46-wb-diabolist-max','max',1);gate(wb_diab,'legion-xvii');add_rule(wb_diab,'r46-wb-diabolist-rule','Diabolist','Gains Daemon and Preferred Enemy (Loyalists). May not select a Bike, Jetbike, Terminator Armour, Power Fist or Thunder Hammer. Enables eligible units to purchase Dark Channelling. May purchase an Accursed Crozius and then counts as a Dark Apostle.')
link('hq-centurion',wb_lore.get('id'),'r46-centurion-wb-burning-lore-diabolist','legion-xvii',extra=[('atLeast',1,'roster','r46-wb-diabolist')],name='Burning Lore (Diabolist)')
for uid in ['tactical-unit','assault-unit','breacher-unit','veteran-unit','terminator-unit']:
    link(uid,wb_dark.get('id'),f'r46-{uid}-wb-dark','legion-xvii',extra=[('atLeast',1,'roster','r46-wb-diabolist')])
gst_set('fl-heavy','fl-heavy-max',1,'r25-rite-xvii-0-the-dark-brethren','r46-wb-dark-brethren-heavy-max')

# XVIII — SALAMANDERS
sal_mantle=shared_up('r46-sal-mantle','Salamanders Mantle',35,'0–1 Salamanders Independent Character. An unsaved Wound that becomes a Massive Wound solely because attack Strength is at least double Toughness instead inflicts one Wound. Does not protect against other explicit Massive-Wound rules.',1)
sal_mc=shared_up('r46-sal-mastercrafted','Master-crafted Weapon — Salamanders price',10,'Salamanders price for the normal Master-crafted Weapon upgrade. All normal restrictions continue to apply.')
sal_art=shared_up('r46-sal-artificer-armour','Artificer Armour — Salamanders access',15,'Salamanders non-Independent Character with Space Marine Armoury access may purchase Artificer Armour for +15 even if the unit entry normally would not allow it; if the unit entry offers a lower price, use that price instead.')
sal_inferno=shared_up('r46-sal-inferno-pistol','Inferno Pistol',15,'Salamanders Independent Character or squad Sergeant. 6”, S8 AP1, Pistol, Melta.')
sal_heavy_flame=shared_up('r46-sal-heavy-flamer','Heavy Flamer instead of Flamer',10,'Where a Salamanders Tactical or Veteran Squad may purchase a Flamer, it may instead purchase a Heavy Flamer for +10. Salamanders Flame weapon profiles receive their Legion Strength increase as stated in Promethean Cult/Fire-based Warfare.')
sal_ceramite=shared_up('r46-sal-ceramite','Armoured Ceramite — Salamanders price',10,'Salamanders Vehicle or Dreadnought which may normally purchase Armoured Ceramite may purchase it for +10. Land Raiders and Spartans use their normal listed price.')
for uid in ['hq-praetor','hq-centurion']:
    for it in [sal_mantle,sal_mc,sal_inferno]:link(uid,it.get('id'),f'r46-{uid}-{it.get("id")}','legion-xviii')
for uid in ['tactical-unit','veteran-unit']:
    link(uid,sal_heavy_flame.get('id'),f'r46-{uid}-sal-heavyflame','legion-xviii')
for uid in ['tactical-unit','assault-unit','breacher-unit','recon-unit','veteran-unit','fa-seeker','hs-heavy-support-squad']:
    link(uid,sal_art.get('id'),f'r46-{uid}-sal-artificer','legion-xviii')
for uid in ['dreadnought-unit','contemptor-unit','hs-deredeo','hs-leviathan','hs-predator','hs-vindicator','hs-artillery','hs-scorpius','hs-sicaran','hs-venator','hs-achilles-alpha']:
    link(uid,sal_ceramite.get('id'),f'r46-{uid}-sal-ceramite','legion-xviii')
# Awakening Fire excludes Vulkan.
vulkan=find_top('vulkan')
if vulkan:hide_if(vulkan,'r25-rite-xviii-1-the-awakening-fire','r46-sal-awakening-hide-vulkan')

# XIX — RAVEN GUARD
rg_talons=shared_up('r46-rg-talons-model','Raven’s Talons — Veteran model',7,'Veteran model with Bolt Pistol and Chainsword replaces both with a pair of Raven’s Talons. They count as a pair of Rending Weapons and grant the normal +1 Attack for two close-combat weapons.',maxv=20)
rg_talon_char=shared_up('r46-rg-talons-character','Upgrade Lightning Claws to Raven’s Talons',5,'Raven Guard Character already equipped with a pair of Lightning Claws may upgrade them to Raven’s Talons. They count as a pair of Rending Weapons.')
rg_hand=shared_up('r46-rg-hand-cannon','Fulcrum Hand Cannon',10,'Raven Guard Independent Character or squad Sergeant replaces Bolt Pistol. 18”, S4 AP4, Pistol, Rending, Concussive.')
rg_infra=shared_up('r46-rg-infravisor','Infravisor',10,'Raven Guard Independent Character or squad Sergeant. Gains Night Vision and +1 BS (max BS6). For Blind Initiative tests, bearer and joined unit count as Initiative 1.')
rg_shroud_ic=shared_up('r46-rg-shroud-character','Shroud Bombs',10,'Raven Guard Independent Character. Counts as Defensive Grenades. An enemy attempting to charge the equipped unit must first pass a Leadership test or cannot attempt that charge; Vehicles, Daemons and units containing Night Vision are unaffected.')
rg_shroud_unit=shared_up('r46-rg-shroud-unit','Shroud Bombs',20,'Raven Guard Recon, Veteran or Mor Deythan Squad. Counts as Defensive Grenades. Charging enemy must pass Leadership test or cannot attempt that charge; Vehicles, Daemons and units containing Night Vision are unaffected.')
rg_camo=shared_up('r46-rg-cameleoline','Cameleoline',10,'Raven Guard Independent Character wearing Power, Artificer or Recon Armour. Grants Stealth.')
rg_trans_ic=shared_up('r46-rg-trans-character','Teleportation Transponders',10,'Raven Guard Independent Character in Terminator Armour. Grants Deep Strike even if the mission would not normally permit it.')
rg_trans_unit=shared_up('r46-rg-trans-unit','Teleportation Transponders',15,'Raven Guard unit entirely in Terminator Armour. Grants Deep Strike even if the mission would not normally permit it.')
for uid in ['hq-praetor','hq-centurion']:
    for it in [rg_talon_char,rg_hand,rg_infra,rg_shroud_ic,rg_camo,rg_trans_ic]:link(uid,it.get('id'),f'r46-{uid}-{it.get("id")}','legion-xix')
link('veteran-unit',rg_talons.get('id'),'r46-veteran-rg-talons','legion-xix',maxv=20)
for uid in ['recon-unit','veteran-unit']:
    link(uid,rg_shroud_unit.get('id'),f'r46-{uid}-rg-shroud','legion-xix')
link('terminator-unit',rg_trans_unit.get('id'),'r46-terminator-rg-trans','legion-xix')
gst_set('fl-heavy','fl-heavy-max',1,'r25-rite-xix-0-decapitation-strike','r46-rg-decap-heavy-max')

# XX — ALPHA LEGION
al_bane_ic=shared_up('r46-al-banestrike-character','Banestrike Ammunition',5,'+5 per eligible model. Bolter/Foeblaster Boltgun/Combi-Bolter/Combi-Weapon uses 18” range, AP4 and Banestrike; natural To Wound 6 is AP3. Seeker Squads may choose this instead of Special Issue Ammunition when firing; never combine ammunition types.')
al_bane_unit=shared_up('r46-al-banestrike-model','Banestrike Ammunition — eligible model',5,'Alpha Legion Seeker/Veteran model with an eligible bolt weapon. Every eligible model in the squad must buy it. 18” AP4 Banestrike; natural To Wound 6 resolves at AP3.',maxv=20)
al_dagger=shared_up('r46-al-power-dagger','Power Dagger',5,'Alpha Legion Character. Counts as a Power Weapon with Rending and Specialist Weapon; attacks are resolved at -1 Strength.')
al_venom=shared_up('r46-al-venom-spheres','Venom Spheres',5,'Alpha Legion Independent Character or squad Sergeant. Grants Hammer of Wrath.')
al_trans_ic=shared_up('r46-al-trans-character','Teleportation Transponders',10,'Alpha Legion Independent Character in Terminator Armour. Grants Deep Strike even if mission rules normally prohibit it.')
al_trans_unit=shared_up('r46-al-trans-unit','Teleportation Transponders',15,'Alpha Legion unit entirely in Terminator Armour. Grants Deep Strike even if mission rules normally prohibit it.')
for uid in ['hq-praetor','hq-centurion']:
    for it in [al_bane_ic,al_dagger,al_venom,al_trans_ic]:link(uid,it.get('id'),f'r46-{uid}-{it.get("id")}','legion-xx')
for uid in ['fa-seeker','veteran-unit']:
    link(uid,al_bane_unit.get('id'),f'r46-{uid}-al-bane','legion-xx',maxv=20)
link('terminator-unit',al_trans_unit.get('id'),'r46-terminator-al-trans','legion-xx')
# Mutable Tactics is an actual required roster selection nested under the Legion choice.
al_selector=cby('legion-xx'); assert al_selector is not None
gs=ensure(al_selector,'selectionEntryGroups');mg=ET.SubElement(gs,C('selectionEntryGroup'),{'id':'r46-al-mutable-tactics','name':'Mutable Tactics','hidden':'false','collective':'false','import':'true'});add_constraint(mg,'r46-al-mutable-min','min',1);add_constraint(mg,'r46-al-mutable-max','max',1)
mes=ET.SubElement(mg,C('selectionEntries'))
for i,n in enumerate(['Counter-Attack','Furious Charge','Infiltrate','Move Through Cover','Siege Specialists','Tank Hunters']):
    e=ET.SubElement(mes,C('selectionEntry'),{'id':f'r46-al-mutable-{i}','name':n,'type':'upgrade','hidden':'false','import':'true'});add_constraint(e,e.get('id')+'-max','max',1);add_rule(e,e.get('id')+'-rule',n,'Selected as the Alpha Legion army’s Mutable Tactic. Applies to all qualifying non-vehicle units and does not count toward their Veteran Skill limit. Normal restrictions of the selected skill apply.')
# Coils requires a third compulsory Troops choice.
gst_set('fl-troops','fl-troops-min',3,'r25-rite-xx-0-the-coils-of-the-hydra','r46-al-coils-troops-min')
# 0-2 Legion Operatives may be taken without occupying Troops: add an Auxiliary category and a slotless clone.
cats=ensure(gr,'categoryEntries',GNS)
if gby('cat-auxiliary') is None:ET.SubElement(cats,G('categoryEntry'),{'id':'cat-auxiliary','name':'Auxiliary','hidden':'false'})
force=gby('force-standard'); fl=ensure(force,'categoryLinks',GNS)
if gby('fl-auxiliary') is None:ET.SubElement(fl,G('categoryLink'),{'id':'fl-auxiliary','name':'Auxiliary','targetId':'cat-auxiliary','hidden':'false'})
op=cby('r41-unit-xx-0-legion-operatives')
if op is not None:
    clone=deepcopy(op);rewrite_ids(clone,'r46-al-operative-aux-');prune_missing(clone);clone.set('id','r46-al-operative-aux');clone.set('name','Legion Operatives (slotless 0–2)');set_primary_cat(clone,'cat-auxiliary','Auxiliary');clone.set('hidden','true');gate(clone,'legion-xx');add_constraint(clone,'r46-al-operative-aux-roster','max',2,'roster');add_rule(clone,'r46-al-operative-aux-rule','Infiltration Network','Up to two Legion Operative units may be selected without occupying a Troops slot. They are paid for normally and still count as units for Martial Hubris.');top.append(clone)
# Rewards of Treachery — materialise eligible Legion-specific squad units as Elites and enforce one reward across the army.
if gby('cat-alpha-reward') is None:ET.SubElement(cats,G('categoryEntry'),{'id':'cat-alpha-reward','name':'Rewards of Treachery Limit','hidden':'true'})
if gby('fl-alpha-reward') is None:
    lk=ET.SubElement(fl,G('categoryLink'),{'id':'fl-alpha-reward','name':'Rewards of Treachery Limit','targetId':'cat-alpha-reward','hidden':'true'});cs=ET.SubElement(lk,G('constraints'));ET.SubElement(cs,G('constraint'),{'id':'r46-al-reward-max','field':'selections','scope':'parent','value':'1','type':'max','shared':'true','includeChildSelections':'false','includeChildForces':'false'})
eligible=[]
for src in list(top):
    sid=src.get('id',''); name=src.get('name','')
    if not sid.startswith('r41-unit-') or sid.startswith('r41-unit-xx-'):continue
    catids={x.get('targetId') for x in src.findall('./'+C('categoryLinks')+'/'+C('categoryLink'))}
    if not catids.intersection({'cat-troops','cat-elites','cat-fast','cat-heavy'}):continue
    # Exclude roster-unique units and obvious lone/named models.
    if any(x.get('scope')=='roster' and x.get('type')=='max' and x.get('value')=='1' for x in src.findall('.//'+C('constraint'))):continue
    low=name.lower()
    if not any(k in low for k in ['squad','cohort','cabal','pack','maniple','team','cadre','terminator','operatives','brethren','guard']):continue
    eligible.append(src)
for idx,src in enumerate(eligible):
    clone=deepcopy(src);prefix=f'r46-al-reward-{idx}-';rewrite_ids(clone,prefix);prune_missing(clone);clone.set('id',f'r46-al-reward-{idx}');clone.set('name',src.get('name')+' — Rewards of Treachery');clone.set('hidden','true')
    # Remove inherited Legion visibility modifiers; retain normal unit content/options otherwise.
    mods=clone.find(C('modifiers'))
    if mods is not None:
        for md in list(mods):
            if any((c.get('childId') or '').startswith('legion-') for c in md.findall('.//'+C('condition'))):mods.remove(md)
    set_primary_cat(clone,'cat-elites','Elites');cats2=ensure(clone,'categoryLinks');ET.SubElement(cats2,C('categoryLink'),{'id':clone.get('id')+'-limit-cat','name':'Rewards of Treachery Limit','targetId':'cat-alpha-reward','hidden':'true'})
    gate(clone,'legion-xx',extra=[('atLeast',1,'force','r25-rite-xx-0-the-coils-of-the-hydra')]);add_rule(clone,clone.get('id')+'-rule','The Rewards of Treachery','One eligible Legion-specific unit from another Legion may be selected as an Elites choice. It retains its profile, equipment, options and unit-specific special rules, but replaces its original Legion-specific Legiones Astartes rules with Legiones Astartes (Alpha Legion) and benefits from Alpha Legion rules including Mutable Tactics.');top.append(clone)

cr.set('revision','46');gr.set('revision',str(int(gr.get('revision','17'))+1));cr.set('gameSystemRevision',gr.get('revision'))
comment=cr.find(C('comment'))
if comment is not None:comment.text='Revision 46: New Recruit completion pass for Legions XVI-XX, including Legion armouries, Word Bearers Diabolist/Dark Channelling, Salamanders forge options, Raven Guard stealth wargear, Alpha Legion Mutable Tactics and functional Rewards of Treachery.'
ct.write(CAT,encoding='UTF-8',xml_declaration=True);gt.write(GST,encoding='UTF-8',xml_declaration=True)
print('REV46 COMPLETE',cr.get('revision'),gr.get('revision'),'Rewards of Treachery choices',len(eligible))
