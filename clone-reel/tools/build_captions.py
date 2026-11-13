"""Word-timed ASS captions for the new narration, using display text and placed timings."""
import json, re, unicodedata, difflib, sys
root = sys.argv[1]
def norm(t):
    t = unicodedata.normalize('NFKD', t.lower())
    t = ''.join(c for c in t if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]', '', t)
speech = open(f'{root}/script/speech-lines.txt').read().split('\n')
display = open(f'{root}/script/new-lines.txt').read().strip().split('\n')
place = json.load(open(f'{root}/assets/voice/placement.json'))
split = next(i for i, s in enumerate(speech) if s.startswith('E daqui em diante'))
words_out = []  # (line, display_token, t0, t1) on the final timeline
redo = set(json.load(open(f'{root}/script/redo-lines.json')))
GROUPS = [(1, [i for i in range(0, split) if i not in redo]), (2, [i for i in range(split, len(speech)) if i not in redo]), (3, sorted(redo))]
for part, LINES in GROUPS:
    tr = json.load(open(f'{root}/assets/voice/part{part}.transcript.json'))
    W = [w for p in tr['passages'] for w in p['words']]
    T = [norm(w['text']) for w in W]
    S, own = [], []
    for li in LINES:
        sp, dp = speech[li].split(), display[li].split()
        assert len(sp) == len(dp), (li, sp, dp)
        for k, tok in enumerate(sp):
            if norm(tok): S.append(norm(tok)); own.append((li, dp[k]))
    m = {}
    for blk in difflib.SequenceMatcher(None, S, T, autojunk=False).get_matching_blocks():
        for k in range(blk.size): m[blk.a + k] = blk.b + k
    for k, (li, dtok) in enumerate(own):
        p = place[li]
        w = W[m[k]] if k in m and 'start_seconds' in W[m[k]] else None
        if w:
            t0 = p['start'] + (w['start_seconds'] - p['src_start']) / p['tempo']
            t1 = p['start'] + (w['end_seconds'] - p['src_start']) / p['tempo']
        else:
            t0 = t1 = None
        words_out.append([li, dtok, t0, t1])
# interpolate missing times
for i, w in enumerate(words_out):
    if w[2] is None:
        prev = next((x for x in reversed(words_out[:i]) if x[2] is not None), None)
        nxt = next((x for x in words_out[i + 1:] if x[2] is not None), None)
        w[2] = prev[3] if prev else nxt[2]; w[3] = nxt[2] if nxt else w[2] + 0.2
# chunk: max 4 words / 26 chars, break at line ends and after punctuation
chunks, cur = [], []
for i, w in enumerate(words_out):
    cur.append(w)
    nxt = words_out[i + 1] if i + 1 < len(words_out) else None
    text = ' '.join(x[1] for x in cur)
    if (nxt is None or nxt[0] != w[0] or len(cur) >= 4 or len(text) >= 22
            or re.search(r'[.,!?:;]$', w[1])):
        chunks.append(cur); cur = []
def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'
CREAM, INK, PINK = '&H00D3E6F3', '&H0030121E', '&H00A25FFF'  # ASS = &HAABBGGRR
head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Fala,Inter Display Black,34,{INK},{INK},{CREAM},&H64000000,0,0,0,0,100,100,1.5,0,3,9,0,2,40,40,118,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = []
for ci, c in enumerate(chunks):
    start = c[0][2]
    nxt_start = chunks[ci + 1][0][2] if ci + 1 < len(chunks) else c[-1][3] + 0.6
    end = min(c[-1][3] + 0.35, nxt_start) if nxt_start > c[-1][3] else c[-1][3]
    # one event per active word: active word in pink
    for wi, w in enumerate(c):
        a = w[2] if wi else start
        b = c[wi + 1][2] if wi + 1 < len(c) else end
        if b <= a: continue
        parts = [(f'{{\\c{PINK}}}{x[1].upper()}{{\\c{INK}}}' if j == wi else x[1].upper()) for j, x in enumerate(c)]
        ev.append(f'Dialogue: 0,{ts(a)},{ts(b)},Fala,,0,0,0,,{" ".join(parts)}')
open(f'{root}/assets/captions.ass', 'w').write(head + '\n'.join(ev) + '\n')
json.dump(words_out, open(f'{root}/assets/voice/words-timeline.json', 'w'), ensure_ascii=False)
print(len(words_out), 'words,', len(chunks), 'cues,', len(ev), 'events')
# Keep the end card clean, as in the reference: no captions once the channel card appears.
CUT = 465.30
def secs(s): h, m, x = s.split(':'); return int(h) * 3600 + int(m) * 60 + float(x)
txt = open(f'{root}/assets/captions.ass').read().split('\n')
keep = []
for ln in txt:
    if ln.startswith('Dialogue:'):
        f = ln.split(',', 9)
        if secs(f[1]) >= CUT: continue
        if secs(f[2]) > CUT: f[2] = ts(CUT); ln = ','.join(f)
    keep.append(ln)
open(f'{root}/assets/captions.ass', 'w').write('\n'.join(keep))
