# PROJECT LEONORA — Estado Atual

> Última atualização: **20/11/2026**

---

## 1. Fase atual

**Fase: Planejamento (documentação inicial)**

- ✅ Nome do projeto definido: **PROJECT LEONORA**.
- ✅ Decisões principais registradas (veja `PROJECT_MASTER.md` e `GAME_DESIGN.md`).
- ⬜ Nada foi construído no Roblox Studio.
- ⬜ Nenhum modelo 3D foi criado no Blender para o projeto.
- ⬜ Nenhum script foi escrito para o projeto.
- ⬜ A região de teste ainda não foi escolhida.

## 2. A experiência no Roblox

| Item | Valor |
|---|---|
| Nome atual no Roblox | `blooz_0's Place: 11122026_1` (ainda não foi renomeado) |
| Universe ID (número do jogo) | `10776083475` |
| Place ID (número do lugar principal) | `112034481350216` |
| Link do painel | https://create.roblox.com/dashboard/creations/experiences/10776083475/overview |
| Acesso | **Privado** (ninguém de fora consegue entrar) |
| Conteúdo atual | **Limpo**: só o modelo padrão do Roblox (chão "Baseplate", ponto de nascimento e iluminação padrão) |
| Versão publicada | **Versão 5** (a versão limpa) |
| Tamanho do servidor | 50 (padrão do Roblox, ainda não ajustado para 1 jogador) |
| Classificação etária mostrada pela API | 13+ (herdada, ainda não revisada para este projeto) |

**Observação:** antes de ficar limpa, essa experiência tinha um projeto antigo, sem relação com o PROJECT LEONORA (um jogo de terror 1 contra 4). Ele foi removido a pedido do proprietário. Se for preciso, ele pode ser recuperado em **Dashboard → Locais → Histórico de versões → versão 4**.

## 3. Ferramentas conectadas

| Ferramenta | Situação | Explicação simples |
|---|---|---|
| **Roblox Open Cloud (chave de API "Claud")** | Conectada | É uma "senha" especial que deixa o Claude ler e alterar o jogo pela internet, sem abrir o Roblox Studio. |
| **Blender 5.3** | Disponível só na sessão atual do Claude, na nuvem | Instalado como teste para criar modelos 3D por código. **Não fica instalado para sempre**: quando a sessão na nuvem acaba, ele some e precisa ser instalado de novo. Os modelos já enviados ao Roblox não se perdem. Nenhum projeto do Blender foi criado para o PROJECT LEONORA. |
| **Roblox Studio** | Não conectado | O Studio está no PC do proprietário. O Claude não tem acesso a ele. |
| **Repositório GitHub** (`clonar-vd`) | Conectado | É onde esta pasta de documentação fica guardada. |

### Permissões da chave "Claud" (o que ela deixa fazer)

| Sistema | Permissão | Para que serve |
|---|---|---|
| universe | universe.place: write | Mudar informações do jogo (descrição, tamanho do servidor) |
| universe-places | write | Publicar novas versões do jogo |
| legacy-assets | legacy-asset: manage | Baixar o arquivo do jogo para leitura |
| assets | read / write | Enviar imagens e modelos 3D |
| universe-thumbnail | read / write | Enviar imagens de capa |

### ⚠️ Atenção com a chave
- A chave **"Claud"** foi colada em texto numa conversa anterior. Isso é um **risco de segurança**: quem tiver o texto da chave pode alterar seus jogos.
- **Recomendação:** excluir essa chave e criar uma nova quando o trabalho for continuar, entregando a nova pelo formulário seguro, **nunca colando no chat**.
- **Pendente:** o proprietário ainda não decidiu quando fazer essa troca.

## 4. Outro jogo na mesma conta (para não confundir)

O jogo **"[🌊PRAIA]Sobreviva às suas idéias [ENHANCED]"** (Universe ID `10777052897`) é **outro projeto**, já publicado, e **não faz parte** do PROJECT LEONORA.

## 5. Bloqueios e riscos atuais

- **Decisões pendentes:** várias perguntas importantes ainda não foram respondidas (lista em `PROJECT_MASTER.md`, seção 6).
- **Testes:** o Claude não consegue jogar para testar. Todos os testes dependem do proprietário, com prints e vídeos.
- **Blender temporário:** precisa ser reinstalado em cada nova sessão na nuvem.
