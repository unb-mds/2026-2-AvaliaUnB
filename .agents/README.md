# Agentes de IA utilizados

## Semestre atual e preservação do histórico (novembro de 2026, #278–#280)

| Item | Detalhe |
|---|---|
| Ferramenta | Codex |
| Pedido | Implementar a decisão híbrida da #242, com testes e validação da coleta de 2026/2 para a entrega |
| Resultado | PR #282 para configuração, #283 para filtro de ofertas e #284 para validação operacional; um PR por issue |
| Decisão técnica | Arquivo versionado para configuração, sem migração; histórico preservado, confirmação explícita após coleta completa e persistência conferida |
| Verificação | Suíte local (716 testes), MkDocs estrito, Bandit, YAML, sintaxe do JavaScript e navegador nos temas claro/escuro e viewport móvel com dados fictícios; resultados remotos e da coleta nos PRs |

A coleta completa inicial foi simulada sem gravar no banco. A execução de gravação
e sua validação têm evidências próprias nos PRs e no workflow; o simples resultado
do dry-run não comprova que todos os vínculos existem no ambiente publicado.

Registro das ferramentas de IA usadas no projeto, para transparência e reprodutibilidade.
A visão geral, com as ferramentas de cada integrante e as regras seguidas, está em
[`docs/USO_DE_IA.md`](../docs/USO_DE_IA.md).

## Logo AvaliaUnB (novembro de 2026)

