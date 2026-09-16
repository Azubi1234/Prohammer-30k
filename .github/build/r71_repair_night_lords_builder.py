from pathlib import Path
import re

p=Path('.github/build/rev71_night_lords_live.py')
s=p.read_text(encoding='utf-8')

old='''def fixed_plus_extra(u,prefix,base,extra_cost,max_total,base_name='Base Squad',extra_name='Additional Models'):\n    b=entry(u,prefix+'-base',base_name,0,'model',base,base,base); ex=entry(u,prefix+'-extra',extra_name,extra_cost,'model',max_total-base,0,0); return b,ex\n'''
new='''def fixed_plus_extra(u,prefix,base,extra_cost,max_total,base_name='Base Squad',extra_name='Additional Models'):\n    # New Recruit UI standard: use one real model counter at the unit's true total size.\n    # The top-level unit pays the non-model remainder, while the counter pays the per-model value.\n    costs=u.findall('./'+C('costs')+'/'+C('cost'))\n    current=float(costs[0].get('value','0')) if costs else 0.0\n    set_points(u,current-(base*extra_cost))\n    m=entry(u,prefix+'-models',base_name.replace('Base Squad — ','') if 'Base Squad — ' in base_name else base_name,extra_cost,'model',max_total,base,base)\n    return m,m\n'''
if old not in s: raise SystemExit('fixed_plus_extra block not found')
s=s.replace(old,new)

old='''def dynamic_group_max(g,base,extra_id,prefix,per_extra=1):\n    c=max_constraint(g)\n    if c is None:c=constraint(g,prefix+'-max','max',base,child=True)\n    else:c.set('value',str(base))\n    m=ET.SubElement(ensure(g,'modifiers'),C('modifier'),{'id':prefix+'-inc','type':'increment','value':str(per_extra),'field':c.get('id')}); rs=ET.SubElement(m,C('repeats')); ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'parent','childId':extra_id,'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})\n'''
new='''def dynamic_group_max(g,base,extra_id,prefix,per_extra=1):\n    # extra_id is now the true total-model counter; allow one replacement per selected model.\n    c=max_constraint(g)\n    if c is None:c=constraint(g,prefix+'-max','max',0,child=True)\n    else:c.set('value','0')\n    m=ET.SubElement(ensure(g,'modifiers'),C('modifier'),{'id':prefix+'-inc','type':'increment','value':str(per_extra),'field':c.get('id')}); rs=ET.SubElement(m,C('repeats')); ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'parent','childId':extra_id,'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})\n'''
if old not in s: raise SystemExit('dynamic_group_max block not found')
s=s.replace(old,new)

old='''def per_five_group(p,i,n,extra_id):\n    g=group(p,i,n,maxv=1); c=max_constraint(g); m=ET.SubElement(ensure(g,'modifiers'),C('modifier'),{'id':i+'-ten','type':'increment','value':'1','field':c.get('id')}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'5','field':'selections','scope':'parent','childId':extra_id,'shared':'true','includeChildSelections':'true','includeChildForces':'false'}); return g\n'''
new='''def per_five_group(p,i,n,extra_id):\n    # All current users are 5-10 model squads: one choice at 5-9, two at 10.\n    g=group(p,i,n,maxv=1); c=max_constraint(g); m=ET.SubElement(ensure(g,'modifiers'),C('modifier'),{'id':i+'-ten','type':'increment','value':'1','field':c.get('id')}); cs=ET.SubElement(m,C('conditions')); ET.SubElement(cs,C('condition'),{'type':'atLeast','value':'10','field':'selections','scope':'parent','childId':extra_id,'shared':'true','includeChildSelections':'true','includeChildForces':'false'}); return g\n'''
if old not in s: raise SystemExit('per_five_group block not found')
s=s.replace(old,new)

old='''def scaled_toggle_multi(p,i,n,per,model_ids,ruletext=None):\n    e=entry(p,i,n,0)\n    mods=ensure(e,'modifiers')\n    for j,mid in enumerate(model_ids):\n        m=ET.SubElement(mods,C('modifier'),{'id':f'{i}-cost-{j}','type':'increment','value':str(per),'field':'pts'}); rs=ET.SubElement(m,C('repeats')); ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'root-entry','childId':mid,'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})\n'''
new='''def scaled_toggle_multi(p,i,n,per,model_ids,ruletext=None):\n    e=entry(p,i,n,0)\n    mods=ensure(e,'modifiers')\n    # Some callers pass the same total-model counter twice for backward helper compatibility.\n    unique_ids=list(dict.fromkeys(model_ids))\n    for j,mid in enumerate(unique_ids):\n        m=ET.SubElement(mods,C('modifier'),{'id':f'{i}-cost-{j}','type':'increment','value':str(per),'field':'pts'}); rs=ET.SubElement(m,C('repeats')); ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'root-entry','childId':mid,'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})\n'''
if old not in s: raise SystemExit('scaled_toggle_multi block not found')
s=s.replace(old,new)

