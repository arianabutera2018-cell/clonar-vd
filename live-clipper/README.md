# Live Clipper

Grava uma live, detecta momentos com potencial viral e gera clipes verticais 9:16 (câmera do streamer em cima, jogo embaixo) prontos pra Reels/TikTok/Shorts.

## Como funciona

1. **Gravação**: `streamlink` (Twitch/Kick, pulando anúncios) ou `yt-dlp` (outros sites) grava em blocos de 10 s.
2. **Detecção** (a cada bloco):
   - salto de volume em relação aos últimos 10 min (grito, explosão, música alta);
   - fala transcrita com Whisper: reações em PT-BR ("meu deus", "não acredito", "caralho", "clipa"...), repetição ("não não não") e fala acelerada;
   - chat (Twitch e Kick, lido por HTTP): pico de mensagens em relação ao normal e reações (KKKK, CLIPA, ????, KEKW, POG, MDS...).
3. **Clipe**: quando a nota passa do limite, junta 30 s antes + 20 s depois e gera:
   - `vertical_9x16.mp4` — **o que se entrega**: 1080x1920, H.264, 30 fps, câmera em cima e centro do jogo embaixo, sem legenda;
   - `original.mp4` (16:9, cópia exata da live; só matéria-prima, não se entrega);
   - `capa.jpg`, `fala.txt`, `meta.json`.
4. **Relatório** em `RELATORIO.md`: chance ALTA / MÉDIA / INCERTA.
5. **Revisão do Claude**: `revisar.py` monta uma folha com 6 quadros de cada clipe. O Claude olha e grava o veredito (ALTA, MÉDIA, INCERTA ou DESCARTAR).

## Uso

```bash
pip install -r requirements.txt          # ffmpeg precisa estar instalado
python3 clipper.py https://www.twitch.tv/CANAL --out live_out --threshold 5
python3 revisar.py live_out              # lista clipes não revisados e gera folhas
python3 revisar.py live_out 3 ALTA "comentário"
python3 revisar.py live_out 3 vertical           # (re)gera o 9:16 câmera em cima
python3 revisar.py live_out 3 vertical cheia     # 9:16 de cena sem gameplay
```

`--threshold`: menor = mais clipes. 5 é o padrão; use 3–4 para lives calmas e 6–7 se vier clipe demais.

## Limitações

- Testado com sucesso em **Twitch** e **Kick** (18/11/2026).
- **Entrega: só 9:16** (`vertical_9x16.mp4`), nunca 16:9. Facecam padrão do Coringa: `--cam 480:270:0:405`; ajuste se o streamer usar outra posição. Em cenas fora do jogo (câmera em tela cheia) use `python3 revisar.py live_out N vertical cheia` (recorte central).
- Depois de estender/refazer um clipe, rode `python3 revisar.py live_out N vertical` de novo.
- O **YouTube** bloqueia downloads vindos de servidores (pede login). Funciona com Twitch e Kick.
- Chat da Kick: a API devolve só as últimas ~25 mensagens; em chats muito rápidos o pico aparece, mas o número exato fica abaixo do real.
- Em lives com muitos momentos seguidos, a análise pode atrasar alguns minutos.
