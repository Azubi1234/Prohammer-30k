from pathlib import Path
from copy import deepcopy
import re
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r74-blood-angels-full.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS); ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()
if cr.get('revision')!='73' or gr.get('revision')!='41': raise RuntimeError(f'Expected CAT73/GST41 baseline, got CAT{cr.get("revision")}/GST{gr.get("revision")}')

LEG='legion-ix'; REV='r25-rite-ix-0-the-day-of-revelation'; SOR='r25-rite-ix-1-the-day-of-sorrows'
IDS={
 'dawn':'r41-unit-ix-0-dawnbreaker-cohort','pal':'r41-unit-ix-1-crimson-paladin-squad','tears':'r41-unit-ix-2-angel-s-tears-squad','ofanim':'r41-unit-ix-3-ofanim-court','grav':'r41-unit-ix-4-grav-chariot-squadron','guard':'r41-unit-ix-5-sanguinary-guard',
 'ral':'r41-unit-ix-6-raldoron-the-blooded','zephon':'r41-unit-ix-7-dominion-zephon','crohne':'r41-unit-ix-8-aster-crohne','azk':'r41-unit-ix-9-azkaellon','amit':'r41-unit-ix-10-nassir-amit-the-flesh-tearer','sang':'r41-unit-ix-11-ix-sanguinius-the-great-angel'}

# ---------- helpers ----------
def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t,ns=CNS):
    Q=C if ns==CNS else (G if ns==GNS else I); x=p.find(Q(t))
    if x is None:x=ET.SubElement(p,Q(t))
    return x
def wipe(p,t,ns=CNS):
    Q=C if ns==CNS else G; x=p.find(Q(t))
    if x is not None:p.remove(x)
def remove_prefixed(root,prefix):
    for p in list(root.iter()):
        for x in list(p):
            if (x.get('id') or '').startswith(prefix):p.remove(x)
def set_points(e,v):
    cs=ensure(e,'costs'); [cs.remove(x) for x in list(cs)]; ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def constraint(p,i,typ,val,field='selections',scope='parent',child=False,ns=CNS):
    Q=C if ns==CNS else G
    return ET.SubElement(ensure(p,'constraints',ns),Q('constraint'),{'id':i,'type':typ,'value':str(val),'field':field,'scope':scope,'shared':'true','includeChildSelections':'true' if child else 'false','includeChildForces':'false'})
def add_rule(p,i,n,text):
    r=ET.SubElement(ensure(p,'rules'),C('rule'),{'id':i,'name':n,'hidden':'false'}); ET.SubElement(r,C('description')).text=text; return r
def add_entry(p,i,n,cost=0,typ='upgrade',default=None,minv=None,maxv=1):
    e=ET.SubElement(ensure(p,'selectionEntries'),C('selectionEntry'),{'id':i,'name':n,'type':typ,'hidden':'false','import':'true',**({'defaultAmount':str(default)} if default is not None else {})});set_points(e,cost)
    if minv is not None:constraint(e,i+'-min','min',minv)
    if maxv is not None:constraint(e,i+'-max','max',maxv)
    return e
def group(p,i,n,minv=None,maxv=None):
    g=ET.SubElement(ensure(p,'selectionEntryGroups'),C('selectionEntryGroup'),{'id':i,'name':n,'hidden':'false','collective':'false','import':'true'})
    if minv is not None:constraint(g,i+'-min','min',minv,child=True)
    if maxv is not None:constraint(g,i+'-max','max',maxv,child=True)
    return g
def entry_link(p,i,n,target,maxv=1,hidden=False):
    l=ET.SubElement(ensure(p,'entryLinks'),C('entryLink'),{'id':i,'name':n,'type':'selectionEntry','targetId':target,'hidden':'true' if hidden else 'false','import':'true'})
    if maxv is not None:constraint(l,i+'-max','max',maxv)
    return l
def hide_if_missing(e,i,child,scope='roster'):
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'true','field':'hidden'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'lessThan','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def hide_if_selected(e,i,child,scope='root-entry'):
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'true','field':'hidden'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def show_if_all(e,i,conds):
    e.set('hidden','true');m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'});gs=ET.SubElement(m,C('conditionGroups'));cg=ET.SubElement(gs,C('conditionGroup'),{'type':'and'});cs=ET.SubElement(cg,C('conditions'))
    for typ,val,scope,child in conds:ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_hidden_category(e,i,target,name):
    cats=ensure(e,'categoryLinks')
    if not any(x.get('targetId')==target for x in cats.findall(C('categoryLink'))):ET.SubElement(cats,C('categoryLink'),{'id':i,'name':name,'hidden':'true','targetId':target,'primary':'false'})
def set_primary_category(e,target,name):
    cats=ensure(e,'categoryLinks'); found=None
    for x in cats.findall(C('categoryLink')):
        x.set('primary','false')
        if x.get('targetId')==target:found=x
    if found is None:found=ET.SubElement(cats,C('categoryLink'),{'id':'r74-ba-'+(e.get('id') or 'x')+'-'+target,'name':name,'hidden':'false','targetId':target,'primary':'true'})
    found.set('primary','true');found.set('name',name);found.set('hidden','false')
def direct_models(u):return [x for x in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if x.get('type')=='model']
def remove_source_rules(u):
    rs=u.find(C('rules'))
    if rs is None:return 0
    n=0
    for r in list(rs):
        nm=(r.get('name') or '').lower()
        if nm.startswith('source entry') or nm in ('special rules','wargear','unit composition'):
            rs.remove(r);n+=1
    if len(rs)==0:u.remove(rs)
    return n
def locked_gear(u,slug,name,text=None):
    e=add_entry(u,f'r74-ba-{slug}',name,0,'upgrade',1,1,1)
    if text:add_rule(e,f'r74-ba-{slug}-rule',name,text)
    return e
def add_ranged(p,i,name,rng,s,ap,typ):
    prof=ET.SubElement(ensure(p,'profiles'),C('profile'),{'id':i,'name':name,'hidden':'false','typeId':'prof-ranged','typeName':'Ranged Weapon'}); cs=ET.SubElement(prof,C('characteristics'))
    for n,tid,v in [('Range','ranged-range',rng),('S','ranged-s',s),('AP','ranged-ap',ap),('Type','ranged-type',typ)]:ET.SubElement(cs,C('characteristic'),{'name':n,'typeId':tid}).text=str(v)
    return prof
def rewrite_ids(node,prefix):
    mp={x.get('id'):prefix+x.get('id') for x in node.iter() if x.get('id')}
    for x in node.iter():
        old=x.get('id')
        if old in mp:x.set('id',mp[old])
        for a in ('childId','field'):
            if x.get(a) in mp:x.set(a,mp[x.get(a)])
    return node
def strip_top_categories(node):
    x=node.find(C('categoryLinks'))
    if x is not None:node.remove(x)
    x=node.find(C('constraints'))
    if x is not None:node.remove(x)
def clone_entry(src,prefix,name=None):
    x=rewrite_ids(deepcopy(src),prefix); strip_top_categories(x); x.set('hidden','false')
    if name:x.set('name',name)
    return x
def find_entry_name(name,typ='unit'):
    low=name.lower()
    exact=[e for e in cr.iter(C('selectionEntry')) if e.get('type')==typ and (e.get('name') or '').lower()==low]
    if exact:return exact[0]
    return next((e for e in cr.iter(C('selectionEntry')) if e.get('type')==typ and low in (e.get('name') or '').lower()),None)
