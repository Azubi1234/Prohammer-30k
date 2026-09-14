import xml.etree.ElementTree as ET
import unicodedata
import re
from pathlib import Path
from collections import Counter

# Reuse the already-tested source parser from the staged Rev25 builder, but stop
# before its unfinished XML materialisation section.
partial = Path('.github/build/rev25_partial.py').read_text(encoding='utf-8')
marker = "CAT=Path('Legiones Astartes.cat')"
if marker not in partial:
    raise RuntimeError('Could not find parser/materialiser boundary in rev25_partial.py')
parser_source = partial.split(marker, 1)[0]
parser_scope = {'__name__': '__rev25_parser__'}
exec(compile(parser_source, '.github/build/rev25_parser_prefix.py', 'exec'), parser_scope)
LEGIONS = parser_scope['LEGIONS']
LOW = parser_scope['LOW']
AERO = parser_scope['AERO']
LOW_WEAPONS = parser_scope['LOW_WEAPONS']
AERO_WEAPONS = parser_scope['AERO_WEAPONS']

CAT_PATH = Path('Legiones Astartes.cat')
GST_PATH = Path('Prohammer 30k.gst')
CNS = 'http://www.battlescribe.net/schema/catalogueSchema'
GNS = 'http://www.battlescribe.net/schema/gameSystemSchema'
ET.register_namespace('', CNS)
ET.register_namespace('', GNS)
C = lambda t: f'{{{CNS}}}{t}'
G = lambda t: f'{{{GNS}}}{t}'

def slug(value):
    s = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii').lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:72] or 'x'

def child(parent, tag, ns=CNS):
    q = f'{{{ns}}}{tag}'
    found = parent.find(q)
    if found is None:
        found = ET.SubElement(parent, q)
    return found

def byid(root, ident):
    return next((e for e in root.iter() if e.get('id') == ident), None)

def remove_generated(root):
    for parent in list(root.iter()):
        for node in list(parent):
            if node.get('id', '').startswith('r25-'):
                parent.remove(node)

def add_cost(parent, value):
    costs = child(parent, 'costs')
    ET.SubElement(costs, C('cost'), {'name':'Points','typeId':'pts','value':str(value)})

def add_constraint(parent, ident, typ, value, scope='parent', field='selections', include_children='true'):
    constraints = child(parent, 'constraints')
    return ET.SubElement(constraints, C('constraint'), {
        'id':ident, 'field':field, 'scope':scope, 'value':str(value),
        'percentValue':'false', 'shared':'true',
        'includeChildSelections':include_children, 'includeChildForces':'false', 'type':typ
    })

def add_rule(parent, ident, name, text):
    rules = child(parent, 'rules')
    r = ET.SubElement(rules, C('rule'), {'name':name, 'id':ident, 'hidden':'false'})
    ET.SubElement(r, C('description')).text = text or ''
    return r

def add_category(parent, ident, target, name):
    links = child(parent, 'categoryLinks')
    return ET.SubElement(links, C('categoryLink'), {
        'id':ident, 'name':name, 'hidden':'false', 'targetId':target
    })

def add_selection(parent, ident, name, stype='upgrade', points=None, maxv=None, minv=None):
    entries = child(parent, 'selectionEntries')
    e = ET.SubElement(entries, C('selectionEntry'), {
        'type':stype, 'import':'true', 'name':name, 'hidden':'false', 'id':ident
    })
    if minv is not None:
        add_constraint(e, ident+'-min', 'min', minv)
    if maxv is not None:
        add_constraint(e, ident+'-max', 'max', maxv)
    if points is not None:
        add_cost(e, points)
    return e

def add_group(parent, ident, name, maxv=None, minv=None):
    groups = child(parent, 'selectionEntryGroups')
    g = ET.SubElement(groups, C('selectionEntryGroup'), {
        'name':name, 'hidden':'false', 'id':ident, 'collective':'false', 'import':'true'
    })
    if minv is not None:
        add_constraint(g, ident+'-min', 'min', minv)
    if maxv is not None:
        add_constraint(g, ident+'-max', 'max', maxv)
    return g

def add_condition_modifier(parent, field, value, condition_type, child_id, scope='roster'):
    mods = child(parent, 'modifiers')
    m = ET.SubElement(mods, C('modifier'), {'type':'set','value':str(value),'field':field})
    conds = ET.SubElement(m, C('conditions'))
    ET.SubElement(conds, C('condition'), {
        'type':condition_type, 'value':'1', 'field':'selections', 'scope':scope,
        'childId':child_id, 'shared':'true', 'includeChildSelections':'true',
        'includeChildForces':'false'
    })
    return m

