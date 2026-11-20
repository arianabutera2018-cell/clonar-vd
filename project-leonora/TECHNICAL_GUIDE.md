# PROJECT LEONORA — Guia Técnico

> Este guia explica **com quais ferramentas** o jogo será feito e **cuidados técnicos** importantes.
> Está escrito para quem está começando. Termos técnicos têm explicação ao lado.
>
> Itens marcados como **💡 Recomendação** são sugestões técnicas, **não decisões tomadas**.
> Eles só viram decisão depois que o proprietário aprovar.

---

## 1. Ferramentas

| Ferramenta | Grátis? | Para que serve | Situação |
|---|---|---|---|
| **Roblox Studio** | ✅ Sim | Programa oficial do Roblox para montar e testar o jogo | Decidido (é obrigatório para jogos Roblox) |
| **Blender** | ✅ Sim | Programa para criar modelos 3D (personagens, prédios, carros) | ✅ Decidido |
| **Roblox Open Cloud** | ✅ Sim | "Porta de acesso" do Roblox pela internet: deixa o Claude alterar o jogo sem abrir o Studio | Já conectado |
| **GitHub** | ✅ Sim (plano grátis) | Guarda a documentação e, futuramente, os códigos, com histórico de mudanças | Já conectado |

✅ Decidido: **prioridade para ferramentas gratuitas**.

❓ Pendente: usar ou não outras ferramentas gratuitas (por exemplo, programas de textura ou de organização de código). Nenhuma será adicionada sem aprovação.

## 2. Linguagem de programação

O Roblox usa a linguagem **Luau**, uma versão do Lua feita pelo Roblox. É nela que os sistemas do jogo serão escritos (veículos, missões, dinheiro, guarda-roupa etc.).

- **Script** = código que roda no **servidor** (o "computador do Roblox" que controla o jogo).
- **LocalScript** = código que roda no **aparelho do jogador** (celular/PC), usado para câmera, tela, botões.
- **ModuleScript** = código "compartilhado", usado por outros scripts.

## 3. Visual realista no Roblox

O Roblox tem limites, mas oferece recursos para um visual mais realista:

| Recurso | O que é |
|---|---|
| **Iluminação "Future"** | Modo de luz mais realista do Roblox (sombras e luzes melhores) |
| **MeshPart** | Peça com formato vindo do Blender (modelo 3D próprio) |
| **SurfaceAppearance / PBR** | Texturas realistas (cor, brilho, relevo, metal) |
| **Atmosphere / Sky** | Céu, neblina e cor do ar |
| **Pós-efeitos** | Brilho (Bloom), cor (ColorCorrection), raios de sol etc. |

⚠️ Cada recurso realista **pesa mais** no celular. Visual e desempenho precisam andar juntos (seção 5).

## 4. Personagens

- O protagonista terá **modelo próprio feito no Blender**, com corpo humano realista.
- Para ser usado no Roblox, o modelo precisa de **esqueleto** (rig) compatível com animações do Roblox.
- 💡 Recomendação: usar o padrão de corpo **R15** do Roblox (15 partes) ou um rig próprio compatível. A escolha final fica pendente.
- O visual precisa seguir os **Padrões da Comunidade do Roblox**. A opção **sem camisa** é permitida para personagens masculinos, desde que o modelo respeite essas regras e a classificação etária do jogo.

❓ Pendente: animações (andar, correr, dirigir, combate) próprias ou padrão do Roblox.

## 5. Desempenho (rodar bem no celular)

✅ Decidido: **desempenho considerado desde o início**, com testes em celulares como o **POCO X7 Pro**.

Por que importa: mundo aberto + visual realista é a combinação **mais pesada** que existe. Se não cuidar desde o começo, o jogo trava no celular e fica difícil de consertar depois.

💡 Recomendações técnicas (dependem de aprovação):

| Técnica | Explicação simples |
|---|---|
| **StreamingEnabled** | O celular só carrega a parte do mapa que está perto do jogador, e não a cidade inteira |
| **LOD (nível de detalhe)** | Objetos longe ficam mais simples; de perto ficam detalhados |
| **Limite de polígonos** | Cada modelo do Blender tem um "orçamento" de detalhes, para não pesar |
| **Reaproveitar modelos e texturas** | Usar o mesmo prédio/árvore várias vezes pesa menos que muitos diferentes |
| **Poucos NPCs e carros ativos ao mesmo tempo** | Só existem os que estão perto do jogador |
| **Medir sempre** | Testar o FPS (fluidez) e a memória no POCO X7 Pro a cada etapa |

❓ Pendente: FPS mínimo aceitável, outros aparelhos de teste, limites exatos de polígonos.

## 6. Um jogador por servidor

✅ Decidido: **um jogador por servidor**.

- No Roblox isso se faz ajustando o **tamanho máximo do servidor** para **1**.
- Hoje a experiência ainda está com **50** (padrão). **Não foi alterado**, pois nada deve ser mudado nesta fase.
- Vantagem: o mundo inteiro "pertence" ao jogador, o que facilita missões, NPCs e economia.

## 7. Salvamento de dados

✅ Decidido: a **roupa escolhida no guarda-roupa** deve ser **salva**.

- No Roblox, o salvamento é feito com o **DataStore**: um "caderno" do Roblox onde o jogo anota o progresso de cada jogador.
- 💡 Recomendação: planejar um único "perfil" por jogador, onde futuramente também ficarão dinheiro, missões e casas. Pendente de aprovação.

## 8. Fluxo de trabalho com o Claude

- O Claude escreve código e cria modelos **por meio de comandos**. Ele **não** usa o Roblox Studio nem o Blender com mouse.
- O Claude **não consegue jogar** para testar. O proprietário testa e envia prints e vídeos.
- O **Blender** usado pelo Claude é temporário: precisa ser reinstalado em cada nova sessão na nuvem.
- Toda mudança importante deve ser anotada no `CHANGELOG.md`.
- ⚠️ **Nunca colar chaves de API no chat.** Usar sempre o formulário seguro.

## 9. Regras para esta fase (planejamento)

Enquanto estiver na fase de planejamento:
- ❌ Não criar objetos no Roblox Studio.
- ❌ Não criar scripts.
- ❌ Não abrir nem alterar projetos do Blender.
- ❌ Não instalar ferramentas.
- ❌ Não publicar o jogo.
- ❌ Não alterar o mapa.
