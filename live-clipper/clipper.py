#!/usr/bin/env python3
"""Live clipper: grava uma live (Twitch/Kick/etc. via yt-dlp), detecta momentos
com potencial viral pelo áudio (gritos, explosões) e pela fala do streamer
(Whisper), corta o trecho, gera versão vertical 9:16 com legendas e escreve um
relatório classificando cada clipe.

Uso: python3 clipper.py URL_DA_LIVE [--out DIR] [--model small]
"""
import argparse, json, os, re, subprocess, sys, threading, time, unicodedata
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chat import ChatMonitor
import legendas

SEG = 10            # segundos por segmento gravado
PRE = 30            # segundos antes do pico incluídos no clipe
POST = 20           # segundos depois do pico
COOLDOWN = 45       # mínimo entre clipes
KEEP_SEGS = 90      # segmentos mantidos no disco (15 min)

# palavras/expressões de reação em PT-BR (peso)
HYPE = {
    "meu deus": 3, "nao acredito": 3, "que isso": 2, "o que": 1, "caralho": 3, "porra": 2,
    "puta que pariu": 4, "puta merda": 3, "mano": 1, "olha isso": 2, "olha ai": 1,
    "socorro": 3, "nossa": 2, "absurdo": 3, "insano": 3, "surreal": 3, "clipa": 4,
    "clip": 3, "corta": 2, "vai vai vai": 3, "nao nao nao": 3, "ai meu deus": 4,
    "que lindo": 2, "que grafico": 3, "grafico": 2, "perfeito": 2, "morri": 3,
    "morreu": 2, "kkk": 2, "ha ha": 2, "rapaz": 2, "jesus": 2, "pqp": 3, "vsf": 3,
    "inacreditavel": 3, "bizarro": 3, "mentira": 2, "ue": 1, "gente": 1, "explodiu": 3,
    "policia": 1, "lucia": 2, "jason": 2, "vice city": 2, "gta": 1, "loucura": 3,
    "chorando": 3, "arrepiei": 3, "arrepio": 3, "eita": 2, "oxe": 2, "fodeu": 3,
}


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def log(*a):
    print(datetime.now().strftime("%H:%M:%S"), *a, flush=True)


def fmt_t(sec):
    sec = int(sec); return f"{sec//3600:02d}:{sec%3600//60:02d}:{sec%60:02d}"


