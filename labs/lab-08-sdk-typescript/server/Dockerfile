# Multi-stage: o compilador fica no estágio de build, e a imagem final roda sem root.
FROM node:24.22.2-slim AS builder
WORKDIR /app
COPY package.json package-lock.json tsconfig.json ./
RUN npm ci
COPY src ./src
# O compilador verifica a estrutura antes de existir qualquer artefato para executar.
RUN npm run build && npm prune --omit=dev

FROM node:24.22.2-slim
WORKDIR /app
COPY --from=builder --chown=node:node /app/node_modules ./node_modules
COPY --from=builder --chown=node:node /app/dist ./dist
COPY --from=builder --chown=node:node /app/package.json ./
USER node
CMD ["node", "--import", "./dist/telemetry.js", "dist/index.js"]
