from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r76-blood-angels-armoury-placement.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS); ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()
if cr.get('revision')!='75' or cr.get('gameSystemRevision')!='43' or gr.get('revision')!='43':
    raise RuntimeError(f'Expected CAT75/GST43 baseline, got CAT{cr.get("revision")}/gameSystemRevision{cr.get("gameSystemRevision")}/GST{gr.get("revision")}')

LEG='legion-ix'; INFERNO='r44-ba-inferno-pistol'; BLADE='r44-ba-blade-perdition'; BLADE_EX='r74-ba-blade-exchange'

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t):
    x=p.find(C(t))
    if x is None:x=ET.SubElement(p,C(t))
    return x
def constraint(p,i,typ,val,child=True):
    return ET.SubElement(ensure(p,'constraints'),C('constraint'),{'id':i,'type':typ,'value':str(val),'field':'selections','scope':'parent','shared':'true','includeChildSelections':'true' if child else 'false','includeChildForces':'false'})
def show_if_legion(e,i):
    e.set('hidden','true')
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'})
    cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':LEG,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def show_if_power_weapon(e,i):
    e.set('hidden','true')
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'})
    cg=ET.SubElement(ET.SubElement(m,C('conditionGroups')),C('conditionGroup'),{'type':'and'});cs=ET.SubElement(cg,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':LEG,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'root-entry','childId':'gear-power-weapon','shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def link(p,i,name,target,hidden=False):
    l=ET.SubElement(ensure(p,'entryLinks'),C('entryLink'),{'id':i,'name':name,'type':'selectionEntry','targetId':target,'hidden':'true' if hidden else 'false','import':'true'})
    constraint(l,i+'-max','max',1,False);return l

def remove_r76():
    for p in list(cr.iter()):
        for x in list(p):
            if (x.get('id') or '').startswith('r76-ba-'):p.remove(x)

remove_r76()

# Rev74 used the substring "armoury" to decide where Blood Angels weapons should be inserted.
# That caught Mobility groups, other Legions' armouries, Sergeant armouries and cloned groups.
# Remove every shared Inferno/Blade/Blade-exchange link created by that broad mechanism; explicit
# unit-local weapon options (Sanguinary Guard, Moritat etc.) are separate selectionEntries and are untouched.
removed=[]
for p in list(cr.iter()):
    for x in list(p):
        if x.tag!=C('entryLink'):continue
        if x.get('targetId') in (INFERNO,BLADE,BLADE_EX):
            removed.append((x.get('id'),x.get('name'),x.get('targetId'),p.get('id'),p.get('name')))
            p.remove(x)

# Re-add the Legion armoury only to the two generic Independent Character HQ shells.
# Consuls inherit the Centurion shell unless their own rules say otherwise, so this is also the
# single correct access point for eligible Centurion-derived Consuls such as the High Priest.
for uid,slug in (('hq-praetor','praetor'),('hq-centurion','centurion')):
    u=byid(cr,uid)
    if u is None:raise RuntimeError('Missing '+uid)
    groups=ensure(u,'selectionEntryGroups')
    g=ET.SubElement(groups,C('selectionEntryGroup'),{'id':f'r76-ba-{slug}-armoury','name':'Blood Angels Armoury — Weapons (counts toward 100 pt Armoury limit)','hidden':'true','collective':'false','import':'true'})
    show_if_legion(g,f'r76-ba-{slug}-armoury-show')
    link(g,f'r76-ba-{slug}-inferno','Inferno Pistol',INFERNO)
    bg=ET.SubElement(ensure(g,'selectionEntryGroups'),C('selectionEntryGroup'),{'id':f'r76-ba-{slug}-blade-group','name':'Blade of Perdition — choose one','hidden':'false','collective':'false','import':'true'})
    constraint(bg,f'r76-ba-{slug}-blade-group-max','max',1)
    link(bg,f'r76-ba-{slug}-blade','Blade of Perdition',BLADE)
    ex=link(bg,f'r76-ba-{slug}-blade-exchange','Blade of Perdition — exchange existing Power Weapon',BLADE_EX,True)
    show_if_power_weapon(ex,f'r76-ba-{slug}-blade-exchange-show')

# Validation: exactly the deliberate six shared links remain (Inferno, full Blade, exchange for each generic HQ).
links=[x for x in cr.iter(C('entryLink')) if x.get('targetId') in (INFERNO,BLADE,BLADE_EX)]
expected={
 'r76-ba-praetor-inferno','r76-ba-praetor-blade','r76-ba-praetor-blade-exchange',
 'r76-ba-centurion-inferno','r76-ba-centurion-blade','r76-ba-centurion-blade-exchange'}
actual={x.get('id') for x in links}
if actual!=expected:raise RuntimeError(f'Unexpected Blood Angels shared weapon links: expected {sorted(expected)}, got {sorted(actual)}')
# The reported UI bug must be impossible: no BA shared weapon may live in Mobility or another Legion armoury group.
parent={c:p for p in cr.iter() for c in p}
for l in links:
    x=parent.get(l)
    while x is not None and x.tag!=C('selectionEntryGroup'):x=parent.get(x)
    if x is None:raise RuntimeError('BA shared weapon link has no containing group: '+str(l.get('id')))
    name=(x.get('name') or '').lower()
    if 'mobility' in name:raise RuntimeError('BA shared weapon still in Mobility: '+str(l.get('id')))
    if any(s in name for s in ('space wolves armoury','imperial fists armoury','iron warriors armoury','night lords armoury','salamanders armoury','thousand sons armoury')):
        raise RuntimeError('BA shared weapon still in another Legion armoury: '+str(l.get('id')))
# No old broad-injection links survive.
old=[x.get('id') for x in cr.iter(C('entryLink')) if (x.get('id') or '').startswith('r74-ba-arm-')]
if old:raise RuntimeError('Old broad BA armoury links remain: '+str(old[:20]))
# Explicit options must survive.
for required in ('r74-ba-moritat-two-inferno','r41-unit-ix-5-sanguinary-guard-opt-0-inferno-pistol'):
    if byid(cr,required) is None:raise RuntimeError('Explicit Blood Angels weapon option was accidentally removed: '+required)
# Duplicate IDs.
seen=set();dups=[]
for e in cr.iter():
    i=e.get('id')
    if not i:continue
    if i in seen:dups.append(i)
    seen.add(i)
if dups:raise RuntimeError('Duplicate CAT IDs: '+str(dups[:20]))

cr.set('revision','76')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat':e.set('dataRevision','76')

ET.indent(ct,space='  ');ET.indent(it,space='  ')
ET.register_namespace('',CNS);ct.write(CAT,encoding='utf-8',xml_declaration=True)
ET.register_namespace('',INS);it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT);ET.parse(GST);ET.parse(IDX)

