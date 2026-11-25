# Frontend

O AvaliaUnB usa Flask e templates Jinja2 em `app/templates/`, com HTML,
CSS e JavaScript em `app/static/`. Links e formulários funcionam no servidor;
não é necessário um build de frontend separado. Este inventário descreve a
`main` conferida em 25/11/2026. O [estado da interface](ESTADO_DA_INTERFACE.md)
separa o que está implementado das evoluções previstas nas issues.

## Páginas e recursos atuais

Todas as páginas usam `_tema.html`: `base.css`, `modelo-editorial.css`,
`integracao-editorial.css`, `tema.js` e favicon. A existência de uma folha
antiga em `static/` não significa que ela seja carregada pela página atual.

| Template | Conteúdo atual | Recursos adicionais ao tema compartilhado |
|---|---|---|
| `index.html` | Início, pesquisa e atalhos de navegação | Topo compartilhado |
| `login.html` | Entrar com Google, primeiro acesso e mensagem de erro | Topo compartilhado |
| `sobre.html` | Projeto, critérios e privacidade | Topo compartilhado |
| `privacidade.html` | Dados da conta, participação e privacidade dos comentários | Topo compartilhado |
| `lista_professores.html` | Busca única, filtro de departamento, cartões e paginação | `indicadores.css`, `campo-busca.js` |
| `perfil_professor.html` | Médias, semestre, gráfico/tabela de evolução, favoritos e comentários | `indicadores.css`, `evolucao.css`, `campo-busca.js` |
| `avaliacao.html` | Notas por cinco critérios; turma cursada; edição das próprias notas | `indicadores.css` |
| `editar_comentario.html` | Disciplina e texto preenchidos; Salvar e Cancelar | `indicadores.css` |
| `excluir_comentario.html` | Confirmação antes de excluir o próprio comentário | `indicadores.css` |
| `denunciar_comentario.html` | Motivo e explicação privada; confirmação de envio | `indicadores.css` |
| `moderacao.html` | Fila restrita de denúncias e contestações; decisões justificadas | Tema compartilhado |
| `contestar_comentario.html` | Contestação privada de decisão de moderação | Tema compartilhado |
| `perfil.html` | Conta, favoritos, Meus comentários e Minhas Avaliações | Topo compartilhado |
| `comparacao.html` | Mesma disciplina ou seleção livre entre disciplinas diferentes | `indicadores.css`, `campo-busca.js` |
| `ranking.html` | Classificação por média, quantidade e filtro de departamento | Tema compartilhado |

`verificar_email.html` e seu fluxo continuam no código, mas não são requisito
para comentar. O login com Google já é suficiente para participar.

## Identidade e navegação

O visual editorial usa fundo escuro por padrão, destaque verde e fontes locais
Inter e Inter Tight. O tema claro é opcional; `tema.js` restaura a preferência
do navegador. Os estilos compartilhados fazem a adaptação dos componentes
antigos `.botao`, `.campo`, `.card` aos atuais `.btn`, `.teacher` e `.review`.

O topo em `_topo.html` oferece **Início**, **Explorar**, **Ranking**,
**Comparar** e **Sobre**, além de alternância de tema e **Entrar** ou **Perfil**.
Quem está logado tem Sair. No celular, o botão de menu abre a navegação;
`editorial.js` controla esse comportamento. A aba atual recebe `aria-current`.
`_rodape.html` contém Sobre, Privacidade e feedback.

`_macros.html` reúne a marca, `icone_seta`, a formatação de nota com vírgula e
`barra_dificuldade`. O chapéu branco com estrela aparece no tema escuro; o
símbolo vetorial usa as cores do tema claro. O favicon de chapéu com estrela
sobre fundo transparente foi integrado na #263 / PR #264, sem mudar a logo
do cabeçalho.

## Fluxos e componentes

- **Busca:** campo único por professor, disciplina ou departamento, com
  sugestões acessíveis em `campo-busca.js`. Sem JavaScript, o formulário envia
  `q` na Consulta e `busca` na Comparação. Departamento é um refinamento opcional.
