"""Importador em grafia comum (issue #236): o mesmo texto convertido em todo o fluxo."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

from persistencia_sigaa import salvar_disciplinas, salvar_professores, salvar_turmas
from texto_sigaa import (
    UnidadeInvalidaError,
    departamento_da_unidade,
    disciplina_do_titulo,
    docentes_em_grafia_comum,
    professores_em_varias_unidades,
)
from turmas_sigaa import registrar_docentes_da_linha
from tests.fake_supabase import ClienteFalso

UNIDADE = "CAMPUS UNB GAMA: FACULDADE DE CIÊNCIAS E TECNOLOGIAS EM ENGENHARIA - BRASÍLIA"
UNIDADE_CONVERTIDA = "Campus UnB Gama: Faculdade de Ciências e Tecnologias em Engenharia - Brasília"


def cliente_vazio():
    cliente = ClienteFalso()
    for tabela in ("professores", "disciplinas", "turmas"):
        cliente.tabelas[tabela].clear()
    return cliente


def extrair(celulas, titulo="FGA0100 - INTRODUÇÃO À FÍSICA II", unidade=UNIDADE):
    """Reproduz o que _extrair_tudo faz por linha, sem navegador."""
    departamento = departamento_da_unidade(unidade)
    disciplina = disciplina_do_titulo(titulo)
    professores, turmas = {}, []
    for bruto in celulas:
        docentes = docentes_em_grafia_comum(bruto)
        if docentes:
            registrar_docentes_da_linha(docentes, departamento, disciplina, 2026, 2,
                                        bruto, professores, turmas)
    return list(professores.values()), [disciplina], turmas


class TestConsistenciaEntreAsPontas(unittest.TestCase):
    def test_nome_da_turma_igual_a_chave_do_dicionario_e_ao_upsert(self):
        professores, disciplinas, turmas = extrair(
            ["MARIA DA COSTA (60h)", "JOÃO SILVA (30h), ARTHUR DE OLIVEIRA D'AREDE (30h)"])
        chaves = {p["nome"] for p in professores}
        self.assertEqual(chaves, {"Maria da Costa", "João Silva", "Arthur de Oliveira D'Arede"})
        self.assertEqual({t["professor_nome"] for t in turmas}, chaves)

        cliente = cliente_vazio()
        mapa_prof = salvar_professores(professores, cliente)
        self.assertEqual({p["nome"] for p in cliente.tabelas["professores"]}, chaves)
        self.assertEqual(set(mapa_prof), chaves)
        mapa_disc = salvar_disciplinas(disciplinas, cliente)
        salvar_turmas(turmas, mapa_prof, mapa_disc, cliente)
        self.assertEqual(len(cliente.tabelas["turmas"]), 3)  # nenhuma turma perdida por divergência

    def test_rodar_duas_vezes_nao_duplica_professores(self):
        cliente = cliente_vazio()
        for _ in range(2):
            professores, disciplinas, turmas = extrair(["MARIA DA COSTA (60h)"])
            mapa_prof = salvar_professores(professores, cliente)
            mapa_disc = salvar_disciplinas(disciplinas, cliente)
            salvar_turmas(turmas, mapa_prof, mapa_disc, cliente)
        self.assertEqual([p["nome"] for p in cliente.tabelas["professores"]], ["Maria da Costa"])
        self.assertEqual(len(cliente.tabelas["turmas"]), 1)

    def test_variantes_de_caixa_na_mesma_celula_viram_um_professor(self):
        self.assertEqual(docentes_em_grafia_comum("ANA LIMA (30h), Ana Lima (30h)"), ["Ana Lima"])


class TestADefinirDocente(unittest.TestCase):
    def test_placeholder_continua_descartado(self):
        self.assertEqual(docentes_em_grafia_comum("A DEFINIR DOCENTE (60h)"), [])
        self.assertEqual(docentes_em_grafia_comum("A DEFINIR DOCENTE, JOÃO SILVA (30h)"), ["João Silva"])
        professores, _, turmas = extrair(["A DEFINIR DOCENTE (60h)"])
        self.assertEqual((professores, turmas), ([], []))


class TestNomeJaEmGrafiaComum(unittest.TestCase):
    def test_professor_em_grafia_comum_permanece_igual(self):
        self.assertEqual(docentes_em_grafia_comum("Luciana Oliveira Militão (60h)"),
                         ["Luciana Oliveira Militão"])
        professores, _, turmas = extrair(["Luciana Oliveira Militão (60h)"])
        self.assertEqual(professores[0]["nome"], "Luciana Oliveira Militão")
        self.assertEqual(turmas[0]["professor_nome"], "Luciana Oliveira Militão")


class TestDisciplinaEDepartamento(unittest.TestCase):
    def test_disciplina_convertida_e_codigo_inalterado(self):
        disciplina = disciplina_do_titulo("FGA0100 - INTRODUÇÃO À FÍSICA II")
        self.assertEqual(disciplina, {"codigo": "FGA0100", "nome": "Introdução à Física II"})
        self.assertEqual(disciplina_do_titulo("  MAT0025 - TÓPICOS - A TV  ")["codigo"], "MAT0025")
        self.assertEqual(disciplina_do_titulo("  MAT0025 - TÓPICOS - A TV  ")["nome"], "Tópicos - A TV")

    def test_titulo_sem_separador_devolve_none(self):
        self.assertIsNone(disciplina_do_titulo("SEM SEPARADOR"))
        self.assertIsNone(disciplina_do_titulo(None))

    def test_departamento_convertido_e_ainda_validado(self):
        self.assertEqual(departamento_da_unidade(UNIDADE), UNIDADE_CONVERTIDA)
        self.assertEqual(departamento_da_unidade("  INSTITUTO\xa0DE ARTES - BRASÍLIA "),
                         "Instituto de Artes - Brasília")
        with self.assertRaises(UnidadeInvalidaError):
            departamento_da_unidade("-- SELECIONE --")

    def test_departamento_e_disciplina_chegam_convertidos_ao_banco(self):
        professores, disciplinas, turmas = extrair(["ANA LIMA (30h)"])
        cliente = cliente_vazio()
        salvar_professores(professores, cliente)
        salvar_disciplinas(disciplinas, cliente)
        self.assertEqual(cliente.tabelas["professores"][0]["departamento"], UNIDADE_CONVERTIDA)
        disc = cliente.tabelas["disciplinas"][0]
        self.assertEqual((disc["codigo"], disc["nome"]), ("FGA0100", "Introdução à Física II"))

    def test_comparacao_entre_unidades_continua_funcionando(self):
        a, _, _ = extrair(["ANA LIMA (30h)"], unidade=UNIDADE)
        b, _, _ = extrair(["ANA LIMA (30h)"], unidade="INSTITUTO DE ARTES - BRASÍLIA")
        em_varias = professores_em_varias_unidades(a + b)
        self.assertEqual(list(em_varias), ["ANA LIMA"])
        self.assertEqual(len(em_varias["ANA LIMA"]), 2)


if __name__ == "__main__":
    unittest.main()
