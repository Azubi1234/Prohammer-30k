from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r64-imperial-fists-full.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS); ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()

def by_id(root,ident): return next((e for e in root.iter() if e.get('id')==ident),None)
def ensure(parent,tag,ns=CNS):
    q=f'{{{ns}}}{tag}'; x=parent.find(q)
    if x is None: x=ET.SubElement(parent,q)
    return x
def parent_of(root,target):
    for p in root.iter():
        if target in list(p): return p
    return None
def remove_pred(root,pred):
    for p in list(root.iter()):
        for x in list(p):
            if pred(x): p.remove(x)
def wipe(parent,tag):
    x=parent.find(C(tag))
    if x is not None: parent.remove(x)
def set_points(entry,value):
    cs=ensure(entry,'costs')
    for x in list(cs): cs.remove(x)
    ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(value)})
def constraint(parent,ident,typ,value,field='selections',scope='parent',child=False):
    return ET.SubElement(ensure(parent,'constraints'),C('constraint'),{'id':ident,'type':typ,'value':str(value),'field':field,'scope':scope,'shared':'true','includeChildSelections':'true' if child else 'false','includeChildForces':'false'})
def add_rule(parent,ident,name,text):
    r=ET.SubElement(ensure(parent,'rules'),C('rule'),{'id':ident,'name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=text; return r
def add_model_profile(parent,ident,name,vals):
    ps=ensure(parent,'profiles'); p=ET.SubElement(ps,C('profile'),{'id':ident,'name':name,'hidden':'false','typeId':'prof-model','typeName':'Model'}); cs=ET.SubElement(p,C('characteristics'))
    for n,tid,v in zip(['WS','BS','S','T','W','I','A','Ld','Sv'],['model-ws','model-bs','model-s','model-t','model-w','model-i','model-a','model-ld','model-sv'],vals): ET.SubElement(cs,C('characteristic'),{'name':n,'typeId':tid}).text=str(v)
    return p
def add_ranged(parent,ident,name,rng,s,ap,typ):
    ps=ensure(parent,'profiles'); p=ET.SubElement(ps,C('profile'),{'id':ident,'name':name,'hidden':'false','typeId':'prof-ranged','typeName':'Ranged Weapon'}); cs=ET.SubElement(p,C('characteristics'))
    for n,tid,v in [('Range','ranged-range',rng),('S','ranged-s',s),('AP','ranged-ap',ap),('Type','ranged-type',typ)]: ET.SubElement(cs,C('characteristic'),{'name':n,'typeId':tid}).text=str(v)
    return p
def selection(parent,ident,name,cost=0,typ='upgrade',maxv=1,default=None):
    e=ET.SubElement(ensure(parent,'selectionEntries'),C('selectionEntry'),{'id':ident,'name':name,'type':typ,'hidden':'false','import':'true',**({'defaultAmount':str(default)} if default is not None else {})}); set_points(e,cost)
    if maxv is not None: constraint(e,ident+'-max','max',maxv)
    return e
def group(parent,ident,name,minv=None,maxv=None):
    g=ET.SubElement(ensure(parent,'selectionEntryGroups'),C('selectionEntryGroup'),{'id':ident,'name':name,'hidden':'false','collective':'false','import':'true'})
    if minv is not None: constraint(g,ident+'-min','min',minv,child=True)
    if maxv is not None: constraint(g,ident+'-max','max',maxv,child=True)
    return g
def model_counter(unit,ident,name,minv,maxv,per,base=0):
    set_points(unit,base); e=selection(unit,ident,name,per,'model',maxv,default=minv); constraint(e,ident+'-min','min',minv,child=False); return e
def local_option(parent,ident,name,cost,maxv=1,rule=None):
    e=selection(parent,ident,name,cost,maxv=maxv)
    if rule: add_rule(e,ident+'-rule',name,rule)
    return e
def scaled_toggle(parent,ident,name,per_model,model_id,rule=None):
    e=selection(parent,ident,name,0,maxv=1); mods=ensure(e,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':ident+'-cost','type':'increment','value':str(per_model),'field':'pts'}); reps=ET.SubElement(m,C('repeats')); ET.SubElement(reps,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'root-entry','childId':model_id,'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})
    if rule: add_rule(e,ident+'-rule',name,rule)
    return e
def entry_link(parent,ident,name,target,maxv=1):
    l=ET.SubElement(ensure(parent,'entryLinks'),C('entryLink'),{'id':ident,'name':name,'type':'selectionEntry','targetId':target,'hidden':'false','import':'true'})
    if maxv is not None: constraint(l,ident+'-max','max',maxv)
    return l
def hide_if_missing(entry,ident,child,scope='roster'):
    mods=ensure(entry,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':ident,'type':'set','value':'true','field':'hidden'}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'lessThan','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def hide_if_selected(entry,ident,child,scope='roster'):
    mods=ensure(entry,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':ident,'type':'set','value':'true','field':'hidden'}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def hide_unless_any(entry,ident,children,scope='root-entry'):
    mods=ensure(entry,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':ident,'type':'set','value':'true','field':'hidden'}); gs=ET.SubElement(m,C('conditionGroups')); g=ET.SubElement(gs,C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(g,C('conditions'))
    for child in children: ET.SubElement(cs,C('condition'),{'type':'lessThan','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def gate_legion(entry,ident='legion-vii'):
    # Preserve unrelated modifiers, replace only our own on reruns.
    hide_if_missing(entry,'r64-if-'+entry.get('id')+'-legion',ident)
def set_primary_category(unit,target,name):
    cats=ensure(unit,'categoryLinks')
    for c in list(cats): c.set('primary','false')
    found=None
    for c in cats.findall(C('categoryLink')):
        if c.get('targetId')==target: found=c
    if found is None: found=ET.SubElement(cats,C('categoryLink'),{'id':'r64-if-'+unit.get('id')+'-cat-'+target,'name':name,'hidden':'false','targetId':target,'primary':'true'})
    found.set('primary','true'); found.set('name',name)
def add_hidden_category(unit,ident,name):
    cats=ensure(unit,'categoryLinks');
    if not any(c.get('targetId')==ident for c in cats.findall(C('categoryLink'))): ET.SubElement(cats,C('categoryLink'),{'id':'r64-if-'+unit.get('id')+'-'+ident,'name':name,'hidden':'true','targetId':ident,'primary':'false'})
def rewrite_ids(node,prefix):
    mp={}
    for e in node.iter():
        if e.get('id'): mp[e.get('id')]=prefix+e.get('id')
    for e in node.iter():
        if e.get('id'): e.set('id',mp[e.get('id')])
        for a in ('childId','field'):
            if e.get(a) in mp: e.set(a,mp[e.get(a)])
    return node
def clone_by_id(ident,prefix):
    src=by_id(cr,ident)
    if src is None: raise RuntimeError('Missing clone source '+ident)
    return rewrite_ids(deepcopy(src),prefix)
def strip_top_categories(node):
    cats=node.find(C('categoryLinks'))
    if cats is not None: node.remove(cats)
    cons=node.find(C('constraints'))
    if cons is not None: node.remove(cons)
def dedicated_transport(unit,ident,choices,model_id=None,max_models=None):
    g=group(unit,ident,'Dedicated Transport',maxv=1)
    if model_id and max_models is not None:
        mods=ensure(g,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':ident+'-hide-size','type':'set','value':'true','field':'hidden'}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'greaterThan','value':str(max_models),'field':'selections','scope':'parent','childId':model_id,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    for key in choices:
        if key=='rhino': entry_link(g,ident+'-rhino','Legion Rhino Armoured Carrier','transport-rhino')
        elif key=='drop': entry_link(g,ident+'-drop','Legion Drop Pod','transport-drop-pod')
        elif key=='dreadclaw': entry_link(g,ident+'-dread','Dreadclaw Drop Pod','transport-dreadclaw')
        elif key=='landraider':
            lr=clone_by_id('hs-land-raider',ident+'-lr-'); lr.set('name','Legion Land Raider'); strip_top_categories(lr)
            for pg in lr.iter(C('selectionEntryGroup')):
                if 'Land Raider Patterns' in (pg.get('name') or ''):
                    for co in pg.findall('.//'+C('constraint')):
                        if co.get('type')=='max': co.set('value','1')
            for pe in lr.iter(C('selectionEntry')):
                if pe.get('type')=='model':
                    for co in pe.findall('./'+C('constraints')+'/'+C('constraint')):
                        if co.get('type')=='max': co.set('value','1')
            ensure(g,'selectionEntries').append(lr)
        elif key=='spartan':
            sp=clone_by_id('hs-spartan',ident+'-sp-'); sp.set('name','Legion Spartan Assault Tank'); strip_top_categories(sp); ensure(g,'selectionEntries').append(sp)
    return g
def retinue_group(char,ident,choices):
    g=group(char,ident,'Command Retinue (does not occupy a separate FOC slot)',maxv=1)
    for name,target,pfx in choices:
        x=clone_by_id(target,pfx); x.set('name',name); strip_top_categories(x); x.set('hidden','false'); ensure(g,'selectionEntries').append(x)
    return g
def clear_build(unit,clear_profiles=False):
    for tag in ('rules','entryLinks','selectionEntries','selectionEntryGroups','costs'):
        wipe(unit,tag)
    if clear_profiles: wipe(unit,'profiles')
def per_five_group(parent,ident,name,model_id,thresholds):
    g=group(parent,ident,name,maxv=1); maxid=ident+'-max'; mods=ensure(g,'modifiers')
    for n,t in enumerate(thresholds,1):
        m=ET.SubElement(mods,C('modifier'),{'id':f'{ident}-inc-{n}','type':'increment','value':'1','field':maxid}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':str(t),'field':'selections','scope':'parent','childId':model_id,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return g

def gst_force_limit(selector,link_id,constraint_id,value,ident):
    link=by_id(gr,link_id)
    if link is None: raise RuntimeError('Missing GST link '+link_id)
    mods=ensure(link,'modifiers',GNS); m=ET.SubElement(mods,G('modifier'),{'id':ident,'type':'set','value':str(value),'field':constraint_id}); cs=ET.SubElement(m,G('conditions')); ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

def add_force_hidden_requirement(cat_id,cat_name,selector,minv=None,maxv=None):
    ce=ensure(gr,'categoryEntries',GNS)
    if by_id(gr,cat_id) is None: ET.SubElement(ce,G('categoryEntry'),{'id':cat_id,'name':cat_name,'hidden':'true'})
    force=by_id(gr,'force-standard'); fl=ensure(force,'categoryLinks',GNS); link=by_id(gr,'r64-if-fl-'+cat_id)
    if link is None: link=ET.SubElement(fl,G('categoryLink'),{'id':'r64-if-fl-'+cat_id,'name':cat_name,'hidden':'true','targetId':cat_id})
    cs=ensure(link,'constraints',GNS)
    if minv is not None:
        cid='r64-if-'+cat_id+'-min'; c=ET.SubElement(cs,G('constraint'),{'id':cid,'type':'min','value':'0','field':'selections','scope':'parent','shared':'true','includeChildSelections':'false','includeChildForces':'false'}); mods=ensure(link,'modifiers',GNS); m=ET.SubElement(mods,G('modifier'),{'id':cid+'-mod','type':'set','value':str(minv),'field':cid}); conds=ET.SubElement(m,G('conditions')); ET.SubElement(conds,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    if maxv is not None:
        cid='r64-if-'+cat_id+'-max'; c=ET.SubElement(cs,G('constraint'),{'id':cid,'type':'max','value':'99','field':'selections','scope':'parent','shared':'true','includeChildSelections':'false','includeChildForces':'false'}); mods=ensure(link,'modifiers',GNS); m=ET.SubElement(mods,G('modifier'),{'id':cid+'-mod','type':'set','value':str(maxv),'field':cid}); conds=ET.SubElement(m,G('conditions')); ET.SubElement(conds,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Clean previous Rev64 and old Imperial Fists Rev44 implementation to prevent duplicate options.
remove_pred(cr,lambda e:(e.get('id') or '').startswith('r64-if-') or ((e.get('id') or '').startswith('r44-') and ('-if-' in (e.get('id') or '') or (e.get('id') or '').startswith('r44-if-'))))
remove_pred(gr,lambda e:(e.get('id') or '').startswith('r64-if-') or (e.get('id') or '').startswith('r44-if-'))

# Source entries.
IDS={
 'templar':'r41-unit-vii-0-templar-brethren-squad','warder':'r41-unit-vii-1-phalanx-warder-squad','huscarl':'r41-unit-vii-2-huscarl-terminator-retinue','tarantula':'r41-unit-vii-3-tarantula-sentry-gun-battery','sigismund':'r41-unit-vii-4-sigismund-first-captain','rann':'r41-unit-vii-5-fafnir-rann','polux':'r41-unit-vii-6-alexis-polux','diaz':'r41-unit-vii-7-camba-diaz','garrius':'r41-unit-vii-8-evander-garrius','dorn':'r41-unit-vii-9-vii-rogal-dorn-the-praetorian-of-terra'}
U={k:by_id(cr,v) for k,v in IDS.items()}
if any(v is None for v in U.values()): raise RuntimeError('Missing Imperial Fists source entries')
for u in U.values(): gate_legion(u)

# Legion special rules exactly from current source.
leg=by_id(cr,'legion-vii')
if leg is None: raise RuntimeError('Missing legion-vii selector')
add_rule(leg,'r64-if-disciplined','Disciplined Fire','When an Imperial Fists unit makes a First Fire or Overwatch shooting attack, models in the unit may re-roll To Hit rolls of 1 when firing Bolters, Bolt Pistols, Combi-Bolters, Storm Bolters, Heavy Bolters, or the bolter component of a Combi-weapon.')
add_rule(leg,'r64-if-fortification','Fortification Masters','Imperial Fists models receive +1 to Armour Penetration rolls against Fortifications, Buildings, Bunkers and other immobile structures with an Armour Value. A non-vehicle Imperial Fists unit occupying a friendly Fortification or Bunker gains Stubborn; this provides no benefit in an enemy Fortification. If the Imperial Fists are defenders in a mission that permits Fortifications or Obstacles, they may place D3 additional 6-inch sections of razor wire or tank traps wholly within their deployment zone.')
add_rule(leg,'r64-if-blind-risk','Blind to the Risk','In a mission with variable game length, when the battle would normally end, the opposing player may demand that one additional complete game turn be played. After that turn the battle ends automatically. This has no effect if the mission already ended because a specific objective or action was completed.')

# Shared Armoury entries.
shared=ensure(cr,'sharedSelectionEntries')
def shared_up(ident,name,cost,text):
    e=ET.SubElement(shared,C('selectionEntry'),{'id':ident,'name':name,'type':'upgrade','hidden':'false','import':'true'}); set_points(e,cost); constraint(e,ident+'-max','max',1); add_rule(e,ident+'-rule',name,text); hide_if_missing(e,ident+'-hide-legion','legion-vii'); return e
solar=shared_up('r64-if-gear-solarite','Solarite Power Gauntlet',30,"Imperial Fists Character with Space Marine Armoury access. Strength 10; Power Weapon, Unwieldy, Specialist Weapon. Unlike a normal Power Fist it always strikes at Strength 10 regardless of the bearer's Strength.")
solar_ex=shared_up('r64-if-gear-solarite-exchange','Solarite Power Gauntlet — exchange Power Fist',5,'Only a model already equipped with a Power Fist may select this exchange. Replace that Power Fist with a Solarite Power Gauntlet.')
shield=shared_up('r64-if-gear-vigil','Vigil Pattern Storm Shield',25,'Imperial Fists Independent Character only. Grants a 3+ Invulnerable Save. The bearer may carry no more than one weapon in addition to the shield; the shield occupies one hand and the bearer never receives the bonus Attack for fighting with two close-combat weapons.')
trans_ic=shared_up('r64-if-gear-trans-ic','Teleportation Transponders',10,'Imperial Fists Independent Character. Normally only available while wearing Terminator Armour; Hammerfall Strike Force removes this restriction. Grants Deep Strike even if the mission would not normally permit it. An Independent Character joining another Deep Striking unit must purchase Transponders separately.')
trans_unit=shared_up('r64-if-gear-trans-unit','Teleportation Transponders',15,'Imperial Fists unit. Normally available only when every model wears Terminator Armour; Hammerfall Strike Force allows any Imperial Fists Infantry unit to purchase it. Grants Deep Strike even if the mission would not normally permit it.')

# Add Solarite options to character Armoury groups catalogue-wide (hidden unless Legion VII). Avoid vehicle armouries.
armoury_groups=[]
for g in cr.iter(C('selectionEntryGroup')):
    n=(g.get('name') or '').lower()
    if 'armoury' in n and 'vehicle' not in n and 'legion-specific' not in n:
        armoury_groups.append(g)
for idx,g in enumerate(armoury_groups):
    entry_link(g,f'r64-if-arm-{idx}-solar','Solarite Power Gauntlet',solar.get('id'))
    entry_link(g,f'r64-if-arm-{idx}-solar-ex','Solarite Power Gauntlet — exchange Power Fist',solar_ex.get('id'))
# Generic Independent Characters receive their dedicated IF group.
for uid in ('hq-praetor','hq-centurion'):
    u=by_id(cr,uid); ag=group(u,'r64-if-'+uid+'-armoury','Imperial Fists Armoury',maxv=5); hide_if_missing(ag,'r64-if-'+uid+'-arm-hide','legion-vii')
    entry_link(ag,'r64-if-'+uid+'-solar','Solarite Power Gauntlet',solar.get('id')); entry_link(ag,'r64-if-'+uid+'-solar-ex','Solarite Power Gauntlet — exchange Power Fist',solar_ex.get('id')); entry_link(ag,'r64-if-'+uid+'-shield','Vigil Pattern Storm Shield',shield.get('id'))
    t=entry_link(ag,'r64-if-'+uid+'-trans','Teleportation Transponders',trans_ic.get('id'))
    hide_unless_any(t,'r64-if-'+uid+'-trans-valid',['gear-hq-terminator','gear-hq-tartaros','gear-hq-cataphractii','r25-rite-vii-1-hammerfall-strike-force'])

# Unit transponders: Terminators always; Hammerfall for broad Infantry list.
def add_trans_link(uid,ident,hammerfall_only=False):
    u=by_id(cr,uid)
    if u is None: return
    l=entry_link(u,ident,'Teleportation Transponders',trans_unit.get('id'))
    if hammerfall_only: hide_if_missing(l,ident+'-rite','r25-rite-vii-1-hammerfall-strike-force')
for uid in ('terminator-unit',IDS['huscarl']): add_trans_link(uid,'r64-if-'+uid+'-trans',False)
for uid in ('tactical-unit','assault-unit','breacher-unit','recon-unit','veteran-unit','fa-seeker','hs-heavy-support-squad',IDS['templar'],IDS['warder']): add_trans_link(uid,'r64-if-'+uid+'-hammerfall-trans',True)

# ---- Unique units ----
# Templar Brethren
u=U['templar']; u.set('name','Templar Brethren Squad'); clear_build(u); set_primary_category(u,'cat-elites','Elites'); mid='r64-if-templar-models'; model_counter(u,mid,'Squad Models',5,10,27,0)
add_rule(u,'r64-if-templar-comp','Unit Composition','4 Templar Brethren and 1 Templar Champion; may include up to five additional Templar Brethren. The Templar Champion is a Character.')
add_rule(u,'r64-if-templar-wg','Wargear','Power Armour, Combat Shield, Bolt pistol and Rending Weapon.')
add_rule(u,'r64-if-templar-special','Special Rules','Legiones Astartes (Imperial Fists), Stubborn, Righteous Zeal.')
add_rule(u,'r64-if-templar-zeal','Righteous Zeal','Whenever the squad would normally take a Morale test for suffering 25% or more casualties from enemy shooting, it may instead move D6 inches directly towards the nearest visible enemy unit. This movement may not bring a model within 1 inch of an enemy and does not count as charging or Falling Back. If no enemy is visible, take the Morale test normally.')
g=group(u,'r64-if-templar-power','Rending Weapon Replacements — up to five models',maxv=5); local_option(g,'r64-if-templar-pw','Power Weapon',10,maxv=5,rule='Replaces that model’s Rending Weapon.')
scaled_toggle(u,'r64-if-templar-frag','Frag Grenades — whole squad',1,mid); scaled_toggle(u,'r64-if-templar-krak','Krak Grenades — whole squad',2,mid); local_option(u,'r64-if-templar-vex','Legion Vexilla',10); local_option(u,'r64-if-templar-nuncio','Nuncio-vox',10)
sg=group(u,'r64-if-templar-champ','Templar Champion Armoury — up to 50 points',maxv=20); entry_link(sg,'r64-if-templar-champ-solar','Solarite Power Gauntlet',solar.get('id')); entry_link(sg,'r64-if-templar-champ-solar-ex','Solarite Power Gauntlet — exchange Power Fist',solar_ex.get('id')); add_rule(sg,'r64-if-templar-champ-note','Templar Champion','The Templar Champion may select up to 50 points of permitted weapons and wargear from the Space Marine Armoury.')
dedicated_transport(u,'r64-if-templar-transport',['rhino','drop','dreadclaw','landraider'],mid,10)
# Hammerfall transponder restored after clear.
add_trans_link(IDS['templar'],'r64-if-templar-hammerfall-trans',True)

# Phalanx Warders
u=U['warder']; u.set('name','Phalanx Warder Squad'); clear_build(u); set_primary_category(u,'cat-elites','Elites'); mid='r64-if-warder-models'; model_counter(u,mid,'Squad Models',5,10,28,10)
add_rule(u,'r64-if-warder-comp','Unit Composition','4 Phalanx Warders and 1 Warder Sergeant; may include up to five additional Phalanx Warders. The Warder Sergeant is a Character.')
add_rule(u,'r64-if-warder-wg','Wargear','Power Armour, Boarding Shield, Bolter and Power Weapon.')
add_rule(u,'r64-if-warder-special','Special Rules','Legiones Astartes (Imperial Fists), Stubborn, Counter-Attack.')
g=per_five_group(u,'r64-if-warder-specialweps','Bolter Replacements — one per five models',mid,[10])
for k,n,c in [('flamer','Flamer',5),('melta','Meltagun',10),('plasma','Plasma Gun',15)]: local_option(g,'r64-if-warder-'+k,n,c,maxv=2,rule='Replaces one Phalanx Warder’s Bolter.')
scaled_toggle(u,'r64-if-warder-frag','Frag Grenades — whole squad',1,mid); scaled_toggle(u,'r64-if-warder-krak','Krak Grenades — whole squad',2,mid); scaled_toggle(u,'r64-if-warder-melta-bombs','Melta Bombs — whole squad',5,mid); local_option(u,'r64-if-warder-vex','Legion Vexilla',10); local_option(u,'r64-if-warder-nuncio','Nuncio-vox',10)
sg=group(u,'r64-if-warder-sgt','Warder Sergeant Armoury — up to 50 points',maxv=20); entry_link(sg,'r64-if-warder-sgt-solar','Solarite Power Gauntlet',solar.get('id')); entry_link(sg,'r64-if-warder-sgt-solar-ex','Solarite Power Gauntlet — exchange Power Fist',solar_ex.get('id')); add_rule(sg,'r64-if-warder-sgt-note','Warder Sergeant','The Warder Sergeant may select up to 50 points of permitted weapons and wargear from the Space Marine Armoury.')
dedicated_transport(u,'r64-if-warder-transport',['rhino','dreadclaw','landraider'],mid,10); add_trans_link(IDS['warder'],'r64-if-warder-hammerfall-trans',True)

# Huscarl Terminator Retinue
u=U['huscarl']; u.set('name','Huscarl Terminator Retinue'); clear_build(u); set_primary_category(u,'cat-retinue','Retinue'); mid='r64-if-huscarl-models'; model_counter(u,mid,'Retinue Models',5,10,50,0)
add_rule(u,'r64-if-huscarl-comp','Unit Composition','4 Huscarls and 1 Huscarl Captain; may include up to five additional Huscarls. The Huscarl Captain is a Character.')
add_rule(u,'r64-if-huscarl-wg','Wargear','Cataphractii Terminator Armour, Combi-bolter and Power Weapon.')
add_rule(u,'r64-if-huscarl-special','Special Rules','Legiones Astartes (Imperial Fists), Stubborn, Retinue.')
g=group(u,'r64-if-huscarl-ranged','Combi-bolter Replacements — any Huscarl',maxv=10)
for k,n,c in [('foe','Foeblaster Boltgun',5),('flamer','Combi-flamer',10),('volkite','Combi-volkite charger',10),('melta','Combi-meltagun',15),('plasma','Combi-plasma gun',15)]: local_option(g,'r64-if-huscarl-'+k,n,c,maxv=10,rule='Replaces that Huscarl’s Combi-bolter.')
g=group(u,'r64-if-huscarl-melee','Power Weapon Replacements — any Huscarl',maxv=10)
for k,n,c in [('fist','Power Fist',10),('claw','Lightning Claw',10),('chain','Chainfist',15),('hammer','Thunder Hammer',15)]: local_option(g,'r64-if-huscarl-melee-'+k,n,c,maxv=10,rule='Replaces that Huscarl’s Power Weapon.')
local_option(u,'r64-if-huscarl-harness','Grenade Harness',10)
sg=group(u,'r64-if-huscarl-captain','Huscarl Captain Armoury — up to 50 points',maxv=20); entry_link(sg,'r64-if-huscarl-cap-solar','Solarite Power Gauntlet',solar.get('id')); entry_link(sg,'r64-if-huscarl-cap-solar-ex','Solarite Power Gauntlet — exchange Power Fist',solar_ex.get('id')); add_rule(sg,'r64-if-huscarl-cap-note','Huscarl Captain','The Huscarl Captain may select up to 50 points of permitted Terminator weapons and wargear from the Space Marine Armoury.')
add_trans_link(IDS['huscarl'],'r64-if-huscarl-trans',False)
add_rule(u,'r64-if-huscarl-retinue','Retinue','One Huscarl Terminator Retinue may be selected for Rogal Dorn, Sigismund or an Imperial Fists Praetor wearing Terminator Armour. The squad does not occupy a separate Force Organisation slot.')

# Tarantula
u=U['tarantula']; u.set('name','Tarantula Sentry Gun Battery'); clear_build(u); set_primary_category(u,'cat-fast','Fast Attack'); mid='r64-if-tarantula-guns'; model_counter(u,mid,'Tarantula Sentry Guns',1,3,20,0)
add_rule(u,'r64-if-tarantula-wg','Wargear','Twin-linked Heavy Bolter.')
add_rule(u,'r64-if-tarantula-special','Special Rules','Automated Targeting, Firing Mode, Disposable Platform.')
add_rule(u,'r64-if-tarantula-mode','Firing Mode','After deployment but before the first turn, choose one mode for each Tarantula. Point Defence: fixed 90-degree arc, engage targets within 24 inches. Sentry: 360-degree arc, engage targets within 12 inches. The mode cannot be changed.')
add_rule(u,'r64-if-tarantula-auto','Automated Targeting','A Tarantula fires automatically during the Imperial Fists Shooting phase if an eligible target exists. Heavy Bolter Tarantulas fire at the nearest visible non-Vehicle enemy unit; Lascannon Tarantulas fire at the nearest visible enemy Vehicle or Monstrous Creature. If no preferred target is available, fire at the nearest other eligible enemy target.')
add_rule(u,'r64-if-tarantula-disposable','Disposable Platform','Any Glancing or Penetrating Hit destroys the Tarantula.')
g=group(u,'r64-if-tarantula-weapons','Weapon Replacement — any gun',maxv=3); local_option(g,'r64-if-tarantula-las','Twin-linked Lascannon',15,maxv=3,rule='Replaces that Tarantula’s Twin-linked Heavy Bolter.')

# Named character helper.
def character_base(key,name,points,wargear,special):
    u=U[key]; u.set('name',name); clear_build(u); set_primary_category(u,'cat-hq','HQ'); set_points(u,points); add_rule(u,'r64-if-'+key+'-wargear','Wargear',wargear); add_rule(u,'r64-if-'+key+'-special','Special Rules',special); return u

u=character_base('sigismund','Sigismund, First Captain',220,'Artificer Armour, Iron Halo, Terminator Honours, Purity Seals, Bolt pistol, The Black Sword.','Legiones Astartes (Imperial Fists), Independent Character, Master of the Legion, Honour or Death, Kingslayer.')
add_rule(u,'r64-if-sig-black','The Black Sword','Two-Handed, Master-crafted Power Weapon; +2 Strength. Sigismund never requires worse than a 3+ To Hit in close combat. A natural To Wound roll of 6 inflicts a Massive Wound (D3) instead of a normal Wound.')
add_rule(u,'r64-if-sig-kingslayer','Kingslayer','After deployment but before the first turn, nominate one enemy Independent Character. If Sigismund personally slays that character, the Imperial Fists player receives +150 Victory Points and Sigismund becomes Fearless for the rest of the battle. If the nominated character survives, the opposing player instead receives +150 Victory Points. Only applies in missions using Victory Points.')
retinue_group(u,'r64-if-sig-retinue',[('Templar Brethren Squad',IDS['templar'],'r64-if-sig-templar-'),('Huscarl Terminator Retinue',IDS['huscarl'],'r64-if-sig-huscarl-')])

u=character_base('rann','Fafnir Rann',175,'Artificer Armour, Refractor Field, The Headsman, The Hunter, Frag grenades.','Legiones Astartes (Imperial Fists), Independent Character, Master of the Legion, Executioner’s Tax, Lord Seneschal.')
local_option(u,'r64-if-rann-krak','Krak Grenades',2); local_option(u,'r64-if-rann-melta','Melta Bombs',5)
add_rule(u,'r64-if-rann-weapons','The Headsman and the Hunter','A matched pair of Power Weapons. The +1 Attack for two close-combat weapons is already included in Rann’s profile. Against a Vehicle, Rann may use both as one heavy blow: he makes one fewer Attack and those attacks gain Armourbane.')
add_rule(u,'r64-if-rann-tax','Executioner’s Tax','Whenever an enemy unit successfully charges Rann or a unit he has joined, that enemy unit suffers D3 automatic Strength 5 AP4 hits after completing the charge move but before close-combat attacks are resolved.')
add_rule(u,'r64-if-rann-seneschal','Lord Seneschal','While Rann has joined a Legion Breacher Squad or Phalanx Warder Squad, that unit receives +1 Weapon Skill during an Assault phase in which it charged.')

u=character_base('polux','Alexis Polux',170,'Power Armour, Vigil Pattern Storm Shield, Terminator Honours, Combi-meltagun, Master-crafted Power Fist, Frag grenades.','Legiones Astartes (Imperial Fists), Independent Character, Master of the Legion, Stubborn, Teleport Transponder, The Crimson Fist.')
local_option(u,'r64-if-polux-krak','Krak Grenades',2)
add_rule(u,'r64-if-polux-shield','Vigil Pattern Storm Shield','Grants a 3+ Invulnerable Save. Occupies one hand and prevents Polux from gaining the bonus Attack for fighting with two close-combat weapons.')
add_rule(u,'r64-if-polux-trans','Teleport Transponder','Before deployment, Polux may be assigned to one Legion Terminator Squad, Legion Terminator Command Squad or Huscarl Terminator Retinue. Polux and the nominated unit gain Deep Strike and must enter play together if they use this rule.')
add_rule(u,'r64-if-polux-fist','The Crimson Fist','At the beginning of an Assault phase in which Polux is engaged, he may make a single attack with his Master-crafted Power Fist instead of his normal attacks. It is resolved at Initiative 4 and Strength 8 and ignores Armour Saves. Polux makes exactly one attack that Assault phase regardless of bonuses.')

u=character_base('diaz','Camba Diaz',160,'Artificer Armour, Refractor Field, Power Weapon, Bolt pistol, Frag grenades.','Legiones Astartes (Imperial Fists), Independent Character, Stubborn, Hold the Line.')
local_option(u,'r64-if-diaz-krak','Krak Grenades',2); local_option(u,'r64-if-diaz-melta','Melta Bombs',5)
add_rule(u,'r64-if-diaz-hold','Hold the Line','If Diaz and the unit he has joined did not move during the Movement phase, they gain Counter-Attack until the beginning of the next Imperial Fists turn. They may also re-roll failed Morale tests during this time.')
retinue_group(u,'r64-if-diaz-retinue',[('Phalanx Warder Squad',IDS['warder'],'r64-if-diaz-warder-'),('Legion Command Squad','hq-centurion-ret-command','r64-if-diaz-command-')])

u=character_base('garrius','Evander Garrius',200,'Cataphractii Terminator Armour, Subjugator, Volkite Charger, Bionics.','Legiones Astartes (Imperial Fists), Independent Character, Master of the Legion, Fearless, Tyrant of Cthonia.')
add_rule(u,'r64-if-garrius-sub','Subjugator','Master-crafted Power Fist. Attacks made with Subjugator are resolved at Strength 10 instead of doubling Garrius’ Strength.')
add_rule(u,'r64-if-garrius-tyrant','Tyrant of Cthonia','Garrius and any Imperial Fists unit he has joined may re-roll failed Pinning tests. If Garrius’ unit wins a close combat, it may re-roll the dice for Consolidation distance; the second result must be accepted.')
retinue_group(u,'r64-if-garrius-retinue',[('Huscarl Terminator Retinue',IDS['huscarl'],'r64-if-garrius-huscarl-'),('Legion Terminator Command Squad','hq-praetor-ret-termcommand','r64-if-garrius-term-')])

# Rogal Dorn
u=U['dorn']; u.set('name','Rogal Dorn — The Praetorian of Terra'); clear_build(u,clear_profiles=True); set_primary_category(u,'cat-low','Lords of War'); set_points(u,490); add_model_profile(u,'r64-if-dorn-profile','Rogal Dorn',['7','6','6','6','6','6','5','10','1+'])
add_rule(u,'r64-if-dorn-wg','Wargear','Auric Armour, Storm’s Teeth, Voice of Terra, Frag Grenades.')
add_rule(u,'r64-if-dorn-special','Special Rules','Primarch, Legiones Astartes (Imperial Fists), The Unyielding, Lord Castellan, Master of Defence, This Ground Shall Not Fall.')
add_rule(u,'r64-if-dorn-armour','Auric Armour','Counts as Primarch Armour.')
add_rule(u,'r64-if-dorn-teeth','Storm’s Teeth','Two-Handed Power Weapon. Attacks are resolved at +2 Strength and have Shred and Rampage.')
add_ranged(u,'r64-if-dorn-voice','Voice of Terra','24"','5','4','Salvo 3/5, Rending')
add_rule(u,'r64-if-dorn-unyield','The Unyielding','Rogal Dorn may re-roll Armour Saves of 1. The second result must be accepted.')
add_rule(u,'r64-if-dorn-castellan','Lord Castellan','Friendly Imperial Fists units with at least one model within 12 inches of Dorn gain Stubborn. A unit which already has Stubborn may instead re-roll failed Pinning tests while within 12 inches.')
add_rule(u,'r64-if-dorn-defence','Master of Defence','Dorn and any unit he has joined count as equipped with Frag Grenades when assaulted through Difficult Terrain. In addition, Dorn and any unit he has joined may make an Overwatch attack when charged even if another rule or circumstance would normally prevent it.')
add_rule(u,'r64-if-dorn-ground','This Ground Shall Not Fall','After terrain has been placed but before deployment, nominate up to two Fortifications, ruins or other suitable defensive terrain features wholly or partially within the Imperial Fists deployment zone. Each nominated feature improves its Cover Save by 1 to a maximum of 3+. Friendly Imperial Fists units occupying either nominated feature may not be Pinned. These benefits last for the battle.')
retinue_group(u,'r64-if-dorn-retinue',[('Legion Honour Guard Squad','hq-praetor-ret-honour','r64-if-dorn-honour-'),('Legion Terminator Command Squad','hq-praetor-ret-termcommand','r64-if-dorn-term-'),('Huscarl Terminator Retinue',IDS['huscarl'],'r64-if-dorn-huscarl-'),('Templar Brethren Squad',IDS['templar'],'r64-if-dorn-templar-')])
add_rule(u,'r64-if-dorn-retinue-note','Primarch Retinue','A Huscarl Terminator Retinue selected for Rogal Dorn ignores any normal requirement for the accompanying Character to wear Terminator Armour.')

# Imperial Fists Praetor Huscarl retinue (available only in Terminator Armour).
pra=by_id(cr,'hq-praetor'); pg=group(pra,'r64-if-praetor-huscarl-group','Imperial Fists Retinue',maxv=1); hide_if_missing(pg,'r64-if-praetor-huscarl-leg','legion-vii'); hide_unless_any(pg,'r64-if-praetor-huscarl-armour',['gear-hq-terminator','gear-hq-tartaros','gear-hq-cataphractii'])
h=clone_by_id(IDS['huscarl'],'r64-if-praetor-huscarl-'); h.set('name','Huscarl Terminator Retinue'); strip_top_categories(h); h.set('hidden','false'); ensure(pg,'selectionEntries').append(h)

# ---- Rites of War ----
STONE='r25-rite-vii-0-the-stone-gauntlet'; HAMMER='r25-rite-vii-1-hammerfall-strike-force'; TEMPLAR='r25-rite-vii-2-templar-assault'
# Max one Fast Attack for Stone Gauntlet and Templar Assault.
gst_force_limit(STONE,'fl-fast','fl-fast-max',1,'r64-if-stone-fast-max'); gst_force_limit(TEMPLAR,'fl-fast','fl-fast-max',1,'r64-if-templar-fast-max')

# Role clones.
top=ensure(cr,'selectionEntries')
def rite_clone(source_id,ident,name,rite,hidden_cat=None):
    x=clone_by_id(source_id,ident+'-'); x.set('id',ident); x.set('name',name); x.set('hidden','false'); set_primary_category(x,'cat-troops','Troops'); gate_legion(x); hide_if_missing(x,ident+'-rite-hide',rite)
    if hidden_cat: add_hidden_category(x,hidden_cat,hidden_cat)
    top.append(x); return x
ward_stone=rite_clone(IDS['warder'],'r64-if-stone-warders','Phalanx Warder Squad — Stone Gauntlet Troops',STONE,'r64-if-cat-stone-comp')
ward_hammer=rite_clone(IDS['warder'],'r64-if-hammer-warders','Phalanx Warder Squad — Hammerfall Troops',HAMMER,None)
temp_troops=rite_clone(IDS['templar'],'r64-if-templar-troops','Templar Brethren Squad — Templar Assault Troops',TEMPLAR,'r64-if-cat-templar-comp')
# Stone compulsory selections: Breachers or Warders, at least two total. Templar Assault: compulsory selections must be Templar Brethren, at least two.
add_hidden_category(by_id(cr,'breacher-unit'),'r64-if-cat-stone-comp','Stone Gauntlet Compulsory Troops')
add_force_hidden_requirement('r64-if-cat-stone-comp','Stone Gauntlet Compulsory Troops',STONE,minv=2)
add_force_hidden_requirement('r64-if-cat-templar-comp','Templar Assault Compulsory Troops',TEMPLAR,minv=2)
# Global 0-1 Templar Brethren across Elite and Rite clone; 0-2 Tarantula Batteries.
add_hidden_category(U['templar'],'r64-if-cat-templar-limit','Templar Brethren 0-1'); add_hidden_category(temp_troops,'r64-if-cat-templar-limit','Templar Brethren 0-1'); add_force_hidden_requirement('r64-if-cat-templar-limit','Templar Brethren 0-1','legion-vii',maxv=1)
add_hidden_category(U['tarantula'],'r64-if-cat-tarantula-limit','Tarantula Batteries 0-2'); add_force_hidden_requirement('r64-if-cat-tarantula-limit','Tarantula Batteries 0-2','legion-vii',maxv=2)

# Templar Assault transport override: add a separate Rite-only choice to both Elite and Troops versions.
def add_templar_assault_transport(unit,prefix):
    g=group(unit,prefix,'Templar Assault — Assault Transport',maxv=1); hide_if_missing(g,prefix+'-hide',TEMPLAR)
    # Explicit patterns from source.
    lr=clone_by_id('hs-land-raider',prefix+'-lr-'); lr.set('name','Land Raider Phobos or Proteus'); strip_top_categories(lr)
    for pg in lr.iter(C('selectionEntryGroup')):
        if 'Land Raider Patterns' in (pg.get('name') or ''):
            for pe in list(pg.findall('./'+C('selectionEntries')+'/'+C('selectionEntry'))):
                if 'Achilles' in (pe.get('name') or ''): parent=parent_of(cr,pe)
            # Hide Achilles pattern if present in this cloned subtree.
            for pe in pg.iter(C('selectionEntry')):
                if 'Achilles' in (pe.get('name') or ''): pe.set('hidden','true')
            for co in pg.findall('.//'+C('constraint')):
                if co.get('type')=='max': co.set('value','1')
    ensure(g,'selectionEntries').append(lr)
    sp=clone_by_id('hs-spartan',prefix+'-sp-'); sp.set('name','Legion Spartan Assault Tank — only where Land Raider capacity is insufficient'); strip_top_categories(sp); ensure(g,'selectionEntries').append(sp)
    add_rule(g,prefix+'-note','Assault Transports','A Templar Brethren Squad may select Land Raider Phobos or Land Raider Proteus at normal cost. A squad size which cannot be carried by either may instead select a Legion Spartan Assault Tank. All normal Transport Capacity restrictions apply.')
add_templar_assault_transport(U['templar'],'r64-if-templar-assault-transport'); add_templar_assault_transport(temp_troops,'r64-if-templar-troops-assault-transport')

# Rite rules displayed on the selections, preserving source mechanics that cannot be safely auto-enforced.
for rid,title,text in [
(STONE,'The Stone Gauntlet','Phalanx Warder Squads may be selected as Troops and fulfil compulsory Troops; Breacher Siege Squads may also fulfil compulsory Troops. A shield-equipped Infantry unit may form a Shield Wall if it did not Advance in its preceding Movement phase, is not Falling Back and did not charge this player turn. While active, failed Invulnerable Saves from Boarding Shields or Vigil Pattern Storm Shields may be re-rolled; the unit gains Stubborn and may re-roll failed Pinning tests. Boarding Shield models gain Hammer of Wrath using the ProHammer definition. Compulsory Troops must be Breacher Siege Squads or Phalanx Warders. The Detachment must include at least one Independent Character with a Boarding Shield or Vigil Pattern Storm Shield. No unit may voluntarily deploy by Deep Strike. Maximum one Fast Attack choice.'),
(HAMMER,'Hammerfall Strike Force','Phalanx Warder Squads may be selected as Troops and fulfil compulsory Troops. Any Imperial Fists Infantry unit may buy Teleportation Transponders for +15 points per unit and any Imperial Fists Independent Character for +10, overriding the Terminator-only restriction. A unit arriving by Deep Strike using Transponders gains Shrouded until the beginning of its next player turn; after placement, enemy units within 12 inches and line of sight test Initiative or suffer Blind until the end of their next player turn. The Warlord must have Transponders; every Vehicle must begin in Reserve; no Fortification may be included.'),
(TEMPLAR,'Templar Assault','Templar Brethren Squads may be selected as Troops and fulfil compulsory Troops. If a Templar Brethren Squad charges after disembarking from an Assault Vehicle in the same turn it gains Furious Charge and its normal charge distance increases from 6 inches to 7 inches. In the first round of a combat in which it charged, models may re-roll To Hit rolls of 1 with Rending Weapons, Power Weapons, Relic Blades and other sword-like weapons. Compulsory Troops must be Templar Brethren. Maximum one Fast Attack choice; no Fortification. The Warlord must have a Power Weapon, Rending Weapon, Relic Blade or other sword-like close-combat weapon which ignores Armour Saves.')]:
    e=by_id(cr,rid)
    if e is not None: add_rule(e,'r64-if-'+rid+'-full',title,text)

# Revision bump.
cr.set('revision','64'); cr.set('gameSystemRevision','32'); gr.set('revision','32')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat': e.set('dataRevision','64')
    if e.get('filePath')=='Prohammer 30k.gst': e.set('dataRevision','32')

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
expected={'templar':(5,10),'warder':(5,10),'huscarl':(5,10),'tarantula':(1,3)}
for k,(mn,mx) in expected.items():
    u=U[k]; counters=[e for e in u.findall('.//'+C('selectionEntry')) if e.get('type')=='model' and (e.get('id') or '').startswith('r64-if-')]
    if not counters: raise RuntimeError('Missing total counter '+k)
    vals={c.get('type'):float(c.get('value')) for c in counters[0].findall('./'+C('constraints')+'/'+C('constraint'))}
    if vals.get('min')!=mn or vals.get('max')!=mx: raise RuntimeError(f'Bad size {k}: {vals}')
# Required exact transports.
def direct_transport_names(unit):
    out=[]
    for g in unit.iter(C('selectionEntryGroup')):
        if g.get('name')=='Dedicated Transport':
            links=g.find(C('entryLinks'))
            if links is not None:
                out += [l.get('name') for l in links.findall(C('entryLink'))]
            entries=g.find(C('selectionEntries'))
            if entries is not None:
                out += [e.get('name') for e in entries.findall(C('selectionEntry'))]
    return set(out)
if direct_transport_names(U['templar'])!={'Legion Rhino Armoured Carrier','Legion Drop Pod','Dreadclaw Drop Pod','Legion Land Raider'}: raise RuntimeError('Templar transport mismatch '+repr(direct_transport_names(U['templar'])))
if direct_transport_names(U['warder'])!={'Legion Rhino Armoured Carrier','Dreadclaw Drop Pod','Legion Land Raider'}: raise RuntimeError('Warder transport mismatch '+repr(direct_transport_names(U['warder'])))

ET.indent(ct,space='  '); ET.indent(gt,space='  '); ET.indent(it,space='  ')
ct.write(CAT,encoding='utf-8',xml_declaration=True); gt.write(GST,encoding='utf-8',xml_declaration=True); it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT); ET.parse(GST); ET.parse(IDX)
OUT.write_text('''Revision 64 — Imperial Fists full-army implementation\nCatalogue revision: 64\nGame-system revision: 32\n\nSource authority: current Forces of the Legions document only.\n\nImplemented:\n- Disciplined Fire, Fortification Masters, Blind to the Risk\n- Solarite Power Gauntlet, Vigil Pattern Storm Shield, Teleportation Transponders\n- The Stone Gauntlet, Hammerfall Strike Force, Templar Assault\n- Templar Brethren Squad 5–10\n- Phalanx Warder Squad 5–10\n- Huscarl Terminator Retinue 5–10\n- Tarantula Sentry Gun Battery 1–3, 0–2 batteries\n- Sigismund, Fafnir Rann, Alexis Polux, Camba Diaz, Evander Garrius\n- Rogal Dorn\n\nExact Dedicated Transport audit:\n- Templar Brethren: Rhino, Drop Pod, Dreadclaw Drop Pod, Land Raider\n- Phalanx Warders: Rhino, Dreadclaw Drop Pod, Land Raider\n\nRite mechanics:\n- Stone Gauntlet and Templar Assault: Fast Attack maximum 1 enforced.\n- Stone Gauntlet compulsory Troops requirement enforced through hidden category: minimum 2 Breacher/Warder selections.\n- Templar Assault compulsory Troops requirement enforced through hidden category: minimum 2 Templar Brethren selections.\n- Hammerfall and Stone Gauntlet Warder Troops role clones added.\n- Templar Assault Templar Brethren Troops role clone added.\n- Templar Assault Land Raider Phobos/Proteus and conditional Spartan transport options exposed with source restriction text.\n- Requirements without a safe universal catalogue tag (Fortification bans, voluntary Deep Strike ban, Vehicle Reserve requirement, Warlord equipment requirement, shield-equipped IC requirement) remain explicitly stated in the Rite rule rather than guessed.\n''',encoding='utf-8')
print(OUT.read_text())
