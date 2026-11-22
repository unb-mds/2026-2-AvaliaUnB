"""Helpers puros de texto do scraper do SIGAA (sem selenium nem Supabase)."""
import re

A_DEFINIR = "A DEFINIR DOCENTE"

# Grafia comum dos nomes (issue #236). Listas fáceis de editar: tudo em minúsculas
# nas partículas e em maiúsculas nas siglas.
TIPOS_NOME = ("professor", "disciplina", "departamento")

# Ficam em minúsculo, exceto no início de um trecho (texto, depois de ":" e de " - ").
PARTICULAS = frozenset({
    "de", "da", "do", "dos", "das", "e", "em", "na", "no", "nas", "nos",
    "ao", "aos", "à", "às", "a", "o", "as", "os", "um", "uma",
    "di", "del", "van", "von", "du",
    "para", "com", "por", "sobre", "sem", "como", "que",
    "pelo", "pela", "pelos", "pelas", "sob", "entre", "até",
})

# Siglas fixas, só para disciplina e departamento. "UNB" é tratada à parte (vira "UnB").
SIGLAS = frozenset({"TCC", "TV", "LGBT", "LSB", "PSL", "PBSL", "LS", "WRTV", "DPG", "DAP", "EJA", "EDF"})

# Algarismos romanos (só I, V e X, até XXXIX), apenas em disciplinas e como palavra inteira.
_ROMANO = re.compile(r"X{0,3}(?:IX|IV|V?I{0,3})")
_SEPARADORES_DE_TRECHO = ("-", "–", "—")
_APOSTROFOS = "'’´`"


def normalizar_texto(texto) -> str:
    """Troca \\xa0 por espaço, colapsa espaços/quebras e remove as pontas."""
    if not texto:
        return ""
    return re.sub(r"\s+", " ", str(texto).replace("\xa0", " ")).strip()


def _tem_minuscula(texto: str) -> bool:
    return any(c.lower() == c and c.upper() != c for c in texto)


def _tem_maiuscula(texto: str) -> bool:
    return any(c.upper() == c and c.lower() != c for c in texto)


def _maiuscula_inicial(palavra: str) -> str:
    return palavra[:1].upper() + palavra[1:].lower()


def grafia_comum(texto, tipo):
    """Converte um nome em CAIXA ALTA para a grafia comum, mantendo os acentos.

    `tipo` é "professor", "disciplina" ou "departamento" (ValueError nos demais).
    Só converte textos 100% em caixa alta: se houver qualquer letra minúscula, ou se
    o texto for vazio, None ou sem letras, devolve o valor como veio (idempotente).
    Partículas (de, da, e...) ficam em minúsculo, menos no início de um trecho;
    siglas e algarismos romanos seguem as listas e regras do topo do módulo.
    """
    if tipo not in TIPOS_NOME:
        raise ValueError(f"Tipo de nome inválido: {tipo!r} (esperado {', '.join(TIPOS_NOME)}).")
    if not texto or not _tem_maiuscula(texto) or _tem_minuscula(texto):
        return texto

    partes = []
    inicio_de_trecho = True
    depois_da_barra = False
    for pedaco in re.split(r"(\s+)", texto):
        if not pedaco or pedaco.isspace():
            partes.append(pedaco)
            continue
        if pedaco in _SEPARADORES_DE_TRECHO:
            partes.append(pedaco)
            inicio_de_trecho = True
            depois_da_barra = False
            continue

        primeira = True
        resultado, posicao = [], 0
        for achado in re.finditer(r"[^\W\d_]+", pedaco):
            resultado.append(pedaco[posicao:achado.start()])
            palavra = achado.group()
            antes = pedaco[achado.start() - 1] if achado.start() > 0 else ""
            depois = pedaco[achado.end()] if achado.end() < len(pedaco) else ""
            minuscula = palavra.lower()
            colada = (antes != "" and (antes in _APOSTROFOS or antes == "-" or antes.isdigit())) or depois.isdigit()
            if tipo == "departamento" and (antes == "/" or (primeira and depois_da_barra)):
                novo = palavra
            elif tipo != "professor" and palavra in SIGLAS:
                novo = palavra
            elif tipo != "professor" and palavra == "UNB":
                novo = "UnB"
            elif tipo == "disciplina" and _ROMANO.fullmatch(palavra):
                novo = palavra
            elif (minuscula in PARTICULAS and not colada
                  and not (primeira and inicio_de_trecho)):
                novo = minuscula
            else:
                novo = _maiuscula_inicial(palavra)
            resultado.append(novo)
            posicao = achado.end()
            primeira = False
        resultado.append(pedaco[posicao:])
        partes.append("".join(resultado))
        inicio_de_trecho = pedaco.endswith(":")
        depois_da_barra = pedaco.endswith("/")
    return "".join(partes)


