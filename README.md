# 🎓 AvaliaUnb

> Consulta, comparação e avaliação de professores e disciplinas da Universidade de Brasília.

O AvaliaUnb reúne avaliações por critérios pedagógicos para ajudar estudantes a
escolher disciplinas e docentes durante a matrícula. É um projeto da disciplina
**Métodos de Desenvolvimento de Software (MDS/UnB), semestre 2026/2**.

**Comece por aqui:** [site](https://avaliaunb.com.br/) ·
[documentação oficial](https://unb-mds.github.io/2026-2-AvaliaUnB/) ·
[documento de visão](docs/DOCUMENTO_DE_VISAO.md) ·
[issues do projeto](https://github.com/unb-mds/2026-2-AvaliaUnB/issues)

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Funcionalidades e releases](#funcionalidades-e-releases)
- [Quem pode usar](#quem-pode-usar)
- [Tecnologias e arquitetura](#tecnologias-e-arquitetura)
- [Como executar](#como-executar)
- [Segurança e correções em andamento](#segurança-e-correções-em-andamento)
- [Documentação](#documentação)
- [Como contribuir](#como-contribuir)
- [Equipe](#equipe)

## Sobre o projeto

Informações sobre professores costumam ficar dispersas em grupos de mensagens,
o que dificulta comparar experiências na hora da matrícula. O AvaliaUnb organiza
a consulta por professor, disciplina e departamento, com notas de **didática,
clareza, organização, disponibilidade e dificuldade**.

O [documento de visão](docs/DOCUMENTO_DE_VISAO.md) apresenta o problema,
as personas, os requisitos e as metas de usabilidade, desempenho e segurança.

## Funcionalidades e releases

O planejamento e o estado da implementação são apresentados separadamente na
tabela. As entregas disponíveis consideram a versão da `main`; branches
anteriores podem conter apenas parte delas.

| Etapa | Funcionalidades | Estado |
|---|---|---|
| Consulta | Busca com sugestões, filtros avançados e paginação; perfis com médias por disciplina/semestre e evolução | Implementado (#220, #221, #224) |
| Avaliação | Cinco critérios por turma cursada; gestão das próprias avaliações | Implementado (#252) |
| Comparação e ranking | Comparação na mesma disciplina ou livre; ranking por departamento | Implementado (#186, #218, #219, #222) |
| Conta pessoal | Favoritos, avaliações e comentários próprios | Implementado (#223, #260) |
| Comentários | Publicação anônima, filtro de conteúdo, edição/exclusão, reações, ordenação e denúncias | Implementado (#212, #213, #214, #215, #258, #260) |
| Moderação e retenção | Decisões justificadas, contestação e descarte dos registros encerrados após 90 dias | Implementado (#216, #217) |
| Consulta ao catálogo | Consultar ofertas de todos os semestres coletados, sem filtro de semestre de oferta | Implementado; [modelo A (#242)](docs/DECISAO_HISTORICO_SEMESTRES.md) |

A consulta principal fica em `/professores`; ranking e comparação ficam em
`/ranking` e `/comparar`. A lista é ordenada pela quantidade de avaliações.
O ranking usa a média de quatro critérios, excluindo dificuldade, e exige
pelo menos cinco avaliações válidas.

Veja as [regras de busca, notas, comparação e ranking](docs/FUNCIONALIDADES.md).

## Quem pode usar

| Perfil | Acesso | O que pode fazer |
|---|---|---|
| Visitante | Sem login | Consultar professores, disciplinas, médias, ranking e comparação |
| Usuário cadastrado | Conta Google | Avaliar e gerenciar as próprias avaliações, comentar anonimamente, reagir, denunciar comentários alheios e gerenciar favoritos |

O público principal são os estudantes da UnB. Docentes também podem consultar
os indicadores públicos. A entrada é feita somente com a conta Google; a conta
no AvaliaUnb é criada automaticamente no primeiro acesso.

## Tecnologias e arquitetura

| Camada | Tecnologias |
|---|---|
| Interface | HTML5, CSS3, JavaScript e templates Jinja2 |
| Backend | Python, Flask e Blueprints |
| Persistência | PostgreSQL hospedado no Supabase |
| Contas e sessões | Supabase Auth |
| Coleta do SIGAA | Python e Selenium, com dependências próprias |
| Execução em contêiner | Docker Compose e Gunicorn |
| Documentação | MkDocs Material e GitHub Pages |
| Testes e qualidade | unittest, pip-audit e Bandit |
| Deploy | Configuração para Vercel adicionada no [PR #131](https://github.com/unb-mds/2026-2-AvaliaUnB/pull/131) |

### Backend

`run.py` cria a aplicação por `create_app`, em `app/__init__.py`.
As requisições passam por rotas, controllers e validações até os repositórios,
que acessam o Supabase. O scraper é executado separadamente e alimenta o catálogo.

O [guia do backend](docs/BACKEND.md) detalha a estrutura, as rotas, as sessões,
os repositórios e a integração com o [scraper](docs/COMO_USAR_SCRAPER.md).

### Dados

O banco contém `professores`, `disciplinas`, `turmas`, `perfis`,
`avaliacoes` e `comentarios`, além da view `vw_professor_disciplina`. A chave de professor
é nome e departamento; o departamento corresponde à unidade que oferece a
disciplina no SIGAA. Consulte o
[modelo de dados e a proposta de comentários](docs/Modelo%20de%20Dados.md).

### Frontend

As páginas são renderizadas no servidor a partir de `app/templates/`, com
recursos em `app/static/`. O design system e a aplicação do visual final estão
acompanhados nas issues
[#112](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/112) e
[#114](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/114).

O [guia do frontend](docs/FRONTEND.md) inventaria as telas, os estilos e os
estados existentes e explica como contribuir. O [design system](docs/DESIGN_SYSTEM.md)
registra cores, tipografia e componentes atuais.

## Como executar

### Ambiente local

Use Python 3.11 ou superior e execute:

```bash
git clone https://github.com/unb-mds/2026-2-AvaliaUnB.git
cd 2026-2-AvaliaUnB
python -m venv .venv
```

Ative o ambiente virtual com `.\.venv\Scripts\Activate.ps1` no PowerShell ou
`source .venv/bin/activate` no Linux/macOS. Depois instale as dependências:

```bash
pip install -r requirements.txt
```

Copie `.env.example` para `.env` na raiz e preencha:

| Variável | Uso |
|---|---|
| `SECRET_KEY` | Chave privada e estável para sessão Flask e CSRF. Obrigatória; em produção, pelo menos 32 caracteres e sem valores fracos. |
| `SUPABASE_URL` | URL do projeto Supabase. |
| `SUPABASE_SERVICE_KEY` | Chave de serviço, restrita ao servidor. |
| `FLASK_DEBUG` | Opcional; desligado por padrão. Use `1` somente no desenvolvimento local. |

Gere uma chave com `python -c "import secrets; print(secrets.token_hex(32))"`.
O `.env` é ignorado pelo Git; variáveis já definidas no ambiente têm prioridade.

Com o banco configurado, inicie o servidor:

```bash
python run.py
```

Acesse `http://127.0.0.1:5000`. O [guia do scraper](docs/COMO_USAR_SCRAPER.md)
cobre o preparo do banco e a coleta. O esquema inicial passou a incluir RLS
e políticas de acesso na [#123](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/123).

### Docker

Com Docker, Docker Compose e o `.env` configurados, execute:

```bash
docker compose up --build
```

A aplicação será servida pelo Gunicorn em `http://localhost:8000`.
O scraper é executado separadamente. A cada semestre, ele roda pelo workflow manual
*Atualizar dados do SIGAA* no GitHub Actions; veja o [guia do scraper](docs/COMO_USAR_SCRAPER.md).
As coletas acrescentam ofertas sem apagar o histórico. A decisão #242 mantém
o catálogo histórico completo, sem priorização do semestre atual. A regra das
avaliações por turma cursada permanece. Consulte o SIGAA para ofertas vigentes.

### Hospedagem

O endereço público informado pela equipe é [avaliaunb.com.br](https://avaliaunb.com.br/).
A configuração para Vercel está no [pyproject.toml](pyproject.toml), com entrada
`run:app`. O guia de hospedagem registra o que está disponível sobre cada ambiente.

As [instruções de hospedagem](docs/HOSPEDAGEM.md) detalham variáveis,
Preview, produção e a validação dos fluxos no ambiente publicado.

## Segurança e correções em andamento

- página pública de **Política de Privacidade e Termos de Uso** (`/privacidade`), acessível pelo rodapé, detalhando em linguagem simples os dados coletados (cadastro, avaliações e formulário de feedback), as regras contra ofensas e avaliações falsas e o canal de contato para solicitação de exclusão de dados (LGPD).

A versão da `main` inclui autenticação com Supabase Auth, proteção CSRF,
cookies de autenticação com `HttpOnly`, `SameSite=Lax` e `Secure` fora do debug,
headers de segurança e limites de requisições. A autorização de edição e
exclusão confere o autor da avaliação no backend.

A [auditoria de 02/11/2026](docs/AUDITORIA_SEGURANCA.md)
foi concluída na #111. O relatório registra um achado de prioridade alta,
três de prioridade média e oito de prioridade baixa, sem achados críticos.
O [PR #139](https://github.com/unb-mds/2026-2-AvaliaUnB/pull/139)
versionou RLS e políticas no esquema inicial. A aplicação ainda usa a chave
de serviço no servidor; a autorização depende do backend. A migração para a
chave pública foi adiada para depois do lançamento após a reversão do PR #141
no PR #157 por regressão em produção. As etapas adiadas são
[#124](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/124),
[#129](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/129) e
[#130](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/130).
A revogação de sessão no logout (#126) foi entregue; os ajustes de baixa
prioridade são acompanhados na #127.
O [resumo de cibersegurança](docs/CIBERSEGURANCA.md) relaciona os mecanismos do
código, a situação do RLS e os resultados da auditoria com cada correção.

Comentários e moderação têm uma [especificação](docs/COMENTARIOS.md),
baseada na #109, para revisão do grupo na
[#116](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/116).
Já estão implementados no perfil do professor (#167): listar os comentários
(mais recentes primeiro, 50 por vez), filtrar por disciplina, publicar, editar e
excluir o próprio comentário. A listagem não identifica o autor. Basta estar
logado para comentar, com limite de 10 comentários por hora por usuário.
Reações (#212), ordenação (#213), filtro automático (#214), denúncias (#215),
moderação (#216) e retenção (#217) estão implementadas. A política e a execução
das migrações ainda precisam ser conferidas no ambiente de destino. Consulte o
[estado da interface](docs/ESTADO_DA_INTERFACE.md) para o inventário atualizado.

## Documentação

| Assunto | Onde consultar |
|---|---|
| Início e instruções de execução | [Documentação do projeto](docs/index.md) · [Mapa e índice por assunto](docs/GUIA_DOCUMENTACAO.md) |
| Produto e requisitos | [Documento de visão](docs/DOCUMENTO_DE_VISAO.md) |
| Funcionalidades | [Busca, notas, comparação e ranking](docs/FUNCIONALIDADES.md) |
| Estado da interface | [Implementado e planejado](docs/ESTADO_DA_INTERFACE.md) |
| Backend | [Estrutura, rotas, sessões e repositórios](docs/BACKEND.md) |
| Frontend | [Templates, estilos, estados e contribuição](docs/FRONTEND.md) |
| Dados | [Modelo de dados](docs/Modelo%20de%20Dados.md) |
| Arquitetura | [Diagramas do sistema](docs/ARQUITETURA.md) |
| Coleta | [Guia do scraper](docs/COMO_USAR_SCRAPER.md) |
| Cibersegurança | [Mecanismos e correções](docs/CIBERSEGURANCA.md) · [Relatório da auditoria](docs/AUDITORIA_SEGURANCA.md) |
| Comentários | [Regras e implementação dos comentários](docs/COMENTARIOS.md) |
| Uso de IA | [Ferramentas por integrante e regras](docs/USO_DE_IA.md) · [Registro dos agentes](.agents/README.md) |
| Automação e checks | [Pipeline do GitHub Actions](docs/pipeline.md) · [DoR e DoD](docs/PROCESSO_CONTRIBUICAO.md) |
| Hospedagem | [Configuração de Preview, produção e lançamento](docs/HOSPEDAGEM.md) |
| Design | [Board do Figma](https://www.figma.com/board/PgqkPopVXOiSqm9gD5RRNv/AvaliaAi---Template-MDS?node-id=0-1) |
| Histórico | [Release 1](RELEASE-v1.0.0.md) · [v1.0.1](RELEASE-v1.0.1.md) · [v1.0.2](https://github.com/unb-mds/2026-2-AvaliaUnB/releases/tag/v1.0.2) · [v2.0.0](https://github.com/unb-mds/2026-2-AvaliaUnB/releases/tag/v2.0.0) |

Para abrir o site localmente, instale `mkdocs-material` no ambiente virtual e
execute `mkdocs serve` na raiz. Valide com `mkdocs build --strict`.
Na `main`, o workflow de documentação publica as mudanças em `docs/` ou
`mkdocs.yml` no GitHub Pages.

## Como contribuir

1. Escolha uma [issue](https://github.com/unb-mds/2026-2-AvaliaUnB/issues)
   e alinhe o escopo com os responsáveis.
2. Crie uma branch a partir da `main` atualizada para a mudança.
3. Use mensagens de commit que indiquem a alteração, como
   `docs: reorganiza o README` ou `fix: corrige filtro de professores`.
4. Para mudanças no código, execute `python -m unittest discover -s tests -t .`.
   A suíte usa um Supabase falso e dispensa credenciais reais e Chrome.
5. Para mudanças na documentação, confira os links e execute
   `mkdocs build --strict`.
6. Abra um pull request para a `main`, referenciando a issue, descrevendo a
   mudança e informando a validação realizada. Confira os checks antes do merge.

Consulte também os [critérios de contribuição](docs/PROCESSO_CONTRIBUICAO.md),
com o Definition of Ready e Definition of Done usados nos templates de issue e PR.

Consulte o [guia do backend](docs/BACKEND.md), os
[diagramas de arquitetura](docs/ARQUITETURA.md) e as
[regras de funcionalidades](docs/FUNCIONALIDADES.md) ao alterar o sistema.

## Equipe

Projeto desenvolvido no contexto da disciplina **Métodos de Desenvolvimento
de Software da Universidade de Brasília**, no semestre **2026/2**.

Resumo do que cada integrante fez, levantado das issues atribuídas e dos
commits na `main` até 25/11/2026. O detalhe completo está no
[histórico de contribuições](https://github.com/unb-mds/2026-2-AvaliaUnB/graphs/contributors)
e no [quadro de issues](https://github.com/unb-mds/2026-2-AvaliaUnB/issues).

| Integrante | Principais contribuições |
| --- | --- |
| Caio ([@caiionog](https://github.com/caiionog)) | Organização do backlog e das sprints, com a maior parte das issues e o modelo de tarefa com DoR e DoD. Controle de sessão e fluxo de autenticação no MVP; configuração do Supabase e primeira versão do scraper do SIGAA; login somente com Google (#162). Tabela de comentários (#166), backup público do banco (#165), barra de dificuldade (#193) e logo. Na Release 2: busca unificada com autocompletar (#220), correção de professores duplicados (#235), atualização semestral do SIGAA pelo GitHub Actions (#225), denúncia de comentários (#215), favoritos (#223), gráfico de evolução por semestre (#224), avaliação por turma cursada (#252) e aparência das reações (#270). |
| Geovana Duarte ([@Geovanaduartee](https://github.com/Geovanaduartee)) | Documentação de backend, frontend, cibersegurança e regras dos comentários (#116), revisão do README (#115) e design system com os protótipos de comentários (#112). Ranking e comparação de professores (#95, #186), revogação da sessão no logout (#126), verificação do e-mail antes de comentar (#189), nova interface editorial (#245), comentários anônimos para o público (#258) e ícone da aba (#263). |
| Giovanna da Costa Santos ([@giiicostaa](https://github.com/giiicostaa)) | Wireframe, story map e estrutura inicial da interface; integração do fluxo principal do MVP (#40), responsividade e testes de autenticação. Correções da auditoria de segurança (#127, #130), revisão e conexão dos documentos (#136, #171, #182), DoR e DoD do processo de contribuição. Reações 👍/👎 nos comentários (#212) e decisão sobre o histórico de semestres (#242). |
| [@gsm22](https://github.com/gsm22) | Consulta, filtros e modelo de professores e disciplinas no MVP, com testes da busca. Evolução do scraper: todas as unidades, paginação, modo `--dry-run` e persistência idempotente. Pipeline do GitHub Actions, GitHub Pages com MkDocs, auditoria de segurança e `CLAUDE.md`. Comentários no perfil do professor (#167), decisões C01–C11 (#211), filtro automático do texto (#214), ordenação dos comentários (#213) e nomes sem CAIXA ALTA (#236). |
| Luiz Guilherme de Alencar Magalhães ([@lgalencar25](https://github.com/lgalencar25)) | Documento de visão, diagramas C4 e de stack, persona 1 e MkDocs inicial. Modelos de usuário e avaliação e schema inicial do PostgreSQL; Docker e docker-compose (#85, #86). Recuperação de senha (#163), retorno à página de origem após o login (#199), comparação entre disciplinas diferentes com destaque do melhor professor (#218, #219), ranking por departamento (#222), releases v1.0.1 (#207) e atualização de links e do `CLAUDE.md` (#209, #210). |
| Miguel Cardoso ([@MiguelCardoso28](https://github.com/MiguelCardoso28)) | Jornada do usuário, página inicial responsiva e release notes da v1.0.0. Perfil do usuário com edição das próprias avaliações, navegação de retorno com filtros (#113) e leitura pública com chave anônima (#124). Página de política de privacidade e termos (#181), correção do "Comparar este professor" (#197), área de moderação com contestação (#216) e descarte de registros após 90 dias (#217). |
