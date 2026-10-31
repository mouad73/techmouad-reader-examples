"""Create a local Arabic post package. No AI calls or Facebook publishing."""
import argparse
import hashlib
import html
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import urlsplit


def validate(story):
    for key in ('title', 'caption'):
        if not isinstance(story.get(key), str) or not story[key].strip():
            raise ValueError(f'Missing {key}')
    if len(story['title']) > 180:
        raise ValueError('Keep the title under 181 characters')
    sources = story.get('sources', [])
    domains = set()
    for source in sources:
        url = urlsplit(source.get('url', ''))
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError('Sources must be public HTTPS URLs')
        domains.add(url.hostname.lower().removeprefix('www.'))
    if len(domains) < 2:
        raise ValueError('Provide at least two different source domains')
    if not story.get('demo'):
        if story.get('reviewed') is not True:
            raise ValueError('Review claims and sources, then set reviewed=true')
        if any(d in {'example.org', 'example.net', 'example.com'} for d in domains):
            raise ValueError('Replace all demonstration source URLs')
    return story


def font_path(explicit=None):
    candidates = [explicit, os.getenv('ARABIC_FONT'),
                  'C:/Windows/Fonts/tahoma.ttf',
                  '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
                  '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                  '/System/Library/Fonts/Supplemental/Arial.ttf']
    for value in candidates:
        if value and Path(value).is_file():
            return value
    raise ValueError('Pass --font with an Arabic-capable TrueType font path')


def render(title, destination, font=None, demo=False):
    from PIL import Image, ImageDraw, ImageFont, features
    if not features.check_feature('raqm'):
        raise ValueError('This Pillow build needs libraqm for Arabic shaping; install a supported Pillow wheel')
    image = Image.new('RGB', (1080, 1350), '#101e36')
    draw = ImageDraw.Draw(image)
    path = font_path(font)
    face = ImageFont.truetype(path, 64)
    small = ImageFont.truetype(path, 30)
    draw.rounded_rectangle((70, 150, 1010, 1150), radius=30, fill='#172b49', outline='#36c9b2', width=4)
    lines, line = [], ''
    for word in title.split():
        candidate = (line+' '+word).strip()
        if draw.textbbox((0, 0), candidate, font=face, direction='rtl')[2] > 810 and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    lines.append(line)
    if len(lines) > 7 or any(draw.textlength(x, font=face, direction='rtl') > 810 for x in lines):
        raise ValueError('Title does not fit: shorten it before rendering')
    for index, text in enumerate(lines):
        draw.text((540, 500+index*105), text, font=face, anchor='mm', fill='white', direction='rtl', language='ar')
    label = 'مثال تجريبي — لا تنشره كخبر' if demo else 'محتوى راجعه قبل النشر'
    draw.text((540, 230), label, font=small, anchor='mm', fill='#60e5d0', direction='rtl', language='ar')
    draw.text((540, 1070), 'TECHMOUAD / CONTENT STARTER', font=small, anchor='mm', fill='white')
    image.save(destination)


def build(story, output, font=None):
    validate(story)
    output = Path(output)
    if output.exists():
        raise ValueError('Output folder already exists; choose a new folder')
    # Validate rendering before creating the final package.
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.parent / (output.name+'.rendering.png')
    render(story['title'], temporary, font, bool(story.get('demo')))
    output.mkdir()
    temporary.replace(output/'post.png')
    (output/'caption.txt').write_text(story['caption']+'\n', encoding='utf-8')
    (output/'sources.json').write_text(json.dumps(story['sources'], ensure_ascii=False, indent=2), encoding='utf-8')
    (output/'story.json').write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding='utf-8')
    (output/'REVIEW.md').write_text('# Before manual publication\n\n- [ ] Verify every claim against the original sources.\n- [ ] Review Arabic text and image rights.\n- [ ] Replace demo data.\n- [ ] Include source links with the post.\n', encoding='utf-8')
    links=''.join('<li><a rel="noopener" href="'+html.escape(s['url'],quote=True)+'">'+html.escape(s.get('title','Source'))+'</a></li>' for s in story['sources'])
    (output/'preview.html').write_text('<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>معاينة المنشور</title><style>body{max-width:700px;margin:30px auto;padding:20px;font:20px/1.8 system-ui}img{max-width:100%;height:auto}p{white-space:pre-wrap}</style><h1>'+html.escape(story['title'])+'</h1><img alt="معاينة التصميم" src="post.png"><p>'+html.escape(story['caption'])+'</p><ul>'+links+'</ul></html>', encoding='utf-8')
    with closing(sqlite3.connect(output/'state.sqlite3')) as db:
        db.execute('CREATE TABLE packages(fingerprint TEXT PRIMARY KEY, status TEXT)')
        digest=hashlib.sha256(json.dumps(story,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        db.execute('INSERT INTO packages VALUES (?,?)',(digest,'demo' if story.get('demo') else 'prepared'))
        db.commit()
    return output


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',default=str(Path(__file__).with_name('story.example.json')))
    parser.add_argument('--out',default='output/demo')
    parser.add_argument('--font')
    args=parser.parse_args()
    try:
        result=build(json.loads(Path(args.input).read_text(encoding='utf-8-sig')),args.out,args.font)
        print('Prepared locally:', result)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1,str(error)+'\n')
