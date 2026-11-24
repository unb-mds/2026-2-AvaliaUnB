"""Filtros avançados na Consulta: faixa de nota e quantidade mínima de avaliações (issue #221)."""
import html as html_lib
import re
import unittest
from urllib.parse import parse_qs, unquote, urlparse

from app.controllers import professor_controller as controller
from tests.test_dificuldade_consulta import BaseConsulta


class BaseFiltrosAvancados(BaseConsulta):
    def setUp(self):
        super().setUp()
        self.web = self.app.test_client()
        # Professor 1 (JOSÉ ÁVILA): 5 avaliações com média 4,50
        self.avaliar(1, 10, 3, 3, 3, didatica=5, clareza=5, organizacao=4, disponibilidade=4)
        self.avaliar(1, 10, 3, 3, didatica=5, clareza=4, organizacao=5, disponibilidade=4)
        # Professor 2 (MARIA LIMA): 2 avaliações com média 3,00
        self.avaliar(2, 20, 4, 4, didatica=3, clareza=3, organizacao=3, disponibilidade=3)
        # Professor 3: 0 avaliações (sem média)

    def ids_catalogo(self, **filtros):
        repos = self.app.extensions['repositorios']
        return [p['id'] for p, _ in repos.professores.catalogo(**filtros)]


class TestFiltrosAvancadosRepositorioEController(BaseFiltrosAvancados):
    def test_filtra_por_nota_minima_e_exclui_sem_avaliacoes(self):
        self.assertEqual(self.ids_catalogo(nota_minima=4.0), [1])
        self.assertEqual(self.ids_catalogo(nota_minima=4.5), [1])
        self.assertEqual(self.ids_catalogo(nota_minima=4.51), [])

    def test_filtra_por_nota_maxima_e_exclui_sem_avaliacoes(self):
        self.assertEqual(self.ids_catalogo(nota_maxima=3.5), [2])
        self.assertEqual(self.ids_catalogo(nota_maxima=3.0), [2])
        self.assertEqual(self.ids_catalogo(nota_maxima=2.99), [])

    def test_filtra_por_faixa_de_nota_combinada(self):
        self.assertEqual(self.ids_catalogo(nota_minima=3.0, nota_maxima=4.5), [1, 2])
        self.assertEqual(self.ids_catalogo(nota_minima=4.8, nota_maxima=4.0), [])

    def test_filtra_por_avaliacoes_minimas(self):
        self.assertEqual(self.ids_catalogo(avaliacoes_minimas=3), [1])
        self.assertEqual(self.ids_catalogo(avaliacoes_minimas=2), [1, 2])
        self.assertEqual(self.ids_catalogo(avaliacoes_minimas=6), [])

    def test_filtros_combinados_nao_fazem_consultas_extras_por_professor(self):
        self.cliente.consultas_avaliacoes = 0
        ids = self.ids_catalogo(departamento='FCTE', nota_minima=4.0, nota_maxima=5.0,
                                avaliacoes_minimas=5)
        self.assertEqual(ids, [1])
        self.assertEqual(self.cliente.consultas_avaliacoes, 1)

    def test_controller_normaliza_virgula_ponto_e_ignora_entradas_invalidas(self):
        with self.app.app_context():
            self.assertEqual([p['id'] for p, _ in controller.catalogo(nota_min='4,5')], [1])
            self.assertEqual([p['id'] for p, _ in controller.catalogo(nota_max='3,0')], [2])
            self.assertEqual([p['id'] for p, _ in controller.catalogo(avaliacoes_min='5')], [1])
            for invalidos in (
                {'nota_min': 'abc'},
                {'nota_min': '-1'},
                {'nota_max': '9'},
                {'avaliacoes_min': '0'},
                {'avaliacoes_min': '-4'},
                {'avaliacoes_min': 'xyz'},
            ):
                with self.subTest(invalidos=invalidos):
                    self.assertEqual([p['id'] for p, _ in controller.catalogo(**invalidos)],
                                     [1, 2, 3])


if __name__ == '__main__':
    unittest.main()