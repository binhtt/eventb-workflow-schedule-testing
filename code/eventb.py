"""Strict executable subset of Event-B for this artifact.

Unsupported syntax raises an error. No implementation/mutant code is imported.
"""
from dataclasses import dataclass
from pathlib import Path
import re
import xml.etree.ElementTree as ET

TOKEN = re.compile(r'\s*(ℕ1|ℕ|[A-Za-z_][A-Za-z_0-9]*|[0-9]+|[(){} ,∅∈∉∪∖∩⊆∧⇒=≠<>≤≥+−])')
PRECEDENCE={'⇒':1,'∧':2,'=':3,'≠':3,'∈':3,'∉':3,'⊆':3,'<':3,'>':3,'≤':3,'≥':3,
            '+':4,'−':4,'∪':4,'∖':4,'∩':4}
NS='org.eventb.core.'

@dataclass(frozen=True)
class Expr:
    op: str
    args: tuple
    def eval(self,env):
        if self.op=='integer': return self.args[0]
        if self.op=='name': return env[self.args[0]]
        if self.op=='set': return frozenset(x.eval(env) for x in self.args)
        if self.op in ('card','finite'):
            value=self.args[0].eval(env)
            return len(value) if self.op=='card' else isinstance(value,(set,frozenset))
        left,right=self.args
        a=left.eval(env)
        if self.op=='∈' and right.op=='name' and right.args[0] in ('ℕ','ℕ1'):
            return isinstance(a,int) and a >= (1 if right.args[0]=='ℕ1' else 0)
        b=right.eval(env)
        operations={'⇒':lambda:not a or b,'∧':lambda:a and b,
                    '=':lambda:a==b,'≠':lambda:a!=b,'∈':lambda:a in b,'∉':lambda:a not in b,
                    '⊆':lambda:a<=b,'<':lambda:a<b,'>':lambda:a>b,'≤':lambda:a<=b,
                    '≥':lambda:a>=b,'+':lambda:a+b,'−':lambda:a-b,
                    '∪':lambda:a|b,'∖':lambda:a-b,'∩':lambda:a&b}
        return operations[self.op]()
    def names(self):
        if self.op=='name': return {self.args[0]}
        return set().union(*(x.names() for x in self.args if isinstance(x,Expr)))

class Parser:
    def __init__(self,text):
        self.tokens=[]
        pos=0
        while pos<len(text):
            match=TOKEN.match(text,pos)
            if match is None: raise ValueError(f'Unsupported Event-B syntax {text[pos:]}')
            pos=match.end()
            if match[1].strip(): self.tokens.append(match[1])
        self.index=0
    def take(self):
        token=self.tokens[self.index]; self.index+=1; return token
    def peek(self):
        return self.tokens[self.index] if self.index<len(self.tokens) else None
    def expr(self,minimum=0):
        token=self.take()
        if token=='(':
            left=self.expr()
            assert self.take()==')'
        elif token=='∅': left=Expr('set',())
        elif token=='{':
            args=[]
            while self.peek()!='}':
                args.append(self.expr())
                if self.peek()!=',': break
                self.take()
            assert self.take()=='}'
            left=Expr('set',tuple(args))
        elif token.isdigit(): left=Expr('integer',(int(token),))
        elif token in ('card','finite'):
            assert self.take()=='('
            left=Expr(token,(self.expr(),))
            assert self.take()==')'
        else: left=Expr('name',(token,))
        while self.peek() in PRECEDENCE and PRECEDENCE[self.peek()]>=minimum:
            operator=self.take()
            right=self.expr(PRECEDENCE[operator]+1)
            left=Expr(operator,(left,right))
        return left

def parse(text):
    parser=Parser(text)
    result=parser.expr()
    if parser.peek() is not None: raise ValueError(text)
    return result

@dataclass
class Event:
    name: str
    guards: dict
    assignments: dict
    variables: frozenset
    @property
    def reads(self):
        return set().union(*(expr.names() for expr in self.guards.values())) & self.variables
    @property
    def writes(self):
        return set(self.assignments)
    def enabled(self,state,parameters):
        return all(expr.eval(state|parameters) for expr in self.guards.values())
    def apply(self,state,parameters):
        env=state|parameters
        return state|{key:expr.eval(env) for key,expr in self.assignments.items()}

class Model:
    def __init__(self,path):
        root=ET.parse(path).getroot()
        self.variables=frozenset(e.attrib[NS+'identifier'] for e in root.findall(NS+'variable'))
        self.invariants={e.attrib[NS+'label']:parse(e.attrib[NS+'predicate'])
                         for e in root.findall(NS+'invariant')}
        self.events={}
        self.raw_guards={}
        for element in root.findall(NS+'event'):
            name=element.attrib[NS+'label']
            guards={g.attrib[NS+'label']:parse(g.attrib[NS+'predicate'])
                    for g in element.findall(NS+'guard')}
            assignments={}
            for action in element.findall(NS+'action'):
                variable,expression=action.attrib[NS+'assignment'].split('≔')
                assignments[variable.strip()]=parse(expression.strip())
            self.events[name]=Event(name,guards,assignments,self.variables)
            self.raw_guards[name]={g.attrib[NS+'label']:g.attrib[NS+'predicate']
                                   for g in element.findall(NS+'guard')}
    def initialise(self,size,capacity):
        return self.events['INITIALISATION'].apply({'REQ':frozenset(range(size)),'CAP':capacity},{})
    def errors(self,state):
        return [name for name,predicate in self.invariants.items() if not predicate.eval(state)]
