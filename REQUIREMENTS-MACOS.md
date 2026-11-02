<!-- TOC -->
- [Requisitos no macOS (amd64 e arm64)](#requisitos-no-macos-amd64-e-arm64)
  - [1. Caminho automático](#1-caminho-automático)
  - [2. Instalação manual (fontes oficiais)](#2-instalação-manual-fontes-oficiais)
    - [Homebrew](#homebrew)
    - [Colima, CLI do Docker, Compose v2 e buildx](#colima-cli-do-docker-compose-v2-e-buildx)
    - [mise, Python e uv](#mise-python-e-uv)
  - [3. Conferência final](#3-conferência-final)
<!-- TOC -->

# Requisitos no macOS (amd64 e arm64)

No macOS os containers rodam numa VM Linux do **[Colima](https://github.com/abiosoft/colima)**; o Docker Desktop não é usado. As imagens do projeto são multi-arch (`linux/amd64` e `linux/arm64`), então funcionam tanto em Macs Intel quanto Apple Silicon.

## 1. Caminho automático

```bash
xcode-select --install       # make, git e curl (Command Line Tools)
make check-os                # confirma macOS e arquitetura (x86_64 ou arm64)
make install-dependencies    # instala Docker e mise, após confirmação
make install                 # não usa sudo, Python, uv, Node.js e as dependências; cria .env
make check-dependencies      # confere Colima/Docker/Compose/buildx/daemon/portas e indica o que falta
```

Ative o mise no shell ([documentação oficial](https://mise.jdx.dev/getting-started.html#activate-mise)):

```bash
echo 'eval "$(~/.local/bin/mise activate zsh)"' >> ~/.zshrc && source ~/.zshrc
```

`make install-dependencies` instala o Colima e a CLI do Docker. Para fazer à mão, ou para registrar os plugins e iniciar a VM, siga o passo 2.

## 2. Instalação manual (fontes oficiais)

### Homebrew

Fonte: [brew.sh](https://brew.sh).

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Colima, CLI do Docker, Compose v2 e buildx

Fontes: [Colima - Installation](https://github.com/abiosoft/colima#installation), fórmulas [docker](https://formulae.brew.sh/formula/docker), [docker-compose](https://formulae.brew.sh/formula/docker-compose) e [docker-buildx](https://formulae.brew.sh/formula/docker-buildx).

```bash
brew install colima docker docker-compose docker-buildx
```

Para a CLI do Docker encontrar os plugins `compose` e `buildx` instalados pelo Homebrew, siga o aviso das fórmulas e registre o diretório de plugins em `~/.docker/config.json`:

```bash
mkdir -p ~/.docker
cat > ~/.docker/config.json <<EOF
{
  "cliPluginsExtraDirs": ["$(brew --prefix)/lib/docker/cli-plugins"]
}
EOF
docker compose version && docker buildx version
```

(Se o `~/.docker/config.json` já existir, só acrescente a chave `cliPluginsExtraDirs`.)

Inicie a VM, que precisa estar rodando sempre que for usar o projeto:

```bash
colima start --cpu 4 --memory 8
docker run --rm hello-world
```

Em Apple Silicon, a VM é arm64 e as imagens arm64 rodam nativamente. Para gerar imagens amd64 também (opcional), habilite a emulação dentro da VM ([multi-platform builds](https://docs.docker.com/build/building/multi-platform/)):

```bash
docker run --privileged --rm tonistiigi/binfmt --install amd64,arm64
```

O lab 12 monta o socket do Docker, que o Colima expõe em `unix:///var/run/docker.sock` dentro da VM.

### mise, Python e uv

Fonte: [mise - Getting started](https://mise.jdx.dev/getting-started.html) (alternativa: `brew install mise`).

```bash
curl https://mise.run | sh
echo 'eval "$(~/.local/bin/mise activate zsh)"' >> ~/.zshrc && source ~/.zshrc
cd mba-protocolos-comunicacao
mise trust && mise install
mise exec -- uv sync --locked --all-packages
make secret                                                  # cria o .env e gera os segredos locais
```


## 3. Conferência final

```bash
make check-dependencies
make lab-smoke LAB=05
```
