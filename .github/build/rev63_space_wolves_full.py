from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET

CAT = Path('Legiones Astartes.cat')
GST = Path('Prohammer 30k.gst')
IDX = Path('index.xml')
OUT = Path('inspection-r63-space-wolves-full.txt')

CNS = 'http://www.battlescribe.net/schema/catalogueSchema'
GNS = 'http://www.battlescribe.net/schema/gameSystemSchema'
INS = 'http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('', CNS)
C = lambda t: f'{{{CNS}}}{t}'
G = lambda t: f'{{{GNS}}}{t}'
I = lambda t: f'{{{INS}}}{t}'

ctree = ET.parse(CAT); cr = ctree.getroot()
gtree = ET.parse(GST); gr = gtree.getroot()
itree = ET.parse(IDX); ir = itree.getroot()

def by_id(root, ident):
    return next((e for e in root.iter() if e.get('id') == ident), None)

def ensure(parent, tag, ns=CNS):
    q = f'{{{ns}}}{tag}'
    x = parent.find(q)
    if x is None:
        x = ET.SubElement(parent, q)
    return x

def remove_if(parent, pred):
    for child in list(parent):
        remove_if(child, pred)
        if pred(child):
            parent.remove(child)

def remove_r63(root):
    remove_if(root, lambda e: (e.get('id') or '').startswith('r63-sw-'))

def wipe_child(parent, tag):
    x = parent.find(C(tag))
    if x is not None:
        parent.remove(x)

def set_points(entry, value):
    costs = ensure(entry, 'costs')
    for c in list(costs): costs.remove(c)
    ET.SubElement(costs, C('cost'), {'name':'Points','typeId':'pts','value':str(value)})

def add_constraint(parent, ident, typ, value, field='selections', scope='parent', child=True, automatic=None):
    cs = ensure(parent, 'constraints')
    a = {'id':ident,'type':typ,'value':str(value),'field':field,'scope':scope,'shared':'true',
         'includeChildSelections':'true' if child else 'false','includeChildForces':'false'}
    if automatic is not None: a['automatic'] = 'true' if automatic else 'false'
    return ET.SubElement(cs, C('constraint'), a)

def add_rule(parent, ident, name, text):
    rs = ensure(parent, 'rules')
    r = ET.SubElement(rs, C('rule'), {'id':ident,'name':name,'hidden':'false'})
    ET.SubElement(r, C('description')).text = text
    return r

def add_profile_ranged(parent, ident, name, rng, strength, ap, typ):
    ps = ensure(parent, 'profiles')
    p = ET.SubElement(ps, C('profile'), {'id':ident,'name':name,'hidden':'false','typeId':'prof-ranged','typeName':'Ranged Weapon'})
    cs = ET.SubElement(p, C('characteristics'))
    for n,tid,v in [('Range','ranged-range',rng),('S','ranged-s',strength),('AP','ranged-ap',ap),('Type','ranged-type',typ)]:
        ET.SubElement(cs, C('characteristic'), {'name':n,'typeId':tid}).text = str(v)
    return p

def add_model_profile(parent, ident, name, vals):
    ps = ensure(parent, 'profiles')
    p = ET.SubElement(ps, C('profile'), {'id':ident,'name':name,'hidden':'false','typeId':'prof-model','typeName':'Model'})
    cs = ET.SubElement(p, C('characteristics'))
    for n,tid,v in zip(['WS','BS','S','T','W','I','A','Ld','Sv'],['model-ws','model-bs','model-s','model-t','model-w','model-i','model-a','model-ld','model-sv'],vals):
        ET.SubElement(cs, C('characteristic'), {'name':n,'typeId':tid}).text = str(v)
    return p

def selection(parent, ident, name, cost=0, typ='upgrade', maxv=1, default=None):
    ses = ensure(parent, 'selectionEntries')
    a = {'id':ident,'name':name,'type':typ,'hidden':'false','import':'true'}
    if default is not None: a['defaultAmount'] = str(default)
    e = ET.SubElement(ses, C('selectionEntry'), a)
    set_points(e, cost)
    if maxv is not None: add_constraint(e, ident+'-max','max',maxv,child=False)
    return e

def group(parent, ident, name, minv=None, maxv=None):
    gs = ensure(parent, 'selectionEntryGroups')
    g = ET.SubElement(gs, C('selectionEntryGroup'), {'id':ident,'name':name,'hidden':'false','collective':'false','import':'true'})
    if minv is not None: add_constraint(g, ident+'-min','min',minv)
    if maxv is not None: add_constraint(g, ident+'-max','max',maxv)
    return g

def model_counter(unit, ident, label, minv, maxv, per_model):
    e = selection(unit, ident, label, per_model, typ='model', maxv=maxv, default=minv)
    add_constraint(e, ident+'-min','min',minv,child=False,automatic=True)
    return e

def scaled_toggle(parent, ident, name, per_model, model_id, rule_text=None):
    e = selection(parent, ident, name, 0, maxv=1)
    mods = ensure(e, 'modifiers')
    m = ET.SubElement(mods, C('modifier'), {'id':ident+'-costmod','type':'increment','value':str(per_model),'field':'pts'})
    reps = ET.SubElement(m, C('repeats'))
    ET.SubElement(reps, C('repeat'), {'value':'1','repeats':'1','field':'selections','scope':'root-entry','childId':model_id,
        'shared':'true','roundUp':'false','includeChildSelections':'false','includeChildForces':'false'})
    if rule_text: add_rule(e, ident+'-rule', name, rule_text)
    return e

