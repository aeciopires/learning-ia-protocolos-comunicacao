<!-- TOC -->
- [Requisitos](#requisitos)
  - [Resumo do que é necessário](#resumo-do-que-é-necessário)
  - [Caminho automático (todos os sistemas)](#caminho-automático-todos-os-sistemas)
<!-- TOC -->

# Requisitos

Os requisitos dependem do sistema operacional. Descubra se o seu é suportado:

```bash
make check-os
```

| Sistema | Arquitetura | Guia |
|---|---|---|
| Ubuntu 22.04, 24.04 e 26.04 | amd64 (x86_64) | [REQUIREMENTS-UBUNTU.md](REQUIREMENTS-UBUNTU.md) (guia único, com as diferenças entre as versões) |
| macOS | amd64 (Intel) e arm64 (Apple Silicon) | [REQUIREMENTS-MACOS.md](REQUIREMENTS-MACOS.md) (Colima no lugar do Docker Desktop) |

Qualquer outro sistema ou arquitetura é recusado por `make check-os`, com a indicação deste arquivo.

## Resumo do que é necessário

| Ferramenta | Quem instala | Para quê |
|---|---|---|
| `make`, `curl`, `git` | sistema operacional | Makefile e instaladores |
| Docker Engine + Compose v2 + buildx | `make install-dependencies`, após confirmação (Colima no macOS) | subir os labs e gerar imagens |
| [mise](https://mise.jdx.dev) | `make install-dependencies` (no diretório do usuário, sem sudo) | gerenciar as ferramentas do projeto |
| Python 3.14.10, uv 0.13.6, Node.js 24.22.2 e shellcheck 0.11.0 | `make install` (via mise, versões em [mise.toml](mise.toml)) | rodar testes e lint; Node.js serve ao MCP Inspector |
| `python3` no sistema | sistema operacional | scripts do Makefile; sem dependências externas |

## Caminho automático (todos os sistemas)

```bash
make check-os              # 1. sistema suportado?
make install-dependencies  # 2. Docker ou Colima e mise, após confirmação (DRY_RUN=1 só mostra os comandos)
make install               # 3. Python, uv, Node.js, dependências do workspace e .env
make check-dependencies    # 4. confere tudo
make lab-list              # 5. lista os laboratórios
```

A stack completa de um lab usa cerca de 1 GB de memória, sem contar os serviços do próprio lab.
