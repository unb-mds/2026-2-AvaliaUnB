# Design system

Referência da interface editorial atual do AvaliaUnB, conferida em 24/11/2026
na revisão da #170. Os protótipos antigos da #112 são histórico de exploração;
a paleta azul e a home “Bem-vindo” não descrevem a interface atual. O
[inventário do frontend](FRONTEND.md) lista os recursos realmente carregados,
e o [estado da interface](ESTADO_DA_INTERFACE.md) separa entregas e planejamento.

## Fontes de verdade e ordem dos estilos

O parcial `_tema.html` carrega `base.css`, `modelo-editorial.css` e
`integracao-editorial.css`, nessa ordem. O primeiro mantém fontes locais,
tokens e componentes compartilhados. O modelo define a paleta editorial e
os componentes visuais. A integração adapta as classes anteriores ao modelo
e define ajustes de navegação, formulários, comentários e responsividade.

Ao alterar uma tela, considere a cascata completa: um valor antigo de
`base.css` pode estar substituído pelo modelo ou pela integração.
`indicadores.css` e `evolucao.css` complementam as telas que os incluem.
Arquivos antigos presentes em `static/` não são automaticamente parte do tema.

## Temas

O escuro é o padrão. O claro usa `data-theme="light"` em `<html>`.
`tema.js`, carregado no `<head>` sem `defer`, restaura a preferência antes da
página aparecer. A chave `tema` do `localStorage` guarda `claro` ou `escuro`;
o acesso é protegido por `try/catch`. Sem preferência, vale o escuro, sem seguir
automaticamente o tema do sistema. Se o armazenamento falhar, a escolha vale
para a página aberta.

O botão `#themeBtn` é centralizado, tem ícones decorativos de sol/lua,
`aria-label` e `aria-pressed`. O CSS usa `color-scheme` nos dois temas para os
controles nativos. Todo template de página completa inclui `_tema.html`.

## Cores

Valores editoriais definidos em `modelo-editorial.css`:

| Token | Escuro | Claro | Uso |
|---|---|---|---|
| `--bg` | `#050505` | `#f6f7f2` | Fundo da página |
| `--panel` | `#111211` | `#ffffff` | Campos e painéis |
| `--card` | `#151615` | `#ffffff` | Cartões |
| `--wash` | `#1c1d1b` | `#ecf0e8` | Superfície suave |
| `--line` | `#292b28` | `#dfe4d9` | Divisores e bordas |
| `--text` | `#f4f5f0` | `#1a2119` | Texto principal |
| `--muted` | `#a1a69d` | `#647062` | Texto secundário |
| `--accent` | `#b2ff80` | `#3f842e` | Destaque e ação principal |
| `--dark-on-accent` | `#10130b` | `#ffffff` | Texto sobre destaque |

A integração conecta os tokens anteriores aos editoriais: por exemplo,
`--cor-texto` aponta para `--text`, `--cor-principal` para `--accent`,
`--cor-divisor` para `--line` e `--cor-sobre-principal` para
`--dark-on-accent`. Reutilize esses tokens nos componentes, em vez de copiar
cores fixas para cada página. Estrelas e estados semânticos mantêm seus tokens
próprios; verde não deve substituir indiscriminadamente erros ou avisos.

## Tipografia e composição

Inter e Inter Tight são hospedadas em `static/fonts/`, com `@font-face` em
`base.css`. Inter é a fonte do conteúdo e controles. Inter Tight aparece na
marca e nos títulos editoriais. Use as pilhas de fallback existentes.

O contêiner `.shell` centraliza o conteúdo e limita a largura; títulos usam
tamanho responsivo com `clamp`. Cartões, painéis e botões têm bordas discretas
e cantos arredondados. Reutilize as classes da composição atual antes de criar
novos raios, espaçamentos e tamanhos.

## Identidade e navegação

A marca do cabeçalho e do login vem das macros `logo` e `simbolo_logo`:
chapéu branco com estrela dourada no tema escuro e símbolo vetorial adaptado
ao tema claro. A seta de navegação é texto com apresentação tipográfica,
pela macro `icone_seta`, para manter a forma no celular e no notebook.

O favicon é um recurso separado em `static/favicon.svg`; a substituição pelo
chapéu com estrela sobre fundo transparente está na #263 / PR #264. Não tratar
um recurso pendente de publicação como confirmação de atualização no navegador.

