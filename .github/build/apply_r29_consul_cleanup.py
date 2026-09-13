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
assert root.get('gameSystemRevision') == '12', root.get('gameSystemRevision')
root.set('revision', '29')
root.set('gameSystemRevision', '12')

comment = root.find(Q('comment'))
if comment is not None:
    comment.text = ('Revision 29: Consul cleanup — explicit granted wargear and split special rules; ProHammer psychic '
                    'discipline/power selectors; restricted Force Weapon access; Moritat pistol pairs; Vigilator Special '
                    'Issue Ammunition; source-backed Praevian automata; Demolisher and Flamestorm Cannon profiles.')


def by_id(id_):
    for e in root.iter():
        if e.get('id') == id_:
            return e
    return None


def pmap():
    return {c: p for p in root.iter() for c in p}


def remove_by_id(id_):
    e = by_id(id_)
    if e is None:
        return False
    p = pmap().get(e)
    if p is not None:
        p.remove(e)
        return True
    return False


def direct(parent, tag):
    return parent.find(Q(tag))


# Child ordering follows the structure already used by this catalogue.
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


def clear_prefix(prefix='r29-'):
    for p in list(root.iter()):
        for ch in list(p):
            if (ch.get('id') or '').startswith(prefix):
                p.remove(ch)


clear_prefix()
shared = direct(root, 'sharedSelectionEntries')
assert shared is not None


def add_cost(parent, value):
    costs = ensure_container(parent, 'costs')
    ET.SubElement(costs, Q('cost'), {'name': 'Points', 'typeId': 'pts', 'value': str(value)})


def add_constraint(parent, id_, typ, value, field='selections', scope='parent', include_children=True, automatic=False):
    cs = ensure_container(parent, 'constraints')
    attrs = {
        'id': id_, 'type': typ, 'value': str(value), 'field': field, 'scope': scope,
        'shared': 'true', 'includeChildSelections': 'true' if include_children else 'false'
    }
    if automatic:
        attrs['automatic'] = 'true'
    return ET.SubElement(cs, Q('constraint'), attrs)


def add_rule(parent, id_, name, desc):
    old = by_id(id_)
    if old is not None:
        op = pmap().get(old)
        if op is not None:
            op.remove(old)
    rules = ensure_container(parent, 'rules')
    r = ET.SubElement(rules, Q('rule'), {'name': name, 'id': id_, 'hidden': 'false'})
    ET.SubElement(r, Q('description')).text = desc
    return r


def add_ranged(parent, id_, name, rng, strength, ap, typ):
    profiles = ensure_container(parent, 'profiles')
    p = ET.SubElement(profiles, Q('profile'), {
        'name': name, 'id': id_, 'typeId': 'prof-ranged', 'typeName': 'Ranged Weapon', 'hidden': 'false'
    })
    cs = ET.SubElement(p, Q('characteristics'))
    for n, tid, val in [
        ('Range', 'ranged-range', rng), ('S', 'ranged-s', strength),
        ('AP', 'ranged-ap', ap), ('Type', 'ranged-type', typ)
    ]:
        ET.SubElement(cs, Q('characteristic'), {'name': n, 'typeId': tid}).text = val
    return p


def shared_upgrade(id_, name, rule_desc=None, profiles=None):
    e = ET.SubElement(shared, Q('selectionEntry'), {
        'type': 'upgrade', 'import': 'true', 'name': name, 'hidden': 'false', 'id': id_
    })
    for args in profiles or []:
        add_ranged(e, *args)
    if rule_desc:
        add_rule(e, id_ + '-rule', name, rule_desc)
    return e


def auto_link(parent, id_, name, target_id, cost=None):
    assert by_id(target_id) is not None, f'auto_link target missing: {target_id}'
    links = ensure_container(parent, 'entryLinks')
    e = ET.SubElement(links, Q('entryLink'), {
        'import': 'true', 'name': name, 'id': id_, 'type': 'selectionEntry',
        'targetId': target_id, 'hidden': 'false', 'defaultAmount': '1'
    })
    add_constraint(e, id_ + '-min', 'min', 1, include_children=False, automatic=True)
    add_constraint(e, id_ + '-max', 'max', 1, include_children=False)
    if cost is not None:
        add_cost(e, cost)
    return e


def condition(parent, typ, value, child_id, scope='root-entry'):
    return ET.SubElement(parent, Q('condition'), {
        'type': typ, 'value': str(value), 'field': 'selections', 'scope': scope,
        'childId': child_id, 'shared': 'true', 'includeChildSelections': 'true'
    })


def hidden_unless(entry, selector_id, scope='root-entry'):
    mods = ensure_container(entry, 'modifiers')
    m = ET.SubElement(mods, Q('modifier'), {'type': 'set', 'value': 'true', 'field': 'hidden'})
    cs = ET.SubElement(m, Q('conditions'))
    condition(cs, 'lessThan', 1, selector_id, scope)


def hidden_if(entry, selected_id, scope='root-entry'):
    mods = ensure_container(entry, 'modifiers')
    m = ET.SubElement(mods, Q('modifier'), {'type': 'set', 'value': 'true', 'field': 'hidden'})
    cs = ET.SubElement(m, Q('conditions'))
    condition(cs, 'atLeast', 1, selected_id, scope)


