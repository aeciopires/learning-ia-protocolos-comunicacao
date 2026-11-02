#!/usr/bin/env bash
# Recusa sistemas e arquiteturas sem suporte, conforme REQUIREMENTS.md.
set -euo pipefail
source "$(dirname "$0")/lib.sh"

arch="$(uname -m)"
case "$(uname -s)" in
  Darwin)
    case "$arch" in
      x86_64 | arm64) ok "macOS $(sw_vers -productVersion) ($arch)" ;;
      *) fail "Unsupported architecture: $arch. See REQUIREMENTS.md"; exit 1 ;;
    esac
    ;;
  Linux)
    # shellcheck disable=SC1091
    . /etc/os-release
    case "${ID:-}:${VERSION_ID:-}" in
      ubuntu:22.04 | ubuntu:24.04 | ubuntu:26.04) ;;
      *) fail "Unsupported system: ${PRETTY_NAME:-unknown}. See REQUIREMENTS.md"; exit 1 ;;
    esac
    if [ "$arch" != x86_64 ]; then
      fail "Unsupported architecture on Ubuntu: $arch (only amd64). See REQUIREMENTS.md"
      exit 1
    fi
    ok "$PRETTY_NAME ($arch)"
    ;;
  *) fail "Unsupported system: $(uname -s). See REQUIREMENTS.md"; exit 1 ;;
esac
