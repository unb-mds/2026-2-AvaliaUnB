# AGENTS.md — AvaliaUnB

## Resumo e stack
O **AvaliaUnB** é a plataforma acadêmica (MDS — UnB) para consulta, comparação, ranking, avaliação e comentários sobre professores e disciplinas da UnB.

- **Backend:** Python + Flask (Blueprints em `app/routes/`, regras em `app/controllers/`, acesso a dados em `app/repositorio.py`)
- **Frontend:** Templates Jinja2 em `app/templates/` e estilos em `app/static/`
- **Banco e autenticação:** Supabase (PostgreSQL + Auth + RLS, migrações em `docs/migrations/`)
- **Infraestrutura e coleta:** Docker (`Dockerfile`, `docker-compose.yml`) e scraper do SIGAA em `scraper/`

## Como rodar e testar
- **Execução local:** `python3 run.py` (ou `docker compose up --build`)
- **Suíte de testes (unittest):** `SECRET_KEY=chave-falsa python3 -m unittest discover -s tests -t .`
- **Suíte de testes (pytest):** `SECRET_KEY=chave-falsa pytest`
- Os testes rodam offline com `ClienteFalso` (`tests/fake_supabase.py`), sem acessar o Supabase real.

## Documentação do projeto
- `docs/BACKEND.md` — arquitetura Flask, camadas, rotas e convenções do servidor
- `docs/FRONTEND.md` — estrutura de templates Jinja2, parciais e comportamento das telas
- `docs/DESIGN_SYSTEM.md` — tokens visuais, tipografia, temas claro/escuro e componentes
- `docs/Modelo de Dados.md` — tabelas, views, constraints e políticas de acesso do banco

## Skills do projeto (`.agents/skills/`)
Antes de executar tarefas nessas áreas, leia o `SKILL.md` correspondente:
- **Engenharia do projeto:** `tdd`, `banco-e-supabase`, `seguranca-e-rotas-flask`, `fluxo-git-e-pr`
- **Design e interface (instaladas pelo time):** `frontend-design`, `web-design-guidelines`, `logo-design` (registro em `.agents/README.md`)

## Regras obrigatórias de segurança e processo
- **Segredos:** nunca ler, imprimir ou commitar `.env`, nem expor chaves do Supabase (`SUPABASE_SERVICE_KEY`, `SUPABASE_ANON_KEY`), `SECRET_KEY`, senhas ou dados pessoais.
- **Scraper SIGAA:** nunca executar `scraper/scraper_sigaa.py` sem pedido explícito; quando solicitado para validação, usar `--dry-run`.
- **Escopo:** respeitar a seção *Fora do escopo* da issue atual e não alterar arquivos não relacionados.
- **Commits humanos:** ferramentas e agentes de IA **não** fazem `git commit` nem `git push`; os commits e revisões são feitos exclusivamente pelas pessoas do grupo.