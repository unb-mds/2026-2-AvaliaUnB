"""Grafia comum dos nomes em CAIXA ALTA (issue #236): função pura do scraper, sem rede."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

from texto_sigaa import PARTICULAS, SIGLAS, grafia_comum

PROFESSORES = [
    ("JOÃO SILVA", "João Silva"),
    ("MARIA DA COSTA", "Maria da Costa"),
    ("ARTHUR DE OLIVEIRA D'AREDE", "Arthur de Oliveira D'Arede"),
    ("CANDIDA IVI MARCOVICH DE ARAUJO", "Candida Ivi Marcovich de Araujo"),
    ("Luciana Oliveira Militão", "Luciana Oliveira Militão"),
    ("JOSÉ ÁVILA JUNIOR", "José Ávila Junior"),
    ("ANA DOS SANTOS E SILVA", "Ana dos Santos e Silva"),
    ("PAULO DI PIETRO", "Paulo di Pietro"),
    ("CARLOS VON BRAUN", "Carlos von Braun"),
    ("MARIA D SOUZA Y LIMA", "Maria D Souza Y Lima"),
    ("JOÃO PEDRO II", "João Pedro Ii"),
    ("RAFAEL UNB", "Rafael Unb"),
    ("ANA TV LGBT", "Ana Tv Lgbt"),
]

DISCIPLINAS = [
    ("CÁLCULO 1", "Cálculo 1"),
    ("CALCULO 1", "Calculo 1"),
    ("INTRODUÇÃO À FÍSICA II", "Introdução à Física II"),
    ("TÓPICOS EM TV E LGBT", "Tópicos em TV e LGBT"),
    ("FÍSICA EXPERIMENTAL: I", "Física Experimental: I"),
    ("FÍSICA EXPERIMENTAL I: MECÂNICA", "Física Experimental I: Mecânica"),
    ("DERMATO-FUNCIONAL", "Dermato-Funcional"),
    ("LABORATÓRIO 2: A VIDA - PRÁTICA III", "Laboratório 2: A Vida - Prática III"),
    ("PRÁTICA IV – A SAÚDE", "Prática IV – A Saúde"),
    ("TCC EM LS E LSB", "TCC em LS e LSB"),
    ("ESTUDOS DE UNB E PSL", "Estudos de UnB e PSL"),
    ("RAIOS X E TOMOGRAFIA", "Raios X e Tomografia"),
    ("CIVIL E MILITAR", "Civil e Militar"),
    ("TURMA 1A E 2ª FASE", "Turma 1A e 2ª Fase"),
    ("ESTRATÉGIAS PARA CRIAÇÃO", "Estratégias para Criação"),
    ("ENSINO COM TECNOLOGIA E PESQUISA SOBRE O MEIO", "Ensino com Tecnologia e Pesquisa sobre o Meio"),
    ("FÍSICA PELO MÉTODO ATÉ O FIM", "Física pelo Método até o Fim"),
    ("COM FOCO: COMO PENSAR", "Com Foco: Como Pensar"),
    ("EDUCAÇÃO DE JOVENS E ADULTOS - EJA", "Educação de Jovens e Adultos - EJA"),
    ("ESTÁGIO SUPERVISIONADO BACHARELADO EM EDF 1", "Estágio Supervisionado Bacharelado em EDF 1"),
    ("FUNDAMENTOS DO DESENVOLVIMENTO E APRENDIZAGEM APLICADOS A EDF INFANTIL",
     "Fundamentos do Desenvolvimento e Aprendizagem Aplicados a EDF Infantil"),
]

DEPARTAMENTOS = [
    ("CAMPUS UNB CEILÂNDIA: FACULDADE DE CIÊNCIAS E TECNOLOGIAS EM SAÚDE - BRASÍLIA",
     "Campus UnB Ceilândia: Faculdade de Ciências e Tecnologias em Saúde - Brasília"),
    ("DEPARTAMENTO DE AUDIOVISUAIS E PUBLICIDADE/DAP - BRASÍLIA",
     "Departamento de Audiovisuais e Publicidade/DAP - Brasília"),
    ("DEPARTAMENTO DE COMUNICAÇÃO ORGANIZACIONAL/COM - BRASÍLIA",
     "Departamento de Comunicação Organizacional/COM - Brasília"),
    ("DECANATO DE PÓS-GRADUAÇÃO / DPG - BRASÍLIA",
     "Decanato de Pós-Graduação / DPG - Brasília"),
    ("DEPARTAMENTO DE COMUNICAÇÃO / COM - BRASÍLIA",
     "Departamento de Comunicação / COM - Brasília"),
    ("CENTRO COM FOCO EM EJA/COM",
     "Centro com Foco em EJA/COM"),
]


class TestExemplos(unittest.TestCase):
    def conferir(self, tipo, casos):
        for original, esperado in casos:
            with self.subTest(tipo=tipo, original=original):
                resultado = grafia_comum(original, tipo)
                self.assertEqual(resultado, esperado)
                self.assertEqual(grafia_comum(resultado, tipo), resultado)  # idempotente

    def test_professores(self):
        self.conferir("professor", PROFESSORES)

    def test_disciplinas(self):
        self.conferir("disciplina", DISCIPLINAS)

    def test_departamentos(self):
        self.conferir("departamento", DEPARTAMENTOS)


class TestRegras(unittest.TestCase):
    def test_qualquer_minuscula_devolve_o_texto_como_veio(self):
        for texto in ("Luciana Oliveira Militão", "JOÃO silva", "MARIA DA COSTa", "cálculo 1"):
            with self.subTest(texto=texto):
                self.assertEqual(grafia_comum(texto, "professor"), texto)

    def test_vazio_none_e_sem_letras(self):
        for tipo in ("professor", "disciplina", "departamento"):
            self.assertIsNone(grafia_comum(None, tipo))
            self.assertEqual(grafia_comum("", tipo), "")
            self.assertEqual(grafia_comum("2024.1 - 3", tipo), "2024.1 - 3")

    def test_tipo_invalido(self):
        for tipo in ("curso", "", None, "Professor"):
            with self.subTest(tipo=tipo), self.assertRaises(ValueError):
                grafia_comum("JOÃO SILVA", tipo)
        with self.assertRaises(ValueError):
            grafia_comum("", "curso")  # o tipo é validado antes do texto vazio

    def test_romano_so_em_disciplina(self):
        self.assertEqual(grafia_comum("FÍSICA II", "disciplina"), "Física II")
        self.assertEqual(grafia_comum("III: TÓPICOS", "disciplina"), "III: Tópicos")
        self.assertEqual(grafia_comum("LUIS III", "professor"), "Luis Iii")
        self.assertEqual(grafia_comum("CANDIDA IVI", "professor"), "Candida Ivi")
        self.assertEqual(grafia_comum("SALA II", "departamento"), "Sala Ii")

    def test_romano_so_como_palavra_inteira(self):
        self.assertEqual(grafia_comum("VIVI MIX DIVIDIR", "disciplina"), "Vivi Mix Dividir")
        self.assertEqual(grafia_comum("XX E XIV", "disciplina"), "XX e XIV")

    def test_siglas_so_em_disciplina_e_departamento(self):
        self.assertEqual(grafia_comum("TCC E DPG", "professor"), "Tcc e Dpg")
        self.assertEqual(grafia_comum("TCC E DPG", "disciplina"), "TCC e DPG")
        self.assertEqual(grafia_comum("INSTITUTO UNB", "departamento"), "Instituto UnB")
        self.assertEqual(grafia_comum("UNB", "professor"), "Unb")

    def test_sigla_depois_da_barra_so_em_departamento(self):
        self.assertEqual(grafia_comum("CENTRO DE ESTUDOS/CEX", "departamento"),
                         "Centro de Estudos/CEX")
        self.assertEqual(grafia_comum("CENTRO / COM", "departamento"), "Centro / COM")
        self.assertEqual(grafia_comum("CENTRO/CEX", "disciplina"), "Centro/Cex")

    def test_particula_no_inicio_de_trecho_fica_maiuscula(self):
        self.assertEqual(grafia_comum("DE LA CRUZ", "professor"), "De La Cruz")
        self.assertEqual(grafia_comum("TEMA: A BASE - E O FIM", "disciplina"), "Tema: A Base - E o Fim")
        self.assertEqual(grafia_comum("MUNDO – OS FATOS", "disciplina"), "Mundo – Os Fatos")

    def test_hifen_e_apostrofo(self):
        self.assertEqual(grafia_comum("PÓS-GRADUAÇÃO EM PRÉ-A", "disciplina"), "Pós-Graduação em Pré-A")
        self.assertEqual(grafia_comum("ANA D'ÁVILA", "professor"), "Ana D'Ávila")
        self.assertEqual(grafia_comum("ANA D’ÁVILA", "professor"), "Ana D’Ávila")

    def test_espacos_numeros_e_simbolos_ficam_como_estao(self):
        self.assertEqual(grafia_comum("CÁLCULO  1\t(2024.1)", "disciplina"), "Cálculo  1\t(2024.1)")
        self.assertEqual(grafia_comum("FÍSICA 1ª PARTE", "disciplina"), "Física 1ª Parte")

    def test_com_como_sigla_depois_da_barra_e_como_preposicao_fora_dela(self):
        self.assertEqual(grafia_comum("ESCOLA/COM", "departamento"), "Escola/COM")
        self.assertEqual(grafia_comum("ESCOLA / COM", "departamento"), "Escola / COM")
        for tipo in ("professor", "disciplina", "departamento"):
            with self.subTest(tipo=tipo):
                self.assertEqual(grafia_comum("ANA COM LUZ", tipo), "Ana com Luz")
        self.assertEqual(grafia_comum("COM LUZ", "professor"), "Com Luz")
        self.assertEqual(grafia_comum("ESCOLA/COM", "disciplina"), "Escola/com")

    def test_eja_so_em_disciplina_e_departamento(self):
        self.assertEqual(grafia_comum("ANA EJA", "professor"), "Ana Eja")
        self.assertEqual(grafia_comum("ESCOLA EJA", "departamento"), "Escola EJA")

    def test_edf_so_em_disciplina_e_departamento(self):
        self.assertEqual(grafia_comum("ANA EDF", "professor"), "Ana Edf")
        self.assertEqual(grafia_comum("CURSO DE EDF", "departamento"), "Curso de EDF")

    def test_listas_do_topo_do_modulo(self):
        self.assertTrue({"de", "da", "do", "dos", "das", "e", "à", "às", "van", "von", "du", "para", "com", "por", "sobre", "sem", "como", "que",
            "pelo", "pela", "pelos", "pelas", "sob", "entre", "até"} <= PARTICULAS)
        self.assertTrue({"TCC", "TV", "LGBT", "DPG", "DAP", "EJA", "EDF"} <= SIGLAS)
        self.assertTrue(all(p == p.lower() for p in PARTICULAS))
        self.assertTrue(all(s == s.upper() for s in SIGLAS))


if __name__ == "__main__":
    unittest.main()