def set_constraint_when(group, constraint_id, value, child_id):
    mods = ensure_container(group, 'modifiers')
    m = ET.SubElement(mods, Q('modifier'), {'type': 'set', 'value': str(value), 'field': constraint_id})
    cs = ET.SubElement(m, Q('conditions'))
    condition(cs, 'atLeast', 1, child_id)


def local_upgrade(container, id_, name, cost=0, default=False, maxv=1, minv=None):
    attrs = {'type': 'upgrade', 'name': name, 'id': id_, 'hidden': 'false', 'import': 'true'}
    if default:
        attrs['defaultAmount'] = '1'
    e = ET.SubElement(container, Q('selectionEntry'), attrs)
    if minv is not None:
        add_constraint(e, id_ + '-min', 'min', minv, include_children=False, automatic=default)
    add_constraint(e, id_ + '-max', 'max', maxv, include_children=False)
    if cost:
        add_cost(e, cost)
    return e


# ---------------------------------------------------------------------------
# Visible shared Consul wargear.
# ---------------------------------------------------------------------------
shared_upgrade('r29-gear-crozius', 'Crozius Arcanum', 'Counts as a Power Weapon and ignores Armour Saves.')
shared_upgrade('r29-gear-rosarius', 'Rosarius', 'Grants a 4+ Invulnerable Save.')
shared_upgrade('r29-gear-servo-arm', 'Servo-Arm',
               'Grants one additional Power Fist-style close-combat attack, rolled separately, and +1 to Battlesmith repair rolls. A normal 5+ repair therefore succeeds on a 4+ while the Servo-Arm is retained.')
shared_upgrade('r29-gear-cognis-signum', 'Cognis Signum',
               'The no-scatter deployment range of the bearer’s Nuncio Vox is increased from 6” to 12”. A Targeting Matrix also provides the normal Signum benefit to the bearer’s joined unit.')
shared_upgrade('r29-gear-aether-shock-maul', 'Aether-shock Maul',
               'Counts as a Power Weapon. Against Psykers and models with the Daemon special rule, it always wounds on a 2+.')
shared_upgrade('r29-gear-cortex-controller', 'Cortex Controller',
               'Friendly Battle-Automata within 6” automatically pass Command Uplink or equivalent control tests. The Praevian’s accompanying Maniple is controlled normally by this item.')
shared_upgrade('r29-gear-cortex-designator', 'Cortex Designator',
               'When the Praevian scores one or more successful To Hit rolls with a shooting weapon against an enemy unit, his attached Battle-Automata Maniple gains Preferred Enemy against that unit until the end of the current player turn. No unsaved Wound is required.')

sia = shared_upgrade('r29-gear-special-issue-ammunition', 'Special Issue Ammunition', profiles=[
    ('r29-sia-dragon', 'Dragonfire Bolts', '24”', '4', '5', 'Rapid Fire, Ignores Cover'),
    ('r29-sia-hellfire', 'Hellfire Bolts', '24”', 'X', '5', 'Rapid Fire, Poison (2+)'),
    ('r29-sia-kraken', 'Kraken Bolts', '30”', '4', '4', 'Rapid Fire'),
    ('r29-sia-vengeance', 'Vengeance Rounds', '18”', '4', '3', 'Rapid Fire, Gets Hot'),
])
add_rule(sia, 'r29-sia-rule', 'Special Issue Ammunition',
         'Each time the bearer fires an eligible bolt weapon, select one ammunition profile. Only one ammunition type may be used for that shooting attack.')


# ---------------------------------------------------------------------------
# Demolisher / Flamestorm profiles.
# ---------------------------------------------------------------------------
for name, pid, vals in [
    ('Demolisher Cannon', 'r29-prof-demolisher', ('24”', '10', '2', 'Ordnance 1, Large Blast')),
    ('Flamestorm Cannon', 'r29-prof-flamestorm', ('Template', '6', '3', 'Heavy 1')),
]:
    matches = [e for e in shared.findall(Q('selectionEntry')) if e.get('name') == name]
    assert matches, f'Missing shared weapon entry: {name}'
    e = matches[0]
    profiles = direct(e, 'profiles')
    if profiles is not None:
        for ch in list(profiles):
            profiles.remove(ch)
    add_ranged(e, pid, name, *vals)
    rules = direct(e, 'rules')
    if rules is not None:
        for r in list(rules):
            if r.get('name') == name:
                d = r.find(Q('description'))
                if d is not None:
                    d.text = 'Use the weapon profile shown above.'


# Force Weapons are no longer generic Praetor/Centurion Armoury purchases.
remove_by_id('hq-centurion-sw-3')
remove_by_id('hq-praetor-sw-3')

consul_ids = {
    'chap': 'hq-consul-chaplain', 'lib': 'hq-consul-librarian', 'mor': 'hq-consul-moritat',
    'delegatus': 'hq-consul-delegatus', 'eso': 'hq-consul-esoterist', 'forge': 'hq-consul-forge',
    'herald': 'hq-consul-herald', 'signals': 'hq-consul-signals', 'med': 'hq-consul-medicae',
    'null': 'hq-consul-null', 'vig': 'hq-consul-vigilator', 'prae': 'hq-consul-praevian',
}
C = {k: by_id(v) for k, v in consul_ids.items()}
assert all(v is not None for v in C.values()), [k for k, v in C.items() if v is None]

