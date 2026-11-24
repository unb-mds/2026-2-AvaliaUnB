"""Rotas restritas da área de moderação de comentários (issue #216)."""
from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from app.controllers import moderacao_controller as controller
from app.controllers.session_controller import login_required, moderador_required, obter_usuario_atual

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
    if not erros:
        try:
            controller.decidir(comentario_id, usuario, acao, justificativa)
        except ValueError as erro:
            erros = {'acao': str(erro)}

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

    if quer_json:
        return jsonify({'mensagem': 'Decisão registrada com sucesso.', 'acao': acao}), 200
    return redirect(url_for('moderacao.fila'), code=303)


@moderacao_bp.route('/comentarios/<int:comentario_id>/contestar', methods=['GET', 'POST'])
@login_required
def contestar_comentario(comentario_id):
    """Formulário privado de contestação para o autor de um comentário ocultado (issue #216)."""
    usuario = obter_usuario_atual()
    quer_json = request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html
    comentario, professor, justificativa_mod, ativa = controller.carregar_comentario_para_contestacao(
        comentario_id, usuario
    )
    erros, status, texto_form = {}, 200, ''

    if request.method == 'POST':
        if ativa:
            status = 409
            erros['contestacao'] = 'Você já possui uma contestação em análise para este comentário.'
        else:
            texto_form = request.form.get('justificativa', '')
            justificativa, erros = controller.validar_dados_contestacao(request.form)
            if erros:
                status = 400
            elif controller.registrar_contestacao(comentario_id, usuario, justificativa):
                if quer_json:
                    return jsonify({'mensagem': 'Contestação enviada para revisão.'}), 201
                return redirect(
                    url_for('moderacao.contestar_comentario', comentario_id=comentario_id),
                    code=303,
                )
            else:
                status = 409
                erros['contestacao'] = 'Você já possui uma contestação em análise para este comentário.'
        if quer_json:
            return jsonify({'erros': erros}), status

    return render_template(
        'contestar_comentario.html',
        usuario=usuario,
        professor=professor,
        comentario=comentario,
        justificativa_moderacao=justificativa_mod,
        contestacao_ativa=ativa,
        erros=erros,
        texto_form=texto_form,
    ), status