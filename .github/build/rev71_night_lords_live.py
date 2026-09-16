from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r71-night-lords-live.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS); ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()
if cr.get('revision')!='70' or gr.get('revision')!='38': raise RuntimeError(f'Expected CAT70/GST38 baseline, got CAT{cr.get("revision")}/GST{gr.get("revision")}')

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t,ns=CNS):
    T=C if ns==CNS else (G if ns==GNS else I); x=p.find(T(t))
    if x is None: x=ET.SubElement(p,T(t))
    return x
def wipe(p,t,ns=CNS):
    T=C if ns==CNS else (G if ns==GNS else I); x=p.find(T(t))
    if x is not None: p.remove(x)
def parent_map(root): return {c:p for p in root.iter() for c in p}
def remove_node(root,node):
    pm=parent_map(root); p=pm.get(node)
    if p is not None:p.remove(node)
def remove_pred(root,pred):
    for p in list(root.iter()):
        for x in list(p):
            if pred(x):p.remove(x)
def set_points(e,v):
    cs=ensure(e,'costs'); [cs.remove(x) for x in list(cs)]; ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def constraint(p,i,typ,val,field='selections',scope='parent',child=False,ns=CNS):
    T=C if ns==CNS else G
    return ET.SubElement(ensure(p,'constraints',ns),T('constraint'),{'id':i,'type':typ,'value':str(val),'field':field,'scope':scope,'shared':'true','includeChildSelections':'true' if child else 'false','includeChildForces':'false'})
def rule(p,i,n,text):
    r=ET.SubElement(ensure(p,'rules'),C('rule'),{'id':i,'name':n,'hidden':'false'}); ET.SubElement(r,C('description')).text=text; return r
def ranged(p,i,n,rng,s,ap,typ):
    ps=ensure(p,'profiles'); q=ET.SubElement(ps,C('profile'),{'id':i,'name':n,'hidden':'false','typeId':'prof-ranged','typeName':'Ranged Weapon'}); cs=ET.SubElement(q,C('characteristics'))
    for nn,tid,v in [('Range','ranged-range',rng),('S','ranged-s',s),('AP','ranged-ap',ap),('Type','ranged-type',typ)]: ET.SubElement(cs,C('characteristic'),{'name':nn,'typeId':tid}).text=str(v)
    return q
def entry(p,i,n,cost=0,typ='upgrade',maxv=1,default=None,minv=None):
    attrs={'id':i,'name':n,'type':typ,'hidden':'false','import':'true'}
    if default is not None:attrs['defaultAmount']=str(default)
    e=ET.SubElement(ensure(p,'selectionEntries'),C('selectionEntry'),attrs); set_points(e,cost)
    if minv is not None:constraint(e,i+'-min','min',minv)
    if maxv is not None:constraint(e,i+'-max','max',maxv)
    return e
def group(p,i,n,minv=None,maxv=None,maxpts=None):
    g=ET.SubElement(ensure(p,'selectionEntryGroups'),C('selectionEntryGroup'),{'id':i,'name':n,'hidden':'false','collective':'false','import':'true'})
    if minv is not None:constraint(g,i+'-min','min',minv,child=True)
    if maxv is not None:constraint(g,i+'-max','max',maxv,child=True)
    if maxpts is not None:constraint(g,i+'-pts','max',maxpts,'pts','parent',True)
    return g
def link(p,i,n,target,maxv=1):
    x=ET.SubElement(ensure(p,'entryLinks'),C('entryLink'),{'id':i,'name':n,'type':'selectionEntry','targetId':target,'hidden':'false','import':'true'})
    if maxv is not None:constraint(x,i+'-max','max',maxv)
    return x
def show_if_all(e,i,conditions):
    e.set('hidden','true'); m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'}); gs=ET.SubElement(m,C('conditionGroups')); cg=ET.SubElement(gs,C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(cg,C('conditions'))
    for typ,val,scope,child in conditions: ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def hide_if_missing(e,i,child,scope='roster'):
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'true','field':'hidden'}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'lessThan','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def hide_if_atleast(e,i,child,val=1,scope='root-entry'):
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'true','field':'hidden'}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def set_primary(u,target,name):
    cs=ensure(u,'categoryLinks')
    for c in cs.findall(C('categoryLink')):c.set('primary','false')
    x=next((c for c in cs.findall(C('categoryLink')) if c.get('targetId')==target),None)
    if x is None:x=ET.SubElement(cs,C('categoryLink'),{'id':'r71-nl-'+u.get('id')+'-'+target,'name':name,'hidden':'false','targetId':target,'primary':'true'})
    x.set('primary','true');x.set('name',name)
def hidden_category(u,target,name):
    cs=ensure(u,'categoryLinks')
    if not any(c.get('targetId')==target for c in cs.findall(C('categoryLink'))): ET.SubElement(cs,C('categoryLink'),{'id':'r71-nl-'+u.get('id')+'-'+target,'name':name,'hidden':'true','targetId':target,'primary':'false'})
def rewrite_ids(node,prefix):
    mp={e.get('id'):prefix+e.get('id') for e in node.iter() if e.get('id')}
    for e in node.iter():
        if e.get('id') in mp:e.set('id',mp[e.get('id')])
        for a in ('childId','field'):
            if e.get(a) in mp:e.set(a,mp[e.get(a)])
    return node
def clone(i,prefix):
    s=byid(cr,i)
    if s is None:raise RuntimeError('Missing clone source '+i)
    return rewrite_ids(deepcopy(s),prefix)
def strip_top(node,mods=True):
    for t in ('categoryLinks','constraints'):
        x=node.find(C(t))
        if x is not None:node.remove(x)
    if mods:
        x=node.find(C('modifiers'))
        if x is not None:node.remove(x)
def max_constraint(e):
    cs=e.find(C('constraints'))
    return next((x for x in cs.findall(C('constraint')) if x.get('type')=='max' and x.get('field')=='selections'),None) if cs is not None else None
def dynamic_group_max(g,base,extra_id,prefix,per_extra=1):
    c=max_constraint(g)
    if c is None:c=constraint(g,prefix+'-max','max',base,child=True)
    else:c.set('value',str(base))
    m=ET.SubElement(ensure(g,'modifiers'),C('modifier'),{'id':prefix+'-inc','type':'increment','value':str(per_extra),'field':c.get('id')}); rs=ET.SubElement(m,C('repeats')); ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'parent','childId':extra_id,'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})
def per_five_group(p,i,n,extra_id):
    g=group(p,i,n,maxv=1); c=max_constraint(g); m=ET.SubElement(ensure(g,'modifiers'),C('modifier'),{'id':i+'-ten','type':'increment','value':'1','field':c.get('id')}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'5','field':'selections','scope':'parent','childId':extra_id,'shared':'true','includeChildSelections':'true','includeChildForces':'false'}); return g
def scaled_toggle_multi(p,i,n,per,model_ids,ruletext=None):
    e=entry(p,i,n,0)
    mods=ensure(e,'modifiers')
    for j,mid in enumerate(model_ids):
        m=ET.SubElement(mods,C('modifier'),{'id':f'{i}-cost-{j}','type':'increment','value':str(per),'field':'pts'}); rs=ET.SubElement(m,C('repeats')); ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'root-entry','childId':mid,'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})
    if ruletext:rule(e,i+'-rule',n,ruletext)
    return e
