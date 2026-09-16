from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r70-imperial-fists-live.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS); ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()
if cr.get('revision')!='69' or gr.get('revision')!='37': raise RuntimeError(f'Expected CAT69/GST37 baseline, got {cr.get("revision")}/{gr.get("revision")}')

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t,ns=CNS):
    q=f'{{{ns}}}{t}'; x=p.find(q)
    if x is None: x=ET.SubElement(p,q)
    return x
def parent_map(root): return {c:p for p in root.iter() for c in p}
def remove_node(root,node):
    pm=parent_map(root); p=pm.get(node)
    if p is not None: p.remove(node)
def constraint(p,i,typ,val,field='selections',scope='parent',child=False,ns=CNS):
    T=C if ns==CNS else G
    return ET.SubElement(ensure(p,'constraints',ns),T('constraint'),{'id':i,'type':typ,'value':str(val),'field':field,'scope':scope,'shared':'true','includeChildSelections':'true' if child else 'false','includeChildForces':'false'})
def link(p,i,name,target,maxv=1):
    x=ET.SubElement(ensure(p,'entryLinks'),C('entryLink'),{'id':i,'name':name,'type':'selectionEntry','targetId':target,'hidden':'false','import':'true'})
    if maxv is not None: constraint(x,i+'-max','max',maxv)
    return x
