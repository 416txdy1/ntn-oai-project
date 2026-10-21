"""Do not count steady labels, partial phases or duplicate completion log lines."""
from pathlib import Path
import tempfile
import unittest
from demo import load_helpers
from replay_handovers import confirmed_handover


def line(phase,iq,satellite='OAI_LEO_P01_S06',switched=0):
    return (f'STKSCHEDULE DL IQ={iq:.6f} STK={8200+iq:.6f} satellite_id={satellite} '
            f'elevation_deg=7.000 visible=1 switched={switched} phase={phase} '
            'previous=OAI_LEO_P01_S06 next=OAI_LEO_P01_S05 samples=100000\n')


class ReplayTests(unittest.TestCase):
    def check_trace(self,rows):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);run=root/'.runtime/runs/integrated-handover/test';run.mkdir(parents=True)
            (run/'ue-live-demo.log').write_text(''.join(rows))
            return confirmed_handover(root,{'tag':'test'},load_helpers())

    def test_complete_sequence(self):
        result=self.check_trace([line('prepare',40),line('blend',41),line('complete',45,'OAI_LEO_P01_S05',1)])
        self.assertTrue(result['verified']);self.assertEqual(len(result['completions']),1)

    def test_steady_label_changes_not_counted(self):
        result=self.check_trace([line('steady',20),line('steady',45,'OAI_LEO_P01_S05',1)])
        self.assertFalse(result['verified'])

    def test_partial_transition_not_counted(self):
        self.assertFalse(self.check_trace([line('prepare',40),line('blend',41)])['verified'])

    def test_repeated_log_line_counted_once(self):
        rows=[line('prepare',40),line('blend',41),line('complete',45,'OAI_LEO_P01_S05',1),line('complete',45.5,'OAI_LEO_P01_S05',1)]
        self.assertEqual(len(self.check_trace(rows)['completions']),1)

    def test_wrong_order_not_counted(self):
        rows=[line('complete',40,'OAI_LEO_P01_S05',1),line('prepare',41),line('blend',42)]
        self.assertFalse(self.check_trace(rows)['verified'])


if __name__=='__main__':unittest.main()
