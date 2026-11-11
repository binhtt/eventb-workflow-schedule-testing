"""Create the parameterized Event-B shared-resource specification."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent / 'SharedWorkflow'
NS = 'org.eventb.core.'

def child(parent, kind, key, **attrs):
    return ET.SubElement(parent,NS+kind,{'name':key,**{NS+k:str(v) for k,v in attrs.items()}})

def write(root,path):
    ET.indent(root)
    ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)

def main():
    ROOT.mkdir(exist_ok=True)
    (ROOT/'.project').write_text('''<?xml version="1.0" encoding="UTF-8"?>
<projectDescription><name>SharedWorkflow</name><comment></comment><projects/>
<buildSpec><buildCommand><name>org.rodinp.core.rodinbuilder</name><arguments/></buildCommand></buildSpec>
<natures><nature>org.rodinp.core.rodinnature</nature></natures></projectDescription>
''')
    context = ET.Element(NS+'contextFile',{'version':'3',NS+'configuration':NS+'fwd'})
    child(context,'carrierSet','requests',identifier='REQ')
    child(context,'constant','capacity',identifier='CAP')
    for label,pred in [('finite_requests','finite(REQ)'),('positive_capacity','CAP ∈ ℕ1')]:
        child(context,'axiom',label,label=label,predicate=pred,theorem='false')
    write(context,ROOT/'Pool.buc')
    machine = ET.Element(NS+'machineFile',{'version':'5',NS+'configuration':NS+'fwd'})
    child(machine,'seesContext','context',target='Pool')
    variables = ('free','held','closed','moved','effected','acked')
    for var in variables:
        child(machine,'variable',var,identifier=var)
    invariants = {f'type_{var}':f'{var} ⊆ REQ' for var in variables if var!='free'}
    invariants.update({'free_nonnegative':'free ∈ ℕ',
                       'conservation':'free + card(held) = CAP',
                       'closed_not_held':'held ∩ closed = ∅',
                       'ack_after_effect':'acked ⊆ effected'})
    for label,pred in invariants.items():
        child(machine,'invariant',label,label=label,predicate=pred,theorem='false')
    init = child(machine,'event','initialise',label='INITIALISATION',convergence=0,extended='false')
    for var in variables:
        child(init,'action',var,label=var,assignment=f'{var} ≔ '+('CAP' if var=='free' else '∅'))
    definitions = [
        ('Reserve',('r ∈ REQ','r ∉ held','r ∉ closed','free > 0'),
         {'held':'held ∪ {r}','free':'free − 1'}),
        ('Execute',('r ∈ REQ','v ∈ {0, 1}','r ∈ held','r ∉ effected',
                    '(r ∈ moved ⇒ v = 1)','(r ∉ moved ⇒ v = 0)'),
         {'effected':'effected ∪ {r}'}),
        ('Transfer',('r ∈ REQ','r ∈ held','r ∉ moved'),{'moved':'moved ∪ {r}'}),
        ('Acknowledge',('r ∈ REQ','v ∈ {0, 1}','r ∈ effected',
                        '(r ∈ moved ⇒ v = 1)','(r ∉ moved ⇒ v = 0)'),
         {'acked':'acked ∪ {r}'}),
        ('Release',('r ∈ REQ','r ∈ held'),
         {'held':'held ∖ {r}','closed':'closed ∪ {r}','free':'free + 1'}),
        ('Expire',('r ∈ REQ','r ∈ held'),
         {'held':'held ∖ {r}','closed':'closed ∪ {r}','free':'free + 1'}),
    ]
    for name,guards,actions in definitions:
        event=child(machine,'event',name,label=name,convergence=0,extended='false')
        child(event,'parameter','request',identifier='r')
        if name in ('Execute','Acknowledge'):
            child(event,'parameter','epoch',identifier='v')
        for index,guard in enumerate(guards):
            child(event,'guard',f'g{index}',label=f'g{index}',predicate=guard,theorem='false')
        for var,expression in actions.items():
            child(event,'action',var,label=var,assignment=f'{var} ≔ {expression}')
    write(machine,ROOT/'Resource.bum')

if __name__=='__main__':
    main()
