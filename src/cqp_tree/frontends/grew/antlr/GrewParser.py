# Generated from Grew.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,27,163,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,6,7,
        6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,2,12,7,12,1,0,1,0,
        5,0,29,8,0,10,0,12,0,32,9,0,1,0,1,0,1,1,1,1,1,1,1,2,1,2,1,2,1,2,
        3,2,43,8,2,1,3,1,3,1,3,1,3,5,3,49,8,3,10,3,12,3,52,9,3,1,3,1,3,3,
        3,56,8,3,3,3,58,8,3,1,3,1,3,1,4,1,4,1,4,1,4,5,4,66,8,4,10,4,12,4,
        69,9,4,1,4,1,4,3,4,73,8,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,4,1,
        4,1,4,1,4,3,4,87,8,4,1,5,1,5,1,5,1,5,5,5,93,8,5,10,5,12,5,96,9,5,
        3,5,98,8,5,1,5,1,5,1,6,1,6,1,6,1,6,1,6,1,6,1,6,1,6,5,6,110,8,6,10,
        6,12,6,113,9,6,3,6,115,8,6,3,6,117,8,6,1,7,1,7,1,7,1,7,1,7,1,7,1,
        7,1,7,1,7,1,7,3,7,129,8,7,1,8,1,8,1,8,5,8,134,8,8,10,8,12,8,137,
        9,8,1,9,1,9,1,9,1,9,3,9,143,8,9,1,10,1,10,1,10,1,10,1,10,1,10,1,
        10,1,10,3,10,153,8,10,1,11,1,11,3,11,157,8,11,1,12,1,12,3,12,161,
        8,12,1,12,0,0,13,0,2,4,6,8,10,12,14,16,18,20,22,24,0,0,175,0,26,
        1,0,0,0,2,35,1,0,0,0,4,42,1,0,0,0,6,44,1,0,0,0,8,86,1,0,0,0,10,88,
        1,0,0,0,12,116,1,0,0,0,14,128,1,0,0,0,16,130,1,0,0,0,18,142,1,0,
        0,0,20,152,1,0,0,0,22,156,1,0,0,0,24,160,1,0,0,0,26,30,3,2,1,0,27,
        29,3,4,2,0,28,27,1,0,0,0,29,32,1,0,0,0,30,28,1,0,0,0,30,31,1,0,0,
        0,31,33,1,0,0,0,32,30,1,0,0,0,33,34,5,0,0,1,34,1,1,0,0,0,35,36,5,
        1,0,0,36,37,3,6,3,0,37,3,1,0,0,0,38,39,5,2,0,0,39,43,3,6,3,0,40,
        41,5,3,0,0,41,43,3,6,3,0,42,38,1,0,0,0,42,40,1,0,0,0,43,5,1,0,0,
        0,44,50,5,4,0,0,45,46,3,8,4,0,46,47,5,5,0,0,47,49,1,0,0,0,48,45,
        1,0,0,0,49,52,1,0,0,0,50,48,1,0,0,0,50,51,1,0,0,0,51,57,1,0,0,0,
        52,50,1,0,0,0,53,55,3,8,4,0,54,56,5,5,0,0,55,54,1,0,0,0,55,56,1,
        0,0,0,56,58,1,0,0,0,57,53,1,0,0,0,57,58,1,0,0,0,58,59,1,0,0,0,59,
        60,5,6,0,0,60,7,1,0,0,0,61,62,5,25,0,0,62,67,3,10,5,0,63,64,5,7,
        0,0,64,66,3,10,5,0,65,63,1,0,0,0,66,69,1,0,0,0,67,65,1,0,0,0,67,
        68,1,0,0,0,68,87,1,0,0,0,69,67,1,0,0,0,70,71,5,25,0,0,71,73,5,8,
        0,0,72,70,1,0,0,0,72,73,1,0,0,0,73,74,1,0,0,0,74,75,5,25,0,0,75,
        76,3,14,7,0,76,77,5,25,0,0,77,87,1,0,0,0,78,79,3,18,9,0,79,80,3,
        24,12,0,80,81,3,18,9,0,81,87,1,0,0,0,82,83,5,25,0,0,83,84,3,22,11,
        0,84,85,5,25,0,0,85,87,1,0,0,0,86,61,1,0,0,0,86,72,1,0,0,0,86,78,
        1,0,0,0,86,82,1,0,0,0,87,9,1,0,0,0,88,97,5,9,0,0,89,94,3,12,6,0,
        90,91,5,10,0,0,91,93,3,12,6,0,92,90,1,0,0,0,93,96,1,0,0,0,94,92,
        1,0,0,0,94,95,1,0,0,0,95,98,1,0,0,0,96,94,1,0,0,0,97,89,1,0,0,0,
        97,98,1,0,0,0,98,99,1,0,0,0,99,100,5,11,0,0,100,11,1,0,0,0,101,117,
        5,25,0,0,102,103,5,12,0,0,103,117,5,25,0,0,104,105,5,25,0,0,105,
        114,3,24,12,0,106,111,3,18,9,0,107,108,5,7,0,0,108,110,3,18,9,0,
        109,107,1,0,0,0,110,113,1,0,0,0,111,109,1,0,0,0,111,112,1,0,0,0,
        112,115,1,0,0,0,113,111,1,0,0,0,114,106,1,0,0,0,114,115,1,0,0,0,
        115,117,1,0,0,0,116,101,1,0,0,0,116,102,1,0,0,0,116,104,1,0,0,0,
        117,13,1,0,0,0,118,129,5,13,0,0,119,120,5,14,0,0,120,121,3,16,8,
        0,121,122,5,15,0,0,122,129,1,0,0,0,123,124,5,14,0,0,124,125,5,16,
        0,0,125,126,3,16,8,0,126,127,5,15,0,0,127,129,1,0,0,0,128,118,1,
        0,0,0,128,119,1,0,0,0,128,123,1,0,0,0,129,15,1,0,0,0,130,135,3,20,
        10,0,131,132,5,7,0,0,132,134,3,20,10,0,133,131,1,0,0,0,134,137,1,
        0,0,0,135,133,1,0,0,0,135,136,1,0,0,0,136,17,1,0,0,0,137,135,1,0,
        0,0,138,139,5,25,0,0,139,140,5,17,0,0,140,143,5,25,0,0,141,143,3,
        20,10,0,142,138,1,0,0,0,142,141,1,0,0,0,143,19,1,0,0,0,144,153,5,
        26,0,0,145,153,5,25,0,0,146,147,5,18,0,0,147,153,5,26,0,0,148,153,
        5,27,0,0,149,150,5,25,0,0,150,151,5,8,0,0,151,153,5,25,0,0,152,144,
        1,0,0,0,152,145,1,0,0,0,152,146,1,0,0,0,152,148,1,0,0,0,152,149,
        1,0,0,0,153,21,1,0,0,0,154,157,5,19,0,0,155,157,5,20,0,0,156,154,
        1,0,0,0,156,155,1,0,0,0,157,23,1,0,0,0,158,161,5,21,0,0,159,161,
        5,22,0,0,160,158,1,0,0,0,160,159,1,0,0,0,161,25,1,0,0,0,19,30,42,
        50,55,57,67,72,86,94,97,111,114,116,128,135,142,152,156,160
    ]

