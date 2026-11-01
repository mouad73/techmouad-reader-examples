"""Authenticated, bounded hosting experiment; this is not a public downloader."""
import hmac
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from probe_worker import validate_url

ROOT = Path(__file__).resolve().parent


def make_handler(token, url, runner=None):
    if len(token) < 32:
        raise ValueError('HOST_TEST_TOKEN must contain at least 32 characters')
    url = validate_url(url)
    lock = threading.Lock()
    completed = 0

    def run():
        environment = {'PATH': os.environ.get('PATH', ''), 'HOME': '/tmp',
                       'PYTHONNOUSERSITE': '1', 'HOST_TEST_VIDEO_URL': url}
        result = subprocess.run([sys.executable, '-I', str(ROOT / 'probe_worker.py')],
                                capture_output=True, text=True, timeout=100, env=environment)
        if result.returncode or len(result.stdout) > 16384:
            return {'ok': False, 'result': 'probe_worker_failed'}
        return json.loads(result.stdout)

    runner = runner or run

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_): pass

        def reply(self, code, body):
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self.reply(200, {'ok': True, 'service': 'techmouad-shorts-host-test'}) if self.path == '/health' else self.reply(404, {'ok': False})

        def do_POST(self):
            nonlocal completed
            if self.path != '/probe':
                return self.reply(404, {'ok': False})
            supplied = self.headers.get('Authorization', '')
            if not hmac.compare_digest(supplied.encode(), ('Bearer ' + token).encode()):
                return self.reply(401, {'ok': False, 'result': 'unauthorized'})
            # The source URL is set by the owner, never supplied by a visitor.
            if self.headers.get('Content-Length', '0') not in ('0', '2'):
                return self.reply(400, {'ok': False, 'result': 'unexpected_input'})
            if self.headers.get('Content-Length') == '2' and self.rfile.read(2) != b'{}':
                return self.reply(400, {'ok': False, 'result': 'unexpected_input'})
            if not lock.acquire(blocking=False):
                return self.reply(429, {'ok': False, 'result': 'probe_busy'})
            try:
                if completed >= 3:
                    return self.reply(429, {'ok': False, 'result': 'test_limit_reached'})
                completed += 1
                try:
                    report = runner()
                except subprocess.TimeoutExpired:
                    report = {'ok': False, 'result': 'probe_timeout'}
                except Exception:
                    report = {'ok': False, 'result': 'probe_failed'}
                self.reply(200, report)
            finally:
                lock.release()

    return Handler


if __name__ == '__main__':
    handler = make_handler(os.environ.get('HOST_TEST_TOKEN', ''), os.environ.get('HOST_TEST_VIDEO_URL', ''))
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '10000'))), handler).serve_forever()