def model_ids(u): return [e.get('id') for e in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if e.get('type')=='model']
def clear_build(u,profiles=False):
    for t in ('rules','entryLinks','selectionEntries','selectionEntryGroups','costs'):wipe(u,t)
    if profiles:wipe(u,'profiles')
def fixed_plus_extra(u,prefix,base,extra_cost,max_total,base_name='Base Squad',extra_name='Additional Models'):
    b=entry(u,prefix+'-base',base_name,0,'model',base,base,base); ex=entry(u,prefix+'-extra',extra_name,extra_cost,'model',max_total-base,0,0); return b,ex
def add_rule_list(u,prefix,items):
    for j,(n,text) in enumerate(items):rule(u,f'{prefix}-{j}',n,text)
def remove_links_target(root,targets):
    for p in list(root.iter()):
        q=p.find(C('entryLinks'))
        if q is not None:
            for x in list(q):
                if x.get('targetId') in targets:q.remove(x)
def group_by_name(u,needle): return next((g for g in u.iter(C('selectionEntryGroup')) if needle.lower() in (g.get('name') or '').lower()),None)
def add_shared_link_once(g,i,n,target):
    if g is None:return None
    old=next((x for x in g.findall('./'+C('entryLinks')+'/'+C('entryLink')) if x.get('targetId')==target),None)
    return old if old is not None else link(g,i,n,target)
def clone_vehicle(source,prefix,name):
    v=clone(source,prefix);v.set('name',name);strip_top(v);c=max_constraint(v)
    if c is None:constraint(v,prefix+'max','max',1)
    else:c.set('value','1')
    return v
def dedicated_transport_infantry(u,prefix,extra_id):
    g=group(u,prefix,'Dedicated Transport',maxv=1)
    link(g,prefix+'-rhino','Legion Rhino Armoured Carrier','transport-rhino');link(g,prefix+'-drop','Legion Drop Pod','transport-drop-pod');link(g,prefix+'-dread','Dreadclaw Drop Pod','transport-dreadclaw')
    for src,nm,cap_extra in [('hs-lr-phobos','Land Raider Phobos',5),('hs-lr-proteus','Land Raider Proteus',5),('hs-lr-achilles','Land Raider Achilles',1)]:
        v=clone_vehicle(src,prefix+'-'+src+'-',nm)
        if cap_extra<5:hide_if_atleast(v,prefix+'-'+src+'-cap',extra_id,cap_extra+1)
        ensure(g,'selectionEntries').append(v)
    return g
def dedicated_transport_terminator(u,prefix,extra_id):
    g=group(u,prefix,'Dedicated Transport',maxv=1)
    d=link(g,prefix+'-dread','Dreadclaw Drop Pod','transport-dreadclaw');hide_if_atleast(d,prefix+'-dread-cap',extra_id,1)
    for src,nm in [('hs-lr-phobos','Land Raider Phobos'),('hs-lr-proteus','Land Raider Proteus')]:
        v=clone_vehicle(src,prefix+'-'+src+'-',nm);hide_if_atleast(v,prefix+'-'+src+'-cap',extra_id,1);ensure(g,'selectionEntries').append(v)
    sp=clone_vehicle('hs-spartan',prefix+'-spartan-','Legion Spartan Assault Tank');ensure(g,'selectionEntries').append(sp)
    return g
def retinue(char,prefix,choices):
    g=group(char,prefix,'Command Retinue (does not occupy a separate Force Organisation slot)',maxv=1)
    for j,(nm,src) in enumerate(choices):
        x=clone(src,f'{prefix}-{j}-');x.set('name',nm);strip_top(x);x.set('hidden','false');ensure(g,'selectionEntries').append(x)
    return g
def gate_traitor(e,prefix):hide_if_missing(e,prefix,'allegiance-traitor')
def direct_top_units():
    top=cr.find(C('selectionEntries'));return [] if top is None else list(top.findall(C('selectionEntry')))

LEG='legion-viii'; TA='r25-rite-viii-0-terror-assault'; HC='r25-rite-viii-1-horror-cult'
IDS={'terror':'r41-unit-viii-0-terror-squad','raptor':'r41-unit-viii-1-night-raptor-squad','contekar':'r41-unit-viii-2-contekar-terminator-elite','atramentar':'r41-unit-viii-3-atramentar-flay-clade','sevatar':'r41-unit-viii-4-jago-sevatarion','ophion':'r41-unit-viii-5-kheron-ophion','malcharion':'r41-unit-viii-6-malcharion-the-war-sage','shang':'r41-unit-viii-7-shang','mawdrym':'r41-unit-viii-8-flaymaster-mawdrym-llansahai','curze':'r41-unit-viii-9-viii-konrad-curze-the-night-haunter'}
for i in (LEG,TA,HC,*IDS.values(),'transport-rhino','transport-drop-pod','transport-dreadclaw','hs-lr-phobos','hs-lr-proteus','hs-lr-achilles','hs-spartan','hq-praetor','hq-centurion','terminator-unit','veteran-unit'):
    if byid(cr,i) is None:raise RuntimeError('Missing required CAT id '+i)
if byid(cr,'allegiance-traitor') is None:raise RuntimeError('Missing Traitor allegiance selector')

# Clean any partial Rev71 rerun and remove the two obsolete Night Lords Troops clones.
remove_pred(cr,lambda e:(e.get('id') or '').startswith('r71-nl-'))
remove_pred(gr,lambda e:(e.get('id') or '').startswith('r71-nl-'))
for oid in ('r42-role-viii-0-terror-formations-night-raptor-squads-r41-unit-viii-1-night-raptor-squad','r42-role-viii-1-effects-raptor-cult-night-raptor-squads-r41-unit-viii-1-night-raptor-squad'):
    x=byid(cr,oid)
    if x is not None:remove_node(cr,x)

# ----- Legion rules -----
leg=byid(cr,LEG)
rr=leg.find(C('rules'))
if rr is not None:
    for x in list(rr):
        if (x.get('name') or '').lower() in ('lords of the night','terror made manifest','masters of the terror assault','terror assault'):rr.remove(x)
add_rule_list(leg,'r71-nl-legion',[
('Lords of the Night','All models with the Legiones Astartes (Night Lords) special rule gain Night Vision. Night Lords retain exclusive access to the Stealth Adept Veteran Skill as described in the Night Lords Armoury.'),
('Terror Made Manifest','Whenever a non-vehicle Night Lords unit completely destroys an enemy unit in close combat, including by Sweeping Advance, it becomes Terrifying until the end of its next Assault phase. A Terrifying unit gains Fear. In addition, if it charges an enemy unit that it outnumbers, every model in the Night Lords unit gains +1 Attack for the first round of that combat. This bonus is not cumulative.'),
('Masters of the Terror Assault','Night Lords units arriving by Deep Strike may re-roll the Scatter die. Night Lords units arriving by Outflank may re-roll the roll used to determine which table edge they arrive from.'),
('Terror Assault','A Night Lords army exchanges two Heavy Support selections for one additional Fast Attack selection. Using the Standard Force Organisation Chart this is 0–4 Fast Attack and 0–1 Heavy Support.')])

