import re
import unittest

from pathlib import Path
from flask import jsonify
from app import create_app
from app.controllers.session_controller import COOKIE_ACESSO, moderador_required
from app.validacoes import validar_contestacao, validar_decisao_moderacao
from tests.fake_supabase import ClienteFalso

class TestMigracaoModeracao(unittest.TestCase):
    MIGRACAO = Path('docs/migrations/008_moderacao_comentarios.sql')

    def _ler_sql(self):
        self.assertTrue(
            self.MIGRACAO.exists(),
            'A migração docs/migrations/008_moderacao_comentarios.sql deve existir.',
        )
        return self.MIGRACAO.read_text(encoding='utf-8').lower()

    def test_cria_tabelas_moderadores_decisoes_e_contestacoes(self):
        sql = self._ler_sql()
        for tabela in ('moderadores', 'moderacoes_comentarios', 'contestacoes_comentarios'):
            self.assertIn(f'create table if not exists {tabela}', sql)

    def test_valida_acoes_de_moderacao_e_justificativa_obrigatoria(self):
        sql = self._ler_sql()
        self.assertRegex(
            sql,
            r"check\s*\(\s*acao\s+in\s*\(\s*'manter'\s*,\s*'ocultar'\s*,\s*'restaurar'\s*\)\s*\)",
        )
        self.assertIn('ck_moderacoes_justificativa_tamanho', sql)
        self.assertIn('ck_contestacoes_justificativa_tamanho', sql)
        self.assertRegex(sql, r'moderador_id\s+uuid\s+not\s+null\s+references\s+perfis\(id\)')

    def test_indices_fila_historico_e_contestacao_ativa_unica(self):
        sql = self._ler_sql()
        self.assertIn('idx_moderacoes_comentario_criado', sql)
        self.assertIn('uq_contestacoes_ativa_comentario', sql)
        self.assertIn('idx_contestacoes_abertas', sql)

    def test_rls_privado_restrito_ao_service_role(self):
        sql = self._ler_sql()
        for tabela in ('moderadores', 'moderacoes_comentarios', 'contestacoes_comentarios'):
            self.assertIn(f'alter table {tabela} enable row level security;', sql)
            self.assertIn(f'revoke all on {tabela} from public, anon, authenticated;', sql)
            self.assertRegex(
                sql,
                rf'grant\s+[a-z,\s]+\s+on\s+{tabela}\s+to\s+service_role;',
            )
            # Nenhuma política pública para anon ou authenticated
            self.assertIsNone(
                re.search(rf'create\s+policy\s+.*\s+on\s+{tabela}\b', sql),
                f'A tabela {tabela} deve ser privada (sem policies para anon/authenticated).',
            )


class TestValidacoesModeracao(unittest.TestCase):
    def test_decisao_valida_normaliza_espacos(self):
        acao, justificativa, erros = validar_decisao_moderacao(' ocultar ', '  Ofensa pessoal clara.  ')
        self.assertEqual(acao, 'ocultar')
        self.assertEqual(justificativa, 'Ofensa pessoal clara.')
        self.assertEqual(erros, {})

    def test_decisao_recusa_acao_invalida_e_justificativa_curta_ou_longa(self):
        _, _, erros = validar_decisao_moderacao('apagar', 'a')
        self.assertIn('acao', erros)
        self.assertIn('justificativa', erros)

        _, _, erros_longa = validar_decisao_moderacao('manter', 'x' * 1001)
        self.assertIn('justificativa', erros_longa)

    def test_contestacao_exige_justificativa_entre_2_e_1000_caracteres(self):
        texto, erros = validar_contestacao('  Crítica apenas à didática.  ')
        self.assertEqual(texto, 'Crítica apenas à didática.')
        self.assertEqual(erros, {})

        _, erros_vazio = validar_contestacao('   ')
        self.assertIn('justificativa', erros_vazio)


