"""Confirmação explícita após cobertura e persistência validadas; gera arquivo para PR.

Executar da raiz: python -m scraper.confirmar_semestre coleta.json --confirmar 2026-2
Acrescente --gravar para gerar a configuração; sem isso, apenas valida e informa.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile

from semestres import (ARQUIVO_SEMESTRE_ATUAL, interpretar_semestre,
                       ler_semestre_atual)
from .validacao_coleta import validar_relatorio


def confirmar(relatorio, confirmacao, caminho=ARQUIVO_SEMESTRE_ATUAL, gravar=False,
              execucao=''):
    ano, periodo = interpretar_semestre(confirmacao)
    totais = validar_relatorio(relatorio, ano, periodo)
    atual = ler_semestre_atual(caminho)
    if atual is not None and (ano, periodo) < atual:
        raise ValueError('Uma reimportação de período anterior não pode substituir o semestre atual.')
    novo = {'semestre_atual': {'ano': ano, 'periodo': periodo},
            'coleta': {'execucao': execucao, 'gerado_em': relatorio['gerado_em'],
                       'assinatura_turmas': relatorio['assinatura_turmas'], **totais}}
    if gravar:
        destino = Path(caminho)
        destino.parent.mkdir(parents=True, exist_ok=True)
        # Um arquivo temporário no mesmo diretório evita deixar JSON incompleto.
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destino.parent,
                                         prefix='.semestre-', suffix='.json', delete=False) as arquivo:
            json.dump(novo, arquivo, ensure_ascii=False, indent=2)
            arquivo.write('\n')
            temporario = arquivo.name
        try:
            os.replace(temporario, destino)
        finally:
            if os.path.exists(temporario):
                os.unlink(temporario)
    return novo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('relatorio', type=Path)
    parser.add_argument('--confirmar', required=True, help='Semestre explícito, ex.: 2026-2')
    parser.add_argument('--config', type=Path, default=ARQUIVO_SEMESTRE_ATUAL)
    parser.add_argument('--gravar', action='store_true', help='Gera o arquivo para revisão em PR')
    args = parser.parse_args()
    try:
        relatorio = json.loads(args.relatorio.read_text(encoding='utf-8'))
        servidor, repositorio, run_id = (os.getenv(k, '') for k in
            ('GITHUB_SERVER_URL', 'GITHUB_REPOSITORY', 'GITHUB_RUN_ID'))
        execucao = f'{servidor}/{repositorio}/actions/runs/{run_id}' if all(
            (servidor, repositorio, run_id)) else ''
        resultado = confirmar(relatorio, args.confirmar, args.config, args.gravar, execucao)
    except (OSError, ValueError, TypeError, KeyError) as erro:
        parser.exit(1, f'Confirmação recusada: {erro}\n')
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    print('Configuração gerada para revisão e deploy.' if args.gravar else
          'Validação concluída. Nada foi alterado; use --gravar para gerar o arquivo.')


if __name__ == '__main__':
    main()
