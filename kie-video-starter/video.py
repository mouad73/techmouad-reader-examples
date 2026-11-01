"""Small Kie.ai Kling V3 Turbo reader example; offline preview is the default."""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

API = 'https://api.kie.ai/api/v1/'
MODEL = 'kling/v3-turbo-text-to-video'
QUOTE_CREDITS = 54  # 3 seconds x 18 credits/s at 720p; verify current price first.

def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def api(endpoint, key, payload=None):
    request = urllib.request.Request(API + endpoint, data=None if payload is None else json.dumps(payload).encode(), headers={'Authorization':'Bearer '+key, 'Content-Type':'application/json'})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=60) as response:
            raw=response.read(2_000_001)
            if len(raw)>2_000_000: raise ValueError('Oversized API response')
            data=json.loads(raw)
    except (urllib.error.URLError, ValueError, TimeoutError) as error:
        raise RuntimeError('API request unsuccessful; credentials and response text are hidden. Inspect the task history before retrying a creation.') from None
    if data.get('code') != 200:
        raise RuntimeError('Kie API rejected the request (code '+str(data.get('code'))+'). Check credentials, balance, parameters and account history.')
    return data.get('data')

def payload(prompt):
    if not prompt.strip() or len(prompt)>2500: raise ValueError('Prompt must contain 1–2500 characters')
    return {'model':MODEL,'input':{'prompt':prompt.strip(),'duration':'3','aspect_ratio':'9:16','resolution':'720p'}}

def key_from_env():
    key=os.environ.get('KIE_API_KEY')
    if not key and Path('.env').is_file():
        for line in Path('.env').read_text(encoding='utf-8-sig').splitlines():
            if line.startswith('KIE_API_KEY='): key=line.split('=',1)[1].strip().strip('\"\'')
    if not key: raise ValueError('Set KIE_API_KEY in your private .env file')
    return key

def create_once(state_path, body, key, confirmed_credits, transport=api):
    if confirmed_credits != QUOTE_CREDITS: raise ValueError('Verify the live price, then confirm the 54-credit estimate with --max-credits 54')
    # The local estimate is a confirmation guard, not a provider-enforced spending cap.
    if state_path.exists(): raise ValueError('State already exists. Use --poll; inspect the provider history if taskId is absent. Do not recreate blindly.')
    balance=transport('chat/credit',key)
    if not isinstance(balance,(int,float)) or balance<QUOTE_CREDITS: raise ValueError('Insufficient or unknown account balance')
    with state_path.open('x',encoding='utf-8') as stream:
        json.dump({'phase':'creation-unconfirmed','model':MODEL,'estimatedCredits':QUOTE_CREDITS},stream)
    created=transport('jobs/createTask',key,body)
    if not created or not isinstance(created.get('taskId'),str) or not created['taskId']: raise RuntimeError('Missing taskId; inspect account history and keep the state file')
    state={'phase':'submitted','model':MODEL,'taskId':created['taskId'],'estimatedCredits':QUOTE_CREDITS}
    write_json(state_path,state)
    return state

def poll_once(state_path,key,transport=api):
    state=json.loads(state_path.read_text(encoding='utf-8'))
    if not state.get('taskId'): raise ValueError('Creation is unconfirmed; inspect provider history before taking further action')
    task=transport('jobs/recordInfo?'+urllib.parse.urlencode({'taskId':state['taskId']}),key)
    if not isinstance(task,dict) or task.get('state') not in ['waiting','queuing','generating','success','fail']: raise RuntimeError('Unknown task response; no new task was submitted')
    state['phase']=task['state']
    if isinstance(task.get('creditsConsumed'),(int,float)): state['actualCredits']=task['creditsConsumed']
    if task['state']=='success':
        result=json.loads(task.get('resultJson') or '{}')
        if not result.get('resultUrls'): raise RuntimeError('Successful task has no downloadable result')
        state['resultUrl']=result['resultUrls'][0]
    write_json(state_path,state)
    return state

def public_url(url):
    value=urllib.parse.urlsplit(url)
    if value.scheme!='https' or value.username or value.password or value.port not in [None,443] or not value.hostname: raise ValueError('Only public HTTPS result URLs are allowed')
    addresses=socket.getaddrinfo(value.hostname,443,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses): raise ValueError('Private or local result address rejected')
    return url

class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req,fp,code,msg,headers,public_url(urllib.parse.urljoin(req.full_url,newurl)))

def download(state_path):
    state=json.loads(state_path.read_text(encoding='utf-8'))
    if state.get('phase')!='success': raise ValueError('Poll until the task succeeds before downloading')
    target=state_path.parent/'video.mp4'; temporary=state_path.parent/'video.part'
    if target.exists() or temporary.exists(): raise ValueError('Download target already exists; inspect it before continuing')
    request=urllib.request.Request(public_url(state['resultUrl']))  # No API credentials sent to the media host.
    try:
        with urllib.request.build_opener(PublicRedirect).open(request,timeout=60) as response, temporary.open('xb') as output:
            size=0
            while chunk:=response.read(65536):
                size+=len(chunk)
                if size>64*1024*1024: raise ValueError('Video exceeds the 64 MiB example limit')
                output.write(chunk)
        with temporary.open('rb') as stream:
            if stream.read(12)[4:8]!=b'ftyp': raise ValueError('Response is not an MP4 container')
        temporary.replace(target)
        state.update({'videoBytes':target.stat().st_size,'videoSha256':hashlib.sha256(target.read_bytes()).hexdigest()})
        write_json(state_path,state)
        return target
    except Exception:
        if temporary.exists(): temporary.unlink()
        raise RuntimeError('Download failed; the successful task is retained. Retry --download without creating another task.') from None

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--create',action='store_true');mode.add_argument('--poll',action='store_true');mode.add_argument('--download',action='store_true')
    parser.add_argument('--prompt',default='prompt.txt');parser.add_argument('--state',default='output/state.json');parser.add_argument('--max-credits',type=int)
    args=parser.parse_args();state=Path(args.state)
    if args.download: print('Saved',download(state));return
    if args.poll:
        result=poll_once(state,key_from_env());print(json.dumps({k:v for k,v in result.items() if k not in ['taskId','resultUrl']},ensure_ascii=False));return
    body=payload(Path(args.prompt).read_text(encoding='utf-8-sig'))
    if not args.create: print(json.dumps({'previewOnly':True,'estimatedCredits':QUOTE_CREDITS,'request':body},ensure_ascii=False,indent=2));return
    state.parent.mkdir(parents=True,exist_ok=True)
    result=create_once(state,body,key_from_env(),args.max_credits)
    print('Task submitted; saved locally. Run --poll until success, then --download. No automatic creation retry.')

if __name__=='__main__':
    try: main()
    except (OSError,ValueError,RuntimeError) as error: print(str(error),file=sys.stderr);sys.exit(1)
