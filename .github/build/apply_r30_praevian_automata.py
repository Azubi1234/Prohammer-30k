from pathlib import Path
import xml.etree.ElementTree as ET
from collections import Counter

CAT = Path('Legiones Astartes.cat')
NS = 'http://www.battlescribe.net/schema/catalogueSchema'
ET.register_namespace('', NS)
Q = lambda t: f'{{{NS}}}{t}'

tree = ET.parse(CAT)
root = tree.getroot()
assert root.tag == Q('catalogue')
assert root.get('revision') in {'29', '30'}, root.get('revision')
assert root.get('gameSystemRevision') == '12', root.get('gameSystemRevision')


def by_id(id_):
    for e in root.iter():
        if e.get('id') == id_:
            return e
    return None


def parent_map():
    return {c: p for p in root.iter() for c in p}


def remove_by_id(id_):
    e = by_id(id_)
    if e is None:
        return False
    p = parent_map().get(e)
    if p is not None:
        p.remove(e)
        return True
    return False


def direct(parent, tag):
    return parent.find(Q(tag))


ORDER = {
    'constraints': 10,
    'costs': 20,
    'profiles': 30,
    'rules': 40,
    'selectionEntries': 50,
    'selectionEntryGroups': 60,
    'entryLinks': 70,
    'categoryLinks': 80,
    'modifiers': 90,
}


def ensure_container(parent, tag):
    x = direct(parent, tag)
    if x is not None:
        return x
    x = ET.Element(Q(tag))
    rank = ORDER.get(tag, 999)
    inserted = False
    for i, ch in enumerate(list(parent)):
        local = ch.tag.split('}')[-1]
        if ORDER.get(local, 999) > rank:
            parent.insert(i, x)
            inserted = True
            break
    if not inserted:
        parent.append(x)
    return x


def add_constraint(parent, id_, typ, value, include_children=False):
    cs = ensure_container(parent, 'constraints')
    return ET.SubElement(cs, Q('constraint'), {
        'id': id_, 'field': 'selections', 'scope': 'parent', 'value': str(value),
        'percentValue': 'false', 'shared': 'true',
        'includeChildSelections': 'true' if include_children else 'false',
        'includeChildForces': 'false', 'type': typ
    })


def add_cost(parent, value):
    costs = ensure_container(parent, 'costs')
    return ET.SubElement(costs, Q('cost'), {
        'name': 'Points', 'typeId': 'pts', 'value': str(value)
    })


def add_rule(parent, id_, name, text):
    rules = ensure_container(parent, 'rules')
    r = ET.SubElement(rules, Q('rule'), {
        'name': name, 'id': id_, 'hidden': 'false'
    })
    ET.SubElement(r, Q('description')).text = text
    return r


def add_model_profile(parent, id_, name, ws, bs, s, t, w, i, a, ld, sv):
    profiles = ensure_container(parent, 'profiles')
    p = ET.SubElement(profiles, Q('profile'), {
        'name': name, 'id': id_, 'typeId': 'prof-model',
        'typeName': 'Model', 'hidden': 'false'
    })
    cs = ET.SubElement(p, Q('characteristics'))
    for n, tid, val in [
        ('WS', 'model-ws', ws), ('BS', 'model-bs', bs), ('S', 'model-s', s),
        ('T', 'model-t', t), ('W', 'model-w', w), ('I', 'model-i', i),
        ('A', 'model-a', a), ('Ld', 'model-ld', ld), ('Sv', 'model-sv', sv)
    ]:
        ET.SubElement(cs, Q('characteristic'), {'name': n, 'typeId': tid}).text = str(val)
    return p


def add_ranged(parent, id_, name, rng, strength, ap, typ):
    profiles = ensure_container(parent, 'profiles')
    p = ET.SubElement(profiles, Q('profile'), {
        'name': name, 'id': id_, 'typeId': 'prof-ranged',
        'typeName': 'Ranged Weapon', 'hidden': 'false'
    })
    cs = ET.SubElement(p, Q('characteristics'))
    for n, tid, val in [
        ('Range', 'ranged-range', rng), ('S', 'ranged-s', strength),
        ('AP', 'ranged-ap', ap), ('Type', 'ranged-type', typ)
    ]:
        ET.SubElement(cs, Q('characteristic'), {'name': n, 'typeId': tid}).text = str(val)
    return p


def add_selection(parent_container, id_, name, stype='upgrade', cost=None, maxv=1):
    e = ET.SubElement(parent_container, Q('selectionEntry'), {
        'type': stype, 'import': 'true', 'name': name,
        'hidden': 'false', 'id': id_
    })
    if maxv is not None:
        add_constraint(e, id_ + '-max', 'max', maxv)
    if cost is not None:
        add_cost(e, cost)
    return e


