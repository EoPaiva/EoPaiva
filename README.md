<!-- mPaiva_ · as animações são SVGs deste repositório, gerados por scripts/build-profile-assets.py -->

<p align="center">
  <img src="./assets/profile/hero.svg" width="100%" alt="mPaiva_ — Código, produto. Experiências que marcam. Full stack development, AI engineering, digital products." />
</p>

<p align="center">
  <a href="https://upaiva.dev/"><b>upaiva.dev</b></a> &nbsp;·&nbsp;
  <a href="https://www.linkedin.com/in/mateuspaiva21/"><b>LinkedIn</b></a> &nbsp;·&nbsp;
  <a href="mailto:mpaiiva21@gmail.com"><b>E-mail</b></a> &nbsp;·&nbsp;
  <a href="#projetos"><b>Projetos</b></a>
</p>

## Oi, eu sou o Mateus.

Desenvolvedor full stack e engenheiro de IA em São José dos Campos, SP. Construo produtos do zero até o ar: interface, backend, banco de dados, integrações com IA e deploy. Meu foco é software que resolve um problema de verdade e que dá vontade de usar.

- **Sistemas web completos**, com login, painel administrativo, APIs e banco, publicados e em uso.
- **IA aplicada a produto:** agentes, RAG, LLMs com contexto e ferramentas como MCP, sempre com uma pessoa no controle das decisões.
- **Automação e ferramentas:** bots, extensões do Chrome e apps de desktop que tiram trabalho manual do caminho.
- **Interfaces com identidade:** animação, tipografia e detalhe, sem pesar a página.

### Como eu trabalho

| Princípio | Na prática |
|---|---|
| **Mostro o que o software faz** | Comando real de cada etapa, auditoria append-only e logs à vista, em vez de caixa-preta. |
| **IA com decisão humana** | No CHOQUE a IA analisa e quem decide é uma pessoa; no Instagram Fluxo ela é opcional e roda com a sua chave. |
| **Teste antes de prometer** | 1.036 testes automatizados no CHOQUE e um status honesto do que ainda falta testar no win-toolkit. |
| **Leve de propósito** | Um `.exe` de 106 KB sem runtime extra, uma extensão sem framework e um site em HTML, CSS e JavaScript. |

<a name="projetos"></a>

## Projetos em destaque

### [CHOQUE BGR](https://choquebgr.online) &nbsp;<sub>Sistema de gestão · no ar</sub>

<p align="center">
  <a href="https://choquebgr.online"><img src="./assets/profile/feature-choque.svg" width="100%" alt="Centro de comando do CHOQUE BGR: ponto por voz com membros mudando de ACTIVE para GRACE e REVIEW, prova de recrutamento com timer no servidor e 24 questões salvas uma a uma, e o registro de auditoria sendo escrito." /></a>
</p>

Plataforma de gestão para uma unidade de roleplay, do Discord à web. Um bot faz cadastro, ponto por voz, carreira, disciplina e treinamentos só com botões, seletores e modais, sem nenhum comando de texto. Um centro de comando web com login Discord mostra tudo isso, e o recrutamento público aplica uma prova cronometrada no servidor.

- **Ponto por voz** com os estados `ACTIVE`, `GRACE`, `REVIEW_REQUIRED` e `CLOSED`, tolerância configurável e recuperação depois de reiniciar.
- **Recrutamento** com Discord OAuth, 24 questões balanceadas, autosave, timer no servidor e decisão final humana.
- **Confiável por padrão:** RBAC com cinco perfis, auditoria transacional com outbox, SQLite em WAL com migrations versionadas e mais de mil testes.

<p align="center">
  <img src="./assets/profile/stack-choque.svg" width="100%" alt="Stack do CHOQUE BGR: discord.py, Python 3.12, FastAPI e Uvicorn, SQLite em WAL, Next.js 16 e React 19, Auth.js com Discord, Tailwind 4 e Zod, Pytest, Vitest, Playwright e Ruff" />
</p>

### [win-toolkit](https://github.com/EoPaiva/win-toolkit) &nbsp;<sub>App para Windows 11 · v1.5</sub>

<p align="center">
  <a href="https://github.com/EoPaiva/win-toolkit"><img src="./assets/profile/feature-wintoolkit.svg" width="100%" alt="Janela do win-toolkit: quatro programas instalando em paralelo enquanto o MSI espera a vez, o planeta de partículas cuja órbita acende com o progresso e o terminal mostrando o comando real de cada etapa." /></a>
</p>

Do Windows recém-formatado ao PC pronto para trabalhar, em uma tela só. Você escolhe o que entra, acompanha o comando real de cada etapa e sai com um relatório do que funcionou e do que não funcionou.

- **Instalar:** 24 dependências estilo AIO e um catálogo de 102 itens, com perfis prontos (Completo, Básico, Gamer, Dev e IA) e até quatro instalações em paralelo, conforme CPU e RAM.
- **Drivers e análise:** drivers do catálogo oficial do Windows Update com backup do anterior, e uma varredura somente leitura de Defender, Firewall, TPM, BitLocker e portas abertas.
- **Otimizar sem susto:** quatro níveis com mais de 170 ações, simulação antes de aplicar e ponto de restauração. Nenhum nível desliga Defender, Firewall ou Windows Update.

