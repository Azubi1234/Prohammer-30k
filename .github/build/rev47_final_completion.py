from pathlib import Path
import re
import xml.etree.ElementTree as ET
from collections import Counter

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
ET.register_namespace('',CNS); ET.register_namespace('',GNS)
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot()
top=cr.find(C('selectionEntries')); shared=cr.find(C('sharedSelectionEntries'))
assert top is not None and shared is not None


def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def cby(i): return byid(cr,i)
def gby(i): return byid(gr,i)
def ensure(p,t,ns=CNS):
    q=f'{{{ns}}}{t}'; x=p.find(q)
    if x is None:x=ET.SubElement(p,q)
    return x
def add_cost(e,v): ET.SubElement(ensure(e,'costs'),C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def add_constraint(e,id_,typ,val,scope='parent',children='true'):
    return ET.SubElement(ensure(e,'constraints'),C('constraint'),{'id':id_,'type':typ,'value':str(val),'field':'selections','scope':scope,'shared':'true','includeChildSelections':children,'includeChildForces':'false'})
def add_rule(e,id_,name,text):
    r=ET.SubElement(ensure(e,'rules'),C('rule'),{'id':id_,'name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=text; return r
def condition_mod(e,hide,conds,id_=None):
    a={'type':'set','value':'true' if hide else 'false','field':'hidden'}
    if id_:a['id']=id_
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),a)
    gs=ET.SubElement(m,C('conditionGroups')); g=ET.SubElement(gs,C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(g,C('conditions'))
    for typ,val,scope,ch in conds:
        ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':ch,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return m
def gate(e,legion,extra=()): e.set('hidden','true'); condition_mod(e,False,[('atLeast',1,'roster',legion),*extra])
def shared_up(id_,name,pts,text,roster_max=None,maxv=1):
    old=cby(id_)
    if old is not None:return old
    e=ET.SubElement(shared,C('selectionEntry'),{'id':id_,'name':name,'type':'upgrade','hidden':'false','import':'true'}); add_cost(e,pts); add_constraint(e,id_+'-max','max',maxv)
    if roster_max is not None:add_constraint(e,id_+'-rmax','max',roster_max,'roster')
    add_rule(e,id_+'-rule',name,text); return e
def link(uid,target,id_,legion,extra=(),name=None,maxv=1):
    u=cby(uid); t=cby(target)
    if u is None or t is None:return None
    ls=ensure(u,'entryLinks')
    if any(x.get('id')==id_ for x in ls.findall(C('entryLink'))):return next(x for x in ls.findall(C('entryLink')) if x.get('id')==id_)
    l=ET.SubElement(ls,C('entryLink'),{'id':id_,'name':name or t.get('name'),'type':'selectionEntry','targetId':target,'hidden':'true','import':'true'}); add_constraint(l,id_+'-max','max',maxv); gate(l,legion,extra); return l
def norm(s): return re.sub(r'[^a-z0-9]+',' ',(s or '').lower()).strip()
def set_primary_cat(e,target,name):
    old=e.find(C('categoryLinks'))
    if old is not None:e.remove(old)
    cs=ET.SubElement(e,C('categoryLinks')); ET.SubElement(cs,C('categoryLink'),{'id':e.get('id')+'-cat','targetId':target,'name':name,'hidden':'false','primary':'true'})
def find_selectors(root_entry,keywords):
    out=[]
    for e in root_entry.iter():
        n=norm(e.get('name'))
        if any(k in n for k in keywords) and e.get('id') and e.tag in (C('selectionEntry'),C('entryLink')): out.append(e.get('id'))
    return list(dict.fromkeys(out))

# Clean this pass on safe re-run.
for p in list(cr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r47-'):p.remove(x)
for p in list(gr.iter()):
    for x in list(p):
        if x.get('id','').startswith('r47-'):p.remove(x)

# V — WHITE SCARS: source-final Horsetail Talisman.
ws_tail=shared_up('r47-ws-horsetail-talisman','Horsetail Talisman',25,'One White Scars Independent Character only; 0–1 per army. Once per battle, at the beginning of the White Scars Shooting phase, reveal the Talisman. The bearer and every friendly White Scars non-vehicle unit with at least one model within 6” may choose to move D6” instead of shooting. Bike and Jetbike units may also make this movement. A unit making this move may not move within 1” of an enemy, must maintain coherency and may not charge that turn. Falling Back, embarked or locked units may not benefit.',1)
for uid in ['hq-praetor','hq-centurion']:
    link(uid,ws_tail.get('id'),f'r47-{uid}-ws-horsetail','legion-v')

# X — IRON HANDS: unit Bionics and Splinter Bolts from the final Legion document.
ih_bionics=shared_up('r47-ih-bionics-model','Bionics — unit model',3,'Iron Hands Infantry unit upgrade. Every model in the unit must receive Bionics. Select this +3-point entry once for each non-Veteran-Sergeant model in the unit. A Veteran Sergeant instead pays +5 points using the separate Sergeant entry. Models already equipped with Bionics receive no additional benefit. Iron Hands Bionics recover on 5+ rather than 6+.',None,20)
ih_bionics_sgt=shared_up('r47-ih-bionics-veteran-sergeant','Bionics — Veteran Sergeant',5,'Veteran Sergeant price when the whole Iron Hands Infantry unit purchases Bionics. The entire unit must be upgraded; models already equipped with Bionics receive no additional benefit. Iron Hands Bionics recover on 5+ rather than 6+.',None,1)
ih_splinter=shared_up('r47-ih-splinter-bolts','Splinter Bolts',5,'Iron Hands Infantry unit equipped with Bolters. Wounds caused by the unit’s Bolters ignore Feel No Pain. Bolters means Bolters, Combi-Bolters, Twin-linked Bolters and the Bolter component of Combi-Weapons. Splinter Bolts may not combine with Special Issue Ammunition or another ammunition upgrade. A Legion Tactical Squad may not use Fury of the Legion in a Shooting phase in which it fires Splinter Bolts.')
# Eligible common Infantry plus Iron Hands-specific Infantry. Bionics is broader; Splinter Bolts only where bolt weapons are part of the unit package.
infantry=['tactical-unit','breacher-unit','recon-unit','veteran-unit','terminator-unit','destroyer-unit','fa-seeker','hs-heavy-support-squad','r41-unit-x-0-medusan-immortal-squad','r41-unit-x-1-gorgon-terminator-squad','r41-unit-x-2-morlock-terminator-squad']
for uid in infantry:
    if cby(uid):
        link(uid,ih_bionics.get('id'),f'r47-{uid}-ih-bionics','legion-x',maxv=20)
        # Sergeant surcharge is exposed only on squads that can contain a Veteran Sergeant; the rule text handles exceptions.
        if uid in ['tactical-unit','breacher-unit','recon-unit','veteran-unit','terminator-unit','destroyer-unit','fa-seeker','hs-heavy-support-squad']:
            link(uid,ih_bionics_sgt.get('id'),f'r47-{uid}-ih-bionics-sgt','legion-x')
for uid in ['tactical-unit','breacher-unit','recon-unit','veteran-unit','terminator-unit','fa-seeker','r41-unit-x-1-gorgon-terminator-squad','r41-unit-x-2-morlock-terminator-squad']:
    if cby(uid):link(uid,ih_splinter.get('id'),f'r47-{uid}-ih-splinter','legion-x')

# X — CASTRMEN ORTH. Orth is represented as the HQ portion of the source's +50-point Tank Commander upgrade;
# the commanded Tank remains selected in its own normal FOC slot.
orth=ET.SubElement(top,C('selectionEntry'),{'id':'r47-ih-castrmen-orth','name':'Castrmen Orth — Tank Commander Upgrade','type':'upgrade','hidden':'true','import':'true'})
add_cost(orth,50); add_constraint(orth,'r47-ih-castrmen-orth-max','max',1,'roster'); set_primary_cat(orth,'cat-hq','HQ'); gate(orth,'legion-x')
add_rule(orth,'r47-ih-castrmen-orth-rule','Castrmen Orth','Purchase Castrmen Orth as a +50 point upgrade for one Iron Hands Vehicle (Tank) in the army. Select that Vehicle separately in its normal Force Organisation slot; Orth also occupies one HQ selection. Orth may not command a Walker, a Vehicle without a Ballistic Skill characteristic, or a Vehicle already commanded by another named character. The commanded Vehicle has Ballistic Skill 5 and Tank Hunters. If the Vehicle is destroyed, Orth is also slain for Victory Point and mission purposes. Orth is not a separate model and may not leave his Vehicle.')

# XV — THOUSAND SONS: Prosperine Æther-Disc.
ts_disc=shared_up('r47-ts-prosperine-aether-disc','Prosperine Æther-Disc',30,'Thousand Sons Independent Character wearing Power Armour or Artificer Armour only. The bearer becomes Jump Infantry and gains Turbo-Boosters and Hammer of Wrath. Ætheric Evasion: if the bearer moved at least 6” in its preceding Movement phase, enemy models suffer -1 To Hit the bearer in close combat, to a maximum required roll of 6+. Lost while Falling Back. May not be combined with a Jump Pack, Bike, Jetbike or any form of Terminator Armour.')
for uid in ['hq-praetor','hq-centurion']:
    l=link(uid,ts_disc.get('id'),f'r47-{uid}-ts-disc','legion-xv')
    if l is not None:
        u=cby(uid)
        blockers=find_selectors(u,['jump pack','bike','jetbike','terminator armour','cataphractii','tartaros'])
        for j,b in enumerate(blockers): condition_mod(l,True,[('atLeast',1,'root-entry',b)],f'r47-{uid}-ts-disc-block-{j}')

# XVII — WORD BEARERS: Favour of the Pantheon, exactly as in the final source.
# A hidden category enforces one Favour across the army, irrespective of which eligible IC buys it.
cats=ensure(gr,'categoryEntries',GNS)
if gby('r47-cat-wb-favour') is None: ET.SubElement(cats,G('categoryEntry'),{'id':'r47-cat-wb-favour','name':'Word Bearers Favour of the Pantheon Limit','hidden':'true'})
force=gby('force-standard'); assert force is not None
fl=ensure(force,'categoryLinks',GNS)
cl=ET.SubElement(fl,G('categoryLink'),{'id':'r47-fl-wb-favour','name':'Word Bearers Favour Limit','targetId':'r47-cat-wb-favour','hidden':'true'})
gcs=ET.SubElement(cl,G('constraints')); ET.SubElement(gcs,G('constraint'),{'id':'r47-wb-favour-roster-max','field':'selections','scope':'roster','value':'1','type':'max','shared':'true','includeChildSelections':'true','includeChildForces':'false'})
favours=[
 ('aura','Daemonic Aura',15,'The model gains a 5+ Invulnerable Save.'),
 ('mutation','Daemonic Mutation',15,'The model gains +1 Attack.'),
 ('strength','Daemonic Strength',10,'The model gains +1 Strength.'),
 ('wings','Daemonic Wings',20,'The model becomes Jump Infantry. This may not be combined with a Jump Pack, Bike, Jetbike or Terminator Armour.'),
 ('visage','Daemonic Visage',5,'An enemy unit which loses a close combat involving the bearer suffers an additional -1 Leadership when taking the resulting Morale test.'),
]
for code,name,pts,text in favours:
    it=shared_up(f'r47-wb-favour-{code}',name,pts,text)
    cs=ensure(it,'categoryLinks'); ET.SubElement(cs,C('categoryLink'),{'id':f'r47-wb-favour-{code}-cat','targetId':'r47-cat-wb-favour','name':'Favour of the Pantheon','hidden':'false','primary':'false'})
    for uid in ['hq-praetor','hq-centurion']:
        l=link(uid,it.get('id'),f'r47-{uid}-wb-favour-{code}','legion-xvii',name='Favour of the Pantheon — '+name)
        if l is not None and code=='wings':
            blockers=find_selectors(cby(uid),['jump pack','bike','jetbike','terminator armour','cataphractii','tartaros'])
            for j,b in enumerate(blockers): condition_mod(l,True,[('atLeast',1,'root-entry',b)],f'r47-{uid}-wb-wings-block-{j}')

# ---------- LEGACY REFERENCE REPAIR ----------
# Resolve the two obsolete generic weapon target IDs against the actual current shared armoury entries.
def generic_shared_exact(name):
    cand=[e for e in shared.findall(C('selectionEntry')) if norm(e.get('name'))==norm(name)]
    preferred=[e for e in cand if not e.get('id','').startswith('r') and not e.get('id','').startswith('da')]
    if len(preferred)==1:return preferred[0].get('id')
    if len(cand)==1:return cand[0].get('id')
    if preferred:return preferred[0].get('id')
    raise AssertionError(('No unambiguous generic target',name,[(x.get('id'),x.get('name')) for x in cand]))
legacy_targets={'gear-chainaxe':generic_shared_exact('Chainaxe'),'gear-pair-lightning-claws':generic_shared_exact('Pair of Lightning Claws')}
retargeted=[]
for e in cr.iter():
    old=e.get('targetId')
    if old in legacy_targets:
        e.set('targetId',legacy_targets[old]); retargeted.append((e.get('id'),old,legacy_targets[old]))

# A broken child condition can never become true because its referenced selection no longer exists.
# Preserve that semantics: an impossible AND/plain modifier is removed; an impossible arm of an explicit OR is removed.
def parent_map(root): return {c:p for p in root.iter() for c in p}
def ancestor(e,pm,tag):
    x=e
    while x in pm:
        x=pm[x]
        if x.tag==tag:return x
    return None
ids={e.get('id') for e in cr.iter() if e.get('id')}|{e.get('id') for e in gr.iter() if e.get('id')}
pm=parent_map(cr); badconds=[e for e in cr.iter() if e.get('childId') and e.get('childId') not in ids]
removed_mods=set(); removed_or=[]; removed_other=[]
for e in badconds:
    # It may already have disappeared with a modifier removed earlier.
    pm=parent_map(cr)
    if e not in pm:continue
    cg=ancestor(e,pm,C('conditionGroup'))
    if cg is not None and cg.get('type')=='or':
        p=pm.get(e)
        if p is not None:p.remove(e); removed_or.append(e.get('childId'))
        continue
    mod=ancestor(e,pm,C('modifier'))
    if mod is not None:
        p=pm.get(mod)
        if p is not None and id(mod) not in removed_mods:p.remove(mod); removed_mods.add(id(mod))
    else:
        p=pm.get(e)
        if p is not None:p.remove(e); removed_other.append(e.get('childId'))

# Final revisions. GST changes because Revision 47 adds the hidden Favour category/force limit.
cr.set('revision','47'); gr.set('revision','19'); cr.set('gameSystemRevision','19')

# Whole-repository structural validation before writing.
def validate():
    allids=[]
    for root,label in [(cr,'CAT'),(gr,'GST')]:
        xs=[e.get('id') for e in root.iter() if e.get('id')]; dup=[x for x,n in Counter(xs).items() if n>1]
        assert not dup,(label,'duplicate IDs',dup[:30]); allids.extend(xs)
    ids=set(allids); broken=[]
    for e in cr.iter():
        for a in ('targetId','childId'):
            v=e.get(a)
            if v and v not in ids:broken.append((e.get('id'),e.get('name'),a,v))
    assert not broken,('broken refs remain',broken[:50])
    for req in ['r47-ws-horsetail-talisman','r47-ih-splinter-bolts','r47-ih-bionics-model','r47-ih-castrmen-orth','r47-ts-prosperine-aether-disc','r47-wb-favour-aura','r47-wb-favour-wings']:
        assert cby(req) is not None,req
    assert cr.get('gameSystemRevision')==gr.get('revision')
    assert not [e for e in top.findall(C('selectionEntry')) if 'experimental wargear' in norm(e.get('name')) or 'experimental units' in norm(e.get('name'))]
    return len(retargeted),len(badconds)
fixed_targets,fixed_children=validate()
ct.write(CAT,encoding='UTF-8',xml_declaration=True); gt.write(GST,encoding='UTF-8',xml_declaration=True)
print(f'REV47 COMPLETE: retargeted={fixed_targets}; broken child conditions repaired={fixed_children}; CAT=47 GST=19')
