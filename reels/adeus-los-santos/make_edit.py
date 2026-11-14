#!/usr/bin/env python3
"""Edit "Adeus, Los Santos": cenas do GTA V + áudio de despedida + legendas PT.

Uso: python3 make_edit.py <trailer_gtav.mp4> <audio.wav> <legendas.srt> <saida.mp4> [--work DIR]

Layout vertical 1080x1920: cena 16:9 no centro, a mesma cena desfocada no fundo,
título no topo e legenda embaixo da cena. No fim, cartela "Adeus, Los Santos" -> "Bem-vindo a Vice City".
"""
import argparse
import os
import re
import subprocess

FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_M = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
W, H, FPS = 1080, 1920, 30
XF = 0.6           # duração do crossfade entre cenas
END = 4.5          # duração da cartela final
CROP = "crop=1280:572:0:74"   # tira as faixas pretas do trailer

# (início, fim) de cada plano no trailer, na ordem em que entram no edit
SHOTS = [
    (8.00, 9.40),    # posto de salva-vidas no pôr do sol
    (39.00, 41.70),  # Los Santos de cima, helicóptero
    (20.10, 21.50),  # Franklin na Grove Street
    (10.95, 12.25),  # Michael na mansão
    (9.45, 10.90),   # os três protagonistas na montanha
    (33.15, 35.30),  # iate
    (12.30, 13.65),  # piscina da mansão
    (24.00, 26.30),  # avião sobre o Mount Chiliad
    (44.90, 46.40),  # lowrider no fim de tarde
    (61.40, 62.90),  # aviões no pôr do sol
    (70.65, 72.05),  # piscina com o skyline ao fundo
    (13.70, 16.10),  # logo sobre a cidade à noite
]


def run(cmd):
    subprocess.run(cmd, check=True)


def dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout)


def parse_srt(path):
    def t(s):
        h, m, rest = s.split(":")
        sec, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000
    blocks = re.split(r"\n\s*\n", open(path, encoding="utf-8").read().strip())
    subs = []
    for b in blocks:
        lines = b.strip().splitlines()
        a, z = lines[1].split(" --> ")
        subs.append((t(a), t(z), " ".join(lines[2:])))
    return subs


def wrap(text, n=26):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > n:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    return "\n".join(lines)


