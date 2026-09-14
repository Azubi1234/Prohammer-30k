import importlib.util, copy, re, unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

NS='http://www.battlescribe.net/schema/catalogueSchema'; Q=lambda t:f'{{{NS}}}{t}'
CAT=Path('Legiones Astartes.cat')
spec=importlib.util.spec_from_file_location('r25','.github/build/rev25_apply.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
tree=ET.parse(CAT); root=tree.getroot(); top=root.find(Q('selectionEntries'))

def norm(s):
    s=unicodedata.normalize('NFKD',s or '').encode('ascii','ignore').decode('ascii').lower()
    s=re.sub(r'\b(legion|squad|squads|squadron|squadrons|team|teams|cabal|cabals|cohort|cohorts|terminator|terminators|the)\b',' ',s)
    return re.sub(r'[^a-z0-9]+',' ',s).strip()
def byid(i): return next((e for e in root.iter() if e.get('id')==i),None)
def child(p,t):
    x=p.find(Q(t))
    if x is None: x=ET.SubElement(p,Q(t))
    return x
def add_hide_unless(e,selector,prefix):
    mods=child(e,'modifiers'); md=ET.SubElement(mods,Q('modifier'),{'type':'set','value':'true','field':'hidden','id':prefix+'-hide'})
    cs=ET.SubElement(md,Q('conditions')); ET.SubElement(cs,Q('condition'),{'type':'lessThan','value':'1','field':'selections','scope':'roster','childId':selector,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def rewrite_ids(node,prefix):
    old_to_new={}
    for x in node.iter():
        if x.get('id'):
            old=x.get('id'); new=prefix+'-'+re.sub(r'[^A-Za-z0-9_-]+','-',old)[:90]
            k=1; base=new
            while new in old_to_new.values(): k+=1; new=f'{base}-{k}'
            old_to_new[old]=new; x.set('id',new)
    for x in node.iter():
        for a in ('targetId','childId'):
            if x.get(a) in old_to_new: x.set(a,old_to_new[x.get(a)])
def set_category(e,catid,name):
    links=child(e,'categoryLinks')
    for x in list(links): links.remove(x)
    ET.SubElement(links,Q('categoryLink'),{'id':e.get('id')+'-cat','name':name,'hidden':'false','targetId':catid,'primary':'true'})
def add_rule(e,rid,name,text):
    rules=child(e,'rules'); r=ET.SubElement(rules,Q('rule'),{'id':rid,'name':name,'hidden':'false'}); ET.SubElement(r,Q('description')).text=text
def clone_to_troops(base,rite_id,prefix,rule_text):
    c=copy.deepcopy(base); rewrite_ids(c,prefix); c.set('hidden','true'); set_category(c,'cat-troops','Troops'); add_hide_unless(c,rite_id,prefix)
    add_rule(c,prefix+'-rite-note','Rite of War Interaction',rule_text); top.append(c); return c

core_alias={'tactical':'tactical-unit','breacher siege':'breacher-unit','breacher':'breacher-unit','veteran':'veteran-unit','terminator':'terminator-unit','assault':'assault-unit','bike':'fa-bike','sky hunter jetbike':'fa-sky-hunter','sky hunter':'fa-sky-hunter','attack bike':'fa-attack-bike','reconnaissance':'recon-unit','recon':'recon-unit','seeker':'fa-seeker','destroyer':'destroyer-unit','heavy support':'hs-heavy-support-squad','predator strike':'hs-predator','predator':'hs-predator','artillery tank':'hs-artillery','dreadnought':'dreadnought-unit','contemptor':'contemptor-unit'}
def source_unit(L,phrase):
    np=norm(phrase); scored=[]
    for idx,e in enumerate(L.get('entries',[])):
        ne=norm(e.get('title'))
        if np==ne or np in ne or ne in np:
            u=byid(f"r41-unit-{m.slug(L['roman'])}-{idx}-{m.slug(e['title'])}")
            if u is not None: scored.append((abs(len(ne)-len(np)),u))
    if scored: return sorted(scored,key=lambda x:x[0])[0][1]
    for k,i in sorted(core_alias.items(),key=lambda kv:-len(kv[0])):
        if k in np: return byid(i)
    return None

for p in list(root.iter()):
    for x in list(p):
        if x.get('id','').startswith('r42-role-'): p.remove(x)
report=[]; made=0; missing=[]
for L in m.LEGIONS:
    if L['roman']=='I': continue
    for ri,rite in enumerate(L.get('rites',[])):
        rid=f"r25-rite-{m.slug(L['roman'])}-{ri}-{m.slug(rite['title'])}"
        if byid(rid) is None: raise RuntimeError('Missing rite '+rid)
        text=' '.join((rite.get('text') or '').split())
        pats=[r'([A-Z][A-Za-z0-9’\'\- ]{2,90}?(?:Squads?|Squadrons?|Cabals?|Teams?|Cohorts?|Terminators?)) may be selected as (?:non-compulsory )?Troops choices',r'One ([A-Z][A-Za-z0-9’\'\- ]{2,90}?(?:Squadron|Squad|Cabal|Team|Cohort)) may be selected as a non-compulsory Troops choice']
        phrases=[]
        for pat in pats: phrases += re.findall(pat,text,re.I)
        expanded=[]
        for ph in phrases:
            for q in re.split(r'\s+and\s+(?=Legion|[A-Z])',ph): expanded.append(q.strip())
        seen=set()
        for ph in expanded:
            key=norm(ph)
            if not key or key in seen: continue
            seen.add(key); base=source_unit(L,ph)
            if base is None: missing.append((L['roman'],rite['title'],ph)); continue
            prefix=f"r42-role-{m.slug(L['roman'])}-{ri}-{m.slug(ph)}"
            clone_to_troops(base,rid,prefix,rite.get('text') or '')
            made+=1; report.append(f"{L['roman']} | {rite['title']} | Troops: {ph} <- {base.get('name')} ({base.get('id')})")
        if L['roman']=='XV' and 'GUARD OF THE CRIMSON KING' in rite['title'].upper():
            magnus=source_unit(L,'Magnus the Red')
            if magnus is not None:
                c=copy.deepcopy(magnus); prefix='r42-role-xv-crimson-magnus-hq'; rewrite_ids(c,prefix); c.set('hidden','true'); set_category(c,'cat-hq','HQ'); add_hide_unless(c,rid,prefix); add_rule(c,prefix+'-note','The Bidding of the Crimson King','Magnus the Red may fulfil a compulsory HQ selection when using this Rite and does not occupy a Lord of War selection.'); top.append(c); made+=1; report.append('XV | Guard of the Crimson King | Magnus the Red -> HQ')
root.set('revision','42')
comment=root.find(Q('comment'))
if comment is not None: comment.text='Revision 42: Remaining Legion source packages plus functional Rite-of-War battlefield-role transformations, retaining the completed Dark Angels implementation and excluding Experimental Wargear and Units.'
tree.write(CAT,encoding='UTF-8',xml_declaration=True)
Path('inspection-r42-rite-roles.txt').write_text('\n'.join(report+['','MISSING:']+[repr(x) for x in missing]),encoding='utf-8')
print('R42 ROLE TRANSFORMS',made,'missing',len(missing))
