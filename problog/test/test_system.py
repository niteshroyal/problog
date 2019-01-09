"""
Part of the ProbLog distribution.

Copyright 2015 KU Leuven, DTAI Research Group

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import unittest

import glob, os, traceback, sys

if __name__ == '__main__' :
    sys.path.insert(0,os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from problog import root_path
from problog import get_evaluatable

from problog.setup import install
from problog.program import PrologFile, DefaultPrologParser, ExtendedPrologFactory, PrologString
from problog.formula import LogicFormula
from problog.ddnnf_formula import DDNNF
from problog.sdd_formula import SDD
from problog import get_evaluatable
from problog.evaluator import SemiringProbability, SemiringLogProbability
from problog.logic import Term

# noinspection PyBroadException
try:
    from pysdd import sdd
    has_sdd = True
except Exception as err:
    has_sdd = False

class TestDummy(unittest.TestCase):

    def test_dummy(self) : pass

# class TestSystemSDD(unittest.TestCase) :

#     def setUp(self) :

#         try :
#             self.assertSequenceEqual = self.assertItemsEqual
#         except AttributeError :
#             self.assertSequenceEqual = self.assertCountEqual

# class TestSystemNNF(unittest.TestCase) :

#     def setUp(self) :

#         try :
#             self.assertSequenceEqual = self.assertItemsEqual
#         except AttributeError :
#             self.assertSequenceEqual = self.assertCountEqual


class TestSystemGeneric(unittest.TestCase) :


    def setUp(self) :
        try :
            self.assertSequenceEqual = self.assertItemsEqual
        except AttributeError :
            self.assertSequenceEqual = self.assertCountEqual

    def test_system_evaluate_custom_weights(self):
        """
        Tests evaluate() with custom weights (not the ones from file)

        """

        class TestSemiringProbabilityNSP(SemiringProbability):
            """
            Uses NSP=True to test the FormulaEvaluatorNSP.
            """

            def is_nsp(self):
                return True

        program = """
            0.25::a.
            query(a).
        """
        pl = PrologString(program)
        lf = LogicFormula.create_from(pl, label_all=True, avoid_name_clash=True)
        semiring = TestSemiringProbabilityNSP()
        kc_class = get_evaluatable(semiring=semiring)
        kc = kc_class.create_from(lf)
        a = Term('a')

        # without custom weights
        results = kc.evaluate(semiring=semiring)
        self.assertEqual(0.25, results[a])

        # with custom weights
        weights = {a: 0.1}
        results = kc.evaluate(semiring=semiring, weights=weights)
        self.assertEqual(0.1, results[a])


def read_result(filename) :
    results = {}
    with open( filename ) as f :
        reading = False
        for l in f :
            l = l.strip()
            if l.startswith('%Expected outcome:') :
                reading = True
            elif reading :
                if l.lower().startswith('% error') :
                    return l[len('% error'):].strip()
                elif l.startswith('% ') :
                    query, prob = l[2:].rsplit(None,1)
                    results[query.strip()] = float(prob.strip())
                else :
                    reading = False
            if l.startswith('query(') and l.find('% outcome:') >= 0 :
                pos = l.find('% outcome:')
                query = l[6:pos].strip().rstrip('.').rstrip()[:-1]
                prob = l[pos+10:]
                results[query.strip()] = float(prob.strip())
    return results


def createSystemTestGeneric(filename, logspace=False, evaluatable_name=None) :

    correct = read_result(filename)

    def test(self) :
        try :
            parser = DefaultPrologParser(ExtendedPrologFactory())
            kc = get_evaluatable(name=evaluatable_name).create_from(PrologFile(filename, parser=parser))

            if logspace:
                semiring = SemiringLogProbability()
            else :
                semiring = SemiringProbability()

            computed = kc.evaluate(semiring=semiring)
            computed = { str(k) : v for k,v in computed.items() }
        except Exception as err :
            e = err
            computed = None

        if computed is None :
            self.assertEqual(correct, type(e).__name__)
        else :
            self.assertIsInstance( correct, dict )
            self.assertSequenceEqual(correct, computed)

            for query in correct :
                self.assertAlmostEqual(correct[query], computed[query], msg=query)

    return test



def createSystemTestSDD(filename, logspace=False) :

    correct = read_result(filename)

    def test(self) :
        try :
            parser = DefaultPrologParser(ExtendedPrologFactory())
            sdd_kc = SDD.createFrom(PrologFile(filename, parser=parser))

            if logspace :
                semiring = SemiringLogProbability()
            else :
                semiring = SemiringProbability()

            computed = sdd_kc.evaluate(semiring=semiring)
            computed = { str(k) : v for k,v in computed.items() }
        except Exception as err :
            e = err
            computed = None

        if computed is None :
            self.assertEqual(correct, type(e).__name__)
        else :
            self.assertIsInstance( correct, dict )
            self.assertSequenceEqual(correct, computed)

            for query in correct :
                self.assertAlmostEqual(correct[query], computed[query], msg=query)

    return test


def createSystemTestNNF(filename, logspace=False) :

    correct = read_result(filename)

    def test(self) :
        try :
            parser = DefaultPrologParser(ExtendedPrologFactory())
            nnf_kc = DDNNF.createFrom(PrologFile(filename, parser=parser))

            if logspace :
                semiring = SemiringLogProbability()
            else :
                semiring = SemiringProbability()

            computed = nnf_kc.evaluate(semiring=semiring)
            computed = { str(k) : v for k,v in computed.items() }
        except Exception as err :
            e = err
            computed = None

        if computed is None :
            self.assertEqual(correct, type(e).__name__)
        else :
            self.assertIsInstance( correct, dict )
            self.assertSequenceEqual(correct, computed)

            for query in correct :
                self.assertAlmostEqual(correct[query], computed[query], msg=query)

    return test


if __name__ == '__main__' :
    filenames = sys.argv[1:]
else :
    filenames = glob.glob( root_path('test', '*.pl' ) )


evaluatables = ["ddnnf"]

if has_sdd:
    evaluatables.append("sdd")
else:
    print("no SDD support")

for evaluatable_name in evaluatables:
    for testfile in filenames:
        # testname = 'test_' + evaluatable_name + 'system_' + os.path.splitext(os.path.basename(testfile))[0]
        # setattr( TestSystemSDD, testname, createSystemTestSDD(testfile) )
        # setattr( TestSystemNNF, testname, createSystemTestNNF(testfile) )

        testname = 'test_' + evaluatable_name + '_system_' + os.path.splitext(os.path.basename(testfile))[0]
        # setattr( TestSystemSDD, testname, createSystemTestSDD(testfile, True) )
        # setattr( TestSystemNNF, testname, createSystemTestNNF(testfile, True) )
        setattr( TestSystemGeneric, testname, createSystemTestGeneric(testfile, True, evaluatable_name) )


if __name__ == '__main__' :
    # suite = unittest.TestLoader().loadTestsFromTestCase(TestSystemSDD)
    # unittest.TextTestRunner(verbosity=2).run(suite)
    # suite = unittest.TestLoader().loadTestsFromTestCase(TestSystemNNF)
    # unittest.TextTestRunner(verbosity=2).run(suite)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSystemGeneric)
    unittest.TextTestRunner(verbosity=2).run(suite)
