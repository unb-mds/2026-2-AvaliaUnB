"""Confirmação operacional: cobertura, vínculos e persistência antes de ativar."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scraper'))
from resumo_sigaa import Resumo
from persistencia_sigaa import conferir_persistencia, gravar_catalogo
from scraper.confirmar_semestre import confirmar
from scraper.validacao_coleta import montar_relatorio, validar_relatorio
from tests.fake_supabase import ClienteFalso


PROFESSORES=[{'nome':'Ana Nova','departamento':'FCTE'}]
DISCIPLINAS=[{'codigo':'FGA0100','nome':'Algoritmos'}]
TURMAS=[{'professor_nome':'Ana Nova','disciplina_codigo':'FGA0100','ano':2026,'periodo':2}]


def relatorio(dry_run=False):
    resumo=Resumo()
    return montar_relatorio('2026','2',[('1','FCTE'),('2','MAT'),
        ('3','PROGRAMA DE PÓS-GRADUAÇÃO EM COMPUTAÇÃO')],
        [{'codigo':'1','status':'ok'},{'codigo':'2','status':'vazio'}],
        resumo,PROFESSORES,DISCIPLINAS,TURMAS,dry_run,not dry_run)


class TestValidacaoColeta(unittest.TestCase):
    def setUp(self):
        self.pasta=tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.config=Path(self.pasta.name)/'semestre.json'
        self.config.write_text('{"semestre_atual": null}')

    def recusa_sem_mudar_config(self, dados, confirmacao='2026-2'):
        anterior=self.config.read_bytes()
        with self.assertRaises(ValueError):
            confirmar(dados,confirmacao,self.config,True)
        self.assertEqual(self.config.read_bytes(),anterior)

    def test_coleta_completa_gravada_e_confirmada_gera_configuracao_rastreavel(self):
        dados=relatorio()
        resultado=confirmar(dados,'2026-2',self.config,True,'https://github.com/exemplo/actions/runs/1')
        self.assertEqual(resultado['semestre_atual'],{'ano':2026,'periodo':2})
        self.assertEqual(resultado['coleta']['unidades'],2)
        self.assertEqual(resultado['coleta']['turmas'],1)
        self.assertEqual(json.loads(self.config.read_text()),resultado)

    def test_validacao_sem_gravar_nao_ativa(self):
        anterior=self.config.read_bytes()
        confirmar(relatorio(),'2026-2',self.config)
        self.assertEqual(self.config.read_bytes(),anterior)

    def test_repetir_confirmacao_e_idempotente(self):
        dados=relatorio()
        confirmar(dados,'2026-2',self.config,True)
        antes=self.config.read_bytes()
        confirmar(dados,'2026-2',self.config,True)
        self.assertEqual(self.config.read_bytes(),antes)

    def test_dry_run_pode_validar_cobertura_mas_nunca_ativa(self):
        dados=relatorio(True)
        self.assertEqual(validar_relatorio(dados,2026,2,False)['unidades'],2)
        self.recusa_sem_mudar_config(dados)

    def test_coleta_parcial_falha_ou_unidade_duplicada_nao_ativa(self):
        for unidades in [[{'codigo':'1','status':'ok'}],
                         [{'codigo':'1','status':'ok'},{'codigo':'2','status':'falha'}],
                         [{'codigo':'1','status':'ok'},{'codigo':'1','status':'ok'},
                          {'codigo':'2','status':'vazio'}]]:
            dados=relatorio()
            dados['unidades_lidas']=unidades
            self.recusa_sem_mudar_config(dados)

    def test_vazia_ou_com_linha_pulada_nao_ativa(self):
        for campo,valor in [('turmas',[]),('professores',[]),('disciplinas',[]),
                            ('unidades_esperadas',[]),('linhas_puladas',{'erro':1})]:
            dados=relatorio()
            dados[campo]=valor
            self.recusa_sem_mudar_config(dados)

    def test_historica_antecipada_e_periodo_diferente_nao_ativam(self):
        for finalidade in ['historica','antecipada']:
            dados=relatorio()
            dados['finalidade']=finalidade
            self.recusa_sem_mudar_config(dados)
        self.recusa_sem_mudar_config(relatorio(),'2027-1')

    def test_periodo_anterior_nao_substitui_atual(self):
        self.config.write_text('{"semestre_atual": {"ano": 2027, "periodo": 1}}')
        self.recusa_sem_mudar_config(relatorio())

    def test_integridade_de_periodo_vinculos_e_assinatura(self):
        for campo,valor in [('professor_nome','Não coletado'),('disciplina_codigo','OUTRA'),
                            ('ano',2025),('periodo',1)]:
            dados=relatorio()
            dados['turmas'][0][campo]=valor
            self.recusa_sem_mudar_config(dados)
        dados=relatorio()
        dados['assinatura_turmas']='invalida'
        self.recusa_sem_mudar_config(dados)

    def test_flag_de_persistencia_nao_aceita_texto_como_booleano(self):
        dados=relatorio()
        dados['persistencia_validada']='true'
        self.recusa_sem_mudar_config(dados)


class TestPersistenciaConferida(unittest.TestCase):
    def test_reimportacao_preserva_ofertas_anteriores_notas_comentarios_e_ids(self):
        cliente=ClienteFalso()
        cliente.tabelas['turmas']=[{'id':30,'professor_id':1,'disciplina_id':10,
                                    'ano':2025,'periodo':2}]
        cliente.tabelas['avaliacoes']=[{'id':1,'professor_id':1,'texto':'não alterar'}]
        cliente.tabelas['comentarios']=[{'id':1,'texto':'não alterar'}]
        anteriores=deepcopy({n:cliente.tabelas[n] for n in ['avaliacoes','comentarios']})
        for _ in range(2):
            gravar_catalogo(PROFESSORES,DISCIPLINAS,TURMAS,cliente)
            self.assertTrue(conferir_persistencia(PROFESSORES,DISCIPLINAS,TURMAS,cliente))
        self.assertEqual(len(cliente.tabelas['turmas']),2)
        self.assertEqual(cliente.tabelas['turmas'][0]['id'],30)
        for tabela,linhas in anteriores.items():
            self.assertEqual(cliente.tabelas[tabela],linhas)

    def test_gravacao_incompleta_nao_pode_ser_validada(self):
        cliente=ClienteFalso()
        with self.assertRaises(ValueError):
            conferir_persistencia(PROFESSORES,DISCIPLINAS,TURMAS,cliente)
        gravar_catalogo(PROFESSORES,DISCIPLINAS,TURMAS,cliente)
        cliente.tabelas['turmas']=[]
        with self.assertRaises(ValueError):
            conferir_persistencia(PROFESSORES,DISCIPLINAS,TURMAS,cliente)
