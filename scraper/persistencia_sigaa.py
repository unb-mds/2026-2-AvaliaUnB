"""Gravação no Supabase dos dados do scraper (sem selenium)."""
from manutencao_banco import ler_tabela, normalizar_chave
from texto_sigaa import grafia_comum
from turmas_sigaa import montar_payload_turmas

CONFLITO_PROFESSORES = "nome"
CONFLITO_DISCIPLINAS = "codigo"
CONFLITO_TURMAS = "professor_id,disciplina_id,ano,periodo"
LOTE_CONSULTA = 100  # nomes por consulta .in_() (mantém a URL do PostgREST curta)

# Trava contra duplicatas (issue #236): o banco precisa estar convertido antes da importação.
COMANDO_CONVERSAO = "python scraper/manutencao_banco.py converter-nomes --gravar"
MAXIMO_EXEMPLOS_CONFLITO = 5
CODIGO_SAIDA_CONVERSAO_PENDENTE = 2


class ConversaoPendenteError(RuntimeError):
    """O banco ainda tem professores em CAIXA ALTA que o importador duplicaria."""

    def __init__(self, conflitos):
        self.conflitos = list(conflitos)
        exemplos = "\n".join(
            f"  {existente!r} -> {novo!r}"
            for existente, novo in self.conflitos[:MAXIMO_EXEMPLOS_CONFLITO]
        )
        restantes = len(self.conflitos) - MAXIMO_EXEMPLOS_CONFLITO
        if restantes > 0:
            exemplos += f"\n  ... e mais {restantes}"
        super().__init__(
            f"Importação interrompida: {len(self.conflitos)} conflito(s) entre professores "
            "já gravados em CAIXA ALTA e os nomes que o importador gravaria em grafia "
            "comum. Nada foi gravado.\n"
            "Exemplos (nome no banco -> nome que seria gravado):\n"
            f"{exemplos}\n"
            f"Rode {COMANDO_CONVERSAO} antes de usar este importador."
        )


def conflitos_de_grafia(nomes_a_gravar, nomes_existentes) -> list:
    """[(nome no banco, nome a gravar)] que criariam um professor duplicado.

    Conflito: o nome existente é diferente do nome a gravar, tem a mesma normalizar_chave
    (sem acento e sem diferença de caixa) e ainda não está em grafia comum. Nomes idênticos
    e nomes já corretos no banco não são conflito. Função pura.
    """
    por_chave = {}
    for nome in nomes_a_gravar:
        por_chave.setdefault(normalizar_chave(nome), set()).add(nome)
    conflitos = set()
    for existente in nomes_existentes:
        if not existente or grafia_comum(existente, "professor") == existente:
            continue
        for novo in por_chave.get(normalizar_chave(existente), ()):
            if novo != existente:
                conflitos.add((existente, novo))
    return sorted(conflitos)


def verificar_conversao_pendente(professores: list, cliente=None) -> None:
    """Levanta ConversaoPendenteError se gravar `professores` duplicaria nomes não convertidos.

    Lê os professores do banco com paginação. Não escreve nada.
    """
    cliente = cliente or _supabase()
    existentes = [linha["nome"] for linha in ler_tabela(cliente, "professores", "id,nome")]
    conflitos = conflitos_de_grafia([p["nome"] for p in professores], existentes)
    if conflitos:
        raise ConversaoPendenteError(conflitos)


def gravar_catalogo(professores: list, disciplinas: list, turmas: list, cliente=None) -> None:
    """Grava professores, disciplinas e turmas, nessa ordem, depois de conferir a trava.

    A conferência vem antes de qualquer escrita: se houver conflito, nada é gravado.
    """
    verificar_conversao_pendente(professores, cliente)
    mapa_prof = salvar_professores(professores, cliente)
    mapa_disc = salvar_disciplinas(disciplinas, cliente)
    salvar_turmas(turmas, mapa_prof, mapa_disc, cliente)


