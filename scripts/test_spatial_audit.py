"""解析公式使用可手算场景验算，避免日志格式正确但单位错误。"""
import unittest
from audit_spatial_run import expected_state

class SpatialAuditTests(unittest.TestCase):
    def test_linear_motion(self) -> None:
        row=[0,7000000,0,0,100,0,0,0,0,0,6377900,0,0,6377900,0,0,-100,-100,20,20,1,1]
        end=[1,7000100,*row[2:]]
        for uplink in (False,True):
            result=expected_state([row,end],0.5,1,uplink)
            self.assertAlmostEqual(result['delay_ms'],2*622150/299792458*1000)
            frequency=1614900000 if uplink else 2488400000
            self.assertAlmostEqual(result['doppler_hz'],-100/(299792458 if uplink else 299792558)*frequency)
            self.assertEqual(result['gain_db'],0)
            self.assertEqual(result['cn_db'],20)
        self.assertEqual(expected_state([row,end],0,0,False)['doppler_hz'],0)

if __name__ == '__main__': unittest.main()