# Existing omnibus rule becomes a short header; all actual rules are split out below.
for key, e in C.items():
    rules = direct(e, 'rules')
    if rules is None:
        continue
    old_id = consul_ids[key] + '-rule'
    for r in list(rules):
        if r.get('id') == old_id:
            d = r.find(Q('description'))
            if d is not None:
                d.text = f'This Centurion is upgraded to {e.get("name")}. Granted wargear and special rules are shown separately below.'


# ---------------------------------------------------------------------------
# Chaplain.
# ---------------------------------------------------------------------------
auto_link(C['chap'], 'r29-chap-crozius', 'Crozius Arcanum', 'r29-gear-crozius')
auto_link(C['chap'], 'r29-chap-rosarius', 'Rosarius', 'r29-gear-rosarius')
add_rule(C['chap'], 'r29-chap-honour', 'Honour of the Legion',
         'The Chaplain and any unit he has joined have the Fearless special rule.')
add_rule(C['chap'], 'r29-chap-liturgies', 'Liturgies of Battle',
         'In a player turn in which the Chaplain and a unit he has joined successfully charge, the Chaplain and all models in that unit may re-roll failed To Hit rolls in close combat for that Assault phase.')


# ---------------------------------------------------------------------------
# ProHammer psychic disciplines.
# ---------------------------------------------------------------------------
DISCIPLINES = {
    'Biomancy': [
        ('Smite', 'Witchfire. Range 18”, S4 AP2 Assault 4.', ('18”', '4', '2', 'Assault 4')),
        ('Iron Arm', 'Blessing — targets Psyker. Adds +2 Strength and +1 Toughness.', None),
        ('Enfeeble', 'Malediction — enemy unit within 24”. -1 Strength and Toughness; treats all movement as Difficult Terrain.', None),
        ('Life Leech', 'Witchfire. Range 18”, S6 AP2 Assault 2. If it causes at least one unsaved Wound, a model within 6” of the Psyker regains a Wound.', ('18”', '6', '2', 'Assault 2')),
        ('Warp Speed', 'Blessing — targets Psyker. Adds +3 Initiative and +3 Attacks and grants Fleet.', None),
        ('Endurance', 'Blessing — friendly unit within 24”. The unit gains Eternal Warrior, Feel No Pain (5+) and Relentless.', None),
        ('Haemorrhage', 'Focused Witchfire — range 18”. Resolve the ProHammer Haemorrhage Toughness-test chain effect.', None),
    ],
    'Divination': [
        ('Prescience', 'Blessing — friendly unit within 12”. Re-roll all failed To Hit rolls.', None),
        ('Foreboding', 'Blessing — targets Psyker. Psyker and joined unit gain Counter-Attack and may fire reaction fire using the full number of allowed shots.', None),
        ('Forewarning', 'Blessing — friendly unit within 12”. Unit gains a 4+ Invulnerable Save.', None),
        ('Perfect Timing', 'Blessing — targets Psyker. Psyker and joined unit ignore Cover when shooting.', None),
        ('Precognition', 'Blessing — targets Psyker. Re-roll failed To Hit, To Wound and Saving Throw rolls as described in ProHammer.', None),
        ('Misfortune', 'Malediction — enemy unit within 24”. Attacks against the target count as Rending.', None),
        ('Scrier’s Gaze', 'Blessing — targets Psyker. Apply the ProHammer Reserve, Outflank and mystery-objective re-roll benefits.', None),
    ],
    'Pyromancy': [
        ('Flame Breath', 'Witchfire. Template, S5 AP4 Assault 1, Soul Blaze.', ('Template', '5', '4', 'Assault 1, Soul Blaze')),
        ('Fiery Form', 'Blessing — targets Psyker. Gains a 4+ Invulnerable Save; melee attacks cause Soul Blaze; re-roll failed Wounds inflicted by other Pyromancy powers.', None),
        ('Molton Beam', 'Beam. Range 12”, S8 AP1 Assault 1, Melta.', ('12”', '8', '1', 'Assault 1, Melta')),
        ('Fire Shield', 'Blessing — friendly unit within 24”. Gains a 4+ Cover Save; enemy units within 6” treat all terrain, including open ground, as Dangerous Terrain.', None),
        ('Sunburst', 'Nova. Range 9”, S4 AP5 Assault 2D6, Ignores Cover, Soul Blaze.', ('9”', '4', '5', 'Assault 2D6, Ignores Cover, Soul Blaze')),
        ('Inferno', 'Witchfire. Range 24”, S4 AP5 Assault 1, Large Blast, Ignores Cover, Soul Blaze.', ('24”', '4', '5', 'Assault 1, Large Blast, Ignores Cover, Soul Blaze')),
        ('Spontaneous Combustion', 'Focused Witchfire — range 18”. Resolve the S6 AP3 Soul Blaze hit and secondary blast as described in ProHammer.', None),
    ],
    'Telekinesis': [
        ('Assail', 'Beam. Range 18”, S6 AP– Assault 1, Strikedown.', ('18”', '6', '–', 'Assault 1, Strikedown')),
        ('Crush', 'Focused Witchfire — range 18”. Roll 2D6 for the hit’s Strength and another D6 for AP.', None),
        ('Objuration Mechanicum', 'Malediction — enemy unit within 24”. Target ranged weapons gain Gets Hot; Vehicles suffer an immediate Haywire hit.', None),
        ('Shockwave', 'Nova. Range 9”, S4 AP– Assault 2D6, Pinning.', ('9”', '4', '–', 'Assault 2D6, Pinning')),
        ('Levitation', 'Blessing — targets Psyker. Psyker and joined unit immediately move up to 12”; cannot charge that turn and count as having moved.', None),
        ('Telekine Dome', 'Blessing — targets Psyker. Psyker and all friendly models within 12” gain a 5+ Invulnerable Save against shooting attacks.', None),
        ('Psychic Maelstrom', 'Witchfire. Range 12”, S10 AP1 Assault 1, Barrage, Large Blast.', ('12”', '10', '1', 'Assault 1, Barrage, Large Blast')),
    ],
    'Telepathy': [
        ('Psychic Shriek', 'Witchfire — range 18”. Roll 3D6 and subtract target Leadership; target suffers Wounds equal to the result with no Armour or Cover Saves.', None),
        ('Dominate', 'Malediction — enemy unit within 24”. Target must pass a Leadership test whenever it attempts to move, Advance, shoot, charge or use a psychic power.', None),
        ('Mental Fortitude', 'Blessing — friendly unit within 24”. If Falling Back, immediately Regroups; target gains Fearless.', None),
        ('Terrify', 'Malediction — enemy unit within 24”. -1 Leadership; treats opposing units as causing Fear; must take a Casualty Test at end of turn.', None),
        ('Hallucination', 'Malediction — enemy unit within 24”. Roll a D6 and apply the ProHammer Hallucination result.', None),
        ('Invisibility', 'Blessing — friendly unit within 24”. Opposing units suffer -1 To Hit with ranged and melee attacks against the target.', None),
        ('Shrouding', 'Blessing — targets Psyker. All friendly models within 6” gain Shrouded.', None),
    ],
    'Sanctic Daemonology': [
        ('Banishment', 'Malediction — enemy Daemon unit within 24”. All models in target unit suffer -1 to their Invulnerable Saves.', None),
        ('Gate of Infinity', 'Blessing — targets Psyker. Remove Psyker and joined unit and immediately redeploy using Deep Strike.', None),
        ('Hammerhand', 'Blessing — targets Psyker. Psyker and joined unit gain +2 Strength.', None),
        ('Sanctuary', 'Blessing — targets Psyker. Psyker and joined unit receive +1 to Invulnerable Saves, or gain a 6+ Invulnerable Save; Daemons treat all terrain within 12” as Dangerous Terrain.', None),
        ('Purge Soul', 'Focused Witchfire — range 24”. Psyker and target roll D6 + Leadership; if Psyker is equal or higher, target suffers one automatic Wound with no Armour or Cover Save.', None),
        ('Cleansing Flame', 'Nova. Range 9”, S5 AP4 Assault 2D6, Ignores Cover, Soul Blaze.', ('9”', '5', '4', 'Assault 2D6, Ignores Cover, Soul Blaze')),
        ('Vortex of Doom', 'Witchfire. Range 12”, S10 AP1 Assault 1, Blast, Vortex.', ('12”', '10', '1', 'Assault 1, Blast, Vortex')),
    ],
    'Malefic Daemonology': [
        ('Summoning', 'Conjuration — range 12”. Summons the Daemon unit choices listed in ProHammer.', None),
        ('Cursed Earth', 'Blessing — targets Psyker. Daemons within 12” gain +1 to Invulnerable Saves; Deep Striking Daemons do not scatter when their centre model is placed within 12”.', None),
        ('Dark Flame', 'Witchfire. Template, S4 AP5 Assault 1, Soul Blaze, Torrent.', ('Template', '4', '5', 'Assault 1, Soul Blaze, Torrent')),
        ('Sacrifice', 'Conjuration — range 6”. Summons a Herald with up to 30 points of wargear; one friendly model within 6” suffers one Wound with no save.', None),
        ('Incursion', 'Conjuration — range 12”. Summons the Daemon cavalry/beast choices listed in ProHammer.', None),
        ('Infernal Gaze', 'Beam. Range 18”, S3 AP4 Assault 1, Armourbane, Fleshbane.', ('18”', '3', '4', 'Assault 1, Armourbane, Fleshbane')),
    ],
}


