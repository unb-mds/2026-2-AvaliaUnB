"""Nomes em grafia comum no app (issue #236): ordenação e iniciais do avatar."""
import re
import unittest

from app import create_app
from app.repositorio import ProfessorRepository
from app.utils import iniciais
from tests.fake_supabase import ClienteFalso

NOMES = ["Beatriz Moura", "Ana Dias", "Ana de Souza", "Álvaro Lima"]
ORDEM_ESPERADA = ["Álvaro Lima", "Ana de Souza", "Ana Dias", "Beatriz Moura"]
DISCIPLINAS = [(10, "FGA0010", "Cálculo 1"), (11, "FGA0011", "Banco de Dados"),
               (12, "FGA0012", "Álgebra Linear"), (13, "FGA0013", "Estruturas de Dados")]
DISCIPLINAS_ESPERADAS = ["Álgebra Linear", "Banco de Dados", "Cálculo 1", "Estruturas de Dados"]


def montar_cliente():
    cliente = ClienteFalso()
    cliente.tabelas["professores"] = [
        {"id": i, "nome": nome, "departamento": "Instituto de Artes - Brasília"}
        for i, nome in enumerate(NOMES, 1)]
    cliente.tabelas["vw_professor_disciplina"] = [
        {"professor_id": i, "professor": nome, "departamento": "Instituto de Artes - Brasília",
         "disciplina_id": d_id, "codigo_disciplina": codigo, "disciplina": d_nome,
         "ano": 2026, "periodo": 1}
        for i, nome in enumerate(NOMES, 1) for d_id, codigo, d_nome in DISCIPLINAS]
    return cliente


class BaseApp(unittest.TestCase):
    def setUp(self):
        self.cliente = montar_cliente()
        self.app = create_app({"TESTING": True, "SECRET_KEY": "chave-exclusiva-dos-testes",
                               "SUPABASE_CLIENT": self.cliente})
        self.web = self.app.test_client()

    def html(self, caminho):
        resposta = self.web.get(caminho, headers={"Accept": "text/html"})
        self.assertEqual(resposta.status_code, 200)
        return resposta.get_data(as_text=True)


def posicoes(html, textos):
    achados = [html.find(f">{t}<") if f">{t}<" in html else html.find(t) for t in textos]
    assert all(p >= 0 for p in achados), (textos, achados)
    return achados


class TestOrdenacaoPorNome(BaseApp):
    def test_repositorio_ordena_professores_e_disciplinas_sem_diferenciar_caixa_e_acento(self):
        repo = ProfessorRepository(self.cliente)
        self.assertEqual([p["nome"] for p, _ in repo.catalogo()], ORDEM_ESPERADA)
        self.assertEqual([d["nome"] for d in repo.listar_disciplinas(1)], DISCIPLINAS_ESPERADAS)

    def test_lista_de_professores_ordena_por_nome_em_grafia_comum(self):
        html = self.html("/professores")
        ordem = sorted(ORDEM_ESPERADA, key=lambda n: html.find(f">{n}</a>"))
        self.assertTrue(all(f">{n}</a>" in html for n in ORDEM_ESPERADA))
        self.assertEqual(ordem, ORDEM_ESPERADA)

    def test_comparacao_lista_os_professores_em_ordem_de_nome(self):
        html = self.html("/comparar?modo=livre")
        achados = {n: re.search(rf">\s*{re.escape(n)}", html) for n in ORDEM_ESPERADA}
        self.assertTrue(all(achados.values()), achados)
        ordem = sorted(ORDEM_ESPERADA, key=lambda n: achados[n].start())
        self.assertEqual(ordem, ORDEM_ESPERADA)

    def test_perfil_do_professor_lista_as_disciplinas_em_ordem_de_nome(self):
        html = self.html("/professores/1")
        nomes = [d for d in DISCIPLINAS_ESPERADAS if re.search(rf">\s*{re.escape(d)}", html)]
        self.assertEqual(nomes, DISCIPLINAS_ESPERADAS)
        ordem = sorted(DISCIPLINAS_ESPERADAS,
                       key=lambda d: re.search(rf">\s*{re.escape(d)}", html).start())
        self.assertEqual(ordem, DISCIPLINAS_ESPERADAS)

    def test_comparacao_lista_as_disciplinas_em_ordem_de_nome(self):
        html = self.html("/comparar")
        ordem = sorted(DISCIPLINAS_ESPERADAS,
                       key=lambda d: re.search(rf">\s*{re.escape(d)}", html).start())
        self.assertEqual(ordem, DISCIPLINAS_ESPERADAS)


class TestIniciais(unittest.TestCase):
    def test_casos_pedidos(self):
        casos = {
            "João de Souza": "JS",
            "Maria da Costa Lima": "MC",
            "Álvaro": "Á",
            "": "",
            None: "",
            "JOSÉ ÁVILA": "JÁ",
        }
        for nome, esperado in casos.items():
            with self.subTest(nome=nome):
                self.assertEqual(iniciais(nome), esperado)

    def test_particulas_ignoradas_em_qualquer_posicao_inicial(self):
        self.assertEqual(iniciais("de Souza"), "S")
        self.assertEqual(iniciais("Maria dos Santos e Silva"), "MS")
        self.assertEqual(iniciais("Paulo di Pietro"), "PP")
        self.assertEqual(iniciais("Carlos von Braun"), "CB")
        self.assertEqual(iniciais("   "), "")
        self.assertEqual(iniciais("de da"), "")

    def test_filtro_registrado_no_app_e_usado_nos_templates(self):
        app = create_app({"TESTING": True, "SECRET_KEY": "chave-exclusiva-dos-testes",
                          "SUPABASE_CLIENT": montar_cliente()})
        self.assertIs(app.jinja_env.filters["iniciais"], iniciais)
        html = app.test_client().get("/professores", headers={"Accept": "text/html"}).get_data(as_text=True)
        self.assertIn('aria-hidden="true">ÁL</div>', html)
        self.assertIn('aria-hidden="true">AS</div>', html)  # Ana de Souza
        self.assertIn('aria-hidden="true">AD</div>', html)  # Ana Dias
        self.assertIn('aria-hidden="true">BM</div>', html)


if __name__ == "__main__":
    unittest.main()
