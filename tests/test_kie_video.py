import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('kie_video',Path(__file__).resolve().parents[1]/'kie-video-starter/video.py')
video=importlib.util.module_from_spec(spec);spec.loader.exec_module(video)

class KieVideoTests(unittest.TestCase):
    def test_create_checks_budget_before_network(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError): video.create_once(Path(folder)/'state.json',video.payload('plant'),'test',1,lambda *a:self.fail('network'))
    def test_ambiguous_create_is_not_repeated(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.json';calls=[]
            def transport(endpoint,*args):
                calls.append(endpoint)
                if endpoint=='chat/credit': return 100
                raise RuntimeError('timeout')
            with self.assertRaises(RuntimeError): video.create_once(path,video.payload('plant'),'test',54,transport)
            with self.assertRaises(ValueError): video.create_once(path,video.payload('plant'),'test',54,transport)
            self.assertEqual(calls,['chat/credit','jobs/createTask'])
    def test_success_receipt_survives_polling(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.json'
            def transport(endpoint,*args): return 100 if endpoint=='chat/credit' else {'taskId':'test-1'}
            video.create_once(path,video.payload('plant'),'test',54,transport)
            result=video.poll_once(path,'test',lambda *a:{'state':'success','creditsConsumed':54,'resultJson':json.dumps({'resultUrls':['https://example.com/video.mp4']})})
            self.assertEqual(result['actualCredits'],54);self.assertEqual(json.loads(path.read_text())['phase'],'success')
    def test_missing_result_never_becomes_success(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.json';path.write_text('{"taskId":"test-1","phase":"submitted"}')
            with self.assertRaises(RuntimeError): video.poll_once(path,'test',lambda *a:{'state':'success','resultJson':'{}'})
            self.assertEqual(json.loads(path.read_text())['phase'],'submitted')
    def test_invalid_prompt_and_local_media_urls_are_rejected(self):
        for prompt in ['', 'a'*2501]:
            with self.assertRaises(ValueError):video.payload(prompt)
        for url in ['http://example.com/a.mp4','https://u:p@example.com/a.mp4','https://127.0.0.1/a.mp4']:
            with self.assertRaises(ValueError):video.public_url(url)
    def test_existing_task_cannot_be_recreated(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.json';path.write_text('{"taskId":"existing"}')
            with self.assertRaises(ValueError):video.create_once(path,video.payload('plant'),'test',54,lambda *a:self.fail('network'))

if __name__=='__main__':unittest.main()
