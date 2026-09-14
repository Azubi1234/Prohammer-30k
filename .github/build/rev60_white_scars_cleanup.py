from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET
import re

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); INDEX=Path('index.xml')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()
top=cr.find(C('selectionEntries')); shared=cr.find(C('sharedSelectionEntries'))
assert top is not None and shared is not None
REPORT=[]
def note(s): REPORT.append(s); print(s)
def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def top_by_name(q):
    q=q.lower(); return next((e for e in list(top) if q in (e.get('name') or '').lower()),None)
def ensure(p,tag,ns=CNS):
    q=f'{{{ns}}}{tag}'; x=p.find(q)
    if x is None:x=ET.SubElement(p,q)
    return x
def wipe(p,tag):
    x=p.find(C(tag))
    if x is not None:p.remove(x)
def add_constraint(e,id_,kind,val,scope='parent'):
    cs=ensure(e,'constraints'); return ET.SubElement(cs,C('constraint'),{'id':id_,'type':kind,'value':str(val),'field':'selections','scope':scope,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_cost(e,v,id_=None):
    cs=ensure(e,'costs'); c=ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
    if id_:c.set('id',id_)
    return c
def set_points(e,v):
    cs=ensure(e,'costs')
    for c in list(cs):
        if c.get('typeId')=='pts' or c.get('name')=='Points':cs.remove(c)
    add_cost(e,v)
def add_rule(e,id_,name,text):
    rs=ensure(e,'rules'); r=ET.SubElement(rs,C('rule'),{'id':id_,'name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=text; return r
def remove_rule_named(e,name):
    rs=e.find(C('rules'))
    if rs is None:return 0
    n=0
    for r in list(rs):
        if (r.get('name') or '').strip().lower()==name.lower(): rs.remove(r); n+=1
    if len(rs)==0:e.remove(rs)
    return n
def group(e,id_,name,maxv=None):
    gs=ensure(e,'selectionEntryGroups'); g=ET.SubElement(gs,C('selectionEntryGroup'),{'id':id_,'name':name,'hidden':'false','collective':'false','import':'true'})
    if maxv is not None:add_constraint(g,id_+'-max','max',maxv)
    return g
def option(g,id_,name,cost=0,maxv=1,rule=None,typ='upgrade'):
    ses=ensure(g,'selectionEntries'); s=ET.SubElement(ses,C('selectionEntry'),{'id':id_,'name':name,'type':typ,'hidden':'false','import':'true'})
    add_constraint(s,id_+'-max','max',maxv); add_cost(s,cost,id_+'-pts')
    if rule:add_rule(s,id_+'-rule',name,rule)
    return s
def model_counter(e,id_,name,mn,mx,per):
    ses=ensure(e,'selectionEntries'); s=ET.SubElement(ses,C('selectionEntry'),{'id':id_,'name':name,'type':'model','hidden':'false','import':'true','defaultAmount':str(mn)})
    add_constraint(s,id_+'-min','min',mn); add_constraint(s,id_+'-max','max',mx); add_cost(s,per,id_+'-pts'); return s
def fixed(e,id_,name):
    ses=ensure(e,'selectionEntries'); s=ET.SubElement(ses,C('selectionEntry'),{'id':id_,'name':name,'type':'upgrade','hidden':'false','import':'true','defaultAmount':'1'}); add_constraint(s,id_+'-min','min',1); add_constraint(s,id_+'-max','max',1); return s
def clean_options(e):
    wipe(e,'selectionEntryGroups'); wipe(e,'selectionEntries')
def set_primary_cat(e,target,name):
    wipe(e,'categoryLinks'); cs=ET.SubElement(e,C('categoryLinks')); ET.SubElement(cs,C('categoryLink'),{'id':e.get('id')+'-cat','name':name,'targetId':target,'hidden':'false','primary':'true'})
def rewrite_ids(node,prefix):
    mp={x.get('id'):prefix+x.get('id') for x in node.iter() if x.get('id')}
    for x in node.iter():
        if x.get('id') in mp:x.set('id',mp[x.get('id')])
        for a in ('targetId','childId','field'):
            if x.get(a) in mp:x.set(a,mp[x.get(a)])
def clone_role(src,newid,newname,catid,catname,legion,rite=None):
    c=deepcopy(src); rewrite_ids(c,newid+'-'); c.set('id',newid); c.set('name',newname); set_primary_cat(c,catid,catname); c.set('hidden','true')
    mods=ensure(c,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':newid+'-show','type':'set','value':'false','field':'hidden'}); cgs=ET.SubElement(m,C('conditionGroups')); cg=ET.SubElement(cgs,C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(cg,C('conditions'))
    for child,scope in [(legion,'roster')]+([(rite,'force')] if rite else []): ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    top.append(c); return c
def hide_if_missing(e,child,scope='roster'):
    mods=ensure(e,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':e.get('id')+'-hide-'+child,'type':'set','value':'true','field':'hidden'}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'lessThan','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def clone_nested(src,newid,newname=None):
    c=deepcopy(src); rewrite_ids(c,newid+'-'); c.set('id',newid)
    if newname:c.set('name',newname)
    wipe(c,'categoryLinks'); wipe(c,'modifiers'); return c
def add_retinue(owner,id_,choices):
    rg=group(owner,id_,'Retinue (does not occupy a separate FOC slot)',1); ses=ensure(rg,'selectionEntries'); added=[]
    for label,src in choices:
        if src is not None: ses.append(clone_nested(src,id_+'-'+re.sub('[^a-z0-9]+','-',label.lower()).strip('-'),label)); added.append(label)
    if added:add_rule(rg,id_+'-rule','Retinue',owner.get('name')+' may select one of: '+', '.join(added)+'. It occupies no separate Force Organisation slot.')
    return rg
def transport_group(e,id_,names):
    g=group(e,id_,'Dedicated Transport',1)
    for n in names:
        t=top_by_name(n)
        if t is None:continue
        ls=ensure(g,'entryLinks'); l=ET.SubElement(ls,C('entryLink'),{'id':id_+'-'+re.sub('[^a-z0-9]+','-',n.lower()).strip('-'),'name':t.get('name'),'type':'selectionEntry','targetId':t.get('id'),'hidden':'false','import':'true'}); add_constraint(l,l.get('id')+'-max','max',1)
    return g

def find_rite(q):
    q=q.lower(); return next((e for e in cr.iter(C('selectionEntry')) if q in (e.get('name') or '').lower() and 'rite' in e.get('id','')),None)
def gst_set_max(selector,value,id_):
    l=next((x for x in gr.iter(G('forceEntry')) if x.get('id')=='fl-heavy'),None)
    if l is None:return
    cs=l.find(G('constraints')); con=next((x for x in cs.findall(G('constraint')) if x.get('type')=='max'),None) if cs is not None else None
    if con is None:return
    mods=ensure(l,'modifiers',GNS); m=ET.SubElement(mods,G('modifier'),{'id':id_,'type':'set','value':str(value),'field':con.get('id')}); c=ET.SubElement(ET.SubElement(m,G('conditions')),G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Idempotent cleanup of this revision and obsolete White Scars r43 structures.
for p in list(cr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r60-') or x.get('id','').startswith('r43-ws-'): p.remove(x)
for p in list(gr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r60-') or x.get('id','').startswith('r43-ws-'): p.remove(x)

chog=find_rite('chogorian brotherhood'); sag=find_rite('sagyar mazan'); assert chog is not None and sag is not None
note(f'Rites: Chogorian={chog.get("id")} Sagyar={sag.get("id")}')

# Final-source White Scars entries.
keys={'gold':'golden keshig','ebon':'ebon keshig','dark':'dark sons of death','falcon':'falcon','qin':'qin xa','yes':'targutai yesugei','shiban':'shiban khan','hibou':'hibou khan','hasik':'hasik noyan','jagh':'jaghatai khan'}
units={}
for k,q in keys.items():
    x=top_by_name(q); assert x is not None,(k,q); units[k]=x
note('Located White Scars final entries: '+', '.join(f'{k}={v.get("id")}' for k,v in units.items()))
removed=sum(remove_rule_named(v,'Source Entry') for v in units.values()); note(f'Removed {removed} White Scars Source Entry dumps')

# Legion rules on the legion selector/reference.
leg=by_id('legion-v')
if leg is not None:
    # remove prior r60 rules only already done
    add_rule(leg,'r60-ws-swift','Swift Advance','Eligible White Scars Infantry in Power, Artificer or Recon Armour may forgo shooting to move an additional D6 inches. This move ignores Difficult Terrain, may not move within 1 inch of the enemy and the unit may not charge that turn. Terminator and Hardened Armour may not use this rule.')
    add_rule(leg,'r60-ws-saddle','Born in the Saddle','White Scars models on Bikes or Jetbikes gain Skilled Rider. Legion Bike and Sky Hunter Jetbike Squadrons also gain Hit & Run while every model in the unit, including attached Independent Characters, is mounted on a Bike or Jetbike. Attack Bikes do not gain Hit & Run from this rule.')
    add_rule(leg,'r60-ws-mounted','Mounted Brotherhoods','Legion Bike Squadrons may be selected as Troops and may fulfil compulsory Troops selections.')

# Armoury on Praetor/Centurion in structured groups.
for uid in ('hq-praetor','hq-centurion'):
    u=by_id(uid)
    if u is None:continue
    g=group(u,'r60-'+uid+'-ws-armoury','White Scars Armoury'); hide_if_missing(g,'legion-v')
    option(g,'r60-'+uid+'-glaive','Power Glaive',25,1,'Character able to select a Power Weapon. One-handed: User Strength, Power Weapon. Two-handed: User +1 Strength, Power Weapon, Two-Handed. If replacing a basic Power Weapon, use the source exchange price of +10 instead.')
    option(g,'r60-'+uid+'-talisman','Horsetail Talisman',25,1,'0–1 per army. Once per battle, bearer and friendly White Scars non-vehicle units within 6 inches may move D6 inches instead of shooting; they may not charge that turn.')
# Praetor-only Cyber-hawk.
p=by_id('hq-praetor')
if p is not None:
    g=next((x for x in p.iter(C('selectionEntryGroup')) if x.get('id')=='r60-hq-praetor-ws-armoury'),None)
    if g is not None: option(g,'r60-ws-cyberhawk','Cyber-hawk',10,1,'0–1 White Scars Praetor. Place or move the marker at the start of each White Scars turn. White Scars Infantry attacking an enemy within 6 inches may re-roll shooting To Hit rolls of 1 and increases charge distance against that enemy from 6 to 7 inches.')
# Mounted units may buy Warlances.
for uid in ('fa-bike','fa-sky'):
    u=by_id(uid)
    if u is not None:
        g=group(u,'r60-'+uid+'-ws-armoury','White Scars Armoury'); hide_if_missing(g,'legion-v'); option(g,'r60-'+uid+'-warlance','Chogorian Warlance',15,10,'Power Weapon, Cavalry Lance. +1 Initiative in the first round when charging; -1 Initiative in rounds in which the bearer did not charge. One-handed.')

# Stormseer Consul replaces Librarian for White Scars.
cent=by_id('hq-centurion')
if cent is not None:
    g=group(cent,'r60-ws-stormseer-group','White Scars Consul Upgrade',1); hide_if_missing(g,'legion-v')
    s=option(g,'r60-ws-stormseer','Stormseer Consul',35,1,'Replace Chainsword with a Force Weapon. Gains Psyker (Mastery Level 1), Adamantium Will and Legion Support Officer. Knows Unseen Bolt: 36 inches, S6 AP4, Assault 1, Blast, Pinning; psychic shooting power. May buy a Psychic Hood +25 and Mastery Level 2 +25, selecting one additional normal Legion Librarian power.')
    sg=group(s,'r60-ws-stormseer-options','Stormseer Options'); option(sg,'r60-ws-stormseer-hood','Psychic Hood',25); option(sg,'r60-ws-stormseer-ml2','Epistolary — Mastery Level 2',25)
lib=by_id('hq-consul-librarian')
if lib is not None:
    mods=ensure(lib,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':'r60-ws-hide-librarian','type':'set','value':'true','field':'hidden'}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':'legion-v','shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Unique units — TOTAL MODEL COUNTERS FROM THE START.
gold=units['gold']; clean_options(gold); set_points(gold,15); mc=model_counter(gold,'r60-ws-gold-models','Golden Keshig Squadron Models',3,5,55)
g=group(gold,'r60-ws-gold-squad','Squad Equipment'); option(g,'r60-ws-gold-krak','Krak grenades — select once per model',2,5); option(g,'r60-ws-gold-melta','Melta bombs — select once per model',5,5)
g=group(gold,'r60-ws-gold-jbike','Jetbike Weapons',1); option(g,'r60-ws-gold-mm','Multi-Melta — replace Heavy Bolter with Hellfire Rounds',10,1); option(g,'r60-ws-gold-volk','Volkite Culverin — replace Heavy Bolter with Hellfire Rounds',10,1)
add_rule(gold,'r60-ws-gold-limit','Jetbike Weapons','For every three models in the squadron, one Golden Keshig may replace the Heavy Bolter with Hellfire Rounds. At 3–5 models this allows one replacement.')

ebon=units['ebon']; clean_options(ebon); set_points(ebon,0); model_counter(ebon,'r60-ws-ebon-models','Ebon Keshig',5,10,45); transport_group(ebon,'r60-ws-ebon-transport',['Land Raider','Dreadclaw Drop Pod','Spartan Assault Tank']); add_rule(ebon,'r60-ws-ebon-dao','Dragon Dao','Power Weapon. At the beginning of each Assault phase the bearer may wield it with both hands, gaining +2 Strength but suffering -2 Initiative and receiving no bonus Attack for two close-combat weapons.')

dark=units['dark']; clean_options(dark); set_points(dark,25); model_counter(dark,'r60-ws-dark-models','Dark Sons of Death',5,10,35)
g=group(dark,'r60-ws-dark-squad','Squad Equipment'); option(g,'r60-ws-dark-krak','Krak grenades — select once per model',2,10); option(g,'r60-ws-dark-melta','Melta bombs — select once per model',5,10); option(g,'r60-ws-dark-jump','Jump Packs — select once per model',15,10,'Every model must take this upgrade. The unit becomes Jump Infantry and may not select a Dedicated Transport.')
g=group(dark,'r60-ws-dark-weapons','Destroyer Weapons',2); option(g,'r60-ws-dark-volk','Volkite serpenta — replace one Bolt pistol',5,2); option(g,'r60-ws-dark-flamer','Hand flamer — replace one Bolt pistol',5,2); option(g,'r60-ws-dark-plasma','Plasma pistol — replace one Bolt pistol',15,2); option(g,'r60-ws-dark-missile','Missile launcher with Suspensor Web and Rad Missiles — replace one Bolt pistol',25,2); add_rule(g,'r60-ws-dark-weapon-limit','Destroyer Weapon Limit','One Destroyer Weapon replacement is permitted for every five models in the squad; therefore 1 at 5–9 models and 2 at 10 models.')
g=group(dark,'r60-ws-dark-speaker','Death Speaker'); option(g,'r60-ws-dark-art','Artificer Armour',10); option(g,'r60-ws-dark-phosphex','Phosphex Bomb',10,3); transport_group(dark,'r60-ws-dark-transport',['Rhino','Drop Pod','Dreadclaw Drop Pod','Land Raider'])

fal=units['falcon']; clean_options(fal); set_points(fal,10); model_counter(fal,'r60-ws-falcon-models',"Falcon's Claws",5,10,22)
g=group(fal,'r60-ws-falcon-squad','Squad Equipment'); option(g,'r60-ws-falcon-krak','Krak grenades — select once per model',2,10); option(g,'r60-ws-falcon-camo','Cameleoline — select once per model',5,10)
g=group(fal,'r60-ws-falcon-weapons','Weapon Replacements',10); option(g,'r60-ws-falcon-shotgun','Astartes Shotgun — replace M.40 Stalker Bolter',0,10); option(g,'r60-ws-falcon-sniper','Sniper Rifle — replace M.40 Stalker Bolter',5,10)
g=group(fal,'r60-ws-falcon-special','Special Equipment'); option(g,'r60-ws-falcon-nuncio','Nuncio Vox',10,1); add_rule(fal,'r60-ws-falcon-sabotage','Sabotage','After deployment but before the first turn, nominate one enemy unit, Vehicle or Fortification. It suffers D6 S5 AP6 hits; against Vehicles/Fortifications use the lowest Armour Value. These casualties do not cause Morale or Pinning tests.')

# Character options and retinues.
cmd=by_id('hq-centurion-ret-command') or by_id('hq-praetor-ret-command'); vet=by_id('veteran-unit'); termcmd=by_id('hq-praetor-ret-termcommand') or by_id('hq-centurion-ret-termcommand'); honour=by_id('hq-praetor-ret-honour')
qin=units['qin']; clean_options(qin); set_points(qin,180); add_retinue(qin,'r60-ws-qin-retinue',[('Ebon Keshig',ebon),('Legion Terminator Command Squad',termcmd)])
yes=units['yes']; clean_options(yes); set_points(yes,195); g=group(yes,'r60-ws-yes-options','Options'); option(g,'r60-ws-yes-krak','Krak grenades',2)
for key,pts in [('shiban',155),('hibou',155),('hasik',175)]:
    e=units[key]; clean_options(e); set_points(e,pts); g=group(e,'r60-ws-'+key+'-options','Options'); option(g,'r60-ws-'+key+'-krak','Krak grenades',2); 
    if key!='hibou': option(g,'r60-ws-'+key+'-melta','Melta bombs',5)
    bike=option(g,'r60-ws-'+key+'-bike','Space Marine Bike',35); option(g,'r60-ws-'+key+'-jetbike','Upgrade Bike to Jetbike',5)
    choices=[('Legion Command Squad',cmd)]
    if key in ('hibou','hasik'): choices.append(('Legion Veteran Squad',vet))
    add_retinue(e,'r60-ws-'+key+'-retinue',choices)
# Explicit allegiance reminder for Hasik.
add_rule(units['hasik'],'r60-ws-hasik-traitor','Traitor Only','Hasik Noyan-Khan may only be selected in a Traitor White Scars Detachment.')

j=units['jagh']; clean_options(j); set_points(j,490); g=group(j,'r60-ws-jagh-options','Options'); option(g,'r60-ws-jagh-voidbike','Sojutsu Pattern Voidbike',40,1,'Jaghatai Khan becomes Jetbike and follows the normal ProHammer Jetbike rules.'); add_retinue(j,'r60-ws-jagh-retinue',[('Legion Honour Guard Squad',honour),('Golden Keshig Squadron',gold)])

# Role clones. Permanent Bike Troops; Chogorian Sky Hunters; Sagyar Ebon Keshig.
bike=by_id('fa-bike'); sky=by_id('fa-sky')
if bike is not None: clone_role(bike,'r60-ws-bike-troops','Legion Bike Squadron','cat-troops','Troops','legion-v')
if sky is not None: clone_role(sky,'r60-ws-sky-troops','Legion Sky Hunter Jetbike Squadron','cat-troops','Troops','legion-v',chog.get('id'))
clone_role(ebon,'r60-ws-sagyar-ebon-troops','EBON KESHIG','cat-troops','Troops','legion-v',sag.get('id'))
# Chogorian Heavy Support cap.
gst_set_max(chog.get('id'),1,'r60-ws-chog-heavy-max')
# Rite mechanics/reference rules.
add_rule(chog,'r60-ws-chog-mechanics','Implemented Roster Effects','Sky Hunter Jetbike Squadrons become Troops; Bike and Sky Hunter Squadrons may fulfil compulsory Troops; Heavy Support is limited to one choice. Apply Lightning Encirclement, Master of the Hunt, Strike and Vanish and Warlord/compulsory-Troops restrictions as written in the Rite.')
add_rule(sag,'r60-ws-sag-mechanics','Implemented Roster Effects','Ebon Keshig become Troops and may fulfil compulsory Troops. This Rite is Loyalist only, may not include Jaghatai Khan, may not include Fortifications and may never contain more Vehicle units than non-vehicle Infantry units. Death Seekers, The Serpent’s Eye, Not Yet Dead and No Path of Retreat apply as written.')

# Revision bump: BOTH catalogue and GST, to force New Recruit refresh.
cr.set('revision','60'); cr.set('gameSystemRevision','28'); gr.set('revision','28')
comment=cr.find(C('comment'))
if comment is not None: comment.text='Revision 60: White Scars final-source cleanup with total-model squad counters, structured armoury, functional Rite role changes and character retinues.'
ET.register_namespace('',CNS); ct.write(CAT,encoding='UTF-8',xml_declaration=True)
ET.register_namespace('',GNS); gt.write(GST,encoding='UTF-8',xml_declaration=True)
idx=INDEX.read_text(encoding='utf-8'); idx=re.sub(r'(dataType="gamesystem"[^>]*dataRevision=")\d+("/>)',r'\g<1>28\2',idx); idx=re.sub(r'(dataType="catalogue"[^>]*dataRevision=")\d+("/>)',r'\g<1>60\2',idx); INDEX.write_text(idx,encoding='utf-8')

# Hard validation: namespaces, IDs, refs and TOTAL-MODEL standard.
cat_ids=[x.get('id') for x in cr.iter() if x.get('id')]; gst_ids=[x.get('id') for x in gr.iter() if x.get('id')]
assert len(cat_ids)==len(set(cat_ids)); assert len(gst_ids)==len(set(gst_ids)); allids=set(cat_ids)|set(gst_ids)
broken=[]
for root in (cr,gr):
    for x in root.iter():
        for a in ('targetId','childId'):
            v=x.get(a)
            if v and v not in allids: broken.append((x.get('id'),a,v))
assert not broken,broken[:20]
cattext=CAT.read_text(encoding='utf-8'); gsttext=GST.read_text(encoding='utf-8'); assert '<ns0:' not in cattext and '<ns0:' not in gsttext
assert '<catalogue xmlns="http://www.battlescribe.net/schema/catalogueSchema"' in cattext; assert '<gameSystem xmlns="http://www.battlescribe.net/schema/gameSystemSchema"' in gsttext
expected=[(gold,'Golden Keshig Squadron Models',3,5),(ebon,'Ebon Keshig',5,10),(dark,'Dark Sons of Death',5,10),(fal,"Falcon's Claws",5,10)]
for u,label,mn,mx in expected:
    m=next((x for x in u.findall(C('selectionEntries')+'/'+C('selectionEntry')) if x.get('type')=='model' and x.get('name')==label),None); assert m is not None,(u.get('name'),label)
    vals={c.get('type'):c.get('value') for c in m.find(C('constraints')).findall(C('constraint'))}; assert int(float(m.get('defaultAmount')))==mn and int(float(vals['min']))==mn and int(float(vals['max']))==mx
# No legacy Additional-model quantity counters anywhere.
for e in cr.iter(C('selectionEntry')):
    nm=(e.get('name') or '').strip(); cs=e.find(C('constraints'))
    if nm.startswith('Additional ') and not nm.startswith(('Additional Armoury','Additional Wargear','Additional Weapon')) and cs is not None:
        mx=next((c.get('value') for c in cs.findall(C('constraint')) if c.get('type')=='max' and c.get('field')=='selections'),None)
        if mx is not None and float(mx)>1: raise AssertionError(f'Legacy Additional-model counter: {e.get("id")} {nm} max={mx}')
note('Validation: CAT60/GST28; canonical namespaces; duplicate IDs 0; broken references 0; no legacy Additional-model quantity counters.')
note('White Scars cleanup complete: final-source rules, armoury, Stormseer, Rites, unique units/characters/Primarch structured; unit sizes use actual total models from the start.')
Path('inspection-r60-white-scars-cleanup.txt').write_text('\n'.join(REPORT)+'\n',encoding='utf-8')
