from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r66-imperial-fists-conditional.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS); ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()

if cr.get('revision')!='65' or gr.get('revision')!='33':
    raise RuntimeError(f'Expected Rev65/33 baseline, got CAT {cr.get("revision")} GST {gr.get("revision")}')

def by_id(root,ident): return next((e for e in root.iter() if e.get('id')==ident),None)
def ensure(parent,tag,ns=CNS):
    q=f'{{{ns}}}{tag}'; x=parent.find(q)
    if x is None: x=ET.SubElement(parent,q)
    return x
def remove_pred(root,pred):
    for p in list(root.iter()):
        for x in list(p):
            if pred(x): p.remove(x)
def add_constraint(parent,ident,typ,value,ns=CNS,child=False):
    T=C if ns==CNS else G
    return ET.SubElement(ensure(parent,'constraints',ns),T('constraint'),{
        'id':ident,'type':typ,'value':str(value),'field':'selections','scope':'parent','shared':'true',
        'includeChildSelections':'true' if child else 'false','includeChildForces':'false'})
def add_hidden_category_link(entry,link_id,target,name):
    cats=ensure(entry,'categoryLinks')
    if not any(c.get('targetId')==target for c in cats.findall(C('categoryLink'))):
        ET.SubElement(cats,C('categoryLink'),{'id':link_id,'name':name,'hidden':'true','targetId':target,'primary':'false'})
def make_force_requirement(cat_id,name,selector,minv=1,maxv=None):
    cats=ensure(gr,'categoryEntries',GNS)
    if by_id(gr,cat_id) is None:
        ET.SubElement(cats,G('categoryEntry'),{'id':cat_id,'name':name,'hidden':'true'})
    force=by_id(gr,'force-standard')
    if force is None: raise RuntimeError('Missing standard force')
    flinks=ensure(force,'categoryLinks',GNS)
    fid='r66-if-fl-'+cat_id
    link=ET.SubElement(flinks,G('categoryLink'),{'id':fid,'name':name,'hidden':'true','targetId':cat_id})
    if minv is not None:
        cid=fid+'-min'
        add_constraint(link,cid,'min',0,ns=GNS,child=True)
        m=ET.SubElement(ensure(link,'modifiers',GNS),G('modifier'),{'id':cid+'-mod','type':'set','value':str(minv),'field':cid})
        cs=ET.SubElement(m,G('conditions')); ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    if maxv is not None:
        cid=fid+'-max'
        add_constraint(link,cid,'max',99,ns=GNS,child=True)
        m=ET.SubElement(ensure(link,'modifiers',GNS),G('modifier'),{'id':cid+'-mod','type':'set','value':str(maxv),'field':cid})
        cs=ET.SubElement(m,G('conditions')); ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def conditional_link(parent,ident,name,target,selector=None):
    l=ET.SubElement(ensure(parent,'entryLinks'),C('entryLink'),{'id':ident,'name':name,'type':'selectionEntry','targetId':target,'hidden':'true' if selector else 'false','import':'true'})
    add_constraint(l,ident+'-max','max',1)
    if selector:
        m=ET.SubElement(ensure(l,'modifiers'),C('modifier'),{'id':ident+'-show','type':'set','value':'false','field':'hidden'})
        cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return l
def local_marker(parent,ident,name,cat_id,cat_name):
    e=ET.SubElement(ensure(parent,'selectionEntries'),C('selectionEntry'),{'id':ident,'name':name,'type':'upgrade','hidden':'true','import':'true'})
    add_constraint(e,ident+'-max','max',1)
    ET.SubElement(ensure(e,'costs'),C('cost'),{'name':'Points','typeId':'pts','value':'0'})
    add_hidden_category_link(e,ident+'-cat',cat_id,cat_name)
    return e
