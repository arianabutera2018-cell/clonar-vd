# Live Clipper

Grava uma live, detecta momentos com potencial viral e gera clipes verticais (9:16) legendados.

## Como funciona

1. **Gravação**: `streamlink` (Twitch/Kick, pulando anúncios) ou `yt-dlp` (outros sites) grava em blocos de 10 s.
2. **Detecção** (a cada bloco):
   - salto de volume em relação aos últimos 10 min (grito, explosão, música alta);
   - fala transcrita com Whisper: reações em PT-BR ("meu deus", "não acredito", "caralho", "clipa"...), repetição ("não não não") e fala acelerada.
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
- O **YouTube** bloqueia downloads vindos de servidores (pede login). Funciona com Twitch e Kick.
- O **chat** não é lido: o ambiente na nuvem não permite WebSocket.
- Em lives com muitos momentos seguidos, a análise pode atrasar alguns minutos.