| Item | Detalhe |
|---|---|
| Ferramenta | [Claude Code](https://claude.com/claude-code) (CLI), modelo Claude Opus 5.5 |
| Skill/plugin | `logo-design` do marketplace [kaankiziltug/logo-design-skill](https://github.com/kaankiziltug/logo-design-skill) (v1.4.5) |
| Resultado | `docs/logo/` (símbolos, lockups e folha de teste em fundos claros e escuros) |
| Instruções da skill | [`skills/logo-design/SKILL.md`](skills/logo-design/SKILL.md) (cópia da v1.4.5, licença MIT em `skills/logo-design/LICENSE`) |
### Instalação da skill

Dentro do Claude Code:

```text
/plugin marketplace add kaankiziltug/logo-design-skill
/plugin install logo-design@logo-design-skill
/reload-plugins
```

### Pedidos feitos ao agente

1. "Utilizando a ideia de logo que já tenho no site, use essa skill e crie algo que misture uma estrela de avaliação com UnB."
   - Foram gerados 3 conceitos (estrela com capelo, U com estrela, estrela de 5 critérios). Descartados.
2. "Utilize a primeira com chapéu de formando, mas faça a estrela bem menor que o chapéu, e utilize azul, branco e preto, de forma que fique boa em fundos escuros e claros. Pode usar amarelo também."
   - Versão aprovada: capelo com a estrela pendurada na borla.

### Scripts da skill usados

- `render_png.py` — renderiza os SVGs em PNG para inspeção visual;
- `svg_audit.py` — confere geometria, cores e detalhes pequenos;
- `concept_sheet.py` — folha de comparação dos conceitos iniciais.

### Observações

- Os lockups ainda usam texto (`<text>`) com fonte do sistema; para a versão final, converter as letras em contornos.
- Em 16 px a estrela praticamente some; o favicon deve ter uma versão própria com a estrela ampliada.
- O logo oficial da UnB não foi copiado. Ele é marca registrada da universidade.

## Aparência das reações nos comentários (novembro de 2026, issue #270)

| Item | Detalhe |
|---|---|
| Ferramenta | [Claude Code](https://claude.com/claude-code), modelo Claude Opus 5.5 |
| Busca da skill | `find-skills` de [vercel-labs/skills](https://www.skills.sh/vercel-labs/skills/find-skills), instalada em `.agents/skills/find-skills/`: consulta ao ranking do skills.sh, preferindo fontes conhecidas e com muitas instalações |
| Skills escolhidas | `frontend-design` ([anthropics/skills](https://www.skills.sh/anthropics/skills/frontend-design)) e `web-design-guidelines` ([vercel-labs/agent-skills](https://www.skills.sh/vercel-labs/agent-skills/web-design-guidelines)) |
| Versões | Fixadas por commit em [`skills-lock.json`](../skills-lock.json) |
| Resultado | `app/templates/_reacoes_comentario.html`, `app/static/integracao-editorial.css` e documentação de frontend |

### Instalação

```bash
npx skills add https://github.com/vercel-labs/skills --skill find-skills   # opcional: para buscar skills
npx skills add https://github.com/anthropics/skills --skill frontend-design
npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines
```

As skills ficam em `.agents/skills/`. O instalador também cria atalhos em
`.claude/skills/` para o Claude Code; eles não foram versionados porque são
links simbólicos, que não funcionam bem no Windows. Para recriá-los, rode o
`npx skills add` de novo.

### Para que cada skill serviu

- `frontend-design`: orientou o ajuste pelos tokens que o site já usa, sem
  inventar outro estilo. O 👍/👎 virou polegar em SVG com o total ao lado, em
  Inter 700 e na cor `--muted`, com o verde `--accent` só na reação selecionada.
  Numa segunda rodada, a pedido do Caio, a borda em volta dos botões saiu.
- `web-design-guidelines`: revisão de acessibilidade. Alvo de toque de 44 px,
  foco visível, `aria-pressed`, nome acessível com o total, ícone preenchido
  além da cor para indicar a seleção e `prefers-reduced-motion` respeitado.

### Diagnóstico

Desde a interface editorial (#247), o perfil do professor não carrega mais o
`comentarios.css`, onde estavam os estilos das reações. Os botões apareciam
com o visual padrão do navegador (cinza, empilhados) e com emojis amarelos,
fora da paleta. Os estilos novos ficam em `integracao-editorial.css`, que é
carregado em todas as páginas.

### Pedido feito ao agente

"A aparência do like e deslike nos comentários está meio destoante com o resto
do site, adeque isso. Faça isso usando o find-skills para achar uma skill e
documente elas nos agents."

### Verificação

- Capturas do perfil do professor nos temas escuro e claro, antes e depois,
  como visitante, autor do comentário e pessoa que já reagiu.
- `pytest`: 697 testes passando; o teste do template de reações foi ajustado
  para os ícones em SVG.
- A revisão e o commit ficaram com o Caio.

## Revisão de arquitetura e documentação (novembro de 2026, issue #170)

| Item | Detalhe |
|---|---|
| Ferramenta | Codex |
| Pedido | Resolver as pendências da issue #170 e alinhar o PR #178 à main |
| Resultado | Integração da main sem reescrever histórico; documentação de arquitetura, interface, comentários e migrações; roteiro de conferência do FigJam |
| Revisão | Preservação dos registros de uso de IA, releases e decisão de semestres; remoção de referências desatualizadas sobre moderação, retenção, autoria e favicon |
| Skills de apoio | Computer Use e Plugin Management para consultar acesso às integrações; sem alteração comprovada no board do FigJam |
| Verificação | Build estrito do MkDocs, suíte existente, links locais, XML dos SVGs e ausência de marcadores de conflito; resultados registrados no PR #178 |

A integração Figma recusou acesso ao board, mas a conta no navegador tinha
permissão de edição. Após as alterações feitas pela usuária, o Codex conferiu
contexto, componentes, stack, story map e os rótulos de planejamento pelo navegador
em 25/11/2026. Os ajustes finais de coleta separada e criação do perfil com Google
foram verificados; as evidências estão em `docs/REVISAO_FIGJAM.md`.

## Skills de apoio instaladas no fim do projeto

| Skill | Origem | Quem usou | Para quê |
|---|---|---|---|
| `find-skills` | [vercel-labs/skills](https://www.skills.sh/vercel-labs/skills/find-skills) | Caio | Achar skills no ecossistema do skills.sh antes de instalar; foi usada para escolher as skills da #270 |
| `test-driven-development` | [obra/superpowers](https://www.skills.sh/obra/superpowers/test-driven-development) | gsm22 | Ciclo red-green-refactor: escrever o teste, vê-lo falhar, implementar o mínimo e refatorar |

As duas ficam em `.agents/skills/` e têm o commit de origem travado em
[`skills-lock.json`](../skills-lock.json). Para instalar de novo:

```bash
npx skills add https://github.com/vercel-labs/skills --skill find-skills
npx skills add https://github.com/obra/superpowers --skill test-driven-development
```

## Histórico de semestres (novembro de 2026, issue #242)

| Item | Detalhe |
|---|---|
| Ferramenta | ChatGPT (assistência à documentação e organização das issues) |
| Pedido | Documentar a opção híbrida e finalizar as pendências da decisão; padronizar o termo como semestre atual |
| Resultado | PR #269, sub-issues #278, #279 e #280 e PR #281 de atualização documental |
| Revisão | Conferência das regras já implementadas (#224 e #252), preservação do histórico, escopo das sub-issues e vínculo com o PR integrado; ratificação coletiva permanece pendente |
| Verificação | `mkdocs build --strict` e `git diff --check` no PR #281; nenhuma alteração de código de produção |
