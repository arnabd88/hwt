import unittest
from vhdl_toolkit.tests.synthetisator.interfaceLevel.baseSynthetisatorTC import BaseSynthetisatorTC
from vhdl_toolkit.synthetisator.interfaceLevel.unitFromHdl import UnitFromHdl
from vhdl_toolkit.hdlObjects.typeShortcuts import hInt

ILVL_V = '../../../samples/iLvl/verilog/'

class VerilogCodesignTC(BaseSynthetisatorTC):
    def test_TernOpInModul(self):
        class TernOpInModulSample(UnitFromHdl):
            _hdlSources = ILVL_V + "ternOpInModul.v"        
        u = TernOpInModulSample(debugParser=True)
        self.assertEquals(u.a._dtype.getBitCnt(), 8)
        self.assertEquals(u.b._dtype.getBitCnt(), 1)
        
        u.CONDP.set(hInt(1))
        self.assertEquals(u.a._dtype.getBitCnt(), 4)
        self.assertEquals(u.b._dtype.getBitCnt(), 2)
        
    def test_SizeExpressions(self):
        class SizeExpressionsSample(UnitFromHdl):
            _hdlSources = ILVL_V + "sizeExpressions.v"        
        u = SizeExpressionsSample()
        A = u.paramA.get()
        B = u.paramB.get()
        self.assertEqual(u.portA._dtype.getBitCnt(), A.val)
        self.assertEqual(u.portB._dtype.getBitCnt(), A.val)
        self.assertEqual(u.portC._dtype.getBitCnt(), A.val // 8)
        self.assertEqual(u.portD._dtype.getBitCnt(), (A.val // 8) * 13)
        self.assertEqual(u.portE._dtype.getBitCnt(), B.val * (A.val // 8))
        self.assertEqual(u.portF._dtype.getBitCnt(), B.val * A.val)
        self.assertEqual(u.portG._dtype.getBitCnt(), B.val * (A.val - 4))
    
    def test_InterfaceArray(self):
        class InterfaceArraySample(UnitFromHdl):
            _hdlSources = ILVL_V + "interfaceArrayAxiStream.v"        
        u = InterfaceArraySample()
        self.assertEqual(u.input_axis._multipliedBy, u.LEN)
    
    
    def test_InterfaceArray2(self):
        class InterfaceArraySample(UnitFromHdl):
            _hdlSources = ILVL_V + "interfaceArrayAxi4.v"        
        u = InterfaceArraySample()
        self.assertEqual(u.s_axi._multipliedBy, u.C_NUM_SLAVE_SLOTS)
    
    
if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(VerilogCodesignTC('test_InterfaceArray2'))
    # suite.addTest(unittest.makeSuite(VhdlCodesignTC))
    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)