class Clipper:
    def __init__(self, url, out, model_name, quality, vertical=False):
        self.url, self.out, self.quality, self.vertical = url, out, quality, vertical
        self.segdir = os.path.join(out, "_segments"); self.clipdir = os.path.join(out, "clips")
        os.makedirs(self.segdir, exist_ok=True); os.makedirs(self.clipdir, exist_ok=True)
        self.report = os.path.join(out, "RELATORIO.md")
        if not os.path.exists(self.report):
            with open(self.report, "w") as f:
                f.write(f"# Clipes da live\n\nFonte: {url}\nInício: {datetime.now():%d/%m/%Y %H:%M}\n\n"
                        "| # | Tempo na live | Chance | Nota | Por quê | Fala |\n|---|---|---|---|---|---|\n")
        from faster_whisper import WhisperModel
        log("carregando Whisper: detecção=base, legendas=" + model_name)
        self.fast = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=2)
        self.whisper = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=2)
        self.wlock = threading.Lock()
        self.loud_hist = deque(maxlen=60)       # pico dB por segmento (10 min)
        self.wps_hist = deque(maxlen=60)        # palavras/seg por segmento
        self.seginfo = {}                       # idx -> dict(score, reasons, text)
        self.last_clip_t = -1e9
        self.n_clips = len([d for d in os.listdir(self.clipdir) if d[:3].isdigit()])
        self.render = ThreadPoolExecutor(1)
        self.rec = None
        self.chat = ChatMonitor(url, log).start()
        self.chat_hist = deque(maxlen=60)       # msgs/seg do chat por segmento

    # ---------- gravação ----------
    def start_recorder(self):
        start = self.max_existing() + 1 if self.has_segs() else 0
        self.rec_start = start
        if re.search(r"twitch\.tv|kick\.com", self.url):
            src = (f"streamlink --twitch-disable-ads --stdout --retry-streams 10 --retry-open 5 "
                   f"'{self.url}' 1080p60,1080p,720p60,best 2>>'{self.out}/gravador.log'")
        else:
            src = f"yt-dlp --no-warnings -q --no-part -f '{self.quality}' -o - '{self.url}'"
        cmd = (f"{src} | ffmpeg -loglevel error -fflags +genpts+discardcorrupt -i - -c copy -f segment "
               f"-segment_time {SEG} -segment_start_number {start} -reset_timestamps 1 '{self.segdir}/seg_%06d.ts'")
        log("gravando:", self.url)
        self.rec = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)

    def seg_path(self, i): return os.path.join(self.segdir, f"seg_{i:06d}.ts")

    # ---------- análise ----------
    def audio(self, path):
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "16000",
                              "-f", "f32le", "-"], capture_output=True).stdout
        return np.frombuffer(raw, np.float32)

    def analyze(self, i):
        a = self.audio(self.seg_path(i))
        if a.size < 16000: return None
        win = a[: a.size // 8000 * 8000].reshape(-1, 8000)      # janelas de 0.5s
        db = 20 * np.log10(np.sqrt((win ** 2).mean(1)) + 1e-9)
        peak = float(np.percentile(db, 95))
        segs, _ = self.fast.transcribe(a, language="pt", vad_filter=True, beam_size=1, initial_prompt=legendas.PROMPT)
        text = " ".join(s.text.strip() for s in segs)
        nt =norm(text); words = len(nt.split()); wps = words / SEG
        score, reasons = 0.0, []
        if len(self.loud_hist) >= 6:
            base = np.median(self.loud_hist); jump = peak - base
            if jump > 4: score += min((jump - 4) * 0.8, 6); reasons.append(f"volume +{jump:.0f}dB")
        if len(self.wps_hist) >= 6:
            wb = np.median(self.wps_hist)
            if wps > wb * 1.6 and wps > 2.5: score += 1.5; reasons.append("fala acelerada")
        hits = [k for k in HYPE if re.search(rf"\b{re.escape(k)}\b", nt)]
        if hits:
            score += min(sum(HYPE[k] for k in hits), 8); reasons.append("reação: " + ", ".join(hits[:5]))
        rep = re.findall(r"\b(\w+)( \1){2,}\b", nt)
        if rep: score += 2; reasons.append("repetição (" + rep[0][0] + "...)")
        if text.count("!") >= 2: score += 1
        # chat: reage com atraso (latência da live), então olha de 12s antes a 6s depois do fim do bloco
        if self.chat.ok:
            end = os.path.getmtime(self.seg_path(i)); t1 = min(time.time(), end + 6)
            n, pts, kinds = self.chat.window(end - 12, t1); rate = n / max(t1 - (end - 12), 1)
            if len(self.chat_hist) >= 6:
                base = max(np.median(self.chat_hist), 0.2); ratio = rate / base
                if ratio > 1.8: score += min((ratio - 1.8) * 2 + 1, 5); reasons.append(f"chat {ratio:.1f}x mais rápido")
            frac = pts / n if n else 0
            if n >= 5 and frac > 0.3:
                score += min(frac * 5, 4)
                reasons.append("chat: " + ", ".join(f"{k} x{v}" for k, v in sorted(kinds.items(), key=lambda x: -x[1])[:3]))
            self.chat_hist.append(rate)
        self.loud_hist.append(peak); self.wps_hist.append(wps)
        self.seginfo[i] = dict(score=score, reasons=reasons, text=text, peak=peak)
        log(f"seg {i} {fmt_t(i*SEG)} nota={score:.1f} {'; '.join(reasons)} | {text[:70]}")
        return score

    # ---------- clipe ----------
    def make_clip(self, center_i):
        self.n_clips += 1; n = self.n_clips
        first = max(0, center_i - PRE // SEG); last = center_i + POST // SEG
        info = max((self.seginfo.get(k, {"score": 0}) for k in range(first, last + 1)), key=lambda d: d["score"])
        total = sum(self.seginfo.get(k, {}).get("score", 0) for k in range(first, last + 1))
        tlive = fmt_t(first * SEG)
        d = os.path.join(self.clipdir, f"{n:03d}_{tlive.replace(':', '')}"); os.makedirs(d, exist_ok=True)
        lst = os.path.join(d, "list.txt")
        with open(lst, "w") as f:
            for k in range(first, last + 1):
                if os.path.exists(self.seg_path(k)): f.write(f"file '{os.path.abspath(self.seg_path(k))}'\n")
        orig = os.path.join(d, "original.mp4")
        if self.vertical:
            enc = ["-threads", "2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-b:a", "160k"]
        else:   # 16:9 na qualidade original da live, sem recodificar
            enc = ["-c", "copy", "-bsf:a", "aac_adtstoasc"]
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, *enc,
                        "-movflags", "+faststart", orig])
        os.remove(lst)
        if not self.vertical:
            full = " ".join(self.seginfo.get(k, {}).get("text", "") for k in range(first, last + 1)).strip()
            with open(os.path.join(d, "fala.txt"), "w", encoding="utf-8") as f: f.write(full + "\n")
        else:
            full = self.subtitle(d, orig)
        self.finish_clip(n, d, orig, tlive, total, info, full)

    def subtitle(self, d, orig):
        a = self.audio(orig)
        with self.wlock:
            segs, _ = self.whisper.transcribe(a, language="pt", word_timestamps=True, vad_filter=True,
                                              initial_prompt=legendas.PROMPT)
            words = [dict(w=w.word.strip(), s=w.start, e=w.end) for s in segs for w in (s.words or [])]
        full = legendas.build_subs(d, legendas.fix_words(words))
        legendas.render_vertical(d)
        return full

    def finish_clip(self, n, d, orig, tlive, total, info, full):
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(PRE), "-i", orig, "-frames:v", "1",
                        "-vf", "scale=640:-2", os.path.join(d, "capa.jpg")])
        chance = "ALTA" if total >= 12 or info["score"] >= 9 else ("MÉDIA" if total >= 7 else "INCERTA")
        meta = dict(n=n, tempo_live=tlive, chance=chance, nota=round(total, 1), motivos=info["reasons"],
                    fala=full, pasta=d, revisado_pelo_claude=False)
        json.dump(meta, open(os.path.join(d, "meta.json"), "w"), ensure_ascii=False, indent=1)
        with open(self.report, "a") as f:
            f.write(f"| {n} | {tlive} | **{chance}** | {total:.1f} | {'; '.join(info['reasons'])} | "
                    f"{full[:120].replace('|', '/')} |\n")
        log(f"CLIPE {n} pronto ({chance}) -> {d}")

    # ---------- loop ----------
    def run(self, threshold):
        self.start_recorder()
        i = self.rec_start
        pending, idle = None, 0
        while True:
            nxt = self.seg_path(i + 1)
            if not os.path.exists(nxt):           # segmento i ainda sendo escrito
                if self.rec.poll() is not None:
                    idle += 1
                    if idle > 3:
                        log("gravação parou; tentando reconectar..."); time.sleep(20)
                        if self.reconnect_tries() is False: break
                        i = self.rec_start; idle = 0
                time.sleep(2); continue
            idle = 0
            try: s = self.analyze(i) or 0
            except Exception as e: log("erro análise", i, e); s = 0
            if pending is not None and i >= pending + POST // SEG:
                self.render.submit(self.safe_clip, pending); pending = None
            if s >= threshold and pending is None and i * SEG - self.last_clip_t >= COOLDOWN:
                pending = i; self.last_clip_t = i * SEG
                log(f">>> momento detectado em {fmt_t(i*SEG)} (nota {s:.1f}), aguardando {POST}s")
            old = self.seg_path(i - KEEP_SEGS)
            if os.path.exists(old) and (pending is None or i - KEEP_SEGS < pending - PRE // SEG): os.remove(old)
            i += 1
        if pending is not None: self.render.submit(self.safe_clip, pending)
        self.render.shutdown(wait=True); log("FIM. Relatório:", self.report)

    def has_segs(self):
        return any(f.endswith(".ts") for f in os.listdir(self.segdir))

    def max_existing(self):
        return max([int(f[4:10]) for f in os.listdir(self.segdir) if f.endswith(".ts")] or [0])

    tries = 0
    def reconnect_tries(self):
        self.tries += 1
        if self.tries > 6: return False
        self.start_recorder(); return True

    def safe_clip(self, i):
        try: self.make_clip(i)
        except Exception as e: log("erro ao gerar clipe", i, e)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("url"); p.add_argument("--out", default="live_out")
    p.add_argument("--model", default="small"); p.add_argument("--threshold", type=float, default=5.0)
    p.add_argument("--quality", default="best[height<=720]/best")
    p.add_argument("--vertical", action="store_true", help="gera também versão 9:16 legendada")
    a = p.parse_args()
    Clipper(a.url, a.out, a.model, a.quality, a.vertical).run(a.threshold)
