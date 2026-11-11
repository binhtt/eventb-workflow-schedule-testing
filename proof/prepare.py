"""Add definitional proof parameters without changing the operational model."""
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
NS='org.eventb.core.'

def main():
    source=ROOT.parent/'model/SharedWorkflow'
    target=ROOT/'SharedWorkflow'
    target.mkdir(exist_ok=True)
    for name in ('.project','Pool.buc'):
        shutil.copy(source/name,target/name)
    root=ET.parse(source/'Resource.bum').getroot()
    for event in root.findall(NS+'event'):
        if event.attrib[NS+'label'] not in ('Release','Expire'): continue
        ET.SubElement(event,NS+'parameter',{'name':'remaining',NS+'identifier':'remaining'})
        guards=[
            ('remaining_definition','remaining = held ∖ {r}','false'),
            ('remaining_partition','held = remaining ∪ {r}','true'),
            ('remaining_disjoint','r ∉ remaining','true'),
            ('remaining_card','card(held) = card(remaining) + 1','true'),
        ]
        for name,predicate,theorem in guards:
            ET.SubElement(event,NS+'guard',{'name':name,NS+'label':name,
                                          NS+'predicate':predicate,NS+'theorem':theorem})
        for action in event.findall(NS+'action'):
            if action.attrib[NS+'label']=='held':
                action.set(NS+'assignment','held ≔ remaining')
    ET.indent(root)
    ET.ElementTree(root).write(target/'Resource.bum',encoding='utf-8',xml_declaration=True)

if __name__=='__main__': main()
