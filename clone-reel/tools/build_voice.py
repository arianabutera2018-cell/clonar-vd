"""Place each new narration line at its original line's start time (elastic, with gentle speed-up)."""
import json, subprocess, sys, os, wave
import numpy as np
root = sys.argv[1]
SR = 44100
L = json.load(open(f'{root}/script/lines.json'))
T = json.load(open(f'{root}/assets/voice/line-times.json'))
total = 470.697
buf = np.zeros(int(total * SR) + SR, dtype=np.float32)
tmp = f'{root}/assets/voice/_seg.wav'
placed, prev_end, maxdrift = [], 0.0, 0.0
for k, (l, t) in enumerate(zip(L, T)):
    nxt = L[k + 1]['start'] if k + 1 < len(L) else total
    s = max(0.0, t['start'] - 0.04); e = t['end'] + 0.10
    d = e - s
    start = max(l['start'] - 0.04, prev_end + 0.05)
    avail = (nxt + 0.25) - start          # may spill 0.25 s into the next line's slot
    tempo = min(1.25, max(1.0, d / max(avail, 0.3)))
    filt = f'atempo={tempo:.4f}' if tempo > 1.001 else 'anull'
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{s:.3f}', '-to', f'{e:.3f}',
                    '-i', f'{root}/assets/voice/part{t["part"]}.mp3', '-af', filt + ',afade=t=in:d=0.02',
                    '-ac', '1', '-ar', str(SR), tmp], check=True)
    with wave.open(tmp) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    i0 = int(start * SR); buf[i0:i0 + len(a)] += a[:len(buf) - i0]
    end = start + len(a) / SR
    placed.append(dict(i=k, start=round(start, 3), end=round(end, 3), tempo=round(tempo, 3),
                       src_start=s, src_part=t['part']))
    maxdrift = max(maxdrift, start - l['start']); prev_end = end
os.remove(tmp)
buf = np.clip(buf[:int(total * SR)], -1, 1)
with wave.open(f'{root}/assets/voice/voice-track.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((buf * 32767).astype(np.int16).tobytes())
json.dump(placed, open(f'{root}/assets/voice/placement.json', 'w'), indent=1)
print('max drift %.2fs' % maxdrift, '| sped up:', sum(p['tempo'] > 1.001 for p in placed),
      '| max tempo', max(p['tempo'] for p in placed), '| last end %.2f' % placed[-1]['end'])
