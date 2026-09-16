from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()
LEG='legion-ix'; REV='r25-rite-ix-0-the-day-of-revelation'; SOR='r25-rite-ix-1-the-day-of-sorrows'; SANG='r41-unit-ix-11-ix-sanguinius-the-great-angel'


def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,tag,ns=CNS):
    q=f'{{{ns}}}{tag}'; x=p.find(q)
    if x is None:x=ET.SubElement(p,q)
    return x
def wipe(p,tag,ns=CNS):
    q=f'{{{ns}}}{tag}'; x=p.find(q)
    if x is not None:p.remove(x)
def constraint(p,id_,typ,val,scope='parent',ns=CNS):
    E=C if ns==CNS else G
    x=ET.SubElement(ensure(p,'constraints',ns),E('constraint'),{'id':id_,'type':typ,'value':str(val),'field':'selections','scope':scope,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return x
def add_rule(p,id_,name,text):
    r=ET.SubElement(ensure(p,'rules'),C('rule'),{'id':id_,'name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=text; return r
def add_entry(p,id_,name,cost=0,hidden='false'):
    e=ET.SubElement(ensure(p,'selectionEntries'),C('selectionEntry'),{'id':id_,'name':name,'type':'upgrade','hidden':hidden,'import':'true'});constraint(e,id_+'-max','max',1)
    ET.SubElement(ensure(e,'costs'),C('cost'),{'name':'Points','typeId':'pts','value':str(cost)});return e
def add_cat(e,id_,target,name,primary='false'):
    if any(x.get('targetId')==target for x in e.findall('./'+C('categoryLinks')+'/'+C('categoryLink'))):return
    ET.SubElement(ensure(e,'categoryLinks'),C('categoryLink'),{'id':id_,'name':name,'hidden':'false','targetId':target,'primary':primary})
def add_show(e,id_,conds):
    e.set('hidden','true')
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':id_,'type':'set','value':'false','field':'hidden'})
    cs=ET.SubElement(m,C('conditions'))
    for typ,val,scope,child in conds:
        ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def remove_prefix(root,prefix):
    for p in list(root.iter()):
        for x in list(p):
            if (x.get('id') or '').startswith(prefix):p.remove(x)
def owner_top(node):
    pm={c:p for p in cr.iter() for c in p}; x=node
    while x is not None:
        if x.tag==C('selectionEntry') and x.get('type')=='unit': return x
        x=pm.get(x)
    return None

# Safe re-run cleanup.
remove_prefix(cr,'r75-ba-'); remove_prefix(gr,'r75-ba-')

# ---------------------------------------------------------------------------
# 1) PRESENTATION FIX: remove nested Source Entry / aggregate import dumps.
# Rev74 only checked rules directly on the top-level unit; New Recruit also renders
# rules nested on the real model child. Scrub the entire subtree of every canonical
# and generated Blood Angels entry.
# ---------------------------------------------------------------------------
TARGET_PREFIXES=('r41-unit-ix-','r74-ba-')
removed=[]
for unit in list(cr.iter(C('selectionEntry'))):
    uid=unit.get('id') or ''
    if unit.get('type')!='unit' or not uid.startswith(TARGET_PREFIXES):continue
    for parent in list(unit.iter()):
        rs=parent.find(C('rules'))
        if rs is None:continue
        for r in list(rs.findall(C('rule'))):
            name=(r.get('name') or '').strip().lower(); desc=(r.findtext(C('description')) or '')
            source_dump = name.startswith('source entry') or ('force organisation:' in desc.lower() and 'wargear:' in desc.lower() and 'special rules:' in desc.lower())
            if source_dump:
                removed.append((uid,r.get('id'),r.get('name'))); rs.remove(r)

# ---------------------------------------------------------------------------
# 2) RITES: present every named effect/limitation as an actual rule, then enforce
# every roster-state restriction New Recruit can safely know.
# ---------------------------------------------------------------------------
rev=byid(cr,REV); sor=byid(cr,SOR)
if rev is None or sor is None: raise RuntimeError('Missing Blood Angels Rite entries')
wipe(rev,'rules'); wipe(sor,'rules')
add_rule(rev,'r75-ba-rev-host','Host of Angels','Legion Veteran Squads equipped with Jump Packs may be selected as Troops choices and may fulfil compulsory Troops selections. Legion Assault Squads remain Troops choices normally.')
add_rule(rev,'r75-ba-rev-revealed','The Day is Revealed','Blood Angels units composed entirely of Jump Infantry may deploy using Deep Strike even if the mission would not normally permit it. All Jump Infantry units placed in Reserve using this Rite must enter play using Deep Strike.')
add_rule(rev,'r75-ba-rev-wings','On Wings of Fire','At the beginning of the second Blood Angels player turn, all Blood Angels Jump Infantry units currently held in Reserve become available automatically. No Reserve rolls are made and they must enter play during that turn using Deep Strike.')
add_rule(rev,'r75-ba-rev-shock','Angelic Shock Assault','A Blood Angels Jump Infantry unit which charges during the same turn it arrived using Deep Strike receives the normal +1 Attack bonus for charging and the normal benefits of any Assault Grenades it carries. This overrides the normal ProHammer restriction on charging after Deep Strike. All other Deep Strike rules apply normally.')
add_rule(rev,'r75-ba-rev-limits','Limitations','The army Warlord must be equipped with a Jump Pack. At least half of the non-Vehicle units in the Detachment, rounding up, must be composed entirely of models equipped with Jump Packs. Every Jump Infantry unit must begin the battle in Reserve and enter play using Deep Strike. The Detachment may include no more than one Heavy Support choice and may not include a Fortification. New Recruit enforces the Warlord, compulsory Troops and Heavy Support restrictions; the half-army ratio and deployment-state restrictions remain player-checked.')
add_rule(sor,'r75-ba-sor-bitter','The Bitter End','When a non-Vehicle Blood Angels unit is reduced to half or fewer of the number of models with which it began the battle, it gains Stubborn and Feel No Pain (6+). These rules remain for the rest of the battle. If it already has Feel No Pain, improve that roll by one step instead, to a maximum of 4+.')
add_rule(sor,'r75-ba-sor-fury','Sorrow Becomes Fury','A Blood Angels unit affected by The Bitter End gains +1 to its combat-resolution score whenever it wins a close combat. This bonus is not cumulative.')
add_rule(sor,'r75-ba-sor-death','No Death Unremembered','Whenever a Blood Angels unit affected by The Bitter End is completely destroyed, every friendly non-Vehicle Blood Angels unit with at least one model within 6 inches may re-roll its next failed Morale or Pinning test before the end of the following Blood Angels player turn.')
add_rule(sor,'r75-ba-sor-hold','Hold Until the Last','Legion Tactical Squads and Legion Breacher Siege Squads may re-roll failed Pinning tests while they have at least one model within 6 inches of an Objective.')
add_rule(sor,'r75-ba-sor-limits','Limitations','The army compulsory Troops choices must be selected from Legion Tactical Squads, Legion Assault Squads or Legion Breacher Siege Squads. Units affected by The Bitter End may not voluntarily withdraw from close combat. If such a unit wins a close combat and the enemy retreats, it must Pursue whenever normally permitted. The Detachment may not include a Fortification.')

# Ensure Rite entries are IX Legion only.
for rite,pfx in ((rev,'rev'),(sor,'sor')):
    add_show(rite,f'r75-ba-{pfx}-legion-show',[('atLeast',1,'roster',LEG)])

# Existing Rev74 compulsory-Troops machinery: validate it and restore if absent.
def ensure_gst_category(cat_id,name,selector,minv):
    ces=ensure(gr,'categoryEntries',GNS); cat=byid(gr,cat_id)
    if cat is None: cat=ET.SubElement(ces,G('categoryEntry'),{'id':cat_id,'name':name,'hidden':'true'})
    force=byid(gr,'force-standard')
    if force is None: raise RuntimeError('Missing force-standard')
    links=ensure(force,'categoryLinks',GNS); l=next((x for x in links.findall(G('categoryLink')) if x.get('targetId')==cat_id),None)
    if l is None:l=ET.SubElement(links,G('categoryLink'),{'id':'r75-ba-fl-'+cat_id,'name':name,'hidden':'true','targetId':cat_id})
    cs=ensure(l,'constraints',GNS); c=next((x for x in cs.findall(G('constraint')) if x.get('type')=='min'),None)
    if c is None:c=constraint(l,'r75-ba-'+cat_id+'-min','min',0,ns=GNS)
    else:c.set('value','0')
    m=ET.SubElement(ensure(l,'modifiers',GNS),G('modifier'),{'id':'r75-ba-'+cat_id+'-set','type':'set','value':str(minv),'field':c.get('id')})
    conds=ET.SubElement(m,G('conditions'));ET.SubElement(conds,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return cat_id
REV_CAT=ensure_gst_category('r74-ba-cat-revelation-comp','Day of Revelation — compulsory Assault/Jump Veteran Troops',REV,2)
SOR_CAT=ensure_gst_category('r74-ba-cat-sorrows-comp','Day of Sorrows — compulsory Tactical/Assault/Breacher Troops',SOR,2)
rv=byid(cr,'r74-ba-rev-vet-veteran-unit'); ass=byid(cr,'assault-unit'); tac=byid(cr,'tactical-unit'); bre=byid(cr,'breacher-unit')
if rv is None: raise RuntimeError('Missing Day of Revelation Jump Veteran Troops clone')
for e,cid,n in ((rv,REV_CAT,'Revelation compulsory Troops'),(ass,REV_CAT,'Revelation compulsory Troops'),(ass,SOR_CAT,'Sorrows compulsory Troops'),(tac,SOR_CAT,'Sorrows compulsory Troops'),(bre,SOR_CAT,'Sorrows compulsory Troops')):
    if e is not None:add_cat(e,'r75-ba-'+(e.get('id') or 'entry')[-30:]+'-'+cid,cid,n)

# Day of Revelation: max one Heavy Support.
heavy=byid(gr,'fl-heavy')
if heavy is None:raise RuntimeError('Missing fl-heavy')
heavymax=next((x for x in heavy.findall('./'+G('constraints')+'/'+G('constraint')) if x.get('type')=='max'),None)
if heavymax is None:raise RuntimeError('Missing Heavy Support max constraint')
m=ET.SubElement(ensure(heavy,'modifiers',GNS),G('modifier'),{'id':'r75-ba-rev-heavy-max','type':'set','value':'1','field':heavymax.get('id')})
cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':REV,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# If a Fortification category/slot exists now or is added later in this data set, set it to zero for both Rites.
for l in gr.iter(G('categoryLink')):
    n=(l.get('name') or '').lower()
    if 'fortification' not in n:continue
    mx=next((x for x in l.findall('./'+G('constraints')+'/'+G('constraint')) if x.get('type')=='max'),None)
    if mx is None:continue
    for selector,slug in ((REV,'rev'),(SOR,'sor')):
        mm=ET.SubElement(ensure(l,'modifiers',GNS),G('modifier'),{'id':f'r75-ba-{slug}-no-fort-{l.get("id")}','type':'set','value':'0','field':mx.get('id')});cc=ET.SubElement(mm,G('conditions'));ET.SubElement(cc,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Day of Revelation Warlord must actually have a Jump Pack.
WARCAT=ensure_gst_category('r75-ba-cat-rev-warlord-jump','Day of Revelation — Warlord with Jump Pack',REV,1)
def add_warlord_marker(owner_id,jump_id,label):
    u=byid(cr,owner_id)
    if u is None:return None
    e=add_entry(u,'r75-ba-'+owner_id+'-rev-warlord','Designate as Day of Revelation Warlord',0,'true')
    add_cat(e,e.get('id')+'-cat',WARCAT,'Day of Revelation — Warlord with Jump Pack')
    add_show(e,e.get('id')+'-show',[('atLeast',1,'roster',LEG),('atLeast',1,'roster',REV),('atLeast',1,'root-entry',jump_id),('lessThan',1,'roster',SANG)])
    add_rule(e,e.get('id')+'-rule','Day of Revelation Warlord',label)
    return e
add_warlord_marker('hq-praetor','hq-praetor-jump','This Praetor is the army Warlord for The Day of Revelation and is equipped with a Jump Pack.')
add_warlord_marker('hq-centurion','hq-centurion-jump','This Centurion is the army Warlord for The Day of Revelation and is equipped with a Jump Pack.')
add_warlord_marker('r41-unit-ix-7-dominion-zephon','r74-ba-zephon-jump','Dominion Zephon is the army Warlord for The Day of Revelation; his fixed wargear includes a Jump Pack.')
# Deliberately no Sanguinius marker: the source says Jump Pack; Great Wings are not silently rewritten as a Jump Pack.

# ---------------------------------------------------------------------------
# 3) Remaining Blood Angels mechanical restrictions from the prior audit.
# ---------------------------------------------------------------------------
# Furioso-pattern Jump Pack: only on a Contemptor with BOTH DCCWs.
cont=byid(cr,'contemptor-unit'); fj=byid(cr,'r74-ba-contemptor-jump')
if cont is not None and fj is not None:
    wipe(fj,'modifiers')
    add_show(fj,'r75-ba-furioso-show',[('atLeast',1,'roster',LEG),('atLeast',1,'root-entry','contemptor-p-dccw'),('atLeast',1,'root-entry','contemptor-s-dccw')])

# Blade of Perdition +10 exchange only when an actual Power Weapon is selected.
for u in (byid(cr,'hq-praetor'),byid(cr,'hq-centurion')):
    if u is None:continue
    for l in u.iter(C('entryLink')):
        if l.get('targetId')!='r74-ba-blade-exchange':continue
        wipe(l,'modifiers')
        add_show(l,'r75-ba-'+(l.get('id') or 'blade')[-35:]+'-show',[('atLeast',1,'roster',LEG),('atLeast',1,'root-entry','gear-power-weapon')])

# Death Mask is explicitly available to Blood Angels Independent Characters.
mask=byid(cr,'r44-ba-death-mask')
if mask is not None:
    for cid in ('r41-unit-ix-6-raldoron-the-blooded','r41-unit-ix-7-dominion-zephon','r41-unit-ix-8-aster-crohne','r41-unit-ix-10-nassir-amit-the-flesh-tearer'):
        u=byid(cr,cid)
        if u is None:continue
        if any(x.get('targetId')==mask.get('id') for x in u.findall('./'+C('entryLinks')+'/'+C('entryLink'))):continue
        l=ET.SubElement(ensure(u,'entryLinks'),C('entryLink'),{'id':'r75-ba-'+cid+'-death-mask','name':'Death Mask','type':'selectionEntry','targetId':mask.get('id'),'hidden':'true','import':'true'});constraint(l,l.get('id')+'-max','max',1);add_show(l,l.get('id')+'-show',[('atLeast',1,'roster',LEG)])

# ---------------------------------------------------------------------------
# 4) VALIDATION: catch the exact New Recruit bug shown by the user.
# ---------------------------------------------------------------------------
# No Source Entry/aggregate dump may remain ANYWHERE in canonical/generated BA unit subtrees.
left=[]
for unit in cr.iter(C('selectionEntry')):
    uid=unit.get('id') or ''
    if unit.get('type')!='unit' or not uid.startswith(TARGET_PREFIXES):continue
    for r in unit.iter(C('rule')):
        n=(r.get('name') or '').lower(); d=(r.findtext(C('description')) or '').lower()
        if n.startswith('source entry') or ('force organisation:' in d and 'wargear:' in d and 'special rules:' in d):left.append((uid,r.get('id'),r.get('name')))
if left:raise RuntimeError('BA Source Entry dumps remain: '+repr(left[:20]))
# Aster Crohne specifically: only actual named rules, never imported source dump text.
crohne=byid(cr,'r41-unit-ix-8-aster-crohne')
if crohne is None:raise RuntimeError('Aster Crohne missing')
if any('source entry' in (r.get('name') or '').lower() for r in crohne.iter(C('rule'))):raise RuntimeError('Aster Crohne Source Entry still renders')
# Rite rules are individually named and both mechanical compulsory categories exist.
for rite,names in ((rev,{'Host of Angels','The Day is Revealed','On Wings of Fire','Angelic Shock Assault','Limitations'}),(sor,{'The Bitter End','Sorrow Becomes Fury','No Death Unremembered','Hold Until the Last','Limitations'})):
    have={r.get('name') for r in rite.findall('./'+C('rules')+'/'+C('rule'))}
    if not names.issubset(have):raise RuntimeError('Rite presentation incomplete: '+repr(names-have))
for cid in (REV_CAT,SOR_CAT,WARCAT):
    if byid(gr,cid) is None:raise RuntimeError('Missing BA Rite category '+cid)
# Jump Veteran clone must have at least one mandatory Jump Pack selection.
jps=[e for e in rv.iter(C('selectionEntry')) if 'jump pack' in (e.get('name') or '').lower()]
if not jps:raise RuntimeError('Revelation Veteran clone lacks Jump Packs')
if not any(any(c.get('type')=='min' and float(c.get('value','0'))>=1 for c in e.findall('./'+C('constraints')+'/'+C('constraint'))) or float(e.get('defaultAmount','0') or 0)>=1 for e in jps):raise RuntimeError('Revelation Veteran Jump Packs are not mandatory')
# Duplicate IDs and parseability.
for root,label in ((cr,'CAT'),(gr,'GST')):
    seen=set();dup=[]
    for x in root.iter():
        i=x.get('id')
        if not i:continue
        if i in seen:dup.append(i)
        seen.add(i)
    if dup:raise RuntimeError(f'Duplicate {label} IDs: {dup[:20]}')

# Revision bump for New Recruit cache refresh.
cr.set('revision','75');cr.set('gameSystemRevision','43');gr.set('revision','43')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat':e.set('dataRevision','75')
    elif e.get('filePath')=='Prohammer 30k.gst':e.set('dataRevision','43')

ET.indent(ct,space='  '); ET.register_namespace('',CNS); ct.write(CAT,encoding='utf-8',xml_declaration=True)
ET.indent(gt,space='  '); ET.register_namespace('',GNS); gt.write(GST,encoding='utf-8',xml_declaration=True)
ET.indent(it,space='  '); ET.register_namespace('',INS); it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT);ET.parse(GST);ET.parse(IDX)

Path('inspection-r75-blood-angels-cleanup.txt').write_text(f'''Revision 75 — Blood Angels Source Entry cleanup + complete Rite pass\nCatalogue revision: 75\nGame-system revision: 43\n\nPresentation\n- Removed {len(removed)} nested Blood Angels Source Entry / aggregate import rule blocks, including model-child dumps that Rev74 did not detect.\n- Aster Crohne is explicitly validated against the exact duplicate Source Entry presentation bug reported in New Recruit.\n\nThe Day of Revelation\n- Host of Angels, The Day is Revealed, On Wings of Fire, Angelic Shock Assault and Limitations are separate actual rule blocks.\n- Jump Pack Veteran Troops remain a Rite-gated Troops choice with mandatory Jump Packs and can satisfy the hidden compulsory-Troops requirement.\n- Assault Squads and Jump Veteran Troops satisfy the two compulsory Troops requirement.\n- Heavy Support is limited to 0-1.\n- A hidden validation category now requires a designated Warlord actually equipped with a Jump Pack. Praetor/Centurion markers only appear with their Jump Pack selected; Zephon qualifies through fixed wargear.\n- Sanguinius deliberately does not satisfy the Jump Pack requirement: Great Wings were not silently redefined as a Jump Pack.\n- The half-of-non-Vehicle-units Jump Pack ratio and Reserve/Deep Strike deployment state remain player-checked because New Recruit cannot safely infer those roster/battlefield states.\n- Fortifications are set to 0 automatically if a Fortification slot exists in the game system.\n\nThe Day of Sorrows\n- The Bitter End, Sorrow Becomes Fury, No Death Unremembered, Hold Until the Last and Limitations are separate actual rule blocks.\n- Compulsory Troops are mechanically restricted to Tactical, Assault and Breacher Squads through the hidden compulsory category.\n- Voluntary withdrawal/Pursuit effects remain readable battlefield rules.\n- Fortifications are set to 0 automatically if a Fortification slot exists.\n\nOther BA restrictions\n- Furioso-pattern Jump Pack now appears only when a Contemptor has BOTH Dreadnought Close Combat Weapons.\n- Blade of Perdition +10 exchange now requires an actually selected Power Weapon on Praetor/Centurion.\n- Raldoron, Zephon, Crohne and Amit receive explicit Death Mask access as Blood Angels Independent Characters.\n\nValidation\n- No Source Entry/aggregate dump remains anywhere under canonical/generated Blood Angels unit subtrees.\n- Both Rite presentations and their functional roster restrictions validate.\n- Duplicate IDs and XML parsing validate.\n''',encoding='utf-8')
print(Path('inspection-r75-blood-angels-cleanup.txt').read_text())