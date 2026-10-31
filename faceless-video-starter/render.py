"""Render a silent vertical text video with FFmpeg/libass; no platform uploads."""
import argparse
import json
import subprocess
from pathlib import Path

def ass_time(seconds):
    value=round(seconds*100)
    return f'{value//360000}:{value//6000%60:02d}:{value//100%60:02d}.{value%100:02d}'

def prepare(data, folder):
    scenes=data.get('scenes',[])
    if not scenes or len(scenes)>20:
        raise ValueError('Use 1-20 scenes')
    folder=Path(folder)
    if folder.exists():
        raise ValueError('Choose a new output folder')
    lines=['[Script Info]','ScriptType: v4.00+','PlayResX: 1080','PlayResY: 1920','WrapStyle: 0','[V4+ Styles]','Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding','Style: Default,Arial,76,&H00FFFFFF,&H00FFFFFF,&H00101E36,&H00101E36,0,0,0,0,100,100,0,0,1,3,0,5,100,100,120,1','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
    cursor=0
    for scene in scenes:
        duration=float(scene['seconds'])
        text=str(scene['text']).strip()
        if not 1<=duration<=15 or not text or len(text)>120:
            raise ValueError('Each scene needs 1-15 seconds and 1-120 characters')
        text=text.replace('\\','').replace('{','').replace('}','').replace('\r','').replace('\n',r'\N')
        lines.append(f'Dialogue: 0,{ass_time(cursor)},{ass_time(cursor+duration)},Default,,0,0,0,,{text}')
        cursor+=duration
    folder.mkdir(parents=True)
    (folder/'captions.ass').write_text('\n'.join(lines),encoding='utf-8-sig')
    return folder,cursor

def render(folder,duration):
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-n','-f','lavfi','-i',f'color=c=0x101e36:s=1080x1920:r=24:d={duration}','-vf','subtitles=captions.ass','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','video.mp4'],cwd=folder,check=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',default=str(Path(__file__).with_name('scenes.example.json')))
    p.add_argument('--out',default='output/demo')
    p.add_argument('--render',action='store_true',help='Run installed FFmpeg to create video.mp4')
    a=p.parse_args()
    try:
        folder,duration=prepare(json.loads(Path(a.input).read_text(encoding='utf-8-sig')),a.out)
        if a.render: render(folder,duration)
        print('Prepared locally:',folder)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        p.exit(1,str(error)+'\n')
