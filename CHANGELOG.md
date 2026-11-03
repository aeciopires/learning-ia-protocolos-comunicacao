<!-- TOC -->
<!-- TOC -->

# Changelog

Todas as mudanças relevantes deste repositório são registradas aqui. O formato segue o [Keep a Changelog 1.1.0](https://keepachangelog.com/pt-BR/1.1.0/), e os números de versão seguem o [Versionamento Semântico 2.0.0](https://semver.org/lang/pt-BR/spec/v2.0.0.html).

## Como as versões são numeradas

O Versionamento Semântico exige declarar uma API pública. Neste repositório, ela é formada pelos caminhos dos documentos, pela numeração dos labs, pelos alvos do `Makefile` e pelas variáveis do `.env.example`. Na prática, o tipo de mudança define qual parte do número aumenta:

| Parte | Quando aumenta | Exemplo |
| --- | --- | --- |
| MAJOR | Algo da API pública é removido, renomeado ou passa a funcionar de forma incompatível | Remover um lab, mover um documento ou renomear um alvo do `Makefile` |
| MINOR | Algo novo entra sem quebrar o que já existe | Criar um documento, um lab, um alvo ou uma variável com padrão |
| PATCH | Uma correção não muda a API pública | Corrigir um texto, um link, um diagrama ou um defeito em um lab |

## 1.0.0 - 2026-11-02

Primeira versão publicada, baseada na revisão `2026-07-28` do MCP e na versão `1.0.0` do A2A. As demais versões estão em [Versões de referência](README.md#versões-de-referência).

### Adicionado

- 12 documentos técnicos em `docs/`, dos fundamentos à operação segura de MCP e A2A, organizados na [trilha de leitura](README.md#trilha-de-leitura).
- [Guia para leigos](docs/guia-para-leigos.md), com analogias, diagramas em Mermaid e glossário.
- 15 laboratórios em Python e Docker Compose, em `labs/lab-01-nxm` a `labs/lab-15-integrador`, com testes que não dependem de Docker e provedor de LLM `fake` como padrão.
- [Stack de observabilidade](labs/observability/README.md) com OpenTelemetry Collector, Prometheus, Jaeger, Loki e Grafana, além de um dashboard para cada um dos labs 03 a 15.
- Código compartilhado pelos labs em `labs/common`.
- `Makefile` e `scripts/` para preparar o ambiente, gerar segredos locais e iniciar, testar e validar cada lab.
- Requisitos por sistema em `REQUIREMENTS.md`, `REQUIREMENTS-UBUNTU.md` e `REQUIREMENTS-MACOS.md`.
- Regras de manutenção em `CLAUDE.md`, guia de contribuição em `CONTRIBUTING.md` e licença GPLv3 em `LICENSE`.
- Este `CHANGELOG.md`, com os critérios de numeração das versões.