def per_five_group(parent, ident, name, model_id, thresholds):
    g = group(parent, ident, name, maxv=1)
    maxid = ident+'-max'
    mods = ensure(g, 'modifiers')
    for n,t in enumerate(thresholds,1):
        m = ET.SubElement(mods, C('modifier'), {'id':f'{ident}-inc-{n}','type':'increment','value':'1','field':maxid})
        cs = ET.SubElement(m, C('conditions'))
        ET.SubElement(cs, C('condition'), {'type':'atLeast','value':str(t),'field':'selections','scope':'parent','childId':model_id,
            'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return g

def entry_link(parent, ident, name, target, maxv=1, default=None):
    links = ensure(parent, 'entryLinks')
    a = {'id':ident,'name':name,'type':'selectionEntry','targetId':target,'hidden':'false','import':'true'}
    if default is not None: a['defaultAmount'] = str(default)
    l = ET.SubElement(links, C('entryLink'), a)
    if maxv is not None: add_constraint(l, ident+'-max','max',maxv,child=False)
    return l

def hide_if_missing(entry, ident, child_id, scope='roster'):
    mods = ensure(entry, 'modifiers')
    m = ET.SubElement(mods, C('modifier'), {'id':ident,'type':'set','value':'true','field':'hidden'})
    cs = ET.SubElement(m, C('conditions'))
    ET.SubElement(cs, C('condition'), {'type':'lessThan','value':'1','field':'selections','scope':scope,'childId':child_id,
        'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return m

def hide_if_selected(entry, ident, child_id, scope='roster'):
    mods = ensure(entry, 'modifiers')
    m = ET.SubElement(mods, C('modifier'), {'id':ident,'type':'set','value':'true','field':'hidden'})
    cs = ET.SubElement(m, C('conditions'))
    ET.SubElement(cs, C('condition'), {'type':'atLeast','value':'1','field':'selections','scope':scope,'childId':child_id,
        'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
    return m

def hide_over_models(entry, ident, model_id, limit):
    mods = ensure(entry, 'modifiers')
    m = ET.SubElement(mods, C('modifier'), {'id':ident,'type':'set','value':'true','field':'hidden'})
    cs = ET.SubElement(m, C('conditions'))
    ET.SubElement(cs, C('condition'), {'type':'greaterThan','value':str(limit),'field':'selections','scope':'parent','childId':model_id,
        'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

def hide_below_points(entry, ident, points):
    mods = ensure(entry, 'modifiers')
    m = ET.SubElement(mods, C('modifier'), {'id':ident,'type':'set','value':'true','field':'hidden'})
    cs = ET.SubElement(m, C('conditions'))
    ET.SubElement(cs, C('condition'), {'type':'lessThan','value':str(points),'field':'limit::pts','scope':'roster','childId':'model',
        'shared':'true','includeChildSelections':'true','includeChildForces':'false'})

def rewrite_ids(node, prefix):
    elems = list(node.iter())
    mapping = {}
    for e in elems:
        oid = e.get('id')
        if oid: mapping[oid] = prefix + oid
    for e in elems:
        oid = e.get('id')
        if oid: e.set('id', mapping[oid])
        for attr in ('childId','field'):
            v = e.get(attr)
            if v in mapping: e.set(attr, mapping[v])
    return node

def clone_by_id(ident, prefix):
    src = by_id(cr, ident)
    if src is None: raise RuntimeError('Missing clone source '+ident)
    return rewrite_ids(deepcopy(src), prefix)

def clear_local_build(unit):
    # Preserve profiles, categories and existing Legion visibility modifier. Rebuild rules/options/costs.
    for tag in ('rules','entryLinks','selectionEntries','selectionEntryGroups'):
        wipe_child(unit, tag)

def set_primary_category(unit, target, name):
    cats = ensure(unit, 'categoryLinks')
    for c in list(cats): cats.remove(c)
    ET.SubElement(cats, C('categoryLink'), {'id':unit.get('id')+'-cat','name':name,'hidden':'false','targetId':target,'primary':'true'})

def legion_gate(unit):
    # Replace only visibility conditions on the top-level unique entry; preserve unrelated modifiers.
    mods = ensure(unit, 'modifiers')
    for m in list(mods):
        if m.get('field') == 'hidden': mods.remove(m)
    hide_if_missing(unit, 'r63-sw-'+unit.get('id')+'-legion-hide', 'legion-vi')

def dedicated_transport(unit, ident, model_id, choices, max_models=None):
    g = group(unit, ident, 'Dedicated Transport', maxv=1)
    if max_models is not None: hide_over_models(g, ident+'-size-hide', model_id, max_models)
    for key in choices:
        if key == 'rhino': entry_link(g, ident+'-rhino', 'Legion Rhino Armoured Carrier', 'transport-rhino')
        elif key == 'drop': entry_link(g, ident+'-drop', 'Legion Drop Pod', 'transport-drop-pod')
        elif key == 'dreadclaw': entry_link(g, ident+'-dreadclaw', 'Dreadclaw Drop Pod', 'transport-dreadclaw')
        elif key == 'landraider':
            lr = clone_by_id('hs-land-raider', ident+'-lr-')
            lr.set('name','Legion Land Raider')
            cats = lr.find(C('categoryLinks'))
            if cats is not None: lr.remove(cats)
            cons = lr.find(C('constraints'))
            if cons is not None: lr.remove(cons)
            # Convert squadron to one transport.
            for rg in lr.iter(C('rule')):
                if rg.get('name') == 'Squadron Composition':
                    d = rg.find(C('description')); d.text = 'Dedicated Transport: select exactly one Land Raider pattern. Normal Transport Capacity restrictions apply.'
            for pg in lr.iter(C('selectionEntryGroup')):
                if 'Land Raider Patterns' in (pg.get('name') or ''):
                    for c in pg.findall('.//'+C('constraint')):
                        if c.get('type') == 'max': c.set('value','1')
            for pe in lr.iter(C('selectionEntry')):
                if pe.get('type') == 'model':
                    for c in pe.findall('./'+C('constraints')+'/'+C('constraint')):
                        if c.get('type') == 'max': c.set('value','1')
            ensure(g,'selectionEntries').append(lr)
        elif key == 'spartan':
            sp = clone_by_id('hs-spartan', ident+'-sp-')
            sp.set('name','Legion Spartan Assault Tank')
            cats = sp.find(C('categoryLinks'))
            if cats is not None: sp.remove(cats)
            cons = sp.find(C('constraints'))
            if cons is not None: sp.remove(cons)
            ensure(g,'selectionEntries').append(sp)
    return g

def local_option(parent, ident, name, cost, maxv=1, rule=None):
    e = selection(parent, ident, name, cost, maxv=maxv)
    if rule: add_rule(e, ident+'-rule', name, rule)
    return e

def add_shared_sw_gear():
    shared = ensure(cr, 'sharedSelectionEntries')
    data = [
      ('frost','Frost Weapon',20,'Strength: User +1. Power Weapon. May be represented by a sword, axe, claw or similar Fenrisian weapon; appearance has no additional rules effect.'),
      ('frost-exchange','Frost Weapon — exchange an existing Power Weapon',5,'Only a model already equipped with a Power Weapon may select this +5 point exchange. The Power Weapon is replaced by a Frost Weapon: Strength User +1, Power Weapon.'),
      ('great-frost','Great Frost Blade',35,'Strength: User +2. Power Weapon, Two-Handed, Master-crafted. A model using it suffers -1 Initiative during that Assault phase.'),
      ('pelt','Wolf Pelt',5,"When the bearer's unit successfully uses Counter-Attack, the bearer receives +2 Attacks instead of the normal +1 Attack granted by Counter-Attack."),
      ('necklace','Wolf Tooth Necklace',10,'The bearer always hits enemy models on a 3+ in close combat, unless the bearer would normally hit on a better result.'),
      ('talisman','Wolf Tail Talisman',5,'Whenever an enemy psychic power directly affects the bearer or a unit he has joined, after the power is successfully invoked and any normal Deny the Witch attempt is resolved, roll a D6. On a 6, the bearer is unaffected. If joined to a unit, the remainder of the unit is affected normally.'),
      ('runic-armour','Runic Armour',25,'Only a Space Wolves Independent Character wearing Power Armour may select this option. Replace Power Armour with Runic Armour. It grants a 2+ Armour Save and Adamantium Will, and counts as Artificer Armour for all other rules and restrictions.'),
    ]
    targets = {}
    for k,n,cost,txt in data:
        e = ET.SubElement(shared, C('selectionEntry'), {'id':'r63-sw-gear-'+k,'name':n,'type':'upgrade','hidden':'false','import':'true'})
        set_points(e,cost); add_constraint(e,e.get('id')+'-max','max',1,child=False)
        add_rule(e,e.get('id')+'-rule',n,txt)
        hide_if_missing(e,e.get('id')+'-hide','legion-vi')
        targets[k] = e.get('id')
    return targets

def link_sw_character_gear(g, prefix, targets, independent=False):
    for k,label in [('frost','Frost Weapon'),('frost-exchange','Frost Weapon — Power Weapon exchange'),('pelt','Wolf Pelt'),('necklace','Wolf Tooth Necklace'),('talisman','Wolf Tail Talisman')]:
        entry_link(g,prefix+k,label,targets[k])
    if independent:
        entry_link(g,prefix+'great-frost','Great Frost Blade',targets['great-frost'])
        entry_link(g,prefix+'runic-armour','Runic Armour',targets['runic-armour'])

def augment_character_armouries(targets):
    seen = 0
    for g in list(cr.iter(C('selectionEntryGroup'))):
        gid = g.get('id','').lower(); name = (g.get('name') or '').lower()
        if ('sgt-armoury' in gid or 'sergeant armoury' in name or 'champ-arm' in gid or 'champion armoury' in name):
            link_sw_character_gear(g, 'r63-sw-arm-'+str(seen)+'-', targets, independent=False); seen += 1
    for uid in ('hq-praetor','hq-centurion'):
        u = by_id(cr,uid)
        if u is None: raise RuntimeError('Missing '+uid)
        g = group(u,'r63-sw-'+uid+'-armoury','Space Wolves Armoury',maxv=None)
        hide_if_missing(g,g.get('id')+'-hide','legion-vi')
        link_sw_character_gear(g,g.get('id')+'-',targets,independent=True)
    return seen

def champion_armoury(unit, src_id, prefix, name):
    src = by_id(cr, src_id)
    if src is None: raise RuntimeError('Missing armoury source '+src_id)
    cg = rewrite_ids(deepcopy(src), prefix)
    cg.set('name', name)
    ensure(unit,'selectionEntryGroups').append(cg)
    return cg

def wolf_retinue(character, ident):
    e = selection(character,ident,'Fenrisian Wolf Retinue — 2 Wolves',24,maxv=1)
    add_model_profile(e,ident+'-profile','Fenrisian Wolf',['4','0','4','4','1','4','2','8','6+'])
    add_rule(e,ident+'-rule','Wolf Retinue','Two Fenrisian Wolves accompany the Independent Character. This may be selected in addition to any normal Retinue squad or alone. The Wolves may never voluntarily leave the character.')
    hide_if_missing(e,ident+'-hide','legion-vi')
    return e

def retinue_group(character, ident, entries):
    g = group(character,ident,'Retinue',maxv=1)
    for label,srcid,prefix in entries:
        x = clone_by_id(srcid,prefix)
        x.set('name',label)
        cats = x.find(C('categoryLinks'))
        if cats is not None: x.remove(cats)
        # Nested retinues never occupy another FOC slot.
        ensure(g,'selectionEntries').append(x)
    return g

# ---------------------------------------------------------------------------
# Clean previous R63 build and obsolete old Space Wolves armoury placeholders.
# ---------------------------------------------------------------------------
remove_r63(cr); remove_r63(gr)
old_names = {'Frost Weapon','Great Frost Blade','Wolf Pelt','Wolf Tooth Necklace','Wolf Tail Talisman','Runic Armour'}
old_targets = set()
for e in cr.iter(C('selectionEntry')):
    if (e.get('id') or '').startswith('r43-sw-') and (e.get('name') or '').split(' — ')[0] in old_names:
        old_targets.add(e.get('id'))
remove_if(cr, lambda e: (e.tag in (C('selectionEntry'),C('entryLink'))) and (((e.get('id') or '').startswith('r43-sw-') and (e.get('name') or '').split(' — ')[0] in old_names) or e.get('targetId') in old_targets))
# Replace imported placeholder Consuls with the structured implementation below.
remove_if(cr, lambda e: e.tag == C('selectionEntry') and e.get('id') in ('r25-consul-vi-wolf-priest-consul','r25-consul-vi-rune-priest-consul'))

gear = add_shared_sw_gear()
armouries_augmented = augment_character_armouries(gear)

# ---------------------------------------------------------------------------
# Consuls — inside the normal Centurion Consul block.
# ---------------------------------------------------------------------------
consuls = by_id(cr,'hq-centurion-consuls')
if consuls is None: raise RuntimeError('Missing Centurion Consul group')
wp = selection(consuls,'r63-sw-consul-wolf-priest','Wolf Priest Consul',35,maxv=1)
hide_if_missing(wp,'r63-sw-consul-wolf-priest-hide','legion-vi')
add_rule(wp,'r63-sw-wp-replace','Wargear','Replace the Centurion’s Chainsword with a Fang of Morkai. The Wolf Priest also has a Rosarius.')
add_rule(wp,'r63-sw-wp-fang','Fang of Morkai','Counts as a Power Weapon.')
add_rule(wp,'r63-sw-wp-rites','Rites of Battle','The Wolf Priest and any Space Wolves unit he has joined may re-roll failed Morale checks.')
add_rule(wp,'r63-sw-wp-oath','Oath of the Slayer','Before deployment, nominate one enemy unit. The Wolf Priest and any Space Wolves unit he has joined may re-roll failed To Hit rolls in close combat against that nominated unit for the duration of the battle.')

rp = selection(consuls,'r63-sw-consul-rune-priest','Rune Priest Consul',25,maxv=1)
hide_if_missing(rp,'r63-sw-consul-rune-priest-hide','legion-vi')
add_rule(rp,'r63-sw-rp-replace','Wargear','Replace the Centurion’s Chainsword with a Runic Force Weapon. The Rune Priest also has a Wolf Tail Talisman.')
add_rule(rp,'r63-sw-rp-force','Runic Force Weapon','Counts as a Force Weapon.')
add_rule(rp,'r63-sw-rp-psyker','Psyker (Mastery Level 1)','The Rune Priest is a Psyker with Mastery Level 1 and follows the normal ProHammer psychic rules.')
add_rule(rp,'r63-sw-rp-support','Legion Support Officer','May not fulfil the compulsory HQ selection unless another rule specifically permits it.')
add_rule(rp,'r63-sw-rp-winds','Mystic Winds of Fenris','Blessing — the Rune Priest or one friendly Space Wolves unit with at least one model within 6 inches. If the Psychic Test is passed, until the beginning of the next Space Wolves turn the nominated unit receives a 5+ Cover Save. If it already has a Cover Save, improve it by 1, to a maximum of 4+.')
entry_link(rp,'r63-sw-rp-hood','Psychic Hood','gear-hq-hood')
master = selection(rp,'r63-sw-rp-master','Master of Runes — Mastery Level 2',25,maxv=1)
add_rule(master,'r63-sw-rp-master-rule','Master of Runes','The Rune Priest has Psychic Mastery Level 2 and selects one additional psychic power from the disciplines normally available to a Legion Librarian.')
power2 = clone_by_id('r61-librarian-power2','r63-sw-rp-')
ensure(master,'selectionEntryGroups').append(power2)

# ---------------------------------------------------------------------------
# Unique unit rebuilds.
# ---------------------------------------------------------------------------
units = {
 'slayer': by_id(cr,'r41-unit-vi-0-grey-slayer-pack'),
 'stalker': by_id(cr,'r41-unit-vi-1-grey-stalker-pack'),
 'scout': by_id(cr,'r41-unit-vi-2-wolf-scout-squad'),
 'deathsworn': by_id(cr,'r41-unit-vi-3-deathsworn-pack'),
 'jorlund': by_id(cr,'r41-unit-vi-4-jorlund-hunter-pack'),
 'varagyr': by_id(cr,'r41-unit-vi-5-varagyr-wolf-guard-terminators'),
 'wolves': by_id(cr,'r41-unit-vi-6-fenrisian-wolf-pack'),
 'hvarl': by_id(cr,'r41-unit-vi-7-hvarl-red-blade'),
 'geigor': by_id(cr,'r41-unit-vi-8-geigor-fell-hand'),
 'bjorn': by_id(cr,'r41-unit-vi-9-bjorn-the-fell-handed'),
 'ohthere': by_id(cr,'r41-unit-vi-10-ohthere-wyrdmake'),
 'russ': by_id(cr,'r41-unit-vi-11-vi-leman-russ-the-wolf-king'),
}
if any(v is None for v in units.values()): raise RuntimeError('One or more Space Wolves source units are missing')
for u in units.values(): legion_gate(u)

# Grey Slayers
u=units['slayer']; u.set('name','Grey Slayer Pack'); clear_local_build(u); set_primary_category(u,'cat-troops','Troops')
mid='r63-sw-slayer-models'; set_points(u,15); model_counter(u,mid,'Pack Models',5,20,18)
add_rule(u,'r63-sw-slayer-comp','Unit Composition','4 Grey Slayers and 1 Grey Slayer Huscarl; may include up to 15 additional Grey Slayers (maximum 20 models). The Huscarl is a Character.')
add_rule(u,'r63-sw-slayer-wg','Wargear','Power Armour, Bolter and Close-combat weapon.')
add_rule(u,'r63-sw-slayer-trugrit','True Grit','A model armed with a Bolter and Close-combat weapon receives +1 Attack in close combat, but does not receive the normal +1 Attack for charging.')
add_rule(u,'r63-sw-slayer-pack','Pack Assault','If this unit charges an enemy unit that was already engaged by another friendly Space Wolves unit at the start of the Assault phase, every Grey Slayer receives +1 Attack for that Assault phase.')
g=group(u,'r63-sw-slayer-shields','Bolter Replacements — any model',maxv=20); local_option(g,'r63-sw-slayer-shield','Combat Shield',3,maxv=20,rule='Replaces that model’s Bolter.')
g=per_five_group(u,'r63-sw-slayer-ranged','Special Weapons — one per five models',mid,[10,15,20])
for k,n,c in [('flamer','Flamer',5),('melta','Meltagun',10),('plasma','Plasma Gun',15)]: local_option(g,'r63-sw-slayer-'+k,n,c,maxv=4,rule='Replaces one Grey Slayer’s Bolter.')
g=per_five_group(u,'r63-sw-slayer-melee','Melee Weapons — one per five models',mid,[10,15,20])
for k,n,c in [('power','Power Weapon',10),('frost','Frost Blade or Frost Axe',15),('fist','Power Fist',15)]: local_option(g,'r63-sw-slayer-'+k,n,c,maxv=4,rule='Replaces one Grey Slayer’s Close-combat weapon.')
local_option(u,'r63-sw-slayer-vexilla','Legion Vexilla',10); local_option(u,'r63-sw-slayer-nuncio','Nuncio-vox',10)
scaled_toggle(u,'r63-sw-slayer-frag','Frag Grenades — whole pack',1,mid); scaled_toggle(u,'r63-sw-slayer-krak','Krak Grenades — whole pack',2,mid)
champion_armoury(u,'sgt-armoury','r63-sw-slayer-huscarl-','Grey Slayer Huscarl Armoury — up to 50 points')
dedicated_transport(u,'r63-sw-slayer-transport',mid,['rhino','drop','dreadclaw','landraider'],max_models=10)

# Grey Stalkers
u=units['stalker']; u.set('name','Grey Stalker Pack'); clear_local_build(u); set_primary_category(u,'cat-troops','Troops')
mid='r63-sw-stalker-models'; set_points(u,15); model_counter(u,mid,'Pack Models',5,15,17)
add_rule(u,'r63-sw-stalker-comp','Unit Composition','4 Grey Stalkers and 1 Grey Stalker Huscarl; may include up to 10 additional Grey Stalkers (maximum 15 models). The Huscarl is a Character.')
add_rule(u,'r63-sw-stalker-wg','Wargear','Power Armour, Bolter and Close-combat weapon.')
add_rule(u,'r63-sw-stalker-special','Special Rules','Legiones Astartes (Space Wolves), Infiltrate, Move Through Cover, Night Vision.')
g=per_five_group(u,'r63-sw-stalker-ranged','Special Weapons — one per five models',mid,[10,15])
for k,n,c in [('flamer','Flamer',5),('melta','Meltagun',10),('plasma','Plasma Gun',15),('volkite','Volkite Charger',10)]: local_option(g,'r63-sw-stalker-'+k,n,c,maxv=3,rule='Replaces one Grey Stalker’s Bolter.')
local_option(u,'r63-sw-stalker-vexilla','Legion Vexilla',10); local_option(u,'r63-sw-stalker-nuncio','Nuncio-vox',10)
scaled_toggle(u,'r63-sw-stalker-frag','Frag Grenades — whole pack',1,mid); scaled_toggle(u,'r63-sw-stalker-krak','Krak Grenades — whole pack',2,mid)
champion_armoury(u,'sgt-armoury','r63-sw-stalker-huscarl-','Grey Stalker Huscarl Armoury — up to 50 points')
tg=dedicated_transport(u,'r63-sw-stalker-transport',mid,['rhino','drop','dreadclaw'],max_models=10)
add_rule(tg,'r63-sw-stalker-transport-note','Infiltrate and Transport','The unit’s Infiltrate special rule only passes to its Dedicated Transport if the vehicle itself is able to Infiltrate.')

# Wolf Scouts
u=units['scout']; u.set('name','Wolf Scout Squad'); clear_local_build(u); set_primary_category(u,'cat-elites','Elites')
mid='r63-sw-scout-models'; set_points(u,15); model_counter(u,mid,'Squad Models',5,10,14)
add_rule(u,'r63-sw-scout-comp','Unit Composition','4 Wolf Scouts and 1 Wolf Scout Huscarl; may include up to 5 additional Wolf Scouts (maximum 10 models). The Huscarl is a Character.')
add_rule(u,'r63-sw-scout-wg','Wargear','Scout Armour, Bolt pistol and Close-combat weapon.')
add_rule(u,'r63-sw-scout-special','Special Rules','Legiones Astartes (Space Wolves), Infiltrate, Move Through Cover, Behind Enemy Lines.')
add_rule(u,'r63-sw-scout-bel','Behind Enemy Lines','The squad may be placed in Reserve. When it arrives, determine the table edge using the rule in the army list. It may shoot in the turn it arrives but may not charge that turn.')
g=group(u,'r63-sw-scout-basic','Basic Weapon Replacement — any model',maxv=10)
for k,n,c in [('bolter','Bolter',0),('shotgun','Astartes Shotgun',0),('sniper','Sniper Rifle',5)]: local_option(g,'r63-sw-scout-'+k,n,c,maxv=10,rule='Replaces that model’s Bolt pistol and Close-combat weapon.')
g=group(u,'r63-sw-scout-specialweps','Special Weapons — up to two Scouts',maxv=2)
for k,n,c in [('flamer','Flamer',5),('melta','Meltagun',10),('plasma','Plasma Gun',15),('pp','Plasma Pistol',15),('power','Power Weapon',10)]: local_option(g,'r63-sw-scout-special-'+k,n,c,maxv=2)
g=group(u,'r63-sw-scout-heavy','Heavy Weapon — one Scout',maxv=1); local_option(g,'r63-sw-scout-hb','Heavy Bolter',10); local_option(g,'r63-sw-scout-ml','Missile Launcher',15)
scaled_toggle(u,'r63-sw-scout-frag','Frag Grenades — whole squad',1,mid); scaled_toggle(u,'r63-sw-scout-krak','Krak Grenades — whole squad',2,mid); scaled_toggle(u,'r63-sw-scout-melta-bombs','Melta Bombs — whole squad',5,mid)
champion_armoury(u,'sgt-armoury','r63-sw-scout-huscarl-','Wolf Scout Huscarl Armoury — up to 50 points')
dedicated_transport(u,'r63-sw-scout-transport',mid,['rhino'])

# Deathsworn
u=units['deathsworn']; u.set('name','Deathsworn Pack'); clear_local_build(u); set_primary_category(u,'cat-elites','Elites')
mid='r63-sw-deathsworn-models'; set_points(u,25); model_counter(u,mid,'Deathsworn',5,10,30)
add_rule(u,'r63-sw-deathsworn-wg','Wargear','Artificer Armour, Bolt pistol, Power Weapon, Yimira Stasis Bombs and Frag grenades.')
add_rule(u,'r63-sw-deathsworn-dreams','Dreams of Death','A Deathsworn slain before it has attacked in an Assault phase may make its attacks at Initiative 1 if at least one other Deathsworn from the unit remains in play. Remove the slain model after those attacks are resolved.')
add_rule(u,'r63-sw-deathsworn-yimira','Yimira Stasis Bombs','Count as Defensive Grenades. When an enemy unit Retreats from combat with the Deathsworn, roll two dice and use the lower result. One Deathsworn may throw a Yimira Stasis Bomb instead of shooting. Yimira Stasis Bombs have no effect on vehicles.')
g=per_five_group(u,'r63-sw-deathsworn-melee','Power Weapon Replacements — one per five models',mid,[10])
for k,n,c in [('fist','Power Fist',5),('great','Great Frost Blade',10),('hammer','Thunder Hammer',10)]: local_option(g,'r63-sw-deathsworn-'+k,n,c,maxv=2,rule='Replaces one Deathsworn’s Power Weapon.')
scaled_toggle(u,'r63-sw-deathsworn-krak','Krak Grenades — whole pack',2,mid); scaled_toggle(u,'r63-sw-deathsworn-melta','Melta Bombs — whole pack',5,mid)
dedicated_transport(u,'r63-sw-deathsworn-transport',mid,['rhino','dreadclaw','landraider'])

# Jorlund Hunters
u=units['jorlund']; u.set('name','Jorlund Hunter Pack'); clear_local_build(u); set_primary_category(u,'cat-troops','Troops')
mid='r63-sw-jorlund-models'; set_points(u,10); model_counter(u,mid,'Pack Models',5,10,18)
add_rule(u,'r63-sw-jorlund-comp','Unit Composition','4 Jorlund Hunters and 1 Hunt-master; may include up to 5 additional Jorlund Hunters (maximum 10 models). The Hunt-master is a Character.')
add_rule(u,'r63-sw-jorlund-wg','Wargear','Power Armour, Hand flamer, Chainsword and Frag grenades.')
add_rule(u,'r63-sw-jorlund-tempest','Scouring Tempest','Once per battle, declare Scouring Tempest before this unit shoots. During that Shooting phase, the unit may re-roll failed To Wound rolls made with Hand Flamers and Flamers.')
g=per_five_group(u,'r63-sw-jorlund-ranged','Flame Weapon Replacements — one per five models',mid,[10]); local_option(g,'r63-sw-jorlund-flamer','Flamer',5,maxv=2); local_option(g,'r63-sw-jorlund-volkite','Volkite Serpenta',5,maxv=2)
local_option(u,'r63-sw-jorlund-vexilla','Legion Vexilla',10); scaled_toggle(u,'r63-sw-jorlund-krak','Krak Grenades — whole pack',2,mid)
champion_armoury(u,'sgt-armoury','r63-sw-jorlund-huntmaster-','Hunt-master Armoury — up to 50 points')
dedicated_transport(u,'r63-sw-jorlund-transport',mid,['rhino','drop','dreadclaw'])

# Varagyr
u=units['varagyr']; u.set('name','Varagyr Wolf Guard Terminator Pack'); clear_local_build(u); set_primary_category(u,'cat-elites','Elites')
mid='r63-sw-varagyr-models'; set_points(u,25); model_counter(u,mid,'Varagyr',5,10,45)
add_rule(u,'r63-sw-varagyr-wg','Wargear','Cataphractii Terminator Armour, Combi-bolter, and a Frost Blade or Frost Axe.')
add_rule(u,'r63-sw-varagyr-special','Special Rules','Legiones Astartes (Space Wolves), Fearless, Glory Seekers, Chosen of Jarl.')
add_rule(u,'r63-sw-varagyr-glory','Glory Seekers','At the start of an Assault phase, if the unit is engaged with one or more enemy Independent Characters, nominate one. Every Varagyr able to attack the nominated character must do so, and each Varagyr may re-roll one failed To Hit roll against that character in that Assault phase.')
add_rule(u,'r63-sw-varagyr-chosen','Chosen of Jarl','A Space Wolves Praetor wearing Terminator Armour may take one Varagyr Wolf Guard Terminator Pack instead of a Legion Terminator Command Squad. The pack occupies no separate Force Organisation slot and the Praetor and pack count as a single HQ choice.')
g=group(u,'r63-sw-varagyr-ranged','Combi-bolter Replacements — any model',maxv=10)
for k,n,c in [('foe','Foeblaster Boltgun',5),('flamer','Combi-flamer',10),('volkite','Combi-volkite charger',10),('melta','Combi-meltagun',15),('plasma','Combi-plasma',15)]: local_option(g,'r63-sw-varagyr-'+k,n,c,maxv=10,rule='Replaces that model’s Combi-bolter.')
g=group(u,'r63-sw-varagyr-melee','Frost Weapon Replacements — any model',maxv=10)
for k,n,c in [('fist','Power Fist',5),('chain','Chainfist',10),('hammer','Thunder Hammer',10)]: local_option(g,'r63-sw-varagyr-melee-'+k,n,c,maxv=10,rule='Replaces that model’s Frost Blade or Frost Axe.')
g=per_five_group(u,'r63-sw-varagyr-heavy','Heavy Weapons — one per five models',mid,[10])
for k,n,c in [('hf','Heavy Flamer',10),('reaper','Reaper Autocannon',15),('assault','Assault Cannon',20)]: local_option(g,'r63-sw-varagyr-heavy-'+k,n,c,maxv=2,rule='Replaces one Varagyr’s Combi-bolter.')
thegn=local_option(u,'r63-sw-varagyr-thegn','Upgrade one Varagyr to a Thegn',25,maxv=1,rule='The Thegn uses the Thegn profile in this entry.')
local_option(thegn,'r63-sw-varagyr-harness','Grenade Harness',10,maxv=1)
champion_armoury(thegn,'terminator-sgt-armoury','r63-sw-varagyr-thegn-arm-','Thegn Terminator Armoury — up to 50 points')
dedicated_transport(u,'r63-sw-varagyr-transport',mid,['landraider','dreadclaw','spartan'])

# Fenrisian Wolves
u=units['wolves']; u.set('name','Fenrisian Wolf Pack'); clear_local_build(u); set_primary_category(u,'cat-fast','Fast Attack')
mid='r63-sw-wolves-models'; set_points(u,0); model_counter(u,mid,'Fenrisian Wolves',5,10,12)
add_rule(u,'r63-sw-wolves-type','Unit Type','Cavalry.')
add_rule(u,'r63-sw-wolves-pack','Pack Hunters','The pack must declare a charge if it is legally able to do so. If it wins a close combat and the enemy Retreats, the pack must Pursue whenever it is able.')
add_rule(u,'r63-sw-wolves-retinue-note','Wolf Retinue','In addition to this Fast Attack pack, eligible Space Wolves Independent Characters may select a separate retinue of exactly two Fenrisian Wolves for +24 points. Those Wolves may be taken in addition to another Retinue and may never voluntarily leave the character.')

# ---------------------------------------------------------------------------
# Named characters.
# ---------------------------------------------------------------------------
# Hvarl
u=units['hvarl']; u.set('name','Hvarl Red-Blade'); clear_local_build(u); set_primary_category(u,'cat-hq','HQ'); set_points(u,195)
add_rule(u,'r63-sw-hvarl-wg','Wargear','Terminator Armour, Iron Halo, Heavy Bolter and the Red-Blade.')
add_rule(u,'r63-sw-hvarl-special','Special Rules','Legiones Astartes (Space Wolves), Independent Character, Master of the Legion, Headsman.')
add_rule(u,'r63-sw-hvarl-redblade','Red-Blade','Two-Handed Power Weapon. The bearer has +2 Strength and suffers -1 Initiative while using it.')
add_rule(u,'r63-sw-hvarl-headsman','Headsman','At the start of an Assault phase, if Hvarl is engaged with one or more enemy Independent Characters, nominate one. Hvarl must attack that character if able and may re-roll failed To Wound rolls against enemy Independent Characters.')
hide_below_points(u,'r63-sw-hvarl-1500',1500)
# Add retinue after top-level Varagyr has been rebuilt.
retinue_group(u,'r63-sw-hvarl-retinue',[('Legion Terminator Command Squad','hq-praetor-ret-termcommand','r63-sw-hvarl-term-'),('Varagyr Wolf Guard Terminator Pack',units['varagyr'].get('id'),'r63-sw-hvarl-varagyr-')])
wolf_retinue(u,'r63-sw-hvarl-wolves')

# Geigor
u=units['geigor']; u.set('name','Geigor Fell-Hand'); clear_local_build(u); set_primary_category(u,'cat-hq','HQ'); set_points(u,145)
add_rule(u,'r63-sw-geigor-wg','Wargear','Artificer Armour, Refractor Field, Bolter, Bolt pistol, The Fell-Hand and Frag grenades.')
add_rule(u,'r63-sw-geigor-special','Special Rules','Legiones Astartes (Space Wolves), Independent Character, Preferred Enemy (Independent Characters).')
add_rule(u,'r63-sw-geigor-fellhand','The Fell-Hand','Master-crafted Lightning Claw. The bearer receives +1 Strength when using it.')
local_option(u,'r63-sw-geigor-krak','Krak Grenades',2)
wolf_retinue(u,'r63-sw-geigor-wolves')

# Bjorn
u=units['bjorn']; u.set('name','Björn the Fell-Handed'); clear_local_build(u); set_primary_category(u,'cat-hq','HQ'); set_points(u,190)
add_rule(u,'r63-sw-bjorn-type','Unit Type','Vehicle (Walker).')
add_rule(u,'r63-sw-bjorn-wg','Wargear','Assault Cannon; Dreadnought Close Combat Weapon with built-in Heavy Flamer; Smoke Launchers; Searchlight.')
add_rule(u,'r63-sw-bjorn-old','Old and Wise','If the mission uses a roll to determine who takes the first turn, a Space Wolves army containing Björn may re-roll that roll once. The second result stands.')
add_rule(u,'r63-sw-bjorn-hard','Hard to Kill','Whenever a Glancing or Penetrating hit against Björn is rolled on the Vehicle Damage table, the Space Wolves player may force the opponent to re-roll that Damage result. The second result stands.')

# Ohthere
u=units['ohthere']; u.set('name','Ohthere Wyrdmake'); clear_local_build(u); set_primary_category(u,'cat-hq','HQ'); set_points(u,150)
add_rule(u,'r63-sw-ohthere-wg','Wargear','Runic Armour, Bolt pistol, Runic Staff and Frag grenades.')
add_rule(u,'r63-sw-ohthere-special','Special Rules','Legiones Astartes (Space Wolves), Independent Character, Psyker (Mastery Level 2), Legion Support Officer.')
add_rule(u,'r63-sw-ohthere-staff','Runic Staff','Counts as a Force Weapon and a Psychic Hood.')
add_rule(u,'r63-sw-ohthere-winds','Mystic Winds of Fenris','Blessing — Ohthere or one friendly Space Wolves unit with at least one model within 6 inches. On a successful Psychic Test, the nominated unit receives a 5+ Cover Save until the beginning of the next Space Wolves turn; improve an existing Cover Save by 1, to a maximum of 4+.')
add_profile_ranged(u,'r63-sw-ohthere-lightning-profile','Living Lightning','24"','5','4','Assault D6, Witchfire')
add_rule(u,'r63-sw-ohthere-lightning-rule','Living Lightning','Psychic Shooting Power. Resolve a successful manifestation using the Living Lightning weapon profile.')
local_option(u,'r63-sw-ohthere-krak','Krak Grenades',2)
retinue_group(u,'r63-sw-ohthere-retinue',[('Legion Command Squad','hq-centurion-ret-command','r63-sw-ohthere-command-')])
wolf_retinue(u,'r63-sw-ohthere-wolves')

# Leman Russ
u=units['russ']; u.set('name','Leman Russ — The Wolf King'); clear_local_build(u); set_primary_category(u,'cat-low','Lords of War'); set_points(u,510)
add_rule(u,'r63-sw-russ-comp','Unit Composition','Leman Russ, Freki and Geri. Freki and Geri are part of Russ’s unit for the entire battle.')
add_rule(u,'r63-sw-russ-wg','Wargear','Armour Elavagar, Scornspitter, Frag grenades, and one of: Mjalnar Sword of Balenight, Axe of Helwinter, or Krakenmaw. Freki and Geri have Rending Claws and Fangs.')
add_rule(u,'r63-sw-russ-special','Special Rules','Primarch, Legiones Astartes (Space Wolves), Emperor’s Executioner, Preternatural Senses, Wolf King, Bring Me the Traitor. Freki and Geri are Fearless and use Wolves of the Wolf King; Freki is the Fierce and Geri is the Cunning.')
add_rule(u,'r63-sw-russ-armour','Armour Elavagar','Counts as Primarch Armour. Whenever a successfully invoked enemy psychic power directly affects Russ, after the normal Deny attempt is resolved, roll a D6. On a 5+, Russ is unaffected by that power.')
add_profile_ranged(u,'r63-sw-russ-scorn-profile','Scornspitter','12"','4','3','Assault 3, Rending')
wg=group(u,'r63-sw-russ-weapon-choice','The Wolf King’s Weapon — select one',minv=1,maxv=1)
local_option(wg,'r63-sw-russ-mjalnar','Mjalnar Sword of Balenight',0,rule='Power Weapon; +1 Strength; Master-crafted; Shred.')
local_option(wg,'r63-sw-russ-helwinter','Axe of Helwinter',0,rule='Power Weapon; +2 Strength; Armourbane.')
local_option(wg,'r63-sw-russ-krakenmaw','Krakenmaw',0,rule='Two-Handed Power Weapon; +2 Strength; Shred; Rending.')
add_rule(u,'r63-sw-russ-claws','Rending Claws and Fangs','Freki and Geri count their Claws and Fangs as a single Close-combat weapon with Rending.')
add_rule(u,'r63-sw-russ-executioner','Emperor’s Executioner','Before deployment, nominate one enemy Primarch, Independent Character or Monstrous Creature as Russ’s Prey. Russ re-rolls To Hit rolls of 1 and To Wound rolls of 1 against his Prey.')
add_rule(u,'r63-sw-russ-senses','Preternatural Senses','Russ has Night Vision. Enemy Infiltrators may never deploy within 18 inches of Russ or a unit he has joined, regardless of line of sight.')
add_rule(u,'r63-sw-russ-wolfking','Wolf King','Friendly Space Wolves units within 12 inches of Russ may re-roll failed Break tests and failed Leadership tests made for Counter-Attack. The second result stands.')
add_rule(u,'r63-sw-russ-traitor','Bring Me the Traitor','If Russ’s Prey is within 12 inches at the start of the Space Wolves Movement phase, Russ may make an additional D6 inch move towards the Prey before moving normally. This bonus move must end closer to the Prey.')
add_rule(u,'r63-sw-russ-wolves','Wolves of the Wolf King','Freki and Geri always remain with Russ. They do not prevent Russ from joining or leaving another unit. Each Wolf counts as two models for Transport Capacity and both accompany any Retinue taken by Russ.')
add_rule(u,'r63-sw-russ-freki','Freki the Fierce','When Freki charges, he receives +1 Attack in addition to the normal charging bonus.')
add_rule(u,'r63-sw-russ-geri','Geri the Cunning','When Geri attacks an Independent Character or Monstrous Creature, in each Assault phase he may re-roll either one failed To Hit roll or one failed To Wound roll.')
hide_if_missing(u,'r63-sw-russ-loyalist-hide','allegiance-loyalist')
retinue_group(u,'r63-sw-russ-retinue',[('Legion Honour Guard Squad','hq-praetor-ret-honour','r63-sw-russ-honour-'),('Legion Terminator Command Squad','hq-praetor-ret-termcommand','r63-sw-russ-term-')])

# Generic Independent Characters may take two Wolves in addition to normal retinues.
for cid in ('hq-praetor','hq-centurion'):
    wolf_retinue(by_id(cr,cid),'r63-sw-'+cid+'-wolves')

# ---------------------------------------------------------------------------
# Rite of War mechanical enforcement that the catalogue can safely model.
# ---------------------------------------------------------------------------
PALE='r25-rite-vi-0-the-pale-hunters'; BLOOD='r25-rite-vi-1-the-bloodied-claws'
# Pale Hunters forbids Artillery Tank Squadrons, Rapiers, Drop Pods, Dreadnought Drop Pods and Dreadclaws.
for tid in ('hs-artillery','rapier-unit'):
    t=by_id(cr,tid)
    if t is not None: hide_if_selected(t,'r63-sw-pale-hide-'+tid,PALE)
for tid in ('transport-drop-pod','transport-dreadnought-pod','transport-dreadclaw'):
    t=by_id(cr,tid)
    if t is not None: hide_if_selected(t,'r63-sw-pale-hide-'+tid,PALE)
# Bloodied Claws forbids Artillery units and Immobile units. Current structured catalogue targets are the artillery entries and static Drop Pod patterns.
for tid in ('hs-artillery','rapier-unit'):
    t=by_id(cr,tid)
    if t is not None: hide_if_selected(t,'r63-sw-blood-hide-'+tid,BLOOD)
for tid in ('transport-drop-pod','transport-dreadnought-pod'):
    t=by_id(cr,tid)
    if t is not None: hide_if_selected(t,'r63-sw-blood-hide-'+tid,BLOOD)

# Hidden category + force minimum enforces at least one Grey Slayer under The Bloodied Claws.
cat_entries = ensure(gr,'categoryEntries',GNS)
ET.SubElement(cat_entries,G('categoryEntry'),{'id':'r63-sw-cat-grey-slayer','name':'Space Wolves Grey Slayer Requirement','hidden':'true'})
force = by_id(gr,'force-standard')
if force is None: raise RuntimeError('Missing standard force entry')
flinks = ensure(force,'categoryLinks',GNS)
fl = ET.SubElement(flinks,G('categoryLink'),{'id':'r63-sw-fl-grey-slayer','name':'Grey Slayer Requirement','hidden':'true','targetId':'r63-sw-cat-grey-slayer'})
cs=ET.SubElement(fl,G('constraints')); ET.SubElement(cs,G('constraint'),{'id':'r63-sw-grey-slayer-min','type':'min','value':'0','field':'selections','scope':'parent','shared':'true','includeChildSelections':'false','includeChildForces':'false'})
mods=ET.SubElement(fl,G('modifiers')); m=ET.SubElement(mods,G('modifier'),{'id':'r63-sw-grey-slayer-min-mod','type':'set','value':'1','field':'r63-sw-grey-slayer-min'}); conds=ET.SubElement(m,G('conditions')); ET.SubElement(conds,G('condition'),{'type':'atLeast','value':'1','field':'selections','scope':'roster','childId':BLOOD,'shared':'true','includeChildSelections':'true','includeChildForces':'false'})
slcats=ensure(units['slayer'],'categoryLinks'); ET.SubElement(slcats,C('categoryLink'),{'id':'r63-sw-grey-slayer-required','name':'Grey Slayer Requirement','hidden':'true','targetId':'r63-sw-cat-grey-slayer','primary':'false'})

# ---------------------------------------------------------------------------
# Revision bump and validations.
# ---------------------------------------------------------------------------
cr.set('revision','63'); gr.set('revision','31')
for e in ir.iter(I('dataIndexEntry')):
    fp=e.get('filePath')
    if fp=='Legiones Astartes.cat': e.set('dataRevision','63')
    if fp=='Prohammer 30k.gst': e.set('dataRevision','31')

# Duplicate IDs within each data file are invalid.
def duplicate_ids(root):
    seen=set(); d=[]
    for e in root.iter():
        i=e.get('id')
        if not i: continue
        if i in seen: d.append(i)
        seen.add(i)
    return d
for root,label in ((cr,'catalogue'),(gr,'game system')):
    d=duplicate_ids(root)
    if d: raise RuntimeError(f'Duplicate IDs in {label}: {d[:20]}')

# Essential source implementation checks.
expected_sizes={
 'slayer':(5,20),'stalker':(5,15),'scout':(5,10),'deathsworn':(5,10),'jorlund':(5,10),'varagyr':(5,10),'wolves':(5,10)
}
for key,(mn,mx) in expected_sizes.items():
    u=units[key]
    counters=[e for e in u.findall('.//'+C('selectionEntry')) if e.get('type')=='model' and (e.get('id') or '').startswith('r63-sw-')]
    if not counters: raise RuntimeError('Missing model counter '+key)
    e=counters[0]
    vals={c.get('type'):float(c.get('value')) for c in e.findall('./'+C('constraints')+'/'+C('constraint'))}
    if vals.get('min')!=mn or vals.get('max')!=mx: raise RuntimeError(f'Bad size {key}: {vals}')

# Dedicated Transport exact presence check for the six units.
def transport_names(unit):
    out=[]
    for g in unit.iter(C('selectionEntryGroup')):
        if g.get('name')=='Dedicated Transport':
            for l in g.iter(C('entryLink')): out.append(l.get('name'))
            for e in g.findall('./'+C('selectionEntries')+'/'+C('selectionEntry')): out.append(e.get('name'))
    return out
transport_expect={
 'slayer':{'Legion Rhino Armoured Carrier','Legion Drop Pod','Dreadclaw Drop Pod','Legion Land Raider'},
 'stalker':{'Legion Rhino Armoured Carrier','Legion Drop Pod','Dreadclaw Drop Pod'},
 'scout':{'Legion Rhino Armoured Carrier'},
 'deathsworn':{'Legion Rhino Armoured Carrier','Dreadclaw Drop Pod','Legion Land Raider'},
 'jorlund':{'Legion Rhino Armoured Carrier','Legion Drop Pod','Dreadclaw Drop Pod'},
 'varagyr':{'Legion Land Raider','Dreadclaw Drop Pod','Legion Spartan Assault Tank'},
}
for k,ex in transport_expect.items():
    got=set(transport_names(units[k]))
    if got!=ex: raise RuntimeError(f'Transport mismatch {k}: got {got}, expected {ex}')

# Final XML parse before write, then write inspection.
ET.indent(ctree, space='  '); ET.indent(gtree, space='  '); ET.indent(itree, space='  ')
ctree.write(CAT,encoding='utf-8',xml_declaration=True)
gtree.write(GST,encoding='utf-8',xml_declaration=True)
itree.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT); ET.parse(GST); ET.parse(IDX)

lines=[
 'Revision 63 — Space Wolves full-army implementation',
 'Catalogue revision: 63',
 'Game-system revision: 31',
 f'Character armoury groups augmented with Space Wolves wargear: {armouries_augmented}',
 '', 'Unique units and exact size ranges:'
]
for k,(mn,mx) in expected_sizes.items(): lines.append(f'- {units[k].get("name")}: {mn}–{mx}')
lines += ['', 'Dedicated Transport audit:']
for k in transport_expect: lines.append(f'- {units[k].get("name")}: ' + ', '.join(sorted(transport_names(units[k]))))
lines += [
 '', 'Consuls: Wolf Priest and Rune Priest are inside the normal Centurion Consul group.',
 'Rune Priest Master of Runes reuses the normal Librarian additional-power picker.',
 'Ohthere Living Lightning is represented as a ranged Psychic/Witchfire profile.',
 'Hvarl is hidden below a 1,500-point roster limit.',
 'Leman Russ is hidden unless Loyalist allegiance is selected.',
 'Pale Hunters: Heavy Support max remains enforced by the existing game-system rule; prohibited artillery and Drop Pod targets are hidden.',
 'Bloodied Claws: Grey Slayer minimum is enforced through a hidden category; structured Artillery and Immobile Drop Pod targets are hidden.',
 'Bloodied Claws restrictions involving Slow and Purposeful, Fortifications, and Allied Legion detachments remain stated by the Rite itself where the current catalogue has no safe universal tag to enforce them.',
 'Permanent unit-size audit is run by the workflow after this script.'
]
OUT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines))
