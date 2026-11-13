#!/usr/bin/env bash
# Final assembly: original picture + word captions + original music/SFX (Demucs no_vocals) + new voice.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=${1:-exports/clone-gta6.mp4}; shift || true
EXTRA=("$@")   # e.g. -t 30 for a preview
mkdir -p "$(dirname "$OUT")"
ffmpeg -loglevel error -stats -y \
  -i references/reel/source.mp4 \
  -i references/reel/stems/htdemucs/source/no_vocals.wav \
  -i assets/voice/voice-track.wav \
  "${EXTRA[@]}" \
  -filter_complex "[0:v]delogo=x=196:y=226:w=888:h=134:enable='gte(t,465.30)',ass=assets/captions.ass,ass=assets/endcard.ass[v];\
[2:a]aresample=44100,volume=2.2dB,asplit=2[vo][sc];\
[1:a][sc]sidechaincompress=threshold=0.03:ratio=3:attack=20:release=300[bg];\
[bg][vo]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset medium -crf 19 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart "$OUT"
