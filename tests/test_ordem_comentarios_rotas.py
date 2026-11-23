"""Ordem dos comentários no perfil do professor e nos fluxos que voltam a ele (issue #213)."""
import re
import unittest
from html import unescape
from urllib.parse import parse_qs, urlsplit

from flask_wtf.csrf import generate_csrf

from app import create_app
from app.repositorio import LIMITE_COMENTARIOS
from tests.fake_supabase import ClienteFalso, entrar_pela_web

ROTULOS = {'recentes': 'Mais recentes', 'antigos': 'Mais antigos',
           'curtidos': 'Mais curtidos', 'reacoes': 'Mais reações'}
FRASE_LIMITE = f'Mostrando os {LIMITE_COMENTARIOS} primeiros comentários.'
NOTAS = {'didatica': 4, 'clareza': 4, 'organizacao': 4, 'disponibilidade': 4, 'dificuldade': 3}


class BaseOrdemRotas(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.cliente.tabelas['vw_professor_disciplina'].append(
            {'professor_id': 1, 'disciplina_id': 11, 'codigo_disciplina': 'FGA0011',
             'disciplina': 'CÁLCULO 2', 'ano': 2026, 'periodo': 1})
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})
        self.app.add_url_rule('/teste/csrf', 'teste_csrf', generate_csrf)
        self.autora = self.app.test_client()
        self.web = self.app.test_client()
        self.ana = self.entrar(self.autora, 'ana@gmail.com', 'Ana')
        self.bia = self.entrar(self.web, 'bia@gmail.com', 'Bia')

    def entrar(self, web, email, nome):
        entrar_pela_web(web, self.cliente, email, nome)
        return next(u['id'] for u in self.cliente.auth.usuarios.values() if u['email'] == email)

    def semear(self, quantidade=1, usuario=None, disciplina=10):
        tabela = self.cliente.tabelas['comentarios']
        for _ in range(quantidade):
            n = len(tabela) + 1
            tabela.append({'id': n, 'usuario_id': usuario or self.ana, 'professor_id': 1,
                           'disciplina_id': disciplina, 'texto': f'texto-{n}',
                           'criado_em': f'2026-03-01T10:{n // 60:02d}:{n % 60:02d}+00:00',
                           'atualizado_em': f'2026-03-01T10:{n // 60:02d}:{n % 60:02d}+00:00',
                           'ocultado_em': None})

    def reagir(self, comentario_id, curtidas=0, descurtidas=0):
        tabela = self.cliente.tabelas['comentarios_reacoes']
        for i in range(curtidas + descurtidas):
            tabela.append({'comentario_id': comentario_id, 'valor': 1 if i < curtidas else -1,
                           'usuario_id': f'u{comentario_id}-{i}'})

    def ver(self, caminho, web=None):
        resposta = (web or self.web).get(caminho, headers={'Accept': 'text/html'})
        self.assertEqual(resposta.status_code, 200)
        return resposta.get_data(as_text=True)

    def enviar(self, caminho, dados, web=None):
        web = web or self.web
        dados = {**dados, 'csrf_token': web.get('/teste/csrf').get_data(as_text=True)}
        return web.post(caminho, data=dados, headers={'Accept': 'text/html'})

    @staticmethod
    def textos(html):
        return re.findall(r'texto-(\d+)', html)

    @staticmethod
    def consulta(resposta):
        return parse_qs(urlsplit(resposta.headers['Location']).query)


