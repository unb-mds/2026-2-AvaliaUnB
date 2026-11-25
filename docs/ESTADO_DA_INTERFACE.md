# Estado da interface e evoluções planejadas

Revisão de **25/11/2026**, issue #170. Base de código conferida: commit
`cea8eced5b7f222ddd9d863a3a33c0d7a7fed560` da `main`. Esta página resume o
comportamento implementado no repositório e separa propostas ainda não
entregues. A presença de uma migração no Git não comprova sua aplicação no
Supabase publicado.

## Implementado na main

| Jornada | Comportamento conferido | Referências |
|---|---|---|
| Acessar | Consulta pública; autenticação apenas com Google; sessão e perfil no primeiro acesso | #162, #199 |
| Explorar | Busca por professor, disciplina ou departamento, com sugestões, alternativa sem JavaScript, paginação e filtros avançados de nota e volume | #220, #221 |
| Consultar | Médias por disciplina e semestre, dificuldade e evolução em gráfico ou tabela; nomes em grafia comum | #224, #236, #252 |
| Avaliar | Cinco critérios e seleção da turma cursada; uma avaliação por conta, professor, disciplina e semestre; editar/excluir no perfil | #252 |
| Comparar | Dois ou mais professores, na mesma disciplina ou em seleção livre, com médias no recorte adequado e destaques | #186, #218, #219 |
| Ranking | Média de quatro critérios, mínimo de cinco avaliações válidas e filtro de departamento | #222 |
| Favoritar | Adicionar e remover professores numa lista pessoal | #223 |
| Comentar | Publicação autenticada, texto validado e filtrado, disciplina obrigatória, limite de dez por hora; listagem anônima com filtro por disciplina | #167, #214, #258 |
| Gerenciar comentários | Editar/excluir próprios relatos, consultar Meus comentários e escolher a ordem da lista | #213, #260, PR #261, PR #268 |
| Reagir | Curtir ou descurtir comentário, trocar/remover reação; contagens sem expor autoria | #212, #267, #270 |
| Denunciar e moderar | Denúncia privada, fila restrita, decisões justificadas, ocultação/restauração e contestação | #215, #216 |
| Retenção | Descarte automático dos registros de moderação encerrados após 90 dias, preservando casos abertos e comentários | #217, #256 |
| Interface | Tema escuro/claro, identidade editorial, navegação móvel, Sobre e Política de Privacidade e Termos | #245, #258, #270 |

## Planejado

| Evolução | Situação | Referência |
|---|---|---|
| Consulta priorizando ofertas do semestre atual | Decisão híbrida registrada; configuração, filtro e integração da coleta ainda são futuros; o catálogo consulta o histórico completo | #242, #278, #279, #280 |
| Publicação e aplicação da política de retenção no ambiente | Conferir configuração e execução no destino; a documentação do workflow não comprova implantação | #217 |

## Decisões vigentes

- Comentários públicos não exibem nome, e-mail, avatar ou rótulo identificador; a autoria permanece privada para as permissões do backend.
- Comentar exige login com Google, sem confirmação adicional de e-mail.
- Avaliações por estrelas e comentários são independentes; a avaliação registra o semestre cursado.
- Comparação suporta professores da mesma disciplina e seleção livre entre disciplinas diferentes.
- PostgreSQL/Supabase é a persistência atual; o scraper do SIGAA alimenta o catálogo fora das requisições web.
- Migrações versionadas precisam ser conferidas no ambiente antes de afirmar que o banco publicado está atualizado.

## FigJam e referências

O [board do projeto](https://www.figma.com/board/PgqkPopVXOiSqm9gD5RRNv/AvaliaAi---Template-MDS?node-id=0-1)
reúne contexto, componentes, stack e story map. Seus estados devem acompanhar
esta lista: entregas concluídas como **IMPLEMENTADO** e evoluções futuras como
**PLANEJADO**. Wireframes são protótipos, não capturas da interface publicada.
Consulte também o [inventário do frontend](FRONTEND.md), as
[funcionalidades](FUNCIONALIDADES.md) e a [especificação de comentários](COMENTARIOS.md).

O [roteiro de conferência do FigJam](REVISAO_FIGJAM.md) lista os cartões,
estados e evidências necessários. A revisão visual do board ainda não foi
concluída; o roteiro não substitui a edição e a conferência por uma conta autorizada.
