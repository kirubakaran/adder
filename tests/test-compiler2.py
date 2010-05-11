#!/usr/bin/env python3

import unittest,pdb,sys,os
from adder.compiler2 import Scope,annotate
from adder.common import Symbol as S, gensym

class AnnotateTestCase(unittest.TestCase):
    def setUp(self):
        Scope.nextId=1

    def scopesToIds(self,scoped):
        scopes={}
        def walk(scoped):
            try:
                (expr,line,scope)=scoped
            except ValueError as ve:
                print(ve,scoped)
                raise
            if scope.id in scopes:
                assert scopes[scope.id] is scope
            else:
                scopes[scope.id]=scope
            if isinstance(expr,list):
                expr=list(map(walk,expr))
            return (expr,line,scope.id)
        withIds=walk(scoped)
        keys=set(scopes.keys())
        if 0 in keys:
            assert keys==set(range(0,len(scopes)))
        else:
            assert keys==set(range(1,len(scopes)+1))
        return (withIds,scopes)

    def annotate(self,exprPE,*,scope=None):
        if scope is None:
            scope=Scope(None)
        annotated=annotate(exprPE,scope)
        return self.scopesToIds(annotated)

    def testInt(self):
        (scoped,scopes)=self.annotate((17,1))
        assert scoped==(17,1,1)
        assert isinstance(scopes,dict)
        assert len(scopes)==1
        assert len(scopes[1])==0

    def testStr(self):
        (scoped,scopes)=self.annotate(('foo',1))
        assert scoped==('foo',1,1)
        assert isinstance(scopes,dict)
        assert len(scopes)==1
        assert len(scopes[1])==0

    def testFloat(self):
        (scoped,scopes)=self.annotate((1.7,1))
        assert scoped==(1.7,1,1)
        assert isinstance(scopes,dict)
        assert len(scopes)==1
        assert len(scopes[1])==0

    def testBool(self):
        (scoped,scopes)=self.annotate((True,1))
        assert scoped==(True,1,1)
        assert isinstance(scopes,dict)
        assert len(scopes)==1
        assert len(scopes[1])==0

    def testVar(self):
        scope=Scope(None)
        scope.addDef(S('foo'),None,1)
        (scoped,scopes)=self.annotate((S('foo'),1),scope=scope)
        assert scoped==(S('foo'),1,1)
        assert isinstance(scopes,dict)
        assert len(scopes)==1
        assert scopes[1] is scope
        assert len(scopes[1])==1
        assert list(scopes[1])==[S('foo')]

    def testDefun(self):
        (scoped,scopes)=self.annotate(([(S('defun'),1),
                                        (S('foo'),1),
                                        ([(S('x'),1),
                                          (S('y'),1)
                                          ],1),
                                        ([(S('*'),2),(S('x'),2),(S('y'),2)],
                                         2)
                                        ],
                                       1))
        assert scoped==([(S('defun'),1,0),
                         (S('foo'),1,1),
                         ([(S('x'),1,2),
                           (S('y'),1,2)
                           ],1,1),
                         ([(S('*'),2,0),(S('x'),2,2),(S('y'),2,2)],2,2)
                         ],
                        1,1)
        assert isinstance(scopes,dict)
        assert len(scopes)==3
        assert scopes[0] is Scope.root
        assert list(scopes[1])==[S('foo')]
        assert sorted(scopes[2])==[S('x'),S('y')]
        assert scopes[2].parent is scopes[1]

    def testLambda(self):
        (scoped,scopes)=self.annotate(([(S('lambda'),1),
                                        ([(S('x'),1),
                                          (S('y'),1)
                                          ],1),
                                        ([(S('*'),2),(S('x'),2),(S('y'),2)],
                                         2)
                                        ],
                                       1))
        assert scoped==([(S('lambda'),1,0),
                         ([(S('x'),1,2),
                           (S('y'),1,2)
                           ],1,1),
                         ([(S('*'),2,0),(S('x'),2,2),(S('y'),2,2)],2,2)
                         ],
                        1,1)
        assert isinstance(scopes,dict)
        assert len(scopes)==3
        assert scopes[0] is Scope.root
        assert len(scopes[1])==0
        assert sorted(scopes[2])==[S('x'),S('y')]
        assert scopes[2].parent is scopes[1]

    def testDefvar(self):
        (scoped,scopes)=self.annotate(([(S('defvar'),1),
                                        (S('x'),1),
                                        (17,1)],
                                       1))
        assert scoped==([(S('defvar'),1,0),
                         (S('x'),1,1),
                         (17,1,1)
                         ],
                        1,1)
        assert isinstance(scopes,dict)
        assert len(scopes)==2
        assert scopes[0] is Scope.root
        assert sorted(scopes[1])==[S('x')]
        assert scopes[1].parent is scopes[0]
        entry=scopes[1][S('x')]
        assert entry.constP
        assert entry.constValue==17

    def testScopeTrivial(self):
        (scoped,scopes)=self.annotate(([(S('scope'),1),
                                        (17,1)],
                                       1))
        assert scoped==([(S('scope'),1,0),
                         (17,1,2)
                         ],
                        1,1)
        assert isinstance(scopes,dict)
        assert len(scopes)==3
        assert scopes[0] is Scope.root
        assert len(scopes[1])==0
        assert len(scopes[2])==0

    def testScopeOneVar(self):
        (scoped,scopes)=self.annotate(([(S('scope'),1),
                                        ([(S('defvar'),1),
                                          (S('x'),1),
                                          (17,1)],
                                         1)
                                        ],
                                       1))
        assert scoped==([(S('scope'),1,0),
                         ([(S('defvar'),1,0),
                           (S('x'),1,2),
                           (17,1,2)
                           ],
                          1,2)
                         ],
                        1,1)
        assert isinstance(scopes,dict)
        assert len(scopes)==3
        assert scopes[0] is Scope.root
        assert len(scopes[1])==0
        assert sorted(scopes[2])==[S('x')]
        entry=scopes[2][S('x')]
        assert entry.constP
        assert entry.constValue==17

    def testScopeNested(self):
        (scoped,scopes)=self.annotate(([(S('scope'),1),
                                        ([(S('defvar'),1),
                                          (S('x'),1),
                                          (17,1)],
                                         1),
                                        ([(S('defvar'),1),
                                          (S('y'),1),
                                          (19,1)],
                                         1),
                                        ([(S('scope'),2),
                                          ([(S('defvar'),2),
                                            (S('x'),2),
                                            (23,2)],
                                           2)
                                          ],
                                         2)
                                        ],
                                       1))
        assert scoped==([(S('scope'),1,0),
                         ([(S('defvar'),1,0),
                           (S('x'),1,2),
                           (17,1,2)
                           ],
                          1,2),
                         ([(S('defvar'),1,0),
                           (S('y'),1,2),
                           (19,1,2)
                           ],
                          1,2),
                         ([(S('scope'),2,0),
                           ([(S('defvar'),2,0),
                             (S('x'),2,3),
                             (23,2,3)
                             ],
                            2,3)
                           ],
                          2,2)
                         ],
                        1,1)
        assert isinstance(scopes,dict)
        assert len(scopes)==4
        assert scopes[0] is Scope.root
        assert len(scopes[1])==0
        assert sorted(scopes[2])==[S('x'),S('y')]
        entry=scopes[2][S('x')]
        assert entry.constP
        assert entry.constValue==17
        entry=scopes[2][S('y')]
        assert entry.constP
        assert entry.constValue==19
        assert sorted(scopes[3])==[S('x')]
        entry=scopes[3][S('x')]
        assert entry.constP
        assert entry.constValue==23
        entry=scopes[3][S('y')]
        assert entry.constP
        assert entry.constValue==19

suite=unittest.TestSuite(
    ( 
      unittest.makeSuite(AnnotateTestCase,'test'),
     )
    )

unittest.TextTestRunner().run(suite)