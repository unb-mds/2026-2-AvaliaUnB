# Decisão de arquitetura: histórico de semestres

Issue [#242](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/242) · 23/11/2026

**Status:** opção C escolhida por Giovanna da Costa Santos (`giiicostaa`),
responsável pela issue, para revisão e ratificação da equipe no PR. A aprovação
coletiva e a data da ratificação ainda devem ser registradas. Esta decisão não
é uma entrega de código nem comprova que o novo filtro já esteja em produção.

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
| A — histórico sem prioridade de oferta atual | Catálogo reúne todas as ofertas; preserva notas e períodos | Atende RF04/RF12, mas dificulta saber o que está disponível na matrícula |
| B — somente período atual | Substitui turmas passadas e compromete vínculos e comparações históricas | Rejeitada: risco de perda de dados e incompatibilidade com RF04/RF12 |
| C — híbrida | Conserva histórico e prioriza ofertas do período ativo, com acesso aos anteriores | Escolhida: combina preservação e utilidade na matrícula |

## Política proposta

- A coleta de um novo semestre nunca apaga turmas, avaliações ou comentários anteriores.
- O período ativo é um par ano/período explicitamente confirmado após uma coleta completa e validada. O maior par encontrado no banco ou a data do calendário, isoladamente, não determina o período ativo: uma coleta antecipada, parcial ou histórica não pode mudar o padrão.
- A busca e o catálogo exibem inicialmente ofertas do período ativo; a pessoa pode escolher outro período ou todos. Perfis antigos continuam acessíveis por URL e pela consulta histórica; ausência de oferta atual não significa exclusão do professor.
- Avaliações continuam vinculadas à turma cursada, inclusive períodos antigos. Médias gerais, ranking e evolução mantêm o histórico; o recorte das médias por semestre segue explícito e independente do filtro de oferta.
- Comentários antigos continuam disponíveis segundo as regras de visibilidade e moderação. Comentários não possuem um semestre cursado; a data de publicação não será usada para inferi-lo ou ocultá-los automaticamente.
- Sem período ativo configurado, o catálogo mantém o comportamento histórico atual e informa que o período ainda não foi definido. Um período sem ofertas exibe estado vazio, sem trocar silenciosamente a seleção.

## Riscos e limites

O crescimento do catálogo pede monitoramento de volume e desempenho, não expurgo
automático. Uma coleta incorreta ou vazia não deve ativar o período. O backup do
catálogo não inclui avaliações ou comentários e não substitui a política de backup
do banco. A ativação explícita evita confundir disponibilidade de oferta com o
semestre efetivamente cursado pelo aluno.

Não há migração, alteração de scraper, workflow ou interface nesta issue. Veja
os [impactos e tarefas](#tarefas-de-implementacao) para a entrega posterior.

## Tarefas de implementação

As tarefas abaixo são propostas para abertura e vinculação à #242 depois da
ratificação. Não são issues já publicadas.

| Tarefa | Escopo e critérios de aceite |
|---|---|
| Configurar período de oferta ativo | Persistir e consultar par válido; ativar somente após validação da coleta; reimportação e coleta histórica não alteram o ativo; ausência de configuração mantém consulta histórica |
| Filtrar catálogo por período de oferta | Padrão ativo, seleção de um período ou todos; busca, sugestões e disciplinas coerentes; URL preserva seleção; estados vazios e perfis históricos acessíveis |
| Integrar coleta e validação de período | Manter upsert e histórico; registrar confirmação do período; testar repetição, coleta parcial, falha, reimportação e preservação de notas/comentários; atualizar guia operacional |

As issues [#225](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/225),
[#252](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/252) e
[#224](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/224) já foram encerradas e
não precisam ser recriadas. A decisão conserva essas entregas.

## Registro de revisão

| Etapa | Responsável | Data / situação |
|---|---|---|
| Proposta e escolha da alternativa C | Giovanna (`giiicostaa`) | 23/11/2026 |
| Ratificação coletiva | Equipe AvaliaUnB | Pendente de confirmação no PR |
| Vínculos das novas issues | Equipe / responsável pela #242 | Pendentes de publicação |
