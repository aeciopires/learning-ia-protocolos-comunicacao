#!/usr/bin/env bash
# Funções compartilhadas pelos scripts do Makefile.

info() { printf '[info] %s\n' "$*"; }
ok() { printf '\033[32m[ ok ]\033[0m %s\n' "$*"; }
warn() { printf '\033[33m[warn]\033[0m %s\n' "$*"; }
fail() { printf '\033[31m[fail]\033[0m %s\n' "$*" >&2; }

# Lê uma variável do .env sem executar o arquivo como shell.
env_value() {
  local name="$1" file="${2:-.env}"
  [ -f "$file" ] || return 0
  grep -E "^${name}=" "$file" | tail -1 | cut -d= -f2-
}

# Identifica o sistema suportado: ubuntu ou macos. Retorna erro nos demais.
detect_os() {
  case "$(uname -s)" in
    Darwin) echo macos ;;
    Linux)
      # shellcheck disable=SC1091
      . /etc/os-release
      if [ "${ID:-}" = ubuntu ]; then echo ubuntu; else return 1; fi
      ;;
    *) return 1 ;;
  esac
}
