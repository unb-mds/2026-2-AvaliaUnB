"""Fluxos completos dos atalhos de comentários, no professor e no perfil (#260)."""
import html
import re
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from app.repositorio import ComentarioRepository, LIMITE_COMENTARIOS
from tests.test_comentarios_editar_excluir import BaseEdicao, BIA


class TestAcoesComentarios(BaseEdicao):
    def setUp(self):
        super().setUp()
        self.entrar()
        self.cliente.tabelas['disciplinas'].extend([
            {'id': 10, 'nome': 'CÁLCULO 1', 'codigo': 'MAT0010'},
            {'id': 11, 'nome': 'CÁLCULO 2', 'codigo': 'FGA0011'},
        ])

    @staticmethod
    def links_acoes(pagina):
        grupo = re.search(r'<p class="comentario-acoes">(.*?)</p>', pagina, re.S).group(1)
        return {texto: html.unescape(url) for url, texto in
                re.findall(r'<a [^>]*href="([^"]+)"[^>]*>(Editar|Excluir)</a>', grupo)}

    def test_publicar_mostra_os_dois_atalhos_e_editar_preserva_os_filtros(self):
        resposta = self.enviar('/professores/1/comentarios', {
            'disciplina_id': '10', 'texto': 'Relato recém publicado',
            'disciplina_medias': '11', 'comentarios_disciplina': '10',
            'next': '/professores?q=calculo'})
        self.assertEqual(resposta.status_code, 303)
        destino = resposta.headers['Location']
        for _ in range(2):  # também após recarregar
            pagina = self.ver(destino).get_data(as_text=True)
            acoes = self.links_acoes(pagina)
            self.assertEqual(set(acoes), {'Editar', 'Excluir'})
            self.assertIn('class="btn ghost acao-editar"', pagina)
            self.assertIn('class="btn ghost acao-excluir"', pagina)
        formulario = self.ver(acoes['Editar']).get_data(as_text=True)
        self.assertIn('>Relato recém publicado</textarea>', formulario)
        self.assertRegex(formulario, r'<option value="10"\s+selected>')
        dados = {k: v[0] for k, v in parse_qs(urlsplit(acoes['Editar']).query).items()}
        dados.update(disciplina_id='10', texto='Relato corrigido')
        resposta = self.editar(1, dados)
        self.assertEqual(resposta.status_code, 303)
        volta = urlsplit(resposta.headers['Location'])
        self.assertEqual(volta.fragment, 'comentarios')
        self.assertEqual(parse_qs(volta.query)['disciplina_id'], ['11'])
        self.assertEqual(parse_qs(volta.query)['comentarios_disciplina'], ['10'])
        self.assertEqual(parse_qs(volta.query)['next'], ['/professores?q=calculo'])
        self.assertIn('Relato corrigido', self.ver(resposta.headers['Location']).get_data(as_text=True))

    def test_perfil_lista_so_os_proprios_comentarios_com_os_dois_atalhos(self):
        self.semear('Relato da própria conta')
        self.semear('Relato de outra conta', usuario=BIA)
        pagina = self.ver('/perfil').get_data(as_text=True)
        secao = pagina.split('id="meus-comentarios"', 1)[1].split('</section>', 1)[0]
        self.assertIn('Relato da própria conta', secao)
        self.assertNotIn('Relato de outra conta', secao)
        self.assertIn('CÁLCULO 1', secao)
        acoes = self.links_acoes(secao)
        self.assertEqual(set(acoes), {'Editar', 'Excluir'})
        self.assertNotIn(self.id_logado, secao)
        self.assertNotIn('usuario_id', secao)
        for url in acoes.values():
            self.assertEqual(parse_qs(urlsplit(url).query)['origem'], ['perfil'])
            form = self.ver(url).get_data(as_text=True)
            self.assertIn('href="/perfil#meus-comentarios"', form)
            self.assertIn('name="origem" value="perfil"', form)

    def test_editar_e_excluir_pelo_perfil_retornam_aos_meus_comentarios(self):
        self.semear()
        resposta = self.editar(1, {'origem': 'perfil', 'disciplina_id': '10', 'texto': 'Atualizado pelo perfil'})
        self.assertEqual(resposta.status_code, 303)
        self.assertEqual(resposta.headers['Location'], '/perfil#meus-comentarios')
        self.assertIn('Atualizado pelo perfil', self.ver(resposta.headers['Location']).get_data(as_text=True))
        resposta = self.excluir(1, {'origem': 'perfil'})
        self.assertEqual(resposta.status_code, 303)
        self.assertEqual(resposta.headers['Location'], '/perfil#meus-comentarios')
        self.assertIn('Você ainda não tem comentários publicados.', self.ver('/perfil').get_data(as_text=True))

    def test_cancelar_nao_modifica_o_comentario(self):
        self.semear()
        antes = self.comentarios()
        for acao in ('editar', 'excluir'):
            pagina = self.ver(f'/comentarios/1/{acao}?origem=perfil').get_data(as_text=True)
            self.assertIn('href="/perfil#meus-comentarios"', pagina)
            self.ver('/perfil#meus-comentarios')
        self.assertEqual(self.comentarios(), antes)

    def test_origem_nao_permite_redirecionamento_externo(self):
        self.semear()
        resposta = self.editar(1, {'origem': 'https://fora.example', 'next': '//fora.example',
                                  'disciplina_id': '10', 'texto': 'Texto válido'})
        volta = urlsplit(resposta.headers['Location'])
        self.assertEqual(volta.netloc, '')
        self.assertEqual(volta.path, '/professores/1')

    def test_falha_na_secao_nao_quebra_as_demais_secoes_do_perfil(self):
        with patch.object(ComentarioRepository, 'listar_do_usuario', side_effect=RuntimeError('detalhe privado')):
            with self.assertLogs(self.app.logger, level='ERROR'):
                resposta = self.ver('/perfil')
        self.assertEqual(resposta.status_code, 200)
        pagina = resposta.get_data(as_text=True)
        self.assertIn('Não foi possível carregar seus comentários.', pagina)
        self.assertIn('Minhas Avaliações', pagina)
        self.assertIn('Favoritos', pagina)
        self.assertNotIn('detalhe privado', pagina)

    def test_repositorio_limita_ordena_e_nao_inclui_contas_ou_comentarios_ocultos(self):
        for numero in range(LIMITE_COMENTARIOS + 1):
            self.semear(f'Relato {numero}')
        self.semear('Outro autor', usuario=BIA)
        oculto = self.semear('Relato oculto')
        self.cliente.tabelas['comentarios'][-1]['ocultado_em'] = '2026-03-01T11:00:00Z'
        repo = ComentarioRepository(self.cliente)
        comentarios, ha_mais = repo.listar_do_usuario(self.id_logado)
        self.assertTrue(ha_mais)
        self.assertEqual(len(comentarios), LIMITE_COMENTARIOS)
        self.assertEqual(comentarios[0]['texto'], f'Relato {LIMITE_COMENTARIOS}')
        self.assertFalse(any(c['id'] == oculto or c['texto'] == 'Outro autor' for c in comentarios))
        for c in comentarios:
            self.assertNotIn('usuario_id', c)
            self.assertNotIn('username', c)

    def test_texto_no_perfil_e_escapado_e_outra_conta_nao_pode_editar(self):
        self.semear('<script>alert(1)</script>')
        outro = self.semear('Relato de outra conta', usuario=BIA)
        pagina = self.ver('/perfil').get_data(as_text=True)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', pagina)
        self.assertNotIn('<script>alert(1)</script>', pagina)
        self.assertEqual(self.ver(f'/comentarios/{outro}/editar?origem=perfil').status_code, 404)
        self.assertEqual(self.editar(outro, {'origem': 'perfil', 'disciplina_id': '10', 'texto': 'Indevido'}).status_code, 404)
