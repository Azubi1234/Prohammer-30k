from pathlib import Path
import re

cat_path = Path('Legiones Astartes.cat')
gst_path = Path('Prohammer 30k.gst')

CAT_NS = 'http://www.battlescribe.net/schema/catalogueSchema'
GST_NS = 'http://www.battlescribe.net/schema/gameSystemSchema'


def normalize(path: Path, ns: str, root_tag: str, revision: str):
    text = path.read_text(encoding='utf-8')

    # ElementTree workflows had registered both catalogue and game-system namespaces
    # as the default namespace in one process. The second registration wins, so the
    # catalogue was serialized as <ns0:catalogue> and every catalogue element as ns0:.
    # Some New Recruit ingestion paths expect the canonical BattleScribe default-
    # namespace form. Normalize the serialized XML without changing IDs or structure.
    text = text.replace(f'xmlns:ns0="{ns}"', f'xmlns="{ns}"')
    text = text.replace('<ns0:', '<').replace('</ns0:', '</')

    # Defensive normalization for any alternate generated prefix bound to this namespace.
    prefixes = set(re.findall(r'xmlns:([A-Za-z_][\w.-]*)="' + re.escape(ns) + r'"', text))
    for p in prefixes:
        text = text.replace(f'xmlns:{p}="{ns}"', f'xmlns="{ns}"')
        text = text.replace(f'<{p}:', '<').replace(f'</{p}:', '</')

    # Bump revision directly on the root element.
    pat = rf'(<{root_tag}\b[^>]*\brevision=")[^"]+("[^>]*>)'
    text, n = re.subn(pat, rf'\g<1>{revision}\g<2>', text, count=1)
    assert n == 1, f'Could not bump {root_tag} revision'

    assert f'<{root_tag} ' in text or f'<{root_tag}\n' in text
    assert f'xmlns="{ns}"' in text[:1000]
    assert '<ns0:' not in text and '</ns0:' not in text
    path.write_text(text, encoding='utf-8')


normalize(cat_path, CAT_NS, 'catalogue', '51')
normalize(gst_path, GST_NS, 'gameSystem', '21')

# Keep catalogue's gameSystemRevision synchronized with GST revision.
cat = cat_path.read_text(encoding='utf-8')
cat, n = re.subn(r'(<catalogue\b[^>]*\bgameSystemRevision=")[^"]+("[^>]*>)', r'\g<1>21\g<2>', cat, count=1)
assert n == 1
cat_path.write_text(cat, encoding='utf-8')

# Add a standards-compatible repository index as a second ingestion path.
index = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<dataIndex battleScribeVersion="2.03" name="Prohammer 30k" xmlns="http://www.battlescribe.net/schema/dataIndexSchema">
  <dataIndexEntries>
    <dataIndexEntry filePath="Prohammer 30k.gst" dataType="gamesystem" dataId="sys-a1d2-5ede-e74f-7479" dataName="Prohammer 30k" dataBattleScribeVersion="2.03" dataRevision="21"/>
    <dataIndexEntry filePath="Legiones Astartes.cat" dataType="catalogue" dataId="cat-30a0-30b0-30c0-0001" dataName="Legiones Astartes" dataBattleScribeVersion="2.03" dataRevision="51"/>
  </dataIndexEntries>
</dataIndex>
'''
Path('index.xml').write_text(index, encoding='utf-8')

# Visible load marker in GST, if the existing Rev50 marker exists update it; otherwise add
# a comment so inspection can prove the source revision. The actual UI marker lives in CAT.
report = '''REVISION 51 — NEW RECRUIT INGESTION REPAIR
Catalogue namespace: canonical default namespace
Game system namespace: canonical default namespace
CAT revision: 51
GST revision: 21
CAT gameSystemRevision: 21
index.xml: created
Reason: previous generated catalogue was serialized with ns0: prefixes after dual default namespace registration.
'''
Path('inspection-r51-ingestion-repair.txt').write_text(report, encoding='utf-8')
print(report)