def psychic_ui(consul, prefix, allowed, epistolary_id=None):
    groups = ensure_container(consul, 'selectionEntryGroups')
    dg = ET.SubElement(groups, Q('selectionEntryGroup'), {
        'name': 'Psychic Discipline(s)', 'id': prefix + '-discipline-group', 'hidden': 'false'
    })
    add_constraint(dg, prefix + '-discipline-min', 'min', 1)
    add_constraint(dg, prefix + '-discipline-max', 'max', 1)
    entries = ET.SubElement(dg, Q('selectionEntries'))
    disc_ids = {}
    for i, name in enumerate(allowed):
        did = f'{prefix}-discipline-{i}'
        disc_ids[name] = did
        x = local_upgrade(entries, did, name)
        add_rule(x, did + '-rule', name,
                 f'This Psyker may select powers from the {name} discipline as permitted by its Consul entry and ProHammer Classic.')

    pg = ET.SubElement(groups, Q('selectionEntryGroup'), {
        'name': 'Psychic Powers', 'id': prefix + '-power-group', 'hidden': 'false'
    })
    add_constraint(pg, prefix + '-power-min', 'min', 1)
    add_constraint(pg, prefix + '-power-max', 'max', 1)
    powers = ET.SubElement(pg, Q('selectionEntries'))
    n = 0
    for dname in allowed:
        for pname, desc, profile in DISCIPLINES[dname]:
            pid = f'{prefix}-power-{n}'
            n += 1
            x = local_upgrade(powers, pid, pname)
            add_rule(x, pid + '-rule', pname, desc)
            if profile:
                add_ranged(x, pid + '-profile', pname, *profile)
            hidden_unless(x, disc_ids[dname])

    if epistolary_id:
        set_constraint_when(dg, prefix + '-discipline-max', 2, epistolary_id)
        set_constraint_when(pg, prefix + '-power-min', 2, epistolary_id)
        set_constraint_when(pg, prefix + '-power-max', 2, epistolary_id)


