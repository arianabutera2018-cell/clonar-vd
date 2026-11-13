# Progress — shorts GTA VI

Entregues (exports/, fora do git): 01-ps5, 02-policia, 03-assaltos, 04-vicecity (1080×1920, 27–33 s).
- 01 e 03: narração Jonas (ElevenLabs Flash, 188 + 189 créditos) + legenda palavra a palavra.
- 02 e 04: só gameplay oficial com som original.
- 05-corridas: CANCELADO a pedido da usuária (ElevenLabs gratuito ocupado). Plano pronto em
  plans/05-corridas.json e roteiro em scripts/narration.json — basta gerar a voz e rodar
  `tools/narrated.py plans/05-corridas.json && tools/short.py specs/05-corridas.json`.

Fonte única: Rockstar "An Extended Look" (sources/extended-look-1080p.mp4).
Renderizar de novo: `python3 tools/short.py specs/<nome>.json` (a partir de shorts/).
