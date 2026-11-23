"""Filtro automático nas rotas de publicar e editar comentário (issue #214)."""
import logging
import unittest

from flask_wtf.csrf import generate_csrf

from app import create_app
from app.seguranca import limiter
from tests.fake_supabase import ClienteFalso, entrar_pela_web

TEXTO_BLOQUEADO = {
    'telefone': ('Me liga no (61) 99999-1234 que eu explico', 'dados pessoais'),
    'email': ('escreve para zeca.silva@gmail.com', 'dados pessoais'),
    'link': ('mais detalhes em www.exemplo.xyz/aula', 'contém um link'),
    'ofensa': ('esse professor é um idiota', 'linguagem ofensiva'),
}
TRECHOS = ('99999-1234', 'zeca.silva', 'exemplo.xyz', 'idiota')


class BaseRotas(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})
        limiter.reset()
        self.app.add_url_rule('/teste/csrf', 'teste_csrf', generate_csrf)
        self.web = self.app.test_client()
        entrar_pela_web(self.web, self.cliente, 'ana@gmail.com', 'Ana')
        self.ana = next(u['id'] for u in self.cliente.auth.usuarios.values()
                        if u['email'] == 'ana@gmail.com')

    def enviar(self, caminho, dados):
        dados = {**dados, 'csrf_token': self.web.get('/teste/csrf').get_data(as_text=True)}
        return self.web.post(caminho, data=dados, headers={'Accept': 'text/html'})

    def publicar(self, texto):
        return self.enviar('/professores/1/comentarios', {'disciplina_id': '10', 'texto': texto})

    def semear(self, texto='texto original'):
        self.cliente.tabelas['comentarios'].append({
            'id': 1, 'usuario_id': self.ana, 'professor_id': 1, 'disciplina_id': 10,
            'texto': texto, 'criado_em': '2026-03-01T10:00:01+00:00',
            'atualizado_em': '2026-03-01T10:00:01+00:00', 'ocultado_em': None})

    def editar(self, texto):
        return self.enviar('/comentarios/1/editar', {'disciplina_id': '10', 'texto': texto})


class TestPublicar(BaseRotas):
    def test_bloqueado_nao_grava_preserva_texto_e_mostra_a_mensagem(self):
        for nome, (texto, categoria) in TEXTO_BLOQUEADO.items():
            with self.subTest(categoria=nome):
                resposta = self.publicar(texto)
                html = resposta.get_data(as_text=True)
                self.assertEqual(resposta.status_code, 400)
                self.assertEqual(self.cliente.tabelas['comentarios'], [])
                self.assertIn('Seu comentário não foi publicado porque', html)
                self.assertIn(categoria, html)
                self.assertIn(f'>{texto}</textarea>', html)

    def test_mensagem_nao_contem_o_trecho_bloqueado(self):
        for texto, _ in TEXTO_BLOQUEADO.values():
            html = self.publicar(texto).get_data(as_text=True)
            inicio = html.index('Seu comentário não foi publicado')
            mensagem = html[inicio:html.index('</p>', inicio)]
            for trecho in TRECHOS:
                self.assertNotIn(trecho, mensagem)

    def test_texto_permitido_continua_publicando(self):
        resposta = self.publicar('Péssima didática, não recomendo. Cálculo 1, 2024.1, nota 8,5.')
        self.assertEqual(resposta.status_code, 303)
        self.assertEqual(len(self.cliente.tabelas['comentarios']), 1)

    def test_tamanho_tem_precedencia_sobre_o_filtro(self):
        resposta = self.publicar('a')
        self.assertIn('pelo menos', resposta.get_data(as_text=True))
        self.assertNotIn('não foi publicado', resposta.get_data(as_text=True))

    def test_log_nao_contem_o_texto(self):
        registros = []

        class Coletor(logging.Handler):
            def emit(self, registro):
                registros.append(registro.getMessage())

        coletor = Coletor(level=logging.DEBUG)
        raiz = logging.getLogger()
        nivel = raiz.level
        raiz.addHandler(coletor)
        raiz.setLevel(logging.DEBUG)
        self.app.logger.addHandler(coletor)
        try:
            for texto, _ in TEXTO_BLOQUEADO.values():
                self.publicar(texto)
        finally:
            raiz.removeHandler(coletor)
            raiz.setLevel(nivel)
            self.app.logger.removeHandler(coletor)
        for linha in registros:
            for trecho in TRECHOS:
                self.assertNotIn(trecho, linha)

    def test_envios_bloqueados_contam_no_limite_por_hora(self):
        # Comportamento atual mantido: o limitador conta toda requisição POST, bloqueada ou não.
        codigos = [self.publicar(TEXTO_BLOQUEADO['link'][0]).status_code for _ in range(11)]
        self.assertEqual(codigos[:10], [400] * 10)
        self.assertEqual(codigos[10], 429)


class TestEditar(BaseRotas):
    def test_bloqueado_nao_altera_o_comentario_e_preserva_o_texto_digitado(self):
        for nome, (texto, categoria) in TEXTO_BLOQUEADO.items():
            with self.subTest(categoria=nome):
                self.cliente.tabelas['comentarios'].clear()
                self.semear()
                resposta = self.editar(texto)
                html = resposta.get_data(as_text=True)
                self.assertEqual(resposta.status_code, 400)
                self.assertEqual(self.cliente.tabelas['comentarios'][0]['texto'], 'texto original')
                self.assertIn('Seu comentário não foi salvo porque', html)
                self.assertNotIn('não foi publicado', html)
                self.assertIn(categoria, html)
                self.assertIn(f'>{texto}</textarea>', html)
                inicio = html.index('Seu comentário não foi salvo')
                mensagem = html[inicio:html.index('</p>', inicio)]
                for trecho in TRECHOS:
                    self.assertNotIn(trecho, mensagem)

    def test_texto_permitido_continua_editando(self):
        self.semear()
        resposta = self.editar('Explica bem, mas as provas são longas. Nota 8,5.')
        self.assertEqual(resposta.status_code, 303)
        self.assertEqual(self.cliente.tabelas['comentarios'][0]['texto'],
                         'Explica bem, mas as provas são longas. Nota 8,5.')


if __name__ == '__main__':
    unittest.main()
