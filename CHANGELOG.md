# Registro de alterações

## 2026-10-02 — Preparação para publicação

- Publicação do dashboard React e do projeto Power BI com dataset sintético de 30.170 pedidos.
- Lockfile npm, exemplo de variáveis opcionais e exclusão de arquivos locais e credenciais do versionamento.
- Validação CSV/JSON, integridade das quatro dimensões e testes de indicadores com recortes do dashboard.
- GitHub Actions para lint, testes, build e verificação da pasta publicada no GitHub Pages.
- README com pergunta de negócio, execução reproduzível e limites do modelo e da validação Power BI.
- A primeira execução dos testes detectou uma comparação exata inadequada para lucro em ponto flutuante;
  a asserção foi corrigida para comparar centavos inteiros. Os valores exibidos não precisaram de alteração.

A validação no Power BI Desktop e a incorporação pelo Power BI Service são verificações separadas.
