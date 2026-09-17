from pathlib import Path
src=Path('.github/build/rev81_iron_hands_live_fix.py').read_text(encoding='utf-8')
old="role=byid(cr,'r42-role-x-1-effects-company-of-immortals-medusan-immortal-squads-r41-unit-x-0-medusan-immortal-squad')\nif role is None:raise RuntimeError('Missing Bitter Iron Immortal role clone')"
new="""role=next((u for u in cr.iter(C('selectionEntry')) if u.get('type')=='unit' and u.get('id')!=IMM and 'medusan immortal' in (u.get('name') or '').lower() and ('r42-role' in (u.get('id') or '') or 'bitter' in (u.get('id') or '').lower())),None)
if role is None:
 role=copy.deepcopy(byid(cr,IMM)); pref='r81-ih-bitter-role-'
 for z in role.iter():
  if z.get('id'):z.set('id',pref+z.get('id'))
 role.set('id','r81-ih-bitter-role');role.set('name','Medusan Immortal Squad — Company of Bitter Iron Troops')
 cr.find(C('selectionEntries')).append(role)"""
if old not in src:raise RuntimeError('Could not patch Bitter Iron role block')
src=src.replace(old,new)
exec(compile(src,'.github/build/rev81_iron_hands_live_fix.py','exec'))