class UnidadeInvalidaError(ValueError):
    """Unidade não selecionada ou com texto inválido no formulário."""


def validar_unidade(texto) -> str:
    """Devolve o texto completo da unidade normalizado ou levanta erro.

    Rejeita texto vazio e a opção-placeholder do select (ex.: '-- SELECIONE --').
    """
    unidade = normalizar_texto(texto)
    if not unidade or "SELECIONE" in unidade.upper():
        raise UnidadeInvalidaError(
            f"Unidade inválida ou não selecionada (texto lido: {unidade!r})."
        )
    return unidade


def validar_ano(texto) -> str:
    """Ano com 4 dígitos (ex.: '2026'); levanta ValueError caso contrário."""
    ano = normalizar_texto(texto)
    if not re.fullmatch(r"\d{4}", ano):
        raise ValueError(f"Ano inválido: {ano!r} (esperado 4 dígitos, ex.: 2026).")
    return ano


def validar_periodo(texto) -> str:
    """Período de 1 a 4 (valores do select do SIGAA); levanta ValueError caso contrário."""
    periodo = normalizar_texto(texto)
    if periodo not in ("1", "2", "3", "4"):
        raise ValueError(f"Período inválido: {periodo!r} (esperado 1, 2, 3 ou 4).")
    return periodo


def professores_em_varias_unidades(professores) -> dict[str, list[str]]:
    """Docentes que aparecem em mais de uma unidade.

    Recebe dicts com 'nome' e 'departamento'. Os nomes são comparados sem
    diferença de caixa ou espaços; a chave do resultado é o nome normalizado
    em maiúsculas e o valor, as unidades em ordem alfabética.
    """
    unidades_por_nome = {}
    for p in professores:
        nome = normalizar_texto(p["nome"]).upper()
        unidades_por_nome.setdefault(nome, set()).add(p["departamento"])
    return {
        nome: sorted(unidades)
        for nome, unidades in sorted(unidades_por_nome.items())
        if len(unidades) > 1
    }


def eh_a_definir(nome: str) -> bool:
    return normalizar_texto(nome).upper() == A_DEFINIR


def _nomes_da_celula(texto) -> list[str]:
    """Todos os nomes da célula (inclusive 'A DEFINIR DOCENTE'), sem '(NNh)'.

    Delimitadores: quebra de linha, ',', ';' e o próprio sufixo '(NNh)'
    (docentes podem vir separados só por espaço depois dele). O último nome
    pode vir sem sufixo.
    """
    nomes = []
    for parte in re.split(r"[\r\n,;]+", str(texto or "").replace("\xa0", " ")):
        for pedaco in re.split(r"\(\s*\d+\s*h\s*\)", parte):
            nome = normalizar_texto(pedaco)
            if nome:
                nomes.append(nome)
    return nomes


def extrair_docentes(texto) -> list[str]:
    """Separa os docentes de uma célula, sem o sufixo '(NNh)'.

    'A DEFINIR DOCENTE', vazios e repetidos ficam de fora.
    """
    docentes = []
    for nome in _nomes_da_celula(texto):
        if not eh_a_definir(nome) and nome not in docentes:
            docentes.append(nome)
    return docentes


def docentes_em_grafia_comum(texto) -> list[str]:
    """Docentes da célula já em grafia comum, sem repetidos (issue #236).

    A conversão vem depois de `extrair_docentes`, que ainda enxerga 'A DEFINIR DOCENTE'
    em caixa alta e o descarta. O resultado é o único texto de nome usado no fluxo.
    """
    nomes = []
    for nome in extrair_docentes(texto):
        convertido = grafia_comum(nome, "professor")
        if convertido not in nomes:
            nomes.append(convertido)
    return nomes


def departamento_da_unidade(texto) -> str:
    """Departamento a gravar: o texto da unidade validado, em grafia comum.

    A seleção da opção no formulário continua usando o texto cru do SIGAA.
    """
    return grafia_comum(validar_unidade(texto), "departamento")


def disciplina_do_titulo(texto):
    """{'codigo', 'nome'} do título 'CÓDIGO - NOME', com o nome em grafia comum.

    O código não muda. Devolve None se o título não tiver o separador ' - '.
    """
    texto = (texto or "").strip()
    if " - " not in texto:
        return None
    codigo, nome = texto.split(" - ", 1)
    return {"codigo": codigo.strip(), "nome": grafia_comum(nome.strip(), "disciplina")}


def contar_a_definir(texto) -> int:
    """Quantas vezes 'A DEFINIR DOCENTE' aparece na célula."""
    return sum(1 for nome in _nomes_da_celula(texto) if eh_a_definir(nome))
