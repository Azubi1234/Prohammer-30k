from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET
import re

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ET.register_namespace('',CNS); ET.register_namespace('',GNS)
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()
top=cr.find(C('selectionEntries')); shared=cr.find(C('sharedSelectionEntries'))
assert top is not None and shared is not None

def cby(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def gby(i): return next((e for e in gr.iter() if e.get('id')==i),None)
def ensure(p,tag,ns=CNS):
    q=f'{{{ns}}}{tag}'; x=p.find(q)
    if x is None: x=ET.SubElement(p,q)
    return x

def add_cost(e,v):
    cs=ensure(e,'costs'); ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def add_max(e,id_,v,scope='parent'):
    cs=ensure(e,'constraints'); ET.SubElement(cs,C('constraint'),{'id':id_,'type':'max','value':str(v),'field':'selections','scope':scope,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_rule(e,id_,name,text):
    rs=ensure(e,'rules'); r=ET.SubElement(rs,C('rule'),{'id':id_,'name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=text
    return r
def cond_modifier(e,visible_when=True,conds=()):
    mods=ensure(e,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'type':'set','value':'false' if visible_when else 'true','field':'hidden'})
    cgs=ET.SubElement(m,C('conditionGroups')); cg=ET.SubElement(cgs,C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(cg,C('conditions'))
    for typ,val,scope,child in conds:
        ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return m
def gate_legion(e,legion,extra=()):
    e.set('hidden','true'); cond_modifier(e,True,[('atLeast',1,'roster',legion),*extra])
def shared_upgrade(id_,name,cost,text,roster_max=None):
    old=cby(id_)
    if old is not None:return old
    e=ET.SubElement(shared,C('selectionEntry'),{'id':id_,'name':name,'type':'upgrade','hidden':'false','import':'true'})
    add_cost(e,cost); add_max(e,id_+'-max',1)
    if roster_max is not None:add_max(e,id_+'-roster-max',roster_max,'roster')
    add_rule(e,id_+'-rule',name,text)
    return e
def link(unit_id,target_id,id_,name=None,legion=None,extra=()):
    u=cby(unit_id); t=cby(target_id)
    if u is None or t is None:return None
    ls=ensure(u,'entryLinks')
    if any(x.get('id')==id_ for x in ls.findall(C('entryLink'))): return next(x for x in ls.findall(C('entryLink')) if x.get('id')==id_)
    l=ET.SubElement(ls,C('entryLink'),{'id':id_,'name':name or t.get('name'),'type':'selectionEntry','targetId':target_id,'hidden':'false','import':'true'})
    add_max(l,id_+'-max',1)
    if legion: gate_legion(l,legion,extra)
    return l
def rewrite_ids(node,prefix):
    mp={}
    for e in node.iter():
        if e.get('id'): mp[e.get('id')]=prefix+e.get('id')
    for e in node.iter():
        if e.get('id') in mp:e.set('id',mp[e.get('id')])
    for e in node.iter():
        for a in ('targetId','childId','field'):
            if e.get(a) in mp:e.set(a,mp[e.get(a)])
def set_cat(e,catid,name):
    old=e.find(C('categoryLinks'))
    if old is not None:e.remove(old)
    cs=ET.SubElement(e,C('categoryLinks')); ET.SubElement(cs,C('categoryLink'),{'id':e.get('id')+'-cat','targetId':catid,'name':name,'hidden':'false','primary':'true'})
def clone_role(src_id,new_id,name,legion,rite=None,rule=''):
    if cby(new_id) is not None:return cby(new_id)
    src=cby(src_id); assert src is not None,src_id
    c=deepcopy(src); rewrite_ids(c,new_id+'-'); c.set('id',new_id); c.set('name',name); set_cat(c,'cat-troops','Troops'); c.set('hidden','true')
    conditions=[('atLeast',1,'roster',legion)]
    if rite:conditions.append(('atLeast',1,'force',rite))
    cond_modifier(c,True,conditions)
    add_rule(c,new_id+'-rule','Battlefield Role',rule)
    top.append(c); return c

def hide_if_legion(entry_id,legion):
    e=cby(entry_id)
    if e is None:return
    cond_modifier(e,False,[('atLeast',1,'roster',legion)])

def gst_set_max(link_id,constraint_id,value,selector,id_):
    l=gby(link_id); assert l is not None,link_id
    mods=ensure(l,'modifiers',GNS)
    if any(x.get('id')==id_ for x in mods.findall(G('modifier'))):return
    m=ET.SubElement(mods,G('modifier'),{'id':id_,'type':'set','value':str(value),'field':constraint_id})
    cs=ET.SubElement(m,G('conditions')); ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Clean this pass on rerun.
for p in list(cr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r43-'):p.remove(x)
for p in list(gr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r43-'):p.remove(x)

# ==================== III — EMPEROR'S CHILDREN ====================
ec_spear=shared_upgrade('r43-ec-phoenix-spear','Phoenix Spear',20,'Power Weapon, Two-Handed, Phoenix Strike. During the first round of each close combat attacks are resolved at +1 Strength; thereafter at normal Strength. Characters already equipped with a Power Weapon as basic wargear exchange it for +5 points instead; use the source restriction when applying this entry.')
ec_lasers=shared_upgrade('r43-ec-digital-lasers','Digital Lasers',15,'Emperor’s Children Independent Character only. Adds +1 to the bearer’s Attacks characteristic. May not be combined with Terminator Honours.')
ec_shrieker=shared_upgrade('r43-ec-sonic-shrieker','Sonic Shrieker',10,'TRAITOR ONLY. During the first round of close combat an enemy model in base contact suffers -1 Weapon Skill. If every model in the unit is equipped, every enemy model engaged with it suffers -1 WS. Not cumulative; Fearless models are unaffected.')
ec_line_apoth=shared_upgrade('r43-ec-line-apothecary','Sergeant upgraded to Apothecary',25,'PURITY ABOVE ALL: Upgrade the Legion Sergeant to an Apothecary. The model retains its weapons and wargear and gains a Narthecium. It counts as an Apothecary and may purchase a Reductor for +5 points. Across the army, only one Tactical Squad OR Assault Squad may take this upgrade.',1)
ec_vet_apoth=shared_upgrade('r43-ec-vet-apothecary','Veteran Sergeant upgraded to Apothecary',25,'PURITY ABOVE ALL: Upgrade the Legion Veteran Sergeant to an Apothecary. The model retains its weapons and wargear and gains a Narthecium. It counts as an Apothecary and may purchase a Reductor for +5 points.')
ec_reductor=shared_upgrade('r43-ec-reductor','Reductor',5,'May only be selected for a Sergeant upgraded to an Apothecary by Purity Above All.')
for uid in ['hq-praetor','hq-centurion']:
    link(uid,ec_spear.get('id'),f'r43-{uid}-ec-spear',legion='legion-iii')
    link(uid,ec_lasers.get('id'),f'r43-{uid}-ec-lasers',legion='legion-iii')
    link(uid,ec_shrieker.get('id'),f'r43-{uid}-ec-shrieker',legion='legion-iii',extra=[('atLeast',1,'roster','allegiance-traitor')])
for uid in ['tactical-unit','assault-unit']:
    link(uid,ec_line_apoth.get('id'),f'r43-{uid}-ec-apoth',legion='legion-iii')
    link(uid,ec_reductor.get('id'),f'r43-{uid}-ec-reductor',legion='legion-iii')
link('veteran-unit',ec_vet_apoth.get('id'),'r43-veteran-ec-apoth',legion='legion-iii')
link('veteran-unit',ec_reductor.get('id'),'r43-veteran-ec-reductor',legion='legion-iii')
# Sonic package lives on HSS and is roster-limited to one squad unless 3rd Company rules override it manually.
sonic_pkg=shared_upgrade('r43-ec-sonic-package','Sonic Weaponry Package',0,'TRAITOR ONLY. One Legion Heavy Support Squad may select up to four Sonic Weapons instead of normal Heavy Weapon options. The 3rd Company Elite Rite increases this allowance to two squads.',1)
for nm,cost,txt in [('Sonic Blaster',15,'24”, S4 AP5, Assault 2 or Heavy 3.'),('Doom Siren',20,'Template, S5 AP4, Assault 1.'),('Blastmaster',35,'48”, S8 AP3, Heavy 1, Blast.')]:
    sid='r43-ec-sonic-'+re.sub('[^a-z]+','-',nm.lower()).strip('-'); s=shared_upgrade(sid,nm,cost,txt)
    link('hs-heavy-support-squad',sid,'r43-hss-'+sid,legion='legion-iii',extra=[('atLeast',1,'roster','allegiance-traitor')])
link('hs-heavy-support-squad',sonic_pkg.get('id'),'r43-hss-ec-sonic-package',legion='legion-iii',extra=[('atLeast',1,'roster','allegiance-traitor')])
fearless=shared_upgrade('r43-ec-perfect-cacophony','Perfect Cacophony — Fearless',20,'A Legion Heavy Support Squad in which the majority of surviving models are equipped with Sonic Weapons gains Fearless.')
link('hs-heavy-support-squad',fearless.get('id'),'r43-hss-ec-perfect-cacophony',legion='legion-iii',extra=[('atLeast',1,'roster','allegiance-traitor')])
# Maru Skara: maximum two Heavy Support choices.
gst_set_max('fl-heavy','fl-heavy-max',2,'r25-rite-iii-0-the-maru-skara','r43-ec-maru-heavy-max')

# ==================== IV — IRON WARRIORS ====================
iw_shrapnel=shared_upgrade('r43-iw-shrapnel-bolts','Shrapnel Bolts',5,'The unit’s Bolt Pistols, Bolters, Combi-Bolters, Storm Bolters, Heavy Bolters, Twin-linked Bolters and bolter components of Combi-Weapons gain Pinning. May not be combined with Special Issue Ammunition, Hellfire Rounds or another special ammunition type.')
iw_servo=shared_upgrade('r43-iw-servo-arm','Servo-Arm',30,'Any Iron Warriors model with Space Marine Armoury access may purchase this even without normal Techmarine access. A Jump Pack model may not purchase it. Use the normal Servo-Arm rules from the Legiones Astartes Army List.')
iw_bionics=shared_upgrade('r43-iw-bionics','Bionics',5,'Iron Warriors Armoury price. Follows the normal Bionics rules from the Legiones Astartes Army List.')
for uid in ['hq-praetor','hq-centurion']:
    link(uid,iw_servo.get('id'),f'r43-{uid}-iw-servo',legion='legion-iv')
    link(uid,iw_bionics.get('id'),f'r43-{uid}-iw-bionics',legion='legion-iv')
for uid in ['tactical-unit','assault-unit','breacher-unit','veteran-unit','terminator-unit','fa-seeker','hs-heavy-support-squad','r41-unit-iv-0-tyrant-siege-terminator-squad','r41-unit-iv-1-iron-havoc-squad','r41-unit-iv-2-dominator-cohort']:
    link(uid,iw_shrapnel.get('id'),f'r43-{uid}-iw-shrapnel',legion='legion-iv')
# Core Iron Warriors FOC exchange: 0-1 Fast Attack / 0-4 Heavy Support.
gst_set_max('fl-fast','fl-fast-max',1,'legion-iv','r43-iw-fast-max')
gst_set_max('fl-heavy','fl-heavy-max',4,'legion-iv','r43-iw-heavy-max')

# ==================== V — WHITE SCARS ====================
# Mounted Brotherhoods is a permanent Legion rule: Bikes are Troops and may fulfil compulsory Troops.
clone_role('fa-bike','r43-ws-bike-troops','Legion Bike Squadron','legion-v',None,'MOUNTED BROTHERHOODS: Legion Bike Squadrons may be selected as Troops choices and may fulfil compulsory Troops selections.')
# Sagyar Mazan explicitly moves Ebon Keshig to Troops.
clone_role('r41-unit-v-1-ebon-keshig','r43-ws-sagyar-ebon-troops','EBON KESHIG','legion-v','r25-rite-v-1-the-sagyar-mazan','THE SAGYAR MAZAN: Ebon Keshig may be selected as Troops and may fulfil compulsory Troops selections.')
ws_glaive=shared_upgrade('r43-ws-power-glaive','Power Glaive',25,'Character able to select a Power Weapon. One-Handed: User Strength, Power Weapon. Two-Handed: User +1 Strength, Power Weapon, Two-Handed. A model with a Power Weapon as basic wargear may exchange it for +10 instead.')
ws_lance=shared_upgrade('r43-ws-warlance','Chogorian Warlance',15,'Requires a Bike or Jetbike. Power Weapon, Cavalry Lance: +1 Initiative in the first round when charging; -1 Initiative in rounds in which the bearer did not charge. One-handed.')
ws_hawk=shared_upgrade('r43-ws-cyber-hawk','Cyber-hawk',10,'0–1 White Scars Praetor. At the beginning of each White Scars turn place/move the marker. White Scars Infantry attacking an enemy within 6” of it may re-roll shooting To Hit rolls of 1 and increases charge distance against that enemy from 6” to 7”.',1)
for uid in ['hq-praetor','hq-centurion']:
    link(uid,ws_glaive.get('id'),f'r43-{uid}-ws-glaive',legion='legion-v')
    link(uid,ws_lance.get('id'),f'r43-{uid}-ws-lance',legion='legion-v')
link('hq-praetor',ws_hawk.get('id'),'r43-praetor-ws-hawk',legion='legion-v')
# Stormseer replaces generic Librarian Consul.
hide_if_legion('hq-consul-librarian','legion-v')
# Chogorian Brotherhood: max one Heavy Support.
gst_set_max('fl-heavy','fl-heavy-max',1,'r25-rite-v-0-chogorian-brotherhood','r43-ws-chogorian-heavy-max')

# ==================== VI — SPACE WOLVES ====================
sw_frost=shared_upgrade('r43-sw-frost-weapon','Frost Weapon',20,'Space Wolves Character with Armoury access. User +1 Strength, Power Weapon. A model already equipped with a Power Weapon may exchange it for +5 instead.')
sw_great=shared_upgrade('r43-sw-great-frost-blade','Great Frost Blade',35,'Space Wolves Independent Character. User +2 Strength, Power Weapon, Two-Handed, Master-crafted. The bearer suffers -1 Initiative while using it.')
sw_pelt=shared_upgrade('r43-sw-wolf-pelt','Wolf Pelt',5,'When the bearer’s unit successfully uses Counter-Attack, the bearer receives +2 Attacks instead of the normal +1 granted by Counter-Attack.')
sw_neck=shared_upgrade('r43-sw-wolf-tooth-necklace','Wolf Tooth Necklace',10,'The bearer always hits enemy models on a 3+ in close combat unless it would normally hit on a better result.')
sw_tail=shared_upgrade('r43-sw-wolf-tail-talisman','Wolf Tail Talisman',5,'When an enemy psychic power directly affects the bearer or joined unit, after the power succeeds and any normal Deny attempt, roll D6; on a 6 the bearer is unaffected.')
sw_runic=shared_upgrade('r43-sw-runic-armour','Runic Armour',25,'Independent Character in Power Armour only. Replaces Power Armour; grants a 2+ Armour Save and Adamantium Will and counts as Artificer Armour for other rules.')
for uid in ['hq-praetor','hq-centurion']:
    for item in [sw_frost,sw_great,sw_pelt,sw_neck,sw_tail,sw_runic]:
        link(uid,item.get('id'),f'r43-{uid}-{item.get("id")}',legion='legion-vi')
# Wolf Priests and Rune Priests replace generic Chaplain/Librarian Consuls.
hide_if_legion('hq-consul-chaplain','legion-vi'); hide_if_legion('hq-consul-librarian','legion-vi')
# Space Wolves Great Company structure allows up to four HQ in a 3,000 point army; point-band minimums remain stated in the Legion reference.
gst_set_max('fl-hq','fl-hq-max',4,'legion-vi','r43-sw-hq-max')
# Pale Hunters: maximum one Heavy Support.
gst_set_max('fl-heavy','fl-heavy-max',1,'r25-rite-vi-0-the-pale-hunters','r43-sw-pale-heavy-max')

cr.set('revision','43'); gr.set('revision',str(int(gr.get('revision','14'))+1)); cr.set('gameSystemRevision',gr.get('revision'))
comment=cr.find(C('comment'))
if comment is not None:comment.text='Revision 43: Dark Angels-level New Recruit interaction pass begun for Legions III-VI: functional core FOC changes, Rite slot limits, Legion armoury selections, specialist Consul replacement gates and additional Rite battlefield-role changes.'
ct.write(CAT,encoding='UTF-8',xml_declaration=True); gt.write(GST,encoding='UTF-8',xml_declaration=True)
print('REV43 LEGIONS III-VI BUILDER PASS COMPLETE; CAT',cr.get('revision'),'GST',gr.get('revision'))
