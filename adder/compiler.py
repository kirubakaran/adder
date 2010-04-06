from adder.common import Symbol as S
import adder.gomer,adder.runtime

from adder.gomer import TwoConsecutiveKeywords,VarRef

class Macro(adder.gomer.Function):
    def __init__(self,name,context,transformer):
        self.name=name
        self.context=context
        self.transformer=transformer

    def transform(self,srcExpr):
        posArgs=[]
        kwArgs=[]

        curKeyword=None
        for arg in srcExpr[1:]:
            # Need to operate on symbols, not VarRefs.
            isKeyword=isinstance(arg,S) and arg.startswith(':')

            if curKeyword:
                if isKeyword:
                    varRef=VarRef(self.context.scope,curKeyword)
                    raise TwoConsecutiveKeywords(varRef,arg)
                kwArgs.append([curKeyword[1:],arg])
                curKeyword=None
            else:
                if isKeyword:
                    assert len(arg.name)>1
                    curKeyword=arg
                else:
                    posArgs.append(arg)

        expr=self.transformer(self.context,
                              srcExpr[0],
                              posArgs,kwArgs)
        if False:
            print('Macro %s:' % self.name)
            print('\tbefore:',srcExpr[0],posArgs,kwArgs)
            print('\tafter:',expr)

        return expr

class Context:
    def __init__(self,parent):
        self.parent=parent
        self.scope=adder.gomer.Scope(parent.scope if parent else None)
        if parent:
            self.globals=parent.globals
        else:
            self.globals={'adder': adder,
                          'gensym': adder.common.gensym}

    def __getitem__(self,name):
        return self.globals[name]

    def __setitem__(self,name,value):
        self.globals[name]=value

    def __contains__(self,name):
        return name in self.globals

    def addDef(self,name,value):
        self.scope.addDef(S(name),
                          (None if (value is None)
                           else adder.gomer.Constant(self.scope,value)
                           ))
        self.globals[name]=value

    def addMacroDef(self,name,transformer):
        self.scope.addDef(S(name),
                          adder.gomer.Constant(self.scope,
                                               Macro(name,self,transformer)
                                               )
                          )

    def addFuncDef(self,name,f):
        self.addDef(name,
                    adder.gomer.PyleExpr(self.scope,
                                         name)
                    )
        self.globals[name]=f

    def eval(self,expr):
        return adder.gomer.evalTopLevel(expr,self.scope,self.globals)

    def compyle(self,expr,stmtCollector):
        return adder.gomer.build(self.scope,expr).compyle(stmtCollector)
