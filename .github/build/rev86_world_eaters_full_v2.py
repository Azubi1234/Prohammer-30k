from pathlib import Path

# Hotfix the R86 implementation before executing it.  The first R86 pass
# correctly identified the source values, but the old R41 importer never
# materialised "Additional model" selections for these World Eaters units.
# Build those selections here and make per-model squad upgrades scale with
# them automatically in New Recruit.
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
 cand=[x for x in e.iter(C('selectionEntry')) if (x.get('name') or '').lower().startswith('additional model')]
 if cand:
  x=cand[0]
 else:
  es=ensure(e,'selectionEntries')
  x=ET.SubElement(es,C('selectionEntry'),{'id':e.get('id')+'-r86-additional','name':'Additional model','type':'model','hidden':'false','import':'true'})
 set_cost(x,cost)
 if maxn is not None:
  cons=ensure(x,'constraints'); mx=next((c for c in cons.findall(C('constraint')) if c.get('type')=='max' and c.get('field')=='selections'),None)
  if mx is None:
   add_constraint(x,x.get('id')+'-max','max',maxn)
  else:
   mx.set('value',str(maxn))
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
 # Charge the starting squad immediately, then automatically add the same
 # per-model surcharge for every selected Additional model.
 adds=[x for x in e.iter(C('selectionEntry')) if (x.get('name') or '').lower().startswith('additional model')]
 add_id=adds[0].get('id') if adds else None
 for x in e.iter(C('selectionEntry')):
  nm=x.get('name') or ''
  m=re.search(r'\\(base unit; \\+([0-9]+) pts/model\\)',nm)
  if not m:continue
  pp=int(m.group(1)); set_cost(x,pp*base_count)
  if add_id:
   mods=ensure(x,'modifiers')
   mid='r86-scaled-cost-'+x.get('id')
   for old in list(mods):
    if old.get('id')==mid:mods.remove(old)
   mod=ET.SubElement(mods,C('modifier'),{'id':mid,'type':'increment','field':'pts','value':str(pp)})
   reps=ET.SubElement(mod,C('repeats'))
   ET.SubElement(reps,C('repeat'),{'field':'selections','scope':'parent','value':'1','percentValue':'false','shared':'true','includeChildSelections':'true','includeChildForces':'false','childId':add_id,'repeats':'1','roundUp':'false'})
  add_rule(x,'r86-scaled-'+x.get('id'),'Per-model cost',f'This upgrade costs +{pp} points per model and automatically scales with additional models selected for the squad.')
'''
if old_scaling not in src:
    raise RuntimeError('Could not locate R86 squadwide scaling helper for hotfix')
src = src.replace(old_scaling, new_scaling, 1)

# In the source data the third value is both the starting model count and the
# maximum number of additional models for each of the six affected units.
src = src.replace('e=unit(uid); set_cost(e,base); additional(e,extra); clean_squadwide_scaling(e,bc)',
                  'e=unit(uid); set_cost(e,base); additional(e,extra,bc); clean_squadwide_scaling(e,bc)')
src = src.replace('set_cost(e,base); additional(e,extra); clean_squadwide_scaling(e,bc)',
                  'set_cost(e,base); additional(e,extra,bc); clean_squadwide_scaling(e,bc)')
src = src.replace('set_cost(rite_ramp,110); additional(rite_ramp,22); clean_squadwide_scaling(rite_ramp,5)',
                  'set_cost(rite_ramp,110); additional(rite_ramp,22,5); clean_squadwide_scaling(rite_ramp,5)')

exec(compile(src, str(path), 'exec'), {'__name__':'__main__','__file__':str(path)})
