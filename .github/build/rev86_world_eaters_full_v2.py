from pathlib import Path

# R86 source values are correct; this wrapper converts the old importer's
# missing "additional models" into the repository's permanent New Recruit
# unit-size standard: one real model counter with a non-zero default quantity.
path = Path('.github/build/rev86_world_eaters_full.py')
src = path.read_text(encoding='utf-8')

old_additional = '''def additional(e,cost,maxn=None):
 cand=[x for x in e.iter(C('selectionEntry')) if (x.get('name') or '').lower().startswith('additional model')]
 if not cand:return False
 x=cand[0]; set_cost(x,cost)
 if maxn is not None:
  cons=ensure(x,'constraints'); mx=next((c for c in cons.findall(C('constraint')) if c.get('type')=='max' and c.get('field')=='selections'),None)
  if mx is not None:mx.set('value',str(maxn))
 return True
'''
new_additional = '''def additional(e,cost,maxn=None):
 # maxn is the starting squad size for these six XII Legion units and also
 # their maximum number of extra models. Represent 5-10 / 10-20 directly.
 base_count=int(maxn or 1)
 # Remove a legacy Additional-model entry if one somehow exists.
 for p in list(e.iter()):
  for old in list(p):
   if old.tag==C('selectionEntry') and (old.get('name') or '').lower().startswith('additional model'):
    p.remove(old)
 es=ensure(e,'selectionEntries')
 sid=e.get('id')+'-r86-size'
 x=next((z for z in es.findall(C('selectionEntry')) if z.get('id')==sid),None)
 if x is None:
  label_map={
   'r41-unit-xii-0-rampager-squad':'Rampager',
   'r41-unit-xii-1-red-butcher-squad':'Red Butcher',
   'r41-unit-xii-2-red-hand-destroyer-mortalis-squad':'Red Hand Destroyer',
   'r41-unit-xii-3-world-eaters-inductii-squad':'Inductii',
   'r41-unit-xii-4-devourer-terminator-squad':'Devourer',
   'r41-unit-xii-5-triarii-breacher-squad':'Triarii Breacher',
  }
  # Rite / Rewards copies inherit their source name; a generic label is fine
  # there because the parent unit already identifies the formation.
  label=label_map.get(e.get('id'),'Squad model')
  x=ET.SubElement(es,C('selectionEntry'),{'id':sid,'name':label,'type':'model','hidden':'false','import':'true','defaultAmount':str(base_count)})
 set_cost(x,cost)
 cons=ensure(x,'constraints')
 for c in list(cons):
  if c.get('field')=='selections' and c.get('type') in ('min','max'):cons.remove(c)
 add_constraint(x,sid+'-min','min',base_count)
 add_constraint(x,sid+'-max','max',base_count*2)
 return x
'''
if old_additional not in src:
    raise RuntimeError('Could not locate R86 additional() helper for hotfix')
src = src.replace(old_additional, new_additional, 1)

