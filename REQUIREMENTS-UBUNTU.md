<!-- TOC -->
- [Requisitos no Ubuntu (22.04, 24.04 e 26.04, amd64)](#requisitos-no-ubuntu-2204-2404-e-2604-amd64)
  - [Diferenças entre as versões](#diferenças-entre-as-versões)
  - [1. Caminho automático](#1-caminho-automático)
  - [2. Instalação manual (fontes oficiais)](#2-instalação-manual-fontes-oficiais)
    - [Docker Engine, Compose v2 e buildx](#docker-engine-compose-v2-e-buildx)
    - [mise, Python e uv](#mise-python-e-uv)
  - [3. Conferência final](#3-conferência-final)
<!-- TOC -->

# Requisitos no Ubuntu (22.04, 24.04 e 26.04, amd64)

Um único guia para as três versões LTS suportadas. Os passos são os mesmos; o que muda de uma versão para outra está na tabela abaixo e nos avisos **[22.04]**, **[24.04]** e **[26.04]** ao longo do texto.

## Diferenças entre as versões

| Item | 22.04 LTS | 24.04 LTS | 26.04 LTS |
|---|---|---|---|
| Codinome (`UBUNTU_CODENAME`) | `jammy` | `noble` | `resolute` |
| Suporte padrão da Canonical até | abril de 2027 | abril de 2029 | abril de 2031 |
| Repositório oficial do Docker (`download.docker.com`) | disponível | disponível | disponível |
| Python e uv do projeto | versões de `mise.toml` (iguais nas três) | idem | idem |

O que isso significa na prática:

- **[22.04]** Sai do suporte padrão em abril de 2027; prefira a 24.04 ou a 26.04 em máquinas novas.
- **[24.04]** Nada específico: todos os passos funcionam como estão.
- **[26.04]** Nada específico: os labs usam o Python do mise.
- **Em todas:** o codinome é lido de `/etc/os-release` no passo do Docker, então o mesmo comando serve para as três versões.

## 1. Caminho automático

```bash
sudo apt-get update && sudo apt-get install -y make curl git   # pré-requisitos do Makefile
make check-os                # confirma Ubuntu suportado e amd64
make install-dependencies    # instala Docker e mise, após confirmação
make install                 # não usa sudo, Python, uv, Node.js e as dependências; cria .env
make check-dependencies      # confere Docker/Compose/buildx/daemon/portas e indica o que falta
```

Se `~/.local/bin` não estiver no `PATH`, ative o mise ([documentação oficial](https://mise.jdx.dev/getting-started.html#activate-mise)):

```bash
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc && source ~/.bashrc
```

Se preferir instalar o Docker à mão, siga o passo 2.

## 2. Instalação manual (fontes oficiais)

### Docker Engine, Compose v2 e buildx

Fonte: [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/). As três versões (Jammy 22.04, Noble 24.04 e Resolute 26.04) estão na lista de suportadas, e os comandos abaixo são os mesmos para todas.

```bash
# Remove pacotes não oficiais que conflitam (o apt pode dizer que nenhum está instalado)
sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc docker-buildx podman-docker containerd runc | cut -f1)

# Chave GPG do repositório oficial da Docker
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Repositório (o codinome jammy/noble/resolute vem de /etc/os-release)
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt update

# Engine + CLI + buildx + Compose v2
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo docker run --rm hello-world
```

Se você já tinha o repositório configurado pelo formato antigo (`/etc/apt/sources.list.d/docker.list`), apague esse arquivo antes, para o apt não reclamar de fonte duplicada: `sudo rm -f /etc/apt/sources.list.d/docker.list`.

Para usar o Docker sem `sudo` ([pós-instalação no Linux](https://docs.docker.com/engine/install/linux-postinstall/)):

```bash
sudo usermod -aG docker "$USER"
newgrp docker    # ou faça logout/login
```

Para gerar imagens arm64 num host amd64 (opcional), habilite a emulação ([multi-platform builds](https://docs.docker.com/build/building/multi-platform/)):

```bash
docker run --privileged --rm tonistiigi/binfmt --install arm64
```

### mise, Python e uv

Fonte: [mise - Getting started](https://mise.jdx.dev/getting-started.html). Igual nas três versões.

```bash
curl https://mise.run | sh                                   # instala em ~/.local/bin
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc && source ~/.bashrc
cd learning-ia-protocolos-comunicacao
mise trust && mise install                                   # ferramentas nas versões de mise.toml
mise exec -- uv sync --locked --all-packages
make secret                                                  # cria o .env e gera os segredos locais
```

Referência do uv: [Installing uv](https://docs.astral.sh/uv/getting-started/installation/). Aqui ele vem pelo mise, não precisa instalar à parte.


## 3. Conferência final

```bash
make check-dependencies
make lab-smoke LAB=05
```
