from pathlib import Path
import re
import xml.etree.ElementTree as ET

CAT = Path("Legiones Astartes.cat")
GST = Path("Prohammer 30k.gst")
INDEX = Path("index.xml")

CNS = "http://www.battlescribe.net/schema/catalogueSchema"
GNS = "http://www.battlescribe.net/schema/gameSystemSchema"
C = lambda t: f"{{{CNS}}}{t}"
G = lambda t: f"{{{GNS}}}{t}"

ct = ET.parse(CAT)
cr = ct.getroot()
gt = ET.parse(GST)
gr = gt.getroot()

REPORT = []
def note(s):
    REPORT.append(s)
    print(s)

def by_id(root, id_):
    return next((e for e in root.iter() if e.get("id") == id_), None)

def ensure(parent, tag, ns=CNS):
    q = f"{{{ns}}}{tag}"
    x = parent.find(q)
    if x is None:
        x = ET.SubElement(parent, q)
    return x

def remove_prefixed(root, prefix):
    n = 0
    for p in list(root.iter()):
        for x in list(p):
            if (x.get("id") or "").startswith(prefix):
                p.remove(x)
                n += 1
    return n

def remove_rule_named(e, name):
    rs = e.find(C("rules"))
    if rs is None:
        return
    for r in list(rs):
        if (r.get("name") or "").strip().lower() == name.lower():
            rs.remove(r)
    if len(rs) == 0:
        e.remove(rs)

def add_rule(e, id_, name, text):
    rs = ensure(e, "rules")
    r = ET.SubElement(rs, C("rule"), {"id": id_, "name": name, "hidden": "false"})
    ET.SubElement(r, C("description")).text = text
    return r

def add_constraint(e, id_, kind, value, scope="parent"):
    cs = ensure(e, "constraints")
    return ET.SubElement(cs, C("constraint"), {
        "id": id_,
        "type": kind,
        "value": str(value),
        "field": "selections",
        "scope": scope,
        "shared": "true",
        "includeChildSelections": "true",
        "includeChildForces": "false",
    })

def group(e, id_, name, minv=None, maxv=None):
    gs = ensure(e, "selectionEntryGroups")
    g = ET.SubElement(gs, C("selectionEntryGroup"), {
        "id": id_,
        "name": name,
        "hidden": "false",
        "collective": "false",
        "import": "true",
    })
    if minv is not None:
        add_constraint(g, id_ + "-min", "min", minv)
    if maxv is not None:
        add_constraint(g, id_ + "-max", "max", maxv)
    return g

def option(g, id_, name, cost=0, maxv=1):
    ses = ensure(g, "selectionEntries")
    s = ET.SubElement(ses, C("selectionEntry"), {
        "id": id_,
        "name": name,
        "type": "upgrade",
        "hidden": "false",
        "import": "true",
    })
    add_constraint(s, id_ + "-max", "max", maxv)
    costs = ensure(s, "costs")
    ET.SubElement(costs, C("cost"), {"name": "Points", "typeId": "pts", "value": str(cost)})
    return s

def add_profile(e, id_, name, range_, strength, ap, type_):
    ps = ensure(e, "profiles")
    p = ET.SubElement(ps, C("profile"), {
        "id": id_,
        "name": name,
        "hidden": "false",
        "typeId": "prof-ranged",
        "typeName": "Ranged Weapon",
    })
    cs = ET.SubElement(p, C("characteristics"))
    vals = [
        ("Range", "ranged-range", range_),
        ("S", "ranged-s", strength),
        ("AP", "ranged-ap", ap),
        ("Type", "ranged-type", type_),
    ]
    for nm, tid, val in vals:
        ET.SubElement(cs, C("characteristic"), {"name": nm, "typeId": tid}).text = str(val)
    return p

def add_hide_if_selected(e, id_, child_id, scope="parent"):
    mods = ensure(e, "modifiers")
    m = ET.SubElement(mods, C("modifier"), {
        "id": id_,
        "type": "set",
        "value": "true",
        "field": "hidden",
    })
    cs = ET.SubElement(m, C("conditions"))
    ET.SubElement(cs, C("condition"), {
        "type": "atLeast",
        "value": "1",
        "field": "selections",
        "scope": scope,
        "childId": child_id,
        "shared": "true",
        "includeChildSelections": "true",
        "includeChildForces": "false",
    })
    return m

