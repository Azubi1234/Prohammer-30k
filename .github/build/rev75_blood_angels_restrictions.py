from pathlib import Path
import xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat');GST=Path('Prohammer 30k.gst');IDX=Path('index.xml');OUT=Path('inspection-r75-blood-angels-restrictions.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema';GNS='http://www.battlescribe.net/schema/gameSystemSchema';INS='http://www.battlescribe.net/schema/dataIndexSchema'
C=lambda t:f'{{{CNS}}}{t}';G=lambda t:f'{{{GNS}}}{t}';I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT);cr=ct.getroot();gt=ET.parse(GST);gr=gt.getroot();it=ET.parse(IDX);ir=it.getroot()
if cr.get('revision')!='74' or gr.get('revision')!='42':raise RuntimeError(f'Expected CAT74/GST42, got {cr.get("revision")}/{gr.get("revision")}')
LEG='legion-ix';REV='r25-rite-ix-0-the-day-of-revelation';SANG='r41-unit-ix-11-ix-sanguinius-the-great-angel';WARCAT='r75-ba-cat-revelation-warlord'
def byid(root,i):return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t,ns=CNS):
 Q=C if ns==CNS else (G if ns==GNS else I);x=p.find(Q(t))
 if x is None:x=ET.SubElement(p,Q(t))
 return x
def wipe(p,t,ns=CNS):
 Q=C if ns==CNS else G;x=p.find(Q(t))
 if x is not None:p.remove(x)
def remove_pref(root,pfx):
 for p in list(root.iter()):
  for x in list(p):
   if (x.get('id') or '').startswith(pfx):p.remove(x)
def constraint(p,i,typ,val,field='selections',scope='parent',ns=CNS):
 Q=C if ns==CNS else G;return ET.SubElement(ensure(p,'constraints',ns),Q('constraint'),{'id':i,'type':typ,'value':str(val),'field':field,'scope':scope,'shared':'true','includeChildSelections':'false','includeChildForces':'false'})
def add_cat(e,i,target,name):
 ET.SubElement(ensure(e,'categoryLinks'),C('categoryLink'),{'id':i,'name':name,'hidden':'true','targetId':target,'primary':'false'})
def add_upgrade(parent,i,name):
 e=ET.SubElement(ensure(parent,'selectionEntries'),C('selectionEntry'),{'id':i,'name':name,'type':'upgrade','hidden':'true','import':'true'});constraint(e,i+'-max','max',1);ET.SubElement(ensure(e,'costs'),C('cost'),{'name':'Points','typeId':'pts','value':'0'});return e
def show_all(e,i,conds):
 e.set('hidden','true');wipe(e,'modifiers');m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'});gs=ET.SubElement(m,C('conditionGroups'));cg=ET.SubElement(gs,C('conditionGroup'),{'type':'and'});cs=ET.SubElement(cg,C('conditions'))
 for typ,val,scope,child in conds:ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def hide_if_selected(e,i,child,scope='roster'):
 m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'true','field':'hidden'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def entry_link(parent,i,name,target):
 l=ET.SubElement(ensure(parent,'entryLinks'),C('entryLink'),{'id':i,'name':name,'type':'selectionEntry','targetId':target,'hidden':'true','import':'true'});constraint(l,i+'-max','max',1);return l
# Safe rerun hygiene.
remove_pref(cr,'r75-ba-');remove_pref(gr,'r75-ba-')

# 1) Remove redundant direct Inferno/Blade purchases from generic HQ roots. Their real Armoury groups already carry these items.
for uid in ('hq-praetor','hq-centurion'):
 u=byid(cr,uid)
 if u is None:raise RuntimeError('Missing '+uid)
 links=u.find(C('entryLinks'))
 if links is not None:
  for x in list(links):
   if x.get('id') in (f'r74-ba-{uid}-r44-ba-inferno-pistol',f'r74-ba-{uid}-r44-ba-blade-perdition'):links.remove(x)
 # Power-Weapon exchange remains a root-level special option but only appears after a Power Weapon has actually been selected.
 ex=byid(cr,f'r74-ba-{uid}-r74-ba-blade-exchange')
 if ex is not None:show_all(ex,f'r75-ba-{uid}-blade-exchange-show',[('atLeast',1,'roster',LEG),('atLeast',1,'root-entry','gear-power-weapon')])

