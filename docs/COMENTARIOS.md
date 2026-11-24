# Especificação de comentários avaliativos

**Status: proposta para revisão do grupo, com origem na issue #116.** Este
documento descreve o comportamento dos comentários, das reações e da
moderação. A primeira parte já está implementada no perfil do professor
(issue #167): listar, filtrar por disciplina, publicar, editar e excluir o
próprio comentário. A denúncia está implementada na issue #215, o filtro automático
na issue #214, as reações na #212 e a ordenação escolhida pela pessoa na #213.
Moderação e ocultação continuam sendo planos futuros (issues #216 e #217). As decisões C01 a C11,
na [tabela do final do documento](#decisoes-para-o-grupo-revisar), foram
decididas pela equipe; os pontos ainda a confirmar estão indicados nelas.

A base é a [proposta de dados da #109](Modelo%20de%20Dados.md#6-proposta-tabela-comentarios).
A tabela `comentarios` está versionada em
[`002_comentarios.sql`](migrations/002_comentarios.sql). As reações usam
[`20261123100000_reacoes.sql`](migrations/20261123100000_reacoes.sql).

## Objetivo

Permitir relatos sobre a experiência pedagógica com um professor. O conteúdo
deve tratar de aspectos como didática, organização,
avaliação e disponibilidade, com contexto útil para outros estudantes.

## Quem pode consultar e participar

| Pessoa | Comportamento proposto |
|---|---|
| Visitante | Lê comentários publicados no perfil do professor |
| Usuário autenticado | Usa uma conta comum, bastando estar logado, para comentar, reagir e denunciar |
| Autor | Edita ou exclui seu próprio comentário e acompanha sua análise em privado |
| Moderador autorizado | Analisa as denúncias, com decisão e justificativa registradas |

O perfil do professor tem uma área de comentários sobre a experiência pedagógica.
A participação usa a mesma conta comum para todos, sem perfil docente, espaço
de resposta oficial ou selo de professor. Não se exige e-mail verificado para
comentar: basta estar logado, porque o login é só pelo Google. O fluxo de
verificação de e-mail por link (`app/verificacao_email.py`) continua no
projeto, mas não é usado para comentar. Comentar preserva as permissões das
demais áreas, como o envio de notas.
Uma conta de comentários não concede acesso à moderação.

## Texto, quantidade e vínculo

| Regra | Proposta para revisão |
|---|---|
| Professor | Obrigatório e existente no catálogo |
| Disciplina | Obrigatória. Deve ter sido ministrada pelo professor |
| Quantidade | Sem limite por conta, inclusive para o mesmo professor e disciplina |
| Limite de envio | 10 comentários por hora por usuário, com contador separado do das avaliações |
| Tamanho | De 2 a 1.000 caracteres após remover espaços, tabulações e quebras de linha das extremidades |
| Formato | Texto simples; HTML e Markdown não são interpretados |
| Identificação pública | Sem nome de usuário, nome completo, e-mail, avatar ou rótulo substituto. O vínculo com a conta permanece privado no backend. A leitura direta pela API exige a migração de privacidade da #258 |
| Ordem da lista | Mais recentes (padrão), Mais antigos, Mais curtidos ou Mais reações, escolhida pela pessoa com o parâmetro `ordem` (#213) |
| Quantidade exibida | Os 50 primeiros comentários na ordem escolhida, com o filtro de disciplina já aplicado. A página avisa quando há mais ("Mostrando os 50 primeiros comentários."); não há paginação e o "ver mais" fica para depois |
| Filtro | Por disciplina, no perfil do professor. "Todas as disciplinas" é o padrão e um valor inválido volta a "todas" |
| Datas | Exibir a data da primeira publicação em cada comentário, em dd/mm/aaaa no horário de Brasília, e indicar com "(editado)" quando a atualização for posterior à criação |

O backend deve validar as regras antes da gravação e escapar o texto na saída.
Um texto curto como «ok» passa pela validação de tamanho. O servidor recusa
o texto que fica com menos de dois caracteres depois de remover os espaços
em branco das extremidades.

A autoria sempre vem da sessão autenticada. O servidor deve ignorar um
`usuario_id` enviado pelo formulário. O servidor valida o vínculo entre a
disciplina e o professor.
Na listagem pública, a API retorna só os campos de exibição e o ID do comentário.
O servidor usa o vínculo privado para indicar ao autor quais ações estão
disponíveis na sua sessão.

## Reações

Os ícones **👍** e **👎** ficam sempre visíveis em cada comentário para
qualquer visitante. Cada ícone exibe seu total quando houver reações
daquele tipo. Os nomes das ações ficam disponíveis para leitores de tela.
Para reagir a um comentário de outra pessoa, é preciso entrar na conta.
Cada conta tem uma reação por comentário e pode trocar de opção ou tocar
novamente para removê-la. O servidor
confere a sessão, impede votos no próprio texto e grava a reação com unicidade
por conta e comentário. A lista mostra as contagens, sem revelar quem reagiu.
O formulário envia POST com CSRF para `/comentarios/<id>/reacao`: `valor=1`
para curtir, `-1` para descurtir e `0` para retirar. A página retorna ao perfil
preservando o filtro e a ordem. O autor vê os totais sem controles de voto; visitantes
são encaminhados ao login. As notas e o ranking são independentes. As ordens
por reação (#213) usam essas contagens.

## Ordenação dos comentários

A pessoa escolhe a ordem no seletor **Ordenar por**, ao lado do filtro de
disciplina (issue #213). A escolha vai no parâmetro de consulta `ordem`, com os
valores `recentes`, `antigos`, `curtidos` e `reacoes`; qualquer outro valor, ou
a ausência dele, usa Mais recentes, sem erro. A ordenação é feita no servidor e
combina com o filtro de disciplina.

| Opção | Como a lista é ordenada |
|---|---|
| Mais recentes | Primeira publicação mais recente primeiro. É a ordem padrão |
| Mais curtidos | Maior quantidade de curtidas primeiro |
| Mais antigos | Primeira publicação mais antiga primeiro |
| Mais reações | Maior soma de curtidas e descurtidas primeiro |

Em empate por curtidas ou reações, o comentário mais recente vem primeiro.
Se dois comentários tiverem a mesma data e hora de publicação, o
identificador desempata na mesma direção da ordenação por data. Editar um comentário
preserva sua data original.

Mais curtidos conta só as curtidas (👍); Mais reações soma curtidas e
descurtidas (👍 + 👎). Comentários sem reação vêm depois dos que têm, também
do mais recente para o mais antigo. Não há paginação: cada ordem mostra os 50
primeiros comentários, escolhidos depois de ordenar todos os comentários
publicados do professor (e da disciplina filtrada). Quando há mais de 50, a
página avisa "Mostrando os 50 primeiros comentários." Comentários ocultados
ficam fora da lista e da contagem. Publicar, editar, excluir, denunciar e
reagir voltam ao perfil com a mesma ordem e o mesmo filtro.

## Estrelas e comentários

Dar estrelas e escrever um comentário são ações independentes. A pessoa pode
usar só uma delas ou as duas na ordem que preferir. Para a mesma disciplina,
pode comentar primeiro e dar estrelas mais tarde, ou dar estrelas primeiro
e comentar depois. Cada ação tem seu próprio formulário e envio.

- Criar, editar ou excluir comentário não altera notas, médias ou ranking.
- Editar ou excluir uma avaliação não remove o comentário.
- Desde a #252, cada estudante pode registrar uma avaliação por estrelas para
  cada professor, disciplina e semestre cursado. Pode avaliar Cálculo 1 com o
  mesmo professor em dois semestres distintos. Para mudar a nota de uma turma,
  edita a avaliação correspondente.
  A pessoa pode publicar vários comentários para a mesma disciplina.

Na [opção híbrida da #242](DECISAO_HISTORICO_SEMESTRES.md), os comentários
históricos permanecem acessíveis, conforme as regras de moderação e exclusão.
O filtro de oferta do catálogo não filtra nem apaga comentários. A data da
publicação não representa necessariamente o semestre cursado.

## Fluxos para as telas da #112

### Listar e escrever

O perfil do professor apresenta os comentários publicados em uma seção
separada das notas. A lista vazia convida a escrever o primeiro comentário.
Visitantes veem a opção de entrar com o Google (**Entrar para comentar**) para
escrever ou reagir.
Cada relato exibe sua disciplina. Quem já comentou pode editar os próprios
textos e escrever outro relato para a mesma disciplina ou para outra
ministrada pelo professor.

A lista mostra os 50 primeiros comentários na ordem escolhida e tem um filtro
**Disciplina**, com "Todas as disciplinas" por padrão, e o seletor **Ordenar
por**, que abre em Mais recentes. Quando há mais de 50, a página avisa
"Mostrando os 50 primeiros comentários."

O formulário informa: "Sua identificação não aparece junto do comentário.
Evite incluir dados pessoais no texto." A listagem não mostra identificação
do autor nem rótulo substituto. A publicação usa o botão **Publicar**.
Mostra o limite, exige a escolha de uma disciplina ministrada pelo professor
e preserva o texto em erros de validação ou moderação. Durante a
verificação, a interface desabilita o botão de envio e só confirma a
publicação quando o texto fica público.

### Editar e excluir

A edição é exclusiva do autor, preserva a data original e atualiza `atualizado_em`.
O identificador do professor e a autoria não podem ser alterados pela edição.
A disciplina pode ser trocada por outra ministrada pelo mesmo professor.
Editar ou excluir o comentário de outra pessoa, ou um que não exista,
responde HTTP 404.

A exclusão deve pedir confirmação, identificando o professor, a disciplina
e a consequência; ela passa por uma página de confirmação. Depois de excluir,
o texto e as reações daquele comentário saem da lista.

### Conteúdo ocultado

Um comentário ocultado pela moderação deixa de aparecer na listagem pública.
O autor recebe o estado e a justificativa. A edição continua privada até a
decisão da moderação. Qualquer novo relato passa pelo filtro antes da
publicação.
O autor pode pedir revisão pelo formulário privado descrito abaixo.

## Filtro automático antes da publicação

O backend verifica comentários novos e edições antes de disponibilizá-los.
O filtro aplica regras em português para dados pessoais (e-mail, telefone,
CPF e matrícula), links e uma lista de palavrões e ofensas. Ameaças, spam e
outros abusos que as regras não reconhecem ficam para a denúncia e a moderação.
O filtro normaliza maiúsculas, acentos, caracteres invisíveis e letras repetidas
para reconhecer tentativas simples de disfarçar termos. Uma crítica à didática ou uma avaliação negativa, por si só,
deve passar.

| Resultado | Comportamento |
|---|---|
| Aprovado | Publica o texto ou aplica a edição |
| Bloqueado | Mostra o motivo ao autor e mantém o texto no formulário para revisão |
| Incerto | Casos duvidosos não são julgados pelo filtro: o comentário é publicado e, se houver denúncia, segue para a moderação (C08) |
| Filtro indisponível | Não se aplica na implementação da #214: o filtro roda no próprio servidor, sem serviço externo, e não tem estado de indisponibilidade |

Uma edição bloqueada preserva a versão anterior de um comentário publicado. Se o comentário já estiver oculto, a edição continua
privada até decisão da moderação. O filtro e a denúncia cumprem papéis
complementares, pois uma regra automática pode deixar passar conteúdo impróprio.

Regras decididas (C10): o filtro roda no envio, antes de publicar. Quando
encontra uma violação, o comentário é rejeitado, sem ser salvo, e a pessoa
recebe um aviso pedindo que o reescreva. O filtro bloqueia telefone, e-mail,
CPF, matrícula (qualquer sequência de 8 ou mais dígitos, mesmo com pontos ou
espaços), links e uma lista de palavrões e ofensas claramente inadequados. A
lista vale por palavra inteira, sem diferenciar maiúscula, minúscula ou
acento, fica em arquivo separado e extensa, e é fácil de atualizar. O filtro
não julga opinião e não usa IA. Implementado na issue #214.

Como o filtro funciona (#214):

- A lista de termos fica em `app/dados/termos_bloqueados.txt`, um termo por
  linha, e é carregada uma vez. Linhas vazias e linhas iniciadas por `#` são
  ignoradas, o que facilita a atualização pelo grupo.
- Os termos são comparados por palavra inteira, sem diferenciar maiúscula nem
  acento. O plural com "s" é coberto. Uma palavra que apenas contém um termo
  (como "burocracia") passa.
- Há expressões de mais de uma palavra, inclusive frases de duas palavras que
  combinam identidade e ofensa (como "negro imundo"), porque palavras como
  "negro", "gordo" ou "nordestino" não são bloqueadas sozinhas.
- A matrícula vale com ponto, hífen ou barra entre os dígitos, e com espaços
  quando há três ou mais grupos de três dígitos ou mais. Números de um ou dois
  dígitos separados por espaço (notas, listas) nunca contam. Semestres
  (2024.1, 2023/2), listas de anos, datas no formato dd/mm/aaaa e códigos de
  disciplina com semestre (FGA0011/2024.1) passam.
- O filtro vale ao publicar e ao editar, depois da validação de tamanho
  (2 a 1.000 caracteres) e antes de gravar.
- Quando bloqueia, a rota responde HTTP 400 e devolve o formulário com o texto
  preservado e uma mensagem junto ao campo, que informa só a categoria, sem
  revelar o trecho nem a lista. As mensagens são "Seu comentário não foi
  publicado porque parece conter dados pessoais (telefone, e-mail, CPF ou
  matrícula). Remova e tente novamente.", "... contém um link. Remova e tente
  novamente." e "... contém linguagem ofensiva. Reescreva e tente novamente."
  Na edição, "publicado" vira "salvo".
- Na edição bloqueada, o comentário original não muda.
- O texto bloqueado não é gravado nem registrado em log.
- O envio bloqueado conta no limite de 10 comentários por hora, porque o
  limite se aplica a toda requisição de publicação. A edição não tem esse limite.
- Casos duvidosos passam; se houver denúncia, seguem para a moderação.

Limitações conhecidas:

- Telefone escrito dígito a dígito, com espaços entre os números, passa.
- Números escritos por extenso passam.
- Identificadores de redes sociais (`@usuario`) não são bloqueados.
- Trocas de letras por homóglifos (por exemplo, letras de outros alfabetos) não
  são reconhecidas.
- As frases de duas palavras só pegam a combinação exata e adjacente.
- Texto colado a um domínio, como "bom.com", é tratado como link.
- O filtro está no controller: quem chamar o repositório diretamente não passa
  por ele.

## Denúncia e moderação

Proposta de fluxo:

1. Um usuário autenticado denuncia um comentário, selecionando motivo e, se
   necessário, acrescentando uma explicação.
2. O sistema confirma o recebimento sem expor a identidade do denunciante ao
   autor ou a visitantes. Uma denúncia ativa por usuário e comentário evita
   duplicação; a regra precisa ser refletida no futuro modelo.
3. Um moderador autorizado consulta texto, motivo e contexto e registra a
   decisão de manter, ocultar ou restaurar, com justificativa.
4. O autor pode pedir revisão em um formulário privado associado ao comentário.
   O pedido fica visível ao autor e aos moderadores designados.

Os motivos propostos são ofensa ou ataque pessoal, exposição de dados pessoais,
discriminação, ameaça, spam ou conteúdo alheio à experiência pedagógica.
Uma avaliação negativa ou discordância com a opinião não são, por si só,
motivos para remoção. O número de denúncias não oculta automaticamente o texto.

Os passos 1 e 2 estão implementados (issue #215): o link «Denunciar» aparece
para usuários logados nos comentários de outras pessoas e leva a um formulário
com os seis motivos acima (spam e conteúdo alheio ficam separados) e uma
explicação opcional de até 500 caracteres. A tabela privada
`denuncias_comentarios` está em
[`005_denuncias_comentarios.sql`](migrations/005_denuncias_comentarios.sql);
veja o [modelo de dados](Modelo%20de%20Dados.md#7-denuncias-de-comentarios-denuncias_comentarios).
Os passos 3 e 4 ficam para a #216.

A [proposta de banco](Modelo%20de%20Dados.md) descreve a proteção das tabelas
de comentários e reações. A implementação futura precisa definir o registro
privado das análises e denúncias e revisar as permissões de moderação,
inclusive o uso de service key descrito em [Cibersegurança](CIBERSEGURANCA.md).
Decidido (C08): os comentários são publicados na hora. A tela de moderação
mostra somente os comentários denunciados, e o moderador pode manter, ocultar
da visão pública ou restaurar, sempre com justificativa. Todos os integrantes
da equipe do projeto têm acesso a essa tela, e toda ação registra quem a fez e
a justificativa. Não existe moderação manual pelo painel do Supabase como
etapa oficial. A proposta operacional é usar três dias úteis como meta para a
primeira análise, a confirmar pelo grupo. Sempre que possível, outra pessoa
moderadora analisa a contestação. Se ninguém da equipe puder atender a fila de
denúncias, a publicação de novos comentários fica pausada até haver cobertura.

## Privacidade e ciclo dos dados

Decisão C05, implementada na #258: a listagem não inclui nome de usuário,
e-mail, nome completo, avatar ou rótulo substituto. O vínculo entre o comentário
e a conta permanece interno, para os limites de participação, a edição e a
exclusão pela própria pessoa e a apuração de abusos. A resposta pública do
backend não inclui identificadores da conta nem consulta o perfil do autor.

A [migração de privacidade](migrations/20261122155752_anonimato_comentarios.sql)
deve ser aplicada após as migrações 001 a 007 para proteger também a leitura
direta pela Data API: `anon` e `authenticated` só podem consultar as colunas
públicas. `usuario_id` e `ocultado_em` permanecem privados. O backend mantém
acesso por `service_role`, sem mudanças nas políticas de escrita ou de RLS.

A orientação ao autor deve pedir que não publique matrículas, contatos,
documentos, informações pessoais de terceiros ou relatos que exponham pessoas
sem necessidade. O acesso às denúncias e aos registros de moderação deve ficar
restrito aos responsáveis autorizados. Logs operacionais não devem copiar
indiscriminadamente o texto ou dados pessoais.

As cascatas propostas na #109 apagam comentários quando o perfil do autor ou o
professor é excluído. Uma disciplina com comentários vinculados deve ser
mantida para preservar o vínculo dos relatos históricos.
O registro mínimo da denúncia, da decisão de moderação e da contestação é guardado por até 90 dias após o encerramento do caso e descartado automaticamente por rotina diária agendada no GitHub Actions (.github/workflows/retencao_moderacao.yml, com função SQL em docs/migrations/009_retencao_moderacao_90_dias.sql), sem apagar comentários publicados (issue #217).
O texto excluído sai da listagem imediatamente. O registro mínimo da denúncia, da decisão de moderação e da contestação é guardado por até **90 dias** após o encerramento do caso e descartado automaticamente por rotina diária agendada no GitHub Actions (`.github/workflows/retencao_moderacao.yml`, chamando a função SQL em `docs/migrations/009_retencao_moderacao_90_dias.sql`), sem apagar comentários publicados e preservando o histórico enquanto o comentário continuar ocultado (`ocultado_em IS NOT NULL`) (issue #217). O texto excluído sai da listagem imediatamente.

## Decisões para o grupo revisar

| ID | Decisão proposta | Situação |
|---|---|---|
| C01 | Leitura pública e participação com conta comum, bastando estar logado (login só pelo Google), sem exigir e-mail verificado. Sem espaço ou perfil exclusivo para professores | Decidida; implementada na #167. Basta estar logado pelo Google, sem exigir e-mail verificado |
| C02 | Disciplina obrigatória. A pessoa pode comentar quantas vezes quiser para o mesmo professor e disciplina | Decidida; já implementada. Pode comentar mais de uma vez no mesmo professor e disciplina, com limite de 10 por hora por usuário |
| C03 | Texto simples de 2 a 1.000 caracteres após remover espaços em branco das extremidades | Decidida; já implementada e verificada. Texto de 2 a 1.000 caracteres, contados após remover espaços nas pontas e normalizar quebras de linha |
| C04 | Estrelas e comentários são independentes e podem ser enviados em qualquer ordem. Uma avaliação por estrelas por estudante, professor, disciplina e semestre cursado (regra atualizada pela #252) | Decidida; já implementada e verificada. Comentar não exige avaliar e avaliar não exige comentar; editar ou excluir um não altera o outro |
| C05 | Comentários anônimos para o público: sem identificação ou rótulo substituto. O vínculo com a conta permanece interno para os limites de participação, edição, exclusão e apuração de abusos | Decidida em reunião da equipe (revisa a #167). Implementação na #258; proteção da leitura direta depende da migração de privacidade |
| C06 | Denúncia privada e moderação por responsáveis autorizados | Decidida e implementada (#215 e #216). A denúncia funciona na #215 e a área restrita de moderação (/moderacao) está implementada na #216, acessível apenas a usuários cadastrados na tabela privada moderadores. |
| C07 | Ocultação motivada, sem republicação automática por edição | Decidida e implementada (#216). Comentário ocultado por moderação sai da listagem pública e não volta por edição do autor; só um moderador restaura, com justificativa registrada. |
| C08 | Comentários publicados na hora. A tela de moderação mostra somente os denunciados, e o moderador pode manter, ocultar da visão pública ou restaurar, sempre com justificativa. Todos os integrantes da equipe têm acesso, e toda ação registra quem a fez e a justificativa. Primeira análise em até três dias úteis, formulário privado de contestação e retenção de até 90 dias após o encerramento | Decidida e implementada (#216; retenção de 90 dias implementada na #217). Comentários são publicados na hora; a tela /moderacao mostra somente os denunciados e permite manter, ocultar ou restaurar com justificativa e registro do moderador. O autor pode contestar em /comentarios/<id>/contestar. |
| C09 | Ícones 👍 e 👎 sempre visíveis, com números apenas nas reações recebidas. Uma reação por conta e comentário, com opção de trocar ou remover | Implementada na #212 |
| C10 | Filtrar no servidor antes de publicar ou editar. Bloquear violações claras e deixar os casos incertos para a moderação, que atua mediante denúncia | Decidida e implementada (#214; veja "Regras decididas (C10)" acima): rejeita sem salvar, com aviso para reescrever; sem IA. Vale ao publicar e ao editar |
| C11 | Data em cada comentário. Ordenação por Mais recentes, Mais curtidos, Mais antigos ou Mais reações | Decidida e implementada: data em cada comentário (#167) e as quatro ordens (#213). Mais recentes é o padrão |

As decisões podem ser revisadas no PR ou na
[issue #116](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/116).
Os [protótipos da #112](TELAS_COMENTARIOS.md) e a [proposta de dados da #109](Modelo%20de%20Dados.md#6-proposta-tabela-comentarios)
acompanham estas regras.

## Critérios para a futura implementação

- Visitantes consultam comentários sem identificação do autor e contagens de reações. Estar logado
  (login pelo Google) é obrigatório para comentar,
  reagir ou denunciar; não se exige e-mail verificado.
- «ok» passa pela validação de tamanho. Campo vazio, texto com menos de
  dois caracteres após retirar os espaços em branco das extremidades e
  texto acima de 1.000 caracteres recebem erro claro.
- Disciplina ausente ou inválida recebe erro claro e preserva o texto
  preenchido.
- A mesma conta pode publicar dois relatos distintos em Cálculo 1 com o
  mesmo professor. Cada relato tem seu próprio texto, reações e ações de
  editar ou apagar.
- Só o autor edita ou exclui. O servidor nega tentativas de se passar por outro
  usuário e mantém os identificadores de conta fora das respostas públicas.
- O e-mail de cadastro do autor não aparece em nenhuma página nem resposta de
  comentários, nem ao clicar no nome de usuário.
- Uma conta troca ou desfaz sua reação. Pedidos simultâneos respeitam a
  unicidade, e autores não reagem ao próprio comentário.
- A lista exibe a data e os dois ícones em cada comentário, inclusive para
  visitantes sem login.
  Os números aparecem só para reações recebidas.
  Com 8 curtidas e 1 descurtida, o comentário aparece com 8 e 1 separados.
  Na opção Mais reações, as duas contagens somam 9 para a ordenação.
- Com 3 curtidas e nenhuma descurtida, a lista exibe 👍 3 e 👎 sem número.
  Sem nenhuma reação, aparecem só os dois ícones.
- Mais recentes abre por padrão. Mais curtidos ordena apenas pelas
  curtidas, e Mais antigos inverte a ordem por data. A edição preserva
  a posição nas duas ordens por data.
- O filtro barra uma ofensa inequívoca e a exposição de um telefone, deixa
  passar uma crítica respeitosa e deixa passar um caso ambíguo, que segue para
  a moderação se for denunciado.
- O filtro também cobre edições. Edições bloqueadas devolvem o texto digitado
  para revisão e preservam a versão anterior do comentário.
- Uma conta autorizada a usar as duas ações consegue enviar só estrelas,
  publicar só um comentário ou fazer os dois em qualquer ordem.
- A mesma conta pode avaliar com estrelas Cálculo 1 e Cálculo 2 com o mesmo
  professor. Uma segunda avaliação de Cálculo 1 no mesmo semestre é recusada;
  uma avaliação de outro semestre cursado é permitida (#252).
- As notas e os resultados de ranking e comparação não mudam por um comentário.
- A identidade do denunciante e os dados privados não aparecem na listagem pública.
- As telas cobrem vazio, envio, erro, edição, confirmação de exclusão e ocultação.
- As permissões de backend e banco seguem o modelo aprovado, com testes de
  autorização. A tabela `comentarios` vem da migração `002_comentarios.sql`;
  reações e denúncias têm migrações versionadas; moderação ainda não.

Documentos relacionados: [modelo de dados](Modelo%20de%20Dados.md),
[protótipos](TELAS_COMENTARIOS.md), [frontend](FRONTEND.md) e
[cibersegurança](CIBERSEGURANCA.md). Os comentários (listar, filtrar por
disciplina, publicar, editar e excluir) já estão ativos no perfil do professor
desde a #167 e o filtro automático desde a #214; reações (#212), denúncia (#215) e
ordenação (#213) também estão implementadas. A moderação fica nas demais issues.