POWERS = [
    ("Biomancy", "Smite", '18"', "4", "2", "Assault 4, Witchfire",
     "Witchfire. Resolve as a normal psychic shooting attack."),
    ("Biomancy", "Iron Arm", "Self", "—", "—", "Blessing",
     "The Psyker gains +2 Strength and +1 Toughness."),
    ("Biomancy", "Enfeeble", '24"', "—", "—", "Malediction",
     "Target enemy unit suffers -1 Strength and -1 Toughness and treats all movement as Difficult Terrain."),
    ("Biomancy", "Life Leech", '18"', "6", "2", "Assault 2, Witchfire",
     "If this power causes at least one unsaved Wound, one model within 6 inches of the Psyker regains one Wound."),
    ("Biomancy", "Warp Speed", "Self", "—", "—", "Blessing",
     "The Psyker gains +3 Initiative, +3 Attacks and Fleet."),
    ("Biomancy", "Endurance", '24"', "—", "—", "Blessing",
     "Target friendly unit gains Eternal Warrior, Feel No Pain (5+) and Relentless."),
    ("Biomancy", "Haemorrhage", '18"', "Special", "Special", "Focused Witchfire",
     "Target model must pass two Toughness tests or suffer a Wound with no Armour or Cover save. If slain, select another model within 2 inches; it takes one Toughness test or suffers a Wound. Continue until a test is passed."),

    ("Divination", "Prescience", '12"', "—", "—", "Blessing",
     "Target friendly unit may re-roll all failed To Hit rolls."),
    ("Divination", "Foreboding", "Self", "—", "—", "Blessing",
     "The Psyker and any joined unit gain Counter-Attack and may make Reaction Fire using the full number of allowed shots."),
    ("Divination", "Forewarning", '12"', "—", "—", "Blessing",
     "Target friendly unit gains a 4+ Invulnerable Save."),
    ("Divination", "Perfect Timing", "Self", "—", "—", "Blessing",
     "The Psyker and any joined unit ignore Cover when shooting an enemy unit."),
    ("Divination", "Precognition", "Self", "—", "—", "Blessing",
     "The Psyker re-rolls failed To Hit and To Wound rolls and failed saving throws."),
    ("Divination", "Misfortune", '24"', "—", "—", "Malediction",
     "All attacks against the target enemy unit count as Rending."),
    ("Divination", "Scrier's Gaze", "Self", "—", "—", "Blessing",
     "While active, one Reserve each turn may automatically pass its Reserve roll; other Reserve and Outflank rolls may be re-rolled, as may Mysterious Objective rolls."),

    ("Pyromancy", "Flame Breath", "Template", "5", "4", "Assault 1, Witchfire, Soul Blaze",
     "Witchfire. Resolve using the profile shown."),
    ("Pyromancy", "Fiery Form", "Self", "—", "—", "Blessing",
     "The Psyker gains a 4+ Invulnerable Save; all of his melee attacks cause Soul Blaze, and failed To Wound rolls caused by his other Pyromancy powers may be re-rolled."),
    ("Pyromancy", "Molton Beam", '12"', "8", "1", "Assault 1, Beam, Melta",
     "Beam. Resolve using the profile shown."),
    ("Pyromancy", "Fire Shield", '24"', "—", "—", "Blessing",
     "Target friendly unit gains a 4+ Cover Save and all enemy units within 6 inches treat all terrain, including open ground, as Dangerous Terrain."),
    ("Pyromancy", "Sunburst", '9"', "4", "5", "Assault 2D6, Nova, Ignores Cover, Soul Blaze",
     "Nova. Resolve using the profile shown."),
    ("Pyromancy", "Inferno", '24"', "4", "5", "Assault 1, Witchfire, Large Blast, Ignores Cover, Soul Blaze",
     "Witchfire. Resolve using the profile shown."),
    ("Pyromancy", "Spontaneous Combustion", '18"', "6", "3", "Focused Witchfire, Soul Blaze",
     "Target model suffers one S6 AP3 hit with Soul Blaze. If slain, place a Blast marker over the removed model; all models hit suffer S5 AP4 hits that ignore Cover and cause Soul Blaze."),

    ("Telekinesis", "Assail", '18"', "6", "—", "Assault 1, Beam, Strikedown",
     "Beam. Resolve using the profile shown."),
    ("Telekinesis", "Crush", '18"', "2D6", "D6", "Focused Witchfire",
     "Roll 2D6 for the hit's Strength and a separate D6 for its AP value."),
    ("Telekinesis", "Objuration Mechanicum", '24"', "—", "—", "Malediction",
     "All ranged attacks made by the target enemy unit gain Gets Hot. Vehicles suffer an immediate Haywire hit."),
    ("Telekinesis", "Shockwave", '9"', "4", "—", "Assault 2D6, Nova, Pinning",
     "Nova. Resolve using the profile shown."),
    ("Telekinesis", "Levitation", "Self", "—", "—", "Blessing",
     "The Psyker and any joined unit may immediately move up to 12 inches. They cannot land on models or Impassable Terrain, cannot charge this turn and count as having moved."),
    ("Telekinesis", "Telekine Dome", "Self / 12\"", "—", "—", "Blessing",
     "The Psyker and all friendly models within 12 inches gain a 5+ Invulnerable Save against shooting attacks."),
    ("Telekinesis", "Psychic Maelstrom", '12"', "10", "1", "Assault 1, Witchfire, Barrage, Large Blast",
     "Witchfire. Resolve using the profile shown."),

    ("Telepathy", "Psychic Shriek", '18"', "Special", "Special", "Witchfire",
     "Roll 3D6 and subtract the target unit's Leadership. The unit suffers a number of Wounds equal to the result, with no Armour or Cover saves."),
    ("Telepathy", "Dominate", '24"', "—", "—", "Malediction",
     "The target enemy unit must pass a Leadership test each time it attempts to move, Advance, shoot, charge or use a psychic power."),
    ("Telepathy", "Mental Fortitude", '24"', "—", "—", "Blessing",
     "If the target friendly unit is Falling Back it immediately Regroups; it also gains Fearless."),
    ("Telepathy", "Terrify", '24"', "—", "—", "Malediction",
     "The target enemy unit suffers -1 Leadership, treats all opposing units as causing Fear and must take a Casualty test at the end of the turn."),
    ("Telepathy", "Hallucination", '24"', "—", "—", "Malediction",
     "Roll D6: 1-2 the unit takes a Pinning test; 3-4 it suffers -1 WS, BS, Initiative and Attacks; 5-6 randomly select a model, which takes one hit for every other model in the unit at Strength equal to the unit's majority Strength."),
    ("Telepathy", "Invisibility", '24"', "—", "—", "Blessing",
     "Opposing units suffer -1 To Hit with ranged and melee attacks against the target friendly unit."),
    ("Telepathy", "Shrouding", "Self / 6\"", "—", "—", "Blessing",
     "All friendly models within 6 inches of the Psyker gain the Shrouded special rule."),
]
assert len(POWERS) == 35

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def add_power_choice_group(owner, id_, label):
    g = group(owner, id_, label, 1, 1)
    for discipline, name, rng, strength, ap, ptype, text in POWERS:
        pid = f"{id_}-{slug(discipline)}-{slug(name)}"
        s = option(g, pid, f"{discipline} — {name}", 0, 1)
        add_profile(s, pid + "-profile", name, rng, strength, ap, ptype)
        add_rule(s, pid + "-rule", name, text)
    return g