# Librarian.
auto_link(C['lib'], 'r29-lib-force', 'Force Weapon', 'gear-hq-force')
add_rule(C['lib'], 'r29-lib-psyker', 'Psyker (Mastery Level 1)',
         'The Librarian is a Psyker with Mastery Level 1 and follows the ProHammer Classic psychic rules.')
add_rule(C['lib'], 'r29-lib-support', 'Legion Support Officer',
         'May not fulfil the compulsory HQ selection unless another rule specifically permits it.')
add_rule(C['lib'], 'r29-lib-powers', 'Psychic Powers',
         'Select powers from Biomancy, Divination, Pyromancy, Telekinesis or Telepathy. Daemonology is not available. ProHammer allows powers to be chosen rather than randomly generated.')
ep = None
for x in C['lib'].iter():
    if 'Epistolary' in (x.get('name') or '') and x.get('id') != C['lib'].get('id'):
        ep = x
        break
assert ep is not None, 'Epistolary upgrade not found'
psychic_ui(C['lib'], 'r29-lib', ['Biomancy', 'Divination', 'Pyromancy', 'Telekinesis', 'Telepathy'], ep.get('id'))


# Moritat.
for slug, name, desc in [
    ('scout', 'Scout', 'Uses the normal ProHammer Scout special rule.'),
    ('counter', 'Counter-Attack', 'Uses the normal ProHammer Counter-Attack special rule.'),
    ('dual', 'Dual Pistols', 'The Moritat may fire both pistols during the Shooting phase. If he does so, he may not fire any other weapon that phase.'),
    ('lone', 'Lone Killer', 'The Moritat may not fulfil a compulsory HQ choice and may never be the Warlord. He may only join a Legion Destroyer Squad and may not benefit from beneficial psychic powers used by another model or another model’s Leadership/re-rolls.'),
    ('chain', 'Chain Fire', 'When firing his pistols, each successful To Hit roll immediately generates another shot with that pistol against the same target, continuing until it misses. Maximum 12 successful hits in total. Gets Hot on a natural 1 ends the attack. After Chain Fire, the Moritat may not charge that turn and may not shoot in his following Shooting phase.'),
]:
    add_rule(C['mor'], 'r29-mor-' + slug, name, desc)
mgroups = ensure_container(C['mor'], 'selectionEntryGroups')
mg = ET.SubElement(mgroups, Q('selectionEntryGroup'), {'name': 'Pistol Pair', 'id': 'r29-mor-pair-group', 'hidden': 'false'})
add_constraint(mg, 'r29-mor-pair-min', 'min', 1)
add_constraint(mg, 'r29-mor-pair-max', 'max', 1)
me = ET.SubElement(mg, Q('selectionEntries'))
for i, (id_, name, cost, prof, desc) in enumerate([
    ('r29-mor-bolt', 'Two Bolt Pistols', 0, ('12”', '4', '5', 'Pistol'), 'The Moritat carries two Bolt Pistols.'),
    ('r29-mor-hand', 'Two Hand Flamers', 10, ('Template', '3', '6', 'Pistol'), 'Both Bolt Pistols are replaced by Hand Flamers.'),
    ('r29-mor-plasma', 'Two Plasma Pistols', 30, ('12”', '7', '2', 'Pistol, Gets Hot'), 'Both Bolt Pistols are replaced by Plasma Pistols.'),
]):
    x = local_upgrade(me, id_, name, cost, default=(i == 0), minv=1 if i == 0 else None)
    add_ranged(x, id_ + '-profile', name, *prof)
    add_rule(x, id_ + '-rule', name, desc)
da = local_upgrade(me, 'r29-mor-calibanite', 'Two Calibanite Plasma Pistols', 30)
add_ranged(da, 'r29-mor-calibanite-profile', 'Calibanite Plasma Pistol (x2)', '12”', '6', '2', 'Pistol')
add_rule(da, 'r29-mor-calibanite-rule', 'Ancient Plasma Weaponry',
         'Both Bolt Pistols are replaced by Calibanite Plasma Pistols. Calibanite Plasma weapons do not have Gets Hot.')
