from pathlib import Path
import re
p=Path('.github/build/rev63_space_wolves_full.py')
s=p.read_text(encoding='utf-8')
# local_option(parent,id,name,cost,maxv=..., <rule text>) -> keyword rule=...
s2=re.sub(r"maxv=(\d+),('(?:[^'\\]|\\.)*')", r"maxv=\1,rule=\2", s)
if s2==s:
    raise SystemExit('No replacements made')
p.write_text(s2,encoding='utf-8')
print('Fixed', s.count('maxv='), 'maxv occurrences; changed', sum(a!=b for a,b in zip(s.splitlines(),s2.splitlines())), 'lines')