O topo apresenta Início, Explorar, Ranking, Comparar e Sobre. A conta aparece
como Entrar ou Perfil. No celular, o menu é aberto pelo botão de navegação;
ele não é uma segunda linha de abas com rolagem. `_rodape.html` reúne os links
complementares. A aba ativa usa `aria-current`.

## Componentes e estados

| Componente | Padrão atual |
|---|---|
| Botão principal | `.btn` ou `.botao-primario`, destaque verde e texto de contraste |
| Ação secundária | `.btn.ghost` ou `.botao-secundario`, fundo transparente e contorno |
| Ação destrutiva | Excluir exige confirmação; cancelar não altera o registro |
| Campo | Rótulo associado, ajuda, valor preservado e erro junto ao campo |
| Busca | Campo único e sugestões; envio por formulário funciona sem JavaScript |
| Cartão de professor | Nome, departamento, disciplinas, notas, dificuldade e ações |
| Comentário | Texto, disciplina, data e ações permitidas; sem identificação pública ou rótulo substituto |
| Editar / Excluir | Juntos, em contorno, área de toque de 44 px e foco visível; apenas para o autor |
| Perfil pessoal | Conta, Favoritos, Meus comentários e Minhas Avaliações |
| Evolução | Gráfico SVG por semestre e tabela alternativa; mensagem com um só semestre ou sem dados |
| Mensagem | Diferencia resultado vazio, erro, ausência de notas e validação do formulário |
| Reação (#212, estilo #270) | Polegares com contagens, troca/remoção e sem voto no próprio comentário; seleção indicada por ícone preenchido e `aria-pressed` |

## Barra de dificuldade

A leitura atual usa a macro `barra_dificuldade(valor, compacta=false)` e as
classes `.barra-hp`, `.barra-hp-trilho`, `.barra-hp-cheia`, `.preenche-N` e
`.nivel-N`. A largura representa o valor entre 1 e 5, com escala e nome
acessível; não corresponde ao antigo desenho de degraus crescentes.

Na Consulta, `.barra-hp-compacta` é decorativa (`aria-hidden="true"`), pois o
texto ao lado informa a dificuldade. Valor ausente não cria nota artificial.
No formulário, a seleção mantém os rádios de 1 a 5 e seus rótulos; o valor
enviado ao backend continua inteiro. A dificuldade fica fora da média geral.

## Home, movimento e acessibilidade

A home usa o título “Seu próximo semestre começa com boas escolhas”, pesquisa,
chapéu decorativo e atalhos editoriais para explorar/comparar, com destaques
de professores quando existem dados. O título não é o antigo “Bem-vindo”.
O formulário atual envia `nome` para a Consulta; a busca unificada completa
fica na página Explorar.

`editorial.js` controla menu, progresso de leitura e posição do brilho em
áreas decorativas. O tratamento de movimento reduzido e a interação por
ponteiro devem ser preservados. O antigo canvas `fundo-animado.js` não é
carregado pela home atual; não o adicionar por seguir desenhos históricos.

Mantenha foco por teclado, rótulos dos controles, texto alternativo quando
necessário e estados com mensagem, sem depender apenas de cor. SVGs
decorativos usam `aria-hidden`; gráficos informativos têm título, descrição
e alternativa em tabela. Confira contraste e legibilidade nos dois temas,
sem reaproveitar como certificação atual as medições da paleta azul antiga.

## Checklist para criar ou alterar uma tela

- Reutilizar tokens e componentes da cascata atual.
- Incluir `_tema.html` e os recursos específicos realmente necessários.
- Preservar CSRF, autoria privada, validações e rótulos acessíveis.
- Evitar estilos/scripts inline que contrariem a política de segurança.
- Conferir notebook, celular, temas, textos longos, foco e movimento reduzido.
- Preservar dados ao falhar uma validação e diferenciar vazio de erro.
- Separar funcionalidade implementada de protótipo ou planejamento.
- Rodar os testes pertinentes e validar a documentação com `mkdocs build --strict`.

Relacionado: [Frontend](FRONTEND.md), [Estado da interface](ESTADO_DA_INTERFACE.md),
[Comentários](COMENTARIOS.md) e [Contribuição](PROCESSO_CONTRIBUICAO.md).