def scaled_toggle_existing(opt,per,model_id,prefix):
    set_points(opt,0); wipe(opt,'modifiers')
    m=ET.SubElement(ensure(opt,'modifiers'),C('modifier'),{'id':prefix+'-cost','type':'increment','value':str(per),'field':'pts'});rs=ET.SubElement(m,C('repeats'));ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'root-entry','childId':model_id,'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})
def dynamic_max(node,model_id,prefix,base=0):
    cs=ensure(node,'constraints'); old=[x for x in cs.findall(C('constraint')) if x.get('type')=='max' and x.get('scope')=='parent']
    for x in old:cs.remove(x)
    cid=prefix+'-max';constraint(node,cid,'max',base,child=(node.tag==C('selectionEntryGroup')))
    m=ET.SubElement(ensure(node,'modifiers'),C('modifier'),{'id':prefix+'-max-inc','type':'increment','value':'1','field':cid});rs=ET.SubElement(m,C('repeats'));ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'root-entry','childId':model_id,'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})
    return cid
def move_into_group(parent_group,entries):
    dest=ensure(parent_group,'selectionEntries')
    for e in entries:
        p=None
        for q in cr.iter():
            if e in list(q):p=q;break
        if p is not None:p.remove(e);dest.append(e)
def clone_armoury_group(owner,slug,label):
    template=None
    vet=byid(cr,'veteran-unit')
    if vet is not None:
        template=next((g for g in vet.iter(C('selectionEntryGroup')) if 'sergeant armoury' in (g.get('name') or '').lower()),None)
    if template is None:return None
    g=rewrite_ids(deepcopy(template),f'r74-ba-{slug}-');g.set('name',label);ensure(owner,'selectionEntryGroups').append(g);return g
def add_retinue_group(char,slug,choices):
    g=group(char,f'r74-ba-{slug}-retinue','RETINUE — choose up to one (no separate FOC slot)',maxv=1)
    for label,src,pfx in choices:
        if src is None:continue
        x=clone_entry(src,f'r74-ba-{slug}-{pfx}-',label);ensure(g,'selectionEntries').append(x)
    return g
def gst_hidden_requirement(cat_id,name,selector,minv=2):
    ce=ensure(gr,'categoryEntries',GNS)
    if byid(gr,cat_id) is None:ET.SubElement(ce,G('categoryEntry'),{'id':cat_id,'name':name,'hidden':'true'})
    force=byid(gr,'force-standard');fl=ensure(force,'categoryLinks',GNS);link=byid(gr,'r74-ba-fl-'+cat_id)
    if link is None:link=ET.SubElement(fl,G('categoryLink'),{'id':'r74-ba-fl-'+cat_id,'name':name,'hidden':'true','targetId':cat_id})
    cid='r74-ba-'+cat_id+'-min';constraint(link,cid,'min',0,ns=GNS)
    m=ET.SubElement(ensure(link,'modifiers',GNS),G('modifier'),{'id':cid+'-set','type':'set','value':str(minv),'field':cid});cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def gst_set_limit(link_id,constraint_id,value,selector,mid):
    l=byid(gr,link_id)
    if l is None:raise RuntimeError('Missing GST link '+link_id)
    m=ET.SubElement(ensure(l,'modifiers',GNS),G('modifier'),{'id':mid,'type':'set','value':str(value),'field':constraint_id});cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def count_condition(parent,typ,val,child,scope='root-entry'):
    cs=ET.SubElement(parent,C('conditions'));ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

def unit_gate(u,extra=None):
    hide_if_missing(u,'r74-ba-'+(u.get('id') or 'u')[-45:]+'-legion',LEG)
    if extra:hide_if_missing(u,'r74-ba-'+(u.get('id') or 'u')[-45:]+'-extra',extra)

# Safe rerun hygiene.
remove_prefixed(cr,'r74-ba-'); remove_prefixed(gr,'r74-ba-')
# Remove legacy BA-specific links but preserve the shared r44 BA item definitions themselves.
for p in list(cr.iter()):
    for x in list(p):
        if x.tag==C('entryLink') and ('r44-ba-' in (x.get('id') or '') or (x.get('targetId') or '').startswith('r44-ba-')):p.remove(x)
for p in list(gr.iter()):
    for x in list(p):
        if (x.get('id') or '').startswith('r44-ba-'):p.remove(x)

U={k:byid(cr,v) for k,v in IDS.items()}
if any(v is None for v in U.values()):raise RuntimeError('Missing BA imported source entry')

# ---------- Legion selector: actual named rules ----------
leg=byid(cr,LEG)
if leg is None:raise RuntimeError('Missing Blood Angels legion selector')
wipe(leg,'rules')
add_rule(leg,'r74-ba-leg-angels','Angels of Death','During an Assault phase in which a Blood Angels model charges, it gains +1 Weapon Skill until the end of that Assault phase. This may combine with other Weapon Skill modifiers. Friendly Imperial Army or Imperial Militia units with at least one model within 6 inches of a Blood Angels unit receive +1 Leadership, to a maximum of 10; this Leadership bonus is not cumulative.')
add_rule(leg,'r74-ba-leg-descent','Descent of Angels','When a Blood Angels Jump Infantry unit deploys using Deep Strike, the controlling player may re-roll the Scatter die and any dice rolled for scatter distance. The entire result must be re-rolled and the second result accepted.')
add_rule(leg,'r74-ba-leg-vengeance','Vengeance of a Fallen Angel','Whenever a friendly Blood Angels Character is slain, every friendly non-vehicle Blood Angels unit with at least one model able to draw line of sight to the Character’s final position is affected until the end of the following Blood Angels player turn: +1 Attack, -1 Leadership, and it must charge the nearest enemy unit it can legally charge. Units already engaged still receive +1 Attack. The effect is not cumulative; another qualifying death extends its duration.')

# ---------- Shared BA armoury ----------
def shared_item(i,name,cost,text):
    e=byid(cr,i)
    if e is None:
        shared=cr.find(C('sharedSelectionEntries'));e=ET.SubElement(shared,C('selectionEntry'),{'id':i,'name':name,'type':'upgrade','hidden':'false','import':'true'});constraint(e,i+'-max','max',1)
    e.set('name',name);set_points(e,cost);wipe(e,'rules');add_rule(e,i+'-rule',name,text);return e
mask=shared_item('r44-ba-death-mask','Death Mask',10,'Blood Angels Independent Character only. If an enemy unit loses a close combat in which at least one enemy model was in base contact with the bearer, that unit suffers an additional -1 Leadership when taking the resulting Morale test. Multiple Death Masks are not cumulative.')
inferno=shared_item('r44-ba-inferno-pistol','Inferno Pistol',15,'Any Blood Angels model with access to the Space Marine Armoury may purchase an Inferno Pistol. A Legion Moritat may instead replace both Bolt Pistols with two Inferno Pistols for +20 points.')
wipe(inferno,'profiles');add_ranged(inferno,'r74-ba-inferno-profile','Inferno Pistol','6"','8','1','Pistol, Melta')
blade=shared_item('r44-ba-blade-perdition','Blade of Perdition',25,'Blood Angels Character with access to the Space Marine Armoury. Power Weapon, Two-Handed, Perdition. A natural To Wound roll of 6 causes a Massive Wound instead of a normal Wound. Counts as a sword-like weapon.')
blade_ex=shared_item('r74-ba-blade-exchange','Blade of Perdition — exchange existing Power Weapon',10,'Only a Blood Angels Character already equipped with a Power Weapon may use this exchange. The Power Weapon is replaced by a Blade of Perdition.')
engines=shared_item('r44-ba-overcharged-engines','Over-charged Engines',15,'Blood Angels Rhino only. Before moving, roll D6: 1 — the Rhino may not move; 2-3 — move normally; 4-6 — it may move as a Fast Vehicle that turn, to a maximum of 18 inches. Passengers follow normal ProHammer transport rules.')
jump=shared_item('r44-ba-furioso-jump-pack','Furioso-pattern Jump Pack',55,'0-1 per army. A Blood Angels Legion Contemptor equipped with two Dreadnought Close Combat Weapons may purchase this. It may move up to 12 inches and pass over models and terrain like Jump Infantry, remains a Walker, may charge normally, may not Deep Strike, and suffers a Glancing Hit on a D6 roll of 1 if it ends the move in Difficult or Dangerous Terrain.')
# Preserve/restore roster max 1 on Furioso pack.
cs=ensure(jump,'constraints')
if not any(x.get('type')=='max' and x.get('scope')=='roster' for x in cs.findall(C('constraint'))):constraint(jump,'r74-ba-furioso-roster','max',1,scope='roster')

