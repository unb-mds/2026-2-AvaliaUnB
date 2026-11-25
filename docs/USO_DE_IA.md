# Uso de IA no projeto

A equipe usou assistentes de IA como apoio para escrever código, documentação e
material visual. Todo resultado passou por um integrante antes de entrar na
`main`: revisão no PR, testes automatizados e checks do GitHub Actions. Este
documento registra quem usou qual ferramenta, onde há evidência no repositório
e as regras seguidas.

O registro detalhado de cada uso com agentes (pedidos feitos, skills
instaladas e verificação) fica em [`.agents/README.md`](https://github.com/unb-mds/2026-2-AvaliaUnB/blob/main/.agents/README.md).

## Ferramentas por integrante

| Integrante | Ferramentas | Evidência no repositório |
| --- | --- | --- |
| Caio ([@caiionog](https://github.com/caiionog)) | Claude (Claude Code, com a skill `find-skills`) e DeepSeek | Logo com a skill `logo-design` (PR #194); mesclagem da interface editorial com coautoria do Claude no commit (PR #247); aparência das reações com as skills `frontend-design` e `web-design-guidelines` (#270) |
| [@gsm22](https://github.com/gsm22) | Claude (Claude Code) com a skill `test-driven-development` | Criação do [`CLAUDE.md`](https://github.com/unb-mds/2026-2-AvaliaUnB/blob/main/CLAUDE.md), que dá ao Claude Code o contexto de arquitetura, comandos e cuidados do código; uso da skill de TDD informado pela equipe |
| Geovana Duarte ([@Geovanaduartee](https://github.com/Geovanaduartee)) | Codex | Branches `codex/docs-115-readme` e `codex/docs-116-sistema-comentarios`, da revisão do README (#115) e da documentação de comentários (#116), PRs #134 e #135 |
| Luiz Guilherme de Alencar Magalhães ([@lgalencar25](https://github.com/lgalencar25)) | Gemini | Informado pelo integrante; sem marca no histórico |
| Miguel Cardoso ([@MiguelCardoso28](https://github.com/MiguelCardoso28)) | Gemini | Informado pelo integrante; sem marca no histórico |
| Giovanna da Costa Santos ([@giiicostaa](https://github.com/giiicostaa)) | ChatGPT | Informado pela integrante; sem marca no histórico |

Quando não há marca no histórico, a ferramenta foi informada pelo integrante.
Cada pessoa pode detalhar em quais issues usou IA e para quê, seguindo o modelo
do fim desta página.

## Regras seguidas

- **Responsabilidade humana:** a IA sugere; quem abre o PR responde pelo
  conteúdo, revisa o diff e confirma os critérios de aceite da issue.
- **Revisão e testes:** todo código passa pela suíte de testes, que roda sem
  rede com `tests/fake_supabase.py`, e pelos workflows de testes, segurança e
  documentação (`mkdocs build --strict`).
- **Segredos fora da IA:** chaves do Supabase, `SECRET_KEY` e credenciais de
  SMTP não são coladas em assistentes. Elas ficam no `.env` local, ignorado
  pelo Git, e nos ambientes protegidos do GitHub e da Vercel.
- **Dados pessoais fora da IA:** dados de usuários, avaliações e e-mails não são
  enviados a assistentes, em linha com a LGPD e a
  [política de privacidade](POLITICA-DE-PRIVACIDADE.md).
- **Transparência:** commits feitos com agente levam a linha `Co-Authored-By`
  quando a ferramenta a gera, e os usos com agentes ficam em
  `.agents/README.md`.
- **Licenças:** skills de terceiros são copiadas com a licença e com a versão
  travada em `skills-lock.json`. O logo oficial da UnB não foi reproduzido.

## Onde a IA não é usada

- **No produto:** o AvaliaUnB não chama nenhum modelo de IA em produção.
- **No filtro de comentários (#214):** o bloqueio de dados pessoais, links e
  termos ofensivos usa regras e uma lista versionada de termos, sem IA. Casos
  duvidosos seguem para denúncia e moderação humana.
- **Na moderação (#216):** as decisões de manter, ocultar ou restaurar um
  comentário são de moderadores da equipe, com justificativa registrada.

## Contexto para agentes

| Arquivo | Para que serve |
| --- | --- |
| `CLAUDE.md` | Arquitetura, comandos, migrações e cuidados do código para o Claude Code |
| `.agents/README.md` | Registro de cada uso com agentes: ferramenta, pedidos e verificação |
| `.agents/skills/` | Skills instaladas: `logo-design`, `frontend-design`, `web-design-guidelines`, `find-skills` e `test-driven-development` |
| `skills-lock.json` | Origem e commit de cada skill instalada pelo `npx skills` |

## Modelo para registrar um novo uso

Copie para `.agents/README.md` e preencha:

```markdown
## <entrega> (<mês de ano>, issue #<número>)

| Item | Detalhe |
|---|---|
| Ferramenta | <assistente e modelo> |
| Pedido | <o que foi pedido, com as próprias palavras> |
| Resultado | <arquivos ou PR> |
| Revisão | <o que foi conferido, corrigido ou descartado> |
| Verificação | <testes, build, capturas de tela> |
```
