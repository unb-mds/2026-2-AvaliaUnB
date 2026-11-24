"""Montagem pura do payload de turmas (sem selenium nem Supabase)."""


def registrar_docentes_da_linha(docentes, departamento, disciplina_atual, ano, periodo,
                                docentes_brutos, professores_dict, turmas_list):
    """Registra professores e turmas de uma linha da busca.

    `docentes` já vem em grafia comum: o mesmo texto vira a chave de `professores_dict`,
    o `nome` do professor e o `professor_nome` de cada turma, sem divergência entre as pontas.
    """
    for nome_prof in docentes:
        professores_dict.setdefault(
            (nome_prof, departamento), {"nome": nome_prof, "departamento": departamento}
        )
        if disciplina_atual:
            turmas_list.append({
                "disciplina_codigo": disciplina_atual["codigo"],
                "professor_nome": nome_prof,
                "ano": int(ano),
                "periodo": int(periodo),
                "docentes_brutos": docentes_brutos,
            })


def montar_payload_turmas(turmas: list, mapa_prof: dict, mapa_disc: dict) -> list:
    """Deduplica turmas pela chave única (professor, disciplina, ano, periodo).

    `mapa_prof` é {nome: id} (um professor por nome, issue #235) e
    `mapa_disc` é {codigo: id}. Turmas cujo professor ou disciplina não estão
    nos mapas são ignoradas.
    """
    vistos = set()
    payload = []

    for t in turmas:
        prof_id = mapa_prof.get(t["professor_nome"])
        disc_id = mapa_disc.get(t["disciplina_codigo"])

        if not prof_id or not disc_id:
            continue

        chave = (prof_id, disc_id, t["ano"], t["periodo"])

        if chave in vistos:
            continue

        vistos.add(chave)
        payload.append({
            "professor_id": prof_id,
            "disciplina_id": disc_id,
            "ano": t["ano"],
            "periodo": t["periodo"],
        })

    return payload