class GrewParser ( Parser ):

    grammarFileName = "Grew.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'pattern'", "'with'", "'without'", "'{'", 
                     "';'", "'}'", "'|'", "':'", "'['", "','", "']'", "'!'", 
                     "'->'", "'-['", "']->'", "'^'", "'.'", "'re'", "'<'", 
                     "'<<'", "'='", "'<>'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "IgnoredWhitespace", 
                      "IgnoredComments", "Identifier", "String", "PCREString" ]

    RULE_request = 0
    RULE_pattern = 1
    RULE_requestItem = 2
    RULE_body = 3
    RULE_clause = 4
    RULE_featureStructure = 5
    RULE_feature = 6
    RULE_arrow = 7
    RULE_edgeTypes = 8
    RULE_featureValue = 9
    RULE_literal = 10
    RULE_order = 11
    RULE_compare = 12

    ruleNames =  [ "request", "pattern", "requestItem", "body", "clause", 
                   "featureStructure", "feature", "arrow", "edgeTypes", 
                   "featureValue", "literal", "order", "compare" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    T__5=6
    T__6=7
    T__7=8
    T__8=9
    T__9=10
    T__10=11
    T__11=12
    T__12=13
    T__13=14
    T__14=15
    T__15=16
    T__16=17
    T__17=18
    T__18=19
    T__19=20
    T__20=21
    T__21=22
    IgnoredWhitespace=23
    IgnoredComments=24
    Identifier=25
    String=26
    PCREString=27

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class RequestContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def pattern(self):
            return self.getTypedRuleContext(GrewParser.PatternContext,0)


        def EOF(self):
            return self.getToken(GrewParser.EOF, 0)

        def requestItem(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(GrewParser.RequestItemContext)
            else:
                return self.getTypedRuleContext(GrewParser.RequestItemContext,i)


        def getRuleIndex(self):
            return GrewParser.RULE_request




    def request(self):

        localctx = GrewParser.RequestContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_request)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 26
            self.pattern()
            self.state = 30
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==2 or _la==3:
                self.state = 27
                self.requestItem()
                self.state = 32
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 33
            self.match(GrewParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PatternContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def body(self):
            return self.getTypedRuleContext(GrewParser.BodyContext,0)


        def getRuleIndex(self):
            return GrewParser.RULE_pattern




    def pattern(self):

        localctx = GrewParser.PatternContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_pattern)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 35
            self.match(GrewParser.T__0)
            self.state = 36
            self.body()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class RequestItemContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return GrewParser.RULE_requestItem

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class WithItemContext(RequestItemContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.RequestItemContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def body(self):
            return self.getTypedRuleContext(GrewParser.BodyContext,0)



    class WithoutItemContext(RequestItemContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.RequestItemContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def body(self):
            return self.getTypedRuleContext(GrewParser.BodyContext,0)




    def requestItem(self):

        localctx = GrewParser.RequestItemContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_requestItem)
        try:
            self.state = 42
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [2]:
                localctx = GrewParser.WithItemContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 38
                self.match(GrewParser.T__1)
                self.state = 39
                self.body()
                pass
            elif token in [3]:
                localctx = GrewParser.WithoutItemContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 40
                self.match(GrewParser.T__2)
                self.state = 41
                self.body()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BodyContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def clause(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(GrewParser.ClauseContext)
            else:
                return self.getTypedRuleContext(GrewParser.ClauseContext,i)


        def getRuleIndex(self):
            return GrewParser.RULE_body




    def body(self):

        localctx = GrewParser.BodyContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_body)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 44
            self.match(GrewParser.T__3)
            self.state = 50
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,2,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 45
                    self.clause()
                    self.state = 46
                    self.match(GrewParser.T__4) 
                self.state = 52
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,2,self._ctx)

            self.state = 57
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & 235143168) != 0):
                self.state = 53
                self.clause()
                self.state = 55
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la==5:
                    self.state = 54
                    self.match(GrewParser.T__4)




            self.state = 59
            self.match(GrewParser.T__5)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ClauseContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return GrewParser.RULE_clause

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class ConstraintClauseContext(ClauseContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.ClauseContext
            super().__init__(parser)
            self.lhs = None # FeatureValueContext
            self.rhs = None # FeatureValueContext
            self.copyFrom(ctx)

        def compare(self):
            return self.getTypedRuleContext(GrewParser.CompareContext,0)

        def featureValue(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(GrewParser.FeatureValueContext)
            else:
                return self.getTypedRuleContext(GrewParser.FeatureValueContext,i)



    class EdgeClauseContext(ClauseContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.ClauseContext
            super().__init__(parser)
            self.label = None # Token
            self.src = None # Token
            self.dst = None # Token
            self.copyFrom(ctx)

        def arrow(self):
            return self.getTypedRuleContext(GrewParser.ArrowContext,0)

        def Identifier(self, i:int=None):
            if i is None:
                return self.getTokens(GrewParser.Identifier)
            else:
                return self.getToken(GrewParser.Identifier, i)


    class OrderClauseContext(ClauseContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.ClauseContext
            super().__init__(parser)
            self.lhs = None # Token
            self.rhs = None # Token
            self.copyFrom(ctx)

        def order(self):
            return self.getTypedRuleContext(GrewParser.OrderContext,0)

        def Identifier(self, i:int=None):
            if i is None:
                return self.getTokens(GrewParser.Identifier)
            else:
                return self.getToken(GrewParser.Identifier, i)


    class NodeClauseContext(ClauseContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.ClauseContext
            super().__init__(parser)
            self.label = None # Token
            self.copyFrom(ctx)

        def featureStructure(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(GrewParser.FeatureStructureContext)
            else:
                return self.getTypedRuleContext(GrewParser.FeatureStructureContext,i)

        def Identifier(self):
            return self.getToken(GrewParser.Identifier, 0)



    def clause(self):

        localctx = GrewParser.ClauseContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_clause)
        self._la = 0 # Token type
        try:
            self.state = 86
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,7,self._ctx)
            if la_ == 1:
                localctx = GrewParser.NodeClauseContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 61
                localctx.label = self.match(GrewParser.Identifier)
                self.state = 62
                self.featureStructure()
                self.state = 67
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==7:
                    self.state = 63
                    self.match(GrewParser.T__6)
                    self.state = 64
                    self.featureStructure()
                    self.state = 69
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                pass

            elif la_ == 2:
                localctx = GrewParser.EdgeClauseContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 72
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input,6,self._ctx)
                if la_ == 1:
                    self.state = 70
                    localctx.label = self.match(GrewParser.Identifier)
                    self.state = 71
                    self.match(GrewParser.T__7)


                self.state = 74
                localctx.src = self.match(GrewParser.Identifier)
                self.state = 75
                self.arrow()
                self.state = 76
                localctx.dst = self.match(GrewParser.Identifier)
                pass

            elif la_ == 3:
                localctx = GrewParser.ConstraintClauseContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 78
                localctx.lhs = self.featureValue()
                self.state = 79
                self.compare()
                self.state = 80
                localctx.rhs = self.featureValue()
                pass

            elif la_ == 4:
                localctx = GrewParser.OrderClauseContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 82
                localctx.lhs = self.match(GrewParser.Identifier)
                self.state = 83
                self.order()
                self.state = 84
                localctx.rhs = self.match(GrewParser.Identifier)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class FeatureStructureContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def feature(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(GrewParser.FeatureContext)
            else:
                return self.getTypedRuleContext(GrewParser.FeatureContext,i)


        def getRuleIndex(self):
            return GrewParser.RULE_featureStructure




    def featureStructure(self):

        localctx = GrewParser.FeatureStructureContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_featureStructure)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 88
            self.match(GrewParser.T__8)
            self.state = 97
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==12 or _la==25:
                self.state = 89
                self.feature()
                self.state = 94
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==10:
                    self.state = 90
                    self.match(GrewParser.T__9)
                    self.state = 91
                    self.feature()
                    self.state = 96
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)



            self.state = 99
            self.match(GrewParser.T__10)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class FeatureContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return GrewParser.RULE_feature

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class RequiresContext(FeatureContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.FeatureContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Identifier(self):
            return self.getToken(GrewParser.Identifier, 0)
        def compare(self):
            return self.getTypedRuleContext(GrewParser.CompareContext,0)

        def featureValue(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(GrewParser.FeatureValueContext)
            else:
                return self.getTypedRuleContext(GrewParser.FeatureValueContext,i)



    class PresenceContext(FeatureContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.FeatureContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Identifier(self):
            return self.getToken(GrewParser.Identifier, 0)


    class AbsenceContext(FeatureContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.FeatureContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Identifier(self):
            return self.getToken(GrewParser.Identifier, 0)



    def feature(self):

        localctx = GrewParser.FeatureContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_feature)
        self._la = 0 # Token type
        try:
            self.state = 116
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,12,self._ctx)
            if la_ == 1:
                localctx = GrewParser.PresenceContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 101
                self.match(GrewParser.Identifier)
                pass

            elif la_ == 2:
                localctx = GrewParser.AbsenceContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 102
                self.match(GrewParser.T__11)
                self.state = 103
                self.match(GrewParser.Identifier)
                pass

            elif la_ == 3:
                localctx = GrewParser.RequiresContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 104
                self.match(GrewParser.Identifier)
                self.state = 105
                self.compare()
                self.state = 114
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if (((_la) & ~0x3f) == 0 and ((1 << _la) & 235143168) != 0):
                    self.state = 106
                    self.featureValue()
                    self.state = 111
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    while _la==7:
                        self.state = 107
                        self.match(GrewParser.T__6)
                        self.state = 108
                        self.featureValue()
                        self.state = 113
                        self._errHandler.sync(self)
                        _la = self._input.LA(1)



                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ArrowContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return GrewParser.RULE_arrow

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class PositiveArrowContext(ArrowContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.ArrowContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def edgeTypes(self):
            return self.getTypedRuleContext(GrewParser.EdgeTypesContext,0)



    class NegatedArrowContext(ArrowContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.ArrowContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def edgeTypes(self):
            return self.getTypedRuleContext(GrewParser.EdgeTypesContext,0)



    class SimpleArrowContext(ArrowContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.ArrowContext
            super().__init__(parser)
            self.copyFrom(ctx)




    def arrow(self):

        localctx = GrewParser.ArrowContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_arrow)
        try:
            self.state = 128
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,13,self._ctx)
            if la_ == 1:
                localctx = GrewParser.SimpleArrowContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 118
                self.match(GrewParser.T__12)
                pass

            elif la_ == 2:
                localctx = GrewParser.PositiveArrowContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 119
                self.match(GrewParser.T__13)
                self.state = 120
                self.edgeTypes()
                self.state = 121
                self.match(GrewParser.T__14)
                pass

            elif la_ == 3:
                localctx = GrewParser.NegatedArrowContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 123
                self.match(GrewParser.T__13)
                self.state = 124
                self.match(GrewParser.T__15)
                self.state = 125
                self.edgeTypes()
                self.state = 126
                self.match(GrewParser.T__14)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class EdgeTypesContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def literal(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(GrewParser.LiteralContext)
            else:
                return self.getTypedRuleContext(GrewParser.LiteralContext,i)


        def getRuleIndex(self):
            return GrewParser.RULE_edgeTypes




    def edgeTypes(self):

        localctx = GrewParser.EdgeTypesContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_edgeTypes)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 130
            self.literal()
            self.state = 135
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==7:
                self.state = 131
                self.match(GrewParser.T__6)
                self.state = 132
                self.literal()
                self.state = 137
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class FeatureValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return GrewParser.RULE_featureValue

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class AttributeContext(FeatureValueContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.FeatureValueContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Identifier(self, i:int=None):
            if i is None:
                return self.getTokens(GrewParser.Identifier)
            else:
                return self.getToken(GrewParser.Identifier, i)


    class ValueContext(FeatureValueContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.FeatureValueContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def literal(self):
            return self.getTypedRuleContext(GrewParser.LiteralContext,0)




    def featureValue(self):

        localctx = GrewParser.FeatureValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_featureValue)
        try:
            self.state = 142
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,15,self._ctx)
            if la_ == 1:
                localctx = GrewParser.AttributeContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 138
                self.match(GrewParser.Identifier)
                self.state = 139
                self.match(GrewParser.T__16)
                self.state = 140
                self.match(GrewParser.Identifier)
                pass

            elif la_ == 2:
                localctx = GrewParser.ValueContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 141
                self.literal()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class LiteralContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return GrewParser.RULE_literal

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class PCREContext(LiteralContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.LiteralContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def PCREString(self):
            return self.getToken(GrewParser.PCREString, 0)


    class RegexContext(LiteralContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.LiteralContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def String(self):
            return self.getToken(GrewParser.String, 0)


    class UnicodeStringContext(LiteralContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.LiteralContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def String(self):
            return self.getToken(GrewParser.String, 0)


    class SimpleStringContext(LiteralContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.LiteralContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Identifier(self):
            return self.getToken(GrewParser.Identifier, 0)


    class SubtypeContext(LiteralContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.LiteralContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def Identifier(self, i:int=None):
            if i is None:
                return self.getTokens(GrewParser.Identifier)
            else:
                return self.getToken(GrewParser.Identifier, i)



    def literal(self):

        localctx = GrewParser.LiteralContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_literal)
        try:
            self.state = 152
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,16,self._ctx)
            if la_ == 1:
                localctx = GrewParser.UnicodeStringContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 144
                self.match(GrewParser.String)
                pass

            elif la_ == 2:
                localctx = GrewParser.SimpleStringContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 145
                self.match(GrewParser.Identifier)
                pass

            elif la_ == 3:
                localctx = GrewParser.RegexContext(self, localctx)
                self.enterOuterAlt(localctx, 3)
                self.state = 146
                self.match(GrewParser.T__17)
                self.state = 147
                self.match(GrewParser.String)
                pass

            elif la_ == 4:
                localctx = GrewParser.PCREContext(self, localctx)
                self.enterOuterAlt(localctx, 4)
                self.state = 148
                self.match(GrewParser.PCREString)
                pass

            elif la_ == 5:
                localctx = GrewParser.SubtypeContext(self, localctx)
                self.enterOuterAlt(localctx, 5)
                self.state = 149
                self.match(GrewParser.Identifier)
                self.state = 150
                self.match(GrewParser.T__7)
                self.state = 151
                self.match(GrewParser.Identifier)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class OrderContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return GrewParser.RULE_order

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class PrecedenceContext(OrderContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.OrderContext
            super().__init__(parser)
            self.copyFrom(ctx)



    class ImmediatePrecedenceContext(OrderContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.OrderContext
            super().__init__(parser)
            self.copyFrom(ctx)




    def order(self):

        localctx = GrewParser.OrderContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_order)
        try:
            self.state = 156
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [19]:
                localctx = GrewParser.ImmediatePrecedenceContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 154
                self.match(GrewParser.T__18)
                pass
            elif token in [20]:
                localctx = GrewParser.PrecedenceContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 155
                self.match(GrewParser.T__19)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class CompareContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return GrewParser.RULE_compare

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class EqualityContext(CompareContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.CompareContext
            super().__init__(parser)
            self.copyFrom(ctx)



    class InequalityContext(CompareContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a GrewParser.CompareContext
            super().__init__(parser)
            self.copyFrom(ctx)




    def compare(self):

        localctx = GrewParser.CompareContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_compare)
        try:
            self.state = 160
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [21]:
                localctx = GrewParser.EqualityContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 158
                self.match(GrewParser.T__20)
                pass
            elif token in [22]:
                localctx = GrewParser.InequalityContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 159
                self.match(GrewParser.T__21)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