def local(p,i,name,cost,rule=None):
    x=ET.SubElement(ensure(p,'selectionEntries'),C('selectionEntry'),{'id':i,'name':name,'type':'upgrade','hidden':'false','import':'true'})
    constraint(x,i+'-max','max',1); ET.SubElement(ensure(x,'costs'),C('cost'),{'name':'Points','typeId':'pts','value':str(cost)})
    if rule:
        r=ET.SubElement(ensure(x,'rules'),C('rule'),{'id':i+'-rule','name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=rule
    return x
def group(p,i,name,maxsel=None,maxpts=None):
    g=ET.SubElement(ensure(p,'selectionEntryGroups'),C('selectionEntryGroup'),{'id':i,'name':name,'hidden':'false','collective':'false','import':'true'})
    if maxsel is not None: constraint(g,i+'-max','max',maxsel,child=True)
    if maxpts is not None: constraint(g,i+'-pts','max',maxpts,field='pts',child=True)
    return g
def add_show_if(x,i,child,scope='roster',value='1'):
    x.set('hidden','true'); m=ET.SubElement(ensure(x,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'}); cs=ET.SubElement(m,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':value,'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_hide_if(x,i,child,scope='roster'):
    m=ET.SubElement(ensure(x,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'true','field':'hidden'}); cs=ET.SubElement(m,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def max_constraint(e):
    cs=e.find(C('constraints')); return next((x for x in cs.findall(C('constraint')) if x.get('type')=='max' and x.get('field')=='selections'),None) if cs is not None else None
def threshold_scale(g,model_id,base,thresholds,prefix):
    mc=max_constraint(g)
    if mc is None: mc=constraint(g,prefix+'-max','max',base,child=True)
    else: mc.set('value',str(base))
    mods=ensure(g,'modifiers')
    for old in list(mods):
        if (old.get('id') or '').startswith(prefix): mods.remove(old)
    for n,t in enumerate(thresholds,1):
        m=ET.SubElement(mods,C('modifier'),{'id':f'{prefix}-inc-{n}','type':'increment','value':'1','field':mc.get('id')}); cs=ET.SubElement(m,C('conditions'))
        ET.SubElement(cs,C('condition'),{'type':'atLeast','value':str(t),'field':'selections','scope':'parent','childId':model_id,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def rewrite_ids(node,prefix):
    mp={e.get('id'):prefix+e.get('id') for e in node.iter() if e.get('id')}
    for e in node.iter():
        if e.get('id') in mp: e.set('id',mp[e.get('id')])
        for a in ('childId','field'):
            if e.get(a) in mp: e.set(a,mp[e.get(a)])
    return node
def clone(i,prefix):
    s=byid(cr,i)
    if s is None: raise RuntimeError('Missing clone source '+i)
    return rewrite_ids(deepcopy(s),prefix)
def strip_categories(e):
    x=e.find(C('categoryLinks'))
    if x is not None: e.remove(x)

def direct_groups(u):
    x=u.find(C('selectionEntryGroups')); return [] if x is None else list(x.findall(C('selectionEntryGroup')))
def direct_entries(u):
    x=u.find(C('selectionEntries')); return [] if x is None else list(x.findall(C('selectionEntry')))
def find_model(u):
    return next((e for e in direct_entries(u) if e.get('type')=='model' and any(k in (e.get('name') or '').lower() for k in ('squad models','retinue models','sentry guns','guns'))),None)
def has_target(u,target): return any(x.get('targetId')==target for x in u.iter(C('entryLink')))

TEMPLAR='r25-rite-vii-2-templar-assault'; HAMMER='r25-rite-vii-1-hammerfall-strike-force'
TRANS_UNIT='r64-if-gear-trans-unit'; SOLAR='r64-if-gear-solarite'; SOLAR_EX='r64-if-gear-solarite-exchange'
for i in (TEMPLAR,HAMMER,TRANS_UNIT,SOLAR,SOLAR_EX,'legion-vii','hs-lr-phobos','hs-lr-proteus'):
    if byid(cr,i) is None: raise RuntimeError('Missing required catalogue id '+i)

# Clean this pass only, preserving all earlier Imperial Fists work.
for root,T in ((cr,C),(gr,G)):
    for p in list(root.iter()):
        for x in list(p):
            if (x.get('id') or '').startswith('r70-if-'): p.remove(x)

# 1) TEMPLAR ASSAULT: suspend the normal Templar Brethren 0-1 cap while the Rite is selected.
limlink=next((x for x in gr.iter(G('categoryLink')) if x.get('targetId')=='r64-if-cat-templar-limit'),None)
if limlink is None: raise RuntimeError('Templar 0-1 force link missing')
maxc=next((x for x in limlink.findall('./'+G('constraints')+'/'+G('constraint')) if x.get('type')=='max'),None)
if maxc is None: raise RuntimeError('Templar 0-1 max constraint missing')
mod=next((x for x in limlink.findall('./'+G('modifiers')+'/'+G('modifier')) if x.get('field')==maxc.get('id')),None)
if mod is None: raise RuntimeError('Templar 0-1 modifier missing')
for tag in (G('conditions'),G('conditionGroups')):
    old=mod.find(tag)
    if old is not None: mod.remove(old)
gs=ET.SubElement(mod,G('conditionGroups')); cg=ET.SubElement(gs,G('conditionGroup'),{'type':'and'}); cs=ET.SubElement(cg,G('conditions'))
ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':'legion-vii','shared':'true','includeChildSelections':'true','includeChildForces':'false'})
ET.SubElement(cs,G('condition'),{'type':'lessThan','value':'1','field':'selections','scope':'roster','childId':TEMPLAR,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
rite=byid(cr,TEMPLAR)
for r in rite.iter(C('rule')):
    d=r.find(C('description'))
    if d is not None and 'Compulsory Troops must be Templar Brethren' in (d.text or '') and 'ignore their normal 0–1' not in (d.text or ''):
        d.text=(d.text or '').replace('Compulsory Troops must be Templar Brethren.','Compulsory Troops must be Templar Brethren. While Templar Assault is selected, Templar Brethren Squads ignore their normal 0–1 restriction.')

# 2) HUSCARL and TARANTULA quantity scaling.
huscarls=[]
for u in cr.iter(C('selectionEntry')):
    if (u.get('name') or '').startswith('Huscarl Terminator Retinue'):
        m=find_model(u)
        if m is None: continue
        for g in u.iter(C('selectionEntryGroup')):
            n=g.get('name') or ''
            if n.startswith('Combi-bolter Replacements') or n.startswith('Power Weapon Replacements — any Huscarl'):
                threshold_scale(g,m.get('id'),4,[6,7,8,9,10],'r70-if-huscarl-scale-'+str(len(huscarls))+'-'+('r' if 'Combi' in n else 'm'))
        huscarls.append(u)
tarant=byid(cr,'r41-unit-vii-3-tarantula-sentry-gun-battery')
if tarant is None: raise RuntimeError('Tarantula missing')
tm=find_model(tarant)
if tm is None: raise RuntimeError('Tarantula model counter missing')
tg=next((g for g in tarant.iter(C('selectionEntryGroup')) if (g.get('name') or '').startswith('Weapon Replacement')),None)
if tg is None: raise RuntimeError('Tarantula weapon group missing')
threshold_scale(tg,tm.get('id'),1,[2,3],'r70-if-tarantula-scale')

# 3) Full permitted Space Marine Armoury for Templar Champion, Warder Sergeant and Huscarl Captain.
PA_SINGLE=[('Hand Flamer','gear-hand-flamer'),('Lightning Claw','gear-lightning-claw'),('Pair of Lightning Claws','gear-pair-claws'),('Plasma Pistol','gear-plasma-pistol'),('Power Fist','gear-power-fist'),('Power Weapon','gear-power-weapon'),('Rending Weapon','gear-rending'),('Thunder Hammer','gear-thunder'),('Volkite Serpenta','gear-volkite-serpenta')]
PA_TWO=[('Combi-Bolter','gear-combi-bolter'),('Combi-Flamer','gear-combi-flamer'),('Combi-Grenade Launcher','gear-combi-grenade'),('Combi-Meltagun','gear-combi-melta'),('Combi-Plasma Gun','gear-combi-plasma'),('Combi-Volkite Charger','gear-combi-volkite'),('Storm Bolter','gear-storm-bolter')]
TDA_SINGLE=[('Chainfist','gear-chainfist'),('Lightning Claw','gear-lightning-claw'),('Pair of Lightning Claws','gear-pair-claws'),('Power Fist','gear-power-fist'),('Thunder Hammer','gear-thunder')]
TDA_TWO=[('Combi-Flamer','gear-combi-flamer'),('Combi-Grenade Launcher','gear-combi-grenade'),('Combi-Meltagun','gear-combi-melta'),('Combi-Plasma Gun','gear-combi-plasma'),('Combi-Volkite Charger','gear-combi-volkite'),('Foeblaster Boltgun','gear-foeblaster'),('Storm Bolter','gear-storm-bolter')]
for _,target in PA_SINGLE+PA_TWO+TDA_SINGLE+TDA_TWO:
    if byid(cr,target) is None: raise RuntimeError('Missing Armoury gear '+target)

def remove_old_armoury(u,leader):
    for g in direct_groups(u):
        if (g.get('name') or '').startswith(leader+' Armoury'): remove_node(cr,g)
def armoury(u,kind,idx):
    model=find_model(u); uid=f'r70-if-arm-{idx}'
    leader='Templar Champion' if kind=='templar' else ('Warder Sergeant' if kind=='warder' else 'Huscarl Captain')
    remove_old_armoury(u,leader)
    a=group(u,uid,leader+' Armoury — up to 50 points',maxpts=50)
    weapons=group(a,uid+'-weapons','Weapons — maximum two',maxsel=2)
    two=group(weapons,uid+'-two','Two-handed Weapons — maximum one',maxsel=1)
    single=PA_SINGLE if kind!='huscarl' else TDA_SINGLE
    twolist=PA_TWO if kind!='huscarl' else TDA_TWO
    # Do not offer equipment already fixed in the unit entry.
    skip={'templar':{'Rending Weapon'},'warder':{'Power Weapon'},'huscarl':set()}[kind]
    for n,(name,target) in enumerate(single):
        if name in skip: continue
        link(weapons,f'{uid}-s-{n}',name,target)
    for n,(name,target) in enumerate(twolist): link(two,f'{uid}-t-{n}',name,target)
    war=group(a,uid+'-wargear','Armour & Wargear')
    if kind!='huscarl': link(war,uid+'-art','Artificer Armour','gear-hq-artificer')
    for n,(name,target) in enumerate([('Auspex','gear-auspex'),('Bionics','gear-bionics'),('Purity Seals','gear-purity'),('Teleport Homer','gear-homer')]): link(war,f'{uid}-w-{n}',name,target)
    local(war,uid+'-mc','Master-crafted Weapon',15,'Select one weapon carried by the model; that weapon is Master-crafted.')
    if kind=='templar':
        link(war,uid+'-mb','Melta Bombs','gear-melta-bombs')
        rf=link(war,uid+'-rf','Refractor Field','gear-hq-refractor'); rf.set('hidden','true')
        m=ET.SubElement(ensure(rf,'modifiers'),C('modifier'),{'id':uid+'-rf-show','type':'set','value':'false','field':'hidden'}); c=ET.SubElement(m,C('conditions'))
        ET.SubElement(c,C('condition'),{'type':'atLeast','value':'10','field':'selections','scope':'root-entry','childId':model.get('id'),'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    if kind=='huscarl': link(war,uid+'-gh','Grenade Harness','gear-grenade-harness')
    link(war,uid+'-solar','Solarite Power Gauntlet',SOLAR)
    link(war,uid+'-solar-ex','Solarite Power Gauntlet — exchange Power Fist',SOLAR_EX)
    return a

target_units=[]
for u in list(cr.iter(C('selectionEntry'))):
    name=u.get('name') or ''
    if name.startswith('Templar Brethren Squad'): target_units.append((u,'templar'))
    elif name.startswith('Phalanx Warder Squad'): target_units.append((u,'warder'))
    elif name.startswith('Huscarl Terminator Retinue'): target_units.append((u,'huscarl'))
for n,(u,k) in enumerate(target_units): armoury(u,k,n)

# Solarite +5 exchange is only visible when that same root entry has selected a Power Fist.
for n,x in enumerate([e for e in cr.iter(C('entryLink')) if e.get('targetId')==SOLAR_EX]):
    # Remove only our own visibility modifier if re-running locally.
    x.set('hidden','true'); mods=ensure(x,'modifiers')
    m=ET.SubElement(mods,C('modifier'),{'id':f'r70-if-solar-ex-show-{n}','type':'set','value':'false','field':'hidden'}); cs=ET.SubElement(m,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'root-entry','childId':'gear-power-fist','shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# 4) Hammerfall: fill omitted Imperial Fists Infantry entries, while keeping normal Terminator transponder access independent of the Rite.
HAMMER_NAMES=('Legion Tactical Squad','Legion Assault Squad','Legion Breacher Siege Squad','Legion Reconnaissance Squad','Legion Veteran Squad','Legion Seeker Squad','Legion Heavy Support Squad','Legion Destroyer Squad','Techmarine Covenant','Legion Command Squad','Legion Honour Guard Squad','Legion Apothecarion Detachment','Legion Apothecary Detachment','Templar Brethren Squad','Phalanx Warder Squad')
added_hammer=[]
for n,u in enumerate(list(cr.iter(C('selectionEntry'))):
    name=u.get('name') or ''
    if any(name.startswith(q) for q in HAMMER_NAMES) and not has_target(u,TRANS_UNIT):
        x=link(u,f'r70-if-hammer-trans-{n}','Teleportation Transponders — Hammerfall',TRANS_UNIT)
        add_show_if(x,f'r70-if-hammer-trans-show-{n}',HAMMER)
        added_hammer.append(name)
for n,u in enumerate(list(cr.iter(C('selectionEntry'))):
    if (u.get('name') or '').startswith('Legion Terminator Command Squad') and not has_target(u,TRANS_UNIT):
        link(u,f'r70-if-termcmd-trans-{n}','Teleportation Transponders',TRANS_UNIT)

# 5) Templar Assault transport: exact one-vehicle choice, Phobos/Proteus only at the current 5-10 squad size.
def new_templar_transport(u,idx):
    for g in direct_groups(u):
        if (g.get('name') or '')=='Templar Assault — Assault Transport': remove_node(cr,g)
    g=group(u,f'r70-if-templar-transport-{idx}','Templar Assault — Assault Transport',maxsel=1)
    add_show_if(g,f'r70-if-templar-transport-{idx}-show',TEMPLAR)
    for j,(source,name) in enumerate((('hs-lr-phobos','Land Raider Phobos'),('hs-lr-proteus','Land Raider Proteus'))):
        v=clone(source,f'r70-if-ta-{idx}-{j}-'); v.set('name',name); strip_categories(v)
        mc=max_constraint(v)
        if mc is None: constraint(v,f'r70-if-ta-{idx}-{j}-max','max',1)
        else: mc.set('value','1')
        ensure(g,'selectionEntries').append(v)
    r=ET.SubElement(ensure(g,'rules'),C('rule'),{'id':f'r70-if-ta-{idx}-note','name':'Spartan condition','hidden':'false'}); ET.SubElement(r,C('description')).text='The Rite permits a Spartan only for a Templar Brethren Squad too large for both a Land Raider Phobos and a Land Raider Proteus. The current Templar Brethren unit size is 5–10, so a Spartan is not a legal Rite transport at present.'

for n,u in enumerate([e for e in cr.iter(C('selectionEntry')) if (e.get('name') or '').startswith('Templar Brethren Squad')]): new_templar_transport(u,n)

# Refresh visible Templar summary to state normal 0-1 / Rite override explicitly.
tsrc=byid(cr,'r41-unit-vii-0-templar-brethren-squad')
for r in tsrc.iter(C('rule')):
    if r.get('id')=='r68-if-templar-entry':
        d=r.find(C('description')); d.text=(d.text or '')+' Normally 0–1. Templar Assault lifts this 0–1 restriction.'

# Revisions / cache refresh.
cr.set('revision','70'); cr.set('gameSystemRevision','38'); gr.set('revision','38')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat': e.set('dataRevision','70')
    elif e.get('filePath')=='Prohammer 30k.gst': e.set('dataRevision','38')

# Validation.
def duplicate_ids(root):
    seen=set(); dup=[]
    for e in root.iter():
        i=e.get('id')
        if not i: continue
        if i in seen: dup.append(i)
        seen.add(i)
    return dup
for root,label in ((cr,'CAT'),(gr,'GST')):
    d=duplicate_ids(root)
    if d: raise RuntimeError(f'Duplicate IDs in {label}: {d[:20]}')
# 0-1 modifier must be AND: Legion VII selected, Templar Assault not selected.
conds=list(mod.iter(G('condition')))
assert any(x.get('childId')=='legion-vii' and x.get('type')=='atLeast' for x in conds)
assert any(x.get('childId')==TEMPLAR and x.get('type')=='lessThan' for x in conds)
# All playable Huscarl replacement groups now start at 4 ordinary Huscarls and scale to 9 at ten models.
for u in huscarls:
    for g in u.iter(C('selectionEntryGroup')):
        if (g.get('name') or '').startswith(('Combi-bolter Replacements','Power Weapon Replacements — any Huscarl')):
            assert max_constraint(g).get('value')=='4'
# Tarantula replacement base equals one selected gun and scales at 2/3.
assert max_constraint(tg).get('value')=='1'
# Unique leader armouries exist and are 50-point groups.
assert len([g for g in cr.iter(C('selectionEntryGroup')) if (g.get('id') or '').startswith('r70-if-arm-') and (g.get('name') or '').endswith('Armoury — up to 50 points')])>=3
# Templar Assault transport groups contain only Phobos and Proteus direct vehicles.
for g in [x for x in cr.iter(C('selectionEntryGroup')) if (x.get('id') or '').startswith('r70-if-templar-transport-') and (x.get('name') or '')=='Templar Assault — Assault Transport']:
    names=[x.get('name') for x in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry'))]
    assert names==['Land Raider Phobos','Land Raider Proteus'],names

ET.indent(ct,space='  '); ET.indent(gt,space='  '); ET.indent(it,space='  ')
ct.write(CAT,encoding='utf-8',xml_declaration=True); gt.write(GST,encoding='utf-8',xml_declaration=True); it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT); ET.parse(GST); ET.parse(IDX)
OUT.write_text(f'''Revision 70 — Imperial Fists live standards fix\nCatalogue revision: 70\nGame-system revision: 38\n\nImplemented:\n- Templar Assault now suspends the normal Templar Brethren 0–1 restriction while the Rite is selected.\n- Templar Assault still requires at least two compulsory Templar Brethren Troops through the existing Rev64 validation.\n- Rite text and Templar unit summary explicitly state the 0–1 override.\n- Huscarl ranged/melee replacement maxima now follow ordinary Huscarl count: 4 at five total models, scaling to 9 at ten total models.\n- Tarantula Lascannon replacements now scale 1–3 with selected Sentry Guns.\n- Templar Champion, Warder Sergeant and Huscarl Captain now receive real 50-point permitted Armoury selectors instead of Solarite-only placeholders.\n- Templar Champion Refractor Field only appears at maximum squad size; Warder/Huscarl leaders do not receive it because their existing Invulnerable Saves make it illegal.\n- Solarite +5 Power Fist exchange options are conditional on a selected Power Fist.\n- Hammerfall transponder coverage was filled for omitted Infantry/retinue entries ({len(added_hammer)} additional entry instances).\n- Legion Terminator Command Squad copies receive normal Terminator transponder access where missing.\n- Templar Assault transport choice is rebuilt as exactly one Phobos or Proteus. Spartan is not selectable with the current 5–10 Templar unit size because the source condition for it is never met.\n- CAT/GST/index revisions bumped for New Recruit cache refresh.\n''',encoding='utf-8')
print(OUT.read_text())
