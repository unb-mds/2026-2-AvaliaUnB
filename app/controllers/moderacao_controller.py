"""Lógica da área restrita de moderação de comentários (issue #216)."""
from flask import abort

from app.repositorio import repositorios
from app.validacoes import MOTIVOS_DENUNCIA, validar_contestacao, validar_decisao_moderacao

ACOES_ROTULOS = {
    'manter': 'Manter publicado',
    'ocultar': 'Ocultar da visão pública',
    'restaurar': 'Restaurar comentário',
}


def listar_fila():
    return repositorios().moderacao.listar_fila()


def motivos_denuncia():
    return MOTIVOS_DENUNCIA


def validar_decisao(dados):
    return validar_decisao_moderacao(dados.get('acao'), dados.get('justificativa'))


def decidir(comentario_id, moderador, acao, justificativa):
    ok = repositorios().moderacao.registrar_decisao(
        comentario_id, moderador['id'], acao, justificativa
    )
    if not ok:
        abort(404, description='Comentário não encontrado.')
    return True


def carregar_comentario_para_contestacao(comentario_id, usuario):
    """Carrega o comentário ocultado do próprio autor; 404 se não for dele ou não estiver oculto."""
    repos = repositorios()
    comentario = repos.comentarios.buscar_do_usuario(comentario_id, usuario['id'])
    if comentario is None or not comentario.get('ocultado'):
        abort(404, description='Comentário ocultado não encontrado.')
    professor = repos.professores.buscar_por_id(comentario['professor_id'])
    justificativa_mod = repos.moderacao.ultima_justificativa_ocultacao(comentario_id)
    ativa = repos.moderacao.buscar_contestacao_ativa(comentario_id)
    return comentario, professor, justificativa_mod, ativa


def validar_dados_contestacao(dados):
    return validar_contestacao(dados.get('justificativa'))


def registrar_contestacao(comentario_id, usuario, justificativa):
    return repositorios().moderacao.criar_contestacao(
        comentario_id, usuario['id'], justificativa
    )