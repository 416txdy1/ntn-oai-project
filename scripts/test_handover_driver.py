"""Driver system boundaries and scientific exports without starting NTN resources."""
import json
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parent))
import handover_acceptance as d
import handover_plot as plot


class DriverBoundaryTests(unittest.TestCase):
    def test_environment_contamination_still_refused(self):
        with self.assertRaises(ValueError):
            d.selected_runtime('full','integrated-handover','case-test',{'OAI_NTN_RUN_DIR':'/tmp/original-run'})
        with self.assertRaises(ValueError):
            d.selected_runtime('firsthandover','integrated-handover','case-test',{'OAI_STK_TRACE':str(d.ROOT/'local_ntn/stk_trace_seamless.csv')})

    def test_first_and_legacy_select_real_inputs(self):
        config,_=d.selected_runtime('firsthandover','integrated-handover','case-test',{})
        self.assertEqual(config.trace.name,'stk_trace_firsthandover.csv')
        self.assertIn('firsthandover',str(config.dl_bundle))
        config,_=d.selected_runtime('legacy','legacy-handover','case-test',{})
        self.assertIsNone(config.dl_bundle)

    def test_receiver_crash_missing_end_or_observation_gap_fails(self):
        ready=dict(event='ready',role='receiver',monotonic_ns=100)
        end=dict(event='end',role='receiver',monotonic_ns=1000000000,failed=False)
        self.assertEqual(d.worker_observation([ready,end],'receiver'),[100,1000000000])
        for rows in ([ready],[ready,{**end,'failed':True}],
                     [ready,{**end,'monotonic_ns':3000000000}],
                     [ready,dict(event='error',role='receiver',monotonic_ns=200),end]):
            with self.assertRaises(ValueError):d.worker_observation(rows,'receiver')

    def test_interrupt_handler_restored_and_second_signal_does_not_abort_cleanup(self):
        old={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
        with d.InterruptGuard() as guard:
            with self.assertRaises(RuntimeError):guard.handle(signal.SIGTERM,None)
            guard.handle(signal.SIGINT,None)
        self.assertEqual(old,{sig:signal.getsignal(sig) for sig in old})

    @unittest.skipUnless(sys.platform=='linux','real Linux /proc identity')
    def test_real_owned_child_cleanup_and_reused_identity_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            children=d.OwnedChildren(Path(directory))
            process=children.spawn('fixture',[sys.executable,'-c','import time;time.sleep(30)'],dict(__import__('os').environ))
            try:
                self.assertTrue(children.alive('fixture'))
                with patch.object(d,'process_identity',return_value=('reused',str(Path(sys.executable).resolve()))):
                    with self.assertRaises(RuntimeError):children.signal('fixture',signal.SIGTERM)
                self.assertIsNone(process.poll())
            finally:children.close()
            self.assertIsNotNone(process.poll())


class ScientificTimelineTests(unittest.TestCase):
    def test_wall_inverse_nonuniform_anchors(self):
        anchors=[dict(samples=0,monotonic_ns=10_000_000_000),
                 dict(samples=100,monotonic_ns=11_000_000_000),
                 dict(samples=300,monotonic_ns=13_000_000_000)]
        self.assertEqual(plot.iq_to_wall(anchors,.2,1000),12)
        with self.assertRaises(ValueError):plot.iq_to_wall(anchors,.4,1000)

    def test_export_keeps_startup_unavailable_wall_units_and_static_iq_axis(self):
        anchors=[dict(samples=x*1000,monotonic_ns=(10+x)*1000000000) for x in range(4)]
        observer=SimpleNamespace(manifest={'epoch':8200,'rate':0},fs=1000,
                    anchors={'gnb':anchors,'ue':anchors},
                    numbers={side:[dict(samples=1000,delay_ms=10,doppler_hz=0,cn_db=20,gain_db=0)] for side in ('gnb','ue')},
                    schedules={side:[dict(samples=1000,satellite_id='SAT_A',phase='steady')] for side in ('gnb','ue')})
        packet=dict(sequence=1,send={'iq_bounds_s':[1.1,1.2],'iq_s':1.15},
                    receive={'iq_s':1.25},received=True,send_ns=11150000000,receive_ns=11250000000,bytes=100)
        probes={name:dict(packets=[packet]) for name in ('ping','uplink','downlink')}
        report={'case':'static','clock_max_iq_gap_s':{'gnb':.1,'ue':.1}}
        with tempfile.TemporaryDirectory() as directory:
            result=plot.write_timeline(Path(directory),observer,probes,1,2,report)
            self.assertEqual(result['x_axis'],'iq_elapsed_s')
            text=(Path(directory)/'timeline.csv').read_text()
            self.assertIn('startup_unavailable',text)
            self.assertIn('ping_wall_rtt_ms',text)
            self.assertIn('observed_iq_bits_per_second',text)
            self.assertIn('measured_wall_bits_per_second',text)
            self.assertTrue((Path(directory)/'timeline.png').stat().st_size>1000)
            self.assertTrue((Path(directory)/'timeline.svg').is_file())

if __name__=='__main__':unittest.main()

