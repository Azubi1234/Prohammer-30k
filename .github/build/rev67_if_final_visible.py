from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r67-imperial-fists-final.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()

if cr.get('revision')!='66' or gr.get('revision')!='34':
    raise RuntimeError(f'Expected Rev66/34 baseline, got CAT {cr.get("revision")} GST {gr.get("revision")}')

def by_id(root,ident): return next((e for e in root.iter() if e.get('id')==ident),None)
def ensure(parent,tag,ns=CNS):
    q=f'{{{ns}}}{tag}'; x=parent.find(q)
    if x is None: x=ET.SubElement(parent,q)
    return x
def remove_pred(root,pred):
    for p in list(root.iter()):
        for x in list(p):
            if pred(x): p.remove(x)
def constraint(parent,ident,typ,value,field='selections',scope='parent',child=False,ns=CNS):
    T=C if ns==CNS else G
    return ET.SubElement(ensure(parent,'constraints',ns),T('constraint'),{
        'id':ident,'type':typ,'value':str(value),'field':field,'scope':scope,'shared':'true',
        'includeChildSelections':'true' if child else 'false','includeChildForces':'false'})
def add_rule(parent,ident,name,text):
    r=ET.SubElement(ensure(parent,'rules'),C('rule'),{'id':ident,'name':name,'hidden':'false'})
    ET.SubElement(r,C('description')).text=text
    return r
def fixed(parent,ident,name,text=None):
    e=ET.SubElement(ensure(parent,'selectionEntries'),C('selectionEntry'),{
        'id':ident,'name':name,'type':'upgrade','hidden':'false','import':'true','defaultAmount':'1'})
    constraint(e,ident+'-min','min',1); constraint(e,ident+'-max','max',1)
    ET.SubElement(ensure(e,'costs'),C('cost'),{'name':'Points','typeId':'pts','value':'0'})
    if text: add_rule(e,ident+'-rule',name,text)
    return e
def fixed_group(unit,slug,items):
    g=ET.SubElement(ensure(unit,'selectionEntryGroups'),C('selectionEntryGroup'),{
        'id':f'r67-if-{slug}-fixed','name':'Wargear & Special Rules (fixed)','hidden':'false','collective':'false','import':'true'})
    for n,(name,text) in enumerate(items,1): fixed(g,f'r67-if-{slug}-fixed-{n}',name,text)
    return g
