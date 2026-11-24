"""Ordem da lista de comentários no repositório (issue #213), com o cliente falso."""
import unittest

from app.controllers.professor_controller import ORDENS_COMENTARIOS, ordem_de_comentarios
from app.repositorio import LIMITE_COMENTARIOS
from tests.test_comentarios import ANA, BIA, BaseComentarios


class BaseOrdem(BaseComentarios):
    def reagir(self, comentario_id, curtidas=0, descurtidas=0):
        """Grava reações de contas distintas direto na tabela."""
        tabela = self.cliente.tabelas['comentarios_reacoes']
        for i in range(curtidas + descurtidas):
            tabela.append({'comentario_id': comentario_id, 'valor': 1 if i < curtidas else -1,
                           'usuario_id': f'u{comentario_id}-{i}'})

    def ids(self, ordem, **kwargs):
        comentarios, ha_mais = self.repo.listar_por_professor(1, ordem=ordem, **kwargs)
        return [c['id'] for c in comentarios], ha_mais


class TestOrdemDeComentarios(unittest.TestCase):
    def test_valores_conhecidos_passam(self):
        for valor in ORDENS_COMENTARIOS:
            self.assertEqual(ordem_de_comentarios(valor), valor)

    def test_valor_invalido_vazio_ou_nulo_vira_recentes(self):
        for valor in (None, '', 'RECENTES', 'curtido', 'x', '1', ' antigos', '<b>'):
            with self.subTest(valor=valor):
                self.assertEqual(ordem_de_comentarios(valor), 'recentes')


class TestOrdens(BaseOrdem):
    def test_recentes_e_o_padrao_e_valor_desconhecido_cai_nele(self):
        self.semear(3)
        padrao, _ = self.repo.listar_por_professor(1)
        self.assertEqual([c['id'] for c in padrao], [3, 2, 1])
        self.assertEqual(self.ids('recentes')[0], [3, 2, 1])
        self.assertEqual(self.ids('qualquer-coisa')[0], [3, 2, 1])

    def test_antigos_do_mais_velho_ao_mais_novo(self):
        self.semear(3)
        self.assertEqual(self.ids('antigos'), ([1, 2, 3], False))

    def test_antigos_desempata_pelo_id_crescente(self):
        self.semear(2)
        self.semear(3, criado_em='2026-04-01T00:00:00+00:00')   # ids 3, 4 e 5 empatados
        self.assertEqual(self.ids('antigos')[0], [1, 2, 3, 4, 5])

    def test_antigos_respeita_o_limite_e_avisa(self):
        self.semear(LIMITE_COMENTARIOS + 1)
        ids, ha_mais = self.ids('antigos')
        self.assertEqual((ids[0], ids[-1], len(ids), ha_mais), (1, 50, 50, True))

    def test_curtidos_ordena_so_pelas_curtidas(self):
        self.semear(4)
        self.reagir(1, curtidas=3)
        self.reagir(2, curtidas=1, descurtidas=5)   # muitas reações, mas só 1 curtida
        self.reagir(3, curtidas=1)
        self.assertEqual(self.ids('curtidos'), ([1, 3, 2, 4], False))

    def test_reacoes_ordena_pela_soma_de_curtidas_e_descurtidas(self):
        self.semear(4)
        self.reagir(1, curtidas=3)
        self.reagir(2, curtidas=1, descurtidas=5)
        self.reagir(3, curtidas=1)
        self.assertEqual(self.ids('reacoes'), ([2, 1, 3, 4], False))

    def test_empate_nas_ordens_por_reacao_vale_o_mais_recente(self):
        self.semear(4)
        for comentario in (1, 2, 3):
            self.reagir(comentario, curtidas=2)
        self.assertEqual(self.ids('curtidos')[0], [3, 2, 1, 4])
        self.assertEqual(self.ids('reacoes')[0], [3, 2, 1, 4])

    def test_empate_com_mesma_data_desempata_pelo_id_decrescente(self):
        self.semear(3, criado_em='2026-04-01T00:00:00+00:00')
        for comentario in (1, 2, 3):
            self.reagir(comentario, curtidas=1)
        self.assertEqual(self.ids('curtidos')[0], [3, 2, 1])

    def test_sem_reacao_fica_depois_de_quem_tem(self):
        self.semear(4)
        self.reagir(1, curtidas=1)              # os dois mais antigos têm reação
        self.reagir(2, descurtidas=1)
        # Sem reação (3 e 4) vem depois, mais recentes primeiro.
        self.assertEqual(self.ids('reacoes')[0], [2, 1, 4, 3])
        # Em 'curtidos' uma descurtida vale 0: só quem tem 👍 vence quem não tem reação.
        self.assertEqual(self.ids('curtidos')[0], [1, 4, 3, 2])

    def test_ocultado_fica_fora_mesmo_com_muitas_reacoes(self):
        self.semear(2)
        self.semear(1, ocultado_em='2026-03-02T00:00:00+00:00')
        self.reagir(3, curtidas=9)
        self.reagir(1, curtidas=1)
        for ordem in ('curtidos', 'reacoes'):
            with self.subTest(ordem=ordem):
                self.assertEqual(self.ids(ordem), ([1, 2], False))

    def test_filtro_de_disciplina_combina_com_a_ordem(self):
        self.semear(2, disciplina=10)
        self.semear(2, disciplina=11)
        self.reagir(1, curtidas=1)
        self.reagir(4, curtidas=5)
        self.reagir(3, curtidas=2)
        self.assertEqual(self.ids('curtidos', disciplina_id=11)[0], [4, 3])
        self.assertEqual(self.ids('curtidos', disciplina_id=10)[0], [1, 2])
        self.assertEqual(self.ids('antigos', disciplina_id=11)[0], [3, 4])
        self.assertEqual(self.ids('curtidos')[0], [4, 3, 1, 2])

    def test_so_do_professor_pedido_nas_ordens_por_reacao(self):
        self.semear(1, professor=1)
        self.semear(1, professor=2, disciplina=20)
        self.reagir(2, curtidas=9)
        self.assertEqual(self.ids('curtidos')[0], [1])


