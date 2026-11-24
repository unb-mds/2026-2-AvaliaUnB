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
class TestFiltrosAvancadosRotasENavegacao(BaseFiltrosAvancados):
    def html(self, caminho):
        resposta = self.web.get(caminho)
        self.assertEqual(resposta.status_code, 200, caminho)
        return resposta.get_data(as_text=True)

    def test_filtra_isoladamente_e_mantem_valores_preenchidos_na_tela(self):
        html_min = self.html('/professores?nota_min=4.0')
        self.assertIn('JOSÉ ÁVILA', html_min)
        self.assertNotIn('MARIA LIMA', html_min)
        self.assertRegex(html_min, r'<input[^>]*name="nota_min"[^>]*value="4\.0"')
        self.assertIn('Filtrando por nota mínima “4.0”', html_min)

        html_max = self.html('/professores?nota_max=3.5')
        self.assertIn('MARIA LIMA', html_max)
        self.assertNotIn('JOSÉ ÁVILA', html_max)
        self.assertRegex(html_max, r'<input[^>]*name="nota_max"[^>]*value="3\.5"')

        html_qtd = self.html('/professores?avaliacoes_min=5')
        self.assertIn('JOSÉ ÁVILA', html_qtd)
        self.assertNotIn('MARIA LIMA', html_qtd)
        self.assertRegex(html_qtd, r'<input[^>]*name="avaliacoes_min"[^>]*value="5"')

    def test_combina_filtros_avancados_com_busca_e_departamento_nos_formularios(self):
        html = self.html('/professores?q=jose&departamento=FCTE&nota_min=4.0&nota_max=5.0&avaliacoes_min=5')
        self.assertIn('1 professor encontrado', html)
        self.assertIn('JOSÉ ÁVILA', html)
        self.assertNotIn('MARIA LIMA', html)

        busca = re.search(r'<form[^>]*busca-unificada[^>]*>(.*?)</form>', html, re.S).group(1)
        for campo, valor in (('departamento', 'FCTE'), ('nota_min', '4.0'),
                             ('nota_max', '5.0'), ('avaliacoes_min', '5')):
            self.assertRegex(busca, rf'<input type="hidden" name="{campo}" value="{re.escape(valor)}">')

        filtros = re.search(r'<form[^>]*filtro-avancado-consulta[^>]*>(.*?)</form>', html, re.S).group(1)
        self.assertIn('<input type="hidden" name="q" value="jose">', filtros)

    def test_navegacao_de_retorno_do_perfil_mantem_os_filtros(self):
        url_consulta = '/professores?departamento=FCTE&nota_min=4.0&nota_max=5.0&avaliacoes_min=5'
        html_lista = self.html(url_consulta)
        link_perfil = html_lib.unescape(
            re.search(r'<h2><a href="([^"]+)">JOSÉ ÁVILA</a></h2>', html_lista).group(1)
        )
        next_param = parse_qs(urlparse(link_perfil).query)['next'][0]
        self.assertEqual(unquote(next_param), url_consulta)

        html_perfil = self.html(link_perfil)
        link_voltar = html_lib.unescape(
            re.search(r'<a class="profile-back" href="([^"]+)">', html_perfil).group(1)
        )
        self.assertEqual(link_voltar, url_consulta)

        html_retorno = self.html(link_voltar)
        self.assertIn('JOSÉ ÁVILA', html_retorno)
        self.assertNotIn('MARIA LIMA', html_retorno)

    def test_paginacao_preserva_filtros_avancados(self):
        for i in range(205):
            pid = 100 + i
            self.cliente.tabelas['professores'].append(
                {'id': pid, 'nome': f'DOCENTE EXTRA {i:03d}', 'departamento': 'FCTE'})
            self.avaliar(pid, 10, 3, 3, 3, 3, 3, didatica=5, clareza=5, organizacao=5, disponibilidade=5)
        self.app.extensions['repositorios'].professores.invalidar_cache()

        html = self.html('/professores?nota_min=4.0&avaliacoes_min=5&pagina=2')
        proxima = html_lib.unescape(re.search(r'<a [^>]*rel="next" href="([^"]+)"', html).group(1))
        anterior = html_lib.unescape(re.search(r'<a [^>]*rel="prev" href="([^"]+)"', html).group(1))
        self.assertIn('nota_min=4.0', proxima)
        self.assertIn('avaliacoes_min=5', proxima)
        self.assertIn('nota_min=4.0', anterior)
        self.assertIn('avaliacoes_min=5', anterior)

if __name__ == '__main__':
    unittest.main()