"""Turn a narration + per-sentence clip pools into a short spec with word captions.

plan = {"name": "01-ps5", "hook": {...same as short.py...}, "body_title": "...",
        "pools": [[[s,e],...] per sentence], "source_gain_db": -16}
"""
import json, re, sys, unicodedata, difflib
root = '/home/user/clonar-vd/shorts'
plan = json.load(open(sys.argv[1])); name = plan['name']
sent = json.load(open(f'{root}/scripts/narration.json'))[name]
tr = json.load(open(f'{root}/assets/voice/{name}.json'))
W = [w for p in tr['passages'] for w in p['words'] if 'start_seconds' in w]
def norm(t):
    t = unicodedata.normalize('NFKD', t.lower()); t = ''.join(c for c in t if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]', '', t)
toks, own = [], []
for si, s in enumerate(sent):
    for tok in s.split():
        if norm(tok): toks.append(tok); own.append(si)
m = {}
for b in difflib.SequenceMatcher(None, [norm(t) for t in toks], [norm(w['text']) for w in W], autojunk=False).get_matching_blocks():
    for k in range(b.size): m[b.a + k] = b.b + k
times = []
for k, tok in enumerate(toks):
    if k in m: times.append([W[m[k]]['start_seconds'], W[m[k]]['end_seconds']])
    else: times.append(None)
for k in range(len(times)):  # fill gaps
    if times[k] is None:
        prev = next((times[j] for j in range(k - 1, -1, -1) if times[j]), [0, 0])
        times[k] = [prev[1], prev[1] + 0.15]
voice_end = W[-1]['end_seconds']
body_len = voice_end + 0.7
# sentence boundaries -> body cuts
starts = [min(times[k][0] for k in range(len(toks)) if own[k] == si) for si in range(len(sent))]
starts[0] = 0.0
bounds = starts + [body_len]
cuts = []
for si, pool in enumerate(plan['pools']):
    need = bounds[si + 1] - bounds[si]
    for s, e in pool:
        if need <= 0.05: break
        d = min(e - s, need); cuts.append([s, round(s + d, 3)]); need -= d
    if need > 0.05:  # stretch last clip pool by reusing from its start
        s, e = pool[-1]; cuts.append([s, round(s + need, 3)])
hook_len = sum(e - s for s, e in plan['hook']['cuts'])
# captions (timeline = hook_len + voice time)
def ts(x): return f'0:{int(x // 60):02d}:{x % 60:05.2f}'
chunks, cur = [], []
for k, tok in enumerate(toks):
    cur.append(k)
    if len(cur) >= 3 or re.search(r'[.,!?:]$', tok) or k + 1 == len(toks) or own[k + 1] != own[k]:
        chunks.append(cur); cur = []
PINK, INK = '&H00A25FFF', '&H00FFFFFF'
ev = []
for ci, c in enumerate(chunks):
    end = min(times[c[-1]][1] + 0.3, times[chunks[ci + 1][0]][0]) if ci + 1 < len(chunks) else times[c[-1]][1] + 0.5
    for wi, k in enumerate(c):
        a = times[k][0] if wi else times[c[0]][0]
        b = times[c[wi + 1]][0] if wi + 1 < len(c) else end
        if b <= a: continue
        txt = ' '.join((f'{{\\c{PINK}}}{toks[j].upper()}{{\\c{INK}}}' if j == k else toks[j].upper()) for j in c)
        pop = '{\\fscx92\\fscy92\\t(0,90,\\fscx100\\fscy100)}' if wi == 0 else ''
        ev.append(f'Dialogue: 0,{ts(hook_len + a)},{ts(hook_len + b)},Fala,,0,0,0,,{pop}{txt}')
head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Fala,Inter Display Black,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,7,4,8,70,70,1420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
cap = f'{root}/assets/{name}.captions.ass'
open(cap, 'w').write(head + '\n'.join(ev) + '\n')
spec = {"fit": plan.get("fit"), "out": f"exports/{name}.mp4", "source": "sources/extended-look-1080p.mp4", "hook": plan['hook'],
        "body": {"cuts": cuts, "title": plan.get('body_title'), "voice": f"assets/voice/{name}.mp3",
                 "captions": f"assets/{name}.captions.ass", "source_gain_db": plan.get('source_gain_db', -16)}}
json.dump(spec, open(f'{root}/specs/{name}.json', 'w'), indent=1)
print(name, 'body', round(body_len, 2), 's;', len(cuts), 'cuts;', len(ev), 'caption events')
