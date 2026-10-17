"""解析公式使用可手算场景验算，避免日志格式正确但单位错误。"""
import unittest
import hashlib
import json
from pathlib import Path
import tempfile
from audit_spatial_run import audit_run, expected_state

class SpatialAuditTests(unittest.TestCase):
    def test_nonzero_trace_start(self) -> None:
        """静止卫星的时延可手算；选错轨迹必须拒绝，不能只匹配日志格式。"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'examples/fdd-pass').mkdir(parents=True)
            (root/'.runtime/reports').mkdir(parents=True)
            (root/'local_ntn').mkdir()
            row = [300,7000000,0,0,0,0,0,0,0,0,6377900,0,0,6377900,0,0,-100,-100,20,20,1,1]
            trace = root/'late.csv'
            trace.write_text('STKTRACE2\n' + '\n'.join(','.join(map(str,[t,*row[1:]])) for t in (300,310)) + '\n')
            (root/'examples/fdd-pass/trace.csv').write_text(trace.read_text().replace('300,','0,').replace('310,','10,'))
            label = 'smoke-0-123'
            (root/'.runtime/reports'/f'{label}.json').write_text(json.dumps({'rate':0,'passed':True}))
            delay = 2*622100/299792458*1000
            for kind, side, ports in (('gnb','UL','1 Tx x 4 Rx'),('ue','DL','4 Tx x 1 Rx')):
                text = 'QDCHANNEL1 spatial ports: '+ports+'\n'
                for iq in (1,2,3):
                    text += f'STKTRACE2 {side} IQ={iq} STK=300 delay={delay:.9f}ms Doppler=0Hz gain=0dB C/N=20dB valid=1 samples={iq*7680000}\n'
                    for port in range(4):
                        text += f'QDCHANNEL1 Tx port {port} IQ={iq} mean_energy=10\n'
                (root/'local_ntn'/f'{kind}-{label}.log').write_text(text)
            with self.assertRaisesRegex(ValueError, '公式验算失败'):
                audit_run(root,label,4)
            result = audit_run(root,label,4,trace)
            self.assertTrue(result['passed'])
            self.assertEqual(result['trace_sha256'],hashlib.sha256(trace.read_bytes()).hexdigest())

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