# Attach BA armoury options to generic armoury groups rather than globally dumping them on units.
def owner_unit(e):
    pm={c:p for p in cr.iter() for c in p};p=e
    while p is not None:
        if p.tag==C('selectionEntry') and p.get('type')=='unit':return p
        p=pm.get(p)
    return None
arm_groups=[]
for g in list(cr.iter(C('selectionEntryGroup'))):
    n=(g.get('name') or '').lower();o=owner_unit(g)
    if 'armoury' in n and o is not None and not (o.get('id') or '').startswith('r41-unit-'):
        arm_groups.append(g)
for idx,g in enumerate(arm_groups):
    # Character/sergeant armoury access: Inferno + Blade. The source permits both to Characters with Armoury access.
    for item,label in ((inferno,'Inferno Pistol'),(blade,'Blade of Perdition')):
        l=entry_link(g,f'r74-ba-arm-{idx}-{item.get("id")}',label,item.get('id'),hidden=True);show_if_all(l,f'r74-ba-arm-{idx}-{item.get("id")}-show',[('atLeast',1,'roster',LEG)])
# Death Mask for generic Independent Characters.
for uid in ('hq-praetor','hq-centurion'):
    u=byid(cr,uid)
    if u is not None:
        l=entry_link(u,f'r74-ba-{uid}-mask','Death Mask',mask.get('id'),hidden=True);show_if_all(l,l.get('id')+'-show',[('atLeast',1,'roster',LEG)])
        # Ensure Inferno/Blade access even if the HQ armoury structure changes.
        for item,label in ((inferno,'Inferno Pistol'),(blade,'Blade of Perdition'),(blade_ex,'Blade of Perdition — exchange existing Power Weapon')):
            l=entry_link(u,f'r74-ba-{uid}-{item.get("id")}',label,item.get('id'),hidden=True);show_if_all(l,l.get('id')+'-show',[('atLeast',1,'roster',LEG)])
# Correct Rhino target: the old pass accidentally attached this to the first entry containing "rhino" (Damocles).
rhino=byid(cr,'transport-rhino')
if rhino is None:raise RuntimeError('Missing transport-rhino')
l=entry_link(rhino,'r74-ba-rhino-engines','Over-charged Engines',engines.get('id'),hidden=True);show_if_all(l,'r74-ba-rhino-engines-show',[('atLeast',1,'roster',LEG)])
# Furioso pack on the real Contemptor entry. Rule text retains the two-DCCW prerequisite; 0-1 is mechanically enforced.
cont=byid(cr,'contemptor-unit')
if cont is None:raise RuntimeError('Missing contemptor-unit')
l=entry_link(cont,'r74-ba-contemptor-jump','Furioso-pattern Jump Pack',jump.get('id'),hidden=True);show_if_all(l,'r74-ba-contemptor-jump-show',[('atLeast',1,'roster',LEG)])
# Moritat special pair for +20.
mor=next((e for e in cr.iter(C('selectionEntry')) if 'moritat' in (e.get('name') or '').lower() and 'consul' in (e.get('name') or '').lower()),None)
if mor is not None:
    x=add_entry(mor,'r74-ba-moritat-two-inferno','Two Inferno Pistols — replace both Bolt Pistols',20);add_rule(x,'r74-ba-moritat-two-inferno-rule','Inferno Pistols','Replaces both of the Moritat’s Bolt Pistols with two Inferno Pistols. Each uses Range 6 inches, Strength 8, AP1, Pistol, Melta.');hide_if_missing(x,'r74-ba-moritat-two-inferno-legion',LEG)

# ---------- Sanguinary High Priest Consul ----------
priest=byid(cr,'r25-consul-ix-sanguinary-high-priest-consul')
if priest is not None:
    set_points(priest,45);wipe(priest,'rules')
    add_rule(priest,'r74-ba-priest-support','Legion Support Officer','A Sanguinary High Priest is a Legion Support Officer and follows the normal restrictions of that rule.')
    add_rule(priest,'r74-ba-priest-apothecarion','Apothecarion','A Sanguinary High Priest counts as an Apothecary for all rules and wargear restrictions.')
    add_rule(priest,'r74-ba-priest-chosen','Sanguinius’ Chosen','The Sanguinary High Priest and any Blood Angels unit he has joined have the Furious Charge special rule.')
    locked_gear(priest,'priest-narthecium','Narthecium');locked_gear(priest,'priest-reductor','Reductor')
    hide_if_missing(priest,'r74-ba-priest-legion',LEG)

# ---------- Imported BA entries: presentation and model profiles ----------
removed_sources=0;profiles_moved=0
for key,u in U.items():
    removed_sources+=remove_source_rules(u)
    # BA entries are only available with Legion IX, except Sanguinary Guard/Azkaellon which become retinue-only below.
    if key not in ('guard','azk'):unit_gate(u)

# Move squad profiles to the actual total-model counter. Fix Grav Chariots by creating the missing 1-3 model counter.
for key in ('dawn','pal','tears','ofanim','guard'):
    u=U[key];ps=u.find(C('profiles'));models=direct_models(u)
    if ps is not None and models:
        dest=ensure(models[0],'profiles')
        for p in list(ps):dest.append(p);profiles_moved+=1
        u.remove(ps)
# Grav: source importer had no model counter, so it was impossible to select 2-3.
grav=U['grav'];ps=grav.find(C('profiles'));set_points(grav,0)
gm=add_entry(grav,'r74-ba-grav-models','Grav Chariots',65,'model',1,1,3)
if ps is not None:
    dest=ensure(gm,'profiles');[dest.append(p) for p in list(ps)];profiles_moved+=len(dest);grav.remove(ps)
# Named characters/Primarch: locked real model child prevents New Recruit from displaying the statline as "Source Entry".
for key in ('ral','zephon','crohne','azk','amit','sang'):
    u=U[key];ps=u.find(C('profiles'))
    if ps is None or len(ps)==0:continue
    m=add_entry(u,f'r74-ba-{key}-model',u.get('name'),0,'model',1,1,1);dest=ensure(m,'profiles')
    for p in list(ps):dest.append(p);profiles_moved+=1
    u.remove(ps)

