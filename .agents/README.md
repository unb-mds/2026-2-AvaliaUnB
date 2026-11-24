# Agentes de IA utilizados

Registro das ferramentas de IA usadas no projeto, para transparência e reprodutibilidade.

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
| Busca da skill | `find-skills` de [vercel-labs/skills](https://www.skills.sh/vercel-labs/skills/find-skills): consulta ao ranking do skills.sh, preferindo fontes conhecidas e com muitas instalações |
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
  inventar outro estilo. O 👍/👎 virou botão fantasma igual a `.btn.ghost`
  (borda `--line`, raio de 10 px, Inter 700), com o verde `--accent` só na
  reação selecionada.
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
