import xml.etree.ElementTree as ET
import unicodedata
from pathlib import Path
import re,json,html

WORDNUM={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}

def clean_md(s):
    s=s.replace('\\+','+').replace('\\-','-').replace('\\!','!').replace('\\.','.')
    s=s.replace('**','').replace('*','')
    s=re.sub(r'^#+\s*','',s)
    s=s.replace('  ',' ')
    s=re.sub(r'\s+',' ',s).strip()
    return s

def plain_block(lines):
    out=[]
    for l in lines:
        s=l.strip()
        if not s: continue
        if s.startswith('|'):
            # skip table separators, retain box table text rows excluding profile tables handled separately
            if re.match(r'^\|\s*:?-+',s): continue
            cells=[clean_md(c.strip()) for c in s.strip('|').split('|')]
            if all(not c or re.fullmatch(r':?-+:?',c) for c in cells): continue
            # profile table rows tend numeric, skip if header stats
            if cells and any(c in {'WS','BS','Front','Side','Rear','S','T','W','I','A','Ld','Sv','SP'} for c in cells):
                continue
            txt=' | '.join(c for c in cells if c)
            if txt: out.append(txt)
            continue
        s=clean_md(s)
        s=re.sub(r'^[•\-]+\s*','• ',s)
        if s: out.append(s)
    return '\n'.join(out)

def profile_table(block):
    # find first markdown table whose header contains WS/BS stats
    for i,l in enumerate(block):
        if not l.strip().startswith('|'): continue
        cells=[clean_md(c.strip()) for c in l.strip().strip('|').split('|')]
        if not (('WS' in cells or 'Ws' in cells or 'BS' in cells or 'Bs' in cells) and ('Sv' in cells or 'Front' in cells)):
            continue
        # separator next
        if i+1>=len(block) or not block[i+1].strip().startswith('|'): continue
        headers=[c.upper() if c.lower() in {'ws','bs','s','t','w','i','a','ld','sv','sp'} else c for c in cells]
        rows=[]
        j=i+2
        while j<len(block) and block[j].strip().startswith('|'):
            rc=[clean_md(c.strip()) for c in block[j].strip().strip('|').split('|')]
            if len(rc)>=len(headers) and not all(re.fullmatch(r':?-+:?',x) or not x for x in rc):
                rows.append(rc[:len(headers)])
            j+=1
        return headers,rows
    return None,[]

def parse_base_count(block):
    # after Unit Composition heading until next bold heading
    for i,l in enumerate(block):
        if 'Unit Composition' in clean_md(l):
            total=0
            for x in block[i+1:i+12]:
                s=clean_md(x)
                if s.startswith(('Unit Type','Wargear','Special Rules','Force Organisation','OPTIONS','Options')): break
                m=re.search(r'[•\-]?\s*(\d+)\s+',s)
                if m: total+=int(m.group(1))
                else:
                    m=re.search(r'(\d+)\s*[–-]\s*(\d+)\s+',s)
                    if m: total+=int(m.group(1))
            if total: return total
    return 1

def title_cost(line):
    t=clean_md(line.strip().strip('*'))
    # support dual-cost titles but use first listed/base price
    m=re.match(r'(.+?)\s*[—-]\s*(\+)?\s*([0-9,]+)(?:\s*POINTS?|\s*POINT)?',t,re.I)
    if not m: return t,None,False
    return m.group(1).strip(),int(m.group(3).replace(',','')),bool(m.group(2))

