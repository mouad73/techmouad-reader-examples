import importlib.util
from contextlib import closing
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'facebook-content-starter'))
import build
spec = importlib.util.spec_from_file_location('facebook_publish', ROOT/'facebook-content-starter/publish.py')
pub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pub)


class Publisher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.story = {'demo': False, 'reviewed': True, 'title': 'منشور عربي موثق', 'caption': 'نص الاختبار بعد المراجعة', 'sources': [{'title': 'Python', 'url': 'https://docs.python.org/3/'}, {'title': 'Pillow', 'url': 'https://pillow.readthedocs.io/'}]}
        self.folder = build.build(self.story, self.root/'post')
        self.item = pub.package(self.folder)
        self.config = {'page': '123456', 'token': 'TEST_ONLY_NOT_A_REAL_TOKEN', 'version': 'v26.0'}
        self.state = self.root/'shared.sqlite3'
        self.calls = []

    def transport(self, config, method, path, fields=None, photo=None):
        self.calls.append((method, path, fields, photo))
        if method == 'GET':
            return {'id': '123456', 'name': 'Test Page'}
        return {'id': '789', 'post_id': '123456_789'}

    def test_demo_and_string_flags_blocked(self):
        for values in [{'demo': True}, {'demo': 'false'}, {'reviewed': 'true'}, {'reviewed': False}]:
            story = {**self.story, **values}
            (self.folder/'story.json').write_text(json.dumps(story), encoding='utf8')
            with self.assertRaises(ValueError):
                pub.package(self.folder)

    def test_changed_caption_or_sources_blocked(self):
        (self.folder/'caption.txt').write_text('unreviewed change', encoding='utf8')
        with self.assertRaises(ValueError):
            pub.package(self.folder)

    def test_invalid_image_blocked(self):
        (self.folder/'post.png').write_bytes(b'not a png')
        with self.assertRaises(OSError):
            pub.package(self.folder)

    def test_default_is_offline_without_credentials(self):
        with patch.object(pub, 'settings', side_effect=AssertionError('no credentials needed')), patch.object(pub, 'request', side_effect=AssertionError('no network')), patch('sys.stdout', new_callable=io.StringIO) as output:
            self.assertEqual(pub.main(['--package', str(self.folder)]), 0)
            self.assertEqual(json.loads(output.getvalue())['mode'], 'offline-preview')

    def test_page_token_identity_and_confirmation(self):
        with self.assertRaises(ValueError):
            pub.publish(self.config, self.item, self.state, '999', self.transport)
        self.assertEqual(self.calls, [])
        wrong = lambda *a, **k: {'id': '999', 'name': 'Wrong Page'}
        with self.assertRaises(ValueError):
            pub.publish(self.config, self.item, self.state, '123456', wrong)
        self.assertFalse(self.state.exists())

    def test_success_photo_sources_receipt_and_duplicate_copy(self):
        receipt = pub.publish(self.config, self.item, self.state, '123456', self.transport)
        post = self.calls[1]
        self.assertEqual(post[:2], ('POST', '123456/photos'))
        self.assertEqual(post[2]['published'], 'true')
        self.assertIn('https://docs.python.org/3/', post[2]['caption'])
        self.assertEqual(post[3], (self.folder/'post.png').read_bytes())
        self.assertEqual(receipt['url'], 'https://www.facebook.com/123456_789')
        self.assertEqual(json.loads((self.folder/'facebook-receipt.json').read_text(encoding='utf8')), receipt)
        self.assertNotIn(self.config['token'], json.dumps(receipt))
        shutil.copytree(self.folder, self.root/'copy')
        with self.assertRaises(ValueError):
            pub.publish(self.config, pub.package(self.root/'copy'), self.state, '123456', self.transport)
        self.assertEqual(len([c for c in self.calls if c[0]=='POST']), 1)

    def test_uncertain_timeout_blocks_second_post(self):
        def timeout(config, method, *args):
            if method == 'GET':
                return {'id': '123456', 'name': 'Test Page'}
            raise pub.GraphFailure('timeout', uncertain=True)
        with self.assertRaises(pub.GraphFailure):
            pub.publish(self.config, self.item, self.state, '123456', timeout)
        with self.assertRaises(ValueError):
            pub.publish(self.config, self.item, self.state, '123456', self.transport)
        self.assertEqual(len([c for c in self.calls if c[0]=='POST']), 0)
        with closing(sqlite3.connect(self.state)) as db:
            self.assertEqual(db.execute('SELECT status FROM publications').fetchone()[0], 'unknown')

    def test_rejected_request_can_be_explicitly_retried(self):
        def rejected(config, method, *args):
            if method == 'GET':
                return {'id': '123456', 'name': 'Test Page'}
            raise pub.GraphFailure('HTTP 403')
        with self.assertRaises(pub.GraphFailure):
            pub.publish(self.config, self.item, self.state, '123456', rejected)
        self.assertEqual(pub.publish(self.config, self.item, self.state, '123456', self.transport)['status'], 'published')

    def test_incomplete_success_blocks_retry(self):
        def incomplete(config, method, *args):
            return {'id': '123456', 'name': 'Test Page'} if method=='GET' else {'id': '789'}
        with self.assertRaises(pub.GraphFailure):
            pub.publish(self.config, self.item, self.state, '123456', incomplete)
        with self.assertRaises(ValueError):
            pub.publish(self.config, self.item, self.state, '123456', self.transport)

    def test_wire_format_and_no_redirects(self):
        requests = []
        class Opener:
            def open(self, req, timeout):
                requests.append(req)
                return io.BytesIO(b'{"id":"789","post_id":"123456_789"}')
        with patch.object(pub.urllib.request, 'build_opener', return_value=Opener()) as opener:
            pub.request(self.config, 'POST', '123456/photos', {'caption': 'نص', 'published': 'true'}, self.item['photo'])
        req = requests[0]
        self.assertEqual(req.full_url, 'https://graph.facebook.com/v26.0/123456/photos')
        self.assertEqual(req.get_header('Authorization'), 'Bearer '+self.config['token'])
        self.assertNotIn(self.config['token'].encode(), req.data)
        self.assertIn(b'name="source"; filename="post.png"', req.data)
        self.assertIn('نص'.encode(), req.data)
        self.assertIsInstance(opener.call_args.args[0], pub.NoRedirect)
        self.assertIsNone(pub.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.org'))

    def test_http_errors_are_sanitized(self):
        class Opener:
            def open(self, *args, **kwargs):
                raise urllib.error.HTTPError('https://graph.facebook.com/', 503, 'secret', {}, io.BytesIO(b'secret'))
        with patch.object(pub.urllib.request, 'build_opener', return_value=Opener()):
            with self.assertRaises(pub.GraphFailure) as error:
                pub.request(self.config, 'POST', '123456/photos', {}, self.item['photo'])
        self.assertTrue(error.exception.uncertain)
        self.assertNotIn('secret', str(error.exception))

    def test_env_values_and_validation(self):
        env = self.root/'.env'
        env.write_text('FACEBOOK_PAGE_ID=123456\nFACEBOOK_PAGE_ACCESS_TOKEN=TEST_TOKEN\nFACEBOOK_GRAPH_VERSION=v26.0\n', encoding='utf8')
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(pub.settings(env)['page'], '123456')
        with patch.dict(os.environ, {'FACEBOOK_PAGE_ID': 'https://example.org'}, clear=True):
            with self.assertRaises(ValueError):
                pub.settings(env)

    def test_cli_explains_guard_without_exposing_secret(self):
        env = self.root/'.env'
        secret = 'PRIVATE_TEST_VALUE_NOT_FOR_OUTPUT'
        env.write_text('FACEBOOK_PAGE_ID=123456\nFACEBOOK_PAGE_ACCESS_TOKEN='+secret+'\nFACEBOOK_GRAPH_VERSION=v26.0\n', encoding='utf8')
        with patch.dict(os.environ, {}, clear=True), patch('sys.stderr', new_callable=io.StringIO) as error:
            code = pub.main(['--package',str(self.folder),'--env-file',str(env),'--publish','--confirm-page-id','999'])
        self.assertEqual(code,1)
        self.assertIn('--confirm-page-id must equal FACEBOOK_PAGE_ID',error.getvalue())
        self.assertNotIn(secret,error.getvalue())

    def test_cli_missing_env_explains_what_to_check(self):
        with patch('sys.stderr',new_callable=io.StringIO) as error:
            code = pub.main(['--package',str(self.folder),'--env-file',str(self.root/'missing.env'),'--check-connection'])
        self.assertEqual(code,1)
        self.assertIn('--env-file is missing',error.getvalue())


if __name__ == '__main__':
    unittest.main()
