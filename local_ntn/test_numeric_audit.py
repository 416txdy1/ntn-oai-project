"""Numerical audit accepts observed Fs and preserves three distinct interpolators."""
import importlib.util
from pathlib import Path
import sys
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

if __name__=='__main__':unittest.main()