# Common actual rule text.
COMMON={
 'Legiones Astartes (Blood Angels)':'This unit belongs to the IX Legion. It is affected by Blood Angels Legion rules and effects that refer to Legiones Astartes (Blood Angels).',
 'Independent Character':'Uses the normal ProHammer Independent Character rules.',
 'Master of the Legion':'This model has Master of the Legion and counts toward all normal Master of the Legion restrictions.',
 'Hammer of Wrath':'Uses the normal ProHammer Hammer of Wrath special rule.',
 'Stubborn':'Uses the normal ProHammer Stubborn special rule.',
 'Counter-Attack':'Uses the normal ProHammer Counter-Attack special rule.',
 'Preferred Enemy (Characters)':'Uses Preferred Enemy against Characters under the normal ProHammer Preferred Enemy rules.',
 'Fearless':'Uses the normal ProHammer Fearless special rule.',
 'Furious Charge':'Uses the normal ProHammer Furious Charge special rule.',
 'Feel No Pain (4+)':'This model has Feel No Pain (4+).',
 'Primarch':'Sanguinius uses the universal Primarch rules presented in Forces of the Legions.'}
def rules(u,slug,names):
    for n in names:add_rule(u,f'r74-ba-{slug}-rule-{re.sub("[^a-z0-9]+","-",n.lower()).strip("-")}',n,COMMON[n])

# ---------- Dawnbreakers ----------
dawn=U['dawn']; dm=direct_models(dawn)[0]; set_points(dawn,35);set_points(dm,35);dm.set('defaultAmount','5')
# confirm 5-10
for c in dm.findall('./'+C('constraints')+'/'+C('constraint')):
    if c.get('type')=='min':c.set('value','5')
    if c.get('type')=='max':c.set('value','10')
