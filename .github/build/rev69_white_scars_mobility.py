from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r69-white-scars-mobility.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()
if cr.get('revision')!='68' or gr.get('revision')!='36': raise RuntimeError(f'Expected CAT68/GST36, got {cr.get("revision")}/{gr.get("revision")}')

def byid(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def ensure(p,t):
    x=p.find(C(t))
    if x is None: x=ET.SubElement(p,C(t))
    return x
def maxcon(e):
    cs=e.find(C('constraints'))
    return next((x for x in cs.findall(C('constraint')) if x.get('type')=='max' and x.get('field')=='selections'),None) if cs is not None else None
def mincon(e):
    cs=e.find(C('constraints'))
    return next((x for x in cs.findall(C('constraint')) if x.get('type')=='min' and x.get('field')=='selections'),None) if cs is not None else None
def pts(e):
    cs=e.find(C('costs'))
    return next((x for x in cs.findall(C('cost')) if x.get('typeId')=='pts'),None) if cs is not None else None
def setcost(e,v,id_=None):
    cs=ensure(e,'costs'); c=pts(e)
    if c is None: c=ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
    else: c.set('value',str(v))
    if id_: c.set('id',id_)
    return c
def addmax(e,id_,v):
    c=maxcon(e)
    if c is None:
        c=ET.SubElement(ensure(e,'constraints'),C('constraint'),{'id':id_,'type':'max','value':str(v),'field':'selections','scope':'parent','shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    else: c.set('value',str(v))
    return c
def addrule(e,id_,name,text):
    rs=ensure(e,'rules'); old=next((r for r in rs.findall(C('rule')) if r.get('id')==id_),None)
    if old is not None: rs.remove(old)
    r=ET.SubElement(rs,C('rule'),{'id':id_,'name':name,'hidden':'false'}); ET.SubElement(r,C('description')).text=text
    return r
def clear_r69():
    for p in list(cr.iter()):
        for x in list(p):
            if (x.get('id') or '').startswith('r69-'): p.remove(x)
def add_show_if(e,child,scope='roster'):
    e.set('hidden','true'); mods=ensure(e,'modifiers')
    m=ET.SubElement(mods,C('modifier'),{'id':e.get('id')+'-show','type':'set','value':'false','field':'hidden'})
    cs=ET.SubElement(m,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_hide_if(e,child,scope='root-entry'):
    mods=ensure(e,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':'r69-hide-'+e.get('id')[-24:]+'-'+child[-18:],'type':'set','value':'true','field':'hidden'})
    cs=ET.SubElement(m,C('conditions'))
    ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def direct_models(u):
    ses=u.find(C('selectionEntries')); return [] if ses is None else [e for e in ses.findall(C('selectionEntry')) if e.get('type')=='model']
def model_counts(u):
    models=[m for m in direct_models(u) if not any(w in (m.get('name') or '').lower() for w in ('land raider','rhino','drop pod','spartan','dreadclaw','vehicle'))]
    if not models: raise RuntimeError('No squad model entries in '+u.get('name','?'))
    defaults=[]
    for m in models:
        mn=mincon(m); d=m.get('defaultAmount')
        defaults.append(int(float(d if d is not None else (mn.get('value') if mn is not None else 0))))
    base=sum(defaults)
    variable=None
    for m,d in zip(models,defaults):
        mx=maxcon(m)
        if mx is not None and int(float(mx.get('value')))>d:
            variable=(m,d,int(float(mx.get('value')))); break
    max_total=base if variable is None else base+(variable[2]-variable[1])
    return base,max_total,variable

def add_squad_mount(unit,owner_mount_id,prefix,label,ppm):
    # Whole-squad mobility checkbox with automatic per-model cost. Uses the same scaling pattern already used by Veteran squad-wide upgrades.
    ses=ensure(unit,'selectionEntries'); e=ET.SubElement(ses,C('selectionEntry'),{'id':prefix,'name':label,'type':'upgrade','hidden':'true','import':'true'})
    addmax(e,prefix+'-max',1)
    base,totalmax,var=model_counts(unit); setcost(e,base*ppm,prefix+'-pts')
    if var is not None:
        counter,default,mx=var
        mods=ensure(e,'modifiers'); m=ET.SubElement(mods,C('modifier'),{'id':prefix+'-scale','type':'increment','value':str(ppm),'field':'pts'})
        reps=ET.SubElement(m,C('repeats'))
        ET.SubElement(reps,C('repeat'),{'value':str(default+1),'repeats':'1','field':'selections','scope':'root-entry','childId':counter.get('id'),'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})
    add_show_if(e,owner_mount_id,'roster')
    addrule(e,prefix+'-rule','Mounted Retinue',f'Available when the selecting character is mounted as stated in its entry. Every model in this retinue takes the same {label.replace(" (entire squad)","")} for +{ppm} points per model. A mounted retinue may not select a Dedicated Transport.')
    # Bike and Jump Pack mobility are mutually exclusive; mounted squads lose Dedicated Transport.
    for jp in unit.iter(C('selectionEntry')):
        if jp is e: continue
        if (jp.get('name') or '').startswith('Jump Packs'):
            add_hide_if(jp,e.get('id'),'root-entry'); add_hide_if(e,jp.get('id'),'root-entry')
    for g in unit.iter(C('selectionEntryGroup')):
        if 'dedicated transport' in (g.get('name') or '').lower(): add_hide_if(g,e.get('id'),'root-entry')
    return base,totalmax

clear_r69(); report=[]
# The final White Scars source explicitly gives Shiban, Hibou and Hasik Bike +35 and a further +5 Jetbike upgrade.
chars={
 'shiban':('r41-unit-v-6-shiban-khan',['Legion Command Squad']),
 'hibou':('r41-unit-v-7-hibou-khan',['Legion Command Squad','Legion Veteran Squad']),
 'hasik':('r41-unit-v-8-hasik-noyan-khan',['Legion Command Squad','Legion Veteran Squad']),
}
for slug,(uid,allowed) in chars.items():
    u=byid(uid); assert u is not None,uid
    bike=byid(f'r60-ws-{slug}-bike'); jet=byid(f'r60-ws-{slug}-jetbike')
    if bike is None:
        og=next((g for g in u.iter(C('selectionEntryGroup')) if (g.get('name') or '').lower()=='options'),None) or ET.SubElement(ensure(u,'selectionEntryGroups'),C('selectionEntryGroup'),{'id':f'r69-ws-{slug}-options','name':'Options','hidden':'false','import':'true'})
        bike=ET.SubElement(ensure(og,'selectionEntries'),C('selectionEntry'),{'id':f'r69-ws-{slug}-bike','name':'Space Marine Bike','type':'upgrade','hidden':'false','import':'true'}); addmax(bike,bike.get('id')+'-max',1); setcost(bike,35,bike.get('id')+'-pts')
    else:
        bike.set('hidden','false'); addmax(bike,bike.get('id')+'-max',1); setcost(bike,35)
    addrule(bike,'r69-ws-'+slug+'-bike-rule','Space Marine Bike','The character becomes Bike unit type and follows the normal ProHammer Bike rules. The bike is armed with twin-linked bolters.')
    if jet is None:
        parent=next((p for p in cr.iter() for c in list(p) if c is bike),None); ses=parent if parent is not None and parent.tag==C('selectionEntries') else ensure(u,'selectionEntries')
        jet=ET.SubElement(ses,C('selectionEntry'),{'id':f'r69-ws-{slug}-jetbike','name':'Upgrade Bike to Jetbike','type':'upgrade','hidden':'true','import':'true'}); addmax(jet,jet.get('id')+'-max',1); setcost(jet,5,jet.get('id')+'-pts')
    else:
        jet.set('hidden','true'); addmax(jet,jet.get('id')+'-max',1); setcost(jet,5)
        # remove only old visibility modifiers from this simple Rev60 option; rebuild dependency correctly.
        mods=jet.find(C('modifiers'))
        if mods is not None: jet.remove(mods)
    add_show_if(jet,bike.get('id'),'roster')
    addrule(jet,'r69-ws-'+slug+'-jet-rule','Jetbike','May only be selected if the character has purchased a Space Marine Bike. For a further +5 points the Bike is upgraded to a Jetbike; the character follows the normal ProHammer Jetbike rules.')
    # Add source-backed Bike mobility to Command/Veteran retinues.
    retgroups=[g for g in u.iter(C('selectionEntryGroup')) if 'retinue' in (g.get('name') or '').lower()]
    found=[]
    for rg in retgroups:
        se=rg.find(C('selectionEntries'))
        if se is None: continue
        for ru in se.findall(C('selectionEntry')):
            if ru.get('name') not in allowed: continue
            key='command' if 'Command' in ru.get('name') else 'veteran'
            base,mx=add_squad_mount(ru,bike.get('id'),f'r69-ws-{slug}-{key}-bikes','Space Marine Bikes (entire squad)',20)
            found.append(f'{ru.get("name")} {base}-{mx}')
    if len(found)!=len(allowed): raise RuntimeError(f'{u.get("name")}: expected retinues {allowed}, found mounted {found}')
    report.append(f'{u.get("name")}: Bike +35, Jetbike +5; mounted retinue options: '+', '.join(found))

# Generic Centurion Command Squad: the core Army List says a Bike-mounted Centurion allows the whole Command Squad to take Bikes +20/model,
# and a Jetbike-mounted Centurion allows Jetbikes +35/model. Add these missing functional choices to the existing retinue.
centcmd=byid('hq-centurion-ret-command'); assert centcmd is not None
b0,bm=add_squad_mount(centcmd,'hq-centurion-bike','r69-centurion-command-bikes','Space Marine Bikes (entire squad)',20)
j0,jm=add_squad_mount(centcmd,'r37-centurion-jetbike','r69-centurion-command-jetbikes','Jetbikes (entire squad)',35)
# Mutually exclusive Command Squad mounted modes.
add_hide_if(byid('r69-centurion-command-bikes'),'r69-centurion-command-jetbikes','root-entry'); add_hide_if(byid('r69-centurion-command-jetbikes'),'r69-centurion-command-bikes','root-entry')
report.append(f'Generic Legion Command Squad retinue: Bikes +20/model and Jetbikes +35/model, {b0}-{bm} models.')

# Jaghatai's final source specifically allows his Honour Guard Primarch Retinue to take Jetbikes +35/model when he has the Sojutsu Voidbike.
jagh=byid('r41-unit-v-9-v-jaghatai-khan-the-warhawk') or next((e for e in cr.iter(C('selectionEntry')) if 'JAGHATAI KHAN' in (e.get('name') or '').upper()),None)
if jagh is not None:
    rg=next((g for g in jagh.iter(C('selectionEntryGroup')) if 'retinue' in (g.get('name') or '').lower()),None)
    if rg is not None:
        se=rg.find(C('selectionEntries'))
        hg=next((x for x in se.findall(C('selectionEntry')) if x.get('name')=='Legion Honour Guard Squad'),None) if se is not None else None
        if hg is not None:
            h0,hm=add_squad_mount(hg,'r60-ws-jagh-voidbike','r69-ws-jagh-honour-jetbikes','Jetbikes (entire squad)',35)
            report.append(f'Jaghatai Honour Guard retinue: Jetbikes +35/model when Voidbike selected, {h0}-{hm} models.')

# Revisions: bump BOTH CAT and GST so New Recruit cannot stay on an older cached catalogue.
cr.set('revision','69'); cr.set('gameSystemRevision','37'); gr.set('revision','37')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat': e.set('dataRevision','69')
    elif e.get('filePath')=='Prohammer 30k.gst': e.set('dataRevision','37')

# Duplicate/broken reference checks.
catids=[e.get('id') for e in cr.iter() if e.get('id')]; gstids=[e.get('id') for e in gr.iter() if e.get('id')]
assert len(catids)==len(set(catids)),'duplicate CAT IDs'; assert len(gstids)==len(set(gstids)),'duplicate GST IDs'
allids=set(catids)|set(gstids); broken=[]
for root in (cr,gr):
    for x in root.iter():
        for a in ('targetId','childId'):
            v=x.get(a)
            if v and v not in allids: broken.append((x.get('id'),a,v))
assert not broken,'broken refs: '+repr(broken[:30])

# IMPORTANT: serialize each BattleScribe XML document immediately after registering ITS namespace as default.
# Do not register CAT/GST/index namespaces together before writing; that caused the old ns0 ingestion regression.
ET.indent(ct,space='  '); ET.register_namespace('',CNS); ct.write(CAT,encoding='utf-8',xml_declaration=True)
ET.indent(gt,space='  '); ET.register_namespace('',GNS); gt.write(GST,encoding='utf-8',xml_declaration=True)
ET.indent(it,space='  '); ET.register_namespace('',INS); it.write(IDX,encoding='utf-8',xml_declaration=True)
cattext=CAT.read_text(encoding='utf-8'); gsttext=GST.read_text(encoding='utf-8')
assert '<ns0:' not in cattext and '<ns0:' not in gsttext
assert '<catalogue xmlns="http://www.battlescribe.net/schema/catalogueSchema"' in cattext
assert '<gameSystem xmlns="http://www.battlescribe.net/schema/gameSystemSchema"' in gsttext

OUT.write_text('\n'.join(report)+'\nCAT69 / GST37; canonical namespaces restored; duplicate IDs=0; broken refs=0.\n',encoding='utf-8')
print(OUT.read_text())
