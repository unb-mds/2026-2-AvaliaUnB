-- Issue #258: a autoria fica privada, inclusive na leitura direta pela Data API.
-- Aplicar depois das migrações 001 a 007. Não remove dados nem o vínculo da conta.
BEGIN;

-- Revogar só uma coluna não basta enquanto houver SELECT na tabela inteira.
REVOKE SELECT ON TABLE public.comentarios FROM PUBLIC, anon, authenticated;
REVOKE SELECT (usuario_id, ocultado_em) ON TABLE public.comentarios
    FROM PUBLIC, anon, authenticated;
GRANT SELECT (id, professor_id, disciplina_id, texto, criado_em, atualizado_em)
    ON TABLE public.comentarios TO anon, authenticated;

-- RLS, autoria, escrita por coluna e permissões do backend permanecem as existentes.
NOTIFY pgrst, 'reload schema';
COMMIT;
