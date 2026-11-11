"""Regression checks for the translator and the reduction baseline."""
from pathlib import Path
from itertools import permutations
import unittest
from eventb import Model,parse
from scheduling import fixture,sleep_orders,Operation
from runtime import Service,MUTANTS
from experiment import replay,MODEL_PATH

class ValidationChecks(unittest.TestCase):
    def test_rejects_unsupported_syntax(self):
        with self.assertRaises(ValueError):
            parse('∀r·r ∈ REQ')
    def test_simultaneous_assignment(self):
        model=Model(MODEL_PATH)
        state=model.initialise(2,1)
        event=model.events['Reserve']
        next_state=event.apply(state,{'r':0})
        self.assertEqual(next_state['free'],0)
        self.assertEqual(next_state['held'],frozenset({0}))
        self.assertEqual(state['held'],frozenset())
    def test_probe_sleep_set_preserves_all_classes(self):
        operations={ (r,'reserve'):Operation(r,'reserve','Reserve') for r in range(2)}
        pred={}
        for request,name in operations:
            pred[request,name,'probe']=set()
            pred[request,name,'apply']={(request,name,'probe')}
        raw=[]
        for order in permutations(pred):
            done=set()
            if all(not (pred[event]-set(order[:i])) for i,event in enumerate(order)):
                raw.append(order)
        def canonical(order):
            result=[]; block=[]
            for event in order:
                if event[2]=='probe': block.append(event)
                else:
                    result.extend(sorted(block)); block=[]
                    result.append(event)
            result.extend(sorted(block))
            return tuple(result)
        import random
        reduced=list(sleep_orders(pred,random.Random(0),100))
        self.assertEqual(len(raw),6)
        self.assertEqual(len(reduced),4)
        self.assertEqual({canonical(o) for o in raw},{canonical(o) for o in reduced})
        outcomes={}
        for order in raw:
            for mutant in (None,)+MUTANTS:
                service=Service(2,1,mutant)
                errors=set()
                for request,name,hook in order:
                    op=operations[request,name]
                    if hook=='probe': service.probe(op)
                    else:
                        _,obs=service.apply(op)
                        errors.update(service.audit(obs))
                value=(service.snapshot(),errors)
                key=(canonical(order),mutant)
                self.assertEqual(outcomes.setdefault(key,value),value)
                service.close()

if __name__=='__main__':
    unittest.main()