def render_shot(src, a, b, seconds, out):
    slow = seconds / (b - a)
    motion = f"setpts={slow:.4f}*PTS,minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir" if slow > 1.05 else f"fps={FPS}"
    grade = "eq=saturation=1.08:contrast=1.03,colorbalance=rs=0.04:bs=-0.03"   # leve tom quente/nostálgico
    fg_w = W
    fg_h = int(round(W * 572 / 1280 / 2) * 2)
    graph = (
        f"[0:v]{CROP},{motion},{grade},split[a][b];"
        f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,eq=brightness=-0.18[bg];"
        f"[b]scale={fg_w}:{fg_h},zoompan=z='min(1+0.0006*on,1.06)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={fg_w}x{fg_h}:fps={FPS}[fg];"
        f"[bg][fg]overlay=0:(H-h)/2-80,trim=duration={seconds:.3f},setpts=PTS-STARTPTS,format=yuv420p[v]"
    )
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{a}", "-t", f"{b - a:.3f}", "-i", src,
         "-filter_complex", graph, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trailer"); ap.add_argument("audio"); ap.add_argument("srt"); ap.add_argument("out")
    ap.add_argument("--work", default="work_adeus")
    o = ap.parse_args()
    os.makedirs(o.work, exist_ok=True)

    audio_len = dur(o.audio)
    n = len(SHOTS)
    seg = (audio_len + (n - 1) * XF) / n          # duração de cada cena para cobrir o áudio
    clips = []
    for i, (a, b) in enumerate(SHOTS):
        p = os.path.join(o.work, f"shot_{i:02d}.mp4")
        if not os.path.exists(p):              # reaproveita cenas já renderizadas
            tmp = p + ".part.mp4"
            render_shot(o.trailer, a, b, seg + XF, tmp)
            os.replace(tmp, p)
        clips.append(p)
        print(f"cena {i + 1}/{n} ok")

    # cartela final (duas fases)
    end = os.path.join(o.work, "end.mp4")
    t1 = os.path.join(o.work, "end1.txt"); open(t1, "w").write("ADEUS, LOS SANTOS")
    t2 = os.path.join(o.work, "end2.txt"); open(t2, "w").write("2013 – 2026")
    t3 = os.path.join(o.work, "end3.txt"); open(t3, "w").write("BEM-VINDO A VICE CITY")
    t4 = os.path.join(o.work, "end4.txt"); open(t4, "w").write("19 DE NOVEMBRO")
    half = END / 2
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
         "-f", "lavfi", "-i", f"color=c=0x0d0716:s={W}x{H}:r={FPS}:d={END}",
         "-vf",
         f"drawtext=fontfile={FONT}:textfile={t1}:fontsize=92:fontcolor=white:x=(w-tw)/2:y=(h/2)-120:enable='lt(t,{half})':alpha='min(t/0.6,1)',"
         f"drawtext=fontfile={FONT_M}:textfile={t2}:fontsize=58:fontcolor=0xbbbbbb:x=(w-tw)/2:y=(h/2)+20:enable='lt(t,{half})':alpha='min(t/0.6,1)',"
         f"drawtext=fontfile={FONT}:textfile={t3}:fontsize=84:fontcolor=0xff5fa2:x=(w-tw)/2:y=(h/2)-120:enable='gte(t,{half})':alpha='min((t-{half})/0.6,1)',"
         f"drawtext=fontfile={FONT_M}:textfile={t4}:fontsize=58:fontcolor=0x5fd3ff:x=(w-tw)/2:y=(h/2)+20:enable='gte(t,{half})':alpha='min((t-{half})/0.6,1)',"
         "format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", end])
    clips.append(end)

    # junta tudo com crossfade
    inputs, chain, last, offset = [], [], "[0:v]", 0.0
    for i, c in enumerate(clips):
        inputs += ["-i", c]
    lengths = [dur(c) for c in clips]
    for i in range(1, len(clips)):
        offset += lengths[i - 1] - XF
        lbl = f"[x{i}]"
        chain.append(f"{last}[{i}:v]xfade=transition=fade:duration={XF}:offset={offset:.3f}{lbl}")
        last = lbl

    # título fixo + legendas
    title1 = os.path.join(o.work, "title1.txt"); open(title1, "w").write("GTA 5 • A DESPEDIDA DA")
    title2 = os.path.join(o.work, "title2.txt"); open(title2, "w").write("NON-STOP-POP FM")
    over = [
        f"drawtext=fontfile={FONT_M}:textfile={title1}:fontsize=46:fontcolor=white:x=(w-tw)/2:y=390:enable='lt(t,{audio_len})'",
        f"drawtext=fontfile={FONT}:textfile={title2}:fontsize=72:fontcolor=0xff5fa2:x=(w-tw)/2:y=450:enable='lt(t,{audio_len})'",
    ]
    for i, (a, z, text) in enumerate(parse_srt(o.srt)):
        tf = os.path.join(o.work, f"sub_{i:02d}.txt")
        open(tf, "w", encoding="utf-8").write(wrap(text))
        over.append(
            f"drawtext=fontfile={FONT}:textfile={tf}:fontsize=54:fontcolor=white:line_spacing=12:"
            f"borderw=5:bordercolor=black@0.85:x=(w-tw)/2:y=1300:enable='between(t,{a},{z})'"
        )
    graph = ";".join(chain) + f";{last}" + ",".join(over) + "[v]"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs, "-i", o.audio,
         "-filter_complex", graph + f";[{len(clips)}:a]afade=t=out:st={audio_len - 1.5}:d=1.5[a]",
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", o.out])
    print("ok ->", o.out, f"({dur(o.out):.1f}s)")


if __name__ == "__main__":
    main()
