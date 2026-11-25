# Decisão de arquitetura: histórico de semestres

Issue [#242](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/242) · 23/11/2026

**Status:** opção A — manutenção do histórico completo, escolhida pela
responsável Giovanna da Costa Santos (`giiicostaa`) em 25/11/2026 para revisão
da equipe. A proposta anterior (opção C) consta dos PRs #269 e #281; foi
reconsiderada antes de integração de código na `main`. A manutenção do modelo A não exige
alteração no banco, scraper, workflow ou interface. A ratificação coletiva
da nova escolha depende da revisão do PR.

## Contexto e diagnóstico

O workflow da #225 coleta um par de ano e período por execução; a persistência
reaproveita professores e disciplinas e faz upsert de turmas por professor,
disciplina, ano e período. O catálogo e os backups preservam os períodos anteriores.
A consulta de ofertas ainda reúne as disciplinas históricas. Desde a #252, a
avaliação já é por semestre cursado (migração 007), com filtro nas médias da
disciplina. A #224 entregou a evolução de notas por semestre. Portanto, a descrição
original da #242 sobre uma avaliação por par e ausência de qualquer filtro de
semestre foi superada por essas entregas.

## Alternativas

| Alternativa | Consequência | Avaliação |
|---|---|---|
| A — histórico sem prioridade de oferta atual | Catálogo reúne todas as ofertas; preserva notas e períodos | Escolhida: atende RF04/RF12 e mantém o funcionamento atual sem risco de regressão de um novo filtro |
| B — somente período atual | Substitui turmas passadas e compromete vínculos e comparações históricas | Rejeitada: risco de perda de dados e incompatibilidade com RF04/RF12 |
| C — híbrida | Conserva histórico e prioriza ofertas do semestre atual, com acesso aos anteriores | Proposta anterior, não adotada: exige configuração, filtro de catálogo e integração operacional |

## Política de manutenção do modelo A

- A coleta de um novo semestre nunca apaga turmas, avaliações ou comentários anteriores.
- A busca e o catálogo consultam todas as ofertas históricas, sem configuração de semestre atual, seletor de semestre de oferta ou priorização automática de ofertas recentes. Professores sem oferta no semestre corrente continuam consultáveis.
- Avaliações continuam vinculadas à turma cursada, inclusive períodos antigos. Médias gerais, ranking e evolução mantêm o histórico; o filtro de semestre das médias continua disponível como já implementado na #252.
- Comentários antigos continuam disponíveis segundo as regras de visibilidade e moderação. Comentários não possuem um semestre cursado; a data de publicação não será usada para inferi-lo ou ocultá-los automaticamente.
- A coleta permanece cumulativa: reimportar ofertas de um semestre não elimina dados dos demais semestres. Não há mecanismo de ativação de um período.

## Riscos e limites

O crescimento do catálogo pede monitoramento de volume e desempenho, não expurgo
automático. O catálogo é histórico e não comprova disponibilidade para matrícula
no semestre corrente; o SIGAA é a referência para ofertas vigentes. O backup do
catálogo não inclui avaliações ou comentários e não substitui a política de backup
do banco. A preservação evita perder o contexto do semestre cursado pelo aluno.

Não há migração, alteração de scraper, workflow ou interface nesta issue. As
entregas existentes já atendem ao modelo A; não há novas tarefas de implementação.

## Tarefas de implementação

As tarefas abaixo foram abertas em 25/11/2026 para a opção C e encerradas na
mesma data como `Not planned`, pois deixaram de ser necessárias no modelo A.
Os PRs [#282](https://github.com/unb-mds/2026-2-AvaliaUnB/pull/282),
[#283](https://github.com/unb-mds/2026-2-AvaliaUnB/pull/283) e
[#284](https://github.com/unb-mds/2026-2-AvaliaUnB/pull/284), de
`Geovanaduartee`, foram fechados sem merge. O histórico das contribuições
permanece disponível; nenhum desses PRs foi integrado à `main`.

| Tarefa | Escopo anterior (opção C) |
|---|---|
| [#278 — Configurar semestre atual](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/278) | Persistir e consultar par válido; ativar somente após validação da coleta; reimportação e coleta histórica não alteram o semestre atual; ausência de configuração mantém consulta histórica |
| [#279 — Filtrar catálogo por semestre](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/279) | Semestre atual por padrão, seleção de um período ou todos; busca, sugestões e disciplinas coerentes; URL preserva seleção; estados vazios e perfis históricos acessíveis |
| [#280 — Integrar coleta e validação do semestre atual](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/280) | Manter upsert e histórico; registrar confirmação do semestre atual; testar repetição, coleta parcial, falha, reimportação e preservação de notas/comentários; atualizar guia operacional |

As issues [#225](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/225),
[#252](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/252) e
[#224](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/224) já foram encerradas e
não precisam ser recriadas. A decisão conserva essas entregas.

## Registro de revisão

| Etapa | Responsável | Data / situação |
|---|---|---|
| Proposta e escolha da alternativa C | Giovanna (`giiicostaa`) | 23/11/2026 |
| Integração do PR #269 | `caiionog` | 24/11/2026 |
| Opção C e padronização anteriores | Giovanna (`giiicostaa`) | PRs #269 e #281; decisão reconsiderada |
| Vínculos das novas issues | Giovanna (`giiicostaa`) | 25/11/2026 — #278, #279 e #280 |
| Escolha de manter o modelo A | Giovanna (`giiicostaa`) | 25/11/2026 — sem mudança de código |
| Ratificação coletiva do modelo A | Equipe AvaliaUnB | Pendente de revisão do PR |
| Encaminhamento das sub-issues | Giovanna (`giiicostaa`) | 25/11/2026 — #278, #279 e #280 canceladas; PRs #282, #283 e #284 fechados sem merge |
| Atualização da issue #242 | Giovanna (`giiicostaa`) | 25/11/2026 — decisão revisada e registro das pendências atualizado |
