from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r77-blood-angels-armoury-ui.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS); ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()
if cr.get('revision')!='76' or gr.get('revision')!='43':
    raise RuntimeError(f'Expected CAT76/GST43 baseline, got CAT{cr.get("revision")}/GST{gr.get("revision")}')

LEG='legion-ix'; MASK='r44-ba-death-mask'; INFERNO='r44-ba-inferno-pistol'; BLADE='r44-ba-blade-perdition'; BLADE_EX='r74-ba-blade-exchange'
TARGETS={MASK,INFERNO,BLADE,BLADE_EX}

def byid(root,i): return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t,ns=CNS):
    q=(C if ns==CNS else G if ns==GNS else I)(t); x=p.find(q)
    if x is None:x=ET.SubElement(p,q)
    return x
def constraint(p,i,typ,val,child=True):
    return ET.SubElement(ensure(p,'constraints'),C('constraint'),{'id':i,'type':typ,'value':str(val),'field':'selections','scope':'parent','shared':'true','includeChildSelections':'true' if child else 'false','includeChildForces':'false'})
def hide_unless_legion(e,i):
    # IMPORTANT: group starts visible. New Recruit can flatten children of groups which begin hidden=true.
    e.set('hidden','false')
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'true','field':'hidden'})
    cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'lessThan','value':'1','field':'selections','scope':'roster','childId':LEG,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def show_if_power_weapon(e,i):
    e.set('hidden','true')
    m=ET.SubElement(ensure(e,'modifiers'),C('modifier'),{'id':i,'type':'set','value':'false','field':'hidden'})
    gs=ET.SubElement(m,C('conditionGroups'));cg=ET.SubElement(gs,C('conditionGroup'),{'type':'and'});cs=ET.SubElement(cg,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':LEG,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'root-entry','childId':'gear-power-weapon','shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def link(p,i,name,target,hidden=False):
    l=ET.SubElement(ensure(p,'entryLinks'),C('entryLink'),{'id':i,'name':name,'type':'selectionEntry','targetId':target,'hidden':'true' if hidden else 'false','import':'true'})
    constraint(l,i+'-max','max',1,False);return l

def remove_prefixed(root,pfx):
    for p in list(root.iter()):
        for x in list(p):
            if (x.get('id') or '').startswith(pfx):p.remove(x)

# Safe rerun cleanup of this pass only.
remove_prefixed(cr,'r77-ba-ui-')

removed=[]
for uid,slug in (('hq-praetor','praetor'),('hq-centurion','centurion')):
    u=byid(cr,uid)
    if u is None:raise RuntimeError('Missing '+uid)

    # Delete the Rev76 group entirely and remove ALL shared BA Armoury links anywhere in the generic HQ shell.
    segs=u.find(C('selectionEntryGroups'))
    if segs is not None:
        for g in list(segs.findall(C('selectionEntryGroup'))):
            if g.get('id') in (f'r76-ba-{slug}-armoury',):
                segs.remove(g); removed.append(g.get('id'))
    for p in list(u.iter()):
        links=p.find(C('entryLinks'))
        if links is None:continue
        for l in list(links.findall(C('entryLink'))):
            if l.get('targetId') in TARGETS:
                removed.append(l.get('id'));links.remove(l)

    # One real, visible container. It is hidden only when Legion IX is NOT selected.
    groups=ensure(u,'selectionEntryGroups')
    g=ET.SubElement(groups,C('selectionEntryGroup'),{'id':f'r77-ba-ui-{slug}-armoury','name':'Blood Angels Armoury (counts toward 100 pt Armoury limit)','hidden':'false','collective':'false','import':'true'})
    hide_unless_legion(g,f'r77-ba-ui-{slug}-armoury-hide')

    link(g,f'r77-ba-ui-{slug}-mask','Death Mask',MASK)
    link(g,f'r77-ba-ui-{slug}-inferno','Inferno Pistol',INFERNO)

    bg=ET.SubElement(ensure(g,'selectionEntryGroups'),C('selectionEntryGroup'),{'id':f'r77-ba-ui-{slug}-blade-group','name':'Blade of Perdition — choose one','hidden':'false','collective':'false','import':'true'})
    constraint(bg,f'r77-ba-ui-{slug}-blade-group-max','max',1)
    link(bg,f'r77-ba-ui-{slug}-blade','Blade of Perdition',BLADE)
    ex=link(bg,f'r77-ba-ui-{slug}-blade-exchange','Blade of Perdition — exchange existing Power Weapon',BLADE_EX,True)
    show_if_power_weapon(ex,f'r77-ba-ui-{slug}-blade-exchange-show')

# Structural validation for the exact UI bug shown by the user.
parent={c:p for p in cr.iter() for c in p}
for uid,slug in (('hq-praetor','praetor'),('hq-centurion','centurion')):
    u=byid(cr,uid); g=byid(cr,f'r77-ba-ui-{slug}-armoury')
    if g is None or g.get('hidden')!='false':raise RuntimeError('BA armoury group is not a real visible container for '+slug)
    # There must be no shared BA link in Armour Replacement, Mobility, Additional Wargear, retinue, or root level.
    bad=[]
    for l in u.iter(C('entryLink')):
        if l.get('targetId') not in TARGETS:continue
        x=parent.get(l); container=None
        while x is not None and x is not u:
            if x.tag==C('selectionEntryGroup'):
                container=x;break
            x=parent.get(x)
        if container is None or not (container.get('id') or '').startswith(f'r77-ba-ui-{slug}-'):
            bad.append((l.get('id'),l.get('name'),container.get('name') if container is not None else '<ROOT>'))
    if bad:raise RuntimeError(f'BA items escaped dedicated {slug} group: {bad}')
    # Explicitly prove the screenshot's parent group contains none.
    for gid in (f'hq-{slug}-armour',f'hq-{slug}-mob',f'hq-{slug}-wargear'):
        x=byid(cr,gid)
        if x is not None and any(l.get('targetId') in TARGETS for l in x.iter(C('entryLink'))):
            raise RuntimeError('BA shared item still found under '+gid)

# Global old broad-injection links must remain gone.
old=[e.get('id') for e in cr.iter() if (e.get('id') or '').startswith('r74-ba-arm-')]
if old:raise RuntimeError('Old r74 broad-injection objects remain: '+str(old[:20]))

# Preserve explicit BA unit options and named-character mask purchases.
for required in ('r74-ba-moritat-two-inferno','r41-unit-ix-5-sanguinary-guard-opt-0-inferno-pistol','r75-ba-r41-unit-ix-6-raldoron-the-blooded-death-mask','r75-ba-r41-unit-ix-7-dominion-zephon-death-mask','r75-ba-r41-unit-ix-8-aster-crohne-death-mask','r75-ba-r41-unit-ix-10-nassir-amit-the-flesh-tearer-death-mask'):
    if byid(cr,required) is None:raise RuntimeError('Explicit BA option missing after UI cleanup: '+required)

# Duplicate IDs.
for root,label in ((cr,'CAT'),(gr,'GST')):
    seen=set();dups=[]
    for e in root.iter():
        i=e.get('id')
        if not i:continue
        if i in seen:dups.append(i)
        seen.add(i)
    if dups:raise RuntimeError(f'Duplicate {label} IDs: {dups[:20]}')

# Force a full New Recruit data refresh as well as a catalogue refresh.
cr.set('revision','77');cr.set('gameSystemRevision','44');gr.set('revision','44')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat':e.set('dataRevision','77')
    elif e.get('filePath')=='Prohammer 30k.gst':e.set('dataRevision','44')

ET.indent(ct,space='  ');ET.indent(gt,space='  ');ET.indent(it,space='  ')
ET.register_namespace('',CNS);ct.write(CAT,encoding='utf-8',xml_declaration=True)
ET.register_namespace('',GNS);gt.write(GST,encoding='utf-8',xml_declaration=True)
ET.register_namespace('',INS);it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT);ET.parse(GST);ET.parse(IDX)

