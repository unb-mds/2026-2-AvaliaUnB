"""Recorte de ofertas sem perder histórico nem alterar notas ou comparação."""
import json
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import parse_qs, urlsplit

from app import create_app
from tests.fake_supabase import ClienteFalso


class TestOfertasSemestre(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.configuracao = Path(self.pasta.name)/'semestre.json'
        self.configurar(None)
        self.cliente = ClienteFalso()
        # José: Cálculo em 2026/1 e 2026/2, Álgebra apenas em 2026/1.
        self.cliente.tabelas['vw_professor_disciplina'].append({
            'professor_id': 1, 'disciplina_id': 30, 'codigo_disciplina': 'MAT0030',
            'disciplina': 'ÁLGEBRA', 'ano': 2026, 'periodo': 1})
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-teste-de-ofertas',
                               'SUPABASE_CLIENT': self.cliente,
                               'SEMESTRE_ATUAL_ARQUIVO': str(self.configuracao)})
        self.web = self.app.test_client()

    def configurar(self, semestre):
        self.configuracao.write_text(json.dumps({'semestre_atual': semestre}))

    def nomes(self, url):
        resposta=self.web.get(url)
        self.assertEqual(resposta.status_code, 200)
        return re.findall(r'<h2><a[^>]*>(.*?)</a></h2>', resposta.text)

    def test_sem_configuracao_mantem_inclusive_professor_sem_turma(self):
        self.assertEqual(set(self.nomes('/professores')), {'JOSÉ ÁVILA','MARIA LIMA','SEM TURMA'})
        self.assertIn('O semestre atual ainda não foi definido', self.web.get('/professores').text)

    def test_atual_explicito_nao_e_o_maior_periodo_do_banco(self):
        self.configurar({'ano': 2026,'periodo': 1})
        self.assertEqual(self.nomes('/professores'), ['JOSÉ ÁVILA'])
        self.assertIn('2026/1 (atual)',self.web.get('/professores').text)
        self.assertEqual(set(self.nomes('/professores?oferta=todos')),
                         {'JOSÉ ÁVILA','MARIA LIMA','SEM TURMA'})

    def test_disciplinas_e_sugestoes_compartilham_recorte(self):
        self.assertEqual(self.nomes('/professores?oferta=2026-2&q=algebra'), [])
        self.assertEqual(self.nomes('/professores?oferta=2026-1&q=algebra'), ['JOSÉ ÁVILA'])
        self.assertEqual(self.web.get('/busca/sugestoes?q=algebra&oferta=2026-2').json['sugestoes'], [])
        sugestao, = self.web.get('/busca/sugestoes?q=algebra&oferta=2026-1').json['sugestoes']
        self.assertEqual(parse_qs(urlsplit(sugestao['url']).query)['oferta'], ['2026-1'])
        html=self.web.get('/professores?oferta=2026-2').text
        self.assertNotIn('ÁLGEBRA',html)

    def test_sugestoes_padrao_usam_atual_e_comparacao_mantem_historico(self):
        self.configurar({'ano':2026,'periodo':1})
        self.assertEqual(self.web.get('/busca/sugestoes?q=maria').json['sugestoes'], [])
        historicas=self.web.get('/busca/sugestoes?q=maria&contexto=comparacao').json['sugestoes']
        self.assertEqual(historicas[0]['texto'],'MARIA LIMA')

    def test_periodo_valido_sem_ofertas_exibe_vazio_sem_substituir_selecao(self):
        resposta=self.web.get('/professores?oferta=2025-1')
        self.assertIn('Nenhum professor encontrado nas ofertas de 2025/1',resposta.text)
        self.assertIn('value="2025-1" selected',resposta.text)
        self.assertEqual(self.nomes('/professores?oferta=2025-1'),[])

    def test_valor_invalido_nao_troca_silenciosamente_para_todos(self):
        for valor in ['2026-9','26-2','banana','2026/2']:
            self.assertEqual(self.web.get('/professores',query_string={'oferta':valor}).status_code,400)
            self.assertEqual(self.web.get('/busca/sugestoes',query_string={'q':'maria','oferta':valor}).status_code,400)

    def test_perfil_historico_continua_acessivel(self):
        self.configurar({'ano':2026,'periodo':1})
        self.assertNotIn('MARIA LIMA',self.nomes('/professores'))
        self.assertEqual(self.web.get('/professores/2').status_code,200)
        self.assertIn('MARIA LIMA',self.web.get('/comparar?modo=livre&professor_1=2').text)

    def test_filtro_nao_altera_notas_nem_comentarios(self):
        self.cliente.tabelas['avaliacoes']=[{'id':1,'professor_id':1,'disciplina_id':10,
            'ano':2026,'periodo':1,'didatica':5,'clareza':5,'organizacao':5,
            'disponibilidade':5,'dificuldade':2}]
        repo=self.app.extensions['repositorios']
        antes=repo.avaliacoes.calcular_medias(1)
        self.nomes('/professores?oferta=2026-2')
        self.assertEqual(repo.avaliacoes.calcular_medias(1),antes)
        self.assertEqual(len(self.cliente.tabelas['avaliacoes']),1)
        self.assertEqual(self.cliente.upserts,[])

    def test_recorte_precede_paginacao_e_preserva_filtro_na_url(self):
        for i in range(4,114):
            self.cliente.tabelas['professores'].append({'id':i,'nome':f'PROF {i:03}', 'departamento':'FCTE'})
            self.cliente.tabelas['vw_professor_disciplina'].append({'professor_id':i,
                'disciplina_id':20,'codigo_disciplina':'FGA0002','disciplina':'FÍSICA 1',
                'ano':2026,'periodo':1})
        html=self.web.get('/professores?oferta=2026-1&pagina=2').text
        self.assertIn('Mostrando 101–111 de 111 professores.',html)
        self.assertRegex(html,r'rel="prev" href="[^"]*oferta=2026-1')
        self.assertIn('name="oferta" value="2026-1"',html)
        self.assertEqual(len(self.nomes('/professores?oferta=2026-2')),2)

    def test_trocar_periodo_nao_contamina_cache_historico(self):
        self.assertEqual(self.nomes('/professores?oferta=2026-1'),['JOSÉ ÁVILA'])
        self.assertEqual(len(self.nomes('/professores?oferta=2026-2')),2)
        self.assertEqual(len(self.nomes('/professores?oferta=todos')),3)
