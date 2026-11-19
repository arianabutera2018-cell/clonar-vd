# Live Clipper

Grava uma live, detecta momentos com potencial viral e gera clipes verticais (9:16) legendados.

## Como funciona

1. **Gravação**: `streamlink` (Twitch/Kick, pulando anúncios) ou `yt-dlp` (outros sites) grava em blocos de 10 s.
2. **Detecção** (a cada bloco):
   - salto de volume em relação aos últimos 10 min (grito, explosão, música alta);
   - fala transcrita com Whisper: reações em PT-BR ("meu deus", "não acredito", "caralho", "clipa"...), repetição ("não não não") e fala acelerada;
   - chat (Twitch e Kick, lido por HTTP): pico de mensagens em relação ao normal e reações (KKKK, CLIPA, ????, KEKW, POG, MDS...).
3. **Clipe**: quando a nota passa do limite, junta 30 s antes + 20 s depois e gera:
   - `original.mp4` (horizontal);
   - `vertical_legendado.mp4` (1080x1920, fundo desfocado, legenda palavra por palavra);
   - `capa.jpg`, `fala.txt`, `meta.json`.
4. **Relatório** em `RELATORIO.md`: chance ALTA / MÉDIA / INCERTA.
5. **Revisão do Claude**: `revisar.py` monta uma folha com 6 quadros de cada clipe. O Claude olha e grava o veredito (ALTA, MÉDIA, INCERTA ou DESCARTAR).

## Uso

```bash
pip install -r requirements.txt          # ffmpeg precisa estar instalado
python3 clipper.py https://www.twitch.tv/CANAL --out live_out --threshold 5
python3 revisar.py live_out              # lista clipes não revisados e gera folhas
python3 revisar.py live_out 3 ALTA "comentário"
```

`--threshold`: menor = mais clipes. 5 é o padrão; use 3–4 para lives calmas e 6–7 se vier clipe demais.

## Limitações

- Testado com sucesso em **Twitch** e **Kick** (18/11/2026).
- Cada clipe sai em 16:9 (original.mp4, cópia da live) e em 9:16 câmera-em-cima (vertical_9x16.mp4: 1080x1920, H.264, 30 fps). Ajuste --cam se a facecam do streamer estiver em outro lugar.
- O **YouTube** bloqueia downloads vindos de servidores (pede login). Funciona com Twitch e Kick.
- Chat da Kick: a API devolve só as últimas ~25 mensagens; em chats muito rápidos o pico aparece, mas o número exato fica abaixo do real.
- Em lives com muitos momentos seguidos, a análise pode atrasar alguns minutos.
