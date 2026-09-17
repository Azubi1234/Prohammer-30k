from pathlib import Path
import re

CAT = Path('Legiones Astartes.cat')
GST = Path('Prohammer 30k.gst')
IDX = Path('index.xml')
OUT = Path('inspection-r84-newrecruit-namespace-fix.txt')

CAT_NS = 'http://www.battlescribe.net/schema/catalogueSchema'
GST_NS = 'http://www.battlescribe.net/schema/gameSystemSchema'


def canonicalize(path: Path, ns: str, root_tag: str):
    text = path.read_text(encoding='utf-8')
    before = text.splitlines()[1] if len(text.splitlines()) > 1 else text[:300]

    # ElementTree scripts in this project register several different namespaces
    # to the empty prefix in one process. Python keeps only the last mapping,
    # which can serialize CAT/GST as <ns0:...>. New Recruit has previously
    # failed to ingest those files and silently kept the old cached catalogue.
    text = text.replace(f'xmlns:ns0="{ns}"', f'xmlns="{ns}"')
    text = text.replace('<ns0:', '<').replace('</ns0:', '</')

    # Defensive support in case a future ElementTree run chooses another
    # generated prefix for the document namespace.
    m = re.search(rf'<(ns\d+):{root_tag}\s+xmlns:\1="{re.escape(ns)}"', text)
    if m:
        pfx = m.group(1)
        text = text.replace(f'xmlns:{pfx}="{ns}"', f'xmlns="{ns}"')
        text = text.replace(f'<{pfx}:', '<').replace(f'</{pfx}:', '</')

    after = text.splitlines()[1] if len(text.splitlines()) > 1 else text[:300]
    if f'<{root_tag} xmlns="{ns}"' not in after:
        raise RuntimeError(f'{path}: canonical default namespace not produced: {after}')
    if re.search(r'<ns\d+:', text):
        raise RuntimeError(f'{path}: generated namespace prefixes remain')

    path.write_text(text, encoding='utf-8')
    return before, after

cat_before, cat_after = canonicalize(CAT, CAT_NS, 'catalogue')
gst_before, gst_after = canonicalize(GST, GST_NS, 'gameSystem')

# Bump revisions WITHOUT reparsing/serializing, otherwise ElementTree can
# reintroduce generated namespace prefixes.
cat = CAT.read_text(encoding='utf-8')
cat = re.sub(r'(<catalogue\b[^>]*\brevision=")83("[^>]*\bgameSystemRevision=")50("[\s>])', r'\g<1>84\g<2>51\g<3>', cat, count=1)
if 'revision="84"' not in cat.splitlines()[1] or 'gameSystemRevision="51"' not in cat.splitlines()[1]:
    raise RuntimeError('Failed to bump catalogue root to 84 / GST ref 51')
CAT.write_text(cat, encoding='utf-8')

gst = GST.read_text(encoding='utf-8')
gst = re.sub(r'(<gameSystem\b[^>]*\brevision=")50("[\s>])', r'\g<1>51\g<2>', gst, count=1)
if 'revision="51"' not in gst.splitlines()[1]:
    raise RuntimeError('Failed to bump GST root to 51')
GST.write_text(gst, encoding='utf-8')

idx = IDX.read_text(encoding='utf-8')
idx = re.sub(r'(filePath="Prohammer 30k\.gst"[^>]*dataRevision=")50(" )', r'\g<1>51\g<2>', idx, count=1)
idx = re.sub(r'(filePath="Legiones Astartes\.cat"[^>]*dataRevision=")83(" )', r'\g<1>84\g<2>', idx, count=1)
if 'dataRevision="51"' not in idx or 'dataRevision="84"' not in idx:
    raise RuntimeError('Failed to bump index revisions')
IDX.write_text(idx, encoding='utf-8')

# Final raw-text validation for New Recruit ingestion.
cat_final = CAT.read_text(encoding='utf-8')
gst_final = GST.read_text(encoding='utf-8')
assert '<catalogue xmlns="http://www.battlescribe.net/schema/catalogueSchema"' in cat_final
assert '<gameSystem xmlns="http://www.battlescribe.net/schema/gameSystemSchema"' in gst_final
assert '<ns0:' not in cat_final and '<ns0:' not in gst_final

OUT.write_text(
    'Revision 84 — New Recruit namespace ingestion fix\n'
    'CAT=84 GST=51\n\n'
    'Root before normalization:\n'
    f'CAT: {cat_before}\nGST: {gst_before}\n\n'
    'Root after normalization and revision bump:\n'
    f'CAT: {CAT.read_text(encoding="utf-8").splitlines()[1]}\n'
    f'GST: {GST.read_text(encoding="utf-8").splitlines()[1]}\n\n'
    'Reason: CAT/GST had again been serialized with ns0: namespace prefixes. '\
    'This previously caused New Recruit ingestion to fail silently and retain the older cached catalogue. '\
    'The live data is now canonical default-namespace BattleScribe XML.\n',
    encoding='utf-8'
)
print(OUT.read_text(encoding='utf-8'))
