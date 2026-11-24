"""Subcomando converter-nomes (issue #236), só com o cliente falso."""
import copy
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

import manutencao_banco
from manutencao_banco import aplicar_conversao, main, planejar_conversao
from tests.fake_supabase import ClienteFalso

UNIDADE = "CAMPUS UNB GAMA: FACULDADE DE CIÊNCIAS E TECNOLOGIAS EM ENGENHARIA - BRASÍLIA"
UNIDADE_CONVERTIDA = "Campus UnB Gama: Faculdade de Ciências e Tecnologias em Engenharia - Brasília"


def cliente_com(professores=None, disciplinas=None):
    cliente = ClienteFalso()
    cliente.tabelas["professores"] = professores if professores is not None else [
        {"id": 1, "nome": "MARIA DA COSTA", "departamento": UNIDADE},
        {"id": 2, "nome": "JOÃO SILVA", "departamento": "INSTITUTO DE ARTES - BRASÍLIA"},
        {"id": 3, "nome": "Luciana Oliveira Militão", "departamento": "Instituto de Artes - Brasília"},
    ]
    cliente.tabelas["disciplinas"] = disciplinas if disciplinas is not None else [
        {"id": 10, "codigo": "FGA0100", "nome": "INTRODUÇÃO À FÍSICA II"},
        {"id": 11, "codigo": "MAT0025", "nome": "Cálculo 1"},
    ]
    return cliente


def rodar(argv, cliente):
    saida = io.StringIO()
    with redirect_stdout(saida):
        codigo = main(argv, cliente=cliente)
    return codigo, saida.getvalue()


class ClienteQueFalha(ClienteFalso):
    """Falha na atualização de número `falhar_na` (1, 2, 3...)."""

    def __init__(self, falhar_na):
        super().__init__()
        self.falhar_na, self.atualizacoes = falhar_na, 0

    def table(self, nome):
        consulta = super().table(nome)
        executar = consulta.execute
        cliente = self

        def execute():
            if consulta.atualizacao is not None:
                cliente.atualizacoes += 1
                if cliente.atualizacoes == cliente.falhar_na:
                    raise RuntimeError("falha simulada do banco")
            return executar()

        consulta.execute = execute
        return consulta


class TestSimulacao(unittest.TestCase):
    def test_simulacao_e_o_padrao_e_nao_grava(self):
        cliente = cliente_com()
        antes = copy.deepcopy(cliente.tabelas)
        codigo, saida = rodar(["converter-nomes"], cliente)
        self.assertEqual(codigo, 0)
        self.assertEqual(cliente.tabelas, antes)
        self.assertIn("Simulação: nada foi gravado", saida)

    def test_mostra_totais_e_exemplos_por_campo(self):
        _, saida = rodar(["converter-nomes"], cliente_com())
        self.assertIn("professores.nome: 3 registro(s) | mudariam: 2 | já corretos: 1", saida)
        self.assertIn("professores.departamento: 3 registro(s) | mudariam: 2 | já corretos: 1", saida)
        self.assertIn("disciplinas.nome: 2 registro(s) | mudariam: 1 | já corretos: 1", saida)
        self.assertIn("'MARIA DA COSTA' -> 'Maria da Costa'", saida)
        self.assertIn(f"{UNIDADE!r} -> {UNIDADE_CONVERTIDA!r}", saida)
        self.assertIn("'INTRODUÇÃO À FÍSICA II' -> 'Introdução à Física II'", saida)

    def test_limita_a_dez_exemplos_por_campo(self):
        professores = [{"id": i, "nome": f"PROFESSOR {i}", "departamento": ""} for i in range(1, 41)]
        _, saida = rodar(["converter-nomes"], cliente_com(professores, []))
        self.assertEqual(saida.count("'PROFESSOR "), 10)

    def test_avisa_do_backup_e_do_importador_em_simulacao_e_ao_gravar(self):
        for argv in (["converter-nomes"], ["converter-nomes", "--gravar"]):
            with self.subTest(argv=argv):
                _, saida = rodar(argv, cliente_com())
                self.assertIn("Rode o backup antes de gravar", saida)
                self.assertIn("só use o importador novo depois da conversão", saida)


