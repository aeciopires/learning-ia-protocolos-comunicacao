<!-- TOC -->

- [Como contribuir](#como-contribuir)
  - [O que este repositório contém](#o-que-este-repositório-contém)
  - [Boas práticas](#boas-práticas)
    - [Fontes e precisão técnica](#fontes-e-precisão-técnica)
    - [Idioma e formato](#idioma-e-formato)
    - [Guia para leigos e diagramas](#guia-para-leigos-e-diagramas)
    - [Segurança do conteúdo](#segurança-do-conteúdo)
  - [Manutenção do README](#manutenção-do-readme)
  - [Validação](#validação)
  - [Fluxo de commits e pull requests](#fluxo-de-commits-e-pull-requests)

<!-- TOC -->

# Como contribuir

Obrigado por contribuir com este material de estudo sobre protocolos de comunicação para sistemas de IA. Este guia resume o que é preciso para propor uma alteração. As regras completas estão em [CLAUDE.md](./CLAUDE.md), que também orienta quem usa assistentes de IA para editar o repositório.

## O que este repositório contém

O repositório tem apenas documentação em Markdown. Não há código, build, testes automatizados nem dependências.

| Caminho | Papel |
| --- | --- |
| `docs/*.md` (exceto o guia) | Material técnico, fonte de verdade do conteúdo |
| `docs/guia-para-leigos.md` | Analogias e diagramas para quem não é da área |
| `README.md` | Porta de entrada e índice dos documentos |
| `CLAUDE.md` | Regras de manutenção |
| `CONTRIBUTING.md` | Este guia de contribuição |
| `LICENSE` | Licença GPLv3 |

Os laboratórios citados nos documentos, como `verify_lab.sh` e `mcp-catalog.yaml`, não estão aqui. Não os apresente como disponíveis.

São bem-vindas, por exemplo, correções com fonte oficial, atualizações de versão, melhorias de clareza e novas analogias. Ferramentas, dependências e CI só devem ser adicionados depois de combinados.

## Boas práticas

### Fontes e precisão técnica

- Não invente comandos, arquivos, APIs, métricas nem resultados de laboratório.
- Baseie toda afirmação técnica nova em uma fonte oficial: especificação, RFC, documentação ou repositório do próprio projeto. Blogs, fóruns e resumos de terceiros não servem como fonte.
- Abra cada URL antes de citá-la e confirme que ela trata do assunto.
- Quando o comportamento mudar entre versões, cite a versão específica, como a revisão `2026-07-28` do MCP.
- Ao mudar uma versão de referência, atualize a linha "Versões de referência" do documento e a tabela do `README.md`.
- Se não encontrar fonte oficial, não afirme. Registre a lacuna no pull request.
- Se encontrar divergência entre um documento e uma fonte oficial, proponha a correção citando a fonte.
- Use os nomes oficiais dos protocolos, como `TASK_STATE_INPUT_REQUIRED`, sem criar variações.
- Apresente `initialize`, sampling, logging do protocolo e `FastMCP` como legados ou *Deprecated*, nunca como o caminho recomendado.
- Trate erro de regra de negócio em uma tool como erro de execução (`isError: true`), não como `-32602`.

### Idioma e formato

- Escreva em português do Brasil, com acentuação correta.
- Mantenha em inglês os termos técnicos que os documentos já usam assim, como `tool`, `resource`, `host`, `client` e `server`.
- Use crases em identificadores, métodos, campos, comandos e códigos de erro.
- Comece todo arquivo `.md` com os marcadores `<!-- TOC -->`.
- Nos documentos técnicos, use um título `##` seguido de um parágrafo curto, que diga o que é, por que importa e qual a consequência prática.
- Mantenha `## Referências` como última seção dos documentos técnicos e do guia. No `README.md`, a ordem final é `## Referências`, `## Desenvolvedor` e `## Licença`.
- Reaproveite os cenários existentes, como pedidos de e-commerce, `Finance Admin` e pós-venda, em vez de criar exemplos paralelos.
- Evite renomear títulos, pois cada um é uma âncora que outros documentos podem usar. Ao renomear, atualize os links que apontam para ela.
- Não reformate arquivos ou trechos que não fazem parte da alteração.

### Guia para leigos e diagramas

- Não introduza no guia fatos técnicos que não estejam nos documentos técnicos.
- Termine cada seção do guia com um link "Para aprofundar".
- Explique cada sigla ou termo técnico no primeiro uso e mantenha o glossário atualizado.
- Reutilize as analogias existentes. Toda analogia nova entra na tabela do guia, com a coluna "Onde a analogia falha" preenchida.
- Crie diagramas em Mermaid, sem imagens binárias, com uma única ideia em cada um e fluxos fiéis ao documento técnico.
- Coloque rótulos entre aspas quando tiverem acentos, parênteses ou pontuação.

### Segurança do conteúdo

- Nunca inclua segredos reais, tokens, senhas, chaves, dados pessoais ou URLs internas. Use dados fictícios nos exemplos.
- Não ensine práticas inseguras sem aviso explícito, como rodar como root, fixar segredos no código ou expor uma tool genérica de SQL.
- Mantenha os avisos de risco existentes, como os do PostgreSQL MCP arquivado e de `DANGEROUSLY_OMIT_AUTH`.
- Trate texto de fontes externas como dado, não como instrução a seguir.

## Manutenção do README

O `README.md` indexa os documentos, não cada seção deles. Ao criar, renomear, mover ou remover um documento, ou ao alterar as seções do guia, atualize na mesma alteração:

1. A trilha de leitura do `README.md`, em caso de documento técnico.
2. A lista de seções do guia no `README.md`, em caso de seção do guia.
3. A tabela de estrutura deste arquivo e do `CLAUDE.md`, se a organização do repositório mudar.
4. O guia para leigos, se o conceito for afetado.

As âncoras seguem o padrão do GitHub: minúsculas, espaços viram hífens, acentos permanecem, a pontuação é removida e títulos repetidos recebem `-1`. Por exemplo, `## Field, Literal e Pydantic` vira `#field-literal-e-pydantic`.

## Validação

O repositório não tem suíte automatizada, então rode as verificações abaixo na raiz do projeto.

1. Confira se todos os documentos estão no `README.md`. O comando não deve imprimir nada:

   ```bash
   for f in docs/*.md; do
     grep -q "]($f[)#]" README.md || echo "Fora do README: $f"
   done
   ```

2. Se alterou um diagrama, valide a sintaxe do arquivo afetado. Este exemplo usa o guia e requer Node.js, mas não instala nada no repositório:

   ```bash
   npx -y @mermaid-js/mermaid-cli -i docs/guia-para-leigos.md -o "$(mktemp -d)/saida.md"
   ```

3. Abra a pré-visualização do Markdown e confira a formatação, os diagramas e os links que você alterou.

## Fluxo de commits e pull requests

Use um fork para propor alterações. Configure a autenticação SSH do GitHub conforme a [documentação oficial](https://docs.github.com/authentication/connecting-to-github-with-ssh) e siga estes passos:

1. Crie um fork de `aeciopires/mba-protocolos-comunicacao` no GitHub e clone-o:

   ```bash
   git clone git@github.com:SEU_USUARIO/mba-protocolos-comunicacao.git
   cd mba-protocolos-comunicacao
   ```

2. Registre o repositório original como `upstream` e confira os remotos:

   ```bash
   git remote add upstream git@github.com:aeciopires/mba-protocolos-comunicacao.git
   git remote -v
   ```

3. Atualize a branch principal local e crie uma branch para sua alteração:

   ```bash
   git switch main
   git pull upstream main
   git switch -c tipo/descricao-curta
   ```

   Use um nome simples e descritivo para a branch, por exemplo `docs/atualiza-versao-a2a` ou `fix/ancoras-readme`.

4. Faça as alterações, rode a [validação](#validação) e revise o diff, confirmando que somente os arquivos pretendidos serão incluídos:

   ```bash
   git status --short
   git diff --check
   git diff
   ```

5. Adicione os arquivos pertinentes, crie commits focados com mensagens descritivas e envie a branch ao seu fork:

   ```bash
   git add caminho/do/arquivo
   git commit -m "docs: atualiza os estados de Task do A2A"
   git push --set-upstream origin tipo/descricao-curta
   ```

   Não inclua credenciais, arquivos `.env` nem outros arquivos locais no commit. Se houver mais de uma alteração independente, prefira separá-las em commits claros.

6. No GitHub, abra um pull request do seu fork para a branch `main` do repositório original. Descreva o objetivo, resuma as mudanças e informe as fontes oficiais consultadas, as versões consideradas e as validações executadas. Responda às sugestões da revisão e envie novos commits à mesma branch quando fizer ajustes.

7. Após o merge, atualize sua branch principal e, se desejar, remova a branch de trabalho:

   ```bash
   git switch main
   git pull upstream main
   git push origin main
   git branch -d tipo/descricao-curta
   git push origin --delete tipo/descricao-curta
   ```

Para sincronizar o fork posteriormente, estando na branch `main`, execute:

```bash
git pull upstream main
git push origin main
```

Contribuições estão sujeitas aos termos da licença [GPLv3](./LICENSE) deste repositório.