<p align="center">
  <img src="./assets/profile/stack-wintoolkit.svg" width="100%" alt="Stack do win-toolkit: WPF e XAML, C# 5, .NET Framework 4.8, PowerShell 5.1, winget, npm e uv, Windows Update Agent, Inter e Cascadia Mono, DrawingContext" />
</p>

### [Instagram Fluxo](https://github.com/EoPaiva/instagram-fluxo) &nbsp;<sub>Extensão do Chrome · v3.1.3</sub>

<p align="center">
  <a href="https://github.com/EoPaiva/instagram-fluxo"><img src="./assets/profile/feature-instagram.svg" width="100%" alt="Painel do Instagram Fluxo percorrendo seis perfis: quatro confirmados, um pulado e um pausado para conferência, com os contadores mudando a cada passo." /></a>
</p>

Organiza quem você segue no Instagram com uma fila assistida. Lê as sugestões de três referências, segue só quem passa nas regras e para de seguir um perfil por vez, conferindo cada resultado no próprio perfil antes de avançar.

- **Ritmo seguro:** intervalos e pausas configuráveis, cota local de tentativas e pausa automática diante de qualquer aviso de restrição.
- **IA opcional com a sua chave:** fallback entre OpenAI, Claude, Gemini e OpenRouter, com as chaves num cofre local cifrado em AES-GCM.
- **Seus dados ficam com você:** fila, tentativas e histórico no navegador, e um coletor opcional para Windows que grava diagnósticos em JSONL.

<p align="center">
  <img src="./assets/profile/stack-instagram.svg" width="100%" alt="Stack do Instagram Fluxo: Chrome Manifest V3, JavaScript, HTML e CSS, chrome.storage, OpenAI, Claude, Gemini e OpenRouter, cofre AES-GCM com PBKDF2, coletor em Python com SQLite, instalação em PowerShell" />
</p>

## Também no ar

| Projeto | O que é | Stack |
|---|---|---|
| [**AZV Lançamentos**](https://azvlancamentos.com.br/) | Vitrine de lançamentos da AZV Imóveis, com página própria por empreendimento e uma home que se abre como uma parede de cobogó. | `Next.js` `GSAP` `Lenis` `TypeScript` |
| [**upaiva.dev**](https://upaiva.dev/) | Meu portfólio, com partículas em canvas, nove guias públicos sobre IA e um terminal no `Ctrl K`. | `HTML` `CSS` `JavaScript` `GSAP` |
| [**HumanReply AI**](https://contextual-chat-lab.vercel.app) | IA para atendimento B2B que reescreve respostas no tom da empresa. Em validação. | `TanStack Start` `TypeScript` `LLMs` |
| [**Studio JM**](https://studiojmarq.com/) | Plataforma para estúdio de arquitetura, com portfólio, briefing e painel administrativo. | `HTML` `Tailwind` `JavaScript` `Supabase` |

Extensões publicadas na Chrome Web Store: [Não Seguidores](https://chromewebstore.google.com/detail/n%C3%A3o-seguidores-upaiva/pggbblnnnofafnnieccbdopeaaafolin?hl=pt-br), [InstaGrowth IA](https://chromewebstore.google.com/detail/instagrowth-ia-upaiva/eopaifcdlgkmmpemkpkdklhaddgllbkc?hl=pt-br) e [Calc Impostos BR](https://chromewebstore.google.com/detail/calculadora-de-impostos-b/cifdfcomjlidngiddbdnhmcakecggehh).

## Stack

| Área | Ferramentas |
|---|---|
| **Frontend** | `TypeScript` `React` `Next.js` `TanStack` `Tailwind` `GSAP` `Framer Motion` `HTML` `CSS` |
| **Backend e dados** | `Node.js` `NestJS` `Python` `FastAPI` `Supabase` `PostgreSQL` `SQLite` `Prisma` |
| **IA aplicada** | `Claude` `OpenAI` `Gemini` `RAG` `MCP` `Vercel AI SDK` `LangChain` `Agentes` |
| **Automação e desktop** | `n8n` `discord.py` `Extensões Chrome (MV3)` `C#` `WPF` `PowerShell` |
| **Infra e qualidade** | `Vercel` `Docker` `GitHub Actions` `Playwright` `Vitest` `Pytest` |

## Código em produção

Atualizado sozinho a cada seis horas por um workflow deste repositório.

<!-- CODE_DASHBOARD:START -->
<p align="center">
  <img width="100%" src="./assets/github-code-dashboard-20261121072421.svg" alt="Painel automático de código em produção — linhas, palavras, repositórios e linguagens" />
</p>
<!-- CODE_DASHBOARD:END -->

## Vamos conversar

Aberto a projetos freelance e parcerias em produto digital, IA aplicada e automação. O caminho mais rápido é pelo [upaiva.dev](https://upaiva.dev/), pelo [LinkedIn](https://www.linkedin.com/in/mateuspaiva21/) ou por [e-mail](mailto:mpaiiva21@gmail.com).

<p align="center"><sub>mPaiva_ · São José dos Campos, SP · 2026</sub></p>