def hide_if_selected(entry,ident,child,scope='roster'):
    m=ET.SubElement(ensure(entry,'modifiers'),C('modifier'),{'id':ident,'type':'set','value':'true','field':'hidden'})
    cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{
        'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def hide_if_missing(entry,ident,child,scope='roster'):
    m=ET.SubElement(ensure(entry,'modifiers'),C('modifier'),{'id':ident,'type':'set','value':'true','field':'hidden'})
    cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{
        'type':'lessThan','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_hidden_category_link(entry,ident,target,name):
    cats=ensure(entry,'categoryLinks')
    if not any(c.get('targetId')==target for c in cats.findall(C('categoryLink'))):
        ET.SubElement(cats,C('categoryLink'),{'id':ident,'name':name,'hidden':'true','targetId':target,'primary':'false'})
def entry_link(parent,ident,name,target):
    l=ET.SubElement(ensure(parent,'entryLinks'),C('entryLink'),{'id':ident,'name':name,'type':'selectionEntry','targetId':target,'hidden':'false','import':'true'})
    constraint(l,ident+'-max','max',1)
    return l

def canon_write(tree,path,ns):
    ET.indent(tree,space='  ')
    ET.register_namespace('',ns)
    tree.write(path,encoding='utf-8',xml_declaration=True)

# Safe reruns / remove old Rev67 structures.
remove_pred(cr,lambda e:(e.get('id') or '').startswith('r67-if-'))
remove_pred(gr,lambda e:(e.get('id') or '').startswith('r67-if-'))

# Remove the overly broad Rev64 Solarite links that were injected into every group containing the word Armoury.
# Keep the actual shared gear and the dedicated Imperial Fists HQ/unique-unit links.
remove_pred(cr,lambda e:(e.get('id') or '').startswith('r64-if-arm-'))

IDS={
 'templar':'r41-unit-vii-0-templar-brethren-squad',
 'warder':'r41-unit-vii-1-phalanx-warder-squad',
 'huscarl':'r41-unit-vii-2-huscarl-terminator-retinue',
 'tarantula':'r41-unit-vii-3-tarantula-sentry-gun-battery',
 'sig':'r41-unit-vii-4-sigismund-first-captain',
 'rann':'r41-unit-vii-5-fafnir-rann',
 'polux':'r41-unit-vii-6-alexis-polux',
 'diaz':'r41-unit-vii-7-camba-diaz',
 'garrius':'r41-unit-vii-8-evander-garrius',
 'dorn':'r41-unit-vii-9-vii-rogal-dorn-the-praetorian-of-terra'}
U={k:by_id(cr,v) for k,v in IDS.items()}
if any(v is None for v in U.values()): raise RuntimeError('Missing Imperial Fists entry')

# Re-add Solarite access only to genuine generic Character armoury groups.
for g in list(cr.iter(C('selectionEntryGroup'))):
    name=(g.get('name') or '')
    low=name.lower()
    if low.startswith('sergeant armoury (') or ('champion' in low and 'armoury' in low and 'additional' in low):
        entry_link(g,'r67-if-'+g.get('id')+'-solarite','Solarite Power Gauntlet','r64-if-gear-solarite')
        entry_link(g,'r67-if-'+g.get('id')+'-solarite-ex','Solarite Power Gauntlet — exchange Power Fist','r64-if-gear-solarite-exchange')

# Full fixed equipment/rules made visible as locked child entries. This is intentional: New Recruit shows these in the unit editor,
# whereas direct <rules> alone can appear only in the roster rules view.
fixed_group(U['templar'],'templar',[
 ('Power Armour',None),('Combat Shield','Grants a 6+ Invulnerable Save. The shield occupies one hand and prevents the bonus Attack for fighting with two close-combat weapons.'),
 ('Bolt pistol',None),('Rending Weapon',None),('Legiones Astartes (Imperial Fists)',None),('Stubborn',None),
 ('Righteous Zeal','Whenever the squad would normally take a Morale test for suffering 25% or more casualties from enemy shooting, it may instead move D6 inches directly towards the nearest visible enemy unit. This movement may not bring any model within 1 inch of an enemy model and does not count as charging or Falling Back. If no enemy unit is visible, take the Morale test normally.')])
fixed_group(U['warder'],'warder',[
 ('Power Armour',None),('Boarding Shield','Grants a 5+ Invulnerable Save, occupies one hand and prevents the bonus Attack for fighting with two weapons.'),
 ('Bolter',None),('Power Weapon',None),('Legiones Astartes (Imperial Fists)',None),('Stubborn',None),('Counter-Attack',None)])
fixed_group(U['huscarl'],'huscarl',[
 ('Cataphractii Terminator Armour',None),('Combi-bolter',None),('Power Weapon',None),('Legiones Astartes (Imperial Fists)',None),('Stubborn',None),
 ('Retinue','One Huscarl Terminator Retinue may be selected for Rogal Dorn, Sigismund or an Imperial Fists Praetor wearing Terminator Armour. The squad does not occupy a separate Force Organisation slot.')])
fixed_group(U['tarantula'],'tarantula',[
 ('Twin-linked Heavy Bolter',None),
 ('Firing Mode','After deployment but before the first turn begins, choose one firing mode for each Tarantula. Point Defence: fixed 90-degree firing arc and targets within 24 inches. Sentry: 360-degree firing arc and targets within 12 inches. The selected mode cannot be changed during the battle.'),
 ('Automated Targeting','A Tarantula fires automatically during the Imperial Fists Shooting phase if an eligible target is available. A Heavy Bolter Tarantula fires at the nearest visible non-Vehicle enemy unit. A Lascannon Tarantula fires at the nearest visible enemy Vehicle or Monstrous Creature. If no preferred target is available, it fires at the nearest other eligible enemy target.'),
 ('Disposable Platform','Any Glancing or Penetrating Hit destroys the Tarantula.')])

fixed_group(U['sig'],'sigismund',[
 ('Artificer Armour',None),('Iron Halo',None),('Terminator Honours',None),('Purity Seals',None),('Bolt pistol',None),
 ('The Black Sword','Two-Handed, Master-crafted Power Weapon; +2 Strength. Sigismund never requires worse than a 3+ To Hit in close combat. Any natural To Wound roll of 6 made with the Black Sword inflicts a Massive Wound (D3) instead of a normal Wound.'),
 ('Legiones Astartes (Imperial Fists)',None),('Independent Character',None),('Master of the Legion',None),('Honour or Death',None),
 ('Kingslayer','After deployment but before the first turn begins, nominate one enemy Independent Character. If Sigismund personally slays the nominated character, the Imperial Fists player receives an additional 150 Victory Points and Sigismund becomes Fearless for the remainder of the battle. If the nominated character survives the battle, the opposing player instead receives an additional 150 Victory Points. This rule only applies in missions using Victory Points.')])
fixed_group(U['rann'],'rann',[
 ('Artificer Armour',None),('Refractor Field',None),('The Headsman',None),('The Hunter',None),('Frag grenades',None),
 ('Legiones Astartes (Imperial Fists)',None),('Independent Character',None),('Master of the Legion',None),
 ('The Headsman and the Hunter','The Headsman and the Hunter are a matched pair of Power Weapons. The +1 Attack for fighting with two close-combat weapons is already included in Rann’s profile. When fighting a Vehicle, Rann may choose to use both weapons as a single heavy blow. If he does so, he makes one fewer Attack, but those attacks gain Armourbane.'),
 ('Executioner’s Tax','Whenever an enemy unit successfully charges Rann or a unit he has joined, that enemy unit suffers D3 automatic Strength 5 AP4 hits after completing its charge move but before close-combat attacks are resolved.'),
 ('Lord Seneschal','While Rann has joined a Legion Breacher Squad or Phalanx Warder Squad, that unit receives +1 Weapon Skill during an Assault phase in which it charged.')])
fixed_group(U['polux'],'polux',[
 ('Power Armour',None),('Vigil Pattern Storm Shield','Grants Polux a 3+ Invulnerable Save. It occupies one hand and prevents him from gaining the bonus Attack for fighting with two close-combat weapons.'),
 ('Terminator Honours',None),('Combi-meltagun',None),('Master-crafted Power Fist',None),('Frag grenades',None),
 ('Legiones Astartes (Imperial Fists)',None),('Independent Character',None),('Master of the Legion',None),('Stubborn',None),
 ('Teleport Transponder','Before deployment, Polux may be assigned to one Legion Terminator Squad, Legion Terminator Command Squad or Huscarl Terminator Retinue. Polux and the nominated unit gain Deep Strike and must enter play together if they use this rule.'),
 ('The Crimson Fist','At the beginning of an Assault phase in which Polux is engaged, he may make a single attack with his Master-crafted Power Fist instead of making his normal attacks. This attack is resolved at Initiative 4 and Strength 8 and ignores Armour Saves. Polux makes exactly one attack that Assault phase regardless of any other bonuses.')])
fixed_group(U['diaz'],'diaz',[
 ('Artificer Armour',None),('Refractor Field',None),('Power Weapon',None),('Bolt pistol',None),('Frag grenades',None),
 ('Legiones Astartes (Imperial Fists)',None),('Independent Character',None),('Stubborn',None),
 ('Hold the Line','If Diaz and the unit he has joined did not move during the Movement phase, they gain Counter-Attack until the beginning of the next Imperial Fists turn. In addition, they may re-roll failed Morale tests during this time.')])
fixed_group(U['garrius'],'garrius',[
 ('Cataphractii Terminator Armour',None),('Subjugator','Master-crafted Power Fist. Attacks made with Subjugator are resolved at Strength 10 instead of doubling Garrius’ Strength.'),
 ('Volkite Charger',None),('Bionics',None),('Legiones Astartes (Imperial Fists)',None),('Independent Character',None),('Master of the Legion',None),('Fearless',None),
 ('Tyrant of Cthonia','Garrius and any Imperial Fists unit he has joined may re-roll failed Pinning tests. If Garrius’ unit wins a close combat, it may re-roll the dice when determining its Consolidation distance. The second result must be accepted.')])
fixed_group(U['dorn'],'dorn',[
 ('Auric Armour','Counts as Primarch Armour.'),
 ('Storm’s Teeth','Two-Handed Power Weapon. Attacks are resolved at +2 Strength and have Shred and Rampage.'),
 ('Voice of Terra','Range 24 inches, Strength 5, AP4, Salvo 3/5, Rending.'),('Frag Grenades',None),('Primarch',None),('Legiones Astartes (Imperial Fists)',None),
 ('The Unyielding','Rogal Dorn may re-roll Armour Saves of 1. The second result must be accepted.'),
 ('Lord Castellan','Friendly Imperial Fists units with at least one model within 12 inches of Rogal Dorn gain Stubborn. A unit which already has Stubborn may instead re-roll failed Pinning tests while within 12 inches of Dorn.'),
 ('Master of Defence','Rogal Dorn and any unit he has joined count as being equipped with Frag Grenades when assaulted through Difficult Terrain. In addition, Dorn and any unit he has joined may make an Overwatch attack when charged even if another rule or circumstance would normally prevent that unit from doing so.'),
 ('This Ground Shall Not Fall','After terrain has been placed but before either army deploys, nominate up to two Fortifications, ruins or other suitable defensive terrain features wholly or partially within the Imperial Fists deployment zone. The Cover Save provided by each nominated terrain feature is improved by 1, to a maximum of 3+. Friendly Imperial Fists units occupying either nominated terrain feature may not be Pinned. These benefits last for the duration of the battle.')])

# Huscarl is a retinue only. Its playable copies already exist inside the permitted character/Praetor retinue groups.
U['huscarl'].set('hidden','true')

# Templar Assault replaces the normal Templar transport choice with its Rite-specific Assault Transport choice.
TEMPLAR='r25-rite-vii-2-templar-assault'; HAMMER='r25-rite-vii-1-hammerfall-strike-force'; DORN=IDS['dorn']
for gid in ('r64-if-templar-transport','r64-if-templar-troops-r64-if-templar-transport'):
    g=by_id(cr,gid)
    if g is not None: hide_if_selected(g,'r67-if-'+gid+'-hide-templar-assault',TEMPLAR)

# Primarch/Warlord interaction. The source states a Primarch must be the Warlord and may not buy upgrades unless its entry permits them.
# Dorn has no option to buy Teleportation Transponders, so Hammerfall and Dorn cannot form a legal roster.
hammer=by_id(cr,HAMMER)
if hammer is None: raise RuntimeError('Missing Hammerfall Rite')
hide_if_selected(hammer,'r67-if-hammer-hide-dorn',DORN)
hide_if_missing(U['dorn'],'r67-if-dorn-base-legion','legion-vii')
hide_if_selected(U['dorn'],'r67-if-dorn-hide-hammer',HAMMER)

# Dorn's fixed Storm's Teeth is a sword-like Power Weapon, so he automatically satisfies the Templar Assault Warlord requirement.
TEMPCAT='r66-if-cat-templar-warlord'; TEMPNAME='Templar Assault — Warlord with qualifying melee weapon'
if by_id(gr,TEMPCAT) is None: raise RuntimeError('Missing Rev66 Templar Warlord category')
add_hidden_category_link(U['dorn'],'r67-if-dorn-templar-warlord-cat',TEMPCAT,TEMPNAME)
# If Dorn is present, Supreme Commander makes him the Warlord; hide the optional designation markers on other characters.
for e in list(cr.iter(C('selectionEntry'))):
    if (e.get('id') or '').startswith('r66-if-') and (e.get('id') or '').endswith('-templar-warlord'):
        hide_if_selected(e,'r67-if-'+e.get('id')+'-hide-dorn',DORN)

# Make the Imperial Fists shared armoury entries themselves visibly descriptive in New Recruit when selected.
for ident,summary in [
 ('r64-if-gear-solarite','Strength 10. Power Weapon, Unwieldy, Specialist Weapon. Always strikes at Strength 10 regardless of the bearer’s Strength.'),
 ('r64-if-gear-solarite-exchange','Replace an already-equipped Power Fist with a Solarite Power Gauntlet for +5 points.'),
 ('r64-if-gear-vigil','3+ Invulnerable Save. The bearer may carry no more than one other weapon; the shield occupies one hand and prevents the bonus Attack for fighting with two close-combat weapons.'),
 ('r64-if-gear-trans-ic','Grants Deep Strike even if the mission would not normally permit it. An Independent Character joining another Deep Striking unit must purchase Transponders separately.'),
 ('r64-if-gear-trans-unit','Grants Deep Strike even if the mission would not normally permit it.')]:
    e=by_id(cr,ident)
    if e is not None and not any(r.get('id')==f'r67-if-{ident}-visible' for r in e.findall('./'+C('rules')+'/'+C('rule'))):
        add_rule(e,f'r67-if-{ident}-visible','Rules',summary)

# Revision bump and canonical namespace serialization.
cr.set('revision','67'); cr.set('gameSystemRevision','35'); gr.set('revision','35')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat': e.set('dataRevision','67')
    elif e.get('filePath')=='Prohammer 30k.gst': e.set('dataRevision','35')

# Validation.
def dupes(root):
    seen=set(); out=[]
    for e in root.iter():
        i=e.get('id')
        if not i: continue
        if i in seen: out.append(i)
        seen.add(i)
    return out
for root,label in ((cr,'catalogue'),(gr,'game system')):
    d=dupes(root)
    if d: raise RuntimeError(f'Duplicate IDs in {label}: {d[:20]}')
for key in ('templar','warder','huscarl','tarantula','sig','rann','polux','diaz','garrius','dorn'):
    if by_id(cr,f'r67-if-{key if key != "sig" else "sigismund"}-fixed') is None:
        raise RuntimeError('Missing visible fixed group for '+key)
if U['huscarl'].get('hidden')!='true': raise RuntimeError('Huscarl top-level retinue not hidden')
if by_id(cr,'r67-if-dorn-templar-warlord-cat') is None: raise RuntimeError('Missing Dorn Templar Warlord validation')

canon_write(ct,CAT,CNS); canon_write(gt,GST,GNS); canon_write(it,IDX,INS)
ET.parse(CAT); ET.parse(GST); ET.parse(IDX)

OUT.write_text('''Revision 67 — Imperial Fists final visible pass\nCatalogue revision: 67\nGame-system revision: 35\n\nPurpose:\n- The Rev64/66 data contained the character rules as direct BattleScribe <rules>, but New Recruit can present those only in the rules/roster view. Revision 67 adds locked visible child entries for all fixed wargear and special rules on every Imperial Fists unique unit and character, so the complete entry is visible when editing the unit.\n\nFinalised:\n- Templar Brethren, Phalanx Warders, Huscarls and Tarantulas now visibly show their fixed equipment and rules.\n- Sigismund, Rann, Polux, Diaz, Garrius and Dorn now visibly show complete fixed wargear and named rules rather than appearing as statblocks only.\n- Existing options, retinues, Rite role changes, exact unit sizes, Dedicated Transports and Rev66 conditional restrictions are retained.\n- Huscarl Terminator Retinue is hidden as a standalone pick and remains available through the legal Dorn/Sigismund/Terminator-Praetor retinue paths.\n- Templar Assault hides the normal Templar Dedicated Transport group and uses the Rite-specific Assault Transport group.\n- Dorn automatically satisfies the Templar Assault Warlord weapon requirement through Storm’s Teeth; other Warlord designation controls hide while Dorn is present.\n- Hammerfall and Dorn are mutually unavailable because a Primarch must be the Warlord, Primarchs cannot buy unlisted upgrades, and Dorn has no Teleportation Transponder option.\n- Broad Rev64 Solarite links were cleaned out of unrelated Armoury groups and restored only to genuine Character armoury groups.\n- Catalogue, game-system and data-index XML are serialized with their own canonical default namespaces.\n''',encoding='utf-8')
print(OUT.read_text())
