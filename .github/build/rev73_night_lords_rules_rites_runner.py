from pathlib import Path

src_path=Path('.github/build/rev73_night_lords_rules_rites.py')
src=src_path.read_text(encoding='utf-8')
needle="assert not has_stealth_selector(cur),'Curze must not purchase Stealth Adept'"
replacement="""# Curze inherited an obsolete purchasable Stealth Adept selector from an older Night Lords pass.\n# Remove that purchase: Night Haunter already grants him Stealth, and Primarchs do not buy generic armoury upgrades.\nfor _p in list(cur.iter()):\n    for _x in list(_p):\n        if _x.tag in (C('selectionEntry'),C('entryLink')) and 'stealth adept' in (_x.get('name') or '').lower():\n            _p.remove(_x)\nassert not has_stealth_selector(cur),'Curze must not purchase Stealth Adept'"""
if needle not in src:
    raise RuntimeError('Could not locate Curze Stealth validation hook')
patched=src.replace(needle,replacement,1)
exec(compile(patched,str(src_path),'exec'),{'__name__':'__main__','__file__':str(src_path)})
