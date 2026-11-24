"""Trava do importador contra professores duplicados (issue #236), com o cliente falso."""
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

import manutencao_banco
import persistencia_sigaa
from persistencia_sigaa import (
    COMANDO_CONVERSAO,
    ConversaoPendenteError,
    conflitos_de_grafia,
    gravar_catalogo,
    verificar_conversao_pendente,
)
from tests.fake_supabase import ClienteFalso

PROFESSORES = [
    {"nome": "Maria da Costa", "departamento": "Instituto de Artes - Brasília"},
    {"nome": "João Silva", "departamento": "Instituto de Artes - Brasília"},
]
DISCIPLINAS = [{"codigo": "FGA0100", "nome": "Introdução à Física II"}]
TURMAS = [
    {"disciplina_codigo": "FGA0100", "professor_nome": "Maria da Costa", "ano": 2026, "periodo": 2},
    {"disciplina_codigo": "FGA0100", "professor_nome": "João Silva", "ano": 2026, "periodo": 2},
]


def cliente_com(nomes):
    cliente = ClienteFalso()
    cliente.tabelas["professores"] = [
        {"id": i, "nome": nome, "departamento": ""} for i, nome in enumerate(nomes, 1)]
    cliente.tabelas["disciplinas"], cliente.tabelas["turmas"] = [], []
    return cliente


def tentar_gravar(cliente):
    with redirect_stdout(io.StringIO()):
        return gravar_catalogo(PROFESSORES, DISCIPLINAS, TURMAS, cliente)


class TestConflitosDeGrafia(unittest.TestCase):
    def test_nome_em_caixa_alta_com_o_mesmo_nome_normalizado_e_conflito(self):
        self.assertEqual(conflitos_de_grafia(["Maria da Costa"], ["MARIA DA COSTA"]),
                         [("MARIA DA COSTA", "Maria da Costa")])

    def test_variacao_de_acento_e_espacos_tambem_e_conflito(self):
        self.assertEqual(conflitos_de_grafia(["José Ávila"], ["JOSE  AVILA", "OUTRA PESSOA"]),
                         [("JOSE  AVILA", "José Ávila")])

    def test_nomes_identicos_nao_sao_conflito(self):
        self.assertEqual(conflitos_de_grafia(["Maria da Costa"], ["Maria da Costa"]), [])
        # nome em CAIXA ALTA que a fonte ainda manda em CAIXA ALTA (grafia não convertida)
        self.assertEqual(conflitos_de_grafia(["MARIA DA COSTA"], ["MARIA DA COSTA"]), [])

    def test_nome_ja_em_grafia_comum_no_banco_nao_e_conflito(self):
        for existente in ("Luciana Oliveira Militão", "Gianni Carlo Gomes", "Gabriel Jamur Gomes"):
            with self.subTest(existente=existente):
                # mesmo nome sem acento ou em outra caixa vindo da fonte: o do banco já está correto
                self.assertEqual(conflitos_de_grafia([existente.upper()], [existente]), [])
                self.assertEqual(conflitos_de_grafia([existente.replace("ã", "a")], [existente]), [])

    def test_sem_correspondencia_nao_ha_conflito(self):
        self.assertEqual(conflitos_de_grafia(["Ana Lima"], ["BRUNO SOUZA"]), [])
        self.assertEqual(conflitos_de_grafia([], ["BRUNO SOUZA"]), [])
        self.assertEqual(conflitos_de_grafia(["Ana Lima"], []), [])


