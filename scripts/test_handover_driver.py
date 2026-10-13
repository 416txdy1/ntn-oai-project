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
    def test_actual_stock_snat_selects_exact_peer_and_rejects_unexpected_rules(self):
        rule='-P POSTROUTING ACCEPT\n-A POSTROUTING -s 12.2.1.0/24 -o eth0 -j SNAT --to-source 192.168.71.134\n'
        self.assertEqual(d.snat_peer(rule,'12.2.1.0/24','12.2.1.2','192.168.71.134'),'192.168.71.134')
        self.assertEqual(d.snat_peer('-P POSTROUTING ACCEPT\n','12.2.1.0/24','12.2.1.2','192.168.71.134'),'12.2.1.2')
        for changed in (rule.replace('192.168.71.134','192.168.71.99'),rule.replace('eth0','foreign'),rule+rule,
                        '-A POSTROUTING -s 0.0.0.0/0 -j MASQUERADE',rule.replace('SNAT','ACCEPT')):
            with self.assertRaises(ValueError):d.snat_peer(changed,'12.2.1.0/24','12.2.1.2','192.168.71.134')

    def test_stock_docker_dns_jump_and_only_exact_loopback_exception(self):
        rules="""-P PREROUTING ACCEPT
-P INPUT ACCEPT
-P OUTPUT ACCEPT
-P POSTROUTING ACCEPT
-N DOCKER_OUTPUT
-N DOCKER_POSTROUTING
-A OUTPUT -d 127.0.0.11/32 -j DOCKER_OUTPUT
-A POSTROUTING -d 127.0.0.11/32 -j DOCKER_POSTROUTING
-A POSTROUTING -s 12.2.1.0/24 -o eth0 -j SNAT --to-source 192.168.71.134
-A DOCKER_OUTPUT -d 127.0.0.11/32 -p tcp -m tcp --dport 53 -j DNAT --to-destination 127.0.0.11:43995
-A DOCKER_OUTPUT -d 127.0.0.11/32 -p udp -m udp --dport 53 -j DNAT --to-destination 127.0.0.11:37342
-A DOCKER_POSTROUTING -s 127.0.0.11/32 -p tcp -m tcp --sport 43995 -j SNAT --to-source :53
-A DOCKER_POSTROUTING -s 127.0.0.11/32 -p udp -m udp --sport 37342 -j SNAT --to-source :53
"""
        self.assertEqual(d.snat_peer(rules,'12.2.1.0/24','12.2.1.2','192.168.71.134'),'192.168.71.134')
        self.assertEqual(d.snat_peer('\n'.join(reversed(rules.splitlines())),'12.2.1.0/24','12.2.1.2','192.168.71.134'),'192.168.71.134')
        jump='-A POSTROUTING -d 127.0.0.11/32 -j DOCKER_POSTROUTING'
        for unsafe in ('-A POSTROUTING -j DOCKER_POSTROUTING',jump.replace('127.0.0.11/32','192.168.71.135/32'),jump.replace('127.0.0.11/32','127.0.0.0/8'),jump.replace('DOCKER_POSTROUTING','FOREIGN'),jump+' -o eth0'):
            with self.assertRaises(ValueError):d.snat_peer(rules.replace(jump,unsafe),'12.2.1.0/24','12.2.1.2','192.168.71.134')

    def test_snat_proof_requires_owned_ids_routes_and_stable_namespace(self):
        from unittest.mock import Mock
        config=SimpleNamespace(core_project='ntn-qd-integrated',ext_dn_container='ntn-qd-integrated-oai-ext-dn',
          gnb_ip_cidr='192.168.71.129/26',ext_dn_ip='192.168.71.135',ue_pdu_subnet='12.2.1.0/24')
        upf={'Name':'/ntn-qd-integrated-oai-upf','Id':'upf-owned','owned':True,'State':{'Pid':11,'Running':True,'Health':{'Status':'healthy'}}}
        dn={'Name':'/ntn-qd-integrated-oai-ext-dn','Id':'dn-owned','owned':True,'State':{'Pid':22,'Running':True,'Health':{'Status':'healthy'}}}
        rule='-A POSTROUTING -s 12.2.1.0/24 -o eth0 -j SNAT --to-source 192.168.71.134'
        forward=[{'dev':'eth0','prefsrc':'192.168.71.134'}]
        reverse=[{'dev':'eth0','gateway':'192.168.71.134','prefsrc':'192.168.71.135'}]
        lab=Mock();lab.preflight.return_value=([upf,dn],[]);lab.read_owner.return_value={'config_hash':'verified'}
        lab.own_container.side_effect=lambda item:item['owned']
        def output(argv):
            if 'iptables' in argv:return rule
            if 'addr' in argv:return json.dumps([{'addr_info':[{'local':'192.168.71.134'}]}])
            return json.dumps(forward if argv[2]=='11' else reverse)
        with patch.object(d,'CoreLab',return_value=lab),patch.object(d,'process_identity',side_effect=lambda pid:('start',str(pid))),patch.object(d,'network_inode',side_effect=lambda pid:pid+100),patch.object(d,'path_output',side_effect=output):
            proof=d.verified_uplink_path(config,'12.2.1.2',22,('start','22'))
            self.assertTrue(proof['snat_verified']);self.assertEqual(proof['uplink_expected_peer'],'192.168.71.134')
            self.assertEqual(proof['original_pdu_address'],'12.2.1.2')
            upf['owned']=False
            with self.assertRaises(ValueError):d.verified_uplink_path(config,'12.2.1.2',22,('start','22'))
            upf['owned']=True;reverse[0]['gateway']='192.168.71.99'
            with self.assertRaises(ValueError):d.verified_uplink_path(config,'12.2.1.2',22,('start','22'))
            reverse[0]['gateway']='192.168.71.134'
            with patch.object(d,'network_inode',side_effect=[111,122,999,122]):
                with self.assertRaises(ValueError):d.verified_uplink_path(config,'12.2.1.2',22,('start','22'))
            lab.preflight.side_effect=ValueError('owner ID/config mismatch')
            with self.assertRaises(ValueError):d.verified_uplink_path(config,'12.2.1.2',22,('start','22'))

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

    def test_actual_production_rrc_idle_and_ra_only_after_pdu(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);gnb=root/'gnb.log';ue=root/'ue.log'
            gnb.write_text('');ue.write_text('RRC moved into IDLE state\nInitialization of 4-Step CBRA procedure\n')
            observer=d.Observer({'logs':{'gnb':str(gnb),'ue':str(ue)},'sample_rate_hz':None,'epoch':8200,'rate':1})
            observer.update()
            self.assertEqual(observer.rrc_idle,0);self.assertEqual(observer.reaccess_count,0)
            with ue.open('a') as stream:
                stream.write('Received PDU Session Establishment Accept, UE IPv4: 12.2.1.2\nRRC moved into IDLE state\nTriggering new RA procedure for UE with RNTI fixture\n')
            observer.update()
            self.assertEqual(observer.rrc_idle,1);self.assertEqual(observer.reaccess_count,1)

    def test_launch_interruption_cleans_only_matching_selected_manifest(self):
        import os
        for matching in (True,False):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);run=root/'run'
                config=SimpleNamespace(root=root,run_dir=run,state_file=run/'processes.json',
                                       profile='integrated-handover',run_id='interrupt-test')
                launch=__import__('unittest.mock',fromlist=['Mock']).Mock()
                launch.poll.side_effect=RuntimeError('controlled interruption fixture')
                class Children:
                    def __init__(self,output):self.closed=False
                    def spawn(self,*_args):
                        (run/'run.json').write_text(json.dumps({'run_id':'interrupt-test' if matching else 'foreign',
                            'profile':config.profile,'workspace':str(root),'logs':{}}))
                        config.state_file.write_text('{}')
                        return launch
                    def close(self):self.closed=True
                    def evidence(self):return {}
                with patch.object(d.os,'geteuid',return_value=0),patch.object(d,'selected_runtime',return_value=(config,{})),\
                     patch.object(d,'OwnedChildren',Children),patch.object(d.subprocess,'run',return_value=__import__('subprocess').CompletedProcess([],0,'','')) as stop:
                    self.assertEqual(d.main(['--run-id','interrupt-test']),1)
                    self.assertEqual(stop.call_count,int(matching))
                    if matching:
                        argv=stop.call_args.args[0]
                        self.assertIn('stop',argv);self.assertIn('integrated-handover',argv);self.assertIn('interrupt-test',argv)
                result=json.loads((run/'acceptance/report.json').read_text())
                self.assertFalse(result['passed'])

    def test_receiver_crash_missing_end_or_observation_gap_fails(self):
        ready=dict(event='ready',role='receiver',monotonic_ns=100)
        end=dict(event='end',role='receiver',monotonic_ns=1000000000,failed=False,received_datagrams=0)
        self.assertEqual(d.worker_observation([ready,end],'receiver'),[100,1000000000])
        for rows in ([ready],[ready,{**end,'failed':True}],
                     [ready,{**end,'monotonic_ns':3000000000}],
                     [ready,dict(event='error',role='receiver',monotonic_ns=200),end]):
            with self.assertRaises(ValueError):d.worker_observation(rows,'receiver')

    def test_numeric_and_schedule_observation_gaps_cannot_pass(self):
        from handover_metrics import case_spec
        numbers=[dict(samples=999+i*1000,iq_s=.999+i,stk_s=8200+.999+i,valid=1) for i in range(620)]
        schedule=[dict(samples=999+i*1000,iq_s=.999+i,stk_s=8200+.999+i,
                       phase='complete' if i in (44,599) else 'steady') for i in range(620)]
        observer=SimpleNamespace(fs=1000,numbers={'gnb':numbers,'ue':numbers},
                                 schedules={'gnb':schedule,'ue':schedule})
        observer.manifest={'epoch':8200,'rate':1}
        observer.channel_starts={}
        observer.anchors={}
        for side in ('gnb','ue'):
            direction='UL' if side=='gnb' else 'DL'
            observer.numbers[side]=[dict(row,direction=direction) for row in numbers]
            observer.schedules[side]=[dict(row,direction=direction) for row in schedule]
            start=dict(direction=direction,monotonic_ns=100, samples=999,sampling_rate=1000,iq_s=.999,stk_s=8200.999)
            observer.channel_starts[side]=[start];observer.anchors[side]=[dict(start)]
        numbers=observer.numbers['ue'];schedule=observer.schedules['ue']
        d.validate_physical_observations(observer,case_spec('full'))
        observer.numbers['ue']=numbers[:40]+numbers[41:]
        with self.assertRaises(ValueError):d.validate_physical_observations(observer,case_spec('full'))
        observer.numbers['ue']=numbers
        observer.schedules['ue']=[row for row in schedule if row['phase']!='complete']
        with self.assertRaises(ValueError):d.validate_physical_observations(observer,case_spec('full'))

    def test_drain_reserve_uses_observed_wall_to_iq_rate_and_preserves_windows(self):
        from handover_metrics import case_spec
        def rows(factor):
            return [dict(samples=100000+i*100,monotonic_ns=10000000000+int(i*.1/factor*1e9)) for i in range(31)]
        for factor,expected in [(1,612),(.1,615)]:
            self.assertAlmostEqual(d.tail_stop_iq(case_spec('full'),{'gnb':rows(factor),'ue':rows(factor)},1000),expected)
        with self.assertRaises(ValueError):d.tail_stop_iq(case_spec('full'),{'gnb':rows(3),'ue':rows(3)},1000)

    def test_sender_event_gap_cannot_be_hidden_by_heartbeat(self):
        rows=[dict(event='ready',role='sender',monotonic_ns=100,offered_wall_bits_per_second=100000),
              dict(event='send',role='sender',monotonic_ns=200,sequence=2,send_ns=190,bytes=1000),
              dict(event='end',role='sender',monotonic_ns=300,sent=1,failed=False)]
        with self.assertRaises(ValueError):d.worker_observation(rows,'sender')

    def test_udp_workload_requires_real_pacing_and_complete_bytes(self):
        def fixture(rate=100000,count=101):
            period=8000/rate
            sends=[dict(event='send',sequence=i+1,send_ns=10_000_000_000+round(i*period*1e9),
                        monotonic_ns=10_000_000_000+round(i*period*1e9)+100,bytes=1000) for i in range(count)]
            return [dict(event='ready',offered_wall_bits_per_second=100000,payload_bytes=1000)]+sends+[
                dict(event='end',sent=count,sent_bytes=count*1000)]
        for rate in (95000,100000,105000):
            result=d.validate_udp_workload(fixture(rate))
            self.assertAlmostEqual(result['actual_offered_wall_bits_per_second'],rate,places=3)
            self.assertEqual(result['sender_bytes'],101000)
        for rows in (fixture(1000),fixture(count=2),fixture(count=1)):
            with self.assertRaises(ValueError):d.validate_udp_workload(rows)
        for field,value in [('sent',100),('sent_bytes',100000)]:
            rows=fixture();rows[-1][field]=value
            with self.assertRaises(ValueError):d.validate_udp_workload(rows)
        rows=fixture();rows[50]['bytes']=999
        with self.assertRaises(ValueError):d.validate_udp_workload(rows)
        rows=fixture();rows[50]['send_ns']=rows[49]['send_ns']
        with self.assertRaises(ValueError):d.validate_udp_workload(rows)
        rows=fixture()
        for i,row in enumerate(rows[1:-1]):row['send_ns']=10_000_000_000+(i*40_000_000 if i<50 else i*40_000_000+4_000_000_000)
        with self.assertRaises(ValueError):d.validate_udp_workload(rows)

    def test_final_report_keeps_loss_before_confirmed_business_and_two_full_windows(self):
        from handover_metrics import ClockMap,evaluate_handover
        from test_handover_metrics import good_report
        anchors=[dict(samples=i*100,monotonic_ns=10000000000+i*100000000,sampling_rate=1000,
                      iq_s=i*.1,stk_s=8200+i*.1,direction='DL') for i in range(6203)]
        observer=SimpleNamespace(fs=1000,manifest={'epoch':8200,'rate':1},
                   anchors={'gnb':anchors,'ue':anchors},pbch_errors=0,rrc_idle=0,reaccess_count=0,
                   qd_loaded={'gnb':1,'ue':1},
                   mapper=lambda side:ClockMap(anchors,8200,1,1000))
        observer.anchors['gnb']=[dict(row,direction='UL') for row in anchors]
        observer.channel_starts={side:[dict(observer.anchors[side][0])] for side in ('gnb','ue')}
        observer.numbers={side:[dict(observer.anchors[side][0],valid=1)] for side in ('gnb','ue')}
        observer.schedules={side:[dict(observer.anchors[side][0])] for side in ('gnb','ue')}
        stop_ns=625000000000;drain_ns=630000000000
        def events(role,sends,receives,end_ns):
            ready=dict(event='ready',role=role,monotonic_ns=21000000000,offered_wall_bits_per_second=100000,payload_bytes=1000)
            body=[{**event,'role':role} for event in sends+receives]
            heartbeats=[dict(event='heartbeat',role=role,monotonic_ns=t) for t in range(22000000000,end_ns,1000000000)]
            body.sort(key=lambda event:event['monotonic_ns'])
            body+=heartbeats;body.sort(key=lambda event:event['monotonic_ns'])
            return [ready]+body+[dict(event='end',role=role,monotonic_ns=end_ns,failed=False,
                                      sent=len(sends),sent_bytes=sum(row['bytes'] for row in sends),received=len({event['sequence'] for event in receives}),
                                      received_datagrams=len(receives))]
        def traffic(step,missing_first=False):
            sends=[];receives=[]
            count=int((615-11.2)/step)
            for index in range(count):
                seq=index+1;ns=10000000000+int((11.2+index*step)*1000000000)
                sends.append(dict(event='send',sequence=seq,send_ns=ns,monotonic_ns=ns+100,bytes=1000))
                if not (missing_first and seq==1):
                    receives.append(dict(event='receive',sequence=seq,send_ns=ns,receive_ns=ns+10000000,
                                         monotonic_ns=ns+10000100,bytes=1000))
            return sends,receives
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)
            for direction in ('uplink','downlink'):
                sends,receives=traffic(.08)
                (output/(direction+'-sender.jsonl')).write_text('\n'.join(json.dumps(row) for row in events('sender',sends,[],stop_ns))+'\n')
                (output/(direction+'-receiver.jsonl')).write_text('\n'.join(json.dumps(row) for row in events('receiver',[],receives,drain_ns))+'\n')
            sends,receives=traffic(1,True)
            (output/'ping.jsonl').write_text('\n'.join(json.dumps(row) for row in events('ping',sends,receives,drain_ns))+'\n')
            report=good_report()
            with patch.object(d,'write_timeline',return_value={'fixture':True}):
                d.build_report(report,observer,output,{'pdu_ns':20000000000,'traffic_ns':21200000000},
                               stop_ns,drain_ns,{})
            self.assertEqual(report['ping']['lost_packets'],1)
            self.assertEqual(report['ping']['sent'],len(sends))
            self.assertGreater(report['traffic_ready_iq_s'],12)
            self.assertTrue(all(window['coverage_ok'] for window in report['windows']))
            self.assertEqual(evaluate_handover(report),[])

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