def add_group(parent, id_, name, minv=None, maxv=None):
    groups = ensure_container(parent, 'selectionEntryGroups')
    g = ET.SubElement(groups, Q('selectionEntryGroup'), {
        'name': name, 'id': id_, 'hidden': 'false',
        'collective': 'false', 'import': 'true'
    })
    if minv is not None:
        add_constraint(g, id_ + '-min', 'min', minv)
    if maxv is not None:
        add_constraint(g, id_ + '-max', 'max', maxv)
    return g


def add_upgrade_to_group(group, id_, name, cost=0, maxv=1, rule_text=None, ranged=None):
    entries = ensure_container(group, 'selectionEntries')
    e = add_selection(entries, id_, name, 'upgrade', cost, maxv)
    if rule_text:
        add_rule(e, id_ + '-rule', name, rule_text)
    if ranged:
        add_ranged(e, id_ + '-profile', name, *ranged)
    return e


praev = by_id('hq-consul-praevian')
assert praev is not None

# Remove the temporary Revision 29 substitute which used the wrong Castellan profile.
remove_by_id('r29-prae-automata-group')
remove_by_id('r30-prae-automata-group')

# Master of Cybernetica requires exactly one of these two Mechanicum Maniples.
group = add_group(praev, 'r30-prae-automata-group', 'Praevian Battle-Automata Maniple', 1, 1)
entries = ensure_container(group, 'selectionEntries')

# ---------------------------------------------------------------------------
# Castellax Class Battle-Automata Maniple — Mechanicum source profile.
# ---------------------------------------------------------------------------
cast = add_selection(entries, 'r30-prae-castellax', 'Castellax Class Battle-Automata Maniple', 'unit', 105, 1)
add_model_profile(cast, 'r30-prae-castellax-profile', 'Castellax', '3', '4', '6', '7', '4', '3', '2', '7', '3+/5+')
add_ranged(cast, 'r30-prae-castellax-mauler', 'Mauler Bolt Cannon', '24”', '6', '4', 'Heavy 3')
add_ranged(cast, 'r30-prae-castellax-bolter', 'Bolter', '24”', '4', '5', 'Rapid Fire')
add_rule(cast, 'r30-prae-castellax-type', 'Unit Type', 'Monstrous Creature.')
add_rule(cast, 'r30-prae-castellax-wargear', 'Standard Wargear', 'Mauler Bolt Cannon; two Bolters; Shock Chargers; Atomantic Shielding.')
add_rule(cast, 'r30-prae-castellax-shock', 'Shock Chargers', 'Melee weapon: Strength User +1, AP -, Melee, Concussive.')
add_rule(cast, 'r30-prae-castellax-atomantic', 'Atomantic Shielding', 'A Castellax has a 5+ Invulnerable Save against shooting attacks and a 6+ Invulnerable Save in close combat.')
add_rule(cast, 'r30-prae-castellax-cortex', 'Cybernetica Cortex', 'Fearless; Poisoned and Fleshbane attacks only wound on a 6+; subject to Programmed Behaviour unless controlled by a Cortex Controller.')
add_rule(cast, 'r30-prae-castellax-reactor', 'Reactor Blast', 'When the model loses its final Wound, roll a D6. On a 6, centre a Large Blast over it; every model touched suffers a hit at Strength equal to the destroyed model’s unmodified Toughness, to a maximum of 8, AP4. Then remove the destroyed model.')
add_rule(cast, 'r30-prae-castellax-rage', 'Rage', 'Uses the normal ProHammer Rage special rule.')
add_rule(cast, 'r30-prae-castellax-support', 'Support Unit', 'Normally a Troops choice that cannot fulfil compulsory Troops; when purchased for a Praevian it instead forms part of the Praevian’s single HQ selection.')
add_rule(cast, 'r30-prae-castellax-no-paragon', 'Praevian Restriction', 'This accompanying Maniple may not purchase Paragon of Metal.')

cse = ensure_container(cast, 'selectionEntries')
extra = add_selection(cse, 'r30-prae-castellax-extra', 'Additional Castellax Battle-Automata', 'upgrade', 105, 4)
add_rule(extra, 'r30-prae-castellax-extra-rule', 'Additional Castellax', 'The Maniple may include up to four additional Castellax, for a maximum of five models.')

