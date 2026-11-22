import unittest
from pathlib import Path


class TestMigracaoRetencaoModeracao(unittest.TestCase):
    MIGRACAO = Path('docs/migrations/009_retencao_moderacao_90_dias.sql')

    def _ler_sql(self):
        self.assertTrue(
            self.MIGRACAO.exists(),
            f'A migração {self.MIGRACAO} deve existir.',
        )
        return self.MIGRACAO.read_text(encoding='utf-8').lower()

    def test_cria_funcao_de_descarte_com_padrao_90_dias(self):
        sql = self._ler_sql()
        self.assertIn('create or replace function descartar_registros_moderacao_expirados', sql)
        self.assertIn('dias_retencao integer default 90', sql)
        self.assertIn('security definer', sql)

    def test_apaga_apenas_registros_encerrados_de_denuncia_moderacao_e_contestacao(self):
        sql = self._ler_sql()
        self.assertIn('delete from denuncias_comentarios', sql)
        self.assertIn('resolvida_em is not null', sql)
        self.assertIn('delete from moderacoes_comentarios', sql)
        self.assertIn('delete from contestacoes_comentarios', sql)
        # Comentários publicados estão fora do escopo e nunca podem ser apagados pela rotina
        self.assertNotIn('delete from comentarios', sql)

    def test_restrito_ao_service_role_e_cria_indices_de_expurgo(self):
        sql = self._ler_sql()
        self.assertIn('revoke all on function descartar_registros_moderacao_expirados(integer) from public, anon, authenticated;', sql)
        self.assertIn('grant execute on function descartar_registros_moderacao_expirados(integer) to service_role;', sql)
        self.assertIn('idx_denuncias_resolvidas_retencao', sql)
        self.assertIn('idx_moderacoes_criado_retencao', sql)
        self.assertIn('idx_contestacoes_resolvidas_retencao', sql)


class TestClienteFalsoRetencao(unittest.TestCase):
    def test_suporta_lt_e_rpc_descarte_90_dias(self):
        from tests.fake_supabase import ClienteFalso

        cliente = ClienteFalso()
        cliente.tabelas['denuncias_comentarios'].extend([
            {
                'id': 1,
                'comentario_id': 10,
                'usuario_id': 'u1',
                'motivo': 'spam',
                'criado_em': '2026-01-01T00:00:00+00:00',
                'resolvida_em': '2026-01-02T00:00:00+00:00',
            },
            {
                'id': 2,
                'comentario_id': 11,
                'usuario_id': 'u2',
                'motivo': 'spam',
                'criado_em': '2026-08-01T00:00:00+00:00',
                'resolvida_em': '2026-08-10T00:00:00+00:00',
            },
            {
                'id': 3,
                'comentario_id': 12,
                'usuario_id': 'u3',
                'motivo': 'ofensa',
                'criado_em': '2026-01-01T00:00:00+00:00',
                'resolvida_em': None,
            },
        ])

        antigas = (
            cliente.table('denuncias_comentarios')
            .select('id')
            .lt('resolvida_em', '2026-06-01T00:00:00+00:00')
            .execute()
            .data
        )
        self.assertEqual([d['id'] for d in antigas], [1])


