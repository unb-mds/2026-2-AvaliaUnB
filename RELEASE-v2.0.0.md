# Release Notes - v2.0.0 | AvaliaUnB

Entrega final (Release 2) do **AvaliaUnB**, plataforma desenvolvida na disciplina de Métodos de Desenvolvimento de Software (MDS/UnB — 2026/2) para consulta, comparação, ranking e avaliação de professores e disciplinas da Universidade de Brasília.

Seguindo a sequência de entregas **v1.0.0 → v1.0.1 → v1.0.2 → v2.0.0**, esta versão consolida o produto final em produção em **https://avaliaunb.com.br/**, trazendo a nova interface editorial, busca unificada com autocompletar e filtros avançados, avaliação por turma cursada, gráfico de evolução por semestre, comparação livre com destaque de desempenho, ranking por departamento, lista pessoal de favoritos, sistema completo de comentários anônimos com reações e moderação, automação da coleta do SIGAA e documentação final no GitHub Pages.

## Links do Projeto
- **Aplicação em produção:** https://avaliaunb.com.br/
- **Documentação oficial (GitHub Pages):** https://unb-mds.github.io/2026-2-AvaliaUnB/
- **Repositório:** https://github.com/unb-mds/2026-2-AvaliaUnB

## Novidades e Funcionalidades Entregues