def infer_foc(block,title):
    txt='\n'.join(block)
    # nearby line after Force Organisation
    for i,l in enumerate(block):
        if 'Force Organisation' in clean_md(l):
            for x in block[i+1:i+20]:
                s=clean_md(x).lower()
                # Only treat short bullet/label lines as the FOC value; boxed rule text may mention HQ/retinue etc.
                if len(s)>60: continue
                s2=s.lstrip('•- ').strip()
                if s2=='hq': return 'HQ'
                if s2.startswith('troops'): return 'Troops'
                if s2.startswith('elites'): return 'Elites'
                if s2.startswith('fast attack'): return 'Fast Attack'
                if s2.startswith('heavy support'): return 'Heavy Support'
                if s2.startswith('lords of war') or s2.startswith('lord of war'): return 'Lords of War'
                if s2.startswith('retinue'): return 'Retinue'
    if re.search(r'may be selected as an HQ choice',txt,re.I): return 'HQ'
    if 'Primarch' in txt[:1400] or re.match(r'^(?:[IVXLCDM]+\s*[—-]\s*)?(?:LION|FULGRIM|PERTURABO|JAGHATAI|LEMAN RUSS|ROGAL DORN|KONRAD CURZE|SANGUINIUS|FERRUS MANUS|ANGRON|ROBOUTE GUILLIMAN|MORTARION|MAGNUS|HORUS|LORGAR|VULKAN|CORVUS CORAX|ALPHARIUS)',title,re.I): return 'Lords of War'
    # semantic defaults
    if re.search(r'CAPTAIN|KHAN|LORD|PRIEST|FORGEFATHER|TARVITZ|LUCIUS|BILE|DREYGUR|GOLG|VHALEN|FORRIX|KROEGER|HVARL|GEIGOR|WYRDMAKE|SIGISMUND|RANN|POLUX|DIAZ|GARRIUS|SEVATAR|OPHION|MALCHARION|SHANG|LLANSAHAI|RALDORON|ZEPHON|CROHNE|AMIT|MEDUSON|AUTEK|SANTAR|KHÂRN|DARR|SURLAK|KARGOS|EHRLEN|DELVARUS|GAGE|VENTANUS|PRAYTO|TYPHON|MORTURG|RASK|GRULGOR|GARRO|AHRIMAN|PHOSIS|AMON|MAAT|SANAKHT|ABADDON|AXIMAND|LOKEN|MALOGHURST|MARR|ASHURHADDON|TORGADDON|ARGEL TAL|EREBUS|KOR PHAERON|LAYAK|BELOTH|NUMEON|RHY.TAN|JURR|T.KELL|NEX|MAUN|NEV|SHARROWKYN|DYNAT|EXODUS|SKORR|PECH|HERZOG|RANKO|QIN XA',title,re.I): return 'HQ'
    if 'SUN KILLER' in title: return 'Heavy Support'
    if 'FALCON' in title: return 'Fast Attack'
    if 'MHARA GAL' in title: return 'Elites'
    # Most remaining single named-character entries omit an explicit Force Organisation line but are HQ choices.
    if re.search(r'Unit Composition.*?[•\-]\s*1\s+', txt, re.I|re.S) and not re.search(r'SQUAD|PACK|COHORT|MANIPLE|SQUADRON|BATTERY|RETINUE|GUARD|OPERATIVES|CABAL', title, re.I):
        return 'HQ'
    return 'Elites'

def allegiance(block):
    t='\n'.join(clean_md(x).upper() for x in block)
    if re.search(r'LOYALIST ONLY|LOYALIST ARM(?:Y|IES) ONLY|MAY ONLY BE SELECTED[^\n]{0,100}LOYALIST|ONLY BE INCLUDED[^\n]{0,100}LOYALIST', t): return 'Loyalist'
    if re.search(r'TRAITOR ONLY|TRAITOR ARM(?:Y|IES) ONLY|MAY ONLY BE SELECTED[^\n]{0,100}TRAITOR|ONLY BE INCLUDED[^\n]{0,100}TRAITOR', t): return 'Traitor'
    return None

def extra_models(block):
    txt=' '.join(clean_md(x) for x in block)
    # various phrasing
    m=re.search(r'(?:squad|squadron|pack|cohort|maniple|unit|cabal|detachment|battery) may include up to (\w+) additional .{0,80}?for \+([0-9]+) points per model',txt,re.I)
    if not m:
        m=re.search(r'may include up to (\w+) additional .{0,80}?for \+([0-9]+) points per model',txt,re.I)
    if m:
        n=WORDNUM.get(m.group(1).lower(), int(m.group(1)) if m.group(1).isdigit() else None)
        return {'max':n,'cost':int(m.group(2))} if n else None
    return None

