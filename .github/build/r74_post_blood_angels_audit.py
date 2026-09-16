from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); OUT=Path('inspection-r74-blood-angels-post.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot(); PM={c:p for p in cr.iter() for c in p}
assert cr.get('revision')=='74' and gr.get('revision')=='42'
L=[]; a=L.append
IDS={
'dawn':'r41-unit-ix-0-dawnbreaker-cohort','pal':'r41-unit-ix-1-crimson-paladin-squad','tears':'r41-unit-ix-2-angel-s-tears-squad','ofanim':'r41-unit-ix-3-ofanim-court','grav':'r41-unit-ix-4-grav-chariot-squadron','guard':'r41-unit-ix-5-sanguinary-guard','ral':'r41-unit-ix-6-raldoron-the-blooded','zephon':'r41-unit-ix-7-dominion-zephon','crohne':'r41-unit-ix-8-aster-crohne','azk':'r41-unit-ix-9-azkaellon','amit':'r41-unit-ix-10-nassir-amit-the-flesh-tearer','sang':'r41-unit-ix-11-ix-sanguinius-the-great-angel'}

def byid(root,i):return next((e for e in root.iter() if e.get('id')==i),None)
def cost(e):
    cs=e.find(C('costs'));return [x.get('value') for x in cs.findall(C('cost'))] if cs is not None else []
def cons(e,T=C):
    cs=e.find(T('constraints'));return [(x.get('id'),x.get('type'),x.get('value'),x.get('field'),x.get('scope')) for x in cs.findall(T('constraint'))] if cs is not None else []
def rules(e):return [x.get('name') for x in e.findall('./'+C('rules')+'/'+C('rule'))]
def mods(e,T=C):
    out=[];ms=e.find(T('modifiers'))
    if ms is not None:
        for m in ms.findall(T('modifier')):
            out.append((m.get('id'),m.get('type'),m.get('field'),m.get('value'),[(c.get('type'),c.get('value'),c.get('scope'),c.get('childId')) for c in m.findall('.//'+T('condition'))],[(r.get('value'),r.get('scope'),r.get('childId')) for r in m.findall('.//'+T('repeat'))]))
    return out
def cats(e):
    cs=e.find(C('categoryLinks'));return [(x.get('name'),x.get('targetId'),x.get('primary')) for x in cs.findall(C('categoryLink'))] if cs is not None else []
def models(e):return [x for x in e.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if x.get('type')=='model']
def owner(e):
    p=e
    while p is not None:
        if p.tag==C('selectionEntry') and p.get('type')=='unit':return p
        p=PM.get(p)
    return None

A={k:byid(cr,v) for k,v in IDS.items()}
assert all(A.values())
a('=== CANONICAL BLOOD ANGELS PRESENTATION ===')
for k,u in A.items():
    src=[r for r in u.findall('./'+C('rules')+'/'+C('rule')) if (r.get('name') or '').lower().startswith('source entry') or (r.get('name') or '').lower()=='special rules']
    top_profiles=u.findall('./'+C('profiles')+'/'+C('profile'))
    a(f"{k}: hidden={u.get('hidden')} top_profiles={len(top_profiles)} source_or_aggregate_rules={len(src)} models={[ (m.get('name'),m.get('defaultAmount'),cost(m),cons(m)) for m in models(u)]} rules={rules(u)}")
    assert not src and not top_profiles

# Expected model sizes/costs.
expected={'dawn':(5,10,35),'pal':(3,5,45),'tears':(5,10,30),'ofanim':(3,5,50),'guard':(3,6,55)}
for k,(mn,mx,pts) in expected.items():
    m=models(A[k])[0]; d={x[1]:float(x[2]) for x in cons(m) if x[1] in ('min','max')}; pc=float(cost(m)[0]); assert d['min']==mn and d['max']==mx and pc==pts
# Grav 1-3.
gm=byid(cr,'r74-ba-grav-models'); assert gm is not None; d={x[1]:float(x[2]) for x in cons(gm)}; assert d['min']==1 and d['max']==3 and float(cost(gm)[0])==65
assert A['guard'].get('hidden')=='true' and A['azk'].get('hidden')=='true'

# Scaling options and per-five caps.
a('\n=== SCALING / CAP CHECKS ===')
for oid in ('r41-unit-ix-0-dawnbreaker-cohort-opt-2-krak-grenades','r41-unit-ix-0-dawnbreaker-cohort-opt-3-melta-bombs','r41-unit-ix-2-angel-s-tears-squad-opt-4-krak-grenades','r41-unit-ix-2-angel-s-tears-squad-opt-5-melta-bombs','r41-unit-ix-5-sanguinary-guard-opt-1-krak-grenades','r41-unit-ix-5-sanguinary-guard-opt-2-melta-bombs'):
    e=byid(cr,oid);a(f'{oid}: cost={cost(e)} mods={mods(e)}');assert e is not None and (not cost(e) or float(cost(e)[0])==0) and any(x[1]=='increment' and x[5] for x in mods(e))
for gid in ('r74-ba-tears-special','r74-ba-pal-heavy'):
    g=byid(cr,gid);a(f'{gid}: cons={cons(g)} mods={mods(g)} entries={[x.get("name") for x in g.findall("./"+C("selectionEntries")+"/"+C("selectionEntry"))]}');assert g is not None

# Armoury and Consul.
a('\n=== ARMOURY / CONSUL ===')
rh=byid(cr,'transport-rhino');dam=byid(cr,'hq-damocles');cont=byid(cr,'contemptor-unit');pr=byid(cr,'r25-consul-ix-sanguinary-high-priest-consul')
for u,label in ((rh,'Rhino'),(dam,'Damocles'),(cont,'Contemptor'),(pr,'High Priest')):
    if u is None:continue
    hits=[(x.get('id'),x.get('name'),x.get('targetId'),mods(x)) for x in u.iter(C('entryLink')) if 'ba-' in (x.get('id') or '') or 'Inferno' in (x.get('name') or '') or 'Furioso' in (x.get('name') or '') or 'Over-charged' in (x.get('name') or '')]
    a(f'{label}: links={hits} rules={rules(u)}')
assert any(x.get('targetId')=='r44-ba-overcharged-engines' for x in rh.iter(C('entryLink')))
assert dam is None or not any(x.get('targetId')=='r44-ba-overcharged-engines' for x in dam.iter(C('entryLink')))
assert pr is not None and {'Legion Support Officer','Apothecarion','Sanguinius’ Chosen'} <= set(rules(pr))

# Retinues and character model children.
a('\n=== CHARACTERS / RETINUES ===')
for k in ('ral','zephon','crohne','amit','sang'):
    u=A[k]; rgs=[(g.get('id'),g.get('name'),[x.get('name') for x in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry'))]) for g in u.iter(C('selectionEntryGroup')) if 'retinue' in (g.get('name') or '').lower()]
    a(f'{k}: models={[m.get("name") for m in models(u)]} retinues={rgs}')
    assert models(u)
# Praetor Sanguinary Guard access.
pra=byid(cr,'hq-praetor'); assert pra is not None
pguard=[x for x in pra.iter(C('selectionEntry')) if x.get('name')=='Sanguinary Guard Squad' and (x.get('id') or '').startswith('r74-ba-pra-')]
a(f'Praetor Sanguinary Guard clones={[(x.get("id"),x.get("hidden"),mods(x)) for x in pguard]}');assert pguard

# Rites.
a('\n=== RITES ===')
rv=byid(cr,'r74-ba-rev-vet-veteran-unit');assert rv is not None
a(f'Revelation Veteran: hidden={rv.get("hidden")} cats={cats(rv)} mods={mods(rv)}')
assert any(c[1]=='cat-troops' and c[2]=='true' for c in cats(rv))
for cid in ('r74-ba-cat-revelation-comp','r74-ba-cat-sorrows-comp'):
    ce=byid(gr,cid); assert ce is not None; link=byid(gr,'r74-ba-fl-'+cid); assert link is not None
    a(f'{cid}: force_constraints={cons(link,G)} mods={mods(link,G)}')
heavy=byid(gr,'fl-heavy'); a(f'Heavy Support BA mods={[x for x in mods(heavy,G) if "r74-ba" in (x[0] or "")]}');assert any(x[0]=='r74-ba-rev-heavy-max' for x in mods(heavy,G))

# Sanguinius explicit checks.
a('\n=== SANGUINIUS ===')
sa=A['sang'];a(f'rules={rules(sa)} wargear={[x.get("name") for x in sa.findall("./"+C("selectionEntries")+"/"+C("selectionEntry"))]}')
assert {'Primarch','Legiones Astartes (Blood Angels)','Angelic Charge','Sire of the Blood Angels','The Angel Descends'} <= set(rules(sa))
assert any(c[3]=='allegiance-loyalist' for m in mods(sa) for c in m[4])

# Investigate remaining enforceable requirements for follow-up.
a('\n=== CONTEMPTOR DCCW STRUCTURE ===')
if cont is not None:
    for g in cont.iter(C('selectionEntryGroup')):
        n=(g.get('name') or '').lower()
        if 'weapon' in n or 'arm' in n or 'fist' in n or 'close combat' in n:
            a(f'GROUP {g.get("id")} {g.get("name")} cons={cons(g)} mods={mods(g)}')
            for e in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')):a(f'  ENTRY {e.get("id")} {e.get("name")} cost={cost(e)} cons={cons(e)} mods={mods(e)}')
            for e in g.findall('./'+C('entryLinks')+'/'+C('entryLink')):a(f'  LINK {e.get("id")} {e.get("name")} -> {e.get("targetId")} cons={cons(e)} mods={mods(e)}')

# Warlord / Jump Pack structure useful for Revelation enforcement.
a('\n=== WARLORD / JUMP-PACK STRUCTURE ===')
for e in cr.iter(C('selectionEntry')):
    n=(e.get('name') or '').lower();i=e.get('id') or ''
    if 'warlord' in n or i=='warlord' or ('jump pack' in n and owner(e) is not None and owner(e).get('id') in ('hq-praetor','hq-centurion')):
        o=owner(e);a(f'{e.tag.split("}")[-1]} {i} {e.get("name")} owner={o.get("id") if o is not None else ""} cons={cons(e)} mods={mods(e)}')

OUT.write_text('\n'.join(L),encoding='utf-8');print('\n'.join(L))
