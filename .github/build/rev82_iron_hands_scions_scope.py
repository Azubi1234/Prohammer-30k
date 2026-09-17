from pathlib import Path
import copy,re,xml.etree.ElementTree as ET
CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r82-iron-hands-scions-scope.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema';GNS='http://www.battlescribe.net/schema/gameSystemSchema';INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS);ET.register_namespace('',GNS);ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}';G=lambda t:f'{{{GNS}}}{t}';I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT);cr=ct.getroot();gt=ET.parse(GST);gr=gt.getroot();it=ET.parse(IDX);ir=it.getroot()
if cr.get('revision')!='81' or gr.get('revision')!='48':raise RuntimeError(f'Expected 81/48, got {cr.get("revision")}/{gr.get("revision")}')
HEAD='r25-rite-x-0-the-head-of-the-gorgon';LEG='legion-x'
def byid(root,i):return next((e for e in root.iter() if e.get('id')==i),None)
def ensure(p,t):
 x=p.find(C(t));
 if x is None:x=ET.SubElement(p,C(t))
 return x
def wipe(p,t):
 x=p.find(C(t));
 if x is not None:p.remove(x)
def setpts(e,v):
 cs=ensure(e,'costs');[cs.remove(x) for x in list(cs)];ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})
def stripcats(e):wipe(e,'categoryLinks')
def find_named(name):return next((e for e in cr.iter(C('selectionEntry')) if (e.get('name') or '').strip().lower()==name.lower()),None)
def parentmap():return {c:p for p in cr.iter() for c in p}
# remove all prior Scions generated entries
removed=0
for p in list(cr.iter()):
 ses=p.find(C('selectionEntries'))
 if ses is not None:
  for x in list(ses):
   if 'scions' in (x.get('id') or '') and ('phobos' in (x.get('id') or '') or 'proteus' in (x.get('id') or '')):
    ses.remove(x);removed+=1
PM=parentmap()
def top_unit(e):
 x=e;last=None
 while x is not None:
  if x.tag==C('selectionEntry') and x.get('type')=='unit':last=x
  x=PM.get(x)
 return last
def gated_other_legion(u):
 if u is None:return True
 for c in u.iter(C('condition')):
  ch=c.get('childId') or ''
  if ch.startswith('legion-') and ch!=LEG:return True
 return False
def rhino_groups(u):
 out=[]
 for g in u.iter(C('selectionEntryGroup')):
  if 'dedicated transport' not in (g.get('name') or '').lower():continue
  choices=list(g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')))+list(g.findall('./'+C('entryLinks')+'/'+C('entryLink')))
  rh=next((x for x in choices if 'rhino' in (x.get('name') or '').lower()),None)
  if rh is not None:out.append((g,rh))
 return out
ph=find_named('Land Raider Phobos');pr=find_named('Land Raider Proteus')
if ph is None or pr is None:raise RuntimeError('Missing LR patterns')
added=[];seen=set()
for u in list(cr.iter(C('selectionEntry'))):
 if u.get('type')!='unit':continue
 top=top_unit(u)
 if gated_other_legion(top):continue
 # only generic Legion infantry structures, universal role copies, or Iron Hands entries
 name=(u.get('name') or '').lower();tid=(top.get('id') or '') if top is not None else ''
 generic=any(name.startswith(x) for x in ('legion tactical squad','legion breacher siege squad','legion reconnaissance squad','legion veteran squad','legion destroyer squad','legion seeker squad','legion heavy support squad','legion command squad','legion honour guard squad','techmarine covenant','medusan immortal squad'))
 iron='r41-unit-x-' in tid or 'r81-ih-' in tid
 if not (generic or iron):continue
 for g,rh in rhino_groups(u):
  key=(u.get('id'),g.get('id'))
  if key in seen:continue
  seen.add(key)
  for base,label,cost in ((ph,'Land Raider Phobos (Scions of Iron)',250),(pr,'Land Raider Proteus (Scions of Iron)',200)):
   idx=len(added);pref=f'r82-ih-scions-{idx}-';x=copy.deepcopy(base)
   for z in x.iter():
    if z.get('id'):z.set('id',pref+z.get('id'))
   x.set('id',pref+('phobos' if 'Phobos' in label else 'proteus'));x.set('name',label);x.set('type','upgrade');stripcats(x);setpts(x,cost)
   # copy Rhino visibility modifiers/hidden state, then require Head of the Gorgon
   wipe(x,'modifiers');rmods=rh.find(C('modifiers'))
   if rmods is not None:
    mods=ensure(x,'modifiers')
    for mm in list(rmods):
     cp=copy.deepcopy(mm)
     for z in cp.iter():
      if z.get('id'):z.set('id',pref+z.get('id'))
     mods.append(cp)
   x.set('hidden',rh.get('hidden','false'));m=ET.SubElement(ensure(x,'modifiers'),C('modifier'),{'id':pref+'hide-without-head','type':'set','value':'true','field':'hidden'});cs=ET.SubElement(m,C('conditions'));ET.SubElement(cs,C('condition'),{'type':'lessThan','value':'1','field':'selections','scope':'roster','childId':HEAD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
   ensure(g,'selectionEntries').append(x);added.append((u.get('id'),u.get('name'),g.get('id'),label))
# revisions
cr.set('revision','82');cr.set('gameSystemRevision','49');gr.set('revision','49')
for e in ir.iter(I('dataIndexEntry')):
 if e.get('filePath')=='Legiones Astartes.cat':e.set('dataRevision','82')
 elif e.get('filePath')=='Prohammer 30k.gst':e.set('dataRevision','49')
# validate no Scions attached under other-Legion gated top unit
PM=parentmap();bad=[]
for x in cr.iter(C('selectionEntry')):
 if (x.get('id') or '').startswith('r82-ih-scions-'):
  t=top_unit(x)
  if gated_other_legion(t):bad.append((x.get('id'),t.get('id') if t is not None else None))
if bad:raise RuntimeError('Cross-legion Scions leakage '+str(bad[:10]))
# duplicate IDs
for root,label in ((cr,'CAT'),(gr,'GST')):
 seenids=set();dup=[]
 for e in root.iter():
  i=e.get('id')
  if i:
   if i in seenids:dup.append(i)
   seenids.add(i)
 if dup:raise RuntimeError(label+' duplicates '+str(dup[:10]))
ET.indent(ct,space='  ');ET.indent(gt,space='  ');ET.indent(it,space='  ');ct.write(CAT,encoding='utf-8',xml_declaration=True);gt.write(GST,encoding='utf-8',xml_declaration=True);it.write(IDX,encoding='utf-8',xml_declaration=True);ET.parse(CAT);ET.parse(GST);ET.parse(IDX)
OUT.write_text('Revision 82 — Iron Hands Scions scope correction\nCAT=82 GST=49\nRemoved prior Scions entries: %d\nAdded legal/generic Iron Hands Scions entries: %d\nNo Scions entries remain under units explicitly gated to another Legion.\n\n%s\n'%(removed,len(added),'\n'.join(f'- {a[1]} :: {a[3]}' for a in added)),encoding='utf-8');print(OUT.read_text())
