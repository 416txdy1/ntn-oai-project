"""Numerical audit accepts observed Fs and preserves three distinct interpolators."""
import importlib.util
from pathlib import Path
import sys
import json
import math
import subprocess
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import audit_runtime_numbers as a

class NumericAuditTests(unittest.TestCase):
    def rows(self):
        rows=[]
        for t in (400,401):
            row=[0.0]*22;row[0]=t;row[1]=10e6+(t-400)*1000;row[4]=100
            row[10]=row[13]=6e6;row[16]=row[17]=-100;row[18]=row[19]=20;row[20]=row[21]=1
            rows.append(row)
        return rows

    def test_three_modes_independent_position_and_velocity(self):
        rows=self.rows()
        linear=a.interpolate(rows,400.5,'legacy-linear')
        hermite=a.interpolate(rows,400.5,'hermite')
        self.assertEqual(linear[1],10000500)
        self.assertEqual(linear[4],100)
        self.assertAlmostEqual(hermite[1],10000500)
        self.assertAlmostEqual(hermite[4],1450)
        self.assertEqual(a.interpolate(rows,400.5,'blend-aware'),hermite)
        with self.assertRaises(ValueError):a.interpolate(rows,400.5,'unknown')

    def test_actual_nondefault_fs_numeric_log(self):
        rows=self.rows()
        delay=8001000/299792458*1000
        doppler=-100/(299792458+100)*2488400000
        log=f'STKTRACE2 DL IQ=0.500000 STK=400.500000 delay={delay:.6f}ms Doppler={doppler:.3f}Hz gain=0.000dB C/N=20.000dB valid=1 samples=1000\n'
        result=a.audit_log(rows,log,'DL',2000,400,1,'legacy-linear')
        self.assertEqual(result['checked_rows'],1)
        with self.assertRaises(ValueError):a.audit_log(rows,log,'DL',4000,400,1,'legacy-linear')

    def test_blend_aware_velocity_is_exported_velocity(self):
        rows=self.rows();rows[1][1]+=500000
        self.assertEqual(a.interpolate(rows,400.5,'blend-aware')[4],100)
        self.assertGreater(a.interpolate(rows,400.5,'hermite')[4],100000)

class LegacyNumericCliTests(unittest.TestCase):
    def run_fixture(self,rate=1,samples=(0,2000),mode='hermite',record_mode=True,declaration=True):
        trace=Path(__file__).resolve().parent/'stk_trace_seamless.csv'
        rows=a.read_rows(trace);fs=1000;epoch=rows[0][0]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);local=root/'local_ntn';local.mkdir()
            result=dict(rate=rate,sample_rate_hz=fs)
            if record_mode:result['interpolation']=mode
            (root/'fixture-result.json').write_text(json.dumps(result))
            for side,direction in [('gnb','UL'),('ue','DL')]:
                lines=['STKRUNTIME sample_rate_hz=1000']
                if declaration:lines.append('STKTRACE2 interpolation='+mode)
                for sample in samples:
                    iq=sample/fs;stk=epoch+rate*iq;row=a.interpolate(rows,stk,mode)
                    delay,vr,_=a.geometry(row,rate);freq=1614900000 if direction=='UL' else 2488400000
                    doppler=-vr/(a.C if direction=='UL' else a.C+vr)*freq
                    power,cn=(17,19) if direction=='UL' else (16,18)
                    lines.append(f'STKTRACE2 {direction} IQ={iq:.6f} STK={stk:.6f} delay={delay:.6f}ms Doppler={doppler:.3f}Hz gain={row[power]-rows[0][power]:.3f}dB C/N={row[cn]:.3f}dB valid=1 samples={sample}')
                (local/(side+'-fixture.log')).write_text('\n'.join(lines)+'\n')
            rg=math.dist(rows[0][1:4],rows[0][10:13]);ta=round(2*rg/a.C/4.072e-9)
            (local/'gnb.local.conf').write_text(f'ta-Common-r17 = {ta};\n')
            (local/'initial_delay_ms.txt').write_text(str(a.geometry(rows[0],0)[0]))
            return subprocess.run([sys.executable,str(Path(a.__file__)), '--run-dir',str(root),
                                   '--labels','fixture','--trace',str(trace)],capture_output=True,text=True)

    def test_old_cli_rejects_frozen_dynamic_even_with_mode(self):
        result=self.run_fixture(samples=(0,0),mode='legacy-linear')
        self.assertNotEqual(result.returncode,0,result.stdout)
        self.assertIn('dynamic trace did not advance',result.stderr)

    def test_old_cli_rejects_explicit_mode_without_declaration(self):
        result=self.run_fixture(samples=(0,2000),mode='legacy-linear',declaration=False)
        self.assertNotEqual(result.returncode,0,result.stdout)
        self.assertIn('recorded interpolation mode mismatch',result.stderr)

    def test_static_frozen_is_permitted_and_one_second_dynamic_is_not(self):
        static=self.run_fixture(rate=0,samples=(0,0))
        self.assertEqual(static.returncode,0,static.stderr)
        dynamic=self.run_fixture(samples=(0,1000))
        self.assertNotEqual(dynamic.returncode,0,dynamic.stdout)

    def test_old_cli_three_modes_nondefault_fs_and_absent_mode_compatibility(self):
        for mode in ('hermite','blend-aware','legacy-linear'):
            result=self.run_fixture(mode=mode)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['sampling_rate_hz'],1000)
        result=self.run_fixture(record_mode=False,declaration=False)
        self.assertEqual(result.returncode,0,result.stderr)

if __name__=='__main__':unittest.main()
