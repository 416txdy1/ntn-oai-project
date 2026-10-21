"""Media-command contracts: preserve source, require audio, and retain legacy demo."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('demo',Path(__file__).with_name('demo.py'))
demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)


class AudioCommandTests(unittest.TestCase):
    def test_source_is_one_literal_argument_and_read_only(self):
        source=Path('/mnt/d/Program Files/影片/clip [1];$test.mp4')
        args=demo.publisher_arguments('/isolated/ffmpeg',source)
        self.assertEqual(args[args.index('-i')+1],str(source))
        self.assertEqual(args[args.index('-stream_loop')+1],'-1')
        self.assertIn('-re',args)
        self.assertNotIn('-y',args)
        self.assertEqual(args[-1],'rtsp://127.0.0.1:8554/live')

    def test_audio_is_mandatory_and_opus_stereo(self):
        args=demo.publisher_arguments('/ffmpeg',Path('/source.mp4'))
        self.assertIn('0:a:0',args)
        self.assertNotIn('-an',args)
        self.assertEqual(args[args.index('-c:a')+1],'libopus')
        self.assertEqual(args[args.index('-ar')+1],'48000')
        self.assertEqual(args[args.index('-ac')+1],'2')

    def test_synthetic_entry_stays_video_only(self):
        args=demo.publisher_arguments('/ffmpeg')
        self.assertIn('-an',args)
        self.assertNotIn('-stream_loop',args)
        self.assertEqual(args[args.index('-i')+1],'testsrc=size=426x240:rate=15')

    def test_receiving_packets_without_play_clock_is_not_audio_pass(self):
        rows=[dict(browser_ms=i*1000,audio_samples_received=100000+i*100,audio_total_energy=1,audio_track_live=True,
                   audio_muted=False,audio_volume=.15,audio_bytes_received=1000*i,audio_playout_samples=100000) for i in range(20)]
        self.assertFalse(demo.audio_quality(rows,[])['passed'])
        for i,row in enumerate(rows):row['audio_samples_received']=100000+i*48000
        self.assertTrue(demo.audio_quality(rows,[])['passed'])
        rows[-1]['audio_muted']=True
        self.assertFalse(demo.audio_quality(rows,[])['passed'])


if __name__=='__main__':unittest.main()
