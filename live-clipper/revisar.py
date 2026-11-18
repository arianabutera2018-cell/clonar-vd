#!/usr/bin/env python3
"""Ajuda o Claude a revisar clipes.

  python3 revisar.py OUT            -> lista clipes ainda não revisados e gera
                                       OUT/clips/NNN/folha.jpg (6 quadros)
  python3 revisar.py OUT N CHANCE "comentário"
                                    -> grava o veredito do Claude no meta.json
                                       e reescreve OUT/RELATORIO.md
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
                    f"`{os.path.relpath(os.path.join(folder, 'vertical_legendado.mp4'), out)}` |\n")


if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) == 2:
        for folder, m in clips(out):
            if not m.get("revisado_pelo_claude"):
                print(f"[{m['n']}] {m['tempo_live']} auto={m['chance']} nota={m['nota']} motivos={m['motivos']}\n"
                      f"    fala: {m['fala'][:300]}\n    folha: {sheet(folder)}")
        rewrite_report(out)
    else:
        n, chance, coment = int(sys.argv[2]), sys.argv[3], " ".join(sys.argv[4:])
        for folder, m in clips(out):
            if m["n"] == n:
                m.update(chance_final=chance, comentario_claude=coment, revisado_pelo_claude=True)
                json.dump(m, open(os.path.join(folder, "meta.json"), "w"), ensure_ascii=False, indent=1)
        rewrite_report(out)
        print("ok")
