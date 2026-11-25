-- Issue #217: descartar registros de denúncia e moderação após 90 dias (LGPD).
-- Depende de: 005_denuncias_comentarios.sql (denuncias_comentarios),
--             008_moderacao_comentarios.sql (moderacoes_comentarios, contestacoes_comentarios).
-- Fora do escopo: apagar comentários publicados.
--
-- Esta migração cria índices para consulta por data de encerramento e a função
-- `descartar_registros_moderacao_expirados(dias_retencao)` restrita ao `service_role`
-- (pode ser chamada pelo job agendado no GitHub Actions via RPC ou por `pg_cron`).

BEGIN;

-- Índices parciais/temporais para acelerar a rotina diária de descarte
CREATE INDEX IF NOT EXISTS idx_denuncias_resolvidas_retencao
    ON denuncias_comentarios (resolvida_em)
    WHERE resolvida_em IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_moderacoes_criado_retencao
    ON moderacoes_comentarios (criado_em);

CREATE INDEX IF NOT EXISTS idx_contestacoes_resolvidas_retencao
    ON contestacoes_comentarios (resolvida_em)
    WHERE resolvida_em IS NOT NULL;

-- Função de expurgo LGPD: remove denúncias encerradas, decisões de moderação
-- e contestações encerradas há mais de `dias_retencao` (padrão: 90 dias).
-- Nunca apaga linhas da tabela `comentarios`.
CREATE OR REPLACE FUNCTION descartar_registros_moderacao_expirados(
    dias_retencao INTEGER DEFAULT 90
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    limite TIMESTAMPTZ;
    qtd_denuncias INTEGER := 0;
    qtd_moderacoes INTEGER := 0;
    qtd_contestacoes INTEGER := 0;
BEGIN
    IF dias_retencao IS NULL OR dias_retencao < 1 THEN
        RAISE EXCEPTION 'dias_retencao deve ser um inteiro positivo';
    END IF;

    limite := NOW() - make_interval(days => dias_retencao);

    DELETE FROM denuncias_comentarios d
    WHERE d.resolvida_em IS NOT NULL
      AND d.resolvida_em < limite
      AND NOT EXISTS (
          SELECT 1
          FROM comentarios c
          WHERE c.id = d.comentario_id
            AND c.ocultado_em IS NOT NULL
      );
    GET DIAGNOSTICS qtd_denuncias = ROW_COUNT;

    DELETE FROM moderacoes_comentarios m
    WHERE m.criado_em < limite
      AND NOT EXISTS (
          SELECT 1
          FROM comentarios c
          WHERE c.id = m.comentario_id
            AND c.ocultado_em IS NOT NULL
      );
    GET DIAGNOSTICS qtd_moderacoes = ROW_COUNT;

    DELETE FROM contestacoes_comentarios ct
    WHERE ct.resolvida_em IS NOT NULL
      AND ct.resolvida_em < limite
      AND NOT EXISTS (
          SELECT 1
          FROM comentarios c
          WHERE c.id = ct.comentario_id
            AND c.ocultado_em IS NOT NULL
      );
    GET DIAGNOSTICS qtd_contestacoes = ROW_COUNT;

    RETURN jsonb_build_object(
        'denuncias_removidas', qtd_denuncias,
        'moderacoes_removidas', qtd_moderacoes,
        'contestacoes_removidas', qtd_contestacoes,
        'limite_utc', limite
    );
END;
$$;

REVOKE ALL ON FUNCTION descartar_registros_moderacao_expirados(INTEGER) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION descartar_registros_moderacao_expirados(INTEGER) TO service_role;

COMMIT;