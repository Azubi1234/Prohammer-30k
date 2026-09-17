from pathlib import Path
import copy,re,xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat');GST=Path('Prohammer 30k.gst');IDX=Path('index.xml');OUT=Path('inspection-r83-iron-hands-scions-final.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema';GNS='http://www.battlescribe.net/schema/gameSystemSchema';INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS);ET.register_namespace('',GNS);ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}';G=lambda t:f'{{{GNS}}}{t}';I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT);cr=ct.getroot();gt=ET.parse(GST);gr=gt.getroot();it=ET.parse(IDX);ir=it.getroot()
if cr.get('revision')!='82' or gr.get('revision')!='49':raise RuntimeError(f'Expected CAT82/GST49, got CAT{cr.get("revision")}/GST{gr.get("revision")}')
HEAD='r25-rite-x-0-the-head-of-the-gorgon';LEG='legion-x';IMM='r41-unit-x-0-medusan-immortal-squad'
def byid(root,i):return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t,Q=C):
 x=p.find(Q(t));
 if x is None:x=ET.SubElement(p,Q(t))
 return x
def wipe(p,t,Q=C):
 x=p.find(Q(t));
 if x is not None:p.remove(x)
def setpts(e,v):
 cs=ensure(e,'costs');[cs.remove(x) for x in list(cs)];ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def constraint(p,i,typ,val,scope='parent'):
 return ET.SubElement(ensure(p,'constraints'),C('constraint'),{'id':i,'type':typ,'value':str(val),'field':'selections','scope':scope,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def clone_link(src,pref):
 x=copy.deepcopy(src)
 for z in x.iter():
  if z.get('id'):z.set('id',pref+z.get('id'))
 return x
def clone_entry(src,pref,name=None):
 x=copy.deepcopy(src)
 for z in x.iter():
  if z.get('id'):z.set('id',pref+z.get('id'))
 if name:x.set('name',name)
 return x
def hide_without_head(x,pref):
 x.set('hidden','true');m=ET.SubElement(ensure(x,'modifiers'),C('modifier'),{'id':pref+'show-head','type':'set','value':'false','field':'hidden'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
def add_hide_over_10(g,pref,u):
 models=[m for m in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if m.get('type')=='model']
 # Current normalized Iron Hands squads use a total-model counter where possible; otherwise use the expandable non-sergeant counter (>9 means >10 total).
 counter=next((m for m in models if 'squad models' in (m.get('name') or '').lower()),None)
 if counter is not None:
  child=counter.get('id');threshold='10'
 else:
  exp=next((m for m in models if any(c.get('type')=='max' and float(c.get('value','0'))>1 for c in m.findall('./'+C('constraints')+'/'+C('constraint')))),None)
  if exp is None:return
  child=exp.get('id');threshold='9'
 mod=ET.SubElement(ensure(g,'modifiers'),C('modifier'),{'id':pref+'hide-over10','type':'set','value':'true','field':'hidden'});cs=ET.SubElement(mod,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'greaterThan','value':threshold,'field':'selections','scope':'root-entry','childId':child,'shared':'true','includeChildSelections':'false','includeChildForces':'false'})
# Remove any generated Scions entries from R82 or remnants.
removed=0
for p in list(cr.iter()):
 ses=p.find(C('selectionEntries'))
 if ses is not None:
  for x in list(ses):
   if 'scions' in (x.get('id') or '').lower() and ('phobos' in (x.get('id') or '').lower() or 'proteus' in (x.get('id') or '').lower()):ses.remove(x);removed+=1
# Source LR entries from existing Honour Guard LR group (known good transport copies).
hon=byid(cr,'hq-praetor-ret-honour');ph=pr=None
if hon is not None:
 for x in hon.iter(C('selectionEntry')):
  if (x.get('name') or '')=='Land Raider Phobos':ph=x
  if (x.get('name') or '')=='Land Raider Proteus':pr=x
if ph is None or pr is None:raise RuntimeError('Could not find reusable Phobos/Proteus transport entries')
# Exact canonical/generic entries whose current army-list structure contains a normal Rhino DT.
TARGETS={
 'tactical-unit':'tac-transport','recon-unit':'recon-transport','veteran-unit':'veteran-transport','destroyer-unit':'destroyer-transport','fa-seeker':'fa-seeker-transport','hs-heavy-support-squad':'hs-hss-transport','hq-praetor-ret-honour':'hq-praetor-ret-honour-transport','hq-centurion-ret-command':'hq-centurion-ret-command-transport',
 'techmarine-covenant':'techmarine-I-transport'
}
added=[]
for uid,gid in TARGETS.items():
 u=byid(cr,uid);g=byid(cr,gid)
 if u is None or g is None:continue
 # Add inside the same normal DT group so its normal Rhino availability/capacity visibility remains authoritative.
 for base,label in ((ph,'Land Raider Phobos (Scions of Iron)'),(pr,'Land Raider Proteus (Scions of Iron)')):
  pref=f'r83-ih-scions-{len(added)}-';x=clone_entry(base,pref,label);x.set('type','upgrade');wipe(x,'categoryLinks');wipe(x,'constraints');constraint(x,pref+'max','max',1);hide_without_head(x,pref);ensure(g,'selectionEntries').append(x);added.append((uid,gid,label))
# Medusan Immortals currently lacked their source-listed DT menu. Rebuild exact <=10 menu from source.
imm=byid(cr,IMM)
if imm is None:raise RuntimeError('Missing Medusan Immortals')
# Remove old generated dedicated transport groups if any exact R83 ID exists.
groups=ensure(imm,'selectionEntryGroups');old=next((x for x in groups.findall(C('selectionEntryGroup')) if x.get('id')=='r83-ih-imm-transport'),None)
if old is not None:groups.remove(old)
ig=ET.SubElement(groups,C('selectionEntryGroup'),{'id':'r83-ih-imm-transport','name':'Dedicated Transport (10 models or fewer)','hidden':'false'});constraint(ig,'r83-ih-imm-transport-max','max',1);add_hide_over_10(ig,'r83-ih-imm-transport-',imm)
# Reuse canonical shared transport links from Veteran DT for Rhino/Drop/Dreadclaw.
vg=byid(cr,'veteran-transport')
if vg is None:raise RuntimeError('Missing Veteran transport source')
for nm in ('Rhino','Drop Pod','Dreadclaw Drop Pod'):
 src=next((x for x in vg.findall('./'+C('entryLinks')+'/'+C('entryLink')) if (x.get('name') or '')==nm),None)
 if src is not None:ensure(ig,'entryLinks').append(clone_link(src,'r83-ih-imm-'+re.sub('[^a-z0-9]+','-',nm.lower())+'-'))
# Land Raider normal option per current Immortal entry: Phobos/Proteus where capacity permits.
for base,label in ((ph,'Land Raider Phobos'),(pr,'Land Raider Proteus')):
 x=clone_entry(base,'r83-ih-imm-'+re.sub('[^a-z0-9]+','-',label.lower())+'-',label);x.set('type','upgrade');wipe(x,'categoryLinks');wipe(x,'constraints');constraint(x,'r83-ih-imm-'+re.sub('[^a-z0-9]+','-',label.lower())+'-max','max',1);ensure(ig,'selectionEntries').append(x)
# Head Scions duplicates are not needed on Immortals because their normal source entry already permits Land Raider at <=10.
# Revisions/cache.
cr.set('revision','83');cr.set('gameSystemRevision','50');gr.set('revision','50')
for e in ir.iter(I('dataIndexEntry')):
 if e.get('filePath')=='Legiones Astartes.cat':e.set('dataRevision','83')
 elif e.get('filePath')=='Prohammer 30k.gst':e.set('dataRevision','50')
# Validation.
assert len(added)>=12,added
assert byid(cr,'r83-ih-imm-transport') is not None
# Generated Scions must exist only below the explicit target groups.
pm={c:p for p in cr.iter() for c in p};bad=[]
for x in cr.iter(C('selectionEntry')):
 if (x.get('id') or '').startswith('r83-ih-scions-'):
  p=pm.get(x)
  if p is None or p.get('id') not in set(TARGETS.values()):bad.append((x.get('id'),p.get('id') if p is not None else None))
if bad:raise RuntimeError('Scions outside explicit groups '+str(bad))
for root,label in ((cr,'CAT'),(gr,'GST')):
 seen=set();dup=[]
 for e in root.iter():
  i=e.get('id')
  if i:
   if i in seen:dup.append(i)
   seen.add(i)
 if dup:raise RuntimeError(label+' duplicate IDs '+str(dup[:10]))
ET.indent(ct,space='  ');ET.indent(gt,space='  ');ET.indent(it,space='  ');ct.write(CAT,encoding='utf-8',xml_declaration=True);gt.write(GST,encoding='utf-8',xml_declaration=True);it.write(IDX,encoding='utf-8',xml_declaration=True);ET.parse(CAT);ET.parse(GST);ET.parse(IDX)
OUT.write_text(f'''Revision 83 — Iron Hands Scions final correction\nCAT=83 GST=50\nRemoved prior generated Scions entries: {removed}\nAdded explicit legal Scions choices: {len(added)}\nScions are now attached only to the known normal-Rhino Dedicated Transport groups listed below.\nMedusan Immortals also regained their current-source Dedicated Transport menu for squads of 10 or fewer: Rhino, Drop Pod, Dreadclaw, Phobos or Proteus.\n\n'''+"\n".join(f'- {u} / {g}: {n}' for u,g,n in added),encoding='utf-8');print(OUT.read_text())
