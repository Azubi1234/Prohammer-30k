from pathlib import Path
import copy,re,xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r80-iron-hands-repairs.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS);ET.register_namespace('',GNS);ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}';G=lambda t:f'{{{GNS}}}{t}';I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT);cr=ct.getroot();gt=ET.parse(GST);gr=gt.getroot();it=ET.parse(IDX);ir=it.getroot()
if cr.get('revision')!='79' or gr.get('revision')!='46':raise RuntimeError(f'Expected CAT79/GST46, got CAT{cr.get("revision")}/GST{gr.get("revision")}')
LEG='legion-x'; HEAD='r25-rite-x-0-the-head-of-the-gorgon'; BITTER='r25-rite-x-1-company-of-bitter-iron'; FERRUS='r41-unit-x-7-x-ferrus-manus-the-gorgon'; IMM='r41-unit-x-0-medusan-immortal-squad'
IDS=[IMM,'r41-unit-x-1-gorgon-terminator-squad','r41-unit-x-2-morlock-terminator-squad','r41-unit-x-3-venerable-forge-lord','r41-unit-x-4-shadrak-meduson','r41-unit-x-5-autek-mor','r41-unit-x-6-gabriel-santar',FERRUS]

def byid(root,i):return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t,Q=C):
    x=p.find(Q(t))
    if x is None:x=ET.SubElement(p,Q(t))
    return x
def wipe(p,t,Q=C):
    x=p.find(Q(t))
    if x is not None:p.remove(x)
def pts(e,v=0):
    cs=ensure(e,'costs');[cs.remove(x) for x in list(cs)];ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def con(p,i,typ,val,scope='parent',Q=C,field='selections',child=None):
    d={'id':i,'type':typ,'value':str(val),'field':field,'scope':scope,'shared':'true','includeChildSelections':'true','includeChildForces':'false'}
    if child:d['childId']=child
    return ET.SubElement(ensure(p,'constraints',Q),Q('constraint'),d)
def rm_prefix(root,pfx):
    for p in list(root.iter()):
        for x in list(p):
            if (x.get('id') or '').startswith(pfx):p.remove(x)
def hide_show_and(e,i,conds):
    e.set('hidden','true');m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'});cg=ET.SubElement(ensure(m,'conditionGroups'),C('conditionGroup'),{'type':'and'});cs=ET.SubElement(cg,C('conditions'))
    for typ,val,scope,child in conds:ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_rule(p,i,n,d):
    r=ET.SubElement(ensure(p,'rules'),C('rule'),{'id':i,'name':n,'hidden':'false'});ET.SubElement(r,C('description')).text=d;return r
def local_upgrade(p,i,n,desc=None):
    e=ET.SubElement(ensure(p,'selectionEntries'),C('selectionEntry'),{'id':i,'name':n,'type':'upgrade','hidden':'false','import':'true','defaultAmount':'1'});pts(e,0);con(e,i+'-min','min',1);con(e,i+'-max','max',1)
    if desc:add_rule(e,i+'-rule',n,desc)
    return e
def remove_node(root,node):
    pm={c:p for p in root.iter() for c in p};p=pm.get(node)
    if p is not None:p.remove(node)
def owner_unit(node):
    pm={c:p for p in cr.iter() for c in p};x=node
    while x is not None:
        if x.tag==C('selectionEntry') and x.get('type')=='unit':return x
        x=pm.get(x)
    return None

def duplicate_ids(root):
    seen=set();dup=[]
    for e in root.iter():
        i=e.get('id')
        if not i:continue
        if i in seen:dup.append(i)
        seen.add(i)
    return dup
rm_prefix(cr,'r80-ih-');rm_prefix(gr,'r80-ih-')

# 1) Kill any remaining imported Source Entry / aggregate dumps for Iron Hands everywhere, including stale copies.
names=('medusan immortal','gorgon terminator','morlock terminator','venerable forge lord','shadrak meduson','autek mor','gabriel santar','ferrus manus')
removed_source=0
for p in list(cr.iter()):
    rs=p.find(C('rules'))
    if rs is None:continue
    for r in list(rs.findall(C('rule'))):
        nm=(r.get('name') or '').lower();desc=(r.findtext(C('description')) or '').lower()
        source=nm.startswith('source entry') and any(n in (nm+' '+desc) for n in names)
        aggregate=(nm in ('special rules','unit composition') and any(n in desc for n in names))
        if source or aggregate:rs.remove(r);removed_source+=1