def hide_unless(parent, selector_id):
    add_condition_modifier(parent, 'hidden', 'true', 'lessThan', selector_id)

def hide_if(parent, selector_id):
    add_condition_modifier(parent, 'hidden', 'true', 'atLeast', selector_id)

def normalise_stat(s):
    return str(s or '').strip().upper().replace(' ', '')

def add_profile(parent, ident, headers, row):
    if not headers or not row:
        return None
    vals = {normalise_stat(h): str(v).strip() for h, v in zip(headers, row)}
    recognized = {'WS','BS','S','T','W','I','A','LD','SV','FRONT','SIDE','REAR','SP'}
    pname = None
    for h, v in zip(headers, row):
        if normalise_stat(h) not in recognized and str(v).strip():
            pname = str(v).strip()
            break
    if not pname:
        pname = str(row[0]).strip() if row else 'Profile'

    profiles = child(parent, 'profiles')
    if all(x in vals for x in ('FRONT','SIDE','REAR')) and 'WS' in vals:
        p = ET.SubElement(profiles, C('profile'), {
            'name':pname, 'typeId':'prof-walker', 'typeName':'Walker', 'hidden':'false', 'id':ident
        })
        chars = ET.SubElement(p, C('characteristics'))
        mapping = [('WS','walker-ws'),('BS','walker-bs'),('S','walker-s'),('FRONT','walker-front'),('SIDE','walker-side'),('REAR','walker-rear'),('I','walker-i'),('A','walker-a')]
    elif all(x in vals for x in ('FRONT','SIDE','REAR')):
        p = ET.SubElement(profiles, C('profile'), {
            'name':pname, 'typeId':'prof-vehicle', 'typeName':'Vehicle', 'hidden':'false', 'id':ident
        })
        chars = ET.SubElement(p, C('characteristics'))
        mapping = [('BS','vehicle-bs'),('FRONT','vehicle-front'),('SIDE','vehicle-side'),('REAR','vehicle-rear'),('SP','vehicle-sp')]
    else:
        p = ET.SubElement(profiles, C('profile'), {
            'name':pname, 'typeId':'prof-model', 'typeName':'Model', 'hidden':'false', 'id':ident
        })
        chars = ET.SubElement(p, C('characteristics'))
        mapping = [('WS','model-ws'),('BS','model-bs'),('S','model-s'),('T','model-t'),('W','model-w'),('I','model-i'),('A','model-a'),('LD','model-ld'),('SV','model-sv')]
    for stat, type_id in mapping:
        if stat in vals and vals[stat] != '':
            ET.SubElement(chars, C('characteristic'), {'name':'Ld' if stat=='LD' else ('Sv' if stat=='SV' else stat.title() if stat in {'FRONT','SIDE','REAR'} else stat), 'typeId':type_id}).text = vals[stat]
    return p

def add_ranged_profile(parent, ident, weapon):
    profiles = child(parent, 'profiles')
    p = ET.SubElement(profiles, C('profile'), {
        'name':weapon['Weapon'], 'typeId':'prof-ranged', 'typeName':'Ranged Weapon',
        'hidden':'false', 'id':ident
    })
    chars = ET.SubElement(p, C('characteristics'))
    for name, tid, key in [('Range','ranged-range','Range'),('S','ranged-s','S'),('AP','ranged-ap','AP'),('Type','ranged-type','Type')]:
        ET.SubElement(chars, C('characteristic'), {'name':name,'typeId':tid}).text = str(weapon.get(key,''))
    return p

FOC = {
    'HQ':('cat-hq','HQ'), 'Troops':('cat-troops','Troops'),
    'Elites':('cat-elites','Elites'), 'Fast Attack':('cat-fast','Fast Attack'),
    'Heavy Support':('cat-heavy','Heavy Support'), 'Lords of War':('cat-low','Lords of War'),
    'Retinue':('cat-retinue','Retinue')
}

def is_unique_entry(e):
    if e.get('foc') == 'Lords of War':
        return True
    if e.get('foc') == 'HQ' and e.get('base_count', 1) == 1:
        return True
    title = e.get('title','').upper()
    details = e.get('details','').upper()
    if re.search(r'ONE PER ARMY|0-1|UNIQUE', details):
        return True
    # Named/special lone models that were classified outside HQ.
    squadish = re.search(r'SQUAD|SQUADRON|PACK|COHORT|MANIPLE|BATTERY|CABAL|DETACHMENT|MOB|OPERATIVES|GUARD$', title)
    if e.get('base_count',1) == 1 and not squadish and e.get('foc') in {'Elites','Fast Attack','Heavy Support'}:
        return True
    return False

