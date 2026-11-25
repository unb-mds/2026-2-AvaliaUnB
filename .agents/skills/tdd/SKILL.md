---
name: tdd
description: Guia o ciclo Red-Green-Refactor no AvaliaUnB usando unittest/pytest e ClienteFalso sem tocar no Supabase real.
---

## Quando usar
- Ao implementar novas funcionalidades, rotas Flask, regras de negócio, validações ou migrações SQL.
- Ao corrigir bugs ou ajustes apontados em revisão de Pull Request (escrever primeiro o teste que reproduz o problema).
- Ao adicionar controles de autorização (visitante, autor, outro usuário e moderador) ou regras de privacidade e LGPD.

## Passo a passo
1. Ler os critérios de aceite da issue e listar os cenários de sucesso, erro e borda antes de editar código de produção.
2. **Fase RED:** criar ou atualizar o arquivo correspondente em `tests/` (ex.: `tests/test_supabase.py`, `tests/test_seguranca.py`, `tests/test_moderacao.py` ou `tests/test_<modulo>.py`).
3. Injetar `ClienteFalso` de `tests/fake_supabase.py` via `create_app({'TESTING': True, 'SECRET_KEY': 'chave-falsa', 'SUPABASE_CLIENT': cliente})`, sem conexão de rede.
4. Rodar o teste novo isolado (`SECRET_KEY=chave-falsa python3 -m unittest tests.test_<modulo>` ou `pytest tests/test_<modulo>.py`) e confirmar a falha esperada.
5. **Fase GREEN:** implementar o mínimo necessário em `app/`, `docs/migrations/` ou `tests/fake_supabase.py` até o teste passar.
6. **Fase REFACTOR:** simplificar o código preservando as camadas (`routes` -> `controllers` -> `repositorio`) e rodar a suíte completa com `SECRET_KEY=chave-falsa python3 -m unittest discover -s tests -t .` (ou `pytest`).

## O que nunca fazer
- Nunca alterar código de produção antes de ver o novo teste falhar na fase RED.
- Nunca conectar no Supabase real, ler `.env` ou rodar o scraper durante os testes automatizados.
- Nunca criar testes sem asserção real sobre comportamento observável (status HTTP, estado no `ClienteFalso` ou HTML renderizado).
- Nunca enfraquecer ou apagar testes existentes para mascarar regressões.