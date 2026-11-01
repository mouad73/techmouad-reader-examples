"""One public Shorts probe. No accounts, cookies, proxies or external download API."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

MAX_BYTES = 64 * 1024 * 1024


def validate_url(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or parsed.hostname not in {'youtube.com', 'www.youtube.com', 'm.youtube.com'}
            or parsed.username or parsed.password or parsed.port is not None
            or not re.fullmatch(r'/shorts/[A-Za-z0-9_-]{11}/?', parsed.path)):
        raise ValueError('invalid_shorts_url')
    return 'https://www.youtube.com' + parsed.path.rstrip('/')


def check_video(url):
    import yt_dlp
    started = time.monotonic()
    url = validate_url(url)
    errors = []

    class Logger:
        def debug(self, _): pass
        def warning(self, _): pass
        def error(self, text): errors.append(str(text))

    def bounded(progress):
        if max(progress.get('downloaded_bytes') or 0, progress.get('total_bytes') or 0) > MAX_BYTES:
            raise ValueError('video_too_large')

    with tempfile.TemporaryDirectory(prefix='shorts-host-probe-') as folder:
        target = Path(folder) / 'clip.mp4'
        options = {
            'quiet': True, 'no_warnings': True, 'logger': Logger(), 'cachedir': False,
            'noplaylist': True, 'proxy': '', 'socket_timeout': 10, 'retries': 0,
            'extractor_retries': 0, 'fragment_retries': 0, 'max_filesize': MAX_BYTES,
            'progress_hooks': [bounded], 'outtmpl': str(target),
            'format': '18/best[ext=mp4][acodec!=none][height<=720]',
            'js_runtimes': {'node': {'path': shutil.which('node') or '/usr/local/bin/node'}},
            'remote_components': [],
        }
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
                duration = info.get('duration')
                if info.get('id') != url.rsplit('/', 1)[1] or info.get('is_live') or info.get('_type') in ('playlist', 'multi_video'):
                    raise ValueError('unexpected_video')
                if not isinstance(duration, (int, float)) or not 0 < duration <= 180:
                    raise ValueError('video_too_long')
                ydl.process_ie_result(info, download=True)
            if not target.is_file() or not 12 <= target.stat().st_size <= MAX_BYTES:
                raise ValueError('invalid_download_size')
            with target.open('rb') as file:
                if file.read(12)[4:8] != b'ftyp':
                    raise ValueError('invalid_mp4')
            media = json.loads(subprocess.check_output([
                'ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-f', 'mov',
                '-show_entries', 'format=duration:stream=codec_type,width,height', '-of', 'json', str(target)
            ], timeout=15))
            kinds = {stream.get('codec_type') for stream in media.get('streams', [])}
            if not {'video', 'audio'} <= kinds or float(media['format']['duration']) > 180:
                raise ValueError('invalid_media_tracks')
            return {'ok': True, 'result': 'download_verified', 'videoId': info['id'],
                    'title': str(info.get('title') or '')[:120], 'bytes': target.stat().st_size,
                    'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'media': media,
                    'elapsedSeconds': round(time.monotonic() - started, 2),
                    'cookiesUsed': False, 'paidApiUsed': False}
        except Exception as error:
            text = str(error) + ' ' + ' '.join(errors)
            if 'not a bot' in text.lower() or 'sign in' in text.lower():
                code = 'youtube_sign_in_required'
            elif '403' in text:
                code = 'youtube_access_denied'
            elif str(error) in {'video_too_large', 'video_too_long', 'unexpected_video', 'invalid_download_size', 'invalid_mp4', 'invalid_media_tracks'}:
                code = str(error)
            else:
                code = 'extraction_failed'
            return {'ok': False, 'result': code, 'elapsedSeconds': round(time.monotonic() - started, 2),
                    'cookiesUsed': False, 'paidApiUsed': False}


if __name__ == '__main__':
    try:
        print(json.dumps(check_video(os.environ['HOST_TEST_VIDEO_URL'])))
    except Exception:
        print(json.dumps({'ok': False, 'result': 'probe_configuration_error'}))
