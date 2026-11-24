"""Manutenção dos dados do catálogo no Supabase (issue #235).

Subcomandos (rodar da raiz do repositório):

    python scraper/manutencao_banco.py duplicatas
        Relatório somente leitura de professores e disciplinas duplicados.
        Sai com código 1 se encontrar duplicatas.

    python scraper/manutencao_banco.py backup [--destino docs/backup]
        Exporta professores, disciplinas e turmas para CSV no mesmo formato
        do "Export to CSV" do Supabase (<tabela>_rows.csv).

    python scraper/manutencao_banco.py converter-nomes [--gravar]
        Converte os nomes em CAIXA ALTA já gravados para a grafia comum
        (professores.nome, professores.departamento e disciplinas.nome),
        com a mesma função usada pelo importador (texto_sigaa.grafia_comum).
        Sem --gravar só simula e mostra totais e exemplos. Com --gravar,
        atualiza por id, só os campos que mudam. Aborta, mesmo com --gravar,
        se algum nome de professor passar a colidir com outro. É idempotente.
        Rode o backup antes de gravar e só use o importador novo depois.

Só as tabelas públicas do catálogo entram no backup: avaliações, comentários
e perfis têm dados de usuários (LGPD) e não vão para o repositório.
"""
import argparse
import csv
import io
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from texto_sigaa import grafia_comum

PAGINA = 1000  # limite padrão de linhas por resposta do PostgREST

COLUNAS_BACKUP = {
    "professores": ["id", "nome", "departamento", "criado_em"],
    "disciplinas": ["id", "codigo", "nome", "criado_em"],
    "turmas": ["id", "professor_id", "disciplina_id", "ano", "periodo", "criado_em"],
}


def _supabase():
    """Import tardio: os helpers puros podem ser testados sem .env."""
    from supabase_client import supabase

    return supabase


# ---------- helpers puros ----------

def normalizar_chave(texto) -> str:
    """Chave de comparação: sem acentos, caixa alta e espaços colapsados."""
    sem_acento = unicodedata.normalize("NFKD", str(texto or ""))
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento.replace("\xa0", " ")).strip().upper()


def agrupar_duplicados(linhas: list, campo: str) -> dict:
    """{chave normalizada: [linhas]} só com as chaves que aparecem mais de uma vez."""
    grupos = defaultdict(list)
    for linha in linhas:
        grupos[normalizar_chave(linha.get(campo))].append(linha)
    return {chave: grupo for chave, grupo in sorted(grupos.items()) if len(grupo) > 1}


def formatar_valor(valor) -> str:
    """Formata como o export CSV do Supabase (timestamps no formato do Postgres)."""
    if valor is None:
        return ""
    texto = str(valor)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T[\d:.]+[+-]\d{2}:\d{2}", texto):
        texto = texto.replace("T", " ", 1)
        if texto.endswith(":00"):
            texto = texto[:-3]  # +00:00 -> +00
    return texto


def gerar_csv(linhas: list, colunas: list) -> str:
    """CSV com CRLF, aspas só quando preciso e sem quebra de linha no fim."""
    saida = io.StringIO()
    escritor = csv.writer(saida, lineterminator="\r\n")
    escritor.writerow(colunas)
    for linha in linhas:
        escritor.writerow([formatar_valor(linha.get(c)) for c in colunas])
    return saida.getvalue().removesuffix("\r\n")


# ---------- acesso ao banco ----------

def ler_tabela(cliente, tabela: str, colunas: str = "*") -> list:
    """Lê a tabela inteira, ordenada por id, paginando de PAGINA em PAGINA."""
    linhas, inicio = [], 0
    while True:
        pagina = (
            cliente.table(tabela).select(colunas).order("id")
            .range(inicio, inicio + PAGINA - 1).execute()
        ).data
        linhas.extend(pagina)
        if len(pagina) < PAGINA:
            return linhas
        inicio += PAGINA


def _imprimir_grupos(titulo: str, grupos: dict, formatar) -> None:
    print(f"\n--- {titulo}: {len(grupos)} grupo(s) ---")
    for chave, grupo in grupos.items():
        print(f"{chave}: " + " | ".join(formatar(l) for l in grupo))


def relatorio_duplicatas(cliente) -> int:
    """Imprime o relatório e devolve quantos grupos duplicados existem."""
    professores = ler_tabela(cliente, "professores", "id,nome,departamento")
    disciplinas = ler_tabela(cliente, "disciplinas", "id,codigo,nome")

    prof_dup = agrupar_duplicados(professores, "nome")
    disc_dup = agrupar_duplicados(disciplinas, "codigo")
    disc_mesmo_nome = agrupar_duplicados(disciplinas, "nome")

    print(f"Professores: {len(professores)} | Disciplinas: {len(disciplinas)}")
    _imprimir_grupos("PROFESSORES COM O MESMO NOME", prof_dup,
                     lambda p: f"#{p['id']} {p.get('departamento') or '(sem unidade)'}")
    _imprimir_grupos("DISCIPLINAS COM O MESMO CÓDIGO", disc_dup,
                     lambda d: f"#{d['id']} {d['nome']}")
    _imprimir_grupos("(informativo) DISCIPLINAS COM O MESMO NOME E CÓDIGOS DIFERENTES",
                     disc_mesmo_nome, lambda d: d["codigo"])
    return len(prof_dup) + len(disc_dup)


