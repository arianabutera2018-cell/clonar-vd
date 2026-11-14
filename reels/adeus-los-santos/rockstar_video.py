#!/usr/bin/env python3
"""Baixa um vídeo oficial do site da Rockstar (rockstargames.com/videos/<id>).

Uso: python3 reels/adeus-los-santos/rockstar_video.py <id_do_video> <pasta_saida>
Ex.: python3 reels/adeus-los-santos/rockstar_video.py s6rrr5ao /tmp/gtav

Consulta a mesma API pública que o player do site usa (graph.rockstargames.com),
escolhe o arquivo de maior resolução e baixa com curl.
"""
import json
import os
import subprocess
import sys

QUERY = """query GET_VIDEO_DATA($id: String!, $locale: String!) {
  video(id: $id, locale: $locale) { id title files { resolution src } }
}"""


def main():
    vid, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    body = json.dumps({"operationName": "GET_VIDEO_DATA", "query": QUERY,
                       "variables": {"id": vid, "locale": "en_us"}})
    r = subprocess.run(["curl", "-s", "-m", "30", "-H", "Content-Type: application/json",
                        "-H", "Origin: https://www.rockstargames.com", "--data", body,
                        "https://graph.rockstargames.com/"], capture_output=True, text=True, check=True)
    video = (json.loads(r.stdout).get("data") or {}).get("video")
    if not video or not video.get("files"):
        sys.exit(f"sem arquivos para {vid}: {r.stdout[:300]}")

    def res(f):
        digits = "".join(ch for ch in str(f.get("resolution", "")) if ch.isdigit())
        return int(digits or 0)

    best = max(video["files"], key=res)
    src = best["src"] if best["src"].startswith("http") else "https:" + best["src"]
    dest = os.path.join(out_dir, f"{vid}.mp4")
    subprocess.run(["curl", "-sL", "-m", "600", "-o", dest, src], check=True)
    print(f"{video['title']} | {best.get('resolution')} -> {dest}")


if __name__ == "__main__":
    main()
