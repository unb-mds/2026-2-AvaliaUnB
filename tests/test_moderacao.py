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


if __name__ == '__main__':
    unittest.main()