class TestListaEOSeletor(BaseOrdemRotas):
    def test_ordens_na_pagina(self):
        self.semear(3)
        self.reagir(1, curtidas=2)
        esperado = {'recentes': ['3', '2', '1'], 'antigos': ['1', '2', '3'],
                    'curtidos': ['1', '3', '2'], 'reacoes': ['1', '3', '2']}
        for ordem, ids in esperado.items():
            with self.subTest(ordem=ordem):
                self.assertEqual(self.textos(self.ver(f'/professores/1?ordem={ordem}')), ids)

    def test_sem_parametro_ou_invalido_cai_em_recentes_sem_erro(self):
        self.semear(3)
        for query in ('', '?ordem=', '?ordem=zzz', '?ordem=CURTIDOS', '?ordem=%3Cscript%3E'):
            with self.subTest(query=query):
                html = self.ver(f'/professores/1{query}')
                self.assertEqual(self.textos(html), ['3', '2', '1'])
                self.assertRegex(html, r'<option value="recentes" selected>')
                self.assertNotIn('<script>', html)

    def test_select_com_rotulo_e_a_opcao_atual_marcada(self):
        self.semear(1)
        for ordem, rotulo in ROTULOS.items():
            with self.subTest(ordem=ordem):
                html = self.ver(f'/professores/1?ordem={ordem}')
                inicio = html.index('<label for="ordem">Ordenar por</label>')
                select = html[inicio:html.index('</select>', inicio)]
                for valor, nome in ROTULOS.items():
                    self.assertRegex(select, rf'<option value="{valor}"[^>]*>{nome}</option>')
                self.assertRegex(select, rf'<option value="{ordem}" selected>{rotulo}</option>')
                self.assertEqual(select.count('selected'), 1)

    def test_select_fica_no_mesmo_formulario_get_do_filtro_de_disciplina(self):
        self.semear(1)
        html = self.ver('/professores/1')
        formulario = re.search(r'<form method="get" class="filtros".*?</form>', html, re.S).group(0)
        self.assertIn('name="comentarios_disciplina"', formulario)
        self.assertIn('name="ordem"', formulario)
        self.assertIn('type="submit"', formulario)

    def test_ordem_combina_com_o_filtro_de_disciplina(self):
        self.semear(2, disciplina=10)
        self.semear(2, disciplina=11)
        self.reagir(4, curtidas=3)
        self.reagir(3, curtidas=1)
        html = self.ver('/professores/1?comentarios_disciplina=11&ordem=curtidos')
        self.assertEqual(self.textos(html), ['4', '3'])
        html = self.ver('/professores/1?comentarios_disciplina=11&ordem=antigos')
        self.assertEqual(self.textos(html), ['3', '4'])

    def test_frase_neutra_so_com_mais_comentarios_que_o_limite_e_igual_em_toda_ordem(self):
        self.semear(LIMITE_COMENTARIOS)
        for ordem in ROTULOS:
            with self.subTest(ordem=ordem, total=LIMITE_COMENTARIOS):
                html = self.ver(f'/professores/1?ordem={ordem}')
                self.assertNotIn('primeiros comentários', html)
                self.assertNotIn('comentários mais recentes', html)
        self.semear(1)
        for ordem in ROTULOS:
            with self.subTest(ordem=ordem, total=LIMITE_COMENTARIOS + 1):
                html = self.ver(f'/professores/1?ordem={ordem}')
                self.assertIn(FRASE_LIMITE, html)
                self.assertEqual(html.count('primeiros comentários'), 1)
                self.assertNotIn('comentários mais recentes', html)
                self.assertEqual(len(self.textos(html)), LIMITE_COMENTARIOS)