class TestRepositorioRetencaoModeracao(unittest.TestCase):
    def test_descarta_apenas_registros_encerrados_ha_mais_de_90_dias_sem_apagar_comentarios(self):
        from datetime import datetime, timedelta, timezone
        from app.repositorio import ModeracaoRepository
        from tests.fake_supabase import ClienteFalso

        cliente = ClienteFalso()
        agora = datetime.now(timezone.utc)
        ha_95_dias = (agora - timedelta(days=95)).isoformat()
        ha_91_dias = (agora - timedelta(days=91)).isoformat()
        ha_45_dias = (agora - timedelta(days=45)).isoformat()

        # Comentários publicados (incluindo antigos) NÃO devem ser apagados
        cliente.tabelas['comentarios'].extend([
            {'id': 1, 'usuario_id': 'u1', 'professor_id': 1, 'disciplina_id': 10,
             'texto': 'Comentário antigo publicado', 'criado_em': ha_95_dias, 'ocultado_em': None},
            {'id': 2, 'usuario_id': 'u2', 'professor_id': 1, 'disciplina_id': 10,
             'texto': 'Comentário recente publicado', 'criado_em': ha_45_dias, 'ocultado_em': None},
        ])

        # Denúncias: 1 encerrada >90d (apaga), 1 encerrada <90d (mantém), 1 aberta >90d (mantém)
        cliente.tabelas['denuncias_comentarios'].extend([
            {'id': 10, 'comentario_id': 1, 'usuario_id': 'u2', 'motivo': 'spam',
             'criado_em': ha_95_dias, 'resolvida_em': ha_91_dias},
            {'id': 11, 'comentario_id': 2, 'usuario_id': 'u1', 'motivo': 'spam',
             'criado_em': ha_45_dias, 'resolvida_em': ha_45_dias},
            {'id': 12, 'comentario_id': 1, 'usuario_id': 'u3', 'motivo': 'ofensa',
             'criado_em': ha_95_dias, 'resolvida_em': None},
        ])

        # Decisões de moderação: 1 >90d (apaga), 1 <90d (mantém)
        cliente.tabelas['moderacoes_comentarios'].extend([
            {'id': 20, 'comentario_id': 1, 'moderador_id': 'mod1', 'acao': 'manter',
             'justificativa': 'Improcedente', 'criado_em': ha_91_dias},
            {'id': 21, 'comentario_id': 2, 'moderador_id': 'mod1', 'acao': 'manter',
             'justificativa': 'Recente', 'criado_em': ha_45_dias},
        ])

        # Contestações: 1 encerrada >90d (apaga), 1 aberta >90d (mantém)
        cliente.tabelas['contestacoes_comentarios'].extend([
            {'id': 30, 'comentario_id': 1, 'usuario_id': 'u1', 'justificativa': 'Revisão antiga',
             'criado_em': ha_95_dias, 'resolvida_em': ha_91_dias},
            {'id': 31, 'comentario_id': 2, 'usuario_id': 'u2', 'justificativa': 'Revisão aberta',
             'criado_em': ha_95_dias, 'resolvida_em': None},
        ])

        repo = ModeracaoRepository(cliente)
        resumo = repo.descartar_registros_expirados(dias_retencao=90, agora=agora)

        self.assertEqual(resumo['denuncias_removidas'], 1)
        self.assertEqual(resumo['moderacoes_removidas'], 1)
        self.assertEqual(resumo['contestacoes_removidas'], 1)
        self.assertEqual([d['id'] for d in cliente.tabelas['denuncias_comentarios']], [11, 12])
        self.assertEqual([m['id'] for m in cliente.tabelas['moderacoes_comentarios']], [21])
        self.assertEqual([c['id'] for c in cliente.tabelas['contestacoes_comentarios']], [31])
        # Comentários publicados continuam todos intactos
        self.assertEqual([c['id'] for c in cliente.tabelas['comentarios']], [1, 2])


class TestRotinaAgendadaRetencao(unittest.TestCase):
    WORKFLOW = Path('.github/workflows/retencao_moderacao.yml')

    def test_script_executa_descarte_e_retorna_resumo(self):
        from datetime import datetime, timedelta, timezone
        from scripts.descartar_moderacao_90_dias import executar_descarte
        from tests.fake_supabase import ClienteFalso

        cliente = ClienteFalso()
        agora = datetime.now(timezone.utc)
        expirado = (agora - timedelta(days=95)).isoformat()
        cliente.tabelas['denuncias_comentarios'].append({
            'id': 1, 'comentario_id': 10, 'usuario_id': 'u1', 'motivo': 'spam',
            'criado_em': expirado, 'resolvida_em': expirado,
        })

        resumo = executar_descarte(cliente=cliente, dias_retencao=90, agora=agora)
        self.assertEqual(resumo['denuncias_removidas'], 1)
        self.assertEqual(cliente.tabelas['denuncias_comentarios'], [])

    def test_workflow_github_actions_agendado_diariamente(self):
        self.assertTrue(self.WORKFLOW.exists(), f'Workflow {self.WORKFLOW} deve existir.')
        conteudo = self.WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('schedule:', conteudo)
        self.assertIn('cron:', conteudo)
        self.assertIn('workflow_dispatch:', conteudo)
        self.assertIn('scripts/descartar_moderacao_90_dias.py', conteudo)


