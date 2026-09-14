from pathlib import Path
import xml.etree.ElementTree as ET
import re

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ET.register_namespace('',CNS); ET.register_namespace('',GNS)
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()
top=cr.find(C('selectionEntries')); shared=cr.find(C('sharedSelectionEntries'))
assert top is not None and shared is not None

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def cby(i): return byid(cr,i)
def gby(i): return byid(gr,i)
def ensure(p,tag,ns=CNS):
    q=f'{{{ns}}}{tag}'; x=p.find(q)
    if x is None:x=ET.SubElement(p,q)
    return x
def add_cost(e,v): ET.SubElement(ensure(e,'costs'),C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def add_max(e,id_,v,scope='parent'):
    ET.SubElement(ensure(e,'constraints'),C('constraint'),{'id':id_,'type':'max','value':str(v),'field':'selections','scope':scope,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_rule(e,id_,name,text):
    r=ET.SubElement(ensure(e,'rules'),C('rule'),{'id':id_,'name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=text
def cond_mod(e,hide,conds):
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'type':'set','value':'true' if hide else 'false','field':'hidden'})
    gs=ET.SubElement(m,C('conditionGroups')); g=ET.SubElement(gs,C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(g,C('conditions'))
    for typ,val,scope,child in conds: ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def gate(e,legion,extra=()): e.set('hidden','true'); cond_mod(e,False,[('atLeast',1,'roster',legion),*extra])
def shared_up(id_,name,cost,text,roster_max=None):
    if cby(id_):return cby(id_)
    e=ET.SubElement(shared,C('selectionEntry'),{'id':id_,'name':name,'type':'upgrade','hidden':'false','import':'true'}); add_cost(e,cost); add_max(e,id_+'-max',1)
    if roster_max is not None:add_max(e,id_+'-roster',roster_max,'roster')
    add_rule(e,id_+'-rule',name,text); return e
def link(uid,target,id_,legion,extra=(),name=None):
    u=cby(uid); t=cby(target)
    if u is None or t is None:return None
    ls=ensure(u,'entryLinks'); l=ET.SubElement(ls,C('entryLink'),{'id':id_,'name':name or t.get('name'),'type':'selectionEntry','targetId':target,'hidden':'true','import':'true'}); add_max(l,id_+'-max',1); gate(l,legion,extra); return l
def find_top_name(*needles):
    vals=[]
    for e in list(top):
        n=(e.get('name') or '').lower()
        if all(x.lower() in n for x in needles):vals.append(e)
    return vals[0] if vals else None
def links_many(unit_ids,item,legion,prefix,extra=()):
    for uid in unit_ids:
        if cby(uid): link(uid,item.get('id'),f'{prefix}-{uid}',legion,extra)
def gst_set(link_id,constraint_id,value,selector,id_):
    l=gby(link_id); assert l is not None
    mods=ensure(l,'modifiers',GNS); m=ET.SubElement(mods,G('modifier'),{'id':id_,'type':'set','value':str(value),'field':constraint_id}); cs=ET.SubElement(m,G('conditions')); ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def hide_if(entry_id,selector,id_):
    e=cby(entry_id)
    if e is None:return
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':id_,'type':'set','value':'true','field':'hidden'}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'force','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Clean only this pass for safe re-runs.
for p in list(cr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r44-'):p.remove(x)
for p in list(gr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r44-'):p.remove(x)

# VII — IMPERIAL FISTS
if_gaunt=shared_up('r44-if-solarite-gauntlet','Solarite Power Gauntlet',30,'Imperial Fists Character with Armoury access. Strength 10, Power Weapon, Unwieldy, Specialist Weapon. A model already equipped with a Power Fist may exchange it for +5 points instead.')
if_shield=shared_up('r44-if-vigil-storm-shield','Vigil Pattern Storm Shield',25,'Imperial Fists Independent Character only. Grants a 3+ Invulnerable Save, occupies one hand, bearer may carry no more than one other weapon and never receives the bonus Attack for two close-combat weapons.')
if_trans_ic=shared_up('r44-if-transponder-character','Teleportation Transponders',10,'Imperial Fists Independent Character wearing Terminator Armour. Grants Deep Strike even if the mission would not normally permit it. Hammerfall Strike Force removes the Terminator Armour restriction.')
if_trans_unit=shared_up('r44-if-transponder-unit','Teleportation Transponders',15,'Imperial Fists unit composed entirely of models in Terminator Armour. Grants Deep Strike even if the mission would not normally permit it. Hammerfall Strike Force extends this to any Imperial Fists Infantry unit.')
for uid in ['hq-praetor','hq-centurion']:
    link(uid,if_gaunt.get('id'),f'r44-{uid}-if-gaunt','legion-vii'); link(uid,if_shield.get('id'),f'r44-{uid}-if-shield','legion-vii'); link(uid,if_trans_ic.get('id'),f'r44-{uid}-if-trans','legion-vii')
for uid in ['terminator-unit','r41-unit-vii-2-huscarl-terminator-retinue']:
    link(uid,if_trans_unit.get('id'),f'r44-{uid}-if-trans','legion-vii')
# Hammerfall transponders for broader Infantry — expose on common infantry while Rite is active.
for uid in ['tactical-unit','assault-unit','breacher-unit','recon-unit','veteran-unit','fa-seeker','hs-heavy-support-squad','r41-unit-vii-0-templar-brethren-squad','r41-unit-vii-1-phalanx-warder-squad']:
    link(uid,if_trans_unit.get('id'),f'r44-{uid}-if-hammerfall-trans','legion-vii',extra=[('atLeast',1,'force','r25-rite-vii-1-hammerfall-strike-force')],name='Teleportation Transponders (Hammerfall)')
gst_set('fl-fast','fl-fast-max',1,'r25-rite-vii-0-the-stone-gauntlet','r44-if-stone-fast-max')
gst_set('fl-fast','fl-fast-max',1,'r25-rite-vii-2-templar-assault','r44-if-templar-fast-max')

# VIII — NIGHT LORDS
nl_glaive=shared_up('r44-nl-chainglaive','Nostraman Chainglaive',10,'Night Lords Independent Character or squad Sergeant. User +1 Strength, Rending, Two-Handed. Does not count as a Power Weapon.')
nl_trophies=shared_up('r44-nl-trophies','Trophies of Judgement',10,'Night Lords Independent Character or squad Sergeant. Enemy units with a model within 8” suffer -1 Leadership. Multiple sources do not stack.')
nl_stealth_ic=shared_up('r44-nl-stealth-ic','Stealth Adept',5,'Night Lords Independent Character. Gains Stealth. Models on Bikes/Jetbikes or in Terminator Armour may not purchase it.')
nl_stealth_unit=shared_up('r44-nl-stealth-unit','Stealth Adept — unit',0,'Night Lords Infantry or Jump Infantry only; +1 point per model and every model must purchase it. Grants Stealth. Bikes, Jetbikes, Terminator Armour, Dreadnoughts and Vehicles cannot take it. Add the correct +1/model total to the roster using the model-counted option where supported.')
nl_kraken=shared_up('r44-nl-kraken-bolts','Kraken Light Bolts',10,'Tactical or Veteran Squad. Bolters, Combi-Bolters, Twin-linked Bolters and bolter components of Combi-Weapons become AP4. Cannot combine with Special Issue Ammunition or another ammunition upgrade; Tactical Squads cannot use Fury of the Legion while firing them.')
nl_trans_ic=shared_up('r44-nl-transponder-character','Teleportation Transponders',10,'Night Lords Independent Character in Terminator Armour. Grants Deep Strike even where mission rules would not normally permit it.')
nl_trans_unit=shared_up('r44-nl-transponder-unit','Teleportation Transponders',15,'Night Lords unit entirely in Terminator Armour. Grants Deep Strike even where mission rules would not normally permit it.')
for uid in ['hq-praetor','hq-centurion']:
    for item in [nl_glaive,nl_trophies,nl_stealth_ic,nl_trans_ic]: link(uid,item.get('id'),f'r44-{uid}-{item.get("id")}','legion-viii')
for uid in ['tactical-unit','assault-unit','recon-unit','veteran-unit','fa-seeker']:
    link(uid,nl_stealth_unit.get('id'),f'r44-{uid}-nl-stealth','legion-viii')
for uid in ['tactical-unit','veteran-unit']:
    link(uid,nl_kraken.get('id'),f'r44-{uid}-nl-kraken','legion-viii')
for uid in ['terminator-unit','r41-unit-viii-2-contekar-terminator-elite','r41-unit-viii-3-atramentar-flay-clade']:
    link(uid,nl_trans_unit.get('id'),f'r44-{uid}-nl-trans','legion-viii')
# Core Night Lords FOC is permanently 0-4 Fast Attack / 0-1 Heavy Support.
gst_set('fl-fast','fl-fast-max',4,'legion-viii','r44-nl-fast-max'); gst_set('fl-heavy','fl-heavy-max',1,'legion-viii','r44-nl-heavy-max')

# IX — BLOOD ANGELS
ba_mask=shared_up('r44-ba-death-mask','Death Mask',10,'Blood Angels Independent Character. If an enemy loses a close combat in which a model was in base contact with the bearer, that unit suffers an additional -1 Leadership on the resulting Morale test. Multiple masks do not stack.')
ba_inferno=shared_up('r44-ba-inferno-pistol','Inferno Pistol',15,'6”, S8 AP1, Pistol, Melta. Any Blood Angels model with Space Marine Armoury access may purchase one. A Moritat has a special two-pistol replacement price in its own rules.')
ba_blade=shared_up('r44-ba-blade-perdition','Blade of Perdition',25,'Blood Angels Character with Armoury access. User Strength, Power Weapon, Two-Handed, Perdition. A natural To Wound roll of 6 causes a Massive Wound. Counts as a sword-like weapon. A model with a Power Weapon as basic wargear exchanges it for +10 instead.')
ba_engines=shared_up('r44-ba-overcharged-engines','Over-charged Engines',15,'Blood Angels Rhino only. Before moving roll D6: 1 = may not move; 2–3 = moves normally; 4–6 = may move as a Fast Vehicle up to 18”. Passengers follow normal transport rules.')
ba_jump=shared_up('r44-ba-furioso-jump-pack','Furioso-pattern Jump Pack',55,'0–1 Blood Angels Legion Contemptor with two Dreadnought Close Combat Weapons. Moves up to 12” over models/terrain like Jump Infantry, remains a Walker, may charge normally, cannot Deep Strike; on ending in Difficult/Dangerous Terrain, suffers a Glancing Hit on a 1.',1)
for uid in ['hq-praetor','hq-centurion']:
    for item in [ba_mask,ba_inferno,ba_blade]: link(uid,item.get('id'),f'r44-{uid}-{item.get("id")}','legion-ix')
rhino=find_top_name('rhino')
if rhino: link(rhino.get('id'),ba_engines.get('id'),'r44-ba-rhino-engines','legion-ix')
link('contemptor-unit',ba_jump.get('id'),'r44-ba-contemptor-jump','legion-ix')
gst_set('fl-heavy','fl-heavy-max',1,'r25-rite-ix-0-the-day-of-revelation','r44-ba-revelation-heavy-max')

# X — IRON HANDS
ih_servo=shared_up('r44-ih-servo-arm','Servo-Arm',30,'Any Iron Hands model with Space Marine Armoury access may purchase this even without Techmarine access. A Jump Pack model may not purchase it.')
ih_mech=shared_up('r44-ih-mechadendrites','Mechadendrites',15,'Iron Hands Independent Character or Sergeant. Once during each phase the bearer may re-roll one failed Armour Save; not an Invulnerable or Cover Save. The second result must be accepted.')
ih_gladius=shared_up('r44-ih-gladius','Albian Power Gladius',10,'Iron Hands Character with Armoury access. User Strength, Rending (5+). Against Vehicles, Rending still triggers only on a natural Armour Penetration roll of 6.')
ih_bionics=shared_up('r44-ih-bionics-character','Bionics',5,'Iron Hands Character/Veteran Sergeant price. Iron Hands Bionics recover on 5+ rather than 6+.')
ih_grav=shared_up('r44-ih-graviton-substitution','Graviton Gun instead of Flamer',15,'Whenever an Iron Hands model may purchase a Flamer, it may instead purchase a Graviton Gun for +15 points. Use the normal Graviton Gun profile/rules from the project armoury.')
ih_auto=shared_up('r44-ih-autosimulacra','Blessed Autosimulacra',10,'Iron Hands Vehicle. At the beginning of the Movement phase choose one Weapon Destroyed or Immobilised result and roll D6; on a 6 it is repaired. One attempt per Vehicle per turn.')
for uid in ['hq-praetor','hq-centurion']:
    for item in [ih_servo,ih_mech,ih_gladius,ih_bionics]: link(uid,item.get('id'),f'r44-{uid}-{item.get("id")}','legion-x')
for uid in ['tactical-unit','assault-unit','breacher-unit','veteran-unit','recon-unit','fa-seeker','hs-heavy-support-squad']:
    link(uid,ih_grav.get('id'),f'r44-{uid}-ih-grav','legion-x')
# Add Blessed Autosimulacra to the principal Legion vehicles.
for uid in ['hs-predator','hs-vindicator','hs-land-raider','hs-artillery','hs-scorpius','hs-spartan','hs-sicaran','hs-venator','hs-achilles-alpha']:
    link(uid,ih_auto.get('id'),f'r44-{uid}-ih-auto','legion-x')
# Head of the Gorgon max one Fast Attack.
gst_set('fl-fast','fl-fast-max',1,'r25-rite-x-0-the-head-of-the-gorgon','r44-ih-gorgon-fast-max')
# Company of Bitter Iron excludes Ferrus Manus.
ferrus=find_top_name('ferrus manus')
if ferrus: hide_if(ferrus.get('id'),'r25-rite-x-1-company-of-bitter-iron','r44-ih-bitter-hide-ferrus')

cr.set('revision','44'); gr.set('revision',str(int(gr.get('revision','15'))+1)); cr.set('gameSystemRevision',gr.get('revision'))
comment=cr.find(C('comment'))
if comment is not None:comment.text='Revision 44: New Recruit interaction pass for Legions VII-X, adding Legion armouries, core FOC alterations, Rite slot limits, vehicle upgrades, teleport options and source-defined exclusions while preserving the completed Dark Angels package.'
ct.write(CAT,encoding='UTF-8',xml_declaration=True); gt.write(GST,encoding='UTF-8',xml_declaration=True)
print('REV44 LEGIONS VII-X COMPLETE',cr.get('revision'),gr.get('revision'))