def gerar_backup(cliente, destino: Path) -> dict:
    """Grava <tabela>_rows.csv em `destino` e devolve {tabela: linhas}."""
    destino.mkdir(parents=True, exist_ok=True)
    totais = {}
    for tabela, colunas in COLUNAS_BACKUP.items():
        linhas = ler_tabela(cliente, tabela, ",".join(colunas))
        arquivo = destino / f"{tabela}_rows.csv"
        arquivo.write_text(gerar_csv(linhas, colunas), encoding="utf-8", newline="")
        totais[tabela] = len(linhas)
        print(f"[*] {arquivo}: {len(linhas)} linhas")
    return totais


# ---------- conversão dos nomes para a grafia comum (issue #236) ----------

# (tabela, campo, tipo de grafia_comum)
CAMPOS_NOMES = (
    ("professores", "nome", "professor"),
    ("professores", "departamento", "departamento"),
    ("disciplinas", "nome", "disciplina"),
)
EXEMPLOS_POR_CAMPO = 10
MAXIMO_COLISOES_LISTADAS = 30
PASSO_PROGRESSO = 100

AVISO_CONVERSAO = (
    "[!] Rode o backup antes de gravar (python scraper/manutencao_banco.py backup) e só "
    "use o importador novo depois da conversão: com o banco ainda em CAIXA ALTA, ele "
    "criaria professores duplicados."
)


def planejar_conversao(cliente) -> dict:
    """Lê as tabelas e calcula, por campo, o que mudaria. Não grava nada."""
    tabelas = {
        "professores": ler_tabela(cliente, "professores", "id,nome,departamento"),
        "disciplinas": ler_tabela(cliente, "disciplinas", "id,codigo,nome"),
    }
    campos = []
    for tabela, campo, tipo in CAMPOS_NOMES:
        mudancas = []
        for linha in tabelas[tabela]:
            antes = linha.get(campo)
            depois = grafia_comum(antes, tipo)
            if depois != antes:
                mudancas.append({"id": linha["id"], "antes": antes, "depois": depois})
        campos.append({"tabela": tabela, "campo": campo,
                       "total": len(tabelas[tabela]), "mudancas": mudancas})
    return {"tabelas": tabelas, "campos": campos}


def _mudancas_de(plano: dict, tabela: str, campo: str) -> list:
    return next(c["mudancas"] for c in plano["campos"]
                if c["tabela"] == tabela and c["campo"] == campo)


def colisoes_de_professores(plano: dict) -> list:
    """Grupos de professores que ficariam com o mesmo nome (exato ou por normalizar_chave).

    Cada nome convertido é comparado com o nome atual e o convertido de todos os outros
    professores. Só entram grupos com ao menos um registro alterado; duplicatas que já
    existem entre registros intactos são assunto do subcomando `duplicatas`.
    """
    novos = {m["id"]: m["depois"] for m in _mudancas_de(plano, "professores", "nome")}
    por_chave = defaultdict(dict)  # chave normalizada -> {id: valor}
    for linha in plano["tabelas"]["professores"]:
        for valor in (linha["nome"], novos.get(linha["id"])):
            if valor:
                por_chave[normalizar_chave(valor)].setdefault(linha["id"], valor)
    grupos = []
    for itens in por_chave.values():
        if len(itens) > 1 and any(i in novos for i in itens):
            grupos.append(sorted(itens.items()))
    return sorted(grupos)


def disciplinas_que_diferem_so_por_acento(plano: dict) -> list:
    """Informativo: nomes de disciplina que, já convertidos, só diferem por acento/caixa."""
    novos = {m["id"]: m["depois"] for m in _mudancas_de(plano, "disciplinas", "nome")}
    grupos = defaultdict(set)
    for linha in plano["tabelas"]["disciplinas"]:
        valor = novos.get(linha["id"], linha["nome"])
        grupos[normalizar_chave(valor)].add(valor)
    return sorted(sorted(v) for v in grupos.values() if len(v) > 1)