class TestPreservaAOrdem(BaseOrdemRotas):
    def setUp(self):
        super().setUp()
        self.semear(2, usuario=self.ana)        # 1 e 2 são da Ana
        self.semear(1, usuario=self.bia)        # 3 é da Bia (logada em self.web)
        self.cid_ana, self.cid_bia = 1, 3

    def test_pagina_leva_a_ordem_nos_hidden_e_links(self):
        html = self.ver('/professores/1?ordem=curtidos&comentarios_disciplina=10')
        # composer + formulário das médias + um formulário de reação por comentário alheio
        self.assertGreaterEqual(html.count('name="ordem" value="curtidos"'), 3)
        editar = re.search(r'href="([^"]*/comentarios/3/editar[^"]*)"', html).group(1)
        excluir = re.search(r'href="([^"]*/comentarios/3/excluir[^"]*)"', html).group(1)
        denunciar = re.search(r'href="([^"]*/comentarios/1/denunciar[^"]*)"', html).group(1)
        for link in (editar, excluir, denunciar):
            self.assertEqual(parse_qs(urlsplit(unescape(link)).query)['ordem'], ['curtidos'])

    def test_pagina_em_recentes_nao_poe_ordem_em_nenhum_lugar(self):
        for query in ('', '?ordem=recentes', '?ordem=invalida'):
            with self.subTest(query=query):
                html = self.ver(f'/professores/1{query}')
                self.assertNotIn('name="ordem" value=', html)
                self.assertNotIn('ordem=', re.sub(r'<select.*?</select>', '', html, flags=re.S))

    def test_links_de_semestre_e_do_grafico_levam_a_ordem(self):
        for ano, periodo in ((2026, 1), (2026, 2)):
            tabela = self.cliente.tabelas['avaliacoes']
            tabela.append({'id': len(tabela) + 1, 'usuario_id': f'u{len(tabela)}',
                           'professor_id': 1, 'disciplina_id': 10,
                           'ano': ano, 'periodo': periodo, **NOTAS})
        html = self.ver('/professores/1?disciplina_id=10&ordem=antigos')
        semestre = re.search(r'href="([^"]*semestre=2026-1[^"]*)"', html).group(1)
        grafico = re.search(r'href="([^"]*evolucao_criterio=clareza[^"]*)"', html).group(1)
        todos = re.search(r'href="([^"]*)#titulo-medias">Todos', html).group(1)
        for link in (semestre, grafico, todos):
            self.assertEqual(parse_qs(urlsplit(unescape(link)).query)['ordem'], ['antigos'])
        html = self.ver('/professores/1?disciplina_id=10')
        for trecho in ('semestre=2026-1', 'evolucao_criterio=clareza'):
            link = re.search(rf'href="([^"]*{trecho}[^"]*)"', html).group(1)
            self.assertNotIn('ordem=', link)

    def test_link_de_entrar_do_visitante_volta_com_a_ordem(self):
        html = self.ver('/professores/1?ordem=reacoes', web=self.app.test_client())
        entrar = unescape(re.search(r'href="(/login\?[^"]*)"', html).group(1))
        destino = parse_qs(urlsplit(entrar).query)['next'][0]
        self.assertEqual(parse_qs(urlsplit(destino).query)['ordem'], ['reacoes'])

    def test_publicar_volta_com_a_ordem(self):
        resposta = self.enviar('/professores/1/comentarios', {
            'disciplina_id': '10', 'texto': 'um novo comentário', 'ordem': 'curtidos',
            'comentarios_disciplina': '10'})
        self.assertEqual(resposta.status_code, 303)
        consulta = self.consulta(resposta)
        self.assertEqual((consulta['ordem'], consulta['comentarios_disciplina']),
                         (['curtidos'], ['10']))
        self.assertTrue(resposta.headers['Location'].endswith('#comentarios'))

    def test_publicar_com_erro_re_renderiza_com_a_ordem(self):
        resposta = self.enviar('/professores/1/comentarios', {
            'disciplina_id': '10', 'texto': 'x', 'ordem': 'antigos'})
        self.assertEqual(resposta.status_code, 400)
        html = resposta.get_data(as_text=True)
        self.assertIn('<option value="antigos" selected>', html)
        self.assertEqual(self.textos(html), ['1', '2', '3'])
        self.assertGreaterEqual(html.count('name="ordem" value="antigos"'), 2)

    def test_publicar_url_limpa_em_recentes_ou_valor_invalido(self):
        for ordem in ('recentes', 'invalida', ''):
            with self.subTest(ordem=ordem):
                resposta = self.enviar('/professores/1/comentarios', {
                    'disciplina_id': '10', 'texto': 'outro comentário', 'ordem': ordem})
                self.assertEqual(resposta.status_code, 303)
                self.assertNotIn('ordem', self.consulta(resposta))
                self.assertNotIn('ordem=', resposta.headers['Location'])

    def test_reagir_volta_com_a_ordem(self):
        resposta = self.enviar(f'/comentarios/{self.cid_ana}/reacao', {
            'valor': 1, 'ordem': 'reacoes', 'comentarios_disciplina': '10'})
        self.assertEqual(resposta.status_code, 303)
        consulta = self.consulta(resposta)
        self.assertEqual((consulta['ordem'], consulta['comentarios_disciplina']),
                         (['reacoes'], ['10']))

    def test_reagir_url_limpa_em_recentes_ou_valor_invalido(self):
        for ordem in ('recentes', 'xyz'):
            with self.subTest(ordem=ordem):
                resposta = self.enviar(f'/comentarios/{self.cid_ana}/reacao',
                                       {'valor': 1, 'ordem': ordem})
                self.assertEqual(resposta.status_code, 303)
                self.assertNotIn('ordem', self.consulta(resposta))

    def test_editar_leva_a_ordem_no_formulario_no_cancelar_e_no_redirect(self):
        caminho = f'/comentarios/{self.cid_bia}/editar'
        html = self.ver(f'{caminho}?ordem=curtidos&comentarios_disciplina=10')
        self.assertIn('name="ordem" value="curtidos"', html)
        cancelar = unescape(re.search(r'class="cancelar[^"]*" href="([^"]*)"', html).group(1))
        self.assertEqual(parse_qs(urlsplit(cancelar).query)['ordem'], ['curtidos'])
        resposta = self.enviar(caminho, {'disciplina_id': '10', 'texto': 'texto editado ok',
                                         'ordem': 'curtidos', 'comentarios_disciplina': '10'})
        self.assertEqual(resposta.status_code, 303)
        self.assertEqual(self.consulta(resposta)['ordem'], ['curtidos'])

    def test_editar_em_recentes_ou_invalido_nao_poe_ordem(self):
        caminho = f'/comentarios/{self.cid_bia}/editar'
        self.assertNotIn('name="ordem"', self.ver(f'{caminho}?ordem=recentes'))
        self.assertNotIn('name="ordem"', self.ver(f'{caminho}?ordem=lixo'))
        resposta = self.enviar(caminho, {'disciplina_id': '10', 'texto': 'texto editado ok',
                                         'ordem': 'lixo'})
        self.assertNotIn('ordem', self.consulta(resposta))

    def test_editar_com_erro_mantem_a_ordem_no_formulario(self):
        resposta = self.enviar(f'/comentarios/{self.cid_bia}/editar',
                               {'disciplina_id': '10', 'texto': 'x', 'ordem': 'antigos'})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('name="ordem" value="antigos"', resposta.get_data(as_text=True))

    def test_excluir_leva_a_ordem_no_formulario_e_no_redirect(self):
        caminho = f'/comentarios/{self.cid_bia}/excluir'
        html = self.ver(f'{caminho}?ordem=reacoes')
        self.assertIn('name="ordem" value="reacoes"', html)
        resposta = self.enviar(caminho, {'ordem': 'reacoes', 'comentarios_disciplina': '10'})
        self.assertEqual(resposta.status_code, 303)
        consulta = self.consulta(resposta)
        self.assertEqual((consulta['ordem'], consulta['comentarios_disciplina']),
                         (['reacoes'], ['10']))

    def test_excluir_em_recentes_nao_poe_ordem(self):
        resposta = self.enviar(f'/comentarios/{self.cid_bia}/excluir', {'ordem': 'recentes'})
        self.assertEqual(resposta.status_code, 303)
        self.assertNotIn('ordem', self.consulta(resposta))

    def test_denunciar_leva_a_ordem_no_formulario_e_no_redirect(self):
        caminho = f'/comentarios/{self.cid_ana}/denunciar'
        html = self.ver(f'{caminho}?ordem=curtidos&comentarios_disciplina=10')
        self.assertIn('name="ordem" value="curtidos"', html)
        voltar = unescape(re.search(r'href="([^"]*)"[^>]*>\s*Voltar', html).group(1)) \
            if re.search(r'href="([^"]*)"[^>]*>\s*Voltar', html) else None
        if voltar:
            self.assertEqual(parse_qs(urlsplit(voltar).query)['ordem'], ['curtidos'])
        resposta = self.enviar(caminho, {'motivo': 'ofensa', 'ordem': 'curtidos',
                                         'comentarios_disciplina': '10'})
        self.assertEqual(resposta.status_code, 303)
        consulta = self.consulta(resposta)
        self.assertEqual((consulta['ordem'], consulta['comentarios_disciplina']),
                         (['curtidos'], ['10']))

    def test_denunciar_em_recentes_nao_poe_ordem(self):
        caminho = f'/comentarios/{self.cid_ana}/denunciar'
        self.assertNotIn('name="ordem"', self.ver(f'{caminho}?ordem=recentes'))
        resposta = self.enviar(caminho, {'motivo': 'ofensa', 'ordem': 'recentes'})
        self.assertEqual(resposta.status_code, 303)
        self.assertNotIn('ordem', self.consulta(resposta))

    def test_meus_comentarios_nao_muda(self):
        resposta = self.enviar(f'/comentarios/{self.cid_bia}/excluir',
                               {'origem': 'perfil', 'ordem': 'curtidos'})
        self.assertEqual(resposta.status_code, 303)
        destino = urlsplit(resposta.headers['Location'])
        self.assertEqual(destino.path, '/perfil')
        self.assertNotIn('ordem', destino.query)


if __name__ == '__main__':
    unittest.main()
