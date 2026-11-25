# Decisão de arquitetura: histórico de semestres

Issue [#242](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/242) · 23/11/2026

**Status:** opção C escolhida por Giovanna da Costa Santos (`giiicostaa`),
responsável pela issue. O [PR #269](https://github.com/unb-mds/2026-2-AvaliaUnB/pull/269)
foi integrado por `caiionog` em 24/11/2026. A confirmação coletiva ainda deve
ser registrada. Esta decisão não
é uma entrega de código nem comprova que o novo filtro já esteja em produção.

## Contexto e diagnóstico

O diagnóstico abaixo registra a base anterior à implementação das #278–#280.
Os PRs [#282](https://github.com/unb-mds/2026-2-AvaliaUnB/pull/282),
[#283](https://github.com/unb-mds/2026-2-AvaliaUnB/pull/283) e
[#284](https://github.com/unb-mds/2026-2-AvaliaUnB/pull/284) entregam, separadamente,
configuração explícita, filtro de ofertas e validação operacional. O
[guia de semestres](SEMESTRE_ATUAL.md) descreve a ativação; entregar o código não
confirma automaticamente o semestre de produção.

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
| A — histórico sem prioridade de oferta atual | Catálogo reúne todas as ofertas; preserva notas e períodos | Atende RF04/RF12, mas dificulta saber o que está disponível na matrícula |
| B — somente período atual | Substitui turmas passadas e compromete vínculos e comparações históricas | Rejeitada: risco de perda de dados e incompatibilidade com RF04/RF12 |
| C — híbrida | Conserva histórico e prioriza ofertas do semestre atual, com acesso aos anteriores | Escolhida: combina preservação e utilidade na matrícula |

## Política proposta

- A coleta de um novo semestre nunca apaga turmas, avaliações ou comentários anteriores.
- O semestre atual é o semestre acadêmico usado por padrão na consulta de ofertas, identificado por um par ano/período explicitamente confirmado após uma coleta completa e validada. O maior par encontrado no banco ou a data do calendário, isoladamente, não determina o semestre atual: uma coleta antecipada, parcial ou histórica não pode mudar o padrão.
- A busca e o catálogo exibem inicialmente ofertas do semestre atual; a pessoa pode escolher outro período ou todos. Perfis antigos continuam acessíveis por URL e pela consulta histórica; ausência de oferta atual não significa exclusão do professor.
- Avaliações continuam vinculadas à turma cursada, inclusive períodos antigos. Médias gerais, ranking e evolução mantêm o histórico; o recorte das médias por semestre segue explícito e independente do filtro de oferta.
- Comentários antigos continuam disponíveis segundo as regras de visibilidade e moderação. Comentários não possuem um semestre cursado; a data de publicação não será usada para inferi-lo ou ocultá-los automaticamente.
- Sem semestre atual configurado, o catálogo mantém o comportamento histórico atual e informa que o semestre atual ainda não foi definido. Um período sem ofertas exibe estado vazio, sem trocar silenciosamente a seleção.

## Riscos e limites

O crescimento do catálogo pede monitoramento de volume e desempenho, não expurgo
automático. Uma coleta incorreta ou vazia não deve ativar o período. O backup do
catálogo não inclui avaliações ou comentários e não substitui a política de backup
do banco. A ativação explícita evita confundir disponibilidade de oferta com o
semestre efetivamente cursado pelo aluno.

Não há migração, alteração de scraper, workflow ou interface nesta issue. Veja
os [impactos e tarefas](#tarefas-de-implementacao) para a entrega posterior.

## Tarefas de implementação

As tarefas abaixo foram abertas em 25/11/2026 como sub-issues vinculadas à #242.

| Tarefa | Escopo e critérios de aceite |
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
| Ratificação coletiva | Equipe AvaliaUnB | Pendente de confirmação explícita |
| Vínculos das novas issues | Giovanna (`giiicostaa`) | 25/11/2026 — #278, #279 e #280 |
