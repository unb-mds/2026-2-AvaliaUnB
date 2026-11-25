---
name: seguranca-e-rotas-flask
description: Padroniza rotas Flask, templates Jinja2, proteção CSRF, redirecionamento seguro e controle de acesso no AvaliaUnB.
---

## Quando usar
- Ao criar ou alterar rotas em `app/routes/` (`main_routes.py`, `auth_routes.py`, `professor_routes.py`, `moderacao_routes.py`).
- Ao adicionar formulários POST, telas ou parciais em `app/templates/` e estilos em `app/static/`.
- Ao implementar ou revisar regras de autenticação, autorização, rate limit e redirecionamentos.

## Passo a passo
1. Consultar `docs/BACKEND.md`, `docs/FRONTEND.md` e `docs/DESIGN_SYSTEM.md` para manter a separação de camadas e o padrão visual do site.
2. Registrar novas rotas no Blueprint adequado e manter a lógica de negócio em `app/controllers/` e o acesso ao banco em `app/repositorio.py`.
3. Proteger rotas restritas com `@login_required` ou `@moderador_required`, validando sempre a autoria no servidor (nunca confiar em `usuario_id` enviado pelo formulário).
4. Incluir `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` em todos os formulários POST e validar parâmetros de retorno (`next`) com `is_safe_url` de `app/seguranca.py`.
5. Reutilizar os parciais globais (`_topo.html`, `_rodape.html`, `_tema.html`) e os tokens de CSS existentes; para revisões de UI e acessibilidade, aplicar também `frontend-design` e `web-design-guidelines`.

## O que nunca fazer
- Nunca criar formulário POST sem token CSRF nem redirecionar para URL recebida do usuário sem passar por `is_safe_url`.
- Nunca retornar dados privados de outros usuários (como denunciante ou e-mail) em templates ou respostas JSON.
- Nunca ativar `FLASK_DEBUG` em produção (`APP_ENV=production`) nem iniciar a aplicação com `SECRET_KEY` fixa ou vazia no código.
- Nunca colocar consultas diretas ao Supabase dentro das rotas ou templates.