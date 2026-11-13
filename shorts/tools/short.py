"""Render one vertical 9:16 short from a JSON spec.

spec = {
  "out": "exports/01.mp4", "source": "sources/extended-look-1080p.mp4",
  "hook": {"cuts": [[s,e],...], "title": "TEXTO|PALAVRA ROSA"},        # ~3 s
  "body": {"cuts": [[s,e],...], "title": "...", "voice": "path.wav"|null, "captions": "path.ass"|null,
           "source_gain_db": -14 (under voice) or 0},
}
Titles: words wrapped in *asterisks* are drawn pink.
"""
import json, subprocess, sys, re
spec = json.load(open(sys.argv[1]))
W, H = 1080, 1920
VY, VH = 560, 760          # video window
FADE = 0.18                # dip-to-black half length

def title_ass(text, start, end, layer=0, style='Titulo'):
    parts = []
    for tok in re.split(r'(\*[^*]+\*)', text):
        if tok.startswith('*'):
            parts.append('{\\c&H00A25FFF&}' + tok.strip('*') + '{\\c&H00FFFFFF&}')
        else:
            parts.append(tok)
    t = ''.join(parts).replace('\n', '\\N')
    def ts(x):
        return f'0:{int(x // 60):02d}:{x % 60:05.2f}'
    pop = '{\\fscx70\\fscy70\\t(0,140,\\fscx104\\fscy104)\\t(140,220,\\fscx100\\fscy100)}'
    return f'Dialogue: {layer},{ts(start)},{ts(end)},{style},,0,0,0,,{pop}{t}'

def seg_len(cuts):
    return sum(e - s for s, e in cuts)

hook_len = seg_len(spec['hook']['cuts'])
body_len = seg_len(spec['body']['cuts'])
total = hook_len + body_len

# overlay ASS: titles + watermark
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Titulo,Inter Display Black,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,6,4,8,60,60,250,1
Style: Gancho,Inter Display Black,100,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,7,5,8,50,50,215,1
Style: Marca,Inter Display,34,&H70FFFFFF,&H70FFFFFF,&H90000000,&H00000000,1,0,0,0,100,100,1,0,1,1.5,0,9,0,40,{VY + VH + 14},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = [title_ass(spec['hook']['title'], 0, hook_len, style='Gancho')]
if spec['body'].get('title'):
    ev.append(title_ass(spec['body']['title'], hook_len, total))
ev.append(f'Dialogue: 1,0:00:00.00,0:{int(total // 60):02d}:{total % 60:05.2f},Marca,,0,0,0,,@news.coringa')
ovl = spec['out'].replace('.mp4', '.overlay.ass')
open(ovl, 'w').write(ass + '\n'.join(ev) + '\n')

# filter graph
src = spec['source']
fc, vlabels, alabels = [], [], []
cuts = [('h', c) for c in spec['hook']['cuts']] + [('b', c) for c in spec['body']['cuts']]
inputs = []
for i, (part, (s, e)) in enumerate(cuts):
    inputs += ['-ss', f'{s:.3f}', '-t', f'{e - s:.3f}', '-i', src]
    fc.append(f'[{i}:v]setpts=PTS-STARTPTS,fps=30,scale=1920:1080,setsar=1[v{i}]')
    fc.append(f'[{i}:a]asetpts=PTS-STARTPTS,aresample=44100[a{i}]')
    vlabels.append(f'[v{i}]'); alabels.append(f'[a{i}]')
nh = len(spec['hook']['cuts'])
fc.append(''.join(vlabels[:nh]) + f'concat=n={nh}:v=1:a=0,fade=t=out:st={hook_len - FADE:.3f}:d={FADE}[vh]')
fc.append(''.join(alabels[:nh]) + f'concat=n={nh}:v=0:a=1,afade=t=out:st={hook_len - FADE:.3f}:d={FADE}[ah]')
nb = len(cuts) - nh
fc.append(''.join(vlabels[nh:]) + f'concat=n={nb}:v=1:a=0,fade=t=in:st=0:d={FADE}[vb]')
fc.append(''.join(alabels[nh:]) + f'concat=n={nb}:v=0:a=1,afade=t=in:st=0:d={FADE}[ab0]')
fc.append('[vh][vb]concat=n=2:v=1:a=0,fps=30,split=2[vx][vy]')
fc.append(f'[vx]scale=-2:{H},crop={W}:{H},boxblur=28:2,eq=brightness=-0.18:saturation=1.2[bg]')
if spec.get('fit') == 'contain':
    fc.append(f'[vy]scale={W}:-2[fg]')
    fc.append(f'[bg][fg]overlay=0:{VY + (VH - 608) // 2}[base]')
else:
    fc.append(f'[vy]scale=-2:{VH},crop={W}:{VH}[fg]')
    fc.append(f'[bg][fg]overlay=0:{VY}[base]')
vchain = f'[base]ass={ovl}'
if spec['body'].get('captions'):
    vchain += f",ass={spec['body']['captions']}"
fc.append(vchain + '[v]')
gain = spec['body'].get('source_gain_db', 0)
fc.append(f'[ab0]volume={gain}dB[ab]')
if spec['body'].get('voice'):
    inputs += ['-i', spec['body']['voice']]
    fc.append(f'[{len(cuts)}:a]adelay={int(hook_len * 1000)}|{int(hook_len * 1000)},volume=2dB[vo]')
    fc.append('[ah][ab]concat=n=2:v=0:a=1[srcmix]')
    fc.append('[srcmix][vo]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5,aresample=44100[a]')
else:
    fc.append('[ah][ab]concat=n=2:v=0:a=1,loudnorm=I=-14:TP=-1.5,aresample=44100[a]')
cmd = ['ffmpeg', '-loglevel', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(fc), '-map', '[v]', '-map', '[a]',
       '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
       '-movflags', '+faststart', spec['out']]
subprocess.run(cmd, check=True)
print(spec['out'], f'{total:.2f}s (hook {hook_len:.2f}s)')
