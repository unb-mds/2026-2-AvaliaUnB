"""Reações aos comentários (issue #212)."""
import unittest

from flask_wtf.csrf import generate_csrf

from app import create_app
from app.repositorio import ReacaoRepository
from tests.fake_supabase import ClienteFalso, entrar_pela_web


class TestReacoes(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'testes-reacoes',
                               'SUPABASE_CLIENT': self.cliente})
        self.app.add_url_rule('/teste/csrf', 'teste_csrf', generate_csrf)
        self.autora = self.app.test_client()
        self.web = self.app.test_client()
        entrar_pela_web(self.autora, self.cliente, 'ana@gmail.com', 'Ana')
        entrar_pela_web(self.web, self.cliente, 'bia@gmail.com', 'Bia')
        self.ana = next(u['id'] for u in self.cliente.auth.usuarios.values() if u['email'] == 'ana@gmail.com')
        self.bia = next(u['id'] for u in self.cliente.auth.usuarios.values() if u['email'] == 'bia@gmail.com')
        self.cliente.tabelas['comentarios'].append({
            'id': 1, 'usuario_id': self.ana, 'professor_id': 1, 'disciplina_id': 10,
            'texto': 'Comentário de teste', 'criado_em': '2026-03-01T10:00:00+00:00',
            'atualizado_em': '2026-03-01T10:00:00+00:00', 'ocultado_em': None})
        self.repo = ReacaoRepository(self.cliente)

    def post(self, valor, web=None, csrf=True, cid=1):
        web = web or self.web
        dados = {'valor': valor, 'comentarios_disciplina': 10, 'usuario_id': self.ana}
        if csrf:
            dados['csrf_token'] = web.get('/teste/csrf').get_data(as_text=True)
        return web.post(f'/comentarios/{cid}/reacao', data=dados)

    def test_reagir_trocar_repetir_remover(self):
        self.assertEqual(self.post(1).status_code, 303)
        self.assertEqual(self.post(1).status_code, 303)
        self.assertEqual(self.repo.resumo([1], self.bia)[1],
                         {'curtidas': 1, 'descurtidas': 0, 'minha_reacao': 1})
        self.assertEqual(self.post(-1).status_code, 303)
        self.assertEqual(self.repo.resumo([1], self.bia)[1],
                         {'curtidas': 0, 'descurtidas': 1, 'minha_reacao': -1})
        self.assertEqual(self.post(0).status_code, 303)
        self.assertEqual(self.cliente.tabelas['comentarios_reacoes'], [])

    def test_regras_de_acesso_e_validacao(self):
        self.assertEqual(self.post(1, self.autora).status_code, 404)
        self.assertEqual(self.post(2).status_code, 400)
        self.assertEqual(self.post(1, csrf=False).status_code, 400)
        self.assertEqual(self.post(1, cid=99).status_code, 404)
        self.assertEqual(self.post(1, self.app.test_client()).status_code, 302)
        self.assertEqual(self.web.get('/comentarios/1/reacao').status_code, 405)
        self.assertEqual(self.cliente.tabelas['comentarios_reacoes'], [])
        self.cliente.tabelas['comentarios'][0]['ocultado_em'] = '2026-04-01'
        self.assertEqual(self.post(1).status_code, 404)

    def test_template_visitante_autora_e_reacao_selecionada(self):
        visitante = self.app.test_client()
        html = visitante.get('/professores/1').get_data(as_text=True)
        self.assertIn('Entrar para curtir', html)
        self.assertIn('class="reacao-icone"', html)
        self.assertIn('reacao-icone-negativa', html)
        self.assertIn('Entrar para descurtir', html)
        self.assertEqual(self.post(1).status_code, 303)
        html = self.web.get('/professores/1').get_data(as_text=True)
        self.assertIn('aria-pressed="true"', html)
        self.assertIn('aria-label="Curtir (1)" aria-pressed="true"', html)
        html = self.autora.get('/professores/1').get_data(as_text=True)
        self.assertIn('class="reacao reacao-leitura" aria-label="Curtir: 1"', html)
        self.assertNotIn('/comentarios/1/reacao', html)
        self.assertNotIn(self.bia, html)

    def test_contagem_paginada(self):
        self.cliente.tabelas['comentarios_reacoes'] = [
            {'comentario_id': 1, 'usuario_id': str(i), 'valor': 1 if i % 2 else -1}
            for i in range(1001)]
        self.assertEqual(self.repo.resumo([1], '0')[1],
                         {'curtidas': 500, 'descurtidas': 501, 'minha_reacao': -1})
