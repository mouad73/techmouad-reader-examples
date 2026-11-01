"""Read-only public launch checks; not an indexing or hosting-account audit."""
import argparse
from html.parser import HTMLParser
import ipaddress
import json
import socket
import urllib.parse
import urllib.request

def public_url(url):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in [None,443]: raise ValueError('Use your public HTTPS site URL')
    if any(not ipaddress.ip_address(a[4][0]).is_global for a in socket.getaddrinfo(parsed.hostname,443,type=socket.SOCK_STREAM)): raise ValueError('Local and private targets are unsupported')
    return url

class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return super().redirect_request(req,fp,code,msg,headers,public_url(urllib.parse.urljoin(req.full_url,newurl)))

class Page(HTMLParser):
    def __init__(self):super().__init__();self.canonical=[];self.robots=[];self.title=False;self.has_title=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='title':self.title=True
        if tag=='link' and 'canonical' in a.get('rel','').lower().split():self.canonical.append(a.get('href'))
        if tag=='meta' and a.get('name','').lower() in ['robots','googlebot']:self.robots.append(a.get('content',''))
    def handle_endtag(self,tag):
        if tag=='title':self.title=False
    def handle_data(self,data):
        if self.title and data.strip():self.has_title=True

def analyze(html,headers=None):
    page=Page();page.feed(html)
    directives=page.robots+[(headers or {}).get('X-Robots-Tag','')]
    return {'hasTitle':page.has_title,'canonical':page.canonical,'robotsDirectives':directives,'explicitNoindex':any('noindex' in d.lower() or 'none' in d.lower().split(',') for d in directives),'note':'Observations only. Noindex absence does not prove Google indexing; hPanel settings and backups are not inspected.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--site',required=True);args=parser.parse_args()
    url=public_url(args.site)
    request=urllib.request.Request(url,headers={'User-Agent':'TechMouadReaderLaunchCheck/1.0'})
    with urllib.request.build_opener(Redirect).open(request,timeout=20) as response:
        raw=response.read(2_000_001)
        if len(raw)>2_000_000:raise ValueError('Page too large for this small checker')
        result=analyze(raw.decode('utf-8','replace'),dict(response.headers))
        result.update({'url':response.url,'httpStatus':response.status})
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
