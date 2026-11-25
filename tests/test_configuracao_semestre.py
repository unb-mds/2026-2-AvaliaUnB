"""A configuração é explícita; ausência ou erro nunca esconde o catálogo histórico."""
import json
from pathlib import Path
import tempfile
import unittest

from semestres import interpretar_semestre, ler_semestre_atual, validar_semestre


class TestConfiguracaoSemestre(unittest.TestCase):
    def test_par_valido_e_periodos_do_sigaa(self):
        for periodo in range(1, 5):
            self.assertEqual(validar_semestre(2026, periodo), (2026, periodo))
            self.assertEqual(interpretar_semestre(f'2026-{periodo}'), (2026, periodo))

    def test_configuracao_desabilitada_explicitamente_nao_le_arquivo(self):
        self.assertIsNone(ler_semestre_atual(None))

    def test_rejeita_entrada_invalida_sem_coercao(self):
        for ano, periodo in [(26, 2), (True, 2), ('2026', 2), (2026, True),
                             (2026, '2'), (2026, 0), (2026, 5), (10000, 1)]:
            with self.subTest(ano=ano, periodo=periodo), self.assertRaises(ValueError):
                validar_semestre(ano, periodo)
        for valor in ['26-2', '2026/2', '2026-0', '2026-5', '2026-22', '', None, '２０２６-2']:
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                interpretar_semestre(valor)

    def test_configuracao_persiste_sem_inferir_maior_periodo(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho=Path(pasta)/'semestre.json'
            caminho.write_text(json.dumps({'semestre_atual': {'ano': 2025, 'periodo': 1}}))
            self.assertEqual(ler_semestre_atual(caminho), (2025, 1))
            # Reabrir não modifica o arquivo nem deriva o semestre do calendário.
            self.assertEqual(ler_semestre_atual(caminho), (2025, 1))

    def test_ausencia_nulo_erro_e_configuracao_parcial_preservam_historico(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho=Path(pasta)/'semestre.json'
            with self.assertLogs('semestres', level='WARNING'):
                self.assertIsNone(ler_semestre_atual(caminho))
            for conteudo in ['{"semestre_atual": null}', '{}', '[]', 'null', 'invalid',
                             '{"semestre_atual": {"ano": 2026}}',
                             '{"semestre_atual": {"ano": 2026, "periodo": 9}}']:
                caminho.write_text(conteudo)
                self.assertIsNone(ler_semestre_atual(caminho))