OUT.write_text(f'''Revision 76 — Blood Angels armoury placement fix\nCatalogue revision: 76\nGame-system revision: 43\n\nRoot cause\n- Rev74 matched every selection group whose name contained the word "armoury". That accidentally injected Inferno Pistol and Blade of Perdition into Mobility, Sergeant, other-Legion and cloned armoury groups.\n\nFix\n- Removed {len(removed)} shared Inferno Pistol / Blade of Perdition / Blade exchange links created across the catalogue.\n- Explicit unit-local Blood Angels options were not touched: Sanguinary Guard Inferno Pistol and the Moritat two-Inferno replacement remain.\n- Generic Blood Angels Praetor and Centurion now each have one dedicated Blood Angels Armoury — Weapons group.\n- Inferno Pistol +15 and Blade of Perdition +25 live only in that group.\n- The +10 Blade of Perdition Power Weapon exchange is in the same group, only appears after an actual Power Weapon is selected, and is mutually exclusive with the +25 purchase.\n- Blade of Perdition no longer appears in ordinary squad/Sergeant entries or unrelated Armoury/Mobility groups.\n\nValidation\n- No r74-ba-arm-* broad-injection links remain.\n- No Blood Angels shared weapon link exists under Mobility or another Legion armoury.\n- Exactly six deliberate shared links remain across Praetor/Centurion.\n- Explicit Sanguinary Guard and Moritat Inferno options survived.\n- Duplicate-ID and XML parse validation passed.\n''',encoding='utf-8')
print(OUT.read_text())