# ----- Shared Night Lords Armoury -----
def rebuild_shared(i,name,cost,text):
    e=byid(cr,i)
    if e is None:
        e=ET.SubElement(ensure(cr,'sharedSelectionEntries'),C('selectionEntry'),{'id':i,'name':name,'type':'upgrade','hidden':'false','import':'true'});constraint(e,i+'-max','max',1)
    e.set('name',name);set_points(e,cost);wipe(e,'rules');wipe(e,'modifiers');rule(e,i+'-rule',name,text);hide_if_missing(e,i+'-legion',LEG);return e
chainglaive=rebuild_shared('r44-nl-chainglaive','Nostraman Chainglaive',10,'Night Lords Independent Character or squad Sergeant with Space Marine Armoury access. Strength: User +1. Rending, Two-Handed. The Nostraman Chainglaive does not count as a Power Weapon.')
trophies=rebuild_shared('r44-nl-trophies','Trophies of Judgement',10,'Enemy units with one or more models within 8 inches of one or more models equipped with Trophies of Judgement suffer -1 Leadership. Multiple Trophies are not cumulative. Friendly models are unaffected. If an entire squad is equipped, measure from any model in that squad; the squad counts as one source.')
stealth_ic=rebuild_shared('r44-nl-stealth-ic','Stealth Adept',5,'Night Lords Independent Character only. Grants Stealth. A model mounted on a Bike or Jetbike or wearing any form of Terminator Armour may not purchase this upgrade. An Independent Character joining a unit with Stealth Adept must also possess Stealth Adept or the unit cannot benefit while that character remains attached.')
# Kept only for backward compatibility; live squad options below calculate +1/model correctly.
stealth_legacy=rebuild_shared('r44-nl-stealth-unit','Stealth Adept — legacy shared marker',0,'Do not select this marker directly. Live Night Lords Infantry and Jump Infantry squads use a unit-local +1 point per model option so the cost scales correctly.')
kraken=rebuild_shared('r44-nl-kraken-bolts','Kraken Light Bolts',10,'Legion Tactical Squad or Legion Veteran Squad. Bolters, Combi-Bolters, Twin-linked Bolters and the bolter component of Combi-Weapons are AP4 while firing Kraken Light Bolts. May not be combined with Special Issue Ammunition or any other ammunition upgrade. A Tactical Squad may not use Fury of the Legion in a Shooting phase in which it fires Kraken Light Bolts.')
trans_ic=rebuild_shared('r44-nl-transponder-character','Teleportation Transponders',10,'Night Lords Independent Character wearing any form of Terminator Armour. Grants Deep Strike even if the mission would not normally permit it. An Independent Character intending to Deep Strike as part of another unit must purchase Transponders separately.')
trans_unit=rebuild_shared('r44-nl-transponder-unit','Teleportation Transponders',15,'Night Lords unit composed entirely of models wearing any form of Terminator Armour. Grants Deep Strike even if the mission would not normally permit it.')

# Remove all obsolete free squad Stealth links; live options are local and scale with model count.
remove_links_target(cr,{'r44-nl-stealth-unit'})
# Rebuild generic Independent Character Night Lords Armoury placement/restrictions.
for uid in ('hq-praetor','hq-centurion'):
    u=byid(cr,uid)
    remove_links_target(u,{'r44-nl-chainglaive','r44-nl-trophies','r44-nl-stealth-ic','r44-nl-transponder-character'})
    two=group_by_name(u,'Two-Handed Weapons'); wg=group_by_name(u,'Additional Wargear') or group_by_name(u,'Wargear')
    add_shared_link_once(two,'r71-nl-'+uid+'-chain','Nostraman Chainglaive','r44-nl-chainglaive')
    add_shared_link_once(wg,'r71-nl-'+uid+'-trophy','Trophies of Judgement','r44-nl-trophies')
    st=add_shared_link_once(wg,'r71-nl-'+uid+'-stealth','Stealth Adept','r44-nl-stealth-ic')
    if st is not None:
        show_if_all(st,'r71-nl-'+uid+'-stealth-show',[('atLeast',1,'roster',LEG),('lessThan',1,'root-entry','gear-hq-terminator'),('lessThan',1,'root-entry','gear-hq-tartaros'),('lessThan',1,'root-entry','gear-hq-cataphractii'),('lessThan',1,'root-entry','gear-hq-bike'),('lessThan',1,'root-entry','r37-praetor-jetbike'),('lessThan',1,'root-entry','r37-centurion-jetbike')])
    tr=add_shared_link_once(wg,'r71-nl-'+uid+'-trans','Teleportation Transponders','r44-nl-transponder-character')
    if tr is not None:
        tr.set('hidden','true');m=ET.SubElement(ensure(tr,'modifiers'),C('modifier'),{'id':'r71-nl-'+uid+'-trans-show','type':'set','value':'false','field':'hidden'});gs=ET.SubElement(m,C('conditionGroups'));cg=ET.SubElement(gs,C('conditionGroup'),{'type':'or'});cs=ET.SubElement(cg,C('conditions'))
        for tid in ('gear-hq-terminator','gear-hq-tartaros','gear-hq-cataphractii'):ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'root-entry','childId':tid,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# ----- Rites -----
for rite_id in (TA,HC):
    r=byid(cr,rite_id);wipe(r,'rules')
if byid(cr,TA) is not None:
    r=byid(cr,TA)
    add_rule_list(r,'r71-nl-ta',[
    ('Cover of Darkness','The first Battle Round uses Night Fighting. At the beginning of the second Battle Round roll a D6; on a 3+ Night Fighting remains for round two. If it remained in round two, roll at the beginning of round three; on a 6 Night Fighting remains for round three. It ends automatically at the beginning of round four. Night Lords use their normal Night Vision throughout.'),
    ('Terror Formations','Night Raptor Squads and Terror Squads may be selected as Troops and may fulfil compulsory Troops selections. At least one compulsory Troops selection must be a Night Raptor Squad or Terror Squad.'),
    ('Terror Attack','Whenever the opposing player makes Reserve rolls, after all rolls have been made, the Night Lords player may force one successful Reserve roll to be re-rolled. The second result is accepted and a die may never be re-rolled more than once.'),
    ('Rapid Strike Force','The Detachment uses 0–4 Fast Attack and 0–1 Heavy Support. All other Force Organisation limits remain unchanged.'),
    ('Limitations','The Detachment must include at least one Night Raptor Squad or Terror Squad, may include no more than one Heavy Support choice, and may not include a Fortification.')])
