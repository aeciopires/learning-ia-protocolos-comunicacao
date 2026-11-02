# Imagem comum aos labs em Python: multi-stage, sem ferramentas de build em runtime e sem root.
FROM python:3.14.10-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv
ARG LAB_PACKAGE
ENV UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY labs ./labs
# --no-editable instala o lab no ambiente virtual, então o estágio final só precisa de .venv.
RUN uv sync --frozen --no-dev --no-editable --package "${LAB_PACKAGE}"

FROM python:3.14.10-slim
# O ownership é ajustado antes de USER: sem isso, o processo perderia acesso aos próprios arquivos.
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
USER app