class TestGravacao(unittest.TestCase):
    def test_gravar_converte_professores_e_disciplinas_por_id(self):
        cliente = cliente_com()
        codigo, saida = rodar(["converter-nomes", "--gravar"], cliente)
        self.assertEqual(codigo, 0)
        profs = {p["id"]: p for p in cliente.tabelas["professores"]}
        self.assertEqual(profs[1]["nome"], "Maria da Costa")
        self.assertEqual(profs[1]["departamento"], UNIDADE_CONVERTIDA)
        self.assertEqual(profs[2]["nome"], "João Silva")
        self.assertEqual(profs[2]["departamento"], "Instituto de Artes - Brasília")
        discs = {d["id"]: d for d in cliente.tabelas["disciplinas"]}
        self.assertEqual(discs[10]["nome"], "Introdução à Física II")
        self.assertIn("professores.nome: 2 atualizado(s)", saida)
        self.assertIn("professores.departamento: 2 atualizado(s)", saida)
        self.assertIn("disciplinas.nome: 1 atualizado(s)", saida)

    def test_registros_ja_em_grafia_comum_nao_mudam(self):
        cliente = cliente_com()
        rodar(["converter-nomes", "--gravar"], cliente)
        luciana = next(p for p in cliente.tabelas["professores"] if p["id"] == 3)
        self.assertEqual(luciana, {"id": 3, "nome": "Luciana Oliveira Militão",
                                   "departamento": "Instituto de Artes - Brasília"})
        calculo = next(d for d in cliente.tabelas["disciplinas"] if d["id"] == 11)
        self.assertEqual(calculo["nome"], "Cálculo 1")

    def test_codigo_da_disciplina_nunca_muda(self):
        cliente = cliente_com()
        rodar(["converter-nomes", "--gravar"], cliente)
        self.assertEqual([d["codigo"] for d in cliente.tabelas["disciplinas"]], ["FGA0100", "MAT0025"])

    def test_idempotencia_segunda_execucao_nao_altera_nada(self):
        cliente = cliente_com()
        rodar(["converter-nomes", "--gravar"], cliente)
        depois_da_primeira = copy.deepcopy(cliente.tabelas)
        codigo, saida = rodar(["converter-nomes", "--gravar"], cliente)
        self.assertEqual(codigo, 0)
        self.assertEqual(cliente.tabelas, depois_da_primeira)
        self.assertIn("Nada a converter", saida)
        plano = planejar_conversao(cliente)
        self.assertEqual([len(c["mudancas"]) for c in plano["campos"]], [0, 0, 0])

    def test_atualiza_so_os_campos_que_mudaram(self):
        professores = [{"id": 1, "nome": "Ana Lima", "departamento": "INSTITUTO DE ARTES - BRASÍLIA"}]
        cliente = cliente_com(professores, [])
        _, saida = rodar(["converter-nomes", "--gravar"], cliente)
        self.assertEqual(cliente.tabelas["professores"][0],
                         {"id": 1, "nome": "Ana Lima", "departamento": "Instituto de Artes - Brasília"})
        self.assertIn("professores.nome: 0 atualizado(s)", saida)

    def test_registro_alterado_durante_a_conversao_e_pulado(self):
        cliente = cliente_com()
        plano = planejar_conversao(cliente)
        cliente.tabelas["professores"][0]["nome"] = "OUTRA PESSOA"  # mudou depois da leitura
        with redirect_stdout(io.StringIO()):
            resultado = aplicar_conversao(cliente, plano)
        self.assertEqual(resultado["pulados"], 1)
        self.assertEqual(cliente.tabelas["professores"][0]["nome"], "OUTRA PESSOA")
        self.assertEqual(cliente.tabelas["professores"][1]["nome"], "João Silva")


