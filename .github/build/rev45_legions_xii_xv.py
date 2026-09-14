from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET
import re
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ET.register_namespace('',CNS); ET.register_namespace('',GNS)
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); top=cr.find(C('selectionEntries')); shared=cr.find(C('sharedSelectionEntries')); assert top is not None and shared is not None

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def cby(i): return byid(cr,i)
def gby(i): return byid(gr,i)
def ensure(p,t,ns=CNS):
 q=f'{{{ns}}}{t}'; x=p.find(q)
 if x is None:x=ET.SubElement(p,q)
 return x
def cost(e,v): ET.SubElement(ensure(e,'costs'),C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def constraint(e,id_,typ,val,scope='parent',children='true'):
 return ET.SubElement(ensure(e,'constraints'),C('constraint'),{'id':id_,'type':typ,'value':str(val),'field':'selections','scope':scope,'shared':'true','includeChildSelections':children,'includeChildForces':'false'})
def rule(e,id_,name,text):
 r=ET.SubElement(ensure(e,'rules'),C('rule'),{'id':id_,'name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=text
def condition_mod(e,hide,conds,id_=None):
 a={'type':'set','value':'true' if hide else 'false','field':'hidden'}
 if id_:a['id']=id_
 m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),a); gs=ET.SubElement(m,C('conditionGroups')); g=ET.SubElement(gs,C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(g,C('conditions'))
 for typ,val,scope,ch in conds:ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':ch,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def gate(e,legion,extra=()):e.set('hidden','true');condition_mod(e,False,[('atLeast',1,'roster',legion),*extra])
def shared_up(id_,name,pts,text,roster_max=None):
 e=ET.SubElement(shared,C('selectionEntry'),{'id':id_,'name':name,'type':'upgrade','hidden':'false','import':'true'});cost(e,pts);constraint(e,id_+'-max','max',1)
 if roster_max is not None:constraint(e,id_+'-rmax','max',roster_max,'roster')
 rule(e,id_+'-rule',name,text);return e
def link(uid,target,id_,legion,extra=(),hide_selector=None):
 u=cby(uid);t=cby(target)
 if u is None or t is None:return None
 l=ET.SubElement(ensure(u,'entryLinks'),C('entryLink'),{'id':id_,'name':t.get('name'),'type':'selectionEntry','targetId':target,'hidden':'true','import':'true'});constraint(l,id_+'-max','max',1);gate(l,legion,extra)
 if hide_selector:condition_mod(l,True,[('atLeast',1,'force',hide_selector)],id_+'-hide-rite')
 return l
def gst_set(link,constraint_id,val,selector,id_):
 l=gby(link);assert l is not None
 m=ET.SubElement(ensure(l,'modifiers',GNS),G('modifier'),{'id':id_,'type':'set','value':str(val),'field':constraint_id});cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def find_top(text):
 text=text.lower()
 return next((e for e in list(top) if text in (e.get('name') or '').lower()),None)
def rewrite_ids(n,p):
 mp={}
 for e in n.iter():
  if e.get('id'):mp[e.get('id')]=p+e.get('id')
 for e in n.iter():
  if e.get('id') in mp:e.set('id',mp[e.get('id')])
 for e in n.iter():
  for a in ('targetId','childId','field'):
   if e.get(a) in mp:e.set(a,mp[e.get(a)])
def prune(n):
 valid={e.get('id') for e in cr.iter() if e.get('id')}
 for p in list(n.iter()):
  for x in list(p):
   if x.get('targetId') and x.get('targetId') not in valid:p.remove(x)
def hide_original_for_legion(e,legion,id_):condition_mod(e,True,[('atLeast',1,'roster',legion)],id_)
def dg_clone(src_id,new_id):
 src=cby(src_id);assert src is not None
 c=deepcopy(src);rewrite_ids(c,new_id+'-');prune(c);c.set('id',new_id);c.set('hidden','true');gate(c,'legion-xiv');cats=ensure(c,'categoryLinks');ET.SubElement(cats,C('categoryLink'),{'id':new_id+'-mobile-cat','name':'Death Guard Mobile Support','targetId':'cat-dg-mobile','hidden':'false'});top.append(c);hide_original_for_legion(src,'legion-xiv',new_id+'-hide-original');return c

def cult_group(uid,legion='legion-xv'):
 u=cby(uid)
 if u is None:return
 gs=ensure(u,'selectionEntryGroups');g=ET.SubElement(gs,C('selectionEntryGroup'),{'id':'r45-cult-'+re.sub('[^a-z0-9]+','-',uid.lower()),'name':'Prosperine Cult','hidden':'true','collective':'false','import':'true'});constraint(g,g.get('id')+'-min','min',1);constraint(g,g.get('id')+'-max','max',1);gate(g,legion)
 data=[('Pavoni','Fleet; Psykers/Psychic Brotherhoods also gain Crusader.'),('Raptora','6+ invulnerable save against shooting; Psychic Mastery improves this to 5+ (or improves an existing invulnerable save by 1 to max 4+) and improves cover by 1 to max 3+.'),('Corvidae','Re-roll To Hit rolls of 1 on First Fire; Psychic Mastery also applies to Overwatch, Return Fire and Stand & Shoot.'),('Athanaeans','Stubborn and re-roll failed Pinning tests; Psychic Mastery also grants Adamantium Will.'),('Pyrae','Hammer of Wrath; Psychic Mastery gives Soul Blaze to close-combat attacks and Flame weapons.')]
 es=ET.SubElement(g,C('selectionEntries'))
 for i,(n,t) in enumerate(data):
  e=ET.SubElement(es,C('selectionEntry'),{'id':g.get('id')+f'-{i}','name':n,'type':'upgrade','hidden':'false','import':'true'});constraint(e,e.get('id')+'-max','max',1);rule(e,e.get('id')+'-rule',n,t)

for p in list(cr.iter()):
 for x in list(p):
  if x.get('id','').startswith('r45-'):p.remove(x)
for p in list(gr.iter()):
 for x in list(p):
  if x.get('id','').startswith('r45-'):p.remove(x)

# XII — WORLD EATERS
we_chain=shared_up('r45-we-chainaxe','Chainaxe',4,'Replace an eligible Close Combat Weapon. User Strength, Chainaxe: Armour Saves better than 4+ are reduced to 4+; 4+ or worse and Invulnerable Saves are unaffected.')
we_caedere=shared_up('r45-we-caedere','Caedere Weapon',15,'World Eaters Independent Character or squad Sergeant. User +1 Strength, Rending, one-handed; does not count as a Power Weapon.')
we_chain_discount=shared_up('r45-we-chainaxe-berserker','Chainaxe — Berserker Assault price',2,'Berserker Assault only. Legion Assault Squad and Rampager models may purchase Chainaxes for +2 points per model instead of +4.')
for uid in ['hq-praetor','hq-centurion']:
 link(uid,we_chain.get('id'),f'r45-{uid}-we-chain','legion-xii');link(uid,we_caedere.get('id'),f'r45-{uid}-we-caedere','legion-xii')
for uid in ['tactical-unit','assault-unit','breacher-unit','veteran-unit','destroyer-unit','r41-unit-xii-0-rampager-squad']:
 link(uid,we_chain.get('id'),f'r45-{uid}-we-chain','legion-xii',hide_selector='r25-rite-xii-0-berserker-assault' if uid in ['assault-unit','r41-unit-xii-0-rampager-squad'] else None)
 if uid in ['assault-unit','r41-unit-xii-0-rampager-squad']:link(uid,we_chain_discount.get('id'),f'r45-{uid}-we-chain-discount','legion-xii',extra=[('atLeast',1,'force','r25-rite-xii-0-berserker-assault')])
gst_set('fl-heavy','fl-heavy-max',1,'r25-rite-xii-0-berserker-assault','r45-we-berserker-heavy-max')

# XIII — ULTRAMARINES
um_axe=shared_up('r45-um-legatine-axe','Legatine Axe',20,'Ultramarines Independent Character with Armoury access. User +1 Strength, Power Weapon, Two-Handed.')
um_mantle=shared_up('r45-um-mantle','Mantle of Ultramar',20,'Ultramarines Praetor with Artificer Armour only. Exchanges it for a 2+ Armour Save, Feel No Pain (5+) and immunity to Blind for the bearer.')
for uid in ['hq-praetor','hq-centurion']:link(uid,um_axe.get('id'),f'r45-{uid}-um-axe','legion-xiii')
link('hq-praetor',um_mantle.get('id'),'r45-praetor-um-mantle','legion-xiii')
breacher=cby('breacher-unit')
if breacher is not None:
 es=ensure(breacher,'selectionEntries');e=ET.SubElement(es,C('selectionEntry'),{'id':'r45-um-breacher-power-weapon','name':'Replace Bolter with Power Weapon','type':'upgrade','hidden':'true','import':'true'});cost(e,5);constraint(e,'r45-um-breacher-power-weapon-max','max',20);gate(e,'legion-xiii');rule(e,'r45-um-breacher-power-weapon-rule','Breacher Power Weapons','Any model in an Ultramarines Breacher Siege Squad may replace its Bolter with a Power Weapon for +5 points. A model doing so may not also select another option which replaces its Bolter.')
gst_set('fl-hq','fl-hq-max',4,'legion-xiii','r45-um-hq-max')
gst_set('fl-hq','fl-hq-min',2,'r25-rite-xiii-0-the-logos-lectora','r45-um-logos-hq-min');gst_set('fl-troops','fl-troops-min',3,'r25-rite-xiii-0-the-logos-lectora','r45-um-logos-troops-min')

# XIV — DEATH GUARD
dg_man=shared_up('r45-dg-manreaper','Manreaper',20,'Death Guard Sergeant or Character with Armoury access. Two-Handed Power Weapon. At the start of each Assault phase roll D3 and gain that many Attacks; if all attacks target one separately targetable Independent Character/model, gain only +1. No bonus for a second close-combat weapon.')
dg_alchem=shared_up('r45-dg-alchem-flamer','Alchem Flamer replacement',0,'A Death Guard model with a Flamer or Heavy Flamer may replace it for free. Template, S2 AP5, Assault 1, Poisoned (3+). Combi-flamers may become Combi-Alchem Flamers for +4 points in addition to their normal cost.')
for uid in ['hq-praetor','hq-centurion']:
 link(uid,dg_man.get('id'),f'r45-{uid}-dg-man','legion-xiv')
for uid in ['tactical-unit','assault-unit','breacher-unit','veteran-unit','destroyer-unit','hs-heavy-support-squad']:
 link(uid,dg_alchem.get('id'),f'r45-{uid}-dg-alchem','legion-xiv')
# Footslogging Killers: exact shared 0-1 limit across Bike, Attack Bike and Land Speeder via hidden auxiliary category and DG-specific copies.
cats=ensure(gr,'categoryEntries',GNS);ET.SubElement(cats,G('categoryEntry'),{'id':'cat-dg-mobile','name':'Death Guard Mobile Support Limit','hidden':'true'})
force=gby('force-standard');fl=ensure(force,'categoryLinks',GNS);cl=ET.SubElement(fl,G('categoryLink'),{'id':'fl-dg-mobile','name':'Death Guard Mobile Support Limit','targetId':'cat-dg-mobile','hidden':'true'});cs=ET.SubElement(cl,G('constraints'));ET.SubElement(cs,G('constraint'),{'id':'r45-dg-mobile-max','field':'selections','scope':'parent','value':'1','type':'max','shared':'true','includeChildSelections':'false','includeChildForces':'false'})
for src,nid in [('fa-bike','r45-dg-bike'),('fa-attack-bike','r45-dg-attack-bike'),('fa-land-speeder','r45-dg-land-speeder')]:dg_clone(src,nid)

# XV — THOUSAND SONS
ts_force=shared_up('r45-ts-force-weapon','Prosperine Force Weapon upgrade',10,'Upgrade a Power Weapon to a Force Weapon. Follows normal Force Weapon rules; a Psychic Brotherhood may attempt only one Force Weapon activation per Assault phase and only wounds caused by the nominated model become Massive Wounds/D3 Wounds.')
ts_lit=shared_up('r45-ts-arcane-litanies','Arcane Litanies',10,'Thousand Sons Independent Character with Mastery Level 1+. Once per battle, ignore one Wound suffered from Perils of the Warp; the test and power are otherwise resolved normally.')
ts_asphyx_ic=shared_up('r45-ts-asphyx-ic','Asphyx Shells',10,'Thousand Sons Independent Character. Bolt Pistols, Bolters, Combi-Bolters and bolter components of Combi-Weapons gain Shred. Cannot combine with Special Issue Ammunition or another ammunition upgrade.')
ts_asphyx_unit=shared_up('r45-ts-asphyx-unit','Asphyx Shells',20,'Thousand Sons Veteran or Terminator Squad. Bolt Pistols, Bolters, Combi-Bolters and bolter components of Combi-Weapons gain Shred. Cannot combine with Special Issue Ammunition or another ammunition upgrade.')
ts_trans_ic=shared_up('r45-ts-trans-ic','Teleportation Transponders',10,'Thousand Sons Independent Character in Terminator Armour. Gains Deep Strike even if the mission would not normally allow it.')
ts_trans_unit=shared_up('r45-ts-trans-unit','Teleportation Transponders',15,'Thousand Sons unit entirely in Terminator Armour. Gains Deep Strike even if the mission would not normally allow it.')
ts_aether=shared_up('r45-ts-aether-fire','Æther-fire Cannon upgrade',0,'Any Plasma Cannon may be upgraded for free; if a unit has multiple Plasma Cannons all or none must upgrade. 36”, S7 AP2, Heavy 1, Blast, Gets Hot, Soul Blaze.')
ts_brother=shared_up('r45-ts-brotherhood','Brotherhood of Psykers (Mastery Level 1)',25,'Veteran or Terminator Squad. The unit becomes Brotherhood of Psykers (ML1), selects one power from the discipline associated with its Prosperine Cult, and gains that Cult’s Cult Mastery benefit.')
ts_brother_fellow=shared_up('r45-ts-brotherhood-fellowship','Brotherhood of Psykers (Fellowships price)',15,'Fellowships of Prospero only. Veteran/Terminator Squads purchase Brotherhood of Psykers (ML1) for +15 instead of +25.')
ts_tac_brother=shared_up('r45-ts-tactical-brotherhood','Brotherhood of Psykers (20-model Tactical Squad)',25,'Fellowships of Prospero only. A 20-model Tactical Squad may purchase Brotherhood of Psykers (ML1), choose a power from its Cult discipline and gain Cult Mastery.')
for uid in ['hq-praetor','hq-centurion']:
 for it in [ts_force,ts_lit,ts_asphyx_ic,ts_trans_ic]:link(uid,it.get('id'),f'r45-{uid}-{it.get("id")}','legion-xv')
for uid in ['veteran-unit','terminator-unit']:
 link(uid,ts_asphyx_unit.get('id'),f'r45-{uid}-ts-asphyx','legion-xv');link(uid,ts_brother.get('id'),f'r45-{uid}-ts-brother','legion-xv',hide_selector='r25-rite-xv-2-the-fellowships-of-prospero');link(uid,ts_brother_fellow.get('id'),f'r45-{uid}-ts-brother-fellow','legion-xv',extra=[('atLeast',1,'force','r25-rite-xv-2-the-fellowships-of-prospero')])
link('terminator-unit',ts_trans_unit.get('id'),'r45-terminator-ts-trans','legion-xv')
# Tactical Brotherhood only when Fellowships selected and the base squad reaches 20 models.
link('tactical-unit',ts_tac_brother.get('id'),'r45-tactical-ts-brother','legion-xv',extra=[('atLeast',1,'force','r25-rite-xv-2-the-fellowships-of-prospero'),('atLeast',20,'parent','tac-marine')])
link('hs-heavy-support-squad',ts_aether.get('id'),'r45-hss-ts-aether','legion-xv')
# Cult selection on core Infantry and applicable XV unique Infantry/characters.
for uid in ['hq-praetor','hq-centurion','tactical-unit','assault-unit','breacher-unit','recon-unit','veteran-unit','terminator-unit','fa-seeker','hs-heavy-support-squad','r41-unit-xv-0-sekhmet-terminator-cabal','r41-unit-xv-1-khenetai-occult-blade-cabal','r41-unit-xv-2-ammitara-occult-intercession-cabal','r41-unit-xv-5-numerologist-cabal','r41-unit-xv-6-ahzek-ahriman','r41-unit-xv-7-phosis-t-kar','r41-unit-xv-8-magistus-amon-the-hidden','r41-unit-xv-9-hathor-maat','r41-unit-xv-10-sanakht']:
 cult_group(uid)

cr.set('revision','45');gr.set('revision',str(int(gr.get('revision','16'))+1));cr.set('gameSystemRevision',gr.get('revision'))
comment=cr.find(C('comment'))
if comment is not None:comment.text='Revision 45: New Recruit interaction pass for Legions XII-XV, including World Eaters pit weapons, Ultramarines command/FoC changes, Death Guard mobile-support restriction, and Thousand Sons Cult/Psychic Brotherhood selections.'
ct.write(CAT,encoding='UTF-8',xml_declaration=True);gt.write(GST,encoding='UTF-8',xml_declaration=True)
print('REV45 COMPLETE',cr.get('revision'),gr.get('revision'))
