import unittest
from pathlib import Path


class TestMigracaoRetencaoModeracao(unittest.TestCase):
    MIGRACAO = Path('docs/migrations/009_retencao_moderacao_90_dias.sql')

    def _ler_sql(self):
        self.assertTrue(
            self.MIGRACAO.exists(),
            f'A migração {self.MIGRACAO} deve existir.',
        )
        return self.MIGRACAO.read_text(encoding='utf-8').lower()

    def test_cria_funcao_de_descarte_com_padrao_90_dias(self):
        sql = self._ler_sql()
        self.assertIn('create or replace function descartar_registros_moderacao_expirados', sql)
        self.assertIn('dias_retencao integer default 90', sql)
        self.assertIn('security definer', sql)

    def test_apaga_apenas_registros_encerrados_de_denuncia_moderacao_e_contestacao(self):
        sql = self._ler_sql()
        self.assertIn('delete from denuncias_comentarios', sql)
        self.assertIn('resolvida_em is not null', sql)
        self.assertIn('delete from moderacoes_comentarios', sql)
        self.assertIn('delete from contestacoes_comentarios', sql)
        # Comentários publicados estão fora do escopo e nunca podem ser apagados pela rotina
        self.assertNotIn('delete from comentarios', sql)

    def test_restrito_ao_service_role_e_cria_indices_de_expurgo(self):
        sql = self._ler_sql()
        self.assertIn('revoke all on function descartar_registros_moderacao_expirados(integer) from public, anon, authenticated;', sql)
        self.assertIn('grant execute on function descartar_registros_moderacao_expirados(integer) to service_role;', sql)
        self.assertIn('idx_denuncias_resolvidas_retencao', sql)
        self.assertIn('idx_moderacoes_criado_retencao', sql)
        self.assertIn('idx_contestacoes_resolvidas_retencao', sql)


if __name__ == '__main__':
    unittest.main()