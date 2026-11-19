"""Legendas: correções de transcrição, arquivo .ass (estilo TikTok) e render vertical."""
import json, os, re, subprocess, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
CORR_FILE = os.path.join(HERE, "correcoes.json")

# contexto dado ao Whisper: nomes e gírias que ele deve reconhecer
PROMPT = ("Live do Coringa na Kick. Gírias: sossega o facho, tá ligado, rapaziada, mano, véi, "
          "KKKKK, pô, caraca, GTA 6, Vice City, Lucia, Jason.")


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^\w ]", "", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip()


def load_corrections():
    try:
        return json.load(open(CORR_FILE, encoding="utf-8"))
    except Exception:
        return {}


def add_correction(wrong, right):
    c = load_corrections(); c[wrong] = right
    json.dump(c, open(CORR_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def fix_words(words, corrections=None):
    """words: [{'w','s','e'}]. Troca sequências erradas (comparação sem acento/pontuação)
    pela forma certa, distribuindo o tempo entre as palavras novas."""
    corrections = load_corrections() if corrections is None else corrections
    rules = sorted(((norm(k).split(), v) for k, v in corrections.items()), key=lambda r: -len(r[0]))
    out, i = [], 0
    while i < len(words):
        for pat, right in rules:
            k = len(pat)
            if pat and [norm(x["w"]) for x in words[i:i + k]] == pat:
                s, e = words[i]["s"], words[i + k - 1]["e"]
                tail = re.findall(r"[.,!?…]+$", words[i + k - 1]["w"].strip())
                new = right.split(); step = (e - s) / len(new)
                for j, t in enumerate(new):
                    out.append({"w": t + (tail[0] if tail and j == len(new) - 1 else ""),
                                "s": s + j * step, "e": s + (j + 1) * step})
                i += k; break
        else:
            out.append(words[i]); i += 1
    return out


def write_ass(words, path):
    def ts(t):
        t = max(t, 0); return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
    hdr = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\n"
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
           "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
           "Style: Default,DejaVu Sans,78,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,2,2,60,60,430,1\n\n"
           "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    lines, chunk = [], []
    for w in words:
        chunk.append(w)
        if len(chunk) == 3 or w["w"].strip()[-1:] in ".!?,":
            lines.append(chunk); chunk = []
    if chunk: lines.append(chunk)
    with open(path, "w", encoding="utf-8") as f:
        f.write(hdr)
        for c in lines:
            for j, w in enumerate(c):   # palavra atual em amarelo
                end = c[j + 1]["s"] if j + 1 < len(c) else w["e"]
                txt = " ".join(("{\\c&H00FFFF&}" + x["w"].strip().upper() + "{\\c&HFFFFFF&}") if x is w
                               else x["w"].strip().upper() for x in c)
                f.write(f"Dialogue: 0,{ts(w['s'])},{ts(end)},Default,,0,0,0,,{txt}\n")


def build_subs(folder, words):
    """Grava palavras.json, legenda.ass e fala.txt; devolve o texto completo."""
    json.dump(words, open(os.path.join(folder, "palavras.json"), "w", encoding="utf-8"), ensure_ascii=False)
    write_ass(words, os.path.join(folder, "legenda.ass"))
    full = " ".join(w["w"].strip() for w in words)
    with open(os.path.join(folder, "fala.txt"), "w", encoding="utf-8") as f: f.write(full + "\n")
    return full


def render_vertical(folder):
    orig = os.path.join(folder, "original.mp4"); ass = os.path.join(folder, "legenda.ass")
    vf = ("[0:v]fps=30,split[a][b];[a]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,"
          "boxblur=10:1,eq=brightness=-0.08,scale=1080:1920[bg];"
          f"[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2-120,subtitles='{ass}'")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", orig, "-filter_complex", vf,
                    "-threads", "2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "copy",
                    "-movflags", "+faststart", os.path.join(folder, "vertical_legendado.mp4")], check=True)