old_scaling = '''def clean_squadwide_scaling(e,base_count):
 # Old importer charged only the parsed base unit for per-model options. Make the visible base charge correct and add a note so roster totals remain auditable.
 for x in e.iter(C('selectionEntry')):
  nm=x.get('name') or ''
  m=re.search(r'\\(base unit; \\+([0-9]+) pts/model\\)',nm)
  if not m:continue
  pp=int(m.group(1)); set_cost(x,pp*base_count)
  add_rule(x,'r86-scaled-'+x.get('id'),'Per-model cost',f'This upgrade costs +{pp} points per model. The displayed base cost covers the unit\\'s starting {base_count} models; add +{pp} points for each additional model selected.')
'''
new_scaling = '''def clean_squadwide_scaling(e,base_count):
 # Whole-squad +X/model upgrades are priced from the live squad-size counter,
 # so adding models automatically increases the upgrade cost too.
 sizes=[x for x in e.iter(C('selectionEntry')) if (x.get('id') or '').endswith('-r86-size')]
 size_id=sizes[0].get('id') if sizes else None
 for x in e.iter(C('selectionEntry')):
  nm=x.get('name') or ''
  m=re.search(r'\\(base unit; \\+([0-9]+) pts/model\\)',nm)
  if not m:continue
  pp=int(m.group(1)); set_cost(x,0)
  if size_id:
   mods=ensure(x,'modifiers'); mid='r86-scaled-cost-'+x.get('id')
   for old in list(mods):
    if old.get('id')==mid:mods.remove(old)
   mod=ET.SubElement(mods,C('modifier'),{'id':mid,'type':'increment','field':'pts','value':str(pp)})
   reps=ET.SubElement(mod,C('repeats'))
   ET.SubElement(reps,C('repeat'),{'field':'selections','scope':'parent','value':'1','percentValue':'false','shared':'true','includeChildSelections':'true','includeChildForces':'false','childId':size_id,'repeats':'1','roundUp':'false'})
  add_rule(x,'r86-scaled-'+x.get('id'),'Per-model cost',f'This upgrade costs +{pp} points per model and automatically scales with the squad size selected.')
'''
if old_scaling not in src:
    raise RuntimeError('Could not locate R86 squadwide scaling helper for hotfix')
src = src.replace(old_scaling, new_scaling, 1)

# The imported top-level cost is the fixed squad premium; the model counter
# supplies the per-model portion. This yields the exact source starting cost
# and exact cost for every additional model without a legacy Additional entry.
src = src.replace('e=unit(uid); set_cost(e,base); additional(e,extra); clean_squadwide_scaling(e,bc)',
                  'e=unit(uid); set_cost(e,base-(extra*bc)); additional(e,extra,bc); clean_squadwide_scaling(e,bc)')
src = src.replace('set_cost(e,base); additional(e,extra); clean_squadwide_scaling(e,bc)',
                  'set_cost(e,base-(extra*bc)); additional(e,extra,bc); clean_squadwide_scaling(e,bc)')
src = src.replace('set_cost(rite_ramp,110); additional(rite_ramp,22); clean_squadwide_scaling(rite_ramp,5)',
                  'set_cost(rite_ramp,0); additional(rite_ramp,22,5); clean_squadwide_scaling(rite_ramp,5)')

old_validation = '''for uid,(base,extra,bc) in fixes.items():
 e=byid(rr,uid); pts=next(c for c in e.findall('./'+C('costs')+'/'+C('cost')) if c.get('typeId')=='pts'); assert float(pts.get('value'))==base
 a=[x for x in e.iter(C('selectionEntry')) if (x.get('name') or '').lower().startswith('additional model')]
 assert a, uid+' no additional model'; ap=next(c for c in a[0].findall('./'+C('costs')+'/'+C('cost')) if c.get('typeId')=='pts'); assert float(ap.get('value'))==extra
'''
new_validation = '''for uid,(base,extra,bc) in fixes.items():
 e=byid(rr,uid)
 pts=next(c for c in e.findall('./'+C('costs')+'/'+C('cost')) if c.get('typeId')=='pts')
 sizes=[x for x in e.iter(C('selectionEntry')) if (x.get('id') or '').endswith('-r86-size')]
 assert sizes, uid+' no squad-size model counter'
 s=sizes[0]; sp=next(c for c in s.findall('./'+C('costs')+'/'+C('cost')) if c.get('typeId')=='pts')
 assert float(sp.get('value'))==extra
 assert s.get('defaultAmount')==str(bc)
 cs=s.findall('./'+C('constraints')+'/'+C('constraint'))
 assert any(c.get('type')=='min' and c.get('value')==str(bc) for c in cs)
 assert any(c.get('type')=='max' and c.get('value')==str(bc*2) for c in cs)
 assert float(pts.get('value')) + bc*extra == base
'''
if old_validation not in src:
    raise RuntimeError('Could not locate R86 final size validation for hotfix')
src = src.replace(old_validation, new_validation, 1)

exec(compile(src, str(path), 'exec'), {'__name__':'__main__','__file__':str(path)})
