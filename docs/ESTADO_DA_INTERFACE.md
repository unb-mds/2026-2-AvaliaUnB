# Estado da interface e evoluções planejadas

Revisão de **22/11/2026**, issue #170. Base de código conferida:
`59ff7442eabf86348dcc27365b8c5ed05d83f7e8` da `main`. Esta página separa o
comportamento implementado do planejamento. Issue aberta ou teste aprovado
isoladamente não comprova entrega no site; migrações e publicação precisam ser
conferidas no ambiente de destino. O objetivo desta revisão é documentar,
sem implementar as funcionalidades pendentes.

## Implementado na main

| Jornada | Comportamento conferido | Referências |
|---|---|---|
| Acessar | Consulta pública; entrada só com Google; perfil criado no primeiro acesso; sair da sessão | #162, #199 |
| Explorar | Busca única por professor, disciplina ou departamento, com sugestões e envio sem JavaScript; filtro opcional de departamento; catálogo paginado | #220 |
| Consultar professor | Disciplinas, médias, volume de avaliações, dificuldade, filtro de semestre e evolução por semestre em gráfico/tabela | #201, #224, #252 |
| Avaliar | Cinco critérios, escolha da turma cursada; uma avaliação por conta, professor, disciplina e semestre; editar/excluir pelo perfil | #252 |
| Comparar | Dois ou mais professores: mesma disciplina (médias daquela disciplina) ou seleção livre entre disciplinas diferentes (médias gerais); destaque de desempenho | #186, #218, #219 |
| Ranking | Média de quatro critérios, sem dificuldade; mínimo de cinco avaliações válidas e filtro de departamento | #222 |
| Favoritar | Adicionar/remover professores na lista pessoal, acessível no perfil | #223 |
| Comentar | Texto de 2 a 1.000 caracteres, disciplina obrigatória, limite de dez publicações/hora; lista dos 50 mais recentes e filtro por disciplina | #167 |
| Gerenciar comentário | Editar e Excluir juntos no próprio comentário; Meus comentários no perfil pessoal; acesso somente ao autor | #260, PR #261 |
| Privacidade | Sem nome, e-mail, avatar ou rótulo acima do comentário; autoria privada preservada. Leitura direta da Data API depende da migração de privacidade | #258, PR #259 |
| Denunciar | Conta autenticada denuncia comentário alheio; motivo obrigatório e envio privado; sem ocultação automática por quantidade de denúncias | #215 |
| Interface | Tema escuro padrão e claro opcional, Inter/Inter Tight, destaque verde, chapéu com estrela, menu de celular, Sobre, Entrar e Privacidade | #245 |

## Planejado ou em revisão

| Evolução | Resultado esperado | Issue / proposta em revisão |
|---|---|---|
| Like e dislike | Ícones de polegar em contorno; uma reação por conta, com troca/remoção; contagens sem identificação de quem reagiu; sem voto no próprio comentário | #212 |
| Ordenação dos comentários | Mais recentes, mais antigos, mais curtidos e mais reações; opções por reação dependem da #212 | #213 |
| Filtro automático | Validar texto ao publicar/editar e bloquear violações claras conforme C10; não confundir validação de tamanho existente com moderação de conteúdo | #214, PR #262 |
| Moderação | Área restrita para decidir sobre denúncias e receber contestações, com justificativa; editar texto ocultado não o republica automaticamente | #216, PR #255 |
| Retenção | Descartar registros encerrados após o prazo aprovado, preservando casos abertos e comentários; revisar implementação antes de ativar rotina | #217, PR #256 |
| Filtros avançados | Faixa de nota e quantidade de avaliações no catálogo | #221 |
| Grafia dos nomes | Converter nomes em caixa alta para apresentação comum, com revisão da transformação | #236, PR #265 |
| Ícone da aba | Chapéu e estrela com fundo transparente; atualização do recurso para evitar o cache antigo | #263, PR #264 |

## Decisões que não devem ser reintroduzidas

- Comentários não expõem nome de usuário ou e-mail, inclusive por clique.
- Comentar exige login com Google; não exige confirmação adicional de e-mail.
- Avaliações por estrelas são independentes dos comentários e incluem o semestre.
- A comparação também admite professores de disciplinas diferentes.
- PostgreSQL/Supabase é a persistência atual; SQLite e planilhas não descrevem a arquitetura de execução atual.
- As telas e desenhos de like/dislike e moderação são planejamento, até a entrega correspondente.

## Revisão no FigJam

O [board do projeto](https://www.figma.com/board/PgqkPopVXOiSqm9gD5RRNv/AvaliaAi---Template-MDS?node-id=0-1)
reúne o contexto, os componentes, a stack e o story map. Cartões com
**IMPLEMENTADO** representam o código conferido; **PLANEJADO** aponta para a
issue correspondente. Wireframes e matrizes históricas registram exploração,
não servem como captura da interface publicada. Para nomes de páginas, temas,
estilos e permissões, use o [inventário do frontend](FRONTEND.md), as
[funcionalidades](FUNCIONALIDADES.md) e a [especificação de comentários](COMENTARIOS.md).
