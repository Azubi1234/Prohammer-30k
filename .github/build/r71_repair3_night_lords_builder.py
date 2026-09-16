from pathlib import Path
p=Path('.github/build/rev71_night_lords_live.py')
s=p.read_text(encoding='utf-8')
old="""ET.indent(ct,space='  ');ET.indent(gt,space='  ');ET.indent(it,space='  ')\nct.write(CAT,encoding='utf-8',xml_declaration=True);gt.write(GST,encoding='utf-8',xml_declaration=True);it.write(IDX,encoding='utf-8',xml_declaration=True)\n"""
new="""ET.indent(ct,space='  ');ET.indent(gt,space='  ');ET.indent(it,space='  ')\n# ElementTree only keeps one default namespace registration at a time. Register the matching schema immediately before each write so New Recruit receives clean default-namespace XML instead of ns0 prefixes.\nET.register_namespace('',CNS);ct.write(CAT,encoding='utf-8',xml_declaration=True)\nET.register_namespace('',GNS);gt.write(GST,encoding='utf-8',xml_declaration=True)\nET.register_namespace('',INS);it.write(IDX,encoding='utf-8',xml_declaration=True)\n"""
if old not in s:
    raise SystemExit('Revision 71 XML write block not found')
s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
compile(s,str(p),'exec')
print('Revision 71 third repair applied: clean default namespaces for CAT/GST/index.')
