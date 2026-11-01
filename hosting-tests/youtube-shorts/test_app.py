import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from app import make_handler
from probe_worker import validate_url


class HostingProbeTests(unittest.TestCase):
    def test_only_short_urls_are_accepted(self):
        self.assertEqual(validate_url('https://m.youtube.com/shorts/5dWszRRzDZw?feature=share'), 'https://www.youtube.com/shorts/5dWszRRzDZw')
        for url in ['http://youtube.com/shorts/5dWszRRzDZw', 'https://youtube.com.evil.test/shorts/5dWszRRzDZw', 'https://user:pass@youtube.com/shorts/5dWszRRzDZw', 'https://youtube.com/watch?v=5dWszRRzDZw', 'https://127.0.0.1/shorts/5dWszRRzDZw']:
            with self.subTest(url=url), self.assertRaises(ValueError): validate_url(url)

    def test_authentication_fixed_input_and_three_run_limit(self):
        calls = []
        def runner():
            calls.append(True)
            return {'ok': True, 'result': 'unit_test_fixture'}
        token = 'a' * 64
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(token, 'https://www.youtube.com/shorts/5dWszRRzDZw', runner))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        root = 'http://127.0.0.1:' + str(server.server_port)
        def request(body=b'{}', authenticated=True):
            headers = {'Authorization': 'Bearer ' + token} if authenticated else {}
            req = urllib.request.Request(root + '/probe', data=body, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=3) as response: return response.status, json.load(response)
            except urllib.error.HTTPError as error: return error.code, json.load(error)
        try:
            self.assertEqual(request(authenticated=False)[0], 401)
            self.assertEqual(request(b'{"url":"https://evil.test"}')[0], 400)
            self.assertEqual(calls, [])
            for _ in range(3): self.assertEqual(request()[0], 200)
            self.assertEqual(request()[0], 429)
            self.assertEqual(len(calls), 3)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == '__main__': unittest.main()
