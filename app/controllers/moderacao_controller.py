"""Lógica da área restrita de moderação de comentários (issue #216)."""
from flask import abort

from app.repositorio import repositorios
from app.validacoes import MOTIVOS_DENUNCIA, validar_decisao_moderacao

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