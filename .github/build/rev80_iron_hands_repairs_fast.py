from pathlib import Path
p=Path('.github/build/rev80_iron_hands_repairs.py')
s=p.read_text(encoding='utf-8')
s=s.replace("def byid(root,i):return next((e for e in root.iter() if e.get('id')==i),None)","PM={c:p for p in cr.iter() for c in p}\ndef byid(root,i):return next((e for e in root.iter() if e.get('id')==i),None)")
s=s.replace("def remove_node(root,node):\n    pm={c:p for p in root.iter() for c in p};p=pm.get(node)\n    if p is not None:p.remove(node)","def remove_node(root,node):\n    p=PM.get(node)\n    if p is not None:p.remove(node)")
s=s.replace("def owner_unit(node):\n    pm={c:p for p in cr.iter() for c in p};x=node\n    while x is not None:\n        if x.tag==C('selectionEntry') and x.get('type')=='unit':return x\n        x=pm.get(x)","def owner_unit(node):\n    x=node\n    while x is not None:\n        if x.tag==C('selectionEntry') and x.get('type')=='unit':return x\n        x=PM.get(x)")
s=s.replace("    p=e\n    pm={c:p for p in cr.iter() for c in p};anc=pm.get(e);inside=False", "    anc=PM.get(e);inside=False")
s=s.replace("        anc=pm.get(anc)","        anc=PM.get(anc)")
exec(compile(s,str(p),'exec'))