- **Cartões:** mostram disciplinas, código, quantidade e dificuldade média
  (`.disciplina-item`, `barra_dificuldade(valor, true)`, `.barra-hp-compacta`).
  Com até cinco disciplinas aparecem todas; acima disso, quatro e um
  `<details class="disciplinas-extras">` para as demais. A barra compacta é
  decorativa; o texto ao lado contém a informação para leitores de tela.
- **Notas:** cinco critérios; a média geral e o ranking excluem dificuldade.
  As estrelas usam `.estrelas` e `.preenche-N`. A turma cursada é escolhida ao
  avaliar; as médias podem ser filtradas por semestre e a evolução tem tabela
  alternativa ao gráfico SVG (`evolucao.css`).
- **Comparação:** dois ou mais professores distintos; na mesma disciplina,
  médias restritas à disciplina; no modo livre, médias gerais e aviso de
  disciplinas diferentes quando aplicável. A seleção permite adicionar/remover.
- **Comentários:** lista de até 50 por vez, mais recentes por padrão; opções
  Mais antigos, Mais curtidos e Mais reações; filtro independente por
  disciplina, texto escapado e data. Não há identificação pública, avatar ou
  rótulo substituto. Os formulários orientam a evitar dados pessoais no texto.
- **Ações próprias:** `_acoes_comentario.html` exibe Editar e Excluir juntos,
  em botões de contorno com área mínima de 44 px e foco visível. Também aparece
  em Meus comentários no perfil pessoal. Salvar ou cancelar retorna ao contexto
  de origem; excluir exige confirmação. Só o autor recebe essas ações.
- **Reações:** polegares em SVG com `currentColor`, contagens inclusive zero,
  `aria-pressed`, ícone preenchido na seleção, foco visível e alvo de 44 px.
  Os estilos ficam em `integracao-editorial.css` (`.review .comentario-reacoes`),
  pois `comentarios.css` não é carregado no perfil desde a interface editorial.
- **Denúncia:** conta autenticada pode denunciar comentário alheio; os dados
  do denunciante e a explicação não aparecem na listagem pública.
- **Favoritos:** lista privada no perfil, com adicionar/remover no professor.

## Implementação e planejamento dos comentários

Listar, publicar, editar, excluir, reagir (#212), ordenar (#213), filtrar
automaticamente o texto (#214), denunciar (#215), moderar/contestar (#216) e
reter os registros de moderação pelo prazo aprovado (#217) têm fluxos
implementados.
As [telas de comentários](TELAS_COMENTARIOS.md) são protótipos de planejamento;
não representam capturas fiéis da interface atual. Seus estados futuros
não devem ser confundidos com funcionalidades disponíveis.

## Estados, acessibilidade e segurança

As telas tratam lista vazia, erro de consulta, formulário inválido e ausência
de notas válidas (`N/A`). A falha em Meus comentários não bloqueia as demais
seções do perfil. As ações usam links/formulários com rótulos, foco por teclado,
mensagens com `role="alert"` quando pertinentes e CSRF em todos os POSTs.

A política de segurança em `app/seguranca.py` usa `style-src 'self'`; estilos
dinâmicos devem usar classes CSS, como `.preenche-N` e `.degrau-ativo`, em vez
de `style` inline. Nenhum vínculo de autoria deve ser exposto para identificar
ações do usuário. A [migração de privacidade](migrations/20261122155752_anonimato_comentarios.sql)
protege a leitura direta da Data API e precisa ser conferida no destino.

## Como contribuir com as telas

1. Confira a rota, o template e os recursos realmente carregados. Preserve os
   campos e parâmetros aceitos pelo backend e use `url_for`.
2. Reutilize o [design system](DESIGN_SYSTEM.md), os estilos e macros atuais;
   confira as outras páginas que compartilham a folha alterada.
3. Preserve CSRF, autoria da sessão, validações e proteção das rotas.
4. Confira notebook e celular, temas claro/escuro, foco por teclado, textos
   longos, filtros, estados vazios e erros.
5. Rode os testes pertinentes e `mkdocs build --strict`. Registre o que foi
   conferido no PR e diferencie proposta de funcionalidade implementada.

As regras detalhadas estão em [Funcionalidades](FUNCIONALIDADES.md),
[Comentários](COMENTARIOS.md), [Backend](BACKEND.md) e no
[mapa da documentação](GUIA_DOCUMENTACAO.md).
