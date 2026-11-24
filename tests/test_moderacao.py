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
            r'moderador_id\s+uuid\s+references\s+perfis\(id\)\s+on\s+delete\s+set\s+null',
        )
        self.assertIn('ck_moderacoes_justificativa_tamanho', sql)
        self.assertIn('ck_contestacoes_justificativa_tamanho', sql)
        self.assertRegex(
            sql,
            r'moderador_id\s+uuid\s+references\s+perfis\(id\)\s+on\s+delete\s+set\s+null',
        )

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

    def test_fila_esvazia_apos_decisao_e_mantem_apenas_pendentes(self):
        c1 = self.comentarios.criar(self.autor_id, 1, 10, 'Comentário que será decidido.')
        c2 = self.comentarios.criar(self.autor_id, 1, 10, 'Comentário ainda pendente.')
        self.denuncias.criar(c1, self.denunciante_id, 'ofensa', 'Ofensa.')
        self.denuncias.criar(c2, self.denunciante_id, 'spam', 'Spam.')

        self.moderacao.registrar_decisao(c1, self.moderador_id, 'manter', 'Sem violação.')

        fila = self.moderacao.listar_fila()
        self.assertEqual([item['comentario_id'] for item in fila], [c2])

        # Decidindo o segundo, a fila esvazia completamente
        self.moderacao.registrar_decisao(c2, self.moderador_id, 'ocultar', 'Spam confirmado.')
        self.assertEqual(self.moderacao.listar_fila(), [])

    def test_fila_inclui_contestacao_aberta_sem_nenhuma_denuncia(self):
        cid = self.comentarios.criar(self.autor_id, 1, 10, 'Comentário ocultado sem denúncia.')
        self.moderacao.registrar_decisao(cid, self.moderador_id, 'ocultar', 'Ocultação administrativa.')
        self.assertEqual(self.moderacao.listar_fila(), [])

        self.moderacao.criar_contestacao(cid, self.autor_id, 'Peço revisão do comentário.')

        fila = self.moderacao.listar_fila()
        self.assertEqual([item['comentario_id'] for item in fila], [cid])
        self.assertEqual(fila[0]['denuncias'], [])
        self.assertEqual(fila[0]['denuncias_abertas'], 0)
        self.assertEqual(len(fila[0]['contestacoes']), 1)

    def test_fila_ordena_pela_pendencia_aberta_mais_antiga(self):
        c_recente = self.comentarios.criar(self.autor_id, 1, 10, 'Denúncia mais recente.')
        c_contestacao_antiga = self.comentarios.criar(self.autor_id, 1, 10, 'Contestação mais antiga.')
        c_denuncia_media = self.comentarios.criar(self.autor_id, 1, 10, 'Denúncia intermediária.')

        self.cliente.tabelas['denuncias_comentarios'].extend([
            {
                'id': 901,
                'comentario_id': c_recente,
                'usuario_id': self.denunciante_id,
                'motivo': 'spam',
                'explicacao': None,
                'criado_em': '2026-05-03T10:00:00+00:00',
                'resolvida_em': None,
            },
            {
                'id': 902,
                'comentario_id': c_denuncia_media,
                'usuario_id': self.denunciante_id,
                'motivo': 'ofensa',
                'explicacao': None,
                'criado_em': '2026-05-02T10:00:00+00:00',
                'resolvida_em': None,
            },
        ])
        self.cliente.tabelas['contestacoes_comentarios'].append({
            'id': 903,
            'comentario_id': c_contestacao_antiga,
            'usuario_id': self.autor_id,
            'justificativa': 'Solicito reavaliação.',
            'criado_em': '2026-05-01T10:00:00+00:00',
            'resolvida_em': None,
        })

        fila = self.moderacao.listar_fila()
        self.assertEqual(
            [item['comentario_id'] for item in fila],
            [c_contestacao_antiga, c_denuncia_media, c_recente],
        )

    def test_recusa_restaurar_comentario_publicado(self):
        cid = self.comentarios.criar(self.autor_id, 1, 10, 'Comentário publicado.')
        with self.assertRaises(ValueError):
            self.moderacao.registrar_decisao(cid, self.moderador_id, 'restaurar', 'Tentativa inválida.')

        decisoes = self.cliente.table('moderacoes_comentarios').select('*').eq('comentario_id', cid).execute().data
        self.assertEqual(decisoes, [])

    def test_comentario_ocultado_recusa_ocultar_novamente_mas_permite_manter_contestacao(self):
        cid = self.comentarios.criar(self.autor_id, 1, 10, 'Comentário que será ocultado.')
        self.moderacao.registrar_decisao(cid, self.moderador_id, 'ocultar', 'Ofensa comprovada.')
        self.moderacao.criar_contestacao(cid, self.autor_id, 'Peço reavaliação.')
        self.assertEqual([item['comentario_id'] for item in self.moderacao.listar_fila()], [cid])

        with self.assertRaises(ValueError):
            self.moderacao.registrar_decisao(cid, self.moderador_id, 'ocultar', 'Ocultar de novo.')

        # "manter" em comentário oculto nega a contestação, mantém oculto e esvazia a fila
        self.assertTrue(
            self.moderacao.registrar_decisao(
                cid, self.moderador_id, 'manter', 'Contestação indeferida: ofensa mantida.'
            )
        )
        self.assertEqual(self.moderacao.listar_fila(), [])
        comentario = self.cliente.table('comentarios').select('*').eq('id', cid).execute().data[0]
        self.assertIsNotNone(comentario['ocultado_em'])
        self.assertIsNone(self.moderacao.buscar_contestacao_ativa(cid))
        decisoes = self.cliente.table('moderacoes_comentarios').select('*').eq('comentario_id', cid).execute().data
        self.assertEqual([d['acao'] for d in decisoes], ['ocultar', 'manter'])
    

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

