"""Filtro automático do texto dos comentários (issue #214, decisão C10).

Roda no servidor, no envio, ao publicar e ao editar. Bloqueia só violações claras: dados
pessoais (e-mail, telefone, CPF, matrícula), links e palavrões ou ofensas de uma lista em
arquivo separado. Não julga opinião e não usa IA: os casos duvidosos passam e ficam para a
moderação por denúncia. A função é pura e não registra o texto em log.
"""
import re
import unicodedata
from pathlib import Path

DADOS_PESSOAIS = 'dados_pessoais'
LINK = 'link'
OFENSA = 'ofensa'

ARQUIVO_TERMOS = Path(__file__).resolve().parent / 'dados' / 'termos_bloqueados.txt'

# O que vem depois de "Seu comentário não foi publicado/salvo porque ...".
_MOTIVOS = {
    DADOS_PESSOAIS: 'parece conter dados pessoais (telefone, e-mail, CPF ou matrícula). '
                    'Remova e tente novamente.',
    LINK: 'contém um link. Remova e tente novamente.',
    OFENSA: 'contém linguagem ofensiva. Reescreva e tente novamente.',
}


def mensagem_bloqueio(categoria, acao='publicado'):
    """Mensagem para a pessoa, sem revelar o trecho que disparou o filtro nem a lista."""
    return f'Seu comentário não foi {acao} porque {_MOTIVOS[categoria]}'


def normalizar(texto):
    """NFKC, sem caracteres invisíveis (zero-width etc.), minúsculas e sem acentos."""
    texto = unicodedata.normalize('NFKC', texto or '')
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Cf')
    texto = unicodedata.normalize('NFD', texto.lower())
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn')


# ------------------------------------------------------------------ dados pessoais e links

_AT = r'(?:@|\(at\)|\[at\]|\barroba\b)'
_PONTO = r'(?:\.|\(dot\)|\[dot\]|\bponto\b)'
_TLDS = r'(?:com|net|org|edu|gov|br|io|info|app|dev|gg|ly)'
_PROVEDORES = r'(?:gmail|hotmail|outlook|yahoo|live|icloud|bol|uol|unb|aluno|protonmail)'

_EMAIL = re.compile(
    rf'[a-z0-9._%+-]+\s*{_AT}\s*(?:[a-z0-9-]+\s*{_PONTO}\s*)+{_TLDS}(?![a-z0-9])'
    rf'|[a-z0-9._%+-]+\s*{_AT}\s*{_PROVEDORES}(?![a-z0-9])')

_LINK = re.compile(
    r'(?:https?://|ftp://|www\.)\S'
    rf'|(?<![a-z0-9@.-])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+{_TLDS}(?![a-z0-9])')

_MATRICULA = re.compile(r'(?<!\d)\d(?:[.\-/]?\d){7,}(?!\d)')
_MATRICULA_ESPACADA = re.compile(r'(?<!\d)\d{3,}(?: \d{3,}){2,}(?!\d)')
_CPF = re.compile(r'(?<!\d)\d{3}[. ]?\d{3}[. ]?\d{3}[- ]?\d{2}(?!\d)')
_TELEFONE_DDD = re.compile(
    r'(?<!\d)(?:\+?55[ .-]?)?\(?\d{2}\)?[ .-]?9?[ .-]?\d{4}[ .-]?\d{4}(?!\d)')
_TELEFONE_LOCAL = re.compile(r'(?<!\d)9?\d{4}[ .-]\d{4}(?!\d)|(?<!\d)9[ .-]?\d{4}[ .-]?\d{4}(?!\d)')
_DATA = re.compile(r'(?:0?[1-9]|[12]\d|3[01])([./-])(?:0?[1-9]|1[0-2])\1(?:19|20)\d\d')


def _so_anos(trecho):
    """True se o trecho é só uma lista de anos (2024-2025, 2023 2024): não é matrícula."""
    grupos = re.findall(r'\d+', trecho)
    return all(len(g) == 4 and 1900 <= int(g) <= 2099 for g in grupos)


def _tem_dados_pessoais(texto):
    if _EMAIL.search(texto):
        return True
    for m in _MATRICULA.finditer(texto):
        trecho = m.group()
        grupos = re.findall(r'\d+', trecho)
        codigo_de_disciplina = (m.start() > 0 and texto[m.start() - 1].isalpha()
                                and len(grupos) >= 2 and len(grupos[0]) == 4)
        if not (_so_anos(trecho) or _DATA.fullmatch(trecho) or codigo_de_disciplina):
            return True
    for padrao in (_MATRICULA_ESPACADA, _CPF, _TELEFONE_DDD, _TELEFONE_LOCAL):
        for m in padrao.finditer(texto):
            trecho = m.group()
            # "FGA0011 2024.1": código de disciplina seguido do semestre não é telefone.
            codigo_e_ano = (m.start() > 0 and texto[m.start() - 1].isalpha()
                            and _so_anos(' '.join(re.findall(r'\d+', trecho)[1:2] or ['0'])))
            if not (_so_anos(trecho) or codigo_e_ano):
                return True
    return False


# ------------------------------------------------------------------ palavrões e ofensas

_LEET = str.maketrans('01345789@$', 'oieastbgas')


def _palavras(texto):
    """Palavras em minúsculas sem acento; letras soltas em sequência (p.u.t.a) são unidas."""
    palavras = re.findall(r'[a-z0-9@$]+', texto)
    unidas, soltas = [], []
    for palavra in palavras + ['']:
        if len(palavra) == 1 and palavra.isalpha():
            soltas.append(palavra)
            continue
        unidas.extend([''.join(soltas)] if len(soltas) >= 3 else soltas)
        soltas = []
        if palavra:
            unidas.append(palavra)
    return unidas


def _reduzir(texto):
    """Reduz letras repetidas ('puuuuta' vira 'puta'); só letras, números ficam como estão."""
    return re.sub(r'([a-z])\1+', r'\1', texto)


def _carregar_termos(caminho=ARQUIVO_TERMOS):
    termos = set()
    for linha in Path(caminho).read_text(encoding='utf-8').splitlines():
        linha = linha.strip()
        if not linha or linha.startswith('#'):
            continue
        termo = ' '.join(_reduzir(p) for p in _palavras(normalizar(linha)))
        if termo:
            termos.add(termo)
    if not termos:
        return None
    ordenados = sorted(termos, key=len, reverse=True)
    corpo = '|'.join(re.escape(t) for t in ordenados)
    return re.compile(rf'(?<![a-z0-9])(?:{corpo})s?(?![a-z0-9])')


_TERMOS = _carregar_termos()


def _tem_ofensa(texto):
    palavras = _palavras(texto)
    variantes = [palavras]
    # Escrita com números e símbolos no lugar de letras (m3rda, put@): só em palavras com letras.
    variantes.append([p.translate(_LEET) if re.search(r'[a-z]', p) else p for p in palavras])
    for variante in variantes:
        if _TERMOS.search(' '.join(_reduzir(p) for p in variante)):
            return True
    return False


# ------------------------------------------------------------------ interface pública

def verificar_comentario(texto):
    """None se o texto pode seguir; senão a categoria bloqueada (DADOS_PESSOAIS, LINK, OFENSA).

    Deve rodar depois da validação de tamanho e antes de gravar. Não guarda nem registra o texto.
    """
    normalizado = normalizar(texto)
    if _tem_dados_pessoais(normalizado):
        return DADOS_PESSOAIS
    if _LINK.search(normalizado):
        return LINK
    if _tem_ofensa(normalizado):
        return OFENSA
    return None