# 2) Death Mask is explicitly available to any Blood Angels Independent Character, including named ICs.
for key in ('r41-unit-ix-6-raldoron-the-blooded','r41-unit-ix-7-dominion-zephon','r41-unit-ix-8-aster-crohne','r41-unit-ix-10-nassir-amit-the-flesh-tearer'):
 u=byid(cr,key)
 if u is None:raise RuntimeError('Missing named BA IC '+key)
 l=entry_link(u,'r75-ba-'+key+'-death-mask','Death Mask','r44-ba-death-mask');show_all(l,l.get('id')+'-show',[('atLeast',1,'roster',LEG)])

# 3) Furioso-pattern Jump Pack only exists when BOTH Contemptor arms are Dreadnought Close Combat Weapons.
cont=byid(cr,'contemptor-unit');fur=byid(cr,'r74-ba-contemptor-jump')
if cont is None or fur is None:raise RuntimeError('Missing Contemptor or BA Furioso link')
show_all(fur,'r75-ba-furioso-show',[('atLeast',1,'roster',LEG),('atLeast',1,'root-entry','contemptor-p-dccw'),('atLeast',1,'root-entry','contemptor-s-dccw')])

# 4) Day of Revelation: exact one Warlord with a Jump Pack.
# Hidden category and Standard-force requirement.
ces=ensure(gr,'categoryEntries',GNS);ET.SubElement(ces,G('categoryEntry'),{'id':WARCAT,'name':'Day of Revelation — Warlord with Jump Pack','hidden':'true'})
force=byid(gr,'force-standard');fl=ensure(force,'categoryLinks',GNS);cl=ET.SubElement(fl,G('categoryLink'),{'id':'r75-ba-fl-revelation-warlord','name':'Day of Revelation — Warlord with Jump Pack','hidden':'true','targetId':WARCAT})
minid='r75-ba-rev-warlord-min';maxid='r75-ba-rev-warlord-max';constraint(cl,minid,'min',0,ns=GNS);constraint(cl,maxid,'max',99,ns=GNS)
for cid,val in ((minid,1),(maxid,1)):
 m=ET.SubElement(ensure(cl,'modifiers',GNS),G('modifier'),{'id':cid+'-set','type':'set','value':str(val),'field':cid});cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':REV,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
# Generic Praetor/Centurion markers require the actual Jump Pack entry-link selection.
for uid,jumpid,slug in (('hq-praetor','hq-praetor-jump','praetor'),('hq-centurion','hq-centurion-jump','centurion')):
 u=byid(cr,uid);e=add_upgrade(u,f'r75-ba-rev-{slug}-warlord','Designate as Day of Revelation Warlord')
 add_cat(e,e.get('id')+'-cat',WARCAT,'Day of Revelation — Warlord with Jump Pack')
 show_all(e,e.get('id')+'-show',[('atLeast',1,'roster',LEG),('atLeast',1,'roster',REV),('atLeast',1,'root-entry',jumpid)])
 # A Primarch must be the Warlord; Sanguinius has Great Wings, not a Jump Pack under the current written restriction.
 hide_if_selected(e,e.get('id')+'-hide-sanguinius',SANG)
# Dominion Zephon is explicitly equipped with a Jump Pack.
ze=byid(cr,'r41-unit-ix-7-dominion-zephon');e=add_upgrade(ze,'r75-ba-rev-zephon-warlord','Designate as Day of Revelation Warlord');add_cat(e,e.get('id')+'-cat',WARCAT,'Day of Revelation — Warlord with Jump Pack');show_all(e,e.get('id')+'-show',[('atLeast',1,'roster',LEG),('atLeast',1,'roster',REV)]);hide_if_selected(e,e.get('id')+'-hide-sanguinius',SANG)