mods = ensure_container(da, 'modifiers')
m = ET.SubElement(mods, Q('modifier'), {'type': 'set', 'value': 'true', 'field': 'hidden'})
cs = ET.SubElement(m, Q('conditions'))
condition(cs, 'lessThan', 1, 'legion-i', 'roster')
for wid in ['hq-centurion-sw-4', 'hq-centurion-sw-7', 'hq-centurion-sw-13', 'da22-alt-pp-17']:
    x = by_id(wid)
    if x is not None:
        hidden_if(x, 'hq-consul-moritat')


# Delegatus.
add_rule(C['delegatus'], 'r29-delegatus-master', 'Master of the Legion',
         'The Delegatus has Master of the Legion and may enable one Rite of War, subject to the normal limits on that rule.')
add_rule(C['delegatus'], 'r29-delegatus-authority', 'Delegated Authority',
         'A Delegatus may possess Master of the Legion in an army of fewer than 1,000 points. Unless the army contains its Primarch, a Delegatus with Master of the Legion must be the Warlord. A Detachment containing a Delegatus may not also contain a Legion Praetor.')


# Esoterist.
auto_link(C['eso'], 'r29-eso-force', 'Force Weapon', 'gear-hq-force')
add_rule(C['eso'], 'r29-eso-psyker', 'Psyker (Mastery Level 1)',
         'The Esoterist is a Psyker with Mastery Level 1 and follows the ProHammer Classic psychic rules.')
add_rule(C['eso'], 'r29-eso-support', 'Legion Support Officer',
         'May not fulfil the compulsory HQ selection unless another rule specifically permits it.')
add_rule(C['eso'], 'r29-eso-lore', 'Forbidden Lore',
         'Select powers from Sanctic Daemonology or Malefic Daemonology regardless of Legion or Allegiance. Possession is not selectable because ProHammer restricts it to Mastery Level 2 or greater.')
psychic_ui(C['eso'], 'r29-eso', ['Sanctic Daemonology', 'Malefic Daemonology'])


# Forge Lord.
auto_link(C['forge'], 'r29-forge-artificer', 'Artificer Armour', 'gear-hq-artificer')
auto_link(C['forge'], 'r29-forge-servo', 'Servo-Arm', 'r29-gear-servo-arm')
add_rule(C['forge'], 'r29-forge-battlesmith', 'Battlesmith',
         'During the Shooting phase, instead of firing a weapon, a Forge Lord in base contact with or embarked upon a friendly damaged Vehicle may attempt a repair. On 5+, remove one Engine Damaged, Weapon Destroyed or Immobilised result. His Servo-Arm grants +1, so he normally succeeds on 4+.')
add_rule(C['forge'], 'r29-forge-armoury', 'Lord of the Armoury',
         'May select equipment restricted to Techmarines from the Space Marine Armoury in addition to equipment normally available to a Centurion.')


# Herald.
add_rule(C['herald'], 'r29-herald-support', 'Legion Support Officer',
         'May not fulfil the compulsory HQ selection unless another rule specifically permits it.')
add_rule(C['herald'], 'r29-herald-banner', 'Banner of Allegiance',
         'Use the selected Banner of the Aquila or Banner of the Eye rule shown by the Herald upgrade.')
add_rule(C['herald'], 'r29-herald-fallen', 'Fallen Honour',
         'If the Herald is slain, the opposing player gains +1 Victory Point in missions using Victory Points.')


# Master of Signals: retain the already-coded Orbital Bombardment and Damocles blocks.
auto_link(C['signals'], 'r29-signals-nuncio', 'Nuncio Vox', 'gear-nuncio')
auto_link(C['signals'], 'r29-signals-cognis', 'Cognis Signum', 'r29-gear-cognis-signum')
add_rule(C['signals'], 'r29-signals-support', 'Legion Support Officer',
         'May not fulfil the compulsory HQ selection unless another rule specifically permits it.')
add_rule(C['signals'], 'r29-signals-cognis-rule', 'Cognis Signum',
         'The Master of Signals’ Nuncio Vox no-scatter range is 12” instead of 6”. The optional Targeting Matrix also grants the normal Signum benefit to his joined unit.')


# Primus Medicae: existing automatic Narthecium and optional Reductor are retained.
add_rule(C['med'], 'r29-med-support', 'Legion Support Officer',
         'May not fulfil the compulsory HQ selection unless another rule specifically permits it.')
add_rule(C['med'], 'r29-med-sacred', 'Sacred Trust',
         'In a mission using Victory Points, whenever a friendly Legiones Astartes Infantry or Jump Infantry unit with a model within 6” is completely destroyed by the enemy, roll a D6. On 5+, gain 50 Victory Points. A unit for which Victory Points are recovered through the Primus Medicae’s Reductor may not also generate Victory Points through Sacred Trust.')


# Primus Nullificator.
auto_link(C['null'], 'r29-null-maul', 'Aether-shock Maul', 'r29-gear-aether-shock-maul')
for slug, name, desc in [
    ('psyker', 'Psyker (Mastery Level 1)', 'The Nullificator is a Psyker with Mastery Level 1 and follows the ProHammer Classic psychic rules.'),
    ('support', 'Legion Support Officer', 'May not fulfil the compulsory HQ selection unless another rule specifically permits it.'),
    ('will', 'Adamantium Will', 'Uses the normal ProHammer Adamantium Will special rule.'),
    ('wards', 'Hexagrammic Wards', 'An enemy Psyker using a psychic power which directly targets the Nullificator or a unit he has joined suffers -1 Leadership for that Psychic Test.'),
    ('credo', 'Credo Annihilato', 'The Nullificator and any unit he has joined have Preferred Enemy (Daemons).'),
]:
    add_rule(C['null'], 'r29-null-' + slug, name, desc)