def _imprimir_plano(plano: dict) -> None:
    for c in plano["campos"]:
        mudam = c["mudancas"]
        print(f"\n--- {c['tabela']}.{c['campo']}: {c['total']} registro(s) | "
              f"mudariam: {len(mudam)} | já corretos: {c['total'] - len(mudam)} ---")
        passo = max(1, len(mudam) // EXEMPLOS_POR_CAMPO)
        for m in mudam[::passo][:EXEMPLOS_POR_CAMPO]:
            print(f"  #{m['id']}: {m['antes']!r} -> {m['depois']!r}")


def aplicar_conversao(cliente, plano: dict) -> dict:
    """Atualiza por id, um registro por vez, só os campos que mudam.

    O UPDATE só vale se os campos ainda tiverem o valor lido (outra rotina pode ter
    mudado o registro no meio); nesse caso o registro é pulado e a próxima execução
    o reavalia. Para na primeira falha. Devolve {'atualizados': Counter, 'pulados': n,
    'total': n, 'erro': texto ou None}.
    """
    por_registro = defaultdict(lambda: {"antes": {}, "depois": {}})
    for c in plano["campos"]:
        for m in c["mudancas"]:
            registro = por_registro[(c["tabela"], m["id"])]
            registro["antes"][c["campo"]] = m["antes"]
            registro["depois"][c["campo"]] = m["depois"]

    resultado = {"atualizados": Counter(), "pulados": 0, "total": len(por_registro), "erro": None}
    for n, ((tabela, id_), dados) in enumerate(sorted(por_registro.items()), 1):
        try:
            consulta = cliente.table(tabela).update(dados["depois"]).eq("id", id_)
            for campo, antes in dados["antes"].items():
                consulta = consulta.eq(campo, antes)
            gravou = bool(consulta.execute().data)
        except Exception as erro:
            resultado["erro"] = f"{tabela} #{id_}: {erro}"
            return resultado
        if gravou:
            for campo in dados["depois"]:
                resultado["atualizados"][f"{tabela}.{campo}"] += 1
        else:
            resultado["pulados"] += 1
        if n % PASSO_PROGRESSO == 0 or n == resultado["total"]:
            print(f"[*] Progresso: {n}/{resultado['total']} registros")
    return resultado


def converter_nomes(cliente, gravar: bool = False) -> int:
    """Simula (padrão) ou grava a conversão. 0 em sucesso; 1 em colisão ou falha."""
    print(AVISO_CONVERSAO)
    plano = planejar_conversao(cliente)
    _imprimir_plano(plano)

    colisoes = colisoes_de_professores(plano)
    if colisoes:
        print(f"\n[!] {len(colisoes)} colisão(ões) de nome de professor. NADA foi gravado.")
        for grupo in colisoes[:MAXIMO_COLISOES_LISTADAS]:
            print("  " + " <-> ".join(f"#{i} {valor!r}" for i, valor in grupo))
        if len(colisoes) > MAXIMO_COLISOES_LISTADAS:
            print(f"  ... e mais {len(colisoes) - MAXIMO_COLISOES_LISTADAS}")
        print("Resolva as colisões (ex.: unificando os registros) e rode de novo.")
        return 1

    so_acento = disciplinas_que_diferem_so_por_acento(plano)
    print(f"\n(informativo) Disciplinas que só diferem por acento depois da conversão: "
          f"{len(so_acento)} grupo(s). O código é a chave; isso não bloqueia.")
    for grupo in so_acento[:5]:
        print("  " + " | ".join(grupo))

    pendentes = sum(len(c["mudancas"]) for c in plano["campos"])
    if not gravar:
        print(f"\nSimulação: nada foi gravado ({pendentes} alteração(ões) pendente(s)). "
              "Use --gravar para aplicar.")
        return 0
    if not pendentes:
        print("\nNada a converter: todos os nomes já estão em grafia comum.")
        return 0

    resultado = aplicar_conversao(cliente, plano)
    atualizados = resultado["atualizados"]
    print("\n--- Resumo ---")
    for tabela, campo, _ in CAMPOS_NOMES:
        print(f"{tabela}.{campo}: {atualizados[f'{tabela}.{campo}']} atualizado(s)")
    if resultado["pulados"]:
        print(f"{resultado['pulados']} registro(s) pulado(s) por terem mudado durante a "
              "conversão; rode de novo para reavaliá-los.")
    if resultado["erro"]:
        print(f"[!] Falha ao atualizar {resultado['erro']}. Parou aqui, com "
              f"{sum(atualizados.values())} campo(s) já gravado(s). Reexecutar é seguro: "
              "a conversão é idempotente.")
        return 1
    return 0


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("duplicatas", help="relatório de professores/disciplinas duplicados")
    backup = sub.add_parser("backup", help="exporta o catálogo para CSV")
    backup.add_argument("--destino", type=Path, default=Path("docs/backup"),
                        help="pasta dos CSVs (padrão: docs/backup)")
    converter = sub.add_parser(
        "converter-nomes",
        help="converte nomes em CAIXA ALTA para a grafia comum (simulação por padrão)",
        description="Converte professores.nome, professores.departamento e disciplinas.nome "
                    "para a grafia comum. Sem --gravar só simula.",
    )
    converter.add_argument("--gravar", action="store_true",
                           help="grava as alterações (por id); sem esta flag nada é gravado")
    return parser


def main(argv=None, cliente=None) -> int:
    args = montar_parser().parse_args(argv)
    cliente = cliente or _supabase()
    if args.comando == "duplicatas":
        return 1 if relatorio_duplicatas(cliente) else 0
    if args.comando == "converter-nomes":
        return converter_nomes(cliente, gravar=args.gravar)
    gerar_backup(cliente, args.destino)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