def clean_option_name(name):
    name = re.sub(r'^[•\-]+\s*', '', str(name or '')).strip(' .:;')
    return name

def useful_option(opt):
    n = clean_option_name(opt.get('name'))
    if not n or len(n) > 90:
        return False
    low = n.lower()
    if ' may ' in low or low.startswith(('the ', 'one model ', 'any model ', 'for every ', 'up to ', 'entire ')):
        return False
    if low in {'options','option'}:
        return False
    return True

def add_parsed_options(unit, uid, entry):
    opts = [o for o in entry.get('options',[]) if useful_option(o)]
    if not opts:
        return 0
    g = add_group(unit, uid+'-options', 'Options')
    count = 0
    for i, opt in enumerate(opts):
        name = clean_option_name(opt.get('name'))
        if not name:
            continue
        maxv = max(1, int(opt.get('max') or 1))
        raw_cost = int(opt.get('cost') or 0)
        if opt.get('squadwide'):
            display_cost = raw_cost * int(entry.get('base_count') or 1)
            label = f"{name} (base unit; {raw_cost:+d} pts/model)"
        else:
            display_cost = raw_cost
            label = name
        oe = add_selection(g, f'{uid}-opt-{i}-{slug(name)}', label, points=display_cost, maxv=maxv)
        context = (opt.get('context') or '').strip()
        if context:
            add_rule(oe, f'{uid}-opt-{i}-context', 'Option restriction', context)
        if opt.get('squadwide'):
            add_rule(oe, f'{uid}-opt-{i}-squadwide', 'Squad-wide cost note', f'The source prices this option at {raw_cost:+d} points per model. The displayed selection charges the parsed base unit only; apply the same per-model surcharge for any additional models selected.')
        count += 1
    return count

def materialise_unit(root, entry, uid, legion_id=None, allegiance=None, category_override=None, weapon_pool=None):
    roots = child(root, 'selectionEntries')
    u = ET.SubElement(roots, C('selectionEntry'), {
        'type':'unit', 'import':'true', 'name':entry['title'], 'hidden':'false', 'id':uid
    })
    add_cost(u, entry.get('cost') or 0)
    foc = category_override or entry.get('foc') or 'Elites'
    catid, catname = FOC.get(foc, ('cat-elites','Elites'))
    add_category(u, uid+'-cat', catid, catname)
    if legion_id:
        hide_unless(u, legion_id)
    if allegiance == 'Loyalist':
        hide_unless(u, 'allegiance-loyalist')
    elif allegiance == 'Traitor':
        hide_unless(u, 'allegiance-traitor')
    if is_unique_entry(entry):
        add_constraint(u, uid+'-unique', 'max', 1, scope='roster')

    headers = entry.get('profile_headers') or []
    for i, row in enumerate(entry.get('profile_rows') or []):
        add_profile(u, f'{uid}-profile-{i}', headers, row)

    details = (entry.get('details') or '').strip()
    if details:
        add_rule(u, uid+'-source', 'Source Entry', details)

    extra = entry.get('extra')
    if extra and extra.get('max'):
        ex = add_selection(u, uid+'-additional', 'Additional model', stype='model', points=int(extra.get('cost') or 0), maxv=int(extra['max']))
        add_rule(ex, uid+'-additional-rule', 'Additional model', f"May include up to {int(extra['max'])} additional models at +{int(extra.get('cost') or 0)} points each, as stated in the source entry.")

    add_parsed_options(u, uid, entry)

    if weapon_pool and details:
        seen = set()
        lower = details.lower()
        for weapon in weapon_pool:
            wname = weapon.get('Weapon','')
            key = (wname.lower(), weapon.get('Range'), weapon.get('S'), weapon.get('AP'), weapon.get('Type'))
            if wname and wname.lower() in lower and key not in seen:
                seen.add(key)
                add_ranged_profile(u, f'{uid}-weapon-{len(seen)}-{slug(wname)}', weapon)
    return u