# 2) Dangerous Weaponry: remove the floating standalone option links and place Graviton Gun inside Special Weapons groups.
old_grav=[]
for l in list(cr.iter(C('entryLink'))):
    if l.get('targetId')=='r44-ih-graviton-substitution':old_grav.append(l)
for l in old_grav:remove_node(cr,l)
grav_added=[]
for g in cr.iter(C('selectionEntryGroup')):
    if 'special weapon' not in (g.get('name') or '').lower():continue
    entries=list(g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')));links=list(g.findall('./'+C('entryLinks')+'/'+C('entryLink')))
    allx=entries+links
    if not any('flamer'==(x.get('name') or '').strip().lower() or (x.get('name') or '').strip().lower().startswith('flamer ') for x in allx):continue
    if any('graviton' in (x.get('name') or '').lower() for x in allx):continue
    u=owner_unit(g)
    if u is None:continue
    idx=len(grav_added);l=ET.SubElement(ensure(g,'entryLinks'),C('entryLink'),{'id':f'r80-ih-grav-special-{idx}','name':'Graviton Gun','type':'selectionEntry','targetId':'r44-ih-graviton-substitution','hidden':'true','import':'true'})
    con(l,f'r80-ih-grav-special-{idx}-max','max',99)
    m=ET.SubElement(ensure(l,'modifiers'),C('modifier'),{'id':f'r80-ih-grav-special-{idx}-show','type':'set','value':'false','field':'hidden'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':LEG,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    grav_added.append((u.get('id'),g.get('id')))

# 3) Ferrus: provide real fixed wargear selections and visible weapon profiles, not only rules.
fer=byid(cr,FERRUS)
if fer is None:raise RuntimeError('Ferrus missing')
# remove any prior r80 group
for g in list(fer.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup'))):
    if (g.get('id') or '').startswith('r80-ih-ferrus-wargear'):remove_node(cr,g)
wg=ET.SubElement(ensure(fer,'selectionEntryGroups'),C('selectionEntryGroup'),{'id':'r80-ih-ferrus-wargear','name':'Wargear','hidden':'false'});con(wg,'r80-ih-ferrus-wargear-min','min',7);con(wg,'r80-ih-ferrus-wargear-max','max',7)

def find_generic(name):
    cand=[e for e in cr.iter(C('selectionEntry')) if e.get('type')=='upgrade' and (e.get('name') or '').strip().lower()==name.lower()]
    cand.sort(key=lambda x:(0 if (x.get('id') or '').startswith('gear-') else 1,len(x.get('id') or '')))
    return cand[0] if cand else None
def add_clone(base,name,i,extra_rule=None,strength8=False):
    if base is None:return local_upgrade(wg,i,name,extra_rule or name)
    x=copy.deepcopy(base)
    for z in x.iter():
        if z.get('id'):z.set('id',i+'-'+z.get('id'))
    x.set('id',i);x.set('name',name);x.set('hidden','false');x.set('defaultAmount','1');pts(x,0);wipe(x,'constraints');con(x,i+'-min','min',1);con(x,i+'-max','max',1)
    for p in x.iter(C('profile')):p.set('name',name)
    if strength8:
        for ch in x.iter(C('characteristic')):
            if (ch.text or '').strip().lower()=='user':ch.text='8'
    if extra_rule:add_rule(x,i+'-extra',name,extra_rule)
    ensure(wg,'selectionEntries').append(x);return x
local_upgrade(wg,'r80-ih-ferrus-carapace','Medusan Carapace','Counts as Primarch Armour (1+ Armour Save, 4+ Invulnerable Save; a natural 1 always fails). It incorporates a Twin-linked Meltagun, Twin-linked Plasma Gun, Heavy Flamer, Cortex Controller and Nuncio Vox. Ferrus may fire up to two incorporated weapons in each Shooting phase.')
add_clone(find_generic('Meltagun'),'Twin-linked Meltagun','r80-ih-ferrus-tl-melta','Twin-linked Meltagun: 12", Strength 8, AP1, Assault 1, Melta, Twin-linked.')
add_clone(find_generic('Plasma Gun'),'Twin-linked Plasma Gun','r80-ih-ferrus-tl-plasma','Twin-linked Plasma Gun: 24", Strength 7, AP2, Rapid Fire, Gets Hot, Twin-linked.')
add_clone(find_generic('Heavy Flamer'),'Heavy Flamer','r80-ih-ferrus-heavy-flamer','Heavy Flamer: Template, Strength 5, AP4, Assault 1.')
add_clone(find_generic('Thunder Hammer'),'Forgebreaker','r80-ih-ferrus-forgebreaker','Forgebreaker is a Master-crafted Thunder Hammer with Armourbane.')
add_clone(find_generic('Power Weapon'),'Living Metal Hands','r80-ih-ferrus-living-hands','Ferrus may fight with his Living Metal Hands instead of Forgebreaker. These are Power Weapon attacks resolved at Strength 8.',True)
frag=find_generic('Frag Grenades') or find_generic('Frag Grenade')
add_clone(frag,'Frag Grenades','r80-ih-ferrus-frag','Uses the normal Frag Grenades rules.')
# Carapace command systems as rules on the armour entry, so they appear without extra fake purchasable items.
car=byid(cr,'r80-ih-ferrus-carapace');add_rule(car,'r80-ih-ferrus-cortex','Cortex Controller','The Medusan Carapace incorporates a Cortex Controller; use the normal Cortex Controller rules.');add_rule(car,'r80-ih-ferrus-nuncio','Nuncio Vox','The Medusan Carapace incorporates a Nuncio Vox; use the normal Nuncio Vox rules.')

# 4) Rebuild Rite visibility cleanly using explicit AND groups.
head=byid(cr,HEAD);bitter=byid(cr,BITTER)
if head is None or bitter is None:raise RuntimeError('Iron Hands rites missing')
# wipe all visibility modifiers on rites, preserve max constraints/rules
wipe(head,'modifiers');wipe(bitter,'modifiers')
hide_show_and(head,'r80-ih-head-show',[('atLeast',1,'roster',LEG)])
hide_show_and(bitter,'r80-ih-bitter-show',[('atLeast',1,'roster',LEG),('atLeast',1,'roster','allegiance-loyalist')])

# 5) Company of Bitter Iron: canonical Immortals are already Troops. Remove obsolete duplicate Rite clone; use canonical unit to satisfy compulsory category.
roleid='r42-role-x-1-effects-company-of-immortals-medusan-immortal-squads-r41-unit-x-0-medusan-immortal-squad'
role=byid(cr,roleid)
if role is not None:remove_node(cr,role)
# Ferrus exclusion: remove old duplicate rite modifiers then add one clean one.
mods=fer.find(C('modifiers'))
if mods is not None:
    for m in list(mods):
        if 'bitter' in (m.get('id') or '').lower():mods.remove(m)
m=ET.SubElement(ensure(fer,'modifiers'),C('modifier'),{'id':'r80-ih-bitter-hide-ferrus','type':'set','value':'true','field':'hidden'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':BITTER,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
# compulsory hidden category on canonical Immortal; min 1 only while Rite is selected.
CATID='r80-ih-bitter-comp';ces=ensure(gr,'categoryEntries',G);cat=byid(gr,CATID)
if cat is None:cat=ET.SubElement(ces,G('categoryEntry'),{'id':CATID,'name':'Company of Bitter Iron — compulsory Medusan Immortal','hidden':'true'})
# add category to canonical Immortals
cls=ensure(byid(cr,IMM),'categoryLinks');
if not any(x.get('targetId')==CATID for x in cls):ET.SubElement(cls,C('categoryLink'),{'id':'r80-ih-bitter-imm-cat','name':'Company of Bitter Iron — compulsory Medusan Immortal','hidden':'false','targetId':CATID,'primary':'false'})
force=byid(gr,'force-standard');fl=ensure(force,'categoryLinks',G);cl=next((x for x in fl.findall(G('categoryLink')) if x.get('targetId')==CATID),None)
if cl is None:cl=ET.SubElement(fl,G('categoryLink'),{'id':'r80-ih-bitter-comp-link','name':'Company of Bitter Iron — compulsory Medusan Immortal','hidden':'true','targetId':CATID})
wipe(cl,'constraints',G);c=con(cl,'r80-ih-bitter-comp-min','min',0,Q=G);wipe(cl,'modifiers',G);mo=ET.SubElement(ensure(cl,'modifiers',G),G('modifier'),{'id':'r80-ih-bitter-comp-set','type':'set','value':'1','field':c.get('id')});cs=ET.SubElement(mo,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':BITTER,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# 6) Head of the Gorgon: clean Fast Attack max and enforce no more than one non-Forge-Lord Consul.
fast=byid(gr,'fl-fast');mx=next((x for x in fast.findall('./'+G('constraints')+'/'+G('constraint')) if x.get('type')=='max'),None)
fm=ensure(fast,'modifiers',G)
for x in list(fm):
    if 'ih-gorgon-fast' in (x.get('id') or '') or 'ih-head-fast' in (x.get('id') or ''):fm.remove(x)
mo=ET.SubElement(fm,G('modifier'),{'id':'r80-ih-head-fast-max','type':'set','value':'1','field':mx.get('id')});cs=ET.SubElement(mo,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
# hidden category for non-Forge-Lord Consuls
CONS='r80-ih-head-nonforge-consul';ces=ensure(gr,'categoryEntries',G);ccat=byid(gr,CONS)
if ccat is None:ccat=ET.SubElement(ces,G('categoryEntry'),{'id':CONS,'name':'Head of the Gorgon — non-Forge-Lord Consuls','hidden':'true'})
consul_count=0
for e in cr.iter(C('selectionEntry')):
    # Consul upgrades live beneath the Centurion Consul group. Exclude Forge Lord and Iron Father branch.
    p=e
    pm={c:p for p in cr.iter() for c in p};anc=pm.get(e);inside=False
    while anc is not None:
        if anc.get('id')=='hq-centurion-consuls':inside=True;break
        anc=pm.get(anc)
    if not inside:continue
    nm=(e.get('name') or '').lower()
    if 'forge lord' in nm or 'iron father' in nm:continue
    cls=ensure(e,'categoryLinks')
    if not any(x.get('targetId')==CONS for x in cls):ET.SubElement(cls,C('categoryLink'),{'id':f'r80-ih-consul-cat-{consul_count}','name':'Head of the Gorgon — non-Forge-Lord Consul','hidden':'false','targetId':CONS,'primary':'false'});consul_count+=1
cfl=next((x for x in fl.findall(G('categoryLink')) if x.get('targetId')==CONS),None)
if cfl is None:cfl=ET.SubElement(fl,G('categoryLink'),{'id':'r80-ih-head-consul-link','name':'Head of the Gorgon — non-Forge-Lord Consuls','hidden':'true','targetId':CONS})
wipe(cfl,'constraints',G);cm=con(cfl,'r80-ih-head-consul-max','max',99,Q=G);wipe(cfl,'modifiers',G);mo=ET.SubElement(ensure(cfl,'modifiers',G),G('modifier'),{'id':'r80-ih-head-consul-set','type':'set','value':'1','field':cm.get('id')});cs=ET.SubElement(mo,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# 7) Repair Scions of Iron visibility conditions on current r79 Land Raiders: explicit Legion + Rite AND.
scions_fixed=0
for e in cr.iter(C('selectionEntry')):
    if not (e.get('id') or '').startswith('r79-ih-scions-'):continue
    if 'land raider' not in (e.get('name') or '').lower():continue
    # keep existing model-count modifier if any, but replace visibility with clean Legion+Rite AND; capacity remains player-visible rule where dynamic count cannot be robustly inferred.
    wipe(e,'modifiers');hide_show_and(e,'r80-ih-scions-show-'+str(scions_fixed),[('atLeast',1,'roster',LEG),('atLeast',1,'roster',HEAD)]);scions_fixed+=1
    add_rule(e,'r80-ih-scions-cap-'+str(scions_fixed),'Scions of Iron — capacity restriction','This Dedicated Transport is only legal for an Iron Hands Infantry unit of ten models or fewer which could normally select a Rhino. Normal Transport Capacity restrictions apply.')

# 8) Head Relics of War: clean existing Autosimulacra links so each becomes free + compulsory only under Head.
autos=0
for l in cr.iter(C('entryLink')):
    if l.get('targetId')!='r44-ih-autosimulacra':continue
    mods=ensure(l,'modifiers')
    for m in list(mods):
        if 'ih-head-auto' in (m.get('id') or ''):mods.remove(m)
    # points modifier applies to target cost in this catalogue pattern
    m=ET.SubElement(mods,C('modifier'),{'id':f'r80-ih-head-auto-free-{autos}','type':'set','value':'0','field':'pts'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    # ensure min constraint exists and set to 1 under rite
    cmin=next((x for x in l.findall('./'+C('constraints')+'/'+C('constraint')) if x.get('type')=='min'),None)
    if cmin is None:cmin=con(l,f'r80-ih-head-auto-min-{autos}','min',0)
    mm=ET.SubElement(mods,C('modifier'),{'id':f'r80-ih-head-auto-force-{autos}','type':'set','value':'1','field':cmin.get('id')});cc=ET.SubElement(mm,C('conditions'));ET.SubElement(cc,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'});autos+=1

# 9) Revisions/cache.
cr.set('revision','80');cr.set('gameSystemRevision','47');gr.set('revision','47')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat':e.set('dataRevision','80')
    elif e.get('filePath')=='Prohammer 30k.gst':e.set('dataRevision','47')
# Validation
for root,label in ((cr,'CAT'),(gr,'GST')):
    d=duplicate_ids(root)
    if d:raise RuntimeError(f'Duplicate IDs {label}: {d[:20]}')
# No standalone grav links remain outside special-weapon groups.
pm={c:p for p in cr.iter() for c in p}
for l in cr.iter(C('entryLink')):
    if l.get('targetId')=='r44-ih-graviton-substitution':
        p=pm.get(l)
        assert p is not None and p.tag==C('entryLinks') and pm.get(p) is not None and pm.get(p).tag==C('selectionEntryGroup') and 'special weapon' in (pm.get(p).get('name') or '').lower(),(l.get('id'),pm.get(p).get('name') if pm.get(p) is not None else None)
assert byid(cr,FERRUS).find('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')+'[@id="r80-ih-ferrus-wargear"]') is not None
assert byid(cr,roleid) is None
ET.indent(ct,space='  ');ET.indent(gt,space='  ');ET.indent(it,space='  ')
ct.write(CAT,encoding='utf-8',xml_declaration=True);gt.write(GST,encoding='utf-8',xml_declaration=True);it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT);ET.parse(GST);ET.parse(IDX)
OUT.write_text(f'''Revision 80 — Iron Hands repair pass\nCAT=80 GST=47\n\nPresentation\n- Removed {removed_source} remaining Iron Hands Source Entry/aggregate dump rules globally.\n\nDangerous Weaponry\n- Removed {len(old_grav)} floating Graviton Gun instead of Flamer links.\n- Added Graviton Gun as an Iron Hands-only choice inside {len(grav_added)} Special Weapons groups which already contain a Flamer.\n\nFerrus Manus\n- Added a real fixed Wargear group: Medusan Carapace, Twin-linked Meltagun, Twin-linked Plasma Gun, Heavy Flamer, Forgebreaker, Living Metal Hands and Frag Grenades.\n- Carapace explicitly carries Cortex Controller and Nuncio Vox rules.\n- Existing Primarch/The Gorgon/Master of the Forge/Forged for War rules and retinues retained.\n\nRites\n- Rebuilt Rite visibility with explicit AND gating.\n- Company of Bitter Iron now uses the canonical 0–1 Medusan Immortal Troops entry rather than a duplicate Troops clone; at least one is mechanically compulsory while the Rite is active.\n- Ferrus is hidden under Company of Bitter Iron.\n- Head of the Gorgon Fast Attack max 1 reasserted.\n- Head of the Gorgon now mechanically limits non-Forge-Lord Consuls to 1 through a hidden validation category ({consul_count} Consul upgrade entries tagged).\n- Scions of Iron repaired on {scions_fixed} current conditional Land Raider entries with explicit Legion X + Rite gating.\n- Relics of War free/compulsory Blessed Autosimulacra reasserted across {autos} existing vehicle links.\n\nValidation\n- No standalone Iron Hands Graviton substitution links remain outside Special Weapons groups.\n- Obsolete Bitter Iron duplicate Troops clone removed.\n- Duplicate-ID and XML parse validation passed.\n''',encoding='utf-8')
print(OUT.read_text())
