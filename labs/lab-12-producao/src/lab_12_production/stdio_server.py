"""O mesmo server em stdio, para o Docker MCP Gateway iniciar em um container próprio."""

from lab_12_production.app import build_server

if __name__ == "__main__":
    build_server().run()