class TestColisoes(unittest.TestCase):
    def conferir_aborto(self, professores):
        cliente = cliente_com(professores, [{"id": 10, "codigo": "FGA0100", "nome": "REDES"}])
        antes = copy.deepcopy(cliente.tabelas)
        for argv in (["converter-nomes"], ["converter-nomes", "--gravar"]):
            with self.subTest(argv=argv):
                codigo, saida = rodar(argv, cliente)
                self.assertEqual(codigo, 1)
                self.assertEqual(cliente.tabelas, antes)  # nada gravado, nem disciplinas
                self.assertIn("NADA foi gravado", saida)
        return saida

    def test_nome_convertido_igual_a_outro_nome_existente_aborta(self):
        saida = self.conferir_aborto([
            {"id": 1, "nome": "ANA LIMA", "departamento": ""},
            {"id": 2, "nome": "Ana Lima", "departamento": ""},
        ])
        self.assertIn("#1 'ANA LIMA' <-> #2 'Ana Lima'", saida)

    def test_colisao_por_normalizar_chave_aborta(self):
        saida = self.conferir_aborto([
            {"id": 1, "nome": "JOSÉ ÁVILA", "departamento": ""},
            {"id": 2, "nome": "Jose  Avila", "departamento": ""},
        ])
        self.assertIn("#1", saida)
        self.assertIn("#2", saida)

    def test_dois_nomes_que_viram_o_mesmo_texto_abortam(self):
        self.conferir_aborto([
            {"id": 1, "nome": "ANA LIMA", "departamento": ""},
            {"id": 2, "nome": "ANA  LIMA", "departamento": ""},
        ])

    def test_duplicata_antiga_entre_registros_intactos_nao_bloqueia(self):
        cliente = cliente_com([
            {"id": 1, "nome": "Ana Lima", "departamento": ""},
            {"id": 2, "nome": "ana lima", "departamento": ""},
            {"id": 3, "nome": "BRUNO SOUZA", "departamento": ""},
        ], [])
        codigo, _ = rodar(["converter-nomes", "--gravar"], cliente)
        self.assertEqual(codigo, 0)
        self.assertEqual(cliente.tabelas["professores"][2]["nome"], "Bruno Souza")

    def test_disciplinas_que_so_diferem_por_acento_sao_informativas(self):
        cliente = cliente_com([], [
            {"id": 10, "codigo": "FGA0001", "nome": "MECÂNICA 1"},
            {"id": 11, "codigo": "MAT0001", "nome": "MECANICA 1"},
        ])
        codigo, saida = rodar(["converter-nomes", "--gravar"], cliente)
        self.assertEqual(codigo, 0)
        self.assertIn("só diferem por acento depois da conversão: 1 grupo(s)", saida)
        self.assertEqual([d["nome"] for d in cliente.tabelas["disciplinas"]],
                         ["Mecânica 1", "Mecanica 1"])


class TestPaginacaoEFalha(unittest.TestCase):
    def test_le_e_converte_mais_de_mil_registros(self):
        professores = [{"id": i, "nome": f"PROFESSOR {i}", "departamento": ""} for i in range(1, 1206)]
        self.assertGreater(len(professores), manutencao_banco.PAGINA)
        cliente = cliente_com(professores, [])
        codigo, saida = rodar(["converter-nomes", "--gravar"], cliente)
        self.assertEqual(codigo, 0)
        self.assertIn("professores.nome: 1205 registro(s) | mudariam: 1205", saida)
        self.assertEqual(cliente.tabelas["professores"][-1]["nome"], "Professor 1205")
        self.assertTrue(all(p["nome"].startswith("Professor ") for p in cliente.tabelas["professores"]))
        self.assertIn("Progresso: 1205/1205", saida)

    def test_falha_no_meio_informa_o_progresso_e_reexecutar_e_seguro(self):
        cliente = ClienteQueFalha(falhar_na=3)
        cliente.tabelas["professores"] = [
            {"id": i, "nome": f"PROFESSOR {i}", "departamento": ""} for i in range(1, 6)]
        cliente.tabelas["disciplinas"] = []
        codigo, saida = rodar(["converter-nomes", "--gravar"], cliente)
        self.assertEqual(codigo, 1)
        self.assertEqual([p["nome"] for p in cliente.tabelas["professores"]],
                         ["Professor 1", "Professor 2", "PROFESSOR 3", "PROFESSOR 4", "PROFESSOR 5"])
        self.assertIn("Falha ao atualizar professores #3", saida)
        self.assertIn("2 campo(s) já gravado(s)", saida)
        self.assertIn("Reexecutar é seguro", saida)

        cliente.falhar_na = None  # a nova execução termina o trabalho
        codigo, _ = rodar(["converter-nomes", "--gravar"], cliente)
        self.assertEqual(codigo, 0)
        self.assertEqual([p["nome"] for p in cliente.tabelas["professores"]],
                         [f"Professor {i}" for i in range(1, 6)])


if __name__ == "__main__":
    unittest.main()
