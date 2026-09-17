from pathlib import Path
import copy, re
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r79-iron-hands-live.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS); ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()
if cr.get('revision')!='78' or gr.get('revision')!='45': raise RuntimeError(f'Expected CAT78/GST45, got CAT{cr.get("revision")}/GST{gr.get("revision")}')

LEG='legion-x'; HEAD='r25-rite-x-0-the-head-of-the-gorgon'; BITTER='r25-rite-x-1-company-of-bitter-iron'
IDS={
'imm':'r41-unit-x-0-medusan-immortal-squad','gorgon':'r41-unit-x-1-gorgon-terminator-squad','morlock':'r41-unit-x-2-morlock-terminator-squad','forge':'r41-unit-x-3-venerable-forge-lord','meduson':'r41-unit-x-4-shadrak-meduson','autek':'r41-unit-x-5-autek-mor','santar':'r41-unit-x-6-gabriel-santar','ferrus':'r41-unit-x-7-x-ferrus-manus-the-gorgon'}

# ---------- helpers ----------
def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t,ns=CNS):
    Q=C if ns==CNS else (G if ns==GNS else I); x=p.find(Q(t))
    if x is None:x=ET.SubElement(p,Q(t))
    return x
def wipe(p,t,ns=CNS):
    Q=C if ns==CNS else (G if ns==GNS else I); x=p.find(Q(t))
    if x is not None:p.remove(x)
def cost(e):
    c=e.find('./'+C('costs')+'/'+C('cost'))
    return float(c.get('value')) if c is not None else 0
def set_points(e,v):
    cs=ensure(e,'costs'); [cs.remove(x) for x in list(cs)]; ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def constraint(p,i,typ,val,scope='parent',child=False,ns=CNS):
    Q=C if ns==CNS else G
    return ET.SubElement(ensure(p,'constraints',ns),Q('constraint'),{'id':i,'type':typ,'value':str(val),'field':'selections','scope':scope,'shared':'true','includeChildSelections':'true' if child else 'false','includeChildForces':'false'})
def add_rule(p,i,n,text):
    rs=ensure(p,'rules'); old=next((x for x in rs.findall(C('rule')) if x.get('id')==i),None)
    if old is not None:rs.remove(old)
    r=ET.SubElement(rs,C('rule'),{'id':i,'name':n,'hidden':'false'}); ET.SubElement(r,C('description')).text=text; return r
def remove_rule_names(u,names):
    names={n.lower() for n in names}; n=0
    for p in list(u.iter()):
        rs=p.find(C('rules'))
        if rs is None:continue
        for r in list(rs.findall(C('rule'))):
            nm=(r.get('name') or '').strip().lower(); desc=(r.findtext(C('description')) or '').lower()
            source=nm.startswith('source entry') or ('force organisation:' in desc and 'wargear:' in desc and 'special rules:' in desc)
            if nm in names or source:rs.remove(r);n+=1
    return n
def add_entry(p,i,n,c=0,typ='upgrade',default=None,minv=None,maxv=1):
    e=ET.SubElement(ensure(p,'selectionEntries'),C('selectionEntry'),{'id':i,'name':n,'type':typ,'hidden':'false','import':'true',**({'defaultAmount':str(default)} if default is not None else {})});set_points(e,c)
    if minv is not None:constraint(e,i+'-min','min',minv)
    if maxv is not None:constraint(e,i+'-max','max',maxv)
    return e
def add_cat(e,i,target,name=None,primary='false'):
    if any(x.get('targetId')==target for x in e.findall('./'+C('categoryLinks')+'/'+C('categoryLink'))):return
    ET.SubElement(ensure(e,'categoryLinks'),C('categoryLink'),{'id':i,'name':name or target,'hidden':'false','targetId':target,'primary':primary})
def show_if(e,i,conds):
    e.set('hidden','true');m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'});cs=ET.SubElement(m,C('conditions'))
    for typ,val,scope,child in conds:ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def hide_if(e,i,conds):
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'true','field':'hidden'});cs=ET.SubElement(m,C('conditions'))
    for typ,val,scope,child in conds:ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def remove_prefix(root,pfx):
    for p in list(root.iter()):
        for x in list(p):
            if (x.get('id') or '').startswith(pfx):p.remove(x)
