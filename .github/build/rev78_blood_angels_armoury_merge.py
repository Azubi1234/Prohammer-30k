from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r78-blood-angels-armoury-merge.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS); ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()
if cr.get('revision')!='77' or gr.get('revision')!='44':
    raise RuntimeError(f'Expected CAT77/GST44, got CAT{cr.get("revision")}/GST{gr.get("revision")}')

LEG='legion-ix'; MASK='r44-ba-death-mask'; INFERNO='r44-ba-inferno-pistol'; BLADE='r44-ba-blade-perdition'; BLADE_EX='r74-ba-blade-exchange'

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t):
    x=p.find(C(t))
    if x is None:x=ET.SubElement(p,C(t))
    return x

def constraint(p,i,typ,val):
    return ET.SubElement(ensure(p,'constraints'),C('constraint'),{'id':i,'type':typ,'value':str(val),'field':'selections','scope':'parent','shared':'true','includeChildSelections':'false','includeChildForces':'false'})
def legion_visible(e,i):
    e.set('hidden','true')
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'})
    cs=ET.SubElement(m,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':LEG,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def blade_exchange_visible(e,i):
    e.set('hidden','true')
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'})
    cg=ET.SubElement(ET.SubElement(m,C('conditionGroups')),C('conditionGroup'),{'type':'and'}); cs=ET.SubElement(cg,C('conditions'))
    for child,scope in ((LEG,'roster'),('gear-power-weapon','root-entry')):
        ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def link(group,i,name,target,kind='legion'):
    l=ET.SubElement(ensure(group,'entryLinks'),C('entryLink'),{'id':i,'name':name,'type':'selectionEntry','targetId':target,'hidden':'true','import':'true'})
    constraint(l,i+'-max','max',1)
    if kind=='legion':legion_visible(l,i+'-show')
    else:blade_exchange_visible(l,i+'-show')
    return l

def immediate_groups(unit):
    s=unit.find(C('selectionEntryGroups'))
    return [] if s is None else list(s.findall(C('selectionEntryGroup')))

def find_group(unit,mode):
    gs=immediate_groups(unit)
    if mode=='weapon':
        cand=[g for g in gs if 'weapon' in (g.get('name') or '').lower() and 'replacement' in (g.get('name') or '').lower()]
        if not cand:
            cand=[g for g in gs if 'weapon' in (g.get('name') or '').lower() and 'armoury' in (g.get('name') or '').lower()]
    else:
        cand=[g for g in gs if 'additional wargear' in (g.get('name') or '').lower()]
        if not cand:
            cand=[g for g in gs if 'wargear' in (g.get('name') or '').lower() and 'weapon' not in (g.get('name') or '').lower() and 'armour' not in (g.get('name') or '').lower()]
    if len(cand)!=1:
        names=[(g.get('id'),g.get('name')) for g in gs]
        raise RuntimeError(f'{unit.get("name")}: expected exactly one {mode} group, got {[(x.get("id"),x.get("name")) for x in cand]}; immediate groups={names}')
    return cand[0]

# Remove the dedicated BA containers from Rev76/77 and any lingering BA shared links on generic HQ shells.
removed=[]
for uid in ('hq-praetor','hq-centurion'):
    u=byid(cr,uid)
    if u is None:raise RuntimeError('Missing '+uid)
    for p in list(u.iter()):
        for x in list(p):
            xid=x.get('id') or ''
            if xid.startswith(('r76-ba-','r77-ba-')):
                removed.append((uid,xid,x.get('name'))); p.remove(x); continue
            if x.tag==C('entryLink') and x.get('targetId') in (MASK,INFERNO,BLADE,BLADE_EX):
                removed.append((uid,xid,x.get('name'))); p.remove(x)

placed=[]
for uid,slug in (('hq-praetor','praetor'),('hq-centurion','centurion')):
    u=byid(cr,uid); wg=find_group(u,'weapon'); gear=find_group(u,'wargear')
    placed.append((uid,'weapon',wg.get('id'),wg.get('name'))); placed.append((uid,'wargear',gear.get('id'),gear.get('name')))
    # Weapons go into the existing weapon-replacement/weapon-armoury group, exactly like normal weapons.
    link(wg,f'r78-ba-{slug}-inferno','Inferno Pistol',INFERNO)
    link(wg,f'r78-ba-{slug}-blade','Blade of Perdition',BLADE)
    ex=link(wg,f'r78-ba-{slug}-blade-exchange','Blade of Perdition — exchange existing Power Weapon',BLADE_EX,'exchange')
    # Death Mask is wargear, so place it in Additional Wargear with the rest of the character wargear.
    link(gear,f'r78-ba-{slug}-mask','Death Mask',MASK)

# Validate exact parent placement.
parent={c:p for p in cr.iter() for c in p}
def nearest_group(x):
    p=parent.get(x)
    while p is not None and p.tag!=C('selectionEntryGroup'):p=parent.get(p)
    return p
for uid,slug in (('hq-praetor','praetor'),('hq-centurion','centurion')):
    u=byid(cr,uid); wg=find_group(u,'weapon'); gear=find_group(u,'wargear')
    for iid in (f'r78-ba-{slug}-inferno',f'r78-ba-{slug}-blade',f'r78-ba-{slug}-blade-exchange'):
        x=byid(cr,iid)
        if nearest_group(x) is not wg:raise RuntimeError(f'{iid} not in weapon group')
    m=byid(cr,f'r78-ba-{slug}-mask')
    if nearest_group(m) is not gear:raise RuntimeError(f'{m.get("id")} not in wargear group')
    # No dedicated BA container should remain under generic HQ.
    bad=[g.get('id') for g in u.iter(C('selectionEntryGroup')) if 'blood angels armoury' in (g.get('name') or '').lower()]
    if bad:raise RuntimeError(f'Dedicated BA groups remain under {uid}: {bad}')

# No old broad-injection links or Rev76/77 BA generic HQ structures remain.
for prefix in ('r74-ba-arm-','r76-ba-praetor-','r76-ba-centurion-','r77-ba-praetor-','r77-ba-centurion-'):
    bad=[e.get('id') for e in cr.iter() if (e.get('id') or '').startswith(prefix)]
    if bad:raise RuntimeError(f'Old BA generic structure remains for {prefix}: {bad[:20]}')

# Explicit special-unit/named-character options must survive.
for required in ('r74-ba-moritat-two-inferno','r41-unit-ix-5-sanguinary-guard-opt-0-inferno-pistol'):
    if byid(cr,required) is None:raise RuntimeError('Missing explicit BA option '+required)

# Duplicate IDs.
seen=set();dups=[]
for e in cr.iter():
    i=e.get('id')
    if not i:continue
    if i in seen:dups.append(i)
    seen.add(i)
if dups:raise RuntimeError('Duplicate IDs: '+str(dups[:20]))

cr.set('revision','78'); cr.set('gameSystemRevision','45'); gr.set('revision','45')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat':e.set('dataRevision','78')
    if e.get('filePath')=='Prohammer 30k.gst':e.set('dataRevision','45')
ET.indent(ct,space='  '); ET.indent(gt,space='  '); ET.indent(it,space='  ')
ET.register_namespace('',CNS);ct.write(CAT,encoding='utf-8',xml_declaration=True)
ET.register_namespace('',GNS);gt.write(GST,encoding='utf-8',xml_declaration=True)
ET.register_namespace('',INS);it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT);ET.parse(GST);ET.parse(IDX)

OUT.write_text('Revision 78 — Blood Angels armoury merge\nCatalogue revision: 78\nGame-system revision: 45\n\n'+
'''Correction\n- Removed the separate Blood Angels Armoury container entirely.\n- Inferno Pistol and both Blade of Perdition purchase modes are now placed directly inside each generic HQ's existing weapon section.\n- Death Mask is now placed directly inside each generic HQ's existing Additional Wargear section.\n- Each BA item is individually hidden unless Legion IX is selected, so New Recruit does not have to render a conditional parent container.\n- Explicit Sanguinary Guard, Moritat and named-character options are unchanged.\n\nActual target groups found at build time:\n'''+''.join(f'- {u}: {k} -> {gid} :: {name}\n' for u,k,gid,name in placed)+
'''\nValidation\n- Weapons have the exact existing weapon group as parent.\n- Death Mask has the exact existing wargear group as parent.\n- No dedicated Blood Angels Armoury group remains on Praetor/Centurion.\n- No old r74 broad-injection or r76/r77 generic BA armoury structures remain.\n- XML parse and duplicate-ID validation passed.\n''',encoding='utf-8')
print(OUT.read_text())
