"""Actual first callback evidence must bound honest physical coverage."""
import copy
import unittest
from handover_metrics import validate_channel_start, parse_channel_start

class StartTests(unittest.TestCase):
    def fixture(self):
        start=dict(direction='UL',monotonic_ns=123,samples=10083,sampling_rate=7680,iq_s=10083/7680,stk_s=8200+10083/7680)
        clock=dict(start)
        state=dict(direction='UL',samples=10083,iq_s=round(start['iq_s'],6),stk_s=round(start['stk_s'],6),valid=1)
        schedule={key:value for key,value in state.items() if key!='valid'}
        return [start],[clock],[state],[schedule]
    def validate(self,rows):
        return validate_channel_start(*rows,direction='UL',fs=7680,epoch=8200,rate=1,duration=620)
    def test_real_nonzero_start_preserves_counter_and_unknown_interval(self):
        result=self.validate(self.fixture())
        self.assertEqual(result['samples'],10083)
        self.assertEqual(result['startup_unobserved_iq_interval_s'],[0,10083/7680])
    def test_missing_duplicate_wrong_direction_sample_rate_state_and_clock_fail(self):
        for kind in range(10):
            rows=list(copy.deepcopy(self.fixture()))
            if kind==0:rows[0]=[]
            elif kind==1:rows[0]*=2
            elif kind==2:rows[0][0]['direction']='DL'
            elif kind==3:rows[0][0]['sampling_rate']=1000
            elif kind==4:rows[1][0]['monotonic_ns']+=1
            elif kind==5:rows[2][0]['samples']+=1
            elif kind==6:rows[3][0]['direction']='DL'
            elif kind==7:rows[2][0]['valid']=0
            elif kind==8:rows[2][0]['iq_s']+=.000001
            else:rows[0][0]['samples']=620*7680
            with self.assertRaises(ValueError,msg=str(kind)):self.validate(rows)
    def test_nonzero_start_report_and_missing_marker_proof_fail(self):
        from test_handover_metrics import good_report
        import handover_metrics as m
        report=good_report()
        for side in ('gnb','ue'):
            start=report['physical_channel_start'][side]
            start.update(samples=1313,iq_s=1.313,stk_s=8201.313)
            report['iq_interval_s'][side][0]=1.313
            report['startup_unobserved_iq_interval_s'][side]=[0,1.313]
        self.assertEqual(m.evaluate_handover(report),[])
        for field in ('physical_start_verified','physical_channel_start','startup_unobserved_iq_interval_s','rf_case_iq_interval_s'):
            bad=copy.deepcopy(report);del bad[field]
            self.assertTrue(m.evaluate_handover(bad))

    def test_partial_startup_bin_keeps_geometry_unknown(self):
        import csv
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from unittest.mock import patch
        import handover_plot as plot
        anchors=[dict(samples=x,monotonic_ns=1000000000+x*1000000) for x in (1313,1400,1500,2000,2100)]
        observer=SimpleNamespace(manifest={'epoch':8200,'rate':0},fs=1000,
            anchors={side:anchors for side in ('gnb','ue')},
            numbers={side:[dict(samples=1313,delay_ms=10,doppler_hz=0,cn_db=20,gain_db=0),dict(samples=2000,delay_ms=11,doppler_hz=0,cn_db=20,gain_db=0)] for side in ('gnb','ue')},
            schedules={side:[dict(samples=1313,satellite_id='SAT_A',phase='steady')] for side in ('gnb','ue')})
        with tempfile.TemporaryDirectory() as directory,patch.object(plot,'draw'):
            plot.write_timeline(directory,observer,{name:{'packets':[]} for name in ('ping','uplink','downlink')},3,4,{'case':'static','clock_max_iq_gap_s':{'gnb':.1,'ue':.1}})
            with (Path(directory)/'timeline.csv').open() as stream:
                rows=list(csv.DictReader(stream))
        self.assertEqual(rows[0]['gnb_physical_coverage'],'startup_unobserved')
        self.assertEqual(rows[1]['gnb_physical_coverage'],'partial_startup_unobserved')
        self.assertEqual(rows[1]['gnb_delay_ms'],'')
        self.assertEqual(rows[1]['gnb_satellite_id'],'')
        self.assertEqual(rows[2]['gnb_delay_ms'],'11.0')

    def test_marker_parser(self):
        self.assertIsNotNone(parse_channel_start('STKCHANNELSTART UL monotonic_ns=123 samples=10083 sampling_rate=7680.000000000 iq_s=1.312890625 stk_s=8201.312890625'))

if __name__=='__main__':unittest.main()