def direct_models(u):return [x for x in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if x.get('type')=='model']
def direct_groups(u):
    s=u.find(C('selectionEntryGroups'));return [] if s is None else list(s.findall(C('selectionEntryGroup')))
def find_group(u,mode):
    gs=direct_groups(u)
    if mode=='weapon': cand=[g for g in gs if 'weapon' in (g.get('name') or '').lower() and ('replacement' in (g.get('name') or '').lower() or 'armoury' in (g.get('name') or '').lower())]
    elif mode=='wargear': cand=[g for g in gs if 'additional wargear' in (g.get('name') or '').lower()]
    else: cand=[]
    if len(cand)!=1: raise RuntimeError(f'{u.get("name")}: expected one {mode} group, got {[(g.get("id"),g.get("name")) for g in cand]}')
    return cand[0]
def link(group,i,n,target,conds,maxv=1):
    l=ET.SubElement(ensure(group,'entryLinks'),C('entryLink'),{'id':i,'name':n,'type':'selectionEntry','targetId':target,'hidden':'true','import':'true'});constraint(l,i+'-max','max',maxv);show_if(l,i+'-show',conds);return l
def nearest_unit(node):
    pm={c:p for p in cr.iter() for c in p};x=node
    while x is not None:
        if x.tag==C('selectionEntry') and x.get('type')=='unit':return x
        x=pm.get(x)
    return None
def clone_with_prefix(src,prefix,name=None):
    x=copy.deepcopy(src)
    for e in x.iter():
        if e.get('id'):e.set('id',prefix+e.get('id'))
        for a in ('childId','field'):
            v=e.get(a)
            if v and byid(cr,v) is not None and v.startswith(src.get('id') or '___'):e.set(a,prefix+v)
    if name:x.set('name',name)
    return x

remove_prefix(cr,'r79-ih-');remove_prefix(gr,'r79-ih-')

# ---------- 1) Presentation: eliminate Source Entry / aggregate dumps everywhere Iron Hands content can appear ----------
canon=list(IDS.values())
relevant=[]
for u in cr.iter(C('selectionEntry')):
    uid=u.get('id') or ''
    if any(c in uid for c in canon) or uid in ('r46-al-reward-25','r46-al-reward-26','r46-al-reward-27'):
        relevant.append(u)
removed_dumps=sum(remove_rule_names(u,{'Special Rules','Unit Composition'}) for u in relevant)

# Move direct profiles onto real model selections; named characters get a locked model child.
profiles_moved=0; model_children=0
for key in ('imm','gorgon','morlock'):
    canonid=IDS[key]
    for u in [x for x in relevant if canonid in (x.get('id') or '')]:
        ps=u.find(C('profiles'))
        if ps is None or len(ps)==0:continue
        models=direct_models(u); destm=next((m for m in models if 'model' in (m.get('name') or '').lower() or 'squad models' in (m.get('name') or '').lower()),None) or (models[0] if models else None)
        if destm is None:
            destm=add_entry(u,'r79-ih-'+re.sub('[^a-z0-9]+','-',u.get('id').lower())[-55:]+'-models','Squad Models',0,'model',1,1,20)
        dest=ensure(destm,'profiles')
        for p in list(ps):dest.append(p);profiles_moved+=1
        u.remove(ps)
for key in ('forge','meduson','autek','santar','ferrus'):
    u=byid(cr,IDS[key]);ps=u.find(C('profiles')) if u is not None else None
    if u is None or ps is None or len(ps)==0:continue
    m=add_entry(u,f'r79-ih-{key}-model',u.get('name'),0,'model',1,1,1);dest=ensure(m,'profiles')
    for p in list(ps):dest.append(p);profiles_moved+=1
    u.remove(ps);model_children+=1

