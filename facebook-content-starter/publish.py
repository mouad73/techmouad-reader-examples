"""Preview by default; explicitly publish a reviewed PNG package to a Facebook Page."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

from build import validate


class GraphFailure(RuntimeError):
    def __init__(self, message, uncertain=False):
        super().__init__(message)
        self.uncertain = uncertain


class SetupError(ValueError):
    """Only fixed, credential-free messages authored by this script."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def settings(env_file=None):
    values = {}
    if env_file:
        for line in Path(env_file).read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, sep, value = line.partition('=')
            if not sep or not re.fullmatch(r'[A-Z_]+', key.strip()):
                raise SetupError('Invalid env file line; use KEY=value, without shell expressions')
            values[key.strip()] = value.strip().strip('\"\'')
    # Environment variables take precedence; no interpolation or shell execution.
    for key in ('FACEBOOK_PAGE_ID', 'FACEBOOK_PAGE_ACCESS_TOKEN', 'FACEBOOK_GRAPH_VERSION'):
        if key in os.environ:
            values[key] = os.environ[key]
    page = values.get('FACEBOOK_PAGE_ID', '')
    token = values.get('FACEBOOK_PAGE_ACCESS_TOKEN', '')
    version = values.get('FACEBOOK_GRAPH_VERSION', '')
    if not re.fullmatch(r'[0-9]+', page):
        raise SetupError('Set FACEBOOK_PAGE_ID to the numeric Page ID')
    if not token or any(c.isspace() for c in token) or token.startswith('YOUR_'):
        raise SetupError('Set a private FACEBOOK_PAGE_ACCESS_TOKEN')
    if not re.fullmatch(r'v[0-9]+\.[0-9]+', version):
        raise SetupError('Set FACEBOOK_GRAPH_VERSION to the version selected for your Meta app')
    return {'page': page, 'token': token, 'version': version}


def package(folder):
    folder = Path(folder)
    story = json.loads((folder/'story.json').read_text(encoding='utf-8-sig'))
    if story['demo'] is not False or story['reviewed'] is not True:
        raise SetupError('Publishing requires demo=false and reviewed=true; demo packages cannot be posted')
    try:
        validate(story)
    except ValueError:
        raise SetupError('Invalid story.json: review title, caption and at least two real HTTPS source domains, then rebuild') from None
    caption = (folder/'caption.txt').read_text(encoding='utf-8-sig').strip()
    sources = json.loads((folder/'sources.json').read_text(encoding='utf-8-sig'))
    if caption != story['caption'].strip() or sources != story['sources']:
        raise SetupError('Package text or sources changed; review and rebuild the package')
    photo = (folder/'post.png').read_bytes()
    if len(photo) > 8*1024*1024:
        raise SetupError('This starter limits PNG uploads to 8 MiB')
    from PIL import Image
    with Image.open(io.BytesIO(photo)) as image:
        if image.format != 'PNG' or image.size != (1080, 1350):
            raise SetupError('Expected the generated 1080x1350 PNG; review and rebuild')
        image.verify()
    text = caption+'\n\nالمصادر:\n'+'\n'.join(s['url'] for s in sources)
    # Fingerprint the actual bytes to upload; a shared ledger also catches copied folders.
    fingerprint = hashlib.sha256(photo+b'\0'+text.encode('utf-8')).hexdigest()
    return {'photo': photo, 'text': text, 'fingerprint': fingerprint, 'folder': folder}


def request(config, method, path, fields=None, photo=None):
    url = 'https://graph.facebook.com/'+config['version']+'/'+path
    headers = {'Authorization': 'Bearer '+config['token']}
    data = None
    if method == 'GET':
        url += '?'+urllib.parse.urlencode(fields or {})
    else:
        boundary = 'TechMouad'+uuid.uuid4().hex
        chunks = []
        for key, value in (fields or {}).items():
            chunks.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="'+key+'"\r\n\r\n'+value+'\r\n').encode('utf-8'))
        if photo is not None:
            chunks += [('--'+boundary+'\r\nContent-Disposition: form-data; name="source"; filename="post.png"\r\nContent-Type: image/png\r\n\r\n').encode(), photo, b'\r\n']
        chunks.append(('--'+boundary+'--\r\n').encode())
        data = b''.join(chunks)
        headers['Content-Type'] = 'multipart/form-data; boundary='+boundary
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=60) as response:
            raw = response.read(1024*1024)
        result = json.loads(raw)
        if not isinstance(result, dict) or 'error' in result:
            raise GraphFailure('Unexpected Meta response; inspect your Page before retrying', uncertain=method=='POST')
        return result
    except urllib.error.HTTPError as error:
        # Never echo raw response bodies, request headers, URLs with tokens, or exception text.
        raise GraphFailure('Meta rejected the request (HTTP '+str(error.code)+'). Check permissions, token and app status.', uncertain=method=='POST' and error.code>=500) from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise GraphFailure('Meta response unavailable. Inspect your Page before retrying a publication.', uncertain=method=='POST') from None