def options_text(block):
    # everything from OPTIONS to before a clearly later named rules box is difficult; just collect price-bearing lines plus transport/restriction context
    out=[]
    active=False
    for l in block:
        s=clean_md(l)
        if s.upper()=='OPTIONS' or s.startswith('OPTIONS '): active=True; continue
        if active:
            # stop at main narrative headers if not option-relevant
            if s.startswith(('DEDICATED TRANSPORT','Transport Vehicle','Transport:','RESTRICTIONS','Restrictions:')):
                out.append(s); continue
            if s and (s.startswith('•') or s.startswith('-') or '+' in s or 'Free' in s or 'may ' in s.lower() or 'replace' in s.lower() or 'take' in s.lower() or 'select' in s.lower()):
                out.append(s)
    return '\n'.join(out)

def simple_options(block,base_count,extra):
    # Parse option price lines, with context from preceding non-price line. Dedup by (name,cost)
    opts=[]; context=''; in_options=False
    max_models=base_count+(extra['max'] if extra else 0)
    for l in block:
        s=clean_md(l)
        if s.upper()=='OPTIONS' or s.startswith('OPTIONS '):
            in_options=True; context=''; continue
        if not in_options: continue
        # retain context lead lines
        if re.search(r'\bmay\b|replace|entire|for every|one model|any model|up to',s,re.I) and not re.search(r'[+-]\s*\d+\s*points|\bFree\b',s,re.I):
            context=s
        m=re.search(r'^(?:•\s*)?(?:-\s*)?(.+?)(?:\.{2,}|\s{2,}|\s)\s*([+-])\s*([0-9]+)\s*points?(.*)$',s,re.I)
        free=False
        if not m:
            mf=re.search(r'^(?:•\s*)?(?:-\s*)?(.+?)(?:\.{2,}|\s{2,}|\s)\s*Free\s*$',s,re.I)
            if mf:
                name=mf.group(1).strip(); cost=0; tail=''; free=True
            else: continue
        else:
            name=m.group(1).strip(); cost=int(m.group(3))*(1 if m.group(2)=='+' else -1); tail=m.group(4)
        if re.search(r'additional .*model',name,re.I): continue
        # avoid title line or weird costs embedded in explanatory sentence
        if len(name)>100 or name.lower().startswith(('one ', 'the ')) and 'may' in name.lower():
            # if this is actually lead+item combined, skip
            pass
        ctx=(context+' '+tail+' '+s).lower()
        squadwide='per model' in ctx and any(k in ctx for k in ['entire squad','entire unit','entire pack','entire squadron','every model'])
        maxsel=1
        if 'any model' in ctx: maxsel=max_models
        fm=re.search(r'for every (\w+) models',ctx)
        if fm:
            d=WORDNUM.get(fm.group(1), int(fm.group(1)) if fm.group(1).isdigit() else 5)
            maxsel=max(1,max_models//d)
        um=re.search(r'up to (\w+)',ctx)
        if um and 'additional' not in ctx:
            maxsel=WORDNUM.get(um.group(1), int(um.group(1)) if um.group(1).isdigit() else maxsel)
        if 'each' in tail.lower() and maxsel==1:
            um=re.search(r'up to (\w+)',context.lower())
            if um: maxsel=WORDNUM.get(um.group(1),maxsel)
        opts.append({'name':name,'cost':cost,'max':maxsel,'squadwide':squadwide,'per_model_cost':cost if squadwide else None,'context':context[:180]})
    # dedup same name/cost/context rough
    out=[]; seen=set()
    for o in opts:
        key=(o['name'].lower(),o['cost'],o['context'].lower())
        if key not in seen:
            seen.add(key); out.append(o)
    return out

def parse_entries(path, section_ranges=None):
    lines=Path(path).read_text(encoding='utf-8').splitlines()
    return lines

# main Forces parser
lines=Path('sources/Forces of the Legions.md').read_text(encoding='utf-8').splitlines()
legs=[]
for i,l in enumerate(lines):
    m=re.match(r'### ([IVXLCDM]+) — (.+)',l)
    if m: legs.append((i,m.group(1),m.group(2).strip()))
legs.append((len(lines),'','END'))
legdata=[]
for li in range(len(legs)-1):
    s,roman,name=legs[li]; e=legs[li+1][0]
    def is_heading(i):
        l=lines[i].strip()
        if not(l.startswith('**') and l.endswith('**') and re.search(r'[—-].*\d',l)): return False
        nxt='\n'.join(lines[i+1:min(i+18,e)])
        return bool(re.search(r'\|\s*\|\s*(?:WS|BS)\s*\|',nxt,re.I) or 'Unit Composition' in nxt or re.search(r'may be selected as an HQ choice',nxt,re.I))
    poss=[i for i in range(s,e) if is_heading(i)]
    entries=[]
    for k,i in enumerate(poss):
        end=poss[k+1] if k+1<len(poss) else e
        title,cost,isplus=title_cost(lines[i])
        block=lines[i:end]
        hdr,rows=profile_table(block)
        base=parse_base_count(block)
        extra=extra_models(block)
        entries.append({'title':title,'cost':cost,'isplus':isplus,'foc':infer_foc(block,title),'allegiance':allegiance(block),'base_count':base,'extra':extra,'profile_headers':hdr,'profile_rows':rows,'details':plain_block(block[1:]),'options':simple_options(block,base,extra)})
    # pre-entry text for rules/armoury/rites
    first=poss[0] if poss else e
    pre=lines[s+1:first]
    # parse rites: marker line containing RITE OF WAR:, next bold line title, block until next rite marker or first entry
    rites=[]
    i=s
    while i<first:
        if 'RITE OF WAR:' in clean_md(lines[i]).upper():
            j=i+1
            while j<first and not (lines[j].strip().startswith('**') and lines[j].strip().endswith('**')): j+=1
            if j<first:
                rtitle=clean_md(lines[j])
                k=j+1
                while k<first and 'RITE OF WAR:' not in clean_md(lines[k]).upper(): k+=1
                rb=lines[j:k]
                rites.append({'title':rtitle,'text':plain_block(rb[1:]),'allegiance':allegiance(rb)})
                i=k; continue
        i+=1
    # consul/special HQ upgrades before units
    consul=[]
    for i in range(s,first):
        l=lines[i].strip()
        if l.startswith('**') and l.endswith('**') and ('CONSUL' in clean_md(l).upper() or clean_md(l).upper().startswith('IRON FATHER')) and re.search(r'\+\s*\d+',clean_md(l)):
            title,cost,isp=title_cost(l)
            # block until next bold heading of same/high level within reasonable area
            k=i+1
            while k<first:
                ss=lines[k].strip()
                if k>i+1 and ss.startswith('**') and ss.endswith('**') and (re.search(r'RITE OF WAR|SQUAD|PACK|COHORT|MANIPLE|ARMOURY|CONSUL|IRON FATHER',clean_md(ss),re.I)):
                    break
                k+=1
            consul.append({'title':title,'cost':cost,'text':plain_block(lines[i+1:k])})
    # build a compact legion reference from pre excluding rite blocks? just entire pre text (can be huge); limit 12000 chars
    pretext=plain_block(pre)
    legdata.append({'roman':roman,'name':name,'reference':pretext[:16000],'rites':rites,'consuls':consul,'entries':entries})

# Supplement parser generic
def parse_supp(path, start_heading, stop_heading=None):
    ls=Path(path).read_text(encoding='utf-8').splitlines()
    # find section start by exact heading phrase
    s=0;e=len(ls)
    for i,l in enumerate(ls):
        if clean_md(l).upper()==start_heading.upper(): s=i+1; break
    if stop_heading:
        for i in range(s,len(ls)):
            if clean_md(ls[i]).upper()==stop_heading.upper(): e=i; break
    # headings price+ first profile in next18
    poss=[]
    for i in range(s,e):
        l=ls[i].strip()
        if not(l.startswith('**') and l.endswith('**') and re.search(r'[—-].*\d',l)): continue
        nxt='\n'.join(ls[i+1:min(i+18,e)])
        if re.search(r'\|\s*\|\s*(?:WS|BS)\s*\|',nxt,re.I) or 'Unit Composition' in nxt:
            poss.append(i)
    out=[]
    for k,i in enumerate(poss):
        end=poss[k+1] if k+1<len(poss) else e
        title,cost,isplus=title_cost(ls[i]); block=ls[i:end]
        hdr,rows=profile_table(block); base=parse_base_count(block); extra=extra_models(block)
        out.append({'title':title,'cost':cost,'foc':infer_foc(block,title),'base_count':base,'extra':extra,'profile_headers':hdr,'profile_rows':rows,'details':plain_block(block[1:]),'options':simple_options(block,base,extra)})
    return out

low=parse_supp('sources/Lords of War.md','LEGIONES ASTARTES','TALONS OF THE EMPEROR')
aero=parse_supp('sources/Areonautica Imperialis.md','LEGIONES ASTARTES','EXERCITUS ET MECHANICUS')


LEGIONS=legdata
LOW=low
AERO=aero
LOW_WEAPONS=[{'Weapon': 'Neutron Laser Battery', 'Range': '72"', 'S': '10', 'AP': '1', 'Type': 'Ordnance D3, Blast, Twin-linked, Concussive, Shock Pulse, Feedback'}, {'Weapon': 'Dreadhammer Siege Cannon — Standard', 'Range': '24"', 'S': '10', 'AP': '1', 'Type': 'Ordnance 1, Massive Blast, Ignores Cover'}, {'Weapon': 'Dreadhammer Siege Cannon — Diverted', 'Range': '48"', 'S': '10', 'AP': '1', 'Type': 'Ordnance 1, Massive Blast, Ignores Cover, Divert Power'}, {'Weapon': 'Volcano Cannon', 'Range': '120"', 'S': '10', 'AP': '2', 'Type': 'Ordnance 1, Large Blast, Titan Killer'}, {'Weapon': 'Twin-linked Volcano Cannon', 'Range': '120"', 'S': '10', 'AP': '2', 'Type': 'Ordnance 1, Large Blast, Titan Killer, Twin-linked'}, {'Weapon': 'Plasma Blastgun — Rapid', 'Range': '72"', 'S': '8', 'AP': '2', 'Type': 'Ordnance 2, Massive Blast'}, {'Weapon': 'Plasma Blastgun — Overload', 'Range': '96"', 'S': '10', 'AP': '2', 'Type': 'Ordnance 1, Apocalyptic Blast'}, {'Weapon': 'Fellblade Accelerator Cannon — HE', 'Range': '100"', 'S': '8', 'AP': '3', 'Type': 'Ordnance 1, Massive Blast, Twin-linked'}, {'Weapon': 'Fellblade Accelerator Cannon — AE', 'Range': '100"', 'S': '9', 'AP': '2', 'Type': 'Heavy 1, Blast, Armourbane, Twin-linked'}, {'Weapon': 'Quad Lascannon', 'Range': '48"', 'S': '9', 'AP': '2', 'Type': 'Heavy 2, Twin-linked'}, {'Weapon': 'Laser Destroyer', 'Range': '36"', 'S': '9', 'AP': '1', 'Type': 'Ordnance 1, Twin-linked'}, {'Weapon': 'Volkite Carronade', 'Range': '48"', 'S': '8', 'AP': '2', 'Type': 'Ordnance 1, Heavy Beam, Deflagrate, Haywire, Ignores Cover'}, {'Weapon': 'Siege Melta Array', 'Range': '12"', 'S': '9', 'AP': '1', 'Type': 'Heavy 4, Blast, Melta, Stone Burner'}, {'Weapon': 'Skyreaper Battery', 'Range': '48"', 'S': '7', 'AP': '4', 'Type': 'Heavy 5, Twin-linked, Skyfire, Interceptor'}, {'Weapon': 'Thunderhawk Cannon', 'Range': '72"', 'S': '8', 'AP': '3', 'Type': 'Ordnance 1, Massive Blast'}, {'Weapon': 'Turbo-laser Destructor', 'Range': '96"', 'S': '10', 'AP': '2', 'Type': 'Ordnance 1, Large Blast, Titan Killer'}, {'Weapon': 'Thunderhawk Cluster Bomb', 'Range': '—', 'S': '6', 'AP': '4', 'Type': 'Bomb 6, Barrage, Large Blast, One Use'}, {'Weapon': 'Dreadstrike Missile', 'Range': '120"', 'S': '10', 'AP': '2', 'Type': 'Ordnance 1, Blast, One Use'}, {'Weapon': 'Macro-bomb Cluster', 'Range': '—', 'S': '8', 'AP': '3', 'Type': 'Bomb 1, Apocalyptic Barrage (3D6), Sunder, One Use'}, {'Weapon': 'Orbital Strike', 'Range': 'Unlimited', 'S': '10', 'AP': '1', 'Type': 'Ordnance 1, Massive Blast, Barrage, Titan Killer, Indirect Only'}, {'Weapon': 'Baneblade Cannon', 'Range': '72"', 'S': '9', 'AP': '2', 'Type': 'Ordnance 1, Apocalyptic Blast'}, {'Weapon': 'Vulcan Mega-Bolter', 'Range': '60"', 'S': '6', 'AP': '3', 'Type': 'Heavy 15'}, {'Weapon': 'Stormsword Siege Cannon', 'Range': '36"', 'S': '10', 'AP': '1', 'Type': 'Ordnance 1, Apocalyptic Blast, Ignores Cover'}, {'Weapon': 'Stormhammer Cannon', 'Range': '60"', 'S': '9', 'AP': '2', 'Type': 'Ordnance 1, Massive Blast, Shred, Pinning'}, {'Weapon': 'Dual Battlecannon', 'Range': '72"', 'S': '8', 'AP': '3', 'Type': 'Ordnance 2, Large Blast, Twin-linked'}, {'Weapon': 'Bomb', 'Range': '—', 'S': '6', 'AP': '4', 'Type': 'Bomb 1, Blast, One Use'}, {'Weapon': 'Hellstrike Missile', 'Range': '72"', 'S': '8', 'AP': '2', 'Type': 'Heavy 1, Sunder, One Use'}, {'Weapon': 'Stormhammer Cannon', 'Range': '60"', 'S': '9', 'AP': '2', 'Type': 'Ordnance 1, Massive Blast, Shred, Pinning'}, {'Weapon': 'Dual Battlecannon', 'Range': '72"', 'S': '8', 'AP': '3', 'Type': 'Ordnance 2, Large Blast, Twin-linked'}]
AERO_WEAPONS=[{'Weapon': 'Avenger Bolt Cannon', 'Range': '36"', 'S': '6', 'AP': '3', 'Type': 'Heavy 7'}, {'Weapon': 'Defensive Heavy Stubber', 'Range': '36"', 'S': '4', 'AP': '6', 'Type': 'Heavy 3, Skyfire'}, {'Weapon': 'Electromagnetic Storm Charge', 'Range': '—', 'S': '3', 'AP': '4', 'Type': 'Bomb 1, Large Blast, Haywire, Concussive, One Use'}, {'Weapon': 'Hellstrike Missile', 'Range': '72"', 'S': '8', 'AP': '2', 'Type': 'Heavy 1, Sunder, One Use'}, {'Weapon': 'Kinetic Piercer Missile', 'Range': '48"', 'S': '6', 'AP': '2', 'Type': 'Heavy 1, Armourbane, Heat Seeker, One Use'}, {'Weapon': 'Kraken Penetrator Heavy Missile', 'Range': '36"', 'S': '8', 'AP': '1', 'Type': 'Heavy 1, Armourbane, One Use'}, {'Weapon': 'Magna-Melta', 'Range': '18"', 'S': '8', 'AP': '1', 'Type': 'Heavy 1, Large Blast, Melta'}, {'Weapon': 'Phosphex Bomb Cluster', 'Range': '—', 'S': '5', 'AP': '2', 'Type': 'Bomb 2, Barrage, Blast, Poisoned (3+), Crawling Fire, Lingering Death, Deadly Cargo, One Use'}, {'Weapon': 'Quad Heavy Bolter', 'Range': '36"', 'S': '5', 'AP': '4', 'Type': 'Heavy 6, Twin-linked'}, {'Weapon': 'Rad Missile', 'Range': '48"', 'S': '4', 'AP': '3', 'Type': 'Heavy 1, Blast, Fleshbane, Rad-phage'}, {'Weapon': 'Reaper Autocannon Battery', 'Range': '36"', 'S': '7', 'AP': '4', 'Type': 'Heavy 4, Twin-linked'}, {'Weapon': 'Sunfury Heavy Missile', 'Range': '36"', 'S': '6', 'AP': '3', 'Type': 'Heavy 1, Large Blast, Blind, One Use'}, {'Weapon': 'Tactical Bomb', 'Range': '—', 'S': '6', 'AP': '4', 'Type': 'Bomb 1, Barrage, Blast, One Use'}, {'Weapon': 'Tempest Rocket', 'Range': '60"', 'S': '6', 'AP': '4', 'Type': 'Heavy 1, Sunder, One Use'}, {'Weapon': 'Vengeance Launcher', 'Range': '48"', 'S': '5', 'AP': '4', 'Type': 'Heavy 2, Large Blast'}, {'Weapon': 'Xiphon Rotary Missile Launcher', 'Range': '60"', 'S': '8', 'AP': '2', 'Type': 'Heavy 2, Cluster Warhead, Terminal Tracking'}, {'Weapon': 'Avenger Bolt Cannon', 'Range': '36"', 'S': '6', 'AP': '3', 'Type': 'Heavy 7'}, {'Weapon': 'Defensive Heavy Stubber', 'Range': '36"', 'S': '4', 'AP': '6', 'Type': 'Heavy 3, Skyfire'}, {'Weapon': 'Electromagnetic Storm Charge', 'Range': '—', 'S': '3', 'AP': '4', 'Type': 'Bomb 1, Large Blast, Haywire, Concussive, One Use'}, {'Weapon': 'Hellstrike Missile', 'Range': '72"', 'S': '8', 'AP': '2', 'Type': 'Heavy 1, Sunder, One Use'}, {'Weapon': 'Kinetic Piercer Missile', 'Range': '48"', 'S': '6', 'AP': '2', 'Type': 'Heavy 1, Armourbane, Heat Seeker, One Use'}]

CAT=Path('Legiones Astartes.cat'); GST=Path('Prohammer 30k.gst')
# Idempotency guard: workflow may retrigger after its own commit.
try:
    _probe=ET.parse(CAT).getroot()
    if int(_probe.get('revision','0'))>=25:
        print('REV25_ALREADY_APPLIED'); raise SystemExit(0)
except FileNotFoundError:
    raise
CNS='http://www.battlescribe.net/schema/catalogueSchema'; GNS='http://www.battlescribe.net/schema/gameSystemSchema'
ET.register_namespace('', CNS); ET.register_namespace('', GNS)
C=lambda t:f'{{{CNS}}}{t}'; G=lambda t:f'{{{GNS}}}{t}'

def slug(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    s=re.sub(r'[^a-z0-9]+','-',s).strip('-')
    return s[:70] or 'x'

def find_id(root, idv):
    for e in root.iter():
        if e.get('id')==idv: return e
    return None

def child(parent, tag, ns=CNS):
    q=f'{{{ns}}}{tag}'
    for x in parent:
        if x.tag==q: return x
    return ET.SubElement(parent,q)

def remove_r25(root):
    # Remove generated rev25 nodes on a rerun.
    for p in list(root.iter()):
        for ch in list(p):
            if ch.get('id','').startswith('r25-'):
                p.remove(ch)

def cost(parent, v):
    cs=child(parent,'costs'); ET.SubElement(cs,C('cost'),{'name':'Points','typeId':'pts','value':str(v)})

def constraint(parent,idv,typ,val,scope='parent',field='selections'):
    cs=child(parent,'constraints'); ET.SubElement(cs,C('constraint'),{'id':idv,'ty