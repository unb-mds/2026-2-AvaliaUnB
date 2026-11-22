"""Rotas restritas da área de moderação de comentários (issue #216)."""
from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.controllers import moderacao_controller as controller
from app.controllers.session_controller import moderador_required, obter_usuario_atual

moderacao_bp = Blueprint('moderacao', __name__)


@moderacao_bp.get('/moderacao')
@moderador_required
def fila():
    usuario = obter_usuario_atual()
    itens = controller.listar_fila()
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({'fila': itens}), 200
    return render_template(
        'moderacao.html',
        usuario=usuario,
        fila=itens,
        motivos=controller.motivos_denuncia(),
        acoes_rotulos=controller.ACOES_ROTULOS,
        erros={},
        comentario_erro_id=None,
    )


@moderacao_bp.post('/moderacao/comentarios/<int:comentario_id>/decidir')
@moderador_required
def decidir(comentario_id):
    usuario = obter_usuario_atual()
    quer_json = request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html
    acao, justificativa, erros = controller.validar_decisao(request.form)
    if erros:
        if quer_json:
            return jsonify({'erros': erros}), 400
        return render_template(
            'moderacao.html',
            usuario=usuario,
            fila=controller.listar_fila(),
            motivos=controller.motivos_denuncia(),
            acoes_rotulos=controller.ACOES_ROTULOS,
            erros=erros,
            comentario_erro_id=comentario_id,
            dados_form=request.form,
        ), 400

    controller.decidir(comentario_id, usuario, acao, justificativa)
    if quer_json:
        return jsonify({'mensagem': 'Decisão registrada com sucesso.', 'acao': acao}), 200
    return redirect(url_for('moderacao.fila'), code=303)