class TestTravaNoFluxoDeGravacao(unittest.TestCase):
    def test_banco_em_caixa_alta_para_com_a_mensagem_e_nao_grava_nada(self):
        cliente = cliente_com(["MARIA DA COSTA", "JOÃO SILVA", "PAULO LIMA"])
        antes = [dict(p) for p in cliente.tabelas["professores"]]
        with self.assertRaises(ConversaoPendenteError) as contexto:
            tentar_gravar(cliente)
        self.assertEqual(cliente.upserts, [])  # nenhum upsert, em nenhuma tabela
        self.assertEqual(cliente.tabelas["professores"], antes)
        self.assertEqual(cliente.tabelas["disciplinas"], [])
        self.assertEqual(cliente.tabelas["turmas"], [])
        mensagem = str(contexto.exception)
        self.assertIn("2 conflito(s)", mensagem)
        self.assertIn("'MARIA DA COSTA' -> 'Maria da Costa'", mensagem)
        self.assertIn("'JOÃO SILVA' -> 'João Silva'", mensagem)
        self.assertIn(f"Rode {COMANDO_CONVERSAO} antes de usar este importador.", mensagem)
        self.assertIn("python scraper/manutencao_banco.py converter-nomes --gravar", mensagem)
        self.assertIn("Nada foi gravado.", mensagem)

    def test_mensagem_mostra_no_maximo_5_exemplos(self):
        cliente = cliente_com([f"PROFESSOR {i}" for i in range(1, 9)])
        novos = [{"nome": f"Professor {i}", "departamento": ""} for i in range(1, 9)]
        with self.assertRaises(ConversaoPendenteError) as contexto:
            verificar_conversao_pendente(novos, cliente)
        mensagem = str(contexto.exception)
        self.assertEqual(mensagem.count("' -> '"), 5)  # só os exemplos
        self.assertIn("8 conflito(s)", mensagem)
        self.assertIn("... e mais 3", mensagem)

    def test_banco_ja_convertido_grava_normalmente(self):
        cliente = cliente_com(["Maria da Costa", "João Silva", "Paulo Lima"])
        tentar_gravar(cliente)
        self.assertEqual(sorted(p["nome"] for p in cliente.tabelas["professores"]),
                         ["João Silva", "Maria da Costa", "Paulo Lima"])
        self.assertEqual(len(cliente.tabelas["disciplinas"]), 1)
        self.assertEqual(len(cliente.tabelas["turmas"]), 2)

    def test_banco_vazio_grava_normalmente(self):
        cliente = cliente_com([])
        tentar_gravar(cliente)
        self.assertEqual(len(cliente.tabelas["professores"]), 2)
        self.assertEqual(len(cliente.tabelas["disciplinas"]), 1)
        self.assertEqual(len(cliente.tabelas["turmas"]), 2)

    def test_professores_que_ja_estavam_em_grafia_comum_nao_geram_conflito(self):
        cliente = cliente_com(["Luciana Oliveira Militão", "Gianni Carlo Gomes", "MARIA OUTRA"])
        novos = [{"nome": "Luciana Oliveira Militão", "departamento": ""},
                 {"nome": "Gianni Carlo Gomes", "departamento": ""}]
        verificar_conversao_pendente(novos, cliente)  # não levanta

    def test_enxerga_conflito_alem_da_primeira_pagina_de_1000(self):
        nomes = [f"Docente {i}" for i in range(1, 1201)] + ["MARIA DA COSTA"]
        self.assertGreater(len(nomes), manutencao_banco.PAGINA)
        cliente = cliente_com(nomes)
        with self.assertRaises(ConversaoPendenteError) as contexto:
            verificar_conversao_pendente(PROFESSORES, cliente)
        self.assertIn("'MARIA DA COSTA' -> 'Maria da Costa'", str(contexto.exception))

    def test_a_checagem_vem_antes_de_qualquer_escrita(self):
        eventos = []
        cliente = cliente_com(["MARIA DA COSTA"])
        with mock.patch.object(persistencia_sigaa, "verificar_conversao_pendente",
                               side_effect=lambda *a, **k: eventos.append("trava")), \
             mock.patch.object(persistencia_sigaa, "salvar_professores",
                               side_effect=lambda *a, **k: eventos.append("professores") or {}), \
             mock.patch.object(persistencia_sigaa, "salvar_disciplinas",
                               side_effect=lambda *a, **k: eventos.append("disciplinas") or {}), \
             mock.patch.object(persistencia_sigaa, "salvar_turmas",
                               side_effect=lambda *a, **k: eventos.append("turmas")):
            gravar_catalogo(PROFESSORES, DISCIPLINAS, TURMAS, cliente)
        self.assertEqual(eventos, ["trava", "professores", "disciplinas", "turmas"])

    def test_nao_existe_flag_para_ignorar_a_trava(self):
        import inspect
        parametros = inspect.signature(gravar_catalogo).parameters
        self.assertEqual(list(parametros), ["professores", "disciplinas", "turmas", "cliente"])


try:
    import scraper_sigaa
except ImportError:  # a CI pode não ter o selenium; o resto dos testes não depende dele
    scraper_sigaa = None


class FakeScraper:
    """Substitui o navegador: devolve uma unidade com os dados de teste."""

    def __init__(self, *args, **kwargs):
        pass

    def listar_unidades(self):
        return [("1", "UNIDADE DE TESTE")]

    def buscar_unidade(self, ano, periodo, valor, texto):
        from resumo_sigaa import Resumo
        return scraper_sigaa.Resultado(
            scraper_sigaa.OK, "",
            [dict(p) for p in PROFESSORES], [dict(d) for d in DISCIPLINAS],
            [dict(t, docentes_brutos="") for t in TURMAS], Resumo())

    def fechar(self):
        pass


@unittest.skipIf(scraper_sigaa is None, "selenium não instalado")
class TestMainDoImportador(unittest.TestCase):
    def rodar(self, cliente, dry_run):
        with mock.patch.object(scraper_sigaa, "SigaaScraper", FakeScraper), \
             mock.patch.object(persistencia_sigaa, "_supabase", return_value=cliente), \
             redirect_stdout(io.StringIO()) as saida:
            codigo = scraper_sigaa.main(ano="2026", periodo="2", dry_run=dry_run, pausa=0)
        return codigo, saida.getvalue()

    def test_dry_run_nao_consulta_o_banco(self):
        cliente = cliente_com(["MARIA DA COSTA"])
        with mock.patch.object(persistencia_sigaa, "_supabase",
                               side_effect=AssertionError("o dry-run não pode abrir o banco")), \
             mock.patch.object(scraper_sigaa, "SigaaScraper", FakeScraper), \
             redirect_stdout(io.StringIO()) as saida:
            codigo = scraper_sigaa.main(ano="2026", periodo="2", dry_run=True, pausa=0)
        self.assertEqual(codigo, 0)
        self.assertIn("[DRY-RUN]", saida.getvalue())
        self.assertEqual(cliente.upserts, [])

    def test_gravar_com_conversao_pendente_sai_com_codigo_diferente_de_zero(self):
        cliente = cliente_com(["MARIA DA COSTA"])
        codigo, saida = self.rodar(cliente, dry_run=False)
        self.assertEqual(codigo, persistencia_sigaa.CODIGO_SAIDA_CONVERSAO_PENDENTE)
        self.assertNotEqual(codigo, 0)
        self.assertIn(COMANDO_CONVERSAO, saida)
        self.assertEqual(cliente.upserts, [])
        self.assertEqual([p["nome"] for p in cliente.tabelas["professores"]], ["MARIA DA COSTA"])

    def test_gravar_com_banco_convertido_funciona(self):
        cliente = cliente_com(["Maria da Costa"])
        codigo, _ = self.rodar(cliente, dry_run=False)
        self.assertEqual(codigo, 0)
        self.assertEqual(len(cliente.tabelas["turmas"]), 2)


if __name__ == "__main__":
    unittest.main()
