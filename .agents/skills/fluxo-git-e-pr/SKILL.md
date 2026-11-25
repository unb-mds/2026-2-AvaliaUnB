---
name: fluxo-git-e-pr
description: Define o padrão de branches, commits, Pull Requests, escopo de issues e autoria humana no repositório AvaliaUnB.
---

## Quando usar
- Antes de iniciar o trabalho em qualquer issue do repositório.
- Ao preparar uma entrega para revisão e abertura de Pull Request no GitHub.
- Ao revisar se as alterações feitas estão estritamente dentro do escopo combinado.

## Passo a passo
1. Ler integralmente a issue, incluindo *Subtarefas*, *Fora do escopo* e *Critérios de aceite*, antes de modificar qualquer arquivo.
2. Criar uma branch a partir da `main` atualizada seguindo o padrão do projeto: `feat/<num>-descricao`, `fix/<num>-descricao`, `docs/<num>-descricao` ou `task/<num>-descricao`.
3. Conferir `git status` e `git diff` para garantir que nenhum arquivo fora do escopo, arquivo temporário (`debug/`, `.env`) ou dado sensível foi alterado ou incluído.
4. Rodar a suíte de testes (`SECRET_KEY=chave-falsa python3 -m unittest discover -s tests -t .`) e verificar se todos os testes passam.
5. Fazer commits pequenos e descritivos no padrão Conventional Commits com o número da issue (ex.: `docs(agents): adiciona AGENTS.md na raiz (#161)`) — sempre executados manualmente por um integrante do grupo.
6. Abrir o Pull Request com resumo claro, lista de alterações e `Closes #<num>`, solicitando revisão de outro membro da equipe antes do merge.

## O que nunca fazer
- Nunca deixar agentes ou ferramentas de IA executarem `git commit`, `git push` ou merge de Pull Requests.
- Nunca commitar diretamente na branch `main` nem alterar arquivos listados na seção *Fora do escopo* da issue.
- Nunca incluir chaves, senhas, URLs privadas ou arquivos gerados localmente (`.env`, `debug/`) em um commit.
- Nunca fazer merge de um PR sem testes passando e sem revisão de outro integrante do grupo.