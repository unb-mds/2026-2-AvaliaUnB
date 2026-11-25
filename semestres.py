"""Configuração explícita do semestre de oferta, compartilhada pelo site e pela coleta.

O arquivo é versionado e só muda por revisão/deploy. Nunca deduzimos o semestre
atual da data, do maior par no banco ou de uma execução parcial do scraper.
"""
import json
import logging
from pathlib import Path

ARQUIVO_SEMESTRE_ATUAL = Path(__file__).resolve().parent / 'config' / 'semestre_atual.json'
log = logging.getLogger(__name__)


def validar_semestre(ano, periodo):
    """Par acadêmico válido; período 1 a 4, como no SIGAA. Rejeita bool e coerções."""
    if type(ano) is not int or not 1000 <= ano <= 9999:
        raise ValueError('O ano deve ser um inteiro com quatro dígitos.')
    if type(periodo) is not int or periodo not in (1, 2, 3, 4):
        raise ValueError('O período deve ser um inteiro entre 1 e 4.')
    return ano, periodo


def ler_semestre_atual(caminho=ARQUIVO_SEMESTRE_ATUAL):
    """Ausência/configuração inválida mantém o histórico; não interrompe o site."""
    if caminho is None:
        return None
    try:
        dados = json.loads(Path(caminho).read_text(encoding='utf-8'))
        atual = dados['semestre_atual']
        if atual is None:
            return None
        return validar_semestre(atual['ano'], atual['periodo'])
    except (OSError, UnicodeError, ValueError, TypeError, KeyError):
        log.warning('Semestre atual não configurado ou inválido; mantendo consulta histórica.')
        return None


def texto_semestre(semestre):
    return f'{semestre[0]}/{semestre[1]}'


def valor_semestre(semestre):
    return f'{semestre[0]}-{semestre[1]}'


def interpretar_semestre(texto):
    """Valor da URL, YYYY-P. Não interpreta datas nem aceita um ano abreviado."""
    if not isinstance(texto, str) or len(texto) != 6 or texto[4] != '-':
        raise ValueError('Semestre inválido. Use o formato AAAA-P.')
    if not texto[:4].isascii() or not texto[:4].isdigit() or texto[5] not in '1234':
        raise ValueError('Semestre inválido. Use o formato AAAA-P.')
    return validar_semestre(int(texto[:4]), int(texto[5]))