def reveal_on_rite(entry,ident,rite):
    m=ET.SubElement(ensure(entry,'modifiers'),C('modifier'),{'id':ident,'type':'set','value':'false','field':'hidden'})
    cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':rite,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def reveal_on_rite_and_target(entry,ident,rite,target,include_children=False):
    m=ET.SubElement(ensure(entry,'modifiers'),C('modifier'),{'id':ident,'type':'set','value':'false','field':'hidden'})
    gs=ET.SubElement(m,C('conditionGroups')); g=ET.SubElement(gs,C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(g,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':rite,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'root-entry','childId':target,'shared':'true','includeChildSelections':'true' if include_children else 'false','includeChildForces':'false'})

# Restart the conditional layer cleanly: remove Rev65 condition structures, preserve Rev64 full army.
remove_pred(cr,lambda e:(e.get('id') or '').startswith('r65-if-') or (e.get('id') or '').startswith('r66-if-'))
remove_pred(gr,lambda e:(e.get('id') or '').startswith('r65-if-') or (e.get('id') or '').startswith('r66-if-'))

STONE='r25-rite-vii-0-the-stone-gauntlet'; HAMMER='r25-rite-vii-1-hammerfall-strike-force'; TEMPLAR='r25-rite-vii-2-templar-assault'
PRA='hq-praetor'; CEN='hq-centurion'; SIG='r41-unit-vii-4-sigismund-first-captain'; RANN='r41-unit-vii-5-fafnir-rann'; POLUX='r41-unit-vii-6-alexis-polux'; DIAZ='r41-unit-vii-7-camba-diaz'; GARRIUS='r41-unit-vii-8-evander-garrius'
required=[STONE,HAMMER,TEMPLAR,PRA,CEN,SIG,RANN,POLUX,DIAZ,GARRIUS,'r64-if-gear-vigil','r64-if-gear-trans-ic','gear-hq-boarding','gear-power-weapon','gear-hq-relic','gear-rending']
for ident in required:
    if by_id(cr,ident) is None: raise RuntimeError('Missing required catalogue entry '+ident)

# STONE GAUNTLET: automatically validate at least one shield-bearing Independent Character.
STONECAT='r66-if-cat-stone-shield-ic'; STONENAME='Stone Gauntlet — Shield-bearing Independent Character'
make_force_requirement(STONECAT,STONENAME,STONE,minv=1)
add_hidden_category_link(by_id(cr,'gear-hq-boarding'),'r66-if-board-cat',STONECAT,STONENAME)
add_hidden_category_link(by_id(cr,'r64-if-gear-vigil'),'r66-if-vigil-cat',STONECAT,STONENAME)
# Polux has a fixed Vigil Pattern Storm Shield and is an Independent Character.
add_hidden_category_link(by_id(cr,POLUX),'r66-if-polux-stone-cat',STONECAT,STONENAME)

# HAMMERFALL: complete the +10 Independent Character transponder access from the Rite.
# Garrius is in Cataphractii armour, so he can buy the normal character transponders without the Rite.
conditional_link(by_id(cr,GARRIUS),'r66-if-garrius-trans','Teleportation Transponders','r64-if-gear-trans-ic')
# The Rite extends transponder access to every other named Imperial Fists Independent Character.
for uid,slug in ((SIG,'sigismund'),(RANN,'rann'),(POLUX,'polux'),(DIAZ,'diaz')):
    conditional_link(by_id(cr,uid),f'r66-if-{slug}-hammer-trans','Teleportation Transponders','r64-if-gear-trans-ic',HAMMER)

# HAMMERFALL Warlord: exactly one model must be explicitly designated, and the designation only appears after that IC has bought Transponders.
HAMCAT='r66-if-cat-hammer-warlord'; HAMNAME='Hammerfall — Warlord with Teleportation Transponders'
make_force_requirement(HAMCAT,HAMNAME,HAMMER,minv=1,maxv=1)
for uid,slug in ((PRA,'praetor'),(CEN,'centurion'),(SIG,'sigismund'),(RANN,'rann'),(POLUX,'polux'),(DIAZ,'diaz'),(GARRIUS,'garrius')):
    u=by_id(cr,uid); mark=local_marker(u,f'r66-if-{slug}-hammer-warlord','Designate as Hammerfall Warlord',HAMCAT,HAMNAME)
    reveal_on_rite_and_target(mark,f'r66-if-{slug}-hammer-warlord-show',HAMMER,'r64-if-gear-trans-ic',False)

# TEMPLAR ASSAULT Warlord: exactly one eligible HQ/IC is designated.
TEMPCAT='r66-if-cat-templar-warlord'; TEMPNAME='Templar Assault — Warlord with qualifying melee weapon'
make_force_requirement(TEMPCAT,TEMPNAME,TEMPLAR,minv=1,maxv=1)
# Generic Praetor/Centurion designation appears only if that character itself has selected Power Weapon, Relic Blade or Rending Weapon.
for uid,slug in ((PRA,'praetor'),(CEN,'centurion')):
    u=by_id(cr,uid); mark=local_marker(u,f'r66-if-{slug}-templar-warlord','Designate as Templar Assault Warlord',TEMPCAT,TEMPNAME)
    for n,target in enumerate(('gear-power-weapon','gear-hq-relic','gear-rending'),1):
        reveal_on_rite_and_target(mark,f'r66-if-{slug}-templar-show-{n}',TEMPLAR,target,False)
# These named Independent Characters have qualifying fixed weapons in the source: Black Sword / matched Power Weapons / Power weapon.
for uid,slug in ((SIG,'sigismund'),(RANN,'rann'),(DIAZ,'diaz')):
    u=by_id(cr,uid); mark=local_marker(u,f'r66-if-{slug}-templar-warlord','Designate as Templar Assault Warlord',TEMPCAT,TEMPNAME)
    reveal_on_rite(mark,f'r66-if-{slug}-templar-show',TEMPLAR)

# Deployment-only limitations remain exact rules text: Reserve and voluntary Deep Strike cannot be truthfully validated from roster composition.
# The standard detachment currently has no Fortification battlefield role/selectable Fortification entries, so the Rite Fortification bans are structurally impossible to violate.

# Revisions.
cr.set('revision','66'); gr.set('revision','34'); cr.set('gameSystemRevision','34')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat': e.set('dataRevision','66')
    elif e.get('filePath')=='Prohammer 30k.gst': e.set('dataRevision','34')

# Validation.
def duplicate_ids(root):
    seen=set(); dup=[]
    for e in root.iter():
        i=e.get('id')
        if not i: continue
        if i in seen: dup.append(i)
        seen.add(i)
    return dup
for root,label in ((cr,'catalogue'),(gr,'game system')):
    d=duplicate_ids(root)
    if d: raise RuntimeError(f'Duplicate IDs in {label}: {d[:20]}')
for ident in ('r66-if-fl-'+STONECAT,'r66-if-fl-'+HAMCAT,'r66-if-fl-'+TEMPCAT,
              'r66-if-praetor-hammer-warlord','r66-if-centurion-hammer-warlord','r66-if-polux-hammer-trans',
              'r66-if-praetor-templar-warlord','r66-if-centurion-templar-warlord','r66-if-sigismund-templar-warlord'):
    if by_id(cr,ident) is None and by_id(gr,ident) is None: raise RuntimeError('Missing Rev66 structure '+ident)

ET.indent(ct,space='  '); ET.indent(gt,space='  '); ET.indent(it,space='  ')
ct.write(CAT,encoding='utf-8',xml_declaration=True); gt.write(GST,encoding='utf-8',xml_declaration=True); it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT); ET.parse(GST); ET.parse(IDX)
OUT.write_text('''Revision 66 — Imperial Fists conditional restriction restart\nCatalogue revision: 66\nGame-system revision: 34\n\nConditional enforcement:\n- Stone Gauntlet automatically requires at least one Independent Character with Boarding Shield or Vigil Pattern Storm Shield; Alexis Polux satisfies this through his fixed Vigil shield.\n- Hammerfall gives the source-legal +10 Teleportation Transponders access to all named Imperial Fists Independent Characters (Garrius normally because of Cataphractii armour; Sigismund, Rann, Polux and Diaz while Hammerfall is selected).\n- Hammerfall requires exactly one designated Warlord. The designation only becomes selectable after that character has selected Teleportation Transponders.\n- Templar Assault requires exactly one designated Warlord. Generic Praetor/Centurion designation only becomes selectable when that character has selected Power Weapon, Relic Blade or Rending Weapon. Sigismund, Fafnir Rann and Camba Diaz are valid through their fixed source wargear.\n\nAlready enforced by Revision 64 and retained:\n- Stone Gauntlet compulsory Breacher/Warder requirement.\n- Templar Assault compulsory Templar Brethren requirement.\n- Stone Gauntlet and Templar Assault Fast Attack maximum 1.\n- Rite-specific Troops role changes and Templar Assault transport access.\n\nSource limitations left as battle/deployment rules rather than false roster restrictions:\n- Stone Gauntlet: no voluntary Deep Strike.\n- Hammerfall: every Vehicle begins in Reserve.\n- Hammerfall/Templar Assault: no Fortifications (the current standard detachment has no selectable Fortification role anyway).\n''',encoding='utf-8')
print(OUT.read_text())
