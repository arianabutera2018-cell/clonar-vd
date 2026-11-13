# Progress

## Entregue
- `exports/clone-gta6-news-coringa.mp4` (470,7 s, 1280×720, 30 fps) — fora do git (grande).
  Recriar: `tools/render.sh exports/clone-gta6-news-coringa.mp4`.

## Como foi feito
1. Reel baixado (`references/reel/source.mp4`), transcrito com WhisperX local (medium, pt).
2. Roteiro reescrito frase a frase (`SCRIPT.md`, `script/new-lines.txt`), mantendo as palavras que
   aparecem gravadas na imagem (hábitos, acabou, arma escondida, mais perigoso, cada porta...).
3. Voz: ElevenLabs, voz "Jonas" (wTABSOIKENuRDeLiHYDF), eleven_flash_v2_5, fluxo eOTvTmu05SV6P5cPYtXQ.
   part1 (2.066 cr), part2 (1.370 cr), part3 regravação de 10 frases (353 cr) + transcrição local grátis.
4. `tools/map_lines.py` → tempos de cada frase; `tools/build_voice.py` encaixa cada frase no início
   da frase original (deriva máx. 0,41 s; até 25% de aceleração em 21 frases).
5. Música/efeitos originais sem a voz: Demucs htdemucs (`references/reel/stems/.../no_vocals.wav`),
   com ducking sob a nova voz e loudnorm -14 LUFS.
6. Legenda palavra a palavra (`tools/build_captions.py` → `assets/captions.ass`): caixa creme, texto
   escuro em Inter Display Black, palavra falada em rosa; some no cartão final.
7. Cartão final: "JACARÉ EXPLICA" apagado (delogo) e substituído por "NEWS CORINGA" (`assets/endcard.ass`)
   com brilho rosa e entrada em zoom igual ao original. Narração: "Se inscreve no News Coringa".

## Limitações conhecidas
- Pastilhas e cartões gravados no vídeo original continuam com o texto original (o sentido bate com a fala).
- Algumas frases ficaram até 25% mais rápidas para caber no tempo da cena original.
- Ambiente de nuvem `clonar-vd` tem Instagram/Hugging Face/ElevenLabs CDN liberados.