cup = add_group(cast, 'r30-prae-castellax-maniple-upgrades', 'Maniple-wide Upgrades (select once per model)', None, None)
add_upgrade_to_group(cup, 'r30-prae-castellax-searchlight', 'Searchlights', 1, 5, 'The entire Maniple may take Searchlights for +1 point per model; select this once for each Castellax in the Maniple.')
add_upgrade_to_group(cup, 'r30-prae-castellax-frag', 'Frag Grenades', 5, 5, 'The entire Maniple may take Frag Grenades for +5 points per model; select this once for each Castellax in the Maniple.')
add_upgrade_to_group(cup, 'r30-prae-castellax-infravisor', 'Infravisors', 5, 5, 'The entire Maniple may take Infravisors for +5 points per model; select this once for each Castellax in the Maniple.')
add_upgrade_to_group(cup, 'r30-prae-castellax-eta', 'Enhanced Targeting Arrays', 15, 5, 'The entire Maniple may take Enhanced Targeting Arrays for +15 points per model; select this once for each Castellax in the Maniple.')

cm = add_group(cast, 'r30-prae-castellax-mauler-replacements', 'Mauler Bolt Cannon Replacements', None, 5)
add_upgrade_to_group(cm, 'r30-prae-castellax-multimelta', 'Multi-Melta', 0, 5, 'Replaces one Castellax model’s Mauler Bolt Cannon.', ('24”', '8', '1', 'Heavy 1, Melta'))
add_upgrade_to_group(cm, 'r30-prae-castellax-darkfire', 'Darkfire Cannon', 20, 5, 'Replaces one Castellax model’s Mauler Bolt Cannon.', ('60”', '7', '2', 'Heavy 2, Lance, Blind, Gets Hot'))

cb = add_group(cast, 'r30-prae-castellax-bolter-replacements', 'Bolter Replacements', None, 10)
add_upgrade_to_group(cb, 'r30-prae-castellax-flamer', 'Flamer', 5, 10, 'Replaces one Bolter. Each Castellax may replace either or both Bolters.', ('Template', '4', '5', 'Assault 1'))

cc = add_group(cast, 'r30-prae-castellax-melee-replacements', 'Shock Charger Replacements', None, 5)
add_upgrade_to_group(cc, 'r30-prae-castellax-blades', 'Two Battle-Automata Power Blades', 10, 5, 'Replaces one Castellax model’s Shock Chargers. Melee, Strength User, AP -, Specialist Weapon.')
add_upgrade_to_group(cc, 'r30-prae-castellax-wrecker', 'Siege Wrecker', 20, 5, 'Replaces one Castellax model’s Shock Chargers. Melee, Strength 10, AP -, Unwieldy, Armourbane.')

# ---------------------------------------------------------------------------
# Vorax Class Battle-Automata Maniple — Mechanicum source profile.
# ---------------------------------------------------------------------------
vorax = add_selection(entries, 'r30-prae-vorax', 'Vorax Class Battle-Automata Maniple', 'unit', 65, 1)
add_model_profile(vorax, 'r30-prae-vorax-profile', 'Vorax', '4', '4', '6', '6', '3', '4', '2(3)', '7', '4+')
add_ranged(vorax, 'r30-prae-vorax-lightning', 'Lightning Gun', '18”', '6', '4', 'Assault 2')
add_ranged(vorax, 'r30-prae-vorax-rotor', 'Rotor Cannon', '30”', '3', '6', 'Salvo 3/4')
add_rule(vorax, 'r30-prae-vorax-type', 'Unit Type', 'Monstrous Creature.')
add_rule(vorax, 'r30-prae-vorax-wargear', 'Standard Wargear', 'Lightning Gun; two Rotor Cannons; Battle-Automata Power Blades; Infravisor.')
add_rule(vorax, 'r30-prae-vorax-blades', 'Battle-Automata Power Blades', 'Melee weapon: Strength User, AP -, Melee, Rending, Paired. The extra Attack from Paired is already shown in the profile as 2(3).')
add_rule(vorax, 'r30-prae-vorax-cortex', 'Cybernetica Cortex', 'Fearless; Poisoned and Fleshbane attacks only wound on a 6+; subject to Programmed Behaviour unless controlled by a Cortex Controller.')
add_rule(vorax, 'r30-prae-vorax-fleet', 'Fleet', 'Uses the normal ProHammer Fleet special rule.')
add_rule(vorax, 'r30-prae-vorax-scout', 'Scout', 'Uses the normal ProHammer Scout special rule.')
add_rule(vorax, 'r30-prae-vorax-no-paragon', 'Praevian Restriction', 'The accompanying Maniple is purchased as part of the Praevian’s single HQ selection. Paragon of Metal is not available to the Praevian’s accompanying Maniple.')