def add_special_consuls(root, legion_map):
    group = byid(root, 'hq-centurion-consuls')
    if group is None:
        raise RuntimeError('Could not find hq-centurion-consuls')
    added = 0
    # These are replacements for generic consul choices in the relevant Legions.
    replacement_targets = {
        ('V','STORMSEER CONSUL'):'hq-consul-librarian',
        ('VI','WOLF PRIEST CONSUL'):'hq-consul-chaplain',
        ('VI','RUNE PRIEST CONSUL'):'hq-consul-librarian',
        ('IX','SANGUINARY HIGH PRIEST CONSUL'):'hq-consul-medicae',
    }
    for L in LEGIONS:
        if L['roman'] == 'I':
            continue
        legion_id = legion_map[L['roman']]
        for cdata in L.get('consuls',[]):
            title = cdata['title']
            if L['roman'] == 'X' and title.upper() == 'IRON FATHER':
                forge = byid(root, 'hq-consul-forge')
                if forge is None:
                    raise RuntimeError('Could not find Forge Lord Consul for Iron Father upgrade')
                ce = add_selection(forge, 'r25-consul-x-iron-father', 'Iron Father', points=cdata.get('cost') or 0, maxv=1)
                hide_unless(ce, legion_id)
                add_rule(ce, 'r25-consul-x-iron-father-rule', 'Iron Father', cdata.get('text') or '')
                added += 1
                continue
            cid = f"r25-consul-{slug(L['roman'])}-{slug(title)}"
            ce = add_selection(group, cid, title.title(), points=cdata.get('cost') or 0, maxv=1)
            hide_unless(ce, legion_id)
            add_rule(ce, cid+'-rule', title.title(), cdata.get('text') or '')
            generic_id = replacement_targets.get((L['roman'], title.upper()))
            if generic_id:
                generic = byid(root, generic_id)
                if generic is not None:
                    hide_if(generic, legion_id)
            added += 1
    return added

def add_legion_references_and_rites(root, legion_map):
    rites_group = byid(root, 'config-rites')
    if rites_group is None:
        raise RuntimeError('Could not find config-rites')
    rites_added = 0
    refs_added = 0
    for L in LEGIONS:
        if L['roman'] == 'I':
            continue
        legion_id = legion_map[L['roman']]
        selector = byid(root, legion_id)
        if selector is None:
            raise RuntimeError(f'Missing Legion selector {legion_id}')
        ref = (L.get('reference') or '').strip()
        if ref:
            add_rule(selector, f"r25-legion-{slug(L['roman'])}-reference", f"{L['name'].title()} — Legion Rules & Armoury", ref)
            refs_added += 1
        for idx, rite in enumerate(L.get('rites',[])):
            rid = f"r25-rite-{slug(L['roman'])}-{idx}-{slug(rite['title'])}"
            relem = add_selection(rites_group, rid, f"{L['name'].title()} Rite of War — {rite['title'].title()}", maxv=1)
            hide_unless(relem, legion_id)
            if rite.get('allegiance') == 'Loyalist':
                hide_unless(relem, 'allegiance-loyalist')
            elif rite.get('allegiance') == 'Traitor':
                hide_unless(relem, 'allegiance-traitor')
            add_rule(relem, rid+'-rule', rite['title'].title(), rite.get('text') or '')
            rites_added += 1
    return refs_added, rites_added

def update_gst(groot):
    # Category: Retinue (slotless; separate display category).
    cats = child(groot, 'categoryEntries', GNS)
    if byid(groot, 'cat-retinue') is None:
        ET.SubElement(cats, G('categoryEntry'), {'id':'cat-retinue','name':'Retinue','hidden':'false'})

    # Vehicle Structure Points.
    vehicle_type = byid(groot, 'prof-vehicle')
    if vehicle_type is None:
        raise RuntimeError('Vehicle profile type not found')
    cts = child(vehicle_type, 'characteristicTypes', GNS)
    if byid(groot, 'vehicle-sp') is None:
        ET.SubElement(cts, G('characteristicType'), {'id':'vehicle-sp','name':'SP'})

    force = byid(groot, 'force-standard')
    if force is None:
        raise RuntimeError('Standard force not found')
    flinks = child(force, 'categoryLinks', GNS)
    if byid(groot, 'fl-retinue') is None:
        ET.SubElement(flinks, G('categoryLink'), {'id':'fl-retinue','name':'Retinue','hidden':'false','targetId':'cat-retinue'})
    low = byid(groot, 'fl-low')
    if low is None:
        raise RuntimeError('Lords of War force category not found')
    if byid(groot, 'r25-fl-low-max') is None:
        constraints = child(low, 'constraints', GNS)
        ET.SubElement(constraints, G('constraint'), {
            'id':'r25-fl-low-max','field':'selections','scope':'parent','value':'1',
            'percentValue':'false','shared':'true','includeChildSelections':'false',
            'includeChildForces':'false','type':'max'
        })
    groot.set('revision', str(max(10, int(groot.get('revision','0')) + 1)))


