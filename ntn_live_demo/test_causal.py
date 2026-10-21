"""Guard against claiming causality from playback glitches or failed controls."""
import copy
import unittest
from causal import assess_pair, rate


def observation(ingress=50000, fps=15, cn=17, freeze=0):
    return dict(ingress_samples=12,player_samples=12,workers_alive=True,ingress_resets=0,publisher_realtime_progress_ratio=1.,
                ingress_bytes_per_wall_s=ingress,decoded_frames_per_wall_s=fps,
                median_input_dl_cn_db=cn,freeze_wall_s=freeze)


class CausalityTests(unittest.TestCase):
    def assess(self, changed, **kwargs):
        return assess_pair(observation(),changed,observation(),observation(),kwargs.get('coverage',True),kwargs.get('protection',True))

    def test_no_effect_is_inconclusive(self):
        self.assertEqual(self.assess(observation(cn=1))['status'],'INCONCLUSIVE')

    def test_local_player_freeze_is_not_channel_evidence(self):
        self.assertEqual(self.assess(observation(fps=0,freeze=8))['status'],'INCONCLUSIVE')

    def test_input_noise_without_business_change_is_not_proof(self):
        self.assertFalse(self.assess(observation(cn=1,freeze=8))['ue_media_ingress_reduction'])

    def test_paired_channel_ingress_and_video_effect(self):
        self.assertEqual(self.assess(observation(ingress=1000,fps=0,cn=1,freeze=8))['status'],'SUPPORTED')

    def test_worker_failure_invalidates_causal_claim(self):
        changed=observation(ingress=1000,fps=0,cn=1,freeze=8);changed['workers_alive']=False
        self.assertEqual(self.assess(changed)['status'],'INVALID')

    def test_counter_reset_does_not_become_false_loss(self):
        changed=observation(ingress=1000,fps=0,cn=1,freeze=8);changed['ingress_resets']=1
        self.assertEqual(self.assess(changed)['status'],'INCONCLUSIVE')

    def test_missing_coverage_invalidates(self):
        self.assertEqual(self.assess(observation(ingress=1000,fps=0,cn=1,freeze=8),coverage=False)['status'],'INVALID')

    def test_stalled_encoder_invalidates(self):
        changed=observation(ingress=1000,fps=0,cn=1,freeze=8);changed['publisher_realtime_progress_ratio']=.05
        self.assertEqual(self.assess(changed)['status'],'INVALID')

    def test_rate_uses_wall_time_not_iq_time(self):
        rows=[dict(bytes=0,wall_s=10,iq_s=1),dict(bytes=400,wall_s=12,iq_s=2)]
        self.assertEqual(rate(rows,'bytes','wall_s'),200)


if __name__=='__main__':unittest.main()