class TestRotasModeracao(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'chave-teste-local',
            'SUPABASE_CLIENT': self.cliente,
            'WTF_CSRF_ENABLED': False,
        })
        self.web = self.app.test_client()

    def _logar(self, email, username, moderador=False):
        codigo = f'cod-{username}'
        verificador = f'ver-{username}'
        self.cliente.auth.preparar_retorno_google(
            codigo, email, {'nome': username.title(), 'username': username}, verificador
        )
        resp = self.cliente.auth.exchange_code_for_session({
            'auth_code': codigo, 'code_verifier': verificador,
        })
        uid = str(resp.user.id)
        self.cliente.table('perfis').insert({
            'id': uid, 'username': username, 'nome_completo': username.title(),
        }).execute()
        if moderador:
            self.cliente.table('moderadores').insert({'usuario_id': uid}).execute()
        self.web.set_cookie(COOKIE_ACESSO, resp.session.access_token)
        return uid

    def _criar_comentario_denunciado(self):
        from app.repositorio import ComentarioRepository, DenunciaRepository
        autor_id = '11111111-1111-1111-1111-111111111111'
        denunciante_id = '22222222-2222-2222-2222-222222222222'
        for uid, user in ((autor_id, 'autor1'), (denunciante_id, 'denunciante1')):
            self.cliente.table('perfis').insert({
                'id': uid, 'username': user, 'nome_completo': user.title(),
            }).execute()
        comentarios = ComentarioRepository(self.cliente)
        denuncias = DenunciaRepository(self.cliente)
        c_normal = comentarios.criar(autor_id, 1, 10, 'Comentário normal sem denúncia.')
        c_denunciado = comentarios.criar(autor_id, 1, 10, 'Comentário ofensivo denunciado.')
        denuncias.criar(c_denunciado, denunciante_id, 'ofensa', 'Contém ataque pessoal.')
        return c_normal, c_denunciado

    def test_fila_bloqueia_comum_e_exibe_somente_denunciados_para_moderador(self):
        self._criar_comentario_denunciado()

        # Usuário comum recebe 403
        self._logar('comum@gmail.com', 'comum', moderador=False)
        self.assertEqual(self.web.get('/moderacao').status_code, 403)

        # Moderador acessa a fila e vê apenas o denunciado
        self._logar('mod@gmail.com', 'moderadora', moderador=True)
        resp = self.web.get('/moderacao')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn('Comentário ofensivo denunciado.', html)
        self.assertNotIn('Comentário normal sem denúncia.', html)
        self.assertNotIn('style=', html)

    def test_post_decidir_registra_ocultar_e_valida_erros(self):
        _, c_denunciado = self._criar_comentario_denunciado()

        # Usuário comum não decide
        self._logar('comum@gmail.com', 'comum', moderador=False)
        resp_negado = self.web.post(
            f'/moderacao/comentarios/{c_denunciado}/decidir',
            data={'acao': 'ocultar', 'justificativa': 'Tentativa indevida.'},
        )
        self.assertEqual(resp_negado.status_code, 403)

        # Moderador sem justificativa recebe 400
        self._logar('mod@gmail.com', 'moderadora', moderador=True)
        resp_invalido = self.web.post(
            f'/moderacao/comentarios/{c_denunciado}/decidir',
            data={'acao': 'ocultar', 'justificativa': ' '},
        )
        self.assertEqual(resp_invalido.status_code, 400)

        # Moderador com justificativa válida oculta e redireciona (303)
        resp_ok = self.web.post(
            f'/moderacao/comentarios/{c_denunciado}/decidir',
            data={'acao': 'ocultar', 'justificativa': 'Ofensa pessoal comprovada.'},
        )
        self.assertEqual(resp_ok.status_code, 303)
        linha = self.cliente.table('comentarios').select('*').eq('id', c_denunciado).execute().data[0]
        self.assertIsNotNone(linha.get('ocultado_em'))

    def test_post_decidir_recusa_acao_incompativel_com_estado_com_400(self):
        _, c_denunciado = self._criar_comentario_denunciado()
        self._logar('mod@gmail.com', 'moderadora', moderador=True)

        # Comentário publicado não pode ser restaurado
        resp_rest = self.web.post(
            f'/moderacao/comentarios/{c_denunciado}/decidir',
            data={'acao': 'restaurar', 'justificativa': 'Tentativa em publicado.'},
        )
        self.assertEqual(resp_rest.status_code, 400)

        # Oculta o comentário (transição válida)
        resp_ok = self.web.post(
            f'/moderacao/comentarios/{c_denunciado}/decidir',
            data={'acao': 'ocultar', 'justificativa': 'Ofensa comprovada.'},
        )
        self.assertEqual(resp_ok.status_code, 303)

        # Comentário oculto não pode ser ocultado de novo
        resp_ocultar_dup = self.web.post(
            f'/moderacao/comentarios/{c_denunciado}/decidir',
            data={'acao': 'ocultar', 'justificativa': 'Tentativa duplicada.'},
            headers={'Accept': 'application/json'},
        )
        self.assertEqual(resp_ocultar_dup.status_code, 400)
        self.assertIn('acao', resp_ocultar_dup.get_json()['erros'])

        # Comentário oculto pode receber "manter" (ex.: negar contestação mantendo oculto)
        resp_manter_oculto = self.web.post(
            f'/moderacao/comentarios/{c_denunciado}/decidir',
            data={'acao': 'manter', 'justificativa': 'Mantido oculto após revisão.'},
            headers={'Accept': 'application/json'},
        )
        self.assertEqual(resp_manter_oculto.status_code, 200)
        self.assertEqual(resp_manter_oculto.get_json()['acao'], 'manter')

    def test_fila_autorizacao_cobre_visitante_comum_e_moderador(self):
        _, c_denunciado = self._criar_comentario_denunciado()

        # 1. Visitante (sem login): 302 para /login em HTML e 401 em JSON
        resp_vis_html = self.web.get('/moderacao', headers={'Accept': 'text/html'})
        self.assertEqual(resp_vis_html.status_code, 302)
        self.assertIn('/login', resp_vis_html.headers['Location'])

        resp_vis_json = self.web.get('/moderacao', headers={'Accept': 'application/json'})
        self.assertEqual(resp_vis_json.status_code, 401)

        # 2. Usuário comum: 403 em HTML e JSON
        self._logar('comum@gmail.com', 'comum', moderador=False)
        self.assertEqual(
            self.web.get('/moderacao', headers={'Accept': 'text/html'}).status_code,
            403,
        )
        self.assertEqual(
            self.web.get('/moderacao', headers={'Accept': 'application/json'}).status_code,
            403,
        )

        # 3. Moderador: 200 em HTML e JSON com o comentário denunciado
        self._logar('mod@gmail.com', 'moderadora', moderador=True)
        resp_mod_html = self.web.get('/moderacao', headers={'Accept': 'text/html'})
        self.assertEqual(resp_mod_html.status_code, 200)
        self.assertIn('Comentário ofensivo denunciado.', resp_mod_html.get_data(as_text=True))

        resp_mod_json = self.web.get('/moderacao', headers={'Accept': 'application/json'})
        self.assertEqual(resp_mod_json.status_code, 200)
        ids_fila = [item['comentario_id'] for item in resp_mod_json.get_json()['fila']]
        self.assertEqual(ids_fila, [c_denunciado])

    def test_decidir_autorizacao_cobre_visitante_comum_e_moderador(self):
        _, c_denunciado = self._criar_comentario_denunciado()
        payload = {'acao': 'ocultar', 'justificativa': 'Ofensa pessoal comprovada.'}

        # 1. Visitante (sem login): 302 para /login em HTML e 401 em JSON
        resp_vis_html = self.web.post(
            f'/moderacao/comentarios/{c_denunciado}/decidir',
            data=payload,
            headers={'Accept': 'text/html'},
        )
        self.assertEqual(resp_vis_html.status_code, 302)
        self.assertIn('/login', resp_vis_html.headers['Location'])

        resp_vis_json = self.web.post(
            f'/moderacao/comentarios/{c_denunciado}/decidir',
            data=payload,
            headers={'Accept': 'application/json'},
        )
        self.assertEqual(resp_vis_json.status_code, 401)

        # 2. Usuário comum: 403 em HTML e JSON
        self._logar('comum@gmail.com', 'comum', moderador=False)
        self.assertEqual(
            self.web.post(
                f'/moderacao/comentarios/{c_denunciado}/decidir',
                data=payload,
                headers={'Accept': 'text/html'},
            ).status_code,
            403,
        )
        self.assertEqual(
            self.web.post(
                f'/moderacao/comentarios/{c_denunciado}/decidir',
                data=payload,
                headers={'Accept': 'application/json'},
            ).status_code,
            403,
        )

        # Nenhuma decisão foi gravada por visitante ou usuário comum
        decisoes_antes = (
            self.cliente.table('moderacoes_comentarios')
            .select('*')
            .eq('comentario_id', c_denunciado)
            .execute()
            .data
        )
        self.assertEqual(decisoes_antes, [])

        # 3. Moderador: registra a decisão com sucesso (200 em JSON)
        self._logar('mod@gmail.com', 'moderadora', moderador=True)
        resp_mod = self.web.post(
            f'/moderacao/comentarios/{c_denunciado}/decidir',
            data=payload,
            headers={'Accept': 'application/json'},
        )
        self.assertEqual(resp_mod.status_code, 200)
        self.assertEqual(resp_mod.get_json()['acao'], 'ocultar')


