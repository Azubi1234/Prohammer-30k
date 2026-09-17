from pathlib import Path
src=Path('.github/build/rev79_iron_hands_full.py').read_text(encoding='utf-8')
src=src.replace("for l in cr.iter(C('entryLink')):\n    if l.get('targetId')!='r44-ih-autosimulacra':continue", "for auto_idx,l in enumerate(cr.iter(C('entryLink'))):\n    if l.get('targetId')!='r44-ih-autosimulacra':continue")
src=src.replace("'r79-ih-head-auto-free-'+re.sub('[^a-z0-9]+','-',l.get('id') or 'x')[-45:]", "f'r79-ih-head-auto-free-{auto_idx}'")
src=src.replace("'r79-ih-head-auto-min-'+re.sub('[^a-z0-9]+','-',l.get('id') or 'x')[-40:]", "f'r79-ih-head-auto-min-{auto_idx}'")
src=src.replace("'r79-ih-head-auto-force-'+re.sub('[^a-z0-9]+','-',l.get('id') or 'x')[-40:]", "f'r79-ih-head-auto-force-{auto_idx}'")
exec(compile(src,'.github/build/rev79_iron_hands_full.py','exec'))
