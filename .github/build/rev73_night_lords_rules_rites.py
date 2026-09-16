from pathlib import Path
import re
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r73-night-lords-rules-rites.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS); ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()
if cr.get('revision')!='72' or gr.get('revision')!='40': raise RuntimeError(f'Expected CAT72/GST40 baseline, got CAT{cr.get("revision")}/GST{gr.get("revision")}')

LEG='legion-viii'; TA='r25-rite-viii-0-terror-assault'; HC='r25-rite-viii-1-horror-cult'
IDS={
 'terror':'r41-unit-viii-0-terror-squad','raptor':'r41-unit-viii-1-night-raptor-squad','contekar':'r41-unit-viii-2-contekar-terminator-elite','atramentar':'r41-unit-viii-3-atramentar-flay-clade',
 'sevatar':'r41-unit-viii-4-jago-sevatarion','ophion':'r41-unit-viii-5-kheron-ophion','malcharion':'r41-unit-viii-6-malcharion-the-war-sage','shang':'r41-unit-viii-7-shang','mawdrym':'r41-unit-viii-8-flaymaster-mawdrym-llansahai','curze':'r41-unit-viii-9-viii-konrad-curze-the-night-haunter'}

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t,ns=CNS):
    Q=C if ns==CNS else (G if ns==GNS else I); x=p.find(Q(t))
    if x is None:x=ET.SubElement(p,Q(t))
    return x
def set_points(e,v):
    cs=ensure(e,'costs'); [cs.remove(x) for x in list(cs)]; ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def constraint(p,i,typ,val,field='selections',scope='parent',child=False,ns=CNS):
    Q=C if ns==CNS else G
    return ET.SubElement(ensure(p,'constraints',ns),Q('constraint'),{'id':i,'type':typ,'value':str(val),'field':field,'scope':scope,'shared':'true','includeChildSelections':'true' if child else 'false','includeChildForces':'false'})
def add_rule(p,i,n,text):
    rs=ensure(p,'rules'); old=next((x for x in rs.findall(C('rule')) if x.get('id')==i),None)
    if old is not None:rs.remove(old)
    r=ET.SubElement(rs,C('rule'),{'id':i,'name':n,'hidden':'false'}); ET.SubElement(r,C('description')).text=text; return r
def add_entry(p,i,n,cost=0,typ='upgrade',default=None,minv=None,maxv=1):
    e=ET.SubElement(ensure(p,'selectionEntries'),C('selectionEntry'),{'id':i,'name':n,'type':typ,'hidden':'false','import':'true',**({'defaultAmount':str(default)} if default is not None else {})});set_points(e,cost)
    if minv is not None:constraint(e,i+'-min','min',minv)
    if maxv is not None:constraint(e,i+'-max','max',maxv)
    return e
