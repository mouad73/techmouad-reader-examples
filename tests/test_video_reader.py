from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'faceless-video-starter'))
import render

class VideoReader(unittest.TestCase):
    def test_malformed_scenes_are_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            for data in [[],{'scenes':'bad'},{'scenes':[None]},{'scenes':{}}]:
                target=Path(tmp)/'out'
                with self.assertRaises(ValueError):render.prepare(data,target)
                self.assertFalse(target.exists())
    def test_strict_scene_types_and_finite_duration(self):
        with tempfile.TemporaryDirectory() as tmp:
            for scene in [{'text':42,'seconds':3},{'text':'text','seconds':True},{'text':'text','seconds':float('nan')},{'text':'text','seconds':'3'}]:
                with self.assertRaises(ValueError):render.prepare({'scenes':[scene]},Path(tmp)/'out')
                self.assertFalse((Path(tmp)/'out').exists())
    def test_missing_ffmpeg_has_actionable_error(self):
        with patch.object(render.shutil,'which',return_value=None):
            with self.assertRaisesRegex(ValueError,'FFmpeg not found in PATH'):render.check_runtime()
    def test_preflight_requires_subtitles_and_encoder(self):
        outputs=[subprocess.CompletedProcess([],0,stdout=' ... subtitles V->V draw subtitles\n'),subprocess.CompletedProcess([],0,stdout=' V....D libx264 H.264\n')]
        with patch.object(render.shutil,'which',return_value='ffmpeg.exe'),patch.object(render.subprocess,'run',side_effect=outputs) as run:
            self.assertEqual(render.check_runtime(),'ffmpeg.exe')
            self.assertEqual(run.call_count,2)
        with patch.object(render.shutil,'which',return_value='ffmpeg.exe'),patch.object(render.subprocess,'run',return_value=subprocess.CompletedProcess([],0,stdout='')):
            with self.assertRaisesRegex(ValueError,'missing subtitles'):render.check_runtime()

if __name__=='__main__':unittest.main()