def conferir_persistencia(professores, disciplinas, turmas, cliente=None):
    """Somente leitura: todas as turmas extraídas devem existir com vínculos válidos.

    Não basta um código zero: os helpers de gravação podem relatar erros sem
    propagá-los. Esta verificação falha se algum vínculo não chegou ao Supabase.
    """
    cliente = cliente or _supabase()
    mapa_prof = {p['nome']: p['id'] for p in ler_tabela(cliente, 'professores', 'id,nome')}
    mapa_disc = {d['codigo']: d['id'] for d in ler_tabela(cliente, 'disciplinas', 'id,codigo')}
    if any(p['nome'] not in mapa_prof for p in professores) or any(
            d['codigo'] not in mapa_disc for d in disciplinas):
        raise ValueError('Professores ou disciplinas da coleta ausentes no banco.')
    esperadas = montar_payload_turmas(turmas, mapa_prof, mapa_disc)
    chaves = lambda linhas: {(t['professor_id'], t['disciplina_id'], t['ano'], t['periodo'])
                              for t in linhas}
    if len(esperadas) != len({(t['professor_nome'], t['disciplina_codigo'], t['ano'], t['periodo'])
                              for t in turmas}):
        raise ValueError('A coleta contém turma sem vínculo de professor ou disciplina.')
    gravadas = ler_tabela(cliente, 'turmas', 'id,professor_id,disciplina_id,ano,periodo')
    if not esperadas or not chaves(esperadas).issubset(chaves(gravadas)):
        raise ValueError('Uma ou mais turmas da coleta não foram persistidas.')
    return True


def _supabase():
    """Import tardio: o --dry-run nunca importa supabase_client (nem lê o .env)."""
    from supabase_client import supabase

    return supabase


def unificar_professores(professores: list) -> list:
    """Um registro por nome (issue #235): a primeira unidade vista é a que fica."""
    por_nome = {}
    for p in professores:
        por_nome.setdefault(p["nome"], p)
    return list(por_nome.values())


def salvar_professores(professores: list, cliente=None) -> dict:
    """Insere os professores novos e devolve {nome: id} de todos.

    Um professor é único pelo nome. Quem já existe não é alterado
    (ignore_duplicates), então o departamento gravado não muda a cada unidade
    raspada; os ids dos existentes são buscados depois do upsert.
    """
    if not professores:
        print("[!] Nenhum professor para salvar.")
        return {}
    unicos = unificar_professores(professores)
    try:
        cliente = cliente or _supabase()
        response = (
            cliente.table("professores")
            .upsert(unicos, on_conflict=CONFLITO_PROFESSORES, ignore_duplicates=True)
            .execute()
        )
        print(f"[*] {len(response.data)} professores novos (de {len(unicos)} únicos).")
        nomes = [p["nome"] for p in unicos]
        mapa = {}
        for i in range(0, len(nomes), LOTE_CONSULTA):
            linhas = (
                cliente.table("professores")
                .select("id,nome")
                .in_("nome", nomes[i:i + LOTE_CONSULTA])
                .execute()
            ).data
            mapa.update({p["nome"]: p["id"] for p in linhas})
        return mapa
    except Exception as e:
        print(f"[!] Erro ao salvar professores: {e}")
        return {}


def salvar_disciplinas(disciplinas: list, cliente=None) -> dict:
    if not disciplinas:
        return {}
    try:
        cliente = cliente or _supabase()
        response = (
            cliente.table("disciplinas")
            .upsert(disciplinas, on_conflict=CONFLITO_DISCIPLINAS)
            .execute()
        )
        print(f"[*] {len(response.data)} disciplinas upsertadas.")
        return {d["codigo"]: d["id"] for d in response.data}
    except Exception as e:
        print(f"[!] Erro ao salvar disciplinas: {e}")
        return {}


def salvar_turmas(turmas: list, mapa_prof: dict, mapa_disc: dict, cliente=None):
    if not turmas:
        return

    # 🔥 Deduplica turmas pela chave única (professor, disciplina, ano, periodo)
    payload = montar_payload_turmas(turmas, mapa_prof, mapa_disc)

    if not payload:
        print("[!] Nenhuma turma única para salvar.")
        return

    print(f"[*] Turmas únicas após deduplicação: {len(payload)} (de {len(turmas)} originais)")

    try:
        cliente = cliente or _supabase()
        response = (
            cliente.table("turmas")
            .upsert(payload, on_conflict=CONFLITO_TURMAS)
            .execute()
        )
        print(f"[*] {len(response.data)} turmas upsertadas.")
    except Exception as e:
        print(f"[!] Erro ao salvar turmas: {e}")
