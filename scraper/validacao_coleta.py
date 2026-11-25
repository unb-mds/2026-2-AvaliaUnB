"""Evidência de cobertura e integridade de uma coleta; sem Selenium ou credenciais."""
import hashlib
import json
from datetime import datetime, timezone

try:
    from .unidades_sigaa import eh_unidade_de_pos
except ImportError:  # execução direta de scraper/scraper_sigaa.py
    from unidades_sigaa import eh_unidade_de_pos


def _chaves_turmas(turmas):
    return sorted({(t['professor_nome'], t['disciplina_codigo'], t['ano'], t['periodo'])
                   for t in turmas})


def assinatura_turmas(turmas):
    return hashlib.sha256(json.dumps(_chaves_turmas(turmas), ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8')).hexdigest()


def montar_relatorio(ano, periodo, disponiveis, resultados, resumo, professores,
                     disciplinas, turmas, dry_run, persistencia_validada=False,
                     finalidade='regular'):
    return {
        'versao': 1, 'ano': int(ano), 'periodo': int(periodo),
        'gerado_em': datetime.now(timezone.utc).isoformat(),
        'finalidade': finalidade, 'modo': 'dry-run' if dry_run else 'gravar',
        'unidades_esperadas': sorted({str(v) for v, nome in disponiveis
                                      if not eh_unidade_de_pos(nome)}),
        'unidades_lidas': resultados,
        'linhas_puladas': dict(resumo.linhas_puladas),
        'a_definir_ignorados': resumo.a_definir_ignorados,
        'professores': sorted({p['nome'] for p in professores}),
        'disciplinas': sorted({d['codigo'] for d in disciplinas}),
        'turmas': [dict(professor_nome=p, disciplina_codigo=d, ano=a, periodo=b)
                   for p, d, a, b in _chaves_turmas(turmas)],
        'assinatura_turmas': assinatura_turmas(turmas),
        'persistencia_validada': persistencia_validada is True,
    }


def validar_relatorio(relatorio, ano, periodo, exigir_persistencia=True):
    """Recusa parcial, vazia, falha, fora do período, histórica ou antecipada."""
    if not isinstance(relatorio, dict):
        raise ValueError('Relatório deve ser um objeto JSON.')
    if type(relatorio.get('versao')) is not int or relatorio['versao'] != 1:
        raise ValueError('Versão de relatório não suportada.')
    if (type(relatorio.get('ano')) is not int or type(relatorio.get('periodo')) is not int
            or (relatorio['ano'], relatorio['periodo']) != (ano, periodo)):
        raise ValueError('O período coletado difere do semestre a confirmar.')
    if relatorio.get('finalidade') != 'regular':
        raise ValueError('Coleta histórica ou antecipada não confirma o semestre atual.')
    esperadas = relatorio.get('unidades_esperadas')
    lidas = relatorio.get('unidades_lidas')
    if not isinstance(esperadas, list) or not esperadas or not isinstance(lidas, list):
        raise ValueError('Não há evidência de cobertura das unidades.')
    if (any(not isinstance(c, str) or not c.isascii() or not c.isdigit() for c in esperadas)
            or len(set(esperadas)) != len(esperadas)
            or any(not isinstance(u, dict) or not isinstance(u.get('codigo'), str) for u in lidas)):
        raise ValueError('Identificadores de unidade inválidos ou repetidos.')
    codigos = [u.get('codigo') for u in lidas]
    if len(codigos) != len(set(codigos)) or set(codigos) != set(esperadas):
        raise ValueError('Coleta parcial: nem todas as unidades foram processadas.')
    if any(u.get('status') not in ('ok', 'vazio') for u in lidas):
        raise ValueError('Uma ou mais unidades falharam.')
    if any(relatorio.get('linhas_puladas', {}).values()):
        raise ValueError('Há linhas puladas por erro; revisar antes de confirmar.')
    professores, disciplinas, turmas = (relatorio.get(k) for k in
                                         ('professores', 'disciplinas', 'turmas'))
    if not professores or not disciplinas or not turmas:
        raise ValueError('Coleta vazia não confirma o semestre atual.')
    for t in turmas:
        if (type(t.get('ano')) is not int or type(t.get('periodo')) is not int
                or (t['ano'], t['periodo']) != (ano, periodo)
                or t.get('professor_nome') not in professores
                or t.get('disciplina_codigo') not in disciplinas):
            raise ValueError('Turma com período ou vínculo inválido.')
    if relatorio.get('assinatura_turmas') != assinatura_turmas(turmas):
        raise ValueError('A assinatura das turmas não corresponde ao relatório.')
    if exigir_persistencia and (relatorio.get('modo') != 'gravar'
                                or relatorio.get('persistencia_validada') is not True):
        raise ValueError('Dry-run não ativa semestre: falta conferir a persistência no banco.')
    return {'unidades': len(esperadas), 'turmas': len(_chaves_turmas(turmas)),
            'professores': len(set(professores)), 'disciplinas': len(set(disciplinas))}
