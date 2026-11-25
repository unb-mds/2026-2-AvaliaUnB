# Conferência do FigJam — issue #170

Referência de código: `cea8eced5b7f222ddd9d863a3a33c0d7a7fed560` da `main`,
conferida em 25/11/2026. Este roteiro prepara a revisão do
[board canônico](https://www.figma.com/board/PgqkPopVXOiSqm9gD5RRNv/AvaliaAi---Template-MDS?node-id=0-1).
Ele não comprova que os cartões do board foram alterados. A conferência visual
e a edição do FigJam continuam pendentes de uma conta com acesso ao board.

## Cartões a conferir e atualizar

| Área do board | Conteúdo de referência | Estado a representar |
|---|---|---|
| Tech stack | HTML, CSS, JavaScript e Jinja2; Python/Flask; PostgreSQL/Supabase; Supabase Auth com Google; scraper Python/Selenium separado; aplicação na Vercel e documentação no GitHub Pages | Implementado |
| Contexto | Visitante consulta catálogo, perfis, médias, comparação, ranking e comentários; conta Google participa; moderador autorizado trata denúncias e contestações | Implementado |
| Componentes | Navegador → rotas/templates Flask → controllers/validações → repositórios → Supabase; SIGAA → scraper → catálogo PostgreSQL | Implementado |
| Acesso | Apenas Google; perfil criado no primeiro acesso; retorno ao destino após autenticação | Implementado (#162, #199) |
| Explorar | Busca unificada e sugestões, filtros avançados, paginação e formulário sem JavaScript; nova busca limpa o filtro de nome anterior | Implementado (#220, #221, PR #276) |
| Consultar e avaliar | Médias por disciplina/semestre, evolução em gráfico/tabela e dificuldade; notas por turma cursada, com edição/exclusão no perfil | Implementado (#224, #252) |
| Comparar e favoritar | Dois ou mais professores; mesma disciplina ou seleção livre; destaques e ranking por departamento; favoritos no perfil pessoal | Implementado (#186, #218, #219, #222, #223) |
| Comentar | Publicar, editar e excluir; filtro automático; autoria privada, sem nome, e-mail, avatar ou rótulo público; sem confirmação adicional de e-mail | Implementado (#167, #214, #258, #260) |
| Reagir e ordenar | Curtir/descurtir, trocar/remover; totais inclusive zero; Mais recentes, Mais antigos, Mais curtidos e Mais reações | Implementado (#212, #213, #270) |
| Denunciar e moderar | Denúncia privada; área restrita; manter, ocultar ou restaurar com justificativa; contestação privada; sem fila de pré-aprovação | Implementado (#215, #216) |
| Retenção | Rotina para descartar registros de casos encerrados após 90 dias, preservando casos abertos e histórico de comentários ainda ocultados | Implementado no repositório (#217); execução no destino deve ser conferida |
| Identidade | Interface editorial, destaque verde, Inter/Inter Tight, temas escuro/claro, navegação móvel e favicon de chapéu com estrela | Implementado (#245, #263, #270) |
| Ofertas por semestre | Preservar histórico e priorizar semestre atual explicitamente configurado; selecionar outros períodos ou todos; médias independentes do filtro de oferta | Planejado (#242, #278, #279, #280) |

## Critérios para concluir a conferência visual

- [ ] Abrir o board com uma conta autorizada e conferir as áreas acima.
- [ ] Atualizar os cartões e suas ligações, com IMPLEMENTADO ou PLANEJADO.
- [ ] Retirar dos fluxos atuais cadastro por senha, SQLite, confirmação adicional
      de e-mail para comentar e identificação pública do autor.
- [ ] Identificar wireframes antigos como histórico; **Verificando** e **Em revisão**
      são estados de protótipo, sem fila de pré-aprovação na implementação atual.
- [ ] Conferir a apresentação em tela larga e estreita e os dois temas contra a
      interface, sem tratar protótipos como capturas do produto.
- [ ] Registrar na issue #170 a data, a pessoa responsável e links dos frames
      conferidos; só então marcar a conferência do FigJam como concluída.

Os SVGs em [Arquitetura](ARQUITETURA.md), o [inventário do frontend](FRONTEND.md)
e o [estado da interface](ESTADO_DA_INTERFACE.md) são as referências versionadas.
Após a revisão da equipe e o merge do PR #178, conferir a execução do workflow
de documentação e a página publicada antes de encerrar a issue.