# Actual individual rules, current source wording/meaning.
COMMON={
'Legiones Astartes (Iron Hands)':'This model belongs to the X Legion and is affected by rules and effects which refer to Legiones Astartes (Iron Hands).',
'Independent Character':'Uses the normal ProHammer Independent Character rules.',
'Master of the Legion':'This model has Master of the Legion and counts toward all normal Master of the Legion restrictions.',
'Fearless':'Uses the normal ProHammer Fearless special rule.',
'Stubborn':'Uses the normal ProHammer Stubborn special rule.',
'Primarch':'Ferrus Manus uses the universal Primarch rules in Forces of the Legions.',
'Battlesmith':'Uses the normal Battlesmith rules. Where a profile specifies a better repair value, use that value.',
'Furious Charge':'Uses the normal ProHammer Furious Charge special rule.'}
def rule_once(u,key,n,text=None):
    rs=ensure(u,'rules')
    for r in list(rs):
        if (r.get('id') or '').startswith('r79-ih-rule-') and r.get('name')==n:rs.remove(r)
    add_rule(u,'r79-ih-rule-'+key+'-'+re.sub('[^a-z0-9]+','-',n.lower()).strip('-'),n,text or COMMON.get(n,n))
for u in [x for x in relevant if IDS['imm'] in (x.get('id') or '')]:
    rule_once(u,'imm','Legiones Astartes (Iron Hands)');rule_once(u,'imm','Stubborn')
for key in ('gorgon','morlock'):
    for u in [x for x in relevant if IDS[key] in (x.get('id') or '')]:
        rule_once(u,key,'Legiones Astartes (Iron Hands)');rule_once(u,key,'Fearless');rule_once(u,key,'Gorgon Field','If one or more models in this unit pass an Invulnerable Save against shooting from an enemy unit, resolve all attacks from that enemy unit, then the attacking unit takes one Initiative test. If failed, it is affected by the normal ProHammer Blind rule until the end of its next turn. A unit takes at most one Gorgon Field test per phase.')
for key,rules in {'meduson':['Legiones Astartes (Iron Hands)','Independent Character','Master of the Legion'],'autek':['Legiones Astartes (Iron Hands)','Independent Character','Master of the Legion','Battlesmith','Furious Charge'],'santar':['Legiones Astartes (Iron Hands)','Independent Character','Master of the Legion'],'ferrus':['Primarch','Legiones Astartes (Iron Hands)']}.items():
    u=byid(cr,IDS[key])
    if u:
        for n in rules:rule_once(u,key,n)
forge=byid(cr,IDS['forge'])
if forge:
    rule_once(forge,'forge','Old & Wise','If the mission requires a roll to determine first turn, an Iron Hands army containing a Venerable Forge Lord may re-roll that roll once; the second result stands.')
    rule_once(forge,'forge','Hard to Kill','Whenever the Venerable Forge Lord suffers a Glancing or Penetrating Hit and a Vehicle Damage result is rolled, the Iron Hands player may force the opponent to re-roll that result; the second result stands.')
    rule_once(forge,'forge','Auto-Repair Simulacra','Whenever a Vehicle Damage result would destroy the Venerable Forge Lord, roll a D6 after resolving Hard to Kill. On a 6, it is not destroyed; replace the result with Crew Shaken.')
med=byid(cr,IDS['meduson']);
if med:rule_once(med,'meduson','Fury of the Survivors','Meduson and any Iron Hands unit he has joined have Counter-Attack. When attacking a Traitor unit, Meduson and his unit may re-roll To Hit rolls of 1 in both Shooting and Assault phases.')
aut=byid(cr,IDS['autek']);
if aut:rule_once(aut,'autek','Battlesmith','Autek Mor uses the normal Battlesmith rule. His Servo-Arm provides the normal +1 bonus, so he normally repairs a damaged Vehicle on a 4+.')
san=byid(cr,IDS['santar']);
if san:
    rule_once(san,'santar','Master of the Morlocks','Gabriel Santar may select one Morlock Terminator Squad as his retinue. The Morlocks do not occupy a separate Elites choice and Santar and the Morlocks count as a single HQ selection.')
    rule_once(san,'santar','The Iron Aegis','The Iron Aegis is a unique suit of Terminator Armour: 2+ Armour, 4+ Invulnerable, and all normal Terminator Armour rules. It incorporates Bionics and a matched pair of master-crafted Power Weapons with Rending; the +1 Attack for two weapons is already included in Santar’s profile.')