removed_cat = remove_prefixed(cr, "r61-")
removed_gst = remove_prefixed(gr, "r61-")
note(f"Removed previous r61 nodes: CAT={removed_cat}, GST={removed_gst}")

cent = by_id(cr, "hq-centurion")
lib = by_id(cr, "hq-consul-librarian")
storm = by_id(cr, "r60-ws-stormseer")
storm_ml2 = by_id(cr, "r60-ws-stormseer-ml2")
dark = next((e for e in cr.iter(C("selectionEntry")) if (e.get("name") or "").strip().lower() == "dark sons of death"), None)
dark_transport = by_id(cr, "r60-ws-dark-transport")
dark_jump = by_id(cr, "r60-ws-dark-jump")

assert cent is not None, "Centurion not found"
assert lib is not None, "Legion Librarian Consul not found"
assert storm is not None, "White Scars Stormseer not found"
assert storm_ml2 is not None, "Stormseer Epistolary upgrade not found"
assert dark is not None, "Dark Sons of Death not found"
assert dark_transport is not None, "Dark Sons of Death transport group not found"
assert dark_jump is not None, "Dark Sons of Death Jump Pack option not found"

remove_rule_named(storm, "Stormseer Consul")
remove_rule_named(storm, "Unseen Bolt")
add_rule(storm, "r61-ws-stormseer-rule", "Stormseer Consul",
         "Replace the Centurion's Chainsword with a Force Weapon. Gains Psyker (Mastery Level 1), Adamantium Will and Legion Support Officer. A White Scars army uses the Stormseer Consul instead of the normal Legion Librarian Consul.")
add_profile(storm, "r61-ws-unseen-bolt-profile", "Unseen Bolt", '36"', "6", "4",
            "Assault 1, Blast, Pinning, Psychic")
add_rule(storm, "r61-ws-unseen-bolt-rule", "Unseen Bolt",
         "Psychic Shooting Power. Use during the Stormseer's Shooting phase instead of firing another weapon. Take a Psychic Test; if successful resolve the attack using the profile shown. Unseen Bolt may not be invoked during Return Fire, Overwatch or Stand & Shoot.")