class TestContestacaoAutor(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'chave-teste-local',
            'SUPABASE_CLIENT': self.cliente,
            'WTF_CSRF_ENABLED': False,
        })
        self.web = self.app.test_client()

    def _logar(self, email, username, moderador=False):
        codigo = f'cod-{username}'
        verificador = f'ver-{username}'
        self.cliente.auth.preparar_retorno_google(
            codigo, email, {'nome': username.title(), 'username': username}, verificador
        )
        resp = self.cliente.auth.exchange_code_for_session({
            'auth_code': codigo, 'code_verifier': verificador,
        })
        uid = str(resp.user.id)
        if not self.cliente.table('perfis').select('id').eq('id', uid).execute().data:
            self.cliente.table('perfis').insert({
                'id': uid, 'username': username, 'nome_completo': username.title(),
            }).execute()
        if moderador and not self.cliente.table('moderadores').select('usuario_id').eq('usuario_id', uid).execute().data:
            self.cliente.table('moderadores').insert({'usuario_id': uid}).execute()
        self.web.set_cookie(COOKIE_ACESSO, resp.session.access_token)
        return uid

    def _preparar_comentario_ocultado(self):
        from app.repositorio import ComentarioRepository, DenunciaRepository, ModeracaoRepository
        autor_id = self._logar('autor@gmail.com', 'autor', moderador=False)
        outro_id = self._logar('outro@gmail.com', 'outro', moderador=False)
        mod_id = self._logar('mod@gmail.com', 'moderadora', moderador=True)

        comentarios = ComentarioRepository(self.cliente)
        denuncias = DenunciaRepository(self.cliente)
        moderacao = ModeracaoRepository(self.cliente)

        cid = comentarios.criar(autor_id, 1, 10, 'Comentário crítico sobre a didática.')
        denuncias.criar(cid, outro_id, 'ofensa', 'Denúncia inicial.')
        moderacao.registrar_decisao(cid, mod_id, 'ocultar', 'Linguagem considerada inadequada.')
        return cid

    def test_terceiro_nao_acessa_nem_envia_contestacao_de_outro_autor(self):
        cid = self._preparar_comentario_ocultado()
        self._logar('outro@gmail.com', 'outro', moderador=False)

        self.assertEqual(self.web.get(f'/comentarios/{cid}/contestar').status_code, 404)
        self.assertEqual(
            self.web.post(
                f'/comentarios/{cid}/contestar',
                data={'justificativa': 'Tentativa de terceiro.'},
            ).status_code,
            404,
        )

    def test_autor_contesta_decisao_e_pedido_aparece_na_fila_da_moderacao(self):
        cid = self._preparar_comentario_ocultado()
        self._logar('autor@gmail.com', 'autor', moderador=False)

        # GET exibe o comentário e a justificativa da moderação
        resp_get = self.web.get(f'/comentarios/{cid}/contestar')
        self.assertEqual(resp_get.status_code, 200)
        html = resp_get.get_data(as_text=True)
        self.assertIn('Linguagem considerada inadequada.', html)
        self.assertNotIn('style=', html)

        # POST inválido retorna 400
        resp_invalido = self.web.post(
            f'/comentarios/{cid}/contestar', data={'justificativa': ' '}
        )
        self.assertEqual(resp_invalido.status_code, 400)

        # POST válido registra contestação e redireciona (303)
        resp_ok = self.web.post(
            f'/comentarios/{cid}/contestar',
            data={'justificativa': 'Não houve ofensa, apenas relato pedagógico.'},
        )
        self.assertEqual(resp_ok.status_code, 303)

        # Segunda contestação enquanto a primeira está aberta retorna 409
        resp_dup = self.web.post(
            f'/comentarios/{cid}/contestar',
            data={'justificativa': 'Tentando enviar de novo.'},
        )
        self.assertEqual(resp_dup.status_code, 409)

        # Moderador visualiza a contestação na fila
        self._logar('mod@gmail.com', 'moderadora', moderador=True)
        html_fila = self.web.get('/moderacao').get_data(as_text=True)
        self.assertIn('Não houve ofensa, apenas relato pedagógico.', html_fila)

    def test_perfil_exibe_comentarios_ocultados_com_link_contestar_somente_para_o_autor(self):
        cid = self._preparar_comentario_ocultado()

        # Autor acessa /perfil em HTML
        self._logar('autor@gmail.com', 'autor', moderador=False)
        resp_html = self.web.get('/perfil', headers={'Accept': 'text/html'})
        self.assertEqual(resp_html.status_code, 200)
        html = resp_html.get_data(as_text=True)
        self.assertIn('Comentários ocultados', html)
        self.assertIn('Comentário crítico sobre a didática.', html)
        self.assertIn('Linguagem considerada inadequada.', html)
        self.assertIn(f'/comentarios/{cid}/contestar', html)
        self.assertIn('Contestar', html)

        # Autor acessa /perfil em JSON
        resp_json = self.web.get('/perfil', headers={'Accept': 'application/json'})
        self.assertEqual(resp_json.status_code, 200)
        ocultados = resp_json.get_json()['comentarios_ocultados']
        self.assertEqual(len(ocultados), 1)
        self.assertEqual(ocultados[0]['id'], cid)

        # Outro usuário não vê comentários ocultados do autor
        self._logar('outro@gmail.com', 'outro', moderador=False)
        resp_outro = self.web.get('/perfil', headers={'Accept': 'text/html'})
        self.assertEqual(resp_outro.status_code, 200)
        html_outro = resp_outro.get_data(as_text=True)
        self.assertNotIn('Comentários ocultados', html_outro)
        self.assertNotIn(f'/comentarios/{cid}/contestar', html_outro)