if byid(cr,HC) is not None:
    r=byid(cr,HC);gate_traitor(r,'r71-nl-hc-traitor')
    add_rule_list(r,'r71-nl-hc',[
    ('Raptor Cult','Night Raptor Squads may be selected as Troops and may fulfil compulsory Troops selections. At least one compulsory Troops selection must be a Night Raptor Squad.'),
    ('Beyond Judgement','Any Night Lords Infantry or Jump Infantry squad may purchase the Beyond Judgement upgrade for +25 points per unit. Every model is treated as equipped with Trophies of Judgement; measure the 8-inch penalty from any model. The unit also gains Fear. Leadership penalties from multiple Trophies remain non-cumulative.'),
    ('Vox-Scream Broadcast','Once per battle, at the beginning of any Night Lords player turn, declare a Vox-Scream Broadcast. Until the beginning of the next Night Lords player turn all enemy units suffer -1 Leadership. This may combine with Trophies of Judgement.'),
    ('The Scent of Blood','A non-Vehicle Night Lords unit using this Rite must declare a charge in its Assault phase if it is normally eligible to charge and at least one legal enemy target is within its current charge distance. If several targets are eligible, the Night Lords player chooses. A unit is never required to declare an illegal charge.'),
    ('Limitations','Traitor Night Lords only. The Detachment may not include a Fortification. A Night Lords unit using this Rite may not voluntarily withdraw from close combat.')])

