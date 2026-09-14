from pathlib import Path
import subprocess,sys,xml.etree.ElementTree as ET
CNS='http://www.battlescribe.net/schema/catalogueSchema'; C=lambda t:f'{{{CNS}}}{t}'
subprocess.run([sys.executable,'.github/build/rev53_unit_sizes_and_sonic_hss.py'])
cr=ET.parse('Legiones Astartes.cat').getroot()
parent={c:p for p in cr.iter() for c in p}
rem=[]
for s in cr.iter(C('selectionEntry')):
    if (s.get('name') or '').strip().lower()!='additional model':continue
    chain=[]; x=s
    while x is not None:
        if x.tag==C('selectionEntry'):chain.append((x.get('id'),x.get('name'),x.get('type')))
        x=parent.get(x)
    rem.append(chain)
print('REMAINING ADDITIONAL MODEL ENTRIES:',len(rem))
for r in rem:print(r)
raise SystemExit(1 if rem else 0)
