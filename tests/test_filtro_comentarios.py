"""Filtro automático dos comentários (issue #214): unidade, sem rede."""
import unittest

from app.filtro_comentarios import (DADOS_PESSOAIS, LINK, OFENSA, mensagem_bloqueio,
                                    normalizar, verificar_comentario)


class BaseFiltro(unittest.TestCase):
    def conferir(self, categoria, textos):
        for texto in textos:
            with self.subTest(texto=texto):
                self.assertEqual(verificar_comentario(texto), categoria)


class TestBloqueios(BaseFiltro):
    def test_email(self):
        self.conferir(DADOS_PESSOAIS, [
            'me escreve em joao.silva@gmail.com por favor',
            'JOAO@ALUNO.UNB.BR',
            'meu contato: fulano arroba gmail ponto com',
            'fulano (at) hotmail',
            'fulano @ outlook . com',
        ])

    def test_telefone(self):
        self.conferir(DADOS_PESSOAIS, [
            '(61) 99999-9999', '61 99999 9999', '61999999999', '+55 61 99999-9999',
            '+5561999999999', '(61)3333-4444', '99999-9999', '3333-4444', '3333 4444',
            '61 9 9999 9999',
        ])

    def test_cpf(self):
        self.conferir(DADOS_PESSOAIS, [
            '123.456.789-01', '12345678901', '123 456 789 01', 'cpf 123.456.789.01',
        ])

    def test_matricula(self):
        self.conferir(DADOS_PESSOAIS, [
            'matrícula 190012345', 'matricula 19/0012345', '19.0012345', '19-0012345',
            '2019.1.2345', 'mat 190 012 345',
        ])

    def test_link(self):
        self.conferir(LINK, [
            'veja http://exemplo.xyz/abc', 'HTTPS://EXEMPLO.XYZ', 'www.exemplo.xyz',
            'acesse exemplo.com', 'exemplo.com.br/prof', 'meusite.net', 'ong.org',
            'curso.edu.br', 'portal.gov.br', 'WWW.Site.Com',
        ])

    def test_palavroes_e_ofensas(self):
        self.conferir(OFENSA, [
            'esse professor é um idiota', 'IDIOTA', 'que merda de aula', 'vai tomar no cu',
            'filho da puta', 'FILHO DA PUTA', 'ele é viado', 'caralho de prova',
            'é um babaca', 'professor retardado',
        ])

    def test_foda_puto_puta_e_burro_com_variacoes(self):
        self.conferir(OFENSA, [
            'foda', 'FODA', 'fodas', 'Fóda', 'fodaaa', 'puto', 'PUTOS', 'Pútos', 'putas',
            'Púta', 'burro', 'BURRO', 'burra', 'BÚRRA', 'burros', 'burras', 'buuurro',
            'ele é muito burro', 'que professor foda',
        ])

    def test_palavras_que_apenas_contem_os_termos_passam(self):
        self.conferir(None, [
            'burocracia', 'burocrático', 'computador', 'disputa', 'reputação', 'imputar',
            'fodástico', 'putrefato', 'burrico', 'inputa', 'sufoda',
        ])

    def test_evasoes_basicas(self):
        self.conferir(OFENSA, [
            'puuuuta', 'PUTA', 'p​u​t​a', 'p.u.t.a', 'p u t a', 'm3rda',
            'merdaaaa', 'cuzão', 'CUZÃO', 'caraaalho', 'f­ilho da put​a',
            'ｉｄｉｏｔａ',
        ])
        self.conferir(DADOS_PESSOAIS, [
            'JOAO​@GMAIL.COM', '6​1 9​9999-9999',
            '１２３.４５６.７８９-０１',
        ])
        self.conferir(LINK, ['W​WW.EXEMPLO.XYZ', 'exemplo​.com'])


class TestTelefoneEMatriculaContinuamBloqueados(BaseFiltro):
    def test_casos_de_referencia(self):
        self.conferir(DADOS_PESSOAIS, [
            'me chama 61 99999 1234', '(61)98888-7777', '61 3333 4444', 'meu zap 61999991234',
            'matrícula 190012345',
        ])


class TestFalsosPositivos(BaseFiltro):
    def test_semestres_notas_e_numeros_curtos(self):
        self.conferir(None, [
            '2024.1', '2023/2', '2024 2', 'cursei em 2024.2 e 2025.1', 'semestre 2024 1 e 2024 2',
            'nota 8,5', 'nota 10', 'tirei 7,5 e 9,0', '100% recomendo', '70% de aprovação',
            'turma 03', 'turma 12', 'FGA0011', 'Cálculo 1', 'Cálculo 2 com FGA0011 em 2024.1',
            'FGA0011/2024.1', '10 de 12 provas eram difíceis', '3 listas e 2 provas',
            '2024-2025', '2023/2024', '2023 2024 2025',
        ])

    def test_datas(self):
        self.conferir(None, [
            '12 de março de 2024', 'prova em 5 de abril', 'entregou dia 10 de maio de 2023',
            'em 01/03/2024 foi a prova',
        ])

    def test_criticas_duras_sem_palavrao(self):
        self.conferir(None, [
            'péssima didática', 'não recomendo', 'aulas confusas e desorganizadas',
            'professor muito ruim, não explica nada', 'a pior disciplina que já cursei',
            'avaliações injustas e sem feedback', 'não vale a pena',
        ])

    def test_palavras_que_contem_termos_dentro_de_outras(self):
        self.conferir(None, [
            'computador', 'disputa por vagas', 'cuidado com os prazos', 'curso difícil',
            'reputação', 'computação', 'execução do projeto', 'análise de algoritmos',
            'cúmulo da organização', 'escudo', 'aculturamento',
        ])

    def test_numeros_curtos_separados_por_espaco_nao_sao_telefone_nem_matricula(self):
        self.conferir(None, [
            'notas 8 9 7 10 6 7 9 8', 'tirei 7 8 9 10 nas quatro provas e 8 na final',
            'aulas às 8 10 14 16 horas, 2 vezes por semana',
            'Notas: P1 8,5; P2 7,0; P3 9,0; trabalho 10.',
            'lista de exercícios 1 2 3 4 5 6 7 8 9', 'média final 7,5 8,0 6,5 9,0',
            'turma 01 02 03 04',
            'tive 2 provas, 3 trabalhos, 4 listas e 1 seminário em 2024.1',
            'questões 10 12 15 20 25 30',
        ])

    def test_texto_vazio_ou_comum(self):
        self.conferir(None, ['', 'Ótimo professor, explica muito bem.', 'ok'])


class TestNormalizacao(unittest.TestCase):
    def test_normalizar(self):
        self.assertEqual(normalizar('ÁÇÃO​ ｔｅｓｔｅ'), 'acao teste')

    def test_mensagens_nao_revelam_o_trecho(self):
        for categoria in (DADOS_PESSOAIS, LINK, OFENSA):
            self.assertIn('Seu comentário não foi publicado', mensagem_bloqueio(categoria))
            self.assertIn('Seu comentário não foi salvo', mensagem_bloqueio(categoria, 'salvo'))


if __name__ == '__main__':
    unittest.main()
