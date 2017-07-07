from hwt.hdlObjects.assignment import Assignment
from hwt.hdlObjects.operator import Operator
from hwt.hdlObjects.statements import IfContainer, SwitchContainer, \
    WhileContainer, WaitStm
from hwt.hdlObjects.types.bits import Bits
from hwt.hdlObjects.types.sliceVal import SliceVal
from hwt.hdlObjects.variables import SignalItem
from hwt.pyUtils.arrayQuery import arr_any
from hwt.serializer.exceptions import SerializerException
from hwt.serializer.serializerClases.indent import getIndent
from hwt.serializer.verilog.utils import verilogTypeOfSig, SIGNAL_TYPE


class VerilogSerializer_statements():
    @classmethod
    def Assignment(cls, a, ctx):
        dst = a.dst
        assert isinstance(dst, SignalItem)

        def valAsHdl(v):
            return cls.Value(v, ctx)

        dstSignalType = verilogTypeOfSig(dst)

        assert not dst.virtualOnly
        if dstSignalType is SIGNAL_TYPE.REG:
            prefix = ""
            symbol = "<="
        else:
            prefix = "assign "
            symbol = "="

        if a.indexes is not None:
            for i in a.indexes:
                if isinstance(i, SliceVal):
                    i = i.clone()
                    i.val = (i.val[0], i.val[1])
                dst = dst[i]

        indent_str = getIndent(ctx.indent)
        dstStr = cls.asHdl(dst, ctx)
        firstPartOfStr = "%s%s%s" % (indent_str, prefix, dstStr)
        if dst._dtype == a.src._dtype:
            return "%s %s %s;" % (firstPartOfStr, symbol, valAsHdl(a.src))
        else:
            srcT = a.src._dtype
            dstT = dst._dtype
            if isinstance(srcT, Bits) and isinstance(dstT, Bits):
                sLen = srcT.bit_length()
                dLen = dstT.bit_length()
                if sLen == dLen:
                    if sLen == 1 and srcT.forceVector != dstT.forceVector:
                        if srcT.forceVector:
                            return "%s %s %s[0];" % (firstPartOfStr, symbol, valAsHdl(a.src))
                        else:
                            return "%s[0] %s %s;" % (firstPartOfStr, symbol, valAsHdl(a.src))
                    elif srcT.signed is not dstT.signed:
                        return "%s %s %s;" % (firstPartOfStr, symbol, valAsHdl(a.src._convSign(dstT.signed)))

            raise SerializerException("%s %s %s is not valid assignment\n because types are different (%r; %r) " % 
                                      (dstStr, symbol, valAsHdl(a.src), dst._dtype, a.src._dtype))


    @classmethod
    def HWProcess(cls, proc, ctx):
        """
        Serialize HWProcess objects
        """
        body = proc.statements
        extraVars = []
        extraVarsSerialized = []

        hasToBeVhdlProcess = extraVars or arr_any(body,
                                                  lambda x: isinstance(x,
                                                                       (IfContainer,
                                                                        SwitchContainer,
                                                                        WhileContainer,
                                                                        WaitStm)) or 
                                                            isinstance(x, Assignment) and x.indexes)

        anyIsEventDependnt = arr_any(proc.sensitivityList, lambda s: isinstance(s, Operator))
        sensitivityList = sorted(map(lambda s: cls.sensitivityListItem(s, None, anyIsEventDependnt),
                                     proc.sensitivityList))

        if hasToBeVhdlProcess:
            childCtx = ctx.withIndent()
        else:
            childCtx = ctx

        def createTmpVarFn(suggestedName, dtype):
            # [TODO] it is better to use RtlSignal
            s = SignalItem(None, dtype, virtualOnly=True)
            s.name = childCtx.scope.checkedName(suggestedName, s)
            s.hidden = False
            serializedS = cls.SignalItem(s, childCtx, declaration=True)
            extraVars.append(s)
            extraVarsSerialized.append(serializedS)
            return s

        childCtx.createTmpVarFn = createTmpVarFn

        statemets = [cls.asHdl(s, childCtx) for s in body]

        if hasToBeVhdlProcess:
            proc.name = ctx.scope.checkedName(proc.name, proc)

        extraVarsInit = []
        for s in extraVars:
            a = Assignment(s.defaultVal, s, virtualOnly=True)
            extraVarsInit.append(cls.Assignment(a, childCtx))

        return cls.processTmpl.render(
            indent=getIndent(ctx.indent),
            name=proc.name,
            hasToBeVhdlProcess=hasToBeVhdlProcess,
            extraVars=extraVarsSerialized,
            sensitivityList=" or ".join(sensitivityList),
            statements=extraVarsInit + statemets
            )