# Diagramas de Arquitetura

Aqui estão as versões mais recentes e atualizadas da arquitetura do projeto AvaliaUnb.

=== "Contexto"

    ### Diagrama de Contexto

    ![Diagrama de Contexto](Diagrama%20de%20contexto.png)

=== "Componentes da API"

    ### Diagrama de Componentes da API

    ![Diagrama de Componentes](Diagrama%20de%20Componentes%20da%20API.png)

=== "Tech Stack"

    ### Tech Stack

    ![Tech Stack](teck%20stack.png)

## Aprofundamento

### Estratégia de histórico de semestres (#242)

A arquitetura mantém a coleta e a persistência cumulativas de ofertas e
avaliações. A proposta de consulta híbrida separa três conceitos: semestre atual (configuração operacional), período cursado (dado de avaliação)
e período selecionado para consulta (estado da navegação).

O scraper registra ofertas por ano e período; uma futura confirmação
operacional define o semestre atual depois da validação. O repositório de
catálogo deverá aplicar o recorte selecionado antes da paginação. Os
repositórios de avaliação continuarão agregando a série histórica, sem
dependência do semestre atual. A configuração e o novo recorte são trabalho
futuro, detalhado no [registro da decisão](DECISAO_HISTORICO_SEMESTRES.md).

Os diagramas mostram as relações gerais. Consulte o [guia do backend](BACKEND.md)
para rotas e repositórios, o [modelo de dados](Modelo%20de%20Dados.md)
para tabelas e RLS, o [scraper](COMO_USAR_SCRAPER.md) para a coleta e
[o mapa da documentação](GUIA_DOCUMENTACAO.md) para os demais temas.
