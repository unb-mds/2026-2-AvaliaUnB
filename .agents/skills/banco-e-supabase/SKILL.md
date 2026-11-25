---
name: banco-e-supabase
description: Orienta alterações de esquema SQL, RLS, modelos, repositórios Supabase e regras do scraper SIGAA no AvaliaUnB.
---

## Quando usar
- Ao criar ou alterar tabelas, views, índices, constraints ou políticas de RLS em `docs/migrations/`.
- Ao modificar consultas, filtros ou persistência em `app/repositorio.py`, `app/models.py` ou `app/supabase_db.py`.
- Ao ajustar a persistência ou manutenção de dados coletados em `scraper/`.

## Passo a passo
1. Consultar `docs/Modelo de Dados.md` e as migrações em `docs/migrations/` (a partir de `001_initial_schema.sql`) antes de propor mudanças no banco.
2. Criar migrações SQL idempotentes (`IF NOT EXISTS`, `CREATE OR REPLACE VIEW`) preservando as constraints únicas usadas pelo upsert do scraper (`nome,departamento` em `professores`, `codigo` em `disciplinas` e `professor_id,disciplina_id,ano,periodo` em `turmas`).
3. Habilitar `ROW LEVEL SECURITY` em tabelas privadas (como `denuncias_comentarios`, `moderadores`, `moderacoes_comentarios` e `contestacoes_comentarios`), restringindo leitura e escrita ao `service_role`.
4. Manter sincronizados `docs/migrations/`, `app/models.py`, `app/repositorio.py` e `tests/fake_supabase.py`, cobrindo as novas operações com testes offline.
5. Quando houver pedido explícito para validar o scraper SIGAA, executar primeiro com `--dry-run` e conferir se programas de pós-graduação continuam sendo ignorados.

## O que nunca fazer
- Nunca expor `SUPABASE_SERVICE_KEY`, `SUPABASE_URL` real ou credenciais em templates, código cliente, documentação ou logs.
- Nunca ler ou commitar o arquivo `.env` nem rodar consultas destrutivas diretamente no banco de produção.
- Nunca executar `scraper/scraper_sigaa.py` sem solicitação explícita da equipe.
- Nunca quebrar ou remover constraints de unicidade exigidas pela persistência do scraper ou pelas avaliações.