vse = ensure_container(vorax, 'selectionEntries')
vextra = add_selection(vse, 'r30-prae-vorax-extra', 'Additional Vorax Battle-Automata', 'upgrade', 65, 5)
add_rule(vextra, 'r30-prae-vorax-extra-rule', 'Additional Vorax', 'The Maniple may include up to five additional Vorax, for a maximum of six models.')

vup = add_group(vorax, 'r30-prae-vorax-maniple-upgrades', 'Maniple-wide Upgrades (select once per model)', None, None)
add_upgrade_to_group(vup, 'r30-prae-vorax-searchlight', 'Searchlights', 1, 6, 'The entire Maniple may take Searchlights for +1 point per model; select this once for each Vorax in the Maniple.')
add_upgrade_to_group(vup, 'r30-prae-vorax-frag', 'Frag Grenades', 5, 6, 'The entire Maniple may take Frag Grenades for +5 points per model; select this once for each Vorax in the Maniple.')
add_upgrade_to_group(vup, 'r30-prae-vorax-eta', 'Enhanced Targeting Arrays', 15, 6, 'The entire Maniple may take Enhanced Targeting Arrays for +15 points per model; select this once for each Vorax in the Maniple.')

vi = add_group(vorax, 'r30-prae-vorax-lightning-replacements', 'Lightning Gun Replacements', None, 6)
add_upgrade_to_group(vi, 'r30-prae-vorax-irad', 'Irad Cleanser', 10, 6, 'Replaces one Vorax model’s Lightning Gun.', ('Template', '2', '5', 'Assault 1, Fleshbane, Rad-phage'))

bio = add_selection(vse, 'r30-prae-vorax-biocorrosive', 'Bio-corrosive Ammunition (select once per model)', 'upgrade', 10, 6)
add_rule(bio, 'r30-prae-vorax-biocorrosive-rule', 'Bio-corrosive Ammunition', 'The entire Maniple may equip its Rotor Cannons with Bio-corrosive Ammunition for +10 points per model; select this once for each Vorax in the Maniple.')
add_ranged(bio, 'r30-prae-vorax-biocorrosive-profile', 'Bio-corrosive Rotor Cannon', '15”', '3', '6', 'Salvo 3/4, Poisoned (4+)')

# The parent Praevian rule already states the attachment/FOC behaviour; make the source identity explicit.
master = by_id('r29-prae-cybernetica')
if master is not None:
    desc = master.find(Q('description'))
    if desc is not None:
        desc.text = ('The Praevian must be accompanied by either a Castellax Class Battle-Automata Maniple or a Vorax Class Battle-Automata Maniple purchased here from the Mechanicum source profiles. The Maniple occupies no additional Force Organisation slot; the Praevian and Maniple count as one HQ choice. The Praevian must begin attached and may not voluntarily leave while any Battle-Automata remain alive. The Praevian may join them despite their Monstrous Creature unit type, and his Cortex Controller controls the Maniple normally. The accompanying Maniple may not purchase Paragon of Metal.')

root.set('revision', '30')
root.set('gameSystemRevision', '12')
comment = root.find(Q('comment'))
if comment is not None:
    comment.text = ('Revision 30: final Praevian correction — replaces the temporary Castellan substitute with the source-accurate Castellax and Vorax Class Battle-Automata Maniples, including their profiles, core wargear and options. All Revision 29 Consul and psychic cleanup remains in place.')

# Validation.
ids = [e.get('id') for e in root.iter() if e.get('id')]
dups = [k for k, v in Counter(ids).items() if v > 1]
assert not dups, f'Duplicate IDs: {dups[:20]}'
assert by_id('r29-prae-automata-group') is None
for req in ['r30-prae-automata-group', 'r30-prae-castellax', 'r30-prae-vorax', 'r30-prae-castellax-profile', 'r30-prae-vorax-profile']:
    assert by_id(req) is not None, req
assert by_id('r30-prae-castellax').get('name') == 'Castellax Class Battle-Automata Maniple'
assert by_id('r30-prae-vorax').get('name') == 'Vorax Class Battle-Automata Maniple'
assert all('Paragon of Metal' not in (e.get('name') or '') for e in by_id('r30-prae-automata-group').iter(Q('selectionEntry')))
assert root.get('revision') == '30'
assert root.get('gameSystemRevision') == '12'

body = ET.tostring(root, encoding='unicode', short_empty_elements=True)
assert body.startswith('<catalogue ')
assert f'xmlns="{NS}"' in body[:500]
output = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + body + '\n'
assert '<ns0:' not in output[:2000] and 'xmlns:ns0=' not in output[:2000]
CAT.write_text(output, encoding='utf-8', newline='\n')
ET.parse(CAT)
print('REV30 OK: Praevian now uses source-accurate Castellax and Vorax Maniples; temporary Castellan substitute removed.')
