# Arquitetura

Os diagramas representam a arquitetura implementada na `main`, conferida em
25/11/2026. O estado de cada fluxo e as evoluções planejadas estão no
[inventário da interface](ESTADO_DA_INTERFACE.md).

## Contexto

![Contexto do AvaliaUnB: consulta pública, participação autenticada e coleta do SIGAA](diagrama-contexto.svg)

Visitantes consultam catálogo, perfis, médias, ranking, comparação e comentários.
Com Google, estudantes avaliam turmas cursadas, comentam, reagem, denunciam e
gerenciam favoritos. O Supabase Auth mantém a sessão; o scraper busca ofertas no
SIGAA e grava o catálogo no PostgreSQL do Supabase.

## Componentes da aplicação

![Navegador, templates Jinja2, rotas Flask, controllers, repositórios e Supabase](diagrama-componentes.svg)

A aplicação renderiza HTML no servidor. Rotas delegam autenticação, validação,
consultas, avaliações, comentários e moderação aos controllers e repositórios.
A autoria dos comentários e as decisões de moderação permanecem privadas no
backend. O navegador não recebe a chave de serviço do Supabase.

## Tech stack

![Stack atual: Jinja2, HTML, CSS, JavaScript, Python, Flask, PostgreSQL, Supabase Auth e Selenium](tech-stack.svg)

Não há build de frontend separado. A aplicação web usa Python e Flask; os dados
e as contas usam Supabase/PostgreSQL e Supabase Auth. A coleta do SIGAA roda
separada da aplicação web, inclusive pelo workflow do GitHub Actions.

## Histórias confirmadas

| Atividade | História | Onde conferir |
|---|---|---|
| Explorar | Buscar por professor, disciplina ou departamento e abrir resultados | `/professores` |
| Consultar | Ver médias por disciplina/semestre e evolução em gráfico ou tabela | `/professores/<id>` |
| Comparar | Comparar professores na mesma disciplina ou em seleção livre | `/comparar` |
| Avaliar | Registrar notas para uma turma cursada e depois editar ou excluir | `/avaliar/<id>` e `/perfil` |
| Comentar | Publicar sem identificação pública e gerenciar os próprios relatos | Perfil do professor e `/perfil` |
| Moderar | Tratar denúncias e contestações com justificativa | `/moderacao` |
| Favoritar | Salvar professores numa lista pessoal e removê-los quando quiser | Perfil do professor e `/perfil` |

O catálogo conserva e consulta ofertas históricas sem filtro de semestre de
oferta. A [decisão #242](DECISAO_HISTORICO_SEMESTRES.md) mantém o modelo A,
isto é, a arquitetura atual, sem configuração de semestre atual ou alteração
do scraper. O semestre cursado permanece um dado da avaliação; as médias por
disciplina podem ser filtradas por semestre, enquanto as médias gerais, ranking
e evolução preservam o histórico. O catálogo não confirma ofertas vigentes.

## Histórico visual

Os PNGs antigos e wireframes são acervo de planejamento. Os diagramas SVG
acima são a referência atual versionada. O [FigJam do projeto](https://www.figma.com/board/PgqkPopVXOiSqm9gD5RRNv/AvaliaAi---Template-MDS?node-id=0-1)
acompanha o story map e as decisões; os estados futuros dos protótipos não
representam funcionalidades publicadas.

Para detalhes, consulte o [backend](BACKEND.md), o [frontend](FRONTEND.md),
o [modelo de dados](Modelo%20de%20Dados.md), o [guia do scraper](COMO_USAR_SCRAPER.md)
e o [mapa da documentação](GUIA_DOCUMENTACAO.md).
