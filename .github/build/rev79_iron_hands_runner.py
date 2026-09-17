from pathlib import Path
src=Path('.github/build/rev79_iron_hands_full.py').read_text(encoding='utf-8')
# Stable unique IDs for the free Autosimulacra modifiers.
src=src.replace("for l in cr.iter(C('entryLink')):\n    if l.get('targetId')!='r44-ih-autosimulacra':continue", "for auto_idx,l in enumerate(cr.iter(C('entryLink'))):\n    if l.get('targetId')!='r44-ih-autosimulacra':continue")
src=src.replace("'r79-ih-head-auto-free-'+re.sub('[^a-z0-9]+','-',l.get('id') or 'x')[-45:]", "f'r79-ih-head-auto-free-{auto_idx}'")
src=src.replace("'r79-ih-head-auto-min-'+re.sub('[^a-z0-9]+','-',l.get('id') or 'x')[-40:]", "f'r79-ih-head-auto-min-{auto_idx}'")
src=src.replace("'r79-ih-head-auto-force-'+re.sub('[^a-z0-9]+','-',l.get('id') or 'x')[-40:]", "f'r79-ih-head-auto-force-{auto_idx}'")
# Actual rule IDs must remain unique across canonical entries and deep clones.
src=src.replace("add_rule(u,'r79-ih-rule-'+key+'-'+re.sub('[^a-z0-9]+','-',n.lower()).strip('-'),n,text or COMMON.get(n,n))", "add_rule(u,'r79-ih-rule-'+re.sub('[^a-z0-9]+','-',u.get('id') or key)[-42:]+'-'+re.sub('[^a-z0-9]+','-',n.lower()).strip('-'),n,text or COMMON.get(n,n))")
# Only unit shells, not nested selections, are presentation-cleanup targets.
src=src.replace("if any(c in uid for c in canon) or uid in ('r46-al-reward-25','r46-al-reward-26','r46-al-reward-27'):\n        relevant.append(u)", "if u.get('type')=='unit' and (any(c in uid for c in canon) or uid in ('r46-al-reward-25','r46-al-reward-26','r46-al-reward-27')):\n        relevant.append(u)")
# Scions of Iron must never bleed into other Legions. Restrict it to the shared generic
# infantry squads that can actually carry a Rhino in the base list plus Medusan Immortals.
old="""    for u in cr.iter(C('selectionEntry')):\n        if u.get('type')!='unit':continue\n        n=(u.get('name') or '').lower()\n        if any(x in n for x in ('terminator','bike','jetbike','dreadnought','vehicle','tank','speeder')):continue\n        for g in rhino_transport_groups(u):"""
new="""    SCIONS_BASE_IDS={'tactical-unit','assault-unit','breacher-unit','recon-unit','veteran-unit','destroyer-unit','techmarine-covenant','fa-seeker','hs-heavy-support-squad',IDS['imm']}\n    for u in cr.iter(C('selectionEntry')):\n        if u.get('type')!='unit' or u.get('id') not in SCIONS_BASE_IDS:continue\n        n=(u.get('name') or '').lower()\n        if any(x in n for x in ('terminator','bike','jetbike','dreadnought','vehicle','tank','speeder')):continue\n        for g in rhino_transport_groups(u):"""
if old not in src: raise RuntimeError('Could not patch Scions candidate loop')
src=src.replace(old,new)
# A Dedicated Transport choice is not a model counter. This also prevents the permanent
# squad-size audit from treating a vehicle choice as expandable squad composition.
src=src.replace("x.set('id',eid);x.set('name','Land Raider '+('Phobos' if slug=='phobos' else 'Proteus')+' (Scions of Iron)');x.set('hidden','true')", "x.set('id',eid);x.set('name','Land Raider '+('Phobos' if slug=='phobos' else 'Proteus')+' (Scions of Iron)');x.set('type','upgrade');x.set('hidden','true')")
exec(compile(src,'.github/build/rev79_iron_hands_full.py','exec'))