# Add a clear builder note to the Rite without replacing its source-derived rules.
rite=byid(cr,REV);rs=ensure(rite,'rules');r=ET.SubElement(rs,C('rule'),{'id':'r75-ba-rev-builder-warlord','name':'Day of Revelation — Warlord Requirement','hidden':'false'});ET.SubElement(r,C('description')).text='New Recruit requires exactly one qualifying Day of Revelation Warlord designation. A generic Praetor or Centurion may only be designated after selecting a Jump Pack; Dominion Zephon qualifies by his fixed Jump Pack. Under the current written wording Sanguinius has Great Wings rather than a Jump Pack, so his presence prevents another model from satisfying the Warlord requirement.'

# Validation.
for uid in ('hq-praetor','hq-centurion'):
 u=byid(cr,uid);assert not any(x.get('id') in (f'r74-ba-{uid}-r44-ba-inferno-pistol',f'r74-ba-{uid}-r44-ba-blade-perdition') for x in u.findall('./'+C('entryLinks')+'/'+C('entryLink')))
assert byid(gr,WARCAT) is not None and byid(gr,'r75-ba-fl-revelation-warlord') is not None
assert byid(cr,'r75-ba-rev-praetor-warlord') is not None and byid(cr,'r75-ba-rev-centurion-warlord') is not None and byid(cr,'r75-ba-rev-zephon-warlord') is not None
# Furioso must have both DCCW child conditions.
conds=[c.get('childId') for c in fur.findall('.//'+C('condition'))];assert 'contemptor-p-dccw' in conds and 'contemptor-s-dccw' in conds
# Duplicate IDs.
for root,label in ((cr,'CAT'),(gr,'GST')):
 seen=set();dup=[]
 for x in root.iter():
  i=x.get('id')
  if not i:continue
  if i in seen:dup.append(i)
  seen.add(i)
 if dup:raise RuntimeError(f'Duplicate IDs {label}: {dup[:20]}')
# Revisions.
cr.set('revision','75');cr.set('gameSystemRevision','43');gr.set('revision','43')
for e in ir.iter(I('dataIndexEntry')):
 if e.get('filePath')=='Legiones Astartes.cat':e.set('dataRevision','75')
 elif e.get('filePath')=='Prohammer 30k.gst':e.set('dataRevision','43')
ET.indent(ct,space='  ');ET.indent(gt,space='  ');ET.indent(it,space='  ')
ET.register_namespace('',CNS);ct.write(CAT,encoding='utf-8',xml_declaration=True);ET.register_namespace('',GNS);gt.write(GST,encoding='utf-8',xml_declaration=True);ET.register_namespace('',INS);it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT);ET.parse(GST);ET.parse(IDX)
OUT.write_text('''Revision 75 — Blood Angels hard-restriction pass\nCatalogue revision: 75\nGame-system revision: 43\n\n- Removed redundant direct Inferno Pistol / Blade of Perdition links from generic Praetor and Centurion roots; their real Armoury groups remain the access point.\n- Blade of Perdition +10 exchange on generic HQs now appears only after an actual Power Weapon is selected.\n- Death Mask +10 added to Raldoron, Dominion Zephon, Aster Crohne and Nassir Amit because the Blood Angels Armoury explicitly permits any Blood Angels Independent Character to buy one.\n- Furioso-pattern Jump Pack now appears only when the Contemptor has a Dreadnought Close Combat Weapon in BOTH arm slots; its existing 0-1 army limit remains.\n- Day of Revelation now requires exactly one designated Warlord with a Jump Pack. Praetor/Centurion designations require their actual Jump Pack option; Dominion Zephon qualifies via fixed Jump Pack.\n- Sanguinius blocks those designations because universal Primarch rules force him to be Warlord, while the current Rite wording requires the Warlord to be equipped with a Jump Pack and his entry lists Great Wings instead. This is intentionally literal and should be changed only if the written source is changed or explicitly interpreted otherwise.\n- XML, duplicate-ID and hard-condition validation passed.\n''',encoding='utf-8');print(OUT.read_text())