class TestAutorizacaoModerador(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'chave-teste-local',
            'SUPABASE_CLIENT': self.cliente,
            'WTF_CSRF_ENABLED': False,
        })

        @self.app.get('/_teste/moderacao')
        @moderador_required
        def _rota_protegida():
            return jsonify({'ok': True}), 200

        self.web = self.app.test_client()

    def _logar_usuario(self, email, username, moderador=False):
        codigo = f'cod-{username}'
        verificador = f'ver-{username}'
        self.cliente.auth.preparar_retorno_google(
            codigo, email, {'nome': username.title(), 'username': username}, verificador
        )
        resposta = self.cliente.auth.exchange_code_for_session({
            'auth_code': codigo, 'code_verifier': verificador,
        })
        uid = str(resposta.user.id)
        self.cliente.table('perfis').insert({
            'id': uid, 'username': username, 'nome_completo': username.title(),
        }).execute()
        if moderador:
            self.cliente.table('moderadores').insert({'usuario_id': uid}).execute()
        self.web.set_cookie(COOKIE_ACESSO, resposta.session.access_token)
        return uid

    def test_visitante_nao_acessa_rota_de_moderacao(self):
        resp_html = self.web.get('/_teste/moderacao', headers={'Accept': 'text/html'})
        self.assertEqual(resp_html.status_code, 302)
        self.assertIn('/login', resp_html.headers['Location'])

        resp_json = self.web.get('/_teste/moderacao', headers={'Accept': 'application/json'})
        self.assertEqual(resp_json.status_code, 401)

    def test_usuario_comum_recebe_403_por_padrao(self):
        self._logar_usuario('aluno@gmail.com', 'aluno', moderador=False)
        resp_html = self.web.get('/_teste/moderacao', headers={'Accept': 'text/html'})
        self.assertEqual(resp_html.status_code, 403)

        resp_json = self.web.get('/_teste/moderacao', headers={'Accept': 'application/json'})
        self.assertEqual(resp_json.status_code, 403)

    def test_moderador_autorizado_acessa_rota(self):
        self._logar_usuario('mod@gmail.com', 'moderadora', moderador=True)
        resp = self.web.get('/_teste/moderacao', headers={'Accept': 'application/json'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {'ok': True})


class TestModeracaoRepository(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        from app.repositorio import ComentarioRepository, DenunciaRepository, ModeracaoRepository
        self.comentarios = ComentarioRepository(self.cliente)
        self.denuncias = DenunciaRepository(self.cliente)
        self.moderacao = ModeracaoRepository(self.cliente)

        self.autor_id = '11111111-1111-1111-1111-111111111111'
        self.denunciante_id = '22222222-2222-2222-2222-222222222222'
        self.moderador_id = '33333333-3333-3333-3333-333333333333'
        for uid, user in (
            (self.autor_id, 'autor'),
            (self.denunciante_id, 'denunciante'),
            (self.moderador_id, 'moderador'),
        ):
            self.cliente.table('perfis').insert({
                'id': uid, 'username': user, 'nome_completo': user.title(),
            }).execute()
        self.cliente.table('moderadores').insert({'usuario_id': self.moderador_id}).execute()

    def test_fila_mostra_somente_comentarios_denunciados(self):
        c1 = self.comentarios.criar(self.autor_id, 1, 10, 'Comentário normal sem denúncia.')
        c2 = self.comentarios.criar(self.autor_id, 1, 10, 'Comentário denunciado por ofensa.')
        self.denuncias.criar(c2, self.denunciante_id, 'ofensa', 'Ataque pessoal direto.')

        fila = self.moderacao.listar_fila()
        ids_na_fila = [item['comentario_id'] for item in fila]
        self.assertEqual(ids_na_fila, [c2])
        self.assertNotIn(c1, ids_na_fila)
        self.assertEqual(fila[0]['total_denuncias'], 1)
        self.assertEqual(fila[0]['denuncias'][0]['motivo'], 'ofensa')

    def test_decisao_ocultar_e_restaurar_registra_autor_justificativa_e_atualiza_comentario(self):
        cid = self.comentarios.criar(self.autor_id, 1, 10, 'Texto denunciado.')
        self.denuncias.criar(cid, self.denunciante_id, 'ofensa', 'Ofensa clara.')

        # Ocultar
        ok = self.moderacao.registrar_decisao(cid, self.moderador_id, 'ocultar', 'Violou regras.')
        self.assertTrue(ok)
        linha = self.cliente.table('comentarios').select('*').eq('id', cid).execute().data[0]
        self.assertIsNotNone(linha.get('ocultado_em'))
        # Denúncia aberta foi marcada como resolvida
        denuncia = self.cliente.table('denuncias_comentarios').select('*').eq('comentario_id', cid).execute().data[0]
        self.assertIsNotNone(denuncia.get('resolvida_em'))

        # Histórico registra moderador e justificativa
        decisoes = self.cliente.table('moderacoes_comentarios').select('*').eq('comentario_id', cid).execute().data
        self.assertEqual(len(decisoes), 1)
        self.assertEqual(decisoes[0]['moderador_id'], self.moderador_id)
        self.assertEqual(decisoes[0]['acao'], 'ocultar')
        self.assertEqual(decisoes[0]['justificativa'], 'Violou regras.')

        # Restaurar
        ok_rest = self.moderacao.registrar_decisao(cid, self.moderador_id, 'restaurar', 'Revisado após contestação.')
        self.assertTrue(ok_rest)
        linha_rest = self.cliente.table('comentarios').select('*').eq('id', cid).execute().data[0]
        self.assertIsNone(linha_rest.get('ocultado_em'))

    def test_decisao_manter_resolve_denuncias_sem_ocultar(self):
        cid = self.comentarios.criar(self.autor_id, 1, 10, 'Crítica respeitosa à didática.')
        self.denuncias.criar(cid, self.denunciante_id, 'fora_do_tema', None)

        self.assertTrue(
            self.moderacao.registrar_decisao(cid, self.moderador_id, 'manter', 'Crítica pedagógica válida.')
        )
        linha = self.cliente.table('comentarios').select('*').eq('id', cid).execute().data[0]
        self.assertIsNone(linha.get('ocultado_em'))

    def test_decisao_sem_justificativa_ou_comentario_inexistente(self):
        cid = self.comentarios.criar(self.autor_id, 1, 10, 'Texto qualquer.')
        with self.assertRaises(ValueError):
            self.moderacao.registrar_decisao(cid, self.moderador_id, 'ocultar', ' ')
        self.assertFalse(
            self.moderacao.registrar_decisao(99999, self.moderador_id, 'ocultar', 'Não existe.')
        )


class TestOcultacaoERepublicacao(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        from app.repositorio import ComentarioRepository, DenunciaRepository, ModeracaoRepository
        self.comentarios = ComentarioRepository(self.cliente)
        self.denuncias = DenunciaRepository(self.cliente)
        self.moderacao = ModeracaoRepository(self.cliente)

        self.autor_id = '11111111-1111-1111-1111-111111111111'
        self.denunciante_id = '22222222-2222-2222-2222-222222222222'
        self.moderador_id = '33333333-3333-3333-3333-333333333333'
        for uid, user in (
            (self.autor_id, 'autor'),
            (self.denunciante_id, 'denunciante'),
            (self.moderador_id, 'moderador'),
        ):
            self.cliente.table('perfis').insert({
                'id': uid, 'username': user, 'nome_completo': user.title(),
            }).execute()
        self.cliente.table('moderadores').insert({'usuario_id': self.moderador_id}).execute()

    def test_comentario_ocultado_sai_da_listagem_publica_e_nao_volta_por_edicao(self):
        cid = self.comentarios.criar(self.autor_id, 1, 10, 'Texto ofensivo inicial.')
        self.denuncias.criar(cid, self.denunciante_id, 'ofensa', 'Ataque pessoal.')
        self.moderacao.registrar_decisao(cid, self.moderador_id, 'ocultar', 'Contém ofensa pessoal.')

        # Sai da listagem pública e de buscar_visivel
        publicos, _ = self.comentarios.listar_por_professor(1)
        self.assertEqual([c['id'] for c in publicos], [])
        self.assertIsNone(self.comentarios.buscar_visivel(cid))

        # O autor ainda vê que o comentário está ocultado
        meu = self.comentarios.buscar_do_usuario(cid, self.autor_id)
        self.assertIsNotNone(meu)
        self.assertTrue(meu['ocultado'])

        # Autor edita o comentário: texto muda, mas continua ocultado (não republica)
        self.assertTrue(self.comentarios.atualizar(cid, self.autor_id, 10, 'Texto reescrito sem ofensa.'))
        publicos_apos_edicao, _ = self.comentarios.listar_por_professor(1)
        self.assertEqual([c['id'] for c in publicos_apos_edicao], [])
        self.assertTrue(self.comentarios.buscar_do_usuario(cid, self.autor_id)['ocultado'])

        # Só volta à listagem pública quando um moderador restaurar com justificativa
        self.moderacao.registrar_decisao(cid, self.moderador_id, 'restaurar', 'Texto adequado após revisão.')
        publicos_restaurados, _ = self.comentarios.listar_por_professor(1)
        self.assertEqual([c['id'] for c in publicos_restaurados], [cid])
        self.assertEqual(publicos_restaurados[0]['texto'], 'Texto reescrito sem ofensa.')

    def test_autor_consulta_seus_comentarios_ocultados_com_justificativa(self):
        cid = self.comentarios.criar(self.autor_id, 1, 10, 'Texto ocultado.')
        self.denuncias.criar(cid, self.denunciante_id, 'ofensa', None)
        self.moderacao.registrar_decisao(cid, self.moderador_id, 'ocultar', 'Linguagem inadequada.')

        ocultados = self.moderacao.listar_ocultados_do_usuario(self.autor_id)
        self.assertEqual(len(ocultados), 1)
        self.assertEqual(ocultados[0]['id'], cid)
        self.assertEqual(ocultados[0]['justificativa_moderacao'], 'Linguagem inadequada.')

        # Outro usuário não vê os comentários ocultados do autor
        self.assertEqual(self.moderacao.listar_ocultados_do_usuario(self.denunciante_id), [])
        

if __name__ == '__main__':
    unittest.main()