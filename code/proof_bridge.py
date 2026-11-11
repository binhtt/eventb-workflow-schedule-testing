"""Check operational equivalence of a proved model with proof-only parameters.

Extra parameters must have explicit nonrecursive definitions. Derived guard
theorems are removed only after checking the native proof-status artifact.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
from eventb import Model,Expr,parse,NS

def substitute(expression,definitions):
    if expression.op=='name' and expression.args[0] in definitions:
        return substitute(definitions[expression.args[0]],definitions)
    return Expr(expression.op,tuple(substitute(arg,definitions) if isinstance(arg,Expr) else arg
                                    for arg in expression.args))

def load_proved(path):
    path=Path(path)
    statuses=ET.parse(path.with_suffix('.bps')).getroot()
    if not len(statuses) or any(int(s.attrib[NS+'confidence'])<=0 for s in statuses):
        raise ValueError('Native proof statuses include pending obligations')
    model=Model(path)
    xml=ET.parse(path).getroot()
    transformations=[]
    for element in xml.findall(NS+'event'):
        name=element.attrib[NS+'label']; event=model.events[name]
        definitions={}; labels=set()
        for guard in element.findall(NS+'guard'):
            label=guard.attrib[NS+'label']
            if guard.attrib.get(NS+'theorem')=='true':
                labels.add(label)
        parameters={p.attrib[NS+'identifier'] for p in element.findall(NS+'parameter')}
        auxiliary=parameters-{'r','v'}
        for label,expression in event.guards.items():
            if expression.op!='=': continue
            left,right=expression.args
            if left.op=='name' and left.args[0] in auxiliary:
                parameter=left.args[0]
                if parameter in right.names(): raise ValueError('Recursive auxiliary parameter')
                if parameter in definitions: raise ValueError('Ambiguous auxiliary parameter')
                definitions[parameter]=right; labels.add(label)
        if definitions.keys()!=auxiliary:
            raise ValueError('Auxiliary parameter has no explicit definition')
        for parameter,expression in definitions.items():
            if expression.names() & auxiliary:
                raise ValueError('Dependent auxiliary definitions are unsupported')
        event.guards={label:substitute(expression,definitions)
                      for label,expression in event.guards.items() if label not in labels}
        event.assignments={variable:substitute(expression,definitions)
                           for variable,expression in event.assignments.items()}
        transformations.append({'event':name,'removed_derived_labels':sorted(labels),
                                'substituted_parameters':sorted(definitions)})
    return model,transformations

def assert_same_core(first,second):
    assert first.variables==second.variables
    assert first.invariants==second.invariants
    assert first.events.keys()==second.events.keys()
    for name in first.events:
        assert first.events[name].guards==second.events[name].guards,name
        assert first.events[name].assignments==second.events[name].assignments,name
