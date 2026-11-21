# Estudo: IA de NPCs para jogos de mundo aberto

Estudo feito só com fontes públicas e legais: uma patente da Take-Two/Rockstar, entrevistas oficiais da Rockstar e capítulos do livro gratuito *Game AI Pro*. Nenhum material vazado foi usado.

O objetivo é entender **como** esses sistemas funcionam para você criar os seus. Não é para copiar o jogo de ninguém.

---

## Índice

1. [Visão geral: as camadas de um NPC de mundo aberto](#1-visão-geral)
2. [Trânsito e carros NPC](#2-trânsito-e-carros-npc) (patente da Rockstar e Driver San Francisco)
3. [Pedestres e rotina diária](#3-pedestres-e-rotina-diária)
4. [Interações entre NPCs (cenas ambientes)](#4-interações-entre-npcs)
5. [Interação jogador ↔ NPC](#5-interação-jogador--npc) (o que a Rockstar disse sobre RDR2 e GTA 6)
6. [Percepção: visão, audição e consciência](#6-percepção)
7. [Polícia e busca pelo jogador](#7-polícia-e-busca)
8. [Combate: cobertura, posição e alvo](#8-combate) (Mafia III)
9. [Multidões](#9-multidões)
10. [Nível de detalhe da IA (LOD)](#10-nível-de-detalhe-da-ia)
11. [Utility AI: como dar "nota" a decisões](#11-utility-ai)
12. [Plano sugerido para o seu jogo](#12-plano-sugerido)
13. [O que não consegui acessar](#13-limitações-deste-estudo)
14. [Fontes](#14-fontes)

---

## 1. Visão geral

Nenhum desses jogos usa uma única "IA". Todos têm **camadas** separadas, cada uma com uma função bem definida:

```
┌──────────────────────────────────────────────────────────┐
│  DECISÃO        Behavior Tree / Máquina de estados /     │
│                 Rotina diária / Utility AI               │
├──────────────────────────────────────────────────────────┤
│  CONHECIMENTO   Percepção (visão, audição), memória,     │
│                 consciência (idle → suspeito → combate)  │
├──────────────────────────────────────────────────────────┤
│  CONSULTAS      Seleção de posição, de alvo, de rota,    │
│                 smart objects ("o banco serve p/ sentar")│
├──────────────────────────────────────────────────────────┤
│  MOVIMENTO      Pathfinding (A*), navmesh, desvio local, │
│                 física do carro                          │
├──────────────────────────────────────────────────────────┤
│  ORÇAMENTO      LOD da IA: quem merece processamento     │
│                 caro agora?                              │
└──────────────────────────────────────────────────────────┘
```

O capítulo do Mafia III resume a ideia principal:

> "Não importa qual sistema de decisão você use: quanto melhor a informação sobre o mundo que você entrega a ele, melhores decisões ele toma."

Ou seja, o behavior tree é só a "cola". A inteligência aparente vem dos sistemas de apoio (percepção, cobertura, seleção de posição).

**Dados em vez de código.** Mafia III tinha 18 arquétipos base de inimigo e 120 variações, todos em arquivos de configuração com herança. Os designers ajustavam tudo sem precisar de programador.

---

## 2. Trânsito e carros NPC

### 2.1 Patente da Take-Two/Rockstar (US 11.071.916 B2)

**Título:** *System and method for virtual navigation in a gaming environment*. Depositada em 2019/2020 e concedida em julho de 2021. Os inventores são David Hynd e Simon Parr, da área de IA e gameplay da Rockstar. A patente **não cita nenhum jogo**, então não dá para afirmar que isso está no GTA 6.

> ⚠️ **Atenção:** o método descrito nas reivindicações (claims) é **protegido**. Pode estudar e se inspirar nos conceitos gerais (que são técnicas conhecidas, como grafo hierárquico e A*), mas não implemente o método reivindicado exatamente como descrito em um jogo comercial sem falar com um advogado. As ideias abaixo também existem em várias outras fontes (veja o Driver San Francisco logo em seguida).

**Como funciona:**

**a) Grafo de ruas de baixo nível.** As ruas são cadeias de **nós** ligados por **links**.
- Os nós guardam: velocidade, tipo de via (rodovia, residencial, entrada particular), veículos permitidos e limitações (túnel, teto baixo).
- Os links guardam: largura, inclinação lateral, comprimento e número de faixas.
- Uma **bifurcação** é um nó ligado a mais de dois outros. Um **cruzamento** é uma bifurcação com lógica especial: semáforo, faixa de parada, tempo de cada fase e regras de faixa.
- O mundo é dividido em **regiões**. Cada nó tem um endereço no formato (região, índice).
- **Tags** restringem quem pode usar cada via: "desligado", "rio", "sem carroças", "uso privado" etc.
- **Ilhas:** cada nó recebe o número do "componente conectado" a que pertence. Se a origem e o destino estão em ilhas diferentes, a busca falha na hora, sem gastar processamento.

**b) Grafo "grosso" (coarse graph).** Criado no tempo de build:
1. Pega só as bifurcações.
2. Para cada bifurcação, segue a rua até a próxima bifurcação e cria **um único link** com a distância somada.
3. Uma rua reta sem cruzamentos vira **um link só**.
4. Guarda uma tabela que liga cada nó grosso ao nó original.

**c) Planejamento de rota:**
1. Origem e destino são colocados em dois **nós "dummy"** temporários, ligados aos nós grossos mais próximos.
2. Roda A* (ou Dijkstra etc.) **no grafo grosso**, que é muito menor.
3. Expande o caminho grosso de volta para os nós detalhados.
4. O carro segue **splines** pelos nós e lê, nos nós à frente, a velocidade-alvo e o quão fechada é a curva.
5. Ele **replaneja** a cada N nós percorridos.
6. Sem destino, entra no **modo "passear"** e escolhe as saídas nas bifurcações por regras.
7. Cada NPC guarda na memória **só os nós da própria rota**.

**d) "Personalidade" do carro e do motorista:**
- Cada carro tem aceleração, distância de frenagem, velocidade máxima e limite de curva. Esses valores vêm de **testes reais no motor de física**: acelerar do zero, fazer curvas de vários raios cada vez mais rápido até perder o controle.
- Os resultados viram **curvas de 3 parâmetros (a, b, c)** por carro, superfície e clima, ajustadas por mínimos quadrados.
- O motorista tem "habilidade" e "velocidade" própria.
- Exemplo dado na patente: **andar mais devagar em rua residencial**.

**e) Obstáculos.** A patente critica o desvio "de última hora" (ver o obstáculo na frente e só então desviar). A proposta é **colocar o bloqueio no próprio grafo**: uma rua fechada recebe a tag "desligado" e as rotas já evitam essa rua com antecedência.

**f) Spawn de carros por densidade:**
- Cada trecho de rua tem uma **densidade-alvo** (carros por distância). Avenidas principais têm densidade maior.
- Perto do jogador, levando em conta para onde ele olha, compara a densidade atual com a alvo e **cria carros para cobrir a diferença**.
- A contagem é feita **ao longo da rede de ruas**, não por raio em linha reta. Assim os carros de um viaduto não contam para a rua de baixo.
- Exemplo da patente: densidade 4 significa ~2 carros a ~10 m de distância. Cada carro "vale" 2 unidades; se sobra 2, cria mais 1 carro.

### 2.2 Driver San Francisco (Game AI Pro 3, cap. 17)

Esse capítulo é mais detalhado que a patente e é livre para estudo.

**Dois tipos de carro:**

| Tipo | Como funciona | Custo |
|---|---|---|
| **Trânsito civil** | Segue **splines em loop** pela cidade. As splines foram desenhadas para **nunca se cruzarem**, então os civis nunca batem entre si. | Baratíssimo |
| **"Active Life"** | Carros com objetivo (perseguir, fugir, correr). Usam o planejador completo. | Caro |

Um carro pode trocar de tipo a qualquer momento. Se o jogador sai de um carro civil, a IA procura a vaga livre mais próxima na spline e "rebaixa" o carro para civil de novo.

**Todo carro tem um "vehicle path":** a previsão de onde ele vai estar nos próximos segundos. É atualizado ~1 vez por segundo, anexando segmentos ao final. Até o carro do jogador tem um, calculado por física e extrapolação. **Isso permite que um carro preveja onde os outros vão estar.**

**Personalidade do motorista** (afeta todas as etapas do planejamento):
- chance de dirigir na contramão;
- chance de subir na calçada;
- velocidade preferida;
- preferência por rodovias, becos e estradas de terra;
- quanto evita bater nos outros.

**Rede de ruas:** cada rua é uma spline. Cada ponta da rua tem a lista de ruas conectadas e um **corte transversal**: número de faixas, largura e tipo (a favor do trânsito, contramão, calçada).

**Planejamento em 3 níveis:**

1. **Rota (A\*)** nas ruas.
   - O mapa foi dividido em 3 áreas ligadas por pontes, usando **A\* hierárquico**: primeiro acha a ponte, depois o resto.
   - O custo de cada rua depende da personalidade. Um civil faz uma rota mais longa para fugir da terra; um fugitivo **evita ruas com polícia**.
   - Para fuga, existe um gerador adaptativo de rota.
   - Na perseguição, a cada cruzamento a IA **prevê para onde o fugitivo vai virar**, usando a física simplificada para saber o que o carro dele consegue fazer.

2. **Caminho médio (mid-level).**
   - Uma grade de nós ~100 m à frente do carro, com **um nó por faixa** a cada poucos metros.
   - Gera todos os caminhos possíveis e dá um **custo** a cada um: seguir reto custa 1; trocar de faixa custa 2; passar perto de outro carro (na posição **prevista**) soma custo; contramão e calçada somam custo conforme a personalidade.
   - Fica com os **5 melhores**.
   - **Velocidade nas curvas:** de trás para frente, calcula a velocidade máxima em cada curva e "propaga" para trás com base na frenagem do carro. Assim o carro começa a frear **antes** da curva. Exemplo: 70 mph na reta, 30 mph na curva fechada, 50 mph no nó anterior.

3. **Otimizador de baixo nível.**
   - Monta um **campo de potencial**: um "terreno" onde o destino é um vale e os obstáculos são montanhas.
   - Esse campo tem duas partes: uma **estática** (paredes, calçadas, contramão, calculada com *fast marching*) e uma **dinâmica** (carros em movimento, consultada **por tempo**).
   - Simula o carro com uma **física 2D simplificada** (mesmo motor e mesmos pneus do carro real) e o mesmo código de "seguir caminho".
   - Dá uma nota ao trajeto: andar morro abaixo no campo + ficar perto da velocidade desejada + **penalidade enorme por colisão**.
   - Empurra o caminho na direção do gradiente e repete. **3–4 iterações bastam.** Faz isso para os 5 caminhos e escolhe o melhor.

**LOD:** carros longe usam só a rota; carros médios usam rota + caminho médio; carros perto e na câmera usam os 3 níveis. Carros longe **saem da física**: só são posicionados no ponto do caminho naquele instante.

**Assíncrono:** tudo roda em várias threads e ao longo de vários frames. Como o caminho já tem alguns segundos de "folga", o carro continua dirigindo enquanto espera o próximo cálculo.

### 2.3 Como aplicar no seu jogo

- **Para começar (simples e barato):** trânsito civil em splines/faixas que não se cruzam + semáforos que liberam ou bloqueiam trechos. A maior parte dos carros fica assim.
- **Carros "promovidos":** quando o jogador interage (bate, aponta arma, começa perseguição), o carro passa para uma IA cara com rota A\* e desvio.
- **Densidade por trecho de rua** para criar e remover carros perto do jogador, contando a distância pela rede de ruas.
- **Personalidade = pesos no custo da rota e do caminho.** É barato e dá muita variedade.

---

## 3. Pedestres e rotina diária

**Fonte:** *Breathing Life into Your Background Characters*, de David "Rez" Graham (Game AI Pro 1, cap. 36). Ele usou esse sistema em *The Sims Medieval*.

**Problemas comuns:**
- NPC que repete a mesma animação para sempre (o ferreiro que martela o jogo inteiro).
- NPC que anda para um ponto aleatório, para e repete.
- O extremo oposto: usar uma IA complexa demais em NPC de fundo.

**Regra de ouro:** NPC de fundo precisa ser **barato**. É melhor ter 30 NPCs simples do que 5 complexos, porque **quantidade** é o que dá a sensação de cidade.

**Sistema de agenda (schedule):**

```
Agenda ──► Entrada de agenda (fatia de tempo) ──► Ação ("vá até X e faça a animação Y")
```

- Uma **agenda** é uma máquina de estados hierárquica cujo estado de cima é escolhido **pelo horário**.
- Cada **entrada** escolhe a ação de um jeito que pode ser trocado: ação fixa, sorteio com pesos, ou pontuação por desejos.
- **Dono de objetos:** a ação diz "dormir em uma **cama**", não em uma cama específica. Cada NPC tem um mapa do tipo "cama → minha cama". A mesma agenda serve para mil NPCs, e cada um vai para a própria cama.
- **Templates com herança:** o "Guarda diurno" e o "Guarda noturno" usam os mesmos blocos com horários trocados.

```xml
<Schedule name="Trabalhador">
  <Entry name="Dormir" type="Simple" startTime="22">
    <Action type="sleep"/>
  </Entry>
  <Entry name="Trabalhar" type="WeightedRandom" startTime="8">
    <Action type="work_at_desk"   weight="3"/>  <!-- 75% -->
    <Action type="work_at_copier" weight="1"/>  <!-- 25% -->
  </Entry>
</Schedule>
```

**Dicas importantes:**
- **Não troque todos ao mesmo tempo.** Se todos vão ao bar às 18h00 em ponto, parece robótico. Sorteie o horário de troca com uma **distribuição normal** em torno do horário certo, e deixe o NPC **terminar a ação atual** antes de ir.
- **A IA principal pode passar por cima da agenda.** Se o jogador ataca o padeiro, ele foge ou reage; quando a ameaça passa, **volta para a rotina**.
- Entradas da agenda também podem mudar por **evento** (alarme, ataque), não só por horário.

---

## 4. Interações entre NPCs

**Fonte:** *Ambient Interactions*, de Hendrik Skubch (Game AI Pro 3, cap. 35), usado em **Final Fantasy XV**.

O problema: behavior trees descrevem bem **um** NPC, mas são ruins para cenas com **vários** NPCs (dois amigos conversando no banco, um vendedor atendendo um cliente).

**Smart objects → smart locations:**
- *Smart object* (ideia de The Sims): **o objeto sabe como ser usado**. A cadeira diz "dá para sentar em mim, e esta é a animação".
- *Smart location*: um objeto invisível que agrupa **vários** objetos (2 cadeiras + 1 mesa) e **controla** quem usa.

**Tipos de emissor:**
- **Notificação:** só avisa que o lugar existe.
- **Script:** vê quais NPCs estão perto, distribui **papéis** e inicia a cena. É o mais usado.
- **Spawn:** cria NPCs para cenas que precisam de 3 ou mais pessoas específicas, ou em lugares inacessíveis como varandas.
- **Jogador:** mostra um ícone de interação; o jogador entra na cena como mais um participante.

**Papéis** têm nome, quantidade mínima e máxima e flags como "pode entrar no meio da cena". Exemplo: `Idoso: 0..1`, `Turista: 0..2`. A cena funciona com qualquer combinação.

**Regras no estilo STRIPS** sobre um quadro compartilhado (*blackboard*):
- **Pré-condição:** quando a regra pode disparar.
- **Ação:** sentar, ir até, falar com…
- **Efeitos:** fatos que são adicionados ou removidos.
- **Efeitos adiados:** aplicados só quando a ação termina.

Exemplo do banco:

```
Regra 1 (sentar):
  ação: sentar(X)
  se:   assento(X) e não reservado(X, alguém)
  efeito imediato: reservado(X, eu)
  efeito ao terminar: sentado(eu), timer(eu, agora + 2..5 min)

Regra 2: se ninguém está falando → escolhe um sentado como "falante"
Regra 3 (falante): falar(X) com outro sentado; ao terminar, deixa de ser falante
Regra 4 (outros): ouvir(falante)   ← acenar com a cabeça etc.
Regra 5: se timer(eu) venceu → levantar e sair da cena
```

**Vantagens observadas:**
- Se não tem idoso, o turista **senta sozinho**.
- Se o banco está cheio, ele **passa reto**.
- Até a **loja** vira um "participante" que escreve no quadro o que o jogador comprou, e o lojista reage a isso.

**Para o seu jogo:** pontos de ônibus, bancos, food trucks, esquinas de conversa e brigas de rua podem ser *smart locations* com cenas de vários papéis. Os pedestres que passam perto entram na cena.

---

## 5. Interação jogador ↔ NPC

O que a Rockstar disse publicamente:

- **Rob Nelson** (co-chefe de estúdio e diretor de arte da Rockstar North), em entrevistas recentes citadas pela GamesRadar e pela Notebookcheck:
  - *"Embora tenhamos levado a interação com NPCs o mais longe que conseguimos em Red Dead Redemption 2, neste jogo [GTA 6] estamos levando muito mais longe."*
  - *"Esse sistema de interação com NPCs está voltando, evoluído, do Red Dead Redemption 2."*
  - No RDR1 e no GTA 5 as interações eram "muito simples"; o RDR2 foi o primeiro a ter um sistema mais completo.
- Segundo reportagem de Jason Schreier (Bloomberg), o protótipo da tecnologia de NPCs do RDR2 foi criado por **Mark Tennant** (VP de animação) por volta de 2014–2015.
- No GTA 6, segundo a cobertura: grupos de NPCs **se juntam e conversam**, e a reação deles depende de como se sentem quando você **escuta a conversa**. No trailer, NPCs perto de um crime **se afastam discretamente**.
- **Imran Sarwar** (diretor de design do RDR2, Official Xbox Magazine, 2018):
  - Os membros da gangue **sabem quando o Arthur está no acampamento e quando ele causou problemas** lá fora. Eles ganharam "memórias melhores" e convidam o jogador para conversar.
  - A ideia foi estendida ao mundo todo (lojista, xerife, cavaleiro passando). As opções dependem do **tipo de pessoa e da situação**, e dá para interagir **sem sacar a arma**.
- **Rob Nelson** (2018, sobre o RDR2):
  - Conversas no acampamento podem **virar missões** (um assalto a banco, por exemplo).
  - Dinheiro por vários caminhos: matar, ou **ameaçar** e pegar o dinheiro sem violência ("não é um sistema maniqueísta").
  - Animais **reagem à aproximação**: o cervo levanta a cabeça; se você nunca foi ameaça, ele continua pastando.

**Como transformar isso em sistema (minha proposta, não é da Rockstar):**

```
NPC
 ├─ arquétipo: lojista | policial | pedestre | gangue rival ...
 ├─ humor: calmo / nervoso / irritado / com medo   (muda com eventos)
 ├─ memória do jogador:
 │    reputação (-100..100), última interação, "viu o jogador cometer crime?"
 └─ opções de interação = f(arquétipo, humor, memória, contexto)
       ex.: Cumprimentar | Provocar | Acalmar | Ameaçar | Pedir informação
```

- Cada opção muda o humor e a memória. Uma provocação pode escalar para briga; acalmar pode encerrar a situação.
- A memória **decai com o tempo**, a não ser que o evento seja grave.
- Conversas podem **liberar missões e atividades**.
- Nada disso exige IA complexa: é uma máquina de estados simples com algumas variáveis. A sensação de "vivo" vem da **variedade de falas e animações**.

---

## 6. Percepção

**Fontes:** *Splinter Cell Blacklist*, de Martin Walsh (Game AI Pro 2, cap. 28), e Mafia III (Online Edition 2021, cap. 16).

### 6.1 Os 4 princípios (Splinter Cell)
1. **Justiça:** o jogador precisa sentir que foi justo ser visto.
2. **Consistência:** distâncias e tempos previsíveis, com **animações e falas variadas**.
3. **Feedback:** o jogador precisa entender **o que** o NPC percebeu e **por quê**.
4. **Inteligência:** não precisa ser genial, precisa ser **plausível**.

> "Só importa o que o **jogador acha** que o NPC consegue ver e ouvir."

### 6.2 Visão
- **Mafia III:** cone de visão + raycasts para **5 pontos** do corpo do jogador (cabeça, cotovelos e joelhos por padrão). Em cobertura, os pontos ficam mais próximos do peito para proteger melhor o jogador.
- **Splinter Cell:** raycasts para **8 ossos**. A quantidade de ossos visíveis necessária depende da postura.
- **Ver não é reconhecer.** Ao ver algo, o NPC começa a **reconhecer**. O tempo para reconhecer é o **produto** de várias curvas:
  - distância;
  - ângulo em relação ao olhar;
  - iluminação (do alvo e do NPC);
  - velocidade do alvo;
  - número de pontos visíveis.

  `tempo = f_distância × f_ângulo × f_luz × f_velocidade × f_pontos`

  Cada `f` é uma **curva linear por partes** editável pelos designers.
- **Formato "caixão":** um cone vai alargando com a distância, e longe isso fica irreal. O Splinter Cell usou uma forma que abre como um cone e depois **fecha**. Também há uma área de **visão periférica**.
- O tempo de detecção aparece como uma **barra na tela**, que é a janela que o jogador tem para sumir.
- Lição do Mafia III: deixar o jogador agachado "mais difícil de ver" **não parecia certo** ("um cara grande agachado no meio da rua não é mais difícil de notar"). Eles mantiveram só a mudança dos pontos de detecção, que ajuda a se esconder atrás de objetos.

### 6.3 Audição
- Os sons de IA são **separados do motor de áudio**. Cada evento tem raio e prioridade.
- **Tiro** coloca o NPC em combate na hora. **Passos** só contam se houver vários em pouco tempo.
- **Distância do som pelas portas:** o mundo é dividido em **áreas** ligadas por **pontos de passagem** (portas, janelas). A distância do som é a soma do caminho de porta em porta, não a linha reta. Assim o som não atravessa paredes.
- **Truque de justiça:** NPCs **fora da tela** e razoavelmente longe ouvem **metade** da distância. O diretor de criação parou de reclamar e o jogo ficou mais divertido.

### 6.4 Estados de consciência (Mafia III)

```
Idle ──► Reconhecimento ──► Investigação ──► Busca ──► Combate
  ▲                                            │
  └────────────── (desiste, volta à rotina) ───┘
```

Cada estado usa **sensores diferentes**. Um NPC tranquilo enxerga mais perto que um NPC em combate.

### 6.5 Truques de "parece inteligente"
- **Objetos alterados:** porta aberta ou luz apagada gera um evento com tempo de vida. O primeiro NPC que vê "pega" o evento e investiga: *"Eu deixei essa porta aberta?"*. Segundo o autor, foi o recurso com **melhor custo-benefício**, e até reviews comentaram.
- **Falas em 3 níveis:** primeiro as específicas (*"Ouvi passos"*), depois as genéricas (*"Ouvi alguém ali"*), depois as muito genéricas (*"Hein?"*). O jogador aprende a mecânica e nunca ouve a mesma frase marcante duas vezes.
- **Contexto muda o significado:** "ver um corpo" numa patrulha calma causa pânico; numa zona de guerra é ignorado. "Ver o jogador no telhado **de novo**, depois de ele matar 5 de lá" faz o NPC fugir em vez de atacar.
- **Conversa interrompida:** a conversa é um comportamento de **grupo**. Um barulho a pausa (*"Ouviu isso?" "Deve ser a TV… o que você dizia?"*); um segundo barulho gera investigação; depois retoma com uma fala de reentrada.
- **O NPC que sumiu:** se A ouvia B por 10 s e B fica 5 s em silêncio (porque morreu), A fica desconfiado e investiga. Barato e convincente.
- **Jogador em lugar inalcançável** (telhado): granada e depois recuo, **anunciando em diálogo** ("Ele tá lá em cima! Joga uma granada!"). Isso evita o exploit e o jogador entende o que está acontecendo.

---

## 7. Polícia e busca

**Fonte:** *Looking for Trouble*, de Rich Welsh (Game AI Pro 2, cap. 27).

**Dois tipos de busca:**

| | Cautelosa | Agressiva |
|---|---|---|
| Gatilho | Distração (garrafa, barulho) | Tiro, explosão, alvo que fugiu |
| Movimento | Anda, olha em volta | Corre, arma levantada |
| Fim | Depois de checar o 1º ponto | Depois de todos os pontos ou do tempo limite |

**Truque da "intuição":** depois de perder o alvo de vista, o NPC **continua sabendo onde ele está por 2–3 segundos**. É mais barato e mais natural do que extrapolar a velocidade. Halo, Crysis e Crackdown usam.

**Fase 1, busca estreita:** ir até a **última posição conhecida**.
- Na busca cautelosa, **só 1 NPC** vai. Isso permite ao jogador "puxar" inimigos um por um.
- Na agressiva, **2–3 no máximo** vão; os outros dão cobertura.

**Fase 2, busca ampla (coordenada):**
- Um **coordenador de busca** gera **pontos de busca**: lugares que esconderiam o jogador, como coberturas fora de vista da posição estimada e esquinas e becos no navmesh.
- Cada NPC pede um ponto ao coordenador, que marca o ponto como "em andamento".
- Enquanto anda, o NPC faz raycasts (a cada 1–2 s) para **todos os pontos que consegue ver** e os marca como "vistos". Os NPCs não repetem lugar.
- **Nota de cada ponto:** distância até a posição estimada + distância até o NPC + **um peso pequeno** para a posição **real** do jogador. Isso dá uma "intuição" sutil sem parecer trapaça.
- **Detecção de vãos:** raycasts laterais à frente do NPC detectam aberturas, e ele **olha para dentro** delas (de vez em quando vai até lá, vira o corpo ou só a cabeça).
- **Fim:** os NPCs **voltam à rotina cada um no seu tempo**. Se todos param juntos, parece uma mente coletiva.

**Para um sistema de "procurado":** os níveis de estrela podem definir quantos policiais participam, o raio de geração dos pontos de busca, o tempo limite da fase 2 e se a polícia usa carros. Perder a polícia = o coordenador esgotar os pontos ou o tempo sem ver o jogador.

---

## 8. Combate

**Fonte:** Mafia III (Online Edition 2021, cap. 16).

**Arquétipo → Tática → Blocos:**
- **Arquétipo:** aparência, sentidos, voz, armas, reações, animações e lista de táticas. Usa herança: o "triggerman" base joga molotov; uma variação joga granada.
- **Tática** = seleção de posição + seleção de alvo + estilo de movimento + ação na cobertura + ação em campo aberto + recarga.
  - Seleção de **posição** e de **alvo** usam **funções de pontuação** (utility).
  - O resto são **árvores de decisão** pequenas. O behavior tree só executa o que a árvore de decisão sugere, separando **o que** fazer de **como** fazer.

**Coberturas:**
- Geradas **automaticamente** no editor a partir da colisão do cenário, com ajuste manual.
- Cada slot tem 1 m de largura e guarda: posição, rotação e largura; pontos de onde dá para se inclinar e atirar; um **perfil de altura** (4 pontos num valor de 64 bits, para capô e teto de carro); **direções de proteção** (círculo dividido em 32, num valor de 32 bits); e os vizinhos.
- **Carros, caixas e caçambas** viram cobertura **quando param**. Quando se movem, a cobertura some. Coberturas bloqueadas encolhem ou se fundem com as vizinhas, e é preciso "colar no chão" (o carro está na rua, a cobertura na calçada).

**Seleção de posição:**
- `nota = valorBase × Π funções`. Usa **produto** para que qualquer fator possa **zerar** a nota.
- A busca é limitada a um raio que depende da tática (em volta de si, do jogador ou dos inimigos). Exemplo: todas as coberturas + 120 pontos abertos num raio de 15 m, até 300 candidatos.
- **Filtro em etapas:** primeiro as funções baratas; só os **50 melhores** passam por raycast e só os **20 melhores** por pathfinding.
- **Mundo dinâmico:** busca completa a cada ~12 s, mas **reavalia só a posição escolhida 5×/s** com funções mais leves. Se a nota cair 50%, o NPC para e atira de onde está, o que parece mais decidido do que mudar de ideia no meio do caminho.
- **Depuração:** esferas coloridas por candidato (vermelho = inacessível, cinza = descartado, verde = melhor) com o texto de cada função.
- **Menos é mais:** muitas vezes o problema era resolvido **removendo** funções de pontuação.

**Tiro "justo":** o behavior tree decide **quando** e **em quem** atirar. O código do frame decide se o tiro sai, passando por validações:
- **estilo de tiro:** o sniper espera pelo menos 2 s mirando antes de atirar, para dar chance de desviar;
- **não atirar se tiver aliado na frente**;
- **proteção do jogador** em momentos específicos.

**Percepção dos civis** no mesmo sistema: o jogador emite um evento "Player"; uma briga emite "melee"; corpos e armas na mão também são eventos. **Pedestres reagem ao ver arma na mão do jogador.**

---

## 9. Multidões

**Fonte:** *Advanced Techniques for Robust, Efficient Crowds*, de Graham Pentheny (Game AI Pro 2, cap. 17).

**Problema:** A\* + desvio local funciona com pouca gente. Com muita gente indo para o mesmo lugar, todos se espremem na mesma porta e ignoram a outra porta livre.

**Mapa de congestionamento:**
1. Para cada célula da grade, guarda a **densidade** de agentes e a **velocidade média** da multidão.
2. No A\*, o custo de cada passo ganha uma **penalidade de congestionamento**:

```
penalidade(direçãoIdeal, velocidadeMultidão, densidade):
    c = dot(direçãoIdeal, velocidadeMultidão) / |direçãoIdeal|²
    se c >= 1: retorna 0          // a multidão anda na mesma direção e rápido
    retorna (1 - c) * densidade   // contra o fluxo ou parado = mais caro
```

- Andar **junto** com o fluxo não é penalizado. Andar **contra** o fluxo ou passar por um bolo parado é.
- Para muitos agentes indo ao mesmo destino, usar **flow field** (um mapa de direções para todos, calculado uma vez com Dijkstra ou Theta\*).
- Melhoria sugerida: **histerese**, para o agente não ficar trocando de caminho toda hora.
- O desvio local (RVO/ORCA) continua necessário para os esbarrões de perto.

**Uso no seu jogo:** fuga em pânico após um tiro (todos para longe da ameaça e para as saídas menos lotadas), saída de estádio e evento de rua.

---

## 10. Nível de detalhe da IA

**Fonte:** *The LOD Trader*, de Ben Sunshine-Hill (Game AI Pro 1, cap. 14), e o Driver San Francisco.

**Ideia básica (todo mundo faz):** NPC longe atualiza menos, usa movimento mais simples ou sai da física; NPC muito longe é removido.

**Ideia avançada (LOD Trader):** em vez de usar só a distância, estima **a chance de o jogador perceber** a falha. Existem três tipos de falha:

| Falha | Exemplo | Depende de |
|---|---|---|
| **Estado irreal** | Correndo parado contra a parede | Visibilidade × atenção |
| **Descontinuidade** | NPC sumiu atrás da esquina, ou ficou congelado enquanto você saiu | Memória × chance de voltar |
| **Comportamento irreal no longo prazo** | NPC andando a esmo em vez de ter objetivo | Atenção × memória × tempo observado |

- **Visibilidade** = área na tela ÷ tamanho de "saturação" (um personagem a 4 m), limitado a 1.
- **Atenção** = média móvel exponencial da visibilidade (70%) + o quanto o jogador **mantém o NPC no centro da câmera** (30%), dividida pela "carga" total de atenção.
- **Memória:** sobe rápido quando o jogador presta atenção (~5 s) e cai devagar.
- Cada frame, um "corretor" **troca** níveis de detalhe entre NPCs (sobe o de quem importa, desce o de quem não importa) **sem passar do orçamento de CPU**.

**Versão prática para começar:**

```
importância = visível_na_tela * (1 / distância)
            + bônus se o jogador está mirando/seguindo
            + bônus se é perseguidor, alvo de missão, ou interagiu recentemente
```

Ordene os NPCs por importância e dê a IA cara só aos N primeiros, conforme o orçamento.

**Lembrete do LOD Trader:** NPCs com quem o jogador interagiu **não podem simplesmente sumir**. O jogador lembra deles (descontinuidade).

---

## 11. Utility AI

**Fonte:** *An Introduction to Utility Theory*, de David "Rez" Graham (Game AI Pro 1, cap. 9), e o uso no Mafia III.

- Cada ação possível recebe uma **nota de 0 a 1**, e a de maior nota vence (ou há um sorteio entre as melhores).
- A nota vem de **fatores normalizados** (0–1) passados por **curvas**:
  - **Linear:** `x`
  - **Quadrática:** `x^k` (devagar no começo, urgente no fim). Com `k` entre 0 e 1, a curva se inverte.
  - **Logística (S):** muda bruscamente no meio, suave nas pontas.
- Combinar fatores por **média** é estável; por **produto** (como no Mafia III), qualquer fator pode vetar a ação.
- **Inércia:** um bônus para a ação atual evita que o NPC fique trocando de decisão.

Exemplo para um pedestre depois de ouvir um tiro:

```
fugir     = curva_S(perigo) × (1 - coragem)
filmar    = curva_quad(curiosidade) × (1 - perigo)  × tem_celular
ligar_190 = cidadão_responsável × perigo_médio
revidar   = coragem × tem_arma × curva_S(perigo)
```

---

## 12. Plano sugerido

Ordem para construir, do mais barato para o mais caro:

1. **Base de dados de arquétipos** (JSON/ScriptableObject) com herança: pedestre, motorista, lojista, policial, gangue.
2. **Pedestres com agenda** (seção 3) + **dono de objetos** + horário de troca sorteado.
3. **Sistema de eventos/estímulos** (tiro, batida, arma visível, sirene, corpo) com raio e tipo. Todo mundo escuta o mesmo sistema.
4. **Reações por Utility AI** (seção 11): fugir, filmar, ligar para a polícia, revidar, ignorar.
5. **Trânsito civil em faixas/splines** + semáforos + **densidade por trecho** (seção 2.3).
6. **Smart locations** para cenas ambientes de 2–3 NPCs (seção 4).
7. **Polícia:** estados de consciência + busca em 2 fases com coordenador (seções 6–7).
8. **Interação jogador ↔ NPC** com humor e memória (seção 5).
9. **Combate** com coberturas automáticas e seleção de posição por nota (seção 8).
10. **LOD da IA** com orçamento (seção 10). Pode começar simples, mas planeje desde cedo.

**Ferramentas de depuração desde o início:** desenhar na tela os cones de visão, os estados, as notas e as rotas. Todos os autores reforçam isso.

---

## 13. Limitações deste estudo

- **Palestras da GDC da Rockstar** sobre os cavalos (*Making the Believable Horses of Red Dead Redemption II*, Tobias Kleanthous) e a vida selvagem (*Breathing Life into the Wild West*, Alex O'Dwyer): os vídeos e slides completos são **pagos** no GDC Vault, então só consegui os resumos oficiais, sem detalhes técnicos. O artigo da PC Gamer sobre os cavalos não carregou.
- **Reivindicações da patente:** li a descrição técnica; as reivindicações (claims) estão resumidas, não citadas literalmente. A patente de continuação (US 11.684.855) não foi lida.
- Alguns artigos (GamesRadar, Medium) bloquearam a leitura direta. As falas do Rob Nelson vêm de reportagens que citam uma entrevista à IGN.
- **Nada aqui confirma como o GTA 6 funciona por dentro.** A patente não cita o jogo, e as entrevistas falam em termos gerais.

---

## 14. Fontes

**Patente**
- [US 11.071.916 B2 – Google Patents](https://patents.google.com/patent/US11071916)
- [US 11.684.855 (continuação) – USPTO](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11684855)
- [GameSpot sobre a patente](https://www.gamespot.com/articles/rockstar-npc-tech-patent-has-people-talking-about-gta-6/1100-6486479/)
- [VGC sobre a patente](https://www.videogameschronicle.com/news/gta6-npc-improvements-patent/)

**Rockstar – entrevistas e GDC**
- [GamesRadar – Rob Nelson: GTA 6 leva a interação com NPCs "muito mais longe"](https://www.gamesradar.com/games/grand-theft-auto/rockstar-lead-says-gta-6-takes-npc-interactions-much-further-than-red-dead-redemption-2-and-its-system-is-returning-and-evolved/)
- [GamesRadar – sistema do RDR2 base dos NPCs do GTA 6](https://www.gamesradar.com/games/grand-theft-auto/a-fundamental-red-dead-redemption-2-system-provided-the-basis-for-how-gta-6s-npcs-work-but-it-was-nearly-cut-because-of-an-ambitious-rockstar-studio-head/)
- [Notebookcheck – detalhes do GTA 6](https://www.notebookcheck.net/GTA-6-details-Red-Dead-Redemption-2-systems-taken-to-the-next-level-physical-intimacy-and-more.1418407.0.html)
- [Wccftech – Imran Sarwar sobre a interação com NPCs no RDR2 (2018)](https://wccftech.com/rockstar-explains-npc-interaction-rdr2/)
- [Wccftech – Rob Nelson sobre os NPCs do RDR2 (2018)](https://wccftech.com/rockstar-talks-about-rdr2-evolved-npcs/amp/)
- [GDC Vault – Making the Believable Horses of RDR2](https://gdcvault.com/play/1027113/contactUs)
- [GDC – Breathing Life into the Wild West](https://gdconf.com/news/learn-how-rockstar-breathed-life-wildlife-red-dead-redemption-2-gdc)

**Game AI Pro (gratuito em [gameaipro.com](http://www.gameaipro.com/))**
- [Open-world Enemy AI in Mafia III](http://www.gameaipro.com/GameAIProOnlineEdition2021/GameAIProOnlineEdition2021_Chapter16_Open-world_Enemy_AI_in_Mafia_III.pdf)
- [Fast Cars, Big City: The AI of Driver San Francisco](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter17_The_AI_of_Driver_San_Francisco.pdf)
- [Breathing Life into Your Background Characters](http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter36_Breathing_Life_into_Your_Background_Characters.pdf)
- [Ambient Interactions (Final Fantasy XV)](http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter35_Ambient_Interactions_Improving_Believability_by_Leveraging_Rule-Based_AI.pdf)
- [Modeling Perception and Awareness in Splinter Cell Blacklist](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter28_Modeling_Perception_and_Awareness_in_Tom_Clancy's_Splinter_Cell_Blacklist.pdf)
- [Looking for Trouble: Making NPCs Search Realistically](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter27_Looking_for_Trouble_Making_NPCs_Search_Realistically.pdf)
- [Advanced Techniques for Robust, Efficient Crowds](http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter17_Advanced_Techniques_for_Robust_Efficient_Crowds.pdf)
- [Phenomenal AI Level-of-Detail Control with the LOD Trader](http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter14_Phenomenal_AI_Level-of-Detail_Control_with_the_LOD_Trader.pdf)
- [An Introduction to Utility Theory](http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter09_An_Introduction_to_Utility_Theory.pdf)

**Outros capítulos do Game AI Pro que valem a leitura depois:**
- *Smart Zones to Create the Ambience of Life* (GAIP2 cap. 11)
- *Human Enemy AI in The Last of Us* (GAIP2 cap. 34)
- *Behavior Selection Algorithms: An Overview* (GAIP1 cap. 4)
- *The Behavior Tree Starter Kit* (GAIP1 cap. 6)
- *Tactical Position Selection* (GAIP1 cap. 26)
- *Crytek's Target Tracks Perception System* (GAIP1 cap. 31)
- *RVO and ORCA: How They Really Work* (GAIP3 cap. 19)
- *1000 NPCs at 60 FPS* (GAIP3 cap. 34)
- *Squad Coordination in Days Gone* (Online 2021 cap. 12)
