from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'
cr=ET.parse(CAT).getroot(); gr=ET.parse(GST).getroot(); top=cr.find(C('selectionEntries'))

def by_id(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def top_matches(q):
    q=q.lower(); return [e for e in list(top) if q in (e.get('name') or '').lower()]
def groups(e): return [(g.get('id'),g.get('name')) for g in e.iter(C('selectionEntryGroup'))]

def show(q):
    print('\nQUERY',q)
    for e in top_matches(q):
        print(' TOP',e.get('id'),repr(e.get('name')),'type',e.get('type'),'hidden',e.get('hidden'))
        print('  GROUPS',groups(e)[:25])
        print('  CATS',[(x.get('targetId'),x.get('name')) for x in e.iter(C('categoryLink'))][:10])
        print('  RULES',[(x.get('id'),x.get('name')) for x in e.findall('.//'+C('rule'))][:20])
        print('  PROFILES',[(x.get('id'),x.get('name'),x.get('typeId')) for x in e.findall('.//'+C('profile'))][:20])

for q in ['grey slayer','grey stalker','wolf scout','deathsworn','jorlund','varagyr','fenrisian wolf','hvarl','geigor','bj','ohthere','leman russ','legion command squad','terminator command squad','honour guard','rhino','drop pod','dreadclaw','land raider','spartan','rapier','artillery']:
    show(q)

for i in ['hq-praetor','hq-centurion','hq-consul-librarian','hq-consul-chaplain','r25-rite-vi-0-the-pale-hunters','r25-rite-vi-1-the-bloodied-claws']:
    e=by_id(i); print('\nID',i,'FOUND',bool(e))
    if e is not None:
        print(' NAME',e.get('name'),'GROUPS',groups(e)[:50])
        print(' RULES',[(x.get('id'),x.get('name')) for x in e.findall('.//'+C('rule'))][:40])

# print likely sergeant armoury groups and librarian ML2 subtree markers
for e in cr.iter(C('selectionEntryGroup')):
    n=(e.get('name') or '').lower(); i=e.get('id','')
    if 'armoury' in n or i=='r61-librarian-power2':
        print('GROUP',i,repr(e.get('name')),'PARENT?', 'entries',len(e.findall('.//'+C('selectionEntry'))),'links',len(e.findall('.//'+C('entryLink'))))

# game-system FOC
for x in gr.iter(G('categoryLink')):
    if x.get('id') in ['fl-hq','fl-troops','fl-elites','fl-fast','fl-heavy','fl-transport','fl-low']:
        print('FOC',x.get('id'),x.get('name'),ET.tostring(x,encoding='unicode')[:2500])
