import re
import unittest
from pathlib import Path


class TestMigracaoModeracao(unittest.TestCase):
    MIGRACAO = Path('docs/migrations/008_moderacao_comentarios.sql')

    def _ler_sql(self):
        self.assertTrue(
            self.MIGRACAO.exists(),
            'A migração docs/migrations/008_moderacao_comentarios.sql deve existir.',
        )
        return self.MIGRACAO.read_text(encoding='utf-8').lower()

    def test_cria_tabelas_moderadores_decisoes_e_contestacoes(self):
        sql = self._ler_sql()
        for tabela in ('moderadores', 'moderacoes_comentarios', 'contestacoes_comentarios'):
            self.assertIn(f'create table if not exists {tabela}', sql)

    def test_valida_acoes_de_moderacao_e_justificativa_obrigatoria(self):
        sql = self._ler_sql()
        self.assertRegex(
            sql,
            r"check\s*\(\s*acao\s+in\s*\(\s*'manter'\s*,\s*'ocultar'\s*,\s*'restaurar'\s*\)\s*\)",
        )
        self.assertIn('ck_moderacoes_justificativa_tamanho', sql)
        self.assertIn('ck_contestacoes_justificativa_tamanho', sql)
        self.assertRegex(sql, r'moderador_id\s+uuid\s+not\s+null\s+references\s+perfis\(id\)')

    def test_indices_fila_historico_e_contestacao_ativa_unica(self):
        sql = self._ler_sql()
        self.assertIn('idx_moderacoes_comentario_criado', sql)
        self.assertIn('uq_contestacoes_ativa_comentario', sql)
        self.assertIn('idx_contestacoes_abertas', sql)

    def test_rls_privado_restrito_ao_service_role(self):
        sql = self._ler_sql()
        for tabela in ('moderadores', 'moderacoes_comentarios', 'contestacoes_comentarios'):
            self.assertIn(f'alter table {tabela} enable row level security;', sql)
            self.assertIn(f'revoke all on {tabela} from public, anon, authenticated;', sql)
            self.assertRegex(
                sql,
                rf'grant\s+[a-z,\s]+\s+on\s+{tabela}\s+to\s+service_role;',
            )
            # Nenhuma política pública para anon ou authenticated
            self.assertIsNone(
                re.search(rf'create\s+policy\s+.*\s+on\s+{tabela}\b', sql),
                f'A tabela {tabela} deve ser privada (sem policies para anon/authenticated).',
            )


if __name__ == '__main__':
    unittest.main()