psychic_ui(C['null'], 'r29-null', ['Sanctic Daemonology'])


# Vigilator.
auto_link(C['vig'], 'r29-vig-bolter', 'Bolter', 'gear-bolter')
auto_link(C['vig'], 'r29-vig-camo', 'Cameleoline', 'gear-cameleoline')
auto_link(C['vig'], 'r29-vig-ammo', 'Special Issue Ammunition', 'r29-gear-special-issue-ammunition')
add_rule(C['vig'], 'r29-vig-scout', 'Scout', 'Uses the normal ProHammer Scout special rule.')
add_rule(C['vig'], 'r29-vig-stealth', 'Stealth', 'Uses the normal ProHammer Stealth special rule. Cameleoline is displayed as granted wargear.')
add_rule(C['vig'], 'r29-vig-sabotage', 'Sabotage',
         'After both armies deploy but before the first turn, nominate one enemy unit, Vehicle or Fortification on the battlefield; an Independent Character may only be selected if part of another unit. The target suffers D6 Strength 5 AP6 hits; against Vehicles or Fortifications use the lowest Armour Value. Casualties do not cause Morale or Pinning tests.')
add_rule(C['vig'], 'r29-vig-ammo-rule', 'Special Issue Ammunition',
         'The Vigilator may use Dragonfire, Hellfire, Kraken or Vengeance ammunition with his Bolter, overriding the normal Seeker-only restriction. All four profiles are displayed under his Special Issue Ammunition wargear.')


# Praevian visible wargear and source-backed robots.
auto_link(C['prae'], 'r29-prae-controller', 'Cortex Controller', 'r29-gear-cortex-controller')
auto_link(C['prae'], 'r29-prae-designator', 'Cortex Designator', 'r29-gear-cortex-designator')
add_rule(C['prae'], 'r29-prae-support', 'Legion Support Officer',
         'May not fulfil the compulsory HQ selection unless another rule specifically permits it.')
add_rule(C['prae'], 'r29-prae-cybernetica', 'Master of Cybernetica',
         'The Praevian must begin attached to his purchased Battle-Automata Maniple and may not voluntarily leave it while any Automata remain. The Maniple occupies no additional Force Organisation slot. If the Praevian is slain, normal Cybernetica Cortex and Programmed Behaviour rules apply.')
add_rule(C['prae'], 'r29-prae-inductees', 'Legion Inductees',
         'Before deployment choose the Praevian’s Legiones Astartes rule, Furious Charge, Tank Hunters or Scout for the accompanying Battle-Automata Maniple. If Scout is chosen the Praevian also gains Scout while attached.')
pgroups = ensure_container(C['prae'], 'selectionEntryGroups')
pg = ET.SubElement(pgroups, Q('selectionEntryGroup'), {
    'name': 'Praevian Battle-Automata', 'id': 'r29-prae-automata-group', 'hidden': 'false'
})
add_constraint(pg, 'r29-prae-automata-max', 'max', 1)
pse = ET.SubElement(pg, Q('selectionEntries'))
man = ET.SubElement(pse, Q('selectionEntry'), {
    'type': 'unit', 'name': 'Castellan Class Robot Maniple (Mechanicum source)',
    'id': 'r29-prae-castellan', 'hidden': 'false', 'import': 'true'
})
add_constraint(man, 'r29-prae-castellan-max', 'max', 1, include_children=False)
add_cost(man, 105)
profiles = ensure_container(man, 'profiles')
mp = ET.SubElement(profiles, Q('profile'), {
    'name': 'Castellan Class Robot', 'id': 'r29-prae-castellan-profile',
    'typeId': 'prof-model', 'typeName': 'Model', 'hidden': 'false'
})
chars = ET.SubElement(mp, Q('characteristics'))
for n, tid, val in [
    ('WS', 'model-ws', '3'), ('BS', 'model-bs', '3'), ('S', 'model-s', '5(10)'),
    ('T', 'model-t', '6'), ('W', 'model-w', '3'), ('I', 'model-i', '3'),
    ('A', 'model-a', '2'), ('Ld', 'model-ld', '8'), ('Sv', 'model-sv', '3+')
]:
    ET.SubElement(chars, Q('characteristic'), {'name': n, 'typeId': tid}).text = val
add_rule(man, 'r29-prae-castellan-wargear', 'Standard Wargear',
         'Two Dreadnought Close Combat Weapons, a Twin-linked Bolter and a shoulder-mounted Heavy Bolter.')
add_rule(man, 'r29-prae-castellan-uplink', 'Command Uplink',
         'At the start of every phase, if not within 6” of a friendly Cortex Controller, the unit must pass its Command Uplink Leadership test before acting. The Praevian’s Cortex Controller controls his accompanying Maniple normally.')
add_rule(man, 'r29-prae-castellan-targeting', 'Targeting Protocols',
         'The model may fire its two weapons at the same target if both are in range.')
