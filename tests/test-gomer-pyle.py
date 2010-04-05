#!/usr/bin/env python3

# Testing Gomer/Pyle integration.

import unittest,pdb,sys,os
from adder.common import Symbol as S
import adder.stdenv,adder.common,adder.gomer,adder.pyle

class GomerToPythonTestCase(unittest.TestCase):
    def setUp(self):
        self.pyleStmtLists=[]
        self.pythonTrees=[]
        self.pythonFlat=''
        self.exprPython=None
        adder.common.gensym.nextId=1
        self.verbose=False
        self.scope=adder.gomer.Scope(None)

    def tearDown(self):
        self.pyleStmtLists=None
        self.pythonTrees=None
        self.pythonFlat=None
        self.exprPython=None
        self.verbose=None

    def addDefs(self,*names):
        for name in names:
            self.scope.addDef(S(name),None)

    def compile(self,gomerList):
        gomerAST=adder.gomer.build(self.scope,gomerList)
        self.exprPyleList=gomerAST.compyle(self.pyleStmtLists.append)
        if self.verbose:
            print(self.exprPyleList)
        if self.exprPyleList:
            self.exprPyleAST=adder.pyle.buildExpr(self.exprPyleList)
            self.exprPython=self.exprPyleAST.toPython(False)
        else:
            self.exprPython=None
        if self.verbose:
            print(repr(self.exprPython))
            print(repr(self.pyleStmtLists))
        for pyleList in self.pyleStmtLists:
            pyleAST=adder.pyle.buildStmt(pyleList)
            pythonTree=pyleAST.toPythonTree()
            self.pythonTrees.append(pythonTree)
            self.pythonFlat+=adder.pyle.flatten(pythonTree)
        if self.verbose:
            print(repr(self.pythonTrees))
        return self.exprPython

    def testConstInt(self):
        assert self.compile(1)=='1'
        assert self.pythonFlat==''

    def testCallQuoteInt(self):
        self.compile([S('quote'),2])
        assert self.exprPython=='2'
        assert self.pythonFlat==''

    def testCallQuoteFloat(self):
        self.compile([S('quote'),2.7])
        # Not an exact string match on x86-64.
        assert float(self.exprPython)==2.7
        assert self.pythonFlat==''

    def testCallQuoteStr(self):
        self.compile([S('quote'),"fred"])
        assert self.exprPython=="'fred'"
        assert self.pythonFlat==''

    def testCallQuoteSym(self):
        self.compile([S('quote'),S("fred")])
        assert self.exprPython=="adder.common.Symbol('fred')"
        assert self.pythonFlat==''

    def testCallQuoteList(self):
        self.compile([S('quote'),[S("fred"),17]])
        assert self.exprPython=="[adder.common.Symbol('fred'), 17]"
        assert self.pythonFlat==''

    def testCallEq(self):
        assert self.compile([S('=='),2,3])=='2==3'
        assert self.pythonFlat==''

    def testCallIf(self):
        assert self.compile([S('if'),[S('<'),5,7],2,3])=='2 if (5<7) else 3'
        assert self.pythonFlat==''

    def testCallNe(self):
        assert self.compile([S('!='),2,3])=='2!=3'
        assert self.pythonFlat==''

    def testCallLt(self):
        assert self.compile([S('<'),2,3])=='2<3'
        assert self.pythonFlat==''

    def testCallLe(self):
        assert self.compile([S('<='),2,3])=='2<=3'
        assert self.pythonFlat==''

    def testCallGt(self):
        assert self.compile([S('>'),2,3])=='2>3'
        assert self.pythonFlat==''

    def testCallGe(self):
        assert self.compile([S('>='),2,3])=='2>=3'
        assert self.pythonFlat==''

    def testCallPlus(self):
        assert self.compile([S('+'),2,3])=='2+3'
        assert self.pythonFlat==''

    def testCallMinus(self):
        assert self.compile([S('-'),2,3])=='2-3'
        assert self.pythonFlat==''

    def testCallTimes(self):
        assert self.compile([S('*'),2,3])=='2*3'
        assert self.pythonFlat==''

    def testCallFDiv(self):
        assert self.compile([S('/'),2,3])=='2/3'
        assert self.pythonFlat==''

    def testCallIDiv(self):
        assert self.compile([S('//'),2,3])=='2//3'
        assert self.pythonFlat==''

    def testCallMod(self):
        assert self.compile([S('%'),2,3])=='2%3'
        assert self.pythonFlat==''

    def testCallIn(self):
        assert self.compile([S('in'),2,3])=='2 in 3'
        assert self.pythonFlat==''

    def testCallRaise(self):
        self.addDefs('Exception')
        assert self.compile([S('raise'),[S('Exception')]])==None
        assert self.pythonFlat=='raise Exception()\n'

    def testCallPrint(self):
        assert self.compile([S('print'),17,19])=='print(17, 19)'
        assert self.pythonFlat==''

    def testCallGensym(self):
        self.compile([S('gensym'),[S('quote'),S('fred')]])
        assert self.exprPython=="gensym(adder.common.Symbol('fred'))"
        assert self.pythonFlat==''

    def testCallGetitem(self):
        self.addDefs('l')
        self.compile([S('[]'),S('l'),17])
        assert self.exprPython=="l[17]"
        assert self.pythonFlat==''

    def testCallGetattr(self):
        self.addDefs('o')
        self.compile([S('getattr'),S('o'),'x'])
        assert self.exprPython=="getattr(o, 'x')"
        assert self.pythonFlat==''

    def testCallSlice1(self):
        self.addDefs('l')
        self.compile([S('slice'),S('l'),17])
        assert self.exprPython=="l[17:]"
        assert self.pythonFlat==''

    def testCallSlice2(self):
        self.addDefs('l')
        self.compile([S('slice'),S('l'),17,23])
        assert self.exprPython=="l[17:23]"
        assert self.pythonFlat==''

    def testCallHead(self):
        self.addDefs('l')
        self.compile([S('head'),S('l')])
        assert self.exprPython=="l[1]"
        assert self.pythonFlat==''

    def testCallTail(self):
        self.addDefs('l')
        self.compile([S('tail'),S('l')])
        assert self.exprPython=="l[1:]"
        assert self.pythonFlat==''

    def testCallList(self):
        self.addDefs('x')
        self.compile([S('list'),S('x')])
        assert self.exprPython=="list(x)"
        assert self.pythonFlat==''

    def testCallTuple(self):
        self.addDefs('x')
        self.compile([S('tuple'),S('x')])
        assert self.exprPython=="tuple(x)"
        assert self.pythonFlat==''

    def testCallSet(self):
        self.addDefs('x')
        self.compile([S('set'),S('x')])
        assert self.exprPython=="set(x)"
        assert self.pythonFlat==''

    def testCallDict(self):
        self.addDefs('x','a')
        self.compile([S('dict'),
                      [S('quote'),[[S('x'),17],[S('a'),23]]]
                      ])
        assert self.exprPython=="dict([[adder.common.Symbol('x'), 17], [adder.common.Symbol('a'), 23]])"
        assert self.pythonFlat==''

    def testCallIsinstance(self):
        self.addDefs('x','str')
        self.compile([S('isinstance'),S('x'),S('str')])
        assert self.exprPython=="isinstance(x, str)"
        assert self.pythonFlat==''

    def testCallMkList(self):
        self.addDefs('a')
        self.compile([S('mk-list'),S('a'),1,2,3])
        assert self.exprPython=="[a, 1, 2, 3]"
        assert self.pythonFlat==''

    def testCallMkTuple(self):
        self.addDefs('a')
        self.compile([S('mk-tuple'),S('a'),1,2,3])
        assert self.exprPython=="(a, 1, 2, 3)"
        assert self.pythonFlat==''

    def testCallMkSet(self):
        self.addDefs('a')
        self.compile([S('mk-set'),S('a'),1,2,3])
        assert self.exprPython=="{a, 1, 2, 3}"
        assert self.pythonFlat==''

    def testCallMkDict1(self):
        self.compile([S('mk-dict'),S(':a'),1,S(':b'),3])
        assert self.exprPython=="{'a': 1, 'b': 3}"
        assert self.pythonFlat==''

    def testCallMkDict2(self):
        self.compile([S('mk-dict'),S(':b'),3,S(':a'),1])
        assert self.exprPython=="{'a': 1, 'b': 3}"
        assert self.pythonFlat==''
        
    def testCallReverse(self):
        self.addDefs('l')
        self.compile([S('reverse'),S('l')])
        assert self.exprPython=="adder.runtime.reverse(l)"
        assert self.pythonFlat==''
        
    def testCallReverseBang(self):
        self.addDefs('l')
        self.compile([S('reverse!'),S('l')])
        scratch=S('#<gensym-scratch #1>').toPython()
        assert self.exprPython==scratch
        assert self.pythonFlat==('%s=l.reverse()\n' % scratch)
        
    def testCallStdenv(self):
        self.compile([S('stdenv')])
        assert self.exprPython=="adder.runtime.stdenv()"
        assert self.pythonFlat==''
        
    def testCallEvalPy(self):
        self.addDefs('x')
        self.compile([S('eval-py'),S('x')])
        assert self.exprPython=="eval(x)"
        assert self.pythonFlat==''
        
    def testCallExecPy(self):
        self.addDefs('x')
        self.compile([S('exec-py'),S('x')])
        assert self.exprPython==None
        assert self.pythonFlat=='exec(x)\n'
        
    def testCallApplyNoKw(self):
        self.addDefs('f')
        self.compile([S('apply'),
                      S('f'),
                      [S('mk-list'),1,2,3]
                      ])
        assert self.exprPython=='f(*[1, 2, 3])'
        assert self.pythonFlat==''
        
    def testCallApplyWithKw(self):
        self.addDefs('f')
        self.compile([S('apply'),
                      S('f'),
                      [S('mk-list'),1,2,3],
                      [S('mk-dict'),S(':b'),3,S(':a'),1]
                      ])
        assert self.exprPython=="f(*[1, 2, 3], **{'a': 1, 'b': 3})"
        assert self.pythonFlat==""
        
    def testCallTryNoFinally(self):
        self.addDefs('f','g','foo','flip','bar','h')
        self.compile([S('try'),
                      [S('f'),7],
                      [S('g'),19],
                      S(':Foo'),[S('foo'),
                                 [S('print'),S('foo')],
                                 [S('flip')]
                                 ],
                      S(':Bar'),[S('bar'),[S('h'),S('bar')]],
                      ])
        scratch1=S('#<gensym-scratch #1>').toPython()
        scratch2=S('#<gensym-scratch #2>').toPython()
        assert self.exprPython==scratch1
        assert self.pythonFlat==("""%s=None
try:
    f(7)
    %s=g(19)
    %s=%s
except Foo as foo:
    print(foo)
    flip()
except Bar as bar:
    h(bar)
""" % (scratch1,scratch2,scratch1,scratch2))

    def testCallTryWithFinally(self):
        self.addDefs('f','g','foo','bar','h','pi')
        self.compile([S('try'),
                      [S('f'),7],
                      [S('g'),19],
                      S(':Foo'),[S('foo'),[S('print'),S('foo')]],
                      S(':Bar'),[S('bar'),[S('h'),S('bar')]],
                      S(':finally'),[[S('pi')]],
                      ])
        scratch1=S('#<gensym-scratch #1>').toPython()
        scratch2=S('#<gensym-scratch #2>').toPython()
        assert self.exprPython==scratch1
        assert self.pythonFlat==("""%s=None
try:
    f(7)
    %s=g(19)
    %s=%s
except Foo as foo:
    print(foo)
except Bar as bar:
    h(bar)
finally:
    pi()
""" % (scratch1,scratch2,scratch1,scratch2))

suite=unittest.TestSuite(
    ( unittest.makeSuite(GomerToPythonTestCase,"test"),
     )
    )

unittest.TextTestRunner().run(suite)