old="""        if cap_extra<5:hide_if_atleast(v,prefix+'-'+src+'-cap',extra_id,cap_extra+1)\n"""
new="""        if cap_extra<5:hide_if_atleast(v,prefix+'-'+src+'-cap',extra_id,7)\n"""
if old not in s: raise SystemExit('infantry capacity line not found')
s=s.replace(old,new)

s=s.replace("hide_if_atleast(d,prefix+'-dread-cap',extra_id,1)","hide_if_atleast(d,prefix+'-dread-cap',extra_id,6)")
s=s.replace("hide_if_atleast(v,prefix+'-'+src+'-cap',extra_id,1)","hide_if_atleast(v,prefix+'-'+src+'-cap',extra_id,6)")

old="""    rf=link(war,prefix+'-rf','Refractor Field','gear-hq-refractor');show_if_all(rf,prefix+'-rf-show',[('atLeast',max_extra,'root-entry',extra_id)])\n"""
new="""    rf=link(war,prefix+'-rf','Refractor Field','gear-hq-refractor');show_if_all(rf,prefix+'-rf-show',[('atLeast',max_extra+5,'root-entry',extra_id)])\n"""
if old not in s: raise SystemExit('refractor threshold line not found')
s=s.replace(old,new)

# Pair of claws: its max follows the true Atramentar model counter, not base+additional arithmetic.
old="""pm=max_constraint(pair);m=ET.SubElement(ensure(pair,'modifiers'),C('modifier'),{'id':'r71-nl-atramentar-pair-inc','type':'increment','value':'1','field':pm.get('id')}); # reset base below\npm.set('value','5');rs=ET.SubElement(m,C('repeats'));ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'parent','childId':e.get('id'),'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})\n"""
new="""pm=max_constraint(pair);pm.set('value','0');m=ET.SubElement(ensure(pair,'modifiers'),C('modifier'),{'id':'r71-nl-atramentar-pair-inc','type':'increment','value':'1','field':pm.get('id')});rs=ET.SubElement(m,C('repeats'));ET.SubElement(rs,C('repeat'),{'value':'1','repeats':'1','field':'selections','scope':'parent','childId':e.get('id'),'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})\n"""
if old not in s: raise SystemExit('Atramentar pair block not found')
s=s.replace(old,new)

# Because fixed_plus_extra now returns the same total-model counter twice, validation expects one model selector rather than two.
old="""    u=U[key];models=[x for x in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if x.get('type')=='model'];assert len(models)>=2,(key,len(models));assert any(x.get('defaultAmount')=='5' for x in models);assert any(any(c.get('type')=='max' and c.get('value')==str(maxextra) for c in x.findall('./'+C('constraints')+'/'+C('constraint'))) and x.get('defaultAmount')=='0' for x in models)\n"""
new="""    u=U[key];models=[x for x in u.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')) if x.get('type')=='model'];assert len(models)>=1,(key,len(models));assert any(x.get('defaultAmount')=='5' for x in models);assert any(any(c.get('type')=='max' and c.get('value')==str(maxextra+5) for c in x.findall('./'+C('constraints')+'/'+C('constraint'))) and x.get('defaultAmount')=='5' for x in models)\n"""
if old not in s: raise SystemExit('unit-size validation line not found')
s=s.replace(old,new)

# Expand full Infantry/Jump Infantry coverage for the reusable squad upgrade system.
old="""ELIGIBLE_PREFIXES=('legion tactical squad','legion assault squad','legion breacher siege squad','legion reconnaissance squad','legion veteran squad','legion destroyer squad','legion seeker squad','legion heavy support squad')\n"""
new="""ELIGIBLE_PREFIXES=('legion tactical squad','legion assault squad','legion breacher siege squad','legion reconnaissance squad','legion veteran squad','legion destroyer squad','legion seeker squad','legion heavy support squad','legion command squad','legion honour guard squad','legion apothecarion detachment','legion apothecary detachment','techmarine covenant')\n"""
if old not in s: raise SystemExit('eligible prefix tuple not found')
s=s.replace(old,new)

old="""for idx,u in enumerate([x for x in cr.iter(C('selectionEntry')) if x.get('type')=='unit' and (x.get('name') or '').lower().startswith('legion terminator squad')]):\n"""
new="""for idx,u in enumerate([x for x in cr.iter(C('selectionEntry')) if x.get('type')=='unit' and ((x.get('name') or '').lower().startswith('legion terminator squad') or (x.get('name') or '').lower().startswith('legion terminator command squad'))]):\n"""
if old not in s: raise SystemExit('terminator transponder scan not found')
s=s.replace(old,new)

# Update audit summary wording to reflect expanded support.
s=s.replace('Generic eligible Sergeants receive Chainglaive/Trophies through their actual Sergeant Armoury groups.','Generic eligible Sergeants receive Chainglaive/Trophies through their actual Sergeant Armoury groups; Infantry/Jump Infantry support also covers Command, Honour Guard, Apothecarion and Techmarine units where applicable.')

p.write_text(s,encoding='utf-8')
compile(s,str(p),'exec')
print('Revision 71 builder repaired for New Recruit unit-size standard and full Infantry support.')