class TestCriteriosAceiteRetencao(unittest.TestCase):
    def test_fronteira_89_e_91_dias_e_validacao_de_parametro(self):
        from datetime import datetime, timedelta, timezone
        from app.repositorio import ModeracaoRepository
        from tests.fake_supabase import ClienteFalso

        cliente = ClienteFalso()
        agora = datetime.now(timezone.utc)
        ha_91_dias = (agora - timedelta(days=91)).isoformat()
        ha_89_dias = (agora - timedelta(days=89)).isoformat()

        cliente.tabelas['denuncias_comentarios'].extend([
            {'id': 1, 'comentario_id': 10, 'usuario_id': 'u1', 'motivo': 'spam',
             'criado_em': ha_91_dias, 'resolvida_em': ha_91_dias},
            {'id': 2, 'comentario_id': 10, 'usuario_id': 'u2', 'motivo': 'spam',
             'criado_em': ha_89_dias, 'resolvida_em': ha_89_dias},
        ])
        cliente.tabelas['moderacoes_comentarios'].extend([
            {'id': 3, 'comentario_id': 10, 'moderador_id': 'm1', 'acao': 'manter',
             'justificativa': 'Antiga', 'criado_em': ha_91_dias},
            {'id': 4, 'comentario_id': 10, 'moderador_id': 'm1', 'acao': 'manter',
             'justificativa': 'Dentro do prazo', 'criado_em': ha_89_dias},
        ])
        cliente.tabelas['contestacoes_comentarios'].extend([
            {'id': 5, 'comentario_id': 10, 'usuario_id': 'u1', 'justificativa': 'Antiga',
             'criado_em': ha_91_dias, 'resolvida_em': ha_91_dias},
            {'id': 6, 'comentario_id': 10, 'usuario_id': 'u2', 'justificativa': 'Dentro do prazo',
             'criado_em': ha_89_dias, 'resolvida_em': ha_89_dias},
        ])

        repo = ModeracaoRepository(cliente)
        for invalido in (0, -5, True, '90'):
            with self.assertRaises(ValueError):
                repo.descartar_registros_expirados(dias_retencao=invalido, agora=agora)

        resumo = repo.descartar_registros_expirados(dias_retencao=90, agora=agora)
        self.assertEqual(resumo['denuncias_removidas'], 1)
        self.assertEqual(resumo['moderacoes_removidas'], 1)
        self.assertEqual(resumo['contestacoes_removidas'], 1)
        self.assertEqual([d['id'] for d in cliente.tabelas['denuncias_comentarios']], [2])
        self.assertEqual([m['id'] for m in cliente.tabelas['moderacoes_comentarios']], [4])
        self.assertEqual([c['id'] for c in cliente.tabelas['contestacoes_comentarios']], [6])

    def test_rpc_descarte_remove_expirados_e_preserva_comentarios(self):
        from datetime import datetime, timedelta, timezone
        from tests.fake_supabase import ClienteFalso

        cliente = ClienteFalso()
        expirado = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        cliente.tabelas['comentarios'].append({
            'id': 1, 'usuario_id': 'u1', 'professor_id': 1, 'disciplina_id': 10,
            'texto': 'Comentário publicado preservado', 'criado_em': expirado, 'ocultado_em': None,
        })
        cliente.tabelas['moderacoes_comentarios'].append({
            'id': 1, 'comentario_id': 1, 'moderador_id': 'm1', 'acao': 'manter',
            'justificativa': 'Encerrado há 100 dias', 'criado_em': expirado,
        })

        resp = cliente.rpc('descartar_registros_moderacao_expirados', {'dias_retencao': 90}).execute()
        self.assertEqual(resp.data['moderacoes_removidas'], 1)
        self.assertEqual(len(cliente.tabelas['comentarios']), 1)


class TestPoliticaPrivacidadeRetencao(unittest.TestCase):
    def test_pagina_privacidade_documenta_retencao_de_90_dias(self):
        from app import create_app
        from tests.fake_supabase import ClienteFalso

        app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'chave-teste-local-com-mais-de-32-caracteres-1234',
            'SUPABASE_CLIENT': ClienteFalso(),
            'WTF_CSRF_ENABLED': False,
        })
        resp = app.test_client().get('/privacidade')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True).lower()
        self.assertIn('90 dias', html)
        self.assertIn('denúncia', html)
        self.assertIn('moderação', html)


if __name__ == '__main__':
    unittest.main()