add_rule(man, 'r29-prae-castellan-type', 'Monstrous Creature',
         'Castellan Class Robots count as Monstrous Creatures for rules and modifiers.')
add_rule(man, 'r29-prae-castellan-source', 'Source Note',
         'The generic Praevian entry calls for Castellax or Vorax Battle-Automata, while the supplied Mechanicum list presently provides a Castellan Class Robot profile. This option reproduces the available Mechanicum profile without inventing a Vorax profile or silently equating the names.')
mse = ensure_container(man, 'selectionEntries')
local_upgrade(mse, 'r29-prae-castellan-extra', 'Additional Castellan Class Robot', 105, maxv=3)
wg = ensure_container(man, 'selectionEntryGroups')
shoulder = ET.SubElement(wg, Q('selectionEntryGroup'), {
    'name': 'Shoulder Weapon Replacements', 'id': 'r29-prae-castellan-shoulder', 'hidden': 'false'
})
add_constraint(shoulder, 'r29-prae-castellan-shoulder-max', 'max', 4)
sse = ET.SubElement(shoulder, Q('selectionEntries'))
for id_, name, cost, prof in [
    ('r29-prae-assault-cannon', 'Assault Cannon', 35, ('24”', '6', '4', 'Heavy 4, Rending')),
    ('r29-prae-multi-melta', 'Multi-Melta', 40, ('24”', '8', '1', 'Heavy 1, Melta')),
    ('r29-prae-plasma-cannon', 'Plasma Cannon', 45, ('36”', '7', '2', 'Heavy 1, Blast, Gets Hot')),
]:
    x = local_upgrade(sse, id_, name, cost, maxv=4)
    add_ranged(x, id_ + '-profile', name, *prof)
bolter = ET.SubElement(wg, Q('selectionEntryGroup'), {
    'name': 'Twin-linked Bolter Replacements', 'id': 'r29-prae-castellan-bolter', 'hidden': 'false'
})
add_constraint(bolter, 'r29-prae-castellan-bolter-max', 'max', 4)
bse = ET.SubElement(bolter, Q('selectionEntries'))
fl = local_upgrade(bse, 'r29-prae-flamer', 'Flamer', 5, maxv=4)
add_ranged(fl, 'r29-prae-flamer-profile', 'Flamer', 'Template', '4', '5', 'Assault 1')
add_rule(man, 'r29-prae-upgrade-limit', 'Robot Upgrade Limit',
         'Weapon replacement selections may not exceed the number of Castellan Class Robots actually present in the Maniple; each robot may replace each listed weapon no more than once.')


# Mandatory Consul armour changes are reflected in the Centurion profile.
cent_prof = by_id('hq-centurion-prof')
assert cent_prof is not None
mods = direct(cent_prof, 'modifiers')
if mods is None:
    mods = ET.SubElement(cent_prof, Q('modifiers'))  # profile modifiers follow characteristics
for id_, value, child in [
    ('r29-cent-sv-forge', '2+', 'hq-consul-forge'),
    ('r29-cent-sv-null', '2+/4+', 'hq-consul-null'),
]:
    m = ET.SubElement(mods, Q('modifier'), {'type': 'set', 'field': 'model-sv', 'value': value, 'id': id_})
    cs = ET.SubElement(m, Q('conditions'))
    condition(cs, 'atLeast', 1, child)


# ---------------------------------------------------------------------------
# Validation and canonical New Recruit serialization.
# ---------------------------------------------------------------------------
ids = [e.get('id') for e in root.iter() if e.get('id')]
dups = [k for k, v in Counter(ids).items() if v > 1]
assert not dups, f'Duplicate IDs: {dups[:20]}'
all_ids = set(ids)
# Only ensure this release introduces no new dangling entryLinks. Rev28 inherited
# a small number of older dangling legacy links which are intentionally not silently
# rewritten as part of the Consul cleanup.
bad = []
for e in root.iter(Q('entryLink')):
    if not (e.get('id') or '').startswith('r29-'):
        continue
    target = e.get('targetId')
    if target and target not in all_ids:
        bad.append((e.get('id'), target))
assert not bad, f'Broken Revision 29 entryLinks: {bad[:20]}'
for need in [
    'r29-gear-crozius', 'r29-gear-special-issue-ammunition', 'r29-lib-discipline-group',
    'r29-mor-pair-group', 'r29-prae-castellan', 'r29-prof-demolisher', 'r29-prof-flamestorm'
]:
    assert by_id(need) is not None, need
assert by_id('hq-centurion-sw-3') is None
assert by_id('hq-praetor-sw-3') is None
assert root.get('revision') == '29' and root.get('gameSystemRevision') == '12'

body = ET.tostring(root, encoding='unicode', short_empty_elements=True)
assert body.startswith('<catalogue '), body[:120]
assert f'xmlns="{NS}"' in body[:500], body[:500]
xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + body + '\n'
assert '<ns0:' not in xml
CAT.write_text(xml, encoding='utf-8', newline='\n')
ET.parse(CAT)

print('REV29 MATERIALISED')
print('Catalogue revision 29 / GST linkage 12')
print('Consuls cleaned:', ', '.join(e.get('name') for e in C.values()))
print('ProHammer powers available:', sum(len(v) for v in DISCIPLINES.values()))
print('Praevian: source-backed Castellan Class Robot Maniple added; Vorax not invented')
