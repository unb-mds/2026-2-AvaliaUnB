# Semestre atual e consulta histórica

## Configuração explícita (#278)

`config/semestre_atual.json` persiste o semestre de oferta usado por padrão.
É um arquivo versionado: sua ativação passa por PR e deploy, com rastreabilidade
e reversão pelo Git, sem alterar as tabelas ou apagar dados no Supabase.

O estado inicial é `{"semestre_atual": null}`. Sem definição, com arquivo ausente
ou configuração inválida, o site mantém a consulta histórica. Um ano de quatro
dígitos e um período inteiro entre 1 e 4 são válidos, como no SIGAA. O semestre
atual nunca é deduzido da data do calendário nem do maior par no banco.

Após uma coleta completa e validada, a confirmação operacional produz:

```json
{
  "semestre_atual": {"ano": 2026, "periodo": 2}
}
```

O exemplo não ativa esse semestre. A confirmação da equipe, a validação da coleta
e o merge do arquivo são necessários. O app pode usar outro caminho via configuração
Flask `SEMESTRE_ATUAL_ARQUIVO` (útil em testes); o padrão é o arquivo versionado.

Alterar esta configuração não modifica o semestre cursado das avaliações,
médias, ranking, evolução, comentários ou ofertas históricas. A coleta continua
cumulativa. A decisão está em [Histórico de semestres](DECISAO_HISTORICO_SEMESTRES.md).

## Filtro de ofertas (#279)

A Consulta aceita `oferta=2026-2` (formato `AAAA-P`) e `oferta=todos`. Sem parâmetro,
usa o semestre atual confirmado; sem configuração, usa o histórico completo e
informa que o semestre atual ainda não foi definido. Período válido sem ofertas
mostra estado vazio e conserva a seleção; formato inválido retorna HTTP 400.

O recorte é aplicado antes da busca e paginação. Sugestões, departamentos e
disciplinas dos cartões usam o mesmo recorte. Os links de paginação e o retorno
do perfil preservam a escolha. A comparação, o ranking e os perfis históricos
continuam acessíveis e suas médias não são alteradas pelo filtro de oferta.
O seletor funciona com GET, inclusive sem JavaScript.

## Coleta e confirmação operacional (#280)

O scraper aceita `--relatorio coleta.json` e `--finalidade regular|historica|antecipada`.
O relatório registra todas as unidades de graduação esperadas, o resultado de cada
uma, linhas puladas, vínculos e assinatura das turmas. O dry-run gera evidência de
leitura sem consultar ou gravar o Supabase, mas nunca permite ativar o semestre.

No modo de gravação, uma leitura posterior verifica se todos os professores,
disciplinas e turmas coletados existem com os vínculos corretos no banco. Unidades
sem turmas são válidas; uma coleta inteiramente vazia não confirma um semestre.
Linhas puladas por erro impedem a confirmação. Docentes ainda "A DEFINIR" são
contabilizados e ignorados conforme a regra existente do catálogo.
Antes da primeira escrita, o workflow exporta o catálogo para `backup-antes/`,
preservado no artifact da execução; avaliações, comentários e contas não são
exportados nem modificados por essa rotina.

O workflow **Atualizar dados do SIGAA** tem dois novos campos:

- `finalidade`: regular, histórica ou antecipada. Histórica/antecipada nunca
  alteram o semestre atual.
- `confirmar_semestre`: vazio por padrão. Para propor uma ativação, digitar o par
  exato, como `2026-2`, usar modo **gravar**, todas as unidades e finalidade regular.

Após cobertura completa, integridade, persistência e duplicatas verificadas, o
workflow executa `python -m scraper.confirmar_semestre coleta.json --confirmar 2026-2 --gravar`.
Ele gera a configuração para revisão no PR de dados e backup. O semestre só muda
no site após o merge e deploy desse arquivo. Uma coleta parcial, vazia, falha,
histórica, antecipada, somente simulada ou com período divergente não o modifica.
Reimportar período anterior ao já confirmado também não regride a configuração.

Antes de mesclar o PR de ativação, conferir o artifact `scraper-log/coleta.json`,
os totais, o link da execução gravado na configuração e o diff do backup. A
configuração é reversível pelo Git; um rollback para `semestre_atual: null` volta
à consulta de todos os semestres, sem apagar registros do banco.

## Evidência inicial de 2026/2

O [dry-run completo de 25/11/2026](https://github.com/unb-mds/2026-2-AvaliaUnB/actions/runs/45622575991)
processou 99 unidades de graduação: 69 com turmas e 30 sem turmas, sem unidade
ou linha pulada por erro. Foram extraídos 2.843 professores, 3.468 disciplinas
e 6.889 vínculos únicos de turma. Os 112 registros de docente "A DEFINIR" foram
contabilizados e ignorados conforme a regra existente. Essa execução não gravou
dados e não comprova, sozinha, que todos os vínculos já estão no banco publicado;
a ativação exige a verificação de persistência descrita acima.

A [execução com gravação e conferência](https://github.com/unb-mds/2026-2-AvaliaUnB/actions/runs/45626854707)
foi concluída em 25/11/2026, com backup prévio, 99 unidades, zero unidade/linha
pulada por erro e 6.888 vínculos únicos verificados no banco. O relatório registrou
2.842 professores e 3.467 disciplinas nessa coleta. O SIGAA é uma fonte mutável;
os totais acima são de execuções distintas, e a persistência cumulativa não remove
os vínculos anteriores que deixem de aparecer em uma coleta posterior.

O arquivo proposto para 2026/2 inclui o link dessa execução, os totais e a assinatura
das turmas. A configuração e o backup foram incorporados ao PR #284 para revisão
junto à tarefa #280. A ativação no site ainda depende da integração e do deploy.
