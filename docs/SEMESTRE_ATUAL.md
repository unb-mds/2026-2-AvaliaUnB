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
