#!/usr/bin/env python3
"""Ajuda o Claude a revisar clipes.

  python3 revisar.py OUT            -> lista clipes ainda não revisados e gera
                                       OUT/clips/NNN/folha.jpg (6 quadros)
  python3 revisar.py OUT N CHANCE "comentário"
                                    -> grava o veredito do Claude no meta.json
                                       e reescreve OUT/RELATORIO.md
  python3 revisar.py OUT N corrigir "errado" "certo"
                                    -> salva a correção (vale p/ clipes futuros) e
                                       refaz a legenda do clipe N
  python3 revisar.py OUT N estender SEGUNDOS
                                    -> refaz o original.mp4 do clipe N com mais SEGUNDOS no fim
  python3 revisar.py OUT N refazer  -> retranscreve o clipe N e refaz a legenda
CHANCE: ALTA | MÉDIA | INCERTA | DESCARTAR
"""
import json, os, subprocess, sys


def clips(out):
    d = os.path.join(out, "clips")
    for name in sorted(os.listdir(d)):
        m = os.path.join(d, name, "meta.json")
        if os.path.exists(m):
            yield os.path.join(d, name), json.load(open(m))


def sheet(folder):
    out = os.path.join(folder, "folha.jpg")
    if not os.path.exists(out):
        src = os.path.join(folder, "original.mp4")
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                                   capture_output=True, text=True).stdout or 30)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-vf",
                        f"fps=6/{dur:.1f},scale=480:-2,tile=3x2", "-frames:v", "1", out])
    return out


def rewrite_report(out):
    rows = list(clips(out))
    order = {"ALTA": 0, "MÉDIA": 1, "INCERTA": 2, "DESCARTAR": 3}
    with open(os.path.join(out, "RELATORIO.md"), "w") as f:
        f.write("# Clipes da live (ordenados por chance de viralizar)\n\n"
                "Chance = veredito do Claude quando revisado; senão, nota automática (áudio + fala).\n\n"
                "| # | Tempo na live | Chance | Revisado? | Por quê | Fala | Arquivo |\n|---|---|---|---|---|---|---|\n")
        for folder, m in sorted(rows, key=lambda r: (order.get(r[1].get("chance_final", r[1]["chance"]), 9), -r[1]["nota"])):
            ch = m.get("chance_final", m["chance"])
            why = m.get("comentario_claude") or "; ".join(m["motivos"])
            f.write(f"| {m['n']} | {m['tempo_live']} | **{ch}** | {'sim' if m.get('revisado_pelo_claude') else 'não'} | "
                    f"{why.replace('|', '/')} | {m['fala'][:100].replace('|', '/')} | "
                    f"`{os.path.relpath(os.path.join(folder, 'original.mp4'), out)}` |\n")


if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) == 2:
        for folder, m in clips(out):
            if not m.get("revisado_pelo_claude"):
                print(f"[{m['n']}] {m['tempo_live']} auto={m['chance']} nota={m['nota']} motivos={m['motivos']}\n"
                      f"    fala: {m['fala'][:300]}\n    folha: {sheet(folder)}")
        rewrite_report(out)
    elif sys.argv[3] == "estender":
        n, extra = int(sys.argv[2]), int(sys.argv[4])
        folder, m = next((f, m) for f, m in clips(out) if m["n"] == n)
        if m.get("seg_fim") is None: sys.exit("clipe antigo, sem índice de segmentos")
        last = m["seg_fim"] + -(-extra // 10)
        segs = [os.path.join(m["segdir"], f"seg_{k:06d}.ts") for k in range(m["seg_inicio"], last + 1)]
        faltam = [x for x in segs if not os.path.exists(x)]
        if faltam: sys.exit(f"segmentos já apagados ou ainda não gravados: {len(faltam)}")
        lst = os.path.join(folder, "list.txt")
        open(lst, "w").write("".join(f"file '{x}'\n" for x in segs))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                        "-bsf:a", "aac_adtstoasc", "-movflags", "+faststart", os.path.join(folder, "original.mp4")], check=True)
        os.remove(lst); m["seg_fim"] = last
        json.dump(m, open(os.path.join(folder, "meta.json"), "w"), ensure_ascii=False, indent=1)
        print(f"clipe {n} agora tem {(last - m['seg_inicio'] + 1) * 10}s")
    elif sys.argv[3] in ("corrigir", "refazer"):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import legendas
        n = int(sys.argv[2])
        folder, m = next((f, m) for f, m in clips(out) if m["n"] == n)
        pj = os.path.join(folder, "palavras.json")
        if sys.argv[3] == "corrigir":
            legendas.add_correction(sys.argv[4], sys.argv[5])
        if sys.argv[3] == "refazer" or not os.path.exists(pj):
            from faster_whisper import WhisperModel
            raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", os.path.join(folder, "original.mp4"), "-ac", "1",
                                  "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
            import numpy as np
            segs, _ = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=2).transcribe(
                np.frombuffer(raw, np.float32), language="pt", word_timestamps=True, vad_filter=True,
                initial_prompt=legendas.PROMPT)
            words = [dict(w=w.word.strip(), s=w.start, e=w.end) for sg in segs for w in (sg.words or [])]
        else:
            words = json.load(open(pj, encoding="utf-8"))
        m["fala"] = legendas.build_subs(folder, legendas.fix_words(words))
        legendas.render_vertical(folder)
        json.dump(m, open(os.path.join(folder, "meta.json"), "w"), ensure_ascii=False, indent=1)
        rewrite_report(out)
        print("legenda refeita:", m["fala"][:300])
    else:
        n, chance, coment = int(sys.argv[2]), sys.argv[3], " ".join(sys.argv[4:])
        for folder, m in clips(out):
            if m["n"] == n:
                m.update(chance_final=chance, comentario_claude=coment, revisado_pelo_claude=True)
                json.dump(m, open(os.path.join(folder, "meta.json"), "w"), ensure_ascii=False, indent=1)
        rewrite_report(out)
        print("ok")