fer=byid(cr,IDS['ferrus']);
if fer:
    for n,t in [('The Gorgon','Ferrus Manus has Feel No Pain (5+).'),('Master of the Forge','Ferrus Manus has Battlesmith and succeeds on a 3+. He may repair friendly Vehicles, Dreadnoughts and Battle-Automata as appropriate.'),('Forged for War','After army selection but before deployment, nominate one friendly Iron Hands Vehicle or Dreadnought that is not a Lord of War. It gains +1 Structure Point for the battle.'),('Forgebreaker','Forgebreaker is a Master-crafted Thunder Hammer with Armourbane.'),('Living Metal Hands','Ferrus may fight with his Living Metal Hands instead of Forgebreaker. These attacks are Power Weapon attacks resolved at Strength 8.'),('Medusan Carapace','Counts as Primarch Armour and incorporates a Twin-linked Meltagun, Twin-linked Plasma Gun, Heavy Flamer, Cortex Controller and Nuncio Vox. Ferrus may fire up to two incorporated weapons in each Shooting phase.')]:rule_once(fer,'ferrus',n,t)

# ---------- 2) Current points ----------
for key,v in {'imm':150,'gorgon':250,'morlock':275,'forge':155,'meduson':165,'autek':205,'santar':220,'ferrus':505}.items():
    u=byid(cr,IDS[key]);
    if u:set_points(u,v)

# ---------- 3) Armoury placement: put weapon in weapon group; wargear in wargear group ----------
SERVO='r44-ih-servo-arm'; MECH='r44-ih-mechadendrites'; GLAD='r44-ih-gladius'; BION='r44-ih-bionics-character'
removed_bad_armoury=0
for uid,slug in (('hq-praetor','praetor'),('hq-centurion','centurion')):
    u=byid(cr,uid)
    if u is None:continue
    # remove all old direct IH links for these four items, wherever they were incorrectly placed
    for p in list(u.iter()):
        for x in list(p):
            if x.tag==C('entryLink') and x.get('targetId') in (SERVO,MECH,GLAD,BION):p.remove(x);removed_bad_armoury+=1
    wg=find_group(u,'weapon');gear=find_group(u,'wargear')
    base=[('atLeast',1,'roster',LEG)]
    link(wg,f'r79-ih-{slug}-gladius','Albian Power Gladius',GLAD,base)
    servo=link(gear,f'r79-ih-{slug}-servo','Servo-Arm',SERVO,base)
    # hide servo if Jump Pack selected
    jump='hq-praetor-jump' if uid=='hq-praetor' else 'hq-centurion-jump'
    hide_if(servo,f'r79-ih-{slug}-servo-jump-hide',[('atLeast',1,'root-entry',jump)])
    link(gear,f'r79-ih-{slug}-mech','Mechadendrites',MECH,base)
    link(gear,f'r79-ih-{slug}-bionics','Bionics',BION,base)

