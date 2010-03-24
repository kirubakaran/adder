# Python Lisp-Like Encoding.  IL which maps directly to Python.  Does not encode all
#  of Python, only the bits which Adder will need to generate.

import itertools,re

def withParens(s,inParens):
    if inParens:
        return '(%s)' % s
    else:
        return s

class Expr:
    pass

class SimpleExpr(Expr):
    def __init__(self,py):
        self.py=py

    def toPython(self,inParens):
        return self.py

class Constant(SimpleExpr):
    def __init__(self,c):
        SimpleExpr.__init__(self,repr(c))

class VarExpr(SimpleExpr):
    def __init__(self,v):
        SimpleExpr.__init__(self,v)

noPaddingRe=re.compile('^[^a-zA-Z]+$')

class BinaryOperator(Expr):
    def __init__(self,operator,left,right):
        self.operator=operator
        self.padding='' if noPaddingRe.match(operator) else ' '
        self.left=left
        self.right=right

    def toPython(self,inParens):
        return withParens('%s%s%s%s%s' % (self.left.toPython(True),
                                          self.padding,
                                          self.operator,
                                          self.padding,
                                          self.right.toPython(True)),
                          inParens)

class UnaryOperator(Expr):
    def __init__(self,operator,operand):
        self.operator=operator
        self.operand=operand
        self.padding='' if noPaddingRe.match(operator) else ' '

    def toPython(self,inParens):
        return withParens('%s%s%s' % (self.operator,
                                      self.padding,
                                      self.operand.toPython(True)),
                          inParens)

class CallExpr(Expr):
    def __init__(self,f,posArgs,kwArgs=None):
        self.f=f
        self.posArgs=posArgs
        self.kwArgs=kwArgs or {}

    def toPython(self,inParens):
        res=self.f.toPython(True)+'('

        posArgsStrs=map(lambda expr: expr.toPython(False),
                        self.posArgs)
        kwArgsStrs=map(lambda a: '%s=%s' % (a[0],a[1].toPython(False)),
                       self.kwArgs.items())

        res+=', '.join(itertools.chain(posArgsStrs,kwArgsStrs))

        res+=')'
        return res

class IfOperator(Expr):
    def __init__(self,condExpr,thenExpr,elseExpr):
        self.condExpr=condExpr
        self.thenExpr=thenExpr
        self.elseExpr=elseExpr

    def toPython(self,inParens):
        return withParens(('%s if %s else %s'
                           % (self.thenExpr.toPython(True),
                              self.condExpr.toPython(True),
                              self.elseExpr.toPython(True))),
                          inParens)

class Stmt:
    indentStep=4

    def flatten(self,tree,depth=0):
        if isinstance(tree,str):
            return (' '*(depth*Stmt.indentStep))+tree+'\n'

        if isinstance(tree,list):
            indent=1
        else:
            indent=0

        return ''.join(map(lambda t: self.flatten(t,depth+indent),tree))

    def toPythonFlat(self):
        return self.flatten(self.toPythonTree())

class Assignment(Stmt):
    def __init__(self,lvalue,rvalue):
        self.lvalue=lvalue
        self.rvalue=rvalue

    def toPythonTree(self):
        return '%s=%s' % (self.lvalue.toPython(False),
                          self.rvalue.toPython(False))

class Block(Stmt):
    def __init__(self,stmts):
        self.stmts=stmts

    def toPythonTree(self):
        return tuple(map(lambda s: s.toPythonTree(),self.stmts))

class IfStmt(Stmt):
    def __init__(self,condExpr,thenStmt,elseStmt):
        self.condExpr=condExpr
        self.thenStmt=thenStmt
        self.elseStmt=elseStmt

    def toPythonTree(self):
        return ('if %s:' % self.condExpr.toPython(False),
                [self.thenStmt.toPythonTree()],
                'else:',
                [self.elseStmt.toPythonTree()])

class WhileStmt(Stmt):
    def __init__(self,condExpr,body):
        self.condExpr=condExpr
        self.body=body

    def toPythonTree(self):
        return ('while %s:' % self.condExpr.toPython(False),
                self.body.toPythonTree())

class DefStmt(Stmt):
    def __init__(self,fname,fixedArgs,optionalArgs,kwArgs,body):
        self.fname=fname
        self.fixedArgs=fixedArgs
        self.optionalArgs=optionalArgs
        self.kwArgs=kwArgs
        self.body=body

    def toPythonTree(self):
        def optArgToPy(optionalArg):
            (name,defExpr)=optionalArg
            return '%s=%s' % (name,defExpr.toPython(False))

        def kwArgToPy(kwArg):
            if isinstance(kwArg,str):
                return kwArg
            else:
                (name,defExpr)=kwArg
                return '%s=%s' % (name,defExpr.toPython(False))

        fixedArgsPy=self.fixedArgs
        optionalArgsPy=map(optArgToPy,self.optionalArgs)
        nonKwArgsPy=list(fixedArgsPy)+list(optionalArgsPy)
        kwArgsPy=map(kwArgToPy,self.kwArgs)

        return ('def %s(%s%s%s%s):' % (self.fname,
                                     ','.join(nonKwArgsPy),
                                     ',' if self.kwArgs and nonKwArgsPy else '',
                                     '*,' if self.kwArgs else '',
                                     ','.join(kwArgsPy)
                                     ),
                [self.body.toPythonTree()])

class ReturnStmt(Stmt):
    def __init__(self,returnExpr):
        self.returnExpr=returnExpr

    def toPythonTree(self):
        return 'return %s' % self.returnExpr.toPython(False)
