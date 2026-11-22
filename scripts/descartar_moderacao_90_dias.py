"""Rotina de descarte LGPD (issue #217): apaga denúncias, decisões e contestações encerradas há >90 dias."""
import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.repositorio import ModeracaoRepository
from app.supabase_db import get_supabase


def executar_descarte(cliente=None, dias_retencao=90, agora=None):
    """Executa o descarte via ModeracaoRepository e devolve o resumo das remoções."""
    repo = ModeracaoRepository(cliente or get_supabase())
    return repo.descartar_registros_expirados(dias_retencao=dias_retencao, agora=agora)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Descarta registros encerrados de denúncia e moderação após 90 dias (LGPD).'
    )
    parser.add_argument(
        '--dias',
        type=int,
        default=90,
        help='Prazo de retenção em dias após o encerramento (padrão: 90).',
    )
    args = parser.parse_args(argv)
    resumo = executar_descarte(dias_retencao=args.dias)
    print(json.dumps(resumo, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())