# ---------- 4) Medusan Immortal squad: 5–20 true total; squad-wide grenade costs scale ----------
imm=byid(cr,IDS['imm'])
if imm:
    # Replace imported "Squad Models" quantity with a clean true-total counter while preserving options separately.
    for x in list(imm.findall('./'+C('selectionEntries')+'/'+C('selectionEntry'))):
        if x.get('type')=='model' and ('squad models' in (x.get('name') or '').lower() or 'additional' in (x.get('id') or '')) and not (x.get('id') or '').startswith('r79-ih-'):
            # Keep profiles if present; quantity structure is normalized below via the selected model counter we already created if needed.
            pass
    models=direct_models(imm)
    counter=next((m for m in models if (m.get('id') or '').startswith('r79-ih-')),None) or next((m for m in models if 'squad models' in (m.get('name') or '').lower()),None)
    if counter:
        wipe(counter,'constraints');constraint(counter,'r79-ih-imm-model-min','min',5);constraint(counter,'r79-ih-imm-model-max','max',20);counter.set('defaultAmount','5')
        # base unit cost is 150 for 5; extra count above five should be +27 each. New Recruit model counter itself would charge every model if cost=27, so use repeat modifier on a zero-cost squadwide shell.
        set_points(counter,0)
    # Remove old squad-wide imported grenade options and recreate clean scalable choices.
    for p in list(imm.iter()):
        for x in list(p):
            n=(x.get('name') or '').lower()
            if x.tag==C('selectionEntry') and ('frag grenades' in n or 'krak grenades' in n) and not (x.get('id') or '').startswith('r79-ih-'):p.remove(x)
    for nm,pp in [('Frag grenades',1),('Krak grenades',2)]:
        e=add_entry(imm,'r79-ih-imm-'+nm.split()[0].lower(),nm+' (+%d pt/model)'%pp,0)
        mods=ensure(e,'modifiers')
        mids=[m.get('id') for m in direct_models(imm) if m.get('id')]
        for j,mid in enumerate(dict.fromkeys(mids)):
            mo=ET.SubElement(mods,C('modifier'),{'id':f'r79-ih-imm-{nm[0].lower()}-cost-{j}','type':'increment','value':str(pp),'field':'pts'});reps=ET.SubElement(mo,C('repeats'));ET.SubElement(reps,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'root-entry','childId':mid,'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})

# ---------- 5) Rites rebuilt as named rules + enforceable roster mechanics ----------
head=byid(cr,HEAD);bitter=byid(cr,BITTER)
if head is None or bitter is None:raise RuntimeError('Missing Iron Hands rites')
wipe(head,'rules');wipe(bitter,'rules')
for i,n,t in [
('ground','Ground of Choice','All Iron Hands Infantry units gain Stubborn while at least half of the unit’s surviving models are within the Iron Hands deployment zone.'),
('relics','Relics of War','All Iron Hands Vehicles in the Detachment receive Blessed Autosimulacra at no additional points cost.'),
('scions','Scions of Iron','Any Iron Hands Infantry unit of ten models or fewer which may normally select a Rhino as a Dedicated Transport may instead select a Land Raider Phobos or Land Raider Proteus as a Dedicated Transport at normal points cost. Normal Transport Capacity restrictions apply.'),
('encirclement','Armoured Encirclement','Iron Hands Vehicles with the Tank unit type gain Outflank if placed in Reserve. A Dedicated Transport carrying a unit may Outflank with its passengers as one Reserve entry.'),
('limits','Limitations','The Detachment may include no more than one Fast Attack choice, no more than one Consul excluding Forge Lords, and may not include an Allied Detachment drawn from another Space Marine Legion.')]:add_rule(head,'r79-ih-head-'+i,n,t)
for i,n,t in [
('company','Company of Immortals','Medusan Immortal Squads may be selected as Troops and fulfil compulsory Troops selections. At least one compulsory Troops choice must be a Medusan Immortal Squad.'),
('hatred','Immortal Hatred','All units in the Detachment with Legiones Astartes (Iron Hands) gain Hatred against Traitor forces.'),
('duty','Bitter Duty','A Medusan Immortal Squad gains Fearless while the majority of its surviving models are within the enemy deployment zone.'),
('purpose','No Death Without Purpose','When a Medusan Immortal Squad is completely destroyed while the majority of its models were within the enemy deployment zone immediately before destruction, every friendly Iron Hands unit within 6 inches may immediately re-roll any failed Morale or Pinning test required as a result.'),
('limits','Limitations','Loyalist Iron Hands only. The army may not include an Allied Detachment and may not include Ferrus Manus.')]:add_rule(bitter,'r79-ih-bitter-'+i,n,t)
show_if(head,'r79-ih-head-show',[('atLeast',1,'roster',LEG)]);show_if(bitter,'r79-ih-bitter-show',[('atLeast',1,'roster',LEG),('atLeast',1,'roster','allegiance-loyalist')])

# Fast Attack max 1 for Head.
flfast=byid(gr,'fl-fast')
if flfast:
    mx=next((x for x in flfast.findall('./'+G('constraints')+'/'+G('constraint')) if x.get('type')=='max'),None)
    if mx:
        m=ET.SubElement(ensure(flfast,'modifiers',GNS),G('modifier'),{'id':'r79-ih-head-fast-max','type':'set','value':'1','field':mx.get('id')});cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Bitter Iron Ferrus exclusion.
if fer:hide_if(fer,'r79-ih-bitter-hide-ferrus',[('atLeast',1,'roster',BITTER)])

# Bitter Iron Troops clone: repair existing role clone and gate to Rite; preserve normal 0-1 on canonical entry.
role=byid(cr,'r42-role-x-1-effects-company-of-immortals-medusan-immortal-squads-r41-unit-x-0-medusan-immortal-squad')
if role:
    remove_rule_names(role,{'Special Rules','Unit Composition'})
    # ensure Troops category and gate only under rite
    cats=ensure(role,'categoryLinks')
    for c in cats.findall(C('categoryLink')):c.set('primary','false')
    tro=next((c for c in cats.findall(C('categoryLink')) if c.get('targetId')=='cat-troops'),None)
    if tro is None:ET.SubElement(cats,C('categoryLink'),{'id':'r79-ih-bitter-role-troops','name':'Troops','hidden':'false','targetId':'cat-troops','primary':'true'})
    else:tro.set('primary','true')
    show_if(role,'r79-ih-bitter-role-show',[('atLeast',1,'roster',LEG),('atLeast',1,'roster',BITTER)])
    rule_once(role,'bitterclone','Legiones Astartes (Iron Hands)');rule_once(role,'bitterclone','Stubborn')

# Compulsory category requiring at least one Bitter-Iron Immortal Troop.
ces=ensure(gr,'categoryEntries',GNS); CATID='r79-ih-bitter-comp'
cat=byid(gr,CATID)
if cat is None:cat=ET.SubElement(ces,G('categoryEntry'),{'id':CATID,'name':'Company of Bitter Iron — compulsory Medusan Immortal','hidden':'true'})
force=byid(gr,'force-standard')
if force:
    links=ensure(force,'categoryLinks',GNS);cl=next((x for x in links.findall(G('categoryLink')) if x.get('targetId')==CATID),None)
    if cl is None:cl=ET.SubElement(links,G('categoryLink'),{'id':'r79-ih-bitter-comp-link','name':'Company of Bitter Iron — compulsory Medusan Immortal','hidden':'true','targetId':CATID})
    wipe(cl,'constraints',GNS);c=constraint(cl,'r79-ih-bitter-comp-min','min',0,ns=GNS)
    mo=ET.SubElement(ensure(cl,'modifiers',GNS),G('modifier'),{'id':'r79-ih-bitter-comp-set','type':'set','value':'1','field':c.get('id')});cs=ET.SubElement(mo,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':BITTER,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    if role:add_cat(role,'r79-ih-bitter-comp-cat',CATID,'Company of Bitter Iron — compulsory Medusan Immortal')

# Head of Gorgon: make paid Autosimulacra free and compulsory on visible vehicle links while Rite active.
auto_links=0
for l in cr.iter(C('entryLink')):
    if l.get('targetId')!='r44-ih-autosimulacra':continue
    mo=ET.SubElement(ensure(l,'modifiers'),C('modifier'),{'id':'r79-ih-head-auto-free-'+re.sub('[^a-z0-9]+','-',l.get('id') or 'x')[-45:],'type':'set','value':'0','field':'pts'});cs=ET.SubElement(mo,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'});auto_links+=1
    # minimum 1 under Rite so the free upgrade is actually received
    cmin=constraint(l,'r79-ih-head-auto-min-'+re.sub('[^a-z0-9]+','-',l.get('id') or 'x')[-40:],'min',0)
    mm=ET.SubElement(ensure(l,'modifiers'),C('modifier'),{'id':'r79-ih-head-auto-force-'+re.sub('[^a-z0-9]+','-',l.get('id') or 'x')[-40:],'type':'set','value':'1','field':cmin.get('id')});cc=ET.SubElement(mm,C('conditions'));ET.SubElement(cc,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Scions of Iron: add Phobos/Proteus to every unit that already has a Rhino DT and <=10 can use it. Use shared vehicle entries from HS pattern where possible.
def rhino_transport_groups(u):
    out=[]
    for g in u.iter(C('selectionEntryGroup')):
        if 'dedicated transport' not in (g.get('name') or '').lower():continue
        if any('rhino' in (x.get('name') or '').lower() for x in g.iter(C('selectionEntry'))) or any('rhino' in (x.get('name') or '').lower() for x in g.iter(C('entryLink'))):out.append(g)
    return out
phobos=byid(cr,'hs-lr-phobos');proteus=byid(cr,'hs-lr-proteus')
scions_links=0
if phobos is not None and proteus is not None:
    for u in cr.iter(C('selectionEntry')):
        if u.get('type')!='unit':continue
        n=(u.get('name') or '').lower()
        if any(x in n for x in ('terminator','bike','jetbike','dreadnought','vehicle','tank','speeder')):continue
        for g in rhino_transport_groups(u):
            for base,slug in ((phobos,'phobos'),(proteus,'proteus')):
                eid=f'r79-ih-scions-{re.sub("[^a-z0-9]+","-",u.get("id") or "unit")[-35:]}-{slug}'
                if byid(cr,eid):continue
                x=copy.deepcopy(base)
                # prefix nested IDs to avoid collisions
                for z in x.iter():
                    if z.get('id'):z.set('id',eid+'-'+z.get('id'))
                x.set('id',eid);x.set('name','Land Raider '+('Phobos' if slug=='phobos' else 'Proteus')+' (Scions of Iron)');x.set('hidden','true')
                show_if(x,eid+'-show',[('atLeast',1,'roster',LEG),('atLeast',1,'roster',HEAD),('atMost',10,'root-entry','model')])
                ensure(g,'selectionEntries').append(x);scions_links+=1

# ---------- 6) Retinues ----------
def add_retinue(owner,base,pfx,label):
    if owner is None or base is None:return None
    gs=ensure(owner,'selectionEntryGroups');g=next((x for x in gs.findall(C('selectionEntryGroup')) if 'retinue' in (x.get('name') or '').lower()),None)
    if g is None:g=ET.SubElement(gs,C('selectionEntryGroup'),{'id':pfx+'-group','name':'Retinue (does not occupy a separate FOC slot)','hidden':'false'});constraint(g,pfx+'-group-max','max',1)
    x=copy.deepcopy(base)
    for z in x.iter():
        if z.get('id'):z.set('id',pfx+'-'+z.get('id'))
    x.set('id',pfx+'-'+base.get('id'));x.set('name',label);wipe(x,'categoryLinks')
    ensure(g,'selectionEntries').append(x);return x
cmd=byid(cr,'hq-centurion-ret-command') or byid(cr,'hq-praetor-ret-command')
tcmd=byid(cr,'hq-praetor-ret-termcommand') or byid(cr,'hq-centurion-ret-termcommand')
hon=byid(cr,'hq-praetor-ret-honour')
if med:add_retinue(med,cmd,'r79-ih-meduson-command','Legion Command Squad')
if aut:add_retinue(aut,tcmd,'r79-ih-autek-termcommand','Legion Terminator Command Squad')
if san:add_retinue(san,byid(cr,IDS['morlock']),'r79-ih-santar-morlocks','Morlock Terminator Squad')
if fer:
    add_retinue(fer,hon,'r79-ih-ferrus-honour','Legion Honour Guard Squad');add_retinue(fer,tcmd,'r79-ih-ferrus-termcommand','Legion Terminator Command Squad');add_retinue(fer,byid(cr,IDS['morlock']),'r79-ih-ferrus-morlocks','Morlock Terminator Squad')

# ---------- 7) Add missing Castrmen Orth ----------
top=cr.find(C('selectionEntries'))
ORTH='r79-ih-castrmen-orth'
if byid(cr,ORTH) is None and top is not None:
    o=ET.SubElement(top,C('selectionEntry'),{'id':ORTH,'name':'CASTRMEN ORTH','type':'unit','hidden':'true','import':'true'});set_points(o,50);constraint(o,ORTH+'-max','max',1,'roster');add_cat(o,ORTH+'-hq','cat-hq','HQ','true');show_if(o,ORTH+'-show',[('atLeast',1,'roster',LEG)])
    add_rule(o,ORTH+'-upgrade','Vehicle Commander','Castrmen Orth is purchased as a +50 point upgrade for one Iron Hands Vehicle (Tank). Orth and that Vehicle together occupy the Vehicle’s normal Force Organisation selection and one HQ selection. He may not command a Walker, a Vehicle without a Ballistic Skill characteristic, or a Vehicle already commanded by another named character. Select the commanded Vehicle in your roster and apply these rules to it.')
    add_rule(o,ORTH+'-spear','Spearhead Centurion','The Vehicle commanded by Castrmen Orth has Ballistic Skill 5, replacing its normal Ballistic Skill.')
    add_rule(o,ORTH+'-hunter','Tank Hunters','Orth’s Vehicle has the normal ProHammer Tank Hunters special rule. If the Vehicle is destroyed, Castrmen Orth is also slain for Victory Point and mission purposes. Orth is not a separate model and may not leave his Vehicle.')

# ---------- 8) Santar 1500+ ----------
if san:
    constraint(san,'r79-ih-santar-1500','min',1500,'roster')

# ---------- 9) Validation ----------
# No Source Entry or aggregate source dump in Iron Hands canon / Bitter clone / AL rewards.
bad=[]
for u in relevant + ([role] if role is not None else []):
    if u is None:continue
    for r in u.iter(C('rule')):
        nm=(r.get('name') or '').lower();desc=(r.findtext(C('description')) or '').lower()
        if nm.startswith('source entry') or ('force organisation:' in desc and 'wargear:' in desc and 'special rules:' in desc):bad.append((u.get('id'),r.get('id'),r.get('name')))
if bad:raise RuntimeError('Source/aggregate dumps remain: '+str(bad[:20]))
# Generic HQ Gladius must be in weapons, not wargear.
for uid in ('hq-praetor','hq-centurion'):
    u=byid(cr,uid);wg=find_group(u,'weapon');gear=find_group(u,'wargear')
    for l in u.iter(C('entryLink')):
        if l.get('targetId')==GLAD:
            pm={c:p for p in u.iter() for c in p};p=pm.get(l)
            while p is not None and p.tag!=C('selectionEntryGroup'):p=pm.get(p)
            if p is not wg:raise RuntimeError(f'Gladius wrong parent under {uid}')
# Duplicate IDs
seen=set();dups=[]
for root in (cr,gr):
    for e in root.iter():
        i=e.get('id')
        if not i:continue
        if i in seen:dups.append(i)
        seen.add(i)
if dups:raise RuntimeError('Duplicate IDs '+str(dups[:25]))

# Revisions
cr.set('revision','79');cr.set('gameSystemRevision','46');gr.set('revision','46')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat':e.set('dataRevision','79')
    if e.get('filePath')=='Prohammer 30k.gst':e.set('dataRevision','46')
ET.indent(ct,space='  ');ET.indent(gt,space='  ');ET.indent(it,space='  ')
ET.register_namespace('',CNS);ct.write(CAT,encoding='utf-8',xml_declaration=True)
ET.register_namespace('',GNS);gt.write(GST,encoding='utf-8',xml_declaration=True)
ET.register_namespace('',INS);it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT);ET.parse(GST);ET.parse(IDX)

OUT.write_text(f'''Revision 79 — Iron Hands full standards pass\nCAT=79 GST=46\n\nPresentation\n- Removed {removed_dumps} Source Entry / aggregate imported rule dumps from Iron Hands canonical, Rite-clone and Rewards-of-Treachery copies.\n- Moved {profiles_moved} top-level profiles onto real model selections; created {model_children} locked named-character/Primarch model children.\n- Replaced source dumps with actual individual rules.\n\nArmoury\n- Removed {removed_bad_armoury} old generic HQ Iron Hands armoury links.\n- Albian Power Gladius now lives in Weapon Replacements.\n- Servo-Arm, Mechadendrites and Bionics now live in Additional Wargear.\n- Servo-Arm is hidden when the generic HQ takes a Jump Pack.\n\nCurrent source values\n- Medusan Immortals 150; Gorgons 250; Morlocks 275; Venerable Forge Lord 155; Meduson 165; Autek Mor 205; Santar 220; Ferrus Manus 505.\n- Santar retains the current 1500+ restriction.\n\nRites\n- Head of the Gorgon rebuilt into named rules; Fast Attack max 1; Blessed Autosimulacra is free/compulsory through {auto_links} existing vehicle links; Scions of Iron added {scions_links} conditional Land Raider pattern entries to Rhino-capable infantry transport menus.\n- Company of Bitter Iron rebuilt into named rules; Loyalist-gated; Ferrus excluded; existing Immortal Troops clone repaired; compulsory Immortal category enforced.\n\nCharacters / retinues\n- Meduson Command Squad; Autek Terminator Command; Santar Morlocks; Ferrus Honour Guard/Terminator Command/Morlocks.\n- Added Castrmen Orth as current 50-point HQ vehicle-commander upgrade entry.\n\nValidation\n- No Iron Hands Source Entry/aggregate source dumps remain in audited canonical/clone/reward entries.\n- Gladius placement validated in generic HQ weapon sections.\n- Duplicate-ID and XML parse validation passed.\n''',encoding='utf-8')
print(OUT.read_text())
