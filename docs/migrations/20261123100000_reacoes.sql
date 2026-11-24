-- Issue #212 (C09). Depende de 002_comentarios.sql.
-- 004 já é usado por professores_unicos; identificador independente.
BEGIN;
CREATE TABLE IF NOT EXISTS comentarios_reacoes (
    comentario_id BIGINT NOT NULL REFERENCES comentarios(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES perfis(id) ON DELETE CASCADE,
    valor SMALLINT NOT NULL CHECK (valor IN (-1, 1)),
    PRIMARY KEY (comentario_id, usuario_id)
);
ALTER TABLE comentarios_reacoes ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON comentarios_reacoes FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON comentarios_reacoes TO service_role;
COMMIT;
