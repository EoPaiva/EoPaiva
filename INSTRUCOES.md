# Instalação rápida

1. Copie todos os arquivos para o repositório de perfil `EoPaiva/EoPaiva`.
2. Faça commit e push.
3. No GitHub, abra a aba Actions.
4. Execute manualmente o workflow `Atualizar painel de código em produção`.
5. O arquivo `assets/github-code-dashboard.svg` será atualizado automaticamente.

Para contar apenas repositórios públicos, não precisa criar token.
Para contar repositórios privados também, crie um novo token seguro e salve como secret `GH_STATS_TOKEN`; depois altere `INCLUDE_PRIVATE` para `true` no workflow.
