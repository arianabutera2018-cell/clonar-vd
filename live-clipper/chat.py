"""Monitor de chat por HTTP (sem WebSocket).

Twitch: recent-messages.robotty.de (serviço público que guarda as mensagens recentes).
Kick:   kick.com/api/v2/channels/{id}/messages (últimas ~25 mensagens).

Guarda (timestamp, texto) de cada mensagem nova; o clipper pergunta
`window(t0, t1)` para saber quantas mensagens e reações caíram num intervalo.
"""
import json, re, threading, time, unicodedata, urllib.request
from collections import deque
from datetime import datetime

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"

# reações típicas do chat (regex em texto normalizado, peso)
CHAT_HYPE = [
    (r"k{4,}|kkk+|hahah|rsrs", "risada", 1.0),
    (r"\b(clip|clipa|clipe|clipar)\b", "CLIPA", 3.0),
    (r"\?{3,}", "????", 1.5),
    (r"\b(kekw|lul|lol|omegalul|icant|lmao|lmfao)\b", "KEKW", 1.0),
    (r"\b(pog|pogchamp|poggers|pogu|w+)\b", "POG", 1.0),
    (r"\b(mds|meu deus|caralho|crl|pqp|porra|nossa|socorro|absurdo|insano)\b", "choque", 1.0),
    (r"\b(f|rip|morreu)\b", "F", 0.8),
]


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


class ChatMonitor:
    def __init__(self, url, log=print):
        self.log = log
        self.msgs = deque(maxlen=50000)      # (ts, texto normalizado)
        self.seen = deque(maxlen=5000); self.seen_set = set()
        self.ok = False
        m = re.search(r"(twitch\.tv|kick\.com)/([A-Za-z0-9_\-]+)", url)
        self.platform, self.channel = (m.group(1).split(".")[0], m.group(2).lower()) if m else (None, None)
        self.kick_id = None

    def start(self):
        if not self.platform:
            self.log("chat: plataforma não suportada; seguindo sem chat"); return self
        threading.Thread(target=self._loop, daemon=True).start(); return self

    def _add(self, mid, ts, text):
        if mid in self.seen_set: return
        self.seen.append(mid); self.seen_set.add(mid)
        if len(self.seen_set) > 4500: self.seen_set = set(self.seen)
        self.msgs.append((ts, norm(text)))

    def _poll_twitch(self):
        d = get_json(f"https://recent-messages.robotty.de/api/v2/recent-messages/{self.channel}?limit=300")
        for raw in d.get("messages", []):
            if " PRIVMSG " not in raw: continue
            tags = dict(kv.split("=", 1) for kv in raw[1:].split(" ", 1)[0].split(";") if "=" in kv)
            mid = tags.get("id") or raw[-60:]
            ts = int(tags.get("tmi-sent-ts", time.time() * 1000)) / 1000
            self._add(mid, ts, raw.split(" PRIVMSG ", 1)[1].split(" ", 1)[-1].removeprefix(":"))

    def _poll_kick(self):
        if self.kick_id is None:
            self.kick_id = get_json(f"https://kick.com/api/v2/channels/{self.channel}")["id"]
        d = get_json(f"https://kick.com/api/v2/channels/{self.kick_id}/messages")
        for m in d.get("data", {}).get("messages", []):
            ts = datetime.fromisoformat(m["created_at"].replace("Z", "+00:00")).timestamp()
            self._add(m["id"], ts, m.get("content", ""))

    def _loop(self):
        poll, every = (self._poll_twitch, 4) if self.platform == "twitch" else (self._poll_kick, 2)
        errs = 0
        while True:
            try:
                poll()
                if not self.ok: self.log(f"chat {self.platform}/{self.channel}: conectado"); self.ok = True
                errs = 0
            except Exception as e:
                errs += 1
                if errs in (1, 10, 100): self.log(f"chat: erro ({errs}x): {e}")
            time.sleep(every if errs == 0 else min(30, every * errs))

    def window(self, t0, t1):
        """-> (n_mensagens, pontos_de_reação, contagem_por_tipo) entre t0 e t1 (epoch s)."""
        n, pts, kinds = 0, 0.0, {}
        for ts, txt in list(self.msgs):
            if t0 <= ts < t1:
                n += 1
                for rx, name, w in CHAT_HYPE:
                    if re.search(rx, txt):
                        pts += w; kinds[name] = kinds.get(name, 0) + 1
        return n, pts, kinds