def check_connection(config, transport=request):
    page = transport(config, 'GET', 'me', {'fields': 'id,name'})
    if str(page.get('id')) != config['page'] or not isinstance(page.get('name'), str) or not page['name']:
        raise SetupError('Token identity does not match FACEBOOK_PAGE_ID; use the intended Page access token')
    return {'id': str(page['id']), 'name': page['name']}


def ledger(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS publications (page TEXT, fingerprint TEXT, status TEXT, receipt TEXT, updated TEXT, PRIMARY KEY(page,fingerprint))')
    db.commit()
    return db


def publish(config, item, state, confirm_page, transport=request):
    if confirm_page != config['page']:
        raise SetupError('--confirm-page-id must equal FACEBOOK_PAGE_ID; verify the destination before publishing')
    page = check_connection(config, transport)
    now = lambda: datetime.now(timezone.utc).isoformat()
    with closing(ledger(state)) as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT status FROM publications WHERE page=? AND fingerprint=?', (page['id'], item['fingerprint'])).fetchone()
        if row and row[0] != 'rejected':
            db.rollback()
            raise SetupError('Duplicate or unresolved publication. Inspect the Page and shared ledger; no automatic retry.')
        db.execute('INSERT OR REPLACE INTO publications VALUES (?,?,?,?,?)', (page['id'], item['fingerprint'], 'pending', None, now()))
        db.commit()
        try:
            result = transport(config, 'POST', page['id']+'/photos', {'caption': item['text'], 'published': 'true'}, item['photo'])
            photo_id, post_id = str(result.get('id', '')), str(result.get('post_id', ''))
            if not re.fullmatch(r'[0-9]+', photo_id) or not re.fullmatch(r'[0-9]+_[0-9]+', post_id):
                raise GraphFailure('Upload response has no complete post receipt. Inspect the Page; do not retry automatically.', uncertain=True)
        except Exception as error:
            status = 'rejected' if isinstance(error, GraphFailure) and not error.uncertain else 'unknown'
            db.execute('UPDATE publications SET status=?,updated=? WHERE page=? AND fingerprint=?', (status, now(), page['id'], item['fingerprint']))
            db.commit()
            raise
        receipt = {'status': 'published', 'page_id': page['id'], 'page_name': page['name'], 'photo_id': photo_id, 'post_id': post_id, 'url': 'https://www.facebook.com/'+post_id, 'fingerprint': item['fingerprint'], 'published_at': now()}
        db.execute('UPDATE publications SET status=?,receipt=?,updated=? WHERE page=? AND fingerprint=?', ('published', json.dumps(receipt, ensure_ascii=False), now(), page['id'], item['fingerprint']))
        db.commit()
    try:
        (item['folder']/'facebook-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    except OSError:
        print('Published; local receipt file could not be written. Receipt is saved in the shared ledger.', file=sys.stderr)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', required=True)
    parser.add_argument('--env-file', help='Private KEY=value file; environment values override it')
    parser.add_argument('--state', default=str(Path(__file__).with_name('output')/'facebook-publish-state.sqlite3'))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check-connection', action='store_true', help='Read-only Page identity check')
    mode.add_argument('--publish', action='store_true', help='Publish the reviewed image and caption immediately')
    parser.add_argument('--confirm-page-id')
    args = parser.parse_args(argv)
    try:
        item = package(args.package)
        if not args.publish and not args.check_connection:
            print(json.dumps({'mode': 'offline-preview', 'fingerprint': item['fingerprint'], 'caption': item['text'], 'image': str(item['folder']/'post.png')}, ensure_ascii=False))
            return 0
        config = settings(args.env_file)
        if args.check_connection:
            print(json.dumps({'mode': 'read-only', 'page': check_connection(config)}, ensure_ascii=False))
        else:
            print(json.dumps(publish(config, item, args.state, args.confirm_page_id), ensure_ascii=False))
        return 0
    except (SetupError, GraphFailure) as error:
        print('Stopped: '+str(error), file=sys.stderr)
        return 1
    except FileNotFoundError:
        print('Stopped: a required package file or --env-file is missing. Check the folder and file names.', file=sys.stderr)
        return 1
    except (ValueError, OSError, KeyError, TypeError, sqlite3.Error):
        # Library exceptions could embed credentials: emit only a fixed generic failure.
        print('Stopped. Check reviewed package, Page identity, private configuration and shared publication ledger. No automatic retry. See the setup guide.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
