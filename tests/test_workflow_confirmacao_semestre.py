"""As opções de confirmação devem chegar aos dois jobs sem expor credenciais no dry-run."""
from pathlib import Path
import unittest

class TestWorkflowConfirmacaoSemestre(unittest.TestCase):
    def test_finalidade_e_relatorio_sao_passados_nos_dois_modos(self):
        caminho=Path(__file__).resolve().parents[1]/'.github/workflows/atualizar-dados-sigaa.yml'
        texto=caminho.read_text(encoding='utf-8')
        seco,gravar=texto.split('\n  dry-run:',1)[1].split('\n  gravar:',1)
        for job in [seco,gravar]:
            self.assertIn('needs: validar-entrada',job)
            etapa=job.split('id: scraper',1)[1].split('      - name:',1)[0]
            ambiente,script=etapa.split('        run:',1)
            self.assertIn('FINALIDADE: ${{ inputs.finalidade }}',ambiente)
            self.assertIn('--relatorio coleta.json',script)
            self.assertIn('--finalidade "$FINALIDADE"',script)
        self.assertNotIn('secrets.',seco)
        confirmacao=gravar.split('id: confirmacao',1)[1].split('      - name:',1)[0]
        self.assertIn("steps.scraper.outputs.codigo == '0'",confirmacao)
        self.assertIn("steps.duplicatas.outputs.codigo == '0'",confirmacao)
