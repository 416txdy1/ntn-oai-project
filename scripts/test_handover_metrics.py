"""Evidence-based cohort, clock, tail and complete-case regression tests."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import handover_metrics as m
import continuous_udp as u


def anchor(ns, samples, epoch=8200, rate=1, fs=1000):
    return dict(monotonic_ns=ns, samples=samples, sampling_rate=fs,
                iq_s=samples/fs, stk_s=epoch+rate*samples/fs, direction='DL')


def good_report(case='full'):
    spec=m.case_spec(case)
    qd=case != 'legacy'
    counters=dict(sent=1000, received=1000, packets=1000, lost_packets=0,
                  definite_sent=1000, loss_upper_bound=0.0,
                  observation_ok=True)
    return dict(case=case, qd_enabled=qd, profile='legacy-handover' if not qd else 'integrated-handover',
                rate=spec['rate'], sample_rate_hz=1000, clock_sample_rates={'gnb':1000,'ue':1000},
                trace_interval_s=spec['trace_interval_s'], iq_interval_s={'gnb':[0,spec['duration_iq_s']], 'ue':[0,spec['duration_iq_s']]},
                pdu_ready_stk_s=8210, traffic_ready_stk_s=8211,
                pdu_ready_iq_s=10, traffic_ready_iq_s=11,
                business_iq_interval_s=[11,spec['duration_iq_s']-5],
                iq_end_stk_s={'gnb':spec['trace_interval_s'][0]+spec['rate']*spec['duration_iq_s'],
                              'ue':spec['trace_interval_s'][0]+spec['rate']*spec['duration_iq_s']},
                pdu_address_changes=0, pbch_errors=0, rrc_idle=0, reaccess_count=0,
                numeric_audit_ok=True, clock_observation_ok=True, worker_observation_ok=True, stop_exit=0,
                ping=copy.deepcopy(counters), udp={'uplink':copy.deepcopy(counters),'downlink':copy.deepcopy(counters)},
                windows=[dict(complete_stk_s=x, start_stk_s=x-5, end_stk_s=x+5,
                              coverage_ok=True, ping=copy.deepcopy(counters),
                              udp={'uplink':copy.deepcopy(counters),'downlink':copy.deepcopy(counters)})
                         for x in spec['completions']])


class ClockTests(unittest.TestCase):
    def test_nonuniform_bracket_and_nonzero_epoch(self):
        mapper=m.ClockMap([anchor(10_000_000_000,0),anchor(11_000_000_000,100),
                           anchor(13_000_000_000,300)],8200,1,1000)
        event=mapper.map(12_000_000_000)
        self.assertAlmostEqual(event['iq_s'],.2)
        self.assertAlmostEqual(event['stk_s'],8200.2)
        self.assertEqual(event['iq_bounds_s'],[.1,.3])
        self.assertAlmostEqual(event['real_time_factor'],.1)

    def test_static_retains_iq_progress(self):
        mapper=m.ClockMap([anchor(10_000_000_000,0,rate=0),anchor(11_000_000_000,100,rate=0)],8200,0,1000)
        event=mapper.map(10_500_000_000)
        self.assertEqual(event['stk_bounds_s'],[8200,8200])
        self.assertAlmostEqual(event['iq_s'],.05)

    def test_no_extrapolation_clock_regression_wrong_fs_or_mapping(self):
        mapper=m.ClockMap([anchor(10,0),anchor(20,100)],8200,1,1000)
        with self.assertRaises(ValueError):mapper.map(21)
        for rows in ([anchor(20,0),anchor(10,100)],
                     [anchor(10,100),anchor(20,0)],
                     [anchor(10,0),anchor(20,100,fs=2000)],
                     [anchor(10,0),{**anchor(20,100),'stk_s':9999}]):
            with self.assertRaises(ValueError):m.ClockMap(rows,8200,1,1000)

    def test_iq_gap_detected(self):
        with self.assertRaises(ValueError):
            m.ClockMap([anchor(10,0),anchor(20,1000)],8200,1,1000,max_iq_gap=.15)


class CohortTests(unittest.TestCase):
    def packet(self,seq,lo,hi,received=True,late=False):
        return dict(sequence=seq, send=dict(iq_bounds_s=[lo,hi],iq_s=(lo+hi)/2),
                    received=received, deadline_timeout=late, late_received=received and late,
                    bytes=100, send_ns=seq*1000000000, receive_ns=seq*1000000000+5000000 if received else None)

    def test_boundary_received_not_artificial_loss(self):
        rows=[self.packet(1,.2,.3),self.packet(2,-.01,.01),self.packet(3,.99,1.01)]
        result=m.cohort_summary(rows,0,1)
        self.assertEqual(result['definite_sent'],1)
        self.assertEqual(result['boundary_ambiguous_sent'],2)
        self.assertEqual(result['loss_upper_bound'],0)

    def test_possible_window_missing_increases_worst_loss(self):
        rows=[self.packet(x,.2,.3) for x in range(1,100)]
        rows += [self.packet(100,-.01,.01,False),self.packet(101,.99,1.01,False)]
        self.assertGreater(m.cohort_summary(rows,0,1)['loss_upper_bound'],.01)

    def test_all_ambiguous_not_valid_window(self):
        result=m.cohort_summary([self.packet(1,-.01,.01)],0,1)
        self.assertFalse(result['observation_ok'])

    def test_late_preserves_timeout_and_eventual_delivery(self):
        result=m.cohort_summary([self.packet(1,.2,.3,True,True)],0,1)
        self.assertEqual(result['deadline_timeouts'],1)
        self.assertEqual(result['late_received'],1)
        self.assertEqual(result['eventual_missing'],0)


class ProbeTests(unittest.TestCase):
    def test_codec_nonce_direction_and_truncation(self):
        wire=u.encode_packet(b'12345678','uplink',7,1234,200)
        self.assertEqual(len(wire),200)
        self.assertEqual(u.decode_packet(wire,b'12345678','uplink'),(7,1234,200))
        for data,token,direction in [(wire[:10],b'12345678','uplink'),
                                     (wire,b'87654321','uplink'),(wire,b'12345678','downlink')]:
            with self.assertRaises(ValueError):u.decode_packet(data,token,direction)

    def test_unknown_duplicate_late_missing_and_out_of_order(self):
        sends=[dict(event='send',sequence=x,send_ns=x*100,monotonic_ns=x*100,bytes=100) for x in (1,2,3)]
        receives=[dict(event='receive',sequence=x,send_ns=x*100,monotonic_ns=t,bytes=100)
                  for x,t in [(2,500),(1,600),(1,650),(9,700)]]
        result=u.match_events(sends,receives,deadline_ns=200,drain_end_ns=800)
        self.assertEqual(result['unknown_receives'],1)
        self.assertEqual(result['duplicates'],1)
        self.assertEqual(result['out_of_order'],1)
        self.assertEqual(result['packets'][2]['received'],False)
        self.assertTrue(result['packets'][0]['late_received'])
        self.assertTrue(result['packets'][0]['deadline_timeout'])

    def test_after_drain_not_claimed_received(self):
        result=u.match_events([dict(event='send',sequence=1,send_ns=100,monotonic_ns=100,bytes=100)],
                              [dict(event='receive',sequence=1,send_ns=100,monotonic_ns=900,bytes=100)],200,800)
        self.assertFalse(result['packets'][0]['received'])

    def test_missing_receiver_report_rejected(self):
        with self.assertRaises(ValueError):u.match_events([],None,200,800)


class AcceptanceTests(unittest.TestCase):
    def test_each_case_is_explicit_and_full_unchanged(self):
        for case in ('full','firsthandover','static','legacy'):
            self.assertEqual(m.evaluate_handover(good_report(case)),[],case)
        self.assertEqual(m.case_spec('full')['duration_iq_s'],620)
        self.assertEqual(m.case_spec('full')['completions'],[8244,8799])
        self.assertEqual(m.case_spec('firsthandover')['duration_iq_s'],70)

    def test_required_evidence_missing_fails(self):
        for key in ('ping','udp','windows','sample_rate_hz','numeric_audit_ok','iq_interval_s',
                    'pdu_ready_stk_s','traffic_ready_stk_s','worker_observation_ok'):
            report=good_report();del report[key]
            self.assertTrue(m.evaluate_handover(report),key)

    def test_late_start_incomplete_empty_window_fs_and_reaccess_fail(self):
        mutations=[('traffic_ready_stk_s',8239),('pdu_ready_stk_s',8239),('sample_rate_hz',2000),
                   ('pdu_address_changes',1),('pbch_errors',1),('rrc_idle',1),('reaccess_count',1),
                   ('numeric_audit_ok',False),('clock_observation_ok',False)]
        for key,value in mutations:
            report=good_report();report[key]=value
            self.assertTrue(m.evaluate_handover(report),key)
        report=good_report();report['iq_interval_s']['ue'][1]=619.99
        self.assertTrue(m.evaluate_handover(report))
        report=good_report();report['windows'][1]['ping']['definite_sent']=0
        self.assertTrue(m.evaluate_handover(report))

    def test_threshold_exact_and_just_outside(self):
        report=good_report()
        for item in [report['ping'],report['udp']['uplink'],report['windows'][0]['udp']['downlink']]:
            item['loss_upper_bound']=.01
        self.assertEqual(m.evaluate_handover(report),[])
        report['windows'][0]['udp']['downlink']['loss_upper_bound']=.010001
        self.assertTrue(m.evaluate_handover(report))

    def test_static_needs_thirty_iq_business(self):
        report=good_report('static');report['business_iq_interval_s']=[35,55]
        self.assertTrue(m.evaluate_handover(report))


class TailTests(unittest.TestCase):
    def test_partial_line_incremental_and_rotation_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'log';path.write_text('first\npar')
            tail=m.IncrementalTail(path)
            self.assertEqual(tail.read_lines(),['first'])
            with path.open('a') as f:f.write('tial\nnext\n')
            self.assertEqual(tail.read_lines(),['partial','next'])
            self.assertEqual(tail.read_lines(),[])
            path.rename(path.with_suffix('.old'));path.write_text('replacement\n')
            with self.assertRaises(ValueError):tail.read_lines()


if __name__=='__main__':unittest.main()

