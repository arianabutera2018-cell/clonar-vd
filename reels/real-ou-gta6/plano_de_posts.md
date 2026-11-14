# Série "Real ou GTA 6?" — contagem até o lançamento (19/11)

Melhor horário para postar (Brasil): entre 18h e 21h.
Música: escolha um áudio em alta no próprio Instagram na hora de postar.

| Dia | Arquivo | Cena real (Mixkit) | Cena do GTA 6 (Rockstar) |
|---|---|---|---|
| Sáb 15/11 | ep1_por_do_sol.mp4 | palmeiras no pôr do sol | Trailer 2, skyline com palmeiras |
| Dom 16/11 | ep2_cidade_de_dia.mp4 | skyline de Miami de dia | Trailer 2, rodovia com prédios |
| Seg 17/11 | ep3_por_do_sol_no_mar.mp4 | pôr do sol no mar com barcos | Trailer 2, pôr do sol visto do píer |
| Ter 18/11 | ep4_cidade_a_noite.mp4 | skyline de Miami à noite | Trailer de lançamento, cidade à noite vista de cima |

## Legendas

**EP1 (15/11)**
Real ou GTA 6? 🌴 Responde nos comentários ANTES de ver o final 👇
Faltam 4 dias pro lançamento!
Cena do jogo: Trailer 2 oficial da Rockstar Games.
#gta6 #gtavi #gta #vicecity #rockstargames #ps5 #gamer

**EP2 (16/11)**
Essa ficou difícil… real ou GTA 6? 🏙️ Comenta seu palpite 👇
Faltam 3 dias!
Cena do jogo: Trailer 2 oficial da Rockstar Games.
#gta6 #gtavi #gta #vicecity #rockstargames #ps5 #gamer

**EP3 (17/11)**
Pôr do sol em Miami ou em Vice City? 🌅 Quem acertar ganha meu respeito 👇
Faltam 2 dias!
Cena do jogo: Trailer 2 oficial da Rockstar Games.
#gta6 #gtavi #gta #vicecity #rockstargames #ps5 #gamer

**EP4 (18/11)**
É AMANHÃ! 🔥 Última rodada: real ou GTA 6? 🌃
Ativa o sininho pra ver as primeiras gameplays aqui amanhã.
Cena do jogo: Trailer de lançamento oficial da Rockstar Games.
#gta6 #gtavi #gta #vicecity #rockstargames #ps5 #gamer

## Dicas
- Responda os comentários na primeira hora: isso aumenta o alcance.
- Fixe um comentário seu com a pergunta: "Quantas você acertou? 1, 2, 3 ou 4?".
- Repostar nos Stories com a enquete "Real / GTA 6" ajuda a gerar interação.

## Como os vídeos foram gerados (versão 2, ~15 s cada)
Fontes: Trailer 2 (`x.com/RockstarGames/status/1920181314092765494`) e Trailer de lançamento
(`x.com/RockstarGames/status/2110717537964953810`), baixados com `yt-dlp`; cenas reais do Mixkit (IDs 24555, 12027, 24550, 12028, versão 720p).

```bash
export A=5.5 R=5
SLOW=1.75 PRE_GTA=crop=1920:864:0:108 TAG="FALTAM 4 DIAS" ./make_reel.sh 24555-720.mp4 2   trailer2.mp4 152.7  ep1_por_do_sol.mp4
SLOW=1.5  PRE_GTA=crop=1920:864:0:108 TAG="FALTAM 3 DIAS" ./make_reel.sh 12027-720.mp4 3   trailer2.mp4 34.55  ep2_cidade_de_dia.mp4
SLOW=2.2  PRE_GTA="crop=1920:864:0:108,scale=1280:-2" TAG="FALTAM 2 DIAS" ./make_reel.sh 24550-720.mp4 1.5 trailer2.mp4 81.55 ep3_por_do_sol_no_mar.mp4
SLOW=7.8  PRE_GTA="crop=3840:1920:0:120,scale=1280:-2" TAG="É AMANHÃ" ./make_reel.sh 12028-720.mp4 2 lancamento.mp4 17.5 ep4_cidade_a_noite.mp4
```
