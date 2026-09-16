from pathlib import Path
p=Path('.github/build/rev71_night_lords_live.py')
s=p.read_text(encoding='utf-8')
old="assert max_constraint(byid(cr,'r71-nl-contekar-ranged')).get('value')=='5'"
new="assert max_constraint(byid(cr,'r71-nl-contekar-ranged')).get('value')=='0'"
if old not in s:
    raise SystemExit('Contekar validation assertion not found')
s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
compile(s,str(p),'exec')
print('Revision 71 second repair applied: validation follows dynamic total-model replacement cap.')