OUT.write_text(f'''Revision 77 — Blood Angels Armoury UI containment fix\nCatalogue revision: 77\nGame-system revision: 44\n\nCause\n- Rev76 correctly removed the 406 broad-injection links, but its new Blood Angels Armoury group began with hidden=true and relied on an unhide modifier. New Recruit can render children of such a conditional container without rendering the container heading, visually flattening the items into the preceding group (for example Armour Replacement).\n- Death Mask was also still a direct root-level Praetor/Centurion link instead of living in the dedicated Blood Angels Armoury container.\n\nFix\n- Rebuilt Praetor and Centurion Blood Angels Armoury groups as normal visible groups which are hidden only when Legion IX is absent, matching the established project pattern used by other Legion armouries.\n- Death Mask, Inferno Pistol and Blade of Perdition now live only inside that one Blood Angels Armoury group on each generic HQ.\n- Blade exchange remains conditional on actually selecting a Power Weapon and mutually exclusive with the full +25 Blade purchase.\n- Removed {len(removed)} stale/shared BA links or old Rev76 containers from those generic HQ shells.\n- Explicit unit-local options such as Sanguinary Guard Inferno Pistols, Moritat double Inferno Pistols, and named-character Death Masks are preserved.\n- CAT and GST revisions both bumped (77 / 44) to force a clean New Recruit refresh rather than relying on catalogue-only cache invalidation.\n\nValidation\n- No shared BA item exists under Armour Replacement, Mobility, Additional Wargear, retinue, or generic HQ root level.\n- No r74-ba-arm-* broad-injection objects remain.\n- Duplicate-ID and XML parse validation passed.\n''',encoding='utf-8')
print(OUT.read_text())