class TestFluxoCompletoModeracao(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'chave-teste-local',
            'SUPABASE_CLIENT': self.cliente,
            'WTF_CSRF_ENABLED': False,
        })
        self.web = self.app.test_client()

    def _logar(self, email, username, moderador=False):
        codigo = f'cod-{username}'
        verificador = f'ver-{username}'
        self.cliente.auth.preparar_retorno_google(
            codigo, email, {'nome': username.title(), 'username': username}, verificador
        )
        resp = self.cliente.auth.exchange_code_for_session({
            'auth_code': codigo, 'code_verifier': verificador,
        })
        uid = str(resp.user.id)
        if not self.cliente.table('perfis').select('id').eq('id', uid).execute().data:
            self.cliente.table('perfis').insert({
                'id': uid, 'username': username, 'nome_completo': username.title(),
            }).execute()
        if moderador and not self.cliente.table('moderadores').select('usuario_id').eq('usuario_id', uid).execute().data:
            self.cliente.table('moderadores').insert({'usuario_id': uid}).execute()
        self.web.set_cookie(COOKIE_ACESSO, resp.session.access_token)
        return uid

    def test_ciclo_completo_denuncia_ocultacao_edicao_contestacao_e_restauracao(self):
        # 1. Autor publica comentário no perfil do professor 1 (disciplina 10)
        self._logar('autor@gmail.com', 'autor', moderador=False)
        resp_pub = self.web.post(
            '/professores/1/comentarios',
            data={'disciplina_id': '10', 'texto': 'Comentário inicial com termo ofensivo.'},
        )
        self.assertEqual(resp_pub.status_code, 303)
        cid = self.cliente.table('comentarios').select('id').execute().data[0]['id']

        # Comentário aparece publicamente no perfil
        html_publico = self.web.get('/professores/1').get_data(as_text=True)
        self.assertIn('Comentário inicial com termo ofensivo.', html_publico)

        # 2. Outro usuário denuncia o comentário
        self._logar('denunciante@gmail.com', 'denunciante', moderador=False)
        resp_den = self.web.post(
            f'/comentarios/{cid}/denunciar',
            data={'motivo': 'ofensa', 'explicacao': 'Linguagem ofensiva.'},
        )
        self.assertEqual(resp_den.status_code, 303)

        # Usuário comum não acessa a moderação
        self.assertEqual(self.web.get('/moderacao').status_code, 403)

        # 3. Moderador vê o comentário na fila e oculta com justificativa
        self._logar('mod@gmail.com', 'moderadora', moderador=True)
        html_fila = self.web.get('/moderacao').get_data(as_text=True)
        self.assertIn('Comentário inicial com termo ofensivo.', html_fila)

        resp_ocultar = self.web.post(
            f'/moderacao/comentarios/{cid}/decidir',
            data={'acao': 'ocultar', 'justificativa': 'Contém ofensa pessoal.'},
        )
        self.assertEqual(resp_ocultar.status_code, 303)

        # 4. Comentário saiu da listagem pública
        html_apos_ocultar = self.web.get('/professores/1').get_data(as_text=True)
        self.assertNotIn('Comentário inicial com termo ofensivo.', html_apos_ocultar)

        # 5. Autor edita o comentário ocultado: texto muda, mas NÃO volta à listagem pública
        self._logar('autor@gmail.com', 'autor', moderador=False)
        resp_edit = self.web.post(
            f'/comentarios/{cid}/editar',
            data={'disciplina_id': '10', 'texto': 'Comentário revisado focando apenas na didática.'},
        )
        self.assertEqual(resp_edit.status_code, 303)
        html_apos_edicao = self.web.get('/professores/1').get_data(as_text=True)
        self.assertNotIn('Comentário revisado focando apenas na didática.', html_apos_edicao)

        # 6. Autor envia contestação privada
        resp_cont = self.web.post(
            f'/comentarios/{cid}/contestar',
            data={'justificativa': 'Removi o termo ofensivo, solicito restauração.'},
        )
        self.assertEqual(resp_cont.status_code, 303)

        # 7. Moderador vê a contestação na fila e restaura o comentário com justificativa
        self._logar('mod@gmail.com', 'moderadora', moderador=True)
        html_fila_cont = self.web.get('/moderacao').get_data(as_text=True)
        self.assertIn('Removi o termo ofensivo, solicito restauração.', html_fila_cont)

        resp_rest = self.web.post(
            f'/moderacao/comentarios/{cid}/decidir',
            data={'acao': 'restaurar', 'justificativa': 'Texto adequado após revisão do autor.'},
        )
        self.assertEqual(resp_rest.status_code, 303)

        # 8. Comentário restaurado volta à listagem pública com o texto editado
        html_final = self.web.get('/professores/1').get_data(as_text=True)
        self.assertIn('Comentário revisado focando apenas na didática.', html_final)

        # Verifica que todas as decisões ficaram registradas com moderador e justificativa
        decisoes = self.cliente.table('moderacoes_comentarios').select('*').eq('comentario_id', cid).execute().data
        self.assertEqual(len(decisoes), 2)
        self.assertEqual([d['acao'] for d in decisoes], ['ocultar', 'restaurar'])
        for d in decisoes:
            self.assertTrue(d['moderador_id'])
            self.assertTrue(d['justificativa'])

            

if __name__ == '__main__':
    unittest.main()