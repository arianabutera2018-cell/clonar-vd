"""Map each script line to start/end times in the generated narration, using WhisperX word times."""
import json, re, unicodedata, difflib, sys
root = sys.argv[1]
def norm(t):
    t = unicodedata.normalize('NFKD', t.lower())
    t = ''.join(c for c in t if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]', '', t)
lines = open(f'{root}/script/speech-lines.txt').read().split('\n')
split = next(i for i, s in enumerate(lines) if s.startswith('E daqui em diante'))
out = []
redo = set(json.load(open(f'{root}/script/redo-lines.json')))
GROUPS = [(1, [i for i in range(0, split) if i not in redo]), (2, [i for i in range(split, len(lines)) if i not in redo]), (3, sorted(redo))]
for part, LINES in GROUPS:
    tr = json.load(open(f'{root}/assets/voice/part{part}.transcript.json'))
    words = [w for p in tr['passages'] for w in p['words']]
    # fill missing times from neighbours
    for i, w in enumerate(words):
        if 'start_seconds' not in w:
            prev = next((x for x in reversed(words[:i]) if 'end_seconds' in x), None)
            w['start_seconds'] = w['end_seconds'] = prev['end_seconds'] if prev else 0.0
    T = [norm(w['text']) for w in words]
    S, owner = [], []
    for li in LINES:
        for tok in lines[li].split():
            n = norm(tok)
            if n: S.append(n); owner.append(li)
    sm = difflib.SequenceMatcher(None, S, T, autojunk=False)
    m = {}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): m[blk.a + k] = blk.b + k
    for li in LINES:
        idx = [m[k] for k in range(len(S)) if owner[k] == li and k in m]
        if not idx:
            out.append(dict(i=li, part=part, start=None, end=None)); continue
        out.append(dict(i=li, part=part, start=words[min(idx)]['start_seconds'], end=words[max(idx)]['end_seconds'],
                        matched=len(idx), total=sum(1 for k in range(len(S)) if owner[k] == li)))
out.sort(key=lambda o: o['i'])
json.dump(out, open(f'{root}/assets/voice/line-times.json', 'w'), indent=1)
bad = [o for o in out if o['start'] is None or o['matched'] < 0.6 * o['total']]
print(len(out), 'lines;', 'weak:', [(o['i'], o.get('matched'), o.get('total')) for o in bad])