### Consulta, Busca Unificada e Filtros Avançados
- **Busca unificada com autocompletar (#220):** campo único em `/professores` que aceita nome do professor, nome ou código da disciplina e departamento, exibindo sugestões tipadas e ignorando acentos, maiúsculas e espaços extras.
- **Filtros avançados combináveis (#221, #276):** filtragem por departamento, faixa de média geral (`nota_min` e `nota_max`) e quantidade mínima de avaliações (`avaliacoes_min`), preservando os filtros ativos na URL, na paginação e no retorno do perfil (`next`), e limpando filtros anteriores ao realizar uma nova busca unificada.
- **Catálogo padronizado (#235, #236):** correção de docentes duplicados, padronização dos nomes de professores, disciplinas e departamentos para grafia comum (sem caixa alta) e exibição da dificuldade média e quantidade de avaliações por disciplina nos cartões.

### Perfil do Professor, Avaliações e Histórico

- **Histórico completo (modelo A, #242):** o catálogo mantém todas as ofertas históricas, sem priorização automática ou filtro de semestre de oferta. A coleta preserva turmas, avaliações e comentários anteriores; a seleção do semestre cursado e o filtro de médias permanecem disponíveis. Para verificar ofertas vigentes para matrícula, consulte o SIGAA. Veja o [registro de decisão](docs/DECISAO_HISTORICO_SEMESTRES.md).
- **Avaliação por turma cursada (#252):** seleção do semestre cursado no formulário de avaliação, permitindo registrar uma avaliação por usuário e por combinação de professor, disciplina e semestre, além das cinco notas pedagógicas (**didática, clareza, organização, disponibilidade e dificuldade**).
- **Médias consolidadas por disciplina e por semestre:** exibição da média geral do docente no topo do perfil, barra visual de dificuldade e alternância entre a média de **Todos** os semestres ou de uma turma específica.
- **Gráfico de evolução por semestre (#224):** gráfico de linha em SVG gerado no servidor (compatível com CSP, sem JavaScript ou estilos inline) acompanhando a evolução das notas do docente nos 6 semestres mais recentes por média geral ou por critério individual, com alternativa acessível em tabela contendo todos os semestres.

### Comparação e Ranking de Professores
- **Comparação livre e destaque de desempenho (#218, #219):** além da comparação de vários docentes na mesma disciplina, `/comparar` oferece o modo livre (`modo=livre`) para comparar professores de disciplinas diferentes, com destaque visual automático para o melhor desempenho geral e em cada critério entre docentes com pelo menos 5 avaliações válidas (em dificuldade, vence a menor média).
- **Ranking geral e por departamento (#222):** classificação em `/ranking` com filtro por unidade acadêmica, calculada pela média dos quatro critérios pedagógicos (excluindo dificuldade) para docentes com no mínimo 5 avaliações válidas.

### Comentários Anônimos, Reações e Moderação
- **Comentários no perfil do professor (#167, #258, #260):** listagem dos 50 primeiros comentários na ordem escolhida, filtro independente por disciplina, publicação, edição e exclusão pelo autor autenticado (limite de 10 comentários por hora), com atalhos padronizados no próprio comentário e exibição totalmente anônima ao público.
- **Reações e ordenação (#212, #213, #270):** reações de curtir (👍) e descurtir (👎) integradas ao visual editorial e seletor com quatro opções de ordenação (`recentes`, `antigos`, `curtidos` e `reacoes`).
- **Filtro automático de conteúdo (#214):** validação no servidor antes da publicação e edição para bloquear dados pessoais (e-mail, telefone, CPF e matrícula), links e ofensas ou palavrões, preservando o texto digitado e informando a categoria do bloqueio.
- **Denúncia, área de moderação e retenção de 90 dias (#215, #216, #217):** denúncia de comentários por usuários logados, área dedicada para moderadores avaliarem pendências com decisões justificadas, acompanhamento e contestação de comentários ocultados pelo autor em `/perfil` e rotina automatizada de descarte dos registros encerrados após 90 dias via função SQL e GitHub Actions, preservando os registros vinculados a comentários que continuam ocultos.

### Conta, Perfil Pessoal e Interface
- **Autenticação com Google e retorno à origem:** login integrado ao Supabase Auth (fluxo PKCE) exclusivamente com conta Google, criação automática do perfil no primeiro acesso, revogação da sessão no logout e redirecionamento para a página de origem.
- **Perfil do usuário expandido (#223, #260):** área autenticada em `/perfil` reunindo a gestão das próprias avaliações (editar e excluir), a lista pessoal de **Professores favoritos** e a seção **Meus comentários** (com atalhos de edição, exclusão e contestação).
- **Interface editorial e identidade visual (#245, #263):** novo design editorial responsivo para desktop e celular, alternância entre tema escuro e tema claro, novo ícone da aba (favicon) e página pública de **Política de Privacidade e Termos de Uso** (`/privacidade`) que descreve o tratamento de dados e os direitos dos usuários.

## Infraestrutura, Coleta de Dados, Segurança e Documentação
- **Atualização semestral do SIGAA (#225):** workflow manual *Atualizar dados do SIGAA* no GitHub Actions para atualizar ofertas de turmas preservando o histórico, com padronização dos nomes coletados e backup público em `docs/backup/`.
- **Segurança e qualidade:** proteção CSRF em formulários, cookies de sessão com `HttpOnly`, `SameSite=Lax` e `Secure` em produção, cabeçalhos de segurança (CSP), limites de requisição (*rate limiting*), validação de `SECRET_KEY` forte e checks automatizados no GitHub Actions (`unittest` com Supabase simulado, `pip-audit` e `Bandit`).
- **Documentação final e governança (#161, #170, #275):** documentação publicada no GitHub Pages (MkDocs Material) totalmente alinhada à `main`, incluindo diagramas de arquitetura em SVG, conferência final com o FigJam (`docs/REVISAO_FIGJAM.md`), inventário da interface (`docs/ESTADO_DA_INTERFACE.md`), Design System atualizado (`docs/DESIGN_SYSTEM.md`), registro de uso de IA (`docs/USO_DE_IA.md`), `CLAUDE.md`, registro de agentes em `.agents/README.md` e skills do projeto em `.agents/skills/`.

## Como Acessar e Rodar

### Acesso online
A aplicação publicada está disponível em: **https://avaliaunb.com.br/**

### Pré-requisitos para execução local
- **Python 3.11+** ou **Docker + Docker Compose**
- Projeto configurado no **Supabase** com as migrações SQL de `docs/migrations/` aplicadas em ordem
- Provedor **Google** habilitado no Supabase (*Authentication → Sign In / Providers → Google*) com a URL de retorno cadastrada em *Authentication → URL Configuration*:
- Execução local com Python: `http://127.0.0.1:5000/login/google/retorno`
- Execução local com Docker: `http://localhost:8000/login/google/retorno`
- Produção: `https://avaliaunb.com.br/login/google/retorno`

### 1. Clone o repositório e configure o `.env`
1. Clone o projeto e acesse a pasta raiz: `git clone https://github.com/unb-mds/2026-2-AvaliaUnB.git && cd 2026-2-AvaliaUnB`
2. Copie `.env.example` para `.env` na raiz do projeto (não versione o `.env`) e preencha as variáveis:

| Variável | Obrigatória | Descrição |
| --- | --- | --- |
| `SECRET_KEY` | Sim | Chave privada e estável para sessão Flask e CSRF (mínimo de 32 caracteres aleatórios). Gere com `python -c \"import secrets; print(secrets.token_hex(32))\"`. |
| `SUPABASE_URL` | Sim | URL do projeto Supabase (ex.: `https://projeto.supabase.co`). |
| `SUPABASE_SERVICE_KEY` | Sim | Chave `service_role` do Supabase, restrita ao servidor. |
| `APP_ENV` | Não | Ambiente de execução (`development` localmente; `production` em produção). |
| `FLASK_DEBUG` | Não | Modo debug (`0` por padrão). Use `1` apenas em desenvolvimento local; em produção, mantenha `0` com `APP_ENV=production`. |
| `PROXY_HOPS` | Não | Quantidade real de proxies reversos confiáveis à frente da aplicação (`0` localmente; ajustar em hospedagem atrás de proxy para manter HTTPS nos callbacks). |
| `RATELIMIT_STORAGE_URI` | Não | Armazenamento compartilhado para limites de requisição em produção com múltiplos workers (ex.: `redis://localhost:6379/0`). |
| `VERIFICACAO_EMAIL_ORIGEM` | Não | URL base HTTPS usada nos links do fluxo opcional de verificação de e-mail no perfil. |
| `VERIFICACAO_EMAIL_SMTP_HOST` | Não | Servidor SMTP (TLS na porta 465) para verificação opcional de e-mail. |
| `VERIFICACAO_EMAIL_SMTP_USUARIO` | Não | Usuário de autenticação SMTP (opcional). |
| `VERIFICACAO_EMAIL_SMTP_SENHA` | Não | Senha de autenticação SMTP (opcional). |
| `VERIFICACAO_EMAIL_REMETENTE` | Não | Endereço remetente autorizado pelo provedor SMTP (opcional). |

### 2. Execução local com Python
1. Crie o ambiente virtual: `python -m venv .venv`
2. Ative o ambiente virtual: `.\\.venv\\Scripts\\Activate.ps1` (Windows PowerShell) ou `source .venv/bin/activate` (Linux/macOS)
3. Instale as dependências: `pip install -r requirements.txt`
4. Inicie o servidor: `python run.py`
5. Acesse no navegador: `http://127.0.0.1:5000`

### 3. Execução com Docker Compose
1. Com Docker, Docker Compose e o `.env` configurados na raiz, execute: `docker compose up --build`
2. A aplicação será servida pelo Gunicorn em `http://localhost:8000`

### 4. Testes automatizados e documentação local
- **Testes automatizados (offline, com Supabase simulado):**
- Linux/macOS: `SECRET_KEY=$(python -c \"import secrets; print(secrets.token_hex(32))\") python -m unittest discover -s tests -t .`
- Windows (PowerShell): `$env:SECRET_KEY=\"chave-de-teste-local-com-mais-de-32-caracteres-1234\"; python -m unittest discover -s tests -t .`
- **Documentação (MkDocs Material):** instale `mkdocs-material`, rode `mkdocs serve` para visualizar localmente e valide com `mkdocs build --strict`.
