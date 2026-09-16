from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r65-imperial-fists-conditional.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS); ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()

if cr.get('revision')!='64' or gr.get('revision')!='32':
    raise RuntimeError(f'Expected Rev64/32 baseline, got CAT {cr.get("revision")} GST {gr.get("revision")}')

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
    return ET.SubElement(ensure(parent,'constraints',ns),T('constraint'),{'id':ident,'type':typ,'value':str(value),'field':'selections','scope':'parent','shared':'true','includeChildSelections':'true' if child else 'false','includeChildForces':'false'})
def add_hidden_category_link(entry,link_id,target,name):
    cats=ensure(entry,'categoryLinks')
    if not any(c.get('targetId')==target for c in cats.findall(C('categoryLink'))):
        ET.SubElement(cats,C('categoryLink'),{'id':link_id,'name':name,'hidden':'true','targetId':target,'primary':'false'})
def make_force_requirement(cat_id,name,selector,minv=1):
    cats=ensure(gr,'categoryEntries',GNS)
    if by_id(gr,cat_id) is None:
        ET.SubElement(cats,G('categoryEntry'),{'id':cat_id,'name':name,'hidden':'true'})
    force=by_id(gr,'force-standard')
    if force is None: raise RuntimeError('Missing standard force')
    flinks=ensure(force,'categoryLinks',GNS)
    fid='r65-if-fl-'+cat_id
    link=by_id(gr,fid)
    if link is None:
        link=ET.SubElement(flinks,G('categoryLink'),{'id':fid,'name':name,'hidden':'true','targetId':cat_id})
    cid=fid+'-min'
    add_constraint(link,cid,'min',0,ns=GNS,child=False)
    mods=ensure(link,'modifiers',GNS)
    m=ET.SubElement(mods,G('modifier'),{'id':cid+'-mod','type':'set','value':str(minv),'field':cid})
    cs=ET.SubElement(m,G('conditions'))
    ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def conditional_link(parent,ident,name,target,selector=None):
    l=ET.SubElement(ensure(parent,'entryLinks'),C('entryLink'),{'id':ident,'name':name,'type':'selectionEntry','targetId':target,'hidden':'true' if selector else 'false','import':'true'})
    add_constraint(l,ident+'-max','max',1)
    if selector:
        mods=ensure(l,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':ident+'-show','type':'set','value':'false','field':'hidden'})
        cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return l
def acknowledgement(rite,ident,title,text):
    g=ET.SubElement(ensure(rite,'selectionEntryGroups'),C('selectionEntryGroup'),{'id':ident+'-group','name':title,'hidden':'false','collective':'false','import':'true'})
    add_constraint(g,ident+'-group-min','min',1,child=True); add_constraint(g,ident+'-group-max','max',1,child=True)
    e=ET.SubElement(ensure(g,'selectionEntries'),C('selectionEntry'),{'id':ident,'name':text,'type':'upgrade','hidden':'false','import':'true'})
    add_constraint(e,ident+'-max','max',1)
    costs=ensure(e,'costs'); ET.SubElement(costs,C('cost'),{'name':'Points','typeId':'pts','value':'0'})
    return e

# Safe reruns.
remove_pred(cr,lambda e:(e.get('id') or '').startswith('r65-if-'))
remove_pred(gr,lambda e:(e.get('id') or '').startswith('r65-if-'))

STONE='r25-rite-vii-0-the-stone-gauntlet'; HAMMER='r25-rite-vii-1-hammerfall-strike-force'; TEMPLAR='r25-rite-vii-2-templar-assault'
POLUX='r41-unit-vii-6-alexis-polux'; SIG='r41-unit-vii-4-sigismund-first-captain'; RANN='r41-unit-vii-5-fafnir-rann'; DIAZ='r41-unit-vii-7-camba-diaz'; GARRIUS='r41-unit-vii-8-evander-garrius'
for ident in (STONE,HAMMER,TEMPLAR,POLUX,SIG,RANN,DIAZ,GARRIUS,'r64-if-gear-vigil','r64-if-gear-trans-ic','gear-hq-boarding'):
    if by_id(cr,ident) is None: raise RuntimeError('Missing required catalogue entry '+ident)

# THE STONE GAUNTLET — at least one Independent Character with Boarding Shield or Vigil Pattern Storm Shield.
STONECAT='r65-if-cat-stone-shield-ic'
make_force_requirement(STONECAT,'Stone Gauntlet — Shield-bearing Independent Character',STONE,1)
add_hidden_category_link(by_id(cr,'gear-hq-boarding'),'r65-if-board-cat',STONECAT,'Stone Gauntlet — Shield-bearing Independent Character')
add_hidden_category_link(by_id(cr,'r64-if-gear-vigil'),'r65-if-vigil-cat',STONECAT,'Stone Gauntlet — Shield-bearing Independent Character')
# Alexis Polux has a fixed Vigil Pattern Storm Shield and is an Independent Character.
add_hidden_category_link(by_id(cr,POLUX),'r65-if-polux-stone-cat',STONECAT,'Stone Gauntlet — Shield-bearing Independent Character')

# HAMMERFALL — make the character-side transponder access complete.
# Garrius is an Independent Character in Cataphractii armour, so he may buy the normal +10 transponder even without Hammerfall.
conditional_link(by_id(cr,GARRIUS),'r65-if-garrius-trans','Teleportation Transponders','r64-if-gear-trans-ic')
# Hammerfall explicitly extends +10 transponders to any Imperial Fists Independent Character.
for uid,slug in ((SIG,'sigismund'),(RANN,'rann'),(DIAZ,'diaz')):
    conditional_link(by_id(cr,uid),f'r65-if-{slug}-hammer-trans','Teleportation Transponders','r64-if-gear-trans-ic',HAMMER)

# Enforce the necessary roster condition: Hammerfall cannot be valid without at least one transponder-equipped IC.
HAMCAT='r65-if-cat-hammer-trans-ic'
make_force_requirement(HAMCAT,'Hammerfall — Transponder-equipped Warlord candidate',HAMMER,1)
add_hidden_category_link(by_id(cr,'r64-if-gear-trans-ic'),'r65-if-trans-ic-cat',HAMCAT,'Hammerfall — Transponder-equipped Warlord candidate')
# Polux has a fixed Teleport Transponder.
add_hidden_category_link(by_id(cr,POLUX),'r65-if-polux-hammer-cat',HAMCAT,'Hammerfall — Transponder-equipped Warlord candidate')

# New Recruit does not have a universal Warlord designation field in this catalogue. Require an explicit acknowledgement inside the Rite
# after the automatic transponder-equipped-IC check above, so the list cannot be marked valid accidentally with the wrong Warlord.
acknowledgement(by_id(cr,HAMMER),'r65-if-hammer-warlord-confirm','Hammerfall Warlord Requirement','Confirm: the chosen Warlord is the Imperial Fists Independent Character equipped with Teleportation Transponders.')
acknowledgement(by_id(cr,TEMPLAR),'r65-if-templar-warlord-confirm','Templar Assault Warlord Requirement','Confirm: the chosen Warlord is equipped with a Power Weapon, Rending Weapon, Relic Blade, or another sword-like close-combat weapon that ignores Armour Saves.')

# The current standard detachment contains no Fortification battlefield role or selectable Fortification entries, so the Hammerfall/Templar
# Fortification prohibition is already structurally impossible to violate. Vehicle Reserve and voluntary Deep Strike are deployment choices,
# not roster selections, and remain exact rule text rather than inventing false list restrictions.

# Revision bump.
cr.set('revision','65'); gr.set('revision','33'); cr.set('gameSystemRevision','33')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat': e.set('dataRevision','65')
    elif e.get('filePath')=='Prohammer 30k.gst': e.set('dataRevision','33')

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
for ident in ('r65-if-fl-'+STONECAT,'r65-if-fl-'+HAMCAT,'r65-if-hammer-warlord-confirm','r65-if-templar-warlord-confirm','r65-if-garrius-trans','r65-if-sigismund-hammer-trans','r65-if-rann-hammer-trans','r65-if-diaz-hammer-trans'):
    if by_id(cr,ident) is None and by_id(gr,ident) is None: raise RuntimeError('Missing Rev65 structure '+ident)

ET.indent(ct,space='  '); ET.indent(gt,space='  '); ET.indent(it,space='  ')
ct.write(CAT,encoding='utf-8',xml_declaration=True); gt.write(GST,encoding='utf-8',xml_declaration=True); it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT); ET.parse(GST); ET.parse(IDX)
OUT.write_text('''Revision 65 — Imperial Fists conditional restriction pass\nCatalogue revision: 65\nGame-system revision: 33\n\nAdded conditional enforcement:\n- Stone Gauntlet now requires at least one shield-bearing Independent Character in the roster. The validation counts a generic HQ taking Boarding Shield, a generic HQ taking Vigil Pattern Storm Shield, or Alexis Polux with his fixed Vigil shield.\n- Hammerfall now requires at least one Independent Character with Teleportation Transponders. Polux satisfies this with his fixed transponder.\n- Hammerfall transponder access is now extended to Sigismund, Fafnir Rann and Camba Diaz while the Rite is selected, and Evander Garrius may buy it normally because he wears Cataphractii armour.\n- Hammerfall includes a required Warlord confirmation after the automatic transponder-equipped-IC validation, because the catalogue has no universal Warlord designation field.\n- Templar Assault includes a required Warlord weapon confirmation for its exact source restriction.\n\nAlready enforced from Revision 64:\n- Stone Gauntlet compulsory Breacher/Warder requirement.\n- Templar Assault compulsory Templar Brethren requirement.\n- Stone Gauntlet and Templar Assault Fast Attack maximum 1.\n\nNot converted into false roster restrictions:\n- Vehicle Reserve and voluntary Deep Strike are deployment choices, so they remain exact rule text.\n- The current standard detachment has no selectable Fortification role/entries, so the Fortification bans cannot currently be violated in New Recruit.\n''',encoding='utf-8')
print('Revision 65 applied: Imperial Fists conditional restrictions strengthened.')
