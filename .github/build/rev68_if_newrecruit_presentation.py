from pathlib import Path
import xml.etree.ElementTree as ET

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst'); IDX=Path('index.xml'); OUT=Path('inspection-r68-imperial-fists-newrecruit.txt')
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'; INS='http://www.battlescribe.net/schema/dataIndexSchema'
ET.register_namespace('',CNS); ET.register_namespace('',GNS); ET.register_namespace('',INS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'; I=lambda t:f'{{{INS}}}{t}'
ct=ET.parse(CAT); cr=ct.getroot(); gt=ET.parse(GST); gr=gt.getroot(); it=ET.parse(IDX); ir=it.getroot()
if cr.get('revision')!='67' or gr.get('revision')!='35': raise RuntimeError(f'Expected Rev67/35, got {cr.get("revision")}/{gr.get("revision")}')

def byid(i): return next((e for e in cr.iter() if e.get('id')==i),None)
def ensure(p,t,ns=CNS):
    q=f'{{{ns}}}{t}'; x=p.find(q)
    if x is None: x=ET.SubElement(p,q)
    return x
def remove_pred(root,pred):
    for p in list(root.iter()):
        for x in list(p):
            if pred(x): p.remove(x)
def rule(p,i,n,text):
    r=ET.SubElement(ensure(p,'rules'),C('rule'),{'id':i,'name':n,'hidden':'false'})
    ET.SubElement(r,C('description')).text=text
    return r

def set_group_name(uid,gid,name):
    u=byid(uid); g=next((x for x in u.iter(C('selectionEntryGroup')) if x.get('id')==gid),None) if u is not None else None
    if g is not None: g.set('name',name)
    return g

IDS={
 'templar':'r41-unit-vii-0-templar-brethren-squad','warder':'r41-unit-vii-1-phalanx-warder-squad','huscarl':'r41-unit-vii-2-huscarl-terminator-retinue','tarantula':'r41-unit-vii-3-tarantula-sentry-gun-battery','sig':'r41-unit-vii-4-sigismund-first-captain','rann':'r41-unit-vii-5-fafnir-rann','polux':'r41-unit-vii-6-alexis-polux','diaz':'r41-unit-vii-7-camba-diaz','garrius':'r41-unit-vii-8-evander-garrius','dorn':'r41-unit-vii-9-vii-rogal-dorn-the-praetorian-of-terra'}
U={k:byid(v) for k,v in IDS.items()}
if any(v is None for v in U.values()): raise RuntimeError('Missing IF source entry')

# The Rev67 locked-child experiment is valid XML but New Recruit does not show those locked children in the Profile card.
# Remove only those fixed-display groups; preserve all actual options, retinues, constraints and conditional Rite logic.
slugs=('templar','warder','huscarl','tarantula','sigismund','rann','polux','diaz','garrius','dorn')
remove_pred(cr,lambda e:any((e.get('id') or '').startswith(f'r67-if-{s}-fixed') for s in slugs))
remove_pred(cr,lambda e:(e.get('id') or '').startswith('r68-if-'))

# Make the functional retinue selectors unmistakable in the roster editor.
set_group_name(IDS['sig'],'r64-if-sig-retinue','RETINUE — choose up to one (no separate FOC slot)')
set_group_name(IDS['diaz'],'r64-if-diaz-retinue','RETINUE — choose up to one (no separate FOC slot)')
set_group_name(IDS['garrius'],'r64-if-garrius-retinue','RETINUE — choose up to one (no separate FOC slot)')
set_group_name(IDS['dorn'],'r64-if-dorn-retinue','PRIMARCH RETINUE — choose up to one (no separate FOC slot)')

# New Recruit Profile-card summaries. These are intentionally explicit named rules rather than generic locked child entries.
# The actual selectable options remain in their existing groups beneath each unit.
rule(U['templar'],'r68-if-templar-entry','TEMPLAR BRETHREN — UNIT ENTRY','Composition: 4 Templar Brethren and 1 Templar Champion; may include up to 5 additional Brethren. Wargear: Power Armour, Combat Shield, Bolt pistol, Rending Weapon. Special Rules: Legiones Astartes (Imperial Fists), Stubborn, Righteous Zeal. Options: up to five models may exchange Rending Weapons for Power Weapons (+10 each); whole squad may take Frag Grenades (+1/model) and/or Krak Grenades (+2/model); one Legion Vexilla (+10); one other Nuncio-vox (+10). The Champion has up to 50 points of permitted Space Marine Armoury access. Dedicated Transport: Rhino, Drop Pod, Dreadclaw Drop Pod or Land Raider where capacity permits.')
rule(U['warder'],'r68-if-warder-entry','PHALANX WARDERS — UNIT ENTRY','Composition: 4 Phalanx Warders and 1 Warder Sergeant; may include up to 5 additional Warders. Wargear: Power Armour, Boarding Shield, Bolter, Power Weapon. Special Rules: Legiones Astartes (Imperial Fists), Stubborn, Counter-Attack. For every five models, one Warder may replace his Bolter with Flamer (+5), Meltagun (+10) or Plasma gun (+15). Whole squad may take Frag Grenades (+1/model), Krak Grenades (+2/model), and/or Melta Bombs (+5/model). One Legion Vexilla (+10), one other Nuncio-vox (+10). Sergeant has up to 50 points of permitted Armoury access. Dedicated Transport: Rhino, Dreadclaw Drop Pod or Land Raider where capacity permits.')
rule(U['huscarl'],'r68-if-huscarl-entry','HUSCARL TERMINATOR RETINUE — UNIT ENTRY','Retinue only. One Huscarl Terminator Retinue may be selected for Rogal Dorn, Sigismund, or an Imperial Fists Praetor wearing Terminator Armour; it occupies no separate Force Organisation slot. Composition: 4 Huscarls and 1 Huscarl Captain; may include up to 5 additional Huscarls. Wargear: Cataphractii Terminator Armour, Combi-bolter, Power Weapon. Special Rules: Legiones Astartes (Imperial Fists), Stubborn, Retinue. Any Huscarl may exchange his Combi-bolter or Power Weapon for the listed unit options; one model may take a Grenade Harness. The Captain has up to 50 points of permitted Terminator weapons/wargear.')
rule(U['tarantula'],'r68-if-tarantula-entry','TARANTULA SENTRY GUN BATTERY — UNIT ENTRY','Fast Attack, 0–2 Batteries. Composition: 1–3 Tarantula Sentry Guns. Unit Type: Immobile Vehicle. Wargear: Twin-linked Heavy Bolter; any gun may replace it with a Twin-linked Lascannon (+15). Special Rules: Automated Targeting, Firing Mode, Disposable Platform.')

rule(U['sig'],'r68-if-sig-wargear','SIGISMUND — WARGEAR','Artificer Armour; Iron Halo; Terminator Honours; Purity Seals; Bolt pistol; The Black Sword.')
rule(U['sig'],'r68-if-sig-special','SIGISMUND — SPECIAL RULES','Legiones Astartes (Imperial Fists); Independent Character; Master of the Legion; Honour or Death; Kingslayer.')
rule(U['sig'],'r68-if-sig-retinue','SIGISMUND — COMMAND RETINUE','Sigismund may select either a Templar Brethren Squad or Huscarl Terminator Retinue as his retinue. The selected unit does not occupy a separate Force Organisation slot. The functional RETINUE selector is part of Sigismund’s roster entry.')

rule(U['rann'],'r68-if-rann-wargear','FAFNIR RANN — WARGEAR','Artificer Armour; Refractor Field; The Headsman; The Hunter; Frag grenades. Options: Krak grenades (+2) and Melta bombs (+5).')
rule(U['rann'],'r68-if-rann-special','FAFNIR RANN — SPECIAL RULES','Legiones Astartes (Imperial Fists); Independent Character; Master of the Legion; Executioner’s Tax; Lord Seneschal.')

rule(U['polux'],'r68-if-polux-wargear','ALEXIS POLUX — WARGEAR','Power Armour; Vigil Pattern Storm Shield; Terminator Honours; Combi-meltagun; Master-crafted Power Fist; Frag grenades. Option: Krak grenades (+2).')
rule(U['polux'],'r68-if-polux-special','ALEXIS POLUX — SPECIAL RULES','Legiones Astartes (Imperial Fists); Independent Character; Master of the Legion; Stubborn; Teleport Transponder; The Crimson Fist.')

rule(U['diaz'],'r68-if-diaz-wargear','CAMBA DIAZ — WARGEAR','Artificer Armour; Refractor Field; Power Weapon; Bolt pistol; Frag grenades. Options: Krak grenades (+2) and Melta bombs (+5).')
rule(U['diaz'],'r68-if-diaz-special','CAMBA DIAZ — SPECIAL RULES','Legiones Astartes (Imperial Fists); Independent Character; Stubborn; Hold the Line.')
rule(U['diaz'],'r68-if-diaz-retinue','CAMBA DIAZ — COMMAND RETINUE','Diaz may select one Phalanx Warder Squad or Legion Command Squad as his retinue. The selected unit does not occupy a separate Force Organisation slot. The functional RETINUE selector is part of Diaz’s roster entry.')

rule(U['garrius'],'r68-if-garrius-wargear','EVANDER GARRIUS — WARGEAR','Cataphractii Terminator Armour; Subjugator; Volkite Charger; Bionics.')
rule(U['garrius'],'r68-if-garrius-special','EVANDER GARRIUS — SPECIAL RULES','Legiones Astartes (Imperial Fists); Independent Character; Master of the Legion; Fearless; Tyrant of Cthonia.')
rule(U['garrius'],'r68-if-garrius-retinue','EVANDER GARRIUS — COMMAND RETINUE','Garrius may select a Huscarl Terminator Retinue or Legion Terminator Command Squad as his retinue. The selected unit does not occupy a separate Force Organisation slot. The functional RETINUE selector is part of Garrius’s roster entry.')

rule(U['dorn'],'r68-if-dorn-wargear','ROGAL DORN — WARGEAR','Auric Armour; Storm’s Teeth; Voice of Terra; Frag Grenades.')
rule(U['dorn'],'r68-if-dorn-special','ROGAL DORN — SPECIAL RULES','Primarch; Legiones Astartes (Imperial Fists); The Unyielding; Lord Castellan; Master of Defence; This Ground Shall Not Fall.')
rule(U['dorn'],'r68-if-dorn-retinue','ROGAL DORN — PRIMARCH RETINUE','Rogal Dorn may select one Legion Honour Guard Squad, Legion Terminator Command Squad, Huscarl Terminator Retinue, or Templar Brethren Squad as his Primarch Retinue. It occupies no additional Force Organisation selection. A Huscarl Retinue selected for Dorn ignores the normal requirement for the accompanying Character to wear Terminator Armour. The functional PRIMARCH RETINUE selector is part of Dorn’s roster entry.')

# Hard validation for Sigismund: source-summary rules plus two actual retinue options must exist.
sig=U['sig']; rg=next((x for x in sig.findall('./'+C('selectionEntryGroups')+'/'+C('selectionEntryGroup')) if x.get('id')=='r64-if-sig-retinue'),None)
if rg is None: raise RuntimeError('Sigismund retinue group missing')
children=rg.findall('./'+C('selectionEntries')+'/'+C('selectionEntry'))
if {x.get('name') for x in children}!={'Templar Brethren Squad','Huscarl Terminator Retinue'}: raise RuntimeError('Sigismund retinue choices wrong: '+repr([x.get('name') for x in children]))
for rid in ('r68-if-sig-wargear','r68-if-sig-special','r68-if-sig-retinue'):
    if byid(rid) is None: raise RuntimeError('Missing Sigismund display rule '+rid)

# Revisions force New Recruit to fetch the presentation correction.
cr.set('revision','68'); cr.set('gameSystemRevision','36'); gr.set('revision','36')
for e in ir.iter(I('dataIndexEntry')):
    if e.get('filePath')=='Legiones Astartes.cat': e.set('dataRevision','68')
    elif e.get('filePath')=='Prohammer 30k.gst': e.set('dataRevision','36')

# Duplicate ID validation.
for root,label in ((cr,'catalogue'),(gr,'game system')):
    seen=set(); dup=[]
    for e in root.iter():
        i=e.get('id')
        if not i: continue
        if i in seen: dup.append(i)
        seen.add(i)
    if dup: raise RuntimeError(f'Duplicate IDs {label}: {dup[:20]}')

ET.indent(ct,space='  '); ET.indent(gt,space='  '); ET.indent(it,space='  ')
ct.write(CAT,encoding='utf-8',xml_declaration=True); gt.write(GST,encoding='utf-8',xml_declaration=True); it.write(IDX,encoding='utf-8',xml_declaration=True)
ET.parse(CAT); ET.parse(GST); ET.parse(IDX)
OUT.write_text('''Revision 68 — Imperial Fists New Recruit presentation correction\nCatalogue revision: 68\nGame-system revision: 36\n\n- Removed the ineffective Rev67 locked-child display groups.\n- Added explicit New Recruit-visible unit-entry rules for fixed wargear, special rules, options/retinue summaries.\n- Sigismund now has explicit Wargear, Special Rules and Command Retinue rule blocks.\n- Sigismund's functional retinue selector is retained and verified to contain Templar Brethren Squad and Huscarl Terminator Retinue.\n- Diaz, Garrius and Dorn retinue selectors remain functional and are renamed clearly.\n- All Rev66 conditional Rite enforcement and Rev64 functional army options are preserved.\n''',encoding='utf-8')
print(OUT.read_text())
