# Painel automático anti-cache do GitHub

Substitua estes arquivos no repositório de perfil `EoPaiva/EoPaiva`:

- `README.md`
- `scripts/generate-code-dashboard.mjs`
- `.github/workflows/update-code-dashboard.yml`
- `assets/github-code-dashboard.svg`

Depois vá em **Actions** e execute manualmente o workflow:

`Atualizar painel de código em produção`

O que esta versão faz:

1. Conta linhas, palavras, arquivos analisados, repositórios e stack principal.
2. Gera o SVG fixo `assets/github-code-dashboard.svg`.
3. Gera também um SVG com nome único, por exemplo `assets/github-code-dashboard-20260511065032.svg`.
4. Atualiza o `README.md` automaticamente entre os marcadores `CODE_DASHBOARD:START` e `CODE_DASHBOARD:END`.
5. Remove SVGs antigos gerados automaticamente.
6. Commita `README.md` + SVGs sozinho.

Assim, o README deixa de ficar preso no cache da imagem antiga.

Para repositórios públicos, não precisa token.
Para privados, crie um novo token e salve como secret `GH_STATS_TOKEN`. Nunca coloque token direto no código.