add_power_choice_group(storm_ml2, "r61-ws-stormseer-power2", "Additional Psychic Power — select 1")

add_power_choice_group(lib, "r61-librarian-power1", "Psychic Power — select 1")
epi = next((e for e in lib.iter(C("selectionEntry")) if "epistolary" in (e.get("name") or "").lower()), None)
if epi is None:
    eg = group(lib, "r61-librarian-epistolary-group", "Librarian Options", None, 1)
    epi = option(eg, "r61-librarian-epistolary", "Epistolary — Mastery Level 2", 25, 1)
add_power_choice_group(epi, "r61-librarian-power2", "Additional Psychic Power — select 1")
note(f"Librarian psychic powers attached; Epistolary entry={epi.get('id')}")

add_hide_if_selected(dark_transport, "r61-ws-dark-hide-transport-with-jump", dark_jump.get("id"), "parent")
add_rule(dark, "r61-ws-dark-transport-rule", "Dedicated Transport",
         "Without Jump Packs, the unit may select a Rhino, Drop Pod, Dreadclaw Drop Pod or Land Raider where Transport Capacity permits. If the squad takes Jump Packs, every model must take them and the unit may not select a Dedicated Transport.")

cr.set("revision", "61")
cr.set("gameSystemRevision", "29")
gr.set("revision", "29")
comment = cr.find(C("comment"))
if comment is not None:
    comment.text = "Revision 61: psychic-discipline profiles for Librarians and Stormseers, Unseen Bolt weapon profile, and White Scars transport enforcement."

ET.register_namespace("", CNS)
ct.write(CAT, encoding="UTF-8", xml_declaration=True)
ET.register_namespace("", GNS)
gt.write(GST, encoding="UTF-8", xml_declaration=True)

idx = INDEX.read_text(encoding="utf-8")
idx = re.sub(r'(dataType="gamesystem"[^>]*dataRevision=")\d+("/>)', r'\g<1>29\2', idx)
idx = re.sub(r'(dataType="catalogue"[^>]*dataRevision=")\d+("/>)', r'\g<1>61\2', idx)
INDEX.write_text(idx, encoding="utf-8")

cat_ids = [x.get("id") for x in cr.iter() if x.get("id")]
gst_ids = [x.get("id") for x in gr.iter() if x.get("id")]
assert len(cat_ids) == len(set(cat_ids)), "Duplicate CAT IDs"
assert len(gst_ids) == len(set(gst_ids)), "Duplicate GST IDs"
all_ids = set(cat_ids) | set(gst_ids)
broken = []
for root in (cr, gr):
    for x in root.iter():
        for a in ("targetId", "childId"):
            v = x.get(a)
            if v and v not in all_ids:
                broken.append((x.get("id"), a, v))
assert not broken, broken[:20]

cattext = CAT.read_text(encoding="utf-8")
gsttext = GST.read_text(encoding="utf-8")
assert "<ns0:" not in cattext and "<ns0:" not in gsttext
assert '<catalogue xmlns="http://www.battlescribe.net/schema/catalogueSchema"' in cattext
assert '<gameSystem xmlns="http://www.battlescribe.net/schema/gameSystemSchema"' in gsttext

for gid in ("r61-librarian-power1", "r61-librarian-power2", "r61-ws-stormseer-power2"):
    g = by_id(cr, gid)
    assert g is not None, gid
    ses = g.find(C("selectionEntries"))
    assert ses is not None and len(ses.findall(C("selectionEntry"))) == 35, gid

ub = by_id(cr, "r61-ws-unseen-bolt-profile")
assert ub is not None
vals = {c.get("name"): (c.text or "") for c in ub.find(C("characteristics")).findall(C("characteristic"))}
assert vals == {"Range": '36"', "S": "6", "AP": "4", "Type": "Assault 1, Blast, Pinning, Psychic"}, vals

transport_links = dark_transport.find(C("entryLinks"))
transport_names = sorted((x.get("name") or "") for x in (transport_links.findall(C("entryLink")) if transport_links is not None else []))
expected_transports = sorted(["Rhino", "Drop Pod", "Dreadclaw Drop Pod", "Land Raider"])
assert transport_names == expected_transports, (transport_names, expected_transports)

note("Validation: CAT61/GST29; 35-power general discipline pool attached to Librarian ML1, Librarian Epistolary and Stormseer Epistolary; Unseen Bolt is a real ranged profile.")
note("Dark Sons transport validation: Rhino, Drop Pod, Dreadclaw Drop Pod, Land Raider; transport group hides when Jump Packs are selected.")
Path("inspection-r61-psychic-and-white-scars.txt").write_text("\n".join(REPORT) + "\n", encoding="utf-8")