def main():
    ctree = ET.parse(CAT_PATH)
    root = ctree.getroot()
    gtree = ET.parse(GST_PATH)
    groot = gtree.getroot()

    if int(root.get('revision','0')) >= 25:
        print('Revision 25 is already applied; exiting without changes.')
        return

    remove_generated(root)
    remove_generated(groot)
    update_gst(groot)

    legion_map = {L['roman']:f"legion-{L['roman'].lower()}" for L in LEGIONS}
    refs_added, rites_added = add_legion_references_and_rites(root, legion_map)
    consuls_added = add_special_consuls(root, legion_map)

    legion_units = 0
    for L in LEGIONS:
        if L['roman'] == 'I':
            continue  # Dark Angels were already fully materialised in Revision 22.
        lid = legion_map[L['roman']]
        for idx, entry in enumerate(L.get('entries',[])):
            uid = f"r25-unit-{slug(L['roman'])}-{idx}-{slug(entry['title'])}"
            materialise_unit(root, entry, uid, legion_id=lid, allegiance=entry.get('allegiance'))
            legion_units += 1

    low_units = 0
    for idx, entry in enumerate(LOW):
        uid = f"r25-low-{idx}-{slug(entry['title'])}"
        materialise_unit(root, entry, uid, category_override='Lords of War', weapon_pool=LOW_WEAPONS)
        low_units += 1

    aero_units = 0
    for idx, entry in enumerate(AERO):
        uid = f"r25-aero-{idx}-{slug(entry['title'])}"
        # Aeronautica has its own one-choice slot, regardless of the source's internal battlefield role.
        roots = child(root, 'selectionEntries')
        u = ET.SubElement(roots, C('selectionEntry'), {
            'type':'unit','import':'true','name':entry['title'],'hidden':'false','id':uid
        })
        add_cost(u, entry.get('cost') or 0)
        add_category(u, uid+'-cat', 'cat-aero', 'Aeronautica Imperialis')
        headers = entry.get('profile_headers') or []
        for pidx, row in enumerate(entry.get('profile_rows') or []):
            add_profile(u, f'{uid}-profile-{pidx}', headers, row)
        details = (entry.get('details') or '').strip()
        if details:
            add_rule(u, uid+'-source', 'Source Entry', details)
        add_parsed_options(u, uid, entry)
        if details:
            seen = set(); lower = details.lower()
            for weapon in AERO_WEAPONS:
                wname = weapon.get('Weapon','')
                key = (wname.lower(), weapon.get('Range'), weapon.get('S'), weapon.get('AP'), weapon.get('Type'))
                if wname and wname.lower() in lower and key not in seen:
                    seen.add(key)
                    add_ranged_profile(u, f'{uid}-weapon-{len(seen)}-{slug(wname)}', weapon)
        aero_units += 1

    root.set('revision', '25')
    root.set('gameSystemRevision', groot.get('revision','10'))
    comment = root.find(C('comment'))
    if comment is None:
        comment = ET.Element(C('comment'))
        root.insert(0, comment)
    comment.text = ('Revision 25: Added the remaining Legion packages from Forces of the Legions, Legiones Astartes Lords of War and Aeronautica Imperialis; added Legion/allegiance gating, specialist Consuls, Retinues, Structure Points and a default one-Lord-of-War limit. Experimental Wargear and Units remains excluded.')
    readme = root.find(C('readme'))
    if readme is not None:
        readme.text = ('Core Legiones Astartes catalogue for Prohammer 30k. Revision 25 expands all eighteen Legions using the final project source documents, including Legion rules/reference material, Rites of War, unique units, named characters and Primarchs, together with universal Legiones Astartes Lords of War and Aeronautica Imperialis. Experimental Wargear and Units is not included.')

    ctree.write(CAT_PATH, encoding='UTF-8', xml_declaration=True)
    gtree.write(GST_PATH, encoding='UTF-8', xml_declaration=True)

    print(f'REV25 MATERIALISED: legion references={refs_added}, rites={rites_added}, specialist consuls={consuls_added}, legion units={legion_units}, Lords of War={low_units}, Aeronautica={aero_units}, GST revision={groot.get("revision")}')

if __name__ == '__main__':
    main()
