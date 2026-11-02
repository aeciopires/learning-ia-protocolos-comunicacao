#!/usr/bin/env bash
# Instala as dependências do sistema, seguindo REQUIREMENTS-UBUNTU.md ou REQUIREMENTS-MACOS.md.
# Altera o sistema, por isso mostra o plano e pede confirmação. DRY_RUN=1 só exibe os comandos.
set -euo pipefail
source "$(dirname "$0")/lib.sh"

DRY_RUN="${DRY_RUN:-0}"
ASSUME_YES="${ASSUME_YES:-0}"

run() {
  printf '  $ %s\n' "$*"
  if [ "$DRY_RUN" != 1 ]; then
    bash -c "$*"
  fi
}

confirm() {
  if [ "$DRY_RUN" = 1 ] || [ "$ASSUME_YES" = 1 ]; then
    return 0
  fi
  read -r -p "This changes your system and may ask for sudo. Continue? [y/N] " answer
  case "$answer" in
    y | Y | yes | s | S | sim) return 0 ;;
    *) info "Nothing was changed."; exit 0 ;;
  esac
}

install_ubuntu() {
  info "Ubuntu: base packages and Docker Engine from the official repository."
  confirm
  run "sudo apt-get update"
  run "sudo apt-get install -y make curl git ca-certificates"
  if ! command -v docker >/dev/null 2>&1; then
    run "sudo install -m 0755 -d /etc/apt/keyrings"
    run "sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc"
    run "sudo chmod a+r /etc/apt/keyrings/docker.asc"
    # O codinome vem de /etc/os-release, então o mesmo comando serve para as três versões.
    # shellcheck disable=SC2016
    run 'printf "Types: deb\nURIs: https://download.docker.com/linux/ubuntu\nSuites: %s\nComponents: stable\nArchitectures: %s\nSigned-By: /etc/apt/keyrings/docker.asc\n" "$(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")" "$(dpkg --print-architecture)" | sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null'
    run "sudo apt-get update"
    run "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
    # shellcheck disable=SC2016
    run 'sudo usermod -aG docker "$USER"'
    warn "Log out and back in (or run: newgrp docker) to use Docker without sudo."
  else
    ok "Docker is already installed."
  fi
}

install_macos() {
  info "macOS: Homebrew, Colima, Docker CLI, Compose and buildx."
  confirm
  if ! command -v brew >/dev/null 2>&1; then
    fail "Homebrew is required. Install it from https://brew.sh and run this again."
    exit 1
  fi
  run "brew install colima docker docker-compose docker-buildx"
  warn "Register the Docker plugins and start the VM as described in REQUIREMENTS-MACOS.md."
}

if ! os="$(detect_os)"; then
  fail "Unsupported system. See REQUIREMENTS.md"
  exit 1
fi
"install_$os"

if ! command -v mise >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/mise" ]; then
  info "Installing mise in ~/.local/bin (official installer, no sudo)."
  run "curl -fsSL https://mise.run | sh"
fi
ok "Done. Next: make install"