class TestLimiteDepoisDaOrdem(BaseOrdem):
    def test_antigo_muito_curtido_entra_no_top_50_de_curtidos(self):
        self.semear(LIMITE_COMENTARIOS + 10)        # ids 1 a 60; o 1 é o mais antigo
        self.reagir(1, curtidas=2)
        self.assertNotIn(1, self.ids('recentes')[0])
        ids, ha_mais = self.ids('curtidos')
        self.assertEqual((ids[0], len(ids), ha_mais), (1, 50, True))
        self.assertEqual(ids[1:4], [60, 59, 58])    # o resto segue pela data

    def test_o_mesmo_vale_para_reacoes(self):
        self.semear(LIMITE_COMENTARIOS + 10)
        self.reagir(2, descurtidas=3)
        ids, ha_mais = self.ids('reacoes')
        self.assertEqual((ids[0], len(ids), ha_mais), (2, 50, True))

    def test_exatamente_no_limite_nao_avisa(self):
        self.semear(LIMITE_COMENTARIOS)
        for ordem in ORDENS_COMENTARIOS:
            with self.subTest(ordem=ordem):
                ids, ha_mais = self.ids(ordem)
                self.assertEqual((len(ids), ha_mais), (LIMITE_COMENTARIOS, False))

    def test_lista_vazia_em_todas_as_ordens(self):
        for ordem in ORDENS_COMENTARIOS:
            with self.subTest(ordem=ordem):
                self.assertEqual(self.repo.listar_por_professor(1, ordem=ordem), ([], False))

    def test_candidatos_alem_de_uma_pagina_do_postgrest(self):
        self.semear(1001)                           # mais que TAMANHO_PAGINA (1000)
        self.reagir(1, curtidas=1)
        ids, ha_mais = self.ids('curtidos')
        self.assertEqual((ids[0], len(ids), ha_mais), (1, 50, True))


class TestMesmosCamposEmTodasAsOrdens(BaseOrdem):
    def test_campos_e_regras_iguais_aos_de_recentes(self):
        self.semear(1, usuario=ANA)
        self.semear(1, usuario=BIA)
        self.linhas()[1]['atualizado_em'] = '2026-05-01T00:00:00+00:00'   # editado
        self.reagir(1, curtidas=1)
        base, _ = self.repo.listar_por_professor(1, usuario_atual_id=ANA)
        por_id = {c['id']: c for c in base}
        for ordem in ('antigos', 'curtidos', 'reacoes'):
            with self.subTest(ordem=ordem):
                comentarios, _ = self.repo.listar_por_professor(1, usuario_atual_id=ANA, ordem=ordem)
                self.assertEqual(len(comentarios), 2)
                for c in comentarios:
                    self.assertEqual(c, por_id[c['id']])
                self.assertTrue(por_id[1]['e_meu'])
                self.assertFalse(por_id[2]['e_meu'])
                self.assertTrue(por_id[2]['editado'])
                self.assertNotIn('usuario_id', por_id[1])


if __name__ == '__main__':
    unittest.main()
