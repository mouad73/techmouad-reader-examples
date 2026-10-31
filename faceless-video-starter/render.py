"""Render a silent vertical text video with FFmpeg/libass; no platform uploads."""
import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path

def ass_time(seconds):
    value=round(seconds*100)
    return f'{value//360000}:{value//6000%60:02d}:{value//100%60:02d}.{value%100:02d}'

def prepare(data, folder):
    if not isinstance(data,dict):
        raise ValueError('Input must be a JSON object with a scenes array')
    scenes=data.get('scenes',[])
    if not isinstance(scenes,list) or not scenes or len(scenes)>20:
        raise ValueError('Use 1-20 scenes')
    folder=Path(folder)
    if folder.exists():
        raise ValueError('Choose a new output folder')
    lines=['[Script Info]','ScriptType: v4.00+','PlayResX: 1080','PlayResY: 1920','WrapStyle: 0','[V4+ Styles]','Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding','Style: Default,Arial,76,&H00FFFFFF,&H00FFFFFF,&H00101E36,&H00101E36,0,0,0,0,100,100,0,0,1,3,0,5,100,100,120,1','[Events]','Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
    cursor=0
    for scene in scenes:
        if not isinstance(scene,dict) or type(scene.get('seconds')) not in (int,float) or not isinstance(scene.get('text'),str):
            raise ValueError('Each scene needs string text and numeric seconds (not true/false)')
        duration=float(scene['seconds'])
        text=scene['text'].strip()
        if not math.isfinite(duration) or not 1<=duration<=15 or not text or len(text)>120:
            raise ValueError('Each scene needs 1-15 seconds and 1-120 characters')
        text=text.replace('\\','').replace('{','').replace('}','').replace('\r','').replace('\n',r'\N')
        lines.append(f'Dialogue: 0,{ass_time(cursor)},{ass_time(cursor+duration)},Default,,0,0,0,,{text}')
        cursor+=duration
    folder.mkdir(parents=True)
    (folder/'captions.ass').write_text('\n'.join(lines),encoding='utf-8-sig')
    return folder,cursor

def check_runtime():
    executable=shutil.which('ffmpeg')
    if not executable:
        raise ValueError('FFmpeg not found in PATH. Install a build with subtitles/libass and libx264, then reopen PowerShell')
    for flag,required in [('-filters','subtitles'),('-encoders','libx264')]:
        result=subprocess.run([executable,'-hide_banner',flag],capture_output=True,text=True,encoding='utf-8',errors='replace',check=True,timeout=20)
        if not any(len(line.split())>1 and line.split()[1]==required for line in result.stdout.splitlines()):
            raise ValueError('This FFmpeg build is missing '+required+'; install a compatible build before rendering')
    return executable

def render(folder,duration,executable='ffmpeg'):
    subprocess.run([executable,'-hide_banner','-loglevel','error','-nostdin','-n','-f','lavfi','-i',f'color=c=0x101e36:s=1080x1920:r=24:d={duration}','-vf','subtitles=captions.ass','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','video.mp4'],cwd=folder,check=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',default=str(Path(__file__).with_name('scenes.example.json')))
    p.add_argument('--out',default='output/demo')
    p.add_argument('--render',action='store_true',help='Run installed FFmpeg to create video.mp4')
    p.add_argument('--check',action='store_true',help='Check FFmpeg filters/encoder without creating files')
    a=p.parse_args()
    try:
        executable=check_runtime() if a.render or a.check else None
        if a.check:
            print('FFmpeg ready: subtitles and libx264; direct process, no command shell required')
            p.exit(0)
        folder,duration=prepare(json.loads(Path(a.input).read_text(encoding='utf-8-sig')),a.out)
        if a.render: render(folder,duration,executable)
        print('Prepared locally:',folder)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        p.exit(1,str(error)+'\n')
