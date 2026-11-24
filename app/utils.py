import unicodedata


def normalizar_busca(texto):
    """Padroniza texto para buscas sem distinção de acentos, caixa ou espaços."""
    texto = unicodedata.normalize('NFKD', str(texto or ''))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return ''.join(texto.casefold().split())


# Partículas ignoradas nas iniciais do avatar (nomes em grafia comum: "João de Souza" -> "JS").
PARTICULAS_NOME = frozenset({'de', 'da', 'do', 'dos', 'das', 'e', 'di', 'del', 'van', 'von', 'du'})


def iniciais(nome):
    """Iniciais, em maiúsculas e com acento, das duas primeiras palavras que não são partículas.

    Vazio ou None devolve ''. Com uma só palavra restante, devolve uma letra.
    """
    palavras = [p for p in str(nome or '').split() if p.casefold() not in PARTICULAS_NOME]
    return ''.join(p[0] for p in palavras[:2]).upper()