rules(dawn,'dawn',['Legiones Astartes (Blood Angels)','Hammer of Wrath'])
locked_gear(dawn,'dawn-armour','Artificer Armour');locked_gear(dawn,'dawn-jump','Jump Pack')
sp=locked_gear(dawn,'dawn-spear','Falling-star Spear','Two-Handed Power Weapon. Attacks are resolved at +1 Strength.')
gd=locked_gear(dawn,'dawn-discharge','Grenade Discharger');add_ranged(gd,'r74-ba-dawn-frag','Frag Grenade','12"','3','6','Assault 1, Blast');add_ranged(gd,'r74-ba-dawn-krak','Krak Grenade','12"','6','4','Assault 1')
locked_gear(dawn,'dawn-frag-grenades','Frag grenades')
opts=next((g for g in dawn.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')) if g.get('id')==IDS['dawn']+'-options'),None)
if opts is not None:
    eq=next((e for e in opts.iter(C('selectionEntry')) if 'equinox' in (e.get('name') or '').lower()),None)
    if eq is not None:
        wipe(eq,'rules');add_rule(eq,'r74-ba-equinox-rule','Equinox Blades','Count as a pair of Power Weapons. This replaces that model’s Falling-star Spear.');dynamic_max(eq,dm.get('id'),'r74-ba-dawn-equinox')
    for e in opts.iter(C('selectionEntry')):
        n=(e.get('name') or '').lower()
        if 'krak grenades' in n:scaled_toggle_existing(e,2,dm.get('id'),'r74-ba-dawn-krak')
        if 'melta bombs' in n:scaled_toggle_existing(e,5,dm.get('id'),'r74-ba-dawn-melta')
clone_armoury_group(dawn,'dawn-champ','Dawnbreaker Champion — Armoury (maximum 50 points)')

# ---------- Crimson Paladins ----------
pal=U['pal'];pm=direct_models(pal)[0];set_points(pal,25);set_points(pm,45);pm.set('defaultAmount','3')
for c in pm.findall('./'+C('constraints')+'/'+C('constraint')):
    if c.get('type')=='min':c.set('value','3')
    if c.get('type')=='max':c.set('value','5')
rules(pal,'pal',['Legiones Astartes (Blood Angels)','Stubborn'])
add_rule(pal,'r74-ba-pal-rule-blood','The Blood is Forever','At the beginning of each Assault phase, if the number of enemy models engaged in the same combat is greater than the number of models in this unit, the Crimson Paladins gain Feel No Pain (5+) until the end of that Assault phase. If the enemy outnumbers the unit by at least two models to one, they instead gain Feel No Pain (4+).')
locked_gear(pal,'pal-cata','Cataphractii Terminator Armour');locked_gear(pal,'pal-power','Power weapon');locked_gear(pal,'pal-shield','Coriolis Shield','Grants a 3+ Invulnerable Save against close-combat attacks. Against all other attacks use the model’s normal saves.')
popts=next((g for g in pal.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')) if g.get('id')==IDS['pal']+'-options'),None)
if popts is not None:
    melee=[e for e in list(popts.findall('./'+C('selectionEntries')+'/'+C('selectionEntry'))) if (e.get('name') or '').lower() in ('power fist','thunder hammer')]
    mg=group(pal,'r74-ba-pal-melee','Replace Power weapon');dynamic_max(mg,pm.get('id'),'r74-ba-pal-melee');move_into_group(mg,melee)
    heavy=[e for e in list(popts.findall('./'+C('selectionEntries')+'/'+C('selectionEntry'))) if any(x in (e.get('name') or '').lower() for x in ('heavy flamer','assault cannon','plasma blaster'))]
    hg=group(pal,'r74-ba-pal-heavy','One Crimson Paladin may replace Coriolis Shield',maxv=1);move_into_group(hg,heavy)
# Transport choices.
dtg=group(pal,'r74-ba-pal-transport','Dedicated Transport',maxv=1)
entry_link(dtg,'r74-ba-pal-dreadclaw','Dreadclaw Drop Pod','transport-dreadclaw')
for tid,label,pfx in (('hs-land-raider','Legion Land Raider','lr'),('hs-spartan','Legion Spartan Assault Tank','sp')):
    src=byid(cr,tid)
    if src is not None:ensure(dtg,'selectionEntries').append(clone_entry(src,f'r74-ba-pal-{pfx}-',label))

# ---------- Angel's Tears ----------
tears=U['tears'];tm=direct_models(tears)[0];set_points(tears,60);set_points(tm,30);tm.set('defaultAmount','5')
for c in tm.findall('./'+C('constraints')+'/'+C('constraint')):
    if c.get('type')=='min':c.set('value','5')
    if c.get('type')=='max':c.set('value','10')
rules(tears,'tears',['Legiones Astartes (Blood Angels)','Counter-Attack'])
add_rule(tears,'r74-ba-tears-dual','Dual Pistols','A model with this rule may fire both of its Pistol weapons during the Shooting phase. Both pistols must fire at the same target.')
add_rule(tears,'r74-ba-tears-cadre','Destroyer Cadre','An Angel’s Tears Squad may normally only be joined by a Moritat. Dominion Zephon is an exception to this rule.')
for s,n in [('armour','Power Armour'),('jump','Jump Pack'),('serp','Two Volkite Serpentas'),('chain','Chainsword'),('frag','Frag grenades'),('rad','Rad grenades')]:locked_gear(tears,'tears-'+s,n)
topts=next((g for g in tears.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')) if g.get('id')==IDS['tears']+'-options'),None)
if topts is not None:
    direct=list(topts.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')))
    specials=[e for e in direct if any(x in (e.get('name') or '').lower() for x in ('rotor cannon','heavy flamer','angel\'s tears grenade launcher','assault cannon with suspensor'))]
    sg=group(tears,'r74-ba-tears-special','Special Weapons — one per five models')
    cid='r74-ba-tears-special-max';constraint(sg,cid,'max',1,child=True)
    mod=ET.SubElement(ensure(sg,'modifiers'),C('modifier'),{'id':'r74-ba-tears-special-at10','type':'increment','value':'1','field':cid});count_condition(mod,'atLeast',10,tm.get('id'))
    move_into_group(sg,specials)
    gl=next((e for e in specials if 'grenade launcher' in (e.get('name') or '').lower()),None)
    if gl is not None:add_ranged(gl,'r74-ba-tears-gl-profile','Angel’s Tears Grenade Launcher','24"','4','4','Assault 3, Fleshbane, Rad-phage')
    arch=[e for e in direct if (e.get('name') or '').lower() in ('rending weapon','power weapon','power fist')]
    ag=group(tears,'r74-ba-tears-arch','Arch-Erelim — replace Chainsword',maxv=1);move_into_group(ag,arch)
    for e in direct:
        n=(e.get('name') or '').lower()
        if 'krak grenades' in n:scaled_toggle_existing(e,2,tm.get('id'),'r74-ba-tears-krak')
        if 'melta bombs' in n:scaled_toggle_existing(e,5,tm.get('id'),'r74-ba-tears-melta')
clone_armoury_group(tears,'tears-arch-arm','Arch-Erelim — Armoury (maximum 50 points)')

# ---------- Ofanim ----------
of=U['ofanim'];om=direct_models(of)[0];set_points(of,0);set_points(om,50);om.set('defaultAmount','3')
for c in om.findall('./'+C('constraints')+'/'+C('constraint')):
    if c.get('type')=='min':c.set('value','3')
    if c.get('type')=='max':c.set('value','5')
rules(of,'ofanim',['Legiones Astartes (Blood Angels)','Preferred Enemy (Characters)'])
locked_gear(of,'ofanim-armour','Artificer Armour');locked_gear(of,'ofanim-blade','Blade of Judgement','Two-Handed Power Weapon. Attacks are resolved at +2 Strength. A natural To Wound roll of 6 inflicts a Massive Wound (D3) instead of a normal Wound.');locked_gear(of,'ofanim-bolt','Bolt pistol');locked_gear(of,'ofanim-shield','Combat Shield');locked_gear(of,'ofanim-frag','Frag grenades')
oopts=next((g for g in of.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')) if g.get('id')==IDS['ofanim']+'-options'),None)
if oopts is not None:
    for e in oopts.iter(C('selectionEntry')):
        n=(e.get('name') or '').lower()
        if 'krak grenades' in n:scaled_toggle_existing(e,2,om.get('id'),'r74-ba-ofanim-krak')
        if 'melta bombs' in n:scaled_toggle_existing(e,5,om.get('id'),'r74-ba-ofanim-melta')
jp=add_entry(of,'r74-ba-ofanim-jump','Jump Packs (+15 pts/model)',0);scaled_toggle_existing(jp,15,om.get('id'),'r74-ba-ofanim-jump');add_rule(jp,'r74-ba-ofanim-jump-rule','Jump Packs','The entire squad is equipped with Jump Packs and becomes Jump Infantry. Every model must take the upgrade.')

# ---------- Grav Chariots ----------
rules(grav,'grav',['Legiones Astartes (Blood Angels)'])
add_rule(grav,'r74-ba-grav-engines','Grav Engines','Grav Chariots follow the normal ProHammer Jetbike rules. A Grav Chariot may fire both its Twin-linked Bolters and its mounted Heavy Bolter, Multi-Melta or Assault Cannon in the same Shooting phase. The mounted weapon may be fired after the Grav Chariot moves.')
locked_gear(grav,'grav-bolters','Twin-linked Bolters');locked_gear(grav,'grav-heavy','Heavy Bolter');locked_gear(grav,'grav-pistol','Bolt pistol')
gopts=next((g for g in grav.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')) if g.get('id')==IDS['grav']+'-options'),None)
if gopts is not None:dynamic_max(gopts,gm.get('id'),'r74-ba-grav-weapons')

# ---------- Sanguinary Guard ----------
guard=U['guard'];sm=direct_models(guard)[0];set_points(guard,10);set_points(sm,55);sm.set('defaultAmount','3')
for c in sm.findall('./'+C('constraints')+'/'+C('constraint')):
    if c.get('type')=='min':c.set('value','3')
    if c.get('type')=='max':c.set('value','6')
guard.set('hidden','true') # retinue only; playable copies are inserted into eligible characters below.
rules(guard,'guard',['Legiones Astartes (Blood Angels)','Fearless'])
add_rule(guard,'r74-ba-guard-servants','Servants of the Great Angel','A Sanguinary Guard Squad may only be selected as the retinue of a Blood Angels Praetor, Raldoron or Sanguinius. It occupies no separate Force Organisation slot. The character must begin the battle joined to the Sanguinary Guard but may leave normally later.')
locked_gear(guard,'guard-armour','Artificer Armour');locked_gear(guard,'guard-jump','Sanguine-pattern Jump Pack','Follows all normal ProHammer Jump Pack rules and grants the wearer a 5+ Invulnerable Save.');ag=locked_gear(guard,'guard-angelus','Angelus Boltgun');add_ranged(ag,'r74-ba-angelus-profile','Angelus Boltgun','12"','4','5','Assault 2, Twin-linked (12” Storm Bolter)');locked_gear(guard,'guard-mask','Death Mask','Uses the Blood Angels Death Mask rule.');locked_gear(guard,'guard-perdition','Perdition Weapon','Counts as a Power Weapon. A natural To Wound roll of 6 inflicts a Massive Wound (D3) instead of a normal Wound.');locked_gear(guard,'guard-frag','Frag grenades')
sopts=next((g for g in guard.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')) if g.get('id')==IDS['guard']+'-options'),None)
if sopts is not None:
    infer=next((e for e in sopts.iter(C('selectionEntry')) if (e.get('name') or '').lower()=='inferno pistol'),None)
    if infer is not None:
        dynamic_max(infer,sm.get('id'),'r74-ba-guard-inferno');add_ranged(infer,'r74-ba-guard-inferno-profile','Inferno Pistol','6"','8','1','Pistol, Melta')
    for e in sopts.iter(C('selectionEntry')):
        n=(e.get('name') or '').lower()
        if 'krak grenades' in n:scaled_toggle_existing(e,2,sm.get('id'),'r74-ba-guard-krak')
        if 'melta bombs' in n:scaled_toggle_existing(e,5,sm.get('id'),'r74-ba-guard-melta')
    oldaz=next((e for e in list(sopts.iter(C('selectionEntry'))) if (e.get('name') or '').lower()=='azkaellon'),None)
    if oldaz is not None:
        # Enrich the squad upgrade itself rather than exposing Azkaellon as a separate Elites choice.
        oldaz.set('type','upgrade');set_points(oldaz,35);wipe(oldaz,'rules');add_rule(oldaz,'r74-ba-azk-up-master','Master of the Seraphim','A Sanguinary Guard Squad containing Azkaellon may deploy using Deep Strike even if the mission does not normally permit it. If selected as a character’s retinue, that character must also be capable of Deep Striking or the unit deploys normally.');add_rule(oldaz,'r74-ba-azk-up-glaive','Glaive Encarmine','Two-Handed, Master-crafted Power Weapon. Attacks are resolved at Strength 6.')
        # Copy Azkaellon's imported model profile onto the upgrade.
        azmodel=next((m for m in direct_models(U['azk']) if m.get('id')=='r74-ba-azk-model'),None)
        if azmodel is not None:
            ps=azmodel.find(C('profiles'))
            if ps is not None:
                dest=ensure(oldaz,'profiles');[dest.append(deepcopy(p)) for p in list(ps)]
        for nm in ('Artificer Armour','Sanguine-pattern Jump Pack','Death Mask','Glaive Encarmine','Angelus Boltgun','Frag grenades'):add_rule(oldaz,'r74-ba-azk-up-'+re.sub('[^a-z0-9]+','-',nm.lower()).strip('-'),nm,'Fixed Azkaellon wargear.')
# Hide standalone Azkaellon imported entry.
U['azk'].set('hidden','true')

# ---------- Named characters ----------
ral=U['ral'];rules(ral,'ral',['Legiones Astartes (Blood Angels)','Independent Character','Master of the Legion'])
add_rule(ral,'r74-ba-ral-first','First Captain of the Blood Angels','Raldoron and any Blood Angels unit he has joined may re-roll failed Morale tests. Friendly Blood Angels units with a model within 6 inches of Raldoron may use his Leadership when taking Morale or Pinning tests.')
add_rule(ral,'r74-ba-ral-blooded','The Blooded','At the beginning of each Assault phase, nominate one enemy Independent Character or squad leader in base contact with Raldoron. Until the end of that phase, Raldoron may re-roll failed To Hit rolls made against that model.')
for s,n,t in [('arm','Artificer Armour',None),('halo','Iron Halo',None),('blade','Encarmine Warblade','Power Weapon; attacks are resolved at +1 Strength.'),('combi','Combi-flamer',None),('frag','Frag grenades',None)]:locked_gear(ral,'ral-'+s,n,t)

ze=U['zephon'];rules(ze,'zephon',['Legiones Astartes (Blood Angels)','Independent Character'])
add_rule(ze,'r74-ba-zephon-dual','Dual Pistols','Zephon may fire both Lament and Grief during the Shooting phase. Both weapons must fire at the same target.')
add_rule(ze,'r74-ba-zephon-exarch','Exarch of the High Host','Zephon may join an Angel’s Tears Squad or Legion Destroyer Squad despite Destroyer Cadre restrictions. He may select one Angel’s Tears Squad as his retinue; it occupies no separate Force Organisation slot.')
for s,n,t in [('arm','Artificer Armour',None),('field','Refractor Field',None),('jump','Jump Pack',None),('lament','Lament','A Volkite Serpenta; use the project Volkite Serpenta profile.'),('grief','Grief','A Volkite Serpenta; use the project Volkite Serpenta profile.'),('spirit','Spiritum Sanguis','Two-Handed, Master-crafted Power Weapon; attacks are resolved at +1 Strength. If Zephon begins an Assault phase in base contact with two or more enemy models, he gains +1 Attack for that phase.'),('frag','Frag grenades',None)]:locked_gear(ze,'zephon-'+s,n,t)

crh=U['crohne'];rules(crh,'crohne',['Legiones Astartes (Blood Angels)','Independent Character','Feel No Pain (4+)'])
for s,n,t in [('arm','Artificer Armour',None),('field','Refractor Field',None),('axe','Saiphan Shard-Axe','Master-crafted Power Weapon; attacks are resolved at +1 Strength.'),('flamer','Hand Flamer',None),('frag','Frag grenades',None)]:locked_gear(crh,'crohne-'+s,n,t)

am=U['amit'];rules(am,'amit',['Legiones Astartes (Blood Angels)','Independent Character','Master of the Legion','Furious Charge'])
for s,n in [('arm','Artificer Armour'),('halo','Iron Halo'),('power','Power weapon'),('rend','Rending Weapon'),('frag','Frag grenades')]:locked_gear(am,'amit-'+s,n)

# Character grenade options remain imported; no generic armoury is added to named characters.
# Functional retinues.
cmd=find_entry_name('Legion Command Squad'); tcmd=find_entry_name('Legion Terminator Command Squad'); honour=find_entry_name('Legion Honour Guard Squad')
add_retinue_group(ral,'ral',[('Legion Command Squad',cmd,'cmd'),('Legion Terminator Command Squad',tcmd,'tcmd'),('Sanguinary Guard Squad',guard,'guard')])
add_retinue_group(ze,'zephon',[('Angel’s Tears Squad',tears,'tears')])
add_retinue_group(crh,'crohne',[('Legion Command Squad',cmd,'cmd')])
add_retinue_group(am,'amit',[('Legion Command Squad',cmd,'cmd')])

# Blood Angels Praetor may take Sanguinary Guard in its existing retinue selector; otherwise make a dedicated one.
pra=byid(cr,'hq-praetor')
if pra is not None:
    rg=next((g for g in pra.iter(C('selectionEntryGroup')) if 'retinue' in (g.get('name') or '').lower()),None)
    if rg is None:rg=group(pra,'r74-ba-pra-retinue','Command Retinue',maxv=1)
    sgclone=clone_entry(guard,'r74-ba-pra-guard-','Sanguinary Guard Squad');sgclone.set('hidden','true');show_if_all(sgclone,'r74-ba-pra-guard-show',[('atLeast',1,'roster',LEG)]);ensure(rg,'selectionEntries').append(sgclone)

# ---------- Sanguinius ----------
sa=U['sang'];rules(sa,'sang',['Primarch','Legiones Astartes (Blood Angels)'])
add_rule(sa,'r74-ba-sang-charge','Angelic Charge','During an Assault phase in which Sanguinius charged, increase his Strength and Attacks characteristics by +1 for that Assault phase.')
add_rule(sa,'r74-ba-sang-sire','Sire of the Blood Angels','Friendly Blood Angels units with at least one model within 12 inches of Sanguinius may re-roll failed Morale and Pinning tests. The second result must be accepted.')
add_rule(sa,'r74-ba-sang-descends','The Angel Descends','When Sanguinius enters play using Deep Strike, he does not scatter. If he charges during the same turn, he receives the normal +1 Attack for charging and normal benefits of any Assault Grenades carried; this overrides the normal ProHammer restriction on charging after Deep Strike.')
locked_gear(sa,'sang-regalia','Regalia Resplendent','Counts as Primarch Armour.')
inf=locked_gear(sa,'sang-infernus','Infernus');add_ranged(inf,'r74-ba-sang-infernus-profile','Infernus','18"','8','1','Assault 2, Melta, One Use')
locked_gear(sa,'sang-wings','Great Wings','Sanguinius is Jump Infantry and follows normal ProHammer Jump Infantry rules. This movement ability may never be lost, disabled or destroyed as the result of damage to wargear.')
locked_gear(sa,'sang-frag','Frag Grenades')
wg=group(sa,'r74-ba-sang-weapon','Primary Weapon',1,1)
b=add_entry(wg,'r74-ba-sang-blade','Blade Encarmine',0);add_rule(b,'r74-ba-sang-blade-rule','Blade Encarmine','Master-crafted Power Weapon. Attacks are resolved at +1 Strength and have Shred and Rampage.')
s=add_entry(wg,'r74-ba-sang-spear','Spear of Telesto',0);add_rule(s,'r74-ba-sang-spear-rule','Spear of Telesto','Master-crafted, Two-Handed Power Weapon. Attacks are resolved at +3 Strength and have Lance.')
# Loyalist only.
hide_if_missing(sa,'r74-ba-sang-loyalist','allegiance-loyalist')
# Primarch retinue: Honour Guard or Sanguinary Guard. Honour Guard gains optional whole-squad Jump Packs at +10/model.
srg=add_retinue_group(sa,'sang',[('Legion Honour Guard Squad',honour,'honour'),('Sanguinary Guard Squad',guard,'guard')])
for x in srg.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')):
    if 'honour guard' in (x.get('name') or '').lower():
        mids=direct_models(x)
        if mids:
            j=add_entry(x,'r74-ba-sang-honour-jump','Jump Packs (+10 pts/model)',0);scaled_toggle_existing(j,10,mids[0].get('id'),'r74-ba-sang-honour-jump');add_rule(j,'r74-ba-sang-honour-jump-rule','Jump Packs','Every model in Sanguinius’ Legion Honour Guard receives a Jump Pack. Every model must take this upgrade.')

# ---------- Rites of War ----------
rev=byid(cr,REV);sor=byid(cr,SOR)
if rev is None or sor is None:raise RuntimeError('Missing Blood Angels Rites')
wipe(rev,'rules');wipe(sor,'rules')
add_rule(rev,'r74-ba-rev-host','Host of Angels','Legion Veteran Squads equipped with Jump Packs may be selected as Troops and may fulfil compulsory Troops selections. Legion Assault Squads remain Troops normally.')
add_rule(rev,'r74-ba-rev-revealed','The Day is Revealed','Blood Angels units composed entirely of Jump Infantry may deploy using Deep Strike even if the mission would not normally permit it. All Jump Infantry units placed in Reserve using this Rite must enter using Deep Strike.')
add_rule(rev,'r74-ba-rev-wings','On Wings of Fire','At the beginning of the second Blood Angels player turn, all Blood Angels Jump Infantry units currently in Reserve become available automatically. No Reserve rolls are made and they must enter that turn using Deep Strike.')
add_rule(rev,'r74-ba-rev-shock','Angelic Shock Assault','A Blood Angels Jump Infantry unit which charges in the same turn it arrived using Deep Strike receives the normal +1 Attack bonus for charging and normal benefits of Assault Grenades. This overrides the normal ProHammer restriction on charging after Deep Strike.')
add_rule(rev,'r74-ba-rev-limits','Day of Revelation — Limitations','The Warlord must have a Jump Pack. At least half of the Detachment’s non-Vehicle units, rounding up, must consist entirely of models with Jump Packs. Every Jump Infantry unit must begin in Reserve and enter by Deep Strike. Maximum one Heavy Support choice. No Fortification. The ratio and deployment-state requirements remain player-checked because New Recruit cannot determine battlefield deployment state or reliably express the required roster ratio.')
add_rule(sor,'r74-ba-sor-bitter','The Bitter End','When a non-Vehicle Blood Angels unit is reduced to half or fewer of the models with which it began the battle, it gains Stubborn and Feel No Pain (6+) for the rest of the battle. If it already has Feel No Pain, improve it one step, to a maximum of 4+.')
add_rule(sor,'r74-ba-sor-fury','Sorrow Becomes Fury','A Blood Angels unit affected by The Bitter End gains +1 to its combat-resolution score whenever it wins a close combat. This is not cumulative.')
add_rule(sor,'r74-ba-sor-death','No Death Unremembered','Whenever a Blood Angels unit affected by The Bitter End is destroyed, every friendly non-Vehicle Blood Angels unit with at least one model within 6 inches may re-roll its next failed Morale or Pinning test before the end of the following Blood Angels player turn.')
add_rule(sor,'r74-ba-sor-hold','Hold Until the Last','Legion Tactical Squads and Legion Breacher Siege Squads may re-roll failed Pinning tests while at least one model is within 6 inches of an Objective.')
add_rule(sor,'r74-ba-sor-limits','Day of Sorrows — Limitations','The compulsory Troops choices must be selected from Legion Tactical Squads, Legion Assault Squads or Legion Breacher Siege Squads. Units affected by The Bitter End may not voluntarily withdraw from close combat; if they win and the enemy retreats, they must Pursue whenever normally permitted. No Fortification.')
# Rite entries themselves are Legion IX only.
hide_if_missing(rev,'r74-ba-rev-legion',LEG);hide_if_missing(sor,'r74-ba-sor-legion',LEG)
# Revelation Veteran Troops clone with mandatory Jump Packs.
vet=byid(cr,'veteran-unit')
if vet is None:raise RuntimeError('Missing veteran-unit')
rv=clone_entry(vet,'r74-ba-rev-vet-','Legion Veteran Squad (Jump Packs) — Day of Revelation');set_primary_category(rv,'cat-troops','Troops');rv.set('hidden','true');show_if_all(rv,'r74-ba-rev-vet-show',[('atLeast',1,'roster',LEG),('atLeast',1,'roster',REV)])
# Force Jump Pack option on clone. If unavailable, create exact current +15/model option from the Army List.
jp_candidates=[e for e in rv.iter(C('selectionEntry')) if 'jump pack' in (e.get('name') or '').lower()]
if jp_candidates:
    j=jp_candidates[0];j.set('defaultAmount','1');
    if not any(c.get('type')=='min' for c in j.findall('./'+C('constraints')+'/'+C('constraint'))):constraint(j,'r74-ba-rev-vet-jump-min','min',1)
    else:
        for c in j.findall('./'+C('constraints')+'/'+C('constraint')):
            if c.get('type')=='min':c.set('value','1')
else:
    mids=direct_models(rv)
    if not mids:raise RuntimeError('Revelation Veteran clone has no model counter')
    j=add_entry(rv,'r74-ba-rev-vet-jump','Jump Packs (+15 pts/model)',0,'upgrade',1,1,1);scaled_toggle_existing(j,15,mids[0].get('id'),'r74-ba-rev-vet-jump')
# Add top-level clone.
ensure(cr,'selectionEntries').append(rv)
# Mechanical compulsory-Troops categories.
REV_CAT='r74-ba-cat-revelation-comp'; SOR_CAT='r74-ba-cat-sorrows-comp'
gst_hidden_requirement(REV_CAT,'Day of Revelation — compulsory Assault/Veteran Troops',REV,2)
gst_hidden_requirement(SOR_CAT,'Day of Sorrows — compulsory Tactical/Assault/Breacher Troops',SOR,2)
ass=byid(cr,'assault-unit');tac=byid(cr,'tactical-unit');bre=byid(cr,'breacher-unit')
if ass is not None:add_hidden_category(ass,'r74-ba-ass-revcat',REV_CAT,'Revelation compulsory Troops');add_hidden_category(ass,'r74-ba-ass-sorcat',SOR_CAT,'Sorrows compulsory Troops')
if tac is not None:add_hidden_category(tac,'r74-ba-tac-sorcat',SOR_CAT,'Sorrows compulsory Troops')
if bre is not None:add_hidden_category(bre,'r74-ba-bre-sorcat',SOR_CAT,'Sorrows compulsory Troops')
add_hidden_category(rv,'r74-ba-rv-revcat',REV_CAT,'Revelation compulsory Troops')
# Max one Heavy Support in Revelation.
gst_set_limit('fl-heavy','fl-heavy-max',1,REV,'r74-ba-rev-heavy-max')

# ---------- Ensure actual BA armoury links reach newly cloned/special armoury groups ----------
# Add Inferno/Blade to BA unique Champion armouries created above; they are already Legion-specific so no gate required.
for g in cr.iter(C('selectionEntryGroup')):
    if (g.get('id') or '').startswith('r74-ba-') and 'armoury' in (g.get('name') or '').lower():
        if not any(x.get('targetId')==inferno.get('id') for x in g.findall('./'+C('entryLinks')+'/'+C('entryLink'))):entry_link(g,'r74-ba-'+(g.get('id') or '')[-35:]+'-inferno','Inferno Pistol',inferno.get('id'))
        if not any(x.get('targetId')==blade.get('id') for x in g.findall('./'+C('entryLinks')+'/'+C('entryLink'))):entry_link(g,'r74-ba-'+(g.get('id') or '')[-35:]+'-blade','Blade of Perdition',blade.get('id'))

# ---------- Validation ----------
# Canonical BA entries: no Source Entry dumps and no profiles directly on top-level unit shells.
for key,u in U.items():
    if any((r.get('name') or '').lower().startswith('source entry') for r in u.findall('./'+C('rules')+'/'+C('rule'))):raise RuntimeError('Source Entry rule remains on '+key)
    if u.find(C('profiles')) is not None and len(u.find(C('profiles'))):raise RuntimeError('Top-level profile remains on '+key)
# Required actual rules.
required={
 'dawn':['Legiones Astartes (Blood Angels)','Hammer of Wrath'], 'pal':['Legiones Astartes (Blood Angels)','Stubborn','The Blood is Forever'], 'tears':['Legiones Astartes (Blood Angels)','Counter-Attack','Dual Pistols','Destroyer Cadre'],
 'ofanim':['Legiones Astartes (Blood Angels)','Preferred Enemy (Characters)'], 'grav':['Legiones Astartes (Blood Angels)','Grav Engines'], 'guard':['Legiones Astartes (Blood Angels)','Fearless','Servants of the Great Angel'],
 'ral':['Legiones Astartes (Blood Angels)','Independent Character','Master of the Legion','First Captain of the Blood Angels','The Blooded'], 'zephon':['Legiones Astartes (Blood Angels)','Independent Character','Dual Pistols','Exarch of the High Host'], 'crohne':['Legiones Astartes (Blood Angels)','Independent Character','Feel No Pain (4+)'], 'amit':['Legiones Astartes (Blood Angels)','Independent Character','Master of the Legion','Furious Charge'], 'sang':['Primarch','Legiones Astartes (Blood Angels)','Angelic Charge','Sire of the Blood Angels','The Angel Descends']}
for key,names in required.items():
    have={r.get('name') for r in U[key].findall('./'+C('rules')+'/'+C('rule'))}
    missing=set(names)-have
    if missing:raise RuntimeError(f'{key} missing actual rules {missing}')
# Critical squad sizes and Grav 1-3.
checks={'dawn':(5,10,35),'pal':(3,5,45),'tears':(5,10,30),'ofanim':(3,5,50),'guard':(3,6,55)}
for key,(mn,mx,cost) in checks.items():
    m=direct_models(U[key])[0];vals={c.get('type'):float(c.get('value')) for c in m.findall('./'+C('constraints')+'/'+C('constraint'))};pc=float(m.find('./'+C('costs')+'/'+C('cost')).get('value'))
    if vals.get('min')!=mn or vals.get('max')!=mx or pc!=cost:raise RuntimeError(f'{key} size/cost wrong {vals} {pc}')
gvals={c.get('type'):float(c.get('value')) for c in gm.findall('./'+C('constraints')+'/'+C('constraint'))}
if gvals.get('min')!=1 or gvals.get('max')!=3:raise RuntimeError('Grav Chariot must be 1-3')
if U['guard'].get('hidden')!='true' or U['azk'].get('hidden')!='true':raise RuntimeError('Sanguinary Guard/Azkaellon source shells must be retinue/upgrade only')
# Rite structures.
if byid(cr,'r74-ba-rev-vet-veteran-unit') is None:raise RuntimeError('Revelation Veteran Troops clone missing')
for cid in (REV_CAT,SOR_CAT):
    if byid(gr,cid) is None:raise RuntimeError('Missing Rite compulsory category '+cid)
# Duplicate IDs.
for root,label in ((cr,'catalogue'),(gr,'game system')):
    seen=set();dup=[]
    for e in root.iter():
        i=e.get('id')
        if not i:continue
        if i in seen:dup.append(i)
        seen.add(i)
    if dup:raise RuntimeError(f'Duplicate IDs in {label}: {dup[:20]}')

# Revisions force New Recruit refresh.
cr.set('revision','74');cr.set('gameSystemRevision','42');gr.set('revision','42')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat':e.set('dataRevision','74')
    elif e.get('filePath')=='Prohammer 30k.gst':e.set('dataRevision','42')

ET.indent(ct,space='  ');ET.indent(gt,space='  ');ET.indent(it,space='  ')
ct.write(CAT,encoding='utf-8',xml_declaration=True);gt.write(GST,encoding='utf-8',xml_declaration=True);it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT);ET.parse(GST);ET.parse(IDX)
OUT.write_text(f'''Revision 74 — Blood Angels full New Recruit implementation\nCatalogue revision: 74\nGame-system revision: 42\n\nPresentation\n- Removed {removed_sources} canonical Blood Angels Source Entry / aggregate dump rules.\n- Moved {profiles_moved} model profiles off top-level unit shells onto real model selections, using the Night Lords Rev73 presentation fix as the permanent standard.\n- Added individually named actual rules and fixed wargear for the Blood Angels units, characters and Sanguinius.\n\nArmy rules and armoury\n- Legion selector now exposes Angels of Death, Descent of Angels and Vengeance of a Fallen Angel as separate actual rules.\n- Repaired Death Mask, Inferno Pistol, Blade of Perdition, Over-charged Engines and Furioso-pattern Jump Pack access.\n- Over-charged Engines now attach to the real Legion Rhino rather than Damocles Command Rhino.\n- Moritat receives the two-Inferno-Pistol +20 replacement.\n- Sanguinary High Priest Consul is a functional Centurion branch with Narthecium, Reductor, Legion Support Officer, Apothecarion and Sanguinius' Chosen.\n\nUnique units\n- Dawnbreakers: 5-10, scaling grenades, Equinox replacements, Champion Armoury and weapon rules.\n- Crimson Paladins: 3-5, shared melee-replacement cap, one shield-to-heavy replacement, Coriolis Shield, Blood is Forever and Dedicated Transport.\n- Angel's Tears: 5-10, correct 1-per-5 special-weapon cap, Arch-Erelim weapon block/Armoury, scaling grenades, Dual Pistols and Destroyer Cadre.\n- Ofanim: 3-5, scaling grenades and whole-squad +15/model Jump Pack option.\n- Grav Chariots: repaired from a fixed one-model shell to a true 1-3 model squadron with model-scaled weapon replacements.\n- Sanguinary Guard: 3-6, retinue only, scaling upgrades, Azkaellon as an in-squad +35 upgrade rather than a standalone Elites choice.\n\nCharacters and Primarch\n- Raldoron, Zephon, Crohne and Amit now have real model profiles, fixed wargear, named actual rules and functional retinues.\n- Sanguinius has a real model profile, Loyalist gate, Blade/Spear choice, Infernus profile, Great Wings, Angelic Charge, Sire of the Blood Angels, The Angel Descends, and Honour Guard/Sanguinary Guard retinues.\n\nRites\n- Day of Revelation: functional Jump Veteran Troops clone, compulsory Assault/Jump Veteran requirement, and 0-1 Heavy Support. Deployment/ratio restrictions remain visible where New Recruit cannot reliably infer battlefield state or a half-roster ratio.\n- Day of Sorrows: functional compulsory Tactical/Assault/Breacher requirement; battlefield half-strength/Pursuit effects remain as actual Rite rules.\n\nValidation\n- No canonical Blood Angels Source Entry rules remain.\n- No canonical Blood Angels model profile remains on a top-level unit shell.\n- Critical unit sizes/cost counters, Rite categories, retinue-only entries, duplicate IDs and XML parsing validated.\n''',encoding='utf-8')
print(OUT.read_text())