def hide_if_missing(e,i,child,scope='roster'):
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'true','field':'hidden'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'lessThan','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def show_if_all(e,i,conds):
    e.set('hidden','true');m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'});gs=ET.SubElement(m,C('conditionGroups'));cg=ET.SubElement(gs,C('conditionGroup'),{'type':'and'});cs=ET.SubElement(cg,C('conditions'))
    for typ,val,scope,child in conds:ET.SubElement(cs,C('condition'),{'type':typ,'value':str(val),'field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def remove_prefixed(root,prefix):
    for p in list(root.iter()):
        for x in list(p):
            if (x.get('id') or '').startswith(prefix):p.remove(x)
def slug(s):return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def direct_models(u):return [x for x in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if x.get('type')=='model']
def direct_rules(u):return u.findall('./'+C('rules')+'/'+C('rule'))
def remove_direct_rule_names(u,names):
    rs=u.find(C('rules'))
    if rs is None:return 0
    names={x.lower() for x in names};n=0
    for r in list(rs):
        if (r.get('name') or '').lower() in names:rs.remove(r);n+=1
    if len(rs)==0:u.remove(rs)
    return n

def matching_units(canon):
    return [u for u in cr.iter(C('selectionEntry')) if u.get('type')=='unit' and canon in (u.get('id') or '')]

def rule_once(u,prefix,name,text):
    # remove any previous same-named R73 local rule, then add one exact rule block
    rs=ensure(u,'rules')
    for r in list(rs):
        if (r.get('id') or '').startswith('r73-nl-rule-') and (r.get('name') or '')==name:rs.remove(r)
    return add_rule(u,f'r73-nl-rule-{prefix}-{slug(name)}',name,text)

# Safe rerun hygiene for developer reruns.
remove_prefixed(cr,'r73-nl-'); remove_prefixed(gr,'r73-nl-')

# ---------- 1. PRESENT ACTUAL RULES, NOT A SYNTHETIC "SPECIAL RULES" SOURCE DUMP ----------
COMMON={
 'Legiones Astartes (Night Lords)':'This model belongs to the VIII Legion and is affected by rules and effects which refer to Legiones Astartes (Night Lords).',
 'Independent Character':'Uses the normal ProHammer Independent Character rules.',
 'Master of the Legion':'This model has the Master of the Legion special rule and counts toward all normal Master of the Legion restrictions.',
 'Psyker (Mastery Level 1)':'This model is a Psyker with Mastery Level 1 and follows the normal ProHammer psychic rules.',
 'Infiltrate':'The unit uses the ProHammer Infiltrate special rule. If its mission or transport circumstances do not permit Infiltrate, deploy it normally.',
 'Preferred Enemy (Infantry)':'The unit has Preferred Enemy against Infantry and uses the normal ProHammer Preferred Enemy rules against eligible Infantry targets.',
 'Preferred Enemy (Independent Characters)':'The model has Preferred Enemy against Independent Characters and uses the normal ProHammer Preferred Enemy rules against eligible Independent Character targets.',
 'Hit & Run':'The unit uses the ProHammer Hit & Run special rule.',
 'Stubborn':'The unit uses the ProHammer Stubborn special rule.',
 'Fearless':'The unit uses the ProHammer Fearless special rule.',
 'Feel No Pain (5+)':'The model has Feel No Pain (5+) and uses the normal ProHammer Feel No Pain rules.',
 'Primarch':'Konrad Curze uses the universal Primarch rules presented in Forces of the Legions.',
 'Stealth':'Konrad Curze has the Stealth special rule as part of Night Haunter.',
}
UNIT_RULES={
 'terror':['Legiones Astartes (Night Lords)','Infiltrate','Preferred Enemy (Infantry)'],
 'raptor':['Legiones Astartes (Night Lords)','Hit & Run'],
 'contekar':['Legiones Astartes (Night Lords)','Stubborn'],
 'atramentar':['Legiones Astartes (Night Lords)','Fearless'],
}
removed_dumps=0; added_actual=0
for key,names in UNIT_RULES.items():
    for u in matching_units(IDS[key]):
        removed_dumps+=remove_direct_rule_names(u,{'Special Rules'})
        # R71 also added source-summary composition/wargear rules. Keep fixed wargear visible, but remove composition prose from Rules.
        remove_direct_rule_names(u,{'Unit Composition'})
        for n in names:rule_once(u,(u.get('id') or key)[-70:],n,COMMON[n]);added_actual+=1
        if key=='atramentar':
            # Teleport Assault already exists as a real detailed rule. Ensure it remains a distinct rule.
            if not any((r.get('name') or '')=='Teleport Assault' for r in direct_rules(u)):
                rule_once(u,(u.get('id') or key)[-70:],'Teleport Assault','An Atramentar Flay-Clade may deploy using Deep Strike even if the mission does not normally permit Deep Strike. All other normal ProHammer Deep Strike rules apply.');added_actual+=1

CHAR_RULES={
 'sevatar':['Legiones Astartes (Night Lords)','Independent Character','Master of the Legion','Psyker (Mastery Level 1)'],
 'ophion':['Legiones Astartes (Night Lords)','Independent Character','Master of the Legion','Stubborn'],
 'malcharion':['Legiones Astartes (Night Lords)','Independent Character'],
 'shang':['Legiones Astartes (Night Lords)','Independent Character','Master of the Legion','Infiltrate','Preferred Enemy (Independent Characters)'],
 'mawdrym':['Legiones Astartes (Night Lords)','Independent Character','Fearless','Feel No Pain (5+)'],
}
for key,names in CHAR_RULES.items():
    u=byid(cr,IDS[key]);
    if u is None:raise RuntimeError('Missing '+key)
    removed_dumps+=remove_direct_rule_names(u,{'Special Rules'})
    for n in names:rule_once(u,key,n,COMMON[n]);added_actual+=1
    # Named rules such as Visions of Doom, Coward, War-Sage, Devil's Luck and Unfit for Command are already detailed R71 rules and are deliberately retained.

cur=byid(cr,IDS['curze'])
if cur is None:raise RuntimeError('Missing Curze')
removed_dumps+=remove_direct_rule_names(cur,{'Special Rules'})
for n in ('Primarch','Legiones Astartes (Night Lords)','Psyker (Mastery Level 1)','Stealth','Hit & Run'):
    text=COMMON.get(n,'Uses the normal ProHammer '+n+' special rule.')
    rule_once(cur,'curze',n,text);added_actual+=1
# Existing detailed named Curze rules are retained. Add his fixed psychic power as a real visible rule.
rule_once(cur,'curze','Precognition','Blessing, Self. The Psyker re-rolls failed To Hit and To Wound rolls and failed saving throws. Curze knows only this Divination power and tests to invoke it using Leadership 8, as specified by Dark Precognition.');added_actual+=1

# ---------- 2. MOVE MODEL PROFILES OFF THE TOP-LEVEL "SOURCE ENTRY" ----------
# New Recruit labels profiles stored directly on a unit as Source Entry. Move them to the actual selected model counter/character model instead.
profiles_moved=0; character_models=0
for key in ('terror','raptor','contekar','atramentar'):
    canon=IDS[key]
    for u in matching_units(canon):
        ps=u.find(C('profiles'))
        if ps is None or len(ps)==0:continue
        models=direct_models(u)
        # R71's live build uses one true total-model counter. Attach profiles there instead of the source-entry shell.
        counter=next((m for m in models if '-models' in (m.get('id') or '')),None) or (models[0] if models else None)
        if counter is None:continue
        dest=ensure(counter,'profiles')
        for p in list(ps):dest.append(p);profiles_moved+=1
        u.remove(ps)

# Named characters/Primarch are one model. Give them a locked real model child and move their profile onto it.
for key in ('sevatar','ophion','malcharion','shang','mawdrym','curze'):
    u=byid(cr,IDS[key]);ps=u.find(C('profiles'))
    if ps is None or len(ps)==0:continue
    mid=f'r73-nl-{key}-model';m=add_entry(u,mid,u.get('name'),0,'model',1,1,1);dest=ensure(m,'profiles')
    for p in list(ps):dest.append(p);profiles_moved+=1
    u.remove(ps);character_models+=1

# ---------- 3. STEALTH ADEPT EVERYWHERE THE CURRENT ARMOURY ALLOWS IT ----------
# Keep existing R71 options, repair missing generic/copy coverage, and add named IC access. Terminators/Bikes/Jetbikes/Dreads/Vehicles are excluded.
STEALTH_TEXT='Every model in the unit gains Stealth. Every model must purchase the upgrade. An attached Independent Character must also possess Stealth Adept or the unit cannot benefit while that character remains attached.'
GENERIC_PREFIXES=(
 'legion tactical squad','legion assault squad','legion breacher siege squad','legion reconnaissance squad','legion veteran squad','legion destroyer squad','legion seeker squad','legion heavy support squad','legion command squad','legion honour guard squad','legion apothecarion detachment','legion apothecary detachment','techmarine covenant'
)
EXCLUDE_STEALTH=('terminator','contekar','atramentar','bike squadron','biker','jetbike','sky hunter','attack bike','land speeder','dreadnought','vehicle','predator','land raider','spartan','whirlwind','vindicator','rapier','tarantula')

def has_stealth_selector(u):
    return any('stealth adept' in (x.get('name') or '').lower() for x in u.iter(C('selectionEntry'))) or any('stealth adept' in (x.get('name') or '').lower() for x in u.iter(C('entryLink')))
def squad_eligible(u):
    if u.get('type')!='unit':return False
    n=(u.get('name') or '').lower()
    if any(x in n for x in EXCLUDE_STEALTH):return False
    if any(n.startswith(x) for x in GENERIC_PREFIXES):return True
    if 'terror squad' in n or 'night raptor squad' in n:return True
    return False

def add_scaled_stealth(u,idx):
    mids=[m.get('id') for m in direct_models(u) if m.get('id')]
    if not mids:return False
    e=add_entry(u,f'r73-nl-stealth-{idx}','Stealth Adept (+1 pt/model)',0)
    mods=ensure(e,'modifiers')
    for j,mid in enumerate(dict.fromkeys(mids)):
        mod=ET.SubElement(mods,C('modifier'),{'id':f'r73-nl-stealth-{idx}-cost-{j}','type':'increment','value':'1','field':'pts'});rs=ET.SubElement(mod,C('repeats'));ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'root-entry','childId':mid,'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})
    add_rule(e,f'r73-nl-stealth-{idx}-rule','Stealth Adept',STEALTH_TEXT);hide_if_missing(e,f'r73-nl-stealth-{idx}-legion',LEG);return True

stealth_squads_added=0
for idx,u in enumerate([x for x in cr.iter(C('selectionEntry')) if squad_eligible(x)]):
    if not has_stealth_selector(u):stealth_squads_added+=1 if add_scaled_stealth(u,idx) else 0

# All current named Night Lords characters are Infantry ICs and may buy +5 Stealth Adept. Curze is excluded: he already has Stealth from Night Haunter and Primarchs cannot buy generic upgrades.
stealth_chars_added=0
for key in ('sevatar','ophion','malcharion','shang','mawdrym'):
    u=byid(cr,IDS[key])
    if not has_stealth_selector(u):
        e=add_entry(u,f'r73-nl-{key}-stealth','Stealth Adept',5);add_rule(e,f'r73-nl-{key}-stealth-rule','Stealth Adept','This Independent Character gains Stealth. If joining a unit with Stealth Adept, both the unit and attached Independent Character must possess the upgrade for the unit to benefit.');stealth_chars_added+=1

# ---------- 4. HORROR CULT BEYOND JUDGEMENT ON ALL ELIGIBLE NL INFANTRY / JUMP INFANTRY SQUADS ----------
BJ_TEXT='Under Horror Cult this unit purchases Beyond Judgement for +25 points. Every model is treated as equipped with Trophies of Judgement and the unit gains Fear. Measure the 8-inch Leadership penalty from any model; multiple Trophies penalties remain non-cumulative.'
# Terminator Infantry ARE eligible for Beyond Judgement (the Rite has no Terminator exclusion), unlike Stealth Adept.
BJ_PREFIXES=GENERIC_PREFIXES+('legion terminator squad','legion terminator command squad')
def bj_eligible(u):
    if u.get('type')!='unit':return False
    n=(u.get('name') or '').lower()
    if any(n.startswith(x) for x in BJ_PREFIXES):return True
    return any(x in n for x in ('terror squad','night raptor squad','contekar terminator elite','atramentar flay-clade'))
def has_bj(u):return any('beyond judgement' in (x.get('name') or '').lower() for x in u.iter(C('selectionEntry')))
bj_added=0
for idx,u in enumerate([x for x in cr.iter(C('selectionEntry')) if bj_eligible(x)]):
    if has_bj(u):continue
    n=(u.get('name') or '').lower();pre=any(x in n for x in ('terror squad','night raptor squad','atramentar flay-clade'))
    label='Beyond Judgement — Fear (Trophies already equipped)' if pre else 'Beyond Judgement — Trophies of Judgement & Fear'
    e=add_entry(u,f'r73-nl-bj-{idx}',label,25);add_rule(e,f'r73-nl-bj-{idx}-rule','Beyond Judgement',BJ_TEXT);show_if_all(e,f'r73-nl-bj-{idx}-show',[('atLeast',1,'roster',LEG),('atLeast',1,'roster',HC)]);bj_added+=1

# ---------- 5. RITE ROLE SWAPS AND RESTRICTIONS ----------
def normalize_clone_visibility(clone_id,rite):
    x=byid(cr,clone_id)
    if x is None:raise RuntimeError('Missing Rite clone '+clone_id)
    mods=x.find(C('modifiers'))
    if mods is not None:
        for m in list(mods):
            mid=m.get('id') or ''
            # only the top-level role-clone visibility modifier, never nested option modifiers
            if mid.endswith('show') or mid.startswith('r73-nl-role-show') or mid.startswith(clone_id.replace(IDS['raptor'],'').replace(IDS['terror'],'')+'show'):
                mods.remove(m)
    # Remove any direct R71 clone visibility modifier robustly by its exact direct modifier condition signature.
    mods=ensure(x,'modifiers')
    for m in list(mods):
        conds=list(m.iter(C('condition')))
        if m.get('field')=='hidden' and any(c.get('childId')==LEG for c in conds) and any(c.get('childId') in (TA,HC) for c in conds):mods.remove(m)
    show_if_all(x,'r73-nl-role-show-'+slug(clone_id),[('atLeast',1,'roster',LEG),('atLeast',1,'roster',rite)])
    return x

ta_rap_id='r71-nl-ta-raptor-'+IDS['raptor'];ta_ter_id='r71-nl-ta-terror-'+IDS['terror'];hc_rap_id='r71-nl-hc-raptor-'+IDS['raptor']
ta_rap=normalize_clone_visibility(ta_rap_id,TA);ta_ter=normalize_clone_visibility(ta_ter_id,TA);hc_rap=normalize_clone_visibility(hc_rap_id,HC)

# Reassert hidden compulsory categories on the Rite Troops copies.
def ensure_hidden_cat(u,target):
    cats=ensure(u,'categoryLinks')
    if not any(c.get('targetId')==target for c in cats.findall(C('categoryLink'))):ET.SubElement(cats,C('categoryLink'),{'id':'r73-nl-'+slug(u.get('id'))+'-'+target,'name':target,'hidden':'true','targetId':target,'primary':'false'})
ensure_hidden_cat(ta_rap,'r71-nl-cat-terror-assault-comp');ensure_hidden_cat(ta_ter,'r71-nl-cat-terror-assault-comp');ensure_hidden_cat(hc_rap,'r71-nl-cat-horror-comp')

# Reassert Legion VIII 4 FA / 1 HS. The source gives this to Night Lords generally, and Terror Assault repeats it.
for lid,cid,val in [('fl-fast','fl-fast-max',4),('fl-heavy','fl-heavy-max',1)]:
    l=byid(gr,lid)
    if l is None:raise RuntimeError('Missing '+lid)
    mods=ensure(l,'modifiers',GNS)
    # remove older Night Lords modifier(s) controlling the same constraint, then add one clean condition
    for m in list(mods):
        if (m.get('id') or '') in ('r44-nl-fast-max','r44-nl-heavy-max','r73-nl-'+lid):mods.remove(m)
    m=ET.SubElement(mods,G('modifier'),{'id':'r73-nl-'+lid,'type':'set','value':str(val),'field':cid});cs=ET.SubElement(m,G('conditions'));ET.SubElement(cs,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':LEG,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

# Horror Cult Rite itself must remain Traitor-only.
hc=byid(cr,HC)
if hc is None:raise RuntimeError('Missing Horror Cult')
# Verify an existing direct Traitor gate; add one only if absent.
if not any(c.get('childId')=='allegiance-traitor' for c in hc.iter(C('condition'))):hide_if_missing(hc,'r73-nl-hc-traitor','allegiance-traitor')

# Standard force currently has no Fortification category link at all. Therefore "may not include a Fortification" cannot be additionally constrained here; the Rite rule text remains authoritative.
fort_links=[x for x in gr.iter(G('categoryLink')) if 'fort' in ((x.get('name') or '')+(x.get('targetId') or '')).lower()]

# ---------- VALIDATION ----------
def direct_cond_childids(x):
    out=[];mods=x.find(C('modifiers'))
    if mods is not None:
        for m in mods.findall(C('modifier')):
            out.extend(c.get('childId') for c in m.iter(C('condition')) if c.get('childId'))
    return out
assert TA in direct_cond_childids(ta_rap) and HC not in [z for z in direct_cond_childids(ta_rap) if z in (TA,HC)],direct_cond_childids(ta_rap)
assert TA in direct_cond_childids(ta_ter) and HC not in [z for z in direct_cond_childids(ta_ter) if z in (TA,HC)],direct_cond_childids(ta_ter)
assert HC in direct_cond_childids(hc_rap),direct_cond_childids(hc_rap)
for cid in ('r71-nl-cat-terror-assault-comp','r71-nl-cat-horror-comp'):
    if byid(gr,cid) is None:raise RuntimeError('Missing compulsory category '+cid)
# Canonical units no longer contain a synthetic Special Rules dump and no canonical NL profile remains on the source-entry shell.
for key in IDS:
    u=byid(cr,IDS[key]);
    assert u is not None
    assert not any((r.get('name') or '')=='Special Rules' for r in direct_rules(u)),key
    assert u.find(C('profiles')) is None or len(u.find(C('profiles')))==0,key
# Stealth: Terror/Raptor + all five named eligible ICs must expose it; Curze gets actual Stealth rule, not a purchasable Stealth Adept.
for key in ('terror','raptor','sevatar','ophion','malcharion','shang','mawdrym'):
    u=byid(cr,IDS[key]);assert has_stealth_selector(u),('missing stealth',key)
assert not has_stealth_selector(cur),'Curze must not purchase Stealth Adept'
assert any((r.get('name') or '')=='Stealth' for r in direct_rules(cur)),'Curze Stealth rule missing'
assert any((r.get('name') or '')=='Hit & Run' for r in direct_rules(cur)),'Curze Hit & Run rule missing'
# Contekar/Atramentar must not get Stealth Adept.
for key in ('contekar','atramentar'):assert not has_stealth_selector(byid(cr,IDS[key])),('illegal stealth',key)
# No duplicate IDs.
def dupids(root):
    seen=set();d=[]
    for x in root.iter():
        i=x.get('id')
        if not i:continue
        if i in seen:d.append(i)
        seen.add(i)
    return d
for root,label in ((cr,'CAT'),(gr,'GST')):
    d=dupids(root)
    if d:raise RuntimeError(f'Duplicate {label} IDs: {d[:20]}')

# ---------- REVISION / WRITE ----------
cr.set('revision','73');cr.set('gameSystemRevision','41');gr.set('revision','41')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat':e.set('dataRevision','73')
    elif e.get('filePath')=='Prohammer 30k.gst':e.set('dataRevision','41')
ET.indent(ct,space='  ');ET.indent(gt,space='  ');ET.indent(it,space='  ')
ET.register_namespace('',CNS);ct.write(CAT,encoding='utf-8',xml_declaration=True)
ET.register_namespace('',GNS);gt.write(GST,encoding='utf-8',xml_declaration=True)
ET.register_namespace('',INS);it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT);ET.parse(GST);ET.parse(IDX)

OUT.write_text(f'''Revision 73 — Night Lords actual rules / Stealth / Rites correction\nCatalogue revision: 73\nGame-system revision: 41\n\n- Removed {removed_dumps} synthetic aggregate Special Rules source-dump blocks and replaced them with {added_actual} individually named actual special-rule blocks on canonical/copy Night Lords entries.\n- Moved {profiles_moved} model profiles off top-level source-entry shells; {character_models} named characters/Primarch now use a real locked model child, preventing their stat profile from being presented as the unit's Source Entry rule block.\n- Curze now visibly carries Primarch, Legiones Astartes (Night Lords), Psyker (ML1), Stealth, Hit & Run and Precognition in addition to his existing detailed named rules. He does not receive a purchasable Stealth Adept upgrade.\n- Added missing Stealth Adept to {stealth_squads_added} eligible Infantry/Jump Infantry squad entries/copies and to {stealth_chars_added} named Night Lords Independent Characters. Existing Terror/Raptor/generic Stealth options were preserved. Terminators/Bikes/Jetbikes/Dreadnoughts/Vehicles remain excluded.\n- Added Beyond Judgement to {bj_added} previously uncovered eligible Horror Cult Infantry/Jump Infantry squad entries/copies.\n- Terror Assault Troops clones are now explicitly gated to Terror Assault; Horror Cult Raptor Troops are explicitly gated to Horror Cult. Hidden compulsory categories remain attached.\n- Legion VIII 0-4 Fast Attack / 0-1 Heavy Support limits were reasserted.\n- Horror Cult Traitor gate was verified.\n- Fortification category links currently present in the Standard force: {len(fort_links)}; where no Fortification slot exists there is nothing additional for New Recruit to mechanically forbid, so the written Rite limitation remains.\n- Duplicate-ID, XML parse, canonical-rule and Rite visibility validation passed.\n''',encoding='utf-8')
print(OUT.read_text())
