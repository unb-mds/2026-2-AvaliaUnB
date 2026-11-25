# Cibersegurança

Esta página resume os mecanismos existentes e o plano de correção da
[auditoria de segurança](AUDITORIA_SEGURANCA.md), realizada em 02/11/2026 na
[issue #111](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/111).
O relatório detalhado é a referência para evidências, método e limites da revisão.

## Mecanismos implementados

| Área | Comportamento atual | Onde consultar no código |
|---|---|---|
| Contas | Entrada apenas com conta Google, pelo Supabase Auth com fluxo PKCE; o app não recebe nem guarda senhas | `UsuarioRepository`, em `app/repositorio.py` |
| Segredos | Configuração por ambiente ou `.env`, fora do Git; service key usada no servidor | `app/supabase_db.py`, `.env.example` |
| Sessão | Cookies `HttpOnly`, `SameSite=Lax` e `Secure` fora do debug; renovação pelo Supabase | `app/controllers/session_controller.py`, `app/seguranca.py` |
| Formulários | Proteção CSRF; token inválido ou ausente resulta em HTTP 400 | `app/__init__.py`, `app/seguranca.py`, templates |
| Autorização | Login exigido nas rotas protegidas; edição e exclusão filtradas pelo autor | Controllers, rotas e repositório de avaliações |
| Headers | CSP, proteção contra enquadramento, tipo de conteúdo e política de referência; HSTS em HTTPS fora do debug | `app/seguranca.py` |
| Limites | Limitação de requisições do login com Google, de avaliação, de publicação de comentários (10 por hora por usuário) e de denúncias (10 por hora por usuário) | `app/seguranca.py` |
| Qualidade | Testes automatizados, pip-audit e Bandit no GitHub Actions | [Pipeline](pipeline.md) |

`SECRET_KEY` é obrigatória na fábrica da aplicação. A configuração de segurança
também verifica chaves fracas em produção. O debug fica desligado por padrão.
Os tokens de autenticação ficam nos cookies e a service key não deve ser
incluída em templates, respostas ou recursos estáticos.

## Resultado da auditoria

O relatório registrou um achado de prioridade alta, três de prioridade média
e oito de prioridade baixa, sem achados críticos. Na data da auditoria,
pip-audit não identificou vulnerabilidades conhecidas nos dois arquivos de
dependências, e Bandit não apontou severidade média ou alta.

Esses resultados correspondem à revisão de 02/11/2026. O relatório informa que
não foi realizado teste de invasão e que alterações posteriores, incluindo a
navegação de retorno, precisam de revisão própria.

## Banco e RLS

Na data da auditoria, as cinco tabelas do banco consultado tinham RLS ativo
sem políticas. O [modelo de dados](Modelo%20de%20Dados.md) detalha essa revisão. A aplicação
usa a service key, que ignora RLS; a autorização do caminho atual depende do
backend. A view `vw_professor_disciplina` expõe dados públicos de professores,
disciplinas e turmas, com as permissões descritas no modelo.

O [PR #139](https://github.com/unb-mds/2026-2-AvaliaUnB/pull/139) incluiu RLS e
políticas no esquema inicial. O SQL versionado contém leitura pública para
catálogo, perfis e avaliações e regras de escrita vinculadas ao usuário em
perfis e avaliações. A adoção da chave pública foi adiada para depois do
lançamento. O PR #141 causou regressão em produção e foi revertido pelo PR #157.

## Correções acompanhadas

**Situação atualizada conforme a issue #182.** A aplicação das migrações em
cada ambiente deve ser verificada separadamente.

| Issue | Prioridade na auditoria | Entrega e situação |
|---|---|---|
| [#123](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/123) | Alta | RLS e políticas versionados no esquema inicial pelo PR #139 |
| [#124](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/124) | Média | Adiada: cliente de chave pública e leitura pública com RLS |
| [#129](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/129) | Desdobramento da #124 | Adiada: avaliações com sessão do usuário e autorização também no banco |
| [#130](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/130) | Desdobramento da #124 | Adiada: perfil do usuário com chave pública e RLS |
| [#125](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/125) | Média | Cancelada: confirmação do e-mail; login atual pelo Google |
| [#126](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/126) | Média | Entregue: revogação da sessão no logout com token de acesso expirado |
| [#127](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/127) | Baixa | Ajustes de CSRF, limites, mensagens, consultas, validações, logs e testes |

Concluir a auditoria significa ter o relatório e o plano de correção. Cada
correção deve atualizar o comportamento documentado quando for entregue.
Não é necessário esperar essas implementações para publicar o diagnóstico.

## Filtro de comentários

O filtro automático (issue #214) reduz a exposição de dados pessoais e de
ofensas em texto público. Ele roda no servidor, ao publicar e ao editar um
comentário, depois da validação de tamanho e antes de gravar. Bloqueia e-mail,
telefone, CPF, matrícula, links e termos de uma lista em
`app/dados/termos_bloqueados.txt`. As regras estão em
[Comentários](COMENTARIOS.md) e o código, em `app/filtro_comentarios.py`.

- O texto bloqueado não é gravado nem registrado em log, e a mensagem de erro
  não revela o trecho que disparou o filtro nem a lista de termos.
- O envio bloqueado conta no limite de 10 comentários por hora por usuário,
  pois o limite se aplica a toda requisição de publicação.
- O filtro não é moderação e não substitui as denúncias: reconhece só violações
  claras e pode ser driblado (por exemplo, com homóglifos ou números por
  extenso). Casos duvidosos passam e ficam para a moderação por denúncia.
- A lista de termos deve ser revisada pelo grupo e mantida em arquivo
  versionado, para que as mudanças passem por revisão no PR.

## Comentários e moderação

As regras de comentários, denúncia, moderação e privacidade estão em
[Comentários](COMENTARIOS.md). A denúncia (#215) fica numa tabela privada,
acessível só pelo servidor, e não revela quem denunciou. A área de moderação
(#216) é restrita ao papel de moderador (`moderador_required`), registra cada
decisão com justificativa e permite ao autor contestar uma ocultação. Os
registros encerrados são descartados após 90 dias (#217).

Relacionado: [auditoria de 02/11](AUDITORIA_SEGURANCA.md),
[modelo de dados](Modelo%20de%20Dados.md), [pipeline](pipeline.md) e
[mapa da documentação](GUIA_DOCUMENTACAO.md).
