#!/usr/bin/env bash
# Reel "Real ou GTA 6?" — 1080x1920, ~13s.
# Uso: [A=4.5 R=4 PRE_REAL=filtro PRE_GTA=filtro] ./make_reel.sh <real.mp4> <inicio_real_s> <gta.mp4> <inicio_gta_s> <saida.mp4>
#   PRE_*: filtro ffmpeg aplicado antes do corte 9:16 (ex.: PRE_GTA=crop=1920:864:0:108 tira as faixas pretas do trailer)
# Estrutura:
#   0–4.5s   cena 1 (real) em tela cheia  -> "REAL OU GTA 6?"
#   4.5–9s   cena 2 (GTA 6) em tela cheia -> "E ESSA?"
#   9–13s    revelação: as duas empilhadas com os rótulos REAL / GTA 6
set -euo pipefail
REAL=$1; RS=$2; GTA=$3; GS=$4; OUT=$5
FONT=/usr/share/fonts/opentype/inter/InterDisplay-Black.otf
A=${A:-4.5}; R=${R:-4}

# corta para 9:16 em tela cheia, e para 1080x960 (metade) na revelação
full='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30'
half='scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,setsar=1,fps=30'
box="fontfile=$FONT:fontcolor=white:borderw=0:box=1:boxcolor=black@0.75:boxborderw=28"

ffmpeg -hide_banner -loglevel error -y \
  -ss "$RS" -t "$A" -i "$REAL" \
  -ss "$GS" -t "$A" -i "$GTA" \
  -ss "$(echo "$RS+$A-$R" | bc)" -t "$R" -i "$REAL" \
  -ss "$(echo "$GS+$A-$R" | bc)" -t "$R" -i "$GTA" \
  -filter_complex "
  [0:v]${PRE_REAL:+$PRE_REAL,}$full,drawtext=$box:text='REAL OU GTA 6?':fontsize=96:x=(w-tw)/2:y=260,
        drawtext=$box:text='responde antes do final':fontsize=48:x=(w-tw)/2:y=430,
        drawtext=fontfile=$FONT:fontcolor=white:fontsize=72:borderw=6:bordercolor=black:text='1/2':x=(w-tw)/2:y=h-360[v1];
  [1:v]${PRE_GTA:+$PRE_GTA,}$full,drawtext=$box:text='E ESSA?':fontsize=110:x=(w-tw)/2:y=260,
        drawtext=fontfile=$FONT:fontcolor=white:fontsize=72:borderw=6:bordercolor=black:text='2/2':x=(w-tw)/2:y=h-360[v2];
  [2:v]${PRE_REAL:+$PRE_REAL,}$half,drawtext=fontfile=$FONT:text='REAL':fontsize=80:fontcolor=white:box=1:boxcolor=0x1e88e5:boxborderw=22:x=60:y=240[t];
  [3:v]${PRE_GTA:+$PRE_GTA,}$half,drawtext=fontfile=$FONT:text='GTA 6':fontsize=80:fontcolor=white:box=1:boxcolor=0xe91e63:boxborderw=22:x=60:y=130[b];
  [t][b]vstack,drawbox=x=0:y=954:w=1080:h=12:color=white:t=fill,
        drawtext=$box:text='ACERTOU? COMENTA':fontsize=64:x=(w-tw)/2:y=(h-th)/2,
        fade=t=in:st=0:d=0.25:color=white[v3];
  [v1][v2]xfade=transition=slideleft:duration=0.3:offset=$(echo "$A-0.3" | bc)[v12];
  [v12][v3]xfade=transition=fade:duration=0.3:offset=$(echo "2*$A-0.6" | bc),format=yuv420p[v]
  " -map "[v]" -an -c:v libx264 -preset medium -crf 20 -movflags +faststart -r 30 "$OUT"
echo "ok -> $OUT"