# ----- Unique units -----
U={k:byid(cr,v) for k,v in IDS.items()}
# Terror Squad
u=U['terror'];u.set('name','Terror Squad');clear_build(u);set_points(u,150);set_primary(u,'cat-elites','Elites');b,e=fixed_plus_extra(u,'r71-nl-terror',5,25,10,'Base Squad — 4 Terror Marines + Headsman','Additional Terror Marines')
add_rule_list(u,'r71-nl-terror-rule',[
('Unit Composition','4 Terror Marines and 1 Headsman. The Headsman is a Character. Up to five additional Terror Marines may be added.'),('Wargear','Power Armour, Bolter, Bolt pistol, Chainsword, Frag grenades and Trophies of Judgement.'),('Special Rules','Legiones Astartes (Night Lords), Infiltrate, Preferred Enemy (Infantry).')])
g=group(u,'r71-nl-terror-melee','Chainsword Replacements — any model',maxv=10);dynamic_group_max(g,5,e.get('id'),'r71-nl-terror-melee');entry(g,'r71-nl-terror-rending','Rending Weapon',5,ruletext if False else 'upgrade')
# replace the two generated choices with explicit rule-bearing upgrades
for x in list(g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry'))):g.find(C('selectionEntries')).remove(x)
x=entry(g,'r71-nl-terror-rending','Rending Weapon',5);rule(x,'r71-nl-terror-rending-rule','Replacement','Replaces one model’s Chainsword.')
x=entry(g,'r71-nl-terror-power','Power Weapon',10);rule(x,'r71-nl-terror-power-rule','Replacement','Replaces one model’s Chainsword.')
g=group(u,'r71-nl-terror-volkite','Bolter Replacements — any model');dynamic_group_max(g,5,e.get('id'),'r71-nl-terror-volkite');x=entry(g,'r71-nl-terror-charger','Volkite Charger',10,maxv=10);rule(x,'r71-nl-terror-charger-rule','Replacement','Replaces one model’s Bolter.')
g=per_five_group(u,'r71-nl-terror-special','Special Weapon Replacements — one per five models',e.get('id'))
for k,n,c in [('flamer','Flamer',5),('rotor','Rotor Cannon',10),('heavy-flamer','Heavy Flamer',10)]:x=entry(g,'r71-nl-terror-'+k,n,c,maxv=2);rule(x,'r71-nl-terror-'+k+'-rule','Replacement','Replaces one Terror Marine’s Bolter.')
scaled_toggle_multi(u,'r71-nl-terror-krak','Krak Grenades — whole squad',2,[b.get('id'),e.get('id')])
scaled_toggle_multi(u,'r71-nl-terror-melta','Melta Bombs — whole squad',5,[b.get('id'),e.get('id')])
scaled_toggle_multi(u,'r71-nl-terror-stealth','Stealth Adept — whole squad',1,[b.get('id'),e.get('id')],'Every model gains Stealth. An attached Independent Character must also possess Stealth Adept or the squad may not benefit while that character remains attached.')
dedicated_transport_infantry(u,'r71-nl-terror-transport',e.get('id'))
# Night Raptor
u=U['raptor'];u.set('name','Night Raptor Squad');clear_build(u);set_points(u,140);set_primary(u,'cat-fast','Fast Attack');b,e=fixed_plus_extra(u,'r71-nl-raptor',5,28,15,'Base Squad — 4 Night Raptors + Raptor Sergeant','Additional Night Raptors')
add_rule_list(u,'r71-nl-raptor-rule',[
('Unit Composition','4 Night Raptors and 1 Raptor Sergeant. The Raptor Sergeant is a Character. Up to ten additional Night Raptors may be added.'),('Wargear','Power Armour, Jump Pack, Bolt pistol, Chainsword, Frag grenades and Trophies of Judgement.'),('Special Rules','Legiones Astartes (Night Lords), Hit & Run.')])
g=group(u,'r71-nl-raptor-melee','Chainsword Replacements — up to five models',maxv=5)
for k,n,c in [('rending','Rending Weapon',5),('power','Power Weapon',10)]:x=entry(g,'r71-nl-raptor-'+k,n,c,maxv=5);rule(x,'r71-nl-raptor-'+k+'-rule','Replacement','Replaces one model’s Chainsword.')
g=group(u,'r71-nl-raptor-pistol','Bolt Pistol Replacements — up to two Night Raptors',maxv=2)
for k,n,c in [('serpenta','Volkite Serpenta',5),('handflamer','Hand Flamer',5),('plasma','Plasma Pistol',15)]:x=entry(g,'r71-nl-raptor-'+k,n,c,maxv=2);rule(x,'r71-nl-raptor-'+k+'-rule','Replacement','Replaces one Night Raptor’s Bolt pistol.')
entry(u,'r71-nl-raptor-melta','Melta Bombs — up to two models',5,maxv=2)
scaled_toggle_multi(u,'r71-nl-raptor-krak','Krak Grenades — whole squad',2,[b.get('id'),e.get('id')]);scaled_toggle_multi(u,'r71-nl-raptor-stealth','Stealth Adept — whole squad',1,[b.get('id'),e.get('id')],'Every model gains Stealth. An attached Independent Character must also possess Stealth Adept or the squad may not benefit while attached.')
head=entry(u,'r71-nl-raptor-headtaker','Upgrade Raptor Sergeant to Headtaker (WS5)',15);rule(head,'r71-nl-raptor-headtaker-rule','Headtaker','The Raptor Sergeant becomes a Headtaker and has Weapon Skill 5. The Headtaker may select up to 50 points of permitted weapons and wargear from the Space Marine Armoury and Night Lords Armoury.')
# Contekar
u=U['contekar'];u.set('name','Contekar Terminator Elite');clear_build(u);set_points(u,250);set_primary(u,'cat-elites','Elites');b,e=fixed_plus_extra(u,'r71-nl-contekar',5,50,10,'Base Squad — 4 Contekar + Contekar Dissident','Additional Contekar')
add_rule_list(u,'r71-nl-contekar-rule',[
('Unit Composition','4 Contekar and 1 Contekar Dissident. The Dissident is a Character. Up to five additional Contekar may be added.'),('Wargear','Tartaros Terminator Armour, Heavy Flamer and Nostraman Chainblade.'),('Special Rules','Legiones Astartes (Night Lords), Stubborn.'),('Nostraman Chainblade','A Nostraman Chainblade is a Two-Handed Rending Weapon which grants +1 Strength.'),('Escaton Power Claw','An Escaton Power Claw counts as a Power Fist. In addition, the wielder may re-roll failed To Wound rolls made with it.')])
g=group(u,'r71-nl-contekar-ranged','Heavy Flamer Replacements — every model');dynamic_group_max(g,5,e.get('id'),'r71-nl-contekar-ranged');x=entry(g,'r71-nl-contekar-culverin','Volkite Culverin',10,maxv=10);rule(x,'r71-nl-contekar-culverin-rule','Replacement','Replaces one model’s Heavy Flamer.')
g=group(u,'r71-nl-contekar-claw','Chainblade Replacements — up to two models',maxv=2);x=entry(g,'r71-nl-contekar-esct','Escaton Power Claw',10,maxv=2);rule(x,'r71-nl-contekar-esct-rule','Replacement','Replaces one Nostraman Chainblade.')
entry(u,'r71-nl-contekar-harness','Grenade Harness — Contekar Dissident',10)
dedicated_transport_terminator(u,'r71-nl-contekar-transport',e.get('id'));link(u,'r71-nl-contekar-transponder','Teleportation Transponders','r44-nl-transponder-unit')
# Atramentar
u=U['atramentar'];u.set('name','Atramentar Flay-Clade');clear_build(u);set_points(u,250);set_primary(u,'cat-elites','Elites');b,e=fixed_plus_extra(u,'r71-nl-atramentar',5,50,10,'Base Squad — 5 Atramentar','Additional Atramentar')
add_rule_list(u,'r71-nl-atramentar-rule',[
('Unit Composition','5 Atramentar. Up to five additional Atramentar may be added.'),('Wargear','Cataphractii Terminator Armour, Trophies of Judgement, Combi-bolter and Power Weapon.'),('Special Rules','Legiones Astartes (Night Lords), Fearless, Teleport Assault.'),('Teleport Assault','An Atramentar Flay-Clade may deploy using Deep Strike even if the mission does not normally permit Deep Strike. All other normal ProHammer Deep Strike rules apply.')])
rangedg=group(u,'r71-nl-atramentar-ranged','Combi-bolter Replacements');dynamic_group_max(rangedg,5,e.get('id'),'r71-nl-atramentar-ranged')
for k,n,c in [('storm','Storm Bolter',0),('foe','Foeblaster Boltgun',5),('flamer','Combi-flamer',10),('volkite','Combi-volkite Charger',10),('melta','Combi-meltagun',15),('plasma','Combi-plasma Gun',15)]:x=entry(rangedg,'r71-nl-atramentar-r-'+k,n,c,maxv=10);rule(x,'r71-nl-atramentar-r-'+k+'-rule','Replacement','Replaces one model’s Combi-bolter.')
meleeg=group(u,'r71-nl-atramentar-melee','Power Weapon Replacements');dynamic_group_max(meleeg,5,e.get('id'),'r71-nl-atramentar-melee')
for k,n,c in [('fist','Power Fist',5),('claw','Lightning Claw',5),('chain','Chainfist',10),('hammer','Thunder Hammer',10)]:x=entry(meleeg,'r71-nl-atramentar-m-'+k,n,c,maxv=10);rule(x,'r71-nl-atramentar-m-'+k+'-rule','Replacement','Replaces one model’s Power Weapon.')
pair=entry(u,'r71-nl-atramentar-pair','Pair of Lightning Claws — replaces both weapons',15,maxv=10);pairmax=max_constraint(pair);dynamic_pair_mods=ensure(u,'modifiers')
# Each selected pair consumes one possible ranged and one possible melee replacement slot.
for j,g in enumerate((rangedg,meleeg)):
    c=max_constraint(g);m=ET.SubElement(ensure(g,'modifiers'),C('modifier'),{'id':f'r71-nl-atramentar-pair-dec-{j}','type':'decrement','value':'1','field':c.get('id')});rs=ET.SubElement(m,C('repeats'));ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'parent','childId':pair.get('id'),'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})
# Pair count itself follows total model count.
pm=max_constraint(pair);m=ET.SubElement(ensure(pair,'modifiers'),C('modifier'),{'id':'r71-nl-atramentar-pair-inc','type':'increment','value':'1','field':pm.get('id')}); # reset base below
pm.set('value','5');rs=ET.SubElement(m,C('repeats'));ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'parent','childId':e.get('id'),'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})
hg=per_five_group(u,'r71-nl-atramentar-heavy','Heavy Weapon Replacements — one per five models',e.get('id'))
for k,n,c in [('flamer','Heavy Flamer',10),('reaper','Reaper Autocannon',15),('plasma','Plasma Blaster',15)]:x=entry(hg,'r71-nl-atramentar-h-'+k,n,c,maxv=2);rule(x,'r71-nl-atramentar-h-'+k+'-rule','Replacement','Replaces one Atramentar’s Combi-bolter.')
dedicated_transport_terminator(u,'r71-nl-atramentar-transport',e.get('id'))

# Proper 50-point Space Marine + Night Lords Armouries for Headsman and Headtaker.
SINGLE=[('Hand Flamer','gear-hand-flamer'),('Lightning Claw','gear-lightning-claw'),('Pair of Lightning Claws','gear-pair-claws'),('Plasma Pistol','gear-plasma-pistol'),('Power Fist','gear-power-fist'),('Power Weapon','gear-power-weapon'),('Rending Weapon','gear-rending'),('Thunder Hammer','gear-thunder'),('Volkite Serpenta','gear-volkite-serpenta')]
TWO=[('Combi-Bolter','gear-combi-bolter'),('Combi-Flamer','gear-combi-flamer'),('Combi-Grenade Launcher','gear-combi-grenade'),('Combi-Meltagun','gear-combi-melta'),('Combi-Plasma Gun','gear-combi-plasma'),('Combi-Volkite Charger','gear-combi-volkite'),('Storm Bolter','gear-storm-bolter')]
WARG=[('Auspex','gear-auspex'),('Bionics','gear-bionics'),('Purity Seals','gear-purity'),('Teleport Homer','gear-homer')]
for _,tid in SINGLE+TWO+WARG+[('Artificer Armour','gear-hq-artificer'),('Refractor Field','gear-hq-refractor'),('Melta Bombs','gear-melta-bombs')]:
    if byid(cr,tid) is None:raise RuntimeError('Missing armoury gear '+tid)
def leader_armoury(u,prefix,title,extra_id,max_extra,show_child=None):
    a=group(u,prefix,title+' Armoury — up to 50 points',maxpts=50)
    if show_child:show_if_all(a,prefix+'-show',[('atLeast',1,'root-entry',show_child)])
    wg=group(a,prefix+'-weapons','Weapons — maximum two',maxv=2);one=group(wg,prefix+'-single','Single-Handed Weapons',maxv=2);two=group(wg,prefix+'-two','Two-Handed Weapons — maximum one',maxv=1)
    for j,(n,tid) in enumerate(SINGLE):link(one,f'{prefix}-s-{j}',n,tid)
    for j,(n,tid) in enumerate(TWO):link(two,f'{prefix}-t-{j}',n,tid)
    link(two,prefix+'-chain','Nostraman Chainglaive','r44-nl-chainglaive')
    war=group(a,prefix+'-war','Armour & Wargear');link(war,prefix+'-art','Artificer Armour','gear-hq-artificer')
    for j,(n,tid) in enumerate(WARG):link(war,f'{prefix}-w-{j}',n,tid)
    link(war,prefix+'-melta','Melta Bombs','gear-melta-bombs');entry(war,prefix+'-mc','Master-crafted Weapon',15)
    rf=link(war,prefix+'-rf','Refractor Field','gear-hq-refractor');show_if_all(rf,prefix+'-rf-show',[('atLeast',max_extra,'root-entry',extra_id)])
leader_armoury(U['terror'],'r71-nl-headsman','Headsman','r71-nl-terror-extra',5)
leader_armoury(U['raptor'],'r71-nl-headtaker-arm','Headtaker','r71-nl-raptor-extra',10,'r71-nl-raptor-headtaker')

# ----- Generic squad Night Lords options -----
# Add Chainglaive/Trophies to Sergeant Armouries; add true +1/model Stealth to eligible Infantry/Jump Infantry unit entries, including generic Rite copies.
ELIGIBLE_PREFIXES=('legion tactical squad','legion assault squad','legion breacher siege squad','legion reconnaissance squad','legion veteran squad','legion destroyer squad','legion seeker squad','legion heavy support squad')
def is_generic_eligible(u):return u.get('type')=='unit' and any((u.get('name') or '').lower().startswith(x) for x in ELIGIBLE_PREFIXES)
def add_generic_nl(u,idx):
    mids=model_ids(u)
    if not mids:return
    # Remove any prior old free Stealth link nested in this unit.
    remove_links_target(u,{'r44-nl-stealth-unit'})
    st=scaled_toggle_multi(u,f'r71-nl-gen-{idx}-stealth','Stealth Adept — whole squad',1,mids,'Every model in the unit gains Stealth. Models in Terminator Armour, Bikes, Jetbikes, Dreadnoughts and Vehicles are not eligible. An attached Independent Character must also possess Stealth Adept or the unit may not benefit while attached.')
    show_if_all(st,f'r71-nl-gen-{idx}-stealth-show',[('atLeast',1,'roster',LEG)])
    # Sergeant armoury additions.
    sg2=next((g for g in u.iter(C('selectionEntryGroup')) if 'two-handed weapons' in (g.get('name') or '').lower()),None)
    sgw=next((g for g in u.iter(C('selectionEntryGroup')) if 'sergeant armoury - wargear' in (g.get('name') or '').lower()),None)
    if sg2 is not None:add_shared_link_once(sg2,f'r71-nl-gen-{idx}-chain','Nostraman Chainglaive','r44-nl-chainglaive')
    if sgw is not None:add_shared_link_once(sgw,f'r71-nl-gen-{idx}-trophies','Trophies of Judgement','r44-nl-trophies')
for idx,u in enumerate([x for x in cr.iter(C('selectionEntry')) if is_generic_eligible(x)]):add_generic_nl(u,idx)

# Kraken remains Tactical/Veteran only. Ensure canonical and generic role copies have one link.
for idx,u in enumerate([x for x in cr.iter(C('selectionEntry')) if x.get('type')=='unit' and any((x.get('name') or '').lower().startswith(q) for q in ('legion tactical squad','legion veteran squad'))]):
    if not any(l.get('targetId')=='r44-nl-kraken-bolts' for l in u.iter(C('entryLink'))):link(u,f'r71-nl-kraken-{idx}','Kraken Light Bolts','r44-nl-kraken-bolts')

# Generic all-Terminator squad transponders.
for idx,u in enumerate([x for x in cr.iter(C('selectionEntry')) if x.get('type')=='unit' and (x.get('name') or '').lower().startswith('legion terminator squad')]):
    if not any(l.get('targetId')=='r44-nl-transponder-unit' for l in u.iter(C('entryLink'))):link(u,f'r71-nl-term-trans-{idx}','Teleportation Transponders','r44-nl-transponder-unit')

# Horror Cult Beyond Judgement for eligible squads. Unique Terror/Raptors already carry Trophies, but the Rite purchase is represented separately because the +25 purchase is what confers Fear.
BJ_NAMES=ELIGIBLE_PREFIXES+('legion terminator squad','terror squad','night raptor squad','contekar terminator elite','atramentar flay-clade')
def add_bj(u,idx):
    if any((x.get('id') or '').startswith('r71-nl-bj-') for x in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry'))):return
    x=entry(u,f'r71-nl-bj-{idx}','Beyond Judgement — Trophies of Judgement & Fear',25);rule(x,f'r71-nl-bj-{idx}-rule','Beyond Judgement','Every model is treated as equipped with Trophies of Judgement and the unit gains Fear. Measure the 8-inch Leadership penalty from any model. Trophies penalties are non-cumulative.');show_if_all(x,f'r71-nl-bj-{idx}-show',[('atLeast',1,'roster',LEG),('atLeast',1,'roster',HC)])
for idx,u in enumerate([x for x in cr.iter(C('selectionEntry')) if x.get('type')=='unit' and any((x.get('name') or '').lower().startswith(q) for q in BJ_NAMES)]):add_bj(u,idx)

# ----- Named characters -----
def char_reset(key,name,pts,wargear,special,extra_rules,options=(),traitor=False):
    u=U[key];u.set('name',name)
    for t in ('rules','entryLinks','selectionEntries','selectionEntryGroups','costs'):wipe(u,t)
    set_points(u,pts);rule(u,'r71-nl-'+key+'-wargear','Wargear',wargear);rule(u,'r71-nl-'+key+'-special','Special Rules',special)
    for j,(n,txt) in enumerate(extra_rules):rule(u,f'r71-nl-{key}-rule-{j}',n,txt)
    for j,(n,c,txt) in enumerate(options):x=entry(u,f'r71-nl-{key}-opt-{j}',n,c);rule(x,f'r71-nl-{key}-opt-{j}-rule','Option',txt)
    if traitor:gate_traitor(u,'r71-nl-'+key+'-traitor')
    return u
sev=char_reset('sevatar','Jago Sevatarion',200,'Artificer Armour; Iron Halo; Night’s Whisper; Bolt pistol; Trophies of Judgement; Frag grenades.','Legiones Astartes (Night Lords); Independent Character; Master of the Legion; Psyker (Mastery Level 1); Visions of Doom.',[
('Night’s Whisper','Night’s Whisper is a Two-Handed, Master-crafted Power Weapon. Attacks made with it are resolved at Strength 6.'),('Visions of Doom','Sevatar knows only the Withering Gaze psychic power. When making its Psychic Test, Sevatar uses Leadership 7 rather than his normal Leadership.'),('Withering Gaze','Used during the Night Lords Shooting phase instead of Sevatar firing a weapon. Choose one visible enemy unit within 12 inches and take a Psychic Test. If successful, until the beginning of the next Night Lords turn that unit must pass a Leadership test before declaring a charge against Sevatar or a unit he has joined. If failed it may not declare that charge, but may charge another legal target.')],[('Krak Grenades',2,'Adds Krak grenades.')])
oph=char_reset('ophion','Kheron Ophion',180,'Power Armour; Refractor Field; Power Axe; Volkite Serpenta; The Bloody Aegis; Frag grenades; Melta bombs.','Legiones Astartes (Night Lords); Independent Character; Master of the Legion; Stubborn; The Coward.',[
('The Bloody Aegis','Against close-combat attacks Ophion’s Invulnerable Save is improved to 3+. Against all other attacks he uses his Refractor Field normally.'),('The Coward','After Ophion loses his first Wound, he gains Feel No Pain (4+) for the remainder of the battle. If subsequently reduced to one remaining Wound, replace this with Feel No Pain (3+).')],[('Krak Grenades',2,'Adds Krak grenades.')],True)
mal=char_reset('malcharion','Malcharion, the War-Sage',155,'Artificer Armour; Refractor Field; Master-crafted Power Weapon; Bolter; Bolt pistol; Frag grenades.','Legiones Astartes (Night Lords); Independent Character; War-Sage.',[('War-Sage','Malcharion and any Night Lords unit he has joined may re-roll failed Morale and Pinning tests. The second result must be accepted.')],[('Krak Grenades',2,'Adds Krak grenades.'),('Melta Bombs',5,'Adds Melta bombs.')])
sha=char_reset('shang','Shang',165,'Artificer Armour; Refractor Field; Master-crafted Power Weapon; Bolt pistol; Trophies of Judgement; Frag grenades.','Legiones Astartes (Night Lords); Independent Character; Master of the Legion; Infiltrate; Preferred Enemy (Independent Characters).',[],[('Krak Grenades',2,'Adds Krak grenades.'),('Melta Bombs',5,'Adds Melta bombs.')])
maw=char_reset('mawdrym','Flaymaster Mawdrym Llansahai',125,'Power Armour; Refractor Field; Narthecium; Red Jaqa; Bolt pistol; Frag grenades.','Legiones Astartes (Night Lords); Independent Character; Fearless; Feel No Pain (5+); Devil’s Luck; Unfit for Command.',[
('Red Jaqa','Red Jaqa is a Rending Weapon. Any natural To Wound roll of 6 made with Red Jaqa inflicts a Massive Wound (D3) instead of a normal Wound.'),('Devil’s Luck','Mawdrym may re-roll Feel No Pain rolls of 1. A dice may never be re-rolled more than once.'),('Unfit for Command','Mawdrym may not fulfil the army’s compulsory HQ requirement and may never be the army’s Warlord.')],[('Krak Grenades',2,'Adds Krak grenades.')],True)
# Retinues, cloned from the now-live unit structures.
retinue(sev,'r71-nl-sev-ret',[('Legion Command Squad','hq-centurion-ret-command'),('Legion Terminator Command Squad','hq-praetor-ret-termcommand'),('Atramentar Flay-Clade',IDS['atramentar'])])
retinue(oph,'r71-nl-oph-ret',[('Legion Command Squad','hq-centurion-ret-command'),('Contekar Terminator Elite',IDS['contekar'])])
retinue(mal,'r71-nl-mal-ret',[('Legion Command Squad','hq-centurion-ret-command'),('Legion Veteran Squad','veteran-unit')])
retinue(sha,'r71-nl-shang-ret',[('Terror Squad',IDS['terror'])])

# Mawdrym cannot satisfy the compulsory HQ by himself: when selected, Standard HQ minimum becomes 2 unless Primarch's Chosen is active.
primarch_chosen=next((x for x in cr.iter(C('selectionEntry')) if "primarch" in (x.get('name') or '').lower() and "chosen" in (x.get('name') or '').lower()),None)
flhq=byid(gr,'fl-hq');hqmin=byid(gr,'fl-hq-min')
if flhq is None or hqmin is None:raise RuntimeError('Missing Standard HQ force link/min constraint')
m=ET.SubElement(ensure(flhq,'modifiers',GNS),G('modifier'),{'id':'r71-nl-mawdrym-hq-min','type':'set','value':'2','field':'fl-hq-min'});gs=ET.SubElement(m,G('conditionGroups'));cg=ET.SubElement(gs,G('conditionGroup'),{'type':'and'});cs=ET.SubElement(cg,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':IDS['mawdrym'],'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
if primarch_chosen is not None:ET.SubElement(cs,G('condition'),{'type':'lessThan','value':'1','field':'selections','scope':'roster','childId':primarch_chosen.get('id'),'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# ----- Curze -----
cur=U['curze'];cur.set('name','Konrad Curze, the Night Haunter')
for t in ('rules','entryLinks','selectionEntries','selectionEntryGroups','costs'):wipe(cur,t)
set_points(cur,500)
add_rule_list(cur,'r71-nl-curze',[
('Wargear','Nightmare Mantle; Mercy & Forgiveness; Widowmakers; Frag Grenades.'),('Special Rules','Primarch; Legiones Astartes (Night Lords); Psyker (Mastery Level 1); King of Terrors; Bloody Murder; Night Haunter; Dark Precognition.'),('Nightmare Mantle','The Nightmare Mantle counts as Primarch Armour.'),('Mercy & Forgiveness','Mercy and Forgiveness are a matched pair of Master-crafted Power Weapons. Attacks are resolved at Curze’s normal Strength and have Shred and Rending. They count as two close combat weapons.'),('Lethal Precision','On an unmodified To Wound roll of 6, a Wound inflicted by the Widowmakers allows neither Armour nor Invulnerable Saves. Cover Saves may be taken normally.'),('King of Terrors','Enemy units with at least one model within 12 inches of Konrad Curze suffer -2 Leadership. Models and units with Fearless are unaffected.'),('Bloody Murder','Curze may re-roll failed To Wound rolls of 1 against an enemy unit which is Pinned, Falling Back or below half strength.'),('Night Haunter','Konrad Curze has Stealth and Hit & Run. In the Movement phase he moves as though Jump Infantry despite not having a Jump Pack. This does not change his Unit Type or grant Deep Strike, Bulky, Swift or other Jump Infantry rules.'),('Dark Precognition','The first successful To Hit roll made against Konrad Curze during each player turn must be re-rolled; the second result is accepted. Curze is a Psyker (Mastery Level 1) and knows only Precognition from Divination. He takes the Psychic Test for Precognition using Leadership 8. All other normal psychic rules apply.')])
ranged(cur,'r71-nl-curze-widow','Widowmakers','12"','4','5','Assault 3, Lethal Precision')
retinue(cur,'r71-nl-curze-ret',[('Legion Terminator Command Squad','hq-praetor-ret-termcommand'),('Atramentar Flay-Clade',IDS['atramentar']),('Night Raptor Squad',IDS['raptor']),('Terror Squad',IDS['terror'])])
rule(cur,'r71-nl-curze-raptor-ret','Night Raptor Retinue','If Konrad Curze selects a Night Raptor Squad as his Primarch Retinue, that unit may use his Hit & Run special rule while he remains part of the unit.')

# ----- Rite Troops clones and compulsory validation -----
top=ensure(cr,'selectionEntries')
def role_clone(src,prefix,name,rite,catid):
    x=clone(src,prefix);x.set('name',name);strip_top(x);set_primary(x,'cat-troops','Troops');x.set('hidden','true');show_if_all(x,prefix+'show',[('atLeast',1,'roster',LEG),('atLeast',1,'roster',rite)]);hidden_category(x,catid,catid);top.append(x);return x
TA_CAT='r71-nl-cat-terror-assault-comp';HC_CAT='r71-nl-cat-horror-comp'
ta_rap=role_clone(IDS['raptor'],'r71-nl-ta-raptor-','Night Raptor Squad — Terror Assault Troops',TA,TA_CAT)
ta_ter=role_clone(IDS['terror'],'r71-nl-ta-terror-','Terror Squad — Terror Assault Troops',TA,TA_CAT)
hc_rap=role_clone(IDS['raptor'],'r71-nl-hc-raptor-','Night Raptor Squad — Horror Cult Troops',HC,HC_CAT)
# GST hidden compulsory categories.
ces=ensure(gr,'categoryEntries',GNS)
for cid,nm in ((TA_CAT,'Terror Assault compulsory Terror formation'),(HC_CAT,'Horror Cult compulsory Night Raptor')):
    if byid(gr,cid) is None:ET.SubElement(ces,G('categoryEntry'),{'id':cid,'name':nm,'hidden':'true'})
force=byid(gr,'force-standard');fl=ensure(force,'categoryLinks',GNS)
def force_min_cat(cid,nm,rite):
    l=ET.SubElement(fl,G('categoryLink'),{'id':'r71-nl-fl-'+cid,'name':nm,'hidden':'true','targetId':cid});c=constraint(l,'r71-nl-'+cid+'-min','min',0,ns=GNS);m=ET.SubElement(ensure(l,'modifiers',GNS),G('modifier'),{'id':'r71-nl-'+cid+'-min-mod','type':'set','value':'1','field':c.get('id')});cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':rite,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
force_min_cat(TA_CAT,'Terror Assault compulsory Terror formation',TA);force_min_cat(HC_CAT,'Horror Cult compulsory Night Raptor',HC)

# Preserve/reassert Legion VIII 4 FA / 1 HS force limits.
for lid,cid,val,mid in [('fl-fast','fl-fast-max',4,'r44-nl-fast-max'),('fl-heavy','fl-heavy-max',1,'r44-nl-heavy-max')]:
    l=byid(gr,lid);mods=ensure(l,'modifiers',GNS)
    for old in list(mods):
        if old.get('id')==mid:mods.remove(old)
    m=ET.SubElement(mods,G('modifier'),{'id':mid,'type':'set','value':str(val),'field':cid});cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':LEG,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Revisions / New Recruit cache refresh.
cr.set('revision','71');cr.set('gameSystemRevision','39');gr.set('revision','39')
for x in ir.iter(I('dataIndexEntry')):
    if x.get('filePath')=='Legiones Astartes.cat':x.set('dataRevision','71')
    elif x.get('filePath')=='Prohammer 30k.gst':x.set('dataRevision','39')

# ----- Validation -----
def dupids(root):
    s=set();d=[]
    for x in root.iter():
        i=x.get('id')
        if not i:continue
        if i in s:d.append(i)
        s.add(i)
    return d
for root,label in ((cr,'CAT'),(gr,'GST')):
    d=dupids(root)
    if d:raise RuntimeError(f'Duplicate {label} IDs: {d[:20]}')
assert not any(x.get('targetId')=='r44-nl-stealth-unit' for x in cr.iter(C('entryLink'))),'Legacy free squad Stealth links remain'
assert byid(cr,'r71-nl-ta-raptor-'+IDS['raptor']) is not None
assert byid(cr,'r71-nl-ta-terror-'+IDS['terror']) is not None
assert byid(cr,'r71-nl-hc-raptor-'+IDS['raptor']) is not None
# Unit-size structures: fixed 5 plus correct extras.
for key,maxextra in [('terror',5),('raptor',10),('contekar',5),('atramentar',5)]:
    u=U[key];models=[x for x in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if x.get('type')=='model'];assert len(models)>=2,(key,len(models));assert any(x.get('defaultAmount')=='5' for x in models);assert any(any(c.get('type')=='max' and c.get('value')==str(maxextra) for c in x.findall('./'+C('constraints')+'/'+C('constraint'))) and x.get('defaultAmount')=='0' for x in models)
# Character retinues and Curze retinue exist.
for x in (sev,oph,mal,sha,cur):assert any('Retinue' in (g.get('name') or '') for g in x.iter(C('selectionEntryGroup'))),x.get('name')
# Traitor gates.
for x in (oph,maw,byid(cr,HC)):assert any(c.get('childId')=='allegiance-traitor' for c in x.iter(C('condition'))),x.get('name')
# Atramentar heavy combined limit begins one; Contekar every-model group begins five.
assert max_constraint(byid(cr,'r71-nl-atramentar-heavy')).get('value')=='1'
assert max_constraint(byid(cr,'r71-nl-contekar-ranged')).get('value')=='5'

ET.indent(ct,space='  ');ET.indent(gt,space='  ');ET.indent(it,space='  ')
ct.write(CAT,encoding='utf-8',xml_declaration=True);gt.write(GST,encoding='utf-8',xml_declaration=True);it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT);ET.parse(GST);ET.parse(IDX)
OUT.write_text('''Revision 71 — Night Lords live implementation\nCatalogue revision: 71\nGame-system revision: 39\n\nImplemented:\n- Current Lords of the Night, Terror Made Manifest, Masters of the Terror Assault and Legion-wide 4 Fast Attack / 1 Heavy Support structure.\n- Night Lords Armoury rebuilt around proper Chainglaive two-handed placement, Trophies, true +1/model Stealth Adept, Kraken Light Bolts, and conditional Terminator-only Teleportation Transponders.\n- Generic eligible Sergeants receive Chainglaive/Trophies through their actual Sergeant Armoury groups.\n- Terror Squad rebuilt at 5–10 models with scaling squad-wide upgrades, per-five special weapons, Headsman 50-point Armoury and capacity-aware transports.\n- Night Raptor Squad rebuilt at 5–15 with correct replacement limits, true per-model upgrades and functional Headtaker + 50-point Armoury.\n- Contekar rebuilt at 5–10; Volkite replacement scales to every selected model; dedicated transports respect Terminator capacity.\n- Atramentar rebuilt at 5–10; ranged/melee replacements scale, paired claws consume both replacement allowances, heavy weapons scale 1 per 5, and dedicated transports respect Terminator capacity.\n- Terror Assault provides functional Raptor and Terror Troops copies plus a compulsory Terror-formation requirement.\n- Horror Cult is Traitor-gated, provides functional Raptor Troops and a compulsory Raptor requirement, and exposes Beyond Judgement as a +25 Rite-gated squad upgrade.\n- Sevatar, Ophion, Malcharion, Shang and Mawdrym were cleaned of source dumps and given their current rules/options; their retinues are selectable and slotless.\n- Ophion and Mawdrym are Traitor-only. Mawdrym cannot satisfy the compulsory HQ by himself: outside Primarch’s Chosen his presence raises the HQ minimum to two.\n- Konrad Curze is rebuilt with clean wargear/rules, Widowmakers ranged profile, current psychic rules, and selectable Primarch retinues.\n- CAT/GST/index revisions bumped for New Recruit cache refresh.\n''',encoding='utf-8')
print(OUT.read_text())
