import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
post=load('post',ROOT/'facebook-content-starter/build.py')
video=load('video',ROOT/'faceless-video-starter/render.py')

class Starters(unittest.TestCase):
    def story(self): return json.loads((ROOT/'facebook-content-starter/story.example.json').read_text(encoding='utf-8'))
    def test_real_content_requires_review(self):
        story=self.story();story['demo']=False
        with self.assertRaises(ValueError):post.validate(story)
    def test_demo_urls_cannot_be_real_sources(self):
        story=self.story();story.update(demo=False,reviewed=True)
        with self.assertRaises(ValueError):post.validate(story)
    def test_same_domain_is_rejected(self):
        story=self.story();story['sources'][1]['url']='https://www.example.org/other'
        with self.assertRaises(ValueError):post.validate(story)
    def test_missing_caption_rejected(self):
        story=self.story();story['caption']=''
        with self.assertRaises(ValueError):post.validate(story)
    def test_package_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(Path(tmp).resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()))
            target=Path(tmp)/'post';post.build(self.story(),target)
            self.assertTrue((target/'post.png').exists())
            self.assertTrue((target/'preview.html').exists())
            with self.assertRaises(ValueError):post.build(self.story(),target)
    def test_video_rejects_bad_duration(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(Path(tmp).resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()))
            with self.assertRaises(ValueError):video.prepare({'scenes':[{'text':'text','seconds':-1}]},Path(tmp)/'video')
    def test_subtitle_control_characters_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(Path(tmp).resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()))
            folder,duration=video.prepare({'scenes':[{'text':r'{\pos(1,1)}نص','seconds':3}]},Path(tmp)/'video')
            text=(folder/'captions.ass').read_text(encoding='utf-8-sig')
            self.assertNotIn(r'{\pos',text);self.assertEqual(duration,3)

if __name__=='__main__': unittest.main()
